# -*- coding: utf-8 -*-
"""ETAPA 2F - itens H/O/21 do pedido: CLASSIFICAR cada bloco divergente
(assimetria da relacao x nao transitividade) e medir a SEVERIDADE geometrica
do agrupamento (quanto um fragmento e' deslocado lateralmente pelo cluster
em que caiu).

Tambem produz os CONTROLES que impedem overclaim: a distribuicao de
comprimento e de distancia-a-abertura dos blocos divergentes so' significa
alguma coisa comparada com a do Layer inteiro.

    py -3 nuvem/benchmark/diagnostics_2f/run_g_classify.py
"""
import json
import math
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402
from run_c_merge_isolate import uf_blocks, restrict  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def rel_props(lines, idxs, mod, tolf):
    caches = {k: mod._line_geom_cache(lines[k]) for k in idxs}

    def R(a, b):
        return (mod._are_parallel_cached(caches[a], caches[b]) and
                mod._distance_between_parallel_cached(caches[a], caches[b]) <= tolf)

    m = {(a, b): R(a, b) for a in idxs for b in idxs}
    asym = sum(1 for a in idxs for b in idxs if a != b and m[(a, b)] != m[(b, a)])
    nont = 0
    for a in idxs:
        for b in idxs:
            if b == a:
                continue
            if not m[(a, b)]:
                continue
            for c in idxs:
                if c in (a, b):
                    continue
                if m[(b, c)] and not m[(a, c)]:
                    nont += 1
    return asym, nont


def opening_dist_cm(lines, k, ops_xy):
    l = lines[k]
    p0, p1 = l.GetEndPoint(0), l.GetEndPoint(1)
    mx, my = (p0.X + p1.X) / 2.0, (p0.Y + p1.Y) / 2.0
    d = np.hypot(ops_xy[:, 0] - mx, ops_xy[:, 1] - my).min()
    return L.cm(d)


def main():
    S = L.load()
    mod = S["mod"]
    raw = S["lines"]
    n = len(raw)
    ids = L.line_ids(raw)
    tolf = mod.COLLINEAR_MATCH_TOLERANCE_FT
    ops_xy = np.array([[o["center_xy"].X, o["center_xy"].Y] for o in S["ops"]])

    lens_all = np.array([L.cm(l.GetEndPoint(0).DistanceTo(l.GetEndPoint(1))) for l in raw])
    dop_all = np.array([opening_dist_cm(raw, k, ops_xy) for k in range(n)])
    print("CONTROLE (Layer inteiro, %d linhas):" % n)
    print("  comprimento: mediana=%.2fcm  <20cm=%.1f%%  <10cm=%.1f%%"
          % (np.median(lens_all), 100.0 * (lens_all < 20).mean(), 100.0 * (lens_all < 10).mean()))
    print("  dist. a' abertura mais proxima: mediana=%.1fcm  <=100cm=%.1f%%"
          % (np.median(dop_all), 100.0 * (dop_all <= 100).mean()))
    sys.stdout.flush()

    base = L.partition(L.raw_clusters(raw), ids)
    rep = dict(control=dict(n=n, len_median_cm=float(np.median(lens_all)),
                            len_lt20_pct=float(100.0 * (lens_all < 20).mean()),
                            len_lt10_pct=float(100.0 * (lens_all < 10).mean()),
                            dop_median_cm=float(np.median(dop_all)),
                            dop_le100_pct=float(100.0 * (dop_all <= 100).mean())),
               seeds={}, blocks=[])

    kinds = Counter()
    for seed in SEEDS:
        other = L.partition(L.raw_clusters(L.shuffled(raw, seed)), ids)
        blocks = uf_blocks(base, other, n)
        bad = [b for b in blocks if restrict(base, b) != restrict(other, b)]
        rows = []
        for b in bad:
            asym, nont = rel_props(raw, b, mod, tolf)
            kind = ("AMBAS" if asym and nont else
                    "ASSIMETRIA" if asym else
                    "NAO_TRANSITIVA" if nont else "OUTRO")
            kinds[kind] += 1
            lens = [lens_all[k] for k in b]
            rows.append(dict(seed=seed, size=len(b), kind=kind, asym=asym, nontrans=nont,
                             min_len_cm=round(float(min(lens)), 3),
                             max_len_cm=round(float(max(lens)), 3),
                             dop_min_cm=round(float(min(dop_all[k] for k in b)), 1),
                             idxs=sorted(b)))
        rep["seeds"][str(seed)] = Counter(r["kind"] for r in rows)
        rep["blocks"].extend(rows)
        print("seed %-3d blocos divergentes=%-3d  %s"
              % (seed, len(rows), dict(Counter(r["kind"] for r in rows))))
        sys.stdout.flush()

    print("")
    print("CLASSIFICACAO TOTAL: %s" % dict(kinds))
    bl = rep["blocks"]
    if bl:
        blens = np.array([r["min_len_cm"] for r in bl])
        bdop = np.array([r["dop_min_cm"] for r in bl])
        print("blocos divergentes: menor linha mediana=%.2fcm (<20cm em %.1f%% dos blocos)"
              % (np.median(blens), 100.0 * (blens < 20).mean()))
        print("blocos divergentes: abertura mais proxima mediana=%.1fcm (<=100cm em %.1f%%)"
              % (np.median(bdop), 100.0 * (bdop <= 100).mean()))
        rep["block_summary"] = dict(min_len_median_cm=float(np.median(blens)),
                                    min_len_lt20_pct=float(100.0 * (blens < 20).mean()),
                                    dop_median_cm=float(np.median(bdop)),
                                    dop_le100_pct=float(100.0 * (bdop <= 100).mean()),
                                    kinds=dict(kinds))

    # ---- SEVERIDADE: deslocamento lateral imposto pelo cluster ----------
    print("")
    print("=== SEVERIDADE do agrupamento (ordem ORIGINAL) ===")
    clusters = L.raw_clusters(raw)
    bridged = mod._bridge_clusters_via_openings(
        clusters, mod.OPENING_BRIDGE_TOLERANCE_FT, S["ops"],
        mod.OPENING_GAP_PERP_TOLERANCE_FT, mod.OPENING_GAP_WIDTH_SLACK_FT)
    disp = []
    for c in bridged:
        outs = L.merge_cluster(c)
        if not outs:
            continue
        for frag in c:
            p0, p1 = frag.GetEndPoint(0), frag.GetEndPoint(1)
            mid_x, mid_y = (p0.X + p1.X) / 2.0, (p0.Y + p1.Y) / 2.0
            best = None
            for o in outs:
                q0, q1 = o.GetEndPoint(0), o.GetEndPoint(1)
                ux, uy = q1.X - q0.X, q1.Y - q0.Y
                ln = math.hypot(ux, uy)
                if ln < 1e-12:
                    continue
                ux, uy = ux / ln, uy / ln
                d = abs(-(mid_x - q0.X) * uy + (mid_y - q0.Y) * ux)
                if best is None or d < best:
                    best = d
            if best is not None:
                disp.append(L.cm(best))
    disp = np.array(disp)
    rep["displacement"] = dict(
        n=len(disp), max_cm=float(disp.max()), median_cm=float(np.median(disp)),
        gt_02cm=int((disp > 0.2).sum()), gt_1cm=int((disp > 1.0).sum()),
        gt_3cm=int((disp > 3.0).sum()))
    print("  fragmentos crus reposicionados: %d" % len(disp))
    print("  deslocamento lateral mediana=%.4fcm  max=%.4fcm" % (np.median(disp), disp.max()))
    print("  acima da propria tolerancia (0,2cm): %d" % int((disp > 0.2).sum()))
    print("  acima de 1cm: %d   acima de 3cm: %d"
          % (int((disp > 1.0).sum()), int((disp > 3.0).sum())))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_g_classify.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2, default=str)
    print("-> " + out)


if __name__ == "__main__":
    main()
