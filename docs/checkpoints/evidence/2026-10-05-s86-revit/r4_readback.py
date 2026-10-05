# -*- coding: utf-8 -*-
# LEITURA DE VOLTA (somente leitura): pecas de bloco CARIMBADAS no documento -> celulas pela
# transformacao REAL de cada instancia (GetTransform x cells_local do catalogo da familia) ->
# regua de coluna continua (prism_free_area.column_census) e B19 fora de fechamento.
# Independente do solver: parede e fiada vem da geometria (eixo mais proximo, Z).
# Saida: JSON no scratchpad com o tag S["rb_tag"]. Rodada 4: mede pelo eixo de entrada (86.9).
import sys, os, json, math
wm = sys.modules["core.wall_modeling"]
from core.engine import prism_free_area as PF
from core.engine import b34_run_arrangement as R
from core.engine import wall_stepper as ws
from Autodesk.Revit.DB import FilteredElementCollector, FamilyInstance, BuiltInParameter, XYZ
FT = 30.48
_alvo = [_d for _d in doc.Application.Documents if _d.Title == u"butanta testes"]
assert len(_alvo) == 1
doc = _alvo[0]
T = doc
S = wm._MCP_STATE; h = S["h"]
tag = S.get("rb_tag", "r4_final")
OUT = os.path.join(u"C:\\", u"Users", u"CIVIX", u"AppData", u"Local", u"Temp", u"claude",
                   u"C--Users-CIVIX-OneDrive--rea-de-Trabalho-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton--claude-worktrees-revit-solver-perf-diagnosis-6dfd89",
                   u"d7e1aa1d-7396-41fa-8dc2-732ff192410e", u"scratchpad", u"readback_%s.json" % tag)
try:
    h._ensure_opening_reinforcement_catalog(T)
except Exception as ex:
    print('channel catalog', ex)
cat = h._creation_catalog()
code_by_sym = {}
for code, e in cat.items():
    s = e.get("symbol") if isinstance(e, dict) else None
    if s is not None:
        code_by_sym[wm._eid_int(s.Id)] = code
axes = []
for wi in range(len(h.walls_to_create)):
    p0, _p1, d, L, th = ws._wall_axis_and_length(h.walls_to_create, wi)
    axes.append((p0, d, L * FT, th * FT))
step_cm = 20.0
base_cm = h.base_z_abs * FT
cc = {}
lots = {}
unassigned = 0
n = 0
for el in FilteredElementCollector(T).OfClass(FamilyInstance).WhereElementIsNotElementType():
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    st = wm._parse_block_lot_stamp(p.AsString() if p is not None else None)
    if st is None or el.Symbol is None:
        continue
    code = code_by_sym.get(wm._eid_int(el.Symbol.Id))
    if code is None:
        continue
    lots[str(st[1]) if isinstance(st, tuple) else str(st)] = lots.get(str(st[1]) if isinstance(st, tuple) else str(st), 0) + 1
    tr = el.GetTransform()
    o = el.Location.Point
    e = cat[code]
    xd = XYZ(tr.BasisX.X, tr.BasisX.Y, 0.0).Normalize()
    yd = XYZ(-xd.Y, xd.X, 0.0)
    cells = []
    for c in e.get("cells_local") or []:
        cx, cy = c["center_local"]
        wp = tr.OfPoint(XYZ(cx, cy, 0.0))
        cells.append({"point": XYZ(wp.X, wp.Y, o.Z), "size_local": c["size_local"]})
    # parede: eixo paralelo mais proximo que contem o centro
    best = None
    for wi, (p0, d, L, th) in enumerate(axes):
        if abs(xd.X * d.X + xd.Y * d.Y) < 0.9:
            continue
        v = o - p0
        t = (v.X * d.X + v.Y * d.Y) * FT
        lat = abs(v.X * d.Y - v.Y * d.X) * FT
        if lat <= th / 2.0 + 1.0 and -30.0 <= t <= L + 30.0 and (best is None or lat < best[0]):
            best = (lat, wi)
    if best is None:
        unassigned += 1
        continue
    course = int(round((o.Z * FT - base_cm - 1.0) / step_cm))
    cc.setdefault(course, []).append({"logical_code": code, "wall_idx": best[1], "origin_world": o, "x_dir": xd,
                                      "y_dir": yd, "length_cm": e["length_cm"], "width_cm": e["width_cm"],
                                      "cells_world": cells, "node_index": None, "element_id": wm._eid_int(el.Id)})
    n += 1
cols = PF.column_census(cc, h.walls_to_create)
hb = R.half_block_census(cc, h.walls_to_create, h.openings_per_wall, cat, limit=200)
prism = PF.prism_census(cc, h.walls_to_create, h.openings_per_wall, base_z_ft=h.base_z_abs)
codes = {}
for v in cc.values():
    for c in v:
        codes[c["logical_code"]] = codes.get(c["logical_code"], 0) + 1
# comparacao com o solver (quando ha' resultado na sessao): celula a celula por ElementId criado
cmp_ = None
res = h.solve_result or {}
cr = h.create_result or {}
if cr.get("created_instances"):
    by_key = {}
    for ci, v in (res.get("course_candidates") or {}).items():
        for cand in v:
            by_key[(ci, id(cand))] = cand
    rb_by_id = dict((c["element_id"], c) for v in cc.values() for c in v)
    worst, checked = 0.0, 0
    for item in cr["created_instances"]:
        cand = by_key.get((item["course_index"], item["candidate_key"]))
        rb = rb_by_id.get(wm._eid_int(item["id"]))
        if cand is None or rb is None:
            continue
        for a, b in zip(sorted((round(x["point"].X, 4), round(x["point"].Y, 4)) for x in cand.get("cells_world") or []),
                        sorted((round(x["point"].X, 4), round(x["point"].Y, 4)) for x in rb["cells_world"])):
            worst = max(worst, math.hypot(a[0] - b[0], a[1] - b[1]) * FT)
        checked += 1
    cmp_ = {"pieces_compared": checked, "max_cell_center_diff_cm": round(worst, 4)}
walls_out = dict((str(k), v) for k, v in cols["walls"].items())
jamb = []
for w in prism["walls"]:
    for jc in w["jamb_columns"]:
        jamb.append({"wall_idx": w["wall_idx"], "edge_cm": jc["edge_cm"], "side": jc["side"],
                     "common_width_cm": jc["common_width_cm"], "broken_at": jc["broken_at"], "narrow_at": jc["narrow_at"]})
# SECAO 86.9: ponta 0 aparada anda o p0 do eixo - a leitura mede pelo eixo de ENTRADA (mesma regua do humano)
try:
    _cuts = h._previous_stub_trim_cuts()
except Exception:
    _cuts = {}
OFF = dict((wi, ((_cuts.get(wi) or {}).get(0, 0.0)) * FT) for wi in range(len(h.walls_to_create)))
rows = {}
for ci, v in cc.items():
    for c in v:
        p0, d = axes[c["wall_idx"]][0], axes[c["wall_idx"]][1]
        a, b = ws._candidate_extent_on_wall_axis(c, p0, d)
        cells_t = [[round(x[0], 2), round(x[1], 2)] for x in PF.piece_cells(c, p0, d)]
        off = OFF.get(c["wall_idx"], 0.0)
        cells_t = [[round(x[0] + off, 2), round(x[1] + off, 2)] for x in cells_t]
        rows.setdefault("%d:%d" % (c["wall_idx"], ci), []).append([round(a + off, 2), round(b + off, 2), c["logical_code"],
                                                                   cells_t, c["element_id"]])
for k in rows:
    rows[k].sort()
out = {"tag": tag, "pieces": n, "unassigned": unassigned, "lots": lots, "codes": codes,
       "columns": dict((k, v) for k, v in cols.items() if k != "walls"), "columns_by_wall": walls_out,
       "half_blocks": dict((k, v) for k, v in hb.items() if k != "list"), "half_block_list": hb["list"],
       "prism": dict((k, prism[k]) for k in ("cells", "ok", "narrow", "interrupted", "jamb_columns", "jamb_ok",
                                             "jamb_narrow", "jamb_broken")),
       "jamb_columns": jamb, "solver_vs_revit": cmp_, "rows": rows,
       "openings": [[[round(o[0] * FT + OFF.get(wi, 0.0), 2), round(o[1] * FT + OFF.get(wi, 0.0), 2), round((o[2] - h.base_z_abs) * FT, 1),
                      round((o[3] - h.base_z_abs) * FT, 1)] for o in (h.openings_per_wall[wi] or [])]
                    for wi in range(len(h.walls_to_create))]}
with open(OUT, "w") as fh:
    fh.write(json.dumps(out, default=str, ensure_ascii=True))
print("readback", tag, "pieces", n, "unassigned", unassigned, "lots", lots)
print("columns", out["columns"])
print("half_blocks", out["half_blocks"])
print("prism", out["prism"])
print("solver_vs_revit", cmp_)
