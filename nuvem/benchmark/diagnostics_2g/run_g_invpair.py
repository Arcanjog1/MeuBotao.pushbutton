# -*- coding: utf-8 -*-
"""ETAPA 2G - PROTOTIPO dos testes de regressao INV-PAIR-001 e INV-PAIR-002.

NAO promove nada para `nuvem/tests/**` (isso e' implementacao, e esta etapa
e' de PROJETO). Aqui os dois testes sao escritos e EXECUTADOS contra todas
as estrategias, para provar que:

  - eles REPROVAM a formula de hoje (`cur`) - senao nao sao teste de nada;
  - eles APROVAM a estrategia vencedora.

INV-PAIR-001  caso minimo real, 2 linhas mescladas (16 x 295 da 2F),
              congeladas em coordenadas literais (cm) - o teste nao pode
              depender de rodar o merge nem de ler input_real.json.
INV-PAIR-002  as 2.868 linhas mescladas, 5 permutacoes: o CONJUNTO
              GEOMETRICO de candidatos tem que ser identico.

    py -3 nuvem/benchmark/diagnostics_2g/run_g_invpair.py
"""
import gc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2g as G2  # noqa: E402
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def fixture_001(frozen):
    """Coordenadas literais (cm) das duas linhas do caso minimo."""
    out = []
    for k in (16, 295):
        p0, p1 = frozen[k].GetEndPoint(0), frozen[k].GetEndPoint(1)
        out.append([round(L.cm(p0.X), 6), round(L.cm(p0.Y), 6),
                    round(L.cm(p1.X), 6), round(L.cm(p1.Y), 6)])
    return out


def main():
    L.load()
    mod = L.load()["mod"]
    frozen = L.baseline_merged()
    rep = {}

    # ================================================================ 001
    fx = fixture_001(frozen)
    print("=== INV-PAIR-001 - fixture literal (cm) ===")
    print("  A = Line(%.6f, %.6f) -> (%.6f, %.6f)" % tuple(fx[0]))
    print("  B = Line(%.6f, %.6f) -> (%.6f, %.6f)" % tuple(fx[1]))
    A, B = L.mkline(*fx[0]), L.mkline(*fx[1])
    Ar, Br = L.mkline(fx[0][2], fx[0][3], fx[0][0], fx[0][1]), \
        L.mkline(fx[1][2], fx[1][3], fx[1][0], fx[1][1])
    print("")
    print("  ASSERCOES (as 4 tem que passar):")
    print("   1. d(A,B) == d(B,A)                        (simetria da distancia)")
    print("   2. ov(A,B) == ov(B,A)                      (simetria do overlap)")
    print("   3. veredito de candidato(A,B) == (B,A)     (o que o CR-2F-B pede)")
    print("   4. as tres valem tambem com os endpoints invertidos")
    print("")
    print("  %-8s %11s %11s %9s %9s %9s %9s %8s" %
          ("estrat", "d(A,B) cm", "d(B,A) cm", "sim.d", "sim.ov", "cand AB",
           "cand BA", "PASS?"))
    rep["INV_PAIR_001"] = dict(fixture_cm=fx, results={})
    for st in G2.STRATEGIES:
        dist, ovl = G2.make_patch(st)
        res = {}
        for tag, (x, y) in (("dir", (A, B)), ("rev", (Ar, Br))):
            cx, cy = mod._line_geom_cache(x), mod._line_geom_cache(y)
            d1, d2 = dist(cx, cy), dist(cy, cx)
            o1, o2 = ovl(cx, cy)[0], ovl(cy, cx)[0]
            def cand(d, o, la, lb):
                if not (mod.MIN_WALL_THICKNESS_FT <= d <= mod.MAX_WALL_THICKNESS_FT):
                    return False
                if mod._closest_target_thickness_ft(d, L.load()["th"],
                                                    L.load()["tol"]) is None:
                    return False
                if o < mod.MIN_WALL_SEGMENT_ABS_FLOOR_FT:
                    return False
                sh = min(la, lb)
                return sh > 1e-9 and (o / sh) >= mod.MIN_WALL_SEGMENT_OVERLAP_RATIO
            la, lb = cx[3], cy[3]
            res[tag] = dict(d1=L.cm(d1), d2=L.cm(d2), sim_d=(d1 == d2),
                            o1=L.cm(o1), o2=L.cm(o2), sim_ov=(o1 == o2),
                            cand_ab=cand(d1, o1, la, lb),
                            cand_ba=cand(d2, o2, lb, la))
        r = res["dir"]
        ok = all(res[t]["sim_d"] and res[t]["sim_ov"] and
                 res[t]["cand_ab"] == res[t]["cand_ba"] for t in ("dir", "rev"))
        print("  %-8s %11.6f %11.6f %9s %9s %9s %9s %8s" %
              (st, r["d1"], r["d2"], "SIM" if r["sim_d"] else "NAO",
               "SIM" if r["sim_ov"] else "NAO",
               "sim" if r["cand_ab"] else "nao",
               "sim" if r["cand_ba"] else "nao", "PASS" if ok else "FAIL"))
        rep["INV_PAIR_001"]["results"][st] = dict(res, pass_=ok)

    # ================================================================ 002
    print("")
    print("=== INV-PAIR-002 - 2.868 linhas, %d permutacoes ===" % len(SEEDS))
    print("  ASSERCAO: o conjunto de pares candidatos, traduzido de volta")
    print("  para a IDENTIDADE das linhas, e' identico em todas as ordens.")
    print("")
    print("  %-8s %10s %s" % ("estrat", "baseline", "diferenca por seed"))
    rep["INV_PAIR_002"] = {}
    base = G2.candidates_all(frozen, G2.STRATEGIES, None, upper_only=True)
    bset = dict((st, set(frozenset((c["i"], c["j"])) for c in base[st]))
                for st in G2.STRATEGIES)
    del base
    gc.collect()
    diffs = dict((st, []) for st in G2.STRATEGIES)
    import random
    for sd in SEEDS:
        idx = list(range(len(frozen)))
        random.Random(sd).shuffle(idx)
        cur = G2.candidates_all([frozen[k] for k in idx], G2.STRATEGIES,
                                None, upper_only=True)
        for st in G2.STRATEGIES:
            s = set(frozenset((idx[c["i"]], idx[c["j"]])) for c in cur[st])
            diffs[st].append(len(bset[st] ^ s))
        del cur
        gc.collect()
    for st in G2.STRATEGIES:
        ok = all(d == 0 for d in diffs[st])
        print("  %-8s %10d %s   %s" % (st, len(bset[st]),
                                       " ".join("s%d=%d" % (sd, d)
                                                for sd, d in zip(SEEDS, diffs[st])),
                                       "PASS" if ok else "FAIL"))
        rep["INV_PAIR_002"][st] = dict(baseline=len(bset[st]),
                                       diffs=diffs[st], pass_=ok)

    print("")
    print("=== VEREDITO ===")
    for st in G2.STRATEGIES:
        a = rep["INV_PAIR_001"]["results"][st]["pass_"]
        b = rep["INV_PAIR_002"][st]["pass_"]
        print("  %-8s INV-PAIR-001=%s  INV-PAIR-002=%s" %
              (st, "PASS" if a else "FAIL", "PASS" if b else "FAIL"))
    G2.dump("out_g_invpair.json", rep)


if __name__ == "__main__":
    main()
