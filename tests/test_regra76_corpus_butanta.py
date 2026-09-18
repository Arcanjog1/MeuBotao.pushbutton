# -*- coding: utf-8 -*-
"""REGRA 76 sobre o corpus versionado do BUTANTA: compensador nunca exerce
funcao de amarracao.

Estado medido (2026-09-18), fluxo CHANNEL:
  * ANTES da regra 76: 11 compensadores (todos C09) assumindo a funcao de
    amarracao - nos T 22/28/30 (fiadas 5,7,9 / 5,7,9 / 5,7) e cantos L 47/48
    (fiadas 2,4 / 3). Metadado e geometria concordam nos 11.
  * A correcao D1 (passo "degrada para L" do T medido a partir do CONTATO onde o
    B34 comeca) resolve os nos 22 e 30 com B34 real nas duas familias - o que o
    projeto humano faz - sem regressao de portao nenhum.
  * RESTAM 6, SEM SOLUCAO AUTOMATICA LIMPA SOB AS REGRAS APROVADAS (medido: recuo
    abre buraco; B19 e o outro braco do L pioram nao-modular/sem apoio). A causa
    e' geometrica: janela a 19,5 cm da face externa do canto (47/48) e pilar de
    14 cm entre duas janelas (28). Estao FIXADOS aqui: o gate continua acusando,
    nao podem crescer nem sumir em silencio. Quando a decisao do usuario chegar,
    este teste muda junto - de proposito.

    python3 -m pytest tests/test_regra76_corpus_butanta.py -q
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import s74_corpus as S  # noqa: E402

pytestmark = pytest.mark.slow

RESTANTES = [(28, 5), (28, 7), (28, 9), (47, 2), (47, 4), (48, 3)]
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
def test_o_gate_acusa_exatamente_os_6_casos_conhecidos(nome):
    _geo, _ctx, res = _solve(nome)
    v = res["compensator_as_junction_bond"]
    assert sorted((x["node_index"], x["course_index"]) for x in v) == RESTANTES
    for x in v:
        assert x["logical_code"] == "C09"
        # metadado E geometria - o motor designou e a peca ocupa a regiao do no'
        assert sorted(x["evidence"]) == ["DESIGNATED_NODE_PIECE", "OCCUPIES_NODE_REGION"]
        assert 0.6 < x["coverage"] < 0.7


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
        assert cobre and cobre[0][1] == "B34", (ni, ci, cobre)
        assert str(cobre[0][2]).startswith("T_INTERSECTION_DEGRADED_L"), (ni, ci, cobre)
        assert all(code not in ("C04", "C09") for _f, code, _r in cobre), (ni, ci, cobre)


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


def test_o_legado_nao_ganha_o_gate_nem_muda():
    geo = S.geometry()
    ctx, res = S.solve_on_fresh_context(geo, False, strategy=None)
    assert "compensator_as_junction_bond" not in res
    legado = S.snapshot_expected()["legacy_cases"][0]["sha256"]
    assert S.snapshot_sha256(S.normalized_snapshot(ctx, res)) == legado
