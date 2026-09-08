"""Tabela FISICA das 10 identidades novas de JUNCTION_MISSING_BINDING
(gabarito, delta STATE_R -> STATE_C). Identidade = (ponto global, elevacao)."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_junctions
from nuvem.benchmark import model, analysis
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    def ach(d):
        s={}
        for f in validate_junctions.validate(d):
            if f["code"]!="JUNCTION_MISSING_BINDING": continue
            s.setdefault((tuple(round(v,1) for v in f["point_cm"]), round(f["elevation_cm"],1)), []).append(f)
        return s
    aR,aC=ach(R),ach(C)
    # nos declarados por ponto, em cada estado
    def nos(d):
        s=collections.defaultdict(list)
        for w in d["walls"]:
            for j in w.get("junctions") or []:
                s[tuple(round(v,1) for v in j["point_cm"])].append((w["id"], w["length_cm"], j.get("type"), j.get("at_end")))
        return s
    nR,nC=nos(R),nos(C)
    novas=sorted(k for k in aC if k not in aR)
    ptsR=set(nR)
    print(f"\n{'='*96}\n{proj}: JUNCTION_MISSING_BINDING identidades NOVAS = {len(novas)}")
    occ=analysis.OccupancyIndex(C)
    for i,(pt,z) in enumerate(novas,1):
        f=aC[(pt,z)][0]
        existia = pt in ptsR
        perto=occ.blocks_near(z, pt[0], pt[1], radius_cm=40.0)
        print(f"  {i:2d}. ponto={pt} z={z} tipo={f.get('junction_type')} | ponto existia em R? {existia}")
        print(f"      paredes no no' (C): {nC.get(pt)}")
        print(f"      paredes no no' (R): {nR.get(pt)}")
        print(f"      pecas reais a <=40cm nessa cota: {len(perto)} -> {[b.get('code') for _,b in perto][:8]}")
