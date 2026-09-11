# -*- coding: utf-8 -*-
"""Benchmarks oficiais (TGD e TP1) com TIE_PARITY_LOCAL_SEARCH off x on,
comparados ao baseline salvo - mesmo harness da bisseccao de 2026-09-11.
Nenhum baseline e' regravado (write_files=False)."""
import os
import sys
import time
import json

ROOT = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "nuvem"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from benchmark import runner, scoring  # noqa: E402
import load_script  # noqa: E402

m = load_script.load()
ws = sys.modules["core.engine.wall_stepper"]
for project in ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"):
    base = json.load(open(runner.project_paths(project)["baseline"], encoding="utf-8"))
    for flag in (False, True):
        ws.TIE_PARITY_LOCAL_SEARCH = flag
        t0 = time.time()
        try:
            out = runner.run_project(project, write_files=False)
            delta = scoring.compare_runs(base, out["score"])
            crit = [(r["code"], r["before"], r["after"]) for r in delta["critical"] if r["before"] != r["after"]]
            cats = [(r.get("category"), r.get("before"), r.get("after")) for r in delta["categories"]
                    if r["status"] == scoring.STATUS_REGRESSED]
            print("%-24s paridade=%-5s %5.0fs %-20s criticos=%s regress=%s" % (
                project, flag, time.time() - t0, delta["verdict"], crit, cats), flush=True)
        except Exception as ex:
            print("%-24s paridade=%-5s ERRO %s" % (project, flag, ex), flush=True)
ws.TIE_PARITY_LOCAL_SEARCH = False
print("FIM", flush=True)
