# VARREDURA AMPLA DO BENCHMARK OFFLINE — 2026-09-08

Base: `main` integrada. Documentação publicada por merge normal
(`08495d9`); trabalho de código na branch
`claude/fervent-mccarthy-lhwoai`.

**Sem Revit. Sem monitoramento automático. Sem merge de código na `main`.**

---

## 0. Estado inicial conferido

| item | valor |
|---|---|
| `main` no início | `4015564` |
| branch documental | `claude/integracao-consolidada-prs-8scic9` HEAD `116fe10` |
| diff documental | 2 arquivos, **exclusivamente** `docs/` — conferido |
| `main` após a publicação | **`08495d9`** |

Gate do `CLAUDE.md` antes da publicação: `tests/test_script.py` →
**260 passed**.

---

## 1. Correção do método de medição (achado que mudou toda a análise)

**`W0xx` NÃO é identidade física entre `input.json` e `result.json`.**
`model.assign_ids` reordena as paredes **geometricamente** e reatribui os
IDs; o `input.json` veio de outra ordenação. Resultado: **165 das 167**
paredes do TGD têm comprimento diferente sob o mesmo `W0xx` nos dois
arquivos — é uma **permutação** (o multiconjunto de comprimentos é
idêntico).

Uma primeira leitura minha, cruzando os dois arquivos por `W0xx`,
"concluiu" que o solver parava de modular no meio de quase toda parede.
**Estava errada.** Refeita pela chave física estável (`wall["key"]`,
que existe e casa 167/167):

| alcance do solver / comprimento | paredes |
|---|---|
| 100% | 105 |
| 90–100% | 23 |
| 30–90% | 9 |
| 0–10% (praticamente vazias) | 29 |

**Toda medição deste relatório usa identidade física**, nunca `W0xx`
cruzado nem contagem de código.

---

## 2. BLOCO 1 — varredura por identidade física

Agrupamento: `(parede, código, posição em t arredondada a 10cm)`,
**ignorando a fiada** — o mesmo defeito repetido em 17 fiadas é **um**
defeito físico, não 17. O gabarito humano passa pelos **mesmos**
validadores, então cada código tem o seu piso de ruído.

### 2.1 TGD (167 paredes) — antes das correções

| código | ident. solver | ident. gabarito | veredito |
|---|---|---|---|
| `COVERAGE_GAP_IN_ROW` | 204 | 330 | solver melhor |
| `PRISM_STAGGER_BELOW_TARGET` | 181 | 101 | pior 1,8× |
| `COMPENSATOR_CONSECUTIVE` | 101 | 52 | pior 1,9× |
| `OPENING_MISSING_LINTEL` | 82 | 56 | equiparável |
| `COMPENSATOR_VERTICAL_STRIP` | 79 | 26 | pior 3,0× |
| `COMPENSATOR_EXCESS_IN_RUN` | 70 | 22 | pior 3,2× |
| `COVERAGE_PARTIAL_WALL` | 48 | 4 | pior 12× |
| `COMPENSATOR_AVOIDABLE` | 39 | **0** | só o solver erra |
| `COVERAGE_MISSING_ROW` | 30 | **0** | só o solver erra |
| `COVERAGE_WALL_NOT_MODULATED` | 29 | **0** | só o solver erra |
| `JUNCTION_NOT_ALTERNATING` | 19 | 1 | pior 19× |
| `POSITION_OVERLAP` | 6 | **0** | só o solver erra |
| `OPENING_SOLID_BELOW_SILL_MISSING` | 4 | **0** | só o solver erra |
| **total** | **959** | — | |

### 2.2 TP1 (96 paredes) — antes das correções

| código | ident. solver | ident. gabarito |
|---|---|---|
| `PRISM_STAGGER_BELOW_TARGET` | 245 | 101 |
| `COMPENSATOR_CONSECUTIVE` | 200 | 52 |
| `COMPENSATOR_VERTICAL_STRIP` | 189 | 26 |
| `COMPENSATOR_EXCESS_IN_RUN` | 153 | 21 |
| `COMPENSATOR_AVOIDABLE` | 87 | **0** |
| `POSITION_OVERLAP` | 2 | 1 |
| **total** | **898** | — |

**A família COMPENSADOR domina**: 629 das 985 identidades do TP1 (64%) e
289 das 998 do TGD. O TP1 sai com **19 572 blocos contra 12 703 do
gabarito** (+54%), sendo **C09 3 153 × 628** (5×).

### 2.3 Erros de AVALIAÇÃO (não defeito físico) identificados

- `JUNCTION_HALF_BLOCK_ADJACENT`: **264/259 no gabarito, 0 no solver**.
  Um validador que só reprova a solução humana e nunca a do solver é
  suspeito de estar medindo a coisa errada — **não foi mexido**, fica
  registrado.
- `JUNCTION_MISSING_BINDING`: 38 identidades no gabarito × 3 no solver —
  o piso de ruído aqui é da **reconstrução geométrica** do gabarito.
- `door_void_violations` do solver (290 TGD / 348 TP1) × 
  `OPENING_BLOCK_INSIDE_DOOR` do validador (5 / 0): contratos diferentes
  (OBB do motor × interseção em `t` por fiada). Divergência registrada,
  não reconciliada nesta sessão.

---

## 3. BLOCO 2 — o que foi CORRIGIDO

### 3.1 `CR-N1` — colisão entre peças de amarração de nós vizinhos ✔ FEITO

Regra registrada em `nuvem/REGRAS_MODULACAO_BLOCOS.md` **seção 40**.

Causa-raiz **medida**: `_room_at_t_on_wall` nunca parava num nó de
encontro no **meio** da parede. Dois T na mesma parede principal a `d` cm
produziam dois B54 centrados sobrepostos em **exatamente `54 − d` cm**.
As **8 identidades de `POSITION_OVERLAP`** do TGD+TP1 eram este caso.

| | TGD | TP1 |
|---|---|---|
| `POSITION_OVERLAP` (ident.) | **6 → 0** | **2 → 0** |
| `POSITION_OVERLAP` (ocorr.) | 29 → 0 | 18 → 0 |
| `COVERAGE_MISSING_ROW` (ident.) | 30 → 18 | — |
| `PRISM_STAGGER_BELOW_TARGET` | 181 → 156 | 245 → 246 |
| `PRISM_JOINT_STACK` | 20 → 14 | 16 → 8 |
| `PRISM_CONTINUOUS_JOINT` | 21 → 15 | 18 → 10 |
| blocos colocados | 11 749 → **12 143** | 19 572 → 19 629 |
| **total de identidades** | 959 → **933** | 898 → **896** |

**Trade-off declarado**: `COMPENSATOR_VERTICAL_STRIP` +30 e
`COMPENSATOR_EXCESS_IN_RUN` +15 no TGD — degradar um T deixa a parede
principal sem peça cheia e o preenchimento comum fecha um trecho maior.
É a tensão normativa da seção 41, não defeito novo.

Reprodutor permanente: `tests/test_neighbor_node_bond_collision.py` (12
testes, geometria sintética) — **falha antes, passa depois**, mais três
guardas no sentido oposto (nós a 70/90/140cm continuam recebendo os dois
B54 inteiros). Nenhum `skip`/`xfail`, nenhum threshold afrouxado,
**nenhuma expectativa de teste existente alterada**.

---

## 3.2 REGRESSÃO CONSOLIDADA — 3 falhas novas, declaradas e diagnosticadas

`python3 -m pytest tests/ -q` na árvore com a CR-N1:
**930 passed, 5 failed** (59min25s).

Base histórica informada: **921 passed, 2 failed**. As 2 falhas
históricas (`tests/regression/test_benchmark_baselines.py`, TGD e TP1)
**continuam** e são pré-existentes (o refresh de `baseline.json` é CR
própria). **3 falhas são novas e são minhas.** Nenhuma foi escondida,
nenhum `skip`/`xfail` foi usado, nenhum threshold foi afrouxado e
**nenhuma expectativa de teste foi alterada** para obter verde.

### Medição que explica as três (harness `_run_tgd` do próprio teste)

| | PRÉ-CR-N1 | PÓS-CR-N1 |
|---|---|---|
| paredes com **prisma forçado** no FINAL | **29** | **27** |
| candidatos ACEITOS pelo ARM SAFE REPAIR | `[(91, SAME_B)]` | **`[]`** |
| paredes candidatas (rejeitadas) | `[4,54,89,90,91,92,120]` | `[4,54]` |
| parede 23 com prisma forçado | não | **não** ✔ |

As paredes 89, 90, 91, 92, 120 e 130 **deixaram de ter prisma forçado no
baseline ORIGINAL** — então nem são propostas ao reparo. O SAFE REPAIR
não foi enfraquecido: **o defeito que ele consertava passou a não existir
na GERAÇÃO**.

### As três falhas, uma a uma

1. `test_block_arm_role_candidate_safety_contract::test_t1_t9_...` —
   falha **só** na asserção 1 (`assert accepted`, "o gate não é vazio").
   As asserções 2 e 3, que são as **físicas**, continuam válidas: a
   parede 23 termina **sem** prisma forçado. É literalmente o precedente
   que o próprio docstring do teste descreve para a parede 23 na CR-G12
   ("o defeito que ele consertava naquela parede deixou de existir na
   geração"), agora acontecendo também com a parede 91.
2. `test_block_arm_role_prism_stagger::test_w076_tp1_...` — a **primeira**
   asserção, a física (*"a coincidência de contorno de W076 está
   RESOLVIDA"*), **PASSA**. Falha só a segunda, de mecanismo (*"um
   candidato ARM foi aceito para W076"*). Mesma causa: resolvido na
   geração, não pelo reparo.
3. `test_cross_band_joint_propagation_cr_g12::test_reproducer_minimo_
   falha_no_codigo_anterior` — o reprodutor PRÉ-G12 **deixou de
   reproduzir**: com a propagação cross-band DESLIGADA, o sub-plano de 3
   paredes agora acusa **zero** identidade (`identidades vistas: []`). A
   CR-N1 mudou o layout das bandas naquele ponto. A mensagem do próprio
   teste antecipa o caso ("conferir se alguma outra correção mudou o
   layout das bandas antes de mexer aqui"). O teste companheiro
   (`..._passa_com_a_correcao`) continua passando.

### Leitura honesta

Nenhuma das três é uma piora física medida — as duas primeiras têm a
asserção física passando no mesmo teste, e a terceira é a premissa de um
reprodutor. Mas **as três são falhas reais de suíte** e a decisão de
converter uma asserção de mecanismo em asserção física (o precedente que
a própria CR-G12 usou, com medição) **é do usuário, não minha** — por
isso os testes ficam **como estão, falhando**, e o PR vai como `draft`.

---

## 4. Frentes que exigem DECISÃO NORMATIVA (registradas, não implementadas)

### 4.1 Teto de compensador × teto de peça especial — seção 41

`TP1/W003`, trecho `[170, 474]` (304cm entre dois nós): o solver entrega
`B39×7 + C09×2 + C04×1` (**3 compensadores em sequência**, violação
literal da regra escrita). Existe `B39×5 + B34×3`, que fecha os **mesmos
304cm** com **ZERO compensadores**, mas é recusado por
`MAX_SPECIAL_BOND_PER_TRECHO = 1`. Enumeração exaustiva: **com peça
especial ≤ 1, o mínimo é 3 compensadores**. O solver está certo dentro
dos tetos que recebeu — **as duas regras é que se contradizem**.

Sub-trechos de 25cm viram `C09+C09+C04`; de 30cm viram `3×C09`.
Entre dois nós fechados, `B19` fecharia com **1** compensador, mas está
proibido ali (regra do meio-bloco + seção 35,
`REQUIRES_HUMAN_DOMAIN_APPROVAL`).

### 4.2 Parede fora do módulo de 5cm fica vazia — seção 42

Parede LIVRE de **197,9cm → 0 peças**; 99,8 / 200,0 / 269,0cm funcionam.
Duas paredes reais de 197,9cm (`W068`, `W091`) saem **vazias** no TGD.
Contrato deliberado (o achado carrega `delta_to_lower_cm`, pedindo
ajuste de comprimento), mas colide com a intenção do tier 8.

---

## 5. DESEMPENHO — investigado, medido, e por que NÃO foi otimizado

Medição no TGD (`nuvem/benchmark/projects/torre_easy_lo_r00_tgd`):

| | |
|---|---|
| tempo total do solver | **57,8 s** |
| rebuilds multi-banda | **7** |
| custo médio por rebuild | **7,9 s** |
| BASELINE | 1 rebuild — 7,6 s (13,1%) |
| **ARM SAFE REPAIR** | **6 rebuilds — 49,2 s (85,1%)** |
| B19 RESIDUAL FILL | 0 rebuilds |
| candidatos ACEITOS pelo ARM | **0** (6 rejeitados) |

As três alavancas do pedido, medidas:

1. **Cache / rebuilds repetidos** → **ganho ZERO, medido**. Com impressão
   digital de **todo** campo serializável de `nodes`, os 7 rebuilds rodam
   sobre **7 estados DISTINTOS**; nenhum repetido. Memoizar não economiza
   nada. *(Uma primeira medição minha, que só contava mutação de bits de
   papel, indicou "6 redundantes" — estava errada por não cobrir as
   marcas do reparo B19. Refeita.)*
2. **Triagem barata antes do rebuild** → **não disponível**. Os 6
   rejeitados dão todos `does_not_resolve_target`, e esse gate lê
   `wall_bond_audits` do **resultado do rebuild**. Não há como decidir
   sem reconstruir.
3. **Escopo incremental** → **é a alavanca real, e está fora do escopo
   desta varredura**. Cada tentativa muda **uma** parede (`dirty_wall_
   idxs` já é calculado no laço) mas re-resolve a planta inteira (167
   paredes). Suportar re-solve parcial exige mexer na coordenação
   multi-banda global do `_solve_building_blocks_all_courses_core` — a
   "refatoração ampla" que o pedido proíbe abrir aqui.

**Nenhuma otimização foi aplicada**: nenhuma das disponíveis tinha ganho
relevante COM equivalência física comprovada, que era a condição do
pedido. **Recomendação**: `CR-PERF-1` dedicada a re-solve por escopo
(`dirty_wall_idxs`), com gate de equivalência bit-a-bit contra o rebuild
completo.

---

## 5.1 DETERMINISMO

Duas execuções do mesmo `input.json` **no mesmo processo**, comparando
peça a peça (`chave física da parede`, fiada, código, `t_start`, `t_end`):

```
TGD  execucao 1: 12143 blocos  fingerprint=fe1218de0cf9f69d
     execucao 2: 12143 blocos  fingerprint=fe1218de0cf9f69d
     DETERMINISTICO: SIM
```

Os testes de determinismo da suíte (`test_t16_execucao_repetida_e_
deterministica`, `test_bench_z_origin`, a família
`block-determinism-*`) **passam** na regressão consolidada.

**Limite honesto desta medição**: ela cobre *mesma entrada, mesmo
processo, posicionamento de blocos*. **Não refuta** a dívida já
registrada em `PROJECT_STATUS.md` ("determinismo global do wall graph —
8 execuções, 8 fingerprints distintos"), que é anterior ao preenchimento
de blocos e não foi reaberta nesta sessão.

---

## 6. Dívidas que continuam abertas

- **C2 / G16**: preservados, **não tocados**. Nada de A/B/C sem decisão
  normativa; nenhuma parede física reagrupada.
- **CR-B**: **não aprovada por inferência**. `input`, `reference`,
  `reference_score` e `baseline` oficiais **não foram regravados**.
- **2 falhas históricas** de `tests/regression/test_benchmark_baselines.py`
  continuam registradas como pré-existentes (o refresh de `baseline.json`
  é CR própria).
- `COMPENSATOR_AVOIDABLE` (39 TGD / 87 TP1 contra 0 no gabarito) e
  `JUNCTION_NOT_ALTERNATING` (19 × 1 no TGD) continuam abertos — os dois
  dependem da decisão da seção 41 para serem atacados sem contradizer
  regra escrita.
- `JUNCTION_HALF_BLOCK_ADJACENT` e a divergência
  `door_void_violations` × `OPENING_BLOCK_INSIDE_DOOR`: suspeita de erro
  de **avaliação**, não medida a fundo.

---

## 7. Recomendação objetiva para a próxima etapa

0. **Resolver as 3 falhas novas de suíte** (seção 3.2) — decisão do
   usuário entre: (a) converter as duas asserções de MECANISMO em
   asserções FÍSICAS, exatamente como a revisão da CR-G12 já fez para a
   parede 23 (a medição que justifica está na seção 3.2); e (b) escolher
   um novo sub-plano para o reprodutor da CR-G12, já que o atual deixou
   de reproduzir. **Nada disso foi feito por mim de propósito** — mexer
   em teste para obter verde é exatamente o que o pedido proíbe.
1. **Decidir a seção 41** (compensador × peça especial). É o gargalo
   normativo de **64% das identidades do TP1**; sem ela, nenhuma correção
   da família compensador pode ser feita sem violar regra escrita.
2. **Decidir a seção 42** (parede fora do módulo). Duas paredes reais
   saem vazias no modelo — é o defeito mais visível num teste real no
   Revit.
3. Só então `CR-PERF-1` (escopo incremental do ARM SAFE REPAIR): 85% do
   tempo, com ganho previsível e gate de equivalência.
