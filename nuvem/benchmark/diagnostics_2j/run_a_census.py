# -*- coding: utf-8 -*-
"""ETAPA 2J - CENSO DE ASSIMETRIA DA RELACAO (CR-2F-A).

SOMENTE LEITURA de `nuvem/core/**`. Mede, sobre o projeto real
`torre_easy_lo_r00_tgd` (9.258 segmentos de CAD), quantos pares tem o
VEREDITO de compatibilidade dependente da direcao:

  ANTES (relacao assimetrica, primitiva `_distance_between_parallel_cached`):
      compat(A,B) := d(A,B) <= tol
  DEPOIS (CR-2F-A, T2/MAX, `_symmetric_within_distance_cached`):
      compat(A,B) := max(d(A,B), d(B,A)) <= tol

As duas primitivas continuam existindo no motor (a antiga serve os
diagnosticos que nao criam geometria), entao o "antes" e o "depois" sao
medidos na MESMA execucao, sobre o MESMO conjunto de pares - nao ha
comparacao entre commits diferentes.

    python3 nuvem/benchmark/diagnostics_2j/run_a_census.py
"""
import json
import math
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "diagnostics_2f"))
import lib2f as L  # noqa: E402

PAR_TOL = 0.05          # mesma tolerancia de _are_parallel_cached
PREFILTER_CM = 5.0      # folga generosa sobre as tolerancias reais (0,2 e 2 cm)


def near_pairs(lines):
    """Pares (i, j), i<j, quase paralelos e proximos em ALGUMA direcao.
    Pre-filtro vetorizado: reduz 42,8 M pares a algumas centenas de
    milhares sem poder descartar nenhum par que qualquer uma das duas
    relacoes aceitaria (o corte usa o MINIMO das duas direcoes e uma folga
    25x maior que a maior tolerancia em jogo)."""
    P0 = np.array([[l.GetEndPoint(0).X, l.GetEndPoint(0).Y] for l in lines])
    P1 = np.array([[l.GetEndPoint(1).X, l.GetEndPoint(1).Y] for l in lines])
    V = P1 - P0
    LEN = np.hypot(V[:, 0], V[:, 1])
    D = V / LEN[:, None]
    M = P0 + D * (LEN[:, None] * 0.5)
    cut = PREFILTER_CM * L.load()["F"] / 100.0
    out = []
    for i in range(len(lines)):
        cr = np.abs(D[i, 0] * D[:, 1] - D[i, 1] * D[:, 0])
        ok = cr < PAR_TOL
        ok[:i + 1] = False
        if not ok.any():
            continue
        j = np.flatnonzero(ok)
        w = M[i] - P0[j]
        t = w[:, 0] * D[j, 0] + w[:, 1] * D[j, 1]
        pr = P0[j] + D[j] * t[:, None]
        dij = np.hypot(M[i, 0] - pr[:, 0], M[i, 1] - pr[:, 1])
        w2 = M[j] - P0[i]
        t2 = w2[:, 0] * D[i, 0] + w2[:, 1] * D[i, 1]
        pr2 = P0[i] + D[i] * t2[:, None]
        dji = np.hypot(M[j, 0] - pr2[:, 0], M[j, 1] - pr2[:, 1])
        keep = np.minimum(dij, dji) <= cut
        for k in np.flatnonzero(keep):
            out.append((i, int(j[k])))
    return out


def census_merge(mod, lines, pairs, tol):
    caches = [mod._line_geom_cache(l) for l in lines]
    antes = depois = 0
    pior = 0.0
    pior_par = None
    for i, j in pairs:
        ci, cj = caches[i], caches[j]
        if not mod._are_parallel_cached(ci, cj):
            continue
        dij = mod._distance_between_parallel_cached(ci, cj)
        dji = mod._distance_between_parallel_cached(cj, ci)
        if abs(dij - dji) > pior:
            pior, pior_par = abs(dij - dji), (i, j, dij, dji)
        if (dij <= tol) != (dji <= tol):
            antes += 1
        # a MESMA funcao de producao, com os argumentos LITERALMENTE trocados
        if (mod._symmetric_within_distance_cached(ci, cj, tol) !=
                mod._symmetric_within_distance_cached(cj, ci, tol)):
            depois += 1
    return antes, depois, pior, pior_par


def census_dedup(mod, walls):
    """Mesma medicao sobre a relacao de duplicidade, nas paredes ACEITAS."""
    tol = mod.DUPLICATE_AXIS_TOLERANCE_FT
    thk = mod.WALL_THICKNESS_MATCH_TOLERANCE_FT

    def base_ok(w1, w2):
        return (abs(w1[1] - w2[1]) <= thk and
                mod.are_lines_parallel(w1[0], w2[0]) and
                mod.lines_overlap_enough(w1[0], w2[0]))

    antes = depois = 0
    total = 0
    for a in range(len(walls)):
        for b in range(a + 1, len(walls)):
            w1, w2 = walls[a], walls[b]
            if not base_ok(w1, w2):
                continue
            total += 1
            d12 = mod.get_distance_between_parallel_lines(w1[0], w2[0])
            d21 = mod.get_distance_between_parallel_lines(w2[0], w1[0])
            if (d12 <= tol) != (d21 <= tol):
                antes += 1
            if (mod.symmetric_lines_within_distance(w1[0], w2[0], tol) !=
                    mod.symmetric_lines_within_distance(w2[0], w1[0], tol)):
                depois += 1
    return antes, depois, total


def main():
    S = L.load()
    mod = S["mod"]
    lines = S["lines"]
    tol = mod.COLLINEAR_MATCH_TOLERANCE_FT

    print("segmentos de CAD           : %d" % len(lines))
    print("COLLINEAR_MATCH_TOLERANCE  : %.4f cm" % L.cm(tol))
    print("DUPLICATE_AXIS_TOLERANCE   : %.4f cm" % L.cm(mod.DUPLICATE_AXIS_TOLERANCE_FT))
    print("")

    t0 = time.time()
    pairs = near_pairs(lines)
    print("pares proximos avaliados   : %d   (%.1fs)" % (len(pairs), time.time() - t0))

    antes, depois, pior, pior_par = census_merge(mod, lines, pairs, tol)
    print("")
    print("=== MERGE (merge_collinear_fragments / bridge) ===")
    print("  vereditos dependentes da direcao ANTES  : %d" % antes)
    print("  vereditos dependentes da direcao DEPOIS : %d" % depois)
    print("  pior |d(A,B) - d(B,A)|                  : %.4f cm" % L.cm(pior))
    if pior_par:
        i, j, dij, dji = pior_par
        print("  pior par: linhas %d x %d  ->  d=%.4f cm  /  d=%.4f cm"
              % (i, j, L.cm(dij), L.cm(dji)))

    frozen = L.baseline_merged()
    walls, _u, _d, _t = L.run_pairs(frozen)
    a2, d2, tot = census_dedup(mod, walls)
    print("")
    print("=== deduplicate_walls (%d paredes aceitas, %d pares candidatos) ===" % (len(walls), tot))
    print("  vereditos dependentes da direcao ANTES  : %d" % a2)
    print("  vereditos dependentes da direcao DEPOIS : %d" % d2)

    rep = dict(segments=len(lines), near_pairs=len(pairs),
               merge_asym_before=antes, merge_asym_after=depois,
               merge_worst_delta_cm=L.cm(pior),
               dedup_candidates=tot, dedup_asym_before=a2, dedup_asym_after=d2,
               accepted_walls=len(walls))
    with open(os.path.join(_HERE, "out_a_census.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print("")
    print("-> out_a_census.json")
    return 0 if (depois == 0 and d2 == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
