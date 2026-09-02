# -*- coding: utf-8 -*-
"""Censo das 24+ variantes com as metricas CORRIGIDAS da finalizacao
(`lib_final`): `wall_end_to_node` canonico e fingerprint FISICO de peca.

    python3 run_final_variants.py [project_id]

Saida: `out_final_variants_<project_id>.json`.
"""
import sys

import lib_final as F
import variants as V


def _run_one(project_id, name, input_project):
    run_data = F.run_solver(project_id, input_project=input_project)
    layers, rows = F.final_layered_fingerprints(run_data)
    return {"name": name, "layers": layers,
            "downstream": F.downstream_metrics(run_data)}, layers, rows


def census(project_id=None):
    project_id = project_id or F.PRIMARY_PROJECT_ID
    input_project = F.load_input(project_id)

    results = []
    layers_by_name = {}
    rows_by_name = {}

    all_runs = [("baseline", input_project)] + list(V.build_all_variants(input_project))
    for name, project in all_runs:
        summary, layers, rows = _run_one(project_id, name, project)
        results.append(summary)
        layers_by_name[name] = layers
        rows_by_name[name] = rows
        print("  ran", name,
              "global=", layers["global_result"]["fingerprint"][:12],
              "pieces=", summary["downstream"]["pieces"],
              "elapsed=", summary["downstream"]["runtime_s"])

    layer_names = [n for n, _ in F.FINAL_LAYER_FUNCS] + ["global_result"]
    per_layer = {}
    for layer_name in layer_names:
        groups = {}
        for row in results:
            fp = layers_by_name[row["name"]][layer_name]["fingerprint"]
            groups.setdefault(fp, []).append(row["name"])
        per_layer[layer_name] = {
            "distinct_fingerprints": len(groups),
            "deterministic": len(groups) == 1,
            "groups": dict((fp[:12], names) for fp, names in groups.items()),
        }

    baseline_layers = layers_by_name["baseline"]
    divergences = []
    for row in results[1:]:
        first = F.first_divergent_layer(baseline_layers, layers_by_name[row["name"]])
        if first is not None:
            divergences.append({"variant": row["name"], "first_divergent_layer": first})

    downstream_range = {}
    numeric_keys = ("pieces", "non_modular", "intersection_failures",
                    "alignment_conflicts", "collisions", "door_void_violations",
                    "B39", "B34", "B54", "B19", "C09", "C04", "runtime_s")
    for key in numeric_keys:
        values = [row["downstream"].get(key, 0) for row in results]
        downstream_range[key] = {"min": min(values), "max": max(values),
                                 "spread": round(max(values) - min(values), 3)}

    reason_range = {}
    reasons = set()
    for row in results:
        reasons.update((row["downstream"].get("by_placement_reason") or {}).keys())
    for reason in sorted(reasons):
        values = [(row["downstream"].get("by_placement_reason") or {}).get(reason, 0)
                  for row in results]
        reason_range[reason] = {"min": min(values), "max": max(values),
                                "spread": max(values) - min(values)}

    return {
        "project_id": project_id,
        "n_variants_total": len(results),
        "global_distinct_fingerprints": per_layer["global_result"]["distinct_fingerprints"],
        "deterministic": per_layer["global_result"]["deterministic"],
        "per_layer_distinct_fingerprints": per_layer,
        "downstream_range": downstream_range,
        "placement_reason_range": reason_range,
        "divergences": divergences,
        "results": results,
    }, rows_by_name


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else F.PRIMARY_PROJECT_ID
    result, _rows = census(project_id)
    F.write_json(F.out_path("out_final_variants_%s.json" % project_id), result)
    print()
    print("n_variants:", result["n_variants_total"])
    print("GLOBAL distinct fingerprints:", result["global_distinct_fingerprints"],
          "deterministic=", result["deterministic"])
    for name, info in result["per_layer_distinct_fingerprints"].items():
        print("  ", name, "distinct=", info["distinct_fingerprints"])
        if not info["deterministic"]:
            for fp, names in info["groups"].items():
                print("       ", fp, len(names), names[:4])
    print("downstream:")
    for key, info in result["downstream_range"].items():
        print("  ", key, info)
    print("placement_reason:")
    for key, info in result["placement_reason_range"].items():
        print("  ", key, info)
    print("divergences:", result["divergences"])
    return result


if __name__ == "__main__":
    main()
