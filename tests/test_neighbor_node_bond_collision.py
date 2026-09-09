# -*- coding: utf-8 -*-
"""CR-BLOCK-NEIGHBOR-NODE-ROOM - duas pecas de amarracao de nos VIZINHOS
da MESMA parede nao podem ocupar o mesmo volume.

Causa-raiz medida na varredura ampla do benchmark offline (2026-09-08):
`_room_at_t_on_wall` so' parava em ABERTURA, na reserva das duas PONTAS
da parede (`_wall_reserved_range_ft`) e na ponta fisica - nunca num no'
de encontro no MEIO da parede. Dois T na mesma parede principal, a `d`
cm um do outro, cada um media espaco ate' a proxima abertura, cada um se
achava com folga e cada um lancava o seu B54 CENTRADO no proprio ponto:
as duas pecas se sobrepunham em exatamente `54 - d` cm.

As 8 identidades de `POSITION_OVERLAP` do TGD+TP1 eram este caso.

Geometria sintetica apenas - nenhuma coordenada de projeto real.

    python3 -m pytest tests/test_neighbor_node_bond_collision.py -q
"""

import pytest

import load_script
import revit_stubs

from test_block_bonding import (CATALOG, ft, seg, solve_plan,
                                wall_course_extents)

m = load_script.load()


def _overlaps_on_wall(walls, candidates, wall_idx):
    """[(t_lo, t_hi, codigo_a, codigo_b, sobreposicao_cm)] de todo par de
    pecas da MESMA fiada de `wall_idx` que ocupa o mesmo volume."""
    extents = wall_course_extents(walls, candidates)
    found = []
    for (w_idx, course), items in sorted(extents.items(),
                                         key=lambda kv: (kv[0][0], kv[0][1])):
        if w_idx != wall_idx:
            continue
        for i in range(len(items) - 1):
            a_lo, a_hi, a_code, _a_tie = items[i]
            b_lo, b_hi, b_code, _b_tie = items[i + 1]
            overlap = a_hi - b_lo
            if overlap > 0.01:
                found.append((course, a_code, b_code, overlap))
    return found


def _plan_two_ts(distance_cm):
    """Parede principal longa (E-O) com DUAS bonecas perpendiculares a
    `distance_cm` uma da outra, as duas longe das pontas - dois nos de
    MEIO DE PAREDE, exatamente a topologia que produzia a colisao."""
    main_len = 800.0
    first_t = 300.0
    second_t = first_t + distance_cm
    return [
        seg(0.0, 0.0, main_len, 0.0),          # 0: parede principal
        seg(first_t, 0.0, first_t, 200.0),     # 1: boneca A
        seg(second_t, 0.0, second_t, 200.0),   # 2: boneca B
    ]


@pytest.mark.parametrize("distance_cm", [12.0, 20.0, 28.0, 35.0, 45.0, 50.0])
def test_dois_nos_vizinhos_nunca_sobrepoem_pecas_de_amarracao(distance_cm):
    """Qualquer distancia ABAIXO do alcance somado das duas pecas: nenhuma
    sobreposicao de volume na parede principal. Antes da correcao, cada
    par produzia exatamente `54 - distancia` cm de sobreposicao."""
    result, walls, _nodes = solve_plan(_plan_two_ts(distance_cm))
    overlaps = _overlaps_on_wall(walls, result["candidates"], 0)
    assert overlaps == [], (
        "nos a {0}cm: pecas de amarracao sobrepostas na parede principal "
        "-> {1}".format(distance_cm, overlaps))


@pytest.mark.parametrize("distance_cm", [70.0, 90.0, 140.0])
def test_nos_bem_separados_continuam_recebendo_a_peca_cheia(distance_cm):
    """Acima de `NEIGHBOR_NODE_BOND_CLEARANCE_FT` (34+34cm) a checagem nova
    NAO pode mudar nada: os dois nos continuam ganhando o B54 inteiro. E' a
    guarda contra o risco oposto - degradar amarracao que sempre coube."""
    result, walls, _nodes = solve_plan(_plan_two_ts(distance_cm))
    extents = wall_course_extents(walls, result["candidates"])
    b54_rows = [items for (w_idx, _c), items in extents.items()
                if w_idx == 0
                for items in [[e for e in items if e[2] == "B54"]]]
    assert any(len(items) >= 2 for items in b54_rows), (
        "nos a {0}cm cabem os dois B54 inteiros, mas a solucao nao os "
        "colocou".format(distance_cm))
    assert _overlaps_on_wall(walls, result["candidates"], 0) == []


def test_limite_de_folga_e_a_soma_do_pior_caso_de_cada_lado():
    """`NEIGHBOR_NODE_BOND_CLEARANCE_FT` e' 2x `CORNER_B34_ROOM_FT` (34cm
    de cada lado) - o alcance maximo que uma peca de amarracao degradada
    pede para UM lado do no'. Fixar isso aqui evita que a constante seja
    afrouxada sem que a conta seja refeita."""
    assert m.NEIGHBOR_NODE_BOND_CLEARANCE_FT == pytest.approx(
        2.0 * m.CORNER_B34_ROOM_FT)


def test_ponto_medio_e_simetrico_entre_os_dois_nos():
    """A fronteira entre dois nos vizinhos e' o PONTO MEDIO: os dois sao
    resolvidos independentemente, entao so' um criterio simetrico faz as
    duas medicoes concordarem sem uma segunda passada de coordenacao."""
    lines = _plan_two_ts(40.0)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(
        walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _end_to_node = m.build_wall_graph(walls, junction_map)

    ts = sorted(m._wall_junction_ts_ft(walls, nodes, 0))
    assert len(ts) >= 2, "esperado ao menos dois nos na parede principal"
    t_a, t_b = ts[0], ts[1]

    forward = m._neighbor_node_boundary_ft(walls, nodes, 0, t_a, 1)
    backward = m._neighbor_node_boundary_ft(walls, nodes, 0, t_b, -1)
    assert forward is not None and backward is not None
    assert forward == pytest.approx(backward), (
        "as duas medicoes precisam concordar sobre a MESMA fronteira")
    assert forward == pytest.approx((t_a + t_b) / 2.0)


def test_sem_nodes_o_comportamento_historico_e_preservado():
    """Chamador antigo (`nodes=None`) nao ganha limite nenhum - a correcao
    e' estritamente aditiva."""
    lines = _plan_two_ts(35.0)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(
        walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _end_to_node = m.build_wall_graph(walls, junction_map)
    ts = sorted(m._wall_junction_ts_ft(walls, nodes, 0))
    assert m._neighbor_node_boundary_ft(walls, None, 0, ts[0], 1) is None


# ============================================================
# CR-N1b - a reserva das PONTAS nao pode ser cobrada DUAS VEZES
#
# `_wall_reserved_range_ft` ja' reserva, para CADA PONTA da parede, o
# PIOR CASO (`CORNER_B34_ROOM_FT` = 34cm) medido a partir da ponta
# FISICA. A CR-N1 passou a cobrar TAMBEM o ponto medio ate' o no'
# vizinho - e, para os nos que estao nas PONTAS, esses dois mecanismos
# descontam a MESMA reserva. Como o codigo fica com o MINIMO dos dois, a
# parede curta perdia espaco que nao devia a ninguem.
#
# Medido no TGD real (2026-09-09), parede de 69cm entre dois L_CORNER
# (`W|-1.5,463.0|-1.5,532.0|t14.0` e
# `W|-1016.5,-570.0|-1016.5,-501.0|t14.0`): a peca de amarracao do canto
# caiu de B34 para um C09 `L_CORNER_DEGRADED` - um COMPENSADOR de 9cm
# fazendo o papel de peca de amarracao de canto - e as duas paredes
# passaram de ZERO para ~50 compensadores cada.
# ============================================================

def _plan_short_wall_between_two_l_corners(axis_len_cm):
    """Duas paredes longas paralelas ligadas por uma CURTA - um L_CORNER
    em cada ponta da curta, e NENHUM no' no meio dela. `axis_len_cm` e' o
    comprimento do EIXO da curta depois de
    `extend_wall_ends_to_junctions` (as pontas andam meia espessura para
    cada lado, entao o vao livre e' `axis_len_cm - 14`)."""
    vao = axis_len_cm - 14.0      # distancia entre os eixos das duas longas
    return [
        seg(0.0, 0.0, 0.0, 400.0),            # 0: longa esquerda
        seg(vao, 0.0, vao, 400.0),            # 1: longa direita
        seg(7.0, 0.0, vao - 7.0, 0.0),        # 2: a CURTA
    ]


def _short_wall_graph(axis_len_cm):
    lines = _plan_short_wall_between_two_l_corners(axis_len_cm)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(
        walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    return walls, nodes, end_to_node


def _rooms_for_short_wall(axis_len_cm):
    """[(historico, cr_n1_sem_correcao, corrigido)] em cm, para cada no'
    da parede curta e cada sentido em que ha' espaco util."""
    walls, nodes, end_to_node = _short_wall_graph(axis_len_cm)
    wall_idx = 2
    openings = dict((i, []) for i in range(len(walls)))
    out = []
    for node_obj, t_ft in m._wall_junction_nodes_and_ts_ft(walls, nodes, wall_idx):
        node_index = m._node_index_of(nodes, node_obj)
        safe = m._wall_reserved_range_ft(walls, nodes, end_to_node, wall_idx,
                                         exclude_node_index=node_index)
        for sign in (1, -1):
            historico = m._room_at_t_on_wall(
                walls, openings, wall_idx, t_ft, sign, safe_range_ft=safe)
            sem_correcao = m._room_at_t_on_wall(
                walls, openings, wall_idx, t_ft, sign, safe_range_ft=safe,
                nodes=nodes, exclude_node_index=node_index)
            corrigido = m._room_at_t_on_wall(
                walls, openings, wall_idx, t_ft, sign, safe_range_ft=safe,
                nodes=nodes, exclude_node_index=node_index,
                end_to_node=end_to_node)
            out.append((historico / m.FEET_PER_METER * 100.0,
                        sem_correcao / m.FEET_PER_METER * 100.0,
                        corrigido / m.FEET_PER_METER * 100.0))
    return out


@pytest.mark.parametrize("axis_len_cm", [69.0, 74.0, 81.0])
def test_reproducer_a_dupla_contagem_encolhe_a_parede_curta(axis_len_cm):
    """PRE-FIX: sem `end_to_node`, o ponto medio corta espaco que a
    reserva de ponta JA' tinha descontado. Falha se a correcao for
    revertida (a' sem ela, `sem_correcao == corrigido`)."""
    medidas = _rooms_for_short_wall(axis_len_cm)
    encolhidos = [(h, s, c) for h, s, c in medidas if s < h - 1e-6]
    assert encolhidos, (
        "esperava a dupla contagem visivel em %.1fcm: %s" % (axis_len_cm, medidas))


@pytest.mark.parametrize("axis_len_cm", [69.0, 74.0, 81.0])
def test_no_de_ponta_nao_e_cobrado_duas_vezes(axis_len_cm):
    """POS-FIX: com `end_to_node`, o espaco volta a ser EXATAMENTE o
    historico - a reserva de ponta e' cobrada uma vez so'."""
    for historico, _sem_correcao, corrigido in _rooms_for_short_wall(axis_len_cm):
        assert corrigido == pytest.approx(historico, abs=1e-9), (
            "a reserva de ponta foi cobrada duas vezes em %.1fcm: "
            "historico=%.2fcm corrigido=%.2fcm" % (axis_len_cm, historico, corrigido))


def test_o_limiar_fisico_do_b34_e_o_que_estava_em_jogo():
    """O efeito FISICO: com eixo de 81cm o canto tem 40,00cm historicos -
    acima de `CORNER_B34_ROOM_FT` (34cm), entao o L recebe B34. A dupla
    contagem derrubava para 33,50cm, ABAIXO do limiar - e o canto caia
    para `L_CORNER_DEGRADED` (um compensador no lugar da peca de
    amarracao). A correcao devolve os 40,00cm."""
    medidas = _rooms_for_short_wall(81.0)
    limiar = m.CORNER_B34_ROOM_FT / m.FEET_PER_METER * 100.0
    cruzou = [(h, s, c) for h, s, c in medidas if h >= limiar > s]
    assert cruzou, (
        "esperava pelo menos um sentido em que a dupla contagem cruza o "
        "limiar do B34 (%.1fcm): %s" % (limiar, medidas))
    for _h, _s, corrigido in cruzou:
        assert corrigido >= limiar - 1e-9, (
            "com a correcao o B34 tem de voltar a caber: %.2fcm < %.2fcm"
            % (corrigido, limiar))


def test_no_de_MEIO_de_parede_continua_limitando_com_end_to_node():
    """GUARDA do ganho da CR-N1: `end_to_node` isenta SO' os nos das duas
    PONTAS. Um no' de MEIO DE PAREDE (o T que produzia os
    `POSITION_OVERLAP`) continua impondo a fronteira do ponto medio."""
    lines = _plan_two_ts(35.0)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(
        walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    ts = sorted(m._wall_junction_ts_ft(walls, nodes, 0))
    t_a, t_b = ts[0], ts[1]
    skip = (end_to_node.get((0, 0)), end_to_node.get((0, 1)))
    fronteira = m._neighbor_node_boundary_ft(walls, nodes, 0, t_a, 1,
                                             skip_node_indices=skip)
    assert fronteira is not None, (
        "o no' de MEIO DE PAREDE nao pode ser isentado - e' ele que "
        "produzia as sobreposicoes que a CR-N1 corrigiu")
    assert fronteira == pytest.approx((t_a + t_b) / 2.0)


def test_node_index_of_usa_identidade_de_objeto():
    """`_node_index_of` nunca pode devolver o indice de um no' GEMEO (dois
    dicts iguais campo a campo) - a planta real tem cantos simetricos."""
    gemeo = {"kind": "L_CORNER", "point": None, "arms": []}
    outro = {"kind": "L_CORNER", "point": None, "arms": []}
    nodes = [gemeo, outro]
    assert gemeo == outro
    assert m._node_index_of(nodes, outro) == 1
    assert m._node_index_of(nodes, {"kind": "L_CORNER"}) is None
