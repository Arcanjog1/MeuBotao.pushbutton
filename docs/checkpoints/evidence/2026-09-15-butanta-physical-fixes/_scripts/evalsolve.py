# -*- coding: utf-8 -*-
"""Roda o solver na bancada do TARGET e imprime as metricas fisicas.
uso: evalsolve.py [all|masonry] [CHANNEL|NONE] [courses]"""
import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics  # noqa: E402
import phys  # noqa: E402
import tbench as tb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def masonry_wall_ids():
    T = phys.load(os.path.join(HERE, "target_1pav.clean.json"))
    H = phys.load(os.path.join(HERE, "human_1pav.clean.json"))
    walls = [phys.Wall(w["id"], w["p0"], w["p1"], w["uid"]) for w in T["walls"]]
    recs = [phys.piece_record(p) for p in H["pieces"]]
    phys.assign_walls(recs, walls, by_stamp=False)
    cnt = collections.Counter(r["wall"].id for r in recs if r["wall"] is not None)
    return set(w.id for w in walls if cnt.get(w.id, 0) >= 20)


if __name__ == "__main__":
    subset = sys.argv[1] if len(sys.argv) > 1 else "all"
    strategy = sys.argv[2] if len(sys.argv) > 2 else "CHANNEL"
    courses = int(sys.argv[3]) if len(sys.argv) > 3 else 17
    doc = tb.load_target()
    ids = masonry_wall_ids() if subset == "masonry" else None
    ctx = tb.build(doc, wall_ids=ids)
    t0 = time.time()
    res = tb.solve(ctx, strategy=(None if strategy == "NONE" else strategy), courses=courses)
    dt = time.time() - t0
    out, bad_under, b34bad, hs, us = metrics.summary(ctx, res, tb.m, courses, label="%s/%s/%d" % (subset, strategy, courses))
    out["solve_s"] = round(dt, 1)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    g = collections.defaultdict(list)
    for wid, c, a, b in hs:
        g[(wid, round(a / 5) * 5, round(b / 5) * 5)].append(c)
    print("holes:", sorted(g.items()))
    print("unsupported:", [(p.wall, p.course, p.code, round(p.lo or 0, 1), f) for p, f, v in us][:30])
    print("underfill:", [(w, tl, th, s, [round(c, 2) for c in cv]) for (w, tl, th, s, cv) in bad_under])
