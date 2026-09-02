# -*- coding: utf-8 -*-
"""Censo independente — encontros L / T / X (missão CONTA 2, seções 14-16).

Fonte primária: o grafo `nodes` (Fase A, `build_wall_graph` — mesma
estrutura para TODO projeto, não depende do solver de blocos) cruzado com
o resultado REAL do solver (`solve_result["course_candidates"]`,
`intersection_failures`, `collisions`, `wall_bond_audits`).

Para uma amostra de nós de cada tipo, este script também RE-INVOCA
diretamente `solve_l_corner` / `solve_t_intersection` / `solve_x_intersection`
e `validate_l_corner` / `validate_t_intersection` / `validate_x_intersection`
(as próprias funções de produção, só como OBJETO DE ESTUDO — nenhuma delas é
modificada) para uma segunda leitura independente da primeira: confirmar que
o que `course_candidates` mostra é exatamente o que o solver de nós geraria
isoladamente, e capturar 1-2 exemplos mínimos reproduzíveis de cada tipo de
falha encontrada.
"""
import sys

import lib_audit as A


def _classify_reason(reason):
    if reason is None:
        return "NONE"
    if "DEGRADED" in reason:
        return "DEGRADED"
    return "TRUE"


def _node_reasons(node_index, solve_result):
    reasons = set()
    for _course_index, candidate in A.physical_course_candidates(solve_result):
        if candidate.get("node_index") == node_index:
            reasons.add(candidate.get("placement_reason"))
    return reasons


def _resolve_and_validate_sample(kind, node, node_index, run_data, engine, sample_out, limit=6):
    if len(sample_out) >= limit:
        return
    walls_to_create = run_data["walls_to_create"]
    catalog = run_data["catalog"]
    openings_per_wall = run_data["openings_per_wall"]
    nodes = run_data["nodes"]
    end_to_node = None  # solve_* aceita end_to_node=None (usado só por alguns ramos)
    try:
        if kind == "L_CORNER":
            res = engine.solve_l_corner(node, walls_to_create, catalog, node_index=node_index,
                                        openings_per_wall=openings_per_wall)
        elif kind == "T_INTERSECTION":
            res = engine.solve_t_intersection(node, walls_to_create, catalog, node_index=node_index,
                                              openings_per_wall=openings_per_wall,
                                              nodes=nodes, end_to_node=end_to_node)
        else:
            res = engine.solve_x_intersection(node, walls_to_create, catalog, node_index=node_index,
                                              openings_per_wall=openings_per_wall)
    except Exception as exc:  # nunca engolir - registra o erro cru
        sample_out.append({"node_index": node_index, "kind": kind, "call_error": repr(exc)})
        return

    degraded = res.get("degraded", False)
    entry = {"node_index": node_index, "kind": kind, "ok": res.get("ok"),
              "reason": res.get("reason"), "degraded": degraded}
    course_a, course_b = res.get("course_a"), res.get("course_b")
    if course_a is not None and course_b is not None:
        # REGRAS_MODULACAO_BLOCOS.md secao 5, Nivel 2: um T degradado vira,
        # na pratica, um canto em L (2x B34) - a prova geometrica correta
        # para ele e' `validate_l_corner`, NAO `validate_t_intersection`
        # (que exige B54+B34, o padrao do T VERDADEIRO). Confirmado ao
        # tentar as duas: validate_t_intersection reprova (corretamente,
        # por nao ser um T) todo T degradado quando aplicada sem essa
        # distincao - nao e' um defeito do solver, e' o validador errado
        # para o caso.
        validator_name = "validate_l_corner" if (kind == "T_INTERSECTION" and degraded) else {
            "L_CORNER": "validate_l_corner",
            "T_INTERSECTION": "validate_t_intersection",
            "X_INTERSECTION": "validate_x_intersection",
        }[kind]
        try:
            valid = getattr(engine, validator_name)(course_a, course_b)
            entry["independent_validation"] = valid
            entry["independent_validation_used"] = validator_name
        except Exception as exc:
            entry["independent_validation_error"] = repr(exc)
    sample_out.append(entry)


def census(run_data):
    nodes = run_data["nodes"]
    solve_result = run_data["solve_result"]
    engine = A.engine()

    by_kind = {}
    for idx, node in enumerate(nodes):
        by_kind.setdefault(node["kind"], []).append(idx)

    # `intersection_failures` e' uma lista de tuplas (node_index, motivo) -
    # ver `solve_all_intersections` em core/engine/wall_stepper.py.
    failures = solve_result.get("intersection_failures") or []
    failures_by_kind = {}
    for f in failures:
        node_index, reason_text = f[0], f[1]
        kind = nodes[node_index]["kind"] if node_index is not None and node_index < len(nodes) else "UNKNOWN"
        failures_by_kind.setdefault(kind, []).append({"node_index": node_index, "reason": reason_text})

    collisions = solve_result.get("collisions") or []
    all_candidates = solve_result.get("candidates") or []
    node_touching_collisions = 0
    for a_i, b_i in collisions:
        ca, cb = all_candidates[a_i], all_candidates[b_i]
        if ca.get("node_index") is not None or cb.get("node_index") is not None:
            node_touching_collisions += 1

    result = {}
    for kind in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
        node_idxs = by_kind.get(kind, [])
        reason_counts = {}
        for node_index in node_idxs:
            for reason in _node_reasons(node_index, solve_result):
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        classified = {"TRUE": 0, "DEGRADED": 0, "NONE_NO_CANDIDATE": 0}
        for node_index in node_idxs:
            reasons = _node_reasons(node_index, solve_result)
            if not reasons:
                classified["NONE_NO_CANDIDATE"] += 1
            elif any(_classify_reason(r) == "TRUE" for r in reasons):
                classified["TRUE"] += 1
            else:
                classified["DEGRADED"] += 1

        sample = []
        for node_index in node_idxs[:8]:
            _resolve_and_validate_sample(kind, nodes[node_index], node_index, run_data, engine, sample)
        for f in (failures_by_kind.get(kind) or [])[:3]:
            node_index = f.get("node_index")
            if node_index is not None:
                _resolve_and_validate_sample(kind, nodes[node_index], node_index, run_data, engine,
                                             sample, limit=len(sample) + 1)

        kind_failures = failures_by_kind.get(kind) or []
        unique_failing_nodes = sorted(set(f["node_index"] for f in kind_failures))
        result[kind] = {
            "total_nodes": len(node_idxs),
            "placement_reason_histogram": reason_counts,
            "classified": classified,
            "failure_entries_reported_by_solver": len(kind_failures),
            "note_failure_entries": ("cada entrada de intersection_failures e' por "
                                      "TENTATIVA (courso/banda), um mesmo no' pode "
                                      "aparecer mais de uma vez - ver unique_nodes_with_failure"),
            "unique_nodes_with_failure": len(unique_failing_nodes),
            "failures_sample": kind_failures[:10],
            "independent_resolve_and_validate_sample": sample,
        }

    result["_meta"] = {
        "total_nodes": len(nodes),
        "kinds_histogram": {k: len(v) for k, v in by_kind.items()},
        "total_collisions": len(collisions),
        "collisions_touching_a_node_piece": node_touching_collisions,
        "total_intersection_failures": len(failures),
    }
    return result


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else A.PRIMARY_PROJECT_ID
    run_data = A.run_solver(project_id)
    result = census(run_data)
    result["project_id"] = project_id
    A.write_json(A.out_path("out_intersection_census.json"), result)
    for kind in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
        print(kind, result[kind]["total_nodes"], result[kind]["classified"],
              "unique_failing=", result[kind]["unique_nodes_with_failure"])
    print("collisions touching node piece:", result["_meta"]["collisions_touching_a_node_piece"],
          "/", result["_meta"]["total_collisions"])
    return result


if __name__ == "__main__":
    main()
