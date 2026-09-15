# -*- coding: utf-8 -*-
"""Arranjo conjunto das corridas de preenchimento (secao 60 de
REGRAS_MODULACAO_BLOCOS.md) - vazado menor do B34 entre fiadas.

Fixture = o trecho REAL da parede 8284543 do BUTANTA (815-964 cm, transladado
para t=0): o solver assentava na fiada par `B34 B39 B39 B34` + B54 de no' e na
impar `B19 B34 B34 B39 B39`; o projeto humano assenta a par como
`B34 B34 B39 B39` - as MESMAS pecas, outra ordem - e o vazado menor fica
alinhado com a corrida de B34 da impar, deslocada ~20 cm e girada 180 graus.

    python3 -m pytest tests/test_b34_run_arrangement.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
ft, seg = sb.ft, sb.seg
from core.engine import b34_run_arrangement as R  # noqa: E402
from core.engine import small_void_alignment as sva  # noqa: E402

CATALOG = sb.CATALOG
WALLS = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
OPENINGS = [[]]
P0 = m.XYZ(0.0, 0.0, 0.0)
DIRECTION = m.XYZ(1.0, 0.0, 0.0)

# fiada par e impar do trecho real (t em cm, joints de 1 cm)
EVEN_SOLVER = [("B34", 0, 34), ("B39", 35, 74), ("B39", 75, 114), ("B34", 115, 149)]
EVEN_NODE = [("B54", 150, 204)]
ODD = [("B19", 0, 19), ("B34", 20, 54), ("B34", 55, 89), ("B39", 90, 129), ("B39", 130, 169)]
HUMAN_EVEN_CODES = ["B34", "B34", "B39", "B39"]


def _row(layout, course, node_layout=()):
    pieces = m._place_pier_layout(layout, CATALOG, P0, DIRECTION, course, 0)
    for code, a, b in node_layout:
        node = m._place_pier_layout([(code, a, b)], CATALOG, P0, DIRECTION, course, 0,
                                    node_index=7, placement_reason="T_INTERSECTION_MAIN")
        pieces.extend(node)
    return pieces


def _courses(n=6):
    out = {}
    for c in range(n):
        out[c] = _row(EVEN_SOLVER, c, EVEN_NODE) if c % 2 == 0 else _row(ODD, c)
    return out


def _codes_by_t(course_candidates, course, t_max=150.0):
    items = []
    for cand in course_candidates[course]:
        lo, hi = m._candidate_extent_on_wall_axis(cand, P0, DIRECTION)
        if hi <= t_max + 1e-6:
            items.append((round(lo, 1), round(hi, 1), cand["logical_code"]))
    return sorted(items)


def _violations(course_candidates):
    return len(sva.b34_small_void_violations(course_candidates, CATALOG))


def _solver_state():
    cc = _courses()
    sva.orient_small_voids(cc, CATALOG)
    return cc


def test_red_orientation_alone_leaves_the_real_segment_misaligned():
    cc = _solver_state()
    assert _violations(cc) > 0
    assert [code for _a, _b, code in _codes_by_t(cc, 0)] == ["B34", "B39", "B39", "B34"]


def test_green_joint_arrangement_reproduces_the_human_order_and_aligns_the_small_voids():
    cc = _solver_state()
    before = _violations(cc)
    summary = R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG)
    sva.orient_small_voids(cc, CATALOG)
    assert summary["runs_changed"] >= 1
    assert _violations(cc) < before
    assert [code for _a, _b, code in _codes_by_t(cc, 0)] == HUMAN_EVEN_CODES
    # todas as fiadas da mesma familia recebem a mesma ordem
    assert _codes_by_t(cc, 2) == _codes_by_t(cc, 0) == _codes_by_t(cc, 4)


def test_same_pieces_same_ends_and_fixed_pieces_never_move():
    cc = _solver_state()
    before = dict((c, _codes_by_t(cc, c, t_max=1e9)) for c in cc)
    node_before = [(c, round(m._candidate_extent_on_wall_axis(x, P0, DIRECTION)[0], 3))
                   for c in cc for x in cc[c] if x.get("node_index") is not None]
    R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG)
    for c in cc:
        after = _codes_by_t(cc, c, t_max=1e9)
        assert sorted(code for _a, _b, code in after) == sorted(code for _a, _b, code in before[c])
        assert after[0][0] == before[c][0][0] and after[-1][1] == before[c][-1][1]
        # sem sobreposicao nem folga nova: juntas continuam de 1 cm
        for (a_lo, a_hi, _x), (b_lo, _b_hi, _y) in zip(after, after[1:]):
            assert abs((b_lo - a_hi) - 1.0) < 1e-6
    node_after = [(c, round(m._candidate_extent_on_wall_axis(x, P0, DIRECTION)[0], 3))
                  for c in cc for x in cc[c] if x.get("node_index") is not None]
    assert node_after == node_before


def test_idempotent_second_pass_changes_nothing():
    cc = _solver_state()
    R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG)
    sva.orient_small_voids(cc, CATALOG)
    snapshot = dict((c, _codes_by_t(cc, c, t_max=1e9)) for c in cc)
    again = R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG)
    assert again["runs_changed"] == 0
    assert dict((c, _codes_by_t(cc, c, t_max=1e9)) for c in cc) == snapshot


def test_channel_piece_inside_a_fill_run_is_never_moved():
    """Canaleta do reforco CHANNEL herda a etiqueta STANDARD_FILL da peca que
    substituiu; mesmo assim nunca e' peca de ajuste de corrida."""
    from core.engine import opening_reinforcement as reinforcement
    channel_code = sorted(reinforcement.CHANNEL_LOGICAL_TYPES)[0]
    cc = _solver_state()
    for c in (0, 2, 4):
        channel = cc[c][1]  # o B39 em 35-74 vira canaleta
        channel["logical_code"] = channel_code
        channel["cells_world"] = []
    positions = [(c, round(m._candidate_extent_on_wall_axis(cc[c][1], P0, DIRECTION)[0], 3)) for c in (0, 2, 4)]
    R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG)
    assert [(c, round(m._candidate_extent_on_wall_axis(cc[c][1], P0, DIRECTION)[0], 3)) for c in (0, 2, 4)] == positions


def test_disabled_flag_leaves_everything_untouched():
    cc = _solver_state()
    snapshot = dict((c, _codes_by_t(cc, c, t_max=1e9)) for c in cc)
    old = R.B34_RUN_ARRANGEMENT_ENABLED
    R.B34_RUN_ARRANGEMENT_ENABLED = False
    try:
        summary = R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG)
    finally:
        R.B34_RUN_ARRANGEMENT_ENABLED = old
    assert summary["runs_changed"] == 0
    assert dict((c, _codes_by_t(cc, c, t_max=1e9)) for c in cc) == snapshot


def test_half_block_near_tie_guard_matches_the_bond_audit_rule():
    """Mesma regra de HALF_BLOCK_NEAR_TIE da auditoria: distancia do CORPO do
    meio bloco ate' a amarracao, zero se a amarracao cair dentro dele."""
    slot = R._Slot()
    slot.code, slot.lo, slot.hi = "B19", 100.0, 119.0
    gap = m.HALF_BLOCK_TIE_ADJACENCY_CM
    assert R._half_blocks_near_ties([slot], [110.0], "B19", gap) == 1       # dentro
    assert R._half_blocks_near_ties([slot], [119.0 + gap], "B19", gap) == 1  # no limite
    assert R._half_blocks_near_ties([slot], [119.0 + gap + 0.5], "B19", gap) == 0
    assert R._half_blocks_near_ties([slot], [110.0], None, gap) == 0


def _odd_b19_at_the_end():
    cc = _courses()
    odd = [("B34", 0, 34), ("B34", 35, 69), ("B39", 70, 109), ("B39", 110, 149), ("B19", 150, 169)]
    for c in (1, 3, 5):
        cc[c] = _row(odd, c)
    sva.orient_small_voids(cc, CATALOG)
    return cc


def _b19_extents(cc, course):
    return [(lo, hi) for lo, hi, code in _codes_by_t(cc, course, t_max=1e9) if code == "B19"]


def test_control_without_ties_the_best_order_puts_the_half_block_at_35cm():
    cc = _odd_b19_at_the_end()
    R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG)
    assert _b19_extents(cc, 1) == [(35.0, 54.0)]


def test_arrangement_keeps_the_half_block_off_a_tie_and_still_aligns():
    """Com uma amarracao em t=44 cm - exatamente onde a melhor ordem sem guarda
    poria o meio bloco - o arranjo tem de escolher OUTRA ordem (regra #2 da
    auditoria) e ainda assim alinhar o vazado menor."""
    cc = _odd_b19_at_the_end()
    before = _violations(cc)
    ties = {0: [44.0]}
    gap = m.HALF_BLOCK_TIE_ADJACENCY_CM
    R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG, tie_positions_by_wall=ties,
                       half_block_code="B19", half_block_tie_gap_cm=gap)
    sva.orient_small_voids(cc, CATALOG)
    assert _violations(cc) < before
    for course in (1, 3, 5):
        for lo, hi in _b19_extents(cc, course):
            assert R._half_blocks_near_ties([_slot(lo, hi)], ties[0], "B19", gap) == 0


def _slot(lo, hi):
    s = R._Slot()
    s.code, s.lo, s.hi = "B19", lo, hi
    return s
