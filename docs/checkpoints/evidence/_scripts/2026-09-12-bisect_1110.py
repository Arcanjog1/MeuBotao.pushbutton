"""Uso: python3 bisect_1110.py <root> <label> [projects...]
Reaplica a reserva de MEIO B54 no vizinho de meio de vao
(_clip_range_by_midspan_neighbours, revertida em cf325f2) e mede o corpus."""
import sys, os, json, time
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]
projects = sys.argv[3:] or ["torre_easy_lo_r00_tp1"]
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner, solver_bridge
m = solver_bridge.engine()
ws = sys.modules["core.engine.wall_stepper"]
src = '''
def _clip_range_by_midspan_neighbours(walls_to_create, nodes, wall_idx, t_ft, safe_range_ft, exclude_node_index=None):
    lo_ft, hi_ft = safe_range_ft
    for other_index, other in enumerate(nodes or []):
        if other_index == exclude_node_index:
            continue
        if wall_idx not in _midspan_node_wall_ids(other):
            continue
        t_other = _t_of_point_on_wall(walls_to_create, wall_idx, other["point"])
        reserve_ft = max(_cm_to_ft(_node_default_reservation_cm(walls_to_create, other)), T_INTERSECTION_B54_HALF_ROOM_FT)
        if t_other > t_ft + 1e-6:
            hi_ft = min(hi_ft, t_other - reserve_ft)
        elif t_other < t_ft - 1e-6:
            lo_ft = max(lo_ft, t_other + reserve_ft)
    return lo_ft, hi_ft
'''
exec(src, ws.__dict__)
print(label, "patched: reserva = max(meia espessura, meio B54) =", ws.T_INTERSECTION_B54_HALF_ROOM_FT, flush=True)
out = {"label": label, "root": root, "variant": "reserva_meio_B54", "projects": {}}
for pid in projects:
    t0 = time.time()
    r = runner.run_project(pid, write_files=False)
    sc = r["score"]
    inv = [f for f in r["findings"] if f.get("code") in ("OPENING_BLOCK_INSIDE_DOOR", "OPENING_BLOCK_INSIDE_WINDOW")]
    entry = {"seconds": round(time.time()-t0,1), "blocks": sc["blocks"], "critical_errors": sc["critical_errors"], "critical_by_code": sc["critical_by_code"],
             "inside_openings": [{k: f.get(k) for k in ("code","wall","row","blocks","block_t_cm","opening_t_cm")} for f in inv]}
    out["projects"][pid] = entry
    print(label, pid, json.dumps({k: entry[k] for k in ("seconds","blocks","critical_errors","critical_by_code")}), flush=True)
    for f in entry["inside_openings"]: print("   ", json.dumps(f), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bisect1110_%s.json" % label), "w"), indent=1)
