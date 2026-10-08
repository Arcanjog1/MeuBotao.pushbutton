# -*- coding: utf-8 -*-
"""SECAO 86.16 (correcao do usuario 2026-10-08) - B54 DA ULTIMA FIADA = U34 + U19.

Palavras do usuario: "bloco 54 na ultima fiada deve virar uma canaleta 34 e uma
canaleta 19". REGRA OBRIGATORIA (chave `opening_reinforcement.TOP_BOND_BEAM_B54_AS_CHANNEL`):

- na ultima fiada (cinta de topo, TOP_BOND_BEAM) TODO B54 - inclusive o B54 de
  amarracao do no' T - vira U34 + U19; a U19 (meia canaleta) so' existe nesse caso,
  o resto da 86.14 continua;
- junta U34|U19: desencontrada das juntas da fiada c-1, coerente com a grade da c-2;
- o B34 de amarracao no quadrado do no' continua BLOCO (variante A da 86.7);
- excecao a' regra 75 / 76.1 so' para essas pecas: os gates aprovam.

    py -3 -m pytest tests/test_b54_cinta_86_16.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
CAT = tcr.sb.CATALOG
NUM = 13
TOP = NUM - 1
ESTRATEGIAS = [None, tcr.CHANNEL]


def _l_corner():
    return ([seg(0, 0, 400, 0), seg(0, 0, 0, 300), seg(400, 0, 400, 300)],
            [[(ft(150), ft(270), ft(100), ft(221))], [], []])


FIXTURES = {"tee": lambda: tcr.tee(80.0), "l_corner": _l_corner}
_CACHE = {}


def _solve(nome, estrategia=None, b54=True, fresh=False):
    chave = (nome, estrategia, b54)
    if fresh or chave not in _CACHE:
        antes = orf.TOP_BOND_BEAM_B54_AS_CHANNEL
        orf.TOP_BOND_BEAM_B54_AS_CHANNEL = b54
        try:
            lines, ops = FIXTURES[nome]()
            out = tcr.solve(lines, ops, strategy=estrategia, num_courses=NUM)
        finally:
            orf.TOP_BOND_BEAM_B54_AS_CHANNEL = antes
        if fresh:
            return out
        _CACHE[chave] = out
    return _CACHE[chave]


def _rows(res, walls, wi, ci):
    return [r for r in orf._wall_strip_pieces(res["course_candidates"].get(ci) or [], walls, wi) if r["along"]]


def _sig(res, ci):
    return sorted(orf._physical_key(c) for c in res["course_candidates"].get(ci) or [])


def test_chave_ligada_por_padrao():
    assert orf.TOP_BOND_BEAM_B54_AS_CHANNEL is True and orf.b54_cinta_enabled()
    assert orf.CHANNEL_HALF_U19_ENABLED is False          # a 86.14 continua valendo
    assert orf.B54_CINTA_SPLIT_LENGTHS_CM == (34.0, 19.0)


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_b54_de_amarracao_do_t_na_ultima_fiada_vira_u34_e_u19(estrategia):
    res, walls, nodes, openings = _solve("tee", estrategia)
    sem, walls0, _n0, _o0 = _solve("tee", estrategia, b54=False)
    # sem a 86.16 o B54 do no' T fica bloco na ultima fiada
    b54_antes = [r for wi in range(len(walls0)) for r in _rows(sem, walls0, wi, TOP)
                 if r["cand"]["logical_code"] == "B54" and r["tie"]]
    assert b54_antes
    # com a 86.16: nenhum B54 na ultima fiada; no lugar dele U34 + U19 com a mesma extensao
    assert not [c for c in res["course_candidates"][TOP] if c["logical_code"] == "B54"]
    for velho in b54_antes:
        novos = [r for w in range(len(walls)) for r in _rows(res, walls, w, TOP)
                 if orf.is_b54_cinta_piece(r["cand"]) and r["lo"] >= velho["lo"] - 0.6 and r["hi"] <= velho["hi"] + 0.6]
        assert sorted(r["cand"]["logical_code"] for r in novos) == [orf.CHANNEL_U_19, orf.CHANNEL_U_34], novos
        assert min(r["lo"] for r in novos) == pytest.approx(velho["lo"], abs=0.6)
        assert max(r["hi"] for r in novos) == pytest.approx(velho["hi"], abs=0.6)
        assert all(r["cand"]["reinforcement"]["b54_tie"] for r in novos)
    counts = res["top_bond_beam"]["counts"]
    assert counts["b54_cinta_tie_split"] >= 1
    # a junta U34|U19 no T cai na face da parede que chega (a c-1 tem a peca transversal): registrada
    assert any(f["code"] == "TOP_BOND_BEAM_B54_JOINT_COINCIDENT" and f["tie"] for f in res["top_bond_beam"]["findings"])


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_gates_aprovam_a_excecao_do_b54_da_cinta(estrategia):
    res, walls, nodes, openings = _solve("tee", estrategia)
    sem, _w0, _n0, _o0 = _solve("tee", estrategia, b54=False)
    assert res["channel_as_junction_bond"] == []                                   # regra 75
    assert len(res.get("missing_required_junction_bond") or []) == \
        len(sem.get("missing_required_junction_bond") or [])                     # regra 76.1
    audit = res["top_bond_beam"]["audit"]["counts"]
    assert audit["TOP_BOND_BEAM_CHANNEL_AT_NODE"] == 0 and audit["TOP_BOND_BEAM_TIE_ROLE"] == 0
    assert audit["b54_cinta_at_node"] >= 1
    val = res["opening_reinforcement"]["validation"]["counts"]
    for key in ("CHANNEL_HALF_PIECE", "CHANNEL_COLLISION", "CHANNEL_INVADES_OPENING", "MISSING_REQUIRED_CHANNEL"):
        assert val[key] == 0, key
    meia = orf.half_channel_audit(res["course_candidates"])["counts"]
    assert meia["total"] == 0 and meia["CHANNEL_U_19_B54_CINTA"] >= 1
    assert res["channel_grid_follow"]["half_channel_audit"]["counts"]["total"] == 0
    assert all(a.get("ok") for a in res.get("wall_bond_audits") or [] if isinstance(a, dict))
    pf = m.controlled_beta_preflight(res, walls, openings, CAT, 0.0)
    plano = m.materialization_plan(res, pf)
    assert not pf.get("opening_violations") and not pf.get("collisions") and not plano["skip"]
    # a auditoria 76.1 sem a excecao reprovaria o no' da ultima fiada (teste nao vacuo)
    antes = orf.TOP_BOND_BEAM_B54_AS_CHANNEL
    orf.TOP_BOND_BEAM_B54_AS_CHANNEL = False
    try:
        assert not orf.is_b54_cinta_piece([c for c in res["course_candidates"][TOP]
                                           if c["logical_code"] == orf.CHANNEL_U_19][0])
        assert orf.channel_as_junction_bond(res["course_candidates"]) == []   # razao propria, nao e' amarracao
    finally:
        orf.TOP_BOND_BEAM_B54_AS_CHANNEL = antes


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_nenhuma_u19_fora_do_b54_da_cinta(estrategia):
    for nome in FIXTURES:
        res, _w, _n, _o = _solve(nome, estrategia)
        for ci, pecas in res["course_candidates"].items():
            for c in pecas:
                if orf.is_half_channel_piece(c):
                    assert ci == TOP and orf.is_b54_cinta_piece(c), (nome, ci, c.get("logical_code"))


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_b34_de_amarracao_no_no_continua_bloco(estrategia):
    res, walls, nodes, _o = _solve("l_corner", estrategia)
    sem, walls0, _n0, _o0 = _solve("l_corner", estrategia, b54=False)
    amarr = lambda r_: sorted(orf._physical_key(c) for c in r_["course_candidates"][TOP]
                              if orf._is_tie(c) and c["logical_code"] == "B34")
    assert amarr(res) and amarr(res) == amarr(sem)
    for wi in range(len(walls)):
        quadrados = orf._node_squares_cm(walls, nodes, wi)
        for r in _rows(res, walls, wi, TOP):
            if orf._square_hit(r["lo"], r["hi"], quadrados, 0.5) is not None and r["cand"]["logical_code"] == "B34":
                assert not orf.is_channel_code(r["cand"]["logical_code"])
    assert orf.half_channel_audit(res["course_candidates"])["counts"]["CHANNEL_U_19_B54_CINTA"] == 0


# ------------------------------------------------------------------ planejador isolado
def _peca(code, lo, hi, reason="STANDARD_FILL", z=241.0, wall_idx=0, course=TOP):
    origin = m.XYZ(ft((lo + hi) / 2.0), 0.0, ft(z))
    return ws._make_block_candidate(code, CAT[code], course, origin, m.XYZ(1.0, 0.0, 0.0), reason, wall_idx=wall_idx)


def _plano(baixo_lo, grade_lo=None):
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    topo = [_peca("B39", 0.0, 39.0), _peca("B39", 40.0, 79.0), _peca("B54", 80.0, 134.0), _peca("B39", 135.0, 174.0)]
    baixo = [_peca("B39", lo, lo + 39.0, z=221.0, course=TOP - 1) for lo in baixo_lo]
    cc = {TOP - 1: baixo, TOP: topo}
    if grade_lo is not None:
        cc[TOP - 2] = [_peca("B39", lo, lo + 39.0, z=201.0, course=TOP - 2) for lo in grade_lo]
    return orf.plan_top_bond_beam(cc, walls, NUM), walls


def test_b54_de_preenchimento_na_ultima_fiada_vira_u34_e_u19():
    plano, walls = _plano((0.0, 40.0, 80.0, 120.0))          # juntas de c-1: 39,5 79,5 119,5
    rows = orf._wall_strip_pieces(plano["course_candidates"][TOP], walls, 0)
    got = [(r["cand"]["logical_code"], round(r["lo"], 1), round(r["hi"], 1)) for r in rows]
    parte = [g for g in got if 80.0 - 0.1 <= g[1] and g[2] <= 134.0 + 0.1]
    assert sorted(g[0] for g in parte) == [orf.CHANNEL_U_19, orf.CHANNEL_U_34], got
    # 34|19 -> junta 114,5 (5 da junta 119,5); 19|34 -> 99,5 (20): a mais desencontrada
    assert parte == [(orf.CHANNEL_U_19, 80.0, 99.0), (orf.CHANNEL_U_34, 100.0, 134.0)]
    assert all(orf.is_b54_cinta_piece(r["cand"]) for r in rows if 80.0 - 0.1 <= r["lo"] and r["hi"] <= 134.1)
    assert all(not r["cand"]["reinforcement"]["b54_tie"] for r in rows if orf.is_b54_cinta_piece(r["cand"]))
    assert orf.channel_as_junction_bond(plano["course_candidates"]) == []
    assert orf.half_channel_audit(plano["course_candidates"])["counts"] == {
        "CHANNEL_U_19": 0, "CHANNEL_U_CUT_19": 0, "total": 0, "CHANNEL_U_19_B54_CINTA": 1}


def test_junta_coerente_com_a_grade_desempata():
    # c-1 sem junta perto do B54: as duas divisoes desencontram; a da grade de c-2 (114,5) vence
    plano, walls = _plano((20.0, 160.0), grade_lo=(75.5, 115.0))
    rows = orf._wall_strip_pieces(plano["course_candidates"][TOP], walls, 0)
    parte = [(r["cand"]["logical_code"], round(r["lo"], 1), round(r["hi"], 1)) for r in rows
             if 80.0 - 0.1 <= r["lo"] and r["hi"] <= 134.1]
    assert parte == [(orf.CHANNEL_U_34, 80.0, 114.0), (orf.CHANNEL_U_19, 115.0, 134.0)]


def test_chave_desligada_volta_a_86_14(monkeypatch):
    monkeypatch.setattr(orf, "TOP_BOND_BEAM_B54_AS_CHANNEL", False)
    plano, walls = _plano((0.0, 40.0, 80.0, 120.0))
    rows = orf._wall_strip_pieces(plano["course_candidates"][TOP], walls, 0)
    assert not any(r["cand"]["logical_code"] == orf.CHANNEL_U_19 for r in rows)
    assert orf.half_channel_audit(plano["course_candidates"])["counts"]["CHANNEL_U_19_B54_CINTA"] == 0


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_determinismo(estrategia):
    a, _w, _n, _o = _solve("tee", estrategia)
    b, _w2, _n2, _o2 = _solve("tee", estrategia, fresh=True)
    for ci in range(NUM):
        assert _sig(a, ci) == _sig(b, ci), ci
    assert a["top_bond_beam"]["runs"] == b["top_bond_beam"]["runs"]
