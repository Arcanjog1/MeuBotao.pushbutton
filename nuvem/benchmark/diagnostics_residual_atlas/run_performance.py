# -*- coding: utf-8 -*-
"""PERFORMANCE (item 22): tempo por projeto e por estagio, via WRAPPERS de
monkeypatch (somente em memoria, nesta execucao) nas funcoes do motor.
Nao altera producao. Conta chamadas e tempo acumulado (inclusive) de:
  solve_all_intersections, process_walls_one_by_one, solve_wall_free_fill,
  _recut_openings_and_repair, _pier_layout_avoiding_joints,
  _pier_full_search_layout, _pier_ordered_layout, audit_all_walls_bond_quality,
  repair_arm_role_isolated_edges (+ numero de rebuilds), validate_same_course_collision,
  find_door_void_violations, orient_compensator_candidates.
    -> performance.json
"""
import os
import sys
import time
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402


def wrap(module, name, stats):
    original = getattr(module, name)

    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            stats[name]["calls"] += 1
            stats[name]["seconds"] += time.perf_counter() - t0
    wrapper.__wrapped__ = original
    setattr(module, name, wrapper)
    return original


def main():
    engine = al.engine()
    st = al.stepper()
    out = {}
    for pid in al.PROJECT_IDS:
        stats = defaultdict(lambda: {"calls": 0, "seconds": 0.0})
        originals = []
        # wall_stepper internals (chamadas internas usam o namespace do stepper)
        for name in ("solve_all_intersections", "solve_wall_free_fill", "_recut_openings_and_repair",
                     "_pier_layout_avoiding_joints", "_pier_full_search_layout", "_pier_ordered_layout",
                     "validate_same_course_collision", "find_door_void_violations",
                     "repair_arm_role_isolated_edges", "process_walls_one_by_one",
                     "_continuous_segment_layout", "_index_node_candidates_by_wall_end",
                     "validate_wall_modulation", "_placed_index_near_wall"):
            originals.append((st, name, wrap(st, name, stats)))
        # wall_modeling namespace (chama por nome solto importado via *)
        for name in ("audit_all_walls_bond_quality", "orient_compensator_candidates",
                     "_solve_building_blocks_all_courses_core", "_drop_fill_colliding_with_ties"):
            originals.append((engine, name, wrap(engine, name, stats)))
        # wall_modeling tambem tem copias dos nomes do stepper via import *: patcha ali tambem
        for name in ("solve_building_blocks", "repair_arm_role_isolated_edges", "process_walls_one_by_one",
                     "validate_same_course_collision", "find_door_void_violations"):
            if hasattr(engine, name):
                originals.append((engine, name, wrap(engine, name, stats)))
        t0 = time.perf_counter()
        run = al.run_solver_in_memory(al.load_input(pid))
        total = time.perf_counter() - t0
        for module, name, original in originals:
            setattr(module, name, original)
        rows = sorted(((k, v["calls"], round(v["seconds"], 3)) for k, v in stats.items()),
                      key=lambda r: -r[2])
        out[al.SHORT[pid]] = {"total_seconds": round(total, 2), "stages": rows,
                              "walls": len(run["walls_to_create"]), "nodes": len(run["nodes"]),
                              "bands": len(run["solve_result"].get("bands") or []),
                              "arm_rebuilds": stats["_solve_building_blocks_all_courses_core"]["calls"]}
        print("=====", al.SHORT[pid], "total %.1fs" % total, "core rebuilds:",
              stats["_solve_building_blocks_all_courses_core"]["calls"])
        for r in rows:
            print("   %-42s calls=%7d  %8.2fs" % r)
    al.write_json(al.out_path("performance.json"), out)


if __name__ == "__main__":
    main()
