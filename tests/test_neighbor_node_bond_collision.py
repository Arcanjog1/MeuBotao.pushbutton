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
