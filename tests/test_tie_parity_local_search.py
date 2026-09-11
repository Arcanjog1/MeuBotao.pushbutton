# -*- coding: utf-8 -*-
"""ETAPA 7 - paridade de amarracao por no' (search_tie_parity).

Evidencia: BUTANTA R08_LT 1o PAV (2026-09-11) - o humano escolhe no' a no'
qual peca de amarracao cai na fiada par; a convencao fixa por papel (B54 da
principal sempre na fiada A) obriga trechos que so' fecham com compensador
empilhado. Ver docs/checkpoints/2026-09-11-revit-scale-autofix-final.md.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
CATALOG = sb.CATALOG
ft = sb.ft
seg = sb.seg
ws = sys.modules["core.engine.wall_stepper"]
EV = os.path.join(os.path.dirname(HERE), "docs", "checkpoints", "evidence")


def _graph(lines):
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jmap)
    return walls, nodes, e2n


def test_marca_no_no_troca_a_fiada_das_duas_pecas():
    """Mecanica: um no' marcado com _tie_parity_flip poe o B54 da principal
    na fiada B e o B34 da que chega na fiada A - a relacao B54<->B34 e' a
    mesma, so' a paridade muda."""
    walls, nodes, e2n = _graph([seg(0, 0, 0, 600), seg(-200, 300, 0, 300)])
    t_nodes = [i for i, n in enumerate(nodes) if n["kind"] == "T_INTERSECTION"]
    assert len(t_nodes) == 1
    before = m.solve_all_intersections(nodes, walls, CATALOG, openings_per_wall=[[] for _ in walls], end_to_node=e2n)
    by_code = {c["logical_code"]: c["course"] for c in before["candidates"]}
    assert by_code == {"B54": "A", "B34": "B"}
    nodes[t_nodes[0]]["_tie_parity_flip"] = True
    after = m.solve_all_intersections(nodes, walls, CATALOG, openings_per_wall=[[] for _ in walls], end_to_node=e2n)
    by_code = {c["logical_code"]: c["course"] for c in after["candidates"]}
    assert by_code == {"B54": "B", "B34": "A"}


def test_sem_parede_reprovada_a_busca_nao_faz_nada():
    walls, nodes, e2n = _graph([seg(0, 0, 340, 0), seg(0, 0, 0, 69)])
    calls = []

    def rebuild():
        calls.append(1)
        return {"error": None, "wall_bond_audits": {0: {"ok": True}}, "course_candidates": {}, "collisions": []}

    base = rebuild()
    out = ws.search_tie_parity(nodes, walls, base, rebuild)
    assert out["changed"] is False and out["flips"] == [] and out["tried"] == 0
    assert not any(n.get("_tie_parity_flip") for n in nodes)


def test_busca_e_determinista_e_reverte_flips_que_nao_ajudam():
    """Rebuild simulado: so' o flip do no' geometricamente menor ajuda."""
    walls, nodes, e2n = _graph([seg(0, 0, 0, 600), seg(-200, 200, 0, 200), seg(0, 400, 200, 400)])
    t_nodes = sorted((i for i, n in enumerate(nodes) if n["kind"] == "T_INTERSECTION"),
                     key=lambda i: ws._canonical_node_sort_key(nodes[i]))
    good = t_nodes[0]

    def rebuild():
        flipped = {i for i, n in enumerate(nodes) if n.get("_tie_parity_flip")}
        reproved = 0 if flipped == {good} else (1 if not flipped else 2)
        return {"error": None, "wall_bond_audits": {0: {"ok": reproved == 0}, 1: {"ok": reproved < 2}},
                "course_candidates": {}, "collisions": []}

    base = {"error": None, "wall_bond_audits": {0: {"ok": False}, 1: {"ok": True}}, "course_candidates": {}, "collisions": []}
    out = ws.search_tie_parity(nodes, walls, base, rebuild)
    assert out["changed"] is True and out["flips"] == [good]
    assert [i for i, n in enumerate(nodes) if n.get("_tie_parity_flip")] == [good]


def test_butanta_494cm_entre_duas_principais_fecha_sem_faixa_de_compensador():
    """Integracao sobre eixos REAIS (fixture de evidencia, nao benchmark):
    a parede de 494cm 8079833 entre as principais 8079818 e 8079777. Com a
    regra #2 intacta o default fecha com faixa de C09 (reprovada); a busca
    de paridade inverte um dos T e a parede fecha - 0 reprovadas."""
    path = os.path.join(EV, "2026-09-10-butanta-test-walls.json")
    if not os.path.isfile(path):
        import pytest
        pytest.skip("fixture ausente")
    walls_json = {w["id"]: w for w in json.load(open(path))["walls"]}
    XYZ, Line = m.XYZ, m.Line
    lines = [Line.CreateBound(XYZ(*map(float, walls_json[i]["p0"])), XYZ(*map(float, walls_json[i]["p1"])))
             for i in (8079818, 8079777, 8079833)]
    walls, nodes, e2n = _graph(lines)
    openings = [[] for _ in walls]
    base = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings, CATALOG, 0.0, 14,
                                               variants_per_course=1, tie_parity_search=False)
    reproved_base = [wi for wi, a in base["wall_bond_audits"].items() if not a["ok"]]
    # 2026-09-11 (regra da fileira de B34, decisao do usuario): a parede de
    # 494cm ja' fecha SEM faixa de compensador no default - B34 + 9xB39 +
    # B34 B34, como o humano. A busca de paridade passa a ser um no-op aqui
    # (nada reprovado para consertar) e nunca pode piorar o resultado.
    assert 2 not in reproved_base, "a parede de 494cm deveria fechar sem faixa no default: %r" % reproved_base
    for n in nodes:
        n.pop("_tie_parity_flip", None)
    best = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings, CATALOG, 0.0, 14,
                                               variants_per_course=1, tie_parity_search=True)
    reproved_best = [wi for wi, a in best["wall_bond_audits"].items() if not a["ok"]]
    assert not best["tie_parity_search"]["flips"], best["tie_parity_search"]
    assert 2 not in reproved_best, reproved_best
    assert len(reproved_best) <= len(reproved_base)
