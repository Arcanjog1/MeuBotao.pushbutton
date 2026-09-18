# Harness BUTANTA (missao 2026-09-15) no Revit real (IronPython, via MCP).
# Fluxo "paredes existentes" com as 34 paredes de alvenaria do TARGET, handler
# real (_execute_solve/_execute_create, beta controlado). Config em r_cfg.json.
# SEGURANCA: so' escreve no TARGET "butanta testes"; o HUMANO nunca recebe
# Transaction (IsModified conferido antes e depois). Nada e' salvo.
import sys
import json
import hashlib
import math
from Autodesk.Revit.DB import (XYZ, FilteredElementCollector, FamilyInstance, BuiltInParameter, Transaction, Wall,
                               ElementId)
from System.Collections.Generic import List

if not hasattr(math, "isfinite"):
    math.isfinite = lambda v: not (math.isinf(v) or math.isnan(v))

NL = chr(10)
CLONE = "C:/Users/twitc/Documents/AgentOrchestrator/MeuBotao.pushbutton"
cfg = json.loads(System.IO.File.ReadAllText(OUTDIR + "r_cfg.json"))
out = {"cfg": cfg, "steps": []}
clock = System.Diagnostics.Stopwatch.StartNew()


def step(label, **kw):
    kw["label"] = label
    kw["t_s"] = round(clock.Elapsed.TotalSeconds, 3)
    out["steps"].append(kw)
    dump(cfg.get("out", "r_out.json"), out)


app = __revit__.Application
T = __revit__.ActiveUIDocument.Document
humans = [d for d in app.Documents if (d.PathName or "").endswith("ENVIO) (1).rvt")]
assert T.Title == "butanta testes", T.Title
assert T.PathName.lower().endswith("butanta testes.rvt"), T.PathName
assert len(humans) == 1, len(humans)
H = humans[0]
assert not H.Equals(T)
out["human_modified_before"] = H.IsModified
assert H.IsModified is False
out["target_modified_before"] = T.IsModified
step("START", target=T.Title, human=H.Title)

for key in list(sys.modules.keys()):
    if key == "core" or key.startswith("core."):
        del sys.modules[key]
nuvem = CLONE + "/nuvem"
if nuvem in sys.path:
    sys.path.remove(nuvem)
sys.path.insert(0, nuvem)
import core.wall_modeling as wm
from core.engine import opening_reinforcement as orf
assert wm.doc.Equals(T), "modulo carregado contra outro documento"
assert not wm.doc.Equals(H)
out["module_file"] = wm.__file__
from core.engine import wall_stepper as _ws_t
from core.engine import small_void_alignment as _sva_t
for _k, _v in (cfg.get("toggles") or {}).items():
    for _mod in (wm, _ws_t, _sva_t):
        if hasattr(_mod, _k):
            setattr(_mod, _k, _v)
step("MODULE_LOADED", toggles=cfg.get("toggles"))
if cfg.get("spy_wall") is not None:
    exec(System.IO.File.ReadAllText(OUTDIR + "../spy_code.py"))
    install_spy(_ws_t, int(cfg["spy_wall"]))


def stamped_instances():
    found = []
    for el in FilteredElementCollector(T).OfClass(FamilyInstance).WhereElementIsNotElementType():
        p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        parsed = wm._parse_block_lot_stamp(p.AsString() if p is not None else None)
        if parsed is not None:
            found.append((el, parsed))
    return found


if cfg.get("purge_all_stamped"):
    olds = stamped_instances()
    lots = {}
    for _el, parsed in olds:
        lots[parsed[1]] = lots.get(parsed[1], 0) + 1
    if olds:
        ids = List[ElementId]()
        for el, _p in olds:
            ids.Add(el.Id)
        assert T.Equals(__revit__.ActiveUIDocument.Document) and not T.Equals(H)
        t = Transaction(T, "BUTANTA missao - remove lotes carimbados do plugin")
        t.Start()
        T.Delete(ids)
        t.Commit()
    step("PURGE", removed=len(olds), lots=lots, remaining=len(stamped_instances()))

want = set(int(i) for i in cfg["ids"])
wall_elements = [w for w in FilteredElementCollector(T).OfClass(Wall) if eid(w.Id) in want]
wall_elements.sort(key=lambda w: cfg["ids"].index(eid(w.Id)))
assert len(wall_elements) == len(want), (len(wall_elements), len(want))
(walls_to_create, created_walls_by_axis, wall_ids, level, wall_height_ft,
 skipped) = wm._build_existing_walls_selection(wall_elements)
out["axes_ft"] = [[w[0].GetEndPoint(0).X, w[0].GetEndPoint(0).Y, w[0].GetEndPoint(0).Z,
                  w[0].GetEndPoint(1).X, w[0].GetEndPoint(1).Y, w[0].GetEndPoint(1).Z, w[1]] for w in walls_to_create]
all_openings, note = wm.collect_opening_instances("auto", None)
diag = {"clamped_opening_count": 0, "opening_center_gap_max_ft": 0.0, "opening_off_center_count": 0,
        "assignments": [], "unassigned_openings": []}
opw = wm.assign_openings_to_walls(walls_to_create, all_openings, diag)
walls_to_create, jmap = wm.extend_wall_ends_to_junctions(walls_to_create, wm.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = wm.build_wall_graph(walls_to_create, jmap)
base_z = wm._level_internal_elevation_ft(level)
out["walls"] = len(walls_to_create)
out["wall_ids"] = [eid(i) for i in wall_ids]
out["openings_detected"] = len(all_openings)
out["openings_assigned"] = sum(len(v) for v in opw)
out["openings_unassigned"] = len(diag["unassigned_openings"])
out["openings_per_wall_ft"] = [[list(o) for o in v] for v in opw]
out["walls_ft"] = [[w[0].GetEndPoint(0).X, w[0].GetEndPoint(0).Y, w[0].GetEndPoint(1).X, w[0].GetEndPoint(1).Y]
                   for w in walls_to_create]
out["wall_height_cm"] = wall_height_ft * FT
step("INPUT", walls=len(walls_to_create), openings=len(all_openings), assigned=out["openings_assigned"],
     base_z_cm=base_z * FT, level=level.Name, height_cm=wall_height_ft * FT)

cat, miss = wm.load_fixed_block_catalog(T)
ccat, cmiss = wm.load_channel_family_catalog(T)
out["catalog_missing"] = miss
out["channel_catalog_missing"] = cmiss
out["fill_catalog"] = dict((k, {"length_cm": v["length_cm"], "height_cm": v["height_cm"], "width_cm": v["width_cm"],
                                "is_special_bond": v["is_special_bond"], "is_compensator": v["is_compensator"],
                                "cells_local": [{"center_local": list(c["center_local"]),
                                                 "size_local": list(c["size_local"])} for c in v["cells_local"]]})
                           for k, v in cat.items())
step("CATALOGS", fill=sorted(cat.keys()), channel=sorted(ccat.keys()), missing=len(miss), channel_missing=len(cmiss))

h = wm._PostCreationEventHandler()
h.controlled_beta = True
h.walls_to_create = walls_to_create
h.openings_per_wall = opw
h.wall_graph_nodes = nodes
h.wall_end_to_node = e2n
h.selected_level = level
h.base_z_abs = base_z
h.wall_height_ft = wall_height_ft
h.catalog = cat
h.channel_catalog = ccat
h.created_walls_by_axis = created_walls_by_axis
h.opening_reinforcement_strategy = cfg.get("strategy")
t_solve = clock.Elapsed.TotalSeconds
h._execute_solve()
res = h.solve_result
t_solve = clock.Elapsed.TotalSeconds - t_solve


def signature(cc):
    rows = []
    for ci in sorted(cc):
        for c in cc[ci]:
            o = c["origin_world"]
            rows.append("%d:%s|%s|%.4f|%.4f|%.3f|%.1f|%s" % (ci, c["logical_code"], c.get("wall_idx"), o.X, o.Y,
                                                             c["length_cm"], float(c.get("rotation_deg") or 0.0),
                                                             c.get("placement_reason")))
    if cfg.get("dump_rows"):
        out["rows"] = sorted(rows)
    return hashlib.sha256(NL.join(sorted(rows))).hexdigest()


cc = res.get("course_candidates") or {}
codes = {}
for v in cc.values():
    for c in v:
        codes[c["logical_code"]] = codes.get(c["logical_code"], 0) + 1
rein = res.get("opening_reinforcement") or {}
pf = res.get("beta_preflight") or {}
sva = res.get("small_void_alignment") or {}
sup = res.get("physical_support") or {}
out["solve"] = {"t_s": round(t_solve, 3), "error": res.get("error"), "num_courses": res.get("num_courses"),
                "pieces": sum(len(v) for v in cc.values()), "codes": codes, "signature": signature(cc),
                "preflight_ok": pf.get("ok"), "preflight_errors": pf.get("errors"),
                "opening_violations": len(pf.get("opening_violations") or []),
                "collisions": len(pf.get("collisions") or []),
                "bond_reproved": sum(1 for a in (res.get("wall_bond_audits") or {}).values() if not a["ok"]),
                "non_modular": len(res.get("non_modular") or []),
                "channel_validation": (rein.get("validation") or {}).get("counts"),
                "channel_findings": [dict((k, v) for k, v in f.items()) for f in rein.get("findings") or []],
                "residual_absorptions": len(res.get("residual_absorptions") or []),
                "channel_physical_tolerances": res.get("channel_physical_tolerances"),
                "small_void": dict((k, v) for k, v in sva.items() if k != "violations"),
                "physical_support": sup.get("counts"),
                "physical_support_items": (sup.get("items") or [])[:40]}
step("SOLVED", pieces=out["solve"]["pieces"], preflight=pf.get("ok"), t_solve=round(t_solve, 2))

if cfg.get("create"):
    assert T.Equals(__revit__.ActiveUIDocument.Document) and not T.Equals(H)
    before = len(stamped_instances())
    t_create = clock.Elapsed.TotalSeconds
    h._execute_create(T)
    t_create = clock.Elapsed.TotalSeconds - t_create
    cr = h.create_result or {}
    after_all = stamped_instances()
    lots = {}
    for _el, parsed in after_all:
        lots[parsed[1]] = lots.get(parsed[1], 0) + 1
    step("CREATED", created=cr.get("created_count"), failures=len(cr.get("failures") or []), before=before,
         after=len(after_all), lots=lots, t_create=round(t_create, 2))
    cand_by_key = {}
    for ci, v in cc.items():
        for c in v:
            cand_by_key[(ci, id(c))] = c
    step_ft = wm._course_height_ft(h._creation_catalog(), res["candidates"])[0]
    mism = []
    checked = 0
    for item in cr.get("created_instances") or []:
        el = T.GetElement(item["id"])
        c = cand_by_key.get((item["course_index"], item["candidate_key"]))
        if el is None or c is None:
            mism.append({"id": str(item["id"]), "why": "missing"})
            continue
        lp = el.Location.Point
        z_expected = wm._course_z_abs(base_z, item["course_index"], step_ft)
        dxy = math.hypot(lp.X - c["origin_world"].X, lp.Y - c["origin_world"].Y) * FT
        dz = abs(lp.Z - z_expected) * FT
        tr = el.GetTransform()
        bx = tr.BasisX
        dot = bx.X * c["x_dir"].X + bx.Y * c["x_dir"].Y
        err = None
        if dxy > 0.05 or dz > 0.05:
            err = "pos dxy=%.3f dz=%.3f" % (dxy, dz)
        if el.Mirrored == bool(c.get("mirrored")) and dot < 0.999 and c["logical_code"] == "B34":
            err = (err or "") + " dir dot=%.4f" % dot
        if err:
            mism.append({"id": str(item["id"]), "code": c["logical_code"], "why": err})
        checked += 1
    out["readback"] = {"checked": checked, "mismatches": mism[:50], "mismatch_count": len(mism)}
    out["create"] = {"t_s": round(t_create, 3), "created": cr.get("created_count"),
                     "failures": (cr.get("failures") or [])[:20], "stamped_before": before,
                     "stamped_after": len(after_all), "lots": lots}
    step("READBACK", mismatches=len(mism), checked=checked)

if cfg.get("spy_wall") is not None:
    out["spy"] = SPY_CALLS
out["human_modified_after"] = H.IsModified
out["target_modified_after"] = T.IsModified
step("END", human_modified_after=H.IsModified)
print("ok")
