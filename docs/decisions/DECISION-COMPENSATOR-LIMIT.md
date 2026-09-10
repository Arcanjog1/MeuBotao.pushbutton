# Limite de compensadores
STATUS: PENDING

## Contexto
Teto quantitativo e proibição de sequência são contratos distintos. N1e intercala peças, sem aprovar relaxamento de teto.

## Evidência
[Auditoria histórica §8](../AUDITORIA_BETA_2026-09-09.md) e candidata #31 5658e9c; asserção TGD compensators 52→66 no 09b6ea0. Contagem é de paredes reprovadas.

## Opções
1. Manter regra vigente e revisão dos casos sem solução.
2. Tornar teto preferencial mantendo proibição de sequência.
3. Alterar preferência por B34/B19 condicionado, mediante contrato específico.

## Impactos
Mudar teto altera aceitação física e pode exigir recalibração autorizada. Intercalar preserva composição; não garante amarração nem reduz contagem.

## Recomendação
Para beta limitado, manter regra vigente. Separar futura decisão de teto da adjacência; não liberar B19 TIE ou K>1 por inferência.

## Decisão do usuário
PENDENTE — nenhuma aprovação presumida pelo pedido de arquitetura ou merge documental.
Escolher política quantitativa e de sequência, escopo e exceções, se desejar mudança. Até lá preserva-se contrato oficial.

## SHA/PR relacionado
Base de consolidação: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9. [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32),
[#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33), [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35).
Produção candidata citada deve ser lida no SHA correspondente, não na main.
Ao decidir: registrar data, autorização literal, opção, escopo e PR de implementação;
atualizar regra oficial e status no mesmo pacote.
