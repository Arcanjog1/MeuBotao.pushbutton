# -*- coding: utf-8 -*-
"""Medicao HEADLESS de PRISMA / FIADAS / AMARRACAO VERTICAL (CR-BLOCK-01).

Este modulo NAO reimplementa o solver: ele roda o solver REAL
(`solve_building_blocks_all_courses`, via `benchmark/solver_bridge.py`) e
mede a geometria que sai dele. Toda leitura de junta e' feita no
REFERENCIAL LONGITUDINAL DA PAREDE (projecao do corpo de cada peca sobre o
eixo, em cm a partir de `p0`) - nunca por indice de bloco, ordem da lista,
ElementId ou coordenada global crua (regra 24.4 e secao 9 do CR).

Taxonomia de coincidencia de junta entre uma fiada e a IMEDIATAMENTE
anterior (secao 10 do CR):

  FORBIDDEN_JOINT_ALIGNMENT
      juntas coincidem e NENHUMA regra documentada permite - e' a
      violacao da regra #1 (secao 11 de REGRAS_MODULACAO_BLOCOS.md).
  DOCUMENTED_EXCEPTION
      juntas coincidem e a EXCECAO da secao 11.8 se aplica (C04/C09/B19
      encostado numa borda de abertura ou na ponta do eixo). Usa a MESMA
      funcao do motor (`_joint_is_opening_aligned_exempt`), nunca uma
      copia.
  UNCLASSIFIED_RULE_CONFLICT
      juntas coincidem e a coincidencia e' consequencia DIRETA de uma peca
      de amarracao de no' (L/T/X, `node_index is not None`), que a secao 5
      manda repetir na mesma posicao. Duas regras documentadas se cruzam
      aqui e o documento nao diz qual vence - registrado, nunca "resolvido"
      por suposicao.
  NO_ALIGNMENT
      a junta desta fiada nao coincide com nenhuma da fiada anterior.
"""

import hashlib
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
if _BENCH not in sys.path:
    sys.path.insert(0, _BENCH)

import solver_bridge  # noqa: E402


# Tolerancia de COINCIDENCIA: a mesma que o proprio solver usa para decidir
# se duas juntas sao "a mesma junta vertical continua"
# (`VERTICAL_JOINT_STAGGER_TOLERANCE_CM`, wall_stepper.py). Medir com outro
# numero mediria outra coisa.
def _tolerances(module):
    return {
        "joint_coincidence_cm": module.VERTICAL_JOINT_STAGGER_TOLERANCE_CM,
        "max_adjacent_gap_cm": module.BOND_MAX_ADJACENT_GAP_CM,
        "cluster_cm": module.BOND_JOINT_CLUSTER_TOLERANCE_CM,
    }


def _wall_axis(module, walls_to_create, wall_idx):
    p0, _p1, wall_dir, length_ft, _t = module._wall_axis_and_length(walls_to_create, wall_idx)
    return p0, wall_dir, length_ft / module.FEET_PER_METER * 100.0


def wall_course_extents(module, walls_to_create, course_candidates, num_courses):
    """{(wall_idx, course_index): [(t_start_cm, t_end_cm, code, is_node), ...]}
    ORDENADO por t_start - a projecao do corpo de cada peca no eixo da
    parede. `is_node` marca as pecas de amarracao de no' (L/T/X)."""
    out = {}
    for course_index in range(num_courses):
        for cand in course_candidates.get(course_index) or []:
            wall_idx = cand.get("wall_idx")
            if wall_idx is None:
                continue
            key = (wall_idx, course_index)
            if key not in out:
                out[key] = []
            out[key].append(cand)
    extents = {}
    axis_cache = {}
    for (wall_idx, course_index), cands in out.items():
        if wall_idx not in axis_cache:
            axis_cache[wall_idx] = _wall_axis(module, walls_to_create, wall_idx)
        p0, wall_dir, _length_cm = axis_cache[wall_idx]
        items = []
        for cand in cands:
            t_start, t_end = module._candidate_extent_on_wall_axis(cand, p0, wall_dir)
            is_tie = bool(module._is_tie_candidate(cand)) or cand.get("node_index") is not None
            items.append((min(t_start, t_end), max(t_start, t_end),
                          cand.get("logical_code"), is_tie))
        items.sort(key=lambda e: (round(e[0], 4), round(e[1], 4), e[2]))
        extents[(wall_idx, course_index)] = items
    return extents, axis_cache


def course_joints(module, items, opening_edges_cm, length_cm, max_gap_cm):
    """Juntas INTERNAS de uma fiada de uma parede, no referencial
    longitudinal: [{"x_cm", "exempt", "node"}]. Duas pecas separadas por
    mais de `max_gap_cm` nao formam junta (ha' um vao entre elas) - a
    mesma protecao de `BOND_MAX_ADJACENT_GAP_CM` da auditoria oficial."""
    joints = []
    for i in range(len(items) - 1):
        a, b = items[i], items[i + 1]
        gap = b[0] - a[1]
        if gap < -1e-6 or gap > max_gap_cm:
            continue
        exempt = module._joint_is_opening_aligned_exempt(
            (a[0], a[1], a[2]), (b[0], b[1], b[2]), opening_edges_cm, length_cm)
        joints.append({
            "x_cm": (a[1] + b[0]) / 2.0,
            "exempt": bool(exempt),
            "node": bool(a[3] or b[3]),
        })
    return joints


def _classify(joint, prev_joints, tol_cm):
    """(classe, stagger_cm) desta junta contra a fiada anterior."""
    best = None
    match = None
    for other in prev_joints:
        d = abs(joint["x_cm"] - other["x_cm"])
        if best is None or d < best:
            best, match = d, other
    if best is None:
        return "NO_ALIGNMENT", None
    if best > tol_cm:
        return "NO_ALIGNMENT", best
    if joint["exempt"] or match["exempt"]:
        return "DOCUMENTED_EXCEPTION", best
    if joint["node"] or match["node"]:
        return "UNCLASSIFIED_RULE_CONFLICT", best
    return "FORBIDDEN_JOINT_ALIGNMENT", best


def _opening_edges_cm(module, openings_per_wall, wall_idx):
    edges = []
    if openings_per_wall and wall_idx < len(openings_per_wall):
        for op in (openings_per_wall[wall_idx] or []):
            edges.append(op[0] / module.FEET_PER_METER * 100.0)
            edges.append(op[1] / module.FEET_PER_METER * 100.0)
    return edges


def _opening_intervals_cm(module, openings_per_wall, wall_idx):
    out = []
    if openings_per_wall and wall_idx < len(openings_per_wall):
        for op in (openings_per_wall[wall_idx] or []):
            out.append((op[0] / module.FEET_PER_METER * 100.0,
                        op[1] / module.FEET_PER_METER * 100.0))
    return out


def _openings_active_by_course(module, openings_per_wall, solve_result, num_courses,
                               catalog, base_z_abs):
    """{course_index: openings_per_wall ATIVO naquela fiada}, reusando as
    BANDAS que o proprio solver montou (`bands` de
    `solve_building_blocks_all_courses`)."""
    out = {}
    for band in solve_result.get("bands") or []:
        result = band.get("result") or {}
        filtered = result.get("openings_per_wall")
        for course_index in band.get("course_indices") or []:
            out[course_index] = filtered
    if any(v is not None for v in out.values()):
        return out
    # `solve_building_blocks` nao devolve as aberturas filtradas: recalcula
    # o agrupamento com a MESMA funcao do motor.
    course_height_ft, _err = module._course_height_ft(catalog, None)
    if course_height_ft is None:
        return {}
    block_height_ft = course_height_ft - module._cm_to_ft(module.COURSE_JOINT_CM)
    groups = module._group_course_indices_by_opening_band(
        openings_per_wall, base_z_abs, course_height_ft, block_height_ft, num_courses)
    out = {}
    for course_indices, filtered in groups:
        for course_index in course_indices:
            out[course_index] = filtered
    return out


def _histogram(values, edges):
    """Distribuicao por faixa: [(rotulo, contagem), ...]."""
    buckets = [0] * (len(edges) + 1)
    for v in values:
        placed = False
        for i, edge in enumerate(edges):
            if v < edge:
                buckets[i] += 1
                placed = True
                break
        if not placed:
            buckets[-1] += 1
    labels = []
    prev = 0.0
    for edge in edges:
        labels.append("[{0:g},{1:g})".format(prev, edge))
        prev = edge
    labels.append(">={0:g}".format(prev))
    return list(zip(labels, buckets))


def solution_fingerprint(module, walls_to_create, course_candidates, num_courses,
                         extents=None):
    """Fingerprint CANONICO da solucao de blocos (secao 8 do CR).

    Determinado por (parede, fiada, codigo, posicao longitudinal
    arredondada a 0,1cm, rotacao arredondada a 1 grau) - NUNCA por
    ElementId, ordem da lista de candidatos ou coordenada global crua. A
    parede entra pela sua GEOMETRIA canonica (extremos ordenados,
    arredondados a 0,1cm), nao pelo indice, para que a mesma planta
    apresentada em outra ordem produza o mesmo fingerprint."""
    if extents is None:
        extents, _axis = wall_course_extents(module, walls_to_create, course_candidates, num_courses)
    wall_key = {}
    for wall_idx in range(len(walls_to_create)):
        p0, _p1, _dir, _len, _t = module._wall_axis_and_length(walls_to_create, wall_idx)
        line = walls_to_create[wall_idx][0]
        a = line.GetEndPoint(0)
        b = line.GetEndPoint(1)
        pts = sorted([
            (round(a.X * 1000.0), round(a.Y * 1000.0)),
            (round(b.X * 1000.0), round(b.Y * 1000.0)),
        ])
        wall_key[wall_idx] = "W:{0}".format(pts)
    rows = []
    for (wall_idx, course_index), items in extents.items():
        for t_start, t_end, code, _node in items:
            rows.append("{0}|c{1}|{2}|{3:.1f}|{4:.1f}".format(
                wall_key.get(wall_idx, "W?"), course_index, code,
                round(t_start, 1) + 0.0, round(t_end, 1) + 0.0))
    rows.sort()
    digest = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
    return {"sha256": digest, "rows": len(rows)}


def measure_project(project_id, project_dir, variants_per_course=None,
                    solve_kwargs=None):
    """Roda o solver real sobre `input.json` e devolve o dicionario de
    metricas (machine-readable) deste projeto."""
    module = solver_bridge.engine()
    with open(os.path.join(project_dir, "input.json")) as handle:
        input_project = json.load(handle)

    started = time.time()
    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, _notes) = solver_bridge.run_solver(
        input_project, variants_per_course=variants_per_course)
    runtime_s = time.time() - started

    tol = _tolerances(module)
    course_candidates = solve_result.get("course_candidates") or {}
    extents, _axis_cache = wall_course_extents(
        module, walls_to_create, course_candidates, num_courses)

    walls_considered = len(walls_to_create)
    walls_with_blocks = sorted(set(w for (w, _c) in extents))

    # ---- juntas e coincidencias fiada a fiada -------------------------
    counts = {"FORBIDDEN_JOINT_ALIGNMENT": 0, "DOCUMENTED_EXCEPTION": 0,
              "UNCLASSIFIED_RULE_CONFLICT": 0, "NO_ALIGNMENT": 0}
    # A qual BANDA (conjunto de aberturas ativas) cada fiada pertence. Duas
    # fiadas vizinhas de bandas DIFERENTES foram resolvidas por chamadas
    # independentes de `solve_building_blocks` e nunca se viram - separar as
    # duas populacoes e' o que distingue o que ESTE CR pode corrigir
    # (`same_band`, o par A/B) do que exigiria mexer em
    # `solve_building_blocks_all_courses` (`cross_band`, fora do escopo).
    band_of = {}
    for band_pos, band in enumerate(solve_result.get("bands") or []):
        for course_index in band.get("course_indices") or []:
            band_of[course_index] = band_pos
    forbidden_same_band = 0
    forbidden_cross_band = 0
    forbidden_by_wall = {}
    unclassified_samples = []
    staggers = []
    total_joints = 0
    comparable_pairs = 0
    for wall_idx in walls_with_blocks:
        _p0, _dir, length_cm = _wall_axis(module, walls_to_create, wall_idx)
        edges = _opening_edges_cm(module, openings_per_wall, wall_idx)
        per_course = {}
        for course_index in range(num_courses):
            items = extents.get((wall_idx, course_index))
            if not items:
                continue
            per_course[course_index] = course_joints(
                module, items, edges, length_cm, tol["max_adjacent_gap_cm"])
        for course_index, joints in per_course.items():
            total_joints += len(joints)
        for course_index in sorted(per_course):
            prev = per_course.get(course_index - 1)
            if prev is None:
                continue
            comparable_pairs += 1
            cross_band = band_of.get(course_index) != band_of.get(course_index - 1)
            for joint in per_course[course_index]:
                klass, stagger = _classify(joint, prev, tol["joint_coincidence_cm"])
                counts[klass] += 1
                if klass == "FORBIDDEN_JOINT_ALIGNMENT":
                    if cross_band:
                        forbidden_cross_band += 1
                    else:
                        forbidden_same_band += 1
                if stagger is not None:
                    staggers.append(stagger)
                if klass == "FORBIDDEN_JOINT_ALIGNMENT":
                    forbidden_by_wall[wall_idx] = forbidden_by_wall.get(wall_idx, 0) + 1
                elif klass == "UNCLASSIFIED_RULE_CONFLICT" and len(unclassified_samples) < 12:
                    unclassified_samples.append(
                        {"wall_idx": wall_idx, "course": course_index,
                         "x_cm": round(joint["x_cm"], 2)})

    # ---- inventario de pecas -----------------------------------------
    # As aberturas ATIVAS variam por fiada (uma janela so' e' vazia na faixa
    # vertical do seu vao - secao 4). Medir "bloco dentro de abertura" com a
    # lista COMPLETA contaria como erro toda peca abaixo do peitoril, que e'
    # exatamente a regra oposta. Usa o MESMO agrupamento do solver.
    openings_by_course = _openings_active_by_course(
        module, openings_per_wall, solve_result, num_courses, catalog, base_z_ft)
    by_code = {}
    blocks_inside_opening = 0
    for (wall_idx, course_index), items in extents.items():
        active = openings_by_course.get(course_index) or openings_per_wall
        intervals = _opening_intervals_cm(module, active, wall_idx)
        for t_start, t_end, code, _node in items:
            by_code[code] = by_code.get(code, 0) + 1
            for a_cm, b_cm in intervals:
                lo, hi = min(a_cm, b_cm), max(a_cm, b_cm)
                overlap = min(t_end, hi) - max(t_start, lo)
                if overlap > 0.5:
                    blocks_inside_opening += 1
                    break

    # Compensadores/pastilhas em sequencia: pela FUNCAO DO MOTOR
    # (`_find_consecutive_compensators`, a mesma que `validate_wall_
    # modulation` usa na regra #2) - nunca por uma copia da regra aqui.
    consecutive_comp = 0
    comp_runs_by_len = {}
    by_wall_cands = {}
    for course_index in range(num_courses):
        for cand in course_candidates.get(course_index) or []:
            if cand.get("wall_idx") is None:
                continue
            copia = dict(cand)
            copia["course"] = course_index
            by_wall_cands.setdefault(cand["wall_idx"], []).append(copia)
    for wall_idx, cands in by_wall_cands.items():
        for run in module._find_consecutive_compensators(
                wall_idx, walls_to_create, cands, catalog):
            consecutive_comp += 1
            key = str(len(run["codes"]))
            comp_runs_by_len[key] = comp_runs_by_len.get(key, 0) + 1

    # ---- auditoria oficial (regressao L/T/X, faixas, B19) -------------
    audits = module.audit_all_walls_bond_quality(
        walls_to_create, course_candidates, catalog, num_courses,
        openings_per_wall=openings_per_wall, nodes=nodes,
        end_to_node=None)
    audit_problems = {}
    walls_audit_failed = 0
    for _wall_idx, audit in audits.items():
        if not audit["ok"]:
            walls_audit_failed += 1
        for problem in audit["problems"]:
            kind = problem.split(":")[0]
            audit_problems[kind] = audit_problems.get(kind, 0) + 1

    intersection_failures = solve_result.get("intersection_failures") or []
    failures_by_kind = {}
    for failure in intersection_failures:
        # `solve_all_intersections` devolve (node_index, motivo) - tupla,
        # nao dict (ver wall_stepper.py).
        kind = failure[1] if isinstance(failure, (tuple, list)) and len(failure) > 1 else failure
        failures_by_kind[str(kind)] = failures_by_kind.get(str(kind), 0) + 1

    fingerprint = solution_fingerprint(
        module, walls_to_create, course_candidates, num_courses, extents=extents)

    return {
        "project_id": project_id,
        "runtime_s": round(runtime_s, 3),
        "tolerances_cm": tol,
        "walls_considered": walls_considered,
        "walls_with_blocks": len(walls_with_blocks),
        "walls_without_blocks": walls_considered - len(walls_with_blocks),
        "num_courses": num_courses,
        "wall_course_pairs_with_blocks": len(extents),
        "comparable_course_pairs": comparable_pairs,
        "internal_joints_total": total_joints,
        "joint_classes": counts,
        "forbidden_by_band": {"same_band": forbidden_same_band,
                              "cross_band": forbidden_cross_band},
        "forbidden_walls": len(forbidden_by_wall),
        "forbidden_top_walls": sorted(
            forbidden_by_wall.items(), key=lambda kv: (-kv[1], kv[0]))[:10],
        "unclassified_samples": unclassified_samples,
        "stagger": {
            "count": len(staggers),
            "min_cm": round(min(staggers), 3) if staggers else None,
            "mean_cm": round(sum(staggers) / len(staggers), 3) if staggers else None,
            "histogram": _histogram(staggers, [1.0, 5.0, 10.0, 15.0, 20.0, 40.0]),
        },
        "blocks_by_code": dict(sorted(by_code.items())),
        "blocks_total": sum(by_code.values()),
        "consecutive_compensator_pairs": consecutive_comp,
        "consecutive_compensator_runs_by_len": dict(sorted(comp_runs_by_len.items())),
        "blocks_inside_opening": blocks_inside_opening,
        "alignment_conflicts": len(solve_result.get("alignment_conflicts") or []),
        "non_modular": len(solve_result.get("non_modular") or []),
        "collisions": len(solve_result.get("collisions") or []),
        "door_void_violations": len(solve_result.get("door_void_violations") or []),
        "jamb_exceptions": len(solve_result.get("jamb_exceptions") or []),
        "intersection_failures": len(intersection_failures),
        "intersection_failures_by_kind": failures_by_kind,
        "walls_audit_failed": walls_audit_failed,
        "audit_problems": audit_problems,
        "fingerprint": fingerprint,
    }


PROJECT_IDS = ("piloto_sintetico_2x2", "torre_easy_lo_r00_tp1", "torre_easy_lo_r00_tgd")


def projects_root():
    return os.path.join(_BENCH, "projects")


def measure_all(project_ids=PROJECT_IDS, variants_per_course=None):
    root = projects_root()
    out = {"projects": {}, "totals": {}}
    for project_id in project_ids:
        directory = os.path.join(root, project_id)
        if not os.path.isdir(directory):
            continue
        out["projects"][project_id] = measure_project(
            project_id, directory, variants_per_course=variants_per_course)
    totals = {}
    for key in ("walls_considered", "walls_with_blocks", "walls_without_blocks",
                "internal_joints_total", "blocks_total", "consecutive_compensator_pairs",
                "blocks_inside_opening", "alignment_conflicts", "non_modular",
                "collisions", "door_void_violations", "walls_audit_failed",
                "comparable_course_pairs", "intersection_failures"):
        totals[key] = sum(p[key] for p in out["projects"].values())
    classes = {}
    for project in out["projects"].values():
        for name, value in project["joint_classes"].items():
            classes[name] = classes.get(name, 0) + value
    totals["joint_classes"] = classes
    bandas = {"same_band": 0, "cross_band": 0}
    for project in out["projects"].values():
        for name, value in (project.get("forbidden_by_band") or {}).items():
            bandas[name] = bandas.get(name, 0) + value
    totals["forbidden_by_band"] = bandas
    codes = {}
    for project in out["projects"].values():
        for code, value in project["blocks_by_code"].items():
            codes[code] = codes.get(code, 0) + value
    totals["blocks_by_code"] = dict(sorted(codes.items()))
    totals["runtime_s"] = round(sum(p["runtime_s"] for p in out["projects"].values()), 3)
    out["totals"] = totals
    return out
