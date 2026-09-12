"""Uso: python3 findings_dump.py <root> <label> <project>
Roda o projeto e grava TODOS os achados + contagem por parede/codigo em JSON."""
import sys, os, json, time
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]; pid = sys.argv[3]
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner
t0 = time.time()
r = runner.run_project(pid, write_files=False)
by_wall = {}
for f in r["findings"]:
    by_wall.setdefault(f.get("wall"), {}).setdefault(f.get("code"), 0)
    by_wall[f.get("wall")][f.get("code")] += 1
out = {"label": label, "project": pid, "seconds": round(time.time()-t0,1), "critical_by_code": r["score"]["critical_by_code"],
       "by_wall": by_wall, "findings": r["findings"],
       "walls": {w["id"]: {"rows": [{"row": row["row"], "blocks": [[b["code"], round(b["t_start_cm"],1), round(b["t_end_cm"],1), b.get("role"), b.get("placement_reason")] for b in row["blocks"]]} for row in w["rows"]], "openings": w.get("openings"), "junctions": w.get("junctions")} for w in r["result"]["walls"]}}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "findings_%s_%s.json" % (label, pid)), "w"), ensure_ascii=False)
print(label, pid, out["seconds"], json.dumps(out["critical_by_code"]))
