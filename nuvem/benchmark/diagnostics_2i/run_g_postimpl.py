# -*- coding: utf-8 -*-
"""ETAPA 2I - verificacao POS-IMPLEMENTACAO do CR-2F-E (S7 em producao).

Roda o pipeline headless REAL com o `create_centerline` novo, ja' em
`nuvem/core/engine/geometry.py` - nenhum monkeypatch: `IMPL["cur"]` chama a
funcao de producao.

    py -3 nuvem/benchmark/diagnostics_2i/run_g_postimpl.py
"""
import gc
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2i as I  # noqa: E402
import lib2f as L  # noqa: E402

# baseline pre-CR-2F-E, medido em out_d_downstream.json no commit f8b28e6
PRE = dict(accepted=199, walls=148, cobertas=87, eixo_ok=96, eixo_10_16=3,
           espurias=4, walls_lt50=23, walls_lt20=16, openings_assigned=91,
           watch_ok=7, total_len_cm=45875.68, excess_len_cm=3039.0,
           centering_worst_cm=1.1438, centering_mean_cm=0.01781,
           runtime_ms=4.38)


def main():
    S = L.load()
    mod = S["mod"]
    ext = mod.CENTERLINE_MAX_EXTENSION_FT
    frozen = L.baseline_merged()
    ids = L.line_ids(frozen)
    rep = {"pre_cr2fe": PRE}

    print("=== 1. Producao == estrategia S7 do laboratorio? ===")
    pairs, _ax = I.accepted_pairs(frozen, "cur")
    bad = sum(1 for (a, b) in pairs
              if I.seg_canon(mod.create_centerline(frozen[a], frozen[b], ext), 6)
              != I.seg_canon(I.cl_S7(frozen[a], frozen[b], ext), 6))
    print("  divergencias: %d / %d" % (bad, len(pairs)))
    rep["prod_equals_lab_S7"] = (bad == 0)

    print("")
    print("=== 2. H1 / H2 na funcao de PRODUCAO ===")
    n1 = n2 = 0
    for (a, b) in pairs:
        c1 = mod.create_centerline(frozen[a], frozen[b], ext)
        c2 = mod.create_centerline(frozen[b], frozen[a], ext)
        if I.seg_canon(c1, 6) != I.seg_canon(c2, 6):
            n1 += 1
        for ra, rb in ((1, 0), (0, 1), (1, 1)):
            la = I.reversed_line(frozen[a]) if ra else frozen[a]
            lb = I.reversed_line(frozen[b]) if rb else frozen[b]
            if I.seg_canon(mod.create_centerline(la, lb, ext), 6) != I.seg_canon(c1, 6):
                n2 += 1
    print("  H1 argument order   : %d / %d" % (n1, len(pairs)))
    print("  H2 endpoint direction: %d / %d" % (n2, 3 * len(pairs)))
    rep["H1_diff"] = n1
    rep["H2_diff"] = n2

    print("")
    print("=== 3. DOWNSTREAM (ordem de producao) ===")
    with I.spy(ids) as sp:
        res = L.full_pipeline(frozen)
    s = I.snap(res)
    pair_set = set(frozenset(p) for p in sp.calls)
    for k, label in (("accepted", "pares aceitos"), ("walls", "paredes finais"),
                     ("cobertas", "cobertura /97"), ("ausentes", "ausentes"),
                     ("eixo_ok", "eixos corretos"), ("eixo_10_16", "eixo 10-16 cm"),
                     ("espurias", "espurias"), ("walls_lt50", "walls_lt50"),
                     ("walls_lt20", "walls_lt20"),
                     ("openings_assigned", "aberturas /91"),
                     ("watch_ok", "monitoradas /7")):
        pre = PRE.get(k)
        print("  %-18s %10s   (antes: %s)" % (label, s[k], pre))
    print("  %-18s %10.2f   (antes: %.2f)" % ("total_len_cm", s["total_len_cm"],
                                              PRE["total_len_cm"]))
    print("  %-18s %10.2f   (antes: %.2f)" % ("excesso_cm", s["excess_len_cm"],
                                              PRE["excess_len_cm"]))
    print("  abertura %s orfa: %s" % (I.OP_WATCH, s["op_watch_orfa"]))
    rep["downstream"] = dict((k, v) for k, v in s.items() if k != "covered")
    rep["covered"] = s["covered"]

    # H6' com a restricao aprovada: se 86, a UNICA perda admissivel e' W097
    ref_ids = [w.get("id") or ("REF%03d" % k) for k, w in enumerate(S["ref"]["walls"])]
    missing = sorted(set(ref_ids) - set(s["covered"]))
    print("")
    print("=== 4. H6' com restricao - identificacao NOMINAL ===")
    print("  cobertas : %d/97" % s["cobertas"])
    print("  ausentes : %s" % (missing or "-"))
    rep["not_covered"] = missing
    rep["W097_missing"] = ("W097" in missing)

    print("")
    print("=== 5. PERMUTACOES (5 seeds) ===")
    print("  %-6s %8s %7s %9s %6s %7s %6s %s" %
          ("seed", "eixos!=", "walls", "cobertura", "eixo", "abert", "watch", "ausentes"))
    perm = []
    ok_all = True
    for sd in I.SEEDS:
        gc.collect()
        with I.spy(ids) as sp2:
            r2 = L.full_pipeline(L.shuffled(frozen, sd))
        s2 = I.snap(r2)
        p2 = set(frozenset(p) for p in sp2.calls)
        dax = sum(1 for k in (pair_set & p2)
                  if sp.axes.get(k) != sp2.axes.get(k))
        miss2 = sorted(set(ref_ids) - set(s2["covered"]))
        same = (s2["wall_fp"] == s["wall_fp"])
        ok_all = ok_all and same and dax == 0 and miss2 == missing
        print("  s%-5d %8d %7d %6d/97 %6d %5d/91 %4d/7 %s%s"
              % (sd, dax, s2["walls"], s2["cobertas"], s2["eixo_ok"],
                 s2["openings_assigned"], s2["watch_ok"], miss2 or "-",
                 "" if same else "   <- PAREDES DIFEREM"))
        perm.append(dict(seed=sd, diff_axes=dax, walls=s2["walls"],
                         cobertas=s2["cobertas"], eixo_ok=s2["eixo_ok"],
                         openings=s2["openings_assigned"], watch_ok=s2["watch_ok"],
                         not_covered=miss2, wall_fp_igual=same))
    print("  resultado identico nas 5 permutacoes: %s" % ok_all)
    rep["permutations"] = perm
    rep["identical_across_permutations"] = ok_all

    print("")
    print("=== 6. CENTRALIZACAO do eixo (_axis_offset_error_ft) ===")
    ce = I.axis_centering_error_cm(frozen, pairs, "cur", ext)
    print("  pior : %.4f cm   (antes: %.4f cm)" % (ce["worst_cm"], PRE["centering_worst_cm"]))
    print("  media: %.5f cm   (antes: %.5f cm)" % (ce["mean_cm"], PRE["centering_mean_cm"]))
    rep["centering"] = ce

    print("")
    print("=== 7. RUNTIME de create_centerline (10 repeticoes dos 199 pares) ===")
    REP = 10
    t0 = time.time()
    for _ in range(REP):
        for (a, b) in pairs:
            mod.create_centerline(frozen[a], frozen[b], ext)
    dt = (time.time() - t0) / REP * 1000.0
    print("  agora : %.2f ms   (antes: %.2f ms)  ->  %+.1f%%"
          % (dt, PRE["runtime_ms"], (dt / PRE["runtime_ms"] - 1.0) * 100.0))
    rep["runtime_ms"] = dt

    I.dump("out_g_postimpl.json", rep)


main()
