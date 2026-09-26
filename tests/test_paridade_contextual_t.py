# -*- coding: utf-8 -*-
"""SECAO 82 (D11) - PARIDADE CONTEXTUAL DOS ENCONTROS T.

A paridade de um T/X (em qual fiada a parede que chega passa pelo eixo do no')
deixa de ser a convencao fixa por papel e passa a ser escolhida pelo que ela
deixa para preencher, em QUALQUER estrategia (a busca da secao 72, antes so' no
CHANNEL). No caminho geral (sem reforco adicional):

  1. estrutura antes de qualidade - uma inversao que cria falha de no', conflito
     de papel ou pecas de no' se interpenetrando e' recusada ANTES do custo;
  2. o custo modela o DESENCONTRO de junta entre as fiadas (a Fiada B desencontra
     a A, a A desencontra as bordas de no' da B - como o preenchimento real);
  3. as aberturas ativas na banda so' VETAM (o custo continuo decide);
  4. SECAO 82.1 - o preenchimento REAL tem a ultima palavra: T invertido que
     deixa junta a prumo (3+ fiadas) na sua regiao volta para a convencao.

FIXTURES: salas retangulares fechadas com paredes internas entre dois T, na
grade do bloco (nenhum id, nenhum offset de projeto real).

    python3 -m pytest tests/test_paridade_contextual_t.py -q
"""
import inspect
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
ws = sys.modules["core.engine.wall_stepper"]
COMPENSADORES = ("C04", "C09")
N_FIADAS = 14


def sala(largura, altura, internas, aberturas=()):
    """Retangulo largura x altura (eixos) com paredes internas verticais em x
    ligando o lado de cima ao de baixo (cada uma entre DOIS T).
    `aberturas`: (parede, inicio_cm, largura_cm, porta)."""
    lines = [seg(0, 0, largura, 0), seg(0, -altura, largura, -altura),
             seg(0, 0, 0, -altura), seg(largura, 0, largura, -altura)]
    for x in internas:
        lines.append(seg(x, 0, x, -altura))
    ops = [[] for _ in lines]
    for parede, inicio, larg, porta in aberturas:
        z0, z1 = (0.0, 221.0) if porta else (100.0, 221.0)
        ops[parede].append((ft(inicio), ft(inicio + larg), ft(z0), ft(z1)))
    return lines, [sorted(o) for o in ops]


# Sala em que a convencao deixa as duas fiadas das paredes longas com sobra que
# so' fecha com compensador; invertendo UM T as sobras passam a fechar com bloco.
SALA_COM_GANHO = dict(largura=800.0, altura=302.0, internas=(240.0, 580.0))
# Sala em que a convencao ja' e' a melhor paridade (nenhuma inversao ajuda).
SALA_SEM_GANHO = dict(largura=600.0, altura=242.0, internas=(300.0,))


def resolve(fixture, geral=True, strategy=None, reverse=False, aberturas=()):
    antes = m.GENERAL_TIE_PARITY_ENABLED
    m.GENERAL_TIE_PARITY_ENABLED = geral
    try:
        lines, ops = sala(aberturas=aberturas, **fixture)
        return tcr.solve(lines, ops, strategy=strategy, reverse=reverse, num_courses=N_FIADAS)
    finally:
        m.GENERAL_TIE_PARITY_ENABLED = antes


def conta(res, codigos):
    return sum(1 for pecas in res["course_candidates"].values() for p in pecas if p["logical_code"] in codigos)


def juntas_a_prumo(res, walls, minimo=3):
    """(parede, posicao) de toda junta vertical repetida em `minimo` fiadas seguidas."""
    from core.engine import opening_reinforcement as orf
    cc = res["course_candidates"]
    out = set()
    for wi in range(len(walls)):
        por_fiada = {}
        for ci in cc:
            rows = [x for x in orf._wall_strip_pieces(cc[ci], walls, wi) if x["along"]]
            por_fiada[ci] = set(round((a["hi"] + b["lo"]) / 2.0)
                                for a, b in zip(rows, rows[1:]) if 0 <= b["lo"] - a["hi"] < 2.5)
        for j in set().union(*por_fiada.values()) if por_fiada else ():
            seguidas = 0
            for ci in sorted(por_fiada):
                seguidas = seguidas + 1 if j in por_fiada[ci] else 0
                if seguidas >= minimo:
                    out.add((wi, j))
    return out


def invertidos(nodes):
    return sorted(i for i, n in enumerate(nodes) if n.get("_tie_parity_flip"))


@pytest.fixture(scope="module")
def com_ganho():
    conv = resolve(SALA_COM_GANHO, geral=False)
    geral = resolve(SALA_COM_GANHO, geral=True)
    return conv, geral


# ----------------------------------------------------------------- chaves
def test_chaves_da_secao_82():
    assert m.GENERAL_TIE_PARITY_ENABLED is True
    assert m.TIE_PARITY_PRISM_CHECK_ENABLED is True
    assert m.TIE_PARITY_PRISM_MIN_COURSES == 3
    # os refinamentos so' valem durante o caminho geral (ligados pelo wall_modeling)
    assert ws.TIE_PARITY_FILL_STAGGER is False
    assert ws.TIE_PARITY_STRUCTURAL_VETO is False
    assert ws.TIE_PARITY_FILL_OPENING_BOUNDARIES is False
    assert ws.TIE_PARITY_FILL_COST_ORDER == "compensadores"
    assert ws.TIE_PARITY_FILL_NODE_KINDS == ("T_INTERSECTION", "X_INTERSECTION")   # o CHANNEL move T e X


# ----------------------------------------------------------------- o principio no preenchimento real
def test_paridade_contextual_reduz_compensadores_sem_criar_problema(com_ganho):
    (res_c, walls_c, nodes_c, _o), (res_g, walls_g, nodes_g, _o2) = com_ganho
    assert invertidos(nodes_c) == []
    assert invertidos(nodes_g), "a sala tem um T cuja inversao fecha as sobras"
    assert conta(res_g, COMPENSADORES) < conta(res_c, COMPENSADORES)
    # estrutura intacta
    assert len(res_g.get("missing_required_junction_bond") or []) <= len(res_c.get("missing_required_junction_bond") or [])
    assert not res_g.get("unresolved_spans")
    assert not res_g.get("collisions")
    # nenhuma junta a prumo nova
    assert juntas_a_prumo(res_g, walls_g) <= juntas_a_prumo(res_c, walls_c)


def test_sem_ganho_a_convencao_fica(com_ganho):
    _res, _walls, nodes, _o = resolve(SALA_SEM_GANHO, geral=True)
    assert invertidos(nodes) == []


def test_observabilidade(com_ganho):
    _conv, (res, _walls, nodes, _o) = com_ganho
    assert res["tie_parity_fill_flips"] == invertidos(nodes)
    assert all(nodes[i].get("_tie_parity_fill_chosen") for i in res["tie_parity_fill_flips"])
    verificacao = res["tie_parity_prism_check"]
    assert verificacao["remaining"] == []


def test_determinismo(com_ganho):
    _conv, (res, _walls, nodes, _o) = com_ganho
    res2, _walls2, nodes2, _o2 = resolve(SALA_COM_GANHO, geral=True)
    assert invertidos(nodes2) == invertidos(nodes)
    assert sorted((ci, p["logical_code"]) for ci, v in res2["course_candidates"].items() for p in v) == \
        sorted((ci, p["logical_code"]) for ci, v in res["course_candidates"].items() for p in v)


def test_espelhamento(com_ganho):
    """A regra e' geometrica: a planta desenhada ao contrario escolhe a mesma
    quantidade de inversoes e fecha com os mesmos compensadores."""
    _conv, (res, _walls, nodes, _o) = com_ganho
    res_r, _walls_r, nodes_r, _o_r = resolve(SALA_COM_GANHO, geral=True, reverse=True)
    assert len(invertidos(nodes_r)) == len(invertidos(nodes))
    assert conta(res_r, COMPENSADORES) == conta(res, COMPENSADORES)


def test_chave_desligada_reproduz_a_convencao():
    _res, _walls, nodes, _o = resolve(SALA_COM_GANHO, geral=False)
    assert invertidos(nodes) == []


# ----------------------------------------------------------------- CHANNEL e secao 68 intocados
def test_channel_mantem_o_custo_calibrado_da_72(monkeypatch):
    estados = []
    core = m._solve_building_blocks_all_courses_core

    def espia(*a, **k):
        estados.append((ws.TIE_PARITY_FILL_STAGGER, ws.TIE_PARITY_STRUCTURAL_VETO,
                        ws.TIE_PARITY_FILL_OPENING_BOUNDARIES))
        return core(*a, **k)

    prisma = []
    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_core", espia)
    monkeypatch.setattr(m, "_tie_parity_prism_rounds", lambda r, *a, **k: prisma.append(1) or r)
    lines, ops = sala(**SALA_SEM_GANHO)
    tcr.solve(lines, ops, strategy=tcr.CHANNEL, num_courses=4)
    assert estados and not any(any(e) for e in estados), estados
    assert prisma == []


def test_caminho_geral_move_so_encontros_t(monkeypatch):
    """No caminho geral a busca so' inverte T; o X fica na convencao (o CHANNEL
    continua movendo os dois)."""
    tipos = []
    real = ws._search_tie_parity_fill_balance

    def espia(*a, **k):
        tipos.append(ws.TIE_PARITY_FILL_NODE_KINDS)
        return real(*a, **k)

    monkeypatch.setattr(ws, "_search_tie_parity_fill_balance", espia)
    lines, ops = sala(**SALA_SEM_GANHO)
    tcr.solve(lines, ops, strategy=None, num_courses=4)
    assert tipos and all(t == ("T_INTERSECTION",) for t in tipos), tipos
    assert ws.TIE_PARITY_FILL_NODE_KINDS == ("T_INTERSECTION", "X_INTERSECTION")   # restaurado


def test_x_fica_na_convencao_no_caminho_geral():
    """Sala com uma parede interna horizontal cruzando as verticais (dois X):
    nenhum X e' invertido pela paridade geral."""
    antes = m.GENERAL_TIE_PARITY_ENABLED
    m.GENERAL_TIE_PARITY_ENABLED = True
    try:
        lines = [seg(0, 0, 800, 0), seg(0, -302, 800, -302), seg(0, 0, 0, -302), seg(800, 0, 800, -302),
                 seg(240, 0, 240, -302), seg(580, 0, 580, -302), seg(0, -151, 800, -151)]
        res, _walls, nodes, _o = tcr.solve(lines, [[] for _ in lines], strategy=None, num_courses=N_FIADAS)
    finally:
        m.GENERAL_TIE_PARITY_ENABLED = antes
    xs = [i for i, n in enumerate(nodes) if n.get("kind") == "X_INTERSECTION"]
    assert xs, "a fixture tem X"
    assert not any(nodes[i].get("_tie_parity_flip") for i in xs)
    assert not any(nodes[i].get("_tie_parity_fill_chosen") for i in xs)


def test_secao_68_nao_executa_com_a_paridade_geral(monkeypatch):
    estados = []
    core = m._solve_building_blocks_all_courses_core

    def espia(*a, **k):
        estados.append((ws.OPENING_REPAIR_PREFER_CLEAN_ACTIVE, ws.TIE_PARITY_FILL_BALANCE,
                        ws.TIE_PARITY_FILL_STAGGER))
        return core(*a, **k)

    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_core", espia)
    lines, ops = sala(aberturas=((0, 95.0, 91.0, True),), **SALA_SEM_GANHO)
    tcr.solve(lines, ops, strategy=None, num_courses=4)
    assert estados
    assert not any(e[0] for e in estados), "a secao 68 nao roda no NONE"
    assert all(e[1] and e[2] for e in estados), "a paridade geral roda no NONE"


# ----------------------------------------------------------------- custo com desencontro
def test_custo_com_desencontro_e_funcao_pura():
    cat = tcr.sb.CATALOG
    # o mesmo trecho nas duas fiadas: a Fiada B precisa desencontrar a A
    segs_a = ((0.0, 359.0, 0.0, 0.0, False, False),)
    segs_b = ((0.0, 359.0, 0.0, 0.0, False, False),)
    ws._TIE_PARITY_WALL_MEMO.clear()
    um = ws._tie_parity_wall_cost_with_stagger(segs_a, segs_b, cat, True)
    ws._TIE_PARITY_WALL_MEMO.clear()
    dois = ws._tie_parity_wall_cost_with_stagger(segs_a, segs_b, cat, True)
    ws._TIE_PARITY_WALL_MEMO.clear()
    assert um == dois
    fail, excess, coinc, pecas, especiais, b34, comps, nao_inteiro = um
    assert fail == 0 and coinc == 0          # a Fiada B desencontra a A...
    assert comps >= 1                        # ...e o desencontro custa compensador (entra na decisao)
    assert comps <= especiais <= pecas and nao_inteiro <= pecas


def test_ordem_do_custo(monkeypatch):
    """"pecas": (falha, excesso #2, juntas #1, pecas, especiais, B34);
    "compensadores": (falha, excesso #2, juntas #1, compensadores, pecas nao-inteiras,
    pecas, especiais, B34)."""
    lines, _ops = sala(**SALA_SEM_GANHO)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    out = m.solve_all_intersections(nodes, walls, tcr.sb.CATALOG, dict((i, []) for i in range(len(walls))), e2n,
                                    _parity_pass=False)
    monkeypatch.setattr(ws, "_tie_parity_wall_cost_with_stagger", lambda *a, **k: (0, 1, 2, 30, 4, 5, 6, 7))
    todas = set(range(len(walls)))
    n = len(walls)
    monkeypatch.setattr(ws, "TIE_PARITY_FILL_COST_ORDER", "pecas")
    assert ws._tie_parity_fill_stagger_cost(todas, nodes, walls, e2n, out["candidates"], tcr.sb.CATALOG) == \
        (0, n, 2 * n, 30 * n, 4 * n, 5 * n)
    monkeypatch.setattr(ws, "TIE_PARITY_FILL_COST_ORDER", "compensadores")
    assert ws._tie_parity_fill_stagger_cost(todas, nodes, walls, e2n, out["candidates"], tcr.sb.CATALOG) == \
        (0, n, 2 * n, 6 * n, 7 * n, 30 * n, 4 * n, 5 * n)


def test_bloco_inteiro_vem_do_catalogo():
    assert ws._tie_parity_full_block_code(tcr.sb.CATALOG) == max(
        ws.COMMON_FILL_BLOCK_CODES, key=lambda c: (tcr.sb.CATALOG.get(c) or {}).get("length_cm") or 0)


# ----------------------------------------------------------------- veto estrutural
def _nos_da_sala():
    lines, _ops = sala(**SALA_SEM_GANHO)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    return walls, nodes, e2n


def test_veto_estrutural_recusa_falha_e_conflito_novos():
    _walls, nodes, _e2n = _nos_da_sala()
    t = next(i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION")
    limpo = {"failures": [], "role_conflicts": [], "candidates": []}
    assert ws._tie_parity_structural_worse(limpo, limpo, t, nodes) is None
    assert ws._tie_parity_structural_worse({"failures": [(t, "x")], "candidates": []}, limpo, t, nodes) == "NODE_FAILED"
    assert ws._tie_parity_structural_worse({"role_conflicts": [1], "candidates": []}, limpo, t, nodes) == "ROLE_CONFLICT"
    # uma falha que JA existia nao veta
    falha = {"failures": [(t, "x")], "candidates": []}
    assert ws._tie_parity_structural_worse(falha, falha, t, nodes) is None


# ----------------------------------------------------------------- 82.1 guarda de prisma
def test_prisma_devolve_o_t_para_a_convencao_e_re_resolve(monkeypatch):
    nodes = [{"kind": "T_INTERSECTION"}, {"kind": "T_INTERSECTION", "_tie_parity_flip": True,
                                         "_tie_parity_fill_chosen": True}]
    chamadas = {"viol": 0, "core": 0}

    def viol(result, nodes_, *a):
        chamadas["viol"] += 1
        return [{"node_index": 1, "wall_idx": 0, "t_cm": 10.0, "from_course": 0, "courses": 3}] \
            if chamadas["viol"] == 1 else []

    def core(*a, **k):
        chamadas["core"] += 1
        return {"error": None, "novo": True}

    monkeypatch.setattr(m, "_tie_parity_prism_violations", viol)
    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_impl_core", core)
    out = m._tie_parity_prism_rounds({"error": None}, nodes, [], {}, [], {}, 0.0, 4, {})
    assert out.get("novo") and chamadas["core"] == 1
    assert "_tie_parity_flip" not in nodes[1] and "_tie_parity_fill_chosen" not in nodes[1]
    assert nodes[1]["_tie_parity_fill_rejected"] == "PRISM_CONTINUOUS_JOINT"
    assert out["tie_parity_prism_check"] == {"rounds": 1, "reverted": [1], "remaining": []}


def test_prisma_para_no_limite_de_rodadas(monkeypatch):
    nodes = [{"kind": "T_INTERSECTION", "_tie_parity_flip": True, "_tie_parity_fill_chosen": True}
             for _ in range(5)]
    rodada = {"n": 0}

    def viol(result, nodes_, *a):
        vivos = [i for i, n in enumerate(nodes_) if n.get("_tie_parity_flip")]
        return [{"node_index": vivos[0], "wall_idx": 0, "t_cm": 0.0, "from_course": 0, "courses": 3}] if vivos else []

    def core(*a, **k):
        rodada["n"] += 1
        return {"error": None}

    monkeypatch.setattr(m, "_tie_parity_prism_violations", viol)
    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_impl_core", core)
    out = m._tie_parity_prism_rounds({"error": None}, nodes, [], {}, [], {}, 0.0, 4, {})
    assert rodada["n"] == m.TIE_PARITY_PRISM_MAX_ROUNDS
    assert len(out["tie_parity_prism_check"]["reverted"]) == m.TIE_PARITY_PRISM_MAX_ROUNDS
    assert out["tie_parity_prism_check"]["remaining"]      # o que sobrou fica visivel


def test_fiada_vazia_numa_parede_do_t_invertido_e_violacao():
    """82.1 - cobertura: a parede do no' invertido tem pecas nas fiadas 0 e 2 e
    nenhuma na 1 (o criterio do validador COVERAGE_MISSING_ROW)."""
    _walls, nodes, _e2n = _nos_da_sala()
    t = next(i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION")
    parede = sorted(w for w in ws._node_walls(nodes[t]) if w is not None)[0]
    outra = parede + 1
    cheio = {0: [{"wall_idx": parede}], 1: [{"wall_idx": outra}], 2: [{"wall_idx": parede}]}
    viol = m._tie_parity_empty_course_violations({"course_candidates": cheio}, nodes, _walls, [t])
    assert {"node_index": t, "wall_idx": parede, "course": 1, "kind": "COURSE_WITHOUT_PIECES"} in viol
    completo = {0: [{"wall_idx": parede}], 1: [{"wall_idx": parede}], 2: [{"wall_idx": parede}]}
    assert not [v for v in m._tie_parity_empty_course_violations({"course_candidates": completo}, nodes, _walls, [t])
                if v["wall_idx"] == parede]
    assert m._tie_parity_empty_course_violations({"course_candidates": cheio}, nodes, _walls, []) == []


def test_fiada_vazia_devolve_o_t_com_o_motivo(monkeypatch):
    nodes = [{"kind": "T_INTERSECTION", "_tie_parity_flip": True, "_tie_parity_fill_chosen": True}]
    rodadas = {"n": 0}
    monkeypatch.setattr(m, "_tie_parity_prism_violations", lambda *a: [])
    monkeypatch.setattr(m, "_tie_parity_empty_course_violations",
                        lambda r, n, w, inv: [{"node_index": 0, "wall_idx": 0, "course": 1,
                                               "kind": "COURSE_WITHOUT_PIECES"}] if inv else [])

    def core(*a, **k):
        rodadas["n"] += 1
        return {"error": None}

    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_impl_core", core)
    out = m._tie_parity_prism_rounds({"error": None}, nodes, [], {}, [], {}, 0.0, 4, {})
    assert rodadas["n"] == 1
    assert nodes[0]["_tie_parity_fill_rejected"] == "COURSE_WITHOUT_PIECES"
    assert out["tie_parity_prism_check"]["reverted"] == [0]


def test_so_o_que_a_convencao_nao_tinha_conta():
    """82.1 comparativa: a mesma violacao na convencao nao derruba a inversao;
    a regra #2 compara o excesso."""
    junta = {"node_index": 3, "kind": "PRISM_CONTINUOUS_JOINT", "identity": (3, "PRISM", 1, 40)}
    vazia = {"node_index": 3, "kind": "COURSE_WITHOUT_PIECES", "identity": (3, "EMPTY", 1, 5)}
    aglom = {"node_index": 4, "kind": "COMPENSATOR_SEQUENCE", "excess": 2, "identity": (4, "CROWD")}
    pior = m._tie_parity_worse_than_convention([junta, vazia, aglom], [junta, dict(aglom, excess=2)])
    assert [v["kind"] for v in pior] == ["COURSE_WITHOUT_PIECES"]
    pior = m._tie_parity_worse_than_convention([aglom], [dict(aglom, excess=1)])
    assert pior and pior[0]["convention_excess"] == 1
    assert m._tie_parity_worse_than_convention([aglom], []) == [aglom]


def test_aglomeracao_de_compensadores_e_medida_no_preenchimento_real(com_ganho):
    _conv, (res, walls, nodes, _o) = com_ganho
    inv = invertidos(nodes)
    um = m._tie_parity_compensator_crowding(res, nodes, walls, tcr.sb.CATALOG, inv)
    dois = m._tie_parity_compensator_crowding(res, nodes, walls, tcr.sb.CATALOG, inv)
    assert um == dois and sorted(um) == inv and all(v >= 0 for v in um.values())
    assert m._tie_parity_compensator_crowding(res, nodes, walls, tcr.sb.CATALOG, []) == {}


def test_convencao_interna_e_o_solve_sem_a_paridade_geral(monkeypatch):
    """A 82.1 compara com o preenchimento real da CONVENCAO: o solve interno e' o
    mesmo da chave geral desligada, peca a peca, e o estado do solve geral volta."""
    guardado = {}
    real = m._tie_parity_convention_result

    def espia(*a, **k):
        guardado["conv"] = real(*a, **k)
        return guardado["conv"]

    monkeypatch.setattr(m, "_tie_parity_convention_result", espia)
    res, _walls, nodes, _o = resolve(SALA_COM_GANHO, geral=True)
    assert "conv" in guardado and res["tie_parity_prism_check"].get("compared_with_convention")
    assert invertidos(nodes) == res["tie_parity_fill_flips"]              # estado geral restaurado
    off, _w2, _n2, _o2 = resolve(SALA_COM_GANHO, geral=False)

    def assinatura(r):
        return sorted((ci, c.get("wall_idx"), c.get("logical_code"), round(c["origin_world"].X, 4),
                       round(c["origin_world"].Y, 4), round(c["origin_world"].Z, 4))
                      for ci, v in r["course_candidates"].items() for c in v)

    assert assinatura(guardado["conv"]) == assinatura(off)


def test_prisma_sem_inversao_nao_mede_nada():
    assert m._tie_parity_prism_violations({"course_candidates": {0: []}}, [], [], [], {}, 0.0, []) == []


# ----------------------------------------------------------------- sem hardcode
FUNCOES_82 = [
    ws._tie_parity_wall_cost_with_stagger, ws._tie_parity_fill_stagger_cost, ws._tie_parity_full_block_code,
    ws._wall_course_free_segments_abs_cm, ws._tie_parity_midspan_with_openings, ws._tie_parity_openings_of_wall,
    ws._tie_parity_structural_state, ws._tie_parity_structural_worse, ws._search_tie_parity_fill_balance,
    ws._tie_parity_fill_layout_cost, m._tie_parity_prism_violations, m._tie_parity_prism_rounds,
    m._tie_parity_empty_course_violations, m._tie_parity_compensator_crowding,
    m._tie_parity_real_fill_violations, m._tie_parity_worse_than_convention, m._tie_parity_convention_result,
]


@pytest.mark.parametrize("funcao", FUNCOES_82, ids=lambda f: f.__name__)
def test_sem_hardcode(funcao):
    """Nenhum id de elemento, de no', de parede ou nome de projeto no codigo da regra."""
    codigo = inspect.getsource(funcao)
    corpo = re.sub(r'"""[\s\S]*?"""', "", codigo)
    corpo = "\n".join(linha.split("#", 1)[0] for linha in corpo.splitlines())
    assert not re.search(r"\b\d{5,}\b", corpo), funcao.__name__
    for projeto in (r"BUTANT", r"TGD", r"TP1", r"PR49", r"HUMANO", r"MCP"):
        assert not re.search(projeto, corpo, re.IGNORECASE), (funcao.__name__, projeto)
    for identidade in ("node_index ==", "wall_idx ==", "\"T_KEY\"", "no_motor", "element_id"):
        assert identidade not in corpo, (funcao.__name__, identidade)
