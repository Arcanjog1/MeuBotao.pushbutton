# -*- coding: utf-8 -*-
"""Censo independente — aberturas e "bloco dentro de vão" (missão CONTA 2,
seções 17-18).

Duas medições independentes, deliberadamente separadas:

1. **Portas/janelas** — a partir de `openings_per_wall` (dado de entrada,
   Fase A) e do que o solver reporta (`non_modular`, `alignment_conflicts`,
   `jamb_exceptions`, `door_void_violations`). Porta sem peitoril é
   classificada usando a MESMA constante de produção
   (`DOOR_NO_SILL_MAX_SILL_CM`), só como leitura.

2. **Bloco dentro do vão, por EXTENT real** — item 18 da missão, "não usar
   apenas ponto central". Para cada peça materializada (`course_candidates`)
   cujo eixo é paralelo ao da própria parede, calcula o intervalo
   `[t_start_cm, t_end_cm]` (usando o COMPRIMENTO real da peça, não o
   centro) e classifica contra cada abertura da parede:
     - `FORA`: não toca o intervalo da abertura;
     - `DENTRO`: o intervalo da peça está inteiramente contido no vão
       (mais a tolerância `OPENING_OVERLAP_TOLERANCE_CM` da produção);
     - `PARCIAL`: sobrepõe só uma parte.
   Essa classificação é feita por uma conta geométrica PRÓPRIA (não chama
   `classify_extent_against_openings`). Depois, para uma amostra, a função
   de produção `classify_extent_against_openings`
   (`core/engine/opening_audit.py`) é chamada sobre os MESMOS dados, e as
   duas respostas são comparadas — trata a função de produção como objeto
   de estudo, nunca como fonte de verdade automática (pedido explícito da
   missão: "não confie cegamente na função").
"""
import sys

import lib_audit as A


def _classify_own(t_start_cm, t_end_cm, opening_start_cm, opening_end_cm, tol_cm):
    """Mesma DEFINIÇÃO documentada na seção 23.2 das REGRAS ("peça é
    derrubada se o corpo invade o vão em mais de
    OPENING_OVERLAP_TOLERANCE_CM"), implementada de forma independente
    (sem chamar `classify_extent_against_openings`) para servir de
    verificação cruzada — ver `cross_check_against_...` abaixo."""
    lo, hi = min(t_start_cm, t_end_cm), max(t_start_cm, t_end_cm)
    a, b = min(opening_start_cm, opening_end_cm), max(opening_start_cm, opening_end_cm)
    overlap = min(hi, b) - max(lo, a)
    if overlap <= tol_cm:
        return "FORA"
    inside = (lo >= a - tol_cm) and (hi <= b + tol_cm)
    return "DENTRO" if inside else "PARCIAL"


def census(run_data):
    engine = A.engine()
    walls_to_create = run_data["walls_to_create"]
    solve_result = run_data["solve_result"]
    openings_per_wall = run_data["openings_per_wall"]

    # --- 1) portas/janelas, a partir do dado de entrada -------------------
    total_openings = 0
    doors_no_sill = 0
    windows = 0
    width_cm_values = []
    for wall_idx, entries in enumerate(openings_per_wall):
        for t_start_ft, t_end_ft, sill_ft, _head_ft in entries:
            total_openings += 1
            width_cm = A.ft_to_cm(t_end_ft - t_start_ft)
            width_cm_values.append(round(width_cm, 2))
            sill_cm = A.ft_to_cm(sill_ft)
            if sill_cm <= engine.DOOR_NO_SILL_MAX_SILL_CM:
                doors_no_sill += 1
            else:
                windows += 1

    non_modular = solve_result.get("non_modular") or []
    alignment_conflicts = solve_result.get("alignment_conflicts") or []
    jamb_exceptions = solve_result.get("jamb_exceptions") or []
    door_void_violations = solve_result.get("door_void_violations") or []

    non_modular_walls = sorted(set(e.get("wall_idx") for e in non_modular if e.get("wall_idx") is not None))

    # --- 2) bloco dentro do vao, por EXTENT real ---------------------------
    # IMPORTANTE (secao 4 das REGRAS): uma janela so' e' vazia na FAIXA
    # VERTICAL REAL do seu vao - fiadas abaixo do peitoril ou acima da verga
    # continuam SOLIDAS ali, de proposito. Comparar contra TODAS as
    # aberturas de `openings_per_wall` sem filtrar por banda superestimaria
    # "bloco dentro do vao" em toda fiada fora da faixa da janela - por
    # isso a mesma filtragem por banda do motor real e' reaplicada aqui
    # (`_course_z_band`/`_opening_active_in_course_band`, objeto de estudo,
    # nao reimplementado).
    spans_by_wall_course = A.wall_course_spans(walls_to_create, solve_result, only_parallel=True)
    tol_cm = engine.OPENING_OVERLAP_TOLERANCE_CM
    classification_counts = {"FORA": 0, "DENTRO": 0, "PARCIAL": 0}
    partial_or_inside_examples = []
    cross_check_agree = 0
    cross_check_disagree = 0
    cross_check_samples = []

    catalog = run_data["catalog"]
    base_z_ft = run_data["base_z_ft"]
    course_height_ft, _height_err = engine._course_height_ft(catalog, None)
    block_height_ft = course_height_ft - engine._cm_to_ft(engine.COURSE_JOINT_CM)

    for (wall_idx, course_index), spans in spans_by_wall_course.items():
        wall_openings = openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else []
        if not wall_openings:
            continue
        z_lo_abs, z_hi_abs = engine._course_z_band(base_z_ft, course_index, course_height_ft, block_height_ft)
        active_openings = [
            (t0, t1, sill, head) for (t0, t1, sill, head) in wall_openings
            if engine._opening_active_in_course_band(sill, head, z_lo_abs, z_hi_abs)
        ]
        if not active_openings:
            continue
        opening_intervals_cm = [
            (A.ft_to_cm(t0), A.ft_to_cm(t1)) for t0, t1, _sill, _head in active_openings
        ]
        for span in spans:
            worst = "FORA"
            for lo_cm, hi_cm in opening_intervals_cm:
                verdict = _classify_own(span["t_start_cm"], span["t_end_cm"], lo_cm, hi_cm, tol_cm)
                if verdict == "DENTRO":
                    worst = "DENTRO"
                    break
                if verdict == "PARCIAL" and worst != "DENTRO":
                    worst = "PARCIAL"
            classification_counts[worst] += 1
            if worst != "FORA":
                if len(partial_or_inside_examples) < 40:
                    partial_or_inside_examples.append({
                        "wall_idx": wall_idx, "course_index": course_index,
                        "code": span["code"], "verdict": worst,
                        "t_range_cm": [round(span["t_start_cm"], 2), round(span["t_end_cm"], 2)],
                    })
                if len(cross_check_samples) < 60:
                    try:
                        prod_raw = engine.classify_extent_against_openings(
                            span["t_start_cm"], span["t_end_cm"], opening_intervals_cm,
                            tolerance_cm=tol_cm)
                        # (BLOCK_OUTSIDE_OPENING/BLOCK_INSIDE_OPENING/
                        # BLOCK_PARTIAL_OPENING, opening_index, overlap_cm)
                        prod_verdict = {
                            engine.BLOCK_OUTSIDE_OPENING: "FORA",
                            engine.BLOCK_INSIDE_OPENING: "DENTRO",
                            engine.BLOCK_PARTIAL_OPENING: "PARCIAL",
                        }.get(prod_raw[0], "UNKNOWN:" + str(prod_raw[0]))
                    except Exception as exc:
                        prod_verdict = "ERROR:" + repr(exc)
                    agree = (prod_verdict == worst)
                    cross_check_agree += int(agree)
                    cross_check_disagree += int(not agree)
                    cross_check_samples.append({
                        "wall_idx": wall_idx, "course_index": course_index, "code": span["code"],
                        "own_verdict": worst, "production_verdict": prod_verdict, "agree": agree,
                    })

    return {
        "openings_input": {
            "total": total_openings,
            "doors_no_sill": doors_no_sill,
            "windows_or_sill_gt_threshold": windows,
            "door_no_sill_threshold_cm": engine.DOOR_NO_SILL_MAX_SILL_CM,
            "width_cm_summary": _summary(width_cm_values),
        },
        "solver_reported": {
            "non_modular_segments": len(non_modular),
            "non_modular_distinct_walls": len(non_modular_walls),
            "alignment_conflicts": len(alignment_conflicts),
            "jamb_exceptions": len(jamb_exceptions),
            "door_void_violations": len(door_void_violations),
            "door_void_violations_sample": door_void_violations[:10],
        },
        "block_extent_vs_opening_own_measurement": {
            "tolerance_cm": tol_cm,
            "classification_counts": classification_counts,
            "partial_or_inside_examples": partial_or_inside_examples,
        },
        "cross_check_against_classify_extent_against_openings": {
            "sampled": cross_check_agree + cross_check_disagree,
            "agree": cross_check_agree,
            "disagree": cross_check_disagree,
            "samples": cross_check_samples[:20],
        },
    }


def _summary(values):
    if not values:
        return None
    values = sorted(values)
    n = len(values)
    return {"count": n, "min": values[0], "max": values[-1], "median": values[n // 2],
            "mean": round(sum(values) / n, 2)}


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else A.PRIMARY_PROJECT_ID
    run_data = A.run_solver(project_id)
    result = census(run_data)
    result["project_id"] = project_id
    A.write_json(A.out_path("out_opening_census.json"), result)
    print("openings:", result["openings_input"]["total"],
          "doors_no_sill=", result["openings_input"]["doors_no_sill"])
    print("extent classification:", result["block_extent_vs_opening_own_measurement"]["classification_counts"])
    print("cross-check vs producao:", result["cross_check_against_classify_extent_against_openings"]["agree"],
          "/", result["cross_check_against_classify_extent_against_openings"]["sampled"])
    return result


if __name__ == "__main__":
    main()
