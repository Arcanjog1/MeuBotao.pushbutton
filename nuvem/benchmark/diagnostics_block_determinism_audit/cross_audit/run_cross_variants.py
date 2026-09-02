# -*- coding: utf-8 -*-
"""CROSS-AUDIT (missão item 4/5) — repete, SEM NENHUMA MODIFICAÇÃO nos
critérios, a mesma bateria de 24 ordens do baseline (`../run_baseline_variants.py`)
contra o código da CONTA 1 (branch `claude/block-pipeline-determinism-uj7cvq`,
mesclada nesta branch de cross-audit). Reusa `lib_det`/`oracle`/`variants` do
diretório-pai (não duplicados) — a MESMA régua, aplicada a um código
diferente. Saída fica em `cross_audit/`, nunca sobre os `out_*.json` do
baseline (que continuam sendo a medição feita ANTES de conhecer a CONTA 1).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

import lib_det as L  # noqa: E402
import run_baseline_variants as RBV  # noqa: E402


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    result, _runs, _layers, _rows = RBV.census(project_id)
    out_path = os.path.join(_HERE, "out_cross_variants_census.json")
    L.write_json(out_path, result)
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
    print("divergences:")
    for d in result["divergences"]:
        print("  ", d)
    return result


if __name__ == "__main__":
    main()
