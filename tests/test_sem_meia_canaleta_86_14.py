# -*- coding: utf-8 -*-
"""SECAO 86.14 (correcao do usuario 2026-10-05) - SEM MEIA CANALETA.

Print do Revit com MEIA CANALETA U19 na cinta/verga sobre uma coluna de pastilha
C04 + meio bloco B19. Palavras do usuario: "isso nao existe, pode parar; a
continuacao das canaletas nao serve para os meio bloco; quando houver um meio
bloco nas fiadas abaixo deve ser completado por bloco de 34 ou 39".

REGRA OBRIGATORIA (chave `opening_reinforcement.CHANNEL_HALF_U19_ENABLED = False`):

- nenhuma MEIA CANALETA (U19, nem U_CUT de 19 cm) em verga, contraverga ou cinta;
- onde a fiada de mesma paridade abaixo (c-2) tem meio bloco (B19) ou compensador
  (C04/C09), a canaleta NAO acompanha a peca: o trecho fecha com U39/U34 (a
  canaleta cobre o meio bloco e avanca sobre a peca vizinha ou sobre o vao);
- juntas de c-2 entre dois blocos INTEIROS sao duras: a junta da canaleta
  continua coincidindo com elas (86.12);
- B54 de preenchimento sob canaleta: U39/U34 e, so' se nada fechar, um U_CUT
  (>= 9 cm) - de preferencia com a junta deslocada para o vao;
- sobre o vao: U39/U34 e no maximo um U_CUT (>= 9 cm, nunca 19).

Fixture sintetica da 86.12 (nenhum ID do projeto): parede de 700 cm entre dois
cantos L, janelas [109,250] (peitoril 100) e [330,471] (peitoril 80), topo 221,
13 fiadas. Na f9 o pilarete da primeira janela e' `B34 | B19 | jamba`.

    py -3 -m pytest tests/test_sem_meia_canaleta_86_14.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import b34_run_arrangement as runs  # noqa: E402
from core.engine import channel_grid_follow as cgf  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
CAT = tcr.sb.CATALOG
NUM = 13
TOP = NUM - 1
ESTRATEGIAS = [None, tcr.CHANNEL]
WHOLE = ("B39", "B34", "CHANNEL_U_39", "CHANNEL_U_34")


def _janelas():
    return ([seg(0, 0, 700, 0), seg(0, 0, 0, 300), seg(700, 0, 700, 300)],
            [[(ft(109), ft(250), ft(100), ft(221)), (ft(330), ft(471), ft(80), ft(221))], [], []])


_CACHE = {}


def _solve(estrategia=None, half=False, fresh=False):
    chave = (estrategia, half)
    if fresh or chave not in _CACHE:
        meia = orf.CHANNEL_HALF_U19_ENABLED
        orf.CHANNEL_HALF_U19_ENABLED = half
        try:
            lines, ops = _janelas()
            out = tcr.solve(lines, ops, strategy=estrategia, num_courses=NUM)
        finally:
            orf.CHANNEL_HALF_U19_ENABLED = meia
        if fresh:
            return out
        _CACHE[chave] = out
    return _CACHE[chave]


def _own(res, walls, wi, ci):
    return [r for r in orf._wall_strip_pieces(res["course_candidates"].get(ci) or [], walls, wi)
            if r["cand"].get("wall_idx") == wi and r["along"]]


def _channel_courses(res):
    return sorted(ci for ci, pcs in res["course_candidates"].items() if any(cgf.is_target_channel(c) for c in pcs))


def _sig(res, ci):
    return sorted(orf._physical_key(c) for c in res["course_candidates"].get(ci) or [])


def _contig(a, b):
    return 0.0 <= b["lo"] - a["hi"] <= 2.5


def _whole(row):
    return row["cand"].get("logical_code") in WHOLE


def _violacoes_duras(res, walls, wi, ci):
    """Regua independente da regra: (1) junta de c-2 entre dois blocos INTEIROS dentro de
    uma canaleta; (2) ponta de canaleta no meio de um bloco inteiro de c-2 que tem bloco
    inteiro encostado dos dois lados."""
    r = _own(res, walls, wi, ci - 2)
    out = []
    for p in _own(res, walls, wi, ci):
        if not cgf.is_target_channel(p["cand"]):
            continue
        for a, b in zip(r, r[1:]):
            j = (a["hi"] + b["lo"]) / 2.0
            if _contig(a, b) and _whole(a) and _whole(b) and p["lo"] + 1.5 < j < p["hi"] - 1.5:
                out.append(("JUNTA_DURA", ci, round(p["lo"], 1), round(p["hi"], 1), round(j, 1)))
        for edge in (p["lo"], p["hi"]):
            for k, x in enumerate(r):
                if x["lo"] < edge - 1.5 and x["hi"] > edge + 1.5 and _whole(x):
                    esq = k > 0 and _contig(r[k - 1], x) and _whole(r[k - 1])
                    dir_ = k + 1 < len(r) and _contig(x, r[k + 1]) and _whole(r[k + 1])
                    if esq and dir_:
                        out.append(("PONTA", ci, round(p["lo"], 1), round(p["hi"], 1), round(edge, 1)))
    return out


# ------------------------------------------------------------------ chave
def test_chave_ligada_por_padrao_proibe_a_meia_canaleta(monkeypatch):
    assert orf.CHANNEL_HALF_U19_ENABLED is False
    assert orf.half_channel_allowed() is False
    assert orf._standard_code_for_length(19.0) is None
    assert orf._standard_code_for_length(34.0) == orf.CHANNEL_U_34
    assert runs._channel_of_block("B19") is None and runs._channel_of_block("B34") == orf.CHANNEL_U_34
    assert [p for p, _c in cgf._free_steps()] == [39.0, 34.0]
    assert orf.is_half_channel_piece({"logical_code": orf.CHANNEL_U_19})
    assert orf.is_half_channel_piece({"logical_code": orf.CHANNEL_U_CUT, "instance_length_cm": 19.0})
    assert not orf.is_half_channel_piece({"logical_code": orf.CHANNEL_U_CUT, "instance_length_cm": 24.0})
    # religada = o contrato antigo (86.7/86.12)
    monkeypatch.setattr(orf, "CHANNEL_HALF_U19_ENABLED", True)
    assert orf._standard_code_for_length(19.0) == orf.CHANNEL_U_19
    assert runs._channel_of_block("B19") == orf.CHANNEL_U_19
    assert [p for p, _c in cgf._free_steps()] == [39.0, 34.0, 19.0]


# ------------------------------------------------------------------ o caso do print
@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_nenhuma_meia_canaleta_em_verga_contraverga_e_cinta(estrategia):
    res, walls, _n, _o = _solve(estrategia)
    cursos = _channel_courses(res)
    assert set(cursos) >= set([3, 4, 11, 12])
    for ci, pecas in res["course_candidates"].items():
        for c in pecas:
            assert not orf.is_half_channel_piece(c), (ci, c.get("logical_code"), c.get("instance_length_cm"))
    assert orf.half_channel_audit(res["course_candidates"])["counts"]["total"] == 0
    assert res["channel_grid_follow"]["half_channel_audit"]["counts"]["total"] == 0
    assert res["opening_reinforcement"]["validation"]["counts"]["CHANNEL_HALF_PIECE"] == 0
    # nenhum U_CUT abaixo de 9 cm nas canaletas
    for ci in cursos:
        for p in _own(res, walls, 0, ci):
            if p["cand"]["logical_code"] == orf.CHANNEL_U_CUT:
                assert p["cand"]["instance_length_cm"] >= 9.0 - 1e-6, (ci, p["lo"], p["hi"])


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_meio_bloco_abaixo_e_completado_por_u34_ou_u39(estrategia):
    res, walls, _n, _o = _solve(estrategia)
    f9 = _own(res, walls, 0, 9)
    f11 = _own(res, walls, 0, 11)
    # o caso do print: pilarete `B34 | B19 | jamba (109)` na f9
    b19 = [x for x in f9 if x["cand"]["logical_code"] == "B19" and abs(x["hi"] - 109.0) < 1.0]
    assert b19, [(x["cand"]["logical_code"], x["lo"], x["hi"]) for x in f9]
    meio = (b19[0]["lo"] + b19[0]["hi"]) / 2.0
    sobre = [p for p in f11 if p["lo"] - 0.05 <= meio <= p["hi"] + 0.05]
    assert sobre and sobre[0]["cand"]["logical_code"] in (orf.CHANNEL_U_39, orf.CHANNEL_U_34), sobre
    # a canaleta nao acompanha o meio bloco: nenhuma peca da verga com a extensao do B19
    assert not [p for p in f11 if abs(p["lo"] - b19[0]["lo"]) < 0.6 and abs(p["hi"] - b19[0]["hi"]) < 0.6]
    # em toda fiada de canaleta: o que cobre um B19 de c-2 e' U39/U34 e passa dele
    for ci in _channel_courses(res):
        for x in _own(res, walls, 0, ci - 2):
            if x["cand"]["logical_code"] != "B19":
                continue
            meio = (x["lo"] + x["hi"]) / 2.0
            cobre = [p for p in _own(res, walls, 0, ci) if p["lo"] - 0.05 <= meio <= p["hi"] + 0.05
                     and cgf.is_target_channel(p["cand"])]
            for p in cobre:
                assert p["cand"]["logical_code"] in (orf.CHANNEL_U_39, orf.CHANNEL_U_34), (ci, x["lo"], p["lo"])
                assert p["lo"] < x["lo"] - 0.5 or p["hi"] > x["hi"] + 0.5, (ci, x["lo"], p["lo"], p["hi"])
    # o passe trocou canaleta sobre peca mole (na 1a passada ou na 2a, depois da jamba - 86.13)
    moles = sum((res.get(k) or {}).get("counts", {}).get("soft_pieces", 0)
                for k in ("channel_grid_follow", "channel_grid_follow_pass1"))
    assert moles > 0


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_juntas_duras_entre_blocos_inteiros_continuam_alinhadas(estrategia):
    res, walls, _n, _o = _solve(estrategia)
    for ci in _channel_courses(res):
        for wi in range(len(walls)):
            assert _violacoes_duras(res, walls, wi, ci) == [], (ci, wi)
    # a junta dura `B39 | B34` do pilarete da f9 (54,5) continua na verga da f11
    f11 = _own(res, walls, 0, 11)
    juntas = [(a["hi"] + b["lo"]) / 2.0 for a, b in zip(f11, f11[1:]) if _contig(a, b)]
    assert any(abs(j - 54.5) < 0.6 for j in juntas), juntas


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_juntas_da_canaleta_desencontradas_das_fiadas_vizinhas(estrategia):
    res, walls, _n, _o = _solve(estrategia)
    for ci in _channel_courses(res):
        c = _own(res, walls, 0, ci)
        viz = []
        for cj in (ci - 1, ci + 1):
            rj = _own(res, walls, 0, cj)
            viz += [(a["hi"] + b["lo"]) / 2.0 for a, b in zip(rj, rj[1:]) if _contig(a, b)]
        for a, b in zip(c, c[1:]):
            if _contig(a, b) and (cgf.is_target_channel(a["cand"]) or cgf.is_target_channel(b["cand"])):
                j = (a["hi"] + b["lo"]) / 2.0
                assert not any(abs(j - t) < 1.5 for t in viz), (ci, j)


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_no_continua_com_bloco_e_tudo_valida(estrategia):
    res, walls, nodes, openings = _solve(estrategia)
    assert res["channel_as_junction_bond"] == []
    assert res["top_bond_beam"]["audit"]["counts"]["TOP_BOND_BEAM_CHANNEL_AT_NODE"] == 0
    for ci in _channel_courses(res):
        for wi in range(len(walls)):
            quadrados = orf._node_squares_cm(walls, nodes, wi)
            for row in _own(res, walls, wi, ci):
                if orf.is_channel_code(row["cand"]["logical_code"]):
                    assert orf._square_hit(row["lo"], row["hi"], quadrados, 0.5) is None, (ci, wi, row["lo"])
    counts = res["opening_reinforcement"]["validation"]["counts"]
    for key in ("MISSING_REQUIRED_CHANNEL", "EXTRA_CHANNEL", "CHANNEL_WRONG_COURSE", "CHANNEL_INVADES_OPENING",
                "CHANNEL_COLLISION", "CHANNEL_SUPPORT_BELOW_POLICY", "CHANNEL_OPENING_OVERCUT", "CHANNEL_HALF_PIECE"):
        assert counts[key] == 0, key
    assert res["channel_grid_follow"]["unresolved"] == []
    assert res["channel_grid_follow"]["support_drops"] == []
    pf = m.controlled_beta_preflight(res, walls, openings, CAT, 0.0)
    plano = m.materialization_plan(res, pf)
    assert not pf.get("opening_violations") and not pf.get("collisions") and not plano["skip"]
    assert all(a.get("ok") for a in res.get("wall_bond_audits") or [] if isinstance(a, dict))


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_apoio_da_verga_nao_diminui_contra_o_legado(estrategia):
    novo, _w, _n, _o = _solve(estrategia)
    velho, _w0, _n0, _o0 = _solve(estrategia, half=True)
    antes = dict(((r["wall_idx"], r["opening_index"]), r) for r in velho["opening_structural_trace"])
    depois = dict(((r["wall_idx"], r["opening_index"]), r) for r in novo["opening_structural_trace"])
    assert set(antes) == set(depois) and antes
    for key in antes:
        for papel in ("lintel", "sill"):
            a, d = antes[key], depois[key]
            assert d[papel + "_status"] == a[papel + "_status"], (key, papel)
            if d[papel + "_left_support"] is None:
                continue
            assert min(d[papel + "_left_support"], d[papel + "_right_support"]) >= 19.0 - 1e-6, (key, papel)


# ------------------------------------------------------------------ chave = comportamento
@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_chave_religada_volta_a_meia_canaleta_da_86_12(estrategia):
    res, walls, _n, _o = _solve(estrategia, half=True)
    assert orf.half_channel_audit(res["course_candidates"])["counts"]["CHANNEL_U_19"] > 0
    f9 = _own(res, walls, 0, 9)
    f11 = _own(res, walls, 0, 11)
    b19 = [x for x in f9 if x["cand"]["logical_code"] == "B19" and abs(x["hi"] - 109.0) < 1.0][0]
    same = [p for p in f11 if abs(p["lo"] - b19["lo"]) < 0.05 and abs(p["hi"] - b19["hi"]) < 0.05]
    assert same and same[0]["cand"]["logical_code"] == orf.CHANNEL_U_19
    # com a chave religada a validacao nao acusa a meia canaleta (contrato antigo)
    assert res["opening_reinforcement"]["validation"]["counts"]["CHANNEL_HALF_PIECE"] == 0
    assert res["channel_grid_follow"]["counts"]["soft_pieces"] == 0


# ------------------------------------------------------------------ determinismo
@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_determinismo(estrategia):
    a, walls, nodes, _o = _solve(estrategia)
    b, _w2, _n2, _o2 = _solve(estrategia, fresh=True)
    for ci in range(NUM):
        assert _sig(a, ci) == _sig(b, ci), ci
    assert a["channel_grid_follow"]["windows"] == b["channel_grid_follow"]["windows"]
    # o passe sobre a mesma entrada, duas vezes: mesmo resultado, entrada intocada
    fonte = dict((ci, list(v)) for ci, v in a["channel_grid_follow"]["source_courses"].items())
    entrada = dict(a["course_candidates"])
    entrada.update(fonte)
    pol = a["opening_reinforcement"]["policy"]
    antes = dict((ci, sorted(orf._physical_key(c) for c in v)) for ci, v in entrada.items())
    x = cgf.plan_channel_grid_follow(entrada, walls, NUM, nodes=nodes, channel_overrides=pol, catalog=CAT)
    y = cgf.plan_channel_grid_follow(entrada, walls, NUM, nodes=nodes, channel_overrides=pol, catalog=CAT)
    assert x["windows"] == y["windows"] and x["counts"] == y["counts"]
    for ci in entrada:
        assert sorted(orf._physical_key(c) for c in entrada[ci]) == antes[ci]
        assert sorted(orf._physical_key(c) for c in x["course_candidates"][ci]) == \
            sorted(orf._physical_key(c) for c in y["course_candidates"][ci])
    assert x["half_channel_audit"]["counts"]["total"] == 0


# ------------------------------------------------------------------ unidades
def test_trecho_livre_nunca_usa_19_cm():
    pol = cgf.channel_grid_follow_policy()
    for length in range(9, 400, 5):
        res = cgf._fill_free(0.0, float(length), True, True, [], pol)
        if res is None:
            continue
        cuts = [p for p in res["pieces"] if p[2] == cgf.FREE_CUT]
        assert len(cuts) <= 1, length
        for lo, hi, code in res["pieces"]:
            assert not orf.is_half_channel_length(hi - lo), (length, lo, hi, code)
            assert code != "B19"
            assert hi - lo >= 9.0 - 1e-6
    assert cgf._fill_free(0.0, 19.0, False, False, [], pol) is None   # 19 sozinho nao fecha


def test_corte_vai_para_cima_do_vao():
    pol = cgf.channel_grid_follow_policy()
    # B19 [285-304] + vao [305-364] + C09 [365-374]: 89 cm so' fecha com um U_CUT, que fica sobre o vao
    res = cgf._fill_free(285.0, 374.0, True, True, [], pol, None, [(305.0, 364.0)])
    cut = [p for p in res["pieces"] if p[2] == cgf.FREE_CUT]
    assert len(cut) == 1 and 305.0 <= (cut[0][0] + cut[0][1]) / 2.0 <= 364.0, res["pieces"]
    assert res["key"][4] == 0


def _ctx():
    return {"pol": cgf.channel_grid_follow_policy(), "canonical": True, "fill_cache": {}, "catalog": CAT}


def _a(lo, hi, code):
    return ["A", {"lo": lo, "hi": hi, "code": code, "cand": {}}]


def _resumo(items):
    out = []
    for it in items:
        if it[0] == "A":
            out.append(("A", it[1]["code"], it[1]["lo"], it[1]["hi"]))
        else:
            out.append(("F", it[1], it[2]))
    return out


def test_meio_bloco_entre_blocos_inteiros_abrange_um_vizinho_e_mantem_a_junta_dura():
    items = [_a(0.0, 39.0, "B39"), _a(40.0, 74.0, "B34"), _a(75.0, 94.0, "B19"), _a(95.0, 134.0, "B39"),
             _a(135.0, 174.0, "B39")]
    zones = [[0.0, 174.0, []]]
    out, info = cgf._soften_items(_ctx(), items, zones, 0.0, 174.0, True, True, [])
    resumo = _resumo(out)
    # B19 sozinho (19 cm) nao fecha sem a meia canaleta: abrange UM bloco inteiro vizinho
    assert info["absorbed"] == 1
    livres = [x for x in resumo if x[0] == "F"]
    assert len(livres) == 1
    # escolhe o B39 (59 cm = U34 + U_CUT 24, corte nao minusculo) e nao o B34 (54 = U39 + U_CUT 14)
    assert livres[0][1:] == (75.0, 134.0)
    # as juntas duras (39,5 entre B39|B34 e 134,5 entre B39|B39) ficam: as ancoras seguem intactas
    assert ("A", "B34", 40.0, 74.0) in resumo and ("A", "B39", 135.0, 174.0) in resumo
    fill = cgf._fill_free(75.0, 134.0, True, True, [], _ctx()["pol"])
    assert sorted(round(hi - lo) for lo, hi, _c in fill["pieces"]) == [24, 34]


def test_b54_entre_blocos_inteiros_e_dividido_por_dentro():
    items = [_a(0.0, 39.0, "B39"), _a(40.0, 94.0, "B54"), _a(95.0, 134.0, "B39")]
    out, info = cgf._soften_items(_ctx(), items, [[0.0, 134.0, []]], 0.0, 134.0, True, True, [])
    resumo = _resumo(out)
    # a junta do B54 com bloco inteiro e' dura: nada e' abrangido, o B54 vira U39 + U_CUT 14
    assert info["absorbed"] == 0
    assert resumo == [("A", "B39", 0.0, 39.0), ("F", 40.0, 94.0), ("A", "B39", 95.0, 134.0)]
    fill = cgf._fill_free(40.0, 94.0, True, True, [], _ctx()["pol"])
    assert sorted(round(hi - lo) for lo, hi, _c in fill["pieces"]) == [14, 39]


def test_b54_junto_do_vao_desloca_a_junta_para_o_vao():
    # B39 | B54 | vao (livre) | B39: o B54 entra no trecho do vao - fecha sem U_CUT (5 x U34)
    items = [_a(0.0, 39.0, "B39"), _a(40.0, 94.0, "B54"), ["F", 95.0, 214.0, True, True], _a(215.0, 254.0, "B39")]
    out, info = cgf._soften_items(_ctx(), items, [[0.0, 254.0, []]], 0.0, 254.0, True, True, [])
    resumo = _resumo(out)
    assert resumo[0] == ("A", "B39", 0.0, 39.0) and resumo[-1] == ("A", "B39", 215.0, 254.0)
    livre = [x for x in resumo if x[0] == "F"]
    assert livre == [("F", 40.0, 214.0)]
    meta = [it for it in out if it[0] == "F"][0][5]
    assert meta["soft"] and meta["covers"] == ["B54"]
    fill = cgf._fill_canonical(40.0, 214.0, True, True, [], _ctx()["pol"], None, True, {}, meta["free_spans"])
    assert all(c != cgf.FREE_CUT for _lo, _hi, c in fill["pieces"]), fill["pieces"]


def test_compensador_entre_blocos_inteiros_nao_vira_pastilha_de_canaleta():
    items = [_a(0.0, 39.0, "B39"), _a(40.0, 44.0, "C04"), _a(45.0, 84.0, "B39")]
    out, info = cgf._soften_items(_ctx(), items, [[0.0, 84.0, []]], 0.0, 84.0, True, True, [])
    livres = [x for x in _resumo(out) if x[0] == "F"]
    # 4 cm nao fecha sozinho: abrange um B39 (44 cm = U34 + U_CUT 9)
    assert info["absorbed"] == 1 and len(livres) == 1 and livres[0][2] - livres[0][1] == pytest.approx(44.0)


def test_trecho_livre_sobre_alvenaria_de_r_nao_amolece_a_junta_dura():
    """Borda da janela no meio de um bloco de r (flanco que nao segue a grade, 86.12): o trecho
    livre [620-649] fica sobre o B39 [620-659] de r - a junta B39|B39 (619,5) continua DURA e o
    bloco ancorado nao e' abrangido (medido na mini-planta: W0 f4, U34 U34 atravessando 1619,5)."""
    cand_a = {"logical_code": "B39"}
    items = [["A", {"lo": 580.0, "hi": 619.0, "code": "B39", "cand": cand_a}], ["F", 620.0, 649.0, True, True]]
    r_rows = [{"lo": 580.0, "hi": 619.0, "cand": cand_a, "along": True, "tie": False},
              {"lo": 620.0, "hi": 659.0, "cand": {"logical_code": "B39"}, "along": True, "tie": False}]
    ctx = dict(_ctx(), r_rows=r_rows)
    out, info = cgf._soften_items(ctx, items, [[580.0, 649.0, []]], 580.0, 649.0, True, True, [])
    assert info["absorbed"] == 0 and _resumo(out) == [("A", "B39", 580.0, 619.0), ("F", 620.0, 649.0)]
    # sobre o vao de verdade (nada em r) o bloco pode ser abrangido: 69 = U34 + U34, sem U_CUT
    ctx = dict(_ctx(), r_rows=r_rows[:1])
    out, info = cgf._soften_items(ctx, items, [[580.0, 649.0, []]], 580.0, 649.0, True, True, [])
    assert info["absorbed"] == 1 and _resumo(out) == [("F", 580.0, 649.0)]
    assert cgf._vao_spans(580.0, 700.0, r_rows, 2.5) == [(659.0, 700.0)]


def test_junta_de_fronteira_coincidente_puxa_o_bloco_vizinho():
    # vao | C04 | B39 | B39: sem abranger, a junta C04|B39 (44,5) cai sobre uma junta da fiada vizinha
    items = [["F", 0.0, 39.0, False, True], _a(40.0, 44.0, "C04"), _a(45.0, 84.0, "B39"), _a(85.0, 124.0, "B39")]
    out, info = cgf._soften_items(_ctx(), items, [[0.0, 124.0, []]], 0.0, 124.0, False, True, [44.5])
    assert info["absorbed"] == 1, _resumo(out)
    out0, info0 = cgf._soften_items(_ctx(), items, [[0.0, 124.0, []]], 0.0, 124.0, False, True, [])
    assert info0["absorbed"] == 0, _resumo(out0)


# ------------------------------------------------- corridas trocadas no lugar (86.7 / verga)
def _peca(code, lo, hi, reason="STANDARD_FILL", z=241.0, wall_idx=0, course=TOP):
    origin = m.XYZ(ft((lo + hi) / 2.0), 0.0, ft(z))
    return ws._make_block_candidate(code, CAT[code], course, origin, m.XYZ(1.0, 0.0, 0.0), reason, wall_idx=wall_idx)


def test_cinta_no_lugar_sem_meia_canaleta_nem_pastilha_de_canaleta():
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    topo = [_peca("B39", 0.0, 39.0), _peca("B39", 40.0, 79.0), _peca("B19", 80.0, 99.0), _peca("B39", 100.0, 139.0),
            _peca("B39", 140.0, 179.0), _peca("C04", 180.0, 184.0), _peca("B39", 185.0, 224.0),
            _peca("B19", 225.0, 244.0), _peca("B19", 245.0, 264.0), _peca("B39", 265.0, 304.0)]
    baixo = [_peca("B39", lo, lo + 39.0, z=221.0, course=TOP - 1) for lo in (20.0, 60.0, 100.0, 140.0, 180.0, 220.0, 260.0)]
    cc = {TOP - 1: baixo, TOP: topo}
    plano = orf.plan_top_bond_beam(cc, walls, NUM)
    rows = orf._wall_strip_pieces(plano["course_candidates"][TOP], walls, 0)
    got = [(r["cand"]["logical_code"], round(r["lo"], 1), round(r["hi"], 1)) for r in rows]
    assert all(r["cand"]["logical_code"] != orf.CHANNEL_U_19 for r in rows), got
    assert not any(orf.is_half_channel_piece(r["cand"]) for r in rows), got
    # nenhum U_CUT abaixo de 9 cm (o C04 entre dois B39 nao vira canaleta de 4 cm)
    for r in rows:
        if r["cand"]["logical_code"] == orf.CHANNEL_U_CUT:
            assert r["cand"]["instance_length_cm"] >= 9.0 - 1e-6, got
    # B19 + B19 = U39 (fusao exata, sem junta nova)
    assert ("CHANNEL_U_39", 225.0, 264.0) in got
    # cobertura igual e todas as pecas viraram canaleta
    assert tcr._covered([r for r in rows]) == [(0.0, 304.0)]
    assert all(orf.is_channel_code(r["cand"]["logical_code"]) for r in rows)
    assert plano["counts"]["half_channel_resplits"] >= 2
    assert orf.channel_as_junction_bond(plano["course_candidates"]) == []


def test_recomposicao_no_lugar_unidade():
    pol = orf.channel_policy()
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    pecas = [_peca("B39", 0.0, 39.0), _peca("B19", 40.0, 59.0), _peca("B39", 60.0, 99.0)]
    linhas = orf._wall_strip_pieces(pecas, walls, 0)
    grupos = orf._group_run_members(linhas, pol)
    assert [round(g[-1]["hi"] - g[0]["lo"]) for g in grupos] == [39, 19, 39]   # B19 sem vizinha para fundir
    novos, recomp, sem = orf._avoid_half_channel_groups(grupos, [], pol, walls, 0)
    assert sem == [] and len(recomp) == 1
    comps = [round(g[-1]["hi"] - g[0]["lo"]) for g in novos]
    assert 19 not in comps and sum(comps) + len(comps) - 1 == 99
    assert all(c <= 39 for c in comps)
    # as pecas originais cobertas ficam registradas para a troca na fiada
    cobertas = [c for g in novos for c in orf.group_source_cands(g)]
    assert set(orf._physical_key(c) for c in cobertas) >= set(orf._physical_key(c) for c in pecas[1:2])
