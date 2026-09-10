# Estratégias de reforço de aberturas
STATUS: PENDING

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

## SHA/PR relacionado
Base de consolidação: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9. [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32),
[#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33), [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35).
Produção candidata citada deve ser lida no SHA correspondente, não na main.
Ao decidir: registrar data, autorização literal, opção, escopo e PR de implementação;
atualizar regra oficial e status no mesmo pacote.
