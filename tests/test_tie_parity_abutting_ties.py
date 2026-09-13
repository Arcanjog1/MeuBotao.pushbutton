# -*- coding: utf-8 -*-
"""DEFEITO 1 - junta corrida na fronteira PREENCHIMENTO | AMARRACAO DO NO'
(fill|tie), classe "duas pecas de amarracao encostadas em fiadas opostas".

Medido no corpus (TGD V2 245 PRISM / TP1 48, 2026-09-12): TODA junta corrida
fill|tie residual e' uma junta NO'|FILL da fiada A exatamente em cima de uma
junta NO'|FILL da fiada B - as duas pecas de no' (de nos DIFERENTES) se
encostam junta a junta na mesma parede, cada uma numa fiada: a B34 do T que
chega (fiada B, [0,34]) e o B54 do X a 55cm (fiada A, [35,89]); ou a B34 do
T e a B34 do canto L na parede de 69cm. O preenchimento NAO tem liberdade
nenhuma ali: nas duas fiadas a junta e' o contorno da propria peca de no'.
A unica variavel fisica e' a PARIDADE (qual fiada hospeda a peca de cada
no') - a inversao A/B que a secao 11 permite e a regra 11.12 implementou
atras de flag (`_tie_parity_flip`).

O que entra: `solve_all_intersections` deduz, SO' da geometria das pecas de
no' (antes de qualquer preenchimento), as juntas NO'|FILL de cada fiada;
onde uma junta da A coincide com uma da B e as duas pecas sao de nos
diferentes, as pecas precisam ficar na MESMA fiada. Isso vira uma restricao
de paridade (XOR) entre os dois nos; T/X podem inverter (`_tie_parity_flip`),
canto L e' fixo (papel coordenado por `_coordinate_arm_role_nodes`). A
propagacao e' deterministica (ordem geometrica), monotona (no' invertido
nunca volta) e so' e' aceita se a contagem de coincidencias NAO'|FILL x
NO'|FILL cair estritamente (nunca piora). Sem busca global, sem re-solucao
completa por tentativa (custo: 2x solve_all_intersections + censo).

Nenhum validador foi alterado: a medicao abaixo e' feita na GEOMETRIA FINAL
das pecas (mesmo estilo de tests/test_block_node_fill_revalidation.py).

    python3 -m pytest tests/test_tie_parity_abutting_ties.py -q
"""
import contextlib
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_block_node_fill_revalidation as NF  # noqa: E402

m = NF.m
ws = NF.ws
seg = NF.seg
ft = NF.ft
TOL = NF.TOL
FLAG = "ABUTTING_TIE_PARITY_ENABLED"


@contextlib.contextmanager
def abutting_parity(enabled):
    before = getattr(ws, FLAG, None)
    setattr(ws, FLAG, enabled)
    try:
        yield
    finally:
        if before is None:
            delattr(ws, FLAG)
        else:
            setattr(ws, FLAG, before)


# ----------------------------------------------------------------- medidor
def tie_tie_prism_violations(walls, candidates, tolerance_cm=TOL):
    """Juntas NO'|FILL da fiada A em cima de juntas NO'|FILL da fiada B na
    MESMA parede - o defeito exato desta missao. [(wall_idx, t_cm), ...]."""
    pieces = NF.wall_course_pieces(walls, candidates)
    found = []
    for wall_idx in sorted(set(w for (w, _c) in pieces)):
        node_a, _fill_a = NF.classified_joints(pieces.get((wall_idx, "A")) or [])
        node_b, _fill_b = NF.classified_joints(pieces.get((wall_idx, "B")) or [])
        for x in node_a:
            if any(abs(x - y) <= tolerance_cm for y in node_b):
                found.append((wall_idx, round(x, 2)))
    return sorted(set(found))


def signature(walls, candidates):
    return NF.layout_signature(walls, candidates)


# ---------------------------------------------------------------- fixtures
def t_l_69():
    """Parede de 69cm entre um T em que ela chega (t=7) e um canto L (t=62)
    - geometria de W006/W013/W137/W139 do TGD V2: B34 do T na fiada B
    [0,34], B34 do L na fiada A [35,69]; junta 34,5 nas duas fiadas."""
    return [seg(-300, 0, 300, 0), seg(0, 0, 0, 55), seg(0, 55, 300, 55)]


def t_x_fill_left():
    """T em que a parede chega (t=7) + X a 55cm (t=62): B34 do T na B [0,34],
    B54 do X na A [35,89] - preenchimento a' ESQUERDA do B54 (A) e a' DIREITA
    da B34 (B) - geometria de W005/W012 do TGD V2. Trecho longo."""
    return [seg(-300, 0, 300, 0), seg(0, 0, 0, 600), seg(-300, 55, 300, 55),
            seg(0, 600, 300, 600)]


def x_t_fill_right():
    """Espelho: X a 55cm de um T na PONTA FINAL da parede - B54 do X [505,559]
    na A e B34 do T [560,594] na B; preenchimento a' DIREITA do B54 e a'
    ESQUERDA da B34 - geometria de W075/W086 (TGD V2) e W003/W008 (TP1)."""
    return [seg(-300, 600, 300, 600), seg(0, 0, 0, 600), seg(-300, 545, 300, 545),
            seg(0, 0, 300, 0)]


def t_chain_on_main():
    """Tres T's a 55cm um do outro na MESMA parede principal (B54 encostados
    [725,779][780,834][835,889] - padrao da W005/idx 5 do TGD), cada boneca
    de 69cm terminando num canto L. Um flip isolado do T do meio troca a
    coincidencia de lugar (cria uma nova na principal); so' a propagacao
    ao longo da cadeia fecha."""
    return [seg(0, 0, 1000, 0),
            seg(400, 0, 400, 55), seg(400, 55, 100, 55),
            seg(455, 0, 455, -55), seg(455, -55, 755, -55),
            seg(510, 0, 510, 55), seg(510, 55, 810, 55)]


def l_x_l_124():
    """Parede de 124cm entre dois cantos L com um X no meio (W021/W022/W140/
    W141 do TGD V2): B34 do L [0,34] + B54 do X [35,89] + B34 do L [90,124].
    Aqui os dois cantos formam uma ARESTA ISOLADA do grafo de coordenacao
    (nenhuma outra parede L-L toca qualquer um deles): a licenca "mesma
    familia" das secoes 31/32 vale, um dos cantos inverte e os tres
    encostados ficam na mesma fiada."""
    return [seg(0, 0, 300, 0), seg(0, 0, 0, 110), seg(-300, 55, 300, 55),
            seg(0, 110, 300, 110)]


def l_x_l_124_coordenado():
    """A mesma parede de 124cm, mas com os dois cantos presos numa CADEIA de
    coordenacao (cada um e' ponta de outra parede L-L, grau 2): a
    alternancia da regra 30.5 e' obrigatoria, o X so' iguala um dos dois -
    RESIDUAL conhecido, fora do alcance da paridade."""
    return [seg(0, 0, 300, 0), seg(300, 0, 300, -200),
            seg(0, 0, 0, 110), seg(-300, 55, 300, 55),
            seg(0, 110, 300, 110), seg(300, 110, 300, 310)]


FIXTURES = {
    "t_l_69": t_l_69,
    "t_x_fill_left": t_x_fill_left,
    "x_t_fill_right": x_t_fill_right,
    "t_chain_on_main": t_chain_on_main,
    "l_x_l_124": l_x_l_124,
}


# ======================================================== RED -> GREEN
@pytest.mark.parametrize("nome", sorted(FIXTURES))
def test_defeito_reproduzido_sem_a_paridade(nome):
    """RED: sem a paridade das pecas encostadas, cada fixture produz a junta
    NO'|FILL x NO'|FILL - o defeito existe e o medidor o ve'."""
    with abutting_parity(False):
        result, walls = NF.solve_plan(FIXTURES[nome]())
    achados = tie_tie_prism_violations(walls, result["candidates"])
    assert achados, (nome, "a fixture deixou de reproduzir o defeito")


@pytest.mark.parametrize("nome", sorted(FIXTURES))
def test_paridade_elimina_a_junta_fill_tie(nome):
    """GREEN: com a paridade, nenhuma junta NO'|FILL empilhada entre fiadas;
    e a garantia no'|fill (metade simetrica, secao 33) continua zero."""
    with abutting_parity(True):
        result, walls = NF.solve_plan(FIXTURES[nome]())
    assert tie_tie_prism_violations(walls, result["candidates"]) == [], nome
    assert NF.node_fill_prism_violations(walls, result["candidates"]) == [], nome
    assert not result.get("intersection_failures"), nome


def test_fixtures_cobrem_lado_e_comprimento():
    """As fixtures cobrem fill a' esquerda e a' direita da peca de no',
    trecho curto (69cm) e longo (594cm) - pedido da missao."""
    with abutting_parity(False):
        r_left, w_left = NF.solve_plan(t_x_fill_left())
        r_right, w_right = NF.solve_plan(x_t_fill_right())
        r_short, w_short = NF.solve_plan(t_l_69())
    assert tie_tie_prism_violations(w_left, r_left["candidates"]) == [(1, 34.5)]
    direita = tie_tie_prism_violations(w_right, r_right["candidates"])
    assert len(direita) == 1 and direita[0][0] == 1 and direita[0][1] > 500.0, direita
    assert tie_tie_prism_violations(w_short, r_short["candidates"]) == [(1, 34.5)]
    assert abs(m._ft_to_cm(m._wall_axis_and_length(w_short, 1)[3]) - 69.0) < 1e-6
    assert abs(m._ft_to_cm(m._wall_axis_and_length(w_left, 1)[3]) - 614.0) < 1e-6


def test_l_x_l_isolado_resolve_por_mesma_familia_do_canto():
    """Aresta isolada: exatamente UM canto L inverte (troca de `arms` + pino,
    a mesma operacao do SAFE REPAIR) e a parede fica sem junta fill|tie;
    o pino sobrevive a uma segunda resolucao (monotonia)."""
    lines = l_x_l_124()
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    per_wall = dict((i, []) for i in range(len(walls)))
    with abutting_parity(True):
        inter = m.solve_all_intersections(nodes, walls, NF.CATALOG, openings_per_wall=per_wall,
                                          end_to_node=e2n)
    flipped_l = [n for n in inter["tie_parity_flips"] if nodes[n]["kind"] == "L_CORNER"]
    assert len(flipped_l) == 1 and all(nodes[n].get("_arm_role_pinned") for n in flipped_l)
    assert inter["tie_parity_conflicts"] == []
    with abutting_parity(True):
        again = m.solve_all_intersections(nodes, walls, NF.CATALOG, openings_per_wall=per_wall,
                                          end_to_node=e2n)
    assert again["tie_parity_flips"] == [] and again["tie_parity_conflicts"] == []


def test_residual_l_x_l_coordenado_e_reportado_nao_escondido():
    """Cantos presos em cadeia coordenada (30.5): a paridade T/X nao resolve
    e NAO mexe nos cantos. O residual continua MEDIDO pelo medidor e
    REPORTADO em `tie_parity_conflicts` (UNSATISFIABLE) - nunca escondido."""
    with abutting_parity(True):
        result, walls = NF.solve_plan(l_x_l_124_coordenado())
    achados = tie_tie_prism_violations(walls, result["candidates"])
    assert len(achados) == 1 and achados[0][0] == 2, achados
    conflicts = result.get("tie_parity_conflicts") or []
    assert conflicts, "residual nao reportado"
    assert any(c.get("wall_idx") == 2 and c.get("reason") == "UNSATISFIABLE" for c in conflicts), conflicts


def test_nunca_piora_e_nao_mexe_onde_nao_ha_coincidencia():
    """Planta sem coincidencia NO'|FILL x NO'|FILL: a paridade nao inverte
    nenhum no' e o resultado e' identico peca a peca ao anterior."""
    for lines in (NF.celula_fechada(), NF.grade_2x2(), NF.T_MEIO, NF.L_LIVRE):
        with abutting_parity(False):
            r_off, w = NF.solve_plan(lines)
        with abutting_parity(True):
            r_on, w2 = NF.solve_plan(lines)
        before = tie_tie_prism_violations(w, r_off["candidates"])
        after = tie_tie_prism_violations(w2, r_on["candidates"])
        assert len(after) <= len(before)
        if not before:
            assert signature(w, r_off["candidates"]) == signature(w2, r_on["candidates"])
            assert not (r_on.get("tie_parity_flips") or [])


# ================================================================ ordem
def _permutations_of(lines):
    n = len(lines)
    yield list(lines)
    yield list(reversed(lines))
    # permutacao deterministica (rotacao + troca dos dois primeiros)
    rotated = list(lines[1:]) + list(lines[:1])
    if n >= 3:
        rotated[0], rotated[1] = rotated[1], rotated[0]
    yield rotated
    # endpoints invertidos
    inv = []
    for line in lines:
        p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
        inv.append(NF.Line.CreateBound(p1, p0))
    yield inv


def _canonical(walls, candidates):
    """Assinatura por CHAVE FISICA (endpoints canonicos), nunca por indice."""
    pieces = NF.wall_course_pieces(walls, candidates)
    out = []
    for (wall_idx, course), items in pieces.items():
        p0, p1, _d, _l, _t = m._wall_axis_and_length(walls, wall_idx)
        a = (round(p0.X, 4), round(p0.Y, 4))
        b = (round(p1.X, 4), round(p1.Y, 4))
        flip = a > b
        length = m._ft_to_cm(_l)
        key = (min(a, b), max(a, b))
        pcs = tuple(sorted(
            (round(length - hi, 2) if flip else round(lo, 2),
             round(length - lo, 2) if flip else round(hi, 2), code)
            for lo, hi, code, _n in items))
        out.append((key, course, pcs))
    # A letra A/B e' convencao de entrada (arms[0] do primeiro canto): uma
    # permutacao pode trocar A<->B na planta INTEIRA sem mudar a fisica.
    # Compara-se, por parede, o PAR nao ordenado de layouts das duas fiadas.
    by_wall = {}
    for key, course, pcs in out:
        by_wall.setdefault(key, []).append(pcs)
    return sorted((key, tuple(sorted(layouts))) for key, layouts in by_wall.items())


@pytest.mark.parametrize("nome", sorted(FIXTURES))
def test_ordem_das_paredes_nao_muda_o_resultado(nome):
    """Ordem normal, reversa, permutacao e endpoints invertidos: em TODAS a
    junta fill|tie desaparece, nenhuma junta no'|fill aparece, nenhum no'
    falha e nao ha' colisao. A COMPOSICAO do preenchimento ja' varia com a
    ordem de entrada ANTES desta CR (medido com a paridade desligada: 4
    assinaturas distintas em 4 ordens para estas fixtures - o papel
    `arms[0]`->A dos cantos e' convencao de entrada), por isso o invariante
    aqui e' o FISICO, nao a assinatura peca a peca; a assinatura para o
    MESMO input e' coberta pelo teste de tres processos abaixo."""
    ties = None
    for lines in _permutations_of(FIXTURES[nome]()):
        with abutting_parity(True):
            result, walls = NF.solve_plan(lines)
        assert tie_tie_prism_violations(walls, result["candidates"]) == [], nome
        assert NF.node_fill_prism_violations(walls, result["candidates"]) == [], nome
        assert not result.get("intersection_failures"), nome
        assert not result.get("tie_parity_conflicts"), (nome, result.get("tie_parity_conflicts"))
        assert not result.get("collisions"), nome
        n_ties = sum(1 for c in result["candidates"] if c.get("node_index") is not None)
        if ties is None:
            ties = n_ties
        assert n_ties == ties, nome


def test_tres_processos_separados_dao_o_mesmo_fingerprint():
    code = (
        "import sys, json, hashlib; sys.path.insert(0, %r); "
        "import test_tie_parity_abutting_ties as T; "
        "out = {}\n"
        "for nome, fx in sorted(T.FIXTURES.items()):\n"
        "    with T.abutting_parity(True):\n"
        "        r, w = T.NF.solve_plan(fx())\n"
        "    out[nome] = hashlib.sha256(json.dumps(T._canonical(w, r['candidates']), sort_keys=True).encode()).hexdigest()\n"
        "print(json.dumps(out, sort_keys=True))"
    ) % os.path.dirname(os.path.abspath(__file__))
    outs = []
    for _ in range(3):
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assert proc.returncode == 0, proc.stderr[-2000:]
        outs.append(proc.stdout.strip().splitlines()[-1])
    assert outs[0] == outs[1] == outs[2], outs


# ============================================================ garantias
def test_abertura_perto_do_no_continua_sem_bloco_dentro():
    """Porta na parede que chega, perto do T: com a paridade ligada nenhum
    bloco entra no vao (INSIDE_DOOR = 0) e a junta fill|tie nao volta."""
    lines = t_x_fill_left()
    porta = (ft(200.0), ft(290.0), ft(0.0), ft(210.0))
    openings = {1: [porta]}
    with abutting_parity(True):
        result, walls, _nodes = NF.solve_all_courses(lines, openings=openings)
    assert NF.blocos_dentro_de_porta(result, walls, openings) == []
    for course_index, cands in (result["course_candidates"] or {}).items():
        pass
    # nas fiadas fisicas a coincidencia NO'|FILL x NO'|FILL nao existe
    by_letter = {"A": [], "B": []}
    for course_index, cands in (result["course_candidates"] or {}).items():
        by_letter["A" if course_index % 2 == 0 else "B"].extend(cands)
    fisicas = by_letter["A"] + by_letter["B"]
    assert tie_tie_prism_violations(walls, fisicas) == []


def test_colisoes_nao_aumentam():
    for nome, fx in sorted(FIXTURES.items()):
        with abutting_parity(False):
            r_off, _w = NF.solve_plan(fx())
        with abutting_parity(True):
            r_on, _w2 = NF.solve_plan(fx())
        assert len(r_on.get("collisions") or []) <= len(r_off.get("collisions") or []), nome
