# Validação obrigatória

Fonte detalhada: REGRAS §7 (ajuste geométrico), §9 (testes), §11.4/§11.5
(validação de alinhamento), §13 (pipeline+relatório), §14 (auditoria de
conformidade), §16 (regra #2 vs. desencontro), §17 (bugs de relatório),
§18.7/§18.8/§18.10/§18.11 (checklist final).

Nenhuma modulação é considerada concluída apenas porque os blocos foram
posicionados. Ela só é válida depois de passar por todas as checagens
abaixo.

## 1. Geometria

- Todos os blocos corretamente posicionados; nenhum deslocado sem
  justificativa.
- Nenhum bloco fora da parede correspondente.
- Nenhum bloco abaixo da planta/nível correto, nenhuma cota Z incorreta
  (fiada 1 = `base_z_abs+1cm`, passo 20cm — ver BLOCKS.md).
- Todas as fiadas alinhadas.
- **Colisão entre blocos**: nenhum bloco dentro do volume de outro, exceto
  a sobreposição prevista pelas regras de amarração. Medir com **OBB
  (SAT)**, nunca AABB (REGRAS §18.7).
- **Cuidado com paredes de peitoril/verga**: podem ter `WALL_USER_HEIGHT_
  PARAM`/`WALL_BASE_OFFSET` próprios, diferentes do resto da seleção —
  usar altura/base globais para todas produz fiadas a mais e blocos
  nascendo na cota errada (REGRAS §15). Agrupar por `(altura,
  offset_de_base)` e validar/gerar por grupo até essa lacuna ser corrigida
  por parede.

## 2. Modulação

- A parede foi modulada com os blocos disponíveis, seguindo a prioridade
  de preenchimento (BLOCKS.md).
- Sem uso excessivo de compensadores/pastilhas (nunca 2+ em sequência,
  `MAX_COMPENSATORS_PER_TRECHO=1`).
- Sem sequências desnecessárias de peças pequenas.
- Peça especial não usada como solução fácil quando existe solução
  modular melhor — o guloso puro pode falhar onde existe composição
  limpa (sem compensador); reforçar com busca por primeiro-bloco
  alternativo e, se preciso, busca exata (programação dinâmica) antes de
  aceitar uma composição com compensador (REGRAS §16.2).
- Blocos distribuídos de forma coerente — buscar a **melhor** modulação
  possível, não só a primeira combinação matemática que fecha.

## 3. Amarrações

Verificar **individualmente** cada L/T/X/ponta:

- Sem amarração incompleta.
- Sem blocos só encostados visualmente (sem prova geométrica).
- Sem sobreposição incorreta.
- Sem deslocamento de blocos distante da região da amarração.
- Sem alteração de apenas parte da parede — a correção sempre trata a
  parede como sistema completo (todos os blocos daquela parede acompanham
  o ajuste; amarrações recalculadas; fiadas continuam alinhadas; blocos
  perto de quinas/encontros também atualizados).
- Cada tipo (L/T/X) obedece às regras específicas de BONDING.md.

## 4. Alinhamento vertical entre fiadas (regra #1)

- Bloqueante: `validate_wall_modulation` reprova (`sem_alinhamento_
  vertical`) qualquer coincidência de junta entre Fiada A e Fiada B fora
  da exceção permitida (peça de fechamento contra abertura — REGRAS
  §11.8, ver BONDING.md).
- Uma reprovação aqui dispara o mesmo ajuste geométrico automático (Etapa
  3B) usado para trecho que não fecha aritmeticamente — nunca é ignorada.

## 5. Meio-bloco perto de amarração (regra #2)

- `audit_wall_bond_quality`/`audit_all_walls_bond_quality` fazem a
  checagem final vendo a parede **inteira** (todas as fiadas físicas de
  uma vez), depois de tudo lançado — segunda verificação independente da
  garantia já aplicada na geração.
- Bloqueia a criação (`HALF_BLOCK_NEAR_TIE`) se algum B19 estiver perto
  de uma amarração real.

## 6. Aberturas

- Nenhum bloco dentro do vão real de porta sem peitoril (bloqueante,
  `find_door_void_violations`).
- Faces alinhadas exatamente com bordas de abertura, fim de parede e
  encontros (REGRAS §18.3).
- Bloco `CORTADO` perto de abertura só é erro se não houver justificativa
  geométrica próxima (REGRAS §10.5).

## 7. Relatório final consolidado

`build_final_modulation_report` junta as duas fontes de problema (Etapa
3B: aritmética/geometria; Etapa 4C: amarração) num único veredito por
parede — **nunca** aceitar "passou numa análise, reprovado na outra" como
sucesso. Categorias:

- **Paredes analisadas** = todos os eixos.
- **Inicialmente com erro** = Etapa 3B antes de qualquer correção.
- **Corrigidas automaticamente** = erro resolvido depois do ajuste.
- **Moduladas com sucesso** = só quando passa nas DUAS etapas.
- **Sem solução** = resto, com o motivo exato de cada etapa que reprovou.

Nenhuma parede é ignorada silenciosamente; "sem solução" é um resultado
honesto quando esgotadas as correções permitidas — nunca escondido atrás
de um "sucesso" que não é real (REGRAS §13.3).

## 8. Cuidados de método (evitar falso positivo/negativo no próprio validador)

- **Colisão**: comparar só candidatos que de fato coexistem no modelo
  (mesmo `course_index`/fiada física, ambos os lados realmente criados) —
  medir sobre variantes alternativas da mesma fiada infla o realce em
  ~127× (bug de relatório conhecido, REGRAS §17.1 — ver ERROR_HISTORY.md).
- **Contagem de instâncias criadas**: `MirrorElement` cria cópia em vez de
  espelhar no lugar — sem registrar o Id da cópia, sobra peça órfã que a
  limpeza por Id nunca remove (REGRAS §17.2 — ver ERROR_HISTORY.md).

## Checklist final antes de dar a modulação por concluída (REGRAS §18.11)

- [ ] Todas as paredes processadas, nenhuma parcialmente modulada, nenhum
      trecho sem bloco.
- [ ] Faces alinhadas com aberturas; nenhum bloco invadindo vão.
- [ ] Pilaretes modulados (individualmente, ver OPENINGS.md).
- [ ] Cruzes com B54 correto e vãos menores alinhados.
- [ ] B34 respeitando o alinhamento do vão menor (onde já garantido: L e
      T degradado).
- [ ] T sem espaço reinterpretado como L (C09/C04), nunca forçado.
- [ ] Nenhuma sobreposição inválida, nenhum bloco dentro de outro.
- [ ] Fiada 1 ≡ Fiada 3 ≡ …, Fiada 2 ≡ Fiada 4 ≡ …, com continuidade
      lógica entre elas.
- [ ] Toda parede/trecho tem um estado explícito: modulado / precisa
      ajuste geométrico (com motivo) / não modulável (com motivo exato).

Ordem de prioridade quando a situação é difícil (REGRAS §18.10) — ver
RULES.md, princípio 3.
