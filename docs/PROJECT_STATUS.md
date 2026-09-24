# PROJECT STATUS

Painel reconciliado por fetch em 2026-09-24 (main `15bacec` = docs do ciclo 2; `74cf2df` = ciclo 2 pós-forense, regra 49.1 / corpus da RUN, direto na main; antes `9376a36` ciclo 1 (regra 78), `ca014aa` runtime canônico e `4bb88bb` = PR #49 mesclado: motor do #42 + UI premium do #46 + OPÇÃO A da regra 48). SHAs são observações datadas.

```json
{
  "observed_utc": "2026-09-24T16:15:33+00:00",
  "main": "15bacec9d5edc58beaf969c78c7c8d0802f8979e",
  "official": [
    {
      "pr": 32,
      "head": "aa58d70d84c6134216f8f15a131edf060c4dce81"
    },
    {
      "pr": 33,
      "head": "59c0352e4a3f66349a08b1d3f1ac5b079ce72bf9"
    },
    {
      "pr": 34,
      "head": "8a93a27a660f59e7b532ea6f9db1a6a3561caffe"
    },
    {
      "pr": 35,
      "head": "6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9"
    },
    {
      "pr": 36,
      "head": "21576ee3d0826f362bce1038131603bd2ccf5dc1"
    },
    {
      "pr": 37,
      "head": "643966994a2552df31e43451b3cb4137a1d3dc59"
    },
    {
      "pr": 38,
      "head": "4d6eecff394b0147a4e59b942162d3aa653755de"
    },
    {
      "pr": 39,
      "head": "cf4e4fb1d825743a75462a660a0965259db035e5"
    },
    {
      "pr": 40,
      "head": "64404af6fdde91aaf9b8dafdb32708a29cdcf0db"
    },
    {
      "pr": 41,
      "head": "1aff5e02104a3508c4eeb2b78e2d103929ca233b"
    },
    {
      "pr": 49,
      "head": "ba66c13dac9e4780880c7be229aaa721ff93ddcb"
    },
    {
      "pr": 42,
      "head": "93f38851836a861acbb48ce25decf8fc3c1b9850",
      "nota": "integrado na main pelo merge do #49 (4bb88bb)"
    },
    {
      "pr": 44,
      "head": "78a79fc1cbd47873b8e24ab1c6a8ee456f10623d",
      "nota": "integrado na main pelo merge do #49 (4bb88bb)"
    },
    {
      "pr": 46,
      "head": "ae4586e0869442a36d5dbca18cb5d7abbf37b3fb",
      "nota": "integrado na main pelo merge do #49 (4bb88bb)"
    }
  ],
  "candidates": [
    {
      "pr": 7,
      "head": "2594f6ff376212e5f24614241a0e1dd4b142b838"
    },
    {
      "pr": 8,
      "head": "e789bf253d82eb7ec1a8f078b85c56cccc30cb3b"
    },
    {
      "pr": 21,
      "head": "766e1ea6ee281cc29a3d6118d6013f3955193352"
    },
    {
      "pr": 28,
      "head": "0596e78eadcbebd9369dbd54272b44952b8211ed"
    },
    {
      "pr": 30,
      "head": "626087b845a23f83b7907c39c448bfa7e8d3e69e"
    },
    {
      "pr": 31,
      "head": "5658e9c7e633a1f9a06e7d374f9a2d63ad22073f"
    },
    {
      "pr": 43,
      "head": "35fb8893dba9c97839ac9aff8c143f8230fff8e8",
      "nota": "draft, somente auditoria (anexo ao #42)"
    },
    {
      "pr": 45,
      "head": "6808570881ac3d77bdc8c43c1a1cf22ac2c7f911",
      "nota": "draft, somente analise do benchmark"
    },
    {
      "pr": 47,
      "head": "17f4bb14b0cd3e5bc13440ff9c10d5304590941b",
      "nota": "draft, CI FAST gate (nao aplicado)"
    },
    {
      "pr": 48,
      "head": "c3e31bbbe48832587af2c30f0d5281bb08e9a93c",
      "nota": "draft, somente auditoria do no T"
    }
  ]
}
```

| Área | Estado |
|---|---|
| MAIN / HEAD observado | `15bacec9d5edc58beaf969c78c7c8d0802f8979e` (docs do ciclo 2); antes `74cf2df` (ciclo 2 / regra 49.1 direto na main; antes `9376a36` = ciclo 1 / regra 78; antes `ca014aa` = runtime canônico; `4bb88bb` = merge do **#49**; antes `55e990d` = #41; #40 CHANNEL em `61d4f6c`); antes 0e41c8e (#39), ad46c61 (#38), 6439669 (#37), 21576ee (#36), 6c00f7e (#35), aa58d70 (#32) |
| Solver oficial (main) | #37 (Beta 1 + scale-autofix: 8a.1, 11.10 revisada, 11.11, 11.13, 11.14, fileira de B34, filtro por layer (49), lote persistente (50)) + #38 (sonda de vão 3.1, licença 33.8, régua V2) + **#39** (paridade das amarrações encostadas, regra 33.9) + **#40** (estratégia de reforço de aberturas CHANNEL, regra 51). CHANNEL é **opt-in**: a Tela de Configuração abre em "Sem reforço", idêntico ao motor legado; verga/contraverga não implementada. Depois: **#42** via #49 (regras 52–77), regra 48 unificada (`8968693`), regra 78 (`9376a36`) e 49.1 (`74cf2df`) — linhas abaixo. Falhas conhecidas: TP1 V1 `JUNCTION_MISSING_BINDING` 8→9 e TGD V2 `COVERAGE_ROW_MOSTLY_EMPTY` 86→92 (as duas reproduzidas em 2026-09-24 com o produto da main); o assert crítico do TGD V2 falha antes do de categoria, e compensators (baseline 61; 62 antes do ciclo 1; 63 desde `9376a36`, segundo os checkpoints dos ciclos 1 e 2) não foi reavaliado — ids KD-01..KD-03 em [KNOWN_DEBT](agents/KNOWN_DEBT.json) |
| Documentação oficial pós-CHANNEL | PR [#41](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/41) `claude/channel-post-merge-doc-fix` HEAD final `1aff5e0`, integrado em `55e990d` (base `61d4f6c`): **correção documental pós-merge do #40** — `channel-strategy-implementation.md` afirmava estado obsoleto de 6627438 (4 cm / VALID_ALTERNATIVE); o estado versionado é apoio efetivo 19/33 cm e `PHYSICALLY_EQUIVALENT`, e o caso de ~4 cm é 6672349 (`KNOWN_LIMITATION`). **Docs-only** — [checkpoint](checkpoints/2026-09-14-post-merge-doc-reconciliation.md) |
| **PR #49 (MERGED em `4bb88bb`)** | Branch `integration/pr42-ui46-final` (base `55e990d`, HEAD `ba66c13`): **motor final do #42 + UI premium do #46** como entrega única. Merge sem perder lado nenhum — a física do #42 é autoridade e a UI do #46 é a referência visual; único conflito textual foi este painel. **OPÇÃO A (usuário, 2026-09-23):** regra 48 sem exceção — peça que invade abertura não é criada (amarração inclusive); amarração rejeitada fica **NÃO resolvida** com revisão humana; só erro fatal bloqueia a RUN. Solver do #42 intacto. PR [#49](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/49) — [checkpoint](checkpoints/2026-09-23-integracao-42-46.md) |
| **Runtime canônico (direto na main, 2026-09-23)** | `8968693`: **regra 48 unificada** — BETA offline e ONLINE passam pelo MESMO gate (`_materialization_gate`), mesmo laudo no cálculo e mesmo `finalize_allowed`; a regra de 2026-08-26 (criar e marcar em vermelho a peça na porta) deixou de valer em qualquer canal. **Loader rastreável**: commit resolvido pela API, download pinado no SHA, `manifest.json` com sha256, `cache=VALIDATED/MISS/OFFLINE_FALLBACK`, banner `MODULAÇÃO AUTOMÁTICA canal= commit=`. Pacote canônico `modulacao-main-<sha7>.zip` (`pacote_pr49.zip` OBSOLETO). [RUNTIME_CANONICO.md](RUNTIME_CANONICO.md) — [checkpoint](checkpoints/2026-09-23-runtime-canonico.md) |
| **Ciclo 1 pós-forense — regra 78 (direto na main, 2026-09-24)** | `9376a36`: **tolerâncias físicas de fechamento (30.8 absorção ≤ 2 cm no nó + 51.13 ruído de jamba, com a tentativa 30.9) valem para QUALQUER estratégia de reforço** — `PHYSICAL_MODULATION_TOLERANCES_ENABLED` ligado no ponto único `_solve_building_blocks_all_courses_impl`; até então só o CHANNEL as tinha e "Sem reforço" deixava trechos inteiros vazios (causa raiz de D1/D7/D8 da comparação forense). Trecho que não fecha nem assim vira **`NON_MODULAR_UNRESOLVED`** (wall_id, fiada, início, fim, comprimento, resíduo, rule_id, revisão humana) no resultado, no relatório e na UI. BUTANTÃ 46 eixos NONE: trechos 224→96, vazio 18 935→9 577 cm, jambas sem peça 198→154; 34 eixos: 78→0 trechos; CHANNEL inalterado; Revit em cópia: 8 184 peças, 0 invasões, bonecas fechadas. Suíte 1702 ok / 1 histórica. **Benchmark TGD V2**: `COVERAGE_ROW_MOSTLY_EMPTY` 86→92 por reclassificação (nenhuma fiada perdeu cobertura; compensadores 2217→2451) — baseline NÃO regravado, decisão humana. D2/D3/D4/D5/D6/D9–D13/D16 ficavam para o ciclo 2 — o ciclo 2 (`74cf2df`, linha abaixo) tratou D5; com o layer de referência (34 eixos) o D4 (B34 invadindo porta, 11→0) desapareceu, e no fluxo de 46 eixos sem layer segue como KD-10; D2/D3 ficam para ciclo próprio; D6, D9–D13, D14, 3B e D16 para o ciclo 3, só com nova autorização. [checkpoint](checkpoints/2026-09-23-ciclo1-tolerancias-fisicas.md) |
| **Ciclo 2 pós-forense — D5 / regra 49.1 (direto na main, 2026-09-24)** | `74cf2df`: **por que o SCRIPT modula 46 eixos e MCP/HUMANO 34** — as 12 a mais são paredes do layer arquitetônico sem alvenaria estrutural (HUMANO: 0–3 peças, só a amarração da parede que as cruza); entram porque o fluxo "paredes existentes" recebia a seleção sem filtro. Nenhum atributo da Wall separa os grupos; a única regra geral é a **seção 49** (cobertura pelas faces `ARQ-STR-BLOCO`: TP 34/TN 12/FP 0/FN 0), que exige um import de referência alinhado — o do doc de teste está a 1/10 e deslocado. Implementado: regra 49 no fluxo de paredes existentes (só descarte, prompt explícito) e **corpus da RUN** (`DETECTED/SELECTED/EXCLUDED` com motivo) em toda execução, relatório e UI. BUTANTÃ 46→34: trechos 96→0, vazio 9 577→30 cm, B34 invasoras 11→0, compensadores 12,0→11,3 %; Revit em cópia 7 397/7 397 criadas, resolvida. **D2/D3 não mudam** (defeito do solver no corpus de 34). Benchmark idêntico à main. [checkpoint](checkpoints/2026-09-24-ciclo2-corpus-d5.md) |
| Solver #42 (integrado na main via #49, `4bb88bb`; PR fechado) | `claude/butanta-modulation-physical-fixes` HEAD `93f3885`, [PR #42](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42): regras 52, 30.9, 53, 54, 55, 60–65 (arranjo das corridas), 66 (microajuste), 68, 71, 72, 74, **75/76/76.1** (canaleta e compensador nunca amarram; nó sem amarração válida fica NÃO RESOLVIDO) e **77** (papel funcional do encontro por fiada). Smoke real no Revit concluído (3 runs, 8.693 peças, readback 0, portões duros 0, `MISSING_REQUIRED_JUNCTION_BOND` 3, `NO_FUNCTIONAL_JUNCTION` 7) — [checkpoint §7.18](checkpoints/2026-09-17-butanta-convergencia-humano.md). (Rótulo "draft / READY FOR MERGE AUTHORIZATION" entrou em 2026-09-23 no commit `e02f881`, antes do merge do #49; em 2026-09-22 o checkpoint dizia READY FOR FINAL REVIEW.) |
| UI #44 (commits integrados via #46/#49; PR fechado) | `codex/modulacao-automatica-ui-redesign`, HEAD avaliado `78a79fc`, [PR #44](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/44): tema grafite, preview contextual, configuração agrupada. **Superada visualmente pelo #46**; seus commits são ancestrais da main pela cadeia do #46. [Entrega](checkpoints/2026-09-16-dark-ui-redesign.md) |
| UI premium (integrada na main via #49, `4bb88bb`; PR fechado) | `codex/modulation-ui-premium-redesign`, HEAD `ae4586e0`, [PR #46](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/46): chrome premium, componentes reutilizáveis, estados de microajuste (planned/applying/confirmed/not_required/failed/cancelled), `run_id`/`revision` contra evento velho, matriz de escala. Incorporada pelo #49 (mesclado); host/solver/regras intocados pelo #46. [Entrega](checkpoints/2026-09-17-ui-post42-preparation.md) |
| Solver candidato (outros) | #31 5658e9c: NO-GO; #34 8a93a27 **está na main** — `8a93a27` e `8cdd33f` são ancestrais de `6439669` pela cadeia `8a93a27` → `0ffa8e9` … `41086e4` (Beta 1) → `2599355` → #37. A leitura de 2026-09-12 ("não ancestral") foi feita num clone raso (`git rev-parse --is-shallow-repository` = true, 252 commits alcançáveis) e corrigida na revisão do #38 após `git fetch --unshallow` ([estado](GITHUB_STATE_2026-09-12.md)) |
| Beta Revit | Teste real do botão CPython feito na missão scale-autofix (8.399 blocos, 16/16 gates, `7bb176b`) e integrado; PASS do Beta continua decisão do usuário. 2026-09-14: CHANNEL criado no Revit real via handler (harness MCP, IronPython), não pelo clique no botão; Tela de Configuração ganhou a escolha da estratégia (testada offline). Depois: smoke real do #42 em 2026-09-22 (3 runs, 8.693 peças); ciclos 1 e 2 em **cópias** via API/MCP (8 184 e 7 397 peças); o clique humano com o prompt do layer de referência e o banner do loader dentro do pyRevit **não** foram exercitados (KD-07, KD-08) |
| Benchmark | V1 (raiz) = HISTORICAL / topologia antiga (TGD 167 paredes); **V2** (`projects/*/v2/`) = topologia do motor atual (TGD 145 paredes / 234 nós / 91 aberturas), `runner.py --version v2` — [README](../nuvem/benchmark/README.md) |
| Bloqueadores | Dívida aberta indexada em [KNOWN_DEBT](agents/KNOWN_DEBT.json) (KD-01..KD-14, com verificação e evidência). Do ciclo 2: D2/D3 (defeitos do solver no corpus de 34), baseline TGD V2 sem regravar (decisão humana), import '1 PAV' do doc de teste. CHANNEL: integrado na main pelo #40. Pendentes: topo/peitoril fora da grade (51.8), cinta de topo (10.7), 30.8 (7719511; a regra 78 ativou 30.8/30.9 em qualquer estratégia — 7719511 não reverificado depois); verga/contraverga não iniciada. Herdados: fill|fill residual (TP1 16), W080/peça duplicada no TGD, COVERAGE do TGD; decisões 11.10/tier 6/regra #1×#2 — [backlog](BETA2_BACKLOG.md) |
| Decisões | A/B, catálogo/cortes, topo, compensadores, fora do módulo, C2/G16 e CR-B D1–D5; [ADRs](decisions/README.md) |
| Referências | [TORRE EASY/BUTANTÃ](../reference_projects/README.md): EVIDÊNCIA / NÃO NORMA |
| Último checkpoint | [Memória técnica F0/F1 — contexto e recuperação (CANDIDATO na branch)](checkpoints/2026-09-24-memoria-contexto-f0-f1.md); antes [Ciclo 2 pós-forense — D5 / regra 49.1](checkpoints/2026-09-24-ciclo2-corpus-d5.md) (main), [ciclo 1 — regra 78](checkpoints/2026-09-23-ciclo1-tolerancias-fisicas.md), [runtime canônico](checkpoints/2026-09-23-runtime-canonico.md), [Missão BUTANTÃ — correções físicas da modulação](checkpoints/2026-09-15-butanta-modulation-physical-fixes.md), [reconciliação documental pós-merge do #40](checkpoints/2026-09-14-post-merge-doc-reconciliation.md) |
| CI | Só validação documental (na branch F0/F1: também manifesto de contexto, registro de dívida e START_HERE sem estado contraditório); não roda solver nem benchmark; recomendação de pytest + `runner --check` em [CI_RECOMMENDATION_2026-09-12.md](CI_RECOMMENDATION_2026-09-12.md); proteção da main não configurada |
| **Memória técnica F0/F1 (CANDIDATO, branch `claude/new-session-9raf0t`)** | Primeira fatia do protocolo de memória técnica (2026-09-24): START_HERE como roteador (PR #40 descrito como "sem merge" corrigido), manifesto de contexto por domínio, pacote de contexto por tarefa (`tools/documentation/context_pack.py`), registro de dívida e avaliação de recuperação; `validate.py` estendido. **Sem mudança de solver, imports, baseline ou RVT.** Sem PR e sem merge até autorização. [checkpoint](checkpoints/2026-09-24-memoria-contexto-f0-f1.md) |
| Próximo objetivo | Ciclo 3 somente com nova autorização (D6 verga/contraverga, D9–D13, D14, 3B, D16); D2/D3 em ciclo próprio; decisões E (topo/peitoril fora da grade) e F (cinta de topo) pendentes; LINTEL não iniciado. Memória técnica: fatia F2 (memória estruturada) só com autorização. [Pacote Beta 2](architecture/beta2-implementation-package.md) e [backlog](BETA2_BACKLOG.md) são snapshots de 2026-09-10 |

PR da consolidação: [#36](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/36).
Integração documental não aprova arquitetura/produção. D6 resolvida por #27.

(HISTÓRICO, 2026-09-10 — o Beta 1 foi integrado pelo #37 em `6439669`, 2026-09-11;
os dois parágrafos abaixo descrevem o estado anterior.)
Branch Beta 1: `claude/revit-solver-perf-diagnosis-6dfd89`, **empurrada em
2026-09-10** e buscavel por outra sessao. O SHA `a5081d8` constava como
ausente do remoto na auditoria anterior porque o push ainda nao havia sido
feito; agora esta publicado. Nao e' ancestral da main e nao deve ser
integrado antes do gate do Revit.

#31: código 09b6ea0, 1112/2; preflight TGD 692 invasões/784 colisões, TP1 500/0.
#34: código 8cdd33f, 1027/2; bancada uniforme 75/81, 187 blocos sem aberturas.
Históricos candidatos, não medição desta main/PASS Revit.
[Fontes fixadas](GITHUB_STATE_2026-09-10.md).

## HISTÓRICO — as seções abaixo descrevem estados ANTERIORES ao #37 (mantidas como registro; o painel acima é o estado corrente)

As frases "sem merge", "Beta 1 CANDIDATO", "#34 bancada" e "pacote 712f221
pendente" abaixo eram verdadeiras nas datas em que foram escritas; desde
2026-09-11 (#37, `6439669`) Beta 1 e a missão scale-autofix estão na main.
Reconciliado em 2026-09-12 — ver [GITHUB_STATE_2026-09-12.md](GITHUB_STATE_2026-09-12.md).

## HISTÓRICO (2026-09-10/11) — Missão claude/revit-scale-autofix — escala e comparação humana

Branch `claude/revit-scale-autofix`, derivada de `41086e43` (Beta 1
reconciliado), HEAD de código `91cc73833c188ca618c86e59cade4f62e6b0a125`,
publicada; main observada por fetch `21576ee3` (inalterada). Sem PR, sem merge.

Pergunta central respondida: o que quebra ao sair das 2 paredes é o
**encontro em T** (e bonecas), não a quantidade — o primeiro FAIL reproduz com
2–3 eixos; a planta inteira da Torre (179 eixos) resolve em 2–8 s.

Cinco correções gerais, todas com teste que falha antes e passa depois:
8a.1 `ProjectElevation` (a modulação nasceria 726 m acima em projetos com
nível no survey point); 11.10 revisada pela evidência humana (T sem espaço
degrada para B34|B34); 11.11 boneca absorvida; fileira de B34 antes de
compensadores empilhados (bug contra a seção 2); 12.1 espelhamento no lugar
(`MirrorElement` duplicava compensadores). Detalhe e evidências:
[fechamento](checkpoints/2026-09-11-revit-scale-autofix-final.md),
[escala](checkpoints/2026-09-10-revit-scale-autofix.md),
[comparação humana](checkpoints/2026-09-10-butanta-human-comparison.md).

Medido no Revit (doc de teste `butanta testes`, 1º PAV, 34 paredes de
alvenaria, 44 aberturas detectadas pelo próprio plugin): 7.257 blocos criados
pelo caminho real (`_execute_create`, modo beta), 0 falhas, 0 colisões, 14
fiadas z=1..261; recriação substitui o lote por exatamente 7.257, 0 órfãs.
Criação custa 36,9 ms por instância (295 s) — gargalo real da Tela 2 em escala.

Gates em aberto: 5 paredes reprovadas pelo auditor (junta corrida na
fronteira preenchimento|amarração — o projeto humano não produz nenhuma);
reserva de canto por fiada; filtro de paredes não estruturais no CAD; um
clique real no botão (CPython) com o pacote do HEAD final `cf325f2` já
instalado em `teste-perf.pushbutton` (backup do `712f221` em `C:/BetaRevit`).
Fechamento das decisões aprovadas (2026-09-11, HEAD `c44c7d9`): regra da
fileira de B34 como regra geral (teto de preferência, flag removida);
regra 11.14 (reserva de canto por fiada, lendo as peças já resolvidas);
filtro por layer de referência estrutural (seção 49, opcional na Tela de
Configuração); seleção corrente de Walls no fluxo "paredes existentes";
bancada salva como `BUTANTA_BENCH_SCALE_AUTOFIX.rvt`. Butantã 12→4
reprovadas (só tocos do CAD + defeito 1), Torre 21→12, TGD sem regressão,
TP1 só a histórica. Teste real no botão CPython (HEAD `198a639`): 16/16 gates, 8.399 blocos
criados e recriados idempotentes (~6,5 min; 33–39 ms por instância); o
travamento 1 (lote anterior não substituído entre sessões) virou a seção 50
(lote persistente por carimbo). Regressão consolidada final: 1066 passed / 2 explicadas (histórica TP1 +
contagem de corpus t48 adaptada). PR aberto para revisão, sem merge. Ver `docs/checkpoints/2026-09-11-fechamento-decisoes-aprovadas.md`.
Regressão consolidada 3 no HEAD final `cf325f2`: 2 failed / 1043 passed (só as
falhas históricas do benchmark: TGD compensators 52→55, TP1 JUNCTION 8→9).
Regressão consolidada 1 (rede de rejeição e fileira de B34 ligadas): 20/1055
falhas — bissecção no TGD provou que a rede de rejeição em par causava
`JUNCTION_MISSING_BINDING` 24→253 (desligada por padrão; sem ela o TGD vira
MELHORIA) e que a fileira de B34 contraria a regra #2 documentada (atrás de
flag, default na regra; decisão pendente). Resultado da regressão 2 e dos
baselines com a configuração final: checkpoint final.

## HISTÓRICO (2026-09-10) — Beta 1 - CANDIDATO, validacao Revit PENDENTE

Branch `claude/revit-solver-perf-diagnosis-6dfd89`, empurrada e buscavel
(HEAD `a5081d8` no momento do push; a branch avancou depois com esta
reconciliacao). Tres defeitos de INTEGRACAO corrigidos, nenhum de
modulacao: acao `create` perdida pelo `finally` do `Execute()`; falso
positivo `REPEATED_VERTICAL_COMPENSATOR_STRIP` (faixa vertical passa a
exigir fiadas ADJACENTES, padrao de mesma paridade preservado como dado);
e `Application.DoEvents()` chamado da thread de fundo, medido em 2652,285s,
corrigido com `_pump_ui`. Em seguida a thread de fundo do `analyze` foi
retirada - `analyze` sincrono no ExternalEvent - apos um deadlock de
1654,774s com o worker sem CPU; `analyze` custa 0,181s na thread principal.

Achado de Z RECLASSIFICADO como comportamento esperado por decisao do
usuario: nenhuma linha vertical alterada (regra 8a das REGRAS).

Medido no Revit: 187 blocos / 17 fiadas criados, recriacao sem duplicata,
encontro L correto. Consolidada 1035 passed / 2 falhas HISTORICAS identicas
as de `8cdd33f`. Detalhe e evidencias:
[checkpoint](checkpoints/2026-09-09-beta-revit-preparing-solver-performance.md).

Fechamento OFFLINE concluido no HEAD reconciliado: testes focados 342
passed; determinismo focal identico em tres processos separados
(`229b46d2...`); consolidada 1054 passed / 2 falhas HISTORICAS com deltas
identicos aos de `8cdd33f`, zero falha nova; CI PASS nos dois passos; diff
revisado - `wall_stepper.py` so' instrumentacao, nenhum baseline, reference,
threshold, skip ou xfail tocado, benchmark oficial intacto.

**Gate obrigatorio em aberto**: UMA execucao real no Revit com o pacote
`712f221`. Sem ela o Beta 1 NAO e' PASS e nao ha' merge.

[Log](PROJECT_STATUS_LOG.md), [status anterior](PROJECT_STATUS_2026-09-09_HISTORICAL.md)
e [processo](DEVELOPMENT_PROCESS.md). Nenhum Revit iniciado.
