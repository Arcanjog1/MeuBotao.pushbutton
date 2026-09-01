# -*- coding: utf-8 -*-
"""ETAPA 2I - item 3 (conclusao): ABLACAO - qual das duas assimetrias de
`create_centerline` responde por quais dos 47 pares divergentes.

Duas variantes de ablacao, cada uma corrigindo UMA coisa so':

  ABL_INT  intervalo simetrico  (clamp da extensao deixa de ser medido a
           partir do comprimento de `l1`), `half_offset` intocado
  ABL_OFF  `half_offset` simetrico (media dos dois sentidos l1->l2 e
           l2->l1), intervalo intocado

    py -3 nuvem/benchmark/diagnostics_2i/run_c_rootcause.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2i as I  # noqa: E402
import lib2f as L  # noqa: E402


def _core(l1, l2, ext, sym_interval, sym_offset):
    """`create_centerline` com um ou os dois mecanismos neutralizados.
    Fora isso, formula IDENTICA a' de producao."""
    mod = L.load()["mod"]
    p0, p1 = l1.GetEndPoint(0), l1.GetEndPoint(1)
    dir1 = (p1 - p0).Normalize()
    q0, q1 = l2.GetEndPoint(0), l2.GetEndPoint(1)
    d2r = (q1 - q0).Normalize()
    dir2 = d2r if dir1.DotProduct(d2r) >= 0.0 else -d2r
    bis = dir1 + dir2
    direction = bis.Normalize() if bis.GetLength() > 1e-9 else dir1
    len1 = (p1 - p0).DotProduct(direction)

    def sample_offset(base, other, n0, n1):
        acc = mod.XYZ(0.0, 0.0, 0.0)
        for t in (0.0, n1 * 0.5, n1):
            sp = base + direction * t
            acc += (mod.project_point_on_line(sp, other) - sp)
        return acc / 3.0

    if sym_offset:
        # media dos dois sentidos: l1->l2 medido em l1, e -(l2->l1) medido
        # em l2. Simetrico por construcao.
        len2 = (q1 - q0).DotProduct(direction)
        o12 = sample_offset(p0, l2, 0.0, len1)
        o21 = sample_offset(q0, l1, 0.0, len2)
        half = ((o12 - o21) / 2.0) * 0.5
    else:
        half = sample_offset(p0, l2, 0.0, len1) * 0.5

    t_q0 = (q0 - p0).DotProduct(direction)
    t_q1 = (q1 - p0).DotProduct(direction)
    ai, zi = 0.0, len1
    aj, zj = (t_q0, t_q1) if t_q0 <= t_q1 else (t_q1, t_q0)
    if sym_interval:
        lo_u, hi_u = min(ai, aj), max(zi, zj)
        lo_lim = min(max(ai, aj - ext), max(aj, ai - ext))
        hi_lim = max(min(zi, zj + ext), min(zj, zi + ext))
        t_lo, t_hi = max(lo_u, lo_lim), min(hi_u, hi_lim)
        if t_hi <= t_lo:
            t_lo, t_hi = max(ai, aj), min(zi, zj)
    else:
        t_lo, t_hi = ai, zi
        for t in (t_q0, t_q1):
            if t < t_lo and (t_lo - t) <= ext:
                t_lo = t
            if t > t_hi and (t - t_hi) <= ext:
                t_hi = t

    a = p0 + direction * t_lo + half
    b = p0 + direction * t_hi + half
    if a.DistanceTo(b) < 0.01:
        return None
    return mod.Line.CreateBound(a, b)


def ABL_INT(l1, l2, ext):
    return _core(l1, l2, ext, True, False)


def ABL_OFF(l1, l2, ext):
    return _core(l1, l2, ext, False, True)


def ABL_BOTH(l1, l2, ext):
    return _core(l1, l2, ext, True, True)


def main():
    mod = L.load()["mod"]
    ext = mod.CENTERLINE_MAX_EXTENSION_FT
    frozen = L.baseline_merged()
    pairs, _ = I.accepted_pairs(frozen, "cur")
    rep = {}

    print("=== ABLACAO: qual mecanismo responde pelos 47 divergentes ===")
    print("%-10s %10s %14s %14s" % ("variante", "divergem", "pior Hausd.cm", "pior |span|cm"))
    variantes = (("cur (baseline)", lambda a, b: mod.create_centerline(a, b, ext)),
                 ("ABL_INT", lambda a, b: ABL_INT(a, b, ext)),
                 ("ABL_OFF", lambda a, b: ABL_OFF(a, b, ext)),
                 ("ABL_BOTH", lambda a, b: ABL_BOTH(a, b, ext)))
    sets = {}
    for name, fn in variantes:
        bad = []
        worst = 0.0
        wspan = 0.0
        for (a, b) in pairs:
            c1, c2 = fn(frozen[a], frozen[b]), fn(frozen[b], frozen[a])
            if c1 is None or c2 is None:
                if (c1 is None) != (c2 is None):
                    bad.append((a, b))
                continue
            if I.seg_canon(c1, 6) != I.seg_canon(c2, 6):
                bad.append((a, b))
                worst = max(worst, I.seg_hausdorff_cm(c1, c2))
                wspan = max(wspan, abs(I.seg_len_cm(c1) - I.seg_len_cm(c2)))
        sets[name] = set(bad)
        print("%-10s %10d %14.2f %14.2f" % (name, len(bad), worst, wspan))
        rep[name] = dict(n_diff=len(bad), worst_haus_cm=worst, worst_span_cm=wspan,
                         pairs=sorted(bad))

    base = sets["cur (baseline)"]
    print("")
    print("  dos %d divergentes do baseline:" % len(base))
    print("    curados SO' pelo intervalo simetrico : %d" % len(base - sets["ABL_INT"]))
    print("    curados SO' pelo offset simetrico    : %d" % len(base - sets["ABL_OFF"]))
    print("    resistentes aos dois isolados        : %d"
          % len(base & sets["ABL_INT"] & sets["ABL_OFF"]))
    print("    resistentes aos DOIS juntos          : %d" % len(base & sets["ABL_BOTH"]))
    rep["cured_by_interval_only"] = len(base - sets["ABL_INT"])
    rep["cured_by_offset_only"] = len(base - sets["ABL_OFF"])
    rep["resistant_both_together"] = len(base & sets["ABL_BOTH"])

    # --- a linha exata responsavel -------------------------------------
    print("")
    print("=== A LINHA responsavel (geometry.py) ===")
    print("  intervalo: `t_lo, t_hi = 0.0, len1` + o clamp")
    print("             `(t_lo - t) <= max_extension_ft` / `(t - t_hi) <= max_extension_ft`")
    print("             -> o teto de extensao e' medido a partir do intervalo de l1.")
    print("  offset   : `sample_ts = (0.0, len1*0.5, len1)` amostrado SOBRE l1 e")
    print("             projetado em l2 -> a media so' cobre o trecho de l1.")

    I.dump("out_c_rootcause.json", rep)


main()
