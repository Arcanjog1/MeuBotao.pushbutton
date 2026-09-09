# Preparacao do beta Revit: relatorio tecnico

Data: 2026-09-09. **NO-GO para lancamento desta cadeia e merge #31.**
Consolidada concluida na secao 14. A missao chegou a GO RESTRITO em uma
alternativa separada da main, SEM N1, no [PR #34](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/34).
Isso NAO libera a cadeia #31. O ensaio34 e bancada uniforme340cm75/81,
nao as Walls nativas260/280cm nem TP1/TGD completos.

## 1. Estado inicial reconstruido

Main inicial `08495d913e72b36a80b034d5f0a1435470d27557`; candidato
#31 `05030d2cf3e18081b040ad048759099a1b215210`, producao/testes iguais a
`420dbcc`/`439fd49`. A cadeia N1 (#30, `626087b`) esta integralmente no
#31, seguida por N1b (`67083b0`), N1c (`cb70224`), N1e (`190fd6e`),
N1f (`03942b4`) e documentacao/resultados. Nao integrar #30 separadamente.
Reconstrucao dos demais PRs e normas na [auditoria inicial](AUDITORIA_BETA_2026-09-09.md).

## 2. Trabalho executado

Worktrees isoladas preservaram os dois checkouts originais sujos. Foram
revisados os PRs, executados censos completos por etapa, instrumentados
pares fisicos/aberturas, reconstruidas auditorias de amarracao, testados
recortes com novo solve, rejeitadas hipoteses locais/globais e implementadas
contencoes beta. O #32 foi integrado apos revisao independente e autorizacao;
nenhum outro PR foi integrado. Revit nao foi iniciado.

## 3. Causas-raiz encontradas

- Medicao agregada misturava templates A/B, bandas e alturas de porta inativas.
- A busca restrita a parede dona/secundaria perdia invasores de outra parede.
- Nos independentes disputam volumes de paredes geometricamente sobrepostas;
  corrigir a disputa longitudinal nao resolve a interpenetracao transversal.
- Reservas de X e ponta se cruzam na parede real de 99,754cm; nao e o caso livre.
- Finalizar confundia algumas pecas criadas com substituicao integral da parede.
- Substituicao do lote anterior nao era atomica; retorno de Commit nao era conferido.
- Geometria invalida ou calculo desatualizado podia chegar a criacao sem bloqueio beta.

## 4. Correcoes implementadas

Preflight beta por fiada fisica e cota ativa: OBB de todas as aberturas e
pecas proximas, inclusive mesmo no e outra parede; bloqueia o lote inteiro
antes de mutacoes. Usa tolerancia existente de colisao (0,1cm), sem mudar
validadores oficiais. Valida finitude, dimensoes, eixos e correspondencia.

Paredes vazias, parcialmente nao modulares ou incompletamente criadas mantem
referencia identificada por coordenadas/motivo no resultado, log e UI.
Criacao beta atomica engloba exclusao anterior, criacao e realce; exige
estados de transacao, correspondencia candidato/fiada, IDs distintos e
instancias existentes. Rollback nao confirmado bloqueia novas operacoes.

Assinatura exige novo calculo apos mudanca da geometria capturada, aberturas,
catalogo, nivel/base ou altura. Refresh beta rejeita referencia ausente e
deslocamento/rotacao/cota nao suportados. Nao rastreia toda edicao nativa de
porta/janela: o beta exige copia estatica e recaptura apos edicoes externas.
Pacote offline por SHA/hashes nao faz fallback para main variavel.

## 5. Hipoteses rejeitadas

O antigo room-zero para no dentro da porta permanece rejeitado: transferia
defeitos para amarracao e cobertura. Giro local A/B de L163/L185 nao elimina
as colisoes; colocar ambas na parede B elimina o par local, mas perde
alternancia e invade portas. No solve completo L163 both-b: blocos
11837->11813, pares fisicos 784->775, invasoes 692->698, GAP_IN_ROW +6,
MISSING_ROW +8, PARTIAL_WALL +2. Rejeitado, nao integrado.
[Resultado completo](checkpoints/evidence/beta-corner163-full.json) e
[validacao com referencia](checkpoints/evidence/beta-corner163-full-scored.json).

As escolhas locais v2 usam o threshold existente de 0,1cm e confirmam o
mesmo resultado; v1 tinha 0,01cm apenas no diagnostico de pecas minimas.
Nao substituir esses experimentos por suposta prova de impossibilidade global.

## 6. Deltas fisicos por identidade

| Projeto | Blocos main->N1f | Colisoes agregadas | Pares por fiada fisica | Invasoes espaciais ativas |
|---|---:|---:|---:|---:|
| TGD | 11749->11837 | 1160->1197 | 726->784 | 697->692 |
| TP1 | 19572->19647 | 14->0 | 18->0 | 500->500 |

TGD: 322 pares-pecas-fiadas adicionados e 264 removidos, saldo +58.
Ha novas regioes reais, nao apenas nova classificacao. Identidades, nos,
origens, codigos, fiadas e WKT em [delta](checkpoints/evidence/beta-tgd-collision-delta.json)
e [regioes](checkpoints/evidence/beta-tgd-collision-regions.json).
Nao somar achados de validadores como se fossem defeitos fisicos distintos.

## 7. Aberturas

TP1: 2094 e a leitura agregada ingenua, nao 2094 instancias invadindo portas
ativas. A leitura fisica restrita a dono/secundaria encontra 412; a espacial
encontra 500, incluindo 88 OPENING_REPAIR_FILL de outras paredes. Todos os
500 eventos medidos sao portas de peitoril relativo zero, nao janelas.
O percentual historico de 68% STANDARD_FILL nao descreve esse conjunto fisico.

W019 tem coordenadas reais `[8017.26,547.95]->[8017.26,1926.95]`, t14.
A chave com 8017.3 era arredondamento historico; o grid do benchmark pode
usar 8017.5. Na porta t564..750, B54 main t715..769 vira B34 t715..749
no candidato, em ci0/2/4/6/8/10/12: invasao antiga, nao corrigida. As outras
493 identidades-fiadas espaciais permanecem. W019 NAO e recorte liberado.

Preflight final: [TGD bloqueado](checkpoints/evidence/beta-preflight-final-tgd.json)
e [TP1 bloqueado](checkpoints/evidence/beta-preflight-final-tp1.json).
Janelas/cotas sao cobertas por testes sinteticos, sem alegar validacao de
familias reais. Contravergas/canaletas/cortados nao suportados continuam
limitacao explicita, nunca promessa de suporte completo.

## 8. Colisoes

| Etapa TGD | Agregadas | Fisicas |
|---|---:|---:|
| main | 1160 | 726 |
| N1 | 1180 | 764 |
| N1b | 1180 | 764 |
| N1c | 1196 | 782 |
| N1f, incluindo N1e | 1197 | 784 |

O saldo agregado +37 e **+132 nos quatro pares que aumentam, -95 nos
dez pares que zeram**. O saldo fisico +58 e +156/-98 nos mesmos grupos.
Nao sao apenas37 pares novos. Pares de maior risco:

| Paredes | Agregado main->N1f | Fisico main->N1f | Origem |
|---|---:|---:|---|
| 12/13 | 16->32 | 16->34 | N1 |
| 31/36 | 169->269 | 154->274 | N1; ultimo incremento N1e/f |
| 86/98 | 8->16 | 8->17 | N1 |
| 99/109 | 0->8 | 0->9 | N1c |
| 88/112 | 8->8 | 9->9 | Zera em N1 e reaparece em N1c; saldo final zero |

Os dez pares zerados: 0/0,7/12,8/69,10/74,13/22,25/25,35/35,38/38,
88/88,109/109; [censo por etapa](checkpoints/evidence/beta-tgd-stages.json).
O passo N1e/f acrescenta area 5,032cm2 em cada uma das ci8/10, sem area
removida nesse passo. Cache nao muda a geometria. Nao absolver N1e por saldo.

Na entrada oficial exata, paredes 31/36 de 14cm tem eixos separados por
12,742cm: faixa sobreposta 1,258cm; 12/13 tem separacao 13,254cm e faixa
0,746cm por 642cm. Nao sao exatamente 13cm/1cm como arredondamentos antigos.
Intersecao de paredes nao e automaticamente defeito num L/T; nesses pares
paralelos ela evidencia uma ambiguidade de duas unidades fisicas ocupando
a mesma faixa. Nao escolher qual eixo apagar/mover por conta propria.
[Geometria exata e vazios subtraidos](checkpoints/evidence/beta-wall-geometry-conflicts-v2.txt).

## 9. Paredes vazias

TGD tem 29 paredes totalmente vazias; TP1, zero. Isso nao conta paredes
parcialmente nao modulaveis, agora tambem retidas. Caso 197,943cm recusa
o modulo pela tolerancia vigente; nao foi truncado para 194cm.

Parede real 97: `[1813.625,-244.618]->[1807.181,-145.072]`, 99,75435455cm.
Grafo completo: AMBIGUOUS135, FREE_END160, X265/272. Trecho final
87,134739->84,548304cm = -2,586435cm, alem de primeiro trecho fora do modulo.
O recorte de tres paredes altera a reserva da ponta e nao reproduz o caso.
Testes de retencao usam o grafo completo. Nenhuma peca foi inventada para preencher.

## 10. Encontros L/T/X

T139/162 nas paredes 86/98: C09/C09 sobrepoe 6,9109cm; mesmo C04/C04
mantendo contatos sobrepoe 3,2464cm. Inverter fases desses elementos iguais
nao resolve. L163: C04 em 99 colide com T181; B34/C09/C04 em 109 invadem
porta99. L185: todas as alternativas minimas em 88/112 invadem porta;
as de 112 tambem colidem. Provas locais com vizinhos fixos, nao UNSAT global.
[Minimos T](checkpoints/evidence/beta-incoming-minimum-footprints.txt),
[L163](checkpoints/evidence/beta-corner163-volume-choices-v2.json),
[L185](checkpoints/evidence/beta-corner185-volume-choices-v2.json).

Recortes com solve novo: TP1 indices35/41/49/52/57, 922 blocos, 3T/1X;
75/76/81, 245 blocos, 2L. Ambos passam OBB, mas nao todos os validadores.
O T/X tem 25 PRISM_STAGGER, 38 CONSECUTIVE, 43 EXCESS, 10 STRIP e duas
contravergas ausentes; L tem 5 PRISM_STAGGER, 3 EXCESS e 1 STRIP.
Com referencia oficial, acrescentam respectivamente 3 e 1 COMP_AVOIDABLE.
Os probes iniciais executavam todos os validadores registrados, mas sem
esse contexto de referencia. Nao considerar esses dois recortes aprovados.

Recortes adicionais: 0/10 ainda tem12 CONSECUTIVE,10 EXCESS,2 STRIP e3
contravergas ausentes;12/20 tem9 EXCESS e3 STRIP, ambos com2 AVOIDABLE.
O recorte75/81 (um L, duas pontas livres, sem aberturas) tem187 blocos e
ZERO achados, inclusive com referencia oficial e auditorias brutas.
[Solve](checkpoints/evidence/beta-region-corner75.json) e
[validacao](checkpoints/evidence/beta-region-corner75-scored.json).
Isso nao elimina as regressoes globais desta cadeia. Motivou uma candidata
SEPARADA da main, sem N1, em `codex/beta-main-safe-20260909`, codigo
`8cdd33f974f41a9bf41010a32f82762740b31ed3`, com as mesmas protecoes e motor
geometrico oficial. Sua consolidada terminou:1027 passed/2 falhas antigas
da main em3021.98s. GO restrito ao ensaio de criacao/recriacao de187 blocos,
sem Finalizar referencias. Nao e merge do #31 nem aceite construtivo.

## 11. Amarracao e juntas

Auditoria reconstruida coincide com todas as auditorias brutas TP1 do
censo frio. Parede4 melhora; parede18 passa a quatro juntas continuas
t749,5/784,5/1089,5/1109,5 nas 17 fiadas; parede40 passa a duas faixas C09
t119,5/169,5 nas nove fiadas pares. Essas regressoes nao foram ocultadas.

No W019, o fill B34 ocupa exatamente t750..784 tanto A quanto B. Com
fronteiras fixas e no maximo um compensador, a unica composicao de 34cm e
B34. Trocar a ordem interna nao muda as juntas externas. Alterar a fase
do T e decisao pendente expressa na secao36.7; repetir A/B com K=1 continua
regra18.4. A hipotese reversivel trocando as pecas A/B retornadas pelos
T95/138 foi rejeitada: 19647->19671 blocos, zero colisoes, as mesmas500
invasoes e quatro juntas continuas, PRISM_STAGGER +39, CONSECUTIVE -2,
EXCESS -5, STRIP -1. Rodou311,731s, wrapper315,031s, 868 chamadas de
hipotese. Nao e implementacao de coordenacao global dos T nem prova de que
nenhuma coordenacao funcionaria; mostra que a troca isolada nao resolve.
[Experimento e comando](checkpoints/evidence/beta-t-phase-tp1-run.json).
[Auditoria](checkpoints/evidence/beta-bond-audit-tp1.json).

## 12. Compensadores

N1e apenas reordena multiset; nao aprovou teto preferencial. No trecho
fechado t35..219 da parede40, 184cm, nao existe composicao com B34<=1,
compensadores<=1 e sem B19. Alternativas aritmeticas: 4B39+2C09+C04
(3 compensadores), 2B39+3B34 (0 compensadores, 3 especiais), ou
4B39+B19+C04 (1 compensador, B19 fechado fora da excecao residual).
Cada alternativa relaxa um contrato diferente; nenhuma foi aplicada.

Foi esgotada tambem a alternativa puramente tecnica de reordenar as mesmas
sete pecas desse trecho:105 ordens distintas,30 sem adjacencia de
compensadores, **zero** dessas30 com auditoria aprovada, minimo de duas
faixas repetidas. Mantidos os nos/fronteiras, todas as fiadas pares e as
impares originais. K=1 e zonas de isencao vigentes foram respeitados.
[Busca exaustiva de ordens](checkpoints/evidence/beta-wall40-orders.json).
Tornar apenas o teto total preferencial nao elimina essas faixas. As
composicoes relaxadas acima sao contas de fechamento, nao layouts aprovados.

Trecho de 14cm depois de B34 do L so fecha com C09+C04 ou 3C04.
Sequencia obrigatoria nesse espaco nao desaparece tornando o teto preferencial.
[Enumeracao reproduzivel](checkpoints/evidence/beta-fixed-span-compositions.json).
Ela mede composicao a fronteiras fixas, nao prismas/amarracao global.

No TGD,61->66 paredes reprovadas significa **7 entram e2 saem**, nao cinco
novos eventos. Por coordenadas, os indices FONTE novos sao12/13/31/36/66/98/109;
saem8/10. Os IDs do resultado foram remapeados pela geometria: W098 do
resultado e a fonte66, NAO a parede vazia de fonte97 que tem esse nome no input.
[Delta por identidade](checkpoints/evidence/beta-compensator-wall-delta.json).
Seis dos sete eixos novos pertencem aos pares geometricos ja examinados.
Na fonte66, o T106 tem21/21,12cm na principal38 e169,248cm na incoming;
degrada para C09 repetido na ponta. O benchmark acusa faixa em t4,5cm,
mas a auditoria bruta a isenta pela zona de borda e passa. Essa divergencia
nao autoriza apagar o achado ou mudar o contrato automaticamente.
[Contexto66](checkpoints/evidence/beta-compensator-wall66-context.json).

## 13. Performance

Censos TGD: main123,563s, N1 54,437s, N1b81,594s, N1c179,734s,
N1f111,765s; TP1 N1f243,016s. Rodadas concorrentes: nao usar como benchmark
rigoroso nem somar percentuais de bases diferentes. Com cache forcado a miss,
TGD224,281s; equivalencia exata de candidatos, fiadas, colisoes, aberturas,
chaves, bandas e resumo em ambos os inputs.
[Asserts de equivalencia](checkpoints/evidence/beta-cache-equivalence.json).
Isso nao certifica invariancia global sob permutacao ou inversao de endpoints.

## 14. Testes

Consolidada concluida no SHA09b6ea0: **1112 passed, 2 failed em2611,63s**
(43min31s; wrapper2612,109s, exit1). Python3.12.14, pytest9.1.1,
xdist3.8.0, `python -m pytest -n 4 --dist loadfile -q --durations=20`.
PID7828, inicio15:47:54 UTC, timeout5400s. As duas falhas sao
`test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]`
(compensadores52->66) e a mesma funcao para `[torre_easy_lo_r00_tp1]`
(binding8->9, INSIDE_DOOR0->7). Nenhuma falha de validador foi ocultada.
[Metadados](checkpoints/evidence/beta-consolidated-final-v2.json) e
[log bruto](checkpoints/evidence/beta-consolidated-final-v2.txt).

Focados finais: [61 testes em1,99s](checkpoints/evidence/beta-final-focused.txt)
de retencao/preflight/atomicidade passaram; 14
controles legados de criacao/refresh/exclusao passaram. Etapa anterior:
314 testes em98,80s; infraestrutura16. Transacoes testadas com dubles,
nao Revit real. Nenhum skip/xfail/threshold foi alterado para aprovar.
A primeira tentativa consolidada no3229924 foi interrompida intencionalmente
aos187,141s ao encontrar a falha de referencia parcial; nao foi falha de
monitor nem regressao concluida. Foi substituida apos correcao relevante.

Controle independente sem resolver novamente: geometria reconstruida dos
censos main/N1f foi avaliada com os validadores e referencia oficiais.
As contagens por codigo do candidato coincidem integralmente com os scores
N1f versionados, sem erros de validador. Contra o baseline oficial:
TGD main52->61 e candidato52->66 paredes na categoria compensadores;
TP1 main ja tem binding8->9 e comp74->78; candidato acrescenta o alerta
INSIDE_DOOR0->7, cuja invasao antiga esta demonstrada na secao7.
[Comando/controle](checkpoints/evidence/beta-baseline-replay-run.json).
Isso e replay verificavel dos censos, nao uma segunda suite completa da main.
Mesmo que as duas falhas tenham nomes antigos, seu conteudo nao e identico;
as regressoes fisicas novas continuam bloqueando o candidato.

## 15. CI

#32: checks verdes e 12 testes infra +260 test_script antes do merge.
#31 no64532c4: dois checks documentais verdes, runs34371586472/34371591737.
Esses jobs NAO executam o solver. Checks da entrega final ainda serao
conferidos; o verde documental nunca substitui os gates fisicos.

## 16. Documentacao e governanca

#32 MERGED em2026-09-09 14:44:50 UTC, merge
`aa58d70d84c6134216f8f15a131edf060c4dce81`; head revisado7ed1a54.
Main reconciliada na branch beta. Checkpoints sao historicos ou atuais,
com validacao de cobertura de codigo, ancestralidade e hashes dos logs.
Regras oficiais atualizadas somente para registrar orientacoes/contencoes
do usuario, na secao48 da fonte unica. Nao houve aprovacao normativa nova.

Input/reference/reference_score/baseline oficiais permanecem intocados.
Proveniencia de bytes: os censos usaram o checkout Windows com CRLF; os
blobs Git sao LF. Os dez arquivos foram comparados: mesmo JSON e bytes
identicos apos normalizar apenas EOL. Hash de input do censo NAO e hash
dos bytes LF do Git. [Ambos os hashes](checkpoints/evidence/beta-fixture-byte-provenance.json).
Para reproduzir um replay que exige hash exato, usar um checkout isolado
com CRLF (`core.autocrlf=true` antes do checkout); nao editar o fixture
para contornar a guarda. O pacote beta usa blobs Git diretamente e nao
depende dessa conversao. Logs `.txt` preservam bytes por `.gitattributes`.
O [inventario final do diff](checkpoints/evidence/beta-final-diff-review.json)
separa4 arquivos de producao,12 de testes,9 diagnosticos/empacotamento,
4 de infraestrutura,14 documentais e65 de resultados/evidencias no09b6ea0.
O diff herdado de420dbcc inclui score/relatorios gerados: nao confundir esses
artefatos com gabarito, nem alegar diff inteiro vazio no benchmark.
O JSON inicial de conflito geometrico falhou por campo ausente em snapshot
antigo; v2 usa entrada oficial. A falha permanece rastreavel, nao e evidencia positiva.

## 17. Dividas nao bloqueantes

**B, somente apos GO:** API/familias reais, alinhamento de celulas e orientacao,
tempo UI/cancelamento, confirmacao de rollback no documento, dependentes de
Document.Delete, fidelidade CAD/RVT/catalogo; somente copia estatica com backup.
Contravergas/cortados/canaletas: excluir do escopo construtivo ou modelar
manualmente; sua ausencia nao pode ser ocultada num recorte que dependa deles.

**D:** otimizacao global de rebuilds, limpeza historica, teste amplo de
permutacao/inversao, desempenho real e aperfeicoamento da distribuicao de
compensadores. A heuristica N1e pode deixar adjacencia quando ha mais
compensadores que separadores; ela nao e busca exaustiva de todas as ordens.
**C fora do recorte:** secao42, migracao completa CR-B/C2/G16 e suas decisoes
nao sao aprovadas por esta missao. Retencao explicita evita exigir floor geral.

## 18. Decisoes do usuario

Os defeitos fisicos restantes sao **A**. As mudancas de contrato abaixo sao
**C**, nao permissoes que o agente possa deduzir do score:

| Decisao | Regra/caso atual | Alternativas e consequencias | Recomendacao |
|---|---|---|---|
| Unidade fisica nos pares sobrepostos e contatos L/T junto a portas | Dois eixos de14cm ocupam a mesma faixa; contatos fixos minimos ainda colidem/invadem | Manter ambos exige modelagem conjunta/representacao de parede composta definida; corrigir/deduplicar captura exige escolher a geometria verdadeira; excluir o componente inteiro muda o escopo beta e requer novo solve | Confirmar a geometria/unidade fisica pelo projeto fonte e autorizar um input de engenharia separado, preservando fixtures oficiais. Nunca mover/apagar eixo automaticamente |
| Fase dos T proximos | Principal na A; W019 tem juntas externas iguais; secao36.7 nao autorizou inversao | Autorizar coordenacao A/B por grupo permite nova busca; manter regra exige recorte sem esses conflitos ou nova solucao de dominio | Nao liberar B19 como TIE. Avaliar fase coordenada somente com evidencia de todo o grupo, sem prometer que a inversao isolada resolve |
| Compensadores/especiais | Teto1 e B34<=1; 184cm fechado sem solucao estrita; nenhuma das30 ordens sem adjacencia passa na auditoria | Teto preferencial mantem3comp e pelo menos2 faixas; permitir3B34 zera comp mas ainda exige auditar faixas/prismas; B19 fechado muda excecao; trecho14 continua consecutivo em qualquer teto | Separar teto total, adjacencia e excecao de trecho impossivel. Nenhuma relaxacao geral silenciosa |

Nao basta autorizar o merge do #31. E necessario definir o contrato fisico dos
casos acima; depois ainda devem ser implementadas e testadas as solucoes
que dele decorrerem. As provas locais nao demonstram impossibilidade de
todo solver global, mas nao fornecem autoridade para escolher outra
geometria, fase normativa ou composicao proibida. O #31 permanece bloqueado.
Essas decisoes NAO sao necessariamente bloqueadoras de um primeiro beta
limitado sobre a main: a alternativa75/81 foi verificada separadamente no34.

## 19. SHA exato da versao candidata

Codigo/testes avaliados e pacote: **09b6ea0ae221a43a3adc27f63bb05d336351584f**.
Tree: `c28422e31373694a70823095d6f77be258d9f2bc`.
Branch `codex/beta-revit-20260909`, espelhada no draft #31
`claude/sleepy-turing-rf4s7o` por fast-forward. Commits documentais posteriores
nao alteram esse codigo. Nao ha SHA certificado seguro para lancamento no
recorte W019/TGD. Mainaa58d70 e o ultimo estado OFICIAL, nao certificado beta.

[Build](checkpoints/evidence/beta-package-09b6ea0.json) e
[verificacao](checkpoints/evidence/beta-package-09b6ea0-verify.json) passaram.
Pacotes antigos656544e/3229924 sao historicos/superados, apesar do nome
`beta-final-package` do artefato3229924. Hashes verificam integridade/proveniencia,
nao sao assinatura criptografica nem atestado de aprovacao tecnica.

## 20. GO/NO-GO para beta Revit

**NO-GO para09b6ea0. #31 nao integrar. Revit nao iniciado.**
Gates1/3 falham: novas regioes de colisao TGD continuam reais.
Gate5 falha para W019 e os recortes T/X e2L; o recorte75/81 passou offline,
mas nao absolve o gate1 global do #31.
Gates2/4 possuem contencao explicita; isso NAO transforma os demais em GO.
Gate6 foi executado com duas falhas classificadas; gate7 tem SHA fixado. Procedimento dos gates8/9
esta no [runbook condicionado](BETA_REVIT_RUNBOOK.md), nao e ordem para iniciar.
Nao trocar o veredito por score, maioria verde, ausencia de POSITION_OVERLAP
ou permissao generica. A alternativa main-safe nao transporta N1: seu
[veredito restrito e procedimento](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/8a93a27/docs/BETA_MAIN_SAFE_2026-09-09.md)
estao no34. Codigo8cdd33f974f41a9bf41010a32f82762740b31ed3, bancada
de engenharia75/81 com altura uniforme340cm. Nenhum Revit iniciado.
