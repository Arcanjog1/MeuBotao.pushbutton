# -*- coding: utf-8 -*-
"""CHANNEL (BUTANTA humano, 1o PAV): corridas de canaleta por abertura.

Medicao somente leitura sobre JSON ja versionados (blocos humanos do 1o PAV,
eixos das 46 Walls de teste, 02_openings). Evidencia, nao norma.
Uso: py -3 docs/checkpoints/evidence/_scripts/2026-09-14-channel-human-runs.py
"""
import json
import math
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
EV = os.path.join(ROOT, "docs", "checkpoints", "evidence")
walls = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json"), encoding="utf-8"))["walls"]
blocks = json.load(open(os.path.join(EV, "2026-09-10-butanta-ref-1pav-blocks.json"), encoding="utf-8"))["blocks"]
ops = json.load(open(os.path.join(ROOT, "docs", "revit_reference_extraction", "butanta-r08-lt", "02_openings.json"),
                     encoding="utf-8"))["openings"]
ops = [o for o in ops if o["level_datum_z_cm"] == 0.0]

CODE = {"BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34", "MEIO BLOCO - 14x19x19": "B19",
        "BLOCO 54 - 14x19x54": "B54", "COMPENSADOR 14x19x9": "C09", "PASTILHA - 14x19X4": "C04",
        "CANALETA INTEIRA - 14x19x39": "K39", "CANALETA 34 - 14x19x34": "K34", "MEIA CANALETA - 14x19x19": "K19",
        "CANALETA J - 14x9-19x19": "KJ", "BLOCO CANALETA CORTADO - 14x19xVAR": "KV",
        "CANALETA J CORTADA - 14x9-19xVAR": "KJV", "COMPENSADOR 14x19x9 (deitado)": "C09D",
        "COMPENSADOR CORTADO 14x19x9 (deitado)": "C09DV"}


def code(sym):
    return CODE.get(sym, "?" + sym[:14])


def is_k(c):
    return c.startswith("K")


axes = []
for w in walls:
    x0, y0 = w["p0_cm"]
    x1, y1 = w["p1_cm"]
    L = math.hypot(x1 - x0, y1 - y0)
    axes.append(dict(id=w["id"], p0=(x0, y0), d=((x1 - x0) / L, (y1 - y0) / L), len=L, horiz=abs(y1 - y0) < 1e-6))

# pecas por parede: (t0, t1, z_lo, z_hi, code, along, id); t em cm do solido
per_wall = defaultdict(list)
for b in blocks:
    bb = b["bb"]
    cx, cy = b["x"], b["y"]
    along_h = abs(math.sin(b["rot"])) < 0.5
    for a in axes:
        x0, y0 = a["p0"]
        dx, dy = a["d"]
        lat = abs((cx - x0) * dy - (cy - y0) * dx)
        if lat > 7.5:
            continue
        t = (cx - x0) * dx + (cy - y0) * dy
        if t < -60 or t > a["len"] + 60:
            continue
        if a["horiz"]:
            t0, t1 = sorted(((bb[0] - x0) * dx, (bb[3] - x0) * dx))
        else:
            t0, t1 = sorted(((bb[1] - y0) * dy, (bb[4] - y0) * dy))
        along = (along_h == a["horiz"])
        if along:  # bbox tem +1 cm por ponta no comprimento (erratas do acervo)
            t0, t1 = t0 + 1.0, t1 - 1.0
        per_wall[a["id"]].append((round(t0, 2), round(t1, 2), round(bb[2], 2), round(bb[5], 2),
                                  code(b["sym"]), along, b["id"]))


def assign(o):
    best = None
    for a in axes:
        if (o["axis"] == "X") != a["horiz"]:
            continue
        x0, y0 = a["p0"]
        dx, dy = a["d"]
        lat = abs((o["x_cm"] - x0) * dy - (o["y_cm"] - y0) * dx)
        s0, s1 = o["span_along_axis_cm"]
        if a["horiz"]:
            ts = sorted(((s0 - x0) * dx, (s1 - x0) * dx))
        else:
            ts = sorted(((s0 - y0) * dy, (s1 - y0) * dy))
        if lat <= 8.0 and ts[0] >= -1 and ts[1] <= a["len"] + 1 and (best is None or lat < best[0]):
            best = (lat, a, ts)
    return best


def course_pieces(wid, zlo, tol=1.5):
    return sorted([p for p in per_wall[wid] if abs(p[2] - zlo) <= tol], key=lambda p: (p[0], p[1]))


def run_over(pieces, t_lo, t_hi):
    """Maior componente contigua de canaletas (along) que intersecta [t_lo, t_hi]."""
    al = [p for p in pieces if p[5]]
    ks = [p for p in al if is_k(p[4])]
    hits = [p for p in ks if p[1] > t_lo + 0.5 and p[0] < t_hi - 0.5]
    if not hits:
        return None
    lo = min(p[0] for p in hits)
    hi = max(p[1] for p in hits)
    changed = True
    while changed:
        changed = False
        for p in ks:
            if p[1] >= lo - 1.6 and p[0] < lo - 0.01:
                lo = p[0]
                changed = True
            if p[0] <= hi + 1.6 and p[1] > hi + 0.01:
                hi = p[1]
                changed = True
    members = [p for p in ks if p[0] >= lo - 0.01 and p[1] <= hi + 0.01]
    over = [p for p in al if p[1] > t_lo + 0.5 and p[0] < t_hi - 0.5]
    return dict(lo=lo, hi=hi, members=[(p[0], p[1], p[4]) for p in members],
                over=[(p[0], p[1], p[4]) for p in over])


records = []
for o in ops:
    m = assign(o)
    if m is None:
        records.append(dict(id=o["element_id"], err="unassigned"))
        continue
    _lat, a, (tl, th) = m
    head = o["opening_top_z_rel_cm"]
    sill = o["opening_base_z_rel_cm"]
    rec = dict(id=o["element_id"], type=o["declared_type_MEDIDO"], wall=a["id"], wall_len=round(a["len"], 1),
               t=[round(tl, 2), round(th, 2)], width=round(th - tl, 2), sill=sill, head=head)
    wz = sorted({round(p[2], 1) for p in per_wall[a["id"]]})
    rec["wall_top_course_z"] = max(wz) if wz else None
    for role, zlo in (("above", head), ("below", sill - 19.0)):
        if role == "below" and sill <= 0.5:
            continue
        pcs = course_pieces(a["id"], zlo)
        r = run_over(pcs, tl, th)
        info = dict(z_lo=zlo, n_pieces_course=len(pcs))
        if r:
            al = [p for p in pcs if p[5]]
            left = [p for p in al if p[1] <= r["lo"] + 0.01]
            right = [p for p in al if p[0] >= r["hi"] - 0.01]
            info.update(run=[round(r["lo"], 2), round(r["hi"], 2)], support_l=round(tl - r["lo"], 2),
                        support_r=round(r["hi"] - th, 2), members=r["members"], over=r["over"],
                        all_over_channel=all(is_k(c) for _, _, c in r["over"]),
                        left_neighbor=(left[-1][0], left[-1][1], left[-1][4]) if left else None,
                        right_neighbor=(right[0][0], right[0][1], right[0][4]) if right else None,
                        course_channel_frac=round(sum(p[1] - p[0] for p in al if is_k(p[4])) /
                                                  max(1e-6, sum(p[1] - p[0] for p in al)), 3))
        else:
            info["over"] = [(p[0], p[1], p[4]) for p in pcs if p[5] and p[1] > tl + 0.5 and p[0] < th - 0.5]
        rec[role] = info
    records.append(rec)

out = os.path.join(EV, "2026-09-14-channel-human-runs.json")
json.dump(dict(source="ref-1pav-blocks + test-walls + 02_openings (1o PAV)", records=records),
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    for r in records:
        if "err" in r:
            print(r)
            continue
        print("%s %-8s w%s L=%s t=[%s,%s] w=%s sill=%s head=%s top=%s" % (
            r["id"], r["type"], r["wall"], r["wall_len"], r["t"][0], r["t"][1], r["width"], r["sill"], r["head"],
            r["wall_top_course_z"]))
        for role in ("above", "below"):
            i = r.get(role)
            if not i:
                continue
            if "run" in i:
                print("   %s z=%s run=%s supL=%s supR=%s n=%d frac=%s | L:%s R:%s | over=%s" % (
                    role, i["z_lo"], i["run"], i["support_l"], i["support_r"], len(i["members"]),
                    i["course_channel_frac"], i["left_neighbor"], i["right_neighbor"],
                    " ".join("%s[%g,%g]" % (c, a0, a1) for a0, a1, c in i["over"])))
            else:
                print("   %s z=%s NO RUN over=%s" % (role, i["z_lo"], i["over"]))
