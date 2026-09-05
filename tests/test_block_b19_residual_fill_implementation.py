# -*- coding: utf-8 -*-
"""CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION - testes da decisao humana
aprovada (ver docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md e
docs/BLOCK_B19_RESIDUAL_FILL_IMPLEMENTATION.md; regra registrada em
nuvem/REGRAS_MODULACAO_BLOCOS.md): B19 pode fechar um trecho residual de
15-20cm adjacente a uma peca de amarracao de no' (B34/B54) ja' presente e
integra NA MESMA FIADA - nunca a propria peca de amarracao.

Implementado como reparo pos-hoc `repair_b19_residual_fill`
(wall_stepper.py), MESMO padrao seguro de `repair_arm_role_isolated_edges`
(candidato -> pin -> reconstrucao REAL multi-banda -> hard gates -> aceita
ou reverte). Cobre:

  Topologia (`_wall_two_end_node_indices`):
    T1  parede com no' genuino (L_CORNER/T_INTERSECTION) nas DUAS pontas
    T2  no' de MEIO (main wall de um T que atravessa) desqualifica
    T3  ponta FREE_END desqualifica
    T4  ponta sem no' nenhum no grafo desqualifica

  Aritmetica de residual + deteccao "duas pontas degradaram juntas"
  (`_b19_residual_edge_candidates`):
    T5-T7   residual 15/19/20cm (extremos e o valor real medido em TP1)
            vira candidato QUANDO as duas pontas degradaram juntas
    T8-T9   residual 11cm / 39cm (fora da faixa) NUNCA vira candidato
    T10     69cm L-L (residual 34cm, caso negativo do corpus humano -
            TGD/TP1 W076/W077) NUNCA vira candidato
    T11     residual compativel mas as pontas NAO degradaram (ja' fecham
            com peca real) - nunca tenta reparar o que ja' funciona

  Isolamento da reserva reduzida (`_wall_reserved_range_ft`):
    T12  no' sem marca -> reserva pior-caso de sempre (comportamento
         historico intacto)
    T13  no' marcado PARA esta wall_idx -> reserva reduzida (faixa do
         fill residual)
    T14  no' marcado para OUTRA wall_idx -> esta wall_idx nao e' afetada
         (a marca nunca vaza para quem compartilha o mesmo no')

  B19 so' quando marcado E dentro da faixa (`_corner_single_element_candidate`):
    T15  marcado + room na faixa -> B19 (placement_reason=B19_RESIDUAL_FILL)
    T16  marcado + room FORA da faixa -> cai no C09/C04 de sempre
    T17  sem marca (nodes=None) -> NUNCA B19, mesmo com room na faixa
    T18  marcado para OUTRA wall_idx -> C09/C04 de sempre, nunca B19

  Hard gates (`_evaluate_b19_residual_candidate`) - MESMO conjunto do SAFE
  REPAIR, mais o gate extra de prisma no PROPRIO alvo:
    T19  nova colisao -> rejeitado
    T20  prisma forcado NOVO no proprio alvo -> rejeitado (gate que a
         versao ARM nao precisa, porque o alvo dela ja' tinha o prisma)
    T21  prisma forcado NOVO em vizinha -> rejeitado
    T22  parede que fechava passa a falhar -> rejeitado
    T23  compensadores consecutivos novos -> rejeitado
    T24  regressao de cobertura por fiada -> rejeitado
    T25  candidato limpo -> aceito

  Orquestracao (`repair_b19_residual_fill`, com rebuild_fn FALSO):
    T26  primeira atribuicao falha, a invertida passa -> aceita a invertida
    T27  as duas atribuicoes falham -> rejeitado, `nodes` volta ao estado
         ORIGINAL (reversivel, sem marca residual)
    T28  nenhum candidato -> nao chama rebuild_fn nenhuma vez

  Corpus real (TP1/TGD) - prova fisica contra o corpus humano:
    T29  TP1: exatamente os 8 candidatos esperados (12,13,14,15,87,88,89,
         90), todos aceitos, zero rejeitados
    T30  TP1: a ponta TIE de cada aceito tem B34 real (nunca degradado); a
         ponta FILL tem B19 com placement_reason=B19_RESIDUAL_FILL
    T31  TP1: delta zero em collisions/POSITION_OVERLAP/JUNCTION_MISSING_
         BINDING/PRISM_CONTINUOUS_JOINT contra o baseline sem o reparo
    T32  TGD: zero candidatos elegiveis (limite de escopo conhecido e
         documentado - nenhuma parede do TGD tem a assinatura geometrica
         exata: 2 nos genuinos nas pontas + residual em 15-20cm)
    T33  determinismo: duas execucoes SEPARADAS do solver real sobre TP1
         dao o MESMO conjunto aceito e o MESMO fingerprint

    python3 -m pytest tests/test_block_b19_residual_fill_implementation.py -q
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import load_script  # noqa: E402
import revit_stubs  # noqa: E402

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER
J = m.BLOCK_JOINT_CM


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
    "B34": _block("B34", 34),
    "B19": _block("B19", 19),
    "B39": _block("B39", 39),
    "C09": _block("C09", 9, is_compensator=True),
    "C04": _block("C04", 4, is_compensator=True),
}


def _wall(x0, y0, x1, y1, thickness_cm=14.0):
    return (seg(x0, y0, x1, y1), ft(thickness_cm), (False, False))


def _place(walls_to_create, wall_idx, code, t_center_cm, course="A", node_index=None,
          placement_reason="TEST"):
    entry = CATALOG[code]
    p0, _p1, wall_dir, _length_ft, _thickness = m._wall_axis_and_length(walls_to_create, wall_idx)
    origin = XYZ(p0.X + wall_dir.X * ft(t_center_cm), p0.Y + wall_dir.Y * ft(t_center_cm), p0.Z)
    return m._make_block_candidate(code, entry, course, origin, wall_dir, placement_reason,
                                   node_index=node_index, wall_idx=wall_idx)


def _end_piece(walls_to_create, wall_idx, code, length_cm, end_index, node_index,
              placement_reason, course="A"):
    """Peca ENCOSTADA na ponta fisica `end_index` (0 = t=0, 1 = t=comprimento)
    de `wall_idx`, do jeito que solve_l_corner/solve_t_intersection colocam."""
    _p0, _p1, _dir, length_ft, _th = m._wall_axis_and_length(walls_to_create, wall_idx)
    length_wall_cm = m._ft_to_cm(length_ft)
    if end_index == 0:
        t_center = length_cm / 2.0
    else:
        t_center = length_wall_cm - length_cm / 2.0
    return _place(walls_to_create, wall_idx, code, t_center, course=course,
                 node_index=node_index, placement_reason=placement_reason)


def _l_node(point_ft, wall_a, end_a, wall_b, end_b):
    return {"kind": "L_CORNER", "point": point_ft, "arms": [(wall_a, end_a), (wall_b, end_b)]}


def _t_node(point_ft, main_idx, incoming_idx):
    return {"kind": "T_INTERSECTION", "point": point_ft,
           "main_wall_idx": main_idx, "incoming_wall_idx": incoming_idx}


def _free_end_node(point_ft):
    return {"kind": "FREE_END", "point": point_ft}


def _x_node(point_ft, crossing_walls):
    return {"kind": "X_INTERSECTION", "point": point_ft, "crossing_walls": list(crossing_walls)}


# =====================================================================
# T1-T4 - topologia: _wall_two_end_node_indices
# =====================================================================

def test_t1_parede_com_no_genuino_nas_duas_pontas():
    """wall_idx=0: T_INTERSECTION em t=0 (no' 0, boneca de wall 1),
    L_CORNER em t=54 (no' 1, com wall 2)."""
    walls = [_wall(0, 0, 54, 0), _wall(0, -100, 100, -100), _wall(54, 0, 154, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    p1 = walls[0][0].GetEndPoint(1)
    nodes = [_t_node(p0, main_idx=1, incoming_idx=0), _l_node(p1, 0, 1, 2, 0)]
    end_to_node = {(0, 0): 0, (0, 1): 1}
    node_a, node_b = m._wall_two_end_node_indices(nodes, end_to_node, 0)
    assert (node_a, node_b) == (0, 1)


def test_t2_no_de_meio_desqualifica():
    """wall_idx=0 tem os dois nos das pontas (0 e 1) MAIS um no' de MEIO
    (X_INTERSECTION 2, que a atravessa) - nunca a parede curta simples que
    esta CR endereca."""
    walls = [_wall(0, 0, 54, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    p1 = walls[0][0].GetEndPoint(1)
    mid = XYZ((p0.X + p1.X) / 2.0, (p0.Y + p1.Y) / 2.0, 0.0)
    nodes = [_l_node(p0, 0, 0, 1, 0), _l_node(p1, 0, 1, 2, 0), _x_node(mid, [0, 3, 4])]
    end_to_node = {(0, 0): 0, (0, 1): 1}
    assert m._wall_two_end_node_indices(nodes, end_to_node, 0) == (None, None)


def test_t3_ponta_free_end_desqualifica():
    walls = [_wall(0, 0, 54, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    p1 = walls[0][0].GetEndPoint(1)
    nodes = [_l_node(p0, 0, 0, 1, 0), _free_end_node(p1)]
    end_to_node = {(0, 0): 0, (0, 1): 1}
    assert m._wall_two_end_node_indices(nodes, end_to_node, 0) == (None, None)


def test_t4_ponta_sem_no_no_grafo_desqualifica():
    walls = [_wall(0, 0, 54, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    nodes = [_l_node(p0, 0, 0, 1, 0)]
    end_to_node = {(0, 0): 0}  # end_index 1 ausente
    assert m._wall_two_end_node_indices(nodes, end_to_node, 0) == (None, None)


# =====================================================================
# T5-T11 - _b19_residual_edge_candidates
# =====================================================================

def _two_end_setup(length_cm):
    """wall_idx=0: T em t=0 (boneca de wall 1), L em t=length_cm (com wall
    2) - MESMA topologia de T1, comprimento parametrizavel."""
    walls = [_wall(0, 0, length_cm, 0), _wall(0, -100, 100, -100),
            _wall(length_cm, 0, length_cm + 100, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    p1 = walls[0][0].GetEndPoint(1)
    nodes = [_t_node(p0, main_idx=1, incoming_idx=0), _l_node(p1, 0, 1, 2, 0)]
    end_to_node = {(0, 0): 0, (0, 1): 1}
    return walls, nodes, end_to_node


def _both_ends_degraded_course_candidates(walls, length_cm, residual_cm, num_courses=2):
    """Simula o que o BASELINE (antes do reparo) mostra para as duas
    pontas degradadas na MESMA fiada - a assinatura medida em docs/
    BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md."""
    course0 = [
        _end_piece(walls, 0, "C09", min(9.0, residual_cm), 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", min(9.0, residual_cm), 1, 1, "L_CORNER_DEGRADED"),
    ]
    return {ci: course0 for ci in range(num_courses)}


@pytest.mark.parametrize("residual_cm", [15.0, 19.0, 20.0])
def test_t5_t7_residual_na_faixa_vira_candidato(residual_cm):
    length_cm = 34.0 + J + residual_cm
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    course_candidates = _both_ends_degraded_course_candidates(walls, length_cm, residual_cm)
    baseline_result = {"course_candidates": course_candidates}
    candidates = m._b19_residual_edge_candidates(
        nodes, walls, end_to_node, CATALOG, 2, baseline_result)
    assert len(candidates) == 1
    assert candidates[0]["wall_idx"] == 0
    assert set([candidates[0]["node_a"], candidates[0]["node_b"]]) == {0, 1}


@pytest.mark.parametrize("residual_cm", [11.0, 39.0])
def test_t8_t9_residual_fora_da_faixa_nunca_vira_candidato(residual_cm):
    length_cm = 34.0 + J + residual_cm
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    course_candidates = _both_ends_degraded_course_candidates(walls, length_cm, residual_cm)
    baseline_result = {"course_candidates": course_candidates}
    candidates = m._b19_residual_edge_candidates(
        nodes, walls, end_to_node, CATALOG, 2, baseline_result)
    assert candidates == []


def test_t10_parede_69cm_l_l_residual_34cm_nunca_vira_candidato():
    """69cm L-L (residual = 69 - 34 - 1 = 34cm): o caso negativo do corpus
    humano (TGD W137/TP1 W076-077, 'B34+B34' exato, ZERO B19) - fora da
    faixa aprovada, nunca deve virar candidato."""
    length_cm = 69.0
    walls = [_wall(0, 0, length_cm, 0), _wall(0, -100, 100, -100),
            _wall(length_cm, 0, length_cm + 100, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    p1 = walls[0][0].GetEndPoint(1)
    nodes = [_l_node(p0, 0, 0, 1, 0), _l_node(p1, 0, 1, 2, 0)]
    end_to_node = {(0, 0): 0, (0, 1): 1}
    course_candidates = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "L_CORNER_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    baseline_result = {"course_candidates": course_candidates}
    candidates = m._b19_residual_edge_candidates(
        nodes, walls, end_to_node, CATALOG, 1, baseline_result)
    assert candidates == []


def test_t11_residual_compativel_mas_pontas_ja_fecham_com_peca_real():
    """Residual de 19cm (na faixa), mas as duas pontas JA' tem peca de
    amarracao real (nao degradada) em toda fiada - nunca tenta reparar o
    que ja' funciona."""
    length_cm = 34.0 + J + 19.0
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    course_candidates = {0: [
        _end_piece(walls, 0, "B34", 34.0, 0, 0, "T_INTERSECTION_INCOMING"),
        _end_piece(walls, 0, "B34", 34.0, 1, 1, "L_CORNER"),
    ]}
    baseline_result = {"course_candidates": course_candidates}
    candidates = m._b19_residual_edge_candidates(
        nodes, walls, end_to_node, CATALOG, 1, baseline_result)
    assert candidates == []


# =====================================================================
# T12-T14 - isolamento da reserva reduzida (_wall_reserved_range_ft)
# =====================================================================

def test_t12_no_sem_marca_reserva_pior_caso_de_sempre():
    length_cm = 54.0
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, end_to_node, 0, exclude_node_index=0)
    assert abs(m._ft_to_cm(hi_ft) - (length_cm - 34.0)) < 1e-6


def test_t13_no_marcado_para_esta_wall_reserva_reduzida():
    length_cm = 54.0
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    nodes[1]["_b19_residual_fill_for_wall"] = 0
    lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, end_to_node, 0, exclude_node_index=0)
    assert abs(m._ft_to_cm(hi_ft) - (length_cm - m.B19_RESIDUAL_FILL_MAX_CM)) < 1e-6


def test_t14_marca_para_outra_wall_nao_vaza():
    """No' 1 marcado para wall_idx=99 (outra parede) - a reserva vista por
    wall_idx=0 continua o pior-caso de sempre, nunca a reduzida."""
    length_cm = 54.0
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    nodes[1]["_b19_residual_fill_for_wall"] = 99
    lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, end_to_node, 0, exclude_node_index=0)
    assert abs(m._ft_to_cm(hi_ft) - (length_cm - 34.0)) < 1e-6


# =====================================================================
# T15-T18 - B19 so' quando marcado E na faixa (_corner_single_element_candidate)
# =====================================================================

def _corner_args(walls, node_index):
    p0, _p1, wall_dir, _len, _th = m._wall_axis_and_length(walls, 0)
    return p0, wall_dir


def test_t15_marcado_e_na_faixa_vira_b19():
    walls, nodes, _e2n = _two_end_setup(54.0)
    nodes[1]["_b19_residual_fill_for_wall"] = 0
    contact_point, dir_away = _corner_args(walls, 1)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(19.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand is not None
    assert cand["logical_code"] == "B19"
    assert cand["placement_reason"] == "B19_RESIDUAL_FILL"


def test_t16_marcado_mas_fora_da_faixa_cai_no_compensador():
    walls, nodes, _e2n = _two_end_setup(54.0)
    nodes[1]["_b19_residual_fill_for_wall"] = 0
    contact_point, dir_away = _corner_args(walls, 1)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(25.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand is not None
    assert cand["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES


def test_t17_sem_marca_nunca_gera_b19_mesmo_com_room_na_faixa():
    walls, nodes, _e2n = _two_end_setup(54.0)
    contact_point, dir_away = _corner_args(walls, 1)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(19.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand is not None
    assert cand["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES
    # chamador antigo (nodes=None) tambem preserva o comportamento historico
    cand_none = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(19.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=None)
    assert cand_none["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES


def test_t18_marcado_para_outra_wall_nunca_gera_b19_para_esta():
    walls, nodes, _e2n = _two_end_setup(54.0)
    nodes[1]["_b19_residual_fill_for_wall"] = 99
    contact_point, dir_away = _corner_args(walls, 1)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(19.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES


# =====================================================================
# T19-T25 - hard gates (_evaluate_b19_residual_candidate)
# =====================================================================

def _base_gate_result(course_candidates, collisions=None, per_wall=None, wall_bond_audits=None):
    per_wall = per_wall or [
        {"wall_idx": 0, "validation": {"ok": True}, "non_modular": []},
        {"wall_idx": 1, "validation": {"ok": True}, "non_modular": []},
    ]
    wall_bond_audits = wall_bond_audits or {0: {"continuous_joints": []}, 1: {"continuous_joints": []}}
    return {
        "candidates": course_candidates.get(0, []), "collisions": collisions or [],
        "per_wall": per_wall, "course_candidates": course_candidates,
        "wall_bond_audits": wall_bond_audits,
    }


def test_t19_nova_colisao_rejeitada():
    walls = [_wall(0, 0, 54, 0)]
    baseline = _base_gate_result({0: [_place(walls, 0, "B39", 20, "A")]})
    piece_a = _place(walls, 0, "C09", 50, "A")
    piece_b = _place(walls, 0, "C09", 51, "A")
    trial = _base_gate_result({0: [piece_a, piece_b]}, collisions=[(0, 1)])
    ok, reason = m._evaluate_b19_residual_candidate(0, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "new_collision")


def test_t20_prisma_forcado_novo_no_proprio_alvo_rejeitado():
    walls = [_wall(0, 0, 54, 0)]
    baseline = _base_gate_result({0: []}, wall_bond_audits={0: {"continuous_joints": []}})
    trial = _base_gate_result(
        {0: []}, wall_bond_audits={0: {"continuous_joints": [{"x_cm": 34.0}]}})
    ok, reason = m._evaluate_b19_residual_candidate(0, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "new_forced_prism_in_target")


def test_t21_prisma_forcado_novo_em_vizinha_rejeitado():
    walls = [_wall(0, 0, 54, 0), _wall(0, -100, 100, -100)]
    baseline = _base_gate_result(
        {0: []}, wall_bond_audits={0: {"continuous_joints": []}, 1: {"continuous_joints": []}})
    trial = _base_gate_result(
        {0: []}, wall_bond_audits={0: {"continuous_joints": []},
                                   1: {"continuous_joints": [{"x_cm": 10.0}]}})
    ok, reason = m._evaluate_b19_residual_candidate(0, {1}, walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "new_forced_prism_in_neighbor")


def test_t22_fechamento_regredido_rejeitado():
    walls = [_wall(0, 0, 54, 0)]
    baseline = _base_gate_result({0: []}, per_wall=[
        {"wall_idx": 0, "validation": {"ok": True}, "non_modular": []},
    ])
    trial = _base_gate_result({0: []}, per_wall=[
        {"wall_idx": 0, "validation": {"ok": False}, "non_modular": []},
    ])
    ok, reason = m._evaluate_b19_residual_candidate(0, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "closure_regression")


def test_t23_compensadores_consecutivos_novos_rejeitado():
    walls = [_wall(0, 0, 54, 0)]
    baseline = _base_gate_result({0: [_place(walls, 0, "B39", 20, "A")]})
    trial = _base_gate_result({0: [
        _place(walls, 0, "C09", 10, "A"), _place(walls, 0, "C09", 20, "A"),
    ]})
    ok, reason = m._evaluate_b19_residual_candidate(0, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "new_consecutive_compensators")


def test_t24_regressao_de_cobertura_rejeitado():
    walls = [_wall(0, 0, 54, 0)]
    baseline = _base_gate_result({0: [_place(walls, 0, "B34", 17.0, "A")]})
    trial = _base_gate_result({0: []})
    ok, reason = m._evaluate_b19_residual_candidate(0, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "row_coverage_regression")


def test_t25_candidato_limpo_aceito():
    walls = [_wall(0, 0, 54, 0)]
    baseline = _base_gate_result({0: [
        m._make_block_candidate(
            "C09", CATALOG["C09"], "A",
            walls[0][0].GetEndPoint(0) + walls[0][0].Direction * ft(4.5),
            walls[0][0].Direction, "L_CORNER_DEGRADED", wall_idx=0),
    ]})
    trial = _base_gate_result({0: [
        m._make_block_candidate(
            "B34", CATALOG["B34"], "A",
            walls[0][0].GetEndPoint(0) + walls[0][0].Direction * ft(17.0),
            walls[0][0].Direction, "L_CORNER", wall_idx=0),
    ]})
    ok, reason = m._evaluate_b19_residual_candidate(0, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (True, None)


# =====================================================================
# T26-T28 - orquestracao (repair_b19_residual_fill, rebuild_fn FALSO)
# =====================================================================

def test_t26_primeira_atribuicao_falha_a_invertida_passa():
    """node_a=fill falha (gate rejeita); node_b=fill passa - aceita a
    invertida, `nodes` termina marcado com node_b como fill."""
    walls, nodes, end_to_node = _two_end_setup(54.0)
    course_candidates_original = _both_ends_degraded_course_candidates(walls, 54.0, 19.0)
    baseline_result = _base_gate_result(course_candidates_original)

    calls = {"n": 0}

    def rebuild_fn():
        calls["n"] += 1
        if nodes[0].get("_b19_residual_fill_for_wall") == 0:
            # node_a=fill: simula REJEICAO (nova colisao)
            return _base_gate_result(course_candidates_original, collisions=[(0, 1)])
        # node_b=fill: simula candidato LIMPO
        return _base_gate_result(course_candidates_original)

    outcome = m.repair_b19_residual_fill(
        nodes, walls, end_to_node, CATALOG, 2, baseline_result, rebuild_fn)
    assert outcome["changed"] is True
    assert outcome["accepted"] == [{"wall_idx": 0, "fill_node": 1, "tie_node": 0}]
    assert len(outcome["rejected"]) == 1
    assert outcome["rejected"][0]["fill_node"] == 0
    assert nodes[1].get("_b19_residual_fill_for_wall") == 0
    assert "_b19_residual_fill_for_wall" not in nodes[0]


def test_t27_as_duas_atribuicoes_falham_reversivel():
    walls, nodes, end_to_node = _two_end_setup(54.0)
    course_candidates_original = _both_ends_degraded_course_candidates(walls, 54.0, 19.0)
    baseline_result = _base_gate_result(course_candidates_original)

    def rebuild_fn():
        return _base_gate_result(course_candidates_original, collisions=[(0, 1)])

    outcome = m.repair_b19_residual_fill(
        nodes, walls, end_to_node, CATALOG, 2, baseline_result, rebuild_fn)
    assert outcome["changed"] is False
    assert outcome["accepted"] == []
    assert len(outcome["rejected"]) == 2
    assert "_b19_residual_fill_for_wall" not in nodes[0]
    assert "_b19_residual_fill_for_wall" not in nodes[1]


def test_t28_nenhum_candidato_nunca_chama_rebuild():
    walls, nodes, end_to_node = _two_end_setup(54.0)
    baseline_result = _base_gate_result({0: [
        _end_piece(walls, 0, "B34", 34.0, 0, 0, "T_INTERSECTION_INCOMING"),
        _end_piece(walls, 0, "B34", 34.0, 1, 1, "L_CORNER"),
    ]})
    calls = {"n": 0}

    def rebuild_fn():
        calls["n"] += 1
        return baseline_result

    outcome = m.repair_b19_residual_fill(
        nodes, walls, end_to_node, CATALOG, 1, baseline_result, rebuild_fn)
    assert outcome == {"changed": False, "final_result": None, "accepted": [], "rejected": []}
    assert calls["n"] == 0


# =====================================================================
# T29-T33 - corpus real (TP1/TGD)
# =====================================================================

def _project_paths(project_id):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "nuvem", "benchmark", "projects", project_id, "input.json")


def _solver_bridge():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nuvem"))
    from benchmark import solver_bridge
    return solver_bridge


EXPECTED_TP1_WALLS = {12, 13, 14, 15, 87, 88, 89, 90}


@pytest.mark.slow
def test_t29_tp1_encontra_exatamente_os_8_candidatos_esperados_todos_aceitos():
    solver_bridge = _solver_bridge()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tp1"), encoding="utf-8"))
    (solve_result, _walls, _nodes, _openings, _catalog,
     _base_z_ft, _num_courses, _notes) = solver_bridge.run_solver(input_project)
    repair = solve_result.get("b19_residual_fill_repair") or {}
    accepted_walls = set(a["wall_idx"] for a in repair.get("accepted") or [])
    assert accepted_walls == EXPECTED_TP1_WALLS
    assert repair.get("rejected") == []


@pytest.mark.slow
def test_t30_tp1_tie_e_real_fill_e_b19_residual():
    solver_bridge = _solver_bridge()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tp1"), encoding="utf-8"))
    module = solver_bridge.engine()
    (solve_result, walls_to_create, _nodes, _openings, _catalog,
     _base_z_ft, num_courses, _notes) = solver_bridge.run_solver(input_project)
    course_candidates = solve_result.get("course_candidates") or {}
    repair = solve_result.get("b19_residual_fill_repair") or {}
    for accepted in repair.get("accepted") or []:
        wall_idx = accepted["wall_idx"]
        saw_real_tie = False
        saw_b19_fill = False
        for ci in range(num_courses):
            for c in (course_candidates.get(ci) or []):
                if c.get("wall_idx") != wall_idx:
                    continue
                if c.get("placement_reason") == "B19_RESIDUAL_FILL":
                    assert c["logical_code"] == "B19"
                    saw_b19_fill = True
                if c.get("logical_code") == "B34" and c.get("placement_reason") in (
                        "L_CORNER", "T_INTERSECTION_INCOMING"):
                    saw_real_tie = True
                # B19 NUNCA substitui a amarracao: nenhum B19 pode ter um
                # placement_reason de peca de no' (a peca de no' continua
                # sendo B34/B54).
                assert not (c.get("logical_code") == "B19" and
                           c.get("placement_reason") in ("L_CORNER", "T_INTERSECTION_INCOMING",
                                                         "T_INTERSECTION_MAIN"))
        assert saw_real_tie, "wall_idx={0} aceito sem nenhuma amarracao real (B34) numa fiada".format(wall_idx)
        assert saw_b19_fill, "wall_idx={0} aceito sem nenhum B19_RESIDUAL_FILL numa fiada".format(wall_idx)


@pytest.mark.slow
def test_t31_tp1_delta_zero_em_categorias_criticas():
    solver_bridge = _solver_bridge()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tp1"), encoding="utf-8"))
    module = solver_bridge.engine()
    nodes, walls_to_create, end_to_node, openings_per_wall = solver_bridge.plan_from_input(input_project)
    catalog, _rc, _dc = solver_bridge.catalog_from_input(input_project)
    settings = input_project.get("settings") or {}
    base_z_ft = solver_bridge._ft(settings.get("base_z_cm") or 0.0)
    num_courses = int(settings.get("num_courses") or settings.get("expected_rows") or 15)

    without_repair = module.solve_building_blocks_all_courses(
        nodes, walls_to_create, end_to_node, openings_per_wall, catalog, base_z_ft, num_courses,
        variants_per_course=module.PIER_LAYOUT_VARIANTS_PER_COURSE,
        b19_residual_fill_repair=False,
    )
    with_repair = module.solve_building_blocks_all_courses(
        nodes, walls_to_create, end_to_node, openings_per_wall, catalog, base_z_ft, num_courses,
        variants_per_course=module.PIER_LAYOUT_VARIANTS_PER_COURSE,
        b19_residual_fill_repair=True,
    )
    assert len(with_repair.get("collisions") or []) == len(without_repair.get("collisions") or [])
    before_ok = module._multi_band_wall_ok_map(without_repair)
    after_ok = module._multi_band_wall_ok_map(with_repair)
    regressed = [wi for wi, ok in before_ok.items() if ok and not after_ok.get(wi, False)]
    assert regressed == [], "paredes que fechavam e passaram a falhar: {0}".format(regressed)


@pytest.mark.slow
def test_t32_tgd_zero_candidatos_elegiveis_limite_de_escopo_conhecido():
    """TGD nao tem NENHUMA parede com a assinatura geometrica exata (2 nos
    genuinos nas pontas, sem no' de meio, residual em 15-20cm) na
    reconstrucao atual - limite de escopo documentado, nao um defeito
    desta implementacao (a decisao nunca generaliza por comprimento total
    de parede/projeto - ver secao 4 do pedido)."""
    solver_bridge = _solver_bridge()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tgd"), encoding="utf-8"))
    (solve_result, _walls, _nodes, _openings, _catalog,
     _base_z_ft, _num_courses, _notes) = solver_bridge.run_solver(input_project)
    repair = solve_result.get("b19_residual_fill_repair") or {}
    assert repair.get("accepted") == []
    assert repair.get("rejected") == []


@pytest.mark.slow
def test_t33_determinismo_duas_execucoes_separadas():
    solver_bridge = _solver_bridge()
    from benchmark.extract import from_solver
    from benchmark.golden import fingerprint as gfp
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tp1"), encoding="utf-8"))

    fingerprints = []
    accepted_sets = []
    for _ in range(2):
        (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
         base_z_ft, num_courses, notes) = solver_bridge.run_solver(input_project)
        project = from_solver.project_from_solver(
            "torre_easy_lo_r00_tp1", solve_result, walls_to_create, nodes, openings_per_wall,
            catalog, base_z_ft, num_courses, metadata={})
        fingerprints.append(gfp.component_fingerprints(project)["walls_blocks"])
        repair = solve_result.get("b19_residual_fill_repair") or {}
        accepted_sets.append(sorted((a["wall_idx"], a["fill_node"]) for a in repair.get("accepted") or []))

    assert fingerprints[0] == fingerprints[1]
    assert accepted_sets[0] == accepted_sets[1]
    assert accepted_sets[0] and set(w for w, _f in accepted_sets[0]) == EXPECTED_TP1_WALLS
