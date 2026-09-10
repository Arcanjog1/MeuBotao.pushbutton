# -*- coding: utf-8 -*-
"""Numeros finais com tolerancia de fiada de 1,5 cm (paredes com grade +-1cm)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_core import *
CTOL = 1.5

P, O, OA, by_lvl = build()
res = []
for o in OA:
    wp = [p for p in by_lvl.get(o["lvl"], ()) if p["_ax"] == o["_ax"] and abs(p["_tc"] - o["_tc"]) <= 3.0]
    if not wp: continue
    s0, s1 = o["_s"]; zt = o["_zt"]; zb = o["_zb"]
    ov = lambda p: p["_s"][1] > s0 + 0.6 and p["_s"][0] < s1 - 0.6
    ab = [p for p in wp if ov(p) and abs(p["_z"][0] - zt) < CTOL]
    be = [p for p in wp if ov(p) and abs(p["_z"][1] - zb) < CTOL] if o["peitoril"] > .1 else []
    res.append({"o": o, "ab": ab, "be": be,
                "ab_can": bool(ab) and all(is_canaleta(p["fam"]) for p in ab),
                "be_can": bool(be) and all(is_canaleta(p["fam"]) for p in be)})
U = [r for r in res if not r["o"].get("_propagated_from")]
print("=== NUMEROS FINAIS (142 aberturas unicas) ===")
for t in ["PORTA", "JANELA", "ABERTURA"]:
    rs = [r for r in U if r["o"]["titulo"] == t]
    nab = sum(1 for r in rs if r["ab"])
    ncan = sum(1 for r in rs if r["ab_can"])
    b = [r for r in rs if r["o"]["peitoril"] > .1]
    print("%-9s n=%2d | ACIMA: com peca %2d, 100%% canaleta %2d (%5.1f%%) | ABAIXO(peit>0 n=%2d): 100%% canaleta %2d"
          % (t, len(rs), nab, ncan, 100.0*ncan/len(rs), len(b), sum(1 for r in b if r["be_can"])))
tot = len(U); tcan = sum(1 for r in U if r["ab_can"])
print("TOTAL     n=%d | ACIMA 100%% canaleta: %d (%.1f%%)" % (tot, tcan, 100.0*tcan/tot))
bb = [r for r in U if r["o"]["peitoril"] > .1]
print("          peitoril>0: %d | ABAIXO 100%% canaleta: %d (%.1f%%)"
      % (len(bb), sum(1 for r in bb if r["be_can"]), 100.0*sum(1 for r in bb if r["be_can"])/len(bb)))
print()
print("=== EXCECOES FINAIS ===")
for r in U:
    if not r["ab_can"]:
        f = dict(collections.Counter(p["fam"] for p in r["ab"]))
        print("  %-9s id=%-9s %-42s larg=%-6.1f alt=%-6.1f -> %s"
              % (r["o"]["titulo"], r["o"]["id"], (r["o"]["parede"] or "").encode("ascii","replace"),
                 r["o"]["largura"], r["o"]["altura"], str(f).encode("ascii","replace") or "SEM PECA"))
json.dump([{"id": r["o"]["id"], "tit": r["o"]["titulo"], "ab_can": r["ab_can"], "be_can": r["be_can"],
            "ab_fams": dict(collections.Counter(p["fam"] for p in r["ab"])),
            "be_fams": dict(collections.Counter(p["fam"] for p in r["be"]))} for r in U],
          io.open(os.path.join(OUT, "an_final.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
