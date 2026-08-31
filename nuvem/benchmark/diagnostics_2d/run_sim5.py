# -*- coding: utf-8 -*-
"""ETAPA 2D rodada 5 - as 6 paredes do trace, consumo silencioso de face,
performance e criterios de aprovacao. SOMENTE LEITURA."""
import os, sys, math, time
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as L

S = L.state()
pending, cands, t_scan = L.build_candidates()
ref = S["ref"]
Q = 0.05
qerr = lambda k: math.floor(k["err"] / Q + 1e-9)
det = lambda k: (-k["ov"], k["i"], k["j"])
KEY_BASE = lambda k: (-k["r"], k["d_ft"]) + det(k)
KEY_TH = lambda k: (qerr(k), -k["r_long"], -k["ov"]) + det(k)

TRACE = ("W012", "W036", "W038", "W057", "W072", "W073")
REFAX = {w["id"]: L.Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1])
         for w in ref["walls"]}

runs = {}
for tag, keyfn, gate in (("BASELINE", KEY_BASE, lambda k: True),
                         ("R1", KEY_TH, lambda k: True),
                         ("R1+err<=1,5", KEY_TH, lambda k: k["err"] <= 1.5),
                         ("R1+err<=1,0", KEY_TH, lambda k: k["err"] <= 1.0)):
    t0 = time.time()
    order = sorted([k for k in cands if gate(k)], key=keyfn)
    t_sort = time.time() - t0
    res = L.run_pipeline(pending, order)
    fin = L.finish(res["walls"])
    XY = [L.wall_xy(w) for w in fin["final"]]
    lens = [math.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1 in XY]
    runs[tag] = dict(res=res, fin=fin, XY=XY, lens=lens, t_sort=t_sort, order=order)

print("=" * 100)
print("1. AS 6 PAREDES DO TRACE DAS 9 ABERTURAS (criterio R3 do relatorio 2C)")
print("=" * 100)
print("   %-8s %8s  %s" % ("parede", "L(cm)", "  ".join("%-13s" % t for t in runs)))
for wid in TRACE:
    A = REFAX[wid]
    cols = []
    for tag in runs:
        cols.append("%13.2f" % L.coverage(A, runs[tag]["XY"]))
    print("   %-8s %8.1f  %s" % (wid, A.L, "  ".join(cols)))

print()
print("=" * 100)
print("2. CONSUMO SILENCIOSO DE FACE (par aceito que NAO gera parede)")
print("=" * 100)
for tag in runs:
    r = runs[tag]["res"]
    n_acc = len(r["accepted"])
    n_walls_raw = len(r["walls"])
    print("   %-14s pares aceitos=%3d | paredes geradas=%3d | faces consumidas sem parede=%d" % (
        tag, n_acc, n_walls_raw, 2 * (n_acc - n_walls_raw)))

print()
print("=" * 100)
print("3. DISTRIBUICAO DE COMPRIMENTO DAS PAREDES FINAIS x GABARITO")
print("=" * 100)
BINS = [(0, 20), (20, 50), (50, 100), (100, 200), (200, 400), (400, 1e9)]
reflens = [w["length_cm"] for w in ref["walls"]]
print("   %-12s %s %8s" % ("faixa", " ".join("%13s" % t for t in runs), "GABARITO"))
for a, b in BINS:
    cols = " ".join("%13d" % sum(1 for v in runs[t]["lens"] if a <= v < b) for t in runs)
    print("   %-12s %s %8d" % ("%.0f-%s" % (a, "%.0f" % b if b < 1e8 else "inf"), cols,
                               sum(1 for v in reflens if a <= v < b)))
print("   %-12s %s %8d" % ("TOTAL", " ".join("%13d" % len(runs[t]["lens"]) for t in runs), len(reflens)))
print("   %-12s %s %8.0f" % ("soma cm", " ".join("%13.0f" % sum(runs[t]["lens"]) for t in runs),
                             sum(reflens)))
print("   %-12s %s %8d" % ("len%5==4", " ".join(
    "%13d" % sum(1 for v in runs[t]["lens"] if abs((v % 5.0) - 4.0) <= 0.5) for t in runs),
    sum(1 for v in reflens if abs((v % 5.0) - 4.0) <= 0.5)))

print()
print("=" * 100)
print("4. PERFORMANCE")
print("=" * 100)
print("   merge_collinear_fragments (9258 -> 2868)    %.2f s" % S["t_merge"])
print("   varredura O(n^2) de candidatos (2868 linhas) %.2f s   <- domina, NAO muda" % t_scan)
for tag in runs:
    print("   ordenacao dos %3d candidatos (%-14s)   %.5f s" % (
        len(runs[tag]["order"]), tag, runs[tag]["t_sort"]))
print("   pares paralelos avaliados: %d" % (2868 * 2867 // 2))

print()
print("=" * 100)
print("5. COBERTURA DO GABARITO, PAREDE A PAREDE (classes)")
print("=" * 100)
for tag in runs:
    c = Counter()
    for wid, A in REFAX.items():
        v = L.coverage(A, runs[tag]["XY"])
        c["COBERTA" if v >= 0.85 else "PARCIAL" if v >= 0.30 else "QUASE_AUSENTE" if v > 0 else "AUSENTE"] += 1
    print("   %-14s %s" % (tag, dict(c)))

print()
print("=" * 100)
print("6. LINHAS ORFAS QUE CONTINUAM SEM PAR (materia-prima de uma futura repescagem)")
print("=" * 100)
for tag in runs:
    used = runs[tag]["res"]["used"]
    orf = [i for i in range(len(pending)) if not used[i]]
    # orfas que TINHAM candidato valido
    cand_lines = set()
    for k in cands:
        cand_lines.add(k["i"]); cand_lines.add(k["j"])
    perdeu = [i for i in orf if i in cand_lines]
    print("   %-14s linhas nao usadas=%4d | dessas, tinham candidato valido=%3d" % (
        tag, len(orf), len(perdeu)))
print("\nOK")
