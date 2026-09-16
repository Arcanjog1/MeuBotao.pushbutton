# -*- coding: utf-8 -*-
"""Paridade Revit (IronPython) x offline (CPython): mesmas paredes (ordem do
Revit), mesmas aberturas atribuidas pelo plugin no Revit, catalogo real."""
import hashlib, json, sys
import tbench as tb
m = tb.m
d = json.load(open(sys.argv[1], encoding="utf-8"))
doc = tb.load_target()
W = dict((w["id"], w) for w in doc["walls"])
axes = []
for wid in d["wall_ids"]:
    w = W[int(wid)]
    axes.append((tb.Line.CreateBound(tb.XYZ(w["p0"][0] * tb.CM2F, w["p0"][1] * tb.CM2F, 0.0),
                                     tb.XYZ(w["p1"][0] * tb.CM2F, w["p1"][1] * tb.CM2F, 0.0)), w["width"] * tb.CM2F, (False, False)))
if d.get("axes_ft") and "--json-axes" not in sys.argv:
    axes = [(tb.Line.CreateBound(tb.XYZ(a[0], a[1], a[2]), tb.XYZ(a[3], a[4], a[5])), a[6], (False, False)) for a in d["axes_ft"]]
opw = [[tuple(o) for o in v] for v in d["openings_per_wall_ft"]]
from core.engine import wall_stepper as _ws_t
from core.engine import small_void_alignment as _sva_t
for _k, _v in (d["cfg"].get("toggles") or {}).items():
    for _mod in (m, _ws_t, _sva_t):
        if hasattr(_mod, _k):
            setattr(_mod, _k, _v)
if "--trace" in sys.argv:
    _orig_pl = _ws_t._pier_layout_avoiding_joints
    def _trace(pier_cm, catalog, lead, trail, seg_start_cm, avoid, **k):
        r = _orig_pl(pier_cm, catalog, lead, trail, seg_start_cm, avoid, **k)
        if seg_start_cm <= 1330 and seg_start_cm + pier_cm >= 1670 and pier_cm < 2500:
            base = _ws_t._pier_ordered_layout(pier_cm, catalog, lead, trail, allow_compensators=k.get("allow_compensators", True),
                                              leading_open_override=k.get("leading_is_open"), trailing_open_override=k.get("trailing_is_open"))
            print("TRACE seg %.9f pier %.9f lead %r trail %r open %r/%r" % (seg_start_cm, pier_cm, lead, trail, k.get("leading_is_open"), k.get("trailing_is_open")))
            print("   avoid", [round(a, 9) for a in sorted(avoid)][:12], "voids", [round(v, 6) for v in sorted(k.get("target_void_positions_cm") or [])][:10])
            print("   baseline", base[:3] if base else base, "chosen", r[:3] if r else r)
            st = _ws_t._layout_min_joint_stagger_cm
            for alt in [base] + list(_ws_t._pier_forced_bypass_layouts(pier_cm, catalog, lead, trail, allow_compensators=True,
                                                                     leading_is_open=k.get("leading_is_open"), trailing_is_open=k.get("trailing_is_open"))):
                print("     alt", [c for c, _a, _b in alt][:4], "stagger %.12f" % (st(alt, seg_start_cm, avoid) or -1),
                      "coinc", _ws_t._count_joint_coincidences_cm(_ws_t._layout_internal_joint_positions_cm(alt, seg_start_cm), avoid),
                      "align", _ws_t._count_void_alignment_cm(_ws_t._layout_void_positions_cm(alt, catalog, seg_start_cm), k.get("target_void_positions_cm")) if k.get("target_void_positions_cm") else 0,
                      "excess", _ws_t._layout_compensator_run_excess(alt, catalog))
        return r
    _ws_t._pier_layout_avoiding_joints = _trace
if "--quantize" in sys.argv:
    _orig_stagger = _ws_t._layout_min_joint_stagger_cm
    def _q(*a, **k):
        v = _orig_stagger(*a, **k)
        return None if v is None else round(v, 6)
    _ws_t._layout_min_joint_stagger_cm = _q
if d["cfg"].get("spy_wall") is not None:
    exec(open("spy_code.py").read())
    install_spy(_ws_t, int(d["cfg"]["spy_wall"]))
walls, jmap = m.extend_wall_ends_to_junctions(axes, m.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = m.build_wall_graph(walls, jmap)
rw = [[w[0].GetEndPoint(0).X, w[0].GetEndPoint(0).Y, w[0].GetEndPoint(1).X, w[0].GetEndPoint(1).Y] for w in walls]
geom_diff = max(abs(a - b) for x, y in zip(rw, d["walls_ft"]) for a, b in zip(x, y))
catalog = {}
for code, e in d["fill_catalog"].items():
    catalog[code] = dict(e, symbol=None, logical_code=code, source_instance_id=None,
                         cells_local=[{"center_local": tuple(c["center_local"]), "size_local": tuple(c["size_local"])} for c in e["cells_local"]])
base_z = 0.0
num = d["solve"]["num_courses"]
res = m.solve_building_blocks_all_courses(nodes, walls, e2n, opw, catalog, base_z, num,
                                          variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
                                          opening_reinforcement_strategy=d["cfg"]["strategy"])
rows = []
for ci in sorted(res["course_candidates"]):
    for c in res["course_candidates"][ci]:
        o = c["origin_world"]
        rows.append("%d:%s|%s|%.4f|%.4f|%.3f|%.1f|%s" % (ci, c["logical_code"], c.get("wall_idx"), o.X, o.Y, c["length_cm"],
                                                         float(c.get("rotation_deg") or 0.0), c.get("placement_reason")))
if d.get("rows"):
    ra, rb = set(d["rows"]), set(rows)
    print("only_revit", len(ra - rb), sorted(ra - rb)[:8])
    print("only_offline", len(rb - ra), sorted(rb - ra)[:8])
json.dump({"spy": SPY_CALLS if d["cfg"].get("spy_wall") is not None else None, "rows": rows, "parity_trials": res.get("channel_tie_parity_trials", {}).get("accepted")}, open("rows_offline.json", "w"), default=str)
sig = hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()
print(json.dumps({"geom_max_diff_ft": geom_diff, "revit_signature": d["solve"]["signature"], "offline_signature": sig,
                  "equal": sig == d["solve"]["signature"], "revit_pieces": d["solve"]["pieces"],
                  "offline_pieces": sum(len(v) for v in res["course_candidates"].values()),
                  "offline_small_void": {k: v for k, v in res["small_void_alignment"].items() if k != "violations"},
                  "offline_support": res["physical_support"]["counts"],
                  "offline_channel": res["opening_reinforcement"]["validation"]["counts"].get("MISSING_REQUIRED_CHANNEL")}, indent=1))
