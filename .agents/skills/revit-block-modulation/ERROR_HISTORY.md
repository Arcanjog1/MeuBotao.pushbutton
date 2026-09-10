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
| "Canaleta sempre na última fiada do topo de toda parede" | Sim, sempre | Só 39,4% (87/221) das linhas confirmam; contraexemplo de 51 peças sem nenhuma canaleta | **NÃO RESOLVIDO** — próximo passo: inspecionar visualmente a linha do contraexemplo antes de decidir se é regra-com-exceção ou problema de método de detecção | §10.7 |

## Padrões observados, ainda NÃO confirmados (não tratar como regra travada)

| Item | Amostra | Nota |
|---|---|---|
| Sequência de fiadas da verga em canaleta (fino-jamba + fino-cheio + canaleta) | 2 exemplos concordantes | forte, mas não codificar o layout exato sem medir mais vãos |
| Comprimento de apoio da canaleta além das jambas | 1 exemplo com medição | precisa de valor numérico confirmado, não só "mais largo que o vão" |
| Desencontro de junta vertical ≈15cm | 1 par de fiadas | precisa medir distribuição completa antes de virar constante |
| Última fiada de pavimento ajusta ~+11cm quando pé-direito não é múltiplo de 20cm | 2 ocorrências, 1 projeto | ver `nuvem/diagnosticos/CHACARA-TORRE-EASY-LO.md` |

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
  REGRAS §6.

## Regra alterada por pedido explícito do usuário (prioridade sempre da mais recente)

- 2026-08-25: prioridade de B19 sem ponta aberta rebaixada — compensador
  tentado antes dele, quando trecho tem as duas pontas fechadas (inverteu
  ordem anterior de 2026-08-21 a 2026-08-24). Ver BLOCKS.md.
- 2026-08-28: variação de layout por fiada de mesma paridade
  (`PIER_LAYOUT_VARIANTS_PER_COURSE`, K=3) contrariada — usuário quer o
  padrão repetindo entre fiadas ímpares/pares de verdade, mesmo que isso
  reintroduza algum risco de `ALTERNATING_JOINT_PATTERN` que a K>1
  tentava evitar. Ver BONDING.md, "Padronização entre fiadas". Pendência:
  reavaliar K=1 medindo `CONTINUOUS_VERTICAL_JOINT`.
