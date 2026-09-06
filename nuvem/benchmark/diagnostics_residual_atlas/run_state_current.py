# -*- coding: utf-8 -*-
"""STATE_CURRENT - reexecuta a main atual (solver REAL) sobre os projetos
do corpus e grava, em ATLAS_OUT_DIR:

    <SHORT>/result.json        projeto-resultado (schema do benchmark)
    <SHORT>/findings.json      todos os achados dos validadores
    <SHORT>/score.json         score oficial
    <SHORT>/nodes.json         resumo dos nos L/T/X do grafo
    <SHORT>/solver_extra.json  non_modular / collisions / arm_role_safe_repair / etc.
    state_current_summary.json contagem por codigo, tempos, fingerprint fisico

NAO escreve nada dentro de nuvem/benchmark/projects/ (baseline/score/
reference intactos).

    ATLAS_OUT_DIR=/caminho python3 run_state_current.py [--project ID ...]
"""
import argparse
import json
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402


def _git_head():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_HERE).decode().strip()
    except Exception:
        return None


def _slim_solver_extra(run):
    sr = run["solve_result"]
    extra = {}
    for key in ("non_modular", "collisions", "intersection_failures", "jamb_exceptions",
                "alignment_conflicts", "door_void_violations", "arm_role_safe_repair",
                "dropped_fill_by_course", "error"):
        value = sr.get(key)
        extra[key] = value
    # bond audits: so' o resumo por parede
    audits = {}
    for wall_idx, audit in (sr.get("wall_bond_audits") or {}).items():
        audits[str(wall_idx)] = {
            "ok": audit.get("ok"),
            "penalty": audit.get("penalty"),
            "problems": list(audit.get("problems") or [])[:20],
            "continuous_joints": audit.get("continuous_joints") or [],
            "compensator_strips": audit.get("compensator_strips") or [],
            "half_blocks_near_ties": audit.get("half_blocks_near_ties") or [],
        }
    extra["wall_bond_audits"] = audits
    # per band: quantas fiadas, quantas aberturas ativas
    extra["bands"] = [
        {"course_indices": b.get("course_indices"),
         "n_candidates": len((b.get("result") or {}).get("candidates") or []),
         "n_non_modular": len((b.get("result") or {}).get("non_modular") or []),
         "n_collisions": len((b.get("result") or {}).get("collisions") or [])}
        for b in (sr.get("bands") or [])
    ]
    return extra


def run_one(project_id):
    short = al.SHORT[project_id]
    t_all = time.time()
    input_project = al.load_input(project_id)
    reference = al.load_reference(project_id)
    run = al.cached_run(project_id, force=True)
    project = al.build_result_project(project_id, run)
    findings, score, comparison, eval_s = al.evaluate(project, reference)
    fp, n_pieces = al.physical_fingerprint(run)
    counts = al.counts_by_code(findings)

    al.write_json(al.out_path(short, "result.json"), project)
    al.write_json(al.out_path(short, "findings.json"), findings)
    al.write_json(al.out_path(short, "score.json"), score)
    al.write_json(al.out_path(short, "nodes.json"), al.node_summary(run))
    al.write_json(al.out_path(short, "solver_extra.json"), _slim_solver_extra(run))
    if comparison is not None:
        al.write_json(al.out_path(short, "comparison.json"), comparison)

    fwd, rev = al.wall_pairs(project, reference)
    al.write_json(al.out_path(short, "wall_pairs.json"), {"solver_to_human": fwd,
                                                          "human_to_solver": rev})
    summary = {
        "project_id": project_id,
        "walls": len(project["walls"]),
        "blocks": al.model.count_blocks(project),
        "physical_pieces": n_pieces,
        "physical_fingerprint": fp,
        "counts_by_code": counts,
        "solver_seconds": round(run["solver_seconds"], 2),
        "evaluate_seconds": round(eval_s, 2),
        "total_seconds": round(time.time() - t_all, 2),
        "num_courses": run["num_courses"],
        "n_nodes": len(run["nodes"] or []),
        "n_bands": len(run["solve_result"].get("bands") or []),
        "solver_signals": project["metadata"].get("solver_signals"),
        "arm_role_safe_repair": {
            k: len(v or []) for k, v in
            (run["solve_result"].get("arm_role_safe_repair") or {}).items()},
        "human_walls": len((reference or {}).get("walls") or []),
        "matched_pairs": len(fwd),
    }
    print(json.dumps(summary, indent=1, sort_keys=True))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", action="append", default=None)
    args = parser.parse_args(argv)
    ids = tuple(args.project) if args.project else al.PROJECT_IDS
    summaries = {}
    for pid in ids:
        summaries[al.SHORT[pid]] = run_one(pid)
    payload = {"git_head": _git_head(), "python": sys.version, "projects": summaries,
               "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    al.write_json(al.out_path("state_current_summary.json"), payload)
    print("OUT_DIR:", al.OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
