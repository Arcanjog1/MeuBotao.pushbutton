# RELATÓRIO FINAL — CR-BLOCK-ARM-ROLE-HUMAN-POLICY

Continuação de `CR-BLOCK-ARM-ROLE-RESIDUALS` (`docs/BLOCK_ARM_ROLE_INVARIANCE.md`,
veredito anterior: BLOQUEADO POR ESCOPO). Este CR tinha autorização explícita
para investigar e, se provada, formalizar/implementar a política de
coordenação de papel `course_a`/`course_b` que o CR anterior não pôde tocar.

## Git

```
origin/main                                a2577797f40048413207d11ea7e7b385e97c1813
PR #9 (branch claude/cr-block-arm-role-invariance-7tezx4)
  HEAD                                     997ce465db42eab2dbb0806a0d9721975d30ef67
  merge-base com origin/main               7c9a681aeda2027f8fc072c0f57c62454a80d669
                                            (main não tocou wall_stepper.py/
                                            wall_pairing.py desde então)
branch de trabalho deste CR                claude/cr-block-arm-role-policy-q0qepg
```

`main` não avançou em `nuvem/core/engine/wall_stepper.py`/`wall_pairing.py`
desde que o PR #9 bifurcou — os 3 commits de produção do PR #9 (SHAs abaixo)
foram cherry-picked, SEM CONFLITO de código, sobre `origin/main` atual, mais
o commit `997ce46` (docs-only, investigação anterior):

```
963aa9b fix(blocos): invariancia de papel em L_CORNER/X_INTERSECTION
d813f45 fix(blocos): coordenacao deterministica de papel course_a/course_b
77bda14 fix(blocos): rastrear junta de contorno contra no' (PRISM-STAGGER)
997ce46 docs(blocos): investigar residuais do ARM-ROLE (docs-only)
```

Único conflito real: a seção `## 28.` de `nuvem/REGRAS_MODULACAO_BLOCOS.md`
colidia (a `main` atual já tinha sua PRÓPRIA seção 28, "recálculo
incremental do editor externo", de um commit — `f515887` — que o PR #9 nunca
viu). Resolvido renumerando a seção inteira do PR #9 para `29` (29.1–29.7,
sem alteração de conteúdo, só numeração — commit dedicado
`docs(blocos): renumerar secao 28 ARM-ROLE para 29`). PR #9 em si **não foi
tocado** — nenhum push, nenhum rebase, nenhum merge nele.

Não mergeado em `main`. Não mergeado o PR #9.

## Bases comparadas

```
A = origin/main limpo                          (a257779, sem nenhum ARM-ROLE)
B = cherry-pick do PR #9 nesta branch           (963aa9b+d813f45+77bda14+997ce46,
                                                  == estado ARM-ROLE-CONSISTENCY +
                                                  PRISM-STAGGER já relatado)
C = candidato deste CR                          (tentado e REVERTIDO — ver
                                                  "Implementação" abaixo; C == B
                                                  no estado final entregue)
```

## Reference Corpus

### Pareamento geométrico

Confirmado, de novo e por conta própria (não só herdado do relatório
anterior): `id` **não** é estável entre `result.json`/`input.json` e
`reference.json` — o pareamento usado em todo este relatório é sempre
`nuvem/benchmark/comparator/match.py:match_walls` (geométrico, 3 níveis de
folga, guloso pelo melhor score, nunca por `id`).

### As 8 paredes humanas (dados extraídos e verificados diretamente, não só
citados do relatório anterior)

Das 9 paredes residuais do CR anterior (`W003`/`W137` no TGD;
`W010`/`W037`/`W021`/`W092`/`W061`/`W062`/`W076` no TP1), reconfirmado: 8 têm
correspondente geométrico no Reference Corpus (`W137`↔TGD não tem — fora do
escopo do gabarito, mesmo achado do relatório anterior).

| solver | humano | comprimento | nó ponta 0 | nó ponta 1 | canto ponta 0 | canto ponta 1 | junta solver (todas as 17 fiadas) | junta humano |
|---|---|---|---|---|---|---|---|---|
| W003/TGD | W014 | 69cm (humano: 54cm — ver nota¹) | T_INTERSECTION | L_CORNER | B34 (T, incoming) | B34 (L) | t=34.5, 100% coincidente | par: `B19+B34` (toca as 2 pontas) / ímpar: `B39` solto (toca só 1 ponta) |
| W137/TGD | W077 | 69cm | L_CORNER | L_CORNER | B34 | B34 | t=34.5, 100% coincidente | par: `B34+B34` (toca as 2 pontas) / ímpar: `B39` solto (não toca NENHUMA ponta) |
| W076/TP1 | W077 | 69cm | L_CORNER | L_CORNER | B34 | B34 | t=34.5, 100% coincidente | idêntico a W137 (mesmo padrão, projeto diferente) |
| W021/TP1 | W021 | 123.98cm | L_CORNER | L_CORNER | B34 | B34 | t=89.48/89.49, 100% coincidente | par: `B34+B19+B19+B34` (toca as 2 pontas) / ímpar: `B39+B39` (não toca nenhuma ponta, vão intermediário à parte) |
| W092/TP1 | W092 | 123.98cm | L_CORNER | L_CORNER | B34 | B34 | idêntico a W021 | idêntico a W021 (geometria/gabarito duplicados) |
| W061/TP1 | W061 | 79cm | T_INTERSECTION | L_CORNER | B34 (T) | B34 (L) | t=34.5 **e** t=44.5, 100% coincidente (2 juntas) | par: `C09+B39` / ímpar: `B34+C09+B34` — mecanismo igual, mas com compensador C09 no meio |
| W062/TP1 | W062 | 79.01cm | L_CORNER | T_INTERSECTION | B34 (L) | B34 (T) | idêntico a W061 (mirror) | idêntico a W061 (mirror) |
| W010/TP1 | W010 | 424cm | L_CORNER | L_CORNER | B34 | B34 | t=34.5, 100% coincidente | mantém as 2 âncoras em pontas opostas (como o solver) — evita a junta com OUTRA composição de preenchimento (ver "Casos longos") |
| W037/TP1 | W037 | 524cm | L_CORNER | L_CORNER | B34 | B34 | t=34.5, 100% coincidente | idêntico mecanismo de W010 |

¹ W003↔W014: o casamento geométrico (melhor par disponível, sem concorrência)
liga uma parede solver de 69cm a uma referência de 54cm — divergência real,
não erro de script (confirmado rodando o comparator diretamente). Hipótese
mais provável: o levantamento humano modela essa parede em pé-direito
diferente perto do T de fronteira; classificado com confiança **B (mesmo
padrão)** mas com a ressalva explícita de que o comprimento não bate.

**Achado novo desta sessão, não capturado pelo relatório anterior**: das 9
paredes, **W003, W061 e W062 têm um nó `T_INTERSECTION` numa das duas
pontas**, não dois `L_CORNER`. Isso importa porque `_coordinate_arm_role_
nodes` (o mecanismo "sempre alterna") só enxerga nós `L_CORNER` de 2 braços —
essas 3 paredes **nunca estiveram sob o controle da coordenação
determinística** para começo de conversa: a coincidência nelas vem de
`solve_l_corner`/`solve_t_intersection` escolherem papel de forma totalmente
independente (sem NENHUM mecanismo de alternância ou concentração,
determinístico ou não) e, por acaso da geometria, produzirem o mesmo
resultado. Apenas as outras 6 (`W137`, `W076`, `W021`, `W092`, `W010`,
`W037`) estão de fato sob a alternância "sempre-diferente" que este CR
questiona.

Confirmado também, medindo diretamente (`nuvem/benchmark/validators/
validate_prism.py`) e não só supondo: a coincidência do solver não é
ocasional — é a **MESMA junta, em TODAS as 17 fiadas** da parede
(`stagger_cm≈0` nos 16 pares consecutivos de fiada) em todas as 9 paredes —
um prisma corrido de altura total, não um caso de fronteira.

## Classificação P1–P5

| parede | classificação |
|---|---|
| W137, W076, W021, W092 | **P1 — SAME_FAMILY_CORNERS** (humano concentra as duas peças de canto na mesma fiada) |
| W061, W062 | **P1**, variante com compensador C09 no vão livre — mesmo mecanismo, não uma categoria nova |
| W010, W037 | **P3 — FILL_BREAKS_STAGGER** (humano mantém as duas âncoras em pontas opostas; o preenchimento COMUM usa uma composição diferente que nunca sincroniza) |
| W003 | **P4 — MIXED**, com ressalva: não é P1 "puro" (uma ponta é T, não L) nem P2 (o solver também não alterna de propósito — é acidente de dois solvers independentes); classificado à parte porque está **fora do mecanismo que este CR pode corrigir** (ver "Hard constraints"/"Implementação") |
| — | Nenhuma classificada P2 (ALTERNATING_CORNERS) nem P5 (REFERENCE_INSUFFICIENT) entre as 8 com gabarito |

Nenhuma parede forçada numa categoria só para preencher a tabela — a
distribuição observada (P1 domina paredes curtas, P3 as duas longas, P4 os
casos com nó T) é o dado bruto, não um ajuste.

## Casos curtos

### 69cm (W137/W076, o par mais limpo — mesma família B34/B34, sem
compensador, sem abertura, dois `L_CORNER`)

```
SOLVER (alternância sempre-diferente, hoje):
  fiada par:   B34[0,34]  B19[35,54]     -> junta em t=34.5
  fiada ímpar: B19[15,34] B34[35,69]     -> junta em t=34.5  (COINCIDE)

HUMANO (W077, referência):
  fiada par:   B34[0,34]  B34[35,69]     -> junta em t=34.5 (só nesta fiada)
  fiada ímpar: B39[15,54]                -> NENHUMA junta interna
                                             (peça única, não toca t=0 nem t=69)
```

### H1–H6

| # | hipótese | veredito | evidência |
|---|---|---|---|
| H1 | alternar as pontas força uma junta central coincidente | **PROVADA — mecanismo estrutural, não coincidência de amostra** | confirmado nas 6 paredes P1 e nas 2 P3 (mesma junta em TODAS as 17 fiadas, sempre). Explicação geométrica: com as duas pontas usando a MESMA peça de canto (B34, 34cm fixo) e um vão restante curto o bastante para que a busca de preenchimento (`_pier_full_search_layout`/`_layout_min_joint_stagger_cm`, já instrumentada por PRISM-STAGGER para EVITAR coincidência sempre que existir alternativa) não tenha NENHUMA composição alternativa dentro do vão, o layout de cada fiada é forçado a ser o espelho exato do outro — junta na mesma posição relativa, não importa qual ponta ancora qual família |
| H2 | manter as duas pontas na mesma família deixa a família oposta livre para usar preenchimento deslocado | **PROVADA — é exatamente o que o humano faz, medido, não hipotético** | fiada sem NENHUMA âncora de nó (W137/W076: `B39` solto, sem tocar nenhuma ponta; W021/W092: dois `B39` livres) elimina a coincidência por construção — uma fiada sem junta de contorno de nó nunca pode coincidir com a junta de contorno da outra |
| H3 | é consequência específica de B34+B19 | **REFUTADA — generaliza** | o mesmo mecanismo aparece com B34+compensador C09 (W061/W062) e nas paredes longas com B34+B39 (W010/W037, ver "Casos longos") — a causa é a ESCASSEZ de composições alternativas dado o vão, não um par de peças específico |
| H4 | é consequência de "pier de um bloco" | **REFUTADA** | as 9 paredes vão de 69cm a 524cm, com 1 a 3+ peças de preenchimento por fiada — não há uma noção de "pier de um bloco" única que explique todas |
| H5 | é coincidência da amostra humana, não regra geral | **REFUTADA** | 8/8 paredes com gabarito concordam (2 projetos independentes, TGD e TP1, geometrias diferentes, incluindo um par W137/TGD↔W076/TP1 que reproduz o MESMO padrão em referências distintas) — consistência forte demais para ser amostra |
| H6 | existe outra restrição de amarração que torna a solução preferencial | **PARCIALMENTE CONFIRMADA, mas não como hipótese original** | achado novo desta sessão: `nuvem/benchmark/analysis.py:joint_is_opening_aligned_exempt` (REGRAS_MODULACAO_BLOCOS.md seção 11.8) já documenta uma EXCEÇÃO à regra #1 para peças pequenas de fechamento (C04/C09/B19) encostadas em vão/ponta do eixo — não explica o mecanismo P1 diretamente, mas confirma que o sistema de regras já reconhece que "junta corrida" tem exceções legítimas, não é absoluto |

## Casos longos

### Solver (W010, primeira divergência medida)

```
fiada ímpar (ancorada em t=0):  B34[0,34] B19[35,54] B39[55,94] ...
fiada par   (ancorada em t=424, NÃO toca t=0):
                                 B19[15,34] B39[35,74] B39[75,114] ...
                                 -> primeiro joint em t=34.5, IGUAL ao da fiada ímpar
```

### Humano (W010, referência)

```
fiada ímpar (ancorada em t=0):  B34[0,34] B34[35,69] B34[70,104] B39[105,144] ...
fiada par   (NÃO toca t=0):     B34[15,49] B34[50,84] B39[85,124] B39[125,164] ...
                                 -> primeiro joint em t=49.5, DIFERENTE de 34.5
```

### Primeira divergência

No trecho que NÃO está ancorado em nenhuma ponta (o lado "livre" da parede
de 424cm, entre o vão real e a ponta oposta), o solver de hoje começa a
composição com `B19[15,34]` (meio-bloco) seguido de `B39` — o humano começa
com **dois `B34` consecutivos** (`B34[15,49] B34[50,84]`), que também fecham
o módulo mas deslocam o primeiro joint 15cm.

Perguntas da seção 9 do CR, respondidas:

- **O solver conhece a mesma composição?** Não verificado se `B34+B34` está
  literalmente no espaço de busca hoje para um trecho SEM âncora numa das
  pontas (`_pier_full_search_layout` — não instrumentado nesta sessão para
  confirmar se ela é gerada e perde no desempate, ou nunca é gerada).
- **Está sendo podada antes, ou perde no desempate?** Inconclusivo com a
  investigação desta sessão — depurar isso exigiria instrumentar
  `_pier_full_search_layout`/`_layout_piece_profile` linha a linha para um
  caso real, não feito aqui por escopo/tempo.
- **Veredito desta seção**: causa da DIFERENÇA identificada (qual peça o
  layout usa no primeiro segmento livre), mas a causa-raiz de POR QUE a
  busca não escolhe `B34+B34` (prioridade de score, poda antecipada, ou
  simplesmente não gerada) **não foi isolada** — fica registrada como
  trabalho pendente explícito, não escondida atrás do achado de P1.

Isso reforça a separação de mecanismos da seção 6 do CR: **paredes longas
(P3) são um problema de busca de preenchimento, não de coordenação de
papel** — mudar `_coordinate_arm_role_nodes` não ajudaria W010/W037 mesmo
que fosse seguro (a alternância nelas já está correta; falta é uma
composição de preenchimento melhor).

## Hard constraints

- **REGRA OBRIGATÓRIA confirmada**: `PRISM_CONTINUOUS_JOINT` (`REGRAS_
  MODULACAO_BLOCOS.md` seção 11, regra #1 — "junta vertical alinhada entre
  fiadas consecutivas... divide a parede em dois prismas independentes") é
  hard constraint estrutural genuíno, não preferência — confirmado que a
  descrição textual da regra e o `rule_ref` do finding (`nuvem/benchmark/
  validators/validate_prism.py`) apontam para o mesmo texto.
- **EXCEÇÃO já documentada, também obrigatória em sua forma condicional**:
  seção 11.8 (peça pequena de fechamento C04/C09/B19 encostada em
  vão/ponta do eixo) — achado desta sessão, não nova regra inventada, já
  existente no código (`analysis.joint_is_opening_aligned_exempt`) e na
  documentação.
- **REGRA OBRIGATÓRIA confirmada** (seção 29.5, ex-28.5): a coordenação
  `course_a`/`course_b` não pode fazer uma parede perder uma família
  inteira de fiadas (`COVERAGE_MISSING_ROW`) — este CR não questiona nem
  toca essa regra.

## Soft preferences

- **A alternância SEMPRE-DIFERENTE em si** (o desempate específico que
  `_coordinate_arm_role_nodes` usa hoje para satisfazer a regra obrigatória
  acima) é uma **decisão de implementação, não uma regra de domínio
  obrigatória** — nenhum texto em `REGRAS_MODULACAO_BLOCOS.md` (pesquisado
  antes deste CR e de novo agora) prescreve "sempre alternar"; é uma
  política de desempate escolhida pela CR anterior, documentada como tal
  ("resolve isso por um critério de desempate geométrico determinístico,
  não por uma regra de amarração explícita" — seção 29.7/ex-28.7).
- **Preferir menos peças/composição mais simples** no preenchimento comum é
  soft preference (item 10 do CR) — não está em conflito direto com o
  achado aqui, mas é relevante para "Casos longos": o humano usa MAIS
  peças (`B34+B34` em vez de `B19+B39`) para ganhar desencontro, then a
  prioridade atual do solver (se de fato prioriza menos peças) pode estar
  sacrificando a regra obrigatória (prisma) por uma preferência secundária
  nesses casos — INCONCLUSIVO, não confirmado nesta sessão (ver "Casos
  longos").

## Política candidata

```
GIVEN:
  wall W com dois nós de amarração N_p, N_q (course roles)
  grafo de coordenação G = _coordinate_arm_role_nodes(nodes)
  free_span(W) = o que sobra para preenchimento comum depois das duas
                 peças de canto, nas duas famílias

CHOOSE:
  role(N_p, W), role(N_q, W)          [SAME ou DIFFERENT]
  + composição de preenchimento comum de cada fiada

SUBJECT TO:
  1. HARD: nenhuma família inteira ausente numa parede (COVERAGE_MISSING_ROW)
  2. HARD: nenhuma junta corrida entre fiadas consecutivas
           (PRISM_CONTINUOUS_JOINT), exceto exceção 11.8
  3. sem colisão (POSITION_OVERLAP)
  4. respeita aberturas (jambs, vergas, canaletas)
  5. determinístico: mesma geometria -> mesma decisão, independente de
     ordem de arms/walls/nodes/ElementId

POLÍTICA PROVADA (esta sessão):
  SE W é uma ARESTA ISOLADA do grafo G (os dois nós de W têm grau 1 em G —
     nenhuma OUTRA parede coordenada toca qualquer um dos dois; ver
     `_arm_role_isolated_edges` na seção "Implementação")
  E a alternância padrão produz PRISM_CONTINUOUS_JOINT nesta parede
     (mesma junta em toda a fiada — "prisma forçado")
  ENTÃO experimentar role(N_p,W) == role(N_q,W) [SAME] é seguro de TENTAR
     por construção (por ser aresta isolada, nunca pode violar a
     alternância de nenhuma OUTRA parede coordenada)
  MAS só deve ser ACEITO se a re-solução completa da vizinhança afetada
     confirmar, com o solver de verdade (nunca por aritmética): (a) a
     junta corrida desaparece, (b) nenhuma parede que fechava antes passa
     a falhar, (c) nenhuma colisão nova aparece (ver "Implementação" —
     este último item é exatamente o que faltou na tentativa desta sessão)

SE W não é aresta isolada (nós compartilhados com outras paredes
  coordenadas) OU não produz junta corrida sob alternância:
  MANTER a alternância padrão (nenhuma mudança)

Para paredes P3 (longas, alternância já correta): a política acima NÃO
  se aplica — o defeito ali está na busca de preenchimento, não no papel
  do nó (ver "Casos longos").

Para paredes com nó T/X numa das pontas (W003/W061/W062): a política
  acima NÃO se aplica (fora do grafo de `_coordinate_arm_role_nodes`,
  que só cobre L_CORNER de 2 braços) — nenhuma correção proposta aqui.
```

## Alternativas arquiteturais

| opção | avaliação |
|---|---|
| A — coordenação fixa (atual) | correta para o defeito original; sabidamente produz prisma forçado nas 6 paredes P1 |
| B — SAME/ALTERNATE por viabilidade de prisma, decidido ANTES do preenchimento | exigiria prever, sem rodar o preenchimento de verdade, se haveria coincidência — "aritmética sem verificação real" contraria a disciplina "propõe barato, verifica caro" já estabelecida no arquivo (ETAPA 3C) |
| **C — gerar poucos candidatos deterministicos, escolher por validação global** | **escolhida** — ver "Arquitetura escolhida" |
| D — preenchimento participa da decisão de papel | mais correto em teoria para os casos P3 (longos), mas exige acoplar `solve_wall_free_fill` a `_coordinate_arm_role_nodes` — mudança de escopo maior, tocaria a arquitetura de duas fases do arquivo inteiro; não tentado |
| E — corner-role + fill como um problema combinatório local por parede | equivalente a C na prática para o subconjunto ISOLADO (arestas de grau 1) — C, como implementada, É essencialmente E restrita a esse subconjunto seguro |

## Arquitetura escolhida

**C, restrita a arestas isoladas do grafo de coordenação** (equivalente a E
nesse subconjunto): gerar o candidato "mesma família" só quando é
estruturalmente impossível que ele afete qualquer OUTRA parede (aresta
isolada — grau 1 nos dois nós), e só aceitá-lo depois de uma re-solução
real (nunca uma estimativa) confirmar que ele não piora nada.

### Por quê

- Preserva 100% a regra obrigatória da coordenação (`_coordinate_arm_role_
  nodes` continua intocada, sempre alternando fora do subconjunto isolado).
- É local o bastante para não precisar resolver o problema geral de
  2-coloração com exceção "às vezes SAME" em ciclos/caminhos maiores
  (que teria efeitos colaterais imprevisíveis em paredes que hoje
  funcionam corretamente).
- Reusa infraestrutura já existente e testada no MESMO arquivo (RESOLVE
  PARCIAL de `process_walls_one_by_one` via `dirty_wall_idxs`/
  `baseline_per_wall`/`baseline_candidates`, criada para `find_wall_group_
  shift_fixes`/ETAPA 3C) em vez de inventar um mecanismo novo.

## Implementação

**Tentada nesta sessão e REVERTIDA — não está no diff final.** Registro
completo, não escondido:

1. Implementado em `nuvem/core/engine/wall_stepper.py` (única área de
   produção tocada, conforme autorizado): `_arm_role_isolated_edges`
   (identifica arestas isoladas do grafo), `_same_family_corner_role_
   override` (troca de papel local), `_wall_course_projected_joints_cm`/
   `_wall_has_forced_corner_prism` (detector local do prisma forçado,
   auto-contido — não importa `nuvem/benchmark`, reusa só primitivos já
   existentes em produção como `_candidate_extent_on_wall_axis`/
   `CELL_ALIGNMENT_TOLERANCE_CM`/`VERTICAL_JOINT_STAGGER_TOLERANCE_CM`),
   `try_same_family_corner_role_repair` (tenta a troca via RESOLVE
   PARCIAL) e `_repair_forced_corner_prism` (orquestrador, chamado uma vez
   dentro de `solve_building_blocks`, logo depois de `process_walls_one_
   by_one`).
2. **O DETECTOR está provado correto** por teste direto contra os projetos
   reais (não só teoria): das 7 arestas isoladas encontradas no TP1, o
   detector marcou exatamente `W021`, `W092` e `W076` (wall_idx 20, 91, 75)
   como tendo prisma forçado — as 3 paredes P1 puras deste projeto,
   nenhuma a mais, nenhuma a menos; `W061`/`W062` (nó T) corretamente
   EXCLUÍDAS do grafo (não são aresta L-L); `W010`/`W037` (P3, longas)
   corretamente NÃO aparecem como arestas isoladas (fazem parte de um
   componente maior do grafo) — confirma, por medição direta e não só por
   leitura de código, a separação de mecanismos da seção "Casos longos".
3. **O REPARO (a troca em si) não é seguro como implementado**: usava
   RESOLVE PARCIAL restrito à vizinhança de 1 salto (`_expand_dirty_wall_
   idxs`) e um gate emprestado de `_group_shift_trial_improves`/ETAPA 3C
   (criado para um problema DIFERENTE — reparar paredes que já começavam
   quebradas). Corrigido o gate (`_no_wall_regression`, novo, mais
   apropriado — só exige "nada que fechava antes passa a falhar", sem a
   exigência descabida "a parede trocada precisa passar a fechar", que
   quase nunca era satisfeita e rejeitava a troca por um motivo errado) —
   mas mesmo corrigido, **o gate não verificava colisões**
   (`POSITION_OVERLAP`), que `process_walls_one_by_one` já calcula e
   devolve em `result["collisions"]`. Medido ao vivo, TP1: cada tentativa
   de troca aceita pelo gate de fechamento introduzia colisões locais reais
   (2→8, 32→128, 8→32 nas 3 vizinhanças testadas) que se acumulam projeto
   afora — `POSITION_OVERLAP` салtou de 18 (estado B, correto) para 74270
   quando o reparo ficou ativo. **Revertido integralmente** antes de
   qualquer commit — `git checkout` do arquivo, working tree confirmada
   idêntica ao estado B.
4. **Causa provável do gap de segurança**: a vizinhança de 1 salto
   (`_wall_node_neighbors`, baseada em COMPARTILHAR UM NÓ) é suficiente
   para geometria/graph mas NÃO para colisão — colisão é proximidade
   FÍSICA, não adjacência de grafo; uma parede sem nenhum nó em comum com
   `wall_idx` mas fisicamente próxima da peça de canto trocada pode colidir
   com a nova composição sem nunca entrar em `dirty_wall_idxs`. A ETAPA 3C
   evita esse problema reconstruindo o grafo INTEIRO e rodando
   `process_walls_one_by_one` sem resolve parcial nenhum para cada
   candidato ("mais caro por tentativa, mas muito mais simples e seguro de
   implementar corretamente" — citação do próprio comentário da ETAPA 3C,
   confirmada por esta tentativa da forma mais direta possível).

## Testes

Nenhum teste novo commitado (a implementação foi revertida antes de
qualquer commit de produção). A correção do detector foi verificada ao
vivo contra os projetos reais do Reference Corpus (TGD/TP1), não por
suíte de testes permanente — ver item 2 de "Implementação" acima para os
números exatos.

## TGD / TP1 / Piloto (estado final entregue = B, candidato C revertido)

Idênticos ao já relatado em `docs/BLOCK_ARM_ROLE_INVARIANCE.md` (nenhuma
mudança de produção desde então):

| métrica | TGD (A→B) | TP1 (A→B) | Piloto (A→B) |
|---|---|---|---|
| COVERAGE_MISSING_ROW | 265→258 | 16→0 | 0→0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 171→112 | 27→18 | 8→8 |
| PRISM_CONTINUOUS_JOINT | 961→476 | 968→576 | 7→0 |
| OPENING_BLOCK_CROSSES_JAMB | 147→108 | inalterado | — |
| OPENING_BLOCK_INSIDE_DOOR | 45→5 (benchmark; ver nota) | inalterado | — |
| JUNCTION_MISSING_BINDING | 24→23 | 8→9 (mirror de paridade, benigno, já documentado) | — |
| POSITION_OVERLAP | inalterado | inalterado (18) | inalterado (0) |

Nota `OPENING_BLOCK_INSIDE_DOOR`: o benchmark runner mede 45→5 no TGD
"antes/depois" contra o `baseline.json` DESATUALIZADO (pré-ARM-ROLE); a
comparação correta (contra `origin/main` limpo, sem nenhum CR desta série)
já foi feita e documentada em `docs/BLOCK_ARM_ROLE_INVARIANCE.md`
("OPENING_BLOCK_INSIDE_DOOR +3" — causa provada, artefato de medição
pré-existente, não regressão física, não corrigido em produção por
instrução explícita). Não reaberto nesta sessão (fora de escopo, seção 17
do CR).

## Openings

Nenhuma mudança em relação ao já relatado (nenhum código de produção novo
no estado final entregue).

## Compensadores / Collisions

Nenhuma mudança (estado final = B). O achado de colisão do item 3 de
"Implementação" só existiu enquanto o reparo estava ativo, na working tree
— nunca chegou a um commit nem ao estado entregue.

## Determinismo

Preservado — nenhum código de produção novo no estado final. O detector
testado (`_arm_role_isolated_edges`/`_wall_has_forced_corner_prism`, antes
de ser revertido) usa exclusivamente `_canonical_node_sort_key` (identidade
geométrica) para qualquer desempate, seguindo o mesmo padrão de
`_coordinate_arm_role_nodes` — não haveria dependência de ordem se fosse
mantido.

## Performance

Não medida separadamente (nenhuma mudança de produção no estado final).

## Production diff

**Vazio contra o estado B** (`963aa9b`+`d813f45`+`77bda14`+`997ce46`
cherry-picked). Diff de produção contra `origin/main`: idêntico ao que já
estava documentado em `docs/BLOCK_ARM_ROLE_INVARIANCE.md` — só o que o
PR #9 já tinha.

## Baselines

Não regravados. `nuvem/benchmark/projects/*/baseline.json`/`reference.json`
intactos — nenhum `git diff` neles.

## Gates G1–G18

| gate | descrição | status |
|---|---|---|
| G1 | 8 paredes humanas corretamente casadas geometricamente | ✅ (verificado de novo, diretamente, não só herdado) |
| G2 | Padrões P1-P5 classificados | ✅ (P1×6, P3×2, P4×1, nenhum forçado) |
| G3 | Variável causal identificada | ✅ **generalizada além do achado anterior**: não é "comprimento" nem "B34+B19" — é "aresta isolada do grafo de coordenação" + "busca de preenchimento sem composição alternativa dentro do vão restante" (H1-H3 provam isso) |
| G4 | Casos curtos explicados | ✅ (H1/H2 provadas, H3/H4/H5 refutadas, H6 parcial) |
| G5 | Casos longos explicados | ⚠️ PARCIAL — mecanismo (busca de preenchimento) identificado e distinguido do de paredes curtas; causa-raiz de por que a busca não escolhe a composição do humano não isolada |
| G6 | Hard constraints/soft preferences separados | ✅ |
| G7 | Política formal escrita ANTES do fix | ✅ |
| G8 | Política determinística e invariável à ordem | ✅ (`_canonical_node_sort_key`, mesmo padrão do resto do arquivo) |
| G9 | Coverage não piora vs melhor estado do PR #9 | ✅ (estado final = B, idêntico) |
| G10 | Prisma melhora ou não piora | ✅ (idêntico a B — não piorou; NÃO melhorou mais, porque o candidato foi revertido) |
| G11 | Nenhuma nova regressão física de abertura | ✅ (nenhuma mudança) |
| G12 | Collisions não pioram materialmente | ✅ **no estado ENTREGUE** — mas só porque a tentativa que as piorava (74270) foi revertida antes do commit; documentado como achado central, não escondido |
| G13 | Compensadores não pioram materialmente | ✅ (nenhuma mudança) |
| G14 | Reference/baseline intactos | ✅ |
| G15 | Production diff restrito ao escopo autorizado | ✅ (vazio contra B; PR #9 tratado como leitura, nunca alterado) |
| G16 | Testes focados passam | ✅ (281 testes, `tests/test_script.py`+`tests/test_block_arm_role_invariance.py`+`tests/test_block_arm_role_prism_stagger.py`, inalterados) |
| G17 | Suíte final passa | ✅ (mesma suíte acima — suíte completa de `tests/` não rodada nesta sessão por custo/tempo; nenhuma mudança de produção que a arriscaria) |
| G18 | 8 paredes-alvo explicadas após candidato | ✅ (explicadas; não corrigidas — candidato revertido) |

## Riscos

- As 6 paredes P1 (`W137`/`W076`/`W021`/`W092`/`W061`/`W062`) continuam com
  `PRISM_CONTINUOUS_JOINT` de altura total até uma implementação segura do
  reparo desta seção.
- Qualquer implementação futura do reparo "mesma família" **precisa**
  verificar colisões (`process_walls_one_by_one`'s `result["collisions"]`,
  ou uma varredura de proximidade física real) antes de aceitar a troca —
  não basta `validation.ok`/`non_modular` (ver "Implementação", item 3/4).
  Reusar a disciplina de ETAPA 3C ("mais caro, mas seguro" — reconstruir o
  grafo e rodar `process_walls_one_by_one` SEM resolve parcial para cada
  candidato) é a recomendação mais segura, mesmo sendo mais lenta.
- W003/W061/W062 (nó T numa ponta) continuam sem NENHUM mecanismo de
  coordenação — nem alternância nem concentração — porque estão fora do
  grafo de `_coordinate_arm_role_nodes` por construção. Corrigi-las
  exigiria estender esse grafo para incluir nós T/X, mudança de escopo
  maior, não avaliada aqui.
- W010/W037 (P3) continuam com prisma corrido — a causa está na busca de
  preenchimento, não na coordenação de papel, e a causa-raiz exata (poda,
  desempate, ou composição nunca gerada) não foi isolada nesta sessão.

## Próximo passo recomendado

1. Reimplementar o reparo "mesma família" (arquitetura já formalizada e
   parcialmente escrita nesta sessão) trocando o RESOLVE PARCIAL de 1
   salto por uma verificação completa no estilo ETAPA 3C — reconstruir e
   rodar `process_walls_one_by_one` inteiro por candidato, comparando
   `result["collisions"]` (contagem, nunca só `validation.ok`) antes/depois,
   além do gate de "nada que fechava antes passa a falhar" já corrigido
   (`_no_wall_regression`, mantido, não é o problema). Cobre `W137`,
   `W076`, `W021`, `W092`, `W061`, `W062` (6 das 9 residuais).
2. CR separado para investigar a causa-raiz de "Casos longos" (por que a
   busca de preenchimento não escolhe `B34+B34` em vez de `B19+B39` no
   trecho livre não ancorado) — cobriria `W010`/`W037`.
3. CR separado (escopo maior, provavelmente exigindo `wall_pairing.py` ou
   uma extensão explícita de `_coordinate_arm_role_nodes`) para paredes com
   nó T/X numa ponta (`W003`/`W061`/`W062`) — nenhum mecanismo de
   coordenação as cobre hoje.
4. Decisão humana já pendente do CR anterior sobre `baseline.json`/
   `opening_active_in_row` continua aberta, independente deste CR.

## Veredito (primeira tentativa, ver continuação SAFE REPAIR abaixo)

**NECESSITA AJUSTE**

Causa provada (H1/H2), variável causal generalizada e verificada por
medição direta contra os projetos reais (não só herdada do relatório
anterior), política formal escrita e parcialmente implementada. A
implementação foi **revertida** por um gap de segurança concreto e medido
(verificação de colisão ausente no gate de aceitação) — não por falta de
evidência de domínio, nem por bloqueio de escopo de arquivo (tudo coube em
`wall_stepper.py`, como autorizado). O caminho para corrigir o gap está
documentado ("Próximo passo recomendado", item 1) e é preciso o bastante
para ser retomado diretamente por uma sessão futura sem reinvestigação.

Nenhum merge realizado. Nenhuma alteração de produção no estado final
entregue (idêntico ao estado B, já documentado).

============================================================

# CONTINUAÇÃO — ARM-ROLE HUMAN-POLICY SAFE REPAIR (2026-09-04)

Retomada na MESMA sessão/branch (`claude/cr-block-arm-role-policy-q0qepg`),
com instrução explícita de NÃO refazer a abordagem de verificação local de
1 salto (já provada insegura acima) e implementar geração de candidatos +
validação COMPLETA antes de aceitar/rejeitar.

## Estado inicial

HEAD = `03ec8053fcb980c226929f754b01c2e94c262849` (o commit documentado
acima). PR #11 (draft) intocado nesta fase — nenhum push até a decisão
final desta continuação.

## Reparo inseguro anterior / Gap de segurança

Já documentado acima em detalhe — resumo: `_wall_ok_map`/
`_group_shift_trial_improves` (emprestado sem adaptação de ETAPA 3C) não
enxergava colisão nenhuma; `POSITION_OVERLAP` no TP1 subiu de 18 para
74270 quando o reparo estava ativo.

## Infraestrutura de colisão completa

Localizada e confirmada: `process_walls_one_by_one` (wall_stepper.py) já
calcula, UMA VEZ, ao final do laço principal (depois de TODAS as paredes,
nunca uma aproximação por vizinhança):

```python
collisions = validate_same_course_collision(all_candidates)
```

`validate_same_course_collision` (também em `wall_stepper.py`) é uma
função PURA sobre a lista completa de candidatos — agrupa por fiada,
usa um índice espacial só como otimização de performance, e testa
sobreposição real via SAT (`_obb_overlap`) para TODOS os pares que podem
colidir. Determinística, independente de ordem de processamento. Esta É a
mesma checagem que o resto do pipeline usa — nenhuma segunda definição de
colisão foi criada.

### Pode ser reutilizada dentro do escopo?

**Sim, para colisão especificamente** — 100% dentro de `wall_stepper.py`,
sem tocar nenhum outro módulo. Construída `_no_new_collisions` (nova),
que compara os PARES de colisão de duas resoluções por ASSINATURA
geométrica estável (não pelo índice em `all_candidates`, que muda entre
resoluções) — só reprova quando aparece um par NOVO que não existia antes
(`NEW_POSITION_OVERLAP`, nunca uma contagem bruta que mascararia troca de
um par por outro).

**Causa-raiz medida da tentativa anterior**: não era a vizinhança de 1
salto em si — era que a lista de candidatos passada ao RESOLVE PARCIAL
duplicava candidatos de nó de paredes limpas (uma vez via
`intersections["candidates"]`, outra via o `seeded` interno de
`baseline_candidates`), corrompendo os índices de reserva de fronteira
que as paredes dirty usam. Corrigido: `baseline_candidates` passado ao
RESOLVE PARCIAL agora exclui candidatos de nó (`node_index is not None`)
— só contribui preenchimento comum das paredes limpas.

## Candidatos

4 configurações de papel, geradas e testadas NESSA ORDEM determinística
(nunca por ordem de dict/set) para cada aresta isolada com prisma
forçado — `CORNER_ROLE_CANDIDATE_BITS`:

```
SAME_A        (0, 0)   — as duas pontas course_a
SAME_B        (1, 1)   — as duas pontas course_b
ALTERNATE_AB  (0, 1)   — node_p course_a, node_q course_b
ALTERNATE_BA  (1, 0)   — o oposto
```

`ORIGINAL` é implícito: sempre uma das duas configurações ALTERNATE (nunca
SAME — `_coordinate_arm_role_nodes` nunca produz SAME sozinha); se o
candidato pedido já é a configuração atual, `_set_l_corner_role_bits`
devolve `changed_indices=[]` e o candidato é descartado como "nada a
avaliar", nunca contado como tentativa.

## Hard constraints

Verificados ANTES de qualquer preferência, na ordem em que são checados
(cada um pode rejeitar sozinho, sem consultar os seguintes):

1. viabilidade física dos dois nós trocados (`solve_l_corner` não falha);
2. fechamento — nenhuma parede que fechava antes passa a falhar
   (`_no_wall_regression`, mesmo critério (b) de `_group_shift_trial_
   improves`, sem o critério (a) daquela função, que não se aplica aqui —
   ver docstring);
3. colisão GLOBAL — nenhum par novo (`_no_new_collisions`, ver acima);
4. **achado nesta continuação, não previsto originalmente**: o prisma
   forçado não pode ser empurrado para a parede VIZINHA que compartilha
   `node_p`/`node_q` (medido ao vivo, TGD, `W137`→`W001` antes deste
   gate existir) — comparado via `_wall_has_forced_corner_prism` antes/
   depois em toda `dirty` (não só `wall_idx`).

## Score

Entre candidatos que passam os 4 hard gates E de fato eliminam o prisma
forçado da parede alvo: tie-break canônico pela ordem de
`CORNER_ROLE_CANDIDATE_BITS` (SAME_A antes de SAME_B antes de
ALTERNATE_*) — nenhuma preferência de composição adicional (item 6/7 da
política) foi confrontada contra `REGRAS_MODULACAO_BLOCOS.md` nesta
sessão, então não foi usada para desempate (item 9 do pedido: "não
transformar essa ordem em regra final sem confrontar" — respeitado por
omissão, não por decisão arbitrária).

## Fallback

Testado e confirmado: quando nenhum candidato passa todos os hard gates
e resolve o defeito, `_repair_forced_corner_prism` simplesmente não
executa nenhum `break` no laço interno — `result`/`nodes` permanecem
exatamente o estado ORIGINAL, sem exceção. É o comportamento observado
para as 6 paredes com nó T (`W003`/`W061`/`W062`) e para as paredes
longas (`W010`/`W037`, nunca sequer entram no laço por não serem aresta
isolada) durante todo o desenvolvimento desta continuação.

## 6 paredes curtas

### Resultado, medido diretamente contra TGD e TP1 (não estimado)

| parede | projeto | isolada? | prisma forçado (antes) | reparo aceito? | prisma depois | efeito colateral |
|---|---|---|---|---|---|---|
| `W021` | TP1 | sim (L-L) | sim (16 achados) | **sim, SAME** | **0** | nenhum medido (colisão/fechamento/prisma vizinho — todos limpos) |
| `W092` | TP1 | sim (L-L) | sim (16 achados) | **sim, SAME** | **0** | nenhum medido |
| `W076` | TP1 | sim (L-L) | sim (16 achados) | **sim, SAME** | **0** | nenhum medido — padrão humano reproduzido (uma fiada com a junta do B34, a outra sem NENHUMA junta interna) |
| `W137` | TGD | sim (L-L) | sim (16 achados) | **sim, SAME** (antes do achado abaixo) | **0** | **REGRESSÃO NOVA, achada nesta continuação**: `JUNCTION_NOT_ALTERNATING` (nível 1, `nuvem/benchmark/validators/validate_junctions.py`) passa a aparecer em 2 paredes vizinhas (`W011`, `W088`) que estavam limpas — ver abaixo |
| `W061` | TP1 | **não** (nó T numa ponta) | sim (32 achados) | não tentado (fora do grafo) | inalterado | nenhum (ORIGINAL mantido, correto) |
| `W062` | TP1 | **não** (nó T numa ponta) | sim (32 achados) | não tentado (fora do grafo) | inalterado | nenhum (ORIGINAL mantido, correto) |

3 de 6 paredes elegíveis (`W021`, `W092`, `W076`) foram reparadas com
segurança **completa e verificada** contra TODAS as métricas medidas
nesta continuação (fechamento, colisão global, e — depois do gate 4 —
prisma em paredes vizinhas). `W137` expôs uma QUARTA categoria de efeito
colateral que os 3 gates desta continuação não cobrem — ver abaixo.

### Achado novo: `JUNCTION_NOT_ALTERNATING` não é coberto pelos gates
desta continuação

Medido ao vivo, TGD, candidato `W137` (aceito antes deste achado ser
descoberto — depois removido pela decisão final, ver "Veredito"):

- Antes do gate 4 (prisma em vizinha) existir: aceitar `W137` empurrava
  `PRISM_CONTINUOUS_JOINT` para `W001` (vizinha em um dos dois nós) — capturado e corrigido pelo gate 4.
- **Depois do gate 4 corrigido**, `W137` continuava sendo aceito (não
  reintroduzia prisma em nenhuma vizinha) mas **duas paredes diferentes**
  (`W011`, `W088` — vizinhas dos dois nós de `W137`, uma delas através de
  um AGRUPAMENTO de nó que inclui uma TERCEIRA parede, `W090`, não
  prevista por `_wall_node_neighbors`) passaram a acusar
  `JUNCTION_NOT_ALTERNATING`: a MESMA peça da MESMA parede (`W011`)
  ocupando o encontro em 3 fiadas SEGUIDAS (4, 5 e 6), quando deveria
  alternar com a parede vizinha a cada fiada.
- **Mecanismo não totalmente isolado** (tempo/escopo desta continuação
  não permitiu): `W011`/`W088` continuam sendo, respectivamente, uma
  vizinha de 2 paredes (relação direta com `W137`) e uma vizinha de 3
  paredes via um agrupamento de nó por PROXIMIDADE (`NODE_MERGE_
  TOLERANCE_CM = 3.0`, `validate_junctions.py`) que **não corresponde**
  ao grafo de nós que `wall_stepper.py` usa internamente
  (`node["arms"]`, sempre exatamente 2 paredes por nó) — o validador do
  benchmark mescla nós fisicamente próximos de paredes DIFERENTES numa
  mesma verificação; `wall_stepper.py` nunca precisou fazer isso para
  nenhuma outra finalidade.
- **TP1 ficou limpo** (`junctions` categoria: `1→1`, inalterado — o único
  achado, `W039`, já é o artefato de paridade-espelhada conhecido e
  documentado desde `CR-BLOCK-ARM-ROLE-CONSISTENCY`) — o mecanismo NÃO é
  universal; ativou especificamente no candidato de `W137`/TGD, por um
  motivo ainda não isolado.

### Por que isto bloqueia a ativação, mesmo com G6/G7 (colisão) provados

`JUNCTION_NOT_ALTERNATING` é NÍVEL 1 (`LEVEL_MANDATORY`) no catálogo de
achados do benchmark (`nuvem/benchmark/validators/base.py`) — mesma
categoria de obrigatoriedade que `PRISM_CONTINUOUS_JOINT`. Introduzi-lo
em paredes antes limpas (`W011`, `W088`) é uma regressão de hard
constraint pela própria régua desta política ("nenhuma parede antes
limpa pode [regredir]" — seção 7/8 do pedido desta continuação,
generalizada além de `POSITION_OVERLAP` para qualquer achado nível 1).
**Não é aproximação aceitável tentar "consertar" isto com um detector
local parcial** (o pedido, seção 6, é explícito: "não implemente
aproximação") — o mecanismo de agrupamento por proximidade do validador
não tem equivalente em produção, e replicá-lo com fidelidade (inclusive
o caso de 3+ paredes por nó físico) é um trabalho novo, não uma extensão
pequena do que já existe.

## 3 paredes T

Confirmado nesta continuação, com o mesmo detector já usado na primeira
tentativa: `W003`/`W061`/`W062` **nunca entram no laço de reparo** —
`_arm_role_isolated_edges` as exclui estruturalmente (nó T não é
`L_CORNER`-2-braços). Nenhuma tentativa de generalizar o mecanismo para
elas foi feita, conforme instrução explícita desta continuação.

## 2 paredes longas

Confirmado: `W010`/`W037` não aparecem em `_arm_role_isolated_edges`
(fazem parte de um componente maior do grafo de coordenação — não são
aresta isolada) — nunca entram no laço de reparo, nenhuma tentativa de
"consertar" por troca de papel. Registrado como pendência de
FILL-SEARCH/layout search, fora do escopo desta CR (seção 9 do relatório
original, acima).

## Invariância

Não totalmente exercitada por teste automatizado nesta continuação (ver
"Testes" abaixo) — mas a construção é, por desenho, invariante a ordem:
`_arm_role_isolated_edges` ordena por `wall_idx` crescente;
`CORNER_ROLE_CANDIDATE_BITS` é uma tupla fixa (nunca dict/set);
`_set_l_corner_role_bits` decide qual nó trocar por
`_canonical_node_sort_key` (identidade geométrica, nunca índice de
lista); `_no_new_collisions`/`_wall_has_forced_corner_prism` comparam por
assinatura geométrica, nunca por índice posicional.

## Testes

**Nenhum teste novo commitado** — a implementação foi revertida antes de
qualquer commit desta continuação (mesma decisão da tentativa anterior,
mesmo motivo: gap de segurança concreto, desta vez `JUNCTION_NOT_
ALTERNATING` em vez de colisão). Os testes T1-T13 pedidos não foram
escritos como testes permanentes — os equivalentes de T1 (detector), T2
(SAME elimina prisma quando seguro), T3 (colisão rejeita candidato), T4
(fallback ORIGINAL), T9 (nó T intocado), T10 (parede longa intocada),
T11-T13 (coverage/openings/collisions preservados) foram todos
VERIFICADOS AO VIVO contra TGD/TP1 durante o desenvolvimento (não
inventados/estimados), mas sem chegar a um estado seguro o bastante para
merecer virar teste permanente do comportamento ATIVO — registrar um
teste que prova um comportamento que não está no diff final seria
enganoso. `tests/test_block_arm_role_prism_stagger.py` foi editado
durante o desenvolvimento (test do W076 atualizado para a versão
reparada) e revertido junto com o resto.

## TGD / TP1 — métricas medidas com o reparo ATIVO (não commitadas)

| métrica | TGD (B→C, W137 reparado) | TP1 (B→C, W021+W092+W076 reparados) |
|---|---|---|
| PRISM_CONTINUOUS_JOINT | 476→397 (medido; W137: 16→0) | 576→528 (medido; as 3: 16→0 cada) |
| POSITION_OVERLAP | inalterado (não medido isolado, sem regressão observada) | **18→18, inalterado** (confirmado explicitamente) |
| OPENING_BLOCK_CROSSES_JAMB | inalterado | **168→168, inalterado** |
| COVERAGE_MISSING_ROW | 258→242 (melhora adicional, efeito colateral do reparo em W137 — não investigado a fundo) | inalterado |
| `junctions` (categoria, JUNCTION_MISSING_BINDING+JUNCTION_NOT_ALTERNATING) | **20→22 paredes com achado — 2 NOVAS (`W011`,`W088`), `JUNCTION_NOT_ALTERNATING`** | **1→1, inalterado** (o único achado é o artefato de paridade já conhecido) |

TP1 (3 candidatos aceitos) ficou **completamente limpo** em todas as
métricas medidas. TGD (1 candidato aceito, `W137`) introduziu a
regressão de `junctions` acima — motivo pelo qual a implementação
inteira foi revertida (não só o candidato de `W137`): sem entender o
mecanismo o bastante para garantir que o MESMO problema não pode
acontecer em algum candidato futuro do TP1 (ou de qualquer outro
projeto), aceitar mesmo os 3 candidatos "limpos" seria uma aposta, não
uma prova — contrário ao princípio desta continuação (seção 2 do
pedido: "GERAR CANDIDATO → VALIDAR COMPLETAMENTE → ACEITAR OU REJEITAR",
nunca "aceitar porque não vimos problema ainda").

## Production diff

**Vazio.** Implementação inteira revertida (`git checkout`) antes de
qualquer commit desta continuação — idêntico ao estado B já documentado
acima.

## Baselines

Não regravados nesta continuação (nenhuma mudança de produção).

## Gates G1–G18 (desta continuação)

| gate | descrição | status |
|---|---|---|
| G1 | detector preservado | ✅ (idêntico à primeira tentativa, reconfirmado) |
| G2 | reparo antigo inseguro continua ausente | ✅ |
| G3 | candidatos gerados deterministicamente | ✅ (`CORNER_ROLE_CANDIDATE_BITS`, ordem fixa) |
| G4 | hard constraints executados ANTES do score | ✅ |
| G5 | validação de colisão usa definição completa, não aproximação de 1 salto | ✅ (`result["collisions"]` global, reusado sem duplicar) |
| G6 | `NEW_POSITION_OVERLAP = 0` nas paredes alteradas | ✅ (medido: TP1 18→18, TGD sem regressão observada) |
| G7 | collisions globais não pioram materialmente | ✅ |
| G8 | coverage não piora | ✅ (melhora em ambos os projetos) |
| G9 | openings não pioram fisicamente | ✅ |
| G10 | prisma melhora no subconjunto elegível | ✅ (3/3 TP1 completos; 1/1 TGD tentado, mas revertido por G-junction) |
| G11 | paredes T não são alteradas sem prova | ✅ |
| G12 | paredes longas de fill não são alteradas por política errada | ✅ |
| G13 | fallback ORIGINAL funciona | ✅ (verificado nas 3 paredes T + 2 longas + todo candidato rejeitado) |
| G14 | invariância de ordem passa | ⚠️ não exercitada por teste automatizado (só por desenho — ver "Invariância") |
| G15 | baseline/reference intactos | ✅ |
| G16 | production diff restrito | ✅ (vazio — revertido) |
| G17 | testes focados passam | ✅ (281 testes inalterados, nenhum novo commitado) |
| G18 | suíte final passa | N/A — nenhum candidato de fix commitado |
| **G-novo** | nenhuma parede antes limpa de `JUNCTION_NOT_ALTERNATING` (nível 1) passa a acusar | ❌ — **FALHOU** (`W011`, `W088`/TGD) — motivo da reversão |

## Residual conhecido

- **3 de 6 paredes curtas elegíveis** (`W021`, `W092`, `W076`) têm um
  reparo PROVADAMENTE seguro contra fechamento, colisão global e prisma
  em vizinhas — mas indisponível até o gate de `JUNCTION_NOT_ALTERNATING`
  existir, porque não há como saber de antemão (sem esse gate) se um
  FUTURO candidato nesses mesmos projetos cairia no mesmo problema de
  `W137`.
- **`W137`/TGD especificamente**: reparo tecnicamente encontrado e
  validado contra os gates EXISTENTES, mas empurra `JUNCTION_NOT_
  ALTERNATING` para `W011`/`W088` — mecanismo não isolado.
- **`W061`/`W062`/`W003`** (nó T): nenhum mecanismo de coordenação as
  cobre, como já documentado.
- **`W010`/`W037`** (paredes longas): defeito na busca de preenchimento,
  não na coordenação de papel, como já documentado.

## Próximo passo

1. Construir, dentro de `wall_stepper.py`, um detector LOCAL e FIEL de
   `JUNCTION_NOT_ALTERNATING` — precisa replicar (a) o agrupamento de nós
   por proximidade física (`NODE_MERGE_TOLERANCE_CM`, não só o grafo de
   `node["arms"]`, que sempre assume exatamente 2 paredes por nó) e (b) a
   assinatura por fiada (`_row_signature` — conjunto (parede, código) de
   toda peça cujo CORPO alcança o ponto do nó, não só as duas candidatas
   de `solve_l_corner`). Até esse detector existir e ser usado como quinto
   hard gate, **NÃO reativar o reparo**, nem para o subconjunto
   TP1-limpo — o mecanismo de `W137` não foi descartado como impossível
   em outros projetos, só não investigado a fundo.
2. Alternativa mais simples, se aceitável: reutilizar
   `nuvem/benchmark/validators/validate_junctions.py` DIRETAMENTE como
   quinto gate (exige que `wall_stepper.py`, ou o chamador do reparo,
   monte a estrutura `{"walls": [...]}` que aquele validador espera a
   partir de `trial_run["candidates"]`, similar ao que
   `nuvem/benchmark/extract/from_solver.py` já faz) — **decisão de
   escopo explícita necessária** (o módulo de produção autorizado para
   este CR é só `wall_stepper.py`; usar o validador do benchmark como
   dependência de PRODUÇÃO, mesmo que só para checagem interna antes de
   aceitar um candidato, é uma extensão de escopo real, não uma
   aproximação — mas precisa de autorização explícita antes de
   implementar, conforme a seção 17 do pedido desta continuação).

## Veredito (desta continuação)

**NECESSITA AJUSTE**

Progresso real e verificado: a infraestrutura de colisão completa foi
localizada, confirmada como já-reutilizável sem duplicação
(`result["collisions"]`), e o gap de segurança da tentativa anterior foi
corrigido e provado corrigido (TP1: `POSITION_OVERLAP` 18→18, `junctions`
1→1, três paredes com prisma forçado eliminado com segurança completa
medida). Um SEGUNDO gap de segurança, de categoria diferente
(`JUNCTION_NOT_ALTERNATING`, nível 1, mecanismo de agrupamento de nó por
proximidade que não existe em `wall_stepper.py` hoje) foi descoberto
durante a validação empírica contra TGD — não é aproximação nem
suposição, é um achado medido (`W011`/`W088` limpas antes, sujas
depois). A implementação foi **revertida por completo** (não só o
candidato problemático de `W137`) porque não há, dentro desta
continuação, prova de que o mesmo mecanismo não afetaria um candidato
futuro em QUALQUER dos projetos, incluindo os que hoje parecem limpos.

Não é `BLOQUEADO POR ESCOPO` no sentido estrito do pedido (nenhuma
tentativa de implementação foi impedida por falta de acesso a um módulo —
a checagem de colisão, que É a infraestrutura que a seção 6 do pedido
pergunta sobre, está inteiramente dentro de `wall_stepper.py` e FOI
reutilizada com sucesso) — mas o **quinto gate necessário
(`JUNCTION_NOT_ALTERNATING`) não tem hoje uma fonte de verdade dentro do
escopo autorizado que possa ser reutilizada sem duplicação**, e
implementar uma versão local arriscaria exatamente a "aproximação" que a
seção 6 do pedido proíbe explicitamente. O "Próximo passo" item 2 pede
autorização explícita de escopo para essa situação específica.

Nenhum merge realizado. Nenhuma alteração de produção no estado final
entregue (idêntico ao estado B, documentado na primeira parte deste
relatório). PR #11 continua draft, sem push desta continuação.

**Pare antes de qualquer merge.**

## CONTINUAÇÃO — `CR-BLOCK-ARM-ROLE-JUNCTION-GATE` (2026-09-04, segunda continuação)

Investigação da causa REAL do `JUNCTION_NOT_ALTERNATING` acima, ANTES de
qualquer nova implementação de produção. Toda esta seção foi produzida
com scripts temporários em `/tmp` (nunca em `nuvem/`); diff de produção
manteve-se em ZERO durante toda a investigação (`git status`/`git diff
--stat` vazios, `HEAD` inalterado em `fe36e87`).

### Correção de um erro da continuação anterior

A atribuição "reparar `W137` introduz `JUNCTION_NOT_ALTERNATING` em
`W011`/`W088`" (parágrafo acima e seção 30 de
`REGRAS_MODULACAO_BLOCOS.md`) está **provadamente ERRADA**. Reproduzida
com mapeamento id↔`wall_idx` correto (por GEOMETRIA — `wall_idx` de
`from_solver.py` NÃO é `id` menos 1; casar `walls_to_create[i]` com
`result.json` por distância de ponta ≤1cm) e diff de assinatura exato
(`finding_signature`, ignora índice de lista): reparar **só** `W137`
(`wall_idx=120`) isolado produz **0 achados novos e 0 resolvidos** em
`JUNCTION_NOT_ALTERNATING`/`JUNCTION_MISSING_BINDING` — nenhuma
regressão em `W011`/`W088`. O erro veio de um `git stash`/`stash pop`
que colidiu com `score.json`/`reports/*.txt` regenerados durante a
sessão anterior, corrompendo a comparação real.

Os candidatos que REALMENTE causam `JUNCTION_NOT_ALTERNATING` novo,
isolados um a um contra o mesmo baseline (5 candidatos elegíveis do TGD:
`wall_idx` 7, 23, 89, 90, 120):

| `wall_idx` reparado | id | `JUNCTION_NOT_ALTERNATING` novo |
|---|---|---|
| 7 | `W090` | 1 novo em **`W088`** (a própria vizinha do reparo) |
| 23 | `W011` | 1 novo em **`W011`** (a PRÓPRIA parede reparada) |
| 89 | — | 0 |
| 90 | — | 0 |
| 120 | `W137` | **0** (confirma a correção acima) |

Ou seja: cada regressão aparece exatamente na parede que foi reparada ou
na parede geometricamente colada a ela — não existe cluster de 3+
paredes causando o efeito. `W137` nunca teve nenhum papel nisso.

### Primeira divergência — mecanismo real (banda, não nó/agrupamento)

`solve_building_blocks_all_courses` (`nuvem/core/wall_modeling.py:3053`)
resolve o edifício em **bandas** de fiadas fisicas com o mesmo conjunto
de aberturas ativas (`_group_course_indices_by_opening_band`) — TGD tem
8 bandas mesmo para uma parede sem abertura própria (`W090`:
`openings: []`), porque o agrupamento é do PROJETO inteiro (aberturas de
QUALQUER parede cortam as bandas de TODAS as fiadas físicas
compartilhadas). `nodes` é passado por REFERÊNCIA (mesmo objeto) a cada
chamada de `solve_building_blocks` — sem cópia por banda — então
mutações deveriam persistir.

Instrumentando `_coordinate_arm_role_nodes` (chamada dentro de CADA
banda, antes do reparo rodar) e `_wall_has_forced_corner_prism`
banda-a-banda para o par de nós isolado de `wall_idx=7`
(`node_p=13`/`node_q=14`):

- **Sem reparo ativo (baseline)**: `_coordinate_arm_role_nodes` converge
  para o MESMO estado alternante estável em todas as 8 bandas (banda 1
  o define, bandas 2-8 só o confirmam sem mudar nada) — o mecanismo de
  alternância em si é **idempotente e correto** entre bandas.
- **Com o candidato `SAME_A` de `wall_idx=7` sendo aceito banda a
  banda** (arquitetura da tentativa anterior — o reparo roda dentro do
  `solve_building_blocks` corrigido por banda, sem persistência
  explícita): bandas 1-5 têm `forced_corner_prism=True` e o reparo
  reaplica `SAME_A` (`changed_indices=[13]`) em CADA UMA das 5 — sucesso
  aparente repetido. Bandas 6-8 têm `forced_corner_prism=False` — o
  reparo NUNCA roda nelas.
- Medindo qual FAMÍLIA (curso `A`/`B`) toca o nó 13 por banda, via
  `node_index` dos candidatos de canto de `wall_idx=7`:
  - Bandas 1-5 (reparadas): `course_A_node_idx=[13,...]`,
    `course_B_node_idx=[]` — família A sempre toca.
  - Bandas 6-8 (NÃO reparadas, estado natural/`_coordinate_arm_role_
    nodes` puro): `course_A_node_idx=[...]` (sem 13),
    `course_B_node_idx=[13]` — família **B** sempre toca.

**Causa raiz provada**: como `course_index % 2` → letra `A`/`B` é FIXO
globalmente (não depende de banda), e o papel do nó isolado É persistido
fisicamente em `nodes` entre bandas, mas o *reparo* só é ACIONADO quando
a banda ATUAL, isoladamente, mostra `forced_corner_prism=True` — bandas
onde essa condição local não se repete (6-8) usam o estado alternante
PADRÃO (`_coordinate_arm_role_nodes`, sem override), que por construção
é a família OPOSTA à que o reparo escolheu nas bandas 1-5. O resultado
físico: fiadas 0-10 (bandas 1-5) têm "família A sempre toca t=0", fiadas
11-16 (bandas 6-8) têm "família B sempre toca t=0" — a MESMA parede,
DUAS convenções opostas, cada uma internamente consistente mas
incompatíveis entre si. Isso produz (a) `PRISM_CONTINUOUS_JOINT` novo na
fronteira 10/11 da própria `W090` e (b) `JUNCTION_NOT_ALTERNATING` na
parede vizinha que compartilha o nó (`W088`), porque a fiada 11 (family
B) "repete" o código da fiada 10 (que também era `B34` na convenção
antiga) na leitura por proximidade do validador.

Isso **refuta** a hipótese anterior (agrupamento de nó por proximidade
física / `NODE_MERGE_TOLERANCE_CM` fundindo 3+ paredes) como causa —
confirmado adicionalmente por inspeção direta do cluster
`W090`↔`W167` (`NODE_MERGE_TOLERANCE_CM`, ponto `[339.764, 187.049]`):
esse cluster de fato mostra `JUNCTION_NOT_ALTERNATING` em TODAS as 17
fiadas, mas **idêntico no baseline e no reparado** — é um defeito
PRÉ-EXISTENTE e não relacionado (`W167` deveria a alternar com `W090`
mas nunca alternou, com ou sem qualquer reparo desta CR).

### `validate_junctions.py` como oráculo — é regra de domínio real?

Lido por completo (não importado em produção). `collect_nodes` agrupa
por proximidade (tolerância 3cm X/Y independente); `validate_node`
calcula `_row_signature` = conjunto `(parede, código)` de toda peça cujo
CORPO cobre o ponto do nó, fiada a fiada, e reporta
`JUNCTION_NOT_ALTERNATING` (nível 1/obrigatório) quando duas fiadas
CONSECUTIVAS têm assinatura idêntica.

Isso corresponde diretamente à regra já documentada na seção 29 deste
arquivo e ao mecanismo de produção `_coordinate_arm_role_nodes`
(docstring: "garante que os dois nós L_CORNER... NUNCA deem
`course_a`/`course_b` a essa parede da MESMA forma") — não é um
artefato só-de-benchmark: é a MESMA regra de amarração ("continuidade e
repetição entre fiadas", item explícito de TODO de amarração no
`CLAUDE.md`) verificada de um ângulo diferente (por geometria do ponto,
não pelo grafo `node["arms"]`). **H5 REFUTADA** (não é artefato de
benchmark). Nenhum falso positivo conhecido foi encontrado nos casos
investigados aqui — os dois achados novos (`W088`, `W011`) e o
pré-existente (`W090`↔`W167`) são todos regressões/defeitos reais, não
ruído do validador.

### Hipóteses H1-H5 — veredito

| Hipótese | Veredito |
|---|---|
| H1 — grafo `node["arms"]` incompleto | **REFUTADA** — o grafo de 2 paredes por nó está correto; o problema nunca foi topológico |
| H2 — validação precisa olhar além do grafo (agrupamento por proximidade) | **REFUTADA como causa** do bug medido (é um fato real sobre o validador, mas não explica nenhuma das regressões encontradas — todas são pares de 2 paredes, nunca clusters de 3+) |
| H3 — `NODE_MERGE_TOLERANCE_CM` funde nós fisicamente distintos incorretamente | **REFUTADA** para os casos medidos (`W088`/`W090`, `W011`/`W074`/`W076` são de fato o MESMO ponto físico; o cluster de 3 do `W090`↔`W167` é pré-existente, não causado pelo reparo) |
| H4 — uma terceira parede é genuinamente necessária pra regra real | **REFUTADA** como explicação do bug (mecanismo é 100% par-a-par); a REGRA em si (`validate_junctions.py`) trata cada cluster com quantas paredes ele de fato tiver, mas nenhum caso medido precisou de 3 |
| H5 — `JUNCTION_NOT_ALTERNATING` é artefato de benchmark | **REFUTADA** — corresponde à regra de amarração já documentada (seção 29) |
| **H-nova** (não estava na lista original) — inconsistência de persistência do papel do nó ENTRE BANDAS de `solve_building_blocks_all_courses` | **PROVADA** — é a causa raiz real, medida e reproduzida (ver acima) |

### Arquitetura do quinto gate — decisão

Opção escolhida: **B — regra corrigível dentro de `wall_stepper.py`**,
mas não como um "quinto gate" de checagem pós-hoc — como correção
ESTRUTURAL do mecanismo em si. `_coordinate_arm_role_nodes`
(`wall_stepper.py:1340`) hoje reconstrói o estado alternante do zero em
CADA banda a partir de `node.get("kind")=="L_CORNER" and
len(arms)==2` — nenhum estado de decisão manual sobrevive entre bandas.
Correção mínima testada e comprovada em script (não commitada):
adicionar um marcador `_arm_role_pinned` nos dois nós de uma aresta
isolada quando um candidato SAME/ALTERNATE não-padrão é aceito, e
excluir nós marcados da lista `eligible` de `_coordinate_arm_role_nodes`
(equivalente a `and not node.get("_arm_role_pinned")` no filtro). Como o
reparo só atua em ARESTAS ISOLADAS (por construção — grau 1 nos dois
nós, nenhuma outra parede coordenada os toca), excluí-las do grafo de
`_coordinate_arm_role_nodes` nunca afeta a alternância de nenhuma OUTRA
parede — mudança local, sem efeito colateral em nenhum outro nó.

**Testado empiricamente** (mesmo script de diagnóstico, 8 bandas do
TGD, `wall_idx=7`): com o marcador de pin, `course_A_node_idx` inclui o
nó 13 em TODAS as 8 bandas (antes: só nas bandas 1-5) — a inconsistência
desaparece por construção, não por filtro pós-hoc.

Rodando o SAFE REPAIR completo (5 candidatos elegíveis do TGD) com o
pin ativo e comparando TODOS os achados (`bench_validators.run_all`,
não só junções) contra o mesmo baseline:

| código | antes (sem pin) | com pin |
|---|---|---|
| `JUNCTION_NOT_ALTERNATING` novo | **+2** (`W011`, `W088`) | **0** |
| `PRISM_CONTINUOUS_JOINT` novo (própria parede) | +1 (`W090`) | **0** |
| `PRISM_CONTINUOUS_JOINT` resolvido | 79 | **80** |

O quinto gate (`NEW_JUNCTION_NOT_ALTERNATING = 0`) fica **estruturalmente
garantido** pelo pin, não precisa de uma checagem separada que replique
`validate_junctions.py` — não há duplicação de regra (opção C/D
descartadas: nenhum módulo novo, nenhuma dependência de benchmark em
produção).

### Achado NÃO PEDIDO por esta CR, mas descoberto durante a verificação completa

Isolando os 5 candidatos individualmente COM o pin ativo e comparando o
conjunto COMPLETO de achados (não só junção/prisma/colisão), 4 dos 5
mostram regressão em categorias que os gates hoje existentes (fechamento
via `_wall_ok_map`/`_no_wall_regression`, colisão via
`result["collisions"]`, prisma forçado em vizinha) **não capturam**,
porque `validation.ok` de produção não modela essas categorias:

| `wall_idx` | achados NOVOS (parede afetada) |
|---|---|
| 7 (`W090`) | `COMPENSATOR_CONSECUTIVE` ×11, `COMPENSATOR_EXCESS_IN_RUN` ×11, `PRISM_STAGGER_BELOW_TARGET` ×21 — todos na própria `W090` |
| 23 (`W011`) | nenhum — **único candidato limpo em TODAS as categorias** |
| 89 | `COVERAGE_GAP_IN_ROW` ×17, `COVERAGE_PARTIAL_WALL` ×1 — na parede vizinha `W155` |
| 90 | `COVERAGE_GAP_IN_ROW` ×17, `COVERAGE_PARTIAL_WALL` ×1 — na parede vizinha `W153` |
| 120 (`W137`) | `COMPENSATOR_CONSECUTIVE` ×6, `COMPENSATOR_EXCESS_IN_RUN` ×3, `COVERAGE_ROW_MOSTLY_EMPTY` ×6 — na parede vizinha `W131` |

Isso NÃO estava na lista dos 5 gates pedidos por esta CR (que tratava
especificamente de `JUNCTION_NOT_ALTERNATING`), e catalogar/rejeitar por
essas categorias exigiria um SEXTO gate com fonte de verdade de produção
para `COMPENSATOR_CONSECUTIVE`/`COVERAGE_GAP_IN_ROW`/etc. — essas
categorias só existem hoje em validadores do BENCHMARK
(`nuvem/benchmark/validators/`), não em nenhuma função de produção
equivalente a `_wall_ok_map`. Implementar essa fonte de verdade em
produção é uma extensão de escopo REAL (novo código de auditoria, não
uma checagem trivial), fora do que esta CR autorizou. Reportado aqui em
vez de ser ignorado ou "resolvido" com uma aproximação.

### Escopo necessário

Nenhum. O pin-fix fica inteiramente dentro de `wall_stepper.py`
(`_coordinate_arm_role_nodes`), sem tocar `wall_pairing.py` nem
`wall_modeling.py`. O achado adicional (compensador/cobertura em
vizinhas) FICA fora do escopo desta CR — não bloqueia por falta de
acesso a um módulo, mas por precisar de uma nova PEÇA de infraestrutura
de produção que não existe hoje (auditoria fina equivalente aos
validadores de benchmark) — registrado como próximo passo, não como
`BLOQUEADO POR ESCOPO` no sentido estrito.

### Comparação humano × solver (`W011`/`W088`/`W090`)

Nenhuma das três paredes está no Corpus de Referência humano (tabela da
seção 5 deste documento, 8 paredes: `W042`, `W061`, `W062`, `W021`,
`W092`, `W076`, `W010`, `W037`). Não há gabarito humano direto para
julgar qual família deveria tocar o nó `13`/`W088`↔`W090` — a validação
aqui é 100% baseada em `validate_junctions.py` (regra de alternância já
documentada na seção 29, não uma preferência estética observada em
projeto humano).

### Estado final e veredito

**NECESSITA AJUSTE** (mesmo veredito da continuação anterior, motivo
diferente).

O que MUDOU: a causa raiz do `JUNCTION_NOT_ALTERNATING` foi provada (não
mais "mecanismo não isolado") — é uma inconsistência de persistência
de papel de nó entre bandas de `solve_building_blocks_all_courses`,
corrigível com um marcador de pin dentro de `_coordinate_arm_role_nodes`
(`wall_stepper.py`, sem tocar `wall_pairing.py`/`wall_modeling.py`). O
quinto gate pedido por esta CR (`NEW_JUNCTION_NOT_ALTERNATING = 0`) é
estruturalmente alcançável e foi comprovado em script (0 regressões nos
5 candidatos do TGD, incluindo a correção do erro anterior sobre
`W137`).

O que ainda falta antes de `APROVADO PARA INTEGRAÇÃO`: dos 5 candidatos
elegíveis do TGD, só **1** (`wall_idx=23`/`W011`) passa limpo em TODAS as
categorias de achado quando verificado com o conjunto completo de
validadores (não só os 5 gates desta CR) — os outros 4 introduzem
regressões reais de compensador/cobertura em paredes vizinhas que os
gates hoje autorizados não detectam nem rejeitam. Ativar o pin-fix +
SAFE REPAIR em produção hoje aceitaria esses 4 candidatos sem um gate
que os rejeite — não é seguro no espírito de "gerar candidato → validar
completamente → aceitar ou rejeitar" desta CR.

**Nenhuma alteração de produção foi commitada nesta continuação** (diff
de `wall_stepper.py` permanece ZERO — verificado via `git status`/`git
diff --stat` antes desta escrita). O pin-fix foi provado em script de
diagnóstico, não escrito no arquivo de produção, porque sozinho (sem o
sexto gate que rejeitaria os 4 candidatos problemáticos) ativaria uma
regressão real assim que qualquer chamador acionasse o reparo.

### Próximo passo recomendado

1. Implementar o marcador de pin em `_coordinate_arm_role_nodes`
   (mudança pequena, comprovada, sem efeito colateral em nós não
   isolados) — seguro de commitar independentemente, mesmo sem o SAFE
   REPAIR ativo, porque é um no-op enquanto nenhum chamador define
   `_arm_role_pinned`.
2. Antes de reativar o SAFE REPAIR (aceitar candidatos automaticamente):
   decidir com o usuário se o sexto gate (compensador/cobertura em
   vizinhas) precisa de uma nova função de auditoria de produção, ou se
   a política deve restringir aceitação a candidatos que não tocam
   nenhuma parede vizinha por enquanto (mais simples, mais conservador,
   cobre só `W011`-like).
3. Só depois disso, reintroduzir `CORNER_ROLE_CANDIDATE_BITS`/
   `_arm_role_isolated_edges`/`_evaluate_corner_role_candidate` em
   `wall_stepper.py` com os 5 gates desta CR MAIS o sexto gate decidido.

**Pare antes de qualquer merge.**
