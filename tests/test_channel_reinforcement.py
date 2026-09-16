# -*- coding: utf-8 -*-
"""Estrategia de reforco de aberturas CHANNEL (canaletas) - regra 51.

Fixtures SINTETICAS derivadas da fisica medida no BUTANTA R08_LT (nenhum
ElementId, W0xx ou coordenada do corpus): parede livre com porta e janela,
T com jamba na face da parede que chega, T com o B54 da principal sobre o
vao, passagem entre dois T, topo fora da grade, vao ate' o topo.

    python3 -m pytest tests/test_channel_reinforcement.py -q
"""
import hashlib
import io
import os
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import revit_stubs  # noqa: E402
import solver_bench as sb  # noqa: E402

m = sb.m
ft = sb.ft
seg = sb.seg

from core.engine import opening_reinforcement as orf  # noqa: E402

NUM_COURSES = 14
CHANNEL = orf.OPENING_REINFORCEMENT_CHANNEL


def _cm(value_ft):
    return value_ft * 100.0 / m.FEET_PER_METER


def solve(lines, openings, strategy=CHANNEL, policy=None, reverse=False, num_courses=NUM_COURSES):
    if reverse:
        lines = [m.Line.CreateBound(l.GetEndPoint(1), l.GetEndPoint(0)) for l in lines]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    if reverse:
        flipped = []
        for wi, ops in enumerate(openings):
            length = _cm(walls[wi][0].Length)
            flipped.append(sorted((ft(length - _cm(o[1])), ft(length - _cm(o[0])), o[2], o[3]) for o in ops))
        openings = flipped
    result = m.solve_building_blocks_all_courses(
        nodes, walls, end_to_node, openings, sb.CATALOG, 0.0, num_courses,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
        opening_reinforcement_strategy=strategy, opening_reinforcement_policy=policy)
    result["num_courses"] = num_courses
    return result, walls, nodes, openings


def strip(result, walls, wall_idx, course):
    return orf._wall_strip_pieces(result["course_candidates"][course], walls, wall_idx)


def codes_over(result, walls, wall_idx, course, lo, hi):
    return [r["cand"]["logical_code"] for r in strip(result, walls, wall_idx, course)
            if r["hi"] > lo + 0.5 and r["lo"] < hi - 0.5]


def physical_signature(result, walls):
    """Identidade FISICA: (fiada, codigo, centro xy arredondado, comprimento)."""
    rows = []
    for ci, pieces in sorted(result["course_candidates"].items()):
        for c in pieces:
            o = c["origin_world"]
            rows.append("%d|%s|%.2f|%.2f|%.2f" % (ci, c["logical_code"], _cm(o.X), _cm(o.Y), c["length_cm"]))
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()


def _covered(rows, gap_cm=2.5):
    """Trechos cobertos da fileira (juntas de ate' `gap_cm` contam como cobertas)."""
    out = []
    for r in sorted(rows, key=lambda r: r["lo"]):
        if out and r["lo"] <= out[-1][1] + gap_cm:
            out[-1][1] = max(out[-1][1], r["hi"])
        else:
            out.append([r["lo"], r["hi"]])
    return [(round(a, 1), round(b, 1)) for a, b in out]


def _specials(result):
    return sum(1 for v in result["course_candidates"].values() for c in v
               if (sb.CATALOG.get(c["logical_code"]) or {}).get("is_compensator"))


def channel_count(result):
    return sum(1 for v in result["course_candidates"].values() for c in v if orf.is_channel_code(c["logical_code"]))


# --------------------------------------------------------------- fixtures
def free_wall():
    """Parede livre de 600 cm: porta [200,300] e janela [400,520] peitoril 100."""
    return [seg(0, 0, 600, 0)], [[(ft(200), ft(300), ft(0), ft(221)), (ft(400), ft(520), ft(100), ft(221))]]


def tee(sill_cm, jamb_t_cm=309.0):
    """T modular (principal de 604 cm, parede que chega em t=302) e janela com
    a jamba na FACE da parede que chega."""
    lines = [seg(-302, 0, 302, 0), seg(0, 0, 0, 298)]
    return lines, [[(ft(jamb_t_cm), ft(jamb_t_cm + 145.0), ft(sill_cm), ft(221))], []]


def passage():
    """Porta sem peitoril com as DUAS jambas no meio-B54 de dois T."""
    lines = [seg(0, 0, 800, 0), seg(200, 0, 200, 300), seg(500, 0, 500, 300)]
    return lines, [[(ft(227), ft(473), ft(0), ft(221))], [], []]


# ------------------------------------------------------------------ legado
def test_legacy_strategy_none_is_byte_identical_and_has_no_channel():
    lines, ops = free_wall()
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    plain = m.solve_building_blocks_all_courses(nodes, walls, e2n, ops, sb.CATALOG, 0.0, NUM_COURSES,
                                                variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    explicit, walls2, _n, _o = solve(lines, ops, strategy=None)
    assert physical_signature(plain, walls) == physical_signature(explicit, walls2)
    assert channel_count(explicit) == 0
    assert "opening_reinforcement" not in explicit


def test_unknown_strategy_is_rejected_never_silently_ignored():
    lines, ops = free_wall()
    with pytest.raises(ValueError):
        solve(lines, ops, strategy="LINTEL_COUNTERLINTEL")


# ----------------------------------------------------------- porta/janela
def test_door_gets_channel_course_on_head_and_nothing_else_changes_geometrically():
    lines, ops = free_wall()
    legacy, walls, _n, _o = solve(lines, ops, strategy=None)
    res, walls, _n, _o = solve(lines, ops)
    door_head_course = 11  # base 1 + 11*20 = 221 = topo da porta
    over = codes_over(res, walls, 0, door_head_course, 200, 300)
    assert over and all(orf.is_channel_code(c) for c in over)
    rec = res["opening_reinforcement"]["openings"][0]
    assert rec["above"]["status"] == "CHANNEL" and rec["below"] is None
    assert rec["above"]["support_l_cm"] >= 19.0 - 1e-6 and rec["above"]["support_r_cm"] >= 19.0 - 1e-6
    # ocupacao identica: a canaleta toma o lugar das pecas (mesmas pontas). Regra
    # do PLANEJADOR de reforco - medida com o arranjo das corridas (secoes 60-64,
    # que roda depois e troca juntas de proposito) desligado.
    from core.engine import b34_run_arrangement as _runs
    saved = _runs.B34_RUN_ARRANGEMENT_ENABLED
    # SECAO 68 desligada pelo MESMO motivo ja' escrito acima para as secoes
    # 60-64: ela e' uma mudanca de MODULACAO exclusiva do fluxo CHANNEL (o
    # reparo de abertura compoe a faixa jamba->ancora inteira em vez de aceitar
    # a primeira composicao que fecha), entao muda junta de proposito. O que
    # esta linha isola e' o PLANEJADOR de reforco: com as duas desligadas, a
    # canaleta tem de tomar o lugar das pecas sem mover nenhuma junta.
    saved_clean = m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED
    _runs.B34_RUN_ARRANGEMENT_ENABLED = False
    m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = False
    try:
        planned, _w, _n2, _o2 = solve(lines, ops)
    finally:
        _runs.B34_RUN_ARRANGEMENT_ENABLED = saved
        m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = saved_clean
    for ci in range(NUM_COURSES):
        a = [(round(r["lo"], 3), round(r["hi"], 3)) for r in strip(legacy, walls, 0, ci)]
        b = [(round(r["lo"], 3), round(r["hi"], 3)) for r in strip(planned, walls, 0, ci)]
        assert [x for x in b if x not in a] == []  # nenhuma junta nova
    # fluxo completo (com o arranjo): mesmos trechos cobertos em toda fiada (mesmas
    # pontas, nada entra no vao), auditoria limpa e sem mais especiais que o legado
    for ci in range(NUM_COURSES):
        assert _covered(strip(res, walls, 0, ci)) == _covered(strip(legacy, walls, 0, ci)), ci
    assert res["wall_bond_audits"][0].get("problems") in ([], None)
    assert _specials(res) <= _specials(legacy)


def test_window_gets_channel_on_head_and_one_course_under_sill():
    lines, ops = free_wall()
    res, walls, _n, _o = solve(lines, ops)
    rec = res["opening_reinforcement"]["openings"][1]
    assert rec["above"]["status"] == "CHANNEL" and rec["above"]["course_index"] == 11
    assert rec["below"]["status"] == "CHANNEL" and rec["below"]["course_index"] == 4  # topo 100 = peitoril
    assert all(orf.is_channel_code(c) for c in codes_over(res, walls, 0, 4, 400, 520))
    # uma fiada so' abaixo do peitoril
    assert not any(orf.is_channel_code(c) for c in codes_over(res, walls, 0, 3, 400, 520))
    counts = res["opening_reinforcement"]["validation"]["counts"]
    for key in ("MISSING_REQUIRED_CHANNEL", "EXTRA_CHANNEL", "CHANNEL_WRONG_COURSE",
                "CHANNEL_INVADES_OPENING", "CHANNEL_COLLISION"):
        assert counts[key] == 0, key


def test_top_course_above_window_is_not_a_second_channel():
    """Cinta de topo e' mecanismo separado: CHANNEL nao duplica o reforco."""
    lines, ops = free_wall()
    res, walls, _n, _o = solve(lines, ops)
    for ci in (12, 13):
        assert not any(orf.is_channel_code(c) for c in codes_over(res, walls, 0, ci, 0, 600))


def test_no_channel_piece_inside_any_active_opening_and_preflight_ok():
    lines, ops = free_wall()
    res, walls, _n, openings = solve(lines, ops)
    pf = m.controlled_beta_preflight(res, walls, openings, sb.CATALOG, 0.0)
    assert pf["ok"] and not pf["opening_violations"] and not pf["collisions"]


# ------------------------------------------------ corrida composta / cortes
def _row(code, lo, hi, reason="STANDARD_FILL"):
    x_dir = m.XYZ(1.0, 0.0, 0.0)
    cand = {"logical_code": code, "course": "A", "origin_world": m.XYZ(ft((lo + hi) / 2.0), 0.0, 0.0),
            "x_dir": x_dir, "y_dir": m.XYZ(0.0, 1.0, 0.0), "length_cm": hi - lo, "width_cm": 14.0,
            "cells_world": [], "placement_reason": reason, "wall_idx": 0}
    return {"cand": cand, "lo": lo, "hi": hi, "along": True, "eligible": True, "tie": False}


@pytest.mark.parametrize("sequence,expected", [
    ([("B19", 0, 19), ("C04", 20, 24)], [(orf.CHANNEL_U_CUT, 24.0)]),         # KV 24 humano
    ([("B19", 0, 19), ("C09", 20, 29)], [(orf.CHANNEL_U_CUT, 29.0)]),         # KV 29 humano
    ([("B34", 0, 34), ("C04", 35, 39)], [(orf.CHANNEL_U_39, 39.0)]),          # vira inteira
    ([("C09", 0, 9), ("C04", 10, 14)], [(orf.CHANNEL_U_CUT, 14.0)]),          # KV 14 humano
    ([("B39", 0, 39), ("C09", 40, 49), ("B39", 50, 89)],
     [(orf.CHANNEL_U_39, 39.0), (orf.CHANNEL_U_CUT, 9.0), (orf.CHANNEL_U_39, 39.0)]),  # KV 9 humano
])
def test_compensators_merge_into_length_cut_channels(sequence, expected):
    members = [_row(code, lo, hi) for code, lo, hi in sequence]
    policy = orf.channel_policy()
    groups = orf._group_run_members(members, policy)
    walls = [(seg(0, 0, 600, 0), ft(14.0), (False, False))]
    record = {"roles": [orf.ROLE_ABOVE_OPENING], "run_id": "r", "opening_indices": [0]}
    got = [orf._channel_candidate_from_group(g, walls, 0, record, policy) for g in groups]
    assert [(p["logical_code"], round(p["length_cm"], 3)) for p in got] == expected
    for piece in got:
        if piece["logical_code"] == orf.CHANNEL_U_CUT:
            assert piece["instance_length_cm"] == pytest.approx(piece["length_cm"])
            assert piece["reinforcement"]["cut"]["kind"] == "LENGTH_CUT"
            assert piece["reinforcement"]["cut"]["final_dimension_cm"] <= 39.0
        else:
            assert piece["instance_length_cm"] is None
        assert piece["mirrored"] is False


# --------------------------------------------------------- encontros (T)
def test_tee_jamb_on_incoming_face_channel_crosses_node_like_human():
    lines, ops = tee(sill_cm=80.0)
    res, walls, _n, _o = solve(lines, ops)
    rein = res["opening_reinforcement"]
    rec = rein["openings"][0]
    assert rec["above"]["status"] == "CHANNEL" and rec["below"]["status"] == "CHANNEL"
    assert rec["above"]["support_l_cm"] > 0 and rec["below"]["support_l_cm"] > 0
    assert sorted(c["course_index"] for c in rein["node_crossings"]) == [3, 11]
    for crossing in rein["node_crossings"]:
        assert (crossing["removed_code"], crossing["added_code"]) == ("B34", "B19")
        ci = crossing["course_index"]
        incoming = strip(res, walls, 1, ci)
        # a parede que chega nao entra mais na principal nesta fiada
        assert not any(r["lo"] < 14.0 - 0.5 and r["cand"]["wall_idx"] == 1 for r in incoming)
        assert any(r["cand"]["placement_reason"] == orf.CROSSING_ABUTMENT_REASON for r in incoming)
    assert rein["validation"]["counts"]["MISSING_REQUIRED_CHANNEL"] == 0
    assert res["wall_bond_audits"][0]["ok"]


def test_tee_crossing_disabled_leaves_no_bearing_finding_red_control():
    lines, ops = tee(sill_cm=80.0)
    res, _w, _n, _o = solve(lines, ops, policy={"cross_tee_when_support_at_most_cm": -1e9})
    rein = res["opening_reinforcement"]
    assert rein["node_crossings"] == []
    assert any(f["code"] == "CHANNEL_SUPPORT_LIMITED" and f["support_cm"] <= 0 for f in rein["findings"])


def test_tee_main_b54_over_span_is_split_into_two_channels_without_new_aligned_joint():
    lines, ops = tee(sill_cm=100.0)
    res, walls, _n, _o = solve(lines, ops)
    rein = res["opening_reinforcement"]
    rec = rein["openings"][0]
    assert rec["below"]["status"] == "CHANNEL"
    splits = [x for x in rein["tie_conversions"] if x["mode"] == "SPLIT"]
    assert len(splits) == 1 and splits[0]["code"] == "B54"
    ci = splits[0]["course_index"]
    joints = orf._row_joints_cm(strip(res, walls, 0, ci), 1.5)
    neighbours = []
    for cj in (ci - 1, ci + 1):
        neighbours += orf._row_joints_cm(strip(res, walls, 0, cj), 1.5)
    new_joint = splits[0]["parts_cm"][0][1] + 0.5
    assert min(abs(new_joint - j) for j in neighbours) >= 1.5
    assert any(abs(new_joint - j) < 1e-6 for j in joints)
    assert all(a["ok"] for a in res["wall_bond_audits"].values())


def test_tee_b54_split_disabled_is_reported_as_tie_over_span_red_control():
    lines, ops = tee(sill_cm=100.0)
    res, _w, _n, _o = solve(lines, ops, policy={"convert_blocking_along_ties": False})
    rein = res["opening_reinforcement"]
    assert any(f["code"] == "MISSING_REQUIRED_CHANNEL" and f["detail"] == "TIE_OVER_SPAN" for f in rein["findings"])


# ------------------------------------------------------------ excecoes
def test_passage_with_both_jambs_on_junction_ties_is_free_to_top():
    lines, ops = passage()
    legacy, walls, _n, _o = solve(lines, ops, strategy=None)
    res, walls, _n, _o = solve(lines, ops)
    rein = res["opening_reinforcement"]
    assert rein["openings"][0]["above"]["status"] == "FREE_TO_TOP"
    for ci in (11, 12, 13):
        assert codes_over(legacy, walls, 0, ci, 227, 473)  # legado fecha acima do vao
        assert codes_over(res, walls, 0, ci, 227, 473) == []
    assert channel_count(res) == 0
    assert rein["validation"]["counts"]["MISSING_REQUIRED_CHANNEL"] == 0


def test_passage_rule_disabled_plans_channel_instead_red_control():
    lines, ops = passage()
    res, _w, _n, _o = solve(lines, ops, policy={"free_to_top_tie_bounded_passages": False})
    assert res["opening_reinforcement"]["openings"][0]["above"]["status"] != "FREE_TO_TOP"


def test_window_with_sill_is_never_free_to_top():
    lines, ops = passage()
    ops = [[(ft(227), ft(473), ft(80), ft(221))], [], []]
    res, _w, _n, _o = solve(lines, ops)
    assert res["opening_reinforcement"]["openings"][0]["above"]["status"] != "FREE_TO_TOP"


def test_head_off_grid_is_reported_needs_rule_and_gets_no_channel():
    lines = [seg(0, 0, 600, 0)]
    ops = [[(ft(400), ft(461), ft(80), ft(171))]]  # BUTANTA K.2: topo em 171
    res, _w, _n, _o = solve(lines, ops)
    rein = res["opening_reinforcement"]
    assert rein["openings"][0]["above"]["status"] == "HEAD_OFF_GRID"
    assert any(f["code"] == "CHANNEL_HEAD_OFF_GRID" and f["classification"] == "NEEDS_RULE"
               for f in rein["findings"])
    assert rein["openings"][0]["below"]["status"] == "CHANNEL"


def test_head_one_joint_below_course_is_the_same_solution():
    """BUTANTA 6616547: vao ate' 220, canaleta na fiada de 221."""
    lines = [seg(0, 0, 600, 0)]
    res, _w, _n, _o = solve(lines, [[(ft(200), ft(300), ft(0), ft(220))]])
    assert res["opening_reinforcement"]["openings"][0]["above"]["course_index"] == 11


def test_opening_reaching_wall_top_gets_no_top_channel():
    lines = [seg(0, 0, 600, 0)]
    res, _w, _n, _o = solve(lines, [[(ft(200), ft(300), ft(0), ft(280))]])
    rec = res["opening_reinforcement"]["openings"][0]
    assert rec["above"]["status"] == "REACHES_WALL_TOP"
    assert channel_count(res) == 0


# ---------------------------------------------------------- validador
def test_independent_validator_catches_missing_wrong_course_and_invasion():
    lines, ops = free_wall()
    res, walls, _n, openings = solve(lines, ops)
    step, _e = m._course_height_ft(sb.CATALOG, res["candidates"])
    height = step - m._cm_to_ft(m.COURSE_JOINT_CM)

    def band(ci):
        return m._course_z_band(0.0, ci, step, height)

    cc = dict((ci, list(v)) for ci, v in res["course_candidates"].items())
    # (a) troca uma canaleta sobre a porta por bloco comum
    for i, c in enumerate(cc[11]):
        o = _cm(c["origin_world"].X)
        if orf.is_channel_code(c["logical_code"]) and 200 < o < 300:
            cc[11][i] = dict(c, logical_code="B39")
            break
    # (b) canaleta numa fiada sem demanda
    cc[7] = [dict(cc[7][0], logical_code=orf.CHANNEL_U_39)] + cc[7][1:]
    # (c) canaleta dentro da porta ativa na fiada 5
    inside = dict(cc[11][0], logical_code=orf.CHANNEL_U_39,
                  origin_world=m.XYZ(ft(250.0), cc[11][0]["origin_world"].Y, 0.0))
    cc[5] = cc[5] + [inside]
    val = orf.validate_channel_reinforcement(cc, walls, openings, band, NUM_COURSES, 0.0)
    assert val["counts"]["MISSING_REQUIRED_CHANNEL"] >= 1
    assert val["counts"]["CHANNEL_WRONG_COURSE"] >= 1
    assert val["counts"]["CHANNEL_INVADES_OPENING"] >= 1


# ----------------------------------------------- determinismo / idempotencia
def test_deterministic_and_endpoint_reversal_invariant():
    lines, ops = tee(sill_cm=80.0)
    a, wa, _n, _o = solve(lines, ops)
    b, wb, _n, _o = solve(lines, ops)
    assert physical_signature(a, wa) == physical_signature(b, wb)
    # Endpoints invertidos: o layout do preenchimento comum pode deslocar
    # (comportamento do motor, anterior ao CHANNEL); o que o reforco garante e'
    # a MESMA decisao fisica por abertura e a mesma validacao.
    lines, ops = free_wall()
    c, _wc, _n, _o = solve(lines, ops)
    d, _wd, _n, _o = solve(lines, ops, reverse=True)

    def decisions(res):
        out = []
        for rec in res["opening_reinforcement"]["openings"]:
            span = (round(min(rec["t_lo_cm"], 600 - rec["t_hi_cm"]), 1), round(rec["t_hi_cm"] - rec["t_lo_cm"], 1))
            out.append((span[1], rec["head_rel_cm"], rec["sill_rel_cm"],
                        (rec["above"] or {}).get("status"), (rec["above"] or {}).get("course_index"),
                        (rec["below"] or {}).get("status"), (rec["below"] or {}).get("course_index")))
        return sorted(out)

    assert decisions(c) == decisions(d)
    vc = c["opening_reinforcement"]["validation"]["counts"]
    vd = d["opening_reinforcement"]["validation"]["counts"]
    for key in ("MISSING_REQUIRED_CHANNEL", "EXTRA_CHANNEL", "CHANNEL_WRONG_COURSE", "CHANNEL_INVADES_OPENING",
                "CHANNEL_COLLISION", "channel_top_matched", "channel_bottom_matched"):
        assert vc[key] == vd[key], key


def test_deterministic_across_processes():
    code = ("import sys; sys.path.insert(0, %r); import test_channel_reinforcement as t; "
            "l, o = t.tee(80.0); r, w, n, oo = t.solve(l, o); print(t.physical_signature(r, w))") % HERE
    outs = set()
    for seed in ("0", "1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        outs.add(subprocess.check_output([sys.executable, "-c", code], env=env, cwd=HERE).decode().strip()[-64:])
    assert len(outs) == 1


def test_planning_is_idempotent_on_already_reinforced_courses():
    lines, ops = free_wall()
    res, walls, _n, openings = solve(lines, ops)
    step, _e = m._course_height_ft(sb.CATALOG, res["candidates"])
    height = step - m._cm_to_ft(m.COURSE_JOINT_CM)
    again = orf.plan_channel_reinforcement(res["course_candidates"], walls, openings,
                                           lambda ci: m._course_z_band(0.0, ci, step, height),
                                           NUM_COURSES, 0.0, catalog=sb.CATALOG)
    first = physical_signature(res, walls)
    second = physical_signature({"course_candidates": again["course_candidates"]}, walls)
    assert first == second


def test_shared_candidates_between_courses_are_not_mutated():
    lines, ops = free_wall()
    res, _w, _n, _o = solve(lines, ops)
    before = res["course_candidates_before_reinforcement"]
    assert not any(orf.is_channel_code(c["logical_code"]) for v in before.values() for c in v)


# ----------------------------------------------------------------- criacao
def _creation_catalog():
    catalog = dict((k, dict(v, symbol=SimpleNamespace(IsActive=True))) for k, v in sb.CATALOG.items())
    for code, entry in m.channel_logical_catalog().items():
        entry = dict(entry, symbol=SimpleNamespace(IsActive=True),
                     length_parameter="Comprimento_bloco" if code == orf.CHANNEL_U_CUT else None)
        catalog[code] = entry
    return catalog


def test_create_sets_instance_length_for_length_cut_channel():
    lines, ops = tee(sill_cm=80.0)
    res, walls, _n, _o = solve(lines, ops)
    doc = revit_stubs._StubDoc()
    out = m.create_building_blocks(doc, res["candidates"], _creation_catalog(), 0.0, SimpleNamespace(),
                                   NUM_COURSES, course_candidates=res["course_candidates"])
    assert not out["failures"]
    planned = sum(len(v) for v in res["course_candidates"].values())
    assert out["created_count"] == planned
    cuts = [c for v in res["course_candidates"].values() for c in v if c["logical_code"] == orf.CHANNEL_U_CUT]
    assert cuts
    written = [inst.params.get("Comprimento_bloco") for _p, _s, _r, inst in doc.Create.family_instances
               if "Comprimento_bloco" in inst.params]
    assert sorted(round(_cm(v), 3) for v in written) == sorted(round(c["instance_length_cm"], 3) for c in cuts)


def test_create_fails_loudly_when_length_parameter_cannot_be_written(monkeypatch):
    lines, ops = tee(sill_cm=80.0)
    res, _w, _n, _o = solve(lines, ops)
    monkeypatch.setattr(revit_stubs._FakeWritableParam, "Set", lambda self, value: False)
    doc = revit_stubs._StubDoc()
    out = m.create_building_blocks(doc, res["candidates"], _creation_catalog(), 0.0, SimpleNamespace(),
                                   NUM_COURSES, course_candidates=res["course_candidates"])
    cuts = sum(1 for v in res["course_candidates"].values() for c in v if c["logical_code"] == orf.CHANNEL_U_CUT)
    assert len([f for f in out["failures"] if "Comprimento_bloco" in f]) == cuts
    assert len(doc.deleted) == cuts


def test_channel_codes_never_enter_the_fill_catalog():
    assert not set(m.BLOCK_FAMILY_CATALOG_DEFINITIONS) & set(m.CHANNEL_FAMILY_CATALOG_DEFINITIONS)
    assert set(m.CHANNEL_FAMILY_CATALOG_DEFINITIONS) == set(orf.CHANNEL_LOGICAL_TYPES)
    assert m.CHANNEL_FAMILY_CATALOG_DEFINITIONS[orf.CHANNEL_U_CUT]["length_parameter"] == "Comprimento_bloco"


def test_module_is_ironpython27_compatible():
    path = os.path.join(os.path.dirname(HERE), "nuvem", "core", "engine", "opening_reinforcement.py")
    source = io.open(path, encoding="utf-8").read()
    assert not re.search(r"\bf\"|\bf'", source)
    assert "math.isfinite(" not in source
    assert "nonlocal" not in source


# ------------------------------------------ travessia de T: nao vaza (51.6)
def test_through_t_pattern_is_classified_specifically():
    lines, ops = tee(sill_cm=80.0)
    res, _w, _n, _o = solve(lines, ops)
    codes = [f["code"] for f in res["opening_reinforcement"]["findings"]]
    assert codes.count(orf.CHANNEL_THROUGH_T_PATTERN) == len(res["opening_reinforcement"]["node_crossings"]) == 2
    assert all(f["classification"] == "SUPPORTED_PATTERN" for f in res["opening_reinforcement"]["findings"]
               if f["code"] == orf.CHANNEL_THROUGH_T_PATTERN)


def test_same_geometry_without_channel_keeps_the_normal_t():
    lines, ops = tee(sill_cm=80.0)
    res, walls, _n, _o = solve(lines, ops, strategy=None)
    reasons = [c["placement_reason"] for v in res["course_candidates"].values() for c in v]
    assert orf.CROSSING_ABUTMENT_REASON not in reasons
    incoming = [r for ci in (3, 11) for r in strip(res, walls, 0, ci) if not r["along"]]
    assert incoming and all(r["cand"]["logical_code"] == "B34" for r in incoming)


def test_normal_t_away_from_opening_is_never_crossed():
    lines, ops = tee(sill_cm=80.0, jamb_t_cm=380.0)  # jamba a 78 cm do eixo do T
    res, _w, _n, _o = solve(lines, ops)
    assert res["opening_reinforcement"]["node_crossings"] == []
    assert orf.CHANNEL_THROUGH_T_PATTERN not in [f["code"] for f in res["opening_reinforcement"]["findings"]]


def test_abutment_label_without_channel_covering_node_is_still_audited():
    """A isencao HALF_BLOCK_NEAR_TIE exige a canaleta cobrindo o no': a
    etiqueta sozinha nao isenta (auditor global intacto)."""
    lines, ops = tee(sill_cm=80.0)
    res, walls, nodes, openings = solve(lines, ops)
    cc = dict((ci, list(v)) for ci, v in res["course_candidates"].items())
    for ci in (3, 11):
        cc[ci] = [dict(c, logical_code="B39") if orf.is_channel_code(c["logical_code"]) else c for c in cc[ci]]
    catalog = dict(sb.CATALOG)
    catalog.update(m.channel_logical_catalog())
    audits = m.audit_all_walls_bond_quality(walls, cc, catalog, NUM_COURSES, openings_per_wall=openings, nodes=nodes)
    problems = [str(p) for a in audits.values() for p in a["problems"]]
    assert any("HALF_BLOCK_NEAR_TIE" in p for p in problems)
