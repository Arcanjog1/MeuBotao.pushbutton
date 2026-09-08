"""CR-C2 2.1 - disseca UM caso: parede-mae em R -> segmentos em C."""
import json, sys, os, collections, math
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis, model

proj="torre_easy_lo_r00_tgd"
R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
def colinear_parent(child, parents):
    """parede de R colinear que CONTEM o eixo do filho."""
    cs,ce=child["start_cm"],child["end_cm"]
    best=None
    for p in parents:
        if abs(p["thickness_cm"]-child["thickness_cm"])>0.5: continue
        d,L=model.direction_of(p["start_cm"],p["end_cm"])
        ok=True; ts=[]
        for pt in (cs,ce):
            t,s=model.axial_coordinates(pt,p["start_cm"],d)
            if abs(s)>1.0 or t<-1.0 or t>L+1.0: ok=False; break
            ts.append(t)
        if ok and (best is None or p["length_cm"]>best[0]["length_cm"]): best=(p,sorted(ts))
    return best

idxC={w["id"]:w for w in C["walls"]}
fC=[x for x in VC.validate(C) if x["code"]=="COVERAGE_ROW_MOSTLY_EMPTY"]
Rkeys={(tuple(w["start_cm"]),tuple(w["end_cm"]),w["thickness_cm"]) for w in R["walls"]}
novos=[x for x in fC if (tuple(idxC[x["wall"]]["start_cm"]),tuple(idxC[x["wall"]]["end_cm"]),idxC[x["wall"]]["thickness_cm"]) not in Rkeys]
bh=analysis.block_height_of(C)
occC=analysis.OccupancyIndex(C); occR=analysis.OccupancyIndex(R)
print(f"achados novos (eixo inexistente em R): {len(novos)}")
x=novos[0]; ch=idxC[x["wall"]]
par=colinear_parent(ch,R["walls"])
p,ts=par
print(f"\nFILHO  eixo={ch['start_cm']}->{ch['end_cm']} L={ch['length_cm']} aberturas={len(ch['openings'])} fiadas={len(ch['rows'])}")
print(f"MAE(R) eixo={p['start_cm']}->{p['end_cm']} L={p['length_cm']} aberturas={len(p['openings'])} fiadas={len(p['rows'])}")
print(f"       filho ocupa t={ts[0]:.1f}..{ts[1]:.1f} da mae")
print(f"\nACHADO: fiada={x['row']} covered={x['covered_cm']} modulavel={x['modulable_cm']} ratio={x['coverage_ratio']} best={x['best_row_ratio']}")
# cobertura da MESMA fiada na mae
prow=[r for r in p["rows"] if r["row"]==x["row"]]
crow=[r for r in ch["rows"] if r["row"]==x["row"]]
for lbl,w,rows,occ in (("MAE",p,prow,occR),("FILHO",ch,crow,occC)):
    if not rows: print(f"  {lbl}: fiada {x['row']} NAO EXISTE"); continue
    r=rows[0]; exp=VC.modulable_intervals(w,r,bh); el=sum(b-a for a,b in exp)
    pcs=[(b["t_start_cm"],b["t_end_cm"]) for b in r["blocks"]]
    print(f"  {lbl}: z={r['elevation_cm']} nblocos={len(r['blocks'])} modulavel={el:.1f} intervalos={[(round(a,1),round(b,1)) for a,b in exp]}")
    print(f"        blocos t=[{', '.join('%.0f-%.0f'%(a,b) for a,b in sorted(pcs))}]")
