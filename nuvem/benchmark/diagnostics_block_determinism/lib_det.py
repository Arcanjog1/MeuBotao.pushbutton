# -*- coding: utf-8 -*-
"""Biblioteca do laboratorio do CR-BLOCK-DETERMINISM (CONTA 1).

Contrato desta pasta (`nuvem/benchmark/diagnostics_block_determinism/`):
  - so' LE o motor (`nuvem/core/**`) atraves de `benchmark.solver_bridge`;
    nenhum script daqui escreve fora desta pasta;
  - roda 100% headless sobre os projetos versionados em
    `nuvem/benchmark/projects/` (via `tests/revit_stubs.py`);
  - todo fingerprint definido aqui e' CANONICO: nao pode depender de
    `wall_idx`, da ordem da lista de paredes, do sentido de desenho de um
    eixo, de `id()` nem da ordem de iteracao de um dict.

A diferenca para `diagnostics_block_audit/lib_audit.py` (CONTA 2, so'
leitura, nao alterar) e' o nivel: la' o fingerprint e' do RESULTADO final
(pecas materializadas); aqui ha' fingerprint POR CAMADA do pipeline
(paredes de entrada -> grafo -> nos -> end_to_node -> blocos), para poder
localizar a PRIMEIRA camada que diverge, que e' o que este CR pede.
"""

import os
import sys
import json
import math
import time
import copy
import random
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_NUVEM_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _NUVEM_DIR not in sys.path:
    sys.path.insert(0, _NUVEM_DIR)

from benchmark import solver_bridge  # noqa: E402
from benchmark import runner as bench_runner  # noqa: E402

FEET_PER_METER = 1.0 / 0.3048
FT_TO_CM = 100.0 * 0.3048

PRIMARY_PROJECT_ID = "torre_easy_lo_r00_tgd"
PROJECT_IDS = ("piloto_sintetico_2x2", "torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1")

SEEDS = (1, 2, 3, 10, 42)

# Casas decimais das chaves canonicas. 2 casas de CM = 0,1 mm: MUITO mais
# fino que qualquer tolerancia do motor (a menor e' 5 cm, o snap de no'),
# entao arredondar aqui NAO cria nem desfaz encontro nenhum - so' garante
# que o mesmo ponto geometrico vira a mesma string em duas execucoes.
# Nao e' tolerancia nova: e' precisao de IMPRESSAO.
CANON_DECIMALS = 2


def engine():
    return solver_bridge.engine()


def load_input(project_id):
    paths = bench_runner.project_paths(project_id)
    with open(paths["input"], "r", encoding="utf-8") as handle:
        return json.load(handle)


def out_path(*parts):
    return os.path.join(_HERE, *parts)


def write_json(path, payload):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
    return path


def sha(rows):
    blob = json.dumps(rows, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


# ----------------------------------------------------------------------
# Chaves canonicas (funcoes puras, sem indice/ordem/id())
# ----------------------------------------------------------------------

def r(value):
    # `+ 0.0` normaliza -0.0 -> 0.0 (senao o mesmo ponto vira duas chaves).
    return round(float(value), CANON_DECIMALS) + 0.0


def pt_cm(point):
    """XYZ (pes) -> (x_cm, y_cm) canonico."""
    return (r(point.X * FT_TO_CM), r(point.Y * FT_TO_CM))


def canonical_wall_key(walls_to_create, wall_idx):
    """Identidade GEOMETRICA de uma parede: pontas ordenadas + espessura.
    Independe do indice na lista e do sentido do desenho."""
    if wall_idx is None or not (0 <= wall_idx < len(walls_to_create)):
        return None
    line, thickness_ft, _locks = walls_to_create[wall_idx]
    a = pt_cm(line.GetEndPoint(0))
    b = pt_cm(line.GetEndPoint(1))
    lo, hi = (a, b) if a <= b else (b, a)
    return (lo[0], lo[1], hi[0], hi[1], r(thickness_ft * FT_TO_CM))


def canonical_arm_key(walls_to_create, wall_idx, end_index):
    """Identidade GEOMETRICA de uma PONTA de parede: a parede canonica +
    QUAL das duas pontas dela, dita pela POSICAO da ponta (nao por
    end_index, que troca de valor quando o eixo e' desenhado ao contrario).
    `0` = a ponta que fica no extremo `lo` da chave canonica da parede."""
    if wall_idx is None or not (0 <= wall_idx < len(walls_to_create)):
        return None
    line, _thickness_ft, _locks = walls_to_create[wall_idx]
    a = pt_cm(line.GetEndPoint(0))
    b = pt_cm(line.GetEndPoint(1))
    mine = a if end_index == 0 else b
    lo = a if a <= b else b
    return (canonical_wall_key(walls_to_create, wall_idx), 0 if mine == lo else 1)


def canonical_node_key(walls_to_create, node):
    """Identidade GEOMETRICA de um NO': posicao XY canonica + tipo + o
    conjunto ORDENADO de braços incidentes (cada um pela sua chave
    canonica) + as paredes de papel especial (main/incoming/neighbor/
    crossing) por chave canonica, nunca por indice."""
    arms = sorted(
        k for k in (canonical_arm_key(walls_to_create, w, e)
                    for w, e in (node.get("arms") or []))
        if k is not None
    )
    crossing = sorted(
        k for k in (canonical_wall_key(walls_to_create, w)
                    for w in (node.get("crossing_walls") or []))
        if k is not None
    )
    return {
        "point_cm": pt_cm(node["point"]),
        "kind": node.get("kind"),
        "arms": arms,
        "main_wall": canonical_wall_key(walls_to_create, node.get("main_wall_idx")),
        "incoming_wall": canonical_wall_key(walls_to_create, node.get("incoming_wall_idx")),
        "neighbor_wall": canonical_wall_key(walls_to_create, node.get("neighbor_wall_idx")),
        "crossing_walls": crossing,
        "is_midspan": not (node.get("arms") or []),
    }


def canonical_node_identity(walls_to_create, node):
    """SO' a identidade do LUGAR (posicao + quem participa), SEM o tipo -
    para poder perguntar 'o mesmo no' geometrico foi classificado
    igual?' em vez de so' comparar contagens (item 15 da missao)."""
    key = canonical_node_key(walls_to_create, node)
    return (key["point_cm"], tuple(key["arms"]), tuple(key["crossing_walls"]))


# ----------------------------------------------------------------------
# Fingerprints por camada
# ----------------------------------------------------------------------

def fp_input_walls(walls_to_create):
    """Camada 0: o conjunto de paredes que ENTRA no build_wall_graph."""
    return sha(sorted(canonical_wall_key(walls_to_create, i)
                      for i in range(len(walls_to_create))))


def fp_nodes(walls_to_create, nodes):
    return sha(sorted(json.dumps(canonical_node_key(walls_to_create, n),
                                 sort_keys=True, default=str)
                      for n in nodes))


def fp_node_classifications(walls_to_create, nodes):
    """So' identidade -> tipo. Isola 'classificou diferente' de 'achou
    nos diferentes'."""
    return sha(sorted(
        [str(canonical_node_identity(walls_to_create, n)), n.get("kind")]
        for n in nodes))


def fp_end_to_node(walls_to_create, nodes, end_to_node):
    """`end_to_node` por identidade geometrica dos dois lados: a PONTA
    canonica -> a IDENTIDADE canonica do no' em que ela esta' (nunca o
    indice do no' na lista, que muda com a ordem de descoberta)."""
    rows = []
    for (wall_idx, end_index), node_index in end_to_node.items():
        arm = canonical_arm_key(walls_to_create, wall_idx, end_index)
        node_id = canonical_node_identity(walls_to_create, nodes[node_index])
        rows.append([str(arm), str(node_id)])
    return sha(sorted(rows))


def fp_midspan(walls_to_create, nodes):
    rows = []
    for node in nodes:
        if node.get("arms"):
            continue
        rows.append([str(pt_cm(node["point"])),
                     str(sorted(k for k in (canonical_wall_key(walls_to_create, w)
                                            for w in (node.get("crossing_walls") or []))
                                if k is not None))])
    return sha(sorted(rows))


def fp_ltx_reservations(walls_to_create, nodes):
    """Reservas L/T/X: so' os nos de amarracao, com os papeis de cada
    parede - e' o que a Etapa 4 consome para reservar B34/B54."""
    rows = []
    for node in nodes:
        kind = node.get("kind")
        if kind not in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
            continue
        key = canonical_node_key(walls_to_create, node)
        rows.append(json.dumps(key, sort_keys=True, default=str))
    return sha(sorted(rows))


def fp_blocks(walls_to_create, solve_result):
    """Fingerprint final das PECAS materializadas, por geometria da
    parede (mesmo espirito do fingerprint da CONTA 2, redefinido aqui
    para esta pasta ser autocontida)."""
    rows = []
    course_candidates = solve_result.get("course_candidates") or {}
    for course_index in sorted(course_candidates.keys()):
        for cand in course_candidates[course_index]:
            origin = cand["origin_world"]
            rows.append([
                str(canonical_wall_key(walls_to_create, cand.get("wall_idx"))),
                course_index,
                cand["logical_code"],
                r(origin.X * FT_TO_CM), r(origin.Y * FT_TO_CM),
                round(cand["rotation_deg"]) % 360,
            ])
    return sha(sorted(rows, key=str)), len(rows)


def fp_candidates(walls_to_create, solve_result):
    """Camada de CANDIDATOS brutos (todas as variantes/bandas), antes da
    escolha da variante fisica."""
    rows = []
    for cand in (solve_result.get("candidates") or []):
        origin = cand.get("origin_world")
        rows.append([
            str(canonical_wall_key(walls_to_create, cand.get("wall_idx"))),
            cand.get("course_index"),
            cand.get("logical_code"),
            r(origin.X * FT_TO_CM) if origin is not None else None,
            r(origin.Y * FT_TO_CM) if origin is not None else None,
        ])
    return sha(sorted(rows, key=str)), len(rows)


# ----------------------------------------------------------------------
# Variantes de entrada (as 8 do CR)
# ----------------------------------------------------------------------

def permuted_input(input_project, order):
    walls = input_project.get("walls") or []
    new_project = copy.deepcopy(input_project)
    new_project["walls"] = [copy.deepcopy(walls[i]) for i in order]
    return new_project


def reversed_endpoints_input(input_project):
    new_project = copy.deepcopy(input_project)
    for wall in new_project.get("walls") or []:
        start_cm = wall["start_cm"]
        end_cm = wall["end_cm"]
        length_cm = math.hypot(end_cm[0] - start_cm[0], end_cm[1] - start_cm[1])
        wall["start_cm"], wall["end_cm"] = end_cm, start_cm
        new_openings = []
        for opening in wall.get("openings") or []:
            new_opening = dict(opening)
            new_opening["t_start_cm"] = length_cm - opening["t_end_cm"]
            new_opening["t_end_cm"] = length_cm - opening["t_start_cm"]
            new_openings.append(new_opening)
        wall["openings"] = new_openings
    return new_project


def build_variants(input_project):
    """As 8 execucoes do CR, na ordem em que o enunciado as lista."""
    n = len(input_project.get("walls") or [])
    variants = [("baseline", input_project),
                ("reversed", permuted_input(input_project, list(reversed(range(n))))),
                ("endpoint_reversal", reversed_endpoints_input(input_project))]
    for seed in SEEDS:
        order = list(range(n))
        random.Random(seed).shuffle(order)
        variants.append(("shuffle_seed_%d" % seed, permuted_input(input_project, order)))
    return variants


# ----------------------------------------------------------------------
# Execucao instrumentada
# ----------------------------------------------------------------------

def plan_only(input_project):
    """So' a Fase A (ate' o grafo), cronometrada separadamente."""
    t0 = time.perf_counter()
    nodes, walls_to_create, end_to_node, openings_per_wall = \
        solver_bridge.plan_from_input(input_project)
    elapsed = time.perf_counter() - t0
    return {
        "nodes": nodes,
        "walls_to_create": walls_to_create,
        "end_to_node": end_to_node,
        "openings_per_wall": openings_per_wall,
        "plan_elapsed_s": elapsed,
    }


def graph_layers(plan_data):
    walls = plan_data["walls_to_create"]
    nodes = plan_data["nodes"]
    kinds = {}
    for node in nodes:
        kinds[node.get("kind")] = kinds.get(node.get("kind"), 0) + 1
    return {
        "fp_input_walls": fp_input_walls(walls),
        "fp_nodes": fp_nodes(walls, nodes),
        "fp_node_classifications": fp_node_classifications(walls, nodes),
        "fp_end_to_node": fp_end_to_node(walls, nodes, plan_data["end_to_node"]),
        "fp_midspan": fp_midspan(walls, nodes),
        "fp_ltx_reservations": fp_ltx_reservations(walls, nodes),
        "n_walls": len(walls),
        "n_nodes": len(nodes),
        "kinds": dict(sorted(kinds.items())),
        "plan_elapsed_s": round(plan_data["plan_elapsed_s"], 4),
    }


def run_full(input_project):
    """Pipeline COMPLETO (Fase A + solver de blocos), com os dois tempos
    medidos separadamente e `end_to_node` preservado (o `run_solver` do
    `solver_bridge` nao o devolve, e este CR precisa dele)."""
    module = engine()
    plan_data = plan_only(input_project)
    nodes = plan_data["nodes"]
    walls_to_create = plan_data["walls_to_create"]
    end_to_node = plan_data["end_to_node"]
    openings_per_wall = plan_data["openings_per_wall"]

    catalog, _cells, _dropped = solver_bridge.catalog_from_input(input_project)
    settings = input_project.get("settings") or {}
    base_z_ft = float(settings.get("base_z_cm") or 0.0) / 100.0 * FEET_PER_METER
    num_courses = int(settings.get("num_courses")
                      or settings.get("expected_rows") or 15)

    t0 = time.perf_counter()
    solve_result = module.solve_building_blocks_all_courses(
        nodes, walls_to_create, end_to_node, openings_per_wall, catalog,
        base_z_ft, num_courses,
        variants_per_course=module.PIER_LAYOUT_VARIANTS_PER_COURSE,
    )
    solve_elapsed = time.perf_counter() - t0

    plan_data["solve_result"] = solve_result
    plan_data["solve_elapsed_s"] = solve_elapsed
    plan_data["num_courses"] = num_courses
    return plan_data


def block_layers(run_data):
    walls = run_data["walls_to_create"]
    solve_result = run_data["solve_result"]
    fp_b, n_pieces = fp_blocks(walls, solve_result)
    fp_c, n_cands = fp_candidates(walls, solve_result)
    return {
        "fp_blocks": fp_b,
        "n_pieces": n_pieces,
        "fp_candidates": fp_c,
        "n_candidates": n_cands,
        "n_non_modular": len(solve_result.get("non_modular") or []),
        "n_intersection_failures": len(solve_result.get("intersection_failures") or []),
        "n_alignment_conflicts": len(solve_result.get("alignment_conflicts") or []),
        "n_collisions": len(solve_result.get("collisions") or []),
        "n_door_void_violations": len(solve_result.get("door_void_violations") or []),
        "solve_elapsed_s": round(run_data["solve_elapsed_s"], 4),
    }


# Ordem em que as camadas sao comparadas para achar a PRIMEIRA divergencia.
LAYER_ORDER = (
    "fp_input_walls",
    "fp_nodes",
    "fp_node_classifications",
    "fp_end_to_node",
    "fp_midspan",
    "fp_ltx_reservations",
    "fp_candidates",
    "fp_blocks",
)


def first_divergent_layer(baseline_layers, other_layers):
    for name in LAYER_ORDER:
        if name in baseline_layers and name in other_layers:
            if baseline_layers[name] != other_layers[name]:
                return name
    return None
