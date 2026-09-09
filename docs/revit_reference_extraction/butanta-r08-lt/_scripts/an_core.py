# -*- coding: utf-8 -*-
"""Nucleo: carrega, propaga aberturas dos pav. TIPO e indexa geometria."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_lib import *
from an_geo import prep, wall_pieces, crossing, course_at, TOL

DATUM = {u"PAV. T\u00c9RREO": -350.0, u"1\u00ba PAVIMENTO": 0.0, u"2\u00ba PAVIMENTO": 272.0,
         u"3\u00ba PAVIMENTO": 544.0, u"4\u00ba PAVIMENTO": 816.0, u"5\u00ba PAVIMENTO": 1088.0,
         u"6\u00ba PAVIMENTO": 1360.0, u"7\u00ba PAVIMENTO": 1632.0, u"8\u00ba PAVIMENTO": 1904.0,
         u"9\u00ba PAVIMENTO": 2176.0, u"BARRILETE": 2448.0, u"COBERTURA": 2808.0}
TIPO_CLONES = [u"3\u00ba PAVIMENTO", u"4\u00ba PAVIMENTO", u"5\u00ba PAVIMENTO", u"6\u00ba PAVIMENTO",
               u"7\u00ba PAVIMENTO", u"8\u00ba PAVIMENTO"]
SRC = u"2\u00ba PAVIMENTO"

def build():
    P, O = load()
    # propaga aberturas do pav. TIPO (2o) para 3o..8o  [INFERIDO por identidade geometrica]
    prop = []
    for o in O:
        if o["lvl"] != SRC:
            continue
        for lv in TIPO_CLONES:
            dz = DATUM[lv] - DATUM[SRC]
            c = dict(o)
            c["lvl"] = lv
            c["bb"] = [o["bb"][0], o["bb"][1], o["bb"][2] + dz,
                       o["bb"][3], o["bb"][4], o["bb"][5] + dz]
            c["z"] = (o["z"] or 0) + dz
            c["id"] = o["id"]
            c["uid"] = o["uid"]
            c["_propagated_from"] = o["id"]
            prop.append(c)
    OA = O + prop
    by_lvl = prep(P, OA)
    return P, O, OA, by_lvl

def wall_groups(P):
    g = collections.defaultdict(list)
    for p in P:
        g[(p["parede"], p["lvl"])].append(p)
    return g

def runs(pieces, gap=1.5):
    """Corridas contiguas ao longo do eixo. Retorna [(lo,hi,[pecas])]."""
    ps = sorted(pieces, key=lambda p: p["_s"][0])
    out = []
    for p in ps:
        if out and p["_s"][0] - out[-1][1] <= gap:
            out[-1][1] = max(out[-1][1], p["_s"][1]); out[-1][2].append(p)
        else:
            out.append([p["_s"][0], p["_s"][1], [p]])
    return out
