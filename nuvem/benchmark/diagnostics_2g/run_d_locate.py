# -*- coding: utf-8 -*-
"""ETAPA 2G - item 5 (continuacao): ONDE sobra a dependencia de ordem
DEPOIS de simetrizar os predicados.

run_b provou que, com predicado simetrico, o CONJUNTO DE CANDIDATOS fica
invariante (0 diferencas em 5 permutacoes). run_c mostrou que, mesmo assim,
as PAREDES FINAIS continuam mudando. Este script separa as tres camadas
seguintes, medindo cada uma no motor real:

  camada 1  conjunto de PARES ACEITOS (saida do consumo guloso)
  camada 2  geometria do EIXO de cada par aceito (create_centerline)
  camada 3  paredes finais (dedup + extensao + grafo)

Os pares aceitos sao capturados envolvendo `create_centerline` num espiao
(ele recebe as DUAS Lines do par; `id()` identifica a linha original,
porque embaralhar reaproveita os MESMOS objetos).

    py -3 nuvem/benchmark/diagnostics_2g/run_d_locate.py
"""
import gc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2g as G2  # noqa: E402
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]
STRATS = ("cur", "A_mean", "E_bis", "E_ovl", "D_long")


class spy(object):
    """Registra (i, j) na ORDEM em que find_wall_pairs chama
    create_centerline, e a geometria canonica do eixo devolvido."""

    def __init__(self, ids):
        self.ids = ids
        self.g = L.load()["mod"].find_wall_pairs.__globals__
        self.calls = []
        self.axes = {}

    def __enter__(self):
        self.old = self.g["create_centerline"]
        real = self.old

        def wrapper(l1, l2, ext):
            a, b = self.ids[id(l1)], self.ids[id(l2)]
            out = real(l1, l2, ext)
            self.calls.append((a, b))
            self.axes[frozenset((a, b))] = L.canon(out) if out else None
            return out
        self.g["create_centerline"] = wrapper
        return self

    def __exit__(self, *a):
        self.g["create_centerline"] = self.old
        return False

    def pairs(self):
        return set(frozenset(p) for p in self.calls)


def run(strat, lines, ids):
    with G2.patched(strat):
        with spy(ids) as sp:
            res = L.full_pipeline(lines)
    wfp, _ = L.wall_fp(res["walls"])
    return sp.pairs(), dict(sp.axes), wfp, len(res["walls"]), res


def main():
    L.load()
    frozen = L.baseline_merged()
    ids = L.line_ids(frozen)
    rep = {"seeds": SEEDS, "strategies": {}}

    print("=== CAMADA 1/2/3: o que sobrevive a' permutacao, por estrategia ===")
    print("%-8s %-6s %9s %9s %10s %8s %s" %
          ("estrat", "seed", "aceitos", "dif pares", "dif eixos", "walls", "fp paredes"))
    for st in STRATS:
        gc.collect()
        bp, bax, bfp, bw, _ = run(st, frozen, ids)
        print("%-8s %-6s %9d %9s %10s %8d %s" %
              (st, "base", len(bp), "-", "-", bw, bfp[:12]))
        rows = []
        for sd in SEEDS:
            gc.collect()
            p, ax, fp, w, _ = run(st, L.shuffled(frozen, sd), ids)
            dpair = len(bp ^ p)
            common = bp & p
            dax = sum(1 for k in common if bax.get(k) != ax.get(k))
            print("%-8s s%-5d %9d %9d %10d %8d %s%s" %
                  (st, sd, len(p), dpair, dax, w, fp[:12],
                   "" if fp == bfp else "   <- paredes DIFEREM"))
            rows.append(dict(seed=sd, accepted=len(p), diff_pairs=dpair,
                             diff_axes=dax, walls=w, wall_fp=fp,
                             wall_fp_igual=(fp == bfp)))
        rep["strategies"][st] = dict(baseline_accepted=len(bp), baseline_walls=bw,
                                     baseline_wall_fp=bfp, seeds=rows)
        print("")

    # ------------------------------------------------------------------
    print("=== create_centerline(a,b) contra create_centerline(b,a) ===")
    print("Mesmo par, so' a ORDEM dos argumentos. Sobre os pares aceitos da")
    print("estrategia E_bis (predicado ja' simetrico).")
    mod = L.load()["mod"]
    with G2.patched("E_bis"):
        with spy(ids) as sp:
            L.full_pipeline(frozen)
    accepted = sorted(tuple(sorted(p)) for p in sp.pairs())
    ndiff = 0
    worst = 0.0
    ex = []
    for a, b in accepted:
        c1 = mod.create_centerline(frozen[a], frozen[b], mod.CENTERLINE_MAX_EXTENSION_FT)
        c2 = mod.create_centerline(frozen[b], frozen[a], mod.CENTERLINE_MAX_EXTENSION_FT)
        if c1 is None or c2 is None:
            continue
        k1, k2 = L.canon(c1, 6), L.canon(c2, 6)
        if k1 != k2:
            ndiff += 1
            d = max(abs(k1[0][0] - k2[0][0]), abs(k1[0][1] - k2[0][1]),
                    abs(k1[1][0] - k2[1][0]), abs(k1[1][1] - k2[1][1]))
            worst = max(worst, d)
            if len(ex) < 6:
                ex.append(dict(pair=[a, b], delta_cm=d,
                               ab=[list(k1[0]), list(k1[1])],
                               ba=[list(k2[0]), list(k2[1])]))
    print("  pares aceitos testados: %d" % len(accepted))
    print("  eixos que MUDAM com a ordem dos argumentos: %d  (pior |delta| = %.4f cm)"
          % (ndiff, worst))
    for e in ex:
        print("    par %-12s delta=%.4f cm" % (str(e["pair"]), e["delta_cm"]))
    rep["centerline_asymmetry"] = dict(n_accepted=len(accepted), n_diff=ndiff,
                                       worst_delta_cm=worst, examples=ex)

    # ------------------------------------------------------------------
    print("")
    print("=== EMPATES no sort_key do CR-1, por estrategia (causa 2F-C) ===")
    import json
    raw = json.load(open(G2.out_path("out_a_candidates.json"), encoding="utf-8"))
    rep["ties"] = {}
    for st in G2.STRATEGIES:
        cs = [dict(i=r[0], j=r[1], rank=r[2], r=r[3], ov=r[4]) for r in raw[st]]
        groups = {}
        for c in cs:
            groups.setdefault((c["rank"], -c["r"], -c["ov"]), []).append(c)
        tied = [g for g in groups.values() if len(g) > 1]
        # grupos empatados que DISPUTAM a mesma linha
        contested = 0
        for g in tied:
            seen = {}
            hit = False
            for c in g:
                for x in (c["i"], c["j"]):
                    if x in seen:
                        hit = True
                    seen[x] = 1
            contested += int(hit)
        print("  %-8s grupos empatados=%3d (cands=%3d)   disputando a mesma linha=%d"
              % (st, len(tied), sum(len(g) for g in tied), contested))
        rep["ties"][st] = dict(n_groups=len(tied),
                               n_cands=sum(len(g) for g in tied),
                               n_contested=contested)

    G2.dump("out_d_locate.json", rep)


if __name__ == "__main__":
    main()
