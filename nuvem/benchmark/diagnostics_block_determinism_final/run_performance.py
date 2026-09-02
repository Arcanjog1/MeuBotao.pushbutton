# -*- coding: utf-8 -*-
"""Item 58 da missao: tempo do GRAFO, do preenchimento, do reparo de
abertura e do pipeline completo, antes/depois - para provar que a
canonizacao nao trouxe explosao de complexidade.

    python3 run_performance.py [project_id] [repeticoes]
"""
import sys
import time

import lib_final as F


def measure(project_id, repeats=5):
    engine = F.L.engine()
    stepper = sys.modules[engine.solve_wall_free_fill.__module__]
    input_project = F.load_input(project_id)

    totals = {"wall_graph_s": [], "fill_s": [], "opening_repair_s": [], "pipeline_s": []}

    original_graph = engine.build_wall_graph
    original_fill = stepper.solve_wall_free_fill
    original_recut = stepper._recut_openings_and_repair
    acc = {"graph": 0.0, "fill": 0.0, "recut": 0.0}

    def timed(name, func, target_module, attr):
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                acc[name] += time.perf_counter() - t0
        return wrapper

    for _ in range(repeats):
        acc["graph"] = acc["fill"] = acc["recut"] = 0.0
        engine.build_wall_graph = timed("graph", original_graph, engine, "build_wall_graph")
        stepper.solve_wall_free_fill = timed("fill", original_fill, stepper, "solve_wall_free_fill")
        stepper._recut_openings_and_repair = timed(
            "recut", original_recut, stepper, "_recut_openings_and_repair")
        try:
            t0 = time.perf_counter()
            F.run_solver(project_id, input_project=input_project)
            pipeline = time.perf_counter() - t0
        finally:
            engine.build_wall_graph = original_graph
            stepper.solve_wall_free_fill = original_fill
            stepper._recut_openings_and_repair = original_recut
        totals["wall_graph_s"].append(acc["graph"])
        # o reparo roda DENTRO do preenchimento - reportado separado e
        # tambem descontado, para "fill" significar so' o preenchimento.
        totals["fill_s"].append(acc["fill"] - acc["recut"])
        totals["opening_repair_s"].append(acc["recut"])
        totals["pipeline_s"].append(pipeline)

    return dict(
        (key, {"min": round(min(values), 4), "max": round(max(values), 4),
               "mean": round(sum(values) / len(values), 4)})
        for key, values in totals.items()
    )


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else F.PRIMARY_PROJECT_ID
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    result = {"project_id": project_id, "repeats": repeats,
              "timings": measure(project_id, repeats)}
    for key, info in result["timings"].items():
        print("  %-18s min=%-8s mean=%-8s max=%s" % (key, info["min"], info["mean"], info["max"]))
    return result


if __name__ == "__main__":
    main()
