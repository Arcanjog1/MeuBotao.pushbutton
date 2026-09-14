# -*- coding: utf-8 -*-
"""Paridade Revit (IronPython) x offline (CPython) do solve CHANNEL.

Le um resultado do harness do Revit (ids de parede, aberturas DETECTADAS pelo
plugin por parede, base do nivel) e resolve offline com as MESMAS entradas;
compara a assinatura fisica das fiadas e a validacao CHANNEL.
Uso: py -3 2026-09-14-channel-revit-parity.py <r_ladder_N.json>
"""
import hashlib
import json
import sys

import channel_bench_common as cb

m = cb.m


def signature(cc):
    rows = []
    for ci in sorted(cc):
        for c in cc[ci]:
            o = c["origin_world"]
            rows.append("%d:%s|%s|%.4f|%.4f|%.3f|%s" % (ci, c["logical_code"], c.get("wall_idx"), o.X, o.Y,
                                                        c["length_cm"], c.get("placement_reason")))
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()


def main(path):
    d = json.load(open(path, encoding="utf-8"))
    walls_json = dict((w["id"], w) for w in json.load(open(cb.EV + "/2026-09-10-butanta-test-walls.json",
                                                           encoding="utf-8"))["walls"])
    axes = []
    for wid in d["cfg"]["ids"]:
        w = walls_json[wid]
        axes.append((cb.Line.CreateBound(cb.XYZ(*[float(v) for v in w["p0"]]), cb.XYZ(*[float(v) for v in w["p1"]])),
                     m._cm_to_ft(14.0), (False, False)))
    walls, jmap = m.extend_wall_ends_to_junctions(list(axes), m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jmap)
    opw = [[tuple(o) for o in v] for v in d["openings_per_wall_ft"]]
    base_z = m._cm_to_ft(float(d["cfg"]["level_pe_cm"]))
    num = int(round(float(d["cfg"].get("wall_height_cm", 280.0)) / 20.0))
    catalog = cb.CATALOG
    if d.get("fill_catalog"):
        # catalogo REAL lido no Revit (celulas da geometria da familia)
        catalog = {}
        for code, e in d["fill_catalog"].items():
            catalog[code] = dict(e, symbol=None, logical_code=code, source_instance_id=None,
                                 cells_local=[{"center_local": tuple(c["center_local"]),
                                               "size_local": tuple(c["size_local"])} for c in e["cells_local"]])
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, opw, catalog, base_z, num,
                                              variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
                                              opening_reinforcement_strategy=d["cfg"].get("strategy"))
    sig = signature(res["course_candidates"])
    val = (res.get("opening_reinforcement") or {}).get("validation", {}).get("counts")
    out = {"revit_signature": d["solve"]["signature"], "offline_signature": sig,
           "equal": sig == d["solve"]["signature"],
           "revit_pieces": d["solve"]["pieces"], "offline_pieces": sum(len(v) for v in res["course_candidates"].values()),
           "revit_validation": d["solve"]["channel_validation"], "offline_validation": val}
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
