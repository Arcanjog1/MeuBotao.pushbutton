# CR-BLOCK-FIT-TOLERANCE-C04 — FIT_TOLERANCE_NOISE

> **STATUS: hard blocker RESOLVIDO — DRAFT, NÃO MERGEAR.** Ver
> "HARD BLOCKER RESOLUTION" e "Veredito". A primeira volta desta CR
> implementou a tolerância de fit de 0,30cm e mediu um efeito colateral
> estrutural real — `OPENING_BLOCK_CROSSES_JAMB` +41 (36 TGD + 5 TP1).
> A segunda volta (documentada abaixo) resolveu esse hard blocker com uma
> GUARDA FÍSICA DE FRONTEIRA, levando as 41 regressões novas a **ZERO** e
> preservando 98,4–100% do ganho de cobertura do C04. Aguarda revisão
> independente.

## Base

```
branch:  main (origin/main)
SHA:     3ebcd9b63875f9114a3d6223aa648e5075e2d35b
```

Confirmado por `git fetch origin main` + `git rev-parse origin/main` no
início desta sessão — bate exatamente com a base canônica exigida pela
CR (pós-PR #19, `CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION`).

## Branch

`claude/cr-block-fit-tolerance-c04-n5qsc4` (nome designado para esta
sessão; variante do nome sugerido `claude/cr-block-fit-tolerance-c04`).

## Causa-raiz (FIT_TOLERANCE_NOISE / C04)

O empacotador real de blocos (`_pier_ordered_layout`, via
`_pier_remaining_snapped_cm`, em `nuvem/core/engine/wall_stepper.py`)
decide se a SOBRA de um trecho — depois de descontar as juntas de
contorno — é um múltiplo (dentro de ruído) de `PIER_MODULE_CM` (5cm) e
portanto pode ser "snapada" para o módulo mais próximo. Antes desta CR
essa decisão usava `PIER_LAYOUT_TOLERANCE_CM` = 0,05cm (alias de
`MODULATION_WHOLE_CM_TOLERANCE_CM`) — suficiente para absorver o ruído de
arredondamento de **uma única** conversão pés↔cm, mas insuficiente para o
ruído **acumulado** de várias operações encadeadas (junção de encontro +
`extend_wall_ends_to_junctions`). Resultado: trechos geometricamente
válidos, a poucos décimos de milímetro/centímetro do múltiplo modular
esperado, eram rejeitados como "não fecha" e ficavam vazios
(`COVERAGE_GAP_IN_ROW`/`COVERAGE_MISSING_ROW`/`COVERAGE_PARTIAL_WALL`).

Varredura independente (0.05 / 0.10 / 0.15 / 0.20 / 0.25 / 0.30cm) sobre o
corpus de referência: TP1 satura o efeito em ~0,15cm; TGD só satura em
~0,30cm. **Valor aprovado para esta CR: 0,30cm.**

## Implementação

Produção limitada a 2 arquivos (ambos autorizados pela CR):

### `nuvem/core/engine/modulation_math.py`

1. Nova constante **dedicada** `PIER_FIT_TOLERANCE_CM = 0.30`, separada
   de `PIER_LAYOUT_TOLERANCE_CM`/`MODULATION_WHOLE_CM_TOLERANCE_CM` (que
   permanecem em 0,05cm, intocadas). Motivo da separação: essas duas
   constantes antigas são reusadas por MUITOS outros contratos que a CR
   proíbe alargar — a checagem de "SEM ESPAÇO FÍSICO"/colisão entre
   limites de trecho, a consistência de composição do DP de stagger
   (`_layout_matches_prism_target_dp`), e as tolerâncias de ADJACÊNCIA de
   compensador/meio-bloco (`BLOCK_JOINT_CM + PIER_LAYOUT_TOLERANCE_CM`,
   inclusive as herdadas em `wall_modeling.py` via
   `HALF_BLOCK_TIE_ADJACENCY_CM`/`COMPENSATOR_OPENING_ADJACENCY_
   TOLERANCE_CM`). Alargar a constante existente teria alargado todas
   essas tolerâncias não-relacionadas junto — exatamente o que a seção 5
   da CR proíbe ("não transformar 0,30cm em tolerância global").
2. `pier_closes_with_blocks_cm`/`wall_length_closes_with_blocks_cm` (a
   pré-checagem, com o MESMO contrato matemático do empacotador real —
   ver comentário original de `PIER_LAYOUT_TOLERANCE_CM`: "quem pré-checa
   e quem monta de verdade nunca podem discordar sobre o que fecha")
   passam a usar `PIER_FIT_TOLERANCE_CM` como tolerância default.
3. **Achado extra dos testes de borda (seção 7):** a fórmula antiga de
   `pier_closes_with_blocks_cm` comparava em "unidades" de
   `PIER_MODULE_CM` (dividindo antes de comparar). Com tolerância
   0,05cm isso nunca divergia por coincidência de arredondamento; com
   0,30cm, o valor EXATAMENTE no limite (`pier_cm == múltiplo ± 0,30`,
   ex.: `830.3`) discordava do empacotador real (que compara em cm) por
   ~2e-15 de erro de ponto flutuante introduzido pela divisão extra —
   violando a invariante documentada. Corrigido: a pré-checagem agora usa
   a MESMA fórmula "snap-e-compara-em-cm" do empacotador real — as duas
   funções são literalmente a mesma conta agora, eliminando a classe
   inteira de divergência (não só o caso encontrado).

### `nuvem/core/engine/wall_stepper.py`

`_pier_remaining_snapped_cm` — o mecanismo REAL que decide se o resto de
um trecho é modular/snapável — passa a usar `PIER_FIT_TOLERANCE_CM` nas 3
comparações internas (limite inferior, trecho-vazio, e a checagem de
"está perto o bastante de um múltiplo de 5"). Esta é a ÚNICA função deste
arquivo alterada, e a alteração era necessária (não apenas preferível):
mudar só a constante compartilhada teria alargado, dentro do MESMO
arquivo, contratos explicitamente fora de escopo — a checagem de colisão
`SEM_ESPACO` (linha ~5326), a consistência de composição do DP de stagger
(linha ~3936/3950) e a tolerância de adjacência de compensador consecutivo
(linhas ~5810/6196, herdada por `HALF_BLOCK_TIE_ADJACENCY_CM`/
`COMPENSATOR_OPENING_ADJACENCY_TOLERANCE_CM` em `wall_modeling.py`).
Todas as demais ocorrências de `PIER_LAYOUT_TOLERANCE_CM` neste arquivo
foram deixadas INTOCADAS de propósito, incluindo dentro de
`_half_block_leading_layout` (tier-scoring do B19 — composição, fora de
escopo por seção 8).

### Diff de produção

```
nuvem/core/engine/modulation_math.py | 63 ++++++++++++++++++++++++++++++++----
nuvem/core/engine/wall_stepper.py    | 25 ++++++++++----
2 files changed, 76 insertions(+), 12 deletions(-)
```

Nenhum terceiro arquivo de produção tocado. Nenhuma outra tolerância
(junction/opening geometry/colisão/coordenada) alterada — confirmado por
testes dedicados (`TestConstantScope`, ver seção Testes abaixo).

## STATE_A (main pristina, antes da implementação)

Medido com `python3 nuvem/benchmark/runner.py --run <project_id>` sobre
`origin/main` intocado (mudanças de produção removidas via `git stash`
antes da medição, restauradas depois).

| métrica | TGD | TP1 | Piloto |
|---|---|---|---|
| walls | 167 | 96 | 12 |
| blocks | 10679 | 18417 | 772 |
| findings_total | 4954 | 4991 | 124 |
| critical_errors | 884 | 469 | 8 |
| PRISM_CONTINUOUS_JOINT | 320 | 256 | 0 |
| PRISM_STAGGER_BELOW_TARGET | 774 | 1370 | 14 |
| COVERAGE_GAP_IN_ROW | 1959 | 327 | 16 |
| COVERAGE_MISSING_ROW | 258 | 0 | 0 |
| COVERAGE_PARTIAL_WALL | 61 | 6 | 0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 112 | 18 | 8 |
| COMPENSATOR_CONSECUTIVE | 379 | 1443 | 36 |
| JUNCTION_MISSING_BINDING | 23 | **9** | 0 |
| OPENING_BLOCK_CROSSES_JAMB | 108 | 168 | 0 |
| OPENING_BLOCK_INSIDE_DOOR | 5 | 0 | 0 |
| POSITION_OVERLAP | 29 | 18 | 0 |

Todos os valores batem EXATAMENTE com os canônicos da CR (seção 2),
incluindo `JUNCTION_MISSING_BINDING=9` no TP1 (seção 13 — falha conhecida
`REAL_SOLVER_DEFECT`, fora do escopo desta CR, confirmada presente e
preservada intacta em STATE_B abaixo). Nenhuma condição de PARE.

## STATE_B_BLOCKED (só o fit de 0,30cm, ANTES da guarda física)

| métrica | TGD | TP1 | Piloto |
|---|---|---|---|
| walls | 167 | 96 | 12 |
| blocks | **11735** | **19572** | 772 |
| findings_total | 4973 | 5141 | 124 |
| critical_errors | 908 | 490 | 8 |
| PRISM_CONTINUOUS_JOINT | 336 | 290 | 0 |
| PRISM_STAGGER_BELOW_TARGET | 830 | 1506 | 14 |
| COVERAGE_GAP_IN_ROW | 1644 | 214 | 16 |
| COVERAGE_MISSING_ROW | 192 | 0 | 0 |
| COVERAGE_PARTIAL_WALL | 48 | 0 | 0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 150 | 0 | 8 |
| COMPENSATOR_CONSECUTIVE | 522 | 1480 | 36 |
| JUNCTION_MISSING_BINDING | 23 | 9 | 0 |
| OPENING_BLOCK_CROSSES_JAMB | **144** | **173** | 0 |
| OPENING_BLOCK_INSIDE_DOOR | 5 | 0 | 0 |
| POSITION_OVERLAP | 29 | 18 | 0 |

## Delta STATE_A → STATE_B_BLOCKED, por código, com classificação

Piloto: **delta zero em tudo** (mesmo `walls`/`blocks`/`findings_total`/
todos os códigos) — o corpus sintético não tem nenhum trecho no regime de
ruído que esta CR mira.

### TGD

| metric | STATE_A | STATE_B | delta | classification |
|---|---|---|---|---|
| blocks | 10679 | 11735 | **+1056** | IMPROVEMENT |
| COVERAGE_GAP_IN_ROW | 1959 | 1644 | **-315** | IMPROVEMENT |
| COVERAGE_MISSING_ROW | 258 | 192 | **-66** | IMPROVEMENT |
| COVERAGE_PARTIAL_WALL | 61 | 48 | **-13** | IMPROVEMENT |
| COVERAGE_ROW_MOSTLY_EMPTY | 112 | 150 | +38 | EXPECTED_EXPOSURE |
| COMPENSATOR_CONSECUTIVE | 379 | 522 | +143 | EXPECTED_EXPOSURE |
| COMPENSATOR_EXCESS_IN_RUN | 341 | 439 | +98 | EXPECTED_EXPOSURE |
| COMPENSATOR_VERTICAL_STRIP | 58 | 81 | +23 | EXPECTED_EXPOSURE |
| COMPENSATOR_AVOIDABLE | 37 | 39 | +2 | EXPECTED_EXPOSURE |
| PRISM_CONTINUOUS_JOINT | 320 | 336 | +16 | EXPECTED_EXPOSURE |
| PRISM_STAGGER_BELOW_TARGET | 774 | 830 | +56 | EXPECTED_EXPOSURE |
| PRISM_JOINT_STACK | 19 | 20 | +1 | EXPECTED_EXPOSURE |
| **OPENING_BLOCK_CROSSES_JAMB** | 108 | 144 | **+36 (genuíno)** | **REAL_REGRESSION** |
| JUNCTION_MISSING_BINDING | 23 | 23 | +0 | UNCHANGED |
| JUNCTION_NOT_ALTERNATING | 303 | 303 | +0 | UNCHANGED |
| OPENING_BLOCK_INSIDE_DOOR | 5 | 5 | +0 | UNCHANGED |
| OPENING_SOLID_BELOW_SILL_MISSING | 32 | 32 | +0 | UNCHANGED |
| POSITION_OVERLAP | 29 | 29 | +0 | UNCHANGED |

### TP1

| metric | STATE_A | STATE_B | delta | classification |
|---|---|---|---|---|
| blocks | 18417 | 19572 | **+1155** | IMPROVEMENT |
| COVERAGE_GAP_IN_ROW | 327 | 214 | **-113** | IMPROVEMENT |
| COVERAGE_PARTIAL_WALL | 6 | 0 | **-6** | IMPROVEMENT |
| COVERAGE_ROW_MOSTLY_EMPTY | 18 | 0 | **-18** | IMPROVEMENT |
| COMPENSATOR_CONSECUTIVE | 1443 | 1480 | +37 | EXPECTED_EXPOSURE |
| COMPENSATOR_EXCESS_IN_RUN | 1067 | 1135 | +68 | EXPECTED_EXPOSURE |
| COMPENSATOR_VERTICAL_STRIP | 186 | 190 | +4 | EXPECTED_EXPOSURE |
| COMPENSATOR_AVOIDABLE | 86 | 87 | +1 | EXPECTED_EXPOSURE |
| PRISM_CONTINUOUS_JOINT | 256 | 290 | +34 | EXPECTED_EXPOSURE |
| PRISM_STAGGER_BELOW_TARGET | 1370 | 1506 | +136 | EXPECTED_EXPOSURE |
| PRISM_JOINT_STACK | 16 | 18 | +2 | EXPECTED_EXPOSURE |
| **OPENING_BLOCK_CROSSES_JAMB** | 168 | 173 | **+5 (genuíno)** | **REAL_REGRESSION** |
| JUNCTION_MISSING_BINDING | 9 | 9 | +0 | UNCHANGED (seção 13) |
| JUNCTION_NOT_ALTERNATING | 0 | 0 | +0 | UNCHANGED |
| OPENING_BLOCK_INSIDE_DOOR | 0 | 0 | +0 | UNCHANGED |
| POSITION_OVERLAP | 18 | 18 | +0 | UNCHANGED |

Todos os deltas de `IMPROVEMENT` batem **exatamente** (até a unidade) com
a expectativa da ablação independente registrada na CR (seção 10):
`COVERAGE_GAP_IN_ROW` TGD -315/TP1 -113, `COVERAGE_PARTIAL_WALL` TGD
-13/TP1 -6, `COVERAGE_MISSING_ROW` TGD -66, `blocks` TGD +1056/TP1 +1155.
`COVERAGE_ROW_MOSTLY_EMPTY` TGD +38 também bate exatamente. (TP1
`COVERAGE_ROW_MOSTLY_EMPTY` foi -18, ou seja MELHOROU em vez do +38
esperado pela ablação para essa métrica isolada — investigado: TP1 tinha
18 fiadas "quase vazias" que a ablação independente também classificou
como iriam ficar mais cobertas o bastante para sair da categoria
"mostly empty" direto para bem cobertas, sem passar por um estado
intermediário; TGD tem trechos MAIORES onde o preenchimento parcial cria
NOVAS fiadas "mostly empty" que antes eram total vazias
(`COVERAGE_MISSING_ROW`) — os dois são o mesmo mecanismo, direção do
efeito depende da distribuição de tamanho de gap de cada projeto.)

## `OPENING_BLOCK_CROSSES_JAMB` — achado central da 1ª volta (hard blocker, RESOLVIDO na 2ª)

**41 novas ocorrências genuínas** (36 TGD + 5 TP1), identificadas por
`(wall, opening, row)` — chave estável contra a renumeração de IDs de
bloco que uma comparação ingênua por `block_id` confunde (ver nota
metodológica abaixo). Todas de magnitude pequena (0,12cm a 0,267cm) mas
**acima** da própria tolerância de ruído do validador
(`OVERLAP_TOLERANCE_CM = 0.1cm`, `nuvem/benchmark/model.py`) — ou seja,
são "erro crítico" pela definição já vigente do projeto, não um
falso-positivo de medição.

### Causa-raiz do efeito colateral

O mecanismo desta CR aceita um trecho como modular quando a sobra REAL
(`remaining`, calculada a partir da geometria bruta) está a até
`PIER_FIT_TOLERANCE_CM` (0,30cm) de um múltiplo de `PIER_MODULE_CM`
(5cm) — e então **usa o valor SNAPADO** (arredondado ao múltiplo) para
posicionar as peças, não o valor bruto. Quando o trecho real é
LIGEIRAMENTE MENOR que o múltiplo mais próximo (a diferença é absorvida
"para cima"), a peça final é colocada com o comprimento do múltiplo
inteiro — ultrapassando fisicamente o limite verdadeiro do trecho pela
diferença exata (até 0,30cm). Quando esse limite é uma junta de
amarração (parede/nó), o excesso é inofensivo (absorvido pela junta de
1cm). Quando esse limite é a JAMBA de uma abertura (junta zero, sem
folga), o excesso invade o vão livre.

Isto é **inerente** a qualquer tolerância de "fit" acima do piso de ruído
do validador de aberturas (0,1cm) — já existia em teoria com a tolerância
antiga (0,05cm), mas ficava sempre ABAIXO do piso de 0,1cm do validador,
logo nunca visível. Widening para 0,30cm torna o excesso máximo possível
(0,30cm) 3x maior que esse piso, tornando o efeito mensurável em ~2-3%
das aberturas dos dois projetos reais do corpus.

### Instâncias completas (TGD, chave wall/opening/row, `overlap_cm`)

```
W044/W044-O01: rows 9, 11                    overlap=0.242cm (C04)
W072/W072-O01: rows 7, 8, 9, 10, 11           overlap=0.242cm (C04/C09)
W075/W075-O01: rows 0..11 (12 fiadas)         overlap=0.243cm (B19)
W075/W075-O02: rows 0..11 (12 fiadas)         overlap=0.242cm (B19/C09)
W113/W113-O01: rows 7, 8, 9, 10, 11           overlap=0.267cm (C09)
```

### Instâncias completas (TP1)

```
W029/W029-O01: rows 1, 3, 5, 7, 9 (5 fiadas)  overlap=0.12cm (C09)
```

### Nota metodológica (evitando um falso-positivo)

Uma primeira comparação por `(wall, opening, row, block_id)` reportou
`W019` (TGD) como "nova" ocorrência — mas o achado é IDÊNTICO em STATE_A
e STATE_B (mesmo `overlap_cm=2.996/3.5`, mesma posição), só o `block_id`
mudou (`B001`→`B002`) porque um bloco NOVO foi inserido mais cedo na
mesma fiada (preenchendo um gap anterior), deslocando a numeração dos
blocos seguintes. Corrigido usando `(wall, opening, row)` como chave
estável — as 41 instâncias acima sobreviveram a essa correção; `W019`
não é uma regressão desta CR (já existia, idêntica, em STATE_A).

### Por que isto é HARD BLOCKER, não trade-off

A CR é explícita (seção 12): `OPENING_BLOCK_CROSSES_JAMB` é um dos
códigos que, se aumentar, exige `PARE`/`NEEDS_FIX` e "não aceite como
simples trade-off de tolerância sem prova física". A prova física está
acima: 41 instâncias reais, cada uma com posição/peça/sobreposição
identificadas, todas fisicamente inválidas pela própria definição do
projeto (bloco invadindo o vão livre de uma porta). Não é composição
(fora de escopo por seção 8) — é uma consequência geométrica direta do
próprio mecanismo de snap que esta CR implementa, então é
inequivocamente desta CR.

Nenhuma correção foi tentada dentro desta CR (ver seção 8: "não corrigir
composição" e seção 5: "não mudar tolerâncias de opening geometry") — o
caminho correto, descrito na seção 24, é reportar como `NEEDS_FIX` e
deixar a decisão (reduzir a tolerância? tratar o snap de forma
assimétrica perto de jambas? aceitar o risco?) para revisão humana.

## Testes unitários de borda (seção 7)

`tests/test_block_fit_tolerance_c04.py` — 55 testes, 3 classes:

- `TestConstantScope` (3): valor da constante (0,30cm), que ela é mais
  larga que `PIER_LAYOUT_TOLERANCE_CM` (0,05cm, inalterada), e que as
  tolerâncias DERIVADAS (`HALF_BLOCK_TIE_ADJACENCY_CM`,
  `COMPENSATOR_OPENING_ADJACENCY_TOLERANCE_CM`) NÃO vazaram o valor novo.
- `TestPierClosesWithBlocksTolerance` (28, com parametrize): dentro/no
  limite/fora da tolerância ao redor de vários múltiplos de 5 (5, 10, 15,
  20, 55, 100, 405, 830, 1000cm), incluindo os valores literais pedidos
  pela CR (5.00/5.05/.../5.35, 4.95/4.80/4.71/4.70/4.69 — generalizados
  para qualquer múltiplo via parametrize), positivo/negativo, e a prova
  de que ruído além da tolerância ANTIGA (0,05cm) agora fecha.
- `TestPierRemainingSnappedCm` (24): o MESMO conjunto de casos de borda,
  mas contra `_pier_remaining_snapped_cm` (o mecanismo real do
  empacotador, via `wall_stepper.py`/`load_script`/`revit_stubs`),
  incluindo ruído de ponto flutuante adversarial (o caso real medido,
  829,99791cm) e a invariante "pré-checagem nunca discorda do solver
  real" nos pontos onde o achado da seção anterior (formula em cm vs.
  unidades) foi corrigido.

```
python3 -m pytest tests/test_block_fit_tolerance_c04.py -q
======================== 55 passed in 0.21s ========================
```

Regressão do teste pré-existente mais próximo (`is_clean_cm`/`is_whole_cm`
não devem ter mudado — só `wall_length_closes_with_blocks_cm`/
`pier_closes_with_blocks_cm` mudaram):

```
python3 -m pytest nuvem/tests/test_modulation_broken_length.py -q
======================== 6 passed in 0.01s =========================
```

## Testes focados (seção 19, preservação de PR #17/#18/#19)

```
python3 -m pytest tests/test_block_b19_residual_fill_implementation.py \
  tests/test_block_arm_role_candidate_safety_contract.py \
  tests/test_block_arm_safe_repair_gate_fidelity.py \
  tests/test_block_node_fill_revalidation.py \
  tests/test_block_arm_role_prism_stagger.py -q
======================== 140 passed in 1664.53s (0:27:44) ========================
```

Confirma preservados sem regressão: `NODE_FILL_OPPOSITE_COURSE_ENABLED`,
`ARM_ROLE_SAFE_REPAIR_ENABLED`, `B19_RESIDUAL_FILL_REPAIR_ENABLED`,
convergência de ponto fixo do B19, Gate Fidelity, contrato
`arm_role_safe_repair=False`.

## Suíte completa (seção 19 / FASE 14)

```
python3 -m pytest tests -q
STATE_B_BLOCKED (1ª volta): 736 passed, 2 failed  (35:47)
STATE_C          (2ª volta): 797 passed, 2 failed  (44:03)
```

O salto de 736→797 é a suíte nova da guarda (`test_block_fit_tolerance_
c04_jamb_guard.py`). As 2 falhas são as MESMAS duas de sempre —
`tests/regression/test_benchmark_baselines.py`, o guard-rail que compara
contra o `baseline.json` **congelado por decisão da CR** (seção 20) — mas o
conteúdo delas mudou, e é isso que importa:

| projeto | STATE_B_BLOCKED | STATE_C |
|---|---|---|
| TGD | `REGRESSAO` categoria `compensators` 52→61 paredes | **igual** (`compensators` 52→61) |
| TP1 | `REGRESSAO CRITICA`: **`OPENING_BLOCK_CROSSES_JAMB` 168→173** + `JUNCTION_MISSING_BINDING` 8→9 | `REGRESSAO CRITICA`: **só** `JUNCTION_MISSING_BINDING` 8→9 |

Ou seja: o guard-rail independente do benchmark **confirma, por um caminho
totalmente separado da análise manual, que a regressão crítica de jamba
desapareceu**. O que resta é:

- `JUNCTION_MISSING_BINDING` 8→9 no TP1: **pré-existente**, não desta CR — o
  `baseline.json` gravou `8`, mas o valor real já era `9` em STATE_A
  (`REAL_SOLVER_DEFECT`, seção 13 da CR, explicitamente fora de escopo);
- categoria `compensators` no TGD: o `EXPECTED_EXPOSURE` documentado (mais
  paredes com achado de compensador nos trechos recém-preenchidos), que
  esta CR não deve corrigir (seção 8).

Nenhuma das duas é código crítico novo atribuível a esta CR, e nenhuma pode
ser "resolvida" aqui sem tocar em `baseline.json` — o que a CR proíbe.

Nota de rigor: a suíte completa rodou sobre o código de produção final; a
única alteração posterior ao disparo foi um bloco de docstring (pré-condição
de `_layout_fitted_to_physical_span`), sem efeito de comportamento. Os 12
testes do ramo `prefer_avoiding` foram adicionados depois e rodados à parte
(73 passed no arquivo da guarda).

## Validação humana

### TP1 W012

STATE_A: gap vazio de 361cm em `t=289..650cm` (fiada 0, e repetido nas
fiadas ímpares/pares ao longo da altura). STATE_B preenche com
`B39×9 + C04(610-614) + B19(630.1-649.1)`. Referência (humano) preenche o
MESMO vão com `B34+B34` (alternando, amarração-style) intercalados com
B39 — nenhum compensador, nenhum B19 solto. **Classificação:
DIFFERENT_VALID** — o trecho passa a ser fisicamente preenchido (o
objetivo da CR), mas a composição escolhida pelo solver (greedy tier tie
B39→B19-em-ponta-aberta→compensador) diverge do padrão de amarração
B34-alternado do humano. Isto é exatamente "correção de composição fora
de escopo" (seção 8) exposta pela nova cobertura — não uma regressão,
mas também não uma confirmação de qualidade igual à do humano. Nenhuma
sobreposição de jamba nesta amostra.

### TP1 W022

STATE_A: só 2 blocos no total na fiada 0 (`B19` 69.99-88.99, `B34`
89.97-123.97) — a maior parte da parede sem NENHUM bloco. STATE_B
adiciona `B39(15.09-54.09)`. Referência no MESMO ponto:
`B39(14.99-53.99)` — **código e posição idênticos** (delta de 0,1cm,
dentro do ruído). **Classificação: IMPROVEMENT_CONFIRMED_BY_HUMAN** para
este trecho específico. A CR alertava que W022 "pode passar a preencher
usando compensadores onde o humano usa B19" — não foi o que aconteceu
aqui: o novo trecho usa B39 (igual ao humano); o par B19+B34 pré-existente
(inalterado por esta CR) é que diverge estruturalmente do
B39(69.99-108.99) único do humano — mas essa divergência já existia em
STATE_A, não é introduzida por esta CR.

### TP1 W093

Mesmo padrão de W022 (gap grande, só 1 bloco em STATE_A). STATE_B
adiciona `B39(15.0-54.0)` — bate exatamente com a referência
(`B39 14.99-53.99`, **IMPROVEMENT_CONFIRMED_BY_HUMAN**) — mas TAMBÉM
adiciona `B19(69.9-88.9)` onde a referência usa `B39(69.99-108.99)` — a
composição prevista no alerta da CR realmente acontece aqui.
**Classificação: IMPROVEMENT_PHYSICAL_ONLY** (fisicamente válido, parte
bate com humano, parte usa B19 onde o humano preferiu B39 — sem B19 ser
estruturalmente necessário nesse ponto).

### TP1 W094 / W095

`W094` não teve NENHUM finding de cobertura alterado por esta CR (não
identificável como amostra relevante — pulado, conforme seção 14 permite
quando a parede "não for mais relevante"). `W095`: mesma geometria de
W012 (par espelhado) — mesma classificação, **DIFFERENT_VALID**.

## Amostra adicional (seção 15)

### TP1 (5 paredes)

| parede | STATE_A | STATE_B (novo) | Referência no mesmo trecho | classificação |
|---|---|---|---|---|
| W012 | gap 361cm vazio | B39×9+C04+B19 | B34/B34 alternado + B39 | DIFFERENT_VALID |
| W029 | só B54 | B19+B39×4 | B34/B34+B39/B39+B34/B34 | DIFFERENT_VALID |
| W040 | gap 156cm vazio | B34+B39×3 | B39×3+B34 (mesmo conjunto, ordem espelhada) | IMPROVEMENT_PHYSICAL_ONLY |
| W072 | gap 156cm vazio | B34+B39×3 | B39×3+B34 (idêntico a W040 — mesma geometria) | IMPROVEMENT_PHYSICAL_ONLY |
| W081 | só B54 | B19+B39×4 | B34/B34+B39/B39+B34/B34 (idêntico a W029) | DIFFERENT_VALID |

### TGD (5 paredes)

| parede | STATE_A | STATE_B (novo) | Referência | classificação |
|---|---|---|---|---|
| W014 | fiada 2 AUSENTE | B39×2+C09×2+C04 | B19+B34 (span bem menor, possível abertura ativa nessa fiada) | INCONCLUSIVE (span da referência não bate em extensão — precisa contexto de abertura por fiada que esta análise rápida não reconstituiu) |
| W002 | gap 45,8cm vazio | B39(90-129)+C04(130-134) | layout inteiro da fiada 0 diferente desde o início (offset 0 vs 15) | INCONCLUSIVE (possível diferença de convenção de início de fiada entre solver/gabarito nesta parede especificamente; sem sinal de defeito novo — não está na lista de jamb-crossing) |
| W044 | — | C04 novo (rows 9,11) | — | **QUALITY_REGRESSION** (jamb-crossing confirmado, overlap 0.242cm) |
| W075 | — | B19/C09 novos (rows 0-11, 2 aberturas) | — | **QUALITY_REGRESSION** (jamb-crossing confirmado, 24 instâncias, overlap 0.242-0.243cm — a PIOR amostra do corpus) |
| W113 | gap 9,7cm | C09(75-84) | fiada 7 ausente na referência (sem base de comparação) | **QUALITY_REGRESSION** (jamb-crossing confirmado, overlap 0.267cm) |

**Não declarado sucesso apenas porque a cobertura diminuiu** (pedido
explícito da seção 14): das 10 paredes amostradas (5+5), 3 confirmam
exatamente o padrão bom esperado pela CR (preenchimento físico necessário
igual ao do humano), 4 são fisicamente válidas mas com composição
diferente da do humano (trade-off de composição, fora de escopo), 3 são
confirmadamente `QUALITY_REGRESSION` (jamb-crossing, ligadas diretamente
ao achado central acima), e 2 ficaram `INCONCLUSIVE` por limitação do
método de comparação rápida usado (comparação ingênua por índice de
fiada, sem reconstituir o casamento completo `comparator.match_walls`
peça a peça) — não por ambiguidade do efeito da CR em si.

## Determinismo (seção 16)

`_pier_remaining_snapped_cm`/`pier_closes_with_blocks_cm` são aritmética
pura sobre floats já existentes no projeto — nenhum dicionário/set cuja
ordem de iteração dependa de hash de string foi introduzido. Medido
diretamente (reusando `nuvem/benchmark/diagnostics_block_audit/lib_audit.py`,
biblioteca de auditoria independente já existente no repo): TP1, solver
real, mesmo `input.json`, 3 processos Python novos:

| PYTHONHASHSEED | fingerprint (sha256, `lib_audit.project_fingerprint`) | piece_count |
|---|---|---|
| 0 | `0dfafa2b...f62c058` | 19572 |
| 1 | `0dfafa2b...f62c058` | 19572 |
| 42 | `0dfafa2b...f62c058` | 19572 |

**Idêntico byte a byte nos 3 seeds.** `piece_count` bate com `blocks` de
STATE_B (19572).

## Invariância (seção 17)

Mesma biblioteca, TP1, comparando `plain` contra 3 variações — e
comparando o MESMO conjunto de variações em STATE_A (pristina) para
separar `PRE_EXISTING` de `NEW_AFTER_C04`:

| variação | STATE_A fingerprint (pieces) | STATE_B fingerprint (pieces) | classificação |
|---|---|---|---|
| plain | `37d7eb14...` (18417) | `0dfafa2b...` (19572) | (base) |
| reversed (ordem de paredes invertida) | `bf13e7df...` (18349, Δ-68) | `2104187a...` (19496, Δ-76) | PRE_EXISTING |
| shuffle-42 | `59dbac3a...` (18467, Δ+50) | `773e8191...` (19617, Δ+45) | PRE_EXISTING |
| endpoint-reversal | `e5038e6b...` (18380, Δ-37) | `fb1a5d28...` (19534, Δ-38) | PRE_EXISTING |

A não-determinismo do grafo de paredes/pairing sob permutação/reversão já
é um problema conhecido e documentado (`docs/PROJECT_STATUS.md`,
"Determinismo global do wall graph — não determinístico antes e depois do
CR-BLOCK-01") — **pré-existente**, não relacionado a blocos. A magnitude
do desvio (Δ na casa de 40-76 peças, <0,5% do total) é da MESMA ORDEM em
STATE_A e STATE_B — esta CR **não piora nem introduz** nenhuma nova
dependência de ordem/sentido/permutação. Nenhum `NEW_AFTER_C04`
encontrado. Rotação/translação/espelho não testados diretamente (exigem
fixture geométrico dedicado, não disponível nesta sessão) — o raciocínio
acima (aritmética pura sobre comprimentos escalares, sem coordenadas)
implica que esses casos são equivalentes ao de reversão de endpoint já
testado.

## NODE-FILL / Gate Fidelity / B19 (seção 18)

Confirmados intactos pelos 140 testes focados (seção 19 acima, todos
`PASS`): `NODE_FILL_OPPOSITE_COURSE_ENABLED=True`,
`ARM_ROLE_SAFE_REPAIR_ENABLED=True`,
`B19_RESIDUAL_FILL_REPAIR_ENABLED=True`, convergência de ponto fixo do
B19, Gate Fidelity (compensador por `course_index`, crédito físico de
nó), contrato `arm_role_safe_repair=False`.

## Baseline / Reference

**Intocados**, conforme seção 20: `baseline.json`, `reference.json`,
`reference_score.json` de nenhum dos 3 projetos foram modificados.
`score.json`/`reports/*.txt` regenerados durante a medição foram
revertidos ao HEAD antes do commit (artefatos de execução, não produção).

## Riscos / defeitos remanescentes

1. ~~**`OPENING_BLOCK_CROSSES_JAMB` +41**~~ — **RESOLVIDO na 2ª volta**
   pela guarda física de fronteira (ver "HARD BLOCKER RESOLUTION"):
   delta A→C = **+0**, verificado por instância.
2. Composição sub-ótima em trechos recém-destravados (W012/W029/W081/
   W095 e análogos) — solver usa compensador/B19 onde o humano usa
   amarração B34 alternada. `EXPECTED_EXPOSURE`, fora de escopo (seção
   8), mas deixado registrado para um futuro CR de composição.
3. Aumento de `PRISM_*`/`COMPENSATOR_*` (ver tabelas de delta) —
   `EXPECTED_EXPOSURE`, mesma razão do item 2.
4. `JUNCTION_MISSING_BINDING=9` no TP1 (falha `REAL_SOLVER_DEFECT`,
   seção 13) — preservada intacta, não é desta CR, não corrigida aqui.
5. Duas amostras TGD (`W002`, `W014`) ficaram `INCONCLUSIVE` na validação
   humana rápida — comparação por índice de fiada não reconstituiu o
   casamento completo `comparator.match_walls`; não há indício de defeito
   novo nessas duas (nenhuma aparece na lista de jamb-crossing), só falta
   de confirmação positiva.

# HARD BLOCKER RESOLUTION — guarda física de fronteira

> Segunda volta desta CR (mesma branch, mesmo PR #20). `OLD_HEAD` =
> `03e6817a3dc89d3b8eb93b5d8eff31b287eac03a` (STATE_B_BLOCKED).

## Causa-raiz do CROSS_JAMB

O fit modular de 0,30cm decide se um trecho PODE ser considerado modular,
absorvendo o ruído geométrico acumulado. Mas o comprimento **snapado**
também é usado para POSICIONAR as peças: quando o trecho real é um pouco
MENOR que o múltiplo aceito, a última peça termina depois do fim físico do
trecho.

- Contra uma **junta de argamassa** (ponta que encosta em outro bloco/âncora)
  isso é inofensivo: a junta de 1cm cede a fração de milímetro.
- Contra uma fronteira **sem junta** — jamba de abertura, ponta livre de
  parede, reserva de nó — não há o que ceder: a peça invade o vão.

Medição: **100% das 41 invasões** eram `LEADING_JAMB` (a peça vem da
esquerda e ultrapassa o `t_start` do vão) e **100% tinham
`placement_reason = OPENING_REPAIR_FILL`** — o único caminho do solver que
assenta peças diretamente contra a coordenada real de uma jamba. O excesso
é sempre exatamente a parte fracionária da coordenada da jamba
(30,76→31,0 = 0,24; 83,73→84,0 = 0,27; 18,88→19,0 = 0,12).

## Inventário dos 41 casos

`(wall, opening, row)` — chave estável contra a renumeração de `block_id`
(uma comparação ingênua por id reporta `W019` como "novo", quando o achado
é idêntico em STATE_A e STATE_B_BLOCKED; ver "Nota metodológica").

| projeto | parede | abertura | tipo | fiadas | peça | overlap |
|---|---|---|---|---|---|---|
| TGD | W044 | W044-O01 | janela | 9, 11 | C04 | 0,242cm |
| TGD | W072 | W072-O01 | janela | 7–11 | C04/C09 | 0,242cm |
| TGD | W075 | W075-O01 | porta | 0–11 (12) | B19 | 0,243cm |
| TGD | W075 | W075-O02 | porta | 0–11 (12) | B19/C09 | 0,242cm |
| TGD | W113 | W113-O01 | janela | 7–11 | C09 | 0,267cm |
| TP1 | W029 | W029-O01 | porta | 1,3,5,7,9 | C09 | 0,120cm |

Total: 36 TGD + 5 TP1 = **41**. Todas acima do piso de ruído do próprio
validador (`OVERLAP_TOLERANCE_CM = 0,1cm`). Inventário completo
machine-readable (com `wall_key`, ângulo da parede, vão, layout da fiada
nos três estados e layout humano) gerado em
`c04_cross_jamb_inventory.json` durante a análise.

## Onde o delta pode ser absorvido (medido, não suposto)

Instrumentando `_solve_repair_subsegments` no corpus real (limiar 0,05cm):

| opção | TGD | TP1 | conclusão |
|---|---|---|---|
| A/B — deslocar para a esquerda (folga de argamassa nesse lado) | 207/828 | 0/124 | **insuficiente** |
| B — comprimir as juntas internas (≥1 junta) | 276/828 | 0/124 | **insuficiente** |
| E — reduzir para o maior conteúdo modular que cabe | 828/828 | 124/124 | **universal** |

A maioria dos casos é **peça única, sem folga de argamassa em nenhum lado**
(um B19 de 19,0cm num trecho de 18,757cm): nem deslocamento nem compressão
de junta fazem uma peça inteira caber num espaço menor que ela. Só a
redução funciona em 100% dos casos.

## Estratégias testadas (FASE 4)

### A — opening-aware physical guard
Adotada como o *predicado*: o fit continua 0,30cm; a materialização é que
passa a respeitar a fronteira física.

### B — absorver no lado não-abertura
Medida: aplicável a 207/828 (TGD) e 0/124 (TP1). Além de insuficiente,
exigiria comprimir junta de argamassa (desvio de regra de domínio) ou
deslocar a sequência para dentro de reserva de nó (risco de colisão).
**Descartada como solução geral.**

### C — shift mínimo do layout
Mesma limitação de B nos casos de peça única; não resolve
`19,0cm em 18,757cm`. **Descartada.**

### D — composição alternativa já legal
É exatamente o que a redução faz: o trecho é remontado com
`_pier_ordered_layout` para um módulo a menos — nenhuma regra nova.
**Incorporada em E.**

### E — reduzir/rejeitar localmente
**Escolhida.** Universal, sem regra de domínio nova, sem deslocar peça
nenhuma (nenhum risco de colisão), e a sobra deixada é sempre
`< PIER_MODULE_CM` por construção.

## Regra física escolhida

```
FIT / FEASIBILIDADE   PIER_FIT_TOLERANCE_CM       = 0,30cm
    "este trecho PODE ser considerado modular?"
COLOCAÇÃO FÍSICA      PIER_PHYSICAL_FIT_TOLERANCE_CM = 0,05cm
    "onde a peça PODE existir de fato?"
```

`PIER_PHYSICAL_FIT_TOLERANCE_CM` vale exatamente `PIER_LAYOUT_TOLERANCE_CM`
(0,05cm) **de propósito**: é o piso de ruído geométrico que o projeto já
usava antes desta CR para todo o resto. Amarrando a guarda nele, o C04 fica
**impossibilitado de materializar uma invasão maior do que o solver já
podia produzir antes dele** — a tolerância de fit mais larga muda o que
*fecha*, nunca o que *atravessa*. É deliberadamente **mais apertado** que o
piso do próprio validador (0,1cm): a guarda é física, não um ajuste para
caber na régua do validador.

O predicado de ativação é `sub["trailing_open"]` — "esta ponta de saída NÃO
tem junta de argamassa" —, puramente geométrico: vale para jamba de
abertura, ponta livre de parede e reserva de nó, e nunca depende de
id/nome de abertura, de parede, de família ou de paridade.

## Mudanças de produção (2ª volta)

Os MESMOS 2 arquivos já autorizados (nenhum terceiro arquivo de produção):

- `nuvem/core/engine/modulation_math.py`: `PIER_PHYSICAL_FIT_TOLERANCE_CM`
  e `pier_cm_floored_to_module` (aritmética pura: o maior conteúdo modular
  que cabe num trecho real).
- `nuvem/core/engine/wall_stepper.py`: `_layout_physical_end_cm` e
  `_layout_fitted_to_physical_span` (a guarda), aplicadas em
  `_solve_repair_subsegments` — o único caminho que assenta peças contra a
  coordenada real de uma jamba.

Quando nem o conteúdo reduzido cabe, a guarda devolve `None`: o trecho fica
vazio, exatamente como acontecia **antes** do C04 — melhor vazio que peça
dentro do vão.

## Testes adicionados

`tests/test_block_fit_tolerance_c04_jamb_guard.py` — **73 testes**, sobre
as funções de PRODUÇÃO e sobre o solver COMPLETO (nunca helper inventado):

- aritmética de `pier_cm_floored_to_module`, incluindo a prova de que a
  sobra deixada fica sempre em `[5 − 0,30; 5,00)`cm — abaixo do menor vazio
  reportável (`MIN_REPORTABLE_GAP_CM = 5,0`);
- as **6 geometrias reais medidas no corpus** (spans 23,757 / 18,757 /
  13,758 / 8,88 / 8,758 / 8,733), cada uma asserindo primeiro que o regime
  existe (sem guarda o conteúdo passaria do fim físico exatamente pela
  invasão medida) e depois que com a guarda cabe;
- âncora com argamassa mantém o snap do fit (a guarda não age onde há junta
  para ceder); trecho exatamente modular intocado; comportamento definido
  no limite do fit; fora do fit não snapa; abertura na ponta de entrada; duas
  fronteiras de abertura; "quando nada cabe, o trecho fica vazio";
- **solver completo** (`solve_building_blocks_all_courses`) em parede
  horizontal, vertical, com reversão de ponta e em todas as fiadas, com
  offsets de jamba que reproduzem o regime C04;
- rede de segurança contra a guarda virar no-op: com ela desligada por
  `monkeypatch`, **o mesmo cenário volta a produzir peças dentro do vão**.

## STATE_A → STATE_B_BLOCKED → STATE_C

| metric | STATE_A | STATE_B_BLOCKED | STATE_C | Δ A→C | Δ B→C | classificação |
|---|---|---|---|---|---|---|
| **TGD** |||||||
| blocks | 10679 | 11735 | 11731 | **+1052** | -4 | IMPROVEMENT |
| COVERAGE_GAP_IN_ROW | 1959 | 1644 | 1649 | **-310** | +5 | IMPROVEMENT |
| COVERAGE_MISSING_ROW | 258 | 192 | 192 | **-66** | +0 | IMPROVEMENT |
| COVERAGE_PARTIAL_WALL | 61 | 48 | 48 | **-13** | +0 | IMPROVEMENT |
| COVERAGE_ROW_MOSTLY_EMPTY | 112 | 150 | 150 | +38 | +0 | EXPECTED_EXPOSURE |
| **OPENING_BLOCK_CROSSES_JAMB** | 108 | 144 | **108** | **+0** | **-36** | **RESOLVIDO** |
| POSITION_OVERLAP | 29 | 29 | 29 | +0 | +0 | UNCHANGED |
| JUNCTION_MISSING_BINDING | 23 | 23 | 23 | +0 | +0 | UNCHANGED |
| JUNCTION_NOT_ALTERNATING | 303 | 303 | 303 | +0 | +0 | UNCHANGED |
| OPENING_BLOCK_INSIDE_DOOR | 5 | 5 | 5 | +0 | +0 | UNCHANGED |
| OPENING_SOLID_BELOW_SILL_MISSING | 32 | 32 | 32 | +0 | +0 | UNCHANGED |
| OPENING_MISSING_LINTEL | 82 | 82 | 82 | +0 | +0 | UNCHANGED |
| COVERAGE_WALL_NOT_MODULATED | 29 | 29 | 29 | +0 | +0 | UNCHANGED |
| COMPENSATOR_CONSECUTIVE | 379 | 522 | 523 | +144 | +1 | EXPECTED_EXPOSURE |
| COMPENSATOR_EXCESS_IN_RUN | 341 | 439 | 440 | +99 | +1 | EXPECTED_EXPOSURE |
| COMPENSATOR_VERTICAL_STRIP | 58 | 81 | 81 | +23 | +0 | EXPECTED_EXPOSURE |
| COMPENSATOR_AVOIDABLE | 37 | 39 | 39 | +2 | +0 | EXPECTED_EXPOSURE |
| PRISM_CONTINUOUS_JOINT | 320 | 336 | 336 | +16 | +0 | EXPECTED_EXPOSURE |
| PRISM_STAGGER_BELOW_TARGET | 774 | 830 | 841 | +67 | +11 | EXPECTED_EXPOSURE |
| PRISM_JOINT_STACK | 19 | 20 | 20 | +1 | +0 | EXPECTED_EXPOSURE |
| critical_errors | 884 | 908 | **872** | **-12** | -36 | IMPROVEMENT |
| **TP1** |||||||
| blocks | 18417 | 19572 | 19572 | **+1155** | +0 | IMPROVEMENT |
| COVERAGE_GAP_IN_ROW | 327 | 214 | 214 | **-113** | +0 | IMPROVEMENT |
| COVERAGE_PARTIAL_WALL | 6 | 0 | 0 | **-6** | +0 | IMPROVEMENT |
| COVERAGE_ROW_MOSTLY_EMPTY | 18 | 0 | 0 | **-18** | +0 | IMPROVEMENT |
| **OPENING_BLOCK_CROSSES_JAMB** | 168 | 173 | **168** | **+0** | **-5** | **RESOLVIDO** |
| POSITION_OVERLAP | 18 | 18 | 18 | +0 | +0 | UNCHANGED |
| JUNCTION_MISSING_BINDING | **9** | 9 | **9** | +0 | +0 | UNCHANGED (seção 13) |
| COMPENSATOR_CONSECUTIVE | 1443 | 1480 | 1480 | +37 | +0 | EXPECTED_EXPOSURE |
| COMPENSATOR_EXCESS_IN_RUN | 1067 | 1135 | 1135 | +68 | +0 | EXPECTED_EXPOSURE |
| PRISM_CONTINUOUS_JOINT | 256 | 290 | 290 | +34 | +0 | EXPECTED_EXPOSURE |
| PRISM_STAGGER_BELOW_TARGET | 1370 | 1506 | 1506 | +136 | +0 | EXPECTED_EXPOSURE |
| critical_errors | 469 | 490 | 485 | +16 | -5 | EXPECTED_EXPOSURE |
| **PILOTO** | — | — | — | **delta ZERO em tudo** | — | UNCHANGED |

Os três estados foram pontuados com o MESMO contexto de referência
(`runner.evaluate_project` com o `reference.json` do projeto), para serem
comparáveis coluna a coluna.

## GATE PRINCIPAL — verificação por instância

Não basta a contagem bater: as instâncias foram comparadas uma a uma pela
chave `(wall, opening, row)`.

```
TGD    : A=108  C=108  |  NOVAS em C: 0  |  sumiram: 0
TP1    : A=168  C=168  |  NOVAS em C: 0  |  sumiram: 0
PILOTO : A=0    C=0    |  NOVAS em C: 0  |  sumiram: 0
```

**Novas ocorrências de `OPENING_BLOCK_CROSSES_JAMB` causadas pelo C04: ZERO.**

`POSITION_OVERLAP` também foi verificado por instância com chave geométrica
estável `(wall, row, overlap_cm)`: 29 = 29 em TGD, zero novas, zero
sumidas (uma primeira comparação usando o texto `detail` acusou "9 novas" —
artefato puro da renumeração de `block_id`, não uma mudança real).

## Retenção do ganho C04

| projeto | métrica | ganho B | ganho C | retido |
|---|---|---|---|---|
| TGD | COVERAGE_GAP_IN_ROW | -315 | -310 | **98,4%** |
| TGD | COVERAGE_MISSING_ROW | -66 | -66 | **100%** |
| TGD | COVERAGE_PARTIAL_WALL | -13 | -13 | **100%** |
| TGD | blocks | +1056 | +1052 | **99,6%** |
| TP1 | COVERAGE_GAP_IN_ROW | -113 | -113 | **100%** |
| TP1 | COVERAGE_PARTIAL_WALL | -6 | -6 | **100%** |
| TP1 | COVERAGE_ROW_MOSTLY_EMPTY | -18 | -18 | **100%** |
| TP1 | blocks | +1155 | +1155 | **100%** |

**`coverage_gain_retained_pct` = 98,4%–100%.**

### O custo exato (os 5 vazios novos, todos numa única posição)

Os 5 vazios `B→C` são a MESMA posição física em 5 fiadas de `W087` (TGD):
subsegmento `lo=85,242 / hi=94,0` (span 8,758), com `trailing_open=True` e
`right_opening=None` — ou seja, a fronteira **não é uma jamba, é a borda da
reserva de nó**. Sem a guarda, o C09 terminava em 94,242, **0,242cm dentro
da zona reservada do nó**; com a guarda, entra um C04 e sobra 4,758cm
(abaixo dos 5,0cm reportáveis) — o vazio de 5,8cm que aparece no relatório
soma essa sobra ao ~1,0cm entre `hi=94,0` e o início da zona de amarração
em 95,0, que já não era preenchível.

Ou seja: o custo medido de 5 vazios comprou a não-invasão de uma reserva de
nó em 5 fiadas. Restringir a guarda apenas a aberturas
(`right_opening is not None`) recuperaria esses 5 vazios e manteria 100% do
ganho, ao preço de deixar a invasão da reserva de nó de pé — **decisão
deixada explícita para a revisão independente**; a versão entregue escolhe
o predicado físico (mais conservador).

## Validação humana dos 41 casos (FASE 6)

O que o humano faz na MESMA jamba, medido no `reference.json`:

| caso | STATE_B_BLOCKED | STATE_C | humano | classificação |
|---|---|---|---|---|
| TP1 W029/O01 (jamba 18,88) | C09 10,0→**19,0** (invade 0,12) | C09 0→9 + C04 10→14 | **C04 14,88→18,88** (termina EXATO na jamba) | CONSISTENT_WITH_HUMAN |
| TGD W044/O01 (jamba 30,76) | C04 27→**31,0** (invade 0,24) | C09 7→16, C09 17→26 | B19 0→19 (não alcança a jamba) | CONSISTENT_WITH_HUMAN |
| TGD W072/O01 (jamba 33,76) | C09 25→**34,0** | C09 20→29 | B39_C 15→54 (composição totalmente outra) | DIFFERENT_VALID |
| TGD W075/O01 (jamba 33,76) | B19 15→**34,0** | C09 15→24 + C04 25→29 | C04 15→19 (não alcança a jamba) | CONSISTENT_WITH_HUMAN |
| TGD W075/O02 (jamba 318,76) | B19 300→**319,0** | C09 300→309 + C04 310→314 | vazio nessa faixa | DIFFERENT_VALID |
| TGD W113/O01 (jamba 83,73) | C09 75→**84,0** | C04 75→79 | fiada sem correspondência no gabarito | INCONCLUSIVE |

**Resposta às perguntas da FASE 6:** o humano usa **(C) mantém a jamba
exata** — em nenhuma das amostras uma peça humana entra no vão — e, quando
preenche até lá, usa **(D) absorve a diferença do outro lado**: no TP1
W029 o C04 humano começa em 14,88 (coordenada fracionária, ancorada NA
JAMBA) e termina exatamente em 18,88. Nunca desloca a abertura, nunca
"quase encosta".

O STATE_C é **consistente com o humano no invariante que importa** (a jamba
nunca é invadida) e difere no detalhe da ancoragem: a guarda mantém a peça
ancorada à esquerda e deixa a folga contra a jamba, enquanto o humano
ancora a peça na jamba. Ancorar na jamba encheria mais 5cm nesses trechos,
mas exige comprimir junta de argamassa — desvio de regra de domínio — e
**não resolveria** os casos de peça única maior que o vão (a maioria).
Registrado como candidato a um CR futuro de composição, com a evidência
humana acima.

## Revalidação humana C04 (FASE 10)

| parede | achados de cobertura A → C | CROSSES_JAMB A → C | classificação (2ª volta) |
|---|---|---|---|
| TP1 W012 | 35 → 34 | 0 → 0 | DIFFERENT_VALID (composição, fora de escopo) |
| TP1 W022 | 18 → **0** | 0 → 0 | IMPROVEMENT_CONFIRMED_BY_HUMAN |
| TP1 W093 | 35 → **0** | 0 → 0 | IMPROVEMENT_PHYSICAL_ONLY |
| TP1 W094 | 34 → 34 | 0 → 0 | não afetada pelo C04 |
| TP1 W095 | 35 → 34 | 0 → 0 | DIFFERENT_VALID |
| TP1 W029 | 24 → **0** | 0 → 0 | **QUALITY_REGRESSION → resolvida** |
| TP1 W040 | 22 → 4 | 0 → 0 | IMPROVEMENT_PHYSICAL_ONLY |
| TP1 W072 | 27 → 8 | 0 → 0 | IMPROVEMENT_PHYSICAL_ONLY |
| TP1 W081 | 21 → **0** | 0 → 0 | DIFFERENT_VALID |
| TGD W014 | 17 → **0** | 0 → 0 | INCONCLUSIVE (fiada com abertura ativa) |
| TGD W002 | 52 → 35 | 0 → 0 | DIFFERENT_VALID |
| TGD W044 | 17 → 15 | 0 → 0 | **QUALITY_REGRESSION → resolvida** |
| TGD W075 | 48 → **0** | 0 → 0 | **QUALITY_REGRESSION → resolvida** |
| TGD W113 | 7 → **0** | 0 → 0 | **QUALITY_REGRESSION → resolvida** |

**`QUALITY_REGRESSION` causada por CROSS_JAMB novo: ZERO.** As 4 paredes
que a carregavam mantêm o ganho de cobertura do C04 **e** deixaram de
invadir o vão.

## Determinismo (FASE 11)

TP1, solver real, processos Python novos, 4 seeds:

| PYTHONHASHSEED | fingerprint | peças |
|---|---|---|
| 0 | `204154ba…5115c67` | 19572 |
| 1 | `204154ba…5115c67` | 19572 |
| 42 | `204154ba…5115c67` | 19572 |
| 12345 | `204154ba…5115c67` | 19572 |

TGD (seeds 0 e 12345): `7a51cb39…f0d0`, 11731 peças, `non_modular` 2667 —
idênticos. Comparados também, e **idênticos entre seeds**:
`arm_role_safe_repair` = `{accepted: 1, rejected: 12}` e
`b19_residual_fill_repair` = `{accepted: 0, rejected: 16}` (TP1),
`non_modular` = 64.

## Invariância (FASE 12)

TP1, mesmas variações medidas em STATE_A e STATE_B_BLOCKED:

| variação | STATE_A (peças) | STATE_B_BLOCKED | STATE_C | classificação |
|---|---|---|---|---|
| plain | 18417 | 19572 | 19572 | (base) |
| reversed | 18349 (Δ-68) | 19496 (Δ-76) | 19496 (Δ-76) | PRE_EXISTING |
| shuffle-42 | 18467 (Δ+50) | 19617 (Δ+45) | 19617 (Δ+45) | PRE_EXISTING |
| endpoint-reversal | 18380 (Δ-37) | 19534 (Δ-38) | 19534 (Δ-38) | PRE_EXISTING |

Os deltas de STATE_C são **idênticos aos de STATE_B_BLOCKED** — a guarda
não introduz nenhuma dependência nova de ordem/sentido. O não-determinismo
do grafo de paredes sob permutação já é conhecido e documentado
(`docs/PROJECT_STATUS.md`), anterior a esta CR. Rotação/translação/espelho
não têm fixture dedicado no repo; a guarda é aritmética escalar sobre
comprimentos (nenhuma coordenada global entra nela), e reversão de ponta —
o caso que de fato espelha o eixo — está coberto tanto aqui quanto nos
testes permanentes. **`NEW_AFTER_C04`: nenhum.**

## Autoauditoria adversarial (FASE 15)

| # | pergunta | resposta / evidência |
|---|---|---|
| 1 | só esconde o validator? | Não. O limiar da guarda (0,05cm) é **mais apertado** que o piso do validador (0,1cm), e o que muda é a geometria materializada, não o relatório. |
| 2 | remove blocos necessários? | Reduz um módulo só onde a peça não cabe fisicamente: `blocks` TGD -4, TP1 ±0; cobertura retida 98,4–100%. |
| 3 | permite gap físico do outro lado? | A sobra é `< PIER_MODULE_CM` por construção (provado e testado). Único efeito reportável: 5 vazios em `W087`, dissecados acima. |
| 4 | move bloco para dentro de outro nó? | Não move peça nenhuma — só reduz conteúdo, mantendo a âncora esquerda. |
| 5 | causa overlap? | `POSITION_OVERLAP` idêntico por instância (29/18/0). |
| 6 | depende da orientação? | Testado horizontal, vertical e com reversão de ponta; invariância idêntica à pré-existente. |
| 7 | usa nome/id de abertura? | Não — o predicado é `trailing_open` (ausência de junta de argamassa). |
| 8 | trata só uma família/paridade? | Não há noção de letra/paridade na guarda; casos do corpus cobrem fiadas pares e ímpares, testes e2e cobrem todas as fiadas. |
| 9 | funciona só no TP1/TGD? | Cenários sintéticos (fora do corpus) reproduzem e validam; Piloto com delta zero. |
| 10 | quebra trecho sem abertura? | Não: com junta de argamassa na saída a guarda devolve o layout intacto (69 subsegmentos TGD com excesso até 0,242cm ficaram intocados). |
| 11 | altera regra de domínio? | Não: nenhuma peça nova, nenhuma junta comprimida, nenhum deslocamento; a composição reduzida é a que o próprio `_pier_ordered_layout` monta para um módulo a menos. |
| 12 | usa 0,30cm como tolerância física? | Não — é exatamente o defeito corrigido: FIT 0,30cm, FÍSICA 0,05cm. |

## Testes (2ª volta)

```
tests/test_block_fit_tolerance_c04_jamb_guard.py    73 passed
tests/test_block_fit_tolerance_c04.py + nuvem/tests/test_modulation_broken_length.py
                                                    61 passed
suíte focada (B19 + ARM contract + Gate Fidelity + NODE-FILL + prism stagger)
                                                   140 passed  (19:21)
suíte completa  python3 -m pytest tests -q        797 passed, 2 failed (44:03)
                (as 2 = guard-rail do baseline congelado; ver "Suíte completa")
```

## Veredito

**READY_FOR_INDEPENDENT_REVIEW** — DRAFT, NÃO MERGEAR.

Critérios da CR, um a um:

- [x] C04 continua usando tolerância de fit **dedicada** de 0,30cm
      (`PIER_FIT_TOLERANCE_CM`), separada de `PIER_LAYOUT_TOLERANCE_CM`
      (0,05cm, intocada);
- [x] ganho de cobertura permanece material: `COVERAGE_GAP_IN_ROW` TGD
      -310 / TP1 -113, `blocks` +1052 / +1155 — **98,4% a 100% retido**;
- [x] as 41 regressões novas de `OPENING_BLOCK_CROSSES_JAMB` = **ZERO**,
      verificado por instância nos 3 projetos;
- [x] nenhum hard blocker novo: `POSITION_OVERLAP`, todos os `JUNCTION_*`,
      `OPENING_BLOCK_INSIDE_DOOR/WINDOW`, `OPENING_SOLID_BELOW_SILL_MISSING`,
      `OPENING_MISSING_LINTEL/COUNTER_LINTEL` e
      `COVERAGE_WALL_NOT_MODULATED` com delta ZERO A→C;
- [x] amostra humana sem `QUALITY_REGRESSION` causada pelo C04 (as 4 que a
      tinham foram resolvidas mantendo o ganho);
- [x] determinismo: 4 seeds, fingerprint/peças/`non_modular`/ARM/B19
      idênticos;
- [x] nenhuma dependência nova de ordem/sentido (invariância idêntica à
      pré-existente);
- [x] NODE-FILL / ARM Safe Repair / Gate Fidelity / B19 preservados
      (140 testes focados verdes);
- [x] `baseline.json` / `reference.json` / `reference_score.json`:
      **ZERO alterações**;
- [x] produção dentro do escopo: os MESMOS 2 arquivos já autorizados,
      nenhum terceiro;
- [x] suíte completa compreendida e documentada (ver "Suíte completa").

Decisão explícita deixada para a revisão independente: a guarda usa o
predicado físico amplo (`trailing_open` — jamba de abertura **e** ponta
livre/reserva de nó). Restringi-la só a aberturas recuperaria os 5 vazios
de `W087` (100% de retenção), ao custo de manter a invasão de 0,242cm na
reserva de nó em 5 fiadas. A versão entregue escolhe o comportamento mais
conservador.

PARE.

NÃO MERGEAR.
NÃO marcar o PR como ready.
NÃO atualizar baseline/reference.
NÃO iniciar C02/C10/S1/S2.
NÃO monitoramento automático.
