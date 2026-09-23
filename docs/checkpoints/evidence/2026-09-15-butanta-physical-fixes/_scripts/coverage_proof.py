# -*- coding: utf-8 -*-
"""Prova de cobertura por (parede, fiada): cm modulavel descoberto, achados de
cobertura e contagem de pecas por codigo. Nada e' gravado no repo.
uso: coverage_proof.py LABEL [FLAG=VAL,...] [projects=tgd,tp1] [versions=v1,v2]"""
import collections
import importlib
import json
import os
import sys
import time

REPO = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
sys.path.insert(0, os.path.join(REPO, "nuvem"))
sys.path.insert(0, os.path.join(REPO, "tests"))
from benchmark import runner, scoring, analysis  # noqa: E402
from benchmark.validators import validate_wall_coverage as VC  # noqa: E402
from benchmark import model  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
label = sys.argv[1]
flags = {}
projects = ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]
versions = [None, "v2"]
for arg in sys.argv[2:]:
    if arg.startswith("projects="):
        projects = ["torre_easy_lo_r00_" + p for p in arg.split("=")[1].split(",")]
    elif arg.startswith("versions="):
        versions = [None if v == "v1" else v for v in arg.split("=")[1].split(",")]
    else:
        for part in arg.split(","):
            if "=" in part:
                k, v = part.split("=")
                flags[k] = {"True": True, "False": False}.get(v, v)


def apply_flags():
    for modname, mod in list(sys.modules.items()):
        if mod is None:
            continue
        for k, v in flags.items():
            if hasattr(mod, k) and (modname.startswith("core.") or "wall_modeling" in modname):
                setattr(mod, k, v)


def per_wall(project):
    bh = analysis.block_height_of(project)
    occ = analysis.OccupancyIndex(project)
    out = {}
    for wall in project.get("walls") or []:
        rows = {}
        for row in model.rows_sorted(wall):
            expected = VC.modulable_intervals(wall, row, bh)
            exp_len = sum(e - s for s, e in expected)
            pieces = list(VC._covered_intervals(row))
            for iv in expected:
                pieces.extend(occ.foreign_coverage_on_axis(wall, row, iv[0], iv[1]))
            pieces = analysis.merge_intervals(pieces, tolerance_cm=analysis.BLOCK_JOINT_CM)
            span = sum(analysis.interval_overlap_cm(p, iv) for p in pieces for iv in expected)
            rows[str(row["row"])] = [round(exp_len, 1), round(max(0.0, exp_len - span), 1)]
        codes = collections.Counter(b.get("code") for row in wall.get("rows") or [] for b in row.get("blocks") or [])
        out[str(wall["id"])] = {"rows": rows, "codes": dict(codes)}
    return out


res = {"label": label, "flags": flags, "runs": {}}
for project in projects:
    for version in versions:
        from benchmark import solver_bridge
        solver_bridge.engine()
        importlib.import_module("core.engine.small_void_alignment")
        importlib.import_module("core.engine.continuous_modulation")
        apply_flags()
        t0 = time.time()
        paths = runner.project_paths(project, version)
        baseline = json.load(open(paths["baseline"], encoding="utf-8"))
        outcome = runner.run_project(project, write_files=False, version=version)
        delta = scoring.compare_runs(baseline, outcome["score"])
        f_by = collections.defaultdict(list)
        for f in outcome["findings"]:
            f_by[f["code"]].append([f.get("wall"), f.get("row")])
        key = "%s/%s" % (project[-3:], version or "v1")
        res["runs"][key] = {
            "verdict": delta["verdict"],
            "critical_changed": [(r["code"], r["before"], r["after"]) for r in delta["critical"] if r["before"] != r["after"]],
            "categories_changed": [(r["category"], r["before"], r["after"], r["status"]) for r in delta["categories"] if r["before"] != r["after"]],
            "findings": dict(f_by),
            "walls": per_wall(outcome["result"]),
            "seconds": round(time.time() - t0, 1),
        }
        print(key, res["runs"][key]["verdict"], res["runs"][key]["critical_changed"], res["runs"][key]["categories_changed"], flush=True)
json.dump(res, open(os.path.join(HERE, "cov_%s.json" % label), "w", encoding="utf-8"), ensure_ascii=False)
