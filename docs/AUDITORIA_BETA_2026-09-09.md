# Auditoria independente e preparacao do beta Revit

Data: 2026-09-09. Escopo: GitHub, documentacao, codigo e evidencias offline.
**Recomendacao: ainda nao liberar a colocacao automatica do candidato inteiro.**
Faltam fechar a invasao de aberturas, a disposicao das paredes vazias e a
regressao consolidada da versao escolhida. Nao e exigida perfeicao do benchmark.
Nenhum Revit foi iniciado; nenhum solver, regra normativa ou benchmark oficial
foi alterado por esta auditoria. O PR de governanca e exclusivamente candidato.

## 1. Fontes e limites

[Inventario Git/GitHub](checkpoints/evidence/2026-09-09-github.json): 31 PRs,
refs remotas, merge-bases, diffs de todos os PRs abertos e 304 revisoes de
documentos/workflows em main/#28/#30/#31. Capturado depois de fetch.
Cada documento tem caminho, HEAD da arvore, ultimo commit e data; essa tabela
maquina e mais completa que a selecao legivel abaixo. Nao e uma lista de
documentos que todos foram lidos linha a linha: a leitura tecnica foi dirigida
por mecanismos, contradicoes e referencias, com aprofundamento nos casos criticos.

Evidencia nesta auditoria tem tres niveis: **executada** (logs novos por SHA),
**inspecionada** (codigo, commit, JSON ou status GitHub) e **relatada** (medicao
antiga sem saida bruta correspondente acessivel). Relato nao foi promovido a
prova independente. PR nao equivale a merge; suite verde nao equivale a geometria
correta. Nenhuma alegacao de resultado no Revit e feita aqui.

## 2. Estado real e linha do tempo

Main Git e API: `08495d913e72b36a80b034d5f0a1435470d27557`, tree
`f46e90b01143e9ab5c88126635acd900d8c8522f`. Sem commits posteriores na
main no snapshot. Protecao da branch: `protected=false`, sem checks obrigatorios.

| PR | Estado confirmado | HEAD | Base da API / merge-base contra main atual |
|---|---|---|---|
| #28 | OPEN, draft | `0596e78eadcbebd9369dbd54272b44952b8211ed` | `91258dd627af97fe437a56c0506eb096ca5aa267` / mesmo SHA |
| #30 | OPEN, draft | `626087b845a23f83b7907c39c448bfa7e8d3e69e` | `08495d913e72b36a80b034d5f0a1435470d27557` / mesmo SHA |
| #31 | OPEN, draft | `439fd49391227e128038fec704833c66c6ce3ffa` | `08495d913e72b36a80b034d5f0a1435470d27557` / mesmo SHA |

Todos tem `baseRefName=main`; o `baseRefOid` retornado para #28 e historico,
NAO a ponta atual da branch. O merge-base confirma de onde seu diff parte.
Branches: #28 `claude/cr-b-preparacao-identidade`; #30
`claude/fervent-mccarthy-lhwoai`; #31 `claude/sleepy-turing-rf4s7o`.
N1c esta na propria branch #31, com N1e/N1f posteriores.

Outros abertos, todos drafts: #7 `2594f6f`, #8 `e789bf2`, #21 `766e1ea`.
Fechados sem merge: #2 e #9. Integrados: #1, #3-#6, #10-#20, #22-#27 e #29
(23 PRs). O inventario preserva HEAD, titulo literal, datas e URL de cada um.
Titulos de #17/#19 ainda dizem draft apesar de `mergedAt` preenchido.

| Momento UTC | Evento verificavel |
|---|---|
| 07/09 23:16 | #24 / V1 integrado em `91258dd` |
| 08/09 18:03-18:34 | #27 D1 `7cc935d`, #25 S1 `32e1c0e`, #26 C1 `0c6e8f7`, #29 G12 `c88a031` |
| 08/09 18:43-20:45 | Reconciliacoes documentais `4015564`, `116fe10`, merge `08495d9` |
| 08/09 21:18-22:37 | N1 `ac9a0e3`; scores `300aef6`; relatorio/determinismo ate `626087b` (#30) |
| 09/09 01:39-03:32 | N1b `417341c`; regressao/relatos e scores ate `67083b0` (#31) |
| 09/09 05:37 | N1c `cb70224`: fronteira considera alcance do vizinho |
| 09/09 06:34 | N1e `190fd6e`: intercala compensadores sem mudar composicao |
| 09/09 10:30-12:29 | N1f `03942b4`: cache; `439fd49`: relatorio atualizado, suite completa ainda inconclusiva |

Producao nao integrada: #30/#31 mudam `nuvem/core/engine/wall_stepper.py`;
#31 inclui #30 por ancestralidade. #7/#8 carregam `wall_pairing.py` e
`wall_stepper.py` desde `21add6e`, mesmo quando seu ultimo trabalho se diz
auditoria. #21/#28 nao tem diff de producao. Nao sao seis patches independentes.
Todas as refs remotas foram inventariadas; branches sem PR nao foram declaradas
prontas. Checkouts locais tinham mudancas de outros trabalhos, preservadas.

## 3. Auditoria documental

Ultimos commits abaixo sao ANTES desta entrega. Main indica existencia/integracao
do documento, nao aprovacao de todas as propostas nele contidas.

| Documento / proposito | Ultimo commit | Arvore | Estado factual e lacuna |
|---|---|---|---|
| `docs/PROJECT_STATUS.md`, estado operacional | `116fe10` | main e #31 | Caixa parava em `c88a031`; #18/#19 pendentes e #25/#26/#27 drafts reapareciam; N1 ausente. Reconciliado |
| `docs/PROJECT_STATUS_LOG.md`, historia | `4dd7008` | main | Ultima atualizacao em 04/09; nao era historico completo de setembro. Indice desta auditoria acrescentado |
| `docs/CURRENT_REFERENCE_SNAPSHOT.md`, medicao legivel | `4b7cf9e` | main | Ainda dizia CURRENT_MAIN `68a6269`; marcado historico sem alterar numeros |
| `nuvem/REGRAS_MODULACAO_BLOCOS.md`, fonte normativa | `9531cf0` / `03942b4` | main / #31 | Cabecalho diz 01/09; main chega a secao 39, candidato a 46. Ordem antiga de B19 e tensoes de compensadores coexistem. Conteudo normativo preservado |
| `nuvem/PADRAO_MODULACAO.md`, medicoes humanas | `30f4466` | main | Distingue dois projetos e confianca; plano local citado nao versionado. Medicao nao e implementacao |
| `nuvem/ARQUITETURA_INTERATIVA.md`, UI historica | `30f4466` | main | Ja obsoleto; dizia que wall_stepper nao existe. Nota corrige inventario atual, preserva historia |
| `README.md` raiz | inexistente | main/#28/#30/#31 | Entrada efetiva e START_HERE; nao criado README redundante |
| `docs/START_HERE.md`, roteador | `642aa00` | main | Bom ponto de entrada; faltava recuperacao por checkpoint/HEAD. Atualizado |
| `AGENTS.md`, `CLAUDE.md` | `642aa00` | main | Revogam merge permanente, exigem manutencao manual. Entrega versionada e reconciliacao agora explicitas |
| `docs/DEVELOPMENT_PROCESS.md` | `642aa00` | main | Fluxo de CR existente; faltavam metadados verificaveis e fechamento por SHA. Modelo incorporado sem novo manual |
| `.claude/skills/cr-checkpoint/SKILL.md` | ver inventario | main | Mandava gravar SOMENTE em pasta ignorada. Caminho permanente corrigido |
| Skills verification/research/debug/modulacao | ver inventario | main | Convencoes manuais, nao hooks. Verification corrigida; roteador de dominio preservado |
| Workflow `check-project-status.yml` | `642aa00` | main | Apenas alteracao de path; comentarios alegavam autorizacao permanente revogada. Substituido por validacao real |
| `docs/CR_V1_JUNCTION_VALIDATOR_ELEVATION_IDENTITY.md` | `684e999` | main | V1 integrada #24; duplicata DRAFT removida do status por `4015564` nao reapareceu como entrada V1 ativa |
| `docs/CR_S1_L_NODE_ALTERNATION.md` | `33d035f` | main | Integra #25; testes/medicoes pertencem as arvores registradas, nao N1f |
| C1 implementacao / revisao | `34bf696` / `b3dcf0a` | main | Revisao ainda dizia merge pendente; nota historica corrige interpretacao |
| C2 diagnostico / decisao fisica | `b3dcf0a` | main | Nenhum patch; C recomendada, B retirada. Nao houve aprovacao presumida |
| CR-B G12/G16 / G12 preparacao | `b3dcf0a` | main | Preparacao tratava G12 nao iniciado; nota temporal acrescentada |
| G12 implementacao / revisao | `9531cf0` / `73243e9` | main | Revisao dizia S1/C1 draft; nota atual. Residuais e limites empiricos preservados |
| Checkpoints integracao / multifase / G12 | `116fe10` / `b3dcf0a` / `777960c` | main | Versionados em docs, formatos heterogeneos. Ultimos dois marcados historicos |
| `docs/CR_B_INTEGRATION_PREPARATION.md` | `0596e78` | somente #28 | Status antigo S1/C1 e D6; nao copiado como oficial. Tabela de identidade existe nessa branch |
| `BENCH_SWEEP_2026-09-08.md` | `626087b` | #30/#31 | Registros N1, nao ultima revisao do solver |
| `BENCH_FECHAMENTO_N1_2026-09-09.md` | `5da9471` | #31 | Descreve N1b; T sem peca supersedido por N1c; abertura nao foi resolvida |
| `BENCH_N1C_N1E_2026-09-09.md` | `439fd49` | #31 | Inclui N1f; execucao final dita em curso sem log conclusivo. Numeros agregados relatados |
| `docs/REFERENCE_CORPUS.md` e READMEs de benchmark/testes | ver inventario | main | Diferenciam origem/confianca/capabilities; nao certificam beta Revit |
| Relatorios ARM, B19, C04, CR-A e arquivos de arquivo morto | ver inventario | main | Evidencia datada por CR; riscos C3/C4 e limitacoes nao promovidos a bloqueio universal |

Busca de links Markdown locais nos documentos versionados encontrou tres links
quebrados em `nuvem/LOADER_SETUP.md`: `Script.py` deveria ser `../Script.py`;
corrigidos. Referencias em crases a planos locais como
`estou-quero-fazer-isso-wild-stardust.md` e `jazzy-nibbling-hanrahan.md`
nao existem na arvore e permanecem declaradas como indisponiveis. Nomes
quebrados por quebra de linha no status anterior foram removidos junto das
duplicatas. Nao se afirma validacao universal de URLs externas/ancoras.

`.gitignore` ignora `.claude/*`, salvo skills, e todos `*.log`.
No checkout local de MeuBotao, `git ls-files --others --ignored` encontrou
somente `scheduled_tasks.lock` e `settings.local.json` nessa pasta, sem
checkpoint recuperavel. Nas duas outras worktrees locais Antigravity,
inventario de `.claude/` encontrou skills, nao checkpoints. Nao foi possivel
inspecionar pastas ignoradas dos ambientes remotos de agentes anteriores;
ausencia local NAO prova ausencia neles. O checkpoint perdido citado pela
multifase continua sem conteudo recuperado. Nao foram lidas credenciais.

## 4. Automacao: resposta objetiva

**Antes: nao, os arquivos nao eram atualizados automaticamente de forma confiavel.**

| Nivel | Evidencia antes | Depois desta entrega candidata |
|---|---|---|
| 1. Agente escreve quando lembra | Status/log divergentes | Continua redacao humana, com contrato verificavel |
| 2. Instrucao manda atualizar | AGENTS, CLAUDE, status, skills | Caminho versionado, campos, reconciliacao e recuperacao claros |
| 3. Hook/script atualiza | Nenhum hook Git ativo (apenas samples), core.hooksPath ausente | Scripts sob demanda capturam fatos/logs; nao geram narrativa nem alteram normas |
| 4. Workflow valida | Checava so `nuvem/core/engine/**` contra status tocado | Valida entrega inteira, SHAs, ancestralidade, checkpoint, referencias e links locais; testa o proprio validador |
| 5. Gera/publica evidencia | Summary de aviso sem estado verificavel | Actions publica HEAD/base/main e resultado no summary; docs versionadas via commit/push manual |

Nos #30/#31 o check de PR estava FAILURE, mas o de push posterior estava
SUCCESS: diff incremental de um commit documental nao continha o motor. O
[run do #31](https://github.com/Arcanjog1/MeuBotao.pushbutton/actions/runs/34351385322)
confirma o motivo no log. Agora branch/PR usa intervalo desde merge-base.

Garantias limitadas: detecta ausencia de checkpoint versionado, campos vazios,
SHA inexistente, mudanca de producao depois do HEAD avaliado, candidato
indevidamente marcado integrado e referencia local quebrada. Reconciliacao
com main atual e exigida na publicacao de branch/PR. Falta de base falha, nao
vira sucesso por skip. Mudanca trivial tambem requer checkpoint neste contrato.
Nao confirma veracidade de prosa, aprovacao normativa, cobertura dos testes,
ausencia de defeitos ou todas as referencias historicas. Checkpoint nao e assinatura.
Protecao de branch continua desativada; ativar required check seria mudanca
administrativa separada. Nao existe publicacao automatica de regras/gabaritos.

## 5. Estado tecnico independente

VERIFICADO abaixo significa somente o escopo da evidencia citada, nao
homologacao universal. Resultados historicos sao rotulados como tal.

| Mecanismo | Classificacao | Evidencia e limite |
|---|---|---|
| Pareamento, fechamento, espessuras, paredes ausentes | PENDENTE DE REGRESSAO | CR-2F-A/E/D e testes de simetria integrados; eixo espurio de 43,9m relatado. Nao houve extracao real nesta auditoria |
| Parede livre 197,943cm | DEFEITO FISICO ABERTO + DECISAO NORMATIVA | Teste de caracterizacao passou precisamente porque gera zero blocos; positivas vizinhas tambem passam |
| Parede 99,754cm, bonecas e negativos | DEFEITO FISICO ABERTO | Relato candidato: X fundidos; sobra trecho 70,832cm e segmento -2,586cm entre ponta/midspan. Caso livre 99,754 fecha, isolando diferenca de topologia |
| L/S1 e alternancia | VERIFICADO (focado) | S1 integrado; testes no #31 incluidos nos 185 verdes. Nao certifica todos os nos reais |
| T vizinhos / N1b / N1c | VERIFICADO (focado), PENDENTE DE REGRESSAO | 31 testes de colisao/reserva/alcance passam; T restaurado no relato. Ainda ha familia de nos centrados em paredes de 124cm |
| X e nos ambiguos | PENDENTE DE REGRESSAO | Controles L/T/X e limites existem; degradacoes/ambiguidade global nao fechadas |
| Portas/janelas: largura, altura, peitoril | DEFEITO FISICO ABERTO | `_room_at_t_on_wall` ignora abertura que contem o ponto; probe da auditoria confirma. CR-A melhora reconstrucao, nao corrige lancamento |
| Paredes acima/abaixo de aberturas | PENDENTE DE REGRESSAO | Solver por bandas e C1 por elevacao; cobertura de topo/cortados ainda limitada |
| Vergas, contravergas, canaletas/cortados | NAO VERIFICADO no beta | `solver_supported_catalog` exclui alturas/codigos nao suportados. Nao confundir banda de abertura com sistema completo de verga |
| B39/B34/B54/B19/C09/C04 e fit | VERIFICADO (focado) | Bonding e fit nos 185; limites normativos preservados; excecao B19 #19 e especifica |
| Compensadores / especiais | DECISAO NORMATIVA + DEFEITO ABERTO | N1e conserva multiset/extensao, intercala; teto/ordem das regras conflitantes exigem decisao. Baseline TGD 52->66 |
| Juntas same-band/cross-band | PENDENTE DE REGRESSAO | G12 integrado, residual 2 identidades relatado. Aceitacao por total liquido nao garante ausencia universal de nova junta em outro ponto |
| Cobertura e fiadas / C1 | VERIFICADO no contrato inspecionado | Altura declarada + elevacao, nao numero global; nao apaga ausencia fisica. Suite da auditoria nao reexecutou toda a cobertura |
| ARM SAFE REPAIR e reparo local | PENDENTE DE REGRESSAO | Rebuild real, gates fisicos e rejeicoes existem; alteracoes de testes no #31 merecem regressao consolidada |
| Identidade fisica | VERIFICADO nos insumos | 12/12 piloto, 167/167 TGD input, 97/97 TGD reference, 96/96 TP1 input/reference: chaves sem colisao ou divergencia gravada |
| Gabarito humano / CR-B | DECISAO NORMATIVA | TGD input medido e independente; TP1 derivado. Candidato que divide paredes exige migracao; #28 nao integrado |
| C2/G16 | DECISAO NORMATIVA | +23 ROW_MOSTLY_EMPTY nao e prova de +23 vazios novos. Opcoes alteram unidade de avaliacao/gate, nao aprovadas |
| Baselines e regressao nova | PENDENTE DE REGRESSAO | Falhas atuais reproduzidas abaixo; contar duas nao prova que sao fisicamente as mesmas |
| Determinismo mesma entrada | VERIFICADO apenas controles focados | Repeticoes locais passam; equivalencia global N1f e relatada, sem artefato bruto final |
| Determinismo sob permutacao/reversao global | NAO VERIFICADO na arvore candidata | Auditorias antigas registram 8/8 fingerprints distintos sob variacoes; nao equivalem a repeticao bit-a-bit |
| Cache N1f | VERIFICADO no contrato local | 9 testes passam. Lista por identidade e limite 4096; trocar ordem dos arms conserva pertinencia, mas refuta a frase absoluta de que nenhum campo lido e escrito |
| Tempo, rebuilds, risco de UI parada | DIVIDA NAO BLOQUEANTE por si | 127s e medicao historica offline, nao SLA Revit. Beta deve medir regiao pequena e permitir recuperacao sem depender de interface responsiva |

Uma chave `W|x0,y0|x1,y1|tE` canoniza eixo/espessura com arredondamento.
`assign_ids` ordena paredes: W0xx e so rotulo local. A chave e valida para
comparar a mesma geometria apenas apos testar unicidade. Para split/merge,
orientacao invertida de coordenadas axiais, ou outra elevacao, usar migracao,
coordenadas globais e cotas; nao fazer join cego por W0xx ou por chave de bloco
que contenha indice ordinal. A reconciliação existente sinaliza chaves FRACAS
sem coordenada; grade espacial e deduplicacao precisam ser explicitadas.
Nao houve comparacao propria input->result nesta auditoria: os resultados
brutos finais antigos estao ausentes; os testes de baseline foram read-only.

## 6. Testes, metricas e contradicoes verificadas

Em `439fd49`, tree `7591d72e9bac4c4e3d244badd8eb633bbe908867`:

| Execucao | Resultado | Evidencia |
|---|---|---|
| 7 arquivos focados N1/b/c/e/f, bonding, C04, S1, nao modular | 185 passed, 1,52s | [log](checkpoints/evidence/2026-09-09-candidate-focused.txt), [proveniencia](checkpoints/evidence/2026-09-09-candidate-focused.json) |
| Baselines, somente `test_projeto_nao_regrediu_contra_o_baseline` | 2 failed, 1 passed, 6 deselected, 354,47s | [log completo](checkpoints/evidence/2026-09-09-candidate-baselines.txt), [PID/timeout/SHA](checkpoints/evidence/2026-09-09-candidate-baselines.json) |
| Chaves e probe pontual de abertura | Sem colisao nos insumos; room positivo dentro do vao | [JSON e hashes](checkpoints/evidence/2026-09-09-static.json) |

Falhas exatas em `tests/regression/test_benchmark_baselines.py`:

1. `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]`:
   `compensators` 52 -> **66**, delta 14, categoria de paredes reprovadas.
2. `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]`:
   `JUNCTION_MISSING_BINDING` 8 -> **9** E `OPENING_BLOCK_INSIDE_DOOR` 0 -> **7**.

Isso NAO e o conteudo historico 52->61/8->9. Nao se atribui causalidade
nova somente pelo codigo: o #31 relata reclassificacao de B54[715,769]
para B34[715,749] no mesmo vao [564,750], sem resolver sua invasao.
Faltam artefatos por peca/cota para confirmar independentemente essa equivalencia
em toda a familia. O teste atual prova que o codigo e emitido; o probe prova a
lacuna do mecanismo. A lista de 281 ocorrencias relatadas nao e 281 defeitos
fisicos independentes nem foi remensurada integralmente aqui.

798->746 (TGD) / 862->811 (TP1) sao totais relatados de identidades de
achados, nao contagem de compensadores. Os relatos divergem em TP1
POSITION_OVERLAP base 2 versus 1 identidade; sem lista/metodo final nao
normalizar silenciosamente essa divergencia. Scores versionados sao N1b:
`67083b0` nos reais, `300aef6` no piloto. Nao provariam N1f mesmo se verdes.
`input/reference/baseline/reference_score` sao byte-identicos entre main e #31.

Desempenho TGD relatado: base 99,3s/22 rebuilds; N1 47,8s/7; N1b 65s/10;
N1c+e 176,4s/22; N1f 127s/22. N1f melhora 28% contra N1c+e, mas custa
28% a mais que a base. Nao somar speedups de bases diferentes. Outra
inconsistencia: 184/631 = **29,2%**, nao 41% como escrito no perfil; 41%
pode usar outro denominador, que nao esta documentado. Medicao final do
tempo de geracao/reparo separada, perfil bruto e equivalencia bit-a-bit
global permanecem **nao verificados**; nao repetimos a varredura para isso.

Suite completa do #31 nao tem conclusao disponivel: relato termina com
execucoes interrompidas/uma final em curso. 964/2 e N1b; 921/2 e relato de
base anterior. A selecao de baselines nova NAO e suite completa nem prova
ausencia de outras falhas. Comando precisou do Python empacotado (alias
`python` do Windows indisponivel) e instalacao de pytest 9.1.1; para os
baselines, `PYTHONPATH=<checkout candidato>/nuvem`. Sem relancamento de
teste por falha de monitor; PIDs 21440/10544 encerrados, resultados preservados.

## 7. Gates de entrada e recomendacao de beta

Gates se aplicam a versao e regiao selecionadas, com contexto dos encontros
vizinhos, nao apenas a um retangulo recortado que esconda interacoes.

| Gate minimo | Estado atual | Trabalho minimo restante |
|---|---|---|
| Nenhuma regressao critica nova conhecida | NAO FECHADO | Resolver/reconciliar achados de abertura por peca/cota e executar regressao consolidada no SHA final |
| Nenhum bloco dentro/cruzando vao | FAIL | Corrigir ancoragem na jamba preservando amarracao; testar porta e janela no nivel certo |
| Parede vazia com tratamento explicito | PARCIAL | Motivo NON_MODULAR existe, mas faltam lista fisica completa do recorte e disposicao visivel: corrigir, excluir do lancamento com revisao ou aprovar contrato |
| L/T/X criticos e amarracao verificados | PARCIAL | Controles passam; conferir nos da regiao, incluindo T restaurado e encontro proximo da abertura |
| Focados + regressao consolidada | PARCIAL | Focados verdes; suite final incompleta e baseline vermelho. Classificar custos e defeitos, sem regravar baseline para ocultar |
| Versao exata efetivamente carregada | NAO FECHADO | Fixar SHA do pacote completo, registrar hash e caminho carregados; `Script.py` configura `GITHUB_BRANCH = main` na linha 556 |
| Rollback | NAO ENSAIADO no Revit | Copia de RVT e pacote anterior preservados; ensaiar restauracao antes da primeira colocacao |
| Evidencia reproduzivel | PARCIAL | Infra offline pronta; registrar entrada/configuracao/catalogo, cota/unidades/eixo, chave e IDs locais, blocos/achados, log, duracao e capturas antes/depois no beta |

**A. Bloqueadores reais:** invasao de vao, omissao silenciosa de parede,
encontro critico sem amarracao, versao nao fixada, ausencia de rollback e
falta de regressao consolidada para sustentar o recorte escolhido.
Mesmo se invasao for antiga, ela bloqueia lancamento naquela regiao.

**B. Investigaveis durante beta:** correspondencia extracao/modelo, espessuras
raras, R1/R2/R3 da CR-B em modo de inspecao, familias reais e orientacao,
tempo/cancelamento/recuperacao, paredes fora do modulo explicitamente retidas
para revisao. Canaletas e cortados somente como limitacao visivel ou modelagem
manual prevista; nao prometer gera-los quando o catalogo do solver os exclui.

**C. Podem ficar depois:** otimizacao global de rebuilds, refinamento de
compensadores fora do recorte, migracao/recalibracao oficial CR-B, limpeza
completa do historico. C2/G16 bloqueia a integracao da CR-B, nao todo beta
com fonte medida independente. Juntas criticas dentro do recorte exigem
correcao/revisao; divida residual fora dele nao impede a experiencia limitada.

Recomendacao limitada: uma CR para a peca de no cuja origem esta dentro da
abertura, ancorada na borda fisica e testada contra perda de amarracao,
colisao, cobertura e novas invasoes. Em seguida uma execucao consolidada na
versao corrigida e escolha de uma regiao pequena. Nao reiniciar meses de
varreduras nem relaxar regua para fazer a pontuacao parecer melhor.

## 8. Decisoes que continuam com o usuario

| Decisao | Alternativas e efeito fisico | Recomendacao tecnica, nao aplicada |
|---|---|---|
| C2/G16 | A filtra fiadas fora do grid (+7 residual); B reagrupa paredes e contradiz CR-B; C mede vazio global sem apagar achados | C isolada, aprovacao explicita do criterio; nao confundir contencao de vazio com ausencia de defeito |
| Compensadores/especiais (candidato secao 41) | Manter acima do teto; preferir B34 repetido; admitir B19 residual entre nos sob condicao; ou teto preferencial com sequencia ainda proibida | Avaliar opcao 4 separando limite total de adjacencia, com regua consistente. N1e apenas intercala; nao presume autorizacao do teto |
| Fora do modulo (candidato secao 42) | Recusar com revisao; preencher modulo inferior com folga declarada; ampliar tolerancia global | Para beta, recusa visivel/revisao manual e suficiente. Folga exige contrato de fronteira; nao ampliar tolerancia geral |
| CR-B D1 | 19 casos TGD como vao estreito ou duas paredes distintas | Evidencia favorece divisao; nao regravar oficial antes dos gates |
| CR-B D2 | TP1 acompanha por evidencia correlata ou extrai fonte medida independente | Preferir conferencia do TP1 no beta; nao chamar inferencia de medicao |
| CR-B D3 | Autorizar migracao do gabarito/IDs e recalibracao ou preservar oficial | Preservar ate aprovar migracao e comparabilidade por versao |
| CR-B D4 | Conferir R1/R2/R3 antes ou gravar valor humano com pendencia | Conferir antes da escrita oficial, durante beta de inspecao |
| CR-B D5 | Criterio C1 vira regra geral ou fica heuristica deste corpus | Manter heuristica; dois niveis do mesmo edificio nao validam regra universal |

Opcoes D1-D5 conferidas no documento de reconciliacao em `aa5dd1a`,
complementado por `14926fb`; nao se decide por titulo de relatorio.
D6 NAO exige nova decisao: os documentos ja foram recuperados por #27.
Permissao de merge deste PR documental sera solicitada somente na revisao
do usuario; nao houve merge, force-push ou alteracao de protecao.

## 9. Entrega e limites finais

Branch, PR, HEAD avaliado e testes da infraestrutura ficam no
[checkpoint de entrega](checkpoints/2026-09-09-auditoria-governanca.md).
Producao inalterada; regras/gabaritos/baselines intocados; alteracoes locais
dos dois repositorios originais preservadas. Trabalho feito em worktrees
isoladas. Subagente ficou indisponivel por limite de uso antes de produzir
resultado; nenhuma conclusao desta auditoria depende dele.

Limites restantes: nao foi inspecionado Revit real, nao ha log completo
concluido da suite N1f, nao foram recuperados artefatos ignorados remotos,
nao foi certificado determinismo global ou performance no Revit. A
governanca melhora rastreabilidade e detecta inconsistencias estruturais;
nao substitui a revisao tecnica nem a autorizacao normativa do usuario.
