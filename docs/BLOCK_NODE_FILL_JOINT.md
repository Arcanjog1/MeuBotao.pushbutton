# RELATÓRIO FINAL — CR-BLOCK-NODE-FILL-JOINT

> Produção alterada: **só** `nuvem/core/engine/wall_stepper.py`.
> `wall_pairing.py`, `continuous_modulation.py` e `geometry.py`: **intactos**.
> Nenhum `baseline.json` / `reference.json` / `reference_score.json` tocado.
> Nenhuma branch de auditoria tocada. **NENHUM MERGE FEITO.**

## Git

```
origin/main                                            21add6ec1f6cad220bdf3ff8651adb90b63d6e1b   CONFERE
origin/claude/cr-block-determinism-final-cross-audit   2594f6ff376212e5f24614241a0e1dd4b142b838   CONFERE
branch deste CR: claude/cr-block-node-fill-joint-9tv0kd, criada a partir de 2594f6ff
```

Três pontos de medição, os mesmos do cross-audit:

| sigla | SHA | o que é |
|---|---|---|
| **MAIN** | `21add6ec` | `origin/main` — sem wall graph, sem finalização |
| **HEAD** | `2594f6ff` | HEAD da auditoria (PR #7) — o ponto de partida deste CR |
| **DEPOIS** | esta branch | HEAD + esta correção |

MAIN e HEAD medidos em `git worktree` separados.

## Reprodução antes

Instrumento do cross-audit reproduzido em
`nuvem/benchmark/diagnostics_block_node_fill_joint/run_nf_trace.py`
(monkeypatch em memória de `_layout_internal_joint_positions_cm`, nenhum
arquivo de produção tocado), sobre `piloto_sintetico_2x2`:

```
chamadas de layout                                        436
juntas de FRONTEIRA distintas          14,5  34,5  74,5  94,5  199,5  219,5
  ... que coincidem com uma junta interna     34,5  74,5  94,5  219,5
alignment_conflicts reportados pelo motor                   0
PRISM_CONTINUOUS_JOINT reais                               14
PRISM_JOINT_STACK reais                                     2
```

Os números batem **exatamente** com os do cross-audit. Confirmado também
pelo score: `piloto_sintetico_2x2` no HEAD dá
`PRISM_CONTINUOUS_JOINT = 14`, `PRISM_JOINT_STACK = 2`, contra **0 e 0** na
`main`.

## W004

Parede vertical, 364 cm × 14 cm depois da extensão, `L_CORNER` nas duas
pontas. A fiada PAR recebe a peça de nó `B34` em 0–34 e o preenchimento
começa em 35 → junta física em **34,5 cm**. Na fiada ÍMPAR a finalização
trocou o layout:

```
HEAD  f1:  B19(15–34) B39(35–74) B34(75–109) C09(110–119) …  1ª junta interna em 34,50  <-- empilha
```

**DEPOIS: 0 violações.** A busca da fiada ímpar passa a receber 34,5 na
lista a evitar e reencontra uma composição sem coincidência.

## W011

Parede horizontal congruente (364 × 14), com janela. Mesmo mecanismo, mesma
posição (34,5 cm), mesmas 8 fiadas — a metade que veio do wall graph.
**DEPOIS: 0 violações**, sem que `wall_pairing.py` fosse tocado: a correção
é do lado do preenchimento e resolve as duas metades.

## Causa-raiz

`_layout_internal_joint_positions_cm` devolve `for i in range(n - 1)` — só
as juntas **entre dois blocos do mesmo layout**. A junta de FRONTEIRA do
trecho (contra o que vem antes do primeiro bloco / depois do último) não
existe nessa lista **por construção**. Quando esse vizinho é uma PEÇA DE
NÓ, a junta é tão física quanto qualquer outra, e a fiada oposta nunca
soube dela.

Como essa é a única fonte de `course_a_joint_positions_cm` e do
`_count_joint_coincidences_cm` que alimenta `alignment_conflicts`, o
defeito era invisível nos dois lugares ao mesmo tempo: a busca não evitava,
e o gate reportava zero.

**Achado adicional deste CR (não estava no cross-audit): o defeito tem DOIS
sentidos.** A Fiada A roda primeiro e também nunca veria a junta de nó da
Fiada B. Medido numa célula fechada sintética de 350 cm (4 × `L_CORNER`),
no código anterior: 4 violações, **2 de cada sentido**.

**Segundo achado: o defeito exige nó nas DUAS pontas.** Varredura de 150 a
600 cm, de 10 em 10, no código anterior:

```
L isolado / T isolado / X isolado   0 violações em TODOS os comprimentos
célula FECHADA                      4 violações em TODOS os comprimentos
grade 2x2 (topologia do piloto)     2 violações
```

Com uma ponta livre o preenchimento tem o meio-bloco (B19) para deslocar
meio módulo; com nó nas duas pontas o B19 é proibido (seção 2) e o trecho
fica sem folga. É por isso que o piloto — uma grade 2 × 2 — reprova.

## Implementação

Três funções PURAS novas em `wall_stepper.py`:

| função | o que faz |
|---|---|
| `_segment_node_boundary_joints_cm` | a junta de fronteira de UM trecho, dado `leading_is_node`/`trailing_is_node` |
| `_node_boundary_joints_backed_by_pieces_cm` | descarta a junta cuja peça o recorte da abertura derrubou |
| `_wall_node_boundary_joints_cm` | as juntas de nó da fiada OPOSTA, deduzidas só da geometria do nó |

Dois flags locais novos em `solve_wall_free_fill`
(`leading_is_node`/`trailing_is_node`), definidos nos MESMOS `if` que já
existiam. O contrato de `_layout_internal_joint_positions_cm` **não mudou**
(seus outros chamadores, entre eles `_layout_min_joint_stagger_cm`,
continuam intactos).

## Junta NODE|FILL

```
junta inicial = seg_start_cm - BLOCK_JOINT_CM / 2      (a peça de nó termina em `border`)
junta final   = seg_end_cm   + BLOCK_JOINT_CM / 2
```

**Discriminador (item 6 do CR — o cuidado crítico).** Só PEÇA DE NÓ:

```
WALL_START/WALL_END com `border` de nó   É NÓ
MIDSPAN_HI / MIDSPAN_LO                  É NÓ
OPENING_HI / OPENING_LO                  NÃO É  (abertura)
ponta livre de verdade                   NÃO É
rede de segurança (`oi_left is None`)    NÃO É   <-- aqui `leading_is_open`
                                                    TAMBÉM é False; é por
                                                    isso que a negação de
                                                    `*_is_open` não serve
```

A **exceção 11.8** (C04/C09/B19 encostado no vão PODE ficar alinhado entre
fiadas) não foi tocada — `OPENING_ALIGNED_EXEMPT_CODES` e o caminho de
isenção continuam idênticos.

**Onde a junta é propagada:**

1. `course_a_node_boundary_joints_cm` — a Fiada B recebe no `avoid_positions_cm`;
2. `own_family_node_boundary_joints_cm` — variantes seguintes da mesma família;
3. `opposite_node_joints_cm` — o sentido simétrico (a Fiada A evita a junta de nó da B);
4. `_recut_openings_and_repair` — o reparo local usa a mesma lista;
5. o gate — `node_boundary_conflicts` (ver abaixo).

## Prisma antes/depois

| métrica | MAIN | HEAD | **DEPOIS** |
|---|---|---|---|
| piloto `PRISM_CONTINUOUS_JOINT` | 0 | 14 | **0** |
| piloto `PRISM_JOINT_STACK` | 0 | 2 | **0** |
| tgd `PRISM_CONTINUOUS_JOINT` | 702 | 562 | **318** |
| tgd `PRISM_JOINT_STACK` | 46 | 39 | **21** |
| tp1 `PRISM_CONTINUOUS_JOINT` | 837 | 730 | **169** |
| tp1 `PRISM_JOINT_STACK` | 49 | 40 | **8** |

**O objetivo do item 7 está cumprido: o piloto volta a ZERO, o número da
`main`** — e não o `baseline.json` velho de 7. TGD e TP1 melhoram muito
além do que o CR pedia (−55% e −80% contra a `main`).

## Determinismo

Bateria do cross-audit, reusada sem alteração (31 entradas por projeto:
baseline + 20 permutações + 10 reversões de endpoint, nas versões ingênua e
geométrica), rodada **depois** da correção:

| projeto | válidas | camadas com 1 fingerprint | global | fingerprints distintos nas 31 entradas |
|---|---|---|---|---|
| `piloto_sintetico_2x2` | 26 | **11/11** | **1** | 6 (as 5 reversões INGÊNUAS descrevem outro prédio) |
| `torre_easy_lo_r00_tgd` | 21 | **11/11** | **1** | **1** |
| `torre_easy_lo_r00_tp1` | 25 | **11/11** | **1** | **1** |

Em TGD e TP1 **todas as 31 entradas colapsam num único fingerprint**,
inclusive as classificadas como variante inválida. No piloto as 5 reversões
ingênuas continuam sendo outro prédio (deslocam os vãos 14 cm — provado
pelo cross-audit) e as 26 válidas dão 1 fingerprint em todas as camadas.

A lista nova sai de `seg_start_cm` e das bordas das peças de nó — tudo já na
grade de snap (`PIER_LENGTH_SNAP_DECIMALS`). **Nenhuma dependência nova de
`wall_idx`, ordem de lista ou `GetEndPoint(0)`.**

## Same-band

```
same-band forbidden   MAIN 0   HEAD 0   DEPOIS 0
```

**PRESERVADO.** Medido com o instrumento do próprio `CR-BLOCK-01`
(`diagnostics_block_prisma/metrics.py`), nunca uma reimplementação.

## Cross-band

```
cross-band forbidden  MAIN 33   HEAD 60   DEPOIS 48
```

**MELHOROU 12 contra o HEAD.** Continua acima da `main`, e os 15 que
sobram são majoritariamente do wall graph (o cross-audit mediu 24 dos 27 do
salto 33 → 60 como sendo do `wall_pairing.py`, fora do escopo deste CR).

Taxonomia completa:

| classe | MAIN | HEAD | DEPOIS |
|---|---|---|---|
| `FORBIDDEN_JOINT_ALIGNMENT` | 33 | 60 | **48** |
| `DOCUMENTED_EXCEPTION` | 595 | 613 | 577 |
| `UNCLASSIFIED_RULE_CONFLICT` | 1506 | 1246 | **439** |
| `NO_ALIGNMENT` | 18696 | 18809 | **20057** |

`UNCLASSIFIED_RULE_CONFLICT` cai 65% — era exatamente a classe "a
coincidência é consequência direta de uma peça de nó" que este CR ataca.

## Compensadores

```
compensadores consecutivos   MAIN 1210   HEAD 1168   DEPOIS 1114
```

**MELHOROU nos dois pontos de comparação** — o risco MÉDIO-ALTO que o
cross-audit apontou como principal **não se materializou**.

| código | MAIN | HEAD | DEPOIS |
|---|---|---|---|
| piloto `COMPENSATOR_CONSECUTIVE` | 36 | 40 | 38 |
| tgd `COMPENSATOR_CONSECUTIVE` | 446 | 551 | **483** |
| tgd `COMPENSATOR_EXCESS_IN_RUN` | 342 | 397 | 392 |
| tgd `COMPENSATOR_VERTICAL_STRIP` | 59 | 62 | **59** |
| tp1 `COMPENSATOR_CONSECUTIVE` | 1463 | 1343 | **1325** |
| tp1 `COMPENSATOR_EXCESS_IN_RUN` | 1038 | 1058 | 1068 |
| tp1 `COMPENSATOR_VERTICAL_STRIP` | 178 | 198 | **196** |

Único que sobe contra o HEAD: `tp1 COMPENSATOR_EXCESS_IN_RUN` +10 (1%).

## L/T/X

Censo de `placement_reason` sobre os candidatos do `solve_result`
(medição própria deste CR — `out_nf_*.json`):

| `placement_reason` | tgd (MAIN / HEAD / **DEPOIS**) | tp1 | piloto |
|---|---|---|---|
| `L_CORNER` | 916 / 916 / **916** | 448 / 448 / **448** | 16 / 16 / **16** |
| `L_CORNER_DEGRADED` | 76 / 76 / **76** | 84 / 84 / **84** | — |
| `T_INTERSECTION_MAIN` | 451 / 451 / **451** | 571 / 571 / **571** | — |
| `T_INTERSECTION_INCOMING` | 451 / 451 / **451** | 571 / 571 / **571** | — |
| `T_INTERSECTION_INCOMING_DEGRADED` | 334 / 334 / **334** | 328 / 328 / **328** | — |
| `T_INTERSECTION_DEGRADED_L` | 412 / 412 / **412** | — | 16 / 16 / **16** |
| `X_INTERSECTION` | 120 / 120 / **120** | 310 / 310 / **310** | — |
| `X_INTERSECTION_DEGRADED` | 8 / 8 / **8** | 54 / 54 / **54** | 4 / 4 / **4** |
| `STANDARD_FILL` | 6830 / 6797 / **6840** | 11438 / 11359 / **11592** | 280 / 284 / **284** |
| `OPENING_REPAIR_FILL` | 547 / 537 / **537** | 1084 / 1106 / **1116** | 70 / 70 / **69** |

**Delta ZERO em TODAS as categorias de nó, nos três projetos e nos três
pontos de medição.** Nenhuma peça de nó foi reposicionada — só a busca de
layout do preenchimento ganhou posições a evitar, exatamente como o item 10
exige. Todo o delta desta CR está em `STANDARD_FILL` e
`OPENING_REPAIR_FILL`. `intersection_failures` também fica igual nos três
pontos (tgd 200, tp1 0, piloto 0).

### Censo de peça (MAIN / HEAD / **DEPOIS**)

| código | tgd | tp1 | piloto |
|---|---|---|---|
| `B19` | 834 / 583 / **583** | 1063 / 1101 / **1101** | 26 / 30 / **30** |
| `B34` | 2521 / 2468 / **2564** | 1966 / 1761 / **2010** | 82 / 81 / **81** |
| `B39` | 4496 / 4630 / **4547** | 7860 / 8047 / **7798** | 220 / 218 / **218** |
| `B54` | 571 / 571 / **571** | 881 / 881 / **881** | 0 / 0 / **0** |
| `C09` | 1139 / 1239 / **1232** | 2457 / 2331 / **2337** | 32 / 36 / **37** |
| `C04` | 584 / 611 / **648** | 661 / 710 / **947** | 26 / 25 / **23** |

Leitura honesta: `B34` e `C04` sobem (o desencontro passa a exigir mais
peça de acerto), `B39` desce. O `C04` do TP1 é o maior salto (+237, +33%
contra o HEAD). **Mesmo assim** `COMPENSATOR_CONSECUTIVE` do TP1 CAI
(1343 → 1325): há mais pastilha no prédio, mas menos pastilha EM SEQUÊNCIA,
que é o que a regra #2 proíbe. `B54` e `B19` ficam intactos.

## Aberturas

| métrica | MAIN | HEAD | **DEPOIS** | veredito |
|---|---|---|---|---|
| tgd `OPENING_BLOCK_INSIDE_DOOR` | 43 | 44 | **49** | **PIOROU (+5)** |
| tgd `OPENING_BLOCK_CROSSES_JAMB` | 147 | 147 | **146** | melhorou (−1) |
| tgd `door_void_violations` | 290 | 290 | **290** | igual |
| tgd `jamb_exceptions` | 172 | 172 | **172** | igual |
| tgd `OPENING_REPAIR_FILL` | 547 | 537 | **537** | igual |
| tp1 `OPENING_BLOCK_CROSSES_JAMB` | 168 | 154 | **154** | igual |
| tp1 `door_void_violations` | 348 | 348 | **348** | igual |
| tp1 `jamb_exceptions` | 44 | 52 | **52** | igual |
| tp1 `OPENING_REPAIR_FILL` | 1084 | 1106 | **1116** | +10 (0,9%) |
| piloto `OPENING_REPAIR_FILL` | 70 | 70 | **69** | melhorou (−1) |
| piloto `OPENING_MISSING_COUNTER_LINTEL` | 4 | 4 | **4** | igual |
| piloto `door_void_violations` | 0 | 0 | **0** | igual |

**Sem esconder atrás de "dentro da faixa histórica".** `INSIDE_DOOR` do TGD
é a ÚNICA regressão de abertura, e é real. Diagnosticada peça a peça:

```
paredes com INSIDE_DOOR   MAIN 18 paredes   DEPOIS as MESMAS 18 paredes
nenhuma parede nova entra na lista
+1 achado em cada uma de W019 W045 W051 W090 W131 W146
quase todos na fiada de cima; W045 e W090 sao CROSSES_JAMB que viraram INSIDE_DOOR
```

São paredes cujo vão já invade a reserva do nó — TGD tem 200
`intersection_failures` e 1024 colisões na própria `main`.
`door_void_violations`, o contador do próprio motor, fica **intacto**.

**Nenhuma versão da correção evita isso:** a versão mínima (só o sentido
A→B, medida em `out_nf_intermediario_so_sentido_A_para_B.json`) já leva o
número a 46, e o `baseline.json` grava 45 — qualquer aumento é
`CRITICAL_REGRESSION` pela régra do corpus. Registrado como conflito real
entre a regra #1 (junta de nó) e a seção 3 (zona de exclusão do vão), em
`REGRAS_MODULACAO_BLOCOS.md` §31.10.

`continuous_first` continua o único default:
`DEFAULT_OPENING_STRATEGY == OPENING_STRATEGY_CONTINUOUS_FIRST`, não tocado.

## Cobertura

| métrica | MAIN | HEAD | **DEPOIS** |
|---|---|---|---|
| tgd `COVERAGE_MISSING_ROW` | 265 | 293 | **293** |
| tgd `COVERAGE_ROW_MOSTLY_EMPTY` | 171 | 187 | **187** |
| tgd `COVERAGE_GAP_IN_ROW` | 1934 | 1913 | **1913** |
| tp1 `COVERAGE_MISSING_ROW` | 16 | 18 | **18** |
| tp1 `COVERAGE_ROW_MOSTLY_EMPTY` | 27 | 26 | **26** |
| piloto `COVERAGE_ROW_MOSTLY_EMPTY` | 8 | 8 | **8** |

**Delta ZERO contra o HEAD em todas.** Este CR **não piora** a dívida de
cobertura do wall graph, exatamente como o item 12 exige. A correção dela
continua com a Conta 2, em `wall_pairing.py`.

## Reference Corpus

`python3 nuvem/benchmark/tools/run_reference_corpus.py --all`, sobre o
código deste CR (saída completa em
`diagnostics_block_node_fill_joint/out_nf_reference_corpus_after.{json,md}`):

```
ANTES (HEAD)                              DEPOIS
OVERALL: CRITICAL_REGRESSION_PRESENT      OVERALL: CRITICAL_REGRESSION_PRESENT
- piloto  PRISM_CONTINUOUS_JOINT  7 -> 14   (RESOLVIDO - sumiu da lista)
- tgd     COVERAGE_MISSING_ROW  265 -> 293  - tgd  COVERAGE_MISSING_ROW  265 -> 293
- tgd     COVERAGE_ROW_MOSTLY_EMPTY 171->187 - tgd COVERAGE_ROW_MOSTLY_EMPTY 171->187
- tp1     COVERAGE_MISSING_ROW   16 -> 18    - tp1 COVERAGE_MISSING_ROW   16 -> 18
                                             - tgd OPENING_BLOCK_INSIDE_DOOR 45 -> 49  (NOVA)
```

Matriz projeto × métrica DEPOIS:

```
tgd     prism IMPROVED  L/T/X IMPROVED  compensators IMPROVED  openings REGRESSED
tp1     prism IMPROVED                  compensators IMPROVED
piloto  prism IMPROVED                  compensators REGRESSED
```

**Nenhuma referência, baseline ou `reference_score` foi atualizada.** Os
artefatos regeráveis (`score.json`, `reports/*.txt`) que a rodada produziu
foram restaurados com `git checkout` — `git status` fica limpo.

## Performance

Mediana de 5 repetições, por fase:

| projeto | fase | HEAD | DEPOIS | delta |
|---|---|---|---|---|
| piloto | grafo | 0,0024 s | 0,0023 s | −4% |
| piloto | solver | 0,0696 s | 0,0728 s | **+4,6%** |
| piloto | total | 0,0721 s | 0,0751 s | **+4,2%** |
| tgd | grafo | 0,7032 s | 0,7345 s | +4,5% |
| tgd | solver | 2,7205 s | 2,8709 s | **+5,5%** |
| tgd | total | 3,4184 s | 3,6106 s | **+5,6%** |
| tp1 | grafo | 0,2408 s | 0,2365 s | −1,8% |
| tp1 | solver | 2,9287 s | 3,2211 s | **+10,0%** |
| tp1 | total | 3,1695 s | 3,4576 s | **+9,1%** |

Nenhuma mudança de ordem de grandeza: o custo novo é O(juntas) por trecho
mais, ocasionalmente, UMA chamada extra de `_pier_layout_avoiding_joints`
(só quando o layout padrão de fato colide com uma junta de nó da fiada
oposta). O grafo não muda — nenhuma linha de `wall_pairing.py` foi tocada.

## Testes

| suíte | HEAD | **DEPOIS** |
|---|---|---|
| `tests/test_block_node_fill_joint.py` (NOVO) | — | **20 passed** |
| `tests/test_block_pipeline_determinism.py` | 52 passed | **52 passed** |
| `tests/test_block_graph_determinism.py` | 27 passed | **27 passed** |
| `tests/test_block_bonding.py` | 32 passed | **32 passed** |
| `tests/test_golden_benchmark.py` | 90 passed | **90 passed** |
| `tests/test_script.py` | 260 passed | **260 passed** |
| `tests/regression` | 110 passed, **3 failed** | 111 passed, **2 failed** |
| `tests/ -m "not slow"` | 574 passed | **588 passed** |
| árvore inteira | 584 passed, **3 failed** | **599 passed, 2 failed** |

**As 2 falhas que sobram** são as duas regressões de COBERTURA do wall
graph (`torre_easy_lo_r00_tgd` e `torre_easy_lo_r00_tp1`,
`COVERAGE_MISSING_ROW`) — as mesmas do HEAD, sem alteração, e explicitamente
fora do escopo pelo item 12. **A terceira falha (o piloto,
`PRISM_CONTINUOUS_JOINT` 7 → 14) foi ELIMINADA.**

### A suíte nova falha no código anterior

`tests/test_block_node_fill_joint.py` rodada em `2594f6ff` (worktree
separado): **17 failed, 3 passed**. No código novo: **20 passed**.

Os testes que DISCRIMINAM (falham por VIOLAÇÃO medida, não por função
inexistente) são os de invariante:

```
010  celula fechada, 5 comprimentos (150/230/350/430/590 cm)  -> 4 violacoes cada, antes
011  grade 2x2 (topologia do piloto)                          -> 2 violacoes, antes
013  o mesmo com ABERTURA (porta e janela, horizontal e vertical)
014  as DUAS fiadas e os DOIS sentidos
015  invariancia a 3 permutacoes da ordem de entrada
016  invariancia a inversao de pontas
```

Cobertura de L, T, X isolados (012) entra como não-regressão: eles já
estavam corretos e continuam.

## Arquivos alterados

```
PRODUCAO
  nuvem/core/engine/wall_stepper.py            +315 -11   (UNICO arquivo de producao)

DOCUMENTACAO (obrigatoria por CLAUDE.md)
  nuvem/REGRAS_MODULACAO_BLOCOS.md             +222       (secao 31)
  docs/BLOCK_NODE_FILL_JOINT.md                           (este arquivo)

TESTES
  tests/test_block_node_fill_joint.py                     (20 testes, geometria sintetica)

LABORATORIO (so' leitura do motor)
  nuvem/benchmark/diagnostics_block_node_fill_joint/
```

**NÃO alterados:** `wall_pairing.py`, `continuous_modulation.py`,
`geometry.py`, qualquer `baseline.json`, `reference.json`,
`reference_score.json`, e a pasta do cross-audit
(`diagnostics_block_determinism_final_cross_audit/`, restaurada com
`git checkout` depois de reusar a bateria dela).

## Produção

Uma única função pública nova no `solve_result`: `node_boundary_conflicts`,
por parede, em `per_wall`.

```
alignment_conflicts      junta interna da Fiada A  x  junta interna da Fiada B
                         consequencia de ESCOLHA -> quase sempre ha' outra
                         composicao. Continua tendo de dar ZERO.  DA' ZERO.

node_boundary_conflicts  junta NO'|FILL            x  junta interna da fiada oposta
                         GEOMETRIA FIXA do no' -> nenhum layout a move.
                         piloto 0 | tgd 23 | tp1 28
```

**Por que separadas.** Contá-las juntas dispararia o ajuste de abertura
(`needs_fix`) para um defeito que abertura nenhuma resolve, e apagaria o
significado do gate histórico do `CR-BLOCK-01`. **Provado que a separação
não muda geometria nenhuma:** o experimento
`out_nf_experimento_gate_cego.json` mede as duas variantes (gate cego x gate
honesto) e todas as métricas geométricas são IDÊNTICAS — a única diferença é
o que o motor reporta.

Os 23 + 28 residuais têm causa medida e são **insolúveis dentro do
catálogo** (§31.7): pilarete de 29 cm com as DUAS pontas fechadas contra
peça de nó, onde `_pier_forced_bypass_layouts` devolve lista VAZIA. Fica
registrado como pendência de código aberta — ampliar o gerador de
candidatos é redesenho da busca de preenchimento, fora do pedido deste CR.

### Fora de escopo, relatado e NÃO feito (item 17)

1. Subir `node_boundary_conflicts` até o topo do `solve_result` exige UMA
   linha em `nuvem/core/wall_modeling.py`. **Não feito.** Lê-se por
   `solve_result["per_wall"][i]["node_boundary_conflicts"]`.
2. Ampliar `_pier_forced_bypass_layouts` para pilarete curto de duas pontas
   fechadas. **Não feito** (raio de impacto e risco de compensador).
3. A dívida de cobertura do wall graph (`wall_pairing.py`). **Não tocado** —
   é da Conta 2, item 12.

## Veredito

```
PRISM piloto ............... 0        APROVADO   (14 -> 0; MAIN = 0)
same-band forbidden ........ 0        APROVADO   (preservado nos 3 pontos)
alignment_conflicts final .. 0        APROVADO   (nos 3 projetos)
determinismo ............... 1 fp     APROVADO   (11/11 camadas, 3 projetos)
cobertura .................. igual    APROVADO   (delta ZERO contra o HEAD)
compensadores .............. 1114     APROVADO   (melhor que MAIN e que HEAD)
cross-band ................. 48       APROVADO   (melhor que HEAD)
L/T/X ...................... delta 0  APROVADO   (nenhum no' reposicionado)
performance ................ +5..10%  APROVADO   (mesma ordem de grandeza)
aberturas .................. +5       ** NAO APROVADO **
```

**O item 18 tem NOVE critérios; oito passam e um falha.**

O que falha é `torre_easy_lo_r00_tgd` / `OPENING_BLOCK_INSIDE_DOOR`:
45 (baseline) → 49, classificado `CRITICAL_REGRESSION` pelo Reference
Corpus. Não é churn anônimo — é +1 achado em cada uma de seis paredes que
já falhavam, quase todos na fiada de cima, com `door_void_violations` e
`jamb_exceptions` intactos. E **não existe versão da correção que o evite**:
a versão mínima já dá 46.

**A decisão é do usuário**, e o CR é explícito em não deixar isso escondido.
O que está sobre a mesa:

```
GANHO   prisma do piloto        14 -> 0     (o objetivo declarado do CR)
        prisma do tgd          702 -> 318   contra a main
        prisma do tp1          837 -> 169   contra a main
        compensadores         1210 -> 1114  contra a main
        cross-band              60 -> 48    contra o HEAD
        UNCLASSIFIED_RULE_CONFLICT 1506 -> 439

CUSTO   tgd OPENING_BLOCK_INSIDE_DOOR  45 -> 49
        +5..10% de tempo de solver
```

**NENHUM MERGE FOI FEITO.** Parado antes, como o item 19 pede.
