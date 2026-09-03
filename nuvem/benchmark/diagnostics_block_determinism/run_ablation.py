# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / secao 10 - TESTE DE ABLACAO.

A missao proibe explicitamente aceitar "sort" como prova. Este script
separa as duas coisas:

  A1  SO' ORDENAR A ENTRADA (nenhuma linha de producao mudada): a lista de
      paredes e' ordenada por chave geometrica antes de entrar no
      pipeline. Isso "conserta" o fingerprint por construcao - passa a
      escolher SEMPRE um dos oito resultados antigos - mas nao torna
      nenhum no' menos ambiguo: o trio nao-transitivo continua sendo
      partido de um jeito que depende de quem apareceu primeiro DENTRO da
      ordem escolhida.

  A2..A5  CORRECAO ESTRUTURAL, uma camada por vez, ligada por monkeypatch
      DA ANALISE (nunca da producao): as versoes ANTIGAS das funcoes sao
      reinstaladas no modulo carregado para medir o efeito isolado de
      cada mudanca.

Metrica de ambiguidade estrutural (a que o "sort" nao muda): quantos
TRIOS de pontas (A~B, A~C, B!~C) existem na planta - cada um e' um no'
cuja composicao a bola gulosa decide pela ordem de visita.
"""
import copy
import itertools
import sys

import lib_det as L
import run_rootcause as RC


# ---------------------------------------------------- versoes ANTIGAS
def _legacy_cluster_wall_arms(arms, tolerance_ft, walls_to_create=None):
    """A bola gulosa de raio fixo em volta da PRIMEIRA ponta visitada -
    o codigo que estava na main 24ada98."""
    clusters = []
    used = [False] * len(arms)
    for i, arm in enumerate(arms):
        if used[i]:
            continue
        group = [arm]
        used[i] = True
        for j in range(i + 1, len(arms)):
            if used[j]:
                continue
            if arm["anchor"].DistanceTo(arms[j]["anchor"]) <= tolerance_ft:
                group.append(arms[j])
                used[j] = True
        clusters.append(group)
    return clusters


def _components_without_canonical_order(arms, tolerance_ft, walls_to_create=None):
    """Componente conexa (a correcao estrutural do agrupamento) SEM a
    ordenacao canonica - para medir quanto de determinismo vem de cada
    metade."""
    n = len(arms)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if arms[i]["anchor"].DistanceTo(arms[j]["anchor"]) <= tolerance_ft:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(arms[i])
    return list(groups.values())


def _legacy_group_point(group):
    """`group[0]["anchor"]` - o ponto do no' escolhido pela ordem."""
    return group[0].get("anchor") or group[0]["point"]


# ---------------------------------------------------------- ablacoes
def _sorted_input(input_project):
    """A1: ordena a LISTA DE PAREDES por chave geometrica canonica, sem
    tocar em nenhuma linha de producao."""
    new_project = copy.deepcopy(input_project)
    def key(wall):
        a = tuple(wall["start_cm"])
        b = tuple(wall["end_cm"])
        lo, hi = (a, b) if a <= b else (b, a)
        return (lo, hi, wall["thickness_cm"])
    new_project["walls"] = sorted(new_project.get("walls") or [], key=key)
    return new_project


ABLATIONS = (
    ("A0_main_sem_correcao", {"cluster": "legacy", "point": "legacy",
                              "sort_input": False}),
    ("A1_so_ordenar_entrada", {"cluster": "legacy", "point": "legacy",
                               "sort_input": True}),
    ("A2_componente_conexa", {"cluster": "components_unordered", "point": "legacy",
                              "sort_input": False}),
    ("A3_mais_ordem_canonica", {"cluster": "current", "point": "legacy",
                                "sort_input": False}),
    ("A4_correcao_completa", {"cluster": "current", "point": "current",
                              "sort_input": False}),
)


def graph_module():
    """O modulo em que `build_wall_graph` REALMENTE resolve seus helpers.

    `L.engine()` devolve `script_under_test` (o core/wall_modeling.py
    carregado pelos dubles), que so' REEXPORTA os nomes: trocar o
    atributo la' nao muda a referencia que `build_wall_graph` usa, porque
    ela e' resolvida nos globals de `core.engine.wall_pairing`. Patchar o
    modulo errado faz toda ablacao medir a MESMA coisa (erro cometido e
    corrigido durante este CR)."""
    module = L.engine()
    return sys.modules[module.build_wall_graph.__module__]


def _install(module, config, originals):
    if config["cluster"] == "legacy":
        module._cluster_wall_arms = _legacy_cluster_wall_arms
    elif config["cluster"] == "components_unordered":
        module._cluster_wall_arms = _components_without_canonical_order
    else:
        module._cluster_wall_arms = originals["_cluster_wall_arms"]
    if config["point"] == "legacy":
        module._wall_node_group_point = _legacy_group_point
    else:
        module._wall_node_group_point = originals["_wall_node_group_point"]


def split_triangles(input_project):
    """Quantos trios nao-transitivos a particao ATUAL (a que estiver
    instalada no modulo) PARTE em nos diferentes.

    E' esta a metrica que separa determinismo de correcao: ordenar a
    entrada congela a particao, mas nao muda quantos trios ela parte. Se
    o numero continuar > 0, os nos continuam geometricamente ambiguos -
    e o CR nao fecha (secao 10 da missao)."""
    module = graph_module()
    walls_to_create, junction_map = RC._rebuild_walls(L.engine(), input_project)
    arms = module._wall_node_arms(walls_to_create, junction_map)
    tol = module.WALL_GRAPH_NODE_SNAP_TOLERANCE_FT
    n = len(arms)
    near = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            close = arms[i]["anchor"].DistanceTo(arms[j]["anchor"]) <= tol
            near[i][j] = near[j][i] = close

    clusters = module._cluster_wall_arms(arms, tol, walls_to_create)
    cluster_of = {}
    for cluster_index, group in enumerate(clusters):
        for arm in group:
            cluster_of[id(arm)] = cluster_index

    split = 0
    for i in range(n):
        partners = [j for j in range(n) if near[i][j]]
        for a, b in itertools.combinations(partners, 2):
            if near[a][b]:
                continue
            ids = set(cluster_of.get(id(arms[k])) for k in (i, a, b))
            if len(ids) > 1:
                split += 1
    return split


def structural_ambiguity(input_project):
    """Trios nao-transitivos da planta - a ambiguidade que NENHUMA
    ordenacao da entrada remove."""
    module = L.engine()
    walls_to_create, junction_map = RC._rebuild_walls(module, input_project)
    arms = module._wall_node_arms(walls_to_create, junction_map)
    tol = module.WALL_GRAPH_NODE_SNAP_TOLERANCE_FT
    n = len(arms)
    near = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            close = arms[i]["anchor"].DistanceTo(arms[j]["anchor"]) <= tol
            near[i][j] = near[j][i] = close
    count = 0
    for i in range(n):
        partners = [j for j in range(n) if near[i][j]]
        for a, b in itertools.combinations(partners, 2):
            if not near[a][b]:
                count += 1
    return count


def _critical_codes(project_id):
    """As regressoes CRITICAS que o benchmark oficial aponta contra o
    baseline versionado, com a ablacao atual instalada - para atribuir
    cada regressao de qualidade a' sub-mudanca que a causou, em vez de
    reportar "o CR regrediu" sem dizer onde."""
    from benchmark import runner as bench_runner
    from benchmark import scoring
    outcome = bench_runner.run_project(project_id, write_files=False)
    baseline = bench_runner.read_baseline(project_id) \
        if hasattr(bench_runner, "read_baseline") else None
    if baseline is None:
        import json
        import os
        paths = bench_runner.project_paths(project_id)
        candidate = paths.get("baseline")
        if not candidate or not os.path.isfile(candidate):
            return "SEM_BASELINE"
        with open(candidate) as handle:
            baseline = json.load(handle)
    delta = scoring.compare_runs(baseline, outcome["score"])
    return dict((row["code"], [row["before"], row["after"]])
                for row in delta["critical"]
                if row["status"] == scoring.STATUS_CRITICAL_REGRESSION)


def run(project_id=None):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    module = graph_module()
    originals = {
        "_cluster_wall_arms": module._cluster_wall_arms,
        "_wall_node_group_point": module._wall_node_group_point,
    }
    input_project = L.load_input(project_id)

    rows = []
    for name, config in ABLATIONS:
        _install(module, config, originals)
        # ATENCAO: a ordenacao da ablacao A1 tem que ser aplicada DEPOIS
        # da permutacao, nunca antes - ordenar e so' entao embaralhar mede
        # o embaralhamento, nao a ordenacao. E' o que uma correcao "so'
        # sort" faria de verdade: normalizar a lista JA' recebida.
        source = input_project
        variants = L.build_variants(source)
        if config["sort_input"]:
            variants = [(vname, _sorted_input(project)) for vname, project in variants]
        fps_nodes, fps_blocks, kinds_seen, pieces = set(), set(), set(), set()
        for _vname, project in variants:
            run_data = L.run_full(project)
            layers = L.graph_layers(run_data)
            blocks = L.block_layers(run_data)
            fps_nodes.add(layers["fp_nodes"])
            fps_blocks.add(blocks["fp_blocks"])
            kinds_seen.add(str(layers["kinds"]))
            pieces.add(blocks["n_pieces"])
        split_by_variant = sorted(set(
            split_triangles(project) for _vn, project in variants))
        critical = _critical_codes(project_id)
        rows.append({
            "ablacao": name,
            "trios_PARTIDOS_por_variante": split_by_variant,
            "regressoes_criticas_vs_baseline": critical,
            "config": config,
            "fingerprints_grafo_distintos": len(fps_nodes),
            "fingerprints_blocos_distintos": len(fps_blocks),
            "classificacoes_distintas": len(kinds_seen),
            "contagens_de_pecas_distintas": sorted(pieces),
            "trios_nao_transitivos_na_planta": structural_ambiguity(source),
        })
        print("  %-26s grafo=%d blocos=%d trios_na_planta=%d partidos=%s crit=%s"
              % (name, len(fps_nodes), len(fps_blocks),
                 rows[-1]["trios_nao_transitivos_na_planta"],
                 split_by_variant, critical))

    _install(module, {"cluster": "current", "point": "current"}, originals)
    return {"project_id": project_id, "ablacoes": rows}


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    result = run(project_id)
    L.write_json(L.out_path("out_ablation.json"), result)
    return result


if __name__ == "__main__":
    main()


# Guardadas na importacao, ANTES de qualquer monkeypatch, para os scripts
# de matriz poderem voltar as funcoes da arvore atual sem depender da
# ordem em que os patches foram aplicados.
_ORIGINALS = {}


def originals_cluster():
    if "cluster" not in _ORIGINALS:
        _ORIGINALS["cluster"] = graph_module()._cluster_wall_arms
    return _ORIGINALS["cluster"]


def originals_point():
    if "point" not in _ORIGINALS:
        _ORIGINALS["point"] = graph_module()._wall_node_group_point
    return _ORIGINALS["point"]
