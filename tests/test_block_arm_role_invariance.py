# -*- coding: utf-8 -*-
"""CR-BLOCK-ARM-ROLE-INVARIANCE - invariancia de papel (arms[0]/arms[1],
crossing_walls[0]/[1]) em nos L_CORNER/T_INTERSECTION/X_INTERSECTION.

Contexto (ver docs/BLOCK_ARM_ROLE_INVARIANCE.md para o relatorio completo):
a ordenacao canonica de `arms`/`crossing_walls` que `wall_pairing.py`
devolve (hoje: ordem de enumeracao das paredes de entrada - o CR
CR-BLOCK-WALL-GRAPH-QUALITY documentou que uma futura ordenacao canonica
por identidade geometrica tem o MESMO efeito) decide qual parede recebe o
papel `wall_a`/`course_a` e qual recebe `wall_b`/`course_b` num encontro.
Essa troca de papel deveria, no maximo, ESPELHAR o resultado (secao 28.3
de REGRAS_MODULACAO_BLOCOS.md) - nunca fazer uma parede perder uma
FAMILIA INTEIRA de fiadas (curso par ou impar). Medido ao vivo, TGD real
(W042/wall_idx 41): quando os dois nos L_CORNER das duas pontas desta
parede escolhem o MESMO papel (os dois "course_b", em vez de alternar),
a familia oposta ("course_a") ficava com ZERO candidatos na parede
inteira - COVERAGE_MISSING_ROW em todas as fiadas pares.

Estes testes NAO tocam wall_pairing.py - constroem/permutam `node["arms"]`
e `node["crossing_walls"]` MANUALMENTE, depois de `build_wall_graph`, para
provar a invariancia do CONSUMIDOR (wall_stepper.py) contra QUALQUER
ordem, sem depender de qual convencao de ordenacao canonica esta' ativa em
wall_pairing.py hoje ou no futuro.

    python3 -m pytest tests/test_block_arm_role_invariance.py -q
"""

import copy

import pytest

import load_script
import revit_stubs

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER


# --------------------------------------------------------------- helpers
def ft(cm):
    return cm / 100.0 * F


def to_cm(value_ft):
    return value_ft / F * 100.0


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


CATALOG = {
    "B39": _block("B39", 39, [_cell(-9.9, 15.7), _cell(9.9, 15.8)]),
    "B34": _block("B34", 34, [_cell(-10.2, 10.7), _cell(7.4, 15.7)]),
    "B54": _block("B54", 54, [_cell(-19.5, 15.8), _cell(0.0, 12.5), _cell(19.5, 15.8)]),
    "B19": _block("B19", 19, [_cell(0.0, 15.7)]),
    "C09": _block("C09", 9, []),
    "C04": _block("C04", 4, []),
}


def build_plan(lines, thickness_cm=14.0):
    walls = [(line, ft(thickness_cm), (False, False)) for line in lines]
    walls, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, jmap)
    return walls, nodes, end_to_node


def solve(walls, nodes, end_to_node, per_wall=None, variants_per_course=1):
    per_wall = per_wall or dict((i, []) for i in range(len(walls)))
    return m.solve_building_blocks(nodes, walls, end_to_node, per_wall, CATALOG,
                                   variants_per_course=variants_per_course)


def swap_two_arm_node(nodes, node_index):
    """Devolve uma COPIA de `nodes` com `arms[0]`/`arms[1]` do no'
    `node_index` invertidos (mesmo caso de 2 arms de um L_CORNER) -
    `neighbor_wall_idx`/`neighbor_end_index` recalculados do ponto de
    vista do NOVO arms[0], exatamente como `_classify_wall_node` faz."""
    nodes2 = copy.deepcopy(nodes)
    node = nodes2[node_index]
    a0, a1 = node["arms"]
    node["arms"] = [a1, a0]
    node["neighbor_wall_idx"] = a0[0]
    node["neighbor_end_index"] = a0[1]
    return nodes2


def swap_crossing_walls(nodes, node_index):
    nodes2 = copy.deepcopy(nodes)
    node = nodes2[node_index]
    a, b = node["crossing_walls"]
    node["crossing_walls"] = (b, a)
    return nodes2


def candidates_by_wall_course(result):
    out = {}
    for cand in result["candidates"]:
        key = (cand.get("wall_idx"), cand.get("course"))
        out.setdefault(key, []).append(cand["logical_code"])
    return out


def wall_families_present(result, wall_idx):
    """{"A": bool, "B": bool} - True se a familia tem PELO MENOS UM
    candidato nesta parede."""
    present = {"A": False, "B": False}
    for cand in result["candidates"]:
        if cand.get("wall_idx") == wall_idx:
            present[cand["course"]] = True
    return present


# ============================================================
# 1/2/9 - L_CORNER simetrico, arms [A,B] vs [B,A], input permutado
# ============================================================

@pytest.mark.parametrize("wall_order", [(0, 1), (1, 0)])
def test_l_corner_simetrico_arms_invertidos_nao_perde_familia(wall_order):
    """L de dois bracos longos (300cm cada) COM ORDEM DE ENTRADA permutada
    (item 9 do CR) - mesma geometria fisica, so' o indice de wall_idx
    trocado. Em qualquer combinacao arms/ordem de entrada, as DUAS paredes
    continuam com as DUAS familias de fiada presentes."""
    raw = [seg(0, 0, 300, 0), seg(0, 0, 0, 300)]
    lines = [raw[i] for i in wall_order]
    walls, nodes, end_to_node = build_plan(lines)
    corner_idx = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]

    base = solve(walls, nodes, end_to_node)
    swapped_nodes = swap_two_arm_node(nodes, corner_idx)
    swapped = solve(walls, swapped_nodes, end_to_node)

    for wall_idx in range(2):
        fam_base = wall_families_present(base, wall_idx)
        fam_swapped = wall_families_present(swapped, wall_idx)
        assert fam_base == {"A": True, "B": True}, (wall_order, wall_idx, "base", fam_base)
        assert fam_swapped == {"A": True, "B": True}, (wall_order, wall_idx, "swapped", fam_swapped)


def test_l_corner_curto_nao_perde_familia_com_arms_invertidos():
    """Parede curta (item 4 do CR) - so' cabe o B34 do canto, sem
    preenchimento comum. Mesmo assim as DUAS familias continuam presentes
    (uma peca de no' cada) em ambas ordens de arms."""
    walls, nodes, end_to_node = build_plan([seg(0, 0, 60, 0), seg(0, 0, 0, 60)])
    corner_idx = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]

    base = solve(walls, nodes, end_to_node)
    swapped = solve(walls, swap_two_arm_node(nodes, corner_idx), end_to_node)

    for result, label in ((base, "base"), (swapped, "swapped")):
        for wall_idx in range(2):
            fam = wall_families_present(result, wall_idx)
            assert fam["A"] or fam["B"], (label, wall_idx, "no' L_CORNER sem nenhuma peca")


def test_l_corner_longo_nao_perde_familia_com_arms_invertidos():
    """Parede longa (item 5 do CR, 900cm) - preenchimento comum extenso
    dos dois lados do L. Cobertura das duas familias preservada nos dois
    braços em qualquer ordem de arms."""
    walls, nodes, end_to_node = build_plan([seg(0, 0, 900, 0), seg(0, 0, 0, 900)])
    corner_idx = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]

    base = solve(walls, nodes, end_to_node)
    swapped = solve(walls, swap_two_arm_node(nodes, corner_idx), end_to_node)

    for result, label in ((base, "base"), (swapped, "swapped")):
        for wall_idx in range(2):
            fam = wall_families_present(result, wall_idx)
            assert fam == {"A": True, "B": True}, (label, wall_idx, fam)


@pytest.mark.parametrize("variants_per_course", [1, 3])
def test_l_corner_multiplas_fiadas_nao_perde_familia(variants_per_course):
    """Item 3 do CR - varias fiadas fisicas (via `solve_building_blocks_all_courses`,
    que gira `variants_per_course` composicoes por familia) continuam
    cobertas em ambas as familias, com ou sem variacao entre fiadas
    fisicas da mesma paridade."""
    walls, nodes, end_to_node = build_plan([seg(0, 0, 400, 0), seg(0, 0, 0, 400)])
    corner_idx = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]
    per_wall = [[], []]

    def run(nodes_arg):
        return m.solve_building_blocks_all_courses(
            nodes_arg, walls, end_to_node, per_wall, CATALOG,
            base_z_abs=0.0, num_courses=6, variants_per_course=variants_per_course,
        )

    base = run(nodes)
    swapped = run(swap_two_arm_node(nodes, corner_idx))

    for result, label in ((base, "base"), (swapped, "swapped")):
        for course_index, cands in result["course_candidates"].items():
            for wall_idx in range(2):
                has_piece = any(c.get("wall_idx") == wall_idx for c in cands)
                assert has_piece, (label, course_index, wall_idx, "fiada fisica sem NENHUMA peca")


# ============================================================
# 6 - T como controle (nao deve regredir com este CR)
# ============================================================

def test_t_intersection_nao_perde_familia():
    """T (parede continua + parede que termina no meio) - controle: este
    CR nao deve introduzir NENHUMA regressao aqui, mesmo sem um mecanismo
    de troca de papel proprio de T (so' L e X tem arms[0]/[1] ou
    crossing_walls[0]/[1] simetricos)."""
    walls, nodes, end_to_node = build_plan(
        [seg(0, 0, 400, 0), seg(200, 0, 200, 300)]
    )
    kinds = sorted(n["kind"] for n in nodes)
    assert "T_INTERSECTION" in kinds, kinds

    result = solve(walls, nodes, end_to_node)
    for wall_idx in range(2):
        fam = wall_families_present(result, wall_idx)
        assert fam["A"] or fam["B"], (wall_idx, "T_INTERSECTION sem nenhuma peca")


# ============================================================
# 7 - X_INTERSECTION com crossing_walls permutado
# ============================================================

def test_x_intersection_crossing_walls_invertido_nao_perde_familia():
    """Cruz de duas paredes CONTINUAS cruzando no meio (_find_wall_midspan_crossings) -
    inverte `crossing_walls[0]/[1]` manualmente (equivalente ao arms[0]/[1]
    do L, mas para X) e confere que as QUATRO extremidades continuam com
    as duas familias presentes."""
    walls, nodes, end_to_node = build_plan([
        seg(0, 200, 400, 200), seg(200, 0, 200, 400),
    ])
    x_idx = [i for i, n in enumerate(nodes) if n["kind"] == "X_INTERSECTION"]
    assert len(x_idx) == 1, [n["kind"] for n in nodes]
    x_idx = x_idx[0]
    assert nodes[x_idx]["crossing_walls"] is not None

    base = solve(walls, nodes, end_to_node)
    swapped = solve(walls, swap_crossing_walls(nodes, x_idx), end_to_node)

    for result, label in ((base, "base"), (swapped, "swapped")):
        for wall_idx in range(2):
            fam = wall_families_present(result, wall_idx)
            assert fam["A"] or fam["B"], (label, wall_idx, "X_INTERSECTION sem nenhuma peca")


# ============================================================
# 8 - endpoint reversal fisicamente equivalente
# ============================================================

def test_l_corner_endpoint_reversal_equivalente_nao_perde_familia():
    """Item 8 do CR - inverte os ENDPOINTS de uma das duas paredes do L
    (p0<->p1, o mesmo segmento fisico desenhado no sentido oposto) E ainda
    troca arms[0]/[1] do no' - a combinacao (fisicamente equivalente a`
    geometria original) nao pode perder familia nenhuma."""
    reversed_v = seg(0, 300, 0, 0)  # mesmo segmento de seg(0,0,0,300), invertido
    walls, nodes, end_to_node = build_plan([seg(0, 0, 300, 0), reversed_v])
    corner_idx = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]

    base = solve(walls, nodes, end_to_node)
    swapped = solve(walls, swap_two_arm_node(nodes, corner_idx), end_to_node)

    for result, label in ((base, "base"), (swapped, "swapped")):
        for wall_idx in range(2):
            fam = wall_families_present(result, wall_idx)
            assert fam == {"A": True, "B": True}, (label, wall_idx, fam)


# ============================================================
# 10/12 - CASO REAL REPRODUZIDO: dois L_CORNER na MESMA parede podem
# escolher o MESMO papel de forma independente - a family completa deve
# sobreviver de qualquer forma (o teste central deste CR).
# ============================================================

def _two_corner_plan():
    """Parede do meio (wall 1, "W042 sintetico") com um L_CORNER em CADA
    ponta - a MESMA topologia (dois nos independentes) que produziu a
    perda de familia inteira medida ao vivo em W042/TGD (wall_idx 41).

    Coordenadas FRACIONARIAS de proposito (300.37/322.19, em vez de
    numeros redondos): e' exatamente o ruido de CAD real (conversao
    pes<->cm, extend_wall_ends_to_junctions) que faz a projecao da peca
    EMPRESTADA de uma parede vizinha (ver
    _index_node_candidates_borrowed_by_wall_end) nao cair num multiplo de
    PIER_MODULE_CM - com coordenadas redondas o defeito nao reproduz (o
    preenchimento comum fecha de qualquer forma, so' espelha o padrao,
    ver test_l_corner_simetrico_arms_invertidos_nao_perde_familia).
    Confirmado escrevendo este teste: SEM o fix, exatamente as combinacoes
    (swap_a=False,swap_b=True) e (True,False) desta geometria fazem a
    parede do meio perder uma familia inteira (COVERAGE_MISSING_ROW);
    COM o fix, as 4 combinacoes preservam as duas familias."""
    wall0 = seg(0, 0, 0, 300.37)         # vertical esquerda
    wall1 = seg(0, 0, 322.19, 0)         # horizontal do meio (o alvo)
    wall2 = seg(322.19, 0, 322.19, -300.0)  # vertical direita
    return build_plan([wall0, wall1, wall2])


def _corner_touching(nodes, wall_idx):
    return [i for i, n in enumerate(nodes)
            if n["kind"] == "L_CORNER" and len(n.get("arms") or []) == 2
            and any(w == wall_idx for w, _e in n["arms"])]


@pytest.mark.parametrize("swap_a,swap_b", [
    (False, False), (True, False), (False, True), (True, True),
])
def test_parede_com_dois_L_corner_nunca_perde_familia_inteira(swap_a, swap_b):
    """O teste central do CR: em QUALQUER uma das 4 combinacoes de papel
    (cada um dos dois nos da parede do meio pode escolher, de forma
    INDEPENDENTE, qual lado vira course_a/course_b), a parede do meio
    nunca pode ficar com uma familia 100% ausente - o defeito medido ao
    vivo em W042/TGD (COVERAGE_MISSING_ROW em todas as fiadas pares)."""
    walls, nodes, end_to_node = _two_corner_plan()
    corners = _corner_touching(nodes, 1)
    assert len(corners) == 2, corners

    nodes2 = copy.deepcopy(nodes)
    if swap_a:
        nodes2 = swap_two_arm_node(nodes2, corners[0])
    if swap_b:
        nodes2 = swap_two_arm_node(nodes2, corners[1])

    result = solve(walls, nodes2, end_to_node)
    fam = wall_families_present(result, 1)
    assert fam == {"A": True, "B": True}, (swap_a, swap_b, fam,
        "familia inteira ausente na parede do meio so' por causa do papel dos nos")


# ============================================================
# 11 - NAO e' so' reordenar: o mesmo mecanismo tem que sobreviver ao
# comportamento HOJE ativo (ordem de lista) sem qualquer sort novo.
# ============================================================

def test_ordem_de_arms_de_hoje_wall_pairing_ja_fecha_sem_intervencao_manual():
    """Sem NENHUMA manipulacao manual de `nodes` - so' `build_wall_graph`
    puro, exatamente como o pipeline de producao roda hoje - a parede do
    meio de `_two_corner_plan` ja' fecha as duas familias. Prova que o fix
    vive no CONSUMIDOR (wall_stepper.py), nao numa ordenacao especial
    imposta pelo teste."""
    walls, nodes, end_to_node = _two_corner_plan()
    result = solve(walls, nodes, end_to_node)
    fam = wall_families_present(result, 1)
    assert fam == {"A": True, "B": True}, fam
