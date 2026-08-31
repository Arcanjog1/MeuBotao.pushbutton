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

import json
import os

import pytest

from benchmark import runner, scoring

PROJECTS = runner.list_projects()


def _baseline(project_id):
    path = runner.project_paths(project_id)["baseline"]
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJECTS)
def test_projeto_nao_regrediu_contra_o_baseline(project_id):
    baseline = _baseline(project_id)
    if baseline is None:
        pytest.skip("{0} ainda nao tem baseline.json".format(project_id))

    outcome = runner.run_project(project_id, write_files=False)
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
def test_nenhum_validador_quebra_no_projeto(project_id):
    """Validador que levanta excecao devolve categoria vazia - que se
    parece com 'nenhum erro'. E' a falha mais perigosa da suite inteira,
    por isso e' testada a parte."""
    outcome = runner.run_project(project_id, write_files=False)
    assert outcome["score"]["validator_errors"] == []


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJECTS)
def test_o_solver_produz_alguma_coisa(project_id):
    """Rede de seguranca contra a falha mais silenciosa possivel: o solver
    recusar o catalogo inteiro e devolver zero peca. Aconteceu de verdade
    no projeto real (catalogo com alturas 9/19/29cm), e sem este teste o
    benchmark reportaria '96 paredes nao moduladas' como se fosse defeito
    de modulacao."""
    outcome = runner.run_project(project_id, write_files=False)
    assert outcome["score"]["blocks"] > 0, (
        "solver nao gerou nenhuma peca em {0} - sinal de catalogo recusado, "
        "nao de erro de modulacao".format(project_id))
