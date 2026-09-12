"""Uso: python3 nodefill.py <root> <label> [projects...]
Medidor no'|fill (node_fill_prism_violations) com/sem metade simetrica."""
import sys, os, json, time
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]
projects = sys.argv[3:] or ["torre_easy_lo_r00_tp1", "torre_easy_lo_r00_tgd"]
os.chdir(root); sys.path.insert(0, root); sys.path.insert(0, os.path.join(root, "tests"))
import test_block_node_fill_revalidation as T
out = {"label": label, "root": root, "projects": {}}
for pid in projects:
    ids = [w["id"] for w in json.load(open(os.path.join(root, "nuvem/benchmark/projects", pid, "input.json")))["walls"]]
    entry = {}
    for enabled in (False, True):
        t0 = time.time()
        res, walls = T._corpus(pid, enabled)
        v = T.node_fill_prism_violations(walls, res["candidates"])
        sig = [x for x in v if abs(x[1] - 34.5) < 1e-6 and x[2] == "B"]
        key = "on" if enabled else "off"
        entry[key] = {"count": len(v), "sig": len(sig), "seconds": round(time.time() - t0, 1),
                      "violations": [[ids[w], w, t, c] for (w, t, c) in v]}
        dump = [int(x) for x in os.environ.get("DUMP_WALLS", "").split(",") if x.strip()]
        if dump:
            pieces = T.wall_course_pieces(walls, res["candidates"])
            by_idx = {}
            for c in res["candidates"]:
                by_idx.setdefault(c.get("wall_idx"), []).append(c)
            entry[key]["walls"] = {}
            for w in dump:
                p0, _p1, d, _l, _t = T.m._wall_axis_and_length(walls, w)
                rows = {}
                for course in ("A", "B"):
                    items = []
                    for c in by_idx.get(w, []):
                        if c.get("course") != course: continue
                        lo, hi = T.m._candidate_extent_on_wall_axis(c, p0, d)
                        items.append([round(min(lo, hi), 2), round(max(lo, hi), 2), c.get("logical_code"), c.get("placement_reason"), c.get("node_index"), bool(T.m._is_tie_candidate(c))])
                    rows[course] = sorted(items)
                entry[key]["walls"][ids[w]] = {"wall_idx": w, "rows": rows,
                    "length_cm": round(_l * 100.0 / T.m.FEET_PER_METER, 2)}
        print(label, pid, key, len(v), "sig", len(sig), sorted(set(ids[w] for (w, _t, _c) in v)), flush=True)
    out["projects"][pid] = entry
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nodefill_%s.json" % label), "w"), indent=1, ensure_ascii=False)
