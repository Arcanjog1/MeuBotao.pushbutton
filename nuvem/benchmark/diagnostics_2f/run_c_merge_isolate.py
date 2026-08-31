# -*- coding: utf-8 -*-
"""ETAPA 2F - TESTE A (itens D/E/F/H do pedido): isolar o `merge`.

Congela as MESMAS 9.258 linhas cruas e roda so' o AGRUPAMENTO (passada 1 do
`merge_collinear_fragments`, replicado em lib2f.raw_clusters com as MESMAS
funcoes do motor) sob varias permutacoes, comparando PARTICOES por
identidade de objeto (embaralhar reusa os mesmos objetos `Line`).

Responde:
  1. os clusters formados mudam?
  2. quais segmentos mudam de cluster?
  3. onde esta' o MENOR bloco divergente?
  4. o que a passada 2 (_bridge_clusters_via_openings) faz com isso?
  5. a divergencia depende de linha curta? esta' perto de abertura?

    py -3 nuvem/benchmark/diagnostics_2f/run_c_merge_isolate.py
"""
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402

SEEDS = [1, 2, 3, 10, 42]


def uf_blocks(parts_a, parts_b, n):
    """Componentes conexas da UNIAO das duas particoes - cada bloco e'
    refinado por A e por B, entao a comparacao vira local."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for parts in (parts_a, parts_b):
        for cl in parts:
            for k in cl[1:]:
                union(cl[0], k)
    blocks = {}
    for k in range(n):
        blocks.setdefault(find(k), []).append(k)
    return list(blocks.values())


def restrict(parts, members):
    ms = set(members)
    out = []
    for cl in parts:
        sub = tuple(sorted(x for x in cl if x in ms))
        if sub:
            out.append(sub)
    return sorted(out)


def near_opening(lines, idxs):
    """Menor distancia (cm) do meio de qualquer linha do bloco ao centro de
    qualquer abertura real."""
    S = L.load()
    best = None
    for k in idxs:
        l = lines[k]
        p0, p1 = l.GetEndPoint(0), l.GetEndPoint(1)
        mx, my = (p0.X + p1.X) / 2.0, (p0.Y + p1.Y) / 2.0
        for op in S["ops"]:
            c = op["center_xy"]
            d = L.cm(math.hypot(mx - c.X, my - c.Y))
            if best is None or d < best:
                best = d
    return best


def main():
    S = L.load()
    raw = S["lines"]
    n = len(raw)
    ids = L.line_ids(raw)

    print("linhas cruas: %d" % n)
    parts = {}
    stage2 = {}
    for tag, order in [("orig", raw)] + [("s%d" % s, L.shuffled(raw, s)) for s in SEEDS]:
        cl = L.raw_clusters(order)
        parts[tag] = L.partition(cl, ids)
        b = S["mod"]._bridge_clusters_via_openings(
            cl, S["mod"].OPENING_BRIDGE_TOLERANCE_FT, S["ops"],
            S["mod"].OPENING_GAP_PERP_TOLERANCE_FT, S["mod"].OPENING_GAP_WIDTH_SLACK_FT)
        stage2[tag] = L.partition(b, ids)
        merged = []
        for c in b:
            merged.extend(L.merge_cluster(c))
        print("%-5s stage1_clusters=%d  stage2_clusters=%d  merged_lines=%d  fp=%s" % (
            tag, len(parts[tag]), len(stage2[tag]), len(merged), L.fp(merged, 2)[:16]))
        sys.stdout.flush()

    base1, base2 = parts["orig"], stage2["orig"]
    report = {"n_raw": n, "orders": {}, "blocks": []}
    report["orders"]["orig"] = dict(stage1=len(base1), stage2=len(base2))

    all_bad_blocks = []
    for tag in ["s%d" % s for s in SEEDS]:
        eq1 = parts[tag] == base1
        eq2 = stage2[tag] == base2
        blocks = uf_blocks(base1, parts[tag], n)
        bad = [b for b in blocks if restrict(base1, b) != restrict(parts[tag], b)]
        blocks2 = uf_blocks(base2, stage2[tag], n)
        bad2 = [b for b in blocks2 if restrict(base2, b) != restrict(stage2[tag], b)]
        moved = sum(len(b) for b in bad)
        print("%-5s stage1 igual=%s  blocos divergentes=%d (linhas envolvidas=%d, menor=%d)"
              % (tag, eq1, len(bad), moved, min([len(b) for b in bad]) if bad else 0))
        print("      stage2 igual=%s  blocos divergentes=%d" % (eq2, len(bad2)))
        report["orders"][tag] = dict(
            stage1=len(parts[tag]), stage2=len(stage2[tag]),
            stage1_equal=eq1, stage2_equal=eq2,
            bad_blocks_stage1=len(bad), lines_in_bad_blocks=len(set(sum(bad, []))),
            bad_blocks_stage2=len(bad2),
            bad_block_sizes=sorted(Counter(len(b) for b in bad).items()),
        )
        all_bad_blocks.append((tag, bad))
        sys.stdout.flush()

    # ---- MENOR bloco divergente (item F: primeiro caso divergente) -------
    tag, bad = min(((t, b) for t, b in all_bad_blocks if b),
                   key=lambda tb: min(len(x) for x in tb[1]))
    smallest = min(bad, key=len)
    smallest = sorted(smallest)
    print("")
    print("=== MENOR BLOCO DIVERGENTE (%s): %d linhas ===" % (tag, len(smallest)))
    det = dict(order=tag, size=len(smallest), idxs=smallest,
               near_opening_cm=near_opening(raw, smallest),
               lines_cm=[], partition_orig=restrict(base1, smallest),
               partition_other=restrict(parts[tag], smallest))
    for k in smallest:
        l = raw[k]
        p0, p1 = l.GetEndPoint(0), l.GetEndPoint(1)
        det["lines_cm"].append(dict(idx=k,
                                    x0=round(L.cm(p0.X), 4), y0=round(L.cm(p0.Y), 4),
                                    x1=round(L.cm(p1.X), 4), y1=round(L.cm(p1.Y), 4),
                                    len_cm=round(L.cm(p0.DistanceTo(p1)), 4)))
    for r in det["lines_cm"]:
        print("  idx=%-5d (%.4f, %.4f) -> (%.4f, %.4f)  len=%.4f cm"
              % (r["idx"], r["x0"], r["y0"], r["x1"], r["y1"], r["len_cm"]))
    print("  particao ordem ORIGINAL : %s" % (det["partition_orig"],))
    print("  particao ordem %-8s : %s" % (tag, det["partition_other"]))
    print("  abertura mais proxima   : %.1f cm" % det["near_opening_cm"])
    report["smallest_block"] = det

    # ---- estatistica dos blocos divergentes (comprimento / abertura) ----
    stats = []
    for t, bad in all_bad_blocks:
        for b in bad:
            lens = []
            for k in b:
                l = raw[k]
                lens.append(L.cm(l.GetEndPoint(0).DistanceTo(l.GetEndPoint(1))))
            stats.append(dict(order=t, size=len(b), min_len_cm=round(min(lens), 3),
                              max_len_cm=round(max(lens), 3),
                              near_opening_cm=round(near_opening(raw, b), 1)))
    report["bad_block_stats"] = stats
    if stats:
        shorts = sum(1 for s in stats if s["min_len_cm"] < 20.0)
        far = sum(1 for s in stats if s["near_opening_cm"] > 100.0)
        print("")
        print("blocos divergentes (todas as seeds): %d" % len(stats))
        print("  com alguma linha < 20cm            : %d" % shorts)
        print("  a mais de 100cm de qualquer abertura: %d" % far)
        print("  tamanhos: %s" % sorted(Counter(s["size"] for s in stats).items()))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_c_merge_isolate.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("-> " + out)


if __name__ == "__main__":
    main()
