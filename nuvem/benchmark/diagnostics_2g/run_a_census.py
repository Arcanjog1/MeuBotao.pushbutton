# -*- coding: utf-8 -*-
"""ETAPA 2G - itens 1/2/4: VALIDACAO da camada vetorizada + CENSO EXAUSTIVO
de simetria das 8 estrategias sobre as 2.868 linhas mescladas congeladas.

  0. valida NumPy == motor (estrategia `cur`, 589 candidatos, campo a campo)
  1. caso minimo real da 2F (linhas 16 x 295)
  2. censo de simetria sobre TODOS os 4.111.278 pares i<j. O valor da
     direcao oposta NAO e' assumido: para cada bloco (A,B) o mesmo codigo
     e' chamado DE NOVO como (B,A) e o resultado transposto e' comparado -
     entao a simetria e' MEDIDA, nunca deduzida da formula.
  3. conjunto de candidatos por estrategia (589 do baseline vs cada uma)

    py -3 nuvem/benchmark/diagnostics_2g/run_a_census.py
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2g as G2  # noqa: E402
import lib2f as L  # noqa: E402

CEN = 256   # bloco quadrado do censo de simetria


def main():
    L.load()
    frozen = L.baseline_merged()
    n = len(frozen)
    print("linhas mescladas congeladas: %d  (pares i<j = %d)" % (n, n * (n - 1) // 2))
    rep = {"n_lines": n, "n_pairs": n * (n - 1) // 2}

    # ---------------------------------------------------------------- 0
    print("")
    print("=== 0. VALIDACAO da camada NumPy contra o MOTOR (estrategia cur) ===")
    t0 = time.time()
    eng = L.build_candidates(frozen)
    t_eng = time.time() - t0
    t0 = time.time()
    G = G2.arrays(frozen)
    K = G2.lexkey(G[0], G[1])
    npc = G2.candidates_np(frozen, "cur", G)
    t_np = time.time() - t0
    ekey = {(c["i"], c["j"]): c for c in eng}
    nkey = {(c["i"], c["j"]): c for c in npc}
    same_set = set(ekey) == set(nkey)
    worst = {"d": 0.0, "ov": 0.0, "r": 0.0}
    rank_diff = 0
    for k in set(ekey) & set(nkey):
        x, y = ekey[k], nkey[k]
        for f in ("d", "ov", "r"):
            worst[f] = max(worst[f], abs(x[f] - y[f]))
        rank_diff += int(x["rank"] != y["rank"])
    print("  motor: %d candidatos (%.1fs)   numpy: %d candidatos (%.1fs)"
          % (len(eng), t_eng, len(npc), t_np))
    print("  mesmo CONJUNTO de pares: %s" % ("SIM" if same_set else "NAO"))
    print("  pior |delta|: d=%.3e ft  ov=%.3e ft  ratio=%.3e   ranks diferentes=%d"
          % (worst["d"], worst["ov"], worst["r"], rank_diff))
    ok_valid = (same_set and worst["d"] < 1e-12 and worst["ov"] < 1e-12
                and rank_diff == 0)
    print("  VALIDACAO: %s" % ("PASS" if ok_valid else "FAIL"))
    rep["validation"] = dict(engine=len(eng), numpy=len(npc), same_set=same_set,
                             worst=worst, rank_diff=rank_diff, ok=ok_valid,
                             t_engine_s=t_eng, t_numpy_s=t_np)
    del eng, ekey, nkey

    # ---------------------------------------------------------------- 1
    print("")
    print("=== 1. CASO MINIMO REAL DA 2F: linhas 16 x 295 ===")
    i, j = 16, 295
    ab = G2.pair_block(G, i, i + 1, K, j, j + 1)
    ba = G2.pair_block(G, j, j + 1, K, i, i + 1)
    ang = float(np.degrees(np.arcsin(min(1.0, abs(float(ab["cross"][0, 0]))))))
    print("  len(16)=%.2f cm  len(295)=%.2f cm  desvio angular=%.4f deg"
          % (L.cm(G[3][i]), L.cm(G[3][j]), ang))
    print("  janela de aceite para 14 cm +/- 2,5 cm = [11,50 ; 16,50] cm")
    print("  %-8s %12s %12s %11s   %s" %
          ("estrat", "d(16,295)", "d(295,16)", "|delta|", "veredito ij / ji"))
    mn = {"pair": [i, j], "len_i_cm": L.cm(G[3][i]), "len_j_cm": L.cm(G[3][j]),
          "ang_deg": ang, "dist": {}, "ov": {}}
    for st in G2.STRATEGIES:
        a = L.cm(float(ab["d_" + st][0, 0]))
        b = L.cm(float(ba["d_" + st][0, 0]))
        va, vb = 11.5 <= a <= 16.5, 11.5 <= b <= 16.5
        print("  %-8s %12.6f %12.6f %11.3e   %s / %s"
              % (st, a, b, abs(a - b), "aceita" if va else "recusa",
                 "aceita" if vb else "recusa"))
        mn["dist"][st] = dict(ij_cm=a, ji_cm=b, delta_cm=abs(a - b),
                              aceita_ij=va, aceita_ji=vb, simetrico=(a == b))
    for st in G2.STRATEGIES:
        a = L.cm(float(ab["ov_" + st][0, 0]))
        b = L.cm(float(ba["ov_" + st][0, 0]))
        mn["ov"][st] = dict(ij_cm=a, ji_cm=b, delta_cm=abs(a - b), simetrico=(a == b))
    rep["min_case_16_295"] = mn

    # ---------------------------------------------------------------- 2
    print("")
    print("=== 2. CENSO DE SIMETRIA (cada bloco recalculado nas DUAS ordens) ===")
    acc = dict((st, {"d": [0.0, 0, 0.0, 0], "ov": [0.0, 0, 0.0, 0]})
               for st in G2.STRATEGIES)
    n_par = 0
    t0 = time.time()
    for a0 in range(0, n, CEN):
        a1 = min(n, a0 + CEN)
        for b0 in range(a0, n, CEN):
            b1 = min(n, b0 + CEN)
            AB = G2.pair_block(G, a0, a1, K, b0, b1)
            BA = G2.pair_block(G, b0, b1, K, a0, a1)
            ii = np.arange(a0, a1)[:, None]
            jj = np.arange(b0, b1)[None, :]
            up = jj > ii
            par = AB["par"] & up
            n_par += int(par.sum())
            for st in G2.STRATEGIES:
                for w, pref in ((0, "d"), (2, "ov")):
                    dif = np.abs(AB[pref + "_" + st] - BA[pref + "_" + st].T)
                    r = acc[st][pref]
                    du = dif[up]
                    if du.size:
                        r[0] = max(r[0], float(du.max()))
                        r[1] += int((du > 0.0).sum())
                    dp = dif[par]
                    if dp.size:
                        r[2] = max(r[2], float(dp.max()))
                        r[3] += int((dp > 0.0).sum())
            del AB, BA
    print("  pares PARALELOS (|cross|<0,05) entre os i<j: %d   (%.1fs)"
          % (n_par, time.time() - t0))
    print("  %-8s | %14s %10s | %14s %10s" %
          ("estrat", "max|dd| cm", "n assim.", "max|dov| cm", "n assim."))
    cen = {}
    for st in G2.STRATEGIES:
        d, o = acc[st]["d"], acc[st]["ov"]
        print("  %-8s | %14.6f %10d | %14.6f %10d"
              % (st, L.cm(d[2]), d[3], L.cm(o[2]), o[3]))
        cen[st] = dict(d_max_all_cm=L.cm(d[0]), d_n_all=d[1],
                       d_max_par_cm=L.cm(d[2]), d_n_par=d[3],
                       ov_max_all_cm=L.cm(o[0]), ov_n_all=o[1],
                       ov_max_par_cm=L.cm(o[2]), ov_n_par=o[3],
                       exatamente_simetrico=(d[1] == 0 and o[1] == 0))
    rep["symmetry_census"] = cen
    rep["n_parallel_pairs"] = n_par

    # ---------------------------------------------------------------- 3
    print("")
    print("=== 3. CONJUNTO DE CANDIDATOS por estrategia ===")
    t0 = time.time()
    up_all = G2.candidates_all(frozen, G2.STRATEGIES, G, upper_only=True)
    full_all = G2.candidates_all(frozen, G2.STRATEGIES, G, upper_only=False)
    print("  (%.1fs para as 8 estrategias, nas duas varreduras)" % (time.time() - t0))
    base_set = G2.cand_pairset(up_all["cur"])
    rep["candidates"] = {}
    print("  %-8s %8s %9s %9s %7s %8s  %s" %
          ("estrat", "cand", "2 direc.", "1 direc.", "novos", "perdidos", "fp"))
    for st in G2.STRATEGIES:
        s_up = G2.cand_pairset(up_all[st])
        seen = {}
        for c in full_all[st]:
            k = frozenset((c["i"], c["j"]))
            seen[k] = seen.get(k, 0) + 1
        both = sum(1 for v in seen.values() if v == 2)
        one = sum(1 for v in seen.values() if v == 1)
        fp = G2.pairset_fp(s_up)
        print("  %-8s %8d %9d %9d %7d %8d  %s"
              % (st, len(up_all[st]), both, one,
                 len(s_up - base_set), len(base_set - s_up), fp[:12]))
        rep["candidates"][st] = dict(
            n=len(up_all[st]), both_dir=both, one_dir=one,
            new_vs_cur=sorted(tuple(sorted(p)) for p in (s_up - base_set)),
            lost_vs_cur=sorted(tuple(sorted(p)) for p in (base_set - s_up)),
            fp=fp)
    G2.dump("out_a_census.json", rep)

    # Listas de candidatos gravadas a' parte: `run_c_downstream.py` roda o
    # motor real e NAO pode pagar o custo/memoria de refazer a varredura
    # vetorizada (o processo tem ~240 MB).
    G2.dump("out_a_candidates.json", dict(
        (st, [[c["i"], c["j"], c["rank"], c["r"], c["ov"], c["d"], c["mt"]]
              for c in up_all[st]]) for st in G2.STRATEGIES))


if __name__ == "__main__":
    main()
