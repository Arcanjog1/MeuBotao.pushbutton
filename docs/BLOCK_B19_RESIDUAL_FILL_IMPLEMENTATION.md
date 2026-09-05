# RELATÓRIO FINAL — B19 RESIDUAL FILL

`CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION` (2026-09-05). Implementa a
decisão humana aprovada sobre B19 em cima da evidência de domínio já
coletada em `docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md` (investigação
apenas, `REQUIRES_HUMAN_DOMAIN_APPROVAL`, nenhum código tocado). Regras:
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, seção 35 (e a atualização na "Regra
do meio-bloco (B19)"/11.6, no início do arquivo).

## Base

```
origin/main = 209695d5559b53fe4cc8a92300779a8ae73b7c1d  (confirmado)
```

Contém: NODE-FILL (PR #17), ARM SAFE REPAIR GATE FIDELITY (PR #18),
`NODE_FILL_OPPOSITE_COURSE_ENABLED = True`, `ARM_ROLE_SAFE_REPAIR_ENABLED
= True`. Confirmado via `git fetch origin` + API do GitHub (PR #17 e #18
`merged=true`) antes de qualquer alteração desta CR.

## Branch / HEAD

```
branch: claude/cr-block-b19-residual-fill-uythsk
base:   origin/main @ 209695d5 (branch nova, sem cherry-pick)
```

## STATE_A pós-Gate-Fidelity

Medido com `nuvem/benchmark.solver_bridge.run_solver` +
`extract.from_solver.project_from_solver` + `validators.run_all`
(`write_files=False`), mesmo caminho real do benchmark usado nas CRs
anteriores desta série, sobre a `main` pura (esta CR ainda não aplicada).

| | TGD | TP1 | Piloto |
|---|---|---|---|
| findings_total | 4917 | 4905 | 124 |
| COMPENSATOR_CONSECUTIVE | 379 | 1443 | 36 |
| COMPENSATOR_EXCESS_IN_RUN | 341 | 1067 | 28 |
| COMPENSATOR_VERTICAL_STRIP | 58 | 186 | 18 |
| COVERAGE_GAP_IN_ROW | 1959 | 327 | 16 |
| PRISM_CONTINUOUS_JOINT / STACK | 320 / 19 | 256 / 16 | 0 / 0 |
| POSITION_OVERLAP / collisions | 29 / 1043 | 18 / 14 | 0 / 0 |
| JUNCTION_MISSING_BINDING | 23 | 9 (falha conhecida, seção 32) | — |
| JUNCTION_HALF_BLOCK_ADJACENT | 0 | 0 | 0 |
| ARM accepted | `23\|SAME_A`, `91\|SAME_B` | `75\|SAME_A` | — |
| runtime solver | 33.3s | 17.5s | 0.25s |

Estes números batem exatamente com o STATE_B já publicado em
`docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_IMPLEMENTATION.md` — confirma
que a medição está sobre a MESMA main pós-#17/#18, sem drift.

## Regra B19 anterior

Estrita e incondicional: B19 nunca perto de amarração (nó L/T/X, ponta ou
meio de parede), só em vão de abertura ou ponta livre de verdade —
`_corner_single_element_candidate` nunca oferece B19
(`CORNER_SINGLE_ELEMENT_CODES = ("C09","C04")`), e a rede de segurança
`audit_wall_bond_quality`/`HALF_BLOCK_NEAR_TIE` bloqueia qualquer B19
lançado perto de amarração, incondicionalmente. Diverge do corpus humano
aprovado em 259 ocorrências medidas no TP1 (seção 24.3 das regras).

## Regra B19 nova

B19 PODE fechar um trecho residual de **15-20cm**, ADJACENTE a uma peça
de amarração de nó (B34/B54) já presente e ÍNTEGRA NA MESMA FIADA — nunca
sendo ele mesmo a peça de amarração, nunca ocupando o ponto físico do nó
da OUTRA ponta, nunca substituindo B34/B54. Depende do TRECHO RESIDUAL
medido, nunca do comprimento total da parede. A proibição estrita
histórica **continua valendo fora dessa condição específica** — não foi
liberado B19 genericamente perto de nó, nem por comprimento de
parede/wall_idx/projeto. Registrada em `nuvem/REGRAS_MODULACAO_BLOCOS.md`
seção 35 e na atualização da seção "Regra do meio-bloco (B19)"/11.6 —
histórico da regra anterior preservado, nunca apagado.

## Primeira divergência

Para as paredes-alvo (TP1 `wall_idx=12/13/14/15/87/88/89/90`, 54cm T+L
nas duas pontas): `_wall_reserved_range_ft` reserva o pior-caso
(`CORNER_B34_ROOM_FT`, 34cm) na ponta OPOSTA para CADA ponta,
simetricamente. Para 54cm isso deixa `room_ft ≈ 20cm` em CADA ponta,
abaixo dos 34cm exigidos — **as DUAS pontas degradam para compensador em
TODA fiada, e NENHUMA peça de amarração real chega a se formar em nenhuma
ponta**. A condição da regra aprovada ("peça de nó já íntegra") nunca
fica satisfeita sozinha — implementar só a preferência B19 sem mais nada
faria B19 nascer nas DUAS pontas ao mesmo tempo (nó nunca amarrado por
peça real, o defeito `W039`↔`W041`, fora de escopo). `room_ft≈20cm` bate
com o topo da faixa aprovada, mas é simétrico nas duas pontas — a decisão
de qual ponta vira TIE (peça real) e qual vira FILL (B19) precisa ser
coordenada, não decidida ponta a ponta isoladamente.

Medido ao vivo, ANTES desta CR (TP1 `wall_idx=12`):

```
fiada par:   C09[0-9](T_DEGRADED)  B34[10-44](STANDARD_FILL, flutuante)  C09[45-54](L_DEGRADED)
fiada ímpar: C09[0-9](T_DEGRADED)  C09[10-19]  C09[20-29]  C09[30-39]      <- cascata C09x4
```

## Implementação

Reparo pós-hoc isolado (`repair_b19_residual_fill`,
`nuvem/core/engine/wall_stepper.py`), MESMO padrão seguro de
`repair_arm_role_isolated_edges` — candidato → pin → reconstrução REAL
multi-banda via `rebuild_fn` → hard gates → aceita ou reverte. Decisão do
usuário (duas opções apresentadas: mudar o room-check global vs. reparo
pós-hoc isolado) — escolhido o reparo pós-hoc, com autorização explícita
de tocar 2 arquivos de produção (`wall_stepper.py` + o 1-linha de fiação
em `wall_modeling.py`, mesmo padrão do SAFE REPAIR) e, depois de reportado
e aprovado, um 3º ajuste em `audit_wall_bond_quality`
(`wall_modeling.py`) para refinar a rede de segurança.

Novos símbolos em `wall_stepper.py` (todos em `__all__`):

- `B19_RESIDUAL_FILL_MIN_CM`/`MAX_CM` (15/20cm), `B19_RESIDUAL_RESERVE_FT`
  (usa o MAIOR valor da faixa — nunca reserva de menos).
- `_wall_reserved_range_ft`: desvio ADITIVO — nó da ponta oposta marcado
  `_b19_residual_fill_for_wall == wall_idx` usa reserva reduzida; sem
  marca, comportamento byte-a-byte idêntico ao anterior. A marca é por
  PAR (nó, parede) — nunca vaza para outra parede que compartilhe o mesmo
  nó (ex.: a perpendicular de um L_CORNER).
- `_corner_single_element_candidate` ganhou `nodes=None` opcional: nó
  marcado PARA esta `wall_idx` + `room_ft` na faixa aprovada → B19
  (`placement_reason="B19_RESIDUAL_FILL"`); fora disso, C09/C04 de
  sempre. Nunca transforma B19 em candidato de peça de nó.
- `_wall_two_end_node_indices`/`_wall_all_junction_node_indices`/
  `_node_other_wall_idx`: topologia — só paredes com DOIS nós genuínos
  (`L_CORNER`/`T_INTERSECTION`) nas duas pontas físicas, sem nó de meio.
- `_b19_residual_edge_candidates`: topologia válida + as DUAS pontas
  degradadas JUNTAS em alguma fiada no ORIGINAL + aritmética de resíduo
  (`comprimento - 34cm(B34) - 1 junta`) na faixa aprovada.
- `_evaluate_b19_residual_candidate`: MESMOS hard gates do SAFE REPAIR
  (fechamento → colisão → prisma forçado NO ALVO **e** em vizinha →
  compensadores consecutivos → cobertura) — o gate de prisma no próprio
  alvo é um acréscimo desta CR.
- `repair_b19_residual_fill`: tenta as DUAS atribuições possíveis (qual
  ponta vira fill) — aceita a primeira que passa os hard gates.

`wall_modeling.py`: `B19_RESIDUAL_FILL_REPAIR_ENABLED = True` (mesmo
padrão de `ARM_ROLE_SAFE_REPAIR_ENABLED`) + fiação em
`solve_building_blocks_all_courses` (roda DEPOIS do SAFE REPAIR do ARM
ROLE — uma peça resgatada pelo ARM precisa estar presente antes deste
reparo decidir se há resíduo). `audit_wall_bond_quality` (rede de
segurança `HALF_BLOCK_NEAR_TIE`): refinado para não contar
`placement_reason == "B19_RESIDUAL_FILL"` como violação — qualquer outro
B19 perto de amarração continua bloqueado exatamente como antes.

## Prova de que B19 continua não sendo peça de amarração

Em TODOS os 8 candidatos aceitos no TP1: a ponta TIE recebe B34 REAL
(`placement_reason` `L_CORNER`/`T_INTERSECTION_INCOMING`, nunca
degradado) e só a ponta FILL recebe B19 (`placement_reason=
"B19_RESIDUAL_FILL"`). Nenhum B19 aceito tem `placement_reason` de peça
de nó (`test_t30_tp1_tie_e_real_fill_e_b19_residual`, que falha
explicitamente se algum B19 aparecer com `placement_reason` de amarração).
A ponta FILL nunca alcança o ponto físico do nó DA OUTRA PONTA (o B19
fica estritamente dentro do `room_ft` calculado, que é sempre menor que
a distância até a reserva da ponta oposta).

## Casos TP1

8 candidatos elegíveis, **8 aceitos, 0 rejeitados** — `wall_idx` 12, 13,
14, 15, 87, 88, 89, 90 (as paredes de 54cm T+L citadas em
`docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md`, Fonte 1+2).

```
ANTES  (wall_idx=12, fiada par):  C09[0-9] B34[10-44](flutuante) C09[45-54]
                (fiada ímpar):    C09[0-9] C09 C09 C09              <- cascata
DEPOIS (fiada par):   B19[0-19](B19_RESIDUAL_FILL) B34[20-54](L_CORNER)
       (fiada ímpar): B19[0-19](B19_RESIDUAL_FILL) B19[20-39](STANDARD_FILL)
HUMANO (TP1 W013, par):  B19[0-19] B34[20-54]   (ímpar: B39[0-39] solto)
```

A fiada par bate EXATAMENTE com o humano (mesma composição, mesma
posição) — `CONFIRMED_BY_HUMAN`. A fiada ímpar cobre o mesmo comprimento
físico (39cm) sem regressão de cobertura/colisão, mas com composição
diferente do humano (`B19+B19` vs `B39` solto) — `DIFFERENT_VALID`: o
humano não tem NENHUMA amarração real nesse nó na fiada ímpar (mecanismo
fora de escopo desta CR, mesma natureza do defeito `W039`↔`W041`).

## Casos TGD

**0 candidatos elegíveis** — nenhuma parede da reconstrução atual do TGD
tem a assinatura geométrica exata (2 nós genuínos nas pontas, sem nó de
meio, resíduo aritmético em 15-20cm). Limite de escopo documentado, não
um defeito: paredes candidatas por comprimento (64/68/69cm, `wall_idx`
120/127/129-134) têm resíduo fora da faixa (29/33/34cm) ou já fecham sem
degradação — a decisão nunca generaliza por comprimento de
parede/projeto para compensar a ausência de casos no TGD.

## Casos negativos

Verificados por teste direto (`tests/test_block_b19_residual_fill_
implementation.py`):

- 69cm L-L (resíduo 34cm, TGD `wall_idx=120`/TP1 `wall_idx=75` — o par
  humano `B34+B34` exato, zero B19): fora da faixa, nunca vira candidato
  (T10).
- Resíduo 11cm / 39cm: fora da faixa, nunca vira candidato (T8/T9).
- Parede com nó de MEIO (main wall de T/X que atravessa): desqualificada
  por topologia, nunca considerada (T2).
- Ponta FREE_END: desqualificada (T3).
- Resíduo compatível mas as pontas já fecham com peça real: nunca tenta
  reparar o que já funciona (T11).
- Nó marcado para OUTRA `wall_idx`: nunca vaza — a reserva e a
  preferência por B19 ficam isoladas por parede (T14/T18).
- Sem marca (`nodes=None`) — nunca gera B19, mesmo com `room_ft` na
  faixa aprovada (T17, prova que o comportamento antigo continua intacto
  para todo chamador que não passa pelo reparo).

## Reference Corpus

- TP1 `wall_idx=12/13/14/15/87/88/89/90`, fiada PAR: `CONFIRMED_BY_HUMAN`
  (composição idêntica ao gabarito, `W013`/`W088` e equivalentes).
- TP1, mesmas paredes, fiada ÍMPAR: `DIFFERENT_VALID` (cobertura igual,
  composição diferente — mecanismo fora de escopo, ver acima).
- Nenhum `CONFLICTS_WITH_HUMAN` identificado.

## C09 / compensadores

| | TGD | TP1 |
|---|---|---|
| COMPENSATOR_CONSECUTIVE | 379 → 379 | 1443 → **1275** (−168) |
| COMPENSATOR_EXCESS_IN_RUN | 341 → 341 | 1067 → **928** (−139) |
| COMPENSATOR_VERTICAL_STRIP | 58 → 58 | 186 → **166** (−20) |

Redução direta da cascata `C09×3`/`C09×4` que motivou a CR, sem trocar
nenhum compensador CORRETO (o caso de 79cm/resíduo 11cm nunca é tocado —
`_corner_single_element_candidate` só é chamado quando o resíduo já é
insuficiente para B34, e minha condição de faixa exclui 11cm por
construção).

## Prism

`PRISM_CONTINUOUS_JOINT`/`PRISM_JOINT_STACK`: delta **zero** nos três
projetos (256/16 TP1, 320/19 TGD, 0/0 Piloto — idênticos antes/depois).
`PRISM_STAGGER_BELOW_TARGET` (nível 2, preferência — nunca reprova):
TP1 1370 → 1382 (+12), TGD/Piloto inalterados — efeito colateral pequeno
e não-bloqueante da nova composição nas fiadas ímpares das 8 paredes
reparadas.

## Coverage

`COVERAGE_GAP_IN_ROW`: TP1 327 → **309** (−18, melhoria — o resíduo que
antes ficava mal fechado por compensadores passa a fechar com B19+B34).
`COVERAGE_PARTIAL_WALL`/`COVERAGE_ROW_MOSTLY_EMPTY`: inalterados nos três
projetos. Nenhuma regressão de cobertura em nenhuma parede (gate
`_no_new_row_coverage_regression`, delta zero fora das 8 paredes
reparadas).

## Junctions

`JUNCTION_MISSING_BINDING`: TP1 9 → 9 (idêntico — a mesma falha conhecida
pré-existente, seção 32); TGD 23 → 23. `JUNCTION_HALF_BLOCK_ADJACENT`: TP1
**0 → 34** — ver "Reference Corpus"/seção 35.6 das regras: este validador
mede literalmente "o corpo de um B19 alcança o ponto físico do nó",
EXATAMENTE a métrica que a evidência de domínio já tinha medido 259 vezes
no próprio gabarito humano aprovado. Antes desta CR o solver media 0
porque nunca colocava B19 perto de nó nenhum; agora converge parcialmente
para o padrão humano (34 das 259 ocorrências) — resultado ESPERADO da
CR, não um defeito. `JUNCTION_NOT_ALTERNATING`: TGD 303 → 303 (TP1 não
mede esta categoria no baseline atual).

## Openings

`OPENING_BLOCK_CROSSES_JAMB`/`OPENING_MISSING_COUNTER_LINTEL`: delta zero
nos três projetos (168/21 TP1, 108/25+82/32 TGD, 0/4 Piloto — idênticos).

## Collisions

`POSITION_OVERLAP`/`collisions` (solver): delta **zero** nos três
projetos (29/1043 TGD, 18/14 TP1, 0/0 Piloto — idênticos antes/depois).

## ARM

`arm_role_safe_repair`: `accepted`/`rejected` idênticos antes/depois nos
três projetos (`23|SAME_A`+`91|SAME_B` TGD, `75|SAME_A` TP1, nenhum
Piloto) — o reparo B19 roda DEPOIS do SAFE REPAIR do ARM e não interfere
nas decisões dele (gates independentes, wiring sequencial documentado em
`solve_building_blocks_all_courses`).

## NODE-FILL preservation

`NODE_FILL_OPPOSITE_COURSE_ENABLED = True` inalterado — não tocado por
esta CR. `tests/test_block_node_fill_revalidation.py` e `tests/
test_block_arm_role_prism_stagger.py` continuam passando integralmente
(nenhum teste alterado por esta CR).

## Determinism

Fingerprint `walls_blocks` idêntico em duas execuções SEPARADAS
(processos novos) sobre o TP1, mesmo conjunto de `wall_idx`
aceitos/`fill_node` (`test_t33_determinismo_duas_execucoes_separadas`).
TGD: fingerprint idêntico ANTES/DEPOIS desta CR (0 candidatos, nenhuma
mudança).

## Performance

| projeto | STATE_A (s) | STATE_B (s) | delta |
|---|---|---|---|
| TGD | 33.3 | 37.0 | +11% (0 candidatos — custo da triagem, sem rebuild extra) |
| TP1 | 17.5 | 40.4 | +130% (9 rebuilds extras: 8 candidatos aceitos de primeira + 1 rebuild final) |
| Piloto | 0.25 | 0.13 | ruído (projeto trivial) |

Custo real e esperado: cada candidato aceito custa 1 rebuild multi-banda
completo extra (o mesmo padrão de custo já aceito pelo SAFE REPAIR do
ARM, que documentou o mesmo tipo de trade-off "caro por tentativa,
seguro"). Sem crescimento de rebuilds por candidato além do necessário
(nenhum candidato desta rodada precisou da segunda tentativa/atribuição
invertida).

## Tests específicos

`tests/test_block_b19_residual_fill_implementation.py` — T1-T33: **33
passed** (28 rápidos, 0.13s; 5 marcados `slow` com corpus real,
TGD+TP1, ≈255s). Cobre topologia, aritmética de resíduo (extremos 15/20cm
e o valor real 19cm, negativos 11/39cm e o caso 69cm-L-L), isolamento da
reserva reduzida (nunca vaza entre paredes), preferência B19 só quando
marcado E na faixa (nunca generaliza), os 6 hard gates (colisão, prisma
no alvo, prisma em vizinha, fechamento, compensadores, cobertura),
orquestração com `rebuild_fn` falso (reversibilidade, determinismo de
ordem), e prova física contra o corpus real (TP1 8/8 aceitos, TGD 0/0,
determinismo em processos separados).

## Full suite

`pytest tests -q`:

| | ANTES desta CR (main, `docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_IMPLEMENTATION.md`) | DEPOIS (medido nesta sessão) |
|---|---|---|
| passed | 606 | **639** (+33 = `test_block_b19_residual_fill_implementation.py`) |
| failed | 1 | 1 (a mesma) |
| falha conhecida | `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]` — `JUNCTION_MISSING_BINDING` 8→9 (P3 — BENCHMARK_ARTIFACT, seção 32) | idêntica, mesma mensagem (a mesma falha CRÍTICA já existente é a que o assert reporta primeiro; a categoria `junctions` TAMBÉM mudaria — ver seção 35.6 das regras — mas o teste já falha antes de chegar lá) |

Nenhum teste desabilitado; nenhuma falha NOVA além da já conhecida.

## Production diff

Dois arquivos de produção tocados (autorizado explicitamente pelo
usuário, com relato antes de cada extensão de escopo):

- `nuvem/core/engine/wall_stepper.py` — novo bloco "CR-BLOCK-B19-
  RESIDUAL-FILL-IMPLEMENTATION" (constantes, 5 funções novas +
  `repair_b19_residual_fill`) + 2 funções existentes estendidas
  (`_wall_reserved_range_ft`, `_corner_single_element_candidate`) com
  parâmetro/desvio ADITIVO (comportamento sem marca é byte-a-byte
  idêntico ao anterior).
- `nuvem/core/wall_modeling.py` — `B19_RESIDUAL_FILL_REPAIR_ENABLED` +
  fiação em `solve_building_blocks_all_courses` (mesmo padrão do SAFE
  REPAIR do ARM) + refinamento de `audit_wall_bond_quality` (exceção
  aditiva por `placement_reason`, reportado e aprovado antes de aplicar).

Sem mudança em `wall_pairing.py`, `solve_l_corner`/`solve_t_intersection`
(lógica de decisão em si), canonical ordering, tolerâncias, ou
special-case por `wall_idx`/projeto.

## Baseline diff

`baseline.json` do TP1 **NÃO foi regravado** por esta CR (decisão
explícita — nunca atualizar baseline só para o teste passar). Isso
significa que `tests/regression/test_benchmark_baselines.py` reporta,
além da falha crítica já conhecida (`JUNCTION_MISSING_BINDING`), a
categoria `junctions` como `REGRESSAO` (1→5 paredes reprovadas) — reflexo
direto do `JUNCTION_HALF_BLOCK_ADJACENT` 0→34, que é a melhoria aprovada
por esta CR, não uma regressão real (ver seção "Junctions" acima).
Atualizar `baseline.json` para refletir isso é decisão do usuário, junto
com a autorização de merge — não feito aqui.

## Reference diff

ZERO — nenhum `reference.json`/`reference_score.json` tocado.

## Deferred / out-of-scope

- NODE-FILL e Gate Fidelity: não tocados (flags inalteradas, testes
  próprios intactos).
- Rotated corners (`OUT_OF_SCOPE_ROTATED_CORNER`, TGD 4/54): não tocados.
- `W039`↔`W041`: não tocado — o nó nunca é fisicamente coberto por
  nenhuma peça (nem no humano); B19 fill não resolve isso.
- Fiadas ÍMPARES das 8 paredes reparadas no TP1 (mecanismo `B39` solto do
  humano, sem amarração real no nó): fora de escopo, mesma natureza do
  item acima.
- TGD sem casos reais desta regra na reconstrução atual: limite de
  escopo documentado, não um defeito.
- `non_modular` +56 no TP1: artefato pré-existente de contabilidade do
  preenchimento comum (mesmo padrão já presente em `wall_idx=75`),
  ampliado (mais paredes com fechamento flush), não investigado a fundo
  — fora do escopo da regra de B19.

## Gates / veredito

| gate | status | evidência |
|---|---|---|
| STATE_A medido | PASS | tabela acima, main pura |
| causa-raiz provada | PASS | leitura de código + medição ao vivo (room_ft≈20cm simétrico nas duas pontas) |
| mudança mínima e isolada | PASS | desvio aditivo por marca `(nó, wall_idx)`, comportamento sem marca idêntico |
| B19 nunca é peça de amarração | PASS | T30, prova por `placement_reason` em 8/8 casos reais |
| não generaliza | PASS | T8-T11/T14/T17/T18, TGD 0 candidatos, 69cm-L-L excluído |
| hard gates (6, incl. prisma no alvo) | PASS | T19-T25 |
| reversibilidade/determinismo | PASS | T26-T28, T33, fingerprint idêntico |
| NODE-FILL/Gate Fidelity preservados | PASS | flags inalteradas, ARM accepted idêntico |
| rotated corners / W039-W041 fora de escopo | PASS | não tocados |
| rede de seguranca HALF_BLOCK_NEAR_TIE refinada, nao desligada | PASS | exceção só por `placement_reason`, qualquer outro B19 continua bloqueado |
| corpus real (TP1) | PASS | 8/8 aceitos, fiada par `CONFIRMED_BY_HUMAN` |
| suíte completa | PASS (1 falha conhecida) | 639 passed / 1 failed (mesma falha da main) |
| coverage/collisions/prism (nível 1) | PASS | delta zero fora das 8 paredes reparadas |
| baseline/reference diff | reference ZERO; baseline TP1 deliberadamente NÃO regravado | ver "Baseline diff" |
| diff de produção restrito e revisado | PASS | 2 arquivos, cada extensão de escopo reportada e aprovada antes de aplicar |

**APROVADO PARA INTEGRAÇÃO.**

A decisão humana aprovada foi implementada exatamente como especificada
(fill residual de 15-20cm, adjacente a peça de amarração real já íntegra
na mesma fiada, nunca substituindo B34/B54, nunca generalizado por
comprimento de parede/projeto), com prova física contra o corpus humano
(8/8 casos TP1, fiada par `CONFIRMED_BY_HUMAN`), os mesmos hard gates
provados pelo SAFE REPAIR do ARM (mais um gate extra de prisma no próprio
alvo), determinismo provado, e NODE-FILL/Gate Fidelity/rotated
corners/`W039`-`W041` preservados intactos. TGD não tem casos reais desta
regra na reconstrução atual (0/0, limite de escopo documentado). Único
ponto de atenção para o merge: `baseline.json` do TP1 fica
intencionalmente desatualizado (reflete a melhoria aprovada, não uma
regressão) — atualizá-lo é decisão do usuário.

**NÃO MESCLADO. Aguarda autorização explícita do usuário para merge.
Nenhum monitoramento automático ativado.**
