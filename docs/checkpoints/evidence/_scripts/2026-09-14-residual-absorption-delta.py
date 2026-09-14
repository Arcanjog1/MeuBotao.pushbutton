# -*- coding: utf-8 -*-
"""Delta por PAREDE da regra 30.8 (folga residual entre dois nos) na
bancada BUTANTA 34 paredes: achados do benchmark e auditoria com a regra
desligada x ligada, separando paredes que JA' fechavam das que estavam com
trecho nao modular. Uso: py -3 2026-09-14-residual-absorption-delta.py [CHANNEL]
"""
import json
import sys
from collections import Counter, defaultdict

import channel_bench_common as cb

m = cb.m
from benchmark import runner as brunner  # noqa: E402
from benchmark.extract import from_solver  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

strategy = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
masonry, ops = cb.load_inputs()
ctx = cb.build(masonry, ops)
catalog = dict(cb.CATALOG)
catalog.update(m.channel_logical_catalog())


def run(flag):
    ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED = flag
    res = cb.solve(ctx, opening_reinforcement_strategy=strategy)
    project = from_solver.project_from_solver("x", res, ctx["walls"], ctx["nodes"], ctx["openings_per_wall"],
                                              catalog, 0.0, cb.NUM_COURSES)
    findings, _score, _c = brunner.evaluate_project(project, None)
    # assign_ids ordena as paredes por geometria: casar pelo eixo, nao pela ordem
    by_geom = dict(((round(w["start_cm"][0], 1), round(w["start_cm"][1], 1),
                     round(w["end_cm"][0], 1), round(w["end_cm"][1], 1)), w["id"]) for w in project["walls"])
    wall_ids = []
    for wi in range(len(ctx["walls"])):
        a = ctx["walls"][wi][0].GetEndPoint(0)
        b = ctx["walls"][wi][0].GetEndPoint(1)
        wall_ids.append(by_geom[(round(a.X * cb.F2CM, 1), round(a.Y * cb.F2CM, 1),
                                 round(b.X * cb.F2CM, 1), round(b.Y * cb.F2CM, 1))])
    by_wall = defaultdict(Counter)
    for f in findings:
        by_wall[f.get("wall")][f["code"]] += 1
    nonmod = Counter(s["wall_idx"] for s in res["non_modular"])
    audits = dict((wi, a) for wi, a in res["wall_bond_audits"].items())
    return res, wall_ids, by_wall, nonmod, audits


r0, ids0, f0, n0, a0 = run(False)
r1, ids1, f1, n1, a1 = run(True)
ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED = True
rows = []
for wi in range(len(ctx["walls"])):
    wid = ids0[wi]
    delta = dict((code, f1[wid][code] - f0[wid][code]) for code in set(f0[wid]) | set(f1[wid])
                 if f1[wid][code] != f0[wid][code])
    was_nonmod = n0.get(wi, 0)
    audit_change = (a0.get(wi, {}).get("ok"), a1.get(wi, {}).get("ok"))
    if delta or n0.get(wi, 0) != n1.get(wi, 0) or audit_change[0] != audit_change[1]:
        rows.append({"wall_idx": wi, "wall_id": ctx["ids"][wi], "non_modular_before": was_nonmod,
                     "non_modular_after": n1.get(wi, 0), "audit_ok_before": audit_change[0],
                     "audit_ok_after": audit_change[1], "finding_delta": delta,
                     "audit_problems_after": [str(p)[:160] for p in a1.get(wi, {}).get("problems", [])]})
absorptions = r1.get("residual_absorptions")
out = {"strategy": strategy, "walls_changed": rows,
       "totals_before": dict(sum((f0[w] for w in f0), Counter())),
       "totals_after": dict(sum((f1[w] for w in f1), Counter())),
       "walls_changed_already_closed": [r["wall_id"] for r in rows if r["non_modular_before"] == 0]}
print(json.dumps(out, indent=1, sort_keys=True))
