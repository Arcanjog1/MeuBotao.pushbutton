# -*- coding: utf-8 -*-
"""Casamento geometrico peca<->abertura, independente do rotulo 'Parede'."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_lib import *

TOL = 0.6

def prep(P, O):
    by_lvl = collections.defaultdict(list)
    for p in P:
        ax = axis_of(p["rot"])
        (a0, a1), (b0, b1) = span(p["bb"], ax)
        p["_ax"] = ax; p["_s"] = (a0, a1); p["_t"] = (b0, b1)
        p["_tc"] = (b0 + b1) / 2.0
        p["_z"] = (p["bb"][2], p["bb"][5])
        by_lvl[p["lvl"]].append(p)
    for o in O:
        ax = axis_of(o["rot"])
        (a0, a1), (b0, b1) = span(o["bb"], ax)
        o["_ax"] = ax; o["_s"] = (a0, a1); o["_t"] = (b0, b1)
        o["_tc"] = (b0 + b1) / 2.0
        o["_datum"] = o["bb"][2]
        o["_zt"] = o["bb"][5]
        o["_zb"] = o["bb"][2] + o["peitoril"]
    return by_lvl

def wall_pieces(o, by_lvl):
    """Pecas na MESMA linha de parede da abertura (mesmo eixo, mesmo plano)."""
    out = []
    for p in by_lvl.get(o["lvl"], ()):
        if p["_ax"] != o["_ax"]:
            continue
        if abs(p["_tc"] - o["_tc"]) > 3.0:
            continue
        out.append(p)
    return out

def crossing(pieces, s0, s1, tol=TOL):
    """Pecas cujo vao horizontal intersecta (s0,s1)."""
    return [p for p in pieces if p["_s"][1] > s0 + tol and p["_s"][0] < s1 - tol]

def course_at(pieces, z, tol=TOL):
    return [p for p in pieces if abs(p["_z"][0] - z) < tol]

def wall_physical_key(o):
    """Identidade fisica estavel da linha de parede (nao usa ElementId)."""
    return "%s|%s|t%.0f|L%s" % (o["_ax"], o["lvl"], round(o["_tc"]), o["lvl_id"])
