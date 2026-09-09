"""Attribute aggregate and physical collision deltas to immutable stage snapshots."""
import argparse
from collections import Counter
import json
from pathlib import Path


def report(snapshots):
    if len({s["input_sha256"] for s in snapshots}) != 1:
        raise ValueError("Stage inputs differ")
    stages = []
    for s in snapshots:
        pieces = s["candidates"]
        def counts(pairs):
            return Counter(tuple(sorted((pieces[i]["wall_idx"], pieces[j]["wall_idx"]))) for i, j in pairs)
        stages.append({"head": s["head"], "summary": s["summary"], "wall_keys": s["wall_keys"],
                       "aggregate": counts(s["aggregate_collisions"]),
                       "physical": counts(pair for row in s["physical"].values() for pair in row["collisions"])})
    changed = {}
    for mode in ("aggregate", "physical"):
        pairs = set().union(*(s[mode] for s in stages))
        changed[mode] = [{"walls": list(pair), "counts": [s[mode][pair] for s in stages],
                          "wall_keys_by_stage": [[s["wall_keys"][i] for i in pair] for s in stages]}
                         for pair in sorted(pairs) if len({s[mode][pair] for s in stages}) > 1]
    return {"input_sha256": snapshots[0]["input_sha256"],
            "stages": [{"head": s["head"], "summary": s["summary"]} for s in stages], "changed_pairs": changed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshots", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = report([json.loads(p.read_text(encoding="utf-8")) for p in args.snapshots])
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    print(json.dumps(data["stages"], indent=2))


if __name__ == "__main__":
    main()
