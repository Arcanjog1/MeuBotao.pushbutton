# -*- coding: utf-8 -*-
"""SECAO 86.12 (correcao do usuario 2026-10-05) - A CANALETA SEGUE A GRADE DA
FIADA DE MESMA PARIDADE ABAIXO.

"algumas canaletas de 34 e 39 nao estao alinhadas com a modulacao abaixo dela,
assim quebrando o prisma dos blocos". Em toda fiada com canaleta (contraverga,
verga, cinta), onde a fiada c-2 tem alvenaria as canaletas repetem peca a peca
as pecas dela (B39->U39, B34->U34, B19->U19, compensador fundido a' vizinha);
sobre o vao a grade e' livre (U39/U34/U19 + no maximo um U_CUT) e absorve a
fase; no quadrado do no' continua o bloco; a corrida so' cresce.

Fixture sintetica (nenhum ID do projeto): parede de 700 cm entre dois cantos L,
janela [109,250] com peitoril 100 (contraverga na f4) e janela [330,471] com
peitoril 80 (contraverga na f3), topo 221 (verga na f11), cinta na f12 (13
fiadas, como o pavimento do humano). Na f9 o pilarete da primeira janela e'
`B34 | B19 | jamba` - o caso dos prints do usuario.

    py -3 -m pytest tests/test_channel_grid_follow_86_12.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import channel_grid_follow as cgf  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
NUM = 13
ESTRATEGIAS = [None, tcr.CHANNEL]
EQUIV = {"CHANNEL_U_39": "B39", "CHANNEL_U_34": "B34", "CHANNEL_U_19": "B19"}


def _janelas():
    return ([seg(0, 0, 700, 0), seg(0, 0, 0, 300), seg(700, 0, 700, 300)],
            [[(ft(109), ft(250), ft(100), ft(221)), (ft(330), ft(471), ft(80), ft(221))], [], []])


_CACHE = {}


def _solve(estrategia=None, follow=True, reverse=False):
    chave = (estrategia, follow, reverse)
    if chave not in _CACHE:
        antes = m.CHANNEL_GRID_FOLLOW_ENABLED
        m.CHANNEL_GRID_FOLLOW_ENABLED = follow
        try:
            lines, ops = _janelas()
            _CACHE[chave] = tcr.solve(lines, ops, strategy=estrategia, num_courses=NUM, reverse=reverse)
        finally:
            m.CHANNEL_GRID_FOLLOW_ENABLED = antes
    return _CACHE[chave]


def _rows(res, walls, wi, ci):
    return orf._wall_strip_pieces(res["course_candidates"].get(ci) or [], walls, wi)


def _own(rows, wi):
    return [r for r in rows if r["cand"].get("wall_idx") == wi and r["along"]]


def _sig(res, ci):
    return sorted(orf._physical_key(c) for c in res["course_candidates"].get(ci) or [])


def _channel_courses(res):
    return sorted(ci for ci, pcs in res["course_candidates"].items() if any(cgf.is_target_channel(c) for c in pcs))


def _desalinhos(res, walls, wi, ci):
    """Canaletas da fiada `ci` que NAO seguem a fiada ci-2 onde ela tem alvenaria:
    toda ponta de canaleta que cai sobre alvenaria de r tem de coincidir (1,5 cm)
    com uma ponta de peca de r (B54 de r pode ser dividido); junta de r DENTRO da
    canaleta so' quando ao lado de um compensador de r (fusao da 51.3). Ponta na
    borda LIVRE da fiada c (nada encostado do outro lado: jamba de vao ativo,
    ponta) nao pode avancar - nunca invade."""
    r = _own(_rows(res, walls, wi, ci - 2), wi)
    todas = _rows(res, walls, wi, ci)
    out = []
    for p in _own(todas, wi):
        if not cgf.is_target_channel(p["cand"]):
            continue
        under = [x for x in r if min(x["hi"], p["hi"]) - max(x["lo"], p["lo"]) > 1.0]
        if not under:
            continue   # sobre o vao: grade livre
        for edge, lado in ((p["lo"], -1), (p["hi"], 1)):
            if lado < 0:
                livre = not any(0.0 <= edge - q["hi"] <= 2.5 for q in todas if q is not p)
            else:
                livre = not any(0.0 <= q["lo"] - edge <= 2.5 for q in todas if q is not p)
            if livre:
                continue
            cortada = [x for x in r if x["lo"] < edge - 1.5 and x["hi"] > edge + 1.5]
            if cortada and cortada[0]["cand"].get("logical_code") != "B54":
                out.append(("PONTA", round(p["lo"], 1), round(p["hi"], 1), p["cand"]["logical_code"]))
        for a, b in zip(r, r[1:]):
            junta = (a["hi"] + b["lo"]) / 2.0
            if p["lo"] + 1.5 < junta < p["hi"] - 1.5 and 0.0 <= b["lo"] - a["hi"] <= 2.5:
                if a["cand"].get("logical_code") not in ("C04", "C09") and \
                        b["cand"].get("logical_code") not in ("C04", "C09"):
                    out.append(("JUNTA", round(p["lo"], 1), round(p["hi"], 1), p["cand"]["logical_code"]))
    return out


# ------------------------------------------------------------------ chave
def test_chave_ligada_por_padrao_e_politica():
    assert m.CHANNEL_GRID_FOLLOW_ENABLED is True
    pol = cgf.channel_grid_follow_policy()
    assert pol["max_cut_cm"] == 39.0 and pol["min_cut_cm"] == 9.0
    assert tuple(cgf.TARGET_ROLES) == (orf.ROLE_ABOVE_OPENING, orf.ROLE_BELOW_SILL, orf.ROLE_TOP_BOND_BEAM)


# ------------------------------------------------------------------ o caso dos prints
@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_verga_sobre_pilarete_b34_b19_jamba_vira_u34_u19(estrategia):
    res, walls, _n, _o = _solve(estrategia)
    f9 = _own(_rows(res, walls, 0, 9), 0)
    f11 = _own(_rows(res, walls, 0, 11), 0)
    # o pilarete da primeira janela na f9 termina em B34 | B19 | jamba (109)
    b19 = [x for x in f9 if x["cand"]["logical_code"] == "B19" and abs(x["hi"] - 109.0) < 1.0]
    assert b19, [(x["cand"]["logical_code"], x["lo"], x["hi"]) for x in f9]
    b34 = [x for x in f9 if x["cand"]["logical_code"] == "B34" and abs(x["hi"] - (b19[0]["lo"] - 1.0)) < 1.0]
    assert b34
    for src, code in ((b34[0], orf.CHANNEL_U_34), (b19[0], orf.CHANNEL_U_19)):
        same = [p for p in f11 if abs(p["lo"] - src["lo"]) < 0.05 and abs(p["hi"] - src["hi"]) < 0.05]
        assert same and same[0]["cand"]["logical_code"] == code, (src["lo"], src["hi"], same)
        assert cgf.is_target_channel(same[0]["cand"])
    assert res["channel_grid_follow"]["applied"]


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_toda_canaleta_segue_a_fiada_de_mesma_paridade_abaixo(estrategia):
    com, walls, _n, _o = _solve(estrategia)
    sem, walls0, _n0, _o0 = _solve(estrategia, follow=False)
    cursos = _channel_courses(com)
    assert set(cursos) >= set([3, 4, 11, 12])
    for ci in cursos:
        assert _desalinhos(com, walls, 0, ci) == [], ci
    # o estado anterior tinha canaleta fora da grade de baixo (o defeito dos prints)
    assert any(_desalinhos(sem, walls0, 0, ci) for ci in _channel_courses(sem))


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_cinta_repete_a_fiada_10_sobre_o_pilarete(estrategia):
    res, walls, _n, _o = _solve(estrategia)
    f10 = _own(_rows(res, walls, 0, 10), 0)
    f12 = _own(_rows(res, walls, 0, 12), 0)
    pilar = [x for x in f10 if x["lo"] >= 245.0 and x["hi"] <= 335.0]
    assert pilar
    juntas10 = [round((a["hi"] + b["lo"]) / 2.0, 1) for a, b in zip(pilar, pilar[1:])
                if a["cand"]["logical_code"] not in ("C04", "C09") and b["cand"]["logical_code"] not in ("C04", "C09")]
    for x in pilar:
        sobre = [p for p in f12 if min(p["hi"], x["hi"]) - max(p["lo"], x["lo"]) > 1.0]
        assert sobre and all(orf.is_channel_code(p["cand"]["logical_code"]) for p in sobre)
        if x["cand"]["logical_code"] in EQUIV.values():
            same = [p for p in sobre if abs(p["lo"] - x["lo"]) < 0.05 and abs(p["hi"] - x["hi"]) < 0.05]
            if same:
                assert EQUIV.get(same[0]["cand"]["logical_code"]) == x["cand"]["logical_code"]
    juntas12 = [round((a["hi"] + b["lo"]) / 2.0, 1) for a, b in zip(f12, f12[1:])]
    assert all(j in juntas12 for j in juntas10), (juntas10, juntas12)


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_fechamento_da_fase_fica_sobre_o_vao(estrategia):
    res, walls, _n, _o = _solve(estrategia)
    for ci in _channel_courses(res):
        r = _own(_rows(res, walls, 0, ci - 2), 0)
        livres = [p for p in _own(_rows(res, walls, 0, ci), 0)
                  if ((p["cand"].get("reinforcement") or {}).get("grid_follow") or {}).get("kind") == "FREE"]
        for p in livres:
            sobre_alvenaria = sum(max(0.0, min(p["hi"], x["hi"]) - max(p["lo"], x["lo"])) for x in r)
            # so' o compensador de r absorvido pelo trecho livre (<= 9 cm) pode ficar sob ele
            assert sobre_alvenaria <= 9.5, (ci, p["lo"], p["hi"], sobre_alvenaria)
            if p["cand"]["logical_code"] == orf.CHANNEL_U_CUT:
                assert p["cand"]["instance_length_cm"] >= 9.0 - 1e-6
    # no maximo uma canaleta cortada por trecho livre
    rep = res["channel_grid_follow"]
    for w in rep["windows"]:
        for lo, hi in w["free_cm"]:
            cuts = [a for a in w["after"] if a[0] == orf.CHANNEL_U_CUT and a[1] >= lo - 0.5 and a[2] <= hi + 0.5]
            assert len(cuts) <= 1, (w["course_index"], lo, hi, cuts)


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_no_mantem_o_bloco_de_amarracao(estrategia):
    com, walls, nodes, openings = _solve(estrategia)
    sem, _w0, _n0, _o0 = _solve(estrategia, follow=False)
    for ci in _channel_courses(com):
        amarr = lambda res: sorted(orf._physical_key(c) for c in res["course_candidates"][ci] if orf._is_tie(c))
        assert amarr(com) == amarr(sem), ci
        for wi in range(len(walls)):
            quadrados = orf._node_squares_cm(walls, nodes, wi)
            for row in _own(_rows(com, walls, wi, ci), wi):
                if orf.is_channel_code(row["cand"]["logical_code"]):
                    assert orf._square_hit(row["lo"], row["hi"], quadrados, 0.5) is None, (ci, wi, row["lo"])
    assert com["channel_as_junction_bond"] == []
    assert (com["top_bond_beam"]["audit"]["counts"]["TOP_BOND_BEAM_CHANNEL_AT_NODE"] == 0)
    assert len(com.get("missing_required_junction_bond") or []) == len(sem.get("missing_required_junction_bond") or [])
    # validacao e materializacao limpas
    counts = com["opening_reinforcement"]["validation"]["counts"]
    for key in ("MISSING_REQUIRED_CHANNEL", "EXTRA_CHANNEL", "CHANNEL_WRONG_COURSE", "CHANNEL_INVADES_OPENING",
                "CHANNEL_COLLISION", "CHANNEL_SUPPORT_BELOW_POLICY", "CHANNEL_OPENING_OVERCUT"):
        assert counts[key] == 0, key
    pf = m.controlled_beta_preflight(com, walls, openings, tcr.sb.CATALOG, 0.0)
    plano = m.materialization_plan(com, pf)
    assert not pf.get("opening_violations") and not pf.get("collisions") and not plano["skip"]
    assert all(a.get("ok") for a in com.get("wall_bond_audits") or [] if isinstance(a, dict))


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_apoio_da_verga_e_da_contraverga_nao_diminui(estrategia):
    com, _w, _n, _o = _solve(estrategia)
    sem, _w0, _n0, _o0 = _solve(estrategia, follow=False)
    antes = dict(((r["wall_idx"], r["opening_index"]), r) for r in sem["opening_structural_trace"])
    depois = dict(((r["wall_idx"], r["opening_index"]), r) for r in com["opening_structural_trace"])
    assert set(antes) == set(depois) and antes
    for key in antes:
        for papel in ("lintel", "sill"):
            a, d = antes[key], depois[key]
            assert d[papel + "_status"] == a[papel + "_status"], (key, papel)
            if a[papel + "_left_support"] is None:
                continue
            assert d[papel + "_left_support"] >= a[papel + "_left_support"] - 1e-6, (key, papel)
            assert d[papel + "_right_support"] >= a[papel + "_right_support"] - 1e-6, (key, papel)
            assert d[papel + "_start"] <= a[papel + "_start"] + 1e-6 and d[papel + "_end"] >= a[papel + "_end"] - 1e-6
    assert com["channel_grid_follow"]["support_drops"] == []


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_chave_desligada_e_o_comportamento_anterior(estrategia):
    com, _w, _n, _o = _solve(estrategia)
    sem, _w0, _n0, _o0 = _solve(estrategia, follow=False)
    assert "channel_grid_follow" not in sem
    assert not any(((c.get("reinforcement") or {}).get("grid_follow")) for v in sem["course_candidates"].values()
                   for c in v)
    tocadas = com["channel_grid_follow"]["source_courses"]
    assert tocadas
    for ci in range(NUM):
        if ci in tocadas:
            # a entrada do passe e' exatamente a fiada do caminho desligado
            assert sorted(orf._physical_key(c) for c in tocadas[ci]) == _sig(sem, ci), ci
            assert _sig(com, ci) != _sig(sem, ci)
        else:
            assert _sig(com, ci) == _sig(sem, ci), ci


def test_paridade_82_1_le_as_fiadas_de_antes_do_passe():
    com, _w, _n, _o = _solve(None)
    sem, _w0, _n0, _o0 = _solve(None, follow=False)
    lida = m._without_top_bond_beam(com)
    lida_sem = m._without_top_bond_beam(sem)
    for ci in range(NUM):
        assert sorted(orf._physical_key(c) for c in lida["course_candidates"][ci]) == \
            sorted(orf._physical_key(c) for c in lida_sem["course_candidates"][ci]), ci


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_determinismo_e_entrada_intocada(estrategia):
    sem, walls, nodes, _o = _solve(estrategia, follow=False)
    entrada = dict((ci, list(v)) for ci, v in sem["course_candidates"].items())
    assinatura = dict((ci, _sig(sem, ci)) for ci in entrada)
    pol = (sem.get("opening_reinforcement") or {}).get("policy")
    a = cgf.plan_channel_grid_follow(sem["course_candidates"], walls, NUM, nodes=nodes, channel_overrides=pol,
                                     catalog=tcr.sb.CATALOG)
    b = cgf.plan_channel_grid_follow(sem["course_candidates"], walls, NUM, nodes=nodes, channel_overrides=pol,
                                     catalog=tcr.sb.CATALOG)
    for ci in entrada:
        assert [id(c) for c in sem["course_candidates"][ci]] == [id(c) for c in entrada[ci]]
        assert _sig(sem, ci) == assinatura[ci]
        sa = sorted(orf._physical_key(c) for c in a["course_candidates"][ci])
        sb_ = sorted(orf._physical_key(c) for c in b["course_candidates"][ci])
        assert sa == sb_, ci
    assert a["windows"] == b["windows"] and a["counts"] == b["counts"]
    # o passe dentro do solve e' o mesmo passe sobre a mesma entrada
    com, _w, _n, _o2 = _solve(estrategia)
    for ci in entrada:
        assert _sig(com, ci) == sorted(orf._physical_key(c) for c in a["course_candidates"][ci]), ci


def test_sentido_do_eixo_invertido_mantem_a_regra():
    com, walls, nodes, _o = _solve(None, reverse=True)
    for ci in _channel_courses(com):
        for wi in range(len(walls)):
            assert _desalinhos(com, walls, wi, ci) == [], (ci, wi)
    assert com["channel_as_junction_bond"] == []
    counts = com["opening_reinforcement"]["validation"]["counts"]
    assert counts["MISSING_REQUIRED_CHANNEL"] == 0 and counts["CHANNEL_COLLISION"] == 0


def test_familias_de_canaleta_ausentes_nada_muda():
    lines, ops = _janelas()
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, ops, tcr.sb.CATALOG, 0.0, NUM,
                                              variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
                                              opening_reinforcement_strategy=None,
                                              opening_structural_channel_available=False)
    assert res["channel_grid_follow"]["applied"] is False
    assert res["channel_grid_follow"]["reason"] == "CHANNEL_FAMILY_MISSING"
    assert tcr.channel_count(res) == 0


# ------------------------------------------------------------------ trecho livre (unidade)
def test_trecho_livre_sem_vizinhas_fecha_com_pecas_padrao():
    pol = cgf.channel_grid_follow_policy()
    res = cgf._fill_free(110.0, 249.0, True, True, [], pol)
    assert res is not None
    comps = [round(hi - lo, 2) for lo, hi, _c in res["pieces"]]
    assert len(comps) == 4 and sum(comps) + 3.0 == pytest.approx(139.0)
    assert all(c in (39.0, 34.0) for c in comps)   # sem U19 nem corte quando nao precisa


def test_trecho_livre_desencontra_as_juntas_de_cima_e_de_baixo():
    pol = cgf.channel_grid_follow_policy()
    juntas = [144.5, 179.5, 214.5]
    res = cgf._fill_free(110.0, 249.0, True, True, juntas, pol)
    novas = [(a[1] + b[0]) / 2.0 for a, b in zip(res["pieces"], res["pieces"][1:])]
    assert all(min(abs(n - j) for j in juntas) >= 1.5 for n in novas), novas
    assert res["key"][0] == 0


def test_trecho_livre_usa_no_maximo_um_corte_e_nunca_minusculo():
    pol = cgf.channel_grid_follow_policy()
    for length in (12.0, 27.0, 50.0, 101.0, 152.0, 233.0):
        res = cgf._fill_free(0.0, length, True, True, [], pol)
        assert res is not None, length
        cuts = [p for p in res["pieces"] if p[2] == cgf.FREE_CUT]
        assert len(cuts) <= 1, length
        assert all(p[1] - p[0] >= 9.0 - 1e-6 for p in cuts), length
        assert res["pieces"][0][0] == pytest.approx(0.0, abs=0.61)
        assert res["pieces"][-1][1] == pytest.approx(length, abs=0.61)
    assert cgf._fill_free(0.0, 5.0, True, True, [], pol) is None


def test_trecho_livre_espelhado_e_o_espelho_do_trecho_canonico():
    pol = cgf.channel_grid_follow_policy()
    juntas = [30.5, 95.5]
    canon = cgf._fill_canonical(0.0, 152.0, True, False, juntas, pol, None, True, {})
    # a mesma parede desenhada ao contrario: t' = 152 - t
    espelho = cgf._fill_canonical(0.0, 152.0, False, True, sorted(152.0 - j for j in juntas), pol, None, False, {})
    assert [(round(152.0 - hi, 3), round(152.0 - lo, 3), c) for lo, hi, c in reversed(espelho["pieces"])] == \
        [(round(lo, 3), round(hi, 3), c) for lo, hi, c in canon["pieces"]]


def test_b54_de_preenchimento_dividido_longe_das_juntas_vizinhas():
    pol = cgf.channel_grid_follow_policy()
    ancora = {"lo": 100.0, "hi": 154.0, "code": "B54"}
    partes = cgf._split_b54(ancora, [134.5], pol)
    assert partes == [(100.0, 119.0), (120.0, 154.0)]
    assert cgf._split_b54(ancora, [119.5, 134.5], pol) is None
