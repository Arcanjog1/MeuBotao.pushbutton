"""Quantos achados ROW_MOSTLY_EMPTY caem em fiada FORA do passo do grid
(faixa de verga/peitoril) x fiada regular?"""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    for st, fn in (("R","reference_roundtrip.json"),("C","reference_candidate.json")):
        d=json.load(open(os.path.join(out,proj,fn)))
        step=analysis.course_step_cm(d); off=analysis.FIRST_COURSE_Z_OFFSET_CM
        idx={w["id"]:w for w in d["walls"]}
        c=collections.Counter()
        for f in VC.validate(d):
            if f["code"]!="COVERAGE_ROW_MOSTLY_EMPTY": continue
            w=idx[f["wall"]]; r=[x for x in w["rows"] if x["row"]==f["row"]][0]
            rel=(r["elevation_cm"]-float(w.get("base_z_cm") or 0.0))
            no_grid = abs((rel % step)) < 1e-6 or abs((rel % step)-step) < 1e-6
            no_grid_off = abs(((rel-off) % step)) < 1e-6 or abs(((rel-off) % step)-step) < 1e-6
            c["grid" if (no_grid or no_grid_off) else "FORA_do_grid"] += 1
        print(f"{proj} {st}: total={sum(c.values())} | {dict(c)}")
