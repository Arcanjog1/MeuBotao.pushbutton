# -*- coding: utf-8 -*-
"""CROSS AUDIT — decompõe as juntas coincidentes suspeitas (a mesma
detecção de `run_course_bond_census.py`, tolerância e definição
IDÊNTICAS) por tipo de nó (`L_CORNER`/`T_INTERSECTION`/`X_INTERSECTION`/
`nenhum`), para servir de proxy independente do `UNCLASSIFIED_RULE_
CONFLICT` que a CONTA 1 reportou (1518 → 1506) — uma categoria da
ferramenta PRÓPRIA dela (`diagnostics_block_prisma`), que não existe na
metodologia da CONTA 2. Não tentamos reproduzir o número exato dela;:
medimos, com o NOSSO critério já usado no baseline (`out_course_bond_
census.json`), quantas coincidências têm pelo menos uma peça de nó (real
ou degradado) dos dois lados.

Reaproveita `run_course_bond_census._wall_dir`/`_t_of`/`_cand_dir_dot`
(mesmas funções, importadas, não reescritas) só para não duplicar a
lógica de projeção no eixo.
"""
import os
import sys

_CROSS_AUDIT_DIR = os.path.dirname(os.path.abspath(__file__))
_LAB_DIR = os.path.dirname(_CROSS_AUDIT_DIR)
if _LAB_DIR not in sys.path:
    sys.path.insert(0, _LAB_DIR)

import lib_audit as A
import run_course_bond_census as RCB

NODE_REASONS = {
    "L_CORNER": "L",
    "T_INTERSECTION_MAIN": "T",
    "T_INTERSECTION_INCOMING": "T",
    "T_INTERSECTION_DEGRADED_L": "T",
    "T_INTERSECTION_INCOMING_DEGRADED": "T",
    "X_INTERSECTION": "X",
    "CORNER_DEGRADED": "L",
}


def _node_kind(reason):
    return NODE_REASONS.get(reason)


def census(run_data):
    solve_result = run_data["solve_result"]
    walls_to_create = run_data["walls_to_create"]
    openings_per_wall = run_data["openings_per_wall"]
    engine = A.engine()

    per_wall_courses = {}
    for course_index, candidate in A.physical_course_candidates(solve_result):
        wall_idx = candidate.get("wall_idx")
        if wall_idx is None:
            continue
        per_wall_courses.setdefault(wall_idx, {}).setdefault(course_index, []).append(candidate)

    breakdown = {"L": 0, "T": 0, "X": 0, "OPENING_JAMB": 0, "OTHER_NONE": 0}
    total_suspect = 0

    for wall_idx, by_course in per_wall_courses.items():
        p0_cm, p1_cm, length_cm, _thick = A.wall_axis(walls_to_create, wall_idx)
        wall_dir = RCB._wall_dir(p0_cm, p1_cm)
        wall_openings = openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else []
        edges_cm = A.opening_edges_cm(wall_openings)

        course_indices = sorted(by_course.keys())
        joints_by_course = {}
        for course_index in course_indices:
            fill = [c for c in by_course[course_index]
                    if RCB._cand_dir_dot(c, wall_dir) >= RCB.PARALLEL_DOT_MIN]
            spans = []
            for c in fill:
                ox, oy = A.candidate_origin_cm(c)
                t_center = RCB._t_of((ox, oy), p0_cm, wall_dir)
                half = c["length_cm"] / 2.0
                spans.append((t_center - half, t_center + half, c))
            spans.sort(key=lambda s: s[0])
            joints = []
            for i in range(len(spans) - 1):
                end_i = spans[i][1]
                start_next = spans[i + 1][0]
                joints.append({"t_cm": (end_i + start_next) / 2.0,
                               "cand_before": spans[i][2], "cand_after": spans[i + 1][2]})
            joints_by_course[course_index] = joints

        for i in range(len(course_indices) - 1):
            a_idx, b_idx = course_indices[i], course_indices[i + 1]
            if b_idx != a_idx + 1:
                continue
            joints_a = joints_by_course.get(a_idx) or []
            joints_b = joints_by_course.get(b_idx) or []
            if not joints_a or not joints_b:
                continue
            for ja in joints_a:
                nearest = min(joints_b, key=lambda jb: abs(jb["t_cm"] - ja["t_cm"]))
                delta = abs(nearest["t_cm"] - ja["t_cm"])
                if delta > RCB.COINCIDENT_TOL_CM:
                    continue
                nearest_edge = min((abs(ja["t_cm"] - e) for e in ([0.0, length_cm] + edges_cm)),
                                    default=1e9)
                cands = (ja["cand_before"], ja["cand_after"], nearest["cand_before"], nearest["cand_after"])
                reasons = [c.get("placement_reason") for c in cands]
                codes = [c.get("logical_code") for c in cands]
                touches_opening_exempt_code = any(
                    code in engine.OPENING_ALIGNED_EXEMPT_CODES for code in codes)
                if nearest_edge <= RCB.EDGE_TOUCH_TOL_CM and touches_opening_exempt_code:
                    continue  # isenta por 11.8, ja contada no censo original
                if nearest_edge <= engine.BOND_STRIP_EDGE_EXEMPT_CM and touches_opening_exempt_code:
                    continue  # ambigua, ja contada no censo original
                total_suspect += 1
                node_kinds = set(filter(None, (_node_kind(r) for r in reasons)))
                if node_kinds:
                    # se mais de um tipo aparece nos 4 candidatos (raro),
                    # prioriza X > T > L so' para ter 1 rotulo por linha do
                    # relatorio - o dado bruto (reasons) fica disponivel.
                    if "X" in node_kinds:
                        breakdown["X"] += 1
                    elif "T" in node_kinds:
                        breakdown["T"] += 1
                    else:
                        breakdown["L"] += 1
                elif nearest_edge <= engine.BOND_STRIP_OPENING_INFLUENCE_CM:
                    breakdown["OPENING_JAMB"] += 1
                else:
                    breakdown["OTHER_NONE"] += 1

    return {"total_suspect_recount": total_suspect, "breakdown_by_touching_node_kind": breakdown}


def main():
    project_ids = sys.argv[1:] or list(A.PROJECT_IDS)
    agg = {"L": 0, "T": 0, "X": 0, "OPENING_JAMB": 0, "OTHER_NONE": 0}
    total = 0
    per_project = {}
    for project_id in project_ids:
        run_data = A.run_solver(project_id)
        result = census(run_data)
        per_project[project_id] = result
        total += result["total_suspect_recount"]
        for k, v in result["breakdown_by_touching_node_kind"].items():
            agg[k] += v
    out = {"per_project": per_project, "aggregate_total_suspect": total, "aggregate_breakdown": agg}
    A.write_json(os.path.join(_CROSS_AUDIT_DIR, "out_node_conflict_breakdown.json"), out)
    print("total suspect (recount):", total)
    print("breakdown:", agg)
    return out


if __name__ == "__main__":
    main()
