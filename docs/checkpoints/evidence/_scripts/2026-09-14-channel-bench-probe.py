# -*- coding: utf-8 -*-
"""Sonda: plano CHANNEL sobre o solve das 34 paredes (BUTANTA 1o PAV)."""
import json
import sys
import time
from collections import Counter

import channel_bench_common as cb

m = cb.m
from core.engine import opening_reinforcement as orf  # noqa: E402

masonry, ops = cb.load_inputs()
ctx = cb.build(masonry, ops)
t0 = time.time()
res = cb.solve(ctx)
t_solve = time.time() - t0
step, _err = m._course_height_ft(cb.CATALOG, res["candidates"])
height = step - m._cm_to_ft(m.COURSE_JOINT_CM)


def band(ci):
    return m._course_z_band(0.0, ci, step, height)


t0 = time.time()
plan = orf.plan_channel_reinforcement(res["course_candidates"], ctx["walls"], ctx["openings_per_wall"], band,
                                      cb.NUM_COURSES, 0.0, nodes=ctx["nodes"], catalog=cb.CATALOG)
t_plan = time.time() - t0
val = orf.validate_channel_reinforcement(plan["course_candidates"], ctx["walls"], ctx["openings_per_wall"], band,
                                         cb.NUM_COURSES, 0.0, free_to_top=plan["free_to_top"])
print("solve %.2fs plan %.3fs" % (t_solve, t_plan))
print("counts", json.dumps(val["counts"], indent=0))
print("findings", Counter(f["code"] for f in plan["findings"]))
for f in plan["findings"]:
    print("  ", f)
print("free_to_top", plan["free_to_top"])
print("crossings", plan["node_crossings"])
for rec in plan["openings"]:
    oid = ctx["opening_ids"][rec["wall_idx"]][rec["opening_index"]]
    print(oid, "w%d" % ctx["ids"][rec["wall_idx"]], rec["t_lo_cm"], rec["t_hi_cm"], "sill", rec["sill_rel_cm"],
          "head", rec["head_rel_cm"], "| above", rec["above"], "| below", rec["below"])
codes = Counter(c["logical_code"] for v in plan["course_candidates"].values() for c in v)
print(codes)
if "--runs" in sys.argv:
    for r in plan["runs"]:
        print(r["run_id"], r["roles"], [(p["code"], p["lo_cm"], p["hi_cm"], p["source_codes"]) for p in r["pieces"]])
