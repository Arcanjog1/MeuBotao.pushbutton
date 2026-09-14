# -*- coding: utf-8 -*-
"""Bancada offline CHANNEL - BUTANTA 1o PAV (34 paredes de alvenaria).

Carrega o motor do repositorio com os dubles de tests/revit_stubs.py, os eixos
das Walls do projeto de teste (evidencia 2026-09-10) e as aberturas humanas
(vao REAL `span_along_axis_cm`). Nada aqui e' norma; so' monta a entrada.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TESTS = os.path.join(ROOT, "tests")
if TESTS not in sys.path:
    sys.path.insert(0, TESTS)
os.environ.setdefault("SCALE_BENCH_TESTS", TESTS)

import load_script  # noqa: E402

m = load_script.load()
import solver_bench as sb  # noqa: E402

CATALOG = sb.CATALOG
XYZ, Line = m.XYZ, m.Line
F2CM = 30.48
CM2F = 1.0 / 30.48
EV = os.path.join(ROOT, "docs", "checkpoints", "evidence")
NUM_COURSES = 14


def load_inputs(min_human_pieces=20):
    walls_json = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json"), encoding="utf-8"))["walls"]
    human = json.load(open(os.path.join(EV, "2026-09-10-butanta-human-sequences.json"), encoding="utf-8"))
    ops_all = json.load(open(os.path.join(ROOT, "docs", "revit_reference_extraction", "butanta-r08-lt",
                                          "02_openings.json"), encoding="utf-8"))["openings"]
    hcount = {w["id"]: sum(len(human["per_wall"].get(str(w["id"]), {}).get(str(c), [])) for c in range(13))
              for w in walls_json}
    masonry = [w for w in walls_json if hcount[w["id"]] >= min_human_pieces]
    return masonry, [o for o in ops_all if o["level_datum_z_cm"] == 0.0]


def build(masonry, ops, wall_filter=None):
    """Monta walls/nodes/e2n/openings_per_wall. `wall_filter(ids)` limita o recorte."""
    sel = [w for w in masonry if wall_filter is None or wall_filter(w["id"])]
    axes, ids = [], []
    for w in sel:
        axes.append((Line.CreateBound(XYZ(*[float(v) for v in w["p0"]]), XYZ(*[float(v) for v in w["p1"]])),
                     14.0 / 100.0 * m.FEET_PER_METER, (False, False)))
        ids.append(w["id"])
    walls, jmap = m.extend_wall_ends_to_junctions(list(axes), m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jmap)
    openings_per_wall = [[] for _ in walls]
    opening_ids = [[] for _ in walls]
    for o in ops:
        best = None
        horiz = (o["axis"] == "X")
        for wi in range(len(walls)):
            p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, wi)
            if (abs(d.Y) < 0.5) != horiz:
                continue
            lat = abs((o["x_cm"] * CM2F - p0.X) * d.Y - (o["y_cm"] * CM2F - p0.Y) * d.X) * F2CM
            s0, s1 = o["span_along_axis_cm"]
            if horiz:
                ts = sorted(((s * CM2F - p0.X) * d.X + (o["y_cm"] * CM2F - p0.Y) * d.Y) * F2CM for s in (s0, s1))
            else:
                ts = sorted(((o["x_cm"] * CM2F - p0.X) * d.X + (s * CM2F - p0.Y) * d.Y) * F2CM for s in (s0, s1))
            L = walls[wi][0].Length * F2CM
            if lat <= 8.0 and ts[0] >= -1 and ts[1] <= L + 1 and (best is None or lat < best[0]):
                best = (lat, wi, ts)
        if best is None:
            continue
        _lat, wi, (tl, th) = best
        openings_per_wall[wi].append((tl * CM2F, th * CM2F, o["opening_base_z_rel_cm"] * CM2F,
                                      o["opening_top_z_rel_cm"] * CM2F))
        opening_ids[wi].append((tl, o["element_id"]))
    for wi in range(len(walls)):
        order = sorted(range(len(openings_per_wall[wi])), key=lambda k: openings_per_wall[wi][k])
        openings_per_wall[wi] = [openings_per_wall[wi][k] for k in order]
        opening_ids[wi] = [sorted(opening_ids[wi])[k][1] for k in range(len(order))]
    return dict(walls=walls, nodes=nodes, e2n=e2n, openings_per_wall=openings_per_wall, ids=ids,
                opening_ids=opening_ids)


def solve(ctx, **kw):
    res = m.solve_building_blocks_all_courses(ctx["nodes"], ctx["walls"], ctx["e2n"], ctx["openings_per_wall"],
                                              CATALOG, 0.0, NUM_COURSES,
                                              variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE, **kw)
    res["num_courses"] = NUM_COURSES
    return res


def extent_cm(walls, wi, cand):
    p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, wi)
    lo, hi = m._candidate_t_range_on_wall(cand, p0, d)
    return lo * F2CM, hi * F2CM


if __name__ == "__main__":
    masonry, ops = load_inputs()
    ctx = build(masonry, ops)
    print("walls", len(ctx["walls"]), "openings", sum(len(v) for v in ctx["openings_per_wall"]))
