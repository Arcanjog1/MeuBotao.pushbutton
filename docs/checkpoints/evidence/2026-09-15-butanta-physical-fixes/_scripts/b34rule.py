# -*- coding: utf-8 -*-
"""Regra candidata B34_SMALL_VOID_ALIGNMENT medida no humano e no target.

Para cada B34 (fiada c) e cada fiada vizinha c+-1: a peca de ALVENARIA
(B39/B34/B54/B19) que cobre o CENTRO do vazado menor tem de oferecer, naquele
ponto, um vazado MENOR (B34) ou o vazado central do B54. Canaleta,
compensador, pastilha ou ausencia de peca nao contam (fora do escopo)."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmodel  # noqa: E402

SMALLISH = {"B34": [(-14.5, -3.75)], "B54": [(-6.25, 6.25)]}
MASONRY = ("B39", "B34", "B54", "B19")


def classify(pieces, max_course, tol_cm=1.5):
    g = pmodel.Grid(pieces)
    out = collections.Counter()
    bad = []
    for p in pieces:
        if p.code != "B34":
            continue
        a, b = pmodel.SMALL_VOID["B34"]
        uc = (a + b) / 2.0
        x, y = p.world(uc, 0.0)
        for other in (p.course - 1, p.course + 1):
            if other < 0 or other > max_course:
                continue
            hits = [h for h in g.at(other, x, y) if h.code in MASONRY]
            if not hits:
                others = g.at(other, x, y)
                out["fora_de_escopo:" + (others[0].code if others else "vazio")] += 1
                continue
            h = hits[0]
            u, v = h.local(x, y)
            ok = False
            for lo, hi in SMALLISH.get(h.code, ()):
                # centro do vazado menor dentro do vazado menor/central da vizinha
                if lo - tol_cm <= u <= hi + tol_cm:
                    ok = True
            key = ("OK:" if ok else "VIOLA:") + h.code
            out[key] += 1
            if not ok:
                bad.append((p, other, h))
    return out, bad
