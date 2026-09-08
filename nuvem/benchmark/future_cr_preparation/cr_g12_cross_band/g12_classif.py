"""FASE 3 - classificacao das identidades NOVAS do G12."""
import json, sys, os, collections
SC=os.environ["SCR"]; sys.path.insert(0, SC+"/wt/proj")
from nuvem.benchmark import model
def load(p,st): return json.load(open(f"{SC}/solved_s1c1/{p}_{st}_solved.json"))
def prism(d):
    idx={w["id"]:w for w in d["walls"]}; res={}
    for f in d["_findings"]:
        if f["code"]!="PRISM_CONTINUOUS_JOINT": continue
        w=idx[f["wall"]]; dv,_=model.direction_of(w["start_cm"],w["end_cm"])
        t=f["joint_t_cm"]
        pt=(round(w["start_cm"][0]+dv[0]*t,1), round(w["start_cm"][1]+dv[1]*t,1))
        z=[]
        for rk in ("row_a","row_b"):
            rr=[r for r in w["rows"] if r["row"]==f[rk]]
            z.append(round(rr[0]["elevation_cm"],1) if rr else None)
        res.setdefault((pt,tuple(z),w["thickness_cm"]),[]).append((f,w))
    return res
def hum_junta(ref, pt, zs, tol=2.0):
    for w in ref["walls"]:
        dv,_=model.direction_of(w["start_cm"],w["end_cm"])
        for r in w.get("rows") or []:
            if round(r["elevation_cm"],1) not in zs: continue
            for b in r.get("blocks") or []:
                for t in (b["t_start_cm"], b["t_end_cm"]):
                    p=(w["start_cm"][0]+dv[0]*t, w["start_cm"][1]+dv[1]*t)
                    if abs(p[0]-pt[0])<=tol and abs(p[1]-pt[1])<=tol: return True
    return False
for proj in sys.argv[1:]:
    R,C=load(proj,"R"),load(proj,"C")
    ref=json.load(open(f"{SC}/cr_b_candidate/{proj}/reference_candidate.json"))
    refR=json.load(open(f"{SC}/cr_b_candidate/{proj}/reference_roundtrip.json"))
    pR,pC=prism(R),prism(C)
    novas=sorted(k for k in pC if k not in pR)
    # eixos que existem em R (input) -> a parede acusada e' nova?
    eixosR={(tuple(w["start_cm"]),tuple(w["end_cm"]),w["thickness_cm"]) for w in R["walls"]}
    print(f"\n{'='*94}\n{proj}: G12 identidades NOVAS = {len(novas)}")
    print(f"  {'#':>2} {'ponto':>20} {'cotas':>16} {'L parede':>9} {'parede nova?':>12} {'desenc':>7} {'humano tem junta?':>18}")
    cls=collections.Counter(); paredes=collections.Counter()
    for i,k in enumerate(novas,1):
        pt,zs,th=k; f,w=pC[k][0]
        nova_parede=(tuple(w["start_cm"]),tuple(w["end_cm"]),th) not in eixosR
        h=hum_junta(ref,pt,set(zs)); hR=hum_junta(refR,pt,set(zs))
        paredes[(w["length_cm"],tuple(w["start_cm"]))]+=1
        c = "C-unidade nova" if nova_parede else "A-defeito fisico"
        cls[c]+=1
        print(f"  {i:2d} {str(pt):>20} {str(zs):>16} {w['length_cm']:9.1f} {str(nova_parede):>12} {f['stagger_cm']:7.2f}   C={h} R={hR}")
    print(f"  --> paredes envolvidas: {dict(paredes)}")
    print(f"  --> classificacao: {dict(cls)}")
