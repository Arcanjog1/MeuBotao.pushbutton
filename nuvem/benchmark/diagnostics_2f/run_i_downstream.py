# -*- coding: utf-8 -*-
"""ETAPA 2F - itens O/P/Q do pedido: IMPACTO DOWNSTREAM identificado.

Nao basta a contagem: aqui se identifica QUAIS paredes do gabarito e QUAIS
aberturas mudam de destino quando so' a ordem muda, nos dois cenarios:

  FASE A completa   - embaralha as 9.258 linhas cruas (merge incluido)
  MERGE CONGELADO   - embaralha so' as 2.868 linhas ja' mescladas

    py -3 nuvem/benchmark/diagnostics_2f/run_i_downstream.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def snapshot(walls, open_diag):
    S = L.load()
    gm = L.gabarito_metrics(walls)
    covered = set()
    for k, c in enumerate(gm["covs"]):
        if c >= 0.85:
            covered.add(S["ref"]["walls"][k].get("id") or ("REF%03d" % k))
    unass = set()
    for o in open_diag["unassigned_openings"]:
        unass.add(str(o.get("element_id") if isinstance(o, dict) else o))
    return covered, unass, gm


def report(tag, base, cur):
    (cb, ub, gb), (cc, uc, gc) = base, cur
    lost = sorted(cb - cc)
    gained = sorted(cc - cb)
    op_lost = sorted(uc - ub)
    op_back = sorted(ub - uc)
    print("  %-6s cobertas %d->%d  perdidas=%s  ganhas=%s" % (
        tag, len(cb), len(cc), lost or "-", gained or "-"))
    print("         aberturas orfas %d->%d  novas orfas=%s" % (
        len(ub), len(uc), op_lost or "-"))
    return dict(tag=tag, cobertas_base=len(cb), cobertas=len(cc),
                walls_lost=lost, walls_gained=gained,
                openings_newly_unassigned=op_lost, openings_recovered=op_back,
                eixo_ok=gc["eixo_ok"], eixo_10_16=gc["eixo_10_16"],
                espurias=gc["espurias"])


def main():
    S = L.load()
    rep = {"fase_a": [], "merge_congelado": []}

    print("=== FASE A COMPLETA (embaralha as 9.258 cruas) ===")
    merged0, _ = L.run_merge(S["lines"])
    r0 = L.full_pipeline(merged0)
    base = snapshot(r0["walls"], r0["open_diag"])
    print("  baseline: %d cobertas, %d aberturas orfas" % (len(base[0]), len(base[1])))
    for seed in SEEDS:
        m, _ = L.run_merge(L.shuffled(S["lines"], seed))
        r = L.full_pipeline(m)
        rep["fase_a"].append(report("s%d" % seed, base, snapshot(r["walls"], r["open_diag"])))
        sys.stdout.flush()

    print("")
    print("=== MERGE CONGELADO (embaralha so' as 2.868 mescladas) ===")
    frozen = L.baseline_merged()
    rf = L.full_pipeline(frozen)
    basef = snapshot(rf["walls"], rf["open_diag"])
    print("  baseline: %d cobertas, %d aberturas orfas" % (len(basef[0]), len(basef[1])))
    for seed in SEEDS:
        r = L.full_pipeline(L.shuffled(frozen, seed))
        rep["merge_congelado"].append(
            report("s%d" % seed, basef, snapshot(r["walls"], r["open_diag"])))
        sys.stdout.flush()

    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_i_downstream.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print("-> " + p)


if __name__ == "__main__":
    main()
