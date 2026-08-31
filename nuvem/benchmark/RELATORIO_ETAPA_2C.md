# RELATORIO FINAL - ETAPA 2C (diagnostico de causa raiz) - CONCLUIDO

> Continuacao direta de `HANDOFF_ETAPA_2C.md` (checkpoint da sessao
> interrompida). Nada foi corrigido: **zero** edicao em `nuvem/core/**`,
> no solver, no Wall Modeling, em tolerancias, catalogo, compensadores,
> prisma, amarracoes ou aberturas.
>
> Convencao: **FATO MEDIDO** = numero que saiu de execucao real.
> **HIPOTESE** = leitura plausivel, ainda nao provada. **PENDENTE** = nao
> executado.

- HEAD / `origin/main` desta sessao: `a9ba8e546cc750823f8243188d6dc1367c39e4a9`
- Projeto: `torre_easy_lo_r00_tgd`
- `solver_decision_fingerprint`: `c74c9c1a...` (decisao do solver)
- `wall_modeling_engine_sha256`: `f0171249...` (sha do `nuvem/core/wall_modeling.py`)
- FASE A re-executada nesta sessao: `merge 9258 -> 2868`, **589 candidatos
  -> 209 aceitos / 380 descartados**, `dedup -42 -> 167`. Identico ao
  checkpoint e ao `wall_modeling_snapshot.json`. **A base e' reproduzivel.**

---

## RESUMO EXECUTIVO EM 5 LINHAS

1. O projetista humano **nao moveu nenhuma abertura** (max 0,244 cm em 75
   pares; 150 bonecas com diferenca max 0,244 cm). Hipotese refutada.
2. As 9 aberturas "sem parede" nascem em `find_wall_pairs`, nao nelas.
3. A causa raiz e' o **criterio de desempate** `sort_key = (-overlap_ratio, dist)`:
   com empate em `overlap_ratio` ele premia a **menor** distancia, nao a
   distancia **mais proxima da espessura pedida**. Em **71 de 72** perdas
   de par verdadeiro, o ladrao tinha espessura PIOR.
4. Efeito: 27 das 97 paredes do gabarito nao foram criadas (16 delas
   recuperaveis por um par que existia e foi descartado), 31 paredes
   espurias < 50 cm, e so' **76 das 167** paredes ficam no eixo certo.
5. **A geometria entregue ao solver esta' errada antes do solver.** Medir
   compensador/prisma/amarracao hoje mede ruido.

---

# PARTE I - ABERTURAS (entregas A a J)

## A. Distribuicao dos deslocamentos das 91 aberturas

**FATO MEDIDO** (`diagnostics_2c/openings_strict.json`, casamento estrito:
mesma reta `|perp|<=15 cm`, `|along|<=60 cm`, `|dw|<=20 cm`).

| | n |
|---|---|
| aberturas do INPUT | 91 |
| aberturas reconstruidas do HUMANO | 94 |
| pares INPUT x HUMANO | **75** |
| INPUT sem contraparte humana | 16 |
| HUMANO sem contraparte no INPUT | 19 |

Deslocamento AO LONGO da parede, nos 75 pares:

| faixa | n |
|---|---|
| 0 - 0,5 cm | **75 (100%)** |
| 0,5 cm ou mais | **0** |

media 0,0807 cm | mediana 0,0047 cm | P90 0,2432 cm | **maximo 0,2442 cm**.

Perpendicular: media 0,2325 | mediana 0,2432 | maximo 5,2408 cm (caso
unico `6558443` x `W060-O01`).

**Residuo sistematico:** o vetor (dx, dy) e' praticamente constante nos 75
pares - `dx ~ 0,00` e `dy = -0,243 cm`. Isso e' um offset global unico do
lado da reconstrucao do gabarito, **nao** movimento de abertura.
**Piso de ruido adotado: 0,5 cm.**

## B. 82 atribuidas x 9 nao atribuidas

**FATO MEDIDO.** Resposta direta: **as 9 problematicas NAO tem deslocamento
humano maior.**

| grupo | n com par | media \|along\| | mediana | P90 | max |
|---|---|---|---|---|---|
| A. atribuidas pelo Wall Modeling | 68 | 0,0747 cm | 0,0047 | 0,2432 | 0,2442 |
| B. NAO atribuidas (das 9) | 7 | 0,1397 cm | 0,2408 | 0,2422 | 0,2422 |

Os dois grupos estao inteiramente dentro do piso de ruido - **duas ordens
de grandeza abaixo da menor peca do catalogo (C04 = 4 cm)**. As outras 2
das 9 (`6558406`, `6558407`, largura 321 cm) nao tem contraparte humana.

## C. Aberturas realmente reposicionadas pelo humano

**FATO MEDIDO: NENHUMA.** Zero em 75. A hipotese prioritaria do pedido
("o humano deslocou portas/janelas alguns cm para a modulacao fechar")
esta' **REFUTADA COM DADO** neste projeto.

## D. Magnitude e direcao dos movimentos

**FATO MEDIDO.** Nao ha' movimento a caracterizar. O que existe e' um
**offset rigido de -0,243 cm em Y aplicado a todo o gabarito**
(reconstrucao), sem componente longitudinal e sem dispersao.
Classificacao de limites: **75 de 75 = `NO_CHANGE`**. Zero `TRANSLATION`,
zero `WIDTH_CHANGE`, zero `TYPE_CHANGE`.

## E. Alteracoes de largura / altura / peitoril

**FATO MEDIDO.**

- **Largura:** `dw = 0` em **74 de 75**; unico desvio `6558460` com `+0,11 cm`.
- **Peitoril:** `dsill = 0,0` em **75 de 75**. Nenhum peitoril alterado.
- **Verga (head):** `dhead` = -1,0 (43x), +9,0 (22x), -61,0 (8x), -6,0 (2x).
  **HIPOTESE (nao provada):** quantizacao do reconstrutor - o topo do vao
  reconstruido e' a ultima fiada com falha, e verga/canaleta fecham antes
  do topo real. Nao ha' evidencia de que o humano tenha mudado altura de vao.

## F. Bonecas INPUT x HUMANO

**FATO MEDIDO** (150 bonecas = 75 pares x 2 lados, `openings_strict.json`):

| | valor |
|---|---|
| diferenca maxima \|boneca_humano - boneca_input\| | **0,244 cm** |
| media | 0,0811 cm |
| bonecas com diferenca > 0,5 cm | **0** |

Ou seja: **nao existe no projeto o caso "11 cm / 144 cm -> 10 cm / 145 cm"**
que o pedido queria detectar. As bonecas que o humano modulou sao
exatamente as que o CAD entregou. (Consequencia aritmetica ja' garantida
por `along <= 0,25 cm` e `dw = 0` em 74/75, agora confirmada boneca a
boneca.)

Exemplos da tabela completa (INPUT / HUMANO, esquerda e direita, cm):

```
6558461  W073-O01  larg 91   19,00 / 19,00   274,00 / 274,00
6558462  W043-O02  larg 91   34,24 / 34,00   133,76 / 134,00
6558472  W016-O02  larg 231  54,24 / 54,00    33,76 /  34,00
6558475  W057-O01  larg 81   59,24 / 59,00    38,76 /  39,00
6558476  W057-O02  larg 81   39,24 / 39,00    43,76 /  44,00
```

(A diferenca de 0,24 cm que aparece e' o offset global de Y, nao ajuste.)

## G. Efeito modular das bonecas que o humano recebeu

**FATO MEDIDO - descoberta nova desta sessao. Existe uma malha modular
rigida no projeto:**

| grandeza | medida |
|---|---|
| comprimento das 97 paredes do gabarito | **96 de 97 sao `= 4 (mod 5)` cm** |
| largura das 91 aberturas do INPUT | **91 de 91 sao `= 1 (mod 5)` cm** |
| largura das 94 aberturas do HUMANO | 93 de 94 `= 1 (mod 5)` cm |
| **todas as 26 bonecas humanas distintas** | **`= 4 (mod 5)` cm** |
| comprimento das 167 paredes do Wall Modeling | **so' 82 de 167 sao `= 4 (mod 5)`** |

Valores distintos de boneca humana medidos: 19, 24, 34, 39, 44, 49, 54,
59, 64, 69, 74, 124, 134, 159, 164, 204, 274, 289, 309, 314, 519, 534,
754, 1024 cm (mais 18,9 e 288,9, que sao os mesmos com o ruido de 0,24).

**Consequencia pratica imediata:** `comprimento % 5 == 4` e' um **teste de
sanidade barato** para paredes reconstruidas do CAD. Hoje **85 das 167
paredes reprovam nesse teste** - todas suspeitas de vir de um par errado.

**HIPOTESE (nao provada):** a boneca nunca precisou ser ajustada porque o
projeto ja' nasceu na malha; e' o Wall Modeling que sai dela.

## H. Lateral das aberturas x blocos e juntas humanas

**FATO MEDIDO** (1.582 encostes medidos nas fiadas reais do gabarito):

- distancia da lateral do vao ate' a junta vertical humana mais proxima:
  **maximo 0,000 cm** dos dois lados. **A abertura e' fronteira dura: a
  fiada humana para exatamente na lateral do vao, em todas as fiadas.**
- bloco encostado na lateral ESQUERDA: B19 262, C04 147, B39 105, C09 97,
  B34 74, B54 39, B39_C 21, B34_C 16, CJ19 10, C09_C 6, B54_C 5, B19_C 4,
  CAN39 3, CM19 2, CAN34 1.
- bloco encostado na lateral DIREITA: B19 268, C04 151, B39 108, C09 94,
  B34 64, B54 37, B39_C 20, B34_C 14, CJ19 10, C09_C 7, B19_C 6, B54_C 4,
  CAN39 4, CM19 3.
- **502 de 1.582 encostes (31,7%) sao compensador (C04/C09).**

Leitura: o humano **absorve o residuo da modulacao encostado na abertura**,
com compensador, em quase um terco dos casos - em vez de mover a abertura.
Isso e' a regra generalizavel que o pedido procurava, so' que com o sinal
invertido em relacao a hipotese original.

## I. Trace das 9 aberturas (CAD -> merge -> pairs -> dedup -> extend -> assign)

**FATO MEDIDO** (do checkpoint, secao 8.10, e re-confirmado aqui). O trace
termina em `find_wall_pairs`: as etapas seguintes nao criam parede nova,
entao o destino ja' estava selado ali.

| abertura | parede do gabarito | mecanismo medido |
|---|---|---|
| 6558406, 6558407, 6558433 | **W012** (1484 cm, cov_wm = 0,00) | a face `y=-556,0` (1456 cm) foi consumida por um par com uma linha de **4,45 cm** a `d=12,100`. O parceiro verdadeiro `y=-570,0` (1681,21 cm, `d=13,999`, `r=1,0000`) ficou orfao. |
| 6558426 | **W036** (524 cm, cov_wm = 0,01) | face `x=-1799,5` (524 cm) consumida por linha de **4,45 cm** a `d=12,095`. Parceiro verdadeiro `x=-1813,5` (496 cm, `d=14,000`) orfao. |
| 6558458 | **W038** (524 cm, cov_wm = 0,01) | espelhado: face `x=1991,5` (524 cm) consumida por linha de **4,45 cm** a `d=12,105`. |
| 6558411 | **W072** (384 cm, cov_wm = 0,00) | face `y=364,1` (370,01 cm) pareada com linha de **18,52 cm** a `d=12,000` -> eixo em `y=370,05` (verdadeiro `y=357,05`). Abertura fica a 12,76 cm > limite 12,0 -> rejeitada. |
| 6558461 | **W073** (384 cm, cov_wm = 0,00) | espelhado (linha de 21,34 cm a `d=12,000`). |
| 6558475, 6558476 | **W057** (304 cm, cov_wm = 0,00) | face `x=156,5` (338 cm) pareada com linha de **94,0 cm** a `d=11,996` -> eixo `x=150,52` (verdadeiro `x=163,5`). Aberturas ficam a 12,99 cm -> rejeitadas. |

**FATO MEDIDO - fechamento do trace:** as 6 paredes do gabarito envolvidas
(W012, W036, W038, W072, W073, W057) estao **todas** na lista de paredes
que um par DESCARTADO teria criado, com cobertura 95-98%.

## J. Classificacao final das 9 aberturas

O rotulo `WALL_MODELING_ERROR` **nao** e' preservado por heranca. Com a
evidencia acima, a classificacao correta e':

| abertura | classificacao |
|---|---|
| 6558406 | `WALL_PAIRING_FACE_STOLEN` - parede W012 nao criada |
| 6558407 | `WALL_PAIRING_FACE_STOLEN` - parede W012 nao criada |
| 6558411 | `WALL_PAIRING_WRONG_AXIS` - eixo W072 13,0 cm fora |
| 6558426 | `WALL_PAIRING_FACE_STOLEN` - parede W036 nao criada |
| 6558433 | `WALL_PAIRING_FACE_STOLEN` - parede W012 nao criada |
| 6558458 | `WALL_PAIRING_FACE_STOLEN` - parede W038 nao criada |
| 6558461 | `WALL_PAIRING_WRONG_AXIS` - eixo W073 13,0 cm fora |
| 6558475 | `WALL_PAIRING_WRONG_AXIS` - eixo W057 13,0 cm fora |
| 6558476 | `WALL_PAIRING_WRONG_AXIS` - eixo W057 13,0 cm fora |

**Nenhuma das 9 e' erro de abertura, de INPUT ou de
`assign_openings_to_walls`.** 5 sao "face roubada", 4 sao "eixo errado" -
e as duas familias tem a **mesma** causa raiz (secao N).

**Nota:** `assign_openings_to_walls` esta' se comportando **corretamente**
nos 4 casos de eixo errado - ele rejeitou a abertura porque ela estava a
12,76 / 12,99 cm de um eixo cujo limite legitimo e' `14/2 + 5 = 12,0 cm`.
Mexer nessa tolerancia mascararia o defeito real.

---

# PARTE II - PAREDES E FRAGMENTACAO (entregas K a M)

## K. Distribuicao das 167 walls por comprimento

**FATO MEDIDO.**

| faixa | 167 walls DEPOIS da extensao | 167 ANTES da extensao | 97 walls do GABARITO |
|---|---|---|---|
| < 20 cm | **22** (13,2%) | **31** (18,6%) | **0** |
| 20-50 cm | 9 (5,4%) | 0 | **0** |
| 50-100 cm | 29 (17,4%) | 39 | 13 (13,4%) |
| 100-200 cm | 38 (22,8%) | 34 | 19 (19,6%) |
| 200-400 cm | 42 (25,1%) | 36 | 31 (32,0%) |
| > 400 cm | 27 (16,2%) | 27 | 34 (35,1%) |
| **total** | 43.032,7 cm | 41.456,3 cm | 45.362,8 cm |

**O gabarito humano nao tem NENHUMA parede abaixo de 50 cm. O Wall
Modeling tem 31.**

### K2. Cobertura do gabarito pelas 167 walls (analise nova desta sessao)

**FATO MEDIDO** (mesmo eixo, `|perp| <= 8 cm`, cobertura longitudinal):

| classe | paredes do gabarito | comprimento |
|---|---|---|
| COBERTA (>=85%) | **70** | 29.579,9 cm |
| PARCIAL (30-85%) | 9 | 7.901,0 cm |
| QUASE_AUSENTE (<30%) | 7 | 4.658,0 cm |
| **AUSENTE (0%)** | **11** | 3.224,0 cm |
| total | 97 | 45.362,9 cm |

**27 das 97 paredes do gabarito nao foram reproduzidas.** Dessas, **16
seriam recuperadas por um par que EXISTIA entre os 589 candidatos e foi
descartado** (cobertura 95-100%): W002, W009, W010, W012, W033, W036,
W038, W045, W053, W054, W057, W071, W072, W073, W079, W080.

As outras 11 nao tem par candidato nenhum:
- **W004, W005, W006, W007** (1344 cm) e **W015** (1379 cm): cobertura
  parcial 0,43-0,74. **HIPOTESE:** o reconstrutor do gabarito juntou
  paredes distintas numa so' (ver Anexo 1, pendencia do reconstrutor).
- **W025, W026, W084, W085** (269 cm) e **W046, W047** (374 cm):
  `cov_wm = 0` e `cov_lost = 0` - nao existe nem par aceito nem par
  descartado ali. **PENDENTE:** confirmar se a face correspondente existe
  no CAD (pode ser parede desenhada so' com uma face).

### K3. Erro de eixo das 167 walls (pendencia 11.1 do handoff, agora fechada)

**FATO MEDIDO** - distancia do eixo criado ate' o eixo do gabarito
paralelo mais proximo:

| erro | n |
|---|---|
| <= 0,5 cm (no lugar) | **76** |
| 0,5 - 2 cm | 15 |
| 2 - 6 cm | 22 |
| 6 - 10 cm | 5 |
| **10 - 16 cm** | **33** |
| > 16 cm (sem correspondencia real) | 11 |
| sem eixo de gabarito paralelo por perto (espurias) | 5 (211,2 cm) |

**So' 76 das 167 paredes (45,5%) estao no eixo certo.** O pico em
**10-16 cm** e' a assinatura do defeito: um eixo construido entre a face
certa e uma face errada fica deslocado de ~1 espessura.

## L. Origem dos fragmentos curtos

**FATO MEDIDO (checkpoint).** Para TODOS os 31 fragmentos < 50 cm, a
vizinha colinear mais proxima esta' a **700 cm ou mais**. Nao sao pedacos
de parede quebrada. `merge_collinear_fragments` esta' **inocentado**.

**FATO MEDIDO (novo, via `provenance_walls.json` + replay):** o par que
gerou cada fragmento curto:

| composicao do par | n |
|---|---|
| **linha curta (<20 cm) pareada com linha LONGA (>=100 cm)** | **19** |
| curta x curta | 12 |

E a origem das linhas curtas no CAD bruto:

| linha curta | origem |
|---|---|
| **4,445 cm** (7 casos) | **existe no CAD bruto** - `4,445 cm = 1,75"`, e' a **espessura da folha de porta**, desenhada dentro do vao |
| **5,08 cm** (8 casos) | **existe no CAD bruto** - `5,08 cm = 2"`, linha de marco/esquadria |
| 2,50 / 3,00 / 4,78 / 7,00 / 14,01 cm | existem no CAD bruto (marco, testa, batente) |
| 4,22 / 8,00 / 8,27 / 15,00 cm | **nascem no `merge_collinear_fragments`** (uniao de pedacos de esquadria) |

**Conclusao L:** os fragmentos curtos sao **linhas de esquadria (folha de
porta, marco, batente) desenhadas no mesmo Layer 'Arquitetura'**, que o
pareamento aceita como se fossem face de parede porque ficam a 11,8-12,5 cm
da face oposta - dentro da tolerancia de deteccao de 2,5 cm em torno de 14.

## M. Relacao entre reposicionamento de abertura e fragmentacao

**FATO MEDIDO.** A relacao pedida no enunciado (**reposicionamento** x
fragmentacao) **nao existe**, porque nao ha' reposicionamento (entrega C).

A relacao real e' outra e e' forte: **as aberturas causam a fragmentacao,
mas pelo desenho das esquadrias, nao pela posicao.**

| distancia do fragmento curto ate' a abertura mais proxima | n |
|---|---|
| <= 30 cm | 8 |
| 30 - 100 cm | 22 |
| 100 - 300 cm | 1 |
| > 300 cm | **0** |

**100% dos 31 fragmentos curtos estao a menos de 3 m de uma abertura; 97%
a menos de 1 m.** Cruzado com L: os fragmentos sao literalmente as pecas
da esquadria daquela abertura.

---

# PARTE III - CAUSA RAIZ (entregas N a S)

## N. Causas raiz agrupadas

### CR-1 (PRINCIPAL) - o desempate do ranking premia a MENOR distancia, nao a MAIS CORRETA

`nuvem/core/engine/wall_pairing.py::find_wall_pairs`, linha ~437:

```python
candidates.append(((-overlap_ratio, dist), i, j, matched_thickness))
...
candidates.sort(key=lambda c: c[0])
```

`sort_key = (-overlap_ratio, dist)` ordenado ascendente = maior
`overlap_ratio` primeiro e, no empate, **menor `dist` primeiro**. Como a
unica espessura pedida e' 14 cm e a tolerancia de deteccao e' 2,5 cm,
**qualquer** distancia entre 11,5 e 16,5 cm e' igualmente valida para
formar par - e o ranking entao prefere sistematicamente a de 11,8-12,1 cm
a de 14,0 cm.

**FATO MEDIDO:**

| medida | valor |
|---|---|
| pares aceitos com espessura exata (\|d-14\| <= 0,05) | **77 de 209 (37%)** |
| erro medio de espessura dos aceitos | 0,842 cm |
| aceitos com `d < 13,95` / `d > 14,05` | 78 / 54 |
| pares verdadeiros perdidos (`d = 14,00 +- 0,05`, `r >= 0,9`) | **52** |
| ocorrencias em que o ladrao tinha espessura **PIOR** | **71** |
| ocorrencias em que o ladrao tinha espessura igual/melhor | **1** |
| distancia dos ladroes | 12,0 (23x), 14,5 (13x), 13,7 (8x), 11,8 (7x), 12,1 (7x), 16,0 (5x), 15,5 (4x), 16,5 (2x), 15,0/14,4 (1x) |

**Simulacao offline (NAO aplicada ao codigo)** - mesmo conjunto de 589
candidatos, so' trocando o desempate:

| ordenacao | aceitos | com espessura exata | erro medio |
|---|---|---|---|
| ATUAL `(-r, d)` | 208* | **77 (37%)** | 0,863 cm |
| ALTERNATIVA `(-r, abs(d-14))` | 202 | **117 (58%)** | 0,428 cm |

66 pares passariam a existir; 72 deixariam de existir.
(*) o replay devolve 208 em vez de 209 por instabilidade de empate na
reordenacao - a comparacao e' valida porque os dois lados usam o mesmo
replay.

**Nota importante:** o docstring da propria funcao diz que o desempate por
menor distancia foi escolhido para **evitar** roubo de face. A medicao
mostra que, com espessura unica e tolerancia de 2,5 cm, ele **produz**
exatamente o roubo que queria evitar.

### CR-2 - `overlap_ratio` normalizado pela linha MAIS CURTA, sem piso de comprimento

`overlap_ratio = overlap / min(len_i, len_j)`. Uma linha de **4,445 cm**
(folha de porta) sobreposta a uma face de **1.456 cm** da
`ratio = 4,445/4,445 = 1,0000` - **empatada no topo do ranking com o par
verdadeiro**. O unico piso e' `MIN_WALL_SEGMENT_ABS_FLOOR_FT = 2,0 cm`,
que essas linhas passam folgado.

**FATO MEDIDO:** 30 dos 209 pares aceitos sao "curta (<20 cm) x longa
(>=100 cm)"; 19 dos 31 fragmentos < 50 cm nascem assim.

CR-2 e' o que **coloca o candidato errado no topo**; CR-1 e' o que
**faz ele ganhar do certo**. Precisam ser lidos juntos.

### CR-3 - guloso sem repescagem: uma face perdida nunca volta

Cada linha e' usada em no maximo um par e nao ha' segunda rodada para
faces orfas. Uma face de 1.456 cm consumida por um toco de 4,45 cm esta'
**definitivamente** perdida, mesmo com o parceiro perfeito (`d=13,999`,
`r=1,0000`) disponivel e sem uso.

**FATO MEDIDO:** 380 candidatos descartados por ponta ja' usada; 52 deles
eram pares verdadeiros.

### CR-4 - tolerancia de deteccao larga demais para espessura unica

`compute_detection_tolerance_ft` so' aperta a tolerancia quando ha' **duas
ou mais** espessuras escolhidas. Com `thicknesses_cm = [14.0]` ela devolve
o maximo, `WALL_DETECTION_TOLERANCE_FT = 2,5 cm`, abrindo a faixa
11,5-16,5 cm. **132 dos 209 pares aceitos entraram por essa folga.**

### CR-5 - linhas de esquadria no mesmo Layer da parede

O Layer 'Arquitetura' carrega folha de porta (4,445 cm), marco (5,08 cm),
batente, testa. O motor nao distingue. **E' a materia-prima de CR-2.**
(Nao e' bug do codigo; e' um fato do INPUT que o codigo precisa tolerar.)

### CR-6 - `deduplicate_walls` nao remove duplicata com angulo levemente diferente

**FATO MEDIDO:** walls 151-154 tem angulo **3,8 / 176,2 / 183,8 graus** num
projeto 0/90/180/270, praticamente em cima das walls 144/145. `dedup`
removeu 42 e deixou essas. Causa secundaria, herdada de CR-2 (as linhas de
origem sao pedacos de esquadria de 4,7-8,4 cm, que nao sao ortogonais).

### CR-7 - o `reason` de `unused_lines` e' enganoso (defeito de DIAGNOSTICO, nao de geometria)

`_classify_unused_line` compara a linha contra os **eixos ja' formados**,
nao contra outras linhas. Por isso as faces roubadas aparecem como
`distancia_fora_das_espessuras_escolhidas` com `esp_medida = 7,95` (meia
espessura ate' um eixo) em vez de "perdeu rodada". Contagem atual: 1431 /
852 / 167. **Nao usar essa coluna como diagnostico.**

## O. Cadeia causal

```
CAD: Layer 'Arquitetura' mistura face de parede com folha/marco de porta   [CR-5]
   |
   v
merge_collinear_fragments: 9258 -> 2868 linhas
   (nao quebra parede; ate' UNE face alem da parede real - ex.: y=-570
    unida ate' x=2267,7 enquanto W012 termina em x=2070,5)
   |
   v
find_wall_pairs: 589 candidatos validos
   |
   +-- overlap_ratio normalizado pela linha mais curta        [CR-2]
   |      => toco de 4,45 cm empata em r=1,0000 com o par verdadeiro
   |
   +-- tolerancia 2,5 cm com espessura unica                  [CR-4]
   |      => 11,5..16,5 cm todos "validos"
   |
   +-- desempate por MENOR dist                               [CR-1]  <== CAUSA RAIZ
   |      => d=12,0 vence d=14,0 em 71 de 72 disputas
   |
   +-- guloso sem repescagem                                  [CR-3]
   |      => face perdida nao volta
   |
   v
209 pares aceitos (so' 77 na espessura certa) / 380 descartados (52 verdadeiros)
   |
   +--> 31 paredes espurias < 50 cm   (o gabarito tem 0)           [K, L]
   +--> 33 paredes com eixo 10-16 cm fora do lugar                 [K3]
   +--> 27 das 97 paredes do gabarito nao criadas, 16 recuperaveis [K2]
   |
   v
deduplicate_walls -42 -> 167 (nao remove as quase-paralelas 151-154)  [CR-6]
   |
   v
extend_wall_ends_to_junctions: encosta fragmento espurio em parede boa
   (22 walls < 20 cm sobram; 9 sobem para a faixa 20-50)
   |
   v
build_wall_graph / assign_openings_to_walls
   |
   +--> 9 aberturas sem parede: 5 porque a parede nao existe,
   |    4 porque o eixo esta' 13 cm fora (12,76 / 12,99 > limite 12,0)
   |    -- assign_openings_to_walls agiu CORRETAMENTE nos 4 casos
   |
   v
SOLVER DE BLOCOS recebe geometria errada
   |
   +--> COMPENSATOR_CONSECUTIVE, PRISM_CONTINUOUS_JOINT,
        JUNCTION_NOT_ALTERNATING  <-- SINTOMA, nao causa.
        1671 criticos / 4986 findings do baseline sao medidos
        sobre paredes que nao deveriam existir ou estao no lugar errado.
```

## P. Causa raiz que deve ser tratada PRIMEIRO

**CR-1 - o criterio de desempate de `find_wall_pairs`.**

Justificativa medida:

1. **Maior efeito por menor mudanca.** E' uma unica linha
   (`(-overlap_ratio, dist)`). A simulacao offline leva a espessura exata
   de 37% para **58%** dos pares aceitos.
2. **Explica as duas familias das 9 aberturas** (face roubada e eixo
   errado) e **16 das 27 paredes ausentes** do gabarito.
3. **E' o passo que decide**: CR-2 e CR-4 apenas colocam o candidato
   errado na disputa; CR-1 e' quem entrega a vitoria a ele - em
   **71 de 72** disputas medidas.
4. **Nao muda o que e' aceito, so' a ordem.** O conjunto de 589 candidatos
   validos e' identico; muda quem ganha o empate. Isso torna o efeito
   colateral menor que o de mexer em tolerancia ou em piso de comprimento.

**Ordem sugerida (nao implementar nesta etapa):** CR-1 -> medir de novo ->
CR-2 (piso de comprimento absoluto ou `overlap_ratio` pela linha mais
LONGA) -> CR-3 (repescagem de faces orfas) -> CR-4 (apertar tolerancia
quando ha' espessura unica) -> CR-6 -> CR-7 (so' diagnostico).
**Nunca dois de uma vez**: o benchmark nao consegue atribuir credito.

## Q. Arquivos e funcoes que uma futura correcao envolve

| arquivo | ponto | papel |
|---|---|---|
| `nuvem/core/engine/wall_pairing.py` | `find_wall_pairs` (~266-445), montagem de `candidates` (~437) e `candidates.sort` (~440) | **CR-1, CR-2, CR-3** - o unico ponto que precisa mudar para CR-1 |
| `nuvem/core/engine/wall_pairing.py` | `compute_detection_tolerance_ft` (~1405-1418) | **CR-4** |
| `nuvem/core/engine/wall_pairing.py` | `deduplicate_walls` | **CR-6** |
| `nuvem/core/engine/tolerances.py` | `MIN_WALL_SEGMENT_OVERLAP_RATIO = 0.6`, `MIN_WALL_SEGMENT_ABS_FLOOR_FT = 2,0 cm`, `WALL_DETECTION_TOLERANCE_FT = 2,5 cm`, `MIN/MAX_WALL_THICKNESS_FT = 5/35 cm` | constantes de CR-2 e CR-4 |
| `nuvem/core/engine/opening_audit.py` | `OPENING_GAP_MIN_CM = 50`, `OPENING_GAP_MAX_CM = 260`, `OPENING_MIN_CONSEC_COURSES = 4` | so' afeta a **reconstrucao do gabarito** (as 16 sem par e as 19 fantasma) - **nao** o Wall Modeling |
| `nuvem/benchmark/wall_modeling_bridge.py` | `_classify_unused_line` | **CR-7** (diagnostico) |
| `nuvem/benchmark/projects/torre_easy_lo_r00_tgd/baselines/baseline_real_v1.json` | `wall_modeling_engine_sha256` | **vai mudar** com qualquer edicao em `wall_modeling.py`; precisa ser re-emitido de proposito |

**Nao envolve** (confirmado por medicao): `merge_collinear_fragments`,
`assign_openings_to_walls`, o catalogo, os compensadores, o prisma, as
amarracoes, e nenhuma tolerancia de abertura.

## R. Casos minimos de regressao necessarios

Todos headless, sem Revit, a partir de `input_real.json`. Nenhum existe
hoje.

| # | caso | criterio de aprovacao (numeros de hoje entre parenteses) |
|---|---|---|
| R1 | **Toco nao rouba face longa** - duas faces a 14,00 cm (1456 e 1681 cm) + uma linha de 4,445 cm a 12,10 cm de uma delas | o par 14,00 vence; nenhuma parede de ~4,45 cm e' criada (hoje: cria) |
| R2 | **W012 existe** - projeto completo | existe parede em `y = -563 +- 0,5`, `x` de 586,5 a 2070,5, len 1484 +- 2 (hoje: cobertura 0,00) |
| R3 | **As 6 paredes ausentes do trace** (W012, W036, W038, W057, W072, W073) | cobertura >= 0,85 nas 6 (hoje: 0,00 / 0,01 / 0,01 / 0,00 / 0,00 / 0,00) |
| R4 | **As 9 aberturas** | 91 de 91 atribuidas (hoje 82) |
| R5 | **Malha modular** | `len % 5 == 4` em >= 95% das paredes criadas (hoje **82/167 = 49%**) |
| R6 | **Sem parede minuscula** | zero paredes < 50 cm (hoje 31); o gabarito tem 0 |
| R7 | **Espessura medida** | `abs(dist_real - 14,0) <= 0,05` em >= 90% dos pares aceitos (hoje **77/209 = 37%**) |
| R8 | **Eixo no lugar** | erro de eixo <= 0,5 cm em >= 90% das paredes (hoje **76/167 = 45,5%**) |
| R9 | **Cobertura do gabarito** | >= 90 das 97 paredes COBERTAS (hoje **70**) |
| R10 | **Nao-regressao do que ja' funciona** | as 70 paredes hoje COBERTAS continuam cobertas; as 82 aberturas hoje atribuidas continuam atribuidas |
| R11 | **Determinismo** | duas execucoes da FASE A dao byte a byte o mesmo `wall_modeling_snapshot.json` |
| R12 | **Custo** | `find_wall_pairs` continua O(n^2) - hoje 1.332.676 pares paralelos avaliados em ~7 s |

R10 e' o mais importante: e' o unico que impede uma "correcao" de trocar
um conjunto de erros por outro.

## S. Riscos de regressao de uma futura correcao

| risco | por que | mitigacao proposta |
|---|---|---|
| **Perder bonecas curtas legitimas** | o docstring registra que o desempate por menor distancia foi posto justamente para nao roubar a face de uma boneca curta. Trocar por `abs(d - espessura)` pode reabrir aquele caso | R10 + inspecionar os **72 pares que a alternativa elimina** um a um antes de aceitar |
| **Empates instaveis / nao determinismo** | com `(-r, abs(d-nominal))` haverao mais empates exatos (varios pares a 14,000). O replay ja' mostrou 208 vs 209 so' por ordem de insercao | acrescentar desempate final deterministico (ex.: maior sobreposicao absoluta, depois indice) e travar com R11 |
| **Quebrar o fingerprint e o baseline** | `wall_modeling_engine_sha256 = f0171249...` muda; `baseline_real_v1` fica invalido; `solver_decision_fingerprint` muda junto | re-emitir baseline **de proposito**, num commit separado, guardando o par antigo/novo |
| **Melhorar a geometria e PIORAR o `success_rate`** | hoje 0,0659 e' medido sobre 167 paredes, 31 das quais nao deveriam existir. Criando W012 (1484 cm) entram milhares de blocos novos que o solver ainda nao sabe modular bem | avaliar por **cobertura do gabarito (R9)** e nao por `success_rate` enquanto a FASE A estiver mudando |
| **Mais paredes = mais tempo** | 10.657 blocos hoje; corrigir a FASE A aumenta paredes e blocos | R12 + medir tempo total antes/depois |
| **Corrigir CR-1 e CR-2 juntos** | os efeitos se confundem e o benchmark nao consegue atribuir credito | um de cada vez, com medicao entre eles |
| **Mexer na tolerancia de abertura (12,0 cm) para "resolver" as 4 de eixo errado** | mascara o defeito: a abertura esta' a 12,76 cm de um eixo que esta' 13 cm fora do lugar | proibido: R3/R8 antes de qualquer discussao sobre tolerancia de abertura |

---

# ANEXO 1 - Hipoteses do checkpoint: estado final

| hipotese | estado |
|---|---|
| FASE A reproduzivel headless bit a bit | **CONFIRMADA** (re-confirmada nesta sessao: 2868 / 209 / 380 / -42 / 167) |
| As 9 nascem em `find_wall_pairs` | **CONFIRMADA** |
| Existe roubo de face por fragmento curto | **CONFIRMADA e quantificada** (30 pares aceitos; 19 dos 31 fragmentos) |
| Gabarito nao tem parede < 50 cm; WM tem 31 | **CONFIRMADA** |
| Fragmentos curtos nao sao parede quebrada | **CONFIRMADA** |
| "O humano moveu aberturas para fechar a modulacao" | **REJEITADA** (max 0,244 cm em 75 pares, 150 bonecas) |
| "As 9 tem deslocamento maior que as 82" | **REJEITADA** |
| "A fragmentacao vem do `merge_collinear_fragments`" | **REJEITADA** |
| "O humano ajustou boneca (11/144 -> 10/145)" | **REJEITADA** (max 0,244 cm em 150 bonecas) |
| Pendencia 11.1 - varredura sistematica de erro de eixo | **FECHADA** (secao K3) |
| Pendencia 11.2 - paredes do gabarito nao criadas | **FECHADA** (secao K2: 27, sendo 16 recuperaveis) |
| Pendencia 11.3 - origem de cada fragmento curto | **FECHADA** (secao L) |
| Pendencia 11.4 - secao 10 do pedido (lateral x blocos humanos) | **FECHADA** (secao H) |
| Pendencia 11.5 - secao 14 (cenario A x B) | **REFORMULADA e FECHADA** (secao G: nao ha' cenario B; a malha modular e' o achado) |
| Pendencia 11.6 - as 3 hipoteses do reconstrutor do gabarito | **AINDA PENDENTE** (16 sem par, 19 fantasma, `dhead` quantizado) - **nao bloqueia a correcao**, afeta so' a leitura do gabarito |
| Pendencia 11.7 - `cap_clipped_count = 11` e `offset_suspect_count = 6` | **AINDA PENDENTE** - volume pequeno, nao explica os numeros grandes |
| Pendencia 11.8 - por que `deduplicate_walls` deixou 151-154 | **EXPLICADA** (CR-6: angulo 3,8 graus vindo de linhas de esquadria), nao medida caso a caso |
| NOVA pendencia - W025/W026/W084/W085/W046/W047 sem par candidato nenhum | **PENDENTE** (ver K2) |

# ANEXO 2 - Os dois comandos que falharam no checkpoint (revisao pedida)

1. **`inspect1.py` - `Permission denied` / caminho errado.** Causa: `$TMPD`
   nao persistia entre chamadas do shell. Foi corrigido e re-executado na
   mesma sessao; a saida esta' transcrita no handoff (secoes 8 e 12).
   **Nenhuma medicao ficou incompleta. Nao precisa ser repetido.**
2. **`provenance.py` (1a execucao) - `ModuleNotFoundError: wall_pairing`.**
   Causa: o motor headless e' carregado como um modulo unico
   (`script_under_test`) por `solver_bridge.engine()`. Corrigido com
   `wp = mod` e re-executado. **Verificado nesta sessao:** o
   `provenance_walls.json` gerado bate par a par e linha a linha com o
   replay independente feito hoje (169 de 209 identicos ate' a 2a casa; os
   40 restantes diferem so' por arredondamento de 2 vs 3 decimais; a soma
   dos comprimentos bate em 47.624,8 x 47.624,7 cm).
   **Nenhuma medicao ficou incompleta. Nao precisa ser repetido.**

**Correcao de documentacao:** o handoff (secao 13) descreve
`provenance_walls.json` como "167 paredes". Ele tem **209 entradas** - os
pares ACEITOS, **antes** do `deduplicate_walls`. O indice `w` desse arquivo
**nao** e' o `index` das 167 walls do snapshot.

**Terceira falha desta sessao (mesma do checkpoint, sem efeito na
analise):** escrever este relatorio por heredoc estourou o limite de
argumento do shell (`ENAMETOOLONG: uv_spawn`); foi escrito pela ferramenta
de escrita direta.

# ANEXO 3 - Numeros de referencia (para a proxima sessao nao remedir)

```
CAD                 9258 linhas no Layer 'Arquitetura'
merge                     -> 2868 linhas
candidatos validos        -> 589
aceitos                   -> 209   (77 na espessura exata 14,00)
descartados               -> 380   (52 eram pares verdadeiros)
dedup                     -> -42 -> 167 paredes
unused_lines              -> 2450  (71.180,3 cm de linha nao aproveitada)
detection_tolerance       = 2,5 cm   (espessuras pedidas: [14.0])
parallel_pairs avaliados  = 1.332.676
offset_suspect_count      = 6   (max 0,0782 ft)
cap_clipped_count         = 11

gabarito                  97 paredes / 45.362,8 cm / 94 aberturas reconstruidas
                          70 COBERTAS, 9 PARCIAIS, 7 QUASE_AUSENTES, 11 AUSENTES
wall modeling             167 paredes / 43.032,7 cm / 82 de 91 aberturas atribuidas
                          76 no eixo certo, 33 com eixo 10-16 cm fora, 5 espurias
                          31 paredes < 50 cm (gabarito tem 0)
                          82 de 167 com len % 5 == 4 (gabarito: 96 de 97)

baseline_real_v1          full  success_rate 0,0659 | 1671 criticos | 167 walls | 10657 blocos
                          scoped success_rate 0,0592 | 1584 criticos | 152 walls | 10237 blocos
```

---

## Estado ao fim desta sessao

- **Nada foi corrigido.** Zero edicao em `nuvem/core/**`, solver, Wall
  Modeling, tolerancias, catalogo, aberturas, compensadores, prisma,
  amarracoes.
- Arquivos novos/alterados: este relatorio, o aviso de continuacao no topo
  de `HANDOFF_ETAPA_2C.md`, e a secao 25 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md` (obrigatoria por CLAUDE.md).
- **Nenhum commit foi feito.**
- A proxima sessao e' o **PLANO da primeira correcao (CR-1)**, ainda sem
  implementar.
