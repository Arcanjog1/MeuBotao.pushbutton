# -*- coding: utf-8 -*-
"""AMARRACOES - L, T, cruz, ponta livre e boneca.

POR QUE ESTE VALIDADOR OLHA O NO', E NAO A PAREDE
-------------------------------------------------
A primeira versao deste arquivo perguntava, parede por parede, "esta
parede tem peca em cima do no'?" - e reprovou 120 encontros de uma planta
sintetica que estava CERTA. O motivo e' a propria definicao de amarracao:
num canto L, a fiada A tem o B34 numa das paredes e a fiada B tem o B34 na
OUTRA. Olhando so' uma parede por vez, metade das fiadas parece vazia.

Entao a unidade de analise aqui e' o NO', com todas as paredes que chegam
nele. Uma peca "ocupa o no'" quando o corpo dela (comprimento x largura,
na rotacao real) alcanca o ponto do encontro - calculo geometrico, nao
`wall_idx`, porque justamente a peca que amarra e' a que invade a parede
vizinha.

O que e' cobrado:

1. `JUNCTION_MISSING_BINDING` (nivel 1) - alguma fiada em que NENHUMA
   parede do no' pos peca no encontro.
2. `JUNCTION_NOT_ALTERNATING` (nivel 1) - fiadas consecutivas resolvem o
   no' com a mesma peca na mesma parede: a amarracao nao troca de sentido
   e o encontro vira junta corrida vertical (secao 18.4).
3. `JUNCTION_HALF_BLOCK_ADJACENT` (nivel 1) - meio-bloco encostado na
   amarracao (regra #2 / secao 11.6).
4. `JUNCTION_WRONG_PIECE` (NIVEL 2) - peca diferente da que o projetista
   usou no mesmo tipo de encontro. Nunca reprova.
"""

import math

from .. import analysis
from .. import model
from . import base

# Folga somada a meia largura da peca ao testar se ela alcanca o ponto do
# no'. Uma junta de assentamento.
JUNCTION_REACH_TOLERANCE_CM = analysis.BLOCK_JOINT_CM

# Distancia maxima entre o CORPO de um meio-bloco e o ponto do encontro
# para valer a regra #2 - `HALF_BLOCK_TIE_ADJACENCY_CM` no motor.
HALF_BLOCK_TIE_ADJACENCY_CM = analysis.BLOCK_JOINT_CM + 0.05

# Dois nos a menos que isto um do outro sao o MESMO no' visto por paredes
# diferentes (cada parede guarda a sua propria copia).
NODE_MERGE_TOLERANCE_CM = 3.0

BINDING_JUNCTION_TYPES = (model.JUNCTION_L, model.JUNCTION_T, model.JUNCTION_X)


def block_covers_point(block, point_cm, tolerance_cm=JUNCTION_REACH_TOLERANCE_CM):
    """A peca alcanca `point_cm`? Testa o retangulo real da peca
    (comprimento x largura, girado por `rotation_deg`), nao a caixa
    alinhada aos eixos - num encontro a 45 graus a diferenca e' de uma
    peca inteira."""
    angle = math.radians(block.get("rotation_deg") or 0.0)
    ux, uy = math.cos(angle), math.sin(angle)
    dx = float(point_cm[0]) - block["center_cm"][0]
    dy = float(point_cm[1]) - block["center_cm"][1]
    along = dx * ux + dy * uy
    across = -dx * uy + dy * ux
    half_length = (block.get("length_cm") or 0.0) / 2.0
    half_width = (block.get("width_cm") or 14.0) / 2.0
    return (abs(along) <= half_length + tolerance_cm
            and abs(across) <= half_width + tolerance_cm)


def collect_nodes(project):
    """Agrupa os encontros que as paredes declaram num unico no' por
    ponto. Devolve `[{"point_cm", "type", "walls": [(wall, junction)]}]`."""
    groups = []
    for wall in project.get("walls") or []:
        for junction in wall.get("junctions") or []:
            point = junction.get("point_cm")
            if point is None:
                continue
            placed = False
            for group in groups:
                if (abs(group["point_cm"][0] - point[0]) <= NODE_MERGE_TOLERANCE_CM
                        and abs(group["point_cm"][1] - point[1]) <= NODE_MERGE_TOLERANCE_CM):
                    group["walls"].append((wall, junction))
                    placed = True
                    break
            if not placed:
                groups.append({
                    "point_cm": [float(point[0]), float(point[1])],
                    "type": junction.get("type"),
                    "node_index": junction.get("node_index"),
                    "walls": [(wall, junction)],
                })
    return groups


def _row_signature(covering):
    """Como aquela fiada resolveu o no': (parede, codigo) de cada peca que
    o ocupa. A PAREDE faz parte da assinatura de proposito - e' o que muda
    entre a fiada A e a fiada B de um canto L bem amarrado."""
    return tuple(sorted((b.get("wall_id"), b.get("code")) for b in covering))


def _covering_blocks(group, row_index):
    covering = []
    for wall, _junction in group["walls"]:
        for row in wall.get("rows") or []:
            if row["row"] != row_index:
                continue
            for block in row.get("blocks") or []:
                if block_covers_point(block, group["point_cm"]):
                    covering.append(block)
    return covering


def _rows_of_group(group):
    indices = set()
    for wall, _junction in group["walls"]:
        for row in wall.get("rows") or []:
            if row.get("blocks"):
                indices.add(row["row"])
    return sorted(indices)


def validate_node(group):
    findings = []
    if group.get("type") not in BINDING_JUNCTION_TYPES:
        return findings
    wall_ids = sorted(set(wall.get("id") for wall, _j in group["walls"]))
    # Um no' de amarracao real tem pelo menos DUAS paredes. Um "L"
    # declarado por uma parede so' e' um dado incompleto da extracao, nao
    # um erro do solver - reportar isso como amarracao faltando seria
    # culpar o solver por uma falha de leitura.
    if len(wall_ids) < 2:
        return findings

    primary_wall = group["walls"][0][0]
    signatures = {}
    for row_index in _rows_of_group(group):
        covering = _covering_blocks(group, row_index)
        if not covering:
            findings.append(base.finding(
                "JUNCTION_MISSING_BINDING",
                wall=primary_wall.get("id"),
                detail=(
                    "encontro {0} em ({1:.1f}, {2:.1f}) sem nenhuma peca na "
                    "fiada {3} - paredes {4}".format(
                        group.get("type"), group["point_cm"][0],
                        group["point_cm"][1], row_index, ", ".join(wall_ids))
                ),
                row=row_index,
                junction_type=group.get("type"),
                point_cm=[round(v, 2) for v in group["point_cm"]],
                neighbors=wall_ids,
            ))
            continue
        signatures[row_index] = _row_signature(covering)

        for block in covering:
            if block.get("code") != analysis.HALF_BLOCK_CODE:
                continue
            findings.append(base.finding(
                "JUNCTION_HALF_BLOCK_ADJACENT",
                wall=block.get("wall_id"),
                detail=(
                    "meio-bloco {0} ocupando o encontro {1} em ({2:.1f}, "
                    "{3:.1f}), fiada {4}".format(
                        block.get("id"), group.get("type"),
                        group["point_cm"][0], group["point_cm"][1], row_index)
                ),
                row=row_index,
                blocks=[block.get("id")],
                junction_type=group.get("type"),
                point_cm=[round(v, 2) for v in group["point_cm"]],
                distance_cm=0.0,
            ))

    ordered = sorted(signatures)
    for index in range(len(ordered) - 1):
        row_a, row_b = ordered[index], ordered[index + 1]
        if row_b != row_a + 1:
            continue
        if signatures[row_a] == signatures[row_b]:
            findings.append(base.finding(
                "JUNCTION_NOT_ALTERNATING",
                wall=primary_wall.get("id"),
                detail=(
                    "encontro {0} em ({1:.1f}, {2:.1f}) resolvido igual nas "
                    "fiadas {3} e {4}: {5}".format(
                        group.get("type"), group["point_cm"][0],
                        group["point_cm"][1], row_a, row_b,
                        " + ".join("{0}:{1}".format(w, c)
                                   for w, c in signatures[row_a]))
                ),
                row_a=row_a, row_b=row_b,
                junction_type=group.get("type"),
                point_cm=[round(v, 2) for v in group["point_cm"]],
                codes=[list(item) for item in signatures[row_a]],
            ))
    return findings


def _node_pieces(group):
    """Assinatura do no' por fiada, so' com os CODIGOS - e' o que da' para
    comparar entre dois projetos diferentes (o id da parede nao)."""
    result = {}
    for row_index in _rows_of_group(group):
        covering = _covering_blocks(group, row_index)
        if covering:
            result[row_index] = tuple(sorted(b.get("code") for b in covering))
    return result


def validate(project, context=None):
    findings = []
    groups = collect_nodes(project)
    for group in groups:
        findings.extend(validate_node(group))

    # ---- nivel 2: comparacao com a escolha do projetista --------------
    reference = (context or {}).get("reference")
    if reference:
        reference_groups = collect_nodes(reference)
        for group in groups:
            if group.get("type") not in BINDING_JUNCTION_TYPES:
                continue
            best = None
            best_distance = None
            for candidate in reference_groups:
                if candidate.get("type") != group.get("type"):
                    continue
                distance = math.hypot(
                    candidate["point_cm"][0] - group["point_cm"][0],
                    candidate["point_cm"][1] - group["point_cm"][1])
                if distance <= model.WALL_MATCH_TOLERANCE_CM and (
                        best_distance is None or distance < best_distance):
                    best, best_distance = candidate, distance
            if best is None:
                continue
            mine, theirs = _node_pieces(group), _node_pieces(best)
            shared = set(mine) & set(theirs)
            different = sorted(r for r in shared if mine[r] != theirs[r])
            if different:
                findings.append(base.finding(
                    "JUNCTION_WRONG_PIECE",
                    wall=group["walls"][0][0].get("id"),
                    detail=(
                        "encontro {0} em ({1:.1f}, {2:.1f}): fiadas {3} usam "
                        "pecas diferentes do projeto humano".format(
                            group.get("type"), group["point_cm"][0],
                            group["point_cm"][1],
                            ", ".join(str(r) for r in different))
                    ),
                    junction_type=group.get("type"),
                    point_cm=[round(v, 2) for v in group["point_cm"]],
                    rows=different,
                    mine=dict((r, list(mine[r])) for r in different),
                    reference=dict((r, list(theirs[r])) for r in different),
                ))
    return findings


base.register("junctions", validate)
