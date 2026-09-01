# -*- coding: utf-8 -*-
"""Censo independente — PAREDES NÃO MODULADAS, com ranking de causas
(missão CONTA 2, seção 21) + PERFORMANCE/hotspots (seção 23, medido junto
porque as duas coisas saem da mesma rodada do solver).

Uma parede é considerada "modulada" aqui se pelo menos uma peça de
preenchimento (`STANDARD_FILL`/`OPENING_REPAIR_FILL`) foi materializada em
pelo menos uma fiada física — critério deliberadamente FRACO (mais fácil
de passar do que falhar), para que "não modulada" só capture o caso
realmente grave (zero peça em toda a parede), e o resto (segmentos
parciais sem fechar) apareça separado em `walls_with_non_modular_segments`.

Ranking de causa por parede sem NENHUMA peça: cruza os `non_modular`
entries daquela parede com `intersection_failures`/`collisions` que
tocam nós daquela parede, e com a presença de abertura na própria parede —
nesta ordem de prioridade (a primeira que casar decide):
  1. `L_T_X_FAILURE` — a parede toca um nó em `intersection_failures`;
  2. `COLLISION` — algum candidato daquela parede aparece em `collisions`;
  3. `OPENING` — a parede tem abertura(ns) e o(s) `non_modular` cai perto
     de uma delas;
  4. `LENGTH_ARITHMETIC` — o `non_modular` não fecha em blocos por conta
     (não é múltiplo válido), sem abertura/nó envolvido;
  5. `UNKNOWN` — nenhuma das anteriores explica.
"""
import sys

import lib_audit as A

NEAR_OPENING_CM = 30.0


def _classify_wall_cause(wall_idx, run_data):
    solve_result = run_data["solve_result"]
    walls_to_create = run_data["walls_to_create"]
    openings_per_wall = run_data["openings_per_wall"]
    nodes = run_data["nodes"]

    wall_non_modular = [e for e in (solve_result.get("non_modular") or []) if e.get("wall_idx") == wall_idx]

    failing_node_idxs = set()
    for f in solve_result.get("intersection_failures") or []:
        node_index = f[0]
        if node_index < len(nodes) and wall_idx in A.node_wall_indices(nodes[node_index]):
            failing_node_idxs.add(node_index)
    if failing_node_idxs:
        return "L_T_X_FAILURE", {"failing_node_idxs": sorted(failing_node_idxs)}

    all_candidates = solve_result.get("candidates") or []
    collisions = solve_result.get("collisions") or []
    for a_i, b_i in collisions:
        ca, cb = all_candidates[a_i], all_candidates[b_i]
        if ca.get("wall_idx") == wall_idx or cb.get("wall_idx") == wall_idx:
            return "COLLISION", {}

    wall_openings = openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else []
    if wall_openings and wall_non_modular:
        edges_cm = A.opening_edges_cm(wall_openings)
        for entry in wall_non_modular:
            seg_center = (entry.get("seg_start_cm", 0) + entry.get("seg_end_cm", 0)) / 2.0
            if any(abs(seg_center - e) <= NEAR_OPENING_CM for e in edges_cm):
                return "OPENING", {}

    if wall_non_modular:
        return "LENGTH_ARITHMETIC", {}

    return "UNKNOWN", {}


def census(run_data):
    walls_to_create = run_data["walls_to_create"]
    solve_result = run_data["solve_result"]
    n_walls = len(walls_to_create)

    walls_with_any_fill = set()
    for _course_index, candidate in A.physical_course_candidates(solve_result):
        reason = candidate.get("placement_reason")
        if reason in ("STANDARD_FILL", "OPENING_REPAIR_FILL"):
            wall_idx = candidate.get("wall_idx")
            if wall_idx is not None:
                walls_with_any_fill.add(wall_idx)

    walls_with_any_piece = set()
    for _course_index, candidate in A.physical_course_candidates(solve_result):
        wall_idx = candidate.get("wall_idx")
        if wall_idx is not None:
            walls_with_any_piece.add(wall_idx)

    not_modulated = sorted(set(range(n_walls)) - walls_with_any_fill - walls_with_any_piece)
    walls_with_non_modular = sorted(set(
        e.get("wall_idx") for e in (solve_result.get("non_modular") or [])
        if e.get("wall_idx") is not None))

    cause_counts = {}
    cause_examples = {}
    for wall_idx in not_modulated:
        cause, extra = _classify_wall_cause(wall_idx, run_data)
        cause_counts[cause] = cause_counts.get(cause, 0) + 1
        cause_examples.setdefault(cause, [])
        if len(cause_examples[cause]) < 10:
            p0_cm, p1_cm, length_cm, thickness_cm = A.wall_axis(walls_to_create, wall_idx)
            cause_examples[cause].append({
                "wall_idx": wall_idx, "length_cm": length_cm, "thickness_cm": thickness_cm,
                **extra,
            })

    length_buckets = {}
    for wall_idx in not_modulated:
        _p0, _p1, length_cm, _t = A.wall_axis(walls_to_create, wall_idx)
        bucket = ("<50" if length_cm < 50 else "50-100" if length_cm < 100 else
                  "100-300" if length_cm < 300 else ">=300")
        length_buckets[bucket] = length_buckets.get(bucket, 0) + 1

    return {
        "total_walls": n_walls,
        "walls_not_modulated_at_all": len(not_modulated),
        "walls_not_modulated_idx": not_modulated,
        "walls_with_at_least_one_non_modular_segment": len(walls_with_non_modular),
        "cause_ranking": A.summarize_counter(cause_counts),
        "cause_examples": cause_examples,
        "not_modulated_length_cm_buckets": length_buckets,
        "performance": {
            "solver_elapsed_s": round(run_data["elapsed_s"], 3),
            "num_courses": run_data["num_courses"],
            "num_bands": len(run_data["solve_result"].get("bands") or []),
            "total_candidates_all_variants": len(run_data["solve_result"].get("candidates") or []),
            "total_materialized_pieces": sum(
                1 for _ in A.physical_course_candidates(run_data["solve_result"])),
            "note": ("hotspot conhecido, ja' documentado em REGRAS_MODULACAO_BLOCOS.md "
                     "26.1 (item M do plano): merge_collinear_fragments e a varredura "
                     "O(n^2) de find_wall_pairs na FASE A, ANTES deste solver de blocos "
                     "- nao remedido aqui, so' referenciado."),
        },
    }


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else A.PRIMARY_PROJECT_ID
    run_data = A.run_solver(project_id)
    result = census(run_data)
    result["project_id"] = project_id
    A.write_json(A.out_path("out_coverage_census.json"), result)
    print("not modulated:", result["walls_not_modulated_at_all"], "/", result["total_walls"])
    print("cause ranking:", result["cause_ranking"])
    print("solver elapsed_s:", result["performance"]["solver_elapsed_s"])
    return result


if __name__ == "__main__":
    main()
