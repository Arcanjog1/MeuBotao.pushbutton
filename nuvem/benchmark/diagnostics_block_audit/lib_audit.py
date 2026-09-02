# -*- coding: utf-8 -*-
"""Biblioteca compartilhada do laboratório de auditoria independente de
blocos (CONTA 2 — auditoria/benchmark, ver docs/BLOCK_MODULATION_AUDIT.md).

Contrato desta pasta inteira (`nuvem/benchmark/diagnostics_block_audit/`):
  - SÓ LEITURA do motor (`core/wall_modeling.py`, `core/engine/**`) e da
    infraestrutura de benchmark já existente (`nuvem/benchmark/*`) — nenhuma
    linha de produção é importada para ser modificada, nenhum arquivo fora
    desta pasta é escrito por nenhum script daqui.
  - Sem MCP, sem Revit aberto: roda 100% headless sobre os projetos já
    versionados em `nuvem/benchmark/projects/` (via `tests/revit_stubs.py`,
    o mesmo caminho que `tests/solver_bench.py` e `nuvem/benchmark/*` usam).
  - Reproduzível: mesma entrada, mesmo projeto -> mesma saída (a menos que o
    próprio script esteja medindo determinismo, caso em que a variação é o
    ponto).
  - Este módulo NÃO reescreve nenhuma regra do solver — ele só chama as
    funções de produção já existentes (via `solver_bridge.engine()`) e faz
    a SUA PRÓPRIA contagem/medição em cima do resultado, para servir de
    censo independente (a auditoria não deve confiar cegamente nos
    validadores do benchmark já existentes em `nuvem/benchmark/validators/`
    — pode usá-los como referência cruzada, mas a medição primária é sua).

Métrica que não pode ser obtida rodando headless (ex.: algo que só existe
dentro do Revit real) deve ser marcada literalmente como a string
`"NOT_HEADLESS_OBSERVABLE"` no JSON de saída — nunca inventada.
"""

import os
import sys
import json
import time
import math
import hashlib
import copy

_HERE = os.path.dirname(os.path.abspath(__file__))

# nuvem/benchmark/diagnostics_block_audit/ -> nuvem/benchmark/ -> nuvem/
_NUVEM_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _NUVEM_DIR not in sys.path:
    sys.path.insert(0, _NUVEM_DIR)

from benchmark import solver_bridge  # noqa: E402
from benchmark import runner as bench_runner  # noqa: E402

FEET_PER_METER = 1.0 / 0.3048
FT_TO_CM = 100.0 * 0.3048  # = 30.48, mesma convenção de core/wall_modeling.py

PROJECT_IDS = ("piloto_sintetico_2x2", "torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1")

# Projeto principal do censo (o único com input MEDIDO, não reconstruído do
# próprio gabarito — ver REGRAS_MODULACAO_BLOCOS.md secao 24.8/24.9 e
# nuvem/benchmark/README.md). Os outros dois entram como comparação.
PRIMARY_PROJECT_ID = "torre_easy_lo_r00_tgd"


def ft_to_cm(value_ft):
    return value_ft * FT_TO_CM


def cm_to_ft(value_cm):
    return value_cm / FT_TO_CM


def xyz_to_cm(point):
    """(x_cm, y_cm) arredondado a 3 casas — ponto XYZ (stub) do motor, em pés."""
    return (round(point.X * FT_TO_CM, 3), round(point.Y * FT_TO_CM, 3))


def engine():
    return solver_bridge.engine()


def project_paths(project_id):
    return bench_runner.project_paths(project_id)


def load_input(project_id):
    paths = project_paths(project_id)
    with open(paths["input"], "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_reference(project_id):
    paths = project_paths(project_id)
    if not os.path.isfile(paths["reference"]):
        return None
    with open(paths["reference"], "r", encoding="utf-8") as handle:
        return json.load(handle)


def plan(input_project):
    """(nodes, walls_to_create, end_to_node, openings_per_wall) — Fase A
    pura, sem solver de blocos. Mesma função usada pelo benchmark oficial."""
    return solver_bridge.plan_from_input(input_project)


def catalog_for(input_project):
    return solver_bridge.catalog_from_input(input_project)


def run_solver(project_id, input_project=None, variants_per_course=None):
    """Roda o SOLVER REAL (`solve_building_blocks_all_courses`) sobre o
    projeto `project_id`, cronometrado. Devolve um dict com todas as
    estruturas cruas — cada script de censo faz sua própria leitura em cima
    disto, sem reimplementar a chamada ao motor."""
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
        "variants_per_course": (variants_per_course
                                 if variants_per_course is not None
                                 else engine().PIER_LAYOUT_VARIANTS_PER_COURSE),
    }


def wall_axis(walls_to_create, wall_idx):
    """(p0_cm, p1_cm, length_cm, thickness_cm) de uma parede, já em cm."""
    line, thickness_ft, _locks = walls_to_create[wall_idx]
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    p0_cm = xyz_to_cm(p0)
    p1_cm = xyz_to_cm(p1)
    length_cm = math.hypot(p1_cm[0] - p0_cm[0], p1_cm[1] - p0_cm[1])
    return p0_cm, p1_cm, round(length_cm, 3), round(ft_to_cm(thickness_ft), 3)


def wall_geom_key(walls_to_create, wall_idx):
    """Chave geométrica CANÔNICA de uma parede — independe da ordem de
    entrada e do sentido do desenho (pontas ordenadas). Usada para comparar
    o mesmo eixo através de permutações/seeds (censo de determinismo, item
    20 da missão) sem depender de `wall_idx`, que muda com a permutação."""
    p0_cm, p1_cm, length_cm, thickness_cm = wall_axis(walls_to_create, wall_idx)
    a, b = sorted([p0_cm, p1_cm])
    return (round(a[0], 2), round(a[1], 2), round(b[0], 2), round(b[1], 2),
            round(thickness_cm, 2))


def physical_course_candidates(solve_result):
    """Itera (course_index, candidate) só sobre o que REALMENTE seria
    materializado no Revit — `course_candidates`, já filtrado por
    `_drop_fill_colliding_with_ties` (regra 18.7) e pela variante física
    escolhida (seção 11.7 das REGRAS) — nunca `solve_result["candidates"]`
    bruto, que agrega TODAS as variantes/bandas juntas (nunca coexistem de
    verdade numa mesma fiada física)."""
    course_candidates = solve_result.get("course_candidates") or {}
    for course_index in sorted(course_candidates.keys()):
        for candidate in course_candidates[course_index]:
            yield course_index, candidate


def candidate_origin_cm(candidate):
    return xyz_to_cm(candidate["origin_world"])


def candidate_fingerprint_tuple(walls_to_create, course_index, candidate):
    """Fingerprint canônico de UMA peça: geometria da parede (não o índice),
    fiada, código, posição arredondada, orientação — pedido explícito do
    item 20 da missão ('wall geometry/reference, course, block code,
    posição longitudinal, orientação')."""
    wall_idx = candidate.get("wall_idx")
    wall_key = wall_geom_key(walls_to_create, wall_idx) if wall_idx is not None else None
    ox, oy = candidate_origin_cm(candidate)
    return (
        wall_key,
        course_index,
        candidate["logical_code"],
        round(ox, 1), round(oy, 1),
        round(candidate["rotation_deg"]) % 360,
    )


def project_fingerprint(walls_to_create, solve_result):
    """sha256 de todo o conjunto de peças materializadas (fingerprint do
    RESULTADO, análogo em espírito ao `solver_decision_fingerprint` já
    oficial, mas por peça física em vez de por decisão de tier — ver
    docs/BLOCK_MODULATION_AUDIT.md, seção Determinismo)."""
    rows = sorted(
        candidate_fingerprint_tuple(walls_to_create, course_index, candidate)
        for course_index, candidate in physical_course_candidates(solve_result)
    )
    blob = json.dumps(rows, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), len(rows)


def is_l_t_x(node):
    return node.get("kind") in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION")


def node_wall_indices(node):
    """Todos os wall_idx envolvidos num nó, cobrindo os 3 formatos usados
    pelo motor (arms= lista de (wall_idx, end_idx) para L; main/incoming
    para T; crossing_walls para X) — ver `build_wall_graph`/`solve_*` em
    `core/engine/wall_stepper.py`."""
    idxs = set()
    for arm in (node.get("arms") or []):
        if isinstance(arm, (list, tuple)) and arm:
            idxs.add(arm[0])
    for key in ("main_wall_idx", "incoming_wall_idx", "neighbor_wall_idx"):
        value = node.get(key)
        if value is not None:
            idxs.add(value)
    for value in (node.get("crossing_walls") or []):
        if isinstance(value, (list, tuple)) and value:
            idxs.add(value[0])
        elif value is not None:
            idxs.add(value)
    return sorted(idxs)


class RawJSONEncoder(json.JSONEncoder):
    """Serializa os pontos XYZ (stub do motor) e outros objetos não-nativos
    do jeito mais honesto possível — nunca usado para dados que já foram
    convertidos por `xyz_to_cm`/`wall_axis` (a via preferida); só como rede
    de segurança para não derrubar um dump por causa de um campo bruto."""

    def default(self, obj):
        if hasattr(obj, "X") and hasattr(obj, "Y"):
            try:
                return {"x_cm": round(obj.X * FT_TO_CM, 3),
                        "y_cm": round(obj.Y * FT_TO_CM, 3),
                        "z_cm": round(getattr(obj, "Z", 0.0) * FT_TO_CM, 3)}
            except Exception:
                pass
        return str(obj)


def write_json(path, payload):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2,
                   sort_keys=False, cls=RawJSONEncoder)
    return path


def out_path(*parts):
    return os.path.join(_HERE, *parts)


def wall_direction_cm(walls_to_create, wall_idx):
    p0_cm, p1_cm, length_cm, thickness_cm = wall_axis(walls_to_create, wall_idx)
    dx = p1_cm[0] - p0_cm[0]
    dy = p1_cm[1] - p0_cm[1]
    norm = math.hypot(dx, dy) or 1.0
    return p0_cm, p1_cm, (dx / norm, dy / norm), length_cm, thickness_cm


def candidate_dir_dot(candidate, wall_dir_xy):
    xd = candidate["x_dir"]
    return abs(xd.X * wall_dir_xy[0] + xd.Y * wall_dir_xy[1])


def opening_edges_cm(openings_for_wall):
    """Bordas (t_cm) de cada abertura de UMA parede — `openings_per_wall[i]`
    já vem em pés (t_start_ft, t_end_ft, sill_ft, head_ft)."""
    edges = []
    for t_start_ft, t_end_ft, _sill_ft, _head_ft in openings_for_wall:
        edges.append(ft_to_cm(t_start_ft))
        edges.append(ft_to_cm(t_end_ft))
    return edges


def wall_course_spans(walls_to_create, solve_result, only_parallel=True):
    """{(wall_idx, course_index): [span, ...]} — span = dict com t_start_cm,
    t_end_cm, t_center_cm, code, candidate, ordenado por t. Só peças
    paralelas ao eixo da própria parede entram por padrão (`only_parallel`)
    — é o que representa a sequência longitudinal de uma fiada; peças de nó
    perpendiculares ao eixo desta parede (mas com wall_idx apontando pra
    ela) são posicionadas no eixo da parede VIZINHA, não nesta."""
    spans = {}
    for course_index, candidate in physical_course_candidates(solve_result):
        wall_idx = candidate.get("wall_idx")
        if wall_idx is None:
            continue
        p0_cm, _p1_cm, wall_dir, _length_cm, _thick_cm = wall_direction_cm(walls_to_create, wall_idx)
        if only_parallel and candidate_dir_dot(candidate, wall_dir) < 0.99:
            continue
        ox, oy = candidate_origin_cm(candidate)
        t_center = (ox - p0_cm[0]) * wall_dir[0] + (oy - p0_cm[1]) * wall_dir[1]
        half = candidate["length_cm"] / 2.0
        spans.setdefault((wall_idx, course_index), []).append({
            "t_start_cm": t_center - half, "t_end_cm": t_center + half,
            "t_center_cm": t_center, "code": candidate["logical_code"],
            "candidate": candidate,
        })
    for key in spans:
        spans[key].sort(key=lambda s: s["t_center_cm"])
    return spans


def nearest_node_distance_cm(point_cm, nodes):
    best = None
    for node in nodes:
        node_cm = xyz_to_cm(node["point"])
        d = math.hypot(point_cm[0] - node_cm[0], point_cm[1] - node_cm[1])
        if best is None or d < best[0]:
            best = (d, node)
    return best if best is not None else (None, None)


def summarize_counter(counter):
    """dict {chave: contagem} ordenado por contagem desc, para relatório."""
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))))
