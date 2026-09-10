# RELATÓRIO FINAL — ARM REJECTED EDGES DIAGNOSIS

`CR-BLOCK-ARM-REJECTED-EDGES-DIAGNOSIS` — investigação SOMENTE
(nenhum fix implementado, nenhum merge, nenhuma alteração de produção,
baseline, reference ou `REGRAS_MODULACAO_BLOCOS.md`; `wall_stepper.py`
e `wall_modeling.py` não tocados; NODE-FILL não aplicado nem
cherry-pickado).

## Base analisada

```
main oficial (PR #12 integrado)     4c89e1216cc6b5708c590f495e1584497e2df583
branch de referência do pedido      claude/arm-role-safety-contract-ljfwnj
HEAD da referência                  78c01aec72ce81e3e5a9d75f0e779e32ed6baa27
branch desta investigação           claude/cr-block-arm-rejected-edges-yqdred
                                    (HEAD == main, 4c89e12)
git diff 78c01ae..4c89e12 -- nuvem/core   VAZIO (produção idêntica)
```

Tudo foi medido na árvore de trabalho `4c89e12` (== `origin/main`). A
produção é byte-idêntica à da referência `78c01ae`, então o comportamento
analisado é o da `main` atual — nenhuma diferença relevante a explicar.

Instrumentação: scripts temporários no scratchpad da sessão (fora da
árvore versionada) que **reimplementam o laço de
`repair_arm_role_isolated_edges` chamando as MESMAS funções de produção**
(`_arm_role_isolated_edges`, `_set_l_corner_role_bits`,
`_evaluate_corner_role_candidate`, `_solve_building_blocks_all_courses_core`
como `rebuild_fn`), capturando por tentativa: composição antes/depois por
fiada física, resultado de cada gate isoladamente, e o DELTA de achados do
**validador real** do benchmark (`from_solver.project_from_solver` +
`validators.run_all`, identidade `(code, wall, detail)` — o mesmo delta
model do contrato). A reprodução bateu exatamente com a tabela do PR #12:
TGD 8 candidatos / 1 aceito (`wall_idx=23`, `SAME_A`) / 7 rejeitados; TP1
3 / 0 / 3; mesmos motivos por candidato.

Convenções: `wall_idx` é o índice em `walls_to_create` desta resolução
(diagnóstico, instável entre execuções); `W###` é o id do projeto do
benchmark (do solver); "humano W###" é o id no `reference.json`, casado
por `comparator.match.match_walls` (geometria, nunca id). Bandas: TGD 8
(`[0-4] [5] [6] [7] [8-10] [11] [12] [13-16]`), TP1 7
(`[0-4] [5-6] [7] [8-10] [11] [12] [13-16]`), 17 fiadas em ambos.

## TGD

Todas as 8 arestas são paredes com `L_CORNER` de 2 braços nas DUAS pontas
(é a definição de aresta isolada). Bits originais: `(0,1)`/`(1,0)` =
alternância normal (canto de uma ponta na família A, da outra na B).

### rejeição 1 — `wall_idx=90` (W157 · humano W093), 124 cm

- nós: p `(-1126.5, 712.0)` L com `133` (W153, 68,05 cm; humano W089 54 cm);
  q `(-1016.5, 712.0)` L com `134` (W154, 68,05 cm; humano W090). Nó X no
  meio da parede (t≈62) — peça `B54 X_INTERSECTION` na família B.
- antes (A = fiadas pares / B = ímpares):
  `A: B34 L[0-34] B19[35-54] ▯[54-70] B39[70-109]` (92 cm),
  `B: B19[15-34] B54 X[35-89] B34 L[90-124]` (107 cm). Prisma forçado em
  **34,5** (junta nó|fill em A, fill|nó em B), 17/17 fiadas.
- `SAME_A` → não resolve (prisma vira `[34.5, 89.5]`); `ALTERNATE_BA` →
  não resolve (`[89.5]`).
- `SAME_B` → **resolve o alvo** (`A: B39[15-54] B39[70-109]`,
  `B: B34 L[0-34] B54 X[35-89] B34 L[90-124]`, zero junta comum) e é
  rejeitado por `row_coverage_regression:90`: fiadas pares 92→78 cm
  (−15,2 % > 10 %); a vizinha 133 também cai 68→34 nas ímpares.
- validador real (`SAME_B`): NOVOS `W153 COVERAGE_GAP_IN_ROW ×17` +
  `COVERAGE_PARTIAL_WALL ×1`; RESOLVIDOS `W153 COVERAGE_MISSING_ROW ×8` +
  `ROW_MOSTLY_EMPTY ×9`, `W157 PRISM_CONTINUOUS_JOINT ×16` +
  `PRISM_JOINT_STACK ×1`. **Nenhum achado novo na própria W157.**
- parede afetada: a própria (só melhora); vizinhas: W153 (troca "família A
  100 % vazia" por "todas as fiadas com um vazio de 19 cm").

### rejeição 2 — `wall_idx=89` (W158 · humano W094), 124 cm

Espelho geométrico de 90 do outro lado da planta: nós `(1208.5, 712.0)` L
com `132` (W155) e `(1318.5, 712.0)` L com `131` (W156). Números idênticos
aos da rejeição 1 (92→78 no alvo, 68→34 na W155; validador: NOVOS W155
GAP×17 + PARTIAL×1, RESOLVIDOS W155 MISSING×8 + MOSTLY_EMPTY×9 + prisma).
Também aparecem `W011 COMPENSATOR_EXCESS_IN_RUN ×5` novo/×5 resolvido —
é o efeito da aresta 23 já ACEITA (pinada antes de 89 na ordem canônica),
não desta aresta.

### rejeição 3 — `wall_idx=92` (W012 · humano W021), 124 cm

- nós: p `(-1016.5, -508.0)` L com `130` (W003, 69 cm; humano W014 54 cm);
  q `(-1126.5, -508.0)` L com `129` (W001, 69 cm; humano W013). Bits `(1,0)`.
- antes: `A: B39[15-54] B19[70-89] B34 L[90-124]`,
  `B: B34 L[0-34] B54 X[35-89] B19[90-109]`. Prisma em **89,5**.
- `SAME_A` → não resolve `[34.5, 89.5]`; `ALTERNATE_AB` → não resolve `[34.5]`.
- `SAME_B` → resolve o alvo, rejeitado por `new_forced_prism_in_neighbor`:
  a vizinha 129 (69 cm, T numa ponta e este L na outra) passa a
  `A: B19[15-34] B34 L[35-69]` / `B: B34 T[0-34] B19[35-54]` → junta 34,5
  nas duas famílias.
- validador: NOVOS `W001 PRISM ×16+1`; RESOLVIDOS `W012 PRISM ×16+1` —
  relocação pura do prisma para a vizinha (R4 genuíno).

### rejeição 4 — `wall_idx=91` (W013 · humano W022), 124 cm

- nós: p `(1318.5, -508.0)` L com `135` (W010, 55 cm; humano W019 54 cm);
  q `(1208.5, -508.0)` L com `128` (W009, 55 cm; humano W018). Bits `(1,0)`.
- antes: igual à rejeição 3 (`A: B39 B19 B34L`, `B: B34L B54X B19`),
  prisma **89,5**. Vizinhas: `128 A: B39[1-40]` /
  `128 B: C09[1-10] B34[11-45] C09 L_DEG[46-55]`; `135` é o espelho (já
  reprovada no baseline: `alignment_conflicts` família B `[0-40]`).
- `SAME_A`/`ALTERNATE_AB` → não resolvem.
- `SAME_B` → resolve o alvo, rejeitado por `closure_regression`: a parede
  **128, que fechava em todas as 8 bandas, passa a reprovar** com
  "1 trecho com junta vertical coincidindo entre Fiada A e Fiada B (regra
  #1)": `A: B39[1-40] C04[41-45] C09 L_DEG[46-55]` / `B: B39[1-40]` →
  junta 40,5 nas duas. Validador: NOVOS `W009 COMPENSATOR_CONSECUTIVE ×9`
  (C04|C09 em 41/46, fiadas pares), `EXCESS_IN_RUN ×9`, `VERTICAL_STRIP ×2`;
  RESOLVIDOS `W013 PRISM ×16+1`, `W009 EXCESS ×8` (ímpares).
- parede afetada: 128 vira exatamente o defeito que 135 já tem no baseline.

### rejeição 5 — `wall_idx=120` (W137 · humano W077), 69 cm

- nós: p `(-1.5, 525.0)` L com `37` (W136, 355,3 cm; humano W083);
  q `(-1.5, 470.0)` L com `88` (W131, 146 cm com porta; humano W078 159 cm).
  Bits `(0,1)`.
- antes: `A: B34 L[0-34] B19[35-54]` (53 cm) / `B: B19[15-34] B34 L[35-69]`
  (53 cm). Prisma **34,5**.
- `SAME_A` → resolve (`A: B34L B34L`, `B: B39[15-54]`), rejeitado por
  `new_consecutive_compensators:88` — REAL: fiadas 11/13/15 ganham
  `C09 C09 C09` em t=82 na W131; e a família A da W131 cai 38→4 cm (perde
  o canto `B34[112-146]` para a 120 e o reparo de jamb deixa `[107-131]`
  vazio). Validador: NOVOS `W131 CONSECUTIVE ×6, EXCESS ×3, GAP ×9,
  MOSTLY_EMPTY ×9`; RESOLVIDOS `W131 CONSECUTIVE ×10, EXCESS ×8, GAP ×9,
  MOSTLY_EMPTY ×3`, `W137 PRISM ×16+1`.
- `SAME_B` → resolve (`A: B39[15-54]`, `B: B34L B34L`), rejeitado por
  `row_coverage_regression:37` (ímpares 68→34; pares sobem 108→142).
  Validador: `W136 COVERAGE_GAP_IN_ROW ×17` NOVO **e** ×17 RESOLVIDO
  (espelho de paridade: o vazio de 117 cm nas pares vira 137 cm nas
  ímpares), `PARTIAL_WALL` 32 %→38 % (melhora), `W011 EXCESS ×5`↔×5
  (aresta 23), `W137 PRISM ×16+1` resolvido. **Nenhuma contagem por
  parede/código sobe.**
- `ALTERNATE_BA` → não resolve.

### rejeição 6 — `wall_idx=4` (W070), 1174 cm — SEM PAR humano

- nós: p `(103.5, 17.0)` L com `20` (584 cm; lado da 20 degradado para
  `C09 L_CORNER_DEGRADED`); q `(1263.5, 17.0)` L com `17` (594 cm).
- prisma em **1139,5** = borda do `B34 L_CORNER[1140-1174]` que a parede 4
  recebe **nas DUAS famílias** no nó q (a 17 não recebe peça de canto em
  nenhuma família).
- `SAME_A` (só inverte o nó q) **não muda NADA** (`changed_courses={}`);
  `SAME_B`/`ALTERNATE_BA` mexem no nó p (canto degradado) e não resolvem.
- causa: `solve_l_corner` → `_corner_bond_blocked_by_other_node` é `True`
  para a 17 no nó q (há um `T_INTERSECTION` — nó 238, parede 153 de
  39,6 cm — a 33,8 cm do canto, dentro do alcance de perigo
  34+27 = 61 cm) → regra "GIRAR o bloco de 34 do canto": **as duas fiadas
  vão para a parede não bloqueada (4)** e "este canto específico perde a
  alternância" (docstring). O bit de papel não participa da decisão.

### rejeição 7 — `wall_idx=54` (W039), 269 cm — SEM PAR humano

- nós: p `(593.5, -240.0)` L com `42` (324,3 cm); q `(848.5, -240.0)` L com
  `44` (324,3 cm). Prisma em **34,5 e 234,5** (bordas dos dois `B34
  L_CORNER` que a 54 recebe nas DUAS famílias, nas DUAS pontas).
- os 3 candidatos **não mudam nada** (`changed_courses={}` nos três).
- causa: os dois nós são "girados": 42 e 44 estão `blocked` por outro
  encontro a **−7,0 cm** — os nós 93/94 (`L_CORNER` de 1 braço da parede
  **59**, uma parede paralela à 54, de 269 cm, a 12,7 cm dela, chegando
  nas mesmas 42/44). Parede dupla na entrada (54 ∥ 59). Além disso 42/44
  têm a família A **totalmente vazia** no baseline (`non_modular`).

## TP1

### rejeição 1 — `wall_idx=20` (W021 · humano W021), 124 cm

- nós: p `(6552.3, 594.9)` L com `12` (W013, 54 cm); q `(6662.3, 594.9)` L
  com `13` (W014, 54 cm). Nó X no meio **degradado** (`B34
  X_INTERSECTION_DEGRADED[45-79]` na família B). Bits `(1,0)`.
- antes: `A: B39[15-54] B19[70-89] B34 L[90-124]`,
  `B: B34 L[0-34] C09[35-44] B34 X_DEG[45-79] C09[80-89] C09[90-99]
  C09[100-109]`. Prisma **89,5** (nó|fill em A, `C09|C09` em B).
- `SAME_A`/`ALTERNATE_AB` → não resolvem.
- `SAME_B` → resolve (`A: B39 B39`; `B: B34L C09 B34X_DEG C09 B34L`),
  rejeitado por `new_consecutive_compensators:13`: o run físico
  `C09×4` da W014 muda de paridade (pares ×9 → ímpares ×8). Validador:
  NOVOS `W014 CONSECUTIVE ×24, EXCESS ×17, STRIP ×1`, `W021 EXCESS ×8`;
  RESOLVIDOS `W014 CONSECUTIVE ×27, EXCESS ×17, STRIP ×3`, `W021
  CONSECUTIVE ×16, EXCESS ×8, PRISM ×16+1, STAGGER ×8`. **Nenhuma contagem
  por parede/código sobe; o alvo passa de 4 para 2 compensadores.**

### rejeição 2 — `wall_idx=91` (W092 · humano W092), 124 cm

Idêntica à rejeição 1 em tudo (vizinhas `87`/W088 e `88`/W089, 54 cm;
mesmas composições, mesmos deltas, `new_consecutive_compensators:88`).

### rejeição 3 — `wall_idx=75` (W076 · humano W076), 69 cm

- nós: p `(7677.2, 1575.0)` L com `76` (W077, 159 cm com porta); q
  `(7677.2, 1630.0)` L com `81` (W082, 354 cm). Bits `(0,1)`.
- antes: `A: B34 L[0-34] B19[35-54]` / `B: B19[15-34] B34 L[35-69]`,
  prisma **34,5**.
- `SAME_A` → resolve (`A: B34L B34L`, `B: B39[15-54]`), rejeitado por
  `new_consecutive_compensators:81`. **Falso positivo PROVADO** (ver
  Grupo A1): o gate compara `result["candidates"]` — o AGREGADO das 7
  bandas — e `_find_consecutive_compensators` agrupa por `c["course"]` =
  letra da banda, então **7 cópias do MESMO `C04` solitário (uma por
  banda, mesmo X) encadeiam como "7 compensadores consecutivos"**. Medido:
  por fiada física, a W082 tem 9 runs reais antes (`C09 C09 C04` em 315)
  e **ZERO depois**; o agregado mostra runs novos `('A', C04×7, 335.0)`,
  `('B', C04×7, 315.0)`. Validador real: **0 achados novos, 102
  resolvidos** (`W082 CONSECUTIVE ×18, EXCESS ×17, STRIP ×2, STAGGER ×48`,
  `W076 PRISM ×16+1`). Se o fantasma não existisse, o gate seguinte
  também rejeitaria: `row_coverage_regression:75` (ímpares 53→39, −26 %) —
  sendo que **39 cm é exatamente a fiada ímpar do humano** (`B39[15-54]`).
- `SAME_B` → resolve, rejeitado por `new_consecutive_compensators:76` —
  REAL (fiadas 12/14/16 ganham `C09 C09 C09` em t=95 na W077; validador
  NOVOS `W077 CONSECUTIVE ×6, EXCESS ×3, STRIP ×1, STAGGER ×7`).
- `ALTERNATE_BA` → não resolve.

## Classificação R1–R8

| caso | candidato decisivo | gate | classe | sintoma × causa |
|---|---|---|---|---|
| TGD 90 | SAME_B | coverage (alvo) | **R2** | proxy local perde o quadrado de canto (14 cm/92 = 15 %); validador: alvo limpo, vizinha 68 cm troca MISSING→GAP |
| TGD 89 | SAME_B | coverage (alvo) | **R2** | idem |
| TGD 92 | SAME_B | prisma em vizinha | **R4** | 129 (69 cm, T+L com B34 nos dois nós) fica com 34,5 nas duas famílias |
| TGD 91 | SAME_B | closure | **R5** (+R3) | 128 (55 cm) recebe canto degradado `C09` + fill `B39+C04` → junta 40,5 coincide com `B39` da outra família |
| TGD 120 | SAME_A / SAME_B | compensador (88) / coverage (37) | **R7** | SAME_A: R6 real (jamb da 88); SAME_B: R2 espelho de paridade numa parede já quebrada |
| TGD 4 | nenhum resolve | — | **R8** | canto GIRADO no nó q (T a 33,8 cm na 17): bit de papel é ignorado |
| TGD 54 | nenhum resolve | — | **R8** | dois cantos GIRADOS (parede dupla 54 ∥ 59 a 12,7 cm) |
| TP1 20 | SAME_B | compensador (13) | **R3** | espelho de paridade do `C09×4` da vizinha de 54 cm; alvo melhora |
| TP1 91 | SAME_B | compensador (88) | **R3** | idem |
| TP1 75 | SAME_A | compensador (81) | **R3** | **fantasma** do agregado de bandas; validador: 0 novos / 102 resolvidos |

## Primeira divergência por caso

Cadeia causal (a PRIMEIRA decisão de layout → consequência → gate):

- **TGD 90/89 (124 cm L–X–L)**: `_coordinate_arm_role_nodes` deixa o canto
  p na família A e o canto q na família B (ALTERNATE) → em A o `B34 L[0-34]`
  força fill `B19[35-54]` (trecho de 19 cm até a peça X); em B o `B54 X[35-89]`
  força fill `B19[15-34]` → junta 34,5 nas duas → prisma. `SAME_B` corrige
  (é o layout humano). Gate rejeita porque `_wall_row_covered_length_cm`
  mede só as peças DA PRÓPRIA parede: ao entregar o canto para a vizinha, a
  família A perde 14 cm que continuam fisicamente cobertos pelo `B34` da
  vizinha (o validador real credita via `OccupancyIndex`; o proxy não).
  Numa parede de 124 cm isso é 15 % > `ROW_COVERAGE_RELATIVE_TOLERANCE`
  (10 %) — o mesmo mecanismo que o docstring chama de "redistribuição
  balanceada e inofensiva" na parede de 555 cm (2,5 %).
- **TGD 92**: mesma cadeia no alvo; na vizinha 129 (69 cm) o T recebe `B34`
  (não `B54`: `room` = 69−34 = 35 < 54 → degradado) e o L recebe `B34` →
  sobram dois trechos de 19 cm (`[15-34]` e `[35-54]`) → só `B19` cabe →
  34,5 nas duas famílias → `_no_new_forced_corner_prism_in_neighbors`.
- **TGD 91**: na vizinha 128 (55 cm) `_corner_wall_room_ft` = 55 − 34
  (reserva PIOR CASO da outra ponta, `_wall_reserved_range_ft`) = 21 < 34 →
  `L_CORNER_DEGRADED` = `C09` (nunca `B19`, `CORNER_SINGLE_ELEMENT_CODES`).
  Com `SAME_B` esse `C09` migra para a família A; o fill do trecho
  `[1-45]` (44 cm) sai `B39+C04` (guloso maior-primeiro, compensador por
  ÚLTIMO → encostado no `C09` do nó = `COMPENSATOR_CONSECUTIVE`, e junta
  40,5 = junta do `B39[1-40]` da família B → regra #1 → `closure_regression`).
  Alternativas que fecham os mesmos 44/39 cm sem coincidência:
  `C04[1-5]+B39[6-45]` (compensador primeiro), `B34+C04`, `B19+B19`.
- **TGD 120 (69 cm L–L)**: canto p em A, canto q em B → dois trechos de
  19 cm → `B19` dos dois lados → 34,5. `SAME_A` = humano. Regressão real
  está na 88: o trecho contínuo `[15-111]` = 96 cm é **não-modular por
  aritmética** (`lower_valid 94 / upper_valid 99`) → família A vazia
  desde o baseline; ao perder o canto `[112-146]`, o reparo de jamb não
  preenche `[107-131]` (24 cm = `C04+B19`, que o humano usa).
- **TGD 4 e 54**: `_corner_bond_blocked_by_other_node` → canto girado →
  as duas fiadas com `B34` na mesma parede → junta nó|fill igual nas duas
  famílias em qualquer fill. Anterior a ARM-ROLE e imune a ele.
- **TP1 20/91**: como TGD 90, com o X degradado para `B34[45-79]` → em B
  sobram `[35-44]` (9 cm → `C09`) e `[80-109]` (29 cm → `C09×3`, 3
  compensadores; `B19+C09` fecharia sem coincidência). Vizinhas de 54 cm:
  `room` = 54−34 = 20 → T degradado (`C09`) E L degradado (`C09`) nas duas
  pontas → `C09 B34 C09` / `C09×4` (fills de último recurso com
  `alignment_conflicts`). `SAME_B` corrige o alvo (= humano) e só espelha
  a paridade do defeito pré-existente da vizinha.
- **TP1 75**: como TGD 120; `SAME_A` = humano; rejeição = fantasma do
  agregado (A1) e, em seguida, proxy de cobertura local (A2).

## Solver × Humano

Casamento geométrico (`match_walls`; TGD: 84 pares de 167 paredes do
solver × 97 do humano — 4, 54 e 19 sem par; TP1: 96/96).

**Paredes de 124 cm (TGD 90/89/92/91 = humano W093/W094/W021/W022; TP1
20/91 = W021/W092) — o humano usa, nas 6, a MESMA composição:**

```
fiada par   : B39[15-54]              B39[70-109]
fiada ímpar : B34[0-34] B19[35-54]    B19[70-89] B34[90-124]
```

= **os dois B34 de canto na MESMA família** (o candidato `SAME_B` do
solver), `B39 B39` na outra (78 cm — o valor que o gate de cobertura
rejeitou como regressão), e **nenhuma peça X/T sobre a parede de 124 cm**
(`B19 B19` em volta do cruzamento; o solver põe `B54 X` ou `B34 X_DEG`).
Achados do humano nessas 6 paredes: só `COVERAGE_MISSING_ROW ×1` (fiada
17 ausente no gabarito) — zero prisma, zero compensador.

**Paredes de 69 cm (TGD 120 = W077; TP1 75 = W076):**

```
fiada par   : B34[0-34] B34[35-69]
fiada ímpar : B39[15-54]
```

= **`SAME_A`**, exatamente. Humano: `PRISM_CONTINUOUS_JOINT ×1` (borda de
altura) + `JUNCTION_MISSING_BINDING ×5`.

**Vizinhas curtas (54/55/68/69 cm) — onde solver e humano de fato
divergem:**

| parede | solver (baseline) | humano |
|---|---|---|
| TGD 133/134/132/131 (68,05 cm; humano 54 cm) | `A: ∅` / `B: B34L B34T` ou `A: B34L` / `B: B34T` | `A: B34[0-34] B19[35-54]` / `B: B39[15-54]` |
| TGD 129/130 (69 cm; humano 54) | `A: B19 B34L` / `B: B34T B19` | `A: B19[0-19] B34[20-54]` / `B: B39[0-39]` |
| TGD 128/135 (55 cm; humano 54) | `A: B39[1-40]` / `B: C09 B34 C09_L_DEG` | `A: B19[0-19] B34[20-54]` / `B: B39[0-39]` |
| TP1 12/13/87/88 (54 cm) | `C09_T_DEG B34 C09_L_DEG` / `C09_T_DEG C09 C09 C09` | `B19[0-19] B34[20-54]` / `B39[0-39]` |
| TGD 88 / TP1 76 (jamb de porta) | `C09 C04 C09` / `C09 C09 … C04` | `C04 B19` / `C04 B34` |

Padrão humano nas paredes curtas: **`B34` inteiro no L** (nunca
degradado), **nenhuma peça de amarração T/X sobre a parede curta que
chega** (o `B19`/`B39` simplesmente encosta — `JUNCTION_HALF_BLOCK_ADJACENT
×6` em cada uma), **zero compensador**. O solver: canto degradado para
`C09` (reserva pior-caso de 34 cm na outra ponta), peça T degradada `C09`
nas duas famílias, trecho de 38,1 cm não-modular → família vazia,
fills de último recurso `C09×3/×4`.

Resposta à pergunta principal (**o humano tem um fill que mantém a
melhoria ARM sem a regressão?**): **SIM, em 8 dos 10 casos** — e é
literalmente o candidato de papel que o solver já gera (`SAME_B` nas seis
de 124 cm, `SAME_A` nas duas de 69 cm), combinado com um fill de vizinha
(`B19+B34`/`B39`) que o solver hoje NÃO gera. Nos 2 restantes (TGD 4, 54)
não há gabarito humano.

## Fill search

### solução existe?

- Para os 8 alvos com par humano: **existe** — é um candidato de PAPEL
  (`SAME_B`/`SAME_A`), não um fill diferente. Com as peças de nó fixas
  (`B34` em cada ponta, `B54`/`B34 X` no meio) e a alternância original,
  os trechos de 19 cm só admitem `B19` → a junta 34,5 é forçada nas duas
  famílias — **não existe fill que resolva o prisma sem mudar o papel**
  (`solve_l_corner` só gera `B34`; um `B54` de canto nunca é gerado e o
  humano também não usa).
- Para as vizinhas: existe no catálogo (`B19+B34` = 54; `B34+C04` = 39;
  `C04`-primeiro; `B19+B19`).
- TGD 4/54: **não existe** fill enquanto o canto girado põe o mesmo `B34`
  nas duas famílias (D).

### é gerada?

- `SAME_B`/`SAME_A`: sim, geradas, resolvem o alvo (`resolved_target=True`
  medido) — a busca de papel funciona.
- Vizinha 68,05 cm, família sem canto: trecho `[15.0, 53.1]` = 38,1 cm;
  `_pier_remaining_snapped_cm` exige múltiplo de 5 dentro de
  `PIER_LAYOUT_TOLERANCE_CM` → 38,1 está a 1,9 de 40 e 3,1 de 35 → `None`
  → `non_modular` → **família inteira vazia** (C: nunca gerada). O humano
  fecha o mesmo vão com `B39` até a face (39 cm, sem a junta de 1 cm que a
  reserva `_wall_end_default_start_cm` soma).
- Vizinhas 54/55 cm: `B19+B34` **não é gerada** por duas regras explícitas
  — reserva pior-caso `CORNER_B34_ROOM_FT` na outra ponta
  (`_wall_reserved_range_ft`) degrada o canto, e
  `_corner_single_element_candidate` "NUNCA B19". (C, por regra.)
- `C04`-primeiro em 44 cm (128): não gerada pelo guloso maior-primeiro
  (`_pier_ordered_layout` põe o compensador por último); `B34+C04` deveria
  vir de `_pier_forced_bypass_layouts` ("B34 primeiro") — o resultado
  medido em 135 (baseline) e 128 (`SAME_B`) mantém a coincidência e
  reporta `alignment_conflicts`, logo a busca de desencontro falhou ali
  (**INCONCLUSIVO** o passo exato em que falha).

### é podada?

- Nas paredes curtas o poda-antes é a **reserva pior-caso de 34 cm da
  outra ponta** (`_wall_reserved_range_ft`, docstring: "superestimar aqui
  só custa uma degradação a mais") — em 54/55 cm ela custa o canto inteiro
  (`room` 20–21 cm) e o T (`room` 20 cm). PROVADO por medição
  (`_corner_wall_room_ft` = 21,0 / 20,0 / 34,1 / 35,0 nas vizinhas).
- No contrato SAFE REPAIR, o candidato certo é podado pelos gates
  (Grupo A), não pelo solver.

### perde no score?

- Nenhum dos 10 casos é "solução segura perde no desempate do fill". O
  único desempate relevante é a ORDEM do compensador dentro do trecho
  (128/135, TP1 `[80-109]`), onde o guloso não pontua adjacência a peça de
  nó nem coincidência com a outra família antes de escolher.

## Grupos de causa-raiz

**Grupo A — proxy do contrato diverge do validador real (rejeição por
artefato de medição, não por regressão física).**
- A1 `_no_new_consecutive_compensators` sobre o AGREGADO multi-banda
  (`result["candidates"]`, `course`=letra da banda): runs fantasma de
  N cópias do mesmo compensador solitário (N = nº de bandas). TP1 75/SAME_A
  — **PROVADO** (0 novos / 102 resolvidos no validador).
- A2 `_wall_row_covered_length_cm` LOCAL (sem cobertura emprestada): toda
  troca de papel move 14–15 cm de quadrado de canto entre paredes;
  em paredes de 69/124 cm isso é 11–26 % > 10 %. TGD 89/90 (motivo
  declarado do gate), TGD 120/SAME_B (37), TP1 75 (2º gate) —
  **PROVADO** que o motivo é local (humano: 78 cm e 39 cm nessas fiadas).
- A3 identidade por fiada conta ESPELHO DE PARIDADE como achado novo:
  TGD 120/SAME_B (W136 GAP 17↔17), TP1 20/91 (W014/W089 CONSECUTIVE
  27→24) — mesmo artefato já classificado P3 no PRE-INTEGRATION AUDIT
  (`JUNCTION_MISSING_BINDING` 8→9). **PROVÁVEL** benigno; é decisão de
  política do contrato ("NEW_FINDINGS nunca aceitos").

**Grupo B — peças de nó e fill em paredes curtas (54–69 cm).** Reserva
pior-caso degrada L→`C09` e T→`C09`/`B34`; trecho 38,1 cm não-modular →
família vazia; trechos de 19 cm → `B19` forçado; fills de último recurso
`C09×3/×4`; compensador por último encostado no `C09` do nó. É a origem de
TODAS as regressões reais em vizinhas (TGD 91→128, 92→129, 89/90→131-134,
TP1 20/91→12/13/87/88) e do estado já ruim dessas paredes no baseline.
Humano: `B19+B34` / `B39`, sem peça T na parede curta. **PROVADO** o
mecanismo; **CONFLITO** com regra vigente (ver abaixo).

**Grupo C — canto girado / geometria de entrada.** TGD 4 (T a 33,8 cm na
17) e 54 (parede dupla 54 ∥ 59). ARM não tem alavanca; sem par humano.
**PROVADO** o mecanismo, **INCONCLUSIVO** o fix (girar para o outro lado?
manter alternância com peça degradada? corrigir a entrada 54/59?).

**Grupo D — abertura/jamb em vizinha.** TGD 120/SAME_A → 88 (trecho
96 cm não-modular pré-existente + jamb `[107-131]` não preenchido);
TP1 75/SAME_B → 76 (`C09 C09` em 19 cm + `C09×3` acima da porta).
**PROVÁVEL** independente de ARM.

Distribuição: A = 5 candidatos decisivos (TP1 75/SAME_A; TGD 89, 90;
TGD 120/SAME_B; TP1 20, 91 — 6 arestas se contado 120), B = vizinhas
de 6 arestas, C = 2 arestas, D = 2 candidatos.

## Relação com NODE-FILL

`CR-BLOCK-NODE-FILL-JOINT` (branch `claude/cr-block-node-fill-joint-9tv0kd`,
SHA `bf4054b`, base `2594f6ff` — anterior a toda a linha ARM-ROLE; só
lido, nada aplicado). Mecanismo: `_layout_internal_joint_positions_cm`
nunca incluía a junta de FRONTEIRA contra uma PEÇA DE NÓ; o fix
(`_wall_node_boundary_joints_cm`) passa essa junta (ex.: 34,5) para a
lista `avoid` da outra família. Medido lá: TGD `PRISM_CONTINUOUS_JOINT`
562→318, TP1 730→169 (base antiga; a `main` atual mede 476/444).

| caso | relação | motivo |
|---|---|---|
| TGD 90, 89, 92, 91 (124 cm) | **INDEPENDENT** | a coincidência é nó\|fill (A) × fill\|nó (B) num trecho de 19 cm com UMA composição possível — evitar 34,5 não tem alternativa; só o papel resolve |
| TGD 120, TP1 75 (69 cm) | **INDEPENDENT** | idem (dois trechos de 19 cm) |
| TGD 4, 54 | **INDEPENDENT** | junta nó\|nó idêntica nas duas famílias (canto girado) |
| TP1 20, 91 | **RELATED** | 89,5 é nó\|fill em A × `C09\|C09` (fill\|fill) em B; existe fill alternativo (`B19+C09`) que a lista `avoid` com 89,5 poderia escolher — possivelmente suficiente sem mudar papel |
| Grupo A (gates) | **INDEPENDENT** | código distinto (seção SAFE REPAIR × fill); sem conflito de mecanismo |
| Grupo B (vizinhas) | **INDEPENDENT** | reserva/room/não-modular, não junta de fronteira |

Conflito de integração: o NODE-FILL altera `wall_stepper.py` (+759) e
`wall_pairing.py` (+284) a partir de uma base anterior a ARM-ROLE/SAFE
REPAIR — precisa de rebase/merge próprio; não conflita com o CR
recomendado abaixo (que vive só na seção SAFE REPAIR).

## Priorização

| grupo | arestas | TGD/TP1 | severidade | ganho se corrigido | risco | arquivos | conflita com NODE-FILL |
|---|---|---|---|---|---|---|---|
| A1+A2 (proxies) | TP1 75 (PROVADO); TGD 89/90 mudam de motivo | 2 / 1 | alta (rejeita o layout humano) | TP1 75: −102 achados, 0 novos; base para A3 | **baixo** (só gates; validado por rebuild + validador completo) | `wall_stepper.py` seção SAFE REPAIR + testes | não |
| A3 (espelho) | TGD 120, TP1 20, 91 | 1 / 2 | média | 3 arestas = layout humano no alvo; alvo do TP1 4→2 compensadores | médio (política do contrato) | idem | não |
| B (paredes curtas) | vizinhas de 6 arestas + TGD 89/90/91/92 restantes | 4 / 2 | alta (todas as paredes de 54–69 cm da planta) | destrava 89/90/91/92; remove `C09×4`, cantos degradados | **alto** (nós L/T + regra de B19; decisão do usuário) | `solve_l_corner`, `solve_t_intersection`, `_wall_reserved_range_ft`, `_corner_single_element_candidate`, `_pier_ordered_layout` | não (regiões distintas) |
| D (jamb) | TGD 120/SAME_A, TP1 75/SAME_B | 1 / 1 | média | 88/76 | médio | `_recut_openings_and_repair` | não |
| C (girado) | TGD 4, 54 | 2 / 0 | baixa (sem gabarito) | 2 prismas longos | médio-alto | `solve_l_corner` (girar), entrada 54/59 | não |
| NODE-FILL | TP1 20, 91 (+ prisma global) | — | alta (global) | −244/−561 prisma (base antiga) | alto (rebase grande) | fill + `wall_pairing` | é o próprio |

**Ordem recomendada**: A1+A2 → (decisão) A3 → decisão de regra para B →
B → D → NODE-FILL (linha própria) → C.

## Próximo CR recomendado

### CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY (recomendado)

- **Objetivo**: os gates 4 e 5 do Candidate Safety Contract passam a medir
  o que o validador real mede — (a) compensadores consecutivos por FIADA
  FÍSICA (`course_candidates`, como o gate de cobertura já faz), nunca
  sobre `result["candidates"]` agregado; (b) cobertura por fiada creditando
  o quadrado de canto ocupado pela peça `L_CORNER` da vizinha (ou, mais
  simples e ainda por delta: comparar a SOMA das duas famílias da parede,
  que é invariante à troca de papel), mantendo a tolerância relativa para
  o resto; (c) **opcional, decisão explícita**: identidade de regressão
  por contagem `(parede, código)` em vez de por fiada, para não contar
  espelho de paridade como achado novo (precedente: P3 no audit).
- **Arquivos prováveis**: `nuvem/core/engine/wall_stepper.py` (só
  `_wall_compensator_run_signatures`, `_no_new_consecutive_compensators`,
  `_wall_row_covered_length_cm`/`_no_new_row_coverage_regression`,
  eventualmente `_evaluate_corner_role_candidate`);
  `tests/test_block_arm_role_candidate_safety_contract.py` (T2/T3 com
  fantasma sintético multi-banda e com quadrado de canto);
  `docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md`;
  `REGRAS_MODULACAO_BLOCOS.md` seção 31/32.
- **Ganho esperado**: com (a)+(b): TP1 75/SAME_A aceito (PROVADO: 0 novos,
  102 resolvidos; `PRISM_CONTINUOUS_JOINT` TP1 −16, `COMPENSATOR_CONSECUTIVE`
  −18, `STAGGER` −48). Com (c): TGD 120/SAME_B, TP1 20/SAME_B, TP1
  91/SAME_B aceitos (PROVÁVEL; nenhuma contagem por parede/código sobe;
  prisma −16/−16/−16, TP1 alvos 4→2 compensadores). TGD 89/90 continuam
  rejeitados (vizinha 68 cm MISSING→GAP não é comparável por contagem) —
  corretamente, até o Grupo B.
- **Risco**: baixo. Não muda o solver; muda só o que o contrato mede. O
  risco real é (c) — por isso separado e opcional. Falso NEGATIVO do
  fantasma (esconder regressão real) não foi observado nos 30 rebuilds
  medidos, mas o gate por fiada física também o elimina.
- **Dependências**: nenhuma de código. Não toca NODE-FILL, nós ou fill.

### CR-BLOCK-SHORT-WALL-NODE-PIECES (seguinte, requer decisão de regra)

- **Objetivo**: parede curta (54–69 cm) entre L e T/L: canto `B34` inteiro
  quando fisicamente cabe (reserva da outra ponta pelo que ELA de fato vai
  colocar, não pior-caso 34 cm), e fill `B19+B34`/`B39` em vez de `C09`
  degradado + `C09×3/×4`; trecho de 38,1 cm até a face da vizinha fecha
  com `B39`.
- **Arquivos**: `solve_l_corner`, `solve_t_intersection`,
  `_wall_reserved_range_ft`/`_corner_wall_room_ft`,
  `_corner_single_element_candidate`, `_wall_end_default_start_cm`,
  `_pier_ordered_layout` (ordem do compensador em relação a peça de nó).
- **Ganho**: destrava TGD 89/90/91/92 (vizinhas) e limpa todas as paredes
  de 54–69 cm (dezenas de `COMPENSATOR_*` e `COVERAGE_*` no baseline).
- **Risco**: alto — colisão entre peças de nós vizinhos (a razão histórica
  do pior-caso) e **conflito de regra**: o Reference Corpus usa `B19`
  encostado em junção em TODAS essas paredes; a regra de 2026-08-25 diz
  "nunca meio bloco como recurso para fechar uma amarração". Precisa de
  decisão do usuário e registro em `REGRAS_MODULACAO_BLOCOS.md` ANTES do
  código.
- **Dependências**: decisão de regra; independente do CR anterior.

### Pendências de registro (NÃO feitas aqui, por instrução explícita de não alterar `REGRAS_MODULACAO_BLOCOS.md`)

`DOCUMENTADO — pendência de registro aberta` (conhecimento de amarração,
obrigatório por CLAUDE.md):

1. PADRÃO OBSERVADO no gabarito (6/6 paredes de 124 cm L–X–L, 2/2 de 69 cm
   L–L): os dois `B34` de canto de uma parede curta ficam na MESMA
   família; a outra família leva só `B39` (e `B19 B19` em volta de um
   cruzamento, sem peça X sobre a parede curta).
2. CONFLITO: gabarito usa `B19` encostado em L/T em paredes de 54 cm
   (`JUNCTION_HALF_BLOCK_ADJACENT ×6` por parede) × regra "nunca B19 como
   recurso de amarração"/`CORNER_SINGLE_ELEMENT_CODES` sem `B19`.
3. PADRÃO OBSERVADO: parede curta que CHEGA num T não recebe peça de
   amarração T no gabarito (encosta `B19`/`B39`).
4. Defeito do contrato: gate de compensadores mede sobre agregado de
   bandas (fantasma) e cobertura local ignora quadrado de canto emprestado.

## Veredito

**DIAGNÓSTICO CONCLUÍDO — PRÓXIMO CR DEFINIDO**
(`CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY`, Grupo A1+A2, com A3 como
decisão explícita).

PROVADO: (i) TP1 75/SAME_A é rejeitado por um run fantasma do agregado de
bandas — validador real: 0 novos / 102 resolvidos; (ii) o motivo declarado
de TGD 89/90 (cobertura do alvo) é artefato do proxy local (o humano tem
exatamente 78 cm nessa fiada); (iii) em 8/10 arestas o gabarito humano é o
próprio candidato de papel que o solver gera (`SAME_B` ×6, `SAME_A` ×2);
(iv) TGD 4/54 são cantos girados por `_corner_bond_blocked_by_other_node`,
fora do alcance de ARM. PROVÁVEL: TGD 120/SAME_B e TP1 20/91/SAME_B são
espelhos de paridade sem aumento de contagem. INCONCLUSIVO: por que a
busca de desencontro não alcança `B34+C04`/`C04`-primeiro em 128/135; fix
correto para os cantos girados.

NÃO IMPLEMENTADO. NÃO MERGEADO. NODE-FILL não iniciado. Nenhum
monitoramento criado.
