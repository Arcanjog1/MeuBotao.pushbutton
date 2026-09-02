# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / etapa D - BENCHMARK COMPLETO.

Mede, nos TRES projetos versionados, tudo o que a missao pede comparar
antes/depois - inclusive os gates de nao-regressao do CR-BLOCK-01
(same-band forbidden = 0, alignment_conflicts = 0, cobertura >= 246/275).

Reusa a medicao ja' existente do CR-BLOCK-01
(`diagnostics_block_prisma/metrics.py`) em vez de reimplementar as
juntas: medir com outro codigo mediria outra coisa, e o gate e'
justamente "o numero do CR-BLOCK-01 continua o mesmo".

Uso:
    python3 run_benchmark.py            # com o codigo ATUAL da arvore
    python3 run_benchmark.py --legacy   # com as funcoes ANTIGAS reinstaladas
                                        # (monkeypatch da analise) = o "antes"
"""
import os
import sys
import time

import lib_det as L

_PRISMA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "diagnostics_block_prisma")
if _PRISMA not in sys.path:
    sys.path.insert(0, _PRISMA)


def _use_legacy():
    """Reinstala as versoes da main 24ada98 (ver run_ablation.py) para
    medir o "antes" no MESMO processo e com a MESMA medicao."""
    import run_ablation as AB
    module = AB.graph_module()
    module._cluster_wall_arms = AB._legacy_cluster_wall_arms
    module._wall_node_group_point = AB._legacy_group_point


def run(legacy=False):
    if legacy:
        _use_legacy()
    import metrics  # diagnostics_block_prisma/metrics.py

    started = time.perf_counter()
    measured = metrics.measure_all()
    elapsed = time.perf_counter() - started

    totals = measured["totals"]
    gates = {
        "CR-BLOCK-01 same_band_forbidden (exigido 0)":
            totals["forbidden_by_band"]["same_band"],
        "CR-BLOCK-01 alignment_conflicts (exigido 0)":
            totals["alignment_conflicts"],
        "CR-BLOCK-01 cobertura paredes com blocos (exigido >= 246)":
            "%d/%d" % (totals["walls_with_blocks"], totals["walls_considered"]),
    }
    resumo = {
        "modo": "legacy (main 24ada98)" if legacy else "arvore atual",
        "gates_CR_BLOCK_01": gates,
        "pieces": totals["blocks_total"],
        "non_modular": totals["non_modular"],
        "collisions": totals["collisions"],
        "door_void_violations": totals["door_void_violations"],
        "intersection_failures": totals["intersection_failures"],
        "joint_classes": totals["joint_classes"],
        "forbidden_by_band": totals["forbidden_by_band"],
        "blocks_by_code": totals["blocks_by_code"],
        "runtime_total_s": round(elapsed, 3),
        "runtime_por_projeto_s": dict(
            (pid, p["runtime_s"]) for pid, p in measured["projects"].items()),
        "por_projeto": dict(
            (pid, {"walls_with_blocks": p["walls_with_blocks"],
                   "walls_considered": p["walls_considered"],
                   "alignment_conflicts": p["alignment_conflicts"],
                   "non_modular": p["non_modular"],
                   "collisions": p["collisions"],
                   "door_void_violations": p["door_void_violations"],
                   "forbidden_by_band": p["forbidden_by_band"],
                   "fingerprint": p["fingerprint"]})
            for pid, p in measured["projects"].items()),
    }
    return resumo


def main():
    legacy = "--legacy" in sys.argv
    resumo = run(legacy=legacy)
    name = "out_benchmark_legacy.json" if legacy else "out_benchmark_atual.json"
    L.write_json(L.out_path(name), resumo)
    print(resumo["modo"])
    for key, value in resumo["gates_CR_BLOCK_01"].items():
        print("  %-58s %s" % (key, value))
    for key in ("pieces", "non_modular", "collisions", "door_void_violations",
                "intersection_failures", "runtime_total_s"):
        print("  %-58s %s" % (key, resumo[key]))
    print("  %-58s %s" % ("forbidden_by_band", resumo["forbidden_by_band"]))
    return resumo


if __name__ == "__main__":
    main()
