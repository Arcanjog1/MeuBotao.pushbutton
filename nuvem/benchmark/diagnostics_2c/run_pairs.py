# -*- coding: utf-8 -*-
"""ETAPA 2C (continuacao) - regenera o estado do pareamento e grava tudo em
JSON para as analises seguintes. SOMENTE LEITURA do repo."""
import json,os,sys,time
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
t0=time.time()
merged=mod.merge_collinear_fragments(lines,mod.COLLINEAR_MATCH_TOLERANCE_FT,mod.MAX_JUNCTION_GAP_FT,
                                     ops,mod.OPENING_GAP_PERP_TOLERANCE_FT,mod.OPENING_GAP_WIDTH_SLACK_FT)
print("merge %d -> %d (%.1fs)"%(len(lines),len(merged),time.time()-t0))
tol=mod.compute_detection_tolerance_ft(th)
pending=list(merged); n=len(pending)
caches=[wp._line_geom_cache(l) for l in pending]
def LN(k):
    p0,p1=pending[k].GetEndPoint(0),pending[k].GetEndPoint(1)
    return [round(cm(p0.X),3),round(cm(p0.Y),3),round(cm(p1.X),3),round(cm(p1.Y),3),
            round(cm(p0.DistanceTo(p1)),3)]
def RAW(l):
    p0,p1=l.GetEndPoint(0),l.GetEndPoint(1)
    return [round(cm(p0.X),3),round(cm(p0.Y),3),round(cm(p1.X),3),round(cm(p1.Y),3),
            round(cm(p0.DistanceTo(p1)),3)]
t0=time.time(); cands=[]
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
        cands.append(((-r,d),i,j,mt,ov))
cands.sort(key=lambda c:c[0])
print("candidatos %d (%.1fs)"%(len(cands),time.time()-t0))
used=[False]*n; acc=[]; lost=[]; owner={}
for key,i,j,mt,ov in cands:
    if used[i] or used[j]:
        lost.append(dict(i=i,j=j,r=round(-key[0],5),d=round(cm(key[1]),4),ov=round(cm(ov),2)))
        continue
    c=mod.create_centerline(pending[i],pending[j],mod.CENTERLINE_MAX_EXTENSION_FT)
    rec=dict(i=i,j=j,r=round(-key[0],5),d=round(cm(key[1]),4),th=round(cm(mt),3),ov=round(cm(ov),2))
    if c:
        clipped,locked=mod.clip_centerline_to_caps(c,mt,pending,ops)
        if clipped is not None:
            p0,p1=clipped.GetEndPoint(0),clipped.GetEndPoint(1)
            rec.update(s=[round(cm(p0.X),3),round(cm(p0.Y),3)],e=[round(cm(p1.X),3),round(cm(p1.Y),3)],
                       len=round(cm(p0.DistanceTo(p1)),3),locked=list(locked))
    owner[i]=len(acc); owner[j]=len(acc)
    acc.append(rec); used[i]=True; used[j]=True
print("aceitos %d | perdidos %d | com centerline %d"%(len(acc),len(lost),sum(1 for a in acc if "len" in a)))
json.dump([LN(k) for k in range(n)],open(os.path.join(OUT,"merged_lines.json"),"w"),indent=0)
json.dump([RAW(l) for l in lines],open(os.path.join(OUT,"raw_lines.json"),"w"),indent=0)
json.dump(acc,open(os.path.join(OUT,"accepted.json"),"w"),indent=0)
json.dump(lost,open(os.path.join(OUT,"lost.json"),"w"),indent=0)
json.dump({str(k):v for k,v in owner.items()},open(os.path.join(OUT,"owner.json"),"w"),indent=0)
# dedup / extend, para poder ligar par aceito -> wall final
pairs=[]
for a in acc:
    pass
print("OK")
