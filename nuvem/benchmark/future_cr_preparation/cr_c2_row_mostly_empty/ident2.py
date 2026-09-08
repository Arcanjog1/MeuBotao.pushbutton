"""FASE 3 - identidade fisica em COORDENADA GLOBAL (sobrevive a' divisao de
parede): PRISM = (ponto da junta, z_a, z_b); JUNCTION = (point_cm, elevacao)."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_prism, validate_junctions
from nuvem.benchmark import model

def prism_ids(d):
    idx={w["id"]:w for w in d["walls"]}; res=collections.Counter()
    for f in validate_prism.validate(d):
        if f["code"]!="PRISM_CONTINUOUS_JOINT": continue
        w=idx[f["wall"]]; dirv,_=model.direction_of(w["start_cm"],w["end_cm"])
        t=f["joint_t_cm"]
        pt=(round(w["start_cm"][0]+dirv[0]*t,1), round(w["start_cm"][1]+dirv[1]*t,1))
        z=[]
        for rk in ("row_a","row_b"):
            rr=[x for x in w["rows"] if x["row"]==f[rk]]
            z.append(round(rr[0]["elevation_cm"],1) if rr else None)
        res[(pt,tuple(z),w["thickness_cm"])]+=1
    return res

def junc_ids(d):
    res=collections.Counter()
    for f in validate_junctions.validate(d):
        if f["code"]!="JUNCTION_MISSING_BINDING": continue
        res[(tuple(round(v,1) for v in f["point_cm"]), round(f["elevation_cm"],1),
             f.get("junction_type"))]+=1
    return res

for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    print(f"===== {proj} — COORDENADA GLOBAL =====")
    for nome, fn in (("G12 PRISM_CONTINUOUS_JOINT", prism_ids),
                     ("    JUNCTION_MISSING_BINDING", junc_ids)):
        r,k=fn(R),fn(C)
        novas=sorted(i for i in k if i not in r); sumiu=sorted(i for i in r if i not in k)
        print(f"  {nome}: R={sum(r.values())} C={sum(k.values())} saldo={sum(k.values())-sum(r.values()):+d}"
              f" | identidades NOVAS={len(novas)} SUMIRAM={len(sumiu)}")
        for i in novas[:5]: print(f"       NOVA: {i}")
