# -*- coding: utf-8 -*-
"""C02 / MODO A - instrumentacao READ-ONLY do room check de amarracao.

Nao altera producao: patcha em memoria (wrappers que CHAMAM o original e
so' registram) as funcoes reais de `core.engine.wall_stepper`:

  X : solve_x_intersection            (gate B54, 27+1 = 28cm)
      _x_intersection_centered_candidate  (degradacao B34/C09/C04)
  T : _t_intersection_room_ok         (gate B54 main, 27cm SEM junta)
  L : solve_l_corner                  (gate B34, 34cm)

Identidade FISICA estavel (nunca wall_idx / block_id):
  no'    -> (round(point.X_cm,3), round(point.Y_cm,3))
  parede -> par ordenado canonico dos dois endpoints em cm
"""
import json
import os
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
# raiz do repositorio: este diretorio vive em nuvem/benchmark/diagnostics_c02/
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from nuvem.benchmark import solver_bridge as SB  # noqa: E402

PROJECTS = {
    "TGD": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tgd/input.json"),
    "TP1": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tp1/input.json"),
    "PILOTO": os.path.join(ROOT, "nuvem/benchmark/projects/piloto_sintetico_2x2/input.json"),
}

EVENTS = []
_CTX = {"project": None}


def _cm(ft, module):
    return ft / module.FEET_PER_METER * 100.0


def _pt_id(point):
    return (round(point.X, 9), round(point.Y, 9))


def _pt_cm(point, module):
    return [round(_cm(point.X, module), 4), round(_cm(point.Y, module), 4)]


def _wall_id(walls_to_create, wall_idx, module):
    """Identidade GEOMETRICA da parede (cm, extremidades ordenadas) - nao
    depende da ordem de entrada nem do indice da lista."""
    if wall_idx is None or wall_idx >= len(walls_to_create):
        return None
    line = walls_to_create[wall_idx][0]
    a = line.GetEndPoint(0)
    b = line.GetEndPoint(1)
    ka = (round(_cm(a.X, module), 3), round(_cm(a.Y, module), 3))
    kb = (round(_cm(b.X, module), 3), round(_cm(b.Y, module), 3))
    lo, hi = (ka, kb) if ka <= kb else (kb, ka)
    return "%.3f,%.3f->%.3f,%.3f" % (lo[0], lo[1], hi[0], hi[1])


def install(module):
    ws = sys.modules["core.engine.wall_stepper"]
    FT = module.FEET_PER_METER

    def to_cm(v):
        return v / FT * 100.0

    joint_cm = ws.BLOCK_JOINT_CM
    x_need_cm = to_cm(ws.X_INTERSECTION_B54_HALF_ROOM_FT) + joint_cm
    t_need_cm = to_cm(ws.T_INTERSECTION_B54_HALF_ROOM_FT)
    l_need_cm = to_cm(ws.CORNER_B34_ROOM_FT)

    orig_x = ws.solve_x_intersection
    orig_cand = ws._x_intersection_centered_candidate
    orig_t_ok = ws._t_intersection_room_ok
    orig_t_assess = ws._t_intersection_room_assessment
    orig_l = ws.solve_l_corner
    orig_corner_room = ws._corner_wall_room_ft

    def solve_x(node, walls_to_create, catalog, node_index=None,
                openings_per_wall=None, nodes=None, end_to_node=None):
        rec = None
        if openings_per_wall is not None:
            pair = node.get("crossing_walls")
            if pair and pair[0] is not None and pair[1] is not None:
                point = node["point"]
                rec = {"kind": "X_GATE", "project": _CTX["project"],
                       "node_cm": _pt_cm(point, module), "walls": []}
                for label, widx in (("A", pair[0]), ("B", pair[1])):
                    rp, rm = ws._x_intersection_wall_room_ft(
                        walls_to_create, openings_per_wall, widx, point,
                        nodes, end_to_node, node_index)
                    room_cm = min(to_cm(rp), to_cm(rm))
                    rec["walls"].append({
                        "course": label,
                        "wall_id": _wall_id(walls_to_create, widx, module),
                        "room_plus_cm": round(to_cm(rp), 6),
                        "room_minus_cm": round(to_cm(rm), 6),
                        "room_cm": round(room_cm, 6),
                        "required_cm": round(x_need_cm, 6),
                        "deficit_cm": round(x_need_cm - room_cm, 6),
                        "b54_accepted": bool(min(rp, rm) + 1e-6 >= ws.X_INTERSECTION_B54_HALF_ROOM_FT
                                             + ws._cm_to_ft(joint_cm)),
                    })
        result = orig_x(node, walls_to_create, catalog, node_index=node_index,
                        openings_per_wall=openings_per_wall, nodes=nodes,
                        end_to_node=end_to_node)
        if rec is not None:
            rec["ok"] = bool(result.get("ok"))
            rec["reason"] = result.get("reason")
            for key, label in (("course_a", "A"), ("course_b", "B")):
                cand = result.get(key)
                for entry in rec["walls"]:
                    if entry["course"] == label:
                        entry["selected_code"] = cand.get("logical_code") if cand else None
                        entry["placement_reason"] = cand.get("placement_reason") if cand else None
            EVENTS.append(rec)
        return result

    def cand(catalog, point, x_dir, room_ft, course, wall_idx,
             secondary_wall_idx, node_index, placement_reason):
        room_cm = to_cm(room_ft)
        tried = []
        for code in ws.X_INTERSECTION_DEGRADED_CODES:
            entry = catalog.get(code)
            if entry is None or not entry.get("length_cm"):
                continue
            half_cm = entry["length_cm"] / 2.0
            need_cm = half_cm + joint_cm
            tried.append({"code": code, "half_len_cm": half_cm,
                          "required_cm": round(need_cm, 6),
                          "deficit_cm": round(need_cm - room_cm, 6),
                          "fits": bool(ws._cm_to_ft(half_cm) + ws._cm_to_ft(joint_cm)
                                       <= room_ft + 1e-6)})
        out = orig_cand(catalog, point, x_dir, room_ft, course, wall_idx,
                        secondary_wall_idx, node_index, placement_reason)
        EVENTS.append({"kind": "X_DEGRADED", "project": _CTX["project"],
                       "node_cm": _pt_cm(point, module), "course": course,
                       "room_cm": round(room_cm, 6), "tried": tried,
                       "selected_code": out.get("logical_code") if out else None})
        return out

    def t_ok(node, walls_to_create, openings_per_wall, nodes=None,
             end_to_node=None, node_index=None):
        out = orig_t_ok(node, walls_to_create, openings_per_wall, nodes=nodes,
                        end_to_node=end_to_node, node_index=node_index)
        if openings_per_wall is not None:
            a = orig_t_assess(node, walls_to_create, openings_per_wall, nodes=nodes,
                              end_to_node=end_to_node, node_index=node_index)
            if a is not None:
                room_cm = min(to_cm(a["room_plus_ft"]), to_cm(a["room_minus_ft"]))
                inc_cm = to_cm(a["room_incoming_ft"])
                EVENTS.append({
                    "kind": "T_GATE", "project": _CTX["project"],
                    "node_cm": _pt_cm(a["point"], module),
                    "main_wall_id": _wall_id(walls_to_create, a["main_idx"], module),
                    "inc_wall_id": _wall_id(walls_to_create, a["inc_idx"], module),
                    "room_plus_cm": round(to_cm(a["room_plus_ft"]), 6),
                    "room_minus_cm": round(to_cm(a["room_minus_ft"]), 6),
                    "room_cm": round(room_cm, 6),
                    "required_cm": round(t_need_cm, 6),
                    "deficit_cm": round(t_need_cm - room_cm, 6),
                    "room_incoming_cm": round(inc_cm, 6),
                    "required_incoming_cm": round(l_need_cm, 6),
                    "deficit_incoming_cm": round(l_need_cm - inc_cm, 6),
                    "accepted": bool(out),
                })
        return out

    def solve_l(node, walls_to_create, catalog, node_index=None,
                openings_per_wall=None, nodes=None, end_to_node=None):
        rec = None
        if openings_per_wall is not None:
            arms = node.get("arms")
            if arms and len(arms) >= 2:
                rec = {"kind": "L_GATE", "project": _CTX["project"],
                       "node_cm": _pt_cm(node["point"], module), "walls": []}
                for label, widx in (("A", arms[0]), ("B", arms[1])):
                    try:
                        contact = ws._node_contact_point_for_wall(node, widx)
                        _e, d_away, _l, _t = ws._wall_end_and_dir_near_point(
                            walls_to_create, widx, contact)
                        room = orig_corner_room(walls_to_create, openings_per_wall, widx,
                                                contact, d_away, nodes, end_to_node, node_index)
                    except Exception:
                        room = None
                    if room is None:
                        continue
                    room_cm = to_cm(room)
                    rec["walls"].append({
                        "course": label,
                        "wall_id": _wall_id(walls_to_create, widx, module),
                        "room_cm": round(room_cm, 6),
                        "required_cm": round(l_need_cm, 6),
                        "deficit_cm": round(l_need_cm - room_cm, 6),
                        "b34_accepted": bool(room + 1e-6 >= ws.CORNER_B34_ROOM_FT),
                    })
        result = orig_l(node, walls_to_create, catalog, node_index=node_index,
                        openings_per_wall=openings_per_wall, nodes=nodes,
                        end_to_node=end_to_node)
        if rec is not None and rec["walls"]:
            rec["ok"] = bool(result.get("ok"))
            for key, label in (("course_a", "A"), ("course_b", "B")):
                c = result.get(key)
                for entry in rec["walls"]:
                    if entry["course"] == label:
                        entry["selected_code"] = c.get("logical_code") if c else None
            EVENTS.append(rec)
        return result

    ws.solve_x_intersection = solve_x
    ws._x_intersection_centered_candidate = cand
    ws._t_intersection_room_ok = t_ok
    ws.solve_l_corner = solve_l
    # `wall_modeling` faz `from core.engine.wall_stepper import *`: os nomes
    # publicos foram COPIADOS para la' e precisam apontar para o wrapper.
    for name in ("solve_x_intersection", "solve_l_corner"):
        if hasattr(module, name):
            setattr(module, name, getattr(ws, name))
    return {"x_required_cm": x_need_cm, "t_required_cm": t_need_cm,
            "l_required_cm": l_need_cm, "joint_cm": joint_cm}


def main():
    module = SB.engine()
    contract = install(module)
    print("contrato medido:", contract)
    for name, path in PROJECTS.items():
        _CTX["project"] = name
        with open(path, "r", encoding="utf-8") as handle:
            project = json.load(handle)
        before = len(EVENTS)
        SB.run_solver(project)
        print("%-7s eventos=%d" % (name, len(EVENTS) - before))
    out = os.path.join(HERE, "c02_events.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump({"contract": contract, "events": EVENTS}, handle)
    print("gravado:", out, len(EVENTS), "eventos")


if __name__ == "__main__":
    main()
