"""Fingerprint canonico do resultado do solver (mesma funcao do manifest V2) - 1 processo."""
import sys, os, time, json
root = os.path.abspath(sys.argv[1]); pid = sys.argv[2]; version = sys.argv[3]
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner
from nuvem.benchmark.golden import fingerprint as fingerprint_module
t0 = time.time()
r = runner.run_project(pid, write_files=False, version=version)
print(json.dumps({"project": pid, "version": version, "pid_os": os.getpid(), "seconds": round(time.time() - t0, 1),
                  "result_fingerprint": fingerprint_module.canonical_fingerprint(r["result"]),
                  "critical_by_code": r["score"]["critical_by_code"], "blocks": r["score"].get("blocks")}))
