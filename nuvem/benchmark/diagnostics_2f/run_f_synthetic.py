# -*- coding: utf-8 -*-
"""ETAPA 2F - item M do pedido: casos SINTETICOS de diagnostico do merge.

MERGE-001..010 do pedido, mais dois casos que o pedido antecipa no item 14
(relacao nao transitiva) e no item 15 (geometria de saida dependente da
linha de referencia). Cada caso roda TODAS as permutacoes da lista e compara
o fingerprint GEOMETRICO canonico da saida.

Estes casos NAO sao (ainda) testes permanentes do core - sao instrumento de
diagnostico, conforme o item 13 do pedido.

    py -3 nuvem/benchmark/diagnostics_2f/run_f_synthetic.py
"""
import itertools
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib2f as L  # noqa: E402


def op(cx, cy, width_cm):
    S = L.load()
    mod = S["mod"]
    f = S["F"] / 100.0
    return {"element_id": -1, "center_xy": mod.XYZ(cx * f, cy * f, 0.0),
            "width_ft": width_cm * f, "sill_z_abs": 0.0, "head_z_abs": 10.0}


def rot90(segs):
    return [(-y0, x0, -y1, x1) for x0, y0, x1, y1 in segs]


def translate(segs, dx, dy):
    return [(x0 + dx, y0 + dy, x1 + dx, y1 + dy) for x0, y0, x1, y1 in segs]


CASES = []


def case(cid, desc, segs, ops=None, perms="all"):
    CASES.append(dict(cid=cid, desc=desc, segs=segs, ops=ops or [], perms=perms))


# MERGE-001 - 3 colineares perfeitos, sobrepostos
case("MERGE-001", "3 colineares perfeitos sobrepostos",
     [(0, 0, 100, 0), (80, 0, 180, 0), (160, 0, 260, 0)])
# MERGE-002 - 3 colineares com gaps pequenos (<= MAX_JUNCTION_GAP 40cm)
case("MERGE-002", "3 colineares com gaps de 10cm (dentro do gap tolerado)",
     [(0, 0, 100, 0), (110, 0, 210, 0), (220, 0, 320, 0)])
# MERGE-003 - segmento curto entre dois longos
case("MERGE-003", "curto (5cm) entre dois longos (400cm)",
     [(0, 0, 400, 0), (400, 0, 405, 0), (405, 0, 805, 0)])
# MERGE-004 - offsets ABAIXO da tolerancia (2mm) - encadeados
case("MERGE-004", "offsets 0,05cm (abaixo da tolerancia de 0,2cm)",
     [(0, 0, 400, 0), (0, 0.05, 400, 0.05), (0, 0.10, 400, 0.10)])
# MERGE-005 - offsets ACIMA da tolerancia
case("MERGE-005", "offsets 0,5cm (acima da tolerancia de 0,2cm)",
     [(0, 0, 400, 0), (0, 0.5, 400, 0.5), (0, 1.0, 400, 1.0)])
# MERGE-006 - fragmentos separados pelo vao de uma abertura real (80cm)
case("MERGE-006", "gap de 80cm explicado por abertura real de 80cm",
     [(0, 0, 200, 0), (280, 0, 480, 0)], ops=[op(240, 0, 80)])
# MERGE-007 - endpoints invertidos (mesma geometria de MERGE-001)
case("MERGE-007", "MERGE-001 com endpoints invertidos",
     [(100, 0, 0, 0), (180, 0, 80, 0), (260, 0, 160, 0)])
# MERGE-008 - rotacao 90 graus de MERGE-001
case("MERGE-008", "MERGE-001 rotacionado 90 graus",
     rot90([(0, 0, 100, 0), (80, 0, 180, 0), (160, 0, 260, 0)]))
# MERGE-009 - translacao de MERGE-001
case("MERGE-009", "MERGE-001 transladado (+1234,5 / -987,6)",
     translate([(0, 0, 100, 0), (80, 0, 180, 0), (160, 0, 260, 0)], 1234.5, -987.6))
# MERGE-010 - ordem aleatoria repetida (5 fragmentos, todas as 120 permutacoes)
case("MERGE-010", "5 fragmentos, todas as 120 permutacoes",
     [(0, 0, 100, 0), (90, 0, 200, 0), (190, 0, 300, 0),
      (290, 0, 400, 0), (390, 0, 500, 0)])
# MERGE-011 - CADEIA nao transitiva (o caso ABC do item 14 do pedido)
case("MERGE-011", "cadeia A~B ~C com offsets de 0,15cm (A~C = FALSO)",
     [(0, 0, 400, 0), (0, 0.15, 400, 0.15), (0, 0.30, 400, 0.30)])
# MERGE-012 - empate de comprimento no cluster (referencia ambigua)
case("MERGE-012", "dois fragmentos de MESMO comprimento, offsets opostos",
     [(0, 0, 400, 0), (0, 0.15, 400, 0.15)])
# MERGE-013 - quase-paralelas dentro do cluster
case("MERGE-013", "quase-paralelas (0,02 grau) coladas",
     [(0, 0, 800, 0), (0, 0.05, 800, 0.05 + 800 * math.tan(math.radians(0.02))),
      (0, 0.10, 800, 0.10 + 800 * math.tan(math.radians(0.02)))])


def run_case(c):
    S = L.load()
    lines = [L.mkline(*s) for s in c["segs"]]
    idx = {id(l): k for k, l in enumerate(lines)}
    fps = Counter()
    parts = Counter()
    samples = {}
    perms = list(itertools.permutations(range(len(lines))))
    for p in perms:
        order = [lines[k] for k in p]
        clusters = L.raw_clusters(order)
        part = tuple(L.partition(clusters, idx))
        parts[part] += 1
        merged, _ = L.run_merge(order, ops=c["ops"])
        f = L.fp(merged, 3)
        fps[f] += 1
        if f not in samples:
            samples[f] = dict(perm="".join("ABCDE"[k] for k in p),
                              n_out=len(merged), lines=L.canon_set(merged, 3),
                              partition=[list(x) for x in part])
    return dict(cid=c["cid"], desc=c["desc"], n_perms=len(perms),
                distinct_partitions=len(parts), distinct_outputs=len(fps),
                invariant=(len(fps) == 1),
                partition_invariant=(len(parts) == 1),
                variants=[dict(count=fps[f], **samples[f]) for f in fps])


def cluster_reference_test():
    """Item 15: MESMO cluster, ordem interna diferente -> mesma geometria?
    Testa `_merge_collinear_cluster` isolado (o agrupamento nao entra)."""
    out = []
    for cid, segs in [
        ("CLU-01 empate de comprimento, offsets opostos",
         [(0, 0, 400, 0), (0, 0.15, 400, 0.15)]),
        ("CLU-02 empate de comprimento, quase-paralelas",
         [(0, 0, 400, 0), (0, 0.10, 400, 0.10 + 400 * math.tan(math.radians(0.05)))]),
        ("CLU-03 tres fragmentos, dois empatados no maior comprimento",
         [(0, 0, 400, 0), (400, 0.10, 800, 0.10), (200, 0.05, 300, 0.05)]),
        ("CLU-04 comprimentos distintos (referencia nao ambigua)",
         [(0, 0, 400, 0), (350, 0.10, 900, 0.10)]),
        ("CLU-05 EMPATE EXATO de comprimento com direcoes diferentes",
         [(0, 0, 400, 0),
          (0, 0.10, 400 * math.cos(math.radians(0.05)),
           0.10 + 400 * math.sin(math.radians(0.05)))]),
        ("CLU-06 EMPATE EXATO de comprimento, tres fragmentos",
         [(0, 0, 400, 0),
          (0, 0.10, 400 * math.cos(math.radians(0.05)),
           0.10 + 400 * math.sin(math.radians(0.05))),
          (600, 0.05, 700, 0.05)]),
    ]:
        lines = [L.mkline(*s) for s in segs]
        fps = Counter()
        samples = {}
        for p in itertools.permutations(range(len(lines))):
            cluster = [lines[k] for k in p]
            merged = L.merge_cluster(cluster, ops=[])
            f = L.fp(merged, 4)
            fps[f] += 1
            if f not in samples:
                samples[f] = dict(perm="".join("ABCD"[k] for k in p),
                                  lines=L.canon_set(merged, 4))
        out.append(dict(cid=cid, distinct_outputs=len(fps),
                        invariant=(len(fps) == 1),
                        variants=[dict(count=fps[f], **samples[f]) for f in fps]))
    return out


def main():
    rep = {"cases": [], "cluster_reference": []}
    print("=== MERGE-001..013 (todas as permutacoes) ===")
    for c in CASES:
        r = run_case(c)
        rep["cases"].append(r)
        print("%-10s %-58s perms=%-4d particoes=%d saidas=%d  %s"
              % (r["cid"], r["desc"], r["n_perms"], r["distinct_partitions"],
                 r["distinct_outputs"], "OK" if r["invariant"] else "<<< DIVERGE"))
        if not r["invariant"]:
            for v in r["variants"]:
                print("     [%2dx] perm=%s  n=%d  %s"
                      % (v["count"], v["perm"], v["n_out"], v["lines"]))
        sys.stdout.flush()

    print("")
    print("=== _merge_collinear_cluster isolado (cluster fixo, ordem interna) ===")
    rep["cluster_reference"] = cluster_reference_test()
    for r in rep["cluster_reference"]:
        print("%-56s saidas=%d  %s" % (r["cid"], r["distinct_outputs"],
                                       "OK" if r["invariant"] else "<<< DIVERGE"))
        if not r["invariant"]:
            for v in r["variants"]:
                print("     [%2dx] perm=%s  %s" % (v["count"], v["perm"], v["lines"]))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_f_synthetic.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print("-> " + out)


if __name__ == "__main__":
    main()
