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
  **Nota 2026-09-25 (D16):** SUSPENSO desde 2026-09-18 pela regra 75 (canaleta nunca amarra). Medido no D16: a travessia remove a B34/B54 do nó naquela fiada (T amarrados 37 → 35 no BUTANTÃ); o conflito D × 75 é decisão humana pendente (REGRAS §75.1).
  **Decidido 2026-09-25 (usuário):** regra 75 MANTIDA; a 51.6 não é reativada — AMARRAÇÃO VÁLIDA > CONTINUIDADE/APOIO (REGRAS §75.1).
- E: topo/peitoril fora da grade continua PENDENTE.
- F: cinta de topo continua PENDENTE (TOP_BOND_BEAM ≠ OPENING_CHANNEL).
Implementação: PR [#40](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/40), regras 51.13 e 51.14.

## Auditoria independente (2026-09-14)
- 30.8 desligada por default (opção B escolhida pelo usuário); 7719511 = limitação temporária do CHANNEL.
- CHANNEL nunca é default da tela; só por escolha explícita.
- Passagem livre isolada abre só o vão (pedido do usuário).

## Fechamento final (2026-09-14)
- APROVADO: passagem livre contínua (padrão PAR28 detectado pela geometria) abre de face de nó a face de nó, sem o pilar intermediário (regra 51.9).
- 30.8 continua desligada; 7719511 KNOWN_LIMITATION. Topo/peitoril fora da grade e cinta de topo continuam pendentes/fora do escopo.
- Merge normal do PR #40 autorizado pelo usuário condicionado aos gates (regra 51.15). LINTEL_COUNTERLINTEL, catálogo de verga e demais escolhas A continuam pendentes.

## SHA/PR relacionado
Base de consolidação: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9. [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32),
[#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33), [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35).
Produção candidata citada deve ser lida no SHA correspondente, não na main.
Ao decidir: registrar data, autorização literal, opção, escopo e PR de implementação;
atualizar regra oficial e status no mesmo pacote.
