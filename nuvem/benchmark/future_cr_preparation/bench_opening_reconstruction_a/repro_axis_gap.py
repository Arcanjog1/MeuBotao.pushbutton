# -*- coding: utf-8 -*-
"""FASE 2, item 5: o consenso e' um VAO na parede ou o ESPACO entre DUAS
paredes MEDIDAS? Re-derivado do zero a partir de input.json (TGD tem
`confidence=measured` / `source_element_ids`), sem depender da branch
diagnostica.
"""
import json
import math
import os
import sys

ROOT = os.environ.get("REPO_ROOT", os.path.abspath("."))
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = sys.argv[1] if len(sys.argv) > 1 else "torre_easy_lo_r00_tgd"

ref = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", PROJ,
                                  "reference.json"), encoding="utf-8"))
inp = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", PROJ,
                                  "input.json"), encoding="utf-8"))
repro = json.load(open(os.path.join(HERE, "repro_envelope.json"), encoding="utf-8"))[PROJ]

ref_walls = {w["id"]: w for w in ref["walls"]}


def axis(wall):
    sx, sy = wall["start_cm"]
    ex, ey = wall["end_cm"]
    length = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / length, (ey - sy) / length)


def project(origin, direction, point):
    dx, dy = point[0] - origin[0], point[1] - origin[1]
    t = dx * direction[0] + dy * direction[1]
    s = -dx * direction[1] + dy * direction[0]
    return t, s


sig = [r for r in repro["runs"]
       if r["spread_inicio"] >= 14.9 and r["spread_fim"] >= 14.9]
hit = miss = nodata = 0
lines = []
for rec in sig:
    host = ref_walls[rec["wall"]]
    origin, direction = axis(host)
    runs = []
    for w in inp["walls"]:
        t0, s0 = project(origin, direction, w["start_cm"])
        t1, s1 = project(origin, direction, w["end_cm"])
        if abs(s0) > 2.0 or abs(s1) > 2.0:      # nao esta' no MESMO eixo
            continue
        runs.append({"w": w["id"], "lo": min(t0, t1), "hi": max(t0, t1)})
    runs.sort(key=lambda r: r["lo"])
    gaps = [(a["hi"], b["lo"], a["w"], b["w"])
            for a, b in zip(runs, runs[1:]) if b["lo"] - a["hi"] > 1.0]
    cons = rec["consenso"]
    env = rec["envelope"]
    if not runs:
        nodata += 1
        lines.append("  %-6s env=%-16s cons=%-16s SEM GEOMETRIA MEDIDA no eixo"
                     % (rec["wall"], env, cons))
        continue
    match = next((g for g in gaps
                  if abs(g[0] - cons[0]) <= 2.0 and abs(g[1] - cons[1]) <= 2.0), None)
    if match:
        hit += 1
        lines.append("  %-6s env=%-16s cons=%-16s == BURACO MEDIDO [%.1f,%.1f] entre %s e %s"
                     % (rec["wall"], env, cons, match[0], match[1], match[2], match[3]))
    else:
        miss += 1
        lines.append("  %-6s env=%-16s cons=%-16s buracos medidos: %s"
                     % (rec["wall"], env, cons,
                        [(round(g[0], 1), round(g[1], 1)) for g in gaps] or "nenhum"))
print(PROJ)
print("\n".join(lines))
print(">> consenso == buraco entre paredes MEDIDAS: %d | divergente: %d | sem geometria medida: %d"
      % (hit, miss, nodata))
