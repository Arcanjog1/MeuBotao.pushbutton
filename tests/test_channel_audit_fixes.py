# -*- coding: utf-8 -*-
"""Correcoes da auditoria independente do PR #40 (2026-09-14).

FREE_TO_TOP sem abrir alem das jambas, validador de abertura real x jambas,
6627438 (paridade do no' T diante da canaleta), determinismo sem id()/ordem de
entrada, result["candidates"] como fonte unica e legado igual com as regras
30.8 / tolerancia de pastilha desligadas por default. Fixtures sinteticas.

    python3 -m pytest tests/test_channel_audit_fixes.py -q
"""
import hashlib
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg, solve, strip = tcr.m, tcr.ft, tcr.seg, tcr.solve, tcr.strip
NUM_COURSES = tcr.NUM_COURSES

from core.engine import continuous_modulation as cm  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402


def _band(res):
    step, _e = m._course_height_ft(tcr.sb.CATALOG, None)
    height = step - m._cm_to_ft(m.COURSE_JOINT_CM)
    return lambda ci: m._course_z_band(0.0, ci, step, height)


def _passage(jamb_lo, jamb_hi, nodes=(200.0, 500.0)):
    lines = [seg(0, 0, 800, 0), seg(nodes[0], 0, nodes[0], 300), seg(nodes[1], 0, nodes[1], 300)]
    return lines, [[(ft(jamb_lo), ft(jamb_hi), ft(0), ft(221))], [], []]


def _crossing(rows, t):
    return [r for r in rows if r["lo"] < t - 0.5 and r["hi"] > t + 0.5]


# ------------------------------------------------------------ defaults
def test_rule_30_8_and_jamb_noise_tolerance_are_off_by_default():
    assert ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED is False
    assert cm.JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED is False


# --------------------------------------------------------- FREE_TO_TOP
@pytest.mark.parametrize("jamb_lo,jamb_hi", [(227.0, 473.0), (214.0, 486.0), (221.0, 480.0), (228.0, 472.0),
                                             (224.5, 476.0)])
def test_free_to_top_opens_exactly_the_opening_and_keeps_masonry_outside_the_jambs(jamb_lo, jamb_hi):
    lines, ops = _passage(jamb_lo, jamb_hi)
    legacy, walls, _n, _o = solve(lines, ops, strategy=None)
    res, walls, _n, openings = solve(lines, ops)
    rein = res["opening_reinforcement"]
    assert rein["openings"][0]["above"]["status"] == "FREE_TO_TOP"
    from_ci = rein["free_to_top"][0]["from_course"]
    crossed_in_legacy = {"L": False, "R": False}
    for ci in range(from_ci, NUM_COURSES):
        rows = strip(res, walls, 0, ci)
        legacy_rows = strip(legacy, walls, 0, ci)
        crossed_in_legacy["L"] |= bool(_crossing(legacy_rows, jamb_lo))
        crossed_in_legacy["R"] |= bool(_crossing(legacy_rows, jamb_hi))
        # (1) regiao interna do vao vazia
        assert not [r for r in rows if r["hi"] > jamb_lo + 0.5 and r["lo"] < jamb_hi - 0.5], ci
        # (2) nenhuma peca atravessando a jamba
        assert not _crossing(rows, jamb_lo) and not _crossing(rows, jamb_hi), ci
        # (3) alvenaria externa encosta na jamba igual as fiadas da porta (mesma paridade)
        ref = strip(res, walls, 0, from_ci - 2 + (ci - from_ci) % 2)
        for t, side in ((jamb_lo, -1), (jamb_hi, 1)):
            ref_gap = orf._jamb_outside_gap_cm(ref, t, side)
            assert orf._jamb_outside_gap_cm(rows, t, side) <= ref_gap + 0.5, (ci, side)
            if ref_gap <= 1.5:  # onde a altura da porta fecha na jamba, acima tambem fecha
                assert orf._jamb_outside_gap_cm(rows, t, side) <= 1.5, (ci, side)
    counts = rein["validation"]["counts"]
    for key in ("CHANNEL_OPENING_OVERCUT", "CHANNEL_FREE_TO_TOP_NOT_OPEN", "CHANNEL_ORPHAN_PIECE",
                "MISSING_REQUIRED_CHANNEL", "CHANNEL_INVADES_OPENING", "CHANNEL_COLLISION"):
        assert counts[key] == 0, key
    pf = m.controlled_beta_preflight(res, walls, openings, tcr.sb.CATALOG, 0.0)
    assert pf["ok"] and not pf["opening_violations"] and not pf["collisions"]
    if (jamb_lo, jamb_hi) == (227.0, 473.0):
        # caso auditado: no legado ha' peca atravessando as DUAS jambas acima do vao
        assert crossed_in_legacy["L"] and crossed_in_legacy["R"]


def test_planner_without_presolve_never_removes_pieces_red_control():
    """O P0: o planejador chamado direto (sem o vao estendido no solve) nao
    remove nada - reporta FREE_TO_TOP_NOT_PRESOLVED."""
    lines, ops = _passage(227.0, 473.0)
    legacy, walls, nodes, openings = solve(lines, ops, strategy=None)
    plan = orf.plan_channel_reinforcement(legacy["course_candidates"], walls, openings, _band(legacy), NUM_COURSES,
                                          0.0, nodes=nodes, catalog=tcr.sb.CATALOG)
    assert plan["openings"][0]["above"]["status"] == "FREE_TO_TOP_NOT_PRESOLVED"
    assert any(f["code"] == "FREE_TO_TOP_NOT_PRESOLVED" for f in plan["findings"])
    for ci in range(NUM_COURSES):
        assert len(plan["course_candidates"][ci]) == len(legacy["course_candidates"][ci])


def test_validator_detects_opening_wider_than_the_jambs_orphan_and_leftover():
    """Reproduz o defeito antigo (peca que cruza/encosta a jamba removida) e
    confirma que o validador acusa - nao basta nao haver peca DENTRO do vao."""
    lines, ops = _passage(227.0, 473.0)
    res, walls, _n, openings = solve(lines, ops)
    ftt = res["opening_reinforcement"]["free_to_top"]
    from_ci = ftt[0]["from_course"]
    band = _band(res)
    cc = dict((ci, list(v)) for ci, v in res["course_candidates"].items())
    rows = strip(res, walls, 0, from_ci)
    left = max((r for r in rows if r["hi"] <= 227.5 and r["along"]), key=lambda r: r["hi"])
    cc[from_ci] = [c for c in cc[from_ci] if c is not left["cand"]]
    val = orf.validate_channel_reinforcement(cc, walls, openings, band, NUM_COURSES, 0.0, free_to_top=ftt)
    assert val["counts"]["CHANNEL_OPENING_OVERCUT"] >= 1
    # compensador solto junto a' jamba + peca esquecida dentro do vao
    template = left["cand"]
    orphan = dict(template, logical_code="C04", length_cm=4.0,
                  origin_world=m.XYZ(ft(222.0), template["origin_world"].Y, template["origin_world"].Z))
    leftover = dict(template, origin_world=m.XYZ(ft(350.0), template["origin_world"].Y, template["origin_world"].Z))
    cc[from_ci + 1] = list(cc[from_ci + 1]) + [orphan, leftover]
    val = orf.validate_channel_reinforcement(cc, walls, openings, band, NUM_COURSES, 0.0, free_to_top=ftt)
    assert val["counts"]["CHANNEL_ORPHAN_PIECE"] >= 1
    assert val["counts"]["CHANNEL_FREE_TO_TOP_NOT_OPEN"] >= 1


def test_validator_detects_overcut_of_a_regular_opening_against_reference():
    lines, ops = tcr.free_wall()
    res, walls, _n, openings = solve(lines, ops)
    band = _band(res)
    ref = res["course_candidates_before_reinforcement"]
    cc = dict((ci, list(v)) for ci, v in res["course_candidates"].items())
    rows = strip(res, walls, 0, 5)
    neighbour = max((r for r in rows if r["hi"] <= 200.5 and r["along"]), key=lambda r: r["hi"])
    cc[5] = [c for c in cc[5] if c is not neighbour["cand"]]
    clean = orf.validate_channel_reinforcement(res["course_candidates"], walls, openings, band, NUM_COURSES, 0.0,
                                               reference_course_candidates=ref)
    broken = orf.validate_channel_reinforcement(cc, walls, openings, band, NUM_COURSES, 0.0,
                                                reference_course_candidates=ref)
    assert clean["counts"]["CHANNEL_OPENING_OVERCUT"] == 0
    assert broken["counts"]["CHANNEL_OPENING_OVERCUT"] >= 1


# ---------------------------------------------------------- 6627438
def _door_next_to_tee(jamb_lo, jamb_hi):
    return [seg(0, 0, 584, 0), seg(382, 0, 382, 300)], [[(ft(jamb_lo), ft(jamb_hi), ft(0), ft(221))], []]


@pytest.mark.parametrize("jamb_lo,jamb_hi", [(269.0, 370.0), (269.022, 370.012)])
def test_red_engine_parity_leaves_4cm_before_incoming_tie(monkeypatch, jamb_lo, jamb_hi):
    """RED: sem a tentativa de paridade, com a pastilha real de 4 cm (ou a de
    3,9989 cm com a tolerancia de ruido ligada) a canaleta para com ~4 cm
    diante da amarracao transversal do T - a conversao ao longo (< 9 cm) nao
    se aplica porque nessa fiada a peca do no' e' da parede que chega."""
    monkeypatch.setattr(m, "_channel_tie_parity_trials",
                        lambda *a, **k: {"changed": False, "accepted": [], "rejected": [], "final_result": a[6]})
    monkeypatch.setattr(cm, "JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED", True)
    lines, ops = _door_next_to_tee(jamb_lo, jamb_hi)
    res, _w, _n, _o = solve(lines, ops)
    above = res["opening_reinforcement"]["openings"][0]["above"]
    assert above["support_r_cm"] < 9.0 and above["limited_r"] == "JUNCTION_TIE"
    assert above["blocker_r"]["along"] is False
    limited = [f for f in res["opening_reinforcement"]["findings"] if f["code"] == "CHANNEL_SUPPORT_LIMITED"]
    assert limited and all(f["classification"] != "VALID_ALTERNATIVE" for f in limited)


@pytest.mark.parametrize("tolerance", [False, True])
@pytest.mark.parametrize("jamb_lo,jamb_hi", [(269.0, 370.0), (269.022, 370.012)])
def test_green_parity_trial_gives_along_tie_support_like_human(monkeypatch, tolerance, jamb_lo, jamb_hi):
    """ATUALIZADO PELA REGRA 75 (2026-09-18). O desfecho "como o humano"
    (apoio de 19 cm) dependia de o trial de paridade poder DIVIDIR o B54 do
    no' em canaletas - que e' exatamente o que a regra 75 proibe. Sem essa
    valvula o trial que poe a amarracao sobre a corrida e' recusado pelo
    gate de erros, o apoio fica limitado e o conflito e' CLASSIFICADO. A
    mecanica antiga continua testada logo abaixo, sob override explicito."""
    monkeypatch.setattr(cm, "JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED", tolerance)
    lines, ops = _door_next_to_tee(jamb_lo, jamb_hi)
    res, walls, _n, openings = solve(lines, ops)
    rein = res["opening_reinforcement"]
    above = rein["openings"][0]["above"]
    assert rein["node_crossings"] == [] and rein["tie_conversions"] == []
    assert res["channel_as_junction_bond"] == []
    assert above["support_r_cm"] < 19.0 - 1e-6
    assert any(f["code"] == "CHANNEL_SUPPORT_LIMITED" for f in rein["findings"])
    for key in ("CHANNEL_OPENING_OVERCUT", "CHANNEL_INVADES_OPENING", "CHANNEL_COLLISION"):
        assert rein["validation"]["counts"][key] == 0


@pytest.mark.parametrize("jamb_lo,jamb_hi", [(269.0, 370.0)])
def test_green_parity_com_override_reproduz_o_humano_e_o_gate_acusa(monkeypatch, jamb_lo, jamb_hi):
    """MUTANTE da regra 75 (conversao ao longo no trial): sob override a
    mecanica antiga volta a dar o apoio de 19 cm do humano - e o hard gate
    CHANNEL_AS_JUNCTION_BOND ACUSA a amarracao convertida."""
    monkeypatch.setattr(cm, "JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED", False)
    lines, ops = _door_next_to_tee(jamb_lo, jamb_hi)
    res, walls, _n, openings = solve(lines, ops, policy={"convert_blocking_along_ties": True})
    rein = res["opening_reinforcement"]
    above = rein["openings"][0]["above"]
    assert above["support_r_cm"] >= 19.0 - 1e-6 and above["bearing_r_cm"] >= 19.0 - 1e-6
    assert res["channel_tie_parity_trials"]["accepted"]
    assert res["channel_as_junction_bond"], "o gate tem de acusar a conversao"


def test_parity_trial_never_runs_for_legacy_strategy():
    lines, ops = _door_next_to_tee(269.0, 370.0)
    res, _w, _n, _o = solve(lines, ops, strategy=None)
    assert "channel_tie_parity_trials" not in res


def test_human_like_face_crossing_is_not_a_parity_candidate():
    """Jamba na face da parede que chega: nem paridade, nem travessia (a 51.6
    esta suspensa pela REGRA 75) - o conflito fica classificado."""
    lines, ops = tcr.tee(sill_cm=80.0)
    res, _w, _n, _o = solve(lines, ops)
    assert res["opening_reinforcement"]["node_crossings"] == []
    assert res["channel_tie_parity_trials"]["accepted"] == []
    assert res["channel_as_junction_bond"] == []


# ------------------------------------------------------- determinismo
def _plan_signature(plan):
    rows = []
    for ci in sorted(plan["course_candidates"]):
        for c in plan["course_candidates"][ci]:
            rows.append("%d|%s" % (ci, orf._physical_key(c)))
    runs = sorted((r["run_id"], tuple((p["code"], p["lo_cm"], p["hi_cm"]) for p in r["pieces"])) for r in plan["runs"])
    return hashlib.sha256(("\n".join(sorted(rows)) + repr(runs)).encode("utf-8")).hexdigest()


@pytest.mark.parametrize("fixture", ["tee", "free_wall", "passage"])
def test_plan_is_independent_of_input_piece_order(fixture):
    if fixture == "tee":
        lines, ops = tcr.tee(sill_cm=100.0)
    elif fixture == "free_wall":
        lines, ops = tcr.free_wall()
    else:
        lines, ops = _passage(227.0, 473.0)
    legacy, walls, nodes, openings = solve(lines, ops, strategy=None)
    band = _band(legacy)
    sigs = set()
    for order in ("asis", "reversed", "rotated"):
        cc = {}
        for ci, pieces in legacy["course_candidates"].items():
            pieces = list(pieces)
            if order == "reversed":
                pieces.reverse()
            elif order == "rotated" and pieces:
                k = len(pieces) // 3
                pieces = pieces[k:] + pieces[:k]
            cc[ci] = pieces
        plan = orf.plan_channel_reinforcement(cc, walls, openings, band, NUM_COURSES, 0.0, nodes=nodes,
                                              catalog=tcr.sb.CATALOG, free_to_top=[])
        sigs.add(_plan_signature(plan))
    assert len(sigs) == 1


def test_planner_source_has_no_identity_keys():
    import inspect
    src = inspect.getsource(orf.plan_channel_reinforcement) + inspect.getsource(orf.validate_channel_reinforcement)
    assert "id(" not in src.replace("_idx(", "").replace("valid(", "")


# ------------------------------------------------ result["candidates"]
@pytest.mark.parametrize("fixture", ["tee", "free_wall", "passage"])
def test_result_candidates_equal_flatten_of_course_candidates_after_channel(fixture):
    if fixture == "tee":
        lines, ops = tcr.tee(sill_cm=80.0)
    elif fixture == "free_wall":
        lines, ops = tcr.free_wall()
    else:
        lines, ops = _passage(227.0, 473.0)
    res, _w, _n, _o = solve(lines, ops)
    flat_keys = set(orf._physical_key(c) for v in res["course_candidates"].values() for c in v)
    cand_keys = [orf._physical_key(c) for c in res["candidates"]]
    assert set(cand_keys) == flat_keys and len(cand_keys) == len(set(cand_keys))
    channel_codes = set(c["logical_code"] for v in res["course_candidates"].values() for c in v
                        if orf.is_channel_code(c["logical_code"]))
    assert channel_codes <= set(c["logical_code"] for c in res["candidates"])
    assert all(0 <= i < len(res["candidates"]) and 0 <= j < len(res["candidates"]) for i, j in res["collisions"])
    assert "candidates_before_reinforcement" in res


def test_legacy_candidates_are_untouched():
    lines, ops = tcr.free_wall()
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    plain = m.solve_building_blocks_all_courses(nodes, walls, e2n, ops, tcr.sb.CATALOG, 0.0, NUM_COURSES,
                                                variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    explicit, _w, _n, _o = solve(lines, ops, strategy=None)
    assert [orf._physical_key(c) for c in plain["candidates"]] == [orf._physical_key(c) for c in explicit["candidates"]]
    assert "candidates_before_reinforcement" not in explicit


# ------------------------------------------ passagem livre CONTINUA (face a face)
def _double_passage(left_node=200.0, pier_node=450.0, right_node=700.0, gap=27.0, head2=221.0, pier_cross=False):
    """Parede principal com tres T (paredes que chegam de um lado so') e duas
    portas sem peitoril encadeadas pelo pilar do T do meio - padrao PAR28."""
    lines = [seg(0, 0, 900, 0), seg(left_node, 0, left_node, 273), seg(right_node, 0, right_node, 273)]
    if pier_cross:
        lines.append(seg(pier_node, -273, pier_node, 273))
    else:
        lines.append(seg(pier_node, 0, pier_node, 273))
    ops = [[(ft(left_node + gap), ft(pier_node - gap), ft(0), ft(221)),
            (ft(pier_node + gap), ft(right_node - gap), ft(0), ft(head2))], [], [], []]
    return lines, ops


@pytest.mark.parametrize("gap,pier", [(27.0, 450.0), (25.0, 450.0), (27.0, 430.0)])
def test_continuous_passage_opens_from_node_face_to_node_face(gap, pier):
    lines, ops = _double_passage(pier_node=pier, gap=gap)
    res, walls, nodes, openings = solve(lines, ops)
    rein = res["opening_reinforcement"]
    assert len(rein["continuous_passages"]) == 1
    passage = rein["continuous_passages"][0]
    lo, hi = passage["region_cm"]
    assert abs(lo - 207.0) < 0.6 and abs(hi - 693.0) < 0.6
    assert [r["above"]["status"] for r in rein["openings"]] == ["FREE_TO_TOP", "FREE_TO_TOP"]
    incoming = passage["inner"][0]["incoming_wall_idx"]
    for ci in range(passage["from_course"], NUM_COURSES):
        pieces = res["course_candidates"][ci]
        # (1) regiao interna vazia (qualquer parede, pela geometria real)
        assert orf._pieces_in_wall_region(pieces, walls, 0, lo, hi) == [], ci
        # (2) nos externos continuam amarrados ate' a face
        rows = strip(res, walls, 0, ci)
        assert orf._jamb_outside_gap_cm(rows, lo, -1) <= 1.5 and orf._jamb_outside_gap_cm(rows, hi, 1) <= 1.5, ci
        # (3) a parede que chega no no' do pilar termina na face da principal
        a, b = passage["inner"][0]["incoming_region_cm"]
        assert strip(res, walls, incoming, ci), ci
        assert orf._pieces_in_wall_region(pieces, walls, incoming, a, b) == [], ci
        assert orf._jamb_outside_gap_cm(strip(res, walls, incoming, ci), b if a <= 0.5 else a,
                                        1 if a <= 0.5 else -1) <= 1.5, ci
    # abaixo do topo: as duas portas e o pilar existem como antes
    below = strip(res, walls, 0, passage["from_course"] - 1)
    assert [r for r in below if pier - 20 < (r["lo"] + r["hi"]) / 2.0 < pier + 20]
    counts = rein["validation"]["counts"]
    for key in ("CHANNEL_FREE_TO_TOP_NOT_OPEN", "CHANNEL_OPENING_OVERCUT", "CHANNEL_ORPHAN_PIECE",
                "CHANNEL_INVADES_OPENING", "CHANNEL_COLLISION", "MISSING_REQUIRED_CHANNEL"):
        assert counts[key] == 0, key
    pf = m.controlled_beta_preflight(res, walls, openings, tcr.sb.CATALOG, 0.0)
    assert pf["ok"] and not pf["opening_violations"] and not pf["collisions"]
    assert not [p for a in res["wall_bond_audits"].values() for p in a["problems"]
                if "CONTINUOUS_VERTICAL_JOINT" in str(p)]


def test_single_free_passage_is_not_continuous_and_opens_only_the_opening():
    lines, ops = _passage(227.0, 473.0)
    res, walls, _n, _o = solve(lines, ops)
    assert res["opening_reinforcement"]["continuous_passages"] == []
    from_ci = res["opening_reinforcement"]["free_to_top"][0]["from_course"]
    assert codes_over_any(res, walls, from_ci, 200.0, 227.0)


def codes_over_any(res, walls, ci, lo, hi):
    return [r["cand"]["logical_code"] for r in strip(res, walls, 0, ci) if r["hi"] > lo + 0.5 and r["lo"] < hi - 0.5]


@pytest.mark.parametrize("variant", ["pier_is_cross", "different_head", "pier_too_wide"])
def test_non_equivalent_geometry_is_not_a_continuous_passage(variant):
    if variant == "pier_is_cross":
        lines, ops = _double_passage(pier_cross=True)
    elif variant == "different_head":
        lines, ops = _double_passage(head2=201.0)
    else:
        lines, ops = _double_passage(gap=27.0)
        ops = [[ops[0][0], (ft(450.0 + 40.0), ft(673.0), ft(0), ft(221))], [], [], []]
    res, _w, _n, _o = solve(lines, ops)
    assert res["opening_reinforcement"]["continuous_passages"] == []


def test_validator_red_leftover_in_passage_and_incoming_wall_intrusion():
    lines, ops = _double_passage()
    res, walls, nodes, openings = solve(lines, ops)
    rein = res["opening_reinforcement"]
    passage = rein["continuous_passages"][0]
    ci = passage["from_course"]
    band = _band(res)
    cc = dict((k, list(v)) for k, v in res["course_candidates"].items())
    template = strip(res, walls, 0, ci - 1)[0]["cand"]
    leftover = dict(template, logical_code="B39", length_cm=39.0,
                    origin_world=m.XYZ(ft(450.0), template["origin_world"].Y, template["origin_world"].Z))
    cc[ci] = cc[ci] + [leftover]
    val = orf.validate_channel_reinforcement(cc, walls, openings, band, NUM_COURSES, 0.0,
                                             free_to_top=rein["free_to_top"], nodes=nodes)
    assert val["counts"]["CHANNEL_FREE_TO_TOP_NOT_OPEN"] >= 1
    inc = passage["inner"][0]["incoming_wall_idx"]
    inc_template = [r for r in strip(res, walls, inc, ci) if r["along"]][0]["cand"]
    p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, inc)
    a, b = passage["inner"][0]["incoming_region_cm"]
    intrusion = dict(inc_template, logical_code="C09", length_cm=9.0,
                     origin_world=m.XYZ((p0 + d * ft((a + b) / 2.0)).X, (p0 + d * ft((a + b) / 2.0)).Y,
                                        inc_template["origin_world"].Z))
    cc2 = dict((k, list(v)) for k, v in res["course_candidates"].items())
    cc2[ci] = cc2[ci] + [intrusion]
    val = orf.validate_channel_reinforcement(cc2, walls, openings, band, NUM_COURSES, 0.0,
                                             free_to_top=rein["free_to_top"], nodes=nodes)
    assert val["counts"]["CHANNEL_FREE_TO_TOP_NOT_OPEN"] >= 1


# ------------------------------------------ desempenho: memo/cache sem mudar nada
def _full_signature(res):
    import json
    rows = sorted("%d|%s" % (ci, orf._physical_key(c)) for ci, v in res["course_candidates"].items() for c in v)
    rein = res["opening_reinforcement"]
    extra = json.dumps({"val": rein["validation"], "openings": rein["openings"], "runs": rein["runs"],
                        "findings": rein["findings"], "passages": rein.get("continuous_passages"),
                        "trials": [(res.get("channel_tie_parity_trials") or {}).get("accepted"),
                                   (res.get("channel_tie_parity_trials") or {}).get("rejected")],
                        "nonmod": res["non_modular"], "collisions": res["collisions"],
                        "candidates": [orf._physical_key(c) for c in res["candidates"]],
                        "bond": sorted((k, a["ok"], a["problems"]) for k, a in res["wall_bond_audits"].items())},
                       sort_keys=True, default=str)
    return hashlib.sha256(("\n".join(rows) + extra).encode("utf-8")).hexdigest()


@pytest.mark.parametrize("fixture", ["tee80", "tee100", "free_wall", "passage", "double_passage", "door_next_to_tee"])
def test_performance_memo_and_caches_give_identical_result(fixture):
    if fixture == "tee80":
        lines, ops = tcr.tee(sill_cm=80.0)
    elif fixture == "tee100":
        lines, ops = tcr.tee(sill_cm=100.0)
    elif fixture == "free_wall":
        lines, ops = tcr.free_wall()
    elif fixture == "passage":
        lines, ops = _passage(227.0, 473.0)
    elif fixture == "double_passage":
        lines, ops = _double_passage()
    else:
        lines, ops = _door_next_to_tee(269.0, 370.0)
    sigs = []
    for fn in (m.solve_building_blocks_all_courses, m._solve_building_blocks_all_courses_impl):
        walls = [(line, ft(14.0), (False, False)) for line in lines]
        walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
        nodes, e2n = m.build_wall_graph(walls, jm)
        res = fn(nodes, walls, e2n, ops, tcr.sb.CATALOG, 0.0, NUM_COURSES,
                 variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE, opening_reinforcement_strategy=tcr.CHANNEL)
        assert "_channel_metrics_cache" not in res
        sigs.append(_full_signature(res))
    assert sigs[0] == sigs[1]
    assert ws.WALL_FILL_MEMO is None  # memo nunca vaza para fora da chamada


def test_memo_key_has_no_identity_or_dict_order_dependency():
    import inspect
    src = inspect.getsource(ws._wall_fill_memo_key)
    assert "id(" not in src and "sorted(" in src
