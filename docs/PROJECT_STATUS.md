# PROJECT STATUS

Estado operacional conferido em 2026-09-09 por fetch e API GitHub.
Esta pagina distingue codigo integrado, candidatos e decisoes pendentes.
Auditoria, limites e gates: [AUDITORIA_BETA_2026-09-09.md](AUDITORIA_BETA_2026-09-09.md).
Evidencia Git/GitHub: [snapshot](checkpoints/evidence/2026-09-09-github.json).
Fechamento posterior do #31: [reconferencia](checkpoints/evidence/2026-09-09-github-final.json).

```json
{
  "observed_utc": "2026-09-10T18:30:44.937352+00:00",
  "main": "aa58d70d84c6134216f8f15a131edf060c4dce81",
  "official": [
    {"pr": 24, "head": "91258dd627af97fe437a56c0506eb096ca5aa267"},
    {"pr": 27, "head": "7cc935d9bd7434ae07e9e70d5839cc07ebd5d483"},
    {"pr": 25, "head": "32e1c0ef09b2d67ae1edf76be38e2678340dacd3"},
    {"pr": 26, "head": "0c6e8f7fb66660b9472445d4067e293bcb193c44"},
    {"pr": 29, "head": "c88a031404459ee4cee0f7c36904b8e7b971a471"}
  ],
  "candidates": [
    {"pr": 7, "head": "2594f6ff376212e5f24614241a0e1dd4b142b838"},
    {"pr": 8, "head": "e789bf253d82eb7ec1a8f078b85c56cccc30cb3b"},
    {"pr": 21, "head": "766e1ea6ee281cc29a3d6118d6013f3955193352"},
    {"pr": 28, "head": "0596e78eadcbebd9369dbd54272b44952b8211ed"},
    {"pr": 30, "head": "626087b845a23f83b7907c39c448bfa7e8d3e69e"},
    {"pr": 31, "head": "05030d2cf3e18081b040ad048759099a1b215210"}
  ]
}
```

## Estado oficial

Main observada por fetch: **aa58d70d84c6134216f8f15a131edf060c4dce81**. #32 integrado em 2026-09-09; checks verdes. O relato detalhado abaixo é o snapshot anterior e será compactado no PR de consolidação.
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
| CR-N1b/c/e/f | Ausente | PR #31 draft, `05030d2` | [185 testes](checkpoints/evidence/2026-09-09-candidate-focused.txt) | Colisoes TGD +37, aberturas e regressao final |
| CR-B / identidade | Preparacao oficial nao integrada | PR #28 draft, `0596e78` | Inventario e relatorio do PR; chaves estaveis ja existem | C2/G16, decisoes D1-D5, migracao e metricas versionadas |
| Governanca desta auditoria | Candidata, recomendada para integracao apos checks finais | [PR #32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32), branch `codex/auditoria-governanca-beta-20260909` | [revisao de integracao](checkpoints/2026-09-09-revisao-pr32.md) | Merge especificamente autorizado nesta missao; ainda nao executado neste registro |

Tambem integrados: ARM SAFE REPAIR (#12), NÓ|FILL (#17), fidelidade dos
gates ARM (#18), B19 residual condicionado (#19), fit C04 (#20),
reconstrucao de aberturas CR-A (#22) e status #23. Os estados antigos
"branch em aberto" de #18 e "nao mesclado" de #19 foram removidos desta
pagina. Regras permanecem em [REGRAS](../nuvem/REGRAS_MODULACAO_BLOCOS.md),
sem alteracao nesta auditoria.

## Trabalho candidato

PRs abertos no snapshot: **#7, #8, #21, #28, #30 e #31**, todos drafts.
Esta entrega acrescentou o **PR #32 draft**, exclusivamente documental/infra.
#2 e #9 foram fechados sem merge; os outros 23 PRs de #1 a #31 foram
integrados. Titulo com "draft" nao substitui `state`/`mergedAt`.

N1c pertence a `claude/sleepy-turing-rf4s7o`, nao a uma terceira branch:
`cb70224` (alcance do vizinho), depois `190fd6e` (N1e, intercala),
`03942b4` (N1f, cache), `439fd49` (relato) e `420dbcc` (13:15 UTC,
fechamento relatado da suite e scores regenerados). Este ultimo commit nao
muda codigo nem testes; equivalencia conferida por diff.
N1b foi `417341c`; o snapshot `67083b0` e anterior a N1c/e/f.
`05030d2` acrescentou somente checkpoint, status e secao 47 das regras.
Codigo/testes permanecem identicos a `420dbcc`. CI atual do #31: dois
checks de governanca verdes; isso nao executa nem aprova o solver.

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
nao autoriza sua geometria. A equivalencia peca a peca entre arvores
continua dependente dos artefatos ausentes, nao apenas da soma de codigos.

**Paredes vazias:** 197,943cm continua sem blocos nos testes de
caracterizacao. A parede real de 99,754cm envolve reservas de ponta e
midspan, nao simplesmente dois X nao fundidos (diagnostico candidato).
Cada parede omitida precisa ter motivo, selecao fisica e disposicao de
revisao explicitos antes de qualquer criacao no beta.

**Desempenho relatado**, no mesmo ambiente historico TGD: base 99,3s/22
rebuilds; N1 47,8s/7; N1b 65,0s/10; N1c+e 176,4s/22; N1f 127,0s/22.
127s melhora N1c+e, mas fica cerca de 28% acima da base. Nao sao tempos
medidos no Revit. A prova bit-a-bit global do cache nao esta disponivel;
os nove testes locais de contrato passaram. Ordem de `arms` e mutada
no solver, embora o conjunto consultado pelo cache seja preservado.

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
Prioridade da missao iniciada apos a auditoria: explicar por identidade
as colisoes TGD 1160 -> 1197; distinguir agregado de bandas/variantes de
fiadas realmente criadas; verificar OBB nas cotas ativas das portas;
implementar contencao explicita e revisar paredes vazias. Nao aplicar a
candidata de zerar room dentro da abertura, rejeitada na secao 47 do #31.
Ancoragem na jamba nao esta aprovada nem provada como correcao suficiente.
Depois das correcoes tecnicas: regressao final e recorte pequeno verificado.

O checkpoint do #31 relata OBB TP1 2094/2094 e TGD 1074/1038, com 68%
do TP1 em STANDARD_FILL. Sao relatos a conferir no escopo de fiadas e
aberturas passado ao instrumento, nao certificacao de 2094 volumes 3D.
O caso B34 em W019 permanece invasao real conhecida, nao eliminado pela
reclassificacao de OPENING_BLOCK_*. Contencao nao autoriza mudar benchmark.
Usuario autorizou #31 somente ao final e apos TODOS os gates tecnicos;
#30 e ancestral integral de #31, nao integrar separadamente. Os demais
PRs continuam sem autorizacao de merge. Revit nao deve ser iniciado.

O beta pode comecar sem benchmark perfeito, em copia de projeto, com
versao fixada e rollback ensaiado, quando essa regiao nao tiver blocos
em vaos, regressao critica nova ou parede vazia silenciosa. C2/CR-B e
desempenho global nao bloqueiam automaticamente uma regiao fora desses
casos. Logs devem registrar entrada, configuracao, versao carregada,
geometria, chave fisica e resultado para gerar regressao offline.

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

## Reconciliação 2026-09-10 — referências humanas

#33: EVIDÊNCIA / NÃO NORMA; revisão e limites em [revisão TORRE EASY](revit_reference_extraction/REVIEW_2026-09-10.md). #35 será revisado depois. #34 e #31 continuam candidatos. Beta 1: **CANDIDATO — VALIDAÇÃO REVIT PENDENTE**; branch de desempenho informada pelo usuário ainda não localizada no remoto. Nenhum desses candidatos foi integrado.
