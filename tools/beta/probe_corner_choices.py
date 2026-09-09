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
    for name, pair in choices(result).items():
        pieces = fixed + list(pair)
        collisions = []
        for i, j in m.validate_same_course_collision(pieces):
            a, b = pieces[i], pieces[j]
            if args.node not in (a.get("node_index"), b.get("node_index")):
                continue
            collisions.append({"a": describe(a), "b": describe(b),
                               "overlap_cm": m._obb_min_overlap(m._candidate_obb(a), m._candidate_obb(b)) * 30.48})
        alternatives[name] = {"pieces": [describe(p) for p in pair], "collisions": collisions,
                              "alternating_owners": pair[0]["wall_idx"] != pair[1]["wall_idx"]}
    payload = {"status": "EXPERIMENT_NOT_PRODUCTION_FIX", "node_index": args.node,
               "project": args.project, "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
               "instrumentation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "alternatives": alternatives}
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
                     "alternating_owners": v["alternating_owners"]} for k, v in alternatives.items()}}))
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
