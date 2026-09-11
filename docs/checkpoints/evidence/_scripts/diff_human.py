# -*- coding: utf-8 -*-
"""Solver do repositorio x modulacao HUMANA (BUTANTA R08_LT, 1o PAV) sobre os
MESMOS 46 eixos. Medicao, nao norma.

Entrada: 2026-09-10-butanta-test-walls.json (eixos reais das Walls do projeto
de teste) e 2026-09-10-butanta-human-sequences.json (blocos humanos por
parede/fiada). Saida: tabela por parede + JSON com as sequencias do solver no
MESMO formato das humanas, para o diff ser reprodutivel.
"""
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("SCALE_BENCH_TESTS",
                      r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\tests")
import scale_bench as sbx  # noqa: E402

m = sbx.m
CATALOG = sbx.CATALOG
XYZ, Line = m.XYZ, m.Line
F2CM = 30.48
EV = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\docs\checkpoints\evidence"
NUM_COURSES = 14
JOINT_TOL = 1.5     # cm, mesma tolerancia de cluster do auditor
COMMON = ("B39", "B34", "B19", "B54", "C09", "C04")   # o que o solver conhece

walls_json = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json")))["walls"]
human = json.load(open(os.path.join(EV, "2026-09-10-butanta-human-sequences.json")))

# ---- eixos reais -> walls_to_create
axes = []
ids = []
for w in walls_json:
    p0 = XYZ(*[float(v) for v in w["p0"]]); p1 = XYZ(*[float(v) for v in w["p1"]])
    axes.append((Line.CreateBound(p0, p1), float(w["width_cm"]) / 100.0 * m.FEET_PER_METER, (False, False)))
    ids.append(w["id"])

walls, jmap = m.extend_wall_ends_to_junctions(list(axes), m.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = m.build_wall_graph(walls, jmap)
kinds = Counter(n["kind"] for n in nodes)
openings = [[] for _ in walls]
res = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings, CATALOG, 0.0, NUM_COURSES,
                                          variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
res["num_courses"] = NUM_COURSES
pf = m.controlled_beta_preflight(res, walls, openings, CATALOG, 0.0)
cc = res["course_candidates"]
audits = res.get("wall_bond_audits") or {}
print("SOLVER sobre os 46 eixos: nos=%s" % dict(kinds))
print("  pecas=%d preflight_ok=%s colisoes=%d ifail=%d nmod=%d bond_reprovadas=%d" % (
    sum(len(v) for v in cc.values()), pf["ok"], len(pf["collisions"]),
    len(res["intersection_failures"] or []), len(res["non_modular"] or []),
    sum(1 for a in audits.values() if not a["ok"])))

# ---- sequencias do solver no formato humano: (t0, t1, code, along)
def wall_frame(wi):
    p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, wi)
    return p0, d

solver_seq = defaultdict(lambda: defaultdict(list))
for ci, pieces in cc.items():
    for c in pieces:
        o = c["origin_world"]
        for wi in range(len(walls)):
            p0, d = wall_frame(wi)
            t = ((o.X - p0.X) * d.X + (o.Y - p0.Y) * d.Y) * F2CM
            lat = abs((o.X - p0.X) * d.Y - (o.Y - p0.Y) * d.X) * F2CM
            L = walls[wi][0].Length * F2CM
            if lat > 7.5 or t < -60 or t > L + 60:
                continue
            along = abs(c["x_dir"].X * d.X + c["x_dir"].Y * d.Y) > 0.99
            if along:
                half = c["length_cm"] / 2.0
            else:
                half = c["width_cm"] / 2.0
            solver_seq[ids[wi]][ci].append((round(t - half, 1), round(t + half, 1), c["logical_code"], along, c.get("wall_idx") == wi))

def joints(seq):
    """Juntas entre pecas ALINHADAS encostadas (gap <= 5cm), como o auditor."""
    pcs = sorted((t0, t1) for t0, t1, cd, al, _ in seq if al)
    out = []
    for (a0, a1), (b0, b1) in zip(pcs, pcs[1:]):
        if -2.5 <= b0 - a1 <= 5.0:   # bbox humano inclui 1cm de junta por face
            out.append((a1 + b0) / 2.0)
    return out

def match(ja, jb):
    if not ja and not jb:
        return 1.0
    if not ja or not jb:
        return 0.0
    hit = sum(1 for x in ja if any(abs(x - y) <= JOINT_TOL for y in jb))
    return hit / float(max(len(ja), len(jb)))

def hist(seqs):
    h = Counter()
    for seq in seqs:
        for t0, t1, cd, al, *_ in seq:
            if al and cd in COMMON:
                h[cd] += 1
    return h

# ---- tabela por parede
print("\n%-9s %-6s %-5s %-5s %-6s %-6s %-6s %-6s %s" % (
    "wall", "len", "hum", "solv", "jm_c0", "jm_c1", "jm_c0x", "jm_c1x", "audit/solver"))
rows = []
tot_h = Counter(); tot_s = Counter()
for wi, wid in enumerate(ids):
    hseq = human["per_wall"].get(str(wid), {})
    h0 = [tuple(x) for x in hseq.get("0", [])]; h1 = [tuple(x) for x in hseq.get("1", [])]
    s0 = solver_seq[wid].get(0, []); s1 = solver_seq[wid].get(1, [])
    jh0, jh1, js0, js1 = joints(h0), joints(h1), joints(s0), joints(s1)
    same = (match(jh0, js0) + match(jh1, js1)) / 2.0
    cross = (match(jh0, js1) + match(jh1, js0)) / 2.0
    hcount = sum(len(hseq.get(str(c), [])) for c in range(13))
    scount = sum(len(solver_seq[wid].get(c, [])) for c in range(13))
    a = audits.get(wi) or {}
    flag = ("REPROVADA" if a and not a.get("ok", True) else "ok")
    nm = sum(1 for e in (res["non_modular"] or []) if e.get("wall_idx") == wi)
    if nm:
        flag += " nmod=%d" % nm
    masonry = hcount >= 20
    if not masonry:
        flag = "NAO-ALVENARIA(humano) " + flag
    else:
        tot_h.update(hist([[tuple(x) for x in hseq.get(str(c), [])] for c in range(13)]))
        tot_s.update(hist([solver_seq[wid].get(c, []) for c in range(13)]))
    rows.append((wid, walls[wi][0].Length * F2CM, hcount, scount, match(jh0, js0), match(jh1, js1),
                 match(jh0, js1), match(jh1, js0), flag))
    print("%-9d %-6.0f %-5d %-5d %-6.2f %-6.2f %-6.2f %-6.2f %s" % rows[-1])

print("\n=== histograma de pecas ALINHADAS, fiadas 0..12, 46 paredes ===")
print("%-6s %-8s %-8s" % ("code", "humano", "solver"))
for cd in COMMON:
    print("%-6s %-8d %-8d" % (cd, tot_h[cd], tot_s[cd]))

# ---- primeira peca em cada ponta, por paridade (humano x solver)
def first_last(seq, L):
    al = sorted((t0, t1, cd) for t0, t1, cd, a, *_ in seq if a)
    if not al:
        return None, None
    return al[0][2], al[-1][2]

print("\n=== primeira/ultima peca alinhada (c0 | c1): humano -> solver, 12 paredes mais longas ===")
for wi, wid in sorted(enumerate(ids), key=lambda x: -walls[x[0]][0].Length)[:12]:
    L = walls[wi][0].Length * F2CM
    hseq = human["per_wall"].get(str(wid), {})
    h0 = [tuple(x) for x in hseq.get("0", [])]; h1 = [tuple(x) for x in hseq.get("1", [])]
    s0 = solver_seq[wid].get(0, []); s1 = solver_seq[wid].get(1, [])
    print("  %d len=%.0f  c0 H %s..%s | S %s..%s     c1 H %s..%s | S %s..%s" % (
        wid, L, *first_last(h0, L), *first_last(s0, L), *first_last(h1, L), *first_last(s1, L)))

# ---- corridas de B34 no humano (comprimento das sequencias consecutivas)
runs = Counter()
for wid, courses in human["per_wall"].items():
    for c, seq in courses.items():
        if int(c) > 12:
            continue
        al = sorted((t0, t1, cd) for t0, t1, cd, a, _ in seq if a)
        run = 0
        for t0, t1, cd in al:
            if cd == "B34":
                run += 1
            else:
                if run:
                    runs[min(run, 6)] += 1
                run = 0
        if run:
            runs[min(run, 6)] += 1
print("\n=== HUMANO: corridas consecutivas de B34 (tamanho -> ocorrencias; 6 = 6+) ===")
print("  %s" % dict(sorted(runs.items())))

# ---- NO' A NO': o que o humano poe em cada encontro (c0, c1) x o que o solver poe
blocks = json.load(open(os.path.join(EV, "2026-09-10-butanta-ref-1pav-blocks.json")))["blocks"]
CODEMAP = {"BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34", "MEIO BLOCO - 14x19x19": "B19",
           "BLOCO 54 - 14x19x54": "B54", "COMPENSADOR 14x19x9": "C09", "PASTILHA - 14x19X4": "C04"}
def human_at(px, py, course):
    out = []
    for b in blocks:
        bb = b.get("bb")
        if not bb: continue
        if int(round((b["z"] - 1.0) / 20.0)) != course: continue
        if bb[0] - 0.5 <= px <= bb[3] + 0.5 and bb[1] - 0.5 <= py <= bb[4] + 0.5:
            out.append(CODEMAP.get(b["sym"], "?"))
    return tuple(sorted(out))
def solver_at(px, py, course):
    out = []
    for c in cc.get(course, []):
        o = c["origin_world"]
        dx, dy = (px / F2CM - o.X), (py / F2CM - o.Y)
        ax = abs(dx * c["x_dir"].X + dy * c["x_dir"].Y) * F2CM
        ay = abs(dx * c["y_dir"].X + dy * c["y_dir"].Y) * F2CM
        if ax <= c["length_cm"] / 2.0 + 0.5 and ay <= c["width_cm"] / 2.0 + 0.5:
            out.append(c["logical_code"])
    return tuple(sorted(out))
pat = defaultdict(Counter)
detail = []
for ni, n in enumerate(nodes):
    if n["kind"] not in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"): continue
    px, py = n["point"].X * F2CM, n["point"].Y * F2CM
    h = (human_at(px, py, 0), human_at(px, py, 1))
    sv = (solver_at(px, py, 0), solver_at(px, py, 1))
    pat[n["kind"]][("H", h)] += 1
    pat[n["kind"]][("S", sv)] += 1
    detail.append((n["kind"], round(px), round(py), h, sv))
print("\n=== NO A NO: peca(s) cobrindo o ponto do no em (c0, c1) ===")
for kind in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
    print("-- %s --" % kind)
    for (who, p), nct in sorted(pat[kind].items(), key=lambda x: (x[0][0], -x[1]))[:16]:
        print("   %s x%-3d %s" % ("HUMANO" if who == "H" else "SOLVER", nct, p))
print("\n=== amostra de 10 nos T (kind, x, y, humano(c0,c1), solver(c0,c1)) ===")
for d in [x for x in detail if x[0] == "T_INTERSECTION"][:10]:
    print("   %s" % (d,))

json.dump({"ids": ids, "solver_seq": {str(k): {str(c): v for c, v in d.items()} for k, d in solver_seq.items()},
           "rows": rows, "hist_human": tot_h, "hist_solver": tot_s, "nodes": detail},
          open(os.path.join(EV, "2026-09-10-butanta-solver-vs-human.json"), "w"))
print("\nescrito 2026-09-10-butanta-solver-vs-human.json")
