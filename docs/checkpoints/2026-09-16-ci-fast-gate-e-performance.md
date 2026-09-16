# Checkpoint — CI rápido e performance da suíte (2026-09-16)

```json
{
  "date": "2026-09-16",
  "scope": "current",
  "branch": "claude/ci-fast-gate-and-test-performance",
  "head": "d933e9e16e1d64275fb900dbee36067292c833c9",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/47",
  "objective": "Executar as quatro decisoes aprovadas: marcar os testes de corpus nao marcados como slow, criar o FAST gate no CI, eliminar os solves repetidos de test_benchmark_baselines com fixture de sessao e preparar a estrutura do corpus BUTANTA sem congelar gabarito enquanto o PR #42 muda a fisica. Classificacao: BENCHMARK / TEST COVERAGE / CI - nao e mudanca de producao.",
  "changes": [
    "tests/test_block_arm_role_prism_stagger.py e tests/test_block_node_fill_revalidation.py: 8 decoradores @pytest.mark.slow (5 + 3) e um import pytest. Diff puramente aditivo - zero remocao, nenhuma alteracao de logica, assercao ou mensagem. Total de slow no repositorio: 31 -> 39.",
    ".github/workflows/fast-tests.yml (novo): FAST gate, pytest -m 'not slow' a cada push/PR nas mesmas branches do workflow documental.",
    ".github/workflows/full-tests.yml (novo): FULL manual (workflow_dispatch), suite inteira + runner.py --all --check, com as falhas conhecidas e a diferenca de plataforma registradas no cabecalho.",
    ".github/workflows/check-project-status.yml: NAO foi tocado.",
    "tests/regression/test_benchmark_baselines.py: fixture corpus_run de escopo de sessao, cache por chave (project_id, version), devolvendo copia profunda. As quatro funcoes de teste trocam runner.run_project(...) por corpus_run(...); nenhuma assercao muda.",
    "nuvem/benchmark/corpus_butanta/ (novo): build_fixtures.py, README.md e 10 fixtures minimas nos 8 grupos pedidos, cada uma com input.json e expected.PENDING.json. Sem expected.json, sem baseline.json, fora de projects/.",
    "tests/test_corpus_butanta_fixtures.py (novo): 64 testes de validade das fixtures.",
    "docs/audits/2026-09-16-ci-fast-gate-e-performance.md (novo): relatorio da missao.",
    "docs/PROJECT_STATUS.md: reconciliacao semantica contra a main buscada por fetch."
  ],
  "tests": [
    "FAST gate local: python3 -m pytest -m 'not slow' -q -p no:cacheprovider -> 1268 passed, 39 deselected in 26.22s.",
    "FAST gate no CI real (GitHub Actions ubuntu-latest, run 35102140664): 1268 passed, 39 deselected in 22.00s; job completo 31s; conclusao success.",
    "test_benchmark_baselines ANTES da fixture: 2 failed, 9 passed in 712.24s.",
    "test_benchmark_baselines DEPOIS da fixture: 2 failed, 9 passed in 472.24s. Ganho 240s (-33,7%).",
    "Equivalencia: diff dos vereditos PASSED/FAILED antes x depois vazio; diff das mensagens de falha vazio.",
    "Prova do marcador: test_t19 isolado = 1 passed in 264.60s, confirmando que o custo e do grupo T18/T19/T20 e nao de um teste.",
    "Suite completa no HEAD estabilizado: 2 failed, 1305 passed in 2261.33s (0:37:41), exit 1.",
    "tests/test_corpus_butanta_fixtures.py: 64 passed in 0.11s."
  ],
  "known_failures": [
    "test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1] - JUNCTION_MISSING_BINDING 8->9. Falha IDENTICA na main 55e990d; nao foi introduzida nem mascarada aqui.",
    "test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2] - compensators 61->62. Falha IDENTICA na main.",
    "test_perf_trace_stall_sampler - especifico de Windows (sys.platform == 'win32' dentro do teste); PASSOU nesta execucao em Linux, como na main. E a terceira falha dos relatos feitos no Windows.",
    "Nenhum skip ou xfail novo foi criado. O workflow FULL termina vermelho por causa das duas primeiras, de proposito, ate serem resolvidas."
  ],
  "physical_deltas": [
    "Nenhum. Missao de testes e CI: zero mudanca de geometria, catalogo, regra de modulacao, baseline, golden ou score. Nenhum lote criado no Revit; Revit nao foi aberto. Verificado: git diff --name-only origin/main HEAD -- nuvem/core Script.py nuvem/REGRAS_MODULACAO_BLOCOS.md nuvem/benchmark/golden nuvem/benchmark/projects devolve vazio."
  ],
  "decisions_taken": [
    "Quatro decisoes aprovadas pelo usuario em 2026-09-16: marcar os testes de corpus como slow, criar o FAST gate, eliminar solves repetidos com fixture de sessao e preparar a estrutura do corpus BUTANTA sem congelar gabarito.",
    "Marcar 8 testes em vez dos 6 apontados pela auditoria, porque T18/T19/T20 dividem _CORPUS_CACHE e marcar so' o T18 moveria o custo para o T19 (provado: T19 isolado = 264,48s).",
    "FULL sem cron: o repositorio nao tem workflow agendado e definir horario e decisao de processo, nao de codigo.",
    "Corpus BUTANTA fora de nuvem/benchmark/projects/ para nao alterar runner.list_projects() e, com ele, as parametrizacoes do portao de corpus enquanto o PR #42 esta' em voo."
  ],
  "decisions_pending": [
    "Classificar formalmente as 2 falhas de baseline (TP1 V1, TGD V2) e criar lista versionada de known failures com plataforma.",
    "Capturar a referencia final do corpus BUTANTA, medindo o projeto humano antes de definir o nivel de cada assercao, com --save-baseline autorizado - missao separada, depois do #42 estabilizar.",
    "Avaliar fixture de sessao tambem em test_block_arm_role_prism_stagger, que repete o solve do TP1 em quatro testes (~89s cada) - fora do escopo autorizado desta missao.",
    "Decidir se o FULL passa a ter cron noturno."
  ],
  "next_steps": [
    "Aguardar revisao do PR #47. Nao mesclar.",
    "Nao tocar no #42, #43, #44 nem #46."
  ],
  "references": [
    {"path": "docs/audits/2026-09-16-ci-fast-gate-e-performance.md"},
    {"path": ".github/workflows/fast-tests.yml"},
    {"path": ".github/workflows/full-tests.yml"},
    {"path": "tests/regression/test_benchmark_baselines.py"},
    {"path": "tests/test_corpus_butanta_fixtures.py"},
    {"path": "nuvem/benchmark/corpus_butanta/README.md"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Resumo

Quatro decisões executadas, todas medidas.

| | Antes | Depois |
|---|---:|---:|
| `pytest -m "not slow"` | ~12,8 min | **22 s no CI** (1.268 testes) |
| `test_benchmark_baselines` | 712,24 s | **472,24 s** (−240 s) |
| Testes `slow` | 31 | **39** |
| Suíte completa | 2 falharam / 1.241 passaram | **2 falharam / 1.305 passaram** |

**Zero falha nova, zero `skip`/`xfail` novo, zero alteração de produção.**

## Dois pontos onde a auditoria estava errada

1. **Eram 8 testes, não 6.** T18/T19/T20 dividem `_CORPUS_CACHE`: quem roda
   primeiro paga os 4 solves. Marcar só o T18 moveria o custo para o T19.
   Provado isolando o T19: **264,48 s**.
2. **A economia é 240 s, não ~390 s.** A auditoria somou o tempo *total* das
   asserções não versionadas em vez do que efetivamente se elimina.

## Escopo

Esta entrega **não aprova** regras de modulação, benchmark, baseline ou solver.
O corpus BUTANTÃ é **estrutura**, não gabarito: nenhum `expected.json` ou
`baseline.json` foi gravado, porque o PR #42 ainda está mudando a física e
`golden/compare.py::_critical_regressions` conta código novo como regressão
crítica.

A edição de `docs/PROJECT_STATUS.md` segue o item 11 da missão: fetch primeiro,
reconciliação semântica contra a main buscada, preservando o estado do #42 e
dos demais PRs sem reproduzir nem julgar o conteúdo normativo deles.
