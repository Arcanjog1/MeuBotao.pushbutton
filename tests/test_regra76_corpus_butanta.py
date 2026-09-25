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

# Motor ANTERIOR a' secao 77 (papel por fiada desligado): os 6 conhecidos.
NAO_RESOLVIDOS = [(28, 5), (28, 7), (28, 9), (47, 2), (47, 4), (48, 3)]
# PRODUTO (secao 77 ligada): o no' 28 nao e' encontro nas fiadas 4-10 - os 3 que
# sobram sao os cantos 47/48, onde o L existe e a peca nao cabe (passo 3).
NAO_RESOLVIDOS_77 = [(47, 2), (47, 4), (48, 3)]
SEM_ENCONTRO_FUNCIONAL_77 = [(28, c) for c in range(4, 11)]
RESOLVIDOS_PELA_D1 = [(22, 5), (22, 7), (22, 9), (30, 5), (30, 7)]
PRE77 = ("original", "pos_micro")                       # secao 77 OFF (motor anterior, preservado)
PRODUTO = ("original_77", "pos_micro_77")               # secao 77 ON (o que o botao faz)


def _solve(nome):
    cache = _solve.__dict__.setdefault("cache", {})
    if nome not in cache:
        geo = S.geometry()
        if nome.startswith("pos_micro"):
            geo = S.with_opening_variant(geo, "post_micro_adjustment_s66")
        cache[nome] = (geo,) + S.solve_on_fresh_context(geo, True, papel_por_fiada=nome.endswith("_77"))
    return cache[nome]


@pytest.mark.parametrize("nome", PRE77 + PRODUTO)
def test_nenhum_compensador_e_designado_amarracao(nome):
    _geo, _ctx, res = _solve(nome)
    assert res["compensator_as_junction_bond"] == []


@pytest.mark.parametrize("nome", PRE77)
def test_os_nos_sem_amarracao_valida_sao_exatamente_os_6_conhecidos(nome):
    """Motor anterior a' secao 77 (flag OFF): registro historico preservado."""
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


@pytest.mark.parametrize("nome", PRE77)
def test_o_no_46_acima_das_portas_nao_e_encontro(nome):
    _geo, _ctx, res = _solve(nome)
    a = res["junction_bond_audit"]
    fora = sorted((x["node_index"], x["course_index"]) for x in a["not_required"])
    assert fora == [(46, c) for c in range(11, 17)]
    assert a["checked"] == 844 and a["valid"] == 838


@pytest.mark.parametrize("nome", PRODUTO)
def test_secao_77_o_no_28_nao_e_encontro_nas_fiadas_das_janelas_e_sobram_os_cantos(nome):
    """PRODUTO: nas fiadas 4-10 a principal 8284502 foi consumida pelas duas
    janelas dos dois lados da regiao do no' 28 -> NO_FUNCTIONAL_JUNCTION (fora
    do denominador), a 8284562 termina livre na face; MISSING 6 -> 3 (47/48,
    onde o L existe e a peca nao cabe). Nunca zero: 47/48 nao sao alcancados."""
    _geo, ctx, res = _solve(nome)
    ws = S.engine()[1]
    falta = res["missing_required_junction_bond"]
    assert sorted((f["node_index"], f["course_index"]) for f in falta) == NAO_RESOLVIDOS_77
    a = res["junction_bond_audit"]
    nfj = sorted((x["node_index"], x["course_index"]) for x in a["not_required"]
                 if x.get("reason") == ws.NO_FUNCTIONAL_JUNCTION_REASON)
    assert nfj == SEM_ENCONTRO_FUNCIONAL_77
    ausente = sorted((x["node_index"], x["course_index"]) for x in a["not_required"]
                     if x.get("reason") != ws.NO_FUNCTIONAL_JUNCTION_REASON)
    assert ausente == [(46, c) for c in range(11, 17)]
    assert a["checked"] == 837 and a["valid"] == 834
    assert res["junction_role_by_course"]["enabled"] is True
    assert sorted(tuple(x[:2]) for x in res["junction_role_by_course"]["no_functional_junction"]) == \
        SEM_ENCONTRO_FUNCIONAL_77
    # a regiao do no' 28 nas fiadas 4-10: so' a parede que chega (8284562), ponta
    # livre ate' a face externa, sem peca de no' nem compensador de no'
    n = ctx["nodes"][28]
    poly = ws._node_region_polygon(n, ctx["walls"])
    area = ws._poly_area(poly)
    paredes = ws._node_wall_indices(n)
    inc = n["incoming_wall_idx"]
    for _ni, ci in SEM_ENCONTRO_FUNCIONAL_77:
        ocup = []
        for c in res["course_candidates"][ci]:
            if c.get("wall_idx") not in paredes:
                continue
            ov = ws._convex_overlap_area(ws._candidate_polygon(c), poly)
            if ov > 1e-6 * area:
                ocup.append((round(ov / area, 3), c["logical_code"], str(c.get("placement_reason") or ""),
                             c.get("wall_idx")))
        ocup.sort(reverse=True)
        assert ocup and ocup[0][3] == inc and ocup[0][0] >= 0.999, (ci, ocup)
        assert all(r == "STANDARD_FILL" for _f, _code, r, _w in ocup), (ci, ocup)
        assert all(code not in ("C04", "C09") for _f, code, _r, _w in ocup), (ci, ocup)


@pytest.mark.parametrize("nome", PRE77 + PRODUTO)
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
    # contrafactual da 76.1 no motor anterior a' secao 77 (papel por fiada OFF)
    ctx2, res2 = S.solve_on_fresh_context(geo, True, regra76_nao_resolvido=False, papel_por_fiada=False)
    assert S.snapshot_sha256(S.normalized_snapshot(ctx2, res2)) == gravado["sha256"]
    # sem a 76.1 os mesmos 6 C09 voltam a ser designados amarracao
    assert sorted((v["node_index"], v["course_index"]) for v in res2["compensator_as_junction_bond"]) == \
        NAO_RESOLVIDOS


def test_os_hard_gates_fisicos_continuam_zerados():
    for nome in PRE77 + PRODUTO:
        _geo, _ctx, res = _solve(nome)
        assert S.hard_gates(res) == {"collisions": 0, "non_modular": 0, "unsupported": 0,
                                     "opening_invasion": 0, "channel_as_junction_bond": 0}


@pytest.mark.parametrize("nome", ["original", "original_77"])
def test_a_parede_8284580_da_secao_74_nao_mudou(nome):
    geo, ctx, res = _solve(nome)
    caso = S.wall_case()
    contagem = S.wall_counts(S.solver_rows(ctx, res, geo), geo, caso["wall_key"])
    assert contagem == caso["expected"]["flag_on"]["solver_counts"]
    assert S.divergence(caso["human_counts"], contagem)["div"] == 3.3


def test_secao_77_so_a_parede_8284562_muda_e_os_nos_22_30_e_os_validos_ficam_iguais():
    """A unica parede fisicamente alterada e' a que chega no no' 28 (8284562).
    Os nos 22/30 (corrigidos pela D1) e os exemplos validos 06/07/08 (nos 5, 0 e
    3) tem a MESMA ocupacao da regiao do no' em todas as fiadas."""
    geo, ctx0, res0 = _solve("original")
    _g, ctx1, res1 = _solve("original_77")
    ids = [w["provenance"]["revit_element_id"] for w in geo["walls"]]
    linhas0 = set(S.normalized_snapshot(ctx0, res0))
    linhas1 = set(S.normalized_snapshot(ctx1, res1))
    chaves = set(l.split("|")[1] for l in (linhas0 ^ linhas1))
    assert chaves == set([ctx0["keys"][ids.index(8284562)]]), chaves
    ws = S.engine()[1]

    def ocupacao(ctx, res, ni):
        n = ctx["nodes"][ni]
        poly = ws._node_region_polygon(n, ctx["walls"])
        area = ws._poly_area(poly)
        paredes = ws._node_wall_indices(n)
        out = []
        for ci in sorted(res["course_candidates"]):
            row = []
            for c in res["course_candidates"][ci]:
                if c.get("wall_idx") not in paredes:
                    continue
                ov = ws._convex_overlap_area(ws._candidate_polygon(c), poly)
                if ov > 1e-6 * area:
                    row.append((round(ov / area, 3), c["logical_code"], str(c.get("placement_reason") or ""),
                                c.get("wall_idx")))
            out.append((ci, sorted(row)))
        return out
    for ni in (22, 30, 5, 0, 3):
        assert ocupacao(ctx0, res0, ni) == ocupacao(ctx1, res1, ni), ni


def test_o_legado_nao_ganha_os_gates_nem_muda():
    geo = S.geometry()
    # legado do PRODUTO (secoes 78 e 79 ligadas): desde a secao 79 os gates das
    # regras 76/76.1 valem sem reforco - e nenhum compensador e' designado
    ctx78, res78 = S.solve_on_fresh_context(geo, False, strategy=None)
    assert res78["compensator_as_junction_bond"] == []
    assert "missing_required_junction_bond" in res78
    # legado HISTORICO (anterior as secoes 78, 79, 80 e 81): continua byte a byte
    # igual ao snapshot gravado e sem os gates
    ctx, res = S.solve_on_fresh_context(geo, False, strategy=None, tolerancias_fisicas=False,
                                        regras_de_encontro=False, reforco_estrutural=False,
                                        regras_gerais=False)
    assert "compensator_as_junction_bond" not in res
    assert "missing_required_junction_bond" not in res
    legado = S.snapshot_expected()["legacy_cases"][0]["sha256"]
    assert S.snapshot_sha256(S.normalized_snapshot(ctx, res)) == legado
