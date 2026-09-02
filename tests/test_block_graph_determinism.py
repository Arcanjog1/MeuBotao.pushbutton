# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM - invariantes permanentes de DETERMINISMO do
WALL GRAPH e do pipeline de blocos.

Pergunta que esta suite congela: para entradas GEOMETRICAMENTE
EQUIVALENTES (mesma planta, ordem diferente das paredes, eixos desenhados
no sentido contrario), `build_wall_graph` constroi o MESMO grafo e o
pipeline produz a MESMA solucao?

Baseline do CR (main 24ada98): NAO. As 8 execucoes do censo produziam 8
fingerprints distintos, e a PRIMEIRA camada divergente era o proprio
grafo - 273 nos virando 274/275 e T_INTERSECTION 118 virando 119/120 so'
de embaralhar a lista de entrada.

Toda geometria daqui e' SINTETICA e construida no proprio teste (mesma
regra de tests/test_block_bonding.py), com uma excecao explicita: os dois
invariantes marcados `@pytest.mark.slow` rodam o pipeline inteiro sobre o
projeto ja' versionado em nuvem/benchmark/projects/ - sao os unicos que
podem responder "o fingerprint FINAL de blocos independe da ordem?".

Regra dos fingerprints desta suite: nenhum deles pode olhar `wall_idx`,
posicao na lista, `id()` ou ordem de `dict`. Identidade de parede e' a
GEOMETRIA (pontas ordenadas + espessura); identidade de ponta e' a parede
canonica + QUAL extremidade dela (dita pela posicao, nao por `end_index`,
que troca de valor quando o eixo e' desenhado ao contrario).

    python3 -m pytest tests/test_block_graph_determinism.py -q
"""

import copy
import itertools
import json
import os
import random
import sys

import pytest

import load_script
import revit_stubs

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER

TOL_CM = m.WALL_GRAPH_NODE_SNAP_TOLERANCE_M * 100.0  # 5,0 cm
SEEDS = (1, 2, 3, 10, 42)


# --------------------------------------------------------------- helpers
def ft(cm):
    return cm / 100.0 * F


def to_cm(value_ft):
    return value_ft / F * 100.0


def wall(x0, y0, x1, y1, thickness_cm=14.0):
    """Uma parede no formato que `build_wall_graph` consome."""
    return (Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0)),
            ft(thickness_cm), (False, False))


def flip(entry):
    """A MESMA parede desenhada no sentido contrario."""
    line, thickness_ft, locks = entry
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    return (Line.CreateBound(XYZ(p1.X, p1.Y, 0.0), XYZ(p0.X, p0.Y, 0.0)),
            thickness_ft, (locks[1], locks[0]))


# ------------------------------------------------- identidade canonica
# Arredondamento de IMPRESSAO, nao tolerancia: 4 casas de cm = 1 micrometro,
# cinco ordens de grandeza abaixo da MENOR tolerancia do motor (o snap de
# no', 5 cm). Nao cria nem desfaz encontro nenhum - so' impede que ruido de
# ultimo bit vire duas chaves diferentes para o mesmo ponto.
def _r(value_ft):
    return round(to_cm(value_ft), 4) + 0.0  # + 0.0 normaliza -0.0


def _pt(point):
    return (_r(point.X), _r(point.Y))


def wall_key(walls, wall_idx):
    """Identidade GEOMETRICA de uma parede: pontas ORDENADAS + espessura.
    Independe do indice na lista e do sentido do desenho."""
    if wall_idx is None or not (0 <= wall_idx < len(walls)):
        return None
    line, thickness_ft, _locks = walls[wall_idx]
    a = _pt(line.GetEndPoint(0))
    b = _pt(line.GetEndPoint(1))
    lo, hi = (a, b) if a <= b else (b, a)
    return (lo[0], lo[1], hi[0], hi[1], _r(thickness_ft))


def arm_key(walls, wall_idx, end_index):
    """Identidade GEOMETRICA de uma PONTA: a parede canonica + QUAL das
    duas extremidades dela, dita pela POSICAO (0 = a extremidade que fica
    no extremo `lo` da chave da parede), nunca por `end_index`."""
    if wall_idx is None or not (0 <= wall_idx < len(walls)):
        return None
    line, _thickness_ft, _locks = walls[wall_idx]
    a = _pt(line.GetEndPoint(0))
    b = _pt(line.GetEndPoint(1))
    mine = a if end_index == 0 else b
    lo = a if a <= b else b
    return (wall_key(walls, wall_idx), 0 if mine == lo else 1)


def node_identity(walls, node):
    """O LUGAR e QUEM participa - sem o tipo. E' com isto que se pergunta
    'o MESMO no' geometrico foi classificado igual?' (item 15 do CR), em
    vez de so' comparar contagens por categoria."""
    arms = tuple(sorted(
        str(arm_key(walls, w, e)) for w, e in (node.get("arms") or [])))
    crossing = tuple(sorted(
        str(wall_key(walls, w)) for w in (node.get("crossing_walls") or [])))
    return (_pt(node["point"]), arms, crossing)


def node_full(walls, node):
    """Identidade + tipo + PAPEIS NA ORDEM em que o solver os le'
    (`main`/`incoming`/`neighbor`, `arms[0]`, `crossing_walls[0]`) - esses
    campos NAO sao ordenados de proposito: a ordem deles e' semantica
    (crossing_walls[0] decide qual parede recebe o B54 da fiada A, ver
    solve_x_intersection), entao ela tambem tem que ser canonica."""
    return (
        node_identity(walls, node),
        node.get("kind"),
        tuple(str(arm_key(walls, w, e)) for w, e in (node.get("arms") or [])),
        str(wall_key(walls, node.get("main_wall_idx"))),
        str(wall_key(walls, node.get("incoming_wall_idx"))),
        str(wall_key(walls, node.get("neighbor_wall_idx"))),
        node.get("neighbor_end_index"),
        tuple(str(wall_key(walls, w)) for w in (node.get("crossing_walls") or [])),
    )


def graph_fingerprint(walls, nodes):
    """Conjunto canonico de nos - a comparacao central desta suite."""
    return sorted(str(node_full(walls, n)) for n in nodes)


def classification_map(walls, nodes):
    """{identidade geometrica do no' -> tipo}."""
    return dict((node_identity(walls, n), n.get("kind")) for n in nodes)


def end_to_node_map(walls, nodes, end_to_node):
    """`end_to_node` traduzido para identidades geometricas dos DOIS lados
    - nunca o indice do no' na lista, que muda com a ordem de descoberta."""
    return dict(
        (str(arm_key(walls, w, e)), str(node_identity(walls, nodes[i])))
        for (w, e), i in end_to_node.items())


def midspan_set(walls, nodes):
    """Cruzamentos de MEIO DE PAREDE (nenhuma das duas termina ali)."""
    return sorted(
        (str(_pt(n["point"])),
         str(sorted(str(wall_key(walls, w)) for w in (n.get("crossing_walls") or []))))
        for n in nodes if not (n.get("arms") or []))


def build(walls, junction_map=None):
    return m.build_wall_graph(walls, junction_map or {})


def permutations_of(walls):
    """As mesmas 8 variantes do CR, aplicadas a uma planta sintetica:
    (nome, paredes)."""
    out = [("baseline", list(walls)),
           ("reversed", list(reversed(walls))),
           ("endpoint_reversal", [flip(w) for w in walls])]
    for seed in SEEDS:
        order = list(range(len(walls)))
        random.Random(seed).shuffle(order)
        out.append(("shuffle_seed_%d" % seed, [walls[i] for i in order]))
    return out


# ------------------------------------------------------------- plantas
def plant_non_transitive():
    """A GEOMETRIA QUE QUEBRAVA O AGRUPAMENTO, reproduzida sinteticamente.

    Medida na planta real torre_easy_lo_r00_tgd: tres paredes horizontais
    morrem na MESMA parede vertical, com as ancoras (a intersecao dos
    eixos) a y = 0, +3,50 e -2,41 cm. Como a tolerancia de agrupamento e'
    5 cm:

        d(A,B) = 3,50  <= 5   -> "mesmo no'"
        d(A,C) = 2,41  <= 5   -> "mesmo no'"
        d(B,C) = 5,91  >  5   -> "nos diferentes"

    A relacao NAO e' transitiva. Um agrupamento guloso que comeca pela
    ponta A junta as tres; comecando por B ou C, separa - MESMA geometria,
    particoes diferentes so' pela ordem da lista.

    Na planta real as tres sao fragmentos SOBREPOSTOS do mesmo trecho
    fisico (tres paredes de 14 cm com os eixos a menos de 6 cm um do
    outro), todas morrendo na mesma vertical - por isso a resposta
    geometricamente correta e' UM no', nao dois: dois nos a 5,9 cm um do
    outro fazem o solver reservar amarracao DUAS vezes praticamente no
    mesmo lugar. As pontas de TRAS ficam em x diferentes so' para o trio
    nao-transitivo aparecer uma vez so' nesta planta."""
    return [
        wall(0.0, -300.0, 0.0, 300.0),      # a vertical em que as tres morrem
        wall(-400.0, 0.0, 0.0, 0.0),        # A  (ancora y =  0,00)
        wall(-500.0, 3.50, 0.0, 3.50),      # B  (ancora y = +3,50)
        wall(-600.0, -2.41, 0.0, -2.41),    # C  (ancora y = -2,41)
    ]


def plant_short_wall():
    """Parede MAIS CURTA que a tolerancia de agrupamento: as duas pontas
    dela caem no mesmo no'. `point = group[0]["anchor"]` escolhia UMA das
    duas pela ordem da lista, entao o no' mudava de LUGAR (4,45 cm) so' de
    inverter o sentido do desenho - medido em 11 grupos da planta real."""
    return [
        wall(0.0, 0.0, 4.45, 0.0),
        wall(-400.0, 200.0, -400.0, 500.0),   # parede distante, so' para
        wall(-700.0, 200.0, -300.0, 200.0),   # a planta ter outros nos
    ]


def plant_ltx():
    """Uma planta com um de cada encontro: L, T, X de quatro pontas,
    continuacao reta, ponta livre e um X de meio de parede."""
    return [
        # L: duas paredes que se encontram so' em (0,0)
        wall(0.0, 0.0, 200.0, 0.0),
        wall(0.0, 0.0, 0.0, 200.0),
        # T: uma parede chega no MEIO de outra
        wall(600.0, -200.0, 600.0, 200.0),
        wall(600.0, 0.0, 900.0, 0.0),
        # X de 4 pontas: quatro paredes terminando no mesmo ponto
        wall(1500.0, 0.0, 1700.0, 0.0),
        wall(1300.0, 0.0, 1500.0, 0.0),
        wall(1500.0, 0.0, 1500.0, 200.0),
        wall(1500.0, -200.0, 1500.0, 0.0),
        # continuacao reta: duas paredes colineares emendadas
        wall(2200.0, 500.0, 2500.0, 500.0),
        wall(2500.0, 500.0, 2800.0, 500.0),
        # ponta livre: uma parede isolada, longe de todo mundo
        wall(-2000.0, -2000.0, -1700.0, -2000.0),
        # X de MEIO DE PAREDE: duas paredes inteiras se cortando
        wall(3200.0, -300.0, 3200.0, 300.0),
        wall(3000.0, 0.0, 3400.0, 0.0),
    ]


ALL_PLANTS = (
    ("nao_transitiva", plant_non_transitive()),
    ("parede_curta", plant_short_wall()),
    ("ltx", plant_ltx()),
)


# ============================================================ INVARIANTES
@pytest.mark.parametrize("plant_name,walls", ALL_PLANTS)
def test_INV_GRAPH_DET_001_permutacao_nao_muda_o_grafo(plant_name, walls):
    """INV-GRAPH-DET-001 - permutar a lista de paredes nao muda o
    fingerprint canonico dos nos."""
    base_nodes, _e = build(walls)
    baseline = graph_fingerprint(walls, base_nodes)
    for seed in SEEDS:
        order = list(range(len(walls)))
        random.Random(seed).shuffle(order)
        permuted = [walls[i] for i in order]
        nodes, _ = build(permuted)
        assert graph_fingerprint(permuted, nodes) == baseline, (
            "%s: seed %d mudou o grafo (%d nos -> %d nos)"
            % (plant_name, seed, len(base_nodes), len(nodes)))


@pytest.mark.parametrize("plant_name,walls", ALL_PLANTS)
def test_INV_GRAPH_DET_002_inverter_todos_os_eixos_nao_muda_o_grafo(plant_name, walls):
    """INV-GRAPH-DET-002 - desenhar TODAS as paredes no sentido contrario
    e' a mesma planta, entao tem que dar o mesmo grafo."""
    baseline = graph_fingerprint(walls, build(walls)[0])
    flipped = [flip(w) for w in walls]
    assert graph_fingerprint(flipped, build(flipped)[0]) == baseline, plant_name


@pytest.mark.parametrize("plant_name,walls", ALL_PLANTS)
def test_INV_GRAPH_DET_003_inverter_um_eixo_nao_muda_a_classificacao(plant_name, walls):
    """INV-GRAPH-DET-003 - inverter UMA parede de cada vez (o caso que a
    inversao global pode mascarar, por simetria) nao muda a classificacao
    de nenhum no'."""
    baseline = classification_map(walls, build(walls)[0])
    for i in range(len(walls)):
        variant = list(walls)
        variant[i] = flip(walls[i])
        assert classification_map(variant, build(variant)[0]) == baseline, (
            "%s: inverter a parede %d mudou a classificacao" % (plant_name, i))


@pytest.mark.parametrize("kind", ["L_CORNER", "T_INTERSECTION", "X_INTERSECTION",
                                  "FREE_END", "STRAIGHT_CONTINUATION"])
def test_INV_GRAPH_DET_004_a_008_cada_tipo_de_no_permanece(kind):
    """INV-GRAPH-DET-004..008 - L continua L, T continua T, X continua X,
    FREE_END continua FREE_END, STRAIGHT_CONTINUATION continua
    equivalente. Compara NO' A NO' (pela identidade geometrica), nunca
    so' a contagem por categoria: 118 T continuarem 118 T nao prova que
    sao OS MESMOS 118."""
    walls = plant_ltx()
    baseline = classification_map(walls, build(walls)[0])
    expected = set(ident for ident, k in baseline.items() if k == kind)
    assert expected, "a planta de teste nao produziu nenhum %s" % kind

    for name, variant in permutations_of(walls)[1:]:
        got = classification_map(variant, build(variant)[0])
        assert set(i for i, k in got.items() if k == kind) == expected, (
            "%s: o conjunto de nos %s mudou" % (name, kind))


@pytest.mark.parametrize("plant_name,walls", ALL_PLANTS)
def test_INV_GRAPH_DET_009_end_to_node_equivalente_por_geometria(plant_name, walls):
    """INV-GRAPH-DET-009 - `end_to_node` e' equivalente por identidade
    geometrica: a mesma PONTA continua apontando para o mesmo NO'."""
    nodes, end_to_node = build(walls)
    baseline = end_to_node_map(walls, nodes, end_to_node)
    for name, variant in permutations_of(walls)[1:]:
        v_nodes, v_end_to_node = build(variant)
        assert end_to_node_map(variant, v_nodes, v_end_to_node) == baseline, (
            "%s / %s" % (plant_name, name))


def test_INV_GRAPH_DET_010_midspan_crossings_invariantes():
    """INV-GRAPH-DET-010 - os cruzamentos de meio de parede (nenhuma das
    duas termina ali) sao os mesmos, no mesmo lugar, com o mesmo par de
    paredes, em toda ordem."""
    walls = plant_ltx()
    baseline = midspan_set(walls, build(walls)[0])
    assert baseline, "a planta de teste nao produziu nenhum X de meio de parede"
    for name, variant in permutations_of(walls)[1:]:
        assert midspan_set(variant, build(variant)[0]) == baseline, name


def test_INV_GRAPH_DET_011_empates_geometricos_tem_desempate_canonico():
    """INV-GRAPH-DET-011 - num X perfeitamente simetrico as quatro pontas
    sao geometricamente EMPATADAS: nada na geometria diz qual parede e'
    `crossing_walls[0]`. Mas `crossing_walls[0]` decide qual parede recebe
    o B54 da fiada A e qual recebe o da fiada B (solve_x_intersection),
    entao o empate precisa de um desempate CANONICO - o mesmo em toda
    ordem de entrada - e nao "quem a lista trouxe primeiro"."""
    walls = [
        wall(-200.0, 0.0, 0.0, 0.0),
        wall(0.0, 0.0, 200.0, 0.0),
        wall(0.0, -200.0, 0.0, 0.0),
        wall(0.0, 0.0, 0.0, 200.0),
    ]
    baseline = graph_fingerprint(walls, build(walls)[0])
    kinds = set(classification_map(walls, build(walls)[0]).values())
    assert "X_INTERSECTION" in kinds, kinds
    for name, variant in permutations_of(walls)[1:]:
        assert graph_fingerprint(variant, build(variant)[0]) == baseline, name


@pytest.mark.parametrize("plant_name,walls", ALL_PLANTS)
def test_INV_GRAPH_DET_012_build_wall_graph_nao_modifica_a_entrada(plant_name, walls):
    """INV-GRAPH-DET-012 - `build_wall_graph` e' uma funcao PURA sobre a
    lista de paredes: nao reordena, nao troca, nao inverte nada."""
    before = [(id(entry), _pt(entry[0].GetEndPoint(0)), _pt(entry[0].GetEndPoint(1)),
               _r(entry[1])) for entry in walls]
    junction_map = {}
    build(walls, junction_map)
    after = [(id(entry), _pt(entry[0].GetEndPoint(0)), _pt(entry[0].GetEndPoint(1)),
              _r(entry[1])) for entry in walls]
    assert after == before, plant_name
    assert junction_map == {}, "%s: junction_map foi mutado" % plant_name


def test_INV_GRAPH_DET_016_trio_nao_transitivo_vira_um_unico_no():
    """INV-GRAPH-DET-016 - CORRECAO ESTRUTURAL, nao so' determinismo.

    Tres pontas cuja relacao "a <=5 cm" nao e' transitiva (A~B, A~C,
    B!~C) descrevem UM encontro fisico: as tres paredes morrem na MESMA
    parede vertical, dentro da tolerancia. Parti-las em dois nos faz o
    solver resolver o mesmo encontro DUAS vezes - exatamente a falha que o
    cabecalho de `_wall_node_arms` documenta (pecas duplicadas colidindo).

    A definicao geometrica que vale e' COMPONENTE CONEXA: "estas pontas
    pertencem ao mesmo encontro fisico". Este teste fixa isso - e nao
    'qualquer particao, desde que estavel'."""
    walls = plant_non_transitive()
    nodes, _e = build(walls)
    with_three_arms = [n for n in nodes if len(n.get("arms") or []) == 3]
    assert len(with_three_arms) == 1, (
        "o trio nao-transitivo deveria formar UM no' de 3 pontas; nos: %s"
        % [(n.get("kind"), len(n.get("arms") or [])) for n in nodes])


def test_INV_GRAPH_DET_017_ponto_do_no_e_funcao_canonica_do_grupo():
    """INV-GRAPH-DET-017 - CORRECAO ESTRUTURAL, nao so' determinismo.

    Numa parede mais curta que a tolerancia, as DUAS pontas dela caem no
    mesmo no'. O PONTO do no' e' onde o solver da Etapa 4 encosta a celula
    de amarracao - se ele depende de qual ponta a lista trouxe primeiro,
    a peca sai 4,45 cm fora do lugar so' por causa do sentido do desenho.
    O ponto tem que ser funcao das ANCORAS do grupo, nao da ordem."""
    walls = plant_short_wall()
    nodes, _e = build(walls)
    short = [n for n in nodes if len(n.get("arms") or []) == 2
             and len(set(w for w, _e2 in n["arms"])) == 1]
    assert len(short) == 1, "a planta de teste nao produziu o no' da parede curta"
    baseline_point = _pt(short[0]["point"])

    flipped = [flip(w) for w in walls]
    f_nodes, _ = build(flipped)
    f_short = [n for n in f_nodes if len(n.get("arms") or []) == 2
               and len(set(w for w, _e2 in n["arms"])) == 1]
    assert len(f_short) == 1
    assert _pt(f_short[0]["point"]) == baseline_point, (
        "o no' mudou de lugar so' por inverter o sentido do desenho: %s -> %s"
        % (baseline_point, _pt(f_short[0]["point"])))


def test_INV_GRAPH_DET_015_find_wall_pairs_permanece_inalterado():
    """INV-GRAPH-DET-015 - este CR nao pode encostar em `find_wall_pairs`.
    O conjunto GEOMETRICO de pares que ela devolve sobre a mesma entrada
    tem que continuar identico - e continuar invariante a' permutacao, que
    e' a garantia que o CR-2F-B ja' tinha deixado."""
    lines = []
    for y in (0.0, 14.0):                       # um par de 14 cm
        lines.append(Line.CreateBound(XYZ(ft(0.0), ft(y), 0.0), XYZ(ft(400.0), ft(y), 0.0)))
    for x in (600.0, 614.0):                    # outro par de 14 cm
        lines.append(Line.CreateBound(XYZ(ft(x), ft(0.0), 0.0), XYZ(ft(x), ft(300.0), 0.0)))
    targets = [ft(14.0)]
    tol = m.compute_detection_tolerance_ft(targets)

    def pair_geometry(input_lines):
        result = m.find_wall_pairs(input_lines, targets, tol, None)
        pairs = result[0] if isinstance(result, tuple) else result
        out = set()
        for pair in pairs:
            centerline = pair[0] if isinstance(pair, (list, tuple)) else pair
            if not hasattr(centerline, "GetEndPoint"):
                continue
            a = _pt(centerline.GetEndPoint(0))
            b = _pt(centerline.GetEndPoint(1))
            out.add((a, b) if a <= b else (b, a))
        return out

    baseline = pair_geometry(lines)
    assert baseline, "a planta de teste nao produziu nenhum par"
    for seed in SEEDS:
        order = list(range(len(lines)))
        random.Random(seed).shuffle(order)
        assert pair_geometry([lines[i] for i in order]) == baseline, seed


# --------------------------------------- pipeline completo (projeto real)
def _projects_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "nuvem", "benchmark", "projects")


def _load_real_project(project_id="torre_easy_lo_r00_tgd"):
    path = os.path.join(_projects_dir(), project_id, "input.json")
    if not os.path.isfile(path):
        pytest.skip("projeto %s nao versionado neste checkout" % project_id)
    with open(path, "r") as handle:
        return json.load(handle)


def _solver_bridge():
    nuvem = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nuvem")
    if nuvem not in sys.path:
        sys.path.insert(0, nuvem)
    from benchmark import solver_bridge
    return solver_bridge


def _permuted_project(input_project, order):
    new_project = copy.deepcopy(input_project)
    walls = input_project.get("walls") or []
    new_project["walls"] = [copy.deepcopy(walls[i]) for i in order]
    return new_project


def _block_fingerprint(walls_to_create, solve_result):
    rows = []
    course_candidates = solve_result.get("course_candidates") or {}
    for course_index in sorted(course_candidates.keys()):
        for cand in course_candidates[course_index]:
            origin = cand["origin_world"]
            rows.append(str((wall_key(walls_to_create, cand.get("wall_idx")),
                             course_index, cand["logical_code"],
                             _r(origin.X), _r(origin.Y),
                             round(cand["rotation_deg"]) % 360)))
    return sorted(rows)


@pytest.mark.slow
def test_INV_GRAPH_DET_013_fingerprint_de_blocos_independe_da_permutacao():
    """INV-GRAPH-DET-013 - o invariante-alvo do CR: sobre o projeto real,
    o fingerprint FINAL das pecas materializadas tem que ser o mesmo em
    todas as ordens de entrada. Baseline do CR: 8 execucoes, 8
    fingerprints."""
    solver_bridge = _solver_bridge()
    input_project = _load_real_project()
    n = len(input_project["walls"])

    orders = [("baseline", list(range(n))),
              ("reversed", list(reversed(range(n))))]
    for seed in (1, 42):   # duas seeds: a suite completa esta' no benchmark
        order = list(range(n))
        random.Random(seed).shuffle(order)
        orders.append(("shuffle_seed_%d" % seed, order))

    baseline = None
    for name, order in orders:
        result = solver_bridge.run_solver(_permuted_project(input_project, order))
        solve_result, walls_to_create = result[0], result[1]
        fingerprint = _block_fingerprint(walls_to_create, solve_result)
        if baseline is None:
            baseline = fingerprint
            continue
        assert len(fingerprint) == len(baseline), (
            "%s: %d pecas contra %d do baseline" % (name, len(fingerprint), len(baseline)))
        assert fingerprint == baseline, name


@pytest.mark.slow
def test_INV_GRAPH_DET_014_cr_block_01_continua_sem_conflito_de_alinhamento():
    """INV-GRAPH-DET-014 - nao-regressao do CR-BLOCK-01: `alignment_conflicts`
    tem que continuar em ZERO, em toda ordem de entrada."""
    solver_bridge = _solver_bridge()
    input_project = _load_real_project()
    n = len(input_project["walls"])
    orders = [list(range(n)), list(reversed(range(n)))]
    for order in orders:
        result = solver_bridge.run_solver(_permuted_project(input_project, order))
        solve_result = result[0]
        assert len(solve_result.get("alignment_conflicts") or []) == 0
