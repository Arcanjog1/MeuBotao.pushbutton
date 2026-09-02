# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM - MATRIZ DE CONVENCOES nos TRES projetos.

A primeira medicao da escolha de convencao (out_point_choice.json) olhou
so' o projeto primario e por isso escolheu errado: no `piloto_sintetico_2x2`
a ordenacao por angulo levava PRISM_CONTINUOUS_JOINT de 7 para 20 - uma
regressao de amarracao vertical, que e' justamente o assunto do
CR-BLOCK-01. Este script mede as convencoes candidatas nos TRES projetos
versionados, que e' o unico jeito de escolher por evidencia.
"""
import sys

import lib_det as L
import run_ablation as AB
import run_point_choice as PC

PROJECTS = ("piloto_sintetico_2x2", "torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1")


def run(arm_names=None):
    module = AB.graph_module()
    arm_names = arm_names or ("legacy", "enum", "angulo", "comprimento")
    # Captura os originais ANTES de qualquer patch. Capturar dentro do
    # laco (lazy) pegava a versao ja' patchada da iteracao anterior e
    # fazia TODAS as linhas medirem o codigo legado - erro cometido e
    # corrigido durante este CR.
    original_arm_key = module._wall_graph_arm_key
    original_cluster = module._cluster_wall_arms
    original_point = module._wall_node_group_point
    rows = []
    for arm_name in arm_names:
        if arm_name == "legacy":
            module._cluster_wall_arms = AB._legacy_cluster_wall_arms
            module._wall_node_group_point = AB._legacy_group_point
        else:
            module._cluster_wall_arms = original_cluster
            module._wall_node_group_point = original_point
            module._wall_graph_arm_key = PC.ARM_KEYS[arm_name]

        criticals = {}
        for project_id in PROJECTS:
            criticals[project_id] = AB._critical_codes(project_id)

        determinism = {}
        if arm_name != "legacy":
            fps = set()
            for _vn, project in L.build_variants(L.load_input(L.PRIMARY_PROJECT_ID)):
                fps.add(L.graph_layers(L.plan_only(project))["fp_nodes"])
            determinism["fingerprints_grafo"] = len(fps)

        total = sum(len(v) for v in criticals.values() if isinstance(v, dict))
        rows.append({"ordem_bracos": arm_name, "regressoes_criticas": criticals,
                     "n_codigos_em_regressao": total, **determinism})
        print("  %-12s codigos_em_regressao=%d  %s"
              % (arm_name, total,
                 dict((p, list(c)) for p, c in criticals.items() if c)))
    module._wall_graph_arm_key = original_arm_key
    module._cluster_wall_arms = original_cluster
    module._wall_node_group_point = original_point
    return {"projetos": PROJECTS, "linhas": rows}


def main():
    result = run(sys.argv[1:] or None)
    L.write_json(L.out_path("out_convention_matrix.json"), result)
    return result


if __name__ == "__main__":
    main()
