import sys, os, json
from collections import Counter, defaultdict
root = os.path.abspath(sys.argv[1]); version = None if sys.argv[2] == "-" else sys.argv[2]
sys.path.insert(0, os.path.join(root, "nuvem")); sys.path.insert(0, os.path.join(root, "tests"))
from benchmark import runner
run = runner.run_project("torre_easy_lo_r00_tgd", write_files=False, version=version)
key_of = dict((w["id"], w["key"]) for w in run["result"]["walls"])
rows = defaultdict(list)
for f in run["findings"]:
    if f["code"].startswith("COVERAGE"):
        rows[f["code"]].append([key_of.get(f.get("wall"), "?"), f.get("row")])
json.dump({"codes": dict(Counter(f["code"] for f in run["findings"])), "coverage_rows": rows}, open(sys.argv[3], "w"))
print("ok")
