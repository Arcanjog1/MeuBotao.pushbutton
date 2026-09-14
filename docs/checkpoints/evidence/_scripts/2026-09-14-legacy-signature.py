# -*- coding: utf-8 -*-
"""Assinatura fisica do motor LEGADO (sem estrategia de reforco) nas 34 paredes
do BUTANTA 1o PAV, no checkout onde este arquivo esta'. Copiado para um
worktree da main para provar `opening_reinforcement_strategy=None` == main.
Uso: py -3 2026-09-14-legacy-signature.py
"""
import hashlib
from collections import Counter

import channel_bench_common as cb

masonry, ops = cb.load_inputs()
masonry = sorted(masonry, key=lambda w: (round(float(w["p0_cm"][0]), 1), round(float(w["p0_cm"][1]), 1),
                                         round(float(w["p1_cm"][0]), 1), round(float(w["p1_cm"][1]), 1)))
ctx = cb.build(masonry, ops)
res = cb.solve(ctx)
h = hashlib.sha256()
pieces = 0
for ci in sorted(res["course_candidates"]):
    rows = []
    for c in res["course_candidates"][ci]:
        o = c["origin_world"]
        rows.append("%s|%s|%.4f|%.4f|%.3f|%s" % (c["logical_code"], c.get("wall_idx"), o.X, o.Y,
                                                 c["length_cm"], c.get("placement_reason")))
    pieces += len(rows)
    for r in sorted(rows):
        h.update(("%d:%s\n" % (ci, r)).encode("utf-8"))
print("legacy", h.hexdigest(), "pieces", pieces, "non_modular", len(res["non_modular"]),
      "bond_reproved", sum(1 for a in res["wall_bond_audits"].values() if not a["ok"]),
      "codes", dict(Counter(c["logical_code"] for pcs in res["course_candidates"].values() for c in pcs)))
