# CROSS-AUDIT FINAL — CR-BLOCK-DETERMINISM

> CONTA 3, auditoria independente da finalização da CONTA 1.
> **PRODUÇÃO ALTERADA: ZERO.** Nenhuma branch da CONTA 1 foi tocada,
> nenhum baseline foi atualizado, nenhum merge foi feito.
> Toda a escrita desta fase ficou em
> `nuvem/benchmark/diagnostics_block_determinism_final_cross_audit/` e
> neste arquivo.

## Git

```
origin/main                                              21add6ec1f6cad220bdf3ff8651adb90b63d6e1b   CONFERE
origin/claude/cr-block-determinism-finalization-chkixk   14b42e6f57fc71230d559ab1aca49f7572a10bf1   CONFERE
branch de auditoria: claude/cr-block-determinism-final-cross-audit
  base                14b42e6f (HEAD da CONTA 1)
  merge de main       21add6ec  ->  228d68afe7274e7f25519cd3fb4759d98584c182
```

Os dois SHAs pedidos batem exatamente. O merge da `main` foi feito com
`git merge` normal (sem rebase, sem force-push) e **não gerou nenhum
conflito**: a interseção entre os arquivos tocados pelos dois lados é
VAZIA (a `main` traz só `nuvem/benchmark/golden/**`,
`nuvem/benchmark/tools/**`, `docs/GOLDEN_BENCHMARK.md`,
`docs/REFERENCE_CORPUS.md` e `tests/test_golden_benchmark.py`).
Nenhum conflito em `wall_stepper.py` nem em qualquer outro arquivo de
produção — não houve nada a classificar na seção 3 da missão.

### TRÊS pontos de medição, não dois — achado que muda a leitura do CR

A `main` **não contém o wall graph**. `git diff cb9ef99 origin/main --
nuvem/core/` mostra que `origin/main` tem **253 linhas a MENOS** em
`nuvem/core/engine/wall_pairing.py`. A branch da CONTA 1 carrega, portanto,
DUAS mudanças de produção que ainda não estão na `main`:

| ponto | sigla | produção | SHA |
|---|---|---|---|
| `origin/main` | **MAIN** | sem wall graph, sem finalização | `21add6ec` |
| pai da finalização | **+GRAFO** | MAIN + `wall_pairing.py` (wall graph canônico) | `cb9ef99` |
| HEAD da auditoria | **+FINAL** | +GRAFO + `wall_stepper.py` (esta CR) | `228d68af` |

Toda medição abaixo é feita nos três pontos. A CONTA 1 comparou só
+GRAFO → +FINAL, e por isso atribuiu à finalização metade do custo real de
mesclar a branch.

## Integração com o Reference Corpus

Merge limpo. `tests/test_golden_benchmark.py` (90 testes) passa integralmente
sobre o código da finalização. `tools/run_reference_corpus.py --all` roda
sem adaptação. Nenhuma referência/baseline foi regravada; os artefatos
regeráveis (`score.json`, `reports/*.txt`) que a rodada produziu foram
restaurados com `git checkout` — `git status` fica limpo.

## Determinismo — objetivo 1: CONFIRMADO

Bateria reescrita do zero (`lib_xa.py`, `variants_xa.py`,
`run_xa_variants.py`), sem reusar `lib_det`/`lib_final`/`lib_cross`.
**31 entradas por projeto**: baseline + 20 permutações (reversed,
15 shuffles, 2 ordenações geométricas, 2 shuffles dentro da orientação)
+ 10 reversões de endpoint (5 subconjuntos × {ingênua, geométrica}).

Fingerprints por camada, **contando só as variantes que descrevem o mesmo
prédio físico**:

| projeto | variantes | válidas | camadas com 1 fingerprint |
|---|---|---|---|
| `torre_easy_lo_r00_tgd` | 31 | **31** | **10/10 + global = 1** |
| `torre_easy_lo_r00_tp1` | 31 | **31** | **10/10 + global = 1** |
| `piloto_sintetico_2x2` | 31 | 26 | **10/10 + global = 1** |

Em TGD e TP1 as 31 variantes — **incluindo todas as reversões de
endpoint** — colapsam num único fingerprint global. Não há grupo excluído.

### Controle: a bateria não é vazia

A MESMA bateria, rodada nos pontos anteriores (`piloto_sintetico_2x2`,
26 variantes válidas):

| camada | MAIN | +GRAFO | +FINAL |
|---|---|---|---|
| `input_wall_geometry` | 1 | 1 | 1 |
| `node_positions` / `node_types` / `node_arms` | 1 | 1 | 1 |
| `wall_end_to_node` canônico | 1 | 1 | 1 |
| `midspan_crossings` | **4** | 1 | 1 |
| `physical_ties` | **21** | 1 | 1 |
| `physical_standard_fill` | **25** | **6** | 1 |
| `physical_opening_repair_fill` | **24** | **6** | 1 |
| `physical_block_layouts` | **26** | **6** | 1 |
| `global_result` | **26** | **6** | **1** |

E em `torre_easy_lo_r00_tgd` (31 variantes válidas, todas as reversões
incluídas):

| camada | MAIN | +GRAFO | +FINAL |
|---|---|---|---|
| `input_wall_geometry` | 1 | 1 | 1 |
| `node_positions` | **25** | 1 | 1 |
| `node_types` | **26** | 1 | 1 |
| `node_arms` | **26** | 1 | 1 |
| `wall_end_to_node` canônico | **26** | 1 | 1 |
| `midspan_crossings` | 1 | 1 | 1 |
| `physical_ties` | **22** | **2** | 1 |
| `physical_standard_fill` | **26** | **6** | 1 |
| `physical_opening_repair_fill` | **22** | **4** | 1 |
| `physical_block_layouts` | **26** | **6** | 1 |
| `global_result` | **26** | **6** | **1** |

**O "6 fingerprints → 1" que a CONTA 1 relatou para o TGD está
CONFIRMADO**, com bateria e métrica independentes. E o
`physical_ties` = 2 no ponto +GRAFO confirma também a terceira causa que
ela descreveu: a peça ASSIMÉTRICA do X (`B34` da degradação) saía
fisicamente espelhada conforme o sentido de desenho — é diferença real de
peça, não artefato de `rotation_deg` (a chave desta auditoria identifica a
peça pelo CONJUNTO de células em coordenadas de mundo, então uma peça
simétrica virada 180° tem a MESMA chave; só a assimétrica muda).

Na `main` cada uma das entradas válidas produz um prédio DIFERENTE (26 de
26 no piloto, 26 de 31 no TGD). O wall graph resolve o grafo e a maior
parte das peças de amarração; a finalização resolve o preenchimento e o
resto das amarrações. As duas metades são necessárias — nenhuma sozinha
entrega determinismo.

## Validade das variantes — a reversão de endpoint

Medida na PLANTA (`run_xa_validity.py`), com tolerância física de
0,05 cm, comparando eixo esticado + posição de mundo/largura/peitoril/verga
de cada abertura:

| projeto | `walls_already_extended` | reversão INGÊNUA | reversão GEOMÉTRICA |
|---|---|---|---|
| `piloto_sintetico_2x2` | **False** | **INVALID** — vãos deslocados **14,00 cm** | **VALID** |
| `torre_easy_lo_r00_tgd` | True | VALID | VALID |
| `torre_easy_lo_r00_tp1` | True | VALID | VALID |

**A afirmação da CONTA 1 está CORRETA e o número bate exatamente.** Medido
independentemente: no piloto o motor roda
`extend_wall_ends_to_junctions(JUNCTION_FACE_SEARCH_FT)` e **todo** eixo
fica 14,0 cm mais longo que o do `input.json` (7 cm por ponta = meia
espessura). A variante antiga reparametriza `t' = L_input − t` e joga cada
vão 14 cm fora do lugar; uma das reversões aleatórias chega a 700,14 cm de
deslocamento e 90 cm de diferença de dimensão, porque mistura paredes
revertidas e não revertidas.

Mas a auditoria não parou em "a variante é inválida". Foi construída a
reversão **fisicamente equivalente** (`t' = L_esticado − t`), depois de
provar que o eixo esticado é invariante à inversão de pontas (desvio máximo
medido: **0,00 cm** nos três projetos). Com ela, as 5 reversões do piloto
passam a ser VÁLIDAS **e convergem para o mesmo fingerprint do baseline**.

> Classificação: `INVALID_METAMORPHIC_VARIANT` para as 5 reversões ingênuas
> do piloto; `VALID_METAMORPHIC_VARIANT` para as outras 26 do piloto e para
> as 31 de TGD e TP1.

## Regressão PRISM 7 → 14 — REPRODUZIDA, e maior do que o relatado

`PRISM_CONTINUOUS_JOINT` no `piloto_sintetico_2x2`, mesmo ponto de medição
do `tests/regression/test_benchmark_baselines.py`:

| ponto | PRISM_CONTINUOUS_JOINT | PRISM_JOINT_STACK |
|---|---|---|
| `baseline.json` (gravado em `f693dcf`, a criação do benchmark) | 7 | 1 |
| **MAIN** | **0** | **0** |
| **+GRAFO** | **7** | 1 |
| **+FINAL** | **14** | 2 |

O 7 → 14 da CONTA 1 está correto **como delta da finalização**. Mas o
`baseline.json` já estava desatualizado na direção BOA: a `main` de hoje
produz **0**. Contra o que de fato seria mesclado, a branch leva o piloto
de **0 para 14** — metade pelo wall graph (W011) e metade pela finalização
(W004).

## Os 7 novos casos — UMA causa, idêntica às 7 antigas

`run_xa_prism_diff.py`, uma linha por violação:

```
NOVAS pelo GRAFO   (+GRAFO menos MAIN):  W011 f0/f1 .. f6/f7, todas em t=34,50 cm
NOVAS pela FINAL   (+FINAL menos +GRAFO): W004 f0/f1 .. f6/f7, todas em t=34,50 cm
SUMIRAM pela FINAL: nenhuma
```

Os 7 casos novos são **a mesma parede, a mesma posição longitudinal, o
mesmo par de blocos, o mesmo desencontro**:

| campo | valor (idêntico nos 14 casos) |
|---|---|
| PROJECT | `piloto_sintetico_2x2` |
| WALL | `W004` (novos) / `W011` (antigos) |
| COURSE_A / COURSE_B | fiadas consecutivas, 0/1 … 6/7 |
| JOINT_POSITION_A / _B | **34,50 cm / 34,50 cm** |
| DISTANCE | **0,00 cm** |
| BLOCK_LEFT / RIGHT (fiada par) | `B34` (peça de nó) \| `B19` (preenchimento) |
| BLOCK_LEFT / RIGHT (fiada ímpar) | `B19` (preenchimento) \| `B39` (preenchimento) |
| NODE_TYPE próximo | `L_CORNER` |
| DISTANCE_TO_NODE | 27,5 cm |
| REASON | junta PEÇA DE NÓ × PREENCHIMENTO não entra na lista de juntas a evitar |

**Resposta ao item 9: causa ÚNICA.** Não são 7 causas diferentes, e é a
mesma causa das 7 antigas.

### Correção factual ao relatório da CONTA 1

A CONTA 1 escreveu que "W004 e W011 são **geometricamente idênticas**
(364 cm, 14 cm, **horizontais**)". Medido:

```
W011  p0=(-7, 700)  p1=(357, 700)   HORIZONTAL  L=364  t=14  1 vão (100–220, peitoril 90)
W004  p0=(350, -7)  p1=(350, 357)   VERTICAL    L=364  t=14  1 vão (120–200, peitoril 0)
```

São **congruentes** (mesmo comprimento e espessura), não idênticas:
orientações diferentes e vãos diferentes. A explicação "as duas passam a
receber o mesmo layout" não se sustenta como escrita — o que de fato
acontece é que a finalização **muda o layout da fiada ÍMPAR de W004**:

```
+GRAFO  f1:  B34(15–49) B39(50–89) C09(90–99) B19(100–119) …   1ª junta em 49,50
+FINAL  f1:  B19(15–34) B39(35–74) B34(75–109) C09(110–119) …  1ª junta em 34,50  <-- colide
        f0 (em todos os pontos): B34(0–34) | B19(35–54) …      junta em 34,50
```

O mecanismo é o mesmo de W011, mas o caminho é outro. O diagnóstico da
CONTA 1 está certo na CAUSA e errado na descrição da geometria.

## Causa-raiz independente — junta NÓ/FILL

**HIPÓTESE DA CONTA 1: CONFIRMADA, e provada por instrumentação.**

`_layout_internal_joint_positions_cm` (wall_stepper.py:3184) devolve
`for i in range(n-1)` — só as juntas **entre dois blocos do mesmo
layout**. A junta de FRONTEIRA do trecho (entre o que vem antes e o
primeiro bloco do preenchimento) não existe na lista, por construção.

Essa é a única fonte de `course_a_joint_positions_cm` (wall_stepper.py:5314
e 5321) — a lista que a Fiada B recebe como `avoid_positions_cm` — e é
também a única fonte do `_count_joint_coincidences_cm` que alimenta
`alignment_conflicts` (wall_stepper.py:5375).

Instrumentação em memória (`run_xa_nodefill.py`, monkeypatch em
`core.engine.wall_stepper`, nenhum arquivo tocado), no piloto:

```
chamadas de layout                                        436
juntas de FRONTEIRA distintas               14,5  34,5  74,5  94,5  199,5  219,5
  ... que COINCIDEM com uma junta interna         34,5  74,5  94,5  219,5
alignment_conflicts reportados pelo motor                   0
PRISM_CONTINUOUS_JOINT reais                               14
```

A junta em `t = 34,5` existe, coincide, e o gate não a vê. É exatamente
o que a hipótese diz.

**Confirmação cruzada, por um caminho que a CONTA 1 não usou:** a própria
auditoria de amarração do motor JÁ enxerga o defeito. `wall_bond_audits`
de W004/W011 traz

```
CONTINUOUS_VERTICAL_JOINT: junta corrida em X~34.5cm, em 8 fiadas (0..7)
penalty 50000.0
```

A informação existe no motor — ela só não chega à busca de layout nem ao
gate `alignment_conflicts`.

### Três medidores discordam sobre esta junta

| medidor | veredito |
|---|---|
| `validators/validate_prism.py` (o gate do `tests/regression`) | **PRISM_CONTINUOUS_JOINT** — erro nível 1 |
| `audit_wall_bond_quality` (o motor) | **CONTINUOUS_VERTICAL_JOINT**, penalty 50000 |
| taxonomia do CR-BLOCK-01 (`diagnostics_block_prisma`) | **UNCLASSIFIED_RULE_CONFLICT** (7 → 14), não `FORBIDDEN` |
| `alignment_conflicts` (o gate do solver) | **não vê nada** (0) |

A taxonomia do CR-BLOCK-01 classifica como "conflito de regra não
resolvido" porque um dos lados é peça de nó, que a seção 5 manda repetir
na mesma posição. Isso é uma pendência de DOCUMENTO (qual regra vence),
registrada e não inventada — mas não muda o fato de que o gate de
regressão reprova.

## CR-BLOCK-01

Medido com o instrumento do próprio CR-BLOCK-01
(`diagnostics_block_prisma/run_baseline.py`), nos três pontos:

| métrica | MAIN | +GRAFO | +FINAL | classificação |
|---|---|---|---|---|
| **same-band forbidden** | **0** | **0** | **0** | PRESERVADO |
| **alignment_conflicts** | **0** | **0** | **0** | PRESERVADO (mas ver acima: é um gate cego para a junta nó/fill) |
| cross_band forbidden | 33 | 57 | **60** | ver abaixo |
| compensadores consecutivos | 1210 | 1143 | **1168** | ver abaixo |

Os números que a missão cita (57 → 60 e 1143 → 1168) foram reproduzidos
exatamente como delta +GRAFO → +FINAL.

- **cross_band 57 → 60**: `REAL_REGRESSION` (pequena, +3). É a mesma
  família de defeito da regressão de prisma — coincidência de junta entre
  fiadas de bandas diferentes. Contra a `main` o salto real é 33 → 60, e
  **24 dos 27 vêm do wall graph**, não desta CR. Cai na mesma correção.
- **compensadores consecutivos 1143 → 1168**: `REAL_REGRESSION` no delta
  da finalização (+25), mas **contra a `main` é MELHORIA** (1210 → 1168).
  Por projeto: TP1 903 → 795 → 805 (melhora forte, piora um pouco);
  TGD 279 → 318 → 333 (piora nos dois passos). Não bloqueia este CR,
  mas TGD merece acompanhamento.
- **collisions do TGD 1034 → 1051** (+17): achado NÃO relatado pela
  CONTA 1. Diff par a par: 122 pares novos, 103 desaparecidos — é
  **churn**, não um modo de falha novo, num projeto que já tem 1034
  colisões e 200 `intersection_failures` na `main`. `POSITION_OVERLAP` do
  validador fica em 29 nos três pontos. Classificação: `DEBT` /
  `PRE_EXISTING_VARIATION` — registrar, não bloquear.

## D6 — mesmo ponto de medição

`pieces / non_modular / collisions / intersection_failures /
alignment_conflicts / door_void_violations / B39 / B34 / B54 / B19 / C09 /
C04`, nos três pontos, na ordem baseline: ver
`run_xa_d6` embutido em `out_xa_*.json` e a tabela em
`nuvem/benchmark/diagnostics_block_determinism_final_cross_audit/`.

**A pergunta do item 14 — "as categorias de L/T/X realmente têm delta
ZERO?" — tem resposta SIM, para o delta da finalização, nos três
projetos:**

| `placement_reason` | TGD +GRAFO→+FINAL | TP1 +GRAFO→+FINAL | piloto |
|---|---|---|---|
| `L_CORNER` | 969 → 969 | 542 → 542 | 32 → 32 |
| `L_CORNER_DEGRADED` | 85 → 85 | 104 → 104 | — |
| `T_INTERSECTION_MAIN` | 509 → 509 | 711 → 711 | — |
| `T_INTERSECTION_INCOMING` | 454 → 454 | 641 → 641 | — |
| `T_INTERSECTION_INCOMING_DEGRADED` | 354 → 354 | 433 → 433 | — |
| `T_INTERSECTION_DEGRADED_L` | 434 → 434 | — | 32 → 32 |
| `X_INTERSECTION` | 128 → 128 | 374 → 374 | — |
| `X_INTERSECTION_DEGRADED` | 8 → 8 | 68 → 68 | 8 → 8 |
| `STANDARD_FILL` | 7207 → **7224** | 13853 → **13837** | 564 → **568** |
| `OPENING_REPAIR_FILL` | 423 → **426** | 1282 → **1326** | 144 → **140** |

**Todo delta restante da finalização está em `STANDARD_FILL` e
`OPENING_REPAIR_FILL`** — exatamente o que a CONTA 1 afirmou.
(Contra a `main`, L/T/X mudam — `X_INTERSECTION` 127→128,
`L_CORNER` do TP1 538→542 etc. — mas isso é o wall graph.)

## Aberturas

| métrica | MAIN | +GRAFO | +FINAL | veredito da FINALIZAÇÃO |
|---|---|---|---|---|
| TGD `OPENING_BLOCK_INSIDE_DOOR` | 43 | 43 | 44 | **piorou (+1)** |
| TGD `OPENING_BLOCK_CROSSES_JAMB` | 147 | 148 | 147 | melhorou (−1) |
| TGD `door_void_violations` | 290 | 290 | 290 | igual |
| TGD `jamb_exceptions` | 172 | 172 | 172 | igual |
| TGD `OPENING_REPAIR_FILL` | 432 | 423 | 426 | +3 |
| TP1 `OPENING_BLOCK_CROSSES_JAMB` | 168 | 154 | 154 | igual (melhora veio do grafo) |
| TP1 `blocks_inside_opening` | 168 | 154 | 154 | igual |
| TP1 `door_void_violations` | 348 | 348 | 348 | igual |
| TP1 `jamb_exceptions` | 44 | 52 | 52 | igual (piora veio do grafo) |
| TP1 `OPENING_REPAIR_FILL` | 1301 | 1282 | **1326** | **piorou (+44)** |
| piloto `OPENING_MISSING_COUNTER_LINTEL` | 4 | 4 | 4 | igual |
| piloto `OPENING_REPAIR_FILL` | 140 | 144 | 140 | melhorou (−4) |

Sem esconder atrás de "dentro da faixa histórica": a finalização
**piora** `OPENING_BLOCK_INSIDE_DOOR` do TGD em 1 e o volume de
`OPENING_REPAIR_FILL` do TP1 em 44 peças; **melhora**
`OPENING_BLOCK_CROSSES_JAMB` do TGD em 1; deixa `door_void_violations`
e `jamb_exceptions` intactos nos três projetos. Nenhum desses deltas é
bloqueante, e a mudança **é** causada pela CR atual (é ela que mexe no
preenchimento e, por consequência, na região de reparo).

## L/T/X

Delta ZERO em todas as categorias de nó, nos três projetos, para o delta
da finalização (tabela acima). Além disso, `intersection_failures` fica
igual nos três pontos (TGD 200, TP1 0, piloto 0) e o `physical_ties`
colapsa para 1 fingerprint nas 31 variantes.

## Ordem oficial

Verificada por TESTE sobre plantas sintéticas construídas na auditoria
(`run_xa_order.py`), não por leitura de código. **Todos os invariantes
passam:**

```
horizontais antes das verticais                                 OK
H: cima -> baixo                                                OK
H: empate esquerda -> direita                                   OK
V: baixo -> cima  (criterio PRINCIPAL)                          OK
V: empate esquerda -> direita                                   OK
inclinadas por angulo canonico, depois posicao                  OK
H antes de V antes de INCLINADA                                 OK
ordem invariante a 40 permutacoes da lista        1 ordem distinta em 40
ordem invariante a inversao de endpoints                        OK
paredes na MESMA faixa e MESMO x_min: ordem estavel             OK
nenhum desempate final por wall_idx                             OK
```

A correção que a CONTA 1 fez na ETAPA 2 (verticais: Y como principal, X
como desempate) está de acordo com o enunciado oficial do usuário, e a
troca do desempate `wall_idx` por `wall_processing_geom_key` remove a
última dependência de ordem de entrada.

## `continuous_first`

```
DEFAULT_OPENING_STRATEGY == OPENING_STRATEGY_CONTINUOUS_FIRST == "continuous_first"
```

Único default de produção. `split_first` só é alcançável (a) por parâmetro
explícito `opening_strategy=` e (b) pela degradação limitada de
`solve_wall_free_fill` (wall_stepper.py:5100-5130 / 5405-5432), que
reintroduz as fronteiras de abertura **apenas dos trechos que falharam**
(`variant_failed_spans`) e registra cada caso em `continuity_degraded`.
**Não há caminho silencioso.** O pipeline conceitual pedido
(L/T/X → parede completa → fill contínuo → prisma → abertura → remoção →
reparo local → validação) está implementado nessa ordem.

## Reference Corpus

`python3 nuvem/benchmark/tools/run_reference_corpus.py --all` sobre o
código da finalização:

```
OVERALL: CRITICAL_REGRESSION_PRESENT
- piloto_sintetico_2x2: PRISM_CONTINUOUS_JOINT 7 -> 14
- torre_easy_lo_r00_tgd: COVERAGE_MISSING_ROW 265 -> 293
- torre_easy_lo_r00_tgd: COVERAGE_ROW_MOSTLY_EMPTY 171 -> 187
- torre_easy_lo_r00_tp1: COVERAGE_MISSING_ROW 16 -> 18

matriz projeto x metrica:
  tgd    prism IMPROVED  openings IMPROVED  L/T/X IMPROVED  compensators REGRESSED
  tp1    prism IMPROVED                                     compensators IMPROVED
  piloto prism REGRESSED                                    compensators REGRESSED
```

**O Reference Corpus DETECTA a regressão de prisma corretamente** e faz
exatamente o que o item 19 dele pede: não deixa a média boa (prisma
melhorando forte em TGD e TP1) esconder a regressão crítica do piloto.
Nenhuma referência ou baseline foi atualizada.

## Baselines

| projeto | código | baseline | MAIN | +GRAFO | +FINAL | classificação da CONTA 1 | classificação desta auditoria |
|---|---|---|---|---|---|---|---|
| tgd | `COVERAGE_MISSING_ROW` | 265 | 265 | 293 | 293 | BASELINE_STALE_SAFE_TO_REFRESH | **REAL_REGRESSION do WALL GRAPH** (a `main` bate o baseline exatamente; a finalização não muda nada) |
| tgd | `COVERAGE_ROW_MOSTLY_EMPTY` | 171 | 171 | 181 | 187 | BASELINE_STALE_SAFE_TO_REFRESH | **REAL_REGRESSION**, 10 do grafo + 6 da finalização |
| tp1 | `COVERAGE_MISSING_ROW` | 16 | 16 | 18 | 18 | BASELINE_STALE_SAFE_TO_REFRESH | **REAL_REGRESSION do WALL GRAPH** |
| piloto | `PRISM_CONTINUOUS_JOINT` | 7 | **0** | 7 | 14 | REAL_QUALITY_REGRESSION | **REAL_QUALITY_REGRESSION**, e maior: 0 → 14 contra a `main` |

**DISCORDÂNCIA com a CONTA 1 nos três primeiros.** O argumento
"BASELINE_STALE" foi sustentado mostrando que, no código anterior, essas
métricas variavam entre as 24 ordens e o `baseline.json` gravou uma delas.
Isso é verdade e é um bom argumento — mas ele explica no máximo a faixa de
variação, não o salto. Medido: nesses três códigos a `main` de hoje
reproduz o `baseline.json` **exatamente** (265/265, 171/171, 16/16). Se o
baseline fosse "uma amostra de uma loteria", ele não bateria na mosca nos
três. A leitura desta auditoria é que os três são regressão de cobertura
real introduzida pelo **wall graph** (`wall_pairing.py`), não staleness — e
que `COVERAGE_ROW_MOSTLY_EMPTY` do TGD ainda ganha +6 da finalização.

Isso **não** transforma o CR-BLOCK-DETERMINISM em reprovado: a maior parte
é dívida do wall graph, que foi aprovado por cross-audit anterior. Mas
proíbe o refresh de baseline como se fosse rotina — o refresh gravaria uma
piora de cobertura como se fosse o novo normal.

**NENHUM baseline foi atualizado nesta auditoria.**

## Testes

| suíte | resultado |
|---|---|
| `tests/test_block_pipeline_determinism.py` | **52 passed** |
| `tests/test_block_graph_determinism.py` | **27 passed** |
| `tests/test_block_bonding.py` | **32 passed** |
| `tests/test_golden_benchmark.py` | **90 passed** |
| `tests/test_script.py` | **260 passed** |
| `tests/regression` | **110 passed, 3 failed** |
| `tests/ -m "not slow"` | **574 passed, 13 deselected** |
| árvore inteira (`tests/`) | **584 passed, 3 failed** em 146 s |

(A CONTA 1 relatou 494 passed; com a `main` mesclada entram os 90 testes do
Golden Benchmark, daí 584.)

### As 3 falhas, classificadas individualmente

Todas as três são o mesmo teste parametrizado,
`tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline`:

| # | projeto | código | classificação |
|---|---|---|---|
| 1 | `piloto_sintetico_2x2` | `PRISM_CONTINUOUS_JOINT` 7 → 14 | **REAL_REGRESSION** — 7 do wall graph, 7 desta CR. Causa-raiz provada. **BLOQUEIA.** |
| 2 | `torre_easy_lo_r00_tgd` | `COVERAGE_MISSING_ROW` 265 → 293, `COVERAGE_ROW_MOSTLY_EMPTY` 171 → 187 | **REAL_REGRESSION**, majoritariamente do wall graph (28 e 10 dos 16). Não é `STALE_BASELINE`. |
| 3 | `torre_easy_lo_r00_tp1` | `COVERAGE_MISSING_ROW` 16 → 18 | **REAL_REGRESSION do wall graph**; a finalização não altera este número. |

Nenhuma é `TEST_BUG` e nenhuma é `UNKNOWN`.

## Arquivos modificados

```
PRODUCTION FILES MODIFIED = ZERO
```

`git diff 228d68af HEAD -- nuvem/core/` é vazio. A auditoria criou apenas:

```
docs/BLOCK_DETERMINISM_FINAL_CROSS_AUDIT.md                        (este arquivo)
nuvem/benchmark/diagnostics_block_determinism_final_cross_audit/   (laboratorio novo)
    lib_xa.py  variants_xa.py
    run_xa_variants.py  run_xa_validity.py  run_xa_order.py
    run_xa_nodefill.py  run_xa_prism_diff.py
    out_xa_*.json
```

Nenhum `baseline.json`, nenhum `reference.json`, nenhum `out_*.json` de
outra pasta de diagnóstico, nenhuma branch da CONTA 1.

## Proposta do menor fix seguro — SEM IMPLEMENTAR

**Função exata:** `solve_wall_free_fill` (`nuvem/core/engine/wall_stepper.py`),
nos dois pontos que hoje fazem
`seg_joints_cm = _layout_internal_joint_positions_cm(layout, seg_start_cm)`
(linhas ~5314 e ~5342) e no ponto do gate (linha ~5375).

**Informação que está faltando:** a junta de FRONTEIRA do trecho, quando o
que está do outro lado dela é uma **peça de nó** — não a ponta livre do
eixo e não a borda de um vão.

**Como representar a junta nó/fill:** ela já é derivável do que a função
calcula, sem estrutura nova. No ramo `kind_left == "WALL_START"`, quando
`node_candidates_by_wall_end.get((wall_idx, 0, course))` **não é None**,
o motor faz `seg_start_cm = border + BLOCK_JOINT_CM`; o centro da junta é
`border + BLOCK_JOINT_CM/2` = `seg_start_cm - BLOCK_JOINT_CM/2`. Idem em
`MIDSPAN_HI` (`seg_start_cm = t_left + BLOCK_JOINT_CM`) e, espelhado, em
`WALL_END` / `MIDSPAN_LO` (`seg_end_cm + BLOCK_JOINT_CM/2`).
**O discriminador já existe e já está calculado**: `leading_is_open` /
`trailing_is_open` são `False` exatamente nesses casos e `True` quando a
fronteira é ponta aberta ou vão. Sugestão: uma função pura
`_segment_node_boundary_joints_cm(seg_start_cm, seg_end_cm, leading_is_open,
trailing_is_open, leading_is_node, trailing_is_node)`, alimentada por dois
flags novos locais (`leading_is_node`/`trailing_is_node`) definidos nos
mesmos `if` que já existem.

**Qual algoritmo deveria enxergá-la:**
1. `course_a_joint_positions_cm` — para a Fiada B receber a junta no
   `avoid_positions_cm` de `_pier_layout_avoiding_joints`;
2. `_count_joint_coincidences_cm` do gate — para `alignment_conflicts`
   deixar de ser cego (hoje reporta 0 com 14 violações reais);
3. `own_family_joint_positions_cm` — para as variantes seguintes da mesma
   família.
   Nada muda em `_layout_internal_joint_positions_cm` (que continua
   respondendo "juntas internas deste layout" — mudar o contrato dela
   afetaria os outros chamadores, entre eles `_layout_min_joint_stagger_cm`).

**Testes que precisam nascer:**
- unitário de `_segment_node_boundary_joints_cm`: fronteira de nó devolve
  a junta, fronteira de vão e ponta livre devolvem vazio;
- regressão dirigida: `piloto_sintetico_2x2` W004 e W011,
  `PRISM_CONTINUOUS_JOINT == 0` nas 8 fiadas;
- invariante permanente: para todo trecho com fronteira de nó, a junta
  `seg_start_cm − BLOCK_JOINT_CM/2` aparece na lista que a fiada oposta
  recebe (o oposto exato do que `run_xa_nodefill.py` mede hoje);
- invariante de gate: se existe `PRISM_CONTINUOUS_JOINT` cuja junta
  coincide com uma fronteira de nó, `alignment_conflicts` **não** pode
  ser 0;
- as 52 invariantes de `test_block_pipeline_determinism.py` continuam
  passando (o fix não pode reintroduzir dependência de ordem — a lista
  nova é derivada de `seg_start_cm`, que já vive na grade de snap).

**Risco de afetar L/T/X:** BAIXO. Nenhuma peça de nó é reposicionada; só
a busca de layout do preenchimento ganha uma posição a evitar. As
categorias L/T/X têm delta ZERO na finalização, e o fix não toca em
`solve_l_corner`/`solve_t_intersection`/`solve_x_intersection`.

**Risco de afetar abertura:** MÉDIO. `OPENING_REPAIR_FILL` recalcula em
cima do preenchimento; mudar o layout de um trecho encostado num nó pode
mudar a região de reparo. Precisa medir `OPENING_BLOCK_INSIDE_DOOR`,
`OPENING_BLOCK_CROSSES_JAMB` e `door_void_violations` nos 3 projetos.
**A exceção 11.8 (C04/C09/B19 encostado em vão) NÃO pode ser afetada** —
por isso a junta só entra quando a fronteira é de NÓ, nunca de vão.

**Risco de aumentar compensadores:** MÉDIO-ALTO, e é o risco principal.
Restringir mais o espaço de busca da Fiada B é exatamente o que faz o
solver cair em composições com compensador. Indício favorável: no piloto,
o layout que a fiada ímpar de W004 tinha na `main` (`B34(15–49) B39(50–89)
C09(90–99) B19(100–119)`) já é sem colisão e existe dentro do catálogo —
o fix deve reencontrá-lo. Indício desfavorável: TGD já vai de 279 para 333
compensadores consecutivos. **Medir `COMPENSATOR_CONSECUTIVE`,
`COMPENSATOR_EXCESS_IN_RUN` e `COMPENSATOR_VERTICAL_STRIP` nos 3 projetos
antes e depois é obrigatório.**

**Escopo:** é mudança na REGRA DE AMARRAÇÃO, não na convenção de direção.
Merece CR próprio (`CR-BLOCK-NODE-FILL-JOINT`), como a CONTA 1 propôs.

## Veredito

```
DETERMINISM ....... APROVADO
QUALITY ........... NECESSITA AJUSTE
MERGE ............. BLOQUEADO
```

**DETERMINISMO — APROVADO.** Reproduzido de forma independente, com
bateria reescrita do zero e 31 entradas por projeto. TGD e TP1: 31/31
variantes válidas, 1 fingerprint em todas as 10 camadas e no global.
Piloto: 26/26 válidas, 1 fingerprint em todas as camadas. O controle nos
pontos anteriores (piloto 26 → 6 → 1; TGD 26 → 6 → 1) prova que a bateria
detecta o problema que diz ter sido resolvido, e reproduz o "6 → 1" que a
CONTA 1 relatou. A ordem oficial das paredes e o
`continuous_first` foram verificados por teste próprio e passam. A
explicação da CONTA 1 sobre a variante `endpoint_reversal` é correta, o
número (14 cm) confere, e a auditoria foi além: construiu a reversão
fisicamente válida e ela também converge.

**QUALIDADE — NECESSITA AJUSTE.** A regressão de prisma é real,
reproduzível, tem causa-raiz única e provada, e o gate do solver
(`alignment_conflicts`) é cego para ela. Contra o que seria de fato
mesclado (`origin/main`), o piloto vai de **0 para 14** violações
`PRISM_CONTINUOUS_JOINT` — o dobro do relatado — e o `COVERAGE_*` de TGD e
TP1 regride de verdade, não por baseline velho.

**Divisão de responsabilidade, medida:**

| item | wall graph (`wall_pairing.py`) | finalização (`wall_stepper.py`, esta CR) |
|---|---|---|
| piloto PRISM 0 → 14 | +7 (W011) | +7 (W004) |
| tgd `COVERAGE_MISSING_ROW` 265 → 293 | +28 | 0 |
| tgd `COVERAGE_ROW_MOSTLY_EMPTY` 171 → 187 | +10 | +6 |
| tp1 `COVERAGE_MISSING_ROW` 16 → 18 | +2 | 0 |
| cross_band 33 → 60 | +24 | +3 |
| tgd collisions 1034 → 1051 | 0 | +17 |
| determinismo (piloto, fingerprints) | 26 → 6 | 6 → **1** |

**NENHUM MERGE FOI FEITO.** Parado antes, como pedido.
