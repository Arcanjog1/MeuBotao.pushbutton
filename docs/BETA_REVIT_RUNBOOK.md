# Runbook condicionado do primeiro beta Revit

**NAO EXECUTAR AINDA: NO-GO em2026-09-09.** Este roteiro define a fronteira
operacional depois de outro checkpoint confirmar todos os gates. Nao aprova
W019, TGD, TP1 completo ou os recortes L/T/X testados.

## Pacote imutavel

Codigo de engenharia: `09b6ea0ae221a43a3adc27f63bb05d336351584f`.
O pacote foi exportado dos objetos Git, nao de arquivos locais soltos.
Nao instalar esta versao no botao de uso normal nem substituir a main.
Reproduzir a exportacao para um diretorio NOVO, usando Python disponivel:

```powershell
python tools/beta/build_package.py --head 09b6ea0ae221a43a3adc27f63bb05d336351584f --output C:/BetaRevit/engenharia-09b6ea0
python -B -c "from beta_package import verify_beta_package; print(verify_beta_package('C:/BetaRevit/engenharia-09b6ea0'))"
```

O destino e exemplo, nao instalacao executada. Pacote local efetivamente
gerado: `C:/Users/CIVIX/.codex/artifacts/beta-revit-09b6ea0-20260909`.
O loader exige manifesto completo e hashes de Script/verificador/todos os
modulos core, recusa bytecode inesperado e nao cai no download online.
Manifesto tem status ENGINEERING_CANDIDATE_NOT_BETA_APPROVAL.

## Condicoes de entrada

1. Checkpoint posterior com GO, SHA completo, recorte por coordenadas/chaves,
   lista de nos/aberturas, testes finais e catalogo suportado.
2. Copia descartavel e estatica do RVT, com backup fechado fora do fluxo de
   trabalho. Nunca arquivo de producao, central ou sincronizacao compartilhada.
3. Registrar versao/build Revit, pyRevit/Python, unidade, nivel/base, altura,
   espessuras, orientacao e familia/tipo/celulas dos seis codigos suportados.
4. Instalar separadamente somente o pacote aprovado; conferir SHA mostrado.
   Nao reaproveitar pacote anterior nem autorizar fallback para main.
5. Capturar o recorte completo e recalcular. Mudanca nativa fora do fluxo
   exige recaptura: assinatura nao detecta toda edicao arbitraria de abertura.
6. Exportar entrada/saida diagnostica e conferir preflight. Qualquer erro,
   colisao ou invasao bloqueia o lote inteiro; nao existe bypass para continuar.
7. Verificar amarracao/cobertura/catalogo independentemente: preflight OBB
   sozinho nao aprova prismas, compensadores, contravergas ou suporte construtivo.

## Criacao e finalizacao

Criar somente apos os gates anteriores. Substituicao do lote e grupo atomico:
limpa o lote anterior, cria novo, verifica cada instancia e so publica sucesso
apos commit confirmado. Contagem igual nao basta; correspondencia por
candidato/fiada e IDs distintos tambem e exigida.

Nao editar/excluir manualmente blocos entre Criar e Finalizar. Conferir
visualmente orientacao/celulas, Z por fiada, volumes das portas/janelas,
amarração, encontros e referencias retidas. Parede total ou parcialmente
nao modulavel deve permanecer identificada para revisao manual. Se o recorte
depende de uma peca nao suportada, parar ou manter fora do escopo aprovado.

Finalizar remove referencias elegiveis; antes confirmar que Document.Delete
nao levara dependentes necessarios do modelo. Isso e verificacao B real,
nao coberta integralmente pelos dubles. No primeiro beta, preservar a copia
pre-finalizacao e nao salvar por cima dela. Falha/estado inesperado: parar.

## Rollback

- Falha de criacao: o grupo externo deve restaurar o lote anterior. Conferir
  a mensagem de rollback e os IDs; ausencia de excecao nao comprova restauracao.
- Rollback nao confirmado: handler fica bloqueado. Nao tentar continuar,
  finalizar ou salvar o arquivo como valido; guardar diagnostico e reabrir backup.
- Mesmo apos sucesso, comparacao fisica reprovada: usar Undo do grupo se
  confirmado no Revit, ou fechar a copia sem salvar e reiniciar pelo backup.
- Nunca corrigir o resultado em silencio para gerar evidencia de sucesso.

## Evidencia para reproducer offline

Guardar SHA/manifesto, hash do input, geometria em cm e unidade original,
origem CAD/RVT, chaves e coordenadas das paredes, nos/contatos, aberturas
(t inicial/final, peitoril, topo), base/altura, catalogo/celulas e todos os
indices de fiada fisica. Guardar relatorio completo de preflight, motivos
de retencao, candidatos/placement_reason/node_index, IDs/UniqueIds de
referencias e instancias, estados/retornos de transacoes, excecao/stack,
tempos e acao imediatamente anterior. Anexar vistas com coordenadas e
fiadas, sem usar apenas screenshot como substituto do input numerico.

O log atual traz diagnostico de solver/preflight/retencao e perf; metadados
do documento/familias/UniqueIds e input devem ser exportados/conferidos no
procedimento. Nao foi implementada captura automatica universal de falhas
Revit. Sem evidencia numerica suficiente, interromper e capturar antes de
repetir. Nenhum Revit foi iniciado para produzir este roteiro.
