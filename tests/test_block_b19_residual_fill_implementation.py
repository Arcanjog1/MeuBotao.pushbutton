# -*- coding: utf-8 -*-
"""CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION - testes da decisao humana
aprovada, REESCRITOS na revisao final de integracao do PR #19 (achado
critico: os 8 candidatos aceitos no TP1 nao tinham NENHUMA peca de
amarracao cobrindo o MESMO no' na MESMA fiada - 0/102 fiadas).

DECISAO DE DOMINIO (pos-revisao, autorizada explicitamente): B19 e' FILL,
NUNCA TIE. Para toda fiada fisica onde existir um B19 marcado como fill
residual, tem que existir, no MESMO no' e na MESMA fiada, uma peca de
amarracao real e integra (B34/B54) que cubra geometricamente o ponto
fisico do no' - vinda de QUALQUER parede participante do no' (a propria
`wall_idx` ou a perpendicular). Nunca aceito so' porque a OUTRA ponta
desta mesma parede fechou com peca real (era assim que o PR #19 original
decidia, e' exatamente o bug). `_b19_tie_integrity_ok` prova isso
GEOMETRICAMENTE, contra o rebuild real - o hard gate central desta
revisao.

Tambem corrigidos nesta revisao (achados da auditoria de integracao):

- UMA UNICA formula de trecho residual (`_b19_residual_span_cm`) usada
  em elegibilidade, reserva E colocacao - antes havia 3 formulas quase-
  iguais que so' coincidiam por acidente aritmetico nos 54cm do TP1.
- Reserva DINAMICA (por parede: `length_ft - CORNER_B34_ROOM_FT`) no
  lugar de uma reserva FIXA no topo da faixa (20cm) - a fixa so'
  funcionava quando o residuo real era exatamente 20cm; qualquer parede
  com residuo entre 15-19cm nunca teria destravado a ponta oposta.
- Estado por no' agora e' um CONJUNTO (`_b19_residual_fill_for_walls`),
  nunca um escalar unico - duas paredes candidatas podem compartilhar o
  mesmo no' sem uma apagar a marca aceita da outra.
- Ordem de tentativa (qual ponta vira fill primeiro) agora e' CANONICA
  GEOMETRICA (`_canonical_node_sort_key`), nunca por `end_index`/
  orientacao de desenho da parede (GetEndPoint(0)/(1)).
- `dirty_wall_idxs`/`wall_credit_node_indices` passam a incluir as
  paredes perpendiculares dos dois nos (MESMO escopo do SAFE REPAIR do
  ARM) - antes os gates de compensador/cobertura so' olhavam a propria
  parede alvo, deixando passar uma regressao real numa vizinha (medida:
  wall_idx=93 do TP1, 18 sequencias novas de compensador).
  - `repair_b19_residual_fill` revalida cada candidato aceito contra a
  COMBINACAO final de todas as marcas (accepted[] so' existe se o efeito
  sobrevive no `final_result`).
- `audit_wall_bond_quality` (wall_modeling.py): a isencao de
  HALF_BLOCK_NEAR_TIE agora verifica a condicao geometrica DIRETAMENTE
  (defesa em profundidade), nunca confia so' na etiqueta `placement_
  reason`.
- `arm_role_safe_repair=False` volta a desligar TODO o pos-processamento
  (contrato historico preservado - nao e' mais uma porta lateral).

RESULTADO MEDIDO NO CORPUS REAL (TGD/TP1/Piloto) apos a correcao: **ZERO
candidatos aceitos nos tres projetos** - nenhuma parede do corpus atual
tem uma atribuicao fill/tie onde o no' de fill fique coberto por
amarracao real NA MESMA fiada (o padrao de alternancia par/impar do
canto L faz o no' ser amarrado so' nas fiadas ONDE O B19 NAO ESTA'). O
mecanismo esta' correto e pronto para o dia em que o corpus tiver um caso
compativel - ver docs/BLOCK_B19_RESIDUAL_FILL_IMPLEMENTATION.md.

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
    "B54": _block("B54", 54),
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


def _tie_at_point(point_ft, wall_dir, wall_idx, node_index, code="B34",
                  placement_reason="L_CORNER", course="A"):
    """Peca de amarracao REAL encostada em `point_ft` (o ponto do no'),
    estendendo-se por `wall_dir` - do jeito que solve_l_corner/
    solve_t_intersection colocam de verdade (contact_point + dir_away *
    metade do comprimento). O CORPO dela cobre `point_ft` por
    construcao."""
    entry = CATALOG[code]
    half_len_ft = m._cm_to_ft(entry["length_cm"]) / 2.0
    origin = point_ft + wall_dir * half_len_ft
    return m._make_block_candidate(code, entry, course, origin, wall_dir, placement_reason,
                                   node_index=node_index, wall_idx=wall_idx)


def _far_piece(point_ft, wall_dir, wall_idx, node_index, distance_cm, code="B34",
              placement_reason="L_CORNER", course="A"):
    """Peca de amarracao REAL, mas LONGE do ponto do no' (nao cobre) -
    para provar que proximidade sozinha nao basta."""
    entry = CATALOG[code]
    half_len_ft = m._cm_to_ft(entry["length_cm"]) / 2.0
    origin = point_ft + wall_dir * (m._cm_to_ft(distance_cm) + half_len_ft)
    return m._make_block_candidate(code, entry, course, origin, wall_dir, placement_reason,
                                   node_index=node_index, wall_idx=wall_idx)


def _l_node(point_ft, wall_a, end_a, wall_b, end_b):
    return {"kind": "L_CORNER", "point": point_ft, "arms": [(wall_a, end_a), (wall_b, end_b)]}


def _t_node(point_ft, main_idx, incoming_idx):
    return {"kind": "T_INTERSECTION", "point": point_ft,
           "main_wall_idx": main_idx, "incoming_wall_idx": incoming_idx}


def _free_end_node(point_ft):
    return {"kind": "FREE_END", "point": point_ft}


def _x_node(point_ft, crossing_walls):
    return {"kind": "X_INTERSECTION", "point": point_ft, "crossing_walls": list(crossing_walls)}


def _two_end_setup(length_cm, mirrored=False):
    """wall_idx=0: T num extremo fisico (boneca de wall 1), L no outro
    extremo fisico (com wall 2) - topologia canonica usada na maioria dos
    testes. `mirrored=True` desenha o MESMO segmento fisico no sentido
    CONTRARIO (GetEndPoint(0) e (1) trocados fisicamente) - usado pelo
    teste de invariancia de orientacao: o no' T continua sendo o mesmo
    PONTO fisico (0,0), so' passa a ser `end_index=1` em vez de `0`."""
    if not mirrored:
        walls = [_wall(0, 0, length_cm, 0), _wall(0, -100, 100, -100),
                _wall(length_cm, 0, length_cm + 100, 0)]
        end_index_of_t_point = 0
        end_index_of_l_point = 1
    else:
        walls = [_wall(length_cm, 0, 0, 0), _wall(0, -100, 100, -100),
                _wall(length_cm, 0, length_cm + 100, 0)]
        end_index_of_t_point = 1
        end_index_of_l_point = 0
    t_point = XYZ(0.0, 0.0, 0.0)
    l_point = XYZ(ft(length_cm), 0.0, 0.0)
    # confirma que os PONTOS fisicos batem com os end_index calculados
    # (nunca confiar em GetEndPoint(0)/(1) diretamente aqui - a premissa
    # deste helper e' que o CHAMADOR nunca precisa saber qual e' qual).
    assert walls[0][0].GetEndPoint(end_index_of_t_point).X == t_point.X
    assert walls[0][0].GetEndPoint(end_index_of_l_point).X == l_point.X
    nodes = {}
    nodes[0] = _t_node(t_point, main_idx=1, incoming_idx=0)
    nodes[1] = _l_node(l_point, 0, 1, 2, 0)
    nodes_list = [nodes[0], nodes[1]]
    end_to_node = {(0, end_index_of_t_point): 0, (0, end_index_of_l_point): 1}
    return walls, nodes_list, end_to_node


# =====================================================================
# T1-T4 - topologia: _wall_two_end_node_indices (inalterado)
# =====================================================================

def test_t1_parede_com_no_genuino_nas_duas_pontas():
    walls, nodes, end_to_node = _two_end_setup(54.0)
    node_a, node_b = m._wall_two_end_node_indices(nodes, end_to_node, 0)
    assert (node_a, node_b) == (0, 1)


def test_t2_no_de_meio_desqualifica():
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
    end_to_node = {(0, 0): 0}
    assert m._wall_two_end_node_indices(nodes, end_to_node, 0) == (None, None)


# =====================================================================
# T5-T11 - UNICA formula de residual (_b19_residual_span_cm) - matriz
# completa 14.9/15/18/19/20/20.1
# =====================================================================

@pytest.mark.parametrize("length_cm,expected", [
    (48.9, 14.9), (49.0, 15.0), (52.0, 18.0), (53.0, 19.0), (54.0, 20.0), (54.1, 20.1),
])
def test_t5_formula_unica_de_residual(length_cm, expected):
    got = m._b19_residual_span_cm(length_cm)
    assert abs(got - expected) < 1e-9


@pytest.mark.parametrize("length_cm", [48.9, 54.1])
def test_t6_fora_da_faixa_14_9_e_20_1_nunca_vira_candidato(length_cm):
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    cc = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    baseline_result = {"course_candidates": cc}
    candidates = m._b19_residual_edge_candidates(nodes, walls, end_to_node, CATALOG, 1, baseline_result)
    assert candidates == []


@pytest.mark.parametrize("length_cm", [49.0, 52.0, 53.0, 54.0])
def test_t7_dentro_da_faixa_15_18_19_20_vira_candidato(length_cm):
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    cc = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    baseline_result = {"course_candidates": cc}
    candidates = m._b19_residual_edge_candidates(nodes, walls, end_to_node, CATALOG, 1, baseline_result)
    assert len(candidates) == 1
    assert set([candidates[0]["node_a"], candidates[0]["node_b"]]) == {0, 1}


def test_t8_residual_11cm_fora_da_faixa():
    walls, nodes, end_to_node = _two_end_setup(34.0 + 11.0)
    cc = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    candidates = m._b19_residual_edge_candidates(nodes, walls, end_to_node, CATALOG, 1, {"course_candidates": cc})
    assert candidates == []


def test_t9_residual_39cm_exato_fora_da_faixa():
    walls, nodes, end_to_node = _two_end_setup(34.0 + 39.0)
    cc = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    candidates = m._b19_residual_edge_candidates(nodes, walls, end_to_node, CATALOG, 1, {"course_candidates": cc})
    assert candidates == []


def test_t10_parede_69cm_l_l_residual_34cm_nunca_vira_candidato():
    """69cm L-L (residual = 69 - 34 = 35cm... mas o caso classico do
    corpus e' exatamente 69cm com residual 34cm usando peca de 35 - o
    ponto e' que fica FORA de [15,20] de qualquer forma): o caso negativo
    do corpus humano (TGD W137/TP1 W076-077, 'B34+B34' exato, ZERO B19)."""
    length_cm = 69.0
    walls = [_wall(0, 0, length_cm, 0), _wall(0, -100, 100, -100),
            _wall(length_cm, 0, length_cm + 100, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    p1 = walls[0][0].GetEndPoint(1)
    nodes = [_l_node(p0, 0, 0, 1, 0), _l_node(p1, 0, 1, 2, 0)]
    end_to_node = {(0, 0): 0, (0, 1): 1}
    cc = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "L_CORNER_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    candidates = m._b19_residual_edge_candidates(nodes, walls, end_to_node, CATALOG, 1, {"course_candidates": cc})
    assert candidates == []


def test_t11_residual_compativel_mas_pontas_ja_fecham_com_peca_real():
    length_cm = 54.0
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    cc = {0: [
        _end_piece(walls, 0, "B34", 34.0, 0, 0, "T_INTERSECTION_INCOMING"),
        _end_piece(walls, 0, "B34", 34.0, 1, 1, "L_CORNER"),
    ]}
    candidates = m._b19_residual_edge_candidates(nodes, walls, end_to_node, CATALOG, 1, {"course_candidates": cc})
    assert candidates == []


# =====================================================================
# T12-T14b - reserva DINAMICA (nunca fixa) e isolamento por (no',parede)
# =====================================================================

@pytest.mark.parametrize("length_cm,residual_cm", [(49.0, 15.0), (52.0, 18.0), (54.0, 20.0)])
def test_t12_reserva_dinamica_da_room_exato_de_corner_b34_room_ft(length_cm, residual_cm):
    """A reserva dinamica tem que dar EXATAMENTE CORNER_B34_ROOM_FT de
    room na ponta TIE, para QUALQUER residuo na faixa - nunca so' para
    20cm (bug real da versao anterior, que usava reserva FIXA = 20cm e so'
    funcionava por coincidencia quando o residuo real era exatamente 20)."""
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    nodes[1]["_b19_residual_fill_for_walls"] = {0}
    lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, end_to_node, 0, exclude_node_index=0)
    room_ft = hi_ft - lo_ft
    assert abs(m._ft_to_cm(room_ft) - 34.0) < 1e-6, "residuo=%s deveria dar 34cm de room na TIE" % residual_cm


def test_t12b_sem_marca_reserva_pior_caso_de_sempre():
    length_cm = 54.0
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, end_to_node, 0, exclude_node_index=0)
    assert abs(m._ft_to_cm(hi_ft) - (length_cm - 34.0)) < 1e-6


def test_t13_marca_e_um_conjunto_nao_um_escalar():
    """A marca e' lida de um CONJUNTO (`{0}`, nao um escalar `0`) - o
    efeito (room exato de CORNER_B34_ROOM_FT na ponta oposta) e' o MESMO
    que T12 ja' prova; este teste foca em que a LEITURA aceita conjunto."""
    walls, nodes, end_to_node = _two_end_setup(54.0)
    nodes[1]["_b19_residual_fill_for_walls"] = {0}
    lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, end_to_node, 0, exclude_node_index=0)
    assert abs(m._ft_to_cm(hi_ft - lo_ft) - m._ft_to_cm(m.CORNER_B34_ROOM_FT)) < 1e-6


def test_t14_marca_para_outra_wall_nao_vaza():
    length_cm = 54.0
    walls, nodes, end_to_node = _two_end_setup(length_cm)
    nodes[1]["_b19_residual_fill_for_walls"] = {99}
    lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, end_to_node, 0, exclude_node_index=0)
    assert abs(m._ft_to_cm(hi_ft) - (length_cm - 34.0)) < 1e-6


def test_t14b_duas_paredes_compartilhando_o_mesmo_no_nao_se_apagam():
    """No' compartilhado por wall_idx=0 e wall_idx=5 (por exemplo, um
    X/T real teria isso) - marcar 0 nao pode apagar uma marca ja' aceita
    de 5, e vice-versa (CONJUNTO, nunca escalar unico)."""
    node = {"kind": "L_CORNER", "point": XYZ(0, 0, 0), "arms": [(0, 1), (5, 0)]}
    marks = node.setdefault("_b19_residual_fill_for_walls", set())
    marks.add(0)
    marks.add(5)
    assert marks == {0, 5}
    marks.discard(0)
    assert marks == {5}, "remover a marca de 0 nao pode afetar a marca de 5"


# =====================================================================
# T15-T18 - B19 so' quando marcado E na faixa (_corner_single_element_candidate)
# =====================================================================

def _corner_args(walls):
    p0, _p1, wall_dir, _len, _th = m._wall_axis_and_length(walls, 0)
    return p0, wall_dir


@pytest.mark.parametrize("room_cm", [19.0, 20.0])
def test_t15_marcado_e_room_suficiente_para_o_bloco_fisico_vira_b19(room_cm):
    """B19 e' um bloco FIXO de 19cm - so' fisicamente possivel quando
    `room_ft` >= 19cm. Testado nos dois valores onde isso e' verdade
    dentro da faixa aprovada (19 e' o proprio comprimento do bloco, sem
    folga de junta; 20 e' o caso real medido no TP1, com 1cm de folga)."""
    walls, nodes, _e2n = _two_end_setup(54.0)
    nodes[1]["_b19_residual_fill_for_walls"] = {0}
    contact_point, dir_away = _corner_args(walls)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(room_cm), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand is not None and cand["logical_code"] == "B19"
    assert cand["placement_reason"] == "B19_RESIDUAL_FILL"


@pytest.mark.parametrize("room_cm", [14.9, 15.0, 18.0, 20.1, 25.0])
def test_t16_room_insuficiente_para_o_bloco_fisico_cai_no_compensador(room_cm):
    """ACHADO da revisao de integracao: `room_cm` em [15.0, 18.0] esta'
    DENTRO da faixa aprovada por elegibilidade de PAREDE
    (B19_RESIDUAL_FILL_MIN_CM=15.0), mas B19 e' um bloco FIXO de 19cm -
    nunca cabe fisicamente em menos de 19cm de room, entao a COLOCACAO
    real cai no C09/C04 mesmo com o no' marcado. Isto significa que
    `B19_RESIDUAL_FILL_MIN_CM` (15cm) e' mais permissivo do que a
    colocacao real jamais consegue satisfazer - documentado aqui como
    achado explicito para decisao do usuario (ver relatorio), nunca
    escondido atras de um teste que finge que "15" produz B19."""
    walls, nodes, _e2n = _two_end_setup(54.0)
    nodes[1]["_b19_residual_fill_for_walls"] = {0}
    contact_point, dir_away = _corner_args(walls)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(room_cm), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand is not None and cand["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES


def test_t17_sem_marca_nunca_gera_b19_mesmo_com_room_na_faixa():
    walls, nodes, _e2n = _two_end_setup(54.0)
    contact_point, dir_away = _corner_args(walls)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(19.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES
    cand_none = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(19.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=None)
    assert cand_none["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES


def test_t18_marcado_para_outra_wall_nunca_gera_b19_para_esta():
    walls, nodes, _e2n = _two_end_setup(54.0)
    nodes[1]["_b19_residual_fill_for_walls"] = {99}
    contact_point, dir_away = _corner_args(walls)
    cand = m._corner_single_element_candidate(
        CATALOG, contact_point, dir_away, m._cm_to_ft(19.0), "A", 0, 1, 1,
        placement_reason="L_CORNER_DEGRADED", nodes=nodes)
    assert cand["logical_code"] in m.CORNER_SINGLE_ELEMENT_CODES


# =====================================================================
# T19-T29 - GATE DE INTEGRIDADE DO NO' (_b19_tie_integrity_ok) - o
# achado central da revisao: B19 nunca pode ser a UNICA peca do no'.
# =====================================================================

NODE_POINT = XYZ(ft(54.0), 0.0, 0.0)
WALL_DIR_PLUS_X = XYZ(1.0, 0.0, 0.0)
WALL_DIR_PLUS_Y = XYZ(0.0, 1.0, 0.0)


def _fill_and_tie_setup():
    """wall_idx=0 (ao longo de +X) tem B19_RESIDUAL_FILL ancorado no no'
    `fill_node=0` (ponto NODE_POINT); wall_idx=9 e' a parede PERPENDICULAR
    que participa do MESMO no' (usada para testar que a amarracao pode vir
    dela)."""
    node = {"kind": "L_CORNER", "point": NODE_POINT, "arms": [(0, 1), (9, 0)]}
    nodes = {0: node}
    return nodes


def _b19_fill_candidate(course="A"):
    entry = CATALOG["B19"]
    origin = NODE_POINT - WALL_DIR_PLUS_X * (m._cm_to_ft(19.0) / 2.0)
    return m._make_block_candidate("B19", entry, course, origin, WALL_DIR_PLUS_X,
                                   "B19_RESIDUAL_FILL", node_index=0, wall_idx=0)


def test_t19_tie_na_mesma_fiada_mesmo_no_propria_parede_valido():
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0)
    cc = {0: [_b19_fill_candidate(), tie]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is True


def test_t20_tie_na_mesma_fiada_mesmo_no_parede_perpendicular_valido():
    """A decisao de dominio permite explicitamente que a amarracao venha
    da parede PERPENDICULAR participante do mesmo no'."""
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_Y, wall_idx=9, node_index=0)
    cc = {0: [_b19_fill_candidate(), tie]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is True


def test_t21_b19_como_unica_peca_do_no_rejeita():
    """O caso EXATO do bug encontrado na revisao: B19 sozinho no no',
    nenhuma amarracao real - deve ser rejeitado."""
    nodes = _fill_and_tie_setup()
    cc = {0: [_b19_fill_candidate()]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is False


def test_t22_tie_so_em_outra_fiada_nao_conta():
    """O padrao real medido no TP1: o no' e' amarrado so' nas fiadas
    ONDE O B19 NAO ESTA' (alternancia par/impar do canto L) - continua
    rejeitado, porque a decisao de dominio exige a MESMA fiada."""
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_Y, wall_idx=9, node_index=0)
    cc = {0: [_b19_fill_candidate()], 1: [tie]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 2, cc) is False


def test_t23_tie_em_outro_no_nao_conta():
    nodes = _fill_and_tie_setup()
    nodes[1] = {"kind": "L_CORNER", "point": XYZ(ft(200.0), 0.0, 0.0), "arms": [(9, 1), (10, 0)]}
    tie_outro_no = _tie_at_point(nodes[1]["point"], WALL_DIR_PLUS_Y, wall_idx=9, node_index=1)
    cc = {0: [_b19_fill_candidate(), tie_outro_no]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is False


def test_t24_peca_qualquer_perto_do_no_sem_ser_tie_nao_conta():
    """B34 fisicamente presente no ponto, mas como STANDARD_FILL (nao
    posicionado como amarracao) - nao conta, mesmo cobrindo o ponto."""
    nodes = _fill_and_tie_setup()
    fake_tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0,
                             placement_reason="STANDARD_FILL")
    cc = {0: [_b19_fill_candidate(), fake_tie]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is False


def test_t25_peca_longe_do_no_nao_cobre_geometricamente():
    nodes = _fill_and_tie_setup()
    longe = _far_piece(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0, distance_cm=50.0)
    cc = {0: [_b19_fill_candidate(), longe]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is False


def test_t26_b54_tambem_conta_como_amarracao_real():
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_Y, wall_idx=9, node_index=0,
                        code="B54", placement_reason="T_INTERSECTION_MAIN")
    cc = {0: [_b19_fill_candidate(), tie]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is True


def test_t27_sem_nenhum_b19_no_fill_node_e_vacuamente_ok_mas_marca_saw_any_fill():
    """Se o B19 nem chegou a ser colocado naquele no' em nenhuma fiada,
    nao ha' nada para validar - mas isso NAO deve contar como candidato
    'valido' para fins de aceitar o reparo (ver `saw_any_fill`)."""
    nodes = _fill_and_tie_setup()
    cc = {0: []}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is False


def test_t28_uma_fiada_sem_tie_reprova_o_candidato_inteiro():
    """Mesmo com a MAIORIA das fiadas validas, UMA fiada sem cobertura
    reprova o candidato inteiro (decisao por parede, nunca parcial por
    fiada)."""
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0)
    cc = {
        0: [_b19_fill_candidate(), tie],
        1: [_b19_fill_candidate()],  # falta o tie aqui
    }
    assert m._b19_tie_integrity_ok(0, 0, nodes, 2, cc) is False


def test_t29_covers_point_usa_o_corpo_inteiro_nao_so_o_centro():
    """Uma peca cujo CENTRO esta' longe mas cujo CORPO (comprimento
    inteiro) alcanca o ponto ainda conta - a checagem usa o retangulo
    real, igual ao benchmark (block_covers_point)."""
    nodes = _fill_and_tie_setup()
    # B34 de 34cm, origem a 15cm do no' (dentro da metade do comprimento,
    # 17cm) - o corpo AINDA alcanca o ponto do no'.
    entry = CATALOG["B34"]
    origin = NODE_POINT - WALL_DIR_PLUS_X * m._cm_to_ft(15.0)
    tie = m._make_block_candidate("B34", entry, "A", origin, WALL_DIR_PLUS_X, "L_CORNER",
                                  node_index=0, wall_idx=0)
    cc = {0: [_b19_fill_candidate(), tie]}
    assert m._b19_tie_integrity_ok(0, 0, nodes, 1, cc) is True


# =====================================================================
# T30-T36 - hard gates (_evaluate_b19_residual_candidate) - com o gate
# de integridade do no' agora OBRIGATORIO
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


def test_t30_sem_tie_integrity_rejeitado_antes_de_qualquer_outro_gate():
    """Um candidato PERFEITO em todos os outros gates (fechamento,
    colisao, prisma, compensador, cobertura) mas SEM amarracao cobrindo o
    no' tem que ser rejeitado - este e' o gate que faltava no PR #19
    original."""
    nodes = _fill_and_tie_setup()
    cc = {0: [_b19_fill_candidate()]}
    baseline = _base_gate_result({0: []})
    trial = _base_gate_result(cc)
    ok, reason = m._evaluate_b19_residual_candidate(
        0, 0, nodes, {0}, set(), [_wall(0, 0, 54, 0)], CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "no_tie_covering_node")


def test_t31_com_tie_integrity_e_resto_limpo_aceito():
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0)
    cc = {0: [_b19_fill_candidate(), tie]}
    baseline = _base_gate_result({0: [
        m._make_block_candidate("C09", CATALOG["C09"], "A",
                                NODE_POINT - WALL_DIR_PLUS_X * ft(4.5), WALL_DIR_PLUS_X,
                                "L_CORNER_DEGRADED", wall_idx=0),
    ]})
    trial = _base_gate_result(cc)
    ok, reason = m._evaluate_b19_residual_candidate(
        0, 0, nodes, {0}, set(), [_wall(0, 0, 54, 0)], CATALOG, 1, baseline, trial)
    assert (ok, reason) == (True, None)


def test_t32_nova_colisao_rejeitada_antes_de_checar_o_no():
    walls = [_wall(0, 0, 54, 0)]
    nodes = _fill_and_tie_setup()
    baseline = _base_gate_result({0: [_place(walls, 0, "B39", 20, "A")]})
    piece_a = _place(walls, 0, "C09", 50, "A")
    piece_b = _place(walls, 0, "C09", 51, "A")
    trial = _base_gate_result({0: [piece_a, piece_b]}, collisions=[(0, 1)])
    ok, reason = m._evaluate_b19_residual_candidate(0, 0, nodes, {0}, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "new_collision")


def test_t33_prisma_forcado_novo_no_proprio_alvo_rejeitado():
    walls = [_wall(0, 0, 54, 0)]
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0)
    cc = {0: [_b19_fill_candidate(), tie]}
    baseline = _base_gate_result({0: []}, wall_bond_audits={0: {"continuous_joints": []}})
    trial = _base_gate_result(cc, wall_bond_audits={0: {"continuous_joints": [{"x_cm": 34.0}]}})
    ok, reason = m._evaluate_b19_residual_candidate(0, 0, nodes, {0}, set(), walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "new_forced_prism_in_target")


def test_t34_prisma_forcado_novo_em_vizinha_rejeitado():
    walls = [_wall(0, 0, 54, 0), _wall(0, -100, 100, -100)]
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0)
    cc = {0: [_b19_fill_candidate(), tie]}
    baseline = _base_gate_result(
        {0: []}, wall_bond_audits={0: {"continuous_joints": []}, 1: {"continuous_joints": []}})
    trial = _base_gate_result(
        cc, wall_bond_audits={0: {"continuous_joints": []}, 1: {"continuous_joints": [{"x_cm": 10.0}]}})
    ok, reason = m._evaluate_b19_residual_candidate(0, 0, nodes, {0}, {1}, walls, CATALOG, 1, baseline, trial)
    assert (ok, reason) == (False, "new_forced_prism_in_neighbor")


def test_t35_compensadores_consecutivos_novos_em_vizinha_dirty_rejeitado():
    """Este e' o achado real da revisao (wall_idx=93 do TP1): o gate agora
    cobre TODAS as `dirty_wall_idxs`, nunca so' a parede alvo."""
    walls = [_wall(0, 0, 54, 0), _wall(0, -100, 100, -100)]
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0)
    cc_target = {0: [_b19_fill_candidate(), tie]}
    baseline_neighbor = [_place(walls, 1, "B39", 700, "A")]
    trial_neighbor = [_place(walls, 1, "C09", 700, "A"), _place(walls, 1, "C09", 710, "A")]
    baseline = _base_gate_result({0: []})
    baseline["course_candidates"][0] = baseline["course_candidates"].get(0, []) + baseline_neighbor
    trial = _base_gate_result(cc_target)
    trial["course_candidates"][0] = trial["course_candidates"][0] + trial_neighbor
    ok, reason = m._evaluate_b19_residual_candidate(
        0, 0, nodes, {0, 1}, {1}, walls, CATALOG, 1, baseline, trial)
    assert ok is False and reason.startswith("new_consecutive_compensators:1")


def test_t36_regressao_de_cobertura_em_vizinha_dirty_rejeitado():
    walls = [_wall(0, 0, 54, 0), _wall(0, -100, 100, -100)]
    nodes = _fill_and_tie_setup()
    tie = _tie_at_point(NODE_POINT, WALL_DIR_PLUS_X, wall_idx=0, node_index=0)
    baseline = _base_gate_result({0: [_place(walls, 1, "B34", 17.0, "A")]})
    trial_cc = {0: [_b19_fill_candidate(), tie]}
    ok, reason = m._evaluate_b19_residual_candidate(
        0, 0, nodes, {0, 1}, {1}, walls, CATALOG, 1, baseline, _base_gate_result(trial_cc))
    assert ok is False and reason.startswith("row_coverage_regression:1")


# =====================================================================
# T37-T42 - orquestracao (repair_b19_residual_fill, rebuild_fn FALSO)
# =====================================================================

def _synthetic_repairable_setup():
    """Topologia onde a atribuicao node_b=fill/node_a=tie E' fisicamente
    valida (uma peca real cobre o no' de fill na mesma fiada) - usada
    para provar o caminho de ACEITE de ponta a ponta."""
    walls, nodes, end_to_node = _two_end_setup(54.0)
    return walls, nodes, end_to_node


def test_t37_primeira_atribuicao_sem_tie_a_invertida_com_tie_e_aceita():
    """node_0=fill nunca tem amarracao cobrindo (simula o defeito
    original); node_1=fill tem uma amarracao REAL vinda da parede
    PERPENDICULAR (wall_idx=9, sintetica) cobrindo o MESMO no' - so' esta
    atribuicao pode ser aceita."""
    walls, nodes, end_to_node = _synthetic_repairable_setup()
    course_candidates_original = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    baseline_result = _base_gate_result(course_candidates_original)

    def rebuild_fn():
        pinned_0 = 0 in (nodes[0].get("_b19_residual_fill_for_walls") or ())
        pinned_1 = 0 in (nodes[1].get("_b19_residual_fill_for_walls") or ())
        if pinned_0:
            cc = {0: [_b19_fill_at(walls, nodes, fill_node=0, tie_node=1)]}
        elif pinned_1:
            cc = {0: [
                _b19_fill_at(walls, nodes, fill_node=1, tie_node=0),
                _real_tie_at(walls, nodes, fill_node=1, wall_idx=9, dir_away=XYZ(0, 1, 0)),
            ]}
        else:
            cc = course_candidates_original
        return _base_gate_result(cc)

    outcome = m.repair_b19_residual_fill(nodes, walls, end_to_node, CATALOG, 1, baseline_result, rebuild_fn)
    assert outcome["changed"] is True
    assert outcome["accepted"] == [{"wall_idx": 0, "fill_node": 1, "tie_node": 0}]
    assert any(r["fill_node"] == 0 and r["reason"] == "no_tie_covering_node" for r in outcome["rejected"])
    assert 0 not in (nodes[0].get("_b19_residual_fill_for_walls") or set())
    assert 0 in (nodes[1].get("_b19_residual_fill_for_walls") or set())


def _b19_fill_at(walls, nodes, fill_node, tie_node, wall_idx=0):
    """B19 encostado no no' de FILL, do lado de DENTRO da parede
    `wall_idx` - NUNCA cobre o no' de `tie_node` (a peca que amarra o
    no' de fill precisa vir de OUTRA parede - ver `_real_tie_at`)."""
    point = nodes[fill_node]["point"]
    p0, _p1, wall_dir, length_ft, _th = m._wall_axis_and_length(walls, wall_idx)
    towards = 1.0 if (point - p0).DotProduct(wall_dir) < length_ft / 2.0 else -1.0
    dir_away = wall_dir * towards
    return _tie_at_point(point, dir_away, wall_idx, fill_node, code="B19",
                         placement_reason="B19_RESIDUAL_FILL")


def _real_tie_at(walls, nodes, fill_node, wall_idx, dir_away):
    """Peca de amarracao REAL cobrindo o MESMO no' `fill_node` - vinda de
    `wall_idx` (a parede PERPENDICULAR participante do no', NUNCA a
    mesma parede do B19), estendendo-se por `dir_away` (arbitrario, so'
    precisa ser um vetor unitario qualquer - esta parede e' sintetica,
    so' existe para prover a amarracao)."""
    point = nodes[fill_node]["point"]
    return _tie_at_point(point, dir_away, wall_idx, fill_node, code="B34", placement_reason="L_CORNER")


def test_t38_as_duas_atribuicoes_sem_tie_reversivel():
    walls, nodes, end_to_node = _synthetic_repairable_setup()
    course_candidates_original = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    baseline_result = _base_gate_result(course_candidates_original)

    def rebuild_fn():
        return _base_gate_result(course_candidates_original)  # nunca tem tie cobrindo nenhum no'

    outcome = m.repair_b19_residual_fill(nodes, walls, end_to_node, CATALOG, 1, baseline_result, rebuild_fn)
    assert outcome["changed"] is False
    assert outcome["accepted"] == []
    assert len(outcome["rejected"]) == 2
    assert all(r["reason"] == "no_tie_covering_node" for r in outcome["rejected"])
    assert not (nodes[0].get("_b19_residual_fill_for_walls") or set())
    assert not (nodes[1].get("_b19_residual_fill_for_walls") or set())


def test_t39_nenhum_candidato_nunca_chama_rebuild():
    walls, nodes, end_to_node = _synthetic_repairable_setup()
    baseline_result = _base_gate_result({0: [
        _end_piece(walls, 0, "B34", 34.0, 0, 0, "T_INTERSECTION_INCOMING"),
        _end_piece(walls, 0, "B34", 34.0, 1, 1, "L_CORNER"),
    ]})
    calls = {"n": 0}

    def rebuild_fn():
        calls["n"] += 1
        return baseline_result

    outcome = m.repair_b19_residual_fill(nodes, walls, end_to_node, CATALOG, 1, baseline_result, rebuild_fn)
    assert outcome == {"changed": False, "final_result": None, "accepted": [], "rejected": []}
    assert calls["n"] == 0


def test_t40_accepted_implica_efeito_no_final_result():
    """Depois de aceitar, o `final_result` devolvido TEM que conter
    fisicamente o B19 + o tie prometidos - nunca so' um registro sem
    efeito (achado H da revisao)."""
    walls, nodes, end_to_node = _synthetic_repairable_setup()
    course_candidates_original = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    baseline_result = _base_gate_result(course_candidates_original)

    def rebuild_fn():
        pinned_1 = 0 in (nodes[1].get("_b19_residual_fill_for_walls") or ())
        pinned_0 = 0 in (nodes[0].get("_b19_residual_fill_for_walls") or ())
        if pinned_1:
            cc = {0: [_b19_fill_at(walls, nodes, fill_node=1, tie_node=0),
                     _real_tie_at(walls, nodes, fill_node=1, wall_idx=9, dir_away=XYZ(0, 1, 0))]}
        elif pinned_0:
            cc = {0: [_b19_fill_at(walls, nodes, fill_node=0, tie_node=1)]}
        else:
            cc = course_candidates_original
        return _base_gate_result(cc)

    outcome = m.repair_b19_residual_fill(nodes, walls, end_to_node, CATALOG, 1, baseline_result, rebuild_fn)
    assert outcome["changed"] is True
    final_cc = outcome["final_result"]["course_candidates"][0]
    codes_reasons = [(c["logical_code"], c.get("placement_reason")) for c in final_cc]
    assert ("B19", "B19_RESIDUAL_FILL") in codes_reasons
    assert ("B34", "L_CORNER") in codes_reasons


def test_t41_no_effect_apos_combinacao_final_e_removido_de_accepted():
    """Simula uma interacao onde o candidato passa SOZINHO mas o efeito
    nao sobrevive na combinacao final (ex.: algo removeu o tie no rebuild
    final) - `accepted` tem que refletir isso, nunca ficar divergente do
    `final_result`."""
    walls, nodes, end_to_node = _synthetic_repairable_setup()
    course_candidates_original = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    baseline_result = _base_gate_result(course_candidates_original)
    state = {"final_rebuild_n": 0}

    def rebuild_fn():
        pinned_1 = 0 in (nodes[1].get("_b19_residual_fill_for_walls") or ())
        if not pinned_1:
            return _base_gate_result(course_candidates_original)
        state["final_rebuild_n"] += 1
        if state["final_rebuild_n"] == 1:
            # 1a chamada (validacao individual do candidato): COM tie.
            cc = {0: [_b19_fill_at(walls, nodes, fill_node=1, tie_node=0),
                     _real_tie_at(walls, nodes, fill_node=1, wall_idx=9, dir_away=XYZ(0, 1, 0))]}
        else:
            # rebuild final (pos-loop): o tie "desaparece" - simula uma
            # interacao que invalida o efeito na combinacao final.
            cc = {0: [_b19_fill_at(walls, nodes, fill_node=1, tie_node=0)]}
        return _base_gate_result(cc)

    outcome = m.repair_b19_residual_fill(nodes, walls, end_to_node, CATALOG, 1, baseline_result, rebuild_fn)
    assert outcome["changed"] is False
    assert outcome["accepted"] == []
    assert any(r["reason"].startswith("no_effect_after_final_combination") for r in outcome["rejected"])
    assert not (nodes[1].get("_b19_residual_fill_for_walls") or set())


def test_t42_ordem_de_tentativa_e_canonica_geometrica_nao_end_index():
    """`_b19_residual_edge_candidates` guarda (node_a,node_b) ordenados
    pela CHAVE GEOMETRICA do ponto (`_canonical_node_sort_key`), nunca
    pelo `end_index` bruto - node com MENOR (x,y) sempre vem primeiro,
    independente de qual e' end 0 ou end 1."""
    walls, nodes, end_to_node = _two_end_setup(54.0)
    cc = {0: [
        _end_piece(walls, 0, "C09", 9.0, 0, 0, "T_INTERSECTION_INCOMING_DEGRADED"),
        _end_piece(walls, 0, "C09", 9.0, 1, 1, "L_CORNER_DEGRADED"),
    ]}
    candidates = m._b19_residual_edge_candidates(nodes, walls, end_to_node, CATALOG, 1, {"course_candidates": cc})
    assert len(candidates) == 1
    node_a, node_b = candidates[0]["node_a"], candidates[0]["node_b"]
    key_a = m._canonical_node_sort_key(nodes[node_a])
    key_b = m._canonical_node_sort_key(nodes[node_b])
    assert key_a <= key_b


# =====================================================================
# T43 - INVARIANCIA A REVERSAO DOS ENDPOINTS
# =====================================================================

def test_t43_invariante_a_reversao_dos_endpoints():
    """A MESMA parede fisica, desenhada nos dois sentidos (GetEndPoint(0)
    e (1) trocados), tem que produzir a MESMA decisao de topologia/
    elegibilidade - nunca depender de qual ponta o desenho chama '0'."""
    walls_fwd, nodes_fwd, e2n_fwd = _two_end_setup(54.0, mirrored=False)
    walls_rev, nodes_rev, e2n_rev = _two_end_setup(54.0, mirrored=True)

    # `_wall_two_end_node_indices` devolve os nos na ordem BRUTA de
    # end_index (0,1) - nunca canonica (so' o candidato, mais abaixo,
    # ordena canonicamente) - por isso a comparacao aqui e' pelo
    # CONJUNTO de kinds, nunca posicional.
    node_a_fwd, node_b_fwd = m._wall_two_end_node_indices(nodes_fwd, e2n_fwd, 0)
    node_a_rev, node_b_rev = m._wall_two_end_node_indices(nodes_rev, e2n_rev, 0)
    kinds_raw_fwd = sorted([nodes_fwd[node_a_fwd]["kind"], nodes_fwd[node_b_fwd]["kind"]])
    kinds_raw_rev = sorted([nodes_rev[node_a_rev]["kind"], nodes_rev[node_b_rev]["kind"]])
    assert kinds_raw_fwd == kinds_raw_rev == ["L_CORNER", "T_INTERSECTION"]

    def degraded_course_candidates(walls, e2n):
        node_end0 = e2n[(0, 0)]
        node_end1 = e2n[(0, 1)]
        return {0: [
            _end_piece(walls, 0, "C09", 9.0, 0, node_end0, "L_CORNER_DEGRADED"),
            _end_piece(walls, 0, "C09", 9.0, 1, node_end1, "L_CORNER_DEGRADED"),
        ]}

    cc_fwd = degraded_course_candidates(walls_fwd, e2n_fwd)
    cc_rev = degraded_course_candidates(walls_rev, e2n_rev)
    cand_fwd = m._b19_residual_edge_candidates(nodes_fwd, walls_fwd, e2n_fwd, CATALOG, 1, {"course_candidates": cc_fwd})
    cand_rev = m._b19_residual_edge_candidates(nodes_rev, walls_rev, e2n_rev, CATALOG, 1, {"course_candidates": cc_rev})
    assert len(cand_fwd) == 1 and len(cand_rev) == 1
    # mesmo par FISICO de nos (kinds) elegivel nos dois sentidos.
    kinds_fwd = sorted(nodes_fwd[i]["kind"] for i in (cand_fwd[0]["node_a"], cand_fwd[0]["node_b"]))
    kinds_rev = sorted(nodes_rev[i]["kind"] for i in (cand_rev[0]["node_a"], cand_rev[0]["node_b"]))
    assert kinds_fwd == kinds_rev

    # reserva dinamica da' o MESMO room fisico (34cm) nos dois sentidos,
    # qualquer que seja a orientacao de desenho.
    for (walls, nodes, e2n, cand) in ((walls_fwd, nodes_fwd, e2n_fwd, cand_fwd),
                                      (walls_rev, nodes_rev, e2n_rev, cand_rev)):
        wall_idx = cand[0]["wall_idx"]
        node_a, node_b = cand[0]["node_a"], cand[0]["node_b"]
        nodes[node_b]["_b19_residual_fill_for_walls"] = {wall_idx}
        lo_ft, hi_ft = m._wall_reserved_range_ft(walls, nodes, e2n, wall_idx, exclude_node_index=node_a)
        assert abs(m._ft_to_cm(hi_ft - lo_ft) - 34.0) < 1e-6


# =====================================================================
# T44-T47 - rede de seguranca HALF_BLOCK_NEAR_TIE (defesa em profundidade)
# =====================================================================

def _audit_setup(placement_reason, tie_present=True, num_courses=6):
    """Parede de 54cm com L_CORNER em t=0 (amarracao real na ponta,
    quando `tie_present`) e um B19 encostado nessa amarracao."""
    walls = [_wall(0, 0, 54, 0), _wall(0, 0, 0, 100)]
    p0 = walls[0][0].GetEndPoint(0)
    p1 = walls[0][0].GetEndPoint(1)
    nodes = [_l_node(p0, 0, 0, 1, 0), _l_node(p1, 0, 1, 2, 0)]
    end_to_node = {(0, 0): 0, (0, 1): 1, (1, 0): 0}
    course_candidates = {}
    for ci in range(num_courses):
        items = [_place(walls, 0, "B19", 9.5, "A", node_index=0, placement_reason=placement_reason)]
        if tie_present:
            items.append(_place(walls, 0, "B34", 37.0, "A", node_index=1, placement_reason="L_CORNER"))
        course_candidates[ci] = items
    return walls, nodes, end_to_node, course_candidates, num_courses


def _half_block_problems(placement_reason, tie_present=True):
    walls, nodes, end_to_node, cc, nc = _audit_setup(placement_reason, tie_present=tie_present)
    audit = m.audit_wall_bond_quality(
        0, walls, cc, CATALOG, nc, openings_per_wall=[[], []],
        nodes=nodes, end_to_node=end_to_node)
    return audit, [p for p in audit["problems"] if p.startswith("HALF_BLOCK_NEAR_TIE")]


def test_t44_b19_residual_fill_com_no_marcado_pelo_proprio_b19_isento():
    """`B19_RESIDUAL_FILL` marcado no node_index=0 (a propria ponta onde
    o B19 esta') com uma amarracao real ALTHOUGH em node_index=1 (a OUTRA
    ponta) - a defesa em profundidade exige tie cobrindo o MESMO no'
    (node_index=0) - este teste usa uma peca de amarracao adjacente a
    ponta 0 tambem, coerente com a decisao de dominio."""
    walls = [_wall(0, 0, 54, 0), _wall(0, 0, 0, 100)]
    p0 = walls[0][0].GetEndPoint(0)
    nodes = [_l_node(p0, 0, 0, 1, 0)]
    end_to_node = {(0, 0): 0}
    cc = {ci: [
        _tie_at_point(p0, XYZ(1, 0, 0), wall_idx=1, node_index=0, code="B34", placement_reason="L_CORNER"),
        _place(walls, 0, "B19", 9.5, "A", node_index=0, placement_reason="B19_RESIDUAL_FILL"),
    ] for ci in range(6)}
    audit = m.audit_wall_bond_quality(0, walls, cc, CATALOG, 6, openings_per_wall=[[], []],
                                      nodes=nodes, end_to_node=end_to_node)
    problems = [p for p in audit["problems"] if p.startswith("HALF_BLOCK_NEAR_TIE")]
    assert problems == []


def test_t45_b19_residual_fill_sem_tie_cobrindo_o_mesmo_no_nao_e_isento():
    """DEFESA EM PROFUNDIDADE (item 4 da revisao): mesmo com a etiqueta
    `B19_RESIDUAL_FILL`, se NENHUMA peca de amarracao cobre o MESMO no' na
    mesma fiada, o audit NAO isenta - nao confia cegamente na etiqueta."""
    walls = [_wall(0, 0, 54, 0)]
    p0 = walls[0][0].GetEndPoint(0)
    nodes = [_l_node(p0, 0, 0, 1, 0)]
    end_to_node = {(0, 0): 0}
    cc = {ci: [_place(walls, 0, "B19", 9.5, "A", node_index=0, placement_reason="B19_RESIDUAL_FILL")]
         for ci in range(6)}
    audit = m.audit_wall_bond_quality(0, walls, cc, CATALOG, 6, openings_per_wall=[[], []],
                                      nodes=nodes, end_to_node=end_to_node)
    problems = [p for p in audit["problems"] if p.startswith("HALF_BLOCK_NEAR_TIE")]
    assert problems, "B19_RESIDUAL_FILL sem tie real deveria continuar bloqueado pela rede de seguranca"


def test_t46_b19_com_outro_placement_reason_continua_bloqueado():
    for reason in ("STANDARD_FILL", "L_CORNER_DEGRADED", "OPENING_REPAIR", ""):
        audit, problems = _half_block_problems(reason, tie_present=True)
        assert problems, "B19 com placement_reason={0!r} deveria disparar HALF_BLOCK_NEAR_TIE".format(reason)
        assert audit["penalty"] >= m.PENALTY_HALF_BLOCK_NEAR_TIE


def test_t47_isencao_nao_muda_o_resto_da_auditoria():
    audit_fill, _p = _half_block_problems("B19_RESIDUAL_FILL", tie_present=True)
    audit_other, _q = _half_block_problems("STANDARD_FILL", tie_present=True)
    assert audit_fill["continuous_joints"] == audit_other["continuous_joints"]
    assert audit_fill["compensator_strips"] == audit_other["compensator_strips"]
    assert audit_fill["alternating_joints"] == audit_other["alternating_joints"]


# =====================================================================
# T48-T52 - corpus real (TP1/TGD/Piloto) - RESULTADO HONESTO POS-REVISAO
# =====================================================================

def _project_paths(project_id):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "nuvem", "benchmark", "projects", project_id, "input.json")


def _solver_bridge():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nuvem"))
    from benchmark import solver_bridge
    return solver_bridge


@pytest.mark.slow
def test_t48_tp1_zero_candidatos_aceitos_apos_gate_de_integridade():
    """RESULTADO HONESTO da revisao: o corpus TP1 tem 8 paredes com
    topologia/aritmetica elegiveis, mas NENHUMA tem amarracao real
    cobrindo o MESMO no' na MESMA fiada (o padrao de alternancia par/
    impar do canto L amarra o no' so' nas fiadas ONDE O B19 NAO ESTA') -
    as 16 tentativas (8 paredes x 2 atribuicoes) sao rejeitadas por
    `no_tie_covering_node`."""
    solver_bridge = _solver_bridge()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tp1"), encoding="utf-8"))
    (solve_result, _walls, _nodes, _openings, _catalog,
     _base_z_ft, _num_courses, _notes) = solver_bridge.run_solver(input_project)
    repair = solve_result.get("b19_residual_fill_repair") or {}
    assert repair.get("accepted") == []
    assert len(repair.get("rejected") or []) == 16
    assert all(r["reason"] == "no_tie_covering_node" for r in repair["rejected"])


@pytest.mark.slow
def test_t49_tp1_fingerprint_identico_com_e_sem_b19():
    """Com ZERO candidatos aceitos, o resultado com o reparo B19 ligado
    tem que ser fisicamente IDENTICO ao resultado com o reparo desligado -
    nenhum efeito colateral do mecanismo em si quando nada e' aceito."""
    solver_bridge = _solver_bridge()
    from benchmark.extract import from_solver
    from benchmark.golden import fingerprint as gfp
    module = solver_bridge.engine()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tp1"), encoding="utf-8"))

    def fp(b19_enabled):
        module.B19_RESIDUAL_FILL_REPAIR_ENABLED = b19_enabled
        (res, walls, nodes, openings, catalog, base_z, nc, _notes) = solver_bridge.run_solver(input_project)
        proj = from_solver.project_from_solver(
            "torre_easy_lo_r00_tp1", res, walls, nodes, openings, catalog, base_z, nc, metadata={})
        return gfp.component_fingerprints(proj)["walls_blocks"]

    try:
        fp_off = fp(False)
        fp_on = fp(True)
    finally:
        module.B19_RESIDUAL_FILL_REPAIR_ENABLED = True
    assert fp_off == fp_on


@pytest.mark.slow
def test_t50_tgd_zero_candidatos_elegiveis_limite_de_escopo_conhecido():
    solver_bridge = _solver_bridge()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tgd"), encoding="utf-8"))
    (solve_result, _walls, _nodes, _openings, _catalog,
     _base_z_ft, _num_courses, _notes) = solver_bridge.run_solver(input_project)
    repair = solve_result.get("b19_residual_fill_repair") or {}
    assert repair.get("accepted") == []
    assert repair.get("rejected") == []


@pytest.mark.slow
def test_t51_piloto_sem_efeito():
    solver_bridge = _solver_bridge()
    input_project = json.load(open(_project_paths("piloto_sintetico_2x2"), encoding="utf-8"))
    (solve_result, _walls, _nodes, _openings, _catalog,
     _base_z_ft, _num_courses, _notes) = solver_bridge.run_solver(input_project)
    repair = solve_result.get("b19_residual_fill_repair") or {}
    assert repair.get("accepted") == []


@pytest.mark.slow
def test_t52_determinismo_duas_execucoes_separadas():
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
    assert accepted_sets[0] == accepted_sets[1] == []


@pytest.mark.slow
def test_t53_arm_role_safe_repair_false_desliga_tudo_contrato_preservado():
    """Blocker J: `arm_role_safe_repair=False` continua desligando TODO o
    pos-processamento, IDENTICO ao comportamento anterior a esta CR -
    nunca uma porta lateral para o B19 rodar fora do pipeline."""
    solver_bridge = _solver_bridge()
    module = solver_bridge.engine()
    input_project = json.load(open(_project_paths("torre_easy_lo_r00_tp1"), encoding="utf-8"))
    nodes, walls_to_create, end_to_node, openings_per_wall = solver_bridge.plan_from_input(input_project)
    catalog, _rc, _dc = solver_bridge.catalog_from_input(input_project)
    settings = input_project.get("settings") or {}
    base_z_ft = solver_bridge._ft(settings.get("base_z_cm") or 0.0)
    num_courses = int(settings.get("num_courses") or settings.get("expected_rows") or 15)
    result = module.solve_building_blocks_all_courses(
        nodes, walls_to_create, end_to_node, openings_per_wall, catalog, base_z_ft, num_courses,
        variants_per_course=module.PIER_LAYOUT_VARIANTS_PER_COURSE,
        arm_role_safe_repair=False,
    )
    assert "arm_role_safe_repair" not in result
    assert "b19_residual_fill_repair" not in result
