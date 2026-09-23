# -*- coding: utf-8 -*-
"""Modelo fisico UNICO de pecas (Revit humano, Revit TARGET e candidatos do
solver) para medir defeitos com a MESMA regua. Evidencia, nao norma.

Geometria dos vazados medida nas familias reais (mcp_cells.py): intervalos
VAZADOS ao longo do X local, com meia largura transversal de 4,5 cm.
"""
import collections
import math

VOID_X = {
    "B39": [(-17.0, -1.25), (1.25, 17.0)],
    "B34": [(-14.5, -3.75), (-1.25, 14.5)],
    "B54": [(-24.5, -8.75), (-6.25, 6.25), (8.75, 24.5)],
    "B19": [(-7.0, 7.0)],
}
SMALL_VOID = {"B34": (-14.5, -3.75)}
LEN = {"B39": 39.0, "B34": 34.0, "B54": 54.0, "B19": 19.0, "C09": 9.0, "C04": 4.0,
       "K39": 39.0, "K34": 34.0, "K19": 19.0}
VOID_HALF_Y = 4.5
HALF_W = 7.0
SOLVER_CODE = {"B39": "B39", "B34": "B34", "B54": "B54", "B19": "B19", "C09": "C09", "C04": "C04",
               "CHANNEL_U_39": "K39", "CHANNEL_U_34": "K34", "CHANNEL_U_19": "K19", "CHANNEL_U_CUT": "KV"}


class P(object):
    __slots__ = ("course", "code", "cx", "cy", "dx", "dy", "length", "mir", "wall", "src", "lo", "hi")

    def __init__(self, course, code, cx, cy, dx, dy, length, mir=False, wall=None, src=None):
        self.course, self.code = course, code
        self.cx, self.cy, self.dx, self.dy = cx, cy, dx, dy
        self.length, self.mir, self.wall, self.src = length, mir, wall, src
        self.lo = self.hi = None

    def local(self, x, y):
        rx, ry = x - self.cx, y - self.cy
        u = rx * self.dx + ry * self.dy
        v = -rx * self.dy + ry * self.dx
        return (-u if self.mir else u), v

    def world(self, u, v):
        if self.mir:
            u = -u
        return self.cx + u * self.dx - v * self.dy, self.cy + u * self.dy + v * self.dx

    def contains(self, x, y, eps=1e-6):
        u, v = self.local(x, y)
        return abs(u) <= self.length / 2.0 + eps and abs(v) <= HALF_W + eps

    def is_void(self, x, y):
        """True se (x,y) cai num vazado VERTICAL da peca (grout passa)."""
        u, v = self.local(x, y)
        if abs(v) > VOID_HALF_Y:
            return False
        for a, b in VOID_X.get(self.code, ()):
            if a <= u <= b:
                return True
        return False

    def bbox(self):
        hx = abs(self.dx) * self.length / 2.0 + abs(self.dy) * HALF_W
        hy = abs(self.dy) * self.length / 2.0 + abs(self.dx) * HALF_W
        return self.cx - hx, self.cy - hy, self.cx + hx, self.cy + hy


def from_revit(recs):
    out = []
    for r in recs:
        code = r["code"]
        base = code.rstrip("H") if code.endswith("H") and code[:-1] in LEN else code
        bb = r["bb"]
        cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
        bx = r["bx"]
        n = math.hypot(bx[0], bx[1]) or 1.0
        # bbox das familias = comprimento + 1 cm em CADA ponta (medido)
        along_bb = abs(bb[3] - bb[0]) if abs(bx[0]) > 0.5 else abs(bb[4] - bb[1])
        length = LEN.get(base) or (along_bb - 2.0)
        p = P(r["course"], base, cx, cy, bx[0] / n, bx[1] / n, length, mir=False,
              wall=(r["wall"].id if r.get("wall") is not None else None), src=r["id"])
        if "lo" in r:
            p.lo, p.hi = r["lo"] + 1.0, r["hi"] - 1.0
        out.append(p)
    return out


def from_solver(ctx, res, m, wall_ids):
    F = 30.48
    out = []
    for ci, cands in (res.get("course_candidates") or {}).items():
        for c in cands:
            code = SOLVER_CODE.get(c["logical_code"], c["logical_code"])
            o, xd = c["origin_world"], c["x_dir"]
            length = float(c.get("length_cm") or LEN.get(code, 0.0))
            wi = c.get("wall_idx")
            p = P(ci, code, o.X * F, o.Y * F, xd.X, xd.Y, length, mir=bool(c.get("mirrored")),
                  wall=(wall_ids[wi] if wi is not None else None), src=c)
            if wi is not None:
                p0, _p1, d, _l, _t = m._wall_axis_and_length(ctx["walls"], wi)
                lo, hi = m._candidate_extent_on_wall_axis(c, p0, d)
                p.lo, p.hi = lo, hi
            out.append(p)
    return out


class Grid(object):
    """Indice espacial por fiada."""

    def __init__(self, pieces, cell=40.0):
        self.cell = cell
        self.idx = collections.defaultdict(list)
        for p in pieces:
            x0, y0, x1, y1 = p.bbox()
            for gx in range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1):
                for gy in range(int(math.floor(y0 / cell)), int(math.floor(y1 / cell)) + 1):
                    self.idx[(p.course, gx, gy)].append(p)

    def at(self, course, x, y):
        key = (course, int(math.floor(x / self.cell)), int(math.floor(y / self.cell)))
        return [p for p in self.idx.get(key, ()) if p.contains(x, y)]


def small_void_alignment(pieces, max_course, step=1.0):
    """Para cada B34 (fiada c), vazado menor x fiadas c-1 e c+1: fracao da area
    do vazado coberta por MACICO (septo/parede/compensador/pastilha/fundo de
    canaleta) de peca da fiada vizinha; fracao sobre vazado; fracao sem peca."""
    g = Grid(pieces)
    rows = []
    for p in pieces:
        if p.code not in SMALL_VOID:
            continue
        a, b = SMALL_VOID[p.code]
        for other in (p.course - 1, p.course + 1):
            if other < 0 or other > max_course:
                continue
            solid = void = empty = 0
            by_code = collections.Counter()
            u = a + step / 2.0
            while u < b:
                v = -VOID_HALF_Y + step / 2.0
                while v < VOID_HALF_Y:
                    x, y = p.world(u, v)
                    hits = g.at(other, x, y)
                    if not hits:
                        empty += 1
                    elif any(h.is_void(x, y) for h in hits):
                        void += 1
                    else:
                        solid += 1
                        by_code[hits[0].code] += 1
                    v += step
                u += step
            tot = float(solid + void + empty)
            rows.append({"piece": p, "other_course": other, "solid": solid / tot, "void": void / tot,
                         "empty": empty / tot, "solid_codes": dict(by_code)})
    return rows
