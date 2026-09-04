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
MEASURED_AT:  68a62693ba4ac3a1def43be8b84d526372a4ee9a (2026-09-04)
CURRENT_MAIN: 68a62693ba4ac3a1def43be8b84d526372a4ee9a
STATUS:       ATUALIZADO — medido direto na ponta da main (PR #13
              integrado, docs-only). Nenhuma mudança de solver/baseline/
              reference desde a medição anterior; os deltas abaixo em
              relação ao snapshot anterior (medido antes de PR#9/PR#12)
              refletem só a integração do ARM-ROLE SAFE REPAIR.
```

Comando oficial usado: `python3 nuvem/benchmark/runner.py --run <project_id>`.
`FORBIDDEN_JOINT_ALIGNMENT` e `walls_with_blocks` vêm do script
complementar `nuvem/benchmark/diagnostics_block_prisma/run_baseline.py`
(não é a taxonomia oficial do runner — ver `docs/REFERENCE_CORPUS.md`).

## TGD (`torre_easy_lo_r00_tgd`)

| métrica | valor |
|---|---|
| walls | 167 |
| blocks | 10672 |
| COVERAGE_MISSING_ROW | 258 |
| COVERAGE_ROW_MOSTLY_EMPTY | 112 |
| COVERAGE_GAP_IN_ROW | 1959 |
| COVERAGE_PARTIAL_WALL | 61 |
| PRISM_CONTINUOUS_JOINT | 444 |
| PRISM_STAGGER_BELOW_TARGET | 690 |
| FORBIDDEN_JOINT_ALIGNMENT | 6 |
| JUNCTION_NOT_ALTERNATING | 303 |
| JUNCTION_MISSING_BINDING | 23 |
| OPENING_BLOCK_INSIDE_DOOR | 5 |
| OPENING_BLOCK_CROSSES_JAMB | 108 |
| COMPENSATOR_CONSECUTIVE | 410 |
| POSITION_OVERLAP / collisions | 29 |
| ARM candidates accepted/rejected | 1 / 7 (arestas) |
| runtime (runner completo) | 35,6s |

## TP1 (`torre_easy_lo_r00_tp1`)

| métrica | valor |
|---|---|
| walls | 96 |
| blocks | 18368 |
| COVERAGE_MISSING_ROW | 0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 18 |
| COVERAGE_GAP_IN_ROW | 327 |
| COVERAGE_PARTIAL_WALL | 6 |
| PRISM_CONTINUOUS_JOINT | 576 |
| PRISM_STAGGER_BELOW_TARGET | 1140 |
| FORBIDDEN_JOINT_ALIGNMENT | 18 |
| JUNCTION_NOT_ALTERNATING | 0 |
| JUNCTION_MISSING_BINDING | 9 |
| OPENING_BLOCK_INSIDE_DOOR | 0 |
| OPENING_BLOCK_CROSSES_JAMB | 168 |
| COMPENSATOR_CONSECUTIVE | 1469 |
| POSITION_OVERLAP / collisions | 18 |
| ARM candidates accepted/rejected | 0 / 3 (arestas) |
| runtime (runner completo) | 20,5s |

`JUNCTION_MISSING_BINDING=9` é a falha conhecida `P3 — BENCHMARK_ARTIFACT`
(baseline gravado com 8; ver `docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md`
e `tests/regression/test_benchmark_baselines.py`). Confirmada nesta
medição, `baseline.json` **não** alterado para escondê-la.

## PILOTO (`piloto_sintetico_2x2`)

| métrica | valor |
|---|---|
| walls | 12 |
| blocks | 772 |
| COVERAGE_MISSING_ROW | 0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 8 |
| COVERAGE_GAP_IN_ROW | 16 |
| COVERAGE_PARTIAL_WALL | 0 |
| PRISM_CONTINUOUS_JOINT | 0 |
| PRISM_STAGGER_BELOW_TARGET | 14 |
| FORBIDDEN_JOINT_ALIGNMENT | 0 |
| JUNCTION_NOT_ALTERNATING | 0 |
| JUNCTION_MISSING_BINDING | 0 |
| OPENING_BLOCK_INSIDE_DOOR | 0 |
| OPENING_BLOCK_CROSSES_JAMB | 0 |
| COMPENSATOR_CONSECUTIVE | 36 |
| POSITION_OVERLAP / collisions | 0 |
| ARM candidates accepted/rejected | 0 / 0 (no-op, 0 arestas candidatas) |
| runtime (runner completo) | 0,18s |

## ARM Safe Repair

`ARM_ROLE_SAFE_REPAIR_ENABLED = True` (`nuvem/core/wall_modeling.py`,
confirmado no código nesta medição). Accepted/rejected por projeto:
TGD 1/7, TP1 0/3, Piloto 0/0 — idêntico ao medido em
`docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md` pós-merge do PR #12.

## Determinismo

Cada projeto executado 2x (`runner.py --run`) e o ARM safe repair medido
2x via `solver_bridge.run_solver` direto: métricas, achados por classe e
`accepted`/`rejected` do ARM byte-idênticos entre as duas execuções. Única
diferença observada foi cosmética (ordem de exibição de duas linhas
empatadas na tabela solver×humano do TGD, mesmos valores).

## Como reproduzir

```bash
py -3 nuvem/benchmark/runner.py --run <project_id>
py -3 nuvem/benchmark/diagnostics_block_prisma/run_baseline.py --out out.json
```

Ver `docs/REFERENCE_CORPUS.md` para o significado de cada métrica e o
procedimento completo de medição/comparação contra `reference.json`.
