# Histórico de erros, correções e conflitos

Fonte detalhada: `nuvem/REGRAS_MODULACAO_BLOCOS.md` (REGRAS), seções
citadas. Este arquivo existe para **não repetir** um bug ou uma decisão já
tomada — antes de "corrigir" algo que parece errado, checar aqui se já
não foi resolvido (ou se está deliberadamente pendente) antes.

## Bugs reais já corrigidos (não reintroduzir)

| Data | Bug | Causa raiz | Correção | Seção |
|---|---|---|---|---|
| 2026-08-21 | Fiada A e B empilhadas na mesma cota | `course_index` não distinguia fiada física par/ímpar | cada índice só recebe candidatos da letra correspondente | §8 |
| 2026-08-21 | Cota Z duplicada na criação | Z passado já absoluto, mas `NewFamilyInstance` trata como offset relativo ao Level | passar sempre offset relativo | §8 |
| 2026-08-25 | Fiada B saía idêntica à Fiada A (100% junta coincidente) em trechos fechados dos 2 lados que fecham só com B39 (múltiplo de 40cm) | `_pier_ordered_layout` ignorava `first_code` quando um tier mais cedo já fechava | `_pier_forced_bypass_layouts` chama `_greedy_fill_blocks` direto com pool/primeiro bloco escolhidos | §11.1 |
| 2026-08-25 | Desencontro de junta escolhia pior solução quando comparado "contra si mesmo" | `_score` comparava `(alinhamento, coincidência)` — alinhamento primeiro | invertido para `(coincidência, -alinhamento)` — coincidência é critério primário | §11.2 |
| 2026-08-25 | "9+9→19" conseguia nascer B19 encostado num nó fechado | fusão de compensadores só olhava aritmética do par, não a parede inteira | só aceita fusão em B19 quando o par está numa ponta aberta de verdade (`leading_open`/`trailing_open`) | §2, regra crítica #2 |
| 2026-08-25 | "Lançar Blocos - criar" não idempotente — parte da parede "andava", parte "ficava parada" ao recalcular | criação nunca apagava o lote anterior; peças de nó ficavam sobrepostas (pareciam iguais), preenchimento comum duplicava | `_execute_create` apaga o lote anterior por completo antes de criar — cada clique é substituição atômica | §13.4 |
| 2026-08-28 | Parede real de 319cm reportada como "não fecha" por poucos cm, nas duas fiadas | `_wall_end_default_start_cm` reservava meia espessura de parede + junta mesmo em `STRAIGHT_CONTINUATION` (onde não existe peça de amarração nenhuma) | reserva zerada para `FREE_END`/`STRAIGHT_CONTINUATION`/`AMBIGUOUS` conforme o caso; `AMBIGUOUS` continua reservando (existe peça real na outra faixa de altura, seção 15) | §11.9 |
| 2026-08-28 | Trecho de 29cm virava `C04+C09+C09+C04` (4 compensadores em sequência, reprovado) em vez de manter uma junta coincidente que só escala pra ajuste | `_score` do desencontro ignorava a regra #2 (excesso de compensadores) | `_score` passou a `(excesso_compensadores, coincidência_junta, -alinhamento)` — regra #2 na frente | §16.1 |
| 2026-08-28 | Trechos de 469cm e 139cm caíam no tier de compensador embora existisse composição limpa (sem compensador) | guloso (`_greedy_fill_blocks`) nunca faz backtracking, só tenta 1 ordem fixa | tenta cada código do pool como primeiro bloco; se ainda falhar, busca exata (DP em décimos de cm, menos-peças-primeiro) | §16.2 |
| 2026-10-09 | Rodar o botão de novo no mesmo documento empilhava Walls: 302 Walls para 34 eixos depois de três execuções | `main()` sempre chamava `Wall.Create` | segmento cuja Wall igual já existe (nível, pontas na grade de 0,5 cm, altura e base) é reaproveitado; o output informa quantos. Sem teste automatizado e sem medição no Revit depois da correção | §87.7 |
| 2026-10-08 | O botão não reproduzia, a partir do arquivo cru, a modulação aprovada do BUTANTÃ | entrada divergente em 6 pontos: layer `Paredes` (acabamento, 52 eixos), referência estrutural só do próprio import, regra 49 aparando eixos, sobra de 5 cm protegida pela testa do CAD, porta 1 cm abaixo do piso, `setup` não repassado ao handler | layer `Estrutura _1_`; referência de qualquer import; regra 49 só classifica; sobra ≤ 10 cm aparada no refresh; peitoril até 2 cm abaixo sobe; `setup` repassado — 6 526/6 526 peças iguais ao aprovado | §87 |
| 2026-10-05 | Junta corrida em X≈49,5 cm em 13 fiadas nas paredes de 99 cm com T e toco (W29/W30/W31) | espaço do B54 medido com a reserva de PIOR CASO do canto da outra ponta (23 de 27 cm); o T degradava para L ancorado na face da que chega | espaço medido de novo só na fiada da peça do T, com a reserva por fiada (11.14), e penalidade na busca de fase | §86.15 |
| 2026-10-05 | Compensador atrás do B19 junto do vão (W6 `B54 \| C09 \| B19 \| vão`; pilaretes da W0) | o recompositor punha o percurso obrigatório antes da faixa e media a última fiada como bloco; a forma certa ficava fora das sementes do estágio A | termo `face` logo depois do `b19`, falha dura `COMPENSATOR_NOT_AT_JAMB_FACE`, falhas monótonas como intrínsecas no estágio A, segunda passada da jamba | §86.13 |
| 2026-10-05 | Meia canaleta (U19) na verga/cinta: 128 U19 no cálculo do BUTANTÃ | B19 → U19 e U19 no trecho livre (§86.7/§86.12) | U19 proibida; peças moles de c−2 não acompanhadas; U39/U34 + no máximo um U_CUT ≥ 9 cm | §86.14 |
| 2026-10-05 | Canaletas da verga/cinta desalinhadas da fiada de baixo: 184 de 621 sobre alvenaria não coincidiam peça a peça com c−2 | verga/cinta era a fiada resolvida como contínua (sem a abertura), trocada peça a peça; a grade do pilarete não subia | sobre alvenaria a canaleta repete as juntas de c−2; sobre o vão a grade é livre | §86.12 |
| 2026-09-30 | O script nunca gerava a grade de B34 que o usuário desenhou na W4 (pilarete 945–1144): mantinha `B19 B39 C09 B54` / `B39 B39 C09`, 14 vazados quebrados | cinco causas juntas: régua recusava menor sobre menor (8,986 < 8,99, ruído de 0,04 mm); lista de composições cortava os lados dos B34 e esgotava o orçamento com B19; fiada da verga fora da unidade; fiadas acima da porta nunca trocadas juntas; estágio A estourava o orçamento (4.158 > 4.096) e caía na descida fiada a fiada | tolerância geométrica 0,5 mm; lados uniformes/alternados, sem B19 primeiro; verga como membro (U39/U34, nunca encolhe); grade derivada da jamba de mesma paridade avaliada com todas as fiadas; triagem por falha intrínseca. Bancada: W4 14 → 0, W5 54 → 0, W2 13 → 0 | §85.9 |
| 2026-09-30 | Isenção da junta do B19 de fechamento (11.8) aplicada sem restrição no recompositor empilhou o pilarete da W5 (`C04 B19 B39 B19` nas duas paridades, a prumo) | toda junta de um pilarete curto é "de fechamento" | isenta só contra junta que NÃO é de fechamento de B19 na outra fiada | §85.9 |
| 2026-09-29 | Recompositor da lateral (1ª versão da §85) trocou o desenho do usuário no pilar direito da janela central (`B39 B39 C09` / `B19 B39 C09 B54`) por `B34 C09 B39 C04` | régua por INTERFACE contava 14 quebras no encontro B39×B54 (4,0 cm de largura comum), quebra que existe igual nas fiadas cheias — a troca só mudava a quebra de lugar | objetivo passou a ser coluna contínua na altura inteira + referência modular comum; células em coluna contínua 11.554 → 11.720 na planta | §85 |
| 2026-09-28 | Compensador/pastilha junto de porta/janela alternava de posição entre as fiadas (0 / 20 / 40 / 60 cm do vão) — 29 de 47 laterais no BUTANTÃ; prisma dos vazados 39/19 interrompido na jamba | trecho junto da jamba recomposto fiada a fiada: fiada A pelo guloso (fusão 9+9→B19 só na ponta aberta, B19 no vão e C09 para dentro); fiada B fugindo de propósito da junta do C09 da A (§11.8 só na validação); uma composição por paridade | passe FINAL de permutação por lateral, fiadas em conjunto, prisma pela geometria real como restrição dura, isenção só da junta da faixa; 29 → 2 laterais alternando, contagem de peças idêntica | §84 |

## Bugs de relatório diagnosticados, ainda NÃO corrigidos

Não afetam a geometria real dos blocos — afetam o que o usuário vê
depois. Não assumir que estão corrigidos.

| Bug | Causa | Correção pendente | Seção |
|---|---|---|---|
| Realce de colisão infla em ~127× (11.211 peças marcadas vs. 55 colisões reais medidas) | detecção compara `candidates` inteiro, incluindo variantes alternativas da mesma fiada que nunca coexistem no modelo | exigir que os DOIS lados do par tenham sido criados **e** compartilhem o mesmo `course_index` antes de marcar | §17.1 |
| `MirrorElement` deixa peças órfãs a cada lançamento (medido: 510 órfãs) | `MirrorElement` cria cópia, a cópia não entra em `created_instances`; limpeza por Id nunca remove a órfã | registrar o Id da cópia, ou usar overload que espelha sem copiar; enquanto isso não existir, limpeza correta = apagar toda instância das famílias do catálogo cujo Id não esteja em `created_instances` | §17.2 |

## Conflitos abertos (não implementar nenhum dos dois lados até resolver)

| Conflito | Hipótese do usuário | Medição real | Status |
|---|---|---|---|
| "Canaleta sempre na última fiada do topo de toda parede" | Sim, sempre | Só 39,4% (87/221) das linhas confirmam; contraexemplo de 51 peças sem nenhuma canaleta | **NÃO RESOLVIDO** no geral — a §86.7 implementou a cinta de topo (chave `TOP_BOND_BEAM_ENABLED`, desligável por projeto): BUTANTÃ 34/34 paredes, prédio inteiro 39–74 %; `DECISION-TOP-BOND-BEAM` continua PENDING | §10.7, §86.7 |
| Alternância obrigatória de papel entre os dois L da mesma parede (§30.5) × humano "mesma fiada" | §30.5 é REGRA OBRIGATÓRIA | humano na mesma fiada em 9/9 paredes entre dois L | no caminho geral com `GENERAL_PHASE_RELATION_ENABLED` a §30.5 vira preferência de custo (pedido de 2026-10-01); CHANNEL e chave desligada mantêm a §30.5; rodar regressão TGD/TP1 antes de mesclar | §86.2 |
| Shaft: B54 + C09 como preenchimento (§85.8) × humano | exceção da §85.8 | humano fecha W27/W33 com os dois cantos na mesma fiada, sem B54 no miolo | **PENDENTE** — perguntar ao usuário se a solução humana substitui a exceção | §86.2, §86.11 |
| Forma A da jamba (`C09 C04` + B34 com vazado menor sobre a faixa) × §84 item 3 / §85.8 | vazado sobre compensador maciço = prisma interrompido | humano 35/35 nas sobras 14/34 | implementado LIGADO (`JAMB_HUMAN_A_FORM_ENABLED`) — **pendente de confirmação do usuário** | §86.6 |
| Cinta variante B (canaleta passando sobre o nó, como o humano) | canaleta nunca amarra (§75) | humano passa a cinta sobre 46–48 de 50 nós | só documentada; exige exceção à §75 — decisão do usuário (a §86.16 adotou só o B54 → U34 + U19) | §86.7 |
| Junta U34\|U19 do B54 da cinta caindo na face da parede que chega | "todo B54" vira U34 + U19 | fixture `tee`: junta em 309,5 = face do T | sai com `TOP_BOND_BEAM_B54_JOINT_COINCIDENT`; PADRÃO OBSERVADO a confirmar com o usuário (alternativa: B54 de nó como bloco nesses casos) | §86.16 |

## Padrões observados, ainda NÃO confirmados (não tratar como regra travada)

| Item | Amostra | Nota |
|---|---|---|
| Sequência de fiadas da verga em canaleta (fino-jamba + fino-cheio + canaleta) | 2 exemplos concordantes | forte, mas não codificar o layout exato sem medir mais vãos |
| Comprimento de apoio da canaleta além das jambas | 1 exemplo com medição | precisa de valor numérico confirmado, não só "mais largo que o vão" |
| Desencontro de junta vertical ≈15cm | 1 par de fiadas | precisa medir distribuição completa antes de virar constante |
| Última fiada de pavimento ajusta ~+11cm quando pé-direito não é múltiplo de 20cm | 2 ocorrências, 1 projeto | ver `nuvem/diagnosticos/CHACARA-TORRE-EASY-LO.md` |
| Lado do B34 ímpar da faixa equilibrada no fim do eixo | ~73 % das fiadas (155/212), com exceções sem regra geométrica | desempate configurável, não regra (§86.3) |
| Apoio de 40 cm para verga de vão ≥ 140 cm | 10/10 lados, 1 projeto | preferencial; mínimo continua 19 cm (§86.8) |
| Ponta livre fechada com coluna de C04 em todas as fiadas | 1 caso (W25) | não implementado — um caso não sustenta regra (§86.9) |
| Lado fechado do C09 = −X local | humano 129/129 pela transformação | implementado (§86.10); confirmar pela geometria sólida da família |

## Pendências de código explícitas (documentadas, aguardando implementação)

Não implementar por conta própria sem reconfirmar — mas também não tratar
como "já resolvido":

- **Pilarete entre aberturas como trecho independente** (não como sobra do
  prisma geral) — REGRAS §18.2, ver OPENINGS.md.
- **Transição B34→B39 com look-ahead da fiada seguinte** — hoje resolve um
  par A/B por vez, sem olhar adiante — REGRAS §18.6, ver BONDING.md.
- **`num_courses`/`base_z_abs` por parede** (hoje globais por seleção) —
  causa fiadas a mais e blocos na cota errada em seleção com peitoril +
  verga separados do trecho cheio. Workaround atual: agrupar por
  `(altura, offset_de_base)` e rodar solver+criação por grupo — REGRAS
  §15.
- **Pré-check "modulation-aware" antes de `Wall.Create`** — hoje a
  modulação é 100% reativa (corrige depois de criar); não existe ainda um
  passo que prefira, entre geometrias de CAD equivalentes, a que já fecha
  sem precisar de ajuste — REGRAS §14.3 (gap de desenho, não bug).
- **B34 de meio-de-parede sem alinhamento de vão menor** entre Fiada A/B —
  REGRAS §6. (Tratado depois pela §52, pelo arranjo §60–§65/§81 e pela faixa
  equilibrada da §86.3; a extensão da §86.3 a corridas com abertura continua
  pendente.)
- **Calço de C09 deitado** quando sobram ≥ 9 cm acima da última fiada — a
  família existe, sem código no catálogo (§86.5).
- **Referência pela peça fixa do nó na jamba de porta/boneca** (sem fiada
  cheia abaixo) — §86.6.
- **Recompositor da jamba mede a última fiada como bloco** embora a cinta a
  troque por canaleta depois — §86.13 (etapa própria; muda a régua de
  colunas).
- **Toco entre 10 e 20 cm além da face** (o B54 centrado não cabe): o T
  continua degradando para L — decisão do usuário (§86.15).
- **§87.7 sem teste automatizado e sem medição no Revit depois da correção**
  — rodar o botão duas vezes no mesmo arquivo e conferir a contagem de Walls.

## Regra alterada por pedido explícito do usuário (prioridade sempre da mais recente)

- 2026-10-08 (§86.16, §87): todo B54 da última fiada vira U34 + U19 (inclusive
  o de amarração do T; exceção à §75/§76.1 e à §86.14 só para essa peça); o
  botão reproduz a modulação aprovada a partir do arquivo cru (layer
  `Estrutura _1_`, nunca `Paredes`).
- 2026-10-05 (§86.9, §86.12–§86.15, prints do Revit): tocos de eixo além da
  face **são modulados** (`STUB_TRIM_ENABLED = False`; só a sobra de CAD
  ≤ 10 cm é aparada); a canaleta segue a grade da fiada de mesma paridade
  abaixo; compensador e pastilha encostados no vão com o B19 atrás; sem meia
  canaleta ("isso não existe, pode parar"); T com toco sem junta na face.
- 2026-10-01 (§86): aproximar o projeto humano BUTANTÃ R08_LT ajustando as
  regras, sem copiá-lo — aberturas na posição ORIGINAL (§86.1, desliga o
  deslocamento da §85.4 no botão); §30.5 vira preferência de custo no caminho
  geral (§86.2); cinta de topo variante A (§86.7, "canaleta nunca serve de
  amarração").

- 2026-09-29 (§85): prioridade = vazados alinhados de verdade (área livre
  comum, coluna na altura inteira); B19 só em fechamento (exceção da §35
  revogada; §56.3 item (a) superado); composição de mesmo comprimento na
  lateral (supera o "só permutação" da §84); aberturas podem andar até 10 cm
  da posição original com largura preservada (conflito com §18.13 registrado).
- 2026-09-28 (§84): compensador/pastilha da lateral de abertura encostado
  no vão e alinhado entre as fiadas (faixa vertical junto do vão); B19
  imediatamente atrás da faixa passa a ser EXCEÇÃO PERMITIDA da regra do
  meio-bloco (§2). Pendência de decisão: ligar também no CHANNEL.
- 2026-08-25: prioridade de B19 sem ponta aberta rebaixada — compensador
  tentado antes dele, quando trecho tem as duas pontas fechadas (inverteu
  ordem anterior de 2026-08-21 a 2026-08-24). Ver BLOCKS.md.
- 2026-08-28: variação de layout por fiada de mesma paridade
  (`PIER_LAYOUT_VARIANTS_PER_COURSE`, K=3) contrariada — usuário quer o
  padrão repetindo entre fiadas ímpares/pares de verdade, mesmo que isso
  reintroduza algum risco de `ALTERNATING_JOINT_PATTERN` que a K>1
  tentava evitar. Ver BONDING.md, "Padronização entre fiadas". Pendência:
  reavaliar K=1 medindo `CONTINUOUS_VERTICAL_JOINT`.

## 2026-10-23 — DONA FRANCISCA: portas encostadas no nó → 56 nós com coluna de C09 (REGRAS §88.7/§88.8)

Causa real: o oráculo da grade de 5 cm mediu só `non_modular`; a porta encostada
no canto (J = 7) passou nesse critério mas deixou 14 cm no braço do nó, abaixo
dos 34 cm do B34 — o motor caiu em `JUNCTION_UNRESOLVED_FILL` (76.1) e empilhou
C09 em 13 fiadas. Correção de motor: `materialization_plan` passo 3 pula esse
compensador e marca o nó em `unresolved_junctions` (gate, chave
`UNRESOLVED_JUNCTION_FILL_IS_SKIPPED`). Correção de projeto: boneca ≥ 34 cm.
