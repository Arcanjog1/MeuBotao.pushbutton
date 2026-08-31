# -*- coding: utf-8 -*-
"""ETAPA 2D - simulacao offline das estrategias de pareamento. SOMENTE LEITURA."""
import json, os, sys, math, time
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as L

OUT = os.environ.get("D2OUT", ".")

S = L.state()
print("merge: %d linhas (%.1fs) | espessuras=%s | tol=%.4f cm" % (
    len(S["merged"]), S["t_merge"], S["setup"]["thicknesses_cm"], L.cm(S["tol"])))
pending, cands, t_scan = L.build_candidates()
print("candidatos: %d (%.1fs)" % (len(cands), t_scan))

# ---------------- caracterizacao dos 589 candidatos ----------------------
print()
print("=" * 100)
print("CARACTERIZACAO DOS %d CANDIDATOS VALIDOS" % len(cands))
print("=" * 100)
c = Counter()
for k in cands:
    e = k["err"]
    c[("exato<=0,05" if e <= 0.05 else "0,05-0,5" if e <= 0.5 else "0,5-1,0" if e <= 1.0
       else "1,0-1,5" if e <= 1.5 else "1,5-2,0" if e <= 2.0 else ">2,0")] += 1
for k in ("exato<=0,05", "0,05-0,5", "0,5-1,0", "1,0-1,5", "1,5-2,0", ">2,0"):
    print("   erro de espessura %-12s %3d" % (k, c[k]))
print()
print("   r (overlap/short) == 1,0000 exato: %d de %d" % (
    sum(1 for k in cands if k["r"] >= 0.99995), len(cands)))
print("   candidatos com linha curta (<20 cm): %d ; curta x longa(>=100): %d" % (
    sum(1 for k in cands if k["short"] < 20.0),
    sum(1 for k in cands if k["short"] < 20.0 and k["long"] >= 100.0)))
print("   r_long (overlap/long) dos curta x longa:",
      Counter(round(k["r_long"], 2) for k in cands if k["short"] < 20.0 and k["long"] >= 100.0).most_common(6))
print()

# ---------------- estrategias -------------------------------------------
Q = 0.05   # quantizacao do erro de espessura (cm) para permitir empate util


def qerr(k):
    return math.floor(k["err"] / Q + 1e-9)


def det(k):
    """desempate final deterministico: maior sobreposicao absoluta, depois indices."""
    return (-k["ov"], k["i"], k["j"])


STRATS = [
    ("BASELINE  (-r, d)",            lambda k: (-k["r"], k["d_ft"]) + det(k)),
    ("A  (-r, err)",                 lambda k: (-k["r"], k["err"]) + det(k)),
    ("B  (err, -r)",                 lambda k: (k["err"], -k["r"]) + det(k)),
    ("B2 (qerr, -r)",                lambda k: (qerr(k), -k["r"]) + det(k)),
    ("C  (qerr, -r_long)",           lambda k: (qerr(k), -k["r_long"]) + det(k)),
    ("C2 (qerr, -ov_abs)",           lambda k: (qerr(k), -k["ov"]) + det(k)),
    ("C3 (qerr, -r_long, -ov)",      lambda k: (qerr(k), -k["r_long"], -k["ov"]) + det(k)),
    ("E  (err_n, -r)",               lambda k: (k["err_n"], -k["r"]) + det(k)),
]


def greedy(keyfn):
    return sorted(cands, key=keyfn)


# ---------------- D: matching global ------------------------------------
def components():
    par = {}

    def find(x):
        while par.get(x, x) != x:
            par[x] = par.get(par[x], par[x])
            x = par[x]
        return x

    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb

    for k in cands:
        par.setdefault(k["i"], k["i"])
        par.setdefault(k["j"], k["j"])
        uni(k["i"], k["j"])
    g = defaultdict(list)
    for k in cands:
        g[find(k["i"])].append(k)
    return list(g.values())


def weight(k, cardinality_bonus=1000.0):
    """peso >0, maior = melhor. cardinalidade domina; depois espessura;
    depois qualidade de sobreposicao pela linha MAIS LONGA."""
    return cardinality_bonus - 100.0 * k["err_n"] + 10.0 * k["r_long"]


def max_weight_matching(edges, wfn):
    """Exato por busca em profundidade com poda; usado so' por componente."""
    edges = sorted(edges, key=lambda k: -wfn(k))
    best = {"w": -1e18, "sol": []}
    n = len(edges)
    suffix = [0.0] * (n + 1)
    for t in range(n - 1, -1, -1):
        suffix[t] = suffix[t + 1] + max(0.0, wfn(edges[t]))

    def rec(t, used, acc, sol):
        if acc + suffix[t] <= best["w"]:
            return
        if t == n:
            if acc > best["w"]:
                best["w"] = acc
                best["sol"] = list(sol)
            return
        e = edges[t]
        if e["i"] not in used and e["j"] not in used:
            used.add(e["i"]); used.add(e["j"]); sol.append(e)
            rec(t + 1, used, acc + wfn(e), sol)
            sol.pop(); used.discard(e["i"]); used.discard(e["j"])
        rec(t + 1, used, acc, sol)

    rec(0, set(), 0.0, [])
    return best["sol"]


comps = components()
print("componentes conexas do grafo de candidatos: %d ; maior = %d arestas" % (
    len(comps), max(len(x) for x in comps)))
print("   distribuicao de tamanho:", Counter(len(x) for x in comps).most_common(10))
print()

results = []
print(L.header())
for name, keyfn in STRATS:
    t0 = time.time()
    order = greedy(keyfn)
    res = L.run_pipeline(pending, order)
    fin = L.finish(res["walls"])
    m = L.metrics(name, res, fin, cands, time.time() - t0)
    results.append(m)
    print(L.row(m))

# D - matching global
for tag, cb in (("D  matching global", 1000.0), ("D2 matching s/ cardinal", 0.0)):
    t0 = time.time()
    sol = []
    for comp in comps:
        sol.extend(max_weight_matching(comp, lambda k: weight(k, cb)))
    sol.sort(key=lambda k: (-k["r"], k["d_ft"]))
    res = L.run_pipeline(pending, sol)
    fin = L.finish(res["walls"])
    # steals precisa ser medido contra TODOS os candidatos, nao so' a solucao
    chosen = {(k["i"], k["j"]) for k in res["accepted"]}
    res["lost"] = [k for k in cands if (k["i"], k["j"]) not in chosen]
    m = L.metrics(tag, res, fin, cands, time.time() - t0)
    results.append(m)
    print(L.row(m))

print()
print("ops nao atribuidas por estrategia:")
for m in results:
    print("   %-26s %d nao atribuidas: %s" % (m["name"], 91 - m["ops_ok"], ",".join(m["unass_ids"])))
print()
print("bins de erro de eixo:")
for m in results:
    print("   %-26s %s" % (m["name"], m["eb"]))

json.dump([{k: v for k, v in m.items()} for m in results],
          open(os.path.join(OUT, "sim_results.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nOK")
