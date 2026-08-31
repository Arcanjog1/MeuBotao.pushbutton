# -*- coding: utf-8 -*-
"""ETAPA 2D - laboratorio OFFLINE do pareamento. SOMENTE LEITURA do repo.

Reconstroi o mesmo estado de find_wall_pairs (merge -> candidatos) e permite
trocar SO' a politica de selecao, rodando o resto do pipeline real
(create_centerline / clip_centerline_to_caps / deduplicate_walls /
extend_wall_ends_to_junctions / build_wall_graph / assign_openings_to_walls)
sem tocar em nuvem/core/**.
"""
import json, os, sys, math, time
from collections import Counter, defaultdict

sys.path.insert(0, "nuvem")
from benchmark import solver_bridge, wall_modeling_bridge as wmb

BASE = "nuvem/benchmark/projects/torre_easy_lo_r00_tgd"

_STATE = {}


def state():
    if _STATE:
        return _STATE
    inp = json.load(open(os.path.join(BASE, "input_real.json"), encoding="utf-8"))
    mod = solver_bridge.engine()
    F = mod.FEET_PER_METER
    setup = inp["setup_frozen"]
    segs = [s for s in inp["segments"] if s.get("layer") == setup["layer"]]
    lines = [wmb._line_from_segment(mod, s) for s in segs]
    ops = [wmb._op_from_dict(mod, o) for o in inp["openings"]]
    th = sorted(wmb._ft(mod, c) for c in setup["thicknesses_cm"])
    t0 = time.time()
    merged = mod.merge_collinear_fragments(
        lines, mod.COLLINEAR_MATCH_TOLERANCE_FT, mod.MAX_JUNCTION_GAP_FT,
        ops, mod.OPENING_GAP_PERP_TOLERANCE_FT, mod.OPENING_GAP_WIDTH_SLACK_FT)
    t_merge = time.time() - t0
    tol = mod.compute_detection_tolerance_ft(th)
    _STATE.update(inp=inp, mod=mod, F=F, setup=setup, ops=ops, th=th,
                  merged=merged, tol=tol, t_merge=t_merge,
                  ref=json.load(open(os.path.join(BASE, "reference.json"), encoding="utf-8")))
    return _STATE


def cm(ft):
    return ft / state()["F"] * 100.0


def build_candidates(th=None, tol=None):
    """Mesma varredura O(n^2) de find_wall_pairs, mas guardando TODOS os
    atributos de cada candidato (nao so' o sort_key)."""
    S = state()
    mod = S["mod"]
    wp = mod
    th = S["th"] if th is None else th
    tol = S["tol"] if tol is None else tol
    pending = list(S["merged"])
    n = len(pending)
    caches = [wp._line_geom_cache(l) for l in pending]
    t0 = time.time()
    cands = []
    for i in range(n):
        ci = caches[i]
        for j in range(i + 1, n):
            cj = caches[j]
            if not wp._are_parallel_cached(ci, cj):
                continue
            d = wp._distance_between_parallel_cached(ci, cj)
            if not (wp.MIN_WALL_THICKNESS_FT <= d <= wp.MAX_WALL_THICKNESS_FT):
                continue
            mt = wp._closest_target_thickness_ft(d, th, tol)
            if mt is None:
                continue
            ov, l1, l2 = wp._line_pair_overlap_ft_cached(ci, cj)
            if ov < wp.MIN_WALL_SEGMENT_ABS_FLOOR_FT:
                continue
            sh = min(l1, l2)
            if sh < 1e-9:
                continue
            r = ov / sh
            if r < wp.MIN_WALL_SEGMENT_OVERLAP_RATIO:
                continue
            lg = max(l1, l2)
            cands.append(dict(
                i=i, j=j,
                d_ft=d, d=cm(d),
                t_ft=mt, t=cm(mt),
                err=abs(cm(d) - cm(mt)),
                err_n=abs(cm(d) - cm(mt)) / cm(mt),
                ov_ft=ov, ov=cm(ov),
                li=cm(l1), lj=cm(l2),
                short=cm(sh), long=cm(lg),
                r=r, r_long=ov / lg,
            ))
    return pending, cands, time.time() - t0


def run_pipeline(pending, chosen):
    """`chosen` = lista de candidatos JA na ordem de aceitacao (greedy sobre
    ela) OU lista de pares ja disjuntos. Roda exatamente o resto do
    pipeline real."""
    S = state()
    mod = S["mod"]
    ops = S["ops"]
    n = len(pending)
    used = [False] * n
    walls = []
    accepted = []
    lost = []
    owner = {}
    for c in chosen:
        i, j = c["i"], c["j"]
        if used[i] or used[j]:
            lost.append(c)
            continue
        centerline = mod.create_centerline(pending[i], pending[j], mod.CENTERLINE_MAX_EXTENSION_FT)
        if centerline:
            locked = (False, False)
            clipped, locked = mod.clip_centerline_to_caps(centerline, c["t_ft"], pending, ops)
            centerline = clipped
            if centerline is not None:
                walls.append((centerline, c["t_ft"], locked))
        # ATENCAO: identico a producao - as duas faces sao consumidas mesmo
        # que nenhuma parede tenha nascido.
        owner[i] = len(accepted)
        owner[j] = len(accepted)
        accepted.append(c)
        used[i] = True
        used[j] = True
    return dict(walls=walls, accepted=accepted, lost=lost, owner=owner, used=used)


def finish(walls):
    """dedup -> extend -> graph -> assign, como wall_modeling_bridge."""
    S = state()
    mod = S["mod"]
    ops = S["ops"]
    walls2, dup = mod.deduplicate_walls(walls)
    before = list(walls2)
    walls3, jmap = mod.extend_wall_ends_to_junctions(walls2, mod.JUNCTION_FACE_SEARCH_FT)
    nodes, w2n = mod.build_wall_graph(walls3, jmap)
    diag = {"clamped_opening_count": 0, "opening_off_center_count": 0,
            "opening_center_gap_max_ft": 0.0, "unassigned_openings": []}
    opw = mod.assign_openings_to_walls(walls3, ops, diag)
    return dict(final=walls3, before=before, dup_removed=dup,
                openings_per_wall=opw, op_diag=diag)


# --------------------------------------------------------------- metricas
def ang(x0, y0, x1, y1):
    return math.degrees(math.atan2(y1 - y0, x1 - x0)) % 180.0


def adiff(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


class Ax(object):
    def __init__(s, x0, y0, x1, y1):
        s.x0, s.y0, s.x1, s.y1 = x0, y0, x1, y1
        s.L = math.hypot(x1 - x0, y1 - y0)
        s.ux, s.uy = ((x1 - x0) / s.L, (y1 - y0) / s.L) if s.L > 1e-9 else (1., 0.)
        s.a = ang(x0, y0, x1, y1)

    def proj(s, p, q):
        return (p - s.x0) * s.ux + (q - s.y0) * s.uy

    def perp(s, p, q):
        return -(p - s.x0) * s.uy + (q - s.y0) * s.ux


def wall_xy(w):
    p0, p1 = w[0].GetEndPoint(0), w[0].GetEndPoint(1)
    return cm(p0.X), cm(p0.Y), cm(p1.X), cm(p1.Y)


def coverage(axis, others, perp_tol=8.0):
    iv = []
    for x0, y0, x1, y1 in others:
        if adiff(axis.a, ang(x0, y0, x1, y1)) > 3.0:
            continue
        pm = (axis.perp(x0, y0) + axis.perp(x1, y1)) / 2.0
        if abs(pm) > perp_tol:
            continue
        t0, t1 = sorted((axis.proj(x0, y0), axis.proj(x1, y1)))
        a, b = max(t0, 0.0), min(t1, axis.L)
        if b - a <= 1.0:
            continue
        iv.append((a, b))
    iv.sort()
    mrg = []
    for a, b in iv:
        if mrg and a <= mrg[-1][1]:
            mrg[-1][1] = max(mrg[-1][1], b)
        else:
            mrg.append([a, b])
    c = sum(b - a for a, b in mrg)
    return c / axis.L if axis.L > 0 else 0.0


def metrics(name, res, fin, cands, elapsed):
    S = state()
    ref = S["ref"]
    acc = res["accepted"]
    final = fin["final"]
    XY = [wall_xy(w) for w in final]
    lens = [math.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1 in XY]

    errs = sorted(c["err"] for c in acc)
    exact = sum(1 for e in errs if e <= 0.05)
    p95 = errs[int(0.95 * (len(errs) - 1))] if errs else 0.0

    # face steals: candidatos "verdadeiros" (err<=0,05 e r>=0,9) descartados
    steals = sum(1 for c in res["lost"] if c["err"] <= 0.05 and c["r"] >= 0.9)

    # cobertura do gabarito
    covs = []
    for w in ref["walls"]:
        A = Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1])
        covs.append(coverage(A, XY))
    cob = sum(1 for c in covs if c >= 0.85)
    aus = sum(1 for c in covs if c <= 0.0)

    # erro de eixo
    R = [Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1]) for w in ref["walls"]]
    eb = Counter()
    espurias = 0
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

    unass = fin["op_diag"].get("unassigned_openings") or []
    unass_ids = sorted(str(o.get("element_id")) for o in unass)
    n_assigned_ops = len(state()["ops"]) - len(unass)

    return dict(
        name=name,
        n_cand=len(cands),
        aceitos=len(acc),
        exatos=exact,
        pct_exato=100.0 * exact / len(acc) if acc else 0.0,
        err_medio=sum(errs) / len(errs) if errs else 0.0,
        err_p95=p95,
        err_max=errs[-1] if errs else 0.0,
        steals=steals,
        walls=len(final),
        dup=fin["dup_removed"],
        w_lt50=sum(1 for L in lens if L < 50.0),
        w_lt20=sum(1 for L in lens if L < 20.0),
        mod5=sum(1 for L in lens if abs((L % 5.0) - 4.0) <= 0.5 or (L % 5.0) <= 0.0001),
        mod5_strict=sum(1 for L in lens if abs((L % 5.0) - 4.0) <= 0.5),
        total_cm=sum(lens),
        cobertas=cob,
        ausentes=aus,
        eixo_ok=eb["<=0,5"],
        eixo_10_16=eb["10-16"],
        espurias=espurias,
        eb=dict(eb),
        ops_ok=n_assigned_ops,
        unass_ids=unass_ids,
        t=elapsed,
    )


HDR = ("estrategia", "aceit", "exato", "%exa", "errmed", "errP95", "steal",
       "walls", "<50", "<20", "%5==4", "cober", "ausen", "eixoOK", "10-16",
       "espur", "ops", "s")


def row(m):
    return "%-26s %5d %5d %5.0f%% %6.3f %6.3f %5d %5d %4d %4d %5d %5d %5d %6d %5d %5d %4d %5.1f" % (
        m["name"], m["aceitos"], m["exatos"], m["pct_exato"], m["err_medio"], m["err_p95"],
        m["steals"], m["walls"], m["w_lt50"], m["w_lt20"], m["mod5_strict"],
        m["cobertas"], m["ausentes"], m["eixo_ok"], m["eixo_10_16"], m["espurias"],
        m["ops_ok"], m["t"])


def header():
    return "%-26s %5s %5s %6s %6s %6s %5s %5s %4s %4s %5s %5s %5s %6s %5s %5s %4s %5s" % HDR
