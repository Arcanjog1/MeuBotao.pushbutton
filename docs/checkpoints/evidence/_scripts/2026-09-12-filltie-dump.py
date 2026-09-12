"""Uso: python3 dump.py <root> <label> <project> [version]
Roda o projeto e grava achados + geometria por parede em JSON."""
import sys, os, json, time
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]; pid = sys.argv[3]
version = sys.argv[4] if len(sys.argv) > 4 else None
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner
t0 = time.time()
r = runner.run_project(pid, write_files=False, version=version)
secs = round(time.time()-t0, 1)
by_wall = {}
for f in r["findings"]:
    by_wall.setdefault(f.get("wall"), {}).setdefault(f.get("code"), 0)
    by_wall[f.get("wall")][f.get("code")] += 1
out = {"label": label, "project": pid, "version": version, "seconds": secs,
       "critical_by_code": r["score"]["critical_by_code"],
       "score": {k: v for k, v in r["score"].items() if k != "per_wall"},
       "by_wall": by_wall, "findings": r["findings"],
       "walls": {w["id"]: {"length_cm": w.get("length_cm"), "start": w.get("start"), "end": w.get("end"),
                           "rows": [{"row": row["row"], "blocks": [[b["code"], round(b["t_start_cm"],2), round(b["t_end_cm"],2), b.get("role"), b.get("placement_reason"), b.get("id")] for b in row["blocks"]]} for row in w["rows"]],
                           "openings": w.get("openings"), "junctions": w.get("junctions")} for w in r["result"]["walls"]}}
outdir = os.path.dirname(os.path.abspath(__file__))
json.dump(out, open(os.path.join(outdir, "findings_%s_%s%s.json" % (label, pid, "_"+version if version else "")), "w"), ensure_ascii=False)
print(label, pid, version, secs, json.dumps(r["score"]["critical_by_code"]))
