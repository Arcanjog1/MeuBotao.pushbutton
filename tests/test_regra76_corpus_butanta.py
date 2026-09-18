# -*- coding: utf-8 -*-
"""REGRA 76 / 76.1 sobre o corpus versionado do BUTANTA: compensador nunca
exerce funcao de amarracao, e no' sem amarracao valida fica NAO RESOLVIDO.

Estado medido (2026-09-18), fluxo CHANNEL:
  * ANTES da regra 76: 11 compensadores (todos C09) designados peca do no' -
    nos T 22/28/30 (fiadas 5,7,9 / 5,7,9 / 5,7) e cantos L 47/48 (fiadas 2,4 / 3).
  * A correcao D1 (passo "degrada para L" do T medido a partir do CONTATO onde o
    B34 comeca) resolve os nos 22 e 30 com B34 real nas duas familias.
  * Nos 28/47/48 nenhuma peca de amarracao aprovada cabe (janela a 19,5 cm da
    face externa do canto; pilar de 14 cm entre duas janelas) e o usuario
    recusou recuo, B19, outro braco e mover a janela. Regra 76.1: o C09 que
    fecha o espaco deixa de ser DESIGNADO amarracao (JUNCTION_UNRESOLVED_FILL) e
    as 6 fiadas ficam em MISSING_REQUIRED_JUNCTION_BOND para revisao humana -
    classificadas pela GEOMETRIA (nenhum B34/B54 cobrindo a regiao do no'),
    nunca por id. As pecas sao as mesmas: so' a classificacao muda.
  * No' 46 fiadas 11-16: passagem livre continua (decisao de 2026-09-14) - o
    encontro nao existe ali acima das portas; nao e' amarracao faltante.

    python3 -m pytest tests/test_regra76_corpus_butanta.py -q
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import s74_corpus as S  # noqa: E402

pytestmark = pytest.mark.slow

NAO_RESOLVIDOS = [(28, 5), (28, 7), (28, 9), (47, 2), (47, 4), (48, 3)]
RESOLVIDOS_PELA_D1 = [(22, 5), (22, 7), (22, 9), (30, 5), (30, 7)]


def _solve(nome):
    cache = _solve.__dict__.setdefault("cache", {})
    if nome not in cache:
        geo = S.geometry()
        if nome == "pos_micro":
            geo = S.with_opening_variant(geo, "post_micro_adjustment_s66")
        cache[nome] = (geo,) + S.solve_on_fresh_context(geo, True)
    return cache[nome]


@pytest.mark.parametrize("nome", ["original", "pos_micro"])
def test_nenhum_compensador_e_designado_amarracao(nome):
    _geo, _ctx, res = _solve(nome)
    assert res["compensator_as_junction_bond"] == []


@pytest.mark.parametrize("nome", ["original", "pos_micro"])
def test_os_nos_sem_amarracao_valida_sao_exatamente_os_6_conhecidos(nome):
    _geo, ctx, res = _solve(nome)
    falta = res["missing_required_junction_bond"]
    assert sorted((f["node_index"], f["course_index"]) for f in falta) == NAO_RESOLVIDOS
    for f in falta:
        assert f["classification"] == "MISSING_REQUIRED_JUNCTION_BOND"
        assert f["review"] == "HUMAN_REVIEW"
        kind = ctx["nodes"][f["node_index"]]["kind"]
        assert f["node_kind"] == kind
        # nenhum B34/B54 cobre a regiao inteira; o C09 que fecha o espaco esta' la',
        # NAO designado amarracao
        assert not any(o["logical_code"] in ("B34", "B54") and o["coverage"] > 0.99 for o in f["occupants"])
        c09 = [o for o in f["occupants"] if o["logical_code"] == "C09"
               and o["placement_reason"] == "JUNCTION_UNRESOLVED_FILL"]
        assert len(c09) == 1 and 0.6 < c09[0]["coverage"] < 0.7, f["occupants"]
        assert f["reason"] == ("BOND_PIECE_PARTIAL" if kind == "T_INTERSECTION" else "NO_BOND_PIECE")


@pytest.mark.parametrize("nome", ["original", "pos_micro"])
def test_o_no_46_acima_das_portas_nao_e_encontro(nome):
    _geo, _ctx, res = _solve(nome)
    a = res["junction_bond_audit"]
    fora = sorted((x["node_index"], x["course_index"]) for x in a["not_required"])
    assert fora == [(46, c) for c in range(11, 17)]
    assert a["checked"] == 844 and a["valid"] == 838


@pytest.mark.parametrize("nome", ["original", "pos_micro"])
def test_a_d1_resolve_os_nos_22_e_30_com_b34_real(nome):
    _geo, ctx, res = _solve(nome)
    ws = S.engine()[1]
    for ni, ci in RESOLVIDOS_PELA_D1:
        n = ctx["nodes"][ni]
        poly = ws._node_region_polygon(n, ctx["walls"])
        area = ws._poly_area(poly)
        paredes = ws._node_wall_indices(n)
        cobre = []
        for c in res["course_candidates"][ci]:
            if c.get("wall_idx") not in paredes:
                continue
            ov = ws._convex_overlap_area(ws._candidate_polygon(c), poly)
            if ov > 1e-6 * area:
                cobre.append((round(ov / area, 3), c["logical_code"], c.get("placement_reason")))
        cobre.sort(reverse=True)
        assert cobre and cobre[0][1] == "B34" and cobre[0][0] >= 0.999, (ni, ci, cobre)
        assert str(cobre[0][2]).startswith("T_INTERSECTION_DEGRADED_L"), (ni, ci, cobre)
        assert all(code not in ("C04", "C09") for _f, code, _r in cobre), (ni, ci, cobre)
    faltando = set(f["node_index"] for f in res["missing_required_junction_bond"])
    assert not faltando & {22, 30}


def test_a_regra_76_1_so_classifica_as_pecas_sao_as_do_corpus():
    """As pecas do produto sao as mesmas gravadas no corpus (tol_0_05): o
    nao-designar do C09 nao move, nao troca e nao remove peca nenhuma."""
    geo, ctx, res = _solve("original")
    gravado = [c for c in S.snapshot_expected()["cases"] if c["label"] == "tol_0_05"][0]
    assert S.snapshot_sha256(S.normalized_snapshot(ctx, res)) == gravado["sha256"]
    ctx2, res2 = S.solve_on_fresh_context(geo, True, regra76_nao_resolvido=False)
    assert S.snapshot_sha256(S.normalized_snapshot(ctx2, res2)) == gravado["sha256"]
    # sem a 76.1 os mesmos 6 C09 voltam a ser designados amarracao
    assert sorted((v["node_index"], v["course_index"]) for v in res2["compensator_as_junction_bond"]) == \
        NAO_RESOLVIDOS


def test_os_hard_gates_fisicos_continuam_zerados():
    for nome in ("original", "pos_micro"):
        _geo, _ctx, res = _solve(nome)
        assert S.hard_gates(res) == {"collisions": 0, "non_modular": 0, "unsupported": 0,
                                     "opening_invasion": 0, "channel_as_junction_bond": 0}


def test_a_parede_8284580_da_secao_74_nao_mudou():
    geo, ctx, res = _solve("original")
    caso = S.wall_case()
    contagem = S.wall_counts(S.solver_rows(ctx, res, geo), geo, caso["wall_key"])
    assert contagem == caso["expected"]["flag_on"]["solver_counts"]
    assert S.divergence(caso["human_counts"], contagem)["div"] == 3.3


def test_o_legado_nao_ganha_os_gates_nem_muda():
    geo = S.geometry()
    ctx, res = S.solve_on_fresh_context(geo, False, strategy=None)
    assert "compensator_as_junction_bond" not in res
    assert "missing_required_junction_bond" not in res
    legado = S.snapshot_expected()["legacy_cases"][0]["sha256"]
    assert S.snapshot_sha256(S.normalized_snapshot(ctx, res)) == legado
