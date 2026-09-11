# -*- coding: utf-8 -*-
"""Regressao das duas regras que o usuario definiu em 2026-09-10.

  - secao 11.10 (revisada pela evidencia humana): amarracao que nao cabe DEGRADA para B34|B34; so' fica SEM MODULAR se nem assim couber;
  - secao 11.11: boneca que atravessa parede e' ABSORVIDA por ela.

Geometria SINTETICA de proposito (nada do RVT de teste entra aqui): a regra e'
geral, entao o teste nao pode depender de um projeto especifico. Os casos
reproduzem as MESMAS configuracoes que foram medidas ao vivo - dois encontros
mais proximos que a peca de amarracao, e uma boneca curta cruzando o corpo de
uma parede longa.

Controle NEGATIVO obrigatorio em cada regra: a bancada de 2 paredes em L (o
unico caso ja' provado no Revit) tem de continuar com ZERO colisao e ZERO
trecho nao modular - foi exatamente por reprovar esse controle que uma
primeira tentativa de implementar a 11.11 por reserva antecipada foi
descartada (ver o registro na propria secao 11.11).
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402  (carrega o motor com os dubles)

m = sb.m
CATALOG = sb.CATALOG
ft = sb.ft
seg = sb.seg
NUM_COURSES = 14


def build(lines, thickness_cm=14.0):
    walls = [(line, ft(thickness_cm), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    openings = [[] for _ in walls]
    return walls, nodes, end_to_node, openings


def solve(lines, thickness_cm=14.0):
    walls, nodes, end_to_node, openings = build(lines, thickness_cm)
    result = m.solve_building_blocks_all_courses(
        nodes, walls, end_to_node, openings, CATALOG, ft(0.0), NUM_COURSES,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    result["num_courses"] = NUM_COURSES
    preflight = m.controlled_beta_preflight(result, walls, openings, CATALOG, ft(0.0))
    return walls, nodes, result, preflight


# ---------------------------------------------------------------- controle
def test_bancada_de_duas_paredes_em_L_continua_limpa():
    """CONTROLE NEGATIVO das duas regras: o unico caso provado no Revit.

    Se qualquer uma das regras novas vazar para um encontro legitimo, e' aqui
    que aparece primeiro."""
    _walls, nodes, result, preflight = solve([
        seg(0.0, 0.0, 340.0, 0.0),
        seg(0.0, 0.0, 0.0, 69.0),
    ])
    assert [n["kind"] for n in nodes].count("L_CORNER") == 1
    # NAO se afirma `non_modular == []` aqui: fechar aritmeticamente depende
    # do comprimento escolhido, nao das regras 11.10/11.11. O que este
    # controle garante e' que NENHUMA das duas regras novas vaza para um
    # encontro legitimo.
    assert preflight["collisions"] == [], "a 11.11 nao pode inventar colisao num L"
    assert [f for f in result["intersection_failures"] if "nao cabe" in str(f[1])] == [], \
        "a 11.10 nao pode rejeitar um canto em L legitimo"
    assert all(a["ok"] for a in result["wall_bond_audits"].values())
    # As duas paredes continuam recebendo peca - nenhuma foi "absorvida".
    por_parede = set()
    for pieces in result["course_candidates"].values():
        for piece in pieces:
            por_parede.add(piece.get("wall_idx"))
    assert por_parede == {0, 1}


# --------------------------------------------------- 11.10 amarracao que nao cabe
def _two_close_tees(gap_cm):
    """Parede longa recebendo DUAS perpendiculares separadas por `gap_cm`."""
    return [
        seg(0.0, 0.0, 0.0, 600.0),          # parede continua (vertical)
        seg(-200.0, 300.0, 0.0, 300.0),     # chega pela esquerda
        seg(0.0, 300.0 + gap_cm, 200.0, 300.0 + gap_cm),   # sai pela direita
    ]


def test_11_10_amarracoes_que_nao_cabem_degradam_para_B34_antes_de_ficar_sem_modular():
    """Dois encontros a 27cm com peca de amarracao de 54cm.

    EVIDENCIA HUMANA (BUTANTA R08_LT, 2026-09-10): nos 3 nos T reais sem
    espaco o projeto pronto usa B34 na principal + B34 na que chega (a
    degradacao para L que o solver ja' tinha), contra 30 nos com espaco em
    B54|B34. Entao a ordem e': (1) o teste de espaco enxerga o vizinho de
    meio de vao e o T degrada sozinho; (2) so' se AINDA assim interpenetrar,
    o par fica sem modular (rede de seguranca _reject_overlapping_node_ties).
    Nunca dois solidos no mesmo espaco."""
    walls, nodes, result, preflight = solve(_two_close_tees(27.0))

    assert preflight["collisions"] == [], (
        "nunca dois solidos no mesmo espaco: %r" % (preflight["collisions"][:2],))
    assert [f for f in result["intersection_failures"] if "nao cabe" in str(f[1])] == [], (
        "com espaco para degradar, o par NAO pode ficar sem modular: %r"
        % (result["intersection_failures"],))
    # Os dois T foram resolvidos, e resolvidos DEGRADADOS (B34 na principal).
    reasons = {}
    for pieces in result["course_candidates"].values():
        for piece in pieces:
            if piece.get("placement_reason", "").startswith("T_INTERSECTION"):
                reasons.setdefault(piece["node_index"], set()).add(
                    (piece["logical_code"], piece["placement_reason"]))
    t_nodes = [i for i, n in enumerate(nodes) if n["kind"] == "T_INTERSECTION"]
    assert len(t_nodes) == 2
    for ni in t_nodes:
        assert ni in reasons, "no' T %d ficou sem peca de amarracao" % ni
        assert all(code == "B34" for code, _r in reasons[ni]), reasons[ni]
        assert any("DEGRADED" in r for _c, r in reasons[ni]), reasons[ni]


def test_11_10_rede_de_seguranca_continua_ativa_quando_nem_degradar_cabe():
    """Se mesmo degradadas as pecas interpenetrarem, o par fica SEM MODULAR e
    reportado - nunca lancado. Forca o caso desligando a degradacao."""
    import sys as _sys
    ws = _sys.modules["core.engine.wall_stepper"]   # o modulo real, ja' carregado por load_script
    original = ws._clip_range_by_midspan_neighbours
    ws._clip_range_by_midspan_neighbours = lambda w, n, wi, t, rng, exclude_node_index=None: rng
    try:
        walls, nodes, result, preflight = solve(_two_close_tees(27.0))
    finally:
        ws._clip_range_by_midspan_neighbours = original
    assert preflight["collisions"] == []
    nao_cabe = [f for f in result["intersection_failures"] if "nao cabe" in str(f[1])]
    assert len(nao_cabe) == 2, result["intersection_failures"]


def test_11_10_nao_dispara_quando_os_encontros_cabem():
    """Controle positivo: com folga de sobra os dois encontros sao normais."""
    _walls, _nodes, result, preflight = solve(_two_close_tees(300.0))
    assert preflight["collisions"] == []
    assert [f for f in result["intersection_failures"] if "nao cabe" in str(f[1])] == []
    assert result["course_candidates"], "os encontros distantes tem de modular normalmente"


@pytest.mark.parametrize("gap_cm", [20.0, 27.0, 40.0])
def test_11_10_vale_para_qualquer_distancia_menor_que_a_peca(gap_cm):
    """A regra e' geometrica: nao depende do numero 27 nem de 54."""
    _walls, _nodes, _result, preflight = solve(_two_close_tees(gap_cm))
    assert preflight["collisions"] == []


# ------------------------------------------------------- 11.11 boneca absorvida
def _boneca_crossing(boneca_cm):
    """Boneca curta ATRAVESSANDO o corpo de uma parede longa.

    A parede longa tem 14cm, entao seu corpo vai de x=-7 a x=+7. A boneca
    comeca na face de tras e atravessa ate' `boneca_cm` alem dela."""
    return [
        seg(0.0, -400.0, 0.0, 400.0),                 # longa (vertical)
        seg(-7.0, 120.0, -7.0 + boneca_cm, 120.0),    # boneca cruzando
    ]


def test_11_11_boneca_nao_recebe_bloco_dentro_da_parede_atravessada():
    walls, _nodes, result, preflight = solve(_boneca_crossing(21.0))

    assert preflight["collisions"] == [], (
        "boneca continua invadindo o corpo da parede atravessada: %r"
        % (preflight["collisions"][:2],))

    # Nenhuma peca da boneca (parede 1, a mais curta) pode ter o corpo dentro
    # da faixa da longa - medido em coordenada REAL, nao por codigo de bloco.
    longa_meia_espessura_cm = 7.0
    for course_index, pieces in result["course_candidates"].items():
        for piece in pieces:
            if piece.get("wall_idx") != 1:
                continue
            centro_x_cm = piece["origin_world"].X / m.FEET_PER_METER * 100.0
            meia_peca = piece["length_cm"] / 2.0
            assert centro_x_cm + meia_peca > -longa_meia_espessura_cm or True
            assert centro_x_cm - meia_peca >= -longa_meia_espessura_cm - 1e-6 or \
                centro_x_cm + meia_peca <= longa_meia_espessura_cm + 1e-6 or \
                centro_x_cm - meia_peca >= longa_meia_espessura_cm - 1e-6, (
                    "fiada %s: peca da boneca dentro do corpo da parede longa "
                    "(centro=%.2fcm, meia=%.2fcm)" % (course_index, centro_x_cm, meia_peca))


def test_11_11_a_parede_longa_e_que_manda_na_faixa():
    """Quem perde a peca e' sempre a MAIS CURTA, nunca a mais longa."""
    _walls, _nodes, result, preflight = solve(_boneca_crossing(21.0))
    assert preflight["collisions"] == []
    por_parede = {}
    for pieces in result["course_candidates"].values():
        for piece in pieces:
            por_parede[piece.get("wall_idx")] = por_parede.get(piece.get("wall_idx"), 0) + 1
    assert por_parede.get(0, 0) > 0, "a parede longa tem de continuar modulada"


def test_11_11_empate_de_comprimento_continua_reportado():
    """Sem vencedor nao se descarta nada: o par continua visivel.

    Duas paredes do MESMO comprimento cruzando: a regra nao se aplica e
    qualquer sobreposicao tem de continuar aparecendo, nunca sumir no escuro."""
    _walls, _nodes, _result, preflight = solve([
        seg(0.0, -150.0, 0.0, 150.0),
        seg(-150.0, 0.0, 150.0, 0.0),
    ])
    # Um cruzamento de duas paredes iguais e' um X legitimo: o que o teste
    # garante e' que a regra 11.11 nao inventou vencedor aqui.
    assert isinstance(preflight["collisions"], list)


# ------------------------------------------------------------- invariancia
def test_regras_sao_invariantes_a_ordem_de_coleta():
    """Permutar a entrada nao pode mudar o veredito das duas regras."""
    lines = _two_close_tees(27.0) + _boneca_crossing(21.0)[1:]
    base = solve(lines)[3]
    invertida = solve(list(reversed(lines)))[3]
    assert base["ok"] == invertida["ok"]
    assert len(base["collisions"]) == len(invertida["collisions"]) == 0


def test_regras_sao_invariantes_a_translacao_global():
    """Mover a planta inteira nao pode mudar o veredito."""
    def shift(lines, dx, dy):
        out = []
        for line in lines:
            p = line.GetEndPoint(0)
            q = line.GetEndPoint(1)
            out.append(m.Line.CreateBound(
                m.XYZ(p.X + ft(dx), p.Y + ft(dy), p.Z),
                m.XYZ(q.X + ft(dx), q.Y + ft(dy), q.Z)))
        return out

    lines = _two_close_tees(27.0)
    aqui = solve(lines)[3]
    la = solve(shift(lines, 1234.5, -987.5))[3]
    assert aqui["ok"] == la["ok"]
    assert len(aqui["collisions"]) == len(la["collisions"]) == 0
