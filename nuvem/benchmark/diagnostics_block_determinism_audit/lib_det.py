# -*- coding: utf-8 -*-
"""Biblioteca da auditoria INDEPENDENTE de determinismo (CONTA 2 —
`docs/BLOCK_DETERMINISM_AUDIT.md`).

Contrato desta pasta (`nuvem/benchmark/diagnostics_block_determinism_audit/`):
  - SÓ LEITURA do motor (`core/wall_modeling.py`, `core/engine/**`) e da
    infraestrutura de benchmark já existente (`nuvem/benchmark/*`, incluindo
    `solver_bridge`/`runner`, o mesmo caminho headless que
    `tests/solver_bench.py` usa) — nenhuma linha de produção é alterada,
    nenhum arquivo fora desta pasta (e de `docs/BLOCK_DETERMINISM_AUDIT.md`)
    é escrito por nenhum script daqui.
  - Não lê nem depende de `claude/block-determinism-graph` (a branch da
    CONTA 1) — esta auditoria nasce independente (missão, item 17).
  - Não usa `wall_idx` como identidade entre execuções: `wall_idx` muda com
    a permutação de entrada, então toda comparação entre variantes usa
    identidade GEOMÉTRICA (`wall_geom_key`, `node_geom_key`, `piece_geom_key`
    — missão, item 7).
  - Métrica que não existe fora do Revit real é marcada literalmente como
    `"NOT_HEADLESS_OBSERVABLE"` — nunca inventada.
"""

import os
import sys
import json
import time
import math
import hashlib
import copy

_HERE = os.path.dirname(os.path.abspath(__file__))
# nuvem/benchmark/diagnostics_block_determinism_audit/ -> nuvem/benchmark/ -> nuvem/
_NUVEM_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _NUVEM_DIR not in sys.path:
    sys.path.insert(0, _NUVEM_DIR)

from benchmark import solver_bridge  # noqa: E402
from benchmark import runner as bench_runner  # noqa: E402

FT_TO_CM = 100.0 * 0.3048  # mesma convenção de core/wall_modeling.py

PRIMARY_PROJECT_ID = "torre_easy_lo_r00_tgd"

# Tolerância de arredondamento para chaves geométricas (mm) — grande o
# bastante para absorver ruído de ponto flutuante entre ordens de execução
# diferentes, pequeno o bastante para não confundir dois nós/paredes reais.
GEOM_ROUND_CM = 2  # 2 casas decimais = 0.01cm


def engine():
    return solver_bridge.engine()


def project_paths(project_id):
    return bench_runner.project_paths(project_id)


def load_input(project_id):
    paths = project_paths(project_id)
    with open(paths["input"], "r", encoding="utf-8") as handle:
        return json.load(handle)


def xyz_to_cm(point):
    return (round(point.X * FT_TO_CM, 3), round(point.Y * FT_TO_CM, 3))


def run_solver(project_id, input_project=None, variants_per_course=None):
    """Roda o SOLVER REAL sobre `project_id`/`input_project`, cronometrado.
    Devolve as estruturas cruas — cada camada de fingerprint lê em cima
    disto, sem reimplementar a chamada ao motor (essa parte não é o que
    está sob auditoria; o resultado dela é)."""
    if input_project is None:
        input_project = load_input(project_id)
    t0 = time.perf_counter()
    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(
        input_project, variants_per_course=variants_per_course)
    elapsed_s = time.perf_counter() - t0
    return {
        "project_id": project_id,
        "input_project": input_project,
        "solve_result": solve_result,
        "walls_to_create": walls_to_create,
        "nodes": nodes,
        "openings_per_wall": openings_per_wall,
        "catalog": catalog,
        "base_z_ft": base_z_ft,
        "num_courses": num_courses,
        "notes": notes,
        "elapsed_s": elapsed_s,
    }


# ---------------------------------------------------------------------
# Identidade GEOMÉTRICA (missão item 7) — nunca por wall_idx/node_index.
# ---------------------------------------------------------------------

def wall_axis(walls_to_create, wall_idx):
    line, thickness_ft, _locks = walls_to_create[wall_idx]
    p0 = xyz_to_cm(line.GetEndPoint(0))
    p1 = xyz_to_cm(line.GetEndPoint(1))
    length_cm = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    return p0, p1, round(length_cm, 3), round(thickness_ft * FT_TO_CM, 3)


def wall_geom_key(walls_to_create, wall_idx):
    """Chave canônica de UMA parede: endpoints ORDENADOS (independe do
    sentido de desenho) + espessura. Estável através de qualquer permutação
    ou reversão de endpoints da lista de entrada."""
    p0, p1, _length_cm, thickness_cm = wall_axis(walls_to_create, wall_idx)
    a, b = sorted([p0, p1])
    r = GEOM_ROUND_CM
    return (round(a[0], r), round(a[1], r), round(b[0], r), round(b[1], r),
            round(thickness_cm, r))


def all_wall_geom_keys(walls_to_create):
    return [wall_geom_key(walls_to_create, i) for i in range(len(walls_to_create))]


def node_point_key(node):
    x_cm, y_cm = xyz_to_cm(node["point"])
    r = GEOM_ROUND_CM
    return (round(x_cm, r), round(y_cm, r))


def node_geom_key(node, walls_to_create):
    """Identidade geométrica de um NÓ: posição + tipo + conjunto de chaves
    geométricas das paredes que chegam nele (não wall_idx, não node_index —
    ver missão item 7). Serve para casar 'o mesmo nó' entre duas ordens de
    entrada diferentes."""
    point = node_point_key(node)
    arm_wall_idxs = sorted(set(w for w, _e in (node.get("arms") or [])))
    if not arm_wall_idxs and node.get("crossing_walls"):
        arm_wall_idxs = sorted(set(node["crossing_walls"]))
    arm_keys = tuple(sorted(wall_geom_key(walls_to_create, w) for w in arm_wall_idxs))
    return (point, arm_keys)


def piece_geom_key(walls_to_create, course_index, candidate):
    """Identidade geométrica de UMA peça física: parede geométrica, fiada,
    código, posição longitudinal e orientação (missão item 7)."""
    wall_idx = candidate.get("wall_idx")
    wall_key = wall_geom_key(walls_to_create, wall_idx) if wall_idx is not None else None
    ox, oy = xyz_to_cm(candidate["origin_world"])
    r = GEOM_ROUND_CM
    return (
        wall_key,
        course_index,
        candidate["logical_code"],
        round(ox, 1), round(oy, 1),
        round(candidate["rotation_deg"]) % 360,
    )


def physical_course_candidates(solve_result):
    """Só o que é REALMENTE materializado (já filtrado por banda física
    escolhida) — nunca `solve_result["candidates"]` bruto (agrega variantes
    de TODAS as bandas juntas)."""
    course_candidates = solve_result.get("course_candidates") or {}
    for course_index in sorted(course_candidates.keys()):
        for candidate in course_candidates[course_index]:
            yield course_index, candidate


# ---------------------------------------------------------------------
# Fingerprints EM CAMADAS (missão item 6)
# ---------------------------------------------------------------------

def _hash_rows(rows):
    blob = json.dumps(rows, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def layer_input_wall_geometry(run_data):
    rows = sorted(all_wall_geom_keys(run_data["walls_to_create"]))
    return _hash_rows(rows), rows


def layer_node_positions(run_data):
    rows = sorted(node_point_key(n) for n in run_data["nodes"])
    return _hash_rows(rows), rows


def layer_node_types(run_data):
    walls = run_data["walls_to_create"]
    rows = sorted((node_geom_key(n, walls)[0], n.get("kind")) for n in run_data["nodes"])
    return _hash_rows(rows), rows


def layer_node_arms(run_data):
    walls = run_data["walls_to_create"]
    rows = sorted(
        (node_geom_key(n, walls)[0], n.get("kind"), node_geom_key(n, walls)[1])
        for n in run_data["nodes"]
    )
    return _hash_rows(rows), rows


def layer_wall_end_to_node(run_data):
    """{(wall_geom_key, end_index): node_point} — camada `WALL_END_TO_NODE`
    pedida na missão (item 6), reconstruída a partir de `node["arms"]` (o
    mesmo conteúdo de `end_to_node`, mas chaveado geometricamente)."""
    walls = run_data["walls_to_create"]
    rows = []
    for node in run_data["nodes"]:
        point = node_point_key(node)
        for wall_idx, end_index in (node.get("arms") or []):
            rows.append((wall_geom_key(walls, wall_idx), end_index, point))
    rows.sort()
    return _hash_rows(rows), rows


def layer_midspan_crossings(run_data):
    walls = run_data["walls_to_create"]
    rows = []
    for node in run_data["nodes"]:
        if node.get("arms"):
            continue
        crossing = node.get("crossing_walls")
        if not crossing:
            continue
        a, b = sorted(wall_geom_key(walls, w) for w in crossing)
        rows.append((node_point_key(node), a, b))
    rows.sort()
    return _hash_rows(rows), rows


def _solutions_layer(run_data, kinds):
    """Fingerprint dos candidatos de amarração (placement_reason distinto de
    STANDARD_FILL) cujo nó geométrico mais próximo é de um dos `kinds` — usa
    como proxy independente de 'L solutions'/'T solutions'/'X solutions' as
    peças que o solver de fato produziu para aquele tipo de nó (mesmos
    campos de identidade de `piece_geom_key`)."""
    walls = run_data["walls_to_create"]
    node_by_kind_points = {}
    for node in run_data["nodes"]:
        node_by_kind_points.setdefault(node.get("kind"), []).append(node_point_key(node))

    target_points = set()
    for kind in kinds:
        target_points.update(node_by_kind_points.get(kind, []))

    rows = []
    for course_index, candidate in physical_course_candidates(run_data["solve_result"]):
        reason = candidate.get("placement_reason") or ""
        if reason == "STANDARD_FILL":
            continue
        ox, oy = xyz_to_cm(candidate["origin_world"])
        near = _nearest_point(target_points, (ox, oy))
        if near is None:
            continue
        rows.append(piece_geom_key(walls, course_index, candidate) + (reason,))
    rows.sort(key=lambda r: json.dumps(r, default=str))
    return _hash_rows(rows), rows


def _nearest_point(points, xy, max_dist_cm=60.0):
    best, best_d = None, None
    for p in points:
        d = math.hypot(p[0] - xy[0], p[1] - xy[1])
        if d <= max_dist_cm and (best_d is None or d < best_d):
            best, best_d = p, d
    return best


def layer_l_solutions(run_data):
    return _solutions_layer(run_data, ("L_CORNER",))


def layer_t_solutions(run_data):
    return _solutions_layer(run_data, ("T_INTERSECTION",))


def layer_x_solutions(run_data):
    return _solutions_layer(run_data, ("X_INTERSECTION",))


def layer_block_reservations(run_data):
    """Peças de amarração (não-STANDARD_FILL) de QUALQUER nó — proxy
    independente da 'reserva' que a Etapa 4 deixa para preenchimento comum
    não invadir (ver `_wall_reserved_range_ft` em `core/engine/wall_stepper.py`,
    lida só como referência, nunca importada/chamada)."""
    walls = run_data["walls_to_create"]
    rows = []
    for course_index, candidate in physical_course_candidates(run_data["solve_result"]):
        reason = candidate.get("placement_reason") or ""
        if reason == "STANDARD_FILL":
            continue
        rows.append(piece_geom_key(walls, course_index, candidate) + (reason,))
    rows.sort(key=lambda r: json.dumps(r, default=str))
    return _hash_rows(rows), rows


def layer_block_layouts(run_data):
    """TODAS as peças físicas materializadas (amarração + preenchimento) —
    a camada mais próxima do 'resultado final' visível no Revit."""
    walls = run_data["walls_to_create"]
    rows = sorted(
        piece_geom_key(walls, course_index, candidate)
        for course_index, candidate in physical_course_candidates(run_data["solve_result"])
    )
    return _hash_rows(rows), rows


LAYER_FUNCS = (
    ("input_wall_geometry", layer_input_wall_geometry),
    ("wall_graph_node_positions", layer_node_positions),
    ("node_types", layer_node_types),
    ("node_arms", layer_node_arms),
    ("wall_end_to_node", layer_wall_end_to_node),
    ("midspan_crossings", layer_midspan_crossings),
    ("l_solutions", layer_l_solutions),
    ("t_solutions", layer_t_solutions),
    ("x_solutions", layer_x_solutions),
    ("block_reservations", layer_block_reservations),
    ("block_layouts", layer_block_layouts),
)


def layered_fingerprints(run_data):
    """Roda TODAS as camadas na ordem da missão (item 6) e devolve
    {layer_name: (fingerprint_hex, n_rows)} + o fingerprint GLOBAL (hash de
    todos os fingerprints de camada concatenados, na ordem fixa acima)."""
    out = {}
    rows_by_layer = {}
    for name, func in LAYER_FUNCS:
        fp, rows = func(run_data)
        out[name] = {"fingerprint": fp, "n_rows": len(rows)}
        rows_by_layer[name] = rows
    global_blob = "|".join(out[name]["fingerprint"] for name, _ in LAYER_FUNCS)
    out["global_result"] = {
        "fingerprint": hashlib.sha256(global_blob.encode("utf-8")).hexdigest(),
        "n_rows": sum(v["n_rows"] for v in out.values()),
    }
    return out, rows_by_layer


def first_divergent_layer(baseline_layers, other_layers):
    for name, _func in LAYER_FUNCS:
        if baseline_layers[name]["fingerprint"] != other_layers[name]["fingerprint"]:
            return name
    return None


# ---------------------------------------------------------------------
# Downstream (missão item 12)
# ---------------------------------------------------------------------

def downstream_metrics(run_data):
    sr = run_data["solve_result"]
    pieces = list(physical_course_candidates(sr))
    codes = {}
    for _ci, cand in pieces:
        codes[cand["logical_code"]] = codes.get(cand["logical_code"], 0) + 1
    return {
        "pieces": len(pieces),
        "coverage_pieces_by_code": codes,
        "non_modular": len(sr.get("non_modular") or []),
        "intersection_failures": len(sr.get("intersection_failures") or []),
        "alignment_conflicts": len(sr.get("alignment_conflicts") or []),
        "collisions": len(sr.get("collisions") or []),
        "door_void_violations": len(sr.get("door_void_violations") or []),
        "C09": codes.get("C09", 0),
        "C04": codes.get("C04", 0),
        "B19": codes.get("B19", 0),
        "runtime_s": round(run_data["elapsed_s"], 3),
    }


def write_json(path, payload):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
    return path


def out_path(*parts):
    return os.path.join(_HERE, *parts)
