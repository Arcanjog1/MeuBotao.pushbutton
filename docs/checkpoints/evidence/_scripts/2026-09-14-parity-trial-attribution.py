import sys
sys.path.insert(0, r"C:/Users/twitc/Documents/butanta-channel/MeuBotao.pushbutton/docs/checkpoints/evidence/_scripts")
import channel_bench_common as cb
from collections import Counter
m = cb.m
from benchmark import runner as brunner
from benchmark.extract import from_solver
masonry, ops = cb.load_inputs()
masonry = sorted(masonry, key=lambda w: (round(float(w["p0_cm"][0]), 1), round(float(w["p0_cm"][1]), 1), round(float(w["p1_cm"][0]), 1), round(float(w["p1_cm"][1]), 1)))
cat = dict(cb.CATALOG); cat.update(m.channel_logical_catalog())
def codes(res, label):
    ctx_local = CTX
    project = from_solver.project_from_solver(label, res, ctx_local["walls"], ctx_local["nodes"], ctx_local["openings_per_wall"], cat, 0.0, cb.NUM_COURSES)
    f, _s, _c = brunner.evaluate_project(project, None)
    return Counter(x["code"] for x in f)
orig_trials = m._channel_tie_parity_trials
variants = {"legacy": dict(strategy=None), "full": dict(strategy="CHANNEL"),
            "no_parity": dict(strategy="CHANNEL", no_parity=True), "no_ftt": dict(strategy="CHANNEL", policy={"free_to_top_tie_bounded_passages": False}),
            "neither": dict(strategy="CHANNEL", no_parity=True, policy={"free_to_top_tie_bounded_passages": False})}
out = {}
for name, v in variants.items():
    CTX = cb.build(masonry, ops)
    if v.get("no_parity"):
        m._channel_tie_parity_trials = lambda *a, **k: {"changed": False, "accepted": [], "rejected": [], "final_result": a[6]}
    else:
        m._channel_tie_parity_trials = orig_trials
    res = cb.solve(CTX, opening_reinforcement_strategy=v["strategy"], opening_reinforcement_policy=v.get("policy"))
    out[name] = codes(res, name)
    extra = res.get("channel_tie_parity_trials")
    print(name, "trials", extra)
base = out["legacy"]
for name in out:
    print(name, {c: out[name].get(c, 0) - base.get(c, 0) for c in sorted(set(out[name]) | set(base)) if out[name].get(c, 0) != base.get(c, 0)})
