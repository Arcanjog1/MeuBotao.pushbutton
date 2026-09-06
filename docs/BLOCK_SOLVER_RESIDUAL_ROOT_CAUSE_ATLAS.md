# Block Solver Residual Root-Cause Atlas

`CR-BLOCK-SOLVER-RESIDUAL-ROOT-CAUSE-ATLAS` — investigação forense, **ZERO
alteração de produção**, sobre os defeitos residuais do solver de blocos
na `main` atual. Toda contagem abaixo foi **reexecutada nesta sessão**
(nenhum número antigo reaproveitado como verdade). Scripts, saídas
resumidas e reprodutores em `nuvem/benchmark/diagnostics_residual_atlas/`
(README lá). Saída machine-readable:
`nuvem/benchmark/diagnostics_residual_atlas/root_cause_atlas.json`.

## Baseline

```
base canônica:  origin/main = 209695d5559b53fe4cc8a92300779a8ae73b7c1d
branch diag.:   claude/block-solver-residual-root-cause-gwcmqa (worktree isolado /home/user/atlas-wt)
python:         3.11.15 (stubs de tests/revit_stubs.py; solver REAL via benchmark/solver_bridge.py)
PR #19:         NÃO usado, NÃO tocado (resultado físico observado no corpus = 0)
produção:       git diff origin/main --name-only -> nenhum arquivo de nuvem/core/** alterado
baseline.json / reference.json / reference_score.json: intactos
```

## Current metrics

`run_state_current.py` (solver real + validadores oficiais; mesma chamada
de `runner.run_project`, sem gravar em `projects/`):

| métrica | TGD | TP1 | Piloto |
|---|---|---|---|
| walls / blocks | 167 / 10 679 | 96 / 18 417 | 12 / 772 |
| PRISM_CONTINUOUS_JOINT | 320 | 256 | 0 |
| PRISM_JOINT_STACK | 19 | 16 | 0 |
| PRISM_STAGGER_BELOW_TARGET (nível 2) | 774 | 1 370 | 14 |
| COVERAGE_MISSING_ROW | 258 | 0 | 0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 112 | 18 | 8 |
| COVERAGE_GAP_IN_ROW | 1 959 | 327 | 16 |
| COVERAGE_PARTIAL_WALL | 61 | 6 | 0 |
| COVERAGE_WALL_NOT_MODULATED | 29 | 0 | 0 |
| POSITION_OVERLAP | 29 | 18 | 0 |
| COMPENSATOR_CONSECUTIVE | 379 | 1 443 | 36 |
| COMPENSATOR_EXCESS_IN_RUN | 341 | 1 067 | 28 |
| COMPENSATOR_VERTICAL_STRIP | 58 | 186 | 18 |
| COMPENSATOR_AVOIDABLE (nível 2) | 37 | 86 | 0 |
| OPENING_BLOCK_INSIDE_DOOR | 5 | 0 | 0 |
| OPENING_BLOCK_CROSSES_JAMB | 108 | 168 | 0 |
| OPENING_SOLID_BELOW_SILL_MISSING | 32 | 0 | 0 |
| OPENING_MISSING_LINTEL / COUNTER (nível 2) | 82 / 25 | 0 / 21 | 0 / 4 |
| JUNCTION_MISSING_BINDING | 23 | 9 | 0 |
| JUNCTION_NOT_ALTERNATING | 303 | 0 | 0 |
| JUNCTION_HALF_BLOCK_ADJACENT | 0 | 0 | 0 |
| solver `collisions` / `door_void_violations` | 1 043 / 290 | 14 / 348 | 0 / 0 |
| solver `intersection_failures` / `non_modular` | 200 / 3 047 | 0 / 281 | 0 / 32 |
| ARM safe repair accepted / rejected (candidatos) | 2 / 19 | 1 / 6 | 0 / 0 |
| runtime solver | 45,6 s | 25,2 s | 0,06 s |
| fingerprint físico | `09bc1b0c…` | `8d08d591…` | `e66bcd80…` |

Delta contra `docs/CURRENT_REFERENCE_SNAPSHOT.md` (medido em `68a6269`,
antes de NODE-FILL e Gate Fidelity): PRISM TGD 444→320, TP1 576→256
(coerente com 336→320 / 272→256 documentados); COMPENSATOR_CONSECUTIVE
TGD 410→379, TP1 1 469→1 443; demais iguais. `JUNCTION_MISSING_BINDING`
TP1 = 9 (o "P3" — ver cluster C19: **não** é artefato de benchmark).

**Piso de ruído humano** (`reference_score.json`, validadores rodados no
gabarito): PRISM 126 / 122; COMPENSATOR_CONSECUTIVE 52 / 52; COVERAGE_GAP
626 / 615; JUNCTION_MISSING_BINDING 373 / 365; **JUNCTION_HALF_BLOCK_
ADJACENT 264 / 259** (o humano encosta B19 em amarração rotineiramente);
OPENING_BLOCK_CROSSES_JAMB 208 / 209 (as aberturas reconstruídas são mais
largas que o vão real — ver C03).

## Method

1. STATE_CURRENT reexecutado (3 projetos), `run.pkl` cacheado para os
   demais scripts.
2. Inventário físico por achado (`inventory.py`): `wall_idx` ↔ `W###`
   pela chave geométrica (`assign_ids` renumera — `W###` ≠ `wall_idx+1`
   no TGD), orientação, comprimento, nós de ponta/meio (tipo, degradado,
   peças por fiada, dono), aberturas ativas na fiada, banda,
   `placement_reason` das peças do achado, feição mais próxima (nó/vão/
   ponta), composição humana no mesmo `t` (eixo do solver, com inversão
   de sentido corrigida e união de TODAS as paredes humanas colineares —
   necessário no TGD, onde o solver fragmenta a parede humana).
3. Clustering causal automático (`cluster_assign.py`) a partir de cinco
   decomposições independentes: assinaturas de prisma
   (`prism_signatures.py`), cadeias de compensadores com contexto físico
   (`compensator_chains.py`), cobertura por causa
   (`coverage_decomposition.py`), aberturas por causa
   (`openings_decomposition.py`), primeira divergência solver×humano
   fiada a fiada (`first_divergence.py`) + paridade por nó
   (`node_parity.json`).
4. Instrumentação por monkeypatch em memória (nunca em produção):
   traço do recorte/reparo de aberturas (`probe_opening_repair.py`),
   tempo por estágio (`run_performance.py`), **ablações de prova**
   (`run_ablation.py`: tolerância de fechamento, folga no room check do
   X, ARM desligado).
5. Reprodutores mínimos (`repro_lib.py`/`run_reproducers.py`), testes de
   invariância (`run_invariance.py`) e determinismo em processos novos
   com `PYTHONHASHSEED` distintos (`run_determinism.py`).
6. Toda geometria "estranha" foi remedida direto nos objetos do solver
   (extensão real das peças no eixo, `block_covers_point` do validador,
   room checks chamados com os mesmos argumentos da produção).

## Corpus limitations

- TGD e TP1 são **o mesmo edifício/planta** (níveis 04 e 05), do mesmo
  projetista: todo "padrão humano" abaixo tem N=1 planta — nível
  **HYPOTHESIS** para generalização, **SUPPORTED** dentro deste corpus.
- TP1: entrada **reconstruída** do gabarito; as aberturas reconstruídas
  são **infladas** pelos corpos das peças de amarração dos T adjacentes
  (C03) — o próprio gabarito acusa 209 `OPENING_BLOCK_CROSSES_JAMB`.
- TGD: entrada **medida** (CAD), mas o Wall Modeling (Fase A) produz 167
  eixos contra 97 humanos: 73 fragmentos colineares de paredes humanas
  longas, 38 eixos sem parede humana colinear (duplicatas a 12,7 cm,
  tocos de 4–40 cm), 15 fora do escopo. O casamento 1:1 deixa 83 eixos
  "sem humano". **63 % dos achados de nível 1 do TGD estão em fragmentos
  ou eixos espúrios** (1 875 + 795 de 4 036).
- Catálogo: solver 6 códigos; humano 15 (cortados `*_C`, canaletas
  CAN34/CAN39/CJ19/CM19) — `OPENING_MISSING_LINTEL/COUNTER` são escopo de
  catálogo, não defeito de modulação.
- Nenhum projeto é `GOLDEN`; o piloto é sintético (controle/regressão).

## Global finding inventory

Nível 1 por classe de parede (TGD): fragmento colinear 1 875 · pontas
casadas 1 245 · espúria/não construída 795 · fora de escopo 121. TP1:
todos os 96 eixos casam ponta a ponta com o humano.

Atribuição causal automática (nível 1; `cluster_summary.json`):

| cluster | TGD | TP1 | Piloto |
|---|---|---|---|
| C01 SHORT_WALL_NODE_ROLE | 151 | 652 | 0 |
| C02 X_ROOM_BORDERLINE_DEGRADED | 0 | 236 | 0 |
| C03 NODE_INSIDE_OPENING_SPAN | 84 | 338 | 0 |
| C04 FIT_TOLERANCE_NOISE | 215 | 176 | 0 |
| C04b NONMODULAR_TRECHO_GEOMETRY | 275 | 32 | 0 |
| C05 DEGRADED_NODE_PIECE_RESIDUE | 374 | 738 | 16 |
| C06 REPAIR_RESIDUE_NEAR_OPENING | 101 | 410 | 75 |
| C07 FILL_RESIDUE_BETWEEN_TIES | 214 | 756 | 7 |
| C08 PHASEA_FRAGMENT_NONMODULAR | 1 564 | 0 | 0 |
| C09 ROTATED_CORNER_SAME_WALL | 480 | 0 | 0 |
| C10 REPAIR_ANCHOR_RECREATES_NODE_JOINT | 0 | 20 | 0 |
| C11 NODE_FILL_JOINT_RESIDUAL | 22 | 0 | 0 |
| C12 FILL_FILL_PRISM_OTHER (cross-band) | 6 | 12 | 0 |
| C13 NODE_RESERVE_EXCEEDS_WALL (SEM_ESPACO) | 24 | 0 | 8 |
| C14 INTERSECTION_FAILURE_NO_PIECE | 175 | 0 | 0 |
| C15 NODE_RESERVE_WITHOUT_PIECE_THIS_COURSE | 62 | 0 | 0 |
| C16 OPENING_REPAIR_FAILED | 102 | 25 | 0 |
| C17 FILL_DROPPED_BY_TIE_COLLISION | 51 | 0 | 0 |
| C18 JUNCTION_NOT_ALTERNATING_OTHER | 31 | 0 | 0 |
| C19 L_ARM_NOT_EXTENDED / C04_TOO_SHORT | 23 | 9 | 0 |
| C20 NODE_PIECE_ROOM_CHECK_MISS | 29 | 0 | 0 |
| C21 NODE_PIECES_COLLIDE | 29 | 18 | 0 |
| V01 VALIDATOR_FOREIGN_PIECE_NOT_CREDITED | 5 | 76 | 0 |
| D01 derivado (PRISM_JOINT_STACK) | 19 | 16 | 0 |
| **total nível 1** | **4 036** | **3 514** | **106** |

## Root-cause clusters

### C01 — SHORT_WALL_NODE_ROLE (parede curta entre dois nós)
- **Validator codes**: COMPENSATOR_CONSECUTIVE, COMPENSATOR_EXCESS_IN_RUN,
  PRISM_CONTINUOUS_JOINT, COMPENSATOR_VERTICAL_STRIP.
- **Walls/courses**: TP1 W013–W016, W032/W033, W061–W064, W088–W091 (54–124 cm,
  todas as fiadas, 652 achados); TGD W003, W012, W079, W095, W137, W157, W158
  (151). Casos históricos W061 (79 cm, T+L) e W021/W092 (124 cm, L–X–L) confirmados.
- **Physical signature**: `[corpo do nó 0–14] [C09][C09][C09] [B34 do nó]`
  nas DUAS famílias (W061: A `[15-24 C09][25-34 C09][35-44 C09][45-79 B34]`,
  B `[0-34 B34][35-44 C09][45-54 C09][55-64 C09]`); prisma NÓ|FILL em
  34,5/44,5 em todos os pares de fiadas (16 por parede).
- **Human reference**: W061 A `[15-24 C09][25-64 B39]` (canto no vizinho),
  B `[0-34 B34][35-44 C09][45-79 B34]` — 1 compensador por fiada, não 3.
  W021 (124): A `[15-54 B39][70-109 B39]` (cantos nos vizinhos, X sem peça),
  B `[0-34 B34][35-54 B19][70-89 B19][90-124 B34]` — os DOIS cantos na mesma
  família. W013 (54): `[0-19 B19][20-54 B34]` / `[0-39 B39]` — sem peça de T.
- **First divergence**: estágio *node pieces* (t = 0). Três decisões do nó
  divergem: (a) papel/paridade — `_coordinate_arm_role_nodes` força papéis
  DIFERENTES nas duas pontas da parede curta; o humano CONCENTRA os dois
  B34 numa família (candidato `SAME_B` do SAFE REPAIR, rejeitado em TP1
  20/91 por `new_consecutive_compensators:13/88` — W013 já tem C09×4 na
  família B; o candidato só espelha a paridade, e o gate conta "novo");
  (b) `_corner_single_element_candidate` nunca oferece B19 (regra #2) — o
  humano fecha o trecho de 19–20 cm com B19; (c) `_wall_reserved_range_ft`
  reserva pior-caso 34 cm na outra ponta, degradando T/L para C09.
- **Root cause**: JUNCTION_ROLE_ERROR + DOMAIN_RULE_BLOCKED + RESERVATION_TOO_CONSERVATIVE.
- **Evidence**: composições `out/TP1_compositions_W061.txt`/`W021.txt`;
  reprodutor R1 (`run_reproducers.py`): boneca de 79 cm entre T e L produz
  exatamente `C09+C09+C09` nas duas famílias; censo T por comprimento da
  boneca (`first_divergence.py`): 16 de 20 T com boneca ≤130 cm degradados.
- **Minimal reproducer**: R1 (5 paredes, 1 T + 1 L, 0 aberturas).
- **Impact**: TP1 652 (18,6 % do nível 1), TGD 151 (directly explained);
  likely related: parte de C05.
- **Confidence**: 5 (mecanismo) / 3 (qual regra humana adotar).
- **Proposed future fix**: `CR-BLOCK-SHORT-WALL-NODE-POLICY` — decisão de
  regra (REQUIRES_HUMAN_DOMAIN_APPROVAL): concentração de papel em paredes
  curtas; B19 como fechamento encostado ao corpo do nó; reserva pior-caso
  substituída pela reserva REAL do nó já resolvido na outra ponta; gate do
  SAFE REPAIR insensível a espelho de paridade.
- **Files likely affected**: `wall_stepper.py` (`solve_l_corner`,
  `solve_t_intersection`, `_corner_single_element_candidate`,
  `_wall_reserved_range_ft`, `_coordinate_arm_role_nodes`, gates do SAFE
  REPAIR).
- **Risks**: regra #2 (meio-bloco) e alternância são regras OBRIGATÓRIAS
  vigentes — só com aprovação humana; alto raio de explosão.
- **Dependencies**: C04 (medir depois da tolerância — paredes vazias
  escondem defeitos); decisão de domínio; conflita em arquivo com C05/C07.

### C02 — X_ROOM_BORDERLINE_DEGRADED (X a 55 cm de um T)
- **Codes**: PRISM_CONTINUOUS_JOINT (96), COMPENSATOR_CONSECUTIVE (84),
  EXCESS (50), STRIP (6). TP1 W003/W008 (32 prismas cada), W021/W092 (16).
- **Signature**: X em t = 61,99 do W003; T em t = 7. `room_minus` = 61,99 −
  34 (reserva pior-caso) = **27,99 < 28,00** (27 + 1 de junta) → B54
  degradado para B34 nas duas paredes (`X_INTERSECTION_DEGRADED`) → na
  família A o trecho 15–44 (30 cm) vira `C09×3`; a junta 34,5 (C09|C09)
  coincide com a junta NÓ|FILL 34,5 da família B (`B34 T_INCOMING|fill`).
- **Human**: W003 A `[15-54 B39][55-94 B39]`, B `[0-34 B34][35-74 B39]` —
  **nenhuma peça de X**; a parede longa é contínua e a curta (W021) encosta
  nos dois lados (4 nós X em TP1 e 2 em TGD com esse padrão `B39/B39`).
- **First divergence**: *reserva de nós → node pieces* (o X existe para o
  solver, não para o humano); e comparação `+1e-6` num valor com 0,01 cm de
  ruído da conversão pés→cm.
- **Evidence**: `_x_intersection_wall_room_ft` chamado com os argumentos de
  produção (+517,0 / −28,0 → 27,99); ablação `x_room_slack` (0,05 cm):
  COMPENSATOR_CONSECUTIVE −32, EXCESS −16, **PRISM 0** — o prisma 34,5 é
  coincidência NÓ|NÓ (borda do B54 do X em 35 × borda do B34 do T em 34) e
  não desaparece com B54; reprodutor R2b (X em 61,99 degrada; em 62,00 não).
- **Impact**: TP1 236 (directly: 48 cadeias por folga numérica; 96 prismas
  só com política de nó/papel ou sem peça de X como o humano).
- **Confidence**: 5 (borderline) / 3 (regra humana "X de parede curta sem amarração").
- **Fix**: `CR-BLOCK-ROOM-CHECK-ROBUSTNESS` (folga ≥ 0,05 cm em todos os
  room checks) + decisão de domínio sobre amarração de X/T de paredes curtas.
- **Files**: `wall_stepper.py` (`_x_intersection_wall_room_ft`,
  `solve_x_intersection`, `_t_intersection_room_ok`, `_corner_wall_room_ft`).
- **Risks**: baixo (folga) / alto (política). **Dependencies**: nenhuma
  para a folga; C01 para a política.

### C03 — NODE_INSIDE_OPENING_SPAN (nó dentro do vão reconstruído)
- **Codes**: OPENING_BLOCK_CROSSES_JAMB (TP1 168, TGD 84),
  COMPENSATOR_CONSECUTIVE/EXCESS/STRIP (TP1 126+23+21: cadeias entre dois
  B54 dentro do vão, W003/W008 t 530–559 e 785–814), `door_void_violations`
  348 (sinal do próprio solver, não vira achado).
- **Signature**: porta reconstruída `[309,01–440]` (131 cm) em W004–W008
  contém dois nós T/X a **8 cm** de cada borda; `_room_at_t_on_wall` só
  considera aberturas que começam DEPOIS de `t` → um nó dentro do vão não
  vê obstáculo → B54 centrado (290–344) invade 35 cm.
- **Human**: fiada 0 `[290-324 B34] … [425-459 B34]` — o vão real é
  325–424 (100 cm); a reconstrução (`extract/reconstruct.py`) tomou a união
  dos vazios das fiadas em que o corpo do B34 perpendicular ocupa 310–324.
  No humano o T vira B34 até a jamba (T degrada para L, regra 18.9).
- **First divergence**: *entrada* (abertura inflada) → *node pieces*.
- **Evidence**: 19 aberturas TP1 (131/186 cm) contêm nós a 8 cm da borda;
  piso humano CROSSES_JAMB 209; reprodutor R4 (nó a 8 cm dentro de porta
  309–440 → B54 invade) vs R4b (porta real 325–425 → solver produz `B34
  [290-324]` **idêntico ao humano**).
- **Classification**: REFERENCE_LIMITATION (TP1) + robustez do solver
  (nó dentro de vão) + no TGD (aberturas medidas) 23 vãos com nó dentro —
  portas de 166 cm com dois T a 80 cm da borda: artefato de atribuição de
  abertura/eixo da Fase A (INPUT).
- **Impact**: TP1 338 + 348 violações; TGD 84. **Confidence**: 5.
- **Fix**: `CR-BENCH-OPENING-RECONSTRUCTION` (benchmark: vão = mínimo entre
  fiadas, excluindo corpos perpendiculares; regera `reference/input` de TP1
  com autorização) e, no solver, detectar nó dentro de vão no room check.
- **Files**: `benchmark/extract/reconstruct.py`; `wall_stepper.py`
  (`_room_at_t_on_wall`). **Risks**: mudança de referência/baseline (só com
  autorização explícita). **Dependencies**: fazer ANTES de qualquer CR de
  aberturas do solver (senão mede contra referência errada).

### C04 — FIT_TOLERANCE_NOISE (trecho recusado por 0,08 cm)
- **Codes**: COVERAGE_GAP_IN_ROW (TP1 152, TGD 209), ROW_MOSTLY_EMPTY (18),
  PARTIAL (6+6), MISSING_ROW/SOLID_BELOW_SILL (TGD).
- **Signature**: `_pier_remaining_snapped_cm` devolve `None` quando o resto
  do trecho desvia > `PIER_LAYOUT_TOLERANCE_CM = 0,05 cm` do módulo de
  5 cm; TP1 tem trechos de 19,08 / 39,08 / 323,92 / 343,92 cm (W012, W022,
  W093–W095…) → **família inteira do trecho fica vazia**. 41 dos 49 trechos
  únicos que falham em TP1 estão a ≤ 0,3 cm de um comprimento válido.
- **Human**: as mesmas paredes estão inteiramente moduladas (226 B39 + 134
  B34 nas fiadas 0–1 das paredes que falham).
- **First divergence**: *layout contínuo* (aritmética), sem candidato algum.
- **Evidence**: ablação `fit_tol_0_3` (0,05→0,30 cm, só em memória): TP1
  +1 155 peças, GAP −113, ROW_MOSTLY_EMPTY −18, PARTIAL −6; TGD +1 056
  peças, GAP −315, MISSING_ROW −66, PARTIAL −13. Efeito colateral: as
  paredes agora preenchidas trazem seus próprios defeitos (TP1 COMPENSATOR
  +37/+68, PRISM +34; TGD COMP +143/+98) — **defeitos que hoje estão
  escondidos por paredes vazias**. Reprodutor R3 (324,08 → nada; 324,00 →
  cheia).
- **Impact**: TP1 176 directly; TGD 215 (mais 275 de C04b onde o desvio é
  geométrico, 0,5–2,5 cm). **Confidence**: 5.
- **Fix**: `CR-BLOCK-FIT-TOLERANCE` — absorver resíduo sub-módulo nas
  juntas (decisão de regra: quanto uma junta absorve; 0,3 cm cobre o ruído
  de entrada de ambos os corpora), com snap do layout ao módulo.
- **Files**: `modulation_math.py` (`MODULATION_WHOLE_CM_TOLERANCE_CM`,
  `_pier_remaining_cm`), `wall_stepper.py` (`_pier_remaining_snapped_cm`).
- **Risks**: baixo; muda a baseline (mais peças ⇒ mais achados de outros
  tipos — registrar como trade-off, nunca esconder). **Dependencies**:
  nenhuma; recomendado PRIMEIRO (desmascara defeitos que as demais CRs
  precisam medir).

### C05 — DEGRADED_NODE_PIECE_RESIDUE (nó degradado + resíduo)
- **Codes**: COMPENSATOR_CONSECUTIVE (TP1 340, TGD 81), EXCESS (253/50),
  COVERAGE_GAP_IN_ROW (TP1 42, TGD 240, Piloto 16), PRISM (64).
- **Signature**: T incoming/L degradado para `C09`/`C04`
  (`T_INTERSECTION_INCOMING_DEGRADED`, `L_CORNER_DEGRADED`) porque room <
  34 cm (porta a 20 cm do nó, boneca curta, reserva pior-caso); os 10–20 cm
  restantes viram outro compensador (reparo ou fill) → `C09+C09`,
  `C09+C04+C04` — regra #2 violada por construção. 16 dos 20 T de TP1 com
  boneca ≤130 cm estão degradados.
- **Human**: 17 fiadas com `B19` exatamente onde o solver tem `C09
  (T_INC_DEGRADED)`; 11 com `C04`; bonecas de 54 cm sem peça de amarração
  (8/8 nós ≤70 cm: parede principal `B39|B39` contínua). Piso humano
  JUNCTION_HALF_BLOCK_ADJACENT 259.
- **First divergence**: *node pieces* (a escolha C09/C04 do
  `_corner_single_element_candidate`).
- **Evidence**: reprodutores R5 (L com 5 cm de folga: solver `C09` degradado
  + `C09+C09` vs humano `B19` cobrindo o quadrado do canto) e R6 (19 cm
  entre T e porta: `C09` + vazio/‘C09’ vs humano `B19`); cadeias
  `(WALL_END_T_INTERSECTION, OPENING)` 49 em TP1 com humano `B19` em 25.
- **Impact**: TP1 738, TGD 374, Piloto 16. **Confidence**: 5 (mecanismo)
  / 3 (regra). **Fix**: dentro de `CR-BLOCK-SHORT-WALL-NODE-POLICY` (B19
  como fechamento de nó degradado; ou nenhum elemento + fill contínuo).
- **Files**: `_corner_single_element_candidate`, `solve_t_intersection`,
  `_recut_openings_and_repair`. **Risks**: regra #2. **Dependencies**: C01.

### C06 — REPAIR_RESIDUE_NEAR_OPENING (resíduo do reparo local)
- **Codes**: COMPENSATOR_CONSECUTIVE/EXCESS (TP1 243/166, TGD 56/44,
  Piloto 36/28), STRIP.
- **Signature**: `_recut_openings_and_repair` recalcula só a região entre a
  peça mantida e a jamba; sobram 14/19/24/29 cm (37/52/26/25 cadeias em
  TP1) → `_pier_ordered_layout` com um lado fechado → `C09+C04`, `C09+C09`
  (a fusão 9+9→19 só vale se o par encosta numa ponta ABERTA; com a peça de
  nó degradada fora do layout não há fusão).
- **Human**: no mesmo intervalo `B39` 26, `B19` 25, `C04` 24, `B34_C`
  (bloco CORTADO) 10, `B19_C` 2 — o humano corta blocos junto ao vão
  (escopo de catálogo) ou muda o layout inteiro do trecho.
- **First divergence**: *local repair* (região fixada pelas peças mantidas).
- **Evidence**: traço `probe_opening_repair.py` (W036: região (54, 215) →
  sub-trecho 55–69 = 14 cm → `C09+C04`); censo de spans.
- **Impact**: TP1 410, TGD 101, Piloto 75. **Confidence**: 4.
- **Fix**: reparo com região expansível e com o custo de compensador no
  score (hoje `OPENING_REPAIR_MAX_EXTRA_BLOCKS=3` só expande por falha de
  fechamento, nunca por qualidade); catálogo de cortados é escopo separado.
- **Files**: `_recut_openings_and_repair`, `_solve_repair_subsegments`,
  `continuous_modulation.region_solid_subsegments`. **Risks**: médio
  (regressão de `OPENING_BLOCK_INSIDE_DOOR`, ver 30.6). **Dependencies**:
  C10 toca as mesmas funções — não em paralelo.

### C07 — FILL_RESIDUE_BETWEEN_TIES (resíduo do fill entre dois nós)
- **Codes**: COMPENSATOR_EXCESS_IN_RUN (TP1 385, TGD 106), CONSECUTIVE
  (290/90), STRIP (81/16).
- **Signature**: trecho entre duas reservas de nó com resíduo 24–30 cm; com
  `MAX_SPECIAL_BOND_PER_TRECHO = 1`, B19 proibido em ponta fechada e
  `MAX_COMPENSATORS_PER_TRECHO = 1`, `_pier_ordered_layout` cai no tier
  7/8 irrestrito (`C09+C09+C04`, `C09×3`); `_pier_full_search_layout` limita
  compensadores/peças especiais ao perfil já aceito, então nunca encontra
  `B34+B34`.
- **Human**: B34 como enchimento em fileiras de 2–8 (**899 pares B34|B34
  adjacentes em TP1, 866 em TGD**); primeira divergência mais frequente do
  TP1 nas fiadas 0/1: solver `B39` × humano `B34` como PRIMEIRA peça do
  trecho (38 fiadas) — o humano desloca o módulo 5 cm com B34 e fecha sem
  compensador (TP1: 4 164 compensadores no solver × 1 137 no humano; B34
  2 386 × 3 494).
- **First divergence**: *escolha de composição* (tiers/tetos).
- **Root cause**: DOMAIN_RULE_BLOCKED — seção 23.6 registra "B34/B54 como
  enchimento 2 460 → 0" como GANHO; o corpus humano faz o oposto. **CONFLITO
  registrado** (REGRAS seção 35), não resolvido aqui.
- **Impact**: TP1 756, TGD 214. **Confidence**: 5 (mecanismo) / 2 (regra).
- **Fix**: `CR-BLOCK-FILL-B34-MODULE` após decisão de domínio (permitir
  fileira de B34 como módulo de 35 cm na busca DP antes do fallback de
  compensador). **Files**: `_pier_ordered_layout`, `_pier_full_search_layout`,
  `_layout_piece_profile`, auditoria `REPEATED_VERTICAL_COMPENSATOR_STRIP`.
  **Risks**: alto (semântica de faixa vertical de peça especial).
  **Dependencies**: decisão humana; após C04.

### C08 — PHASEA_FRAGMENT_NONMODULAR (TGD: topologia de entrada)
- **Codes**: COVERAGE_GAP_IN_ROW 865, MISSING_ROW 238, COMPENSATOR 118+107,
  ROW_MOSTLY_EMPTY, PARTIAL, NOT_MODULATED (1 564 no total).
- **Signature**: o Wall Modeling entrega 73 fragmentos colineares (uma
  parede humana de 1 344 cm vira 324,26 + 594,00 + …; 14 paredes humanas
  cobertas por 2–5 eixos), 38 eixos sem parede humana (duplicatas a 12,7 cm
  — W038/W039/W121/W122 contra humanos W034/W035/W075/W076 — e tocos de
  4,4–40 cm) e "cantos L" falsos nas pontas dos fragmentos, com 17 braços
  que param na face PRÓXIMA (t = −5,7/−6,0) em vez de estender à face
  oposta. Os comprimentos dos fragmentos não são modulares (411 trechos
  únicos; distância ao válido distribuída uniformemente, só 25 % ≤ 0,5 cm)
  → **73 paredes com as 17 fiadas sem preenchimento**.
- **Human**: paredes longas contínuas com T reais (a fragmentação
  transforma T em dois L).
- **First divergence**: *grafo L/T/X* (antes do solver de blocos).
- **Evidence**: `wall_maps`/`human_overlaps`; censo de braços L não
  estendidos; comprimentos 324,26/269,01/537,26/1 174,01.
- **Impact**: TGD 1 564 directly; likely related C09/C13/C14/C15/C17/C21
  (≈ 2 300, 57 % do nível 1 do TGD). **Confidence**: 5 (mecanismo).
- **Fix**: linha própria de Wall Modeling (`CR-WALLMODEL-FRAGMENTS`):
  mesclar fragmentos colineares através de paredes perpendiculares,
  descartar eixos duplicados a ~1 espessura, estender braços de forma
  consistente. **Files**: `wall_pairing.py`, `geometry.py` (área "não reabrir
  sem evidência" — esta é a evidência). **Risks**: muito alto; corpus TGD
  único. **Dependencies**: nenhuma; não paralelizar com CRs que medem TGD.

### C09 — ROTATED_CORNER_SAME_WALL (canto girado, TGD 4/54)
- **Codes**: JUNCTION_NOT_ALTERNATING 272 (de 303), PRISM_CONTINUOUS_JOINT
  208, mais fills derrubados (219 peças em `dropped_fill_by_course`).
- **Signature**: 17 nós L com as DUAS peças de canto na mesma parede
  (`_corner_bond_blocked_by_other_node` → "girar o 34"): 11 bloqueados por
  OUTRO nó L a **7,0 cm** (eixo duplicado da Fase A: W038/W039/W121/W122/
  W124/W163/W161/W125), 6 por um T a 14–41 cm (tocos: W066 diagonal de
  39,6 cm, W147/W015 sem família A, W093, W085, W167). A parede REAL
  (W036=humano W005, W004/W005/W035) fica **sem peça de canto em nenhuma
  família**; o eixo espúrio ganha as duas.
- **Historic TGD 4 (W070)**: nó 8, bloqueado pelo T do toco W066 (40,8 cm)
  → as duas peças em W070. **TGD 54 (W039)**: nós 68/72, bloqueados pelos L
  de W033 (humano W035) a 7 cm — W039 é a duplicata a 12,7 cm de W033.
- **Human**: sem parede em y = −240/444 (não comparável).
- **Classification**: `canonical orientation bug` = NÃO; `role assignment` =
  NÃO; **geometria de entrada (duplicata/toco) + política de rotação que
  aceita perder a alternância** em vez de rejeitar o nó a 7 cm como erro de
  entrada.
- **Impact**: TGD 480 (+ 51 de C17). **Confidence**: 5.
- **Fix**: depois de C08; guarda no solver: bloqueador a < espessura+junta
  ⇒ suspeita de duplicata, reportar em vez de girar; canto girado nunca
  pode deixar a parede real sem peça.
- **Files**: `solve_l_corner`, `_corner_bond_blocked_by_other_node`.
  **Risks**: médio. **Dependencies**: C08.

### C10 — REPAIR_ANCHOR_RECREATES_NODE_JOINT (33.5, W036/W038)
- **Codes**: PRISM_CONTINUOUS_JOINT TP1 20 (W036/W038 6+6 nas bandas 1–3;
  W023, W042, W043, W085).
- **Signature (traço real, `probe_opening_repair.py`)**: família A, banda
  com janela ativa: layout contínuo `[15-34 B19][35-74 B39]…` — o filtro
  33.3 ignora a junta 34,5 porque `[35-74]` cruza a jamba (69) → o recorte
  derruba `[35-74]` → região de reparo `(34, 234)` com âncora esquerda =
  `B19` mantido → sub-trecho 35–69 (34 cm) → `_pier_ordered_layout` →
  `B34 [35-69]` → junta 34,5 renasce, em cima da junta NÓ|FILL 34,5 da
  família B (`B34 T_INCOMING [0-34]`). `avoid_joint_positions_cm` do reparo
  da A = `[]`.
- **Human**: W036 34,5 numa família / 49,5 na outra — CONFIRMED_BY_HUMAN.
- **First divergence**: *layout contínuo* (a troca por `_pier_layout_avoiding_
  joints` não acontece porque a junta é classificada como "de peça que o
  vão derruba") — o *local repair* só herda a fronteira.
- **Fix**: a junta entre peça MANTIDA e peça derrubada continua existindo
  como borda da região de reparo ⇒ deve contar como "sobrevivente" em
  `_layout_joints_surviving_openings_cm` (a Fiada A trocaria para
  `[15-54 B39][55-74 B19]`, como na banda 0), e/ou o reparo recebe
  `opposite_node_joints_cm` com expansão sobre a peça mantida.
- **Impact**: TP1 20 (+ 4 residuais de 54,5 em C12). **Confidence**: 5.
- **Files**: `_layout_joints_surviving_openings_cm`, `solve_wall_free_fill`,
  `_recut_openings_and_repair`. **Risks**: baixo. **Dependencies**: mesmas
  funções de C06 — sequenciar.

### C11–C21 e V01 (clusters menores)
- **C11 NODE_FILL_JOINT_RESIDUAL** (TGD 22): juntas NÓ|FILL restantes
  (W002 T 34,5, W069/W070/W113 T de meio) — mesma natureza da seção 33,
  sem composição alternativa no trecho (19–20 cm).
- **C12 FILL|FILL cross-band** (TP1 12, TGD 6): juntas `B39|B39` iguais nas
  duas famílias junto a vãos de bandas diferentes (27.7) — não investigado
  além da classificação.
- **C13 SEM_ESPACO** (TGD 24: tocos de 5–25 cm entre dois T; Piloto 8
  fiadas): reserva de nó > parede — INPUT (TGD) / a investigar (Piloto).
- **C14 INTERSECTION_FAILURE_NO_PIECE** (TGD 175 gaps; 200 nós sem
  solução: T 120, X 72, L 8): densidade de nós da entrada TGD (273 nós);
  o nó fica sem NENHUMA peça e a reserva vira vazio.
- **C15** (TGD 62): reserva de nó sem peça naquela família (T degradado
  só numa família, L com peça na vizinha e reserva de 7 cm desta).
- **C16 OPENING_REPAIR_FAILED** (TGD 102, TP1 25): `ABERTURA_NAO_
  COMPATIVEL` — pilarete entre dois vãos sem solução (só ajuste geométrico).
- **C17 FILL_DROPPED_BY_TIE_COLLISION** (TGD 51; 219 peças): fill colidindo
  com peça de nó da parede duplicada (consequência de C08/C09).
- **C18** (TGD 31): JUNCTION_NOT_ALTERNATING em W092/W130 (tocos de 14–15
  cm entre T) — INPUT.
- **C19 L_ARM_NOT_EXTENDED / C04_TOO_SHORT** (TGD 23: W050 9, W117 8, W133
  6; **TP1 9: W039/W041**): buraco FÍSICO no quadrado do canto numa
  paridade. TP1 nó 64: o eixo de W041 começa 8 cm DEPOIS do ponto do nó
  (também no humano reconstruído); o B34 de canto da família A, em W041,
  nasce em t=0 e não entra no quadrado; W039 termina em 269 antes da porta
  → fiadas pares sem peça no canto. O humano preenche o canto com `B19
  [365-384]` de W039 nas duas famílias. **REAL_SOLVER_DEFECT** com
  precondição de entrada (braço curto) — **não é** artefato P3. TGD W050/
  W117: braço para na face próxima; W133: `C04` degradado (4 cm) não
  alcança o eixo (7 cm) — `_corner_single_element_candidate` sem exigência
  de cobrir o quadrado do canto.
- **C20 NODE_PIECE_ROOM_CHECK_MISS** (TGD 29): peça de nó cruzando jamba
  sem nó dentro do vão (W131 `L_CORNER` dentro de porta a 6 cm do canto —
  `solve_l_corner` não checa a abertura da parede que recebe a largura).
- **C21 NODE_PIECES_COLLIDE** (TGD 29, TP1 18 W019): B54 de T principal
  contra peça de nó vizinho a < 54 cm (dois T a 5–20 cm no TGD = entrada;
  W019 TP1 não aprofundado).
- **V01 VALIDATOR_FOREIGN_PIECE_NOT_CREDITED** (TP1 76, TGD 5): o "vazio"
  está fisicamente ocupado pela peça de nó perpendicular da vizinha;
  `OccupancyIndex.foreign_coverage_on_axis` não credita — artefato de
  régua do benchmark (W011/W028/W094).

## Super root causes

- **S1 — Política de peça de nó em nós apertados** (C01 + C02 + C05 +
  parte de C06): TP1 1 626 achados (46 % do nível 1) + TGD 525. Uma única
  família de decisões (degradar para C09/C04, nunca B19; alternância
  forçada; reserva pior-caso 34 cm; amarrar todo X/T mesmo de parede
  curta) gera compensador consecutivo, excesso, faixa vertical, prisma
  NÓ|FILL e vazio de cobertura ao mesmo tempo.
- **S2 — Regras de composição do fill** (C07 + C06): TP1 1 166. `MAX_SPECIAL_
  BOND=1` + B19 só em ponta aberta + fallback irrestrito ⇒ cadeias onde o
  humano usa fileira de B34 ou bloco cortado.
- **S3 — Geometria de entrada/referência** (TGD: C08 + C09 + C13 + C14 +
  C15 + C17 + C21 ≈ 2 300 = 57 %; TP1: C03 338 + piso 209): fragmentos,
  duplicatas, tocos, braços não estendidos, vãos reconstruídos inflados.
- **S4 — Tolerâncias numéricas** (C04 + folga de C02): TP1 208, TGD 215,
  correções baratas e de alta confiança; C04 desmascara ~1 100 peças por
  projeto.

## Opening repair findings
Mecanismo 33.5 **confirmado por traço** (C10): a junta 34,5 renasce como
borda da região de reparo fixada pela peça mantida; a solução futura deve
ser "junta de âncora conta como sobrevivente" na Fiada A (preferencial —
resolve antes do recorte, sem tocar o reparo) e, complementarmente, reparo
consciente da junta de nó oposta. Os demais achados de abertura: CROSSES_
JAMB é 100 % peça de nó (TP1: nó dentro do vão inflado, C03; TGD: 84 nó
dentro do vão medido + 24 room check + 5 L dentro de porta), SOLID_BELOW_
SILL_MISSING (TGD 32) = família vazia por trecho não modular (C04/C08),
MISSING_LINTEL/COUNTER = catálogo. **Nenhum** achado foi atribuído a
origem vertical (BENCH-Z-ORIGIN) — as fiadas casam por elevação.

## Compensator-chain findings
151 cadeias únicas em TP1 (1 443 pares×fiadas), 53 em TGD. Padrões:
`C09+C09` 47, `C09+C04` 27, `C09+C09+C09` 25, `C09+C09+C04` 21, `C09×4` 8.
Spans 14/19/24/29/39 cm. Contextos: T na ponta → porta (49), fill → porta
(17), fill → nó (14), nó → nó (7), nó estrangeiro → nó (6). Causas: C05
(nó degradado) 37+17 cadeias, C06 (reparo) 31+10, C07 (fill) 43, C01/C02
(paredes curtas/X). Humano no mesmo intervalo: B39 26, B19 25, C04 24,
B34/B34_C 19, vazio 16 — **não é limitação física**: existe composição
humana válida em > 85 % dos casos; é regra/reserva do solver. B19 é a
resposta em ~1/3 dos casos (não presumido: medido), B34 em fileira em
outro terço.

## Rotated-corner findings
Ver C09. TGD 4 = T de toco diagonal a 40,8 cm; TGD 54 = duplicata de eixo
a 12,7 cm (11 dos 17 nós girados). Não é bug de canonicalização nem de
papel: a geometria de entrada é inválida e a rotação a aceita.

## Junction findings
JUNCTION_MISSING_BINDING: **REAL_SOLVER_DEFECT** (TP1 W039/W041 9; TGD
W050/W117 — braço não estendido; W133 — C04 curto): buraco físico no canto
numa paridade; precondição INPUT (braço curto) mas o solver não detecta.
JUNCTION_NOT_ALTERNATING 303 = C09 (272) + tocos (31). Humano × solver em
nós comparáveis (TP1): L 18 mesma paridade / 19 invertida; T 50 / 19 /
27 mesmas paredes em ordem trocada / 9 paredes diferentes; X 10 / 12 / 4 —
a paridade do solver coincide com a humana em ~50 %, e o humano usa
padrões que o solver não gera (B19 no canto em 8/38 L; B34 na principal do
T sem B54 em 23/≈100 T; B19 na boneca em 12+; sem amarração em 8 T de
boneca ≤ 70 cm e 4 X de parede curta).

## Coverage findings
TGD 2 419 achados de cobertura: 1 330 GAP + 249 MISSING_ROW + 106 MOSTLY_
EMPTY + 58 PARTIAL + 17 NOT_MODULATED por trecho NÃO modular (C08 + C04 +
C04b); 240 GAP por nó degradado curto (C05); 175 por nó sem solução (C14);
96 por reparo de abertura sem solução (C16); 62 reserva sem peça (C15); 51
fill derrubado (C17); 5 artefato de régua. TP1 351: 184 tolerância (C04),
76 artefato de validador (V01), 42 nó degradado (C05), 25 reparo (C16),
32 geometria (C04b). Vazio físico real: tudo exceto V01.

## Prism findings
320/256 achados = 33/34 assinaturas únicas; 314/236 são NÓ|FILL; 17/14
assinaturas repetem em 16 pares de fiadas (toda a altura). TGD: 224 junto a
L (208 girados, C09); TP1: T 76, X 64, L 64, T meio 32 → C02 96, C01 64,
C05 64, C10 20, C12 12. Humano no mesmo t: junta numa só família 194/103;
mesma junta corrida 10/2; sem junta 24/23.

## Benchmark/validator artifacts
- V01 (TP1 76 GAP): peça perpendicular da vizinha não creditada.
- C03 (TP1): aberturas reconstruídas infladas (+15 cm por lado adjacente a
  T) — afeta solver (entrada) e piso humano (209).
- TGD: casamento 1:1 (`comparator/match.py`) deixa fragmentos "sem humano";
  este atlas usou união colinear (`Bundle.human_overlaps`).
- `door_void_violations` (348) ≠ CROSSES_JAMB (168): o detector do solver
  conta por candidato agregado de banda — não verificado a fundo (unknown).

## Determinism
`run_determinism.py`: 3 projetos × `PYTHONHASHSEED` ∈ {0, 1, 12345,
random}, processos novos: fingerprint físico **idêntico** em todos
(TGD `09bc1b0c…`, TP1 `8d08d591…`, Piloto `e66bcd80…`). Nenhum finding HIGH
de não-determinismo.

## Ordering/mirror invariance
`run_invariance.py` (assinatura canônica por chave geométrica; classifica
`INVARIANT` / `PARITY_FLIP_ONLY` / `DIFFERENT_LAYOUT`):

| caso | permutação de ordem | inversão de pontas (todas / metade) | espelho | rotação 90° | translação |
|---|---|---|---|---|---|
| grade 2×2 (piloto) | 0/6 invariantes, DIFFERENT_LAYOUT | DIFFERENT / DIFFERENT | INVARIANT | INVARIANT | INVARIANT |
| R1 boneca 79 | 1/6, DIFFERENT_LAYOUT | DIFFERENT / INVARIANT | DIFFERENT | INVARIANT | INVARIANT |
| R2b X 61,99 | 1/6 | DIFFERENT / INVARIANT | INVARIANT | DIFFERENT | **DIFFERENT (126 peças)** |
| R5 2 paredes | PARITY_FLIP_ONLY | INVARIANT | INVARIANT | INVARIANT | INVARIANT |

Classificação: **ORDER_DEPENDENT** e **ENDPOINT_DEPENDENT** (a ordem dos
braços do grafo decide qual parede recebe a família A em L/X;
`_coordinate_arm_role_nodes` só garante alternância relativa) — coerente
com o problema aberto `CR-BLOCK-DETERMINISM`; e **sensível a 0,01 cm**
(R2b muda com translação por causa do borderline de C02).

## Performance
`run_performance.py` (wrappers em memória): TGD 46,8 s, dos quais
**`repair_arm_role_isolated_edges` 43,7 s** (23 rebuilds multi-banda
completos); sem ARM (`ARM_ROLE_SAFE_REPAIR_ENABLED=False`, ablação) 2,7 s e
PRISM +27. TP1 25,8 s (ARM 22,7 s, 9 rebuilds; sem ARM 2,9 s, PRISM +16).
Dentro de um rebuild: `solve_wall_free_fill` 19,4 s/30 728 chamadas,
`_pier_layout_avoiding_joints` 11,9 s/67 137, `_pier_ordered_layout`
10,2 s/284 759, `validate_same_course_collision` 9,4 s, `_pier_full_search_
layout` 2,8 s/8 111. Hotspot para CRs futuras: qualquer candidato ARM a
mais custa um rebuild inteiro (~2 s); a ablação de tolerância elevou TP1 a
46,9 s (mais paredes preenchidas ⇒ mais candidatos).

## Ranked next CRs

| # | CR | IMPACT | CONF | RISK | BLAST | COMPLEX | CORPUS | HUMAN |
|---|---|---|---|---|---|---|---|---|
| 1 | CR-BLOCK-FIT-TOLERANCE (C04) | 4 | 5 | 2 | 2 | LOW | BOTH | STRONG |
| 2 | CR-BENCH-OPENING-RECONSTRUCTION (C03 ref.) | 4 | 4 | 3 | 3 | MEDIUM | TP1 | STRONG |
| 3 | CR-BLOCK-ROOM-CHECK-ROBUSTNESS (C02 folga + nó dentro de vão + C20) | 3 | 4 | 2 | 3 | LOW-MED | BOTH | MEDIUM |
| 4 | CR-BLOCK-REPAIR-ANCHOR-JOINT (C10) | 2 | 5 | 2 | 2 | LOW | TP1 | STRONG |
| 5 | CR-BLOCK-SHORT-WALL-NODE-POLICY (C01+C05+C19, S1) | 5 | 4 | 4 | 4 | HIGH | BOTH | MEDIUM* |
| 6 | CR-BLOCK-FILL-B34-MODULE (C07+C06, S2) | 5 | 3 | 4 | 3 | MED-HIGH | BOTH | STRONG* |
| 7 | CR-BLOCK-ARM-SAFE-REPAIR-PERF (rebuild parcial) | 2 | 5 | 3 | 2 | MEDIUM | BOTH | n/a |
| 8 | CR-WALLMODEL-FRAGMENTS (C08/C09/C14/C17/C21) | 5 (TGD) | 4 | 5 | 5 | VERY_HIGH | TGD | WEAK |
| 9 | CR-BLOCK-CORNER-ROTATION-GUARD (C09 solver) | 3 | 4 | 3 | 3 | MEDIUM | TGD | WEAK |
| 10 | CR-BENCH-COVERAGE-FOREIGN-CREDIT (V01) | 1 | 5 | 1 | 1 | LOW | TP1 | n/a |

`*` = exige decisão de domínio (conflito com regra vigente).

## Recommended execution sequence

1. **#1 FIT-TOLERANCE** primeiro: barato, certo, e muda a baseline (mais
   peças ⇒ desmascara defeitos); todas as demais CRs devem ser medidas
   sobre a base pós-#1.
2. **#2 BENCH-OPENING-RECONSTRUCTION** em paralelo com #1 (arquivos
   disjuntos: benchmark × modulation_math) — sem ela, qualquer CR de
   abertura mede contra vão errado. Requer autorização para regravar
   `reference/input` de TP1.
3. **#3 ROOM-CHECK-ROBUSTNESS** (após #2, para medir CROSSES_JAMB real).
4. **#4 REPAIR-ANCHOR-JOINT** (independente; não paralelizar com #3 nem com
   #6 — mesmas funções de fill/reparo).
5. **Decisões de domínio** (seção 35 do REGRAS): B19 como fechamento de
   nó; concentração de papel em parede curta; X/T de boneca sem
   amarração; fileira de B34. Só então **#5** e depois **#6** (mesma
   seção de código; nunca em paralelo).
6. **#7 ARM-PERF** pode correr em paralelo com #3/#4 (seção SAFE REPAIR).
7. **#8/#9** linha própria de Wall Modeling (TGD), fora da fila do solver.

## What NOT to work on yet
- Regra do B19 / fileira de B34 / amarração de X-T curto **sem aprovação
  humana** (conflito com regras OBRIGATÓRIAS vigentes; seção 35).
- `CR-BLOCK-DETERMINISM` como CR de solver: a dependência de ordem nasce
  na ordem dos braços do grafo; definir a política de paridade (#5)
  antes de "canonizar".
- Tratar JUNCTION_MISSING_BINDING TP1 como artefato P3 — é buraco físico.
- Reabrir BENCH-Z-ORIGIN (nenhuma evidência nova).
- Achados de nível 2 e MISSING_LINTEL (catálogo).
- Otimizar performance dentro do fill antes de #7 (ARM domina 90 %).

## Unknowns
- Se a fileira de B34 e o B19 encostado ao nó são regra de escritório ou
  hábito de um projetista (N=1 planta).
- Se "X/T de parede curta sem amarração" é aceitável estruturalmente.
- TP1 W019 POSITION_OVERLAP 18 e Piloto SEM_ESPACO 8 — não aprofundados.
- TGD: portas medidas de 166 cm contendo dois T (W145/W146/W019/W020) —
  atribuição de abertura da Fase A ou geometria real?
- `door_void_violations` 348 × CROSSES_JAMB 168 (contagem por banda?).
- C12 cross-band (27.7) — 18 achados, não investigado.
- Impacto exato de #5/#6 não é demonstrável sem implementar (as ablações
  cobrem só C04/C02/ARM).
