# -*- coding: utf-8 -*-
"""Comparacao HUMANO x SOLVER CHANNEL por abertura - BUTANTA 1o PAV (44 vaos).

Humano: 2026-09-14-channel-human-runs.json (corridas medidas nos blocos reais).
Solver: solve das 34 paredes com opening_reinforcement_strategy="CHANNEL".
Identidade FISICA: abertura casada por element_id do acervo (so' para ligar os
dois lados da MESMA abertura); corridas comparadas em coordenada de MUNDO ao
longo do eixo (o solver estende as pontas das paredes ate' a face dos nos).

Classificacao por papel (acima/abaixo): EXACT_MATCH, PHYSICALLY_EQUIVALENT,
VALID_ALTERNATIVE, SOLVER_BETTER, SOLVER_WORSE, ACTUAL_ERROR, MISSING_CATALOG,
NORMATIVE_DECISION, NOT_COMPARABLE. Evidencia, nao norma.
"""
import json
import os
import sys
from collections import Counter

import channel_bench_common as cb

m = cb.m
MIN_SUPPORT = 19.0
TOL = 1.6

human = json.load(open(os.path.join(cb.EV, "2026-09-14-channel-human-runs.json"), encoding="utf-8"))["records"]
human_by_id = dict((r["id"], r) for r in human)
walls_json = dict((w["id"], w) for w in json.load(open(os.path.join(cb.EV, "2026-09-10-butanta-test-walls.json"),
                                                       encoding="utf-8"))["walls"])

masonry, ops = cb.load_inputs()
ctx = cb.build(masonry, ops)
res = cb.solve(ctx, opening_reinforcement_strategy="CHANNEL")
rein = res["opening_reinforcement"]


def human_t_of_solver_t(wi, t_cm):
    """t no eixo ESTENDIDO do solver -> t no eixo da Wall de teste (humano)."""
    p0, _p1, d, _l, _t = m._wall_axis_and_length(ctx["walls"], wi)
    x = p0.X * cb.F2CM + d.X * t_cm
    y = p0.Y * cb.F2CM + d.Y * t_cm
    w = walls_json[ctx["ids"][wi]]
    hx0, hy0 = w["p0_cm"]
    hx1, hy1 = w["p1_cm"]
    L = ((hx1 - hx0) ** 2 + (hy1 - hy0) ** 2) ** 0.5
    return (x - hx0) * (hx1 - hx0) / L + (y - hy0) * (hy1 - hy0) / L


def solver_run_pieces(run):
    return [(p["code"], round(p["hi_cm"] - p["lo_cm"], 1)) for p in run["pieces"]]


runs_by_id = dict((r["run_id"], r) for r in rein["runs"])
rows = []
for rec in rein["openings"]:
    wi, oi = rec["wall_idx"], rec["opening_index"]
    oid = ctx["opening_ids"][wi][oi]
    h = human_by_id.get(oid)
    for role in ("above", "below"):
        s = rec.get(role)
        hh = (h or {}).get(role)
        if s is None and hh is None:
            continue
        row = {"opening_id": oid, "type": (h or {}).get("type"), "wall": ctx["ids"][wi], "role": role,
               "width_cm": round(rec["t_hi_cm"] - rec["t_lo_cm"], 1), "sill": rec["sill_rel_cm"],
               "head": rec["head_rel_cm"], "solver_status": (s or {}).get("status")}
        h_has = bool(hh and "run" in hh and hh.get("all_over_channel"))
        row["human_status"] = "CHANNEL" if h_has else ("NO_CHANNEL" if hh is not None else "NONE")
        if h_has:
            row["human_z"] = hh["z_lo"]
            row["human_support"] = [hh["support_l"], hh["support_r"]]
            row["human_run"] = hh["run"]
            row["human_codes"] = dict(Counter(c for _a, _b, c in hh["members"]))
        if s and s.get("status") == "CHANNEL":
            run = runs_by_id[s["run_id"]]
            lo = human_t_of_solver_t(wi, run["lo_cm"])
            hi = human_t_of_solver_t(wi, run["hi_cm"])
            lo, hi = min(lo, hi), max(lo, hi)
            row["solver_course"] = s["course_index"]
            row["solver_z"] = 1 + 20 * s["course_index"]
            row["solver_run_human_axis"] = [round(lo, 2), round(hi, 2)]
            row["solver_support"] = [s["support_l_cm"], s["support_r_cm"]]
            row["solver_bearing"] = [s.get("bearing_l_cm", s["support_l_cm"]), s.get("bearing_r_cm", s["support_r_cm"])]
            row["solver_codes"] = dict(Counter(c for c, _l in solver_run_pieces(run)))
        # ---- classificacao
        st = row["solver_status"]
        if row["human_status"] == "CHANNEL" and st == "CHANNEL":
            same_z = abs(row["human_z"] - row["solver_z"]) <= 1.5
            hs, ss = row["human_support"], row["solver_support"]
            bearing = row["solver_bearing"]
            hr, sr = row["human_run"], row["solver_run_human_axis"]
            if not same_z:
                cls = "ACTUAL_ERROR"
            elif abs(hr[0] - sr[0]) <= TOL and abs(hr[1] - sr[1]) <= TOL:
                cls = "EXACT_MATCH"
            elif min(ss) >= MIN_SUPPORT - 0.05 and min(hs) >= MIN_SUPPORT - 0.05:
                cls = "PHYSICALLY_EQUIVALENT"
            elif min(ss) >= min(hs) - 0.05:
                cls = "SOLVER_BETTER" if min(ss) > min(hs) + 0.05 else "PHYSICALLY_EQUIVALENT"
            elif min(ss) > 0 and min(bearing) > 0.5:
                # 19 cm e' PREFERENCIAL (decisao 2026-09-14): apoio menor
                # sobre alvenaria real da fiada de baixo e' alternativa valida.
                cls = "VALID_ALTERNATIVE"
            else:
                cls = "SOLVER_WORSE"
        elif row["human_status"] != "CHANNEL" and st == "FREE_TO_TOP":
            cls = "EXACT_MATCH"
        elif row["human_status"] != "CHANNEL" and st in ("HEAD_OFF_GRID", "SILL_OFF_GRID"):
            cls = "NOT_COMPARABLE"   # K.2: compensador deitado (NEEDS_RULE)
        elif row["human_status"] == "CHANNEL" and st in ("HEAD_OFF_GRID", "SILL_OFF_GRID"):
            cls = "ACTUAL_ERROR"
        elif row["human_status"] == "CHANNEL" and st == "MISSING":
            cls = "ACTUAL_ERROR"
        elif row["human_status"] != "CHANNEL" and st == "CHANNEL":
            cls = "NORMATIVE_DECISION"
        elif row["human_status"] != "CHANNEL" and st == "MISSING":
            cls = "NOT_COMPARABLE"
        else:
            cls = "NOT_COMPARABLE"
        row["classification"] = cls
        rows.append(row)

summary = Counter(r["classification"] for r in rows)
by_role = Counter((r["role"], r["classification"]) for r in rows)
out = {"summary": dict(summary), "by_role": dict(("%s:%s" % k, v) for k, v in by_role.items()),
       "rows": rows, "findings": dict(Counter(f["code"] for f in rein["findings"])),
       "validation": rein["validation"]["counts"]}
# cinta de topo humana (nao gerada pelo CHANNEL): canaletas humanas na ultima fiada
top_ch = 0
top_total = 0
for r in human:
    pass
json.dump(out, open(os.path.join(cb.EV, "2026-09-14-channel-human-vs-solver.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print(json.dumps({"summary": out["summary"], "by_role": out["by_role"]}, indent=1))
if "-v" in sys.argv:
    for r in rows:
        if r["classification"] not in ("EXACT_MATCH", "PHYSICALLY_EQUIVALENT"):
            print(r["opening_id"], r["role"], r["classification"], r.get("human_status"), r["solver_status"],
                  "H", r.get("human_run"), r.get("human_support"), "S", r.get("solver_run_human_axis"),
                  r.get("solver_support"))
