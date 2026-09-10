"""CR-C2 2.1 - reproducer por IDENTIDADE FISICA (nunca W0xx)."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis

def key_of(w):  # identidade fisica: eixo + espessura
    return (tuple(w["start_cm"]), tuple(w["end_cm"]), w["thickness_cm"])

for proj in ("torre_easy_lo_r00_tgd",):
    R = json.load(open(os.path.join(out, proj, "reference_roundtrip.json")))
    C = json.load(open(os.path.join(out, proj, "reference_candidate.json")))
    bh = analysis.block_height_of(C)
    for st, d in (("R",R),("C",C)):
        f = [x for x in VC.validate(d) if x["code"]=="COVERAGE_ROW_MOSTLY_EMPTY"]
        idx = {w["id"]: w for w in d["walls"]}
        d["_me"] = [(key_of(idx[x["wall"]]), x["row"], x) for x in f]
    setR = collections.Counter(k for k,_,_ in R["_me"])
    setC = collections.Counter(k for k,_,_ in C["_me"])
    print(f"== {proj}: R={len(R['_me'])} C={len(C['_me'])} delta={len(C['_me'])-len(R['_me'])}")
    novos = [t for t in C["_me"] if t[0] not in setR]
    sumidos = [t for t in R["_me"] if t[0] not in setC]
    print(f"   em eixo FISICO novo (parede que nao existia em R): {len(novos)}")
    print(f"   em eixo FISICO que sumiu de C:                     {len(sumidos)}")
    # fiadas COMPLETAMENTE vazias entre os achados de C
    vazias = [t for t in C["_me"] if t[2]["covered_cm"] == 0.0]
    print(f"   achados de C com covered_cm == 0 (fiada SEM bloco): {len(vazias)} de {len(C['_me'])}")
    vaziasR = [t for t in R["_me"] if t[2]["covered_cm"] == 0.0]
    print(f"   idem em R:                                          {len(vaziasR)} de {len(R['_me'])}")
    print("   --- amostra dos novos ---")
    for k,r,x in novos[:6]:
        print(f"     eixo={k} fiada={r} covered={x['covered_cm']} modulavel={x['modulable_cm']} ratio={x['coverage_ratio']} best={x['best_row_ratio']}")
