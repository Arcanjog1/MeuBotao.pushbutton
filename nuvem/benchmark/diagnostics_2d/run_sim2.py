# -*- coding: utf-8 -*-
"""ETAPA 2D rodada 2 - separa o efeito RANKING do efeito FILTRO DE QUALIDADE,
e testa greedy x matching global sob o MESMO filtro. SOMENTE LEITURA."""
import json, os, sys, math, time, random
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as L

OUT = os.environ.get("D2OUT", ".")
S = L.state()
pending, cands, t_scan = L.build_candidates()
ref = S["ref"]

Q = 0.05


def qerr(k):
    return math.floor(k["err"] / Q + 1e-9)


def det(k):
    return (-k["ov"], k["i"], k["j"])


KEY_BASE = lambda k: (-k["r"], k["d_ft"]) + det(k)
KEY_TH = lambda k: (qerr(k), -k["r_long"], -k["ov"]) + det(k)


def gate_none(k):
    return True


def gate_err(v):
    return lambda k: k["err"] <= v


def gate_rlong(v):
    return lambda k: k["r_long"] >= v


def gate_d2(k):
    return 100.0 * k["err_n"] - 10.0 * k["r_long"] < 0.0


def gate_and(*gs):
    return lambda k: all(g(k) for g in gs)


def run(name, keyfn, gate, matching=False, wfn=None):
    t0 = time.time()
    pool = [k for k in cands if gate(k)]
    if matching:
        sol = []
        for comp in comps_of(pool):
            sol.extend(mwm(comp, wfn))
        sol.sort(key=keyfn)
        order = sol
    else:
        order = sorted(pool, key=keyfn)
    res = L.run_pipeline(pending, order)
    fin = L.finish(res["walls"])
    chosen = {(k["i"], k["j"]) for k in res["accepted"]}
    res["lost"] = [k for k in cands if (k["i"], k["j"]) not in chosen]
    m = L.metrics(name, res, fin, cands, time.time() - t0)
    m["pool"] = len(pool)
    m["_walls_xy"] = [L.wall_xy(w) for w in fin["final"]]
    return m


def comps_of(edges):
    par = {}

    def find(x):
        while par.get(x, x) != x:
            par[x] = par.get(par[x], par[x]); x = par[x]
        return x

    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    for k in edges:
        par.setdefault(k["i"], k["i"]); par.setdefault(k["j"], k["j"]); uni(k["i"], k["j"])
    g = defaultdict(list)
    for k in edges:
        g[find(k["i"])].append(k)
    return list(g.values())


def mwm(edges, wfn):
    edges = sorted(edges, key=lambda k: (-wfn(k), k["i"], k["j"]))
    n = len(edges)
    suffix = [0.0] * (n + 1)
    for t in range(n - 1, -1, -1):
        suffix[t] = suffix[t + 1] + max(0.0, wfn(edges[t]))
    best = {"w": -1e18, "sol": []}

    def rec(t, used, acc, sol):
        if acc + suffix[t] <= best["w"] + 1e-12:
            return
        if t == n:
            if acc > best["w"]:
                best["w"] = acc; best["sol"] = list(sol)
            return
        e = edges[t]
        if e["i"] not in used and e["j"] not in used:
            used.add(e["i"]); used.add(e["j"]); sol.append(e)
            rec(t + 1, used, acc + wfn(e), sol)
            sol.pop(); used.discard(e["i"]); used.discard(e["j"])
        rec(t + 1, used, acc, sol)
    rec(0, set(), 0.0, [])
    return best["sol"]


W_QUAL = lambda k: 10.0 * k["r_long"] - 100.0 * k["err_n"]
W_CARD = lambda k: 1000.0 + 10.0 * k["r_long"] - 100.0 * k["err_n"]

RUNS = [
    ("BASELINE (-r,d)",            KEY_BASE, gate_none, False, None),
    ("R1 rank-espessura",          KEY_TH,   gate_none, False, None),
    ("R1+gate err<=1,0",           KEY_TH,   gate_err(1.0), False, None),
    ("R1+gate err<=0,5",           KEY_TH,   gate_err(0.5), False, None),
    ("R1+gate r_long>=0,30",       KEY_TH,   gate_rlong(0.30), False, None),
    ("R1+gate r_long>=0,50",       KEY_TH,   gate_rlong(0.50), False, None),
    ("R1+gate D2 (err<1,4*rl)",    KEY_TH,   gate_d2, False, None),
    ("R1+rl>=0,30+err<=1,0",       KEY_TH,   gate_and(gate_rlong(0.30), gate_err(1.0)), False, None),
    ("MG qual (gate none)",        KEY_TH,   gate_none, True, W_QUAL),
    ("MG card (gate none)",        KEY_TH,   gate_none, True, W_CARD),
    ("MG card + gate D2",          KEY_TH,   gate_d2, True, W_CARD),
    ("MG card + rl>=0,30+err<=1",  KEY_TH,   gate_and(gate_rlong(0.30), gate_err(1.0)), True, W_CARD),
]

res = []
print(L.header() + "  pool")
for name, kf, g, mt, wf in RUNS:
    m = run(name, kf, g, mt, wf)
    res.append(m)
    print(L.row(m) + " %5d" % m["pool"])

# ---------- R10: nao-regressao das 70 paredes hoje COBERTAS --------------
base = res[0]
REFAX = [L.Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1]) for w in ref["walls"]]
RID = [w["id"] for w in ref["walls"]]


def cov_set(m):
    return {RID[i] for i, A in enumerate(REFAX) if L.coverage(A, m["_walls_xy"]) >= 0.85}


b = cov_set(base)
print()
print("R10 - nao-regressao (paredes do gabarito hoje COBERTAS que deixam de ser):")
for m in res:
    s = cov_set(m)
    print("   %-28s cobertas=%3d | perdidas em relacao ao baseline: %-2d %s | ganhas: %d" % (
        m["name"], len(s), len(b - s), sorted(b - s) if len(b - s) <= 8 else "...", len(s - b)))

# ---------- determinismo / invariancia -----------------------------------
print()
print("DETERMINISMO - mesma estrategia com a lista de candidatos EMBARALHADA:")
for name, kf, g in (("BASELINE (-r,d)", KEY_BASE, gate_none),
                    ("R1+rl>=0,30+err<=1,0", KEY_TH, gate_and(gate_rlong(0.30), gate_err(1.0)))):
    sigs = set()
    for seed in (1, 2, 3):
        rnd = random.Random(seed)
        pool = [k for k in cands if g(k)]
        rnd.shuffle(pool)
        order = sorted(pool, key=kf)
        r2 = L.run_pipeline(pending, order)
        sigs.add(tuple(sorted((k["i"], k["j"]) for k in r2["accepted"])))
    print("   %-28s assinaturas distintas em 3 embaralhamentos: %d %s" % (
        name, len(sigs), "OK (estavel)" if len(sigs) == 1 else "INSTAVEL"))

json.dump([{k: v for k, v in m.items() if not k.startswith("_")} for m in res],
          open(os.path.join(OUT, "sim2_results.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nOK")
