import sys, hashlib, json
sys.path.insert(0, r"C:/Users/twitc/Documents/butanta-channel/MeuBotao.pushbutton/docs/checkpoints/evidence/_scripts")
import channel_bench_common as cb
m = cb.m
from core.engine import opening_reinforcement as orf
def sig(res):
    rows = []
    for ci in sorted(res["course_candidates"]):
        for c in res["course_candidates"][ci]:
            rows.append("%d|%s" % (ci, orf._physical_key(c)))
    extra = json.dumps({"val": res["opening_reinforcement"]["validation"]["counts"],
                        "openings": res["opening_reinforcement"]["openings"],
                        "trials": [res["channel_tie_parity_trials"]["accepted"], res["channel_tie_parity_trials"]["rejected"]],
                        "nonmod": len(res["non_modular"]), "coll": len(res["collisions"]),
                        "bond": sorted((k, a["ok"], a["problems"]) for k, a in res["wall_bond_audits"].items())},
                       sort_keys=True, default=str)
    return hashlib.sha256(("\n".join(sorted(rows)) + extra).encode()).hexdigest()
masonry, ops = cb.load_inputs()
masonry = sorted(masonry, key=lambda w: (round(float(w["p0_cm"][0]), 1), round(float(w["p0_cm"][1]), 1), round(float(w["p1_cm"][0]), 1), round(float(w["p1_cm"][1]), 1)))
out = []
for label, fn in (("memo", m.solve_building_blocks_all_courses), ("no_memo", m._solve_building_blocks_all_courses_impl)):
    ctx = cb.build(masonry, ops)
    res = fn(ctx["nodes"], ctx["walls"], ctx["e2n"], ctx["openings_per_wall"], cb.CATALOG, 0.0, cb.NUM_COURSES,
             variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE, opening_reinforcement_strategy="CHANNEL")
    out.append((label, sig(res)))
    print(label, out[-1][1], res["channel_tie_parity_trials"].get("wall_fill_memo"))
print("IDENTICAL", out[0][1] == out[1][1])
