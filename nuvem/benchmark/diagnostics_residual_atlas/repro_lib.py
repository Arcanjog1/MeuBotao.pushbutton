# -*- coding: utf-8 -*-
"""Reprodutores MINIMOS (item 19) - plantas sinteticas de 2-5 paredes que
reproduzem os clusters principais, resolvidas com o MESMO motor
(solve_building_blocks_all_courses) e o catalogo padrao dos testes.
Somente leitura do motor; nada de producao e' alterado."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402

m = al.engine()
XYZ, Line = m.XYZ, m.Line
F = m.FEET_PER_METER
NUM_COURSES = 4


def ft(cm):
    return cm / 100.0 * F


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _cell(center_cm, size_cm, width_cm=8.0):
    return {"center_local": (ft(center_cm), 0.0), "size_local": (ft(size_cm), ft(width_cm))}


def _block(code, length_cm, cells):
    return {"symbol": None, "logical_code": code, "length_cm": float(length_cm), "height_cm": 19.0,
            "width_cm": 14.0, "cells_local": cells, "is_special_bond": code in ("B34", "B54"),
            "is_compensator": code in ("C09", "C04"), "source_instance_id": None}


def catalog():
    return {
        "B39": _block("B39", 39, [_cell(-9.9, 15.7), _cell(9.9, 15.8)]),
        "B34": _block("B34", 34, [_cell(-10.2, 10.7), _cell(7.4, 15.7)]),
        "B54": _block("B54", 54, [_cell(-19.5, 15.8), _cell(0.0, 12.5), _cell(19.5, 15.8)]),
        "B19": _block("B19", 19, [_cell(0.0, 15.7)]),
        "C09": _block("C09", 9, []),
        "C04": _block("C04", 4, []),
    }


def solve(lines, openings=None, thickness_cm=14.0, num_courses=NUM_COURSES, already_extended=False):
    """openings: {wall_index: [(t_lo_cm, t_hi_cm, sill_cm, head_cm), ...]}"""
    walls = [(line, ft(thickness_cm), (False, False)) for line in lines]
    search = 0.0 if already_extended else m.JUNCTION_FACE_SEARCH_FT
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, search)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    per_wall = []
    for i in range(len(walls)):
        per_wall.append([(ft(a), ft(b), ft(s), ft(h)) for (a, b, s, h) in (openings or {}).get(i, [])])
    result = m.solve_building_blocks_all_courses(nodes, walls, end_to_node, per_wall, catalog(),
                                                 base_z_abs=0.0, num_courses=num_courses)
    run = {"solve_result": result, "walls_to_create": walls, "nodes": nodes, "end_to_node": end_to_node,
           "openings_per_wall": per_wall, "catalog": catalog(), "base_z_ft": 0.0, "num_courses": num_courses}
    return run


def rows(run, wall_idx, courses=(0, 1)):
    out = []
    for ci in courses:
        out.append((ci, al.fmt_items(al.wall_course_items(run, wall_idx, ci, include_secondary=True))))
    return out


def describe(run, title):
    print("=== " + title)
    for ni, node in enumerate(run["nodes"]):
        if node.get("kind") in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
            pcs = [(c["course"], c["wall_idx"], c["logical_code"], c["placement_reason"]) for c in run["solve_result"]["candidates"] if c.get("node_index") == ni]
            pcs = sorted(set(pcs))
            print("  node", ni, node["kind"], [round(v) for v in al.xyz_cm(node["point"])], pcs)
    for wi in range(len(run["walls_to_create"])):
        _p0, _p1, _d, L, _t = al.wall_axis_cm(run["walls_to_create"], wi)
        print("  wall", wi, "len %.2f" % L)
        for ci, txt in rows(run, wi):
            print("     r%d %s: %s" % (ci, al.course_letter(ci), txt))
    nm = run["solve_result"].get("non_modular") or []
    if nm:
        print("  non_modular:", sorted(set((x["wall_idx"], x["course"], x.get("conflict") or "fit", round(x["current_length_cm"], 2)) for x in nm)))
    fails = run["solve_result"].get("intersection_failures") or []
    if fails:
        print("  intersection_failures:", [(n, r[:60]) for n, r in fails])
    return run
