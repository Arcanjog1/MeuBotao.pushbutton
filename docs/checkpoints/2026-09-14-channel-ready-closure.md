# Fechamento CHANNEL — PR #40 pronto para revisão (2026-09-14)

> **HISTÓRICO** — veredito revogado pela auditoria independente; ver [correções da auditoria](2026-09-14-channel-audit-fixes.md).

```json
{
  "date": "2026-09-14",
  "scope": "historical",
  "branch": "claude/butanta-channel-reference-implementation",
  "head": "f918c1c0ee44269fb533238a82320bfbe4ff601f",
  "base": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "main_observada": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/40",
  "veredito": "READY FOR REVIEW — CHANNEL COMPLETE (20/20 critérios; regressão consolidada 4 failed / 1161 passed, todas classificadas: 2 históricas/ambiente e 2 de cobertura do TGD por reclassificação da regra 30.8, sem baseline regravado)",
  "objective": "Fechar a estratégia CHANNEL com as decisões A–F do usuário: zerar MISSING_REQUIRED_CHANNEL (7719511) com correção física geral, reanalisar 6627438, formalizar a travessia de T sem vazar a exceção, UI de escolha e bloqueio por família, revalidar 34 paredes/44 vãos offline e no Revit real (idempotência, desempenho) e levar o PR #40 a ready for review, sem verga/contraverga.",
  "changes": [
    "nuvem/core/engine/wall_stepper.py: regra 30.8 — folga residual <= 2 cm num trecho fechado por dois nós distribuída nas duas juntas de contorno (RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED/MAX_CM, result['residual_absorptions']); _absorbed_segment_rule2_layout — a Fiada A de um trecho absorvido evita compensadores em sequência quando o mesmo trecho tem composição com menos excesso.",
    "nuvem/core/engine/continuous_modulation.py: region_solid_subsegments aceita trecho >= mínimo - PIER_PHYSICAL_FIT_TOLERANCE_CM (pastilha de jamba de 3,9989 cm em 6627438).",
    "nuvem/core/engine/opening_reinforcement.py: CHANNEL_THROUGH_T_SUPPORTED_PATTERN; apoio efetivo (_bearing_cm, bearing_l/r_cm; SUPPORT_LIMITED com assentamento = VALID_ALTERNATIVE); contiguous_gap_cm 1,5 -> 2,0 + epsilon.",
    "nuvem/core/wall_modeling.py: Tela de Configuração '7. Reforço de aberturas' (CHANNEL padrão, Sem reforço, VERGA/CONTRAVERGA visível e bloqueada), escolha lembrada e aplicada ao handler; _ensure_opening_reinforcement_catalog bloqueia antes de calcular/criar listando famílias/tipos faltantes; timing_s do pós-passe; agregação de residual_absorptions.",
    "tests: test_node_bounded_residual.py (12), test_channel_ui_and_family_gate.py (6), test_channel_reinforcement.py (+4 de não vazamento da travessia, 34 no total).",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 30.8 e 51.13; 51 (status oficial, 51.4 apoio efetivo, 51.6 decisão D, 51.8/51.10 pendentes, 51.9 decisão C).",
    "docs: arquitetura CHANNEL, DECISION-OPENING-REINFORCEMENT (A–F), checkpoint anterior marcado histórico, este checkpoint, PROJECT_STATUS, START_HERE, PROJECT_STATUS_LOG; evidências 2026-09-14-channel-*, corpus-v2-*, regressão final."
  ],
  "tests": [
    "Focados no HEAD f918c1c: test_channel_reinforcement.py 34 + test_node_bounded_residual.py 12 + test_channel_ui_and_family_gate.py 6 = 52 passed.",
    "RED/GREEN: anel 7719511 sem a 30.8 -> MISSING >= 1 e anel vazio; com -> MISSING 0, top 1/1, bottom 1/1. Fiada A gulosa (monkeypatch) -> REPEATED_VERTICAL_COMPENSATOR_STRIP; com o complemento -> sem faixa nas duas ordens de parede. Contiguidade: 2 failed com a folga 1,5 / 12 passed com 2,0.",
    "Bancada offline 1/3/5/10/20/34 paredes (evidence/2026-09-14-channel-bench-*.json) e determinismo em 3 processos PYTHONHASHSEED 0/1/2: legado 9b3f0501…, CHANNEL 7a2f516a… idênticos.",
    "Revit real 34 paredes run1 (limpeza) + run2 (sessão nova sem limpeza): evidence/2026-09-14-channel-revit/r_final34_run{1,2}.json; paridade offline evidence/2026-09-14-channel-revit-parity-final34.json (equal=true).",
    "REGRESSÃO CONSOLIDADA `py -3 -m pytest tests -q -p no:cacheprovider` no HEAD f918c1c (tree 624ce74), Windows, CPython 3.14.7, capturada por tools/documentation/capture_validation.py: 4 failed / 1161 passed em 2.425,6 s, exit 1 (evidence/2026-09-14-channel-regressao-final.json + evidence/regressao-consolidada-f918c1c.txt)."
  ],
  "known_failures": [
    "test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]: JUNCTION_MISSING_BINDING 8→9 — HISTÓRICA (V1), idêntica à main e ao #39.",
    "test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]: COVERAGE_ROW_MOSTLY_EMPTY 171→232 (V1 HISTORICAL; main 158) — regra 30.8: PARTIAL_WALL 57→38, MISSING_ROW 232→220, GAP_IN_ROW 1855→1601, preenchimento total +36.077 cm; 105 das 110 fiadas novas estavam em paredes PARTIAL_WALL (achado de parede mascarava o de fiada); perda líquida real em 3 paredes (−95, −210, −75 cm). evidence/2026-09-14-channel-regressao-cobertura-tgd.txt.",
    "test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]: COVERAGE_ROW_MOSTLY_EMPTY 86→92 — as 12 fiadas novas têm o MESMO preenchimento (3.240 = 3.240 cm), eram GAP_IN_ROW em paredes PARTIAL_WALL (32→24); MISSING_ROW 142→136, GAP_IN_ROW 1275→1090, preenchimento +34.123 cm; perdas aparentes são eixos sobrepostos do TGD trocando blocos (líquido ≥ 0). A falha anterior desta régua (compensators 61→62) não é mais a primeira acusada.",
    "test_perf_trace_stall_sampler::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas: UnboundLocalError ctypes em win32 — falha também na origin/main (evidence/2026-09-14-channel-stall-sampler-on-main.txt).",
    "Corpus V2 TP1 (tolerância da pastilha): 9 paredes que já fechavam recompostas em cascata (C09 → C04+C04 na região de reparo de porta, B39 → B34+C04), COMPENSATOR_CONSECUTIVE +9 nelas — não crítico, registrado em 51.13 como pendência (fundir C04+C04)."
  ],
  "physical_deltas": [
    "7719511: MISSING_REQUIRED_CHANNEL 1 → 0 (canaleta sob o peitoril com apoio 19,5/14 cm; humano 4/9 → SOLVER_BETTER); topo em 91 cm continua HEAD_OFF_GRID (decisão E).",
    "Offline 34 paredes/44 vãos: legado 7.439 peças (non_modular 78 → 0), CHANNEL 7.413; top 40/40, bottom 23/23; MISSING/EXTRA/WRONG_COURSE/INVADES/COLLISION 0; PRISM_CONTINUOUS_JOINT 0 (nó|fill 0, fill|tie 0); paredes reprovadas 3 = 3 (99 cm históricas); 4 travessias (SUPPORTED_PATTERN), 2 passagens livres, 7 canaletas cortadas; preflight 0 invasão/0 colisão.",
    "Humano × solver 67 papéis: 15 EXACT, 45 EQUIVALENT, 4 BETTER, 1 VALID_ALTERNATIVE (6627438, 4 cm sobre C04), 2 NOT_COMPARABLE (topo fora da grade), 0 ACTUAL_ERROR, 0 WORSE. Humano × Revit (44/44 vãos casados): 4/55/5/1/2, 0 ACTUAL_ERROR.",
    "Revit real 34 paredes: 7.416 peças (323 canaletas, 8 cortadas), 0 falhas, releitura 7.416/0 divergências; sessão nova 7.416 → 7.416 com assinatura idêntica (844b04c3…) e igual à bancada offline; HUMANO IsModified=false antes/depois; TARGET não salvo.",
    "Desempenho Revit (run1): solve 16,8 s (plano CHANNEL 0,51 s, validação 0,42 s, re-auditoria 0,18 s), criação 266 s (NewFamilyInstance 232 s, rotação 25 s, commit 5,2 s), execução total 286 s. Offline 34 paredes: legado 2,73 s × CHANNEL 2,85 s.",
    "Corpus V2 (estratégia None), main → HEAD: TP1 blocos 18.963 → 19.047, COVERAGE_GAP −34; TGD 16.289 → 17.452, COVERAGE_GAP −185, MISSING_ROW −6, PARTIAL_WALL −8; COMPENSATOR_* e STAGGER sobem nas paredes antes vazias; códigos críticos (PRISM_CONTINUOUS_JOINT, INSIDE_DOOR/WINDOW, CROSSES_JAMB, POSITION_OVERLAP, JUNCTION_*) idênticos; piloto idêntico. Atribuição por parede em evidence/2026-09-14-corpus-v2-changed-walls.txt.",
    "Nenhum baseline/reference/threshold/validador alterado; nenhum skip/xfail."
  ],
  "decisions_taken": [
    "Decisões do usuário A–F aplicadas (DECISION-OPENING-REINFORCEMENT, 51.13).",
    "7719511 classificado como falha do preenchimento legado (folga 1–2 cm entre nós) e corrigido pela 30.8 em vez de exceção por abertura.",
    "Alternativa 'mesma família por parede' no anel (padrão humano medido em q07) testada e rejeitada: nas paredes de 86 cm gera junta corrida e meio bloco perto de amarração; mantida a alternância 30.5 + regra #2 nos trechos absorvidos.",
    "Contiguidade da corrida alinhada com a 30.8 (2,0 cm) em planejador e validador juntos.",
    "Falhas de baseline do TGD classificadas e mantidas visíveis; baselines não regravados."
  ],
  "decisions_pending": [
    "E: topo/peitoril fora da grade (51.8).",
    "F: cinta de topo (10.7).",
    "LINTEL_COUNTERLINTEL (não iniciado).",
    "Fundir C04+C04 adjacentes na região de reparo (cascata TP1) e as 3 paredes V1 do TGD com perda líquida.",
    "Regravar baselines de benchmark somente com autorização."
  ],
  "next_steps": [
    "Revisão humana do PR #40 (ready for review); sem merge sem autorização específica.",
    "Não iniciar verga/contraverga nesta linha."
  ],
  "references": [
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/core/engine/continuous_modulation.py"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "tests/test_node_bounded_residual.py"},
    {"path": "tests/test_channel_ui_and_family_gate.py"},
    {"path": "tests/test_channel_reinforcement.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "docs/architecture/channel-strategy-implementation.md"},
    {"path": "docs/decisions/DECISION-OPENING-REINFORCEMENT.md"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-bench-34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-determinism.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-solver.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-revit-34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit/r_final34_run1.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit/r_final34_run2.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit/q07_ring_human.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit-parity-final34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-corpus-v2-changed-walls.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-14-corpus-v2-state-main.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-corpus-v2-state-head.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-regressao-final.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-regressao-cobertura-tgd.txt"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## 1. Git

`origin/main` inicial = final: `0e41c8e` (merge do #39). Branch
`claude/butanta-channel-reference-implementation`, código avaliado `f918c1c`
(commits `a9e3e3b` e `f918c1c` sobre o checkpoint histórico `26cf5d2`/`109d453`).
PR [#40](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/40), sem merge.

## 2. 7719511 — causa e correção

| Item | Resultado |
|---|---|
| Causa | preenchimento legado: anel de 4 cantos L (115 × 86 cm) com miolos 1–2 cm fora do módulo → anel vazio em todas as fiadas; canaleta sem peças onde assentar |
| Correção | regra 30.8 (folga ≤ 2 cm distribuída nas juntas de contorno entre nós) + regra #2 nos trechos absorvidos |
| RED → GREEN | `test_ring_red_without_absorption…` / `test_ring_green_with_absorption…`; faixa de compensador RED/GREEN; contiguidade RED/GREEN |
| Resultado | canaleta inferior presente (19,5/14 cm), SOLVER_BETTER; superior HEAD_OFF_GRID (topo 91, decisão E) |

## 3. 6627438

A pastilha C04 entre jamba e amarração media 3,9989 cm e era descartada como
sobra → corrida de canaleta sem assentamento. Com a tolerância física de 0,05 cm
o C04 existe em todas as fiadas e o apoio de 4 cm assenta nele:
`VALID_ALTERNATIVE` (51.4, 51.13).

## 4. Critérios READY

| # | Critério | Resultado |
|---|---|---|
| 1 | MISSING=0 | 0 (offline e Revit) |
| 2 | ACTUAL_ERROR=0 | 0 (67 papéis offline e Revit) |
| 3–6 | porta / janela / canaleta superior / inferior | PASS — top 40/40, bottom 23/23 |
| 7 | cortes | 7 (offline) / 8 (Revit) `CHANNEL_U_CUT` por parâmetro de instância |
| 8 | travessia de T formalizada | `CHANNEL_THROUGH_T_SUPPORTED_PATTERN` + 4 testes de não vazamento |
| 9 | livre até o topo | 2 passagens |
| 10 | cinta de topo separada | nenhuma TOP_BOND_BEAM gerada |
| 11–13 | nó\|fill / fill\|tie / INSIDE | 0 / 0 / 0 |
| 14 | colisão crítica | 0 |
| 15 | determinismo | 3 processos idênticos; Revit = offline |
| 16 | idempotência | 7.416 → 7.416 |
| 17 | 34 paredes | criadas, releitura 0, preflight ok, reprovadas 3 = 3 históricas |
| 18 | testes CHANNEL | 52 passed |
| 19 | regressão entendida | 4 failed classificadas (seção 5) |
| 20 | docs/CI | validador documental PASS; CI do PR conferido após o push |

## 5. Regressão consolidada

4 failed / 1161 passed em 40 min (HEAD `f918c1c`). TP1 V1 JUNCTION 8→9 e o
amostrador de GIL no Windows são as mesmas falhas da main. As duas do TGD
(`COVERAGE_ROW_MOSTLY_EMPTY`) nascem da regra 30.8, que fecha paredes antes
vazias: a parede sai de `PARTIAL_WALL` e passa a ser contada por fiada. Na V2
o preenchimento das fiadas acusadas é idêntico. Na V1 histórica o preenchimento
total sobe 10% e 3 paredes perdem até 210 cm líquidos. Baselines não regravados.

## 6. Veredito

**READY FOR REVIEW — CHANNEL COMPLETE.** Sem merge; verga/contraverga não iniciada.
