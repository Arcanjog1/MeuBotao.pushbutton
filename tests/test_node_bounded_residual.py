# -*- coding: utf-8 -*-
"""Regra 30.8 - folga residual em trecho fechado por DOIS nos.

Defeito real (BUTANTA 1o PAV, vao 7719511): um anel fechado de 4 paredes com
4 cantos L (115 x 86 cm) ficava SEM NENHUM preenchimento em todas as fiadas -
os miolos (65 e 36 cm) estavam 1 e 2 cm fora do modulo - e a canaleta sob o
peitoril nao tinha onde assentar (MISSING_REQUIRED_CHANNEL). O humano fecha
os mesmos miolos com as pecas recuadas 0,5 cm (parede de 115) e 1,0 cm
(paredes de 86) das pontas. Fixtures derivadas da geometria, sem ElementId.

    python3 -m pytest tests/test_node_bounded_residual.py -q
"""
import contextlib
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
ft = sb.ft
seg = sb.seg

from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

NUM_COURSES = 14


@contextlib.contextmanager
def absorption(enabled):
    before = ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED
    ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED = enabled
    try:
        yield
    finally:
        ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED = before


def ring_lines():
    """Anel de shaft: paredes de 115 cm (y=1000 e y=928) e 86 cm (x=544 e x=645)."""
    return [seg(537, 1000, 652, 1000), seg(537, 928, 652, 928), seg(544, 921, 544, 1007), seg(645, 921, 645, 1007)]


def solve(lines, openings, strategy=None):
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    res = m.solve_building_blocks_all_courses(
        nodes, walls, e2n, openings, sb.CATALOG, 0.0, NUM_COURSES,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE, opening_reinforcement_strategy=strategy)
    res["num_courses"] = NUM_COURSES
    return res, walls


def ring_window():
    """Janela sob a qual o humano assenta canaleta: peitoril 40 (fiada 1)."""
    return [[(ft(19.5), ft(85.5), ft(40), ft(141))], [], [], []]


def test_ring_red_without_absorption_leaves_ring_empty_and_channel_missing():
    with absorption(False):
        res, _walls = solve(ring_lines(), ring_window(), strategy=orf.OPENING_REINFORCEMENT_CHANNEL)
    counts = res["opening_reinforcement"]["validation"]["counts"]
    assert counts["MISSING_REQUIRED_CHANNEL"] >= 1
    assert sum(1 for s in res["non_modular"] if s.get("wall_idx") in (0, 1, 2, 3)) > 0


def test_ring_green_with_absorption_closes_every_course_and_channel_is_present():
    with absorption(True):
        res, walls = solve(ring_lines(), ring_window(), strategy=orf.OPENING_REINFORCEMENT_CHANNEL)
    counts = res["opening_reinforcement"]["validation"]["counts"]
    assert counts["MISSING_REQUIRED_CHANNEL"] == 0
    assert counts["channel_top_matched"] == counts["channel_top_expected"] == 1
    assert counts["channel_bottom_matched"] == counts["channel_bottom_expected"] == 1
    assert counts["CHANNEL_INVADES_OPENING"] == 0 and counts["CHANNEL_COLLISION"] == 0
    assert not [s for s in res["non_modular"] if s.get("conflict") is None]
    assert res["residual_absorptions"]
    for item in res["residual_absorptions"]:
        assert 0 < item["residual_cm"] <= ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_MAX_CM + 1e-6


def test_ring_absorption_is_split_on_both_node_joints_and_never_overlaps():
    with absorption(True):
        res, walls = solve(ring_lines(), [[], [], [], []])
    assert not res["non_modular"]
    assert not res["collisions"]
    for ci, pieces in res["course_candidates"].items():
        for wi in range(4):
            rows = orf._wall_strip_pieces(pieces, walls, wi)
            for a, b in zip(rows, rows[1:]):
                gap = b["lo"] - a["hi"]
                assert gap >= 1.0 - 1e-6, (ci, wi, a["lo"], b["lo"])
                assert gap <= 1.0 + ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_MAX_CM / 2.0 + 1e-6, (ci, wi, gap)


def test_ring_absorption_creates_no_running_joint():
    with absorption(True):
        res, _walls = solve(ring_lines(), [[], [], [], []])
    for wi, audit in res["wall_bond_audits"].items():
        assert not [p for p in audit["problems"] if "CONTINUOUS_VERTICAL_JOINT" in str(p)], (wi, audit["problems"])


def test_residual_above_limit_is_not_absorbed():
    """Anel com parede de 118 cm: folga de 4 cm (> 2 cm) continua nao modular."""
    lines = [seg(537, 1000, 655, 1000), seg(537, 928, 655, 928), seg(544, 921, 544, 1007), seg(648, 921, 648, 1007)]
    with absorption(True):
        res, _walls = solve(lines, [[], [], [], []])
    long_nonmod = [s for s in res["non_modular"] if s.get("wall_idx") in (0, 1)]
    assert long_nonmod
    assert all(a["wall_idx"] not in (0, 1) for a in res["residual_absorptions"])


def test_opening_jamb_and_free_end_boundaries_never_absorb():
    """Parede livre com porta: os trechos terminam em ponta livre e em jamba -
    a folga nunca e' distribuida ali (a jamba e a ponta ficam onde estao)."""
    with absorption(True):
        res, _walls = solve([seg(0, 0, 601, 0)], [[(ft(200), ft(301), ft(0), ft(221))]])
    assert res["residual_absorptions"] == []


def test_legacy_walls_that_already_close_are_unchanged():
    """Paredes que ja' fechavam (sem trecho nao modular) e que nao receberam
    absorcao ficam com EXATAMENTE as mesmas pecas: planta de grade do benchmark."""
    runs = []
    for flag in (False, True):
        nodes, walls, e2n, openings = sb.make_plan(3, 3)
        with absorption(flag):
            res = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings, sb.CATALOG, 0.0, NUM_COURSES,
                                                      variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
        runs.append(res)
    before, after = runs
    closed = set(range(len(walls))) - set(s["wall_idx"] for s in before["non_modular"])
    touched = set(a["wall_idx"] for a in after["residual_absorptions"])
    keep = closed - touched

    def pieces(res):
        return sorted((ci, c["wall_idx"], c["logical_code"], round(c["origin_world"].X, 4),
                       round(c["origin_world"].Y, 4)) for ci, v in res["course_candidates"].items()
                      for c in v if c.get("wall_idx") in keep)

    assert keep
    assert pieces(before) == pieces(after)
