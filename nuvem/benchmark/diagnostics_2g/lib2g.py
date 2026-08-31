# -*- coding: utf-8 -*-
"""ETAPA 2G - laboratorio de SIMETRIA dos predicados de `find_wall_pairs`
(CR-2F-B / PAIR_PREDICATE_ASYMMETRY).

SOMENTE LEITURA de `nuvem/core/**`. Nenhum arquivo do motor e' alterado.
As estrategias candidatas sao avaliadas de duas formas COMPLEMENTARES:

  1. camada NumPy vetorizada -> censo exaustivo dos 4.111.278 pares das
     2.868 linhas mescladas, para todas as estrategias de uma vez;
  2. camada de MONKEYPATCH em memoria -> injeta a estrategia dentro do
     `find_wall_pairs` REAL (via `find_wall_pairs.__globals__`, que e' o
     dict do modulo `core.engine.wall_pairing`), para medir o DOWNSTREAM
     real (paredes, cobertura, aberturas) sem reimplementar o pipeline.

A camada 1 e' VALIDADA contra a camada 2 (estrategia `cur`) em
`run_a_census.py`: os 589 candidatos do baseline tem que sair identicos,
campo a campo, ou o resto do estudo nao vale.

Estrategias (nomes usados em todos os relatorios desta etapa):

  cur     assimetrica atual (baseline)              - so' para comparacao
  A_mean  media das duas direcoes
  B_min   minimo das duas direcoes
  C_max   maximo das duas direcoes
  D_long  a linha MAIS LONGA e' a referencia
  E_bis   formulacao intrinsecamente simetrica (normal da BISSETRIZ)
  E_ovl   E_bis restrita a' sobreposicao mutua (folga media medida so'
          onde as duas faces realmente se encaram)
  F_lex   orientacao canonica por chave lexicografica das coordenadas
"""
import hashlib
import json
import math
import os
import sys

# O processo desta maquina tem ~240 MB. O OpenBLAS reserva buffers POR
# THREAD na primeira chamada de BLAS e sozinho estoura o teto quando o
# motor (com os dubles do Revit) ja' esta' carregado - trava medida em
# 2026-08-31 no run_c. Uma thread basta: nada aqui e' algebra pesada.
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_2F = os.path.abspath(os.path.join(_HERE, "..", "diagnostics_2f"))
if _2F not in sys.path:
    sys.path.insert(0, _2F)

import lib2f as L  # noqa: E402

STRATEGIES = ("cur", "A_mean", "B_min", "C_max", "D_long", "E_bis", "E_ovl", "F_lex")
SYMMETRIC = ("A_mean", "B_min", "C_max", "D_long", "E_bis", "E_ovl", "F_lex")

PAR_TOL = 0.05          # _are_parallel_cached
BLOCK = 64              # linhas por bloco (limite de ~240 MB do processo)
COLS = 512              # colunas por bloco


def out_path(name):
    return os.path.join(_HERE, name)


def dump(name, obj):
    p = out_path(name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    print("-> " + p)


# ==========================================================================
# CAMADA 1 - NumPy
# ==========================================================================
def arrays(lines):
    """(P0, P1, D, Lg, M, N) em pes, como arrays (n,2)/(n,) - os MESMOS
    campos que `_line_geom_cache` do motor produz (validado em run_a)."""
    mod = L.load()["mod"]
    n = len(lines)
    P0 = np.empty((n, 2))
    P1 = np.empty((n, 2))
    for k, ln in enumerate(lines):
        c = mod._line_geom_cache(ln)
        P0[k] = (c[0].X, c[0].Y)
        P1[k] = (c[1].X, c[1].Y)
    V = P1 - P0
    Lg = np.hypot(V[:, 0], V[:, 1])
    D = V / Lg[:, None]
    M = P0 + D * (Lg[:, None] * 0.5)
    N = np.stack([-D[:, 1], D[:, 0]], axis=1)
    return P0, P1, D, Lg, M, N


def lexkey(P0, P1):
    """Chave canonica por COORDENADA (ponta lexicograficamente menor
    primeiro) - mesma ideia de lib2f.canon. Usada so' pela estrategia
    F_lex."""
    swap = (P0[:, 0] > P1[:, 0]) | ((P0[:, 0] == P1[:, 0]) & (P0[:, 1] > P1[:, 1]))
    key = np.empty((len(P0), 4))
    key[:, 0] = np.where(swap, P1[:, 0], P0[:, 0])
    key[:, 1] = np.where(swap, P1[:, 1], P0[:, 1])
    key[:, 2] = np.where(swap, P0[:, 0], P1[:, 0])
    key[:, 3] = np.where(swap, P0[:, 1], P1[:, 1])
    return key


def _lex_less(ki, kj):
    """ki < kj lexicograficamente, com broadcast."""
    lt = ki < kj
    eq = ki == kj
    out = lt[..., 0].copy()
    run = eq[..., 0].copy()
    for c in (1, 2, 3):
        out |= run & lt[..., c]
        run &= eq[..., c]
    return out


def pair_block(G, i0, i1, K=None, j0=0, j1=None):
    """Todos os predicados para o bloco de linhas [i0,i1) contra [j0,j1).

    Devolve dict de matrizes (m, q). Nao filtra nada. O bloco e' 2-D de
    proposito: o processo desta maquina tem ~240 MB, entao materializar a
    matriz n x n inteira (66 MB por predicado) nao cabe."""
    P0, P1, D, Lg, M, N = G
    n = len(Lg)
    j1 = n if j1 is None else j1
    m, q = i1 - i0, j1 - j0
    Di, Dj = D[i0:i1, None, :], D[None, j0:j1, :]
    Ni, Nj = N[i0:i1, None, :], N[None, j0:j1, :]
    Mi, Mj = M[i0:i1, None, :], M[None, j0:j1, :]
    Li, Lj = np.broadcast_to(Lg[i0:i1, None], (m, q)), np.broadcast_to(Lg[None, j0:j1], (m, q))

    cross = Di[..., 0] * Dj[..., 1] - Di[..., 1] * Dj[..., 0]
    par = np.abs(cross) < PAR_TOL

    Delta = Mi - Mj
    d12 = np.abs(Nj[..., 0] * Delta[..., 0] + Nj[..., 1] * Delta[..., 1])
    d21 = np.abs(Ni[..., 0] * Delta[..., 0] + Ni[..., 1] * Delta[..., 1])

    # --- bissetriz (direcao simetrica; o sentido de j e' alinhado ao de i)
    dot = Di[..., 0] * Dj[..., 0] + Di[..., 1] * Dj[..., 1]
    sgn = np.where(dot >= 0.0, 1.0, -1.0)
    Bv = Di + Dj * sgn[..., None]
    Bn = np.hypot(Bv[..., 0], Bv[..., 1])
    degen = Bn < 1e-9
    B = Bv / np.where(degen, 1.0, Bn)[..., None]
    B = np.where(degen[..., None], np.broadcast_to(Di, B.shape), B)
    Nb = np.stack([-B[..., 1], B[..., 0]], axis=-1)
    d_bis = np.abs(Nb[..., 0] * Delta[..., 0] + Nb[..., 1] * Delta[..., 1])

    # --- projecoes na bissetriz, a partir da origem simetrica o=(Mi+Mj)/2
    O = (Mi + Mj) * 0.5

    def proj(Pk, is_i):
        P = Pk[i0:i1, None, :] if is_i else Pk[None, j0:j1, :]
        W = P - O
        t = W[..., 0] * B[..., 0] + W[..., 1] * B[..., 1]
        s = W[..., 0] * Nb[..., 0] + W[..., 1] * Nb[..., 1]
        return t, s

    ti0, si0 = proj(P0, True)
    ti1, si1 = proj(P1, True)
    tj0, sj0 = proj(P0, False)
    tj1, sj1 = proj(P1, False)
    lo = np.maximum(np.minimum(ti0, ti1), np.minimum(tj0, tj1))
    hi = np.minimum(np.maximum(ti0, ti1), np.maximum(tj0, tj1))
    ov_bis = np.maximum(0.0, hi - lo)

    def s_at(t0, s0, t1, s1, t):
        dt = t1 - t0
        flat = np.abs(dt) < 1e-12
        val = s0 + (s1 - s0) * (t - t0) / np.where(flat, 1.0, dt)
        return np.where(flat, s0, val)

    g_lo = np.abs(s_at(ti0, si0, ti1, si1, lo) - s_at(tj0, sj0, tj1, sj1, lo))
    g_hi = np.abs(s_at(ti0, si0, ti1, si1, hi) - s_at(tj0, sj0, tj1, sj1, hi))
    d_ovl = np.where(ov_bis > 1e-12, (g_lo + g_hi) * 0.5, d_bis)

    # --- sobreposicao com eixo em i (atual) e com eixo em j (espelhada)
    def ov_axis(axis_is_i):
        if axis_is_i:
            A0, Dax, Lax = P0[i0:i1, None, :], Di, Li
            Q0, Q1 = P0[None, j0:j1, :], P1[None, j0:j1, :]
        else:
            A0, Dax, Lax = P0[None, j0:j1, :], Dj, Lj
            Q0, Q1 = P0[i0:i1, None, :], P1[i0:i1, None, :]
        t0 = (Q0[..., 0] - A0[..., 0]) * Dax[..., 0] + (Q0[..., 1] - A0[..., 1]) * Dax[..., 1]
        t1 = (Q1[..., 0] - A0[..., 0]) * Dax[..., 0] + (Q1[..., 1] - A0[..., 1]) * Dax[..., 1]
        tlo = np.minimum(t0, t1)
        thi = np.maximum(t0, t1)
        return np.maximum(0.0, np.minimum(Lax, thi) - np.maximum(0.0, tlo))

    ov12 = ov_axis(True)
    ov21 = ov_axis(False)

    i_longer = Li > Lj
    j_longer = Lj > Li
    d_long = np.where(i_longer, d21, np.where(j_longer, d12, (d12 + d21) * 0.5))
    ov_long = np.where(i_longer, ov12, np.where(j_longer, ov21, (ov12 + ov21) * 0.5))

    if K is None:
        K = lexkey(P0, P1)
    i_first = _lex_less(K[i0:i1, None, :], K[None, j0:j1, :])
    d_lex = np.where(i_first, d12, d21)
    ov_lex = np.where(i_first, ov12, ov21)

    out = {"par": par, "cross": cross, "d12": d12, "d21": d21,
           "ov12": ov12, "ov21": ov21, "Li": Li, "Lj": Lj,
           "tie_len": ~(i_longer | j_longer)}
    out["d_cur"] = d12
    out["d_A_mean"] = (d12 + d21) * 0.5
    out["d_B_min"] = np.minimum(d12, d21)
    out["d_C_max"] = np.maximum(d12, d21)
    out["d_D_long"] = d_long
    out["d_E_bis"] = d_bis
    out["d_E_ovl"] = d_ovl
    out["d_F_lex"] = d_lex
    out["ov_cur"] = ov12
    out["ov_A_mean"] = (ov12 + ov21) * 0.5
    out["ov_B_min"] = np.minimum(ov12, ov21)
    out["ov_C_max"] = np.maximum(ov12, ov21)
    out["ov_D_long"] = ov_long
    out["ov_E_bis"] = ov_bis
    out["ov_E_ovl"] = ov_bis
    out["ov_F_lex"] = ov_lex
    return out


def _consts():
    S = L.load()
    mod = S["mod"]
    from core.engine.tolerances import THICKNESS_RANK_BUCKET_FT as BUCK
    return dict(th=np.array(sorted(S["th"])), tol=S["tol"],
                MINW=mod.MIN_WALL_THICKNESS_FT, MAXW=mod.MAX_WALL_THICKNESS_FT,
                FLOOR=mod.MIN_WALL_SEGMENT_ABS_FLOOR_FT,
                RATIO=mod.MIN_WALL_SEGMENT_OVERLAP_RATIO, BUCK=BUCK)


def candidates_all(lines, strats, G=None, upper_only=True):
    """Enumera os candidatos de VARIAS estrategias numa unica varredura,
    replicando a MESMA cadeia de filtros de find_wall_pairs.

    upper_only=True  -> so' i<j (a varredura real);
    upper_only=False -> matriz inteira (para medir a assimetria)."""
    C = _consts()
    G = arrays(lines) if G is None else G
    n = len(G[3])
    K = lexkey(G[0], G[1])
    out = dict((st, []) for st in strats)
    for i0 in range(0, n, BLOCK):
        i1 = min(n, i0 + BLOCK)
        for j0 in range(0, n, COLS):
            j1 = min(n, j0 + COLS)
            if upper_only and j1 <= i0 + 1:
                continue
            blk = pair_block(G, i0, i1, K, j0, j1)
            ii = np.arange(i0, i1)[:, None]
            jj = np.arange(j0, j1)[None, :]
            side = (jj > ii) if upper_only else (jj != ii)
            shorter = np.minimum(blk["Li"], blk["Lj"])
            base = blk["par"] & side & (shorter >= 1e-9)
            for st in strats:
                d = blk["d_" + st]
                ov = blk["ov_" + st]
                ok = base & (d >= C["MINW"]) & (d <= C["MAXW"]) & (ov >= C["FLOOR"])
                ratio = ov / np.maximum(shorter, 1e-30)
                ok &= ratio >= C["RATIO"]
                diff = np.abs(d[..., None] - C["th"][None, None, :])
                best = np.argmin(diff, axis=-1)
                ok &= np.take_along_axis(diff, best[..., None], axis=-1)[..., 0] <= C["tol"]
                for a, b in np.argwhere(ok):
                    dd = float(d[a, b])
                    mt = float(C["th"][best[a, b]])
                    err = abs(dd - mt)
                    out[st].append(dict(i=int(i0 + a), j=int(j0 + b), d=dd, mt=mt,
                                        ov=float(ov[a, b]), r=float(ratio[a, b]),
                                        err=err, rank=int(err / C["BUCK"])))
    return out


def candidates_np(lines, strat, G=None, upper_only=True):
    return candidates_all(lines, (strat,), G, upper_only)[strat]


def cand_pairset(cands):
    return set(frozenset((c["i"], c["j"])) for c in cands)


def pairset_fp(pairs):
    blob = json.dumps(sorted(tuple(sorted(p)) for p in pairs), separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


# ==========================================================================
# CAMADA 2 - MONKEYPATCH no motor real (aritmetica em float puro; nada de
# NumPy aqui - estas funcoes rodam milhoes de vezes dentro do laco O(n^2))
# ==========================================================================
def _d_dir_xy(mx, my, nx, ny, ox, oy):
    return abs(nx * (mx - ox) + ny * (my - oy))


def _cur_dist(c1, c2):
    m1 = c1[4]
    d2 = c2[2]
    m2 = c2[4]
    return _d_dir_xy(m1.X, m1.Y, -d2.Y, d2.X, m2.X, m2.Y)


def _cur_ov(c1, c2):
    p0, _p1, d, l1, _m = c1
    q0, q1, _d2, l2, _m2 = c2
    dx, dy = d.X, d.Y
    t0 = (q0.X - p0.X) * dx + (q0.Y - p0.Y) * dy
    t1 = (q1.X - p0.X) * dx + (q1.Y - p0.Y) * dy
    if t0 > t1:
        t0, t1 = t1, t0
    hi = l1 if t1 > l1 else t1
    lo = 0.0 if t0 < 0.0 else t0
    return (hi - lo if hi > lo else 0.0), l1, l2


def _bis(c1, c2):
    """(bx, by, nbx, nby, ox, oy) - referencial simetrico do par."""
    d1, d2 = c1[2], c2[2]
    s = 1.0 if (d1.X * d2.X + d1.Y * d2.Y) >= 0.0 else -1.0
    bx = d1.X + d2.X * s
    by = d1.Y + d2.Y * s
    nb = math.hypot(bx, by)
    if nb < 1e-9:
        bx, by = d1.X, d1.Y
    else:
        bx, by = bx / nb, by / nb
    m1, m2 = c1[4], c2[4]
    return bx, by, -by, bx, (m1.X + m2.X) * 0.5, (m1.Y + m2.Y) * 0.5


def make_patch(strat):
    """Devolve (dist_fn, overlap_fn) com a MESMA assinatura do motor."""
    def dist(cache1, cache2):
        if strat == "cur":
            return _cur_dist(cache1, cache2)
        d12 = _cur_dist(cache1, cache2)
        d21 = _cur_dist(cache2, cache1)
        if strat == "A_mean":
            return (d12 + d21) * 0.5
        if strat == "B_min":
            return d12 if d12 < d21 else d21
        if strat == "C_max":
            return d12 if d12 > d21 else d21
        if strat == "D_long":
            l1, l2 = cache1[3], cache2[3]
            if l1 > l2:
                return d21
            if l2 > l1:
                return d12
            return (d12 + d21) * 0.5
        if strat == "F_lex":
            return d12 if _lexk(cache1) < _lexk(cache2) else d21
        bx, by, nx, ny, ox, oy = _bis(cache1, cache2)
        m1, m2 = cache1[4], cache2[4]
        d_bis = abs(nx * (m1.X - m2.X) + ny * (m1.Y - m2.Y))
        if strat == "E_bis":
            return d_bis
        if strat == "E_ovl":
            def ts(p):
                wx, wy = p.X - ox, p.Y - oy
                return bx * wx + by * wy, nx * wx + ny * wy
            ti0, si0 = ts(cache1[0])
            ti1, si1 = ts(cache1[1])
            tj0, sj0 = ts(cache2[0])
            tj1, sj1 = ts(cache2[1])
            lo = max(min(ti0, ti1), min(tj0, tj1))
            hi = min(max(ti0, ti1), max(tj0, tj1))
            if hi - lo <= 1e-12:
                return d_bis
            def sa(t0, s0, t1, s1, t):
                dt = t1 - t0
                return s0 if abs(dt) < 1e-12 else s0 + (s1 - s0) * (t - t0) / dt
            g0 = abs(sa(ti0, si0, ti1, si1, lo) - sa(tj0, sj0, tj1, sj1, lo))
            g1 = abs(sa(ti0, si0, ti1, si1, hi) - sa(tj0, sj0, tj1, sj1, hi))
            return (g0 + g1) * 0.5
        raise ValueError(strat)

    def overlap(cache1, cache2):
        if strat == "cur":
            return _cur_ov(cache1, cache2)
        l1, l2 = cache1[3], cache2[3]
        o12 = _cur_ov(cache1, cache2)[0]
        o21 = _cur_ov(cache2, cache1)[0]
        if strat == "A_mean":
            return (o12 + o21) * 0.5, l1, l2
        if strat == "B_min":
            return (o12 if o12 < o21 else o21), l1, l2
        if strat == "C_max":
            return (o12 if o12 > o21 else o21), l1, l2
        if strat == "D_long":
            v = o12 if l1 > l2 else (o21 if l2 > l1 else (o12 + o21) * 0.5)
            return v, l1, l2
        if strat == "F_lex":
            return (o12 if _lexk(cache1) < _lexk(cache2) else o21), l1, l2
        bx, by, _nx, _ny, ox, oy = _bis(cache1, cache2)

        def rng(c):
            a = bx * (c[0].X - ox) + by * (c[0].Y - oy)
            z = bx * (c[1].X - ox) + by * (c[1].Y - oy)
            return (a, z) if a <= z else (z, a)
        ai, zi = rng(cache1)
        aj, zj = rng(cache2)
        v = min(zi, zj) - max(ai, aj)
        return (v if v > 0.0 else 0.0), l1, l2

    return dist, overlap


def _lexk(c):
    a = (c[0].X, c[0].Y)
    b = (c[1].X, c[1].Y)
    return (a, b) if a <= b else (b, a)


class patched(object):
    """`with patched('E_bis'): ...` troca os dois predicados DENTRO do
    `find_wall_pairs` real, e desfaz ao sair."""
    NAMES = ("_distance_between_parallel_cached", "_line_pair_overlap_ft_cached")

    def __init__(self, strat):
        self.strat = strat
        self.g = L.load()["mod"].find_wall_pairs.__globals__
        self.old = {}

    def __enter__(self):
        if self.strat != "cur":
            d, o = make_patch(self.strat)
            for nm, fn in zip(self.NAMES, (d, o)):
                self.old[nm] = self.g[nm]
                self.g[nm] = fn
        return self

    def __exit__(self, *a):
        for nm, fn in self.old.items():
            self.g[nm] = fn
        self.old.clear()
        return False


# ==========================================================================
# MOVIMENTO RIGIDO (invariancia a rotacao / translacao / sentido)
# ==========================================================================
def rigid(lines, deg=0.0, dx_cm=0.0, dy_cm=0.0, flip=None):
    """Recria as linhas rotacionadas/transladadas (coordenadas em cm).
    `flip[k]` inverte o SENTIDO (endpoints) da linha k."""
    th = math.radians(deg)
    co, si = math.cos(th), math.sin(th)
    out = []
    for k, ln in enumerate(lines):
        p0, p1 = ln.GetEndPoint(0), ln.GetEndPoint(1)
        pts = [(L.cm(p0.X), L.cm(p0.Y)), (L.cm(p1.X), L.cm(p1.Y))]
        if flip is not None and flip[k]:
            pts.reverse()
        r = [(x * co - y * si + dx_cm, x * si + y * co + dy_cm) for x, y in pts]
        out.append(L.mkline(r[0][0], r[0][1], r[1][0], r[1][1]))
    return out
