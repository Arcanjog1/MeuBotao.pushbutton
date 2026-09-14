import sys, time, cProfile, pstats, io
sys.path.insert(0, r"C:/Users/twitc/Documents/butanta-channel/MeuBotao.pushbutton/docs/checkpoints/evidence/_scripts")
import channel_bench_common as cb
m = cb.m
masonry, ops = cb.load_inputs()
masonry = sorted(masonry, key=lambda w: (round(float(w["p0_cm"][0]), 1), round(float(w["p0_cm"][1]), 1), round(float(w["p1_cm"][0]), 1), round(float(w["p1_cm"][1]), 1)))
stats = {}
def wrap(name, fn):
    def inner(*a, **k):
        t0 = time.time()
        try:
            return fn(*a, **k)
        finally:
            s = stats.setdefault(name, [0, 0.0]); s[0] += 1; s[1] += time.time() - t0
    return inner
for name in ("_solve_building_blocks_all_courses_core", "_channel_tie_parity_trials", "_channel_plan_metrics",
             "_channel_trial_joint_quality", "search_tie_parity", "repair_arm_role_isolated_edges",
             "repair_b19_residual_fill", "_apply_opening_reinforcement", "_unify_candidates_with_courses",
             "audit_all_walls_bond_quality"):
    if hasattr(m, name):
        setattr(m, name, wrap(name, getattr(m, name)))
from core.engine import opening_reinforcement as orf
for name in ("plan_channel_reinforcement", "validate_channel_reinforcement", "_wall_strip_pieces", "free_to_top_openings", "continuous_free_passages"):
    setattr(orf, name, wrap("orf." + name, getattr(orf, name)))
mode = sys.argv[1]
ctx = cb.build(masonry, ops)
t0 = time.time()
if mode == "profile":
    pr = cProfile.Profile(); pr.enable()
res = cb.solve(ctx, opening_reinforcement_strategy=None if mode == "legacy" else "CHANNEL")
if mode == "profile":
    pr.disable(); s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(35); print(s.getvalue()[:6000])
print(mode, "total %.2f s" % (time.time() - t0))
for k, v in sorted(stats.items(), key=lambda kv: -kv[1][1]):
    print("  %-45s calls %5d  %.2f s" % (k, v[0], v[1]))
print(res.get("channel_tie_parity_trials"))
