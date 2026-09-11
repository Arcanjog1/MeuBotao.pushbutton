import os, sys, time
from collections import Counter
ROOT = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
sys.path.insert(0, os.path.join(ROOT, "tests")); sys.path.insert(0, os.path.join(ROOT, "docs", "checkpoints", "evidence", "_scripts"))
os.environ.setdefault("SCALE_BENCH_TESTS", os.path.join(ROOT, "tests"))
src = open(os.path.join(ROOT, "docs", "checkpoints", "evidence", "_scripts", "with_openings.py"), encoding="utf-8").read()
exec(src.split('print("\n=== (B) AUDITOR')[0])
import core.engine.wall_stepper as ws
import scale_bench as sbx
for parity in (False, True):
    for n in nodes: n.pop("_tie_parity_flip", None)
    t0 = time.time()
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings_per_wall, CATALOG, 0.0, 14, variants_per_course=1, tie_parity_search=parity)
    res["num_courses"] = 14
    aud = res["wall_bond_audits"]; rep = [wi for wi, a in aud.items() if not a["ok"]]
    kinds = Counter(str(p).split(":")[0] for wi in rep for p in aud[wi]["problems"])
    cc = res["course_candidates"]; comp = sum(1 for v in cc.values() for c in v if c["logical_code"] in ("C09", "C04"))
    pf = m.controlled_beta_preflight(res, walls, openings_per_wall, CATALOG, 0.0)
    print("BUTANTA paridade=%-5s %6.1fs reprovadas=%2d %s comp=%d nmod=%d col=%d pf=%s flips=%s" % (parity, time.time()-t0, len(rep), [ids[w] for w in rep], comp, len(res["non_modular"] or []), len(pf["collisions"]), pf["ok"], (res.get("tie_parity_search") or {}).get("flips")))
    print("   tipos: %s" % dict(kinds))
axes, meta = sbx.load_axes(os.path.join(ROOT, "docs", "checkpoints", "evidence", "2026-09-10-scale-autofix-axes.json"))
for parity in (False, True):
    ws.TIE_PARITY_LOCAL_SEARCH = parity
    t0 = time.time(); o = sbx.run_subset(axes, list(range(len(axes))), meta, "torre")
    print("TORRE paridade=%-5s %6.1fs pecas=%s bond=%s ifail=%s nmod=%s col=%s pf=%s" % (parity, time.time()-t0, o.get("pieces"), o.get("bond_reproved"), o.get("intersection_failures"), o.get("non_modular"), o.get("collisions"), o.get("preflight_ok")))
ws.TIE_PARITY_LOCAL_SEARCH = False
