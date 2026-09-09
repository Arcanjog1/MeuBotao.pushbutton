"""Reversible local L-choice experiment; never an approved solver candidate.

Uses only the two pieces already selected by solve_l_corner. Enumerates their
existing role-swap / same-side fallback choices against every junction piece.
An optional full solve measures secondary effects of one explicit hypothesis.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def choices(result):
    a, b = result["course_a"], result["course_b"]
    return {"unchanged": (a, b), "swap": (dict(b, course="A"), dict(a, course="B")),
            "both-a": (dict(a, secondary_wall_idx=a["wall_idx"]),
                       dict(a, course="B", secondary_wall_idx=a["wall_idx"])),
            "both-b": (dict(b, course="A", secondary_wall_idx=b["wall_idx"]),
                       dict(b, secondary_wall_idx=b["wall_idx"]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--node", required=True, type=int)
    parser.add_argument("--full-choice", choices=["swap", "both-a", "both-b"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite evidence")
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "nuvem"))
    from benchmark import solver_bridge as bridge, validators
    from benchmark.extract.from_solver import project_from_solver
    m = bridge.engine()
    import core.engine.wall_stepper as stepper
    source = root / "nuvem/benchmark/projects" / args.project / "input.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    nodes, walls, ends, openings = bridge.plan_from_input(data)
    catalog, _cells, _dropped = bridge.catalog_from_input(data)
    baseline = m.solve_all_intersections(nodes, walls, catalog, openings, ends)
    node = nodes[args.node]
    if node["kind"] != "L_CORNER":
        parser.error("Selected node must be L_CORNER")
    original = stepper.solve_l_corner
    result = original(node, walls, catalog, args.node, openings, nodes, ends)
    if not result["ok"]:
        parser.error("Selected L has no two-piece solution to compare")

    def describe(piece):
        return {"wall_idx": piece.get("wall_idx"), "node_index": piece.get("node_index"),
                "course": piece["course"], "code": piece["logical_code"],
                "reason": piece.get("placement_reason"),
                "origin_cm": [piece["origin_world"].X * 30.48, piece["origin_world"].Y * 30.48],
                "axis": [piece["x_dir"].X, piece["x_dir"].Y]}

    fixed = [p for p in baseline["candidates"] if p.get("node_index") != args.node]
    alternatives = {}
    base_z = bridge._ft((data.get("settings") or {}).get("base_z_cm") or 0.0)
    for name, pair in choices(result).items():
        pieces = fixed + list(pair)
        collisions = []
        for i, j in m.validate_same_course_collision(pieces):
            a, b = pieces[i], pieces[j]
            if args.node not in (a.get("node_index"), b.get("node_index")):
                continue
            collisions.append({"a": describe(a), "b": describe(b),
                               "overlap_cm": m._obb_min_overlap(m._candidate_obb(a), m._candidate_obb(b)) * 30.48})
        gate = m.controlled_beta_preflight(
            {"num_courses": 2, "candidates": list(pair), "course_candidates": {0: [pair[0]], 1: [pair[1]]}},
            walls, openings, catalog, base_z)
        alternatives[name] = {"pieces": [describe(p) for p in pair], "collisions": collisions,
                              "opening_violations_first_two_courses": gate["opening_violations"],
                              "alternating_owners": pair[0]["wall_idx"] != pair[1]["wall_idx"]}
    minimum_footprints = []
    for wi in m._l_corner_wall_pair(node):
        point = m._node_contact_point_for_wall(node, wi)
        _end, direction, _length, _t = m._wall_end_and_dir_near_point(walls, wi, point)
        room = m._corner_wall_room_ft(walls, openings, wi, point, direction,
                                     nodes=nodes, end_to_node=ends, exclude_node_index=args.node)
        for code in ("B34", "C09", "C04"):
            entry = catalog[code]
            if room is not None and bridge._ft(entry["length_cm"]) > room + 1e-6:
                continue
            origin = point + direction * bridge._ft(entry["length_cm"] / 2.0)
            for ci, course in enumerate(("A", "B")):
                candidate = m._make_block_candidate(code, entry, course, origin, direction,
                                                     "EXPERIMENT_MINIMUM_FOOTPRINT", node_index=args.node, wall_idx=wi)
                gate = m.controlled_beta_preflight(
                    {"num_courses": 2, "candidates": [candidate], "course_candidates": {0: [], 1: [], ci: [candidate]}},
                    walls, openings, catalog, base_z)
                overlaps = [describe(other) for other in fixed if other["course"] == course
                            and m._obb_min_overlap(m._candidate_obb(candidate), m._candidate_obb(other)) > m.BOND_COLLISION_EPS_FT]
                minimum_footprints.append({"piece": describe(candidate), "room_cm": room * 30.48 if room is not None else None,
                                           "colliding_neighbors": overlaps, "opening_violations": gate["opening_violations"]})
    payload = {"status": "EXPERIMENT_NOT_PRODUCTION_FIX", "node_index": args.node,
               "project": args.project, "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
               "instrumentation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "alternatives": alternatives,
               "relaxed_minimum_footprints_not_approved_layouts": minimum_footprints}
    if args.full_choice:
        calls = []

        def hypothesis(*call_args, **kwargs):
            answer = original(*call_args, **kwargs)
            ni = kwargs.get("node_index", call_args[3] if len(call_args) > 3 else None)
            if ni == args.node and answer["ok"]:
                pair = choices(answer)[args.full_choice]
                answer = dict(answer, course_a=pair[0], course_b=pair[1])
                calls.append([describe(p) for p in pair])
            return answer

        stepper.solve_l_corner = hypothesis
        try:
            solved, walls, nodes, openings, catalog, base, courses, notes = bridge.run_solver(data)
        finally:
            stepper.solve_l_corner = original
        solved["num_courses"] = courses
        project = project_from_solver(args.project, solved, walls, nodes, openings, catalog, base, courses)
        findings, errors = validators.run_all(project)
        payload["full"] = {"choice": args.full_choice, "hypothesis_calls": calls,
                           "project": project, "findings": findings, "validator_errors": errors,
                           "preflight": m.controlled_beta_preflight(solved, walls, openings, catalog, base),
                           "bond_audits": solved.get("wall_bond_audits"),
                           "unmodulated_walls": solved.get("unmodulated_walls"),
                           "intersection_failures": solved.get("intersection_failures"),
                           "physical_blocks": sum(len(pcs) for pcs in solved["course_candidates"].values()),
                           "aggregate_collisions": len(solved["collisions"])}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, separators=(",", ":"))
    print(json.dumps({"node": args.node, "choices": {k: {"collisions": len(v["collisions"]),
                     "opening_violations": len(v["opening_violations_first_two_courses"]),
                     "alternating_owners": v["alternating_owners"]} for k, v in alternatives.items()},
                     "minimum_footprints": [{"wall": p["piece"]["wall_idx"], "course": p["piece"]["course"],
                                             "code": p["piece"]["code"], "collisions": len(p["colliding_neighbors"]),
                                             "openings": len(p["opening_violations"])} for p in minimum_footprints]}))
    if args.full_choice:
        from collections import Counter
        full = payload["full"]
        print(json.dumps({"physical_blocks": full["physical_blocks"], "aggregate_collisions": full["aggregate_collisions"],
                          "physical_collisions": len(full["preflight"]["collisions"]),
                          "opening_violations": len(full["preflight"]["opening_violations"]),
                          "findings": dict(Counter(f["code"] for f in full["findings"])),
                          "validator_errors": errors, "hypothesis_calls": len(calls)}))


if __name__ == "__main__":
    main()
