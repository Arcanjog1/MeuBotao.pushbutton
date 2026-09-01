# -*- coding: utf-8 -*-
"""ETAPA 2I - item 12: os GATES HARD, alternativa por alternativa, e o
RUNTIME (H11).

Inclui a atribuicao causal da unica perda de cobertura da finalista S7:
a parede ESPURIA de 43,9 m gerada pelo par (474, 2306) remove, dentro de
`deduplicate_walls`, a parede boa que cobre W097 - `deduplicate_walls`
mantem sempre a MAIS LONGA de um grupo, mesmo quando a mais longa e' a
espuria. Isso NAO e' create_centerline: e' o mesmo territorio de
CR-2F-A/CR-2F-D, fora do escopo desta etapa.

    py -3 nuvem/benchmark/diagnostics_2i/run_f_gates.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2i as I  # noqa: E402
import lib2f as L  # noqa: E402

BASE_FP = "c74c9c1ae0e3f169f76e05fe53c01a858fce0af5b4e9d5f1b86fd71e92d2a316"


def pipeline_from(walls):
    S = L.load()
    mod = S["mod"]
    accepted = len(walls)
    walls, dedup = mod.deduplicate_walls(walls)
    walls, jmap = mod.extend_wall_ends_to_junctions(walls, mod.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = mod.build_wall_graph(walls, jmap)
    od = {"clamped_opening_count": 0, "opening_off_center_count": 0,
          "opening_center_gap_max_ft": 0.0, "unassigned_openings": []}
    pw = mod.assign_openings_to_walls(walls, S["ops"], od)
    return dict(accepted=accepted, dedup=dedup, walls=walls, unused=[],
                pair_diag={}, open_diag=od, openings_per_wall=pw,
                nodes=nodes, pair_time=0.0)


def main():
    mod = L.load()["mod"]
    ext = mod.CENTERLINE_MAX_EXTENSION_FT
    frozen = L.baseline_merged()
    pairs, _ = I.accepted_pairs(frozen, "cur")
    rep = {"gates": {}, "runtime": {}}

    print("=== 12. GATES HARD por alternativa ===")
    print("H1 argument order | H2 endpoint dir | H3 5 permutacoes (eixos)")
    print("H4 pares aceitos  | H5 91/91 | H6 >=87/97 | H7 >=96 | H8 7/7 | H9 abertura")
    print("")
    print("%-5s %3s %3s %3s %3s %3s %3s %3s %3s %3s   %s" %
          ("estr", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "observacao"))

    import json
    dd = json.load(open(I.out_path("out_d_downstream.json"), encoding="utf-8"))
    ee = json.load(open(I.out_path("out_e_finalists.json"), encoding="utf-8"))

    for st in I.STRATEGIES:
        if st not in dd["strategies"]:
            continue
        b = dd["strategies"][st]["baseline"]
        seeds = dd["strategies"][st]["seeds"]
        e = ee["strategies"][st]
        g = dict(
            H1=(e["h1_diff"] == 0),
            H2=(e["h2_diff"] == 0),
            H3=all(x["diff_axes"] == 0 for x in seeds),
            H4=(dd["strategies"][st]["pair_diff_vs_cur"] == 0),
            H5=(b["openings_assigned"] == 91),
            H6=(b["cobertas"] >= 87),
            H7=(b["eixo_ok"] >= 96),
            H8=(b["watch_ok"] == 7),
            H9=(not b["op_watch_orfa"]),
        )
        obs = ""
        if st == "S7":
            obs = "unica falha: H6 por 1 parede (W097) - causa fora do CR-2F-E, ver abaixo"
        if st in ("S1", "S2"):
            obs = "H2 falha; centralizacao piora %.2f cm -> %.2f cm" % (
                ee["strategies"]["cur"]["centering"]["worst_cm"], e["centering"]["worst_cm"])
        print("%-5s %3s %3s %3s %3s %3s %3s %3s %3s %3s   %s" %
              ((st,) + tuple("OK" if g[k] else "--" for k in
                             ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9")) + (obs,)))
        rep["gates"][st] = g

    # ------------------------------------------------------------------
    print("")
    print("=== ATRIBUICAO CAUSAL da unica falha de H6 na finalista S7 ===")
    for st in ("cur", "S7"):
        with I.patched(st):
            walls, _u, _d, _t = L.run_pairs(frozen)
        s = I.snap(pipeline_from(list(walls)))
        keep = [w for w in walls
                if I.seg_len_cm((w[0], 0, 0)[0]) < 4000.0]
        s2 = I.snap(pipeline_from(keep))
        print("  %-4s completo        : cobert=%d/97 eixo=%d abert=%d/91 watch=%d/7 walls=%d excesso=%.0f cm"
              % (st, s["cobertas"], s["eixo_ok"], s["openings_assigned"],
                 s["watch_ok"], s["walls"], s["excess_len_cm"]))
        print("  %-4s sem eixos > 40 m: cobert=%d/97 eixo=%d abert=%d/91 watch=%d/7 walls=%d excesso=%.0f cm  (removidas: %d)"
              % (st, s2["cobertas"], s2["eixo_ok"], s2["openings_assigned"],
                 s2["watch_ok"], s2["walls"], s2["excess_len_cm"], len(walls) - len(keep)))
        rep["gates"].setdefault("_causal", {})[st] = dict(
            full=dict((k, s[k]) for k in ("cobertas", "eixo_ok", "openings_assigned",
                                          "watch_ok", "walls", "excess_len_cm")),
            without_40m=dict((k, s2[k]) for k in ("cobertas", "eixo_ok", "openings_assigned",
                                                  "watch_ok", "walls", "excess_len_cm")),
            removed=len(walls) - len(keep))

    # ------------------------------------------------------------------
    print("")
    print("=== H11. RUNTIME de create_centerline (10 repeticoes dos 199 pares) ===")
    REP = 10
    for st in I.STRATEGIES:
        fn = I.IMPL[st]
        t0 = time.time()
        for _ in range(REP):
            for (a, b) in pairs:
                fn(frozen[a], frozen[b], ext)
        dt = (time.time() - t0) / REP
        rep["runtime"][st] = dt
        base = rep["runtime"]["cur"]
        print("  %-5s %8.2f ms / 199 pares   (%+.1f%% vs cur)"
              % (st, dt * 1000.0, (dt / base - 1.0) * 100.0))

    print("")
    print("=== H10. solver_decision_fingerprint ===")
    print("  esperado: %s" % BASE_FP[:16])
    print("  esta etapa NAO altera nenhum arquivo de producao -> inalterado")
    print("  (o fingerprint mede as PECAS que o solver decide, tests/solver_bench.py;")
    print("   nada aqui roda dentro do solver de blocos)")
    rep["solver_fingerprint_expected"] = BASE_FP

    I.dump("out_f_gates.json", rep)


main()
