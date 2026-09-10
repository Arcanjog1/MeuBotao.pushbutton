"""Um vazio CONTIDO num vazio anterior nao e', por isso, falso.
Testa se todo vazio fisico continua DETECTADO - e por qual codigo."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis, model
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
  for st,fn in (("R","reference_roundtrip.json"),("C","reference_candidate.json")):
    d=json.load(open(os.path.join(out,proj,fn))); bh=analysis.block_height_of(d)
    occ=analysis.OccupancyIndex(d)
    vazios=set(); comp=0.0
    for w in d["walls"]:
        dirv,_=model.direction_of(w["start_cm"],w["end_cm"])
        for r in w.get("rows") or []:
            exp=VC.modulable_intervals(w,r,bh)
            if not exp: continue
            pcs=[(b["t_start_cm"],b["t_end_cm"]) for b in r.get("blocks") or []]
            for iv in exp: pcs.extend(occ.foreign_coverage_on_axis(w,r,iv[0],iv[1]))
            pcs=analysis.merge_intervals(pcs, tolerance_cm=analysis.BLOCK_JOINT_CM)
            for iv in exp:
                for a,b in analysis.subtract_intervals(iv,pcs):
                    if b-a<5.0: continue
                    vazios.add((w["id"],r["row"],round(a,1),round(b,1))); comp+=b-a
    fs=VC.validate(d)
    gaps={(f["wall"],f["row"],round(f["gap_t_cm"][0],1),round(f["gap_t_cm"][1],1))
          for f in fs if f["code"]=="COVERAGE_GAP_IN_ROW"}
    c=collections.Counter(f["code"] for f in fs)
    print(f"  {proj} {st}: vazios fisicos>=5cm={len(vazios)} ({comp:.0f}cm) | "
          f"GAP_IN_ROW={c['COVERAGE_GAP_IN_ROW']} | vazios SEM achado GAP={len(vazios-gaps)}")
