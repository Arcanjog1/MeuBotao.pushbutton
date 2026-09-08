"""FASE 3 - G12/G16 e demais hard gates: delta R->C por IDENTIDADE FISICA."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark import runner as _r
from nuvem.benchmark.validators import (validate_wall_coverage, validate_junctions,
    validate_prism, validate_openings, validate_compensators, validate_block_positions)
MODS=[validate_wall_coverage, validate_junctions, validate_prism,
      validate_openings, validate_compensators, validate_block_positions]
def todos(d):
    f=[]
    for m in MODS:
        try: f.extend(m.validate(d))
        except Exception as e: f.append({"code":"ERRO_"+m.__name__.split(".")[-1],"wall":None,"detail":str(e)})
    return f
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    cR=collections.Counter(x["code"] for x in todos(R))
    cC=collections.Counter(x["code"] for x in todos(C))
    print(f"===== {proj} (delta STATE_R -> STATE_C) =====")
    for c in sorted(set(cR)|set(cC)):
        d=cC[c]-cR[c]
        print(f"   {c:36s} R={cR[c]:5d} C={cC[c]:5d} delta={d:+5d}{'   <<<' if d else ''}")
