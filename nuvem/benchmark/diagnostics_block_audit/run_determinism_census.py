# -*- coding: utf-8 -*-
"""Censo independente — DETERMINISMO do solver de BLOCOS (missão CONTA 2,
seção 20). O motor de PAREDES já é determinístico (CR-2F-D, mergeado na
main que esta auditoria audita) — esta pergunta é sobre a camada de CIMA:
`solve_building_blocks_all_courses`.

Variações testadas (todas seguras/reversíveis, todas headless):
  - baseline: ordem original de `input.json["walls"]`;
  - `reversed`: lista de paredes invertida;
  - `shuffle-<seed>`: `random.Random(seed).shuffle`, mesmas seeds já usadas
    no censo de determinismo do motor de paredes (1, 2, 3, 10, 42) — só
    para comparabilidade entre os dois censos, não é o mesmo teste;
  - `endpoint-reversal`: start_cm/end_cm trocados em TODA parede (e as
    aberturas re-parametrizadas: `novo_t = comprimento - t_antigo`, com
    início/fim trocados) — mede se o sentido de desenho de cada eixo
    afeta o resultado.

Fingerprint: `lib_audit.project_fingerprint`, por peça física
materializada, chaveado pela GEOMETRIA da parede (não pelo índice — que
muda com a permutação), fiada, código, posição arredondada e orientação —
exatamente os campos pedidos no item 20 da missão.
"""
import copy
import random
import sys

import lib_audit as A

SEEDS = (1, 2, 3, 10, 42)


def _permuted_input(input_project, order):
    walls = input_project.get("walls") or []
    new_project = copy.deepcopy(input_project)
    new_project["walls"] = [copy.deepcopy(walls[i]) for i in order]
    return new_project


def _reversed_endpoints_input(input_project):
    new_project = copy.deepcopy(input_project)
    for wall in new_project.get("walls") or []:
        start_cm = wall["start_cm"]
        end_cm = wall["end_cm"]
        length_cm = ((end_cm[0] - start_cm[0]) ** 2 + (end_cm[1] - start_cm[1]) ** 2) ** 0.5
        wall["start_cm"], wall["end_cm"] = end_cm, start_cm
        new_openings = []
        for opening in wall.get("openings") or []:
            new_opening = dict(opening)
            new_opening["t_start_cm"] = length_cm - opening["t_end_cm"]
            new_opening["t_end_cm"] = length_cm - opening["t_start_cm"]
            new_openings.append(new_opening)
        wall["openings"] = new_openings
    return new_project


def _run_variant(project_id, name, input_project):
    run_data = A.run_solver(project_id, input_project=input_project)
    fp, n_pieces = A.project_fingerprint(run_data["walls_to_create"], run_data["solve_result"])
    return {
        "name": name,
        "fingerprint": fp,
        "n_pieces": n_pieces,
        "elapsed_s": round(run_data["elapsed_s"], 3),
        "n_walls": len(run_data["walls_to_create"]),
        "n_non_modular": len(run_data["solve_result"].get("non_modular") or []),
        "n_intersection_failures": len(run_data["solve_result"].get("intersection_failures") or []),
    }, run_data


def _locate_first_divergent_layer(baseline_run, other_run, other_name):
    """Quando dois fingerprints divergem, tenta localizar a PRIMEIRA camada
    que diverge: grafo de nos (contagem por tipo), depois candidatos
    agregados por parede (chaveados pela geometria da propria parede, nao
    pelo indice)."""
    b_kinds = {}
    for node in baseline_run["nodes"]:
        b_kinds[node["kind"]] = b_kinds.get(node["kind"], 0) + 1
    o_kinds = {}
    for node in other_run["nodes"]:
        o_kinds[node["kind"]] = o_kinds.get(node["kind"], 0) + 1
    if b_kinds != o_kinds:
        return {"layer": "wall_graph_nodes (L/T/X/FREE_END/...)",
                "baseline": b_kinds, other_name: o_kinds}

    def _pieces_by_wall_geom(run_data):
        out = {}
        for course_index, cand in A.physical_course_candidates(run_data["solve_result"]):
            key = A.wall_geom_key(run_data["walls_to_create"], cand.get("wall_idx"))
            out.setdefault(key, 0)
            out[key] += 1
        return out

    b_counts = _pieces_by_wall_geom(baseline_run)
    o_counts = _pieces_by_wall_geom(other_run)
    if b_counts != o_counts:
        diverging = [k for k in set(b_counts) | set(o_counts)
                     if b_counts.get(k, 0) != o_counts.get(k, 0)][:5]
        return {"layer": "piece_count_per_wall_geometry",
                "diverging_wall_keys_sample": diverging}
    return {"layer": "piece-level (posicao/codigo/rotacao) - contagens batem, "
                     "conteudo diverge - ver fingerprint por peca"}


def census(project_id=None):
    project_id = project_id or A.PRIMARY_PROJECT_ID
    input_project = A.load_input(project_id)

    baseline_summary, baseline_run = _run_variant(project_id, "baseline", input_project)

    variants = [("reversed", _permuted_input(input_project, list(reversed(range(len(input_project["walls"])))))),
                ("endpoint_reversal", _reversed_endpoints_input(input_project))]
    for seed in SEEDS:
        order = list(range(len(input_project["walls"])))
        random.Random(seed).shuffle(order)
        variants.append(("shuffle_seed_%d" % seed, _permuted_input(input_project, order)))

    results = [baseline_summary]
    runs_by_name = {"baseline": baseline_run}
    for name, proj in variants:
        summary, run_data = _run_variant(project_id, name, proj)
        results.append(summary)
        runs_by_name[name] = run_data

    fingerprints = sorted(set(r["fingerprint"] for r in results))
    divergences = []
    if len(fingerprints) > 1:
        for r in results[1:]:
            if r["fingerprint"] != baseline_summary["fingerprint"]:
                divergences.append({
                    "variant": r["name"],
                    "first_divergent_layer": _locate_first_divergent_layer(
                        baseline_run, runs_by_name[r["name"]], r["name"]),
                })

    return {
        "project_id": project_id,
        "runs": results,
        "distinct_fingerprints": len(fingerprints),
        "fingerprints": fingerprints,
        "deterministic": len(fingerprints) == 1,
        "divergences": divergences,
    }


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else A.PRIMARY_PROJECT_ID
    result = census(project_id)
    A.write_json(A.out_path("out_determinism_census.json"), result)
    print("distinct fingerprints:", result["distinct_fingerprints"], "deterministic=", result["deterministic"])
    for r in result["runs"]:
        print(" ", r["name"], r["fingerprint"][:16], "pieces=", r["n_pieces"])
    return result


if __name__ == "__main__":
    main()
