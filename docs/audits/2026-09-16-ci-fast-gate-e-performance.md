# CI rápido + performance da suíte (2026-09-16)

Missão de execução das quatro decisões aprovadas. **Nenhuma alteração de
produção**: `nuvem/core/**`, `Script.py`, UI, `nuvem/REGRAS_MODULACAO_BLOCOS.md`,
golden e baseline estão intocados. Nenhum merge. PR #42 não foi tocado.

## 1. Base

| Item | Valor |
|---|---|
| `origin/main` | `55e990d962ed22ae1021f0d335db197607bddda1` |
| Branch | `claude/ci-fast-gate-and-test-performance` |
| Base da branch | `origin/main` — o PR #45 **não** está integrado, então nada dele foi copiado |
| Ambiente das medições | Linux, CPython 3.11, pytest 9.1.1, sem paralelismo |

## 2. Os testes marcados `slow` — são 8, não 6

A auditoria do PR #45 mediu 6 testes de corpus sem o marcador. Ao aplicar,
apareceu um detalhe que **muda a conta**.

Em `tests/test_block_node_fill_revalidation.py`, os testes T18/T19/T20
compartilham `_CORPUS_CACHE`. Quem roda primeiro paga os 4 solves
(TGD off/on + TP1 off/on); os outros dois saem de graça. Foi por isso que a
medição na main mostrou **255,49 s no T18 e 0,18 s no T19/T20** — não é que
T19 e T20 sejam baratos, é que **T18 chegou antes**.

Consequência: marcar só o T18 não tiraria nada do portão rápido — o custo
migraria para o T19. Medido, isolando o T19 nesta branch:

```
tests/test_block_node_fill_revalidation.py::test_t19_candidato_rejeitado_nao_e_liberado_indevidamente
1 passed in 264.60s (0:04:24)
```

**264,48 s** — a prova. Os três levam o marcador.

| Arquivo | Testes | Custo medido |
|---|---:|---|
| `tests/test_block_arm_role_prism_stagger.py` | 5 | 162,26 + 81,55 + 80,77 + 80,62 + 80,49 = **485,7 s** (todos resolvem o TP1 inteiro) |
| `tests/test_block_node_fill_revalidation.py` | 3 | T18 mede 255,49 s; T19 isolado mede 264,48 s — é custo **do grupo**, não de um teste |

### Prova de que nada mudou além da classificação

O diff nesses dois arquivos é **puramente aditivo**: um `import pytest`, oito
decoradores `@pytest.mark.slow` e comentários registrando o custo medido.
**Zero remoção.** Nenhuma linha de lógica, asserção, parametrização ou
mensagem foi tocada.

```
$ git diff <base> -- tests/test_block_arm_role_prism_stagger.py \
                     tests/test_block_node_fill_revalidation.py \
    | grep -E '^[+-]' | grep -vE '^[+-]{3}' | grep -vE '^\+#|^\+$'
+import pytest
+@pytest.mark.slow      (× 8)
```

Total de `slow` no repositório: **31 → 39**.

## 3. FAST gate — medido

### Local

```
$ python3 -m pytest -m "not slow" -q -p no:cacheprovider
1268 passed, 39 deselected in 26.22s
```

### No CI real (GitHub Actions, `ubuntu-latest`)

```
Testes rapidos (FAST gate)  —  success
1268 passed, 39 deselected in 22.00s
job completo (checkout + setup-python + pip install + pytest): 31 s
```

| | Antes | Depois |
|---|---:|---:|
| `pytest -m "not slow"` | ~12,8 min | **22 s** |
| Testes no portão | 1.212 | **1.268** (os 8 saem, os 64 do corpus novo entram) |

Ordem de grandeza de **segundos**, como pedido. Nenhum tempo virou gate: o
portão reprova por teste vermelho, nunca por relógio.

## 4. CI

| Workflow | Quando | Conteúdo |
|---|---|---|
| `check-project-status.yml` | push/PR | **intocado** — validação documental |
| `fast-tests.yml` *(novo)* | push/PR em `main`, `claude/**`, `codex/**` | `pytest -m "not slow"` |
| `full-tests.yml` *(novo)* | `workflow_dispatch` | suíte inteira + `runner.py --all --check` |

As branches do FAST são exatamente as que o workflow documental já usa — não
inventei padrão novo.

O FULL ficou **manual, sem cron**: este repositório não tem nenhum workflow
agendado, e definir horário noturno é decisão de processo, não de código.
Virar noturno é acrescentar um bloco `schedule:` ao `on:`.

`timeout-minutes` nos dois (15 e 90) é rede contra travamento, **não** gate de
desempenho.

O cabeçalho do `full-tests.yml` registra as falhas conhecidas da main **com
plataforma**, para que "2 falhas" nunca seja número decorado.

## 5. `test_benchmark_baselines` — fixture de sessão

### O defeito de suíte

Os quatro testes do arquivo fazem **perguntas diferentes sobre o mesmo
resultado** — não regrediu contra o baseline, nenhum validador quebrou, o
solver produziu peça — e cada um chamava `runner.run_project()` do zero,
porque o runner não tem cache. **Onze solves para cinco resultados distintos.**

### A correção

Fixture `corpus_run`, escopo de sessão, cache por chave `(project_id, version)`:

```python
@pytest.fixture(scope="session")
def corpus_run():
    cache = {}

    def run(project_id, version=None):
        key = (project_id, version)
        if key not in cache:
            cache[key] = runner.run_project(project_id, write_files=False, version=version)
        return copy.deepcopy(cache[key])

    return run
```

Duas garantias que a missão exige explicitamente:

- **não cacheia entre entradas/configurações diferentes.** V1 e `v2` de um
  mesmo projeto leem `input.json` distintos e continuam sendo dois solves,
  como sempre foram;
- **devolve cópia profunda.** Um teste que mutasse o resultado não contamina o
  próximo — sem isso o cache trocaria tempo por acoplamento invisível.

O diff nas funções de teste é exatamente este, quatro vezes:

```diff
-    outcome = runner.run_project(project_id, write_files=False)
+    outcome = corpus_run(project_id)
```

Nenhuma asserção, mensagem, parametrização ou `skip` mudou. **Refatoração de
teste; produção não foi tocada.**

## 6. Prova de equivalência

Mesma branch, mesmo ambiente, antes e depois da fixture:

| | Antes | Depois |
|---|---|---|
| Resultado | `2 failed, 9 passed in 712.24s` | `2 failed, 9 passed in 472.24s` |
| Veredito por teste | — | `diff` das 11 linhas `PASSED`/`FAILED`: **vazio** |
| Mensagens de falha | — | `diff` das mensagens: **vazio** |

As duas falhas são, nos dois casos, literalmente as mesmas:

```
AssertionError: REGRESSAO CRITICA em torre_easy_lo_r00_tp1:
  [{'code': 'JUNCTION_MISSING_BINDING', 'before': 8, 'after': 9, 'delta': 1, ...}]

AssertionError: REGRESSAO em torre_easy_lo_r00_tgd/v2:
  [{'category': 'compensators', 'before': 61, 'after': 62, 'delta': 1, ...}]
```

Mesmos códigos, mesmos números, mesmo delta. Foi só otimização de suíte.

## 7. Ganho medido

| Teste | Antes | Depois |
|---|---:|---:|
| `test_o_solver_produz_alguma_coisa[tp1]` | 84,60 s | **0,75 s** |
| `test_nenhum_validador_quebra_no_projeto[tp1]` | 84,00 s | **0,64 s** |
| `test_o_solver_produz_alguma_coisa[tgd]` | 48,02 s | **0,44 s** |
| `test_nenhum_validador_quebra_no_projeto[tgd]` | 47,74 s | **0,51 s** |
| `test_projeto_nao_regrediu_contra_o_baseline[tp1]` | 84,98 s | 90,40 s |
| `test_projeto_nao_regrediu_contra_o_baseline[tgd]` | 47,98 s | 49,20 s |
| `..._versionado[tgd-v2]` | 228,76 s | 238,71 s |
| `..._versionado[tp1-v2]` | 85,69 s | 91,21 s |
| **arquivo inteiro** | **712,24 s** | **472,24 s** |

**Ganho: 240 s (−33,7%).** Cinco solves em vez de onze. As quatro linhas que
caíram para menos de 1 s são as asserções que agora leem o resultado já
calculado; o que sobra nelas é o `deepcopy` que as isola.

Os quatro solves legítimos ficaram 2–6% mais lentos (ruído de execução mais o
`deepcopy`) — é o custo que paga o isolamento entre testes.

### Correção de uma estimativa da auditoria

O relatório do PR #45 estimou economia de **≈390 s**. O real é **240 s**: eu
havia somado o tempo *total* das asserções não versionadas em vez do que
efetivamente se elimina. O número correto é este, medido.

## 8. Suíte completa — HEAD estabilizado

Uma execução, no HEAD com tudo aplicado:

```
2 failed, 1305 passed in 2261.33s (0:37:41)

FAILED tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]
FAILED tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]
```

| | main `55e990d` | HEAD desta branch |
|---|---:|---:|
| Testes | 1.243 | **1.307** (+64 do corpus novo) |
| Passaram | 1.241 | **1.305** |
| Falharam | 2 | **2 - as mesmas** |
| Tempo | 2.380,72 s | 2.261,33 s |

**Zero falha nova. Zero `skip`/`xfail` novo.** Os 64 testes do corpus BUTANTA
entraram todos verdes.

### Falhas classificadas por plataforma

| Falha | Plataforma | Estado |
|---|---|---|
| `test_benchmark_baselines[torre_easy_lo_r00_tp1]` - `JUNCTION_MISSING_BINDING` 8 para 9 | **Linux e Windows** | falha **identica na main**; gate de corpus vermelho desde antes desta missao |
| `test_benchmark_baselines[torre_easy_lo_r00_tgd-v2]` - `compensators` 61 para 62 | **Linux e Windows** | idem |
| `test_perf_trace_stall_sampler` | **so Windows** (`sys.platform == "win32"` dentro do teste) | **passou aqui**, como na main - e a terceira falha dos relatos feitos no Windows |

Nenhuma delas foi mascarada: as duas primeiras estao registradas no cabecalho
do `full-tests.yml`, e o workflow FULL termina vermelho por causa delas, de
proposito, ate serem resolvidas.

### Leitura honesta do tempo total

O ganho da fixture e de ~234 s, mas a suite inteira caiu so 119,4 s. **Nao e
contradicao - e o container.** Os testes pesados que nao mudaram rodaram mais
devagar nesta passada:

| Teste (inalterado) | main | HEAD | |
|---|---:|---:|---:|
| `test_t18_candidato_aceito_permanece_seguro_no_corpus` | 255,49 s | 269,91 s | +5,6% |
| `test_determinismo_w076_w041_duas_rodadas_identicas` | 162,26 s | 176,93 s | +9,0% |
| `test_t52_determinismo_duas_execucoes_separadas` | 163,90 s | 175,75 s | +7,2% |
| `test_t16_execucao_repetida_e_deterministica` | 93,14 s | 100,34 s | +7,7% |
| **soma dos 12 testes pesados comuns** | **1.348,0 s** | **1.443,3 s** | **+7,1%** |

Nenhum desses arquivos foi tocado por esta missao, entao os +7,1% sao deriva
do ambiente (CPU compartilhada, medicoes concorrentes nesta sessao).

Na **mesma** execucao, o arquivo do benchmark caiu de 692,5 s para **458,1 s**:

> a economia da fixture e real e maior que o delta do total; ela so esta
> parcialmente encoberta por um container ~7% mais lento nesta passada.

Por isso o numero a citar como ganho e o **medido isoladamente, antes x depois
no mesmo ambiente: 712,24 s para 472,24 s (-240 s)** - nao o delta do total,
que mistura deriva de maquina.

### 15 mais lentos no HEAD

```
269.91s call     tests/test_block_node_fill_revalidation.py::test_t18_candidato_aceito_permanece_seguro_no_corpus
233.29s call     tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]
176.93s call     tests/test_block_arm_role_prism_stagger.py::test_determinismo_w076_w041_duas_rodadas_identicas
175.75s call     tests/test_block_b19_residual_fill_implementation.py::test_t52_determinismo_duas_execucoes_separadas
100.34s call     tests/test_block_arm_role_candidate_safety_contract.py::test_t16_execucao_repetida_e_deterministica
95.69s call     tests/test_block_b19_residual_fill_implementation.py::test_t49_tp1_fingerprint_identico_com_e_sem_b19
95.28s call     tests/test_cross_band_joint_propagation_cr_g12.py::test_determinismo_da_correcao
88.92s call     tests/test_block_arm_role_prism_stagger.py::test_w010_tp1_com_abertura_nenhum_bloco_invade_o_vao
88.90s call     tests/test_block_arm_role_prism_stagger.py::test_w022_w093_tp1_cobertura_do_arm_role_consistency_preservada
88.68s call     tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]
88.60s call     tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tp1-v2]
88.59s call     tests/test_block_arm_role_prism_stagger.py::test_w076_tp1_coincidencia_de_contorno_foi_resolvida_pelo_arm_safe_repair
88.23s call     tests/test_cross_band_joint_propagation_cr_g12.py::test_fronteira_de_banda_deixa_de_criar_junta_continua[torre_easy_lo_r00_tp1]
87.66s call     tests/test_block_b19_residual_fill_implementation.py::test_t48_tp1_zero_candidatos_aceitos_apos_gate_de_integridade
87.14s call     tests/test_block_arm_role_prism_stagger.py::test_w041_tp1_prisma_resolvido_de_verdade_nao_so_reportado
```

O perfil nao mudou de natureza: os caros continuam sendo **testes de
determinismo e de corpus que resolvem a planta inteira duas ou mais vezes**.
O custo e inerente ao que provam - agora estao todos atras do marcador `slow`,
fora do portao rapido.

## 9. Corpus BUTANTÃ — estrutura, sem gabarito

`nuvem/benchmark/corpus_butanta/`: 10 fixtures mínimas nos 8 grupos pedidos,
geradas por `build_fixtures.py` a partir do princípio físico medido.

| Grupo | Caso | Princípio |
|---|---|---|
| `b34_alignment` | `b34_single_wall` | vazado menor do B34 alinhado entre fiadas vizinhas (§52) |
| `b34_alignment` | `b34_pair_courses` | há configuração em que só o giro do **par** alinha |
| `channel_window` | `window_head_sill` | canaleta na verga + uma única sob o peitoril (§41) |
| `channel_door` | `door_head_only` | porta: canaleta na verga, nenhuma abaixo |
| `t_with_b54` | `t_jamb_on_incoming_face` | canaleta cruza o nó T; B54 sobre o vão é dividido (§51) |
| `special_clusters` | `c09_c09_upright` | `C09+C09` em pé encostados são proibidos (§56.2) |
| `special_clusters` | `c04_c04_span` | `C04+C04` vira o compensador do vão total (§54) |
| `under_window` | `sill_joint_1_6cm` | junta de ~1,6 cm é argamassa, não vazio |
| `opening_adjustment` | `strip_20_35cm` | faixa de 20–35 cm entre peça de nó e jamba (§66) |
| `support` | `small_block_over_empty_course` | peça pequena não fica suspensa sobre fiada vazia (§53) |

### O que deliberadamente NÃO tem

Nenhum `expected.json`, nenhum `baseline.json`, nenhum número de saída do
solver. Enquanto o #42 muda a física, congelar a saída corrente
transformaria estado em movimento em "verdade" — e
`golden/compare.py::_critical_regressions` conta código novo como **regressão
crítica**, o que faria BUTANTÃ, TGD e TP1 aparecerem vermelhos de uma vez.

Cada caso traz `expected.PENDING.json` dizendo em texto **qual asserção vai
valer** quando houver referência autorizada. O teste
`test_expected_declarado_como_pendente_e_nao_como_gabarito` quebra se alguém
gravar um `expected.json` ou `baseline.json` ali sem passar pela autorização.

### Por que fica fora de `projects/`

`runner.list_projects()` varre `nuvem/benchmark/projects/` e devolve todo
diretório com `input.json`. Um projeto novo ali entraria **hoje** nas
parametrizações de `test_benchmark_baselines.py` e mudaria o portão de corpus
com o #42 em voo. O teste `test_fixtures_nao_entram_no_portao_de_corpus` fixa
isso: a lista continua sendo exatamente `piloto_sintetico_2x2`,
`torre_easy_lo_r00_tgd` e `torre_easy_lo_r00_tp1`.

### Não overfit — como cada fixture se defende

| Princípio | Como está garantido, com teste |
|---|---|
| Sem `ElementId` | `test_nenhuma_identidade_de_projeto` reprova qualquer sequência de 7 dígitos e exige `source_element_id: null` |
| Sem `W0xx` | o mesmo teste reprova `\bW\d{3}\b`; as paredes se chamam `A`/`B` |
| Pequena de verdade | `test_e_pequena_de_verdade`: no máximo 3 paredes e 2 aberturas |
| Fisicamente coerente | `test_geometria_internamente_coerente`: comprimento bate com os extremos, vão dentro da parede, peitoril abaixo da verga, verga dentro da altura, porta sem peitoril, janela com peitoril |
| Reutilizável | formato é o `input.json` do benchmark; trocar as medidas gera o caso equivalente de outro projeto |
| Sem ruído de diff | `test_gerador_e_deterministico`: rodar `build_fixtures.py` de novo não muda byte |

`tests/test_corpus_butanta_fixtures.py`: **64 testes em 0,11 s**.

## 10. Prova de que produção não mudou

```
$ git diff --name-only origin/main HEAD -- nuvem/core Script.py \
      nuvem/REGRAS_MODULACAO_BLOCOS.md nuvem/benchmark/golden \
      'nuvem/benchmark/projects/**'
(vazio)
```

