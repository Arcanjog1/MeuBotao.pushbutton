# -*- coding: utf-8 -*-
"""Biblioteca do CROSS-AUDIT FINAL do CR-BLOCK-DETERMINISM (CONTA 3).

Escrita do ZERO em cima do `solver_bridge` (o mesmo caminho headless de
`tests/solver_bench.py`), sem reusar `lib_det`/`lib_final`/`lib_cross`: o
pedido e' PROVA INDEPENDENTE, entao as camadas de fingerprint, as
variantes e a classificacao de validade nascem aqui de novo.

NENHUM arquivo de producao e' lido para escrita e nenhum `out_*.json` de
outra pasta de diagnostico e' sobrescrito.
"""

import os
import sys
import json
import math
import copy
import time
import random
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_NUVEM = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _NUVEM not in sys.path:
    sys.path.insert(0, _NUVEM)

from benchmark import solver_bridge          # noqa: E402
from benchmark import runner as bench_runner  # noqa: E402

FT_TO_CM = 100.0 * 0.3048
R = 2          # 0.01 cm nas chaves geometricas
RC = 1         # 0.1 cm (1 mm) nas celulas


def engine():
    return solver_bridge.engine()


def load_input(project_id):
    with open(bench_runner.project_paths(project_id)["input"], "r",
              encoding="utf-8") as handle:
        return json.load(handle)


def run_solver(project_id, input_project=None):
    if input_project is None:
        input_project = load_input(project_id)
    t0 = time.perf_counter()
    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(input_project)
    # `run_solver` nao devolve `end_to_node`; o planejamento e' puro e
    # barato, entao roda-se de novo so' para ter a camada do grafo.
    _nodes2, _walls2, end_to_node, _op2 = solver_bridge.plan_from_input(input_project)
    return {
        "end_to_node": end_to_node,
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
        "elapsed_s": time.perf_counter() - t0,
    }


def plan_only(input_project):
    """So' o planejamento (extensao + grafo), sem solver - usado para medir
    o EIXO ESTICADO que o motor realmente usa."""
    return solver_bridge.plan_from_input(input_project)


# ------------------------------------------------------------------
# identidade geometrica (nunca wall_idx / node_index / ordem de lista)
# ------------------------------------------------------------------

def _cm(point):
    return (round(point.X * FT_TO_CM, 6), round(point.Y * FT_TO_CM, 6))


def wall_key(walls, wall_idx):
    line, thickness_ft, _locks = walls[wall_idx]
    a = _cm(line.GetEndPoint(0))
    b = _cm(line.GetEndPoint(1))
    lo, hi = sorted([a, b])
    return (round(lo[0], R), round(lo[1], R), round(hi[0], R), round(hi[1], R),
            round(thickness_ft * FT_TO_CM, R))


def wall_lo_hi(walls, wall_idx):
    """(ponta_lo, ponta_hi) em cm, ORDENADAS - independem do sentido."""
    line, _t, _l = walls[wall_idx]
    a = _cm(line.GetEndPoint(0))
    b = _cm(line.GetEndPoint(1))
    return tuple(sorted([a, b]))


def wall_length_cm(walls, wall_idx):
    line, _t, _l = walls[wall_idx]
    a = _cm(line.GetEndPoint(0))
    b = _cm(line.GetEndPoint(1))
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _hash(rows):
    blob = json.dumps(rows, sort_keys=True, default=str,
                      ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


# ------------------------------------------------------------------
# CAMADAS DE FINGERPRINT (item 6 da missao)
# ------------------------------------------------------------------

def layer_input_wall_geometry(run):
    walls = run["walls_to_create"]
    return sorted(wall_key(walls, i) for i in range(len(walls)))


def layer_node_positions(run):
    return sorted((round(_cm(n["point"])[0], R), round(_cm(n["point"])[1], R))
                  for n in run["nodes"])


def layer_node_types(run):
    return sorted((round(_cm(n["point"])[0], R), round(_cm(n["point"])[1], R),
                   n.get("kind") or n.get("type"))
                  for n in run["nodes"])


def layer_node_arms(run):
    walls = run["walls_to_create"]
    rows = []
    for node in run["nodes"]:
        point = (round(_cm(node["point"])[0], R), round(_cm(node["point"])[1], R))
        arms = sorted(set(wall_key(walls, w) for w, _e in (node.get("arms") or [])))
        rows.append((point, tuple(arms)))
    return sorted(rows)


def layer_wall_end_to_node_canonical(run):
    """A ponta e' identificada pela COORDENADA dela (lo/hi da parede), nunca
    pelo `end_index` cru - que troca de valor por definicao quando o eixo e'
    desenhado ao contrario e faria a camada divergir sem nenhuma diferenca
    fisica."""
    walls = run["walls_to_create"]
    nodes = run["nodes"]
    rows = []
    for (wall_idx, end_index), node_index in sorted(
            (run.get("end_to_node") or {}).items()):
        line, _t, _l = walls[wall_idx]
        point_cm = _cm(line.GetEndPoint(end_index))
        lo, hi = wall_lo_hi(walls, wall_idx)
        side = "lo" if point_cm == lo else ("hi" if point_cm == hi else "?")
        node_point = _cm(nodes[node_index]["point"])
        rows.append((wall_key(walls, wall_idx), side,
                     (round(node_point[0], R), round(node_point[1], R))))
    return sorted(rows)


def layer_midspan_crossings(run):
    walls = run["walls_to_create"]
    rows = []
    for node in run["nodes"]:
        crossing = node.get("crossing_walls")
        if not crossing:
            continue
        point = (round(_cm(node["point"])[0], R), round(_cm(node["point"])[1], R))
        rows.append((point, tuple(sorted(wall_key(walls, w) for w in crossing))))
    return sorted(rows)


def _course_candidates(solve_result):
    """(course_index, candidate) de todas as fiadas, do jeito que o
    `from_solver` do benchmark le."""
    out = []
    for course_index, candidates in sorted(
            (solve_result.get("course_candidates") or {}).items()):
        for candidate in candidates or []:
            out.append((course_index, candidate))
    return out


def piece_key(walls, course_index, candidate):
    """Identidade FISICA da peca: parede geometrica, fiada, codigo, centro e
    o CONJUNTO de celulas em coordenadas de MUNDO.

    As celulas sao o que separa "mesma peca representada ao contrario"
    (B39/B54/B19/C09/C04 - celulas simetricas, mesma chave) de "peca
    fisicamente espelhada" (B34 - celulas assimetricas, chave diferente).
    Nao ha' lista fixa de codigo: a propria geometria decide."""
    wall_idx = candidate.get("wall_idx")
    wkey = wall_key(walls, wall_idx) if wall_idx is not None else None
    cx, cy = _cm(candidate["origin_world"])
    cells = []
    for cell in candidate.get("cells_world") or []:
        px, py = _cm(cell["point"])
        sx, sy = cell["size_local"]
        cells.append((round(px, RC), round(py, RC),
                      round(abs(sx) * FT_TO_CM, RC), round(abs(sy) * FT_TO_CM, RC)))
    return (wkey, course_index, candidate["logical_code"],
            round(cx, RC), round(cy, RC), tuple(sorted(cells)))


def _pieces_by_reason(run, keep):
    walls = run["walls_to_create"]
    rows = []
    for course_index, candidate in _course_candidates(run["solve_result"]):
        reason = candidate.get("placement_reason") or ""
        if keep(reason):
            rows.append(piece_key(walls, course_index, candidate))
    return sorted(rows)


def layer_physical_ties(run):
    return _pieces_by_reason(
        run, lambda r: r not in ("STANDARD_FILL", "OPENING_REPAIR_FILL"))


def layer_physical_standard_fill(run):
    return _pieces_by_reason(run, lambda r: r == "STANDARD_FILL")


def layer_physical_opening_repair_fill(run):
    return _pieces_by_reason(run, lambda r: r == "OPENING_REPAIR_FILL")


def layer_physical_block_layouts(run):
    walls = run["walls_to_create"]
    return sorted(piece_key(walls, ci, c)
                  for ci, c in _course_candidates(run["solve_result"]))


LAYERS = (
    ("input_wall_geometry", layer_input_wall_geometry),
    ("node_positions", layer_node_positions),
    ("node_types", layer_node_types),
    ("node_arms", layer_node_arms),
    ("wall_end_to_node_canonical", layer_wall_end_to_node_canonical),
    ("midspan_crossings", layer_midspan_crossings),
    ("physical_ties", layer_physical_ties),
    ("physical_standard_fill", layer_physical_standard_fill),
    ("physical_opening_repair_fill", layer_physical_opening_repair_fill),
    ("physical_block_layouts", layer_physical_block_layouts),
)


def fingerprints(run):
    out, rows_by_layer = {}, {}
    for name, func in LAYERS:
        rows = func(run)
        rows_by_layer[name] = rows
        out[name] = {"fingerprint": _hash(rows), "n_rows": len(rows)}
    blob = "|".join(out[name]["fingerprint"] for name, _f in LAYERS)
    out["global_result"] = {"fingerprint": hashlib.sha256(blob.encode()).hexdigest(),
                            "n_rows": sum(v["n_rows"] for v in out.values())}
    return out, rows_by_layer


def first_divergent_layer(a, b):
    for name, _f in LAYERS:
        if a[name]["fingerprint"] != b[name]["fingerprint"]:
            return name
    return None


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False,
                  sort_keys=True, default=str)


def out_path(*parts):
    return os.path.join(_HERE, *parts)
