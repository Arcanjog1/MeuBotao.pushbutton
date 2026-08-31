# -*- coding: utf-8 -*-
"""Modelo de dados do benchmark - o formato UNICO que tanto o projeto
humano (extraido do Revit) quanto o resultado do solver produzem.

Por que um formato so': o comparador e os validadores nunca podem saber
de ONDE veio o que estao lendo. Se o gabarito e o resultado tivessem
schemas diferentes, cada validador teria dois caminhos de codigo e a
comparacao viraria adivinhacao. Aqui os dois lados sao o MESMO dict.

UNIDADES: centimetro e grau, sempre. Coordenadas sao as do projeto
(planta), nao locais da parede - o eixo da parede aparece a parte, em
`t_start_cm`/`t_end_cm` de cada bloco, porque e' nele que quase toda
regra de modulacao e' escrita (junta vertical, cobertura, vao).

IDENTIDADE (item 4 do pedido): NENHUM ElementId do Revit e' usado como
chave. `ElementId` muda entre arquivos, entre execucoes e some quando as
paredes de referencia sao apagadas (que e' exatamente o que o processo
real faz). As chaves aqui sao GEOMETRICAS e RELACIONAIS - ver
`wall_stable_key`/`opening_stable_key`/`block_stable_key`. O ElementId,
quando existe, e' guardado so' como `source_element_id`, informativo.

Modulo 100% PURO: nenhuma dependencia do Revit nem do motor. Roda em
qualquer Python.
"""

import json
import math

SCHEMA_VERSION = 2

# ---------------------------------------------------------------- papeis
#
# Taxonomia de FUNCAO de cada bloco (item 3 do pedido). Vale para os dois
# lados: o solver preenche a partir de `placement_reason`, a extracao do
# Revit a partir do nome da familia + geometria. Uma peca so' tem UM
# papel; quando duas leituras cabem, vence a mais especifica (ex.: uma
# canaleta num encontro L e' `channel_block`, nao `L_binding` - a
# informacao de amarracao continua em `junction_role`).
ROLE_STANDARD = "standard"
ROLE_L_BINDING = "L_binding"
ROLE_T_BINDING = "T_binding"
ROLE_CROSS_BINDING = "cross_binding"
ROLE_OPENING_ADJUSTMENT = "opening_adjustment"
ROLE_COMPENSATOR = "compensator"
ROLE_HALF_BLOCK = "half_block"
ROLE_CHANNEL_BLOCK = "channel_block"
ROLE_LINTEL = "lintel"
ROLE_COUNTER_LINTEL = "counter_lintel"
ROLE_CUT_BLOCK = "cut_block"
ROLE_UNKNOWN = "unknown"

ALL_ROLES = (
    ROLE_STANDARD, ROLE_L_BINDING, ROLE_T_BINDING, ROLE_CROSS_BINDING,
    ROLE_OPENING_ADJUSTMENT, ROLE_COMPENSATOR, ROLE_HALF_BLOCK,
    ROLE_CHANNEL_BLOCK, ROLE_LINTEL, ROLE_COUNTER_LINTEL, ROLE_CUT_BLOCK,
    ROLE_UNKNOWN,
)

# Papeis que representam AMARRACAO de encontro (usados pelo validador de
# amarracao e pelo aprendizado de padroes).
BINDING_ROLES = (ROLE_L_BINDING, ROLE_T_BINDING, ROLE_CROSS_BINDING)

# ------------------------------------------------------------- encontros
JUNCTION_L = "L"
JUNCTION_T = "T"
JUNCTION_X = "X"
JUNCTION_FREE_END = "FREE_END"
JUNCTION_COLLINEAR = "COLLINEAR"
ALL_JUNCTION_TYPES = (JUNCTION_L, JUNCTION_T, JUNCTION_X, JUNCTION_FREE_END,
                      JUNCTION_COLLINEAR)

OPENING_DOOR = "door"
OPENING_WINDOW = "window"

# ----------------------------------------------------------- tolerancias
#
# Todas em cm. Escolhidas a partir das que o motor ja usa (ver
# core/engine/tolerances.py e modulation_math.py) - nao inventadas aqui.
# O benchmark le' GEOMETRIA MEDIDA (do Revit) e geometria CALCULADA (do
# solver): as duas nunca batem no ultimo decimal, entao toda comparacao
# passa por uma destas.

# Grade de arredondamento das chaves estaveis. 0,5cm e' menor que
# qualquer diferenca fisica que importe (a menor peca do catalogo tem
# 4cm) e maior que o ruido de conversao pes<->cm.
STABLE_ID_GRID_CM = 0.5

# Duas paredes sao "a mesma parede" se as pontas casarem dentro disto.
# 5cm = metade da menor peca util; abaixo disso duas paredes distintas
# nunca ficariam.
WALL_MATCH_TOLERANCE_CM = 5.0

# Distancia perpendicular maxima do centro de um bloco ao eixo da parede
# pra ele ser considerado DAQUELA parede. Meia espessura (7cm de uma
# parede de 14) + folga.
BLOCK_TO_WALL_PERP_TOLERANCE_CM = 9.0

# Duas juntas verticais estao "alinhadas" (regra do prisma) quando os
# centros distam menos que isto. Mesmo valor de
# BOND_JOINT_CLUSTER_TOLERANCE_CM no motor.
JOINT_ALIGNMENT_TOLERANCE_CM = 1.5

# Sobreposicao de volume abaixo disto e' ruido de arredondamento, nao
# colisao (regra 18.7 do REGRAS_MODULACAO_BLOCOS.md usa 0,1cm).
OVERLAP_TOLERANCE_CM = 0.1

# Vazio entre duas pecas vizinhas ate' aqui e' JUNTA de assentamento
# (1cm medido em projeto real), acima disso e' buraco.
MAX_ADJACENT_GAP_CM = 3.0

# Fiadas (cotas Z) mais proximas que isto sao a MESMA fiada.
COURSE_Z_TOLERANCE_CM = 2.0


def _snap(value, grid=STABLE_ID_GRID_CM):
    return round(round(float(value) / grid) * grid, 3)


def _fmt(value):
    """Numero -> texto canonico para chave estavel (sem '-0.0', sem
    notacao cientifica, sempre 1 casa)."""
    snapped = _snap(value)
    if abs(snapped) < 1e-9:
        snapped = 0.0
    return "{0:.1f}".format(snapped)


# --------------------------------------------------------------- chaves
def canonical_segment(start_cm, end_cm):
    """Ordem canonica das pontas de um segmento: a ponta menor em (x, y)
    vem primeiro. Sem isso a MESMA parede desenhada no sentido contrario
    geraria outra chave - e o gabarito nunca casaria com o resultado."""
    a = (float(start_cm[0]), float(start_cm[1]))
    b = (float(end_cm[0]), float(end_cm[1]))
    if (_snap(a[0]), _snap(a[1])) <= (_snap(b[0]), _snap(b[1])):
        return a, b
    return b, a


def wall_stable_key(start_cm, end_cm, thickness_cm):
    """Chave GEOMETRICA de uma parede - nunca o ElementId (item 4).

    Nao e' usada para CASAR gabarito x resultado (isso e'
    `comparator.match`, com tolerancia): serve para dar a mesma parede o
    mesmo nome em execucoes diferentes do MESMO lado, deixando os
    relatorios comparaveis linha a linha."""
    a, b = canonical_segment(start_cm, end_cm)
    return "W|{0},{1}|{2},{3}|t{4}".format(
        _fmt(a[0]), _fmt(a[1]), _fmt(b[0]), _fmt(b[1]), _fmt(thickness_cm)
    )


def opening_stable_key(wall_key, t_start_cm, t_end_cm, sill_cm):
    """Chave de abertura: parede + posicao NO EIXO da parede + peitoril.
    Usar a coordenada axial (e nao a XY do mundo) e' o que mantem a chave
    valida quando a parede inteira e' deslocada alguns centimetros pelo
    ajuste automatico (Etapa 3B/3C)."""
    return "{0}|O|{1}-{2}|s{3}".format(
        wall_key, _fmt(t_start_cm), _fmt(t_end_cm), _fmt(sill_cm)
    )


def block_stable_key(wall_key, row_index, t_start_cm):
    """Chave de bloco: parede + fiada + inicio no eixo. Deliberadamente
    NAO inclui o codigo da peca: assim, quando o solver troca um B39 por
    dois B19 no mesmo lugar, o comparador ve' uma peca DIFERENTE no mesmo
    ponto (informacao util) em vez de duas pecas sem relacao."""
    return "{0}|R{1}|{2}".format(wall_key, int(row_index), _fmt(t_start_cm))


# ------------------------------------------------------------- geometria
def direction_of(start_cm, end_cm):
    dx = float(end_cm[0]) - float(start_cm[0])
    dy = float(end_cm[1]) - float(start_cm[1])
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return (1.0, 0.0), 0.0
    return (dx / length, dy / length), length


def axial_coordinates(point_cm, origin_cm, direction):
    """(t, s): distancia AO LONGO do eixo e distancia PERPENDICULAR a ele,
    ambas em cm e com sinal."""
    dx = float(point_cm[0]) - float(origin_cm[0])
    dy = float(point_cm[1]) - float(origin_cm[1])
    t = dx * direction[0] + dy * direction[1]
    s = -dx * direction[1] + dy * direction[0]
    return t, s


def angle_deg(direction):
    return math.degrees(math.atan2(direction[1], direction[0])) % 360.0


def normalize_axis_angle(deg):
    """Angulo de EIXO (nao de vetor): 0 e 180 graus sao a mesma direcao.
    Devolve sempre [0, 180)."""
    return float(deg) % 180.0


# -------------------------------------------------------- construtores
def make_block(code, length_cm, center_cm, z_cm, rotation_deg,
               t_start_cm, t_end_cm, role=ROLE_UNKNOWN, family=None,
               type_name=None, height_cm=None, width_cm=None,
               mirrored=False, wall_id=None, secondary_wall_id=None,
               row=None, source_element_id=None, placement_reason=None):
    return {
        "code": code,
        "family": family,
        "type_name": type_name,
        "length_cm": round(float(length_cm), 3),
        "height_cm": None if height_cm is None else round(float(height_cm), 3),
        "width_cm": None if width_cm is None else round(float(width_cm), 3),
        "center_cm": [round(float(center_cm[0]), 3), round(float(center_cm[1]), 3)],
        "z_cm": round(float(z_cm), 3),
        "rotation_deg": round(float(rotation_deg) % 360.0, 3),
        "mirrored": bool(mirrored),
        "t_start_cm": round(float(t_start_cm), 3),
        "t_end_cm": round(float(t_end_cm), 3),
        "role": role,
        "wall_id": wall_id,
        "secondary_wall_id": secondary_wall_id,
        "row": row,
        "source_element_id": source_element_id,
        "placement_reason": placement_reason,
    }


def make_opening(kind, t_start_cm, t_end_cm, sill_cm, head_cm,
                 source_element_id=None, confidence="measured"):
    return {
        "kind": kind,
        "t_start_cm": round(float(t_start_cm), 3),
        "t_end_cm": round(float(t_end_cm), 3),
        "width_cm": round(float(t_end_cm) - float(t_start_cm), 3),
        "sill_cm": round(float(sill_cm), 3),
        "head_cm": round(float(head_cm), 3),
        "height_cm": round(float(head_cm) - float(sill_cm), 3),
        "source_element_id": source_element_id,
        # "measured" = lido de uma porta/janela real do Revit;
        # "reconstructed" = deduzido do vazio deixado pelos blocos (o caso
        # dos projetos ja entregues, onde as portas/janelas foram
        # apagadas junto com as paredes de referencia).
        "confidence": confidence,
    }


def make_wall(wall_id, start_cm, end_cm, thickness_cm, base_z_cm=0.0,
              height_cm=None, openings=None, junctions=None, rows=None,
              source_element_ids=None):
    direction, length = direction_of(start_cm, end_cm)
    return {
        "id": wall_id,
        "key": wall_stable_key(start_cm, end_cm, thickness_cm),
        "start_cm": [round(float(start_cm[0]), 3), round(float(start_cm[1]), 3)],
        "end_cm": [round(float(end_cm[0]), 3), round(float(end_cm[1]), 3)],
        "length_cm": round(length, 3),
        "angle_deg": round(angle_deg(direction), 3),
        "thickness_cm": round(float(thickness_cm), 3),
        "base_z_cm": round(float(base_z_cm), 3),
        "height_cm": None if height_cm is None else round(float(height_cm), 3),
        "openings": list(openings or []),
        "junctions": list(junctions or []),
        "rows": list(rows or []),
        "source_element_ids": list(source_element_ids or []),
    }


def make_row(index, elevation_cm, blocks=None):
    return {
        "row": int(index),
        "elevation_cm": round(float(elevation_cm), 3),
        "blocks": list(blocks or []),
    }


def make_project(project_id, source, walls=None, settings=None, catalog=None,
                 metadata=None, orphan_blocks=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        # "revit_reference" (projeto humano correto), "solver" (resultado
        # gerado) ou "synthetic" (plantas construidas nos testes).
        "source": source,
        "settings": dict(settings or {}),
        "catalog": dict(catalog or {}),
        "walls": list(walls or []),
        # Pecas que nao puderam ser atribuidas a nenhuma parede. NUNCA
        # descartadas em silencio: um monte de blocos orfaos e' sinal de
        # que a reconstrucao de eixos falhou, e o relatorio precisa dizer.
        "orphan_blocks": list(orphan_blocks or []),
        "metadata": dict(metadata or {}),
    }


# ----------------------------------------------------------- utilitarios
def iter_blocks(project):
    for wall in project.get("walls") or []:
        for row in wall.get("rows") or []:
            for block in row.get("blocks") or []:
                yield wall, row, block


def count_blocks(project):
    return sum(1 for _ in iter_blocks(project))


def wall_by_id(project, wall_id):
    for wall in project.get("walls") or []:
        if wall.get("id") == wall_id:
            return wall
    return None


def rows_sorted(wall):
    return sorted(wall.get("rows") or [], key=lambda r: r["row"])


def blocks_sorted(row):
    return sorted(row.get("blocks") or [], key=lambda b: b["t_start_cm"])


def assign_ids(project):
    """Da nome definitivo (W001, W001-O01, W001-R00-B003) a tudo, na
    ordem geometrica - determinista, para o relatorio de hoje ser
    comparavel com o de amanha."""
    walls = sorted(
        project.get("walls") or [],
        key=lambda w: (round(w["start_cm"][1], 1), round(w["start_cm"][0], 1),
                       round(w["end_cm"][1], 1), round(w["end_cm"][0], 1)),
    )
    for w_index, wall in enumerate(walls):
        wall["id"] = "W{0:03d}".format(w_index + 1)
        wall["key"] = wall_stable_key(wall["start_cm"], wall["end_cm"], wall["thickness_cm"])
        wall["openings"] = sorted(wall.get("openings") or [], key=lambda o: o["t_start_cm"])
        for o_index, opening in enumerate(wall["openings"]):
            opening["id"] = "{0}-O{1:02d}".format(wall["id"], o_index + 1)
            opening["key"] = opening_stable_key(
                wall["key"], opening["t_start_cm"], opening["t_end_cm"], opening["sill_cm"]
            )
        for row in rows_sorted(wall):
            row["blocks"] = blocks_sorted(row)
            for b_index, block in enumerate(row["blocks"]):
                block["wall_id"] = wall["id"]
                block["row"] = row["row"]
                block["id"] = "{0}-R{1:02d}-B{2:03d}".format(
                    wall["id"], row["row"], b_index + 1
                )
                block["key"] = block_stable_key(wall["key"], row["row"], block["t_start_cm"])
        wall["rows"] = rows_sorted(wall)
    project["walls"] = walls
    return project


def save(project, path):
    """Grava o projeto.

    UMA LINHA POR PAREDE, e nao um `indent` global: um pavimento real tem
    ~12 mil pecas, e indentar tudo custa 3MB so' de espaco em branco (9,0
    contra 5,8MB medidos no projeto piloto). Uma linha por parede mantem o
    arquivo legivel e, mais importante, mantem o `git diff` util - mexer
    numa parede muda uma linha, nao o arquivo inteiro."""
    walls = project.get("walls") or []
    head = dict((k, v) for k, v in project.items() if k != "walls")
    parts = [json.dumps(head, ensure_ascii=False, indent=1)[:-2]]
    parts.append(',\n "walls": [\n')
    parts.append(",\n".join(
        "  " + json.dumps(wall, ensure_ascii=False, separators=(",", ":"))
        for wall in walls
    ))
    parts.append("\n ]\n}\n")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(parts))
    return path


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        project = json.load(handle)
    version = project.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(
            "schema_version {0} em {1}; este codigo le' {2}. Reextraia o "
            "projeto em vez de editar o JSON a mao.".format(
                version, path, SCHEMA_VERSION)
        )
    return project
