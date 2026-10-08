import json, sys
# juntas de canaleta caindo NO MEIO de uma peca da fiada c-2 (prisma quebrado pela canaleta)
d = json.load(open(sys.argv[1]))
W = {}
for k, v in d["rows"].items():
    w, c = [int(x) for x in k.split(":")]
    W.setdefault(w, {})[c] = sorted(v)
bad = []
u19 = 0
for w, rows in W.items():
    for c, items in rows.items():
        for it in items:
            if it[2] == "CHANNEL_U_19":
                u19 += 1
        r = rows.get(c - 2)
        if not r:
            continue
        for it in items:
            if not it[2].startswith("CHANNEL"):
                continue
            for e in (it[0], it[1]):
                host = [x for x in r if x[0] + 1.5 < e < x[1] - 1.5]
                if not host:
                    continue
                bad.append((w, c, it[2].replace("CHANNEL_U_", "U"), round(e), host[0][2], round(host[0][0]), round(host[0][1])))
by = {}
for b in bad:
    by[(b[0], b[1])] = by.get((b[0], b[1]), 0) + 1
print("juntas de canaleta caindo NO MEIO de uma peca da fiada c-2:", len(bad), "| meias canaletas U19:", u19)
print("  por parede:fiada:", sorted(by.items()))
for b in bad[:25]:
    print("  ", b)
