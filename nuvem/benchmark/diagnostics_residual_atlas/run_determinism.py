# -*- coding: utf-8 -*-
"""DETERMINISMO (item 21): roda cada projeto em PROCESSOS NOVOS com
PYTHONHASHSEED diferentes e compara o fingerprint FISICO (parede, fiada,
codigo, t0, t1, placement_reason) e as contagens por codigo.

    python3 run_determinism.py            (3 sementes x 3 projetos)
    -> determinism.json
"""
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402

CHILD = r'''
import os, sys, json
sys.path.insert(0, %r)
import atlas_lib as al
pid = %r
run = al.run_solver_in_memory(al.load_input(pid))
fp, n = al.physical_fingerprint(run)
project = al.build_result_project(pid, run)
findings, score, comparison, _s = al.evaluate(project, al.load_reference(pid))
print(json.dumps({"fp": fp, "pieces": n, "counts": al.counts_by_code(findings),
                  "seconds": round(run["solver_seconds"], 2),
                  "arm": {k: len(v or []) for k, v in (run["solve_result"].get("arm_role_safe_repair") or {}).items()}}))
'''


def main(argv=None):
    seeds = ("0", "1", "12345", "random")
    out = {}
    for pid in al.PROJECT_IDS:
        out[al.SHORT[pid]] = {}
        for seed in seeds:
            env = dict(os.environ)
            env["PYTHONHASHSEED"] = seed
            env["ATLAS_OUT_DIR"] = al.OUT_DIR
            proc = subprocess.run([sys.executable, "-c", CHILD % (_HERE, pid)], env=env,
                                  capture_output=True, text=True)
            line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}"
            try:
                out[al.SHORT[pid]][seed] = json.loads(line)
            except Exception:
                out[al.SHORT[pid]][seed] = {"error": proc.stderr[-2000:]}
            print(al.SHORT[pid], "seed", seed, out[al.SHORT[pid]][seed].get("fp", "")[:16],
                  out[al.SHORT[pid]][seed].get("pieces"), out[al.SHORT[pid]][seed].get("seconds"))
        fps = set(v.get("fp") for v in out[al.SHORT[pid]].values())
        out[al.SHORT[pid]]["DETERMINISTIC"] = len(fps) == 1
        print("  ->", al.SHORT[pid], "deterministic across seeds:", len(fps) == 1)
    al.write_json(al.out_path("determinism.json"), out)


if __name__ == "__main__":
    main()
