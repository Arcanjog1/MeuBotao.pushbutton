# CR-B — CANDIDATO E VALIDAÇÃO ESTRUTURAL DO GABARITO

> **Nada aqui é gabarito oficial.** Esta pasta contém apenas os
> GERADORES e os DIAGNÓSTICOS do candidato. `nuvem/benchmark/projects/**`
> (`reference.json`, `input.json`, `baseline.json`,
> `reference_score.json`, `evaluation_scope.json`) está **intocado** —
> conferido por `git diff --name-only`. O solver
> (`nuvem/core/engine/**`) e `nuvem/REGRAS_MODULACAO_BLOCOS.md` também.

| item | valor |
|---|---|
| base obrigatória | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` |
| branch | `claude/candidato-validacao-gabarito-q450yr` |
| fonte diagnóstica | `claude/reconciliacao-gabarito-aberturas-uynv0q` (`docs/BENCH_OPENING_RECONSTRUCTION_B_RECONCILIATION.md`) |
| versão do candidato | `cand-B-2026-09-07.1` |
| relatório | `docs/BENCH_OPENING_RECONSTRUCTION_B_CANDIDATE.md` |

## Por que o candidato NÃO está versionado como JSON

`reference.json` tem ~5,7 MB por projeto; o candidato completo somaria
~23 MB de artefato derivado. Em vez disso, versionamos o **gerador
determinístico** e os `sha256` esperados. O candidato é reproduzido
por comando, byte a byte (verificado em 3 processos novos).

## Como reproduzir

```bash
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate
export CR_B_OUT=/tmp/cr_b_candidate          # QUALQUER diretório fora de projects/
python3 build_candidate.py                    # gera o candidato + invariantes
python3 analyze_junctions.py                  # §5 — risco T→L
python3 analyze_divergences.py                # §6 — R1, R2, R3
python3 project_solver.py                     # §7 — projeção real do solver
```

Saída (em `$CR_B_OUT`):

```
candidate_manifest.json          versão, proveniência, changelog por identidade
                                 física, mapa de identidade, sha256
<proj>/reference_roundtrip.json  STATE_R — controle (round-trip SEM corte)
<proj>/reference_candidate.json  STATE_C — o candidato
<proj>/input_roundtrip.json      entrada derivada de STATE_R
<proj>/input_candidate.json      entrada derivada de STATE_C
junction_analysis.json           todo nó com tipo alterado, antes/depois
divergences.json                 R1/R2/R3, fonte medida x humano x candidato
solver_projection.json           solver de produção sobre cópias isoladas
```

## Os três estados (nunca misturar)

| estado | o que é | para que serve |
|---|---|---|
| **STATE_A** | `reference.json` oficial, como está em disco | o gabarito de hoje |
| **STATE_R** | round-trip do gabarito **sem corte** | **controle**. Isola o efeito da CR-A (consenso), já mesclado na `main` mas ainda **não propagado** para o gabarito |
| **STATE_C** | STATE_R **+ corte estrutural C1** nos 19 casos | o candidato |

**Todo delta reivindicado por esta CR é `STATE_C − STATE_R`.**
Comparar STATE_C com STATE_A somaria dois efeitos diferentes: as **31
aberturas por projeto** cuja geometria muda de envelope para consenso
(CR-A, já decidida e mesclada) e os **19 cortes** (esta CR).

## O critério — estrutural, sem limiar de largura

`C1`: as **duas** jambas do vão coincidem (≤ 1,0 cm) com a face interna
de uma parede **perpendicular** que cruza o eixo (reserva de nó nos dois
lados). `WALL_SPLIT_GAP_CM` e `OPENING_GAP_MAX_CM` permanecem **260,0** —
medido na reconciliação (§5.1) que nenhum limiar de largura separa os 19
sem destruir porta medida real.

A tolerância de 1,0 cm é de **classificação**, não de geometria: nenhuma
coordenada gravada vem dela. Abertura com `source_element_id` nunca entra
neste caminho (verificado: 0 das 19 removidas tem `source_element_id`).

## Estatuto epistêmico

O critério estrutural é **heurística de extração validada neste corpus**
(19/19 acertos, 0 falsos positivos em 148 trechos de controle de dois
níveis do MESMO edifício) — **não** é regra normativa geral de modulação.
Promovê-lo a regra em `nuvem/REGRAS_MODULACAO_BLOCOS.md` depende da
decisão **D5**, que não foi tomada.
