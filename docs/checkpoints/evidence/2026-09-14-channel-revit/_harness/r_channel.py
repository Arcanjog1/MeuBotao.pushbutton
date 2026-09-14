# Harness CHANNEL no Revit real (IronPython, via MCP). Config em r_cfg.json.
# SEGURANCA: so' escreve no TARGET "butanta testes"; o HUMANO nunca recebe
# Transaction (verificado antes/depois por IsModified).
import sys
import json
import hashlib
from Autodesk.Revit.DB import XYZ, Line, FilteredElementCollector, FamilyInstance, BuiltInParameter, Level, Transaction
from System.Collections.Generic import List
from Autodesk.Revit.DB import ElementId, Options, ViewDetailLevel, GeometryInstance, Solid
import math
if not hasattr(math, "isfinite"):
    math.isfinite = lambda v: not (math.isinf(v) or math.isnan(v))

NL = chr(10)
CLONE = "C:/Users/twitc/Documents/butanta-channel/MeuBotao.pushbutton"
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
humans = [d for d in app.Documents if d.Title.startswith("BUTANT") and "R08_LT" in d.Title]
assert T.Title == "butanta testes", T.Title
assert T.PathName.lower().endswith("butanta testes.rvt"), T.PathName
assert len(humans) == 1 and not humans[0].Equals(T)
H = humans[0]
out["human_modified_before"] = H.IsModified
assert H.IsModified is False
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
step("MODULE_LOADED")
PERF = {}
def _perf_wrap(owner, name, label):
    fn = getattr(owner, name)
    def inner(*a, **k):
        t0 = clock.Elapsed.TotalSeconds
        try:
            return fn(*a, **k)
        finally:
            rec = PERF.setdefault(label, [0, 0.0]); rec[0] += 1; rec[1] += clock.Elapsed.TotalSeconds - t0
    setattr(owner, name, inner)
for _name in (() if not cfg.get("perf_wrappers", True) else ("_solve_building_blocks_all_courses_core", "_channel_tie_parity_trials", "_channel_plan_metrics",
              "_channel_trial_joint_quality", "_apply_opening_reinforcement", "_unify_candidates_with_courses",
              "audit_all_walls_bond_quality", "repair_arm_role_isolated_edges", "repair_b19_residual_fill",
              "controlled_beta_preflight")):
    if hasattr(wm, _name):
        _perf_wrap(wm, _name, _name)
for _name in (() if not cfg.get("perf_wrappers", True) else ("plan_channel_reinforcement", "validate_channel_reinforcement", "_wall_strip_pieces")):
    _perf_wrap(orf, _name, "orf." + _name)

BENCH_PREFIX = "CHANNELBENCH-"


def bench_instances():
    found = []
    for el in FilteredElementCollector(T).OfClass(FamilyInstance).WhereElementIsNotElementType():
        p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        parsed = wm._parse_block_lot_stamp(p.AsString() if p is not None else None)
        if parsed is not None and (parsed[0] or "").startswith(BENCH_PREFIX):
            found.append(el)
    return found


if cfg.get("purge_bench"):
    olds = bench_instances()
    if olds:
        ids = List[ElementId]()
        for el in olds:
            ids.Add(el.Id)
        t = Transaction(T, "CHANNEL bench - remove lote carimbado da bancada")
        t.Start()
        T.Delete(ids)
        t.Commit()
    step("PURGE", removed=len(olds), remaining=len(bench_instances()))
    if cfg.get("purge_only"):
        out["human_modified_after"] = H.IsModified
        step("END")
        raise RuntimeError("PURGE_ONLY_DONE")

walls_json = json.loads(System.IO.File.ReadAllText(CLONE + "/docs/checkpoints/evidence/2026-09-10-butanta-test-walls.json"))["walls"]
by_id = dict((w["id"], w) for w in walls_json)
sel = [by_id[i] for i in cfg["ids"]]
axes = []
keys = []
for w in sel:
    p0 = XYZ(float(w["p0"][0]), float(w["p0"][1]), float(w["p0"][2]))
    p1 = XYZ(float(w["p1"][0]), float(w["p1"][1]), float(w["p1"][2]))
    axes.append((Line.CreateBound(p0, p1), wm._cm_to_ft(14.0), (False, False)))
    a = sorted([(round(p0.X * 30.48, 1), round(p0.Y * 30.48, 1)), (round(p1.X * 30.48, 1), round(p1.Y * 30.48, 1))])
    keys.append("%s_%s_%s_%s" % (a[0][0], a[0][1], a[1][0], a[1][1]))
walls, jmap = wm.extend_wall_ends_to_junctions(list(axes), wm.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = wm.build_wall_graph(walls, jmap)
ops = wm.get_opening_instances()
opw = wm.assign_openings_to_walls(walls, ops)
level = [l for l in FilteredElementCollector(T).OfClass(Level) if abs(l.ProjectElevation * 30.48 - float(cfg["level_pe_cm"])) < 0.5][0]
base_z = wm._level_internal_elevation_ft(level)
out["walls"] = len(walls)
out["openings_detected"] = len(ops)
out["openings_assigned"] = sum(len(v) for v in opw)
out["openings_per_wall_ft"] = [[list(o) for o in v] for v in opw]
out["walls_ft"] = [[w[0].GetEndPoint(0).X, w[0].GetEndPoint(0).Y, w[0].GetEndPoint(1).X, w[0].GetEndPoint(1).Y] for w in walls]
step("INPUT", walls=len(walls), openings=len(ops), assigned=out["openings_assigned"], base_z_cm=base_z * 30.48)

cat, miss = wm.load_fixed_block_catalog(T)
ccat, cmiss = wm.load_channel_family_catalog(T)
out["catalog_missing"] = miss
out["channel_catalog_missing"] = cmiss
out["channel_catalog"] = dict((k, {"length_cm": v["length_cm"], "height_cm": v["height_cm"], "width_cm": v["width_cm"],
                                   "length_parameter": v["length_parameter"], "family": v["symbol"].FamilyName})
                              for k, v in ccat.items())
out["fill_catalog"] = dict((k, {"length_cm": v["length_cm"], "height_cm": v["height_cm"], "width_cm": v["width_cm"],
                                "is_special_bond": v["is_special_bond"], "is_compensator": v["is_compensator"],
                                "cells_local": [{"center_local": list(c["center_local"]), "size_local": list(c["size_local"])}
                                                for c in v["cells_local"]]})
                           for k, v in cat.items())
step("CATALOGS", fill=sorted(cat.keys()), channel=sorted(ccat.keys()), missing=len(miss), channel_missing=len(cmiss))

h = wm._PostCreationEventHandler()
h.controlled_beta = True
h.walls_to_create = walls
h.openings_per_wall = opw
h.wall_graph_nodes = nodes
h.wall_end_to_node = e2n
h.selected_level = level
h.base_z_abs = base_z
h.wall_height_ft = wm._cm_to_ft(float(cfg.get("wall_height_cm", 280.0)))
h.catalog = cat
h.channel_catalog = ccat
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
            rows.append("%d:%s|%s|%.4f|%.4f|%.3f|%s" % (ci, c["logical_code"], c.get("wall_idx"), o.X, o.Y,
                                                        c["length_cm"], c.get("placement_reason")))
    return hashlib.sha256(NL.join(sorted(rows))).hexdigest()


cc = res.get("course_candidates") or {}
codes = {}
for v in cc.values():
    for c in v:
        codes[c["logical_code"]] = codes.get(c["logical_code"], 0) + 1
rein = res.get("opening_reinforcement") or {}
pf = res.get("beta_preflight") or {}
out["solve"] = {"t_s": round(t_solve, 3), "error": res.get("error"), "pieces": sum(len(v) for v in cc.values()),
                "codes": codes, "signature": signature(cc),
                "preflight_ok": pf.get("ok"), "preflight_errors": pf.get("errors"),
                "opening_violations": len(pf.get("opening_violations") or []),
                "collisions": len(pf.get("collisions") or []),
                "bond_reproved": sum(1 for a in (res.get("wall_bond_audits") or {}).values() if not a["ok"]),
                "non_modular": len(res.get("non_modular") or []),
                "channel_validation": (rein.get("validation") or {}).get("counts"),
                "channel_findings": [dict((k, v) for k, v in f.items()) for f in rein.get("findings") or []],
                "openings": rein.get("openings"), "node_crossings": rein.get("node_crossings"),
                "tie_conversions": rein.get("tie_conversions"), "free_to_top": rein.get("free_to_top"),
                "channel_timing_s": rein.get("timing_s"),
                "residual_absorptions": len(res.get("residual_absorptions") or []),
                "parity_trials": res.get("channel_tie_parity_trials"),
                "continuous_passages": (rein.get("continuous_passages") or []),
                "perf_functions": dict((k, [v[0], round(v[1], 3)]) for k, v in PERF.items())}
step("SOLVED", pieces=out["solve"]["pieces"], preflight=pf.get("ok"), t_solve=round(t_solve, 2))

if cfg.get("create"):
    owner = dict((i, BENCH_PREFIX + keys[i]) for i in range(len(walls)))
    h._owner_wall_uids = lambda app_doc: owner
    before = len(bench_instances())
    t_create = clock.Elapsed.TotalSeconds
    h._execute_create(T)
    t_create = clock.Elapsed.TotalSeconds - t_create
    cr = h.create_result or {}
    after_all = bench_instances()
    step("CREATED", created=cr.get("created_count"), failures=len(cr.get("failures") or []), before=before,
         after=len(after_all), t_create=round(t_create, 2))
    # releitura fisica: familia/tipo, posicao, rotacao, comprimento de instancia
    cand_by_key = {}
    for ci, v in cc.items():
        for c in v:
            cand_by_key[(ci, id(c))] = c
    step_ft = wm._course_height_ft(h._creation_catalog(), res["candidates"])[0]
    mism = []
    fam_by_code = {}
    checked = 0
    for item in cr.get("created_instances") or []:
        el = T.GetElement(item["id"])
        c = cand_by_key.get((item["course_index"], item["candidate_key"]))
        if el is None or c is None:
            mism.append({"id": str(item["id"]), "why": "missing"})
            continue
        fam = el.Symbol.FamilyName
        fam_by_code.setdefault(c["logical_code"], set()).add(fam)
        lp = el.Location.Point
        z_expected = wm._course_z_abs(base_z, item["course_index"], step_ft)
        dxy = math.hypot(lp.X - c["origin_world"].X, lp.Y - c["origin_world"].Y) * 30.48
        dz = abs(lp.Z - z_expected) * 30.48
        err = None
        if dxy > 0.05 or dz > 0.05:
            err = "pos dxy=%.3f dz=%.3f" % (dxy, dz)
        if c["logical_code"] == orf.CHANNEL_U_CUT:
            p = el.LookupParameter("Comprimento_bloco")
            got = p.AsDouble() * 30.48 if p is not None else None
            if got is None or abs(got - c["instance_length_cm"]) > 0.05:
                err = "len %s != %s" % (got, c["instance_length_cm"])
            # comprimento do SOLIDO ao longo do eixo da peca (a bbox da
            # familia VAR infla de forma assimetrica em pecas curtas)
            xd = c["x_dir"]
            opt = Options()
            opt.DetailLevel = ViewDetailLevel.Fine
            proj = []
            for g in el.get_Geometry(opt):
                items = g.GetInstanceGeometry() if isinstance(g, GeometryInstance) else [g]
                for sol in items:
                    if isinstance(sol, Solid) and sol.Volume > 1e-9:
                        for e in sol.Edges:
                            for q in e.Tessellate():
                                proj.append(q.X * xd.X + q.Y * xd.Y)
            item_len = (max(proj) - min(proj)) * 30.48 if proj else -1.0
            if abs(item_len - c["instance_length_cm"]) > 0.05:
                err = (err or "") + " solid_len %.3f" % item_len
        if err:
            mism.append({"id": str(item["id"]), "code": c["logical_code"], "why": err})
        checked += 1
    out["readback"] = {"checked": checked, "mismatches": mism[:50], "mismatch_count": len(mism),
                       "families_by_code": dict((k, sorted(v)) for k, v in fam_by_code.items())}
    out["create"] = {"t_s": round(t_create, 3), "created": cr.get("created_count"), "failures": (cr.get("failures") or [])[:20],
                     "perf": cr.get("perf"), "bench_before": before, "bench_after": len(after_all),
                     "retained_walls": len(cr.get("retained_walls") or [])}
    step("READBACK", mismatches=len(mism), checked=checked)

out["human_modified_after"] = H.IsModified
out["target_modified_after"] = T.IsModified
step("END")
print("ok")
