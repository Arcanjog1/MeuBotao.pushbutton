# -*- coding: utf-8 -*-
"""Bug real (medido em BUTANTA, paredes de 99cm, 2026-09-11): a reserva de
amarracao numa PONTA LIVRE era 34cm. `_wall_end_default_start_cm` devolve 0
para FREE_END/STRAIGHT_CONTINUATION ("nada para encostar"), mas
`_wall_reserved_range_ft` aplicava `max(reserva, CORNER_B34_ROOM_FT)` a toda
ponta com no' - inclusive a livre. Um T a 42cm de uma ponta livre media 8cm de
espaco em vez de 42 e degradava para um compensador nas duas fiadas (junta
corrida em 14 fiadas); o humano poe B34 na principal."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
CATALOG = sb.CATALOG
ft = sb.ft
seg = sb.seg
ws = sys.modules["core.engine.wall_stepper"]
F2CM = 30.48


def _graph(lines):
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jmap)
    return walls, nodes, e2n


def test_ponta_livre_nao_reserva_nada():
    walls, nodes, e2n = _graph([seg(0, 0, 0, 600), seg(-200, 300, 0, 300)])   # principal com 2 pontas livres
    lo, hi = ws._wall_reserved_range_ft(walls, nodes, e2n, 0)
    assert lo * F2CM < 1e-6 and abs(hi * F2CM - walls[0][0].Length * F2CM) < 1e-6, (lo * F2CM, hi * F2CM)


def test_canto_continua_reservando_34():
    walls, nodes, e2n = _graph([seg(0, 0, 340, 0), seg(0, 0, 0, 69)])
    lo, hi = ws._wall_reserved_range_ft(walls, nodes, e2n, 0)
    assert abs(lo * F2CM - 34.0) < 1e-6, lo * F2CM
    assert abs(hi * F2CM - walls[0][0].Length * F2CM) < 1e-6   # a outra ponta e' livre


def test_T_perto_da_ponta_livre_degrada_para_B34_e_nao_compensador():
    """Parede curta 0..99 com canto em t=0 e ponta livre em t=99; T em t=57."""
    walls, nodes, e2n = _graph([seg(0, 0, 99, 0), seg(0, 0, 0, -300), seg(57, 0, 57, 300)])
    t_nodes = [i for i, n in enumerate(nodes) if n["kind"] == "T_INTERSECTION"]
    assert len(t_nodes) == 1, [n["kind"] for n in nodes]
    out = m.solve_all_intersections(nodes, walls, CATALOG, openings_per_wall=[[] for _ in walls], end_to_node=e2n)
    pieces = sorted((c["course"], c["logical_code"], c["placement_reason"])
                    for c in out["candidates"] if c["node_index"] == t_nodes[0])
    codes = [code for _c, code, _r in pieces]
    assert "C09" not in codes and "C04" not in codes, pieces
    assert codes in (["B34", "B34"], ["B54", "B34"]), pieces
