# -*- coding: utf-8 -*-
import collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import phys, pmodel, holes, evalsolve
HERE = os.path.dirname(os.path.abspath(__file__))
T = phys.load(os.path.join(HERE, os.environ.get("TARGET_JSON", "target_1pav.clean.json")))
H = phys.load(os.path.join(HERE, "human_1pav.clean.json"))
walls = [phys.Wall(w["id"], w["p0"], w["p1"], w["uid"]) for w in T["walls"]]
mas = evalsolve.masonry_wall_ids()
ops = []
for op in T["openings"]:
    best = None
    for w in walls:
        s = phys.opening_span_on_wall(op, w)
        if not s: continue
        bb = op["bb"]; thick = abs((bb[3]-bb[0]) if w.axis == "Y" else (bb[4]-bb[1])); along = abs((bb[4]-bb[1]) if w.axis == "Y" else (bb[3]-bb[0]))
        if along + 1e-6 < thick: continue
        lat = abs(w.lat_of((bb[0]+bb[3])/2, (bb[1]+bb[4])/2))
        if best is None or lat < best[0]: best = (lat, w, s)
    if best: ops.append((best[1].id, best[2][0], best[2][1], best[2][2], best[2][3]))
obw = holes.openings_by_wall(walls, ops)
W = {w.id: w for w in walls}
def in_op(x, y, z):
    for wid, lst in obw.items():
        w = W[wid]
        if abs(w.lat_of(x, y)) > 7.5: continue
        t = w.t_of(x, y)
        for tl, th, s, h in lst:
            if tl - 0.5 <= t <= th + 0.5 and s - 0.5 <= z <= h + 0.5: return True
    return False
def run(doc, stamp, label, courses):
    recs = [phys.piece_record(p) for p in doc["pieces"]]
    phys.assign_walls(recs, walls, by_stamp=stamp)
    recs = [r for r in recs if r["course"] < courses]
    pcs = pmodel.from_revit(recs)
    hs = holes.scan(walls, pcs, obw, courses, wall_filter=mas)
    us = holes.unsupported(pcs, in_op, courses)
    tot = collections.Counter()
    for wid, c, a, b in hs: tot[wid] += b - a
    print("== %s (fiadas 0-%d, 34 paredes de alvenaria): buracos=%d (%.0f cm) | pecas sem apoio (<50%%)=%d" % (label, courses-1, len(hs), sum(tot.values()), len(us)))
    print("   por codigo sem apoio:", collections.Counter(p.code for p, f, v in us).most_common())
    print("   sem apoio SOBRE vazio (nao vao):", collections.Counter(p.code for p, f, v in us if v < 0.5).most_common())
    return hs, us
hh, hu = run(H, False, "HUMANO", 13)
th_, tu = run(T, True, "TARGET", 13)
print("\nburacos HUMANO (amostra):", hh[:15])
print("\nburacos TARGET por parede (cm):", sorted(collections.Counter({k: 0 for k in []}).items()))
agg = collections.defaultdict(float)
for wid, c, a, b in th_: agg[wid] += b - a
print(sorted(((w, round(v)) for w, v in agg.items()), key=lambda x: -x[1])[:20])
print("\namostra buracos TARGET:", th_[:25])
print("\nTARGET sem apoio sobre vazio (amostra):", [(p.wall, p.course, p.code, round(p.lo,1), round(p.hi,1), f) for p, f, v in tu if v < 0.5][:25])
print("\nHUMANO sem apoio sobre vazio (amostra):", [(p.wall, p.course, p.code, round(p.lo,1) if p.lo is not None else None, f) for p, f, v in hu if v < 0.5][:25])

def group(hs):
    g = collections.defaultdict(list)
    for wid, c, a, b in hs:
        g[(wid, round(a / 5) * 5, round(b / 5) * 5)].append(c)
    return sorted(g.items())
print("\n=== HUMANO buracos agrupados (parede, t_lo, t_hi) -> fiadas")
for k, cs in group(hh): print("  ", k, cs)
print("\n=== TARGET buracos agrupados (parede, t_lo, t_hi) -> fiadas")
for k, cs in group(th_): print("  ", k, cs)
