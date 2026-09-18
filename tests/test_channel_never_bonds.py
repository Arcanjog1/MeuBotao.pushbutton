# -*- coding: utf-8 -*-
"""REGRA 75 - canaleta NUNCA exerce funcao de amarracao (L, T ou X).

Origem: revisao visual humana do smoke do PR #42 (2026-09-18) encontrou um
CHANNEL_U_34 exercendo a funcao de peca de canto (no' 48, 8284584 x 8284590) e
quatro travessias de canaleta sobre o no' com a amarracao recuada. A funcao de
amarracao pertence exclusivamente aos blocos estruturais aprovados; canaleta
pode coexistir com o encontro (cinta/verga/contraverga), nunca substituir a
peca do no'.

O hard gate e' `result["channel_as_junction_bond"]` (aceitavel SOMENTE vazio),
com deteccao por FUNCAO - razao de peca de no', marca de conversao ou registro
de travessia - nunca por distancia. Os casos de T (padrao + mutantes sob
override) estao em test_channel_reinforcement.py e test_channel_audit_fixes.py;
a regressao da secao 74 e da parede 8284580 esta em test_s74_corpus_butanta.py.

    python3 -m pytest tests/test_channel_never_bonds.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg, solve, strip = tcr.m, tcr.ft, tcr.seg, tcr.solve, tcr.strip
from core.engine import opening_reinforcement as orf  # noqa: E402

K = set(orf.CHANNEL_LOGICAL_TYPES)
TIE = orf.TIE_REASON_PREFIXES


def _canaletas_com_papel_de_no(res):
    fora = []
    for ci, cands in (res.get("course_candidates") or {}).items():
        for c in cands:
            if c.get("logical_code") in K and any(
                    str(c.get("placement_reason") or "").startswith(p) for p in TIE):
                fora.append((ci, c.get("logical_code"), c.get("placement_reason")))
    return fora


# ======================================================= L + canaleta
def canto_com_contraverga():
    """L modular com janela cuja fiada de contraverga corre ate' perto do
    canto - a topologia do caso real (no' 48, 8284584 x 8284590). Comprimentos
    escolhidos para fechar modularmente com a extensao de 7 cm do canto."""
    lines = [seg(0, 0, 402, 0), seg(0, 0, 0, 298)]
    # peitoril em 100 -> contraverga na fiada 4; jamba a 1 cm do bloco de canto
    return lines, [[(ft(35.0), ft(155.0), ft(100.0), ft(221.0))], []]


def test_L_com_contraverga_mantem_o_bloco_de_canto():
    res, walls, _n, _o = solve(*canto_com_contraverga())
    assert res["channel_as_junction_bond"] == []
    assert res["opening_reinforcement"]["tie_conversions"] == []
    assert _canaletas_com_papel_de_no(res) == []
    cantos = [c for v in res["course_candidates"].values() for c in v
              if str(c.get("placement_reason") or "").startswith(("L_CORNER", "CORNER"))]
    assert cantos, "a fixture precisa produzir pecas de canto"
    assert all(c["logical_code"] not in K for c in cantos)


# O mutante da CONVERSAO (amarracao -> canaleta, o caso real do no' 48) esta'
# em test_channel_audit_fixes.test_green_parity_com_override_reproduz_o_humano_
# e_o_gate_acusa e em test_channel_reinforcement.test_split_do_b54_so_sob_
# override_e_o_gate_acusa; o da TRAVESSIA em test_travessia_51_6_so_sob_
# override_explicito_e_o_gate_acusa; e o de peca FORJADA (K34 no papel de tie,
# item 13 da missao) logo abaixo. Nao ha' mecanismo sem mutante.


# ======================================================= X + canaleta
def cruz_com_verga():
    """Cruz (parede atravessando outra no meio) com janela cuja verga corre na
    parede continua, perto do cruzamento."""
    lines = [seg(0, 150, 604, 150), seg(302, 0, 302, 300)]
    return lines, [[(ft(100.0), ft(220.0), ft(100.0), ft(221.0))], []]


def test_X_com_verga_nao_poe_canaleta_no_papel_do_no():
    res, walls, _n, _o = solve(*cruz_com_verga())
    assert res["channel_as_junction_bond"] == []
    assert _canaletas_com_papel_de_no(res) == []
    # a fixture tem de ter canaleta em algum lugar (senao o teste e' vacuo)
    assert tcr.channel_count(res) > 0


# ==================================== canaleta PERTO do no', fora do envelope
def test_canaleta_perto_do_no_mas_fora_do_envelope_e_permitida():
    """Prova de que a regra NAO e' proibicao por distancia: com a jamba a
    78 cm do eixo do T a corrida existe, chega perto do no' e nada e' acusado."""
    lines, ops = tcr.tee(sill_cm=80.0, jamb_t_cm=380.0)
    res, walls, _n, _o = solve(lines, ops)
    rein = res["opening_reinforcement"]
    rec = rein["openings"][0]
    assert rec["above"]["status"] == "CHANNEL"
    assert tcr.channel_count(res) > 0
    assert rein["node_crossings"] == [] and rein["tie_conversions"] == []
    assert res["channel_as_junction_bond"] == []


# ========================================= mutante direto do VALIDADOR
def test_validador_acusa_peca_forjada_e_volta_a_zero_com_a_peca_certa():
    """Item 13 da missao: forcar uma K34 no papel de amarracao tem de FALHAR o
    gate; restaurar a peca certa tem de voltar a zero."""
    lines, ops = tcr.tee(sill_cm=80.0)
    res, _w, _n, _o = solve(lines, ops)
    cc = dict((ci, [dict(c) for c in v]) for ci, v in res["course_candidates"].items())
    assert orf.channel_as_junction_bond(cc, None) == []
    forjadas = 0
    for v in cc.values():
        for c in v:
            if forjadas == 0 and str(c.get("placement_reason") or "").startswith("T_INTERSECTION_INCOMING"):
                c["logical_code"] = orf.CHANNEL_U_34          # K34/U34 no papel de tie
                forjadas += 1
    assert forjadas == 1
    violacoes = orf.channel_as_junction_bond(cc, None)
    assert violacoes and violacoes[0]["kind"] == "CHANNEL_PIECE_WITH_TIE_ROLE"
    assert violacoes[0]["logical_code"] == orf.CHANNEL_U_34
    # restaura a peca certa -> volta a zero
    for v in cc.values():
        for c in v:
            if c.get("logical_code") == orf.CHANNEL_U_34 and str(
                    c.get("placement_reason") or "").startswith("T_INTERSECTION_INCOMING"):
                c["logical_code"] = "B34"
    assert orf.channel_as_junction_bond(cc, None) == []


def test_validador_cobre_todos_os_codigos_de_canaleta():
    """O gate nao depende do rotulo visual U: cobre TODOS os codigos K do
    sistema, inclusive corte e pseudo-pecas de travessia/split."""
    base = {"placement_reason": "L_CORNER", "wall_idx": 0, "node_index": 1}
    for code in sorted(orf.CHANNEL_LOGICAL_TYPES) + [orf.TIE_SPLIT_CODE, orf.CROSSING_CODE]:
        cc = {0: [dict(base, logical_code=code)]}
        assert orf.channel_as_junction_bond(cc, None), code
    assert orf.channel_as_junction_bond({0: [dict(base, logical_code="B54")]}, None) == []


def test_o_gate_le_os_registros_do_laudo_alem_das_pecas():
    laudo = {"tie_conversions": [{"course_index": 1, "wall_idx": 0, "node_index": 48,
                                  "mode": "SAME_GEOMETRY", "code": "B34"}],
             "node_crossings": [{"course_index": 3, "main_wall_idx": 0,
                                 "incoming_wall_idx": 1, "node_index": 22}]}
    tipos = sorted(v["kind"] for v in orf.channel_as_junction_bond({}, laudo))
    assert tipos == ["CHANNEL_CROSSED_NODE_TIE", "TIE_CONVERTED_TO_CHANNEL"]


def test_politica_padrao_do_motor_e_a_da_regra_75():
    politica = orf.channel_policy()
    assert politica["convert_blocking_along_ties"] is False
    assert politica["channel_may_cross_node_tie"] is False
