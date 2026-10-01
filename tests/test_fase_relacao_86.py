# -*- coding: utf-8 -*-
"""SECAO 86.2 - FASE DOS ENCONTROS: RELACAO POR TRECHO (R4) + CONVENCAO DE
FACHADA (R2). Pedido do usuario (2026-10-01): aproximar o projeto HUMANO
BUTANTA R08_LT ajustando as regras e o calculo, sem copia-lo.

PRINCIPIO (aritmetica de junta, nenhum id): entre dois nos CONSECUTIVOS de uma
parede, a parede ocupa os dois na MESMA fiada ou ALTERNA; a relacao decide o
comprimento dos dois trechos livres (fiada A e fiada B) e, com o catalogo
padrao (B39=40, B34=35, B19=20, C09=10, C04=5 com a junta), o resto modulo 40
decide quantos blocos de ajuste eles pedem. Humano: trecho cego segue
"D mod 40 <= 15 -> mesma fiada; >= 20 -> alterna" em 26/26; parede entre dois
cantos L na MESMA fiada em 9/9 (CONFLITO com a alternancia forcada da 30.5); na
fiada 0 a parede paralela ao lado maior ocupa os cantos do contorno externo
(8/8).

FIXTURES: paredes retas entre dois T, retangulos fechados de 4 cantos L, planta
em L - tudo na grade do bloco.

    python3 -m pytest tests/test_fase_relacao_86.py -q
"""
import contextlib
import inspect
import itertools
import os
import random
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_block_node_fill_revalidation as NF  # noqa: E402

m = NF.m
ws = sys.modules["core.engine.wall_stepper"]
seg, ft = NF.seg, NF.ft
CATALOG = NF.CATALOG
XYZ = m.XYZ

_FLAGS = ("TIE_PARITY_FILL_BALANCE", "PHASE_RELATION_COMPONENTS", "TIE_PARITY_FILL_NODE_KINDS",
          "TIE_PARITY_FILL_ALL_OPENINGS", "TIE_PARITY_STRUCTURAL_VETO", "PHASE_RELATION_FACADE_CONVENTION",
          "PHASE_RELATION_FACADE_CORNER_WEIGHT")


@contextlib.contextmanager
def secao86(ligada=True, todas_aberturas=None, fachada=True, peso_canto=None):
    """As chaves como o caminho geral (wall_modeling) as liga."""
    salvo = dict((k, getattr(ws, k)) for k in _FLAGS)
    ws.TIE_PARITY_FILL_BALANCE = True
    ws.PHASE_RELATION_COMPONENTS = ligada
    ws.TIE_PARITY_FILL_NODE_KINDS = ("T_INTERSECTION", "L_CORNER") if ligada else ("T_INTERSECTION",)
    ws.TIE_PARITY_FILL_ALL_OPENINGS = todas_aberturas
    ws.TIE_PARITY_STRUCTURAL_VETO = True
    ws.PHASE_RELATION_FACADE_CONVENTION = fachada
    if peso_canto is not None:
        ws.PHASE_RELATION_FACADE_CORNER_WEIGHT = peso_canto
    try:
        yield
    finally:
        for k, v in salvo.items():
            setattr(ws, k, v)


def grafo(lines):
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    return walls, nodes, e2n


def resolve_nos(lines, openings=None, **chaves):
    walls, nodes, e2n = grafo(lines)
    per_wall = openings if openings is not None else dict((i, []) for i in range(len(walls)))
    with secao86(**chaves):
        out = m.solve_all_intersections(nodes, walls, CATALOG, per_wall, e2n)
    return walls, nodes, e2n, out


def no_em(nodes, x_cm, y_cm):
    melhor = None
    for i, n in enumerate(nodes):
        if n.get("kind") not in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
            continue
        p = n["point"]
        d = ((ws._ft_to_cm(p.X) - x_cm) ** 2 + (ws._ft_to_cm(p.Y) - y_cm) ** 2) ** 0.5
        if melhor is None or d < melhor[0]:
            melhor = (d, i)
    assert melhor is not None and melhor[0] < 10.0, (x_cm, y_cm)
    return melhor[1]


def passa_na_fiada_a(walls, nodes, out, node_index, wall_idx):
    pecas = [c for c in out["candidates"] if c.get("node_index") == node_index]
    t = ws._phase_t_cm(walls, wall_idx, nodes[node_index]["point"])
    return ws._phase_passes_course_a(pecas, wall_idx, walls, t)


def assinatura(walls, nodes, out, translate=(0.0, 0.0)):
    """{(x, y) do no': paredes (pelo ponto medio do eixo) que ocupam o no' na fiada A}."""
    sig = {}
    for i, n in enumerate(nodes):
        if n.get("kind") not in ("L_CORNER", "T_INTERSECTION"):
            continue
        p = n["point"]
        chave = (round(ws._ft_to_cm(p.X) - translate[0]), round(ws._ft_to_cm(p.Y) - translate[1]))
        paredes = []
        for w in sorted(ws._phase_node_walls(n)):
            if passa_na_fiada_a(walls, nodes, out, i, w):
                p0, p1, _d, _l, _t = ws._wall_axis_and_length(walls, w)
                paredes.append((round(ws._ft_to_cm((p0.X + p1.X) / 2.0) - translate[0]),
                                round(ws._ft_to_cm((p0.Y + p1.Y) / 2.0) - translate[1])))
        sig[chave] = tuple(sorted(paredes))
    return sig


def parede_entre_dois_T(comprimento_cm, braco_cm=150.0):
    return [seg(0, 0, comprimento_cm, 0),
            seg(0, -braco_cm, 0, braco_cm),
            seg(comprimento_cm, -braco_cm, comprimento_cm, braco_cm)]


def retangulo(largura, altura, dx=0.0, dy=0.0):
    return [seg(dx, dy, dx + largura, dy), seg(dx + largura, dy, dx + largura, dy + altura),
            seg(dx + largura, dy + altura, dx, dy + altura), seg(dx, dy + altura, dx, dy)]


def sala_com_internas(dx=0.0, dy=0.0):
    """Retangulo 800 x 302 com duas paredes internas verticais (4 T + 4 L)."""
    return retangulo(800.0, 302.0, dx, dy) + [seg(dx + 240.0, dy, dx + 240.0, dy + 302.0),
                                              seg(dx + 580.0, dy, dx + 580.0, dy + 302.0)]


# ----------------------------------------------------------------- chaves
def test_chaves_da_secao_86():
    assert m.GENERAL_PHASE_RELATION_ENABLED is True
    # o modulo fica desligado; o caminho geral (wall_modeling) liga durante o solve
    assert ws.PHASE_RELATION_COMPONENTS is False
    assert (ws.PHASE_RELATION_WEIGHT_BLIND, ws.PHASE_RELATION_WEIGHT_DOOR, ws.PHASE_RELATION_WEIGHT_WINDOW) == (4, 0, 1)
    assert ws.PHASE_RELATION_FACADE_CONVENTION is True
    assert ws.PHASE_RELATION_OPENING_REACH_GUARD is False
    # a preferencia do canto fica entre a de um trecho com janela (8 B34 x 2 estados
    # x peso 1) e a menor de um trecho cego (8 B34 x 2 x peso 4)
    assert 2 * 8 * ws.PHASE_RELATION_WEIGHT_WINDOW < ws.PHASE_RELATION_FACADE_CORNER_WEIGHT \
        < 2 * 8 * ws.PHASE_RELATION_WEIGHT_BLIND


# ----------------------------------------------------------------- fecho exato do trecho
def test_fecho_exato_do_trecho_e_funcao_pura():
    f = ws._phase_segment_composition
    assert f(159.0, CATALOG) == (0, 0, 4)          # 4 B39 exatos
    assert f(174.0, CATALOG) == (0, 5, 5)          # resto 15 -> 5 B34
    assert f(164.0, CATALOG) == (1, 0, 5)          # resto 5 -> uma pastilha e nada de B34
    assert f(-1.0, CATALOG) == (0, 0, 0)           # pecas encostadas: nada a preencher
    assert f(-10.0, CATALOG) is None               # trecho negativo nao fecha
    assert f(174.0, CATALOG) == f(174.0, CATALOG)


# ----------------------------------------------------------------- R4: tabela mod 40 (oraculo do humano)
@pytest.mark.parametrize("d_cm", [140, 165, 195, 210, 250, 285, 345, 400, 405, 430, 480])
def test_relacao_entre_dois_T_segue_o_modulo_40(d_cm):
    """Parede cega entre dois T: a relacao escolhida e' a de menor custo, que e'
    a tabela medida no humano (26/26 trechos cegos)."""
    walls, nodes, _e2n, out = resolve_nos(parede_entre_dois_T(float(d_cm)))
    a, b = no_em(nodes, 0.0, 0.0), no_em(nodes, float(d_cm), 0.0)
    mesma = passa_na_fiada_a(walls, nodes, out, a, 0) == passa_na_fiada_a(walls, nodes, out, b, 0)
    assert mesma == (d_cm % 40 <= 15), (d_cm, mesma)
    assert out["phase_relation"]["applied"] and out["phase_relation"]["exact"]


# ----------------------------------------------------------------- R4: parede entre dois L (CONFLITO 30.5)
def _cantos(largura, altura):
    return [(0.0, 0.0), (largura, 0.0), (largura, altura), (0.0, altura)]


def _paredes_do_retangulo_por_canto(walls, nodes, largura, altura):
    """{parede: (no' da ponta 1, no' da ponta 2)} do retangulo."""
    cantos = [no_em(nodes, x, y) for x, y in _cantos(largura, altura)]
    return {0: (cantos[0], cantos[1]), 1: (cantos[1], cantos[2]), 2: (cantos[2], cantos[3]),
            3: (cantos[3], cantos[0])}


def test_retangulo_classico_cada_parede_nos_dois_cantos_na_mesma_fiada():
    """480 x 250: as duas distancias pedem "mesma fiada" (resto 0 e 10). O humano
    faz o retangulo classico; a 30.5 (alternancia forcada) fazia o catavento."""
    largura, altura = 480.0, 250.0
    walls, nodes, _e2n, out = resolve_nos(retangulo(largura, altura))
    for w, (p, q) in _paredes_do_retangulo_por_canto(walls, nodes, largura, altura).items():
        assert passa_na_fiada_a(walls, nodes, out, p, w) == passa_na_fiada_a(walls, nodes, out, q, w), w
    # a decisao fica PINADA: a coordenacao da 30.5 nao a refaz nas bandas seguintes
    assert all(n.get("_arm_role_pinned") for n in nodes if n.get("kind") == "L_CORNER")
    antes = [list(n.get("arms") or []) for n in nodes]
    assert ws._coordinate_arm_role_nodes(nodes) == []
    assert [list(n.get("arms") or []) for n in nodes] == antes


def test_parede_curta_entre_dois_L_segue_o_custo_exato_e_nao_a_tabela():
    """U de 101 cm: a tabela mod 40 (resto 21) diria "alterna", mas o fecho exato
    manda a MESMA fiada (2 especiais contra 4) - a regra e' o custo, a tabela so'
    descreve os trechos longos (o humano faz o mesmo nas paredes de 101 do shaft)."""
    lines = [seg(0, 0, 101.0, 0), seg(0, 0, 0, -242.0), seg(101.0, 0, 101.0, -242.0)]
    walls, nodes, _e2n, out = resolve_nos(lines)
    a, b = no_em(nodes, 0.0, 0.0), no_em(nodes, 101.0, 0.0)
    assert passa_na_fiada_a(walls, nodes, out, a, 0) == passa_na_fiada_a(walls, nodes, out, b, 0)
    w0, nodes0, _e0, out0 = resolve_nos(lines, ligada=False)
    a0, b0 = no_em(nodes0, 0.0, 0.0), no_em(nodes0, 101.0, 0.0)
    assert passa_na_fiada_a(w0, nodes0, out0, a0, 0) != passa_na_fiada_a(w0, nodes0, out0, b0, 0)


def test_sem_a_86_a_30_5_alterna_as_paredes_entre_dois_L():
    """Registro do CONFLITO: com a chave desligada a parede entre dois L alterna."""
    largura, altura = 480.0, 250.0
    walls, nodes, _e2n, out = resolve_nos(retangulo(largura, altura), ligada=False)
    for w, (p, q) in _paredes_do_retangulo_por_canto(walls, nodes, largura, altura).items():
        assert passa_na_fiada_a(walls, nodes, out, p, w) != passa_na_fiada_a(walls, nodes, out, q, w), w


# ----------------------------------------------------------------- R2: convencao de fachada
@pytest.mark.parametrize("largura,altura", [(480.0, 250.0), (250.0, 480.0)])
def test_na_fiada_a_a_parede_paralela_ao_lado_maior_ocupa_os_cantos(largura, altura):
    walls, nodes, _e2n, out = resolve_nos(retangulo(largura, altura))
    paralelas = (0, 2) if largura > altura else (1, 3)
    for x, y in _cantos(largura, altura):
        no = no_em(nodes, x, y)
        donas = [w for w in ws._phase_node_walls(nodes[no]) if passa_na_fiada_a(walls, nodes, out, no, w)]
        assert len(donas) == 1 and donas[0] in paralelas, (x, y, donas)


def test_espelho_pela_convencao_nao_muda_o_custo_de_preenchimento():
    """Sem a preferencia por canto, a convencao so' ESPELHA componentes: o custo
    dos trechos e' o mesmo com e sem a convencao."""
    walls, nodes, e2n = grafo(sala_com_internas())
    per_wall = dict((i, []) for i in range(len(walls)))
    bond = [i for i, n in enumerate(nodes) if ws._phase_is_bond_node(n)]
    with secao86():
        base = m.solve_all_intersections(nodes, walls, CATALOG, per_wall, e2n, _parity_pass=False)
        assert base["candidates"]
        problem = ws._phase_relation_problem(nodes, walls, CATALOG, per_wall, e2n, bond, bond)

    def custo(bits):
        return sum(e["table"][(bits.get(e["i"], 0), bits.get(e["j"], 0))] * e["weight"] for e in problem["edges"])
    custos = []
    for fachada in (False, True):
        with secao86(fachada=fachada, peso_canto=0):
            bits, _total, exato, _rel = ws._phase_solve(problem, nodes, walls, bond)
        assert exato
        custos.append(custo(bits))
    assert custos[0] == custos[1]


# ----------------------------------------------------------------- peso do trecho
def test_porta_libera_a_fase_e_janela_pesa_um_quarto():
    porta = (ft(100.0), ft(190.0), ft(0.0), ft(210.0))
    janela = (ft(250.0), ft(370.0), ft(100.0), ft(220.0))
    todas = [[porta, janela]]
    banda = [[porta]]          # na primeira fiada so' a porta esta' ativa
    assert ws._phase_edge_weight(0, 0.0, 200.0, todas, banda) == (ws.PHASE_RELATION_WEIGHT_DOOR, "door")
    assert ws._phase_edge_weight(0, 200.0, 400.0, todas, banda) == (ws.PHASE_RELATION_WEIGHT_WINDOW, "window")
    assert ws._phase_edge_weight(0, 400.0, 600.0, todas, banda) == (ws.PHASE_RELATION_WEIGHT_BLIND, "blind")
    assert ws.PHASE_RELATION_WEIGHT_DOOR == 0


def test_trecho_com_porta_nao_liga_os_dois_nos():
    """Parede de 405 (cega pediria "mesma fiada") com uma porta no meio: sem
    preferencia, os dois T ficam em componentes separados."""
    lines = parede_entre_dois_T(405.0)
    porta = (ft(150.0), ft(240.0), ft(0.0), ft(210.0))
    ops = [[porta], [], []]
    walls, nodes, _e2n, out = resolve_nos(lines, openings=ops, todas_aberturas=ops)
    componentes = out["phase_relation"]["components"]
    assert len(componentes) == 2 and all(len(c["nodes"]) == 1 for c in componentes)


# ----------------------------------------------------------------- busca exata
def _forca_bruta(order, edges, unary):
    melhor = None
    for bits in itertools.product((0, 1), repeat=len(order)):
        b = dict(zip(order, bits))
        c = sum(u[b[v]] for v, u in unary.items())
        c += sum(ce if b[i] == b[j] else cd for i, j, ce, cd in edges)
        if melhor is None or c < melhor:
            melhor = c
    return melhor


def test_busca_exata_bate_com_a_forca_bruta():
    rnd = random.Random(86)
    for _caso in range(60):
        n = rnd.randint(2, 9)
        order = list(range(n))
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                if rnd.random() < 0.45:
                    edges.append((i, j, rnd.randint(0, 40), rnd.randint(0, 40)))
        unary = {}
        if rnd.random() < 0.5:
            for v in rnd.sample(order, rnd.randint(1, n)):
                unary[v] = (rnd.randint(0, 30), rnd.randint(0, 30))
        sol, custo, exato = ws._phase_exact_component(order, edges, unary, 10 ** 6)
        assert exato
        assert custo == _forca_bruta(order, edges, unary)
        refeito = sum(unary.get(v, (0, 0))[sol[v]] for v in order) + \
            sum(ce if sol[i] == sol[j] else cd for i, j, ce, cd in edges)
        assert refeito == custo
        if not unary:
            assert sol[order[0]] == 0          # simetrico: o espelho fica para a convencao


def test_busca_exata_com_orcamento_estourado_devolve_a_melhor_achada():
    order = list(range(8))
    edges = [(i, (i + 1) % 8, 0, 5) for i in range(8)] + [(0, 4, 7, 0), (2, 6, 7, 0)]
    _sol, custo, exato = ws._phase_exact_component(order, edges, {}, 1)
    assert exato is False and custo >= _forca_bruta(order, edges, {})


# ----------------------------------------------------------------- contorno externo
def test_contorno_externo_de_planta_em_L_tem_seis_cantos():
    """T no meio de uma fachada (parede interna chegando) nao e' canto: o contorno
    segue reto por ali."""
    lines = [seg(0, 0, 800, 0), seg(800, 0, 800, 400), seg(800, 400, 400, 400),
             seg(400, 400, 400, 800), seg(400, 800, 0, 800), seg(0, 800, 0, 0),
             seg(200, 0, 200, 800)]
    walls, nodes, _e2n = grafo(lines)
    bond = [i for i, n in enumerate(nodes) if ws._phase_is_bond_node(n)]
    cantos = ws._phase_outer_contour_corners(nodes, ws._phase_wall_sequences(nodes, walls, bond))
    esperados = set(no_em(nodes, x, y) for x, y in ((0, 0), (800, 0), (800, 400), (400, 400), (400, 800), (0, 800)))
    assert set(cantos) == esperados
    assert no_em(nodes, 200, 0) not in cantos and no_em(nodes, 200, 800) not in cantos


# ----------------------------------------------------------------- invariancia e determinismo
def test_decisao_nao_depende_da_ordem_das_paredes_nem_de_translacao():
    base = sala_com_internas()
    walls, nodes, _e2n, out = resolve_nos(base)
    ref = assinatura(walls, nodes, out)
    assert ref
    variantes = [
        (list(reversed(base)), (0.0, 0.0)),
        ([m.Line.CreateBound(l.GetEndPoint(1), l.GetEndPoint(0)) for l in base], (0.0, 0.0)),
        (sala_com_internas(1234.5, -987.25), (1234.5, -987.25)),
    ]
    for lines, tr in variantes:
        w2, n2, _e, o2 = resolve_nos(lines)
        assert assinatura(w2, n2, o2, tr) == ref


def test_determinismo_e_decisao_unica_por_planta():
    walls, nodes, e2n, out = resolve_nos(sala_com_internas())
    w2, n2, _e2, o2 = resolve_nos(sala_com_internas())
    assert assinatura(walls, nodes, out) == assinatura(w2, n2, o2)
    assert out["tie_parity_fill_flips"] == o2["tie_parity_fill_flips"]
    # segunda chamada sobre os MESMOS nos (outra banda/rebuild): a decisao e' lida do no'
    assert all(n.get("_phase_relation_done") for n in nodes)
    with secao86():
        de_novo = m.solve_all_intersections(nodes, walls, CATALOG, dict((i, []) for i in range(len(walls))), e2n)
    assert assinatura(walls, nodes, de_novo) == assinatura(walls, nodes, out)
    assert sorted(de_novo.get("tie_parity_fill_flips") or []) == sorted(out["tie_parity_fill_flips"])
    assert all(nodes[i].get("_tie_parity_fill_chosen") for i in out["tie_parity_fill_flips"])


# ----------------------------------------------------------------- veto estrutural
def _peca(x_cm, curso, no):
    return {"logical_code": "B34", "course": curso, "origin_world": XYZ(ft(x_cm), 0.0, 0.0),
            "x_dir": XYZ(1.0, 0.0, 0.0), "y_dir": XYZ(0.0, 1.0, 0.0), "length_cm": 34.0, "width_cm": 14.0,
            "node_index": no}


def test_estado_estrutural_ve_pecas_de_nos_diferentes_interpenetradas():
    sobrepostas = {"failures": [(3, "x")], "candidates": [_peca(0.0, "A", 1), _peca(20.0, "A", 2)]}
    falhas, pares = ws._phase_structural_state(sobrepostas)
    assert falhas == {3} and pares == {(1, 2)}
    _f, pares = ws._phase_structural_state({"candidates": [_peca(0.0, "A", 1), _peca(20.0, "B", 2)]})
    assert pares == set()                       # fiadas diferentes nunca colidem
    _f, pares = ws._phase_structural_state({"candidates": [_peca(0.0, "A", 1), _peca(35.0, "A", 2)]})
    assert pares == set()                       # encostadas com junta


# ----------------------------------------------------------------- 82.1 tambem julga o canto L trocado
def test_canto_L_trocado_fica_marcado_para_a_82_1():
    walls, nodes, _e2n, out = resolve_nos(retangulo(250.0, 480.0))
    trocados = out["phase_relation"]["swapped_corners"]
    assert out["phase_relation_swapped_corners"] == trocados
    for i in trocados:
        assert nodes[i]["_tie_parity_fill_chosen"] and nodes[i]["_phase_relation_original"]["arms"] != nodes[i]["arms"]
    # tie_parity_fill_flips continua sendo so' T/X invertidos
    assert all(nodes[i].get("kind") != "L_CORNER" for i in out["tie_parity_fill_flips"])


def test_prisma_82_1_devolve_o_canto_L_trocado_ao_estado_original(monkeypatch):
    original = {"arms": [(0, 1), (1, 0)], "neighbor_wall_idx": 1, "neighbor_end_index": 0}
    nodes = [{"kind": "L_CORNER", "arms": [(1, 0), (0, 1)], "neighbor_wall_idx": 0, "neighbor_end_index": 1,
              "_arm_role_pinned": True, "_phase_relation_swapped": True, "_tie_parity_fill_chosen": True,
              "_phase_relation_original": original}]
    chamadas = {"viol": 0, "core": 0}

    def viol(result, nodes_, *a):
        chamadas["viol"] += 1
        return [{"node_index": 0, "wall_idx": 0, "t_cm": 10.0, "from_course": 0, "courses": 3}] \
            if chamadas["viol"] == 1 else []

    def core(*a, **k):
        chamadas["core"] += 1
        return {"error": None, "novo": True}

    monkeypatch.setattr(m, "_tie_parity_prism_violations", viol)
    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_impl_core", core)
    out = m._tie_parity_prism_rounds({"error": None}, nodes, [], {}, [], {}, 0.0, 4, {})
    assert out.get("novo") and chamadas["core"] == 1
    assert nodes[0]["arms"] == original["arms"] and nodes[0]["neighbor_wall_idx"] == 1
    assert "_phase_relation_swapped" not in nodes[0] and "_tie_parity_fill_chosen" not in nodes[0]
    assert nodes[0]["_arm_role_pinned"] is True          # a 30.5 das bandas seguintes nao o refaz
    assert out["tie_parity_prism_check"]["reverted"] == [0]
    assert ws._phase_revert_swapped_corner(nodes[0]) is False


# ----------------------------------------------------------------- integracao com o caminho geral
def test_o_caminho_geral_liga_a_86_e_restaura_as_chaves():
    import test_channel_reinforcement as tcr
    lines = retangulo(480.0, 250.0)
    ops = [[] for _ in lines]
    _res, _walls, nodes, _o = tcr.solve(lines, ops, strategy=None, num_courses=2)
    assert all(n.get("_phase_relation_done") for n in nodes if n.get("kind") == "L_CORNER")
    assert ws.PHASE_RELATION_COMPONENTS is False
    assert ws.TIE_PARITY_FILL_NODE_KINDS == ("T_INTERSECTION", "X_INTERSECTION")
    antes = m.GENERAL_PHASE_RELATION_ENABLED
    m.GENERAL_PHASE_RELATION_ENABLED = False
    try:
        _res, _walls, nodes_off, _o = tcr.solve(lines, ops, strategy=None, num_courses=2)
    finally:
        m.GENERAL_PHASE_RELATION_ENABLED = antes
    assert not any(n.get("_phase_relation_done") for n in nodes_off)
    # CHANNEL: a 86.2 nao entra (custo calibrado da 72)
    _res, _walls, nodes_ch, _o = tcr.solve(lines, ops, strategy=tcr.CHANNEL, num_courses=2)
    assert not any(n.get("_phase_relation_done") for n in nodes_ch)


def test_no_caminho_geral_a_86_substitui_a_busca_gulosa(monkeypatch):
    import test_channel_reinforcement as tcr
    chamadas = {"gulosa": 0, "fase": 0}
    gulosa, fase = ws._search_tie_parity_fill_balance, ws._search_phase_relation_components

    def espia_gulosa(*a, **k):
        chamadas["gulosa"] += 1
        return gulosa(*a, **k)

    def espia_fase(*a, **k):
        chamadas["fase"] += 1
        assert ws.TIE_PARITY_FILL_NODE_KINDS == ("T_INTERSECTION", "L_CORNER")
        return fase(*a, **k)

    monkeypatch.setattr(ws, "_search_tie_parity_fill_balance", espia_gulosa)
    monkeypatch.setattr(ws, "_search_phase_relation_components", espia_fase)
    lines = sala_com_internas()
    tcr.solve(lines, [[] for _ in lines], strategy=None, num_courses=2)
    assert chamadas["fase"] >= 1 and chamadas["gulosa"] == 0


# ----------------------------------------------------------------- nenhum id
@pytest.mark.parametrize("funcao", [
    ws._search_phase_relation_components, ws._phase_solve, ws._phase_relation_problem,
    ws._phase_exact_component, ws._phase_outer_contour_corners, ws._phase_edge_weight,
    ws._phase_edge_state_cost, ws._phase_node_border_cm, ws._phase_segment_composition,
    ws._phase_canonical_l_first, ws._phase_passes_course_a, ws._phase_structural_state])
def test_sem_hardcode(funcao):
    """Nenhum id de elemento, de no', de parede ou nome de projeto no codigo da regra."""
    corpo = re.sub(r'"""[\s\S]*?"""', "", inspect.getsource(funcao))
    corpo = "\n".join(linha.split("#", 1)[0] for linha in corpo.splitlines())
    assert not re.search(r"\b\d{5,}\b", corpo), funcao.__name__
    for projeto in (r"BUTANT", r"TGD", r"TP1", r"PR49", r"HUMANO", r"MCP"):
        assert not re.search(projeto, corpo, re.IGNORECASE), (funcao.__name__, projeto)
    for identidade in ("node_index ==", "wall_idx ==", "element_id"):
        assert identidade not in corpo, (funcao.__name__, identidade)
