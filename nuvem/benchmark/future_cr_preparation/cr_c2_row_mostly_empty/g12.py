"""FASE 3 - G12 na SAIDA DO SOLVER: identidades NOVAS de PRISM_CONTINUOUS_JOINT
no delta IN_R -> IN_C, por COORDENADA GLOBAL (sobrevive a' divisao de parede)."""
import json, sys, os, collections
root, out, tag = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver

def solve(inp, pid):
    (res, walls, nodes, ops, cat, bz, nc, notes) = solver_bridge.run_solver(inp)
    return from_solver.project_from_solver(pid, res, walls, nodes, ops, cat, bz, nc,
                                           metadata={"from_input": "G12 review"})

def gid(d, code):
    """identidade fisica global do achado"""
    idx={w["id"]:w for w in d["walls"]}; res=collections.Counter()
    f,e = validators.run_all(d, {})
    for x in f:
        if x["code"]!=code: continue
        w=idx.get(x.get("wall"))
        if w is None: res[("<orfao>",x.get("detail"))]+=1; continue
        dirv,_=model.direction_of(w["start_cm"],w["end_cm"])
        t=x.get("joint_t_cm")
        if t is None: res[(x.get("wall"),x.get("row"))]+=1; continue
        pt=(round(w["start_cm"][0]+dirv[0]*t,1), round(w["start_cm"][1]+dirv[1]*t,1))
        z=[]
        for rk in ("row_a","row_b"):
            rr=[r for r in w["rows"] if r["row"]==x.get(rk)]
            z.append(round(rr[0]["elevation_cm"],1) if rr else None)
        res[(pt,tuple(z),w["thickness_cm"])]+=1
    return res, collections.Counter(y["code"] for y in f)

for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    sR = solve(json.load(open(os.path.join(out,proj,"input_roundtrip.json"))), proj)
    sC = solve(json.load(open(os.path.join(out,proj,"input_candidate.json"))), proj)
    pR,cR = gid(sR,"PRISM_CONTINUOUS_JOINT"); pC,cC = gid(sC,"PRISM_CONTINUOUS_JOINT")
    novas=[i for i in pC if i not in pR]; sumiu=[i for i in pR if i not in pC]
    print(f"===== [{tag}] {proj} — SOLVER, delta IN_R -> IN_C =====")
    print(f"  G12 PRISM_CONTINUOUS_JOINT: R={sum(pR.values())} C={sum(pC.values())} "
          f"saldo={sum(pC.values())-sum(pR.values()):+d} | NOVAS={len(novas)} SUMIRAM={len(sumiu)}")
    for c in sorted(set(cR)|set(cC)):
        if cC[c]-cR[c]: print(f"     {c:34s} R={cR[c]:5d} C={cC[c]:5d} delta={cC[c]-cR[c]:+d}")
