# -*- coding: utf-8 -*-
"""Pastilha de 9 cm na amarracao do no' degradado (secao 58 de
REGRAS_MODULACAO_BLOCOS.md).

Evidencia humana (BUTANTA R08_LT, 34 paredes, 6.018 pecas, 383 pontas de fiada):
o humano NUNCA termina uma fiada com C09 - 0 casos; C04 na ponta ele aceita, 12
vezes. O solver fazia isso 40 vezes, e 33 dessas eram peca de NO': o ramo
degradado de `solve_t_intersection` punha um compensador na boneca mesmo quando
ela tinha espaco de sobra para o bloco de amarracao (no' 46 do BUTANTA: 175 cm
livres na boneca, C09 de 9 cm colocado, porque quem reprovava era a parede
PRINCIPAL com 27 dos 34 cm exigidos).

A escada correta ja' existia no cruzamento em X
(`X_INTERSECTION_DEGRADED_CODES = ("B34",) + CORNER_SINGLE_ELEMENT_CODES`):
bloco de amarracao primeiro, compensador depois, NUNCA B19.

    python3 -m pytest tests/test_degraded_node_tie_block.py -q
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
MAIN_LEN_CM = 400.0
ARM_CM = 150.0
# 25 cm de cada lado do no' na parede PRINCIPAL: menos que os 34 exigidos para
# degradar para um canto em L, o que forca o ramo do elemento unico.
MAIN_ROOM_CM = 25.0


def _degraded_t():
    lines = [seg(0, 0, MAIN_LEN_CM, 0), seg(MAIN_LEN_CM / 2.0, 0, MAIN_LEN_CM / 2.0, -ARM_CM)]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    half = MAIN_LEN_CM / 2.0
    openings = [[(ft(0.0), ft(half - MAIN_ROOM_CM), ft(0.0), ft(210.0)),
                 (ft(half + MAIN_ROOM_CM), ft(MAIN_LEN_CM), ft(0.0), ft(210.0))], []]
    index = next(i for i, node in enumerate(nodes) if node.get("kind") == "T_INTERSECTION")
    return nodes, walls, end_to_node, openings, index


def _solve(prefers_tie, alternates):
    nodes, walls, end_to_node, openings, index = _degraded_t()
    before = (ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK, ws.CORNER_DEGRADED_ALTERNATES_TIE)
    ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK = prefers_tie
    ws.CORNER_DEGRADED_ALTERNATES_TIE = alternates
    try:
        return ws.solve_t_intersection(nodes[index], walls, CATALOG, node_index=index,
                                       openings_per_wall=openings, nodes=nodes,
                                       end_to_node=end_to_node)
    finally:
        ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK, ws.CORNER_DEGRADED_ALTERNATES_TIE = before


def _room_cm():
    nodes, walls, _end_to_node, openings, index = _degraded_t()
    assessment = ws._t_intersection_room_assessment(
        nodes[index], walls, openings, nodes=nodes, end_to_node=None, node_index=index)
    return (assessment["room_incoming_ft"] * 30.48, assessment["room_plus_ft"] * 30.48)


def test_the_fixture_really_is_a_degraded_t_with_room_to_spare_on_the_stub():
    room_incoming_cm, room_main_cm = _room_cm()
    # a boneca tem espaco de sobra para o B34; quem reprova e' a parede principal
    assert room_incoming_cm > 34.0
    assert room_main_cm < 34.0
    assert _solve(False, False).get("degraded") is True


def test_red_degraded_t_used_a_9cm_pastilha_on_both_courses():
    result = _solve(False, False)
    assert result["ok"]
    assert result["course_a"]["logical_code"] == "C09"
    assert result["course_b"]["logical_code"] == "C09"
    assert result["course_a"]["placement_reason"] == "T_INTERSECTION_INCOMING_DEGRADED"


def test_green_degraded_t_ties_with_a_block_when_the_stub_has_room():
    result = _solve(True, True)
    assert result["ok"]
    assert result["course_a"]["logical_code"] == "B34"
    assert result["course_a"]["placement_reason"] == "T_INTERSECTION_INCOMING_DEGRADED"
    # a peca fica na BONECA (parede que chega), nao na principal
    assert result["course_a"]["wall_idx"] == 1
    assert result["course_a"]["secondary_wall_idx"] == 0


def test_green_the_opposite_family_keeps_the_short_piece():
    """Repetir o bloco nas duas familias poe a MESMA face em todas as fiadas -
    junta corrida (regra #1). Deixar a familia oposta VAZIA tambem nao serve: o
    preenchimento dela recomeca do zero e refaz a mesma face (medido no TP1 V1,
    PRISM_CONTINUOUS_JOINT 16 -> 72). A familia oposta fica com a peca CURTA, o
    que cobre as duas fiadas com faces em posicoes diferentes."""
    result = _solve(True, True)
    assert result["course_b"] is not None
    assert result["course_b"]["logical_code"] in ("C09", "C04")
    assert result["course_b"]["logical_code"] != result["course_a"]["logical_code"]


def test_pastilha_still_used_when_the_stub_has_no_room_for_a_block():
    """A escada nao apaga o caso original: boneca curta continua recebendo
    compensador nas DUAS familias (nada de abrir buraco)."""
    entry = dict(CATALOG["B34"])
    catalog = dict(CATALOG)
    catalog["B34"] = entry
    nodes, walls, end_to_node, openings, index = _degraded_t()
    before = ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK
    ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK = True
    try:
        # boneca de 5 cm: nem o B34 nem o C09 cabem, so' o C04
        candidate_a = ws._corner_single_element_candidate(
            catalog, walls[1][0].GetEndPoint(0), m.XYZ(0.0, 1.0, 0.0), 5.0 / 30.48, "A", 1, 0, index,
            placement_reason="T_INTERSECTION_INCOMING_DEGRADED", nodes=nodes)
    finally:
        ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK = before
    assert candidate_a["logical_code"] == "C04"
