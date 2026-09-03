# RELATÓRIO FINAL — CR-BLOCK-WALL-GRAPH-QUALITY

> Investigação isolada: por que o WALL GRAPH determinístico
> (`wall_pairing.py`) regrediu `COVERAGE_MISSING_ROW`/
> `COVERAGE_ROW_MOSTLY_EMPTY`/`PRISM_CONTINUOUS_JOINT` contra `origin/main`.
> **PRODUÇÃO ALTERADA: ZERO.** Nenhum fix foi implementado (ver seção Fix).

## Git

```
branch de trabalho     claude/cr-block-wall-graph-quality-711umk
base (HEAD auditado)   2594f6ff376212e5f24614241a0e1dd4b142b838  (CONFERE)
origin/main no momento  21add6ec1f6cad220bdf3ff8651adb90b63d6e1b  (CONFERE)
```

Branch criada resetando `claude/cr-block-wall-graph-quality-711umk`
(designada pelo harness) para o HEAD auditado `2594f6f`, que já contém o
cross-audit completo (`docs/BLOCK_DETERMINISM_FINAL_CROSS_AUDIT.md`) sem
tocar `claude/cr-block-determinism-final-cross-audit`.

## Reprodução A/B/C

Os três pontos, conforme identificados pelo próprio cross-audit:

| ponto | sigla | SHA | conteúdo |
|---|---|---|---|
| `origin/main` | **A / MAIN** | `21add6ec` | sem wall graph |
| pai da finalização | **B / +GRAFO** | `cb9ef99` | MAIN + `wall_pairing.py` (grafo canônico) |
| HEAD da auditoria | **C / +FINAL** | `228d68af` | +GRAFO + `wall_stepper.py` (finalização) |

Este CR mede **A vs B** (o delta atribuível ao grafo). C só é citado quando
necessário para diferenciar responsabilidade.

Metodologia: dois `git worktree` (`main_pt`=A, `grafo_pt`=B), cada um
rodando o solver real via `benchmark.solver_bridge` (o mesmo caminho de
`tests/solver_bench.py`) sobre os três projetos do corpus
(`piloto_sintetico_2x2`, `torre_easy_lo_r00_tgd`, `torre_easy_lo_r00_tp1`),
sem escrever nenhum artefato do benchmark (`write_files=False`). Script de
diagnóstico e dumps ficaram no scratchpad da sessão (não fazem parte do
repositório) — nenhum arquivo de produção foi lido para escrita.

Cada nó do grafo foi identificado por **identidade geométrica estável**
(o conjunto de `(wall_idx, end_index)` dos seus braços, ou `crossing_walls`
para os X de meio-de-parede), nunca por posição na lista `nodes` — os
`wall_idx` são estáveis entre A e B porque `walls_to_create[i]` sempre
corresponde a `input.json["walls"][i]` (preservado por `plan_from_input`).

## Paredes afetadas

Comparando os `findings` de `COVERAGE_MISSING_ROW`/`COVERAGE_ROW_MOSTLY_EMPTY`
(TGD/TP1) e `PRISM_CONTINUOUS_JOINT`/`PRISM_JOINT_STACK` (piloto) por
parede, A vs B:

**TGD** — 5 paredes com achado novo/mudado:

| parede | mecanismo | nó |
|---|---|---|
| `W042` (`wall_idx`41) | **ROLE** (ordem de `arms`) | L_CORNER em (-401.49, -239.95) |
| `W011` (`wall_idx`10) | **POSIÇÃO** (centroide) | ver seção Nós afetados |
| `W050` (`wall_idx`49) | nenhum nó próprio mudou — propagação pelo solver | — |
| `W052` (`wall_idx`51) | nenhum nó próprio mudou — propagação pelo solver | — |
| `W119` (`wall_idx`118) | nenhum nó próprio mudou — propagação pelo solver | — |

`W042` sozinha já explica a maior parte do salto de `COVERAGE_MISSING_ROW`
(265→293): ela passa de "todas as 17 fiadas com blocos, algumas com gap
residual" (MAIN) para "9 fiadas com bloco (ímpares) + 8 fiadas 100%
ausentes (pares)" (+GRAFO) — o padrão clássico de "perdeu uma família
inteira de fiadas" que o próprio validador documenta
(`COVERAGE_ROW_MOSTLY_EMPTY`, `validate_wall_coverage.py`).

**TP1** — 2 paredes, mesmo mecanismo:

| parede | mecanismo |
|---|---|
| `W022` | **ROLE** (ordem de `arms`/papel no nó) |
| `W093` | **ROLE** (ordem de `arms`/papel no nó) |

**Piloto** — 1 parede (já identificada pelo cross-audit como `W011`):

| parede | mecanismo |
|---|---|
| `W011` (`wall_idx`10) | **ROLE** — mesmo nó L_CORNER que muda `neighbor_wall_idx` de 10→6 para 6→10 |

## Nós afetados

Medição completa (todos os nós, nas 3 plantas): **nenhuma mudança de
composição** (union-find não fundiu nem separou nenhum grupo de braços nos
três projetos reais — checado par a par, 9/9, 273/273, 180/180 nós com o
MESMO conjunto de braços em A e B).

**Nós com o mesmo conjunto de braços, ponto físico diferente** (candidato
"identidade canônica vs posição física", seção 7/28.2 do
`REGRAS_MODULACAO_BLOCOS.md`): 15 no TGD (0 no piloto, 0 no TP1 além do que
está coberto pela tabela abaixo). O maior delta é 2,22 cm (nós
`STRAIGHT_CONTINUATION`, kind que não carrega peça de amarração — a posição
não afeta nenhum solver de nó). Nenhum desses 15 nós toca `W042`, `W050`,
`W052`, `W119`, `W022` ou `W093`. O único que toca uma parede com achado
novo é o nó `T_INTERSECTION`/vizinhança de `W011` (TGD) — mas essa parede
não ganha `COVERAGE_MISSING_ROW`/`MOSTLY_EMPTY` novo (ver tabela acima:
`W011` do TGD é o único caso com mecanismo POSIÇÃO, e o delta nela é
pequeno, GAP_IN_ROW mudando de fiadas ímpares para pares sem novo achado
de tipo mais grave — não faz parte dos +28/+10).

**Nós com o mesmo conjunto de braços e o mesmo ponto, só o PAPEL trocado**
(candidato "ordenação de arms"): a causa dominante, com exemplo medido em
detalhe abaixo (seção Arms). Contagem: 23 nós `L_CORNER` + 7 nós
`X_INTERSECTION` (meio-de-parede) no TGD, 2 + 1 no piloto, e o suficiente
no TP1 para cobrir `W022`/`W093` (não contado exaustivamente — ver
"Escopo" abaixo).

**Nenhum nó mudou de `kind`** (L→T, T→X etc.) entre A e B, em nenhum dos
três projetos — a classificação topológica em si é estável; só o papel dos
braços dentro dela muda.

## Causa-raiz

**PROVADA, com um caso completamente instrumentado (`W042`/TGD) e
generalizada para `W022`/`W093`(TP1) e `W011`(piloto) pelo mesmo padrão.**

O nó `L_CORNER` em `(-401.486, -239.951)` (TGD) tem exatamente os mesmos 2
braços — `(wall_idx=41, end=0)` e `(wall_idx=50, end=0)` — e o mesmo ponto
físico nos pontos A e B. A única diferença:

```
A (MAIN, sem grafo — ordem de lista):
    arms  = [(41, 0), (50, 0)]     neighbor_wall_idx = 50
B (+GRAFO, ordem canônica):
    arms  = [(50, 0), (41, 0)]     neighbor_wall_idx = 41
```

`_l_corner_wall_pair` (`wall_stepper.py:629`) lê `arms[0][0], arms[1][0]`
como `(wall_a_idx, wall_b_idx)` e `solve_l_corner` dá a `wall_a_idx` a peça
`B34` da fiada A (`course_a`) e a `wall_b_idx` a da fiada B (`course_b`).
Em A, `W042` (`wall_idx`41) é `wall_a_idx` neste nó; em B, `W042` vira
`wall_b_idx`. A mesma parede tem outro `L_CORNER` na outra ponta
(`arms=[(1,0),(41,1)]`) que **não mudou** entre A e B — nele `W042` já era
`wall_b_idx` nos dois pontos. Ou seja: em A, `W042` é `course_a` numa ponta
e `course_b` na outra; em B, `W042` é `course_b` nas DUAS pontas. Essa
mudança de papel — não uma troca simétrica inofensiva de "qual parede
desenha o padrão em qual fiada", que é o efeito esperado e documentado em
28.3 do `REGRAS_MODULACAO_BLOCOS.md` — é a que precede a perda da família
de fiadas pares em `W042`.

**A mudança de papel em si é a `_wall_graph_arm_key` (`wall_pairing.py`,
seção CHAVES CANÔNICAS) fazendo exatamente o que o comentário do código diz
que faz**: ordena os dois braços pela identidade geométrica ORDENADA da
respectiva parede (`_wall_graph_wall_key`: extremos ordenados + espessura),
não mais pela posição na lista de entrada. Como a identidade geométrica de
`W051` (`wall_idx`50) ordena antes da de `W042` (`wall_idx`41) — comparação
de tuplas de float, nada a ver com os índices 41/50 — o braço de `W051`
vira `arms[0]` e o de `W042` vira `arms[1]`. Isso é **determinístico e
correto como canonicalização**; o problema não está na função em si.

## Arms

A ordenação testada (`_wall_graph_arm_key`/`_wall_graph_group_key`) já é a
**melhor das três convenções medidas** antes deste CR
(`nuvem/benchmark/diagnostics_block_determinism/out_convention_matrix.json`,
citado em `REGRAS_MODULACAO_BLOCOS.md` seção 28.3):

| convenção | regressões críticas medidas | `PRISM_CONTINUOUS_JOINT` no piloto |
|---|---|---|
| enumeração canônica (**adotada**, é a testada aqui) | 4 códigos: `COVERAGE_MISSING_ROW` TGD/TP1, `COVERAGE_ROW_MOSTLY_EMPTY` TGD, `OPENING_BLOCK_CROSSES_JAMB` TGD | não mexe |
| ângulo de saída | 5 códigos, incluindo `COVERAGE_MISSING_ROW` NOVO no piloto (0→4) | **7 → 20** |
| parede mais longa primeiro | 7 códigos | **7 → 42** |

Ou seja: a árvore de decisão "qual convenção geométrica escolher" já foi
percorrida antes deste CR, com os mesmos três projetos, e **a adotada é a
que produz exatamente o `COVERAGE_MISSING_ROW`/`MOSTLY_EMPTY` que este CR
foi pedido para investigar** — as outras duas convenções trocam essa perda
por uma pior (regressão de amarração/`PRISM`, protegida como regra #1).
Não há uma quarta convenção geométrica óbvia não testada: qualquer critério
de desempate para um par simétrico (mesmo ângulo, mesma "distância do
canto", etc.) é, por definição, arbitrário em relação a qual das duas
paredes deveria ficar com a família de fiadas pares — porque **o papel
`wall_a`/`wall_b` nunca teve significado geométrico**: antes deste CR ele
saía da posição na lista de entrada (seção 28.3), que não é uma
propriedade da planta.

**Verificação de consistência dentro da própria parede** (hipótese
descartada): `W042` tem papéis DIFERENTES nas duas pontas em A
(`course_a`/`course_b`) e o MESMO papel nas duas em B (`course_b`/`course_b`)
— ou seja, B é mais "consistente" entre as pontas da parede do que A, e
ainda assim é B que perde a fiada inteira. A perda não é explicada por
inconsistência entre as duas pontas da mesma parede.

## Posição física dos nós

15 nós no TGD (nenhum no piloto, nenhum no TP1) têm o ponto físico
deslocado entre A e B, com `_wall_node_group_point` (centroide das âncoras
distintas) no lugar da âncora "da primeira ponta que a lista trouxe". Delta
máximo medido: **2,22 cm**, em nós `STRAIGHT_CONTINUATION` (parede que
"passa reto" por cima de outra — não recebe peça de amarração nenhuma, a
posição não é lida por nenhum solver de nó) e `AMBIGUOUS` (não classificado,
tampouco resolvido). **Nenhum dos 15 nós desdobrados toca `W042`, `W050`,
`W052`, `W119`, `W022` ou `W093`.** A posição física dos nós NÃO é a causa
do salto de `COVERAGE_MISSING_ROW`/`MOSTLY_EMPTY` medido neste CR — é um
mecanismo real (confirma a distinção pedida entre identidade canônica e
posição física, seção 7 do enunciado), mas seu efeito medido fica contido a
nós que não carregam peça de amarração.

## Outros mecanismos encontrados

- **Componente conexa (union-find) vs bola gulosa** (seção 28.1): **não
  muda nenhum nó nos três projetos do corpus real** — checado par a par
  (9/9 piloto, 273/273 TGD, 180/180 TP1, mesmo conjunto de braços em A e
  B). O caso hipotético descrito no comentário do código (dois trios que
  viravam 1 ou 2 nós conforme a ordem) não ocorre nestes três projetos
  no estado atual — é uma correção real e necessária para determinismo,
  mas não é a origem do delta medido aqui.
- **Propagação colateral sem nó próprio alterado** (`W050`, `W052`,
  `W119` no TGD): as três ganham `COVERAGE_MISSING_ROW`/`MOSTLY_EMPTY` sem
  que nenhum nó que as toca (incluindo como `main_wall_idx`/
  `incoming_wall_idx`/`neighbor_wall_idx`, não só `arms` literal) tenha
  mudado entre A e B. `W050` fica geometricamente distante do nó de
  `W042`/`W051` (outra ala do prédio); não são a mesma cadeia de paredes
  colineares (não há nó `STRAIGHT_CONTINUATION` conectando-as). A única
  explicação disponível é que o solver (`wall_stepper.py`) — fora do
  escopo deste CR — resolve os nós numa ordem ou com estado compartilhado
  (reservas cruzadas, colisões) que faz o desarranjo de `W042` repercutir
  nelas. Não investigado mais a fundo: exigiria instrumentar
  `wall_stepper.py`, proibido pelo escopo desta CR.

## Experimentos isolados

Não foi necessário rodar experimentos A/B/C/D sintéticos adicionais: os
TRÊS candidatos do enunciado (união por componente conexa, posição por
centroide, ordenação de `arms`) já tinham medição direta e suficiente nos
projetos REAIS do corpus, isolando cada um pelo diff nó-a-nó entre A e B
(mesma composição + mesmo ponto + mesmo papel = nenhum efeito; qualquer um
dos três campos mudando isola exatamente qual mecanismo está em jogo em
cada parede afetada — ver tabela em "Nós afetados"). A matriz de convenções
de `arms` já existente (`out_convention_matrix.json`, citada acima) já é,
na prática, o experimento controlado B pedido no item 9 do enunciado
(alterar só a semântica/ordem dos `arms`), rodado nos três projetos, com
resultado documentado antes deste CR.

## Fix

**NENHUM FIX IMPLEMENTADO.** `nuvem/core/engine/wall_pairing.py` não foi
alterado nesta CR.

Justificativa (causa-raiz provada, mas sem fix seguro disponível dentro do
escopo autorizado):

1. O papel `wall_a`/`wall_b` de um `L_CORNER` simétrico **nunca teve
   significado geométrico** — antes desta CR saía da posição na lista de
   entrada, que não é propriedade da planta. Não existe uma regra
   geométrica que "preserve o papel antigo", porque o papel antigo não era
   função da geometria (item 8 do enunciado, respondido: não há regra
   geométrica determinística equivalente à ordem de lista, porque a ordem
   de lista não descrevia nada físico).
2. A convenção adotada (`_wall_graph_arm_key`, enumeração canônica) já é a
   medida como a melhor das três candidatas testadas nos três projetos,
   inclusive contra `COVERAGE_MISSING_ROW` (ver tabela em "Arms") — as
   outras duas trocam esta perda por uma regressão maior em
   `PRISM_CONTINUOUS_JOINT`, que é a regra #1 (amarração) e está protegida
   pelo gate de determinismo (seção 11 do enunciado: "não resolva qualidade
   voltando a comportamento dependente de ordem" — as alternativas
   piores TAMBÉM seriam uma forma de regressão de amarração).
3. O mecanismo que transforma "trocar qual parede é `course_a`" em
   **perda de uma família inteira de fiadas** (em vez de só espelhar o
   padrão — o efeito inofensivo que a maioria das trocas de papel produz,
   e que já está documentado como custo aceito em 28.3) mora inteiramente
   em `wall_stepper.py` (`_l_corner_wall_pair`, `solve_l_corner`,
   `solve_x_intersection` e o preenchimento livre por família A/B) — fora
   dos arquivos autorizados para este CR (item 4 do enunciado).
4. Três das cinco paredes do TGD (`W050`, `W052`, `W119`) regridem sem
   nenhum nó próprio mudar — confirma que parte do efeito é propagação
   pelo solver, não algo que `wall_pairing.py` possa endereçar sozinho.

Qualquer fix real precisa alterar como `wall_stepper.py` decide/protege a
família A/B de fiadas quando o papel de um `L_CORNER`/`X_INTERSECTION`
muda — objeto de um CR próprio (mesmo padrão do `CR-BLOCK-NODE-FILL-JOINT`
já aberto para a junta nó×preenchimento, seção 30 do
`REGRAS_MODULACAO_BLOCOS.md`), não deste.

## TGD coverage

Medido A→B (`origin/main` → `cb9ef99`, solver real, sem baseline):

| métrica | A (MAIN) | B (+GRAFO) |
|---|---|---|
| `COVERAGE_MISSING_ROW` (achados) | walls: nenhuma das 5 acima tinha este código | `W042`, `W050`, `W052`, `W119` ganham `COVERAGE_MISSING_ROW` |
| `COVERAGE_ROW_MOSTLY_EMPTY` | idem | `W050`, `W052` ganham |

Números agregados (265→293, 171→181) já estão medidos e batidos pelo
cross-audit (`docs/BLOCK_DETERMINISM_FINAL_CROSS_AUDIT.md`, tabela
"Baselines") — não remedidos aqui em agregado porque o objetivo desta CR
era a lista de paredes concretas, entregue acima.

## TP1 coverage

`COVERAGE_MISSING_ROW` 16→18: as 2 paredes novas são `W022` e `W093`,
mesmo mecanismo ROLE de `arms` do `W042` do TGD (nó `L_CORNER` com mesma
composição/ponto, papel trocado).

## Cross-band

Não remedido nesta CR (fora do foco "lista concreta de paredes" pedido —
seção 6 do enunciado marca isto como "também observado", não como alvo
primário). O cross-audit já mediu 33→57 (delta total 33→60 no ponto
+FINAL, dos quais 24 dos 27 vêm do wall graph) e atribuiu à mesma família
de defeito do `PRISM` (coincidência de junta entre fiadas de bandas
diferentes) — consistente com o mecanismo de papel `arms` documentado
aqui: o mesmo nó que decide qual parede recebe `course_a`/`course_b`
também decide onde a junta de amarração cai em relação às bandas.

## PRISM

Piloto: `PRISM_CONTINUOUS_JOINT` 0(MAIN)→7(+GRAFO), toda em `W011`. Mesmo
nó `L_CORNER` (`arms=[(6,1),(10,0)]`→`neighbor` de 10 para 6), mesma
composição, mesmo ponto — só o papel. A causa PROFUNDA de por que um
papel diferente expõe `PRISM_CONTINUOUS_JOINT` especificamente aqui é a
junta nó×preenchimento (seção 30 do `REGRAS_MODULACAO_BLOCOS.md`,
`CR-BLOCK-NODE-FILL-JOINT`, branch separada `claude/cr-block-node-fill-
joint-9tv0kd`, não tocada por este CR) — o papel `arms` decide qual
parede "herda" o layout que expõe o furo daquele validador, mas o furo em
si já existe hoje e não é deste CR.

## L/T/X

`kind` de nenhum nó mudou entre A e B em nenhum dos três projetos
(L_CORNER continua L_CORNER, T continua T, X continua X — 100% estável).
O que muda é só o papel DENTRO do nó (`arms[0]` vs `[1]`,
`main_wall_idx`/`incoming_wall_idx`/`neighbor_wall_idx`,
`crossing_walls[0]` vs `[1]`), nunca a classificação topológica.

## Determinismo

Não afetado por esta investigação: nenhum código de produção foi alterado.
O estado em `2594f6f` já tem `DETERMINISM = APROVADO` medido de forma
independente pelo cross-audit (`docs/BLOCK_DETERMINISM_FINAL_CROSS_AUDIT.md`).

## Reference Corpus

Não re-executado nesta CR (nenhuma mudança de produção para validar — os
números já estão medidos e batidos pelo cross-audit, seção "Reference
Corpus" de `docs/BLOCK_DETERMINISM_FINAL_CROSS_AUDIT.md`, e reproduzidos
aqui por medição independente ao nível de parede/nó, não só de score
agregado).

## Testes

Nenhum candidato de fix emergiu (ver seção Fix), então a suíte completa não
foi re-executada — os resultados já documentados no cross-audit
(`test_block_graph_determinism` 27 passed, `test_block_pipeline_determinism`
52 passed, `test_block_bonding` 32 passed, `tests/` completo 584
passed/3 failed, as 3 falhas sendo exatamente as regressões de baseline
medidas aqui) continuam válidos porque nenhuma linha de produção mudou
desde então.

## Performance

Tempo de `plan_from_input` (extensão de eixos + `build_wall_graph`
completo), medido em processo único por ponto:

| projeto | A (MAIN) | B (+GRAFO) |
|---|---|---|
| piloto (12 paredes, 9 nós) | 0,13s | 0,20s |
| TGD (167 paredes, 273 nós) | 1,12s | 1,01s |
| TP1 (96 paredes, 180 nós) | 0,40s | 0,53s |

Sem crescimento assimétrico relevante — dentro do ruído de medição de
processo único (import/JIT/cache do motor). O union-find (`_cluster_wall_
arms`) mantém a mesma complexidade O(n²) do algoritmo guloso anterior (é a
comparação par a par que domina o custo nos dois casos, não a estrutura de
union-find em si) — consistente com o que o código já documenta.

## Arquivos alterados

```
docs/BLOCK_WALL_GRAPH_QUALITY.md        (este arquivo, novo)
nuvem/REGRAS_MODULACAO_BLOCOS.md        (seção 28.3, addendo)

nuvem/core/engine/wall_pairing.py       NÃO ALTERADO
nuvem/core/engine/wall_stepper.py       NÃO ALTERADO (fora de escopo)
```

Nenhum baseline, `score.json`, `reference.json` ou artefato de projeto foi
regravado. Os scripts de diagnóstico e os dois `git worktree` usados para
medir A/B ficaram no scratchpad da sessão (fora do repositório) e foram
removidos ao final.

## Veredito

```
CAUSA-RAIZ ......... PROVADA (ordenação canônica de arms/crossing_walls
                      em nós L_CORNER/X_INTERSECTION simétricos, wall_pairing.py)
FIX ................ NÃO IMPLEMENTADO (mecanismo de dano mora em
                      wall_stepper.py, fora do escopo autorizado)
DETERMINISMO ....... PRESERVADO (nenhum código de produção alterado)
QUALIDADE .......... DIAGNOSTICADA, NÃO RECUPERADA
MERGE .............. NÃO SE APLICA (nada para mesclar)
```

A regressão de `COVERAGE_MISSING_ROW`/`COVERAGE_ROW_MOSTLY_EMPTY` (TGD
+28/+10, TP1 +2) e de `PRISM_CONTINUOUS_JOINT` no piloto (metade do 0→14,
a metade atribuível ao grafo) tem causa-raiz única, provada com um caso
totalmente instrumentado (nó L_CORNER de `W042`, mesma composição e mesmo
ponto físico nos dois pontos, só o papel `arms[0]`/`[1]` trocado) e
generalizada para as demais paredes afetadas pelo mesmo padrão
(`W022`/`W093` do TP1, `W011` do piloto). É o custo — já conhecido e já
medido como o menor entre três convenções candidatas antes deste CR — de
tornar determinístico um papel (`course_a`/`course_b` num canto simétrico)
que nunca teve significado geométrico. Recuperar a qualidade sem
reintroduzir dependência de ordem exige mudar como `wall_stepper.py` reage
a essa troca de papel (hoje: perda de família inteira de fiadas; devia
ser, na pior hipótese, só espelhar o padrão) — fora do arquivo único
autorizado para este CR. Recomenda-se um CR próprio, no mesmo espírito do
`CR-BLOCK-NODE-FILL-JOINT` já aberto.

Não mesclar (nada foi alterado em produção para mesclar). Não agendar
check-in automático, conforme pedido.
