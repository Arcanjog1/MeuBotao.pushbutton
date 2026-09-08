"""Mede PRISM_CONTINUOUS_JOINT no projeto OFICIAL e separa o que e'
CROSS-BAND (fronteira de banda de abertura) do que e' intra-banda.
Uso: medir_crossband.py <root> <projeto> [saida.json]
"""
import json, sys, os, collections
root = sys.argv[1]; proj = sys.argv[2]
saida = sys.argv[3] if len(sys.argv) > 3 else None
sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver

if os.environ.get("G12_OFF") == "1":
    solver_bridge.engine().CROSS_BAND_JOINT_PROPAGATION_ENABLED = False
    print("CROSS_BAND_JOINT_PROPAGATION_ENABLED = False (pre-fix)")
inp = json.load(open(os.path.join(root, "nuvem/benchmark/projects", proj, "input.json")))
res, walls, nodes, ops, cat, bz, nc, notes = solver_bridge.run_solver(inp)
out = from_solver.project_from_solver(proj, res, walls, nodes, ops, cat, bz, nc)
findings, errors = validators.run_all(out, {})

# banda de cada course_index, direto do motor
mod = solver_bridge.engine()
ch, _err = mod._course_height_ft(cat, None)
bh = ch - mod._cm_to_ft(mod.COURSE_JOINT_CM)
groups = mod._group_course_indices_by_opening_band(ops, bz, ch, bh, nc)
band_of = {}
for bi, (idxs, _f) in enumerate(groups):
    for ci in idxs:
        band_of[ci] = bi
print("bandas:", [(bi, g[0]) for bi, g in enumerate(groups)])

rows_by_wall = {w["id"]: {r["row"]: r for r in w["rows"]} for w in out["walls"]}
wall_by_id = {w["id"]: w for w in out["walls"]}

# row -> course_index: as rows saem na ordem das fiadas fisicas
cont = [f for f in findings if f["code"] == "PRISM_CONTINUOUS_JOINT"]
print("PRISM_CONTINUOUS_JOINT total:", len(cont))

def course_index_of(w, row_id):
    rs = sorted(w["rows"], key=lambda r: r["elevation_cm"])
    for i, r in enumerate(rs):
        if r["row"] == row_id:
            return i
    return None

cross, intra = [], []
det = []
for f in cont:
    w = wall_by_id[f["wall"]]
    ia = course_index_of(w, f["row_a"]); ib = course_index_of(w, f["row_b"])
    ba, bb = band_of.get(ia), band_of.get(ib)
    dv, _ = model.direction_of(w["start_cm"], w["end_cm"])
    t = f["joint_t_cm"]
    pt = (round(w["start_cm"][0] + dv[0] * t, 1), round(w["start_cm"][1] + dv[1] * t, 1))
    za = rows_by_wall[w["id"]][f["row_a"]]["elevation_cm"]
    zb = rows_by_wall[w["id"]][f["row_b"]]["elevation_cm"]
    rec = {"wall": w["id"], "len": w["length_cm"], "pt": pt, "z": (round(za,1), round(zb,1)),
           "ci": (ia, ib), "band": (ba, bb), "t": t, "stagger": f["stagger_cm"],
           "th": w["thickness_cm"]}
    det.append(rec)
    (cross if ba != bb else intra).append(rec)
print("  cross-band:", len(cross), " intra-banda:", len(intra))
c = collections.Counter((r["band"], r["ci"]) for r in cross)
for k, v in sorted(c.items())[:20]:
    print("   ", k, v)
if saida:
    json.dump({"total": len(cont), "cross": cross, "intra": intra,
               "bands": [g[0] for g in groups],
               "findings_por_codigo": dict(collections.Counter(x["code"] for x in findings))},
              open(saida, "w"), indent=1)
    print("salvo em", saida)
