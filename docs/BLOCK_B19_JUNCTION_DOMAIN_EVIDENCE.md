# RELATÓRIO FINAL — B19 JUNCTION DOMAIN EVIDENCE

`CR-BLOCK-B19-JUNCTION-DOMAIN-EVIDENCE` — investigação SOMENTE. Nenhuma
alteração de `wall_stepper.py`, `wall_modeling.py`, `continuous_modulation.py`,
`modulation_math.py`, `wall_pairing.py`, `geometry.py`, `baseline.json`,
`reference.json` ou `REGRAS_MODULACAO_BLOCOS.md`. NODE-FILL e Gate Fidelity
não implementados.

## Base

```
origin/main esperado   5f4f98e8a87352ad811666eb441d99bc7ad3cf92 (confirmado)
branch desta CR        claude/b19-junction-domain-investigation-1h4ow8
```

`git diff 4c89e1216cc6b5708c590f495e1584497e2df583 5f4f98e -- nuvem/core/engine/wall_stepper.py nuvem/core/wall_modeling.py`
— **vazio**. O código de produção relevante (gates SAFE REPAIR,
`solve_l_corner`, `solve_t_intersection`, regra do meio-bloco) é o
MESMO que já foi instrumentado e medido ao vivo em
`docs/BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md` — nenhuma remedição contra
o corpus foi necessária para os 10 casos já instrumentados lá; esta CR
reusa aquela medição (mesma árvore de produção) e adiciona: (a) leitura
direta do Reference Corpus (`reference.json`) para ampliar a busca além
dos 10 casos já conhecidos, (b) leitura cruzada com dois outros
relatórios de investigação (`BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_SPEC.md`,
`BLOCK_ARM_ROLE_HUMAN_POLICY.md`) que confirmam o mesmo padrão por vias
independentes, (c) a matriz e a recomendação de escopo que nenhum dos
três documentos anteriores reuniu num só lugar sob a pergunta "B19 pode
participar de amarração em parede curta?".

## Onboarding lido

`docs/START_HERE.md`, `docs/PROJECT_STATUS.md`,
`docs/BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md`,
`docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_SPEC.md`,
`nuvem/REGRAS_MODULACAO_BLOCOS.md` (seções 2/11.6 — regra do meio-bloco;
24.3 — conflito já registrado; 30/31 — `CR-BLOCK-ARM-ROLE-HUMAN-POLICY`;
seção sobre `W039`↔`W041`). Adicional, encontrado durante a busca em
camadas (não estava na lista de onboarding do pedido, mas é a
continuação mais recente da mesma linha de investigação):
`docs/BLOCK_ARM_ROLE_HUMAN_POLICY.md` — leitura completa, por conter uma
segunda medição independente das MESMAS paredes (`W021`/`W092`/`W076`)
com foco em prisma, não em B19, mas cruzando exatamente o mesmo corpus.

## Regra atual

`nuvem/REGRAS_MODULACAO_BLOCOS.md`, "Regra do meio-bloco (B19)" (dentro
da seção 2) + seção 11.6 (rede de segurança):

- B19 nunca no meio de um trecho (incondicional).
- Só encosta em **ponta aberta de verdade** (vão de abertura ou
  extremidade de parede **sem amarração**). Uma boneca/pilar de
  encontro (L/T/X) **não conta como ponta aberta**, mesmo degradada.
- Prioridade rebaixada em 2026-08-25: com as duas pontas fechadas contra
  nó, o solver tenta compensador(es) ANTES de B19 sem ponta aberta;
  B19 sem ponta aberta é "últimíssimo recurso".
- `_corner_single_element_candidate`: **nunca gera B19** como peça única
  de canto degradado (`CORNER_SINGLE_ELEMENT_CODES` sem B19).
- Rede de segurança (`audit_wall_bond_quality`/`HALF_BLOCK_NEAR_TIE`):
  bloqueia a criação da parede se qualquer B19 lançado estiver perto
  (`HALF_BLOCK_TIE_ADJACENCY_CM ≈ 2cm`) de um nó L/T/X, ponta ou meio de
  parede.

Ou seja: a regra atual, lida ao pé da letra, é a **INTERPRETAÇÃO A**
(estrita) — B19 nunca participa de nó de amarração, em nenhuma
circunstância, incondicionalmente.

**Conflito já registrado antes desta CR** (seção 24.3,
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, 2026-08-31): `JUNCTION_HALF_BLOCK_ADJACENT`
aparece 259 vezes no projeto humano aprovado (TP1) e 0 vezes no solver —
"a regra #2 é mais restrita do que a prática real do escritório, ou a
reconstrução de encontros está marcando como 'encontro' pontos que não
são" — marcado como pendência de investigação, não resolvido. Esta CR é
essa investigação.

## Corpus analisado

### Fonte 1 — `BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md` (medição ao vivo,
instrumentada, contra o corpus real — reusada, não remedida)

10 arestas isoladas rejeitadas pelo SAFE REPAIR (TGD 89/90/91/92/120/4/54,
TP1 20/91/75), casadas por geometria (`match_walls`) com o Reference
Corpus. Fonte primária desta CR.

### Fonte 2 — leitura direta de `reference.json` (TGD e TP1), nesta sessão

Script: varrer as 97 (TGD) + 96 (TP1) paredes do gabarito humano por
`length_cm` em `[40, 80]` **com pelo menos uma junção L/T/X**, agrupando
peças por fiada par/ímpar. Resultado (13 paredes em cada projeto,
26 no total, além das já citadas na Fonte 1):

```
TGD 54cm (T+L ou L+T nas duas pontas): W013 W014 W018 W019 W089 W090 W091 W092
  -> par: B19[0-19]/B34[20-54] ou B19[35-54]/B34[0-34] (varia com a orientação)
     ímpar: B39[0-39] inteiro
  -> 6 peças B19 por parede, sempre encostada no nó

TGD 69cm (L+L): W077
  -> par: B34[0-34] B34[35-69]  (as DUAS âncoras na MESMA família)
     ímpar: B39[15-54]  (peça solta, não toca nenhuma ponta)
  -> ZERO B19

TGD 79cm (T+L ou L+T): W048 W049 W062 W063
  -> usa B34+B39+C09 (compensador), só B19_C (peça CORTADA, não bloco
     inteiro) aparece — NÃO é o mesmo padrão de fill B19 dos casos de
     54/124cm

TP1: mesmo padrão, com W013 W014 W015 W016 W088 W089 W090 W091 (54cm),
     W076 (69cm), W048 W049 W061 W062 (79cm)
```

Script fonte: `scan_short_walls.py` (scratchpad da sessão, não
versionado — reproduzível por qualquer sessão futura lendo
`reference.json` diretamente, sem dependência de estado externo).

### Fonte 3 — `BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_SPEC.md` e
`BLOCK_ARM_ROLE_HUMAN_POLICY.md` (confirmação independente)

Ambos os documentos, produzidos em sessões diferentes desta, chegam à
MESMA composição humana para `W021`/`W092` (124cm) e `W077`/`W076`
(69cm) por vias de leitura/instrumentação independentes uma da outra e
desta sessão — três fontes convergentes sem terem sido cruzadas antes
num único documento.

## Casos positivos (B19 encostado em nó, no gabarito humano)

| caso | comprimento | junção | fiada com B19 | posição | B19 toca o nó? | é peça de amarração? |
|---|---|---|---|---|---|---|
| TGD 89/90 (W157/W158 alvo) | 124cm | L—X—L | ímpar | `[15-34]` e `[70-89]`, encostado no `B54 X` central | sim, direto | NÃO — o `B54 X`/`B34 L` fecham o nó; B19 só preenche o resto de 19cm até a peça de nó |
| TGD 91/92 (W012/W013 alvo) | 124cm | L—X—L | idêntico ao acima | idêntico | sim | NÃO |
| TP1 20/91 (W021/W092 alvo) | 123,98cm | L—X—L | ímpar (`B34+B19+B19+B34`) | encostado nos dois `B34` de canto | sim | NÃO |
| TGD 89/90/91/92 vizinhas (131-134, 128/129, ref. `W013/014/018/019/089-092`) | 54cm | T+L (ambas pontas fechadas) | par | `[0-19]`/`[35-54]` | sim, direto | NÃO — `B34[20-54]` fecha o L; B19 preenche o resto até o T |
| TP1 20/91 vizinhas (`W013-016/088-091`) | 54cm | T+L | idêntico | idêntico | sim | NÃO |
| `W039`↔`W041` (nó L, TP1) | — | L | maioria das fiadas | repetido, sem alternância | sim, mas **NUNCA cobre o nó** (medido por `block_covers_point`) | NÃO — nem o humano fecha esse nó em todas as fiadas (`JUNCTION_MISSING_BINDING` real em 2 fiadas mesmo no gabarito aprovado) |

**Padrão consistente nos 3 grupos**: em NENHUM caso positivo o B19 é a
peça que fisicamente amarra o nó (fecha o vértice/vão menor entre as
duas paredes). A peça de amarração é sempre `B34`/`B54` (ou, no caso
`W039`/`W041`, nenhuma peça alcança o ponto físico do nó — nem do
humano). O B19 preenche o TRECHO RESIDUAL entre essa peça de nó e a
próxima peça/nó, um trecho de 15-20cm que nenhuma outra peça do
catálogo fecha sem compensador.

## Casos negativos (B19 ausente / não usado, mesmo perto de nó)

| caso | comprimento | junção | composição humana | por que sem B19 |
|---|---|---|---|---|
| TGD 120 / TP1 75 (`W077`/`W076`) | 69cm | L—L | par: `B34+B34` (as duas âncoras); ímpar: `B39` solto, sem tocar nenhuma ponta | as duas âncoras B34 cabem **exatas** nos 34+35=69cm da família par; a família ímpar tem um vão de 39cm livre — exatamente um B39, sem resto — não sobra trecho de 15-20cm para B19 |
| TGD/TP1 79cm (`W048/049/061-063`) | 79cm | T—L ou L—T | `B34+C09+B34` (ímpar) / `C09+B39` (par) | o resto depois das duas âncoras B34 é 79−68=11cm — não é 19-20cm, então o humano fecha com compensador (`C09`), não com B19 |
| `W010`/`W037` (424/524cm, longas) | >400cm | L—L | mantém as âncoras em pontas opostas; preenchimento comum no meio nunca gera trecho de 15-20cm | sem trecho residual pequeno, B19 nunca é candidato — nem no humano nem seria esperado no solver |

**Conclusão da comparação positivo × negativo**: o uso de B19 no
gabarito humano não é "qualquer parede curta perto de nó" — é
especificamente **o trecho residual entre uma peça de nó (B34/B54/B34
X) e o próximo limite (outro nó ou fim do vão)**, quando esse resto mede
15-20cm. Quando o resto é outro valor (11cm, 39cm exato, 0cm), o humano
usa a peça correspondente (compensador, B39 inteiro, nada) — nunca B19
fora dessa faixa.

## Solver × Humano — primeira divergência

Dois mecanismos DIFERENTES estão misturados na formulação original do
pedido ("solver produz C09+C09+C09 onde humano usa B19+B34/B39") —
separá-los é o achado central desta CR:

### Mecanismo 1 — paredes ALVO de 124cm (TGD 89/90/91/92, TP1 20/91)

O candidato de papel `SAME_B` (`_coordinate_arm_role_nodes`, contrato
SAFE REPAIR) **já é gerado** e **já produz** a composição humana
(`B39`+`B39` numa família, `B34...B19...B19...B34` na outra) — não é uma
questão de regra de B19. É **rejeitado por um proxy do Gate Fidelity**
(cobertura local por `wall_idx` dono, cega à peça de canto emprestada
pela vizinha — Grupo A2 do diagnóstico original) ou por um artefato de
agregação cross-banda do gate de compensador (Grupo A1, `TP1 75`).

- Classificação: **DOMAIN_RULE_BLOCKED = NÃO** para o alvo em si.
  Classificação correta: candidato **SEARCH_PRUNED por gate incorreto**
  (não é regra de domínio nem limitação geométrica — é bug de medição do
  contrato SAFE REPAIR, já com CR definido:
  `CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY`).
- **RELATED_TO_GATE_FIDELITY**: sim, diretamente — a spec já lista TGD
  89/90 e TP1 20/91/75 como beneficiários esperados do fix de gate.
- **RELATED_TO_NODE_FILL**: TGD 89/90/91/92 e TP1 75 = INDEPENDENT
  (herdado do diagnóstico original); TP1 20/91 = RELATED (existe fill
  alternativo `B19+C09` que a lista `avoid` do NODE-FILL poderia
  escolher, possivelmente sem precisar mudar o papel).
- **B19 rule**: não é o gargalo. A regra de B19 já permite exatamente
  esta composição (B19 encostado numa peça de nó, nunca sendo ele mesmo
  a peça de amarração) — o candidato humano JÁ NASCE assim no solver.

### Mecanismo 2 — paredes VIZINHAS curtas (54-69cm: TGD 128/129/131-134,
TP1 12/13/87/88, e as 8+8 adicionais encontradas na Fonte 2)

Aqui sim está o `C09`/`C09×3`/`C09×4` citado no pedido, e aqui sim a
regra de B19 é o gargalo direto:

- `_corner_wall_room_ft`/`_wall_reserved_range_ft` reservam
  **pior-caso 34cm** na outra ponta da parede vizinha antes de decidir o
  canto — medido: 21,0/20,0/34,1/35,0cm de "room" real disponível nos 4
  casos instrumentados, sempre abaixo do necessário para `B34` inteiro
  → degrada para `C09` (`_corner_single_element_candidate`, que
  **nunca** oferece `B19`, por regra explícita do catálogo).
- Com o canto e o T degradados para `C09`, o trecho residual de
  15-20cm — que o humano fecha com 1 único `B19` — só pode ser fechado
  pelo solver com `C09` (compensador), e o teto de 1
  compensador/trecho força `C09×3`/`C09×4` como fill de último recurso
  quando o trecho maior (38,1cm, não-modular por aritmética) também
  falha.
- Classificação: **DOMAIN_RULE_BLOCKED** — é literalmente a regra
  "`_corner_single_element_candidate` nunca B19" + a reserva pior-caso
  que juntas impedem a composição humana de nascer. Não é
  `SEARCH_PRUNED` (a busca nem chega a considerar B19 aqui — a função
  geradora do catálogo de canto degradado simplesmente não o inclui) nem
  `GEOMETRY_LIMITATION` (o espaço físico existe — 54cm cabe
  `B19+B34`/`B39` perfeitamente; a reserva é uma escolha conservadora de
  código, não uma restrição física).
- **RELATED_TO_NODE_FILL**: INDEPENDENT (mecanismo de reserva/room, não
  de junta de fronteira entre fiadas — herdado do diagnóstico original,
  Grupo B).
- **RELATED_TO_GATE_FIDELITY**: INDEPENDENT — o Gate Fidelity corrige o
  contrato SAFE REPAIR (candidatos de papel `course_a`/`course_b`),
  nunca `solve_l_corner`/`solve_t_intersection`/`_corner_single_element_candidate`,
  que é onde o Mecanismo 2 vive. Corrigir o Gate Fidelity **não**
  destrava nenhuma das paredes vizinhas de 54-69cm.

## Matriz objetiva

| caso | geometria | humano | solver (baseline atual) | usa B19 | regra atual | causa da divergência | NODE-FILL | Gate Fidelity | evidência |
|---|---|---|---|---|---|---|---|---|---|
| TGD 89 (alvo, W157) | 124cm L–X–L | `B39+B39` / `B34+B19+B19+B34` | `C09+C09+C09` (candidato correto rejeitado) | sim (fill) | permite | proxy de cobertura local (Grupo A2) | INDEPENDENT | RELATED | diagnóstico instrumentado |
| TGD 90 (alvo, W158) | idem, espelho | idem | idem | sim | permite | idem | INDEPENDENT | RELATED | idem |
| TGD 91 (alvo, W013) | 124cm L–X–L | idem | `C09+C09+C09` (rejeitado por `closure_regression` na vizinha) | sim | permite | Grupo A2 + B combinados (vizinha 128 degrada) | INDEPENDENT | RELATED (alvo) / INDEPENDENT (vizinha) | idem |
| TGD 92 (alvo, W012) | idem | idem | idem, rejeitado por prisma forçado em vizinha 129 | sim | permite | Grupo A (proxy) + prisma vizinha | INDEPENDENT | RELATED | idem |
| TGD 120 (W137) | 69cm L–L | `B34+B34` / `B39` solto — **zero B19** | `C09` em cascata (candidato `SAME_A` correto rejeitado) | **não** | n/a | Grupo A2 (paridade) + Grupo D (jamb vizinha 88) | INDEPENDENT | RELATED | idem + `BLOCK_ARM_ROLE_HUMAN_POLICY.md` |
| TP1 75 (W076) | 69cm L–L | idêntico ao TGD 120 | idem, `SAME_A` rejeitado por fantasma do gate (PROVADO: 0 novos/102 resolvidos) | **não** | n/a | Grupo A1 (fantasma comprovado) | INDEPENDENT | RELATED | idem |
| TP1 20 (W021) | 123,98cm L–X–L | `B39+B39` / `B34+B19+B19+B34` | `C09` (candidato `SAME_B` correto rejeitado) | sim | permite | Grupo A2 + espelho paridade | **RELATED** | RELATED | idem + `BLOCK_ARM_ROLE_HUMAN_POLICY.md` |
| TP1 91 (W092) | idêntico a TP1 20 | idêntico | idêntico | sim | permite | idêntico | RELATED | RELATED | idem |
| TGD 4 (sem par humano) | 1174cm, canto girado | — | prisma forçado, nenhum candidato resolve | n/a | n/a | `_corner_bond_blocked_by_other_node` (geometria) | INDEPENDENT | INDEPENDENT | diagnóstico instrumentado |
| TGD 54 (sem par humano) | 269cm, parede dupla | — | idem | n/a | n/a | idem | INDEPENDENT | INDEPENDENT | idem |
| **Vizinhas 54-69cm** (TGD `W013/014/018/019/089-092`, TP1 `W013-016/088-091` + as 4-6 já citadas no diagnóstico original: 128/129/131-134, TP1 12/13/87/88) | 54-69cm, T+L ou L+L nas duas pontas | `B19[0-19]+B34[20-54]` / `B39[0-39]` — **B19 sistemático, 259 ocorrências no TP1** | `C09` degradado no canto/T + `C09×3`/`C09×4` de fill | **sim, faltando no solver** | **BLOQUEIA** (`_corner_single_element_candidate` nunca B19 + reserva pior-caso) | **DOMAIN_RULE_BLOCKED** | INDEPENDENT | INDEPENDENT | Fonte 1 (4-6 casos instrumentados) + Fonte 2 (26 casos por leitura direta do gabarito) |
| 79cm T–L (TGD `W048/049/062/063`, TP1 `W048/049/061/062`) | 79cm | `B34+C09+B34` / `C09+B39` — **sem B19** | não instrumentado nesta CR (fora dos 10 casos originais) | não | n/a | resto de 11cm (não 19-20cm) → compensador, não B19 | INCONCLUSIVO (não medido) | INCONCLUSIVO (não medido) | Fonte 2 |
| `W039`↔`W041` (TP1) | nó L | B19 repetido, sem alternância; nó **NUNCA** fisicamente coberto por `W041`, nem no humano | fiadas ímpares sem peça (main) / pares sem peça (branch ARM) — mesmo defeito espelhado | sim (mas nunca resolve o nó) | permite (B19 não é peça de amarração aqui) | P3 — artefato de paridade/banco, não regra de B19 | INDEPENDENT | INDEPENDENT | `nuvem/REGRAS_MODULACAO_BLOCOS.md` seção 30 (auditoria pré-integração) |

## Pergunta principal — classificação A/B/C/D

- **A — regra atual estrita**: **NOT_SUPPORTED**. O gabarito humano
  aprovado usa B19 encostado em nó L/T/X sistematicamente (259
  ocorrências medidas no TP1; confirmado em 8 paredes de 124cm e 16
  paredes de 54cm nesta CR, por três fontes independentes). Manter a
  regra tal como está descreve o comportamento do SOLVER, não do
  ESCRITÓRIO.
- **B — B19 como FILL (nunca a peça que resolve o nó)**:
  **SUPPORTED_BY_HUMAN_REFERENCE**. Em TODOS os 24+ casos positivos
  medidos (Fonte 1 + Fonte 2), sem exceção, a peça que fisicamente
  amarra o nó é `B34`/`B54`/`B34 X` — nunca `B19`. O B19 sempre fecha um
  trecho residual ADJACENTE a essa peça, nunca ocupa o lugar dela. Esta
  é a descrição mais fiel e mais simples do que o corpus mostra.
- **C — exceção para parede curta (com as 6 condições do pedido)**:
  **PARTIALLY_SUPPORTED**. É consistente com o corpus, mas só quando
  refinada: a condição relevante não é "parede curta" em si — é
  **"trecho residual de 15-20cm entre uma peça de nó já lançada e o
  próximo limite (nó ou fim do vão), com composição convencional que não
  fecha sem compensador"**. Uma parede curta de 79cm (Fonte 2) NÃO
  ativa a exceção, porque o resto lá é 11cm, não 19-20cm — o corpus
  distingue por TRECHO, não por comprimento total da parede. As 6
  condições do pedido (não cria prisma, não cria colisão, mantém
  cobertura, mantém amarração física do nó, passa hard gates) batem com
  o padrão observado (a amarração física continua sendo `B34`/`B54` em
  100% dos casos positivos).
- **D — outra regra**: não há evidência de um padrão diferente de B/C
  refinado nos dados coletados.

**Conclusão da pergunta principal**: **B e C não competem — C é a forma
operacional de B.** B descreve o PAPEL do B19 (nunca amarra, só
preenche); C descreve a CONDIÇÃO geométrica sob a qual isso deveria ser
permitido pelo solver (trecho residual de ~19-20cm, sem alternativa sem
compensador, com a peça de amarração de nó já presente e íntegra na
mesma fiada).

## Relação com NODE-FILL

Ver coluna da matriz. Resumo: dos casos onde B19 é de fato o gargalo
(vizinhas 54-69cm, Mecanismo 2), a relação é **INDEPENDENT** em todos —
o mecanismo é reserva pior-caso / catálogo de canto degradado, nunca
junta de fronteira entre fiadas (o que NODE-FILL endereça). A única
exceção é TP1 20/91, onde a peça de nó em si (não o resto de 19-20cm)
tem uma relação `RELATED` com NODE-FILL — mas esses dois casos já são
Mecanismo 1 (gate fidelity), não Mecanismo 2 (regra de B19).

## Relação com Gate Fidelity

Ver coluna da matriz. Resumo: os candidatos ALVO de 124/69cm (Mecanismo
1) são diretamente `RELATED` — implementar o Gate Fidelity já
resolvido/especificado deve destravá-los sem precisar tocar a regra de
B19. As paredes VIZINHAS de 54-69cm (Mecanismo 2, onde o C09×3/C09×4
realmente aparece) são `INDEPENDENT` de Gate Fidelity — corrigir os
gates SAFE REPAIR não muda `solve_l_corner`/`solve_t_intersection`.

**Isso significa que, mesmo depois do Gate Fidelity + NODE-FILL
mesclarem, as paredes de 54-69cm citadas nesta CR continuam
degradadas** — nenhuma CR hoje planejada as resolve. É esse o motivo
pelo qual esta investigação foi pedida separadamente.

## Option A — manter regra atual

- **Casos humanos explicados**: nenhum dos 24+ casos positivos fica
  explicado — todos continuam sendo tratados como defeito de reconstrução
  de encontros (a segunda hipótese não confirmada da seção 24.3) em vez
  de reconhecidos como prática legítima.
- **Casos sem solução**: todas as paredes de 54-69cm citadas (Fonte 1 +
  Fonte 2) continuam degradando para `C09`/`C09×3`/`C09×4`.
- **Risco de regressão**: zero (nenhuma mudança).
- **Risco de prisma**: zero.
- **Risco de compensadores**: mantém o problema atual (é a causa dos
  compensadores em excesso já listados em "Problemas abertos" do
  `PROJECT_STATUS.md`).
- **Risco de overfitting**: nenhum (não usa o corpus).
- **Testes necessários**: nenhum.

## Option B — flexibilização mínima (B19 como FILL, condição C aplicada)

Permitir B19 **apenas** como preenchimento de um trecho residual
adjacente a uma peça de amarração de nó já presente e íntegra na mesma
fiada (nunca substituindo B34/B54, nunca em trecho de meio de parede sem
nó, nunca se `audit_wall_bond_quality` mostrar B19 ocupando o próprio
ponto do nó em vez da peça de canto).

- **Casos humanos explicados**: os 24+ casos positivos medidos (54cm e
  124cm) passam a ter uma composição gerável sem violar a regra.
- **Casos que continuam sem solução**: `W039`↔`W041` (o nó nunca é
  fisicamente coberto por nenhuma peça — B19 fill não resolve isso,
  precisa de NODE-FILL ou de aceitar `JUNCTION_MISSING_BINDING` como o
  próprio humano faz); TGD 4/54 (canto girado, sem relação com B19).
- **Risco de regressão**: médio — `HALF_BLOCK_TIE_ADJACENCY_CM`/
  `HALF_BLOCK_NEAR_TIE` hoje bloqueiam QUALQUER B19 perto de nó; afrouxar
  isso exige a condição C explícita (peça de amarração presente E
  íntegra na mesma fiada) para não reabrir o bug já corrigido em
  2026-08-25 ("REGRA CRÍTICA #2" — fusão 9+9→19 nascendo B19 encostado
  num nó fechado só por aritmética).
- **Risco de prisma**: baixo — os 24+ casos medidos não mostram prisma
  novo introduzido pelo B19 em si (o prisma dos casos de 124cm vem do
  Mecanismo 1/gate, não do B19).
- **Risco de compensadores**: reduz (é literalmente o problema que
  motiva a mudança).
- **Risco de overfitting**: médio — a condição "resto de 15-20cm" foi
  medida em 2 projetos (TGD, TP1), mesma origem de escritório
  (`torre_easy_lo_r00`); não testada contra um terceiro projeto com
  proporções de vão diferentes.
- **Testes necessários**: sintéticos (peça de nó presente + resto
  19-20cm → aceita B19; peça de nó AUSENTE + resto 19-20cm → continua
  rejeitando; resto de 11/39/qualquer outro valor → não muda
  comportamento atual) + regressão contra os 24+ casos reais (TGD, TP1)
  medindo `C09×N`/`COMPENSATOR_*` antes/depois.

## Option C — regra alternativa (B19 liberado por comprimento total de
parede, não por trecho residual)

Permitir B19 perto de nó sempre que a parede inteira tiver ≤80cm
(interpretação literal do "40-80cm" citado no pedido original).

- **Casos humanos explicados**: os casos de 54-69cm sim; os de 124cm
  (TGD 89-92, TP1 20/91) **não** — são mais longos que 80cm, ficariam
  de fora mesmo sendo exatamente o padrão que o corpus confirma.
- **Casos que continuam sem solução**: os 124cm inteiros, que são 8 dos
  24+ casos medidos — maioria dos casos com evidência mais forte
  (3 fontes independentes).
- **Risco de regressão/prisma/compensadores/overfitting**: mesmos riscos
  da Option B, mas SEM o benefício correspondente nos casos de 124cm, e
  com risco adicional de permitir B19 em paredes curtas onde ele NÃO é
  necessário (ex.: 69cm L-L, onde o humano usa zero B19 — liberar por
  comprimento abriria uma porta que o próprio corpus não pede).
- **Testes necessários**: os mesmos da Option B, mais um teste negativo
  específico (parede de 69cm L-L não deveria preferir B19 mesmo estando
  dentro do range de comprimento, porque o corpus mostra `B34+B34`
  fechando exato).

Não recomendada — o corte por comprimento total da parede não corresponde
ao mecanismo real observado no corpus (trecho residual, não comprimento
da parede-mãe).

## Recomendação

**Option B (flexibilização mínima, escopada por trecho residual +
condição de amarração de nó íntegra) é a mais consistente com o corpus.**
Option C (corte por comprimento de parede) é mais simples de implementar
mas deixa de fora justamente os casos com evidência mais forte (124cm,
3 fontes independentes) e abre uma porta desnecessária nos casos de
69cm onde o humano não usa B19. Option A preserva o status quo, que já
está registrado como conflito não resolvido desde 2026-08-31 (seção
24.3) — mantê-lo sem decisão é, na prática, aceitar o `C09×3`/`C09×4`
como resultado permanente das paredes de 54-69cm.

**REQUIRES_HUMAN_DOMAIN_APPROVAL** — esta CR não decide a regra de
alvenaria. A condição proposta (trecho residual 15-20cm, peça de nó
`B34`/`B54` presente e íntegra na MESMA fiada, sem prisma novo, sem
colisão, cobertura mantida) precisa de aprovação explícita do usuário
antes de qualquer implementação — inclusive porque ela reverte
parcialmente uma decisão explícita anterior do próprio usuário
(2026-08-25, "não utilizar meio bloco como recurso para fechar uma
amarração") e precisa ser registrada como atualização oficial de regra
em `nuvem/REGRAS_MODULACAO_BLOCOS.md`, nunca implementada primeiro e
documentada depois.

## Decisão humana necessária

1. A condição proposta (Option B: B19 como fill de trecho residual
   15-20cm, adjacente a peça de amarração de nó já íntegra na mesma
   fiada, nunca substituindo B34/B54) reflete a intenção original da
   regra de 2026-08-25, ou essa regra deve permanecer estrita mesmo
   sabendo que ela diverge do escritório em 259 ocorrências?
2. Se aprovada, a condição deve valer só para trechos medidos entre
   15-20cm, ou o usuário quer um intervalo diferente (o corpus atual só
   tem amostras nesse intervalo — não há evidência para generalizar além
   dele)?
3. `W039`↔`W041` (nó nunca coberto, nem pelo humano) deve ser aceito
   como "mesmo defeito do gabarito aprovado" (P3, sem CR) ou precisa de
   investigação própria fora do escopo de B19?
4. Ordem de implementação: esta CR (regra de B19) depende de
   `CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY` e `CR-BLOCK-NODE-FILL-JOINT`
   apenas nos casos de 124cm (Mecanismo 1) — os casos de 54-69cm
   (Mecanismo 2, onde a regra de B19 é o gargalo real) são
   **independentes** e poderiam ser priorizados antes, em paralelo, ou
   depois, por decisão do usuário.

## Production diff

ZERO

## Baseline diff

ZERO

## Reference diff

ZERO

## Rules diff

ZERO

## Veredito

**EVIDENCE_READY_FOR_DOMAIN_DECISION**

Regra atual = Interpretação A (estrita), lida ao pé da letra. Corpus
humano (3 fontes independentes, 24+ casos positivos em 2 projetos,
mais casos negativos que refinam a condição) = Interpretação B (B19
nunca amarra, só preenche), operacionalizada como Interpretação C
refinada por TRECHO RESIDUAL (15-20cm), não por comprimento total da
parede. Dois mecanismos de divergência solver×humano foram separados: o
que a formulação original do pedido descreve como "C09+C09+C09" mistura
um bug de Gate Fidelity já com CR definido (paredes-alvo de 124/69cm,
RELATED_TO_GATE_FIDELITY) com um bloqueio real de regra de domínio nas
paredes vizinhas de 54-69cm (DOMAIN_RULE_BLOCKED, INDEPENDENT de
NODE-FILL e de Gate Fidelity) — só o segundo mecanismo é, de fato, uma
questão de regra de B19. Nenhuma regra alterada. Nenhum código tocado.
