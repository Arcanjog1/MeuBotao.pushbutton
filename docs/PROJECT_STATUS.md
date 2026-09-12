# PROJECT STATUS

Painel reconciliado por fetch em 2026-09-12 (main `ad46c61`, merge do #38); SHAs são observações datadas.

```json
{
  "observed_utc": "2026-09-12T15:07:27+00:00",
  "main": "ad46c61372ba0292d117e14ba605375af7acd807",
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
      "branch": "claude/fix-fill-tie-running-joint",
      "head": "6b78a9aa70ff0cac239dcdd9ed1deaab730eb9a1"
    }
  ]
}
```

| Área | Estado |
|---|---|
| MAIN / HEAD observado | `ad46c61372ba0292d117e14ba605375af7acd807` (merge do **#38**, 2026-09-12); antes 6439669 (#37), 21576ee (#36), 6c00f7e (#35), aa58d70 (#32) |
| Solver oficial (main) | #37 (Beta 1 + scale-autofix: 8a.1, 11.10 revisada, 11.11, 11.13, 11.14, fileira de B34, filtro por layer (49), lote persistente (50)) + **#38** (sonda de vão 3.1, licença 33.8, régua V2, testes estritos). Falha histórica do benchmark V1: TP1 JUNCTION 8→9 |
| Candidato desta sessão | `claude/fix-fill-tie-running-joint` HEAD `6b78a9a` (base `ad46c61`): **Defeito 1 — junta corrida fill|tie** — paridade das peças de amarração encostadas (regra 33.9): TP1 PRISM 48 → 16 (fill|tie 32 → 0), TGD V2 245 → 53 (fill|tie entre nós distintos 203 → 0); nó|fill 0, INSIDE_DOOR/WINDOW 0, CROSSES_JAMB/OVERLAP iguais. **Sem merge**; PR draft [#39](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/39) para revisão — [checkpoint](checkpoints/2026-09-12-fill-tie-running-joint.md). Anterior: #38 (integrado) — [checkpoint](checkpoints/2026-09-12-pre-beta2-critical-sanitization.md) |
| Solver candidato (outros) | #31 5658e9c: NO-GO; #34 8a93a27 **está na main** — `8a93a27` e `8cdd33f` são ancestrais de `6439669` pela cadeia `8a93a27` → `0ffa8e9` … `41086e4` (Beta 1) → `2599355` → #37. A leitura de 2026-09-12 ("não ancestral") foi feita num clone raso (`git rev-parse --is-shallow-repository` = true, 252 commits alcançáveis) e corrigida na revisão do #38 após `git fetch --unshallow` ([estado](GITHUB_STATE_2026-09-12.md)) |
| Beta Revit | Teste real do botão CPython feito na missão scale-autofix (8.399 blocos, 16/16 gates, `7bb176b`) e integrado; PASS do Beta continua decisão do usuário. Nenhum Revit iniciado em 2026-09-12 |
| Benchmark | V1 (raiz) = HISTORICAL / topologia antiga (TGD 167 paredes); **V2** (`projects/*/v2/`) = topologia do motor atual (TGD 145 paredes / 234 nós / 91 aberturas), `runner.py --version v2` — [README](../nuvem/benchmark/README.md) |
| Bloqueadores | Defeito 1: classe fill|tie fechada no candidato (resta fill|fill — cadeias `C09 C09 C04`/fronteira de banda, TP1 16 — e W080/peça duplicada no TGD, 53); COVERAGE do TGD; decisões pendentes (reserva de meio B54 na 11.10; tier 6 padrão; prioridade regra #1 × #2) — [backlog](BETA2_BACKLOG.md) |
| Decisões | A/B, catálogo/cortes, topo, compensadores, fora do módulo, C2/G16 e CR-B D1–D5; [ADRs](decisions/README.md) |
| Referências | [TORRE EASY/BUTANTÃ](../reference_projects/README.md): EVIDÊNCIA / NÃO NORMA |
| Último checkpoint | [Defeito 1 — junta corrida fill|tie](checkpoints/2026-09-12-fill-tie-running-joint.md); antes [saneamento pré-Beta 2](checkpoints/2026-09-12-pre-beta2-critical-sanitization.md) |
| CI | Só validação documental; recomendação de pytest + `runner --check` em [CI_RECOMMENDATION_2026-09-12.md](CI_RECOMMENDATION_2026-09-12.md) |
| Próximo objetivo | Decidir as três pendências acima; [pacote Beta 2](architecture/beta2-implementation-package.md) |

PR da consolidação: [#36](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/36).
Integração documental não aprova arquitetura/produção. D6 resolvida por #27.

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

## Missão claude/revit-scale-autofix (2026-09-10/11) — escala e comparação humana

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

## Beta 1 - CANDIDATO, validacao Revit PENDENTE

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
