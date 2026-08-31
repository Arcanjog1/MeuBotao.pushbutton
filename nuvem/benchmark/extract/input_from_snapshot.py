# -*- coding: utf-8 -*-
"""`wall_modeling_snapshot.json` -> `input.json` (schema do `model.py`).

Fecha o elo que faltava da ETAPA 2B (ver `nuvem/benchmark/README.md`, secao
"Wall Modeling (Etapa 2A)", onde estava anotado como "proxima etapa"):

    input_real.json
       -> wall_modeling_bridge.run_wall_modeling()     (FASE A, ja existia)
          -> wall_modeling_snapshot.json
             -> ESTE MODULO                            (FASE B, o elo novo)
                -> input.json
                   -> solver_bridge.run_solver()       (SOLVER REAL, intocado)
                      -> result.json

Funcao PURA - roda em CPython, nao toca no Revit, nao abre Transaction, nao
reimplementa nenhuma regra geometrica. Os eixos, os encontros e a atribuicao
abertura->parede JA foram decididos pelo motor real na FASE A; aqui so' se
troca o formato.

A ORDEM das paredes do snapshot e' preservada: `walls[i]` sai de
`snapshot["walls"][i]`. `solver_bridge.plan_from_input` depende disso -
`openings_per_wall` e' indexado por POSICAO, e reordenar aqui faria cada
abertura cair na parede errada.

`walls_already_extended: true` e' propagado do snapshot. As pontas ja foram
esticadas por `extend_wall_ends_to_junctions` na FASE A; sem a flag,
`plan_from_input` esticaria de novo e empurraria cada ponta mais uma
espessura de parede.

CATALOGO: o snapshot nao tem catalogo (a FASE A so' decide GEOMETRIA de
parede - eixos, nos, vaos - nunca pecas). Quem chama passa o catalogo
explicitamente; `metadata["catalog_source"]` registra de onde ele veio, para
o relatorio nunca dar a impressao de que o catalogo foi medido no projeto
cru quando na verdade veio do gabarito.
"""

from .. import model

# Uma abertura cujo peitoril coincide com a base da parede e' PORTA; acima
# dela, JANELA. E' a mesma leitura que `reconstruct.py` faz do vazio entre
# blocos - so' um rotulo para o relatorio, nao entra em nenhuma decisao
# geometrica do solver.
DOOR_SILL_TOLERANCE_CM = 1.0


def _kind_for(sill_cm, base_z_cm):
    return "door" if abs(float(sill_cm) - float(base_z_cm)) <= DOOR_SILL_TOLERANCE_CM else "window"


def _openings_by_wall_index(snapshot, base_z_cm):
    """`snapshot["openings_per_wall"]` -> `{wall_index: [make_opening(...)]}`.

    Os intervalos aqui ja sao os do resultado FINAL da FASE A (depois de
    `_merge_opening_matches`) - nao ha' nada a recalcular."""
    by_index = {}
    for entry in snapshot.get("openings_per_wall") or []:
        wall_index = entry.get("wall_index")
        if wall_index is None:
            continue
        source = entry.get("source_opening_key")
        if isinstance(source, list):
            source = ",".join(str(s) for s in source) or None
        by_index.setdefault(wall_index, []).append(model.make_opening(
            kind=_kind_for(entry["sill_cm"], base_z_cm),
            t_start_cm=entry["t_start_cm"],
            t_end_cm=entry["t_end_cm"],
            sill_cm=entry["sill_cm"],
            head_cm=entry["head_cm"],
            source_element_id=source,
            # "measured": veio de uma familia de abertura REAL do documento
            # cru (Largura_abertura/Altura_abertura/Peitoril), nao do vazio
            # entre blocos ja colocados - e' exatamente a diferenca que este
            # pipeline existe para eliminar.
            confidence="measured",
        ))
    return by_index


def _junctions_by_wall_index(snapshot):
    """Nos do grafo L/T/X reagrupados por parede, so' para o `input.json`
    ficar legivel/auditavel. `plan_from_input` NAO le' isto - ele reconstroi
    o grafo com `build_wall_graph` a partir dos eixos."""
    nodes = snapshot.get("nodes") or []
    by_index = {}
    for node_index, node in enumerate(nodes):
        for wall_idx, end_index in (node.get("arms") or []):
            by_index.setdefault(wall_idx, []).append({
                "type": node.get("kind"),
                "point_cm": node.get("point_cm"),
                "node_index": node_index,
                "at_end": bool(end_index),
            })
    return by_index


def build_input(snapshot, catalog, project_id=None, metadata=None,
                catalog_source=None):
    """Snapshot da FASE A + catalogo -> projeto `input` pronto para
    `solver_bridge.run_solver`."""
    settings_in = dict(snapshot.get("settings") or {})
    base_z_cm = float(settings_in.get("base_z_cm") or 0.0)
    wall_height_cm = settings_in.get("wall_height_cm")

    openings_by_index = _openings_by_wall_index(snapshot, base_z_cm)
    junctions_by_index = _junctions_by_wall_index(snapshot)

    walls = []
    for index, wall in enumerate(snapshot.get("walls") or []):
        walls.append(model.make_wall(
            "W{0:03d}".format(index + 1),
            wall["start_cm"], wall["end_cm"], wall["thickness_cm"],
            base_z_cm=base_z_cm,
            height_cm=wall_height_cm,
            openings=openings_by_index.get(index) or [],
            junctions=junctions_by_index.get(index) or [],
            rows=[],  # o input NUNCA tem peca colocada - e' o problema, nao a solucao
        ))

    settings = {
        "base_z_cm": base_z_cm,
        "course_step_cm": settings_in.get("course_step_cm"),
        "num_courses": settings_in.get("num_courses"),
        "expected_rows": settings_in.get("num_courses"),
        # Propagada do snapshot, nunca assumida - ver o cabecalho do modulo.
        "walls_already_extended": bool(settings_in.get("walls_already_extended")),
    }

    project = model.make_project(
        project_id or snapshot.get("project_id"), "input",
        walls=walls, settings=settings, catalog=dict(catalog or {}),
        metadata=dict(metadata or {}),
    )
    project["metadata"].update({
        "derived_from": "wall_modeling_snapshot.json",
        "source_kind": "projeto CRU (CAD + aberturas), passado pelo Wall "
                       "Modeling headless - NENHUM bloco do gabarito foi lido",
        "wall_modeling_engine_sha256": snapshot.get("wall_modeling_engine_sha256"),
        "setup_frozen": snapshot.get("setup_frozen"),
        "walls_total": len(walls),
        "openings_total": sum(len(w["openings"]) for w in walls),
        "openings_source": "revit_family_params (documento INPUT) via FASE A",
        "walls_source": "wall_modeling_bridge (linhas do CAD do documento INPUT)",
        "catalog_source": catalog_source,
    })
    return project
