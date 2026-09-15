# -*- coding: utf-8 -*-
"""Secao 52 de REGRAS_MODULACAO_BLOCOS.md - VAZADO MENOR DO B34 ENTRE FIADAS.

Regra do usuario (2026-09-15): se existe um B34 numa fiada, a fiada vizinha
preserva o vazado menor dele. Evidencia (BUTANTA R08_LT, 1o PAV, via MCP,
somente leitura): 2.500 de 2.541 pares B34 x peca vazada da fiada vizinha tem
o vazado menor sobre vazado menor de B34 ou central de B54; no TARGET modulado
pelo solver, 2.460 de 3.426 pares estavam desalinhados.

Fixture fisica (relativa, sem ElementId/coordenada de projeto): parede
principal longa, parede perpendicular de 514 cm e uma parede de 444 cm que
une as duas em T (a geometria do caso reduzido do BUTANTA)."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import solver_bench as sb  # noqa: E402

m = sb.m
CATALOG = sb.CATALOG
ft = sb.ft
seg = sb.seg
import importlib  # noqa: E402
sva = importlib.import_module("core.engine.small_void_alignment")


def _lines(dx=0.0, dy=0.0, reverse=False, order=(0, 1, 2)):
    raw = [(437, -600, 437, 600), (7, -257, 7, 257), (0, 0, 444, 0)]
    out = []
    for x0, y0, x1, y1 in raw:
        if reverse:
            x0, y0, x1, y1 = x1, y1, x0, y0
        out.append(seg(x0 + dx, y0 + dy, x1 + dx, y1 + dy))
    return [out[i] for i in order]


def _solve(lines, courses=4, enabled=True):
    before = sva.SMALL_VOID_ORIENTATION_ENABLED
    sva.SMALL_VOID_ORIENTATION_ENABLED = enabled
    try:
        walls = [(line, ft(14.0), (False, False)) for line in lines]
        walls, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
        nodes, e2n = m.build_wall_graph(walls, jmap)
        res = m.solve_building_blocks_all_courses(nodes, walls, e2n, [[] for _ in walls], CATALOG, 0.0, courses,
                                                  variants_per_course=1)
    finally:
        sva.SMALL_VOID_ORIENTATION_ENABLED = before
    return res


def _signature(res):
    """Contorno fisico (sem orientacao): fiada, codigo, centro, eixo."""
    out = []
    for ci, cands in res["course_candidates"].items():
        for c in cands:
            o, xd = c["origin_world"], c["x_dir"]
            out.append((ci, c["logical_code"], round(o.X * 30.48, 1), round(o.Y * 30.48, 1),
                        "X" if abs(xd.X) > 0.5 else "Y"))
    return sorted(out)


def test_red_orientacao_fixa_deixa_vazado_menor_desalinhado():
    res = _solve(_lines(), enabled=False)
    assert res["small_void_alignment"]["after"] > 20, res["small_void_alignment"]["after"]


def test_green_orientacao_reduz_violacoes_sem_mudar_contorno():
    off = _solve(_lines(), enabled=False)
    on = _solve(_lines(), enabled=True)
    assert on["small_void_alignment"]["after"] < off["small_void_alignment"]["after"] / 3.0
    assert on["small_void_alignment"]["rotated"] > 0
    # mesmas pecas, mesmas posicoes, mesmas juntas: so' a orientacao muda
    assert _signature(on) == _signature(off)
    assert len(on.get("collisions") or []) == len(off.get("collisions") or [])


def test_peca_de_no_nunca_gira():
    off = _solve(_lines(), enabled=False)
    on = _solve(_lines(), enabled=True)

    def nodes_rot(res):
        return sorted((ci, c["logical_code"], round(c["origin_world"].X * 30.48, 1),
                       round(c["origin_world"].Y * 30.48, 1), round(c["rotation_deg"], 1))
                      for ci, cands in res["course_candidates"].items() for c in cands
                      if c.get("node_index") is not None)
    assert nodes_rot(on) == nodes_rot(off)


def test_giro_e_rigido_rotacao_bate_com_x_dir_e_vazado_menor_no_mesmo_lado_local():
    res = _solve(_lines(), enabled=True)
    for cands in res["course_candidates"].values():
        for c in cands:
            if c["logical_code"] != "B34":
                continue
            xd, o = c["x_dir"], c["origin_world"]
            angle = math.degrees(math.atan2(xd.Y, xd.X)) % 360.0
            delta = abs(angle - c["rotation_deg"] % 360.0)
            assert min(delta, 360.0 - delta) < 1e-6
            small = sva.candidate_small_cell(c)
            u = (small["point"].X - o.X) * xd.X + (small["point"].Y - o.Y) * xd.Y
            assert u < 0  # o lado local do vazado menor e' o do catalogo: o giro e' rigido


@pytest.mark.parametrize("variant", [
    dict(dx=1000.0, dy=-700.0), dict(reverse=True), dict(order=(2, 0, 1)), dict(order=(1, 2, 0), dx=-333.0)])
def test_invariante_a_translacao_ordem_e_sentido(variant):
    base = _solve(_lines(), enabled=True)
    other = _solve(_lines(**variant), enabled=True)
    assert other["small_void_alignment"]["after"] == base["small_void_alignment"]["after"]


def test_validador_b34_deslocado_20cm_girado_alinha_e_mesma_orientacao_nao():
    """Controle do validador com o arranjo humano: dois B34 em fiadas vizinhas
    deslocados 20 cm, um girado 180 graus em relacao ao outro, empilham o
    vazado menor; com a mesma orientacao, nao."""
    entry = CATALOG["B34"]
    X = m.XYZ
    a = m._make_block_candidate("B34", entry, "A", X(ft(17.0), 0.0, 0.0), X(1.0, 0.0, 0.0), "STANDARD_FILL")
    b_same = m._make_block_candidate("B34", entry, "B", X(ft(37.0), 0.0, 0.0), X(1.0, 0.0, 0.0), "STANDARD_FILL")
    b_flip = m._make_block_candidate("B34", entry, "B", X(ft(37.0), 0.0, 0.0), X(-1.0, 0.0, 0.0), "STANDARD_FILL")
    assert sva.b34_small_void_violations({0: [a], 1: [b_same]}, CATALOG)
    assert not sva.b34_small_void_violations({0: [a], 1: [b_flip]}, CATALOG)


def test_sem_peca_vazada_vizinha_nao_ha_restricao():
    entry = CATALOG["B34"]
    X = m.XYZ
    a = m._make_block_candidate("B34", entry, "A", X(ft(17.0), 0.0, 0.0), X(1.0, 0.0, 0.0), "STANDARD_FILL")
    comp = m._make_block_candidate("C09", CATALOG["C09"], "B", X(ft(10.0), 0.0, 0.0), X(1.0, 0.0, 0.0), "STANDARD_FILL")
    assert not sva.b34_small_void_violations({0: [a], 1: [comp]}, CATALOG)
    assert not sva.b34_small_void_violations({0: [a]}, CATALOG)
