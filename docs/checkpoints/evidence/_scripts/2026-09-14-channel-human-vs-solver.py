# -*- coding: utf-8 -*-
"""HUMANO x SOLVER CHANNEL (offline) - BUTANTA 1o PAV, 34 paredes / 44 vaos, com o
comparador ENDURECIDO (channel_strict_compare.py, auditoria 2026-09-14).
Mesma ordem de paredes da bancada (2026-09-14-channel-bench.py).
Uso: py -3 2026-09-14-channel-human-vs-solver.py [-v]
"""
import json
import os
import sys

import channel_bench_common as cb
from channel_strict_compare import StrictComparator
from core.engine import opening_reinforcement as orf

m = cb.m
masonry, ops = cb.load_inputs()
masonry = sorted(masonry, key=lambda w: (round(float(w["p0_cm"][0]), 1), round(float(w["p0_cm"][1]), 1),
                                         round(float(w["p1_cm"][0]), 1), round(float(w["p1_cm"][1]), 1)))
ctx = cb.build(masonry, ops)
res = cb.solve(ctx, opening_reinforcement_strategy="CHANNEL")
walls_json = dict((w["id"], w) for w in json.load(open(os.path.join(cb.EV, "2026-09-10-butanta-test-walls.json"),
                                                       encoding="utf-8"))["walls"])
human = json.load(open(os.path.join(cb.EV, "2026-09-14-channel-human-runs.json"), encoding="utf-8"))["records"]
seq = json.load(open(os.path.join(cb.EV, "2026-09-10-butanta-human-sequences.json"), encoding="utf-8"))
cmp_ = StrictComparator(m, orf, ctx["walls"], ctx["nodes"], res, ctx["ids"], walls_json, human, seq)
out = cmp_.compare(ctx["opening_ids"])
rein = res["opening_reinforcement"]
out["validation"] = rein["validation"]["counts"]
out["findings"] = {}
for f in rein["findings"]:
    key = "%s:%s" % (f["code"], f.get("classification"))
    out["findings"][key] = out["findings"].get(key, 0) + 1
out["channel_tie_parity_trials"] = res.get("channel_tie_parity_trials")
json.dump(out, open(os.path.join(cb.EV, "2026-09-14-channel-human-vs-solver.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False, default=str)
print(json.dumps({"summary": out["summary"], "by_role": out["by_role"]}, indent=1))
if "-v" in sys.argv:
    for r in out["rows"]:
        if r["classification"] not in ("EXACT_MATCH", "PHYSICALLY_EQUIVALENT"):
            print(r["opening_id"], r["role"], r["classification"], r["reasons"], r.get("human_support"),
                  r.get("solver_support_effective"), r.get("joint_coincidences"), r.get("node_parity"))
