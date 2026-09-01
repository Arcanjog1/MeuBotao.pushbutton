# -*- coding: utf-8 -*-
"""ETAPA 2I - itens 9 e 10: CORRECAO GEOMETRICA das alternativas, alem da
simetria. Simetria e' necessaria, nao suficiente (item 10).

Mede, por alternativa:
  - H1 (argument order) e H2 (endpoint direction), ja' medidos no run_b
  - reproducao do `cur` nos pares em que o `cur` JA' era simetrico
    (uma alternativa que muda esses pares esta' mudando comportamento que
     nao e' o alvo do CR-2F-E)
  - erro de CENTRALIZACAO do eixo (`_axis_offset_error_ft` do proprio motor)
  - excesso de comprimento fora do gabarito (disparo do eixo)

    py -3 nuvem/benchmark/diagnostics_2i/run_e_finalists.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2i as I  # noqa: E402
import lib2f as L  # noqa: E402


def main():
    mod = L.load()["mod"]
    ext = mod.CENTERLINE_MAX_EXTENSION_FT
    frozen = L.baseline_merged()
    pairs, _ = I.accepted_pairs(frozen, "cur")

    sym, asym = [], []
    for (a, b) in pairs:
        c1 = mod.create_centerline(frozen[a], frozen[b], ext)
        c2 = mod.create_centerline(frozen[b], frozen[a], ext)
        (sym if I.seg_canon(c1, 6) == I.seg_canon(c2, 6) else asym).append((a, b))
    print("pares aceitos: %d  (ja' simetricos no `cur`: %d | ambiguos: %d)"
          % (len(pairs), len(sym), len(asym)))

    rep = {"n_pairs": len(pairs), "n_sym": len(sym), "n_asym": len(asym),
           "strategies": {}}

    print("")
    print("=== 9/10. CORRECAO GEOMETRICA (nao so' simetria) ===")
    print("%-5s %10s %10s %12s %12s %10s" %
          ("estr", "H1 dif", "H2 dif", "muda SIM", "centr.pior", "centr.med"))
    for st in I.STRATEGIES:
        n1 = n2 = 0
        w2 = 0.0
        for (a, b) in pairs:
            c1 = I.IMPL[st](frozen[a], frozen[b], ext)
            c2 = I.IMPL[st](frozen[b], frozen[a], ext)
            if I.seg_canon(c1, 6) != I.seg_canon(c2, 6):
                n1 += 1
            cr = I.IMPL[st](I.reversed_line(frozen[a]), I.reversed_line(frozen[b]), ext)
            if I.seg_canon(cr, 6) != I.seg_canon(c1, 6):
                n2 += 1
                if cr is not None and c1 is not None:
                    w2 = max(w2, I.seg_hausdorff_cm(cr, c1))
        nsim = 0
        for (a, b) in sym:
            c0 = mod.create_centerline(frozen[a], frozen[b], ext)
            c = I.IMPL[st](frozen[a], frozen[b], ext)
            if I.seg_canon(c, 4) != I.seg_canon(c0, 4):
                nsim += 1
        ce = I.axis_centering_error_cm(frozen, pairs, st, ext)
        print("%-5s %10d %10d %10d/%d %12.4f %10.5f"
              % (st, n1, n2, nsim, len(sym), ce["worst_cm"], ce["mean_cm"]))
        rep["strategies"][st] = dict(h1_diff=n1, h2_diff=n2, h2_worst_cm=w2,
                                     changes_already_symmetric=nsim,
                                     centering=ce)

    I.dump("out_e_finalists.json", rep)


main()
