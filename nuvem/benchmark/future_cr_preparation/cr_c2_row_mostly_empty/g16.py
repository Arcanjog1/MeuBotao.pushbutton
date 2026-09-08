import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    res = {}
    for st, fn in (("R","reference_roundtrip.json"), ("C","reference_candidate.json")):
        d = json.load(open(os.path.join(out, proj, fn)))
        res[st] = collections.Counter(f["code"] for f in VC.validate(d))
    codes = sorted(set(res["R"]) | set(res["C"]))
    print(f"== {proj}")
    for c in codes:
        r, k = res["R"][c], res["C"][c]
        flag = "   <<<" if r != k else ""
        print(f"   {c:34s} R={r:5d} C={k:5d} delta={k-r:+d}{flag}")
