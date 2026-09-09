# PROJECT STATUS

Estado operacional conferido em 2026-09-09 por fetch e API GitHub.
Esta pagina distingue codigo integrado, candidatos e decisoes pendentes.
Auditoria, limites e gates: [AUDITORIA_BETA_2026-09-09.md](AUDITORIA_BETA_2026-09-09.md).
Evidencia Git/GitHub: [snapshot](checkpoints/evidence/2026-09-09-github.json).
Snapshot historico do #31: [reconferencia](checkpoints/evidence/2026-09-09-github-final.json).
Missao atual: [beta main-safe](BETA_MAIN_SAFE_2026-09-09.md), SEM N1.
GO tecnico restrito ao ensaio de bancada75/81; nao aprova31 ou projetos completos.

```json
{
  "observed_utc": "2026-09-09T18:25:30.512157+00:00",
  "main": "aa58d70d84c6134216f8f15a131edf060c4dce81",
  "official": [
    {"pr": 24, "head": "91258dd627af97fe437a56c0506eb096ca5aa267"},
    {"pr": 27, "head": "7cc935d9bd7434ae07e9e70d5839cc07ebd5d483"},
    {"pr": 25, "head": "32e1c0ef09b2d67ae1edf76be38e2678340dacd3"},
    {"pr": 26, "head": "0c6e8f7fb66660b9472445d4067e293bcb193c44"},
    {"pr": 29, "head": "c88a031404459ee4cee0f7c36904b8e7b971a471"},
    {"pr": 32, "head": "aa58d70d84c6134216f8f15a131edf060c4dce81"}
  ],
  "candidates": [
    {"pr": 7, "head": "2594f6ff376212e5f24614241a0e1dd4b142b838"},
    {"pr": 8, "head": "e789bf253d82eb7ec1a8f078b85c56cccc30cb3b"},
    {"pr": 21, "head": "766e1ea6ee281cc29a3d6118d6013f3955193352"},
    {"pr": 28, "head": "0596e78eadcbebd9369dbd54272b44952b8211ed"},
    {"pr": 30, "head": "626087b845a23f83b7907c39c448bfa7e8d3e69e"},
    {"pr": 31, "head": "73cbf08b4584f2e952e17a444ed88a99f9df5498"},
    {"pr": 33, "head": "51ed8c20c8c7ab903b851cfaae1432663955200a"},
    {"pr": 34, "head": "8cdd33f974f41a9bf41010a32f82762740b31ed3"}
  ]
}
```

## Estado oficial

Main observada: **aa58d70d84c6134216f8f15a131edf060c4dce81**.
#32 integrado por merge normal autorizado em14:44:50 UTC, somente
documentacao/infra. Nenhum outro PR foi integrado nesta missao.
Ultimo marco de solver desta cadeia: CR-G12, merge `c88a031`.
Os commits seguintes ate `08495d9` reconciliam documentacao.
O SHA e uma observacao datada, nao uma promessa de que a main nunca avancara.

| Componente | Estado na main | Estado candidato | Evidencia | Pendencia |
|---|---|---|---|---|
| CR-V1 | PR #24 integrado, `91258dd` | Nenhum novo | [relatorio](CR_V1_JUNCTION_VALIDATOR_ELEVATION_IDENTITY.md), teste por elevacao | Regua de encontros nao elimina defeitos do solver |
| CR-D1 | PR #27 integrado, `7cc935d` | Nenhum | [recuperacao](CR_D1_DOCUMENTAL_RECOVERY.md) | D6 documental resolvida |
| CR-S1 | PR #25 integrado, `32e1c0e` | Herdado pelo #31 | [alternancia](CR_S1_L_NODE_ALTERNATION.md) | Custo de compensadores aceito nessa integracao, nao licenca geral |
| CR-C1 | PR #26 integrado, `0c6e8f7` | Herdado pelo #31 | [cobertura](CR_C1_COVERAGE_EXPECTED_ROWS_PHYSICAL.md) | Nao resolve C2/G16 inteiro |
| CR-G12 | PR #29 integrado, `c88a031` | Herdado pelo #31 | [revisao](CR_G12_REVISAO_INDEPENDENTE.md) | Duas identidades cross-band residuais historicas; custo ARM |
| CR-N1 | Ausente | PR #30 draft, `626087b`; incluido no #31 | Diff de `wall_stepper.py`, testes de vizinhos | Nao integrar #30 isoladamente: regressao do T corrigida so depois |
| CR-N1b/c/e/f + beta | Ausente | PR #31 draft, codigo09b6ea0, documentos73cbf08 | [Relatorio completo](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/73cbf08b4584f2e952e17a444ed88a99f9df5498/docs/RELATORIO_BETA_2026-09-09.md) | NO-GO: TGD+37 agregado/+58 fisico, regressoes de amarracao;1112 passed/2 failed |
| Beta main-safe | Ausente | [PR #34 draft](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/34), codigo8cdd33f; SEM N1 | [Relatorio e escopo](BETA_MAIN_SAFE_2026-09-09.md) | GO restrito a bancada75/81;1027 passed/2 falhas antigas na consolidada |
| CR-B / identidade | Preparacao oficial nao integrada | PR #28 draft, `0596e78` | Inventario e relatorio do PR; chaves estaveis ja existem | C2/G16, decisoes D1-D5, migracao e metricas versionadas |
| Governanca | #32 integrado emaa58d70 | Melhorias de checkpoint historico e captura de timeout na branch beta | [revisao de integracao](checkpoints/2026-09-09-revisao-pr32.md) | CI documental nao executa solver nem aprova regras |

Tambem integrados: ARM SAFE REPAIR (#12), NÓ|FILL (#17), fidelidade dos
gates ARM (#18), B19 residual condicionado (#19), fit C04 (#20),
reconstrucao de aberturas CR-A (#22) e status #23. Os estados antigos
"branch em aberto" de #18 e "nao mesclado" de #19 foram removidos desta
pagina. Regras permanecem em [REGRAS](../nuvem/REGRAS_MODULACAO_BLOCOS.md),
sem alteracao nesta auditoria.

## Trabalho candidato

PRs abertos no snapshot: **#7, #8, #21, #28, #30 e #31**, todos drafts.
O **PR #32 foi integrado**. Main-safe esta no **PR #34 draft**, separado.
#33 tambem apareceu como draft de outra frente documental de extracao
humana; nao foi integrado, revisado integralmente ou transportado aqui.
[Snapshot de publicacao](checkpoints/evidence/main-safe-github-publication.json).
#2 e #9 foram fechados sem merge; os outros 23 PRs de #1 a #31 foram
integrados. Titulo com "draft" nao substitui `state`/`mergedAt`.

N1c pertence a `claude/sleepy-turing-rf4s7o`, nao a uma terceira branch:
`cb70224` (alcance do vizinho), depois `190fd6e` (N1e, intercala),
`03942b4` (N1f, cache), `439fd49` (relato) e `420dbcc` (13:15 UTC,
fechamento relatado da suite e scores regenerados). Este ultimo commit nao
muda codigo nem testes; equivalencia conferida por diff.
N1b foi `417341c`; o snapshot `67083b0` e anterior a N1c/e/f.
`05030d2` acrescentou somente checkpoint, status e secao 47 das regras.
Naquele snapshot, codigo/testes eram identicos a `420dbcc`. Posteriormente
o #31 recebeu contencoes ate09b6ea0, mantendo N1 e suas regressoes fisicas.
Consolidada1112 passed/2 failed,2611.63s. No73cbf08, checks documentais
verdes34383983344/34383985595; isso nao executa nem aprova o solver.

A alternativa atual foi criada DIRETAMENTE deaa58d70, com motor/validadores
identicos a main e os testes originais de ARM/G12 preservados. Apenas
Script.py, beta_package.py e wall_modeling.py transportam protecoes; nenhuma
correcao N1/N1e/N1f foi integrada ou revertida na branch do outro trabalho.
Codigo8cdd33f:331 controles iniciais verdes em112.95s e teste do recorte
verde. Consolidada iniciou17:32:04 UTC, PID25596, timeout5400s; terminou
com1027 passed/2 failed em3021.98s (50min21s), exit1. Falhas antigas:
TGD compensators52->61 e TP1 JUNCTION_MISSING_BINDING8->9.
CI noee2250a: dois checks documentais verdes34389067319/34389092291.
Commits documentais posteriores nao mudam o codigo8cdd33f avaliado.
Pacote fixo exportado/verificado, nao instalado. Escopo de bancada: dois
eixos75/81, sem aberturas, altura uniforme definida no runbook. Nao aprova
as alturas heterogeneas260/280cm das Walls nativas nem TP1/TGD completos.

Os PRs #7/#8 tambem carregam diferencas de producao em
`wall_pairing.py`/`wall_stepper.py` desde o merge-base, apesar do escopo
documental declarado por parte dos commits. Nao integrar pela descricao.
#21 e preparacao documental antiga do PR #20 ja integrado.
Branches locais com trabalho nao publicado foram preservadas.

## Testes e fatos confirmados

No candidato exato `439fd49`, Python 3.12.14 e pytest 9.1.1, sem Revit:

- **185 passed** nos sete arquivos focados N1/b/c/e/f, bonding, fit C04,
  S1 e paredes nao modulares; 1,52s de pytest.
- Comparacao de baseline selecionada: **2 failed, 1 passed, 6 deselected**,
  354,47s; `runner.run_project(write_files=False)`.
- TGD: categoria `compensators` **52 -> 66 paredes reprovadas**, nao
  numero de pecas. TP1: `JUNCTION_MISSING_BINDING` **8 -> 9** e
  `OPENING_BLOCK_INSIDE_DOOR` **0 -> 7 ocorrencias**.
- [Log integral e nomes das falhas](checkpoints/evidence/2026-09-09-candidate-baselines.txt).
  O conteudo NAO equivale ao historico TGD 52 -> 61 / TP1 8 -> 9.
- [Probe independente](checkpoints/evidence/2026-09-09-static.json):
  no em `t=742` dentro do vao `564..750` ainda recebe room positivo
  nos dois sentidos (742cm/58cm). Defeito de medicao confirmado no codigo.
- Suite completa de N1c/e/f: **1003 passed / 2 failed relatados** em
  `420dbcc` (39min, `-n 4 --dist loadfile`), sem log bruto acessivel.
  Nao repetida: codigo/testes identicos aos auditados. As duas assercoes
  relatadas batem com nossa execucao independente. 964/2 era N1b.

Relatos do #31 informam 798 -> 746 / 862 -> 811: sao **totais de identidades
de achados**, NAO compensadores, nem necessariamente defeitos fisicos
distintos entre codigos. Conjuntos brutos finais nao estavam versionados;
nao foram reproduzidos nesta auditoria. Os `score.json` de TGD/TP1 eram de
`67083b0` na primeira consulta e foram atualizados em `420dbcc`: registram
11837/19647 blocos, overlap zero, TGD binding 23 e TP1 binding 9, com 5/7
ocorrencias INSIDE_DOOR abertas. Sao agregados, nao prova dos conjuntos
finais de identidades. O
[CURRENT_REFERENCE_SNAPSHOT](CURRENT_REFERENCE_SNAPSHOT.md) e historico de
`68a6269`, nao medicao da main atual.

## Defeitos, dividas e desempenho

**Aberturas:** o T sem peca tem correcao candidata N1c e testes focados;
a invasao de porta continua aberta. O #31 relata que B54 atravessando a
jamba virou B34 dentro da porta, reclassificando a mesma situacao. Isso
nao autoriza sua geometria. Os censos fisicos posteriores estao publicados
no73cbf08: TP1 tem500 invasoes espaciais ativas tanto na main quanto N1f;
sete ocorrencias W019 sao uma familia antiga reclassificada, nao correcao.

**Paredes vazias:** 197,943cm continua sem blocos nos testes de
caracterizacao. A parede real de 99,754cm envolve reservas de ponta e
midspan, nao simplesmente dois X nao fundidos (diagnostico candidato).
As protecoes candidatas agora registram coordenadas/motivo e preservam
referencias vazias, parcialmente nao modulares ou incompletamente criadas.
Nao ampliam tolerancia nem corrigem cobertura vertical heterogenea.

**Desempenho relatado**, no mesmo ambiente historico TGD: base 99,3s/22
rebuilds; N1 47,8s/7; N1b 65,0s/10; N1c+e 176,4s/22; N1f 127,0s/22.
127s melhora N1c+e, mas fica cerca de 28% acima da base. Nao sao tempos
medidos no Revit. Censos completos TGD/TP1 posteriores sem acertos de
cache reproduziram candidatos e resultados fisicos do N1f; artefatos
publicados no73cbf08. Isso nao prova invariancia global de permutacao.
N1f nao foi transportado para esta branch main-safe.

Continuam como dividas: juntas cross-band residuais, compensadores,
limites de catalogo (canaletas/cortados/vergas), C04 C3/C4, arestas ARM,
eixo espurio historico de 43,9m e sugestao de espessuras limitada na UI.
Determinismo sob permutacao global nao e provado por repetir a mesma
entrada: manter esses escopos separados. Nao reabrir pairing/merge
estabilizados sem contraexemplo.

## Decisoes pendentes

- C2/G16: opcoes exatas em [CR_C2_DECISAO_FISICA](CR_C2_DECISAO_FISICA.md).
  Recomendada C isolada, medicao por vazio fisico global; ainda exige
  aprovar o criterio do gate. B foi retirada por contradizer a CR-B.
- CR-B: nao aprovada oficialmente; D6 foi resolvida por #27. D1-D5 e
  escrita oficial de gabarito/recalibracao nao foram autorizadas aqui.
- Compensadores: manter politica, preferir B34 repetido, admitir B19
  residual condicionado, ou distinguir teto preferencial de proibicao de
  sequencia. N1e so reordena composicao; nao aprova a metade normativa.
- Fora do modulo: manter recusa com revisao, ou preencher modulo inferior
  com folga declarada. Ampliar tolerancia global nao e recomendado.
  Nenhuma alternativa foi aplicada nesta auditoria.

## Beta e proximo passo

**Nao liberar a colocacao automatica do candidato inteiro no Revit agora.**
As colisoes TGD foram decompostas por identidade: agregado+37=+132/-95
nos pares que aumentam/zeram; fisico+58=+156/-98. Ha322 pares-pecas-fiadas
novos e264 removidos, com novas regioes reais. Nao mesclar31. A medicao
ingenua2094 misturava fiadas/bandas/cotas;412 restringia a propriedade;
espacial500 TP1 inclui88 OPENING_REPAIR_FILL de outras paredes. A antiga
afirmacao68%STANDARD_FILL nao caracteriza essas invasoes fisicas ativas.
Hipoteses locais L/T rejeitadas e conflitos normativos estao no relatorio31.

O main-safe8cdd33f terminou a consolidada e tem GO tecnico RESTRITO
ao ensaio de bancada75/81, uniforme340cm. Recorte
sem aberturas,1L,187 blocos e zero achados; verificacao de familias/API
ficara no beta futuro. Nao usar as Walls nativas260/280cm como se fossem
esse ensaio. Nenhum GO foi declarado antes da conclusao da consolidada.
Revit nao foi iniciado; o proximo passo fica para a execucao real do
runbook. Nao finalizar referencias, ampliar escopo ou mesclar31.
Usuario autorizou #31 somente ao final e apos TODOS os gates tecnicos;
#30 e ancestral integral de #31, nao integrar separadamente. Os demais
PRs continuam sem autorizacao de merge. Revit nao deve ser iniciado.

O beta pode comecar sem benchmark perfeito, em copia de projeto, com
versao fixada e rollback ensaiado, quando essa regiao nao tiver blocos
em vaos, regressao critica nova ou parede vazia silenciosa. C2/CR-B e
desempenho global nao bloqueiam automaticamente uma regiao fora desses
casos. Logs devem registrar entrada, configuracao, versao carregada,
geometria, chave fisica e resultado para gerar regressao offline.
Procedimento especifico: [runbook main-safe](BETA_MAIN_SAFE_RUNBOOK.md).

## Diagnostico do beta no Revit: "Preparando o solver..."

Primeiro beta controlado (8cdd33f) trava minutos em "Preparando o
solver..." numa bancada de 2 Walls, 1 encontro em L e 0 aberturas.
Detalhe, numeros e limites:
[checkpoint](checkpoints/2026-09-09-beta-revit-preparing-solver-performance.md).

Medido, nao suposto: a entrada real do Revit e congruente com
[main-safe-engineering-input.json](checkpoints/evidence/main-safe-engineering-input.json)
(sem erro de unidade, sem Z incorreto), o grafo tem 3 nos / 1 L / 2 pontas
livres sem residuo da execucao anterior, e o caminho `analyze` do botao
custa 0,37s no documento real. O benchmark offline de 0,1-1,1s exercita
`_execute_solve`, e o botao dispara `analyze` - os dois numeros nao sao
comparaveis.

CAUSA-RAIZ AINDA ABERTA e sem correcao. A branch entrega instrumentacao
[PERF] no caminho real (`core/engine/perf_trace.py`); falta um clique no
pacote instrumentado para separar latencia do ExternalEvent de trabalho
real. Estado candidato, nao oficial - nao mesclar.

## Governanca e recuperacao

Seguir [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md).
Novo agente: fetch, status, checkpoint versionado e evidencias por SHA.
Validacao detecta arquivos/campos/SHAs ausentes, referencia local invalida,
checkpoint so ignorado e classificacao ancestral incoerente. Nao julga
regra normativa nem corrige texto automaticamente. A protecao da main
estava desativada no snapshot; checks nao sao veto administrativo.

Historico: [PROJECT_STATUS_LOG.md](PROJECT_STATUS_LOG.md) e Git.
Relatos datados anteriores preservam o que se sabia naquela revisao; nao
substituem este estado operacional reconciliado.
