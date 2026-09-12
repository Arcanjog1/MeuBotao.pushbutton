# -*- coding: utf-8 -*-
"""Sonda de vao `_room_at_t_on_wall` x ponto DENTRO de uma abertura.

Defeito auditado (AUDITORIA_BETA_2026-09-09, secao 5, "Portas/janelas"):
quando o ponto sondado `t_ft` cai DENTRO de uma abertura (t_lo < t_ft <
t_hi), a sonda ignorava essa abertura - o filtro so' enxergava aberturas
INTEIRAMENTE a frente (`t_lo >= t_ft`) ou INTEIRAMENTE atras (`t_hi <=
t_ft`) - e media espaco ate' o proximo obstaculo ATRAVES do vazio da porta.
O solver concluia que havia espaco para uma peca de amarracao e a punha
dentro do vao (OPENING_BLOCK_INSIDE_DOOR; caso W019 do TP1; regressao 0->7
na bisseccao 11.10 de 2026-09-11).

Geometria SINTETICA e geral: nenhuma coordenada, porta, largura ou peca
especifica do corpus entra aqui. A regra e' puramente geometrica - a
disponibilidade a partir de um ponto no vazio e' ZERO em qualquer sentido,
porque nao existe alvenaria onde apoiar a peca.
"""
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

WALL_CM = 600.0
TOL_CM = 1e-3


def _cm(value_ft):
    return value_ft * 100.0 / m.FEET_PER_METER


def _wall():
    return [(seg(0.0, 0.0, WALL_CM, 0.0), ft(14.0), (False, False))]


def _opening(t_lo_cm, t_hi_cm, sill_cm=0.0, head_cm=210.0):
    return (ft(t_lo_cm), ft(t_hi_cm), ft(sill_cm), ft(head_cm))


def room_cm(openings, t_cm, sign, safe_range_cm=None):
    walls = _wall()
    safe_range = None
    if safe_range_cm is not None:
        safe_range = (ft(safe_range_cm[0]), ft(safe_range_cm[1]))
    return _cm(m._room_at_t_on_wall(walls, [openings], 0, ft(t_cm), sign, safe_range))


DOOR = [_opening(200.0, 300.0)]


# --------------------------------------------------------------- controle A
def test_A_ponto_antes_da_abertura_para_na_jamba_e_na_ponta():
    assert room_cm(DOOR, 100.0, +1) == pytest.approx(100.0, abs=TOL_CM)   # ate' a jamba em 200
    assert room_cm(DOOR, 100.0, -1) == pytest.approx(100.0, abs=TOL_CM)   # ate' a ponta em 0


# --------------------------------------------------------------- controle B
def test_B_ponto_depois_da_abertura_para_na_ponta_e_na_jamba():
    assert room_cm(DOOR, 400.0, +1) == pytest.approx(200.0, abs=TOL_CM)   # ate' a ponta em 600
    assert room_cm(DOOR, 400.0, -1) == pytest.approx(100.0, abs=TOL_CM)   # ate' a jamba em 300


# ------------------------------------------------------------------- caso C
@pytest.mark.parametrize("t_cm", [210.0, 250.0, 290.0])
@pytest.mark.parametrize("sign", [+1, -1])
def test_C_ponto_dentro_da_abertura_nao_tem_espaco_em_nenhum_sentido(t_cm, sign):
    """O ponto esta' no VAZIO da porta (~10cm para dentro da jamba, no meio,
    ~10cm da outra jamba): a sonda nunca pode atravessar o vao e informar
    espaco continuo ate' o proximo obstaculo."""
    assert room_cm(DOOR, t_cm, sign) == pytest.approx(0.0, abs=TOL_CM)


def test_C_ponto_dentro_da_abertura_continua_sem_espaco_com_safe_range():
    """O `safe_range_ft` (reserva de outro encontro nas pontas) nao reabre o
    vao: o vazio e' um obstaculo antes de qualquer limite de reserva."""
    assert room_cm(DOOR, 210.0, +1, safe_range_cm=(30.0, 570.0)) == pytest.approx(0.0, abs=TOL_CM)
    assert room_cm(DOOR, 210.0, -1, safe_range_cm=(30.0, 570.0)) == pytest.approx(0.0, abs=TOL_CM)


# ------------------------------------------------------------------- caso D
def test_D_ponto_exatamente_na_jamba():
    """Na jamba de entrada (t=200) andando PARA o vao: zero; andando para
    fora: ate' a ponta. Na jamba de saida (t=300) o simetrico."""
    assert room_cm(DOOR, 200.0, +1) == pytest.approx(0.0, abs=TOL_CM)
    assert room_cm(DOOR, 200.0, -1) == pytest.approx(200.0, abs=TOL_CM)
    assert room_cm(DOOR, 300.0, +1) == pytest.approx(300.0, abs=TOL_CM)
    assert room_cm(DOOR, 300.0, -1) == pytest.approx(0.0, abs=TOL_CM)


@pytest.mark.parametrize("delta_cm", [0.05, 0.5, 2.0])
def test_D_ponto_logo_apos_a_jamba_ja_esta_no_vazio(delta_cm):
    """Um ponto uns milimetros/centimetros para DENTRO da jamba ja' esta' no
    vao: zero nos dois sentidos (nao ha' 'quase-jamba' que reabra o vao)."""
    assert room_cm(DOOR, 200.0 + delta_cm, +1) == pytest.approx(0.0, abs=TOL_CM)
    assert room_cm(DOOR, 200.0 + delta_cm, -1) == pytest.approx(0.0, abs=TOL_CM)
    assert room_cm(DOOR, 300.0 - delta_cm, +1) == pytest.approx(0.0, abs=TOL_CM)
    assert room_cm(DOOR, 300.0 - delta_cm, -1) == pytest.approx(0.0, abs=TOL_CM)


# ------------------------------------------------------------------- caso E
def test_E_endpoints_da_abertura_invertidos_dao_o_mesmo_resultado():
    """A tupla e' (t_lo, t_hi, sill, head); se vier com t_lo > t_hi a sonda
    tem de tratar como o MESMO intervalo fisico, nunca como 'sem abertura'."""
    inverted = [_opening(300.0, 200.0)]
    for t_cm in (100.0, 210.0, 250.0, 290.0, 400.0, 200.0, 300.0):
        for sign in (+1, -1):
            assert room_cm(inverted, t_cm, sign) == pytest.approx(room_cm(DOOR, t_cm, sign), abs=TOL_CM), (t_cm, sign)
    assert room_cm(inverted, 250.0, +1) == pytest.approx(0.0, abs=TOL_CM)


# ------------------------------------------------------------------- caso F
TWO = [_opening(200.0, 300.0), _opening(400.0, 450.0)]


def test_F_duas_aberturas_na_mesma_parede():
    # entre as duas: para na jamba mais proxima de cada lado
    assert room_cm(TWO, 350.0, +1) == pytest.approx(50.0, abs=TOL_CM)
    assert room_cm(TWO, 350.0, -1) == pytest.approx(50.0, abs=TOL_CM)
    # dentro da segunda
    assert room_cm(TWO, 420.0, +1) == pytest.approx(0.0, abs=TOL_CM)
    assert room_cm(TWO, 420.0, -1) == pytest.approx(0.0, abs=TOL_CM)
    # dentro da primeira
    assert room_cm(TWO, 250.0, +1) == pytest.approx(0.0, abs=TOL_CM)
    assert room_cm(TWO, 250.0, -1) == pytest.approx(0.0, abs=TOL_CM)
    # antes de todas / depois de todas
    assert room_cm(TWO, 100.0, +1) == pytest.approx(100.0, abs=TOL_CM)
    assert room_cm(TWO, 500.0, -1) == pytest.approx(50.0, abs=TOL_CM)
    assert room_cm(TWO, 500.0, +1) == pytest.approx(100.0, abs=TOL_CM)
    # a ordem da lista nao importa
    assert room_cm(list(reversed(TWO)), 350.0, +1) == pytest.approx(50.0, abs=TOL_CM)
    assert room_cm(list(reversed(TWO)), 420.0, -1) == pytest.approx(0.0, abs=TOL_CM)


# ------------------------------------------------- consequencia no solver
def test_T_dentro_da_porta_nao_lanca_peca_de_amarracao_no_vao():
    """Consequencia da sonda no solver: um encontro em T cujo no' cai DENTRO
    de uma porta da parede principal nao pode receber B54/B34 dentro do vao.
    Sem a correcao, `_t_intersection_room_ok` via 'espaco' atravessando a
    porta e a peca de amarracao era posicionada no vazio.

    Verificacao geometrica direta, sem validador do benchmark: nenhuma peca
    emitida na fiada em que a porta esta' ativa pode ter >= 90% do seu
    comprimento dentro do intervalo do vao."""
    main = seg(0.0, 0.0, 600.0, 0.0)
    incoming = seg(250.0, 0.0, 250.0, 300.0)   # no' T em t=250, no meio da porta [200,300]
    walls = [(main, ft(14.0), (False, False)), (incoming, ft(14.0), (False, False))]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    assert any(n["kind"] == "T_INTERSECTION" for n in nodes), nodes
    openings = [[_opening(200.0, 300.0, 0.0, 210.0)], []]
    result = m.solve_building_blocks_all_courses(
        nodes, walls, end_to_node, openings, sb.CATALOG, ft(0.0), 4,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    p0, _p1, wall_dir, _len, _t = m._wall_axis_and_length(walls, 0)
    inside = []
    for course_key, pieces in result["course_candidates"].items():
        for piece in pieces:
            if piece.get("wall_idx") != 0:
                continue
            t_lo, t_hi = m._candidate_extent_on_wall_axis(piece, p0, wall_dir)   # ja' em cm
            lo, hi = min(t_lo, t_hi), max(t_lo, t_hi)
            overlap = max(0.0, min(hi, 300.0) - max(lo, 200.0))
            if overlap >= 0.9 * (hi - lo):
                inside.append((course_key, piece.get("logical_code"), piece.get("placement_reason"), round(lo, 1), round(hi, 1)))
    assert inside == [], inside
