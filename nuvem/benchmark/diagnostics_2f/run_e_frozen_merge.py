# -*- coding: utf-8 -*-
"""ETAPA 2F - TESTE B (itens I/J/K/L do pedido): merge CONGELADO.

Tira o `merge_collinear_fragments` da equacao: parte EXATAMENTE das 2.868
linhas mescladas do baseline, embaralha SO' a ordem dessa lista e roda a
geracao de candidatos + `find_wall_pairs` REAL + o resto da FASE A.

Mede separadamente:
  DETERMINISMO   - mesma lista, duas execucoes -> mesmo resultado?
  INVARIANCIA    - mesma geometria, ordem diferente -> mesma geometria?

    py -3 nuvem/benchmark/diagnostics_2f/run_e_frozen_merge.py
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def main():
    S = L.load()
    merged = L.baseline_merged()
    print("linhas mescladas congeladas: %d  fp=%s" % (len(merged), L.fp(merged, 2)[:16]))

    rows = []
    base = None
    for tag, order in ([("orig", merged), ("orig-2a-vez", list(merged))] +
                       [("s%d" % s, L.shuffled(merged, s)) for s in SEEDS]):
        cands = L.build_candidates(order)
        cfp, ckeys = L.cand_fp(cands, order, 2)
        ckeys1 = L.cand_keys(cands, order, 1)
        res = L.full_pipeline(order)
        wfp, wkeys = L.wall_fp(res["walls"], 2)
        wkeys1 = L.wall_keys(res["walls"], 1)
        gm = L.gabarito_metrics(res["walls"])
        unass = len(res["open_diag"]["unassigned_openings"])
        row = dict(tag=tag, n_lines=len(order), n_cands=len(cands), fp_cands=cfp[:16],
                   accepted=res["accepted"], dedup=res["dedup"],
                   final_walls=len(res["walls"]), fp_walls=wfp[:16],
                   cobertas=gm["cobertas"], ausentes=gm["ausentes"],
                   eixo_ok=gm["eixo_ok"], eixo_10_16=gm["eixo_10_16"],
                   espurias=gm["espurias"], walls_lt50=gm["walls_lt50"],
                   walls_lt20=gm["walls_lt20"],
                   total_len_cm=round(gm["total_len_cm"], 0),
                   openings_assigned=len(S["ops"]) - unass)
        if base is None:
            base = (ckeys, wkeys, ckeys1, wkeys1)
        else:
            ca, cb = Counter(base[0]), Counter(ckeys)
            row["cands_only_base"] = len(list((ca - cb).elements()))
            row["cands_only_here"] = len(list((cb - ca).elements()))
            wa, wb = Counter(base[1]), Counter(wkeys)
            row["walls_only_base"] = len(list((wa - wb).elements()))
            row["walls_only_here"] = len(list((wb - wa).elements()))
            ca1, cb1 = Counter(base[2]), Counter(ckeys1)
            row["cands_only_base_1mm"] = len(list((ca1 - cb1).elements()))
            row["cands_only_here_1mm"] = len(list((cb1 - ca1).elements()))
            wa1, wb1 = Counter(base[3]), Counter(wkeys1)
            row["walls_only_base_1mm"] = len(list((wa1 - wb1).elements()))
            row["walls_only_here_1mm"] = len(list((wb1 - wa1).elements()))
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
        sys.stdout.flush()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_e_frozen_merge.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    print("-> " + out)


if __name__ == "__main__":
    main()
