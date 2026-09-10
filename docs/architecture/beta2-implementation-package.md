# Próximo pacote de implementação
STATUS: PROPOSTA — depende das decisões e de autorização do próximo objetivo.

Objetivo recomendado: **fechar a validação do Beta 1 e entregar contratos
versionados de catálogo/reforço com uma primeira estratégia em recorte controlado**.
Não começar por N1, CR-B ou troca de baseline.

## Dependências e entregas pequenas

| Etapa | Entrada/gate | Entrega | Aceitação |
|---|---|---|---|
| 0. Recuperação Beta 1 | Branch/SHA posterior a a5081d8 e logs | Proveniência fixa e ensaio síncrono Revit, quando autorizado | Executar runbook em cópia, confirmar rollback e resultado; PASS só com prova real |
| 1. Contratos offline | Aprovação dos [ADRs](../decisions/README.md) relevantes | DTOs/versionamento, catálogo lógico, parser e validação, adaptador legado | Nenhuma mudança de resultado legado; serialize/replay estáveis |
| 2. Mapping/preflight | Tipos e capacidades aprovados | Detecção/seleção/mapping, erros antes do solve | Família errada/ausente/corte inválido bloqueia explicitamente |
| 3. Planejador A | Política de apoio/comprimento/simetria aprovada | Reservas e peças dedicadas em subfaixas de 9 cm | Porta/janela, sem tipo viável, nó/jamba, catálogo discreto, transição |
| 4. Planejador B | Apoio/corridas/grade/cortes de B aprovados | CHANNEL por faixa de 19 cm, composição e união de demandas | Vãos vizinhos, lacuna que impede união, extremidade, U/J, conflitos |
| 5. Integração comum | Itens A do backlog no recorte resolvidos | Solver/rebuild/cross-band consumindo plano imutável | Sem perda de amarração, invasão, parede silenciosa, dupla contagem |
| 6. UI/criação Beta 2 | Gates offline e versão fixada | Escolha anterior ao cálculo, captura/hash, criação/rollback | Família real, pose/cotas, quantidade, retenção e recriação verificadas |

Recomendação de sequência A→B reduz risco da união de corridas, mas é revisável;
não é autorização para implementar A nesta missão. TOP_BOND_BEAM independente
fica fora até decisão. Graute/armadura e cálculo estrutural não fazem parte
do primeiro pacote geométrico.

## Matriz mínima de testes futura

- Contrato: unidades/datum/eixos invertidos, round-trip, mapping sem objetos Revit.
- Geometria: porta e janela, peitoril divergente, faixa de 9/19, largura positiva,
  extremos/nós L/T/X, overlap 3D, abertura atravessando outra parede.
- Catálogo: comprimentos discretos/variáveis, HEIGHT_CUT versus LENGTH_CUT,
  corte combinado proibido, célula removida, deitado, U/J e tipo VEDAÇÃO.
- Reforços: duas demandas compartilham uma peça/corrida sem dupla contagem;
  corrida descontínua não ganha apoio pelo envelope.
- Amarração: same-band e cross-band, todas as fiadas físicas do recorte,
  sem somar A/B como volumes coexistentes.
- Determinismo: ordem permutada, cache on/off, replay de configuração,
  invalidação por catálogo/mapping/cota; comparador por identidade física.
- Integração: referência parcial retida, assinatura antiga recusada,
  falha no meio da criação restaura recorte, reexecução não duplica peças.

Testar mínimo → módulo → regressão pertinente → suíte no SHA final quando
houver alteração física. Congelar árvore/log/ambiente durante a execução.
Separar teste de contrato de medição no Revit; usar referência humana com
limites e sem regravar benchmark oficial.

## Fora do pacote inicial

Refatoração N1, C2, migração CR-B, recalibração oficial, tolerância global nova,
mistura de estratégias por abertura, cinta universal e recuperação cega de
todos os scripts antigos. As dívidas não justificam omitir falha crítica
no recorte escolhido.
