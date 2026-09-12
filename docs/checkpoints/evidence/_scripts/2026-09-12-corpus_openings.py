"""Uso: python3 corpus_openings.py <root> <label> [projects...]
Roda runner.run_project (write_files=False) e imprime criticos por codigo."""
import sys, os, json, time
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]
projects = sys.argv[3:] or ["torre_easy_lo_r00_tp1", "torre_easy_lo_r00_tgd"]
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner, scoring
out = {"label": label, "root": root, "projects": {}}
for pid in projects:
    t0 = time.time()
    r = runner.run_project(pid, write_files=False)
    sc = r["score"]
    base = runner._read_json(runner.project_paths(pid)["baseline"])
    delta = r.get("delta")
    entry = {
        "seconds": round(time.time() - t0, 1),
        "walls": sc["walls"], "blocks": sc["blocks"],
        "success_rate": sc["success_rate"], "critical_errors": sc["critical_errors"],
        "critical_by_code": sc["critical_by_code"],
        "baseline_critical_by_code": (base or {}).get("critical_by_code"),
        "delta_verdict": (delta or {}).get("verdict") if isinstance(delta, dict) else None,
    }
    # detalhe das invasoes de vao: parede/fiada/bloco
    inv = [f for f in r["findings"] if f.get("code") in ("OPENING_BLOCK_INSIDE_DOOR", "OPENING_BLOCK_INSIDE_WINDOW")]
    entry["inside_openings"] = [{k: f.get(k) for k in ("code", "wall", "row", "blocks", "block_t_cm", "opening_t_cm")} for f in inv]
    out["projects"][pid] = entry
    print(label, pid, json.dumps({k: entry[k] for k in ("seconds", "walls", "blocks", "critical_errors", "critical_by_code")}, ensure_ascii=False), flush=True)
    for f in entry["inside_openings"]:
        print("   ", json.dumps(f, ensure_ascii=False), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus_%s.json" % label), "w"), indent=1, ensure_ascii=False)
