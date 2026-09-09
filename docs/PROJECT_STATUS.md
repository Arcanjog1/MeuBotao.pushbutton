# PROJECT STATUS

Estado operacional conferido em 2026-09-09 por fetch e API GitHub.
Esta pagina distingue codigo integrado, candidatos e decisoes pendentes.
Auditoria, limites e gates: [AUDITORIA_BETA_2026-09-09.md](AUDITORIA_BETA_2026-09-09.md).
Evidencia Git/GitHub: [snapshot](checkpoints/evidence/2026-09-09-github.json).
Snapshot historico do #31: [reconferencia](checkpoints/evidence/2026-09-09-github-final.json).
Missao posterior: [relatorio beta](RELATORIO_BETA_2026-09-09.md) e
[runbook condicionado](BETA_REVIT_RUNBOOK.md). **NO-GO; #31 nao integrado.**

```json
{
  "observed_utc": "2026-09-09T16:00:00+00:00",
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
    {"pr": 31, "head": "09b6ea0ae221a43a3adc27f63bb05d336351584f"}
  ]
}
```

## Estado oficial

Main observada: **aa58d70d84c6134216f8f15a131edf060c4dce81**.
PR #32 integrado por merge normal em 2026-09-09 14:44:50 UTC, confirmado
MERGED pela API. Head revisado: 7ed1a545146ac12072a15a5bdcdea92008170051.
Nenhum solver ou norma mudou nesse merge. #31 continua NAO integrado.
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
| CR-N1b/c/e/f + beta | Ausente | PR #31 draft, codigo/testes `09b6ea0` | [relatorio beta](RELATORIO_BETA_2026-09-09.md), 61 focados finais verdes; consolidada1112 passed/2 failed | Colisoes reais TGD, amarracao TP1 e decisoes de dominio; contencao nao e GO |
| CR-B / identidade | Preparacao oficial nao integrada | PR #28 draft, `0596e78` | Inventario e relatorio do PR; chaves estaveis ja existem | C2/G16, decisoes D1-D5, migracao e metricas versionadas |
| Governanca | PR #32 integrado, `aa58d70` | Checkpoints historicos explicitos e timeout de arvore de processos na branch beta | [revisao de integracao](checkpoints/2026-09-09-revisao-pr32.md) | Base: 12 testes infra e 260 test_script; candidato: 16 testes infra verdes |

Tambem integrados: ARM SAFE REPAIR (#12), NÓ|FILL (#17), fidelidade dos
gates ARM (#18), B19 residual condicionado (#19), fit C04 (#20),
reconstrucao de aberturas CR-A (#22) e status #23. Os estados antigos
"branch em aberto" de #18 e "nao mesclado" de #19 foram removidos desta
pagina. Regras permanecem em [REGRAS](../nuvem/REGRAS_MODULACAO_BLOCOS.md),
sem alteracao nesta auditoria.

## Trabalho candidato

PRs abertos no snapshot: **#7, #8, #21, #28, #30 e #31**, todos drafts.
O **PR #32 foi integrado** apos revisao e autorizacao especifica.
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

Etapa beta posterior: `8d75bb4` e `656544e` acrescentam contencao e
retencao sem alterar `wall_stepper.py`. Preparados na branch
`codex/beta-revit-20260909` e publicados tambem no #31 por fast-forward,
mantendo draft e sem merge. O SHA de codigo avaliado e 656544e; o HEAD do
PR inclui o commit documental seguinte. CI do HEAD publicado 1522b3b foi
conferido: dois checks de governanca verdes, sem executar o solver.
Etapa 3: `f9e81cc` protege substituicao atomica do lote beta e valida
transacoes/instancias; `edc9666` acrescenta experimento L separado.
314 testes verdes em 98.80s no codigo f9e81cc; censos completos sem cache
preservam exatamente a geometria TGD/TP1. Recortes L/T/X ainda possuem
achados de amarracao/compensadores e NAO estao liberados. O SHA da tabela
identifica a revisao avaliada; HEAD publicado inclui checkpoints posteriores.

Etapa 4: `3229924`/`09b6ea0` validam entrada finita, retencao de referencia
parcial e assinatura do calculo/refresh beta. Pacote09b6ea0 gerado e verificado,
sem instalar/abrir Revit. 61 testes finais verdes,1.99s, e 14 controles legados
verdes. Consolidada no09b6ea0, PID7828, concluida:1112 passed/2 failed em
2611.63s (43min31s); exit1. TGD comp52->66; TP1 binding8->9 e door0->7.
Giro L163 e troca isolada de fases T95/138 foram medidos no solve completo e
rejeitados por novas invasoes/+39 PRISM_STAGGER. Nenhuma hipotese mudou a
producao. Pares paralelos do input TGD se sobrepoem em faixas0.746/1.258cm;
escolher nova unidade fisica/geometria nao foi autorizado. Aritmetica a
fronteiras fixas confirma conflitos entre tetos de compensadores/especiais.
Ultimo CI publicado conferido:64532c4, dois checks documentais verdes.

Alternativa separada com GO RESTRITO: [PR #34 draft](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/34),
branch `codex/beta-main-safe-20260909`,
codigo8cdd33f974f41a9bf41010a32f82762740b31ed3, baseaa58d70 e motor
geometrico identico a main, SEM N1. Recorte TP1 fonte75/81:187 blocos,
um L, duas pontas livres, nenhuma abertura, zero achados com referencia.
Nao e aprovacao do #31 ou do projeto inteiro. Consolidada propria:
1027 passed/2 falhas antigas da main em3021.98s. Ensaio de bancada
uniforme340cm, NAO substituicao das Walls nativas260/280cm; somente
criacao/recriacao, sem Finalizar referencias. Pacote fixo verificado e
runbook no34. A missao alcancou essa fronteira de beta sem iniciar Revit.

Os PRs #7/#8 tambem carregam diferencas de producao em
`wall_pairing.py`/`wall_stepper.py` desde o merge-base, apesar do escopo
documental declarado por parte dos commits. Nao integrar pela descricao.
#21 e preparacao documental antiga do PR #20 ja integrado.
Branches locais com trabalho nao publicado foram preservadas.

## Testes e fatos confirmados

Missao beta em andamento na branch `codex/beta-revit-20260909`:
novos censos independentes confirmam TGD agregado 1160 -> 1197, mas
colisoes por fiada fisica 726 -> 784 (+58), com novas regioes de overlap
real. OBB fisico com porta ativa na cota: TGD 318 -> 318; TP1 candidato
412, e nao 2094 (este ultimo e medicao agregada contra todas as portas,
incluindo bandas inativas). Nenhum desses resultados corrige invasoes.
Varredura beta espacial, sem limitar dono/secundaria, encontra 500 invasoes
no TP1 (88 adicionais OPENING_REPAIR_FILL de outra parede) e 692 no TGD.
Nao liberar #31. Contencao candidata bloqueia o lote ANTES de criar ou
apagar instancias se houver invasao/colisao; solver bruto nao e filtrado.
Paredes vazias/com criacao incompleta passam a manter suas referencias,
com motivo e identificacao fisica no resultado/log/UI. Loader offline por
SHA e hashes implementado, sem instalar/abrir Revit e sem fallback online.
479 testes intermediarios verdes no HEAD 656544e (219 focados + 260 de
test_script); 16 testes infra e 4 diagnosticos verdes. Consolidada
final dessa etapa nao foi executada. A consolidada posterior terminou
no09b6ea0:1112 passed/2 failed, com log bruto e PID em
[evidencia](checkpoints/evidence/beta-consolidated-final-v2.json).
O preflight e contencao, NAO prova de correcao do solver nem GO.

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
nao autoriza sua geometria. Censos por fiada/Z e propriedade recuperados
nas etapas beta:500 invasoes espaciais TP1 tanto na main quanto N1f,
incluindo88 OPENING_REPAIR_FILL de outra parede. Provas no relatorio beta.

**Paredes vazias:** 197,943cm continua sem blocos nos testes de
caracterizacao. A parede real de 99,754cm envolve reservas de ponta e
midspan, nao simplesmente dois X nao fundidos (diagnostico candidato).
Reproducer com grafo real confirmou reserva negativa -2.5864347014cm
na parede 99.7543545516cm. Registro e retencao estao implementados no
candidato; nao alteram topologia ou comprimento para obter preenchimento.

**Desempenho relatado**, no mesmo ambiente historico TGD: base 99,3s/22
rebuilds; N1 47,8s/7; N1b 65,0s/10; N1c+e 176,4s/22; N1f 127,0s/22.
127s melhora N1c+e, mas fica cerca de 28% acima da base. Nao sao tempos
medidos no Revit. Censos TGD/TP1 posteriores sem acerto de cache
reproduziram exatamente candidatos e resultados fisicos N1f; evidencias
versionadas nesta branch. Isso nao prova invariancia global de permutacao.

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
As etapas1-4 concluiram censos, contencoes, hipoteses e consolidada09b6ea0,
1112 passed/2 failed. +37 agregado=+132/-95 nos pares que aumentam/zeram;
+58 fisico=+156/-98, com322 pares-pecas-fiadas novos e264 removidos.
Novas regioes reais permanecem:31 nao integrar. A alternativa34 nasce
diretamente da main e NAO transporta N1; possui GO restrito de bancada,
com evidencias e limites no seu relatorio, nao aprovacao desta cadeia.

O checkpoint do #31 relata OBB TP1 2094/2094 e TGD 1074/1038, com 68%
do TP1 em STANDARD_FILL. Esses relatos foram reconciliados:2094 mistura
bandas/fiadas/alturas;412 e restrito a propriedade;500 e espacial ativo.
O percentual68% nao caracteriza essas invasoes fisicas ativas.
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
