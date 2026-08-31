# -*- coding: utf-8 -*-
"""ETAPA 2F - itens F/G/H/N/20 do pedido: MENOR caso real divergente,
TRACE passo a passo e propriedades matematicas da relacao de cluster.

Le `out_c_merge_isolate.json` (bloco divergente encontrado no projeto real),
reduz o caso ate' o menor subconjunto de segmentos que AINDA reproduz a
divergencia e imprime o trace das duas ordens.

    py -3 nuvem/benchmark/diagnostics_2f/run_d_min_case.py
"""
import itertools
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def relation_matrix(lines, labels):
    mod = L.load()["mod"]
    n = len(lines)
    caches = [mod._line_geom_cache(l) for l in lines]
    rows = []
    for a in range(n):
        for b in range(n):
            par = mod._are_parallel_cached(caches[a], caches[b])
            d = mod._distance_between_parallel_cached(caches[a], caches[b])
            rows.append(dict(a=labels[a], b=labels[b], parallel=par,
                             d_cm=round(L.cm(d), 6),
                             compat=bool(par and d <= mod.COLLINEAR_MATCH_TOLERANCE_FT)))
    return rows


def properties(lines, labels):
    mod = L.load()["mod"]
    n = len(lines)
    caches = [mod._line_geom_cache(l) for l in lines]
    tolf = mod.COLLINEAR_MATCH_TOLERANCE_FT

    def R(a, b):
        return (mod._are_parallel_cached(caches[a], caches[b]) and
                mod._distance_between_parallel_cached(caches[a], caches[b]) <= tolf)

    refl = all(R(a, a) for a in range(n))
    asym, nontrans = [], []
    for a in range(n):
        for b in range(n):
            if a != b and R(a, b) != R(b, a):
                asym.append((labels[a], labels[b]))
    for a in range(n):
        for b in range(n):
            for c in range(n):
                if a in (b, c) or b == c:
                    continue
                if R(a, b) and R(b, c) and not R(a, c):
                    nontrans.append((labels[a], labels[b], labels[c]))
    return dict(reflexive=refl, symmetric=(not asym), transitive=(not nontrans),
                asymmetric_pairs=asym[:20], asymmetric_count=len(asym),
                nontransitive_triples=nontrans[:20], nontransitive_count=len(nontrans))


def trace(lines, labels, order):
    """Trace passo a passo do agrupamento (passada 1) para UMA ordem."""
    mod = L.load()["mod"]
    tolf = mod.COLLINEAR_MATCH_TOLERANCE_FT
    seq = [(labels[k], lines[k]) for k in order]
    remaining = [(lb, l, mod._line_geom_cache(l)) for lb, l in seq]
    steps, clusters = [], []
    while remaining:
        blb, base, bc = remaining.pop(0)
        cluster = [(blb, base)]
        rest = []
        for olb, other, oc in remaining:
            par = mod._are_parallel_cached(bc, oc)
            d = mod._distance_between_parallel_cached(bc, oc)
            take = bool(par and d <= tolf)
            steps.append(dict(base=blb, cand=olb, parallel=par,
                              perp_cm=round(L.cm(d), 6),
                              tol_cm=round(L.cm(tolf), 6), merge=take,
                              cluster_after=[x[0] for x in cluster] + ([olb] if take else [])))
            (cluster if take else None)
            if take:
                cluster.append((olb, other))
            else:
                rest.append((olb, other, oc))
        remaining = rest
        clusters.append(cluster)
    merged_lines = []
    per_cluster = []
    for c in clusters:
        outs = L.merge_cluster([l for _, l in c], ops=[])
        merged_lines.extend(outs)
        per_cluster.append(dict(members=[lb for lb, _ in c],
                                out=L.canon_set(outs, 4)))
    return dict(order=[labels[k] for k in order], steps=steps,
                clusters=per_cluster, fp=L.fp(merged_lines, 3),
                out=L.canon_set(merged_lines, 3))


def variants_of(lines, ops, nd=3, max_perms=5040):
    idx = {id(l): k for k, l in enumerate(lines)}
    fps = Counter()
    first = {}
    perms = list(itertools.permutations(range(len(lines))))
    if len(perms) > max_perms:
        perms = perms[:max_perms]
    for p in perms:
        order = [lines[k] for k in p]
        merged, _ = L.run_merge(order, ops=ops)
        f = L.fp(merged, nd)
        fps[f] += 1
        if f not in first:
            first[f] = (p, L.canon_set(merged, nd),
                        [tuple(sorted(idx[id(x)] for x in c))
                         for c in L.raw_clusters(order)])
    return fps, first


def minimize(lines, ops, labels):
    """Item 20: reduz ate' o MENOR subconjunto que ainda diverge."""
    n = len(lines)
    for size in range(2, n + 1):
        for combo in itertools.combinations(range(n), size):
            sub = [lines[k] for k in combo]
            fps, first = variants_of(sub, ops)
            if len(fps) > 1:
                return list(combo), fps, first
    return None, None, None


def main():
    S = L.load()
    raw = S["lines"]
    data = json.load(open(os.path.join(HERE, "out_c_merge_isolate.json"), encoding="utf-8"))
    blk = data["smallest_block"]
    idxs = blk["idxs"]
    print("bloco divergente real (%s): %d segmentos crus" % (blk["order"], len(idxs)))

    lines = [raw[k] for k in idxs]
    labels = ["L%d" % k for k in idxs]
    for lb, l in zip(labels, lines):
        p0, p1 = l.GetEndPoint(0), l.GetEndPoint(1)
        print("  %-8s (%.4f, %.4f) -> (%.4f, %.4f)  len=%.4f cm"
              % (lb, L.cm(p0.X), L.cm(p0.Y), L.cm(p1.X), L.cm(p1.Y),
                 L.cm(p0.DistanceTo(p1))))

    rep = dict(block=blk, labels=labels)

    print("")
    print("=== MINIMIZACAO (item 20) ===")
    combo, fps, first = minimize(lines, [], labels)
    if combo is None:
        print("nenhum subconjunto isolado diverge - a divergencia depende do "
              "contexto completo do bloco")
        rep["minimal"] = None
    else:
        mlab = [labels[k] for k in combo]
        print("MENOR subconjunto divergente: %d segmentos -> %s" % (len(combo), mlab))
        rep["minimal"] = dict(size=len(combo), labels=mlab,
                              idxs=[idxs[k] for k in combo],
                              distinct_outputs=len(fps),
                              variants=[dict(count=fps[f],
                                             first_perm=[mlab[x] for x in first[f][0]],
                                             out=first[f][1],
                                             clusters=first[f][2]) for f in fps])
        for f in fps:
            p, out, cl = first[f]
            print("  [%dx] primeira ordem %s -> %d linha(s): %s | clusters=%s"
                  % (fps[f], [mlab[x] for x in p], len(out), out, cl))

        sub = [lines[k] for k in combo]
        rep["properties"] = properties(sub, mlab)
        pr = rep["properties"]
        print("")
        print("=== PROPRIEDADES DA RELACAO (caso minimo) ===")
        print("  reflexiva : %s" % pr["reflexive"])
        print("  simetrica : %s  (pares assimetricos: %d)" % (pr["symmetric"], pr["asymmetric_count"]))
        print("  transitiva: %s  (triplas nao transitivas: %d)" % (pr["transitive"], pr["nontransitive_count"]))
        for t in pr["nontransitive_triples"][:10]:
            print("     %s ~ %s ~ %s  mas  %s !~ %s" % (t[0], t[1], t[2], t[0], t[2]))
        rep["relation_matrix"] = relation_matrix(sub, mlab)
        print("")
        print("  matriz da relacao (perpendicular em cm, tol=0,2cm):")
        for r in rep["relation_matrix"]:
            if r["a"] != r["b"]:
                print("     d(%s,%s)=%.6f  paralela=%s  compat=%s"
                      % (r["a"], r["b"], r["d_cm"], r["parallel"], r["compat"]))

        # ---- TRACE das duas ordens divergentes ------------------------
        keys = list(fps.keys())
        p_a = first[keys[0]][0]
        p_b = first[keys[1]][0]
        rep["traces"] = []
        print("")
        print("=== TRACE (item 7) ===")
        for tagp in (p_a, p_b):
            t = trace(sub, mlab, list(tagp))
            rep["traces"].append(t)
            print("")
            print("  ORDEM %s -> fp=%s" % (t["order"], t["fp"][:16]))
            for s in t["steps"]:
                print("    base=%-6s cand=%-6s paralela=%-5s perp=%.6fcm tol=%.6fcm -> %s  cluster=%s"
                      % (s["base"], s["cand"], s["parallel"], s["perp_cm"],
                         s["tol_cm"], "MERGE" if s["merge"] else "separa",
                         s["cluster_after"]))
            for c in t["clusters"]:
                print("    cluster %s -> %s" % (c["members"], c["out"]))

    out = os.path.join(HERE, "out_d_min_case.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print("-> " + out)


if __name__ == "__main__":
    main()
