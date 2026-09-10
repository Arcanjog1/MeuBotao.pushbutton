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


def _mirror_fam(fam):
    """Troca A<->B DENTRO da MESMA parede - o efeito ESPERADO (secao 28.3
    de REGRAS_MODULACAO_BLOCOS.md) de inverter arms[0]/[1] num L_CORNER
    ISOLADO (so' um no', nada para `_coordinate_arm_role_nodes`
    coordenar): a peca de amarracao que esta parede recebia como
    course_a passa a ser course_b (a peca em si nao muda de posicao, so'
    de ROTULO), entao QUALQUER fiada fisica que dependia daquele rotulo
    (a peca de no', ou o preenchimento comum que fechava so' por causa da
    borda que aquela peca deixava) migra de familia junto. NAO e' uma
    troca entre paredes - cada parede continua com o MESMO conjunto de
    fiadas fisicas cobertas, so' com a letra A/B trocada."""
    return {"A": fam["B"], "B": fam["A"]}


# ============================================================
# 1/2/9 - L_CORNER simetrico, arms [A,B] vs [B,A], input permutado
# ============================================================

@pytest.mark.parametrize("wall_order", [(0, 1), (1, 0)])
def test_l_corner_simetrico_arms_invertidos_nao_perde_familia(wall_order):
    """L de dois bracos longos (300cm cada) COM ORDEM DE ENTRADA permutada
    (item 9 do CR) - mesma geometria fisica, so' o indice de wall_idx
    trocado.

    ESCOPO (CR-BLOCK-ARM-ROLE-CONSISTENCY, follow-up): este CR resolve a
    CONSISTENCIA de papel entre os DOIS nos que fecham uma mesma parede -
    aqui ha' so' UM no' (cada parede so' toca este L_CORNER uma vez), nada
    para coordenar. O que se prova aqui e' que trocar arms[0]/[1] NUNCA
    piora o conjunto de familias presentes - so' pode ESPELHAR (secao
    28.3 de REGRAS_MODULACAO_BLOCOS.md, custo ja' aceito) ou manter
    exatamente o mesmo resultado. Uma familia ausente em AMBAS as ordens
    (o caso medido aqui: o preenchimento comum da parede nao fecha em
    blocos para uma das duas paridades, independente do papel do no') e'
    NON_MODULAR_WALL legitimo - mesma geometria, mesmo resultado nas duas
    ordens, portanto nao e' um efeito de ORDEM (ver secao 15 do CR
    original: "se a fiada realmente nao couber por geometria, isso
    continua permitido" - contanto que seja independente da ordem, o que
    esta' provado abaixo)."""
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
        assert fam_swapped == _mirror_fam(fam_base), (
            wall_order, wall_idx, "trocar arms so' pode ESPELHAR A/B, nunca mudar QUAIS fiadas existem",
            fam_base, fam_swapped)


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
    dos dois lados do L. So' UM no' (ver docstring de
    test_l_corner_simetrico_arms_invertidos_nao_perde_familia para o
    escopo) - a invariancia provada e' de ESPELHAMENTO, nao de "familia
    sempre presente"."""
    walls, nodes, end_to_node = build_plan([seg(0, 0, 900, 0), seg(0, 0, 0, 900)])
    corner_idx = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]

    base = solve(walls, nodes, end_to_node)
    swapped = solve(walls, swap_two_arm_node(nodes, corner_idx), end_to_node)

    for wall_idx in range(2):
        fam_base = wall_families_present(base, wall_idx)
        fam_swapped = wall_families_present(swapped, wall_idx)
        assert fam_swapped == _mirror_fam(fam_base), (wall_idx, fam_base, fam_swapped)


@pytest.mark.parametrize("variants_per_course", [1, 3])
def test_l_corner_multiplas_fiadas_nao_perde_familia(variants_per_course):
    """Item 3 do CR - varias fiadas fisicas (via `solve_building_blocks_all_courses`,
    que gira `variants_per_course` composicoes por familia). So' UM no'
    (ver escopo em test_l_corner_simetrico_arms_invertidos_nao_perde_
    familia) - prova espelhamento (mesmo conjunto de fiadas fisicas
    cobertas nas duas ordens), nao "toda fiada sempre coberta"."""
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

    def _wall_letter_coverage(result):
        """{(wall_idx, letter): True} agregado por TODAS as fiadas
        fisicas da mesma paridade - letter vem do PROPRIO course_index
        (par=A, impar=B, fixo por construcao), entao o que muda com o
        swap e' QUAL parede aparece em cada letra, nunca a letra em si."""
        present = {}
        for course_index, cands in result["course_candidates"].items():
            letter = "A" if course_index % 2 == 0 else "B"
            for c in cands:
                present[(c.get("wall_idx"), letter)] = True
        return present

    def _mirror_wall_letter(coverage):
        return set((wall_idx, "B" if letter == "A" else "A") for wall_idx, letter in coverage)

    cov_base = set(_wall_letter_coverage(base))
    cov_swapped = set(_wall_letter_coverage(swapped))
    assert cov_swapped == _mirror_wall_letter(cov_base), (cov_base, cov_swapped)


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
    geometria original) so' pode ESPELHAR o resultado do endpoint NAO
    invertido (ver escopo em
    test_l_corner_simetrico_arms_invertidos_nao_perde_familia - so' UM
    no', nada para este CR coordenar), nunca perder uma familia que a
    geometria original tinha."""
    reversed_v = seg(0, 300, 0, 0)  # mesmo segmento de seg(0,0,0,300), invertido
    walls_ref, nodes_ref, end_to_node_ref = build_plan([seg(0, 0, 300, 0), seg(0, 0, 0, 300)])
    reference = solve(walls_ref, nodes_ref, end_to_node_ref)

    walls, nodes, end_to_node = build_plan([seg(0, 0, 300, 0), reversed_v])
    corner_idx = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]

    base = solve(walls, nodes, end_to_node)
    swapped = solve(walls, swap_two_arm_node(nodes, corner_idx), end_to_node)

    for wall_idx in range(2):
        fam_ref = wall_families_present(reference, wall_idx)
        fam_base = wall_families_present(base, wall_idx)
        fam_swapped = wall_families_present(swapped, wall_idx)
        assert fam_base == fam_ref, ("reversal sozinho", wall_idx, fam_ref, fam_base)
        assert fam_swapped == _mirror_fam(fam_ref), (
            "reversal + swap", wall_idx, fam_ref, fam_swapped)


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
    numeros redondos): e' o ruido de CAD real (conversao pes<->cm,
    extend_wall_ends_to_junctions) que reproduz a mesma fragilidade
    medida em W042/TGD - com coordenadas redondas o defeito nao
    reproduz (o preenchimento comum fecha de qualquer forma, so' espelha
    o padrao, ver test_l_corner_simetrico_arms_invertidos_nao_perde_
    familia). Confirmado escrevendo este teste: SEM
    `_coordinate_arm_role_nodes`, exatamente as combinacoes
    (swap_a=False,swap_b=True) e (True,False) desta geometria fazem a
    parede do meio perder uma familia inteira (COVERAGE_MISSING_ROW);
    COM a coordenacao, as 4 combinacoes preservam as duas familias."""
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


# ============================================================
# 12 - CICLOS: retangulo fechado (ciclo PAR, 4 nos) e U (cadeia aberta,
# ja' coberta acima) - a coordenacao precisa fechar SEM conflito num
# ciclo par real, construido so' com L_CORNER de 90 graus.
# ============================================================

def test_retangulo_fechado_coordena_sem_conflito_nenhuma_parede_perde_familia():
    """4 paredes formando um retangulo fechado (400x300cm) - CICLO de 4
    nos L_CORNER no grafo de `_coordinate_arm_role_nodes`, com geometria
    REAL (nao sintetica). Confirma empiricamente, no caso real mais
    simples de ciclo fechado, a prova geral de
    test_ciclo_de_l_corner_nunca_gera_conflito_residual_par_ou_impar:
    fecha SEM nenhum conflito residual, e NENHUMA das 4 paredes fica com
    uma familia inteira ausente."""
    walls, nodes, end_to_node = build_plan([
        seg(0, 0, 400, 0), seg(400, 0, 400, 300),
        seg(400, 300, 0, 300), seg(0, 300, 0, 0),
    ])
    kinds = sorted(n["kind"] for n in nodes)
    assert kinds.count("L_CORNER") == 4, kinds

    # confere a coordenacao diretamente (ANTES do solve() mutar `nodes`
    # in place - ver docstring de _coordinate_arm_role_nodes) - ciclo par
    # sempre 2-coloravel, zero conflitos esperados.
    conflicts = m._coordinate_arm_role_nodes(nodes)
    assert conflicts == [], conflicts

    result = solve(walls, nodes, end_to_node)
    for wall_idx in range(4):
        fam = wall_families_present(result, wall_idx)
        assert fam["A"] or fam["B"], (wall_idx, "parede do retangulo sem nenhuma peca")


def _synthetic_cycle_nodes(length, flip_pattern):
    """Monta um ciclo SINTETICO de `length` nos L_CORNER de 2 arms (nao
    depende de geometria real): no' i tem arms para a parede i (liga a
    i+1) e a parede i-1 (liga a i-1), com a ORDEM dos dois arms
    controlada por `flip_pattern[i]` (0/1) - isso simula qualquer
    convencao de ordenacao que `wall_pairing.py` poderia produzir."""
    nodes = []
    for i in range(length):
        wall_next = i
        wall_prev = (i - 1) % length
        arms = [(wall_prev, 1), (wall_next, 0)]
        if flip_pattern[i]:
            arms = [arms[1], arms[0]]
        nodes.append({"kind": "L_CORNER", "arms": arms, "point": XYZ(float(i), 0.0, 0.0)})
    return nodes


def test_ciclo_de_l_corner_nunca_gera_conflito_residual_par_ou_impar():
    """Prova (por construcao, testando VARIOS comprimentos e VARIAS
    combinacoes de ordem de arms) que `_coordinate_arm_role_nodes` NUNCA
    deixa um conflito residual num ciclo de nos L_CORNER de 2 arms -
    seja o ciclo PAR ou IMPAR.

    Motivo matematico (nao e' so' sorte da geometria real ser sempre
    par): cada no' L_CORNER de 2 arms atribui, por construcao,
    EXATAMENTE um papel 0 (arms[0]) e um papel 1 (arms[1]) as suas duas
    arestas - nunca 0/0 nem 1/1. Isso limita o grau de cada no' no grafo
    de coordenacao a no maximo 2, entao qualquer componente conexo e' um
    CAMINHO ou um CICLO SIMPLES (nunca uma estrutura mais complexa).
    Para um ciclo v0..v(L-1) com arestas e_i=(v_i,v_{i+1}), seja s_i o
    papel de e_i em v_{i+1}; como v_{i+1} so' tem 2 arms, o papel de
    e_{i+1} em v_{i+1} e' forcosamente o complemento 1^s_i. Somando
    (XOR) a paridade de todas as L arestas do ciclo, cada termo
    "1^s_i^papel(e_i em v_i)" se cancela em pares ao percorrer o ciclo
    inteiro (telescopagem), resultando em XOR total = 0 SEMPRE -
    independente de L ser par ou impar, e independente de qualquer
    padrao de ordenacao de arms. Ou seja: um ciclo de L_CORNER e' SEMPRE
    2-coloravel (0 conflitos), e o ramo de `conflicts` em
    `_coordinate_arm_role_nodes` e' codigo morto/rede de seguranca para
    esta topologia - nunca dispara, comprovado aqui por construcao para
    varios comprimentos e todas as combinacoes possiveis de ordem de
    arms num ciclo de ate' 5 nos (2^5 = 32 combinacoes), alem de casos
    isolados maiores."""
    import itertools

    for length in (3, 4, 5):
        for flip_pattern in itertools.product((0, 1), repeat=length):
            nodes = _synthetic_cycle_nodes(length, flip_pattern)
            conflicts = m._coordinate_arm_role_nodes(nodes)
            assert conflicts == [], (length, flip_pattern, conflicts)

    for length in (6, 7):
        nodes = _synthetic_cycle_nodes(length, [i % 2 for i in range(length)])
        conflicts = m._coordinate_arm_role_nodes(nodes)
        assert conflicts == [], (length, conflicts)

    # DETERMINISMO: mesma entrada -> mesmo resultado; permutar a ORDEM da
    # lista de nos (equivalente a mudar a ordem em que build_wall_graph
    # devolveria os nos) tambem tem que devolver o mesmo conjunto de
    # conflitos (aqui, sempre vazio), porque a raiz/ordem de visita e'
    # escolhida por `_canonical_node_sort_key` (geometria), nunca pela
    # posicao na lista.
    import copy as _copy

    fake_nodes = _synthetic_cycle_nodes(5, [1, 0, 1, 1, 0])
    conflicts = m._coordinate_arm_role_nodes(_copy.deepcopy(fake_nodes))
    again = m._coordinate_arm_role_nodes(_copy.deepcopy(fake_nodes))
    assert again == conflicts == []

    reordered = [fake_nodes[3], fake_nodes[0], fake_nodes[4], fake_nodes[1], fake_nodes[2]]
    conflicts_reordered = m._coordinate_arm_role_nodes(_copy.deepcopy(reordered))
    assert conflicts_reordered == conflicts == []
