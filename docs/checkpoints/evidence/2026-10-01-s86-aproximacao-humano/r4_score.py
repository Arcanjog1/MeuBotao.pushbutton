# -*- coding: utf-8 -*-
"""Medidor da rodada 4: candidato (rows no formato do readback/sol_to_rows) x HUMANO (human_rows_unpad.json).
- F1 de pecas 1:1 por parede/fiada: mesmo codigo normalizado (U19/U34/U39 = canaleta pelo comprimento; *_H9 -> base),
  mesmo lado do vazado menor no B34, centro +-2 cm; precisao, revocacao, F1.
- paridade por encontro: em cada ponta/no, quem ocupa o ponto na fiada 0 (humano x candidato).
- qualidade (r2_eval) do candidato e do humano, fiadas 0..11 (a 12/13 do humano e' cinta/calco).
Uso: py -3 r4_score.py CANDIDATO.json [--perwall]"""
import json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r2_eval as E
cand = json.load(open(sys.argv[1]))
hum = json.load(open(os.path.join(HERE, "human_rows_unpad.json")))
PERWALL = "--perwall" in sys.argv
def walls(d):
    out = {}
    for k, v in d["rows"].items():
        w, c = [int(x) for x in k.split(":")]
        out.setdefault(w, {})[c] = sorted(v)
    return out
def norm(code):
    code = code.split("_H9")[0]
    return code
def side(it):
    if it[2].startswith("B34") and it[3]:
        sm = min(it[3], key=lambda c: c[1] - c[0])
        return 1 if (sm[0] + sm[1]) / 2.0 > (it[0] + it[1]) / 2.0 else -1
    return 0
C, H = walls(cand), walls(hum)
tp = fp = fn = 0
per = []
for w in sorted(set(C) | set(H)):
    m = nh = nc = 0
    for c in set(C.get(w, {})) | set(H.get(w, {})):
        hs = H.get(w, {}).get(c, [])
        cs = list(C.get(w, {}).get(c, []))
        nh += len(hs)
        nc += len(cs)
        used = set()
        for it in hs:
            ctr = (it[0] + it[1]) / 2.0
            best = None
            for j, x in enumerate(cs):
                if j in used or norm(x[2]) != norm(it[2]) or side(x) != side(it):
                    continue
                d = abs((x[0] + x[1]) / 2.0 - ctr)
                if d <= 2.0 and (best is None or d < best[0]):
                    best = (d, j)
            if best:
                used.add(best[1])
                m += 1
    tp += m
    fn += nh - m
    fp += nc - m
    per.append((w, m, nh, nc))
P = tp / float(tp + fp) if tp + fp else 0
R = tp / float(tp + fn) if tp + fn else 0
F = 2 * P * R / (P + R) if P + R else 0
print("SEMELHANCA pecas: iguais %d | humano %d | candidato %d | precisao %.1f%% revocacao %.1f%% F1 %.1f%%" % (tp, tp + fn, tp + fp, 100 * P, 100 * R, 100 * F))
if PERWALL:
    for w, m, nh, nc in per:
        print("  W%-2d %4d/%-4d (%3d%%) candidato %d" % (w, m, nh, 100 * m // max(nh, 1), nc))
# qualidade nas fiadas 0..11
tot = {"C": {}, "H": {}}
for tag, D, ops in (("C", C, cand["openings"]), ("H", H, hum["openings"])):
    for w, rows in D.items():
        r = dict((c, v) for c, v in rows.items() if c <= 11)
        if not r:
            continue
        L = max(it[1] for v in r.values() for it in v)
        e = E.evaluate(r, ops[w] if w < len(ops) else [], L, E.ties_from_rows(r))
        for k in E.KEYS:
            tot[tag][k] = tot[tag].get(k, 0) + e[k]
print("QUALIDADE f0-11 candidato:", dict((k, tot["C"][k]) for k in ("broken", "sv", "septa_unsupported", "comps", "comps_off_jamb", "b19_misplaced", "joints_coincident_nonexempt")))
print("QUALIDADE f0-11 humano   :", dict((k, tot["H"][k]) for k in ("broken", "sv", "septa_unsupported", "comps", "comps_off_jamb", "b19_misplaced", "joints_coincident_nonexempt")))
