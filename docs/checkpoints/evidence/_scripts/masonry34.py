# -*- coding: utf-8 -*-
"""So' as paredes que sao ALVENARIA no projeto humano (>=20 blocos). Tres medicoes:
(A) diff no' a no' limpo; (B) o AUDITOR do repositorio aplicado a' modulacao HUMANA;
(C) orientacao dos B34|B34 em T proximos e o trecho curto antes do 1o T."""
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
CM2F = 1 / 30.48
EV = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\docs\checkpoints\evidence"
walls_json = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json")))["walls"]
human = json.load(open(os.path.join(EV, "2026-09-10-butanta-human-sequences.json")))
blocks = json.load(open(os.path.join(EV, "2026-09-10-butanta-ref-1pav-blocks.json")))["blocks"]
CODEMAP = {"BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34", "MEIO BLOCO - 14x19x19": "B19",
           "BLOCO 54 - 14x19x54": "B54", "COMPENSADOR 14x19x9": "C09", "PASTILHA - 14x19X4": "C04"}
hcount = {w["id"]: sum(len(human["per_wall"].get(str(w["id"]), {}).get(str(c), [])) for c in range(13))
          for w in walls_json}
masonry = [w for w in walls_json if hcount[w["id"]] >= 20]
print("paredes alvenaria (humano): %d de %d" % (len(masonry), len(walls_json)))
axes = []
ids = []
for w in masonry:
    axes.append((Line.CreateBound(XYZ(*[float(v) for v in w["p0"]]), XYZ(*[float(v) for v in w["p1"]])),
                 14.0 / 100.0 * m.FEET_PER_METER, (False, False)))
    ids.append(w["id"])
walls, jmap = m.extend_wall_ends_to_junctions(list(axes), m.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = m.build_wall_graph(walls, jmap)
print("nos: %s" % dict(Counter(n["kind"] for n in nodes)))
res = m.solve_building_blocks_all_courses(nodes, walls, e2n, [[] for _ in walls], CATALOG, 0.0, 14,
                                          variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
res["num_courses"] = 14
pf = m.controlled_beta_preflight(res, walls, [[] for _ in walls], CATALOG, 0.0)
cc = res["course_candidates"]
aud = res["wall_bond_audits"]
print("SOLVER(34): pecas=%d preflight_ok=%s ifail=%d nmod=%d bond_reprov=%d" % (
    sum(len(v) for v in cc.values()), pf["ok"], len(res["intersection_failures"] or []),
    len(res["non_modular"] or []), sum(1 for a in aud.values() if not a["ok"])))
for f in (res["intersection_failures"] or []):
    print("   ifail: no %s: %s" % (f[0], str(f[1])[:100]))


def frame(wi):
    p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, wi)
    return p0, d


def human_at(px, py, course):
    out = []
    for b in blocks:
        bb = b.get("bb")
        if not bb or int(round((b["z"] - 1.0) / 20.0)) != course:
            continue
        if bb[0] - 0.5 <= px <= bb[3] + 0.5 and bb[1] - 0.5 <= py <= bb[4] + 0.5:
            out.append((CODEMAP.get(b["sym"], "?"), "H" if abs(math.sin(b["rot"])) < 0.5 else "V"))
    return tuple(sorted(out))


def solver_at(px, py, course):
    out = []
    for c in cc.get(course, []):
        o = c["origin_world"]
        dx, dy = px / F2CM - o.X, py / F2CM - o.Y
        ax = abs(dx * c["x_dir"].X + dy * c["x_dir"].Y) * F2CM
        ay = abs(dx * c["y_dir"].X + dy * c["y_dir"].Y) * F2CM
        if ax <= c["length_cm"] / 2.0 + 0.5 and ay <= c["width_cm"] / 2.0 + 0.5:
            out.append((c["logical_code"], "H" if abs(c["x_dir"].Y) < 0.5 else "V"))
    return tuple(sorted(out))


print("\n=== (A) NOS T (34 paredes): humano x solver, orientacao da peca (H/V), direcao da principal ===")
tie = [n for n in nodes if n["kind"] in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION")]
pat = Counter()
for n in nodes:
    if n["kind"] != "T_INTERSECTION":
        continue
    px, py = n["point"].X * F2CM, n["point"].Y * F2CM
    mi = n["main_wall_idx"]
    p0, d = frame(mi)
    mdir = "H" if abs(d.Y) < 0.5 else "V"
    dl = [abs((o["point"].X - n["point"].X) * d.X + (o["point"].Y - n["point"].Y) * d.Y) * F2CM
          for o in tie if o is not n and abs((o["point"].X - p0.X) * d.Y - (o["point"].Y - p0.Y) * d.X) * F2CM <= 1.0]
    dmin = min(dl) if dl else 9999
    h = (human_at(px, py, 0), human_at(px, py, 1))
    s = (solver_at(px, py, 0), solver_at(px, py, 1))
    tag = "<54" if dmin < 54 else ">=54"
    pat[(tag, "H", h)] += 1
    pat[(tag, "S", s)] += 1
    if dmin < 54 or h[0] == h[1]:
        print("   (%5.0f,%5.0f) principal=%s dmin=%4.0f  HUM %s  SOL %s" % (px, py, mdir, dmin, h, s))
print("-- resumo --")
for k, v in sorted(pat.items(), key=lambda x: (x[0][0], x[0][1], -x[1])):
    print("   %s %s x%-2d %s" % (k[0], "HUM" if k[1] == "H" else "SOL", v, k[2]))

print("\n=== (B) AUDITOR DO REPOSITORIO aplicado a' MODULACAO HUMANA (fiadas 0..12) ===")


def wall_for_block(b):
    bh = abs(math.sin(b["rot"])) < 0.5
    for wi in range(len(walls)):
        p0, d = frame(wi)
        if (abs(d.Y) < 0.5) != bh:
            continue
        cx, cy = b["x"] * CM2F, b["y"] * CM2F
        lat = abs((cx - p0.X) * d.Y - (cy - p0.Y) * d.X) * F2CM
        t = ((cx - p0.X) * d.X + (cy - p0.Y) * d.Y) * F2CM
        if lat <= 7.5 and -30 <= t <= walls[wi][0].Length * F2CM + 30:
            return wi
    return None


cch = defaultdict(list)
skipped = Counter()
for b in blocks:
    code = CODEMAP.get(b["sym"])
    ci = int(round((b["z"] - 1.0) / 20.0))
    if code is None or ci > 12:
        skipped["canaleta/outro/cinta"] += 1
        continue
    wi = wall_for_block(b)
    if wi is None:
        skipped["sem parede alvenaria"] += 1
        continue
    bb = b["bb"]
    cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
    ang = b["rot"]
    xd = XYZ(math.cos(ang), math.sin(ang), 0.0)
    yd = XYZ(-math.sin(ang), math.cos(ang), 0.0)
    cch[ci].append({"origin_world": XYZ(cx * CM2F, cy * CM2F, b["z"] * CM2F), "x_dir": xd, "y_dir": yd,
                    "length_cm": CATALOG[code]["length_cm"], "width_cm": 14.0, "height_cm": 19.0,
                    "logical_code": code, "course": "A" if ci % 2 == 0 else "B", "course_index": ci,
                    "wall_idx": wi, "placement_reason": "HUMAN", "node_index": None})
print("blocos usados: %d | pulados: %s" % (sum(len(v) for v in cch.values()), dict(skipped)))
audh = m.audit_all_walls_bond_quality(walls, cch, CATALOG, 13, openings_per_wall=[[] for _ in walls],
                                      nodes=nodes, end_to_node=e2n)
rep = {wi: a for wi, a in audh.items() if not a["ok"]}
print("HUMANO auditado: %d paredes, %d REPROVADAS pelo auditor do repo" % (len(audh), len(rep)))
kinds = Counter()
for wi, a in sorted(rep.items()):
    for p in a["problems"]:
        kinds[str(p).split(":")[0]] += 1
    print("   wall %d (len %.0f): %s" % (ids[wi], walls[wi][0].Length * F2CM, [str(p)[:95] for p in a["problems"]][:3]))
print("-- tipos de problema no HUMANO: %s" % dict(kinds))
print("   continuous_joints=%d  half_blocks_near_ties=%d  compensator_strips=%d  alternating_strips(info)=%d" % (
    sum(len(a["continuous_joints"]) for a in audh.values()),
    sum(len(a.get("half_blocks_near_ties") or []) for a in audh.values()),
    sum(len(a["compensator_strips"]) for a in audh.values()),
    sum(len(a["alternating_strips"]) for a in audh.values())))

print("\n=== (C) trecho curto antes do 1o T a partir de uma PONTA LIVRE: humano c0|c1 ===")
for n in nodes:
    if n["kind"] != "T_INTERSECTION":
        continue
    mi = n["main_wall_idx"]
    p0, d = frame(mi)
    L = walls[mi][0].Length * F2CM
    t = ((n["point"].X - p0.X) * d.X + (n["point"].Y - p0.Y) * d.Y) * F2CM
    for end, tt in ((0, t), (1, L - t)):
        if tt > 120 or e2n.get((mi, end)) is None:
            continue
        if nodes[e2n[(mi, end)]]["kind"] != "FREE_END":
            continue
        seqs = []
        for ci in (0, 1):
            parts = []
            for c in cch.get(ci, []):
                if c["wall_idx"] != mi:
                    continue
                o = c["origin_world"]
                tc = ((o.X - p0.X) * d.X + (o.Y - p0.Y) * d.Y) * F2CM
                if end == 1:
                    tc = L - tc
                if -5 <= tc <= tt + 30:
                    parts.append((round(tc - c["length_cm"] / 2), c["logical_code"]))
            seqs.append(" ".join("%s@%d" % (cd, t0) for t0, cd in sorted(parts)))
        print("   wall %d ponta%d->T em %.0fcm: c0: %s | c1: %s" % (ids[mi], end, tt, seqs[0], seqs[1]))
