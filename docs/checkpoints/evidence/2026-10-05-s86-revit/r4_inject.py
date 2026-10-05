# -*- coding: utf-8 -*-
# Carrega no handler do botao o resultado calculado FORA do Revit pelo mesmo script (sol_final.json, secao 86) - so'
# depois de conferir que paredes e aberturas do Revit batem com as do calculo (<= 0,5 cm). Refaz o fim do
# _execute_solve (rastreio, preflight da regra 48, assinatura, plano de materializacao) e o gate.
import sys, os, json, math
wm = sys.modules["core.wall_modeling"]
from Autodesk.Revit.DB import XYZ
FT = 30.48
S = wm._MCP_STATE; h = S["h"]
SOL = os.path.join(u"C:\\", u"Users", u"CIVIX", u"AppData", u"Local", u"Temp", u"s85r4", u"sol_final.json")
data = json.loads(open(SOL).read())
# o MESMO preparo que a acao 'solve' do botao faz antes de calcular (a acao 'create' refaz os dois e
# compara a assinatura): geometria viva das paredes + catalogo de canaletas
h._refresh_geometry_from_document(doc)
h._ensure_opening_reinforcement_catalog(doc)
# ---- conferencia de geometria
bad = []
if len(data["walls_cm"]) != len(h.walls_to_create):
    bad.append("numero de paredes %d x %d" % (len(data["walls_cm"]), len(h.walls_to_create)))
else:
    for wi, (p0, p1, th) in enumerate(data["walls_cm"]):
        line = h.walls_to_create[wi][0]
        a, b = line.GetEndPoint(0), line.GetEndPoint(1)
        d = max(math.hypot(a.X * FT - p0[0], a.Y * FT - p0[1]), math.hypot(b.X * FT - p1[0], b.Y * FT - p1[1]))
        if d > 0.5:
            bad.append("parede %d eixo difere %.2f cm" % (wi, d))
    for wi, row in enumerate(data["openings_per_wall_cm"]):
        mine = h.openings_per_wall[wi] or []
        if len(mine) != len(row):
            bad.append("parede %d: %d x %d aberturas" % (wi, len(mine), len(row)))
            continue
        for o1, o2 in zip(row, mine):
            dd = max(abs(o1[0] - o2[0] * FT), abs(o1[1] - o2[1] * FT))
            if dd > 0.5:
                bad.append("parede %d: vao %.1f-%.1f x %.1f-%.1f" % (wi, o1[0], o1[1], o2[0] * FT, o2[1] * FT))
if bad:
    print("GEOMETRIA DIVERGE - nada carregado:", bad[:20])
    raise SystemExit
print("geometria confere: %d paredes, %d aberturas" % (len(h.walls_to_create), sum(len(r or []) for r in h.openings_per_wall)))


def de(o):
    if isinstance(o, dict):
        if "__xyz__" in o:
            x, y, z = o["__xyz__"]
            return XYZ(x, y, z)
        if "__str__" in o and len(o) == 1:
            return o["__str__"]
        return dict((k, de(v)) for k, v in o.items())
    if isinstance(o, list):
        return [de(v) for v in o]
    return o


cc = dict((int(k), [de(c) for c in v]) for k, v in data["course_candidates"].items())
res = de(data["result"])
res["course_candidates"] = cc
res["candidates"] = [c for ci in sorted(cc) for c in cc[ci]]
res["num_courses"] = data["num_courses"]
res["solved_outside_revit"] = {"source": "sol_final.json", "shifts": data["shifts"],
                               "motor": "worktree revit-solver-perf-diagnosis-6dfd89 (secao 86, rodada 4 - aproximacao do humano)"}
h.solve_result = res
try:
    wm._fill_opening_trace_ids(res, h.walls_to_create, getattr(h, "all_openings", None), h.created_walls_by_axis)
except Exception as ex:
    print("trace ids:", ex)
res["corpus_selection"] = (getattr(h, "setup", None) or {}).get("corpus_selection")
res["beta_preflight"] = wm.controlled_beta_preflight(res, h.walls_to_create, h.openings_per_wall, h.catalog, h.base_z_abs)
res["beta_input_signature"] = h._beta_input_signature()
plano = wm.materialization_plan(res, res["beta_preflight"])
try:
    wm._opening_trace_apply_materialization(res, plano)
except Exception as ex:
    print("opening trace:", ex)
if res.get("bond_trace") is not None:
    try:
        wm._bond_trace_apply_materialization(res["bond_trace"], plano["unresolved_bonds"])
    except Exception as ex:
        print("bond trace:", ex)
res["materialization"] = {"skipped": [rec for _ci, _k, rec in plano["skip"]],
                          "unresolved_bonds": plano["unresolved_bonds"], "fatal": plano["fatal"]}
pf = res["beta_preflight"]
codes = {}
for v in cc.values():
    for c in v:
        codes[c["logical_code"]] = codes.get(c["logical_code"], 0) + 1
print("pecas", sum(len(v) for v in cc.values()), sorted(codes.items()))
print("preflight ok", pf.get("ok"), "errors", len(pf.get("errors") or []), "opening_violations",
      len(pf.get("opening_violations") or []), "collisions", len(pf.get("collisions") or []))
print("materializacao: pular", len(plano["skip"]), "amarracoes nao resolvidas", len(plano["unresolved_bonds"]), "fatal", plano["fatal"])
allowed, reason = wm._ui_creation_gate(res, h.catalog_missing, ())
S["gate"] = (allowed, reason)
print("creation gate", allowed, reason)
