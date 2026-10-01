# -*- coding: utf-8 -*-
"""Pecas do projeto HUMANO (1o PAV, ref_1pav.json) -> formato do readback (parede = indice do corpus s74 = indice do
handler do butanta testes, t ao longo do eixo, fiada, celulas reais pelo catalogo das familias)."""
import json, math, sys
G = json.load(open(sys.argv[1], encoding="utf-8"))           # geometry.json do corpus
H = json.load(open(sys.argv[2], encoding="utf-8"))           # ref_1pav.json
OUT = sys.argv[3]
FT = 30.48
CODE = [("BLOCO INTEIRO CORTADO", "B39_H9"), ("BLOCO 34 CORTADO", "B34_H9"), ("MEIO BLOCO CORTADO", "B19_H9"),
        ("BLOCO 54 CORTADO", "B54_H9"), ("BLOCO CANALETA CORTADO", "CHANNEL_U_CUT"), ("CANALETA J CORTADA", "CHANNEL_J_CUT"),
        ("COMPENSADOR CORTADO", "C09_CUT"), ("COMPENSADOR 14x19x9 (deitado)", "C09_DEITADO"),
        ("BLOCO INTEIRO", "B39"), ("BLOCO 34", "B34"), ("MEIO BLOCO", "B19"), ("BLOCO 54", "B54"), ("PASTILHA", "C04"),
        ("COMPENSADOR", "C09"), ("CANALETA INTEIRA", "CHANNEL_U_39"), ("CANALETA 34", "CHANNEL_U_34"),
        ("MEIA CANALETA", "CHANNEL_U_19"), ("CANALETA J", "CHANNEL_J")]
def code_of(fam):
    for k, c in CODE:
        if fam.upper().startswith(k.upper()):
            return c
    return "OUTRO:" + fam
cat = G["catalog"]
cells_local = {}
for c, e in cat.items():
    cells_local[c] = [(cl["center_local"][0] * FT, cl["center_local"][1] * FT, cl["size_local"][0] * FT) for cl in e.get("cells_local") or []]
axes = []
for w in G["walls"]:
    (x0, y0), (x1, y1) = w["p0_cm"], w["p1_cm"]
    L = math.hypot(x1 - x0, y1 - y0)
    axes.append((x0, y0, (x1 - x0) / L, (y1 - y0) / L, L, w["thickness_cm"]))
rows, unassigned, codes = {}, [], {}
for p in H["pieces"]:
    code = code_of(p["fam"])
    codes[code] = codes.get(code, 0) + 1
    bb = p["bb"]
    cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
    zb = bb[2]
    bx = p["bx"]
    best = None
    for wi, (x0, y0, dx, dy, L, th) in enumerate(axes):
        if abs(bx[0] * dx + bx[1] * dy) < 0.9:
            continue
        t = (cx - x0) * dx + (cy - y0) * dy
        lat = abs((cx - x0) * dy - (cy - y0) * dx)
        if lat <= th / 2.0 + 1.0 and -30.0 <= t <= L + 30.0 and (best is None or lat < best[0]):
            best = (lat, wi, t)
    if best is None:
        unassigned.append((p["id"], code, round(cx), round(cy)))
        continue
    _lat, wi, t = best
    x0, y0, dx, dy, L, th = axes[wi]
    # extensao ao longo do eixo pela caixa (pecas paralelas a parede)
    ext = abs((bb[3] - bb[0]) * dx) + abs((bb[4] - bb[1]) * dy)
    lo, hi = t - ext / 2.0, t + ext / 2.0
    course = int(round((zb - 1.0) / 20.0))
    cells = []
    base = code.split("_H9")[0]
    if base in cells_local and p["o"]:
        ox, oy = p["o"][0], p["o"][1]
        by = p["by"]
        for (lx, ly, sx) in cells_local[base]:
            wx = ox + bx[0] * lx + by[0] * ly
            wy = oy + bx[1] * lx + by[1] * ly
            tc = (wx - x0) * dx + (wy - y0) * dy
            cells.append([round(tc - sx / 2.0, 2), round(tc + sx / 2.0, 2)])
    rows.setdefault("%d:%d" % (wi, course), []).append([round(lo, 2), round(hi, 2), code, sorted(cells), p["id"]])
for k in rows:
    rows[k].sort()
ops = []
for wi, (x0, y0, dx, dy, L, th) in enumerate(axes):
    lst = []
    for o in H["openings"]:
        bb = o["bb"]
        cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
        lat = abs((cx - x0) * dy - (cy - y0) * dx)
        t = (cx - x0) * dx + (cy - y0) * dy
        if lat <= th / 2.0 + 2.0 and 0 <= t <= L:
            w = o["w"] or 0.0
            lst.append([round(t - w / 2.0, 2), round(t + w / 2.0, 2), o["sill"] or 0.0, (o["sill"] or 0.0) + (o["h"] or 0.0)])
    ops.append(sorted(lst))
json.dump({"rows": rows, "openings": ops, "codes": codes, "unassigned": unassigned}, open(OUT, "w"))
print("pecas", len(H["pieces"]), "atribuidas", sum(len(v) for v in rows.values()), "sem parede", len(unassigned))
print("codigos", codes)
print("sem parede (amostra)", unassigned[:12])
