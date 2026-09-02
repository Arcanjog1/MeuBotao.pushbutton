# AUDITORIA INDEPENDENTE — Determinismo do Wall Graph / Solver de Blocos

> CONTA 2. Auditoria independente do não-determinismo que a CONTA 1 está
> corrigindo em `claude/block-determinism-graph`. Esta fase (baseline) foi
> produzida **sem ler** aquela branch — nasce independente, para depois
> servir de árbitro externo (cross-audit) da correção da CONTA 1.
>
> Baseline: `main` @ `24ada98f5a8d4e7aa4cf0b30621d7818e4bb4fdc`.
> Branch desta auditoria: `claude/block-determinism-audit`.
> Escrita restrita a `nuvem/benchmark/diagnostics_block_determinism_audit/**`
> e a este arquivo — **zero arquivos de produção alterados**.
> Projeto usado: `torre_easy_lo_r00_tgd` (167 paredes, 17 fiadas, o único
> com input MEDIDO do catálogo real — ver `REGRAS_MODULACAO_BLOCOS.md`
> 24.8/24.9), via o mesmo caminho headless (`benchmark.solver_bridge`,
> `tests/revit_stubs.py`) que `tests/solver_bench.py` usa.

## Git

```
git fetch origin
git checkout main
git pull --ff-only        # HEAD = 24ada98f5a8d4e7aa4cf0b30621d7818e4bb4fdc
git checkout -b claude/block-determinism-audit
```

## 1. As 8 variantes oficiais — reproduzidas independentemente

Rodadas de novo nesta sessão (não copiadas de nenhum censo anterior),
sobre `torre_easy_lo_r00_tgd`:

| variante | fingerprint global (12 primeiros chars) | peças |
|---|---|---|
| baseline | ver `out_variants_census.json` | 10647 |
| reversed | distinto do baseline | 10601 |
| endpoint_reversal | distinto do baseline | 10612 |
| shuffle_seed_1 | distinto do baseline | 10616 |
| shuffle_seed_2 | distinto do baseline | 10685 |
| shuffle_seed_3 | distinto do baseline | 10696 |
| shuffle_seed_10 | distinto do baseline | 10569 |
| shuffle_seed_42 | distinto do baseline | 10566 |

**8/8 fingerprints distintos** — confirmado independentemente. O
não-determinismo pré-existe nesta `main` e não é um artefato de um censo
anterior.

## 2. Bateria mais forte — 24 ordens no total

Além das 8 oficiais: seeds extras `5, 7, 11, 13, 17, 23, 50, 99, 123, 999`
(10 seeds — total 15 shuffles) + `reverse_horizontal_only` +
`reverse_vertical_only` + `shuffle_within_orientation` (2 seeds) +
`random_endpoint_reversal` (2 seeds, ~metade das paredes com endpoints
trocados aleatoriamente) = **24 ordens no total** (baseline + 23
variantes). Script: `run_baseline_variants.py`, saída:
`out_variants_census.json`.

**Resultado: 24 fingerprints globais DISTINTOS em 24 ordens** — nenhuma
das 23 variantes bateu com o baseline. Overfit nas 8 variantes conhecidas
não é um risco real aqui: a bateria mais forte encontrou não-determinismo
com a mesma severidade que a bateria oficial (piorou, na verdade — 8/8 e
24/24 são igualmente "sempre diferente").

## 3. Fingerprints em camadas — onde nasce a divergência

Onze camadas medidas (`lib_det.LAYER_FUNCS`) + o fingerprint global, cada
uma com identidade **geométrica** (nunca `wall_idx`/`node_index`, que
mudam com a permutação — ver seção "Identidade geométrica" abaixo):

| camada | determinística nas 24 ordens? |
|---|---|
| `input_wall_geometry` | **SIM** (1 fingerprint) — mesmo conjunto de paredes, só a ordem da lista muda, como esperado |
| `wall_graph_node_positions` | **NÃO** (23 fingerprints distintos) |
| `node_types` | NÃO (24 distintos) |
| `node_arms` | NÃO (24 distintos) |
| `wall_end_to_node` | NÃO (24 distintos) |
| `midspan_crossings` | **SIM** (1 fingerprint) |
| `l_solutions` | NÃO (24 distintos) |
| `t_solutions` | NÃO (24 distintos) |
| `x_solutions` | NÃO (24 distintos) |
| `block_reservations` | NÃO (24 distintos) |
| `block_layouts` | NÃO (24 distintos) |
| `global_result` | NÃO (24 distintos) |

**Achado central: em TODAS as 23 variantes divergentes, a PRIMEIRA camada
a divergir é `wall_graph_node_positions`.** O não-determinismo nasce na
ETAPA 2 (construção do grafo de paredes — clusterização de pontas e
cálculo da posição do nó), não em nenhuma decisão de blocagem mais abaixo
no pipeline (L/T/X solutions, reservas, layout final apenas herdam e
amplificam a divergência que já existe no grafo). Uma correção que só
mexer em `solve_l_corner`/`solve_t_intersection`/`solve_x_intersection`
etc. sem tocar a construção do grafo (`build_wall_graph`/
`_classify_wall_node`/`_cluster_wall_arms` em
`core/engine/wall_pairing.py`) está tratando o sintoma, não a causa raiz
medida aqui.

`input_wall_geometry` e `midspan_crossings` deterministas confirmam que a
comparação está correta: a auditoria não está confundindo "o conjunto de
paredes é o mesmo" com "o processamento é determinístico" — a entrada é
idêntica (só reordenada/redesenhada), a saída não é.

## 4. Identidade geométrica (nunca por índice)

- **Parede**: `(endpoint_a, endpoint_b, espessura)`, com os dois
  endpoints ORDENADOS (`sorted`) para independer do sentido de desenho —
  `lib_det.wall_geom_key`.
- **Nó**: posição (arredondada) + tipo + conjunto ordenado de chaves de
  parede dos braços que chegam nele — `lib_det.node_geom_key`. Para casar
  "o mesmo nó" entre execuções (ver seção 5), a identidade usada é
  `(tipo, conjunto de chaves de parede dos braços)` **sem a posição**
  (que é justamente o que pode divergir).
- **Bloco**: parede geométrica + fiada (`course_index`) + código lógico +
  posição longitudinal arredondada + rotação — `lib_det.piece_geom_key`.

## 5. Nós divergentes — `out_divergent_nodes.json`

Casando nós entre as 24 execuções por identidade geométrica estável
(nunca posição), de **273 nós no baseline**, **60 identidades de nó
divergem** entre pelo menos duas das 24 ordens:

- **54 só de POSIÇÃO**: mesmo tipo (nenhuma dessas mudou de classificação
  L/T/X/FREE_END/STRAIGHT_CONTINUATION/AMBIGUOUS entre ordens), mas o
  ponto do nó varia entre ordens (tipicamente < 1cm, mas o bastante para
  quebrar o arredondamento de 2 casas decimais usado nas chaves). Causa
  provável (ver `possible_cause` de cada entrada): não-associatividade de
  ponto flutuante no cálculo do centróide do cluster de pontas na Etapa
  2, sensível à ordem em que as pontas chegam para agrupar.
- **6 identidades "somem"** em até 19 das 24 variantes — todas
  `AMBIGUOUS`, envolvendo grupos de 2-3 paredes quase-colineares com um
  pequeno desalinhamento entre si (poucos cm de gap perpendicular). Este
  é o achado mais sério: não é só a POSIÇÃO do nó que muda, é se as
  paredes sequer se AGRUPAM no mesmo cluster — um bug de clusterização
  order-dependente (a decisão "essas duas pontas quase-coincidentes
  pertencem ao mesmo nó?" some/aparece dependendo da ordem de
  processamento), mais grave que jitter de ponto flutuante puro.
- **0 identidades mudaram de TIPO** de classificação nesta bateria (ex.:
  nenhum L_CORNER virou T_INTERSECTION entre ordens) — o não-determinismo
  medido aqui é de POSIÇÃO/AGRUPAMENTO, não de reclassificação L/T/X.
  Isso não é garantia para toda entrada futura (ver GATE D2 abaixo).

## 6. Oráculo geométrico independente

`oracle.py` — reimplementação própria, do zero, de "o que significa
geometricamente um FREE_END/STRAIGHT_CONTINUATION/L_CORNER/
T_INTERSECTION/X_INTERSECTION/AMBIGUOUS", a partir só de endpoints +
espessura das paredes. **Não importa nem chama** `_classify_wall_node`.

Detalhe medido que guiou o desenho do oráculo: as paredes em
`walls_to_create` chegam **já esticadas até a FACE da parede vizinha**
(não até a interseção dos eixos) — um nó `L_CORNER` medido tinha as duas
pontas a ~7-8cm do ponto do nó (metade da espessura de 14cm), não
coincidentes entre si. Por isso o oráculo usa a **interseção dos EIXOS**
(retas infinitas) como ponto-candidato a nó, e só depois verifica, parede
a parede, se a ponta REAL fica perto o bastante (dentro de meia espessura
da parede vizinha + folga) para "terminar ali", ou se o eixo só "passa"
por ali no meio do vão.

Aplicado a cada ponto observado nos 60 nós divergentes (`out_divergent_nodes.json`,
campo `oracle_verdicts_per_observed_point`): nos casos amostrados, o
oráculo concorda com a classificação do motor em ambos os pontos
observados de cada nó divergente de posição — a divergência típica é
literalmente "mesmo grupo de paredes, mesmo veredito, ~1cm de diferença
de posição do centróide", não uma reclassificação incorreta.

**Limitação conhecida e documentada** (`oracle.py`, topo do arquivo): no
censo COMPLETO (`classify_all`, avaliando TODOS os ~230-270 pontos-
candidato de uma vez), paredes-toco muito curtas (~4-5cm, trechos entre
aberturas) podem cair dentro da margem de meia-espessura de um nó vizinho
de verdade e inflar `n_terminating` ali, virando `AMBIGUOUS` onde o motor
viu um nó limpo. Isso não invalida o oráculo aplicado a um ponto
específico (uso principal: arbitrar nós divergentes, seção 5 acima); só
afeta a comparação agregada de censo completo (usada como referência
adicional, não como veredito único) — ver seção 7.

## 7. Experimento "sort falso" (canonical sort)

`run_oracle_divergence.py::canonical_sort_experiment` — entrada ordenada
por uma chave geométrica canônica (`variants.geometric_sort`), rodada 5
vezes seguidas:

```
CANONICAL_SORT_MAKES_REPEATABLE = true
```

As 5 execuções produziram o MESMO fingerprint global. **Isso não prova
correção.** Comparando os 273 nós desse resultado estável com o oráculo
independente (`out_canonical_sort_experiment.json`):

```
node_agreement_with_oracle = {"agree": 183, "disagree": 88, "no_oracle_point_nearby": 2}
```

183/273 (67%) concordam; 88 discordam (a maioria cai na limitação
documentada na seção 6 — grupos de paredes quase-colineares onde o
próprio oráculo também não consegue decidir uma classificação limpa e
cai em `AMBIGUOUS`, não uma discordância de "o motor errou, o oráculo
tinha razão"). **Conclusão explícita para a CONTA 1**: um `sort()` das
paredes antes de rodar o motor (sem tocar a lógica de clusterização em
si) É SUFICIENTE para tornar o resultado repetível nesta bateria — mas
"repetível" não é o GATE; "bate com uma reconstrução geométrica
independente nos pontos que hoje divergem" é (ver GATE D4). Uma correção
que apenas ordenar a entrada e devolver 1 fingerprint sem checar isso
está mascarando o sintoma, não resolvendo a causa raiz da seção 3.

## 8. Downstream — variação entre as 24 ordens

| métrica | min | max | spread |
|---|---|---|---|
| pieces | 10566 | 10696 | 130 |
| non_modular | 3023 | 3111 | 88 |
| intersection_failures | 200 | 200 | 0 |
| alignment_conflicts | 0 | 0 | 0 |
| collisions | 1034 | 1051 | 17 |
| door_void_violations | 290 | 290 | 0 |
| C09 | 1107 | 1214 | 107 |
| C04 | 531 | 600 | 69 |
| B19 | 661 | 896 | 235 |
| runtime_s | 1.96 | 3.39 | 1.42 |

`intersection_failures`, `alignment_conflicts` e `door_void_violations`
ficaram ESTÁVEIS (spread 0) nesta bateria — não significa que essas
métricas sejam imunes ao não-determinismo em geral, só que, neste
projeto, nenhuma das 24 ordens testadas cruzou um limiar que as movesse.
`B19` (peça de amarração de nó) teve a maior variação relativa
(661-896, quase 36%) — consistente com a causa raiz estar na Etapa 2
(grafo de nós): toda vez que um cluster de nó se forma diferente entre
ordens (seção 5), as peças de amarração daquele nó (B19/B34/B54) mudam
de contagem.

## 9. `CR-BLOCK-01` — não confundir com este bug

`alignment_conflicts` ficou em **0/0/0** (min=max=0) nas 24 ordens desta
bateria — consistente com `CR-BLOCK-01` (busca de amarração vertical
completa, `nuvem/REGRAS_MODULACAO_BLOCOS.md` seção 27, já implementado
nesta `main`) continuar funcionando e não reintroduzir a falha de
`sem_alinhamento_vertical` que existia antes dele. O não-determinismo
medido aqui é uma questão SEPARADA: mesmo com `CR-BLOCK-01` correto para
QUALQUER ordem individual, a ORDEM em si já muda o resultado (contagens
de L/T/X, posições de peça, `B19`/`C09`/`C04`) — não é um retrocesso do
prisma, é uma dimensão de bug ortogonal. Uma correção futura do
determinismo não deve, por engano, tratar essa variação de `B19`/L/T/X
como se fosse uma regressão do `CR-BLOCK-01` (não é — é a mesma classe de
bug que motivou esta auditoria).

## 10. Gates para a CONTA 1

Definidos **antes** de ler `claude/block-determinism-graph` (ainda não
lida nesta sessão). Não serão flexibilizados depois de ver a
implementação da CONTA 1 só para fazê-la passar.

| Gate | Critério |
|---|---|
| **D1** | `wall_graph_node_positions` (e todas as camadas acima dela) fingerprint = 1 em TODAS as ordens testadas (mínimo: as 24 desta auditoria) |
| **D2** | Cada identidade geométrica de nó (tipo + conjunto de paredes dos braços) produz UMA classificação, igual em todas as ordens — nenhuma identidade muda de L_CORNER/T_INTERSECTION/X_INTERSECTION/FREE_END/STRAIGHT_CONTINUATION/AMBIGUOUS entre ordens |
| **D3** | `wall_end_to_node` equivalente entre ordens (mesma parede+ponta aponta pro mesmo nó geométrico em todas as ordens) |
| **D4** | Nos nós que HOJE divergem (`out_divergent_nodes.json`, 60 identidades), o resultado da correção bate com o oráculo independente (`oracle.classify_point`) — não basta ficar estável, tem que bater com a reconstrução geométrica |
| **D5** | `global_result` (fingerprint de todas as peças físicas materializadas) = 1 em todas as ordens |
| **D6** | `coverage` (contagem de peças, `pieces`) não cai abaixo do MÍNIMO já observado nesta bateria para a ordem correspondente (10566) — a correção não pode "resolver" o determinismo devolvendo sistematicamente menos peça |
| **D7** | `CR-BLOCK-01` não regride: `alignment_conflicts` continua 0 no projeto principal (ou, se não-zero, com a MESMA causa já documentada em `REGRAS_MODULACAO_BLOCOS.md` 27.8, nunca uma nova) |
| **D8** | Contagem de L/T/X (por tipo) não piora: nenhuma ordem da correção deve produzir MENOS nós L/T/X resolvidos com sucesso (mais `AMBIGUOUS`/`intersection_failures`) do que o pior caso já observado nesta auditoria |
| **D9** | Runtime aceitável: dentro da mesma ordem de grandeza da faixa já medida aqui (1.96s-3.39s para 167 paredes/17 fiadas) — uma correção que travar o determinismo com um custo de runtime muito maior (ex.: força bruta O(n²) extra por fiada) precisa ser justificada explicitamente, não é gate automático de reprovação, mas exige nota no relatório da CONTA 1 |
| **D10** | O CONJUNTO de paredes antes do grafo (`input_wall_geometry`) não muda — a correção não pode "resolver" o determinismo removendo/fundindo/duplicando paredes; só a ORDEM/AGRUPAMENTO pode mudar, nunca a geometria de entrada em si |

## 11. Arquivos criados

```
nuvem/benchmark/diagnostics_block_determinism_audit/
  lib_det.py                        # plumbing, identidade geometrica, fingerprints em camadas, downstream
  oracle.py                         # oraculo geometrico independente de classificacao de nos
  variants.py                       # gerador das 24 ordens (8 oficiais + 16 adicionais)
  run_baseline_variants.py          # roda baseline + 23 variantes, fingerprints por camada
  run_oracle_divergence.py          # localiza nos divergentes + arbitra com o oraculo + canonical-sort
  out_variants_census.json          # saida de run_baseline_variants.py
  out_divergent_nodes.json          # saida de run_oracle_divergence.py (nos divergentes)
  out_canonical_sort_experiment.json  # saida de run_oracle_divergence.py (sort falso)
docs/BLOCK_DETERMINISM_AUDIT.md     # este arquivo
```

**ARQUIVOS DE PRODUÇÃO ALTERADOS: ZERO.**

---

# CONTA 2 — AUDITORIA BASELINE CONCLUÍDA.
# NENHUM CÓDIGO DE PRODUÇÃO ALTERADO.
# AGUARDANDO CONTA 1 PARA CROSS-AUDIT.
