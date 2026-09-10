# -*- coding: utf-8 -*-
import json, io, collections, os
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "out")

def load():
    P = [json.loads(l) for l in io.open(os.path.join(OUT, "pieces.jsonl"), encoding="utf-8")]
    O = json.load(io.open(os.path.join(OUT, "openings_raw.json"), encoding="utf-8"))
    return P, O

CANALETA_FAMS = set()
def is_canaleta(f):
    return "CANALETA" in f.upper()
def is_cut(f):
    u = f.upper()
    return "CORTAD" in u
def fam_short(f):
    return f

def axis_of(rot):
    """rot em graus -> 'Y' se parede corre em Y, 'X' se corre em X."""
    r = round((rot or 0.0)) % 180
    return "Y" if r == 90 else "X"

def span(bb, ax):
    """(min,max) ao longo do eixo da parede e (min,max) transversal."""
    if ax == "Y":
        return (bb[1], bb[4]), (bb[0], bb[3])
    return (bb[0], bb[3]), (bb[1], bb[4])

def zrange(bb):
    return (bb[2], bb[5])

def wall_group_key(p):
    return (p["parede"], p["lvl"])
