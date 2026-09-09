"""Replay the current beta gate over versioned physical snapshots, without solving."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite evidence")
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "nuvem"))
    from benchmark import solver_bridge
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    source = root / "nuvem/benchmark/projects" / snapshot["project"] / "input.json"
    import hashlib
    if hashlib.sha256(source.read_bytes()).hexdigest() != snapshot["input_sha256"]:
        raise ValueError("Snapshot and input do not match")
    data = json.loads(source.read_text(encoding="utf-8"))
    _nodes, walls, _ends, openings = solver_bridge.plan_from_input(data)
    catalog, _cells, _dropped = solver_bridge.catalog_from_input(data)
    m = solver_bridge.engine()
    pcs = snapshot["candidates"]
    for c in pcs:
        for key in ("origin_world", "x_dir", "y_dir"):
            c[key] = m.XYZ(*c[key])
    result = {"num_courses": len(snapshot["physical"]), "candidates": pcs,
              "course_candidates": {int(ci): [pcs[i] for i in row["candidates"]]
                                    for ci, row in snapshot["physical"].items()}}
    base = solver_bridge._ft((data.get("settings") or {}).get("base_z_cm") or 0)
    gate = m.controlled_beta_preflight(result, walls, openings, catalog, base)
    payload = {"snapshot_head": snapshot["head"], "input_sha256": snapshot["input_sha256"],
               "gate_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
               "gate_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True),
               "gate_source_sha256": hashlib.sha256((root / "nuvem/core/wall_modeling.py").read_bytes()).hexdigest(),
               "project": snapshot["project"], "gate": gate}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, separators=(",", ":"))
    print(json.dumps({"ok": gate["ok"], "opening_violations": len(gate["opening_violations"]),
                      "collisions": len(gate["collisions"]), "errors": gate["errors"]}))


if __name__ == "__main__":
    main()
