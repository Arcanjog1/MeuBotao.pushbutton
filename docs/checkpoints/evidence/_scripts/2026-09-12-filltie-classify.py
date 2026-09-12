import sys, json, collections
path = sys.argv[1]; d = json.load(open(path)); walls = d["walls"]
BIND = ("L_binding", "T_binding", "cross_binding")
def binfo(w, bid):
    for row in walls[w]["rows"]:
        for b in row["blocks"]:
            if b[5] == bid: return b
def jkind(w, js):
    L = binfo(w, js["left_block"]); R = binfo(w, js["right_block"])
    lb = L[3] in BIND; rb = R[3] in BIND
    lo = L[3] == "opening_adjustment"; ro = R[3] == "opening_adjustment"
    if lb and rb: return "TT"
    if lb or rb: return "NF"   # node|fill boundary
    if lo or ro: return "OF"
    return "FF"
sig = collections.Counter(); detail = collections.defaultdict(list)
for f in d["findings"]:
    if f["code"] != "PRISM_CONTINUOUS_JOINT": continue
    w = f["wall"]; ka = jkind(w, f["joint_a"]); kb = jkind(w, f["joint_b"])
    key = (w, f["joint_t_cm"], ka+"x"+kb, f["joint_a"]["left_code"]+"|"+f["joint_a"]["right_code"], f["joint_b"]["left_code"]+"|"+f["joint_b"]["right_code"])
    sig[key] += 1; detail[key].append((f["row_a"], f["row_b"]))
print(d["project"], "PRISM_CONTINUOUS_JOINT", sum(sig.values()))
pair = collections.Counter()
for k, n in sig.items(): pair[k[2]] += n
print("pairs:", dict(pair))
for k in sorted(sig): print(" ", k, sig[k], "rows", detail[k][:3], "..." if len(detail[k])>3 else "", "len", walls[k[0]]["length_cm"])
