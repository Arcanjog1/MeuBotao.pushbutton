# -*- coding: utf-8 -*-
"""Secao 80 (D6, decisao do usuario 2026-09-25): verga e contraverga sao
REFORCO ESTRUTURAL da abertura, independentes da estrategia adicional CHANNEL.

"Sem reforco adicional" (strategy=None) roda o MESMO planejador de canaleta
provado no CHANNEL (secao 51: fiada acima do topo / cujo topo e' o peitoril,
pecas da fiada convertidas em canaleta, corrida ate' o apoio preferencial,
parada em amarracao - regra 75) e NADA MAIS do CHANNEL: nem a passagem livre
51.9, nem a paridade da canaleta 51.14, nem o arranjo 60-65, nem 58.2/68/71/72.
Toda abertura sai com LINTEL_CREATED / LINTEL_NOT_REQUIRED / LINTEL_UNRESOLVED
e SILL_REINFORCEMENT_* no rastreio `opening_structural_trace`, e cada corrida
parada por uma amarracao fica em `channel_stopped_by_junction`, com a CAUSA
(D16: CHANNEL_STOP_RULE_75 / _SUPPORT_RULE / _EXISTING_JUNCTION_PIECE / _GEOMETRY).

Fixtures sinteticas (nenhum ID do projeto): parede livre com porta e janela,
T com a jamba na face da parede que chega, passagem entre dois T, vao ate' o
topo, topo fora da grade e o U dos cantos L 55/56.

    python3 -m pytest tests/test_opening_structural_reinforcement.py -q
"""
import inspect
import io
import os
import re
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

m, ft, seg, solve = tcr.m, tcr.ft, tcr.seg, tcr.solve
CAT = tcr.sb.CATALOG
NUM = tcr.NUM_COURSES
F = 30.48


def _u_55_56():
    """U dos cantos L 55/56: parede de 101 cm entre dois L, janela com pilares de
    19,5 / 29,5 cm, peitoril 40 (na grade) e topo 91 (fora da grade)."""
    lines = [seg(0, 0, 101.0, 0), seg(0, 0, 0, -242.0), seg(101.0, 0, 101.0, -242.0)]
    return lines, [[(ft(19.5), ft(115.0 - 29.5), ft(40.0), ft(91.0))], [], []]


def _off_grid():
    return [seg(0, 0, 600, 0)], [[(ft(400), ft(461), ft(80), ft(171))]]


def _wall_top():
    return [seg(0, 0, 600, 0)], [[(ft(200), ft(300), ft(0), ft(280))]]


_CACHE = {}


def _solve(nome, estrategia=None, **kw):
    fixtures = {"free_wall": tcr.free_wall, "tee": lambda: tcr.tee(80.0), "passage": tcr.passage,
                "u_55_56": _u_55_56, "off_grid": _off_grid, "wall_top": _wall_top}
    chave = (nome, estrategia, tuple(sorted(kw.items())))
    if chave not in _CACHE:
        lines, ops = fixtures[nome]()
        _CACHE[chave] = solve(lines, ops, strategy=estrategia, num_courses=kw.get("num_courses", NUM))
    return _CACHE[chave]


def _sem_80(lines, ops, estrategia=None, num_courses=NUM):
    antes = m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED
    m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = False
    try:
        return solve(lines, ops, strategy=estrategia, num_courses=num_courses)
    finally:
        m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = antes


def _linhas(res):
    return sorted(res["opening_structural_trace"], key=lambda r: (r["wall_idx"], r["opening_index"]))


def _canaletas(res, ci=None):
    return [c for k, pecas in res["course_candidates"].items() if ci is None or k == ci
            for c in pecas if orf.is_channel_code(c["logical_code"])]


def _assinatura_completa(res):
    """Identidade fisica COMPLETA: fiada, codigo, centro, comprimento, direcao
    local (a rotacao do vazado menor), espelhamento e comprimento de instancia."""
    linhas = []
    for ci, pecas in sorted(res["course_candidates"].items()):
        for c in pecas:
            o, xd = c["origin_world"], c.get("x_dir")
            linhas.append((ci, c["logical_code"], round(o.X * F, 2), round(o.Y * F, 2), round(c["length_cm"], 3),
                           (round(xd.X, 4), round(xd.Y, 4)) if xd is not None else None,
                           bool(c.get("mirrored")), c.get("instance_length_cm")))
    return sorted(linhas, key=repr)


def _sem_invasao(res, walls, openings):
    pf = m.controlled_beta_preflight(res, walls, openings, CAT, 0.0)
    plano = m.materialization_plan(res, pf)
    return (not pf.get("opening_violations") and not pf.get("collisions") and not plano["skip"])


# ----------------------------------------------------------------- porta e janela
@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_porta_com_alvenaria_acima_recebe_verga(estrategia):
    res, walls, _n, openings = _solve("free_wall", estrategia)
    porta = _linhas(res)[0]
    assert porta["type"] == "DOOR" and porta["strategy"] == (estrategia or "NONE")
    assert porta["lintel_required"] is True and porta["lintel_status"] == m.LINTEL_CREATED
    assert porta["lintel_course"] == 11                      # fiada cuja base e' o topo (221)
    assert porta["lintel_codes"] and all(orf.is_channel_code(c) for c in porta["lintel_codes"])
    assert porta["lintel_start"] <= porta["start_cm"] and porta["lintel_end"] >= porta["end_cm"]
    assert porta["lintel_left_support"] >= 0 and porta["lintel_right_support"] >= 0
    assert porta["sill_required"] is False and porta["sill_status"] == m.SILL_REINFORCEMENT_NOT_REQUIRED
    assert _canaletas(res, 11)
    assert _sem_invasao(res, walls, openings)


@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_janela_recebe_verga_e_contraverga(estrategia):
    res, walls, _n, openings = _solve("free_wall", estrategia)
    janela = _linhas(res)[1]
    assert janela["type"] == "WINDOW"
    assert janela["lintel_status"] == m.LINTEL_CREATED and janela["lintel_course"] == 11
    assert janela["sill_required"] is True and janela["sill_status"] == m.SILL_REINFORCEMENT_CREATED
    assert janela["sill_course"] == 4                        # fiada cujo topo e' o peitoril (100)
    assert janela["sill_codes"] and all(orf.is_channel_code(c) for c in janela["sill_codes"])
    assert janela["requires_human_review"] is False
    assert _sem_invasao(res, walls, openings)


def test_none_e_channel_dao_o_mesmo_papel_estrutural_na_mesma_parede():
    """Numa parede sem encontro (nada das regras do CHANNEL muda o layout ali),
    o reforco estrutural das duas opcoes e' identico: mesmas fiadas, codigos e
    corridas."""
    none, _w, _n, _o = _solve("free_wall", None)
    chan, _w2, _n2, _o2 = _solve("free_wall", tcr.CHANNEL)
    campos = ("lintel_status", "lintel_course", "lintel_codes", "lintel_start", "lintel_end",
              "sill_status", "sill_course", "sill_codes", "sill_start", "sill_end")
    for a, b in zip(_linhas(none), _linhas(chan)):
        assert [a[c] for c in campos] == [b[c] for c in campos]


def test_espelhamento_mantem_os_status():
    lines, ops = tcr.free_wall()
    direto, _w, _n, _o = solve(lines, ops, strategy=None)
    invertido, _w2, _n2, _o2 = solve(lines, ops, strategy=None, reverse=True)
    status = lambda res: sorted((r["type"], r["lintel_status"], r["lintel_course"], r["sill_status"],
                                 r["sill_course"]) for r in res["opening_structural_trace"])
    assert status(direto) == status(invertido)
    # a corrida pode juntar vergas vizinhas conforme o sentido do preenchimento,
    # mas sempre cobre o vao inteiro
    for res in (direto, invertido):
        for r in res["opening_structural_trace"]:
            assert r["lintel_start"] <= r["start_cm"] + 0.5 and r["lintel_end"] >= r["end_cm"] - 0.5


# ----------------------------------------------------------------- sem alvenaria acima / fora da grade
@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_vao_ate_o_topo_da_parede_nao_requer_verga(estrategia):
    res, _w, _n, _o = _solve("wall_top", estrategia)
    linha = _linhas(res)[0]
    assert linha["lintel_required"] is False
    assert linha["lintel_status"] == m.LINTEL_NOT_REQUIRED
    assert linha["lintel_reason"] == "NO_MASONRY_ABOVE_REACHES_WALL_TOP"
    assert not _canaletas(res)


def test_passagem_livre_so_no_channel_e_o_none_mantem_alvenaria_com_verga():
    """51.9 continua SO' no CHANNEL (a decisao do usuario nao a liga no None):
    no CHANNEL a porta entre dois T fica aberta ate' o topo (NOT_REQUIRED); sem
    reforco adicional a alvenaria acima existe, entao a verga e' exigida."""
    chan, _w, _n, _o = _solve("passage", tcr.CHANNEL)
    linha = _linhas(chan)[0]
    assert linha["lintel_status"] == m.LINTEL_NOT_REQUIRED and linha["lintel_reason"] == "FREE_TO_TOP_PASSAGE_51_9"
    none, walls, _n2, openings = _solve("passage", None)
    assert none["opening_reinforcement"]["free_to_top"] == []
    linha = _linhas(none)[0]
    assert linha["lintel_required"] is True and linha["lintel_status"] == m.LINTEL_CREATED
    assert linha["lintel_course"] == 11
    sobre = tcr.codes_over(none, walls, 0, 11, 227, 473)     # a verga cobre o vao na fiada 11
    assert sobre and all(orf.is_channel_code(c) for c in sobre)
    assert tcr.codes_over(none, walls, 0, 12, 227, 473)      # alvenaria acima do vao
    assert _sem_invasao(none, walls, openings)


@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_topo_fora_da_grade_fica_sem_solucao_e_nao_inventa_canaleta(estrategia):
    res, walls, _n, openings = _solve("off_grid", estrategia)
    linha = _linhas(res)[0]
    assert linha["lintel_status"] == m.LINTEL_UNRESOLVED
    assert linha["lintel_reason"] == "HEAD_OFF_GRID_51_8"
    assert linha["requires_human_review"] is True and linha["top_cm"] == pytest.approx(171.0)
    lo, hi = linha["lintel_course_grid_cm"]
    assert lo < 171.0 < hi and hi - lo == pytest.approx(20.0)
    assert linha["lintel_codes"] == [] and linha["lintel_course"] is None
    # a contraverga (peitoril 80, na grade) continua criada
    assert linha["sill_status"] == m.SILL_REINFORCEMENT_CREATED
    # nenhuma canaleta nas fiadas cortadas pelo topo nem logo acima
    assert not _canaletas(res, 8) and not _canaletas(res, 9)
    assert _sem_invasao(res, walls, openings)
    assert m.unresolved_opening_reinforcement(res)[0]["status"] == m.LINTEL_UNRESOLVED


# ----------------------------------------------------------------- encontros e regra 75
def test_janela_junto_ao_l_impedida_pela_regra_75():
    """O U dos cantos 55/56: o B34 de canto (paridade 30.5) entra sob o
    peitoril; canaleta nunca substitui amarracao, entao a contraverga fica sem
    solucao, com o no' que a impede - e o topo (91) esta' fora da grade."""
    res, walls, _n, openings = _solve("u_55_56")
    linha = _linhas(res)[0]
    assert linha["sill_status"] == m.SILL_REINFORCEMENT_UNRESOLVED
    assert linha["sill_reason"] == "RULE_75_TIE_OVER_SPAN"
    assert linha["sill_stopped_by_junction"] is True and linha["sill_junction_ids"]
    assert linha["lintel_status"] == m.LINTEL_UNRESOLVED and linha["lintel_reason"] == "HEAD_OFF_GRID_51_8"
    paradas = [p for p in res["channel_stopped_by_junction"] if p["role"] == "SILL"]
    assert paradas and all(p["reason"] == m.CHANNEL_STOP_RULE_75 and p["junction_id"] in linha["sill_junction_ids"]
                           for p in paradas)
    # as amarracoes dos cantos continuam as mesmas (a 76.1 nao muda)
    sem80, _w0, _n0, _o0 = _sem_80(*_u_55_56())
    assert res["missing_required_junction_bond"] == sem80["missing_required_junction_bond"]
    assert _sem_invasao(res, walls, openings)


@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_abertura_junto_ao_t_registra_a_parada_pela_regra_75(estrategia):
    res, _w, nodes, _o = _solve("tee", estrategia)
    linha = _linhas(res)[0]
    assert linha["lintel_status"] == m.LINTEL_CREATED
    assert linha["lintel_stopped_by_junction"] is True
    t = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"][0]
    assert t in linha["lintel_junction_ids"]
    paradas = [p for p in res["channel_stopped_by_junction"] if p["role"] == "LINTEL"]
    assert paradas and paradas[0]["junction_id"] == t and paradas[0]["reason"] == m.CHANNEL_STOP_RULE_75
    assert paradas[0]["channel_stopped_by_junction"] is True
    assert paradas[0]["remaining_support_cm"] is not None
    assert res["opening_structural_summary"][m.CHANNEL_STOPS_AT_JUNCTION] == len(res["channel_stopped_by_junction"])


# ----------------------------------------------------------------- canaleta nunca amarra
@pytest.mark.parametrize("nome", ["free_wall", "tee", "u_55_56", "passage"])
@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_canaleta_de_abertura_nunca_conta_como_amarracao(nome, estrategia):
    res, _w, _n, _o = _solve(nome, estrategia)
    assert res["channel_as_junction_bond"] == []
    for row in res["bond_trace"]:
        if row["bond_resolved"]:
            assert (row.get("selected") or {}).get("code") in ws.JUNCTION_BOND_CODES, row
    assert not [c for c in _canaletas(res) if c.get("node_index") is not None]


@pytest.mark.parametrize("papel", ["verga", "contraverga", "topo"])
def test_canaleta_no_lugar_da_amarracao_e_reprovada_pelos_dois_gates(papel):
    """Prova nao vacua: uma canaleta posta no lugar da peca de amarracao do T -
    na fiada da verga, da contraverga ou do topo - e' acusada pela regra 75 e o
    encontro fica sem amarracao pela 76.1. Papel de abertura nunca amarra."""
    res, walls, nodes, openings = _solve("tee", None)
    t = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"][0]
    ci = {"verga": 11, "contraverga": 3, "topo": NUM - 1}[papel]
    copia = dict(res)
    copia["course_candidates"] = dict((k, list(v)) for k, v in res["course_candidates"].items())
    trocadas = 0
    for i, c in enumerate(copia["course_candidates"][ci]):
        if c.get("node_index") == t and c["logical_code"] in ws.JUNCTION_BOND_CODES:
            copia["course_candidates"][ci][i] = dict(c, logical_code=orf.CHANNEL_U_34)
            trocadas += 1
    assert trocadas
    assert orf.channel_as_junction_bond(copia["course_candidates"], None)
    audit = m._junction_bond_audit_final(copia, nodes, walls, openings, CAT, 0.0, NUM, None)
    assert any(x["node_index"] == t and x["course_index"] == ci for x in audit["missing"])


# ----------------------------------------------------------------- independencia do CHANNEL
@pytest.mark.parametrize("geral", [True, False])
def test_none_nao_liga_nenhuma_regra_da_estrategia_adicional(monkeypatch, geral):
    """Durante o solve sem reforco adicional: 68 e 58.2 desligadas; a paridade
    51.14 nunca roda; 51.9 nao decide. SECAO 81: 71 e o arranjo 60-65 sao regras
    GERAIS de composicao - ligados no NONE com a chave geral (o arranjo sempre com
    a aceitacao exata por parede) e desligados sem ela. SECAO 82: a busca de
    paridade pelo preenchimento (72) tambem e' regra GERAL - no NONE ela roda com a
    chave da 82 (aberturas da banda como fronteira + veto estrutural)."""
    monkeypatch.setattr(m, "GENERAL_COMPOSITION_QUALITY_ENABLED", geral)
    monkeypatch.setattr(m, "GENERAL_TIE_PARITY_ENABLED", geral)
    estados, arranjos, chamadas = [], [], []
    core = m._solve_building_blocks_all_courses_core

    def espia_core(*a, **k):
        estados.append((ws.OPENING_REPAIR_PREFER_CLEAN_ACTIVE, ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK,
                        ws.COMPENSATOR_COUNT_IN_TIEBREAK, ws.TIE_PARITY_FILL_BALANCE,
                        ws.TIE_PARITY_FILL_OPENING_BOUNDARIES, ws.TIE_PARITY_STRUCTURAL_VETO))
        return core(*a, **k)

    orient = m._orient_small_voids_final

    def espia_orient(*a, **k):
        arranjos.append(bool(k.get("arrange")))
        if k.get("arrange"):
            assert k.get("validate_wall") is not None  # nunca sem a aceitacao exata
        return orient(*a, **k)

    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_core", espia_core)
    monkeypatch.setattr(m, "_orient_small_voids_final", espia_orient)
    monkeypatch.setattr(m, "_channel_tie_parity_trials", lambda *a, **k: chamadas.append("51.14") or {})
    real_busca = ws._search_tie_parity_fill_balance
    monkeypatch.setattr(ws, "_search_tie_parity_fill_balance",
                        lambda *a, **k: chamadas.append("72") or real_busca(*a, **k))
    lines, ops = tcr.tee(80.0)
    res, _w, _n, _o = solve(lines, ops, strategy=None)
    assert estados and not any(any(e[:2]) for e in estados), estados  # 68, 58.2
    assert all(e[2] is geral for e in estados), estados                # 71 (geral, 81)
    assert all(e[3] is geral and e[4] is geral and e[5] is geral for e in estados), estados  # 72/82 (geral)
    assert arranjos and any(arranjos) is geral, arranjos               # 60-65 (geral)
    assert "51.14" not in chamadas                                     # 51.14 nunca
    assert ("72" in chamadas) is geral, chamadas                       # busca 72 so' com a chave da 82
    assert res["opening_reinforcement"]["free_to_top"] == []           # 51.9
    assert "channel_tie_parity_trials" not in res
    assert _canaletas(res)                                             # e a verga existe


def test_none_e_o_motor_sem_a_secao_80_mais_o_planejador_de_abertura(monkeypatch):
    """Independencia real: o resultado sem reforco adicional e' o motor sem a
    secao 80 com SO' o planejador de verga/contraverga aplicado por cima.

    SECAO 81: vale para a secao 80 ISOLADA (chave geral desligada). Com as
    regras gerais de composicao, orientacao e arranjo rodam DEPOIS da conversao
    (a ordem do CHANNEL) e podem mexer fora das corridas - ver §80.1/§81 e
    test_regras_gerais_composicao.py."""
    monkeypatch.setattr(m, "GENERAL_COMPOSITION_QUALITY_ENABLED", False)
    lines, ops = tcr.tee(80.0)
    produto, walls, nodes, openings = solve(lines, ops, strategy=None)
    base, walls0, nodes0, openings0 = _sem_80(lines, ops)
    plano = orf.plan_channel_reinforcement(base["course_candidates"], walls0, openings0,
                                           m._free_to_top_band(CAT, 0.0), NUM, 0.0, nodes=nodes0,
                                           catalog=CAT, free_to_top=[])
    esperado = dict(base, course_candidates=plano["course_candidates"])
    assert tcr.physical_signature(produto, walls) == tcr.physical_signature(esperado, walls0)
    # inclusive a rotacao do vazado menor (secao 52) e o espelhamento: fora das
    # corridas de verga/contraverga nenhuma peca muda
    assert _assinatura_completa(produto) == _assinatura_completa(esperado)
    # a canaleta foi validada e a amarracao reauditada com o catalogo de canaletas
    assert produto["opening_reinforcement"]["validation"] is not None
    assert produto["opening_reinforcement"]["validation"]["counts"].get("OPENING_INVASION", 0) == 0
    assert "wall_bond_audits_before_reinforcement" in produto
    assert produto["small_void_alignment"]["after"] == len(produto["small_void_alignment"]["violations"])


def test_none_ignora_politica_que_religaria_a_travessia_do_t():
    """REGRA 75 absoluta no reforco estrutural: uma politica recebida com 51.6 /
    51.7 ligadas nao muda nada sem reforco adicional."""
    lines, ops = tcr.tee(80.0)
    padrao, _w, _n, _o = solve(lines, ops, strategy=None)
    forcada, _w2, _n2, _o2 = solve(lines, ops, strategy=None,
                                   policy={"channel_may_cross_node_tie": True, "convert_blocking_along_ties": True})
    assert _assinatura_completa(forcada) == _assinatura_completa(padrao)
    assert forcada["opening_reinforcement"]["policy"]["channel_may_cross_node_tie"] is False
    assert forcada["opening_reinforcement"]["policy"]["convert_blocking_along_ties"] is False
    assert forcada["channel_as_junction_bond"] == []


@pytest.mark.parametrize("nome", ["free_wall", "tee", "passage", "u_55_56"])
def test_channel_mantem_o_comportamento_atual(nome):
    fixtures = {"free_wall": tcr.free_wall, "tee": lambda: tcr.tee(80.0), "passage": tcr.passage,
                "u_55_56": _u_55_56}
    lines, ops = fixtures[nome]()
    com, walls, _n, _o = solve(lines, ops, strategy=tcr.CHANNEL)
    sem, walls0, _n0, _o0 = _sem_80(lines, ops, estrategia=tcr.CHANNEL)
    assert tcr.physical_signature(com, walls) == tcr.physical_signature(sem, walls0)
    assert _assinatura_completa(com) == _assinatura_completa(sem)
    assert com["missing_required_junction_bond"] == sem["missing_required_junction_bond"]


def test_familias_de_canaleta_ausentes_planejam_sem_converter_e_ficam_sem_solucao():
    lines, ops = tcr.free_wall()
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, ops, CAT, 0.0, NUM,
                                              variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
                                              opening_structural_channel_available=False)
    base, walls0, _n0, _o0 = _sem_80(lines, ops)
    assert not _canaletas(res)
    assert tcr.physical_signature(res, walls) == tcr.physical_signature(base, walls0)
    linhas = _linhas(res)
    assert [r["lintel_status"] for r in linhas] == [m.LINTEL_UNRESOLVED] * 2
    assert all(r["lintel_reason"] == "CHANNEL_FAMILY_MISSING" and r["requires_human_review"] for r in linhas)
    assert linhas[1]["sill_status"] == m.SILL_REINFORCEMENT_UNRESOLVED
    assert res["opening_reinforcement"]["pieces_applied"] is False


# ----------------------------------------------------------------- host / UI
def test_host_sem_reforco_confere_canaletas_uma_vez_sem_bloquear():
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = None
    chamadas = []
    faltando = [{"logical_code": "CHANNEL_U_CUT", "family_name": "x", "type_name": "x", "reason": "MISSING"}]
    handler._load_channel_family_catalog = lambda doc: chamadas.append(1) or ({}, faltando)
    handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    assert chamadas == [1]
    assert handler._opening_structural_channel_available() is False
    assert handler._creation_catalog() is handler.catalog
    # o usuario carrega a familia e reanalisa: enquanto faltar, rele
    completo = dict((code, {"is_channel": True, "source_instance_id": code}) for code in m.CHANNEL_FAMILY_CATALOG_DEFINITIONS)
    handler._load_channel_family_catalog = lambda doc: chamadas.append(2) or (completo, [])
    handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    assert chamadas == [1, 2] and handler._opening_structural_channel_available() is True
    handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    assert chamadas == [1, 2]                                  # completo: nao rele mais
    outro = m._PostCreationEventHandler()
    outro.opening_reinforcement_strategy = None
    outro._load_channel_family_catalog = lambda doc: (completo, [])
    outro._ensure_opening_reinforcement_catalog(SimpleNamespace())
    assert outro._opening_structural_channel_available() is True
    assert set(m.CHANNEL_FAMILY_CATALOG_DEFINITIONS) <= set(outro._creation_catalog())


def test_verga_sem_solucao_entra_na_revisao_e_no_estado_estrutural():
    from core import ui_state
    res, _w, _n, _o = _solve("off_grid")
    itens = m.unresolved_opening_reinforcement(res)
    assert itens and itens[0]["requires_human_review"] is True
    textos = [r["text"] for r in ui_state.review_items(res)]
    assert any(u"Verga NÃO resolvida" in t and "HEAD_OFF_GRID_51_8" in t for t in textos)


def test_rotulo_da_opcao_sem_reforco_diz_que_ha_verga():
    rotulos = dict((k, v) for k, v, _ok in m.OPENING_REINFORCEMENT_UI_OPTIONS)
    assert rotulos["NONE"] == u"Sem reforço adicional"
    assert m.DEFAULT_OPENING_REINFORCEMENT_UI_VALUE == "NONE"


# ----------------------------------------------------------------- sem hardcode
def test_nenhum_identificador_de_projeto_na_secao_80():
    fontes = "\n".join(inspect.getsource(f) for f in (
        m._apply_opening_structural_reinforcement, m._attach_opening_structural_trace,
        m._opening_role_trace, m._opening_structural_trace_rows, m._opening_grid_cm,
        m._opening_rule48_overlap_cm, m._opening_trace_apply_materialization,
        m.opening_reinforcement_review, m.unresolved_opening_reinforcement, m._fill_opening_trace_ids))
    assert "8284" not in fontes and "BUTANT" not in fontes.upper()
    assert not re.search(r"(opening_index|wall_idx|node_index)\s*==\s*\d", fontes)


# ----------------------------------------------------------------- achados da revisao adversarial
@pytest.mark.parametrize("papel,peitoril,topo", [("lintel", 100.0, 221.3), ("sill", 99.7, 221.0)])
def test_vao_que_entra_na_fiada_da_canaleta_fica_sem_solucao_pela_regra_48(papel, peitoril, topo):
    """A grade aceita 0,5 cm; a regra 48 so' 0,1 cm. Topo 221,3 (ou peitoril
    99,7) poe a canaleta 0,3 cm dentro do vao: a materializacao a pula - a verga
    (contraverga) NAO existe e o rastreio diz isso ja' no calculo."""
    lines, ops = [seg(0, 0, 600, 0)], [[(ft(200), ft(300), ft(peitoril), ft(topo))]]
    res, walls, _n, openings = solve(lines, ops, strategy=None)
    linha = _linhas(res)[0]
    esperado = {"lintel": (m.LINTEL_UNRESOLVED, "HEAD_IN_COURSE_RULE_48", 11),
                "sill": (m.SILL_REINFORCEMENT_UNRESOLVED, "SILL_IN_COURSE_RULE_48", 4)}[papel]
    assert (linha[papel + "_status"], linha[papel + "_reason"], linha[papel + "_course"]) == esperado
    assert linha[papel + "_requires_human_review"] is True and linha["requires_human_review"] is True
    lo, hi = linha[papel + "_course_grid_cm"]
    cota = topo if papel == "lintel" else peitoril
    assert lo <= cota < hi
    # prova: a materializacao pula justamente as canaletas dessa fiada
    pf = m.controlled_beta_preflight(res, walls, openings, CAT, 0.0)
    plano = m.materialization_plan(res, pf)
    puladas = set((ci, orf.is_channel_code(rec.get("logical_code"))) for ci, _i, rec in plano["skip"])
    assert puladas == {(esperado[2], True)}
    assert any(i["role"] == papel.upper() for i in m.unresolved_opening_reinforcement(res))


def _handler_de_teste(res, walls, openings, estrategia=None):
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = estrategia
    handler.walls_to_create, handler.openings_per_wall = walls, openings
    handler.catalog = dict(CAT)
    handler.base_z_abs = 0.0
    handler.wall_height_ft = ft(280.0)
    handler._num_courses_for_wall_height = lambda *a, **k: (NUM, None)
    handler.selected_level = None
    kwargs = {}
    handler._solve_building_blocks_all_courses = lambda *a, **k: kwargs.update(k) or res
    handler._save_modulation_state_cache = lambda: None
    handler._opening_structural_channel_available = lambda: False
    return handler, kwargs


def test_rastreio_reconcilia_com_a_materializacao_no_host(monkeypatch):
    """Canaleta de verga pulada pela materializacao (qualquer regra 48) derruba
    a verga para *_UNRESOLVED no rastreio, no resumo e na revisao - pelo
    `_execute_solve` real."""
    lines, ops = tcr.free_wall()
    res, walls, _n, openings = solve(lines, ops, strategy=None)
    janela = _linhas(res)[1]
    alvo = [c for c in res["course_candidates"][11] if orf.is_channel_code(c["logical_code"])
            and c["reinforcement"]["run_id"] == janela["lintel_run_id"]][0]
    real = m.materialization_plan

    def plano_com_pulo(resultado, preflight):
        plano = real(resultado, preflight)
        plano["skip"] = list(plano["skip"]) + [(11, id(alvo), {"rule_id": "OPENING_VOID_INVASION",
                                                                "course_index": 11,
                                                                "logical_code": alvo["logical_code"]})]
        return plano

    monkeypatch.setattr(m, "materialization_plan", plano_com_pulo)
    handler, kwargs = _handler_de_teste(res, walls, openings)
    handler._execute_solve()
    # sem reforco adicional, o host passa a disponibilidade das canaletas
    assert kwargs["opening_structural_channel_available"] is False
    linha = _linhas(handler.solve_result)[1]
    assert linha["lintel_status"] == m.LINTEL_UNRESOLVED
    assert linha["lintel_reason"] == "REGRA_48_OPENING_VOID_INVASION"
    assert handler.solve_result["opening_structural_summary"][m.LINTEL_UNRESOLVED] >= 1


def test_host_com_channel_declara_canaletas_disponiveis():
    lines, ops = tcr.free_wall()
    res, walls, _n, openings = solve(lines, ops, strategy=tcr.CHANNEL)
    handler, kwargs = _handler_de_teste(res, walls, openings, estrategia=tcr.CHANNEL)
    handler._execute_solve()
    assert kwargs["opening_structural_channel_available"] is True


@pytest.mark.parametrize("peitoril", [0.6, 1.0, 10.0, 19.0])
def test_peitoril_dentro_da_primeira_fiada_e_porta_pela_10_4(peitoril):
    """Nao ha' fiada cujo topo seja o peitoril (e nenhuma alvenaria abaixo dele):
    o vao toca a fiada mais baixa - porta, contraverga nao requerida."""
    lines, ops = [seg(0, 0, 600, 0)], [[(ft(200), ft(300), ft(peitoril), ft(221))]]
    res, walls, _n, openings = solve(lines, ops, strategy=None)
    linha = _linhas(res)[0]
    assert linha["type"] == "DOOR"
    assert linha["sill_required"] is False and linha["sill_status"] == m.SILL_REINFORCEMENT_NOT_REQUIRED
    assert linha["sill_reason"] == "SILL_WITHIN_LOWEST_COURSE_10_4"
    assert linha["lintel_status"] == m.LINTEL_CREATED
    assert not _canaletas(res, 0) and _sem_invasao(res, walls, openings)


def test_peitoril_no_topo_da_primeira_fiada_tem_contraverga():
    lines, ops = [seg(0, 0, 600, 0)], [[(ft(200), ft(300), ft(20.0), ft(221))]]
    res, walls, _n, openings = solve(lines, ops, strategy=None)
    linha = _linhas(res)[0]
    assert linha["type"] == "WINDOW" and linha["sill_status"] == m.SILL_REINFORCEMENT_CREATED
    assert linha["sill_course"] == 0 and _sem_invasao(res, walls, openings)


def test_verga_criada_sem_assentamento_vai_para_revisao_sem_virar_minimo():
    """Junto ao T a verga para na amarracao (regra 75) com apoio <= 0,5 cm num
    lado (51.4 ACTUAL_ERROR): fica CRIADA, entra na revisao humana, mas NAO e'
    pendencia estrutural (nenhum minimo novo de apoio neste ciclo)."""
    from core import ui_state
    res, _w, _n, _o = _solve("tee", None)
    linha = _linhas(res)[0]
    assert linha["lintel_status"] == m.LINTEL_CREATED and linha["lintel_reason"] == "SUPPORT_ACTUAL_ERROR"
    revisao = m.opening_reinforcement_review(res)
    assert revisao and all(i["requires_human_review"] and i["status"].endswith("_CREATED") for i in revisao)
    assert [i for i in revisao if i["role"] == "LINTEL"][0]["junction_ids"] == linha["lintel_junction_ids"]
    assert m.unresolved_opening_reinforcement(res) == []
    textos = [r["text"] for r in ui_state.review_items(res)]
    assert any(u"Verga criada sem assentamento" in t for t in textos)


def test_estado_estrutural_do_channel_so_muda_com_a_secao_80():
    """Com a secao 80 o CHANNEL passa a contar verga sem solucao como pendencia
    estrutural (mudanca INTENCIONAL - as pecas continuam identicas); sem ela,
    nada muda."""
    res, _w, _n, _o = _solve("off_grid", tcr.CHANNEL)
    assert m.unresolved_opening_reinforcement(res)
    antes = m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED
    m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = False
    try:
        assert m.unresolved_opening_reinforcement(res) == []
    finally:
        m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = antes


def test_criacao_avisa_verga_sem_solucao_sem_bloquear():
    from core import ui_state
    res, _w, _n, _o = _solve("off_grid", None)
    assert ui_state.opening_reinforcement_pending(res) == 1
    textos = [r["text"] for r in ui_state.review_items(res)]
    assert any(u"Verga NÃO resolvida" in t and u"#0" in t for t in textos)


def test_canaleta_com_altura_diferente_dos_blocos_nao_e_usada():
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = None
    handler.catalog = {"B39": {"height_cm": 19.0}}
    handler.channel_catalog_missing = []
    codigos = sorted(m.CHANNEL_FAMILY_CATALOG_DEFINITIONS)
    handler.channel_catalog = dict((code, {"is_channel": True, "height_cm": 19.0}) for code in codigos)
    assert handler._opening_structural_channel_available() is True
    handler.channel_catalog[codigos[0]] = {"is_channel": True, "height_cm": 20.0}
    assert handler._opening_structural_channel_available() is False
    assert handler._creation_catalog() is handler.catalog


def test_gate_75_do_none_nao_e_vacuo(monkeypatch):
    """Se o planejador (por qualquer defeito) entregasse uma canaleta no lugar
    da amarracao do T, o caminho sem reforco adicional a acusa: regra 75 e 76.1."""
    real = orf.plan_channel_reinforcement
    alvo = {}

    def planejador_defeituoso(course_candidates, walls, openings, *a, **k):
        plano = real(course_candidates, walls, openings, *a, **k)
        nos = k.get("nodes") or []
        t = [i for i, n in enumerate(nos) if n.get("kind") == "T_INTERSECTION"][0]
        fiada = list(plano["course_candidates"][11])
        for i, c in enumerate(fiada):
            if c.get("node_index") == t and c["logical_code"] in ws.JUNCTION_BOND_CODES:
                fiada[i] = dict(c, logical_code=orf.CHANNEL_U_34)
                alvo["t"] = t
        plano["course_candidates"] = dict(plano["course_candidates"])
        plano["course_candidates"][11] = fiada
        return plano

    monkeypatch.setattr(orf, "plan_channel_reinforcement", planejador_defeituoso)
    lines, ops = tcr.tee(80.0)
    res, _w, _n, _o = solve(lines, ops, strategy=None)
    assert "t" in alvo
    assert any(v["node_index"] == alvo["t"] and v["course_index"] == 11 for v in res["channel_as_junction_bond"])
    assert any(x["node_index"] == alvo["t"] and x["course_index"] == 11
               for x in res["missing_required_junction_bond"])


def test_microajuste_nao_trata_o_apoio_preferencial_como_portao_no_reforco_estrutural():
    base = {"course_candidates": {}, "opening_reinforcement": {
        "validation": {"counts": {"SUPPORT_BELOW_POLICY": 2, "OPENING_INVASION": 0}}}}
    band = m._free_to_top_band(CAT, 0.0)
    _res, walls, _n, openings = _solve("free_wall", None)
    channel = m._micro_adjust_measure(base, walls, openings, CAT, band, 0)["gates"]
    assert channel["CHANNEL_SUPPORT_BELOW_POLICY"] == 2
    estrutural = dict(base, opening_reinforcement=dict(base["opening_reinforcement"],
                                                       scope=m.OPENING_STRUCTURAL_SCOPE))
    gates = m._micro_adjust_measure(estrutural, walls, openings, CAT, band, 0)["gates"]
    assert "CHANNEL_SUPPORT_BELOW_POLICY" not in gates and gates["CHANNEL_OPENING_INVASION"] == 0


def test_modulos_da_secao_80_compativeis_com_ironpython27():
    """UI e reforco rodam em IronPython 2.7 no Revit (arvore de sintaxe)."""
    import ast
    raiz = os.path.dirname(HERE)
    proibidos = tuple(getattr(ast, n) for n in ("JoinedStr", "Nonlocal", "NamedExpr", "YieldFrom", "AnnAssign",
                                                 "AsyncFunctionDef", "AsyncFor", "AsyncWith", "Await", "Match")
                      if hasattr(ast, n))
    alvos = [("nuvem", "core", "engine", "opening_reinforcement.py"), ("nuvem", "core", "wall_modeling.py")]
    alvos += [("nuvem", "core", nome) for nome in sorted(os.listdir(os.path.join(raiz, "nuvem", "core")))
              if nome.startswith("ui_") and nome.endswith(".py")]
    for rel in alvos:
        arvore = ast.parse(io.open(os.path.join(raiz, *rel), encoding="utf-8").read())
        achados = []
        for no in ast.walk(arvore):
            if isinstance(no, proibidos):
                achados.append((type(no).__name__, getattr(no, "lineno", None)))
            elif isinstance(no, (ast.FunctionDef, ast.Lambda)):
                a = no.args
                if a.kwonlyargs or getattr(a, "posonlyargs", None):
                    achados.append(("kwonly/posonly", getattr(no, "lineno", None)))
            elif isinstance(no, ast.Raise) and no.cause is not None:
                achados.append(("raise from", no.lineno))
            elif isinstance(no, ast.Dict) and any(k is None for k in no.keys):
                achados.append(("{**d}", no.lineno))
            elif (isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "print"
                  and any(k.arg in ("end", "sep", "file", "flush") for k in no.keywords)):
                achados.append(("print(..., end=)", no.lineno))
        assert not achados, (rel, achados[:10])
