# -*- coding: utf-8 -*-
"""Validador de APOIO FISICO entre fiadas (secao 53, 2026-09-15).

Peca da fiada c >= 1 com menos de metade do comprimento sobre peca da fiada
de baixo, e menos de metade sobre vao ativo, e' reportada:
UNSUPPORTED_SMALL_BLOCK (B19/C09/C04) ou UNSUPPORTED_BLOCK. Fixtures
sinteticas, sem ElementId.

    python3 -m pytest tests/test_physical_support_audit.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
ft = sb.ft
from core.engine import physical_support as ps  # noqa: E402

WALL = [(sb.seg(0, 0, 400, 0), ft(14.0), (False, False))]


def _piece(code, start_cm, course_label="A"):
    entry = sb.CATALOG[code]
    p0, d = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    return m._place_pier_layout([(code, start_cm, start_cm + entry["length_cm"])], sb.CATALOG, p0, d,
                                course_label, 0)[0]


def _band(course_index):
    z = ft(1.0 + 20.0 * course_index)
    return z, z + ft(19.0)


def test_small_block_flying_over_empty_course_is_reported():
    courses = {0: [_piece("B39", 0.0)], 1: [_piece("B19", 100.0)]}
    items = ps.unsupported_pieces(courses, WALL, [[]], _band)
    assert [(i["kind"], i["code"], i["course"]) for i in items] == [("UNSUPPORTED_SMALL_BLOCK", "B19", 1)]


def test_block_with_half_support_or_more_is_not_reported():
    courses = {0: [_piece("B39", 0.0)], 1: [_piece("B39", 19.0)]}
    assert ps.unsupported_pieces(courses, WALL, [[]], _band) == []
    courses = {0: [_piece("B39", 0.0)], 1: [_piece("B39", 21.0)]}
    items = ps.unsupported_pieces(courses, WALL, [[]], _band)
    assert [(i["kind"], i["code"]) for i in items] == [("UNSUPPORTED_BLOCK", "B39")]


def test_piece_over_an_active_opening_is_reinforcement_not_unsupported():
    # vao [100, 140] cm ativo na fiada 0 (peitoril 0, topo 21 cm)
    openings = [[(ft(100.0), ft(140.0), 0.0, ft(21.0))]]
    courses = {0: [_piece("B39", 60.0), _piece("B39", 141.0)], 1: [_piece("B39", 100.0)]}
    assert ps.unsupported_pieces(courses, WALL, openings, _band) == []
    # o mesmo vao fora da faixa da fiada de baixo nao desculpa nada
    openings = [[(ft(100.0), ft(140.0), ft(200.0), ft(300.0))]]
    assert ps.unsupported_pieces(courses, WALL, openings, _band)


def test_support_from_perpendicular_wall_counts():
    wall_y = sb.seg(50, -100, 50, 100)
    walls = WALL + [(wall_y, ft(14.0), (False, False))]
    below = m._place_pier_layout([("B39", 0.0, 39.0)], sb.CATALOG, m.XYZ(ft(50), ft(-19.5), 0.0),
                                 m.XYZ(0.0, 1.0, 0.0), "A", 1)[0]
    courses = {0: [below], 1: [_piece("C09", 45.5)]}
    assert ps.unsupported_pieces(courses, walls, [[], []], _band) == []


def test_order_is_deterministic_under_input_permutation():
    pieces = [_piece("B19", 100.0), _piece("C09", 200.0), _piece("C04", 300.0)]
    a = ps.unsupported_pieces({0: [], 1: list(pieces)}, WALL, [[]], _band)
    b = ps.unsupported_pieces({0: [], 1: list(reversed(pieces))}, WALL, [[]], _band)
    assert a == b and len(a) == 3
