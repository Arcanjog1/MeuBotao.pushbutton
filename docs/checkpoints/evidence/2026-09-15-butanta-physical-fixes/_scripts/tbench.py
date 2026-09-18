# -*- coding: utf-8 -*-
"""Bancada OFFLINE que reproduz o fluxo REAL do botao ("Utilizar paredes
existentes") no TARGET butanta testes: as 46 Walls do Revit (eixo, espessura,
altura 340 -> 17 fiadas), as 44 aberturas lidas como o plugin le
(`_build_opening_dict`: centro da geometria = centro da bbox nestas familias,
largura/altura/peitoril por parametro), `assign_openings_to_walls` ANTES de
`extend_wall_ends_to_junctions` (mesma ordem de run_modulation_on_existing_walls),
estrategia CHANNEL."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("MB_REPO", r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton")
TESTS = os.path.join(REPO, "tests")
sys.path.insert(0, TESTS)
os.environ.setdefault("SCALE_BENCH_TESTS", TESTS)
import load_script  # noqa: E402

m = load_script.load()
import solver_bench as sb  # noqa: E402

CATALOG = sb.CATALOG
XYZ, Line = m.XYZ, m.Line
F2CM = 30.48
CM2F = 1.0 / F2CM


def load_target(path=None):
    path = path or os.path.join(HERE, "target_1pav.clean.json")
    return json.load(open(path, encoding="utf-8"))


def opening_dicts(doc):
    ops = []
    for o in doc["openings"]:
        bb = o["bb"]
        cx, cy = (bb[0] + bb[3]) / 2.0 * CM2F, (bb[1] + bb[4]) / 2.0 * CM2F
        sill = (o.get("Peitoril") or 0.0) * CM2F
        ops.append({
            "center_xy": XYZ(cx, cy, 0.0), "center_source": "geometria",
            "insertion_xy": XYZ(o["o"][0] * CM2F, o["o"][1] * CM2F, 0.0),
            "bbox_center_xy": XYZ(cx, cy, 0.0), "hand_xy": XYZ(o["bx"][0], o["bx"][1], 0.0),
            "width_ft": o["Largura_abertura"] * CM2F, "sill_z_abs": sill,
            "head_z_abs": sill + o["Altura_abertura"] * CM2F,
            "element_id": str(o["id"]), "element_id_obj": o["id"],
        })
    return ops


def build(doc, wall_ids=None, order=None):
    ws = [w for w in doc["walls"] if wall_ids is None or w["id"] in wall_ids]
    if order is not None:
        ws = [ws[i] for i in order]
    walls_to_create = []
    ids = []
    for w in ws:
        line = Line.CreateBound(XYZ(w["p0"][0] * CM2F, w["p0"][1] * CM2F, 0.0),
                                XYZ(w["p1"][0] * CM2F, w["p1"][1] * CM2F, 0.0))
        walls_to_create.append((line, w["width"] * CM2F, (False, False)))
        ids.append(w["id"])
    ops = opening_dicts(doc)
    diag = {"clamped_opening_count": 0, "opening_center_gap_max_ft": 0.0,
            "opening_off_center_count": 0, "assignments": [], "unassigned_openings": []}
    openings_per_wall = m.assign_openings_to_walls(walls_to_create, ops, diag)
    original_axes = list(walls_to_create)
    walls, jmap = m.extend_wall_ends_to_junctions(walls_to_create, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jmap)
    return dict(walls=walls, nodes=nodes, e2n=e2n, openings_per_wall=openings_per_wall, ids=ids,
                original_axes=original_axes, ops=ops, diag=diag)


def num_courses(height_cm=340.0):
    return int(math.floor(height_cm / 20.0 + 1e-9))


def solve(ctx, strategy="CHANNEL", courses=17, **kw):
    res = m.solve_building_blocks_all_courses(
        ctx["nodes"], ctx["walls"], ctx["e2n"], ctx["openings_per_wall"], CATALOG, 0.0, courses,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
        opening_reinforcement_strategy=strategy, **kw)
    res["num_courses"] = courses
    return res


def pieces_world(ctx, res):
    """[(wall_id, course, code, lo_cm, hi_cm)] pelo eixo ESTENDIDO."""
    out = []
    walls = ctx["walls"]
    for ci, cands in (res.get("course_candidates") or {}).items():
        for c in cands:
            wi = c.get("wall_idx")
            if wi is None:
                continue
            p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, wi)
            lo, hi = m._candidate_extent_on_wall_axis(c, p0, d)
            out.append((ctx["ids"][wi], ci, c["logical_code"], lo, hi, c))
    return out


if __name__ == "__main__":
    import time
    doc = load_target()
    ctx = build(doc)
    t0 = time.time()
    res = solve(ctx)
    n = sum(len(v) for v in res["course_candidates"].values())
    print("walls=%d openings=%d pecas=%d em %.1fs" % (len(ctx["walls"]), sum(len(v) for v in ctx["openings_per_wall"]), n, time.time() - t0))
