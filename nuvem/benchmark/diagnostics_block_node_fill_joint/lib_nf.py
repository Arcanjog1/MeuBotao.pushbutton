# -*- coding: utf-8 -*-
"""Laboratorio do CR-BLOCK-NODE-FILL-JOINT.

Mede, num unico passe por projeto, TUDO o que o veredito do CR pede:

  - codigos dos validadores (PRISM_*, COVERAGE_*, COMPENSATOR_*, OPENING_*);
  - `alignment_conflicts` / `non_modular` / colisoes / falhas de intersecao
    direto do `solve_result`;
  - censo de `placement_reason` (L/T/X, STANDARD_FILL, OPENING_REPAIR_FILL);
  - censo de codigo de peca (B19/B34/B39/B54/C09/C04);
  - as metricas do CR-BLOCK-01 (same-band forbidden, cross_band forbidden,
    compensadores consecutivos), reusando `diagnostics_block_prisma.metrics`
    - nunca uma reimplementacao;
  - tempo de parede das fases (grafo, solver, validacao).

NAO grava nada em `projects/**` (roda sempre com `write_files=False`) e NAO
toca em nenhum `out_*.json` de outra pasta de diagnostico.
"""

import os
import sys
import time
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_NUVEM = os.path.dirname(_BENCH)
for _p in (_NUVEM, _BENCH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PROJECT_IDS = ("piloto_sintetico_2x2", "torre_easy_lo_r00_tgd",
               "torre_easy_lo_r00_tp1")

# codigos que o veredito do CR nomeia explicitamente
WATCHED_CODES = (
    "PRISM_CONTINUOUS_JOINT", "PRISM_JOINT_STACK",
    "COVERAGE_MISSING_ROW", "COVERAGE_ROW_MOSTLY_EMPTY", "COVERAGE_GAP_IN_ROW",
    "COMPENSATOR_CONSECUTIVE", "COMPENSATOR_EXCESS_IN_RUN",
    "COMPENSATOR_VERTICAL_STRIP",
    "OPENING_BLOCK_INSIDE_DOOR", "OPENING_BLOCK_CROSSES_JAMB",
    "OPENING_MISSING_COUNTER_LINTEL", "POSITION_OVERLAP",
)

PLACEMENT_REASONS = (
    "L_CORNER", "L_CORNER_DEGRADED",
    "T_INTERSECTION_MAIN", "T_INTERSECTION_INCOMING",
    "T_INTERSECTION_INCOMING_DEGRADED", "T_INTERSECTION_DEGRADED_L",
    "X_INTERSECTION", "X_INTERSECTION_DEGRADED",
    "STANDARD_FILL", "OPENING_REPAIR_FILL",
)

PIECE_CODES = ("B39", "B34", "B54", "B19", "C09", "C04")


def _counts(values):
    out = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return out


def measure_project(project_id):
    """Uma medicao completa de UM projeto. Roda o solver DUAS vezes: uma
    pelo `runner` (para os validadores/score) e uma pelo `solver_bridge`
    (para o `solve_result` cru e o censo de pecas) - as duas sao puras."""
    from benchmark import runner
    from benchmark import solver_bridge

    t0 = time.perf_counter()
    input_project = json.load(open(runner.project_paths(project_id)["input"],
                                   "r", encoding="utf-8"))
    t_plan0 = time.perf_counter()
    solver_bridge.plan_from_input(input_project)
    t_plan = time.perf_counter() - t_plan0

    t_solve0 = time.perf_counter()
    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(input_project)
    t_solve = time.perf_counter() - t_solve0

    t_score0 = time.perf_counter()
    run = runner.run_project(project_id, write_files=False)
    t_score = time.perf_counter() - t_score0

    score = run["score"]
    by_code = dict(score.get("findings_by_code") or {})

    candidates = solve_result.get("candidates") or []
    reasons = _counts(c.get("placement_reason") for c in candidates)
    codes = _counts(c.get("logical_code") for c in candidates)

    return {
        "project_id": project_id,
        "codes": {name: by_code.get(name, 0) for name in WATCHED_CODES},
        "all_codes": by_code,
        "score": {
            "success_rate": score.get("success_rate"),
            "critical_errors": score.get("critical_errors"),
            "findings_level_1": score.get("findings_level_1"),
            "findings_level_2": score.get("findings_level_2"),
            "blocks": score.get("blocks"),
            "walls": score.get("walls"),
            "walls_failing": score.get("walls_failing"),
        },
        "solve": {
            "candidates": len(candidates),
            "alignment_conflicts": len(solve_result.get("alignment_conflicts") or []),
            # CR-BLOCK-NODE-FILL-JOINT. So' existe em `per_wall`: propagar a
            # chave ate' o topo do `solve_result` exigiria mexer em
            # `nuvem/core/wall_modeling.py`, fora do escopo deste CR (item 17).
            "node_boundary_conflicts": sum(
                len(entry.get("node_boundary_conflicts") or [])
                for entry in (solve_result.get("per_wall") or [])),
            "non_modular": len(solve_result.get("non_modular") or []),
            "collisions": len(solve_result.get("collisions") or []),
            "intersection_failures": len(solve_result.get("intersection_failures") or []),
            "door_void_violations": len(solve_result.get("door_void_violations") or []),
            "jamb_exceptions": len(solve_result.get("jamb_exceptions") or []),
            "continuity_degraded": len(solve_result.get("continuity_degraded") or []),
        },
        "placement_reasons": {name: reasons.get(name, 0) for name in PLACEMENT_REASONS},
        "placement_reasons_all": reasons,
        "piece_codes": {name: codes.get(name, 0) for name in PIECE_CODES},
        "timing_s": {
            "plan_graph": round(t_plan, 4),
            "solver": round(t_solve, 4),
            "score_and_validators": round(t_score, 4),
            "total": round(time.perf_counter() - t0, 4),
        },
    }


def measure_cr_block_01(project_ids=PROJECT_IDS):
    """same-band forbidden / cross_band forbidden / compensadores
    consecutivos com o instrumento do PROPRIO CR-BLOCK-01."""
    prisma_dir = os.path.join(_BENCH, "diagnostics_block_prisma")
    if prisma_dir not in sys.path:
        sys.path.insert(0, prisma_dir)
    import metrics as prisma_metrics  # noqa: E402
    out = prisma_metrics.measure_all(tuple(project_ids))
    slim = {"totals": out["totals"], "projects": {}}
    for pid, project in out["projects"].items():
        slim["projects"][pid] = {
            "fingerprint": project["fingerprint"]["sha256"][:16],
            "joint_classes": project.get("joint_classes"),
            "forbidden_by_band": project.get("forbidden_by_band"),
            "consecutive_compensator_pairs": project.get("consecutive_compensator_pairs"),
            "blocks_inside_opening": project.get("blocks_inside_opening"),
            "alignment_conflicts": project.get("alignment_conflicts"),
            "collisions": project.get("collisions"),
            "consecutive_compensator_runs_by_len":
                project.get("consecutive_compensator_runs_by_len"),
            "internal_joints_total": project.get("internal_joints_total"),
        }
    return slim


def measure_all(project_ids=PROJECT_IDS):
    return {
        "projects": {pid: measure_project(pid) for pid in project_ids},
        "cr_block_01": measure_cr_block_01(project_ids),
    }


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def out_path(name):
    return os.path.join(_HERE, name)
