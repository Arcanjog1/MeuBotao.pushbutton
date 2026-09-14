# -*- coding: utf-8 -*-
"""Corpus V2 (TP1, TGD, piloto) com a regra 30.8 desligada x ligada.
Estrategia None (legado) - mede o efeito da folga residual entre nos no
motor comum. Sem gravar arquivos do benchmark (write_files=False).
Uso: py -3 2026-09-14-residual-absorption-corpus.py <saida.json>
"""
import json
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "nuvem"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

from benchmark import runner  # noqa: E402
from benchmark import solver_bridge  # noqa: E402

eng = solver_bridge.engine()
import core.engine.wall_stepper as ws  # noqa: E402

out = {}
for project_id, version in (("torre_easy_lo_r00_tp1", "v2"), ("torre_easy_lo_r00_tgd", "v2"),
                            ("piloto_sintetico_2x2", None)):
    for flag in (False, True):
        ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED = flag
        eng_ws = sys.modules.get("core.engine.wall_stepper")
        if eng_ws is not None:
            eng_ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED = flag
        t0 = time.time()
        run = runner.run_project(project_id, write_files=False, version=version)
        codes = Counter(f["code"] for f in run["findings"])
        delta = run.get("delta")
        out["%s|%s|%s" % (project_id, version, flag)] = {
            "seconds": round(time.time() - t0, 1), "codes": dict(sorted(codes.items())),
            "blocks": sum(len(r["blocks"]) for w in run["result"]["walls"] for r in w["rows"]),
            "delta_vs_baseline": delta,
        }
        print(project_id, version, flag, round(time.time() - t0, 1), flush=True)
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), indent=1, sort_keys=True)
