# -*- coding: utf-8 -*-
"""ETAPA 2I - itens 8, 9, 11 e 12: DOWNSTREAM REAL por alternativa, com as
5 permutacoes, e o isolamento CAMADA POR CAMADA.

Cada alternativa e' injetada no lugar de `create_centerline` DENTRO do
`find_wall_pairs` real (dict de globais de `core.engine.wall_pairing`) -
nenhum arquivo do motor e' alterado. `find_wall_pairs` continua com os
predicados CR-2F-B e o desempate CR-2F-C: o conjunto de pares aceitos
NAO pode mudar, e isso e' medido (H4).

Camadas isoladas:
  1 input        as 2.868 linhas mescladas (congeladas)
  2 candidatos   varredura O(n^2) de find_wall_pairs
  3 pares aceitos  (H4)
  4 create_centerline  <- o alvo do CR-2F-E (H3)
  5 deduplicate_walls
  6 paredes finais

    py -3 nuvem/benchmark/diagnostics_2i/run_d_downstream.py
"""
import gc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2i as I  # noqa: E402
import lib2f as L  # noqa: E402


def layers(lines, strat, ids):
    """Roda o pipeline uma vez e devolve as 6 camadas em forma canonica."""
    with I.patched(strat):
        with I.spy(ids) as sp:
            res = L.full_pipeline(lines)
    pairs = set(frozenset(p) for p in sp.calls)
    axes = dict(sp.axes)
    return dict(pairs=pairs, axes=axes, axis_fp=I.axis_fp(axes),
                dedup=res["dedup"], snap=I.snap(res))


def main():
    L.load()
    frozen = L.baseline_merged()
    ids = L.line_ids(frozen)
    rep = {"seeds": I.SEEDS, "strategies": {}}

    print("=== 11/12. DOWNSTREAM REAL (ordem de producao) ===")
    hdr = ("%-6s %8s %6s %6s %8s %5s %7s %5s %6s %6s %6s %8s %8s %6s %5s" %
           ("estr", "aceitos", "dedup", "walls", "cobert", "eixo", "10-16cm",
            "esp", "lt50", "lt20", "abert", "len_cm", "excesso", "watch", "t(s)"))
    print(hdr)
    base = {}
    for st in I.STRATEGIES:
        gc.collect()
        lay = layers(frozen, st, ids)
        s = lay["snap"]
        base[st] = lay
        print("%-6s %8d %6d %6d %6d/97 %5d %7d %5d %6d %6d %5d/91 %8.0f %8.0f %5d/7 %5.1f"
              % (st, s["accepted"], lay["dedup"], s["walls"], s["cobertas"],
                 s["eixo_ok"], s["eixo_10_16"], s["espurias"], s["walls_lt50"],
                 s["walls_lt20"], s["openings_assigned"], s["total_len_cm"],
                 s["excess_len_cm"], s["watch_ok"], s["pair_time"]))
        rep["strategies"][st] = dict(
            baseline=dict((k, v) for k, v in s.items() if k != "covered"),
            baseline_covered=s["covered"], dedup=lay["dedup"],
            axis_fp=lay["axis_fp"], seeds=[])

    # H4: pares aceitos identicos ao baseline `cur`?
    print("")
    print("=== H4. conjunto de PARES ACEITOS x baseline pos CR-2F-C ===")
    bp = base["cur"]["pairs"]
    for st in I.STRATEGIES:
        d = len(bp ^ base[st]["pairs"])
        print("  %-6s difs=%d  %s" % (st, d, "OK" if d == 0 else "*** MUDOU ***"))
        rep["strategies"][st]["pair_diff_vs_cur"] = d

    # ------------------------------------------------------------------
    print("")
    print("=== 8/H3. PERMUTACOES - onde surge cada divergencia ===")
    print("%-6s %-5s %9s %9s %9s %7s %8s %6s %6s" %
          ("estr", "seed", "c3 pares", "c4 eixos", "c6 walls", "cobert",
           "abert", "watch", "walls"))
    for st in I.STRATEGIES:
        b = base[st]
        bcov = set(b["snap"]["covered"])
        for sd in I.SEEDS:
            gc.collect()
            lay = layers(L.shuffled(frozen, sd), st, ids)
            s = lay["snap"]
            dpair = len(b["pairs"] ^ lay["pairs"])
            common = b["pairs"] & lay["pairs"]
            dax = sum(1 for k in common if b["axes"].get(k) != lay["axes"].get(k))
            dwall = (0 if s["wall_fp"] == b["snap"]["wall_fp"] else 1)
            lost = sorted(bcov - set(s["covered"]))
            print("%-6s s%-4d %9d %9d %9s %5d/97 %5d/91 %4d/7 %6d%s"
                  % (st, sd, dpair, dax,
                     "iguais" if dwall == 0 else "DIFEREM",
                     s["cobertas"], s["openings_assigned"], s["watch_ok"],
                     s["walls"], ("  perdidas=%s" % lost) if lost else ""))
            rep["strategies"][st]["seeds"].append(dict(
                seed=sd, diff_pairs=dpair, diff_axes=dax,
                wall_fp=s["wall_fp"], wall_fp_igual=(dwall == 0),
                axis_fp=lay["axis_fp"], axis_fp_igual=(lay["axis_fp"] == b["axis_fp"]),
                cobertas=s["cobertas"], openings=s["openings_assigned"],
                watch_ok=s["watch_ok"], walls=s["walls"], perdidas=lost))
        print("")

    I.dump("out_d_downstream.json", rep)


main()
