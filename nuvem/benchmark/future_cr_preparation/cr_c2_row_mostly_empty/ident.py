"""FASE 3 - deltas R->C por IDENTIDADE FISICA (eixo+espessura+cota), nunca W0xx."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import (validate_wall_coverage, validate_junctions,
    validate_prism, validate_openings, validate_compensators, validate_block_positions)
MODS=[validate_wall_coverage, validate_junctions, validate_prism,
      validate_openings, validate_compensators, validate_block_positions]
def ident(d):
    """{codigo: Counter(identidade fisica)} - identidade = eixo+espessura(+cota da fiada)."""
    idx={w["id"]:w for w in d["walls"]}
    res=collections.defaultdict(collections.Counter)
    for m in MODS:
        for f in m.validate(d):
            w=idx.get(f.get("wall"))
            if w is None: k=("<sem parede>",)
            else:
                z=None
                if f.get("row") is not None:
                    rr=[x for x in w["rows"] if x["row"]==f["row"]]
                    z=round(rr[0]["elevation_cm"],1) if rr else None
                k=(tuple(w["start_cm"]),tuple(w["end_cm"]),w["thickness_cm"],z)
            res[f["code"]][k]+=1
    return res
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=ident(json.load(open(os.path.join(out,proj,"reference_roundtrip.json"))))
    C=ident(json.load(open(os.path.join(out,proj,"reference_candidate.json"))))
    print(f"===== {proj} — IDENTIDADE FISICA =====")
    print(f"   {'codigo':36s} {'R':>5s} {'C':>5s} {'saldo':>6s} {'NOVAS':>6s} {'SUMIRAM':>8s}")
    for c in sorted(set(R)|set(C)):
        r,k=R[c],C[c]; nr,nk=sum(r.values()),sum(k.values())
        novas=sum(v for i,v in k.items() if i not in r)
        sumiu=sum(v for i,v in r.items() if i not in k)
        flag="   <<<" if (novas or sumiu) else ""
        print(f"   {c:36s} {nr:5d} {nk:5d} {nk-nr:+6d} {novas:6d} {sumiu:8d}{flag}")
