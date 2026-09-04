# CURRENT REFERENCE SNAPSHOT

> **CURRENT STATE ONLY — REPLACEABLE SNAPSHOT.**
> **THIS FILE IS NOT A BASELINE, NOT HISTORY, NOT APPEND-ONLY.**
> Quando uma nova medição oficial for feita, o conteúdo abaixo deve ser
> SUBSTITUÍDO pela nova fotografia — não acumulado. Histórico de medições
> anteriores fica no Git (histórico deste arquivo) ou em relatórios
> específicos, nunca aqui.

Fotografia humana e legível do último estado oficialmente medido da
`main`, para dar contexto rápido a um agente sem precisar rodar o
benchmark. Não substitui `docs/REFERENCE_CORPUS.md` (que é o documento
vivo sobre o corpus) nem os arquivos de dados versionados em
`nuvem/benchmark/projects/*/` (`baseline.json`, `reference.json`,
`reference_score.json` - esses sim são a fonte de verdade numérica).

## Medição

```
MEASURED_AT:  d214c11a40fc7520bddab2e73e08d30615595656
CURRENT_MAIN: 4c89e1216cc6b5708c590f495e1584497e2df583
STATUS:       DESATUALIZADO — medido antes da integração do PR #9
              (ARM-ROLE invariance) e do PR #12 (ARM-ROLE candidate
              safety contract, já mesclado). Os números abaixo NÃO
              incluem nenhum resultado desses dois PRs. Repetir a
              medição (`py -3 nuvem/benchmark/runner.py --run
              <project_id>`) é recomendado antes de usar estes números
              para decisão fina.
```

## TGD (`torre_easy_lo_r00_tgd`)

| métrica | valor |
|---|---|
| walls | 167 |
| blocks | 10647 |
| COVERAGE_MISSING_ROW | 265 |
| COVERAGE_ROW_MOSTLY_EMPTY | 129 |
| PRISM_CONTINUOUS_JOINT | 702 |
| OPENING_BLOCK_INSIDE_DOOR | 5 |
| OPENING_BLOCK_CROSSES_JAMB | 108 |
| collisions | 1034 |

## TP1 (`torre_easy_lo_r00_tp1`)

| métrica | valor |
|---|---|
| walls | 96 |
| blocks | 18088 |
| COVERAGE_MISSING_ROW | 16 |
| COVERAGE_ROW_MOSTLY_EMPTY | 27 |
| PRISM_CONTINUOUS_JOINT | 837 |
| OPENING_BLOCK_INSIDE_DOOR | 0 |
| OPENING_BLOCK_CROSSES_JAMB | 168 |
| collisions | 14 |

## PILOTO (`piloto_sintetico_2x2`)

| métrica | valor |
|---|---|
| walls | 12 |
| blocks | 772 |
| COVERAGE_MISSING_ROW | 0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 8 |
| PRISM_CONTINUOUS_JOINT | 0 |
| collisions | 0 |

## Amarração (todos os projetos)

| métrica | valor |
|---|---|
| same-band forbidden | 0 nos três projetos |
| cross-band forbidden | 33 total |

## Como reproduzir

```bash
py -3 nuvem/benchmark/runner.py --run <project_id>
```

Ver `docs/REFERENCE_CORPUS.md` para o significado de cada métrica e o
procedimento completo de medição/comparação contra `reference.json`.
