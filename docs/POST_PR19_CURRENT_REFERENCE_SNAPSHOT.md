# Post-PR19 Current Reference Snapshot

> Snapshot factual e reproduzível, medido do zero, imediatamente após o
> merge do PR #19 (`CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION`). Marco
> canônico para comparar as próximas CRs. Esta CR é SOMENTE
> snapshot/medição/documentação — nenhum arquivo de produção foi tocado
> (ver seção "Production diff" no final).

## Canonical main

```
MAIN (merge commit PR#19):  3ebcd9b63875f9114a3d6223aa648e5075e2d35b
MAIN ANTERIOR (base PR#19): 209695d5559b53fe4cc8a92300779a8ae73b7c1d
PR#19 HEAD (integrado):     9fcd01292eb4bff52af882968320610404d30bba
```

Confirmado via `git fetch origin` + `git rev-parse origin/main` +
`git merge-base --is-ancestor` (ambos os pais do merge commit
verificados: `209695d5` e `9fcd0129` são ancestrais de `3ebcd9b6`).

## Included merges

| PR | título | estado |
|---|---|---|
| #17 | CR-BLOCK-NODE-FILL-REVALIDATION | `merged` |
| #18 | CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY | `merged` |
| #19 | CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION | `merged` |

Confirmado via GitHub API (`pull_request_read`, method `get`) — os três
retornam `"state": "closed", "merged": true`.

## Environment

- Branch de trabalho: `claude/post-pr19-reference-snapshot-s01rhc`
  (já criada em `origin/main` na ponta `3ebcd9b6` no início desta
  sessão — usada como worktree isolado, sem trabalho de outra sessão).
- Python: solver rodado headless via `tests/load_script.py` +
  `tests/revit_stubs.py` (stubs do RevitAPI) + `nuvem/benchmark/solver_bridge.py`.
- `pytest` instalado nesta sessão (`pip install pytest`, versão 9.1.1)
  para rodar a suíte de testes.

## Method

Todas as métricas abaixo foram **medidas do zero** (nenhum número
antigo foi copiado de relatório anterior). Para cada projeto:

1. `input.json` carregado de `nuvem/benchmark/projects/<id>/input.json`.
2. `benchmark.solver_bridge.run_solver(input_project)` — roda o solver
   real (`nuvem/core/wall_modeling.py` + `nuvem/core/engine/wall_stepper.py`)
   sem escrever nada em disco.
3. `benchmark.extract.from_solver.project_from_solver(...)` — monta o
   projeto no formato do benchmark.
4. `benchmark.validators.run_all(...)` + `benchmark.scoring.score_project(...)`
   — os mesmos validadores/scorer oficiais do `runner.py`.
5. `benchmark.golden.fingerprint.component_fingerprints(...)` —
   fingerprint físico (`walls_blocks`) para os testes de determinismo e
   B19 ON/OFF.

Nenhum destes passos grava `score.json`/`result.json`/`baseline.json`
em disco (diferente do `runner.py --run`, que grava e sujaria o diff) —
o script auxiliar usado ficou fora do repositório
(`/tmp/.../scratchpad/snapshot_run.py`), só o resultado agregado foi
persistido em `nuvem/benchmark/diagnostics_post_pr19/current_snapshot.json`.

## TGD

### Geometry
- walls: **167**
- courses (fiadas): **17**
- blocks (peças totais): **10679**

### Blocks
Ver tabela cross-project abaixo.

### Findings
findings_total **4917** | critical **884** | non-critical **4033**

### ARM
`ARM_ROLE_SAFE_REPAIR_ENABLED = True`. Accepted: **2** — `wall_idx=23/SAME_A`,
`wall_idx=91/SAME_B`. Rejected: **19**, razões:
`does_not_resolve_target` (14), `row_coverage_regression:133` (1),
`row_coverage_regression:37` (1), `row_coverage_regression:132` (1),
`new_forced_prism_in_neighbor` (1), `new_consecutive_compensators:88` (1).

### B19
`B19_RESIDUAL_FILL_REPAIR_ENABLED = True`. Elegíveis (paredes): **0**.
Tentativas: **0**. Accepted: **0**. Rejected: **0**. Nenhum candidato no
corpus TGD tem a topologia/aritmética de resíduo elegível.

### NODE-FILL
`NODE_FILL_OPPOSITE_COURSE_ENABLED = True` (confirmado no código,
`nuvem/core/engine/wall_stepper.py:3384`). Preservado — findings de
`PRISM_CONTINUOUS_JOINT` (320) e `PRISM_JOINT_STACK` (19) refletem o
efeito acumulado de NODE-FILL (PR#17) + Gate Fidelity (PR#18) sobre o
valor pré-PR17 (444/27 — ver comparação abaixo).

## TP1

### Geometry
- walls: **96**
- courses (fiadas): **17**
- blocks (peças totais): **18417**

### Blocks
Ver tabela cross-project abaixo.

### Findings
findings_total **4905** | critical **469** | non-critical **4436**

### ARM
`ARM_ROLE_SAFE_REPAIR_ENABLED = True`. Accepted: **1** — `wall_idx=75/SAME_A`.
Rejected: **6**, razões: `does_not_resolve_target` (4),
`new_consecutive_compensators:13` (1), `new_consecutive_compensators:88` (1).

### B19
`B19_RESIDUAL_FILL_REPAIR_ENABLED = True`. Elegíveis (paredes): **8**.
Tentativas: **16** (8 paredes × 2 atribuições fill/tie). Accepted: **0**.
Rejected: **16**, 100% pela razão `no_tie_covering_node` (nenhum
candidato tem amarração real cobrindo o MESMO nó na MESMA fiada — o
padrão de alternância par/ímpar do canto L amarra o nó só nas fiadas
onde o B19 não está).

### NODE-FILL
`NODE_FILL_OPPOSITE_COURSE_ENABLED = True`. Preservado — `PRISM_CONTINUOUS_JOINT`
= 256 (efeito acumulado PR#17+PR#18 sobre o valor pré-PR17 de 576).

## Pilot

### Geometry
- walls: **12**
- courses (fiadas): **8**
- blocks (peças totais): **772**

### Blocks
Ver tabela cross-project abaixo.

### Findings
findings_total **124** | critical **8** | non-critical **116**

### ARM
Accepted: **0**. Rejected: **0** (no-op, 0 arestas candidatas — projeto
sintético 2x2 sem topologia de canto elegível).

### B19
Elegíveis: **0**. Nenhum efeito.

### NODE-FILL
`NODE_FILL_OPPOSITE_COURSE_ENABLED = True`. Sem efeito físico no Piloto
(0 `PRISM_CONTINUOUS_JOINT` antes e depois — projeto sem juntas
prisma-relevantes nesta escala).

## Cross-project metrics table

| métrica | TGD | TP1 | Piloto |
|---|---|---|---|
| PRISM_CONTINUOUS_JOINT | 320 | 256 | 0 |
| PRISM_JOINT_STACK | 19 | 16 | 0 |
| PRISM_STAGGER_BELOW_TARGET | 774 | 1370 | 14 |
| COVERAGE_MISSING_ROW | 258 | 0 | 0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 112 | 18 | 8 |
| COVERAGE_GAP_IN_ROW | 1959 | 327 | 16 |
| COVERAGE_PARTIAL_WALL | 61 | 6 | 0 |
| COVERAGE_WALL_NOT_MODULATED | 29 | 0 | 0 |
| POSITION_OVERLAP | 29 | 18 | 0 |
| COMPENSATOR_CONSECUTIVE | 379 | 1443 | 36 |
| COMPENSATOR_EXCESS_IN_RUN | 341 | 1067 | 28 |
| COMPENSATOR_VERTICAL_STRIP | 58 | 186 | 18 |
| COMPENSATOR_AVOIDABLE | 0 | 0 | 0 |
| OPENING_BLOCK_INSIDE_DOOR | 5 | 0 | 0 |
| OPENING_BLOCK_CROSSES_JAMB | 108 | 168 | 0 |
| OPENING_MISSING_LINTEL | 82 | 0 | 0 |
| OPENING_MISSING_COUNTER_LINTEL | 25 | 21 | 4 |
| OPENING_SOLID_BELOW_SILL_MISSING | 32 | 0 | 0 |
| JUNCTION_MISSING_BINDING | 23 | 9 | 0 |
| JUNCTION_HALF_BLOCK_ADJACENT | 0 | 0 | 0 |
| JUNCTION_NOT_ALTERNATING | 303 | 0 | 0 |
| **findings_total** | 4917 | 4905 | 124 |
| **critical_total** | 884 | 469 | 8 |
| **noncritical_total** | 4033 | 4436 | 116 |
| **walls** | 167 | 96 | 12 |
| **blocks** | 10679 | 18417 | 772 |
| **courses** | 17 | 17 | 8 |
| **collisions (= POSITION_OVERLAP)** | 29 | 18 | 0 |
| **ARM accepted / rejected** | 2 / 19 | 1 / 6 | 0 / 0 |
| **B19 eligible (walls) / attempted / accepted / rejected** | 0/0/0/0 | 8/16/0/16 | 0/0/0/0 |
| **runtime (s)** | 60.93 | 100.2 | 0.08 |
| **fingerprint walls_blocks** (prefixo) | `3f699aabbb09…` | `da02eeb3f350…` | `c012bb211914…` |

Nenhum código de finding fora desta lista apareceu nos três projetos
(conferido contra o conjunto completo de `counts_by_code` medido).

## B19 ON/OFF

Comparado `B19_RESIDUAL_FILL_REPAIR_ENABLED=True` vs `=False` nos três
projetos, mesmo `input.json`, mesma execução do solver, comparando o
fingerprint físico `walls_blocks`:

| projeto | fingerprint ON == OFF |
|---|---|
| TGD | **idêntico** |
| TP1 | **idêntico** |
| Piloto | **idêntico** |

Confirma o veredito do PR #19: zero efeito físico no corpus atual —
nenhum candidato passa o gate de integridade de nó (`_b19_tie_integrity_ok`)
em nenhum dos três projetos hoje.

## Fixed-point status

A convergência até ponto fixo de `repair_b19_residual_fill` (achado da
rodada 2 de revisão do PR #19, testes T54–T58) não é exercitada pelo
corpus atual — como `accepted == []` nos três projetos, o laço de
revalidação/remoção nunca remove nada (zero iterações além da
confirmação inicial). O mecanismo está testado sinteticamente (T54–T58,
ver seção "Focused tests") mas **não tem efeito observável no corpus
real hoje** — consistente com o resultado "zero efeito físico" acima.

## NODE-FILL preservation

`NODE_FILL_OPPOSITE_COURSE_ENABLED = True` confirmado em
`nuvem/core/engine/wall_stepper.py:3384`. Suíte própria
(`tests/test_block_node_fill_revalidation.py`) e testes de invariância
ARM×NODE-FILL (`tests/test_block_arm_role_prism_stagger.py`) — **33
testes, 33 passed** (parte da rodada focada de 140, ver abaixo). Sem
reabertura da investigação histórica — só confirmação de preservação
pós-PR19.

## Gate Fidelity preservation

`ARM_ROLE_SAFE_REPAIR_ENABLED = True` confirmado em
`nuvem/core/wall_modeling.py:3061`. Gates por `course_index` físico
(compensador) e crédito físico de nó bidirecional (cobertura)
preservados — accepted/rejected por projeto medidos acima batem
exatamente com os números do PR #18 (`TGD 23/SAME_A + 91/SAME_B`,
`TP1 75/SAME_A`). `wall_credit_node_indices` e `_arm_role_pinned`
seguem presentes no código (`nuvem/core/wall_modeling.py`,
`nuvem/core/engine/wall_stepper.py`) — não reaberto o PR #18.

## Determinism

Cada um dos três projetos executado **2x em processos Python
totalmente novos** (`python3 snapshot_run.py`, chamado duas vezes
separadamente), a segunda vez com `PYTHONHASHSEED=4242` explícito
(diferente do default da primeira execução). Comparado:

- fingerprint físico `walls_blocks` (hash sobre paredes/blocos/fiadas)
- `counts_by_code` completo (todos os achados, todos os validadores)

Resultado: **byte-idêntico** nos três projetos, nas duas dimensões.
Nenhuma divergência.

## Focused tests

```
python3 -m pytest \
  tests/test_block_b19_residual_fill_implementation.py \
  tests/test_block_arm_role_candidate_safety_contract.py \
  tests/test_block_arm_safe_repair_gate_fidelity.py \
  tests/test_block_node_fill_revalidation.py \
  tests/test_block_arm_role_prism_stagger.py -q
```

Resultado medido: **140 passed** em 1544.74s (25m44s). Nenhuma falha.
Inclui T54–T58 (convergência até ponto fixo do B19, cascata adversarial
A→B→C, cascata de 4 níveis, caso sem cascata, determinismo da
convergência).

## Full suite

```
python3 -m pytest tests -q
```

Resultado medido: **682 passed, 1 failed** em 2170.12s (36m10s).

## Known failure

```
tests/regression/test_benchmark_baselines.py::
  test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]

JUNCTION_MISSING_BINDING: before=8, after=9, delta=+1
status: REGRESSAO CRITICA (contra o baseline.json gravado)
```

Classificação histórica preservada: **PRE_EXISTING / P3 / BENCHMARK_ARTIFACT**
(baseline gravado com 8, o valor real medido pelo mesmo código é 9 desde
antes do PR #17 — ver `docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md`).
Nenhuma falha NOVA apareceu na suíte completa. Número medido bate
exatamente com o esperado pelo enunciado desta CR (682/1).

## Benchmark artifacts

Único artefato de benchmark conhecido no corpus atual é o
`JUNCTION_MISSING_BINDING` 8→9 do TP1 acima — nenhum artefato novo
encontrado nesta medição.

## Baseline/reference status

Confirmado por inspeção (`git status`/`git diff` durante toda a
sessão): **nenhuma escrita** em `baseline.json`, `reference.json` ou
`reference_score.json` de nenhum dos três projetos. A execução usada
nesta CR (`solver_bridge.run_solver` direto, ou `runner.run_project(...,
write_files=False)` dentro dos próprios testes de regressão) nunca
grava esses arquivos. Nenhum diff.

## Comparison with previous snapshot

Baseline de comparação: `docs/CURRENT_REFERENCE_SNAPSHOT.md`, medido em
`68a62693` (antes de PR#17/#18/#19).

| métrica | TGD antes | TGD agora | TP1 antes | TP1 agora | classificação |
|---|---|---|---|---|---|
| walls | 167 | 167 | 96 | 96 | idêntico (esperado) |
| blocks | 10672 | 10679 | 18368 | 18417 | EXPECTED_PR17/PR18/PR19 (peças de fill/tie ajustadas) |
| PRISM_CONTINUOUS_JOINT | 444 | 320 | 576 | 256 | EXPECTED_PR17 (444→336, 576→272) + EXPECTED_PR18 (336→320, 272→256); PR19 zero efeito (ON/OFF idêntico) |
| COMPENSATOR_CONSECUTIVE | 410 | 379 | 1469 | 1443 | TGD: EXPECTED_PR17 (410→379, medido no PR#17). TP1: PR#17 mediu 1469→1461; delta adicional de −18 até 1443 é **EXPECTED_PR18** (2º candidato ARM aceito em TP1 — `wall_idx=75/SAME_A` — muda posicionamento físico e portanto contagem de compensadores; PR#19/B19 excluído por fingerprint ON/OFF idêntico) |
| JUNCTION_MISSING_BINDING | 23 | 23 | 9 | 9 | idêntico — TP1=9 é o `PRE_EXISTING / P3 / BENCHMARK_ARTIFACT` já documentado (baseline gravado com 8) |
| POSITION_OVERLAP / collisions | 29 | 29 | 18 | 18 | idêntico |
| ARM accepted/rejected | 1/7 | 2/19 | 0/3 | 1/6 | EXPECTED_PR18 (Gate Fidelity: TGD +1 aceito `91/SAME_B`, TP1 +1 aceito `75/SAME_A`; rejected cresce porque o gate agora enumera por `course_index`, não por letra de família — mais linhas de rejeição, mesma decisão física) |

Nenhuma diferença **UNKNOWN** encontrada. Todas as diferenças físicas
observadas se explicam integralmente por PR#17 (NODE-FILL) e/ou PR#18
(Gate Fidelity), com PR#19/B19 confirmado como efeito físico **zero**
em todo o corpus (fingerprint ON/OFF idêntico nos três projetos —
seção "B19 ON/OFF" acima). Isso é consistente com o enunciado desta CR:
"qualquer diferença física real nova atribuída ao PR #19 é suspeita" —
nenhuma foi encontrada.

## Interpretation

O estado da `main` pós-PR19 é fisicamente **idêntico** ao estado
pós-PR18 (pré-PR19) para os três projetos do corpus atual — o mecanismo
B19 está implementado, testado (140 testes focados + T54–T58 de
convergência) e corretamente integrado ao pipeline (dirty-scope,
tie-integrity, ordem canônica, contrato `arm_role_safe_repair=False`
preservado), mas **não encontra nenhum candidato fisicamente elegível**
no corpus real hoje — os 8 candidatos topológicos do TP1 são todos
rejeitados por `no_tie_covering_node`. NODE-FILL (PR#17) e Gate Fidelity
(PR#18) seguem preservados e ativos, responsáveis por toda a diferença
física medida contra o snapshot anterior. Determinismo confirmado em
todas as dimensões medidas. A única falha da suíte completa é o
artefato de benchmark pré-existente e já documentado.

## Canonical numbers for next CR

```
MAIN:              3ebcd9b63875f9114a3d6223aa648e5075e2d35b
TGD:    walls=167  blocks=10679  courses=17  findings=4917  critical=884
TP1:    walls=96   blocks=18417  courses=17  findings=4905  critical=469
Piloto: walls=12   blocks=772    courses=8   findings=124   critical=8

ARM accepted:  TGD=2 (23/SAME_A, 91/SAME_B)  TP1=1 (75/SAME_A)  Piloto=0
B19 accepted:  TGD=0  TP1=0 (8 eligible, all rejected: no_tie_covering_node)  Piloto=0
B19 ON/OFF:    idêntico nos 3 projetos (zero efeito físico)

Full suite:    682 passed, 1 failed (JUNCTION_MISSING_BINDING TP1 8->9,
               PRE_EXISTING / P3 / BENCHMARK_ARTIFACT)
Focused suite: 140 passed, 0 failed

Determinismo:  fingerprint + counts_by_code byte-idênticos em 2
               processos novos (PYTHONHASHSEED diferente)
```

JSON machine-readable equivalente:
`nuvem/benchmark/diagnostics_post_pr19/current_snapshot.json`.
