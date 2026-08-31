# -*- coding: utf-8 -*-
"""EVALUATION SCOPE: onde existe gabarito humano para comparar.

Etapa 2B.1 (pedido do usuario, 2026-08-31). O problema medido: o Wall
Modeling sobre o CAD cru forma 167 paredes; a pessoa modulou 97. O layer
`Arquitetura` cobre area MAIOR que a regiao que o projetista de fato
modulou. Chamar as 70 paredes a mais de "erro do solver" seria falso - nao
existe gabarito naquela regiao para dizer que estao erradas.

Entao separam-se dois escopos:

  EXECUTION SCOPE  - o INPUT INTEIRO. O solver roda sobre tudo, sempre.
  EVALUATION SCOPE - a regiao onde ha' modulacao humana, e portanto onde a
                     comparacao com o gabarito significa alguma coisa.

REGRA INEGOCIAVEL: o evaluation_scope **nunca** entra na entrada do solver.
Ele e' aplicado DEPOIS, sobre o resultado. O fluxo correto e'

    INPUT COMPLETO -> SOLVER -> RESULTADO COMPLETO
    RESULTADO COMPLETO + evaluation_scope  <->  REFERENCE

e nunca `REFERENCE -> recortar INPUT -> SOLVER`, que vazaria o gabarito
para a execucao (era exatamente o vicio que a Etapa 2B.1 veio corrigir no
catalogo).

COMO O ESCOPO E' DERIVADO (geometrico e auditavel)
--------------------------------------------------
Rasteriza-se a ocupacao da modulacao humana numa grade quadrada: cada peca
do gabarito marca as celulas que o seu retangulo cobre. Depois a mascara e'
DILATADA por uma margem, para que uma parede do solver ligeiramente
deslocada (ou uma ponta esticada ate' um encontro) continue contando como
"dentro da regiao com gabarito" - a dilatacao existe para nao punir o
solver por milimetros, nunca para esticar o escopo sobre regiao que a
pessoa nao modulou.

Uma parede do resultado e' INSIDE quando pelo menos `min_coverage` da sua
extensao cai em celula ocupada. Nem centro, nem bbox: FRACAO DA EXTENSAO -
uma parede de 15m que so' encosta no gabarito pela ponta nao pode ser
avaliada como se tivesse gabarito inteiro.

Tudo o que define o escopo (tamanho de celula, dilatacao, limiar, e a
propria lista de celulas) e' gravado em `evaluation_scope.json`: outra
pessoa refaz a classificacao sem precisar rodar nada.
"""

import datetime
import json
import math

# 25cm: menor que a menor peca comum (B34/B39) e divisor exato do passo de
# 20cm nao e' requisito - o que importa e' a celula ser menor que a peca,
# senao uma unica peca marcaria uma area muito maior que a que ocupa.
DEFAULT_CELL_CM = 25.0

# 75cm de dilatacao = 3 celulas. Cobre a maior extensao de ponta que
# `extend_wall_ends_to_junctions` acrescenta (uma espessura de parede por
# ponta, 14cm) com folga larga, sem chegar perto de atravessar um comodo.
DEFAULT_DILATION_CM = 75.0

# Metade da extensao dentro da mascara. Abaixo disso a parede esta' mais
# fora do que dentro, e comparar o trecho de dentro sozinho daria uma
# leitura enganosa.
DEFAULT_MIN_COVERAGE = 0.5

# Amostragem ao longo do eixo da parede ao classificar.
SAMPLE_STEP_CM = 10.0

# --- SEGUNDO CRITERIO: SUPORTE DE EIXO ---------------------------------
# A mascara de ocupacao sozinha NAO basta, e isso foi medido (2026-08-31):
# das 167 paredes que o Wall Modeling formou, 164 tem 100% da extensao
# dentro da mascara. O comprimento total das duas leituras bate a 5%
# (43.033 cm contra 45.363 cm) e 96,5% da extensao dos eixos do input cai a
# <= 15cm de um eixo do gabarito. Ou seja: a diferenca 167 x 97 NAO e'
# regiao a mais - e' FRAGMENTACAO (mediana 169cm contra 269cm) mais uma
# cauda de lascas de 8 a 16cm.
#
# Essas lascas ficam DENTRO da area modulada, entao nenhuma mascara
# espacial as separa. O que as separa e' nao existir eixo humano onde elas
# estao: sao artefato do pareamento de linhas do CAD (FASE A), nao peca mal
# escolhida pelo solver. Por isso o escopo exige TAMBEM que a parede tenha
# eixo de gabarito por baixo.
#
# 15cm ~ uma espessura de parede: cobre o desencontro normal entre o eixo
# calculado e o eixo reconstruido do gabarito, sem aceitar uma parede que
# esteja num lugar onde a pessoa nao modulou nada.
DEFAULT_AXIS_TOLERANCE_CM = 15.0
DEFAULT_MIN_AXIS_SUPPORT = 0.5


def _cell(x_cm, y_cm, cell_cm):
    return (int(math.floor(x_cm / cell_cm)), int(math.floor(y_cm / cell_cm)))


def _reference_blocks(reference):
    for wall in reference.get("walls") or []:
        for row in wall.get("rows") or []:
            for block in row.get("blocks") or []:
                yield block
    for block in reference.get("orphan_blocks") or []:
        yield block


def build_scope(reference, cell_cm=DEFAULT_CELL_CM,
                dilation_cm=DEFAULT_DILATION_CM,
                min_coverage=DEFAULT_MIN_COVERAGE,
                axis_tolerance_cm=DEFAULT_AXIS_TOLERANCE_CM,
                min_axis_support=DEFAULT_MIN_AXIS_SUPPORT):
    """Gabarito humano -> mascara de celulas ocupadas + parametros.

    A peca e' marcada pelo retangulo `length_cm x width_cm` girado por
    `rotation_deg` em torno de `center_cm` - nao so' pelo centro, senao uma
    peca de 54cm marcaria uma celula de 25cm e deixaria buraco na mascara."""
    occupied = set()
    blocks_used = 0
    for block in _reference_blocks(reference):
        center = block.get("center_cm")
        if not center:
            continue
        blocks_used += 1
        length = float(block.get("length_cm") or 0.0)
        width = float(block.get("width_cm") or 14.0)
        angle = math.radians(float(block.get("rotation_deg") or 0.0))
        ux, uy = math.cos(angle), math.sin(angle)
        vx, vy = -uy, ux
        # Passo de meia celula nas duas direcoes locais: garante que
        # nenhuma celula interna ao retangulo fique sem marcar.
        steps_u = max(1, int(math.ceil(length / (cell_cm / 2.0))))
        steps_v = max(1, int(math.ceil(width / (cell_cm / 2.0))))
        for i in range(steps_u + 1):
            du = -length / 2.0 + length * i / float(steps_u)
            for j in range(steps_v + 1):
                dv = -width / 2.0 + width * j / float(steps_v)
                occupied.add(_cell(center[0] + du * ux + dv * vx,
                                   center[1] + du * uy + dv * vy, cell_cm))

    core_count = len(occupied)

    radius = int(math.ceil(dilation_cm / cell_cm))
    dilated = set(occupied)
    for (cx, cy) in occupied:
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    dilated.add((cx + dx, cy + dy))

    cells = sorted(dilated)
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return {
        "schema_version": 1,
        "generated_at": datetime.datetime.now().isoformat(),
        "derived_from": "reference.json (modulacao humana)",
        "purpose": "define APENAS onde existe gabarito humano para comparar; "
                   "NUNCA entra na entrada do solver",
        "frame": reference.get("metadata", {}).get("frame"),
        "params": {
            "cell_cm": cell_cm,
            "dilation_cm": dilation_cm,
            "min_coverage": min_coverage,
            "sample_step_cm": SAMPLE_STEP_CM,
            "axis_tolerance_cm": axis_tolerance_cm,
            "min_axis_support": min_axis_support,
        },
        "criteria": [
            "occupancy: >= min_coverage da extensao dentro da mascara de celulas",
            "axis_support: >= min_axis_support da extensao a <= axis_tolerance_cm "
            "de um eixo de parede do gabarito",
        ],
        "stats": {
            "reference_blocks_used": blocks_used,
            "core_cells": core_count,
            "dilated_cells": len(cells),
            "reference_axes": len(reference.get("walls") or []),
            "bbox_cm": [min(xs) * cell_cm, min(ys) * cell_cm,
                        (max(xs) + 1) * cell_cm, (max(ys) + 1) * cell_cm] if cells else None,
        },
        "cells": [[c[0], c[1]] for c in cells],
        # Eixos do gabarito, gravados junto para a classificacao ser
        # refazivel sem abrir o reference.json inteiro (9 MB).
        "axis_segments_cm": [
            [wall["start_cm"][0], wall["start_cm"][1],
             wall["end_cm"][0], wall["end_cm"][1]]
            for wall in (reference.get("walls") or [])
        ],
    }


def _cell_set(scope):
    return set((int(a), int(b)) for a, b in scope["cells"])


def _distance_point_segment(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-9:
        return math.hypot(px - x0, py - y0)
    t = ((px - x0) * dx + (py - y0) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def wall_coverage(scope, wall, cells=None):
    """`(occupancy, axis_support)` - as duas fracoes da extensao do eixo:
    quanto cai dentro da mascara, e quanto tem eixo do gabarito por baixo."""
    cells = cells if cells is not None else _cell_set(scope)
    cell_cm = float(scope["params"]["cell_cm"])
    step = float(scope["params"].get("sample_step_cm") or SAMPLE_STEP_CM)
    axis_tolerance = float(scope["params"].get("axis_tolerance_cm")
                           or DEFAULT_AXIS_TOLERANCE_CM)
    axes = scope.get("axis_segments_cm") or []

    x0, y0 = wall["start_cm"]
    x1, y1 = wall["end_cm"]
    length = math.hypot(x1 - x0, y1 - y0)
    samples = max(2, int(math.ceil(length / step)) + 1)
    inside = 0
    supported = 0
    for i in range(samples):
        t = i / float(samples - 1)
        px = x0 + t * (x1 - x0)
        py = y0 + t * (y1 - y0)
        if _cell(px, py, cell_cm) in cells:
            inside += 1
        for ax0, ay0, ax1, ay1 in axes:
            if _distance_point_segment(px, py, ax0, ay0, ax1, ay1) <= axis_tolerance:
                supported += 1
                break
    return inside / float(samples), supported / float(samples)


def classify_walls(scope, project):
    """Rotula TODA parede do projeto - nunca remove nada aqui.

    `inside` exige os DOIS criterios (ver o cabecalho e a nota de
    `DEFAULT_AXIS_TOLERANCE_CM`): estar na regiao modulada E ter eixo de
    gabarito por baixo. `reason` diz qual criterio reprovou, para o
    resultado ser auditavel parede a parede."""
    cells = _cell_set(scope)
    min_coverage = float(scope["params"]["min_coverage"])
    min_axis_support = float(scope["params"].get("min_axis_support")
                             or DEFAULT_MIN_AXIS_SUPPORT)
    out = {}
    for wall in project.get("walls") or []:
        occupancy, axis_support = wall_coverage(scope, wall, cells)
        ok_occupancy = occupancy >= min_coverage
        ok_axis = axis_support >= min_axis_support
        if ok_occupancy and ok_axis:
            reason = "inside"
        elif not ok_occupancy and not ok_axis:
            reason = "fora_da_regiao_modulada_e_sem_eixo_de_gabarito"
        elif not ok_occupancy:
            reason = "fora_da_regiao_modulada"
        else:
            reason = "sem_eixo_de_gabarito_por_baixo"
        out[wall["id"]] = {
            "inside": ok_occupancy and ok_axis,
            "coverage": round(occupancy, 4),
            "axis_support": round(axis_support, 4),
            "length_cm": wall.get("length_cm"),
            "reason": reason,
        }
    return out


def scoped_project(project, classification):
    """Copia do projeto com SOMENTE as paredes de dentro do escopo.

    Copia rasa de proposito: as paredes nao sao alteradas, so' filtradas.
    O projeto ORIGINAL (completo) continua sendo o resultado oficial do
    solver - este recorte serve so' para a metrica SCOPED."""
    scoped = dict(project)
    scoped["walls"] = [w for w in (project.get("walls") or [])
                       if classification.get(w["id"], {}).get("inside")]
    metadata = dict(project.get("metadata") or {})
    metadata["evaluation_scope"] = {
        "applied": True,
        "walls_kept": len(scoped["walls"]),
        "walls_dropped": len(project.get("walls") or []) - len(scoped["walls"]),
        "note": "recorte usado SO' para a metrica SCOPED; o resultado "
                "oficial do solver e' o projeto completo",
    }
    scoped["metadata"] = metadata
    return scoped


def summarize(scope, result_project, reference_project):
    """Os numeros que o relatorio pede (item 8): total, dentro, fora, e o
    tamanho do gabarito. Paredes de fora NUNCA sao escondidas - so' nao sao
    chamadas de erro."""
    result_class = classify_walls(scope, result_project)
    reference_class = classify_walls(scope, reference_project)
    inside = [wid for wid, info in result_class.items() if info["inside"]]
    outside = [wid for wid, info in result_class.items() if not info["inside"]]
    return {
        "walls_total_solver": len(result_project.get("walls") or []),
        "walls_inside_evaluation_scope": len(inside),
        "walls_outside_evaluation_scope": len(outside),
        "reference_walls": len(reference_project.get("walls") or []),
        "reference_walls_inside_scope": sum(
            1 for info in reference_class.values() if info["inside"]),
        "outside_wall_ids": sorted(outside),
        "outside_by_reason": _count_by_reason(result_class),
        "outside_total_length_cm": round(sum(
            float(result_class[wid].get("length_cm") or 0.0) for wid in outside), 1),
        "inside_total_length_cm": round(sum(
            float(result_class[wid].get("length_cm") or 0.0) for wid in inside), 1),
        "outside_walls": sorted(
            ({"id": wid} for wid in outside),
            key=lambda item: item["id"]),
        "classification": result_class,
    }


def _count_by_reason(classification):
    counts = {}
    for info in classification.values():
        if info["inside"]:
            continue
        counts[info["reason"]] = counts.get(info["reason"], 0) + 1
    return counts


def save(scope, path):
    """Grava `evaluation_scope.json` de forma COMPACTA para os dois arrays
    grandes (`cells`, `axis_segments_cm`) - um pavimento real tem milhares
    de celulas, e `json.dump(indent=1)` genérico gasta uma linha por
    numero (2 numeros por celula). Compactar esses dois campos (uma linha
    por lista inteira, sem indentacao) e manter o resto legivel e' a mesma
    ideia de `model.save()`, aplicada aqui porque o payload nao tem uma
    lista dominante unica chamada `walls`.

    Medido no primeiro commit real: 229,6 KB / 35.069 linhas -> ~75 KB /
    poucas dezenas de linhas, MESMO conteudo."""
    body = dict(scope)
    cells = body.pop("cells", None)
    axes = body.pop("axis_segments_cm", None)

    parts = [json.dumps(body, ensure_ascii=False, indent=1)[:-2]]
    if cells is not None:
        parts.append(',\n "cells": ')
        parts.append(json.dumps(cells, ensure_ascii=False, separators=(",", ":")))
    if axes is not None:
        parts.append(',\n "axis_segments_cm": ')
        parts.append(json.dumps(axes, ensure_ascii=False, separators=(",", ":")))
    parts.append("\n}\n")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(parts))
    return path
