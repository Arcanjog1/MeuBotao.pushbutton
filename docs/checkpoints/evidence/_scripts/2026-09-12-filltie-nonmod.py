import sys, os, json, collections
root = os.path.abspath(sys.argv[1]); os.chdir(root); sys.path.insert(0, root); sys.path.insert(0, os.path.join(root, "tests"))
import test_block_arm_role_candidate_safety_contract as T
m = T.m; ws = sys.modules["core.engine.wall_stepper"]
from nuvem.benchmark import runner as bench_runner
from nuvem.benchmark.solver_bridge import plan_from_input, catalog_from_input
out = {}
for enabled in (True, False):
    ws.ABUTTING_TIE_PARITY_ENABLED = enabled
    paths = bench_runner.project_paths("torre_easy_lo_r00_tp1")
    inp = json.load(open(paths["input"], encoding="utf-8"))
    nodes, walls, e2n, op = plan_from_input(inp); cat, _r, _d = catalog_from_input(inp)
    s = inp.get("settings") or {}
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, op, cat, float(s.get("base_z_cm") or 0.0)/100.0*m.FEET_PER_METER, int(s.get("num_courses") or 15), variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    nm = res.get("non_modular") or []
    sig = collections.Counter((e.get("wall_idx"), e.get("course"), e.get("conflict"), round(e.get("seg_start_cm") or 0, 1), round(e.get("seg_end_cm") or 0, 1)) for e in nm)
    out[str(enabled)] = {"n": len(nm), "sig": {str(k): v for k, v in sig.items()}, "blocks": sum(len(v) for v in (res.get("course_candidates") or {}).values()), "collisions": len(res.get("collisions") or [])}
    print("paridade", enabled, "non_modular", len(nm), "collisions", out[str(enabled)]["collisions"], "blocos fisicos", out[str(enabled)]["blocks"], flush=True)
a, b = out["True"]["sig"], out["False"]["sig"]
print("so' com paridade ON:"); [print("  ", k, a[k]) for k in sorted(set(a) - set(b))]
print("so' com paridade OFF:"); [print("  ", k, b[k]) for k in sorted(set(b) - set(a))]
