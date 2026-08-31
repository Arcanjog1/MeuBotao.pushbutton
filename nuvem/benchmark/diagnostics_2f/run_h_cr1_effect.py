# -*- coding: utf-8 -*-
"""ETAPA 2F - item K do pedido: efeito ISOLADO do desempate `(i, j)` do CR-1.

Separa duas coisas que o Teste B mistura:
  (1) o CONJUNTO de candidatos muda com a ordem (assimetria dos predicados);
  (2) mesmo com o MESMO conjunto de candidatos, o desempate `(i, j)` pode
      escolher outro par quando os indices sao renumerados.

Metodo: congela os candidatos gerados na ordem baseline (geometria fixa) e
so' RENUMERA os indices (permutacao), reordenando pelo mesmo `sort_key` do
CR-1 e repetindo o mesmo consumo guloso. Nada do motor e' alterado.

    py -3 nuvem/benchmark/diagnostics_2f/run_h_cr1_effect.py
"""
import json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def greedy(cands, n, perm=None):
    """Mesmo consumo guloso de find_wall_pairs, com os indices RENUMERADOS
    por `perm` (perm[k] = novo indice da linha k). Devolve o conjunto de
    pares aceitos, identificado pelas LINHAS (nao pelos indices novos)."""
    if perm is None:
        keyed = [((c["rank"], -c["r"], -c["ov"], c["i"], c["j"]), c) for c in cands]
    else:
        keyed = []
        for c in cands:
            a, b = perm[c["i"]], perm[c["j"]]
            lo, hi = (a, b) if a < b else (b, a)
            keyed.append(((c["rank"], -c["r"], -c["ov"], lo, hi), c))
    keyed.sort(key=lambda t: t[0])
    used = [False] * n
    acc = []
    for _, c in keyed:
        if used[c["i"]] or used[c["j"]]:
            continue
        used[c["i"]] = used[c["j"]] = True
        acc.append((min(c["i"], c["j"]), max(c["i"], c["j"])))
    return sorted(acc)


def main():
    merged = L.baseline_merged()
    n = len(merged)
    cands = L.build_candidates(merged)
    print("linhas congeladas: %d   candidatos (ordem baseline): %d" % (n, len(cands)))

    # ---- quantos EMPATES reais existem nos 3 primeiros campos do sort_key
    groups = Counter((c["rank"], round(-c["r"], 12), round(-c["ov"], 12)) for c in cands)
    tied = {k: v for k, v in groups.items() if v > 1}
    n_tied_cands = sum(tied.values())
    print("grupos de empate em (rank, -overlap_ratio, -overlap_ft): %d "
          "(envolvendo %d candidatos)" % (len(tied), n_tied_cands))

    # empates que DISPUTAM a mesma linha (so' esses podem mudar o resultado)
    conflicting = 0
    for k, v in tied.items():
        members = [c for c in cands if (c["rank"], round(-c["r"], 12), round(-c["ov"], 12)) == k]
        seen = Counter()
        for c in members:
            seen[c["i"]] += 1
            seen[c["j"]] += 1
        if any(x > 1 for x in seen.values()):
            conflicting += 1
    print("grupos de empate que DISPUTAM a mesma linha: %d" % conflicting)

    base = greedy(cands, n)
    print("pares aceitos (ordem baseline): %d" % len(base))

    rows = []
    for seed in SEEDS:
        perm = list(range(n))
        random.Random(seed).shuffle(perm)
        acc = greedy(cands, n, perm)
        only_b = sorted(set(base) - set(acc))
        only_p = sorted(set(acc) - set(base))
        rows.append(dict(seed=seed, accepted=len(acc), only_base=len(only_b),
                         only_perm=len(only_p), identical=(acc == base)))
        print("  renumeracao seed %-3d -> aceitos=%d  identico=%s  (so' na base: %d, "
              "so' na permutada: %d)" % (seed, len(acc), acc == base, len(only_b), len(only_p)))

    out = dict(n_lines=n, n_cands=len(cands), tie_groups=len(tied),
               tied_candidates=n_tied_cands, conflicting_tie_groups=conflicting,
               accepted_baseline=len(base), permutations=rows,
               ij_invariant=all(r["identical"] for r in rows))
    print("")
    print("VEREDITO: com o MESMO conjunto de candidatos, o desempate (i,j) do "
          "CR-1 %s a renumeracao." % ("SOBREVIVE a" if out["ij_invariant"]
                                      else "NAO SOBREVIVE a"))
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_h_cr1_effect.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("-> " + p)


if __name__ == "__main__":
    main()
