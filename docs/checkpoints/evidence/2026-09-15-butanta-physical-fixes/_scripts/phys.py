# -*- coding: utf-8 -*-
"""Leitura FISICA de pecas extraidas do Revit (humano ou TARGET), independente
do solver. Evidencia/diagnostico, nao norma.

- codigo logico por familia;
- fiada pelo Z da origem (grade de 20 cm a partir de z=1);
- parede dona: carimbo (TARGET) ou geometria (eixo mais proximo, humano);
- extensao ao longo do eixo da parede (t, cm) e lado transversal;
- vazados em coordenadas locais medidos no Revit (mcp_cells.py).
"""
import collections
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CODE_BY_FAMILY = [
    ("BLOCO INTEIRO CORTADO", "B39H"), ("BLOCO INTEIRO", "B39"),
    ("BLOCO 34 CORTADO", "B34H"), ("BLOCO 34", "B34"),
    ("BLOCO 54 CORTADO", "B54H"), ("BLOCO 54", "B54"),
    ("BLOCO CANALETA CORTADO", "KV"),
    ("MEIO BLOCO CORTADO", "B19H"), ("MEIO BLOCO", "B19"),
    ("COMPENSADOR CORTADO 14x19x9 (deitado)", "C09DH"), ("COMPENSADOR 14x19x9 (deitado)", "C09D"),
    ("COMPENSADOR CORTADO", "C09H"), ("COMPENSADOR", "C09"),
    ("PASTILHA CORTADA", "C04H"), ("PASTILHA", "C04"),
    ("CANALETA INTEIRA", "K39"), ("CANALETA 34", "K34"), ("MEIA CANALETA", "K19"),
    ("CANALETA J CORTADA", "KJV"), ("CANALETA J", "KJ"),
]
LENGTH = {"B39": 39.0, "B34": 34.0, "B54": 54.0, "B19": 19.0, "C09": 9.0, "C04": 4.0,
          "K39": 39.0, "K34": 34.0, "K19": 19.0, "KJ": 19.0}
# solidos ao longo do X local na meia espessura (medido no Revit, cm)
SOLID_X = {
    "B39": [(-19.5, -17.0), (-1.25, 1.25), (17.0, 19.5)],
    "B34": [(-17.0, -14.5), (-3.75, -1.25), (14.5, 17.0)],
    "B54": [(-27.0, -24.5), (-8.75, -6.25), (6.25, 8.75), (24.5, 27.0)],
    "B19": [(-9.5, -7.0), (7.0, 9.5)],
}
SMALL_VOID_X = {"B34": (-14.5, -3.75), "B54": (-6.25, 6.25)}
SPECIAL = ("C09", "C04", "B19")


def code_of(fam, typ):
    for prefix, code in CODE_BY_FAMILY:
        if typ.upper().startswith(prefix.upper()) or fam.upper().startswith(prefix.upper()):
            return code
    return "?"


def load(path):
    return json.load(open(path, encoding="utf-8"))


def base_code(code):
    return code.rstrip("H").rstrip("D") if code not in ("KV", "KJV") else code


class Wall(object):
    def __init__(self, wid, p0, p1, uid=None):
        self.id, self.uid = wid, uid
        self.p0, self.p1 = p0, p1
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        self.L = math.hypot(dx, dy)
        self.u = (dx / self.L, dy / self.L)
        self.n = (-self.u[1], self.u[0])
        self.axis = "X" if abs(self.u[0]) > 0.5 else "Y"

    def t_of(self, x, y):
        return (x - self.p0[0]) * self.u[0] + (y - self.p0[1]) * self.u[1]

    def lat_of(self, x, y):
        return (x - self.p0[0]) * self.n[0] + (y - self.p0[1]) * self.n[1]


def piece_record(p, level_z0=0.0):
    code = code_of(p["fam"], p["typ"])
    ox, oy, oz = p["o"]
    bx = p["bx"]
    ang_axis = "X" if abs(bx[0]) > 0.5 else "Y"
    bb = p.get("bb")
    course = int(round((oz - 1.0) / 20.0))
    rec = dict(id=p["id"], code=code, fam=p["fam"], x=ox, y=oy, z=oz, bx=(bx[0], bx[1]),
               axis=ang_axis, course=course, bb=bb, cm=p.get("cm"), len_param=p.get("len_param"),
               mir=p.get("mir"))
    if bb:
        rec["ztop"] = bb[5]
        rec["zbot"] = bb[2]
    return rec


def along_extent(rec, wall):
    """(lo, hi) ao longo do eixo da parede pela bbox (paredes ortogonais)."""
    bb = rec["bb"]
    ts = [wall.t_of(bb[0], bb[1]), wall.t_of(bb[3], bb[4]), wall.t_of(bb[0], bb[4]), wall.t_of(bb[3], bb[1])]
    return min(ts), max(ts)


def assign_walls(recs, walls, by_stamp=None, lat_tol=8.0, t_slack=40.0):
    """Parede dona: carimbo quando existe; senao o eixo PARALELO mais proximo
    que contem a origem."""
    uid2wall = {w.uid: w for w in walls if w.uid}
    for r in recs:
        w = None
        cm = r.get("cm") or ""
        if by_stamp and "parede=" in cm:
            w = uid2wall.get(cm.split("parede=")[1].split("|")[0])
        if w is None:
            best = None
            for ww in walls:
                if ww.axis != r["axis"]:
                    continue
                lat = abs(ww.lat_of(r["x"], r["y"]))
                t = ww.t_of(r["x"], r["y"])
                if lat <= lat_tol and -t_slack <= t <= ww.L + t_slack and (best is None or lat < best[0]):
                    best = (lat, ww)
            w = best[1] if best else None
        r["wall"] = w
        if w is not None and r.get("bb"):
            r["lo"], r["hi"] = along_extent(r, w)
    return recs


def by_wall_course(recs):
    out = collections.defaultdict(list)
    for r in recs:
        if r.get("wall") is None or "lo" not in r:
            continue
        out[(r["wall"].id, r["course"])].append(r)
    for k in out:
        out[k].sort(key=lambda r: (r["lo"], r["hi"]))
    return out


def opening_span_on_wall(op, wall, lat_tol=10.0):
    """Vao real (t_lo, t_hi) sobre `wall`: largura pelo parametro, centro pela
    geometria quando houver, senao pela bbox (familias deste projeto: bbox =
    retangulo do vao)."""
    bb = op.get("bb")
    if not bb:
        return None
    cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
    if abs(wall.lat_of(cx, cy)) > lat_tol:
        return None
    ts = sorted([wall.t_of(bb[0], bb[1]), wall.t_of(bb[3], bb[4])])
    width = op.get("Largura_abertura") or (ts[1] - ts[0])
    tc = (ts[0] + ts[1]) / 2.0
    if tc < -5 or tc > wall.L + 5:
        return None
    sill = op.get("Peitoril") or 0.0
    head = sill + (op.get("Altura_abertura") or 0.0)
    return (tc - width / 2.0, tc + width / 2.0, sill, head)
