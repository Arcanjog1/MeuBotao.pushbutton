# -*- coding: utf-8 -*-
"""Performance do CR-BLOCK-NODE-FILL-JOINT (item 16 do CR).

Mede, por projeto e por FASE (grafo / solver / validacao / total), com N
repeticoes, para o antes/depois nao virar ruido de uma rodada so'.

    python3 run_nf_performance.py [--repeat 5] [--out out_nf_performance.json]
"""
import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_NUVEM = os.path.dirname(_BENCH)
for _p in (_NUVEM, _BENCH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PROJECT_IDS = ("piloto_sintetico_2x2", "torre_easy_lo_r00_tgd",
               "torre_easy_lo_r00_tp1")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--out", default=os.path.join(_HERE, "out_nf_performance.json"))
    args = parser.parse_args(argv)

    from benchmark import runner, solver_bridge

    out = {"repeat": args.repeat, "projects": {}}
    for project_id in PROJECT_IDS:
        payload = json.load(open(runner.project_paths(project_id)["input"],
                                 "r", encoding="utf-8"))
        graph_s, solver_s, total_s = [], [], []
        for _ in range(args.repeat):
            t0 = time.perf_counter()
            solver_bridge.plan_from_input(payload)
            t1 = time.perf_counter()
            solver_bridge.run_solver(payload)
            t2 = time.perf_counter()
            graph_s.append(t1 - t0)
            solver_s.append(t2 - t1)
            total_s.append(t2 - t0)

        def stats(values):
            return {"min": round(min(values), 4),
                    "median": round(sorted(values)[len(values) // 2], 4),
                    "mean": round(sum(values) / len(values), 4)}

        out["projects"][project_id] = {
            "graph": stats(graph_s), "solver": stats(solver_s),
            "total": stats(total_s),
        }
        print("{0:<26} grafo {1:>7.4f}s  solver {2:>7.4f}s  total {3:>7.4f}s (mediana)".format(
            project_id, out["projects"][project_id]["graph"]["median"],
            out["projects"][project_id]["solver"]["median"],
            out["projects"][project_id]["total"]["median"]))

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print("gravado em {0}".format(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
