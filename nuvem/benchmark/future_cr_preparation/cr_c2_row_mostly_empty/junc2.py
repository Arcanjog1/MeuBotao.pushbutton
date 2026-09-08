"""Disseca os 16 nos PRE-EXISTENTES do TP1 que ganharam achado em C."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_junctions
proj="torre_easy_lo_r00_tp1"
R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
def ach(d):
    s=collections.defaultdict(set)
    for f in validate_junctions.validate(d):
        if f["code"]!="JUNCTION_MISSING_BINDING": continue
        s[tuple(round(v,1) for v in f["point_cm"])].add((round(f["elevation_cm"],1), f.get("junction_type")))
    return s
def nos(d):
    s=collections.defaultdict(list)
    for w in d["walls"]:
        for j in w.get("junctions") or []:
            s[tuple(round(v,1) for v in j["point_cm"])].append((w["id"], w["length_cm"], j.get("type"), len(w.get("rows") or [])))
    return s
aR,aC=ach(R),ach(C); nR,nC=nos(R),nos(C)
pt=(6600.2,1120.0)
print(f"PONTO {pt}")
print(f"  R: achados em cotas {sorted(aR.get(pt,[]))}")
print(f"  C: achados em cotas {sorted(aC.get(pt,[]))}")
print(f"  R: paredes no no': {nR.get(pt)}")
print(f"  C: paredes no no': {nC.get(pt)}")
# tipo do no' mudou?
mud=0; tipo_mudou=[]
for p in aC:
    if p in aR:
        tR={t for _,t in aR[p]}; tC={t for _,t in aC[p]}
        if tR!=tC: tipo_mudou.append((p,tR,tC))
print(f"\n  pontos cujo TIPO de no' mudou entre R e C: {len(tipo_mudou)}")
for p,a,b in tipo_mudou[:8]: print(f"     {p}: R={a} -> C={b}")
