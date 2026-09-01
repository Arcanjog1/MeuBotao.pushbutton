# -*- coding: utf-8 -*-
"""ETAPA 2I - itens 3 e 7: DISSECACAO operacao-a-operacao de
`create_centerline` e as DUAS invariancias, medidas SEPARADAMENTE.

  ARGUMENT ORDER   create_centerline(A,B)  x  create_centerline(B,A)
  ENDPOINT DIR     A(p0,p1)/B(p0,p1)  x  A(p1,p0)/B(p0,p1)  x  ...

    py -3 nuvem/benchmark/diagnostics_2i/run_b_invariance.py
"""
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2i as I  # noqa: E402
import lib2f as L  # noqa: E402


def dissect(l1, l2, ext):
    """Recalcula, passo a passo, EXATAMENTE o que `create_centerline` faz -
    para poder dizer QUAL operacao muda quando a ordem inverte. A formula e'
    copiada linha a linha de core/engine/geometry.py (verificada contra a
    funcao real no fim desta funcao)."""
    mod = L.load()["mod"]
    p0 = l1.GetEndPoint(0)
    p1 = l1.GetEndPoint(1)
    dir1 = (p1 - p0).Normalize()
    q0, q1 = l2.GetEndPoint(0), l2.GetEndPoint(1)
    dir2_raw = (q1 - q0).Normalize()
    dir2 = dir2_raw if dir1.DotProduct(dir2_raw) >= 0.0 else -dir2_raw
    bis = dir1 + dir2
    direction = bis.Normalize() if bis.GetLength() > 1e-9 else dir1
    len1 = (p1 - p0).DotProduct(direction)
    sample_ts = (0.0, len1 * 0.5, len1)
    off = mod.XYZ(0.0, 0.0, 0.0)
    for t in sample_ts:
        sp = p0 + direction * t
        off += (mod.project_point_on_line(sp, l2) - sp)
    half = (off / len(sample_ts)) * 0.5
    t_lo, t_hi = 0.0, len1
    t_q0 = (q0 - p0).DotProduct(direction)
    t_q1 = (q1 - p0).DotProduct(direction)
    for t in (t_q0, t_q1):
        if t < t_lo and (t_lo - t) <= ext:
            t_lo = t
        if t > t_hi and (t - t_hi) <= ext:
            t_hi = t
    a = p0 + direction * t_lo + half
    b = p0 + direction * t_hi + half
    return dict(
        anchor=(I.cm(p0.X), I.cm(p0.Y)),
        direction=(direction.X, direction.Y),
        # direcao canonica (sinal removido) - para separar "direcao do eixo"
        # de "sentido em que o eixo foi escrito"
        direction_canon=((direction.X, direction.Y)
                         if (direction.X, direction.Y) >= (0.0, 0.0)
                         else (-direction.X, -direction.Y)),
        len1_cm=I.cm(len1),
        half_offset=(I.cm(half.X), I.cm(half.Y)),
        half_offset_norm_cm=I.cm(math.hypot(half.X, half.Y)),
        t_lo_cm=I.cm(t_lo), t_hi_cm=I.cm(t_hi),
        span_cm=I.cm(t_hi - t_lo),
        start=(I.cm(a.X), I.cm(a.Y)), end=(I.cm(b.X), I.cm(b.Y)),
    )


def rnd(v, nd=6):
    if isinstance(v, tuple):
        return tuple(round(x, nd) + 0.0 for x in v)
    return round(v, nd) + 0.0


def main():
    S = L.load()
    mod = S["mod"]
    ext = mod.CENTERLINE_MAX_EXTENSION_FT
    frozen = L.baseline_merged()
    pairs, _ = I.accepted_pairs(frozen, "cur")
    rep = {}

    # --- 0. a dissecacao reproduz a funcao real? -----------------------
    bad = 0
    for (a, b) in pairs:
        d = dissect(frozen[a], frozen[b], ext)
        real = mod.create_centerline(frozen[a], frozen[b], ext)
        if real is None:
            continue
        k = I.seg_canon(real, 4)
        mine = tuple(sorted(((rnd(d["start"], 4)), (rnd(d["end"], 4)))))
        if k != mine:
            bad += 1
    print("=== 3.0 A dissecacao replica `create_centerline`? divergencias: %d/%d ==="
          % (bad, len(pairs)))
    rep["dissect_matches_engine"] = (bad == 0)
    assert bad == 0, "dissecacao NAO replica a funcao real - o resto nao vale"

    # --- 3. qual operacao muda com a ORDEM DOS ARGUMENTOS -------------
    print("")
    print("=== 3. QUAL OPERACAO muda quando (A,B) vira (B,A) ===")
    FIELDS = ("anchor", "direction_canon", "len1_cm", "half_offset_norm_cm",
              "t_lo_cm", "t_hi_cm", "span_cm")
    chg = Counter()
    span_delta = []
    for (a, b) in pairs:
        d1 = dissect(frozen[a], frozen[b], ext)
        d2 = dissect(frozen[b], frozen[a], ext)
        for f in FIELDS:
            if rnd(d1[f]) != rnd(d2[f]):
                chg[f] += 1
        span_delta.append(abs(d1["span_cm"] - d2["span_cm"]))
    print("  %-24s %s" % ("operacao", "pares (de %d) em que o valor MUDA" % len(pairs)))
    for f in FIELDS:
        print("  %-24s %4d" % (f, chg[f]))
    print("  pior |span(A,B) - span(B,A)| = %.2f cm" % max(span_delta))
    rep["op_changes_argument_order"] = dict(chg)
    rep["worst_span_delta_cm"] = max(span_delta)

    # o eixo final so' muda se o SEGMENTO muda; conta quantos dos que mudam
    # tem a direcao igual (isolando "so' o intervalo/ancora" de "a direcao")
    same_dir_diff_seg = 0
    for (a, b) in pairs:
        c1 = mod.create_centerline(frozen[a], frozen[b], ext)
        c2 = mod.create_centerline(frozen[b], frozen[a], ext)
        if c1 is None or c2 is None:
            continue
        if I.seg_canon(c1, 6) == I.seg_canon(c2, 6):
            continue
        d1, d2 = dissect(frozen[a], frozen[b], ext), dissect(frozen[b], frozen[a], ext)
        if rnd(d1["direction_canon"]) == rnd(d2["direction_canon"]):
            same_dir_diff_seg += 1
    print("  dos divergentes, com a MESMA direcao de eixo: %d" % same_dir_diff_seg)
    rep["diff_seg_same_direction"] = same_dir_diff_seg

    # --- 7. ENDPOINT DIRECTION ----------------------------------------
    print("")
    print("=== 7. ENDPOINT DIRECTION (invariancia DIFERENTE da de argumentos) ===")
    VAR = (("A(p0,p1) B(p0,p1)", False, False),
           ("A(p1,p0) B(p0,p1)", True, False),
           ("A(p0,p1) B(p1,p0)", False, True),
           ("A(p1,p0) B(p1,p0)", True, True))
    print("  %-20s %10s %14s %14s" % ("variante", "difere", "pior Hausd.", "pior |span|"))
    rep["endpoint_direction"] = {}
    for strat in I.STRATEGIES:
        base_axes = {}
        for (a, b) in pairs:
            base_axes[(a, b)] = I.IMPL[strat](frozen[a], frozen[b], ext)
        out = {}
        for name, ra, rb in VAR[1:]:
            nd = 0
            worst = 0.0
            wspan = 0.0
            for (a, b) in pairs:
                la = I.reversed_line(frozen[a]) if ra else frozen[a]
                lb = I.reversed_line(frozen[b]) if rb else frozen[b]
                c = I.IMPL[strat](la, lb, ext)
                c0 = base_axes[(a, b)]
                if c is None or c0 is None:
                    if c is not c0:
                        nd += 1
                    continue
                if I.seg_canon(c, 6) != I.seg_canon(c0, 6):
                    nd += 1
                    worst = max(worst, I.seg_hausdorff_cm(c, c0))
                    wspan = max(wspan, abs(I.seg_len_cm(c) - I.seg_len_cm(c0)))
            out[name] = dict(n_diff=nd, worst_haus_cm=worst, worst_span_cm=wspan)
        # ARGUMENT ORDER da mesma estrategia, para a tabela ficar completa
        nd = 0
        worst = 0.0
        for (a, b) in pairs:
            c1 = base_axes[(a, b)]
            c2 = I.IMPL[strat](frozen[b], frozen[a], ext)
            if c1 is None or c2 is None:
                if (c1 is None) != (c2 is None):
                    nd += 1
                continue
            if I.seg_canon(c1, 6) != I.seg_canon(c2, 6):
                nd += 1
                worst = max(worst, I.seg_hausdorff_cm(c1, c2))
        out["ARGUMENT ORDER (B,A)"] = dict(n_diff=nd, worst_haus_cm=worst,
                                           worst_span_cm=0.0)
        print("  --- estrategia %s (%d pares)" % (strat, len(pairs)))
        for k in ("ARGUMENT ORDER (B,A)",) + tuple(v[0] for v in VAR[1:]):
            v = out[k]
            print("  %-22s %8d %14.2f %14.2f"
                  % (k, v["n_diff"], v["worst_haus_cm"], v["worst_span_cm"]))
        rep["endpoint_direction"][strat] = out

    I.dump("out_b_invariance.json", rep)


main()
