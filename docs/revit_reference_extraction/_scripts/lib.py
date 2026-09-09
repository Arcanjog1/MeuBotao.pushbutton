# -*- coding: utf-8 -*-
import json, os, collections
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
LEVELS = {"01. TER":750-1510,"02. G02":1065-1510,"03. G03":1430-1510,"04. TGD":340,"05. TP1":611,
          "08. TP1":1424,"10. TP1":1966,"20. TP1":4676,"21. COB":4947}
def load(fn):
    with open(os.path.join(RAW,fn),encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def all_blocks():
    for fn in sorted(os.listdir(RAW)):
        if fn.startswith("blocks_"):
            for r in load(fn): yield r
def axis(r):
    hx = r.get("hx")
    if hx is None: return None
    return "X" if abs(hx) > 0.5 else "Y"
def geom(r):
    """retorna (eixo, a0, a1, t_centro, z0, z1) no eixo do comprimento"""
    b=r["bb"]; ax=axis(r)
    if ax=="X": return ("X", b[0], b[3], (b[1]+b[4])/2.0, b[2], b[5])
    return ("Y", b[1], b[4], (b[0]+b[3])/2.0, b[2], b[5])
def klass(r):
    f=(r["family"] or "").upper(); t=(r["type"] or "").upper()
    if f.startswith("VERGA"): return "LINTEL"
    if f.startswith("CONTRAVERGA"): return "COUNTER_LINTEL"
    if "CANALETA" in f: return "CHANNEL_CUT" if "CORTAD" in f else "CHANNEL"
    if "CORTAD" in f: return "CUT_BLOCK"
    return "BLOCK"
def vedacao(r):
    return "VEDA" in ((r["type"] or "").upper())
