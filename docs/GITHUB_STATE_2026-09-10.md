# Estado Git/GitHub reconstruído em 2026-09-10

Main inicial: aa58d70d84c6134216f8f15a131edf060c4dce81.
Main após referências: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9.
Snapshots: [inicial](checkpoints/evidence/2026-09-10-github-initial.json),
[após integrações](checkpoints/evidence/2026-09-10-github-references-merged.json).
Registros datados; fetch antes de retomar.

## PRs prioritários e antigos abertos

| PR | Classificação | HEAD | Merge-base contra main após referências | Disposição |
|---|---|---|---|---|
| [#7](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/7) | HISTORICAL | 2594f6ff376212e5f24614241a0e1dd4b142b838 | 21add6ec1f6cad220bdf3ff8651adb90b63d6e1b | Auditoria antiga com diferenças de produção herdadas; preservar. |
| [#8](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/8) | HISTORICAL | e789bf253d82eb7ec1a8f078b85c56cccc30cb3b | 21add6ec1f6cad220bdf3ff8651adb90b63d6e1b | Diagnóstico histórico de wall graph com diferenças de produção herdadas; preservar. |
| [#21](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/21) | SUPERSEDED | 766e1ea6ee281cc29a3d6118d6013f3955193352 | 3ebcd9b63875f9114a3d6223aa648e5075e2d35b | Preparação de #20 já integrado; recomendar fechamento com link ao histórico. |
| [#28](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/28) | BLOCKED | 0596e78eadcbebd9369dbd54272b44952b8211ed | 91258dd627af97fe437a56c0506eb096ca5aa267 | CR-B: D1–D5/G16/migração pendentes; D6 resolvida por #27. |
| [#30](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/30) | SUPERSEDED | 626087b845a23f83b7907c39c448bfa7e8d3e69e | 08495d913e72b36a80b034d5f0a1435470d27557 | Ancestral integral de #31; recomendar fechamento como supersedido, sem merge isolado. |
| [#31](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/31) | BLOCKED | 5658e9c7e633a1f9a06e7d374f9a2d63ad22073f | aa58d70d84c6134216f8f15a131edf060c4dce81 | NO-GO físico; 5658e9c encaminha bancada para #34. Não mesclar. |
| [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32) | HISTORICAL — integrado | 7ed1a545146ac12072a15a5bdcdea92008170051 | 7ed1a545146ac12072a15a5bdcdea92008170051 | Governança existente adotada, não duplicada. |
| [#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33) | HISTORICAL — integrado | f4cd6a8c0f50e980b4a8590e6eef3b0a57b6483a | f4cd6a8c0f50e980b4a8590e6eef3b0a57b6483a | Acervo integrado com erratas; evidência, não norma. |
| [#34](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/34) | ACTIVE | 8a93a27a660f59e7b532ea6f9db1a6a3561caffe | aa58d70d84c6134216f8f15a131edf060c4dce81 | Bancada main-safe 75/81 sem N1; GO restrito offline, não PASS Revit. Sem merge autorizado. |
| [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35) | HISTORICAL — integrado | 25ee78a927322e7b8e46a5b47e95d932c1caf84b | 25ee78a927322e7b8e46a5b47e95d932c1caf84b | Diff próprio reconciliado e integrado com erratas; evidência, não norma. |

Classificações deste registro; PRs antigos não foram fechados e branches
não foram removidas. Todos os 35 PRs/refs estão inventariados.
Inicialmente nove abertos/draft: #7/#8/#21/#28/#30/#31/#33/#34/#35.
Após #33/#35 restam sete; PR da consolidação é separado.

## Governança #32

Integrado em 2026-09-09T14:44:50Z, merge
aa58d70d84c6134216f8f15a131edf060c4dce81, HEAD
7ed1a545146ac12072a15a5bdcdea92008170051. Checks push/PR SUCCESS.
Workflow check-project-status.yml valida entrega desde merge-base:
checkpoint versionado, main observada, ancestralidade, hashes e links.
12 testes existentes passaram nesta missão. Não valida verdade física/normativa.
Proteção inicial protected=false; não alterada.

## Referências integradas

#33 original 51ed8c2, base 0ff784e, conflitava com main. Incorporada main
por merge na branch, sem reescrever histórico; seção evidencial 30→40,
preservando regras. HEAD final f4cd6a8c0f50e980b4a8590e6eef3b0a57b6483a.
Merge normal **59c0352e4a3f66349a08b1d3f1ac5b079ce72bf9**.
260 testes, JSON offline e checks push/PR passaram.
[Revisão](revit_reference_extraction/REVIEW_2026-09-10.md).

#35 original 5f1a0c4 empilhado em 51ed8c2; diff próprio 36 arquivos.
Incorporada main com #33 por merge, sem force-push; comparação final exclui
herança integrada. Seção evidencial 31→41.
HEAD final 25ee78a927322e7b8e46a5b47e95d932c1caf84b.
Merge normal **6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9**.
260 testes, JSON offline e checks push/PR passaram.
[Revisão](revit_reference_extraction/butanta-r08-lt/REVIEW_2026-09-10.md).

Scripts lidos estaticamente, JSON conferidos. Nenhum Revit executado.
Raw/intermediários ausentes impedem regeneração integral pelo Git.
Erratas documentadas; JSON originais preservados; sem benchmark/norma nova.

## Trabalho posterior aos relatos conhecidos

#31 avançou de 05030d2 para 5658e9c, com contenções e evidências beta.
Código final 09b6ea0: **1112 passed/2 failed**, 2611,63s, log publicado;
supera relato de 1003/2 sem log. TGD compensators 52→66; TP1 binding 8→9
e INSIDE_DOOR 0→7. Preflight TGD 692 invasões/784 colisões; TP1 500/0. NO-GO.

#34 HEAD 8a93a27, código 8cdd33f sobre aa58d70: **1027 passed/2 failed**,
3021,98s; TGD compensators 52→61, TP1 binding 8→9.
Bancada uniforme derivada 340 cm, TP1 75/81: 187 blocos, L sem aberturas.
Não equivale às alturas nativas 260/280 cm nem libera T/X/projeto inteiro.
CI desses candidatos é governança, não aprovação Revit.

Fontes fixadas:

- [Checkpoint final #31](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/5658e9c7e633a1f9a06e7d374f9a2d63ad22073f/docs/checkpoints/2026-09-09-beta-etapa4.md)
- [Relatório beta N1](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/5658e9c7e633a1f9a06e7d374f9a2d63ad22073f/docs/RELATORIO_BETA_2026-09-09.md)
- [Proveniência consolidada #31](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/5658e9c7e633a1f9a06e7d374f9a2d63ad22073f/docs/checkpoints/evidence/beta-consolidated-final-v2.json)
- [Checkpoint #34](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/8a93a27a660f59e7b532ea6f9db1a6a3561caffe/docs/checkpoints/2026-09-09-beta-main-safe.md)
- [Proveniência consolidada #34](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/8a93a27a660f59e7b532ea6f9db1a6a3561caffe/docs/checkpoints/evidence/main-safe-consolidated.json)
- [Preparação #28 histórica](https://github.com/Arcanjog1/MeuBotao.pushbutton/blob/0596e78eadcbebd9369dbd54272b44952b8211ed/docs/CR_B_INTEGRATION_PREPARATION.md)

## Beta 1 — lacuna concreta preservada

**CANDIDATO — VALIDAÇÃO REVIT PENDENTE**.
Branch informada: claude/revit-solver-perf-diagnosis-6dfd89.
SHA informado: a5081d85b3fcb79cbb2f8c99dadcd08b4c186f8b.
Ausente das refs remotas buscadas; API retorna HTTP 422 “No commit found for SHA”.
Trabalho posterior e merge-base não verificáveis sem localizar/publicar clone.
Não inventar HEAD atual ou afirmar que o trabalho não existe.
Localização solicitada ao usuário enquanto a missão continuava.

Nenhuma branch beta foi apagada, sobrescrita ou integrada. #34 não substitui
validação do analyze síncrono posterior. Nenhum PASS ou ensaio Revit novo.
Lacuna não bloqueia arquitetura/documentação.
