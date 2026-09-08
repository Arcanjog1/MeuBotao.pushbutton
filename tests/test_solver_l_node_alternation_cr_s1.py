# -*- coding: utf-8 -*-
"""CR-S1 - o solver DEIXA DE ALTERNAR a amarracao num encontro em L.

O DEFEITO (medido, ver docs/CR_S1_L_NODE_ALTERNATION.md)
--------------------------------------------------------
No' fisico presente nos DOIS niveis do corpus real:

    TGD (338,52 ; 187,05)      TP1 (8017,26 ; 1289,95)
    (o mesmo ponto: + [7678,7371 ; 1102,9024])

Geometria local, identica nos dois niveis:

    parede N-S   comeca no no' e sobe 644cm         (TERMINA aqui -> L)
    parede E-O   comeca no no' e vai 939cm para +x  (porta em t=534..625)
    parede E-O   um T na parede N-S, a 50cm do no'  (189cm de comprimento)

Com a topologia antiga a parede N-S ATRAVESSAVA o no' (T) e o solver
alternava. Quando ela passa a TERMINAR ali (L), `solve_l_corner` girava as
DUAS fiadas para a parede E-O e o no' ficava com um dono so' nas 17
fiadas. O humano alterna nas DUAS topologias.

A CAUSA (nao e' "parede curta" - as duas tem 644cm e 939cm)
-----------------------------------------------------------
`_corner_bond_blocked_by_other_node` devolvia um BOOLEANO: sabia que o T
vizinho estava perto demais, e jogava fora em QUAL FIADA. Sem a fiada, a
unica saida segura era girar as duas - o que custa a amarracao do no'.

Estes testes provam a alternancia FISICA no no', nas 17 fiadas e em todos
os 16 pares consecutivos, sem colisao e sem tocar regra de dominio.

    python3 -m pytest tests/test_solver_l_node_alternation_cr_s1.py -q
"""

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

# As DUAS instancias reais do MESMO no' fisico, com as coordenadas
# ABSOLUTAS que a entrada reconstruida da CR-B entrega ao solver (extraidas
# de `input_candidate.json`, paredes 64/70 e o T vizinho). O TP1 e' o caso
# de entrada reconstruida de verdade; o TGD e' a geometria equivalente.
NODE_CASES = {
    # rotulo: (dx, dy, base_z_cm, sill_cm, head_cm)
    "TGD": (0.0, 0.0, 0.0, 0.0, 160.0),
    "TP1": (7678.7371, 1102.9024, 612.0, 612.0, 772.0),
}
NUM_COURSES = 17
NS, EW, TEE = 0, 1, 2          # papeis, nao indices - ver `build_case`


def build_case(dx=0.0, dy=0.0, sill_cm=0.0, head_cm=160.0, order=(NS, EW, TEE),
               mirror_y=False):
    """A planta local do no' da CR-S1. `order` permuta a ORDEM DE ENTRADA
    das paredes (nunca a geometria); `mirror_y` espelha o T para o outro
    lado do no', invertendo a orientacao do encontro.

    Devolve `(walls, nodes, end_to_node, openings, role_to_idx, node_index)`."""
    ns_len, ew_len = 644.0, 939.0
    tee_dy = -50.0 if mirror_y else 50.0
    node_x, node_y = 338.523 + dx, 187.048 + dy
    lines = {
        NS: seg(node_x, node_y - 7.0, node_x, node_y - 7.0 + ns_len),
        EW: seg(node_x - 7.02, node_y, node_x - 7.02 + ew_len, node_y),
        TEE: seg(node_x - 182.01, node_y + tee_dy, node_x + 7.0, node_y + tee_dy),
    }
    openings = {
        NS: [],
        EW: [(ft(534.0), ft(625.0), ft(sill_cm), ft(head_cm))],
        TEE: [],
    }
    role_to_idx = dict((role, position) for position, role in enumerate(order))
    walls = [(lines[role], ft(14.0), (False, False)) for role in order]
    per_wall = [openings[role] for role in order]
    # `walls_already_extended` na entrada real -> extensao 0.0 aqui.
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, 0.0)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)

    node_index = None
    for index, node in enumerate(nodes):
        point = node.get("point")
        if point is None:
            continue
        if (abs(to_cm(point.X) - node_x) < 1.0
                and abs(to_cm(point.Y) - node_y) < 1.0):
            node_index = index
            break
    assert node_index is not None, "no' da CR-S1 nao encontrado na planta"
    return walls, nodes, end_to_node, per_wall, role_to_idx, node_index


def node_owner_by_course(result, node_index):
    """`{indice_de_fiada: parede_dona}` - a parede sobre a qual a peca de
    amarracao DESTE no' deita, fiada fisica a fiada fisica."""
    owners = {}
    for course_index, candidates in result["course_candidates"].items():
        for candidate in candidates:
            if candidate.get("node_index") != node_index:
                continue
            owners.setdefault(course_index, set()).add(candidate.get("wall_idx"))
    return owners


def run_stack(dx=0.0, dy=0.0, base_z_cm=0.0, sill_cm=0.0, head_cm=160.0,
              order=(NS, EW, TEE), mirror_y=False):
    walls, nodes, end_to_node, per_wall, role_to_idx, node_index = build_case(
        dx=dx, dy=dy, sill_cm=sill_cm, head_cm=head_cm, order=order, mirror_y=mirror_y)
    result = m.solve_building_blocks_all_courses(
        nodes, walls, end_to_node, per_wall, CATALOG,
        base_z_abs=ft(base_z_cm), num_courses=NUM_COURSES)
    return result, walls, nodes, role_to_idx, node_index


# ============================================================
# 1 - O DEFEITO: alternancia fisica no no' real, nas 17 fiadas
# ============================================================

@pytest.mark.parametrize("label", sorted(NODE_CASES))
def test_no_da_cr_s1_alterna_em_todas_as_fiadas(label):
    """FALHA no codigo pre-CR-S1: o no' saia com UM dono nas 17 fiadas.

    Nao exige QUAL parede leva a fiada par - exige que as duas paredes do
    L apareçam e que NENHUM par consecutivo repita o dono (a definicao
    fisica de amarracao entre fiadas)."""
    dx, dy, base_z, sill, head = NODE_CASES[label]
    result, _walls, _nodes, role_to_idx, node_index = run_stack(
        dx=dx, dy=dy, base_z_cm=base_z, sill_cm=sill, head_cm=head)
    owners = node_owner_by_course(result, node_index)

    assert sorted(owners) == list(range(NUM_COURSES)), (
        "%s: toda fiada precisa de peca de amarracao neste no': %s" % (label, sorted(owners)))
    for course_index, walls_here in sorted(owners.items()):
        assert len(walls_here) == 1, (label, course_index, walls_here)

    donos = set(next(iter(owners[c])) for c in owners)
    assert donos == {role_to_idx[NS], role_to_idx[EW]}, (
        "%s: as DUAS paredes do L precisam levar a amarracao em alguma fiada "
        "(um dono so' = alternancia perdida, o defeito da CR-S1): %s" % (label, donos))

    # os 16 pares consecutivos das 17 fiadas - o que a evidencia da CR-B
    # contou como 16 achados de UM no' so'
    pares_iguais = [
        (c, c + 1) for c in range(NUM_COURSES - 1)
        if next(iter(owners[c])) == next(iter(owners[c + 1]))
    ]
    assert pares_iguais == [], (
        "%s: pares consecutivos sem troca de dono: %s" % (label, pares_iguais))


@pytest.mark.parametrize("label", sorted(NODE_CASES))
def test_no_da_cr_s1_alterna_sem_colisao_na_mesma_fiada(label):
    """Alternancia restaurada NAO pode custar colisao: as pecas de
    amarracao de cada fiada fisica continuam sem sobreposicao."""
    dx, dy, base_z, sill, head = NODE_CASES[label]
    result, _walls, _nodes, _role_to_idx, _node_index = run_stack(
        dx=dx, dy=dy, base_z_cm=base_z, sill_cm=sill, head_cm=head)
    for course_index, candidates in sorted(result["course_candidates"].items()):
        colisoes = m.validate_same_course_collision(candidates)
        assert colisoes == [], (label, course_index, colisoes)


def test_no_da_cr_s1_e_o_mesmo_resultado_fisico_nos_dois_niveis():
    """TGD e TP1 sao o MESMO ponto fisico transladado - a decisao de
    amarracao precisa ser a mesma, papel por papel (nao por wall_idx)."""
    por_nivel = {}
    for label, (dx, dy, base_z, sill, head) in sorted(NODE_CASES.items()):
        result, _w, _n, role_to_idx, node_index = run_stack(
            dx=dx, dy=dy, base_z_cm=base_z, sill_cm=sill, head_cm=head)
        idx_to_role = dict((v, k) for k, v in role_to_idx.items())
        owners = node_owner_by_course(result, node_index)
        por_nivel[label] = dict(
            (c, idx_to_role[next(iter(w))]) for c, w in owners.items())
    assert por_nivel["TGD"] == por_nivel["TP1"], por_nivel


# ============================================================
# 2 - INVARIANCIA: ordem de entrada e orientacao do encontro
# ============================================================

@pytest.mark.parametrize("order", [(NS, EW, TEE), (TEE, EW, NS), (EW, TEE, NS)])
def test_alternancia_do_no_independe_da_ordem_de_entrada(order):
    """A alternancia nao pode depender de a parede bloqueada ser `arms[0]`
    ou `arms[1]`. Foi exatamente isso que quebrou a primeira versao desta
    correcao: numa ordem ela trocava os papeis, na outra girava."""
    result, _w, _n, role_to_idx, node_index = run_stack(order=order)
    owners = node_owner_by_course(result, node_index)
    idx_to_role = dict((v, k) for k, v in role_to_idx.items())
    por_fiada = dict((c, idx_to_role[next(iter(w))]) for c, w in owners.items())
    esperado = dict((c, EW if c % 2 == 0 else NS) for c in range(NUM_COURSES))
    assert por_fiada == esperado, (order, por_fiada)


def test_alternancia_do_no_com_o_T_espelhado_para_o_outro_lado():
    """Mesma geometria com o T do outro lado do no' (orientacao invertida
    do encontro) - continua alternando, e sem colisao."""
    result, _w, _n, role_to_idx, node_index = run_stack(mirror_y=True)
    owners = node_owner_by_course(result, node_index)
    donos = set(next(iter(owners[c])) for c in owners)
    assert donos == {role_to_idx[NS], role_to_idx[EW]}, donos
    for course_index, candidates in sorted(result["course_candidates"].items()):
        assert m.validate_same_course_collision(candidates) == [], course_index


def test_alternancia_do_no_e_determinista_em_execucoes_repetidas():
    """Mesma entrada, 3 execucoes -> mesma decisao."""
    saidas = []
    for _ in range(3):
        result, _w, _n, role_to_idx, node_index = run_stack()
        idx_to_role = dict((v, k) for k, v in role_to_idx.items())
        owners = node_owner_by_course(result, node_index)
        saidas.append(tuple(sorted(
            (c, idx_to_role[next(iter(w))]) for c, w in owners.items())))
    assert len(set(saidas)) == 1, saidas


# ============================================================
# 3 - CONTROLE: o que ja' estava certo NAO pode mudar
# ============================================================

def test_controle_T_a_20cm_continua_girando_as_duas_fiadas():
    """O caso que ORIGINOU o giro (2026-08-25): com o T a 20cm, o vizinho
    ocupa a parede bloqueada nas DUAS fiadas (peca deitada na fiada A,
    corpo da peca da perpendicular na fiada B), a troca de papeis so'
    migraria a colisao, e o giro continua sendo a unica saida sem
    sobreposicao. Controle direto contra "resolver a CR-S1 alternando
    sempre"."""
    walls = [(seg(0, 0, 500, 0), ft(14.0), (False, False)),
             (seg(0, 0, 0, 300), ft(14.0), (False, False)),
             (seg(20, 0, 20, 300), ft(14.0), (False, False))]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    corner = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]
    candidates = m.solve_all_intersections(
        nodes, walls, CATALOG, [[], [], []], end_to_node)["candidates"]
    donos = set(c["wall_idx"] for c in candidates if c.get("node_index") == corner)
    assert len(donos) == 1, (
        "com o vizinho ocupando as duas fiadas o giro continua: %s" % donos)
    for course in ("A", "B"):
        do_course = [c for c in candidates if c["course"] == course]
        assert m.validate_same_course_collision(do_course) == [], course


def test_controle_L_isolado_continua_alternando():
    """L sem vizinho nenhum - nunca passou pelo gate, nao pode mudar."""
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False)),
             (seg(0, 0, 0, 400), ft(14.0), (False, False))]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    corner = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]
    result = m.solve_l_corner(nodes[corner], walls, CATALOG, node_index=corner,
                              openings_per_wall=[[], []], nodes=nodes,
                              end_to_node=end_to_node)
    assert result["ok"] is True, result["reason"]
    assert result["course_a"]["wall_idx"] != result["course_b"]["wall_idx"], result


def test_controle_T_e_X_isolados_nao_mudam_de_papel():
    """T e X sao controles: a CR-S1 nao toca os solvers deles."""
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False)),
             (seg(200, 0, 200, 300), ft(14.0), (False, False))]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    tee = [i for i, n in enumerate(nodes) if n["kind"] == "T_INTERSECTION"][0]
    result = m.solve_t_intersection(nodes[tee], walls, CATALOG, node_index=tee,
                                    openings_per_wall=[[], []], nodes=nodes,
                                    end_to_node=end_to_node)
    assert result["course_a"]["wall_idx"] == nodes[tee]["main_wall_idx"], result
    assert result["course_b"]["wall_idx"] == nodes[tee]["incoming_wall_idx"], result

    walls_x = [(seg(0, 200, 400, 200), ft(14.0), (False, False)),
               (seg(200, 0, 200, 400), ft(14.0), (False, False))]
    walls_x, jmap_x = m.extend_wall_ends_to_junctions(walls_x, m.JUNCTION_FACE_SEARCH_FT)
    nodes_x, e2n_x = m.build_wall_graph(walls_x, jmap_x)
    cross = [i for i, n in enumerate(nodes_x) if n["kind"] == "X_INTERSECTION"][0]
    result_x = m.solve_x_intersection(nodes_x[cross], walls_x, CATALOG, node_index=cross,
                                      openings_per_wall=[[], []], nodes=nodes_x,
                                      end_to_node=e2n_x)
    pair = nodes_x[cross]["crossing_walls"]
    assert result_x["course_a"]["wall_idx"] == pair[0], result_x
    assert result_x["course_b"]["wall_idx"] == pair[1], result_x


# ============================================================
# 4 - As pecas novas do gate, uma a uma
# ============================================================

def test_predicado_booleano_do_gate_nao_mudou():
    """`_corner_bond_blocked_by_other_node` continua respondendo o MESMO
    que antes da CR-S1 - a fiada "deitada" mantem os 27cm, que e' o maior
    dos dois alcances, entao "bloqueado em alguma fiada" e' identico.
    Aqui: o T a 50cm bloqueia (50 < 34+27), e um T a 70cm nao (70 > 61)."""
    for distancia_cm, esperado in ((50.0, True), (70.0, False)):
        walls = [(seg(0, 0, 500, 0), ft(14.0), (False, False)),
                 (seg(0, 0, 0, 300), ft(14.0), (False, False)),
                 (seg(distancia_cm, 0, distancia_cm, 300), ft(14.0), (False, False))]
        walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
        nodes, end_to_node = m.build_wall_graph(walls, junction_map)
        corner = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]
        point = m._node_contact_point_for_wall(nodes[corner], 0)
        _end, direction, _len, _t = m._wall_end_and_dir_near_point(walls, 0, point)
        blocked = m._corner_bond_blocked_by_other_node(
            walls, nodes, 0, point, direction, m.CORNER_B34_ROOM_FT, corner)
        assert blocked is esperado, (distancia_cm, blocked)


def test_fiadas_de_um_no_sobre_uma_parede_seguem_a_convencao_do_solver():
    """`_node_bond_courses_on_wall` so' pode afirmar UMA fiada quando o
    solver daquele tipo de no' a fixa em TODOS os caminhos dele."""
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False)),
             (seg(200, 0, 200, 300), ft(14.0), (False, False))]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    tee = [n for n in nodes if n["kind"] == "T_INTERSECTION"][0]
    # principal: SO' a fiada A (B54 cheio, B34 da degradacao-L, ou nada)
    assert tuple(m._node_bond_courses_on_wall(tee, tee["main_wall_idx"])) == ("A",)
    # boneca: a degradacao 2 poe o mesmo elemento nas DUAS -> pior caso
    assert set(m._node_bond_courses_on_wall(tee, tee["incoming_wall_idx"])) == {"A", "B"}

    walls_x = [(seg(0, 200, 400, 200), ft(14.0), (False, False)),
               (seg(200, 0, 200, 400), ft(14.0), (False, False))]
    walls_x, jmap_x = m.extend_wall_ends_to_junctions(walls_x, m.JUNCTION_FACE_SEARCH_FT)
    nodes_x, _e2n_x = m.build_wall_graph(walls_x, jmap_x)
    cross = [n for n in nodes_x if n["kind"] == "X_INTERSECTION"][0]
    pair = cross["crossing_walls"]
    assert tuple(m._node_bond_courses_on_wall(cross, pair[0])) == ("A",)
    assert tuple(m._node_bond_courses_on_wall(cross, pair[1])) == ("B",)

    # L_CORNER: o proprio giro pode mandar as duas fiadas para a mesma
    # parede -> nunca afirma uma fiada so'
    walls_l = [(seg(0, 0, 400, 0), ft(14.0), (False, False)),
               (seg(0, 0, 0, 400), ft(14.0), (False, False))]
    walls_l, jmap_l = m.extend_wall_ends_to_junctions(walls_l, m.JUNCTION_FACE_SEARCH_FT)
    nodes_l, _e2n_l = m.build_wall_graph(walls_l, jmap_l)
    corner = [n for n in nodes_l if n["kind"] == "L_CORNER"][0]
    for wall_idx, _end_index in corner["arms"]:
        assert set(m._node_bond_courses_on_wall(corner, wall_idx)) == {"A", "B"}


def test_gate_por_fiada_usa_dois_alcances_diferentes():
    """A fiada em que o vizinho DEITA peca sobre a parede usa o teto de
    27cm; a outra usa a reserva generica do no' (metade da espessura). E'
    o que separa o T a 50cm (bloqueia so' a fiada A) do T a 20cm
    (bloqueia as duas)."""
    def busy_na_parede_principal(distancia_cm):
        walls = [(seg(0, 0, 500, 0), ft(14.0), (False, False)),
                 (seg(0, 0, 0, 300), ft(14.0), (False, False)),
                 (seg(distancia_cm, 0, distancia_cm, 300), ft(14.0), (False, False))]
        walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
        nodes, end_to_node = m.build_wall_graph(walls, junction_map)
        corner = [i for i, n in enumerate(nodes) if n["kind"] == "L_CORNER"][0]
        point = m._node_contact_point_for_wall(nodes[corner], 0)
        _end, direction, _len, _t = m._wall_end_and_dir_near_point(walls, 0, point)
        return m._corner_bond_blocking_courses(
            walls, nodes, 0, point, direction, m.CORNER_B34_ROOM_FT, corner)

    assert busy_na_parede_principal(50.0) == {"A"}, busy_na_parede_principal(50.0)
    assert busy_na_parede_principal(20.0) == {"A", "B"}, busy_na_parede_principal(20.0)
    assert busy_na_parede_principal(70.0) == set(), busy_na_parede_principal(70.0)
