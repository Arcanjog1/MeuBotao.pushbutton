# -*- coding: utf-8 -*-
"""ETAPA 2F - itens A/B/C do pedido: reproduzir o baseline e medir varias
sementes de embaralhamento das 9.258 linhas CRUAS.

Para cada ordem registra: entrada, saida do merge, fingerprint geometrico
canonico da saida, candidatos de find_wall_pairs (contagem + fingerprint
geometrico), pares aceitos, dedup, walls finais e metricas de gabarito.

    py -3 nuvem/benchmark/diagnostics_2f/run_a_baseline.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402

SEEDS = [None, 1, 2, 3, 10, 42]


def main():
    S = L.load()
    raw = S["lines"]
    rows = []
    base_merged = None
    for seed in SEEDS:
        order = raw if seed is None else L.shuffled(raw, seed)
        merged, t_merge = L.run_merge(order)
        f2 = L.fp(merged, 2)
        f1 = L.fp(merged, 1)
        f0 = L.fp(merged, 0)
        cands = L.build_candidates(merged)
        cfp, _ = L.cand_fp(cands, merged, 2)
        res = L.full_pipeline(merged)
        wfp, _ = L.wall_fp(res["walls"], 2)
        gm = L.gabarito_metrics(res["walls"])
        unass = len(res["open_diag"]["unassigned_openings"])
        row = dict(
            seed=("orig" if seed is None else seed),
            n_in=len(order), n_merged=len(merged), t_merge=round(t_merge, 2),
            fp_merge_01mm=f2[:16], fp_merge_1mm=f1[:16], fp_merge_1cm=f0[:16],
            n_cands=len(cands), fp_cands=cfp[:16],
            accepted=res["accepted"], dedup=res["dedup"],
            final_walls=len(res["walls"]), fp_walls=wfp[:16],
            cobertas=gm["cobertas"], ausentes=gm["ausentes"],
            eixo_ok=gm["eixo_ok"], eixo_10_16=gm["eixo_10_16"], espurias=gm["espurias"],
            walls_lt50=gm["walls_lt50"], walls_lt20=gm["walls_lt20"],
            total_len_cm=round(gm["total_len_cm"], 0),
            openings_assigned=len(S["ops"]) - unass, openings_total=len(S["ops"]),
        )
        rows.append(row)
        if seed is None:
            base_merged = merged
        else:
            oa, ob = L.diff_sets(base_merged, merged, 2)
            row["merge_only_in_orig"] = len(oa)
            row["merge_only_in_seed"] = len(ob)
            oa1, ob1 = L.diff_sets(base_merged, merged, 1)
            row["merge_only_in_orig_1mm"] = len(oa1)
            row["merge_only_in_seed_1mm"] = len(ob1)
        print(json.dumps(row, ensure_ascii=False))
        sys.stdout.flush()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_a_baseline.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    print("-> " + out)


if __name__ == "__main__":
    main()
