# Checkpoint — Auditoria do benchmark e da cobertura de regressão (2026-09-16)

```json
{
  "date": "2026-09-16",
  "scope": "current",
  "branch": "claude/laughing-einstein-cl3cen",
  "head": "15f1d7726bff3316921132756eb43b2b5c3607e7",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/45",
  "objective": "Auditar, SOMENTE em leitura, o sistema de testes e o benchmark contra a main observada e o PR #42: mapear o que cada corpus prova, montar a matriz regra x teste, medir a suite real, identificar buracos de cobertura e propor corpus permanente do BUTANTA e gates de CI. Classificacao: BENCHMARK / TEST COVERAGE / CI - nao e mudanca de producao.",
  "changes": [
    "Novo: docs/audits/2026-09-16-auditoria-benchmark-cobertura.md (relatorio unico da auditoria, 17 secoes + apendice de medicao).",
    "docs/PROJECT_STATUS.md: reconciliacao semantica com a main buscada por fetch (observed_utc, main 55e990d, #41 movido de candidato para oficial, candidatos abertos reais 42/43/44/45), linha nova da auditoria do #45 e atualizacao das linhas MAIN/HEAD, ultimo checkpoint e CI. Nenhuma linha de conteudo normativo de outra sessao foi reproduzida ou sobrescrita.",
    "Nenhuma alteracao em nuvem/core/**, Script.py, UI, nuvem/REGRAS_MODULACAO_BLOCOS.md, benchmark golden/baseline ou qualquer arquivo do PR #42."
  ],
  "tests": [
    "python3 -m pytest -q --durations=60 -p no:cacheprovider (main 55e990d, Linux, CPython 3.11, pytest 9.1.1, sem paralelismo): 2 failed, 1241 passed in 2380.72s (0:39:40), exit 1.",
    "python3 -m pytest --collect-only -q: 1243 testes; -m \"not slow\": 1212/1243; -m \"slow\": 31/1243.",
    "Nenhum teste foi criado, alterado, pulado ou desmarcado nesta missao."
  ],
  "known_failures": [
    "test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1] - falha na main 55e990d (gate de corpus TP1 V1).",
    "test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2] - falha na main 55e990d (gate de corpus TGD V2).",
    "test_perf_trace_stall_sampler - NAO falhou nesta execucao: e especifico de Windows (sys.platform == 'win32'). O numero '3 falhas = main' repetido em checkpoints anteriores nao registra plataforma e por isso nao e conferivel.",
    "check-status-doc do PR #45 estava vermelho antes desta entrega por exigir a reconciliacao do PROJECT_STATUS.md; a edicao foi autorizada pelo usuario em 2026-09-16 exclusivamente para destravar o #45."
  ],
  "physical_deltas": [
    "Nenhum. Missao de analise: zero mudanca de geometria, catalogo, regra de modulacao, baseline, golden ou score. Nenhum lote criado no Revit; Revit nao foi aberto."
  ],
  "decisions_taken": [
    "Autorizacao explicita do usuario (2026-09-16) para editar docs/PROJECT_STATUS.md SOMENTE para destravar o CI documental do PR #45, preservando o conteudo do PR #42 e sem merge.",
    "Registrar o #45 no painel como BENCHMARK / TEST COVERAGE / CI, nunca como mudanca de producao.",
    "Nao inscrever o PR em monitoramento automatico nem agendar rechecagem: CLAUDE.md proibe check-in/monitoramento por iniciativa propria."
  ],
  "decisions_pending": [
    "Marcar @pytest.mark.slow nos 6 testes de corpus sem o marcador (test_block_node_fill_revalidation::test_t18 e os cinco de test_block_arm_role_prism_stagger) e ligar o FAST gate no CI - depende de autorizacao para alterar testes e workflow.",
    "Classificar formalmente as 2 falhas de baseline (TP1 V1, TGD V2) e criar lista versionada de known failures com plataforma.",
    "Criar corpus permanente do BUTANTA em nuvem/benchmark/projects/ - exige CR com autorizacao de --save-baseline, porque new_codes conta como regressao critica (golden/compare.py).",
    "Versionar a bancada de medicao citada na secao 59 do PR #42 (delta_metrics.py, physmetrics.py) - hoje nao existe no repositorio."
  ],
  "next_steps": [
    "Aguardar decisao do usuario sobre as pendencias acima; nenhuma delas foi executada nesta missao.",
    "Nao mesclar o #45; nao tocar no #42, no #44 nem em codigo de producao."
  ],
  "references": [
    {"path": "docs/audits/2026-09-16-auditoria-benchmark-cobertura.md"},
    {"path": "docs/PROJECT_STATUS.md"},
    {"path": "tests/regression/test_benchmark_baselines.py"},
    {"path": "nuvem/benchmark/validators/base.py"},
    {"path": "nuvem/benchmark/golden/manifest.json"},
    {"path": ".github/workflows/check-project-status.yml"}
  ]
}
```

## Resumo

Auditoria em leitura sobre `origin/main` `55e990d` e o PR #42 (head `7724ab6`).
Entrega: um relatório isolado em `docs/audits/`, sem tocar em solver, UI,
regras físicas, golden, baseline ou qualquer arquivo do #42.

**Veredito: BENCHMARK PARTIAL — GAPS IDENTIFIED.**

Achados que sustentam o veredito, todos verificáveis:

- nenhum workflow executa `pytest` ou `runner --check`; o único que existe
  valida documentação e declara isso no próprio summary;
- o único gate de corpus está vermelho na main (2 falhas medidas, TP1 V1 e
  TGD V2);
- o BUTANTÃ não é projeto de benchmark: vazado menor, apoio físico, especiais
  e microajuste só existem como métrica em scripts de evidência;
- 7 dos 28 códigos da taxonomia oficial não têm nenhum teste, entre eles
  `OPENING_BLOCK_INSIDE_WINDOW` (nível 1, crítico);
- determinismo é testado por invariante local, nunca sobre a planta inteira;
- o marcador `slow` está incompleto: 6 testes de corpus somam 741,2 s sem ele.

A medição também traz a boa notícia: **1.206 dos 1.243 testes rodam em ≈ 28 s**.
O gate que falta é barato.

## Escopo e limites desta entrega

Esta é uma auditoria. Ela **não aprova** regras de modulação, benchmark,
baseline ou solver, e **não é** aprovação normativa de nada do PR #42, do #43
ou do #44 — o conteúdo normativo e as métricas físicas desses PRs são deles, e
este painel não os reproduz nem os julga.

A edição de `docs/PROJECT_STATUS.md` nesta entrega foi autorizada
explicitamente pelo usuário em 2026-09-16, com escopo restrito a destravar o
CI documental do PR #45, preservando o conteúdo do #42 e sem merge.
