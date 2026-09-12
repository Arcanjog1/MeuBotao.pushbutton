# Defeito 1 — junta corrida PREENCHIMENTO | AMARRAÇÃO DO NÓ (fill|tie), régua V2 (2026-09-12)

```json
{
  "date": "2026-09-12",
  "scope": "current",
  "branch": "claude/fix-fill-tie-running-joint",
  "head": "6b78a9aa70ff0cac239dcdd9ed1deaab730eb9a1",
  "base": "ad46c61372ba0292d117e14ba605375af7acd807",
  "main_observada": "ad46c61372ba0292d117e14ba605375af7acd807",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/39",
  "veredito": "PARTIAL — FILL|TIE FIXED, OTHER PRISM REMAINS (ver seção Veredito: fill|tie entre nós distintos 0/0; resta fill|fill no TP1 e abertura/peça duplicada/mesma peça de canto no TGD)",
  "objective": "Sem MCP/Revit, sobre origin/main ad46c61 (PR #38 integrado) e a régua V2: classificar os PRISM_CONTINUOUS_JOINT residuais (TP1 48, TGD 245), reproduzir a classe fill|tie em fixtures mínimas, provar a causa e corrigi-la de forma física e geral (sem tocar auditor/tolerância/baseline), com fill|tie = 0 nas duas plantas, nó|fill = 0, INSIDE_DOOR/WINDOW = 0, CROSSES_JAMB/POSITION_OVERLAP sem regressão, determinismo e custo local.",
  "changes": [
    "nuvem/core/engine/wall_stepper.py — solve_all_intersections: (a) a marca _tie_parity_flip (11.12) passa a ser aplicada no momento em que o nó é resolvido (antes de solved_by_node, para a 11.14 ler a fiada real); (b) nova etapa ABUTTING_TIE_PARITY_ENABLED (_apply_abutting_tie_parity): censo preciso das juntas NÓ|FILL por fiada deduzido só das peças de nó (_node_fill_boundary_joint_census, isenção 11.8), coincidências NÓ|FILL(A) × NÓ|FILL(B) entre nós diferentes (_census_coincidences) e pares de peças encostadas na mesma fiada (_abutting_same_course_tie_pairs) viram restrições XOR; _plan_abutting_tie_parity faz 2-coloração por componente em ordem geométrica (T/X e cantos L livres/de aresta isolada móveis; cantos coordenados/pinados fixos; monotonia); componente sem nó fixo escolhe a coloração pelo proxy de compensadores (_tie_parity_fill_proxy sobre _wall_course_free_segments_cm); inversão por _tie_parity_apply (T/X marca; L troca de arms + _arm_role_pinned); aceite só com queda estrita das coincidências numa re-solução dos nós; residual em tie_parity_conflicts. _node_bond_courses_on_wall/_node_lays_bond_on_wall_in_course respeitam a marca (_flip_course). _arm_role_isolated_edges lista arestas com respect_pins=True. OPENING_ALIGNED_TOUCH_TOLERANCE_CM definida no engine (única). process_walls_one_by_one publica tie_parity_flips/tie_parity_conflicts.",
    "nuvem/core/wall_modeling.py — agrega tie_parity_flips/tie_parity_conflicts por banda; OPENING_ALIGNED_TOUCH_TOLERANCE_CM passa a vir do engine (mesmo valor 2,0).",
    "tests/test_tie_parity_abutting_ties.py (novo, 22 testes): fixtures mínimas T–L 69 cm, T–X fill à esquerda (594), X–T fill à direita (594), cadeia de 3 T a 55 cm, L-X-L 124 isolado e coordenado; RED sem a paridade / GREEN com ela; ordem normal, reversa, permutada, endpoints invertidos; 3 processos; porta perto do nó (0 no vão); colisões; residual reportado.",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md — 33.9 (REGRA OBRIGATÓRIA: peças de amarração de nós diferentes encostadas na mesma parede ficam na mesma fiada; definição física, classificação, algoritmo, por que não é auditor, medição, limites).",
    "docs: este checkpoint; PROJECT_STATUS.md reconciliado com origin/main ad46c61 (#38 oficial) e candidato fb618b2; PROJECT_STATUS_LOG.md (índice); START_HERE.md; evidência em docs/checkpoints/evidence/2026-09-12-filltie-*.{json,md,txt} e _scripts/2026-09-12-filltie-*.py."
  ],
  "tests": [
    "RED→GREEN: `python3 -m pytest tests/test_tie_parity_abutting_ties.py -q` — com ABUTTING_TIE_PARITY_ENABLED=False as 5 fixtures produzem a junta NÓ|FILL × NÓ|FILL (test_defeito_reproduzido_sem_a_paridade); com True 0 juntas fill|tie, 0 nó|fill, 0 falhas de nó, 0 colisões (22 passed em 1,2 s no HEAD fb618b2).",
    "Focados (HEAD fb618b2, Linux, Python 3.11.15, pytest 9.1.1): test_block_node_fill_revalidation (t1–t17), test_forced_half_licence, test_tie_parity_local_search, test_corner_reserve_per_course, test_script, test_tie_parity_abutting_ties -k 'not t18 and not t19 and not t20': 325 passed / 3 deselected em 56,5 s (evidence/2026-09-12-filltie-focados.txt).",
    "Corpus V2 antes/depois (`runner.run_project(version='v2', write_files=False)`, evidence/2026-09-12-filltie-corpus-before-after.json e tabela por chave física em evidence/2026-09-12-filltie-cases.txt): ver seção 'Métrica antes/depois'.",
    "Determinismo (evidence/2026-09-12-filltie-determinism.json): fingerprint canônico do resultado (golden.fingerprint.canonical_fingerprint) em 3 processos separados por planta — TP1 f72853f9…69a00 idêntico ×3; TGD 1403b49d…5a648 idêntico ×3.",
    "REGRESSÃO CONSOLIDADA (`python3 -m pytest tests -q -p no:cacheprovider`, HEAD de produção fb618b2, capturada por tools/documentation/capture_validation.py em evidence/2026-09-12-filltie-regressao-consolidada.{json,txt}): 4 failed / 1109 passed em 2.395,56 s, exit 1 — 1 histórica (TP1 JUNCTION 8→9 vs V1), 1 categoria nível 2 (TGD V2 compensators 61→62), 2 asserções de mecanismo ARM substituídas pela prova física (ver seção 8). O HEAD avaliado deste checkpoint difere de fb618b2 SOMENTE nos dois testes ajustados (git diff fb618b2..HEAD -- nuvem/core/ vazio; só documentação em nuvem/REGRAS_MODULACAO_BLOCOS.md); os dois testes foram re-executados isolados no HEAD avaliado (evidence/2026-09-12-filltie-arm-tests-rerun.txt).",
    "Validador documental: `python3 tools/documentation/validate.py --base ad46c61 --main origin/main --require-current-main` — ver seção 'Validação documental'."
  ],
  "known_failures": [
    "Regressão consolidada (fb618b2): 4 failed / 1109 passed — (1) test_benchmark_baselines[tp1] JUNCTION_MISSING_BINDING 8→9 vs V1, HISTÓRICA; (2) test_benchmark_baselines_versionado[tgd-v2] categoria compensators 61→62 (nível 2, W016; baseline V2 não regravado — decisão do usuário); (3) e (4) asserções de MECANISMO do SAFE REPAIR (candidato aceito 91/SAME_B no TGD, 75/SAME_A em W076 do TP1) que a paridade passa a resolver antes — ajustadas ao contrato físico e re-executadas isoladas (seção 8).",
    "non_modular do solver: +14 (TP1 V1) / +63 (TGD V1) entradas SEM_ESPACO de −1 cm entre duas peças de nó encostadas na mesma fiada — bookkeeping pré-existente do laço de trechos, sem peça faltando; pendência pequena registrada.",
    "TP1 V2 residual 16 PRISM_CONTINUOUS_JOINT, todos fill|fill: W002/W009/W078/W079 (3 cada, rows 13–16: cadeia `C09 C09 C04` do trecho de 65 cm entre T e canto contra `B34 B34 B34` da fiada oposta) e W034/W044/W065/W074 (1 cada, rows 11–12: fronteira de banda acima da porta). Defeito próprio (tier 7 / cross-band), fora do escopo desta missão (item 17: tier 6 padrão é decisão pendente).",
    "TGD V2 residual 53: 40 em W027/W028/W129/W130 (844 cm, 4 portas): peça B34 `T_INTERSECTION_DEGRADED_L` DUPLICADA no mesmo lugar ([613,647]×2 / [181.5,215.5]×2 — POSITION_OVERLAP) forma junta artificial contra o C09 de reparo de abertura da fiada vizinha; 2 tie|tie nas mesmas paredes; 11 em W080 (379 cm): os dois cantos L põem B34 nas DUAS fiadas na mesma posição (SAME_NODE) — giro do canto, não paridade. Nenhum é fill|tie entre nós distintos.",
    "TGD: COMPENSATOR_EXCESS_IN_RUN 444 → 454 e COMPENSATOR_VERTICAL_STRIP 82 → 86 nas quatro principais das cadeias de T (W015/W016/W142/W143, 1484–1936 cm), nível 2; COMPENSATOR_CONSECUTIVE 472 = 472. Registrado como delta, não escondido.",
    "Limite: L-X-L com cantos presos em cadeia coordenada (alternância 30.5) é UNSATISFIABLE para a paridade T/X (fixture `l_x_l_124_coordenado`, reportado em tie_parity_conflicts) — no corpus os quatro L-X-L são arestas isoladas e resolvem."
  ],
  "physical_deltas": [
    "TP1 V2: PRISM_CONTINUOUS_JOINT 48 → 16 (fill|tie 32 → 0 em W003/W008; restam 16 fill|fill); PRISM_JOINT_STACK 2 → 0; JUNCTION_MISSING_BINDING 9 = 9; POSITION_OVERLAP 11 = 11; INSIDE_DOOR/WINDOW 0 = 0; CROSSES_JAMB 0 = 0; COMPENSATOR_CONSECUTIVE 988 → 936, EXCESS 947 → 933, STRIP 151 → 149, AVOIDABLE 81 → 80; PRISM_STAGGER_BELOW_TARGET 1571 → 1539; COVERAGE_GAP_IN_ROW 336 = 336; blocos 19.039 → 18.963; 96 paredes; success_rate 19,8 % → 20,8 %. Inversões: X 157, X 169 (6607/8942, 1815) e canto 126.",
    "TGD V2: PRISM_CONTINUOUS_JOINT 245 → 53 (fill|tie entre nós distintos 203 → 0 nas 13 paredes W005/W006/W012/W013/W021/W022/W075/W086/W137/W139/W140/W141 + W080 parcial); PRISM_JOINT_STACK 17 → 5; CROSSES_JAMB 96 = 96; POSITION_OVERLAP 140 = 140; INSIDE_DOOR/WINDOW 0 = 0; JUNCTION_MISSING_BINDING 0 = 0; COVERAGE 86/142/10/32/1275 iguais; COMPENSATOR_CONSECUTIVE 472 = 472, EXCESS_IN_RUN 444 → 454, VERTICAL_STRIP 82 → 86; blocos 16.361 → 16.289; 145 paredes / 234 nós; success_rate 23,5 % → 29,0 %; paredes reprovadas 112 → 106. Inversões: 12 T + 5 cantos (X ficaram).",
    "Nenhum baseline/reference/threshold/tolerância/validador alterado; nenhum skip/xfail; nenhuma peça nova; posição de nenhuma amarração muda — só a fiada que a hospeda. Walls, nós e aberturas iguais.",
    "Performance: run_project TP1 90,0 → 81,2 s, TGD 273 → 216 s (mesma máquina, cargas concorrentes diferentes); custo isolado da etapa: solve_all_intersections do TGD 0,05 s → 0,80 s na primeira chamada (censo + 2 re-soluções de nós por componente livre) e 0,05 s nas chamadas seguintes (marcas já aplicadas); TP1 0,28 s / 0,04 s. Nenhuma re-solução de preenchimento por tentativa.",
    "Nenhum Revit aberto; nenhum documento RVT tocado."
  ],
  "decisions_taken": [
    "Classe A (fill|tie) definida fisicamente como NÓ|FILL(A) × NÓ|FILL(B) na mesma parede; medido que em 100 % dos casos as duas peças de nó são de nós diferentes encostadas junta a junta (T que chega + X a 55 cm; T + canto L em 69 cm; L + X + L em 124 cm; X + T na ponta) — a hipótese 'o fill desconhece a junta da tie' foi refutada: o fill conhece (33.1) mas o trecho é de uma peça só entre dois contornos fixos.",
    "Correção pela PARIDADE dos nós (licença 11.12 já existente + licença 'mesma família' de aresta isolada 31/32), não pelo layout do fill — não há layout que mova uma junta de contorno. TIE_PARITY_LOCAL_SEARCH continua desligada: extraída só a restrição local barata (censo + XOR), sem re-solução de preenchimento.",
    "Escolha da coloração por proxy de compensadores (não por convenção): sem ele a inversão do X nas paredes de 594 cm criava `C09 C09 C04` nas duas fiadas (+136 COMPENSATOR_CONSECUTIVE no TGD, medido e descartado).",
    "Cantos de cadeia coordenada continuam fixos (30.5); inversão de componente inteiro de cantos não implementada (sem caso no corpus).",
    "Baselines V1/V2 não regravados; V2 continua a régua (o candidato é MELHORIA contra ela). Nenhum merge."
  ],
  "decisions_pending": [
    "fill|fill residual do TP1 (cadeias `C09 C09 C04` de 65 cm entre T e canto; fronteira de banda acima de porta): tier 6 padrão / prioridade regra #1 × #2 (33.8, decisão do usuário).",
    "Peça de nó duplicada em T_INTERSECTION_DEGRADED_L (W027/W028/W129/W130 do TGD, POSITION_OVERLAP) e canto com B34 nas duas fiadas (W080): defeitos próprios do solver de L/T degradado, fora desta missão.",
    "Regravar a régua V2 num artefato/versão próprio quando a governança permitir (o delta está registrado aqui; V2 não foi alterada) — inclusive a categoria compensators 61→62 que faz o gate versionado falhar.",
    "Trecho de −1 cm entre duas peças de nó encostadas na mesma fiada reportado como SEM_ESPACO em solve_wall_free_fill (non_modular): ignorar quando os dois contornos são de nó (correção pequena, não feita depois do HEAD avaliado)."
  ],
  "next_steps": [
    "Revisão humana do PR draft; sem merge sem autorização específica.",
    "Missão seguinte: fill|fill (cadeias de compensadores / cross-band) e COVERAGE do TGD sobre a régua V2."
  ],
  "references": [
    {"path": "docs/PROJECT_STATUS.md"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "tests/test_tie_parity_abutting_ties.py"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-corpus-before-after.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-cases.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-determinism.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-focados.txt"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-dump.py"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-classify.py"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-cases.py"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-predict.py"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-census-prototype.py"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-fp.py"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-arm-check.py"},
    {"path": "docs/checkpoints/evidence/_scripts/2026-09-12-filltie-nonmod.py"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-regressao-consolidada.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-regressao-consolidada.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-arm-check.json"},
    {"path": "docs/checkpoints/evidence/2026-09-12-filltie-arm-tests-rerun.txt"},
    {"path": "docs/checkpoints/2026-09-12-pre-beta2-critical-sanitization.md"}
  ]
}
```

## 1. Estado autoritativo

`origin/main` = `ad46c61372ba0292d117e14ba605375af7acd807` (merge do #38),
confirmado por `git fetch` + `git rev-parse origin/main`. Branch
`claude/fix-fill-tie-running-joint` derivada dela, sem rebase, sem
force-push. Commit de produção `fb618b2` (engine + testes novos + scripts); HEAD avaliado
`6b78a9aa70ff0cac239dcdd9ed1deaab730eb9a1` = fb618b2 + ajuste dos dois testes ARM ao contrato físico
(`git diff fb618b2..HEAD -- nuvem/core/ tests/test_tie_parity_abutting_ties.py` vazio; em `nuvem/` só o REGRAS_MODULACAO_BLOCOS.md documental); depois só documentação.

## 2. Classificação dos PRISM (antes, régua V2)

Método: cada `PRISM_CONTINUOUS_JOINT` classificado pelo papel das peças das
duas juntas — NF = peça de nó|preenchimento, FF = preenchimento|preenchimento,
TT = nó|nó, OF = peça de ajuste de abertura (`_scripts/2026-09-12-filltie-classify.py`).
Tabela completa por chave física em [evidence/2026-09-12-filltie-cases.txt](evidence/2026-09-12-filltie-cases.txt).

| Régua V2 | PRISM | A fill\|tie (NF×NF) | B fill\|fill | C tie\|tie | D abertura/peça duplicada | E extremidade | F exceção | G outro |
|---|---|---|---|---|---|---|---|---|
| TP1 | 48 | **32** — W003/W008 (1344 cm): B54 do X a 1282 (A) `[1255,1309]` encostado na B34 do T em que chega a 1337 (B) `[1310,1344]`, junta 1309,5 nas 16 fiadas | 16 — W002/W009/W078/W079 (269 cm, `C09 C09 C04` × `B34 B34 B34`, rows 13–16); W034/W044/W065/W074 (fronteira de banda, rows 11–12) | 0 | 0 | 0 | 0 | 0 |
| TGD | 245 | **203** — 594 cm T-que-chega `[0,34]`(B) + X a 55 cm `[35,89]`(A): W005/W012; X + T na ponta: W075/W086; 69 cm T `[0,34]`(B) + canto `[35,69]`(A): W006/W013/W137/W139; 124 cm L `[0,34]`(A) + X `[35,89]`(B) + L `[90,124]`(B): W021/W022/W140/W141; W080 (379 cm, canto com B34 nas duas fiadas, 11) | 0 | 2 (W027/W129) | 40 — W027/W028/W129/W130: B34 `T_INTERSECTION_DEGRADED_L` duplicada no mesmo lugar contra C09 de reparo de abertura | 0 | 0 | 0 |

Todos os casos A têm a MESMA física: as duas peças de nó são de nós
diferentes e se encostam junta a junta, cada uma numa fiada; o trecho de
preenchimento ao lado é de uma peça só (B19 / `C09 C09`) entre dois
contornos fixos — nenhum layout do catálogo move a junta.

## 3. Reprodução mínima (RED → GREEN)

`tests/test_tie_parity_abutting_ties.py`: `t_l_69` (T + L, 69 cm),
`t_x_fill_left` (T + X a 55 cm, fill à esquerda do B54, 607 cm),
`x_t_fill_right` (X + T na ponta, fill à direita), `t_chain_on_main` (três T
a 55 cm na principal com bonecas de 69 cm até cantos), `l_x_l_124` (aresta
isolada) e `l_x_l_124_coordenado` (residual). Sem a paridade cada fixture
produz a junta NÓ|FILL × NÓ|FILL (medidor `tie_tie_prism_violations` sobre a
geometria final); com ela, zero — e zero nó|fill, zero colisão, zero falha de
nó, mesmo número de amarrações em qualquer ordem de entrada.

## 4. Causa raiz e algoritmo

Ver regra 33.9 (`nuvem/REGRAS_MODULACAO_BLOCOS.md`) e o cabeçalho de
`ABUTTING_TIE_PARITY_ENABLED` em `wall_stepper.py`. Resumo: a junta de
contorno da peça de nó é fixa pela geometria do encontro (30.6/33.1 já a
publicam ao fill); quando a peça de OUTRO nó começa exatamente onde esta
termina, numa fiada diferente, a junta corrida é certa. Solução local: censo
pré-preenchimento → restrições XOR (coincidência = "um inverte"; encostadas
na mesma fiada = "invertem juntos") → 2-coloração geométrica → inversão de
paridade (T/X marca 11.12; canto livre/aresta isolada troca de `arms` + pino,
31/32) → re-solução dos nós → aceite só com queda estrita. Custo: sem
preenchimento por tentativa.

## 5. Métrica antes/depois (régua V2, `run_project(write_files=False)`)

| | TP1 antes | TP1 depois | TGD antes | TGD depois |
|---|---|---|---|---|
| PRISM_CONTINUOUS_JOINT | 48 | **16** | 245 | **53** |
| A fill\|tie (NF×NF, nós distintos) | 32 | **0** | 203 | **0** (11 em W080 = mesma peça de canto nas duas fiadas) |
| B fill\|fill | 16 | 16 | 0 | 0 |
| C tie\|tie | 0 | 0 | 2 | 2 |
| D abertura/peça duplicada | 0 | 0 | 40 | 40 |
| PRISM_JOINT_STACK | 2 | 0 | 17 | 5 |
| nó\|fill (33.1) | 0 | 0 | 0 | 0 |
| INSIDE_DOOR / INSIDE_WINDOW | 0/0 | 0/0 | 0/0 | 0/0 |
| CROSSES_JAMB | 0 | 0 | 96 | 96 |
| POSITION_OVERLAP | 11 | 11 | 140 | 140 |
| JUNCTION_MISSING_BINDING | 9 | 9 | 0 | 0 |
| COVERAGE (todas) | iguais | iguais | iguais | iguais |
| COMPENSATOR_CONSECUTIVE / EXCESS / STRIP | 988/947/151 | 936/933/149 | 472/444/82 | 472/454/86 |
| blocos | 19.039 | 18.963 | 16.361 | 16.289 |
| críticos | 68 | 36 | 719 | 527 |
| tempo run_project | 90,0 s | 81,2 s | 273 s | 216 s |

## 6. Determinismo, performance, regressão consolidada, validação

Preenchido nas seções 7–9 (evidência em `evidence/2026-09-12-filltie-*`).

## 7. Determinismo

Ordem normal / reversa / permutada / endpoints invertidos: invariante
físico garantido em todas (teste `test_ordem_das_paredes_nao_muda_o_resultado`);
a composição do preenchimento já variava com a ordem antes desta CR (medido
com a paridade desligada: 4 assinaturas distintas em 4 ordens — convenção
`arms[0]`→A). Mesmo input em três processos separados: fingerprint canônico
idêntico — TP1 `f72853f978eac9807725295577250f71e0426e52acb4b9876afb6705f0569a00`
×3; TGD `1403b49da5d2e2bdf4e14c3dab0a0dfc142976693e6b5598547e4f9a9395a648` ×3 (`evidence/2026-09-12-filltie-determinism.json`).

## 8. Regressão consolidada

`python3 -m pytest tests -q -p no:cacheprovider` no HEAD de produção `fb618b2`
(tree `39bde403…`), Linux, Python 3.11.15, pytest 9.1.1, capturada por
`tools/documentation/capture_validation.py` (PID 3138, timeout 7000 s) em
`evidence/2026-09-12-filltie-regressao-consolidada.{json,txt}`:

**4 failed / 1109 passed em 2.395,56 s (39m55s), exit code 1**, terminada às
15:59:47 UTC (os dois watchers bash desta sessão ficaram presos por `pgrep -f`
casar a própria linha de comando; encerrados sem relançar nada).

| Falha | Assercão | Natureza |
|---|---|---|
| `tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]` | `REGRESSAO CRITICA … JUNCTION_MISSING_BINDING 8 → 9` contra o baseline V1 | HISTÓRICA (8cdd33f/cf325f2/c3eb0a1/4d6eecf); JUNCTION continua 9 |
| `…::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]` | `REGRESSAO em torre_easy_lo_r00_tgd/v2: [{'category': 'compensators', 'before': 61, 'after': 62}]` | NOVA, nível 2: W016 (1483 cm, principal de uma cadeia de T invertida) passa a contar 2 `COMPENSATOR_EXCESS_IN_RUN` (trecho 270..1084 das fiadas 13/15) + 1 `VERTICAL_STRIP` (C04 de jamb em t=612, 9 de 17 fiadas) — as MESMAS peças (`B19 C04` de jamb das portas) trocaram de fiada com o B54 do T e a contagem por faixa/banda é assimétrica entre fiadas pares e ímpares. Categoria de paredes reprovadas 61 → 62; críticos do TGD 719 → 527. Baseline V2 NÃO regravado (governança) — decisão do usuário |
| `tests/test_block_arm_role_candidate_safety_contract.py::test_t1_t9_candidato_seguro_e_aceito_no_tgd_real` | `esperava pelo menos 1 candidato aceito no TGD` | asserção de MECANISMO: a aresta isolada 91/SAME_B que o SAFE REPAIR aceitava passa a ser resolvida antes, pela paridade (canto pinado). Reproduzido isolado (`_scripts/2026-09-12-filltie-arm-check.py`, TGD V1, paridade ON × OFF): accepted [91/SAME_B] → [], rejected 19 → 6, paredes com prisma forçado 25 → 19, colisões 1121 = 1121, auditorias reprovadas 26 → 20, parede 23 sem prisma forçado nas duas. Teste ajustado ao contrato físico (aceita alguém OU 91 sem prisma forçado; 23 nunca rejeitada e sem prisma) |
| `tests/test_block_arm_role_prism_stagger.py::test_w076_tp1_coincidencia_de_contorno_foi_resolvida_pelo_arm_safe_repair` | `esperava um candidato ARM aceito para W076 (wall_idx=75)` — o primeiro assert (juntas de W076 não coincidem) PASSOU | idem: W076 (69 cm L-L, aresta isolada) resolvido pela paridade; reproduzido isolado (TP1 V1): accepted [75/SAME_A] → [], prisma forçado 23 → 21 paredes, colisões 8 = 8, auditorias 25 → 23. Teste ajustado (aceito OU não rejeitado; prova física mantida) |

Efeito colateral medido na reprodução (`_scripts/2026-09-12-filltie-nonmod.py`):
`non_modular` do solver TP1 V1 43 → 57 e TGD V1 2676 → 2739 — todos
`SEM_ESPACO` de **−1 cm** entre duas peças de nó ENCOSTADAS na mesma fiada
(ex.: TP1 walls 2/7 fiada B `[1310,1309]`, 7 bandas/variantes cada): o laço de
trechos de `solve_wall_free_fill` reporta como conflito o trecho vazio entre
duas amarrações que compartilham uma junta — bookkeeping pré-existente (wall
75 fiada A tinha o mesmo antes), sem peça faltando (COVERAGE idêntica no
benchmark). Correção pequena (ignorar trecho de −J entre dois contornos de nó)
registrada como pendência, não feita aqui para não mudar produção depois do
HEAD avaliado.

Zero skip/xfail; nenhum baseline/reference/threshold tocado.

## 9. Validação documental

`python3 tools/documentation/validate.py --base ad46c61 --main origin/main --require-current-main`
→ `PASS: versioned documentation, commit provenance and explicit local links`
(clone completo após `git fetch --unshallow`; sem isso o validador acusava
`official revision is not integrated: 8a93a27`, o mesmo artefato de clone raso
registrado na revisão do #38).

## Veredito

**PARTIAL — FILL|TIE FIXED, OTHER PRISM REMAINS.** Gates da missão: (1)
casos classificados por chave física; (2) reprodução mínima (6 fixtures);
(3) RED antes; (4) correção geral (nenhum comprimento/peça/nó hardcoded;
regra #1 aplicada à paridade); (5) fill|tie = 0 no TP1; (6) fill|tie entre
nós distintos = 0 no TGD (W080 = mesma peça de canto nas duas fiadas, fora
da paridade, reportado); (7) nó|fill 0; (8) INSIDE_DOOR 0; (9) INSIDE_WINDOW
0; (10) nenhuma regressão crítica (CROSSES_JAMB/OVERLAP/COVERAGE/JUNCTION
iguais; delta nível 2 de +10 EXCESS_IN_RUN/+4 STRIP no TGD registrado);
(11) determinismo; (12) custo local (<1 s por planta); (13) focados verdes;
(14) consolidada compreendida: 4 falhas nomeadas, 1 histórica, 1 categoria nível 2 (compensators 61→62 no TGD V2) e 2 asserções de mecanismo ajustadas (seção 8); (15) 33.9 + checkpoint + status. Sem MCP, sem
Revit, sem merge.
