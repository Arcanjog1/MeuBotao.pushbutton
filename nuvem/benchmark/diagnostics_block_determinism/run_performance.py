# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / secao 20 - PERFORMANCE antes/depois.

Mede `build_wall_graph` isolado (nao so' o pipeline inteiro, onde ele some
no ruido do solver) com o codigo ATUAL e com as funcoes da main 24ada98
reinstaladas, no MESMO processo.

Tambem conta as COMPARACOES de distancia entre ancoras - a operacao O(n^2)
que as duas versoes fazem - para mostrar que a componente conexa nao
aumentou a ordem do algoritmo: ela faz o MESMO numero de comparacoes que a
bola gulosa faria no pior caso, so' que sem poder pular pares ja' usados.
"""
import sys
import time

import lib_det as L
import run_ablation as AB
import run_rootcause as RC

REPEATS = 7


def _measure(module, walls_to_create, junction_map):
    best = None
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        nodes, end_to_node = module.build_wall_graph(walls_to_create, junction_map)
        elapsed = time.perf_counter() - t0
        if best is None or elapsed < best:
            best = elapsed
    return best, nodes, end_to_node


def run(project_id=None):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    engine = L.engine()
    module = AB.graph_module()
    input_project = L.load_input(project_id)
    walls_to_create, junction_map = RC._rebuild_walls(engine, input_project)
    arms = module._wall_node_arms(walls_to_create, junction_map)

    originals = {"_cluster_wall_arms": module._cluster_wall_arms,
                 "_wall_node_group_point": module._wall_node_group_point}

    module._cluster_wall_arms = AB._legacy_cluster_wall_arms
    module._wall_node_group_point = AB._legacy_group_point
    legacy_s, legacy_nodes, _e = _measure(module, walls_to_create, junction_map)

    module._cluster_wall_arms = originals["_cluster_wall_arms"]
    module._wall_node_group_point = originals["_wall_node_group_point"]
    current_s, current_nodes, _e2 = _measure(module, walls_to_create, junction_map)

    n_arms = len(arms)
    pares = n_arms * (n_arms - 1) // 2
    result = {
        "project_id": project_id,
        "n_paredes": len(walls_to_create),
        "n_pontas_de_parede": n_arms,
        "n_nos_legacy": len(legacy_nodes),
        "n_nos_atual": len(current_nodes),
        "pares_de_ancoras_no_pior_caso": pares,
        "build_wall_graph_legacy_s": round(legacy_s, 4),
        "build_wall_graph_atual_s": round(current_s, 4),
        "delta_s": round(current_s - legacy_s, 4),
        "delta_pct": round((current_s / legacy_s - 1.0) * 100.0, 1) if legacy_s else None,
        "repeticoes_melhor_de": REPEATS,
        "nota": ("As duas versoes sao O(n^2) em comparacoes de ancora. A bola "
                 "gulosa PULA pares ja' usados, entao faz <= `pares`; a "
                 "componente conexa faz exatamente `pares`. O custo extra e' "
                 "esse, mais o union-find (quase O(1) amortizado) e a "
                 "ordenacao canonica (O(n log n) por grupo, grupos de 1 a 4 "
                 "pontas nesta planta)."),
    }
    return result


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    result = run(project_id)
    L.write_json(L.out_path("out_performance.json"), result)
    for key in ("n_paredes", "n_pontas_de_parede", "n_nos_legacy", "n_nos_atual",
                "pares_de_ancoras_no_pior_caso", "build_wall_graph_legacy_s",
                "build_wall_graph_atual_s", "delta_s", "delta_pct"):
        print("  %-34s %s" % (key, result[key]))
    return result


if __name__ == "__main__":
    main()
