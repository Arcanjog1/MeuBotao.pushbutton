import json, sys
# compensador (C04/C09) logo atras de um bloco que encosta no vao (pastilha fora da face)
d = json.load(open(sys.argv[1]))
W = {}
for k, v in d["rows"].items():
    w, c = [int(x) for x in k.split(":")]
    W.setdefault(w, {})[c] = sorted(v)
out = []
for w, rows in W.items():
    for c, items in rows.items():
        zc = c * 20 + 10
        for o in d["openings"][w]:
            if not (o[2] - 1 <= zc <= o[3] + 1):
                continue
            for e, dirn in ((o[0], -1), (o[1], +1)):
                seq = [it for it in items if (it[1] <= e + 1.5 if dirn < 0 else it[0] >= e - 1.5)]
                seq = sorted(seq, key=lambda it: -it[1] if dirn < 0 else it[0])
                if len(seq) < 2:
                    continue
                a, b = seq[0], seq[1]
                face = a[1] if dirn < 0 else a[0]
                if abs(face - e) > 1.5:
                    continue
                gap = (a[0] - b[1]) if dirn < 0 else (b[0] - a[1])
                if gap > 2.5:
                    continue
                if a[2] in ("B19", "B39", "B34") and b[2] in ("C04", "C09"):
                    out.append((w, c, round(e), a[2], b[2]))
by = {}
for x in out:
    by.setdefault((x[0], x[2]), []).append(x)
print("compensador logo atras de bloco encostado no vao:", len(out))
for k, v in sorted(by.items()):
    print("  W%d jamba %d fiadas %s (%s|%s)" % (k[0], k[1], sorted(x[1] for x in v), v[0][3], v[0][4]))
