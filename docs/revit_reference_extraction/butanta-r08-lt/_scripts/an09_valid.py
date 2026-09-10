# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_core import *

P, O, OA, by_lvl = build()
R = json.load(io.open(os.path.join(OUT, "an_open_full.json"), encoding="utf-8"))
U = [r for r in R if not r["prop"]]

print("=== VALIDACAO CRUZADA ===")
print("pecas totais                 : %d" % len(P))
print("ElementIds duplicados        : %d" % (len(P) - len(set(p["id"] for p in P))))
print("UniqueIds duplicados         : %d" % (len(P) - len(set(p["uid"] for p in P))))
print("pecas sem parametro Parede   : %d" % sum(1 for p in P if not p["parede"]))
print("pecas sem posicao (x/y/z)    : %d" % sum(1 for p in P if p["x"] is None))
print("pecas sem bbox               : %d" % sum(1 for p in P if not p["bb"]))
print("pecas sem nivel              : %d" % sum(1 for p in P if not p["lvl"]))
print("pecas sem L/H/W              : %d" % sum(1 for p in P if not (p["L"] and p["H"] and p["W"])))
print("largura != 14 cm             : %d" % sum(1 for p in P if abs((p["W"] or 0) - 14.0) > .1))
print("rotacao nao multipla de 90   : %d" % sum(1 for p in P if p["rot"] is not None and min(abs(round(p["rot"]) % 90), 90 - abs(round(p["rot"]) % 90)) > 0.01))
print("aberturas totais             : %d" % len(O))
print("aberturas sem parametro Parede: %d" % sum(1 for o in O if not o["parede"]))
print("aberturas sem linha de parede : %d" % (len(O) - sum(1 for r in U if r)))
print("aberturas sem solucao ACIMA   : %d" % sum(1 for r in U if "above" not in r))
print("janelas/aberturas c/ peitoril sem solucao ABAIXO: %d"
      % sum(1 for r in U if r["peit"] > .1 and "below" not in r))
mism = [o for o in O if o["parede"] and o["lvl"] and o["parede"].split(" - ")[-1] != o["lvl"]
        and "TIPO" not in o["parede"]]
print("aberturas com rotulo Parede de outro nivel: %d %s" % (len(mism), [x["id"] for x in mism]))
print()
print("=== EXCECOES: aberturas SEM canaleta acima ===")
for r in U:
    if "above" not in r or not r.get("above_all_canaleta_over_span"):
        f = r.get("above_fams_over_span") or {}
        print("  id=%-9s %-9s %-30s larg=%-6.1f alt=%-6.1f peit=%-5.1f topo_vao=%-6.1f topo_parede=%-6.1f  -> %s"
              % (r["id"], r["tit"], (r["parede"] or "?").encode("ascii", "replace"),
                 r["larg"], r["alt"], r["peit"], r["vao_z_rel"][1], r["wall_top_z_rel"],
                 str(f).encode("ascii", "replace") or "<VAZIO>"))
print()
print("=== EXCECOES: peitoril sem canaleta abaixo ===")
n = 0
for r in U:
    if r["peit"] > .1 and (("below" not in r) or not r.get("below_all_canaleta_over_span")):
        n += 1
        print("  id=%s %s %s" % (r["id"], r["tit"], str(r.get("below_fams_over_span")).encode("ascii","replace")))
print("  total: %d" % n)
print()
print("=== PECAS DE 9 CM (meia fiada) ===")
n9 = [p for p in P if abs((p["H"] or 0) - 9.0) < .1]
print("pecas com altura 9 cm: %d" % len(n9))
mod = collections.Counter(round((p["_z"][0] - DATUM[p["lvl"]] - 1.0) % 20.0, 1) for p in n9)
print("z_rel mod 20 (offset a partir de +1):", sorted(mod.items(), key=lambda x: -x[1])[:8])
print()
print("=== COMPENSADOR / PASTILHA (pecas de ajuste) ===")
for f in ["COMPENSADOR 14x19x9", "PASTILHA - 14x19X4", "COMPENSADOR 14x19x9 (deitado)", "MEIO BLOCO - 14x19x19"]:
    s = [p for p in P if p["fam"] == f]
    if not s: continue
    print("  %-32s n=%5d  L=%s H=%s" % (f, len(s), sorted(set(p["L"] for p in s))[:3], sorted(set(p["H"] for p in s))[:3]))
