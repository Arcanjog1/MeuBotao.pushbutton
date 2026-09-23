# -*- coding: utf-8 -*-
"""Compara duas provas de cobertura: uso cov_diff.py A B [run]"""
import collections, json, sys
A = json.load(open("cov_%s.json" % sys.argv[1], encoding="utf-8"))
B = json.load(open("cov_%s.json" % sys.argv[2], encoding="utf-8"))
runs = [sys.argv[3]] if len(sys.argv) > 3 else sorted(A["runs"])
for run in runs:
    a, b = A["runs"][run], B["runs"][run]
    print("=====", run, a["verdict"], "->", b["verdict"])
    unc_a = sum(r[1] for w in a["walls"].values() for r in w["rows"].values())
    unc_b = sum(r[1] for w in b["walls"].values() for r in w["rows"].values())
    exp_a = sum(r[0] for w in a["walls"].values() for r in w["rows"].values())
    exp_b = sum(r[0] for w in b["walls"].values() for r in w["rows"].values())
    print("cm modulavel descoberto: %.0f -> %.0f   (modulavel %.0f -> %.0f)" % (unc_a, unc_b, exp_a, exp_b))
    codes = sorted(set(a["findings"]) | set(b["findings"]))
    for c in codes:
        na, nb = len(a["findings"].get(c, [])), len(b["findings"].get(c, []))
        if na != nb:
            print("   %-40s %5d -> %5d" % (c, na, nb))
    me_a = set(tuple(x) for x in a["findings"].get("COVERAGE_ROW_MOSTLY_EMPTY", []))
    me_b = set(tuple(x) for x in b["findings"].get("COVERAGE_ROW_MOSTLY_EMPTY", []))
    pw_a = set(x[0] for x in a["findings"].get("COVERAGE_PARTIAL_WALL", []))
    new = me_b - me_a
    gone = me_a - me_b
    print("MOSTLY_EMPTY novos %d, sumidos %d" % (len(new), len(gone)))
    cls = collections.Counter()
    for wall, row in sorted(new, key=str):
        wa, wb = a["walls"].get(str(wall)), b["walls"].get(str(wall))
        ra = wa["rows"].get(str(row)) if wa else None
        rb = wb["rows"].get(str(row)) if wb else None
        was_partial = wall in pw_a
        better = ra is not None and rb is not None and rb[1] <= ra[1] + 0.5
        key = ("parede_era_PARTIAL" if was_partial else "parede_nao_era_partial",
               "fiada_igual_ou_melhor" if better else ("fiada_pior" if ra is not None else "fiada_nova"))
        cls[key] += 1
        if key[1] != "fiada_igual_ou_melhor":
            print("   novo", wall, row, "antes", ra, "depois", rb, "PARTIAL antes" if was_partial else "")
    print("classes:", dict(cls))
    # paredes com mais descoberto
    worse = []
    for wid, wb in b["walls"].items():
        wa = a["walls"].get(wid)
        if not wa:
            continue
        ua = sum(r[1] for r in wa["rows"].values()); ub = sum(r[1] for r in wb["rows"].values())
        if ub > ua + 1:
            worse.append((round(ub - ua), wid, round(ua), round(ub)))
    print("paredes com MAIS descoberto:", sorted(worse, reverse=True)[:15])
    print("paredes piores:", len(worse))
