# CHANNEL — correções da auditoria independente do PR #40 (2026-09-14)

> **HISTÓRICO** — superado pelo [fechamento final](2026-09-14-channel-final-merge.md).

```json
{
  "date": "2026-09-14",
  "scope": "historical",
  "branch": "claude/butanta-channel-reference-implementation",
  "head": "612f9f3b2f950e34ddc6b817f6e4c5d620dfe2a2",
  "base": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "main_observada": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/40",
  "veredito": "READY FOR REVIEW — CHANNEL COMPLETE (os cinco pontos bloqueantes da auditoria fechados; limitações declaradas: 7719511 com a 30.8 desligada, 6672349 com 4 cm igual ao humano; decisão pendente: passagem livre humana abre até as faces dos nós)",
  "objective": "Reconciliar o PR #40 com a auditoria independente: sem regressão crítica no legado (30.8), P0 do FREE_TO_TOP comprovadamente corrigido, comparador humano × solver endurecido, 6627438 com causa/RED/correção, CHANNEL nunca default na UI, determinismo IronPython sem id()/ordem de dict, result['candidates'] como fonte única, regressão e Revit real refeitos. Sem merge, sem verga/contraverga.",
  "changes": [
    "nuvem/core/engine/wall_stepper.py: RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED=False; lógica da 30.8 e o teste 'vão dentro do trecho degradado' em funções auxiliares (_residual_node_bounded_absorption, _interval_inside_any_span) — quebra do IronPython no Revit.",
    "nuvem/core/engine/continuous_modulation.py: JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED=False (tolerância de ruído da pastilha só como parâmetro).",
    "nuvem/core/engine/opening_reinforcement.py: free_to_top_openings/openings_extended_to_top (decisão pré-solve, planejador sem remoção, FREE_TO_TOP_NOT_PRESOLVED); validador com CHANNEL_OPENING_OVERCUT, CHANNEL_FREE_TO_TOP_NOT_OPEN, CHANNEL_ORPHAN_PIECE e reference_course_candidates; _physical_key no lugar de id(); blocker_l/r e geometric_support_cm; SUPPORT_LIMITED < 9 cm = KNOWN_LIMITATION.",
    "nuvem/core/wall_modeling.py: pré-solve da passagem livre; _channel_tie_parity_trials (paridade do nó T com reconstrução real e gates: validador, reprovadas, juntas corridas, não modulares, colisões, invasões, compensadores encostados, desencontro, apoios); _unify_candidates_with_courses; UI default NONE e estratégia passada por _show_post_creation_window(opening_reinforcement_strategy=...).",
    "tests/test_channel_audit_fixes.py (novo, 25 testes); tests/test_channel_ui_and_family_gate.py reescrito (10 testes).",
    "docs/checkpoints/evidence/_scripts/channel_strict_compare.py (comparador endurecido) e drivers human-vs-solver/human-vs-revit; 2026-09-14-legacy-signature.py; 2026-09-14-parity-trial-attribution.py.",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 30.8 (desligada), 51 (nunca default), 51.9 (regra do vão + CONFLITO com o humano), 51.13 (itens superados), 51.14 (correções da auditoria).",
    "docs: arquitetura, DECISION-OPENING-REINFORCEMENT, checkpoint anterior histórico, PROJECT_STATUS, START_HERE, PROJECT_STATUS_LOG."
  ],
  "tests": [
    "Focados (HEAD de código 8019ce2): test_channel_audit_fixes 25 + test_channel_reinforcement 34 + test_node_bounded_residual 12 + test_channel_ui_and_family_gate 10 + preflight/C04/paridade relacionados = 198 passed.",
    "RED no código anterior 4695925 (testes novos copiados): 26 failed / 9 passed (evidence/2026-09-14-audit-fixes-red-on-4695925.txt); P0 comportamental na sonda (evidence/2026-09-14-free-to-top-p0-probe.txt).",
    "Legado = main: assinatura BUTANTÃ 34 paredes 94541746… na main e no HEAD (_scripts/2026-09-14-legacy-signature.py); corpus por parede em coordenada de mundo TGD V1/V2 e TP1 V1/V2 com 0 paredes alteradas (evidence/2026-09-14-audit-corpus-legacy-equivalence.txt); Revit real legado HEAD = main (evidence/2026-09-14-channel-revit/r_legacy_{main,head}_solve.json, 7.253 peças, mesma assinatura).",
    "Bancada 1/3/5/10/20/34 e determinismo 3 processos: legado 94541746…, CHANNEL b509a425… (evidence/2026-09-14-channel-determinism.txt).",
    "Revit real 34 paredes CHANNEL run1+run2 (evidence/2026-09-14-channel-revit/r_final34_run{1,2}.json) e paridade offline equal=true 42e61f52… (evidence/2026-09-14-channel-revit-parity-final34.json).",
    "REGRESSÃO CONSOLIDADA `py -3 -m pytest tests -q -p no:cacheprovider` no HEAD 612f9f3, Windows, CPython 3.14.7, capture_validation.py: 3 failed / 1191 passed em 2.091,8 s, exit 1 (evidence/2026-09-14-channel-regressao-auditoria.json + evidence/regressao-consolidada-audit.txt)."
  ],
  "known_failures": [
    "test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]: JUNCTION_MISSING_BINDING 8→9 — histórica (V1), idêntica à main 0e41c8e/#39.",
    "test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]: compensators 61→62 — idêntica à main/#39 (legado do HEAD = main parede a parede).",
    "test_perf_trace_stall_sampler::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas: UnboundLocalError ctypes em win32 — falha também na origin/main.",
    "7719511 (canaleta inferior): KNOWN_LIMITATION — trecho não modular do anel com a 30.8 desligada (opção B).",
    "6672349: apoio 4 cm igual ao humano; a inversão de paridade foi rejeitada pelo gate (+12 compensadores encostados em W018) — KNOWN_LIMITATION."
  ],
  "physical_deltas": [
    "TGD V1 e V2: sem nova regressão de COVERAGE (legado idêntico à main); a regressão crítica COVERAGE_ROW_MOSTLY_EMPTY 171→232 / 86→92 do HEAD anterior não existe mais.",
    "FREE_TO_TOP BUTANTÃ (vãos 6919324/6919219): alvenaria termina nas jambas (B19[1395,1414], B19[1570,1589], B19[1605,1624], B19[1780,1799] na fiada 11); OVERCUT/NOT_OPEN/ORPHAN 0; antes aberto 1394–1590 e 1604–1800.",
    "6627438: offline apoio 19/39 (efetivo 19/33), Revit efetivo 24/33, humano 34/39, mesma paridade no nó 382 (principal passa), sem travessia → PHYSICALLY_EQUIVALENT; antes 34/4.",
    "Offline 34 paredes/44 vãos CHANNEL: 7.222 peças, top 40/40, bottom 22/23, EXTRA/WRONG/INVADES/COLLISION/OVERCUT/NOT_OPEN/ORPHAN 0, PRISM 0, reprovadas 3 = 3; delta benchmark × legado COVERAGE_GAP_IN_ROW +6 (passagens livres), PRISM_STAGGER_BELOW_TARGET +1.",
    "Humano × solver endurecido (67 papéis): 1 EXACT, 14 EQUIVALENT, 9 BETTER, 37 VALID_ALTERNATIVE (20 paridade de canto, 17 desencontro abaixo do alvo), 2 KNOWN_LIMITATION, 2 NORMATIVE_DECISION, 2 NOT_COMPARABLE, 0 ACTUAL_ERROR, 0 SOLVER_WORSE.",
    "Revit real 34 paredes: 7.238 peças (321 canaletas, 6 cortadas), 0 falhas, releitura 0, sessão nova 7.238 → 7.238; humano × Revit endurecido 44/44: 14 EQUIVALENT, 9 BETTER, 38 VALID_ALTERNATIVE, 2 KNOWN_LIMITATION, 2 NORMATIVE_DECISION, 2 NOT_COMPARABLE, 0 ACTUAL_ERROR, 0 SOLVER_WORSE; HUMANO IsModified=false; TARGET não salvo.",
    "Desempenho: solve CHANNEL no Revit 44,6 s (antes 17 s; a tentativa de paridade reconstrói o motor por candidato), plano 0,23 s, validação 0,97 s, re-auditoria 0,30 s, criação 237 s; offline legado 2,3 s × CHANNEL 12,4 s.",
    "Nenhum baseline/reference/threshold alterado; nenhum skip/xfail."
  ],
  "decisions_taken": [
    "Opção B do usuário: 30.8 desligada; tolerância da pastilha também desligada (mudava o legado do TP1).",
    "Passagem livre resolvida no motor (vão estendido até o topo) em vez de remoção pós-solve.",
    "6627438 por tentativa de paridade com gates, não por regra obrigatória (evidência humana conflitante 6627438 × 6672349).",
    "Apoio < 9 cm nunca é VALID_ALTERNATIVE: KNOWN_LIMITATION se igual ao humano, SOLVER_WORSE se pior.",
    "Passagens livres em que o humano abre até as faces dos nós classificadas NORMATIVE_DECISION (regra do usuário prevalece, conflito registrado)."
  ],
  "decisions_pending": [
    "Passagem livre: seguir o humano (abrir até as faces dos nós, sem o pilar entre vãos) ou manter só o vão (regra atual).",
    "Religar a 30.8 com baseline regravado ou corrigir a métrica COVERAGE_ROW_MOSTLY_EMPTY (7719511).",
    "E: topo/peitoril fora da grade; F: cinta de topo.",
    "Custo de tempo da tentativa de paridade (solve CHANNEL 44,6 s no Revit)."
  ],
  "next_steps": [
    "Revisão humana do PR #40; sem merge sem autorização específica.",
    "Não iniciar verga/contraverga nesta linha."
  ],
  "references": [
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/core/engine/continuous_modulation.py"},
    {"path": "tests/test_channel_audit_fixes.py"},
    {"path": "tests/test_channel_ui_and_family_gate.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "docs/architecture/channel-strategy-implementation.md"},
    {"path": "docs/checkpoints/evidence/_scripts/channel_strict_compare.py"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-solver.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-revit-34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit-parity-final34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-audit-corpus-legacy-equivalence.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-14-free-to-top-p0-probe.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-14-audit-fixes-red-on-4695925.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-regressao-auditoria.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-determinism.txt"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Tabela da auditoria

| Achado | Antes | Fix | Teste | Depois | Status |
|---|---|---|---|---|---|
| 30.8 | TGD V1 `COVERAGE_ROW_MOSTLY_EMPTY` 171→232, V2 86→92 | desligada (opção B); lógica em função auxiliar | `test_rule_30_8_and_jamb_noise_tolerance_are_off_by_default`; corpus por parede | legado = main (BUTANTÃ, TGD V1/V2, TP1 V1/V2: 0 paredes alteradas; Revit) | FECHADO (7719511 = limitação) |
| FREE_TO_TOP | peça que cruza jamba removida; aberto 1394–1590 (jambas 1414–1570) | decisão pré-solve + vão estendido até o topo; validador OVERCUT/NOT_OPEN/ORPHAN | 5 posições de jamba, RED do planejador e do validador | alvenaria até as jambas; 0 overcut/órfã | FECHADO (conflito com o humano registrado) |
| UI default | CHANNEL | NONE | `test_default_is_none_and_old_installation_stays_legacy` | NONE | FECHADO |
| Persistência UI | handler relia o disco | estratégia passada pelo formulário | `test_failed_persistence_preserves_the_current_choice`, `test_execution_receives_the_form_choice_never_the_disk` | escolha atual preservada | FECHADO |
| 6627438 | 34/4 cm, "VALID_ALTERNATIVE" | tentativa de paridade do nó T com gates | RED `test_red_engine_parity_leaves_4cm…`, GREEN `test_green_parity_trial…` | 19/39 offline, 24/33 efetivo Revit; humano 34/39; mesma paridade | FECHADO |
| Comparador | FREE_TO_TOP=EXACT; VALID com apoio > 0,5 | juntas, paridade, prisma, amarração, apoio efetivo, bordas abertas | driver offline e Revit | 0 ACTUAL_ERROR, 0 WORSE, diferenças com motivo | FECHADO |
| Determinismo | `id()`/ordem de dict | `_physical_key` | `test_plan_is_independent_of_input_piece_order`, 3 processos | idêntico | FECHADO |
| result candidates | lista pré-CHANNEL | `_unify_candidates_with_courses` | `test_result_candidates_equal_flatten…` | fonte única | FECHADO |
| TGD V1 | falha nova COVERAGE | legado = main | regressão consolidada | passa | FECHADO |
| TGD V2 | falha COVERAGE | legado = main | regressão consolidada | só a histórica compensators 61→62 | FECHADO |
| Revit real | 7.416 com 30.8; depois erro IronPython | correção IronPython | run1/run2 + paridade | 7.238 → 7.238, 0 falhas/divergências | FECHADO |
| Humano × solver | 0 ACTUAL_ERROR com critério permissivo | comparador endurecido | offline + Revit | 0 ACTUAL_ERROR, 0 WORSE | FECHADO |

## Veredito

**READY FOR REVIEW — CHANNEL COMPLETE.** Sem merge; verga/contraverga não iniciada.
