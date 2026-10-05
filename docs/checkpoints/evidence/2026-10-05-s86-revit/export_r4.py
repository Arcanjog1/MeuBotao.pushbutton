# -*- coding: utf-8 -*-
"""Resolve a BUTANTA (estado do doc de trabalho + deslocamentos KEY:DX:DY) com o motor do worktree e
EXPORTA o resultado inteiro (pecas com XYZ serializado) para ser materializado no Revit pelo handler.
Rodada 4 (humano): aberturas ORIGINAIS (sem variante s66, porta 8078997 como no corpus), fiadas = $COURSES (14).
Uso: COURSES=13 py -3 export_r4.py REPO OUT.json"""
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import sys, json, time
REPO, OUT = sys.argv[1], sys.argv[2]
SHIFTS = [tuple(float(x) if i else int(x) for i, x in enumerate(s.split(":"))) for s in sys.argv[3:]]
sys.path.insert(0, os.path.join(REPO, "tools", "audit"))
import s74_corpus as S
m, ws = S.engine()
# FLAGS_OFF=modulo:NOME,... desliga chaves para medicao A/B (ex.: core.engine.b34_run_arrangement:JAMB_HUMAN_A_FORM_ENABLED)
for _f in [x for x in os.environ.get("FLAGS_OFF", "").split(",") if x.strip()]:
    _mod, _name = _f.split(":")
    _cands = [v for k, v in list(sys.modules.items()) if v is not None and (k == _mod or k.endswith('.' + _mod.split('.')[-1]) or k == _mod.split('.')[-1])]
    if not _cands:
        __import__(_mod)
        _cands = [sys.modules[_mod]]
    for _m in _cands:
        setattr(_m, _name, False)
    print("chave desligada:", _f)
FT = 30.48
geo = S.geometry()  # aberturas ORIGINAIS (o humano nao moveu nenhuma)
ops = []
for o in geo["openings"]:
    for key, dx, dy in SHIFTS:
        if o["key"] == key:
            o = dict(o, center_cm=[o["center_cm"][0] + dx, o["center_cm"][1] + dy],
                     insertion_cm=[o["insertion_cm"][0] + dx, o["insertion_cm"][1] + dy])
    ops.append(o)
geo = dict(geo, openings=ops)
t0 = time.time()
COURSES = int(os.environ.get("COURSES", "14"))
ctx, res = S.solve_on_fresh_context(geo, True, courses=COURSES, strategy=os.environ.get("STRATEGY") or None)
print("solve %.1fs" % (time.time() - t0))
seen = {}


def ser(o, depth=0):
    if depth > 12:
        return {"__str__": str(o)[:200]}
    if o is None or isinstance(o, (bool, int, float, str)):
        return o
    if hasattr(o, "X") and hasattr(o, "Y") and hasattr(o, "Z"):
        return {"__xyz__": [o.X, o.Y, o.Z]}
    if isinstance(o, dict):
        return dict((str(k), ser(v, depth + 1)) for k, v in o.items())
    if isinstance(o, (list, tuple, set)):
        return [ser(v, depth + 1) for v in o]
    return {"__str__": str(o)[:200]}


cc = {}
for ci, cands in res["course_candidates"].items():
    cc[str(ci)] = [ser(c) for c in cands]
walls = []
for wi, (line, th, locks) in enumerate(ctx["walls"]):
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    walls.append([[p0.X * FT, p0.Y * FT], [p1.X * FT, p1.Y * FT], th * FT])
opw = [[[o[0] * FT, o[1] * FT, o[2] * FT, o[3] * FT] for o in (row or [])] for row in ctx["openings_per_wall"]]
# 86.9: ponta aparada anda o p0 - a regua mede pelo eixo de ENTRADA (o humano tambem)
walls_orig = []
for line, th, _l in (ctx.get("original_axes") or ctx["walls"]):
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    walls_orig.append([[p0.X * FT, p0.Y * FT], [p1.X * FT, p1.Y * FT], th * FT])
opw_orig = [[[o[0] * FT, o[1] * FT, o[2] * FT, o[3] * FT] for o in (row or [])]
            for row in (ctx.get("openings_per_wall_original") or ctx["openings_per_wall"])]
keep = {}
for k, v in res.items():
    if k in ("course_candidates", "candidates", "bands"):
        continue
    try:
        keep[k] = ser(v)
    except Exception as ex:
        keep[k] = {"__str__": "erro %s" % ex}
out = {"shifts": SHIFTS, "walls_cm": walls, "openings_per_wall_cm": opw, "walls_cm_orig": walls_orig,
       "openings_per_wall_cm_orig": opw_orig, "course_candidates": cc, "result": keep,
       "num_courses": res.get("num_courses", COURSES)}
json.dump(out, open(OUT, "w"))
print("pieces", sum(len(v) for v in cc.values()), "walls", len(walls), "size_mb", round(os.path.getsize(OUT) / 1e6, 1))
