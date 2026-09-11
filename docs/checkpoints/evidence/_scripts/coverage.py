# -*- coding: utf-8 -*-
"""Comparacao FISICA Revit x Revit por COBERTURA: blocos CRIADOS no doc de teste
(2026-09-11-butanta-created-blocks.json) x blocos HUMANOS (BUTANTA 1o PAV), ambos
projetados nos eixos das 34 paredes de alvenaria. Por parede e por fiada: uniao
dos intervalos ocupados, intersecao, faltas (humano tem bloco, solver nao) e
sobras (solver tem bloco, humano nao). Canaletas humanas contam como
'ocupado' na cobertura (sao blocos), mas fiadas 12-13 (cinta/canaleta) ficam
fora do veredito por serem escopo nao implementado."""
import json
import math
import os
from collections import defaultdict

EV = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\docs\checkpoints\evidence"
walls_json = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json")))["walls"]
human = json.load(open(os.path.join(EV, "2026-09-10-butanta-human-sequences.json")))["per_wall"]
created = json.load(open(os.path.join(EV, "2026-09-11-butanta-created-blocks.json")))["blocks"]
HALF = 7.0
COURSES = range(0, 12)          # 0..11: alvenaria comum; 12-13 = cinta/canaleta (fora de escopo)

hcount = {w["id"]: sum(len(human.get(str(w["id"]), {}).get(str(c), [])) for c in range(13)) for w in walls_json}
masonry = [w for w in walls_json if hcount[w["id"]] >= 20]
axes = []
for w in masonry:
    x0, y0 = w["p0_cm"]; x1, y1 = w["p1_cm"]
    L = math.hypot(x1 - x0, y1 - y0)
    axes.append({"id": w["id"], "p0": (x0, y0), "d": ((x1 - x0) / L, (y1 - y0) / L), "len": L, "horiz": abs(y1 - y0) < 1e-6})

# criados -> por parede/fiada (mesma logica do human_seq: orientacao pela rotacao)
cseq = defaultdict(lambda: defaultdict(list))
for b in created:
    bb = b["bb"]; cx, cy = b["cx"], b["cy"]
    bh = abs(math.sin(b["rot"])) < 0.5
    for a in axes:
        x0, y0 = a["p0"]; dx, dy = a["d"]
        t = (cx - x0) * dx + (cy - y0) * dy
        lat = abs((cx - x0) * dy - (cy - y0) * dx)
        if lat > HALF + 0.5 or t < -60 or t > a["len"] + 60:
            continue
        if a["horiz"]:
            t0, t1 = (bb[0] - x0) * dx, (bb[2] - x0) * dx
        else:
            t0, t1 = (bb[1] - y0) * dy, (bb[3] - y0) * dy
        cseq[a["id"]][b["c"]].append((round(min(t0, t1), 1), round(max(t0, t1), 1), b["code"], bh == a["horiz"], b["id"]))


def union(intervals):
    iv = sorted((max(a, 0.0), b) for a, b, *_ in intervals if b > a)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + 0.6:      # 0.6cm: junta de 1cm ja' esta' no bbox
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def length(iv):
    return sum(b - a for a, b in iv)


def inter(u, v):
    tot = 0.0
    for a, b in u:
        for c, d in v:
            tot += max(0.0, min(b, d) - max(a, c))
    return tot


def diff(u, v):
    """trechos de u nao cobertos por v"""
    out = []
    for a, b in u:
        cur = [(a, b)]
        for c, d in v:
            nxt = []
            for p, q in cur:
                if d <= p or c >= q:
                    nxt.append((p, q))
                else:
                    if c > p: nxt.append((p, c))
                    if d < q: nxt.append((d, q))
            cur = nxt
        out += [(p, q) for p, q in cur if q - p > 0.6]
    return out


tot_h = tot_c = tot_i = 0.0
falta = []; sobra = []
print("%-9s %-6s %-8s %-8s %-8s %-8s %s" % ("wall", "len", "humano", "solver", "cobre%", "extra%", "faltas(cm)>10 / sobras(cm)>10"))
for a in axes:
    wid = a["id"]; H = C = I = 0.0; f_w = []; s_w = []
    for c in COURSES:
        hu = union([(t0, t1) for t0, t1, cd, al, _ in human.get(str(wid), {}).get(str(c), []) if al])
        cu = union([(t0, t1) for t0, t1, cd, al, _ in cseq[wid].get(c, []) if al])
        H += length(hu); C += length(cu); I += inter(hu, cu)
        for p, q in diff(hu, cu):
            if q - p > 10: f_w.append((c, round(p), round(q)))
        for p, q in diff(cu, hu):
            if q - p > 10: s_w.append((c, round(p), round(q)))
    tot_h += H; tot_c += C; tot_i += I
    falta += [(wid,) + x for x in f_w]; sobra += [(wid,) + x for x in s_w]
    print("%-9d %-6.0f %-8.0f %-8.0f %-8.1f %-8.1f %d / %d" % (wid, a["len"], H, C, 100 * I / H if H else 0, 100 * (C - I) / C if C else 0, len(f_w), len(s_w)))
print("\nTOTAL fiadas 0..11: humano=%.0f cm, solver=%.0f cm, intersecao=%.0f cm" % (tot_h, tot_c, tot_i))
print("  COBERTURA do humano pelo solver: %.1f%%   |   EXTRA do solver fora do humano: %.1f%%" % (100 * tot_i / tot_h, 100 * (tot_c - tot_i) / tot_c))
print("  faltas > 10cm: %d trechos (%.0f cm) | sobras > 10cm: %d trechos (%.0f cm)" % (
    len(falta), sum(q - p for *_, p, q in falta), len(sobra), sum(q - p for *_, p, q in sobra)))
from collections import Counter
print("  faltas por parede: %s" % dict(Counter(f[0] for f in falta).most_common(8)))
print("  sobras por parede: %s" % dict(Counter(s[0] for s in sobra).most_common(8)))
print("  maiores faltas: %s" % sorted(falta, key=lambda f: -(f[3] - f[2]))[:6])
print("  maiores sobras: %s" % sorted(sobra, key=lambda s: -(s[3] - s[2]))[:6])

# ---- defeito 1: pecas CRIADAS perto dos X das juntas corridas do solver
cases = {8079818: [999.5], 8079838: [454.5, 464.5], 8079861: [49.5, 64.5]}
print("\n=== DEFEITO 1: pecas CRIADAS (solver, Revit) perto de cada X, fiadas 0..3 ('*' = transversal) ===")
for wid, xs in cases.items():
    for x in xs:
        print("-- wall %d x=%.1f --" % (wid, x))
        for c in (0, 1, 2, 3):
            seq = sorted(cseq[wid].get(c, []))
            near = ["%s[%.0f,%.0f]%s" % (cd, t0, t1, "" if al else "*") for t0, t1, cd, al, _ in seq if t1 >= x - 80 and t0 <= x + 80]
            print("   c%d: %s" % (c, " ".join(near)))
json.dump({"faltas": falta, "sobras": sobra, "cobertura": tot_i / tot_h, "extra": (tot_c - tot_i) / tot_c},
          open(os.path.join(EV, "2026-09-11-butanta-coverage.json"), "w"))
