# -*- coding: utf-8 -*-
"""D16 (2026-09-25, REVISAO HUMANA; sem mudanca de codigo): a corrida de verga /
contraverga que chega num encontro T para na peca que E' a amarracao daquela fiada.
Estes testes fixam a evidencia medida no ciclo D16 (REGRAS secao 75.1):

- a parada acontece na amarracao selecionada do no' naquela fiada (bond_trace
  BOND_RESOLVED), nunca numa peca qualquer "perto" do no';
- continuar a canaleta pela regiao do no' ocuparia o MESMO volume da amarracao
  (colisao > 0,1 cm) - nao existe travessia com amarracao independente;
- a unica travessia possivel (51.6, suspensa pela regra 75) tira a B34/B54 do no'
  naquela fiada: o no' fica sem amarracao e o gate 75 acusa;
- a canaleta nunca resolve o no' (bond_resolved ignora canaleta);
- jamba longe do no' nao para; no' nao resolvido continua nao resolvido.

Fixtures sinteticas (nenhum ID do projeto): o T modular de
test_channel_reinforcement (principal de 604 cm, parede que chega em t=302, faces
em 295/309) com a jamba na face (T20-like), jambas nas DUAS faces (T26-like: o
pilar entre os vaos e' o proprio no') e jamba a 5 cm da face (T28-like); e o U dos
cantos L 55/56 (no' nao resolvido).

    python3 -m pytest tests/test_d16_canaleta_no_t.py -q
"""
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

m, ft, seg = tcr.m, tcr.ft, tcr.seg
CAT = tcr.sb.CATALOG
NUM = tcr.NUM_COURSES
T_NODE = 302.0      # eixo da parede que chega, ao longo da principal
FACE_R = 309.0      # face da parede que chega do lado direito
FACE_L = 295.0      # face do lado esquerdo


def _lines():
    return [seg(-302, 0, 302, 0), seg(0, 0, 0, 298)]


def _t20_like(jamba=FACE_R, sill=80.0):
    """Janela com a jamba esquerda em `jamba` (na face da parede que chega)."""
    return _lines(), [[(ft(jamba), ft(jamba + 145.0), ft(sill), ft(221))], []]


def _t26_like(sill=80.0):
    """Duas janelas com as jambas nas DUAS faces: o pilar entre elas e' o no'."""
    return _lines(), [[(ft(FACE_L - 145.0), ft(FACE_L), ft(sill), ft(221)),
                       (ft(FACE_R), ft(FACE_R + 145.0), ft(sill), ft(221))], []]


def _u_55_56():
    lines = [seg(0, 0, 101.0, 0), seg(0, 0, 0, -242.0), seg(101.0, 0, 101.0, -242.0)]
    return lines, [[(ft(19.5), ft(115.0 - 29.5), ft(40.0), ft(91.0))], [], []]


def _solve(fixture, estrategia=None, travessia=False, limite=0.0, reverse=False):
    """`travessia=True` religa a 51.6 SO' para medir o que ela faria (mutante)."""
    lines, ops = fixture
    real = orf.plan_channel_reinforcement

    def wrapped(*a, **k):
        if travessia:
            pol = dict(k.get("policy") or {})
            pol["channel_may_cross_node_tie"] = True
            pol["cross_tee_when_support_at_most_cm"] = limite
            k["policy"] = pol
        return real(*a, **k)

    orf.plan_channel_reinforcement = wrapped
    try:
        return tcr.solve(lines, ops, strategy=estrategia, reverse=reverse)
    finally:
        orf.plan_channel_reinforcement = real


def _node(nodes, kind="T_INTERSECTION"):
    return [i for i, n in enumerate(nodes) if n.get("kind") == kind][0]


def _bond_row(res, node, ci):
    return [r for r in res["bond_trace"] if r["node_index"] == node and r["course"] == ci][0]


def _sem_48(res, walls, openings):
    pf = m.controlled_beta_preflight(res, walls, openings, CAT, 0.0)
    return not pf.get("opening_violations") and not m.materialization_plan(res, pf)["skip"]


def _bloqueio(res, walls, node, ci):
    tira = orf._wall_strip_pieces(res["course_candidates"][ci], walls, 0)
    return [r for r in tira if r["tie"] and r["cand"].get("node_index") == node]


# ------------------------------------------------------------------ a parada e' na amarracao
@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
@pytest.mark.parametrize("reverse", [False, True])
def test_t20_like_verga_e_contraverga_param_na_amarracao_da_fiada(estrategia, reverse):
    res, walls, nodes, openings = _solve(_t20_like(), estrategia, reverse=reverse)
    t = _node(nodes)
    linha = res["opening_structural_trace"][0]
    assert linha["lintel_status"] == m.LINTEL_CREATED and linha["sill_status"] == m.SILL_REINFORCEMENT_CREATED
    for papel in ("lintel", "sill"):
        assert t in linha[papel + "_junction_ids"]
        assert min(linha[papel + "_left_support"], linha[papel + "_right_support"]) <= 0.5
        ci = linha[papel + "_course"]
        row = _bond_row(res, t, ci)
        assert row["bond_resolved"] is True and row["selected"]["code"] in ws.JUNCTION_BOND_CODES
        bloqueio = _bloqueio(res, walls, t, ci)
        # a peca que parou a corrida e' a amarracao selecionada (transversal da chegada,
        # atravessando toda a espessura da principal no quadrado do no')
        assert bloqueio and all(not r["along"] and r["cand"]["logical_code"] == row["selected"]["code"]
                                and r["cand"]["placement_reason"] == row["selected"]["placement_reason"]
                                for r in bloqueio)
        centro = (bloqueio[0]["lo"] + bloqueio[0]["hi"]) / 2.0
        assert abs(centro - ((604.0 - T_NODE) if reverse else T_NODE)) < 0.6
    paradas = res["channel_stopped_by_junction"]
    assert paradas and all(p["junction_id"] == t and p["reason"] == "RULE_75" for p in paradas)
    assert res["channel_as_junction_bond"] == [] and res["missing_required_junction_bond"] == []
    assert _sem_48(res, walls, openings)


@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_t26_like_as_duas_corridas_param_na_mesma_amarracao(estrategia):
    """Pilar = no': as duas corridas (verga e contraverga das duas janelas) param na
    MESMA peca, que e' a amarracao da fiada; nenhuma atravessa, o no' continua
    amarrado."""
    res, walls, nodes, openings = _solve(_t26_like(), estrategia)
    t = _node(nodes)
    linhas = sorted(res["opening_structural_trace"], key=lambda r: r["opening_index"])
    assert len(linhas) == 2
    for linha in linhas:
        for papel in ("lintel", "sill"):
            assert linha[papel + "_status"].endswith("_CREATED")
            assert t in linha[papel + "_junction_ids"]
            assert min(linha[papel + "_left_support"], linha[papel + "_right_support"]) <= 0.5
    for ci in (linhas[0]["lintel_course"], linhas[0]["sill_course"]):
        assert _bond_row(res, t, ci)["bond_resolved"] is True
        assert len(_bloqueio(res, walls, t, ci)) == 1
    assert res["opening_reinforcement"]["node_crossings"] == []
    assert res["channel_as_junction_bond"] == []
    # a verga/contraverga nao muda NENHUMA fiada do no': as amarracoes sao as mesmas do
    # motor sem a secao 80 (nesta geometria o NONE ja' tem fiadas FREE_END_NOT_COMPOSED
    # entre as duas janelas, independentes da canaleta)
    antes = m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED
    m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = False
    try:
        base, _w0, _n0, _o0 = _solve(_t26_like(), estrategia)
    finally:
        m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = antes
    assert res["missing_required_junction_bond"] == base["missing_required_junction_bond"]
    assert not any(x["course_index"] in (linhas[0]["lintel_course"], linhas[0]["sill_course"])
                   for x in res["missing_required_junction_bond"])
    assert _sem_48(res, walls, openings)


def test_t28_like_jamba_a_5_cm_da_face_para_com_o_apoio_que_sobra():
    res, walls, nodes, openings = _solve(_t20_like(jamba=FACE_R + 5.0))
    t = _node(nodes)
    linha = res["opening_structural_trace"][0]
    lado = min(linha["lintel_left_support"], linha["lintel_right_support"])
    assert 3.0 <= lado <= 5.0 and t in linha["lintel_junction_ids"]
    assert _bond_row(res, t, linha["lintel_course"])["bond_resolved"] is True
    assert _sem_48(res, walls, openings)


def test_jamba_longe_do_no_nao_para():
    res, walls, nodes, openings = _solve(_t20_like(jamba=FACE_R + 40.0))
    linha = res["opening_structural_trace"][0]
    assert linha["lintel_stopped_by_junction"] is False and linha["sill_stopped_by_junction"] is False
    assert min(linha["lintel_left_support"], linha["lintel_right_support"]) >= 19.0 - 1e-6
    assert res["channel_stopped_by_junction"] == []


# ------------------------------------------------------------------ reserva geometrica do no'
@pytest.mark.parametrize("papel", ["lintel", "sill"])
def test_continuar_a_canaleta_ocupa_o_volume_da_amarracao(papel):
    """RESERVA GEOMETRICA: a canaleta estendida sobre o trecho do no' (mesma fiada,
    largura da principal) e a amarracao ocupam o MESMO volume: colisao, nao
    coexistencia. Nao existe travessia com amarracao independente."""
    res, walls, nodes, _o = _solve(_t20_like())
    t = _node(nodes)
    ci = res["opening_structural_trace"][0][papel + "_course"]
    tira = orf._wall_strip_pieces(res["course_candidates"][ci], walls, 0)
    tie = [r for r in tira if r["tie"] and r["cand"].get("node_index") == t][0]
    canal = [r for r in tira if orf.is_channel_code(r["cand"]["logical_code"])][0]
    extensao = dict(canal["cand"])
    p0, _p1, wdir, _l, _th = ws._wall_axis_and_length(walls, 0)
    atual = (extensao["origin_world"] - p0).DotProduct(wdir)
    extensao["origin_world"] = extensao["origin_world"] + wdir * (ws._cm_to_ft((tie["lo"] + tie["hi"]) / 2.0) - atual)
    extensao["length_cm"] = tie["hi"] - tie["lo"]
    assert ws._obb_min_overlap(ws._candidate_obb(extensao), ws._candidate_obb(tie["cand"])) > ws.BOND_COLLISION_EPS_FT


# ------------------------------------------------------------------ a travessia tira a amarracao
@pytest.mark.parametrize("fixture", ["t20", "t26"])
def test_travessia_51_6_tira_a_amarracao_e_o_gate_75_acusa(fixture):
    """MUTANTE (o que o HUMANO faz no BUTANTA): para a canaleta passar, a B34 da parede
    que chega recua ate' a face (B19) - o no' fica SEM B34/B54 naquela fiada. Apoio
    melhora, amarracao some, gate 75 acusa. Por isso a 51.6 esta' suspensa."""
    geo = _t20_like() if fixture == "t20" else _t26_like()
    res, walls, nodes, openings = _solve(geo, travessia=True)
    t = _node(nodes)
    cruz = res["opening_reinforcement"]["node_crossings"]
    assert cruz and all((x["removed_code"], x["added_code"]) == ("B34", "B19") for x in cruz)
    for x in cruz:
        assert _bond_row(res, t, x["course_index"])["bond_resolved"] is False
        assert any(mm["node_index"] == t and mm["course_index"] == x["course_index"]
                   for mm in res["missing_required_junction_bond"])
    assert [v["kind"] for v in res["channel_as_junction_bond"]].count("CHANNEL_CROSSED_NODE_TIE") == len(cruz)
    assert _sem_48(res, walls, openings)


def test_travessia_com_limite_de_4_cm_tambem_tira_a_amarracao():
    res, _w, nodes, _o = _solve(_t20_like(jamba=FACE_R + 5.0), travessia=True, limite=4.5)
    t = _node(nodes)
    assert any(mm["node_index"] == t for mm in res["missing_required_junction_bond"])
    assert any(v["kind"] == "CHANNEL_CROSSED_NODE_TIE" for v in res["channel_as_junction_bond"])


def test_modelo_a_literal_nao_deixa_nenhuma_travessia():
    """MODELO A (travessia so' se o no' continuar amarrado): toda travessia da 51.6
    deixa o no' sem amarracao naquela fiada - nenhuma sobra."""
    res, _w, nodes, _o = _solve(_t26_like(), travessia=True)
    t = _node(nodes)
    sobram = [x for x in res["opening_reinforcement"]["node_crossings"]
              if _bond_row(res, t, x["course_index"])["bond_resolved"]]
    assert res["opening_reinforcement"]["node_crossings"] and sobram == []


# ------------------------------------------------------------------ canaleta nunca amarra
@pytest.mark.parametrize("papel", ["lintel", "sill"])
def test_canaleta_no_lugar_da_amarracao_nunca_resolve_o_no(papel):
    res, walls, nodes, openings = _solve(_t20_like())
    t = _node(nodes)
    ci = res["opening_structural_trace"][0][papel + "_course"]
    copia = dict(res)
    copia["course_candidates"] = dict((k, list(v)) for k, v in res["course_candidates"].items())
    for i, c in enumerate(copia["course_candidates"][ci]):
        if c.get("node_index") == t and c["logical_code"] in ws.JUNCTION_BOND_CODES:
            copia["course_candidates"][ci][i] = dict(c, logical_code=orf.CHANNEL_U_34)
    assert orf.channel_as_junction_bond(copia["course_candidates"], None)
    audit = m._junction_bond_audit_final(copia, nodes, walls, openings, CAT, 0.0, NUM, None)
    assert any(x["node_index"] == t and x["course_index"] == ci for x in audit["missing"])


@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
def test_no_nao_resolvido_continua_nao_resolvido_com_canaleta_perto(estrategia):
    """U dos cantos L 55/56: a contraverga fica sem solucao (regra 75) e as fiadas
    sem amarracao do canto continuam exatamente as mesmas - a canaleta nunca apaga
    o BOND_UNRESOLVED."""
    res, walls, nodes, openings = _solve(_u_55_56(), estrategia)
    linha = res["opening_structural_trace"][0]
    assert linha["sill_status"] == m.SILL_REINFORCEMENT_UNRESOLVED
    antes = m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED
    m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = False
    try:
        base, _w0, _n0, _o0 = _solve(_u_55_56(), estrategia)
    finally:
        m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = antes
    assert res["missing_required_junction_bond"] == base["missing_required_junction_bond"]
    for x in res["missing_required_junction_bond"]:
        assert _bond_row(res, x["node_index"], x["course_index"])["bond_resolved"] is False
    assert res["channel_as_junction_bond"] == []
    assert _sem_48(res, walls, openings)


# ------------------------------------------------------------------ sem hardcode
def test_parada_por_no_nao_depende_de_identificador():
    fontes = "\n".join(inspect.getsource(f) for f in (orf._extend_run, orf._is_tie, orf._wall_strip_pieces,
                                                      orf.channel_as_junction_bond))
    assert "8284" not in fontes and "BUTANT" not in fontes.upper()
    assert not re.search(r"(node_index|wall_idx|opening_index)\s*==\s*\d", fontes)
