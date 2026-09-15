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


# ---------------------------------------------------------------------------
# SECAO 61 - composicao de mesmo comprimento + aceitacao exata por parede
# ---------------------------------------------------------------------------
EVEN_ALL_B39 = [("B39", 0, 39), ("B39", 40, 79), ("B39", 80, 119), ("B39", 120, 159), ("B39", 160, 199)]
ODD_B34_C04 = [("B19", 0, 19), ("B39", 20, 59), ("B39", 60, 99), ("B34", 100, 134), ("C04", 135, 139),
               ("B39", 140, 179), ("B19", 180, 199)]


def _composition_case():
    cc = dict((c, _row(EVEN_ALL_B39 if c % 2 == 0 else ODD_B34_C04, c)) for c in range(6))
    for c in cc:
        for cand in cc[c]:
            cand["course_variant"] = c % 2
    sva.orient_small_voids(cc, CATALOG)
    return cc


def _with_composition(enabled, fn):
    old = R.B34_RUN_COMPOSITION_ENABLED
    R.B34_RUN_COMPOSITION_ENABLED = enabled
    try:
        return fn()
    finally:
        R.B34_RUN_COMPOSITION_ENABLED = old


def test_red_without_composition_no_order_of_the_same_pieces_aligns_the_lonely_b34():
    cc = _composition_case()
    before = _violations(cc)
    _with_composition(False, lambda: R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG))
    sva.orient_small_voids(cc, CATALOG)
    assert before > 0 and _violations(cc) == before


def test_green_same_length_composition_removes_the_violation_and_a_special():
    cc = _composition_case()
    before = _violations(cc)
    specials_before = sum(1 for c in cc for x in cc[c] if CATALOG[x["logical_code"]]["is_compensator"])
    summary = _with_composition(True, lambda: R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG))
    sva.orient_small_voids(cc, CATALOG)
    specials_after = sum(1 for c in cc for x in cc[c] if CATALOG[x["logical_code"]]["is_compensator"])
    assert summary["compositions"] >= 1
    assert _violations(cc) < before
    assert specials_after < specials_before
    # nunca inventa familia: so' codigos que ja' eram preenchimento
    assert set(x["logical_code"] for c in cc for x in cc[c]) <= {"B19", "B34", "B39", "C04"}


def test_created_pieces_are_whole_catalog_pieces_filling_the_same_span():
    cc = _composition_case()
    before = dict((c, _codes_by_t(cc, c, t_max=1e9)) for c in cc)
    _with_composition(True, lambda: R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG))
    for c in cc:
        after = _codes_by_t(cc, c, t_max=1e9)
        assert after[0][0] == before[c][0][0] and after[-1][1] == before[c][-1][1]
        for lo, hi, code in after:
            assert abs((hi - lo) - CATALOG[code]["length_cm"]) < 1e-6
        for (a_lo, a_hi, _x), (b_lo, _b_hi, _y) in zip(after, after[1:]):
            assert abs((b_lo - a_hi) - 1.0) < 1e-6
        assert all(x.get("course_variant") == c % 2 for x in cc[c])


def test_exact_validation_rejects_and_restores_the_wall_exactly():
    """A busca e' um modelo; quem decide e' o validador de producao. Se ele
    acusar piora, a parede volta EXATAMENTE ao estado anterior."""
    cc = _composition_case()
    lists_before = dict((c, list(cc[c])) for c in cc)
    geometry_before = dict((id(x), (x["origin_world"].X, x["origin_world"].Y, x["x_dir"].X, x["x_dir"].Y))
                           for c in cc for x in cc[c])
    calls = []

    def validator(wall_idx, support=True):
        calls.append(wall_idx)
        # "antes" limpo, "depois" com um problema novo de auditoria
        return {"audit": {} if len(calls) == 1 else {"REPEATED_VERTICAL_COMPENSATOR_STRIP": 1},
                "unsupported": 0}

    summary = _with_composition(True, lambda: R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG,
                                                                 validate_wall=validator))
    assert summary["walls_rejected_by_validation"] and summary["walls_changed"] == 0
    for c in cc:
        assert [id(x) for x in cc[c]] == [id(x) for x in lists_before[c]]
        for x in cc[c]:
            assert (x["origin_world"].X, x["origin_world"].Y, x["x_dir"].X, x["x_dir"].Y) == geometry_before[id(x)]


def test_exact_validation_accepts_when_nothing_gets_worse():
    cc = _composition_case()
    before = _violations(cc)
    summary = _with_composition(True, lambda: R.arrange_b34_runs(
        cc, WALLS, OPENINGS, CATALOG, validate_wall=lambda wi, support=True: {"audit": {}, "unsupported": 0}))
    sva.orient_small_voids(cc, CATALOG)
    assert not summary["walls_rejected_by_validation"] and _violations(cc) < before


def test_adjacent_compensator_pair_is_never_traded_for_a_c09_at_the_wall_end():
    """As duas guardas sao separadas: somadas, a busca trocava o par C09+C09
    encostado por um C09 na ponta da parede (medido nesta fixture)."""
    even = [("B39", 0, 39), ("B39", 40, 79), ("C09", 80, 89), ("C09", 90, 99), ("B39", 100, 139), ("B39", 140, 179)]
    odd = [("B34", 0, 34), ("B39", 35, 74), ("B39", 75, 114), ("B39", 115, 154), ("B19", 155, 174), ("C04", 175, 179)]
    cc = dict((c, _row(even if c % 2 == 0 else odd, c)) for c in range(6))
    sva.orient_small_voids(cc, CATALOG)
    _with_composition(True, lambda: R.arrange_b34_runs(cc, WALLS, OPENINGS, CATALOG))
    for c in cc:
        row = _codes_by_t(cc, c, t_max=1e9)
        first = row[0]
        assert not (first[2] == "C09" and first[0] <= 2.0), (c, row)


# ---------------------------------------------------------------------------
# SECAO 62 - orientacao otima exata (DP) - fixture = parede REAL 8284579 do
# BUTANTA (209 cm, B34 de no' nas duas pontas, 17 fiadas), no estado em que a
# orientacao gulosa da secao 52 travou com 10 violacoes.
# ---------------------------------------------------------------------------
WALL_209 = [(seg(0, 0, 209, 0), ft(14.0), (False, False))]
_E02 = [("B39", 15, 54, 0, False), ("B34", 55, 89, 1, False), ("B34", 90, 124, 1, False),
        ("B34", 125, 159, 1, False), ("B34", 160, 194, -1, False)]
_O13 = [("B34", 0, 34, -1, True), ("B34", 35, 69, 1, False), ("B34", 70, 104, -1, False),
        ("B34", 105, 139, -1, False), ("B34", 140, 174, 1, False), ("B34", 175, 209, 1, True)]
_E4 = [("B39", 15, 54, 0, False), ("B34", 55, 89, -1, False), ("B34", 90, 124, 1, False),
       ("B34", 125, 159, -1, False), ("B34", 160, 194, -1, False)]
_OUP = [("B34", 0, 34, -1, True), ("B34", 35, 69, 1, False), ("B34", 70, 104, 1, False),
        ("B34", 105, 139, 1, False), ("B34", 140, 174, 1, False), ("B34", 175, 209, 1, True)]
_EUP = [("B39", 15, 54, 0, False), ("B34", 55, 89, -1, False), ("B34", 90, 124, -1, False),
        ("B34", 125, 159, -1, False), ("B34", 160, 194, -1, False)]


def _real_row(spec, course):
    out = []
    for code, a, b, side, node in spec:
        cand = m._place_pier_layout([(code, a, b)], CATALOG, P0, DIRECTION, course, 0,
                                    node_index=(3 if node else None),
                                    placement_reason=("T_INTERSECTION_INCOMING" if node else "STANDARD_FILL"))[0]
        if code == "B34" and side > 0:
            sva.rotate_candidate_180(cand)
        out.append(cand)
    return out


def _wall_8284579():
    spec = {0: _E02, 2: _E02, 1: _O13, 3: _O13, 4: _E4}
    for c in range(5, 17):
        spec[c] = _OUP if c % 2 == 1 else _EUP
    cc = dict((c, _real_row(spec[c], c)) for c in range(17))
    sva.orient_small_voids(cc, CATALOG)
    return cc


def _run(cc, dp=True, band=None):
    old = (R.B34_ORIENTATION_DP_ENABLED, R.B34_RUN_COMPOSITION_ENABLED, R.ORIENTATION_DP_MAX_BAND)
    R.B34_ORIENTATION_DP_ENABLED = dp
    R.B34_RUN_COMPOSITION_ENABLED = False
    if band is not None:
        R.ORIENTATION_DP_MAX_BAND = band
    try:
        summary = R.arrange_b34_runs(cc, WALL_209, OPENINGS, CATALOG)
    finally:
        R.B34_ORIENTATION_DP_ENABLED, R.B34_RUN_COMPOSITION_ENABLED, R.ORIENTATION_DP_MAX_BAND = old
    sva.orient_small_voids(cc, CATALOG)
    return summary


def _geometry(cc):
    return dict((c, sorted((round(m._candidate_extent_on_wall_axis(x, P0, DIRECTION)[0], 3), x["logical_code"],
                            x.get("node_index")) for x in cc[c])) for c in cc)


def _node_sides(cc):
    return [(c, round(x["x_dir"].X, 3)) for c in sorted(cc) for x in cc[c] if x.get("node_index") is not None]


def test_red_real_wall_greedy_orientation_and_reordering_stay_stuck():
    cc = _wall_8284579()
    stuck = _violations(cc)
    assert stuck == 10
    _run(cc, dp=False)
    assert _violations(cc) == stuck


def test_green_exact_orientation_aligns_the_real_wall_without_touching_geometry_or_nodes():
    cc = _wall_8284579()
    geometry, nodes = _geometry(cc), _node_sides(cc)
    summary = _run(cc, dp=True)
    assert summary.get("orientation_dp_changes")
    assert _violations(cc) == 0
    assert _geometry(cc) == geometry      # so' giro: mesmas pecas, mesmas posicoes
    assert _node_sides(cc) == nodes       # peca de no' mantem a orientacao (secao 5)


def test_band_ceiling_leaves_the_wall_to_the_greedy_pass():
    cc = _wall_8284579()
    summary = _run(cc, dp=True, band=0)
    assert not summary.get("orientation_dp_changes")
    assert _violations(cc) == 10


def test_exact_orientation_is_idempotent():
    cc = _wall_8284579()
    _run(cc, dp=True)
    again = _run(cc, dp=True)
    assert not again.get("orientation_dp_changes") and _violations(cc) == 0
