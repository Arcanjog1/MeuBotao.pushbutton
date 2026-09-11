# -*- coding: utf-8 -*-
"""Mede TIE_PARITY_LOCAL_SEARCH off x on: Butanta (34 paredes, vaos reais) e
Torre (179 eixos)."""
import json
import os
import sys
import time
from collections import Counter

ROOT = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "docs", "checkpoints", "evidence", "_scripts"))
os.environ.setdefault("SCALE_BENCH_TESTS", os.path.join(ROOT, "tests"))
src = open(os.path.join(ROOT, "docs", "checkpoints", "evidence", "_scripts", "with_openings.py"), encoding="utf-8").read()
exec(src.split('print("\\n=== (B) AUDITOR')[0])   # walls, nodes, e2n, openings_per_wall, m, CATALOG, ids
import core.engine.wall_stepper as ws  # noqa: E402
import scale_bench as sbx  # noqa: E402


def summarize(res, walls_):
    res["num_courses"] = 14
    aud = res["wall_bond_audits"]
    rep = [wi for wi, a in aud.items() if not a["ok"]]
    kinds = Counter(str(p).split(":")[0] for wi in rep for p in aud[wi]["problems"])
    cc = res["course_candidates"]
    comp = sum(1 for v in cc.values() for c in v if c["logical_code"] in ("C09", "C04"))
    return rep, dict(kinds), comp, sum(len(v) for v in cc.values()), len(res["non_modular"] or []), len(res["collisions"] or [])


print("=== BUTANTA 34 paredes, vaos reais, regra #2 intacta (fileira B34 OFF) ===")
for flag in (False, True):
    for n in nodes:
        n.pop("_tie_parity_flip", None)
    t0 = time.time()
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings_per_wall, CATALOG, 0.0, 14,
                                              variants_per_course=1, tie_parity_search=flag)
    dt = time.time() - t0
    rep, kinds, comp, pieces, nmod, col = summarize(res, walls)
    pf = m.controlled_beta_preflight(res, walls, openings_per_wall, CATALOG, 0.0)
    ts = res.get("tie_parity_search", {})
    print("  paridade=%-5s %6.1fs reprovadas=%2d %s comp=%d pecas=%d nmod=%d col=%d pf=%s flips=%s tried=%s" % (
        flag, dt, len(rep), [ids[w] for w in rep], comp, pieces, nmod, col, pf["ok"], ts.get("flips"), ts.get("tried")))
    print("     tipos: %s" % kinds)

print("\n=== TORRE 179 eixos (0 aberturas) ===")
axes, meta = sbx.load_axes(os.path.join(ROOT, "docs", "checkpoints", "evidence", "2026-09-10-scale-autofix-axes.json"))
for flag in (False, True):
    ws.TIE_PARITY_LOCAL_SEARCH = flag
    t0 = time.time()
    o = sbx.run_subset(axes, list(range(len(axes))), meta, "torre")
    dt = time.time() - t0
    print("  paridade=%-5s %6.1fs verdict=%s pecas=%s bond=%s ifail=%s nmod=%s col=%s pf=%s" % (
        flag, dt, o["verdict"], o.get("pieces"), o.get("bond_reproved"), o.get("intersection_failures"),
        o.get("non_modular"), o.get("collisions"), o.get("preflight_ok")))
ws.TIE_PARITY_LOCAL_SEARCH = False
