# -*- coding: utf-8 -*-
"""ETAPA 2F - laboratorio de INVARIANCIA A' ORDEM. SOMENTE LEITURA de
`nuvem/core/**` (nenhuma funcao do motor e' reimplementada aqui: todas sao
importadas ao vivo via `solver_bridge.engine()`).

O que esta biblioteca oferece:
  - `load()`            estado congelado do torre_easy_lo_r00_tgd
  - `canon()`/`fp()`    fingerprint GEOMETRICO canonico (independente de
                        ordem da lista E do sentido de cada linha)
  - `run_merge()`       merge_collinear_fragments sobre uma ordem qualquer
  - `raw_clusters()`    so' a passada 1 (agrupamento cru), replicada com as
                        MESMAS funcoes do motor, para poder inspecionar os
                        clusters (o motor nao os expoe)
  - `build_candidates()` varredura O(n^2) identica a' de find_wall_pairs
  - `run_pairs()`       find_wall_pairs REAL sobre uma lista de linhas
  - `full_pipeline()`   merge congelado -> pares -> dedup -> extensao ->
                        grafo -> aberturas (mesma ordem de
                        wall_modeling_bridge.run_wall_modeling)

NAO introduz nada no runtime do plugin.
"""
import hashlib
import json
import math
import os
import random
import sys
import time
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "nuvem") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "nuvem"))

from benchmark import solver_bridge, wall_modeling_bridge as wmb  # noqa: E402
from core.engine.tolerances import THICKNESS_RANK_BUCKET_FT  # noqa: E402

BASE = os.path.join(_ROOT, "nuvem", "benchmark", "projects", "torre_easy_lo_r00_tgd")

_S = {}


def load():
    if _S:
        return _S
    inp = json.load(open(os.path.join(BASE, "input_real.json"), encoding="utf-8"))
    ref = json.load(open(os.path.join(BASE, "reference.json"), encoding="utf-8"))
    mod = solver_bridge.engine()
    setup = inp["setup_frozen"]
    segs = [s for s in inp["segments"] if s.get("layer") == setup["layer"]]
    lines = [wmb._line_from_segment(mod, s) for s in segs]
    ops = [wmb._op_from_dict(mod, o) for o in inp["openings"]]
    th = sorted(wmb._ft(mod, c) for c in setup["thicknesses_cm"])
    tol = mod.compute_detection_tolerance_ft(th)
    _S.update(inp=inp, ref=ref, mod=mod, setup=setup, segs=segs, lines=lines,
              ops=ops, th=th, tol=tol, F=mod.FEET_PER_METER)
    return _S


def cm(ft):
    return ft / load()["F"] * 100.0


# --------------------------------------------------------------------------
# FINGERPRINT GEOMETRICO CANONICO (item C do pedido)
# --------------------------------------------------------------------------
def canon(line, nd=2):
    """Tupla canonica de UMA linha, em cm, arredondada a `nd` casas
    (nd=2 -> 0,01cm = 0,1mm), com o endpoint MENOR primeiro - portanto
    independente do sentido em que a linha foi construida."""
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    a = (round(cm(p0.X), nd) + 0.0, round(cm(p0.Y), nd) + 0.0)
    b = (round(cm(p1.X), nd) + 0.0, round(cm(p1.Y), nd) + 0.0)
    return (a, b) if a <= b else (b, a)


def canon_set(lines, nd=2):
    return sorted(canon(l, nd) for l in lines)


def fp(lines, nd=2):
    """sha256 do CONJUNTO canonico ordenado por geometria."""
    blob = json.dumps(canon_set(lines, nd), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def diff_sets(a_lines, b_lines, nd=2):
    """(so_em_A, so_em_B) como listas de tuplas canonicas, com
    multiplicidade (Counter, nao set - duplicatas nao somem)."""
    ca, cb = Counter(canon_set(a_lines, nd)), Counter(canon_set(b_lines, nd))
    return sorted((ca - cb).elements()), sorted((cb - ca).elements())


def seg_len(t):
    (x0, y0), (x1, y1) = t
    return math.hypot(x1 - x0, y1 - y0)


# --------------------------------------------------------------------------
# MERGE
# --------------------------------------------------------------------------
def shuffled(lines, seed):
    out = list(lines)
    random.Random(seed).shuffle(out)
    return out


def run_merge(lines, ops=None):
    S = load()
    mod = S["mod"]
    t0 = time.time()
    out = mod.merge_collinear_fragments(
        lines, mod.COLLINEAR_MATCH_TOLERANCE_FT, mod.MAX_JUNCTION_GAP_FT,
        ops if ops is not None else S["ops"],
        mod.OPENING_GAP_PERP_TOLERANCE_FT, mod.OPENING_GAP_WIDTH_SLACK_FT)
    return out, time.time() - t0


def raw_clusters(lines):
    """Replica EXATA da passada 1 de merge_collinear_fragments (o loop
    while/pop(0) do motor), usando as MESMAS funcoes cacheadas do motor.
    Devolve lista de clusters; cada cluster e' lista de Line."""
    mod = load()["mod"]
    tolf = mod.COLLINEAR_MATCH_TOLERANCE_FT
    remaining = [(l, mod._line_geom_cache(l)) for l in lines]
    clusters = []
    while remaining:
        base, bc = remaining.pop(0)
        cluster = [base]
        rest = []
        for other, oc in remaining:
            if (mod._are_parallel_cached(bc, oc) and
                    mod._distance_between_parallel_cached(bc, oc) <= tolf):
                cluster.append(other)
            else:
                rest.append((other, oc))
        remaining = rest
        clusters.append(cluster)
    return clusters


def compatible(a, b):
    """A relacao binaria que decide se `b` entra no cluster de `a`
    (predicado do motor, sem nenhuma reimplementacao)."""
    mod = load()["mod"]
    ca, cb = mod._line_geom_cache(a), mod._line_geom_cache(b)
    return (mod._are_parallel_cached(ca, cb) and
            mod._distance_between_parallel_cached(ca, cb) <= mod.COLLINEAR_MATCH_TOLERANCE_FT)


def compat_parts(a, b):
    mod = load()["mod"]
    ca, cb = mod._line_geom_cache(a), mod._line_geom_cache(b)
    par = mod._are_parallel_cached(ca, cb)
    d = mod._distance_between_parallel_cached(ca, cb)
    return par, d, mod.COLLINEAR_MATCH_TOLERANCE_FT


def merge_cluster(cluster, ops=None):
    S = load()
    mod = S["mod"]
    return mod._merge_collinear_cluster(
        cluster, mod.MAX_JUNCTION_GAP_FT, S["ops"] if ops is None else ops,
        mod.OPENING_GAP_PERP_TOLERANCE_FT, mod.OPENING_GAP_WIDTH_SLACK_FT)


def mkline(x0, y0, x1, y1):
    """Line a partir de coordenadas em CM (helper dos casos sinteticos)."""
    S = load()
    mod = S["mod"]
    f = S["F"] / 100.0
    return mod.Line.CreateBound(mod.XYZ(x0 * f, y0 * f, 0.0), mod.XYZ(x1 * f, y1 * f, 0.0))


# --------------------------------------------------------------------------
# PAREAMENTO
# --------------------------------------------------------------------------
def build_candidates(lines, th=None, tol=None):
    """Mesma varredura O(n^2) de find_wall_pairs, guardando TODOS os campos
    por candidato. Nao decide nada - so' enumera."""
    S = load()
    mod = S["mod"]
    th = S["th"] if th is None else th
    tol = S["tol"] if tol is None else tol
    caches = [mod._line_geom_cache(l) for l in lines]
    n = len(lines)
    cands = []
    for i in range(n):
        ci = caches[i]
        for j in range(i + 1, n):
            cj = caches[j]
            if not mod._are_parallel_cached(ci, cj):
                continue
            d = mod._distance_between_parallel_cached(ci, cj)
            if not (mod.MIN_WALL_THICKNESS_FT <= d <= mod.MAX_WALL_THICKNESS_FT):
                continue
            mt = mod._closest_target_thickness_ft(d, th, tol)
            if mt is None:
                continue
            ov, l1, l2 = mod._line_pair_overlap_ft_cached(ci, cj)
            if ov < mod.MIN_WALL_SEGMENT_ABS_FLOOR_FT:
                continue
            sh = min(l1, l2)
            if sh < 1e-9:
                continue
            r = ov / sh
            if r < mod.MIN_WALL_SEGMENT_OVERLAP_RATIO:
                continue
            err = abs(d - mt)
            rank = int(err / THICKNESS_RANK_BUCKET_FT)
            cands.append(dict(i=i, j=j, d=d, mt=mt, ov=ov, r=r, err=err, rank=rank,
                              key=(rank, -r, -ov, i, j)))
    return cands


def cand_keys(cands, lines, nd=2):
    """Cada candidato vira o par canonico das duas linhas (nao os indices)."""
    return sorted(tuple(sorted((canon(lines[c["i"]], nd), canon(lines[c["j"]], nd))))
                  for c in cands)


def cand_fp(cands, lines, nd=2):
    keys = cand_keys(cands, lines, nd)
    blob = json.dumps(keys, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), keys


def run_pairs(lines):
    """find_wall_pairs REAL (mesmos argumentos de
    wall_modeling_bridge.run_wall_modeling)."""
    S = load()
    mod = S["mod"]
    diag = {"parallel_pairs": 0, "min_dist_ft": None, "max_dist_ft": None,
            "offset_suspect_count": 0, "offset_suspect_max_ft": 0.0,
            "cap_clipped_count": 0}
    t0 = time.time()
    walls, unused = mod.find_wall_pairs(lines, S["th"], S["tol"], lines, S["ops"], diag)
    return walls, unused, diag, time.time() - t0


def full_pipeline(merged_lines):
    """Mesma sequencia de run_wall_modeling, a partir das linhas ja'
    mescladas (o merge fica FORA, para poder congela-lo)."""
    S = load()
    mod = S["mod"]
    walls, unused, diag, dt = run_pairs(merged_lines)
    accepted = len(walls)
    walls, dedup = mod.deduplicate_walls(walls)
    walls, jmap = mod.extend_wall_ends_to_junctions(walls, mod.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = mod.build_wall_graph(walls, jmap)
    odiag = {"clamped_opening_count": 0, "opening_off_center_count": 0,
             "opening_center_gap_max_ft": 0.0, "unassigned_openings": []}
    per_wall = mod.assign_openings_to_walls(walls, S["ops"], odiag)
    return dict(accepted=accepted, dedup=dedup, walls=walls, unused=unused,
                pair_diag=diag, open_diag=odiag, openings_per_wall=per_wall,
                nodes=nodes, pair_time=dt)


def wall_xy(w):
    c = w[0]
    p0, p1 = c.GetEndPoint(0), c.GetEndPoint(1)
    return (cm(p0.X), cm(p0.Y), cm(p1.X), cm(p1.Y))


def wall_keys(walls, nd=2):
    keys = []
    for w in walls:
        x0, y0, x1, y1 = wall_xy(w)
        a = (round(x0, nd) + 0.0, round(y0, nd) + 0.0)
        b = (round(x1, nd) + 0.0, round(y1, nd) + 0.0)
        keys.append(((a, b) if a <= b else (b, a), round(cm(w[1]), 3)))
    keys.sort()
    return keys


def wall_fp(walls, nd=2):
    keys = wall_keys(walls, nd)
    blob = json.dumps(keys, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), keys


# --------------------------------------------------------------------------
# GABARITO (mesmos helpers da Etapa 2D, reaproveitados)
# --------------------------------------------------------------------------
class Ax(object):
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        dx, dy = x1 - x0, y1 - y0
        self.L = math.hypot(dx, dy)
        self.ux, self.uy = (dx / self.L, dy / self.L) if self.L > 1e-9 else (1.0, 0.0)
        self.a = math.degrees(math.atan2(dy, dx)) % 180.0

    def proj(self, x, y):
        return (x - self.x0) * self.ux + (y - self.y0) * self.uy

    def perp(self, x, y):
        return -(x - self.x0) * self.uy + (y - self.y0) * self.ux


def adiff(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def coverage(A, XY, perp_tol=6.0, ang_tol=3.0):
    covered = []
    for x0, y0, x1, y1 in XY:
        B = Ax(x0, y0, x1, y1)
        if adiff(A.a, B.a) > ang_tol:
            continue
        if abs(A.perp(x0, y0)) > perp_tol or abs(A.perp(x1, y1)) > perp_tol:
            continue
        t0, t1 = sorted((A.proj(x0, y0), A.proj(x1, y1)))
        lo, hi = max(0.0, t0), min(A.L, t1)
        if hi > lo:
            covered.append((lo, hi))
    if not covered:
        return 0.0
    covered.sort()
    tot, ch, cl = 0.0, covered[0][1], covered[0][0]
    for lo, hi in covered[1:]:
        if lo > ch:
            tot += ch - cl
            cl, ch = lo, hi
        else:
            ch = max(ch, hi)
    tot += ch - cl
    return tot / A.L


def gabarito_metrics(walls):
    S = load()
    XY = [wall_xy(w) for w in walls]
    covs = [coverage(Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1]), XY)
            for w in S["ref"]["walls"]]
    eb = Counter()
    espurias = 0
    R = [Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1])
         for w in S["ref"]["walls"]]
    for x0, y0, x1, y1 in XY:
        A = Ax(x0, y0, x1, y1)
        mid = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        best = None
        for B in R:
            if adiff(A.a, B.a) > 3.0:
                continue
            t = B.proj(*mid)
            if t < -20 or t > B.L + 20:
                continue
            e = abs(B.perp(*mid))
            if best is None or e < best:
                best = e
        if best is None:
            espurias += 1
            continue
        k = ("<=0,5" if best <= 0.5 else "0,5-2" if best <= 2 else "2-6" if best <= 6
             else "6-10" if best <= 10 else "10-16" if best <= 16 else ">16")
        eb[k] += 1
    lens = [math.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1 in XY]
    return dict(total=len(S["ref"]["walls"]),
                cobertas=sum(1 for c in covs if c >= 0.85),
                ausentes=sum(1 for c in covs if c <= 0.0),
                eixo_ok=eb["<=0,5"], eixo_10_16=eb["10-16"], espurias=espurias,
                walls_lt50=sum(1 for l in lens if l < 50.0),
                walls_lt20=sum(1 for l in lens if l < 20.0),
                total_len_cm=sum(lens), covs=covs)


# --------------------------------------------------------------------------
# CACHE EM DISCO do merge baseline (o merge custa ~12s; varios scripts desta
# etapa partem EXATAMENTE das mesmas 2868 linhas mescladas)
# --------------------------------------------------------------------------
MERGED_CACHE = os.path.join(_HERE, "out_merged_baseline.json")


def baseline_merged(force=False):
    if not force and os.path.exists(MERGED_CACHE):
        data = json.load(open(MERGED_CACHE, encoding="utf-8"))
        return [mkline(*row) for row in data["lines_cm"]]
    merged, dt = run_merge(load()["lines"])
    rows = []
    for l in merged:
        p0, p1 = l.GetEndPoint(0), l.GetEndPoint(1)
        rows.append([cm(p0.X), cm(p0.Y), cm(p1.X), cm(p1.Y)])
    with open(MERGED_CACHE, "w", encoding="utf-8") as fh:
        json.dump({"n": len(rows), "t_merge_s": dt, "fp_01mm": fp(merged, 2),
                   "lines_cm": rows}, fh, ensure_ascii=False)
    return merged


def line_ids(lines):
    """Indice estavel por IDENTIDADE do objeto Line - embaralhar a lista
    reaproveita os MESMOS objetos, entao id() identifica a linha crua
    original independentemente da posicao."""
    return {id(l): k for k, l in enumerate(lines)}


def partition(clusters, ids):
    return sorted(tuple(sorted(ids[id(l)] for l in c)) for c in clusters)
