# Beta main-safe: candidato independente da cadeia N1

Data:2026-09-09. **GO TECNICO RESTRITO ao ensaio de bancada definido aqui.**
Nenhum Revit foi iniciado. Este documento complementa, sem substituir,
o [relatorio integral do #31](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/73cbf08b4584f2e952e17a444ed88a99f9df5498/docs/RELATORIO_BETA_2026-09-09.md).

## 1. Estado inicial reconstruido

Main inicial08495d9, agoraaa58d70d84c6134216f8f15a131edf060c4dce81,
apos merge autorizado do #32. #30 esta contido no #31. #31 permanece
draft, sem merge, codigo09b6ea0 e documentacao73cbf08. O principal alvo
da missao e primeiro beta controlado, nao integrar N1 a qualquer custo.

## 2. Trabalho executado

Depois da auditoria, das correcoes e da consolidada N1, foram resolvidos
recortes novos, nao recortada visualmente a geometria do projeto inteiro.
Um L com as paredes fonte75/81 passou em todas as verificacoes offline.
Foi criada esta branch diretamente da main, transportando somente
protecoes beta, seus testes e ferramentas de evidencia/empacotamento.
Nenhuma alteracao preexistente dos checkouts originais foi removida.

## 3. Causas-raiz encontradas

A cadeia N1 corrige sobreposicoes longitudinais de nos, mas cria novas
regioes de colisao TGD em pares com geometria de entrada conflitante.
Eliminar saldo global nao aprova esses pares. Juntas/fases e composicoes
de outros recortes tambem dependem de contratos ainda nao autorizados.
Um ensaio de criacao menor pode evitar esses componentes SEM transportar
a regressao N1 e SEM mudar a norma. Isso nao resolve o projeto inteiro.

## 4. Correcoes implementadas

Tres arquivos de producao diferem da main: Script.py, beta_package.py e
nuvem/core/wall_modeling.py. O motor nuvem/core/engine, benchmark e testes
legados de ARM/G12 sao identicos a main. wall_modeling acrescenta registro
de retencao ao resultado, sem alterar candidatos geometrizados.

Preflight por volume/fiada ativa recusa invasoes, colisoes, NaN e geometria
invalida antes de apagar/criar. Paredes vazias/parciais/incompletas mantem
referencias. Substituicao atomica confere commits, IDs e correspondencia
por candidato/fiada. Assinatura exige calculo atual; refresh nao suportado
exige recaptura. Pacote por SHA/hashes nao usa main/cache variavel.
Os mesmos arquivos de protecao do09b6ea0 foram transportados sem edicao.

## 5. Hipoteses rejeitadas

Nao transportar N1 sob a justificativa de recorte limpo: falharia gate1
global do candidato. Nao trocar fases T, liberar B19 fechado, aumentar
tetos/tolerancias, corrigir entrada oficial ou esconder achados. As
hipoteses fisicamente rejeitadas L163/T95/T138 e enumeracoes permanecem
no relatorio integral do #31. Selecoes0/10,12/20,35/41/49/52/57 e75/76/81
tambem nao foram aprovadas. A nova candidata nao equivale a nenhuma delas.

## 6. Deltas fisicos por identidade

Nao ha mudanca de formula geometrica em relacao a main. O recorte75/81
produz187 blocos, um L, duas pontas livres, nenhum trecho nao modular,
auditorias brutas aprovadas e zero achados com referencia oficial.
[Solve completo](checkpoints/evidence/main-safe-region-final.json) e
[avaliacao](checkpoints/evidence/main-safe-region-final-scored.json).
Proveniencia:285 arquivos de engine/benchmark e30 arquivos de testes
originais sao identicos byte a byte; os3 arquivos de protecao coincidem
com o donor09b6ea0. AST do wrapper de solve coincide com main exceto os
retornos pelo registrador de retencao. [Prova](checkpoints/evidence/main-safe-provenance.json).

## 7. Aberturas

O recorte escolhido NAO possui aberturas. Nao e validacao real de portas,
janelas, vergas, contravergas ou canaletas. Casos sinteticos de preflight
continuam cobertos pelos testes. Main conserva as500 invasoes espaciais
ativas TP1 e697 TGD do censo anterior; o recorte completo nao esta liberado.
O preflight bloqueia o lote, nao remove pecas para parecer corrigido.

## 8. Colisoes

Recorte:zero. Os +37 agregados/+58 fisicos pertencem a cadeia N1 que NAO
esta nesta branch. Main conserva726 pares fisicos TGD e18 TP1, conhecidos
e fora do ensaio. Nao declarar correcao desses defeitos; preflight deve
bloquear selecoes que os contenham. Detalhes por identidade no relatorio31.

## 9. Paredes vazias

Recorte:zero paredes vazias/parciais e zero trechos nao modulares. Protecao
geral preserva referencias com motivos. Casos197,943cm e99,754cm foram
testados; nao houve truncamento ou alteracao de input. Retencao nao
certifica cobertura vertical de paredes nativas de alturas diferentes.

## 10. Encontros L/T/X

Um L efetivamente presente e verificado; nenhum T/X pertence ao escopo.
Geometria exata em cm: fonte75 `[7677.25,1567.95]->[7677.25,1636.95]`,
69cm; fonte81 `[7670.25,1629.95]->[8024.26,1629.95]`,354,01cm; t14.
Nao usar apenas nomes W076/W082, que podem ser renumerados. A ponta que
se ligava a outra parede no plano completo agora e livre: escopo diferente.

## 11. Amarracao e juntas

Auditorias brutas e todos os validadores, com referencia oficial, passaram
no recorte. O caminho de extensao usado por paredes existentes tambem foi
conferido:13/14/17 fiadas dao143/154/187 blocos, sem achados ou colisoes.
[Experimento de fronteira](checkpoints/evidence/main-safe-ui-boundary-run.json).
Execute_solve do handler com bancada uniforme340cm tambem reproduziu
exatamente paredes/blocos/catalogo, preflight e assinatura validos:
[replay](checkpoints/evidence/main-safe-handler-bench-run.json).
Eixos com Z real612cm conservaram exatamente a mesma geometria fisica:
[controle de cota](checkpoints/evidence/main-safe-native-z.json).
Nao e prova global de invariancia sob permutacao/inversao de endpoints.

## 12. Compensadores

Zero achados no recorte; nenhum teto/composicao foi relaxado. N1e nao foi
transportado, nem seus ganhos de ordenacao. Conflitos normativos do
projeto inteiro continuam pendentes e nao sao resolvidos por este ensaio.

## 13. Performance

Solve focal e pequeno (aproximadamente0,1 a1,1s nos probes, concorrentes
com outros testes); nao e benchmark de ganho. N1f/cache novo nao foi
transportado. A consolidada usa4 workers e registra as20 maiores duracoes.
Consolidada3021,98s contra2611,63s da cadeia N1, com arvores e conjuntos
de testes diferentes: nao interpretar como benchmark controlado de ganho
ou regressao das protecoes. Maior teste:T18 de corpus,1140,11s. O motor e
identico a main e o wrapper so acrescenta registro linear de retencao,
sem nova busca/rebuild. Nenhuma otimizacao foi introduzida para mascarar
o tempo;50min21s e custo offline observado, nao tempo esperado da bancada.

## 14. Testes

Controles iniciais:331 passed em112,95s (quatro arquivos beta e
test_script.py, antes do commit; mesmos arquivos no SHA final). Novo
teste do recorte passou em0,61s. Consolidada no SHA abaixo:
**1027 passed,2 failed em3021,98s (50min21s)**, wrapper3025,078s, exit1.
Inicio17:32:04 UTC, PID25596, timeout5400s; concluida normalmente.
Comando:`python -m pytest -n 4 --dist loadfile -q --durations=20`.
[Metadados](checkpoints/evidence/main-safe-consolidated.json),
[log](checkpoints/evidence/main-safe-consolidated.txt).
As duas falhas sao `test_projeto_nao_regrediu_contra_o_baseline` para
TGD (compensators52->61) e TP1 (JUNCTION_MISSING_BINDING8->9).
Coincidem com o [replay independente da main](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/73cbf08b4584f2e952e17a444ed88a99f9df5498/docs/checkpoints/evidence/beta-baseline-replay.json).
Nao houve falha adicional; INSIDE_DOOR0->7 e compensators66 da cadeia N1
nao pertencem a esta candidata. As falhas antigas continuam reais, fora
do recorte; nao foram transformadas em PASS nem removidas do benchmark.
Nenhum baseline, skip, xfail ou threshold foi alterado. Os testes N1 nao
foram transportados porque o mecanismo N1 nao existe nesta candidata;
todos os testes da main foram preservados, inclusive os controles ARM/G12.
Governanca:16 testes passaram em25,589s, wrapper26,094s;
[log completo](checkpoints/evidence/main-safe-governance-tests.txt).

## 15. CI

#31/73cbf08: checks documentais verdes34383983344/34383985595, nao solver.
Esta branch esta no [PR #34 draft](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/34).
No HEAD documentalee2250a6284981d2f2f97fc8f09389ffff6d2315, os checks
[push](https://github.com/Arcanjog1/MeuBotao.pushbutton/actions/runs/34389067319/job/102592599010)
e [PR](https://github.com/Arcanjog1/MeuBotao.pushbutton/actions/runs/34389092291/job/102592682319)
passaram. [Snapshot](checkpoints/evidence/main-safe-github-publication.json).
O commit seguinte registra esses links, sem alterar codigo/testes8cdd33f.
Verde documental nao substitui consolidada nem fisica. #34 nao foi mesclado.

## 16. Documentacao e governanca

Main reconciliada por fetch, regras na fonte unica secao48, checkpoint
proprio, procedimentos e artefatos com SHA. Relatorio31 continua acessivel
no commit fixo73cbf08. Inputs/referencias/scores/baselines oficiais nao
foram regravados. Pacote e engenharia, nao instalacao nem assinatura
criptografica. O probe inicial registraaa58d70 como HEAD mas foi rodado
na arvore com protecoes ainda nao commitadas; somente o probe FINAL e
evidencia do8cdd33f. Isso nao e execucao limpa da main sem protecoes.

## 17. Dividas nao bloqueantes

**B:** comportamento Revit/pyRevit, familias/celulas/orientacao, desempenho
de criacao e rollback real, somente no futuro ensaio descartavel.
**D:** solver completo, otimizacao global, testes amplos de permutacao.
**C fora do escopo:** eixos sobrepostos TGD, fase coordenada T, tetos,
fora de modulo, CR-B/C2/G16. Nenhuma aprovacao implicita dessas regras.
**A fora do recorte:** defeitos fisicos conhecidos impedem ampliar beta
ou integrar #31. Nao sao dividas liberadas para producao.

## 18. Decisoes do usuario

O agente selecionou a alternativa reduzida dentro da autonomia de escolher
o primeiro recorte. NAO decidiu que duas paredes TGD sao a mesma unidade,
nem mudou regras. Essas decisoes permanecem necessarias para os componentes
bloqueados, mas nao precisam impedir uma bancada sem eles. Merge deste
novo draft nao esta autorizado pela permissao especifica de31/32.

O ensaio usa uma copia de engenharia com APENAS os dois eixos e altura
UNIFORME. Os campos nativos do fixture dizem260/280cm, mas settings pede
17 fiadas: nao alegar equivalencia dessas alturas. O runbook escolhe uma
bancada explicita340cm/17 fiadas, nao correcao das Walls nativas. Nao criar
as17 fiadas sobre as duas Walls nativas e declara-las substituidas.
[Entrada separada de engenharia](checkpoints/evidence/main-safe-engineering-input.json).

## 19. SHA exato da versao candidata

**8cdd33f974f41a9bf41010a32f82762740b31ed3**.
Tree:`d835bdbb5092ac7d472502525434126c730a17e6`.
Branch:`codex/beta-main-safe-20260909`, baseaa58d70, PR#34 draft.
Pacote:`C:/Users/CIVIX/.codex/artifacts/beta-main-safe-8cdd33f-20260909`.
[Build](checkpoints/evidence/main-safe-package-build.json) e
[verificacao](checkpoints/evidence/main-safe-package-verify.json) passaram.
Nao instalar sobre o botao normal; manifesto continua ENGINEERING_CANDIDATE_NOT_BETA_APPROVAL.

## 20. GO/NO-GO para beta Revit

**GO TECNICO RESTRITO**, exclusivamente para criacao/recriacao observada
dos187 blocos da bancada
uniforme75/81, sem aberturas, em copia descartavel. Nao liberar TP1/TGD
inteiros, alturas heterogeneas, outras regioes, ajustes automaticos,
uniao de paredes, Finalizar/exclusao de referencias ou merge#31.
Gates por evidencia, sem aprovar a suite inteira como verde:

| Gate | Resultado e limite |
|---|---|
| 1 | Sem regressao critica nova conhecida versus main: motor/benchmark identicos, testes originais intactos e somente as duas falhas antigas na consolidada |
| 2 | Bancada sem aberturas; preflight bloqueia invasao de qualquer abertura capturada antes de mutacao. Nao certifica portas/janelas reais |
| 3 | Zero colisoes na bancada; +37 TGD explicado no31, mecanismo N1 nao transportado. Projetos completos seguem bloqueados |
| 4 | Zero nao-modulares na bancada; referencias vazias/parciais/incompletas retidas por codigo/testes; nenhuma exclusao de referencia neste ensaio |
| 5 | Um L e amarracao passaram em auditorias e validadores com referencia. Nenhum T/X no escopo |
| 6 | Focados verdes; consolidada8cdd33f executada,1027 passed/2 falhas antigas classificadas |
| 7 | SHA completo fixo, pacote exportado e hashes verificados |
| 8 | Copia descartavel/backup, grupo atomico e parada em rollback nao confirmado; procedimento definido, API real a verificar no beta |
| 9 | Input de bancada e replay numerico completos; log/IDs/familias/metadados reais exigidos pelo runbook, sem alegar exportador universal |

Procedimento:[runbook](BETA_MAIN_SAFE_RUNBOOK.md). Publicacao/CI documental
registrados na secao15 e checkpoint. Nao iniciar Revit nesta missao.
