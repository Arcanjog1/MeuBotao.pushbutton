# -*- coding: utf-8 -*-
"""Secao 81 (D9/D10/D12/D13, 2026-09-25): regras GERAIS de qualidade de composicao.

A 71 (quantidade de compensadores no desempate) e o arranjo das corridas 60-65
(reordenacao, composicao de mesmo comprimento, orientacao exata e conjunta, reparo
movel, passes) valem em QUALQUER estrategia - no NONE com a mesma aceitacao exata
por parede do CHANNEL. A 68 (melhor composicao do reparo), a 58.2 e a 72 (paridade
dos T) continuam SO' no CHANNEL.

Fixtures sinteticas (nenhum ID do projeto): parede livre de 199 cm (exata), de
204 cm (1 compensador inevitavel por fiada), U de 101 cm entre dois L (dois
compensadores evitaveis) e T com porta a 35 cm da peca de no'.

    python3 -m pytest tests/test_regras_gerais_composicao.py -q
"""
import collections
import inspect
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest  # noqa: E402
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402
from core.engine import b34_run_arrangement as runs_mod  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
COMP = ("C04", "C09")


def _livre(comprimento):
    return [seg(0, 0, comprimento, 0)], [[]]


def _u(largura):
    return ([seg(0, 0, largura, 0), seg(0, 0, 0, -242.0), seg(largura, 0, largura, -242.0)], [[], [], []])


def _t_porta():
    """T modular (principal 604 cm, chegada em t=302) e porta 344-435: 15 cm entre a
    peca de no' e a jamba; do outro lado da porta, corrida livre ate' a ponta."""
    return [seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[(ft(344.0), ft(435.0), ft(0), ft(221))], []]


FIXTURES = {"livre_199": lambda: _livre(199.0), "livre_204": lambda: _livre(204.0), "u_101": lambda: _u(101.0),
            "t_porta": _t_porta}
_CACHE = {}


def _solve(nome, geral=True, estrategia=None, reverse=False):
    chave = (nome, geral, estrategia, reverse)
    if chave not in _CACHE:
        antes = m.GENERAL_COMPOSITION_QUALITY_ENABLED
        m.GENERAL_COMPOSITION_QUALITY_ENABLED = geral
        try:
            lines, ops = FIXTURES[nome]()
            _CACHE[chave] = tcr.solve(lines, ops, strategy=estrategia, reverse=reverse)
        finally:
            m.GENERAL_COMPOSITION_QUALITY_ENABLED = antes
    return _CACHE[chave]


def _fiada(res, walls, wi, ci):
    return [(r["cand"]["logical_code"], round(r["lo"], 1), round(r["hi"], 1), r["along"])
            for r in orf._wall_strip_pieces(res["course_candidates"][ci], walls, wi)]


def _codigos(res):
    return collections.Counter(c["logical_code"] for v in res["course_candidates"].values() for c in v)


def _juntas_continuas(res, walls, wi, minimo=3):
    """(t da junta, fiadas) com a mesma junta em `minimo`+ fiadas seguidas."""
    juntas = {}
    for ci in sorted(res["course_candidates"]):
        rows = [r for r in orf._wall_strip_pieces(res["course_candidates"][ci], walls, wi) if r["along"]]
        juntas[ci] = set(round((a["hi"] + b["lo"]) / 2.0) for a, b in zip(rows, rows[1:]) if 0 <= b["lo"] - a["hi"] < 2.5)
    out = set()
    for j in set().union(*juntas.values()):
        corrida = 0
        for ci in sorted(juntas):
            corrida = corrida + 1 if j in juntas[ci] else 0
            if corrida >= minimo:
                out.add(j)
    return out


def _colunas_compensador(res, walls, wi, minimo=4):
    cols = collections.Counter()
    for ci in res["course_candidates"]:
        for code, lo, hi, _al in _fiada(res, walls, wi, ci):
            if code in COMP:
                cols[(code, round(lo))] += 1
    return sum(1 for v in cols.values() if v >= minimo)


# ------------------------------------------------------------------ composicao
def test_composicao_exata_simples_so_b39_e_igual_com_e_sem_as_regras():
    com, walls, _n, _o = _solve("livre_199", True)
    sem, walls0, _n0, _o0 = _solve("livre_199", False)
    assert tcr.physical_signature(com, walls) == tcr.physical_signature(sem, walls0)
    cod = _codigos(com)
    assert not (set(cod) & set(COMP)) and cod["B34"] == 0 and cod["B39"] > 0


def test_compensador_inevitavel_continua_e_b34_desnecessario_vira_b39():
    """204 cm: resto 5 cm - um compensador por fiada e' inevitavel; a composicao de
    mesmo comprimento (61) troca `C09 + ... + B34` por `C04 + ... + B39`."""
    com, walls, _n, _o = _solve("livre_204", True)
    sem, walls0, _n0, _o0 = _solve("livre_204", False)
    for res, w in ((com, walls), (sem, walls0)):
        for ci in res["course_candidates"]:
            assert sum(1 for c, _a, _b, _al in _fiada(res, w, 0, ci) if c in COMP) == 1
    assert _codigos(com)["B34"] < _codigos(sem)["B34"]
    assert _codigos(com)["B39"] > _codigos(sem)["B39"]
    assert sum(_codigos(com)[c] for c in COMP) == sum(_codigos(sem)[c] for c in COMP)


def test_dois_compensadores_evitaveis_viram_meio_bloco():
    """U de 101 cm entre dois L: `C09 B39 C09 C04` -> `B19 B39 C04` (preferencia do
    B19 sobre dois C09, via composicao de mesmo comprimento)."""
    com, walls, _n, _o = _solve("u_101", True)
    sem, walls0, _n0, _o0 = _solve("u_101", False)
    assert _codigos(sem)["C09"] > 0 and _codigos(com)["C09"] == 0
    assert _codigos(com)["B19"] > _codigos(sem)["B19"]
    assert sum(_codigos(com)[c] for c in COMP) < sum(_codigos(sem)[c] for c in COMP)
    for ci in com["course_candidates"]:
        fiada = [c for c, _a, _b, al in _fiada(com, walls, 0, ci) if al]
        assert not any(a in COMP and b in COMP for a, b in zip(fiada, fiada[1:]))


def test_b34_necessario_permanece():
    """Peca de amarracao B34 dos cantos e as B34 que fecham trecho sem outra
    composicao continuam."""
    com, walls, _n, _o = _solve("u_101", True)
    for ci in com["course_candidates"]:
        fiada = _fiada(com, walls, 0, ci)
        assert any(c == "B34" for c, _a, _b, _al in fiada)


def test_regiao_proxima_de_abertura_troca_compensadores_por_blocos_e_respeita_a_jamba():
    com, walls, _n, openings = _solve("t_porta", True)
    sem, walls0, _n0, _o0 = _solve("t_porta", False)
    lado = lambda res, w, ci: [(c, a) for c, a, b, al in _fiada(res, w, 0, ci) if 435 - 0.5 <= a < 500]
    assert any(c in COMP for c, _a in lado(sem, walls0, 0)) and not any(c in COMP for c, _a in lado(com, walls, 0))
    for ci in com["course_candidates"]:
        if ci > 10:
            continue
        # a face da jamba nunca se move: sempre ha' peca encostada nos dois lados da porta
        fiada = _fiada(com, walls, 0, ci)
        assert any(abs(b - 344.0) < 1.01 for _c, _a, b, _al in fiada)
        assert any(abs(a - 435.0) < 1.01 for _c, a, _b, _al in fiada)
    pf = m.controlled_beta_preflight(com, walls, openings, tcr.sb.CATALOG, 0.0)
    assert not pf.get("opening_violations") and not m.materialization_plan(com, pf)["skip"]


def test_regiao_proxima_ao_t_amarracao_preservada():
    """As regras gerais nao mexem em peca de no': o rastreio de amarracao e as pecas de
    no' sao identicos com e sem elas; a faixa curta entre o no' e a jamba nao vira
    composicao 'limpa' a' custa de junta (a 68 continua so' no CHANNEL)."""
    com, walls, nodes, _o = _solve("t_porta", True)
    sem, walls0, _n0, _o0 = _solve("t_porta", False)
    chave = lambda res: sorted((r["node_index"], r["course"], r["classification"], (r.get("selected") or {}).get("code"))
                               for r in res["bond_trace"])
    assert chave(com) == chave(sem)
    no = lambda res: sorted((ci, c["logical_code"], round(c["origin_world"].X, 4), round(c["origin_world"].Y, 4))
                            for ci, v in res["course_candidates"].items() for c in v if c.get("node_index") is not None)
    assert no(com) == no(sem)
    assert com["missing_required_junction_bond"] == [] and com["channel_as_junction_bond"] == []
    faixa = lambda res, w, ci: [c for c, a, b, al in _fiada(res, w, 0, ci) if 329 < a < 344]
    assert [faixa(com, walls, ci) for ci in range(10)] == [faixa(sem, walls0, ci) for ci in range(10)]


# ------------------------------------------------------------------ prisma
@pytest.mark.parametrize("nome", sorted(FIXTURES))
def test_prisma_nenhuma_junta_continua_nova(nome):
    com, walls, _n, _o = _solve(nome, True)
    sem, walls0, _n0, _o0 = _solve(nome, False)
    for wi in range(len(walls)):
        assert _juntas_continuas(com, walls, wi) <= _juntas_continuas(sem, walls0, wi), (nome, wi)


def _parede_da_ponta_do_t(ordem_impar):
    """Ponta de parede junto de um T (padrao medido no TP1, 49,5 cm do no'): fiada par
    `B39 B39 B39`, fiada impar `B39` + `ordem_impar`, as duas terminando na mesma face."""
    from core.engine import small_void_alignment as sva
    p0, direcao = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    par = [("B39", 10, 49), ("B39", 50, 89), ("B39", 90, 129)]
    impar = [("B39", 15, 54)] + ordem_impar
    cc = {}
    for ci in range(6):
        cc[ci] = m._place_pier_layout(par if ci % 2 == 0 else impar, tcr.sb.CATALOG, p0, direcao, ci, 0)
    sva.orient_small_voids(cc, tcr.sb.CATALOG)
    paredes = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    return runs_mod._collect_rows(cc, paredes)[0], paredes


@pytest.mark.parametrize("guarda", [True, False])
def test_guarda_de_identidade_barra_junta_a_prumo_nova(guarda):
    """SECAO 81.1: trocar `B39 B34` por `B34 B39` na ponta poe a junta da fiada impar
    em cima da junta da par (89/90) - junta a prumo nova. Com a guarda a troca e'
    reconhecida como criadora de junta; sem ela (o CHANNEL historico) nao."""
    rows, paredes = _parede_da_ponta_do_t([("B39", 55, 94), ("B34", 95, 129)])
    parede = runs_mod._Wall(0, rows, paredes, [[]], tcr.sb.CATALOG, 1.5, joint_identity_guard=guarda)
    fam = parede.course_fam[1]
    corrida = runs_mod._runs(parede.fam[fam])[0]
    janela = parede._window(fam, corrida)
    antes = parede._coincident_positions(fam, janela)
    assert not parede._creates_joint(fam, janela, antes)  # a propria ordem nunca e' "nova"
    parede._apply(fam, corrida, ["B39", "B34", "B39"], [1, 1, 1])
    depois = parede._coincident_positions(fam, janela)
    assert len(depois) > len(antes)
    assert parede._creates_joint(fam, janela, antes) is guarda


@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_aceitacao_por_parede_nunca_cria_encontro_faltando(monkeypatch, estrategia):
    """Estrutura antes de composicao: a auditoria FINAL de encontro (76.1/77) entra na
    aceitacao exata por parede (compartilhada pelos dois caminhos). Fixture da D3 (janela
    a 7 cm dos dois lados do T): sem ela o arranjo recompoe a ponta livre da parede que
    chega e deixa 3 fiadas FREE_END_NOT_COMPOSED - no NONE com a secao 81 e tambem no
    CHANNEL da main; com ela, nenhuma."""
    import test_regras_fisicas_de_encontro as fis
    lines, ops = fis._fixture("D3_dois_lados")
    com, _w, _n, _o = tcr.solve(lines, ops, strategy=estrategia, num_courses=fis.NUM)
    assert com["missing_required_junction_bond"] == []
    dentro = {"v": False}
    real_audit, real_validator = m._junction_bond_audit_final, m._channel_wall_validator

    def validador(*a, **k):
        v = real_validator(*a, **k)

        def envolto(*aa, **kk):
            dentro["v"] = True
            try:
                return v(*aa, **kk)
            finally:
                dentro["v"] = False
        return envolto

    monkeypatch.setattr(m, "_channel_wall_validator", validador)
    monkeypatch.setattr(m, "_junction_bond_audit_final",
                        lambda *a, **k: {"missing": []} if dentro["v"] else real_audit(*a, **k))
    sem, _w2, _n2, _o2 = tcr.solve(lines, ops, strategy=estrategia, num_courses=fis.NUM)
    assert sorted(x["reason"] for x in sem["missing_required_junction_bond"]) == ["FREE_END_NOT_COMPOSED"] * 3


def test_none_usa_a_guarda_de_junta_e_o_channel_nao(monkeypatch):
    """A guarda de identidade de junta e' da secao 81 (caminho geral); o CHANNEL
    continua com a aceitacao historica (identico a' main)."""
    guardas = {}
    real_arrange = runs_mod.arrange_b34_runs

    def espia(*a, **k):
        guardas.setdefault(estrategia[0], []).append(bool(k.get("joint_identity_guard")))
        return real_arrange(*a, **k)

    monkeypatch.setattr(runs_mod, "arrange_b34_runs", espia)
    lines, ops = _t_porta()
    for estrategia in ([None], [tcr.CHANNEL]):
        tcr.solve(lines, ops, strategy=estrategia[0])
    assert guardas[None] and all(guardas[None])
    assert guardas[tcr.CHANNEL] and not any(guardas[tcr.CHANNEL])


def test_ponta_de_trecho_sem_compensador_longo_na_extremidade():
    """Ponta livre (204 cm): sem as regras gerais o compensador inevitavel fica como
    peca extrema LONGA (C09 na ponta - secao 58) nas fiadas impares; com elas a
    composicao de mesmo comprimento o troca por C04 e nenhuma ponta fica com C09."""
    extremos = {}
    for geral in (True, False):
        res, walls, _n, _o = _solve("livre_204", geral)
        extremos[geral] = 0
        for ci in res["course_candidates"]:
            fiada = [x for x in _fiada(res, walls, 0, ci) if x[3]]
            extremos[geral] += (fiada[0][0] == "C09") + (fiada[-1][0] == "C09")
    assert extremos[False] > 0 and extremos[True] == 0, extremos


def test_coluna_vertical_de_compensador_junto_a_jamba_some():
    com, walls, _n, _o = _solve("t_porta", True)
    sem, walls0, _n0, _o0 = _solve("t_porta", False)
    assert _colunas_compensador(com, walls, 0) < _colunas_compensador(sem, walls0, 0)


def test_espelhamento_mantem_as_contagens():
    direto, _w, _n, _o = _solve("u_101", True)
    invertido, _w2, _n2, _o2 = _solve("u_101", True, reverse=True)
    assert _codigos(direto) == _codigos(invertido)


# ------------------------------------------------------------------ NONE x CHANNEL
@pytest.mark.parametrize("nome", ["u_101", "t_porta"])
def test_channel_nao_muda_com_a_chave_geral(nome):
    """O CHANNEL ja' tinha 71 e 60-65: a chave geral nao muda nenhuma peca dele."""
    com, walls, _n, _o = _solve(nome, True, estrategia=tcr.CHANNEL)
    sem, walls0, _n0, _o0 = _solve(nome, False, estrategia=tcr.CHANNEL)
    assert tcr.physical_signature(com, walls) == tcr.physical_signature(sem, walls0)


def test_none_liga_so_71_e_60_65_nunca_68_58_2_ou_72(monkeypatch):
    estados, arranjos, chamadas72 = [], [], []
    core = m._solve_building_blocks_all_courses_core

    def espia_core(*a, **k):
        estados.append({"71": ws.COMPENSATOR_COUNT_IN_TIEBREAK, "68": ws.OPENING_REPAIR_PREFER_CLEAN_ACTIVE,
                        "72": ws.TIE_PARITY_FILL_BALANCE, "58.2": ws.CORNER_DEGRADED_PREFERS_TIE_BLOCK})
        return core(*a, **k)

    real_arrange = runs_mod.arrange_b34_runs

    def espia_arranjo(*a, **k):
        arranjos.append((runs_mod.B34_RUN_COMPOSITION_ENABLED, runs_mod.B34_ORIENTATION_DP_ENABLED,
                         runs_mod.NEIGHBOUR_FLIPS_ENABLED, runs_mod.B34_RUN_OPENING_REPAIR_MOVABLE,
                         k.get("validate_wall") is not None, bool(k.get("joint_identity_guard"))))
        return real_arrange(*a, **k)

    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_core", espia_core)
    monkeypatch.setattr(runs_mod, "arrange_b34_runs", espia_arranjo)
    monkeypatch.setattr(ws, "_search_tie_parity_fill_balance", lambda *a, **k: chamadas72.append(1) or a[0])
    lines, ops = _t_porta()
    res, _w, _n, _o = tcr.solve(lines, ops, strategy=None)
    assert estados and all(e["71"] and not e["68"] and not e["72"] and not e["58.2"] for e in estados), estados
    assert arranjos and all(all(x) for x in arranjos)            # 60-65 com aceitacao exata + guarda de junta
    assert chamadas72 == []                                      # 72 nunca no NONE
    assert res["general_composition_quality"]["enabled"] is True
    assert "channel_tie_parity_trials" not in res


def test_desligar_a_chave_devolve_o_comportamento_anterior(monkeypatch):
    """Chave desligada: no NONE nenhum arranjo 60-65 roda e a 71 fica desligada."""
    chamadas, tiebreak = [], []
    real_arrange = runs_mod.arrange_b34_runs
    monkeypatch.setattr(runs_mod, "arrange_b34_runs", lambda *a, **k: chamadas.append(1) or real_arrange(*a, **k))
    core = m._solve_building_blocks_all_courses_core
    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_core",
                        lambda *a, **k: tiebreak.append(ws.COMPENSATOR_COUNT_IN_TIEBREAK) or core(*a, **k))
    monkeypatch.setattr(m, "GENERAL_COMPOSITION_QUALITY_ENABLED", False)
    lines, ops = _t_porta()
    res, _w, _n, _o = tcr.solve(lines, ops, strategy=None)
    assert chamadas == [] and tiebreak and not any(tiebreak)
    assert "general_composition_quality" not in res


def test_verga_e_contraverga_nao_mudam_de_papel():
    """A verga/contraverga (secao 80) continua com o mesmo status com e sem as regras
    gerais; canaleta nunca entra nas corridas do arranjo nem vira amarracao."""
    lines = [seg(0, 0, 600, 0)]
    ops = [[(ft(200), ft(300), ft(0), ft(221)), (ft(400), ft(520), ft(100), ft(221))]]
    resultados = []
    for geral in (True, False):
        antes = m.GENERAL_COMPOSITION_QUALITY_ENABLED
        m.GENERAL_COMPOSITION_QUALITY_ENABLED = geral
        try:
            resultados.append(tcr.solve(lines, ops, strategy=None))
        finally:
            m.GENERAL_COMPOSITION_QUALITY_ENABLED = antes
    status = lambda res: sorted((r["opening_index"], r["lintel_status"], r["lintel_course"], r["sill_status"],
                                 r["sill_course"]) for r in res[0]["opening_structural_trace"])
    assert status(resultados[0]) == status(resultados[1])
    assert resultados[0][0]["channel_as_junction_bond"] == []
    assert resultados[0][0]["opening_reinforcement"]["validation"]["counts"].get("OPENING_INVASION", 0) == 0


# ------------------------------------------------------------------ sem hardcode
def test_regras_gerais_sem_identificador_de_projeto():
    fontes = "\n".join(inspect.getsource(f) for f in (m._general_composition_arrangement,
                                                      m._general_composition_reaudit))
    assert "8284" not in fontes and "BUTANT" not in fontes.upper()
    assert not re.search(r"(node_index|wall_idx|opening_index)\s*==\s*\d", fontes)
