# -*- coding: utf-8 -*-
"""Resultado do SOLVER -> o mesmo JSON do gabarito.

Este e' o lado "resultado gerado" do ciclo. Ele nao roda o solver (isso e'
`benchmark/runner.py`): recebe o que `solve_building_blocks_all_courses`
devolveu, mais a planta que entrou, e traduz para `model.py`.

DUAS COISAS QUE ESTE MODULO NAO FAZ, de proposito:

1. **Nao valida nada.** Se o solver deixou uma parede vazia, a parede sai
   daqui vazia - e' o `validate_wall_coverage` que tem que gritar. Um
   extrator que "conserta" o que extrai destroi a medicao.
2. **Nao reordena nem deduplica pecas.** O que o solver decidiu e' o que
   aparece.

Precisa dos objetos vivos do motor (XYZ do Revit ou os dubles de
`tests/revit_stubs.py`) porque `walls_to_create`/`candidates` carregam
geometria em pes. A conversao para cm acontece toda aqui.
"""

from .. import model

FEET_TO_CM = 30.48

# `placement_reason` do solver -> papel do benchmark. Nomes vindos de
# `core/engine/wall_stepper.py` (ver `_make_block_candidate`).
PLACEMENT_REASON_TO_ROLE = {
    "L_CORNER": model.ROLE_L_BINDING,
    "L_CORNER_DEGRADED": model.ROLE_L_BINDING,
    "CORNER_DEGRADED": model.ROLE_L_BINDING,
    "T_INTERSECTION": model.ROLE_T_BINDING,
    "T_INTERSECTION_MAIN": model.ROLE_T_BINDING,
    "T_INTERSECTION_INCOMING": model.ROLE_T_BINDING,
    "T_INTERSECTION_INCOMING_DEGRADED": model.ROLE_T_BINDING,
    "T_INTERSECTION_DEGRADED_L": model.ROLE_T_BINDING,
    "X_INTERSECTION": model.ROLE_CROSS_BINDING,
    "X_INTERSECTION_DEGRADED": model.ROLE_CROSS_BINDING,
    "STANDARD_FILL": model.ROLE_STANDARD,
    "STRAIGHT_CONTINUATION": model.ROLE_STANDARD,
    "WALL_START": model.ROLE_STANDARD,
    "WALL_END": model.ROLE_STANDARD,
    "FREE_END": model.ROLE_STANDARD,
    "OPENING_LEFT_JAMB": model.ROLE_OPENING_ADJUSTMENT,
    "OPENING_RIGHT_JAMB": model.ROLE_OPENING_ADJUSTMENT,
    "OPENING_LO": model.ROLE_OPENING_ADJUSTMENT,
    "OPENING_HI": model.ROLE_OPENING_ADJUSTMENT,
    "OPENING_REPAIR_FILL": model.ROLE_OPENING_ADJUSTMENT,
    "MIDSPAN_LO": model.ROLE_STANDARD,
    "MIDSPAN_HI": model.ROLE_STANDARD,
}

# `kind` do no' do grafo -> tipo de encontro do benchmark.
NODE_KIND_TO_JUNCTION = {
    "L_CORNER": model.JUNCTION_L,
    "T_INTERSECTION": model.JUNCTION_T,
    "X_INTERSECTION": model.JUNCTION_X,
    "FREE_END": model.JUNCTION_FREE_END,
    "STRAIGHT_CONTINUATION": model.JUNCTION_COLLINEAR,
}


def _cm(value_ft):
    return float(value_ft) * FEET_TO_CM


def block_role(candidate, catalog):
    """Papel de UMA peca. A ordem importa: o que a peca E' (compensador,
    meio-bloco) vence o que ela esta' FAZENDO (preenchimento comum), mas
    perde para amarracao de encontro - uma amarracao feita com C09 num T
    sem espaco (regra 18.9) continua sendo amarracao."""
    reason = candidate.get("placement_reason")
    role = PLACEMENT_REASON_TO_ROLE.get(reason)
    if role in model.BINDING_ROLES:
        return role
    code = candidate.get("logical_code")
    entry = (catalog or {}).get(code) or {}
    if entry.get("is_compensator"):
        return model.ROLE_COMPENSATOR
    if code == "B19":
        return model.ROLE_HALF_BLOCK
    return role or model.ROLE_UNKNOWN


def _wall_geometry_cm(walls_to_create, wall_idx):
    line, thickness_ft, _locks = walls_to_create[wall_idx]
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    start = (_cm(p0.X), _cm(p0.Y))
    end = (_cm(p1.X), _cm(p1.Y))
    return start, end, _cm(thickness_ft)


def _junctions_for_wall(wall_idx, nodes, walls_to_create):
    """Encontros DESTA parede, ja' com a coordenada no eixo dela - e' assim
    que o validador de amarracao consulta."""
    start, end, _thickness = _wall_geometry_cm(walls_to_create, wall_idx)
    direction, length = model.direction_of(start, end)
    result = []
    for node_index, node in enumerate(nodes or []):
        arms = node.get("arms") or []
        if not any(arm[0] == wall_idx for arm in arms):
            continue
        point = node.get("point")
        if point is None:
            continue
        t_cm, _s = model.axial_coordinates((_cm(point.X), _cm(point.Y)), start, direction)
        result.append({
            "node_index": node_index,
            "type": NODE_KIND_TO_JUNCTION.get(node.get("kind"), node.get("kind")),
            "kind_raw": node.get("kind"),
            "t_cm": round(t_cm, 3),
            "point_cm": [round(_cm(point.X), 3), round(_cm(point.Y), 3)],
            "neighbors": sorted(set(arm[0] for arm in arms if arm[0] != wall_idx)),
            "arms": [list(arm) for arm in arms],
            # Encontro no MEIO do eixo (T recebido) x na ponta.
            "at_end": bool(t_cm <= 1.0 or t_cm >= length - 1.0),
        })
    result.sort(key=lambda item: item["t_cm"])
    return result


def _openings_for_wall(wall_idx, openings_per_wall, base_z_cm):
    """`openings_per_wall[i]` e' `[(t_lo_ft, t_hi_ft, sill_z_ft, head_z_ft)]`
    - coordenadas JA no eixo da parede (o solver usa assim)."""
    result = []
    for opening in (openings_per_wall or [None] * (wall_idx + 1))[wall_idx] or []:
        t_lo, t_hi, sill, head = opening[0], opening[1], opening[2], opening[3]
        sill_cm = _cm(sill)
        kind = (model.OPENING_DOOR
                if sill_cm <= base_z_cm + 1.0
                else model.OPENING_WINDOW)
        result.append(model.make_opening(
            kind, _cm(t_lo), _cm(t_hi), sill_cm, _cm(head),
            confidence="measured",
        ))
    return result


def catalog_to_benchmark(catalog):
    result = {}
    for code, entry in (catalog or {}).items():
        result[code] = {
            "code": code,
            "length_cm": entry.get("length_cm"),
            "height_cm": entry.get("height_cm"),
            "width_cm": entry.get("width_cm"),
            "is_special_bond": bool(entry.get("is_special_bond")),
            "is_compensator": bool(entry.get("is_compensator")),
        }
    return result


def project_from_solver(project_id, solve_result, walls_to_create, nodes,
                        openings_per_wall, catalog, base_z_abs_ft, num_courses,
                        course_height_ft=None, metadata=None):
    """Monta o projeto do benchmark a partir de UMA execucao do solver.

    `solve_result` e' o dict de `solve_building_blocks_all_courses` - o que
    interessa aqui e' `course_candidates` (peca por FIADA FISICA), nunca
    `candidates` agregado: aquele mistura variantes A/B que nunca coexistem
    no modelo, e contar prisma sobre ele daria erro fantasma (a mesma
    armadilha registrada na secao 17.1 do REGRAS_MODULACAO_BLOCOS.md)."""
    base_z_cm = _cm(base_z_abs_ft)
    course_candidates = solve_result.get("course_candidates") or {}
    if course_height_ft is None:
        heights = [entry.get("height_cm") for entry in (catalog or {}).values()
                   if entry.get("height_cm")]
        course_step_cm = (min(heights) + 1.0) if heights else 20.0
    else:
        course_step_cm = _cm(course_height_ft)

    walls = []
    for wall_idx in range(len(walls_to_create)):
        start, end, thickness_cm = _wall_geometry_cm(walls_to_create, wall_idx)
        direction, length_cm = model.direction_of(start, end)
        rows = []
        for course_index in range(num_courses):
            elevation_cm = base_z_cm + course_index * course_step_cm
            blocks = []
            for candidate in course_candidates.get(course_index) or []:
                if candidate.get("wall_idx") != wall_idx:
                    continue
                origin = candidate["origin_world"]
                center = (_cm(origin.X), _cm(origin.Y))
                t_center, _s = model.axial_coordinates(center, start, direction)
                half = float(candidate["length_cm"]) / 2.0
                blocks.append(model.make_block(
                    code=candidate["logical_code"],
                    length_cm=candidate["length_cm"],
                    center_cm=center,
                    z_cm=elevation_cm,
                    rotation_deg=candidate.get("rotation_deg") or 0.0,
                    t_start_cm=t_center - half,
                    t_end_cm=t_center + half,
                    role=block_role(candidate, catalog),
                    width_cm=candidate.get("width_cm"),
                    height_cm=(catalog.get(candidate["logical_code"]) or {}).get("height_cm"),
                    mirrored=bool(candidate.get("mirrored")),
                    wall_id=None,
                    secondary_wall_id=candidate.get("secondary_wall_idx"),
                    row=course_index,
                    placement_reason=candidate.get("placement_reason"),
                ))
            rows.append(model.make_row(course_index, elevation_cm, blocks))
        walls.append(model.make_wall(
            "W{0:03d}".format(wall_idx + 1), start, end, thickness_cm,
            base_z_cm=base_z_cm,
            height_cm=num_courses * course_step_cm,
            openings=_openings_for_wall(wall_idx, openings_per_wall, base_z_cm),
            junctions=_junctions_for_wall(wall_idx, nodes, walls_to_create),
            rows=rows,
        ))

    project = model.make_project(
        project_id, "solver", walls=walls,
        settings={
            "base_z_cm": round(base_z_cm, 3),
            "course_step_cm": round(course_step_cm, 3),
            "expected_rows": num_courses,
            "num_courses": num_courses,
        },
        catalog=catalog_to_benchmark(catalog),
        metadata=dict(metadata or {}),
    )
    # Sinais do proprio solver que o benchmark guarda para o relatorio -
    # nao viram achado (o validador mede de novo, por geometria), mas
    # ajudam a investigar causa.
    project["metadata"]["solver_signals"] = {
        "collisions": len(solve_result.get("collisions") or []),
        "non_modular": len(solve_result.get("non_modular") or []),
        "intersection_failures": len(solve_result.get("intersection_failures") or []),
        "door_void_violations": len(solve_result.get("door_void_violations") or []),
        "bond_audits_failing": sum(
            1 for audit in (solve_result.get("wall_bond_audits") or {}).values()
            if not audit.get("ok")),
        "error": solve_result.get("error"),
    }
    return model.assign_ids(project)


def input_from_plan(project_id, walls_to_create, nodes, openings_per_wall,
                    catalog, base_z_abs_ft, num_courses, metadata=None):
    """`input.json` (item 6): o PROBLEMA, sem nenhuma peca.

    Guardar o input a parte e' o que permite reproduzir a mesma execucao
    amanha sem depender de reabrir o .rvt nem de interpretacao humana."""
    project = project_from_solver(
        project_id, {"course_candidates": {}}, walls_to_create, nodes,
        openings_per_wall, catalog, base_z_abs_ft, num_courses,
        metadata=metadata,
    )
    project["source"] = "input"
    for wall in project["walls"]:
        wall["rows"] = []
    project["metadata"].pop("solver_signals", None)
    return project
