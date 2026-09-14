# -*- coding: utf-8 -*-
import json, sys, urllib.request, urllib.error, io, time
PORT = 48884
URL = "http://localhost:%d/revit_mcp/execute_code/" % PORT
def run(code, desc="q", timeout=900):
    payload = json.dumps({"code": code, "description": desc}).encode("utf-8")
    req = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
    t=time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8","replace")
    try: d = json.loads(raw)
    except Exception: return raw
    if d.get("status") == "error":
        sys.stderr.write("ERRO: %s\n%s\n" % (d.get("error"), d.get("traceback", "")[-4000:]))
        if d.get("partial_output"): sys.stderr.write("PARCIAL:\n%s\n" % d["partial_output"][-4000:])
        sys.exit(1)
    sys.stderr.write("[%.1fs]\n" % (time.time()-t))
    return d.get("output", "")
if __name__ == "__main__":
    with io.open(sys.argv[1], encoding="utf-8") as f: code = f.read()
    sys.stdout.write(run(code, desc=sys.argv[1]))
