"""CR-C2 2.2 - o achado ROW_MOSTLY_EMPTY de C recai sobre regiao FISICA ja'
acusada em R? Mapeia cada achado para os vazios globais da sua fiada."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis, model

def achados_fisicos(d, bh):
    occ = analysis.OccupancyIndex(d); idx = {w["id"]: w for w in d["walls"]}
    saida = []
    for f in VC.validate(d):
        if f["code"] != "COVERAGE_ROW_MOSTLY_EMPTY": continue
        w = idx[f["wall"]]; dirv,_ = model.direction_of(w["start_cm"], w["end_cm"])
        r = [x for x in w["rows"] if x["row"] == f["row"]][0]
        exp = VC.modulable_intervals(w, r, bh)
        pcs = [(b["t_start_cm"], b["t_end_cm"]) for b in r.get("blocks") or []]
        for iv in exp: pcs.extend(occ.foreign_coverage_on_axis(w, r, iv[0], iv[1]))
        pcs = analysis.merge_intervals(pcs, tolerance_cm=analysis.BLOCK_JOINT_CM)
        segs = []
        for iv in exp:
            for a, b in analysis.subtract_intervals(iv, pcs):
                if b-a < 5.0: continue
                p0=(w["start_cm"][0]+dirv[0]*a, w["start_cm"][1]+dirv[1]*a)
                p1=(w["start_cm"][0]+dirv[0]*b, w["start_cm"][1]+dirv[1]*b)
                segs.append((round(min(p0[0],p1[0]),1),round(min(p0[1],p1[1]),1),
                             round(max(p0[0],p1[0]),1),round(max(p0[1],p1[1]),1)))
        saida.append({"z": round(r["elevation_cm"],1), "segs": segs,
                      "L": w["length_cm"], "cov": f["covered_cm"], "mod": f["modulable_cm"]})
    return saida

def cobre(seg, alvo, tol=1.0):
    return (alvo[0]>=seg[0]-tol and alvo[1]>=seg[1]-tol
            and alvo[2]<=seg[2]+tol and alvo[3]<=seg[3]+tol)

for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    bh=analysis.block_height_of(C)
    aR, aC = achados_fisicos(R,bh), achados_fisicos(C,bh)
    segR = collections.defaultdict(list)
    for a in aR:
        for s in a["segs"]: segR[a["z"]].append(s)
    ja, novo = 0, []
    for a in aC:
        if a["segs"] and all(any(cobre(rs,s) for rs in segR[a["z"]]) for s in a["segs"]): ja += 1
        else: novo.append(a)
    print(f"== {proj}: achados R={len(aR)} C={len(aC)} delta={len(aC)-len(aR):+d}")
    print(f"   achados de C cuja regiao fisica JA ERA acusada em R: {ja}")
    print(f"   achados de C sobre regiao fisica NAO acusada em R:   {len(novo)}")
    for a in novo[:10]:
        print(f"      z={a['z']} L_parede={a['L']} coberto={a['cov']} modulavel={a['mod']} segs={a['segs'][:3]}")
