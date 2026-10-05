# -*- coding: utf-8 -*-
# ETAPA 3 (rodada 4, com a 86.9): fluxo 'paredes existentes' (ordem de run_modulation_on_existing_walls) + regra 49.1 com o
# import '1 PAV' preparado + handler do botao (espelho de _show_post_creation_window). Sem UI.
import sys, json
wm = sys.modules["core.wall_modeling"]
from Autodesk.Revit.DB import FilteredElementCollector, ImportInstance, Options, Wall
FT = 30.48
T = doc
S = wm._MCP_STATE
assert T.Title == "butanta testes" and wm.doc.Equals(T)
ws_ = sorted([w for w in FilteredElementCollector(T).OfClass(Wall) if wm._eid_int(w.Id) in set(S["walls"])], key=lambda w: wm._eid_int(w.Id))
assert len(ws_) == 46
wtc, cwba, wids, lvl, h_ft, skipped = wm._build_existing_walls_selection(ws_)
out = {"selection": len(wtc), "skipped": len(skipped or []), "level": lvl.Name, "height_cm": round(h_ft * FT, 2)}
base_z = wm._level_internal_elevation_ft(lvl)
ops, note = wm.collect_opening_instances("auto", None)
detected = len(wtc)
keys = [wm._wall_axis_key(i) for i in wids]
imp = [i for i in FilteredElementCollector(T).OfClass(ImportInstance) if wm._eid_int(i.Id) == 7097743][0]
opt = Options(); opt.IncludeNonVisibleObjects = True
rl = {}
wm.extract_lines_by_layer(imp.get_Geometry(opt), rl)
ref = rl.get("ARQ-STR-BLOCO") or []
out["ref_lines"] = len(ref)
wtc, cwba, wids, corpus = wm.select_existing_axes_by_reference_layer(wtc, cwba, wids, ref, "ARQ-STR-BLOCO", keys)
out["corpus"] = [corpus["detected_axes"], corpus["selected_axes"], corpus["excluded_axes"], corpus.get("rule_id")]
out["excluded"] = [(it["wall_id"], it["geometry_summary"]["length_cm"], it["geometry_summary"]["coverage"]) for it in corpus["excluded"]]
run_setup = {"origem": "paredes existentes", "level": lvl.Name, "height_m": h_ft / wm.FEET_PER_METER, "walls": len(wtc),
             "detected_axes": detected, "openings_mode": "auto", "opening_reinforcement": "NONE",
             "reference_layer": "ARQ-STR-BLOCO", "corpus_selection": corpus,
             "thicknesses_cm": sorted(set(round(w[1] * FT, 1) for w in wtc))}
od = {"clamped_opening_count": 0, "opening_center_gap_max_ft": 0.0, "opening_off_center_count": 0, "assignments": [], "unassigned_openings": []}
opw = wm.assign_openings_to_walls(wtc, ops, od)
out["openings"] = [len(ops), sum(len(v) for v in opw), len(od["unassigned_openings"])]
inc = [r for r in wm.evaluate_opening_modulation(ops) if not r["compatible"]]
# SECAO 86.9: mesmo ponto do produto (run_modulation_on_existing_walls) - tocos aparados antes do grafo
wtc, opw, stub_trims = wm.trim_wall_end_stubs(wtc, opw)
if stub_trims:
    _trim_items = wm.stub_trim_corpus_items(stub_trims, [wm._wall_id_int(w) for w in wids],
                                            [wm._wall_axis_key(w) for w in wids])
    corpus["trimmed"] = list(corpus.get("trimmed") or []) + _trim_items
out["stub_trims"] = [(it["wall_idx"], it["end_index"], round(it["stub_ft"] * FT, 1)) for it in (stub_trims or [])]
wtc, jm = wm.extend_wall_ends_to_junctions(wtc, wm.JUNCTION_FACE_SEARCH_FT)
nodes, e2n = wm.build_wall_graph(wtc, jm)
out["nodes"] = len(nodes)
kinds = {}
for n in nodes:
    k = n.get("kind") if isinstance(n, dict) else getattr(n, "kind", None)
    kinds[str(k)] = kinds.get(str(k), 0) + 1
out["node_kinds"] = kinds
wsg = {}
for wi, ent in cwba.items():
    cl = wtc[wi][0]
    a = wm._axis_t_of_point(cl, cl.GetEndPoint(0)); b = wm._axis_t_of_point(cl, cl.GetEndPoint(1))
    wsg[wi] = [{"element_id": e, "seg_origin": o, "t_a": min(a, b), "t_b": max(a, b)} for e, o in ent]
mres = wm.evaluate_wall_modulation(wids, target_doc=T)
cat, miss = wm.load_fixed_block_catalog(T)
out["catalog"] = sorted(cat.keys()); out["catalog_missing"] = miss
h = wm._PostCreationEventHandler()
h.controlled_beta = False
h.walls_to_create = wtc; h.openings_per_wall = opw; h.created_walls_by_axis = cwba; h.created_cuts_by_axis = {}
h.wall_segment_geometry = wsg; h.all_openings = ops; h.wall_graph_nodes = nodes; h.wall_end_to_node = e2n
h.created_wall_ids_all = wids; h.selected_level = lvl; h.base_z_abs = base_z; h.wall_height_ft = h_ft
h.catalog = cat; h.catalog_missing = miss; h.opening_reinforcement_strategy = None
h.setup = dict(run_setup); h.error_rows = []; h.solve_result = None; h.create_result = None
h.modulation_results = mres; h.opening_incompatible_modulation = inc
def _done(kind, err):
    S["done"].append((kind, err))
h.on_done = _done
S["h"] = h
S["corpus"] = corpus
S["ref_lines"] = len(ref)
out["max_abs_xy_m"] = round(max(max(abs(w[0].GetEndPoint(k).X), abs(w[0].GetEndPoint(k).Y)) for w in wtc for k in (0, 1)) * FT / 100.0, 2)
print(json.dumps(out, default=repr, ensure_ascii=True).encode("ascii", "replace") if False else repr(out)[:3000])
