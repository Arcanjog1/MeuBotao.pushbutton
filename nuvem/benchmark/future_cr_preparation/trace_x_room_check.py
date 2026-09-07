import collections, json, os, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,ROOT)
from nuvem.benchmark import runner, solver_bridge
solver_bridge.engine()
ws=sys.modules["core.engine.wall_stepper"]
FT=ws.FEET_PER_METER if hasattr(ws,"FEET_PER_METER") else None
def cm(ft): return ft*100.0/3.280839895013123
EV=[]
orig=ws._x_intersection_centered_candidate
def traced(catalog, point, x_dir, room_ft, course, wall_idx, secondary_wall_idx, node_index, placement_reason):
    out=orig(catalog, point, x_dir, room_ft, course, wall_idx, secondary_wall_idx, node_index, placement_reason)
    EV.append({"room_cm": round(cm(room_ft),4), "node": node_index, "wall": wall_idx,
               "escolhido": (out.get("logical_code")) if isinstance(out,dict) else ("None" if out is None else str(type(out)))})
    return out
ws._x_intersection_centered_candidate=traced
for pid in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    EV.clear()
    solver_bridge.run_solver(json.load(open(runner.project_paths(pid)["input"],encoding="utf-8")))
    print(f"\n### {pid}: {len(EV)} degradacoes de X avaliadas")
    if not EV: continue
    vals=sorted(e["room_cm"] for e in EV)
    print("   room_cm distintos:", sorted(set(vals))[:20])
    near=[v for v in vals if 27.0<=v<29.5]
    print(f"   perto do teto 28.00cm (27.0..29.5): {len(near)} -> {sorted(set(near))}")
    print("   codigo escolhido:", dict(collections.Counter(str(e["escolhido"]) for e in EV)))
