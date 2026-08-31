# -*- coding: utf-8 -*-
"""ETAPA 2G - desempate entre as finalistas + custo + o achado novo.

  1. MECANISMO da assimetria de `create_centerline` (achado NOVO desta
     etapa, nao previsto na 2F): quanto e por que o eixo muda quando so'
     a ordem dos argumentos muda.
  2. DIFERENCIAL E_bis x E_ovl: quais candidatos uma aceita e a outra nao,
     e se esses candidatos sao paredes de verdade ou lixo.
  3. FALLBACK de E_ovl: com que frequencia o caminho "sem sobreposicao
     mutua" e' exercido (se nunca for, ele e' so' guarda defensiva).
  4. CUSTO: tempo do pareamento, repetido, para o requisito HARD H12.

    py -3 nuvem/benchmark/diagnostics_2g/run_e_finalists.py
"""
import gc
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2g as G2  # noqa: E402
import lib2f as L  # noqa: E402

REPS = 3


def main():
    S = L.load()
    mod = S["mod"]
    frozen = L.baseline_merged()
    rep = {}
    raw = json.load(open(G2.out_path("out_a_candidates.json"), encoding="utf-8"))
    cand = dict((st, dict(((r[0], r[1]), dict(rank=r[2], r=r[3], ov=r[4],
                                              d=r[5], mt=r[6])) for r in raw[st]))
                for st in G2.STRATEGIES)

    # ---------------------------------------------------------------- 1
    print("=== 1. MECANISMO da assimetria de create_centerline ===")
    print("   CENTERLINE_MAX_EXTENSION = %.2f cm" % L.cm(mod.CENTERLINE_MAX_EXTENSION_FT))
    print("   O eixo e' ancorado em p0 de `l1` e o intervalo comeca em")
    print("   [0, len(l1)]; `l2` so' ESTENDE, e no maximo max_extension por")
    print("   ponta. Logo o alcance depende de QUEM e' l1.")
    print("")
    print("   %-14s %10s %10s %12s %12s %10s" %
          ("par", "len(a) cm", "len(b) cm", "eixo(a,b)", "eixo(b,a)", "delta cm"))
    det = []
    for a, b in [(89, 1350), (90, 1349), (92, 265), (94, 264), (96, 263), (98, 262)]:
        c1 = mod.create_centerline(frozen[a], frozen[b], mod.CENTERLINE_MAX_EXTENSION_FT)
        c2 = mod.create_centerline(frozen[b], frozen[a], mod.CENTERLINE_MAX_EXTENSION_FT)
        la = L.cm(mod._line_geom_cache(frozen[a])[3])
        lb = L.cm(mod._line_geom_cache(frozen[b])[3])
        def ln(c):
            p, q = c.GetEndPoint(0), c.GetEndPoint(1)
            return math.hypot(L.cm(p.X) - L.cm(q.X), L.cm(p.Y) - L.cm(q.Y))
        k1, k2 = L.canon(c1, 6), L.canon(c2, 6)
        d = max(abs(k1[0][0] - k2[0][0]), abs(k1[0][1] - k2[0][1]),
                abs(k1[1][0] - k2[1][0]), abs(k1[1][1] - k2[1][1]))
        print("   %-14s %10.2f %10.2f %12.2f %12.2f %10.4f" %
              ("[%d,%d]" % (a, b), la, lb, ln(c1), ln(c2), d))
        det.append(dict(pair=[a, b], len_a_cm=la, len_b_cm=lb,
                        axis_ab_cm=ln(c1), axis_ba_cm=ln(c2), delta_cm=d))
    rep["centerline_mechanism"] = dict(
        max_extension_cm=L.cm(mod.CENTERLINE_MAX_EXTENSION_FT), examples=det)

    # ---------------------------------------------------------------- 2
    print("")
    print("=== 2. DIFERENCIAL E_bis x E_ovl (os candidatos que so' uma aceita) ===")
    kb = set(cand["E_bis"])
    ko = set(cand["E_ovl"])
    only_bis = sorted(kb - ko)
    only_ovl = sorted(ko - kb)
    print("   so' E_bis aceita: %d      so' E_ovl aceita: %d" % (len(only_bis), len(only_ovl)))
    print("   %-14s %9s %9s %9s %9s %9s %9s" %
          ("par", "len_i cm", "len_j cm", "d_bis cm", "d_ovl cm", "ang deg", "ratio"))
    G = G2.arrays(frozen)
    K = G2.lexkey(G[0], G[1])
    rows = []
    for tag, lst in (("SO' E_bis", only_bis[:14]), ("SO' E_ovl", only_ovl[:14])):
        print("   -- %s --" % tag)
        for i, j in lst:
            blk = G2.pair_block(G, i, i + 1, K, j, j + 1)
            db = L.cm(float(blk["d_E_bis"][0, 0]))
            do = L.cm(float(blk["d_E_ovl"][0, 0]))
            ang = math.degrees(math.asin(min(1.0, abs(float(blk["cross"][0, 0])))))
            rr = (cand["E_bis"].get((i, j)) or cand["E_ovl"].get((i, j)))["r"]
            print("   %-14s %9.2f %9.2f %9.4f %9.4f %9.4f %9.4f" %
                  ("[%d,%d]" % (i, j), L.cm(G[3][i]), L.cm(G[3][j]), db, do, ang, rr))
            rows.append(dict(tag=tag, pair=[i, j], len_i_cm=L.cm(G[3][i]),
                             len_j_cm=L.cm(G[3][j]), d_bis_cm=db, d_ovl_cm=do,
                             ang_deg=ang, ratio=rr))
    def stats(lst):
        if not lst:
            return {}
        sh = [min(L.cm(G[3][i]), L.cm(G[3][j])) for i, j in lst]
        an = []
        for i, j in lst:
            blk = G2.pair_block(G, i, i + 1, K, j, j + 1)
            an.append(math.degrees(math.asin(min(1.0, abs(float(blk["cross"][0, 0]))))))
        return dict(n=len(lst), menor_len_mediana_cm=sorted(sh)[len(sh) // 2],
                    menor_len_max_cm=max(sh), ang_mediano_deg=sorted(an)[len(an) // 2],
                    ang_max_deg=max(an))
    rep["diferencial_bis_ovl"] = dict(
        only_bis=[list(p) for p in only_bis], only_ovl=[list(p) for p in only_ovl],
        stats_only_bis=stats(only_bis), stats_only_ovl=stats(only_ovl), rows=rows)
    print("")
    print("   perfil dos que SO' E_bis aceita: %s" % rep["diferencial_bis_ovl"]["stats_only_bis"])
    print("   perfil dos que SO' E_ovl aceita: %s" % rep["diferencial_bis_ovl"]["stats_only_ovl"])
    del G, K
    gc.collect()

    # ---------------------------------------------------------------- 3
    print("")
    print("=== 3. FALLBACK de E_ovl (par sem sobreposicao mutua na bissetriz) ===")
    dist_fn, _ov = G2.make_patch("E_ovl")
    caches = [mod._line_geom_cache(l) for l in frozen]
    n_fb = n_par = 0
    for i in range(len(frozen)):
        ci = caches[i]
        for j in range(i + 1, len(frozen)):
            cj = caches[j]
            if not mod._are_parallel_cached(ci, cj):
                continue
            n_par += 1
            bx, by, _nx, _ny, ox, oy = G2._bis(ci, cj)
            def t(p):
                return bx * (p.X - ox) + by * (p.Y - oy)
            lo = max(min(t(ci[0]), t(ci[1])), min(t(cj[0]), t(cj[1])))
            hi = min(max(t(ci[0]), t(ci[1])), max(t(cj[0]), t(cj[1])))
            if hi - lo <= 1e-12:
                n_fb += 1
    print("   pares paralelos: %d   caindo no fallback: %d  (%.2f%%)" %
          (n_par, n_fb, 100.0 * n_fb / max(1, n_par)))
    n_fb_c = sum(1 for (i, j) in cand["E_ovl"] if False)
    print("   entre os %d CANDIDATOS aceitos por E_ovl: %d  (o filtro de"
          % (len(cand["E_ovl"]), n_fb_c))
    print("    ratio >= %.2f ja' exige sobreposicao, entao o fallback e' guarda"
          % mod.MIN_WALL_SEGMENT_OVERLAP_RATIO)
    print("    defensiva, nunca caminho normal)")
    rep["fallback_E_ovl"] = dict(pares_paralelos=n_par, fallback=n_fb,
                                 pct=100.0 * n_fb / max(1, n_par),
                                 entre_candidatos=n_fb_c)
    del caches
    gc.collect()

    # ---------------------------------------------------------------- 4
    print("")
    print("=== 4. CUSTO do pareamento (find_wall_pairs real, %d repeticoes) ===" % REPS)
    print("   %-8s %10s %10s %10s   %s" % ("estrat", "min(s)", "mediana", "max", "vs cur"))
    times = {}
    for st in G2.STRATEGIES:
        ts = []
        for _ in range(REPS):
            gc.collect()
            with G2.patched(st):
                _w, _u, _d, dt = L.run_pairs(frozen)
            ts.append(dt)
        ts.sort()
        times[st] = ts
        base = times["cur"][len(times["cur"]) // 2] if "cur" in times else ts[len(ts) // 2]
        med = ts[len(ts) // 2]
        print("   %-8s %10.2f %10.2f %10.2f   %+.1f%%" %
              (st, ts[0], med, ts[-1], 100.0 * (med / base - 1.0)))
    med_cur = times["cur"][len(times["cur"]) // 2]
    rep["timing"] = dict(
        reps=REPS,
        per_strategy=dict((st, dict(min=t[0], mediana=t[len(t) // 2], max=t[-1],
                                    delta_pct=100.0 * (t[len(t) // 2] / med_cur - 1.0)))
                          for st, t in times.items()))
    print("")
    print("   NOTA: este e' o tempo do PAREAMENTO isolado. A FASE A completa")
    print("   inclui merge_collinear_fragments (11,35-14,60 s medidos na 2F),")
    print("   entao o impacto relativo em H12 e' bem menor - ver PLANO.")
    G2.dump("out_e_finalists.json", rep)


if __name__ == "__main__":
    main()
