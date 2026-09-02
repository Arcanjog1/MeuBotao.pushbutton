# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / etapa A - REPRODUCAO do baseline.

Roda as 8 variantes do CR (baseline, reversed, endpoint_reversal,
shuffle_seed_{1,2,3,10,42}) e mede, POR CAMADA do pipeline, o fingerprint
CANONICO (nunca `wall_idx`, nunca a ordem da lista) - para localizar a
PRIMEIRA camada que diverge em cada variante, em vez de so' constatar que
o resultado final mudou.

Uso:  python3 run_baseline.py [project_id] [-o saida.json]
"""
import sys

import lib_det as L


def run(project_id=None):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    input_project = L.load_input(project_id)
    variants = L.build_variants(input_project)

    runs = []
    layers_by_name = {}
    for name, project in variants:
        run_data = L.run_full(project)
        layers = L.graph_layers(run_data)
        layers.update(L.block_layers(run_data))
        layers["name"] = name
        layers["total_elapsed_s"] = round(
            layers["plan_elapsed_s"] + layers["solve_elapsed_s"], 4)
        layers_by_name[name] = layers
        runs.append(layers)
        print("  %-20s nodes=%d pieces=%d fp_nodes=%s fp_blocks=%s"
              % (name, layers["n_nodes"], layers["n_pieces"],
                 layers["fp_nodes"][:12], layers["fp_blocks"][:12]))

    baseline = layers_by_name["baseline"]
    divergences = []
    for layers in runs[1:]:
        layer = L.first_divergent_layer(baseline, layers)
        divergences.append({
            "variant": layers["name"],
            "first_divergent_layer": layer,
            "kinds_baseline": baseline["kinds"],
            "kinds_variant": layers["kinds"],
            "n_nodes_baseline": baseline["n_nodes"],
            "n_nodes_variant": layers["n_nodes"],
        })

    distinct = {}
    for key in L.LAYER_ORDER:
        distinct[key] = len(sorted(set(r[key] for r in runs)))

    return {
        "project_id": project_id,
        "n_variants": len(runs),
        "runs": runs,
        "distinct_fingerprints_by_layer": distinct,
        "divergences": divergences,
        "deterministic": distinct["fp_blocks"] == 1,
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    out_name = "out_baseline.json"
    if "-o" in sys.argv:
        out_name = sys.argv[sys.argv.index("-o") + 1]
        args = [a for a in args if a != out_name]
    project_id = args[0] if args else L.PRIMARY_PROJECT_ID
    print("projeto:", project_id)
    result = run(project_id)
    L.write_json(L.out_path(out_name), result)
    print("\ndistintos por camada:")
    for key in L.LAYER_ORDER:
        print("  %-26s %d" % (key, result["distinct_fingerprints_by_layer"][key]))
    print("\nprimeira camada divergente:")
    for d in result["divergences"]:
        print("  %-20s %s (nodes %d -> %d)"
              % (d["variant"], d["first_divergent_layer"],
                 d["n_nodes_baseline"], d["n_nodes_variant"]))
    return result


if __name__ == "__main__":
    main()
