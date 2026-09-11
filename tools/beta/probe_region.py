"""Solve an explicit wall selection without editing any official benchmark file.

Selection changes boundary topology; this is a fresh region solve, not a crop
of a previously solved building. Source coordinates/openings are unchanged.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--walls", nargs="+", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "nuvem"))
    from benchmark import solver_bridge, validators
    from benchmark.extract.from_solver import project_from_solver
    if args.output.exists():
        parser.error("Refusing to overwrite region evidence")
    source = root / "nuvem/benchmark/projects" / args.project / "input.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    indices = sorted(set(args.walls))
    if not indices or indices[0] < 0 or indices[-1] >= len(data["walls"]):
        parser.error("Invalid source wall indices")
    selected = [data["walls"][i] for i in indices]
    data["walls"] = selected
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    start = time.monotonic()
    result, walls, nodes, openings, catalog, base, courses, notes = solver_bridge.run_solver(data)
    elapsed = time.monotonic() - start
    result["num_courses"] = courses
    m = solver_bridge.engine()
    gate = m.controlled_beta_preflight(result, walls, openings, catalog, base)
    project = project_from_solver(args.project + "_beta_selection", result, walls, nodes,
                                  openings, catalog, base, courses, metadata={"solver_notes": notes})
    findings, errors = validators.run_all(project)
    payload = {"head": head, "solver_seconds": elapsed,
               "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "source_project": args.project, "source_indices": indices,
               "source_wall_keys": [wall["key"] for wall in selected], "input_selection": data,
               "result_project": project, "preflight": gate,
               "unmodulated_walls": result.get("unmodulated_walls"),
               "non_modular": result.get("non_modular"),
               "intersection_failures": result.get("intersection_failures"),
               "bond_audits": result.get("wall_bond_audits"),
               "findings": findings, "validator_errors": errors,
               "node_counts": dict(Counter(n["kind"] for n in nodes)),
               "physical_blocks": sum(len(pcs) for pcs in result["course_candidates"].values())}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, separators=(",", ":"))
    print(json.dumps({"head": head, "source_indices": indices, "seconds": elapsed,
                      "physical_blocks": payload["physical_blocks"], "preflight_ok": gate["ok"],
                      "node_counts": payload["node_counts"], "validator_errors": errors,
                      "unmodulated_walls": result.get("unmodulated_walls"),
                      "findings": dict(Counter(f["code"] for f in findings)),
                      "bond_audits_failing": [wi for wi, audit in payload["bond_audits"].items() if not audit["ok"]]}, indent=2))


if __name__ == "__main__":
    main()
