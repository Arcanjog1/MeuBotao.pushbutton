# -*- coding: utf-8 -*-
"""PROVENANCE CAD -> WALL (secao 17). Replica o laco de find_wall_pairs
usando AS MESMAS funcoes do motor (nenhuma alteracao no core), so' que
guardando qual par (i,j) de linhas gerou cada parede e quem 'roubou' cada
linha longa que sobrou."""
import json,os,sys,math,time
sys.path.insert(0,"nuvem")
from benchmark import solver_bridge, wall_modeling_bridge as wmb
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; OUT=os.environ["DIAG_OUT"]
inp=json.load(open(os.path.join(BASE,"input_real.json"),encoding="utf-8"))
mod=solver_bridge.engine(); F=mod.FEET_PER_METER
cm=lambda ft: ft/F*100.0
wp = mod
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
cands=[]
t0=time.time()
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
print("candidatos validos:",len(cands),"(%.1fs)"%(time.time()-t0))
used=[False]*n; walls=[]; prov=[]
stolen_by={}
for key,i,j,mt in cands:
    if used[i] or used[j]:
        # registra quem tinha esse par como candidato mas perdeu
        stolen_by.setdefault(i,[]).append((key,j))
        stolen_by.setdefault(j,[]).append((key,i))
        continue
    c=mod.create_centerline(pending[i],pending[j],mod.CENTERLINE_MAX_EXTENSION_FT)
    if c:
        locked=(False,False)
        clipped,locked=mod.clip_centerline_to_caps(c,mt,pending,ops)
        c=clipped
        if c is not None:
            walls.append((c,mt,locked)); prov.append((i,j,key[0],key[1]))
    used[i]=True; used[j]=True
print("paredes:",len(walls))
def L(idx):
    p0,p1=pending[idx].GetEndPoint(0),pending[idx].GetEndPoint(1)
    return (round(cm(p0.X),2),round(cm(p0.Y),2),round(cm(p1.X),2),round(cm(p1.Y),2),round(cm(p0.DistanceTo(p1)),2))
out=[]
for k,(c,mt,locked) in enumerate(walls):
    i,j,negr,d=prov[k]
    p0,p1=c.GetEndPoint(0),c.GetEndPoint(1)
    out.append({"w":k,"s":[round(cm(p0.X),2),round(cm(p0.Y),2)],"e":[round(cm(p1.X),2),round(cm(p1.Y),2)],
                "len":round(cm(p0.DistanceTo(p1)),2),"th":round(cm(mt),2),"locked":list(locked),
                "line_i":L(i),"line_j":L(j),"overlap_ratio":round(-negr,4),"dist_cm":round(cm(d),3)})
json.dump(out,open(os.path.join(OUT,"provenance_walls.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=0)
# quem consumiu cada linha longa importante
alvo=[(-1813.5,350.0,-1813.5,-146.0),(-1799.5,-160.0,-1799.5,364.0),
      (2005.5,-146.0,2005.5,350.0),(1991.5,364.0,1991.5,-160.0),
      (2267.7,-569.9,586.5,-569.9),(2056.5,-556.0,600.5,-556.0),
      (-1878.5,350.0,-1494.5,350.0),(-1494.5,364.0,-1864.5,364.0),
      (1686.5,350.0,2070.5,350.0),(2056.5,364.0,1686.5,364.0),
      (167.5,288.0,167.5,368.0),(170.5,228.0,170.5,518.0),(156.5,518.0,156.5,180.0),
      (164.2,401.4,164.2,477.6),(168.6,477.6,168.6,401.4)]
def find_idx(a):
    for k in range(n):
        x0,y0,x1,y1,_=L(k)
        if (abs(x0-a[0])<0.3 and abs(y0-a[1])<0.3 and abs(x1-a[2])<0.3 and abs(y1-a[3])<0.3) or \
           (abs(x1-a[0])<0.3 and abs(y1-a[1])<0.3 and abs(x0-a[2])<0.3 and abs(y0-a[3])<0.3):
            return k
    return None
print()
print("=== destino de cada linha-face relevante ===")
for a in alvo:
    k=find_idx(a)
    if k is None: print("   NAO ACHOU",a); continue
    w=[x for x in out if x["line_i"]==L(k) or x["line_j"]==L(k)]
    info="SOBROU (unused)" if not w else "parede w=%d len=%.1f eixo (%s)->(%s) parceira len=%.1f"%(
        w[0]["w"],w[0]["len"],w[0]["s"],w[0]["e"],
        (w[0]["line_j"][4] if w[0]["line_i"]==L(k) else w[0]["line_i"][4]))
    print("   linha %-4d len=%8.2f (%9.1f,%8.1f)->(%9.1f,%8.1f) : %s"%(k,L(k)[4],L(k)[0],L(k)[1],L(k)[2],L(k)[3],info))
    if not w:
        best=sorted(stolen_by.get(k,[]))[:3]
        for key,other in best:
            ow=[x for x in out if x["line_i"]==L(other) or x["line_j"]==L(other)]
            print("        candidato perdido: r=%.4f d=%.3fcm com linha %d len=%.2f -> %s"%(
                -key[0],cm(key[1]),other,L(other)[4],
                ("parede w=%d len=%.1f"%(ow[0]["w"],ow[0]["len"]) if ow else "tambem sobrou")))
