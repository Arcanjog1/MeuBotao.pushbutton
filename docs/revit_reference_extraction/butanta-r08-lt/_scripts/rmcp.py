# -*- coding: utf-8 -*-
"""Cliente HTTP para o pyRevit Routes (revit_mcp) na porta 48885."""
import json, sys, urllib.request, io

PORT = 48885
URL = "http://localhost:%d/revit_mcp/execute_code/" % PORT

def run(code, desc="extract", timeout=600):
    payload = json.dumps({"code": code, "description": desc}).encode("utf-8")
    req = urllib.request.Request(URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
    try:
        d = json.loads(raw)
    except Exception:
        return raw
    if d.get("status") == "error":
        sys.stderr.write("ERRO: %s\n%s\n" % (d.get("error"), d.get("traceback", "")[-3000:]))
        if d.get("partial_output"):
            sys.stderr.write("PARCIAL:\n%s\n" % d["partial_output"][-3000:])
        sys.exit(1)
    return d.get("output", "")

if __name__ == "__main__":
    path = sys.argv[1]
    with io.open(path, encoding="utf-8") as f:
        code = f.read()
    out = run(code, desc=path)
    sys.stdout.write(out if isinstance(out, str) else str(out))
