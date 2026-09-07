# -*- coding: utf-8 -*-
"""C02 / MODO A - auditoria do room check de L_CORNER (teto 34cm)."""
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
# raiz do repositorio: este diretorio vive em nuvem/benchmark/diagnostics_c02/
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from nuvem.benchmark import solver_bridge as SB

PROJECTS = {"TGD": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tgd/input.json"),
            "TP1": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tp1/input.json"),
            "PILOTO": os.path.join(ROOT, "nuvem/benchmark/projects/piloto_sintetico_2x2/input.json")}
REC = []
CTX = {"p": None}

def install(module):
    ws = sys.modules["core.engine.wall_stepper"]
    FT = module.FEET_PER_METER
    need_cm = ws.CORNER_B34_ROOM_FT / FT * 100.0
    orig = ws._corner_wall_room_ft
    def wrapper(walls_to_create, openings_per_wall, wall_idx, contact_point, dir_away,
                nodes=None, end_to_node=None, exclude_node_index=None):
        out = orig(walls_to_create, openings_per_wall, wall_idx, contact_point, dir_away,
                   nodes=nodes, end_to_node=end_to_node, exclude_node_index=exclude_node_index)
        if out is not None:
            room_cm = out / FT * 100.0
            line = walls_to_create[wall_idx][0]
            a, b = line.GetEndPoint(0), line.GetEndPoint(1)
            ka = (round(a.X / FT * 100.0, 3), round(a.Y / FT * 100.0, 3))
            kb = (round(b.X / FT * 100.0, 3), round(b.Y / FT * 100.0, 3))
            lo, hi = (ka, kb) if ka <= kb else (kb, ka)
            REC.append({"project": CTX["p"], "room_cm": round(room_cm, 6),
                        "deficit_cm": round(need_cm - room_cm, 6),
                        "wall_id": "%.3f,%.3f->%.3f,%.3f" % (lo[0], lo[1], hi[0], hi[1]),
                        "contact_cm": [round(contact_point.X / FT * 100.0, 3),
                                       round(contact_point.Y / FT * 100.0, 3)]})
        return out
    ws._corner_wall_room_ft = wrapper
    return need_cm

def main():
    module = SB.engine()
    need_cm = install(module)
    for name, path in PROJECTS.items():
        CTX["p"] = name
        SB.run_solver(json.load(open(path, encoding="utf-8")))
    out = {"required_cm": need_cm, "by_project": {}}
    for p in PROJECTS:
        rs = [r for r in REC if r["project"] == p]
        buck = collections.Counter()
        ident = collections.defaultdict(set)
        for r in rs:
            d = r["deficit_cm"]
            b = ("cabe" if d <= 0 else "ruido<=0.05" if d <= 0.05
                 else "borderline<=0.30" if d <= 0.30 else "insuficiente>0.30")
            buck[b] += 1
            ident[b].add((tuple(r["contact_cm"]), r["wall_id"]))
        out["by_project"][p] = {
            "evaluations": len(rs),
            "buckets": dict(buck),
            "unique_identities": {k: len(v) for k, v in ident.items()},
            "borderline_examples": sorted(
                {(r["room_cm"], r["wall_id"], tuple(r["contact_cm"]))
                 for r in rs if 0 < r["deficit_cm"] <= 0.30})[:10],
        }
    print(json.dumps(out, indent=1, ensure_ascii=False))
    json.dump(out, open(os.path.join(HERE, "c02_lcorner_audit.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

main()
