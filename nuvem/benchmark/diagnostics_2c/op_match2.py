# -*- coding: utf-8 -*-
"""Casamento ESTRITO INPUT x HUMANO + decomposicao longitudinal/perpendicular,
limites da abertura, bonecas e classificacao. LEITURA APENAS."""
import json, math, os, statistics
from collections import Counter, defaultdict

BASE="nuvem/benchmark/projects/torre_easy_lo_r00_tgd"
OUT=os.environ["DIAG_OUT"]
L=lambda n: json.load(open(os.path.join(BASE,n),encoding="utf-8"))
inp=L("input_real.json"); ref=L("reference.json"); snap=L("wall_modeling_snapshot.json"); audit=L("unassigned_openings_audit.json")
unassigned={o["element_id"] for o in audit["openings"]}

human=[]
for w in ref["walls"]:
    sx,sy=w["start_cm"]; ex,ey=w["end_cm"]; ln=math.hypot(ex-sx,ey-sy); ux,uy=(ex-sx)/ln,(ey-sy)/ln
    for o in w["openings"]:
        t0,t1=o["t_start_cm"],o["t_end_cm"]; tc=0.5*(t0+t1)
        human.append(dict(id=o["id"],wall=w["id"],wkey=w["key"],ws=[sx,sy],we=[ex,ey],ln=ln,u=[ux,uy],
                          angle=w["angle_deg"],t0=t0,t1=t1,c=[sx+ux*tc,sy+uy*tc],w=o["width_cm"],
                          sill=o["sill_cm"],head=o["head_cm"],kind=o["kind"],
                          junc=w["junctions"],sibs=w["openings"]))

# criterio ESTRITO: mesma reta (|perp|<=15), deslocamento longitudinal <=60,
# largura compativel (|dw| <= 20 cm)
cands=[]
for i,io in enumerate(inp["openings"]):
    cx,cy=io["center_cm"]
    for j,h in enumerate(human):
        ux,uy=h["u"]; dx=h["c"][0]-cx; dy=h["c"][1]-cy
        along=dx*ux+dy*uy; perp=-dx*uy+dy*ux
        if abs(perp)>15.0 or abs(along)>60.0: continue
        if abs(h["w"]-io["width_cm"])>20.0: continue
        cands.append((abs(along)+abs(perp)*0.5+abs(h["w"]-io["width_cm"])*0.1,i,j,along,perp))
cands.sort()
mi={};mj={}
for score,i,j,along,perp in cands:
    if i in mi or j in mj: continue
    mi[i]=(j,along,perp); mj[j]=i

rows=[]
for i,io in enumerate(inp["openings"]):
    cx,cy=io["center_cm"]
    r=dict(input_id=io["element_id"],cx=round(cx,3),cy=round(cy,3),w_in=io["width_cm"],
           sill_in=io["sill_cm"],head_in=io["head_cm"],
           assigned_by_wm=io["element_id"] not in unassigned)
    if i not in mi:
        r["status"]="NO_HUMAN_COUNTERPART"; rows.append(r); continue
    j,along,perp=mi[i]; h=human[j]; ux,uy=h["u"]
    tin_c=(cx-h["ws"][0])*ux+(cy-h["ws"][1])*uy
    tin0=tin_c-io["width_cm"]/2.0; tin1=tin_c+io["width_cm"]/2.0
    d0=h["t0"]-tin0; d1=h["t1"]-tin1
    r.update(status="MATCHED",human_id=h["id"],ref_wall=h["wall"],ref_wall_key=h["wkey"],
             ref_wall_len=round(h["ln"],2),angle=h["angle"],kind=h["kind"],
             hx=round(h["c"][0],3),hy=round(h["c"][1],3),
             dx=round(h["c"][0]-cx,4),dy=round(h["c"][1]-cy,4),
             along=round(along,4),perp=round(perp,4),
             w_h=h["w"],sill_h=h["sill"],head_h=h["head"],
             dw=round(h["w"]-io["width_cm"],4),dsill=round(h["sill"]-io["sill_cm"],3),
             dhead=round(h["head"]-io["head_cm"],3),
             t_in=[round(tin0,3),round(tin1,3)],t_h=[round(h["t0"],3),round(h["t1"],3)],
             d_start=round(d0,4),d_end=round(d1,4),human_idx=j)
    rows.append(r)

# ---- classificacao dos limites -----------------------------------------
NOISE=0.5   # piso de ruido, cm (ver secao 7)
for r in rows:
    if r["status"]!="MATCHED": r["boundary_class"]="NA"; continue
    d0,d1=r["d_start"],r["d_end"]
    if abs(d0)<=NOISE and abs(d1)<=NOISE: r["boundary_class"]="NO_CHANGE"
    elif abs(d0-d1)<=NOISE: r["boundary_class"]="TRANSLATION"
    elif abs(d0+d1)<=NOISE: r["boundary_class"]="WIDTH_CHANGE_SYMMETRIC"
    else: r["boundary_class"]="WIDTH_CHANGE"
    if abs(r["dsill"])>NOISE or abs(r["dhead"])>NOISE:
        r["boundary_class"]+= "+Z_CHANGE"

# ---- bonecas: distancia da lateral ate' o fim do trecho util ------------
# trecho util = parede do gabarito; vizinhos = outras aberturas na mesma parede
for r in rows:
    if r["status"]!="MATCHED": continue
    h=human[r["human_idx"]]
    others=sorted([(o["t_start_cm"],o["t_end_cm"]) for o in h["sibs"]
                   if not (abs(o["t_start_cm"]-h["t0"])<1e-6 and abs(o["t_end_cm"]-h["t1"])<1e-6)])
    def bonecas(t0,t1):
        lo=0.0; hi=h["ln"]
        for a,b in others:
            if b<=t0: lo=max(lo,b)
            if a>=t1: hi=min(hi,a)
        return t0-lo, hi-t1
    bl_h,br_h=bonecas(h["t0"],h["t1"])
    bl_i,br_i=bonecas(r["t_in"][0],r["t_in"][1])
    r["boneca_left_human"]=round(bl_h,3); r["boneca_right_human"]=round(br_h,3)
    r["boneca_left_input"]=round(bl_i,3); r["boneca_right_input"]=round(br_i,3)

json.dump(rows,open(os.path.join(OUT,"openings_strict.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)

# ---- relatorios ---------------------------------------------------------
matched=[r for r in rows if r["status"]=="MATCHED"]
nohuman=[r for r in rows if r["status"]!="MATCHED"]
print("INPUT total %d | casados %d | sem contraparte humana %d | humanos sem par %d"%(
    len(rows),len(matched),len(nohuman),len(human)-len(mj)))
print()
BINS=[(0,0.5),(0.5,1),(1,2),(2,5),(5,10),(10,20),(20,50),(50,1e9)]
def dist(rs,label):
    if not rs: print(label,"(vazio)"); return
    v=sorted(abs(r["along"]) for r in rs)
    print("--- %s (n=%d) deslocamento AO LONGO da parede"%(label,len(v)))
    for a,b in BINS:
        c=sum(1 for x in v if a<=x<b)
        if c: print("   %5.1f-%-6s cm : %3d"%(a,("%.1f"%b if b<1e8 else "inf"),c))
    print("   media %.4f mediana %.4f p90 %.4f max %.4f"%(
        statistics.mean(v),statistics.median(v),v[min(int(0.9*len(v)),len(v)-1)],max(v)))
    p=sorted(abs(r["perp"]) for r in rs)
    print("   perp: media %.4f mediana %.4f max %.4f"%(statistics.mean(p),statistics.median(p),max(p)))
dist(matched,"TODOS os casados")
dist([r for r in matched if r["assigned_by_wm"]],"A. atribuidas pelo Wall Modeling")
dist([r for r in matched if not r["assigned_by_wm"]],"B. NAO atribuidas (das 9)")
print()
print("classe de limite:",Counter(r["boundary_class"] for r in matched))
print("sem contraparte humana, por largura:",Counter(r["w_in"] for r in nohuman))
print("sem contraparte, atribuidas pelo WM:",Counter(r["assigned_by_wm"] for r in nohuman))
print()
print("=== as 9 NAO atribuidas, uma a uma ===")
for r in rows:
    if r["assigned_by_wm"]: continue
    if r["status"]=="MATCHED":
        print("%-9s %-9s w=%6.1f  along=%+7.3f perp=%+7.3f dw=%+6.3f dsill=%+5.1f dhead=%+5.1f  %s  parede %s (%.0f cm)"%(
            r["input_id"],r["human_id"],r["w_in"],r["along"],r["perp"],r["dw"],r["dsill"],r["dhead"],
            r["boundary_class"],r["ref_wall"],r["ref_wall_len"]))
    else:
        print("%-9s %-9s w=%6.1f  SEM CONTRAPARTE HUMANA  centro=(%.1f, %.1f)"%(
            r["input_id"],"-",r["w_in"],r["cx"],r["cy"]))
