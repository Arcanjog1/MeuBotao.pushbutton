# -*- coding: utf-8 -*-
"""REGRESSAO DO BENCHMARK (item 12) - o teste que impede uma correcao nova
de destruir uma solucao antiga.

Como funciona: cada projeto em `nuvem/benchmark/projects/` pode ter um
`baseline.json` (gravado com `runner.py --all --save-baseline`). Este
arquivo roda o solver de novo e compara com o baseline:

* achado CRITICO que aumentou  -> falha (REGRESSAO CRITICA);
* categoria com mais paredes reprovadas -> falha (REGRESSAO);
* tudo igual ou melhor -> passa.

Quando uma melhoria real acontecer, o baseline e' regravado DE PROPOSITO,
num commit que diz o que melhorou - nunca em silencio para "fazer o teste
passar".

Estes testes rodam o solver de verdade e sao os mais lentos da suite. Sao
marcados `slow`: `pytest -m "not slow"` pula, `pytest tests/regression`
roda tudo.
"""

import copy
import json
import os

import pytest

from benchmark import runner, scoring

PROJECTS = runner.list_projects()


def _baseline(project_id, version=None):
    path = runner.project_paths(project_id, version)["baseline"]
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _versions(project_id):
    """Reguas VERSIONADAS de um projeto (2026-09-12): subdiretorios de
    `projects/<id>/` que tem `baseline.json` E `manifest.json` (gerados por
    `tools/build_version_manifest.py`). `provisional_2b/` (so' score.json) e
    `baselines/` (arquivos avulsos) NAO entram - nao sao reguas."""
    directory = runner.project_paths(project_id)["dir"]
    found = []
    for name in sorted(os.listdir(directory)):
        sub = os.path.join(directory, name)
        if (os.path.isdir(sub) and os.path.isfile(os.path.join(sub, "baseline.json"))
                and os.path.isfile(os.path.join(sub, "manifest.json"))):
            found.append(name)
    return found


VERSIONED = [(project_id, version) for project_id in PROJECTS for version in _versions(project_id)]


@pytest.fixture(scope="session")
def corpus_run():
    """UM solve por `(project_id, version)` na sessao inteira.

    POR QUE: os quatro testes deste arquivo fazem PERGUNTAS DIFERENTES
    sobre o MESMO resultado - nao regrediu, nenhum validador quebrou, o
    solver produziu peca - e cada um chamava `runner.run_project()` do
    zero. Medido na main `55e990d` (Linux, CPython 3.11): as tres
    asercoes sobre o TP1 custavam 82,95s + 82,46s + 82,45s, tres solves
    identicos do mesmo projeto, e o arquivo inteiro 692,5s.

    O CACHE E' POR CHAVE, nunca global: `(project_id, version)` sao
    entradas/configuracoes DIFERENTES e cada uma paga o seu solve. V1 e
    `v2` de um mesmo projeto continuam sendo dois solves, como sempre
    foram - a regua versionada le outro `input.json`.

    Devolve uma COPIA PROFUNDA a cada chamada: um teste que mutasse o
    resultado nao pode contaminar o proximo. Sem isso, o cache trocaria
    tempo por acoplamento invisivel entre testes.

    Nada disto muda o que e' testado: mesmas asercoes, mesmos numeros,
    mesmas falhas. E' otimizacao da suite, nao mudanca de regra.
    """
    cache = {}

    def run(project_id, version=None):
        key = (project_id, version)
        if key not in cache:
            cache[key] = runner.run_project(project_id, write_files=False, version=version)
        return copy.deepcopy(cache[key])

    return run


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJECTS)
def test_projeto_nao_regrediu_contra_o_baseline(project_id, corpus_run):
    baseline = _baseline(project_id)
    if baseline is None:
        pytest.skip("{0} ainda nao tem baseline.json".format(project_id))

    outcome = corpus_run(project_id)
    delta = scoring.compare_runs(baseline, outcome["score"])

    assert delta["verdict"] != scoring.STATUS_CRITICAL_REGRESSION, (
        "REGRESSAO CRITICA em {0}: {1}".format(
            project_id,
            [row for row in delta["critical"]
             if row["status"] == scoring.STATUS_CRITICAL_REGRESSION])
    )
    regressoes = [row for row in delta["categories"]
                  if row["status"] == scoring.STATUS_REGRESSED]
    assert not regressoes, (
        "REGRESSAO em {0}: {1}".format(project_id, regressoes))


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJECTS)
def test_nenhum_validador_quebra_no_projeto(project_id, corpus_run):
    """Validador que levanta excecao devolve categoria vazia - que se
    parece com 'nenhum erro'. E' a falha mais perigosa da suite inteira,
    por isso e' testada a parte."""
    outcome = corpus_run(project_id)
    assert outcome["score"]["validator_errors"] == []


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJECTS)
def test_o_solver_produz_alguma_coisa(project_id, corpus_run):
    """Rede de seguranca contra a falha mais silenciosa possivel: o solver
    recusar o catalogo inteiro e devolver zero peca. Aconteceu de verdade
    no projeto real (catalogo com alturas 9/19/29cm), e sem este teste o
    benchmark reportaria '96 paredes nao moduladas' como se fosse defeito
    de modulacao."""
    outcome = corpus_run(project_id)
    assert outcome["score"]["blocks"] > 0, (
        "solver nao gerou nenhuma peca em {0} - sinal de catalogo recusado, "
        "nao de erro de modulacao".format(project_id))


@pytest.mark.slow
@pytest.mark.parametrize("project_id,version", VERSIONED)
def test_projeto_nao_regrediu_contra_o_baseline_versionado(project_id, version, corpus_run):
    """Mesma regra do teste V1, contra a regua VERSIONADA (ex.: `v2` =
    topologia do motor ATUAL, FASE A regenerada em 2026-09-12). A V1 (raiz)
    continua sendo medida pelo teste acima - HISTORICAL, nunca regravada."""
    baseline = _baseline(project_id, version)
    assert baseline is not None, (project_id, version)

    outcome = corpus_run(project_id, version)
    delta = scoring.compare_runs(baseline, outcome["score"])

    assert delta["verdict"] != scoring.STATUS_CRITICAL_REGRESSION, (
        "REGRESSAO CRITICA em {0}/{1}: {2}".format(
            project_id, version,
            [row for row in delta["critical"]
             if row["status"] == scoring.STATUS_CRITICAL_REGRESSION])
    )
    regressoes = [row for row in delta["categories"]
                  if row["status"] == scoring.STATUS_REGRESSED]
    assert not regressoes, (
        "REGRESSAO em {0}/{1}: {2}".format(project_id, version, regressoes))
