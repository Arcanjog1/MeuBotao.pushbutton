"""O que compoe FISICAMENTE as fiadas acusadas por ROW_MOSTLY_EMPTY?"""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis
from nuvem.benchmark.solver_bridge import SOLVER_KNOWN_CODES
print("SOLVER_KNOWN_CODES =", sorted(SOLVER_KNOWN_CODES))
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
  for st,fn in (("R","reference_roundtrip.json"),("C","reference_candidate.json")):
    d=json.load(open(os.path.join(out,proj,fn)))
    cat=d.get("catalog") or {}; step=analysis.course_step_cm(d); off=analysis.FIRST_COURSE_Z_OFFSET_CM
    idx={w["id"]:w for w in d["walls"]}
    c=collections.Counter()
    for f in VC.validate(d):
        if f["code"]!="COVERAGE_ROW_MOSTLY_EMPTY": continue
        w=idx[f["wall"]]; r=[x for x in w["rows"] if x["row"]==f["row"]][0]
        codes=[b.get("code") for b in r.get("blocks") or []]
        hs={round(float((cat.get(b.get('code')) or {}).get('height_cm') or b.get('height_cm') or 0),1) for b in r.get("blocks") or []}
        sup=[x for x in codes if x in SOLVER_KNOWN_CODES]
        rel=r["elevation_cm"]-float(w.get("base_z_cm") or 0)
        g=(abs(rel%step)<1e-6 or abs(rel%step-step)<1e-6 or abs((rel-off)%step)<1e-6 or abs((rel-off)%step-step)<1e-6)
        if not codes: k="fiada_SEM_bloco"
        elif not sup: k="100%_pecas_NAO_suportadas_pelo_solver"
        elif len(sup)<len(codes): k="mista"
        else: k="100%_pecas_suportadas"
        c[k]+=1
        c["  ..dessas, altura!=19cm"] += (1 if (hs and hs!={19.0}) else 0) if k=="100%_pecas_NAO_suportadas_pelo_solver" else 0
        c["[grid]" if g else "[fora do grid]"]+=1
    print(f"  {proj} {st}: total={sum(v for k,v in c.items() if not k.startswith(('[','  ')))} | {dict(c)}")
