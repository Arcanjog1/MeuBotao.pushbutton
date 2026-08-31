# -*- coding: utf-8 -*-
"""ETAPA 2D rodada 4 - invariancia geometrica (rotacao/translacao/inversao) e
MULTIPLAS ESPESSURAS em fixture sintetica. SOMENTE LEITURA do repo."""
import json, os, sys, math, random
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as L
import benchmark.wall_modeling_bridge as wmb

S = L.state()
mod = S["mod"]
wp = mod
Q = 0.05
qerr = lambda k: math.floor(k["err"] / Q + 1e-9)
det = lambda k: (-k["ov"], k["i"], k["j"])
KEY_BASE = lambda k: (-k["r"], k["d_ft"]) + det(k)
KEY_TH = lambda k: (qerr(k), -k["r_long"], -k["ov"]) + det(k)


def pair_lines(lines, th, tol):
    n = len(lines)
    caches = [wp._line_geom_cache(l) for l in lines]
    cc = []
    for i in range(n):
        ci = caches[i]
        for j in range(i + 1, n):
            cj = caches[j]
            if not wp._are_parallel_cached(ci, cj):
                continue
            d = wp._distance_between_parallel_cached(ci, cj)
            if not (wp.MIN_WALL_THICKNESS_FT <= d <= wp.MAX_WALL_THICKNESS_FT):
                continue
            mt = wp._closest_target_thickness_ft(d, th, tol)
            if mt is None:
                continue
            ov, l1, l2 = wp._line_pair_overlap_ft_cached(ci, cj)
            if ov < wp.MIN_WALL_SEGMENT_ABS_FLOOR_FT:
                continue
            sh = min(l1, l2)
            if sh < 1e-9:
                continue
            r = ov / sh
            if r < wp.MIN_WALL_SEGMENT_OVERLAP_RATIO:
                continue
            cc.append(dict(i=i, j=j, d_ft=d, d=L.cm(d), t_ft=mt, t=L.cm(mt),
                           err=abs(L.cm(d) - L.cm(mt)),
                           err_n=abs(L.cm(d) - L.cm(mt)) / L.cm(mt),
                           ov_ft=ov, ov=L.cm(ov), li=L.cm(l1), lj=L.cm(l2),
                           short=L.cm(sh), long=L.cm(max(l1, l2)),
                           r=r, r_long=ov / max(l1, l2)))
    return cc


def select(lines, cc, keyfn, ops):
    n = len(lines)
    used = [False] * n
    walls = []
    for k in sorted(cc, key=keyfn):
        i, j = k["i"], k["j"]
        if used[i] or used[j]:
            continue
        cl = mod.create_centerline(lines[i], lines[j], mod.CENTERLINE_MAX_EXTENSION_FT)
        if cl:
            cl, lk = mod.clip_centerline_to_caps(cl, k["t_ft"], lines, ops)
            if cl is not None:
                walls.append((cl, k["t_ft"], lk))
        used[i] = used[j] = True
    return walls


def sig(walls, xf=None):
    out = []
    for w in walls:
        x0, y0, x1, y1 = L.wall_xy(w)
        if xf:
            x0, y0 = xf(x0, y0)
            x1, y1 = xf(x1, y1)
        a, b = sorted([(round(x0, 1), round(y0, 1)), (round(x1, 1), round(y1, 1))])
        out.append((a, b, round(L.cm(w[1]), 1)))
    return sorted(out)


print("=" * 100)
print("A. INVARIANCIA GEOMETRICA (rotacao/translacao/inversao) - sem merge, so' o PAREAMENTO")
print("=" * 100)
merged = S["merged"]
ops = S["ops"]
th = S["th"]
tol = S["tol"]
base_cc = pair_lines(merged, th, tol)
XYZ = mod.XYZ
Line = mod.Line


def xform(lines, fn):
    out = []
    for l in lines:
        p0, p1 = l.GetEndPoint(0), l.GetEndPoint(1)
        a = fn(p0.X, p0.Y)
        b = fn(p1.X, p1.Y)
        out.append(Line.CreateBound(XYZ(a[0], a[1], 0.0), XYZ(b[0], b[1], 0.0)))
    return out


def xops(fn):
    out = []
    for o in ops:
        c = o["center_xy"]
        a = fn(c.X, c.Y)
        d = dict(o)
        d["center_xy"] = XYZ(a[0], a[1], 0.0)
        if o.get("bbox_center_xy") is not None:
            bb = o["bbox_center_xy"]
            e = fn(bb.X, bb.Y)
            d["bbox_center_xy"] = XYZ(e[0], e[1], 0.0)
        out.append(d)
    return out


TR = 1234.5


def T90(x, y):  return (-y, x)
def T180(x, y): return (-x, -y)
def T270(x, y): return (y, -x)
def TT(x, y):   return (x + TR, y - TR / 3.0)


INV = {"rot90": lambda X, Y: (Y, -X), "rot180": lambda X, Y: (-X, -Y),
       "rot270": lambda X, Y: (-Y, X), "transl": lambda X, Y: (X - L.cm(TR), Y + L.cm(TR / 3.0))}

for tag, keyfn in (("BASELINE", KEY_BASE), ("R1", KEY_TH)):
    ref_sig = sig(select(merged, base_cc, keyfn, ops))
    print("   --- %s (referencia: %d paredes) ---" % (tag, len(ref_sig)))
    for name, fn in (("rot90", T90), ("rot180", T180), ("rot270", T270), ("transl", TT)):
        lines2 = xform(merged, fn)
        ops2 = xops(fn)
        cc2 = pair_lines(lines2, th, tol)
        w2 = select(lines2, cc2, keyfn, ops2)
        s2 = sig(w2, INV[name])
        same = (s2 == ref_sig)
        if not same:
            d1 = set(ref_sig) - set(s2)
            d2 = set(s2) - set(ref_sig)
            print("      %-8s cands=%3d walls=%3d  IDENTICO=%s (dif: -%d/+%d)" % (
                name, len(cc2), len(w2), same, len(d1), len(d2)))
        else:
            print("      %-8s cands=%3d walls=%3d  IDENTICO=SIM" % (name, len(cc2), len(w2)))
    # inversao de endpoints (sem merge)
    inv = [Line.CreateBound(XYZ(l.GetEndPoint(1).X, l.GetEndPoint(1).Y, 0.0),
                            XYZ(l.GetEndPoint(0).X, l.GetEndPoint(0).Y, 0.0)) for l in merged]
    cc3 = pair_lines(inv, th, tol)
    s3 = sig(select(inv, cc3, keyfn, ops))
    print("      %-8s cands=%3d walls=%3d  IDENTICO=%s (dif: -%d/+%d)" % (
        "inv-ends", len(cc3), len(s3), s3 == ref_sig,
        len(set(ref_sig) - set(s3)), len(set(s3) - set(ref_sig))))
    # embaralhamento da ORDEM das linhas (sem merge)
    for seed in (5,):
        idx = list(range(len(merged)))
        random.Random(seed).shuffle(idx)
        sl = [merged[i] for i in idx]
        cc4 = pair_lines(sl, th, tol)
        s4 = sig(select(sl, cc4, keyfn, ops))
        print("      %-8s cands=%3d walls=%3d  IDENTICO=%s (dif: -%d/+%d)" % (
            "shuffle", len(cc4), len(s4), s4 == ref_sig,
            len(set(ref_sig) - set(s4)), len(set(s4) - set(ref_sig))))

# --------------------------------------------------------------------------
print()
print("=" * 100)
print("B. MULTIPLAS ESPESSURAS - fixture sintetica (PAIR-001..010)")
print("=" * 100)
F = S["F"]
ft = lambda c: c / 100.0 * F


def mk(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def case(name, lines, th_cm, expect, ops_=None):
    th_ = sorted(ft(c) for c in th_cm)
    tol_ = mod.compute_detection_tolerance_ft(th_)
    cc = pair_lines(lines, th_, tol_)
    out = {}
    for tag, keyfn in (("BASE", KEY_BASE), ("R1", KEY_TH)):
        w = select(lines, cc, keyfn, ops_ or [])
        got = sorted((round(L.cm(x[1]), 1),
                      round(math.hypot(*(lambda a: (a[2] - a[0], a[3] - a[1]))(L.wall_xy(x))), 1))
                     for x in w)
        out[tag] = got
    ok_b = out["BASE"] == expect
    ok_r = out["R1"] == expect
    print("   %-9s tol=%.2f cm cands=%2d | esperado %s" % (name, L.cm(tol_), len(cc), expect))
    print("             BASELINE -> %-34s %s" % (out["BASE"], "OK" if ok_b else "FALHA"))
    print("             R1       -> %-34s %s" % (out["R1"], "OK" if ok_r else "FALHA"))
    return ok_b, ok_r


res = []
# PAIR-001: par unico exato a 14
res.append(case("PAIR-001", [mk(0, 0, 400, 0), mk(0, 14, 400, 14)], [14.0], [(14.0, 400.0)]))

# PAIR-002: face A com dois candidatos, 12 e 14 -> deve escolher 14
res.append(case("PAIR-002", [mk(0, 0, 400, 0), mk(0, 12, 400, 12), mk(0, 14, 400, 14)],
                [14.0], [(14.0, 400.0)]))

# PAIR-003: candidatos 14 e 16 -> deve escolher 14
res.append(case("PAIR-003", [mk(0, 0, 400, 0), mk(0, 14, 400, 14), mk(0, 16, 400, 16)],
                [14.0], [(14.0, 400.0)]))

# PAIR-004: allowed [9,14,19]; duas paredes reais, uma de 9 e uma de 14
res.append(case("PAIR-004",
                [mk(0, 0, 400, 0), mk(0, 9, 400, 9),
                 mk(0, 300, 400, 300), mk(0, 314, 400, 314)],
                [9.0, 14.0, 19.0], [(9.0, 400.0), (14.0, 400.0)]))

# PAIR-005: duas paredes proximas disputando a MESMA face central
res.append(case("PAIR-005",
                [mk(0, 0, 400, 0), mk(0, 14, 400, 14), mk(0, 28, 400, 28)],
                [14.0], [(14.0, 400.0), (14.0, 400.0)]))

# PAIR-006 (CR-1): folha de porta de 4,445 cm a 12,1 cm da face longa
res.append(case("PAIR-006",
                [mk(0, 0, 1456, 0),              # face longa A
                 mk(0, 14, 1681, 14),            # face longa verdadeira (14 cm)
                 mk(700, 12.1, 704.445, 12.1)],  # folha de porta
                [14.0], [(14.0, 1681.0)]))

# PAIR-007: T
res.append(case("PAIR-007",
                [mk(0, 0, 400, 0), mk(0, 14, 400, 14),
                 mk(200, 14, 200, 300), mk(214, 14, 214, 300)],
                [14.0], [(14.0, 286.0), (14.0, 400.0)]))

# PAIR-008: L
res.append(case("PAIR-008",
                [mk(0, 0, 400, 0), mk(0, 14, 386, 14),
                 mk(386, 14, 386, 300), mk(400, 0, 400, 300)],
                [14.0], [(14.0, 293.0), (14.0, 400.0)]))

# PAIR-010: ordem embaralhada de PAIR-002
ls = [mk(0, 14, 400, 14), mk(0, 0, 400, 0), mk(0, 12, 400, 12)]
res.append(case("PAIR-010", ls, [14.0], [(14.0, 400.0)]))

# PAIR-011: ordem das espessuras embaralhada
res.append(case("PAIR-011",
                [mk(0, 0, 400, 0), mk(0, 9, 400, 9),
                 mk(0, 300, 400, 300), mk(0, 314, 400, 314)],
                [19.0, 9.0, 14.0], [(9.0, 400.0), (14.0, 400.0)]))

# PAIR-012: espessuras vizinhas [12,14] (tolerancia aperta para 1,0)
res.append(case("PAIR-012",
                [mk(0, 0, 400, 0), mk(0, 12, 400, 12), mk(0, 14, 400, 14)],
                [12.0, 14.0], [(12.0, 400.0)]))

print()
print("   RESUMO fixture sintetica: BASELINE passa %d/%d | R1 passa %d/%d" % (
    sum(1 for b, r in res if b), len(res), sum(1 for b, r in res if r), len(res)))
print("\nOK")
