# -*- coding: utf-8 -*-
"""Bancada offline CHANNEL x legado - BUTANTA 1o PAV.

Uso:
  py -3 2026-09-14-channel-bench.py [--walls N] [--json saida.json]

Roda o MESMO solve com opening_reinforcement_strategy=None e "CHANNEL",
pontua os dois pela regua do benchmark (validators do repo) e pelo validador
CHANNEL, e classifica cada PRISM_CONTINUOUS_JOINT por tipo de fronteira
(fill|tie, no|fill, fill|fill, tie|tie). `--walls N` recorta as N primeiras
paredes (ordem estavel por id fisico) para a escada de escala.
"""
import hashlib
import json
import sys
import time
from collections import Counter

import channel_bench_common as cb

m = cb.m
from benchmark import model as bmodel  # noqa: E402
from benchmark import runner as brunner  # noqa: E402
from benchmark.extract import from_solver  # noqa: E402

BIND = set(bmodel.BINDING_ROLES)


def _args():
    walls = None
    out = None
    ids = None
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--walls":
            walls = int(argv[i + 1])
        if a == "--json":
            out = argv[i + 1]
        if a == "--ids":
            ids = set(int(x) for x in argv[i + 1].split(","))
    return walls, out, ids


def signature(course_candidates):
    h = hashlib.sha256()
    for ci in sorted(course_candidates):
        rows = []
        for c in course_candidates[ci]:
            o = c["origin_world"]
            rows.append("%s|%s|%.4f|%.4f|%.3f|%s" % (c["logical_code"], c.get("wall_idx"), o.X, o.Y,
                                                     c["length_cm"], c.get("placement_reason")))
        for r in sorted(rows):
            h.update(("%d:%s\n" % (ci, r)).encode("utf-8"))
    return h.hexdigest()


def prism_classes(project, findings):
    blocks = {}
    for w in project["walls"]:
        for row in w["rows"]:
            for b in row["blocks"]:
                blocks[b["id"]] = b

    def kind(js):
        lb = blocks.get(js["left_block"], {}).get("role") in BIND
        rb = blocks.get(js["right_block"], {}).get("role") in BIND
        if lb and rb:
            return "tie|tie"
        if lb or rb:
            return "fill|tie"
        return "fill|fill"

    out = Counter()
    for f in findings:
        if f["code"] != "PRISM_CONTINUOUS_JOINT":
            continue
        ka, kb = kind(f["joint_a"]), kind(f["joint_b"])
        pair = "x".join(sorted((ka, kb)))
        if "fill|tie" in (ka, kb) and ka != kb:
            out["no|fill (fill|tie x outro)"] += 1
        out[pair] += 1
    return out


def score(ctx, res, catalog, label):
    project = from_solver.project_from_solver(label, res, ctx["walls"], ctx["nodes"], ctx["openings_per_wall"],
                                              catalog, 0.0, cb.NUM_COURSES)
    findings, sc, _cmp = brunner.evaluate_project(project, None)
    codes = Counter(f["code"] for f in findings)
    return project, findings, codes


def run(ctx, strategy):
    t0 = time.time()
    res = cb.solve(ctx, opening_reinforcement_strategy=strategy)
    dt = time.time() - t0
    return res, dt


def main():
    n_walls, out_path, ids = _args()
    masonry, ops = cb.load_inputs()
    masonry = sorted(masonry, key=lambda w: (round(float(w["p0_cm"][0]), 1), round(float(w["p0_cm"][1]), 1),
                                             round(float(w["p1_cm"][0]), 1), round(float(w["p1_cm"][1]), 1)))
    if ids:
        keep = ids
    elif n_walls:
        keep = set(w["id"] for w in masonry[:n_walls])
    else:
        keep = None
    ctx = cb.build(masonry, ops, wall_filter=(lambda wid: wid in keep) if keep else None)
    audit_catalog = dict(cb.CATALOG)
    audit_catalog.update(m.channel_logical_catalog())
    report = {"walls": len(ctx["walls"]), "openings": sum(len(v) for v in ctx["openings_per_wall"])}
    for strategy in (None, "CHANNEL"):
        res, dt = run(ctx, strategy)
        label = strategy or "LEGACY"
        project, findings, codes = score(ctx, res, audit_catalog, label)
        pf = m.controlled_beta_preflight(res, ctx["walls"], ctx["openings_per_wall"], cb.CATALOG, 0.0)
        cc = res["course_candidates"]
        entry = {
            "solve_s": round(dt, 2),
            "pieces": sum(len(v) for v in cc.values()),
            "codes": dict(Counter(c["logical_code"] for v in cc.values() for c in v)),
            "signature": signature(cc),
            "bench_codes": dict((k, v) for k, v in sorted(codes.items())),
            "prism_classes": dict(prism_classes(project, findings)),
            "preflight_ok": pf["ok"], "preflight_opening_violations": len(pf["opening_violations"]),
            "preflight_collisions": len(pf["collisions"]),
            "bond_reproved_walls": sum(1 for a in (res.get("wall_bond_audits") or {}).values() if not a["ok"]),
            "non_modular": len(res.get("non_modular") or []),
            "door_void_violations": len(res.get("door_void_violations") or []),
        }
        rein = res.get("opening_reinforcement")
        if rein:
            entry["channel_validation"] = rein["validation"]["counts"]
            entry["channel_findings"] = dict(Counter(f["code"] for f in rein["findings"]))
            entry["free_to_top"] = len(rein["free_to_top"])
            entry["node_crossings"] = len(rein["node_crossings"])
            entry["runs"] = len(rein["runs"])
        report[label] = entry
    # delta de achados do benchmark
    a, b = report["LEGACY"]["bench_codes"], report["CHANNEL"]["bench_codes"]
    report["bench_delta"] = dict((k, b.get(k, 0) - a.get(k, 0)) for k in sorted(set(a) | set(b))
                                 if b.get(k, 0) != a.get(k, 0))
    print(json.dumps(report, indent=1, sort_keys=True))
    if out_path:
        json.dump(report, open(out_path, "w", encoding="utf-8"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
