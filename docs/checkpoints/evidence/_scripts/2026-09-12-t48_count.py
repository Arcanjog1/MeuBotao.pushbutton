import sys, os, json, time
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge
inp = json.load(open("nuvem/benchmark/projects/torre_easy_lo_r00_tp1/input.json"))
t0=time.time()
(res, walls, nodes, opw, cat, z, n, notes) = solver_bridge.run_solver(inp)
rep = res.get("b19_residual_fill_repair") or {}
rej = rep.get("rejected") or []
print(label, "accepted", len(rep.get("accepted") or []), "rejected", len(rej), "reasons", sorted(set(r.get("reason") for r in rej)), "walls", sorted(set(r.get("wall_idx") for r in rej)), "seconds", round(time.time()-t0,1))
