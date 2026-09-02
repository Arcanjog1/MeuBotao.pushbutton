# -*- coding: utf-8 -*-
"""CR-BLOCK-NODE-FILL-JOINT - a junta PECA DE NO' | PREENCHIMENTO.

O defeito que esta suite tranca: `_layout_internal_joint_positions_cm`
devolve, por construcao (`for i in range(n - 1)`), so' as juntas ENTRE dois
blocos do MESMO layout de preenchimento. A junta de FRONTEIRA - a que
separa o preenchimento da PECA DE AMARRACAO DO NO' encostada nele - nao
existia em lista nenhuma. Consequencia medida em `piloto_sintetico_2x2`
(W004 e W011): a fiada oposta punha uma junta EXATAMENTE em cima dela
(t = 34,5 cm, nas 8 fiadas), `PRISM_CONTINUOUS_JOINT` reprovava 14 vezes e
`alignment_conflicts` reportava ZERO - o gate era cego.

Nenhum teste aqui usa parede, ID ou comprimento de projeto real: toda a
geometria e' sintetica, construida no proprio teste, exatamente como em
`tests/test_block_bonding.py`.

    python3 -m pytest tests/test_block_node_fill_joint.py -q
"""

import pytest

import load_script
import revit_stubs

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER
J = m.BLOCK_JOINT_CM
TOL = m.VERTICAL_JOINT_STAGGER_TOLERANCE_CM


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
    result = m.solve_building_blocks(nodes, walls, end_to_node, per_wall,
                                     catalog or CATALOG)
    return result, walls


# ---------------------------------------------------------------------
# MEDICAO da junta NO'|FILL na GEOMETRIA FINAL - nunca por dentro do
# solver. Uma junta e' "de no'" quando as duas pecas adjacentes (separadas
# por, no maximo, uma junta de argamassa) sao uma PECA DE NO' e uma peca de
# PREENCHIMENTO; e' "interna" quando as duas sao de preenchimento.
# ---------------------------------------------------------------------
def _wall_course_pieces(walls, candidates):
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


def _classified_joints(items, max_gap_cm=None):
    """({juntas NO'|FILL}, {juntas FILL|FILL}) de uma fiada de uma parede."""
    if max_gap_cm is None:
        max_gap_cm = m.BLOCK_JOINT_CM * 2.0
    node_joints, fill_joints = [], []
    for i in range(len(items) - 1):
        lo_a, hi_a, _code_a, node_a = items[i]
        lo_b, _hi_b, _code_b, node_b = items[i + 1]
        gap = lo_b - hi_a
        if not (-1e-6 <= gap <= max_gap_cm):
            continue          # separadas por um VAO: nao formam junta
        center = hi_a + gap / 2.0
        if node_a != node_b:
            node_joints.append(center)
        elif not node_a:
            fill_joints.append(center)
    return node_joints, fill_joints


def node_fill_prism_violations(walls, candidates, tolerance_cm=TOL):
    """Juntas NO'|FILL de uma fiada que uma junta INTERNA de preenchimento
    da fiada oposta empilha em cima - a violacao exata que esta CR corrige.
    Devolve [(wall_idx, posicao_cm, fiada_do_no'), ...]."""
    pieces = _wall_course_pieces(walls, candidates)
    found = []
    for wall_idx in sorted(set(w for (w, _c) in pieces)):
        items_a = pieces.get((wall_idx, "A")) or []
        items_b = pieces.get((wall_idx, "B")) or []
        if not items_a or not items_b:
            continue
        node_a, fill_a = _classified_joints(items_a)
        node_b, fill_b = _classified_joints(items_b)
        for course_label, nodes_cm, others_cm in (("A", node_a, fill_b),
                                                  ("B", node_b, fill_a)):
            for x_node in nodes_cm:
                if any(abs(x_node - x) <= tolerance_cm for x in others_cm):
                    found.append((wall_idx, round(x_node, 2), course_label))
    return sorted(set(found))


# =====================================================================
# INV-NODEFILL-001..004 - a FUNCAO PURA
# =====================================================================
def test_inv_nodefill_001_fronteira_de_no_produz_a_junta():
    """A peca de no' termina em `border`; o trecho comeca em
    `border + BLOCK_JOINT_CM`. A junta esta' no meio."""
    assert m._segment_node_boundary_joints_cm(
        35.0, 119.0, leading_is_node=True, trailing_is_node=False) == [35.0 - J / 2.0]
    assert m._segment_node_boundary_joints_cm(
        35.0, 119.0, leading_is_node=False, trailing_is_node=True) == [119.0 + J / 2.0]
    assert m._segment_node_boundary_joints_cm(
        35.0, 119.0, leading_is_node=True, trailing_is_node=True) == [34.5, 119.5]


def test_inv_nodefill_002_abertura_e_ponta_livre_nao_produzem_junta_de_no():
    """ITEM 6 DO CR, o cuidado critico: borda de vao, jamb, recorte e ponta
    livre NAO viram junta de no'. A excecao da secao 11.8 (C04/C09/B19
    encostado no vao PODE ficar alinhado entre fiadas) continua intacta."""
    assert m._segment_node_boundary_joints_cm(35.0, 119.0) == []
    assert m._segment_node_boundary_joints_cm(
        35.0, 119.0, leading_is_node=False, trailing_is_node=False) == []


def test_inv_nodefill_003_a_junta_e_a_borda_da_peca_de_no():
    """A junta devolvida tem de cair EXATAMENTE a meia junta da ponta do
    trecho - senao ela nao descreve a fronteira fisica."""
    for seg_start_cm in (0.0, 15.0, 34.999, 220.5):
        (joint,) = m._segment_node_boundary_joints_cm(
            seg_start_cm, seg_start_cm + 99.0, leading_is_node=True)
        assert abs((seg_start_cm - joint) - J / 2.0) < 1e-9


def test_inv_nodefill_004_junta_sem_peca_encostada_nao_conta():
    """Depois do recorte da abertura a peca que encostava no no' pode nao
    existir mais - e uma junta sem peca dos dois lados nao e' junta."""
    # peca posicionada exatamente encostada na junta 34,5 (comeca em 35,0)
    assert m._node_boundary_joints_backed_by_pieces_cm(
        [34.5], [(35.0, 74.0), (75.0, 114.0)]) == [34.5]
    # o recorte derrubou a primeira peca: a proxima so' comeca em 75,0
    assert m._node_boundary_joints_backed_by_pieces_cm(
        [34.5], [(75.0, 114.0)]) == []
    assert m._node_boundary_joints_backed_by_pieces_cm([34.5], []) == []
    assert m._node_boundary_joints_backed_by_pieces_cm([], [(35.0, 74.0)]) == []


# =====================================================================
# INV-NODEFILL-010..016 - a JUNTA CHEGA na fiada oposta
#
# O defeito so' aparece quando a parede tem PECA DE NO' nas DUAS pontas:
# com uma ponta livre o preenchimento tem o meio-bloco (B19) para deslocar
# e a coincidencia nao se forma. Por isso o caso que DISCRIMINA e' a
# celula fechada (4 L_CORNER) e a grade 2x2 - exatamente a topologia do
# `piloto_sintetico_2x2`, onde a auditoria mediu `NODE_TYPE` proximo =
# `L_CORNER` e `DISTANCE_TO_NODE` = 27,5 cm. Medido: no codigo anterior a
# celula de 350 cm da' 4 violacoes e a grade 2x2 da' 2, todas em
# t = 34,5 cm - a MESMA posicao das 14 violacoes reais do piloto.
# =====================================================================
def celula_fechada(lado_cm=350.0):
    """4 paredes formando uma celula fechada: cada parede tem L_CORNER nas
    DUAS pontas."""
    return [seg(0, 0, lado_cm, 0), seg(0, 0, 0, lado_cm),
            seg(lado_cm, 0, lado_cm, lado_cm), seg(0, lado_cm, lado_cm, lado_cm)]


def grade_2x2(lado_cm=350.0):
    """Grade 2x2 - mesma topologia do `piloto_sintetico_2x2` (12 paredes,
    L_CORNER nos cantos, T no meio de cada lado)."""
    a, b = lado_cm, lado_cm * 2.0
    return [seg(0, 0, a, 0), seg(0, 0, 0, a), seg(a, 0, b, 0), seg(a, 0, a, a),
            seg(b, 0, b, a), seg(0, a, a, a), seg(0, a, 0, b),
            seg(a, a, b, a), seg(a, a, a, b), seg(b, a, b, b),
            seg(0, b, a, b), seg(a, b, b, b)]


L_LIVRE = [seg(0, 0, 364, 0), seg(0, 0, 0, 364)]
T_MEIO = [seg(0, 0, 700, 0), seg(200, 0, 200, 300), seg(500, 0, 500, 300)]
X_MEIO = [seg(0, 0, 700, 0), seg(200, -300, 200, 300), seg(500, -300, 500, 300)]


@pytest.mark.parametrize("lado_cm", [150.0, 230.0, 350.0, 430.0, 590.0])
def test_inv_nodefill_010_celula_fechada_nao_empilha_junta_de_no(lado_cm):
    """O CASO QUE DISCRIMINA (falha no codigo anterior, em todos estes
    comprimentos): parede com L_CORNER nas duas pontas, horizontal e
    vertical na mesma planta."""
    result, walls = solve_plan(celula_fechada(lado_cm))
    assert not result.get("error")
    assert result["candidates"]
    assert node_fill_prism_violations(walls, result["candidates"]) == []


def test_inv_nodefill_011_grade_2x2_nao_empilha_junta_de_no():
    """Topologia do `piloto_sintetico_2x2`. No codigo anterior: 2 violacoes,
    ambas em t = 34,5 cm - a assinatura exata do bug."""
    result, walls = solve_plan(grade_2x2())
    assert not result.get("error")
    assert node_fill_prism_violations(walls, result["candidates"]) == []


@pytest.mark.parametrize("nome,linhas", [
    ("L_CORNER_ponta_livre", L_LIVRE),
    ("T_INTERSECTION", T_MEIO),
    ("X_INTERSECTION", X_MEIO),
])
def test_inv_nodefill_012_l_t_x_continuam_limpos(nome, linhas):
    """COBERTURA de L, T e X isolados: eles ja' estavam corretos (a ponta
    livre da' folga ao preenchimento) e nao podem passar a errar - o fix
    nao pode redesenhar no' nenhum (item 10 do CR)."""
    result, walls = solve_plan(linhas)
    assert not result.get("error"), nome
    assert result["candidates"], nome
    assert node_fill_prism_violations(walls, result["candidates"]) == [], nome


def test_inv_nodefill_013_com_abertura_o_invariante_continua():
    """O caminho `continuous_first` (recorte + reparo local) - o unico
    default de producao, e o que o piloto exercita: W011 e' HORIZONTAL com
    janela, W004 e' VERTICAL. A excecao da secao 11.8 continua valendo:
    o fix nao transforma borda de vao em junta de no'."""
    janela = (ft(100.0), ft(220.0), ft(90.0), ft(200.0))
    porta = (ft(120.0), ft(200.0), ft(0.0), ft(210.0))
    linhas = grade_2x2()
    aberturas = dict((i, []) for i in range(len(linhas)))
    aberturas[0] = [porta]      # horizontal com porta
    aberturas[3] = [porta]      # vertical com porta
    aberturas[10] = [janela]    # horizontal com janela
    aberturas[6] = [janela]     # vertical com janela
    result, walls = solve_plan(linhas, openings=aberturas)
    assert not result.get("error")
    assert node_fill_prism_violations(walls, result["candidates"]) == []


def test_inv_nodefill_014_vale_nas_DUAS_fiadas_e_nos_dois_sentidos():
    """Nao basta a fiada A enxergar a junta da B: as 14 violacoes do piloto
    eram `junta de no' da fiada PAR x junta interna da fiada IMPAR`, e a
    celula fechada produz TAMBEM o sentido contrario (medido: 2 das 4
    violacoes do codigo anterior sao da fiada B)."""
    result, walls = solve_plan(celula_fechada())
    cursos = set(c.get("course") for c in result["candidates"])
    assert cursos == {"A", "B"}, cursos
    violacoes = node_fill_prism_violations(walls, result["candidates"])
    assert violacoes == []
    assert [v for v in violacoes if v[2] == "A"] == []
    assert [v for v in violacoes if v[2] == "B"] == []


def test_inv_nodefill_015_invariante_e_estavel_a_ordem_de_entrada():
    """A lista nova sai de `seg_start_cm` e das bordas das pecas de no' -
    tudo ja' na grade de snap. Nada de `wall_idx`, ordem de lista ou
    `GetEndPoint(0)`."""
    linhas = grade_2x2()
    for ordem in ([11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
                  [3, 7, 0, 11, 5, 2, 9, 1, 6, 10, 4, 8],
                  [6, 0, 9, 2, 11, 4, 7, 1, 10, 3, 8, 5]):
        result, walls = solve_plan([linhas[i] for i in ordem])
        assert node_fill_prism_violations(walls, result["candidates"]) == [], ordem


def test_inv_nodefill_016_invariante_e_estavel_a_inversao_de_pontas():
    """Mesma planta desenhada com as pontas invertidas: mesmo predio, mesma
    resposta."""
    lado = 350.0
    invertidas = [seg(lado, 0, 0, 0), seg(0, lado, 0, 0),
                  seg(lado, lado, lado, 0), seg(lado, lado, 0, lado)]
    result, walls = solve_plan(invertidas)
    assert node_fill_prism_violations(walls, result["candidates"]) == []


def test_inv_nodefill_017_a_junta_de_no_da_fiada_oposta_e_deduzivel_sem_layout():
    """`_wall_node_boundary_joints_cm` e' o que permite a Fiada A (que roda
    primeiro) evitar a junta de no' da Fiada B: a posicao da peca de no'
    depende so' de `course`, nunca de layout nem de `variant_index`."""
    by_end = {(0, 0, "A"): 34.0, (0, 1, "A"): 330.0, (0, 0, "B"): 54.0}
    juntas = m._wall_node_boundary_joints_cm(0, "A", by_end, {})
    assert sorted(juntas) == [34.0 + J / 2.0, 330.0 - J / 2.0]
    assert m._wall_node_boundary_joints_cm(0, "B", by_end, {}) == [54.0 + J / 2.0]
    # parede sem no' nenhum nessa fiada: lista vazia
    assert m._wall_node_boundary_joints_cm(9, "A", by_end, {}) == []
    # encontro de MEIO de parede: junta dos dois lados da faixa reservada
    midspan = {(0, "A"): [(100.0, 150.0)]}
    assert sorted(m._wall_node_boundary_joints_cm(0, "A", {}, midspan)) == [
        100.0 - J / 2.0, 150.0 + J / 2.0]


# =====================================================================
# INV-NODEFILL-020/021 - o GATE deixou de ser cego
# =====================================================================
def test_inv_nodefill_020_o_motor_publica_o_conflito_de_junta_de_no():
    """O motor passa a ter um lugar onde a coincidencia contra uma junta de
    no' aparece (`node_boundary_conflicts`, por parede). Antes desta CR a
    informacao nao existia em canto nenhum: `alignment_conflicts` dava 0
    com 14 violacoes reais."""
    result, _walls = solve_plan(grade_2x2())
    per_wall = result.get("per_wall") or []
    assert per_wall
    for entry in per_wall:
        assert "node_boundary_conflicts" in entry, entry.get("wall_idx")


def test_inv_nodefill_021_a_junta_de_no_entra_na_busca_da_fiada_oposta():
    """Prova DIRETA de que a junta de fronteira alimenta o desencontro: um
    trecho cuja unica composicao "natural" cai em cima da junta de no' da
    fiada oposta escolhe outra composicao quando essa junta esta' na lista
    a evitar."""
    pier_cm, seg_start_cm = 119.0, 35.0
    baseline = m._pier_ordered_layout(pier_cm, CATALOG, 0.0, 0.0,
                                      leading_open_override=False,
                                      trailing_open_override=False)
    juntas = m._layout_internal_joint_positions_cm(baseline, seg_start_cm)
    assert juntas, "cenario perdeu o sentido"
    # a fiada oposta tem uma PECA DE NO' terminando logo antes da 1a junta
    junta_de_no = juntas[0]
    seg_da_fiada_oposta = junta_de_no + J / 2.0
    assert m._segment_node_boundary_joints_cm(
        seg_da_fiada_oposta, seg_da_fiada_oposta + pier_cm,
        leading_is_node=True) == [junta_de_no]
    escolhido = m._pier_layout_avoiding_joints(
        pier_cm, CATALOG, 0.0, 0.0, seg_start_cm, [junta_de_no],
        leading_is_open=False, trailing_is_open=False)
    assert escolhido is not None
    assert m._count_joint_coincidences_cm(
        m._layout_internal_joint_positions_cm(escolhido, seg_start_cm),
        [junta_de_no]) == 0
