# -*- coding: utf-8 -*-
"""CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY - testes T1-T10 (+ invariancia/
determinismo/wiring) da spec (docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_
SPEC.md).

Cobre os dois gates corrigidos do SAFE REPAIR (ver
nuvem/core/engine/wall_stepper.py, secao "CR-BLOCK-ARM-ROLE-CANDIDATE-
SAFETY-CONTRACT - SAFE REPAIR"):

  Compensator gate (identidade de fiada FISICA = course_index, nunca a
  letra de familia "A"/"B" que se repete em toda banda de abertura):
    T1  o MESMO compensador isolado (C09), repetido em 7 course_index
        diferentes na mesma posicao X, NAO e' uma sequencia (0 achados) -
        prova que course_index separa fisicamente as fiadas
    T2  C09/C04 REALMENTE consecutivos na MESMA fiada fisica continuam
        bloqueados (regressao real detectada)
    T3  sequencia real de 3+ compensadores na mesma fiada fisica continua
        detectada
    T4  permutar a ordem dos itens dentro de uma fiada nao muda o
        resultado (determinismo/invariancia de ordem)

  Coverage gate (credito FISICO de no', 5 condicoes da spec):
    T5  credito de no' evita falso positivo (proxy LOCAL cairia a zero;
        crédito FISICO restaura a fiada perto do valor ANTES) - contraste
        explicito: SEM credito (node_index=None) rejeita, COM credito
        aceita
    T6  variante geometrica de T5 (comprimentos/posicoes diferentes) -
        prova que nao e' um artefato de um unico numero
    T7  peca REALMENTE ausente (nenhum candidato cobre a regiao, nem no
        mesmo no') continua bloqueado - credito nunca inventa geometria
    T8  peca presente mas em OUTRA fiada fisica (course_index diferente)
        NAO recebe credito
    T9  peca presente mas em OUTRO no' (node_index diferente) NAO recebe
        credito
    T10 geometria insuficiente (peca credora pequena demais) NAO fecha o
        gap - perda fisica real continua bloqueada mesmo com credito
        habilitado

  Integracao/wiring:
    T_WIRING  `_evaluate_corner_role_candidate` so' aplica o credito
              quando `neighbor_node_by_wall` liga o vizinho ao no' certo -
              sem o mapeamento, o candidato e' rejeitado (mesmo bug antigo);
              com o mapeamento, e' aceito
    T_HV      orientacao H/V (paredes horizontal e vertical) - o mecanismo
              e' agnostico a orientacao (usa produto escalar, nunca eixo
              fixo)

Corpus real (T5/T6/T11-T13 da spec, TP1 wall_idx=75 e TGD 89/90): cobertos
pela medicao STATE_A/STATE_B desta CR (nao duplicados aqui como pytest
pesado) e por tests/test_block_arm_role_candidate_safety_contract.py (T1,
`wall_idx=23`/W011 do TGD, continua aceito - ja' roda o corpus real com os
gates desta CR embutidos, sem custo extra de rebuild).

    python3 -m pytest tests/test_block_arm_safe_repair_gate_fidelity.py -q
"""

import os
import random
import sys

import load_script
import revit_stubs

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# --------------------------------------------------------------- helpers
def ft(cm):
    return cm / 100.0 * F


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _block(code, length_cm, width_cm=14.0, is_compensator=False):
    return {
        "symbol": None, "logical_code": code, "length_cm": float(length_cm),
        "height_cm": 19.0, "width_cm": float(width_cm), "cells_local": [],
        "is_special_bond": code in ("B34", "B54"),
        "is_compensator": is_compensator,
        "source_instance_id": None,
    }


CATALOG = {
    "B39": _block("B39", 39),
    "C09": _block("C09", 9, is_compensator=True),
    "C04": _block("C04", 4, is_compensator=True),
    # peca de amarracao sintetica (nao existe no catalogo real de producao)
    # usada SO' para controlar a LARGURA fisica do credito de no' - o
    # mecanismo (`_candidate_extent_on_wall_axis`) e' generico, nao
    # amarrado a codigo especifico.
    "CORNER_WIDE": _block("CORNER_WIDE", 10, width_cm=30.0),
    "CORNER_NARROW": _block("CORNER_WIDE", 10, width_cm=2.0),
}


def _wall(x0, y0, x1, y1, thickness_cm=14.0):
    return (seg(x0, y0, x1, y1), ft(thickness_cm), (False, False))


def _place(walls_to_create, wall_idx, code, t_center_cm, course="A"):
    entry = CATALOG[code]
    p0, _p1, wall_dir, _length_ft, _thickness = m._wall_axis_and_length(walls_to_create, wall_idx)
    origin = XYZ(p0.X + wall_dir.X * ft(t_center_cm), p0.Y + wall_dir.Y * ft(t_center_cm), p0.Z)
    return m._make_block_candidate(code, entry, course, origin, wall_dir, "TEST", wall_idx=wall_idx)


def _node_piece(walls_to_create, wall_idx, node_index, code, t_center_cm, course="A"):
    """Peca de amarracao 'pertencente' (nos dados) a `wall_idx`, orientada
    ao longo do EIXO de `wall_idx`, ancorada em `node_index` - imita
    exatamente o que `solve_l_corner`/`solve_t_intersection` produzem
    (`_make_block_candidate(..., node_index=..., wall_idx=...)`)."""
    entry = CATALOG[code]
    p0, _p1, wall_dir, _length_ft, _thickness = m._wall_axis_and_length(walls_to_create, wall_idx)
    origin = XYZ(p0.X + wall_dir.X * ft(t_center_cm), p0.Y + wall_dir.Y * ft(t_center_cm), p0.Z)
    return m._make_block_candidate(code, entry, course, origin, wall_dir, "L_CORNER",
                                   node_index=node_index, wall_idx=wall_idx)


# ============================================================
# T1-T4 - compensator gate: identidade de fiada FISICA (course_index)
# ============================================================

def test_t1_mesmo_compensador_repetido_em_varias_fiadas_nao_e_sequencia():
    """Mesmo C09 solitario, repetido em 7 course_index DIFERENTES na
    MESMA posicao X (o cenario exato do fantasma multi-banda medido em
    docs/BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md, TP1 wall_idx=75/SAME_A: 7
    bandas, mesmo compensador solitario, curinga confundido com sequencia
    de 7). Cada fiada fisica tem SO' 1 compensador - nunca e' uma
    sequencia (precisa de 2+ na MESMA fiada)."""
    walls = [_wall(0, 0, 200, 0)]
    num_courses = 7
    course_candidates = dict(
        (ci, [_place(walls, 0, "C09", 60.0, "A")]) for ci in range(num_courses)
    )
    signatures = m._wall_compensator_run_signatures(0, walls, num_courses, course_candidates, CATALOG)
    assert signatures == set()
    assert m._no_new_consecutive_compensators(
        0, walls, CATALOG, num_courses, course_candidates, course_candidates) is True


def test_t2_compensadores_realmente_consecutivos_na_mesma_fiada_bloqueados():
    walls = [_wall(0, 0, 200, 0)]
    baseline = {0: [_place(walls, 0, "B39", 20, "A"), _place(walls, 0, "B39", 100, "A")]}
    trial = {0: [_place(walls, 0, "B39", 20, "A"),
                 _place(walls, 0, "C09", 55, "A"), _place(walls, 0, "C09", 62, "A"),
                 _place(walls, 0, "B39", 100, "A")]}
    assert m._no_new_consecutive_compensators(0, walls, CATALOG, 1, baseline, baseline) is True
    assert m._no_new_consecutive_compensators(0, walls, CATALOG, 1, baseline, trial) is False


def test_t3_sequencia_de_3_compensadores_na_mesma_fiada_detectada():
    walls = [_wall(0, 0, 200, 0)]
    course_candidates = {0: [
        _place(walls, 0, "C09", 50, "A"), _place(walls, 0, "C09", 57, "A"),
        _place(walls, 0, "C04", 63, "A"),
    ]}
    runs = m._find_consecutive_compensators_in_course(0, walls, course_candidates[0], CATALOG)
    assert len(runs) == 1
    assert runs[0]["codes"] == ["C09", "C09", "C04"]


def test_t4_ordem_dos_itens_dentro_da_fiada_nao_muda_o_resultado():
    walls = [_wall(0, 0, 200, 0)]
    items = [_place(walls, 0, "C09", 50, "A"), _place(walls, 0, "C09", 57, "A"),
             _place(walls, 0, "C04", 63, "A")]
    baseline = {0: []}
    shuffled = list(items)
    random.Random(42).shuffle(shuffled)
    sig_a = m._wall_compensator_run_signatures(0, walls, 1, {0: items}, CATALOG)
    sig_b = m._wall_compensator_run_signatures(0, walls, 1, {0: shuffled}, CATALOG)
    assert sig_a == sig_b
    assert m._no_new_consecutive_compensators(0, walls, CATALOG, 1, baseline, {0: items}) is False
    assert m._no_new_consecutive_compensators(0, walls, CATALOG, 1, baseline, {0: shuffled}) is False


# ============================================================
# T5-T10 - coverage gate: credito FISICO de no' (5 condicoes)
# ============================================================
#
# Topologia comum (L_CORNER sintetico): parede A (wall_idx=0, ao longo de
# +X) e parede B (wall_idx=1, curta, ao longo de +Y), encontrando-se no
# no' 0 (origem comum). ANTES: a peca de amarracao pertence a B (cobre a
# fiada inteira dela, ao longo do EIXO de B). DEPOIS (candidato ARM que
# troca o papel do no'): a MESMA peca fisica passa a pertencer a A -
# fisicamente ainda encosta no no' e cobre parte do eixo de B pela
# LARGURA dela (nunca pelo comprimento) - exatamente o mecanismo descrito
# em docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_SPEC.md, secao "Coverage
# gate: cobertura fisica".

def _l_corner_walls(wall_a_len_cm=100.0, wall_b_len_cm=10.0):
    wall_a = _wall(0, 0, wall_a_len_cm, 0)          # +X
    wall_b = _wall(0, 0, 0, wall_b_len_cm)          # +Y
    return [wall_a, wall_b]


def test_t5_credito_de_no_evita_falso_positivo():
    walls = _l_corner_walls(wall_b_len_cm=10.0)
    baseline = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 5.0)]}  # dono: B, cobre 0..10
    trial = {0: [_node_piece(walls, 0, 0, "CORNER_WIDE", 0.0)]}     # dono: A, no' 0

    # SEM credito (comportamento antigo, node_index=None) - proxy LOCAL
    # cai de 10 para 0 -> falso positivo de regressao.
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=None) is False

    # COM credito (esta CR) - a peca continua fisicamente presente no
    # MESMO no', a largura dela projetada no eixo de B fecha o trecho.
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=[0]) is True


def test_t6_credito_de_no_variante_geometrica():
    """Mesma mecanica de T5, numeros diferentes (parede B mais longa,
    peca credora ainda mais larga) - nao e' um artefato de um unico
    conjunto de medidas."""
    walls = _l_corner_walls(wall_a_len_cm=250.0, wall_b_len_cm=24.0)
    baseline = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 12.0)]}  # dono: B, cobre 0..24
    trial = {0: [_node_piece(walls, 0, 0, "CORNER_WIDE", 0.0)]}      # dono: A

    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=None) is False
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=[0]) is True


def test_t7_peca_realmente_ausente_continua_bloqueado():
    """Nenhum candidato cobre a regiao perdida, nem no mesmo no' - o
    credito nunca inventa geometria que nao esta' no `trial_result`."""
    walls = _l_corner_walls(wall_b_len_cm=10.0)
    baseline = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 5.0)]}
    trial = {0: []}  # peca REALMENTE removida - nenhuma outra a substitui
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=[0]) is False


def test_t8_peca_em_outra_fiada_fisica_nao_recebe_credito():
    """A peca credora existe, no MESMO no', mas em outro `course_index` -
    condicao 3 (mesma fiada fisica) tem que bloquear o credito."""
    walls = _l_corner_walls(wall_b_len_cm=10.0)
    baseline = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 5.0)], 1: []}
    trial = {0: [], 1: [_node_piece(walls, 0, 0, "CORNER_WIDE", 0.0)]}  # course_index=1, nao 0
    assert m._no_new_row_coverage_regression(1, walls, 2, baseline, trial, node_indices=[0]) is False


def test_t9_peca_em_outro_no_nao_recebe_credito():
    """A peca credora existe, na MESMA fiada fisica, mas ancorada em outro
    `node_index` - condicao 1 (mesmo no') tem que bloquear o credito."""
    walls = _l_corner_walls(wall_b_len_cm=10.0)
    baseline = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 5.0)]}
    trial = {0: [_node_piece(walls, 0, 99, "CORNER_WIDE", 0.0)]}  # no' 99, nao 0
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=[0]) is False


def test_t10_geometria_insuficiente_nao_fecha_o_gap():
    """A peca credora existe no MESMO no'/MESMA fiada, mas e' pequena
    demais (largura insuficiente) para cobrir o trecho perdido - perda
    fisica REAL continua bloqueada mesmo com o credito habilitado
    (condicao 5, ausencia de gap fisico)."""
    walls = _l_corner_walls(wall_b_len_cm=10.0)
    baseline = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 5.0)]}
    trial = {0: [_node_piece(walls, 0, 0, "CORNER_NARROW", 0.0)]}  # largura 2cm so'
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=[0]) is False


# ============================================================
# Integracao / wiring
# ============================================================

def _two_wall_results(baseline_course, trial_course):
    per_wall = [
        {"wall_idx": 0, "validation": {"ok": True}, "non_modular": []},
        {"wall_idx": 1, "validation": {"ok": True}, "non_modular": []},
    ]
    wall_bond_audits = {0: {"continuous_joints": []}, 1: {"continuous_joints": []}}
    baseline_result = {
        "candidates": baseline_course[0], "collisions": [], "per_wall": per_wall,
        "course_candidates": baseline_course, "wall_bond_audits": wall_bond_audits,
    }
    trial_result = {
        "candidates": trial_course[0], "collisions": [], "per_wall": per_wall,
        "course_candidates": trial_course, "wall_bond_audits": wall_bond_audits,
    }
    return baseline_result, trial_result


def test_wiring_neighbor_credita_do_alvo():
    """`_evaluate_corner_role_candidate` so' credita quando o chamador
    informa QUAL no' liga o vizinho ao alvo (`wall_credit_node_indices`) -
    sem o mapeamento (dict vazio - simula um vizinho fora do grafo do
    candidato), o gate de cobertura usa o comportamento antigo (sem
    credito) e rejeita; com o mapeamento correto, aceita. Sentido: a peca
    de canto migra do VIZINHO (wall_idx=1) para o ALVO (wall_idx=0) - o
    VIZINHO precisa creditar do alvo."""
    walls = _l_corner_walls(wall_b_len_cm=10.0)
    baseline_course = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 5.0)]}
    trial_course = {0: [_node_piece(walls, 0, 0, "CORNER_WIDE", 0.0)]}
    baseline_result, trial_result = _two_wall_results(baseline_course, trial_course)

    ok_no_map, reason_no_map = m._evaluate_corner_role_candidate(
        0, {0, 1}, {1}, walls, CATALOG, 1, baseline_result, trial_result,
        wall_credit_node_indices={})
    assert ok_no_map is False
    assert reason_no_map == "row_coverage_regression:1"

    ok_with_map, reason_with_map = m._evaluate_corner_role_candidate(
        0, {0, 1}, {1}, walls, CATALOG, 1, baseline_result, trial_result,
        wall_credit_node_indices={1: [0]})
    assert ok_with_map is True, reason_with_map


def test_wiring_alvo_credita_da_vizinha():
    """Sentido INVERSO do anterior - o mecanismo REAL medido em TGD
    89/90/91/92 (docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_SPEC.md): e' o
    proprio ALVO (`wall_idx=0`, nao a vizinha) que perde a peca de canto
    ao no' (ela migra PARA a vizinha `wall_idx=1`) - o ALVO precisa
    conseguir creditar da vizinha que agora a possui. `wall_credit_node_
    indices` do alvo cobre os DOIS nos isolados dele (aqui, so' o no' 0
    importa)."""
    walls = _l_corner_walls(wall_a_len_cm=10.0, wall_b_len_cm=100.0)
    baseline_course = {0: [_node_piece(walls, 0, 0, "CORNER_WIDE", 5.0)]}  # dono: ALVO
    trial_course = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 0.0)]}     # dono: vizinha

    baseline_result, trial_result = _two_wall_results(baseline_course, trial_course)

    ok_no_map, reason_no_map = m._evaluate_corner_role_candidate(
        0, {0, 1}, {1}, walls, CATALOG, 1, baseline_result, trial_result,
        wall_credit_node_indices={})
    assert ok_no_map is False
    assert reason_no_map == "row_coverage_regression:0"

    ok_with_map, reason_with_map = m._evaluate_corner_role_candidate(
        0, {0, 1}, {1}, walls, CATALOG, 1, baseline_result, trial_result,
        wall_credit_node_indices={0: [0, 0]})
    assert ok_with_map is True, reason_with_map


def test_hv_orientacao_horizontal_e_vertical():
    """O mecanismo (`_candidate_extent_on_wall_axis`, produto escalar) e'
    agnostico a orientacao - repete T5 com a parede B na horizontal (e a
    A na vertical), invertendo os papeis H/V do cenario original."""
    wall_a = _wall(0, 0, 0, 100.0)   # A vertical (+Y)
    wall_b = _wall(0, 0, 10.0, 0)    # B horizontal (+X), curta
    walls = [wall_a, wall_b]
    baseline = {0: [_node_piece(walls, 1, 0, "CORNER_WIDE", 5.0)]}
    trial = {0: [_node_piece(walls, 0, 0, "CORNER_WIDE", 0.0)]}
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=None) is False
    assert m._no_new_row_coverage_regression(1, walls, 1, baseline, trial, node_indices=[0]) is True
