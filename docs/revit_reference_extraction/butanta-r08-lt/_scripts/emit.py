# -*- coding: utf-8 -*-
"""Emite os entregaveis 01..10 na pasta do repositorio (roda em Python 3, local)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_core import *

DEST = ("C:\\Users\\CIVIX\\OneDrive\\\u00c1rea de Trabalho\\Scripts.extension\\MinhaAba.tab"
        "\\MeuPainel.panel\\MeuBotao.pushbutton\\docs\\revit_reference_extraction\\butanta-r08-lt")
PROJECT = {
    "project_id": "butanta-r08-lt",
    "document_name": "BUTANT\u00c3 - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO)",
    "document_path": ("T:\\EM ANDAMENTO\\CIV0495_BUTANTA\\PRANCHAS\\BIM\\REVIT\\"
                      "BUTANT\u00c3 - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO).rvt"),
    "revit_version": "2026 (build 26.3.0.37)",
    "length_unit": "centimeters",
    "extraction_date": "2026-09-09",
    "method": ("pyRevit Routes POST /revit_mcp/execute_code/ (porta 48885) - "
               "SOMENTE LEITURA, nenhuma Transaction aberta"),
}

CTOL = 1.5


def wj(name, obj):
    path = os.path.join(DEST, name)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=False))
    print("  %-42s %8.1f KB" % (name, os.path.getsize(path) / 1024.0))


P, O, OA, by_lvl = build()
g = wall_groups(P)
topz = dict((k, max(p["_z"][0] for p in v)) for k, v in g.items())
wspan = dict((k, (min(p["_s"][0] for p in v), max(p["_s"][1] for p in v))) for k, v in g.items())
SOLID = dict((r["fam"], r) for r in json.load(
    io.open(os.path.join(OUT, "solid_check.json"), encoding="utf-8")))
CATMAP = {"BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34",
          "BLOCO 54 - 14x19x54": "B54", "MEIO BLOCO - 14x19x19": "B19",
          "COMPENSADOR 14x19x9": "C09", "PASTILHA - 14x19X4": "C04"}


def wall_key(e):
    return "%s|%s|ax=%s|perp=%.0f" % (e["parede"], e["lvl"], e["_ax"], round(e["_tc"]))


# ---------------- 01 family catalog ----------------
cnt = collections.Counter((p["fam"], p["typ"]) for p in P)
cat = []
for (f, t), n in sorted(cnt.items(), key=lambda x: -x[1]):
    s = SOLID.get(f, {})
    sub = [p for p in P if p["fam"] == f and p["typ"] == t]
    code = CATMAP.get(f) if t == f else None
    cat.append({
        "family_name": f, "type_name": t, "category": "Modelos gen\u00e9ricos",
        "instances": n,
        "solid_dims_cm_MEDIDO": s.get("solid_dims_cm"),
        "solid_volume_cm3_MEDIDO": s.get("solid_vol_cm3"),
        "bbox_dims_cm_MEDIDO": s.get("bbox_dims_cm"),
        "param_L_H_W_cm_MEDIDO": s.get("param_LHW_cm"),
        "instance_L_values_cm_MEDIDO": sorted(set(round(p["L"], 2) for p in sub))[:8],
        "instance_H_values_cm_MEDIDO": sorted(set(round(p["H"], 2) for p in sub))[:8],
        "solver_code": code,
        "solver_status": ("SUPPORTED" if code else
                          "PARTIALLY_SUPPORTED" if f in CATMAP else "NOT_SUPPORTED"),
        "is_canaleta": is_canaleta(f), "is_cut": is_cut(f),
        "levels": dict(collections.Counter(p["lvl"] for p in sub)),
        "rotations_deg": sorted(set(round(p["rot"]) % 360 for p in sub)),
    })
wj("01_family_catalog.json", {"project": PROJECT, "n_family_types": len(cat),
                              "n_pieces": len(P), "families": cat})

# ---------------- 02 openings ----------------
ops = []
for o in O:
    ops.append({
        "element_id": o["id"], "unique_id": o["uid"],
        "family_name": o["fam"], "type_name": o["typ"], "category": "Mobili\u00e1rio",
        "declared_type_MEDIDO": o["titulo"],
        "wall_label": o["parede"], "wall_physical_key": wall_key(o),
        "level": o["lvl"], "level_datum_z_cm": DATUM[o["lvl"]],
        "opening_width_cm": round(o["largura"], 2),
        "opening_height_cm": round(o["altura"], 2),
        "sill_height_cm": round(o["peitoril"], 2),
        "opening_base_z_rel_cm": round(o["_zb"] - DATUM[o["lvl"]], 2),
        "opening_top_z_rel_cm": round(o["_zt"] - DATUM[o["lvl"]], 2),
        "axis": o["_ax"], "rotation_deg": round(o["rot"], 3),
        "span_along_axis_cm": [round(o["_s"][0], 2), round(o["_s"][1], 2)],
        "x_cm": round(o["x"], 2), "y_cm": round(o["y"], 2),
        "classification_CALCULADO": ("PORTA (peitoril=0)" if o["peitoril"] < .1
                                     else "JANELA/ABERTURA (peitoril>0)"),
        "label_matches_geometry": (o["titulo"] == "PORTA") == (o["peitoril"] < .1),
    })
wj("02_openings.json", {
    "project": PROJECT, "n": len(ops),
    "note": ("Aberturas instanciadas em 4 niveis; 3o-8o PAV sao clones geometricos "
             "exatos do 2o (0 diferencas em 6727 pecas) - ver README."),
    "openings": ops})

# ---------------- 03 above / 04 below ----------------
above, below = [], []
for o in OA:
    wp = [p for p in by_lvl.get(o["lvl"], ())
          if p["_ax"] == o["_ax"] and abs(p["_tc"] - o["_tc"]) <= 3.0]
    if not wp:
        continue
    s0, s1 = o["_s"]; zt = o["_zt"]; zb = o["_zb"]; d = DATUM[o["lvl"]]
    wlo = min(p["_s"][0] for p in wp); whi = max(p["_s"][1] for p in wp)

    def ov(p):
        return p["_s"][1] > s0 + .6 and p["_s"][0] < s1 - .6

    ab = [p for p in wp if ov(p) and abs(p["_z"][0] - zt) < CTOL]
    ab2 = [p for p in wp if ov(p) and abs(p["_z"][0] - (zt + 20.0)) < CTOL]
    cs = [p for p in wp if abs(p["_z"][0] - zt) < CTOL and is_canaleta(p["fam"])]
    rr = [x for x in runs(cs) if x[1] > s0 + .6 and x[0] < s1 - .6]
    rec = {
        "opening_id": o["id"], "opening_unique_id": o["uid"],
        "propagated_from_opening_id": o.get("_propagated_from"),
        "opening_type": o["titulo"], "level": o["lvl"],
        "wall_label": o["parede"], "wall_physical_key": wall_key(o),
        "opening_width_cm": round(o["largura"], 2),
        "opening_top_z_cm_MEDIDO": round(zt - d, 2),
        "reinforcement_base_z_cm_MEDIDO": (round(min(p["_z"][0] for p in ab) - d, 2) if ab else None),
        "vertical_offset_cm_CALCULADO": (round(min(p["_z"][0] for p in ab) - zt, 2) if ab else None),
        "n_pieces_over_span": len(ab),
        "families_over_span": dict(collections.Counter(p["fam"] for p in ab)),
        "all_canaleta_over_span": bool(ab) and all(is_canaleta(p["fam"]) for p in ab),
        "second_course_above_families": dict(collections.Counter(p["fam"] for p in ab2)),
        "second_course_above_is_canaleta": bool(ab2) and all(is_canaleta(p["fam"]) for p in ab2),
        "classification": ("CHANNEL_REINFORCEMENT" if ab and all(is_canaleta(p["fam"]) for p in ab)
                           else "COMMON_BLOCKS" if ab else "UNKNOWN (nenhuma peca sobre o vao)"),
        "wall_top_z_cm": (round(topz[(o["parede"], o["lvl"])] - d, 2)
                          if (o["parede"], o["lvl"]) in topz else None),
    }
    if rr:
        lo = min(x[0] for x in rr); hi = max(x[1] for x in rr)
        sel = [p for x in rr for p in x[2]]
        rec.update({
            "channel_run_cm": [round(lo, 2), round(hi, 2)],
            "total_reinforcement_length_cm_MEDIDO": round(hi - lo, 2),
            "left_bearing_cm_bbox_MEDIDO": round(s0 - lo, 2),
            "right_bearing_cm_bbox_MEDIDO": round(hi - s1, 2),
            "left_bearing_cm_solid_CALCULADO": round(s0 - lo - 1.0, 2),
            "right_bearing_cm_solid_CALCULADO": round(hi - s1 - 1.0, 2),
            "n_channel_pieces_in_run": len(sel),
            "run_reaches_wall_start": abs(lo - wlo) < 2.0,
            "run_reaches_wall_end": abs(hi - whi) < 2.0,
            "symmetric_bearing": abs((s0 - lo) - (hi - s1)) < 1.0,
        })
    above.append(rec)

    if o["peitoril"] > .1:
        be = [p for p in wp if ov(p) and abs(p["_z"][1] - zb) < CTOL]
        be2 = [p for p in wp if ov(p) and abs(p["_z"][1] - (zb - 20.0)) < CTOL]
        cb = [p for p in wp if abs(p["_z"][1] - zb) < CTOL and is_canaleta(p["fam"])]
        rb = [x for x in runs(cb) if x[1] > s0 + .6 and x[0] < s1 - .6]
        r2 = {
            "opening_id": o["id"], "opening_unique_id": o["uid"],
            "propagated_from_opening_id": o.get("_propagated_from"),
            "opening_type": o["titulo"], "level": o["lvl"],
            "wall_label": o["parede"], "wall_physical_key": wall_key(o),
            "opening_width_cm": round(o["largura"], 2),
            "sill_z_cm_MEDIDO": round(zb - d, 2),
            "reinforcement_top_z_cm_MEDIDO": (round(max(p["_z"][1] for p in be) - d, 2) if be else None),
            "vertical_offset_cm_CALCULADO": (round(zb - max(p["_z"][1] for p in be), 2) if be else None),
            "n_pieces_under_span": len(be),
            "families_under_span": dict(collections.Counter(p["fam"] for p in be)),
            "all_canaleta_under_span": bool(be) and all(is_canaleta(p["fam"]) for p in be),
            "second_course_below_families": dict(collections.Counter(p["fam"] for p in be2)),
            "second_course_below_is_canaleta": bool(be2) and all(is_canaleta(p["fam"]) for p in be2),
            "classification": ("CHANNEL_REINFORCEMENT" if be and all(is_canaleta(p["fam"]) for p in be)
                               else "COMMON_BLOCKS" if be else "UNKNOWN"),
        }
        if rb:
            lo = min(x[0] for x in rb); hi = max(x[1] for x in rb)
            r2.update({
                "channel_run_cm": [round(lo, 2), round(hi, 2)],
                "total_reinforcement_length_cm_MEDIDO": round(hi - lo, 2),
                "left_bearing_cm_bbox_MEDIDO": round(s0 - lo, 2),
                "right_bearing_cm_bbox_MEDIDO": round(hi - s1, 2),
                "left_bearing_cm_solid_CALCULADO": round(s0 - lo - 1.0, 2),
                "right_bearing_cm_solid_CALCULADO": round(hi - s1 - 1.0, 2),
                "n_channel_pieces_in_run": len([p for x in rb for p in x[2]]),
                "run_reaches_wall_start": abs(lo - wlo) < 2.0,
                "run_reaches_wall_end": abs(hi - whi) < 2.0,
            })
        below.append(r2)

wj("03_above_openings.json", {
    "project": PROJECT, "n": len(above),
    "note": ("Inclui clones INFERIDOS dos pav. 3o-8o "
             "(propagated_from_opening_id != null). Registros unicos: 142."),
    "records": above})
wj("04_below_windows.json", {
    "project": PROJECT, "n": len(below),
    "note": "Somente aberturas com peitoril > 0 (89 unicas).",
    "records": below})
print("EMIT 01-04 OK")
