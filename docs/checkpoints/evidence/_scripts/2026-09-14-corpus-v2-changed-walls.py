# -*- coding: utf-8 -*-
"""Atribuicao fisica das paredes que MUDARAM entre main e HEAD (corpus V2).

Roda o solver no checkout indicado e grava, por parede (chave fisica): blocos
em coordenada de MUNDO (fiada, codigo, x0, y0, x1, y1 arredondados), trechos
nao modulares do solver e absorcoes da regra 30.8. Com dois dumps (main e
HEAD) o modo `compare` separa: (a) pares de eixos sobrepostos cujo conjunto
de blocos em mundo e' identico (so' a atribuicao de eixo mudou), (b) paredes
cujos blocos novos caem em trecho que era nao modular na main, (c) resto.
Uso:
  py -3 2026-09-14-corpus-v2-changed-walls.py dump <raiz> <project_id> <version|-> <saida.json>
  py -3 2026-09-14-corpus-v2-changed-walls.py compare <main.json> <head.json>
"""
import json
import os
import sys
from collections import Counter, defaultdict


def _key_geom(key):
    parts = key.split("|")
    x0, y0 = [float(v) for v in parts[1].split(",")]
    x1, y1 = [float(v) for v in parts[2].split(",")]
    return x0, y0, x1, y1


def _world(key, t0, t1):
    x0, y0, x1, y1 = _key_geom(key)
    L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    a = (round(x0 + ux * t0, 1), round(y0 + uy * t0, 1))
    b = (round(x0 + ux * t1, 1), round(y0 + uy * t1, 1))
    return tuple(sorted((a, b)))


def dump(root, project_id, version, out):
    sys.path.insert(0, os.path.join(root, "nuvem"))
    sys.path.insert(0, os.path.join(root, "tests"))
    from benchmark import runner, solver_bridge  # noqa
    from benchmark.extract import from_solver  # noqa
    paths = runner.project_paths(project_id, version)
    inp = runner._read_json(paths["input"]) or runner._read_json(runner.project_paths(project_id)["input"])
    res, walls, nodes, ops, catalog, base_z, nc, notes = solver_bridge.run_solver(inp)
    project = from_solver.project_from_solver(project_id, res, walls, nodes, ops, catalog, base_z, nc)
    by_idx = {}
    data = {}
    for w in project["walls"]:
        blocks = []
        for r in w["rows"]:
            for b in r["blocks"]:
                blocks.append([r["row"], b["code"]] + [list(p) for p in _world(w["key"], b["t_start_cm"], b["t_end_cm"])])
        data[w["key"]] = {"blocks": sorted(blocks), "non_modular": 0, "absorptions": 0}
        by_idx[w.get("source_index", w["id"])] = w["key"]
    # indice do solver -> chave: pela geometria do eixo criado
    F2CM = 30.48
    idx_key = {}
    for wi, wall in enumerate(walls):
        line = wall[0]
        p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
        pts = sorted([(p0.X * F2CM, p0.Y * F2CM), (p1.X * F2CM, p1.Y * F2CM)])
        best = None
        for key in data:
            x0, y0, x1, y1 = _key_geom(key)
            q = sorted([(x0, y0), (x1, y1)])
            dist = abs(q[0][0] - pts[0][0]) + abs(q[0][1] - pts[0][1]) + abs(q[1][0] - pts[1][0]) + abs(q[1][1] - pts[1][1])
            if best is None or dist < best[0]:
                best = (dist, key)
        if best and best[0] < 2.0:
            idx_key[wi] = best[1]
    for s in res.get("non_modular", []):
        k = idx_key.get(s.get("wall_idx"))
        if k:
            data[k]["non_modular"] += 1
    for a in res.get("residual_absorptions", []):
        k = idx_key.get(a.get("wall_idx"))
        if k:
            data[k]["absorptions"] += 1
    json.dump({"project": project_id, "walls": data}, open(out, "w", encoding="utf-8"), sort_keys=True)
    print("ok", project_id, len(data), "non_modular", len(res.get("non_modular", [])),
          "absorptions", len(res.get("residual_absorptions", [])))


def compare(main_path, head_path):
    a = json.load(open(main_path, encoding="utf-8"))["walls"]
    b = json.load(open(head_path, encoding="utf-8"))["walls"]
    changed = sorted(k for k in a if a[k]["blocks"] != b[k]["blocks"])
    groups = defaultdict(list)
    for k in changed:
        x0, y0, x1, y1 = _key_geom(k)
        axis = ("H", round(min(y0, y1) / 20.0)) if abs(y0 - y1) < 1e-6 else ("V", round(min(x0, x1) / 20.0))
        groups[axis].append(k)
    out = Counter()
    for k in changed:
        tag = None
        x0, y0, x1, y1 = _key_geom(k)
        # eixo paralelo sobreposto (menos de uma espessura) que tambem mudou
        partners = [o for o in changed if o != k and _overlaps(k, o)]
        if partners:
            ua = Counter(tuple(map(str, x)) for kk in [k] + partners for x in a[kk]["blocks"])
            ub = Counter(tuple(map(str, x)) for kk in [k] + partners for x in b[kk]["blocks"])
            if ua == ub:
                tag = "OVERLAPPING_AXES_SAME_WORLD_BLOCKS"
        if tag is None and a[k]["non_modular"] > 0:
            tag = "HAD_NON_MODULAR_ON_MAIN"
        if tag is None and b[k]["absorptions"] > 0:
            tag = "RULE_30_8_ABSORPTION"
        if tag is None:
            tag = "OTHER"
        out[tag] += 1
        print(tag, k, "blocks %d->%d nonmod %d->%d absorb %d" % (len(a[k]["blocks"]), len(b[k]["blocks"]),
                                                              a[k]["non_modular"], b[k]["non_modular"],
                                                              b[k]["absorptions"]))
    print("changed", len(changed), dict(out))


def _overlaps(k1, k2):
    a = _key_geom(k1)
    b = _key_geom(k2)
    if abs(a[1] - a[3]) < 1e-6 and abs(b[1] - b[3]) < 1e-6:
        return abs(a[1] - b[1]) < 14.0 and min(max(a[0], a[2]), max(b[0], b[2])) > max(min(a[0], a[2]), min(b[0], b[2]))
    if abs(a[0] - a[2]) < 1e-6 and abs(b[0] - b[2]) < 1e-6:
        return abs(a[0] - b[0]) < 14.0 and min(max(a[1], a[3]), max(b[1], b[3])) > max(min(a[1], a[3]), min(b[1], b[3]))
    return False


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(os.path.abspath(sys.argv[2]), sys.argv[3], None if sys.argv[4] == "-" else sys.argv[4], sys.argv[5])
    else:
        compare(sys.argv[2], sys.argv[3])
