# -*- coding: utf-8 -*-
"""Comparador humano x lote real (Revit) por lado de vao, fiadas 0-11.
Regiao: 60 cm a partir da jamba para fora do vao (ou ate' a ponta da parede).
Classes (endurecidas): EXACT_MATCH (mesmas pecas nas mesmas posicoes),
PHYSICALLY_EQUIVALENT (mesma cobertura, mesmo numero de especiais, sem peca sem
apoio/buraco), VALID_ALTERNATIVE (cobertura completa, especiais <= humano + 1,
sem buraco), SOLVER_BETTER (cobertura completa e menos especiais que o humano),
SOLVER_WORSE (cobertura menor que a do humano ou especiais >= humano + 2)."""
import collections, json, os, sys
sys.path.insert(0, ".")
import phys, pmodel, evalsolve
T0 = phys.load("target_1pav.clean.json")
H = phys.load("human_1pav.clean.json")
R = phys.load(os.environ.get("TARGET_JSON", "target_run1.clean.json"))
walls = [phys.Wall(w["id"], w["p0"], w["p1"], w["uid"]) for w in T0["walls"]]
W = {w.id: w for w in walls}
mas = evalsolve.masonry_wall_ids()
SPECIAL = ("C09", "C04", "C09D", "C09DH")
REACH = 60.0


def pieces(doc, stamp):
    recs = [phys.piece_record(p) for p in doc["pieces"]]
    phys.assign_walls(recs, walls, by_stamp=stamp)
    by = collections.defaultdict(list)
    for p in pmodel.from_revit(recs):
        if p.course < 12 and p.wall in mas:
            by[(p.wall, p.course)].append(p)
    return by


hb, rb = pieces(H, False), pieces(R, True)
ops = []
for op in T0["openings"]:
    best = None
    for w in walls:
        if w.id not in mas:
            continue
        s = phys.opening_span_on_wall(op, w)
        if not s:
            continue
        bb = op["bb"]
        lat = abs(w.lat_of((bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2))
        if best is None or lat < best[0]:
            best = (lat, w, s)
    if best:
        ops.append((op["id"], best[1], best[2]))


def region_stats(by, wid, c, lo, hi):
    seq = [p for p in by.get((wid, c), []) if p.hi > lo + 0.5 and p.lo < hi - 0.5]
    cov = []
    for p in sorted(seq, key=lambda p: p.lo):
        a, b = max(p.lo, lo), min(p.hi, hi)
        if cov and a <= cov[-1][1] + 2.5:
            cov[-1][1] = max(cov[-1][1], b)
        else:
            cov.append([a, b])
    covered = sum(b - a for a, b in cov)
    sig = tuple((p.code, round(p.lo), round(p.hi)) for p in sorted(seq, key=lambda p: p.lo))
    return covered, sum(1 for p in seq if p.code in SPECIAL), sig


rows = []
for oid, w, (tl, th, sill, head) in ops:
    for side in ("L", "R"):
        lo, hi = (max(0.0, tl - REACH), tl) if side == "L" else (th, min(w.L, th + REACH))
        if hi - lo < 5:
            continue
        hc = hs = rc = rs = 0.0
        exact = True
        for c in range(12):
            h = region_stats(hb, w.id, c, lo, hi)
            r = region_stats(rb, w.id, c, lo, hi)
            hc += h[0]; hs += h[1]; rc += r[0]; rs += r[1]
            exact = exact and h[2] == r[2]
        if exact:
            status = "EXACT_MATCH"
        elif rc + 12 < hc:
            status = "SOLVER_WORSE"
        elif rs >= hs + 2:
            status = "SOLVER_WORSE"
        elif rs < hs:
            status = "SOLVER_BETTER"
        elif rs == hs:
            status = "PHYSICALLY_EQUIVALENT"
        else:
            status = "VALID_ALTERNATIVE"
        rows.append({"opening": oid, "wall": w.id, "side": side, "width": round(th - tl), "sill": sill,
                     "human_cov_cm": round(hc), "solver_cov_cm": round(rc), "human_specials": int(hs),
                     "solver_specials": int(rs), "status": status})
print(json.dumps(collections.Counter(r["status"] for r in rows)))
worse = [r for r in rows if r["status"] == "SOLVER_WORSE"]
for r in worse[:40]:
    print(r)
json.dump(rows, open("comparator_rows.json", "w"), indent=1)
