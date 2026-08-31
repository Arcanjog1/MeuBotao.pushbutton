# -*- coding: utf-8 -*-
"""`wall_modeling_bridge.run_wall_modeling()` -> `wall_modeling_snapshot.json`.

FASE A do benchmark de Wall Modeling (ver `nuvem/benchmark/README.md` e o
cabecalho de `wall_modeling_bridge.py`):

    input_real -> wall_modeling_bridge -> ESTE MODULO -> snapshot.json

O snapshot e' JSON PURO e DETERMINISTICO: dois `run_wall_modeling()` com o
mesmo `input_real` produzem o mesmo snapshot byte a byte (exceto
`generated_at`, que fica isolado em `metadata` e nunca entra no
`engine_fingerprint`).

Reutiliza `model.wall_stable_key`/`model.canonical_segment` - NAO reimplementa
uma segunda nocao de identidade de parede.

`walls_already_extended: true` em `settings` e' OBRIGATORIO: os eixos aqui ja
passaram por `extend_wall_ends_to_junctions` no bridge. Uma etapa futura que
alimente isto no `solver_bridge.plan_from_input` DEVE preservar essa flag -
`solver_bridge.py` ja respeita ela (ver `plan_from_input`), o que evita
esticar a mesma ponta duas vezes.
"""

import hashlib
import json

from .. import model

SCHEMA_VERSION = 1


def _cm(module, value_ft):
    return float(value_ft) * 100.0 / module.FEET_PER_METER


def _round(value, places=3):
    return round(float(value), places)


def _engine_fingerprint(module):
    """sha256 do arquivo fonte do motor carregado (`core/wall_modeling.py`).
    Serve para a Etapa 2A confirmar que nenhuma alteracao no core aconteceu
    durante a implementacao (item 15 do pedido) - e para qualquer sessao
    futura notar, so' de olhar o snapshot, que o motor usado era outro."""
    path = getattr(module, "__file__", None)
    if not path:
        return None
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _wall_entries(bridge_result):
    module = bridge_result["module"]
    walls_to_create = bridge_result["walls_to_create"]
    walls_before = bridge_result["walls_before_extension"]
    entries = []
    for index, (centerline, thickness_ft, locked_ends) in enumerate(walls_to_create):
        p0 = centerline.GetEndPoint(0)
        p1 = centerline.GetEndPoint(1)
        start_cm = [_round(_cm(module, p0.X)), _round(_cm(module, p0.Y))]
        end_cm = [_round(_cm(module, p1.X)), _round(_cm(module, p1.Y))]
        thickness_cm = _round(_cm(module, thickness_ft))
        direction, length_cm = model.direction_of(start_cm, end_cm)

        before_line, _before_thickness, _before_locks = walls_before[index]
        bp0 = before_line.GetEndPoint(0)
        bp1 = before_line.GetEndPoint(1)

        entries.append({
            "index": index,
            "key": model.wall_stable_key(start_cm, end_cm, thickness_cm),
            "start_cm": start_cm,
            "end_cm": end_cm,
            "thickness_cm": thickness_cm,
            "length_cm": _round(length_cm),
            "angle_deg": _round(model.angle_deg(direction)),
            "locked_ends": [bool(locked_ends[0]), bool(locked_ends[1])],
            # Geometria ANTES de extend_wall_ends_to_junctions (item 3/4 do
            # pedido) - o unico ponto do pipeline em que o eixo tem
            # exatamente o comprimento que as duas linhas do CAD definiram.
            "before_extension": {
                "start_cm": [_round(_cm(module, bp0.X)), _round(_cm(module, bp0.Y))],
                "end_cm": [_round(_cm(module, bp1.X)), _round(_cm(module, bp1.Y))],
            },
        })
    return entries


def _node_entries(bridge_result, wall_keys):
    module = bridge_result["module"]
    entries = []
    for node in bridge_result["wall_graph_nodes"]:
        point = node.get("point")
        crossing = node.get("crossing_walls")
        entry = {
            "point_cm": (
                [_round(_cm(module, point.X)), _round(_cm(module, point.Y))]
                if point is not None else None
            ),
            "kind": node.get("kind"),
            "arms": [[int(w), int(e)] for w, e in (node.get("arms") or [])],
            "main_wall_idx": node.get("main_wall_idx"),
            "incoming_wall_idx": node.get("incoming_wall_idx"),
            "neighbor_wall_idx": node.get("neighbor_wall_idx"),
            "neighbor_end_index": node.get("neighbor_end_index"),
            "crossing_walls": (
                [int(crossing[0]), int(crossing[1])] if crossing is not None else None
            ),
        }
        entries.append(entry)
    return entries


def _end_to_node_entries(bridge_result):
    # `end_to_node` e' `{(wall_idx, end_index): node_index}` - chave tupla,
    # que JSON nao representa. Serializado como lista de registros; a ordem
    # e' estavel (por wall_idx, end_index) para o snapshot ser deterministico.
    end_to_node = bridge_result["wall_end_to_node"]
    keys = sorted(end_to_node.keys())
    return [
        {"wall_idx": int(wall_idx), "end_index": int(end_index),
         "node_index": int(end_to_node[(wall_idx, end_index)])}
        for wall_idx, end_index in keys
    ]


def _openings_per_wall_entries(bridge_result, wall_entries):
    module = bridge_result["module"]
    assignments = (bridge_result["diagnostics"]["openings"].get("assignments") or [])
    # `assignments` guarda o casamento opening ORIGINAL -> parede + intervalo
    # ANTES de `_merge_opening_matches`. Usado so' para reconstruir
    # `source_opening_key` no intervalo (possivelmente ja mesclado) do
    # resultado final - nunca para recalcular geometria.
    by_wall = {}
    for record in assignments:
        by_wall.setdefault(record["wall_idx"], []).append(record)

    result = []
    for wall_idx, intervals in enumerate(bridge_result["openings_per_wall"]):
        wall_key = wall_entries[wall_idx]["key"] if wall_idx < len(wall_entries) else None
        candidates = by_wall.get(wall_idx) or []
        for t_lo_ft, t_hi_ft, sill_ft, head_ft in intervals:
            t_start_cm = _round(_cm(module, t_lo_ft))
            t_end_cm = _round(_cm(module, t_hi_ft))
            sill_cm = _round(_cm(module, sill_ft))
            head_cm = _round(_cm(module, head_ft))
            source_keys = sorted(set(
                str(record["op"].get("element_id"))
                for record in candidates
                if record["t_lo"] >= t_lo_ft - 1e-6 and record["t_hi"] <= t_hi_ft + 1e-6
                and record["op"].get("element_id") is not None
            ))
            result.append({
                "wall_index": wall_idx,
                "wall_key": wall_key,
                "t_start_cm": t_start_cm,
                "t_end_cm": t_end_cm,
                "sill_cm": sill_cm,
                "head_cm": head_cm,
                "source_opening_key": (
                    source_keys[0] if len(source_keys) == 1
                    else (source_keys or None)
                ),
            })
    return result


def build_snapshot(bridge_result, project_id, metadata=None):
    """`wall_modeling_bridge.run_wall_modeling()` -> dict pronto para
    `save()`. Puro - nao toca disco."""
    module = bridge_result["module"]
    wall_entries = _wall_entries(bridge_result)
    wall_keys_by_index = [w["key"] for w in wall_entries]

    settings = dict(bridge_result["setup_frozen"])
    settings["walls_already_extended"] = True

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "source": "wall_modeling",
        "setup_frozen": bridge_result["setup_frozen"],
        "engine_fingerprint": _engine_fingerprint(module),
        "walls": wall_entries,
        "nodes": _node_entries(bridge_result, wall_keys_by_index),
        "end_to_node": _end_to_node_entries(bridge_result),
        "openings_per_wall": _openings_per_wall_entries(bridge_result, wall_entries),
        "unused_lines": bridge_result["unused_lines"],
        "diagnostics": bridge_result["diagnostics"],
        "settings": settings,
        "metadata": dict(metadata or {}),
    }
    return snapshot


def save(snapshot, path):
    """Grava o snapshot - uma linha por parede/no', igual a `model.save`,
    para o `git diff` ficar util (mexer numa parede muda uma linha, nao o
    arquivo inteiro)."""
    head = dict((k, v) for k, v in snapshot.items()
               if k not in ("walls", "nodes", "openings_per_wall", "unused_lines"))
    parts = [json.dumps(head, ensure_ascii=False, indent=1, sort_keys=True)[:-2]]
    for key in ("walls", "nodes", "openings_per_wall", "unused_lines"):
        items = snapshot.get(key) or []
        parts.append(',\n "{0}": [\n'.format(key))
        parts.append(",\n".join(
            "  " + json.dumps(item, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            for item in items
        ))
        parts.append("\n ]")
    parts.append("\n}\n")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(parts))
    return path


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        snapshot = json.load(handle)
    version = snapshot.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(
            "wall_modeling_snapshot schema_version {0} em {1}; este codigo "
            "le' {2}. Reextraia em vez de editar o JSON a mao.".format(
                version, path, SCHEMA_VERSION)
        )
    return snapshot


def to_solver_input(snapshot, project_id=None):
    """`wall_modeling_snapshot` -> `input.json` no schema de `model.py`
    (o mesmo que `solver_bridge.run_solver` consome), com
    `settings.walls_already_extended = True` OBRIGATORIO - as paredes do
    snapshot ja passaram por `extend_wall_ends_to_junctions` no bridge;
    sem essa flag, `solver_bridge.plan_from_input` esticaria as pontas de
    novo (ver item 7 do pedido / teste `test_walls_already_extended_...`).

    NAO roda o solver - so' monta o formato de entrada dele. Reutiliza
    `model.make_wall`/`model.make_opening`, nunca uma segunda conversao."""
    openings_by_wall = {}
    for entry in snapshot.get("openings_per_wall") or []:
        openings_by_wall.setdefault(entry["wall_index"], []).append(entry)

    walls = []
    for wall in snapshot.get("walls") or []:
        wall_openings = [
            model.make_opening(
                model.OPENING_DOOR if o["sill_cm"] <= (snapshot["settings"].get("base_z_cm") or 0.0) + 1.0
                else model.OPENING_WINDOW,
                o["t_start_cm"], o["t_end_cm"], o["sill_cm"], o["head_cm"],
                source_element_id=o.get("source_opening_key"),
            )
            for o in sorted(openings_by_wall.get(wall["index"]) or [],
                            key=lambda o: o["t_start_cm"])
        ]
        walls.append(model.make_wall(
            "W{0:03d}".format(wall["index"] + 1),
            wall["start_cm"], wall["end_cm"], wall["thickness_cm"],
            base_z_cm=snapshot["settings"].get("base_z_cm") or 0.0,
            height_cm=snapshot["settings"].get("wall_height_cm"),
            openings=wall_openings,
        ))

    project = model.make_project(
        project_id or snapshot.get("project_id"), "input",
        walls=walls,
        settings={
            "base_z_cm": snapshot["settings"].get("base_z_cm") or 0.0,
            "wall_height_cm": snapshot["settings"].get("wall_height_cm"),
            "num_courses": snapshot["settings"].get("num_courses"),
            "expected_rows": snapshot["settings"].get("num_courses"),
            # OBRIGATORIO - ver docstring desta funcao.
            "walls_already_extended": True,
        },
        metadata={"derived_from": "wall_modeling_snapshot",
                  "engine_fingerprint": snapshot.get("engine_fingerprint")},
    )
    return model.assign_ids(project)
