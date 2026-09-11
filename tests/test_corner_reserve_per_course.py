# -*- coding: utf-8 -*-
"""Regra 11.14 - RESERVA DE CANTO POR FIADA (decisao do usuario, 2026-09-11,
sobre a evidencia do projeto humano BUTANTA R08_LT).

Geometria REAL das tres paredes curtas de BUTANTA (cm, frame local): parede
de 64cm (x 1135..1199, y 1437) entre um canto com a vertical x=1142 (y 730..
1449) e um canto com a vertical x=1192 (y 1430..1944). O humano poe B34 num
canto na fiada A e no OUTRO canto na fiada B, com C04+C09 no meio:

    fiada par : [corpo da vizinha 0..14] C04 C09 B34[30,64]
    fiada impar: B34[0,34] C04 C09 [corpo da vizinha 50..64]

ANTES (pior caso fixo de 34cm nas duas fiadas para a outra ponta): a parede
"nao tinha espaco" para B34 em nenhuma fiada, os dois vizinhos recebiam B34
nas DUAS fiadas (faixa repetida na curta + junta corrida nos dois vizinhos:
3 paredes reprovadas). DEPOIS: 0 reprovadas, mesmo padrao do humano
(paridade espelhada), invariante a' ordem de entrada.

O CAD 'Paredes' desenha essas tres paredes com 99cm (toco de 34cm alem da
vizinha, que NAO e' alvenaria no projeto pronto): esse caso continua
reprovado e fica registrado como geometria de entrada, nao como regra.
"""
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
ws = sys.modules["core.engine.wall_stepper"]
F2CM = 30.48

CORNER = seg(1142, 730, 1142, 1449)
TEE = seg(1192, 1430, 1192, 1944)
SHORT64 = seg(1135, 1437, 1199, 1437)
SHORT99 = seg(1135, 1437, 1234, 1437)


@pytest.fixture
def flag():
    before = ws.CORNER_RESERVE_PER_COURSE
    yield
    ws.CORNER_RESERVE_PER_COURSE = before


def _solve(lines):
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jmap)
    opw = [[] for _ in walls]
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, opw, CATALOG, 0.0, 14,
                                              variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    res["num_courses"] = 14
    pf = m.controlled_beta_preflight(res, walls, opw, CATALOG, 0.0)
    return res, pf, walls


def _reproved(res):
    return sorted(wi for wi, a in res["wall_bond_audits"].items() if not a["ok"])


def _seq(res, walls, wall_idx, course_index):
    p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, wall_idx)
    items = []
    for c in res["course_candidates"].get(course_index, []):
        if c["wall_idx"] != wall_idx:
            continue
        lo, hi = m._candidate_extent_on_wall_axis(c, p0, d)
        items.append((round(lo), round(hi), c["logical_code"]))
    return sorted(items)


def _short_idx(walls):
    return min(range(len(walls)), key=lambda i: walls[i][0].Length)


def test_antes_pior_caso_fixo_reprova_as_tres_paredes(flag):
    ws.CORNER_RESERVE_PER_COURSE = False
    res, pf, walls = _solve([SHORT64, CORNER, TEE])
    assert pf["ok"] and not pf["collisions"]
    assert _reproved(res) == [0, 1, 2], _reproved(res)
    s = _short_idx(walls)
    # a curta nao ganha canto em fiada nenhuma: mesmo B34 de enchimento nas duas
    assert _seq(res, walls, s, 0) == _seq(res, walls, s, 1) == [(15, 49, "B34")]


def test_depois_um_canto_por_fiada_como_o_humano(flag):
    ws.CORNER_RESERVE_PER_COURSE = True
    res, pf, walls = _solve([SHORT64, CORNER, TEE])
    assert pf["ok"] and not pf["collisions"]
    assert not res["intersection_failures"]
    assert not res["non_modular"], res["non_modular"]
    assert _reproved(res) == [], _reproved(res)
    s = _short_idx(walls)
    c0, c1 = _seq(res, walls, s, 0), _seq(res, walls, s, 1)
    # um B34 de canto em cada fiada, em cantos OPOSTOS, e C04+C09 no meio
    b34 = {0: [i for i in c0 if i[2] == "B34"], 1: [i for i in c1 if i[2] == "B34"]}
    assert len(b34[0]) == 1 and len(b34[1]) == 1, (c0, c1)
    ends = sorted([b34[0][0][0], b34[1][0][0]])
    assert ends == [0, 30], (c0, c1)          # um encosta na ponta 0, o outro na ponta 64
    for seq in (c0, c1):
        codes = sorted(i[2] for i in seq)
        assert codes == ["B34", "C04", "C09"], seq


@pytest.mark.parametrize("order", [(0, 1, 2), (2, 0, 1), (1, 2, 0)])
def test_invariante_a_ordem_de_entrada(flag, order):
    ws.CORNER_RESERVE_PER_COURSE = True
    lines = [SHORT64, CORNER, TEE]
    res, pf, walls = _solve([lines[i] for i in order])
    assert pf["ok"] and _reproved(res) == [] and not res["non_modular"]
    s = _short_idx(walls)
    multiset = sorted(sorted(i[2] for i in _seq(res, walls, s, ci)) for ci in (0, 1))
    assert multiset == [["B34", "C04", "C09"], ["B34", "C04", "C09"]]


def test_toco_de_34cm_do_cad_continua_reprovado_geometria_de_entrada(flag):
    """LIMITE DE ENTRADA, nao de regra: com o toco de 34cm alem da vizinha
    (99cm no CAD 'Paredes'; o layer estrutural cobre so' 65%), a parede
    continua com junta corrida - e' o que o projeto humano NAO constroi."""
    ws.CORNER_RESERVE_PER_COURSE = True
    res, pf, walls = _solve([SHORT99, CORNER, TEE])
    assert pf["ok"]
    assert _short_idx(walls) in _reproved(res)


def test_parede_longa_entre_dois_cantos_nao_muda(flag):
    """Controle: com espaco de sobra a regra e' neutra - mesmo resultado com
    e sem a reserva por fiada."""
    lines = [seg(0, 0, 400, 0), seg(0, 0, 0, 300), seg(400, 0, 400, 300)]
    out = {}
    for value in (False, True):
        ws.CORNER_RESERVE_PER_COURSE = value
        res, pf, walls = _solve(lines)
        out[value] = (pf["ok"], _reproved(res), [_seq(res, walls, i, ci) for i in range(3) for ci in (0, 1)])
    assert out[False] == out[True]
