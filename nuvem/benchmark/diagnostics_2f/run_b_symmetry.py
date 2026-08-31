# -*- coding: utf-8 -*-
"""ETAPA 2F - itens G/H do pedido: SIMETRIA e TRANSITIVIDADE dos predicados.

Testa `f(A,B)` contra `f(B,A)` para todo predicado binario usado (a) no
agrupamento do merge e (b) na geracao de candidatos de `find_wall_pairs`,
sobre a geometria REAL do torre_easy_lo_r00_tgd - nao so' em caso sintetico.

O censo exaustivo O(n^2) sobre as 9.258 linhas cruas e' feito em duas fases:
  1. PRE-FILTRO vetorizado (numpy) com margem folgada, so' para ACHAR os
     pares que podem interessar - nunca para decidir nada;
  2. verificacao pelo CODIGO REAL do motor (`_are_parallel_cached`,
     `_distance_between_parallel_cached`, `_line_pair_overlap_ft_cached`),
     em ambas as direcoes.

    py -3 nuvem/benchmark/diagnostics_2f/run_b_symmetry.py
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402

PAR_TOL = 0.05  # _are_parallel_cached default


def geom_arrays(lines):
    p0 = np.array([[l.GetEndPoint(0).X, l.GetEndPoint(0).Y] for l in lines])
    p1 = np.array([[l.GetEndPoint(1).X, l.GetEndPoint(1).Y] for l in lines])
    d = p1 - p0
    ln = np.hypot(d[:, 0], d[:, 1])
    u = d / ln[:, None]
    mid = p0 + u * (ln[:, None] * 0.5)
    return p0, p1, u, ln, mid


def near_pairs(lines, perp_margin_ft, par_margin=0.06, chunk=400):
    """Pares (i<j) com |cross| < par_margin e perpendicular (em QUALQUER das
    duas direcoes) <= perp_margin_ft. Pre-filtro so' para reduzir o censo."""
    p0, p1, u, ln, mid = geom_arrays(lines)
    n = len(lines)
    out = []
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        cross = u[a:b, 0][:, None] * u[None, :, 1] - u[a:b, 1][:, None] * u[None, :, 0]
        ok = np.abs(cross) < par_margin
        dx = mid[a:b, 0][:, None] - p0[None, :, 0]
        dy = mid[a:b, 1][:, None] - p0[None, :, 1]
        perp_ij = np.abs(dx * u[None, :, 1] - dy * u[None, :, 0])
        dx2 = mid[None, :, 0] - p0[a:b, 0][:, None]
        dy2 = mid[None, :, 1] - p0[a:b, 1][:, None]
        perp_ji = np.abs(dx2 * u[a:b, 1][:, None] - dy2 * u[a:b, 0][:, None])
        ok &= (perp_ij <= perp_margin_ft) | (perp_ji <= perp_margin_ft)
        ii, jj = np.nonzero(ok)
        ii = ii + a
        keep = ii < jj
        out.append(np.stack([ii[keep], jj[keep]], axis=1))
    return np.concatenate(out) if out else np.zeros((0, 2), dtype=int)


def census(lines, pairs, tag, tolf, mod):
    """Simetria dos tres predicados do motor sobre `pairs`."""
    caches = {}

    def C(k):
        if k not in caches:
            caches[k] = mod._line_geom_cache(lines[k])
        return caches[k]

    res = dict(tag=tag, pairs=len(pairs), par_flip=0, dist_max_abs_diff_ft=0.0,
               dist_max_rel=0.0, compat_flip=0, ov_flip=0, ov_max_abs_diff_ft=0.0,
               examples_compat=[], examples_dist=[])
    for i, j in pairs:
        ci, cj = C(int(i)), C(int(j))
        pij = mod._are_parallel_cached(ci, cj)
        pji = mod._are_parallel_cached(cj, ci)
        if pij != pji:
            res["par_flip"] += 1
        if not pij:
            continue
        dij = mod._distance_between_parallel_cached(ci, cj)
        dji = mod._distance_between_parallel_cached(cj, ci)
        dd = abs(dij - dji)
        if dd > res["dist_max_abs_diff_ft"]:
            res["dist_max_abs_diff_ft"] = dd
        base = max(dij, dji, 1e-12)
        if dd / base > res["dist_max_rel"]:
            res["dist_max_rel"] = dd / base
        cij, cji = dij <= tolf, dji <= tolf
        if cij != cji:
            res["compat_flip"] += 1
            if len(res["examples_compat"]) < 12:
                res["examples_compat"].append(dict(
                    i=int(i), j=int(j),
                    d_ij_cm=round(L.cm(dij), 6), d_ji_cm=round(L.cm(dji), 6),
                    tol_cm=round(L.cm(tolf), 6)))
        oij = mod._line_pair_overlap_ft_cached(ci, cj)[0]
        oji = mod._line_pair_overlap_ft_cached(cj, ci)[0]
        od = abs(oij - oji)
        if od > res["ov_max_abs_diff_ft"]:
            res["ov_max_abs_diff_ft"] = od
        if od > 1e-9:
            res["ov_flip"] += 1
        if len(res["examples_dist"]) < 8 and dd > 1e-7:
            res["examples_dist"].append(dict(
                i=int(i), j=int(j), d_ij_cm=round(L.cm(dij), 6),
                d_ji_cm=round(L.cm(dji), 6), diff_cm=round(L.cm(dd), 6)))
    res["dist_max_abs_diff_cm"] = round(L.cm(res["dist_max_abs_diff_ft"]), 6)
    res["ov_max_abs_diff_cm"] = round(L.cm(res["ov_max_abs_diff_ft"]), 6)
    return res


def pairing_gate_flip(lines, mod):
    """Sobre as linhas JA' MESCLADAS: quantos pares MUDAM DE VEREDITO como
    candidato de find_wall_pairs se `i` e `j` trocarem de lugar."""
    S = L.load()
    th, tol = S["th"], S["tol"]
    n = len(lines)
    pairs = near_pairs(lines, mod.MAX_WALL_THICKNESS_FT * 1.05)
    caches = [mod._line_geom_cache(l) for l in lines]

    def verdict(a, b):
        ca, cb = caches[a], caches[b]
        if not mod._are_parallel_cached(ca, cb):
            return None
        d = mod._distance_between_parallel_cached(ca, cb)
        if not (mod.MIN_WALL_THICKNESS_FT <= d <= mod.MAX_WALL_THICKNESS_FT):
            return None
        mt = mod._closest_target_thickness_ft(d, th, tol)
        if mt is None:
            return None
        ov, l1, l2 = mod._line_pair_overlap_ft_cached(ca, cb)
        if ov < mod.MIN_WALL_SEGMENT_ABS_FLOOR_FT:
            return None
        sh = min(l1, l2)
        if sh < 1e-9:
            return None
        r = ov / sh
        if r < mod.MIN_WALL_SEGMENT_OVERLAP_RATIO:
            return None
        err = abs(d - mt)
        return dict(d=d, mt=mt, ov=ov, r=r, err=err,
                    rank=int(err / L.THICKNESS_RANK_BUCKET_FT))

    only_fwd, only_rev, both, rank_diff, ex = 0, 0, 0, 0, []
    for i, j in pairs:
        a, b = int(i), int(j)
        vf, vr = verdict(a, b), verdict(b, a)
        if vf and vr:
            both += 1
            if vf["rank"] != vr["rank"]:
                rank_diff += 1
                if len(ex) < 12:
                    ex.append(dict(i=a, j=b, rank_ij=vf["rank"], rank_ji=vr["rank"],
                                   d_ij_cm=round(L.cm(vf["d"]), 5),
                                   d_ji_cm=round(L.cm(vr["d"]), 5)))
        elif vf and not vr:
            only_fwd += 1
            if len(ex) < 12:
                ex.append(dict(i=a, j=b, kind="only_ij", d_ij_cm=round(L.cm(vf["d"]), 5),
                               d_ji_cm=round(L.cm(mod._distance_between_parallel_cached(
                                   caches[b], caches[a])), 5)))
        elif vr and not vf:
            only_rev += 1
            if len(ex) < 12:
                ex.append(dict(i=a, j=b, kind="only_ji",
                               d_ij_cm=round(L.cm(mod._distance_between_parallel_cached(
                                   caches[a], caches[b])), 5),
                               d_ji_cm=round(L.cm(vr["d"]), 5)))
    return dict(pairs_scanned=len(pairs), valid_both=both, only_ij=only_fwd,
                only_ji=only_rev, rank_differs=rank_diff, examples=ex)


def synthetic():
    """Casos sinteticos minimos de simetria (nao dependem do projeto)."""
    mod = L.load()["mod"]
    out = []

    def probe(name, a, b, tolf=None):
        ca, cb = mod._line_geom_cache(a), mod._line_geom_cache(b)
        dij = mod._distance_between_parallel_cached(ca, cb)
        dji = mod._distance_between_parallel_cached(cb, ca)
        oij = mod._line_pair_overlap_ft_cached(ca, cb)[0]
        oji = mod._line_pair_overlap_ft_cached(cb, ca)[0]
        out.append(dict(case=name,
                        parallel_ij=mod._are_parallel_cached(ca, cb),
                        parallel_ji=mod._are_parallel_cached(cb, ca),
                        d_ij_cm=round(L.cm(dij), 6), d_ji_cm=round(L.cm(dji), 6),
                        d_symmetric=abs(dij - dji) < 1e-12,
                        ov_ij_cm=round(L.cm(oij), 6), ov_ji_cm=round(L.cm(oji), 6),
                        ov_symmetric=abs(oij - oji) < 1e-12))

    probe("SYM-01 paralelas exatas",
          L.mkline(0, 0, 400, 0), L.mkline(0, 14, 400, 14))
    probe("SYM-02 paralelas exatas, comprimentos diferentes",
          L.mkline(0, 0, 1513, 0), L.mkline(500, 14, 924, 14))
    probe("SYM-03 quase-paralelas (0,5 grau)",
          L.mkline(0, 0, 400, 0), L.mkline(0, 14, 400, 14 + 400 * math.tan(math.radians(0.5))))
    probe("SYM-04 quase-paralelas (2,0 graus)",
          L.mkline(0, 0, 400, 0), L.mkline(0, 14, 400, 14 + 400 * math.tan(math.radians(2.0))))
    probe("SYM-05 quase-paralelas + comprimentos muito diferentes",
          L.mkline(0, 0, 1500, 0),
          L.mkline(700, 14, 800, 14 + 100 * math.tan(math.radians(2.0))))
    probe("SYM-06 endpoints invertidos (mesma geometria de SYM-01)",
          L.mkline(400, 0, 0, 0), L.mkline(400, 14, 0, 14))
    probe("SYM-07 sem sobreposicao no eixo",
          L.mkline(0, 0, 100, 0), L.mkline(300, 14, 400, 14))
    return out


def main():
    S = L.load()
    mod = S["mod"]
    rep = {}

    print("=== SINTETICOS ===")
    rep["synthetic"] = synthetic()
    for r in rep["synthetic"]:
        print("%-52s d(A,B)=%.6f d(B,A)=%.6f  sym=%s | ov(A,B)=%.6f ov(B,A)=%.6f sym=%s"
              % (r["case"], r["d_ij_cm"], r["d_ji_cm"], r["d_symmetric"],
                 r["ov_ij_cm"], r["ov_ji_cm"], r["ov_symmetric"]))

    print("")
    print("=== CENSO REAL: relacao do MERGE sobre as 9.258 linhas cruas ===")
    raw = S["lines"]
    tolf = mod.COLLINEAR_MATCH_TOLERANCE_FT
    pr = near_pairs(raw, tolf * 4.0)
    print("pares pre-filtrados: %d" % len(pr))
    sys.stdout.flush()
    rep["merge_relation"] = census(raw, pr, "merge(2mm)", tolf, mod)
    r = rep["merge_relation"]
    print("  paralelismo assimetrico : %d" % r["par_flip"])
    print("  |d(A,B)-d(B,A)| max     : %.6f cm" % r["dist_max_abs_diff_cm"])
    print("  compat(A,B) != compat(B,A): %d  <<< assimetria da relacao de cluster"
          % r["compat_flip"])
    for e in r["examples_compat"][:6]:
        print("     ex: i=%d j=%d  d(i,j)=%.6f cm  d(j,i)=%.6f cm  tol=%.6f cm"
              % (e["i"], e["j"], e["d_ij_cm"], e["d_ji_cm"], e["tol_cm"]))
    sys.stdout.flush()

    print("")
    print("=== CENSO REAL: predicados de find_wall_pairs sobre as 2.868 mescladas ===")
    merged = L.baseline_merged()
    print("linhas mescladas: %d" % len(merged))
    pr2 = near_pairs(merged, mod.MAX_WALL_THICKNESS_FT * 1.05)
    rep["pair_predicates"] = census(merged, pr2, "pairing", mod.MAX_WALL_THICKNESS_FT, mod)
    r2 = rep["pair_predicates"]
    print("pares pre-filtrados: %d" % len(pr2))
    print("  paralelismo assimetrico : %d" % r2["par_flip"])
    print("  |d(A,B)-d(B,A)| max     : %.6f cm" % r2["dist_max_abs_diff_cm"])
    print("  |ov(A,B)-ov(B,A)| max   : %.6f cm  (pares com diferenca: %d)"
          % (r2["ov_max_abs_diff_cm"], r2["ov_flip"]))
    sys.stdout.flush()

    print("")
    print("=== VEREDITO DE CANDIDATO: (i,j) contra (j,i) ===")
    rep["candidate_gate"] = pairing_gate_flip(merged, mod)
    g = rep["candidate_gate"]
    print("  pares varridos        : %d" % g["pairs_scanned"])
    print("  validos nas 2 direcoes: %d" % g["valid_both"])
    print("  validos SO' como (i,j): %d" % g["only_ij"])
    print("  validos SO' como (j,i): %d" % g["only_ji"])
    print("  rank de espessura difere entre as direcoes: %d" % g["rank_differs"])
    for e in g["examples"][:10]:
        print("     %s" % json.dumps(e, ensure_ascii=False))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_b_symmetry.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print("-> " + out)


if __name__ == "__main__":
    main()
