# -*- coding: utf-8 -*-
"""Contexto de cada no' T: o que o HUMANO poe (c0,c1) x o SOLVER, em funcao de
(a) a parede que chega ser alvenaria no projeto humano e (b) a distancia ao no'
vizinho mais proximo na parede principal. Medicao para decidir as regras 11.10
(amarracao que nao cabe) e o defeito 1 pela evidencia humana."""
import json, os, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault("SCALE_BENCH_TESTS", r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\tests")
import scale_bench as sbx
m = sbx.m; CATALOG = sbx.CATALOG; XYZ, Line = m.XYZ, m.Line; F2CM = 30.48
EV = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\docs\checkpoints\evidence"
walls_json = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json")))["walls"]
human = json.load(open(os.path.join(EV, "2026-09-10-butanta-human-sequences.json")))
blocks = json.load(open(os.path.join(EV, "2026-09-10-butanta-ref-1pav-blocks.json")))["blocks"]
CODEMAP = {"BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34", "MEIO BLOCO - 14x19x19": "B19",
           "BLOCO 54 - 14x19x54": "B54", "COMPENSADOR 14x19x9": "C09", "PASTILHA - 14x19X4": "C04"}
axes = []; ids = []
for w in walls_json:
    axes.append((Line.CreateBound(XYZ(*[float(v) for v in w["p0"]]), XYZ(*[float(v) for v in w["p1"]])), 14.0/100.0*m.FEET_PER_METER, (False, False))); ids.append(w["id"])
walls, jmap = m.extend_wall_ends_to_junctions(list(axes), m.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = m.build_wall_graph(walls, jmap)
res = m.solve_building_blocks_all_courses(nodes, walls, e2n, [[] for _ in walls], CATALOG, 0.0, 14, variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
cc = res["course_candidates"]
hcount = {ids[i]: sum(len(human["per_wall"].get(str(ids[i]), {}).get(str(c), [])) for c in range(13)) for i in range(len(ids))}
def human_at(px, py, course):
    out = []
    for b in blocks:
        bb = b.get("bb")
        if not bb or int(round((b["z"]-1.0)/20.0)) != course: continue
        if bb[0]-0.5 <= px <= bb[3]+0.5 and bb[1]-0.5 <= py <= bb[4]+0.5: out.append(CODEMAP.get(b["sym"], "?"))
    return tuple(sorted(out))
def solver_at(px, py, course):
    out = []
    for c in cc.get(course, []):
        o = c["origin_world"]; dx, dy = px/F2CM-o.X, py/F2CM-o.Y
        ax = abs(dx*c["x_dir"].X+dy*c["x_dir"].Y)*F2CM; ay = abs(dx*c["y_dir"].X+dy*c["y_dir"].Y)*F2CM
        if ax <= c["length_cm"]/2.0+0.5 and ay <= c["width_cm"]/2.0+0.5: out.append(c["logical_code"])
    return tuple(sorted(out))
tie_nodes = [n for n in nodes if n["kind"] in ("L_CORNER","T_INTERSECTION","X_INTERSECTION")]
groups = defaultdict(Counter)
print("%-14s %-24s %-22s %-9s %-7s %s" % ("no (x,y)", "HUMANO (c0,c1)", "SOLVER (c0,c1)", "chega_alv", "dmin", "principal len / chega len"))
for n in nodes:
    if n["kind"] != "T_INTERSECTION": continue
    px, py = n["point"].X*F2CM, n["point"].Y*F2CM
    mi, ii = n.get("main_wall_idx"), n.get("incoming_wall_idx")
    inc_m = (hcount.get(ids[ii], 0) >= 20) if ii is not None else None
    dmin = None
    if mi is not None:
        p0, _p1, d, _l, _t = m._wall_axis_and_length(walls, mi)
        for o in tie_nodes:
            if o is n: continue
            pt = o["point"]
            if abs((pt.X-p0.X)*d.Y-(pt.Y-p0.Y)*d.X)*F2CM > 1.0: continue
            dist = abs((pt.X-n["point"].X)*d.X+(pt.Y-n["point"].Y)*d.Y)*F2CM
            dmin = dist if dmin is None else min(dmin, dist)
    h = (human_at(px,py,0), human_at(px,py,1)); sv = (solver_at(px,py,0), solver_at(px,py,1))
    bucket = "sem vizinho" if dmin is None else ("<54" if dmin < 54 else ("<100" if dmin < 100 else ">=100"))
    groups[(inc_m, bucket)][("H", h)] += 1; groups[(inc_m, bucket)][("S", sv)] += 1
    print("(%5.0f,%5.0f) %-24s %-22s %-9s %-7s %.0f / %.0f" % (px, py, h, sv, inc_m, ("%.0f" % dmin) if dmin is not None else "-",
          walls[mi][0].Length*F2CM if mi is not None else -1, walls[ii][0].Length*F2CM if ii is not None else -1))
print("\n=== agrupado (parede que chega e' alvenaria no humano?, distancia ao no' vizinho na principal) ===")
for key in sorted(groups, key=str):
    print("-- chega_alvenaria=%s | vizinho %s --" % key)
    for (who, pt), nct in sorted(groups[key].items(), key=lambda x: (x[0][0], -x[1])):
        print("     %-6s x%-3d %s" % ("HUMANO" if who == "H" else "SOLVER", nct, pt))
