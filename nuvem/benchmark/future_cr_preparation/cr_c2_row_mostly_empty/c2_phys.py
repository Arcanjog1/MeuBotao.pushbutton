"""CR-C2 2.2 - os +23 sao vazio FISICO novo, ou a mesma geometria contada
em outra unidade? Comparacao em coordenadas GLOBAIS (x,y,z), nunca por
rotulo de parede nem por indice de fiada."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis, model

def gaps_globais(d, bh):
    """Uniao dos trechos MODULAVEIS NAO cobertos, em coordenadas globais,
    por cota z. Independe de como as paredes foram particionadas."""
    occ = analysis.OccupancyIndex(d)
    porz = collections.defaultdict(list)
    for w in d["walls"]:
        dirv, _ = model.direction_of(w["start_cm"], w["end_cm"])
        for r in w.get("rows") or []:
            exp = VC.modulable_intervals(w, r, bh)
            if not exp: continue
            pcs = [(b["t_start_cm"], b["t_end_cm"]) for b in r.get("blocks") or []]
            for iv in exp:
                pcs.extend(occ.foreign_coverage_on_axis(w, r, iv[0], iv[1]))
            pcs = analysis.merge_intervals(pcs, tolerance_cm=analysis.BLOCK_JOINT_CM)
            for iv in exp:
                for a, b in analysis.subtract_intervals(iv, pcs):
                    if b - a < 5.0: continue
                    p0 = (w["start_cm"][0]+dirv[0]*a, w["start_cm"][1]+dirv[1]*a)
                    p1 = (w["start_cm"][0]+dirv[0]*b, w["start_cm"][1]+dirv[1]*b)
                    porz[round(r["elevation_cm"],1)].append(
                        (round(min(p0[0],p1[0]),1), round(min(p0[1],p1[1]),1),
                         round(max(p0[0],p1[0]),1), round(max(p0[1],p1[1]),1)))
    return {z: sorted(set(v)) for z, v in porz.items()}

for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    bh=analysis.block_height_of(C)
    gR, gC = gaps_globais(R,bh), gaps_globais(C,bh)
    nR=sum(len(v) for v in gR.values()); nC=sum(len(v) for v in gC.values())
    setR={(z,s) for z,v in gR.items() for s in v}
    setC={(z,s) for z,v in gC.items() for s in v}
    tot=lambda S: sum(abs(s[2]-s[0])+abs(s[3]-s[1]) for _,s in S)
    print(f"== {proj}")
    print(f"   vazios fisicos (>=5cm): R={nR} C={nC}")
    print(f"   comprimento total de vazio fisico: R={tot(setR):.1f}cm C={tot(setC):.1f}cm  delta={tot(setC)-tot(setR):+.1f}cm")
    print(f"   so' em C (vazio fisico NOVO): {len(setC-setR)}  | so' em R (desapareceu): {len(setR-setC)}")

print("\n### CONTENCAO: cada vazio novo de C esta' dentro de um vazio de R?")
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    bh=analysis.block_height_of(C)
    gR,gC=gaps_globais(R,bh),gaps_globais(C,bh)
    setR={(z,s) for z,v in gR.items() for s in v}; setC={(z,s) for z,v in gC.items() for s in v}
    contidos=[]; fora=[]
    for z,s in sorted(setC-setR):
        ok=any(rs[0]-1<=s[0] and rs[1]-1<=s[1] and s[2]<=rs[2]+1 and s[3]<=rs[3]+1
               for rz,rs in setR if rz==z)
        (contidos if ok else fora).append((z,s))
    print(f"  {proj}: novos={len(setC-setR)} | CONTIDOS num vazio de R={len(contidos)} | FORA (geometria nova)={len(fora)}")
    for z,s in fora[:8]: print(f"      z={z} seg={s}")
