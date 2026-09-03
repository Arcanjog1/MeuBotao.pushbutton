# RELATÓRIO FINAL — CR-BLOCK-ARM-ROLE-CONSISTENCY

## Estado recuperado da sessão

Esta CR é continuação direta de CR-BLOCK-ARM-ROLE-INVARIANCE (relatório
anterior, verdito NECESSITA AJUSTE: o fix "inward-reserve" trocava
`COVERAGE_MISSING_ROW` por `COVERAGE_ROW_MOSTLY_EMPTY` em vez de resolver
a causa raiz). O usuário rejeitou esse fix e pediu um mecanismo de
coordenação determinístico entre os dois nós que fecham a mesma parede,
formalizado ANTES de assumir 2-coloring como solução.

Ao retomar a sessão (após uma compactação de contexto), o estado do
working tree foi preservado sem nenhum `reset`/`checkout`/`pull`: a
branch `claude/cr-block-arm-role-invariance-7tezx4` já continha, sem
commit, o mecanismo de coordenação (`_coordinate_arm_role_nodes` e
auxiliares) e o workaround "inward-reserve" do CR anterior já removido.
Faltava apenas: 1 teste sintético de ciclo com premissa matemática
incorreta (corrigido nesta sessão — ver seção "Ciclos"), verificação
explícita dos casos reais nomeados pelo usuário (W022/TP1, W093/TP1,
W011/piloto), medição de `GAP_IN_ROW`/colisões, suíte completa, e este
relatório.

## Branch / HEAD

```
branch de trabalho     claude/cr-block-arm-role-invariance-7tezx4
HEAD inicial (sessão)  86db87d (docs: PROJECT_STATUS.md do CR anterior)
HEAD final              ver commit desta entrega, no topo do log
```

Nenhuma integração com `origin/main` foi feita nesta sessão (main avançou
externamente para o SHA pós-BENCH-Z informado pelo usuário — não foi
mesclado, conforme instruído explicitamente: "NÃO integre a main nesta
branch agora").

## Hipótese em que a sessão havia parado

A hipótese didática original ("um ciclo de nós L_CORNER só pode ter
comprimento PAR, porque a geometria ortogonal alterna eixo H/V a cada
90°, logo ciclo ímpar é geometricamente impossível") estava **incompleta
e foi corrigida nesta sessão** — ver "Contrato formal" abaixo. A prova
correta é puramente combinatória, não geométrica, e é mais forte: vale
para QUALQUER topologia, par ou ímpar, real ou sintética.

## Causa raiz

Sem mudanças em relação ao relatório anterior: `_l_corner_wall_pair`
(único ponto do arquivo que lê `arms[0]`/`arms[1]` por POSIÇÃO, não por
filtragem "a outra parede") usa a ordem de `node["arms"]` para decidir
qual parede vira `course_a` e qual vira `course_b` num nó L_CORNER de 2
arms. Como essa ordem hoje vem de `wall_pairing.py` na ORDEM DE ENTRADA
das paredes (não existe convenção canônica geométrica em `origin/main`
neste ponto), os DOIS nós que fecham as duas pontas da MESMA parede podem
escolher `course_a`/`course_b` de forma independente e contraditória —
fazendo uma fiada inteira (família A ou B) desaparecer da parede.

## Contrato formal de papéis A/B

Antes de qualquer decisão de algoritmo, o contrato exigido foi
formalizado assim:

**Entrada**: o conjunto de nós L_CORNER de exatamente 2 arms (`node["kind"]
== "L_CORNER"` e `len(node["arms"]) == 2`). Cada um desses nós, por
construção, tem EXATAMENTE 2 arms — nunca mais, nunca menos — e
`_l_corner_wall_pair` sempre lê `arms[0]` como papel 0 (`course_a`) e
`arms[1]` como papel 1 (`course_b`).

**Restrição a satisfazer**: para toda parede `w` que toca EXATAMENTE 2
desses nós (as duas pontas fechadas por L_CORNER), os papéis que `w`
recebe nos dois nós devem ser CONSISTENTES entre si — ou seja, a
combinação dos dois papéis não pode fazer com que uma família (A ou B)
fique sem NENHUMA peça em `w` (o defeito original). Não se exige "sempre
alternar" nem "sempre igual" — apenas que os dois nós concordem sobre o
que a parede recebe, e a busca é livre para decidir, POR PAREDE, entre
"mesmo papel nas duas pontas" e "papel trocado", desde que a decisão seja
GLOBALMENTE consistente entre nós que compartilham arestas.

**Variáveis de decisão**: para cada nó elegível, uma decisão booleana
`swap` (trocar `arms[0]`↔`arms[1]` ou não).

**Restrição por parede-aresta**: cada parede que toca 2 nós elegíveis
define uma restrição binária entre os `swap` dos dois nós (mesmo valor
ou valores opostos, calculado a partir de como a parede já está
referenciada em cada nó — ver `parity` no código).

Isso é, por construção — não por escolha prévia de "vamos usar
2-coloring" —, exatamente uma instância de **2-SAT com restrições
XOR / 2-coloring de grafo com arestas com sinal**: nós = vértices,
paredes-aresta = arestas rotuladas com uma paridade. A adoção de
2-coloring **emergiu da formalização**, não foi assumida a priori — é a
única estrutura que representa "duas variáveis booleanas ligadas por uma
restrição de igualdade/diferença" de forma exata.

## Solução implementada

`_coordinate_arm_role_nodes(nodes)`, em `nuvem/core/engine/wall_stepper.py`:

1. Elegibilidade: nós `L_CORNER` com exatamente 2 arms.
2. Grafo de coordenação: vértice = índice do nó; aresta = parede que toca
   EXATAMENTE 2 nós elegíveis (uma aresta por parede assim), com peso
   `parity = 1 ^ role_p ^ role_q` (`role_*` = 0 se a parede é `arms[0]`
   naquele nó, 1 se é `arms[1]`).
3. BFS por componente conexo, resolvendo `swap` por 2-coloring
   determinístico: tanto a escolha da RAIZ de cada componente quanto a
   ORDEM de visita dos vizinhos são ordenadas por
   `_canonical_node_sort_key(node)` = `(point.X, point.Y, node_index)` —
   NUNCA pela posição na lista de entrada nem por `wall_idx` — para que
   o resultado não dependa da ordem de `nodes`/`walls`/`arms` recebida.
4. Ao revisitar um nó já decidido por outra aresta com um valor
   conflitante, a política determinística é: MANTER a decisão já tomada
   e registrar a parede em `conflicts` (lista deduplicada e ordenada no
   final). Ver "Ciclos e casos impossíveis" — na prática este ramo nunca
   é alcançado para esta regra de elegibilidade, mas seu comportamento é
   testado e determinístico caso a premissa de elegibilidade mude no
   futuro.
5. Aplicação: para cada nó com `swap=True`, `node["arms"]` é invertido
   (`[a1, a0]`) e `neighbor_wall_idx`/`neighbor_end_index` recalculados —
   exatamente a convenção que `_classify_wall_node` já usa — mutando os
   MESMOS dicts que o chamador guarda (`solve_all_intersections` chama
   isso como primeiro passo, antes do loop principal por nó), então todo
   consumidor downstream automaticamente vê os papéis já coordenados.

`solve_all_intersections` agora devolve também `"role_conflicts"` (a
lista de `conflicts`, hoje sempre vazia nos casos testados).

## Por que é invariante

- **Arms order**: a decisão de swap é sobre CADA nó individualmente
  (papel calculado por comparação `wall_idx == arms[0][0]`, não por
  índice fixo), então trocar a ordem de `arms` na entrada só troca o
  ponto de partida do cálculo de `role_p`/`role_q` — a saída final
  (papéis coordenados) é a mesma, comprovado por
  `test_l_corner_simetrico_arms_invertidos_nao_perde_familia` e
  similares (a família da parede fica EXATAMENTE espelhada A↔B, nunca
  ausente).
- **Input wall order**: a ordenação de `wall_touches`/`adjacency` é
  irrelevante para o resultado — a raiz e a ordem de visita do BFS usam
  `_canonical_node_sort_key`, geometria pura, nunca a posição na lista;
  `test_ordem_de_arms_de_hoje_wall_pairing_ja_fecha_sem_intervencao_manual`
  e o teste de retângulo com nós/paredes permutados confirmam.
- **Endpoint reversal**: reverter os pontos de uma parede não muda qual
  nó ela toca em cada ponta, então não afeta `wall_touches`; testado em
  `test_l_corner_endpoint_reversal_equivalente_nao_perde_familia`.
- **Consistência entre as duas pontas da mesma parede**: é exatamente o
  que a aresta de coordenação impõe — por construção do grafo, não pode
  haver combinação em que os dois nós discordem sem isso aparecer em
  `conflicts` (e mesmo nesse caso residual, o resultado é determinístico
  — ver abaixo).
- **L, T, X**: T não tem ambiguidade de ordem (usa geometria
  `main_wall_idx`/`incoming_wall_idx`, fora do escopo desta CR) — testado
  como controle (`test_t_intersection_nao_perde_familia`) para confirmar
  que a coordenação NÃO interfere em T. X tem 4 arms — fora da
  elegibilidade de 2 arms desta função por construção — testado em
  `test_x_intersection_crossing_walls_invertido_nao_perde_familia`
  (comportamento herdado do CR anterior, sem regressão).

## Ciclos e casos impossíveis

A hipótese inicial ("ciclo ímpar de L_CORNER é geometricamente
impossível porque a geometria ortogonal alterna eixo H/V") foi
**substituída por uma prova mais forte e puramente combinatória**,
obtida ao tentar (e falhar) construir um ciclo sintético de 3 nós com
conflito residual:

Cada nó L_CORNER de 2 arms atribui, por construção, EXATAMENTE um papel
0 (`arms[0]`) e um papel 1 (`arms[1]`) às suas duas arestas — nunca 0/0
nem 1/1 no mesmo nó. Isso limita o grau de qualquer nó no grafo de
coordenação a no máximo 2 (um por arm), então qualquer componente conexo
é um CAMINHO ou um CICLO SIMPLES — nunca uma estrutura de grau maior.

Para um ciclo `v0..v(L-1)` com arestas `e_i=(v_i,v_{i+1})`: seja `s_i` o
papel de `e_i` no nó `v_{i+1}`; como `v_{i+1}` só tem 2 arms, o papel de
`e_{i+1}` em `v_{i+1}` é forçosamente o complemento `1 ^ s_i`. Somando
(XOR) a paridade das `L` arestas do ciclo, cada termo se cancela em pares
ao percorrer o ciclo inteiro (telescopagem) — o resultado é **sempre 0**,
**independente de `L` ser par ou ímpar**, e independente de qualquer
padrão de ordenação de `arms`.

**Conclusão**: um ciclo de nós L_CORNER de 2 arms é SEMPRE 2-colorável
(zero conflitos) — não porque a geometria real só produz ciclos pares
(isso também é verdade, mas é irrelevante para a prova), e sim porque a
estrutura combinatória (grau ≤ 2, papéis complementares forçados em cada
nó) torna qualquer ciclo — par OU ímpar — balanceado. O ramo `conflicts`
de `_coordinate_arm_role_nodes` é, para esta regra de elegibilidade,
**matematicamente inalcançável** — mantido como rede de segurança
determinística caso a elegibilidade seja estendida no futuro (ex.: nós
com mais de 2 arms participando da coordenação), não porque se espera
que dispare hoje.

Isso é testado por construção em
`test_ciclo_de_l_corner_nunca_gera_conflito_residual_par_ou_impar`: todas
as 2⁵=32 combinações de ordem de arms em ciclos de 3, 4 e 5 nós, mais
ciclos de 6 e 7 nós com padrão alternado — todas resultam em
`conflicts == []`, e o resultado é confirmado determinístico e invariante
à ordem de entrada da lista de nós.

## W042/TGD

Caso real original (CR anterior), reproduzido sinteticamente em
`_two_corner_plan()` com coordenadas fracionárias (300.37/322.19/300.0,
ruído de CAD real) — confirmado via `git stash` que o teste central
(`test_parede_com_dois_L_corner_nunca_perde_familia_inteira`, 4
combinações de swap) falha na base sem o fix para 2 das 4 combinações, e
passa com o fix nas 4. Sem regressão nesta sessão.

## W022/TP1

Achados nesta parede, comparando o estado pré-CR (A, SHA `7c9a681`) e o
estado atual (C, esta entrega):

| estado | achados em W022 |
|---|---|
| A (pré-CR) | `COVERAGE_MISSING_ROW`×8, `COVERAGE_ROW_MOSTLY_EMPTY`×9, `COMPENSATOR_EXCESS_IN_RUN`×8, `COMPENSATOR_AVOIDABLE`×1 |
| C (esta CR) | `COVERAGE_GAP_IN_ROW`×17, `COVERAGE_PARTIAL_WALL`×1, `COMPENSATOR_AVOIDABLE`×1 |

`COVERAGE_MISSING_ROW` e `COVERAGE_ROW_MOSTLY_EMPTY` foram ELIMINADOS
nesta parede (não reclassificados para outro achado crítico — viraram
`GAP_IN_ROW`, que é nível de severidade menor: lacuna dentro de uma
fiada que agora EXISTE, não fiada inteira ausente ou quase vazia).
`COMPENSATOR_EXCESS_IN_RUN` também desapareceu (efeito colateral
positivo não medido antes).

## W093/TP1

| estado | achados em W093 |
|---|---|
| A (pré-CR) | `COVERAGE_MISSING_ROW`×8, `COVERAGE_PARTIAL_WALL`×1, `COVERAGE_GAP_IN_ROW`×16 |
| C (esta CR) | `COVERAGE_PARTIAL_WALL`×1, `COVERAGE_GAP_IN_ROW`×34 |

`COVERAGE_MISSING_ROW` eliminado (8→0). `GAP_IN_ROW` sobe de 16 para 34 —
reclassificação explícita e esperada: as 8 fiadas que antes estavam
TOTALMENTE ausentes agora existem, mas com lacunas internas (melhor que
ausentes, ainda não perfeitas).

## Piloto

`W011/piloto_sintetico_2x2`: achados IDÊNTICOS nos três estados A/B/C —
`COMPENSATOR_CONSECUTIVE`×2, `COMPENSATOR_EXCESS_IN_RUN`×2,
`OPENING_MISSING_COUNTER_LINTEL`×1. Esta parede não é afetada pela
coordenação de papéis (não corresponde à topologia de 2 nós L_CORNER
fechando a mesma parede com papéis contraditórios) — confirma que a
mudança não introduz ruído em paredes fora do escopo do defeito.
O projeto piloto inteiro tem métricas de cobertura idênticas nos três
estados (`MISSING_ROW`=0, `MOSTLY_EMPTY`=8, `GAP_IN_ROW`=16, 124 achados
totais) — pequeno demais para conter a topologia do defeito original.

## Comparação A/B/C/D

- **A** — baseline antes de qualquer workaround (merge-base `7c9a681`).
- **B** — workaround "inward-reserve" do CR anterior (commit `963aa9b`,
  ainda no histórico desta branch, hoje sem efeito porque foi removido
  do arquivo de produção nesta sessão).
- **C** — coordenação de papéis (esta CR), SEM o workaround
  inward-reserve — estado atual, não commitado antes desta entrega.
- **D** — coordenação + workaround simultâneos: testado ainda na parte
  anterior desta mesma sessão (reintroduzindo uma variante simplificada
  do inward-reserve sobre a coordenação já funcionando) — os artefatos
  dessa experiência não foram preservados (o código foi revertido depois
  de confirmar o resultado), mas a conclusão medida foi: nenhuma
  combinação testada de coordenação+workaround superou a coordenação
  sozinha nos dois eixos (`MISSING_ROW` e `MOSTLY_EMPTY`) simultaneamente
  — o workaround não somava nada que a coordenação não resolvesse
  melhor, e ainda reintroduzia parte do custo de `MOSTLY_EMPTY` que a
  coordenação sozinha evita. Por isso o workaround foi mantido removido.
  Se for necessário auditar D com números exatos, isso exige refazer o
  experimento (não é uma alegação nova nesta entrega, é uma decisão já
  tomada e aplicada ao código).

TGD (167 paredes):

| métrica | A | B | C | C vs A |
|---|---|---|---|---|
| COVERAGE_MISSING_ROW | 265 | 145 | 258 | -7 |
| COVERAGE_ROW_MOSTLY_EMPTY | 171 | 309 | 153 | -18 |
| TOTAL_COVERAGE_CRITICAL | 436 | 454 | 411 | **-25** |
| COVERAGE_GAP_IN_ROW | 1934 | 1939 | 1961 | +27 (reclassificação) |
| JUNCTION_MISSING_BINDING | 24 | 24 | 23 | -1 |
| POSITION_OVERLAP (colisões) | 29 | 29 | 29 | 0 |
| PRISM_CONTINUOUS_JOINT (achados) | 702 | 702 | 691 | -11 |
| PRISM_CONTINUOUS_JOINT (paredes distintas) | 39 | — | 41 | **+2 (ver Riscos)** |
| achados totais | 5307 | 5430 | 5239 | -68 |

TP1 (96 paredes):

| métrica | A | B | C | C vs A |
|---|---|---|---|---|
| COVERAGE_MISSING_ROW | 16 | 16 | 0 | **-16** |
| COVERAGE_ROW_MOSTLY_EMPTY | 27 | 27 | 18 | -9 |
| TOTAL_COVERAGE_CRITICAL | 43 | 43 | 18 | **-25 (-58%)** |
| COVERAGE_GAP_IN_ROW | 293 | 293 | 319 | +26 (reclassificação) |
| JUNCTION_MISSING_BINDING | 8 | 8 | 9 | +1 (ver Riscos — mesma junção, mirror de paridade) |
| POSITION_OVERLAP (colisões) | 18 | 18 | 18 | 0 |
| PRISM_CONTINUOUS_JOINT (achados) | 837 | 837 | 896 | +59 |
| PRISM_CONTINUOUS_JOINT (paredes distintas) | 50 | — | 53 | **+3 (ver Riscos — defeito novo)** |
| achados totais | 4964 | 4964 | 5198 | +234 |

Piloto (12 paredes): A=B=C em toda métrica de cobertura e prisma
(nenhuma mudança).

## Coverage

### MISSING_ROW
TGD 265→258 (-7); TP1 16→0 (**eliminado**); piloto 0→0. Nenhuma
regressão em nenhum projeto.

### MOSTLY_EMPTY
TGD 171→153 (-18); TP1 27→18 (-9); piloto 8→8. Nenhuma regressão. Este é
o eixo em que o workaround do CR anterior (estado B) regredia
fortemente (TGD 171→309); a coordenação sozinha não tem esse efeito.

### TOTAL_COVERAGE_CRITICAL (MISSING_ROW + MOSTLY_EMPTY)
TGD 436→411 (-25); TP1 43→18 (-25, -58%); piloto 8→8. Melhora nos dois
projetos onde a topologia do defeito existe, sem piorar em nenhum.
**G9 satisfeito nesta métrica especificamente** — mas ver G9/G10 no
veredito, porque a melhoria de cobertura não é a única condição das
gates.

### GAP_IN_ROW
Sobe em ambos: TGD +27 (1934→1961), TP1 +26 (293→319). Esperado e
explícito — é exatamente a reclassificação "fiada inteira ausente" →
"fiada presente com lacuna", confirmada caso a caso em W022/W093 acima:
severidade menor, cobertura real maior. Não é uma métrica escondida —
está reportada aqui e nas tabelas acima sem filtragem.

## Prisma

`PRISM_CONTINUOUS_JOINT` cai em contagem bruta de achados no TGD
(702→691) mas SOBE no TP1 (837→896); em NÚMERO DE PAREDES DISTINTAS
afetadas, sobe nos dois projetos (TGD 39→41, TP1 50→53). Isso é tratado
em detalhe em "Riscos" abaixo — é a principal pendência desta entrega.

## Aberturas

Nenhuma mudança nesta sessão: `wall_pairing.py`/`geometry.py`/regras de
abertura não foram tocados, e a coordenação de papéis não altera a
lógica de aberturas. `OPENING_BLOCK_CROSSES_JAMB`/`OPENING_BLOCK_INSIDE_DOOR`
não aparecem nas listas de códigos monitorados acima com variação — não
há achado novo desses códigos atribuível a esta CR.

## Compensadores

Efeito colateral positivo observado em W022/TP1: `COMPENSATOR_EXCESS_IN_RUN`
(8 achados) desaparece nessa parede ao eliminar `MISSING_ROW`/`MOSTLY_EMPTY`
(a fiada que passa a existir corretamente não gera mais um padrão de
compensador excessivo). Não foi feita varredura agregada de compensadores
no corpus inteiro nesta sessão — o efeito medido é local a W022.

## Collisions

`POSITION_OVERLAP` (proxy de colisão no benchmark): idêntico nos três
projetos entre A e C (TGD 29/29, TP1 18/18, piloto 0/0) — nenhuma
colisão nova, nenhuma resolvida no corpus real. O teste sintético
`test_solve_l_corner_considera_reserva_do_encontro_na_outra_ponta_da_mesma_parede`
(`tests/test_script.py`) confirma que a colisão de mesma-fiada que o CR
original media (duas peças da mesma família disputando o mesmo espaço
numa parede curta entre dois L_CORNER) deixa de ocorrer com a
coordenação — `validate_same_course_collision` passa a não encontrar
nada nesse caso, e as duas pontas da parede curta passam a alternar A/B
corretamente (antes, o teste antigo esperava a colisão como comportamento
"conhecido"; agora ela não acontece mais e o teste foi atualizado para
provar isso).

## Determinismo

Coberto por construção (`_canonical_node_sort_key` como única fonte de
ordem, nunca a lista de entrada) e testado explicitamente: mesma entrada
roda duas vezes → mesmo resultado; lista de nós permutada → mesmo
resultado; arms permutados em qualquer nó → família final apenas espelha
A↔B na MESMA parede, nunca some; endpoints revertidos → equivalente à
não-reversão.

## Testes sintéticos

`tests/test_block_arm_role_invariance.py`, 16 testes, todos passando:
nó único (arms invertidos, ambas as pontas), parede longa, múltiplas
fiadas, endpoint reversal, T como controle (não afetado), X como
controle (não afetado), reordenação de paredes de entrada, retângulo
fechado real (ciclo par, 4 paredes, 0 conflitos), e o teste geral de
ciclo (par e ímpar, sintético, prova combinatória — ver "Ciclos e casos
impossíveis"). `tests/test_script.py`: 1 teste atualizado (colisão
deixa de ocorrer + alternância A/B confirmada na parede curta entre dois
L_CORNER).

Não foi construído teste sintético dedicado de topologia "U" separado —
a cadeia usada em `_two_corner_plan()`/nos testes de "parede longa" já
cobre a forma de caminho com 2+ nós L_CORNER em sequência, que é a
mesma estrutura de grafo (caminho) que uma planta em U produziria para
fins de `_coordinate_arm_role_nodes` (a função não distingue "formato U"
de "caminho reto" — só enxerga o grafo nó↔parede↔nó). Registrado aqui
para transparência, não como lacuna escondida.

## Reference Corpus

Não tocado (`nuvem/benchmark/projects/*/reference.json`,
`reference_score.json` intactos — apenas lidos para comparação, nunca
escritos nesta sessão).

## Production diff

Único arquivo de produção alterado: `nuvem/core/engine/wall_stepper.py`
(confirmado via `git diff --stat`). `wall_pairing.py`, `continuous_modulation.py`,
`wall_modeling.py`, `geometry.py`, `tolerances.py`, `modulation_math.py`
não foram tocados. Não foi necessário ampliar o escopo — a coordenação é
implementável inteiramente em `wall_stepper.py` porque toda a informação
necessária (`node["arms"]`, `node["kind"]`, `node["point"]`) já chega
pronta de `wall_pairing.py` como parâmetro de `solve_all_intersections`.

## Baselines

`nuvem/benchmark/projects/*/baseline.json` **não foram regravados** nesta
sessão (a regra do repositório é regravar só quando uma melhoria é
aceita explicitamente, em commit dedicado — não nesta entrega, dado o
veredito abaixo). Rodar
`tests/regression/test_benchmark_baselines.py -m slow` contra os
baselines atuais dá 2 falhas (TGD: regressão de categoria `prism`; TP1:
regressão crítica de `JUNCTION_MISSING_BINDING` + regressão de categoria
`prism`) — detalhadas em "Riscos".

## Gates G1–G12

| gate | descrição | status |
|---|---|---|
| G1 | causa reproduzida | ✅ (W042/TGD, sintético e determinístico) |
| G2 | coordenação A/B consistente entre endpoints | ✅ (prova combinatória + testes) |
| G3 | invariância a arms/input/endpoints | ✅ (testes dedicados, todos passam) |
| G4 | L/T/X sem regressão | ✅ (T e X como controle, sem mudança de comportamento) |
| G5 | ciclos/retângulos/U cobertos por teste | ✅ (retângulo real + ciclos sintéticos 3–7; "U" coberto indiretamente — ver nota em Testes sintéticos) |
| G6 | determinismo preservado | ✅ |
| G7 | TP1 não piora | ⚠️ PARCIAL — `TOTAL_COVERAGE_CRITICAL` melhora muito (-58%), mas `PRISM_CONTINUOUS_JOINT` piora (+3 paredes, +59 achados) e `JUNCTION_MISSING_BINDING` +1 (mirror de paridade da mesma junção) |
| G8 | piloto não piora | ✅ (idêntico em todas as métricas) |
| G9 | TOTAL_COVERAGE_CRITICAL melhora sem trade-off oculto | ✅ na métrica em si — TODOS os deslocamentos (GAP_IN_ROW, PRISM) estão reportados explicitamente acima, nada escondido |
| G10 | nenhuma regressão crítica nova | ❌ — ver Riscos: `PRISM_CONTINUOUS_JOINT` introduz um padrão novo (perda total de desencontro vertical) em 8 paredes do TP1 que não existia nem em A nem em B |
| G11 | baseline/reference intactos | ✅ |
| G12 | diff de produção restrito ao escopo autorizado | ✅ (só `wall_stepper.py`) |

## Riscos

**Risco principal, não resolvido nesta entrega**: a coordenação de
papéis introduz uma regressão nova e genuína em `PRISM_CONTINUOUS_JOINT`
(junta vertical alinhada entre fiadas consecutivas — quebra a regra de
amarração "alternância do vão menor entre fiadas", `REGRAS_MODULACAO_BLOCOS.md`
seção 11), medida em 8 paredes do TP1 (`W010, W021, W037, W041, W061,
W062, W076, W092`) onde TODAS as junções entre fiadas consecutivas (0–1,
1–2, ..., 15–16) passam a ter desencontro 0.00cm — perda TOTAL de
stagger ao longo de toda a altura da parede, não apenas um ponto
isolado. Padrão similar (16 fiadas alinhadas) em 2 paredes do TGD
(`W003`, `W137`) e um caso parcial numa terceira (`W117`, fiadas 11–16).

Diferença crucial em relação ao achado de `JUNCTION_MISSING_BINDING`
(+1 no TP1): aquele é comprovadamente a MESMA junção (W039/W041, ponto
(6177.2, 950.0)) com a paridade das fiadas espelhada (linhas ímpares
1,3,...,15 → linhas pares 0,2,...,16 — +1 só porque o total de fiadas
(17) é ímpar, então o lado par tem uma fiada a mais) — não é um defeito
novo, é o MESMO defeito pré-existente visível no lado oposto da
paridade. Já o padrão de prisma nas 8 paredes do TP1 **não tem esse
formato de mirror**: são paredes que em A não tinham NENHUM achado de
prisma e em C passam a ter TODAS as junções falhando — indica que a
coordenação, ao trocar qual parede é `course_a`/`course_b` numa ponta
L_CORNER, pode estar dessincronizando a peça de canto (B34/B54, cujo
"vão menor" deveria alternar de lado a cada fiada) da regra fixa
`letter = "A" if course_index % 2 == 0 else "B"` que rege o preenchimento
comum do resto da parede — hipótese não totalmente confirmada nem
corrigida nesta sessão (exigiria alterar a lógica de geração de peça de
canto em `solve_l_corner`/`solve_wall_free_fill`, dentro do escopo
autorizado, mas é trabalho adicional não verificado).

**Risco secundário**: o teste de regressão contra baseline.json
(`tests/regression/test_benchmark_baselines.py -m slow`) FALHA hoje para
TGD e TP1 por causa exatamente deste risco principal — confirmado que
o estado A (pré-CR, merge-base) passa limpo (`MELHORIA`) contra os
mesmos baselines, então as duas falhas são genuinamente introduzidas por
esta CR, não uma staleness pré-existente.

## Veredito

**NECESSITA AJUSTE**

A causa raiz do defeito original (perda de fiada inteira por
inconsistência de papel A/B entre as duas pontas de uma parede) está
RESOLVIDA de forma determinística, invariante e provada — gates
G1–G6, G8, G9 (na métrica de cobertura), G11 e G12 passam sem ressalva.
`TOTAL_COVERAGE_CRITICAL` melhora substancialmente nos dois projetos
reais onde a topologia do defeito existe (TGD -25, TP1 -25/-58%), sem
piorar em nenhum.

Mas esta sessão descobriu, ao medir explicitamente contra os baselines
armazenados (G10), uma regressão nova e não trivial em
`PRISM_CONTINUOUS_JOINT` — perda de alternância vertical de junta em
múltiplas paredes reais (8 no TP1, 2–3 no TGD) que não é um artefato de
reclassificação benigna como o caso de `JUNCTION_MISSING_BINDING`. Essa
regressão não foi corrigida nesta entrega — corrigi-la provavelmente
exige entender e ajustar como a peça de canto assimétrica (B34/B54) é
escolhida em função do papel coordenado, dentro de `wall_stepper.py`
(sem precisar ampliar escopo, mas sem garantia de que a correção seja
trivial).

Por isso a CR não está pronta para integração: o mecanismo de
coordenação em si é sólido e deve ser preservado (não voltar ao
workaround inward-reserve, comprovadamente pior), mas precisa de uma
iteração adicional focada em resolver o efeito colateral de prisma antes
de qualquer merge.

**Pare antes de qualquer merge.**
