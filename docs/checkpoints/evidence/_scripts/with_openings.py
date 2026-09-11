# -*- coding: utf-8 -*-
"""Rodada COM as aberturas humanas (02_openings.json do repo) sobre as 34
paredes de alvenaria: (B) auditor do repo aplicado ao humano, agora com as
jambas isentas como manda a regra; (D) solver COM aberturas x humano, no' a
no' e histograma; (C) trechos curtos ponta-livre -> T, agora sabendo onde ha'
abertura. Medicao, nao norma."""
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
ROOT = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
EV = os.path.join(ROOT, "docs", "checkpoints", "evidence")
walls_json = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json")))["walls"]
human = json.load(open(os.path.join(EV, "2026-09-10-butanta-human-sequences.json")))
blocks = json.load(open(os.path.join(EV, "2026-09-10-butanta-ref-1pav-blocks.json")))["blocks"]
ops_all = json.load(open(os.path.join(ROOT, "docs", "revit_reference_extraction", "butanta-r08-lt",
                                      "02_openings.json"), encoding="utf-8"))["openings"]
CODEMAP = {"BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34", "MEIO BLOCO - 14x19x19": "B19",
           "BLOCO 54 - 14x19x54": "B54", "COMPENSADOR 14x19x9": "C09", "PASTILHA - 14x19X4": "C04"}
hcount = {w["id"]: sum(len(human["per_wall"].get(str(w["id"]), {}).get(str(c), [])) for c in range(13))
          for w in walls_json}
masonry = [w for w in walls_json if hcount[w["id"]] >= 20]
axes, ids = [], []
for w in masonry:
    axes.append((Line.CreateBound(XYZ(*[float(v) for v in w["p0"]]), XYZ(*[float(v) for v in w["p1"]])),
                 14.0 / 100.0 * m.FEET_PER_METER, (False, False)))
    ids.append(w["id"])
walls, jmap = m.extend_wall_ends_to_junctions(list(axes), m.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = m.build_wall_graph(walls, jmap)


def frame(wi):
    p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, wi)
    return p0, d


# ---- aberturas humanas do 1o PAV -> openings_per_wall (t_lo, t_hi, sill, head) em pes
ops = [o for o in ops_all if str(o.get("level", "")).startswith("1")]
openings_per_wall = [[] for _ in walls]
unassigned = []
for o in ops:
    ox, oy = o["x_cm"], o["y_cm"]
    horiz = (o["axis"] == "X")
    w = o["opening_width_cm"]
    best = None
    for wi in range(len(walls)):
        p0, d = frame(wi)
        if (abs(d.Y) < 0.5) != horiz:
            continue
        lat = abs((ox * CM2F - p0.X) * d.Y - (oy * CM2F - p0.Y) * d.X) * F2CM
        t = ((ox * CM2F - p0.X) * d.X + (oy * CM2F - p0.Y) * d.Y) * F2CM
        L = walls[wi][0].Length * F2CM
        if lat <= 8.0 and -1 <= t <= L + 1 and (best is None or lat < best[0]):
            best = (lat, wi, t)
    if best is None:
        unassigned.append((ox, oy, o["axis"], w))
        continue
    _lat, wi, t = best
    sill = o["opening_base_z_rel_cm"]
    head = o["opening_top_z_rel_cm"]
    openings_per_wall[wi].append(((t - w / 2.0) * CM2F, (t + w / 2.0) * CM2F, sill * CM2F, head * CM2F))
for lst in openings_per_wall:
    lst.sort()
print("aberturas 1o PAV: %d | associadas a paredes de alvenaria: %d | sem parede: %d" % (
    len(ops), sum(len(v) for v in openings_per_wall), len(unassigned)))
kinds_op = Counter(o["classification_CALCULADO"][:22] for o in ops)
print("   classes: %s" % dict(kinds_op))

# ---- candidatos humanos
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
for b in blocks:
    code = CODEMAP.get(b["sym"])
    ci = int(round((b["z"] - 1.0) / 20.0))
    if code is None or ci > 12:
        continue
    wi = wall_for_block(b)
    if wi is None:
        continue
    bb = b["bb"]
    cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
    ang = b["rot"]
    cch[ci].append({"origin_world": XYZ(cx * CM2F, cy * CM2F, b["z"] * CM2F),
                    "x_dir": XYZ(math.cos(ang), math.sin(ang), 0.0), "y_dir": XYZ(-math.sin(ang), math.cos(ang), 0.0),
                    "length_cm": CATALOG[code]["length_cm"], "width_cm": 14.0, "height_cm": 19.0,
                    "logical_code": code, "course": "A" if ci % 2 == 0 else "B", "course_index": ci,
                    "wall_idx": wi, "placement_reason": "HUMAN", "node_index": None})

print("\n=== (B) AUDITOR DO REPO sobre o HUMANO, COM aberturas ===")
audh = m.audit_all_walls_bond_quality(walls, cch, CATALOG, 13, openings_per_wall=openings_per_wall,
                                      nodes=nodes, end_to_node=e2n)
rep = {wi: a for wi, a in audh.items() if not a["ok"]}
print("HUMANO: %d paredes auditadas, %d REPROVADAS" % (len(audh), len(rep)))
kinds = Counter()
for wi, a in sorted(rep.items()):
    for p in a["problems"]:
        kinds[str(p).split(":")[0]] += 1
    print("   wall %d (len %.0f, aberturas %d): %s" % (ids[wi], walls[wi][0].Length * F2CM, len(openings_per_wall[wi]),
                                                    [str(p)[:110] for p in a["problems"]][:3]))
print("-- problemas no HUMANO com aberturas: %s" % dict(kinds))
# juntas corridas restantes: encostam em amarracao?
tie_codes = ("B34", "B54")
for wi, a in sorted(rep.items()):
    p0, d = frame(wi)
    for cj in a["continuous_joints"]:
        x = cj["x_cm"]
        touching = Counter()
        for ci in cj["courses"]:
            for c in cch.get(ci, []):
                if c["wall_idx"] != wi:
                    continue
                lo, hi = m._candidate_extent_on_wall_axis(c, p0, d)
                if abs(hi - x) < 2 or abs(lo - x) < 2:
                    touching["TIE" if c["logical_code"] in tie_codes else "FILL"] += 1
        print("      junta corrida wall %d x=%.1f fiadas=%d -> pecas encostadas: %s" % (ids[wi], x, len(cj["courses"]), dict(touching)))

print("\n=== (D) SOLVER COM aberturas x HUMANO (34 paredes) ===")
res = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings_per_wall, CATALOG, 0.0, 14,
                                          variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
res["num_courses"] = 14
pf = m.controlled_beta_preflight(res, walls, openings_per_wall, CATALOG, 0.0)
cc = res["course_candidates"]
aud = res["wall_bond_audits"]
print("SOLVER: pecas=%d preflight_ok=%s colisoes=%d invasoes=%d ifail=%d nmod=%d bond_reprov=%d door_void=%d" % (
    sum(len(v) for v in cc.values()), pf["ok"], len(pf["collisions"]), len(pf["opening_violations"]),
    len(res["intersection_failures"] or []), len(res["non_modular"] or []),
    sum(1 for a in aud.values() if not a["ok"]), len(res.get("door_void_violations") or [])))
hs, ss = Counter(), Counter()
for ci in range(13):
    for c in cch.get(ci, []):
        hs[c["logical_code"]] += 1
    for c in cc.get(ci, []):
        ss[c["logical_code"]] += 1
print("%-6s %-8s %-8s" % ("code", "humano", "solver"))
for cd in ("B39", "B34", "B19", "B54", "C09", "C04"):
    print("%-6s %-8d %-8d" % (cd, hs[cd], ss[cd]))
print("total  %-8d %-8d" % (sum(hs.values()), sum(ss.values())))
# juntas: coincidencia por parede (melhor paridade)
def joints_of(cands, wi):
    p0, d = frame(wi)
    ext = sorted(m._candidate_extent_on_wall_axis(c, p0, d) for c in cands if c["wall_idx"] == wi)
    return [(a1 + b0) / 2.0 for (a0, a1), (b0, b1) in zip(ext, ext[1:]) if -2.5 <= b0 - a1 <= 5.0]
def match(ja, jb):
    if not ja or not jb:
        return 1.0 if (not ja and not jb) else 0.0
    return sum(1 for x in ja if any(abs(x - y) <= 1.5 for y in jb)) / float(max(len(ja), len(jb)))
scores = []
for wi in range(len(walls)):
    h0, h1 = joints_of(cch.get(0, []), wi), joints_of(cch.get(1, []), wi)
    s0, s1 = joints_of(cc.get(0, []), wi), joints_of(cc.get(1, []), wi)
    same = (match(h0, s0) + match(h1, s1)) / 2.0
    cross = (match(h0, s1) + match(h1, s0)) / 2.0
    scores.append((max(same, cross), ids[wi], walls[wi][0].Length * F2CM, len(openings_per_wall[wi])))
scores.sort(reverse=True)
print("coincidencia de juntas c0/c1 (melhor paridade): media=%.2f | >=0.5: %d/%d" % (
    sum(s[0] for s in scores) / len(scores), sum(1 for s in scores if s[0] >= 0.5), len(scores)))
print("   melhores: %s" % [(round(s[0], 2), s[1], int(s[2]), s[3]) for s in scores[:6]])
print("   piores:   %s" % [(round(s[0], 2), s[1], int(s[2]), s[3]) for s in scores[-6:]])

print("\n=== (C) trecho ponta-livre -> 1o T (humano c0|c1), com as aberturas marcadas ===")
for n in nodes:
    if n["kind"] != "T_INTERSECTION":
        continue
    mi = n["main_wall_idx"]
    p0, d = frame(mi)
    L = walls[mi][0].Length * F2CM
    t = ((n["point"].X - p0.X) * d.X + (n["point"].Y - p0.Y) * d.Y) * F2CM
    for end, tt in ((0, t), (1, L - t)):
        if tt > 120 or e2n.get((mi, end)) is None or nodes[e2n[(mi, end)]]["kind"] != "FREE_END":
            continue
        ops_here = [(round(a * F2CM), round(b * F2CM)) for a, b, _s, _h in openings_per_wall[mi]]
        if end == 1:
            ops_here = [(round(L - b), round(L - a)) for a, b in ops_here]
        ops_here = [o for o in ops_here if o[0] <= tt + 30]
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
        print("   wall %d ponta%d->T em %.0fcm | aberturas ate' ai: %s | c0: %s | c1: %s" % (ids[mi], end, tt, ops_here, seqs[0], seqs[1]))
