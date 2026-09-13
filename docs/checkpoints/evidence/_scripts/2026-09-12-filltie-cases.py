"""Tabela dos casos fill|tie (NF x NF) por CHAVE FISICA da parede: nó, tipo, fiadas, peças, juntas."""
import sys, os, json, collections
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]; pid = sys.argv[3]; version = sys.argv[4]
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner, solver_bridge, model
from nuvem.benchmark.extract import from_solver
paths = runner.project_paths(pid, version)
inp = runner._read_json(paths["input"]) or runner._read_json(runner.project_paths(pid)["input"])
# Replica `model.assign_ids` sobre as paredes do SOLVER (walls_to_create): o
# resultado do benchmark reatribui W0xx pela ordem geometrica dessas paredes.
_nodes, walls_to_create, _e2n, _op = solver_bridge.plan_from_input(inp)
geo = []
for wi in range(len(walls_to_create)):
    start, end, thick = from_solver._wall_geometry_cm(walls_to_create, wi)
    geo.append({"start_cm": start, "end_cm": end, "thickness_cm": thick, "solver_idx": wi})
geo.sort(key=lambda w: (round(w["start_cm"][1], 1), round(w["start_cm"][0], 1), round(w["end_cm"][1], 1), round(w["end_cm"][0], 1)))
keys = {}
for i, w in enumerate(geo):
    keys["W%03d" % (i + 1)] = (model.wall_stable_key(w["start_cm"], w["end_cm"], w["thickness_cm"]), w["start_cm"], w["end_cm"], w["solver_idx"])
S = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(S, "findings_%s_%s_%s.json" % (label, pid, version))))
walls = d["walls"]
BIND = ("L_binding", "T_binding", "cross_binding")
def binfo(w, bid):
    for row in walls[w]["rows"]:
        for b in row["blocks"]:
            if b[5] == bid: return b
def jkind(w, js):
    L = binfo(w, js["left_block"]); R = binfo(w, js["right_block"])
    lb = L[3] in BIND; rb = R[3] in BIND
    if lb and rb: return "TT"
    if lb or rb: return "NF"
    if L[3] == "opening_adjustment" or R[3] == "opening_adjustment": return "OF"
    return "FF"
rows = collections.OrderedDict()
for f in d["findings"]:
    if f["code"] != "PRISM_CONTINUOUS_JOINT": continue
    w = f["wall"]; ka = jkind(w, f["joint_a"]); kb = jkind(w, f["joint_b"])
    cat = "A_fill|tie" if {ka, kb} == {"NF"} else ("B_fill|fill" if {ka, kb} == {"FF"} else ("C_tie|tie" if "TT" in (ka, kb) and "OF" not in (ka, kb) else ("D_abertura" if "OF" in (ka, kb) else "G_outro")))
    if "OF" in (ka, kb): cat = "D_abertura"
    elif {ka, kb} == {"NF"}: cat = "A_fill|tie"
    elif {ka, kb} == {"FF"}: cat = "B_fill|fill"
    elif "TT" in (ka, kb): cat = "C_tie|tie"
    else: cat = "G_outro"
    key = (w, round(f["joint_t_cm"], 1), cat)
    r = rows.setdefault(key, {"pairs": [], "ja": [], "jb": []})
    r["pairs"].append((f["row_a"], f["row_b"]))
    r["ja"].append("%s|%s" % (f["joint_a"]["left_code"], f["joint_a"]["right_code"]))
    r["jb"].append("%s|%s" % (f["joint_b"]["left_code"], f["joint_b"]["right_code"]))
total = collections.Counter()
print("## %s %s (%s) — PRISM_CONTINUOUS_JOINT por parede/junta" % (label, pid, version))
print("| W0xx | idx solver | chave física | comp. cm | t junta | categoria | pares de fiadas | junta A (ex.) | junta B (ex.) | aberturas | placement das peças |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for (w, t, cat), r in rows.items():
    total[cat] += len(r["pairs"])
    k, _s, _e, sidx = keys.get(w, (None, None, None, None))
    ops = ";".join("%s[%g,%g]" % (o["kind"], o["t_start_cm"], o["t_end_cm"]) for o in walls[w].get("openings") or [])
    pl = set()
    for row in walls[w]["rows"]:
        for b in row["blocks"]:
            if abs((b[1] + b[2]) / 2 - t) < 30 and b[4] != "STANDARD_FILL": pl.add("%s@%s[%g,%g]" % (b[0], b[4], b[1], b[2]))
    print("| %s | %s | `%s` | %.1f | %.1f | %s | %d (%s…) | %s | %s | %s | %s |" % (w, sidx, k, walls[w]["length_cm"], t, cat, len(r["pairs"]), ",".join("%d-%d" % p for p in r["pairs"][:3]), r["ja"][0], r["jb"][0], ops or "-", "; ".join(sorted(pl))[:120]))
print("\nTotais:", dict(total), "PRISM_CONTINUOUS_JOINT =", sum(total.values()))
