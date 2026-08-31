# -*- coding: utf-8 -*-
"""Quem roubou a face de cada parede do gabarito que sumiu; e de onde vem
cada fragmento curto (< 50 cm) das 167. SOMENTE LEITURA."""
import json,os,math
from collections import Counter,defaultdict
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; OUT=os.environ["DIAG_OUT"]
LB=lambda n: json.load(open(os.path.join(BASE,n),encoding="utf-8"))
LO=lambda n: json.load(open(os.path.join(OUT,n),encoding="utf-8"))
snap=LB("wall_modeling_snapshot.json"); ref=LB("reference.json")
ML=LO("merged_lines.json"); ACC=LO("accepted.json"); LOST=LO("lost.json")
OWN={int(k):v for k,v in LO("owner.json").items()}
COV=LO("ref_coverage.json"); RAW=LO("raw_lines.json")

def ang(x0,y0,x1,y1): return math.degrees(math.atan2(y1-y0,x1-x0))%180.0
def adiff(a,b):
    d=abs(a-b)%180.0; return min(d,180.0-d)
class Ax:
    def __init__(s,x0,y0,x1,y1):
        s.x0,s.y0,s.x1,s.y1=x0,y0,x1,y1; s.L=math.hypot(x1-x0,y1-y0)
        s.ux,s.uy=((x1-x0)/s.L,(y1-y0)/s.L) if s.L>1e-9 else (1.,0.); s.a=ang(x0,y0,x1,y1)
    def proj(s,p,q): return (p-s.x0)*s.ux+(q-s.y0)*s.uy
    def perp(s,p,q): return -(p-s.x0)*s.uy+(q-s.y0)*s.ux

def pair_axis(i,j):
    xi0,yi0,xi1,yi1,Li=ML[i]; xj0,yj0,xj1,yj1,Lj=ML[j]
    A=Ax(xi0,yi0,xi1,yi1); pj=(A.perp(xj0,yj0)+A.perp(xj1,yj1))/2.0
    ox,oy=-A.uy*pj/2.0, A.ux*pj/2.0
    t0,t1=sorted((A.proj(xj0,yj0),A.proj(xj1,yj1)))
    a,b=max(0.,t0),min(A.L,t1)
    if b<=a: return None
    return (A.x0+A.ux*a+ox,A.y0+A.uy*a+oy,A.x0+A.ux*b+ox,A.y0+A.uy*b+oy)

print("="*100)
print("N/O. POR QUE CADA PAREDE DO GABARITO AUSENTE NAO FOI CRIADA (par perdido -> quem roubou)")
print("="*100)
motivos=Counter(); detalhe=[]
for r in COV:
    if r["cov"]>=0.85 or r["covlost"]<0.5: continue
    A=Ax(r["x0"],r["y0"],r["x1"],r["y1"])
    # melhor par perdido que cobre essa parede
    best=None
    for k,l in enumerate(LOST):
        pa=pair_axis(l["i"],l["j"])
        if not pa: continue
        if adiff(A.a,ang(*pa))>3.0: continue
        pm=(A.perp(pa[0],pa[1])+A.perp(pa[2],pa[3]))/2.0
        if abs(pm)>8.0: continue
        t0,t1=sorted((A.proj(pa[0],pa[1]),A.proj(pa[2],pa[3])))
        ov=min(t1,A.L)-max(t0,0.)
        if ov<=1.0: continue
        sc=ov
        if best is None or sc>best[0]: best=(sc,k,l,pm)
    if best is None: continue
    sc,k,l,pm=best
    li,lj=ML[l["i"]],ML[l["j"]]
    txt=[]
    for who,idx in (("i",l["i"]),("j",l["j"])):
        if idx in OWN:
            a=ACC[OWN[idx]]
            other=a["j"] if a["i"]==idx else a["i"]
            txt.append((who,round(ML[idx][4],2),round(ML[other][4],2),a["d"],a["r"],a.get("len")))
    detalhe.append((r,l,txt,pm))
    # classificar
    thief_short=[t for t in txt if t[2]<20.0]
    if thief_short: motivos["face consumida por linha CURTA (<20 cm)"]+=1
    elif txt:      motivos["face consumida por outro par (parceiro >=20 cm)"]+=1
    else:          motivos["nenhuma das faces consumida (?)"]+=1
    print()
    print("  %-6s L=%7.1f  (%8.1f,%8.1f)->(%8.1f,%8.1f)"%(r["id"],r["L"],r["x0"],r["y0"],r["x1"],r["y1"]))
    print("     par perdido: r=%.4f d=%.3f cm | linha_i len=%8.2f (%8.1f,%8.1f)->(%8.1f,%8.1f)"%(
        l["r"],l["d"],li[4],li[0],li[1],li[2],li[3]))
    print("                                     | linha_j len=%8.2f (%8.1f,%8.1f)->(%8.1f,%8.1f)"%(
        lj[4],lj[0],lj[1],lj[2],lj[3]))
    for who,lenme,lenother,d,rr,cl in txt:
        flag="  <== ROUBO POR FRAGMENTO CURTO" if lenother<20.0 else ""
        print("     linha_%s (%7.2f cm) foi consumida por par com linha de %7.2f cm  d=%6.3f r=%.4f -> parede de %s cm%s"%(
            who,lenme,lenother,d,rr,cl,flag))
print()
print("--- motivos agrupados ---")
for k,v in motivos.most_common(): print("   %-52s %2d"%(k,v))

print()
print("="*100)
print("L. ORIGEM DOS FRAGMENTOS CURTOS (<50 cm) DAS 167 WALLS")
print("="*100)
short=[w for w in snap["walls"] if w["length_cm"]<50.0]
def find_acc(w):
    b=w["before_extension"]; s=b["start_cm"]; e=b["end_cm"]
    best=None
    for k,a in enumerate(ACC):
        if "len" not in a: continue
        d1=math.hypot(a["s"][0]-s[0],a["s"][1]-s[1])+math.hypot(a["e"][0]-e[0],a["e"][1]-e[1])
        d2=math.hypot(a["s"][0]-e[0],a["s"][1]-e[1])+math.hypot(a["e"][0]-s[0],a["e"][1]-s[1])
        d=min(d1,d2)
        if best is None or d<best[0]: best=(d,k)
    return best
tab=[]
for w in sorted(short,key=lambda w:w["length_cm"]):
    r=find_acc(w)
    if r is None or r[0]>2.0:
        print("  idx=%-4d len=%6.2f  -> par NAO localizado (delta=%s)"%(w["index"],w["length_cm"],r and round(r[0],2)))
        continue
    a=ACC[r[1]]; li,lj=ML[a["i"]],ML[a["j"]]
    lo,hi=sorted((li[4],lj[4]))
    tab.append((w["index"],w["length_cm"],lo,hi,a["d"],a["r"],li,lj))
    print("  idx=%-4d len=%6.2f ang=%6.1f | linhas %7.2f x %8.2f cm  d=%6.3f r=%.4f | curta (%8.1f,%8.1f)->(%8.1f,%8.1f)"%(
        w["index"],w["length_cm"],w["angle_deg"],lo,hi,a["d"],a["r"],
        *(li if li[4]<=lj[4] else lj)[:4]))
print()
cc=Counter()
for idx,L,lo,hi,d,rr,li,lj in tab:
    if lo<20 and hi>=100: cc["curta(<20) roubou LONGA(>=100)"]+=1
    elif lo<20 and hi>=50: cc["curta(<20) x media(50-100)"]+=1
    elif lo<20: cc["curta x curta"]+=1
    else: cc["ambas >=20"]+=1
for k,v in cc.most_common(): print("   %-36s %2d"%(k,v))
print()
print("--- distancia perpendicular real dos pares que geraram fragmento curto ---")
print("   ",Counter(round(t[4],1) for t in tab).most_common())

# de onde vem a LINHA CURTA no CAD bruto?
print()
print("=== as linhas curtas (<20 cm) que originaram fragmento: existiam no CAD bruto? ===")
seen=set()
for idx,L,lo,hi,d,rr,li,lj in tab:
    sh=li if li[4]<=lj[4] else lj
    key=tuple(round(v,1) for v in sh[:4])
    if key in seen: continue
    seen.add(key)
    n_raw=0; exemplos=[]
    for x0,y0,x1,y1,rl in RAW:
        if (abs(x0-sh[0])<0.6 and abs(y0-sh[1])<0.6 and abs(x1-sh[2])<0.6 and abs(y1-sh[3])<0.6) or \
           (abs(x1-sh[0])<0.6 and abs(y1-sh[1])<0.6 and abs(x0-sh[2])<0.6 and abs(y0-sh[3])<0.6):
            n_raw+=1; exemplos.append(rl)
    print("   curta len=%6.2f (%8.1f,%8.1f)->(%8.1f,%8.1f)  presente no CAD bruto: %s"%(
        sh[4],sh[0],sh[1],sh[2],sh[3],("SIM (%d, len %s)"%(n_raw,exemplos[:2])) if n_raw else "NAO (nasceu no merge)"))
