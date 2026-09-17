"""Prove this mission leaves the host, solver and physical rules unchanged."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = "ca301c34da730b8fea7ef5bd7256a36f81a51e42"
changed = subprocess.check_output(["git", "diff", "--name-only", BASE], cwd=ROOT, text=True).splitlines()
allowed = {"nuvem/core/ui_components.py", "nuvem/core/ui_execution.py", "tests/test_ui_redesign.py"}
unexpected = [p for p in changed if p not in allowed and not p.startswith(("docs/", "tools/documentation/"))]
print(json.dumps(dict(baseline=BASE, changed=changed, unexpected=unexpected,
                     host_solver_rules_unchanged=not unexpected), indent=2))
raise SystemExit(bool(unexpected))
