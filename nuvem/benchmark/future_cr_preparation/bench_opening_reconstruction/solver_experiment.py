# -*- coding: utf-8 -*-
"""EXPERIMENTO CONTROLADO no SOLVER (TP1) - nao altera arquivo oficial.

O `input.json` do TP1 carrega as MESMAS aberturas reconstruidas do gabarito
(`confidence=reconstructed`), entao o defeito de reconstrucao chega ao
SOLVER, nao so' a' metrica. Este script copia o projeto para um diretorio
temporario, troca SO' o `input.json` pelo candidato e mede o efeito.

O TGD nao entra: o `input.json` dele tem aberturas `measured` (Revit) e
portanto nao e' afetado.

Uso:  python3 solver_experiment.py [--project torre_easy_lo_r00_tp1]
"""
import argparse
import collections
import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from nuvem.benchmark import runner, validators  # noqa: E402


def _fingerprint(project):
    """Assinatura FISICA do resultado: peca a peca, sem id sequencial."""
    parts = []
    for wall in sorted(project.get("walls") or [], key=lambda w: w["id"]):
        for row in sorted(wall.get("rows") or [], key=lambda r: r["row"]):
            for block in sorted(row.get("blocks") or [],
                                key=lambda b: (b["t_start_cm"], b["t_end_cm"])):
                parts.append("%s|%s|%d|%.3f|%.3f" % (
                    wall["id"], block.get("code"), row["row"],
                    block["t_start_cm"], block["t_end_cm"]))
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]
    return digest, len(parts)


def run_with_input(project_id, input_path):
    tmp = tempfile.mkdtemp(prefix="bench_openrec_")
    try:
        dst = os.path.join(tmp, project_id)
        shutil.copytree(os.path.join(runner.PROJECTS_DIR, project_id), dst)
        shutil.copyfile(input_path, os.path.join(dst, "input.json"))
        # REPORTS_DIR e' separado de PROJECTS_DIR: sem redirecionar os DOIS,
        # a rodada candidata sobrescreve o relatorio oficial em
        # nuvem/benchmark/reports/.
        original_projects = runner.PROJECTS_DIR
        original_reports = runner.REPORTS_DIR
        reports_tmp = os.path.join(tmp, "reports")
        os.makedirs(reports_tmp, exist_ok=True)
        runner.PROJECTS_DIR = tmp
        runner.REPORTS_DIR = reports_tmp
        try:
            outcome = runner.run_project(project_id, write_files=True)
        finally:
            runner.PROJECTS_DIR = original_projects
            runner.REPORTS_DIR = original_reports
        with open(os.path.join(dst, "result.json")) as handle:
            result = json.load(handle)
        return outcome, result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="torre_easy_lo_r00_tp1")
    args = parser.parse_args()
    proj = args.project

    official = os.path.join(runner.PROJECTS_DIR, proj, "input.json")
    candidate = os.path.join(HERE, "candidate_input_%s.json" % proj)
    if not os.path.exists(candidate):
        print("sem candidate_input para %s (input MEDIDO, nao afetado)" % proj)
        return 0

    out = {}
    for label, path in (("ATUAL", official), ("CANDIDATO", candidate)):
        outcome, result = run_with_input(proj, path)
        digest, pieces = _fingerprint(result)
        findings = outcome["findings"]
        counts = collections.Counter(f["code"] for f in findings)
        out[label] = {"fingerprint": digest, "pecas": pieces,
                      "score": {k: outcome["score"].get(k) for k in
                                ("success_rate", "critical_errors",
                                 "findings_level_1", "blocks")},
                      "counts": dict(counts)}
        print("%-10s fingerprint=%s pecas=%d criticos=%s" % (
            label, digest, pieces, outcome["score"].get("critical_errors")))

    codes = sorted(set(out["ATUAL"]["counts"]) | set(out["CANDIDATO"]["counts"]))
    print("\ncodigo                                  ATUAL  CAND   delta")
    for code in codes:
        a = out["ATUAL"]["counts"].get(code, 0)
        c = out["CANDIDATO"]["counts"].get(code, 0)
        if a != c:
            print("  %-36s %5d %5d  %+d" % (code, a, c, c - a))
    with open(os.path.join(HERE, "solver_experiment_%s.json" % proj), "w") as handle:
        json.dump(out, handle, indent=1, sort_keys=True)
    print("\nescrito: solver_experiment_%s.json" % proj)
    return 0


if __name__ == "__main__":
    sys.exit(main())
