# -*- coding: utf-8 -*-
"""Entregaveis 05..10."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_core import *
from emit import DEST, PROJECT, wj, CTOL, wall_key, CATMAP  # reaproveita e ja emite 01-04

P, O, OA, by_lvl = build()
g = wall_groups(P)
topz = dict((k, max(p["_z"][0] for p in v)) for k, v in g.items())
wspan = dict((k, (min(p["_s"][0] for p in v), max(p["_s"][1] for p in v))) for k, v in g.items())
SOLID = dict((r["fam"], r) for r in json.load(
    io.open(os.path.join(OUT, "solid_check.json"), encoding="utf-8")))

op_by_line = collections.defaultdict(list)
for o in OA:
    op_by_line[(o["lvl"], o["_ax"], round(o["_tc"]))].append(o)
MARG = 60.0

# ---------------- 05 channels ----------------
ch = []
for p in P:
    if not is_canaleta(p["fam"]):
        continue
    k = (p["parede"], p["lvl"]); zb, zt = p["_z"]; s0, s1 = p["_s"]
    ctx, rel = [], []
    for o in op_by_line.get((p["lvl"], p["_ax"], round(p["_tc"])), ()):
        a, b = o["_s"]
        if s1 <= a - MARG or s0 >= b + MARG:
            continue
        tag = {"PORTA": "DOOR", "JANELA": "WINDOW"}.get(o["titulo"], "OPENING")
        if abs(zb - o["_zt"]) < CTOL:
            ctx.append("ABOVE_" + tag); rel.append(o["id"])
        elif o["peitoril"] > .1 and abs(zt - o["_zb"]) < CTOL:
            ctx.append("BELOW_" + tag); rel.append(o["id"])
        elif o["peitoril"] > .1 and o["_zb"] - 25 < zt <= o["_zb"] + CTOL:
            ctx.append("BELOW_%s_2ND" % tag); rel.append(o["id"])
        elif min(abs(s1 - a), abs(s0 - b)) <= 25.0:
            ctx.append("NEAR_JAMB"); rel.append(o["id"])
    if abs(zb - topz[k]) < .6:
        ctx.append("TOP_BOND_BEAM")
    lo, hi = wspan[k]
    if abs(s0 - lo) < 2.0 or abs(s1 - hi) < 2.0:
        ctx.append("WALL_END")
    if not ctx:
        ctx = ["OTHER"]
    s = SOLID.get(p["fam"], {})
    ch.append({
        "element_id": p["id"], "unique_id": p["uid"],
        "family_name": p["fam"], "type_name": p["typ"], "category": "Modelos genéricos",
        "level": p["lvl"], "wall_label": p["parede"], "wall_physical_key": wall_key(p),
        "piece_length_cm": round(p["L"], 2), "piece_height_cm": round(p["H"], 2),
        "piece_width_cm": round(p["W"], 2),
        "solid_dims_cm_MEDIDO": s.get("solid_dims_cm"),
        "x_cm": round(p["x"], 2), "y_cm": round(p["y"], 2),
        "z_cm": round(p["z"], 2), "z_rel_cm": round(zb - DATUM[p["lvl"]], 2),
        "rotation_deg": round(p["rot"], 3),
        "span_along_axis_cm": [round(s0, 2), round(s1, 2)],
        "context": sorted(set(ctx)), "related_opening_ids": sorted(set(rel)),
        "is_top_course": "TOP_BOND_BEAM" in ctx,
    })
wj("05_channels.json", {"project": PROJECT, "n": len(ch),
                        "context_counts": dict(collections.Counter(
                            x for r in ch for x in r["context"])),
                        "channels": ch})

# ---------------- 06 cut blocks ----------------
NOM = {"BLOCO 34 CORTADO - 14x9x34": ("BLOCO 34 - 14x19x34", "ALTURA", 19.0, 9.0),
       "MEIO BLOCO CORTADO - 14x9x19": ("MEIO BLOCO - 14x19x19", "ALTURA", 19.0, 9.0),
       "BLOCO 54 CORTADO - 14x9x54": ("BLOCO 54 - 14x19x54", "ALTURA", 19.0, 9.0),
       "PASTILHA CORTADA- 14x9X4": ("PASTILHA - 14x19X4", "ALTURA", 19.0, 9.0),
       "BLOCO INTEIRO CORTADO - 14x9x39": ("BLOCO INTEIRO - 14x19x39", "ALTURA", 19.0, 9.0),
       "COMPENSADOR CORTADO - 14xVARx9": ("COMPENSADOR 14x19x9", "ALTURA", 19.0, 9.0),
       "COMPENSADOR CORTADO 14x19x9 (deitado)": ("COMPENSADOR 14x19x9 (deitado)", "COMPRIMENTO", 19.0, None),
       "BLOCO CANALETA CORTADO - 14x19xVAR": ("CANALETA INTEIRA - 14x19x39", "COMPRIMENTO", 39.0, None),
       "CANALETA J CORTADA - 14x9-19xVAR": ("CANALETA J - 14x9-19x19", "COMPRIMENTO", 19.0, None)}
cuts = []
for p in P:
    if not is_cut(p["fam"]):
        continue
    k = (p["parede"], p["lvl"]); zb, zt = p["_z"]; s0, s1 = p["_s"]
    base, mode, nom, cutval = NOM.get(p["fam"], (None, "DESCONHECIDO", None, None))
    ctx, dj = [], None
    for o in op_by_line.get((p["lvl"], p["_ax"], round(p["_tc"])), ()):
        a, b = o["_s"]
        d = min(abs(s1 - a), abs(s0 - b), abs(s0 - a), abs(s1 - b))
        if dj is None or d < dj:
            dj = round(d, 2)
        over = s1 > a + .6 and s0 < b - .6
        if over and abs(zb - o["_zt"]) < CTOL:
            ctx.append("ABOVE_OPENING")
        elif over and o["peitoril"] > .1 and abs(zt - o["_zb"]) < CTOL:
            ctx.append("BELOW_SILL")
        elif over and o["_zb"] - .6 < zb and zt < o["_zt"] + .6:
            ctx.append("INSIDE_OPENING")
        elif d <= 25.0:
            ctx.append("NEAR_JAMB")
    if abs(zb - topz[k]) < .6:
        ctx.append("TOP_OF_WALL")
    lo, hi = wspan[k]
    if abs(s0 - lo) < 2.0 or abs(s1 - hi) < 2.0:
        ctx.append("WALL_END")
    if not ctx:
        ctx = ["OTHER"]
    s = SOLID.get(p["fam"], {})
    cuts.append({
        "element_id": p["id"], "unique_id": p["uid"],
        "family_name": p["fam"], "base_family_INFERIDO": base,
        "cut_mode_CALCULADO": mode,
        "nominal_dim_cm": nom, "cut_dim_cm": cutval,
        "solid_dims_cm_MEDIDO": s.get("solid_dims_cm"),
        "instance_length_cm_MEDIDO": round(p["L"], 3),
        "instance_height_cm_MEDIDO": round(p["H"], 3),
        "bbox_length_cm_MEDIDO": round(s1 - s0, 2),
        "bbox_height_cm_MEDIDO": round(zt - zb, 2),
        "level": p["lvl"], "wall_label": p["parede"], "wall_physical_key": wall_key(p),
        "z_rel_cm": round(zb - DATUM[p["lvl"]], 2),
        "x_cm": round(p["x"], 2), "y_cm": round(p["y"], 2),
        "dist_to_nearest_jamb_cm_MEDIDO": dj,
        "context": sorted(set(ctx)),
    })
wj("06_cut_blocks.json", {"project": PROJECT, "n": len(cuts),
                          "mode_counts": dict(collections.Counter(c["cut_mode_CALCULADO"] for c in cuts)),
                          "context_counts": dict(collections.Counter(x for c in cuts for x in c["context"])),
                          "cut_blocks": cuts})

# ---------------- 07 special blocks ----------------
SPEC = ["COMPENSADOR 14x19x9", "COMPENSADOR 14x19x9 (deitado)", "PASTILHA - 14x19X4",
        "MEIO BLOCO - 14x19x19", "BLOCO 34 - 14x19x34", "BLOCO 54 - 14x19x54",
        "MEIA CANALETA - 14x19x19", "CANALETA J - 14x9-19x19"]
spec = []
for f in SPEC:
    sub = [p for p in P if p["fam"] == f]
    if not sub:
        continue
    s = SOLID.get(f, {})
    zr = collections.Counter(round((p["_z"][0] - DATUM[p["lvl"]] - 1.0) % 20.0, 1) for p in sub)
    top = sum(1 for p in sub if abs(p["_z"][0] - topz[(p["parede"], p["lvl"])]) < .6)
    spec.append({
        "family_name": f, "instances": len(sub),
        "solid_dims_cm_MEDIDO": s.get("solid_dims_cm"),
        "role_INFERIDO": ("compensador vertical de 9 cm" if f == "COMPENSADOR 14x19x9"
                          else "compensador deitado (9 cm de altura, meia fiada)" if "deitado" in f
                          else "pastilha de 4 cm (ajuste fino de comprimento)" if "PASTILHA" in f
                          else "amarracao / ajuste modular"),
        "z_rel_mod20_counts_MEDIDO": dict(sorted(zr.items(), key=lambda x: -x[1])[:6]),
        "in_top_course": top,
        "levels": dict(collections.Counter(p["lvl"] for p in sub)),
    })
n9 = [p for p in P if abs(p["H"] - 9.0) < .1]
wj("07_special_blocks.json", {
    "project": PROJECT, "families": spec,
    "pieces_9cm_tall": {
        "n": len(n9),
        "z_rel_mod20_counts_MEDIDO": dict(sorted(collections.Counter(
            round((p["_z"][0] - DATUM[p["lvl"]] - 1.0) % 20.0, 1) for p in n9).items(),
            key=lambda x: -x[1])),
        "nota": "9 + 1 de junta + 9 = 19: duas pecas de 9 cm reconstroem uma fiada",
    }})

# ---------------- 08 relations ----------------
rel = []
for o in OA:
    wp = [p for p in by_lvl.get(o["lvl"], ())
          if p["_ax"] == o["_ax"] and abs(p["_tc"] - o["_tc"]) <= 3.0]
    s0, s1 = o["_s"]; zt = o["_zt"]; zb = o["_zb"]; d = DATUM[o["lvl"]]
    for p in wp:
        ps0, ps1 = p["_s"]
        over = ps1 > s0 + .6 and ps0 < s1 - .6
        pos = None
        if over and abs(p["_z"][0] - zt) < CTOL:
            pos = "ABOVE_OPENING_FIRST_COURSE"
        elif over and abs(p["_z"][0] - (zt + 20.0)) < CTOL:
            pos = "ABOVE_OPENING_SECOND_COURSE"
        elif over and o["peitoril"] > .1 and abs(p["_z"][1] - zb) < CTOL:
            pos = "BELOW_SILL_FIRST_COURSE"
        elif over and o["peitoril"] > .1 and abs(p["_z"][1] - (zb - 20.0)) < CTOL:
            pos = "BELOW_SILL_SECOND_COURSE"
        elif (not over) and min(abs(ps1 - s0), abs(ps0 - s1)) <= 25.0 \
                and zb - CTOL <= p["_z"][0] < zt:
            pos = "JAMB"
        if pos is None:
            continue
        rel.append({
            "element_id": p["id"], "unique_id": p["uid"],
            "family_name": p["fam"], "type_name": p["typ"],
            "wall_label": p["parede"], "wall_physical_key": wall_key(p),
            "level": p["lvl"],
            "opening_id": o["id"], "opening_unique_id": o["uid"],
            "opening_propagated_from": o.get("_propagated_from"),
            "opening_type": o["titulo"],
            "opening_width_cm": round(o["largura"], 2),
            "opening_height_cm": round(o["altura"], 2),
            "sill_height_cm": round(o["peitoril"], 2),
            "x_cm": round(p["x"], 2), "y_cm": round(p["y"], 2), "z_cm": round(p["z"], 2),
            "z_rel_cm": round(p["_z"][0] - d, 2),
            "rotation_deg": round(p["rot"], 3),
            "piece_length_cm": round(p["L"], 2), "piece_width_cm": round(p["W"], 2),
            "piece_height_cm": round(p["H"], 2),
            "relative_position_to_opening": pos,
            "classification": ("CHANNEL_REINFORCEMENT" if is_canaleta(p["fam"])
                               else "CUT_BLOCK_SYSTEM" if is_cut(p["fam"])
                               else "COMMON_BLOCKS"),
            "confidence": "ALTA" if not o.get("_propagated_from") else "ALTA (clone geometrico)",
        })
wj("08_piece_opening_wall_relations.json", {
    "project": PROJECT, "n": len(rel),
    "position_counts": dict(collections.Counter(r["relative_position_to_opening"] for r in rel)),
    "relations": rel})
print("EMIT 05-08 OK")
