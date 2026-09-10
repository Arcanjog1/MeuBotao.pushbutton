# Migração oficial CR-B
STATUS: PENDING

## Contexto
Preparação #28 possui tabela de identidade; não autoriza escrita de input/reference/baseline/reference_score.

## Evidência
[Auditoria §8](../AUDITORIA_BETA_2026-09-09.md), #28 0596e78 e contrato candidato 14926fb. D6 documental resolvida por #27.

## Opções
1. Preservar oficiais e concluir D1–D5/gates.
2. Autorizar migração versionada somente após fechar os gates, com mapa físico e comparabilidade.

## Impactos
Split muda rótulos/fiadas: G18/G20 precisam migração e métricas versionadas. S1/C1/G12 integrados não aprovam automaticamente toda matriz CR-B.

## Recomendação
Opção 1 agora. Não usar W0xx como identidade nem inferência TP1 como medição independente.

## Decisão do usuário
PENDENTE — nenhuma aprovação presumida pelo pedido de arquitetura ou merge documental.
D1: 19 casos TGD como vãos ou duas paredes; D2: fonte independente TP1 ou inferência explícita; D3: autorização de escrita/migração; D4: conferência R1/R2/R3 antes da escrita; D5: critério local ou regra geral. D6 já resolvida.

## SHA/PR relacionado
Base de consolidação: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9. [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32),
[#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33), [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35).
Produção candidata citada deve ser lida no SHA correspondente, não na main.
Ao decidir: registrar data, autorização literal, opção, escopo e PR de implementação;
atualizar regra oficial e status no mesmo pacote.
