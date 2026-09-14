# -*- coding: utf-8 -*-
"""HUMANO (1o PAV) x SOLVER CHANNEL executado NO REVIT (bancada, 2o PAV).

Usa o resultado do harness (aberturas detectadas pelo plugin, suportes e fiada
por abertura) e as corridas humanas medidas. Casamento FISICO: mesma parede
(eixo) e sobreposicao do vao em coordenada de mundo. Z comparado relativo ao
nivel. Classificacao igual a 2026-09-14-channel-human-vs-solver.py (sem
extensao exata da corrida: EXACT = mesmos apoios +-1,6 cm).
Uso: py -3 2026-09-14-channel-human-vs-revit.py <r_ladder_34.json> <saida.json>
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, "..")
MIN_SUPPORT = 19.0
TOL = 1.6
F2CM = 30.48

d = json.load(open(sys.argv[1], encoding="utf-8"))
human = json.load(open(os.path.join(EV, "2026-09-14-channel-human-runs.json"), encoding="utf-8"))["records"]
walls_json = dict((w["id"], w) for w in json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json"),
                                                       encoding="utf-8"))["walls"])


def to_human_t(wi, t_cm):
    x0, y0, x1, y1 = [v * F2CM for v in d["walls_ft"][wi]]
    L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    x = x0 + (x1 - x0) / L * t_cm
    y = y0 + (y1 - y0) / L * t_cm
    w = walls_json[d["cfg"]["ids"][wi]]
    hx0, hy0 = w["p0_cm"]
    hx1, hy1 = w["p1_cm"]
    H = ((hx1 - hx0) ** 2 + (hy1 - hy0) ** 2) ** 0.5
    return (x - hx0) * (hx1 - hx0) / H + (y - hy0) * (hy1 - hy0) / H


rows = []
unmatched = []
for rec in d["solve"]["openings"]:
    wi = rec["wall_idx"]
    wid = d["cfg"]["ids"][wi]
    a, b = sorted((to_human_t(wi, rec["t_lo_cm"]), to_human_t(wi, rec["t_hi_cm"])))
    cands = [h for h in human if h.get("wall") == wid and min(b, h["t"][1]) - max(a, h["t"][0]) > 0.5 * (b - a)]
    if len(cands) != 1:
        unmatched.append((wid, round(a, 1), round(b, 1), len(cands)))
        continue
    h = cands[0]
    flipped = to_human_t(wi, rec["t_lo_cm"]) > to_human_t(wi, rec["t_hi_cm"])
    for role in ("above", "below"):
        s = rec.get(role)
        hh = h.get(role)
        if s is None and hh is None:
            continue
        h_has = bool(hh and "run" in hh and hh.get("all_over_channel"))
        row = {"opening_id": h["id"], "wall": wid, "role": role, "solver_status": (s or {}).get("status"),
               "human_status": "CHANNEL" if h_has else "NO_CHANNEL"}
        st = row["solver_status"]
        if h_has and st == "CHANNEL":
            ss = [s["support_l_cm"], s["support_r_cm"]]
            if flipped:
                ss = ss[::-1]
            hs = [hh["support_l"], hh["support_r"]]
            same_z = abs(hh["z_lo"] - (1 + 20 * s["course_index"])) <= 1.5
            row.update(human_support=hs, solver_support=ss, human_z=hh["z_lo"], solver_course=s["course_index"])
            if not same_z:
                cls = "ACTUAL_ERROR"
            elif abs(hs[0] - ss[0]) <= TOL and abs(hs[1] - ss[1]) <= TOL:
                cls = "EXACT_MATCH"
            elif min(ss) >= MIN_SUPPORT - 0.05 and min(hs) >= MIN_SUPPORT - 0.05:
                cls = "PHYSICALLY_EQUIVALENT"
            elif min(ss) >= min(hs) - 0.05:
                cls = "SOLVER_BETTER" if min(ss) > min(hs) + 0.05 else "PHYSICALLY_EQUIVALENT"
            elif min(ss) > 0 and min(hs) < MIN_SUPPORT - 0.05:
                cls = "VALID_ALTERNATIVE"
            else:
                cls = "SOLVER_WORSE"
        elif not h_has and st == "FREE_TO_TOP":
            cls = "EXACT_MATCH"
        elif not h_has and st in ("HEAD_OFF_GRID", "SILL_OFF_GRID"):
            cls = "NOT_COMPARABLE"
        elif h_has and st in ("MISSING", "HEAD_OFF_GRID", "SILL_OFF_GRID", "FREE_TO_TOP", None):
            cls = "ACTUAL_ERROR"
        elif not h_has and st == "CHANNEL":
            cls = "NORMATIVE_DECISION"
        else:
            cls = "NOT_COMPARABLE"
        row["classification"] = cls
        rows.append(row)

out = {"source": os.path.basename(sys.argv[1]), "summary": dict(Counter(r["classification"] for r in rows)),
       "by_role": dict(("%s:%s" % k, v) for k, v in Counter((r["role"], r["classification"]) for r in rows).items()),
       "openings_matched": len(set(r["opening_id"] for r in rows)), "unmatched": unmatched, "rows": rows}
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(json.dumps(dict((k, out[k]) for k in ("summary", "by_role", "openings_matched", "unmatched")), indent=1))
for r in rows:
    if r["classification"] not in ("EXACT_MATCH", "PHYSICALLY_EQUIVALENT"):
        print(r)
