# -*- coding: utf-8 -*-
"""Casamento gabarito <-> resultado, SEM ElementId (item 4 do pedido).

O problema real: o gabarito vem de um .rvt entregue (onde as paredes de
referencia foram apagadas e so' sobraram blocos) e o resultado vem de uma
execucao nova do solver. Os ElementId nao tem nada a ver uns com os
outros; ate' a ORDEM das paredes muda. O unico vinculo confiavel entre os
dois lados e' geometrico.

Estrategia, em tres niveis de folga, sempre determinista:

1. **Pontas iguais** dentro de `WALL_MATCH_TOLERANCE_CM` (nos dois
   sentidos - a mesma parede pode ter sido desenhada ao contrario).
2. **Mesma reta + sobreposicao** - cobre o caso comum de uma parede que
   o ajuste automatico encurtou/alongou alguns centimetros: mesma
   direcao, mesmo offset perpendicular, e os intervalos se sobrepoem em
   pelo menos `MIN_OVERLAP_RATIO` do menor dos dois.
3. **Sem par** - fica registrado como `only_in_reference` ou
   `only_in_result`. Nunca casado "na forca": um par errado polui todas
   as comparacoes seguintes daquela parede.

O casamento e' 1-para-1 e guloso pelo MELHOR score (menor distancia),
nao pela ordem da lista - ordem de entrada nao pode mudar o resultado.
"""

import math

from .. import model

# Fracao minima de sobreposicao (sobre o menor comprimento) para duas
# paredes colineares contarem como a mesma.
MIN_OVERLAP_RATIO = 0.6

# Desvio angular maximo entre dois eixos para eles serem "a mesma reta".
AXIS_ANGLE_TOLERANCE_DEG = 2.0

# Distancia perpendicular maxima entre duas retas paralelas para elas
# serem a mesma reta. Meia espessura de parede.
AXIS_OFFSET_TOLERANCE_CM = 7.0


def _endpoint_distance(wall_a, wall_b):
    """Menor soma de distancias entre pontas, testando os dois sentidos.
    `None` quando nem o melhor sentido fica dentro da tolerancia."""
    a0, a1 = wall_a["start_cm"], wall_a["end_cm"]
    b0, b1 = wall_b["start_cm"], wall_b["end_cm"]
    direct = (math.hypot(a0[0] - b0[0], a0[1] - b0[1])
              + math.hypot(a1[0] - b1[0], a1[1] - b1[1]))
    flipped = (math.hypot(a0[0] - b1[0], a0[1] - b1[1])
               + math.hypot(a1[0] - b0[0], a1[1] - b0[1]))
    return min(direct, flipped)


def _same_infinite_line(wall_a, wall_b):
    angle_a = model.normalize_axis_angle(wall_a["angle_deg"])
    angle_b = model.normalize_axis_angle(wall_b["angle_deg"])
    delta = abs(angle_a - angle_b)
    delta = min(delta, 180.0 - delta)
    if delta > AXIS_ANGLE_TOLERANCE_DEG:
        return False
    direction, _length = model.direction_of(wall_a["start_cm"], wall_a["end_cm"])
    _t0, s0 = model.axial_coordinates(wall_b["start_cm"], wall_a["start_cm"], direction)
    _t1, s1 = model.axial_coordinates(wall_b["end_cm"], wall_a["start_cm"], direction)
    return max(abs(s0), abs(s1)) <= AXIS_OFFSET_TOLERANCE_CM


def _collinear_overlap_ratio(wall_a, wall_b):
    direction, length_a = model.direction_of(wall_a["start_cm"], wall_a["end_cm"])
    t0, _s0 = model.axial_coordinates(wall_b["start_cm"], wall_a["start_cm"], direction)
    t1, _s1 = model.axial_coordinates(wall_b["end_cm"], wall_a["start_cm"], direction)
    lo, hi = min(t0, t1), max(t0, t1)
    overlap = max(0.0, min(hi, length_a) - max(lo, 0.0))
    shorter = min(length_a, hi - lo)
    if shorter <= 1e-6:
        return 0.0
    return overlap / shorter


def score_pair(result_wall, reference_wall):
    """Custo do par (menor e' melhor) ou `None` se eles nao podem ser a
    mesma parede. O custo comeca na distancia entre pontas para que, entre
    dois candidatos possiveis, vale sempre o mais proximo."""
    distance = _endpoint_distance(result_wall, reference_wall)
    if distance <= 2.0 * model.WALL_MATCH_TOLERANCE_CM:
        return distance
    if _same_infinite_line(result_wall, reference_wall):
        ratio = _collinear_overlap_ratio(result_wall, reference_wall)
        if ratio >= MIN_OVERLAP_RATIO:
            # Penaliza: par por sobreposicao e' sempre pior que par por
            # pontas, entao nunca rouba uma parede de um casamento exato.
            return 1000.0 + (1.0 - ratio) * 1000.0
    return None


def match_walls(result_project, reference_project):
    """Devolve `{"pairs", "only_in_result", "only_in_reference"}`.

    `pairs` e' `[(parede_do_resultado, parede_do_gabarito), ...]`, em
    ordem estavel (id da parede do resultado)."""
    result_walls = list(result_project.get("walls") or [])
    reference_walls = list(reference_project.get("walls") or [])

    candidates = []
    for r_index, result_wall in enumerate(result_walls):
        for f_index, reference_wall in enumerate(reference_walls):
            cost = score_pair(result_wall, reference_wall)
            if cost is not None:
                candidates.append((cost, r_index, f_index))
    # Ordena por custo e, em empate, pelos indices - determinismo total.
    candidates.sort()

    used_result, used_reference = set(), set()
    pairs = []
    for _cost, r_index, f_index in candidates:
        if r_index in used_result or f_index in used_reference:
            continue
        used_result.add(r_index)
        used_reference.add(f_index)
        pairs.append((result_walls[r_index], reference_walls[f_index]))

    pairs.sort(key=lambda pair: pair[0].get("id") or "")
    return {
        "pairs": pairs,
        "only_in_result": [w for i, w in enumerate(result_walls) if i not in used_result],
        "only_in_reference": [w for i, w in enumerate(reference_walls)
                              if i not in used_reference],
    }


def match_openings(result_wall, reference_wall,
                   tolerance_cm=model.WALL_MATCH_TOLERANCE_CM):
    """Aberturas casadas pela posicao NO EIXO (nao pela XY): a parede toda
    pode ter andado alguns centimetros, o vao dentro dela nao."""
    reference_openings = list(reference_wall.get("openings") or [])
    pairs, used = [], set()
    for opening in result_wall.get("openings") or []:
        best, best_cost = None, None
        for index, candidate in enumerate(reference_openings):
            if index in used:
                continue
            cost = (abs(opening["t_start_cm"] - candidate["t_start_cm"])
                    + abs(opening["t_end_cm"] - candidate["t_end_cm"]))
            if cost <= 2.0 * tolerance_cm and (best_cost is None or cost < best_cost):
                best, best_cost = index, cost
        if best is None:
            pairs.append((opening, None))
        else:
            used.add(best)
            pairs.append((opening, reference_openings[best]))
    for index, candidate in enumerate(reference_openings):
        if index not in used:
            pairs.append((None, candidate))
    return pairs


def match_blocks_in_row(result_row, reference_row, tolerance_cm=2.0):
    """Casa bloco a bloco DENTRO de uma fiada, pelo inicio no eixo.

    Nao exige mesmo codigo: e' exatamente a troca de peca (um B39 onde o
    humano pos dois B19) que interessa ver. Blocos sem par de um lado ou
    do outro voltam com `None` no lugar."""
    reference_blocks = model.blocks_sorted(reference_row or {"blocks": []})
    pairs, used = [], set()
    for block in model.blocks_sorted(result_row or {"blocks": []}):
        best, best_cost = None, None
        for index, candidate in enumerate(reference_blocks):
            if index in used:
                continue
            cost = abs(block["t_start_cm"] - candidate["t_start_cm"])
            if cost <= tolerance_cm and (best_cost is None or cost < best_cost):
                best, best_cost = index, cost
        if best is None:
            pairs.append((block, None))
        else:
            used.add(best)
            pairs.append((block, reference_blocks[best]))
    for index, candidate in enumerate(reference_blocks):
        if index not in used:
            pairs.append((None, candidate))
    return pairs
