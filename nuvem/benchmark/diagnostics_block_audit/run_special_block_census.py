# -*- coding: utf-8 -*-
"""Censo independente — C09, C04, B19, B34, B54 (missão CONTA 2, seções
9-13) + repetição vertical (seção 19), medido sobre TODAS as peças em
`course_candidates` (o que seria de fato materializado no Revit).

Cada peça especial é classificada, quando aplicável, por:
  - `placement_reason` (dado bruto do próprio motor — nunca reinterpretado
    por adivinhação): L_CORNER / T_INTERSECTION_MAIN / T_INTERSECTION_
    INCOMING / T_INTERSECTION_DEGRADED_L / T_INTERSECTION_INCOMING_
    DEGRADED / X_INTERSECTION / CORNER_DEGRADED / STANDARD_FILL /
    OPENING_REPAIR_FILL / outro.
  - distância até a borda de abertura mais próxima da própria parede e até
    a ponta da parede (cm) — para achar "meio de parede" vs "perto de
    vão/extremidade".
  - distância até o nó L/T/X mais próximo em planta (qualquer parede).
  - sequência: quantos do MESMO código aparecem consecutivos na mesma
    fiada física da mesma parede (join por posição ao longo do eixo).
  - repetição vertical: mesma posição X aproximada (tolerância
    `VERTICAL_STRIP_POSITION_TOL_CM`) em >=3 fiadas físicas consecutivas —
    o dado bruto que sustenta (ou não) `REPEATED_VERTICAL_COMPENSATOR_
    STRIP`/`COMPENSATOR_VERTICAL_STRIP` já documentados, mas medido aqui do
    zero, sem chamar o validador oficial.
"""
import sys

import lib_audit as A

VERTICAL_STRIP_POSITION_TOL_CM = 5.0
VERTICAL_STRIP_MIN_RUN = 3
CONSECUTIVE_CODES = ("C09", "C04")
MID_WALL_REASONS = ("STANDARD_FILL", "OPENING_REPAIR_FILL")
NODE_TRUE_REASONS = ("L_CORNER", "T_INTERSECTION_MAIN", "T_INTERSECTION_INCOMING", "X_INTERSECTION")


def _reason_bucket(reason):
    if reason is None:
        return "UNKNOWN"
    if reason in MID_WALL_REASONS:
        return "MID_WALL_FILL"
    if reason in NODE_TRUE_REASONS:
        return "NODE_TRUE"
    if "DEGRADED" in reason:
        return "NODE_DEGRADED"
    return "OTHER:" + reason


def _distance_to_edges_cm(t_center_cm, wall_length_cm, edges_cm):
    all_edges = [0.0, wall_length_cm] + edges_cm
    return min(abs(t_center_cm - e) for e in all_edges)


def _census_code(code, walls_to_create, spans_by_wall_course, nodes, openings_per_wall):
    occurrences = []
    for (wall_idx, course_index), spans in spans_by_wall_course.items():
        wall_openings = openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else []
        edges_cm = A.opening_edges_cm(wall_openings)
        _p0, _p1, wall_dir, wall_length_cm, _thick = A.wall_direction_cm(walls_to_create, wall_idx)
        for i, span in enumerate(spans):
            if span["code"] != code:
                continue
            cand = span["candidate"]
            reason = cand.get("placement_reason")
            node_dist_cm, node = A.nearest_node_distance_cm(A.candidate_origin_cm(cand), nodes)
            run_len = 1
            j = i + 1
            while j < len(spans) and spans[j]["code"] == code:
                run_len += 1
                j += 1
            k = i - 1
            while k >= 0 and spans[k]["code"] == code:
                run_len += 1
                k -= 1
            # run_len acima conta os dois lados separadamente na varredura
            # (double count evitado abaixo: só grava run_len no PRIMEIRO
            # elemento consecutivo, os demais recebem a mesma "run_id").
            occurrences.append({
                "wall_idx": wall_idx, "course_index": course_index,
                "t_center_cm": round(span["t_center_cm"], 2),
                "reason": reason, "reason_bucket": _reason_bucket(reason),
                "node_index": cand.get("node_index"),
                "dist_to_edge_cm": round(_distance_to_edges_cm(
                    span["t_center_cm"], wall_length_cm, edges_cm), 2),
                "dist_to_node_cm": round(node_dist_cm, 2) if node_dist_cm is not None else None,
                "is_mid_wall": _reason_bucket(reason) == "MID_WALL_FILL",
            })

    total = len(occurrences)
    per_wall = {}
    per_course = {}
    reason_hist = {}
    for occ in occurrences:
        per_wall[occ["wall_idx"]] = per_wall.get(occ["wall_idx"], 0) + 1
        per_course[occ["course_index"]] = per_course.get(occ["course_index"], 0) + 1
        reason_hist[occ["reason_bucket"]] = reason_hist.get(occ["reason_bucket"], 0) + 1

    # --- sequencias consecutivas na mesma fiada/parede (so' faz sentido
    # para pecas de preenchimento, medido para todas mesmo assim).
    run_lengths = []
    run_examples_ge2 = []
    mid_wall_only_runs_ge2 = 0
    runs_touching_node_ge2 = 0
    for (wall_idx, course_index), spans in spans_by_wall_course.items():
        i = 0
        while i < len(spans):
            if spans[i]["code"] != code:
                i += 1
                continue
            j = i
            while j < len(spans) and spans[j]["code"] == code:
                j += 1
            run_len = j - i
            run_lengths.append(run_len)
            if run_len >= 2:
                all_mid_wall = all(
                    _reason_bucket(spans[k]["candidate"].get("placement_reason")) == "MID_WALL_FILL"
                    for k in range(i, j))
                if all_mid_wall:
                    mid_wall_only_runs_ge2 += 1
                else:
                    runs_touching_node_ge2 += 1
                if len(run_examples_ge2) < 25:
                    run_examples_ge2.append({
                        "wall_idx": wall_idx, "course_index": course_index, "run_len": run_len,
                        "t_range_cm": [round(spans[i]["t_start_cm"], 1), round(spans[j - 1]["t_end_cm"], 1)],
                        "all_mid_wall_fill": all_mid_wall,
                    })
            i = j
    runs_hist = {}
    for r in run_lengths:
        bucket = str(r) if r <= 3 else "4+"
        runs_hist[bucket] = runs_hist.get(bucket, 0) + 1

    # --- repeticao vertical: mesma parede, posicoes t proximas em fiadas
    # fisicas consecutivas.
    by_wall = {}
    for occ in occurrences:
        by_wall.setdefault(occ["wall_idx"], []).append(occ)
    vertical_strips = []
    for wall_idx, occs in by_wall.items():
        occs_sorted = sorted(occs, key=lambda o: (o["t_center_cm"], o["course_index"]))
        used = [False] * len(occs_sorted)
        for i, occ in enumerate(occs_sorted):
            if used[i]:
                continue
            cluster = [occ]
            used[i] = True
            for k in range(i + 1, len(occs_sorted)):
                if used[k]:
                    continue
                if abs(occs_sorted[k]["t_center_cm"] - occ["t_center_cm"]) <= VERTICAL_STRIP_POSITION_TOL_CM:
                    cluster.append(occs_sorted[k])
                    used[k] = True
            courses_in_cluster = sorted(set(c["course_index"] for c in cluster))
            # fiadas consecutivas dentro do cluster (maior sequencia)
            best_run = 1
            cur_run = 1
            for a, b in zip(courses_in_cluster, courses_in_cluster[1:]):
                if b == a + 1:
                    cur_run += 1
                    best_run = max(best_run, cur_run)
                else:
                    cur_run = 1
            if best_run >= VERTICAL_STRIP_MIN_RUN:
                vertical_strips.append({
                    "wall_idx": wall_idx, "t_center_cm": round(occ["t_center_cm"], 1),
                    "courses": courses_in_cluster, "consecutive_run": best_run,
                })

    return {
        "code": code,
        "total": total,
        "per_wall_top20": dict(list(A.summarize_counter(per_wall).items())[:20]),
        "per_course": dict(sorted(per_course.items())),
        "reason_bucket_histogram": reason_hist,
        "run_length_histogram": runs_hist,
        "run_examples_len_ge2": run_examples_ge2,
        "consecutive_2plus_runs": sum(1 for r in run_lengths if r >= 2),
        "consecutive_3plus_runs": sum(1 for r in run_lengths if r >= 3),
        "consecutive_runs_mid_wall_fill_only": mid_wall_only_runs_ge2,
        "consecutive_runs_touching_a_node_piece": runs_touching_node_ge2,
        "dist_to_opening_or_end_cm_summary": _summary([o["dist_to_edge_cm"] for o in occurrences]),
        "mid_wall_far_from_edge_count": sum(
            1 for o in occurrences if o["is_mid_wall"] and o["dist_to_edge_cm"] > 60.0),
        "dist_to_node_cm_summary": _summary([o["dist_to_node_cm"] for o in occurrences
                                              if o["dist_to_node_cm"] is not None]),
        "vertical_strips_ge_%d_courses" % VERTICAL_STRIP_MIN_RUN: vertical_strips[:40],
        "vertical_strips_total_found": len(vertical_strips),
    }


def _summary(values):
    if not values:
        return None
    values = sorted(values)
    n = len(values)
    return {
        "count": n, "min": values[0], "max": values[-1],
        "median": values[n // 2],
        "mean": round(sum(values) / n, 2),
    }


def census(run_data):
    walls_to_create = run_data["walls_to_create"]
    solve_result = run_data["solve_result"]
    nodes = run_data["nodes"]
    openings_per_wall = run_data["openings_per_wall"]
    spans_by_wall_course = A.wall_course_spans(walls_to_create, solve_result, only_parallel=True)

    out = {}
    for code in ("C09", "C04", "B19", "B34", "B54"):
        out[code] = _census_code(code, walls_to_create, spans_by_wall_course, nodes, openings_per_wall)
    return out


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else A.PRIMARY_PROJECT_ID
    run_data = A.run_solver(project_id)
    result = census(run_data)
    result["project_id"] = project_id
    A.write_json(A.out_path("out_special_block_census.json"), result)
    for code in ("C09", "C04", "B19", "B34", "B54"):
        print(code, "total=", result[code]["total"],
              "runs>=2=", result[code]["consecutive_2plus_runs"],
              "vstrips=", result[code]["vertical_strips_total_found"])
    return result


if __name__ == "__main__":
    main()
