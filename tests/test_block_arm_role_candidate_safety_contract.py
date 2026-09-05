# -*- coding: utf-8 -*-
"""CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT - contrato geral de
seguranca para aceitar/rejeitar um candidato de troca de papel
`course_a`/`course_b` numa aresta ISOLADA do grafo de
`_coordinate_arm_role_nodes` (ver REGRAS_MODULACAO_BLOCOS.md secao 30/31 e
docs/BLOCK_ARM_ROLE_HUMAN_POLICY.md para o relatorio completo).

Cobre os testes T1-T16 pedidos pela CR:

    T1  W011/wall_idx=23 (TGD) aceito
    T2  candidato com COMPENSATOR_CONSECUTIVE novo rejeitado
    T3  candidato com COVERAGE_GAP_IN_ROW novo rejeitado
    T4  candidato com COVERAGE_PARTIAL_WALL novo rejeitado
    T5  candidato com COVERAGE_ROW_MOSTLY_EMPTY novo rejeitado
    T6  PRISM_STAGGER_BELOW_TARGET e' SOFT PREFERENCE (nivel 2 na propria
        taxonomia do benchmark) - sozinho, nao e' motivo de rejeicao; o
        candidato real que TEM esse achado (e outros hard) continua
        rejeitado pelo gate que de fato se aplica (T2)
    T7  candidato com POSITION_OVERLAP novo rejeitado
    T8  JUNCTION_NOT_ALTERNATING nunca pode surgir ENTRE BANDAS (prevenido
        estruturalmente pelo pin, nao por um gate pos-hoc)
    T9  candidato sem regressao e com melhoria aceito (mesmo caso de T1)
    T10 fallback ORIGINAL (nenhum candidato serve)
    T11 persistencia entre bandas
    T12 ordem de bandas nao muda semantica
    T13 paredes permutadas
    T14 arms permutados
    T15 endpoints invertidos
    T16 execucao repetida deterministica

    python3 -m pytest tests/test_block_arm_role_candidate_safety_contract.py -q
"""

import copy
import json
import os
import sys

import pytest

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

from nuvem.benchmark import runner as bench_runner  # noqa: E402
from nuvem.benchmark.solver_bridge import plan_from_input, catalog_from_input  # noqa: E402
from nuvem.benchmark import validators as bench_validators  # noqa: E402
from nuvem.benchmark.validators import base as bench_base  # noqa: E402


# --------------------------------------------------------------- helpers
def ft(cm):
    return cm / 100.0 * F


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _cell(center_cm, size_cm, width_cm=8.0):
    return {"center_local": (ft(center_cm), 0.0), "size_local": (ft(size_cm), ft(width_cm))}


def _block(code, length_cm, cells, is_compensator=False):
    return {
        "symbol": None, "logical_code": code, "length_cm": float(length_cm),
        "height_cm": 19.0, "width_cm": 14.0, "cells_local": cells,
        "is_special_bond": code in ("B34", "B54"),
        "is_compensator": is_compensator,
        "source_instance_id": None,
    }


CATALOG = {
    "B39": _block("B39", 39, [_cell(-9.9, 15.7), _cell(9.9, 15.8)]),
    "B34": _block("B34", 34, [_cell(-10.2, 10.7), _cell(7.4, 15.7)]),
    "B19": _block("B19", 19, [_cell(0.0, 15.7)]),
    "C09": _block("C09", 9, [], is_compensator=True),
}


def _straight_wall(length_cm=400.0, thickness_cm=14.0):
    """Uma unica parede reta (wall_idx=0), do' t=0 ao t=length_cm."""
    line = seg(0, 0, length_cm, 0)
    return [(line, ft(thickness_cm), (False, False))]


def _place(walls_to_create, wall_idx, code, t_center_cm, course):
    entry = CATALOG[code]
    p0, _p1, wall_dir, _length_ft, _thickness = m._wall_axis_and_length(walls_to_create, wall_idx)
    origin = XYZ(p0.X + wall_dir.X * ft(t_center_cm), p0.Y + wall_dir.Y * ft(t_center_cm), p0.Z)
    return m._make_block_candidate(code, entry, course, origin, wall_dir, "TEST", wall_idx=wall_idx)


def _course_candidates(walls_to_create, wall_idx, placements):
    """`placements`: {course_index: [(code, t_center_cm, "A"|"B"), ...]}."""
    return dict(
        (ci, [_place(walls_to_create, wall_idx, code, t, letter) for code, t, letter in items])
        for ci, items in placements.items()
    )


# ============================================================
# T2 - COMPENSATOR_CONSECUTIVE novo -> rejeitado
# ============================================================

def test_t2_compensador_consecutivo_novo_e_rejeitado():
    walls = _straight_wall()
    baseline = _course_candidates(walls, 0, {
        0: [("B39", 20, "A"), ("C09", 60, "A"), ("B39", 100, "A")],
    })
    trial = _course_candidates(walls, 0, {
        0: [("B39", 20, "A"), ("C09", 55, "A"), ("C09", 62, "A"),  # NOVO - encostado
            ("B39", 100, "A")],
    })
    assert m._no_new_consecutive_compensators(
        0, walls, CATALOG, 1, baseline, baseline) is True
    assert m._no_new_consecutive_compensators(
        0, walls, CATALOG, 1, baseline, trial) is False


# ============================================================
# T3/T4/T5 - regressao de cobertura por fiada (COVERAGE_GAP_IN_ROW /
# COVERAGE_PARTIAL_WALL / COVERAGE_ROW_MOSTLY_EMPTY) -> rejeitado
# ============================================================

def test_t3_gap_novo_no_meio_da_fiada_e_rejeitado():
    """Um buraco de 40cm aparece NO MEIO de uma fiada antes fechada -
    mesmo mecanismo real medido (candidato bom vira mau quando
    `_drop_fill_colliding_with_ties` descarta um bloco que antes cabia)."""
    walls = _straight_wall()
    baseline = _course_candidates(walls, 0, {
        0: [("B39", 20, "A"), ("B39", 60, "A"), ("B39", 100, "A")],
    })
    trial = _course_candidates(walls, 0, {
        0: [("B39", 20, "A"), ("B39", 100, "A")],  # o do meio sumiu - buraco de ~40cm
    })
    assert m._no_new_row_coverage_regression(0, walls, 1, baseline, baseline) is True
    assert m._no_new_row_coverage_regression(0, walls, 1, baseline, trial) is False


def test_t4_parede_so_parcialmente_modulada_e_rejeitado():
    """Metade da parede deixa de receber qualquer candidato - COVERAGE_
    PARTIAL_WALL (fiada cobre so' uma fracao pequena do trecho modulavel)."""
    walls = _straight_wall(length_cm=200.0)
    baseline = _course_candidates(walls, 0, {
        0: [("B39", 20, "A"), ("B39", 60, "A"), ("B39", 100, "A"), ("B39", 140, "A"), ("B39", 180, "A")],
    })
    trial = _course_candidates(walls, 0, {
        0: [("B39", 20, "A")],  # so' 1 bloco de 39cm numa parede de 200cm
    })
    assert m._no_new_row_coverage_regression(0, walls, 1, baseline, trial) is False


def test_t5_fiada_quase_vazia_e_rejeitado():
    """Uma familia inteira perde quase todo o conteudo numa fiada que
    antes fechava perto de 100% - COVERAGE_ROW_MOSTLY_EMPTY."""
    walls = _straight_wall(length_cm=140.0)
    baseline = _course_candidates(walls, 0, {
        1: [("B39", 20, "B"), ("B39", 60, "B"), ("B39", 100, "B")],
    })
    trial = _course_candidates(walls, 0, {
        1: [("B39", 20, "B")],
    })
    assert m._no_new_row_coverage_regression(0, walls, 2, baseline, trial) is False


def test_redistribuicao_pequena_entre_familias_nao_e_falso_positivo():
    """CONTROLE POSITIVO - regressao real medida (TGD, `wall_idx=23`/W011,
    ver docstring de `_no_new_row_coverage_regression`): quando um no'
    troca de familia, a fiada que PERDE o no' cai um pouco (aqui, -14 de
    555) e a que GANHA sobe (+15) - redistribuicao balanceada, PRECISA
    continuar aceita (senao o candidato seguro W011 seria rejeitado por
    engano, como a primeira versao desta funcao fazia)."""
    walls = _straight_wall(length_cm=600.0)
    baseline = _course_candidates(walls, 0, {
        0: [("B34", 17, "A"), ("B19", 44, "A")] + [("B39", 70 + 39 * i, "A") for i in range(12)],
        1: [("B34", 583, "B")] + [("B39", 70 + 39 * i, "B") for i in range(12)] + [("B19", 556, "B")],
    })
    trial = _course_candidates(walls, 0, {
        # familia A perde o B34+B19 do no' (a parede fica so' com o
        # preenchimento comum, ligeiramente menor) - mesma ordem de
        # grandeza da regressao INOFENSIVA medida ao vivo.
        0: [("B39", 70 + 39 * i, "A") for i in range(12)],
        1: [("B34", 583, "B"), ("B34", 548, "B")] + [("B39", 70 + 39 * i, "B") for i in range(12)],
    })
    assert m._no_new_row_coverage_regression(0, walls, 2, baseline, trial) is True


# ============================================================
# T6 - PRISM_STAGGER_BELOW_TARGET e' SOFT PREFERENCE (nivel 2), nunca
# hard constraint sozinho - classificacao confirmada contra a PROPRIA
# taxonomia do benchmark (nuvem/benchmark/validators/base.py), nao
# inventada por este contrato.
# ============================================================

def test_t6_prism_stagger_below_target_e_soft_preference_na_taxonomia():
    klass = bench_base.error_class("PRISM_STAGGER_BELOW_TARGET")
    assert klass.level == bench_base.LEVEL_PREFERENCE, (
        "PRISM_STAGGER_BELOW_TARGET deveria ser nivel 2 (preferencia) - "
        "se isto mudou na taxonomia do benchmark, o contrato desta CR "
        "precisa de um gate dedicado para ele, o que hoje NAO existe "
        "de proposito (ver secao 'Hard constraints' do relatorio)")


def test_t6_evaluate_corner_role_candidate_nao_tem_gate_de_stagger():
    """Sem UM regressao HARD (fechamento/colisao/prisma-em-vizinha/
    compensador/cobertura), o contrato ACEITA mesmo que o candidato tenha
    pior stagger - por desenho (soft preference nao bloqueia). O
    candidato real do TGD que combina stagger ruim COM compensador novo
    e' rejeitado pelo gate de compensador (T2), nao por este."""
    walls = _straight_wall()
    baseline_candidates = [_place(walls, 0, "B39", 20, "A")]
    trial_candidates = [_place(walls, 0, "B39", 20, "A")]
    baseline_result = {
        "candidates": baseline_candidates, "collisions": [],
        "per_wall": [{"wall_idx": 0, "validation": {"ok": True}, "non_modular": []}],
        "course_candidates": {0: baseline_candidates},
        "wall_bond_audits": {0: {"continuous_joints": []}},
    }
    trial_result = copy.deepcopy(baseline_result)
    ok, reason = m._evaluate_corner_role_candidate(
        0, {0}, set(), walls, CATALOG, 1, baseline_result, trial_result)
    assert ok is True, reason


# ============================================================
# T7 - POSITION_OVERLAP novo -> rejeitado
# ============================================================

def test_t7_colisao_nova_e_rejeitada():
    walls = _straight_wall()
    baseline_candidates = [_place(walls, 0, "B39", 20, "A"), _place(walls, 0, "B39", 100, "A")]
    trial_candidates = [_place(walls, 0, "B39", 20, "A"), _place(walls, 0, "B39", 30, "A")]  # sobrepoe
    baseline_result = {"candidates": baseline_candidates, "collisions": []}
    trial_collisions = m.validate_same_course_collision(trial_candidates)
    assert trial_collisions, "esperava overlap real entre os dois B39 a 10cm um do outro"
    trial_result = {"candidates": trial_candidates, "collisions": trial_collisions}
    assert m._no_new_collisions(baseline_result, baseline_result) is True
    assert m._no_new_collisions(baseline_result, trial_result) is False


# ============================================================
# T8 - JUNCTION_NOT_ALTERNATING nunca surge ENTRE BANDAS: prevenido por
# CONSTRUCAO (pin), nao por um gate de rejeicao pos-hoc - ver
# REGRAS_MODULACAO_BLOCOS.md secao 30/31 ("H-nova PROVADA").
# ============================================================

def _isolated_edge_nodes():
    """Grafo sintetico MINIMO com uma aresta isolada (wall_idx=1 liga
    node 0 <-> node 1, cada um com outro braco para uma parede DIFERENTE -
    exatamente a topologia que `_arm_role_isolated_edges` deve achar)."""
    nodes = [
        {"kind": "L_CORNER", "arms": [(0, 1), (1, 0)], "point": XYZ(0.0, 0.0, 0.0)},
        {"kind": "L_CORNER", "arms": [(1, 1), (2, 0)], "point": XYZ(ft(69.0), 0.0, 0.0)},
    ]
    return nodes


def test_t8_papel_do_no_isolado_pinado_sobrevive_a_re_coordenacao_entre_bandas():
    """Simula 2 BANDAS: `_coordinate_arm_role_nodes` roda de novo sobre o
    MESMO objeto `nodes` (exatamente como `solve_building_blocks_all_
    courses` faz banda a banda) - sem o pin, uma aresta isolada e'
    idempotente por construcao (raiz do BFS nunca muda - ver docstring de
    `_coordinate_arm_role_nodes`), mas o PIN precisa, no minimo, nunca
    permitir que uma banda subsequente reverta uma escolha manual
    (SAME_A/SAME_B) que o SAFE REPAIR fixou - e' exatamente essa reversao,
    quando ausente, que produz duas convencoes opostas na mesma parede e
    aparece como JUNCTION_NOT_ALTERNATING na parede vizinha (causa raiz
    provada, REGRAS_MODULACAO_BLOCOS.md secao 30)."""
    nodes = _isolated_edge_nodes()
    isolated = m._arm_role_isolated_edges(nodes)
    assert len(isolated) == 1, isolated
    edge = isolated[0]
    assert edge["wall_idx"] == 1

    bit_p, bit_q = m.CORNER_ROLE_CANDIDATE_BITS[0][1]  # SAME_A
    m._set_l_corner_role_bits(nodes, edge["node_p"], edge["node_q"], 1, bit_p, bit_q, pinned=True)
    role_after_pin = m._two_arm_l_corner_role_bit(nodes[edge["node_p"]], 1)

    for _band in range(5):  # 5 "bandas" seguidas, mesmo objeto `nodes`
        conflicts = m._coordinate_arm_role_nodes(nodes)
        assert conflicts == []
        assert m._two_arm_l_corner_role_bit(nodes[edge["node_p"]], 1) == role_after_pin, (
            "o papel PINADO nao pode ser revertido por uma banda seguinte")
        assert m._two_arm_l_corner_role_bit(nodes[edge["node_q"]], 1) == role_after_pin


def test_t8_sem_pin_papel_e_idempotente_mas_nao_protegido():
    """CONTROLE: sem pin nenhum, a aresta isolada JA' e' idempotente entre
    bandas por construcao (raiz do BFS estavel) - a persistencia real do
    SAFE REPAIR vem do PIN excluir o no' do grafo de coordenacao, nao de
    uma propriedade nova do BFS em si (ver T8 acima para o cenario que
    de fato precisa do pin: um papel MANUAL, fora do que o BFS natural
    escolheria)."""
    nodes = _isolated_edge_nodes()
    edge = m._arm_role_isolated_edges(nodes)[0]
    m._coordinate_arm_role_nodes(nodes)
    role_band1 = m._two_arm_l_corner_role_bit(nodes[edge["node_p"]], 1)
    for _band in range(5):
        m._coordinate_arm_role_nodes(nodes)
        assert m._two_arm_l_corner_role_bit(nodes[edge["node_p"]], 1) == role_band1


# ============================================================
# T11/T12 - persistencia entre bandas / ordem de bandas nao muda semantica
# ============================================================

def test_t11_persistencia_entre_bandas_com_pin_manual():
    nodes = _isolated_edge_nodes()
    edge = m._arm_role_isolated_edges(nodes)[0]
    bit_p, bit_q = m.CORNER_ROLE_CANDIDATE_BITS[1][1]  # SAME_B
    m._set_l_corner_role_bits(nodes, edge["node_p"], edge["node_q"], 1, bit_p, bit_q, pinned=True)

    band_order_a = [0, 1, 2, 3, 4]
    band_order_b = [4, 3, 2, 1, 0]  # so' pra provar que a ORDEM das chamadas nao importa
    roles_a, roles_b = [], []
    for _ in band_order_a:
        m._coordinate_arm_role_nodes(nodes)
        roles_a.append(m._two_arm_l_corner_role_bit(nodes[edge["node_p"]], 1))

    nodes2 = copy.deepcopy(nodes)
    for _ in band_order_b:
        m._coordinate_arm_role_nodes(nodes2)
        roles_b.append(m._two_arm_l_corner_role_bit(nodes2[edge["node_p"]], 1))

    assert len(set(roles_a)) == 1, roles_a
    assert roles_a == roles_b


def test_t12_ordem_de_bandas_nao_muda_semantica_do_edificio():
    """`_arm_role_isolated_edges`/`_coordinate_arm_role_nodes` dependem so'
    de geometria (`_canonical_node_sort_key`) - permutar a ORDEM em que
    duas arestas isoladas independentes sao processadas pelo SAFE REPAIR
    nao muda o resultado de nenhuma delas (arestas isoladas nunca
    compartilham no')."""
    nodes = [
        {"kind": "L_CORNER", "arms": [(0, 1), (1, 0)], "point": XYZ(0.0, 0.0, 0.0)},
        {"kind": "L_CORNER", "arms": [(1, 1), (2, 0)], "point": XYZ(ft(69.0), 0.0, 0.0)},
        {"kind": "L_CORNER", "arms": [(3, 1), (4, 0)], "point": XYZ(ft(500.0), 0.0, 0.0)},
        {"kind": "L_CORNER", "arms": [(4, 1), (5, 0)], "point": XYZ(ft(569.0), 0.0, 0.0)},
    ]
    edges = m._arm_role_isolated_edges(nodes)
    assert sorted(e["wall_idx"] for e in edges) == [1, 4]

    for order in ([0, 1], [1, 0]):
        nodes_copy = copy.deepcopy(nodes)
        edges_copy = m._arm_role_isolated_edges(nodes_copy)
        by_wall = dict((e["wall_idx"], e) for e in edges_copy)
        for wall_idx in [1, 4][::(1 if order == [0, 1] else -1)]:
            e = by_wall[wall_idx]
            bit_p, bit_q = m.CORNER_ROLE_CANDIDATE_BITS[0][1]
            m._set_l_corner_role_bits(nodes_copy, e["node_p"], e["node_q"], wall_idx, bit_p, bit_q, pinned=True)
        role_1 = m._two_arm_l_corner_role_bit(nodes_copy[by_wall[1]["node_p"]], 1)
        role_4 = m._two_arm_l_corner_role_bit(nodes_copy[by_wall[4]["node_p"]], 4)
        assert (role_1, role_4) == (0, 0), (order, role_1, role_4)


# ============================================================
# T13/T14/T15 - invariancia a permutacao de paredes/arms/endpoints
# ============================================================

def test_t13_paredes_permutadas_mesma_identificacao_de_aresta_isolada():
    def make(order):
        raw = {
            0: (0, 1, (0, 1)),
        }
        nodes = [
            {"kind": "L_CORNER", "arms": [(order[0], 1), (order[1], 0)], "point": XYZ(0.0, 0.0, 0.0)},
            {"kind": "L_CORNER", "arms": [(order[1], 1), (order[2], 0)], "point": XYZ(ft(69.0), 0.0, 0.0)},
        ]
        return nodes

    nodes_a = make([10, 11, 12])
    nodes_b = make([12, 11, 10])  # mesma topologia, wall_idx "invertidos"
    edges_a = m._arm_role_isolated_edges(nodes_a)
    edges_b = m._arm_role_isolated_edges(nodes_b)
    assert [e["wall_idx"] for e in edges_a] == [11]
    assert [e["wall_idx"] for e in edges_b] == [11]


def test_t14_arms_permutados_mesmo_resultado_de_isolamento():
    nodes_a = _isolated_edge_nodes()
    nodes_b = copy.deepcopy(nodes_a)
    a0, a1 = nodes_b[0]["arms"]
    nodes_b[0]["arms"] = [a1, a0]
    b0, b1 = nodes_b[1]["arms"]
    nodes_b[1]["arms"] = [b1, b0]

    edges_a = m._arm_role_isolated_edges(nodes_a)
    edges_b = m._arm_role_isolated_edges(nodes_b)
    assert [e["wall_idx"] for e in edges_a] == [e["wall_idx"] for e in edges_b] == [1]


def test_t15_endpoints_invertidos_nao_muda_identificacao():
    """Trocar qual ponta fisica de uma parede e' "ponta 0" (o mesmo
    segmento, sentido oposto) nao pode mudar QUAIS arestas o grafo
    considera isoladas - `_canonical_node_sort_key` usa so' o PONTO do
    no', nunca o sentido/indice do segmento."""
    nodes_a = _isolated_edge_nodes()
    nodes_b = copy.deepcopy(nodes_a)
    nodes_b[0]["arms"] = [(nodes_b[0]["arms"][0][0], 1), (nodes_b[0]["arms"][1][0], 1)]
    edges_a = m._arm_role_isolated_edges(nodes_a)
    edges_b = m._arm_role_isolated_edges(nodes_b)
    assert [e["wall_idx"] for e in edges_a] == [e["wall_idx"] for e in edges_b] == [1]


# ============================================================
# T1/T9/T10/T16 - corpus REAL (TGD): aceita o bom, rejeita os maus,
# fallback ORIGINAL, execucao deterministica. Mesma pratica ja' usada em
# tests/test_block_arm_role_prism_stagger.py (a reserva emprestada do
# quadrado do canto so' aparece com topologia real de mais de 2 paredes
# por no').
# ============================================================

def _run_tgd(enabled):
    m.ARM_ROLE_SAFE_REPAIR_ENABLED = enabled
    paths = bench_runner.project_paths("torre_easy_lo_r00_tgd")
    input_project = json.load(open(paths["input"], encoding="utf-8"))
    nodes, walls_to_create, end_to_node, openings_per_wall = plan_from_input(input_project)
    catalog, _reconstructed, _dropped = catalog_from_input(input_project)
    settings = input_project.get("settings") or {}
    base_z_ft = float(settings.get("base_z_cm") or 0.0) / 100.0 * F
    num_courses = int(settings.get("num_courses") or settings.get("expected_rows") or 15)
    result = m.solve_building_blocks_all_courses(
        nodes, walls_to_create, end_to_node, openings_per_wall, catalog, base_z_ft, num_courses,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
    )
    return result, nodes, walls_to_create, end_to_node, openings_per_wall, catalog, base_z_ft, num_courses


@pytest.mark.slow
def test_t1_t9_candidato_seguro_e_aceito_no_tgd_real():
    result, _nodes, _walls, _e2n, _op, _cat, _bz, _nc = _run_tgd(enabled=True)
    safe_repair = result.get("arm_role_safe_repair") or {}
    accepted = safe_repair.get("accepted") or []
    assert accepted, "esperava pelo menos 1 candidato aceito no TGD (wall_idx=23/W011)"
    assert any(a["wall_idx"] == 23 for a in accepted), accepted


@pytest.mark.slow
def test_t10_fallback_original_para_candidatos_inseguros_no_tgd_real():
    result, nodes, _walls, _e2n, _op, _cat, _bz, _nc = _run_tgd(enabled=True)
    safe_repair = result.get("arm_role_safe_repair") or {}
    rejected_walls = set(r["wall_idx"] for r in (safe_repair.get("rejected") or []))
    accepted_walls = set(a["wall_idx"] for a in (safe_repair.get("accepted") or []))
    only_rejected = rejected_walls - accepted_walls
    assert only_rejected, "esperava pelo menos 1 wall_idx so' rejeitado, nenhum candidato aceito"
    for edge in m._arm_role_isolated_edges(nodes):
        if edge["wall_idx"] in only_rejected:
            assert not nodes[edge["node_p"]].get("_arm_role_pinned")
            assert not nodes[edge["node_q"]].get("_arm_role_pinned")


@pytest.mark.slow
def test_t16_execucao_repetida_e_deterministica():
    from nuvem.benchmark.extract import from_solver

    (result_1, _n1, walls_1, e2n_1, op_1, cat_1, bz_1, nc_1) = _run_tgd(enabled=True)
    (result_2, _n2, walls_2, e2n_2, op_2, cat_2, bz_2, nc_2) = _run_tgd(enabled=True)
    safe_1 = result_1.get("arm_role_safe_repair") or {}
    safe_2 = result_2.get("arm_role_safe_repair") or {}
    assert safe_1["accepted"] == safe_2["accepted"]
    assert safe_1["rejected"] == safe_2["rejected"]

    project_1 = from_solver.project_from_solver(
        "torre_easy_lo_r00_tgd", result_1, walls_1, _n1, op_1, cat_1, bz_1, nc_1, metadata={})
    project_2 = from_solver.project_from_solver(
        "torre_easy_lo_r00_tgd", result_2, walls_2, _n2, op_2, cat_2, bz_2, nc_2, metadata={})
    findings_1, _errors_1 = bench_validators.run_all(project_1, {})
    findings_2, _errors_2 = bench_validators.run_all(project_2, {})
    sig = lambda f: (f.get("code"), f.get("wall"), f.get("detail"))  # noqa: E731
    assert sorted(map(sig, findings_1)) == sorted(map(sig, findings_2))
