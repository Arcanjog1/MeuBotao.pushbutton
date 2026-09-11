import os, sys, time, json
ROOT = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "nuvem")); sys.path.insert(0, os.path.join(ROOT, "tests"))
from benchmark import runner, scoring
import load_script
m = load_script.load()
ws = sys.modules["core.engine.wall_stepper"]
PROJECT = "torre_easy_lo_r00_tp1"
base = json.load(open(runner.project_paths(PROJECT)["baseline"], encoding="utf-8"))
orig_clip = ws._clip_range_by_midspan_neighbours
orig_drop = m._drop_fill_colliding_with_ties
def clip_old_reserve(walls_to_create, nodes, wall_idx, t_ft, safe_range_ft, exclude_node_index=None):
    lo_ft, hi_ft = safe_range_ft
    for oi, other in enumerate(nodes or []):
        if oi == exclude_node_index or wall_idx not in ws._midspan_node_wall_ids(other): continue
        t_other = ws._t_of_point_on_wall(walls_to_create, wall_idx, other["point"])
        r = ws._cm_to_ft(ws._node_default_reservation_cm(walls_to_create, other))
        if t_other > t_ft + 1e-6: hi_ft = min(hi_ft, t_other - r)
        elif t_other < t_ft - 1e-6: lo_ft = max(lo_ft, t_other + r)
    return lo_ft, hi_ft
CONFIGS = [
    ("FINAL (HEAD 09ce2a7)", {}),
    ("rede LIGADA", {"reject": True}),
    ("clip reserva antiga (meia esp.)", {"clip": "old"}),
    ("sem clip", {"clip": "off"}),
    ("fileira B34 ligada", {"b34": True}),
    ("sem boneca absorvida", {"boneca": False}),
    ("tudo desligado (~base)", {"clip": "off", "boneca": False}),
]
for label, cfg in CONFIGS:
    c = cfg.get("clip", "new")
    ws._clip_range_by_midspan_neighbours = orig_clip if c == "new" else (clip_old_reserve if c == "old" else (lambda w, n, wi, t, rng, exclude_node_index=None: rng))
    ws.REJECT_OVERLAPPING_NODE_TIES = cfg.get("reject", False)
    ws.PREFER_B34_ROW_OVER_STACKED_COMPENSATORS = cfg.get("b34", False)
    m._drop_fill_colliding_with_ties = orig_drop if cfg.get("boneca", True) else (lambda pieces, walls=None: orig_drop(pieces, None))
    t0 = time.time()
    try:
        out = runner.run_project(PROJECT, write_files=False)
        delta = scoring.compare_runs(base, out["score"])
        crit = [(r["code"], r["before"], r["after"]) for r in delta["critical"] if r["before"] != r["after"]]
        cats = [(r.get("category"), r.get("before"), r.get("after")) for r in delta["categories"] if r["status"] == scoring.STATUS_REGRESSED]
        print("%-32s %5.0fs %-20s criticos=%s regress=%s" % (label, time.time()-t0, delta["verdict"], crit, cats), flush=True)
    except Exception as ex:
        print("%-32s ERRO %s" % (label, ex), flush=True)
