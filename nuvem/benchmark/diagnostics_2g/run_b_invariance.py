# -*- coding: utf-8 -*-
"""ETAPA 2G - item 3: INVARIANCIA do CONJUNTO DE CANDIDATOS, separada de
DETERMINISMO.

O alvo do pedido: "mesmo conjunto GEOMETRICO de candidatos para a mesma
geometria, independentemente de ordem i/j, direcao dos endpoints, ordem da
lista, rotacao e translacao".

Cada eixo e' medido separadamente, sobre as 2.868 linhas congeladas, para
as 8 estrategias. A comparacao e' sempre pelo conjunto de pares de LINHAS
(identidade da linha, nao coordenada) - a unica nocao que sobrevive a uma
rotacao.

Controles obrigatorios:
  - IDENT: o mesmo transform com angulo/deslocamento ZERO, para separar o
    ruido do ida-e-volta pes->cm->pes do efeito do proprio movimento;
  - MARGEM: para cada par que entra/sai, a distancia ate' a fronteira de
    decisao mais proxima. Fronteira ~0 => ruido de ponto flutuante;
    fronteira grande => assimetria ESTRUTURAL (causa diferente).
  - a ordem i/j ja' foi medida em run_a (censo nas duas ordens).

    py -3 nuvem/benchmark/diagnostics_2g/run_b_invariance.py
"""
import gc
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2g as G2  # noqa: E402
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def margins(cands):
    """Para cada par candidato, quanto a grandeza teria que se mover para o
    veredito VIRAR. Duas escalas separadas (nao somaveis):
      dist_cm  - fronteiras que vivem na distancia (MIN/MAX de espessura e
                 a janela +/- tolerancia) e na sobreposicao absoluta;
      ratio    - a fronteira MIN_WALL_SEGMENT_OVERLAP_RATIO (adimensional).
    Margem ~0 => o par estava EM CIMA da fronteira: virar e' ruido de ponto
    flutuante, nao assimetria."""
    C = G2._consts()
    out = {}
    for c in cands:
        dm = min(c["d"] - C["MINW"], C["MAXW"] - c["d"],
                 C["tol"] - abs(c["d"] - c["mt"]), c["ov"] - C["FLOOR"])
        out[frozenset((c["i"], c["j"]))] = (L.cm(dm), c["r"] - C["RATIO"])
    return out


def sets_for(lines, perm=None):
    allc = G2.candidates_all(lines, G2.STRATEGIES, None, upper_only=True)
    sets, mrg = {}, {}
    for st, cs in allc.items():
        if perm is None:
            sets[st] = set(frozenset((c["i"], c["j"])) for c in cs)
            mrg[st] = margins(cs)
        else:
            for c in cs:
                c["i"], c["j"] = perm[c["i"]], perm[c["j"]]
            sets[st] = set(frozenset((c["i"], c["j"])) for c in cs)
            mrg[st] = margins(cs)
    del allc
    gc.collect()
    return sets, mrg


def _worst(diff, bmrg, cmrg, st):
    dm, rm = 0.0, 0.0
    for p in diff:
        v = bmrg[st].get(p) or cmrg[st].get(p)
        if v:
            dm = max(dm, v[0])
            rm = max(rm, v[1])
    return dm, rm


def cmp_row(tag, base, bmrg, cur, cmrg, rep, bucket, show_margin=False):
    line = "  %-22s" % tag
    row = {"tag": tag, "per_strategy": {}}
    ml = "  %-22s" % ""
    for st in G2.STRATEGIES:
        diff = base[st] ^ cur[st]
        dm, rm = _worst(diff, bmrg, cmrg, st)
        line += " %s=%-3d" % (st, len(diff))
        ml += " %s=%-3.3g" % (st, dm)
        row["per_strategy"][st] = dict(n_diff=len(diff), pior_margem_cm=dm,
                                       pior_margem_ratio=rm)
    print(line)
    if show_margin:
        print(ml + "   <- pior margem em cm dos pares que viraram")
    rep.setdefault(bucket, []).append(row)


def main():
    L.load()
    frozen = L.baseline_merged()
    n = len(frozen)
    rep = {"n_lines": n, "seeds": SEEDS}
    print("2.868 linhas congeladas; diferenca simetrica do conjunto de pares")
    print("(0 = invariante). Coluna por estrategia.")
    t0 = time.time()
    base, bmrg = sets_for(frozen)
    print("")
    print("baseline: " + "  ".join("%s=%d" % (st, len(base[st])) for st in G2.STRATEGIES))
    rep["baseline_sizes"] = dict((st, len(base[st])) for st in G2.STRATEGIES)

    def run(tag, bucket, lines, perm=None, show_margin=False):
        cur, cmrg = sets_for(lines, perm)
        cmp_row(tag, base, bmrg, cur, cmrg, rep, bucket, show_margin)
        del cur, cmrg, lines
        gc.collect()

    print("")
    print("=== A. ORDEM DA LISTA (embaralhar as 2.868) ===")
    for sd in SEEDS:
        idx = list(range(n))
        random.Random(sd).shuffle(idx)
        run("shuffle s%d" % sd, "ordem_lista", [frozen[k] for k in idx], idx)

    print("")
    print("=== B. DIRECAO DOS ENDPOINTS (inverter p0/p1) ===")
    run("flip TODAS", "endpoints", G2.rigid(frozen, flip=[True] * n))
    for sd in (7, 99):
        fl = [random.Random(sd).random() < 0.5 for _ in range(n)]
        run("flip 50%% s%d" % sd, "endpoints", G2.rigid(frozen, flip=fl))

    print("")
    print("=== C. CONTROLE (transform IDENTIDADE - so' o ida-e-volta ft->cm->ft) ===")
    run("IDENT", "controle", G2.rigid(frozen))

    print("")
    print("=== D. ROTACAO ===")
    for deg in (0.5, 37.0, 90.0, 180.0):
        run("rot %.1f deg" % deg, "rotacao", G2.rigid(frozen, deg=deg), None, True)

    print("")
    print("=== E. TRANSLACAO ===")
    for dx, dy, tag in ((100.0, -250.0, "1 m"),
                        (12345.678, -9876.543, "~120 m"),
                        (1e6, 1e6, "10 km")):
        run("transl %s" % tag, "translacao",
            G2.rigid(frozen, dx_cm=dx, dy_cm=dy), None, True)

    print("")
    print("=== F. COMBINADO (rot 37 + transl 120 m + flip 50% + shuffle) ===")
    idx = list(range(n))
    random.Random(5).shuffle(idx)
    fl = [random.Random(11).random() < 0.5 for _ in range(n)]
    moved = G2.rigid(frozen, deg=37.0, dx_cm=12345.678, dy_cm=-9876.543, flip=fl)
    moved = [moved[k] for k in idx]
    run("combinado", "combinado", moved, idx, True)

    print("")
    print("(%.1fs)" % (time.time() - t0))
    G2.dump("out_b_invariance.json", rep)


if __name__ == "__main__":
    main()
