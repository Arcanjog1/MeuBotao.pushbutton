# -*- coding: utf-8 -*-
"""ETAPA 2G - CUSTO, medido de forma JUSTA.

O run_e comparou as estrategias contra o `cur` do MOTOR - e isso e' injusto
nos dois sentidos: as estrategias entram como funcoes de float puro, e a do
motor usa objetos XYZ (CrossProduct/DotProduct alocam). Varias estrategias
apareceram MAIS RAPIDAS que o baseline so' por causa disso.

Aqui o baseline correto e' `cur_py`: a MESMA formula de hoje, reescrita no
mesmo estilo de float puro das candidatas. A diferenca `estrategia - cur_py`
e' o custo REAL de simetrizar; a diferenca `cur_py - cur` e' o brinde (ou o
prejuizo) de trocar XYZ por float, que vale para todas igualmente.

    py -3 nuvem/benchmark/diagnostics_2g/run_f_cost.py
"""
import gc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2g as G2  # noqa: E402
import lib2f as L  # noqa: E402

REPS = 5
ORDER = ("cur", "cur_py", "A_mean", "B_min", "C_max", "D_long", "E_bis", "E_ovl")

# `cur_py`: a formula ATUAL no estilo float puro (baseline justo).
_g = None


class patched_py(G2.patched):
    def __enter__(self):
        if self.strat != "cur_py":
            return G2.patched.__enter__(self)
        for nm, fn in zip(self.NAMES, (G2._cur_dist, G2._cur_ov)):
            self.old[nm] = self.g[nm]
            self.g[nm] = fn
        return self


def main():
    L.load()
    frozen = L.baseline_merged()
    print("find_wall_pairs sobre as 2.868 linhas congeladas, %d repeticoes" % REPS)
    print("")
    times = {}
    for st in ORDER:
        ts = []
        for _ in range(REPS):
            gc.collect()
            with patched_py(st):
                _w, _u, _d, dt = L.run_pairs(frozen)
            ts.append(dt)
        ts.sort()
        times[st] = ts
    base_eng = times["cur"][REPS // 2]
    base_py = times["cur_py"][REPS // 2]
    print("%-10s %8s %8s %8s   %10s   %10s" %
          ("estrat", "min", "mediana", "max", "vs cur", "vs cur_py"))
    rep = {"reps": REPS, "per_strategy": {}}
    for st in ORDER:
        t = times[st]
        med = t[REPS // 2]
        a = 100.0 * (med / base_eng - 1.0)
        b = 100.0 * (med / base_py - 1.0)
        print("%-10s %8.2f %8.2f %8.2f   %+9.1f%%   %+9.1f%%" %
              (st, t[0], med, t[-1], a, b))
        rep["per_strategy"][st] = dict(min=t[0], mediana=med, max=t[-1],
                                       vs_cur_pct=a, vs_cur_py_pct=b)

    # ------------------------------------------------------------------
    # Peso do pareamento dentro da FASE A: o merge domina (11,35-14,60 s
    # medidos na 2F). Aqui so' o merge, uma vez, para dar o denominador.
    print("")
    print("=== peso na FASE A (denominador do requisito HARD H12) ===")
    S = L.load()
    gc.collect()
    _m, t_merge = L.run_merge(S["lines"])
    print("  merge_collinear_fragments (9.258 linhas cruas): %.2f s" % t_merge)
    print("  %-10s %10s %10s %12s" %
          ("estrat", "pareamento", "merge+par", "vs cur (H12)"))
    tot_cur = t_merge + base_eng
    for st in ORDER:
        med = times[st][REPS // 2]
        tot = t_merge + med
        print("  %-10s %10.2f %10.2f %11.1f%%" %
              (st, med, tot, 100.0 * (tot / tot_cur - 1.0)))
        rep["per_strategy"][st]["fase_a_delta_pct"] = 100.0 * (tot / tot_cur - 1.0)
    rep["t_merge_s"] = t_merge
    print("")
    print("  (a FASE A real inclui ainda dedup/extensao/grafo/aberturas; o")
    print("   denominador medido na 2E foi 25,42 s - usar esse no PLANO)")
    for st in ORDER:
        med = times[st][REPS // 2]
        rep["per_strategy"][st]["fase_a_25s_delta_pct"] = \
            100.0 * ((25.42 + med - base_eng) / 25.42 - 1.0)
    print("  %-10s %s" % ("estrat", "delta sobre a FASE A de 25,42 s (2E)"))
    for st in ORDER:
        print("  %-10s %+.2f%%" % (st, rep["per_strategy"][st]["fase_a_25s_delta_pct"]))
    G2.dump("out_f_cost.json", rep)


if __name__ == "__main__":
    main()
