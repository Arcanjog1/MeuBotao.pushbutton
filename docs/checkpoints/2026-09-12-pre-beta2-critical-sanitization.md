# Missão pré-Beta 2 — saneamento crítico: sonda de vão, régua V2 e regressão nó|fill (2026-09-12)

```json
{
  "date": "2026-09-12",
  "scope": "current",
  "branch": "claude/nifty-lovelace-d3ewpi",
  "head": "4d6eecff394b0147a4e59b942162d3aa653755de",
  "base": "643966994a2552df31e43451b3cb4137a1d3dc59",
  "main_observada": "643966994a2552df31e43451b3cb4137a1d3dc59",
  "pr": "not-created",
  "veredito": "READY FOR REVIEW — PRÉ-BETA 2 SANITIZED (ver a seção Veredito; regressão consolidada registrada em evidence/2026-09-12-regressao-consolidada.json)",
  "objective": "Sem MCP/Revit: (1) corrigir a sonda de vão `_room_at_t_on_wall` (ponto dentro de abertura); (2) criar a régua V2 do benchmark com a topologia do motor atual sem apagar a V1; (3) localizar e corrigir a regressão nó|fill (+2, W088/W090) escondida pelo PR #37 e restaurar os testes afrouxados.",
  "changes": [
    "nuvem/core/engine/wall_stepper.py — _room_at_t_on_wall: intervalos normalizados (t_lo>t_hi) e ponto DENTRO do vão devolve 0.0 em qualquer sentido (regra 3.1). _pier_full_search_layout(allow_forced_half): licença restrita de 1 B19 forçado quando o melhor candidato viola as duas regras (cadeia de compensadores E junta empilhada), aceita só se zerar a coincidência; chamada por _pier_layout_avoiding_joints (regra 33.8). Docstring do tier 6 registra a decisão pendente (tier 6 padrão medido, NÃO aplicado).",
    "nuvem/benchmark/runner.py — project_paths/run_project/run_wall_modeling_only/run_scoped_evaluation aceitam version=...; CLI --version v2; input de raiz reutilizado quando a versão não tem FASE A própria (registrado em metadata.from_input). nuvem/benchmark/tools/build_version_manifest.py (novo): regenera FASE A pelo pipeline real, roda o solver, grava baseline/score e manifest.json com SHAs, contagens, fingerprints e identidade física.",
    "nuvem/benchmark/projects/torre_easy_lo_r00_tgd/v2/{wall_modeling_snapshot,input,baseline,score,manifest}.json e torre_easy_lo_r00_tp1/v2/{baseline,score,manifest}.json (novos, HEAD de geração ac5e447); reports/*__v2.txt. V1 (raiz) intocada: nenhum baseline/reference/input histórico regravado.",
    "tests/test_room_probe_inside_opening.py (novo, 16: RED 12 failed/4 passed no 6439669 → GREEN); tests/test_forced_half_licence.py (novo, 5); tests/test_block_node_fill_revalidation.py t3/t4 (controle real canto–T restaurado, any(antes) volta, residual 70cm registrado) e t20 (0 violações, mais estrito que <=14/<=16); tests/test_block_b19_residual_fill_implementation.py t48 (== 12, wall_idx [12,13,14,15,88,90]); tests/regression/test_benchmark_baselines.py (réguas versionadas descobertas em disco); tests/test_perf_trace_stall_sampler.py (libc.usleep fora do Windows — portabilidade, commit separado a5cb248).",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md — 3.1 (sonda de vão), 11.10 (bissecção repetida: causa era a sonda; reserva de meio B54 fica pendente), 11.14 (efeito colateral registrado), 33.8 (regressão W088/W090: causa, mecanismo peça a peça, regra da licença, residual 70cm, decisão pendente do tier 6). nuvem/benchmark/README.md (réguas V1/V2). .gitignore (saídas regeneráveis de <projeto>/<versão>/).",
    "docs: GITHUB_STATE_2026-09-12.md, CI_RECOMMENDATION_2026-09-12.md, PROJECT_STATUS.md reconciliado (main 6439669, #37 oficial, seções antigas marcadas históricas), START_HERE.md, PROJECT_STATUS_LOG.md; evidência em docs/checkpoints/evidence/2026-09-12-*.{txt,json} e _scripts/2026-09-12-*.py."
  ],
  "tests": [
    "Sonda RED→GREEN: `python3 -m pytest tests/test_room_probe_inside_opening.py -q` — no HEAD 6439669: 12 failed / 4 passed (evidence/2026-09-12-room-probe-RED.txt); com o fix: 16 passed (evidence/2026-09-12-room-probe-GREEN.txt).",
    "Focados no candidato final (bf836bb, Linux, pytest 9.1.1): 16 arquivos (bonding, fill_prefers_b34_row, fit_tolerance c04 + jamb guard, cross_band CR-G12 completo incl. corpus, scale_autofix_rules, room_probe, corner_reserve, free_end_reserve, tie_parity, unmodulated_wall_retention, S1, arm_role_prism_stagger, bond_strip, test_script, node_fill t1–t17) -k 'not t18 and not t19 and not t20': 544 passed em 11 min 24 s. test_forced_half_licence: 5 passed. node_fill t3/t4: 3 passed. test_perf_trace_stall_sampler: 4 passed (era 1 failed em Linux: OSError kernel32).",
    "Corpus por estado (runner.run_project, write_files=False; evidence/2026-09-12-corpus-states.json): ver tabela 'Corpus antes/depois' abaixo.",
    "Medidor nó|fill (evidence/2026-09-12-nodefill-bisect.json): 21576ee 16/14, e34f710 16/14, ee34c2a 16/14, 7239946 14/14, cd4a261 16/16 (+W088/+W090), 6439669 16/16; candidato final 0/0 (TP1) e 0/0 (TGD).",
    "Bissecção 11.10 repetida (evidence/2026-09-12-bisect-1110.json): ver seção abaixo.",
    "REGRESSÃO CONSOLIDADA (`python3 -m pytest tests -q -p no:cacheprovider`, HEAD 4d6eecf, capturada por tools/documentation/capture_validation.py em evidence/2026-09-12-regressao-consolidada.{json,txt}): 1 failed / 1090 passed em 4.236,67 s — a única falha é a histórica test_benchmark_baselines::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1] (JUNCTION_MISSING_BINDING 8→9 contra o baseline V1, idêntica a 8cdd33f/cf325f2/c3eb0a1); a histórica do TGD (compensators 52→55) desapareceu. Zero falha nova.",
    "Validador documental: `python3 tools/documentation/validate.py --base 6439669 --main origin/main --require-current-main` — resultado na seção 'Validação documental'."
  ],
  "known_failures": [
    "Regressão consolidada: 1 failed / 1090 passed — tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1], asserção `delta['verdict'] != 'REGRESSAO CRITICA'` (JUNCTION_MISSING_BINDING 8→9 contra o baseline V1) — HISTÓRICA, presente em 8cdd33f/cf325f2/c3eb0a1 e em todos os estados medidos nesta missão (JUNCTION 9 constante).",
    "Residual nó|fill sintético: parede curta canto–T de 70 cm (fixture LT_RESIDUAL em t4) — nem a metade simétrica nem a licença fecham sem junta empilhada; registrado na regra 33.8.",
    "TP1 PRISM_CONTINUOUS_JOINT 300 (main) → 304 (sonda) → 48 (final): os 48 restantes são W003/W008 (16 cada), W002/W009/W078/W079 (3 cada) e W034/W044/W065/W074 (1 cada — junta 49,5 entre as fiadas 11 e 12, consequência da degradação correta do T a 7 cm de uma porta: o B54 que antes atravessava a jamba vira C09 e o preenchimento 3×B39 alinha com a fiada de cima). Defeito 1 estrutural, não regressão desta missão.",
    "TGD (régua V1) inalterado entre a sonda e o final: 831 críticos (PRISM 324, JUNCTION 23, CROSSES_JAMB 72, COVERAGE 216/144/28, POSITION_OVERLAP 24). CROSSES_JAMB 108 → 72 e INSIDE_DOOR 5 → 0 vêm da sonda.",
    "TGD régua V2 (topologia atual, 145 paredes): 911 críticos no HEAD de geração ac5e447 — PRISM 437, POSITION_OVERLAP 140, CROSSES_JAMB 96, COVERAGE 142/86/10; JUNCTION_MISSING_BINDING 0 e INSIDE_DOOR 0. Registrado como está (o baseline mede o solver, não o protege).",
    "PR #34: a API do GitHub marca merged (2026-09-11T18:09:05Z) mas 8a93a27/8cdd33f não são ancestrais da main 6439669 — inconsistência a esclarecer pelo usuário; os documentos seguem o Git."
  ],
  "physical_deltas": [
    "TP1 (V1): críticos 495 → 68; OPENING_BLOCK_CROSSES_JAMB 168 → 0 (todos eram B54 de T_INTERSECTION_MAIN/X_INTERSECTION atravessando jamba — a sonda media espaço através do vão); POSITION_OVERLAP 18 → 11; PRISM 300 → 48; JUNCTION_MISSING_BINDING 9 → 9; blocos 18.955 → 19.039.",
    "TGD (V1): críticos 872 → 831; OPENING_BLOCK_INSIDE_DOOR 5 → 0; CROSSES_JAMB 108 → 72; demais iguais; blocos 11.045 → 11.084.",
    "Régua V2 TGD: FASE A regenerada 145 paredes (V1 167; 58 chaves em comum, 109 só V1, 87 só V2), 234 nós (FREE_END 20, T 134, L 50, X 18, AMBIGUOUS 12; V1 tinha 66 FREE_END e 10 STRAIGHT_CONTINUATION), 91 aberturas atribuídas / 0 não atribuídas (V1 82/9), comprimento total 550,6 m (V1 430,3 m), 2.866 linhas após merge (V1 2.868). Fingerprint do resultado 41f82538…1402cd; input af44db2a….",
    "Régua V2 TP1: sem input_real (reconstruído do gabarito) — input idêntico à V1; baseline 19,8% / 324 críticos (ac5e447); fingerprint ecb645b0….",
    "Nenhum Revit aberto; nenhum documento RVT tocado."
  ],
  "decisions_taken": [
    "Branch designada pela sessão (`claude/nifty-lovelace-d3ewpi`) usada no lugar do nome sugerido `claude/pre-beta2-critical-sanitization` — mesmo conteúdo, derivada de 6439669.",
    "Tier 6 PADRÃO (B19 + 1 compensador no lugar de qualquer cadeia) medido e NÃO aplicado: TP1 PRISM 304 → 36 mas TGD 324 → 326 e reproducer mínimo da CR-G12 volta a acusar; entrou só a licença restrita (regra 33.8).",
    "Reserva de meio B54 (11.10) NÃO religada, apesar de a bissecção repetida mostrar 0 INSIDE_DOOR com a sonda corrigida — instrução do usuário: apresentar evidência primeiro.",
    "V2 gerada no HEAD ac5e447 (sonda corrigida, antes do fix nó|fill) e não regravada depois: o estado final é medido CONTRA ela (seção 'Estado atual contra V2').",
    "Nenhum baseline/reference/threshold histórico alterado; nenhum skip/xfail; nenhum merge; CI não alterado (recomendação separada)."
  ],
  "decisions_pending": [
    "Religar a reserva de meio B54 em _clip_range_by_midspan_neighbours (11.10): com a sonda corrigida, TP1 INSIDE_DOOR 0 e POSITION_OVERLAP 11 → 0; resolve o limite conhecido dos dois T entre 34 e 54 cm.",
    "Tier 6 padrão (B19 + 1 compensador): exige decidir a prioridade regra #1 × regra #2 na busca de desencontro (hoje regra #2 primeiro) ou lookahead da família A sobre a B.",
    "Migração completa de identidade (#28): validadores/scoring por chave física em vez de W0xx — débito registrado no manifest V2.",
    "CI: adotar pytest -m 'not slow' em PR e runner --check (V1 e V2) agendado (CI_RECOMMENDATION_2026-09-12.md).",
    "Esclarecer o estado do PR #34 (API merged × Git)."
  ],
  "next_steps": [
    "Revisão humana do PR; sem merge sem autorização específica.",
    "Missão seguinte: defeito 1 estrutural (TP1 PRISM 48 restantes, TGD 324) e COVERAGE do TGD, sobre a régua V2."
  ],
  "references": [
    {"path": "docs/PROJECT_STATUS.md"},
    {"path": "docs/GITHUB_STATE_2026-09-12.md"},
    {"path": "docs/CI_RECOMMENDATION_2026-09-12.md"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "nuvem/benchmark/README.md"},
    {"path": "nuvem/benchmark/tools/build_version_manifest.py"},
    {"path": "nuvem/benchmark/projects/torre_easy_lo_r00_tgd/v2/manifest.json"},
    {"path": "nuvem/benchmark/projects/torre_easy_lo_r00_tp1/v2/manifest.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-room-probe-RED.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-12-room-probe-GREEN.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-12-bisect-1110.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-nodefill-bisect.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-corpus-states.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-regressao-consolidada.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-regressao-consolidada.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-12-v2-delta.json"},
    {"path": "tests/test_room_probe_inside_opening.py"},
    {"path": "tests/test_forced_half_licence.py"}
  ]
}
```

## 1. Estado autoritativo

`origin/main` = `643966994a2552df31e43451b3cb4137a1d3dc59` (merge do #37), confirmado
por `git fetch` e pela API (`list_commits main`). Os três SHAs candidatos da
auditoria existem (`git cat-file -t`): `7239946`, `ee34c2a`, `cd4a261`.
Branch: `claude/nifty-lovelace-d3ewpi`, derivada de `6439669`, sem rebase,
sem force-push. Commits de código: `ac5e447` (sonda + runner --version),
`a5cb248` (teste portável), `bf836bb` (licença 33.8 + V2 + bissecções),
`4d6eecf` (t20/t48 exatos) = HEAD avaliado.

## 2. Sonda de vão — causa, fix, RED/GREEN

`_room_at_t_on_wall` filtrava só aberturas inteiramente à frente (`t_lo >=
t_ft`) ou inteiramente atrás (`t_hi <= t_ft`); com o ponto DENTRO do vão a
abertura era ignorada e a sonda media espaço através do vazio até o próximo
obstáculo. Fix geral: intervalos normalizados e ponto dentro do vão → 0,0 nos
dois sentidos. Teste `tests/test_room_probe_inside_opening.py` (A antes, B
depois, C dentro ×3 pontos ×2 sentidos + safe_range, D jamba exata e +0,05/
0,5/2 cm, E endpoints invertidos, F duas aberturas, consequência no solver):
**RED 12 failed / 4 passed** no `6439669` → **GREEN 16 passed**.

## 3. Corpus antes/depois (régua V1, `runner.run_project`, evidence/2026-09-12-corpus-states.json)

| Estado | TP1 críticos | TP1 por código | TGD críticos | TGD por código |
|---|---|---|---|---|
| main `6439669` | 495 | PRISM 300, JUNCTION 9, **CROSSES_JAMB 168**, POSITION_OVERLAP 18, INSIDE_DOOR 0 | 872 | PRISM 324, JUNCTION 23, CROSSES_JAMB 108, **INSIDE_DOOR 5**, COVERAGE 216/144/28, POSITION_OVERLAP 24 |
| sonda `ac5e447` | 324 | PRISM 304, JUNCTION 9, CROSSES_JAMB **0**, POSITION_OVERLAP 11 | 831 | PRISM 324, JUNCTION 23, CROSSES_JAMB 72, INSIDE_DOOR **0**, COVERAGE idem, POSITION_OVERLAP 24 |
| tier 6 padrão (medido, NÃO aplicado) | 56 | PRISM 36, JUNCTION 9, POSITION_OVERLAP 11 | 833 | PRISM **326**, resto idem |
| **final `bf836bb`/`4d6eecf`** | **68** | PRISM **48**, JUNCTION 9, POSITION_OVERLAP 11 | **831** | idem à sonda (PRISM 324) |

Os 168 CROSSES_JAMB do TP1 eram todos peças B54 de amarração
(T_INTERSECTION_MAIN 78, X_INTERSECTION 90) postas através da jamba porque a
sonda via "espaço" no vão. Blocos dentro de porta/janela no corpus: **0** nas
duas plantas após o fix.

## 4. Bissecção 11.10 repetida (evidence/2026-09-12-bisect-1110.json)

Reserva de meio B54 reaplicada em `_clip_range_by_midspan_neighbours`
(patch em runtime, `_scripts/2026-09-12-bisect_1110.py`):

| Árvore | TP1 INSIDE_DOOR | TP1 demais | TGD INSIDE_DOOR |
|---|---|---|---|
| ANTES do fix (main + reserva) | **7** — W019, bloco [715,749] no vão [564,750], fiadas 0–12 pares (idêntico a 2026-09-11) | CROSSES_JAMB 161, PRISM 300, JUNCTION 9 | 5 |
| DEPOIS do fix (ac5e447 + reserva) | **0** | CROSSES_JAMB 0, **POSITION_OVERLAP 0**, PRISM 304, JUNCTION 9 | 0 |

A causa dos 7 blocos dentro da porta era a sonda, não a reserva. Nada foi
religado (decisão pendente).

## 5. Régua V2 (evidence: manifests)

V1 = HISTORICAL / TOPOLOGIA ANTIGA (raiz, FASE A de 2026-08-31, engine sha
f0171249…). V2 = CURRENT ENGINE TOPOLOGY, gerada por
`tools/build_version_manifest.py --version v2` no HEAD `ac5e447` (base main
`6439669`, engine wall_modeling sha 8efd1f4b…), pipeline real
`input_real → runner.run_wall_modeling_only → wall_modeling_bridge →
snapshot → input_from_snapshot`.

| | V1 TGD | V2 TGD |
|---|---|---|
| paredes | 167 | **145** (58 chaves comuns) |
| nós | 272 (L 52, T 116, X 17, AMB 11, FREE 66, STRAIGHT 10) | **234** (L 50, T 134, X 18, AMB 12, FREE 20) |
| interseções (L+T+X+AMB) | 196 | 214 |
| aberturas atribuídas / não | 82 / 9 | **91 / 0** |
| linhas no layer / após merge / não usadas | 9258 / 2868 / 2450 | 9258 / 2866 / 2464 |
| comprimento total | 430,3 m | 550,6 m (paredes esticadas até os encontros; fragmentos retos fundidos) |
| baseline (ac5e447) | — | 23,4 %, 911 críticos: PRISM 437, POSITION_OVERLAP 140, CROSSES_JAMB 96, COVERAGE 142/86/10; JUNCTION 0, INSIDE_DOOR 0; 16.463 blocos |
| fingerprint resultado | — | 41f8253890aa193fee64632479f4dbd283148334f6c2d91fcf16be082f1402cd |
| identidade | W0xx | chave física por parede (endpoints canônicos + espessura + aberturas por element_id) e por nó (ponto + chaves das paredes); W0xx só alias; débito #28 registrado no manifest |

TP1 V2: sem `input_real` → input da raiz reutilizado (gravado em
`input_source`); baseline 19,8 % / 324 críticos (PRISM 304, JUNCTION 9,
POSITION_OVERLAP 11); fingerprint ecb645b018adfa18abeca0a02a07a23945f699f2dc5127c591fbafadedf2a59d.

## 6. Estado atual contra V2

Preenchido na seção 10 (delta medido com `runner.run_project(version="v2")`).

## 7. Regressão nó|fill — bissecção, causa, correção

| Estado | TP1 OFF / ON (sig 34,5-B) | paredes novas |
|---|---|---|
| 21576ee (main pré-#37) | 16 / 14 (5 / 4) | — |
| e34f710 (Etapa 7 flag) | 16 / 14 | — |
| ee34c2a (11.13) | 16 / 14 | — |
| 7239946 (fileira de B34) | 14 / 14 (4 / 4) | W027/W095 removidas na geração |
| **cd4a261 (11.14 reserva de canto por fiada)** | **16 / 16** | **+W088 (idx 87), +W090 (idx 89), t=34,5 fiada A** |
| 6439669 (main) | 16 / 16 | idem |
| **final** | **0 / 0** | — (TGD 0 / 0) |

Culpado: `cd4a261`, funções `_wall_reserved_range_ft` / `_corner_wall_room_ft`
/ `_node_lays_bond_on_wall_in_course` (CORNER_RESERVE_PER_COURSE). Mecanismo
físico (W088: 54 cm entre canto L em t=0 e T em que ela chega em t=54):
fiada A antes `C09[0,9] canto degradado + B34[10,44] fill + C09[45,54] T`
(juntas 9,5/44,5); depois `B34[0,34] canto (11.14) + C09[35,44] + C09[45,54]`
(juntas **34,5**/44,5). Fiada B, nos dois estados: `C09[15,24] C09[25,34]
C09[35,44] + C09[45,54] T` — cadeia do tier 7 com juntas fixas
24,5/**34,5**/44,5. A junta 34,5 nova da A caiu em cima da 34,5 da cadeia.
A metade simétrica não fechava porque `C09 + B19` (junta só em 24,5) nunca
era candidato (B19 fora de ponta aberta excluído da busca). Correção:
licença restrita (regra 33.8) — só quando a cadeia empilha junta e só se
zerar a coincidência. Efeito: TP1 PRISM 304 → 48 nas 12 paredes que o
medidor acusava; TGD inalterado; reproducer mínimo da CR-G12 verde.

## 8. Testes restaurados

| Teste | PR #37 (afrouxado) | Agora |
|---|---|---|
| t20 | `v_on <= v_off`, `sig_on <= 4`, `v_on <= 16` | `v_on == []`, `sig_on == []`, `v_on <= v_off`, sem violação nova (medido 0/0; histórico 31→14, 16→14, 16→16, 0→0 no docstring) |
| t48 | `len % 2 == 0 and <= 16` | `== 12` e `wall_idx == [12,13,14,15,88,90]`, todas `no_tie_covering_node` |
| t3 | só controle a mão | controle a mão + saída REAL do solver (parede curta canto–T 75/110/115/150 cm, metade simétrica OFF produz a junta 34,5-B) |
| t4 | perdeu `any(antes)` | `all(antes)` nas fixtures reais, `depois == []`; grade 2x2 nunca piora; residual 70 cm registrado como limite |
| amostrador de GIL | 1 failed em Linux (kernel32) | `libc.usleep` fora do Windows; 4 passed |

## 9. Regressão consolidada (evidence/2026-09-12-regressao-consolidada.{json,txt})

`python3 -m pytest tests -q -p no:cacheprovider` no HEAD `4d6eecf` (tree
`fef15919…`), Linux, Python 3.11.15, pytest 9.1.1, capturada por
`tools/documentation/capture_validation.py` (PID 3942, timeout 7000 s):

**1 failed / 1090 passed em 4.236,67 s (1h10m36s), exit code 1.**

Falha (nome e asserção):
`tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]`
— `REGRESSAO CRITICA em torre_easy_lo_r00_tp1: JUNCTION_MISSING_BINDING 8 → 9`
contra o baseline **V1** do TP1. É a falha HISTÓRICA já registrada nos
checkpoints de 2026-09-09/10/11 (idêntica em `8cdd33f`, `cf325f2`,
`c3eb0a1`: "TP1 JUNCTION 8→9"); não foi introduzida nem alterada por esta
missão (JUNCTION 9 em todos os estados medidos: main, sonda, final). A outra
falha histórica (TGD `compensators` 52→55, categoria) **desapareceu**: o TGD
passa contra o baseline V1. Zero falha nova; nenhum skip/xfail adicionado;
baseline V1 não regravado. A régua V2 (`test_projeto_nao_regrediu_contra_o_
baseline_versionado[tgd/tp1-v2]`) passa (MELHORIA nas duas plantas).

## 10. Estado atual contra V2 (evidence/2026-09-12-v2-delta.json)

`runner.run_project(version="v2", write_files=False)` no estado final,
comparado ao baseline V2 (gerado em `ac5e447`) por `scoring.compare_runs`:

| Projeto | Veredito | Críticos V2 baseline → agora | PRISM | Blocos |
|---|---|---|---|---|
| TGD v2 | **MELHORIA** | 911 → 719 | 437 → **245** | 16.463 → 16.361 |
| TP1 v2 | **MELHORIA** | 324 → 68 | 304 → **48** | 19.181 → 19.039 |

Nenhum código crítico piorou em nenhuma das duas réguas; o baseline V2 não
foi regravado (mede o solver, não o protege). `runner.py --all --check
--version v2` passa no estado final.

## 11. Validação documental e CI

CI atual: só `check-project-status.yml` (validação documental). Recomendação
(sem alterar CI neste PR): [CI_RECOMMENDATION_2026-09-12.md](../CI_RECOMMENDATION_2026-09-12.md).

## Veredito

**READY FOR REVIEW — PRÉ-BETA 2 SANITIZED.** Os 16 critérios de sucesso da
missão: (1) sonda corrigida; (2) teste mínimo RED→GREEN prova o ponto dentro
da abertura; (3) corpus com 0 blocos dentro de porta/janela nas duas
plantas; (4) bissecção 11.10 repetida e documentada (causa era a sonda);
(5) régua V2 criada, V1 intacta; (6) V2 reproduz a FASE A do motor atual
(145/234/91) pelo pipeline real; (7) estado atual medido contra V2 (MELHORIA,
baseline não regravado); (8) causa de W088/W090 localizada (`cd4a261`,
11.14 × cadeia `C09 C09 C09` do tier 7); (9) regressão corrigida (16 → 0);
(10) t20/t48/t3/t4 restaurados estritos; (11) focados verdes (544 + 5 + 16);
(12) consolidada compreendida (1 falha, histórica e nomeada; 1090 passed);
(13) docs reconciliados; (14) CI compreendido, recomendação separada;
(15) nenhum baseline histórico regravado; (16) nenhum skip/xfail. Sem MCP,
sem Revit, sem merge.
