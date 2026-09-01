# -*- coding: utf-8 -*-
"""ETAPA 2I - itens 0, 5 e 6: BASELINE, caso minimo e CENSO dos pares
aceitos sob ARGUMENT ORDER.

    py -3 nuvem/benchmark/diagnostics_2i/run_a_baseline_census.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2i as I  # noqa: E402
import lib2f as L  # noqa: E402


def pct(vals, q):
    if not vals:
        return 0.0
    v = sorted(vals)
    k = (len(v) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return v[lo] if lo == hi else v[lo] + (v[hi] - v[lo]) * (k - lo)


def stats(vals):
    if not vals:
        return {}
    return dict(n=len(vals), max=max(vals), mean=sum(vals) / len(vals),
                p50=pct(vals, .50), p90=pct(vals, .90),
                p95=pct(vals, .95), p99=pct(vals, .99))


def main():
    S = L.load()
    mod = S["mod"]
    ext = mod.CENTERLINE_MAX_EXTENSION_FT
    rep = {}

    print("=== 0. BASELINE (estado real do repo) ===")
    frozen = L.baseline_merged()
    print("  linhas apos merge          : %d" % len(frozen))
    res = L.full_pipeline(frozen)
    s = I.snap(res)
    print("  pares aceitos              : %d" % s["accepted"])
    print("  paredes finais             : %d" % s["walls"])
    print("  cobertura humana           : %d/97" % s["cobertas"])
    print("  eixos corretos (<=0,5cm)   : %d" % s["eixo_ok"])
    print("  aberturas atribuidas       : %d/91" % s["openings_assigned"])
    print("  7 monitoradas preservadas  : %d/7  (faltam: %s)"
          % (s["watch_ok"], s["watch_missing"] or "-"))
    print("  abertura %s orfa       : %s" % (I.OP_WATCH, s["op_watch_orfa"]))
    print("  espurias=%d lt50=%d lt20=%d ausentes=%d total_len=%.1f cm"
          % (s["espurias"], s["walls_lt50"], s["walls_lt20"], s["ausentes"],
             s["total_len_cm"]))
    print("  CENTERLINE_MAX_EXTENSION   : %.4f ft = %.2f cm" % (ext, I.cm(ext)))
    rep["baseline"] = dict((k, v) for k, v in s.items() if k != "covered")
    rep["baseline"]["merged_lines"] = len(frozen)
    rep["baseline"]["merged_fp"] = L.fp(frozen, 2)
    rep["baseline"]["ext_cm"] = I.cm(ext)

    # ------------------------------------------------------------------
    print("")
    print("=== 6. CENSO dos pares ACEITOS - create_centerline(A,B) x (B,A) ===")
    pairs, _ax = I.accepted_pairs(frozen, "cur")
    print("  pares aceitos capturados: %d" % len(pairs))

    rows = []
    for (a, b) in pairs:
        la, lb = frozen[a], frozen[b]
        c1 = mod.create_centerline(la, lb, ext)
        c2 = mod.create_centerline(lb, la, ext)
        cls = I.classify(c1, c2)
        row = dict(a=a, b=b, cls=cls)
        row["len_a_cm"] = I.seg_len_cm(la)
        row["len_b_cm"] = I.seg_len_cm(lb)
        row["len_ratio"] = (min(row["len_a_cm"], row["len_b_cm"]) /
                            max(row["len_a_cm"], row["len_b_cm"], 1e-9))
        da = I.seg_angle_deg(la)
        db = I.seg_angle_deg(lb)
        d = abs(da - db) % 180.0
        row["ang_deg"] = min(d, 180.0 - d)
        ci, cj = mod._line_geom_cache(la), mod._line_geom_cache(lb)
        row["thick_cm"] = I.cm(mod._pair_symmetric_thickness_ft_cached(ci, cj))
        ov, l1f, l2f = mod._pair_symmetric_overlap_ft_cached(ci, cj)
        row["overlap_cm"] = I.cm(ov)
        row["overlap_ratio"] = I.cm(ov) / max(min(row["len_a_cm"], row["len_b_cm"]), 1e-9)
        if c1 is not None and c2 is not None:
            row["haus_cm"] = I.seg_hausdorff_cm(c1, c2)
            d0, d1 = I.seg_endpoint_delta_cm(c1, c2)
            row["d_origem_cm"], row["d_destino_cm"] = d0, d1
            row["len_ab_cm"] = I.seg_len_cm(c1)
            row["len_ba_cm"] = I.seg_len_cm(c2)
            row["ab"] = [list(I.seg_canon(c1, 4)[0]), list(I.seg_canon(c1, 4)[1])]
            row["ba"] = [list(I.seg_canon(c2, 4)[0]), list(I.seg_canon(c2, 4)[1])]
        else:
            row["haus_cm"] = float("inf")
            row["d_origem_cm"] = row["d_destino_cm"] = float("inf")
        rows.append(row)

    from collections import Counter
    cnt = Counter(r["cls"] for r in rows)
    print("  classificacao:")
    for k, v in cnt.most_common():
        print("    %-32s %4d" % (k, v))
    ndiff = sum(1 for r in rows if r["cls"] not in ("identicos", "so_direcao_endpoints"))
    print("  DIFERENTES geometricamente : %d / %d" % (ndiff, len(rows)))
    worst = max(rows, key=lambda r: r["haus_cm"])
    print("  pior desvio (Hausdorff)    : %.2f cm  (par %d,%d)"
          % (worst["haus_cm"], worst["a"], worst["b"]))

    dif = [r for r in rows if r["cls"] not in ("identicos", "so_direcao_endpoints")]
    print("")
    print("  distribuicao do desvio (SO' os %d divergentes), em cm:" % len(dif))
    st = stats([r["haus_cm"] for r in dif])
    print("    max=%.2f mean=%.2f p50=%.2f p90=%.2f p95=%.2f p99=%.2f"
          % (st["max"], st["mean"], st["p50"], st["p90"], st["p95"], st["p99"]))
    print("  distribuicao sobre TODOS os %d pares:" % len(rows))
    stall = stats([r["haus_cm"] for r in rows])
    print("    max=%.2f mean=%.2f p50=%.2f p90=%.2f p95=%.2f p99=%.2f"
          % (stall["max"], stall["mean"], stall["p50"], stall["p90"],
             stall["p95"], stall["p99"]))

    print("")
    print("  QUE GEOMETRIA provoca? (divergentes x identicos)")
    ident = [r for r in rows if r["cls"] in ("identicos", "so_direcao_endpoints")]
    for campo in ("len_a_cm", "len_b_cm", "len_ratio", "ang_deg", "thick_cm",
                  "overlap_cm", "overlap_ratio"):
        sd = stats([r[campo] for r in dif])
        si = stats([r[campo] for r in ident])
        print("    %-14s divergentes p50=%9.3f p90=%9.3f max=%9.3f | iguais p50=%9.3f max=%9.3f"
              % (campo, sd["p50"], sd["p90"], sd["max"], si["p50"], si["max"]))

    rep["census"] = dict(n_pairs=len(rows), classes=dict(cnt),
                         n_diff=ndiff, worst_haus_cm=worst["haus_cm"],
                         stats_diff_cm=st, stats_all_cm=stall,
                         geom_diff=dict((c, stats([r[c] for r in dif]))
                                        for c in ("len_a_cm", "len_b_cm", "len_ratio",
                                                  "ang_deg", "thick_cm", "overlap_cm",
                                                  "overlap_ratio")),
                         geom_ident=dict((c, stats([r[c] for r in ident]))
                                         for c in ("len_a_cm", "len_b_cm", "len_ratio",
                                                   "ang_deg", "thick_cm", "overlap_cm",
                                                   "overlap_ratio")),
                         rows=rows)

    # ------------------------------------------------------------------
    print("")
    print("=== 5. CASO MINIMO REAL (maior assimetria do benchmark) ===")
    top = sorted(dif, key=lambda r: -r["haus_cm"])[:5]
    for r in top:
        la, lb = frozen[r["a"]], frozen[r["b"]]
        (pa0, pa1), (pb0, pb1) = I.xy(la), I.xy(lb)
        print("  --- par (%d, %d)  Hausdorff=%.2f cm  [%s]"
              % (r["a"], r["b"], r["haus_cm"], r["cls"]))
        print("      A: (%.2f, %.2f) -> (%.2f, %.2f)   L=%.2f cm  ang=%.4f deg"
              % (I.cm(pa0[0]), I.cm(pa0[1]), I.cm(pa1[0]), I.cm(pa1[1]),
                 r["len_a_cm"], I.seg_angle_deg(la)))
        print("      B: (%.2f, %.2f) -> (%.2f, %.2f)   L=%.2f cm  ang=%.4f deg"
              % (I.cm(pb0[0]), I.cm(pb0[1]), I.cm(pb1[0]), I.cm(pb1[1]),
                 r["len_b_cm"], I.seg_angle_deg(lb)))
        print("      ang(A,B)=%.4f deg  esp=%.3f cm  overlap=%.2f cm (ratio %.4f)"
              % (r["ang_deg"], r["thick_cm"], r["overlap_cm"], r["overlap_ratio"]))
        print("      centerline(A,B): %s  L=%.2f cm" % (r["ab"], r["len_ab_cm"]))
        print("      centerline(B,A): %s  L=%.2f cm" % (r["ba"], r["len_ba_cm"]))
        print("      d_origem=%.2f cm  d_destino=%.2f cm" % (r["d_origem_cm"], r["d_destino_cm"]))
    rep["minimal_real"] = top

    I.dump("out_a_baseline_census.json", rep)


main()
