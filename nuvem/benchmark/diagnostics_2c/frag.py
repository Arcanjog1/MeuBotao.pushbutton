import json,os,math,statistics
from collections import Counter,defaultdict
BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"; OUT=os.environ["DIAG_OUT"]
L=lambda n: json.load(open(os.path.join(BASE,n),encoding="utf-8"))
snap=L("wall_modeling_snapshot.json"); ref=L("reference.json")
walls=snap["walls"]
def blen(w):
    b=w["before_extension"]; return math.hypot(b["end_cm"][0]-b["start_cm"][0],b["end_cm"][1]-b["start_cm"][1])
BINS=[(0,20),(20,50),(50,100),(100,200),(200,400),(400,1e9)]
def dist(vals,label):
    print("---",label,"n=%d total=%.1f cm"%(len(vals),sum(vals)))
    for a,b in BINS:
        c=[v for v in vals if a<=v<b]
        print("   %5.0f-%-5s cm : %3d  (%.1f%%)  soma %.0f cm"%(a,("%.0f"%b if b<1e8 else "inf"),len(c),100.0*len(c)/len(vals),sum(c)))
dist([w["length_cm"] for w in walls],"167 walls DEPOIS de extend_wall_ends_to_junctions")
dist([blen(w) for w in walls],"167 walls ANTES da extensao")
dist([w["length_cm"] for w in ref["walls"]],"97 walls do GABARITO humano")
print()
print("=== fragmentos curtos (<50 cm depois da extensao) ===")
short=[w for w in walls if w["length_cm"]<50]
short.sort(key=lambda w:w["length_cm"])
for w in short:
    print("idx=%-4d len=%7.2f (antes %7.2f) ang=%6.1f key=%s locked=%s"%(
        w["index"],w["length_cm"],blen(w),w["angle_deg"],w["key"],w["locked_ends"]))
print()
print("=== faixa 8-16 cm ===")
for w in walls:
    if 8.0<=w["length_cm"]<=16.0: print(w["index"],round(w["length_cm"],2),w["key"])
print()
# colineares vizinhas dos curtos
def axis_key(w):
    a=round(w["angle_deg"]%180.0,1)
    sx,sy=w["start_cm"];ex,ey=w["end_cm"]
    if abs(a-90.0)<0.5: return ("V",round((sx+ex)/2.0,1))
    if a<0.5 or abs(a-180)<0.5: return ("H",round((sy+ey)/2.0,1))
    return ("O",round(a,1))
groups=defaultdict(list)
for w in walls: groups[axis_key(w)].append(w)
print("=== vizinhas COLINEARES dos fragmentos < 50 cm (mesmo eixo) ===")
for w in short:
    k=axis_key(w); sib=[x for x in groups[k] if x["index"]!=w["index"]]
    sx,sy=w["start_cm"];ex,ey=w["end_cm"]
    ux,uy=(ex-sx)/w["length_cm"],(ey-sy)/w["length_cm"]
    def proj(p): return (p[0]-sx)*ux+(p[1]-sy)*uy
    near=[]
    for x in sib:
        t0,t1=sorted((proj(x["start_cm"]),proj(x["end_cm"])))
        gap = t0-w["length_cm"] if t0>w["length_cm"] else (0.0-t1 if t1<0 else 0.0)
        near.append((round(gap,2),x["index"],round(x["length_cm"],1),round(t0,1),round(t1,1)))
    near.sort(key=lambda z: abs(z[0]))
    print(" idx %-4d len %6.2f | vizinhas: %s"%(w["index"],w["length_cm"],near[:4]))
