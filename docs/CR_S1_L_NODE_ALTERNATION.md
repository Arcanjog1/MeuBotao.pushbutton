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
  custo REAL, localizado, e são O MESMO defeito físico contado duas
  vezes.** 100% deles caem na parede **N-S do próprio nó** — eixo
  `[338,523;180,048] → [338,523;824,048]` (TGD) e
  `[8017,26;1282,95] → [8017,26;1926,95]` (TP1) — que voltou a receber a
  peça de amarração em 8 das 17 fiadas. Investigação completa,
  aritmética exaustiva e alternativas: **§9**.
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

As **2 falhas são PRÉ-EXISTENTES na `main`**, não desta CR. Duas provas
independentes, nenhuma presumida.

**Prova 1 (a definitiva) — os próprios testes, na base limpa.** *Worktree*
novo em `91258dd`, **sem o patch**, rodando SÓ o arquivo que falha:

```
$ git worktree add <tmp> 91258dd
$ cd <tmp> && python3 -m pytest tests/regression/test_benchmark_baselines.py -q -rf

E   AssertionError: REGRESSAO CRITICA em torre_easy_lo_r00_tp1:
E     [{'code': 'JUNCTION_MISSING_BINDING', 'before': 8, 'after': 9,
E       'delta': 1, 'status': 'REGRESSAO CRITICA'}]

FAILED ...::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]
FAILED ...::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]
2 failed, 7 passed in 375.47s (0:06:15)
```

**Os mesmos dois testes, a mesma asserção, a mesma linha — na base, sem
uma linha desta CR.** (A suíte completa de ~30min não foi repetida só
para isto, por não acrescentar informação.)

**Prova 2 (corroboração) — a comparação de benchmark.** Rodando a MESMA
comparação que o teste faz (`runner.run_project(write_files=False)` +
`scoring.compare_runs`, sem gravar nada) nas duas árvores, o resultado é
**linha por linha idêntico**:

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
  projeto** (major) na parede N-S do nó. **Investigado até o fim (§9):
  são 8 eventos físicos, não 16; a causa é aritmética (sobra de 14cm sem
  peça única no catálogo) e o solver já escolhe o mínimo possível (2
  compensadores).** Não existe correção dentro do contrato atual —
  removê-los exige decisão normativa (revogar a seção 35 para permitir
  `B19` como amarração, ou mudar a convenção de fiada do `T`). **Fica
  pendente de decisão do usuário, não de código.**
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


---

## 9. A regressão localizada de compensadores — investigada até o fim

> Investigação pedida depois da primeira entrega. **Conclusão: não é um
> defeito do solver e não existe solução dentro do contrato atual.** O
> custo é aritmético e forçado. Nenhuma linha de código foi alterada por
> esta investigação.

### 9.1 Identidade física (o rótulo `W065` NÃO é identidade)

O `id` `W0xx` é derivado do **índice** da parede no estado exportado, e
aponta para paredes **diferentes** em cada estado — conferido:

| estado | `W065` é o eixo |
|---|---|
| `IN_OFICIAL` TGD | `[1296,016;−18,976] → [1280,322;−20,008]` |
| `IN_R` TGD | `[718,513;335,048] → [718,513;464,048]` |
| `IN_C` TGD | `[338,523;180,048] → [338,523;824,048]` ← esta |
| `IN_C` TP1 | `[8017,26;1282,95] → [8017,26;1926,95]` ← esta |

A parede desta seção é sempre a **N-S do nó da CR-S1**: 644cm, esp. 14cm,
17 fiadas, começando **no próprio nó** (t=0). A menção a `W065` na §5
vale só dentro do estado `IN_C`; corrigido aqui.

### 9.2 O que muda, bloco a bloco

**Fiada PAR (0, 2, …, 16) — byte a byte IDÊNTICA pré e pós:**

```
B34[15,0–49,0]  STANDARD_FILL
B34[50,0–84,0]  T_INTERSECTION_DEGRADED_L   <- a peca do T vizinho (t=57)
B39[85,0–124,0] STANDARD_FILL ...
```

**Fiada ÍMPAR (1, 3, …, 15) — a única que muda:**

```
PRE   B34[15,0–49,0] STANDARD_FILL           B39[65,0–104,0] ...
POS   B34[ 0,0–34,0] L_CORNER / L_binding    <- a peca de amarracao da CR-S1
      C04[35,0–39,0] STANDARD_FILL
      C09[40,0–49,0] STANDARD_FILL           B39[65,0–104,0] ...
```

Fiadas atingidas e **cotas físicas**: TGD 21 / 61 / 101 / 141 / 181 / 221
/ 261 / 301 cm; TP1 633 / 673 / 713 / 753 / 793 / 833 / 873 / 913 cm.
Oito fiadas por projeto, nos dois níveis, no mesmo ponto físico.

### 9.3 Os dois achados são O MESMO defeito físico

Comparando os **ids dos blocos** que cada achado cita:

| | TGD | TP1 |
|---|---|---|
| `COMPENSATOR_CONSECUTIVE` novos | 8 (16 blocos citados) | 8 (16 blocos) |
| `COMPENSATOR_EXCESS_IN_RUN` novos | 8 (16 blocos citados) | 8 (16 blocos) |
| conjuntos de blocos **iguais**? | **sim** (interseção 16) | **sim** (interseção 16) |

São **8 eventos físicos por projeto**, não 16: o mesmo par `C04`+`C09`
dispara `COMPENSATOR_CONSECUTIVE` (por estarem encostados) **e**
`COMPENSATOR_EXCESS_IN_RUN` (por serem 2 num trecho com teto
`MAX_COMPENSATORS_PER_TRECHO = 1`). O total de 16 achados por projeto é
contagem por critério, não por defeito.

### 9.4 Qual etapa introduz a sequência

Pelos próprios campos do resultado: o `B34[0–34]` tem
`placement_reason = "L_CORNER"` e `role = "L_binding"` — é a peça da
CR-S1, posta pelo solver de encontros. O `C04` e o `C09` têm
`placement_reason = "STANDARD_FILL"` e `role = "compensator"` — vêm do
**preenchimento comum** do trecho residual, depois que o candidato de nó
já ocupou o começo da parede. Não é o solver de L/T/X que escolhe os
compensadores.

### 9.5 A relação causal, e por que o custo é aritmético

O trecho da fiada ímpar é delimitado fisicamente dos **dois** lados:

- à esquerda, **t = 0**: o próprio nó (a peça de amarração de um L
  encosta no nó, por definição — não pode começar depois);
- à direita, **t ≈ 50**: a reserva do **T vizinho** a 57cm. Na fiada
  ímpar a peça daquele T está na parede que chega, mas o **corpo** dela
  (14cm de largura) atravessa esta parede em `[50, 64]`. Confirmado: na
  fiada PAR existe peça começando exatamente em `t = 50`.

Logo o trecho útil é de **49cm**. Com a peça de amarração B34 obrigatória
em `t = 0`: `49 − 34 − 1 (junta) = **14cm** de sobra`.

**Enumeração exaustiva** do catálogo do solver (`B39` 39, `B34` 34, `B19`
19, `C09` 9, `C04` 4; junta de 1cm), todas as composições **exatas** de
14cm:

| composição | compensadores |
|---|---|
| `C04 + C09` | **2** ← o que o solver escolhe |
| `C04 + C04 + C04` | 3 |

**Não existe composição com 1 ou 0 compensadores** — nenhuma peça do
catálogo fecha 14cm sozinha, e `B19` (19cm) não cabe. **O solver já
escolhe o mínimo possível.**

E o contraste que fecha a causalidade: **sem** peça de amarração no nó (o
que a `main` fazia ao girar), o trecho útil era de **34cm a partir de
t = 15** — que fecha exato com **um B34, zero compensadores**. Era esse o
"lucro" contábil do giro: ele comprava composição limpa **ao preço da
amarração**.

### 9.6 O `repair_b19_residual_fill` (seção 35) não se aplica

Verificado no código, não presumido: `_b19_residual_span_cm(length_cm)`
é `length_cm − 34`, ou seja, o residual da **parede inteira**
(644 − 34 = 610cm), muito fora da faixa `[15, 20]` da seção 35. O
mecanismo não olha trecho interno, e mesmo se olhasse um `B19` (19cm) não
cabe nos 14cm. **Nenhum mecanismo já aprovado fecha este trecho melhor.**

### 9.7 O que o humano faz — e por que o solver não pode copiar

Gabarito, mesma parede física, fiada ímpar:

```
B19[0,0–19,0]   C09[20,0–29,0]   B54[30,0–84,0]   B34[85,0–119,0] ...
```

O humano gasta **1** compensador, não 2 — mas com **duas** escolhas que o
contrato atual do solver não permite:

1. **`B19` como peça de amarração do canto** (19cm no nó) — proibido pela
   **seção 35** (`B19` nunca é amarração);
2. o **`B54` do T centrado em `t = 57`** na fiada **ÍMPAR** — o solver fixa
   a peça principal do T na **Fiada A** (par), convenção de
   `solve_t_intersection`.

Com `B19` no nó a sobra vira 29cm, e aí `B19 + C09` fecha com **1**
compensador. Sem `B19` no nó, 2 é o piso. **O humano não tem uma
composição melhor com `B34`** — ele tem uma peça de amarração diferente.

### 9.8 Alternativas, com custo medido — para decisão humana

Nenhuma foi implementada.

| # | alternativa | efeito nos compensadores | efeito na amarração | exige mudança normativa? |
|---|---|---|---|---|
| **A** | **manter como está** (o patch atual) | +8 eventos / +16 achados `major` por projeto | `JUNCTION_NOT_ALTERNATING` **32→0** (TGD) e **16→0** (TP1) | **não** |
| B | `B19` como peça de amarração do canto em L | volta a **0** achados novos (sobra 29cm = `B19+C09`, 1 compensador ⇒ nem `CONSECUTIVE` nem `EXCESS`) | preservada | **sim** — revoga a seção 35 |
| C | voltar a girar (comportamento da `main`) | **0** achados novos | **perde a alternância** — é o defeito que a CR-S1 corrige | não, mas anula a CR |
| D | deixar os 14cm vazios | **0** achados novos | preservada | não — mas troca 8 `COMPENSATOR_*` (`major`) por 8 `COVERAGE_GAP_IN_ROW` (`major`) e abre buraco real na alvenaria |
| E | pôr o `B54` do T na fiada ímpar (como o humano) | provavelmente 0, **não medido** | preservada | **sim** — muda a convenção de fiada de `solve_t_intersection`, com efeito em **todo** T do corpus |

**Recomendação:** manter **A**. É a única que não exige decisão normativa
nova e a única que não desfaz a correção de amarração. B e E são
decisões do usuário; C anula a CR; D piora fisicamente.

### 9.9 Margem para um achado adicional — declarada, não escondida

Os compensadores novos ficam em `t` centrado em **37,0** (`C04`) e
**44,5** (`C09`), em **8 de 17** fiadas. `COMPENSATOR_VERTICAL_STRIP`
exige `BOND_STRIP_MIN_COURSES = 3` **e** razão `≥ 0,50`; aqui a razão é
`8/17 = 0,47`, e a distância entre os dois centros (7,5cm) é maior que
`BOND_STRIP_CLUSTER_TOLERANCE_CM = 6,0`, então são dois agrupamentos
separados de 8 fiadas cada. **Medido: `COMPENSATOR_VERTICAL_STRIP` fica
2 → 2, sem delta.** Mas a margem é de **uma fiada**: numa parede com
número diferente de fiadas o mesmo padrão passaria do limiar. Fica
registrado.

### 9.10 Comparação exigida entre estados

| estado | efeito da CR-S1 nos compensadores |
|---|---|
| `main` sem patch × `main` com patch (corpus oficial) | **delta ZERO em todos os códigos** — o nó T→L não existe no `input.json` oficial |
| candidato CR-B sem patch × com patch | `COMPENSATOR_CONSECUTIVE` +8, `COMPENSATOR_EXCESS_IN_RUN` +8 (TGD e TP1) = os 8 eventos desta seção |
| `IN_R` (topologia antiga) sem × com patch | `COMPENSATOR_CONSECUTIVE` e `EXCESS_IN_RUN` **delta ZERO**; só `COMPENSATOR_AVOIDABLE` +1 (TGD, em `W073`) |

**Nada aqui é atribuível a defeito pré-existente e nada pré-existente é
atribuído ao patch.** Na mesma parede física, `COMPENSATOR_EXCESS_IN_RUN`
já era **9** antes do patch (uma por fiada PAR, por causa dos dois `C09`
em `t=165` e `t=310` — intocados) e passa a **17**; os 8 novos são
exclusivamente das fiadas ímpares. `COMPENSATOR_VERTICAL_STRIP` (2) e
`COMPENSATOR_AVOIDABLE` (1) nesta parede ficam com **delta zero em número
de achados** — o detalhe do `AVOIDABLE` muda de "42 compensadores contra
6 do humano" para "58", refletindo os 16 blocos novos (8 fiadas × 2).

### 9.11 Veredito da investigação

**Não há patch adicional.** A regressão é **local, entendida, mínima e
forçada pela aritmética do catálogo**: 14cm não fecham com menos de dois
compensadores. Corrigi-la exige uma **decisão normativa** (alternativa B
ou E), que não foi tomada nem inventada. O código da CR-S1 permanece
exatamente como estava em `98ae935`.

---

## 10. Veredito

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
- as 2 falhas da suíte completa são **pré-existentes**, agora provadas
  formalmente: os próprios testes falham, com a mesma asserção, num
  *worktree* limpo de `91258dd` sem o patch (§6);
- a regressão local de compensadores foi **investigada até o fim** (§9):
  8 eventos físicos, causa aritmética, solver já no mínimo — **nenhum
  patch adicional**, o código continua exatamente o de `98ae935`.

O que **não** está resolvido e precisa de decisão do usuário — agora
investigado até o fim e quantificado em **§9**: o custo de
`COMPENSATOR_CONSECUTIVE` +8 / `COMPENSATOR_EXCESS_IN_RUN` +8 por projeto
(8 eventos físicos) na parede N-S do nó. **Provado que não existe
composição melhor dentro do contrato**: a sobra é de 14cm e nenhuma peça
do catálogo a fecha sozinha. As duas saídas conhecidas — `B19` como peça
de amarração (revoga a seção 35) ou o `B54` do `T` na fiada ímpar (muda a
convenção de `solve_t_intersection` em todo o corpus) — são **decisões
normativas**, apresentadas em §9.8 com custo medido e **não
implementadas**.

**Não marcar `ready` e não mesclar sem autorização específica. Nenhum
monitoramento automático foi criado.**
