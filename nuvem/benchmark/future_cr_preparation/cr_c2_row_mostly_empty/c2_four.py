"""CR-C2 - disseca os 4 achados que nao recaem sobre regiao acusada em R."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis, model
proj="torre_easy_lo_r00_tgd"
R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
bh=analysis.block_height_of(C)
idxC={w["id"]:w for w in C["walls"]}
alvo=[w for w in C["walls"] if abs(w["length_cm"]-169.0)<0.1]
print(f"paredes de 169cm em C: {len(alvo)}")
w=[x for x in alvo if abs(x["start_cm"][0]-(-401.5))<1][0]
print(f"\nFILHO 169cm: eixo={w['start_cm']}->{w['end_cm']} th={w['thickness_cm']} base_z={w['base_z_cm']} h={w['height_cm']}")
print(f"   aberturas={w['openings']}")
print(f"   junctions={w['junctions']}")
occC=analysis.OccupancyIndex(C)
for r in sorted(w["rows"], key=lambda r: r["elevation_cm"]):
    exp=VC.modulable_intervals(w,r,bh); el=sum(b-a for a,b in exp)
    pcs=[(b["t_start_cm"],b["t_end_cm"]) for b in r.get("blocks") or []]
    fo=[]
    for iv in exp: fo.extend(occC.foreign_coverage_on_axis(w,r,iv[0],iv[1]))
    m=analysis.merge_intervals(list(pcs)+fo, tolerance_cm=1.0)
    span=sum(analysis.interval_overlap_cm(p,iv) for p in m for iv in exp)
    print(f"   fiada {r['row']:2d} z={r['elevation_cm']:6.1f} nb={len(r['blocks']):2d} mod={el:6.1f} exp={[(round(a,1),round(b,1)) for a,b in exp]} proprios={[('%.0f-%.0f'%(a,b)) for a,b in sorted(pcs)]} vizinho={[('%.0f-%.0f'%(a,b)) for a,b in fo]} ratio={span/el if el else 0:.2f}")
# a mae em R
def parent(child,parents):
    best=None
    for p in parents:
        if abs(p["thickness_cm"]-child["thickness_cm"])>0.5: continue
        d,L=model.direction_of(p["start_cm"],p["end_cm"]); ok=True
        for pt in (child["start_cm"],child["end_cm"]):
            t,s=model.axial_coordinates(pt,p["start_cm"],d)
            if abs(s)>1.0 or t<-1.0 or t>L+1.0: ok=False;break
        if ok and (best is None or p["length_cm"]>best["length_cm"]): best=p
    return best
p=parent(w,R["walls"])
print(f"\nMAE(R): eixo={p['start_cm']}->{p['end_cm']} L={p['length_cm']} h={p['height_cm']} aberturas={len(p['openings'])}")
occR=analysis.OccupancyIndex(R)
fR=[f for f in VC.validate(R) if f["code"]=="COVERAGE_ROW_MOSTLY_EMPTY" and f["wall"]==p["id"]]
print(f"   achados ROW_MOSTLY_EMPTY na mae: {len(fR)} -> fiadas {[f['row'] for f in fR]}")
for r in sorted(p["rows"], key=lambda r: r["elevation_cm"]):
    exp=VC.modulable_intervals(p,r,bh); el=sum(b-a for a,b in exp)
    pcs=[(b["t_start_cm"],b["t_end_cm"]) for b in r.get("blocks") or []]
    fo=[]
    for iv in exp: fo.extend(occR.foreign_coverage_on_axis(p,r,iv[0],iv[1]))
    m=analysis.merge_intervals(list(pcs)+fo, tolerance_cm=1.0)
    span=sum(analysis.interval_overlap_cm(x,iv) for x in m for iv in exp)
    print(f"   fiada {r['row']:2d} z={r['elevation_cm']:6.1f} nb={len(r['blocks']):2d} mod={el:6.1f} ratio={span/el if el else 0:.2f}")
