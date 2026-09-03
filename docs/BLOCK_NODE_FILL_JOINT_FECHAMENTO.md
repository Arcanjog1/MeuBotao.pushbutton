# RELATÓRIO FINAL — CR-BLOCK-NODE-FILL-JOINT / FECHAMENTO

> **PRODUÇÃO ALTERADA NESTA ETAPA: ZERO.** O diagnóstico provou que não há
> violação física a corrigir no motor. Nenhum `baseline.json` /
> `reference.json` / `reference_score.json` tocado. **NENHUM MERGE FEITO.**

## Git

```
branch                     claude/cr-block-node-fill-joint-9tv0kd
HEAD ao iniciar            d1fc4abb79e5623e680abf847c76385d26994520   CONFERE
ponto de comparacao ANTES  2594f6ff (HEAD da auditoria, sem o NODE-FILL)
```

## As seis paredes

`W019`, `W045`, `W051`, `W090`, `W131`, `W146` — mais `W020`, `W112` e
`W050`, que também aparecem no diff peça a peça. A tabela completa está em
`diagnostics_block_node_fill_joint/out_nf_door_table_{before_HEAD,after}.json`
(uma linha por achado, com parede, fiada, cota, abertura, bloco, sobreposição
e estágio).

## Os blocos adicionais dentro das portas

Diff peça a peça (`run_nf_door_table.py`), ANTES → DEPOIS:

```
WALL   ROW  ELEV    OPENING     CLASSE  BLOCO_T          BLK   OVERLAP  ESTAGIO         VAO_T
--- NOVOS (17) ---
W020   11   220.0   W020-O03    JAMB    470.0..509.0     B39     5.0    STANDARD_FILL   504.0..595.0
W020   11   220.0   W020-O03    IN      510.0..549.0     B39    39.0    STANDARD_FILL   504.0..595.0
W020   11   220.0   W020-O03    IN      550.0..589.0     B39    39.0    STANDARD_FILL   504.0..595.0
W020   11   220.0   W020-O03    JAMB    590.0..629.0     B39     5.0    STANDARD_FILL   504.0..595.0
W045   11   220.0   W045-O01    IN       55.0..89.0      B34    34.0    STANDARD_FILL    19.0..110.0
W045   11   220.0   W045-O01    IN       90.0..109.0     B19    19.0    STANDARD_FILL    19.0..110.0
W051   11   220.0   W051-O02    IN      263.0..267.0     C04     4.0    STANDARD_FILL   259.2..350.2
W051   11   220.0   W051-O02    IN      268.0..287.0     B19    19.0    STANDARD_FILL   259.2..350.2
W051   11   220.0   W051-O02    IN      288.0..322.0     B34    34.0    STANDARD_FILL   259.2..350.2
W112   11   220.0   W112-O02    JAMB    343.0..377.0     B34     6.8    STANDARD_FILL   258.8..349.8
W131   11   220.0   W131-O01    IN       42.0..51.0      C09     9.0    STANDARD_FILL     6.0..107.0
W131   11   220.0   W131-O01    IN       52.0..91.0      B39    39.0    STANDARD_FILL     6.0..107.0
W131   11   220.0   W131-O01    JAMB     92.0..131.0     B39    15.0    STANDARD_FILL     6.0..107.0
W146   11   220.0   W146-O02    JAMB    215.0..254.0     B39     5.0    STANDARD_FILL   249.0..340.0
W146   11   220.0   W146-O02    IN      255.0..294.0     B39    39.0    STANDARD_FILL   249.0..340.0
W146   11   220.0   W146-O02    IN      295.0..334.0     B39    39.0    STANDARD_FILL   249.0..340.0
W146   11   220.0   W146-O02    JAMB    335.0..374.0     B39     5.0    STANDARD_FILL   249.0..340.0
--- SUMIRAM (13) ---
W020   11   220.0   W020-O03    JAMB    480.0..519.0     B39    15.0    STANDARD_FILL   504.0..595.0
W020   11   220.0   W020-O03    IN      520.0..559.0     B39    39.0    STANDARD_FILL   504.0..595.0
W020   11   220.0   W020-O03    JAMB    560.0..599.0     B39    35.0    STANDARD_FILL   504.0..595.0
W045   11   220.0   W045-O01    IN       55.0..94.0      B39    39.0    STANDARD_FILL    19.0..110.0
W045   11   220.0   W045-O01    JAMB     95.0..114.0     B19    15.0    STANDARD_FILL    19.0..110.0
W051   11   220.0   W051-O02    IN      263.0..282.0     B19    19.0    STANDARD_FILL   259.2..350.2
W051   11   220.0   W051-O02    IN      283.0..322.0     B39    39.0    STANDARD_FILL   259.2..350.2
W112   11   220.0   W112-O02    JAMB    343.0..382.0     B39     6.8    STANDARD_FILL   258.8..349.8
W131   11   220.0   W131-O01    IN       42.0..81.0      B39    39.0    STANDARD_FILL     6.0..107.0
W131   11   220.0   W131-O01    JAMB     82.0..121.0     B39    25.0    STANDARD_FILL     6.0..107.0
W146   11   220.0   W146-O02    JAMB    245.0..284.0     B39    35.0    STANDARD_FILL   249.0..340.0
W146   11   220.0   W146-O02    IN      285.0..324.0     B39    39.0    STANDARD_FILL   249.0..340.0
W146   11   220.0   W146-O02    JAMB    325.0..364.0     B39    15.0    STANDARD_FILL   249.0..340.0
```

Saldo: `INSIDE_DOOR` +11 −6 = **+5** (44 → 49); `CROSSES_JAMB` +6 −7 = **−1**
(147 → 146). Total de achados de porta: 187 → 191.

**As 30 linhas do diff estão na MESMA fiada (11) e no MESMO estágio
(`STANDARD_FILL`).** Nenhuma parede nova entra na lista: as 18 paredes com
`INSIDE_DOOR` são exatamente as mesmas antes e depois.

Distribuição por fiada, `OPENING_BLOCK_INSIDE_DOOR`:

| | fiada 1 | 3 | 5 | 7 | 9 | **fiada 11** | total |
|---|---|---|---|---|---|---|---|
| **ANTES** | 1 | 1 | 1 | 1 | 1 | **39** | 44 |
| **DEPOIS** | 1 | 1 | 1 | 1 | 1 | **44** | 49 |

**Os 5 achados fora da fiada 11 não mudaram. 100 % do delta está na
fiada 11.**

## Estágio que criou cada um

Rastreabilidade peça a peça, pelo `placement_reason` que o próprio candidato
carrega até o modelo do benchmark:

| origem candidata (item 4 do CR) | achados novos |
|---|---|
| **A) STANDARD_FILL** | **17 de 17** |
| B) OPENING CUT | 0 |
| C) CONFLICT REMOVAL | 0 |
| D) LOCAL OPENING REPAIR (`OPENING_REPAIR_FILL`) | 0 |
| E) NODE PIECE (L/T/X) | 0 |
| F) FINAL ASSEMBLY | 0 |
| G) VALIDATOR / METRIC DIFFERENCE | ver abaixo — **é aqui que a regressão nasce** |

Todos os 17 vêm da FASE 1 (preenchimento contínuo) da fiada 11. Nenhum vem
do recorte nem do reparo local — o item 7 do CR (“não deixar o reparo de
abertura quebrar o NODE-FILL”) **não é o caso**: o reparo não participa.

## Por que `door_void_violations` não mudou

Porque o motor e o modelo do benchmark **medem em origens verticais
diferentes**, e só o segundo enxerga estes 44 achados.

```
FIRST_COURSE_Z_OFFSET_CM = 1.0        (medido no Revit real - PADRAO_MODULACAO.md:
                                       "progressao exata 21/41/61/.../201/221cm")

MOTOR   _course_z_abs(base, n) = base + 1 + n*20
        fiada 10  ->  201.00 .. 220.00
        fiada 11  ->  221.00 .. 240.00      <-- comeca EXATAMENTE na verga
        fiada 12  ->  241.00 .. 260.00

MODELO  extract/from_solver: base + n*20   (o offset e' PERDIDO)
        fiada 10  ->  200.00 .. 219.00
        fiada 11  ->  220.00 .. 239.00
        fiada 12  ->  240.00 .. 259.00

...mas `sill_cm`/`head_cm` do MESMO modelo continuam no Z ABSOLUTO do motor.
```

As portas destas seis paredes têm **verga em 221,0 cm** — exatamente a
fronteira entre a fiada 10 e a fiada 11 do motor. Medido pelas próprias
funções do motor (`run_nf_z_origin.py`):

```
porta sill=0.0 head=221.0
  fiada 10  MOTOR ativo=True   sobrep=19.00cm | MODELO ativo=True   sobrep=19.00cm
  fiada 11  MOTOR ativo=False  sobrep= 0.00cm | MODELO ativo=True   sobrep= 1.00cm
  fiada 12  MOTOR ativo=False  sobrep= 0.00cm | MODELO ativo=False  sobrep= 0.00cm
```

O que cada métrica mede, e onde:

| métrica | estrutura | convenção vertical | vê a fiada 11? |
|---|---|---|---|
| `door_void_violations` | `solve_result`, candidatos do motor | a do MOTOR (`_course_z_abs`, com offset) | **NÃO** — sobreposição 0,00 cm |
| `jamb_exceptions` | `solve_result`, jambas | não é vertical (é por trecho) | não se aplica |
| `OPENING_BLOCK_INSIDE_DOOR` | modelo do benchmark, `rows[].blocks` | fiada SEM offset × abertura COM offset | **SIM** — 1,00 cm fantasma |

**Resposta ao item 5: é diferença legítima de definição — e um bug de
medição.** As duas coordenadas comparadas por
`analysis.opening_active_in_row` vivem em origens 1 cm distantes. Toda porta
cuja verga caia exatamente numa fronteira de fiada ganha 1 cm de
sobreposição fantasma na fiada de cima, em TODO o projeto.

## Causa-raiz

Duas medições independentes, e as duas dizem o mesmo:

**1. Por altura da interseção** (`run_nf_door_volume.py`) — separa o
fantasma do defeito real:

| altura da interseção | comprimento ANTES | DEPOIS | fiadas |
|---|---|---|---|
| **1,0 cm** (fantasma) | 1856,58 cm | **1851,58 cm** | 11 |
| **19,0 cm** (real) | 1455,09 cm | **1455,09 cm** | 0 a 10 |

O defeito REAL (bloco 19 cm dentro do vão, fiadas 0–10) fica **idêntico**.
Só o fantasma muda, e **para menos**.

**2. Material físico dentro do vão de porta**, que não depende da fronteira
de 90 % do validador (`INSIDE_RATIO`):

```
comprimento    3311,663 cm   ->   3306,661 cm    (-5,00 cm)
area           29503,211 cm2 ->   29498,209 cm2  (-5,00 cm2)
pecas                 187    ->          191     (+4)
```

**O material dentro das portas DIMINUIU.** O que aumentou foi o número de
PEÇAS em que esse mesmo material está cortado: o NODE-FILL desloca a fase da
corrente de B39 da fiada 11 em 10 cm, e peças que antes cruzavam a jamba
(< 90 % dentro) passam a cair inteiras dentro do intervalo — atravessando a
fronteira de classificação do validador, sem que nada de físico piore.

**3. A prova decisiva** — as MESMAS medições com as duas origens alinhadas
(`run_nf_z_origin.py`, monkeypatch em memória, nada gravado):

| código | ANTES | DEPOIS | ANTES alinhado | DEPOIS alinhado |
|---|---|---|---|---|
| `OPENING_BLOCK_INSIDE_DOOR` | 44 | 49 | **5** | **5** |
| `OPENING_BLOCK_CROSSES_JAMB` | 147 | 146 | **108** | **108** |
| `COVERAGE_ROW_MOSTLY_EMPTY` | 187 | 187 | **136** | **136** |
| `COVERAGE_PARTIAL_WALL` | 55 | 55 | **59** | **59** |
| `PRISM_CONTINUOUS_JOINT` | 562 | 318 | **562** | **318** |

**Com uma origem vertical consistente, este CR é IDÊNTICO ao ponto anterior
em toda métrica de abertura e de cobertura — e só o prisma melhora.**
A regressão 44 → 49 não existe na geometria; existe só na régua.

## Fix

**Item 6 não se aplica: não há violação física a corrigir.** A fiada 11 do
motor começa em 221,00 cm e a verga está em 221,0 cm — sobreposição
**0,00 cm**. Não há bloco no vazio da porta ali, e por isso
`door_void_violations` (que usa a convenção do motor) não se mexeu.

**Nenhuma linha de `wall_stepper.py` foi alterada nesta etapa.** Mexer na
geometria para baixar um número que a régua inventou seria exatamente o que
os itens 5 e 9 proíbem.

### O que precisa ser corrigido, e por que NÃO foi feito aqui

A correção é de UMA função, fora do escopo autorizado pelo item 8:

```
nuvem/benchmark/extract/from_solver.py   (camada de MEDIÇÃO, não o motor)
```

Duas formas consistentes, ambas medidas:

| variante | o que faz | risco |
|---|---|---|
| **R1** | `elevation_cm = base + FIRST_COURSE_Z_OFFSET_CM + n*passo` (fiadas passam a 1, 21, … 221) | quebra o pareamento de fiada contra o `reference.json`, cujas fiadas estão em 0, 20, … 220 |
| **R2** | `sill_cm`/`head_cm` passam para a MESMA origem nominal das fiadas (−1 cm) | mexe só na abertura; foi a variante medida acima |

**Por que parei (item 8).** A correção é fora de `wall_stepper.py` e move
vários códigos rastreados por `baseline.json`, em mais de um projeto:

```
tgd  OPENING_BLOCK_INSIDE_DOOR    49 -> 5     (-44)
tgd  OPENING_BLOCK_CROSSES_JAMB  146 -> 108   (-38)
tgd  COVERAGE_ROW_MOSTLY_EMPTY   187 -> 136   (-51)
tgd  COVERAGE_PARTIAL_WALL        55 -> 59    (+4)
tp1  OPENING_MISSING_LINTEL       92 -> 0     (-92)
piloto                            sem efeito nenhum (verga 210 nao cai em fronteira de fiada)
```

Embutir isso neste CR faria o CR “passar” por um motivo que nada tem a ver
com a junta nó/preenchimento, e invalidaria em silêncio o significado de
quatro códigos do `baseline.json` — que o item 11 proíbe atualizar.
**É um CR próprio (`CR-BENCH-Z-ORIGIN`), com decisão explícita de refresh de
baseline.** Está medido, reproduzível e pronto para aplicar assim que
autorizado.

## PRISM

| | MAIN | ANTES | **DEPOIS** |
|---|---|---|---|
| piloto `PRISM_CONTINUOUS_JOINT` | 0 | 14 | **0** |
| piloto `PRISM_JOINT_STACK` | 0 | 2 | **0** |
| tgd `PRISM_CONTINUOUS_JOINT` | 702 | 562 | **318** |
| tgd `PRISM_JOINT_STACK` | 46 | 39 | **21** |
| tp1 `PRISM_CONTINUOUS_JOINT` | 837 | 730 | **169** |
| tp1 `PRISM_JOINT_STACK` | 49 | 40 | **8** |

Todo o ganho preservado — nada foi desfeito.

## OPENING_BLOCK_INSIDE_DOOR

```
baseline.json  45      main  43      ANTES  44      DEPOIS  49
                                     ANTES  5       DEPOIS  5    <- com origem consistente
```

Real: **5 antes, 5 depois**. Fantasma: 39 antes, 44 depois.

## door_void_violations

```
MAIN 290   ANTES 290   DEPOIS 290     tgd
MAIN 348   ANTES 348   DEPOIS 348     tp1
MAIN   0   ANTES   0   DEPOIS   0     piloto
```

Inalterado — e agora se sabe exatamente por quê (secção “Por que
`door_void_violations` não mudou”).

## jamb_exceptions

```
MAIN 172   ANTES 172   DEPOIS 172     tgd
MAIN  44   ANTES  52   DEPOIS  52     tp1   (a piora veio do wall graph, nao deste CR)
MAIN   4   ANTES   4   DEPOIS   4     piloto
```

## Determinismo

Bateria metamórfica do cross-audit (31 entradas por projeto: baseline + 20
permutações + 10 reversões de endpoint), **inalterada** desde a etapa
anterior — nenhuma linha de produção mudou nesta etapa:

```
piloto  11/11 camadas com 1 fingerprint, global = 1
tgd     11/11 camadas com 1 fingerprint, global = 1  (as 31 entradas colapsam numa so')
tp1     11/11 camadas com 1 fingerprint, global = 1  (idem)
```

## L/T/X

Delta ZERO em todas as categorias de nó, nos três projetos e nos três pontos
de medição (tabela completa no relatório da etapa anterior,
`docs/BLOCK_NODE_FILL_JOINT.md`). Nenhuma peça de nó reposicionada.

## Cross-band

```
MAIN 33   ANTES 60   DEPOIS 48
```

## Compensadores

```
compensadores consecutivos   MAIN 1210   ANTES 1168   DEPOIS 1114
```

## Cobertura

```
tgd COVERAGE_MISSING_ROW        265 / 293 / 293      (MAIN / ANTES / DEPOIS)
tgd COVERAGE_ROW_MOSTLY_EMPTY   171 / 187 / 187
tp1 COVERAGE_MISSING_ROW         16 /  18 /  18
```

Delta ZERO contra o ponto anterior — este CR continua sem piorar a dívida do
wall graph (item 15 respeitado). Registro adicional: **51 dos 187
`COVERAGE_ROW_MOSTLY_EMPTY` do TGD também são do mesmo fantasma de 1 cm**
(caem para 136 com as origens alinhadas). Parte da “dívida de cobertura” que
o cross-audit atribuiu ao wall graph é, na verdade, régua — informação para
a frente que cuida de `wall_pairing.py`, não para este CR.

## Reference Corpus

Sem alteração de produção nesta etapa, o corpus continua como no fim da
etapa anterior:

```
OVERALL: CRITICAL_REGRESSION_PRESENT
- tgd  COVERAGE_MISSING_ROW        265 -> 293    (wall graph, item 15)
- tgd  COVERAGE_ROW_MOSTLY_EMPTY   171 -> 187    (wall graph + 51 de regua)
- tgd  OPENING_BLOCK_INSIDE_DOOR    45 -> 49     (FANTASMA - provado acima)
- tp1  COVERAGE_MISSING_ROW         16 -> 18     (wall graph, item 15)
```

Nenhum `baseline.json`, `reference.json` ou `reference_score.json` foi
tocado.

## Performance

Inalterada — nenhuma linha de produção mudou nesta etapa. O custo medido na
etapa anterior continua valendo: **+4,2 % (piloto), +5,6 % (tgd), +9,1 %
(tp1)** no tempo total, mediana de 5 repetições.

## Testes

| suíte | resultado |
|---|---|
| `tests/test_block_node_fill_joint.py` | **23 passed** (eram 20; +3 do item 12) |
| `tests/test_block_pipeline_determinism.py` | 52 passed |
| `tests/test_block_graph_determinism.py` | 27 passed |
| `tests/test_block_bonding.py` | 32 passed |
| `tests/test_golden_benchmark.py` | 90 passed |
| `tests/test_script.py` | 260 passed |
| `tests/regression` | 111 passed, 2 failed |
| `tests/ -m "not slow"` | **597 passed** |
| árvore inteira | **608 passed, 2 failed** |

As 2 falhas são as mesmas de sempre: as duas regressões de COBERTURA do wall
graph (item 15) — agora com a informação adicional de que 51 delas são
régua, não geometria.

### Os 3 testes novos (item 12)

`INV-NODEFILL-030/031/032` — NÓ nas duas pontas + PORTA + múltiplas fiadas,
na célula fechada (a geometria onde o NODE-FILL comprovadamente MUDA o
layout). Verificam, **na mesma rodada e sobre a mesma geometria**, os dois
invariantes que não podem ser trocados um pelo outro:

```
PRISMA        nenhuma junta NO'|FILL empilhada
VAO DE PORTA  nenhum bloco dentro do vazio fisico
```

O vão é medido na convenção vertical **do MOTOR** (`_course_z_band` /
`_opening_active_in_course_band`) — a mesma que decide quais fiadas o solver
esvazia. `INV-NODEFILL-032` é o CONTROLE: resolve a mesma planta SEM abertura
e confere que o medidor acusa mesmo, para os outros dois não passarem por
engano.

No código anterior (`2594f6ff`): **19 failed, 4 passed**. Neste: **23 passed**.
Em `030`, o que falha antes é o assert de PRISMA — o de vão de porta já
passava, o que confirma que o CR corrige prisma **sem** introduzir bloco no
vão.

## Arquivos alterados

```
PRODUCAO
  (nenhum)

TESTES
  tests/test_block_node_fill_joint.py            +3 testes (item 12)

DOCUMENTACAO
  docs/BLOCK_NODE_FILL_JOINT_FECHAMENTO.md       (este arquivo)
  nuvem/REGRAS_MODULACAO_BLOCOS.md               secao 32

LABORATORIO (so' leitura do motor)
  nuvem/benchmark/diagnostics_block_node_fill_joint/
      run_nf_door_table.py  run_nf_door_volume.py  run_nf_z_origin.py
      out_nf_door_table_{before_HEAD,after}.json
      out_nf_door_volume_{before_HEAD,after}.json
      out_nf_z_origin_{before_HEAD,after}.json
```

## Veredito

```
PILOTO PRISM = 0 ......................... PASSA   (14 -> 0)
TGD PRISM nao piorou vs 318 .............. PASSA   (318, identico)
TP1 PRISM nao piorou vs 169 .............. PASSA   (169, identico)
same-band = 0 ............................ PASSA
alignment_conflicts = 0 .................. PASSA
determinismo = 1 fingerprint ............. PASSA
L/T/X delta ZERO ......................... PASSA
cobertura nao piorou vs o ponto anterior . PASSA
cross-band vs 48 ......................... PASSA   (48, identico)
compensadores vs 1114 .................... PASSA   (1114, identico)
door_void_violations nao piorou .......... PASSA   (290 / 348 / 0)
jamb_exceptions nao piorou ............... PASSA
performance .............................. PASSA
OPENING_BLOCK_INSIDE_DOOR TGD <= 45 ...... ** NAO PASSA como medido hoje (49) **
                                              REAL: 5 antes, 5 depois
```

```
NECESSITA AJUSTE
```

**Um único gate falha, e o ajuste que ele pede não é no motor.** Está
provado, por três medições independentes, que:

1. a fiada 11 do motor começa **exatamente** na verga (221,00 cm) —
   sobreposição **0,00 cm**, nenhum bloco no vazio da porta;
2. o material físico dentro das portas **diminuiu** (−5,00 cm, −5,00 cm²);
3. com uma origem vertical consistente, este CR dá **5 = 5** contra o ponto
   anterior, em `INSIDE_DOOR` e em toda métrica de abertura e cobertura.

O ajuste é uma função em `nuvem/benchmark/extract/from_solver.py`, fora do
escopo do item 8, e move quatro códigos rastreados por `baseline.json` em
dois projetos. **Parei e relatei, como o item 8 manda.** A correção está
medida e pronta; basta autorizar (`CR-BENCH-Z-ORIGIN`) — e com ela aplicada
este CR passa TODOS os gates.

**NENHUM MERGE FOI FEITO.**
