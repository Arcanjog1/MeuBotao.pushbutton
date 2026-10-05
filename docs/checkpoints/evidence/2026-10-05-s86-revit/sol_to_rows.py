# -*- coding: utf-8 -*-
"""sol_*.json (export_solution) -> formato da leitura de volta (rows com celulas por peca), para as
mesmas reguas/figuras antes de criar no Revit. Uso: py -3 sol_to_rows.py SOL.json OUT.json"""
import json, sys, math
sol = json.load(open(sys.argv[1]))
FT = 30.48
walls = sol.get("walls_cm_orig") or sol["walls_cm"]  # 86.9: eixo de entrada
rows = {}
for ci, cands in sol["course_candidates"].items():
    for c in cands:
        wi = c.get("wall_idx")
        if not isinstance(wi, int):
            continue
        (x0, y0), (x1, y1), th = walls[wi]
        L = math.hypot(x1 - x0, y1 - y0)
        dx, dy = (x1 - x0) / L, (y1 - y0) / L
        o = c["origin_world"]["__xyz__"]
        ox, oy = o[0] * FT, o[1] * FT
        xd = c["x_dir"]["__xyz__"]
        yd = c["y_dir"]["__xyz__"]
        hl, hw = c["length_cm"] / 2.0, c["width_cm"] / 2.0
        half = abs(hl * (xd[0] * dx + xd[1] * dy)) + abs(hw * (yd[0] * dx + yd[1] * dy))
        t = (ox - x0) * dx + (oy - y0) * dy
        along = abs(xd[0] * dx + xd[1] * dy) >= 0.5
        cells = []
        for cell in c.get("cells_world") or []:
            pt = cell["point"]["__xyz__"]
            tc = (pt[0] * FT - x0) * dx + (pt[1] * FT - y0) * dy
            sx = float(cell["size_local"][0]) * FT
            sy = float(cell["size_local"][1]) * FT
            a = sx if along else sy
            cells.append([round(tc - a / 2, 2), round(tc + a / 2, 2)])
        rows.setdefault("%d:%s" % (wi, ci), []).append([round(t - half, 2), round(t + half, 2), c["logical_code"], sorted(cells), None])
for k in rows:
    rows[k].sort()
out = {"rows": rows, "openings": [[[o[0], o[1], o[2], o[3]] for o in row] for row in (sol.get("openings_per_wall_cm_orig") or sol["openings_per_wall_cm"])]}
json.dump(out, open(sys.argv[2], "w"))
print("ok", len(rows))
