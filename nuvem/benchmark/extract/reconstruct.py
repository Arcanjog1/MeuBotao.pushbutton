# -*- coding: utf-8 -*-
"""Dump bruto do Revit -> `reference.json` + `input.json`.

O PROBLEMA QUE ESTE MODULO RESOLVE
----------------------------------
Num projeto ja' ENTREGUE nao sobrou nada para ler direto: as paredes de
referencia e as portas/janelas nativas sao apagadas no fim do processo
(medido nos dois projetos de PADRAO_MODULACAO.md - Walls/Doors/Windows =
0). O que existe e' um monte de blocos soltos. Entao os eixos, os vaos e
os encontros precisam ser RECONSTRUIDOS a partir do proprio layout de
pecas.

Como:

1. **Fiadas** - agrupa as pecas por cota Z (`COURSE_Z_TOLERANCE_CM`).
2. **Eixos** - cada peca define uma reta (centro + direcao da rotacao).
   Pecas na MESMA reta infinita (mesmo angulo mod 180, mesmo afastamento
   perpendicular) formam um eixo; o eixo e' quebrado em paredes so' onde
   o vazio passa de `OPENING_GAP_MAX_CM` - abaixo disso o vazio pode ser
   uma porta, e cortar ali partiria uma parede real em duas.
3. **Vaos** - `core/engine/opening_audit.detect_wall_openings_from_courses`,
   que ja existe, e' puro e ja' foi validado contra este mesmo projeto
   (secao 10 do REGRAS_MODULACAO_BLOCOS.md). Nao ha' nenhuma
   reimplementacao aqui.
4. **Encontros** - onde dois eixos de direcoes diferentes se cruzam ou se
   tocam; L / T / X pelo numero de bracos que chegam no ponto.
5. **Papeis** - pelo nome da familia (canaleta/verga/cortado, tambem via
   `opening_audit`) e pela posicao (amarracao quando a peca ocupa um
   encontro).

TUDO AQUI E' PURO. Nenhum import do Revit - o dump ja' e' JSON. E' o que
permite testar a reconstrucao com uma planta inventada, sem abrir o Revit.

O QUE ESTE MODULO NAO FAZ
-------------------------
Nao corrige nada do que le'. Se o projeto humano tem um bloco fora do
eixo, ele sai fora do eixo - o gabarito precisa ser o que o projeto E', nao
o que ele deveria ser. A unica coisa que fica de fora sao as pecas que nao
couberam em nenhum eixo, e mesmo essas vao para `orphan_blocks`, contadas
e visiveis.
"""

import math
import os
import sys

from .. import analysis
from .. import model

# `core/engine/opening_audit.py` e' 100% puro (o proprio cabecalho dele
# garante) - da' para importar sem nenhum duble do Revit.
_CORE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "core", "engine",
)
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)
import opening_audit  # noqa: E402

# --------------------------------------------------------- reconstrucao
# Duas pecas estao na mesma reta infinita quando o angulo bate dentro de
# `AXIS_ANGLE_TOLERANCE_DEG` e o afastamento perpendicular dentro de
# `AXIS_OFFSET_TOLERANCE_CM`. O afastamento tem que ser generoso o
# bastante para absorver peca de amarracao encostada na face (que fica
# meia espessura fora do eixo) e apertado o bastante para nao juntar duas
# paredes paralelas vizinhas - por isso meia espessura + folga.
AXIS_ANGLE_TOLERANCE_DEG = 2.0
AXIS_OFFSET_TOLERANCE_CM = 8.0

# Vazio maior que isto quebra o eixo em duas paredes. Igual ao teto de
# largura de vao ja' medido em projeto real (`OPENING_GAP_MAX_CM`): abaixo
# disso o vazio ainda pode ser uma porta.
WALL_SPLIT_GAP_CM = opening_audit.OPENING_GAP_MAX_CM

# Um eixo com menos que isto de comprimento nao e' parede - e' peca
# avulsa (uma amarracao girada, um bloco solto).
MIN_WALL_LENGTH_CM = 40.0

# Distancia maxima entre o fim de um eixo e a reta de outro para eles
# formarem um encontro.
JUNCTION_TOUCH_TOLERANCE_CM = 12.0


def code_for_type(type_name, length_cm, height_cm):
    """Codigo logico curto e ESTAVEL de um tipo do Revit.

    As seis pecas do catalogo nucleo recebem os mesmos codigos que o solver
    usa (B39/B34/B54/B19/C09/C04) - e' o que permite comparar gabarito e
    resultado peca a peca. As demais (canaleta, verga, cortado, vedacao)
    ganham codigo derivado, porque o solver ainda nao as gera: elas
    aparecem no gabarito e o comparador as classifica como diferenca, nunca
    como erro."""
    name = (type_name or "").upper()
    length = int(round(length_cm or 0.0))
    cut = "CORTADO" in name

    if "PASTILHA" in name:
        code = "C04"
    elif "COMPENSADOR" in name:
        code = "C09"
    elif "CANALETA J" in name:
        code = "CJ{0}".format(length)
    elif "MEIA CANALETA" in name:
        code = "CM{0}".format(length)
    elif "CANALETA" in name:
        code = "CAN{0}".format(length)
    elif "CONTRAVERGA" in name:
        code = "CV{0}".format(length)
    elif "VERGA" in name:
        code = "VG{0}".format(length)
    elif "MEIO BLOCO" in name:
        code = "B19"
    elif "BLOCO 34" in name:
        code = "B34"
    elif "BLOCO 54" in name:
        code = "B54"
    elif "BLOCO INTEIRO" in name:
        code = "B39"
    else:
        code = "X{0}".format(length)
    if cut and not code.startswith(("VG", "CV")):
        code += "_C"
    return code


def role_for_type(type_name):
    """Papel deduzido do NOME DA FAMILIA. As tres primeiras perguntas usam
    `opening_audit`, que ja' define esses reconhecedores (e ja' foram
    medidos contra este mesmo projeto)."""
    name = (type_name or "").upper()
    if "CONTRAVERGA" in name:
        return model.ROLE_COUNTER_LINTEL
    if opening_audit.is_verga_or_contraverga_family_name(name):
        return model.ROLE_LINTEL
    if opening_audit.is_canaleta_family_name(name):
        return model.ROLE_CHANNEL_BLOCK
    if opening_audit.is_cortado_family_name(name):
        return model.ROLE_CUT_BLOCK
    if "PASTILHA" in name or "COMPENSADOR" in name:
        return model.ROLE_COMPENSATOR
    if "MEIO BLOCO" in name:
        return model.ROLE_HALF_BLOCK
    return model.ROLE_STANDARD


def _direction_from_rotation(rotation_deg):
    angle = math.radians(rotation_deg or 0.0)
    return math.cos(angle), math.sin(angle)


def _axis_key(center_cm, rotation_deg):
    """(angulo_do_eixo, afastamento_perpendicular) - a identidade da reta
    infinita em que a peca esta'."""
    axis_angle = model.normalize_axis_angle(rotation_deg or 0.0)
    radians = math.radians(axis_angle)
    normal = (-math.sin(radians), math.cos(radians))
    offset = center_cm[0] * normal[0] + center_cm[1] * normal[1]
    return axis_angle, offset


def group_by_course(blocks, tolerance_cm=model.COURSE_Z_TOLERANCE_CM):
    """[(z_cm, [bloco, ...])] ordenado por cota, agrupando cotas
    proximas."""
    ordered = sorted(blocks, key=lambda b: b["z_cm"])
    courses = []
    for block in ordered:
        if courses and block["z_cm"] - courses[-1][0] <= tolerance_cm:
            courses[-1][1].append(block)
        else:
            courses.append((block["z_cm"], [block]))
    return [(z, items) for z, items in courses]


def group_by_axis(blocks):
    """Agrupa as pecas por reta infinita. Guloso e determinista: percorre
    em ordem de (angulo, afastamento) e junta ao grupo aberto mais
    proximo."""
    keyed = []
    for block in blocks:
        angle, offset = _axis_key(block["center_cm"], block["rotation_deg"])
        keyed.append((angle, offset, block))
    keyed.sort(key=lambda item: (item[0], item[1]))

    groups = []
    for angle, offset, block in keyed:
        placed = False
        for group in groups:
            angle_delta = abs(group["angle"] - angle)
            angle_delta = min(angle_delta, 180.0 - angle_delta)
            if (angle_delta <= AXIS_ANGLE_TOLERANCE_DEG
                    and abs(group["offset"] - offset) <= AXIS_OFFSET_TOLERANCE_CM):
                group["blocks"].append(block)
                placed = True
                break
        if not placed:
            groups.append({"angle": angle, "offset": offset, "blocks": [block]})
    return groups


def _axis_frame(angle_deg):
    radians = math.radians(angle_deg)
    return (math.cos(radians), math.sin(radians))


def split_axis_into_walls(group):
    """Quebra um eixo em paredes, so' onde o vazio passa de
    `WALL_SPLIT_GAP_CM`. O vazio e' medido sobre a UNIAO de todas as
    fiadas: uma janela deixa buraco em algumas fiadas e nenhuma em outras,
    entao medir fiada a fiada partiria a parede a esmo."""
    direction = _axis_frame(group["angle"])
    origin = group["blocks"][0]["center_cm"]
    extents = []
    for block in group["blocks"]:
        t_center, _s = model.axial_coordinates(block["center_cm"], origin, direction)
        half = block["length_cm"] / 2.0
        extents.append((t_center - half, t_center + half, block))
    extents.sort(key=lambda item: item[0])

    segments = []
    current = [extents[0]]
    reach = extents[0][1]
    for item in extents[1:]:
        if item[0] - reach > WALL_SPLIT_GAP_CM:
            segments.append(current)
            current = []
        current.append(item)
        reach = max(reach, item[1])
    if current:
        segments.append(current)

    walls = []
    for segment in segments:
        t_lo = min(item[0] for item in segment)
        t_hi = max(item[1] for item in segment)
        if t_hi - t_lo < MIN_WALL_LENGTH_CM:
            continue
        start = (origin[0] + direction[0] * t_lo, origin[1] + direction[1] * t_lo)
        end = (origin[0] + direction[0] * t_hi, origin[1] + direction[1] * t_hi)
        walls.append({
            "start_cm": start,
            "end_cm": end,
            "direction": direction,
            "blocks": [item[2] for item in segment],
            "t_offset": t_lo,
        })
    return walls


def detect_junctions(walls):
    """Encontros entre as paredes reconstruidas.

    Um encontro e' um ponto onde a ponta de uma parede toca outra. O tipo
    sai da CONTAGEM de bracos naquele ponto, que e' a mesma definicao que
    `build_wall_graph` usa no motor: 2 bracos = L (ou continuacao, quando
    sao colineares), 3 = T, 4+ = X. Uma parede que so' termina no ar e'
    ponta livre."""
    points = []
    for index, wall in enumerate(walls):
        for end_index, point in enumerate((wall["start_cm"], wall["end_cm"])):
            points.append({"wall": index, "end": end_index, "point": point})

    # Ponta encostada no MEIO de outra parede tambem e' braco daquele no'.
    for index, wall in enumerate(walls):
        direction, length = model.direction_of(wall["start_cm"], wall["end_cm"])
        for entry in points:
            if entry["wall"] == index:
                continue
            t, s = model.axial_coordinates(entry["point"], wall["start_cm"], direction)
            if (abs(s) <= JUNCTION_TOUCH_TOLERANCE_CM
                    and JUNCTION_TOUCH_TOLERANCE_CM < t < length - JUNCTION_TOUCH_TOLERANCE_CM):
                entry.setdefault("crosses", []).append(index)

    clusters = []
    for entry in points:
        placed = False
        for cluster in clusters:
            if (abs(cluster["point"][0] - entry["point"][0]) <= JUNCTION_TOUCH_TOLERANCE_CM
                    and abs(cluster["point"][1] - entry["point"][1]) <= JUNCTION_TOUCH_TOLERANCE_CM):
                cluster["entries"].append(entry)
                placed = True
                break
        if not placed:
            clusters.append({"point": list(entry["point"]), "entries": [entry]})

    for cluster in clusters:
        ends_here = set(e["wall"] for e in cluster["entries"])
        crossing = set()
        for entry in cluster["entries"]:
            crossing.update(entry.get("crosses") or [])
        crossing -= ends_here
        walls_here = ends_here | crossing
        cluster["walls"] = sorted(walls_here)
        # BRACOS, nao paredes. Uma parede que PASSA pelo ponto (o encontro
        # cai no meio do vao dela) contribui com DOIS bracos, um para cada
        # lado; uma que TERMINA ali contribui com um. Contar paredes dava
        # 2 num T de verdade (a que chega + a que passa) e classificava
        # todo T como L - foi o que aconteceu na primeira reconstrucao
        # deste projeto: 286 "L" e nenhum T num pavimento inteiro.
        count = len(ends_here) + 2 * len(crossing)
        if count <= 1:
            cluster["type"] = model.JUNCTION_FREE_END
        elif count == 2:
            angles = []
            for wall_index in cluster["walls"]:
                angles.append(model.normalize_axis_angle(
                    model.angle_deg(model.direction_of(
                        walls[wall_index]["start_cm"], walls[wall_index]["end_cm"])[0])))
            delta = abs(angles[0] - angles[1])
            delta = min(delta, 180.0 - delta)
            cluster["type"] = (model.JUNCTION_COLLINEAR if delta <= AXIS_ANGLE_TOLERANCE_DEG
                               else model.JUNCTION_L)
        elif count == 3:
            cluster["type"] = model.JUNCTION_T
        else:
            cluster["type"] = model.JUNCTION_X
    return clusters


def build_project(dump, project_id, source="revit_reference", metadata=None):
    """Dump bruto -> projeto do benchmark (o `reference.json`)."""
    types_by_index = dict((t["index"], t) for t in dump.get("types") or [])

    raw_blocks = []
    for row in dump.get("instances") or []:
        type_index, x_cm, y_cm, z_cm, rotation_deg, mirrored = row[:6]
        entry = types_by_index.get(type_index) or {}
        length_cm = entry.get("length_cm")
        if not length_cm:
            continue
        raw_blocks.append({
            "center_cm": [float(x_cm), float(y_cm)],
            "z_cm": float(z_cm),
            "rotation_deg": float(rotation_deg),
            "mirrored": bool(mirrored),
            "length_cm": float(length_cm),
            "height_cm": entry.get("height_cm"),
            "width_cm": entry.get("width_cm") or 14.0,
            "type_name": entry.get("type_name"),
            "family": entry.get("family"),
            "code": code_for_type(entry.get("type_name"), length_cm,
                                  entry.get("height_cm")),
            "role": role_for_type(entry.get("type_name")),
        })

    axis_groups = group_by_axis(raw_blocks)
    raw_walls = []
    for group in axis_groups:
        raw_walls.extend(split_axis_into_walls(group))

    assigned = set()
    for wall in raw_walls:
        for block in wall["blocks"]:
            assigned.add(id(block))
    orphans = [b for b in raw_blocks if id(b) not in assigned]

    junction_clusters = detect_junctions(raw_walls)

    course_step = _dominant_course_step(raw_blocks)
    base_z_cm = min((b["z_cm"] for b in raw_blocks), default=0.0)

    walls = []
    for wall_index, raw_wall in enumerate(raw_walls):
        direction, length_cm = model.direction_of(raw_wall["start_cm"], raw_wall["end_cm"])
        thickness_cm = _dominant(
            [round(b["width_cm"], 1) for b in raw_wall["blocks"] if b["width_cm"]]) or 14.0

        rows = []
        courses_for_audit = []
        # O indice da fiada e' a POSICAO dela na pilha desta parede (1a,
        # 2a, 3a...), nao `(z - base) / passo`.
        #
        # Medido em TORRE EASY-LO-R00, nivel 05. TP1: alem da grade de
        # 20cm (612, 632, ... 852) existem meias-fiadas legitimas fora da
        # grade (722, 742, 762, 782, 802, 822, 842, 872) feitas de peca
        # CORTADA de 9cm - o ajuste de altura antes da canaleta de topo,
        # ja' anotado em PADRAO_MODULACAO.md ("ultima fiada ajusta ~+11cm").
        # Pelo indice de grade, 712 e 722 caiam na mesma fiada e uma
        # sobrescrevia a outra; pela ORDEM, cada fiada fisica e' uma fiada.
        for order, (z_cm, blocks_in_course) in enumerate(group_by_course(raw_wall["blocks"])):
            row_index = order
            blocks, intervals = [], []
            for block in sorted(
                    blocks_in_course,
                    key=lambda b: model.axial_coordinates(
                        b["center_cm"], raw_wall["start_cm"], direction)[0]):
                t_center, _s = model.axial_coordinates(
                    block["center_cm"], raw_wall["start_cm"], direction)
                half = block["length_cm"] / 2.0
                intervals.append((t_center - half, t_center + half,
                                  block["type_name"]))
                blocks.append(model.make_block(
                    code=block["code"],
                    length_cm=block["length_cm"],
                    center_cm=block["center_cm"],
                    z_cm=z_cm,
                    rotation_deg=block["rotation_deg"],
                    t_start_cm=t_center - half,
                    t_end_cm=t_center + half,
                    role=block["role"],
                    family=block["family"],
                    type_name=block["type_name"],
                    height_cm=block["height_cm"],
                    width_cm=block["width_cm"],
                    mirrored=block["mirrored"],
                    row=row_index,
                ))
            rows.append(model.make_row(row_index, z_cm, blocks))
            courses_for_audit.append((z_cm, intervals))

        openings = []
        for detected in opening_audit.detect_wall_openings_from_courses(courses_for_audit):
            kind = (model.OPENING_DOOR if detected["tipo_provavel"] == "PORTA"
                    else model.OPENING_WINDOW)
            openings.append(model.make_opening(
                kind,
                detected["x_range"][0], detected["x_range"][1],
                detected["z_range"][0],
                detected["z_range"][1] + course_step,
                # RECONSTRUIDO, nao medido: nao ha' porta/janela nativa
                # neste .rvt. O relatorio precisa poder dizer isso.
                confidence="reconstructed",
            ))

        junctions = []
        for cluster in junction_clusters:
            if wall_index not in cluster["walls"]:
                continue
            t_cm, _s = model.axial_coordinates(
                cluster["point"], raw_wall["start_cm"], direction)
            junctions.append({
                "type": cluster["type"],
                "t_cm": round(t_cm, 3),
                "point_cm": [round(cluster["point"][0], 3),
                             round(cluster["point"][1], 3)],
                "neighbors": [w for w in cluster["walls"] if w != wall_index],
                "at_end": bool(t_cm <= 1.0 or t_cm >= length_cm - 1.0),
            })
        junctions.sort(key=lambda item: item["t_cm"])

        walls.append(model.make_wall(
            "W{0:03d}".format(wall_index + 1),
            raw_wall["start_cm"], raw_wall["end_cm"], thickness_cm,
            base_z_cm=base_z_cm,
            height_cm=(max(r["elevation_cm"] for r in rows) + course_step - base_z_cm
                       if rows else None),
            openings=openings, junctions=junctions, rows=rows,
        ))

    catalog = {}
    for entry in dump.get("types") or []:
        if not entry.get("length_cm"):
            continue
        code = code_for_type(entry.get("type_name"), entry["length_cm"],
                             entry.get("height_cm"))
        catalog.setdefault(code, {
            "code": code,
            "length_cm": entry["length_cm"],
            "height_cm": entry.get("height_cm"),
            "width_cm": entry.get("width_cm") or 14.0,
            "is_special_bond": code in ("B34", "B54"),
            "is_compensator": code in ("C09", "C04"),
            "type_names": [],
            "count": 0,
        })
        catalog[code]["type_names"].append(entry.get("type_name"))
        catalog[code]["count"] += entry.get("count") or 0

    max_rows = max((len(wall["rows"]) for wall in walls), default=0)
    project = model.make_project(
        project_id, source, walls=walls,
        settings={
            "base_z_cm": round(base_z_cm, 3),
            "course_step_cm": round(course_step, 3),
            "num_courses": max_rows,
            "expected_rows": max_rows,
            # Os eixos daqui saem do CORPO das pecas, ja' incluindo o que
            # o motor chamaria de extensao ate' o encontro.
            "walls_already_extended": True,
        },
        catalog=catalog,
        metadata=dict(metadata or {}),
        orphan_blocks=[
            {"code": b["code"], "type_name": b["type_name"],
             "center_cm": b["center_cm"], "z_cm": b["z_cm"],
             "rotation_deg": b["rotation_deg"]}
            for b in orphans
        ],
    )
    off_grid = 0
    for block in raw_blocks:
        remainder = abs(block["z_cm"] - base_z_cm) % course_step
        if min(remainder, course_step - remainder) > model.COURSE_Z_TOLERANCE_CM:
            off_grid += 1
    project["metadata"].update({
        # Pecas em cota FORA da grade de `course_step_cm`. Nao sao erro:
        # sao as meias-fiadas de ajuste de altura (peca CORTADA) medidas
        # no projeto real. Contadas para que ninguem confunda "fiada extra
        # legitima" com "cota errada".
        "off_grid_blocks": off_grid,
        "document": dump.get("document"),
        "document_path": dump.get("document_path"),
        "level_filter": dump.get("level_filter"),
        "extracted_instances": len(dump.get("instances") or []),
        "blocks_placed": sum(len(row["blocks"]) for wall in walls
                             for row in wall["rows"]),
        "orphan_blocks": len(orphans),
        "openings_source": "reconstructed_from_blocks" if not dump.get("openings")
                           else "revit_native",
        "walls_source": "reconstructed_from_blocks" if not dump.get("walls")
                        else "revit_native",
        "dump_warnings": dump.get("warnings") or [],
    })
    return model.assign_ids(project)


def _dominant(values):
    if not values:
        return None
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]


def _dominant_course_step(blocks, default_cm=20.0, population_ratio=0.2):
    """Passo entre fiadas medido nas cotas Z reais - nao suposto.

    So' entram no calculo as cotas POVOADAS (pelo menos `population_ratio`
    da cota mais cheia). Sem esse filtro o resultado sai errado num projeto
    de verdade: as canaletas J (29cm de altura) e as vergas se apoiam em
    cotas intermediarias com 2 a 30 pecas cada, e a mediana dos deltas
    entre TODAS as cotas distintas dava 10cm num projeto cujo passo real,
    medido em 12.758 pecas, e' 20cm (o mesmo 20cm ja' registrado em
    PADRAO_MODULACAO.md para os dois projetos diagnosticados)."""
    counts = {}
    for block in blocks:
        z = round(block["z_cm"], 1)
        counts[z] = counts.get(z, 0) + 1
    if not counts:
        return default_cm
    threshold = max(counts.values()) * population_ratio
    z_values = sorted(z for z, count in counts.items() if count >= threshold)
    deltas = [round(z_values[i + 1] - z_values[i], 1)
              for i in range(len(z_values) - 1)]
    deltas = [d for d in deltas if d > 1.0]
    return _dominant(deltas) or default_cm


def input_from_reference(reference_project, project_id=None):
    """`input.json` a partir do gabarito: o MESMO problema (eixos, vaos,
    catalogo, pe-direito), com zero peca colocada.

    E' o que fecha o ciclo do item 1 - o solver recebe exatamente a planta
    que a pessoa recebeu, e o gabarito fica guardado para a comparacao."""
    project = model.make_project(
        project_id or reference_project["project_id"], "input",
        walls=[
            model.make_wall(
                wall["id"], wall["start_cm"], wall["end_cm"], wall["thickness_cm"],
                base_z_cm=wall["base_z_cm"], height_cm=wall["height_cm"],
                openings=[dict(o) for o in wall.get("openings") or []],
                junctions=[dict(j) for j in wall.get("junctions") or []],
                rows=[],
            )
            for wall in reference_project.get("walls") or []
        ],
        settings=dict(reference_project.get("settings") or {}),
        catalog=dict(reference_project.get("catalog") or {}),
        metadata=dict(reference_project.get("metadata") or {}),
    )
    project["metadata"]["derived_from"] = "reference.json"
    return model.assign_ids(project)
