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

## Veredito

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

**Pare antes de qualquer merge.**
