# -*- coding: utf-8 -*-
"""Assinatura FISICA do solve (CHANNEL, 34 paredes, 17 fiadas) sob variacoes da
entrada: normal | reverse (pontas invertidas) | permute (ordem invertida) |
translate (+1000,+500 cm). Assinatura: por fiada, codigo + centro (0,1 cm) +
centro do vazado menor (0,1 cm) - independe de indice, ordem e sentido."""
import hashlib, json, sys, copy
sys.path.insert(0, ".")
import evalsolve
import tbench as tb
m = tb.m
mode = sys.argv[1]
doc = copy.deepcopy(tb.load_target())
DX, DY = (1000.0, 500.0) if mode == "translate" else (0.0, 0.0)
for w in doc["walls"]:
    if mode == "reverse":
        w["p0"], w["p1"] = w["p1"], w["p0"]
    w["p0"] = [w["p0"][0] + DX, w["p0"][1] + DY] + list(w["p0"][2:])
    w["p1"] = [w["p1"][0] + DX, w["p1"][1] + DY] + list(w["p1"][2:])
for o in doc["openings"]:
    o["bb"] = [o["bb"][0] + DX, o["bb"][1] + DY, o["bb"][2], o["bb"][3] + DX, o["bb"][4] + DY, o["bb"][5]]
    o["o"] = [o["o"][0] + DX, o["o"][1] + DY] + list(o["o"][2:])
ids = sorted(evalsolve.masonry_wall_ids())
walls = [w for w in doc["walls"] if w["id"] in ids]
if mode == "permute":
    walls = list(reversed(walls))
doc["walls"] = walls
ctx = tb.build(doc)
from core.engine import small_void_alignment as sva
if "--off" in sys.argv:
    m.CHANNEL_PHYSICAL_TOLERANCES_ENABLED = False
    sva.SMALL_VOID_ORIENTATION_ENABLED = False
    from core.engine import wall_stepper as _ws
    _ws.COMPENSATOR_PAIR_FUSION_ENABLED = False
res = tb.solve(ctx, courses=17)
F = 30.48
rows = []
for ci in sorted(res["course_candidates"]):
    for c in res["course_candidates"][ci]:
        o = c["origin_world"]
        cell = sva.candidate_small_cell(c)
        sc = "" if cell is None else "%.1f,%.1f" % (round(cell["point"].X * F - DX, 1), round(cell["point"].Y * F - DY, 1))
        rows.append("%d|%s|%.1f,%.1f|%s" % (ci, c["logical_code"], round(o.X * F - DX, 1), round(o.Y * F - DY, 1), sc))
rows.sort()
sig = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
json.dump(rows, open("det_%s%s.json" % (mode, "_off" if "--off" in sys.argv else ""), "w"))
print(mode, sig, len(rows), res["small_void_alignment"]["after"], res["physical_support"]["counts"])
