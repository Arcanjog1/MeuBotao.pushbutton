# -*- coding: utf-8 -*-
"""Corpus V2 (TP1, TGD) + piloto no estado do checkout em que roda (estrategia
None - motor legado). Sem gravar arquivos do benchmark.
Uso: py -3 2026-09-14-corpus-v2-state.py <raiz_do_checkout> <saida.json>
"""
import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(ROOT, "nuvem"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from benchmark import runner  # noqa: E402

out = {"root": ROOT}
for project_id, version in (("torre_easy_lo_r00_tp1", "v2"), ("torre_easy_lo_r00_tgd", "v2"),
                            ("piloto_sintetico_2x2", None)):
    t0 = time.time()
    run = runner.run_project(project_id, write_files=False, version=version)
    out["%s|%s" % (project_id, version)] = {
        "seconds": round(time.time() - t0, 1),
        "codes": dict(sorted(Counter(f["code"] for f in run["findings"]).items())),
        "blocks": sum(len(r["blocks"]) for w in run["result"]["walls"] for r in w["rows"]),
        "delta_vs_baseline": run.get("delta"),
    }
    print(project_id, version, round(time.time() - t0, 1), flush=True)
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, sort_keys=True, default=str)
