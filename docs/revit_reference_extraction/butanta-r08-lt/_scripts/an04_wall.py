# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_lib import *
from an_geo import *

P, O = load()
by_lvl = prep(P, O)

def wall_of_opening(o):
    return wall_pieces(o, by_lvl)

def courses(pieces, datum):
    d = collections.defaultdict(list)
    for p in pieces:
        d[round(p["_z"][0] - datum, 1)].append(p)
    return d

def show(o, maxc=30):
    wp = wall_of_opening(o)
    datum = o["_datum"]
    s0, s1 = o["_s"]
    cs = courses(wp, datum)
    tot_lo = min(p["_s"][0] for p in wp); tot_hi = max(p["_s"][1] for p in wp)
    print("### %s id=%s  %s | %s" % (o["titulo"], o["id"],
          (o["parede"] or "?").encode("ascii", "replace"), (o["lvl"] or "?").encode("ascii", "replace")))
    print("    vao: larg=%.0f alt=%.0f peitoril=%.0f  -> z_rel [%.0f .. %.0f]  eixo=%s  span=[%.0f..%.0f]"
          % (o["largura"], o["altura"], o["peitoril"], o["_zb"]-datum, o["_zt"]-datum, o["_ax"], s0, s1))
    print("    parede: comprimento total=%.0f cm  (span %.0f..%.0f)  n_pecas=%d"
          % (tot_hi - tot_lo, tot_lo, tot_hi, len(wp)))
    for z in sorted(cs)[:maxc]:
        ps = cs[z]
        can = [p for p in ps if is_canaleta(p["fam"])]
        cov_lo = min(p["_s"][0] for p in ps); cov_hi = max(p["_s"][1] for p in ps)
        canpct = (100.0*len(can)/len(ps)) if ps else 0
        inspan = [p for p in ps if p["_s"][1] > s0+TOL and p["_s"][0] < s1-TOL]
        mark = ""
        if abs(z - (o["_zt"]-datum)) < .6: mark = "  <== TOPO DO VAO"
        if abs(z + 20 - (o["_zb"]-datum)) < .6 and o["peitoril"] > 0: mark = "  <== ULTIMA FIADA SOB PEITORIL"
        sig = collections.Counter(p["fam"].split(" -")[0].split(" 14")[0] for p in ps)
        print("    z=%6.1f  n=%3d  canaleta=%3d(%3.0f%%)  cobre[%6.0f..%6.0f]  sobre_vao=%2d  %s%s"
              % (z, len(ps), len(can), canpct, cov_lo, cov_hi, len(inspan),
                 str(dict(sig)).encode("ascii", "replace"), mark))

# 2 portas, 2 janelas, 1 excecao
sel = []
for t, k in [("PORTA", 2), ("JANELA", 2)]:
    c = 0
    for o in O:
        if o["titulo"] == t and o["lvl"] == u"1\u00ba PAVIMENTO":
            sel.append(o); c += 1
            if c >= k: break
for o in sel:
    show(o); print()
