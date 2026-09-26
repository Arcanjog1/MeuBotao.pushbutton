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


def _solve(lines, courses=4, enabled=True, general=None):
    """`general=False` isola a secao 52 (so' orientacao): com as regras gerais de
    composicao (secao 81) o arranjo 60-65 tambem recompõe as corridas. Com `general`
    informado a paridade contextual (secao 82) fica desligada - estes testes medem
    orientacao e composicao sobre a MESMA paridade."""
    before = sva.SMALL_VOID_ORIENTATION_ENABLED
    before_general = m.GENERAL_COMPOSITION_QUALITY_ENABLED
    before_parity = m.GENERAL_TIE_PARITY_ENABLED
    sva.SMALL_VOID_ORIENTATION_ENABLED = enabled
    if general is not None:
        m.GENERAL_COMPOSITION_QUALITY_ENABLED = general
        m.GENERAL_TIE_PARITY_ENABLED = False
    try:
        walls = [(line, ft(14.0), (False, False)) for line in lines]
        walls, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
        nodes, e2n = m.build_wall_graph(walls, jmap)
        res = m.solve_building_blocks_all_courses(nodes, walls, e2n, [[] for _ in walls], CATALOG, 0.0, courses,
                                                  variants_per_course=1)
    finally:
        sva.SMALL_VOID_ORIENTATION_ENABLED = before
        m.GENERAL_COMPOSITION_QUALITY_ENABLED = before_general
        m.GENERAL_TIE_PARITY_ENABLED = before_parity
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
    res = _solve(_lines(), enabled=False, general=False)
    assert res["small_void_alignment"]["after"] > 20, res["small_void_alignment"]["after"]


def test_green_orientacao_reduz_violacoes_sem_mudar_contorno():
    off = _solve(_lines(), enabled=False, general=False)
    on = _solve(_lines(), enabled=True, general=False)
    assert on["small_void_alignment"]["after"] < off["small_void_alignment"]["after"] / 3.0
    assert on["small_void_alignment"]["rotated"] > 0
    # mesmas pecas, mesmas posicoes, mesmas juntas: so' a orientacao muda
    assert _signature(on) == _signature(off)
    assert len(on.get("collisions") or []) == len(off.get("collisions") or [])


def test_regras_gerais_nao_pioram_o_vazado_menor_da_secao_52():
    """SECAO 81: o arranjo geral (60-65) parte da orientacao da 52 e so' aceita
    parede que nao piora - o vazado menor final nunca fica pior que o da 52 so'."""
    so52 = _solve(_lines(), enabled=True, general=False)
    geral = _solve(_lines(), enabled=True, general=True)
    assert geral["small_void_alignment"]["after"] <= so52["small_void_alignment"]["after"]
    assert len(geral.get("collisions") or []) == len(so52.get("collisions") or [])


def test_peca_de_no_nunca_gira():
    # a MESMA paridade nos dois solves: com a secao 82 a paridade e' escolhida pelo
    # preenchimento real, que a orientacao (e o arranjo que depende dela) muda
    off = _solve(_lines(), enabled=False, general=True)
    on = _solve(_lines(), enabled=True, general=True)

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


def _piece_at(code, start_cm, course_label):
    entry = CATALOG[code]
    return m._place_pier_layout([(code, start_cm, start_cm + entry["length_cm"])], CATALOG,
                                m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0), course_label, 0)[0]


def _pair_only_case():
    """Dois B34 sobrepostos (deslocados 15 cm) em fiadas vizinhas, cada um com
    um B39 do outro lado: girar UM so' troca uma violacao por outra; girar os
    DOIS juntos alinha os dois vazados menores (padrao humano de corrida de
    B34 deslocada com orientacao oposta)."""
    a = _piece_at("B34", 0.0, "A")      # vazado menor a esquerda (6,8 cm)
    b = _piece_at("B34", 15.0, "B")     # vazado menor a esquerda (21,8 cm)
    sva.rotate_candidate_180(b)         # comeca a direita (42,2 cm): errado
    courses = {0: [a, _piece_at("B39", 35.0, "A")], 1: [_piece_at("B39", -25.0, "B"), b]}
    return courses, a, b


def test_pair_rotation_red_single_flips_cannot_fix():
    courses, a, b = _pair_only_case()
    before = len(sva.b34_small_void_violations(courses, CATALOG))
    assert before == 2
    for piece in (a, b):
        sva.rotate_candidate_180(piece)
        assert len(sva.b34_small_void_violations(courses, CATALOG)) >= before
        sva.rotate_candidate_180(piece)


def test_pair_rotation_green_aligns_both_small_voids():
    courses, a, b = _pair_only_case()
    summary = sva.orient_small_voids(courses, CATALOG)
    assert summary["before"] == 2 and summary["after"] == 0
    cell_a = sva.candidate_small_cell(a)["point"].X * 30.48
    cell_b = sva.candidate_small_cell(b)["point"].X * 30.48
    assert abs(cell_a - 27.2) < 0.2 and abs(cell_b - 21.8) < 0.2
