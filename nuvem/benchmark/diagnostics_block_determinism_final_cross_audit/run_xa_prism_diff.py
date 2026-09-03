# -*- coding: utf-8 -*-
"""DIFF por VIOLACAO das novas `PRISM_CONTINUOUS_JOINT` (itens 8 e 9).

Para cada violacao nova, emite exatamente os campos pedidos:
PROJECT / WALL / COURSE_A / COURSE_B / JOINT_POSITION_A / JOINT_POSITION_B /
BLOCK_LEFT / BLOCK_RIGHT / NODE_TYPE proximo / DISTANCE_TO_NODE / REASON.

Roda contra o ponto de medicao ATUAL da arvore em que for executado; o
antes/depois e' feito comparando dois arquivos gerados em duas arvores.

    python3 run_xa_prism_diff.py <label> <project_id>
"""
import os
import sys
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_xa as X  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(X._NUVEM), "nuvem"))
from benchmark import runner, solver_bridge, analysis, model   # noqa: E402
from benchmark.extract import from_solver                      # noqa: E402
from benchmark.validators import validate_prism                # noqa: E402


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "head"
    project_id = sys.argv[2] if len(sys.argv) > 2 else "piloto_sintetico_2x2"

    inp = runner._read_json(runner.project_paths(project_id)["input"])
    (solve_result, walls, nodes, openings, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(inp)
    project = from_solver.project_from_solver(
        project_id, solve_result, walls, nodes, openings, catalog,
        base_z_ft, num_courses, metadata={})

    node_points = [(n["point"].X * X.FT_TO_CM, n["point"].Y * X.FT_TO_CM,
                    n.get("kind")) for n in nodes]

    rows = []
    for wall in project.get("walls") or []:
        start = wall.get("start_cm") or [0.0, 0.0]
        end = wall.get("end_cm") or [0.0, 0.0]
        length = math.hypot(end[0] - start[0], end[1] - start[1]) or 1.0
        ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
        rows_by_row = dict((r["row"], r) for r in model.rows_sorted(wall))
        for finding in validate_prism.validate_wall(wall):
            if finding["code"] != "PRISM_CONTINUOUS_JOINT":
                continue
            t_cm = finding["joint_t_cm"]
            jx, jy = start[0] + ux * t_cm, start[1] + uy * t_cm
            nearest, nkind, ndist = None, None, None
            for nx, ny, kind in node_points:
                d = math.hypot(nx - jx, ny - jy)
                if ndist is None or d < ndist:
                    nearest, nkind, ndist = (round(nx, 2), round(ny, 2)), kind, d

            def block_at(row_index, side, code):
                row = rows_by_row.get(row_index)
                if not row:
                    return None
                for block in row.get("blocks") or []:
                    if block.get("code") != code:
                        continue
                    edge = block.get("t_end_cm") if side == "left" else block.get("t_start_cm")
                    if edge is not None and abs(edge - t_cm) <= 1.5:
                        return {"code": code,
                                "t_start_cm": round(block.get("t_start_cm"), 2),
                                "t_end_cm": round(block.get("t_end_cm"), 2),
                                "origem": block.get("placement_reason") or block.get("source")}
                return {"code": code}

            rows.append({
                "PROJECT": project_id,
                "WALL": wall["id"],
                "COURSE_A": finding["row_a"],
                "COURSE_B": finding["row_b"],
                "JOINT_POSITION_A": finding["joint_a"]["t_cm"],
                "JOINT_POSITION_B": finding["joint_b"]["t_cm"],
                "DISTANCE_CM": finding["stagger_cm"],
                "A_BLOCK_LEFT": block_at(finding["row_a"], "left", finding["joint_a"]["left_code"]),
                "A_BLOCK_RIGHT": block_at(finding["row_a"], "right", finding["joint_a"]["right_code"]),
                "B_BLOCK_LEFT": block_at(finding["row_b"], "left", finding["joint_b"]["left_code"]),
                "B_BLOCK_RIGHT": block_at(finding["row_b"], "right", finding["joint_b"]["right_code"]),
                "NEAREST_NODE": nearest,
                "NODE_TYPE": nkind,
                "DISTANCE_TO_NODE_CM": round(ndist, 2) if ndist is not None else None,
                "REASON": None,   # preenchido abaixo
            })

    # classificacao da CAUSA de cada violacao, pela origem dos blocos
    for row in rows:
        origins = [(row["A_BLOCK_LEFT"] or {}).get("origem"),
                   (row["A_BLOCK_RIGHT"] or {}).get("origem"),
                   (row["B_BLOCK_LEFT"] or {}).get("origem"),
                   (row["B_BLOCK_RIGHT"] or {}).get("origem")]
        node_side = [o for o in origins if o and o not in ("STANDARD_FILL", "OPENING_REPAIR_FILL")]
        if node_side:
            row["REASON"] = ("JUNTA_PECA_DE_NO_x_PREENCHIMENTO nao entra em "
                             "`_layout_internal_joint_positions_cm`: a fiada oposta "
                             "nao a ve' como junta a evitar (origens: %s)"
                             % sorted(set(node_side)))
        else:
            row["REASON"] = "juntas INTERNAS de preenchimento nas duas fiadas"

    key = lambda r: (r["WALL"], r["COURSE_A"], r["COURSE_B"], r["JOINT_POSITION_A"])
    rows.sort(key=key)
    out = {"label": label, "project_id": project_id, "n": len(rows), "violacoes": rows}
    X.write_json(X.out_path("out_xa_prism_diff_%s_%s.json" % (label, project_id)), out)
    print(label, project_id, "PRISM_CONTINUOUS_JOINT =", len(rows))
    for row in rows:
        print("  %s f%s/f%s  t=%.2f  dist=%.2f  no'=%s a %.1fcm | %s" % (
            row["WALL"], row["COURSE_A"], row["COURSE_B"], row["JOINT_POSITION_A"],
            row["DISTANCE_CM"], row["NODE_TYPE"], row["DISTANCE_TO_NODE_CM"],
            row["REASON"][:70]))
    return out


if __name__ == "__main__":
    main()
