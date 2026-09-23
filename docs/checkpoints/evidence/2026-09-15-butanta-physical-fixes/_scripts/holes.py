# -*- coding: utf-8 -*-
"""Buracos (trecho de parede sem peca, fora de vao) e pecas sem apoio, na
MESMA regua para humano, TARGET e solver. Evidencia/diagnostico."""
import collections
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmodel  # noqa: E402

MASONRY = ("B39", "B34", "B54", "B19", "C09", "C04")


def openings_by_wall(walls, openings_world):
    """openings_world: [(wall_id, t_lo, t_hi, sill, head)] em cm."""
    out = collections.defaultdict(list)
    for w, tl, th, s, h in openings_world:
        out[w].append((tl, th, s, h))
    return out


def course_z(c):
    return 20.0 * c + 10.0


def scan(walls, pieces, ops_by_wall, courses, wall_filter=None, step=1.0, min_run=4.0):
    g = pmodel.Grid(pieces)
    holes = []
    for w in walls:
        if wall_filter is not None and w.id not in wall_filter:
            continue
        for c in range(courses):
            z = course_z(c)
            run = None
            t = step / 2.0
            while t < w.L:
                x = w.p0[0] + w.u[0] * t
                y = w.p0[1] + w.u[1] * t
                occupied = bool(g.at(c, x, y))
                in_op = any(tl - 0.5 <= t <= th + 0.5 and s - 0.5 <= z <= h + 0.5 for tl, th, s, h in ops_by_wall.get(w.id, ()))
                if not occupied and not in_op:
                    if run is None:
                        run = [t, t]
                    else:
                        run[1] = t
                else:
                    if run is not None and run[1] - run[0] + step >= min_run:
                        holes.append((w.id, c, round(run[0] - step / 2, 1), round(run[1] + step / 2, 1)))
                    run = None
                t += step
            if run is not None and run[1] - run[0] + step >= min_run:
                holes.append((w.id, c, round(run[0] - step / 2, 1), round(run[1] + step / 2, 1)))
    return holes


def unsupported(pieces, ops_world_xy, courses, min_support=0.5, step=1.0):
    """Peca de alvenaria (fiada >= 1) cuja projecao na fiada de baixo tem menos
    de `min_support` do comprimento apoiado em peca (qualquer parede).
    ops_world_xy: funcao (x, y, z) -> True se o ponto cai num vao ativo."""
    g = pmodel.Grid(pieces)
    rows = []
    for p in pieces:
        if p.course < 1 or p.code not in MASONRY or p.course >= courses:
            continue
        n = sup = over_void = 0
        u = -p.length / 2.0 + step / 2.0
        while u < p.length / 2.0:
            x, y = p.world(u, 0.0)
            n += 1
            if g.at(p.course - 1, x, y):
                sup += 1
            elif ops_world_xy(x, y, course_z(p.course - 1)):
                over_void += 1
            u += step
        frac = sup / float(n) if n else 0.0
        if frac < min_support:
            rows.append((p, round(frac, 2), round(over_void / float(n), 2) if n else 0.0))
    return rows
