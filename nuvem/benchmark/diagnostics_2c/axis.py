# -*- coding: utf-8 -*-
"""Varredura sistematica 'eixo criado x eixo do gabarito' (pendencia 11.1 do
handoff) + paredes espurias + bonecas distintas. SOMENTE LEITURA."""
import json,os,math
from collections import Counter
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; OUT=os.environ["DIAG_OUT"]; DIAG="nuvem/benchmark/diagnostics_2c"
LB=lambda n: json.load(open(os.path.join(BASE,n),encoding="utf-8"))
LO=lambda n: json.load(open(os.path.join(OUT,n),encoding="utf-8"))
snap=LB("wall_modeling_snapshot.json"); ref=LB("reference.json")
ACC=LO("accepted.json")
strict=json.load(open(os.path.join(DIAG,"openings_strict.json"),encoding="utf-8"))
def ang(x0,y0,x1,y1): return math.degrees(math.atan2(y1-y0,x1-x0))%180.0
def adiff(a,b):
    d=abs(a-b)%180.0; return min(d,180.0-d)
class Ax:
    def __init__(s,x0,y0,x1,y1):
        s.x0,s.y0,s.x1,s.y1=x0,y0,x1,y1; s.L=math.hypot(x1-x0,y1-y0)
        s.ux,s.uy=((x1-x0)/s.L,(y1-y0)/s.L) if s.L>1e-9 else (1.,0.); s.a=ang(x0,y0,x1,y1)
    def proj(s,p,q): return (p-s.x0)*s.ux+(q-s.y0)*s.uy
    def perp(s,p,q): return -(p-s.x0)*s.uy+(q-s.y0)*s.ux
R=[Ax(w["start_cm"][0],w["start_cm"][1],w["end_cm"][0],w["end_cm"][1]) for w in ref["walls"]]
RID=[w["id"] for w in ref["walls"]]
print("="*95)
print("PENDENCIA 11.1 - ERRO DE EIXO: cada uma das 167 walls x eixo do gabarito mais proximo")
print("="*95)
c=Counter(); esp=[]; desl=[]
for w in snap["walls"]:
    A=Ax(w["start_cm"][0],w["start_cm"][1],w["end_cm"][0],w["end_cm"][1])
    mid=((A.x0+A.x1)/2.0,(A.y0+A.y1)/2.0)
    best=None
    for k,B in enumerate(R):
        if adiff(A.a,B.a)>3.0: continue
        t=B.proj(*mid)
        if t<-20 or t>B.L+20: continue
        e=abs(B.perp(*mid))
        if best is None or e<best[0]: best=(e,k)
    if best is None:
        c["sem eixo de gabarito paralelo por perto"]+=1; esp.append(w); continue
    e=best[0]
    k=("<=0,5 cm (no lugar)" if e<=0.5 else "0,5-2 cm" if e<=2 else "2-6 cm" if e<=6 else "6-10 cm" if e<=10 else "10-16 cm" if e<=16 else ">16 cm")
    c[k]+=1
    if e>2.0: desl.append((round(e,2),w["index"],round(w["length_cm"],1),RID[best[1]]))
for k in ("<=0,5 cm (no lugar)","0,5-2 cm","2-6 cm","6-10 cm","10-16 cm",">16 cm","sem eixo de gabarito paralelo por perto"):
    if c[k]: print("   %-42s %3d"%(k,c[k]))
print()
print("   walls com eixo > 2 cm fora do eixo do gabarito (%d):"%len(desl))
for e,i,L,rid in sorted(desl,reverse=True)[:25]:
    print("      idx=%-4d len=%7.1f  erro=%5.2f cm  gabarito %s"%(i,L,e,rid))
print()
print("   walls SEM nenhum eixo de gabarito paralelo por perto (espurias): %d, soma %.1f cm"%(
    len(esp),sum(w["length_cm"] for w in esp)))
print("      por comprimento:",Counter(("<20" if w["length_cm"]<20 else "20-50" if w["length_cm"]<50 else "50-100" if w["length_cm"]<100 else ">=100") for w in esp).most_common())
print()
print("="*95); print("G (detalhe). Valores DISTINTOS de boneca humana e modularidade"); print("="*95)
vals=sorted(set(round(v,1) for r in strict if r["status"]=="MATCHED" for v in (r["boneca_left_human"],r["boneca_right_human"])))
print("   ",vals)
print("   resto mod 5:",sorted(set(round(v%5.0,2) for v in vals)))
