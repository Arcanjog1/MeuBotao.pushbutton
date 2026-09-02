# -*- coding: utf-8 -*-
"""Censo independente de determinismo (missão itens 4, 5, 6, 12, 13).

Roda o solver real sobre o projeto principal em `baseline` + TODAS as
variantes (8 oficiais + bateria adicional, `variants.build_all_variants`),
mede fingerprints em CAMADAS (`lib_det.layered_fingerprints`) e métricas
downstream (`lib_det.downstream_metrics`) em cada uma, e localiza a
PRIMEIRA camada onde cada variante diverge do baseline.

Uso:
    python3 run_baseline_variants.py [project_id]

Saída: `out_variants_census.json`.
"""
import sys

import lib_det as L
import variants as V


def _run_one(project_id, name, input_project):
    run_data = L.run_solver(project_id, input_project=input_project)
    layers, rows_by_layer = L.layered_fingerprints(run_data)
    downstream = L.downstream_metrics(run_data)
    return {
        "name": name,
        "layers": layers,
        "downstream": downstream,
    }, run_data, layers, rows_by_layer


def census(project_id=None):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    input_project = L.load_input(project_id)

    baseline_summary, baseline_run, baseline_layers, baseline_rows = _run_one(
        project_id, "baseline", input_project)

    all_variants = V.build_all_variants(input_project)

    results = [baseline_summary]
    runs_by_name = {"baseline": baseline_run}
    layers_by_name = {"baseline": baseline_layers}
    rows_by_name = {"baseline": baseline_rows}

    for name, proj in all_variants:
        summary, run_data, layers, rows = _run_one(project_id, name, proj)
        results.append(summary)
        runs_by_name[name] = run_data
        layers_by_name[name] = layers
        rows_by_name[name] = rows
        print("  ran", name, "global=", layers["global_result"]["fingerprint"][:12],
              "pieces=", summary["downstream"]["pieces"],
              "elapsed=", summary["downstream"]["runtime_s"])

    # -------- fingerprints por camada, agregados --------
    layer_names = [name for name, _ in L.LAYER_FUNCS] + ["global_result"]
    per_layer_distinct = {}
    for layer_name in layer_names:
        fps = sorted(set(layers_by_name[r["name"]][layer_name]["fingerprint"] for r in results))
        per_layer_distinct[layer_name] = {
            "distinct_fingerprints": len(fps),
            "deterministic": len(fps) == 1,
        }

    global_fps = sorted(set(r["layers"]["global_result"]["fingerprint"] for r in results))

    divergences = []
    for r in results[1:]:
        if r["layers"]["global_result"]["fingerprint"] != baseline_summary["layers"]["global_result"]["fingerprint"]:
            layer = L.first_divergent_layer(baseline_layers, layers_by_name[r["name"]])
            divergences.append({"variant": r["name"], "first_divergent_layer": layer})

    # -------- downstream min/max entre TODAS as ordens (missao item 12) --------
    downstream_keys = ("pieces", "non_modular", "intersection_failures",
                        "alignment_conflicts", "collisions", "door_void_violations",
                        "C09", "C04", "B19", "runtime_s")
    downstream_range = {}
    for key in downstream_keys:
        values = [r["downstream"][key] for r in results]
        downstream_range[key] = {"min": min(values), "max": max(values),
                                  "spread": round(max(values) - min(values), 4)}

    out = {
        "project_id": project_id,
        "n_variants_total": len(results),
        "variant_names": [r["name"] for r in results],
        "runs": results,
        "per_layer_distinct_fingerprints": per_layer_distinct,
        "global_distinct_fingerprints": len(global_fps),
        "global_fingerprints": global_fps,
        "deterministic": len(global_fps) == 1,
        "divergences": divergences,
        "downstream_range": downstream_range,
    }
    return out, runs_by_name, layers_by_name, rows_by_name


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    result, _runs, _layers, _rows = census(project_id)
    L.write_json(L.out_path("out_variants_census.json"), result)
    print()
    print("n_variants:", result["n_variants_total"])
    print("global distinct fingerprints:", result["global_distinct_fingerprints"],
          "deterministic=", result["deterministic"])
    print("per-layer determinism:")
    for name, info in result["per_layer_distinct_fingerprints"].items():
        print("  ", name, "distinct=", info["distinct_fingerprints"],
              "deterministic=", info["deterministic"])
    print("downstream min/max spread:")
    for key, info in result["downstream_range"].items():
        print("  ", key, info)
    return result


if __name__ == "__main__":
    main()
