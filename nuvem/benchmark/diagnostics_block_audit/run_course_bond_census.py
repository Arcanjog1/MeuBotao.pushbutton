# -*- coding: utf-8 -*-
"""Censo independente — PRISMA / FIADAS (missão CONTA 2, seção 8) + uma
primeira leitura de soluções alternativas não escolhidas (seção 22).

Método (próprio deste censo — não chama `nuvem/benchmark/validators/
validate_prism.py`, embora os números sejam comparáveis a ele como
referência cruzada, ver README.md desta pasta):

Para cada parede, e cada par de fiadas FÍSICAS consecutivas (course_index,
course_index+1) que pertencem à MESMA banda de abertura (ver seção 4 das
REGRAS — comparar fiadas de bandas diferentes não faz sentido, o conjunto
de peças muda por desenho):

1. Filtra os candidatos de `course_candidates[course_index]` cujo
   `wall_idx` é a parede em questão E cujo `x_dir` é paralelo (dot >= 0.99)
   à direção do eixo da parede — só peças de PREENCHIMENTO/CORPO contam
   para prisma (uma peça de nó travada 90° fora do eixo não faz parte da
   sequência longitudinal).
2. Projeta o centro de cada peça no eixo da parede (parâmetro `t`, cm) e
   ordena por `t`.
3. A JUNTA entre duas peças vizinhas é o ponto médio entre o fim de uma e
   o início da próxima.
4. Compara o conjunto de juntas da fiada N com o da fiada N+1: para cada
   junta de N, acha a mais próxima em N+1. `|delta| <= COINCIDENT_TOL_CM`
   é candidato a `CONTINUOUS_VERTICAL_JOINT` (regra #1, obrigatória) — a
   menos que caia dentro do raio de isenção de uma abertura/ponta de
   parede (seção 11.8 das REGRAS: C04/C09/B19 encostados num vão podem
   alinhar) OU dentro de `BOND_STRIP_EDGE_EXEMPT_CM`/`BOND_STRIP_
   OPENING_INFLUENCE_CM` (mesmo raio que a auditoria oficial usa para nó,
   reaproveitado aqui só como CONTEXTO, nunca para decidir sozinho — ver
   `RULE_AMBIGUOUS` abaixo).

Casos em que a classificação depende de saber se a peça encostada é uma
das exceções do código (C04/C09/B19) E se ela realmente encosta na borda
(não só "perto"): quando os dados brutos não deixam claro (peça no meio
do intervalo de isenção mas não tocando a borda), o caso é marcado
`RULE_AMBIGUOUS` e o dado bruto é mantido (nunca promovido a violação nem
descartado — pedido explícito da missão, item 8).
"""
import statistics
import sys

import lib_audit as A

COINCIDENT_TOL_CM = 1.0  # abaixo disso, juntas contam como "na mesma posição"
EDGE_TOUCH_TOL_CM = 0.6  # "encostada na borda de verdade" (abertura/ponta)
PARALLEL_DOT_MIN = 0.99


def _wall_dir(p0_cm, p1_cm):
    dx = p1_cm[0] - p0_cm[0]
    dy = p1_cm[1] - p0_cm[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1e-9:
        return (1.0, 0.0)
    return (dx / length, dy / length)


def _t_of(point_cm, p0_cm, dir_xy):
    dx = point_cm[0] - p0_cm[0]
    dy = point_cm[1] - p0_cm[1]
    return dx * dir_xy[0] + dy * dir_xy[1]


def _cand_dir_dot(candidate, wall_dir):
    xd = candidate["x_dir"]
    return abs(xd.X * wall_dir[0] + xd.Y * wall_dir[1])


def _opening_edges_cm(openings_for_wall):
    edges = []
    for t_start_ft, t_end_ft, _sill_ft, _head_ft in openings_for_wall:
        edges.append(A.ft_to_cm(t_start_ft))
        edges.append(A.ft_to_cm(t_end_ft))
    return edges


def census(run_data):
    solve_result = run_data["solve_result"]
    walls_to_create = run_data["walls_to_create"]
    openings_per_wall = run_data["openings_per_wall"]
    course_candidates = solve_result.get("course_candidates") or {}
    engine = A.engine()

    per_wall_courses = {}
    for course_index, candidate in A.physical_course_candidates(solve_result):
        wall_idx = candidate.get("wall_idx")
        if wall_idx is None:
            continue
        per_wall_courses.setdefault(wall_idx, {}).setdefault(course_index, []).append(candidate)

    total_pairs = 0
    coincident_suspect = 0
    coincident_exempt_opening = 0
    coincident_exempt_edge = 0
    ambiguous = 0
    stagger_values_cm = []
    suspects_sample = []
    walls_with_suspect = set()

    for wall_idx, by_course in per_wall_courses.items():
        p0_cm, p1_cm, length_cm, _thickness_cm = A.wall_axis(walls_to_create, wall_idx)
        wall_dir = _wall_dir(p0_cm, p1_cm)
        edges_cm = [0.0, length_cm] + _opening_edges_cm(openings_per_wall[wall_idx]
                                                          if wall_idx < len(openings_per_wall) else [])

        course_indices = sorted(by_course.keys())
        joints_by_course = {}
        for course_index in course_indices:
            fill = [c for c in by_course[course_index]
                    if _cand_dir_dot(c, wall_dir) >= PARALLEL_DOT_MIN]
            spans = []
            for c in fill:
                ox, oy = A.candidate_origin_cm(c)
                t_center = _t_of((ox, oy), p0_cm, wall_dir)
                half = c["length_cm"] / 2.0
                spans.append((t_center - half, t_center + half, c["logical_code"]))
            spans.sort(key=lambda s: s[0])
            joints = []
            for i in range(len(spans) - 1):
                end_i = spans[i][1]
                start_next = spans[i + 1][0]
                joint_t = (end_i + start_next) / 2.0
                joints.append({"t_cm": joint_t, "code_before": spans[i][2],
                               "code_after": spans[i + 1][2]})
            joints_by_course[course_index] = joints

        for i in range(len(course_indices) - 1):
            a_idx, b_idx = course_indices[i], course_indices[i + 1]
            if b_idx != a_idx + 1:
                continue  # não são fisicamente adjacentes (banda descontínua)
            joints_a = joints_by_course.get(a_idx) or []
            joints_b = joints_by_course.get(b_idx) or []
            if not joints_a or not joints_b:
                continue
            for ja in joints_a:
                nearest = min(joints_b, key=lambda jb: abs(jb["t_cm"] - ja["t_cm"]))
                delta = abs(nearest["t_cm"] - ja["t_cm"])
                total_pairs += 1
                stagger_values_cm.append(round(delta, 3))
                if delta <= COINCIDENT_TOL_CM:
                    nearest_edge = min((abs(ja["t_cm"] - e) for e in edges_cm), default=1e9)
                    exempt_codes = {ja["code_before"], ja["code_after"],
                                     nearest["code_before"], nearest["code_after"]}
                    touches_exempt_code = bool(exempt_codes & set(engine.OPENING_ALIGNED_EXEMPT_CODES))
                    if nearest_edge <= EDGE_TOUCH_TOL_CM and touches_exempt_code:
                        coincident_exempt_opening += 1
                    elif nearest_edge <= engine.BOND_STRIP_EDGE_EXEMPT_CM and touches_exempt_code:
                        # perto da borda E peça isenta, mas nao comprovadamente
                        # ENCOSTADA (tolerancia maior) -> ambigua, nao decidida
                        # por suposicao (item 8 da missao).
                        ambiguous += 1
                    else:
                        coincident_suspect += 1
                        walls_with_suspect.add(wall_idx)
                        if len(suspects_sample) < 40:
                            suspects_sample.append({
                                "wall_idx": wall_idx, "course_a": a_idx, "course_b": b_idx,
                                "t_cm": round(ja["t_cm"], 2), "delta_cm": round(delta, 3),
                                "codes_a": (ja["code_before"], ja["code_after"]),
                                "codes_b": (nearest["code_before"], nearest["code_after"]),
                                "nearest_edge_cm": round(nearest_edge, 2),
                            })

    stagger_hist = {}
    for v in stagger_values_cm:
        bucket = "0-1" if v <= 1 else ("1-3" if v <= 3 else ("3-10" if v <= 10 else ("10-20" if v <= 20 else ">20")))
        stagger_hist[bucket] = stagger_hist.get(bucket, 0) + 1

    # --- item 22 (leve): soluções alternativas não escolhidas, minerando
    # TODAS as variantes que o solver gerou para o mesmo segmento (aggregate
    # `candidates`, que contem variant_count composicoes, mesmo que so' UMA
    # seja fisicamente materializada em cada fiada - ver
    # solve_building_blocks_all_courses). So' relevante quando a rodada usa
    # variants_per_course > 1 (produção usa 1 hoje - secao 18.4 das REGRAS).
    alt_solutions_by_segment = {}
    for c in solve_result.get("candidates") or []:
        variant = c.get("course_variant")
        if variant is None:
            continue
        wall_idx = c.get("wall_idx")
        key = (wall_idx, c.get("course"))
        alt_solutions_by_segment.setdefault(key, {}).setdefault(variant, []).append(c["logical_code"])
    alt_examples = []
    for key, variants in alt_solutions_by_segment.items():
        if len(variants) < 2:
            continue
        codes_by_variant = {v: tuple(sorted(codes)) for v, codes in variants.items()}
        distinct = set(codes_by_variant.values())
        if len(distinct) < 2:
            continue
        has_compensator_variant = any(
            any(code in ("C04", "C09") for code in codes) for codes in codes_by_variant.values())
        no_compensator_variant = any(
            not any(code in ("C04", "C09") for code in codes) for codes in codes_by_variant.values())
        entry = {"wall_idx": key[0], "course": key[1],
                 "variants": {str(v): list(c) for v, c in codes_by_variant.items()}}
        if has_compensator_variant and no_compensator_variant:
            entry["note"] = "existe variante sem compensador para o mesmo segmento"
        alt_examples.append(entry)
        if len(alt_examples) >= 30:
            break

    return {
        "method": __doc__.strip().splitlines()[0],
        "coincident_tolerance_cm": COINCIDENT_TOL_CM,
        "pairs_of_consecutive_courses_measured": total_pairs,
        "joint_coincidence": {
            "suspect_continuous_vertical_joint": coincident_suspect,
            "exempt_opening_touch_11_8": coincident_exempt_opening,
            "ambiguous_near_edge_not_confirmed_touch": ambiguous,
            "not_coincident": total_pairs - coincident_suspect - coincident_exempt_opening - ambiguous,
        },
        "walls_with_suspect_continuous_joint": len(walls_with_suspect),
        "stagger_cm_summary": {
            "count": len(stagger_values_cm),
            "min": min(stagger_values_cm) if stagger_values_cm else None,
            "median": statistics.median(stagger_values_cm) if stagger_values_cm else None,
            "mean": round(statistics.fmean(stagger_values_cm), 3) if stagger_values_cm else None,
            "max": max(stagger_values_cm) if stagger_values_cm else None,
            "histogram_cm": stagger_hist,
        },
        "suspects_sample": suspects_sample,
        "variants_per_course_used": run_data["variants_per_course"],
        "alternative_solutions_same_segment_different_variant": {
            "note": ("so' populado quando variants_per_course > 1 na rodada; "
                     "producao real usa variants_per_course=1 (secao 18.4 das "
                     "REGRAS) - ver run_full_census para uma rodada extra com K=3"),
            "count_segments_with_alternatives": len(alt_examples),
            "examples": alt_examples,
        },
    }


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else A.PRIMARY_PROJECT_ID
    run_data = A.run_solver(project_id)
    result = census(run_data)
    result["project_id"] = project_id
    A.write_json(A.out_path("out_course_bond_census.json"), result)
    print("prisma:", result["joint_coincidence"])
    return result


if __name__ == "__main__":
    main()
