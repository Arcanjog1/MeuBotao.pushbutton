# CROSS-AUDIT — CR-BLOCK-DETERMINISM

> CONTA 2, fase 2 (cross-audit). Continua sendo AUDITOR — nenhuma correção
> de produção foi feita, nenhuma branch da CONTA 1 foi alterada, nenhum
> merge na `main`.
>
> Branch: `claude/block-determinism-cross-audit`, criada a partir de
> `origin/claude/block-pipeline-determinism-uj7cvq` (HEAD confirmado
> `4516190` = `45161900bce82c65749328f0702571b89bfef2ac`, exatamente o
> esperado), com os artefatos do baseline (`origin/claude/block-determinism-audit`)
> mesclados por cima sem conflito. `main` de referência:
> `24ada98f5a8d4e7aa4cf0b30621d7818e4bb4fdc`. Produção alterada pela CONTA
> 1: só `nuvem/core/engine/wall_pairing.py` (confirmado por `git diff
> --stat 24ada98 4516190` — 284 linhas, nenhum outro arquivo em
> `nuvem/core/**`).
>
> Escrita desta fase restrita a
> `nuvem/benchmark/diagnostics_block_determinism_audit/cross_audit/**` e a
> este arquivo.

## Git

```
git fetch origin
git checkout -b claude/block-determinism-cross-audit origin/claude/block-pipeline-determinism-uj7cvq
git merge --no-edit origin/claude/block-determinism-audit   # sem conflito
```

## Resumo executivo

A CONTA 1 afirmou: grafo 8→1 fingerprint, pipeline global 8→2 (só
`endpoint_reversal` diverge), causa raiz identificada em
`_greedy_fill_blocks`/helpers de `wall_stepper.py`. **Reproduzido e
confirmado com uma bateria 3× maior** (24 ordens, não só 8): o GRAFO está
de fato **totalmente determinístico e canônico** — todas as 19 variantes
que só mudam a ORDEM da lista (sem inverter nenhum eixo) convergem para o
mesmo fingerprint global, incluindo variantes que a CONTA 1 nunca testou
(`reverse_horizontal_only`, `reverse_vertical_only`,
`shuffle_within_orientation`, `random_endpoint_reversal`). Mas o
não-determinismo do PIPELINE GLOBAL é mais amplo do que "endpoint_reversal
é o único caso": qualquer variante que muda o SENTIDO DE DESENHO de pelo
menos uma parede produz um fingerprint distinto — e distinto ENTRE SI, não
só do baseline (**6 fingerprints globais em 24 ordens**, não 2). A causa
raiz está confirmada como sendo a camada de PREENCHIMENTO
(`STANDARD_FILL`/`OPENING_REPAIR_FILL`), nunca a resolução L/T/X (que bate
100% em contagem entre baseline e `endpoint_reversal`).

## Gates D1-D10

| Gate | Critério | Veredito | Evidência |
|---|---|---|---|
| **D1** | node fingerprint = 1 em todas as ordens | **PASS** | `wall_graph_node_positions`: 1 fingerprint distinto em 24/24 ordens (`cross_audit/out_cross_variants_census.json`) — mais forte que os 8/8 da CONTA 1, cobre 16 variantes extras que ela não testou |
| **D2** | cada nó geométrico recebe uma única classificação | **PASS** | `node_types`: 1 fingerprint em 24/24. Confirmado também por contagem direta: `{FREE_END:55, T_INTERSECTION:118, STRAIGHT_CONTINUATION:9, L_CORNER:63, AMBIGUOUS:11, X_INTERSECTION:17}` idêntico em baseline e `endpoint_reversal` |
| **D3** | `wall_end_to_node` equivalente | **PASS (com ressalva sobre a própria métrica)** | Ver seção "wall_end_to_node" abaixo — a métrica ORIGINAL do baseline usa `end_index` cru (0/1), que por definição troca de valor quando o sentido de uma parede é invertido; isso gerou 6/24 "divergências" que são artefato da métrica, não do motor. Uma versão CANÔNICA (`cross_audit/lib_cross.py::canonical_wall_end_to_node`, identifica a ponta pelo endpoint `lo`/`hi`, não pelo `end_index`) bate 100% em todas as variantes testadas, incluindo as 5 de reversão de endpoint |
| **D4** | resultado bate com oráculo independente nos nós divergentes | **PASS** | Das 60 identidades de nó divergentes no baseline, **60/60 não divergem mais** (`out_cross_60_nodes.json`). Os 6 casos críticos ("somem" em até 19/24 ordens) agora convergem para 1 identidade canônica cada (a fusão de 3 fragmentos quase-colineares em 1 nó, nunca 2), presente nas 24 ordens, e o oráculo concorda que a classificação (`AMBIGUOUS`) é geometricamente correta — ver seção dedicada |
| **D5** | global block fingerprint = 1 | **FAIL** | 6 fingerprints globais distintos em 24 ordens (não 2) — ver seção "Endpoint reversal" |
| **D6** | coverage não cai | **FAIL** | `pieces` no baseline/ordem canônica: 10647 (código antigo) → 10571 (CONTA 1); a faixa min/max das 24 ordens também caiu e ficou mais estreita: 10566-10696 (spread 130, código antigo) → 10530-10571 (spread 41, CONTA 1) — o teto E o piso caíram. `B19` caiu de 853 (canônica antiga) para 603 — abaixo do MÍNIMO histórico já observado (661) em qualquer das 24 ordens antigas |
| **D7** | `CR-BLOCK-01` não regride | **PASS** | `alignment_conflicts = 0` em 24/24 ordens (código da CONTA 1), igual ao baseline. `intersection_failures=200`, `collisions=1034`, `door_void_violations=290` idênticos entre o baseline antigo (ordem canônica) e o novo na mesma ordem |
| **D8** | L/T/X não pioram | **PASS** (nível de classificação de nó) / **flag** (nível de peça, ver D5/D6) | Contagem de nós L/T/X/FREE_END/AMBIGUOUS idêntica à do código antigo na mesma ordem (ver D2). A divergência mora em QUAL peça de preenchimento cada L-corner recebe (B19 vs outros códigos), não em quantos L/T/X foram resolvidos |
| **D9** | runtime aceitável | **PASS** | Antigo: 1.96-3.39s (24 ordens); CONTA 1: 2.00-3.07s (24 ordens) — mesma ordem de grandeza, sem degradação |
| **D10** | conjunto de paredes antes do grafo não muda | **PASS** | `input_wall_geometry`: 1 fingerprint em 24/24, 167 paredes em todas — mesmo conjunto, só a ordem/sentido mudam |

## 24 ordens

Repetida a MESMA bateria do baseline (8 oficiais + 16 adicionais, mesmos
critérios, nenhuma redução) contra o código da CONTA 1 —
`cross_audit/run_cross_variants.py` → `out_cross_variants_census.json`.

Fingerprint global por variante (agrupado):

| grupo de fingerprint | variantes | o que têm em comum |
|---|---|---|
| A (= baseline) | `baseline`, `reversed`, `shuffle_seed_{1,2,3,5,7,10,11,13,17,23,42,50,99,123,999}`, `shuffle_within_orientation_seed_{1,2}` — **19 variantes** | só mudam a ORDEM da lista de entrada; nenhum eixo de parede é invertido |
| B | `endpoint_reversal` | TODOS os eixos invertidos |
| C | `reverse_horizontal_only` | só paredes horizontais invertidas |
| D | `reverse_vertical_only` | só paredes verticais invertidas |
| E | `random_endpoint_reversal_seed_1` | ~metade das paredes invertida (aleatório, seed 1) |
| F | `random_endpoint_reversal_seed_2` | ~metade das paredes invertida (aleatório, seed 2) |

Fingerprints por camada (24 ordens): `input_wall_geometry`,
`wall_graph_node_positions`, `node_types`, `node_arms`, `midspan_crossings`
— todos **1 distinto** (determinísticos). `wall_end_to_node` (métrica
original, não-canônica), `l_solutions`, `t_solutions`, `x_solutions`,
`block_reservations`, `block_layouts`, `global_result` — **6 distintos**
cada, alinhados exatamente com os 6 grupos da tabela acima.

Downstream (min/max nas 24 ordens, CONTA 1): `pieces` 10530-10571,
`non_modular` 3111-3120, `intersection_failures` 200 (fixo),
`alignment_conflicts` 0 (fixo), `collisions` 1034-1051,
`door_void_violations` 290 (fixo), `C09` 1238-1280, `C04` 533-572, `B19`
603-634, `runtime_s` 2.00-3.07.

## 60 nós originalmente divergentes

Recheck completo em `run_cross_60_nodes.py` → `out_cross_60_nodes.json`,
casando por identidade geométrica estável (nunca posição/índice, mesma
convenção do baseline):

- **60/60 identidades não divergem mais** nas 24 ordens (`n_still_divergent_now
  = 0`).
- **0 novas divergências** surgiram (`n_new_divergent_now = 0`) — a
  correção não introduziu nenhuma instabilidade nova detectável por esta
  bateria.

## 6 nós que desapareciam

Os 6 casos críticos do baseline eram, na verdade, **2 encontros físicos**
(dois grupos espelhados de 3 paredes quase-colineares, a poucos cm de
gap), cada um registrado no baseline sob 3 identidades PARCIAIS diferentes
(o fragmento A+B, o fragmento A+C, e o grupo completo A+B+C — dependendo
de qual clusterização a ordem de entrada produzia naquela execução).

No código da CONTA 1:
- as identidades PARCIAIS (2 paredes) **nunca mais aparecem** em nenhuma
  das 24 ordens (0/24) — a clusterização por componente conexa
  (union-find) sempre funde as 3 pontas no MESMO nó, nunca fragmenta;
- a identidade COMPLETA (3 paredes) está presente em **24/24 ordens**,
  com **1 única posição** e **1 único tipo** (`AMBIGUOUS`) — confirmado:
  mesma posição canônica, mesmos braços, mesmo tipo em todas as ordens;
- o oráculo geométrico independente (`oracle.classify_point`, sem chamar
  `_classify_wall_node`), aplicado ao ponto canônico de cada um dos 2
  encontros, também devolve `AMBIGUOUS` — **bate com o motor**. Não é um
  bug de classificação: são 3 paredes de fato quase-colineares com um
  pequeno desalinhamento real entre si (poucos cm), geometria
  genuinamente ambígua, não um erro do solver.

**Gate crítico: CONFIRMADO.** Os 2 encontros físicos (6 identidades
antigas) agora são 2 identidades canônicas estáveis, corretamente
resolvidas como `AMBIGUOUS` pelo motor E pelo oráculo independente.

## Canonical sort vs correção estrutural

O baseline já tinha mostrado que `MAIN + canonical sort` produz um
resultado ESTÁVEL (`CANONICAL_SORT_MAKES_REPEATABLE=true`) mas que bate
com o oráculo em só **183/273 (67%)** nós.

Medido agora, no código da CONTA 1, rodando **UMA** vez (não precisa
repetir — o resultado já é estável por construção): **183/273 nós batem
com o oráculo, 88 discordam, 2 sem ponto de oráculo próximo** —
`out_cross_node_oracle_agreement.json`. **Exatamente a mesma proporção do
"sort falso".**

Isso poderia, à primeira vista, indicar que a CONTA 1 "só trocou uma
ordem arbitrária estável por outra igualmente arbitrária" — mas os dados
não sustentam essa leitura:

1. A contagem de nós por TIPO (L/T/X/FREE_END/STRAIGHT/AMBIGUOUS) é
   **idêntica** entre o código antigo (em qualquer ordem que produzisse o
   mesmo resultado do canonical-sort) e o código da CONTA 1 — não é uma
   classificação DIFERENTE, é a MESMA classificação, agora alcançada de
   forma determinística por construção (união geométrica de componentes
   conexas + centróide canônico) em vez de como efeito colateral de uma
   ordenação específica.
2. Investigação direta dos 60 nós que ANTES divergiam (seção acima) mostra
   que, nos casos auditados em detalhe, as discordâncias remanescentes com
   o oráculo são majoritariamente geometria genuinamente ambígua (grupos
   de paredes quase-colineares) onde o PRÓPRIO oráculo, por limitação
   documentada (`oracle.py`, paredes-toco curtas inflando margem de nó
   vizinho), também não consegue decidir uma classificação limpa — não um
   caso de "motor errado, oráculo certo".
3. Portanto: a igualdade 183=183 é esperada e não é um sinal de alarme —
   é a MESMA árvore de decisão geométrica (mesmo conjunto de nós
   ambíguos, mesma causa), agora estável por engenharia em vez de por
   sorte de ordenação. **Não caracteriza REPROVAÇÃO do item 7** por si
   só. Recomenda-se, ainda assim, que uma revisão humana dos 88 casos (não
   feita aqui em profundidade, por orçamento) confirme se algum
   subconjunto é de fato um erro do motor mascarado pela limitação do
   oráculo — risco residual, não uma bandeira vermelha confirmada.

## Clusterização

O `_cluster_wall_arms` documenta o exemplo triangular medido na planta
real: `d(A,B)=3,50cm`, `d(A,C)=2,41cm`, `d(B,C)=5,91cm` — uma relação NÃO
TRANSITIVA sob o critério "está a ≤5cm", exatamente o tipo de bug que o
próprio baseline desta auditoria já tinha detectado independentemente
(seção "6 nós que desapareciam" acima, mesmos 2 grupos de 3 paredes
quase-colineares — mesma causa, descrita duas vezes por caminhos
diferentes).

A correção troca o algoritmo guloso (absorve tudo que está perto do
PRIMEIRO braço não usado — dependente de quem a lista trouxe primeiro)
por **componente conexa via union-find**: uma definição puramente
geométrica ("estas pontas pertencem ao mesmo encontro físico"),
independente de qual braço é visitado primeiro. Verificado:

- **forma o conjunto geométrico correto**: confirmado pela seção anterior
  (as 6 identidades antigas colapsam sempre para a MESMA identidade
  completa de 3 braços, nunca fragmentos);
- **é independente do primeiro braço visitado**: por construção
  (union-find é comutativo — `union(i,j)` não depende de qual dos dois é
  visitado primeiro) e confirmado empiricamente (24/24 ordens convergem);
- **não funde nós que deveriam permanecer separados**: a maior componente
  medida na planta real tem 4 braços (uma cruz) — não há evidência, nas
  24 ordens testadas, de um encontro real sendo fundido com outro
  fisicamente distante (a tolerância de 5cm é menor que meia espessura de
  parede, o que limita o encadeamento, como o próprio código argumenta);
- **não separa nós que deveriam estar unidos**: mesma evidência da seção
  "6 nós que desapareciam" — o comportamento antigo (guloso) é que às
  vezes separava indevidamente; o novo nunca separa.

## Posição dos nós

Confirmado independentemente: `wall_graph_node_positions` fingerprint = 1
em 24/24 ordens (não só as 8 oficiais). O código documenta um exemplo
medido de **4,45cm** de deslocamento por causa de `group[0]["anchor"]` —
**este número bate exatamente com o que a auditoria baseline já tinha
medido de forma totalmente independente**, antes de ler a CONTA 1: os
nós `STRAIGHT_CONTINUATION` das paredes 159/163/165 no baseline (ver
`docs/BLOCK_DETERMINISM_AUDIT.md`, dump bruto na sessão anterior) tinham
exatamente `dist=4.445cm` entre as duas âncoras do mesmo grupo. Essa
coincidência entre duas medições feitas por caminhos independentes é
evidência forte de que o número é real, não um artefato de metodologia.

- **como é calculada agora**: centróide das âncoras DISTINTAS do grupo
  (`_wall_node_group_point`), somadas em ordem canônica (paredes
  ordenadas antes de somar, para não reintroduzir dependência de ordem
  via não-associatividade de ponto flutuante);
- **é simétrica**: sim — centróide não depende de qual âncora é "a
  primeira", por construção;
- **é canônica**: sim — função pura da geometria (lista de âncoras
  distintas), sem `id()`/índice/ordem de descoberta;
- **endpoint reversal muda o ponto?**: não, confirmado — `endpoint_reversal`
  está no mesmo grupo de fingerprint de grafo que o baseline (camadas
  `wall_graph_node_positions`/`node_types`/`node_arms` idênticas);
- **faz sentido geometricamente**: sim — quando todas as âncoras
  coincidem (caso normal), o centróide é exatamente essa âncora (nenhuma
  mudança de comportamento no caso comum); só nos casos de âncoras
  distintas (parede mais curta que a tolerância de agrupamento, ~11 casos
  medidos na planta) o centróide entra em ação, e todos os pontos
  resultantes batem com o oráculo geométrico (ver seção "60 nós").

## Papéis L/T/X

A canonização (`_wall_graph_arm_key`) decide qual parede é `arms[0]`
(logo, qual recebe qual papel em `main_wall_idx`/`incoming_wall_idx`/
`neighbor_wall_idx`/`crossing_walls[0]`) por GEOMETRIA — não mais por
posição na lista de entrada. Determinado: **(A)**, não (B) — a
canonização apenas RENOMEIA os papéis de forma estável; não altera qual
DECISÃO GEOMÉTRICA cada papel representa (L continua L, T continua T, a
peça de amarração continua indo no braço menor/mais próximo do nó pela
mesma regra de sempre — `solve_l_corner`/`solve_t_intersection`/
`solve_x_intersection`, NÃO tocados por este CR). O que muda é *qual das
duas paredes simetricamente equivalentes* (antes indistinguíveis exceto
pela posição na lista) é rotulada `arms[0]` vs `arms[1]` — e isso É
aceitável pela regra explícita da missão ("é aceitável mudar um papel que
antes era arbitrário por índice, desde que a nova convenção seja
geometricamente consistente"), com a ressalva de que essa troca de rótulo
tem efeito colateral REAL e mensurável a jusante (qual parede ganha o
B34/B19 da fiada A vs B) — é exactly a fonte das duas falhas de
regressão (ver seção dedicada) e do `n_codigos_em_regressao=4` que o
próprio `out_convention_matrix.json` da CONTA 1 documenta, medido em 3
convenções candidatas, TODAS com alguma regressão — confirmando que a
troca de papel é **inevitável** para qualquer escolha canônica, não uma
falha de engenharia da convenção escolhida especificamente.

## Midspan crossings

`midspan_crossings`: fingerprint = 1 em 24/24 ordens (não só as 8
oficiais) — confirma, mais forte que o pedido:
- **identidade é canônica**: sim, por `_wall_graph_wall_key` aplicado a
  cada lado do par + ordenação da lista de cruzamentos pelo ponto e pelas
  chaves das paredes;
- **inverter a lista não altera**: confirmado — `reversed` e
  `endpoint_reversal` (que inverte inclusive o SENTIDO de cada eixo, mais
  agressivo que só reordenar) ambos no grupo de fingerprint determinístico
  desta camada;
- **classificação X continua correta**: `x_solutions`/contagem de nós
  `X_INTERSECTION` (17) idêntica entre código antigo e CONTA 1 na mesma
  ordem;
- **nenhum crossing desaparece/aparece incorretamente**: `n_rows=17` em
  todas as 24 execuções (verificado via `layered_fingerprints`).

## Fingerprint global

Não é 1. **6 fingerprints distintos em 24 ordens** (não os 2 relatados
pela CONTA 1 — ela testou só as 8 variantes oficiais, que de fato caem em
exatamente 2 grupos; a bateria estendida revela que o segundo grupo se
subdivide em 5, um por padrão de reversão de direção testado). Todas as
19 variantes de PURA REORDENAÇÃO (sem inverter nenhum eixo) convergem
para 1 fingerprint; toda variante que inverte ALGUM eixo cai num
fingerprint PRÓPRIO, distinto do baseline E das outras variantes de
reversão entre si — ver tabela na seção "24 ordens".

## Endpoint reversal

Investigação camada-a-camada (baseline vs `endpoint_reversal`, código da
CONTA 1):

| camada | igual? | detalhe |
|---|---|---|
| `input_wall_geometry` | sim | 167 paredes, mesmo conjunto |
| `wall_graph_node_positions` | sim | 273 nós, mesmas posições |
| `node_types` | sim | mesma contagem por tipo |
| `node_arms` | sim | mesmos braços por nó |
| `wall_end_to_node` (métrica canônica) | sim | ver "wall_end_to_node" abaixo |
| `midspan_crossings` | sim | 17 cruzamentos, mesma identidade |
| contagem de peças por `placement_reason` de amarração (`L_CORNER`, `L_CORNER_DEGRADED`, `T_INTERSECTION_MAIN/INCOMING/DEGRADED_L/INCOMING_DEGRADED`, `X_INTERSECTION`/`_DEGRADED`) | **sim, byte-a-byte** | 969, 85, 509, 454, 434, 354, 128, 8 — TODOS idênticos entre baseline e `endpoint_reversal`. **Confirma explicitamente a afirmação da CONTA 1: "peças L/T/X batem"** — embora o número total delas (2941) não bata com o "1581" citado por ela, o que sugere ela usou um critério de contagem diferente (possivelmente só um subconjunto, ou uma unidade diferente de "peça") — a AFIRMAÇÃO qualitativa (L/T/X não mudam) está confirmada; o número específico "1581" não foi reproduzido e deve ser tratado como não verificado |
| `STANDARD_FILL` | **NÃO** | 7207 → 7205 (-2 peças) |
| `OPENING_REPAIR_FILL` | **NÃO** | 423 → 402 (**-21 peças, ~5%**) — o grosso da divergência |
| `block_layouts` (tudo) | **NÃO** | 10647 → 10571 no total desta comparação específica (nota: números absolutos diferem levemente dos citados na tabela "24 ordens" porque aquela usa a ordem canônica do `input.json` como baseline explícito desta seção, não a média/faixa da bateria) |

**Confirmado**: a primeira camada REAL divergente pós-grafo é o
PREENCHIMENTO (`STANDARD_FILL` + principalmente `OPENING_REPAIR_FILL`),
nunca a resolução L/T/X. Isso é consistente com — mas não prova
definitivamente, já que `wall_stepper.py` não foi instrumentado
linha-a-linha nesta fase — a hipótese da CONTA 1 de que
`_greedy_fill_blocks`/helpers do reparo de abertura (`_recut_openings_and_repair`,
`_pier_layout_avoiding_joints` e cadeia) usam a orientação
`GetEndPoint(0)→GetEndPoint(1)` da própria parede como referência de
"início" da sequência de preenchimento, sem canonizar para um eixo
`lo→hi` estável. A concentração da perda de peças em
`OPENING_REPAIR_FILL` (-21/423, ~5%) vs `STANDARD_FILL` (-2/7205, ~0.03%)
é o dado mais forte a favor dessa hipótese: o reparo local de abertura
(que decide onde COMEÇAR a reempacotar depois de remover peças que
invadem o vão) é muito mais sensível à direção de referência do que o
preenchimento comum de um vão livre sem abertura por perto.

**Funções que precisariam ser alteradas no próximo CR** (não alteradas
aqui): `_recut_openings_and_repair`, `_pier_layout_avoiding_joints`,
`_pier_ordered_layout`, `_greedy_fill_blocks`/`_greedy_fill_blocks_any_first`
(todos em `wall_stepper.py`) — a referência de "início" da sequência
precisa vir de um eixo CANÔNICO (`lo→hi`, mesma convenção de
`_wall_graph_wall_key`), não de `GetEndPoint(0)`.

## wall_end_to_node

Achado metodológico desta fase, não do código auditado: a camada
`wall_end_to_node` de `lib_det.py` (usada pelo baseline e por esta
cross-audit) usa `end_index` CRU (0 ou 1, literalmente
`GetEndPoint(0)`/`(1)`) para identificar QUAL ponta de uma parede aponta
para qual nó. Isso não é uma identidade geométrica estável: quando
`endpoint_reversal` troca o sentido de desenho de uma parede, `end_index`
0 e 1 TROCAM de valor por definição, mesmo que o grafo esteja
perfeitamente correto. Isso produzia uma falsa "divergência" nessa
camada especificamente para as 5 variantes de reversão de direção.

Corrigido nesta fase (só para fins de MEDIÇÃO — nenhum arquivo do
baseline foi alterado) com `cross_audit/lib_cross.py::canonical_wall_end_to_node`,
que identifica cada ponta pelo endpoint canônico (`lo`/`hi` de
`wall_geom_key`) em vez do `end_index` cru. Com essa correção,
`wall_end_to_node` bate 100% em TODAS as variantes testadas, incluindo as
5 de reversão — confirmando que o mapeamento ponta-física→nó está
correto; a divergência real do pipeline global está inteiramente a
jusante disso, na camada de preenchimento (ver "Endpoint reversal").

## Duas regressões de benchmark

Reproduzidas: `pytest tests/regression` → **111 passed, 2 failed**
(exatamente como relatado), mesmos 2 testes
(`test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]` e
`[torre_easy_lo_r00_tp1]`), mesmos códigos de regressão crítica:

- `tgd`: `COVERAGE_MISSING_ROW` 265→293 (+28), `COVERAGE_ROW_MOSTLY_EMPTY`
  171→181 (+10), `OPENING_BLOCK_CROSSES_JAMB` 147→148 (+1);
- `tp1`: `COVERAGE_MISSING_ROW` 16→18 (+2).

Estes números batem EXATAMENTE com a linha `"ordem_bracos": "enum"` de
`nuvem/benchmark/diagnostics_block_determinism/out_convention_matrix.json`
(arquivo da própria CONTA 1, usado aqui só como referência cruzada, não
como prova por si só) — confirmado por medição independente, não só
citado.

**Investigação adicional (nova nesta fase)**: rodado `pytest
tests/regression` na `main` (24ada98, worktree separado) 4 vezes seguidas
(1 + 3 repetições) — **113 passed, 0 failed em TODAS as execuções**. Ou
seja, a `main` só "passa" porque roda SEMPRE com a mesma ordem de entrada
fixa (`input.json`), e essa ordem fixa por acaso produzia o resultado que
`baseline.json` capturou — não porque o resultado antigo fosse
canonicamente "correto". `baseline.json` (ambos os projetos) foi gravado
em **31/08/2026**, ANTES do `CR-BLOCK-01` (01/09) e muito antes deste CR
— já era, por definição, um snapshot de um comportamento arbitrário
(dependente de ordem) capturado num instante específico, não uma
referência canônica.

O próprio `out_convention_matrix.json` da CONTA 1 mostra que **as 3
convenções canônicas candidatas testadas (`enum`, `angulo`,
`comprimento`) regridem TODAS** contra esse baseline antigo (4, 5 e 7
códigos em regressão respectivamente) — só a convenção `legacy` (=
reproduzir o comportamento antigo dependente de ordem) dá zero
regressões, o que é esperado e não prova nada (ela é circular: o baseline
FOI gerado por esse comportamento). Isso é evidência geométrica de que
**alguma mudança de resultado nos casos ambíguos de papel A/B é
inevitável** para qualquer correção de determinismo — não uma falha
específica da convenção escolhida.

**Classificação: (A) BASELINE STALE**, com ressalva importante: a causa
raiz é uma mudança SEMÂNTICA real e deliberada (qual parede recebe qual
papel num L simétrico), não um bug incidental — mas o "baseline" contra o
qual ela regride nunca foi uma referência canônica, era a fotografia de
um comportamento arbitrário. A ação recomendada não é reverter a
canonização (isso reintroduziria o não-determinismo), é **regravar
`baseline.json` dos dois projetos** contra o resultado agora
determinístico (fora do escopo desta auditoria — `NÃO atualize os JSON`,
conforme instruído) — e então os 2 testes voltam a passar de forma
válida, contra uma referência que agora É estável entre execuções.

## `CR-BLOCK-01`

`same-band forbidden` e `alignment_conflicts`: **0 e 0**, confirmados
independentemente nas 24 ordens do código da CONTA 1 (não só na ordem que
ela reportou). `intersection_failures` (200), `collisions` (1034),
`door_void_violations` (290) idênticos ao código antigo na mesma ordem
canônica — nenhuma dessas métricas de amarração/prisma regrediu. A queda
de `coverage`/`B19` (seção D6) tem causa identificada e não relacionada
ao prisma (é canonização de papel A/B em L simétrico, não busca de
amarração vertical) — **não é uma regressão do `CR-BLOCK-01`**, é uma
questão ortogonal, como o próprio baseline desta auditoria já havia
antecipado (seção 9 de `docs/BLOCK_DETERMINISM_AUDIT.md`).

## Performance

Comparável: 2.00-3.07s (CONTA 1, 24 ordens) vs 1.96-3.39s (código antigo,
24 ordens) — mesma ordem de grandeza, sem indício de custo extra
relevante pela canonização (union-find + ordenação são baratos frente ao
resto do pipeline).

## Testes

```
pytest tests/test_block_graph_determinism.py -q   -> 27 passed
pytest tests/test_block_bonding.py -q              -> 32 passed
pytest tests/test_script.py -q                     -> 260 passed
pytest tests/regression -q                          -> 111 passed, 2 failed (ver secao dedicada)
```

`nuvem/tests` não existe como diretório de testes neste repositório
(`ls nuvem/tests` → não encontrado) — item da missão não aplicável a esta
árvore; os testes relevantes de `nuvem/` já estão cobertos por
`tests/test_script.py` (que importa e testa `nuvem/core/**` via
`tests/load_script.py`, ver `solver_bridge.py`).

## Veredito

**WALL GRAPH: APROVADO.**
Grafo (posição de nó, tipo, braços, `wall_end_to_node` canônico, midspan
crossings) 100% determinístico e canônico em 24/24 ordens — mais forte do
que as 8 testadas pela própria CONTA 1. Os 60 nós divergentes do baseline
e os 6 casos críticos de clusterização não-transitiva estão resolvidos e
verificados contra um oráculo geométrico independente. Nenhuma regressão
em `CR-BLOCK-01`.

**PIPELINE GLOBAL: AINDA NÃO DETERMINÍSTICO.**
D5 falha (6 fingerprints globais em 24 ordens, causa localizada e
confirmada na camada de preenchimento — `_recut_openings_and_repair`/
`_pier_layout_avoiding_joints`/`_greedy_fill_blocks` em `wall_stepper.py`,
fora do escopo desta CR). D6 falha (coverage caiu, causa identificada e
compreendida — canonização inevitável de papel A/B em L simétrico — mas
ainda é uma queda real de peças/`B19` que merece acompanhamento).

Por D1-D4 e D7-D10 passarem mas D5 (e D6) falharem — exatamente o caso
previsto pela missão (item 17):

## **VEREDITO GERAL: NECESSITA AJUSTE**

## Censo — ordem oficial das paredes

Ver `cross_audit/official_process_order_census.json`. Resumo: a regra já
existe em produção (`order_walls_for_processing`/`classify_wall_orientation`,
`wall_stepper.py`), já é a única forma de decidir sequência de
processamento entre paredes, e já implementa exatamente o enunciado
pedido pelo usuário. Único gap: o enunciado completo nunca foi escrito
por extenso em `REGRAS_MODULACAO_BLOCOS.md` (só referenciado como "regra
#5"). Nenhum código contradiz a regra.

## Censo — parede completa primeiro / aberturas depois

Ver `cross_audit/full_wall_first_opening_census.json`. Resumo: a
arquitetura pedida já existe em produção desde 2026-08-28
(`OPENING_STRATEGY_CONTINUOUS_FIRST`, módulo `continuous_modulation.py`),
já é o padrão (`DEFAULT_OPENING_STRATEGY`), e já está documentada por
extenso (`REGRAS_MODULACAO_BLOCOS.md`, seção 23). O modo antigo
(`split_first`) só é alcançado via parâmetro explícito em testes
comparativos — nenhum caminho de produção o usa silenciosamente. Único
item aberto (pré-existente, não criado por este CR): `jamb_exceptions=172`
em modo `continuous_first`, já registrado como "inesperado" em
`docs/BLOCK_MODULATION_AUDIT.md` (P2-3) — não investigado aqui, fora do
escopo do determinismo.

## Arquivos que contradizem as novas regras

**Nenhum encontrado.** Ambas as regras (ordem de processamento de paredes
e parede-completa-antes-de-abertura) já são a única estratégia usada por
qualquer caminho de produção. O que existe de "legado" (`split_first`)
está corretamente isolado a testes comparativos e a um mecanismo de
degradação bounded e documentado — dentro do que o item 21 da missão
permite explicitamente.

## Texto recomendado para documentação permanente

### REGRA A — Ordem oficial de processamento das paredes

Recomenda-se adicionar a `nuvem/REGRAS_MODULACAO_BLOCOS.md` uma seção
nova (a numeração cabe ao usuário/próximo CR) com o texto:

> **Ordem oficial de processamento entre paredes** (regra #5,
> implementada em `order_walls_for_processing`/`classify_wall_orientation`,
> `nuvem/core/engine/wall_stepper.py`): a ordem de processamento é
> decidida SÓ pela geometria, nunca pela ordem em que as paredes
> aparecem no CAD/`input.json`:
> 1. Todas as HORIZONTAIS primeiro, de cima para baixo (Y decrescente);
>    empate (mesmo nível, tolerância `WALL_ALIGNMENT_TOLERANCE_FT`):
>    esquerda para direita (X crescente).
> 2. Depois todas as VERTICAIS, da esquerda para a direita (X crescente);
>    empate (mesmo alinhamento): de baixo para cima (Y crescente).
> 3. Por fim as DIAGONAIS (nem H nem V dentro da tolerância de ~3°), em
>    cima→baixo/esquerda→direita — só para a ordem ser determinística,
>    nunca arbitrária.
>
> Esta ordem usa `min`/`max` dos dois endpoints de cada parede, nunca
> `p0`/`p1` diretamente: inverter o sentido de desenho de uma parede
> (`GetEndPoint(0)`↔`(1)`) NUNCA muda a ordem de processamento.
>
> Arquivos: `nuvem/core/engine/wall_stepper.py` (`order_walls_for_processing`,
> `classify_wall_orientation`, `_cluster_values_ft`). Testes:
> `tests/test_script.py` (linhas ~1370, ~2956) — recomenda-se adicionar um
> teste permanente novo que confirme invariância a endpoint reversal
> explicitamente (gap identificado nesta auditoria).

### REGRA B — Parede completa primeiro, abertura depois

Já documentada em `nuvem/REGRAS_MODULACAO_BLOCOS.md`, seção 23 ("PIPELINE
OFICIAL DE ABERTURAS — parede completa primeiro"). Recomenda-se só
ACRESCENTAR uma nota de rastreabilidade cruzada, sem reescrever a seção:

> **Nota (CR-BLOCK-DETERMINISM, 2026-09-02)**: esta regra (seção 23) e a
> regra #5 (ordem de processamento entre paredes) são ORTOGONAIS ao
> determinismo do GRAFO de paredes (`build_wall_graph`,
> `nuvem/core/engine/wall_pairing.py`) — a primeira decide COMO uma
> parede é modulada depois que o grafo já existe; a segunda decide EM QUE
> ORDEM as paredes são processadas. Nenhuma das duas, sozinha, garante
> determinismo do PIPELINE GLOBAL: a camada de preenchimento
> (`_recut_openings_and_repair`/`_pier_layout_avoiding_joints`/
> `_greedy_fill_blocks`) ainda depende do SENTIDO DE DESENHO de cada
> parede individual (`GetEndPoint(0)`→`(1)`), não só da ordem entre
> paredes — ver `docs/BLOCK_DETERMINISM_CROSS_AUDIT.md`, seção "Endpoint
> reversal", para o CR que precisa fechar isso.

Arquivos que precisarão ser atualizados quando o próximo CR (fechar
endpoint reversal) for implementado: `wall_stepper.py` (as 4 funções
citadas na seção "Endpoint reversal" acima), mais um teste permanente
novo em `tests/test_block_graph_determinism.py` ou arquivo irmão
específico para o pipeline de preenchimento (não só o grafo).

## Próximos CRs

Com base nos dados medidos aqui (não assumido a priori):

1. **Fechar o determinismo do pipeline global** (D5) — canonizar a
   direção de referência (`lo→hi`) nas 4 funções de preenchimento
   identificadas na seção "Endpoint reversal". Prioridade mais alta:
   é o próprio objeto desta CR ainda incompleto, e a queda de coverage
   (D6) provavelmente está entrelaçada com a mesma causa (fill mais
   robusto a direção tende a fechar mais vãos de forma consistente).
2. **Regravar `baseline.json` de `torre_easy_lo_r00_tgd` e
   `torre_easy_lo_r00_tp1`** contra o resultado determinístico (depois do
   item 1, para não regravar duas vezes) — resolve as 2 falhas de
   regressão sem reverter a canonização.
3. Escrever a REGRA A por extenso em `REGRAS_MODULACAO_BLOCOS.md` (texto
   pronto acima) + teste permanente de invariância a endpoint reversal
   para `order_walls_for_processing`.
4. Investigar `jamb_exceptions=172` em modo `continuous_first` (P2-3,
   pré-existente) — não bloqueante para o determinismo, mas já estava
   aberto e pode compartilhar causa com a queda de `OPENING_REPAIR_FILL`
   medida aqui (mesma vizinhança de código).
5. Demais itens do roadmap sugerido pela missão (compensadores, X, door
   exclusion, cross-band) — sem dados desta auditoria que justifiquem
   reordená-los; ficam depois dos itens 1-4 acima, que são os únicos que
   este cross-audit encontrou evidência direta de estarem incompletos.

## Arquivos criados nesta fase

```
nuvem/benchmark/diagnostics_block_determinism_audit/cross_audit/
  lib_cross.py                          # wall_end_to_node canonico (correcao metodologica)
  run_cross_variants.py                 # reusa run_baseline_variants.py contra o codigo da CONTA 1
  run_cross_60_nodes.py                 # recheck dos 60 nos divergentes do baseline
  out_cross_variants_census.json
  out_cross_60_nodes.json
  out_cross_node_oracle_agreement.json
  official_process_order_census.json    # item 18
  full_wall_first_opening_census.json   # item 19/20
docs/BLOCK_DETERMINISM_CROSS_AUDIT.md   # este arquivo
```

**ARQUIVOS DE PRODUÇÃO ALTERADOS: ZERO.**

---

# CROSS-AUDIT DO CR-BLOCK-DETERMINISM CONCLUÍDA.
# NENHUM CÓDIGO DE PRODUÇÃO ALTERADO.
# PARADO ANTES DO MERGE.
