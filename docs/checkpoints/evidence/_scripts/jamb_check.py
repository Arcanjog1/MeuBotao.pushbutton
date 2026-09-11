import os, sys, json, math
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SCALE_BENCH_TESTS", r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\tests")
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "with_openings.py")).read().split("print(\"\n=== (D) SOLVER")[0])
F2CM = 30.48
print("\n=== cada junta corrida HUMANA: distancia a borda de abertura mais proxima e as duas pecas encostadas (fiada 0 e 1) ===")
tot = Counter()
for wi, a in sorted(rep.items()):
    p0, d = frame(wi)
    edges = []
    for lo, hi, s_, h_ in openings_per_wall[wi]:
        edges += [lo * F2CM, hi * F2CM]
    for cj in a["continuous_joints"]:
        x = cj["x_cm"]
        dmin = min([abs(x - e) for e in edges] or [9999])
        desc = []
        for ci in (0, 1, 5):
            near = []
            for c in cch.get(ci, []):
                if c["wall_idx"] != wi: continue
                lo, hi = m._candidate_extent_on_wall_axis(c, p0, d)
                if abs(hi - x) < 2 or abs(lo - x) < 2:
                    near.append("%s[%.0f,%.0f]" % (c["logical_code"], lo, hi))
            desc.append("c%d:%s" % (ci, "+".join(sorted(near))))
        small = any(cd in ("C04", "C09") for cd in [s.split("[")[0].split(":")[-1] for s in desc])
        tag = "JAMBA(pastilha)" if (dmin <= 12 and small) else ("borda<=12" if dmin <= 12 else "LONGE da abertura")
        tot[tag] += 1
        print("  wall %d x=%7.1f fiadas=%2d dist_borda=%6.1f  %s  %s" % (ids[wi], x, len(cj["courses"]), dmin, tag, " ".join(desc)))
print("\nresumo: %s" % dict(tot))
