"""O que E' fisicamente uma 'fiada fora do passo do grid' no corpus?
Mede altura das pecas, codigos e presenca de abertura ativa."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark import analysis
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    d=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    step=analysis.course_step_cm(d); off=analysis.FIRST_COURSE_Z_OFFSET_CM
    cat=d.get("catalog") or {}
    stats={"grid":collections.Counter(),"fora":collections.Counter()}
    alt={"grid":collections.Counter(),"fora":collections.Counter()}
    nfi={"grid":0,"fora":0}
    ab_ativa={"grid":[0,0],"fora":[0,0]}
    for w in d["walls"]:
        bz=float(w.get("base_z_cm") or 0.0)
        for r in w.get("rows") or []:
            rel=r["elevation_cm"]-bz
            g = (abs(rel%step)<1e-6 or abs(rel%step-step)<1e-6
                 or abs((rel-off)%step)<1e-6 or abs((rel-off)%step-step)<1e-6)
            k="grid" if g else "fora"
            nfi[k]+=1
            # abertura ativa nesta cota?
            ativa=any(o["sill_cm"]-1 <= r["elevation_cm"] <= o["head_cm"]+1 for o in w.get("openings") or [])
            ab_ativa[k][0 if ativa else 1]+=1
            for b in r.get("blocks") or []:
                stats[k][b.get("code")]+=1
                h=(cat.get(b.get("code")) or {}).get("height_cm") or b.get("height_cm")
                alt[k][round(float(h or 0),1)]+=1
    print(f"===== {proj} (passo={step}cm)")
    for k in ("grid","fora"):
        tot=sum(alt[k].values())
        print(f"  fiadas {k:5s}: {nfi[k]:5d}  pecas={tot:6d}  com abertura ativa={ab_ativa[k][0]:4d} / sem={ab_ativa[k][1]:4d}")
        print(f"      alturas: {sorted(alt[k].items(), key=lambda x:-x[1])[:6]}")
        print(f"      codigos: {stats[k].most_common(6)}")
