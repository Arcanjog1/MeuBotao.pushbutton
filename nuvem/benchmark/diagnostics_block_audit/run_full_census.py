# -*- coding: utf-8 -*-
"""Orquestrador do laboratório de auditoria independente de blocos (CONTA
2). Roda TODOS os censos sobre a MAIN baseline (`main` @
9f3bab41b35f0e2a5f9782583ead8e1ee7755f49, ver docs/archive/BLOCK_MODULATION_AUDIT.md)
e escreve:

  - um `out_<censo>.json` por censo (mesmo arquivo que cada script escreve
    sozinho, para poder rodar um de cada vez durante desenvolvimento);
  - `out_full_census.json` — tudo consolidado, mais metadados de proveniência
    (projeto, SHA do arquivo do motor, timestamp, tempo total).

Roda o SOLVER UMA VEZ para o projeto principal (evita recomputar 5x o
mesmo resultado ~3-4s) e reaproveita `run_data` em todos os censos que só
precisam de uma rodada; o censo de determinismo (que por definição PRECISA
rodar o solver várias vezes, com variações) usa sua própria função
`census(project_id)`.

Projetos secundários (`torre_easy_lo_r00_tp1`, `piloto_sintetico_2x2`)
entram só no resumo comparativo no fim — o censo detalhado usa
`PRIMARY_PROJECT_ID` (o único com input MEDIDO, não reconstruído do
próprio gabarito — ver `nuvem/benchmark/README.md`).
"""
import datetime
import hashlib
import os
import sys
import time

import lib_audit as A

import run_course_bond_census
import run_special_block_census
import run_intersection_census
import run_opening_census
import run_determinism_census
import run_coverage_census


def _engine_sha256():
    module_path = A.engine().__file__
    with open(module_path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _secondary_projects_summary():
    summaries = []
    for project_id in A.PROJECT_IDS:
        if project_id == A.PRIMARY_PROJECT_ID:
            continue
        try:
            run_data = A.run_solver(project_id)
        except Exception as exc:
            summaries.append({"project_id": project_id, "error": repr(exc)})
            continue
        solve_result = run_data["solve_result"]
        n_pieces = sum(1 for _ in A.physical_course_candidates(solve_result))
        summaries.append({
            "project_id": project_id,
            "n_walls": len(run_data["walls_to_create"]),
            "n_pieces_materialized": n_pieces,
            "n_non_modular": len(solve_result.get("non_modular") or []),
            "n_intersection_failures": len(solve_result.get("intersection_failures") or []),
            "elapsed_s": round(run_data["elapsed_s"], 3),
        })
    return summaries


def main():
    t0 = time.time()
    project_id = A.PRIMARY_PROJECT_ID
    print("Rodando solver principal sobre", project_id, "...")
    run_data = A.run_solver(project_id)
    print("  elapsed_s=", round(run_data["elapsed_s"], 3))

    fp, n_pieces = A.project_fingerprint(run_data["walls_to_create"], run_data["solve_result"])

    print("Censo: prisma/fiadas...")
    course_bond = run_course_bond_census.census(run_data)

    print("Censo: C09/C04/B19/B34/B54...")
    special_blocks = run_special_block_census.census(run_data)

    print("Censo: L/T/X...")
    intersections = run_intersection_census.census(run_data)

    print("Censo: aberturas + bloco em vao...")
    openings = run_opening_census.census(run_data)

    print("Censo: paredes nao moduladas + performance...")
    coverage = run_coverage_census.census(run_data)

    print("Censo: determinismo (varias rodadas do solver)...")
    determinism = run_determinism_census.census(project_id)

    print("Rodando projetos secundarios (resumo)...")
    secondary = _secondary_projects_summary()

    consolidated = {
        "provenance": {
            "generated_at": datetime.datetime.now().isoformat(),
            "primary_project_id": project_id,
            "engine_file": A.engine().__file__,
            "engine_sha256": _engine_sha256(),
            "solver_decision_fingerprint_official": (
                "c74c9c1ae0e3f169f76e05fe53c01a858fce0af5b4e9d5f1b86fd71e92d2a316"
                " (REFERENCE_SOLVER_DECISION_FINGERPRINT, tests/solver_bench.py --fingerprint,"
                " referencia - nao recalculado aqui)"),
            "audit_project_fingerprint_baseline": fp,
            "audit_project_pieces_baseline": n_pieces,
            "total_wall_time_s": None,  # preenchido no fim
        },
        "wall_modeling_notes": run_data["notes"],
        "course_bond_prism": course_bond,
        "special_blocks": special_blocks,
        "intersections_l_t_x": intersections,
        "openings": openings,
        "coverage_and_performance": coverage,
        "determinism": determinism,
        "secondary_projects_summary": secondary,
    }
    consolidated["provenance"]["total_wall_time_s"] = round(time.time() - t0, 1)

    A.write_json(A.out_path("out_full_census.json"), consolidated)
    print()
    print("out_full_census.json escrito. tempo total: %.1fs" % (time.time() - t0))
    print("fingerprint do projeto principal (baseline):", fp)
    print("determinismo: distintos=", determinism["distinct_fingerprints"],
          "deterministic=", determinism["deterministic"])
    return consolidated


if __name__ == "__main__":
    main()
