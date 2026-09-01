# -*- coding: utf-8 -*-
"""ETAPA 2J - IMPACTO DOWNSTREAM e RUNTIME do CR-2F-A.

SOMENTE LEITURA de `nuvem/core/**`. Roda o pipeline headless REAL (merge
INCLUIDO, nao congelado) na ordem de producao e nas 5 permutacoes de
referencia (seeds 1, 2, 3, 10, 42), e mede o custo da passada afetada.

O "antes" e' obtido injetando EM MEMORIA a relacao assimetrica de volta nos
quatro sitios (as primitivas antigas continuam no motor, intactas) - mesma
tecnica das etapas 2G/2I. Nenhum arquivo e' alterado.

Observacao de escopo: as diferencas ENTRE seeds sao OBSERVACIONAIS. O
CR-2F-A entrega simetria da relacao, nao invariancia a' ordem - a relacao
continua nao transitiva e o agrupamento continua sendo estrela (CR-2F-D).

    python3 nuvem/benchmark/diagnostics_2j/run_b_downstream.py
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


@contextlib.contextmanager
def relacao_assimetrica(mod):
    """Devolve os quatro sitios ao comportamento pre-CR-2F-A."""
    GG = mod.merge_collinear_fragments.__globals__
    GW = mod.deduplicate_walls.__globals__
    dc = GG["_distance_between_parallel_cached"]
    dl_g = GG["get_distance_between_parallel_lines"]
    dl_w = GW["get_distance_between_parallel_lines"]

    GG["_symmetric_within_distance_cached"] = lambda c1, c2, tol: dc(c1, c2) <= tol
    GG["symmetric_lines_within_distance"] = lambda a, b, tol: dl_g(a, b) <= tol
    GW["symmetric_lines_within_distance"] = lambda a, b, tol: dl_w(a, b) <= tol
    try:
        yield
    finally:
        GG["_symmetric_within_distance_cached"] = mod._symmetric_within_distance_cached
        GG["symmetric_lines_within_distance"] = mod.symmetric_lines_within_distance
        GW["symmetric_lines_within_distance"] = mod.symmetric_lines_within_distance


def rodada(lines_in, antes, mod):
    ctx = relacao_assimetrica(mod) if antes else contextlib.nullcontext()
    with ctx:
        merged, t_merge = L.run_merge(lines_in)
        res = L.full_pipeline(merged)
    s = I.snap(res)
    ref_ids = [w["id"] for w in L.load()["ref"]["walls"]]
    s["ausentes_ids"] = sorted(set(ref_ids) - set(s["covered"]))
    s["merged"] = len(merged)
    s["merge_fp"] = L.fp(merged, 2)[:12]
    s["t_merge"] = t_merge
    return s


def tabela(tag, rows):
    print("")
    print("### %s" % tag)
    print("%-10s %7s %12s %8s %6s %9s %5s %7s %6s %5s %12s %7s" %
          ("ordem", "mescl", "merge_fp", "aceitos", "walls", "cobertas",
           "eixo", "abert.", "monit", "esp", "wall_fp", "t_merge"))
    for lab, s in rows:
        print("%-10s %7d %12s %8d %6d %9d %5d %7d %6d %5d %12s %7.1f" %
              (lab, s["merged"], s["merge_fp"], s["accepted"], s["walls"],
               s["cobertas"], s["eixo_ok"], s["openings_assigned"],
               s["watch_ok"], s["espurias"], s["wall_fp"][:12], s["t_merge"]))
    seeds = [s for _l, s in rows[1:]]
    print("  cobertura nas 5 seeds : %s" % sorted(set(s["cobertas"] for s in seeds)))
    print("  eixo_ok nas 5 seeds   : %s" % sorted(set(s["eixo_ok"] for s in seeds)))
    print("  aberturas nas 5 seeds : %s" % sorted(set(s["openings_assigned"] for s in seeds)))
    print("  monitoradas 5 seeds   : %s" % sorted(set(s["watch_ok"] for s in seeds)))
    print("  wall_fp identico      : %s  (CR-2F-D - observacional)"
          % (len(set(s["wall_fp"] for s in seeds)) == 1))
    print("  ausentes (producao)   : %s" % ",".join(rows[0][1]["ausentes_ids"]))
    p = rows[0][1]
    print("  producao: walls_lt50=%d  walls_lt20=%d  compr_total=%.1f cm  excesso=%.1f cm"
          % (p["walls_lt50"], p["walls_lt20"], p["total_len_cm"], p["excess_len_cm"]))


def main():
    S = L.load()
    mod = S["mod"]
    raw = S["lines"]
    saida = {}

    for tag, antes in (("ANTES (relacao assimetrica)", True),
                       ("DEPOIS (CR-2F-A, T2/MAX)", False)):
        rows = [("producao", rodada(raw, antes, mod))]
        for sd in SEEDS:
            rows.append(("seed %d" % sd, rodada(L.shuffled(raw, sd), antes, mod)))
        tabela(tag, rows)
        saida["antes" if antes else "depois"] = [
            {"ordem": l, **{k: v for k, v in s.items()
                            if k not in ("covered", "ausentes", "unassigned",
                                         "watch_missing")}}
            for l, s in rows]

    print("")
    print("### RUNTIME da passada afetada (merge_collinear_fragments)")
    tempos = {}
    for tag, antes in (("antes", True), ("depois", False)):
        amostras = []
        for _ in range(5):
            # um context manager NOVO por repeticao (os de @contextmanager
            # sao de uso unico)
            with (relacao_assimetrica(mod) if antes else contextlib.nullcontext()):
                _out, dt = L.run_merge(raw)
            amostras.append(dt)
        tempos[tag] = amostras
        print("  %-6s: %s   media=%.2fs" %
              (tag, " ".join("%.2f" % x for x in amostras),
               sum(amostras) / len(amostras)))
    ma = sum(tempos["antes"]) / 5.0
    md = sum(tempos["depois"]) / 5.0
    print("  variacao: %+.1f%%" % ((md - ma) / ma * 100.0))
    saida["runtime_s"] = tempos

    with open(os.path.join(_HERE, "out_b_downstream.json"), "w", encoding="utf-8") as fh:
        json.dump(saida, fh, indent=1, default=str)
    print("")
    print("-> out_b_downstream.json")


if __name__ == "__main__":
    main()
