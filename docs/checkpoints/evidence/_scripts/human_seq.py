# -*- coding: utf-8 -*-
"""Extrai as SEQUENCIAS HUMANAS de blocos por parede e por fiada, a partir dos
blocos livres do projeto de referencia (BUTANTA R08_LT, 1o PAV) e dos eixos
das 46 Walls do projeto de teste.

Somente leitura de JSON ja' exportado. Nada aqui e' norma: e' medicao.
"""
import json
import math
import os
import sys
from collections import defaultdict

EV = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton\docs\checkpoints\evidence"
walls = json.load(open(os.path.join(EV, "2026-09-10-butanta-test-walls.json")))["walls"]
ref = json.load(open(os.path.join(EV, "2026-09-10-butanta-ref-1pav-blocks.json")))
blocks = ref["blocks"]

HALF = 7.0          # meia espessura (14cm)
COURSE = 20.0       # passo de fiada (19 + 1 junta)
Z0 = 1.0            # z do primeiro bloco medido

CODE = {
    "BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34",
    "MEIO BLOCO - 14x19x19": "B19", "BLOCO 54 - 14x19x54": "B54",
    "COMPENSADOR 14x19x9": "C09", "PASTILHA - 14x19X4": "C04",
    "CANALETA INTEIRA - 14x19x39": "K39", "CANALETA 34 - 14x19x34": "K34",
    "MEIA CANALETA - 14x19x19": "K19", "CANALETA J - 14x9-19x19": "KJ",
    "COMPENSADOR 14x19x9 (deitado)": "C09d",
}


def code(sym):
    return CODE.get(sym, "?" + sym[:10])


def course_of(z):
    return int(round((z - Z0) / COURSE))


# eixos das walls em cm
axes = []
for w in walls:
    x0, y0 = w["p0_cm"]
    x1, y1 = w["p1_cm"]
    L = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    axes.append({"id": w["id"], "p0": (x0, y0), "d": (dx, dy), "len": L,
                 "horiz": abs(dy) < 1e-6})

# atribui cada bloco a paredes (pode cair em mais de uma perto de encontros)
per_wall = defaultdict(lambda: defaultdict(list))   # wall_id -> course -> [(t0,t1,code,along,id)]
attributed = 0
for b in blocks:
    bb = b.get("bb")
    if not bb:
        continue
    cx, cy = b["x"], b["y"]
    c = course_of(b["z"])
    # orientacao do bloco: eixo longo do bbox
    wx, wy = bb[3] - bb[0], bb[4] - bb[1]
    block_horiz = abs(math.sin(b['rot'])) < 0.5   # pela ROTACAO: bbox engana em pecas < 14cm
    hit_any = False
    for a in axes:
        x0, y0 = a["p0"]
        dx, dy = a["d"]
        t = (cx - x0) * dx + (cy - y0) * dy
        lat = abs((cx - x0) * dy - (cy - y0) * dx)
        if lat > HALF + 0.5:
            continue
        if t < -60 or t > a["len"] + 60:
            continue
        # extensao ao longo do eixo a partir do bbox
        if a["horiz"]:
            t0, t1 = (bb[0] - x0) * dx, (bb[3] - x0) * dx
        else:
            t0, t1 = (bb[1] - y0) * dy, (bb[4] - y0) * dy
        t0, t1 = min(t0, t1), max(t0, t1)
        along = (block_horiz == a["horiz"])   # bloco alinhado com a parede?
        per_wall[a["id"]][c].append((round(t0, 1), round(t1, 1), code(b["sym"]), along, b["id"]))
        hit_any = True
    if hit_any:
        attributed += 1

print("blocos ref 1o PAV: %d | atribuidos a alguma das 46 walls: %d (%.1f%%)" % (
    len(blocks), attributed, 100.0 * attributed / len(blocks)))
courses = sorted({c for w in per_wall.values() for c in w})
print("fiadas vistas: %s" % courses)

# resumo por parede
print("\n%-9s %-8s %-6s %s" % ("wall", "len_cm", "fiadas", "pecas por fiada (c0..c13)"))
for a in axes:
    pw = per_wall.get(a["id"], {})
    counts = [len(pw.get(c, [])) for c in range(14)]
    print("%-9d %-8.0f %-6d %s" % (a["id"], a["len"], len(pw), counts))

# dump das sequencias das 3 primeiras walls, fiadas 0 e 1
def fmt(seq):
    return " ".join("%s[%.0f,%.0f]%s" % (cd, t0, t1, "" if al else "*") for t0, t1, cd, al, _ in sorted(seq))

print("\n=== amostra: sequencias humanas (fiada 0 e 1). '*' = peca transversal (amarracao de outra parede) ===")
for a in axes[:4]:
    print("\nwall %d len=%.0f" % (a["id"], a["len"]))
    for c in (0, 1):
        print("  c%d: %s" % (c, fmt(per_wall[a["id"]].get(c, []))[:400]))

out = {"walls": [{"id": a["id"], "len": a["len"], "p0": a["p0"], "d": a["d"]} for a in axes],
       "per_wall": {str(k): {str(c): v for c, v in d.items()} for k, d in per_wall.items()}}
json.dump(out, open(os.path.join(EV, "2026-09-10-butanta-human-sequences.json"), "w"))
print("\nescrito 2026-09-10-butanta-human-sequences.json")
