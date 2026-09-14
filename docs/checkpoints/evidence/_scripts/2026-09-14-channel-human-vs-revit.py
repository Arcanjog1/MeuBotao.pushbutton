# -*- coding: utf-8 -*-
"""HUMANO (1o PAV) x SOLVER CHANNEL executado NO REVIT (bancada, 2o PAV), com o
comparador ENDURECIDO (channel_strict_compare.py, auditoria 2026-09-14).

As pecas por fiada vem do solve offline com as MESMAS entradas do harness
(paredes por id, aberturas DETECTADAS pelo plugin, base do nivel, catalogo lido
no Revit); a comparacao so' roda se a assinatura fisica offline for IDENTICA a'
do Revit (paridade). Aberturas casadas ao humano por parede + sobreposicao do
vao em coordenada de mundo (sem ElementId do TARGET).
Uso: py -3 2026-09-14-channel-human-vs-revit.py <r_final34_run.json> <saida.json>
"""
import hashlib
import json
import os
import sys

import channel_bench_common as cb
from channel_strict_compare import StrictComparator
from core.engine import opening_reinforcement as orf

m = cb.m


def signature(cc):
    rows = []
    for ci in sorted(cc):
        for c in cc[ci]:
            o = c["origin_world"]
            rows.append("%d:%s|%s|%.4f|%.4f|%.3f|%s" % (ci, c["logical_code"], c.get("wall_idx"), o.X, o.Y,
                                                        c["length_cm"], c.get("placement_reason")))
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()


d = json.load(open(sys.argv[1], encoding="utf-8"))
walls_json = dict((w["id"], w) for w in json.load(open(os.path.join(cb.EV, "2026-09-10-butanta-test-walls.json"),
                                                       encoding="utf-8"))["walls"])
human = json.load(open(os.path.join(cb.EV, "2026-09-14-channel-human-runs.json"), encoding="utf-8"))["records"]
seq = json.load(open(os.path.join(cb.EV, "2026-09-10-butanta-human-sequences.json"), encoding="utf-8"))
ids = d["cfg"]["ids"]
axes = []
for wid in ids:
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
    catalog = {}
    for code, e in d["fill_catalog"].items():
        catalog[code] = dict(e, symbol=None, logical_code=code, source_instance_id=None,
                             cells_local=[{"center_local": tuple(c["center_local"]),
                                           "size_local": tuple(c["size_local"])} for c in e["cells_local"]])
res = m.solve_building_blocks_all_courses(nodes, walls, e2n, opw, catalog, base_z, num,
                                          variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
                                          opening_reinforcement_strategy=d["cfg"].get("strategy"))
sig = signature(res["course_candidates"])
if sig != d["solve"]["signature"]:
    raise SystemExit("PARIDADE QUEBRADA: offline %s x Revit %s" % (sig, d["solve"]["signature"]))

cmp_ = StrictComparator(m, orf, walls, nodes, res, ids, walls_json, human, seq)
opening_ids = []
unmatched = []
for wi, ops in enumerate(opw):
    row = []
    for op in ops:
        a, b = sorted((cmp_.to_human_t(wi, m._ft_to_cm(op[0])), cmp_.to_human_t(wi, m._ft_to_cm(op[1]))))
        cands = [h["id"] for h in human if h.get("wall") == ids[wi]
                 and min(b, h["t"][1]) - max(a, h["t"][0]) > 0.5 * (b - a)]
        if len(cands) != 1:
            unmatched.append((ids[wi], round(a, 1), round(b, 1), len(cands)))
        row.append(cands[0] if len(cands) == 1 else None)
    opening_ids.append(row)
out = cmp_.compare(opening_ids)
out["source"] = os.path.basename(sys.argv[1])
out["parity_signature"] = sig
out["openings_matched"] = len(set(r["opening_id"] for r in out["rows"] if r["opening_id"] is not None))
out["unmatched"] = unmatched
out["validation"] = res["opening_reinforcement"]["validation"]["counts"]
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print(json.dumps(dict((k, out[k]) for k in ("summary", "by_role", "openings_matched", "unmatched", "parity_signature")),
                 indent=1))
