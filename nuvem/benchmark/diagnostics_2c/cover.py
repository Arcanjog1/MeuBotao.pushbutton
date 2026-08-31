# -*- coding: utf-8 -*-
"""Cruzamento 97 walls do GABARITO x 167 walls do WALL MODELING x 380 pares
perdidos. Responde: quantas paredes do gabarito o WM nao criou, e quantas
delas o roubo de face explica. SOMENTE LEITURA."""
import json,os,math
from collections import Counter,defaultdict
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; OUT=os.environ["DIAG_OUT"]
LB=lambda n: json.load(open(os.path.join(BASE,n),encoding="utf-8"))
LO=lambda n: json.load(open(os.path.join(OUT,n),encoding="utf-8"))
ref=LB("reference.json"); snap=LB("wall_modeling_snapshot.json")
ML=LO("merged_lines.json"); ACC=LO("accepted.json"); LOST=LO("lost.json"); OWN=LO("owner.json")

def seg(o,ks="start_cm",ke="end_cm"):
    return o[ks][0],o[ks][1],o[ke][0],o[ke][1]
def ang(x0,y0,x1,y1): return math.degrees(math.atan2(y1-y0,x1-x0))%180.0
def adiff(a,b):
    d=abs(a-b)%180.0
    return min(d,180.0-d)

class Ax:
    def __init__(self,x0,y0,x1,y1):
        self.x0,self.y0,self.x1,self.y1=x0,y0,x1,y1
        self.L=math.hypot(x1-x0,y1-y0)
        self.ux,self.uy=((x1-x0)/self.L,(y1-y0)/self.L) if self.L>1e-9 else (1.0,0.0)
        self.a=ang(x0,y0,x1,y1)
    def proj(self,px,py): return (px-self.x0)*self.ux+(py-self.y0)*self.uy
    def perp(self,px,py): return -(px-self.x0)*self.uy+(py-self.y0)*self.ux

def coverage(axis,others,perp_tol):
    """others: lista de (x0,y0,x1,y1,label). devolve (frac_coberta, intervalos, labels)"""
    iv=[];lab=[]
    for x0,y0,x1,y1,label in others:
        if adiff(axis.a,ang(x0,y0,x1,y1))>3.0: continue
        pm=(axis.perp(x0,y0)+axis.perp(x1,y1))/2.0
        if abs(pm)>perp_tol: continue
        t0,t1=sorted((axis.proj(x0,y0),axis.proj(x1,y1)))
        a,b=max(t0,0.0),min(t1,axis.L)
        if b-a<=1.0: continue
        iv.append((a,b)); lab.append((label,round(a,1),round(b,1),round(pm,2)))
    iv.sort(); mrg=[]
    for a,b in iv:
        if mrg and a<=mrg[-1][1]: mrg[-1][1]=max(mrg[-1][1],b)
        else: mrg.append([a,b])
    cov=sum(b-a for a,b in mrg)
    return cov/axis.L if axis.L>0 else 0.0, mrg, lab

WM=[(w["start_cm"][0],w["start_cm"][1],w["end_cm"][0],w["end_cm"][1],"wm%d"%w["index"]) for w in snap["walls"]]

# ---------- centerline aproximada de cada par PERDIDO --------------------
def pair_axis(i,j):
    xi0,yi0,xi1,yi1,Li=ML[i]; xj0,yj0,xj1,yj1,Lj=ML[j]
    A=Ax(xi0,yi0,xi1,yi1)
    # deslocamento perpendicular medio ate' a linha j
    pj=(A.perp(xj0,yj0)+A.perp(xj1,yj1))/2.0
    ox,oy=-A.uy*pj/2.0, A.ux*pj/2.0
    tj0,tj1=sorted((A.proj(xj0,yj0),A.proj(xj1,yj1)))
    a=max(0.0,tj0); b=min(A.L,tj1)
    if b<=a: return None
    return (A.x0+A.ux*a+ox, A.y0+A.uy*a+oy, A.x0+A.ux*b+ox, A.y0+A.uy*b+oy, b-a)

LOSTAX=[]
for k,l in enumerate(LOST):
    pa=pair_axis(l["i"],l["j"])
    if pa: LOSTAX.append((pa[0],pa[1],pa[2],pa[3],"lost%d"%k))

print("="*90)
print("K/N. COBERTURA DAS 97 PAREDES DO GABARITO PELAS 167 DO WALL MODELING")
print("="*90)
rows=[]
for w in ref["walls"]:
    x0,y0,x1,y1=seg(w); A=Ax(x0,y0,x1,y1)
    frac,mrg,lab=coverage(A,WM,8.0)
    fracL,mrgL,labL=coverage(A,LOSTAX,8.0)
    rows.append(dict(id=w["id"],key=w.get("key"),L=round(A.L,1),ang=round(A.a,1),
                     cov=round(frac,3),covlost=round(fracL,3),n=len(lab),
                     lab=lab,labL=labL,x0=x0,y0=y0,x1=x1,y1=y1))
def cls(r):
    if r["cov"]>=0.85: return "COBERTA"
    if r["cov"]>=0.30: return "PARCIAL"
    if r["cov"]>0.0:   return "QUASE_AUSENTE"
    return "AUSENTE"
for r in rows: r["cls"]=cls(r)
c=Counter(r["cls"] for r in rows)
for k in ("COBERTA","PARCIAL","QUASE_AUSENTE","AUSENTE"):
    sel=[r for r in rows if r["cls"]==k]
    print("  %-14s %3d paredes  %9.1f cm"%(k,len(sel),sum(r["L"] for r in sel)))
print("  TOTAL          %3d paredes  %9.1f cm"%(len(rows),sum(r["L"] for r in rows)))
print()
print("--- paredes do gabarito NAO cobertas (cov < 0.85), com o que um par PERDIDO cobriria ---")
bad=[r for r in rows if r["cls"]!="COBERTA"]
bad.sort(key=lambda r:-r["L"])
rec=0
for r in bad:
    mark="<== par perdido cobre %.0f%%"%(100*r["covlost"]) if r["covlost"]>=0.5 else ""
    if r["covlost"]>=0.5: rec+=1
    print("  %-8s L=%8.1f ang=%5.1f cov_wm=%5.2f cov_lost=%5.2f  (%8.1f,%8.1f)->(%8.1f,%8.1f) %s"%(
        r["id"],r["L"],r["ang"],r["cov"],r["covlost"],r["x0"],r["y0"],r["x1"],r["y1"],mark))
print()
print("paredes do gabarito nao cobertas: %d ; dessas, %d seriam recuperadas por um par PERDIDO (>=50%%)"%(len(bad),rec))
json.dump(rows,open(os.path.join(OUT,"ref_coverage.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=0)
