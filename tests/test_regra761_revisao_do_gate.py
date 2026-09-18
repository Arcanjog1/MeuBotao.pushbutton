# -*- coding: utf-8 -*-
"""REGRA 76.1 - defeitos do gate MISSING_REQUIRED_JUNCTION_BOND achados pela
revisao adversarial e corrigidos (2026-09-18). Cada teste reproduz o defeito
medido e fixa a correcao:

  1. `non_modular` do motor grava "course" = FAMILIA ("A"/"B") por banda; o gate
     procurava pela fiada fisica e o criterio "fora de trecho nao-modular"
     nunca disparava. Agora wall_modeling._non_modular_by_physical_course
     converte cada entrada pela PROPRIA banda.
  2. "cobre a regiao inteira" era um orcamento de AREA (aceitava 0,20 cm de
     falta numa face, 4x a tolerancia). Agora e' exato: todo ponto a mais de
     0,05 cm da borda tem de estar coberto.
  3. Parede mais espessa que o bloco (19 x bloco de 14): a regiao do no' era
     14 x 19 e nenhuma peca a cobria. Agora a regiao e' medida na faixa de
     ALVENARIA (largura do bloco de amarracao do catalogo).

    python3 -m pytest tests/test_regra761_revisao_do_gate.py -q
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_channel_reinforcement as tcr  # noqa: E402
from test_missing_required_junction_bond import porta  # noqa: E402

m, ft, seg, sb = tcr.m, tcr.ft, tcr.seg, tcr.sb
from core.engine import wall_stepper as ws  # noqa: E402


def _solve_espessuras(lines, espessuras, openings=None):
    walls = [(line, ft(t), (False, False)) for line, t in zip(lines, espessuras)]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    res = m.solve_building_blocks_all_courses(
        nodes, walls, e2n, openings or [[] for _ in lines], sb.CATALOG, 0.0, 14,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
        opening_reinforcement_strategy=tcr.CHANNEL)
    return res, walls, nodes


# ------------------------------------------------ 1. non_modular por familia
def test_o_non_modular_do_motor_grava_a_familia_e_o_gate_recebe_a_fiada_fisica():
    res, walls, nodes, _o = tcr.solve([seg(0, 0, 600, 0), seg(0, 0, 0, 298)],
                                      [[porta(100, 190), porta(195, 300)], []])
    familias = set(e["course"] for e in res["non_modular"])
    assert familias <= {"A", "B"} and familias, familias
    fis = m._non_modular_by_physical_course(res)
    assert fis and all(isinstance(e["course"], int) for e in fis)
    assert all(e["course"] in res["course_candidates"] for e in fis)
    # a letra da entrada original e' a paridade da fiada fisica
    origem = set((e["wall_idx"], e["seg_start_cm"], e["seg_end_cm"], e["course"]) for e in res["non_modular"])
    for e in fis:
        letra = "A" if e["course"] % 2 == 0 else "B"
        assert (e["wall_idx"], e["seg_start_cm"], e["seg_end_cm"], letra) in origem, e


def test_trecho_nao_modular_no_formato_do_motor_desqualifica_a_amarracao_no_gate_final():
    """Uma entrada de `non_modular` com a FAMILIA (formato do motor) sobre o
    B34 de canto desqualifica a amarracao nas fiadas fisicas daquela familia."""
    res, walls, nodes, _o = tcr.solve([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[], []])
    base = m._junction_bond_audit_final(res, nodes, walls, [[], []], sb.CATALOG, 0.0, 14, None)
    assert base["missing"] == []
    cc = res["course_candidates"]
    b34 = [c for c in cc[0] if c.get("logical_code") == "B34"
           and str(c.get("placement_reason")).startswith("L_CORNER")][0]
    entrada = {"wall_idx": b34["wall_idx"], "course": "A", "seg_start_cm": 0.0, "seg_end_cm": 40.0}
    res2 = dict(res, non_modular=[entrada], bands=[])
    audit = m._junction_bond_audit_final(res2, nodes, walls, [[], []], sb.CATALOG, 0.0, 14, None)
    fiadas = sorted(f["course_index"] for f in audit["missing"] if f["reason"] == "BOND_PIECE_NON_MODULAR")
    assert fiadas and all(ci % 2 == 0 for ci in fiadas), fiadas


# ---------------------------------------------------- 2. regiao inteira exata
@pytest.mark.parametrize("recuo_cm,valido", [(0.0, True), (0.04, True), (0.06, False), (0.15, False)])
def test_cobertura_inteira_e_exata_so_uma_faixa_de_0_05_cm_pode_faltar(recuo_cm, valido):
    res, walls, nodes, _o = tcr.solve([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[], []])
    cc = dict((ci, [dict(c) for c in v]) for ci, v in res["course_candidates"].items())
    ni = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]
    alvo = [c for c in cc[0] if c.get("node_index") == ni and c.get("logical_code") == "B34"][0]
    # recua a peca de canto para DENTRO da propria parede (abre falta numa face so')
    alvo["origin_world"] = alvo["origin_world"] + alvo["x_dir"] * ft(recuo_cm)
    so_fiada_0 = {0: cc[0]}
    audit = ws.junction_bond_audit(so_fiada_0, nodes, walls, catalog=sb.CATALOG)
    assert (audit["missing"] == []) is valido, (recuo_cm, audit["missing"])
    if not valido:
        assert audit["missing"][0]["reason"] == "BOND_PIECE_PARTIAL"


# ------------------------------------------------ 3. faixa de alvenaria (19 x 14)
@pytest.mark.parametrize("nome,lines,espessuras", [
    ("L_14x19", [seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [14.0, 19.0]),
    ("L_19x19", [seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [19.0, 19.0]),
    ("T_19x19", [seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [19.0, 19.0]),
    ("X_19x19", [seg(0, 302, 604, 302), seg(302, 0, 302, 604)], [19.0, 19.0]),
])
def test_parede_mais_espessa_que_o_bloco_nao_acusa_amarracao_faltante(nome, lines, espessuras):
    res, walls, nodes = _solve_espessuras(lines, espessuras)
    larguras = set(c["width_cm"] for v in res["course_candidates"].values() for c in v)
    assert larguras == {14.0}, larguras
    a = res["junction_bond_audit"]
    assert res["missing_required_junction_bond"] == [], (nome, res["missing_required_junction_bond"][:2])
    assert a["checked"] == a["valid"] == 14, (nome, a["checked"], a["valid"])


def test_sem_catalogo_a_regiao_volta_a_ser_a_espessura_inteira():
    """Sem o catalogo o gate nao sabe a largura do bloco: a regiao e' a
    espessura inteira e a parede de 19 acusa - comportamento declarado."""
    res, walls, nodes = _solve_espessuras([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [19.0, 19.0])
    audit = ws.junction_bond_audit(res["course_candidates"], nodes, walls)
    assert audit["missing"] and all(f["reason"] == "BOND_PIECE_PARTIAL" for f in audit["missing"])


# ------------- 4. a razao nova nao pode mudar a fisica (canaleta / paridade)
def _op(lo, hi, sill, head):
    return (ft(lo), ft(hi), ft(sill), ft(head))


def _solve_flag(lines, openings, ligada):
    antes = m.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED
    m.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED = ligada
    try:
        return tcr.solve(lines, openings, num_courses=14)
    finally:
        m.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED = antes


def test_a_canaleta_nao_absorve_o_compensador_de_no_nao_resolvido():
    """Achado da revisao (ALTA): com a razao JUNCTION_UNRESOLVED_FILL o reforco
    passava a tratar o C09 do canto como preenchimento elegivel e a canaleta o
    engolia, cobrindo 100% da regiao do no' sem o CHANNEL_AS_JUNCTION_BOND
    acusar. A peca de no' nao resolvido continua ocupando a posicao do no'."""
    lines = [seg(0, 0, 300, 0), seg(0, 0, 0, 298)]
    ops = [[_op(14, 26, 0, 80), _op(29, 89, 80, 221)], []]
    com, walls, nodes, _o = _solve_flag(lines, ops, True)
    sem, _w, _n, _o2 = _solve_flag(lines, ops, False)
    assert tcr.physical_signature(com, walls) == tcr.physical_signature(sem, walls)
    assert com["channel_as_junction_bond"] == []
    regioes = ws._bond_regions(nodes, walls)
    for ci, pecas in com["course_candidates"].items():
        for c in pecas:
            if not str(c.get("logical_code")).startswith("CHANNEL"):
                continue
            assert c.get("placement_reason") != ws.JUNCTION_UNRESOLVED_FILL_REASON, (ci, c)
            for ni, f in ws._region_overlaps(c, regioes):
                assert f < 0.5, ("canaleta ocupando a regiao do no'", ni, ci, f)


def test_a_tentativa_de_paridade_do_channel_nao_muda_com_a_76_1():
    """Achado da revisao (MEDIA): a mesma causa fazia a tentativa de paridade
    do canto ser aceita com a 76.1 e rejeitada sem ela."""
    lines = [seg(0, 0, 300, 0), seg(0, 0, 0, 298)]
    ops = [[_op(16, 21, 0, 60), _op(24, 84, 60, 221)], []]
    com, walls, _n, _o = _solve_flag(lines, ops, True)
    sem, _w, _n2, _o2 = _solve_flag(lines, ops, False)
    assert tcr.physical_signature(com, walls) == tcr.physical_signature(sem, walls)
    assert com["channel_tie_parity_trials"]["accepted"] == sem["channel_tie_parity_trials"]["accepted"]


def test_as_razoes_de_posicao_de_no_estao_em_sincronia_com_o_motor():
    from core.engine import opening_reinforcement as orf
    assert orf.NODE_POSITION_FILL_REASONS == (ws.JUNCTION_UNRESOLVED_FILL_REASON,)
    assert m.NODE_POSITION_FILL_REASONS == (ws.JUNCTION_UNRESOLVED_FILL_REASON,)
    peca = {"placement_reason": ws.JUNCTION_UNRESOLVED_FILL_REASON, "logical_code": "C09"}
    assert orf._is_tie(peca) and m._is_tie_candidate(peca)
    # canaleta que herdasse a razao seria acusada pelo gate da regra 75
    canal = dict(peca, logical_code=orf.CHANNEL_U_19)
    assert orf.channel_as_junction_bond({3: [canal]})
    # e o gate da regra 76 nunca acusa o nao resolvido como DESIGNADO
    assert ws.JUNCTION_UNRESOLVED_FILL_REASON not in ws.COMPENSATOR_BOND_ROLE_PREFIXES
    assert not any(ws.JUNCTION_UNRESOLVED_FILL_REASON.startswith(p) for p in ws.COMPENSATOR_BOND_ROLE_PREFIXES)


def test_o_microajuste_calcula_o_missing_quando_o_resultado_nao_traz_a_chave():
    """Achado da revisao (BAIXA): no fluxo sem reforco o portao da secao 66
    perdia a evidencia geometrica. Agora o MISSING e' calculado ali."""
    res, walls, nodes, ops = tcr.solve([seg(0, 0, 402, 0), seg(0, 0, 0, 25)], [[], []], strategy=None,
                                       num_courses=14)
    assert "missing_required_junction_bond" not in res
    faixa = m._free_to_top_band(sb.CATALOG, 0.0)
    gates = m._micro_adjust_measure(res, walls, ops, sb.CATALOG, faixa, 0, nodes=nodes)["gates"]
    assert "MISSING_REQUIRED_JUNCTION_BOND" in gates
    assert gates["MISSING_REQUIRED_JUNCTION_BOND"] > 0, gates   # braco de 25 cm: canto sem amarracao
