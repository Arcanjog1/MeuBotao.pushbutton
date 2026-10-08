import json, sys
# 86.12/86.14: junta de canaleta caindo no meio de um BLOCO INTEIRO (B39/B34) da fiada c-2 = prisma quebrado.
# Sobre meio bloco / compensador / B54 / U_CUT de c-2 (pecas moles) a canaleta pode passar (86.14).
d = json.load(open(sys.argv[1]))
W = {}
for k, v in d["rows"].items():
    w, c = [int(x) for x in k.split(":")]
    W.setdefault(w, {})[c] = sorted(v)
HARD = ("B39", "B34", "CHANNEL_U_39", "CHANNEL_U_34")
bad = []
for w, rows in W.items():
    for c, items in rows.items():
        r = rows.get(c - 2)
        if not r:
            continue
        for it in items:
            if not it[2].startswith("CHANNEL"):
                continue
            for e in (it[0], it[1]):
                host = [x for x in r if x[0] + 1.5 < e < x[1] - 1.5 and x[2] in HARD]
                if host:
                    bad.append((w, c, it[2].replace("CHANNEL_U_", "U"), round(e), host[0][2], round(host[0][0]), round(host[0][1])))
print("juntas de canaleta no meio de BLOCO INTEIRO da fiada c-2:", len(bad))
by = {}
for b in bad:
    by[(b[0], b[1])] = by.get((b[0], b[1]), 0) + 1
print("  por parede:fiada:", sorted(by.items()))
for b in bad[:30]:
    print("  ", b)
