# -*- coding: utf-8 -*-
"""CROSS AUDIT — roda os MESMOS censos da CONTA 2 (mesma biblioteca, mesmas
tolerâncias, mesmas classificações, mesmos projetos, mesmo método de
fingerprint) contra o código desta branch (`claude/block-01-cross-audit`,
que é o `CR-BLOCK-01` + as ferramentas da CONTA 2 mescladas por cima).

**NADA aqui reimplementa medição.** Este script só importa
`lib_audit.py` e os `run_*_census.py` já existentes em
`nuvem/benchmark/diagnostics_block_audit/` (trazidos da CONTA 2 por
merge, não tocados) e roda as mesmas funções `census(run_data)` — a única
diferença é o destino do JSON (`cross_audit/out_block01_*.json`, para não
sobrescrever os `out_*.json` que são a medição da MAIN).

Contrato: comparado item a item com `run_full_census.py`, este arquivo
não pode ter NENHUMA lógica de classificação/tolerância própria — se
algo aqui parecer estar "decidindo" uma regra, é bug de escopo.
"""
import datetime
import hashlib
import os
import sys
import time

_CROSS_AUDIT_DIR = os.path.dirname(os.path.abspath(__file__))
_LAB_DIR = os.path.dirname(_CROSS_AUDIT_DIR)  # nuvem/benchmark/diagnostics_block_audit
if _LAB_DIR not in sys.path:
    sys.path.insert(0, _LAB_DIR)

import lib_audit as A  # mesma biblioteca da CONTA 2, não modificada
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


def _write_json(name, payload):
    path = os.path.join(_CROSS_AUDIT_DIR, name)
    return A.write_json(path, payload)


def _secondary_projects_full(project_ids):
    """Roda o censo COMPLETO (não só o resumo) em todos os projetos
    pedidos - usado para a agregação cross-project (seção 5 da missão,
    comparável à agregação de 275 paredes/3 projetos que a CONTA 1
    reportou)."""
    out = {}
    for project_id in project_ids:
        run_data = A.run_solver(project_id)
        out[project_id] = {
            "run_data_summary": {
                "n_walls": len(run_data["walls_to_create"]),
                "elapsed_s": round(run_data["elapsed_s"], 3),
            },
            "course_bond_prism": run_course_bond_census.census(run_data),
            "special_blocks": run_special_block_census.census(run_data),
            "intersections_l_t_x": run_intersection_census.census(run_data),
            "openings": run_opening_census.census(run_data),
            "coverage_and_performance": run_coverage_census.census(run_data),
        }
    return out


def main():
    t0 = time.time()
    print("[cross-audit] rodando os censos da CONTA 2, sem alterar logica, "
          "sobre o codigo desta branch (CR-BLOCK-01 + ferramentas mescladas)...")

    per_project = _secondary_projects_full(A.PROJECT_IDS)

    print("[cross-audit] censo de determinismo (projeto principal)...")
    determinism = run_determinism_census.census(A.PRIMARY_PROJECT_ID)

    # --- agregado cross-project (comparavel ao "275 paredes / 3 projetos"
    # que a CONTA 1 reportou como baseline do CR-BLOCK-01) -----------------
    agg = {
        "n_walls_total": 0,
        "n_pieces_total": 0,
        "non_modular_segments_total": 0,
        "walls_not_modulated_total": 0,
        "door_void_violations_total": 0,
        "alignment_conflicts_total": 0,
        "jamb_exceptions_total": 0,
        "prism_suspect_continuous_vertical_joint_total": 0,
        "prism_pairs_measured_total": 0,
        "c09_total": 0, "c09_runs2plus_total": 0,
        "c04_total": 0, "c04_runs2plus_total": 0,
        "b19_total": 0,
        "collisions_total": 0,
        "intersection_failures_total": 0,
    }
    for project_id, data in per_project.items():
        agg["n_walls_total"] += data["run_data_summary"]["n_walls"]
        cov = data["coverage_and_performance"]
        agg["n_pieces_total"] += cov["performance"]["total_materialized_pieces"]
        agg["walls_not_modulated_total"] += cov["walls_not_modulated_at_all"]
        op = data["openings"]
        agg["non_modular_segments_total"] += op["solver_reported"]["non_modular_segments"]
        agg["door_void_violations_total"] += op["solver_reported"]["door_void_violations"]
        agg["alignment_conflicts_total"] += op["solver_reported"]["alignment_conflicts"]
        agg["jamb_exceptions_total"] += op["solver_reported"]["jamb_exceptions"]
        cb = data["course_bond_prism"]
        agg["prism_suspect_continuous_vertical_joint_total"] += (
            cb["joint_coincidence"]["suspect_continuous_vertical_joint"])
        agg["prism_pairs_measured_total"] += cb["pairs_of_consecutive_courses_measured"]
        sb = data["special_blocks"]
        agg["c09_total"] += sb["C09"]["total"]
        agg["c09_runs2plus_total"] += sb["C09"]["consecutive_2plus_runs"]
        agg["c04_total"] += sb["C04"]["total"]
        agg["c04_runs2plus_total"] += sb["C04"]["consecutive_2plus_runs"]
        agg["b19_total"] += sb["B19"]["total"]
        ix = data["intersections_l_t_x"]
        agg["collisions_total"] += ix["_meta"]["total_collisions"]
        agg["intersection_failures_total"] += ix["_meta"]["total_intersection_failures"]

    consolidated = {
        "provenance": {
            "generated_at": datetime.datetime.now().isoformat(),
            "branch": "claude/block-01-cross-audit (CR-BLOCK-01 + ferramentas da CONTA 2)",
            "engine_file": A.engine().__file__,
            "engine_sha256": _engine_sha256(),
            "projects": list(per_project.keys()),
            "total_wall_time_s": None,
        },
        "per_project": per_project,
        "cross_project_aggregate": agg,
        "determinism_primary_project": determinism,
    }
    consolidated["provenance"]["total_wall_time_s"] = round(time.time() - t0, 1)

    _write_json("out_block01_full_census.json", consolidated)
    print()
    print("[cross-audit] out_block01_full_census.json escrito. tempo total: %.1fs"
          % (time.time() - t0))
    print("[cross-audit] agregado cross-project:")
    for k, v in agg.items():
        print("   ", k, "=", v)
    print("[cross-audit] determinismo:", determinism["distinct_fingerprints"],
          "fingerprints distintos, deterministic=", determinism["deterministic"])
    return consolidated


if __name__ == "__main__":
    main()
