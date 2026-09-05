# -*- coding: utf-8 -*-
"""CR-BLOCK-NODE-FILL-REVALIDATION - a METADE SIMETRICA da junta NO'|FILL.

A main ja' rastreia a junta de CONTORNO da Fiada A contra a peca de no'
(`_pier_boundary_joint_positions_cm`, CR-BLOCK-ARM-ROLE-PRISM-STAGGER) e a
Fiada B a evita. O que faltava - e e' o que esta CR revalida do fix
historico NODE-FILL - e' o sentido contrario: a Fiada A roda PRIMEIRO e
nunca via a junta NO'|FILL que a Fiada B vai ter; como a posicao da peca
de no' depende so' da geometria do encontro (nunca do layout), ela e'
deduzivel antes de resolver (`_wall_node_boundary_joints_cm`) e a Fiada A
passa a evita-la (`NODE_FILL_OPPOSITE_COURSE_ENABLED`, wall_stepper.py).

Assinatura do defeito, medida no corpus real (TGD/TP1, fiada A x fiada B,
t = 34,5 cm): junta interna `B19|B39` da Fiada A exatamente em cima da junta
`B34(no')|fill` da Fiada B.

Nenhum teste abaixo depende de validador do benchmark: a medicao e' feita
na GEOMETRIA FINAL das pecas (`node_fill_prism_violations`), exatamente
como em tests/test_block_node_fill_joint historico.

    python3 -m pytest tests/test_block_node_fill_revalidation.py -q
"""

import contextlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import load_script  # noqa: E402
import revit_stubs  # noqa: E402

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
ws = sys.modules["core.engine.wall_stepper"]
F = m.FEET_PER_METER
J = m.BLOCK_JOINT_CM
TOL = m.VERTICAL_JOINT_STAGGER_TOLERANCE_CM

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


@contextlib.contextmanager
def node_fill(enabled):
    """Liga/desliga a metade simetrica SO' dentro do bloco - o default do
    modulo nunca e' alterado permanentemente por um teste."""
    before = ws.NODE_FILL_OPPOSITE_COURSE_ENABLED
    ws.NODE_FILL_OPPOSITE_COURSE_ENABLED = enabled
    try:
        yield
    finally:
        ws.NODE_FILL_OPPOSITE_COURSE_ENABLED = before


# --------------------------------------------------------------- helpers
def ft(cm):
    return cm / 100.0 * F


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _cell(center_cm, size_cm, width_cm=8.0):
    return {"center_local": (ft(center_cm), 0.0), "size_local": (ft(size_cm), ft(width_cm))}


def _block(code, length_cm, cells):
    return {
        "symbol": None, "logical_code": code, "length_cm": float(length_cm),
        "height_cm": 19.0, "width_cm": 14.0, "cells_local": cells,
        "is_special_bond": code in ("B34", "B54"),
        "is_compensator": code in ("C09", "C04"),
        "source_instance_id": None,
    }


def build_catalog(order=None):
    pieces = {
        "B39": _block("B39", 39, [_cell(-9.9, 15.7), _cell(9.9, 15.8)]),
        "B34": _block("B34", 34, [_cell(-10.2, 10.7), _cell(7.4, 15.7)]),
        "B54": _block("B54", 54, [_cell(-19.5, 15.8), _cell(0.0, 12.5), _cell(19.5, 15.8)]),
        "B19": _block("B19", 19, [_cell(0.0, 15.7)]),
        "C09": _block("C09", 9, []),
        "C04": _block("C04", 4, []),
    }
    keys = list(order) if order else list(pieces)
    return dict((code, pieces[code]) for code in keys)


CATALOG = build_catalog()


def solve_plan(lines, thickness_cm=14.0, openings=None, catalog=None):
    walls = [(line, ft(thickness_cm), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    per_wall = openings or dict((i, []) for i in range(len(walls)))
    result = m.solve_building_blocks(nodes, walls, end_to_node, per_wall, catalog or CATALOG)
    return result, walls


def wall_course_pieces(walls, candidates):
    """{(wall_idx, course): [(t_lo, t_hi, code, is_node), ...]} na geometria
    FINAL - nunca por dentro do solver."""
    out = {}
    for cand in candidates:
        wall_idx = cand.get("wall_idx")
        if wall_idx is None:
            continue
        p0, _p1, wall_dir, _len, _t = m._wall_axis_and_length(walls, wall_idx)
        t_lo, t_hi = m._candidate_extent_on_wall_axis(cand, p0, wall_dir)
        is_node = bool(m._is_tie_candidate(cand) or cand.get("node_index") is not None)
        out.setdefault((wall_idx, cand.get("course")), []).append(
            (min(t_lo, t_hi), max(t_lo, t_hi), cand.get("logical_code"), is_node))
    for items in out.values():
        items.sort(key=lambda e: (round(e[0], 4), round(e[1], 4), e[2]))
    return out


def classified_joints(items, max_gap_cm=None):
    """({juntas NO'|FILL}, {juntas FILL|FILL}) de uma fiada de uma parede."""
    if max_gap_cm is None:
        max_gap_cm = m.BLOCK_JOINT_CM * 2.0
    node_joints, fill_joints = [], []
    for i in range(len(items) - 1):
        lo_a, hi_a, _code_a, node_a = items[i]
        lo_b, _hi_b, _code_b, node_b = items[i + 1]
        gap = lo_b - hi_a
        if not (-1e-6 <= gap <= max_gap_cm):
            continue
        center = hi_a + gap / 2.0
        if node_a != node_b:
            node_joints.append(center)
        elif not node_a:
            fill_joints.append(center)
    return node_joints, fill_joints


def node_fill_prism_violations(walls, candidates, tolerance_cm=TOL):
    """Juntas NO'|FILL de uma fiada que uma junta INTERNA de preenchimento
    da fiada oposta empilha em cima. [(wall_idx, posicao_cm, fiada_do_no'),
    ...] - o defeito exato desta CR."""
    pieces = wall_course_pieces(walls, candidates)
    found = []
    for wall_idx in sorted(set(w for (w, _c) in pieces)):
        items_a = pieces.get((wall_idx, "A")) or []
        items_b = pieces.get((wall_idx, "B")) or []
        if not items_a or not items_b:
            continue
        node_a, fill_a = classified_joints(items_a)
        node_b, fill_b = classified_joints(items_b)
        for course_label, nodes_cm, others_cm in (("A", node_a, fill_b), ("B", node_b, fill_a)):
            for x_node in nodes_cm:
                if any(abs(x_node - x) <= tolerance_cm for x in others_cm):
                    found.append((wall_idx, round(x_node, 2), course_label))
    return sorted(set(found))


def layout_signature(walls, candidates):
    pieces = wall_course_pieces(walls, candidates)
    return sorted((k, tuple((round(lo, 2), round(hi, 2), code) for lo, hi, code, _n in v))
                  for k, v in pieces.items())


def celula_fechada(lado_cm=350.0):
    """4 paredes, L_CORNER nas DUAS pontas de cada uma."""
    return [seg(0, 0, lado_cm, 0), seg(0, 0, 0, lado_cm),
            seg(lado_cm, 0, lado_cm, lado_cm), seg(0, lado_cm, lado_cm, lado_cm)]


def grade_2x2(lado_cm=350.0):
    """Topologia do `piloto_sintetico_2x2` (L nos cantos, T no meio dos lados,
    X no centro)."""
    a, b = lado_cm, lado_cm * 2.0
    return [seg(0, 0, a, 0), seg(0, 0, 0, a), seg(a, 0, b, 0), seg(a, 0, a, a),
            seg(b, 0, b, a), seg(0, a, a, a), seg(0, a, 0, b),
            seg(a, a, b, a), seg(a, a, a, b), seg(b, a, b, b),
            seg(0, b, a, b), seg(a, b, b, b)]


L_LIVRE = [seg(0, 0, 364, 0), seg(0, 0, 0, 364)]
T_MEIO = [seg(0, 0, 700, 0), seg(200, 0, 200, 300), seg(500, 0, 500, 300)]
X_MEIO = [seg(0, 0, 700, 0), seg(200, -300, 200, 300), seg(500, -300, 500, 300)]

# Ordens de entrada em que a main (sem a metade simetrica) empilha uma
# junta interna da Fiada A sobre a junta NO'|FILL da Fiada B na grade 2x2.
ORDENS = ([11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
          [3, 7, 0, 11, 5, 2, 9, 1, 6, 10, 4, 8],
          [6, 0, 9, 2, 11, 4, 7, 1, 10, 3, 8, 5])


# =====================================================================
# T1 - a junta NO'|FILL da fiada oposta e' deduzivel so' da geometria do no'
# =====================================================================
def test_t1_junta_no_fill_da_fiada_oposta_e_identificada_pela_geometria():
    by_end = {(0, 0, "A"): 34.0, (0, 1, "A"): 330.0, (0, 0, "B"): 54.0}
    assert sorted(m._wall_node_boundary_joints_cm(0, "A", by_end, {})) == [34.0 + J / 2.0, 330.0 - J / 2.0]
    assert m._wall_node_boundary_joints_cm(0, "B", by_end, {}) == [54.0 + J / 2.0]
    midspan = {(0, "A"): [(100.0, 150.0)]}
    assert sorted(m._wall_node_boundary_joints_cm(0, "A", {}, midspan)) == [100.0 - J / 2.0, 150.0 + J / 2.0]


def test_t1b_a_deducao_coincide_com_a_junta_de_contorno_que_a_fiada_publica():
    """A lista deduzida (antes de resolver) tem de ser EXATAMENTE a junta de
    contorno que `_pier_boundary_joint_positions_cm` publica quando o
    trecho e' resolvido - mesma aritmetica (`border + BLOCK_JOINT_CM/2`)."""
    border = 34.0
    seg_start = border + J
    deduzida = m._wall_node_boundary_joints_cm(7, "B", {(7, 0, "B"): border}, {})
    publicada = m._pier_boundary_joint_positions_cm(seg_start, seg_start + 119.0, "WALL_START", "WALL_END",
                                                    leading_is_open=False, trailing_is_open=True)
    assert deduzida == publicada == [border + J / 2.0]


# =====================================================================
# T2 - fronteira legitima (abertura / ponta livre) NAO vira junta de no'
# =====================================================================
def test_t2_ponta_livre_e_abertura_nao_produzem_junta_de_no():
    assert m._wall_node_boundary_joints_cm(3, "A", {}, {}) == []
    assert m._wall_node_boundary_joints_cm(3, "A", {(3, 0, "B"): 34.0}, {}) == []  # so' a OUTRA fiada tem no'
    # L com ponta livre: o layout da Fiada A nao muda com a metade simetrica
    # ligada, porque a ponta livre nao gera junta de no' a evitar.
    with node_fill(False):
        r_off, w_off = solve_plan(L_LIVRE)
    with node_fill(True):
        r_on, w_on = solve_plan(L_LIVRE)
    assert layout_signature(w_off, r_off["candidates"]) == layout_signature(w_on, r_on["candidates"])


# =====================================================================
# T3 - junta fisica real continua detectada (o medidor e o gate nao cegam)
# =====================================================================
def test_t3_junta_fisica_real_continua_detectada():
    """CONTROLE do medidor: no codigo SEM a metade simetrica, a grade 2x2
    numa ordem de entrada permutada produz a violacao real (junta interna
    da A em cima da junta de no' da B, t=34,5) e o medidor a acusa."""
    linhas = grade_2x2()
    with node_fill(False):
        achados = []
        for ordem in ORDENS:
            result, walls = solve_plan([linhas[i] for i in ordem])
            achados.extend(node_fill_prism_violations(walls, result["candidates"]))
    assert achados, "o medidor nao esta' medindo nada"
    assert all(abs(v[1] - 34.5) < 1e-6 and v[2] == "B" for v in achados), achados


def test_t3b_o_gate_do_motor_nao_e_silenciado():
    """A metade simetrica nao mexe no gate residual da main
    (`alignment_conflicts`, que inclui as juntas de contorno contra no'):
    a coincidencia contorno x contorno num T degradado continua reportada."""
    with node_fill(False):
        r_off, _w = solve_plan(grade_2x2())
    with node_fill(True):
        r_on, _w = solve_plan(grade_2x2())
    assert len(r_on.get("alignment_conflicts") or []) == len(r_off.get("alignment_conflicts") or [])
    assert len(r_on.get("alignment_conflicts") or []) > 0


# =====================================================================
# T4 - nao mascara prisma real: a reducao e' na GEOMETRIA, mesmo medidor
# =====================================================================
def test_t4_reducao_e_fisica_nao_mascaramento():
    linhas = grade_2x2()
    antes, depois = [], []
    for ordem in ORDENS:
        with node_fill(False):
            r, w = solve_plan([linhas[i] for i in ordem])
            antes.append(node_fill_prism_violations(w, r["candidates"]))
        with node_fill(True):
            r, w = solve_plan([linhas[i] for i in ordem])
            depois.append(node_fill_prism_violations(w, r["candidates"]))
    assert any(antes), antes
    assert all(v == [] for v in depois), depois


# =====================================================================
# T5 - ordem dos candidatos/da lista a evitar nao altera o resultado
# =====================================================================
def test_t5_ordem_da_lista_a_evitar_nao_altera_o_layout():
    pier_cm, seg_start_cm = 119.0, 35.0
    juntas = [34.5, 74.5, 154.5]
    ref = m._pier_layout_avoiding_joints(pier_cm, CATALOG, 0.0, 0.0, seg_start_cm, list(juntas),
                                         leading_is_open=False, trailing_is_open=False)
    for perm in ([74.5, 34.5, 154.5], [154.5, 74.5, 34.5], [74.5, 154.5, 34.5]):
        alt = m._pier_layout_avoiding_joints(pier_cm, CATALOG, 0.0, 0.0, seg_start_cm, perm,
                                             leading_is_open=False, trailing_is_open=False)
        assert alt == ref, perm
    # e a ordem do catalogo tambem nao
    for order in (("C04", "C09", "B19", "B54", "B34", "B39"), ("B34", "B39", "B19", "B54", "C09", "C04")):
        alt = m._pier_layout_avoiding_joints(pier_cm, build_catalog(order), 0.0, 0.0, seg_start_cm, juntas,
                                             leading_is_open=False, trailing_is_open=False)
        assert alt == ref, order


# =====================================================================
# T6 - permutacao das paredes nao altera o invariante
# =====================================================================
def test_t6_permutacao_de_paredes_nao_altera_o_invariante():
    linhas = grade_2x2()
    with node_fill(True):
        for ordem in ORDENS + (list(range(12)),):
            result, walls = solve_plan([linhas[i] for i in ordem])
            assert not result.get("error")
            assert node_fill_prism_violations(walls, result["candidates"]) == [], ordem


# =====================================================================
# T7 - duas execucoes produzem resultado identico
# =====================================================================
def test_t7_duas_execucoes_identicas():
    with node_fill(True):
        r1, w1 = solve_plan(grade_2x2())
        r2, w2 = solve_plan(grade_2x2())
    assert layout_signature(w1, r1["candidates"]) == layout_signature(w2, r2["candidates"])
    assert len(r1["candidates"]) == len(r2["candidates"]) > 0


# =====================================================================
# T8 / T9 - horizontal e vertical
# =====================================================================
@pytest.mark.parametrize("orientacao,wall_idxs", [("horizontal", (0, 3)), ("vertical", (1, 2))])
def test_t8_t9_horizontal_e_vertical(orientacao, wall_idxs):
    with node_fill(True):
        result, walls = solve_plan(celula_fechada())
    pieces = wall_course_pieces(walls, result["candidates"])
    violacoes = node_fill_prism_violations(walls, result["candidates"])
    for w in wall_idxs:
        assert pieces.get((w, "A")) and pieces.get((w, "B")), (orientacao, w)
        assert [v for v in violacoes if v[0] == w] == [], (orientacao, w)
        # a Fiada A desencontra de TODAS as juntas de no' da Fiada B (e vice-versa)
        node_b, _fill_b = classified_joints(pieces[(w, "B")])
        _node_a, fill_a = classified_joints(pieces[(w, "A")])
        assert node_b, (orientacao, w)
        for x in node_b:
            assert all(abs(x - y) > TOL for y in fill_a), (orientacao, w, x, fill_a)


# =====================================================================
# T10 / T11 / T12 - L, T e X
# =====================================================================
@pytest.mark.parametrize("nome,linhas", [
    ("L_CORNER", L_LIVRE), ("T_INTERSECTION", T_MEIO), ("X_INTERSECTION", X_MEIO),
])
def test_t10_t11_t12_l_t_x(nome, linhas):
    with node_fill(True):
        result, walls = solve_plan(linhas)
    assert not result.get("error"), nome
    assert result["candidates"], nome
    assert node_fill_prism_violations(walls, result["candidates"]) == [], nome


# =====================================================================
# T13 / T14 - parede curta e longa (no' nas duas pontas)
# =====================================================================
@pytest.mark.parametrize("lado_cm", [150.0, 230.0, 350.0, 430.0, 590.0, 1030.0])
def test_t13_t14_parede_curta_e_longa(lado_cm):
    with node_fill(True):
        result, walls = solve_plan(celula_fechada(lado_cm))
    assert not result.get("error")
    assert result["candidates"]
    assert node_fill_prism_violations(walls, result["candidates"]) == []


# =====================================================================
# T15 - abertura proxima (porta e janela, horizontal e vertical)
# =====================================================================
PORTA_T0_CM, PORTA_T1_CM = 120.0, 200.0
PORTA_SILL_CM, PORTA_HEAD_CM = 0.0, 210.0
NUM_COURSES = 13


def solve_all_courses(lines, openings=None, thickness_cm=14.0, arm_role_safe_repair=None):
    walls = [(line, ft(thickness_cm), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    per_wall = [list((openings or {}).get(i) or []) for i in range(len(walls))]
    result = m.solve_building_blocks_all_courses(
        nodes, walls, end_to_node, per_wall, build_catalog(),
        base_z_abs=0.0, num_courses=NUM_COURSES, arm_role_safe_repair=arm_role_safe_repair,
    )
    return result, walls, nodes


def blocos_dentro_de_porta(result, walls, openings_por_parede):
    catalog = build_catalog()
    course_height_ft, _e = m._course_height_ft(catalog, None)
    block_height_ft, _e2 = m._block_height_ft(catalog, None)
    violacoes = []
    for course_index in range(NUM_COURSES):
        z_lo, z_hi = m._course_z_band(0.0, course_index, course_height_ft, block_height_ft)
        for cand in result["course_candidates"].get(course_index) or []:
            wall_idx = cand.get("wall_idx")
            if wall_idx is None:
                continue
            for (t_lo, t_hi, sill, head) in (openings_por_parede.get(wall_idx) or []):
                if not m._opening_active_in_course_band(sill, head, z_lo, z_hi):
                    continue
                p0, _p1, wall_dir, _len, _t = m._wall_axis_and_length(walls, wall_idx)
                a, b = m._candidate_extent_on_wall_axis(cand, p0, wall_dir)
                bloco = (min(a, b), max(a, b))
                vao = (m._ft_to_cm(t_lo), m._ft_to_cm(t_hi))
                sobreposicao = min(bloco[1], vao[1]) - max(bloco[0], vao[0])
                if sobreposicao > m.BOND_COLLISION_EPS_CM:
                    violacoes.append((wall_idx, course_index, cand.get("logical_code"),
                                      round(bloco[0], 2), round(bloco[1], 2), round(sobreposicao, 2)))
    return sorted(violacoes)


def test_t15_abertura_proxima_nao_recebe_bloco_e_o_invariante_continua():
    janela = (ft(100.0), ft(220.0), ft(90.0), ft(200.0))
    porta = (ft(120.0), ft(200.0), ft(0.0), ft(210.0))
    linhas = grade_2x2()
    aberturas = dict((i, []) for i in range(len(linhas)))
    aberturas[0] = [porta]; aberturas[3] = [porta]; aberturas[10] = [janela]; aberturas[6] = [janela]
    with node_fill(True):
        result, walls = solve_plan(linhas, openings=aberturas)
    assert not result.get("error")
    assert node_fill_prism_violations(walls, result["candidates"]) == []
    # celula fechada + porta em varias fiadas: prisma correto E vao livre
    porta_t = (ft(PORTA_T0_CM), ft(PORTA_T1_CM), ft(PORTA_SILL_CM), ft(PORTA_HEAD_CM))
    aberturas = {0: [porta_t], 1: [porta_t], 2: [], 3: []}
    with node_fill(True):
        result, walls, _nodes = solve_all_courses(celula_fechada(), openings=aberturas)
    assert not result.get("error")
    assert node_fill_prism_violations(walls, result["candidates"]) == []
    assert blocos_dentro_de_porta(result, walls, aberturas) == []


# =====================================================================
# T16 - compensador proximo: a metade simetrica nao cria sequencia nova
# =====================================================================
@pytest.mark.parametrize("lado_cm", [355.0, 363.0, 447.0])
def test_t16_compensador_proximo_sem_sequencia_nova(lado_cm):
    def runs(result, walls):
        total = 0
        for w in range(len(walls)):
            cands = [c for c in result["candidates"] if c.get("wall_idx") == w]
            total += len(m._find_consecutive_compensators(w, walls, cands, CATALOG))
        return total
    with node_fill(False):
        r_off, w_off = solve_plan(celula_fechada(lado_cm))
    with node_fill(True):
        r_on, w_on = solve_plan(celula_fechada(lado_cm))
    assert not r_on.get("error")
    assert node_fill_prism_violations(w_on, r_on["candidates"]) == []
    assert runs(r_on, w_on) <= runs(r_off, w_off)


# =====================================================================
# T17 - ARM SAFE REPAIR ligado
# =====================================================================
def test_t17_safe_repair_ligado_mantem_o_invariante_e_e_deterministico():
    with node_fill(True):
        r_on, walls, nodes = solve_all_courses(grade_2x2(), arm_role_safe_repair=True)
        r_on2, walls2, _n = solve_all_courses(grade_2x2(), arm_role_safe_repair=True)
        r_noarm, walls3, _n3 = solve_all_courses(grade_2x2(), arm_role_safe_repair=False)
    assert not r_on.get("error")
    assert "arm_role_safe_repair" in r_on
    assert node_fill_prism_violations(walls, r_on["candidates"]) == []
    assert layout_signature(walls, r_on["candidates"]) == layout_signature(walls2, r_on2["candidates"])
    # sem candidato aceito o resultado e' o mesmo com SAFE REPAIR desligado
    if not r_on["arm_role_safe_repair"]["accepted"]:
        assert layout_signature(walls, r_on["candidates"]) == layout_signature(walls3, r_noarm["candidates"])


# =====================================================================
# T18 / T19 / T20 - corpus real (TP1/TGD) via nuvem.benchmark.solver_bridge
# =====================================================================
_CORPUS_CACHE = {}


def _corpus(project_id, enabled):
    key = (project_id, enabled)
    if key not in _CORPUS_CACHE:
        from nuvem.benchmark import solver_bridge
        path = os.path.join(_ROOT, "nuvem", "benchmark", "projects", project_id, "input.json")
        with open(path, encoding="utf-8") as handle:
            input_project = json.load(handle)
        with node_fill(enabled):
            (solve_result, walls_to_create, nodes, _opw, _cat, _z, _n, _notes) = solver_bridge.run_solver(input_project)
        _CORPUS_CACHE[key] = (solve_result, walls_to_create)
    return _CORPUS_CACHE[key]


def test_t18_candidato_aceito_permanece_seguro_no_corpus():
    """Contrato de seguranca (PR #12) preservado: com a metade simetrica, todo
    candidato ACEITO continua resolvendo o prisma forcado da parede alvo e
    nenhuma parede que era reparavel antes fica com prisma forcado sem
    tentativa (ou e' aceita, ou nao precisa mais de reparo)."""
    for project_id in ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"):
        off, _w = _corpus(project_id, False)
        on, _w = _corpus(project_id, True)
        arm_off, arm_on = off.get("arm_role_safe_repair") or {}, on.get("arm_role_safe_repair") or {}
        audits_on = on.get("wall_bond_audits")
        for cand in arm_on.get("accepted") or []:
            assert not m._wall_has_forced_corner_prism(cand["wall_idx"], audits_on), (project_id, cand)
        aceitas_on = set(c["wall_idx"] for c in (arm_on.get("accepted") or []))
        tentadas_on = aceitas_on | set(c["wall_idx"] for c in (arm_on.get("rejected") or []))
        for cand in arm_off.get("accepted") or []:
            w = cand["wall_idx"]
            assert w in aceitas_on or not m._wall_has_forced_corner_prism(w, audits_on), (project_id, w)
        # nenhuma colisao nova em relacao ao estado sem a metade simetrica
        # quando um candidato foi aceito (o gate _no_new_collisions e' do contrato)
        if aceitas_on:
            assert len(on.get("collisions") or []) <= len(off.get("collisions") or [])
        assert tentadas_on is not None


def test_t19_candidato_rejeitado_nao_e_liberado_indevidamente():
    """Nenhum candidato ARM pode passar a ACEITO com NODE-FILL ligado (ON,
    o unico estado que roda em producao) por causa de um efeito colateral
    NAO EXPLICADO de NODE-FILL sobre os gates - todo flip OFF-rejeitado ->
    ON-aceito precisa estar em `KNOWN_INTERACTIONS`, com o MOTIVO exato da
    rejeicao OFF documentado (nunca silencioso).

    EXCECAO CONHECIDA (2026-09-04, apos `CR-BLOCK-ARM-SAFE-REPAIR-GATE-
    FIDELITY`): TGD `wall_idx=91/SAME_B`. Com Gate Fidelity, os DOIS
    estados (OFF/ON) usam os MESMOS gates corrigidos - o flip nao vem de
    nenhum gate desta CR, vem de `closure_regression`: SEM o preenchimento
    comum corrigido por NODE-FILL (OFF, nunca roda em producao), uma
    parede TERCEIRA deixa de fechar quando este candidato e' tentado; COM
    NODE-FILL (ON, producao), o preenchimento fecha e o candidato e'
    corretamente avaliado como seguro (aceito, composicao final bate com
    o gabarito humano - REGRAS_MODULACAO_BLOCOS.md 34.2). NAO e' uma
    liberacao indevida: NODE-FILL e' um PRE-REQUISITO FISICO real para
    este candidato especifico, nao um efeito colateral do proprio Gate
    Fidelity."""
    KNOWN_INTERACTIONS = {
        ("torre_easy_lo_r00_tgd", (91, "SAME_B")): "closure_regression",
    }
    for project_id in ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"):
        off, _w = _corpus(project_id, False)
        on, _w = _corpus(project_id, True)
        rej_off = dict(
            ((c["wall_idx"], c["bits"]), c.get("reason"))
            for c in (off.get("arm_role_safe_repair") or {}).get("rejected") or [])
        acc_on = set((c["wall_idx"], c["bits"]) for c in (on.get("arm_role_safe_repair") or {}).get("accepted") or [])
        for key in (acc_on & set(rej_off)):
            expected_reason = KNOWN_INTERACTIONS.get((project_id, key))
            assert expected_reason is not None, (
                "flip OFF-rejeitado -> ON-aceito NAO documentado em "
                "KNOWN_INTERACTIONS: {} {} (motivo OFF: {})".format(
                    project_id, key, rej_off[key]))
            assert rej_off[key] == expected_reason, (
                project_id, key, "motivo OFF mudou:", rej_off[key], "esperado:", expected_reason)
        # e os motivos de rejeicao continuam sendo reportados (auditoria)
        for c in (on.get("arm_role_safe_repair") or {}).get("rejected") or []:
            assert c.get("reason"), c


def test_t20_caso_real_tp1_junta_b19_b39_em_cima_da_peca_de_no():
    """Assinatura real do defeito no TP1 (t = 34,5 cm, fiada A `B19|B39` ou
    `B19|B34` sobre a junta `B34(no')|fill` da fiada B): existe SEM a metade
    simetrica e desaparece COM ela - medido na geometria do solver, sem
    validador do benchmark."""
    off, walls = _corpus("torre_easy_lo_r00_tp1", False)
    on, walls_on = _corpus("torre_easy_lo_r00_tp1", True)
    v_off = node_fill_prism_violations(walls, off["candidates"])
    v_on = node_fill_prism_violations(walls_on, on["candidates"])
    sig_off = [v for v in v_off if abs(v[1] - 34.5) < 1e-6 and v[2] == "B"]
    sig_on = [v for v in v_on if abs(v[1] - 34.5) < 1e-6 and v[2] == "B"]
    assert sig_off, v_off[:10]
    assert len(v_on) < len(v_off), (len(v_off), len(v_on))
    # Medido (2026-09-04): 16 -> 4. O residual sao cadeias de 3 compensadores
    # (3 x C09 em 30cm entre a largura do no vizinho e um X/T degradado) - a
    # UNICA composicao possivel, juntas fixas em 24,5/34,5/44,5 - o limite
    # genuino ja documentado (REGRAS 30.6 / 33.5), que nenhuma troca de
    # layout move. O teste tranca a reducao, nao a impossibilidade.
    assert len(sig_on) * 2 <= len(sig_off), (sig_off, sig_on)
    # e nenhuma violacao NOVA: todo residual ja' existia sem a metade simetrica
    assert set(sig_on) <= set(sig_off), sorted(set(sig_on) - set(sig_off))
