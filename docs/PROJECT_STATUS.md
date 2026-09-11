# PROJECT STATUS

Painel reconciliado por fetch/API em 2026-09-10; SHAs são observações datadas.

```json
{
  "observed_utc": "2026-09-10T18:57:19.155668+00:00",
  "main": "21576ee3d0826f362bce1038131603bd2ccf5dc1",
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
      "pr": 35,
      "head": "6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9"
    },
    {
      "pr": 36,
      "head": "21576ee3d0826f362bce1038131603bd2ccf5dc1"
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
      "pr": 34,
      "head": "8a93a27a660f59e7b532ea6f9db1a6a3561caffe"
    },
    {
      "branch": "claude/revit-solver-perf-diagnosis-6dfd89",
      "head": "a5081d85b3fcb79cbb2f8c99dadcd08b4c186f8b"
    }
  ]
}
```

| Área | Estado |
|---|---|
| MAIN / HEAD observado | 21576ee3d0826f362bce1038131603bd2ccf5dc1 (merge do #36); antes 6c00f7e; main inicial aa58d70 |
| Solver oficial | Produção igual à main inicial; S1/C1/G12 e ARM integrados, N1 ausente |
| Solver candidato | #31 5658e9c: NO-GO; #34 8a93a27: bancada offline restrita |
| Beta Revit | **CANDIDATO — ESCALA E CRIAÇÃO REAL MEDIDAS** na branch `claude/revit-scale-autofix` (HEAD 91cc738): planta de 179 eixos passa o gate de criação; 7.257 blocos criados e recriados no Revit sem duplicata (Butantã, 34 paredes, 44 aberturas); 5 paredes ainda reprovadas pelo auditor (humano: 2). Sem merge. |
| PRs importantes | #32 governança, #33/#35 referências integrados; [inventário/checks](GITHUB_STATE_2026-09-10.md) |
| Bloqueadores | Invasões/colisões/amarração no recorte, omissões, validação síncrona/rollback real; [backlog](BETA2_BACKLOG.md) |
| Decisões | A/B, catálogo/cortes, topo, compensadores, fora do módulo, C2/G16 e CR-B D1–D5; [ADRs](decisions/README.md) |
| Referências | [TORRE EASY/BUTANTÃ](../reference_projects/README.md): EVIDÊNCIA / NÃO NORMA; BUTANTÃ 1º PAV comparado ao vivo com o solver em 2026-09-10 — [comparação](checkpoints/2026-09-10-butanta-human-comparison.md) |
| Último checkpoint | [Fechamento scale-autofix](checkpoints/2026-09-11-revit-scale-autofix-final.md); antes [Consolidação Beta 2](checkpoints/2026-09-10-beta2-consolidation.md) |
| Próximo objetivo | [Pacote](architecture/beta2-implementation-package.md), após decisões e validação Beta 1 |

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
TP1 só a histórica. Pendentes: teste real no botão CPython, regressão
consolidada final, PR. Ver `docs/checkpoints/2026-09-11-fechamento-decisoes-aprovadas.md`.
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
