# -*- coding: utf-8 -*-
"""Microajuste da POSICAO da abertura (secao 66) - ETAPA 3B por QUALIDADE.

Fixture fisica: parede com um T (peca de no' B54) e uma abertura cuja jamba fica
a ~30 cm do fim da peca de no'. Um B34 + junta precisa 35 cm, entao a fiada e'
obrigada a fechar o trecho com peca de acerto; deslocando a abertura 5 cm o
mesmo trecho passa a caber um B34 inteiro.

    python3 -m pytest tests/test_opening_micro_adjust.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
ft, seg = sb.ft, sb.seg
CATALOG = sb.CATALOG
from core.engine import opening_micro_adjust as oma  # noqa: E402

NUM_COURSES = 8


# geometria da fixture: os dois pilaretes so' fecham quando cada um e'
# congruente a 4 modulo PIER_MODULE_CM - com vao de 91 cm isso exige uma parede
# de 604 cm. O T fica em 177 para a peca de no' (B54 centrada) terminar em 204,
# exatamente 30 cm antes da jamba de 234: um B34 + junta precisa de 35.
WALL_CM = 604.0
TEE_CM = 177.0
JAMB_CM = 234.0
OPENING_CM = 91.0


def _solve(openings_cm, wall_len_cm=WALL_CM, tee_t_cm=TEE_CM):
    """Parede com um T e uma abertura; devolve (result, walls, openings)."""
    lines = [seg(0, 0, wall_len_cm, 0), seg(tee_t_cm, 0, tee_t_cm, 300)]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    openings = [[(ft(lo), ft(hi), ft(0.0), ft(221.0)) for lo, hi in openings_cm], []]
    result = m.solve_building_blocks_all_courses(
        nodes, walls, end_to_node, openings, CATALOG, 0.0, NUM_COURSES,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    return result, walls, openings


def _fillers(result, walls, openings, wall_idx=0):
    spans = [(m._ft_to_cm(o[0]), m._ft_to_cm(o[1])) for o in openings[wall_idx]]
    return oma.strip_filler_pieces(result["course_candidates"], wall_idx, walls, spans, CATALOG)


def _specials(result):
    return sum(1 for pieces in result["course_candidates"].values() for c in pieces
               if (CATALOG.get(c["logical_code"]) or {}).get("is_compensator"))


# ------------------------------------------------------------------ reguas

def test_strip_filler_ruler_counts_only_filler_pieces_between_node_and_jamb():
    result, walls, openings = _solve([(JAMB_CM, JAMB_CM + OPENING_CM)])
    assert _fillers(result, walls, openings) > 0          # a regua ve' o defeito
    # a mesma regua num trecho sem vao: nada a contar
    assert oma.strip_filler_pieces(result["course_candidates"], 0, walls, [], CATALOG) == 0


def test_pre_screen_keeps_only_offsets_whose_piers_close():
    # numeros REAIS da parede 8284543 do BUTANTA (1039 cm, vaos 469-560 e 724-815)
    span, others, length = (469.0, 560.0), [(724.0, 815.0)], 1039.0
    offsets = oma.feasible_offsets(span, others, length, [])
    closing = [d for d in offsets if oma.piers_close((span[0] + d, span[1] + d), others, length)]
    assert closing == [0.0, 5.0, -5.0, 10.0, -10.0]
    assert len(offsets) == 21                              # +-10 cm, passo de 1 cm


def test_safety_limits_reject_offsets_that_leave_the_wall_or_touch_another_opening():
    offsets = oma.feasible_offsets((20.0, 100.0), [(108.0, 200.0)], 300.0, [])
    assert all(d <= 0.0 for d in offsets)                  # nao pode avancar contra o vizinho
    assert all(20.0 + d >= oma.MICRO_ADJUST_WALL_EDGE_MIN_CM for d in offsets)
    # no' a 5 cm da jamba: os deslocamentos que encostam nele saem
    near_node = oma.feasible_offsets((100.0, 200.0), [], 400.0, [104.0])
    assert 4.0 not in near_node and 0.0 in near_node


# ------------------------------------------------------------------ escolha

def _evaluator(table):
    def evaluate(offset):
        return table[offset]
    return evaluate


_CANDIDATE = {"wall_idx": 0, "opening_index": 0, "span_cm": [JAMB_CM, JAMB_CM + OPENING_CM],
              "reasons": ["teste"]}


def _quality(**kw):
    base = {"small_void": 0, "strip_fillers": 0, "mid_wall_half_blocks": 0, "specials": 0,
            "special_clusters": 0, "non_modular": 0}
    base.update(kw)
    return base


def test_does_not_move_when_the_current_position_is_already_as_good():
    table = {0.0: {"gates": {}, "quality": _quality(strip_fillers=4)},
             5.0: {"gates": {}, "quality": _quality(strip_fillers=4)},
             -5.0: {"gates": {}, "quality": _quality(strip_fillers=4)}}
    record = oma.choose_offset(_CANDIDATE, _evaluator(table), sorted(table))
    assert record["chosen_offset_cm"] == 0.0 and record["applied"] is False


def test_moves_when_a_shift_is_strictly_better_and_prefers_the_smallest_one():
    table = {0.0: {"gates": {}, "quality": _quality(strip_fillers=6)},
             5.0: {"gates": {}, "quality": _quality(strip_fillers=2)},
             -5.0: {"gates": {}, "quality": _quality(strip_fillers=2)},
             10.0: {"gates": {}, "quality": _quality(strip_fillers=2)}}
    record = oma.choose_offset(_CANDIDATE, _evaluator(table), [0.0, 5.0, -5.0, 10.0])
    assert record["chosen_offset_cm"] == 5.0 and record["applied"] is True


def test_a_shift_that_breaks_any_hard_gate_is_rejected_even_if_quality_improves():
    table = {0.0: {"gates": {"colisoes": 0, "sem_apoio": 0}, "quality": _quality(strip_fillers=6)},
             5.0: {"gates": {"colisoes": 1, "sem_apoio": 0}, "quality": _quality(strip_fillers=0)},
             -5.0: {"gates": {"colisoes": 0, "sem_apoio": 2}, "quality": _quality(strip_fillers=0)}}
    record = oma.choose_offset(_CANDIDATE, _evaluator(table), [0.0, 5.0, -5.0])
    assert record["chosen_offset_cm"] == 0.0 and record["applied"] is False


def test_quality_order_puts_the_vertical_pattern_above_the_specials():
    """Prioridade 10 (padrao vertical) vale mais que 12 (compensador/pastilha):
    o caso real troca C09+B19 na faixa da amarracao por um B34, e o residual do
    outro lado fecha com uma peca menor."""
    table = {0.0: {"gates": {}, "quality": _quality(strip_fillers=18, specials=35)},
             5.0: {"gates": {}, "quality": _quality(strip_fillers=12, specials=36)}}
    record = oma.choose_offset(_CANDIDATE, _evaluator(table), [0.0, 5.0])
    assert record["chosen_offset_cm"] == 5.0


# ------------------------------------------------- vermelho/verde no solver real

def _gates(result):
    kinds = {}
    audits = result.get("wall_bond_audits") or []
    if isinstance(audits, dict):
        audits = list(audits.values())
    for audit in audits:
        if not isinstance(audit, dict):
            continue
        for problem in (audit or {}).get("problems") or ():
            kind = str(problem).split(":")[0]
            kinds[kind] = kinds.get(kind, 0) + 1
    kinds["colisoes"] = len(result.get("collisions") or [])
    kinds["nao_modular"] = len(result.get("non_modular") or [])
    return kinds


def test_red_green_the_shift_lets_a_whole_block_close_the_strip_after_the_tie():
    """VERMELHO: com a jamba a 30 cm do fim da peca de no', a fiada fecha o
    trecho com peca de acerto (`B19 C09`). VERDE: com o deslocamento que a busca
    escolhe - o valor sai da busca, nao do teste - o mesmo trecho fecha com um
    bloco inteiro, sem piorar nenhum portao."""
    before, walls, openings = _solve([(JAMB_CM, JAMB_CM + OPENING_CM)])
    fillers_before = _fillers(before, walls, openings)
    assert fillers_before > 0                       # vermelho: o defeito existe

    solved = {}

    def evaluate(offset):
        result, w, o = _solve([(JAMB_CM + offset, JAMB_CM + OPENING_CM + offset)])
        solved[offset] = (result, w, o)
        return {"gates": _gates(result),
                "quality": {"small_void": 0, "strip_fillers": _fillers(result, w, o),
                            "mid_wall_half_blocks": 0, "specials": _specials(result),
                            "special_clusters": 0, "non_modular": len(result.get("non_modular") or [])}}

    offsets = [d for d in oma.feasible_offsets((JAMB_CM, JAMB_CM + OPENING_CM), [], WALL_CM, [])
               if oma.piers_close((JAMB_CM + d, JAMB_CM + OPENING_CM + d), [], WALL_CM)]
    assert len(offsets) > 1
    record = oma.choose_offset(_CANDIDATE, evaluate, offsets)

    assert record["applied"] and abs(record["chosen_offset_cm"]) <= oma.MICRO_ADJUST_MAX_CM
    assert record["after"]["quality"]["strip_fillers"] < fillers_before
    for kind, value in record["after"]["gates"].items():
        assert value <= record["before"]["gates"].get(kind, 0), kind
    # e' bloco inteiro que fecha a faixa, nao peca de acerto
    result, w, o = solved[record["chosen_offset_cm"]]
    assert _fillers(result, w, o) == 0


def test_the_total_shift_from_the_original_position_is_capped(monkeypatch):
    """O teto de 10 cm vale para o deslocamento TOTAL desde a posicao do
    projeto: uma abertura que ja' andou 10 cm nao anda mais (nao ha' abertura
    passeando a cada rodada), e uma que andou 5 cm so' pode andar mais 5."""
    span = (JAMB_CM, JAMB_CM + OPENING_CM)
    full = oma.feasible_offsets(span, [], WALL_CM, [])
    assert max(abs(d) for d in full) == oma.MICRO_ADJUST_MAX_CM

    half = oma.feasible_offsets(span, [], WALL_CM, [], already_moved_cm=5.0)
    assert max(half) == 5.0 and min(half) == -10.0        # 5 para frente, 15 para tras nao

    spent = oma.feasible_offsets(span, [], WALL_CM, [], already_moved_cm=10.0)
    assert max(spent) == 0.0 and min(spent) == -10.0      # so' pode voltar


def test_control_a_position_already_as_good_is_not_moved():
    """Regra 14 com o solver real: quando nenhum deslocamento melhora a
    qualidade, a escolha e' 0 (a igualdade fica com a posicao do projeto)."""
    span = (JAMB_CM, JAMB_CM + OPENING_CM)

    def evaluate(offset):
        result, w, o = _solve([(span[0] + offset, span[1] + offset)])
        fillers = _fillers(result, w, o)
        # qualidade ACHATADA de proposito: todas as posicoes empatam
        return {"gates": _gates(result),
                "quality": {"small_void": 0, "strip_fillers": min(fillers, 1), "mid_wall_half_blocks": 0,
                            "specials": 0, "special_clusters": 0, "non_modular": 0}}

    offsets = [d for d in oma.feasible_offsets(span, [], WALL_CM, [])
               if oma.piers_close((span[0] + d, span[1] + d), [], WALL_CM)]
    record = oma.choose_offset(dict(_CANDIDATE, span_cm=list(span)), evaluate, [0.0] + [d for d in offsets if d == 0.0])
    assert record["chosen_offset_cm"] == 0.0 and record["applied"] is False
