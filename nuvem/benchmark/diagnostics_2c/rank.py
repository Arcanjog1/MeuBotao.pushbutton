# -*- coding: utf-8 -*-
"""Quantifica o efeito do criterio de desempate (-overlap_ratio, dist) e a
relacao fragmento curto x abertura. SOMENTE LEITURA."""
import json,os,math
from collections import Counter
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; OUT=os.environ["DIAG_OUT"]
LB=lambda n: json.load(open(os.path.join(BASE,n),encoding="utf-8"))
LO=lambda n: json.load(open(os.path.join(OUT,n),encoding="utf-8"))
inp=LB("input_real.json"); snap=LB("wall_modeling_snapshot.json")
ML=LO("merged_lines.json"); ACC=LO("accepted.json"); LOST=LO("lost.json")
OWN={int(k):v for k,v in LO("owner.json").items()}
NOM=14.0
print("espessuras pedidas:",inp["setup_frozen"]["thicknesses_cm"])
print()
print("="*90); print("EFEITO DO CRITERIO DE ORDENACAO  sort_key = (-overlap_ratio, dist)"); print("="*90)
print("209 pares ACEITOS por erro de espessura |d-14|:")
c=Counter()
for a in ACC:
    e=abs(a["d"]-NOM)
    k=("exato <=0,05" if e<=0.05 else "0,05-0,5" if e<=0.5 else "0,5-1,0" if e<=1.0 else "1,0-1,5" if e<=1.5 else "1,5-2,0" if e<=2.0 else ">2,0")
    c[k]+=1
for k in ("exato <=0,05","0,05-0,5","0,5-1,0","1,0-1,5","1,5-2,0",">2,0"): print("   %-14s %3d"%(k,c[k]))
print("   media |d-14| dos aceitos: %.3f cm"%(sum(abs(a['d']-NOM) for a in ACC)/len(ACC)))
print()
print("aceitos com d ABAIXO de 14 (%.0f) x ACIMA (%.0f)"%(
    sum(1 for a in ACC if a["d"]<13.95),sum(1 for a in ACC if a["d"]>14.05)))
print()
true_lost=[l for l in LOST if abs(l["d"]-NOM)<=0.05 and l["r"]>=0.9]
print("pares PERDIDOS 'verdadeiros' (|d-14|<=0,05 e r>=0,9): %d"%len(true_lost))
melhor=0; pior=0; det=Counter()
for l in true_lost:
    for idx in (l["i"],l["j"]):
        if idx not in OWN: continue
        a=ACC[OWN[idx]]
        if abs(a["d"]-NOM)>abs(l["d"]-NOM)+1e-9:
            melhor+=1
            det[round(a["d"],1)]+=1
        else: pior+=1
print("  ocorrencias em que a face foi levada por um par com espessura PIOR: %d"%melhor)
print("  ocorrencias em que o ladrao tinha espessura igual/melhor:           %d"%pior)
print("  distancia do par ladrao nesses casos:",sorted(det.items()))
print()
print("=> em %d das %d perdas, o par vencedor so' ganhou porque a regra de"%(melhor,melhor+pior))
print("   desempate premia a MENOR distancia, e nao a distancia mais PROXIMA da espessura nominal.")
print()
# simulacao: e se o desempate fosse por |d-espessura|?
print("="*90); print("SIMULACAO (nao aplicada ao codigo): desempate por |d - espessura nominal|"); print("="*90)
# recria todos os candidatos a partir de accepted+lost
allc=[(a["r"],a["d"],a["i"],a["j"]) for a in ACC]+[(l["r"],l["d"],l["i"],l["j"]) for l in LOST]
print("candidatos totais:",len(allc))
def greedy(key):
    used=set(); acc=[]
    for r,d,i,j in sorted(allc,key=key):
        if i in used or j in used: continue
        acc.append((r,d,i,j)); used.add(i); used.add(j)
    return acc
A=greedy(lambda t:(-t[0],t[1]))
B=greedy(lambda t:(-t[0],abs(t[1]-NOM)))
for nome,S in (("ATUAL   (-r, d)",A),("ALTERNATIVA (-r, |d-14|)",B)):
    ex=sum(1 for r,d,i,j in S if abs(d-NOM)<=0.05)
    print("  %-26s aceitos=%3d | com espessura exata=%3d (%.0f%%) | media |d-14|=%.3f"%(
        nome,len(S),ex,100.0*ex/len(S),sum(abs(d-NOM) for r,d,i,j in S)/len(S)))
setA={(min(i,j),max(i,j)) for r,d,i,j in A}; setB={(min(i,j),max(i,j)) for r,d,i,j in B}
print("  pares que so' existem na ALTERNATIVA: %d ; so' no ATUAL: %d"%(len(setB-setA),len(setA-setB)))
print()
print("="*90); print("M. FRAGMENTO CURTO x ABERTURA (a hipotese de reposicionamento nao se aplica)"); print("="*90)
ops=inp["openings"]
def d2seg(px,py,x0,y0,x1,y1):
    dx,dy=x1-x0,y1-y0; L2=dx*dx+dy*dy
    t=0.0 if L2==0 else max(0.0,min(1.0,((px-x0)*dx+(py-y0)*dy)/L2))
    return math.hypot(px-(x0+t*dx),py-(y0+t*dy))
short=[w for w in snap["walls"] if w["length_cm"]<50.0]
near=Counter()
for w in short:
    s,e=w["start_cm"],w["end_cm"]
    best=min((d2seg(o["center_cm"][0],o["center_cm"][1],s[0],s[1],e[0],e[1]),o["element_id"],o["width_cm"]) for o in ops)
    k=("<=30 cm de uma abertura" if best[0]<=30 else "30-100 cm" if best[0]<=100 else "100-300 cm" if best[0]<=300 else ">300 cm")
    near[k]+=1
    print("   idx=%-4d len=%6.2f  abertura mais proxima: %s (larg %.0f) a %7.1f cm"%(w["index"],w["length_cm"],best[1],best[2],best[0]))
print()
for k,v in near.most_common(): print("   %-26s %2d"%(k,v))
