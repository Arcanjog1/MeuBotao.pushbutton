# -*- coding: utf-8 -*-
import json,os,sys,math,time
from collections import Counter
sys.path.insert(0,"nuvem")
from benchmark import solver_bridge, wall_modeling_bridge as wmb
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; OUT=os.environ["DIAG_OUT"]
inp=json.load(open(os.path.join(BASE,"input_real.json"),encoding="utf-8"))
mod=solver_bridge.engine(); wp=mod; F=mod.FEET_PER_METER
cm=lambda ft: ft/F*100.0
setup=inp["setup_frozen"]
segs=[s for s in inp["segments"] if s.get("layer")==setup["layer"]]
lines=[wmb._line_from_segment(mod,s) for s in segs]
ops=[wmb._op_from_dict(mod,o) for o in inp["openings"]]
th=sorted(wmb._ft(mod,c) for c in setup["thicknesses_cm"])
merged=mod.merge_collinear_fragments(lines,mod.COLLINEAR_MATCH_TOLERANCE_FT,mod.MAX_JUNCTION_GAP_FT,
                                     ops,mod.OPENING_GAP_PERP_TOLERANCE_FT,mod.OPENING_GAP_WIDTH_SLACK_FT)
tol=mod.compute_detection_tolerance_ft(th)
pending=list(merged); n=len(pending)
caches=[wp._line_geom_cache(l) for l in pending]
def LN(k):
    p0,p1=pending[k].GetEndPoint(0),pending[k].GetEndPoint(1)
    return dict(x0=round(cm(p0.X),2),y0=round(cm(p0.Y),2),x1=round(cm(p1.X),2),y1=round(cm(p1.Y),2),
                L=round(cm(p0.DistanceTo(p1)),2))
cands=[]
for i in range(n):
    ci=caches[i]
    for j in range(i+1,n):
        cj=caches[j]
        if not wp._are_parallel_cached(ci,cj): continue
        d=wp._distance_between_parallel_cached(ci,cj)
        if not (wp.MIN_WALL_THICKNESS_FT<=d<=wp.MAX_WALL_THICKNESS_FT): continue
        mt=wp._closest_target_thickness_ft(d,th,tol)
        if mt is None: continue
        ov,l1,l2=wp._line_pair_overlap_ft_cached(ci,cj)
        if ov<wp.MIN_WALL_SEGMENT_ABS_FLOOR_FT: continue
        sh=min(l1,l2)
        if sh<1e-9: continue
        r=ov/sh
        if r<wp.MIN_WALL_SEGMENT_OVERLAP_RATIO: continue
        cands.append(((-r,d),i,j,mt))
cands.sort(key=lambda c:c[0])
used=[False]*n; accepted=[]; lost=[]
for key,i,j,mt in cands:
    if used[i] or used[j]:
        lost.append((key,i,j)); continue
    accepted.append((key,i,j,mt)); used[i]=True; used[j]=True
print("candidatos=%d  aceitos=%d  perdidos=%d"%(len(cands),len(accepted),len(lost)))
# --- 1. pares aceitos com desequilibrio de comprimento -------------------
print()
print("=== PARES ACEITOS: comprimento das duas linhas ===")
buck=Counter(); roubo=[]
for key,i,j,mt in accepted:
    a,b=LN(i)["L"],LN(j)["L"]
    lo,hi=min(a,b),max(a,b)
    if lo<20 and hi>=100: buck["curta<20 x longa>=100"]+=1; roubo.append((key,i,j,lo,hi))
    elif lo<20: buck["curta<20 x curta"]+=1
    elif lo<50: buck["20-50 x qualquer"]+=1
    else: buck["ambas >=50"]+=1
for k,v in buck.most_common(): print("   %-28s %3d"%(k,v))
print()
print("=== os %d pares em que uma linha CURTA (<20cm) consumiu uma linha LONGA (>=100cm) ==="%len(roubo))
roubo.sort(key=lambda z:-z[4])
for key,i,j,lo,hi in roubo:
    li,lj=LN(i),LN(j)
    print("   r=%.4f d=%.3fcm | curta %6.2f cm  x  LONGA %8.2f cm  em (%.1f,%.1f)-(%.1f,%.1f)"%(
        -key[0],cm(key[1]),lo,hi,li["x0"],li["y0"],lj["x0"],lj["y0"]))
# --- 2. pares "verdadeiros" perdidos ------------------------------------
print()
print("=== PARES PERDIDOS com distancia ~14.00 cm (|d-14|<=0.05) e ratio>=0.9 ===")
true_lost=[]
for key,i,j in lost:
    d=cm(key[1]); r=-key[0]
    if abs(d-14.0)<=0.05 and r>=0.9:
        true_lost.append((key,i,j))
print("total:",len(true_lost))
tl=sorted(true_lost,key=lambda z:-min(LN(z[1])["L"],LN(z[2])["L"]))
for key,i,j in tl[:25]:
    li,lj=LN(i),LN(j)
    print("   d=%.3f r=%.4f | %8.2f cm (%9.1f,%8.1f)->(%9.1f,%8.1f)  x  %8.2f cm (%9.1f,%8.1f)->(%9.1f,%8.1f)"%(
        cm(key[1]),-key[0],li["L"],li["x0"],li["y0"],li["x1"],li["y1"],lj["L"],lj["x0"],lj["y0"],lj["x1"],lj["y1"]))
# --- 3. distribuicao das distancias aceitas -----------------------------
print()
print("=== distancia perpendicular dos 209 pares aceitos (espessura REAL medida) ===")
c=Counter()
for key,i,j,mt in accepted:
    d=cm(key[1]); c[round(d,1)]+=1
for k in sorted(c): print("   %6.1f cm : %3d"%(k,c[k]))
