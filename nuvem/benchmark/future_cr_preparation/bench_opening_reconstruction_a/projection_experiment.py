# -*- coding: utf-8 -*-
"""PROJECAO (nao aplicada) do efeito da CR-A no SOLVER, via CR-B.

A CR-A corrige o DETECTOR. Como `input.json`/`reference.json` estao
CONGELADOS, o solver dos 3 projetos nao muda (STATE_A == STATE_B, medido).
O efeito so' chega ao solver quando o gabarito for REGERADO - o que e' a
CR-B e exige autorizacao humana explicita.

Este script MEDE essa projecao sem aplicar nada: copia o projeto para um
diretorio temporario, reescreve SO' as bordas `t_start_cm`/`t_end_cm` das
aberturas ja' existentes do `input.json` com o CONSENSO que o detector
corrigido calcula sobre a geometria do `reference.json`, e roda o solver.
Nenhuma abertura e' criada, apagada ou movida de parede; nenhum arquivo
oficial e' tocado; nenhuma parede e' dividida (isso e' decisao da CR-B).

So' o TP1 entra: o `input.json` do TGD carrega aberturas `measured` do
Revit e, por regra da CR-A, aberturas medidas sao PRESERVADAS.

Uso:  python3 projection_experiment.py [--project torre_easy_lo_r00_tp1]
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

from nuvem.benchmark import runner  # noqa: E402
from nuvem.core.engine import opening_audit  # noqa: E402

MATCH_TOL_CM = 0.5


def _courses_of(wall):
    by_z = {}
    for r in wall.get("rows") or []:
        bucket = by_z.setdefault(r.get("elevation_cm"), [])
        for b in r.get("blocks") or []:
            bucket.append((b["t_start_cm"], b["t_end_cm"], b.get("type_name")))
    return [(z, iv) for z, iv in sorted(by_z.items())]


def _fingerprint(project):
    parts = []
    for wall in sorted(project.get("walls") or [], key=lambda w: w["id"]):
        for row in sorted(wall.get("rows") or [], key=lambda r: r["row"]):
            for block in sorted(row.get("blocks") or [],
                                key=lambda b: (b["t_start_cm"], b["t_end_cm"])):
                parts.append("%s|%s|%d|%.3f|%.3f" % (
                    wall["id"], block.get("code"), row["row"],
                    block["t_start_cm"], block["t_end_cm"]))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12], len(parts)


def build_projected_input(project_id):
    base = os.path.join(runner.PROJECTS_DIR, project_id)
    with open(os.path.join(base, "input.json"), encoding="utf-8") as handle:
        data = json.load(handle)
    with open(os.path.join(base, "reference.json"), encoding="utf-8") as handle:
        ref = json.load(handle)

    consensus_by_wall = {}
    for wall in ref.get("walls") or []:
        consensus_by_wall[wall["id"]] = opening_audit.detect_wall_openings_from_courses(
            _courses_of(wall))

    changed, untouched, unmatched, measured = [], 0, [], 0
    for wall in data.get("walls") or []:
        detected = consensus_by_wall.get(wall["id"]) or []
        for op in wall.get("openings") or []:
            if op.get("confidence") == "measured" or op.get("source_element_id"):
                measured += 1
                continue                       # abertura MEDIDA e' preservada
            hit = None
            for det in detected:
                elo, ehi = det["x_range_envelope"]
                if (abs(elo - op["t_start_cm"]) <= MATCH_TOL_CM
                        and abs(ehi - op["t_end_cm"]) <= MATCH_TOL_CM):
                    hit = det
                    break
            if hit is None:
                unmatched.append((wall["id"], op["t_start_cm"], op["t_end_cm"]))
                continue
            lo, hi = hit["x_range"]
            if (lo, hi) == (op["t_start_cm"], op["t_end_cm"]):
                untouched += 1
                continue
            changed.append({
                "wall": wall["id"],
                "de": [op["t_start_cm"], op["t_end_cm"]],
                "para": [lo, hi],
                "jamb_spread_cm": hit["jamb_spread_cm"],
                "opening_provenance": hit["opening_provenance"],
            })
            op["t_start_cm"], op["t_end_cm"] = lo, hi
            op["width_cm"] = hi - lo
    return data, {"alteradas": changed, "inalteradas": untouched,
                  "medidas_preservadas": measured, "sem_par": unmatched}


def run_with_input(project_id, payload):
    tmp = tempfile.mkdtemp(prefix="bench_openrec_a_")
    try:
        dst = os.path.join(tmp, project_id)
        shutil.copytree(os.path.join(runner.PROJECTS_DIR, project_id), dst)
        if payload is not None:
            with open(os.path.join(dst, "input.json"), "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
        original_projects, original_reports = runner.PROJECTS_DIR, runner.REPORTS_DIR
        reports_tmp = os.path.join(tmp, "reports")
        os.makedirs(reports_tmp, exist_ok=True)
        runner.PROJECTS_DIR, runner.REPORTS_DIR = tmp, reports_tmp
        try:
            return runner.run_project(project_id, write_files=False)
        finally:
            runner.PROJECTS_DIR, runner.REPORTS_DIR = original_projects, original_reports
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="torre_easy_lo_r00_tp1")
    args = parser.parse_args()
    proj = args.project

    projected, summary = build_projected_input(proj)
    print("aberturas alteradas=%d  inalteradas=%d  medidas preservadas=%d  sem par=%d"
          % (len(summary["alteradas"]), summary["inalteradas"],
             summary["medidas_preservadas"], len(summary["sem_par"])))
    if summary["medidas_preservadas"]:
        print("  (aberturas MEDIDAS nao sao tocadas - regra da CR-A)")

    out = {"resumo_da_projecao": summary}
    for label, payload in (("OFICIAL", None), ("PROJETADO", projected)):
        outcome = run_with_input(proj, payload)
        digest, pieces = _fingerprint(outcome["result"])
        counts = collections.Counter(f["code"] for f in outcome["findings"])
        out[label] = {"fingerprint": digest, "pecas": pieces,
                      "criticos": outcome["score"].get("critical_errors"),
                      "counts": dict(counts)}
        print("%-10s fingerprint=%s pecas=%d criticos=%s"
              % (label, digest, pieces, outcome["score"].get("critical_errors")))

    print("\ncodigo                                 OFICIAL  PROJ   delta")
    for code in sorted(set(out["OFICIAL"]["counts"]) | set(out["PROJETADO"]["counts"])):
        a = out["OFICIAL"]["counts"].get(code, 0)
        b = out["PROJETADO"]["counts"].get(code, 0)
        if a != b:
            print("  %-36s %5d %5d  %+d" % (code, a, b, b - a))
    path = os.path.join(HERE, "projection_%s.json" % proj)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=1, sort_keys=True)
    print("\nescrito:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
