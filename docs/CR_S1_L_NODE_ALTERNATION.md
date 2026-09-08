# CR-S1 — PERDA REAL DE ALTERNÂNCIA EM NÓ L (correção do solver)

> Corrige o defeito **do solver** que deixava de alternar a amarração num
> encontro em **L**. Não altera o gabarito oficial, não implementa a
> CR-C1, não integra a CR-B e não muda nenhuma regra normativa de
> domínio.

## Base / branch / HEAD

| item | valor |
|---|---|
| base obrigatória | `91258dd627af97fe437a56c0506eb096ca5aa267` (`origin/main`, confirmada por `git fetch`) |
| branch | `claude/corrigir-alternancia-no-l-76nnb3` |
| fonte diagnóstica | `claude/cr-b-reconciliacao-contrato-1byigr` (`14926fb`) — §4 do `BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_RECONCILIATION.md` |
| candidato CR-B | `claude/candidato-validacao-gabarito-q450yr` (`5640933`), reproduzido em cópia isolada |
| arquivo de produção tocado | **1** — `nuvem/core/engine/wall_stepper.py` |

`nuvem/benchmark/projects/**` (`input.json`, `reference.json`,
`baseline.json`, `reference_score.json`) **intocado** — conferido por
`git status --short nuvem/benchmark/projects/` (0 linhas). O extrator e o
gerador do candidato da CR-B também: rodaram a partir de uma *worktree*
isolada, em modo leitura.

---

## 1. O nó, e a reprodução do defeito ANTES de tocar em código

Ponto físico presente nos **dois níveis** do mesmo edifício:

```
TGD  (338,52 ; 187,05)        TP1  (8017,26 ; 1289,95)
     diferenca = [7678,7371 ; 1102,9024]  = a translacao documentada
```

`repro_solver_l_node_alternation.py` (evidência da CR-V1/CR-B, rodado sem
alteração nenhuma), contra a `main` `91258dd`:

| estado | fiadas com peça | donos distintos | alterna? |
|---|---|---|---|
| alvenaria HUMANA STATE_R | 13 | 2 | **SIM** |
| alvenaria HUMANA STATE_C | 13 | 2 | **SIM** |
| solver sobre IN_R | 17 | 2 | **SIM** |
| solver sobre IN_C | 17 | **1** | **NÃO** ← |

`projetos com a regressao reproduzida: 2 de 2`. As três premissas da
evidência anterior ficam confirmadas: o humano alterna nas duas
topologias, o solver alternava com a entrada antiga, e os **16 achados
por projeto são UM nó** (17 fiadas → 16 pares consecutivos), não 16 nós.

### A geometria real (não é "parede curta")

Medido no grafo do solver sobre `input_candidate.json` (cópia isolada):

```
IN_R   no' (338,52;187,05)  kind=T_INTERSECTION  main=parede N-S (atravessa)
IN_C   no' (338,52;187,05)  kind=L_CORNER        arms=[N-S, E-O]

  parede N-S   [338,523 ; 180,048] -> [338,523 ; 824,048]   644cm
  parede E-O   [331,503 ; 187,048] -> [1270,503 ; 187,048]  939cm
  vizinho: T_INTERSECTION a 50cm do no', na parede N-S (y=237,048),
           com a N-S como `main_wall_idx`
```

As duas paredes do L têm **644cm e 939cm**. A causa não é comprimento de
parede, não é a contagem de achados e não é o validador.

---

## 2. Causa-raiz

`solve_l_corner` (`wall_stepper.py`) tem um gate de segurança de
2026-08-25: quando a peça de amarração de um dos lados do L esbarraria na
peça de um encontro vizinho da MESMA parede, ele **gira** a peça do canto
— manda as **duas** fiadas para a parede não bloqueada. O custo, já
documentado no próprio código: *aquele canto perde a alternância entre
fiadas*.

O gate que decide isso, `_corner_bond_blocked_by_other_node`, devolvia um
**booleano**: sabia que havia conflito e **jogava fora em QUAL FIADA**.
Sem a fiada, a única saída segura era mesmo girar as duas.

Instrumentação do nó (pré-fix):

```
node[98]  wa=parede N-S  wb=parede E-O   blocked_a=True  blocked_b=False
   lado A (N-S)  t0=0cm  outros encontros em t = 57, 202, 347, 382, 637 cm
                 danger = 34 (B34) + 27 (meio B54) = 61cm  ->  57 < 61  BLOQUEIA
   lado B (E-O)  t0=0cm  outros encontros em t = 197, 262, 517, 932 cm   livre
   => course_a e course_b vao AMBOS para a parede E-O
```

**Mas o vizinho que bloqueia é um `T_INTERSECTION` cuja parede principal é
a N-S — e `solve_t_intersection` só deita peça na parede principal na
FIADA A**, em todos os seus caminhos (B54 no caminho cheio, B34 na
degradação-L, nada na degradação de compensador). Confirmado rodando o
próprio `solve_t_intersection` naquele nó: `course_a` → B34 na parede N-S,
`course_b` → B34 na boneca.

Ou seja: **a fiada B da parede N-S estava livre o tempo todo.** O canto
podia manter a peça nas duas paredes — bastava a peça da N-S ir para a
fiada B. O solver não tinha como saber disso porque a informação da fiada
era descartada no `bool`.

Etapa exata em que a solução correta é perdida: dentro de
`solve_l_corner`, no ramo `blocked_a != blocked_b`, **antes** de qualquer
escolha de peça, de reserva de nó ou de modulação contínua. Não há
recálculo nem reparo posterior desfazendo a alternância — o SAFE REPAIR do
ARM e o `repair_b19_residual_fill` não tocam neste nó.

---

## 3. A correção mínima

Um arquivo, `nuvem/core/engine/wall_stepper.py`. Nenhuma constante de
domínio, nenhuma tolerância, nenhum hard gate e nenhuma regra de L/T/X
alterada. Nenhum B54 forçado, nenhuma regra de "parede curta", nenhum
compensador usado para esconder amarração.

1. **`_wall_junction_nodes_and_ts_ft`** — a varredura de encontros da
   parede passa a devolver `(nó, t)` em vez de só `t`.
   `_wall_junction_ts_ft` vira um `[t for _n, t in ...]` sobre ela, para
   não existir cópia paralela da varredura.

2. **`_node_bond_courses_on_wall(node, wall_idx)`** — em quais fiadas
   aquele nó **deita** peça sobre aquela parede. Só afirma UMA fiada
   quando a convenção do solver daquele tipo de nó a fixa em **todos** os
   caminhos dele (inclusive os degradados e o `ok=False`):
   - `T_INTERSECTION` na parede **principal** → `("A",)`;
   - `X_INTERSECTION` → `crossing_walls[0]` → `("A",)`, `[1]` → `("B",)`;
   - qualquer outro caso (boneca de T, L_CORNER, nó desconhecido) → as
     **duas**, o pior caso, idêntico ao comportamento anterior.

   Isto **lê** convenções que já estavam escritas nos solvers. Não
   introduz regra de amarração nova.

3. **`_corner_bond_blocking_courses`** — mesma geometria e mesma margem do
   gate antigo, mas com **dois alcances-para-trás**, um por fiada:
   - na fiada em que o vizinho deita peça sobre a parede: o teto
     histórico `T_INTERSECTION_B54_HALF_ROOM_FT` (27cm), superestimado de
     propósito — exatamente o valor que o gate já usava;
   - na outra fiada, a peça do vizinho está na perpendicular, mas o
     **corpo** dela ainda atravessa esta parede: a reserva genérica de nó
     `_node_default_reservation_cm` (metade da maior espessura do nó) —
     a mesma medida que o preenchimento comum já reserva para esse corpo.
     **Nunca zero.**

   `_corner_bond_blocked_by_other_node` passa a ser `bool()` disso. Como a
   fiada "deitada" mantém os 27cm, que é o **maior** dos dois alcances,
   o predicado booleano é **idêntico** ao anterior para qualquer
   geometria — nada que dependia dele muda.

4. **A decisão em `solve_l_corner`** — três saídas, nesta ordem:
   1. a fiada que a parede bloqueada **já tem** está livre → não faz nada
      (o gate booleano girava aqui à toa);
   2. a **outra** fiada está livre → **troca** `course_a`↔`course_b`:
      alternância preservada, as duas paredes continuam com peça;
   3. o vizinho ocupa as duas fiadas → **gira**, exatamente como antes.

   A ordem 1→2→3 é o que torna o resultado **invariante à ordem de
   entrada das paredes**: qual fiada a parede bloqueada "já tem" depende
   de ela ser `arms[0]` ou `arms[1]`. A primeira versão desta correção só
   tinha (2) e (3) — e o mesmo nó físico alternava numa ordem de entrada e
   girava na outra. Pego pelo teste de inversão de ordem desta CR, antes
   de qualquer medição de corpus.

O caso que **originou** o giro em 2026-08-25 (T a 20cm de um canto em L)
continua girando, e o teste que o guarda continua passando sem alteração:
ali o vizinho ocupa a parede bloqueada nas duas fiadas
(`{"A","B"}` — 20cm < 34+27 e 20cm < 34+7), a troca só migraria a colisão
e o giro segue sendo a única saída sem sobreposição.

---

## 4. Resultado físico no nó (pós-fix)

`repro_solver_l_node_alternation.py`, mesmo reprodutor, mesma evidência:

```
solver IN_C  TGD   fiadas=17  donos=2  ALTERNA   (W071 <-> W065)
solver IN_C  TP1   fiadas=17  donos=2  ALTERNA   (W071 <-> W065)
projetos com a regressao reproduzida: 0 de 2
```

O solver alterna com **B34/B34**; o humano alterna com **B34/B19**. A
alternância física é a mesma; a peça da fiada ímpar difere. **Não foi
copiada a escolha de B19 do humano** — B19 como peça de amarração é
proibido pela seção 35 e isso exigiria decisão normativa nova.

Efeito colateral **fora do nó alvo, mesma causa-raiz**: o nó
pré-existente do TGD `(163,51 ; 237,05)` — que a reconciliação da CR-B
classificou como defeito prévio fora de escopo — **também passa a
alternar**, nas duas topologias (`IN_R` e `IN_C`). Não é um segundo
mecanismo: é o mesmo gate, no mesmo ramo.

---

## 5. Benchmark — A / B / C / D

Cópias isoladas, gabarito oficial em modo leitura. `A`/`B` = solver sobre
o `input.json` **oficial** contra `reference.json` oficial, sem e com o
patch. `C`/`D` = o mesmo sobre o candidato da CR-B (`IN_C x STATE_C`).
Todo delta abaixo é reconciliado por **identidade física** (coordenada de
mundo + cota), nunca por contagem.

### A → B — `main` atual, gabarito oficial

| projeto | blocos | `critical_errors` | achados alterados |
|---|---|---|---|
| TGD | 11731 → 11731 | 872 → 872 | **nenhum** |
| TP1 | 19572 → 19572 | 485 → 485 | **nenhum** |

**Delta ZERO por identidade física, em todos os códigos, nos dois
projetos.** O patch não tem efeito nenhum no corpus oficial de hoje: a
topologia T→L que expõe o defeito só existe na entrada reconstruída da
CR-B. Portanto **risco de regressão na `main` atual = zero medido**.

### C → D — candidato CR-B (`IN_C × STATE_C`)

| código | severidade | TGD | TP1 |
|---|---|---|---|
| `JUNCTION_NOT_ALTERNATING` | major | 32 → **0** (−32) | 16 → **0** (−16) |
| `PRISM_CONTINUOUS_JOINT` | **critical** | 272 → 240 (−32) | 244 → 228 (−16) |
| `PRISM_JOINT_STACK` | major | 17 → 15 (−2) | 15 → 14 (−1) |
| `PRISM_STAGGER_BELOW_TARGET` | minor | 1591 → 1623 (**+32**) | 1545 → 1561 (**+16**) |
| `COMPENSATOR_CONSECUTIVE` | major | 1414 → 1422 (**+8**) | 1410 → 1418 (**+8**) |
| `COMPENSATOR_EXCESS_IN_RUN` | major | 1151 → 1159 (**+8**) | 1134 → 1142 (**+8**) |
| `COMPENSATOR_AVOIDABLE` | minor | 105 → 106 (+1, em `W073`) | 0 (sem delta) |
| blocos | — | 19433 → 19457 | 19364 → 19380 |
| `critical_errors` | — | 290 → 258 | 262 → 246 |

**Delta ZERO** (por identidade física) em: `COVERAGE_GAP_IN_ROW`,
`COVERAGE_MISSING_ROW`, `COVERAGE_ROW_MOSTLY_EMPTY`, `POSITION_OVERLAP`,
`JUNCTION_MISSING_BINDING`, `JUNCTION_HALF_BLOCK_ADJACENT` e todos os
`OPENING_*`. Ou seja: **sem perda de cobertura, sem colisão nova, sem
regressão de amarração em nenhum outro nó, sem defeito novo de abertura.**

### Controle `IN_R × STATE_R` (topologia ANTIGA)

| projeto | efeito |
|---|---|
| TGD | `JUNCTION_NOT_ALTERNATING` 16 → **0**; `PRISM_CONTINUOUS_JOINT` 314 → 298; `PRISM_STAGGER_BELOW_TARGET` +16; `PRISM_JOINT_STACK` −1 |
| TP1 | **nenhum achado mudou** |

O ganho do TGD aqui é o nó pré-existente `(163,51 ; 237,05)` — a mesma
causa-raiz, exposta também na topologia antiga.

### Leitura honesta dos trade-offs

- **Não declarar sucesso pelo saldo crítico.** `JUNCTION_NOT_ALTERNATING`
  é `major` e **não entra** em `critical_errors` (`scoring.py:75` conta
  por severidade). A queda de `critical_errors` vem inteiramente de
  `PRISM_CONTINUOUS_JOINT`/`PRISM_JOINT_STACK`; o ganho de amarração é
  invisível ali. Os dois são reportados separadamente acima, de propósito.
- **`PRISM_STAGGER_BELOW_TARGET` +32/+16 não é problema novo: é o MESMO
  problema, uma severidade abaixo.** Medido por parede: TGD `W071` −16 e
  `W073` −16 em `PRISM_CONTINUOUS_JOINT` contra `W071` +16 e `W073` +16 em
  `PRISM_STAGGER_BELOW_TARGET`; TP1 `W071` −16 contra `W071` +16. As
  juntas não sumiram — deixaram de ser **coincidentes** (critical) e
  passaram a ser **desencontradas abaixo do alvo** (minor), nas mesmas
  paredes e nas mesmas fiadas. A coordenada exata muda porque a junta
  MUDOU DE LUGAR, que é justamente o efeito desejado.
- **`COMPENSATOR_CONSECUTIVE` +8 e `COMPENSATOR_EXCESS_IN_RUN` +8 são
  custo REAL, e localizado.** 100% deles caem na parede `W065` — a parede
  N-S que voltou a receber a peça de amarração em 8 das 17 fiadas — a
  poucos centímetros do próprio nó (TGD `(338;220)` e `(338;180)`; TP1
  `(8018;1322)` e `(8018;1282)`) — conferido por parede nos dois projetos:
  `{'W065': 8}` em cada um dos dois códigos, e nada em nenhuma outra
  parede. É a composição do trecho que sobra na
  fiada recém-devolvida àquela parede. **Não foi escondido, não foi
  compensado com nada e não justifica o ganho de amarração** — fica
  registrado como dívida (§7).
- **Não confundir com outras CRs.** Nada aqui é ganho de `CROSS_JAMB` da
  CR-A (`OPENING_BLOCK_CROSSES_JAMB` tem delta zero) nem correção de
  `expected_rows` da CR-C1 (não tocada). Nenhuma contagem foi comparada
  entre topologias diferentes: `A→B` e `C→D` são cada um um par com a
  MESMA entrada e o MESMO gabarito, só o solver muda.

---

## 6. Testes

`tests/test_solver_l_node_alternation_cr_s1.py` — **16 casos**.

Prova de causalidade, executada nas duas árvores:

| árvore | resultado |
|---|---|
| `origin/main` `91258dd` (**sem** o patch) | **7 falham**, 9 passam |
| esta branch (**com** o patch) | **16 passam** |

Os 7 que falham pré-fix são exatamente os que descrevem o defeito e o
mecanismo novo: o nó do TGD, o nó do TP1, as três ordens de entrada, a
convenção de fiada por tipo de nó e o gate de dois alcances.

Cobertura dos testes:

- o nó **real do TP1** e a **geometria equivalente do TGD**, com as
  coordenadas absolutas que a entrada reconstruída da CR-B entrega ao
  solver, nas **17 fiadas** e nos **16 pares consecutivos**;
- ausência de colisão por fiada física (`validate_same_course_collision`);
- mesmo resultado físico nos dois níveis, papel por papel;
- **invariância à ordem de entrada** das paredes (3 permutações);
- **inversão de orientação** do encontro (T espelhado para o outro lado);
- **determinismo** (3 execuções);
- **controles**: T a 20cm continua girando (sem colisão), L isolado
  continua alternando, T e X isolados não mudam de papel;
- o predicado booleano do gate antigo é bit a bit o mesmo (50cm bloqueia,
  70cm não).

### Suíte completa

`python3 -m pytest tests/ -q` (inclui os `slow`), nesta branch:

```
2 failed, 882 passed in 1853.71s (0:30:53)
```

As **2 falhas são PRÉ-EXISTENTES na `main`**, não desta CR — e isso foi
provado diretamente, não presumido. As duas são
`tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_
contra_o_baseline` (TGD e TP1). Rodando a MESMA comparação
(`runner.run_project(write_files=False)` + `scoring.compare_runs`, sem
gravar nada) nas duas árvores, o resultado é **linha por linha idêntico**:

| projeto | veredito | linha que reprova | `origin/main` `91258dd` | esta branch |
|---|---|---|---|---|
| TGD | `REGRESSAO` | categoria `compensators` 52 → 61 (+9) | igual | igual |
| TP1 | `REGRESSAO CRITICA` | `JUNCTION_MISSING_BINDING` 8 → 9 (+1) | igual | igual |

Todas as demais linhas dos dois vereditos (`COVERAGE_*`, `POSITION_
OVERLAP`, `OPENING_*`, `PRISM_CONTINUOUS_JOINT`, `junctions`,
`block_positions`, `openings`, `prism`, `wall_coverage`) também batem
exatamente entre as duas árvores. O `JUNCTION_MISSING_BINDING` 8 → 9 do
TP1 vem da CR-V1 (`PR #24`, já mesclada), que mudou a **unidade de
avaliação** do validador sem regravar o `baseline.json` congelado — dívida
já registrada, e **não** um efeito da CR-S1 (que mede
`JUNCTION_MISSING_BINDING` 9 → 9 no corpus oficial, delta zero).

**Nenhum baseline foi regravado, nenhum `--save-baseline` foi usado,
nenhum teste foi marcado `skip`/`xfail` e nenhum threshold foi alterado
para obter verde.**

### Determinismo no corpus

Solver de produção sobre `input_candidate.json`, **3 processos novos e
independentes** por projeto, `sha256` do resultado completo:

```
torre_easy_lo_r00_tgd   43e3633ebf229bb6efe47dccd9358bc9912029257a922378a3891c4ac49f608c  (x3)
torre_easy_lo_r00_tp1   80399696cfa1e4e1275457fbd16ae2a1ca07b669a586eca3fef36cb18b7e478b  (x3)
```

Idêntico byte a byte. Além disso o próprio patch não introduz nenhuma
fonte de ordem nova: `_corner_bond_blocking_courses` acumula um
**conjunto** de fiadas (união, independente da ordem de varredura) e
`_node_bond_courses_on_wall` lê só o tipo do nó e índices de parede que já
existiam.

---

## 7. Regressões e dívidas — o que NÃO foi resolvido

- **`COMPENSATOR_CONSECUTIVE` +8 e `COMPENSATOR_EXCESS_IN_RUN` +8 por
  projeto** (major), 100% em `W065`, ao lado do nó corrigido. Custo real
  do patch, não compensado. Resolver isso é composição de pilarete, não
  amarração — CR separada.
- **`JUNCTION_NOT_ALTERNATING` = 303 no TGD `IN_OFICIAL × STATE_A`**,
  inalterado (303 → 303). É dívida pré-existente de outra natureza (o
  `input.json` oficial do TGD ainda produz 11731 blocos contra 19433 da
  entrada reconstruída — a CR-A não foi propagada para o gabarito).
  **Fora do escopo da CR-S1.**
- **`POSITION_OVERLAP` 29/18/9** e **`JUNCTION_MISSING_BINDING` 23/9**
  continuam exatamente como estavam: falhas pré-existentes, não tocadas.
- A escolha do humano de fechar a fiada ímpar deste nó com **B19** não foi
  reproduzida (seção 35 proíbe B19 como amarração). Se o usuário quiser
  que o solver possa usar B19 ali, é **decisão normativa nova** — não foi
  tomada nesta CR.

---

## 8. Preservação

- `nuvem/benchmark/projects/**` — **intocado** (`git status` limpo).
- `baseline.json`, `reference.json`, `reference_score.json`,
  `input.json` — **intocados**. Nenhum `--save-baseline`.
- `nuvem/benchmark/validators/validate_junctions.py` — **intocado** (a CR
  não mexe no validador para "passar").
- Extrator/gerador do candidato da CR-B — **intocado**, rodado de
  *worktree* isolada.
- Nenhum teste marcado `skip`/`xfail`, nenhum threshold alterado.
- Regras normativas de X/T/L, B54/B34, amarração em duas fiadas e as
  restrições de B19 da seção 35 — **preservadas**. A seção 36 nova de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md` documenta o giro (que nunca tinha
  sido registrado) e a precedência da troca sobre o giro; não cria regra
  de domínio nova.

## 9. Veredito

**PRONTO PARA REVISÃO INDEPENDENTE — NÃO MESCLADO.**

O que está provado:

- o defeito reproduz nos 2 projetos contra a `main` `91258dd`, e some nos
  2 com o patch (`repro_solver_l_node_alternation.py`: `2 de 2` → `0 de 2`);
- a causa-raiz é um defeito de **implementação dentro do contrato
  existente** (informação de fiada descartada num `bool`), não uma decisão
  normativa faltando — por isso a CR não parou para pedir decisão;
- alternância física restaurada nas 17 fiadas e nos 16 pares consecutivos,
  nos dois níveis, com **zero colisão nova**, **zero perda de cobertura**,
  **zero regressão de amarração em outros nós** e **zero defeito novo de
  abertura**, medido por identidade física;
- **delta ZERO** no corpus oficial de hoje (`main` A → B);
- determinismo idêntico (3 processos, sha256);
- 16 testes novos, 7 dos quais falham comprovadamente contra a `main`;
- as 2 falhas da suíte completa são **pré-existentes e idênticas** na
  `main`, provadas por comparação lado a lado.

O que **não** está resolvido e precisa de decisão do usuário: o custo de
`COMPENSATOR_CONSECUTIVE` +8 / `COMPENSATOR_EXCESS_IN_RUN` +8 por projeto
em `W065` (§7), e a questão normativa do **B19 como peça de amarração**,
que é o que o humano usa neste nó e o solver (corretamente, pela seção 35)
não usa.

**Não marcar `ready` e não mesclar sem autorização específica. Nenhum
monitoramento automático foi criado.**
