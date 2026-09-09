# Primeiro ensaio Revit: bancada main-safe

**GO tecnico restrito, conforme relatorio e checklist abaixo.** Nenhuma
instalacao, criacao de RVT ou abertura de Revit foi executada nesta missao.
Escopo: calcular, criar, inspecionar e recriar187 blocos de um unico L.
Nao usar Ajustar Erros, Unir Paredes, Finalizar/Deletar Paredes ou salvar
como modelo construtivo aprovado. A main e o botao normal ficam intactos.

## Identidade e isolamento

Codigo:`8cdd33f974f41a9bf41010a32f82762740b31ed3`, SEM N1.
Pacote ja exportado:
`C:/Users/CIVIX/.codex/artifacts/beta-main-safe-8cdd33f-20260909`.
Manifesto ENGINEERING_CANDIDATE_NOT_BETA_APPROVAL e deliberado: integridade
de bytes nao e aprovacao tecnica. Usar o veredito do relatorio/checkpoint.

Reproduzir para um diretorio NOVO, no checkout desta branch:

```powershell
python tools/beta/build_package.py --head 8cdd33f974f41a9bf41010a32f82762740b31ed3 --output C:/BetaRevit/main-safe-8cdd33f
python -B -c "from beta_package import verify_beta_package; print(verify_beta_package('C:/BetaRevit/main-safe-8cdd33f'))"
```

Instalacao futura em botao pyRevit separado `.pushbutton`, com todos os
arquivos do pacote, nunca sobre o botao de producao. Confirmar no log
`BETA CONTROLADO - pacote offline verificado` e o SHA completo acima.
Manifesto ausente/invalido, hash diferente ou tentativa de fallback: parar.
Usar sessao nova do Revit para o ensaio futuro, sem janelas de modulacao
anteriores; nao abrir o botao normal durante o ensaio do pacote fixo.

## Entrada exata da bancada

Usar copia descartavel de engenharia do RVT, nao central/arquivo de
producao, com backup fechado. Nessa bancada devem existir APENAS duas
paredes de referencia no volume do ensaio, ambas com altura340cm e
espessura14cm, base em nivel de elevacao612cm. Sem portas, janelas,
vinculos, grupos ou dependentes no volume ensaiado. Geometria em cm:

| Origem TP1 | Inicio XY | Fim XY | Comprimento |
|---|---|---|---:|
| indice75, W076 | 7677.25,1567.95 | 7677.25,1636.95 | 69.00 |
| indice81, W082 | 7670.25,1629.95 | 8024.26,1629.95 | 354.01 |

Indices de origem sao base zero. Selecionar75 antes de81 e preservar
orientacao dos endpoints; permutacoes/inversoes nao sao escopo aprovado.

Esta e uma BANCADA DERIVADA das coordenadas TP1, nao substituicao das Walls
nativas. Os campos nativos tem260/280cm; settings do benchmark tem17 fiadas.
Nao alterar aquelas Walls para alegar correcao do projeto. A definicao
uniforme340cm e exclusiva do ensaio isolado e esta explicitamente no
[input de engenharia](checkpoints/evidence/main-safe-engineering-input.json).
Nenhum input/reference/reference_score/baseline oficial foi regravado.

Selecionar somente essas duas referencias pelo fluxo de paredes existentes.
Nao aceitar selecao de projeto inteiro nem dados capturados diferentes.
Registrar ordem, endpoints, unidade/transformacao de coordenadas e IDs.
Usar catalogo fixo B39/B34/B54/B19/C09/C04: dimensoes e celulas devem
coincidir com o input. Blocos altura19cm, junta vertical1cm,17 fiadas.
Familias/tipos reais e celulas ainda precisam de verificacao no beta.
Familia ausente ou dimensao diferente: parar, sem substituicao aproximada.

## Calculo e criacao

1. Conferir SHA,2 eixos,1L,2 pontas livres,zero aberturas,base612cm e340cm
   de altura uniforme. Guardar numericamente a entrada antes de calcular.
2. Calcular sem ajustar geometria. Esperado:17 fiadas,187 blocos,zero
   colisoes/invasoes/trechos nao modulares e auditorias de amarracao verdes.
   Comparar com [resultado completo](checkpoints/evidence/main-safe-handler-bench.json).
3. Preflight sozinho nao aprova amarracao. Divergencia de contagem, codigo,
   posicao, catalogo ou referencia: nao criar; preservar log e recapturar.
4. Criar, registrar IDs e conferir187 instancias com17 indices de fiada.
   Bases fisicas esperadas:613+20*ci cm; alturas19cm,ci0..16. Conferir
   rotacoes, espelhamento/celulas, contato do L e juntas. Nao editar pecas.
5. Recriar SEM alterar entrada: novo lote deve substituir integralmente
   o anterior, sem duplicatas. Registrar IDs antigos/novos e mensagens.
6. Nao finalizar nem excluir referencias neste primeiro ensaio. Referencias
   permanecem como controle; observacoes nao equivalem a aceite construtivo.

## Rollback e parada

Falha de criacao deve reverter o grupo inteiro, incluindo exclusao do lote
anterior. Conferir isso no documento real; testes offline usam dubles.
Rollback nao confirmado bloqueia operacoes: guardar diagnostico, fechar a
copia sem salvar e reabrir o backup. Mesmo apos sucesso, defeito fisico
exige parar e descartar a copia; Undo somente se o estado for confirmado.
Nao salvar por cima do backup, sincronizar ou transferir pecas a producao.

Edicao nativa fora do fluxo, inclusive porta/janela, exige nova captura e
nova validacao. Assinatura do handler nao rastreia toda edicao arbitraria.
O pacote nao tem bloqueio por lista de coordenadas: este escopo depende
da selecao e conferencia operacional. Preflight continua bloqueando volume
invalido, mas nao certifica outro recorte. Nao ampliar o ensaio por conta
de uma selecao diferente passar no OBB.

## Evidencias para reproducer

Guardar manifesto/SHA, versoes Revit/pyRevit/Python, RVT de bancada e backup,
input numerico real, nivel/base, alturas, espessuras, endpoints/transformacao,
familias/tipos/dimensoes/celulas e IDs/UniqueIds. Guardar log completo da
tela (Copiar log e caminho de log mostrado), excecao/InnerException,
acao imediatamente anterior, tempo e estados de transacao observados.
Relacionar cada instancia a parede/fiada/codigo/posicao e fotografar vistas
com cotas. Screenshot nao substitui entrada numerica e IDs.

O [comando de replay do handler](checkpoints/evidence/main-safe-handler-bench-run.json)
reproduz a bancada offline. Para erro real, criar OUTRO input de engenharia
com os dados capturados, preservando o fixture e o resultado anterior.
Nao ha exportador automatico universal de falhas Revit nesta entrega;
sem captura suficiente, interromper antes de repetir ou alterar o modelo.
