# -*- coding: utf-8 -*-
"""ETAPA 2D - depuracao do teste minimo de CR-1 (PAIR-006) e da invariancia de
inversao de endpoints. SOMENTE LEITURA."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as L

S = L.state()
mod = S["mod"]; wp = mod
XYZ = mod.XYZ; Line = mod.Line
F = S["F"]
ft = lambda c: c / 100.0 * F
mk = lambda x0, y0, x1, y1: Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))
Q = 0.05
qerr = lambda k: math.floor(k["err"] / Q + 1e-9)
det = lambda k: (-k["ov"], k["i"], k["j"])
KEY_BASE = lambda k: (-k["r"], k["d_ft"]) + det(k)
KEY_TH = lambda k: (qerr(k), -k["r_long"], -k["ov"]) + det(k)


def pair_lines(lines, th, tol):
    n = len(lines); caches = [wp._line_geom_cache(l) for l in lines]; cc = []
    for i in range(n):
        for j in range(i + 1, n):
            ci, cj = caches[i], caches[j]
            if not wp._are_parallel_cached(ci, cj): continue
            d = wp._distance_between_parallel_cached(ci, cj)
            if not (wp.MIN_WALL_THICKNESS_FT <= d <= wp.MAX_WALL_THICKNESS_FT): continue
            mt = wp._closest_target_thickness_ft(d, th, tol)
            if mt is None: continue
            ov, l1, l2 = wp._line_pair_overlap_ft_cached(ci, cj)
            if ov < wp.MIN_WALL_SEGMENT_ABS_FLOOR_FT: continue
            sh = min(l1, l2)
            if sh < 1e-9: continue
            r = ov / sh
            if r < wp.MIN_WALL_SEGMENT_OVERLAP_RATIO: continue
            cc.append(dict(i=i, j=j, d_ft=d, d=L.cm(d), t_ft=mt, t=L.cm(mt),
                           err=abs(L.cm(d) - L.cm(mt)), err_n=abs(L.cm(d) - L.cm(mt)) / L.cm(mt),
                           ov_ft=ov, ov=L.cm(ov), li=L.cm(l1), lj=L.cm(l2),
                           short=L.cm(sh), long=L.cm(max(l1, l2)), r=r, r_long=ov / max(l1, l2)))
    return cc


NAMES = ["A_face_longa_1456", "B_face_verdadeira_1681", "folha_porta_4.445"]
lines = [mk(0, 0, 1456, 0), mk(0, 14, 1681, 14), mk(700, 12.1, 704.445, 12.1)]
th = [ft(14.0)]
tol = mod.compute_detection_tolerance_ft(th)
cc = pair_lines(lines, th, tol)
print("PAIR-006 - candidatos:")
for k in cc:
    print("   %-24s x %-24s d=%7.3f err=%5.3f r=%.4f r_long=%.4f ov=%8.2f" % (
        NAMES[k["i"]], NAMES[k["j"]], k["d"], k["err"], k["r"], k["r_long"], k["ov"]))
print()
for tag, keyfn in (("BASELINE", KEY_BASE), ("R1", KEY_TH)):
    print("   %s - ordem de avaliacao:" % tag)
    used = [False] * len(lines); walls = []
    for k in sorted(cc, key=keyfn):
        skip = used[k["i"]] or used[k["j"]]
        print("      %-24s x %-24s d=%7.3f %s" % (
            NAMES[k["i"]], NAMES[k["j"]], k["d"], "PULADO (ponta ja' usada)" if skip else "ACEITO"))
        if skip: continue
        cl = mod.create_centerline(lines[k["i"]], lines[k["j"]], mod.CENTERLINE_MAX_EXTENSION_FT)
        if cl:
            cl2, lk = mod.clip_centerline_to_caps(cl, k["t_ft"], lines, [])
            if cl2 is not None:
                walls.append((cl2, k["t_ft"], lk))
        used[k["i"]] = used[k["j"]] = True
    for w in walls:
        x0, y0, x1, y1 = L.wall_xy(w)
        print("      => parede esp=%.1f eixo y=%.3f  x de %.2f a %.2f  (len %.2f)" % (
            L.cm(w[1]), (y0 + y1) / 2.0, min(x0, x1), max(x0, x1), math.hypot(x1 - x0, y1 - y0)))
    orfas = [NAMES[i] for i in range(len(lines)) if not used[i]]
    print("      linhas nao usadas: %s" % (orfas or "nenhuma"))
    print()

# ------------------------------------------------------------------ inv-ends
print("=" * 90)
print("INVERSAO DE ENDPOINTS no projeto real - magnitude real da diferenca")
print("=" * 90)
merged = S["merged"]; ops = S["ops"]; TH = S["th"]; TOL = S["tol"]
cc0 = pair_lines(merged, TH, TOL)
inv = [Line.CreateBound(XYZ(l.GetEndPoint(1).X, l.GetEndPoint(1).Y, 0.0),
                        XYZ(l.GetEndPoint(0).X, l.GetEndPoint(0).Y, 0.0)) for l in merged]
cc1 = pair_lines(inv, TH, TOL)
print("   candidatos: original=%d invertido=%d ; mesmos pares (i,j)? %s" % (
    len(cc0), len(cc1), {(k["i"], k["j"]) for k in cc0} == {(k["i"], k["j"]) for k in cc1}))


def sel(lines_, cc_, keyfn):
    used = [False] * len(lines_); out = []
    for k in sorted(cc_, key=keyfn):
        if used[k["i"]] or used[k["j"]]: continue
        cl = mod.create_centerline(lines_[k["i"]], lines_[k["j"]], mod.CENTERLINE_MAX_EXTENSION_FT)
        if cl:
            cl, lk = mod.clip_centerline_to_caps(cl, k["t_ft"], lines_, ops)
            if cl is not None: out.append(((k["i"], k["j"]), cl))
        used[k["i"]] = used[k["j"]] = True
    return out


for tag, keyfn in (("BASELINE", KEY_BASE), ("R1", KEY_TH)):
    a = dict(sel(merged, cc0, keyfn)); b = dict(sel(inv, cc1, keyfn))
    print("   %s: pares escolhidos identicos? %s (orig=%d inv=%d)" % (
        tag, set(a) == set(b), len(a), len(b)))
    comum = set(a) & set(b)
    worst = 0.0; nlen = 0
    for key in comum:
        x0, y0, x1, y1 = L.cm(a[key].GetEndPoint(0).X), L.cm(a[key].GetEndPoint(0).Y), L.cm(a[key].GetEndPoint(1).X), L.cm(a[key].GetEndPoint(1).Y)
        u0, v0, u1, v1 = L.cm(b[key].GetEndPoint(0).X), L.cm(b[key].GetEndPoint(0).Y), L.cm(b[key].GetEndPoint(1).X), L.cm(b[key].GetEndPoint(1).Y)
        d1 = max(math.hypot(x0 - u0, y0 - v0), math.hypot(x1 - u1, y1 - v1))
        d2 = max(math.hypot(x0 - u1, y0 - v1), math.hypot(x1 - u0, y1 - v0))
        dd = min(d1, d2)
        if dd > worst: worst = dd
        if abs(math.hypot(x1 - x0, y1 - y0) - math.hypot(u1 - u0, v1 - v0)) > 0.5: nlen += 1
    print("      pares em comum: %d | maior deslocamento de ponta: %.3f cm | com comprimento diferente >0,5 cm: %d" % (
        len(comum), worst, nlen))
    print("      pares so' no original: %d | so' no invertido: %d" % (len(set(a) - set(b)), len(set(b) - set(a))))
print("\nOK")
