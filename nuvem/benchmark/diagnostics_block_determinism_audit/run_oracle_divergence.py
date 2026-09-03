# -*- coding: utf-8 -*-
"""Localiza os nós GEOMÉTRICOS que mudam conforme a ordem de entrada, e
arbitra cada um com o oráculo independente (missão itens 8, 9, 10).

Passos:
  1. Roda baseline + a mesma bateria de `variants.build_all_variants`.
  2. Casa nós entre execuções por IDENTIDADE GEOMÉTRICA estável
     (`node_identity` = tipo + conjunto de chaves de parede dos braços —
     NUNCA a posição do nó em si, que é justamente o que pode divergir).
  3. Para cada identidade cujo PONTO ou TIPO muda entre execuções, grava
     uma entrada em `out_divergent_nodes.json` com a classificação
     independente do `oracle` em cada ponto candidato observado.
  4. Roda o experimento de "sort falso" (item 10): entrada ordenada por
     uma chave geométrica canônica, repetida váras vezes — se o
     fingerprint global bater sempre, marca CANONICAL_SORT_MAKES_REPEATABLE
     = true, e compara os nós desse resultado com o oráculo (repetível não
     é o mesmo que correto).

Uso:
    python3 run_oracle_divergence.py [project_id]

Saída: `out_divergent_nodes.json`, `out_canonical_sort_experiment.json`.
"""
import sys

import lib_det as L
import oracle as O
import variants as V


def _node_identity(node, walls):
    """Identidade ESTÁVEL de um nó através de execuções: tipo + conjunto
    de chaves geométricas das paredes que chegam nele. Nunca a posição
    (é o que pode divergir) nem wall_idx/node_index (mudam com a ordem)."""
    _point, arm_keys = L.node_geom_key(node, walls)
    return (node.get("kind"), arm_keys)


def _collect_nodes_by_identity(run_data):
    walls = run_data["walls_to_create"]
    out = {}
    for node in run_data["nodes"]:
        identity = _node_identity(node, walls)
        out.setdefault(identity, []).append({
            "point_cm": L.node_point_key(node),
            "kind": node.get("kind"),
        })
    return out


def _run_all(project_id):
    input_project = L.load_input(project_id)
    baseline_run = L.run_solver(project_id, input_project=input_project)
    runs = {"baseline": baseline_run}
    for name, proj in V.build_all_variants(input_project):
        runs[name] = L.run_solver(project_id, input_project=proj)
    return runs


def find_divergent_nodes(runs):
    """Para cada identidade de nó vista em QUALQUER execução, junta os
    (ponto, tipo) observados em cada variante. Diverge se há mais de um
    ponto distinto (tolerância `lib_det.GEOM_ROUND_CM`) OU mais de um tipo."""
    by_identity_per_run = dict((name, _collect_nodes_by_identity(run))
                                for name, run in runs.items())

    all_identities = set()
    for per_run in by_identity_per_run.values():
        all_identities.update(per_run.keys())

    divergent = []
    for identity in sorted(all_identities, key=lambda k: (str(k[0]), str(k[1]))):
        observed_by_variant = {}
        points = set()
        kinds = set()
        for name, per_run in by_identity_per_run.items():
            entries = per_run.get(identity)
            if not entries:
                observed_by_variant[name] = None
                continue
            # normalmente 1 entrada por identidade; se >1 (colisao rara de
            # identidade), pega a primeira e registra a colisao.
            entry = entries[0]
            observed_by_variant[name] = entry
            points.add(entry["point_cm"])
            kinds.add(entry["kind"])
        missing = [name for name, v in observed_by_variant.items() if v is None]
        if len(points) <= 1 and len(kinds) <= 1 and not missing:
            continue
        divergent.append({
            "identity_kind": identity[0],
            "identity_arm_wall_keys": identity[1],
            "n_distinct_points": len(points),
            "n_distinct_kinds": len(kinds),
            "missing_in_variants": missing,
            "observed_by_variant": observed_by_variant,
        })
    return divergent


def _oracle_verdict_for_divergent_node(entry, wall_geom_rows):
    """Roda o oráculo em CADA ponto distinto observado para esta
    identidade de nó (missão item 8/9) — devolve o que o oráculo acha de
    cada um, para o relatório apontar qual(is) execução(ões) bateu(ram)
    com uma reconstrução geometrica independente."""
    points_seen = {}
    for _name, obs in entry["observed_by_variant"].items():
        if obs is None:
            continue
        points_seen.setdefault(obs["point_cm"], obs["kind"])

    verdicts = []
    for point_cm, engine_kind in points_seen.items():
        oracle_result = O.classify_point(O.walls_from_geom_rows(wall_geom_rows), point_cm)
        verdicts.append({
            "point_cm": point_cm,
            "engine_kind_at_this_point": engine_kind,
            "oracle_kind": oracle_result["kind"],
            "oracle_reason": oracle_result["reason"],
            "agrees_with_engine": oracle_result["kind"] == engine_kind,
        })
    return verdicts


def _possible_cause(entry):
    if entry["missing_in_variants"]:
        return ("no' com este conjunto de paredes nao foi encontrado em %d variante(s) - "
                "possivel dependencia de ORDEM na propria clusterizacao/pareamento de "
                "pontas (Etapa 2), nao so' na posicao final" % len(entry["missing_in_variants"]))
    if entry["n_distinct_kinds"] > 1:
        return ("mesma parede-conjunto, TIPO de no' diferente entre ordens - "
                "reclassificacao (ex.: L_CORNER vs AMBIGUOUS) dependente de ordem, "
                "provavel tolerancia geometrica no limite (quase-colinear/quase-perpendicular) "
                "decidida de formas diferentes conforme a ordem de agrupamento")
    return ("mesmo conjunto de paredes e mesmo TIPO, mas POSICAO do no' muda entre ordens - "
            "provavel nao-associatividade de ponto flutuante na media/centroide do cluster de "
            "pontas (Etapa 2), sensivel a ordem de agrupamento")


def build_divergent_report(runs):
    baseline_walls = runs["baseline"]["walls_to_create"]
    wall_geom_rows = L.all_wall_geom_keys(baseline_walls)
    divergent = find_divergent_nodes(runs)

    out_entries = []
    for entry in divergent:
        verdicts = _oracle_verdict_for_divergent_node(entry, wall_geom_rows)
        out_entries.append({
            "identity_kind": entry["identity_kind"],
            "identity_arm_wall_keys": entry["identity_arm_wall_keys"],
            "n_distinct_points": entry["n_distinct_points"],
            "n_distinct_kinds": entry["n_distinct_kinds"],
            "missing_in_variants": entry["missing_in_variants"],
            "engine_classification_by_variant": dict(
                (name, (obs["kind"] if obs else None))
                for name, obs in entry["observed_by_variant"].items()
            ),
            "oracle_verdicts_per_observed_point": verdicts,
            "possible_cause": _possible_cause(entry),
        })
    return out_entries


def canonical_sort_experiment(project_id, repeats=5):
    """Item 10 da missão: entrada ordenada por chave geométrica CANÔNICA,
    repetida `repeats` vezes seguidas. Se o fingerprint global bater
    sempre, marca CANONICAL_SORT_MAKES_REPEATABLE=true — mas isso não
    prova correção: compara os nós desse resultado com o oráculo."""
    input_project = L.load_input(project_id)
    sorted_project = V.geometric_sort(input_project, reverse=False)

    fingerprints = []
    last_run = None
    for _i in range(repeats):
        run_data = L.run_solver(project_id, input_project=sorted_project)
        layers, _rows = L.layered_fingerprints(run_data)
        fingerprints.append(layers["global_result"]["fingerprint"])
        last_run = run_data

    repeatable = len(set(fingerprints)) == 1

    walls = last_run["walls_to_create"]
    wall_geom_rows = L.all_wall_geom_keys(walls)
    oracle_results = O.classify_all(wall_geom_rows)
    oracle_by_point = {}
    for r in oracle_results:
        oracle_by_point[(round(r["point_cm"][0], 1), round(r["point_cm"][1], 1))] = r["kind"]

    node_agreement = {"agree": 0, "disagree": 0, "no_oracle_point_nearby": 0}
    disagreements = []
    for node in last_run["nodes"]:
        p = L.node_point_key(node)
        best = None
        for op, kind in oracle_by_point.items():
            d = ((op[0] - p[0]) ** 2 + (op[1] - p[1]) ** 2) ** 0.5
            if d <= 10.0 and (best is None or d < best[0]):
                best = (d, kind)
        if best is None:
            node_agreement["no_oracle_point_nearby"] += 1
            continue
        if best[1] == node.get("kind"):
            node_agreement["agree"] += 1
        else:
            node_agreement["disagree"] += 1
            if len(disagreements) < 40:
                disagreements.append({
                    "point_cm": p, "engine_kind": node.get("kind"),
                    "oracle_kind": best[1], "oracle_dist_cm": round(best[0], 2),
                })

    return {
        "project_id": project_id,
        "repeats": repeats,
        "fingerprints": fingerprints,
        "CANONICAL_SORT_MAKES_REPEATABLE": repeatable,
        "note": ("repetivel != correto - ver node_agreement_with_oracle abaixo "
                 "para saber se o resultado (mesmo estavel) bate com uma "
                 "reconstrucao geometrica independente"),
        "node_agreement_with_oracle": node_agreement,
        "sample_disagreements": disagreements,
    }


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID

    print("rodando bateria completa para localizar nos divergentes...")
    runs = _run_all(project_id)
    divergent_report = build_divergent_report(runs)
    L.write_json(L.out_path("out_divergent_nodes.json"), {
        "project_id": project_id,
        "n_variants": len(runs),
        "variant_names": sorted(runs.keys()),
        "n_divergent_node_identities": len(divergent_report),
        "divergent_nodes": divergent_report,
    })
    print("nos divergentes (identidade geometrica estavel):", len(divergent_report))
    kinds_of_divergence = {}
    for e in divergent_report:
        if e["missing_in_variants"]:
            k = "missing_in_some_variant"
        elif e["n_distinct_kinds"] > 1:
            k = "kind_changes"
        else:
            k = "position_only_changes"
        kinds_of_divergence[k] = kinds_of_divergence.get(k, 0) + 1
    print("  por causa:", kinds_of_divergence)

    print()
    print("rodando experimento de canonical-sort (item 10)...")
    sort_result = canonical_sort_experiment(project_id)
    L.write_json(L.out_path("out_canonical_sort_experiment.json"), sort_result)
    print("CANONICAL_SORT_MAKES_REPEATABLE =", sort_result["CANONICAL_SORT_MAKES_REPEATABLE"])
    print("node_agreement_with_oracle:", sort_result["node_agreement_with_oracle"])


if __name__ == "__main__":
    main()
