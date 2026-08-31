# -*- coding: utf-8 -*-
"""ETAPA 2D rodada 3 - empates, linhas de esquadria, W074, invariancia de
ordem das linhas. SOMENTE LEITURA."""
import json, os, sys, math, time, random
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as L

S = L.state()
pending, cands, _ = L.build_candidates()
ref = S["ref"]
Q = 0.05
qerr = lambda k: math.floor(k["err"] / Q + 1e-9)
det = lambda k: (-k["ov"], k["i"], k["j"])
KEY_BASE = lambda k: (-k["r"], k["d_ft"]) + det(k)
KEY_TH = lambda k: (qerr(k), -k["r_long"], -k["ov"]) + det(k)
KEY_TH_R = lambda k: (qerr(k), -k["r"], -k["ov"]) + det(k)

print("=" * 100)
print("1. EMPATES - com que frequencia o criterio SECUNDARIO chega a decidir?")
print("=" * 100)
c = Counter(qerr(k) for k in cands)
print("   candidatos por balde de erro de 0,05 cm (top 8):", c.most_common(8))
# quantos pares COMPETEM pela mesma linha e caem no mesmo balde
byline = defaultdict(list)
for k in cands:
    byline[k["i"]].append(k); byline[k["j"]].append(k)
disputa = 0; empate_balde = 0
for idx, ks in byline.items():
    if len(ks) < 2:
        continue
    disputa += 1
    b = Counter(qerr(k) for k in ks)
    if max(b.values()) > 1:
        empate_balde += 1
print("   linhas disputadas por >=2 candidatos: %d" % disputa)
print("   dessas, com 2+ candidatos no MESMO balde de erro (secundario decide): %d" % empate_balde)
print("   -> em %.0f%% das disputas o erro de espessura ja' decide sozinho" % (
    100.0 * (disputa - empate_balde) / disputa))

print()
print("=" * 100)
print("2. LINHAS DE ESQUADRIA - o ranking corrigido deixa de escolhe-las?")
print("=" * 100)


def esq(name, keyfn, gate=lambda k: True):
    order = sorted([k for k in cands if gate(k)], key=keyfn)
    r = L.run_pipeline(pending, order)
    acc = r["accepted"]
    curta_longa = sum(1 for k in acc if k["short"] < 20.0 and k["long"] >= 100.0)
    curta = sum(1 for k in acc if k["short"] < 20.0)
    fin = L.finish(r["walls"])
    XY = [L.wall_xy(w) for w in fin["final"]]
    lens = [math.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1 in XY]
    print("   %-26s aceitos=%3d | com linha <20 cm: %3d | curta(<20) x longa(>=100): %3d"
          " | walls<20cm=%2d" % (name, len(acc), curta, curta_longa,
                                 sum(1 for x in lens if x < 20)))
    return acc


A_BASE = esq("BASELINE (-r,d)", KEY_BASE)
A_TH = esq("R1 (qerr,-r_long,-ov)", KEY_TH)
A_THR = esq("R1' (qerr,-r,-ov)", KEY_TH_R)
A_G1 = esq("R1+gate err<=1,0", KEY_TH, lambda k: k["err"] <= 1.0)

print()
print("   erro de espessura dos pares 'curta x longa' ACEITOS no baseline:")
print("     ", Counter(round(k["err"], 1) for k in A_BASE
                       if k["short"] < 20.0 and k["long"] >= 100.0).most_common())
print("   os mesmos, na estrategia R1:")
print("     ", Counter(round(k["err"], 1) for k in A_TH
                       if k["short"] < 20.0 and k["long"] >= 100.0).most_common())
print("   comprimento das linhas curtas ainda aceitas em R1:")
print("     ", Counter(round(min(k["li"], k["lj"]), 2) for k in A_TH if k["short"] < 20.0).most_common())

print()
print("=" * 100)
print("3. W074 - por que o gate err<=1,0 a perde?")
print("=" * 100)
W = [w for w in ref["walls"] if w["id"] in ("W074", "W001", "W068", "W037")]
for w in W:
    A = L.Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1])
    best = []
    for k in cands:
        xi0, yi0, xi1, yi1 = [L.cm(v) for v in (pending[k["i"]].GetEndPoint(0).X,
                                                pending[k["i"]].GetEndPoint(0).Y,
                                                pending[k["i"]].GetEndPoint(1).X,
                                                pending[k["i"]].GetEndPoint(1).Y)]
        if L.adiff(A.a, L.ang(xi0, yi0, xi1, yi1)) > 3.0:
            continue
        pm = (A.perp(xi0, yi0) + A.perp(xi1, yi1)) / 2.0
        if abs(pm) > 12.0:
            continue
        t0, t1 = sorted((A.proj(xi0, yi0), A.proj(xi1, yi1)))
        ov = min(t1, A.L) - max(t0, 0.0)
        if ov < 0.5 * A.L:
            continue
        best.append(k)
    best.sort(key=lambda k: k["err"])
    print("   %-6s L=%7.1f  candidatos plausiveis: %d" % (w["id"], A.L, len(best)))
    for k in best[:4]:
        print("      d=%7.3f err=%5.3f r=%.4f r_long=%.4f  linhas %8.2f x %8.2f cm" % (
            k["d"], k["err"], k["r"], k["r_long"], k["li"], k["lj"]))

print()
print("=" * 100)
print("4. INVARIANCIA - ordem das LINHAS de entrada embaralhada (merge + pairing)")
print("=" * 100)
mod = S["mod"]
inp = S["inp"]
ops = S["ops"]
th = S["th"]
tol = S["tol"]
import benchmark.wall_modeling_bridge as wmb
segs = [s for s in inp["segments"] if s.get("layer") == S["setup"]["layer"]]


def full_run(seglist, keyfn, tag):
    lines = [wmb._line_from_segment(mod, s) for s in seglist]
    merged = mod.merge_collinear_fragments(
        lines, mod.COLLINEAR_MATCH_TOLERANCE_FT, mod.MAX_JUNCTION_GAP_FT,
        ops, mod.OPENING_GAP_PERP_TOLERANCE_FT, mod.OPENING_GAP_WIDTH_SLACK_FT)
    wp = mod
    n = len(merged)
    caches = [wp._line_geom_cache(l) for l in merged]
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
    order = sorted(cc, key=keyfn)
    used = [False] * n
    walls = []
    for k in order:
        i, j = k["i"], k["j"]
        if used[i] or used[j]:
            continue
        cl = mod.create_centerline(merged[i], merged[j], mod.CENTERLINE_MAX_EXTENSION_FT)
        if cl:
            cl, lk = mod.clip_centerline_to_caps(cl, k["t_ft"], merged, ops)
            if cl is not None:
                walls.append((cl, k["t_ft"], lk))
        used[i] = used[j] = True
    w2, _ = mod.deduplicate_walls(walls)
    sig = sorted(tuple(round(v, 2) for v in sorted(
        [L.wall_xy(w)[:2], L.wall_xy(w)[2:]])[0] + tuple(sorted([L.wall_xy(w)[:2], L.wall_xy(w)[2:]])[1]))
        for w in w2)
    print("   %-34s linhas=%4d merged=%4d cands=%4d walls(dedup)=%3d" % (
        tag, len(seglist), n, len(cc), len(w2)))
    return sig


ORIG_B = full_run(segs, KEY_BASE, "BASELINE ordem original")
ORIG_T = full_run(segs, KEY_TH, "R1 ordem original")
for seed in (7, 11):
    sh = list(segs)
    random.Random(seed).shuffle(sh)
    sb = full_run(sh, KEY_BASE, "BASELINE embaralhado seed=%d" % seed)
    st = full_run(sh, KEY_TH, "R1 embaralhado seed=%d" % seed)
    print("      BASELINE identico ao original? %s | R1 identico? %s" % (
        "SIM" if sb == ORIG_B else "NAO", "SIM" if st == ORIG_T else "NAO"))

# inversao de endpoints
inv = [dict(s, start=s["end"], end=s["start"]) for s in segs]
sb = full_run(inv, KEY_BASE, "BASELINE endpoints invertidos")
st = full_run(inv, KEY_TH, "R1 endpoints invertidos")
print("      BASELINE identico? %s | R1 identico? %s" % (
    "SIM" if sb == ORIG_B else "NAO", "SIM" if st == ORIG_T else "NAO"))
print("\nOK")
