# Estratégias de reforço de aberturas
STATUS: PENDING (arquitetura geral); CHANNEL aprovada como estratégia oficial em 2026-09-14

## Contexto
Há gramática comum, mas peças dedicadas de 9 cm e corridas de 19 cm exigem ocupações diferentes. opening_strategy atual tem outro significado.

## Evidência
[Comparação](../../reference_projects/COMPARISON.md) e [contrato proposto](../architecture/opening-reinforcement-strategies.md). #33/#35 integrados apenas como evidência.

## Opções
1. Um motor + OpeningReinforcementStrategy configurável antes da modulação.
2. Dois motores completos: duplica contratos, testes e manutenção.
3. Manter somente comportamento legado: adia suporte aos reforços.

## Impactos
A opção 1 requer reservas/subfaixas, altura por peça, mapping e validação comum. Apoio/simetria/comprimento, cortes e escopo de vãos precisam políticas explícitas; ≥9 cm não se aplica automaticamente a CHANNEL.

## Recomendação
Opção 1. Propor escolha explícita por recorte/nível; preservar política continuous_first separada. Implementar em CRs graduais, sem default A/B implícito.

## Decisão do usuário
PENDENTE — nenhuma aprovação presumida pelo pedido de arquitetura ou merge documental.
Aprovar ou revisar arquitetura; definir catálogo discreto e apoio mínimo de A, simetria/preferência de excedente, apoio/continuidade de B e tratamento de ABERTURA/peitoril divergente. Valores ainda não aprovados.

## Implementação candidata (2026-09-14)
Estratégia B (CHANNEL) implementada como opt-in na branch `claude/butanta-channel-reference-implementation` ([arquitetura](../architecture/channel-strategy-implementation.md), regra 51). **Não é aprovação**: a decisão continua PENDENTE; A (LINTEL) não implementada.

## Decisões do usuário (2026-09-14, missão "FECHAR CHANNEL E LEVAR PR #40 A READY FOR REVIEW")
- A: CHANNEL é estratégia oficial; a arquitetura terá também LINTEL_COUNTERLINTEL, que não é implementada agora.
- B: apoio de 19 cm é PREFERENCIAL, não mínimo.
- C: abertura livre até o topo é válida (sem canaleta superior artificial).
- D: o cruzamento de T do humano é válido — classificação `CHANNEL_THROUGH_T_SUPPORTED_PATTERN`, sem relaxar o auditor global.
- E: topo/peitoril fora da grade continua PENDENTE.
- F: cinta de topo continua PENDENTE (TOP_BOND_BEAM ≠ OPENING_CHANNEL).
Implementação: PR [#40](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/40), regra 51.13. LINTEL_COUNTERLINTEL, catálogo de verga e demais escolhas A continuam pendentes.

## SHA/PR relacionado
Base de consolidação: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9. [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32),
[#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33), [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35).
Produção candidata citada deve ser lida no SHA correspondente, não na main.
Ao decidir: registrar data, autorização literal, opção, escopo e PR de implementação;
atualizar regra oficial e status no mesmo pacote.
