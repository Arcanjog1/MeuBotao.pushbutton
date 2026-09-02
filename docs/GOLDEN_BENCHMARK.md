# Golden Benchmark — comparação com projetos de referência

> **Este documento descreve o estado do `CR-BLOCK-GOLDEN-BENCHMARK`
> (histórico).** A partir do `CR-BLOCK-REFERENCE-CORPUS`, o sistema
> inteiro passou a se chamar **Reference Corpus** / **Reference
> Benchmark** — ver **[`docs/REFERENCE_CORPUS.md`](REFERENCE_CORPUS.md)**,
> que é a documentação atual e ponto de entrada. `GOLDEN_CONFIRMED`
> continua existindo, mas agora é só o nível mais alto de confiança
> dentro do corpus, nunca requisito de entrada — a ideia de que só um
> projeto "golden o suficiente" participava do benchmark, descrita
> abaixo, **não vale mais**. Este arquivo fica como registro do raciocínio
> original (inventário, classificação item a item) e continua preciso
> sobre os módulos que não mudaram de forma (validadores, comparator,
> scoring, matching geométrico).

`CR-BLOCK-GOLDEN-BENCHMARK`. Infraestrutura para responder, de forma
estruturada e reprodutível: **"essa nova versão do solver ficou melhor,
igual ou pior que a versão de referência?"** — por categoria, nunca com
uma nota única.

> Esta frente é **paralela** ao `CR-BLOCK-DETERMINISM` (outra conta,
> trabalhando em `nuvem/core/engine/wall_stepper.py`). Nada em
> `nuvem/benchmark/golden/**` importa nem altera `wall_stepper.py`,
> `wall_pairing.py`, `geometry.py`, `tolerances.py`,
> `continuous_modulation.py`, `modulation_math.py` ou `wall_modeling.py`.
> É construído **em cima** de `nuvem/benchmark/*` (model/scoring/
> validators/comparator/runner), que já existia e já implementa boa
> parte do que este pacote pede — ver seção "O que já existia" abaixo.

## O que já existia (não foi duplicado)

Antes de escrever qualquer coisa nova, o repositório foi vasculhado
inteiro (`benchmark`, `baseline`, `golden`, `reference`, `approved`,
`regression`, `input.json`, `diagnostics`, etc.). `nuvem/benchmark/`
já é uma infraestrutura de benchmark madura:

| Já existia | Cobre |
|---|---|
| `benchmark/model.py` | Schema único result/reference, identidade **geométrica** (`wall_stable_key`/`block_stable_key`, sem `ElementId`, invariante a reversão de ponta) |
| `benchmark/validators/*` + `validators/base.py` | Taxonomia de erro (nível 1/2, severidade, `SEVERITY_CRITICAL`), 6 validadores independentes |
| `benchmark/comparator/match.py` | Casamento geométrico resultado × gabarito (pontas iguais → mesma reta+overlap → sem par) |
| `benchmark/comparator/compare_projects.py` | Diff bloco a bloco por parede/fiada: `IDENTICAL/EQUIVALENT_SUBSTITUTION/DIFFERENT_LAYOUT/MISSING_IN_RESULT/EXTRA_IN_RESULT` |
| `benchmark/scoring.py` | `score_project` (PASS/FAIL por categoria, críticos à parte) e `compare_runs` (baseline × nova versão, com REGRESSAO CRITICA por código) |
| `benchmark/runner.py` | O laço `input → solver → result → validadores → score → baseline` |
| `tests/solver_bench.py` | `solver_decision_fingerprint` (hash de decisão do solver, escopo diferente do fingerprint deste pacote — ver seção Fingerprint) |

Este pacote (`nuvem/benchmark/golden/`) **não reimplementa nada disso**.
Ele:

1. classifica formalmente a confiabilidade de cada projeto (`manifest.py`) —
   isso **não existia**: nenhum projeto tinha um registro explícito de
   "isso é golden" vs "isso é só um baseline do solver";
2. reorganiza `score`/`findings`/`project` nas categorias de domínio que
   o pedido especifica, com **direção** por métrica (`metrics.py`) — a
   direção (maior é melhor / menor é melhor / informativo / depende do
   contexto) também não existia;
3. compara dois bundles de métricas com deltas e veredito por categoria
   (`compare.py`), delegando a regra de "regressão crítica" para
   `scoring.compare_runs`, já testada;
4. calcula um fingerprint canônico independente de ordem/`ElementId`
   (`fingerprint.py`);
5. reorganiza o diff já produzido por `compare_projects.py` na
   nomenclatura ADDED/REMOVED/MOVED/CHANGED_CODE, por parede e por fiada
   (`wall_diff.py`);
6. valida a ordem oficial de paredes definida pelo usuário, como
   infraestrutura pronta para o futuro (`wall_order.py`,
   `pipeline_order.py`) — **sem alterar produção**;
7. gera relatório Markdown (`report_md.py`) e uma CLI
   (`tools/run_golden_compare.py`).

## Inventário do repositório

Buscas feitas: `benchmark`, `baseline`, `golden`, `reference`,
`approved`, `project`, `regression`, `human`, `expected`, `input.json`,
`baseline.json`, `diagnostics`, `solver_bench`, `comparison`, além de
`nuvem/benchmark/**`, `tests/regression/**`, `docs/**` e
`nuvem/REGRAS_MODULACAO_BLOCOS.md` inteiros.

Resultado: **três projetos** em `nuvem/benchmark/projects/`, nenhum
outro diretório de "regressão"/"golden" fora dali, e nenhum framework de
benchmark concorrente. `tests/regression/test_benchmark_baselines.py` é
quem hoje consome `baseline.json` para regressão do solver.

O inventário **mecânico** (só o que existe em disco, sem julgamento de
confiabilidade) é gerado por `nuvem/benchmark/golden/inventory.py` e
gravado em `nuvem/benchmark/golden/inventory.json` — regenerável a
qualquer momento com:

```bash
py -3 -m nuvem.benchmark.golden.inventory
```

### Os três projetos, e por que cada um é classificado como está

A classificação HUMANA (não mecânica) mora em
`nuvem/benchmark/golden/manifest.json`. Resumo:

| project_id | `reference_type` | por quê |
|---|---|---|
| `torre_easy_lo_r00_tgd` | `HUMAN_REFERENCE_AVAILABLE` | Par de documentos Revit reais (input **medido**, referência do nível 04. TGD). Os blocos do gabarito foram posicionados por uma pessoa — não pelo solver. Mas o `.rvt` entregue não tem mais `Wall`/`Door`/`Window` nativos (0 de cada); `reference.json` é **reconstruído** a partir do layout dos blocos. E, principal: **não há nenhum registro de aprovação formal** (data, responsável, processo de sign-off) em `metadata.json`. |
| `torre_easy_lo_r00_tp1` | `HUMAN_REFERENCE_AVAILABLE` | Mesma família de projeto, nível 05. TP1. Mesma limitação (reference reconstruído, aberturas `confidence: reconstructed`) e mesma ausência de prova de aprovação formal. |
| `piloto_sintetico_2x2` | `SOLVER_GENERATED_ONLY` | Grade sintética gerada por `extract/synthetic.py`. Não existe `reference.json` (o próprio `metadata.json` diz "SEM GABARITO"). Só serve como fixture barata de regressão/determinismo da infraestrutura. |

**Nenhum projeto é `GOLDEN_CONFIRMED`** (item 6 do pedido: não inventar
golden). `HUMAN_REFERENCE_AVAILABLE` é o teto que a evidência hoje
sustenta — são os **candidatos** a golden
(`manifest.candidates_for_promotion`), não golden em si. Promover um
deles exigiria um registro explícito de validação humana (quem aprovou,
quando, como) editado a mão em `manifest.json` — `manifest.validate_entry`
recusa uma entrada `GOLDEN_CONFIRMED` sem `validated_at` e
`approved_by_human: true`.

### `baseline.json` nunca é referência — é sempre `LEGACY_BASELINE`

Item 3 do pedido, confirmado na prática: **todo** `baseline.json` do
repositório tem `"source": "solver"` — é um `score.json` congelado de uma
execução anterior do **próprio solver**, gravado por
`runner.py --save-baseline`. Prova reprodutibilidade (o motor decide a
mesma coisa de novo), nunca correção. O mesmo vale para
`torre_easy_lo_r00_tgd/baselines/baseline_real_v1.json`: o campo
`"status": "OFICIAL"` ali quer dizer "é o baseline de regressão valendo
agora", não "foi validado por humano" — ele carrega
`solver_decision_fingerprint`, que é uma prova de determinismo do
solver, não de correção do resultado.

Por isso `reference.json` (classificado em `manifest.json`, acima) e
`baseline.json` (sempre `LEGACY_BASELINE`, documentado nas notas de cada
entrada do manifesto) **nunca se confundem** neste pacote.

## Arquitetura

```
nuvem/benchmark/golden/
    manifest.py         schema + validacao de GOLDEN_CONFIRMED/HUMAN_REFERENCE_AVAILABLE/
                         LEGACY_BASELINE/SOLVER_GENERATED_ONLY/UNKNOWN
    manifest.json        classificacao OFICIAL dos 3 projetos (editado a mao)
    inventory.py          scan mecanico de nuvem/benchmark/projects/ (regeneravel)
    inventory.json         snapshot do scan
    metrics.py            metricas por categoria + DIRECAO (HIGHER/LOWER_IS_BETTER,
                           INFORMATIONAL, CONTEXT_DEPENDENT)
    compare.py             motor de comparacao puro: dois bundles -> deltas + veredito
                            (IMPROVED/NEUTRAL/REGRESSED/MIXED) + criticos (via scoring.compare_runs)
    fingerprint.py         fingerprint canonico (sem wall_idx/id()/ordem/sentido de ponta)
    wall_diff.py            ADDED/REMOVED/MOVED/CHANGED_CODE por parede/fiada/bloco
    wall_order.py           valida a ordem oficial de paredes (H->V->inclinada) - NAO produz
    pipeline_order.py       interface preparada (NOT_AVAILABLE) para provar continuous_first
    report_md.py            relatorio Markdown a partir do JSON de compare.py

nuvem/benchmark/tools/
    run_golden_compare.py   CLI

tests/test_golden_benchmark.py   43 testes, tudo sintetico, sem Revit/solver
```

## Manifesto (`manifest.json`)

Schema por projeto (`manifest.new_entry`): `project_id`, `name`,
`status`/`reference_type`, `source`, `created_at`, `validated_at`,
`baseline_commit`, `has_revit_model`, `produced_by_solver`,
`approved_by_human`, `available_metrics`, `notes`.

`manifest.validate_entry(entry)` devolve a lista de problemas (vazia =
ok) — nunca levanta exceção sozinha, para o sistema poder **avisar** sem
quebrar. A única regra rígida: `GOLDEN_CONFIRMED` exige `validated_at` e
`approved_by_human: true`. Testada em
`test_manifest_recusa_golden_confirmed_sem_prova_de_validacao`.

## Métricas por categoria (`metrics.py`)

`compute_metrics(project=None, score=None, findings=None,
timing_seconds=None, by_stage_seconds=None)` monta o bundle:
`walls`, `courses`, `blocks`, `prism`, `junctions`, `openings`,
`quality`, `performance`. Cada métrica é
`{"value", "status", "direction", "unit", "note"}`.

**Nada é recalculado do zero.** Os números vêm de
`scoring.score_project(...)` (`score["findings_by_code"]`,
`score["critical_errors"]`, ...) e, quando o `project` bruto está
disponível, de `model.iter_blocks`/`model.rows_sorted` para a contagem
de blocos por código (B39/B34/B54/B19/C09/C04/outros) — que o `score.json`
sozinho não guarda.

**Dado incompleto nunca vira zero** (item 26): sem `project` nem
`score`, toda métrica sai `{"value": None, "status": "NOT_AVAILABLE"}`.
Testado em `test_metricas_sem_nenhum_dado_saem_not_available_nunca_zero`.

### Direção — a tabela que decide o que é "melhor" (item 12)

| Direção | Quando | Exemplos |
|---|---|---|
| `HIGHER_IS_BETTER` | maior é melhor | `coverage_pct`, `walls_modulated` |
| `LOWER_IS_BETTER` | menor é melhor | `collisions`, `alignment_conflicts`, `missing_binding`, `runtime_seconds` |
| `INFORMATIONAL` | não julga (nível 2, preferência) | `stagger_below_target`, `avoidable_compensators`, `total_walls` |
| `CONTEXT_DEPENDENT` | nem maior nem menor é automaticamente melhor | `total_blocks`, contagem de cada código de peça (B19, B39...) |

Nenhuma direção foi inventada por capricho: cada uma cita, no código, o
achado (`validators/base.py`) ou a seção do
`REGRAS_MODULACAO_BLOCOS.md` de onde a métrica vem.

### Invariantes críticos (item 14)

`metrics.critical_invariant_codes()` **não é uma lista nova** — é
exatamente os códigos que `validators/base.py` já marca
`SEVERITY_CRITICAL` (`PRISM_CONTINUOUS_JOINT`,
`JUNCTION_MISSING_BINDING`, `OPENING_BLOCK_INSIDE_DOOR`,
`OPENING_BLOCK_INSIDE_WINDOW`, `OPENING_BLOCK_CROSSES_JAMB`,
`COVERAGE_WALL_NOT_MODULATED`, `COVERAGE_MISSING_ROW`,
`COVERAGE_ROW_MOSTLY_EMPTY`, `POSITION_OVERLAP`), cada um já citando a
seção do `REGRAS_MODULACAO_BLOCOS.md` de origem.

## Motor de comparação (`compare.py`)

```python
from benchmark.golden import compare
resultado = compare.compare(
    {"score": score_referencia, "project": projeto_referencia, "findings": achados_referencia},
    {"score": score_atual, "project": projeto_atual, "findings": achados_atual},
)
resultado["verdict"]              # IMPROVED / NEUTRAL / REGRESSED / MIXED
resultado["critical_invariants"]  # regressoes criticas, via scoring.compare_runs
resultado["categories"]           # por categoria: cada metrica com delta_abs/delta_pct/status
```

Regra do veredito (nunca uma nota única cega, item 13): se **qualquer**
invariante crítico piorou, o veredito é sempre `REGRESSED` — mesmo que
a maioria das métricas tenha melhorado (testado em
`test_veredito_e_regressed_quando_critico_piora_mesmo_com_outras_metricas_iguais`).
Fora isso: só melhoras → `IMPROVED`; só pioras → `REGRESSED`; nada mudou
→ `NEUTRAL`; melhora e piora ao mesmo tempo (em métricas diferentes) →
`MIXED`.

Todo argumento de `compare(...)` é opcional — dado que falta em um dos
lados vira `NOT_AVAILABLE` naquela métrica, nunca erro nem zero
inventado.

## Fingerprint canônico (`fingerprint.py`)

Constrói a assinatura do projeto inteiro **só** com o que
`model.wall_stable_key`/`model.block_stable_key` já garantem: nenhuma
dependência de `wall_idx`, `id()` do Python, ou ordem de entrada da lista
`walls`. Paredes são ordenadas pela própria chave antes do hash — duas
execuções que produzem as mesmas paredes/blocos em ordem diferente dão o
**mesmo** fingerprint; duas execuções que decidem algo diferente dão
fingerprints diferentes.

```python
from benchmark.golden import fingerprint
fingerprint.canonical_fingerprint(projeto)          # sha256 hex
fingerprint.multi_run_report([r1, r2, r3, ...])     # {"deterministic": bool, "distinct_fingerprints": N, ...}
```

`multi_run_report` é a peça que fica pronta para o `CR-BLOCK-DETERMINISM`
(outra frente, em paralelo): rodar o mesmo `input.json` N vezes e
verificar se dá **1** fingerprint ou **N**.

**Limitação documentada** (item 16): cobre geometria de parede +
posicionamento de bloco (o que o solver decide). Aberturas e nós L/T/X
ainda não têm chave canônica dedicada em `model.py` — quando ganharem,
o fingerprint pode ser estendido sem quebrar o que já existe.

## Diff por parede / fiada / bloco (`wall_diff.py`)

Não recalcula nada geometricamente — reorganiza
`comparator.compare_projects(...)` (que já casa paredes por geometria,
nunca por índice) na terminologia do pedido:

| Classe de `compare_projects.py` | Ação (`wall_diff.py`) |
|---|---|
| `EXTRA_IN_RESULT` | `ADDED` |
| `MISSING_IN_RESULT` | `REMOVED` |
| `DIFFERENT_LAYOUT` | `MOVED` |
| `EQUIVALENT_SUBSTITUTION` | `CHANGED_CODE` |

```python
from benchmark.golden import wall_diff
comparacao = wall_diff.compute_wall_diff(projeto_atual, projeto_referencia)
wall_diff.changed_wall_ids(comparacao)        # "quais paredes mudaram", ordenado por qtd. de mudanca
wall_diff.block_diff_for_wall(comparacao, "W003")   # ADDED/REMOVED/MOVED/CHANGED_CODE naquela parede
wall_diff.course_diff_for_wall(comparacao, "W003")  # o mesmo, agrupado por fiada
wall_diff.wall_diff_report(comparacao)         # tudo junto, pronto pro relatorio
```

Validado com o projeto real `torre_easy_lo_r00_tgd` (97 paredes, 12.508
blocos): `reference.json` comparado consigo mesmo dá zero paredes
alteradas e as métricas de bloco batem exatamente.

## Ordem oficial das paredes (`wall_order.py`) — item 17

Implementa, como **infraestrutura de validação apenas** (nunca chamada
pela produção), a regra definida pelo usuário:

* horizontais primeiro, cima→baixo, empate esquerda→direita, sentido
  interno (o próprio `start_cm→end_cm`) esquerda→direita;
* verticais depois, baixo→cima, empate esquerda→direita, sentido interno
  baixo→cima;
* inclinadas por último, por geometria canônica (`model.wall_stable_key`).

`wall_order.official_order(walls)` devolve a lista na ordem oficial;
`wall_order.validate_wall_order(walls)` diz se uma lista já dada respeita
a regra, apontando o **primeiro** ponto de divergência (nunca só um
booleano cego); `wall_order.audit_internal_directions(walls)` lista as
paredes cujo próprio eixo está no sentido contrário ao "sentido interno"
da regra.

## Estratégia "parede completa primeiro" (`pipeline_order.py`) — item 18

**Não implementado de verdade, documentado como limitação** (itens 18 e
34 pedem exatamente isso: não inventar prova onde não há dado). O motor
hoje não emite nenhum rastro de EM QUE ORDEM as etapas
(`graph_l_t_x → full_wall → continuous_modulation → prism → opening →
removal → local_repair → validation`) rodaram para uma parede com
abertura. Sem esse rastro, `pipeline_order.continuous_first_evidence()`
**sempre** devolve `NOT_AVAILABLE` — nunca um "sim" adivinhado a partir
do resultado final (o resultado final é compatível com mais de uma ordem
de execução). Quando o motor passar a emitir esse rastro, a função já
sabe comparar contra `EXPECTED_STAGE_ORDER` (copiado do pedido, não
inventado).

## CLI

```bash
# baseline de um projeto x a ultima rodada dele
py -3 nuvem/benchmark/tools/run_golden_compare.py \
    --project torre_easy_lo_r00_tgd --reference baseline --current score

# dois arquivos quaisquer (score/baseline/result/reference/findings -
# o formato e' detectado sozinho)
py -3 nuvem/benchmark/tools/run_golden_compare.py \
    --reference-file A/score.json --current-file B/score.json \
    --reference-project-file A/result.json --current-project-file B/result.json \
    --out-json comparacao.json --out-md relatorio.md
```

Zero dependência nova — só biblioteca padrão + `nuvem/benchmark/*`.

## Testes

`tests/test_golden_benchmark.py`, 43 testes, sintéticos (mesmo estilo de
`tests/regression/test_benchmark_infra.py`, sem Revit nem solver real).
Cobre: fingerprint determinístico e invariante a ordem/reversão de ponta,
métricas com dado incompleto (`NOT_AVAILABLE`, nunca zero), direção de
métrica (higher/lower/informational), veredito
IMPROVED/NEUTRAL/REGRESSED/MIXED (inclusive regressão crítica escondida
atrás de média boa), diff ADDED/REMOVED/MOVED/CHANGED_CODE, diff por
fiada, manifesto (recusa `GOLDEN_CONFIRMED` sem prova, projeto
inexistente devolve `None` sem lançar exceção), inventário, e a ordem
oficial de paredes.

```bash
py -3 -m pytest tests/test_golden_benchmark.py -q
```

## Limitações explícitas

* **Nenhum projeto é `GOLDEN_CONFIRMED`** — o repositório não tem hoje
  prova de validação humana formal para nenhum dos dois projetos reais.
  Isso é uma limitação de **dado**, não deste pacote: a arquitetura já
  está pronta para promover um projeto assim que essa prova existir
  (`manifest.validate_entry`).
* **Fingerprint cobre parede+bloco, não abertura/nó L-T-X** (falta chave
  canônica dedicada em `model.py` para esses dois).
* **Quebra L/T/X do diff de encontros** (`missing_binding_by_type_L/T/X`)
  só funciona com a lista de `findings` — `score.json`/`baseline.json`
  sozinhos não guardam `junction_type`.
* **`continuous_first` (item 18) não tem como ser provado hoje** — falta
  o motor emitir um rastro de ordem de execução por parede. A interface
  já existe (`pipeline_order.py`), sempre honesta sobre não saber.
* **Nenhum parser de `.rvt`/importador de "projeto humano aprovado"** foi
  criado (itens 34/35 pediram explicitamente para não fazer isso agora)
  — só a interface de manifesto está pronta para receber um projeto
  assim quando existir.
* **`baseline.json`/`reference.json` existentes não foram alterados,
  regravados nem reclassificados** — confirmado por `git status`
  (nenhum arquivo dentro de `nuvem/benchmark/projects/**` foi tocado por
  esta tarefa).

## Próximo passo

1. Quando um projeto tiver prova de validação humana (data + responsável
   + o que foi aprovado), promovê-lo a `GOLDEN_CONFIRMED` em
   `manifest.json` — a validação já recusa a promoção sem essa prova.
2. Rodar `run_golden_compare.py` de verdade contra o
   `CR-BLOCK-DETERMINISM` assim que ele terminar (comparar
   `torre_easy_lo_r00_tgd`/`torre_easy_lo_r00_tp1` antes × depois da
   correção em `wall_stepper.py`) — sem tocar nos baselines existentes.
3. Estender `fingerprint.py` com chave canônica de abertura/nó quando
   `model.py` ganhar uma.
4. Instrumentar o motor com um rastro de ordem de execução por parede
   para `pipeline_order.py` deixar de ser `NOT_AVAILABLE`.
