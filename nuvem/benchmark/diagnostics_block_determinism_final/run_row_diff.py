# -*- coding: utf-8 -*-
"""Diff LINHA A LINHA entre o baseline e uma variante, por camada fisica -
para achar QUAIS pecas (e em qual parede) ainda divergem, em vez de so'
saber que o hash mudou.

    python3 run_row_diff.py [variant_name] [project_id] [layer]
"""
import sys
import json

import lib_final as F
import variants as V

VARIANT_BUILDERS = {
    "endpoint_reversal": lambda p: V.endpoint_reversal(p),
    "reverse_horizontal_only": V.reverse_horizontal_only,
    "reverse_vertical_only": V.reverse_vertical_only,
    "random_endpoint_reversal_seed_1": lambda p: V.random_endpoint_reversal(p, 1),
    "random_endpoint_reversal_seed_2": lambda p: V.random_endpoint_reversal(p, 2),
}


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "endpoint_reversal"
    project_id = sys.argv[2] if len(sys.argv) > 2 else F.PRIMARY_PROJECT_ID
    only_layer = sys.argv[3] if len(sys.argv) > 3 else None

    base_project = F.load_input(project_id)
    base_run = F.run_solver(project_id, input_project=base_project)
    var_run = F.run_solver(project_id, input_project=VARIANT_BUILDERS[variant](base_project))

    _b_layers, b_rows = F.final_layered_fingerprints(base_run)
    _v_layers, v_rows = F.final_layered_fingerprints(var_run)

    report = {"variant": variant, "project_id": project_id, "layers": {}}
    for name, _func in F.FINAL_LAYER_FUNCS:
        if only_layer and name != only_layer:
            continue
        base_set = set(json.dumps(r, default=str, sort_keys=True) for r in b_rows[name])
        var_set = set(json.dumps(r, default=str, sort_keys=True) for r in v_rows[name])
        only_base = sorted(base_set - var_set)
        only_var = sorted(var_set - base_set)
        walls = set()
        for blob in only_base + only_var:
            try:
                walls.add(json.dumps(json.loads(blob)[0]))
            except Exception:
                pass
        report["layers"][name] = {
            "n_base": len(base_set), "n_variant": len(var_set),
            "n_only_base": len(only_base), "n_only_variant": len(only_var),
            "n_walls_touched": len(walls),
            "walls_touched": sorted(walls),
            "sample_only_base": only_base[:12],
            "sample_only_variant": only_var[:12],
        }
        print(name, "only_base=", len(only_base), "only_variant=", len(only_var),
              "walls=", len(walls))
    F.write_json(F.out_path("out_row_diff_%s_%s.json" % (project_id, variant)), report)
    return report


if __name__ == "__main__":
    main()
