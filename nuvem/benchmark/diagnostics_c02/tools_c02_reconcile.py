# -*- coding: utf-8 -*-
"""C02 / RECONCILIACAO DE DOMINIO - o no' X existe na geometria original?

Para cada no' que mudaria com X @0,05cm, reconstroi a geometria completa
ANTES e DEPOIS de `extend_wall_ends_to_junctions`, o no' que o solver cria,
o que o gabarito humano registra no MESMO ponto absoluto, e as pecas
humanas nas duas primeiras fiadas.

READ-ONLY. Nenhuma funcao de producao e' alterada.
"""
import json
import math
import os
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nuvem.benchmark import solver_bridge as SB  # noqa: E402

PROJECTS = {
    "TGD": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tgd"),
    "TP1": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tp1"),
}

# Os nos medidos em first_divergence.json (os 4 que mudam + o borderline).
TARGETS = {
    "TGD": [(1263.518, -507.951)],
    "TP1": [(6607.25, 594.93), (8942.24, 594.93),
            (6607.25, 1814.95), (8942.24, 1814.95)],
}


def cm(v, ft):
    return v / ft * 100.0


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def seg_distance_to_point(p0, p1, q):
    """Distancia do ponto `q` ao SEGMENTO p0-p1, e o parametro t (cm)."""
    vx, vy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(vx, vy)
    if length < 1e-9:
        return dist(p0, q), 0.0
    t = ((q[0] - p0[0]) * vx + (q[1] - p0[1]) * vy) / length
    t_clamped = max(0.0, min(length, t))
    proj = (p0[0] + vx / length * t_clamped, p0[1] + vy / length * t_clamped)
    return dist(proj, q), t


def describe_walls(walls, point, ft=None, tol=1.5):
    """Paredes (do input cru ou ja' posicionadas) que passam por `point`."""
    out = []
    for idx, w in enumerate(walls):
        p0, p1 = w["p0"], w["p1"]
        d, t = seg_distance_to_point(p0, p1, point)
        if d > tol:
            continue
        length = dist(p0, p1)
        at_end = min(abs(t), abs(t - length)) <= tol
        out.append({
            "idx": idx,
            "p0": [round(v, 3) for v in p0],
            "p1": [round(v, 3) for v in p1],
            "length_cm": round(length, 3),
            "thickness_cm": w.get("thickness_cm"),
            "dist_eixo_ao_ponto_cm": round(d, 4),
            "t_do_ponto_cm": round(t, 3),
            "relacao": ("TERMINA no ponto" if at_end else "ATRAVESSA o ponto"),
            "sobra_apos_o_ponto_cm": round(min(t, length - t), 3),
        })
    return out


def input_walls(project_dir):
    data = json.load(open(os.path.join(project_dir, "input.json"), encoding="utf-8"))
    walls = [{"p0": tuple(w["start_cm"]), "p1": tuple(w["end_cm"]),
              "thickness_cm": w["thickness_cm"],
              "openings": w.get("openings") or []} for w in data["walls"]]
    return data, walls


def positioned_walls(data):
    """Geometria DEPOIS de extend_wall_ends_to_junctions, + os nos do solver."""
    module = SB.engine()
    ft = module.FEET_PER_METER
    nodes, walls_to_create, end_to_node, openings = SB.plan_from_input(data)
    ws = sys.modules["core.engine.wall_stepper"]
    out = []
    for idx in range(len(walls_to_create)):
        p0, p1, _d, length_ft, thick_ft = ws._wall_axis_and_length(walls_to_create, idx)
        out.append({"p0": (cm(p0.X, ft), cm(p0.Y, ft)),
                    "p1": (cm(p1.X, ft), cm(p1.Y, ft)),
                    "thickness_cm": round(cm(thick_ft, ft), 3),
                    "openings": openings[idx] if idx < len(openings) else []})
    return out, nodes, end_to_node, openings, ft


def solver_node_at(nodes, point, ft, tol=1.5):
    module = SB.engine()
    found = []
    for i, node in enumerate(nodes):
        p = node.get("point")
        if p is None:
            continue
        q = (cm(p.X, ft), cm(p.Y, ft))
        if dist(q, point) <= tol:
            found.append({
                "node_index": i,
                "kind": node.get("kind"),
                "point_cm": [round(v, 3) for v in q],
                "crossing_walls": node.get("crossing_walls"),
                "arms": node.get("arms"),
                "main_wall_idx": node.get("main_wall_idx"),
                "incoming_wall_idx": node.get("incoming_wall_idx"),
            })
    return found


def reference_at(project_dir, point, tol=2.0):
    ref = json.load(open(os.path.join(project_dir, "reference.json"), encoding="utf-8"))
    walls, juncs = [], []
    for w in ref["walls"]:
        p0, p1 = tuple(w["start_cm"]), tuple(w["end_cm"])
        d, t = seg_distance_to_point(p0, p1, point)
        if d > tol:
            continue
        length = dist(p0, p1)
        rows = w.get("rows") or []
        walls.append({
            "id": w["id"], "p0": [round(v, 3) for v in p0], "p1": [round(v, 3) for v in p1],
            "length_cm": round(w["length_cm"], 3), "thickness_cm": w.get("thickness_cm"),
            "t_do_ponto_cm": round(t, 3),
            "relacao": ("TERMINA no ponto"
                        if min(abs(t), abs(t - length)) <= tol else "ATRAVESSA o ponto"),
            "junctions": [{"type": j.get("type"), "t_cm": round(j.get("t_cm") or 0.0, 3),
                           "point_cm": [round(v, 2) for v in (j.get("point_cm") or [0, 0])]}
                          for j in (w.get("junctions") or [])],
            "junction_no_ponto": [
                {"type": j.get("type"), "t_cm": round(j.get("t_cm") or 0.0, 3)}
                for j in (w.get("junctions") or [])
                if j.get("point_cm") and dist(tuple(j["point_cm"]), point) <= tol],
            "codigos": dict(collections.Counter(
                b["code"] for r in rows for b in (r.get("blocks") or []))),
            "fiada_0": [(b["code"], b["t_start_cm"], b["t_end_cm"])
                        for b in ((rows[0].get("blocks") if rows else []) or [])],
            "fiada_1": [(b["code"], b["t_start_cm"], b["t_end_cm"])
                        for b in ((rows[1].get("blocks") if len(rows) > 1 else []) or [])],
        })
        for j in (w.get("junctions") or []):
            if j.get("point_cm") and dist(tuple(j["point_cm"]), point) <= tol:
                juncs.append({"wall": w["id"], "type": j.get("type"),
                              "t_cm": round(j.get("t_cm") or 0.0, 3)})
    return walls, juncs


def solver_pieces_at(project, point, tol=40.0):
    """O que o SOLVER coloca perto do ponto, nas duas primeiras fiadas."""
    module = SB.engine()
    ft = module.FEET_PER_METER
    result = SB.run_solver(project)[0]
    out = collections.defaultdict(list)
    for course, cands in (result.get("course_candidates") or {}).items():
        if course > 1:
            continue
        for c in cands or []:
            o = c["origin_world"]
            q = (cm(o.X, ft), cm(o.Y, ft))
            if dist(q, point) <= tol:
                out[course].append({
                    "code": c["logical_code"], "length_cm": float(c["length_cm"]),
                    "center_cm": [round(v, 2) for v in q],
                    "reason": c.get("placement_reason"),
                    "dist_ao_no_cm": round(dist(q, point), 3),
                })
    return {str(k): sorted(v, key=lambda e: e["dist_ao_no_cm"]) for k, v in out.items()}


def main():
    report = {"nota": ("READ-ONLY. `input` = geometria crua do input.json; "
                       "`posicionada` = depois de extend_wall_ends_to_junctions."),
              "nos": []}
    for proj, targets in TARGETS.items():
        pdir = PROJECTS[proj]
        data, raw = input_walls(pdir)
        pos, nodes, end_to_node, openings, ft = positioned_walls(data)
        pos_as_walls = [{"p0": w["p0"], "p1": w["p1"],
                         "thickness_cm": w["thickness_cm"]} for w in pos]
        for point in targets:
            ref_walls, ref_juncs = reference_at(pdir, point)
            entry = {
                "project": proj,
                "no_cm": list(point),
                "input_paredes_no_ponto": describe_walls(raw, point),
                "posicionada_paredes_no_ponto": describe_walls(pos_as_walls, point),
                "no_do_solver": solver_node_at(nodes, point, ft),
                "gabarito_paredes_no_ponto": ref_walls,
                "gabarito_junctions_no_ponto": ref_juncs,
                "solver_pecas_perto": solver_pieces_at(data, point),
            }
            # aberturas proximas
            nearby = []
            for idx, w in enumerate(pos):
                d, t = seg_distance_to_point(w["p0"], w["p1"], point)
                if d > 1.5:
                    continue
                for (t_lo, t_hi, sill, head) in (w["openings"] or []):
                    lo, hi = cm(t_lo, ft), cm(t_hi, ft)
                    if lo - 60 <= t <= hi + 60:
                        nearby.append({"wall_idx": idx, "t_lo_cm": round(lo, 2),
                                       "t_hi_cm": round(hi, 2),
                                       "dist_do_no_cm": round(min(abs(t - lo), abs(t - hi)), 2)})
            entry["aberturas_a_60cm"] = nearby
            report["nos"].append(entry)
            print("ok", proj, point)

    out = os.path.join(HERE, "node_reconciliation.json")
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("gravado", out)


if __name__ == "__main__":
    main()
