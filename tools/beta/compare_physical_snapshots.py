"""Compare census geometry without rerunning either solver or changing scores."""
import argparse
from collections import Counter
import json
from pathlib import Path


def piece_key(snapshot, index):
    c = snapshot["candidates"][index]
    return (snapshot["wall_keys"][c["wall_idx"]], c["logical_code"],
            tuple(round(v * 30.48, 5) for v in c["origin_world"]),
            tuple(round(v, 8) for v in c["x_dir"]),
            c["length_cm"], c["width_cm"])


def records(snapshot, physical):
    rows = snapshot["physical"].items() if physical else [("aggregate", {
        "collisions": snapshot["aggregate_collisions"]})]
    found = {}
    for course, row in rows:
        for a, b in row["collisions"]:
            key = (course, tuple(sorted((piece_key(snapshot, a), piece_key(snapshot, b)))))
            found[key] = {"course": course, "indexes": [a, b],
                          "pieces": [snapshot["candidates"][a], snapshot["candidates"][b]],
                          "wall_keys": [snapshot["wall_keys"][snapshot["candidates"][i]["wall_idx"]]
                                        for i in (a, b)]}
    return found


def compare(before, after, physical):
    old, new = records(before, physical), records(after, physical)
    added = [new[k] for k in sorted(new.keys() - old.keys())]
    removed = [old[k] for k in sorted(old.keys() - new.keys())]
    def counts(rows):
        return dict(Counter(" | ".join(sorted(r["wall_keys"])) for r in rows))
    return {"before_unique": len(old), "after_unique": len(new),
            "before_by_wall_pair": counts(old.values()),
            "after_by_wall_pair": counts(new.values()),
            "added": added, "removed": removed,
            "added_by_wall_pair": counts(added), "removed_by_wall_pair": counts(removed)}


def collision_volume_delta(before, after):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    def polygon(c):
        p = [v * 30.48 for v in c["origin_world"][:2]]
        x, y = c["x_dir"], c["y_dir"]
        hx, hy = c["length_cm"] / 2, c["width_cm"] / 2
        return Polygon([(p[0] + sx * hx * x[0] + sy * hy * y[0],
                         p[1] + sx * hx * x[1] + sy * hy * y[1])
                        for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]])

    def regions(snapshot):
        by_course = {}
        polygons = [polygon(c) for c in snapshot["candidates"]]
        for ci, row in snapshot["physical"].items():
            by_course[ci] = unary_union([polygons[a].intersection(polygons[b])
                                        for a, b in row["collisions"]])
        return by_course
    old, new = regions(before), regions(after)
    rows = []
    for ci in sorted(old, key=int):
        added = new[ci].difference(old[ci])
        removed = old[ci].difference(new[ci])
        rows.append({"course": int(ci), "before_cm2": old[ci].area,
                     "after_cm2": new[ci].area, "new_cm2": added.area,
                     "removed_cm2": removed.area, "new_wkt": added.wkt})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    before = json.loads(args.before.read_text(encoding="utf-8"))
    after = json.loads(args.after.read_text(encoding="utf-8"))
    if before["input_sha256"] != after["input_sha256"]:
        parser.error("Inputs differ")
    output = {"before": before["head"], "after": after["head"],
              "aggregate": compare(before, after, False),
              "physical": compare(before, after, True),
              "collision_regions": collision_volume_delta(before, after)}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
    for key in ("aggregate", "physical"):
        block = output[key]
        print(key, block["before_unique"], "->", block["after_unique"],
              "added", len(block["added"]), "removed", len(block["removed"]))
        print("added by walls:", json.dumps(block["added_by_wall_pair"], indent=2))


if __name__ == "__main__":
    main()
