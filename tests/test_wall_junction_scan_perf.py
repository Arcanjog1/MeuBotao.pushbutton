# -*- coding: utf-8 -*-
"""CR-N1f - a varredura de nos por parede: mesma resposta, 28% mais rapida.

`_wall_junction_indices_nodes_and_ts_ft` respondia por **41% do tempo do
solver** depois que a CR-N1 a pos no caminho quente (ela roda a cada
`_room_at_t_on_wall`). Medido com cProfile no TGD (2026-09-09): 184s de
tottime em 631s, com 334 224 chamadas e 205 milhoes de `set.add`.

Tres mudancas, TODAS de custo - nenhuma muda um valor sequer:
  1. o eixo da parede e' calculado UMA VEZ por chamada, nao 1x por no';
  2. a pertinencia usa short-circuit (`_node_touches_wall`) em vez de
     montar um `set` por no' so' para fazer um `in`;
  3. cache por IDENTIDADE (`is`) da lista de nos e da de paredes.

O cache e' seguro porque NENHUM campo lido pela varredura (`kind`,
`arms`, `main_wall_idx`, `incoming_wall_idx`, `neighbor_wall_idx`,
`crossing_walls`, `point`) e' escrito em `wall_stepper.py`: todos vem de
`wall_pairing.py`, na construcao do grafo, antes do solver rodar.

    python3 -m pytest tests/test_wall_junction_scan_perf.py -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import load_script  # noqa: E402
import revit_stubs  # noqa: F401,E402

from test_block_bonding import ft, seg  # noqa: E402

m = load_script.load()


def _grafo():
    """Planta com L, T e X - exercita todos os papeis que
    `_node_touches_wall` tem de reconhecer."""
    lines = [
        seg(0.0, 0.0, 800.0, 0.0),        # 0: principal
        seg(0.0, 0.0, 0.0, 300.0),        # 1: L na ponta
        seg(300.0, 0.0, 300.0, 300.0),    # 2: T no meio
        seg(500.0, -200.0, 500.0, 300.0),  # 3: X (atravessa)
    ]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(
        walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    return walls, nodes, end_to_node


def test_cache_devolve_exatamente_a_mesma_varredura():
    """Primeira chamada (cache frio) e segunda (cache quente) tem de dar o
    MESMO resultado - indices, nos e `t`."""
    walls, nodes, _e2n = _grafo()
    m._WALL_JUNCTION_SCAN_CACHE.clear()
    frio = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    quente = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    assert frio == quente
    assert [i for i, _n, _t in frio] == [i for i, _n, _t in quente]
    direto = m._scan_wall_junction_nodes(walls, nodes, 0)
    assert frio == direto, "o cache divergiu da varredura direta"


def test_o_cache_nunca_e_usado_para_OUTRA_lista_de_nos():
    """A guarda e' por IDENTIDADE: uma lista diferente (mesmo que igual
    campo a campo) nao pode reaproveitar a entrada."""
    walls, nodes, _e2n = _grafo()
    m._WALL_JUNCTION_SCAN_CACHE.clear()
    original = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    outros = [dict(n) if isinstance(n, dict) else n for n in nodes]
    # some com um no' na copia: se o cache fosse reusado, o resultado seria
    # igual ao da lista original.
    for node in outros:
        if isinstance(node, dict) and node.get("kind") not in (None, "FREE_END"):
            node["kind"] = "FREE_END"
            break
    copia = m._wall_junction_indices_nodes_and_ts_ft(walls, outros, 0)
    assert len(copia) < len(original), (
        "o cache foi reusado para outra lista de nos: %d x %d"
        % (len(copia), len(original)))


def test_exclude_node_index_filtra_sem_corromper_o_cache():
    """`exclude_node_index` e' aplicado DEPOIS do cache - pedir com
    exclusao nao pode empobrecer a entrada guardada."""
    walls, nodes, _e2n = _grafo()
    m._WALL_JUNCTION_SCAN_CACHE.clear()
    todos = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    assert todos, "esperava nos na parede principal"
    alvo = todos[0][0]
    sem_alvo = m._wall_junction_indices_nodes_and_ts_ft(
        walls, nodes, 0, exclude_node_index=alvo)
    assert alvo not in [i for i, _n, _t in sem_alvo]
    assert len(sem_alvo) == len(todos) - 1
    de_novo = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    assert de_novo == todos, "a exclusao corrompeu a entrada do cache"


def test_a_lista_devolvida_nao_e_o_objeto_do_cache():
    """Quem recebe pode mutar a propria lista sem envenenar o cache."""
    walls, nodes, _e2n = _grafo()
    m._WALL_JUNCTION_SCAN_CACHE.clear()
    primeira = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    primeira.append(("lixo", None, 0.0))
    segunda = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    assert ("lixo", None, 0.0) not in segunda


@pytest.mark.parametrize("campo,valor", [
    ("main_wall_idx", 7),
    ("incoming_wall_idx", 7),
    ("neighbor_wall_idx", 7),
])
def test_node_touches_wall_reconhece_todos_os_papeis(campo, valor):
    assert m._node_touches_wall({campo: valor}, 7) is True
    assert m._node_touches_wall({campo: valor}, 8) is False


def test_node_touches_wall_arms_e_crossing():
    assert m._node_touches_wall({"arms": [(3, 0), (7, 1)]}, 7) is True
    assert m._node_touches_wall({"arms": [(3, 0)]}, 7) is False
    assert m._node_touches_wall({"crossing_walls": (2, 7)}, 7) is True
    assert m._node_touches_wall({"crossing_walls": (2, 4)}, 7) is False
    assert m._node_touches_wall({}, 7) is False


def test_wall_junction_ts_ft_continua_com_o_mesmo_contrato():
    """A funcao publica antiga (`(no', t)`) segue devolvendo o mesmo, agora
    delegando a varredura com indice."""
    walls, nodes, _e2n = _grafo()
    com_indice = m._wall_junction_indices_nodes_and_ts_ft(walls, nodes, 0)
    sem_indice = m._wall_junction_nodes_and_ts_ft(walls, nodes, 0)
    assert [(n, t) for _i, n, t in com_indice] == sem_indice
    assert m._wall_junction_ts_ft(walls, nodes, 0) == [t for _i, _n, t in com_indice]
