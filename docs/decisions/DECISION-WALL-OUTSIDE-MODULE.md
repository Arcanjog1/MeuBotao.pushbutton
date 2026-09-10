# Parede fora do módulo
STATUS: PENDING

## Contexto
197,943 cm permanece sem blocos no diagnóstico; 99,754 cm depende de reservas/nós. Não é resolvido por arredondamento global.

## Evidência
[Auditoria §5](../AUDITORIA_BETA_2026-09-09.md) e #31, retenção parcial em 09b6ea0 (candidato).

## Opções
1. Recusar geração e manter parede visível para revisão.
2. Preencher módulo inferior e declarar folga residual por contrato de fronteira.
3. Ampliar tolerância global.

## Impactos
A opção 2 requer localizar folga e validar cobertura/amarração; a 3 pode mascarar invasão, junta ou erro de captura. Retenção técnica não aprova geometria incompleta.

## Recomendação
Opção 1 para beta; não ampliar tolerância. Decisão não impede arquitetura nem recorte comprovadamente modular.

## Decisão do usuário
PENDENTE — nenhuma aprovação presumida pelo pedido de arquitetura ou merge documental.
Aprovar política de residual apenas se mudar a recusa vigente; indicar folga máxima, posição e tratamento construtivo.

## SHA/PR relacionado
Base de consolidação: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9. [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32),
[#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33), [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35).
Produção candidata citada deve ser lida no SHA correspondente, não na main.
Ao decidir: registrar data, autorização literal, opção, escopo e PR de implementação;
atualizar regra oficial e status no mesmo pacote.
