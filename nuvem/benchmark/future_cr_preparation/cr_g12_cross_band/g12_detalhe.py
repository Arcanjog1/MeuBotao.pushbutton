"""FASE 3 - as 12 identidades do G12 (PRISM_CONTINUOUS_JOINT) com S1+C1.
Resolve IN_R e IN_C, salva os projetos e detalha cada identidade nova."""
import json, sys, os, collections
root, out, dst = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, root); os.makedirs(dst, exist_ok=True)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver
def solve(inp, pid):
    (res, walls, nodes, ops, cat, bz, nc, notes) = solver_bridge.run_solver(inp)
    return from_solver.project_from_solver(pid, res, walls, nodes, ops, cat, bz, nc,
                                           metadata={"from_input":"G12 detalhe"})
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    for st, fn in (("R","input_roundtrip.json"),("C","input_candidate.json")):
        p = solve(json.load(open(os.path.join(out,proj,fn))), proj)
        f, e = validators.run_all(p, {})
        p["_findings"] = f
        json.dump(p, open(os.path.join(dst,f"{proj}_{st}_solved.json"),"w"))
        print(f"  salvo {proj} {st}: paredes={len(p['walls'])} achados={len(f)}")
