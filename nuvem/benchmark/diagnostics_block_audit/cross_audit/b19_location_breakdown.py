# -*- coding: utf-8 -*-
"""CROSS AUDIT — detalhe de localização do B19 (item pedido na seção 5 da
missão: "meio de parede / perto de abertura / perto de ponta /
alinhamentos verticais"), separado do `run_special_block_census.py`
original da CONTA 2 porque aquele censo só guarda a distância até a
borda MAIS PRÓXIMA (sem dizer se essa borda é abertura ou ponta de
parede) — não é lógica de classificação NOVA, é a MESMA definição de
"borda" (`lib_audit.opening_edges_cm` + pontas 0/comprimento), só
reportada com o tipo de borda em vez do mínimo agregado.

Limiar de "encostado" = 5cm (mais generoso que `OPENING_OVERLAP_
TOLERANCE_CM=0,2cm`, de propósito: aqui a pergunta é "está perto o
bastante para ser lido como intencional", não "invade fisicamente").
"""
import sys
import os

_CROSS_AUDIT_DIR = os.path.dirname(os.path.abspath(__file__))
_LAB_DIR = os.path.dirname(_CROSS_AUDIT_DIR)
if _LAB_DIR not in sys.path:
    sys.path.insert(0, _LAB_DIR)

import lib_audit as A

TOUCH_TOL_CM = 5.0


def census(run_data, code="B19"):
    walls_to_create = run_data["walls_to_create"]
    solve_result = run_data["solve_result"]
    openings_per_wall = run_data["openings_per_wall"]
    spans_by_wall_course = A.wall_course_spans(walls_to_create, solve_result, only_parallel=True)

    counts = {"NEAR_OPENING": 0, "NEAR_WALL_END": 0, "MID_WALL": 0, "AMBIGUOUS_BOTH": 0}
    vertical_alignment_candidates = 0
    total = 0
    by_wall = {}

    for (wall_idx, course_index), spans in spans_by_wall_course.items():
        wall_openings = openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else []
        opening_edges = A.opening_edges_cm(wall_openings)
        _p0, _p1, _dir, wall_length_cm, _thick = A.wall_direction_cm(walls_to_create, wall_idx)
        for span in spans:
            if span["code"] != code:
                continue
            total += 1
            # Distancia da BORDA do bloco (t_start/t_end), nao do centro -
            # um B19 de 19cm ENCOSTADO numa abertura tem o centro a ~9,5cm
            # do vao, mas a borda a ~0cm (mais a junta).
            block_edges = (span["t_start_cm"], span["t_end_cm"])
            d_opening = min((abs(be - e) for be in block_edges for e in opening_edges), default=1e9)
            d_end = min(abs(be - 0.0) for be in block_edges)
            d_end = min(d_end, min(abs(be - wall_length_cm) for be in block_edges))
            near_opening = d_opening <= TOUCH_TOL_CM
            near_end = d_end <= TOUCH_TOL_CM
            if near_opening and near_end:
                counts["AMBIGUOUS_BOTH"] += 1
            elif near_opening:
                counts["NEAR_OPENING"] += 1
            elif near_end:
                counts["NEAR_WALL_END"] += 1
            else:
                counts["MID_WALL"] += 1
            by_wall.setdefault(wall_idx, []).append((course_index, round(span["t_center_cm"], 1)))

    # alinhamento vertical: mesma parede, posicao t proxima (tolerancia
    # generosa de 5cm, mesma logica de vertical_strips do censo original,
    # so' que aqui conta QUALQUER par de fiadas alinhado, nao so' runs >=3
    # (pedido explicito da missao: "alinhamentos verticais" no plural, sem
    # piso de 3 fiadas).
    for wall_idx, occs in by_wall.items():
        occs_sorted = sorted(occs, key=lambda o: o[1])
        used = [False] * len(occs_sorted)
        for i in range(len(occs_sorted)):
            if used[i]:
                continue
            cluster = [occs_sorted[i]]
            for j in range(i + 1, len(occs_sorted)):
                if used[j]:
                    continue
                if abs(occs_sorted[j][1] - occs_sorted[i][1]) <= TOUCH_TOL_CM:
                    cluster.append(occs_sorted[j])
                    used[j] = True
            if len(cluster) >= 2:
                vertical_alignment_candidates += 1

    return {
        "code": code,
        "touch_tolerance_cm": TOUCH_TOL_CM,
        "total": total,
        "location_breakdown": counts,
        "vertical_alignment_clusters_2plus_courses": vertical_alignment_candidates,
    }


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else A.PRIMARY_PROJECT_ID
    run_data = A.run_solver(project_id)
    result = census(run_data)
    result["project_id"] = project_id
    A.write_json(os.path.join(_CROSS_AUDIT_DIR, "out_b19_location_%s.json" % project_id), result)
    print(project_id, result["location_breakdown"], "valign_clusters=",
          result["vertical_alignment_clusters_2plus_courses"])
    return result


if __name__ == "__main__":
    main()
