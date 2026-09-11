import os, sys, time, json
ROOT = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "nuvem")); sys.path.insert(0, os.path.join(ROOT, "tests"))
from benchmark import runner, scoring
import load_script
m = load_script.load()
ws = sys.modules["core.engine.wall_stepper"]
PROJECT = sys.argv[1] if len(sys.argv) > 1 else "torre_easy_lo_r00_tgd"
base = json.load(open(runner.project_paths(PROJECT)["baseline"], encoding="utf-8"))
orig_clip = ws._clip_range_by_midspan_neighbours
orig_rej = ws._reject_overlapping_node_ties
orig_drop = m._drop_fill_colliding_with_ties
CONFIGS = [
    ("TUDO LIGADO (HEAD)", {}),
    ("sem clip (T vizinho)", {"clip": False}),
    ("sem reject (rede)", {"reject": False}),
    ("sem fileira B34 (flag)", {"b34": False}),
    ("sem boneca absorvida", {"boneca": False}),
    ("TUDO DESLIGADO (~base)", {"clip": False, "reject": False, "b34": False, "boneca": False}),
]
for label, cfg in CONFIGS:
    ws._clip_range_by_midspan_neighbours = orig_clip if cfg.get("clip", True) else (lambda w, n, wi, t, rng, exclude_node_index=None: rng)
    ws._reject_overlapping_node_ties = orig_rej if cfg.get("reject", True) else (lambda solved, failures: set())
    ws.PREFER_B34_ROW_OVER_STACKED_COMPENSATORS = cfg.get("b34", True)
    m._drop_fill_colliding_with_ties = orig_drop if cfg.get("boneca", True) else (lambda pieces, walls=None: orig_drop(pieces, None))
    t0 = time.time()
    try:
        out = runner.run_project(PROJECT, write_files=False)
        delta = scoring.compare_runs(base, out["score"])
        crit = [(r["code"], r["before"], r["after"]) for r in delta["critical"] if r["status"] != "OK" and r["before"] != r["after"]]
        cats = [(r.get("code") or r.get("category"), r.get("before"), r.get("after")) for r in delta["categories"] if r["status"] == scoring.STATUS_REGRESSED]
        print("%-26s %6.0fs veredito=%-22s criticos=%s regress_cat=%s" % (label, time.time()-t0, delta["verdict"], crit, cats), flush=True)
    except Exception as ex:
        print("%-26s ERRO %s" % (label, ex), flush=True)
