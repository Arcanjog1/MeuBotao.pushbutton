# -*- coding: utf-8 -*-
"""F/G/H - bonecas INPUT x HUMANO, efeito modular e o que o humano assentou
ao lado de cada abertura. SOMENTE LEITURA."""
import json,os,math
from collections import Counter,defaultdict
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; DIAG="nuvem/benchmark/diagnostics_2c"
LB=lambda n: json.load(open(os.path.join(BASE,n),encoding="utf-8"))
ref=LB("reference.json")
strict=json.load(open(os.path.join(DIAG,"openings_strict.json"),encoding="utf-8"))
refw={w["id"]:w for w in ref["walls"]}
M=[r for r in strict if r["status"]=="MATCHED"]
print("pares casados:",len(M))
print()
print("="*100)
print("F. BONECAS  (distancia da lateral do vao ate' o vizinho: outra abertura ou a ponta da parede)")
print("="*100)
print("%-9s %-9s %-6s %9s %9s %9s %9s %9s %9s"%("INPUT","HUMANO","larg","bonE_IN","bonE_HUM","dif","bonD_IN","bonD_HUM","dif"))
dif=[]
for r in sorted(M,key=lambda r:r["input_id"]):
    dl=r["boneca_left_human"]-r["boneca_left_input"]; dr=r["boneca_right_human"]-r["boneca_right_input"]
    dif.append(abs(dl)); dif.append(abs(dr))
    print("%-9s %-9s %6.0f %9.2f %9.2f %+9.3f %9.2f %9.2f %+9.3f"%(
        r["input_id"],r["human_id"],r["w_in"],r["boneca_left_input"],r["boneca_left_human"],dl,
        r["boneca_right_input"],r["boneca_right_human"],dr))
print()
print("diferenca |boneca_humano - boneca_input| em %d bonecas: max=%.3f cm  media=%.4f cm  >0,5cm: %d"%(
    len(dif),max(dif),sum(dif)/len(dif),sum(1 for d in dif if d>0.5)))
print()
print("="*100)
print("G. AS BONECAS QUE O HUMANO RECEBEU: sao modulares? (catalogo B39/B34/B19/C09/C04)")
print("="*100)
vals=sorted(set(round(v,1) for r in M for v in (r["boneca_left_human"],r["boneca_right_human"])))
MOD=[39.0,34.0,19.0,9.0,4.0]
def combos(x,tol=0.6):
    best=None
    from itertools import product
    # busca gulosa por quantidade minima de pecas ate' 12 pecas
    import heapq
    seen={0.0:[]}
    frontier=[(0.0,[])]
    for _ in range(12):
        nf=[]
        for tot,seq in frontier:
            for m in MOD:
                t=round(tot+m,1)
                if t>x+tol: continue
                if t not in seen:
                    seen[t]=seq+[m]; nf.append((t,seq+[m]))
        frontier=nf
        if not frontier: break
    for t,seq in sorted(seen.items(),key=lambda kv:(abs(kv[0]-x),len(kv[1]))):
        if abs(t-x)<=tol: return t,seq
    return None,None
c=Counter()
for v in vals:
    if v<=0.5: c["0 (vao encosta na ponta/vizinho)"]+=1; continue
    t,seq=combos(v)
    if t is None: c["NAO modular"]+=1; continue
    key="modular"
    if any(m in (9.0,4.0) for m in seq): key="modular COM compensador"
    c[key]+=1
print("valores distintos de boneca humana:",len(vals))
for k,v in c.most_common(): print("   %-34s %3d"%(k,v))
print("   exemplos:",[ (v,combos(v)[1]) for v in vals[:12] ])
print()
print("="*100)
print("H. O QUE O HUMANO ASSENTOU ENCOSTADO NA LATERAL DO VAO (bloco adjacente, por fiada)")
print("="*100)
adjL=Counter(); adjR=Counter(); joint_err=[]
comp_next=0; tot_jamb=0
for r in M:
    w=refw.get(r["ref_wall"])
    if not w: continue
    t0,t1=r["t_h"][0],r["t_h"][1]
    for row in w["rows"]:
        for b in row["blocks"]:
            if abs(b["t_end_cm"]-t0)<=1.0:
                adjL[b["code"]]+=1; tot_jamb+=1
                if b.get("code") in ("C09","C04","C09_C"): comp_next+=1
            if abs(b["t_start_cm"]-t1)<=1.0:
                adjR[b["code"]]+=1; tot_jamb+=1
                if b.get("code") in ("C09","C04","C09_C"): comp_next+=1
    # junta vertical humana mais proxima de cada lateral
    js=set()
    for row in w["rows"]:
        for b in row["blocks"]:
            js.add(round(b["t_start_cm"],2)); js.add(round(b["t_end_cm"],2))
    if js:
        joint_err.append((min(abs(j-t0) for j in js),min(abs(j-t1) for j in js)))
print("bloco encostado na lateral ESQUERDA do vao:",adjL.most_common())
print("bloco encostado na lateral DIREITA  do vao:",adjR.most_common())
print("total de encostes medidos: %d ; deles compensador (C04/C09): %d (%.1f%%)"%(
    tot_jamb,comp_next,100.0*comp_next/max(tot_jamb,1)))
print()
le=[a for a,b in joint_err]; re_=[b for a,b in joint_err]
print("distancia da lateral do vao ate' a junta vertical humana mais proxima:")
print("   esquerda: max=%.3f cm  media=%.4f | direita: max=%.3f cm  media=%.4f"%(
    max(le),sum(le)/len(le),max(re_),sum(re_)/len(re_)))
print("   (=> a modulacao humana PARA exatamente na lateral do vao; a abertura e' fronteira dura)")
