# -*- coding: utf-8 -*-
"""ETAPA 2G - item 5: DOWNSTREAM REAL de cada estrategia.

Cada estrategia e' injetada DENTRO do `find_wall_pairs` do motor (troca dos
dois predicados no dict de globais de `core.engine.wall_pairing`, desfeita
ao sair) e o pipeline real de `wall_modeling_bridge` roda em cima das 2.868
linhas mescladas CONGELADAS - merge fora do escopo, exatamente como manda o
recorte do CR-2F-B.

Medido por estrategia, na ordem baseline e em 5 permutacoes:
  candidatos, pares aceitos, paredes finais, cobertura do gabarito (87/97),
  eixo correto (96), aberturas (91/91), quais paredes do gabarito somem,
  se a abertura 6558457 fica orfa, e o tempo do pareamento.

    py -3 nuvem/benchmark/diagnostics_2g/run_c_downstream.py
"""
import gc
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2g as G2  # noqa: E402
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]
WATCH = ("W001", "W010", "W037", "W053", "W054", "W068", "W074")
OP_WATCH = "6558457"


def greedy_rank0(cands):
    """Reproduz o consumo guloso do CR-1 sobre a lista de candidatos e conta
    quantos pares aceitos caem no balde de espessura 0 (erro < 0,05 cm) -
    o proxy comparavel a' metrica "espessura exata" de 26.1."""
    cands = sorted(cands, key=lambda c: (c["rank"], -c["r"], -c["ov"], c["i"], c["j"]))
    used = set()
    n0 = n = 0
    for c in cands:
        if c["i"] in used or c["j"] in used:
            continue
        used.add(c["i"])
        used.add(c["j"])
        n += 1
        n0 += int(c["rank"] == 0)
    return n, n0


def snap(res):
    S = L.load()
    gm = L.gabarito_metrics(res["walls"])
    covered = set()
    for k, c in enumerate(gm["covs"]):
        if c >= 0.85:
            covered.add(S["ref"]["walls"][k].get("id") or ("REF%03d" % k))
    unass = set()
    for o in res["open_diag"]["unassigned_openings"]:
        unass.add(str(o.get("element_id") if isinstance(o, dict) else o))
    return dict(accepted=res["accepted"], walls=len(res["walls"]),
                cobertas=len(covered), covered=covered,
                ausentes=gm["ausentes"], eixo_ok=gm["eixo_ok"],
                eixo_10_16=gm["eixo_10_16"], espurias=gm["espurias"],
                lt50=gm["walls_lt50"], lt20=gm["walls_lt20"],
                total_len_cm=gm["total_len_cm"],
                openings_ok=91 - len(unass), unass=unass,
                pair_time=res["pair_time"])


def main():
    L.load()
    frozen = L.baseline_merged()
    rep = {"seeds": SEEDS, "strategies": {}}
    # Candidatos vem do JSON gravado por run_a_census.py (ja' validado
    # campo a campo contra o motor): refazer a varredura vetorizada aqui
    # estoura o teto de ~240 MB do processo com o motor carregado.
    raw = json.load(open(G2.out_path("out_a_candidates.json"), encoding="utf-8"))
    allc = dict((st, [dict(i=r[0], j=r[1], rank=r[2], r=r[3], ov=r[4],
                           d=r[5], mt=r[6]) for r in raw[st]])
                for st in G2.STRATEGIES)
    ncand = dict((st, len(allc[st])) for st in G2.STRATEGIES)
    del raw
    gc.collect()

    print("=== BASELINE (ordem de producao) ===")
    print("%-8s %6s %8s %6s %9s %6s %7s %6s %7s %6s %6s" %
          ("estrat", "cand", "aceitos", "walls", "cobertas", "eixo", "10-16cm",
           "esp.", "aberts", "rank0", "t(s)"))
    base = {}
    for st in G2.STRATEGIES:
        gc.collect()
        with G2.patched(st):
            r = L.full_pipeline(frozen)
        s = snap(r)
        acc_sim, r0 = greedy_rank0(allc[st])
        s["greedy_sim_accepted"] = acc_sim
        s["greedy_sim_rank0"] = r0
        s["candidates"] = ncand[st]
        base[st] = s
        print("%-8s %6d %8d %6d %9d %6d %7d %6d %7d %6d %6.1f" %
              (st, ncand[st], s["accepted"], s["walls"], s["cobertas"],
               s["eixo_ok"], s["eixo_10_16"], s["espurias"], s["openings_ok"],
               r0, s["pair_time"]))
        rep["strategies"][st] = dict(
            baseline=dict((k, v) for k, v in s.items()
                          if k not in ("covered", "unass")),
            baseline_covered=sorted(s["covered"]),
            baseline_unassigned=sorted(s["unass"]),
            seeds=[])
        del r
        gc.collect()

    print("")
    print("=== PERMUTACOES (mesma geometria, ordem da lista diferente) ===")
    print("%-8s %-6s %8s %6s %9s %6s %7s  %s" %
          ("estrat", "seed", "aceitos", "walls", "cobertas", "eixo", "aberts",
           "paredes do gabarito perdidas / abertura orfa"))
    for st in G2.STRATEGIES:
        b = base[st]
        for sd in SEEDS:
            gc.collect()
            with G2.patched(st):
                r = L.full_pipeline(L.shuffled(frozen, sd))
            s = snap(r)
            lost = sorted(b["covered"] - s["covered"])
            gained = sorted(s["covered"] - b["covered"])
            newop = sorted(s["unass"] - b["unass"])
            print("%-8s s%-5d %8d %6d %9d %6d %7d  perdidas=%s ganhas=%s orfas+=%s" %
                  (st, sd, s["accepted"], s["walls"], s["cobertas"], s["eixo_ok"],
                   s["openings_ok"], lost or "-", gained or "-", newop or "-"))
            rep["strategies"][st]["seeds"].append(dict(
                seed=sd, accepted=s["accepted"], walls=s["walls"],
                cobertas=s["cobertas"], eixo_ok=s["eixo_ok"],
                eixo_10_16=s["eixo_10_16"], espurias=s["espurias"],
                openings_ok=s["openings_ok"], lost=lost, gained=gained,
                newly_unassigned=newop,
                invariante=(not lost and not gained and not newop and
                            s["accepted"] == b["accepted"] and
                            s["walls"] == b["walls"])))
            del r
            gc.collect()
        sys.stdout.flush()

    print("")
    print("=== PAREDES VIGIADAS (cobertas no baseline?) e ABERTURA %s ===" % OP_WATCH)
    print("%-8s %s" % ("estrat", "  ".join("%-5s" % w for w in WATCH)))
    for st in G2.STRATEGIES:
        b = base[st]
        print("%-8s %s   abertura %s: %s" %
              (st, "  ".join("%-5s" % ("SIM" if w in b["covered"] else "nao")
                             for w in WATCH),
               OP_WATCH, "ORFA" if OP_WATCH in b["unass"] else "ok"))
        rep["strategies"][st]["watch"] = dict(
            (w, w in b["covered"]) for w in WATCH)
        rep["strategies"][st]["opening_6558457_orfa"] = OP_WATCH in b["unass"]

    print("")
    print("=== ESTABILIDADE (quantas das 5 seeds sao IDENTICAS ao baseline) ===")
    for st in G2.STRATEGIES:
        ok = sum(1 for s in rep["strategies"][st]["seeds"] if s["invariante"])
        print("  %-8s %d/5" % (st, ok))
        rep["strategies"][st]["seeds_invariantes"] = ok

    G2.dump("out_c_downstream.json", rep)


if __name__ == "__main__":
    main()
