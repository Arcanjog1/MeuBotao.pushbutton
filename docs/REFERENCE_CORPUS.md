# Reference Corpus — benchmark de referência da modulação

`CR-BLOCK-REFERENCE-CORPUS`. Evolução do `CR-BLOCK-GOLDEN-BENCHMARK`
(ver [`docs/archive/GOLDEN_BENCHMARK.md`](archive/GOLDEN_BENCHMARK.md) para o histórico).
Este é o ponto de entrada atual.

> Paralela ao `CR-BLOCK-DETERMINISM` (outra conta, em
> `nuvem/core/engine/wall_stepper.py`). Nada aqui importa nem altera
> `wall_stepper.py`, `wall_pairing.py`, `geometry.py`, `tolerances.py`,
> `continuous_modulation.py`, `modulation_math.py` ou `wall_modeling.py`.

## A mudança de estratégia

**Antes** (Golden Benchmark): só participava do benchmark um projeto
"golden o suficiente".

**Agora** (Reference Corpus): **todo projeto com dado suficiente
participa**. `GOLDEN_CONFIRMED` continua existindo — é só o **nível mais
alto de confiança**, nunca requisito de entrada.

```
reference_type != GOLDEN_CONFIRMED   NÃO impede comparação, execução,
                                      diff, regressão nem análise.
                                      Só muda o nível de confiança e a
                                      interpretação do resultado.
```

## Dois eixos, não um enum gigante

Cada projeto do corpus é classificado em **dois eixos independentes**
(`nuvem/benchmark/golden/manifest.py`):

| Eixo | Pergunta | Valores |
|---|---|---|
| `reference_kind` | O QUE produziu o dado? | `HUMAN` / `SOLVER` / `SYNTHETIC` / `ANALYSIS_ONLY` / `UNKNOWN` |
| `confidence` | QUANTO confiar nisso como verdade de correção? | `NONE` → `LOW` → `MEDIUM` → `HIGH` → `GOLDEN` |

```
REFERENCE PROJECT
   │
   ├── reference_kind=SOLVER,    confidence=LOW      "SOLVER_REFERENCE" / LEGACY_BASELINE
   ├── reference_kind=SYNTHETIC, confidence=NONE      grade sintética (determinismo/invariantes)
   ├── reference_kind=HUMAN,     confidence=MEDIUM     "HUMAN_REFERENCE_AVAILABLE"
   ├── reference_kind=HUMAN,     confidence=HIGH        "HUMAN_VERIFIED" (extração revisada)
   └── reference_kind=HUMAN,     confidence=GOLDEN       "GOLDEN_CONFIRMED" — o TETO
```

O **rótulo legado** (`reference_type`: `GOLDEN_CONFIRMED` /
`HUMAN_REFERENCE_AVAILABLE` / `LEGACY_BASELINE` / `SOLVER_GENERATED_ONLY`
/ `ANALYSIS_ONLY_REFERENCE` / `UNKNOWN`) continua existindo — nenhum
import antigo quebra. `manifest.new_entry(...)` **deriva**
`reference_kind`/`confidence` sozinho a partir dele
(`manifest.LEGACY_TO_AXES`) quando eles não são passados explicitamente.

### Promoção entre níveis de confiança (nunca automática)

`manifest.promote(entry, to_confidence, evidence, ...)` sobe um nível,
sempre com `evidence` obrigatória e sempre devolvendo uma **cópia nova**
(a entrada original nunca é mutada — histórico preservado em
`promotion_history`):

| Degrau | Exige |
|---|---|
| `MEDIUM` → `HIGH` (HUMAN_VERIFIED) | `verified_at` (+ `verified_by` recomendado): alguém revisou a extração contra a fonte |
| `HIGH` → `GOLDEN` (GOLDEN_CONFIRMED) | `validated_at` **e** `approved_by_human: true`: aprovação formal registrada |

`validate_entry(...)` recusa: `GOLDEN` sem os dois campos acima; `HIGH`
sem `verified_at`; `GOLDEN` com `reference_kind` diferente de `HUMAN`;
`ANALYSIS_ONLY` marcado `reproducible: true` ou com `confidence`
diferente de `NONE`. Nunca levanta exceção sozinho ao *ler* uma entrada —
só `promote()`/`make_manifest()` recusam ativamente uma entrada inválida.

**Hoje, nenhum projeto do repositório é `confidence=GOLDEN`** — não há
prova de validação humana formal registrada para nenhum (mesmo
raciocínio do CR anterior, ver `docs/archive/GOLDEN_BENCHMARK.md`).

## Capabilities — o que cada projeto sustenta testar (item 12)

Um projeto **parcial** participa do corpus, só que apenas nas
comparações que os dados dele sustentam. `nuvem/benchmark/golden/capabilities.py`
infere **mecanicamente** (nunca decide confiança) o que cada projeto tem:

```
CAN_TEST_WALL_COVERAGE      CAN_TEST_LTX               CAN_COMPARE_TO_HUMAN
CAN_TEST_BLOCK_LAYOUT       CAN_TEST_DETERMINISM       CAN_TEST_PROCESS_ORDER
CAN_TEST_PRISM              CAN_TEST_OPENINGS          CAN_TEST_CONTINUOUS_FIRST
```

`CAN_TEST_CONTINUOUS_FIRST` nunca é inferida `True` hoje — depende de
`pipeline_trace.py` (ver abaixo), e o motor ainda não emite esse rastro.
Nenhuma capability geral vira "todos tem tudo": o que faltar fica de fora
da lista, nunca inventado.

## O Reference Corpus (`golden/corpus.py`)

```python
from benchmark.golden import corpus

rc = corpus.ReferenceCorpus.load_default()
rc.list_projects()                                    # todos os project_id
rc.get_project("torre_easy_lo_r00_tgd")                # entrada do manifesto, ou None
rc.filter_by_capability(capabilities.CAN_TEST_OPENINGS)
rc.filter_by_reference_kind(manifest.KIND_HUMAN)
rc.filter_by_confidence(minimum=manifest.CONFIDENCE_MEDIUM)
rc.reproducible_projects()
rc.human_reference_projects()
rc.golden_projects()                                    # [] hoje
rc.analysis_only_projects()
```

`ReferenceCorpus` é só uma **fachada de leitura** sobre `manifest.json` —
a classificação continua 100% humana, gravada a mão.

### Executar o corpus inteiro

```python
rows = corpus.run_corpus(rc)                            # ou project_ids=[...]
summary = corpus.summarize_corpus_run(rows)              # counts + overall
matrix = corpus.build_matrix(rows)                        # projeto x metrica
```

`run_corpus` **nunca roda o solver** e **nunca regrava artefato** — só lê
o que já está gravado (`baseline.json`/`score.json` por padrão, os
mesmos nomes de `tools/run_golden_compare.py`). Um projeto sem os dois
artefatos, ou `reference_kind=ANALYSIS_ONLY`/não reprodutível, entra como
`NOT_COMPARABLE` com o motivo — nunca descartado em silêncio.

**Regra dura** (item 19): se **qualquer** projeto comparável tiver
regressão crítica, `summary["overall"]` é sempre
`CRITICAL_REGRESSION_PRESENT` — nunca "11 melhoraram, 1 quebrou porta →
overall improved". Testado literalmente em
`test_summarize_corpus_run_nunca_esconde_regressao_critica_atras_de_media`.

## CLI

```bash
# um projeto so'
py -3 nuvem/benchmark/tools/run_reference_corpus.py --project torre_easy_lo_r00_tgd

# o corpus inteiro
py -3 nuvem/benchmark/tools/run_reference_corpus.py --all

# so' quem sustenta comparar com humano
py -3 nuvem/benchmark/tools/run_reference_corpus.py --all --capability CAN_COMPARE_TO_HUMAN

# grava JSON completo + relatorio Markdown
py -3 nuvem/benchmark/tools/run_reference_corpus.py --all --out-json corpus.json --out-md corpus.md
```

`tools/run_golden_compare.py` (do CR anterior) continua existindo e
funcionando igual — é o motor por-projeto que `run_reference_corpus.py`
reaproveita por baixo.

## Fingerprint canônico — agora cobre abertura e L/T/X (itens 22-24)

O CR anterior documentava como limitação: "fingerprint não cobre
abertura/nó L-T-X adequadamente". Corrigido em
`nuvem/benchmark/golden/fingerprint.py`:

* **Bug de reversão corrigido primeiro**: `t_start_cm`/`t_end_cm` de
  blocos e aberturas são medidos a partir do `start_cm` que aquele objeto
  guarda — duas cópias da MESMA parede física, uma desenhada
  ponta-A→ponta-B e outra ponta-B→ponta-A, têm os blocos físicos com
  `t_*` **espelhados**. O fingerprint do CR anterior não corrigia isso
  (o teste que "provava" invariância a reversão era tautológico — usava
  o mesmo bloco cru dos dois lados). Corrigido: `_wall_is_reversed`/
  `_canonical_t_range` detectam e espelham antes de assinar.
* **Abertura**: `opening_signature` — tipo, centro no eixo (canônico),
  largura, altura, peitoril, parede associada
  (`model.opening_stable_key`).
* **Nó L/T/X**: `canonical_junction_signatures` agrupa pelo **ponto
  físico** (`point_cm`), nunca pelo índice `neighbors` que
  `extract/reconstruct.py::detect_junctions` grava — esse índice é
  `wall_idx` da extração, exatamente o que é proibido usar como
  identidade (item 22). Tipos divergentes entre cópias do mesmo nó
  aparecem como conflito visível, nunca escondidos.
* `component_fingerprints(project)` devolve hash separado por parte
  (`walls_blocks`/`openings`/`junctions`) + o geral — ajuda a apontar
  QUAL parte mudou quando o fingerprint geral muda.

Validado com `torre_easy_lo_r00_tgd` real: 94 aberturas e 155 nós L/T/X
hasheados em ~0,2s.

## Diff parede → fiada → bloco (preservado e reaproveitado)

`wall_diff.py` (do CR anterior) continua a fonte — `ADDED`/`REMOVED`/
`MOVED`/`CHANGED_CODE` por parede e por fiada, em cima do
`compare_projects.py` já existente.

## Comparação HUMANO x SOLVER (itens 40-41)

`nuvem/benchmark/golden/human_reference.py` classifica cada diferença
num vocabulário mais fino que ADDED/REMOVED/MOVED/CHANGED_CODE:

```
IDENTICAL              mesma peca, mesmo lugar
EQUIVALENT               peca diferente, MESMO intervalo, nivel 1 ok
DIFFERENT_VALID           layout diferente, nivel 1 ok - solucao diferente, nao errada
POTENTIAL_REGRESSION       ha achado de nivel 1 na parede E a diferenca e' de layout
RULE_VIOLATION               ha achado de nivel 1 numa TROCA de peca no mesmo lugar
UNKNOWN                       sem achados pra checar - NUNCA adivinhado como valido
```

Cruza o diff já calculado com achados de nível 1 dos validadores
**existentes** (`validators/base.py`) — nunca reimplementa regra (item
43). Sem a lista de `findings`, uma diferença de layout fica `UNKNOWN`
(não `DIFFERENT_VALID` adivinhado) — só uma troca de peça no mesmo lugar
(`EQUIVALENT`) é um fato estrutural que não precisa de achado para ser
afirmado.

## Pipeline trace — schema preparado, não implementado em produção (itens 27-30)

**Não alterado nesta tarefa**: `wall_stepper.py`,
`continuous_modulation.py`. O que existe é só o **contrato**
(`nuvem/benchmark/golden/pipeline_trace.py`):

```python
pipeline_trace.make_trace_event(wall_id, stage, sequence,
                                opening_id=None, affected_region=None, metadata=None)
```

8 estágios oficiais, na ordem (item 27 do pedido):

```
WALL_START → INTERSECTIONS_RESOLVED → CONTINUOUS_FILL → PRISM_VALIDATED
   → OPENING_APPLIED → CONFLICTING_BLOCK_REMOVED → LOCAL_REPAIR → FINAL_VALIDATION
```

Uma parede **sem abertura** pode pular os três estágios só-de-abertura
(`OPENING_APPLIED`/`CONFLICTING_BLOCK_REMOVED`/`LOCAL_REPAIR`) — uma
abertura é um vazio *dentro* da parede contínua (item 27), não um
estágio universal.

`pipeline_trace.parse_trace(raw_events)` nunca lê arquivo sozinho (só
recebe dados já em memória) e nunca derruba o parser inteiro por um
evento malformado — reporta o problema por índice.
`pipeline_trace.validate_trace(events)` checa, por parede: `sequence`
estritamente crescente + estágios na ordem oficial.

### `continuous_first` — honestamente `NOT_AVAILABLE`

```python
from benchmark.golden import pipeline_order
pipeline_order.continuous_first_evidence_from_trace(events)   # forma nova, por parede
pipeline_order.continuous_first_evidence(stage_trace)          # forma antiga, mantida
```

**Sem rastro, a resposta é SEMPRE `NOT_AVAILABLE`** — nunca um "sim"
inventado a partir do resultado final (compatível com mais de uma ordem
de execução). Isto continua verdade nesta tarefa: o motor ainda não
emite pipeline trace. Quando emitir, as duas funções acima já sabem
comparar contra a ordem oficial.

## Ordem oficial das paredes (preservada do CR anterior)

`nuvem/benchmark/golden/wall_order.py` — horizontais primeiro (cima→baixo,
empate esquerda→direita), depois verticais (baixo→cima, empate
esquerda→direita), depois inclinadas por geometria canônica. Infraestrutura
de validação apenas, nunca chamada pela produção.

## Manifesto (`manifest.json`) — agora é catálogo do corpus

Regenerável com:

```bash
py -3 -m nuvem.benchmark.tools.build_manifest
```

Este script é o **"1 lugar"** (item 31) para cadastrar um projeto novo:
colocar os dados em `nuvem/benchmark/projects/<id>/` (ou registrar como
`ANALYSIS_ONLY_REFERENCE` quando só há resumo/censo), acrescentar uma
linha em `ENTRIES` dentro do script (com a classificação HUMANA — nunca
inferida sozinha) e rodar o script. `capabilities`/`available_metrics`
são inferidos mecanicamente pelo próprio script.

### Os 5 projetos catalogados hoje

| project_id | reference_kind | confidence | reproducible | origem |
|---|---|---|---|---|
| `torre_easy_lo_r00_tgd` | HUMAN | MEDIUM | sim | par de documentos Revit reais (input medido + nível 04. TGD) |
| `torre_easy_lo_r00_tp1` | HUMAN | MEDIUM | sim | projeto Revit entregue, nível 05. TP1 |
| `piloto_sintetico_2x2` | SYNTHETIC | NONE | sim | grade sintética gerada por `extract/synthetic.py` |
| `chacara_torre_easy_lo_tropicale` | ANALYSIS_ONLY | NONE | não | censo agregado (`nuvem/diagnosticos/CHACARA-TORRE-EASY-LO.md`) — **novo**, achado na varredura desta tarefa |
| `torre_easy_lo_r00_full_building` | ANALYSIS_ONLY | NONE | não | os ~19 níveis do mesmo edifício de TGD/TP1 ainda não extraídos (`nuvem/diagnosticos/TORRE_EASY-LO-R00.md`) — **novo** |

Os dois `ANALYSIS_ONLY` têm `missing_requirements` explícito no
manifesto — o que falta extrair para virarem projeto de verdade. Nenhum
foi inventado como reproduzível: nenhum tem `input.json`/geometria por
parede, só contagem agregada de peças por tipo.

### Varredura do repositório (item 5/6)

Buscado por: `project`, `projects`, `benchmark`, `baseline`, `reference`,
`result`, `input`, `score`, `findings`, `diagnostics`, `audit`, `TGD`,
`TP1`, `piloto`, `synthetic`, `Revit`, `RVT`, `human`, `approved`,
`comparison`, `regression`, `solver_bench`, `wall`, `block`, em
`nuvem/benchmark/**`, `tests/**`, `docs/**`, `nuvem/*.md`.

**Confirmado**: `diagnostics_2c/…2k/`, `diagnostics_block_audit/`,
`diagnostics_block_prisma/` são todos slices/censos DERIVADOS dos 3
projetos já catalogados (`lib_audit.py::PROJECT_IDS`) — nenhum projeto
novo escondido ali. `tests/solver_bench.py` gera grades sintéticas
procedurais (`(2,2)`, `(3,2)`, `(3,3)`) só para regressão de performance/
fingerprint do motor — não são "projetos" no sentido de referência de
modulação, e não foram catalogados. Os únicos dois achados novos foram os
`ANALYSIS_ONLY_REFERENCE` da tabela acima.

## Limitações explícitas

* **Nenhum projeto é `confidence=GOLDEN`** — segue sem prova de
  validação humana formal para nenhum dos dois projetos `HUMAN`. A
  arquitetura de promoção já está pronta (`manifest.promote`).
* **`CAN_TEST_CONTINUOUS_FIRST` nunca é `True` hoje** — depende de
  pipeline trace, que o motor não emite.
* **Os dois `ANALYSIS_ONLY_REFERENCE`** (`chacara_torre_easy_lo_tropicale`,
  `torre_easy_lo_r00_full_building`) não têm nenhum dado executável —
  só entram no corpus como registro do que falta extrair.
* **Fingerprint de junção não valida geometricamente `neighbors`** —
  usa só `point_cm` + a chave de cada parede que guarda uma cópia do nó;
  se a extração nunca gravar a cópia do nó numa das paredes participantes,
  aquela parede simplesmente não aparece no grupo (sem crash, mas sem
  aviso automático de "faltou" — fica para quem lê o diagnóstico notar).
* **`pipeline_trace.py` é só o contrato** — o motor não emite nada disso
  ainda; nenhuma alteração em `wall_stepper.py`/`continuous_modulation.py`
  foi feita ou é necessária para o schema existir.

## Como adicionar um projeto novo (item 37 — preparação, não implementado)

```
EXTRAÇÃO (mcp__revit-pyrevit__execute_revit_code, READ-ONLY)
   ↓
REFERENCE DATASET (input.json / input_real.json + reference.json,
                    mesmo schema de benchmark/model.py)
   ↓
REGISTRO NO CORPUS (uma linha em ENTRIES de tools/build_manifest.py,
                    classificacao HUMANA de reference_kind/confidence)
   ↓
py -3 -m nuvem.benchmark.tools.build_manifest
   ↓
COMPARAÇÃO AUTOMÁTICA (tools/run_reference_corpus.py --project <id>)
```

Nenhum parser de `.rvt` foi criado nesta tarefa (item 37 pede
explicitamente para não implementar isso ainda) — só a interface acima,
que já existe e já funciona para os 5 projetos catalogados.

## Como promover um projeto para `GOLDEN_CONFIRMED`

```python
from benchmark.golden import manifest

data = manifest.load_default()
entry = manifest.get(data, "torre_easy_lo_r00_tgd")

# 1. MEDIUM -> HIGH: alguem revisa a extracao contra o .rvt original
high = manifest.promote(entry, manifest.CONFIDENCE_HIGH,
                        evidence="revisei X, Y, Z contra o modelo original",
                        by="nome_de_quem_revisou")

# 2. HIGH -> GOLDEN: aprovacao formal
golden = manifest.promote(high, manifest.CONFIDENCE_GOLDEN,
                          evidence="aprovado formalmente em <processo/reuniao>",
                          by="responsavel_tecnico",
                          extra_fields={"approved_by_human": True})

# 3. gravar manualmente em manifest.json (nunca automatico)
```

`manifest.promote` nunca é chamado por `inventory.py`/`build_manifest.py`
— sempre uma ação humana explícita, com evidência (item 32/38).
