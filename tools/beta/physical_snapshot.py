"""Read-only solver census: distinguish templates from physical courses.

Runs the selected checkout in a fresh process and never writes benchmark files.
Output retains candidate indexes plus geometry, not unstable W labels alone.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def source_fingerprint(repo):
    digest = hashlib.sha256()
    for path in sorted((repo / "nuvem/core").rglob("*.py")):
        digest.update(path.relative_to(repo).as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / "nuvem"))
    from benchmark import solver_bridge, model
    source = repo / "nuvem/benchmark/projects" / args.project / "input.json"
    source_bytes = source.read_bytes()
    data = json.loads(source_bytes.decode("utf-8"))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    status_before = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
    code_hash = source_fingerprint(repo)
    instrumentation_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    result, walls, nodes, openings, catalog, base, courses, notes = solver_bridge.run_solver(data)
    elapsed = time.monotonic() - clock
    m = solver_bridge.engine()
    candidates = result["candidates"]
    indexes = {id(c): i for i, c in enumerate(candidates)}
    keys = []
    for line, thickness, _locks in walls:
        p, q = line.GetEndPoint(0), line.GetEndPoint(1)
        keys.append(model.wall_stable_key(
            [p.X * 30.48, p.Y * 30.48], [q.X * 30.48, q.Y * 30.48],
            thickness * 30.48))

    def piece(c):
        item = {k: c.get(k) for k in (
            "wall_idx", "secondary_wall_idx", "course", "course_variant",
            "logical_code", "length_cm", "width_cm", "placement_reason",
            "node_index", "mirrored", "rotation_deg")}
        for k in ("origin_world", "x_dir", "y_dir"):
            p = c.get(k)
            item[k] = [p.X, p.Y, p.Z] if p is not None else None
        return item

    def door_records(items):
        return [{"wall": v["wall_idx"], "opening": v["opening_index"],
                 "candidate": indexes[id(v["candidate"])],
                 "overlap_cm": v["overlap_cm"]} for v in items]

    physical = {}
    step, error = m._course_height_ft(catalog, None)
    if error:
        raise RuntimeError(error)
    height = step - m._cm_to_ft(m.COURSE_JOINT_CM)
    for ci, pcs in sorted(result["course_candidates"].items()):
        z0, z1 = m._course_z_band(base, ci, step, height)
        active = m._filter_openings_per_wall_for_band(openings, z0, z1)
        violations = m.find_door_void_violations(pcs, walls, active, base)
        # Active filtering renumbers openings; recover their original identity.
        for v in violations:
            v["opening_index"] = openings[v["wall_idx"]].index(
                active[v["wall_idx"]][v["opening_index"]])
        physical[ci] = {
            "z_cm": [z0 * 30.48, z1 * 30.48],
            "candidates": [indexes[id(c)] for c in pcs],
            "collisions": [[indexes[id(pcs[i])], indexes[id(pcs[j])]]
                           for i, j in m.validate_same_course_collision(pcs)],
            "door_void": door_records(violations),
        }
    counts = Counter(c.get("wall_idx") for pcs in result["course_candidates"].values() for c in pcs)
    naive = m.find_door_void_violations(candidates, walls, openings, base)
    summary = {
        "blocks": sum(len(p["candidates"]) for p in physical.values()),
        "aggregate_collisions": len(result["collisions"]),
        "physical_course_collisions": sum(len(p["collisions"]) for p in physical.values()),
        "band_door_void": len(result["door_void_violations"]),
        "naive_all_openings_door_void": len(naive),
        "physical_active_door_void": sum(len(p["door_void"]) for p in physical.values()),
        "empty_walls": [i for i in range(len(walls)) if not counts[i]],
        "intersection_failures": len(result["intersection_failures"]),
    }
    if code_hash != source_fingerprint(repo) or source_bytes != source.read_bytes():
        raise RuntimeError("Solver source or input changed during snapshot; result is not immutable evidence")
    payload = {
        "head": head,
        "head_after": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "status_before": status_before, "solver_source_sha256": code_hash,
        "instrumentation_sha256": instrumentation_hash,
        "status": subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True),
        "input_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "started_utc": started, "solver_seconds": elapsed, "project": args.project,
        "summary": summary, "wall_keys": keys, "notes": notes,
        "wall_geometry_cm": [{"start_cm": [line.GetEndPoint(0).X * 30.48, line.GetEndPoint(0).Y * 30.48],
                              "end_cm": [line.GetEndPoint(1).X * 30.48, line.GetEndPoint(1).Y * 30.48],
                              "thickness_cm": thickness * 30.48} for line, thickness, _locks in walls],
        "openings_cm": [[[v * 30.48 for v in opening] for opening in wall] for wall in openings],
        "wall_bond_audits": result.get("wall_bond_audits"),
        "unmodulated_walls": result.get("unmodulated_walls"),
        "nodes": [{"kind": node.get("kind"),
                   "point_cm": [node["point"].X * 30.48, node["point"].Y * 30.48],
                   "arms": node.get("arms"), "main_wall_idx": node.get("main_wall_idx"),
                   "incoming_wall_idx": node.get("incoming_wall_idx"),
                   "crossing_walls": node.get("crossing_walls")} for node in nodes],
        "candidates": [piece(c) for c in candidates],
        "aggregate_collisions": result["collisions"],
        "band_door_void": door_records(result["door_void_violations"]),
        "naive_door_void": door_records(naive), "physical": physical,
        "bands": [b["course_indices"] for b in result["bands"]],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, separators=(",", ":"))
    print(json.dumps({"head": payload["head"], "seconds": elapsed, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
