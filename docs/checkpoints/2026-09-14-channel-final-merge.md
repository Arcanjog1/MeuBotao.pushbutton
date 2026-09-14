# CHANNEL — fechamento final e merge condicional do PR #40 (2026-09-14)

```json
{
  "date": "2026-09-14",
  "scope": "current",
  "branch": "claude/butanta-channel-reference-implementation",
  "head": "aba95147340fcc3cade4646ec91f1a41d6cfc928",
  "base": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "main_observada": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/40",
  "veredito": "READY FOR MERGE — CHANNEL COMPLETE (18/18 gates; merge normal autorizado pelo usuário)",
  "objective": "Fechar os últimos pontos antes do merge: passagem livre contínua de face de nó a face de nó (decisão do usuário), 30.8 desligada com 7719511 como limitação, off-grid e cinta de topo pendentes/fora do escopo, eliminar a regressão de tempo das tentativas de paridade sem mudar o resultado físico, refazer comparação humano × solver, Revit real, regressão consolidada e merge normal.",
  "changes": [
    "nuvem/core/engine/opening_reinforcement.py: continuous_free_passages (detecção geométrica), openings_extended_to_top com vãos sintéticos de face a face, _footprint_on_wall/_pieces_in_wall_region, validação da passagem contínua, course_wall_buckets/cached_strip_rows.",
    "nuvem/core/engine/wall_stepper.py: WALL_FILL_MEMO (memo exato de solve_wall_free_fill por chave canônica), OBB_MEMO, _plain_clone em três níveis.",
    "nuvem/core/wall_modeling.py: wrapper de memo só para CHANNEL, passagem contínua no pré-solve, métricas em dois estágios (gates baratos antes do plano), reaproveitamento do plano/validação, timing permanente das tentativas.",
    "tests/test_channel_audit_fixes.py: passagem contínua (3 geometrias positivas, 3 não equivalentes, validador RED), identidade da otimização em 6 fixtures, chave do memo sem id().",
    "docs/checkpoints/evidence/_scripts/channel_strict_compare.py: bordas livres por ocupação geométrica (inclui paredes que chegam nos nós); NORMATIVE_DECISION removido.",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 51.9 (regra aprovada da passagem contínua), 51.15 (fechamento e desempenho); arquitetura, decisão, checkpoint anterior histórico, status."
  ],
  "tests": [
    "Focados: test_channel_audit_fixes + test_channel_reinforcement + test_node_bounded_residual + test_channel_ui_and_family_gate + preflight/C04/paridade = 213 passed.",
    "Identidade da otimização: assinatura completa (peças, plano, validação, decisões, auditorias) BUTANTÃ 34 paredes com e sem memo a663b943… = a663b943…; 6 fixtures idênticas no teste.",
    "Determinismo 3 processos: legado 94541746…, CHANNEL 7082e71e… (evidence/2026-09-14-channel-determinism.txt).",
    "Legado = main: BUTANTÃ 94541746…; corpus TGD V1/V2 e TP1 V1/V2 com 0 paredes alteradas (evidence/2026-09-14-audit-corpus-legacy-equivalence.txt).",
    "Revit real 34 paredes run1+run2 com criação (evidence/2026-09-14-channel-revit/r_final34_run{1,2}.json); paridade offline equal=true 112ccde5… (evidence/2026-09-14-channel-revit-parity-final34.json); desempenho antes/depois (evidence/2026-09-14-channel-revit/r_perf_*.json).",
    "REGRESSÃO CONSOLIDADA `py -3 -m pytest tests -q -p no:cacheprovider` no HEAD aba9514, Windows, CPython 3.14.7, capture_validation.py: 3 failed / 1206 passed em 2.123,5 s, exit 1 (evidence/2026-09-14-channel-regressao-merge.json + evidence/regressao-consolidada-final.txt)."
  ],
  "known_failures": [
    "test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]: JUNCTION_MISSING_BINDING 8→9 — histórica, idêntica à main.",
    "test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]: compensators 61→62 — idêntica à main (legado do HEAD = main parede a parede).",
    "test_perf_trace_stall_sampler::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas: UnboundLocalError ctypes em win32 — falha também na origin/main.",
    "7719511 (canaleta inferior): KNOWN_LIMITATION com a 30.8 desligada.",
    "6672349: apoio 4 cm igual ao humano (inversão de paridade rejeitada por +12 compensadores encostados) — KNOWN_LIMITATION."
  ],
  "physical_deltas": [
    "Passagem contínua BUTANTÃ (vãos 6919324/6919219): fiadas acima do topo livres de 1394 a 1800 (faces dos nós 1387 e 1807), pilar não reconstruído, parede que chega no nó 1597 termina na face — EXACT_MATCH com o humano offline e no Revit.",
    "Offline 34 paredes/44 vãos CHANNEL: 7.210 peças; top 40/40, bottom 22/23; EXTRA/WRONG_COURSE/INVADES/COLLISION/OVERCUT/NOT_OPEN/ORPHAN 0; PRISM 0 (nó|fill 0, fill|tie 0); preflight 0 invasão/0 colisão; reprovadas 3 = 3; delta benchmark × legado COVERAGE_GAP_IN_ROW +3 (passagens), PRISM_STAGGER_BELOW_TARGET +2.",
    "Humano × solver (67 papéis): 3 EXACT, 14 EQUIVALENT, 9 BETTER, 37 VALID_ALTERNATIVE, 2 KNOWN_LIMITATION, 0 NORMATIVE_DECISION, 2 NOT_COMPARABLE, 0 SOLVER_WORSE, 0 ACTUAL_ERROR. Humano × Revit (44/44): 2 EXACT, 14 EQUIVALENT, 9 BETTER, 38 VALID_ALTERNATIVE, 2 KNOWN_LIMITATION, 0 NORMATIVE_DECISION, 2 NOT_COMPARABLE, 0 WORSE, 0 ACTUAL_ERROR.",
    "Revit real 34 paredes: 7.222 planejadas = 7.222 criadas, 0 falhas, releitura 0 divergências, sessão nova 7.222 → 7.222, assinatura igual à offline; HUMANO IsModified=false; TARGET não salvo.",
    "Desempenho Revit (solve 34 paredes): CHANNEL 44,6 s → 24,2 s (legado 19,2 s); reconstruções 2 → 2, 13,6 s → 2,7 s cada; memo 1.137 acertos / 291 cálculos.",
    "Nenhum baseline/reference/threshold alterado; nenhum skip/xfail."
  ],
  "decisions_taken": [
    "Usuário: passagem livre contínua de face de nó a face de nó (geometria detectada), 30.8 desligada, off-grid pendente, cinta de topo fora do escopo, merge normal condicionado aos gates.",
    "Passagem contínua implementada como vãos sintéticos no solve (recorte do próprio motor), não como remoção pós-solve.",
    "Otimizações limitadas a memo/cache exatos com chave de valores; nenhuma reconstrução parcial não comprovada."
  ],
  "decisions_pending": [
    "Topo/peitoril fora da grade (51.8).",
    "Cinta de topo (10.7).",
    "Religar a 30.8 (7719511).",
    "Verga/contraverga (não iniciar)."
  ],
  "next_steps": [
    "Merge normal do PR #40 (sem squash/rebase/force-push) e fetch da nova origin/main.",
    "Parar: não iniciar verga, contraverga ou TORRE EASY."
  ],
  "references": [
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "tests/test_channel_audit_fixes.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "docs/architecture/channel-strategy-implementation.md"},
    {"path": "docs/decisions/DECISION-OPENING-REINFORCEMENT.md"},
    {"path": "docs/checkpoints/evidence/_scripts/channel_strict_compare.py"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-solver.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-revit-34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit-parity-final34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit/r_perf_after_clean.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-audit-corpus-legacy-equivalence.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-determinism.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-regressao-merge.json"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Gates para merge

| # | Gate | Resultado |
|---|---|---|
| 1 | CHANNEL ponta a ponta | solve → criação → releitura no Revit real |
| 2 | ACTUAL_ERROR = 0 | 0 (offline e Revit) |
| 3 | SOLVER_WORSE = 0 | 0 |
| 4 | NORMATIVE_DECISION = 0 | 0 |
| 5 | passagem livre aprovada | face de nó a face de nó; EXACT_MATCH |
| 6 | 7719511 limitação | KNOWN_LIMITATION, baseline intacto |
| 7 | off-grid pendente | NOT_COMPARABLE (51.8) |
| 8 | cinta de topo separada | nenhuma TOP_BOND_BEAM |
| 9–11 | nó\|fill / fill\|tie / INSIDE | 0 / 0 / 0 |
| 12 | determinismo | 3 processos idênticos |
| 13 | offline == Revit | assinatura 112ccde5… |
| 14 | idempotência | 7.222 → 7.222 |
| 15 | desempenho | 44,6 s → 24,2 s, resultado idêntico |
| 16 | testes CHANNEL | 213 passed |
| 17 | regressão | 3 failed / 1206 passed = falhas da main |
| 18 | CI/documentação | validador PASS; CI conferido no PR |
