# -*- coding: utf-8 -*-
"""CR-BLOCK-SOLVER-RESIDUAL-ROOT-CAUSE-ATLAS - biblioteca DIAGNOSTICA.

Contrato desta pasta (`nuvem/benchmark/diagnostics_residual_atlas/`):
  - SO' LEITURA do motor (`core/wall_modeling.py`, `core/engine/**`) e da
    infraestrutura de benchmark (`nuvem/benchmark/*`). Nenhum arquivo de
    producao e' modificado. Nenhum arquivo versionado dos projetos
    (`baseline.json`, `reference.json`, `reference_score.json`,
    `score.json`) e' escrito por nenhum script daqui.
  - Headless (stubs de `tests/revit_stubs.py`), reproduzivel.
  - Instrumentacao SOMENTE por monkeypatch/wrapper em memoria, dentro
    dos scripts desta pasta - nunca editando producao para imprimir log.
  - Dumps grandes vao para `ATLAS_OUT_DIR` (por default fora do repo, no
    scratchpad da sessao); no repo ficam so' saidas pequenas e uteis.
"""

import copy
import hashlib
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_NUVEM_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _NUVEM_DIR not in sys.path:
    sys.path.insert(0, _NUVEM_DIR)

from benchmark import model  # noqa: E402
from benchmark import runner as bench_runner  # noqa: E402
from benchmark import solver_bridge  # noqa: E402
from benchmark import validators  # noqa: E402
from benchmark import scoring  # noqa: E402
from benchmark.comparator import match as matcher  # noqa: E402
from benchmark.extract import from_solver  # noqa: E402

FT_TO_CM = 30.48
PROJECT_IDS = ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1", "piloto_sintetico_2x2")
SHORT = {"torre_easy_lo_r00_tgd": "TGD", "torre_easy_lo_r00_tp1": "TP1",
         "piloto_sintetico_2x2": "PILOTO"}

OUT_DIR = os.environ.get(
    "ATLAS_OUT_DIR",
    os.path.join(_HERE, "out"),
)


def out_path(*parts):
    path = os.path.join(OUT_DIR, *parts)
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    return path


def _sanitize(value):
    """Chaves nao-string (tuplas/ints) viram string; XYZ vira lista."""
    if isinstance(value, dict):
        return dict((k if isinstance(k, str) else str(k), _sanitize(v)) for k, v in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_sanitize(v) for v in value]
    if hasattr(value, "X") and hasattr(value, "Y"):
        return [value.X, value.Y, getattr(value, "Z", 0.0)]
    return value


def write_json(path, payload, indent=1):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_sanitize(payload), handle, ensure_ascii=False, indent=indent, sort_keys=True,
                  default=_json_default)
        handle.write("\n")
    return path


def cached_run(project_id, force=False, variants_per_course=None):
    """Executa o solver UMA vez por projeto e guarda o `run` inteiro em
    pickle (OUT_DIR/<SHORT>/run.pkl) para os scripts diagnosticos
    seguintes nao pagarem os 20-40s de solver de novo. `force=True`
    reexecuta. O motor precisa estar carregado ANTES do unpickle (as
    classes XYZ/Line dos stubs sao referenciadas por modulo)."""
    import pickle
    engine()
    short = SHORT.get(project_id, project_id)
    path = out_path(short, "run.pkl")
    if not force and variants_per_course is None and os.path.isfile(path):
        with open(path, "rb") as handle:
            return pickle.load(handle)
    run = run_solver_in_memory(load_input(project_id), variants_per_course=variants_per_course)
    if variants_per_course is None:
        with open(path, "wb") as handle:
            pickle.dump(run, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return run


def _json_default(value):
    # XYZ dos stubs / tuplas / sets
    if hasattr(value, "X") and hasattr(value, "Y"):
        return [value.X, value.Y, getattr(value, "Z", 0.0)]
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)
    return str(value)


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def engine():
    return solver_bridge.engine()


def stepper():
    """O modulo `core.engine.wall_stepper` DE VERDADE (onde as funcoes
    internas de preenchimento vivem - e' nele que um monkeypatch precisa
    ser aplicado para afetar as chamadas internas)."""
    engine()
    return sys.modules["core.engine.wall_stepper"]


def project_paths(project_id):
    return bench_runner.project_paths(project_id)


def load_input(project_id):
    return read_json(project_paths(project_id)["input"])


def load_reference(project_id):
    path = project_paths(project_id)["reference"]
    if not os.path.isfile(path):
        return None
    return read_json(path)


def run_solver_in_memory(input_project, variants_per_course=None):
    """Mesma chamada que `runner.run_project` faz, sem escrever nada."""
    t0 = time.time()
    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(
        input_project, variants_per_course=variants_per_course)
    elapsed = time.time() - t0
    # end_to_node nao e' devolvido por run_solver - reconstruimos com a
    # mesma funcao (deterministica) para diagnosticos que precisam dele.
    nodes2, walls2, end_to_node, _op = solver_bridge.plan_from_input(input_project)
    return {
        "solve_result": solve_result,
        "walls_to_create": walls_to_create,
        "nodes": nodes,
        "end_to_node": end_to_node,
        "openings_per_wall": openings_per_wall,
        "catalog": catalog,
        "base_z_ft": base_z_ft,
        "num_courses": num_courses,
        "notes": notes,
        "solver_seconds": elapsed,
    }


def build_result_project(project_id, run):
    return from_solver.project_from_solver(
        project_id, run["solve_result"], run["walls_to_create"], run["nodes"],
        run["openings_per_wall"], run["catalog"], run["base_z_ft"], run["num_courses"],
        metadata={"from_input": "input.json", "solver_notes": run["notes"]},
    )


def evaluate(project, reference):
    t0 = time.time()
    findings, score, comparison = bench_runner.evaluate_project(project, reference)
    return findings, score, comparison, time.time() - t0


def counts_by_code(findings):
    counts = {}
    for row in findings:
        counts[row["code"]] = counts.get(row["code"], 0) + 1
    return dict(sorted(counts.items()))


def wall_pairs(project, reference):
    """{solver_wall_id: human_wall_id} + reverso, via o casamento oficial."""
    if reference is None:
        return {}, {}
    matching = matcher.match_walls(project, reference)
    fwd, rev = {}, {}
    for result_wall, reference_wall in matching["pairs"]:
        fwd[result_wall["id"]] = reference_wall["id"]
        rev[reference_wall["id"]] = result_wall["id"]
    return fwd, rev


# --------------------------------------------------------------- geometria
def xyz_cm(point):
    return (point.X * FT_TO_CM, point.Y * FT_TO_CM)


def wall_axis_cm(walls_to_create, wall_idx):
    line, thickness_ft, _locks = walls_to_create[wall_idx]
    p0 = xyz_cm(line.GetEndPoint(0))
    p1 = xyz_cm(line.GetEndPoint(1))
    direction, length = model.direction_of(p0, p1)
    return p0, p1, direction, length, thickness_ft * FT_TO_CM


def wall_orientation(walls_to_create, wall_idx):
    p0, p1, direction, _l, _t = wall_axis_cm(walls_to_create, wall_idx)
    ang = model.normalize_axis_angle(model.angle_deg(direction))
    if abs(ang) < 1.0 or abs(ang - 180.0) < 1.0:
        return "H"
    if abs(ang - 90.0) < 1.0:
        return "V"
    return "D"


def candidate_extent_cm(candidate, walls_to_create, wall_idx):
    """(t_start_cm, t_end_cm) do candidato PROJETADO no eixo de wall_idx.
    Peca PARALELA ao eixo: centro +- length/2 (mesma conta de from_solver).
    Peca PERPENDICULAR (a peca de no' da parede vizinha vista desta parede):
    centro +- width/2 - e' o que ela ocupa fisicamente NESTE eixo."""
    p0, _p1, direction, _length, _t = wall_axis_cm(walls_to_create, wall_idx)
    center = xyz_cm(candidate["origin_world"])
    t_center, s = model.axial_coordinates(center, p0, direction)
    x_dir = candidate.get("x_dir")
    parallel = True
    if x_dir is not None:
        dot = abs(x_dir.X * direction[0] + x_dir.Y * direction[1])
        parallel = dot > 0.7
    half = float(candidate["length_cm"]) / 2.0 if parallel else float(candidate.get("width_cm") or 14.0) / 2.0
    return t_center - half, t_center + half, s


def course_letter(course_index):
    return "A" if course_index % 2 == 0 else "B"


def physical_courses(solve_result):
    """{course_index: [candidatos]} ordenado por indice."""
    cc = solve_result.get("course_candidates") or {}
    return dict(sorted((int(k), v) for k, v in cc.items()))


def wall_course_items(run, wall_idx, course_index, include_secondary=True):
    """Pecas da fiada fisica `course_index` que pertencem (ou tocam, quando
    include_secondary) a parede wall_idx, ordenadas por t_start no eixo
    dela. Cada item: dict com code, t0, t1, s, reason, owner, node_index,
    course_letter, secondary."""
    items = []
    for cand in physical_courses(run["solve_result"]).get(course_index) or []:
        owner = cand.get("wall_idx")
        secondary = cand.get("secondary_wall_idx")
        if owner != wall_idx and not (include_secondary and secondary == wall_idx):
            continue
        t0, t1, s = candidate_extent_cm(cand, run["walls_to_create"], wall_idx)
        items.append({
            "code": cand.get("logical_code"),
            "t0": round(t0, 2), "t1": round(t1, 2), "s": round(s, 2),
            "len": cand.get("length_cm"),
            "reason": cand.get("placement_reason"),
            "owner": owner, "secondary": secondary,
            "node_index": cand.get("node_index"),
            "letter": cand.get("course"),
            "mirrored": bool(cand.get("mirrored")),
            "is_own": owner == wall_idx,
        })
    items.sort(key=lambda it: (it["t0"], it["t1"]))
    return items


def compose(items, only_own=False):
    """'B34 | B39 | C09' a partir dos itens (na ordem do eixo)."""
    seq = [it for it in items if (it["is_own"] or not only_own)]
    return " | ".join(it["code"] + ("" if it["is_own"] else "*") for it in seq)


def human_row_items(reference_wall, row_index, reversed_axis=False):
    """Blocos humanos da fiada `row_index` como itens comparaveis (t0, t1,
    code). Se `reversed_axis`, espelha t no comprimento da parede humana
    (quando o eixo do solver esta' invertido em relacao ao humano)."""
    length = reference_wall["length_cm"]
    items = []
    for row in reference_wall.get("rows") or []:
        if row["row"] != row_index:
            continue
        for block in row.get("blocks") or []:
            t0, t1 = block["t_start_cm"], block["t_end_cm"]
            if reversed_axis:
                t0, t1 = length - t1, length - t0
            items.append({"code": block.get("code"), "t0": round(t0, 2),
                          "t1": round(t1, 2), "role": block.get("role"),
                          "is_own": True, "family": block.get("family"),
                          "type_name": block.get("type_name")})
    items.sort(key=lambda it: (it["t0"], it["t1"]))
    return items


def axes_reversed(solver_wall, human_wall):
    """True quando start/end do solver casam com end/start do humano."""
    a0, a1 = solver_wall["start_cm"], solver_wall["end_cm"]
    b0, b1 = human_wall["start_cm"], human_wall["end_cm"]
    direct = (abs(a0[0] - b0[0]) + abs(a0[1] - b0[1]) + abs(a1[0] - b1[0]) + abs(a1[1] - b1[1]))
    flipped = (abs(a0[0] - b1[0]) + abs(a0[1] - b1[1]) + abs(a1[0] - b0[0]) + abs(a1[1] - b0[1]))
    return flipped < direct


def human_t_offset(solver_wall, human_wall):
    """t_solver = offset + sign * t_human. `offset` e' o t (no eixo do
    solver) do PONTO INICIAL humano; `sign` e' -1 quando os eixos estao
    invertidos. Vale para paredes que se sobrepoem so' parcialmente
    (fragmento do solver dentro de uma parede humana longa): t_solver pode
    sair negativo ou maior que o comprimento do fragmento - e' o esperado."""
    rev = axes_reversed(solver_wall, human_wall)
    direction, _l = model.direction_of(solver_wall["start_cm"], solver_wall["end_cm"])
    t_h0, _s = model.axial_coordinates(human_wall["start_cm"], solver_wall["start_cm"], direction)
    return (-1.0 if rev else 1.0), t_h0


def human_items_on_solver_axis(solver_wall, human_wall, row_index):
    sign, offset = human_t_offset(solver_wall, human_wall)
    items = []
    for row in human_wall.get("rows") or []:
        if row["row"] != row_index:
            continue
        for block in row.get("blocks") or []:
            a = offset + sign * block["t_start_cm"]
            b_ = offset + sign * block["t_end_cm"]
            t0, t1 = min(a, b_), max(a, b_)
            items.append({"code": block.get("code"), "t0": round(t0, 2), "t1": round(t1, 2),
                          "role": block.get("role"), "is_own": True})
    items.sort(key=lambda it: (it["t0"], it["t1"]))
    return items


# ------------------------------------------------------------- fingerprint
def physical_fingerprint(run):
    """Hash das pecas fisicas (parede, fiada, codigo, t0, t1 arredondados) -
    identidade geometrica, nunca ElementId/indice de lista."""
    rows = []
    walls = run["walls_to_create"]
    for course_index, cands in physical_courses(run["solve_result"]).items():
        for cand in cands:
            wall_idx = cand.get("wall_idx")
            if wall_idx is None:
                continue
            p0, p1, _d, _l, _t = wall_axis_cm(walls, wall_idx)
            t0, t1, s = candidate_extent_cm(cand, walls, wall_idx)
            key = (round(p0[0], 1), round(p0[1], 1), round(p1[0], 1), round(p1[1], 1),
                   course_index, cand.get("logical_code"), round(t0, 1), round(t1, 1),
                   cand.get("placement_reason"))
            rows.append(key)
    rows.sort()
    blob = json.dumps(rows, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), len(rows)


def node_summary(run):
    """Resumo dos nos: index, kind, point_cm, arms [(wall_idx, end_index)]."""
    out = []
    for index, node in enumerate(run["nodes"] or []):
        point = node.get("point")
        out.append({
            "node_index": index,
            "kind": node.get("kind"),
            "point_cm": [round(v, 2) for v in xyz_cm(point)] if point is not None else None,
            "arms": [list(a) for a in (node.get("arms") or [])],
            "extra": dict((k, v) for k, v in node.items()
                          if k not in ("point", "arms", "kind") and not hasattr(v, "X")),
        })
    return out


def timer():
    return time.time()


# ================================================================ contexto
TIE_PREFIXES = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION", "CORNER")


def is_tie_reason(reason):
    reason = str(reason or "")
    return any(reason.startswith(p) for p in TIE_PREFIXES)


def wall_id_of(wall_idx):
    return "W{0:03d}".format(wall_idx + 1)


def wall_idx_of(wall_id):
    return int(wall_id[1:]) - 1


def node_t_on_wall(run, node_index, wall_idx):
    node = run["nodes"][node_index]
    p0, _p1, direction, _l, _t = wall_axis_cm(run["walls_to_create"], wall_idx)
    t, _s = model.axial_coordinates(xyz_cm(node["point"]), p0, direction)
    return t


def node_pieces(run):
    """{node_index: [candidatos de no' (todas as pecas de amarracao geradas
    por solve_all_intersections, a partir de qualquer banda)]}. Usa os
    candidatos agregados do `solve_result` (`candidates`), deduplicando
    por (course, wall_idx, code, origem arredondada)."""
    out = {}
    seen = set()
    for cand in run["solve_result"].get("candidates") or []:
        if cand.get("node_index") is None:
            continue
        key = (cand.get("node_index"), cand.get("course"), cand.get("wall_idx"),
               cand.get("logical_code"), round(cand["origin_world"].X, 3),
               round(cand["origin_world"].Y, 3))
        if key in seen:
            continue
        seen.add(key)
        out.setdefault(cand["node_index"], []).append(cand)
    return out


def wall_context(run, wall_idx, node_pieces_index=None):
    """Tudo que a classificacao causal precisa saber sobre UMA parede."""
    walls = run["walls_to_create"]
    p0, p1, direction, length, thickness = wall_axis_cm(walls, wall_idx)
    if node_pieces_index is None:
        node_pieces_index = node_pieces(run)
    ends = {}
    for end_index in (0, 1):
        node_index = run["end_to_node"].get((wall_idx, end_index))
        if node_index is None:
            ends[end_index] = {"node_index": None, "kind": "NONE", "t_cm": 0.0 if end_index == 0 else length}
            continue
        node = run["nodes"][node_index]
        pieces = []
        for cand in node_pieces_index.get(node_index, []):
            t0, t1, s = candidate_extent_cm(cand, walls, wall_idx)
            pieces.append({"code": cand.get("logical_code"), "course": cand.get("course"),
                           "reason": cand.get("placement_reason"),
                           "owner": cand.get("wall_idx"), "t0": round(t0, 2), "t1": round(t1, 2),
                           "own": cand.get("wall_idx") == wall_idx})
        ends[end_index] = {
            "node_index": node_index, "kind": node.get("kind"),
            "t_cm": round(node_t_on_wall(run, node_index, wall_idx), 2),
            "arms": [list(a) for a in (node.get("arms") or [])],
            "other_walls": sorted(set(
                [a[0] for a in (node.get("arms") or []) if a[0] != wall_idx]
                + [node[k] for k in ("main_wall_idx", "incoming_wall_idx", "neighbor_wall_idx")
                   if node.get(k) is not None and node.get(k) != wall_idx])),
            "pieces": sorted(pieces, key=lambda p: (p["course"], p["t0"])),
            "degraded": any("DEGRADED" in str(p["reason"]) for p in pieces),
            "pinned": bool(node.get("_arm_role_pinned")),
        }
    midspan = []
    for node_index, node in enumerate(run["nodes"] or []):
        kind = node.get("kind")
        involved = False
        if kind == "T_INTERSECTION" and node.get("main_wall_idx") == wall_idx:
            involved = True
        if kind == "X_INTERSECTION" and wall_idx in (node.get("crossing_walls") or []):
            involved = True
        if not involved:
            continue
        pieces = []
        for cand in node_pieces_index.get(node_index, []):
            t0, t1, s = candidate_extent_cm(cand, walls, wall_idx)
            pieces.append({"code": cand.get("logical_code"), "course": cand.get("course"),
                           "reason": cand.get("placement_reason"), "owner": cand.get("wall_idx"),
                           "t0": round(t0, 2), "t1": round(t1, 2), "own": cand.get("wall_idx") == wall_idx})
        midspan.append({
            "node_index": node_index, "kind": kind,
            "t_cm": round(node_t_on_wall(run, node_index, wall_idx), 2),
            "other_walls": sorted(set(
                [node[k] for k in ("main_wall_idx", "incoming_wall_idx") if node.get(k) is not None and node.get(k) != wall_idx]
                + [w for w in (node.get("crossing_walls") or []) if w is not None and w != wall_idx])),
            "pieces": sorted(pieces, key=lambda p: (p["course"], p["t0"])),
            "degraded": any("DEGRADED" in str(p["reason"]) for p in pieces),
        })
    midspan.sort(key=lambda m: m["t_cm"])
    openings = []
    for op in (run["openings_per_wall"][wall_idx] or []):
        t0, t1, sill, head = [v * FT_TO_CM for v in op[:4]]
        base = run["base_z_ft"] * FT_TO_CM
        openings.append({"t0": round(t0, 2), "t1": round(t1, 2), "sill_cm": round(sill, 2),
                         "head_cm": round(head, 2),
                         "kind": "door" if sill <= base + 1.0 else "window"})
    openings.sort(key=lambda o: o["t0"])
    return {
        "wall_idx": wall_idx, "wall_id": wall_id_of(wall_idx),
        "key": model.wall_stable_key(p0, p1, thickness),
        "orientation": wall_orientation(walls, wall_idx),
        "start_cm": [round(p0[0], 2), round(p0[1], 2)], "end_cm": [round(p1[0], 2), round(p1[1], 2)],
        "length_cm": round(length, 2), "thickness_cm": round(thickness, 2),
        "ends": ends, "midspan_nodes": midspan, "openings": openings,
    }


def band_of_course(run, course_index):
    for band_pos, band in enumerate(run["solve_result"].get("bands") or []):
        if course_index in (band.get("course_indices") or []):
            return band_pos
    return None


def openings_active_in_course(ctx, run, course_index):
    """Aberturas da parede ativas na fiada fisica (mesmo criterio do motor:
    faixa [z_lo, z_lo+block_height) cruza [sill, head))."""
    catalog = run["catalog"]
    heights = [e["height_cm"] for e in catalog.values() if e.get("height_cm")]
    block_h = min(heights) if heights else 19.0
    step = block_h + 1.0
    base = run["base_z_ft"] * FT_TO_CM
    z_lo = base + 1.0 + course_index * step
    z_hi = z_lo + block_h
    active = []
    for op in ctx["openings"]:
        lo = max(op["sill_cm"], z_lo)
        hi = min(op["head_cm"], z_hi)
        if hi - lo > 0.2:
            active.append(op)
    return active


def nearest_feature(ctx, t_cm):
    """(tipo, distancia_cm, referencia) da feicao mais proxima de t_cm:
    no' de ponta, no' de meio, borda de abertura ou ponta livre."""
    best = None
    for end_index, end in ctx["ends"].items():
        kind = end["kind"]
        label = ("NODE_END_" + kind) if kind not in ("NONE", "FREE_END") else "FREE_END"
        d = abs(t_cm - end["t_cm"])
        if best is None or d < best[1]:
            best = (label, round(d, 2), {"end_index": end_index, "node_index": end.get("node_index"), "kind": kind})
    for mid in ctx["midspan_nodes"]:
        d = abs(t_cm - mid["t_cm"])
        if best is None or d < best[1]:
            best = ("NODE_MID_" + mid["kind"], round(d, 2), {"node_index": mid["node_index"], "kind": mid["kind"]})
    for op in ctx["openings"]:
        for edge_name, edge in (("lo", op["t0"]), ("hi", op["t1"])):
            d = abs(t_cm - edge)
            if best is None or d < best[1]:
                best = ("OPENING_" + op["kind"].upper() + "_" + edge_name, round(d, 2), dict(op))
    return best


def load_state(short):
    """Le' o que run_state_current.py gravou para um projeto."""
    base = os.path.join(OUT_DIR, short)
    state = {
        "result": read_json(os.path.join(base, "result.json")),
        "findings": read_json(os.path.join(base, "findings.json")),
        "score": read_json(os.path.join(base, "score.json")),
        "solver_extra": read_json(os.path.join(base, "solver_extra.json")),
        "wall_pairs": read_json(os.path.join(base, "wall_pairs.json")),
    }
    return state


def result_wall_by_id(result_project):
    return dict((w["id"], w) for w in result_project.get("walls") or [])


def reference_wall_by_id(reference):
    return dict((w["id"], w) for w in (reference or {}).get("walls") or [])


# ============================================================ id <-> idx
# ATENCAO: `model.assign_ids` REORDENA as paredes geometricamente e
# renumera W001..; o `W{idx+1}` de from_solver NAO sobrevive. O vinculo
# estavel e' a chave geometrica (`wall_stable_key`).
def wall_maps(run, result_project):
    """(idx_to_id, id_to_idx) casando pela chave geometrica estavel."""
    walls = run["walls_to_create"]
    key_to_idx = {}
    for wall_idx in range(len(walls)):
        p0, p1, _d, _l, thickness = wall_axis_cm(walls, wall_idx)
        key_to_idx.setdefault(model.wall_stable_key(p0, p1, thickness), []).append(wall_idx)
    idx_to_id, id_to_idx = {}, {}
    ambiguous = []
    for wall in result_project.get("walls") or []:
        key = wall["key"]
        idxs = key_to_idx.get(key) or []
        if len(idxs) == 1:
            idx_to_id[idxs[0]] = wall["id"]
            id_to_idx[wall["id"]] = idxs[0]
        elif len(idxs) > 1:
            # paredes DUPLICADAS na entrada (mesma chave): casa pela
            # posicao dos blocos (primeira fiada) - se nada distinguir,
            # registra ambiguidade e usa o primeiro livre.
            free = [i for i in idxs if i not in idx_to_id]
            chosen = free[0] if free else idxs[0]
            idx_to_id[chosen] = wall["id"]
            id_to_idx[wall["id"]] = chosen
            ambiguous.append((wall["id"], idxs))
        else:
            ambiguous.append((wall["id"], []))
    # Fallback GEOMETRICO para chaves que nao casaram (arredondamento de 3
    # casas do result.json cruzando a grade de 0,5cm da chave): menor soma
    # de distancias entre pontas, nos dois sentidos, entre os idx livres.
    unmatched = [wid for wid, idxs in ambiguous if not idxs]
    for wid in unmatched:
        wall = next(w for w in result_project["walls"] if w["id"] == wid)
        best, best_d = None, None
        for wall_idx in range(len(walls)):
            if wall_idx in idx_to_id:
                continue
            p0, p1, _d, _l, _t = wall_axis_cm(walls, wall_idx)
            a0, a1 = wall["start_cm"], wall["end_cm"]
            direct = (abs(a0[0] - p0[0]) + abs(a0[1] - p0[1]) + abs(a1[0] - p1[0]) + abs(a1[1] - p1[1]))
            flipped = (abs(a0[0] - p1[0]) + abs(a0[1] - p1[1]) + abs(a1[0] - p0[0]) + abs(a1[1] - p0[1]))
            d = min(direct, flipped)
            if best_d is None or d < best_d:
                best, best_d = wall_idx, d
        if best is not None and best_d is not None and best_d < 2.0:
            idx_to_id[best] = wid
            id_to_idx[wid] = best
            ambiguous = [(w, i) for (w, i) in ambiguous if w != wid]
    return idx_to_id, id_to_idx, ambiguous


# ============================================================ bundle
class Bundle(object):
    """Tudo de um projeto ja' carregado, para scripts/probes curtos."""

    def __init__(self, project_id):
        self.project_id = project_id
        self.short = SHORT[project_id]
        self.run = cached_run(project_id)
        self.state = load_state(self.short)
        self.result = self.state["result"]
        self.reference = load_reference(project_id)
        self.idx_to_id, self.id_to_idx, self.ambiguous = wall_maps(self.run, self.result)
        self.pairs = self.state["wall_pairs"]["solver_to_human"]
        self.ref_by_id = reference_wall_by_id(self.reference)
        self.res_by_id = result_wall_by_id(self.result)
        self.node_pieces = node_pieces(self.run)
        path = os.path.join(OUT_DIR, self.short, "wall_context.json")
        self.contexts = {}
        if os.path.isfile(path):
            raw = read_json(path)
            for k, v in raw.items():
                v["ends"] = dict((int(ek), ev) for ek, ev in v["ends"].items())
                self.contexts[int(k)] = v
        self.inventory = read_json(os.path.join(OUT_DIR, self.short, "inventory.json")) \
            if os.path.isfile(os.path.join(OUT_DIR, self.short, "inventory.json")) else []

    def ctx(self, wall_idx):
        if wall_idx not in self.contexts:
            self.contexts[wall_idx] = wall_context(self.run, wall_idx, self.node_pieces)
            self.contexts[wall_idx]["wall_id"] = self.idx_to_id.get(wall_idx)
            self.contexts[wall_idx]["human_wall"] = self.pairs.get(self.idx_to_id.get(wall_idx))
        return self.contexts[wall_idx]

    def idx(self, wall_id):
        return self.id_to_idx[wall_id]

    def solver_row(self, wall_idx, course_index, include_secondary=True):
        return wall_course_items(self.run, wall_idx, course_index, include_secondary)

    def human_overlaps(self, wall_idx):
        """TODAS as paredes humanas colineares que se sobrepoem a esta parede
        do solver (nao so' o par 1:1 do casamento oficial). Necessario no TGD,
        onde o solver fragmenta uma parede humana longa em varios eixos e o
        casamento 1:1 deixa os demais fragmentos 'sem humano'."""
        from benchmark.comparator import match as _match
        if not hasattr(self, "_overlap_cache"):
            self._overlap_cache = {}
        if wall_idx in self._overlap_cache:
            return self._overlap_cache[wall_idx]
        wid = self.idx_to_id.get(wall_idx)
        out = []
        if wid and self.reference:
            sw = self.res_by_id[wid]
            for hw in self.reference["walls"]:
                cost = _match.score_pair(sw, hw)
                if cost is not None:
                    out.append(hw)
        self._overlap_cache[wall_idx] = out
        return out

    def human_row(self, wall_idx, course_index):
        """Blocos humanos da fiada no eixo do solver, unindo TODAS as paredes
        humanas colineares sobrepostas (ver human_overlaps). None se nenhuma."""
        wid = self.idx_to_id.get(wall_idx)
        if not wid:
            return None
        hws = self.human_overlaps(wall_idx)
        if not hws:
            return None
        items = []
        sw = self.res_by_id[wid]
        for hw in hws:
            items.extend(human_items_on_solver_axis(sw, hw, course_index))
        items.sort(key=lambda it: (it["t0"], it["t1"]))
        return items

    def human_label(self, wall_idx):
        hws = self.human_overlaps(wall_idx)
        return "+".join(h["id"] for h in hws) if hws else None

    def findings(self, code=None, wall_id=None):
        out = []
        for f in self.state["findings"]:
            if code and f["code"] != code:
                continue
            if wall_id and f.get("wall") != wall_id:
                continue
            out.append(f)
        return out


def fmt_items(items):
    if items is None:
        return "(sem humano)"
    return " ".join("[{0}-{1} {2}{3}]".format(int(round(it["t0"])), int(round(it["t1"])), it["code"],
                                              "" if it.get("is_own", True) else "*") for it in items)
