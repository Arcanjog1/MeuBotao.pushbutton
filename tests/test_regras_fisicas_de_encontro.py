# -*- coding: utf-8 -*-
"""Secao 79 (2026-09-24, ciclo 3 / D2-D3) - as regras FISICAS de encontro
(tolerancia do teste de espaco do T - 74; T degradado para L medido do CONTATO
- 76 D1; compensador de no' nunca designado amarracao - 76.1; papel funcional do
encontro por fiada - 77) e os gates 76/76.1 valem tambem SEM reforco de
abertura, e toda RUN leva o rastreio `bond_trace` por no'/fiada.

Fixtures sinteticas com as topologias medidas no BUTANTA (nenhum ID, nome ou
coordenada do projeto no motor): um T no meio de uma parede de 604 cm, a
parede que chega com 242 cm, comprimentos que fecham em modulo.

    D2-like      : duas portas, pilar de 54 cm menos 0,08 mm em volta do no'
    D3 um lado   : janela a 7 cm de um lado do no' e a 26,99 cm do outro
    D3 dois lados: janela a 7 cm dos dois lados (a principal some na faixa)
    impossivel   : portas a 7 e a 20 cm - nem T, nem L, nem L do contato
    normal       : T longe de abertura (resultado anterior preservado)

    python3 -m pytest tests/test_regras_fisicas_de_encontro.py -q
"""
import collections
import contextlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

m, ft, seg, solve = tcr.m, tcr.ft, tcr.seg, tcr.solve
CAT = tcr.sb.CATALOG
NO_T = 302.0
NUM = 14
CORE = os.path.join(os.path.dirname(HERE), "nuvem", "core")


def _fixture(nome):
    lines = [seg(0, 0, 604, 0), seg(NO_T, 0, NO_T, 242)]
    vaos = {
        "D2": [(149.0, NO_T - 26.996, 0.0, 221.0), (NO_T + 26.996, 455.0, 0.0, 221.0)],
        "D3_um_lado": [(149.0, NO_T - 26.99, 80.0, 221.0), (NO_T + 7.0, 455.0, 80.0, 221.0)],
        "D3_dois_lados": [(149.0, NO_T - 7.0, 100.0, 221.0), (NO_T + 7.0, 455.0, 100.0, 221.0)],
        "impossivel": [(149.0, NO_T - 20.0, 0.0, 221.0), (NO_T + 7.0, 455.0, 0.0, 221.0)],
        "normal": [],
    }[nome]
    return lines, [sorted(tuple(ft(v) for v in o) for o in vaos), []]


_CACHE = {}


def _solve(nome, estrategia=None):
    """(res, walls, nodes, openings, preflight, no' T). Cacheado: nunca mutar."""
    chave = (nome, estrategia)
    if chave not in _CACHE:
        lines, ops = _fixture(nome)
        res, walls, nodes, openings = solve(lines, ops, strategy=estrategia, num_courses=NUM)
        pf = m.controlled_beta_preflight(res, walls, openings, CAT, 0.0)
        ni = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"][0]
        _CACHE[chave] = (res, walls, nodes, openings, pf, ni)
    return _CACHE[chave]


def _pecas_do_no(res, ni):
    return dict((ci, sorted((c["logical_code"], str(c.get("placement_reason") or ""))
                            for c in pecas if c.get("node_index") == ni))
                for ci, pecas in sorted(res["course_candidates"].items()))


def _rastreio(res, ni):
    return dict((r["course"], r) for r in res["bond_trace"] if r["node_index"] == ni)


def _sem_invasao(res, walls, openings, pf):
    """Regra 48 intacta: o plano nao invade abertura nem colide - e o que
    sobra depois da materializacao seletiva continua limpo."""
    plano = m.materialization_plan(res, pf)
    conferencia = m.verify_materialization(res, walls, openings, CAT, 0.0,
                                           set((ci, k) for ci, k, _r in plano["skip"]))
    return (not pf.get("opening_violations") and not pf.get("collisions")
            and not conferencia.get("opening_violations") and not conferencia.get("collisions"))


# ----------------------------------------------------------------- interruptor
def test_interruptor_liga_o_caminho_sem_reforco_e_as_chaves_do_modulo_seguem_desligadas():
    assert m.JUNCTION_PHYSICAL_RULES_ENABLED is True
    assert m.BOND_TRACE_ENABLED is True
    res, _w, _n, _o, _pf, _ni = _solve("normal")
    assert res["junction_physical_rules"] is True
    # as regras valem SO' durante o solve (ponto unico) - nada vaza
    assert ws.T_ROOM_PHYSICAL_TOLERANCE is False
    assert ws.T_DEGRADED_L_ROOM_FROM_CONTACT is False
    assert ws.JUNCTION_ROLE_BY_COURSE is False
    assert ws.COMPENSATOR_NODE_PIECE_UNDESIGNATED is False
    assert ws.BOND_TRACE is None and ws.BOND_TRACE_BAND is None


def test_a_paridade_da_secao_72_nao_entra_na_secao_79(monkeypatch):
    """Durante o solve sem reforco a busca de paridade por comprimento (72)
    nunca e' chamada nem ligada; no CHANNEL ela continua ligada (controle)."""
    vistos = []
    original = ws._search_tie_parity_fill_balance

    def espia(*a, **k):
        vistos.append(ws.TIE_PARITY_FILL_BALANCE)
        return original(*a, **k)

    estados = []
    original_all = ws.solve_all_intersections

    def espia_all(*a, **k):
        estados.append(ws.TIE_PARITY_FILL_BALANCE)
        return original_all(*a, **k)

    monkeypatch.setattr(ws, "_search_tie_parity_fill_balance", espia)
    monkeypatch.setattr(ws, "solve_all_intersections", espia_all)
    lines, ops = _fixture("D3_um_lado")
    solve(lines, ops, strategy=None, num_courses=NUM)
    assert estados and not any(estados), estados       # a chave da 72 fica desligada o solve inteiro
    assert vistos == []                                # e a busca nunca roda
    del estados[:]
    solve(lines, ops, strategy=tcr.CHANNEL, num_courses=NUM)
    assert any(estados)                                # controle: no CHANNEL a 72 liga


# ----------------------------------------------------------------- D2-like
def test_d2_t_entre_duas_portas_com_pilar_de_54cm_resolve_com_b54_e_b34():
    res, walls, _n, openings, pf, ni = _solve("D2")
    pecas = _pecas_do_no(res, ni)
    for ci in range(NUM):
        esperado = ("B54", "T_INTERSECTION_MAIN") if ci % 2 == 0 else ("B34", "T_INTERSECTION_INCOMING")
        assert pecas[ci] == [esperado], (ci, pecas[ci])
    assert [v for v in res["missing_required_junction_bond"] if v["node_index"] == ni] == []
    assert all(r["classification"] == m.BOND_TRACE_RESOLVED for r in _rastreio(res, ni).values())
    assert _sem_invasao(res, walls, openings, pf)


def test_d2_antes_da_secao_79_o_b54_perdia_por_submilimetro_e_o_rastreio_diz_por_que():
    """O mesmo no' no motor anterior: o B54 reprova por 0,04 mm (epsilon de
    ponto flutuante no lugar da tolerancia fisica), a escada cai no C09 e o
    no' fica sem amarracao em todas as fiadas da faixa das portas."""
    res, _w, nodes, _o, _pf, ni = _solve("D2", tcr.LEGADO_HISTORICO)
    res = dict(res)   # copia rasa: o resultado cacheado nunca e' mutado
    pecas = _pecas_do_no(res, ni)
    assert all(pecas[ci] == [("C09", "T_INTERSECTION_INCOMING_DEGRADED")] for ci in range(11))
    # o rastreio e' so' observacao: anexado aqui com os gates, sem mudar pecas
    m._attach_junction_gates(res, nodes, _w, _o, CAT, 0.0, NUM, {}, role_by_course=False)
    linhas = _rastreio(res, ni)
    for ci in range(11):
        r = linhas[ci]
        assert r["classification"] == m.BOND_TRACE_NOT_GENERATED, r
        regras = [x["rule"] for x in r["rejected"]]
        assert regras[:3] == ["T_B54_B34", "T_DEGRADED_L_B34", "T_DEGRADED_L_FROM_CONTACT"], regras
        assert "26.996" in r["rejected"][0]["detail"]
        assert r["room_cm"]["main_plus"] == pytest.approx(26.996, abs=1e-3)
        assert r["selected"]["code"] == "C09"


# ----------------------------------------------------------------- D3-like
def test_d3_t_junto_da_janela_de_um_lado_amarra_com_b34_do_contato_nas_fiadas_da_janela():
    res, walls, _n, openings, pf, ni = _solve("D3_um_lado")
    pecas = _pecas_do_no(res, ni)
    faixa_janela = range(4, 11)       # peitoril 80 -> topo 221
    for ci in range(NUM):
        if ci in faixa_janela:
            assert pecas[ci] == [("B34", "T_INTERSECTION_DEGRADED_L")], (ci, pecas[ci])
        else:
            assert pecas[ci] and pecas[ci][0][0] in ws.JUNCTION_BOND_CODES, (ci, pecas[ci])
    assert [v for v in res["missing_required_junction_bond"] if v["node_index"] == ni] == []
    linhas = _rastreio(res, ni)
    for ci in faixa_janela:
        assert linhas[ci]["classification"] == m.BOND_TRACE_RESOLVED
        assert linhas[ci]["room_cm"]["main_plus"] == pytest.approx(7.0, abs=0.01)
    assert _sem_invasao(res, walls, openings, pf)


def test_d3_janela_dos_dois_lados_o_no_nao_existe_na_faixa_e_nao_e_pendencia():
    """A principal some dos dois lados na faixa da janela: nao ha' T ali
    (secao 77) - a parede que chega termina como ponta livre composta. Acima
    e abaixo da janela o T volta sozinho com B54/B34."""
    res, walls, _n, openings, pf, ni = _solve("D3_dois_lados")
    pecas = _pecas_do_no(res, ni)
    linhas = _rastreio(res, ni)
    faixa = [ci for ci in range(NUM) if linhas[ci]["classification"] == m.BOND_TRACE_NOT_REQUIRED]
    assert faixa == list(range(5, 11)), faixa          # peitoril 100 -> topo 221
    assert all(pecas[ci] == [] for ci in faixa)
    assert all(linhas[ci]["classification"] == m.BOND_TRACE_RESOLVED for ci in range(NUM) if ci not in faixa)
    assert res["missing_required_junction_bond"] == []
    nfj = res["junction_role_by_course"]["no_functional_junction"]
    assert sorted(ci for n, ci, _r, _l in nfj if n == ni) == faixa
    assert _sem_invasao(res, walls, openings, pf)


# ----------------------------------------------------------------- impossivel
def test_t_realmente_sem_espaco_fica_nao_resolvido_com_motivo_e_sem_invadir_abertura():
    res, walls, _n, openings, pf, ni = _solve("impossivel")
    faltas = dict((v["course_index"], v) for v in res["missing_required_junction_bond"] if v["node_index"] == ni)
    assert sorted(faltas) == list(range(11))           # faixa das portas
    assert all(v["reason"] == "NO_BOND_PIECE" for v in faltas.values())
    # o compensador que fecha o espaco NUNCA e' designado amarracao (76.1)
    assert res["compensator_as_junction_bond"] == []
    pecas = _pecas_do_no(res, ni)
    assert all(pecas[ci] == [("C09", ws.JUNCTION_UNRESOLVED_FILL_REASON)] for ci in range(11))
    linhas = _rastreio(res, ni)
    for ci in range(11):
        r = linhas[ci]
        assert r["bond_resolved"] is False and r["classification"] == m.BOND_TRACE_NOT_GENERATED
        assert r["rejection_rule"] == "T_DEGRADED_L_FROM_CONTACT"
        assert "7.000 / 20.000" in r["rejection_detail"]
    # a UI e o estado estrutural enxergam a pendencia
    from core import ui_state
    textos = [row["text"] for row in ui_state.review_items(res)]
    assert sum(1 for t in textos if "encontro em T" in t) == 11
    assert _sem_invasao(res, walls, openings, pf)


# ----------------------------------------------------------------- normal / paridade
def test_t_longe_de_abertura_fica_identico_com_e_sem_a_secao_79():
    novo, walls, _n, _o, _pf, ni = _solve("normal")
    velho, walls_v, _n2, _o2, _pf2, _ni2 = _solve("normal", tcr.LEGADO_HISTORICO)
    assert tcr.physical_signature(novo, walls) == tcr.physical_signature(velho, walls_v)
    assert _pecas_do_no(novo, ni) == _pecas_do_no(velho, ni)     # mesma paridade, mesma peca
    assert novo["missing_required_junction_bond"] == []


def test_no_que_ja_amarrava_nao_troca_de_paridade():
    """Fiadas em que o T ja' tinha espaco (abaixo das janelas) guardam a mesma
    peca e a mesma familia com e sem a secao 79."""
    for nome in ("D3_um_lado", "D3_dois_lados"):
        novo = _pecas_do_no(_solve(nome)[0], _solve(nome)[5])
        velho = _pecas_do_no(_solve(nome, tcr.LEGADO_HISTORICO)[0], _solve(nome, tcr.LEGADO_HISTORICO)[5])
        for ci in range(4):
            assert novo[ci] == velho[ci], (nome, ci, novo[ci], velho[ci])


# ----------------------------------------------------------------- canaleta
def test_canaleta_nunca_resolve_o_no():
    """(a) no CHANNEL ha' canaleta de verdade e nenhuma exerce amarracao;
    (b) se a peca que amarra o no' fosse uma canaleta, a auditoria 76.1 deixa
    a fiada SEM amarracao e o gate da regra 75 acusa - o teste falharia se a
    canaleta passasse a contar como amarracao."""
    res, walls, nodes, openings, _pf, ni = _solve("D3_um_lado", tcr.CHANNEL)
    cc = res["course_candidates"]
    assert any(str(c["logical_code"]).startswith("CHANNEL_") for pecas in cc.values() for c in pecas)
    assert orf.channel_as_junction_bond(cc) == []
    # troca a amarracao do no' na fiada 0 por uma canaleta no MESMO lugar
    alvo = [c for c in cc[0] if c.get("node_index") == ni and c["logical_code"] in ws.JUNCTION_BOND_CODES]
    assert alvo, "a fiada 0 do no' precisa ter a peca de amarracao"
    canal = dict(alvo[0], logical_code=orf.CHANNEL_U_39)
    copia = dict(res)
    copia["course_candidates"] = dict(cc)
    copia["course_candidates"][0] = [canal if c is alvo[0] else c for c in cc[0]]
    assert orf.channel_as_junction_bond(copia["course_candidates"])
    audit = m._junction_bond_audit_final(copia, nodes, walls, openings, CAT, 0.0, NUM, None)
    assert any(v["node_index"] == ni and v["course_index"] == 0 for v in audit["missing"])
    assert not any(v["node_index"] == ni and v["course_index"] == 0 for v in audit["resolved"])


def test_channel_continua_resolvendo_os_mesmos_nos():
    for nome in ("D2", "D3_um_lado"):
        res, _w, _n, _o, _pf, ni = _solve(nome, tcr.CHANNEL)
        assert [v for v in res["missing_required_junction_bond"] if v["node_index"] == ni] == [], nome


# ----------------------------------------------------------------- rastreio: as duas falhas
def test_rastreio_distingue_nao_gerado_de_gerado_e_rejeitado():
    """BOND_CANDIDATE_GENERATED_BUT_REJECTED: (a) a peca gerada nao esta' no
    resultado final; (b) a regra 48 pula a amarracao na materializacao."""
    res, walls, nodes, openings, _pf, ni = _solve("D2")
    copia = dict(res)
    copia["course_candidates"] = dict((ci, [c for c in pecas if not (c.get("node_index") == ni and ci == 0)])
                                      for ci, pecas in res["course_candidates"].items())
    audit = m._junction_bond_audit_final(copia, nodes, walls, openings, CAT, 0.0, NUM, None)
    linhas = dict((r["course"], r) for r in m._bond_trace_from_result(copia, audit, nodes) if r["node_index"] == ni)
    assert linhas[0]["classification"] == m.BOND_TRACE_REJECTED
    assert linhas[0]["rejection_rule"] == "DROPPED_AFTER_NODE_STEP"
    assert linhas[1]["classification"] == m.BOND_TRACE_RESOLVED
    rastreio = [dict(r) for r in res["bond_trace"]]
    m._bond_trace_apply_materialization(rastreio, [{"node_index": ni, "course_index": 2, "rejected_rule": "OPENING",
                                                    "message": "amarracao NAO resolvida: invadia a abertura"}])
    linha = [r for r in rastreio if r["node_index"] == ni and r["course"] == 2][0]
    assert linha["classification"] == m.BOND_TRACE_REJECTED and linha["rejection_rule"] == "REGRA_48_OPENING"
    assert linha["bond_resolved"] is False


def test_rastreio_casa_a_peca_por_tolerancia_e_nao_por_arredondamento():
    """Achado da revisao: com chave arredondada (2 casas, depois 1) uma peca
    presente parecia ausente. O casamento e' por codigo + origem a <= 0,05 cm."""
    res, walls, nodes, openings, _pf, ni = _solve("D2")
    copia = dict(res)
    copia["bond_trace_steps"] = []
    for rec in res["bond_trace_steps"]:
        rec = dict(rec)
        if rec["node_index"] == ni:
            rec["generated"] = [dict(g, origin_cm=[g["origin_cm"][0] + 0.04, g["origin_cm"][1] - 0.04])
                                for g in rec["generated"]]
        copia["bond_trace_steps"].append(rec)
    audit = m._junction_bond_audit_final(copia, nodes, walls, openings, CAT, 0.0, NUM, None)
    linhas = [r for r in m._bond_trace_from_result(copia, audit, nodes) if r["node_index"] == ni]
    assert linhas and all(r["classification"] == m.BOND_TRACE_RESOLVED for r in linhas)
    for r in linhas:
        # em cada fiada exatamente UMA peca gerada e' desta familia e esta' la'
        assert sorted(str(c["accepted"]) for c in r["candidates"]) == ["None", "True"], r["candidates"]


def test_rastreio_tem_os_campos_pedidos_e_vai_no_relatorio():
    res, _w, _n, _o, _pf, ni = _solve("impossivel")
    r = _rastreio(res, ni)[0]
    for chave in ("node_index", "node_kind", "course", "main_wall_idx", "arriving_wall_idx", "room_cm",
                  "candidates", "rejected", "selected", "bond_resolved", "classification",
                  "rejection_rule", "rejection_detail"):
        assert chave in r, chave
    for cand in r["candidates"]:
        for chave in ("family", "code", "origin_cm", "rotation_deg", "placement_reason", "accepted"):
            assert chave in cand, chave
    texto = m._format_block_solve_report(res, CAT)
    texto = texto[0] if isinstance(texto, tuple) else texto
    assert "AMARRACAO POR NO'/FIADA (bond_trace, secao 79)" in texto
    assert texto.count("BOND_TRACE node={} kind=T_INTERSECTION".format(ni)) == 11


# ----------------------------------------------------------------- ausencia de hardcode
def test_nenhuma_regra_cita_id_no_projeto_ou_coordenada():
    import io as _io
    import tokenize
    proibidos = [re.compile(r"\b8(079|284)\d{3}\b"), re.compile(r"node_index\s*==\s*\d"),
                 re.compile(r"wall_idx\s*==\s*\d"), re.compile(r"butanta", re.I)]
    for nome in ("wall_modeling.py", os.path.join("engine", "wall_stepper.py")):
        partes = []
        with _io.open(os.path.join(CORE, nome), encoding="utf-8") as handle:
            for tok in tokenize.generate_tokens(handle.readline):
                if tok.type in (tokenize.NAME, tokenize.NUMBER, tokenize.OP):
                    partes.append(tok.string)
        codigo = " ".join(partes)
        for padrao in proibidos:
            achado = padrao.search(codigo)
            assert achado is None, (nome, padrao.pattern, achado.group(0) if achado else None)


# ----------------------------------------------------------------- achados da revisao adversarial
def test_amarracao_pulada_pela_regra_48_aparece_rejeitada_no_rastreio_e_no_relatorio():
    """A porta sobe acima do nivel da amarracao (topo 241,4): o B54 da fiada 12
    invade o vao e a regra 48 o pula. No calculo (antes do relatorio), o rastreio
    ja' diz GENERATED_BUT_REJECTED com a regra - nunca BOND_RESOLVED."""
    lines = [seg(0, 0, 604, 0), seg(NO_T, 0, NO_T, 242)]
    ops = [[tuple(ft(v) for v in (NO_T + 7.0, 455.0, 0.0, 241.4))], []]
    res, walls, nodes, openings = solve(lines, ops, strategy=None, num_courses=NUM)
    ni = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"][0]
    handler = m._PostCreationEventHandler()
    handler.walls_to_create, handler.openings_per_wall = walls, openings
    handler.catalog = dict(CAT)
    handler.base_z_abs = 0.0
    handler.wall_height_ft = ft(280.0)
    handler._num_courses_for_wall_height = lambda *a, **k: (NUM, None)
    handler.selected_level = None
    handler._solve_building_blocks_all_courses = lambda *a, **k: res
    handler._save_modulation_state_cache = lambda: None
    handler._execute_solve()
    pulada = handler.solve_result["materialization"]["unresolved_bonds"]
    assert [(u["node_index"], u["course_index"]) for u in pulada] == [(ni, 12)], pulada
    linha = [r for r in handler.solve_result["bond_trace"] if r["node_index"] == ni and r["course"] == 12][0]
    assert linha["classification"] == m.BOND_TRACE_REJECTED and linha["bond_resolved"] is False
    assert linha["rejection_rule"].startswith("REGRA_48_")
    texto = m._format_block_solve_report(handler.solve_result, CAT)
    texto = texto[0] if isinstance(texto, tuple) else texto
    assert "BOND_TRACE node={} kind=T_INTERSECTION course=12 classification={}".format(
        ni, m.BOND_TRACE_REJECTED) in texto


def test_papel_por_fiada_da_auditoria_segue_a_chave_do_solve_sem_reforco(monkeypatch):
    """Sem reforco o solve usa a secao 77 pela chave da secao 79; a auditoria
    tem de usar a MESMA - desligar a chave do CHANNEL nao pode criar MISSING
    falso nas fiadas sem encontro funcional."""
    monkeypatch.setattr(m, "CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED", False)
    lines, ops = _fixture("D3_dois_lados")
    res, _w, nodes, _o = solve(lines, ops, strategy=None, num_courses=NUM)
    assert res["missing_required_junction_bond"] == []
    assert res["junction_role_by_course"]["enabled"] is True
    ni = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"][0]
    faixa = [r["course"] for r in res["bond_trace"] if r["node_index"] == ni
             and r["classification"] == m.BOND_TRACE_NOT_REQUIRED]
    assert faixa == list(range(5, 11))


def test_detalhe_do_rastreio_culpa_o_lado_que_falta():
    """Parede que chega com 25 cm: quem nao comporta o B34 e' a CHEGADA - o
    detalhe diz isso (e nao culpa a principal, que tem espaco de sobra)."""
    lines = [seg(0, 0, 604, 0), seg(NO_T, 0, NO_T, 25)]
    res, _w, nodes, _o = solve(lines, [[], []], strategy=None, num_courses=NUM)
    ni = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"][0]
    passos = [s for rec in res["bond_trace_steps"] if rec["node_index"] == ni for s in rec["steps"]]
    t = [s for s in passos if s["rule"] == "T_B54_B34"][0]
    assert t["passed"] is False and "chegada" in t["detail"] and "principal" not in t["detail"]
    l = [s for s in passos if s["rule"] == "T_DEGRADED_L_B34"][0]
    assert "chegada" in l["detail"] and "principal" not in l["detail"]
    # a D1 nem e' tentada sem espaco na chegada (nao ha' passo falso dela)
    assert not [s for s in passos if s["rule"] == "T_DEGRADED_L_FROM_CONTACT"]


def test_rastreio_e_da_passada_que_gerou_o_resultado():
    """Cada passada do solver leva o PROPRIO rastreio; nada de uma passada
    vaza para outra e o contexto global volta ao que era."""
    lines, ops = _fixture("D2")
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jmap)
    antes = ws.BOND_TRACE
    ws.BOND_TRACE = {}
    try:
        a = m._solve_building_blocks_all_courses_pass(nodes, walls, e2n, ops, CAT, 0.0, NUM)
        b = m._solve_building_blocks_all_courses_pass(nodes, walls, e2n, [[], []], CAT, 0.0, NUM)
    finally:
        externo, ws.BOND_TRACE = ws.BOND_TRACE, antes
    assert a["bond_trace_steps"] and b["bond_trace_steps"]
    assert a["bond_trace_steps"] is not b["bond_trace_steps"]
    # a passada com as portas tem o T degradado (C09); a sem portas, o T cheio (B54)
    codigos_a = set(g["code"] for rec in a["bond_trace_steps"] if rec["kind"] == "T_INTERSECTION"
                    for g in rec["generated"])
    codigos_b = set(g["code"] for rec in b["bond_trace_steps"] if rec["kind"] == "T_INTERSECTION"
                    for g in rec["generated"])
    assert "B54" in codigos_b and codigos_a != codigos_b
    assert externo, "o coletor externo continua recebendo os registros"


def test_familia_do_rastreio_bate_com_a_fiada_das_pecas_presentes():
    """Em planta com reparo de papel de braco (tentativas descartadas), toda
    peca marcada como presente numa fiada e' da familia FISICA daquela fiada."""
    lines = [seg(0, 0, 400, 0), seg(0, 0, 0, 300), seg(70, 0, 70, 300), seg(400, 0, 400, 300)]
    res, _w, _n, _o = solve(lines, [[], [], [], []], strategy=None, num_courses=6)
    vistos = 0
    for r in res["bond_trace"]:
        for c in r["candidates"]:
            if c["accepted"] is True:
                vistos += 1
                assert c["family"] == ("A" if r["course"] % 2 == 0 else "B"), (r["node_index"], r["course"], c)
    assert vistos > 0


def test_banda_de_uma_so_fiada_nao_inventa_peca_descartada():
    """Achado da revisao: numa banda de UMA fiada (janela 80..100 cria a banda
    [4]) a peca da OUTRA familia nao aparece na banda - isso nao e' descarte.
    O canto sem amarracao nessa fiada e' NAO GERADO, nunca DROPPED."""
    lines = [seg(0, 0, 300, 0), seg(0, 0, 0, 300)]
    ops = [[tuple(ft(v) for v in (20.0, 100.0, 0.0, 221.0))], [tuple(ft(v) for v in (150.0, 250.0, 80.0, 100.0))]]
    res, _w, nodes, _o = solve(lines, ops, strategy=None, num_courses=NUM)
    assert [4] in [b["course_indices"] for b in res["bands"]]
    ni = [i for i, n in enumerate(nodes) if n.get("kind") == "L_CORNER"][0]
    linha = [r for r in res["bond_trace"] if r["node_index"] == ni and r["course"] == 4][0]
    assert linha["band"] == [4]
    assert linha["classification"] == m.BOND_TRACE_NOT_GENERATED, linha
    assert sorted(str(c["accepted"]) for c in linha["candidates"]) == ["None", "True"]
    assert not [r for r in res["bond_trace"] if r["rejection_rule"] == "DROPPED_AFTER_NODE_STEP"]
