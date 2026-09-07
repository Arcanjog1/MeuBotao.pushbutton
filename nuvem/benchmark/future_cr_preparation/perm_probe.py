"""Invariancia a PERMUTACAO da ordem das paredes na entrada.
Separa dependencia PRE-EXISTENTE (aparece em STATE_A) de dependencia NOVA
(so' aparece em STATE_C)."""
import hashlib, json, os, random, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,ROOT)
from nuvem.benchmark import runner, solver_bridge
from nuvem.benchmark.extract import from_solver

def phys_fp(project):
    rows=[]
    for w in project.get("walls") or []:
        for row in w.get("rows") or []:
            for b in row.get("blocks") or []:
                c=b.get("center_cm") or [0,0]
                rows.append((b.get("code"), round(float(c[0]),2), round(float(c[1]),2),
                             round(float(b.get("z_cm") or 0),2)))
    rows.sort()
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()[:16], len(rows)

pid=sys.argv[1]; n=int(sys.argv[2])
base=json.load(open(runner.project_paths(pid)["input"],encoding="utf-8"))
res=[]
for k in range(n):
    p=json.loads(json.dumps(base))
    if k>0:
        rnd=random.Random(1000+k); rnd.shuffle(p["walls"])
    r=solver_bridge.run_solver(p)
    proj=from_solver.project_from_solver(pid,r[0],r[1],r[2],r[3],r[4],r[5],r[6],metadata={})
    fp,nb=phys_fp(proj)
    res.append((k,fp,nb))
    print(f"   perm {k}: fp_fisico={fp} blocos={nb}")
uniq={f for _,f,_ in res}
print(f"  >>> {len(uniq)} fingerprint(s) distinto(s) em {n} permutacoes -> "
      + ("INVARIANTE" if len(uniq)==1 else "DEPENDE DA ORDEM"))
