# -*- coding: utf-8 -*-
"""Compensadores encostados (secao 56 de REGRAS_MODULACAO_BLOCOS.md).

Evidencia humana (BUTANTA R08_LT, 1o PAV, 34 paredes, 6.018 pecas): ZERO pares
C09+C09 e ZERO pares C04+C04 encostados; o humano encosta C04 com C09 (97
vezes). Os 6 pares de codigo identico que o humano tem sao todos do compensador
DEITADO (C09D), peca que o solver nao emite. O solver tinha 20 pares C09+C09,
nascidos de duas causas:

1. o guloso da Fiada A nunca olhou a regra #2 (compensador em sequencia) fora
   do trecho absorvido pela 30.8 - parede de 100 cm entre dois cantos L:
   B39 + C09 + C09 + C04 em vez de C09 + B39 + C09 + C04;
2. o compensador da ponta do preenchimento encostando no compensador de uma
   peca de NO' (T degradado).

    python3 -m pytest tests/test_compensator_adjacency.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
ft, seg = sb.ft, sb.seg
from core.engine import wall_stepper as ws  # noqa: E402

CATALOG = sb.CATALOG


def _solve_wall(length_cm, rule2):
    before = ws.RULE2_ON_EVERY_COURSE_A_SEGMENT
    ws.RULE2_ON_EVERY_COURSE_A_SEGMENT = rule2
    try:
        lines = [seg(0, 0, length_cm, 0), seg(0, 0, 0, -300), seg(length_cm, 0, length_cm, -300)]
        walls = [(line, ft(14.0), (False, False)) for line in lines]
        walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
        nodes, e2n = m.build_wall_graph(walls, jm)
        res = m.solve_building_blocks_all_courses(nodes, walls, e2n, [[], [], []], CATALOG, 0.0, 6,
                                                  variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    finally:
        ws.RULE2_ON_EVERY_COURSE_A_SEGMENT = before
    p0, _p1, wall_dir, _l, _t = m._wall_axis_and_length(walls, 0)
    rows = {}
    for course_index in (0, 1):
        items = []
        for cand in res["course_candidates"][course_index]:
            if cand.get("wall_idx") != 0:
                continue
            lo, hi = m._candidate_t_range_on_wall(cand, p0, wall_dir)
            items.append((round(min(lo, hi), 1), round(max(lo, hi), 1), cand["logical_code"]))
        rows[course_index] = sorted(items)
    return rows


def _adjacent_compensator_pairs(rows):
    pairs = []
    for course_index, items in rows.items():
        for (a_lo, a_hi, a_code), (b_lo, _b_hi, b_code) in zip(items, items[1:]):
            if (CATALOG[a_code]["is_compensator"] and CATALOG[b_code]["is_compensator"]
                    and 0.0 <= b_lo - a_hi <= 1.6):
                pairs.append((course_index, a_code, b_code, a_lo))
    return pairs


def _equal_code_pairs(rows):
    return [pair for pair in _adjacent_compensator_pairs(rows) if pair[1] == pair[2]]


def test_red_course_a_greedy_puts_two_equal_compensators_side_by_side():
    rows = _solve_wall(100, rule2=False)
    assert [pair[1:3] for pair in _equal_code_pairs(rows)] == [("C09", "C09"), ("C09", "C09")]


def test_green_rule2_on_every_course_a_segment_removes_the_pair():
    rows = _solve_wall(100, rule2=True)
    assert _equal_code_pairs(rows) == []
    # C04 encostado em C09 continua permitido: o humano usa 97 vezes
    assert _adjacent_compensator_pairs(rows)
    # mesmas pecas, mesma aritmetica: nada some da parede
    assert sorted(code for items in rows.values() for _lo, _hi, code in items) == \
        sorted(code for items in _solve_wall(100, rule2=False).values() for _lo, _hi, code in items)


def _layout(codes, joint_cm=1.0):
    out = []
    cursor = 0.0
    for code in codes:
        length = CATALOG[code]["length_cm"]
        out.append((code, cursor, cursor + length))
        cursor += length + joint_cm
    return out


def test_mirrored_layout_keeps_envelope_and_joints():
    layout = _layout(["B39", "C09"])
    mirrored = ws._mirrored_layout(layout)
    assert [code for code, _a, _b in mirrored] == ["C09", "B39"]
    assert abs(mirrored[-1][2] - layout[-1][2]) < 1e-9 and mirrored[0][1] == layout[0][1]


def test_layout_avoiding_compensator_against_node_mirrors_when_the_node_piece_is_a_compensator():
    layout = _layout(["B39", "C09"])
    pier = layout[-1][2]
    ws._COMPENSATOR_NODE_TRIAL[0] = True
    try:
        kept = ws._layout_avoiding_compensator_against_node(
            layout, pier, CATALOG, 1.0, 1.0, 0.0, None, "B39", [], [], course_label="B")
        fixed_inner = ws._layout_avoiding_compensator_against_node(
            layout, pier, CATALOG, 1.0, 1.0, 0.0, None, "C09", [], [], course_label="B")
    finally:
        ws._COMPENSATOR_NODE_TRIAL[0] = False
    assert [code for code, _a, _b in kept] == ["B39", "C09"]  # vizinho nao e' compensador: nada muda
    assert [code for code, _a, _b in fixed_inner] == ["C09", "B39"]
    # fora da tentativa por parede a regra nao age sozinha
    assert [code for code, _a, _b in ws._layout_avoiding_compensator_against_node(
        layout, pier, CATALOG, 1.0, 1.0, 0.0, None, "C09", [], [], course_label="B")] == ["B39", "C09"]


def test_layout_avoiding_compensator_keeps_layout_when_no_alternative_removes_the_touch():
    layout = _layout(["C09"])
    ws._COMPENSATOR_NODE_TRIAL[0] = True
    try:
        fixed = ws._layout_avoiding_compensator_against_node(
            layout, layout[-1][2], CATALOG, 1.0, 1.0, 0.0, "C09", "C09", [], [], course_label="B")
    finally:
        ws._COMPENSATOR_NODE_TRIAL[0] = False
    assert [code for code, _a, _b in fixed] == ["C09"]


def _fill(candidates, non_modular_cm=0.0, conflicts=0):
    return {"candidates": list(candidates), "alignment_conflicts": [{}] * conflicts,
            "non_modular": [{"current_length_cm": non_modular_cm}] if non_modular_cm else []}


def _piece(code, t_cm, course="A"):
    entry = CATALOG[code]
    p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    return m._place_pier_layout([(code, t_cm, t_cm + entry["length_cm"])], CATALOG, p0, direction,
                                course, 0)[0]


def _trial(base, trial, node_pieces):
    calls = []

    def solve_once():
        calls.append(ws._COMPENSATOR_NODE_TRIAL[0])
        return trial if ws._COMPENSATOR_NODE_TRIAL[0] else base
    p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    return ws.compensator_node_adjacency_trial(solve_once, CATALOG, p0, direction, 400.0, [], node_pieces), calls


def test_trial_accepts_when_the_touch_disappears_without_new_repeated_joint():
    node = [(90.0, 99.0, "C09")]
    base = _fill([_piece("B39", 40.0), _piece("C09", 80.0)])
    better = _fill([_piece("C09", 40.0), _piece("B39", 50.0)])
    chosen, calls = _trial(base, better, node)
    assert calls == [False, True]
    assert chosen is better and chosen["compensator_node_trial"]["accepted"] is True


def test_trial_refuses_when_it_would_add_non_modular_or_lose_wall():
    node = [(90.0, 99.0, "C09")]
    base = _fill([_piece("B39", 40.0), _piece("C09", 80.0)])
    worse = _fill([_piece("C09", 40.0)], non_modular_cm=39.0)
    chosen, _calls = _trial(base, worse, node)
    assert chosen is base and chosen["compensator_node_trial"]["accepted"] is False


def test_trial_is_skipped_when_no_compensator_touches_a_node_compensator():
    node = [(90.0, 99.0, "B39")]
    base = _fill([_piece("B39", 40.0), _piece("C09", 80.0)])
    chosen, calls = _trial(base, _fill([]), node)
    assert chosen is base and calls == [False] and "compensator_node_trial" not in chosen


# ---------------------------------------------------------------------------
# Determinismo do escolhedor da secao 56.2 - caso REAL capturado na parede
# 8284580 do BUTANTA: planta normal x transladada (+1000, +500 cm). Mesma
# composicao de entrada; as juntas da fiada oposta diferem so' por ruido
# numerico (1e-13 cm). Antes do arredondamento do travamento, a escolha trocava
# (C09 ... B34 x C04 ... B39).
# ---------------------------------------------------------------------------
_TIE_NORMAL = {'layout': [('B34', 0.0, 34.0), ('B39', 35.0, 74.0), ('B39', 75.0, 114.0), ('B39', 115.0, 154.0), ('C09', 155.0, 164.0)], 'pier': 164.00000000861957, 'seg_start': 35.000000000000036, 'left': 'B34', 'right': 'C09', 'avoid': [54.50000000000004, 94.50000000000004, 134.50000000000003, 14.50000000000004, 174.50000000861962, 54.50000000000007, 94.50000000000006, 134.50000000000009, 174.50000000430987]}
_TIE_TRANSLATED = {'layout': [('B34', 0.0, 34.0), ('B39', 35.0, 74.0), ('B39', 75.0, 114.0), ('B39', 115.0, 154.0), ('C09', 155.0, 164.0)], 'pier': 164.00000000861988, 'seg_start': 35.000000000000036, 'left': 'B34', 'right': 'C09', 'avoid': [54.50000000000016, 94.50000000000016, 134.50000000000017, 14.500000000000162, 174.50000000861974, 54.49999999999996, 94.49999999999997, 134.5, 174.50000000430987]}


def _tie_choice(case):
    ws._COMPENSATOR_NODE_TRIAL[0] = True
    try:
        out = ws._layout_avoiding_compensator_against_node(
            case["layout"], case["pier"], CATALOG, 0.0, 0.0, case["seg_start"], case["left"], case["right"],
            [], case["avoid"], course_label="B", allow_compensators=True,
            leading_is_open=False, trailing_is_open=False)
    finally:
        ws._COMPENSATOR_NODE_TRIAL[0] = False
    return [code for code, _a, _b in out]


def test_node_compensator_chooser_is_not_decided_by_numeric_noise():
    assert _tie_choice(_TIE_NORMAL) == _tie_choice(_TIE_TRANSLATED)
