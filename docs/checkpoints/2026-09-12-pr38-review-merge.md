# Revisão independente e merge do PR #38 — PRÉ-BETA 2 SANITIZED (2026-09-12)

```json
{
  "date": "2026-09-12",
  "scope": "current",
  "branch": "claude/zealous-ritchie-z2ap3y",
  "head": "ad46c61372ba0292d117e14ba605375af7acd807",
  "base": "643966994a2552df31e43451b3cb4137a1d3dc59",
  "main_observada": "ad46c61372ba0292d117e14ba605375af7acd807",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/38",
  "veredito": "MERGED — PRÉ-BETA 2 SANITIZED (15/15 gates; merge normal ad46c61)",
  "objective": "Revisar de forma independente tudo o que entrou no PR #38 (sonda de vão, régua V2, regressão nó|fill W088/W090, testes restaurados, docs) reproduzindo as provas essenciais, e — somente com os 15 gates aprovados — integrar por merge normal na main. Sem MCP, sem Revit, sem iniciar o defeito 1.",
  "changes": [
    "Nenhum código, teste, benchmark ou regra alterado nesta sessão. Único commit adicionado ao PR antes do merge: 609a8b3 (docs) — correção factual sobre o PR #34 (está na main; a leitura 'não ancestral' veio de um clone raso) e reconciliação do PROJECT_STATUS (#34 candidate → official), que era a causa exata da falha do CI documental no head d7dbb94.",
    "Merge normal do #38 na main: ad46c61 (pais 6439669 + 609a8b3). Sem rebase, sem force-push. PR marcado ready for review antes do merge; check-status-doc verde em 609a8b3.",
    "Esta branch (claude/zealous-ritchie-z2ap3y, derivada de ad46c61): PROJECT_STATUS (main ad46c61, #38 official), START_HERE, PROJECT_STATUS_LOG, GITHUB_STATE_2026-09-12 (seção de atualização), este checkpoint e evidência."
  ],
  "tests": [
    "Sonda RED→GREEN reproduzida: tests/test_room_probe_inside_opening.py copiado para a main 6439669 → 13 failed / 3 passed (a evidência da sessão anterior registrava 12/4: aqui o teste da consequência no solver também falha na main — B54 [223,277] dentro do vão [200,300] — o RED é ainda mais forte); no head do PR → 16 passed.",
    "Focados no head do PR: room_probe + test_forced_half_licence + test_perf_trace_stall_sampler = 25 passed (2,95 s); t3/t4/t20/t48 = 4 passed (283 s).",
    "Corpus (runner.run_project, write_files=False; evidence/2026-09-12-pr38-review-evidence.json): TP1 V1 críticos 68 (INSIDE_DOOR 0, INSIDE_WINDOW 0, CROSSES_JAMB 0, POSITION_OVERLAP 11, PRISM 48, JUNCTION 9); TGD V1 831 (INSIDE_DOOR 0, INSIDE_WINDOW 0, CROSSES_JAMB 72, POSITION_OVERLAP 24, PRISM 324, JUNCTION 23); TP1 V2 68 (idem, MELHORIA); TGD V2 719 (INSIDE_DOOR 0, INSIDE_WINDOW 0, CROSSES_JAMB 96, POSITION_OVERLAP 140, PRISM 245, JUNCTION 0, MELHORIA).",
    "Medidor nó|fill (node_fill_prism_violations, metade simétrica OFF/ON): TP1 0/0, TGD 0/0 no head do PR. Bissecção reproduzida: 7239946 14/14; cd4a261 16/16 (+W088/+W090, t=34,5 fiada A); main 6439669 16/16; PR 0/0.",
    "Régua V2 (TGD) reproduzida sem escrever: FASE A regenerada = 145 paredes / 234 nós (AMB 12, FREE 20, L 50, T 134, X 18) / 91 aberturas (0 não atribuídas); chaves de parede, conjunto de nós e aberturas IDÊNTICOS ao snapshot gravado; engine sha 8efd1f4b; fingerprint do input == manifest (af44db2a…); fingerprint do resultado no manifest 41f82538…. V1 gravada continua 167/272/82 (9 não atribuídas).",
    "REGRESSÃO CONSOLIDADA (python3 -m pytest tests -q -p no:cacheprovider, worktree em d7dbb94 — árvores nuvem a740c76 e tests c26f5d5 idênticas às de 609a8b3): 1 failed / 1090 passed em 3.436,92 s (57 min). Única falha: tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1] — JUNCTION_MISSING_BINDING 8→9 contra o baseline V1 (baseline V1 grava 8 desde f693dcf; a main 6439669 já media 9 — checkpoints de 2026-09-09/10/11). Log em evidence/2026-09-12-pr38-review-regressao-consolidada.txt.",
    "Validador documental no head do PR após 609a8b3: PASS local e CI check-status-doc success (2 runs)."
  ],
  "known_failures": [
    "Histórica preservada: TP1 JUNCTION_MISSING_BINDING 8→9 contra o baseline V1 (única falha da consolidada; V2 do TP1 grava 9 e passa).",
    "Residual sintético nó|fill de 70 cm (LT_RESIDUAL em t4) — registrado na regra 33.8, não escondido.",
    "Defeito 1 estrutural continua aberto: TP1 PRISM_CONTINUOUS_JOINT 48 (V1/V2), TGD 324 (V1) / 245 (V2). Próxima missão.",
    "Discrepância de evidência (não bloqueante): room-probe-RED.txt da sessão anterior registra 12 failed / 4 passed na main; reproduzido aqui como 13/3 (o teste da consequência no solver também falha na main)."
  ],
  "physical_deltas": [
    "Nenhuma mudança física nesta sessão além do conteúdo do próprio #38, já medido acima. W088/W090 (54 cm, canto L em t=0 e T em t=54): fiada A B34[0,34] C09[35,44] C09[45,54] (11.14); fiada B antes C09[15,24] C09[25,34] C09[35,44] C09[45,54] (junta 34,5 empilhada), depois C09[15,24] B19[25,44] C09[45,54] (juntas 24,5/44,5) — junta nó|fill zerada.",
    "Nenhum Revit aberto; nenhum documento RVT tocado."
  ],
  "decisions_taken": [
    "Gates 1–15 da missão avaliados e aprovados; merge normal executado com a autorização explícita da missão (só com todos os gates).",
    "Commit de docs 609a8b3 empurrado na branch do PR (claude/nifty-lovelace-d3ewpi) como correção de defeito claramente no escopo do #38 (CI documental vermelho por afirmação factual errada sobre o #34).",
    "Não iniciado: defeito 1, reserva de meio B54 (11.10), tier 6 padrão, migração #28, verga/contraverga/canaleta, cortes, L/T/X novos, ETAPA 3B, GOLDEN novo.",
    "PR #34: registrado o estado real (está na main pela cadeia do Beta 1); nenhum cherry-pick, nenhuma recriação de commit, nenhum ajuste de histórico."
  ],
  "decisions_pending": [
    "Religar a reserva de meio B54 em _clip_range_by_midspan_neighbours (11.10) — evidência no checkpoint da missão.",
    "Tier 6 padrão (B19 + 1 compensador) — prioridade regra #1 × regra #2 (33.8).",
    "Migração completa de identidade (#28) — débito no manifest V2.",
    "CI: pytest -m 'not slow' em PR e runner --check (V1 e V2) agendado (CI_RECOMMENDATION_2026-09-12.md)."
  ],
  "next_steps": [
    "Missão separada: DEFEITO 1 — junta corrida preenchimento|amarração, sobre a régua V2.",
    "Sem merge desta branch sem autorização específica."
  ],
  "references": [
    {"path": "docs/PROJECT_STATUS.md"},
    {"path": "docs/GITHUB_STATE_2026-09-12.md"},
    {"path": "docs/checkpoints/2026-09-12-pre-beta2-critical-sanitization.md"},
    {"path": "docs/checkpoints/evidence/2026-09-12-pr38-review-evidence.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-pr38-review-regressao-consolidada.txt"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "nuvem/benchmark/projects/torre_easy_lo_r00_tgd/v2/manifest.json"},
    {"path": "tests/test_room_probe_inside_opening.py"},
    {"path": "tests/test_forced_half_licence.py"}
  ]
}
```

## Gates (missão, seção 14)

| # | Gate | Resultado |
|---|---|---|
| 1 | diff compreendido | 43 arquivos + 609a8b3 (docs): PRODUCTION `nuvem/core/engine/wall_stepper.py`, `nuvem/benchmark/runner.py`; TOOLING `nuvem/benchmark/tools/build_version_manifest.py`, `.gitignore`; TESTS 6 arquivos; BENCHMARK V2 `projects/*/v2/*`, `reports/*__v2.txt`; HISTORICAL V1 **nenhum arquivo tocado** (`git diff --name-only` sem `/v2/` = só os dois reports V2; `golden/` intocado); DOCUMENTATION 7 + REGRAS + README; EVIDENCE `docs/checkpoints/evidence/2026-09-12-*` |
| 2 | sonda corrigida | `_room_at_t_on_wall`: spans normalizados (`t_a<=t_b`), ponto com `t_lo+1e-6 < t < t_hi-1e-6` → 0.0 nos dois sentidos, jamba exata mede para fora; casos A–F + consequência no solver; RED 13/3 na main → 16 passed |
| 3–4 | INSIDE_DOOR / INSIDE_WINDOW | 0 / 0 em TP1 e TGD, réguas V1 e V2 |
| 5 | V1 preservado | nenhum `baseline/input/reference/snapshot/score` da raiz alterado; `golden/` intocado; `test_projeto_nao_regrediu_contra_o_baseline` V1 continua rodando sem skip |
| 6 | V2 reproduzível | FASE A regenerada idêntica ao snapshot (145/234/91, chaves/nós/aberturas iguais, engine sha igual, fingerprint do input igual ao manifest) |
| 7–8 | nó|fill TP1 / TGD | 0/0 e 0/0 (OFF/ON) |
| 9 | testes afrouxados restaurados | t20 `v_on == []` e `sig_on == []`; t48 `== 12` e `wall_idx == [12,13,14,15,88,90]`; t3 controle a mão + saída real (canto–T 75/110/115/150); t4 `all(antes)` + `depois == []` + residual 70 cm trancado; 4 passed |
| 10 | sem regressão crítica nova | corpus V1/V2: nenhum código crítico piorou; TGD V1 MELHORIA, V2 MELHORIA nas duas plantas |
| 11 | consolidada compreendida | 1 failed / 1090 passed (57 min); falha = histórica TP1 JUNCTION 8→9 vs V1 |
| 12 | nenhum baseline/golden regravado | confirmado por `git diff --name-only` |
| 13 | nenhum skip/xfail | `grep` no diff dos testes: zero ocorrências |
| 14 | docs coerentes | após 609a8b3: PROJECT_STATUS/START_HERE/GITHUB_STATE/checkpoint/REGRAS coerentes com o HEAD; validador PASS |
| 15 | CI compreendido | único workflow `check-status-doc`; vermelho em d7dbb94 por "candidate already integrated: 8a93a27" (afirmação errada sobre o #34), verde em 609a8b3 |

## Licença do B19 (33.8) — restrição verificada no código

`_pier_layout_avoiding_joints`: a busca licenciada só é chamada quando `best_score[0] > 0 and best_score[1] > 0` (excesso de compensadores em sequência **e** coincidência de junta) e só é aceita se `forcada_score[1] == 0 and forcada_score < best_score`. Em `_pier_full_search_layout`, `allow_forced_half` só eleva `max_half`/`max_misplaced` para 1 quando `base_profile[0] > MAX_COMPENSATORS_PER_TRECHO`. `tests/test_forced_half_licence.py` tranca: sem conflito a cadeia continua; nunca 2 B19; trecho sem cadeia nunca ganha B19; caso CR-G12 (W113) continua sem B19. Tier 6 padrão **não** aplicado (decisão pendente).

## Amostrador de GIL (portabilidade)

`sys.platform == "win32"` → `kernel32.Sleep(900)` (inalterado); senão `libc.usleep(900000)` via `PyDLL` (GIL retida). Mesmas asserções nos dois ramos; nenhum código de produção alterado; 4 passed em Linux.

## PR #34 — estado real

API: merged 2026-09-11T18:09:05Z. Git (clone completo): `8a93a27` e `8cdd33f` **são** ancestrais de `6439669` — `8a93a27` → `0ffa8e9` … `41086e4` (Beta 1) → `2599355` → `6439669` (#37). A leitura "não ancestral" de 2026-09-12 foi feita num clone raso (252 commits alcançáveis; 262 após `--unshallow`). Sem impacto técnico no #38 além do CI documental, corrigido em 609a8b3. Nenhum cherry-pick nem recriação de commit.
