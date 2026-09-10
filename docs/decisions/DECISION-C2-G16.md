# Unidade física do gate C2/G16
STATUS: PENDING

## Contexto
Mudança de particionamento altera contagem de ROW_MOSTLY_EMPTY sem criar necessariamente vazio novo. Metade resolvida por C1 não aprova o gate.

## Evidência
[Decisão física existente](../CR_C2_DECISAO_FISICA.md): 58 vazios novos por identidade contidos em vazios anteriores; contenção não os torna falsos. GAP_IN_ROW preserva detecção.

## Opções
A. Filtrar faixas fora do grid: cria regra e ainda deixa +7.
B. Reagrupar parede-mãe: retirada na revisão por contradizer CR-B.
C. Manter código e avaliar vazio físico global para o gate.

## Impactos
C altera critério de aprovação e exige autorização, ainda que não mude solver. A/B não são implementação de regra já inequívoca.

## Recomendação
C isolada, preservando detecção de todo vazio real; nenhuma adoção nesta missão.

## Decisão do usuário
PENDENTE — nenhuma aprovação presumida pelo pedido de arquitetura ou merge documental.
Aprovar ou revisar C como critério do gate. Não há autorização de recalibrar arquivos oficiais.

## SHA/PR relacionado
Base de consolidação: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9. [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32),
[#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33), [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35).
Produção candidata citada deve ser lida no SHA correspondente, não na main.
Ao decidir: registrar data, autorização literal, opção, escopo e PR de implementação;
atualizar regra oficial e status no mesmo pacote.
