# -*- coding: utf-8 -*-
"""ETAPA 2K - BATERIA COMPLETA E PERFORMANCE do CR-2F-D.

SOMENTE LEITURA de `nuvem/core/**`. Roda o pipeline headless REAL na ordem
de producao e nas 5 permutacoes de referencia (seeds 1, 2, 3, 10 e 42) e
mede o custo da passada afetada.

O "antes" e' obtido injetando EM MEMORIA a passada 1 anterior (base saindo
de `remaining.pop(0)`, lista `rest` reconstruida) - mesma tecnica das Etapas
2G/2I/2J. Nenhum arquivo e' alterado. Sao medidas TRES variantes:

  ANTES     ordem de ENTRADA + lista `rest`      (pre-CR-2F-D)
  SO' ORDEM ordem CANONICA   + lista `rest`      (a correcao, sem a otimizacao)
  PRODUCAO  ordem CANONICA   + marcador `taken`  (a correcao COM a otimizacao)

`SO' ORDEM` e `PRODUCAO` tem de devolver a MESMA particao e o MESMO
fingerprint - e' o que autoriza a otimizacao (ela nao muda comportamento,
so' paga o custo que a ordenacao introduz).

    python3 nuvem/benchmark/diagnostics_2k/run_b_downstream.py

> Ao redirecionar a saida, NAO use `| head` - o SIGPIPE mata o script antes
> de ele gravar o JSON. Redirecione para um arquivo.
"""
import contextlib
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "diagnostics_2f"))
sys.path.insert(0, os.path.join(_HERE, "..", "diagnostics_2i"))
import lib2f as L  # noqa: E402
import lib2i as I  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def _passada1(mod, lines, coll_tol, canonica, com_taken):
    """A passada 1 do merge nas quatro combinacoes possiveis de
    (ordem canonica?) x (marcador `taken`?)."""
    items = [(line, mod._line_geom_cache(line)) for line in lines]
    if canonica:
        items.sort(key=lambda it: (-it[1][3], mod._line_span_key(it[0])))

    if com_taken:
        taken = [False] * len(items)
        raw = []
        for index, (base, base_cache) in enumerate(items):
            if taken[index]:
                continue
            cluster = [base]
            for other_index in range(index + 1, len(items)):
                if taken[other_index]:
                    continue
                other, other_cache = items[other_index]
                if (mod._are_parallel_cached(base_cache, other_cache) and
                        mod._symmetric_within_distance_cached(
                            base_cache, other_cache, coll_tol)):
                    taken[other_index] = True
                    cluster.append(other)
            raw.append(cluster)
        return raw

    remaining = list(items)
    raw = []
    while remaining:
        base, base_cache = remaining.pop(0)
        cluster, rest = [base], []
        for other, other_cache in remaining:
            if (mod._are_parallel_cached(base_cache, other_cache) and
                    mod._symmetric_within_distance_cached(
                        base_cache, other_cache, coll_tol)):
                cluster.append(other)
            else:
                rest.append((other, other_cache))
        remaining = rest
        raw.append(cluster)
    return raw


@contextlib.contextmanager
def variante(mod, canonica, com_taken):
    """Troca `merge_collinear_fragments` por uma versao com a passada 1
    escolhida. As passadas 2 e 3 sao as DE PRODUCAO, chamadas por nome."""
    original = mod.merge_collinear_fragments

    def substituta(lines, coll_tol, gap_tol, openings, perp, slack,
                   bridge_tol=None):
        if bridge_tol is None:
            bridge_tol = mod.OPENING_BRIDGE_TOLERANCE_FT
        raw = _passada1(mod, lines, coll_tol, canonica, com_taken)
        raw = mod._bridge_clusters_via_openings(raw, bridge_tol, openings,
                                                perp, slack)
        out = []
        for cluster in raw:
            out.extend(mod._merge_collinear_cluster(cluster, gap_tol, openings,
                                                    perp, slack))
        return out

    mod.merge_collinear_fragments = substituta
    try:
        yield
    finally:
        mod.merge_collinear_fragments = original


def particao(raw, mod):
    return sorted(tuple(sorted(mod._line_span_key(l) for l in c)) for c in raw)


def rodada(mod, lines, canonica, com_taken):
    with variante(mod, canonica, com_taken):
        merged, t_merge = L.run_merge(lines)
        res = L.full_pipeline(merged)
    s = I.snap(res)
    ref_ids = [w["id"] for w in L.load()["ref"]["walls"]]
    s["ausentes_ids"] = sorted(set(ref_ids) - set(s["covered"]))
    s["merged"] = len(merged)
    s["merge_fp"] = L.fp(merged, 2)
    s["dedup"] = res["dedup"]
    s["t_merge"] = t_merge
    return s


def tabela(tag, linhas):
    print("")
    print("### %s" % tag)
    print("%-10s %7s %13s %8s %6s %6s %9s %5s %7s %6s %5s %13s %8s" %
          ("ordem", "mescl", "merge_fp", "aceitos", "dedup", "walls",
           "cobertas", "eixo", "abert.", "monit", "esp", "wall_fp", "t_merge"))
    for rotulo, s in linhas:
        print("%-10s %7d %13s %8d %6d %6d %9d %5d %7d %6d %5d %13s %7.1fs" %
              (rotulo, s["merged"], s["merge_fp"][:12], s["accepted"],
               s["dedup"], s["walls"], s["cobertas"], s["eixo_ok"],
               s["openings_assigned"], s["watch_ok"], s["espurias"],
               s["wall_fp"][:12], s["t_merge"]))
    merge_fps = set(s["merge_fp"] for _r, s in linhas)
    wall_fps = set(s["wall_fp"] for _r, s in linhas)
    print("  fingerprints DISTINTOS do merge   : %d" % len(merge_fps))
    print("  fingerprints DISTINTOS das paredes: %d   <- gate do CR-2F-D"
          % len(wall_fps))
    print("  ausentes (producao)               : %s"
          % ",".join(linhas[0][1]["ausentes_ids"]))
    print("  W097 coberta                      : %s"
          % all("W097" not in s["ausentes_ids"] for _r, s in linhas))
    return len(merge_fps), len(wall_fps)


def main():
    S = L.load()
    mod = S["mod"]
    raw = S["lines"]
    saida = {}

    variantes = (("ANTES (ordem de entrada, pre-CR-2F-D)", False, False),
                 ("SO' A ORDEM CANONICA (sem a otimizacao)", True, False),
                 ("PRODUCAO (CR-2F-D: ordem canonica + taken)", True, True))

    for tag, canonica, com_taken in variantes:
        linhas = [("producao", rodada(mod, raw, canonica, com_taken))]
        for sd in SEEDS:
            linhas.append(("seed %d" % sd,
                           rodada(mod, L.shuffled(raw, sd), canonica, com_taken)))
        nm, nw = tabela(tag, linhas)
        saida[tag] = dict(
            merge_fps_distintos=nm, wall_fps_distintos=nw,
            linhas=[{"ordem": r, **{k: v for k, v in s.items()
                                    if k not in ("covered", "ausentes",
                                                 "unassigned", "watch_missing")}}
                    for r, s in linhas])

    print("")
    print("### A OTIMIZACAO NAO MUDA COMPORTAMENTO")
    coll = mod.COLLINEAR_MATCH_TOLERANCE_FT
    iguais = True
    for rotulo, lines in [("producao", raw)] + [("seed %d" % s, L.shuffled(raw, s))
                                                for s in SEEDS]:
        p_rest = particao(_passada1(mod, lines, coll, True, False), mod)
        p_taken = particao(_passada1(mod, lines, coll, True, True), mod)
        ok = p_rest == p_taken
        iguais = iguais and ok
        print("  %-10s particao `rest` == particao `taken`: %s  (%d clusters)"
              % (rotulo, ok, len(p_taken)))
    saida["otimizacao_particao_identica"] = iguais

    print("")
    print("### RUNTIME da passada 1 do merge (3 amostras cada)")
    tempos = {}
    for tag, canonica, com_taken in (("antes", False, False),
                                     ("so a ordem", True, False),
                                     ("producao", True, True)):
        amostras = []
        for _ in range(3):
            t0 = time.time()
            _passada1(mod, raw, coll, canonica, com_taken)
            amostras.append(time.time() - t0)
        tempos[tag] = amostras
        print("  %-11s: %s   media=%.2fs"
              % (tag, " ".join("%.2f" % x for x in amostras),
                 sum(amostras) / len(amostras)))
    ma = sum(tempos["antes"]) / 3.0
    mp = sum(tempos["producao"]) / 3.0
    print("  antes -> producao: %+.2fs  (%+.1f%%)" % (mp - ma, (mp - ma) / ma * 100.0))
    saida["runtime_passada1_s"] = tempos

    with open(os.path.join(_HERE, "out_b_downstream.json"), "w", encoding="utf-8") as fh:
        json.dump(saida, fh, indent=1, default=str)
    print("")
    print("-> out_b_downstream.json")


if __name__ == "__main__":
    main()
