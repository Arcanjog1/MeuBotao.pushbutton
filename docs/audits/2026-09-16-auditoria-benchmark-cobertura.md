# Auditoria do benchmark e da cobertura de regressão (2026-09-16)

Missão paralela, **somente leitura** sobre solver, UI e PR #42. Nada em
`nuvem/core/**`, `Script.py`, arquivos de UI, `nuvem/REGRAS_MODULACAO_BLOCOS.md`
ou `docs/PROJECT_STATUS.md` foi alterado. Nenhum merge foi feito.

## 1. Main observada

| Item | Valor |
|---|---|
| `origin/main` | `55e990d962ed22ae1021f0d335db197607bddda1` (merge do PR #41) |
| Data da observação | 2026-09-16, após `git fetch origin` |
| `docs/PROJECT_STATUS.md` na main | declara `main = 61d4f6c` (merge do #40) — **defasado em 3 commits** |
| Testes coletados na main | **1.243** (`pytest --collect-only -q`) |
| Arquivos de teste | 55 (`tests/` 41, `tests/regression/` 9 + `conftest.py`, `nuvem/tests/` 3, `tools/documentation/` 2) |
| Marcados `slow` | 20 declarações (**31 testes** após parametrização) (`tests/regression/test_benchmark_baselines.py`, `test_block_b19_*`, `test_cross_band_*`, `test_block_arm_role_candidate_safety_contract`, `test_script`) |
| Suíte completa medida | **2 falharam, 1.241 passaram em 2.380,72 s (39min40s)** — Linux, CPython 3.11 |
| Falhas na main | `test_benchmark_baselines[torre_easy_lo_r00_tp1]` e `[torre_easy_lo_r00_tgd-v2]` |
| `skip`/`xfail` | 7 pontos, todos condicionais (fixture/corpus/baseline ausente, `skipif` de plataforma) — **nenhum `xfail` mascarando defeito** |

## 2. PR #42 observado (somente leitura)

| Item | Valor |
|---|---|
| Head | `7724ab68d7a695062605c96ae9ef81a27428ee1e` |
| Base | `55e990d` (= main atual) |
| Estado | aberto, **draft**, `mergeable_state: unstable` |
| Tamanho | 43 arquivos, +9.974 / −45, 38 commits |
| Motor tocado | `wall_stepper.py`, `wall_modeling.py`, `continuous_modulation.py` + 4 módulos novos (`b34_run_arrangement`, `small_void_alignment`, `opening_micro_adjust`, `physical_support`) |
| Testes novos | 7 arquivos, ~90 funções (`test_b34_run_arrangement`, `test_b34_small_void_alignment`, `test_opening_micro_adjust`, `test_compensator_adjacency`, `test_degraded_node_tie_block`, `test_physical_support_audit`, `test_physical_tolerance_trial`) |
| Regras novas | §52–§66 de `REGRAS_MODULACAO_BLOCOS.md` |
| Único check de CI | **vermelho** — `check-status-doc`: `ERROR: docs/checkpoints/2026-09-15-butanta-modulation-physical-fixes.md: head: expected full 40-character commit SHA` |

O check vermelho do PR #42 é **documental**, não físico — observação registrada
aqui apenas como leitura; corrigi-lo é da sessão dona do PR.

Observação de escopo que muda a leitura de toda a matriz abaixo: as seções
**60–65 são explicitamente "só CHANNEL"**. O caminho legado (`strategy=None`,
o default de instalação) não recebe nenhuma das correções físicas do PR — e é
o caminho que os corpora TP1/TGD V2 exercitam. Por isso "corpora legados
idênticos achado por achado" **não é evidência de não-regressão das correções
novas**: é evidência de que elas não são exercitadas pelo corpus permanente.

## 3. Mapa da suíte — o que cada corpus prova

### 3.1 Corpus permanente do benchmark (`nuvem/benchmark/projects/`)

Três projetos, e só três:

| Projeto | Tipo | Confiança | O que prova |
|---|---|---|---|
| `torre_easy_lo_r00_tgd` | `HUMAN_REFERENCE_AVAILABLE` / HUMAN | MEDIUM | comparação contra gabarito humano medido; réguas V1 (raiz) e `v2/` |
| `torre_easy_lo_r00_tp1` | `HUMAN_REFERENCE_AVAILABLE` / HUMAN | MEDIUM | idem, input derivado do gabarito; réguas V1 e `v2/` |
| `piloto_sintetico_2x2` | `SOLVER_GENERATED_ONLY` | NONE | fixture de infraestrutura — **não é referência** |

O manifesto cataloga mais dois (`chacara_torre_easy_lo_tropicale`,
`torre_easy_lo_r00_full_building`), ambos `ANALYSIS_ONLY_REFERENCE` /
`confidence: NONE`: só existe resumo agregado, sem geometria reproduzível —
não rodam e não comparam.

**BUTANTÃ não é projeto de benchmark.** Toda a evidência do BUTANTÃ vive em
`docs/checkpoints/evidence/` (224 arquivos versionados) e em scripts avulsos
de `evidence/_scripts/`. Não há `input.json`/`reference.json`/`baseline.json`
para o BUTANTÃ, logo **nenhuma métrica do BUTANTÃ é comparada automaticamente
por nenhum teste**.

### 3.2 Benchmark V1 × V2

`runner.project_paths(project_id, version)`: V1 é a raiz do projeto
(HISTORICAL, nunca regravada); `v2/` é a régua com a topologia do motor atual
(FASE A regenerada em 2026-09-12). Os insumos (`reference.json`,
`input_real.json`, `metadata.json`, `evaluation_scope.json`) são
compartilhados; só baseline/score/result são versionados.

### 3.3 Validadores — a taxonomia oficial

`nuvem/benchmark/validators/base.py` é a fonte única: **28 classes de erro**,
6 categorias (`prism`, `compensators`, `junctions`, `openings`,
`wall_coverage`, `block_positions`), cada uma NÍVEL 1 (obrigatória) ou
NÍVEL 2 (preferência).

**O que a taxonomia NÃO tem nenhum código para:**
vazado menor do B34, canaleta (CHANNEL), apoio físico entre fiadas,
junta nó|fill e fill|tie como classes próprias, aglomerado de especiais,
microajuste de abertura, `NON_MODULAR`. São exatamente as áreas em
desenvolvimento.

### 3.4 Os quatro gates de corpus

`tests/regression/test_benchmark_baselines.py`, 11 testes parametrizados, **todos `slow`**:

1. `test_projeto_nao_regrediu_contra_o_baseline` — crítico novo ou categoria pior ⇒ falha;
2. `test_nenhum_validador_quebra_no_projeto` — validador que levanta exceção devolve categoria vazia (parece "sem erro");
3. `test_o_solver_produz_alguma_coisa` — rede contra catálogo recusado;
4. `test_projeto_nao_regrediu_contra_o_baseline_versionado` — idem contra a régua `v2/`.

**Este é o único gate de corpus do repositório inteiro.**

### 3.5 Demais corpora

| Corpus | Arquivos | Testes | O que prova |
|---|---|---|---|
| Motor headless (dublês) | `tests/test_script.py` | 262 | pareamento de faces, grafo L/T/X, pipeline parede a parede, regra #1, criação Etapa 5, varredura de colisão por topologia |
| GOLDEN (formato de saída) | `tests/test_golden_benchmark.py` | 90 | manifesto, fingerprint, inventário, comparação, relatório — **não importa `core/engine/*`**: prova o formato, nunca o motor |
| Infra do benchmark | `tests/regression/test_benchmark_infra.py` | 21 | identidade de parede, comparador, score, sobre plantas desenhadas à mão |
| Validadores red/green | `tests/regression/test_validators.py` | 23 | cada validador contra um defeito plantado + o controle sem o defeito |
| Ponte FASE A | `test_wall_modeling_bridge.py` (21) + `test_wall_modeling_snapshot_serialization.py` (5) | 26 | `input_real → run_wall_modeling → snapshot`, headless, e serialização sobre planta real |
| Constantes | `test_engine_constants_match.py` | 23 | impede o benchmark de medir uma regra que o motor não tem mais |
| CRs de medição | `test_junction_elevation_identity_cr_v1.py` (13), `test_validator_coverage_expected_rows_cr_c1.py` (19), `test_reconstruct.py` (12) | 44 | fidelidade do validador (elevação física; fiada esperada física) |
| PRISMA / amarração | `test_block_bonding.py` (32), `test_block_node_fill_revalidation.py` (28), `test_tie_parity_abutting_ties.py` (22), `test_block_arm_role_*` + `test_block_arm_safe_repair_gate_fidelity` (52), `test_cross_band_joint_propagation_cr_g12.py` (20), `test_bond_strip_adjacent_courses.py` (9) | 163 | junta vertical, nó\|fill, fill\|tie, papel de braço, fronteira entre bandas, faixa vertical |
| Aberturas | `test_opening_reconstruction_cr_a.py` (44), `test_block_fit_tolerance_c04_jamb_guard.py` (73), `test_room_probe_inside_opening.py` (16) | 133 | identidade × geometria do vão, guarda de jamba, sonda dentro do vão |
| CHANNEL | `test_channel_reinforcement.py` (34), `test_channel_audit_fixes.py` (40), `test_channel_ui_and_family_gate.py` (10) | 84 | ver §8 |
| B19 | `test_block_b19_residual_fill_implementation.py` | 76 | B19 é FILL, nunca TIE |
| Beta / criação | `test_beta_atomic_creation.py` (28), `test_controlled_beta_preflight.py` (22), `test_beta_package.py` (10), `test_block_lot_persistence.py` (5) | 65 | criação transacional, fail-closed, lote persistente |
| UI / travamento | `test_console_pump_ui_thread_guard.py` (5), `test_analyze_sincrono_sem_thread.py` (7), `test_perf_trace_stall_sampler.py` (4) | 16 | causa-raiz dos congelamentos medidos no Revit |

**TP1 e TGD só existem como corpus em (3.4) e em quatro testes que leem
`reference.json` diretamente.** Não há "suíte TP1" nem "suíte TGD"
separadas — o que existe é um baseline por projeto por régua.

## 4. Erros reais do BUTANTÃ — cobertura por defeito

Levantados de `REGRAS_MODULACAO_BLOCOS.md` §41/§49/§50/§51, dos checkpoints de
2026-09-10 a 2026-09-15, do `ERROR_HISTORY.md` e do corpo do PR #42. Salvo a
linha 14 (marcada), todos apareceram no **Revit real** do BUTANTÃ R08_LT ou do
doc de teste `butanta testes` — não em bancada.

Colunas: **FIX** = fixture mínima versionada; **TESTE** = teste permanente que
falha se voltar; **MÉTRICA** = contador no benchmark oficial; **CI** = algum
workflow executa; **AUTO** = uma regressão futura seria pega automaticamente.

| # | Defeito real | FIX | TESTE | MÉTRICA | CI | AUTO |
|---|---|:--:|:--:|:--:|:--:|:--:|
| 1 | Nível com Base = Ponto de Levantamento: modulação 726 m acima das paredes | sim | `test_level_internal_elevation` (4) | não | **não** | **não** |
| 2 | `MirrorElement` cria cópia: 54 compensadores duplicados, órfãos sobrevivem à troca de lote | sim | `test_mirror_in_place` (2) | não | **não** | **não** |
| 3 | Lote anterior não apagado: 8.399 blocos por cima de 7.257, 13.940 avisos, UI travada | sim | `test_block_lot_persistence` (5) | não | **não** | **não** |
| 4 | `Application.DoEvents()` na thread de fundo: 2.652 s parados | sim | `test_console_pump_ui_thread_guard` (5) + `test_analyze_sincrono_sem_thread` (7) | não | **não** | **não** |
| 5 | Layer arquitetônico traz 46 pares; layer estrutural correto é outro (§49) | **evidência**, não fixture | `test_reference_layer_filter` (4) — **pula se o JSON sumir** | não | **não** | **não** |
| 6 | Reserva de amarração 34 cm em ponta livre (paredes de 99 cm): junta corrida em 14 fiadas | sim | `test_free_end_reserve` (3) | não | **não** | **não** |
| 7 | Reserva de canto por fiada (paredes curtas de 64 cm), §11.14 | sim | `test_corner_reserve_per_course` (7) | não | **não** | **não** |
| 8 | Trecho de 466 cm fechava com `11×B39 + C09 C09 C04` (3 compensadores em sequência) | sim | `test_fill_prefers_b34_row_over_stacked_compensators` (5) | `COMPENSATOR_EXCESS_IN_RUN` | **não** | **não** |
| 9 | Falso positivo `REPEATED_VERTICAL_COMPENSATOR_STRIP` na parede de 69 cm | sim | `test_bond_strip_adjacent_courses` (9) | `COMPENSATOR_VERTICAL_STRIP` | **não** | **não** |
| 10 | Anel de 4 paredes (115×86 cm) sem preenchimento em todas as fiadas + `MISSING_REQUIRED_CHANNEL` (vão 7719511) | sim | `test_node_bounded_residual` (12) | não | **não** | **não** |
| 11 | Convenção fixa de paridade por papel obriga compensador empilhado | **evidência** | `test_tie_parity_local_search` (4) — **pula se a fixture sumir** | não | **não** | **não** |
| 12 | Junta corrida `fill\|tie` (duas peças de nó encostadas em fiadas opostas) | sim | `test_tie_parity_abutting_ties` (22) | `PRISM_CONTINUOUS_JOINT` | **não** | **não** |
| 13 | Boneca curta atravessando parede; amarração que não cabe (§11.10/§11.11) | sim | `test_scale_autofix_rules` (12) | não | **não** | **não** |
| 14 | Sonda de vão media espaço ATRAVÉS da porta → peça dentro do vão (auditoria beta 2026-09-09, caso W019 do **TP1** — incluído aqui por ser a mesma classe física) | sim | `test_room_probe_inside_opening` (16) | `OPENING_BLOCK_INSIDE_DOOR` | **não** | **não** |
| 15 | CHANNEL: canaleta na verga, sob peitoril, T, passagem livre, corte, família ausente | sim | 84 testes (§7) | não | **não** | **não** |
| 16 | **Vazado menor do B34 desalinhado — 1.931 ocorrências na BASE** | só no PR #42 | só no PR #42 (10) | **não** | **não** | **não** |
| 17 | **Peças sem apoio — 50 na bancada BASE** | só no PR #42 | só no PR #42 (5) | **não** | **não** | **não** |
| 18 | **`NON_MODULAR` — 78 na BASE** | não | **não** | **não** | **não** | **não** |
| 19 | **Buracos — 94 (3.754 cm) na BASE** | não | **não** | **não** | **não** | **não** |
| 20 | **`C09+C09` / `C09+C04` encostados — 11 / 98 na BASE** | parcial (PR #42) | parcial — `COMPENSATOR_CONSECUTIVE` cobre o par obrigatório | parcial | **não** | **não** |
| 21 | **`MISSING_UNDER_WINDOW` — junta de 1,6 cm contada como vazio** | não | **não** | **não** | **não** | **não** |
| 22 | **Faixa de 20–35 cm entre peça de nó e jamba — 41 casos censados (§66)** | só no PR #42 | só no PR #42 (10) | **não** | **não** | **não** |
| 23 | **Pastilha de 9 cm na amarração do nó T degradado (§58)** | só no PR #42 | só no PR #42 (6) | **não** | **não** | **não** |
| 24 | **`C04+C04` que deveria virar o compensador do vão total (§54)** | só no PR #42 | só no PR #42 | **não** | **não** | **não** |
| 25 | Realce de colisão infla ~127× (11.211 marcadas × 55 reais) — §17.1 | não | **não** — declarado NÃO corrigido | não | **não** | **não** |

### 4.1 Leitura da tabela

- **Coluna CI: `não` em 25 de 25 linhas.** Nenhum defeito real do BUTANTÃ tem
  detecção automática, porque nenhum workflow roda a suíte (§10).
- **Coluna MÉTRICA: `não` em 20 de 25.** As cinco exceções são códigos que já
  existiam na taxonomia antes do BUTANTÃ. **Nenhuma métrica nova nasceu do
  BUTANTÃ no benchmark oficial** — todas ficaram na bancada de evidência.
- **Onde há teste, o padrão é bom**: fixture mínima, geometria sintética
  derivada da medição, controle vermelho. Os itens 1–15 são trabalho de
  qualidade. O problema é a segunda metade da tabela.
- **Os itens 16–24 são exatamente a área de desenvolvimento ativo** e existem
  apenas dentro do PR #42. No dia em que o PR for mesclado, esses testes entram
  — mas **sem métrica de corpus e sem CI**, o que significa que protegem a
  *lógica* das funções novas e não o *resultado físico* sobre uma planta.
- **Itens 18, 19, 21 e 25 não têm nada**: nem fixture, nem teste, nem métrica.
  São os quatro pontos cegos absolutos.

## 5. Matriz REGRA × TESTE

Legenda: **COVERED** = teste permanente que falha se o defeito voltar;
**PARTIAL** = coberto num nível (unidade ou validador) mas não no nível em que
o defeito apareceu; **ONLY_DIAGNOSTIC** = existe régua/medição, mas nenhum
teste que reprove; **NOT_COVERED** = nada.

"GATE REAL?" pergunta se **algum processo automático** reprova. Como nenhum
workflow de CI executa `pytest` (ver §10), a coluna significa: *o teste existe
e falharia se alguém rodasse a suíte*.

| REGRA / DEFEITO | TESTE EXISTE? | CORPUS | GATE REAL? | Classe |
|---|---|---|---|---|
| bloco dentro de porta | sim — `test_validators` red/green, `test_room_probe_inside_opening` (16), `test_bench_z_origin` | sintético + TGD/TP1 | validador NÍVEL 1 crítico no gate de corpus | **COVERED** |
| bloco dentro de janela | **não** — `OPENING_BLOCK_INSIDE_WINDOW` não é citado por nenhum teste | — | só via corpus, se aparecer | **NOT_COVERED** |
| B34 small void (vazado menor) | só no PR #42 (`test_b34_small_void_alignment`, 10) | fixtures sintéticas | não há código na taxonomia; não entra em score | **NOT_COVERED na main / PARTIAL no PR** |
| node\|fill | sim — `test_block_node_fill_revalidation` (28) | sintético + corpus | `PRISM_CONTINUOUS_JOINT` crítico | **COVERED** |
| fill\|tie | sim — `test_tie_parity_abutting_ties` (22), `test_tie_parity_local_search` (4) | sintético + evidência BUTANTÃ | idem | **COVERED** |
| B34 sobre abertura | parcial — `test_channel_reinforcement::tee_main_b54_over_span`, `OPENING_MISSING_LINTEL` citado só em `test_bench_z_origin` | sintético | `OPENING_MISSING_LINTEL` é NÍVEL 2 | **PARTIAL** |
| B34 entre bandas | **não** — `test_cross_band_joint_propagation_cr_g12` cobre a *junta* entre bandas, nunca a *composição* de B34 entre bandas | — | — | **NOT_COVERED** (é a limitação declarada do próprio PR #42) |
| C09+C09 | sim — `COMPENSATOR_CONSECUTIVE` red/green + `test_script::pier_ordered_layout_nunca_devolve_dois_compensadores_iguais_adjacentes`; PR #42 acrescenta `test_compensator_adjacency` (9) | sintético + corpus | NÍVEL 1 major | **COVERED** |
| clusters de especiais | régua existe (`opening_micro_adjust.special_clusters`, `_scripts/`), nenhum teste que reprove | — | §59 do PR mede o humano em 109 e classifica como **preferência** | **ONLY_DIAGNOSTIC** |
| B19 | sim — `test_block_b19_residual_fill_implementation` (76), `test_forced_half_licence` (5) | sintético + TP1 | contrato "B19 é FILL, nunca TIE" | **COVERED** |
| T com B54 | parcial — `test_channel_reinforcement` (T com jamba na face, B54 sobre o vão), `JUNCTION_WRONG_PIECE` citado só em `test_benchmark_infra` | sintético | `JUNCTION_WRONG_PIECE` é NÍVEL 2; `JUNCTION_HALF_BLOCK_ADJACENT` **sem teste** | **PARTIAL** |
| CHANNEL superior | sim — porta/janela na verga, topo fora da grade, vão até o topo | sintético BUTANTÃ-derivado | validador independente no teste | **COVERED** |
| CHANNEL inferior | sim — canaleta sob peitoril, janela nunca free-to-top | idem | idem | **COVERED** |
| under-window | parcial — `OPENING_SOLID_BELOW_SILL_MISSING` red/green existe; `MISSING_UNDER_WINDOW` (a métrica que o PR move de 1 → 0) **não existe na taxonomia** | sintético | NÍVEL 1 major | **PARTIAL** |
| apoio (peça sem apoio) | só no PR #42 (`test_physical_support_audit`, 5) | fixtures sintéticas | nenhum código na taxonomia | **NOT_COVERED na main** |
| collision | sim — `POSITION_OVERLAP` red/green + varredura de topologias em `test_script` | sintético + corpus | NÍVEL 1 crítico | **COVERED** |
| junction | sim — `JUNCTION_MISSING_BINDING` red/green, CR-V1 (13) | sintético + corpus | NÍVEL 1 crítico | **COVERED** |
| prism | sim — `PRISM_CONTINUOUS_JOINT` red/green + 163 testes de amarração | sintético + corpus | NÍVEL 1 crítico | **COVERED** |
| coverage | sim — 7 dos 8 códigos com teste; CR-C1 (19) | sintético + corpus | NÍVEL 1 | **COVERED** |
| non-modular | parcial — `COVERAGE_WALL_NOT_MODULATED` tem red/green; `NON_MODULAR` como contador do motor (78 → 0 no PR) **não tem teste nem código de taxonomia** | sintético | — | **PARTIAL** |
| determinismo | sim — ≥25 testes (ordem, permutação, translação, inversão de endpoints, processos separados) | sintético + corpus | ver §9 | **COVERED (unidade) / PARTIAL (planta inteira)** |
| idempotência | parcial — `test_channel_reinforcement::planning_is_idempotent`, `test_block_lot_persistence` (5), PR #42 acrescenta idempotência do arranjo | sintético | idempotência **no Revit** só por evidência manual | **PARTIAL** |
| opening micro-adjustment | só no PR #42 (`test_opening_micro_adjust`, 10) | fixtures sintéticas | sem chamador de produção (ver §14, B7) | **NOT_COVERED na main / PARTIAL no PR** |

### 5.1 Códigos da taxonomia oficial sem NENHUM teste

Sete dos 28 códigos não são citados por teste algum:

| Código | Nível | Severidade |
|---|---|---|
| `OPENING_BLOCK_INSIDE_WINDOW` | **1** | **crítica** |
| `JUNCTION_HALF_BLOCK_ADJACENT` | **1** | major |
| `POSITION_OFF_AXIS` | **1** | major |
| `POSITION_BAD_ORIENTATION` | **1** | major |
| `PRISM_JOINT_STACK` | **1** | major |
| `COMPENSATOR_AVOIDABLE` | 2 | menor |
| `OPENING_MISSING_COUNTER_LINTEL` | 2 | menor |

`OPENING_BLOCK_INSIDE_WINDOW` é o achado mais grave desta lista: mesmo nível e
severidade de `OPENING_BLOCK_INSIDE_DOOR` (que tem 4 arquivos de teste) e zero
cobertura. Se o validador de janela quebrar, ele devolve lista vazia — que se
parece com "nenhum erro" — e nada reprova.

## 6. Cobertura do B34

| Item | Main | PR #42 | Classe |
|---|---|---|---|
| vazado menor | nada | `test_b34_small_void_alignment`: red/green, peça de nó nunca gira, giro rígido, invariância a translação/ordem/sentido, validador com B34 deslocado 20 cm, rotação em par | **PARTIAL** |
| B34×B39 | nada específico | coberto de lado pelas corridas (`test_b34_run_arrangement`) | **PARTIAL** |
| B34×B34 | nada específico | `test_pair_rotation_green_aligns_both_small_voids` | **PARTIAL** |
| B34 sobre janela | nada | nada — a §66 mexe na posição do vão, não no B34 sobre ele | **NOT_COVERED** |
| B34 perto de T/L | `test_corner_reserve_per_course` (7), `test_free_end_reserve` (3), `test_scale_autofix_rules` (12) | `test_degraded_node_tie_block` (6): T degradado amarra com bloco quando o toco tem espaço | **COVERED** (para reserva/degradação), **NOT_COVERED** para *vazado menor* perto de nó |
| B34 em fill | `test_fill_prefers_b34_row_over_stacked_compensators` (5) | arranjo das corridas | **COVERED** |
| B34 entre bandas | nada | nada | **NOT_COVERED** |
| orientação | nada na main | `test_dp_orientation_reaches_the_brute_force_minimum_on_a_real_slice`, `..._does_not_depend_on_family_order`, limite inferior nunca acima do mínimo exato, idempotência | **COVERED (no PR)** |
| posição | `test_block_bonding` / `POSITION_*` | ordem das corridas: mesmas peças, mesmos extremos, peças fixas nunca se movem | **COVERED (no PR)** |

### 6.1 O que continua desprotegido no B34, mesmo com o PR #42

1. **Duas réguas diferentes para a mesma regra.** `_scripts/b34rule.py` (régua
   "externa", que bateu com o Revit) e o contador do motor dão números
   diferentes para o mesmo lote: `metrics_summary.json` registra
   `b34_small_void_violations_external: 336` contra
   `b34_violations_engine: 264` no mesmo `revit_final`. Nenhum teste amarra
   as duas. Uma régua pode derivar da outra sem ninguém perceber.
2. **A régua externa não é código de produção.** `b34rule.py` vive em
   `docs/checkpoints/evidence/.../_scripts/`, importa `pmodel` por
   `sys.path.insert`, e nenhum teste o importa. É o instrumento que decidiu
   "1.931 → 34" e ele não tem teste próprio.
3. **Nenhum teste fixa o número.** Não existe um teste de fixture que diga
   "nesta parede real, violações = N". Uma regressão que leve 34 → 300
   passa em todos os testes verdes do PR.
4. **B34 sobre abertura e entre bandas**: declarados como próximo passo, sem
   fixture nem contador permanente.

## 7. Cobertura do CHANNEL

O corpus CHANNEL é o mais maduro do repositório: 84 testes, fixtures
sintéticas derivadas da física medida no BUTANTÃ, **sem nenhum `ElementId`,
W0xx ou coordenada de corpus**, com controles vermelhos explícitos
(`..._disabled_...red_control`) que provam que o teste reprova quando a regra
é desligada.

| Regressão | Detectaria? | Onde |
|---|---|---|
| canaleta superior ausente | **sim** | `door_gets_channel_course_on_head`, `window_gets_channel_on_head`, validador independente `MISSING_REQUIRED_CHANNEL` |
| canaleta inferior ausente | **sim** | `window_gets_channel_on_head_and_one_course_under_sill`, `window_with_sill_is_never_free_to_top` |
| canaleta extra | **sim** | `top_course_above_window_is_not_a_second_channel`, `opening_reaching_wall_top_gets_no_top_channel`, código `EXTRA_CHANNEL` |
| wrong course | **sim** | `independent_validator_catches_missing_wrong_course_and_invasion`, `head_one_joint_below_course_is_the_same_solution` |
| canaleta atravessando abertura | **sim** | `no_channel_piece_inside_any_active_opening_and_preflight_ok`, `CHANNEL_INVADES_OPENING`, `CHANNEL_OPENING_OVERCUT` |
| cut incorreto | **sim** | `compensators_merge_into_length_cut_channels`, `create_sets_instance_length_for_length_cut_channel`, `create_fails_loudly_when_length_parameter_cannot_be_written` |
| free-to-top | **sim** | `passage_with_both_jambs_on_junction_ties_is_free_to_top` + controle vermelho, `free_to_top_opens_exactly_the_opening_and_keeps_masonry_outside_the_jambs`, `continuous_passage_opens_from_node_face_to_node_face` |
| T | **sim** | `tee_jamb_on_incoming_face_channel_crosses_node_like_human`, `tee_main_b54_over_span_is_split_into_two_channels`, `through_t_pattern_is_classified_specifically`, `normal_t_away_from_opening_is_never_crossed` — cada um com controle vermelho |
| famílias ausentes | **sim** | `test_channel_ui_and_family_gate` (10): falta de família bloqueia ANTES de calcular; `NONE` continua funcionando sem as famílias |
| idempotência | **parcial** | `planning_is_idempotent_on_already_reinforced_courses` cobre o *planejamento*. A idempotência **no Revit** (lote substituído, assinatura igual) é só evidência manual do checkpoint |

**Buracos do CHANNEL:**

- **Off-grid** está `NEEDS_RULE`/`NOT_COMPARABLE` (§51.8) — testado como
  "reporta e não põe canaleta", nunca como solução;
- **Cinta de topo** declarada fora de escopo, sem teste;
- **Conflito §10.7** ("canaleta sempre na última fiada") continua **NÃO
  RESOLVIDO** no `ERROR_HISTORY.md`, com três medições divergentes (39,4% /
  71,4% / 73,8%) e nenhum teste;
- **`CHANNEL_ALIGNMENT_ERROR`** — §59 registra "não medido nesta rodada".

## 8. Especiais — HARD ERROR × QUALITY METRIC

A separação já existe na taxonomia (`LEVEL_MANDATORY` × `LEVEL_PREFERENCE`) e
a §59 do PR #42 a aplica corretamente, **medindo o humano antes de decidir o
nível**. A régua a preservar está escrita lá: *"um validador que reprova o
projeto humano de referência está errado, não o projeto"* — e reprovou três
dos cinco validadores pedidos.

| Item | Classe correta | Cobertura hoje |
|---|---|---|
| `C09+C09` em pé encostados | **HARD ERROR** (humano = 0) | **COVERED** — `COMPENSATOR_CONSECUTIVE` NÍVEL 1 + `test_compensator_adjacency` no PR |
| `C04+C04` | **HARD ERROR** quando vira o compensador do vão total (§54) | **PARTIAL** — `test_physical_tolerance_trial::fusion_c04_c04_becomes_c09_same_span` (PR); nada na main |
| `C09+C04` | **QUALITY METRIC** (humano = 97 ocorrências) | **ONLY_DIAGNOSTIC** — contado no `metrics_summary.json`, sem validador |
| clusters (2 especiais a ≤40 cm) | **QUALITY METRIC** (humano 109 × solver 158) | **ONLY_DIAGNOSTIC** |
| compensadores consecutivos (3+) | **HARD ERROR** | **COVERED** — `COMPENSATOR_EXCESS_IN_RUN` + `test_fill_prefers_b34_row_over_stacked_compensators` |
| vertical strip | **HARD ERROR** com a correção de fiadas adjacentes | **COVERED** — `COMPENSATOR_VERTICAL_STRIP` + `test_bond_strip_adjacent_courses` (9), que nasceu de um **falso positivo real** |
| jamba (especiais junto da jamba) | **QUALITY METRIC** | **ONLY_DIAGNOSTIC** — §55 está marcada `DOCUMENTADO — pendência de código aberta`; comparador por lado de vão só existe em `_scripts/channel_strict_compare.py` |
| special density | **QUALITY METRIC** | **ONLY_DIAGNOSTIC** — total de especiais (714 → 594 × 500 do humano) não tem contador permanente |

**Achado:** `MID_WALL_HALF_BLOCK` e `REPLACEABLE_COMPOSITE_BY_B54` aparecem na
tabela de "pioras classificadas" do PR como se fossem métricas, e a §59 os
**refuta** (o humano usa *mais* dos dois). Duas linhas da tabela de pioras do
PR medem, portanto, uma não-regra. Isso não invalida o PR — mas qualquer CI
futuro que as transforme em gate reprovaria o projeto humano.

## 9. Determinismo

### 9.1 Já testado permanentemente

| Eixo | Testes |
|---|---|
| ordem de walls | `test_t6_permutacao_de_paredes`, `test_alternancia_do_no_independe_da_ordem_de_entrada`, `test_invariancia_a_ordem_de_entrada_das_paredes` (CR-C1), `test_g_determinismo_ordem_de_entrada_das_paredes` (CR-V1), `test_regras_sao_invariantes_a_ordem_de_coleta`, `test_invariante_a_ordem_de_entrada` |
| ordem de nodes / arms | `test_t14_arms_permutados_mesmo_resultado`, `test_t13_paredes_permutadas_mesma_identificacao_de_aresta` |
| endpoints invertidos | `test_g_invariancia_por_inversao_de_paredes_start_end`, `test_t43_invariante_a_reversao_dos_endpoints`, `test_l_corner_endpoint_reversal_equivalente`, `test_INV_CENTER_002`, `deterministic_and_endpoint_reversal_invariant` (CHANNEL) |
| translação | `test_g_invariancia_por_translacao`, `test_INV_02_translacao_arbitraria`, `test_invariancia_a_translacao_do_eixo`, `test_regras_sao_invariantes_a_translacao_global` |
| ruído | `test_floating_point_adversarial_noise`, `test_noise_beyond_old_tolerance_now_closes`, `test_ruido_de_geometria_do_cad_nao_reprova_pilarete`, `test_real_geometry_noise_stays_clean` |
| processos diferentes | `test_tres_processos_separados_dao_o_mesmo_fingerprint`, `deterministic_across_processes` (CHANNEL), `test_t52_determinismo_duas_execucoes_separadas` |
| identidade / ordem de dict | `test_planner_source_has_no_identity_keys`, `test_memo_key_has_no_identity_or_dict_order_dependency` |

### 9.2 O que ainda muda e NÃO tem teste permanente

Tudo abaixo está registrado em evidência (`metrics_summary.json` do PR #42),
nunca num teste:

| Sensibilidade | Medição | Teste? |
|---|---|---|
| translação (+1000, +500 cm) na planta inteira | 39 peças mudam — empate numérico pré-existente do planejador CHANNEL, **parede 0** | **não** |
| inversão de sentido na planta inteira | 9.102 peças × 9.103 normais; pré-existente (8.905 × 8.903 com as mudanças desligadas) | **não** |
| permutação de ordem na planta inteira | 9.087 × 9.103; pré-existente (8.905 × 8.888) | **não** |
| ruído de eixo 1,4e−14 ft | 39 peças de uma parede trocam B34 do início para o fim do trecho | **não** |

O padrão é claro: **o determinismo é testado por unidade e por invariante
local, nunca sobre a planta inteira.** As três sensibilidades acima são
conhecidas, medidas, classificadas como pré-existentes — e invisíveis para a
suíte. Um CR futuro que as piore não quebra nenhum teste.

## 10. CI — o que realmente roda

Existe **um único workflow**: `.github/workflows/check-project-status.yml`.

```
python3 -m unittest discover -s tools/documentation -p 'test_*.py' -v
python3 tools/documentation/validate.py --base <base> --main <main> [--require-current-main]
```

| Pergunta | Resposta |
|---|---|
| o CI executa `pytest`? | **não** |
| `runner.py --check`? | **não** — a string `--check` não aparece em nenhum workflow, script, Makefile ou hook |
| TP1? | **não** |
| TGD V2? | **não** |
| CHANNEL? | **não** |
| determinismo? | **não** |
| documentação? | **sim — e só isso** |

O próprio workflow declara no summary: *"Validacao estrutural; nao aprova
regras, benchmark ou solver."* A honestidade está no lugar certo; o problema é
que **não existe nenhum outro gate**. Toda a proteção física do projeto depende
de alguém lembrar de rodar `pytest` na mão e de ler o resultado.

Efeito colateral já ativo: `docs/PROJECT_STATUS.md` na main declara
`main = 61d4f6c`, enquanto `origin/main` está em `55e990d`. Com
`--require-current-main`, qualquer PR aberto agora reprova nesse workflow até
alguém reconciliar o status.

### 10.1 Proposta objetiva de CI

Números medidos nesta auditoria (CPython 3.11, container Linux).

**FAST GATE** — a cada push, **≈ 30 s medidos**

```
pytest -q -p no:cacheprovider \
       -m "not slow" \
       --deselect tests/test_block_node_fill_revalidation.py::test_t18_candidato_aceito_permanece_seguro_no_corpus \
       --deselect tests/test_block_arm_role_prism_stagger.py
```

1.206 testes. As duas linhas de `--deselect` são o conserto provisório do
marcador `slow` incompleto (§11.2): sem elas o mesmo comando leva **12,8 min**,
porque 6 testes de corpus não estão marcados. A correção definitiva é
acrescentar `@pytest.mark.slow` nesses 6 — uma linha por teste — e aí o gate
volta a ser só `-m "not slow"`.

Cobre motor headless, validadores red/green, PRISMA, aberturas, CHANNEL, B19,
determinismo por unidade, UI/travamento. É o gate que faltava, e ele cabe
folgado em qualquer push.

**MEDIUM GATE** — a cada PR, **≈ 5 min** (≈ 3,5 min com a fixture de sessão)

- FAST GATE, mais
- os 6 testes de corpus deselecionados acima (741 s hoje — é a parte cara)
- `pytest tests/regression/test_benchmark_baselines.py -k "piloto_sintetico or torre_easy_lo_r00_tp1"`
  (TP1 custa 82 s por asserção, TGD 47 s — mas TP1 é o que hoje falha, logo é
  o que precisa estar no gate)
- `python3 nuvem/benchmark/runner.py --run torre_easy_lo_r00_tp1 --check`
- o workflow documental que já existe.

**NIGHTLY / FULL** — diário na main e antes de merge autorizado — **39min40s medidos**

- suíte inteira, incluindo `slow` (TGD V1+V2, TP1 V1+V2)
- `runner.py --all --check`
- lote de determinismo de planta inteira (§9.2), quando existir
- publicação das métricas físicas do corpus BUTANTÃ (§12), quando existir.

**Regra que o CI precisa herdar do processo:** as falhas conhecidas precisam
virar uma lista explícita de *known failures* versionada e conferida pelo CI,
não um número decorado ("3 = main") repetido de checkpoint em checkpoint. E a
lista tem que registrar a plataforma: **nesta medição em Linux deram 2 falhas,
não 3** — `test_perf_trace_stall_sampler` passou aqui e só falha no Windows
(`sys.platform == "win32"`). Um número global sem plataforma não é
conferível. Ver §13.

## 11. Performance dos testes

### 11.1 Medição executada

`pytest -q --durations=60 -p no:cacheprovider` sobre a main `55e990d`,
container Linux, CPython 3.11, sem paralelismo.

```
2 failed, 1241 passed in 2380.72s (0:39:40)
FAILED tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]
FAILED tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]
```

**Distribuição do tempo**

| Grupo | Tempo | % da suíte |
|---|---:|---:|
| 31 testes marcados `slow` | **1.611,6 s** | 67,7% |
| 6 testes de corpus **não marcados** `slow` | **741,2 s** | 31,1% |
| **os outros 1.206 testes** | **≈ 28 s** | **1,2%** |

### 11.2 O achado que corrige a proposta de CI

**Seis testes consomem 96% do que sobraria num `pytest -m "not slow"`.** Eles
rodam o solver real sobre TP1/TGD e **não têm o marcador**:

| Tempo | Teste | Marcado `slow`? |
|---:|---|---|
| **255,49 s** | `test_block_node_fill_revalidation::test_t18_candidato_aceito_permanece_seguro_no_corpus` | **não** |
| **162,26 s** | `test_block_arm_role_prism_stagger::test_determinismo_w076_w041_duas_rodadas_identicas` | **não** |
| 81,55 s | `test_block_arm_role_prism_stagger::test_w010_tp1_com_abertura_nenhum_bloco_invade_o_vao` | **não** |
| 80,77 s | `test_block_arm_role_prism_stagger::test_w041_tp1_prisma_resolvido_de_verdade_nao_so_reportado` | **não** |
| 80,62 s | `test_block_arm_role_prism_stagger::test_w022_w093_tp1_cobertura_do_arm_role_consistency_preservada` | **não** |
| 80,49 s | `test_block_arm_role_prism_stagger::test_w076_tp1_coincidencia_de_contorno_foi_resolvida_pelo_arm_safe_repair` | **não** |

Consequência prática: `pytest -m "not slow"` hoje leva **≈ 12,8 min**, não os
3 min que o marcador promete. Corrigir o marcador nesses 6 testes (ou
deselecioná-los no gate) leva o FAST GATE para **≈ 30 s cobrindo 1.206
testes** — a diferença entre um gate que roda a cada push e um que ninguém
aguenta.

*O marcador `slow` está, portanto, incompleto: ele descreve a intenção, não o
custo real. Esta auditoria não altera testes; fica registrado como correção
de uma linha por arquivo.*

### 11.3 Os 10 mais lentos da suíte

| # | Tempo | Teste | `slow`? |
|---|---:|---|---|
| 1 | 255,49 s | `test_block_node_fill_revalidation::test_t18_...corpus` | não |
| 2 | 221,56 s | `test_benchmark_baselines::..._versionado[torre_easy_lo_r00_tgd-v2]` | sim |
| 3 | 163,90 s | `test_block_b19_residual_fill::test_t52_determinismo_duas_execucoes_separadas` | sim |
| 4 | 162,26 s | `test_block_arm_role_prism_stagger::test_determinismo_w076_w041_...` | não |
| 5 | 93,18 s | `test_cross_band_joint_propagation_cr_g12::test_determinismo_da_correcao` | sim |
| 6 | 93,14 s | `test_block_arm_role_candidate_safety_contract::test_t16_execucao_repetida_e_deterministica` | sim |
| 7 | 89,20 s | `test_block_b19_residual_fill::test_t49_tp1_fingerprint_identico_com_e_sem_b19` | sim |
| 8 | 85,92 s | `test_cross_band_...::test_fronteira_de_banda_deixa_de_criar_junta_continua[tp1]` | sim |
| 9 | 82,95 s | `test_benchmark_baselines::test_projeto_nao_regrediu_contra_o_baseline[tp1]` | sim |
| 10 | 82,47 s | `test_benchmark_baselines::..._versionado[torre_easy_lo_r00_tp1-v2]` | sim |

**Padrão:** os mais caros são, quase todos, **testes de determinismo e de
corpus que resolvem a planta inteira duas ou mais vezes**. O custo é inerente
ao que provam — o problema não é que existam, é que estão misturados com
testes de 20 ms sem uma separação confiável.

### 11.4 Trabalho duplicado, medido

**`test_benchmark_baselines.py`: 692,5 s no total.** `runner.run_project()`
não tem cache, e os três testes parametrizados pelos mesmos projetos chamam-no
do zero cada um. Os números mostram isso com nitidez — as três asserções sobre
TP1 custam praticamente o mesmo, porque cada uma refaz o mesmo solve:

```
82,95 s  test_projeto_nao_regrediu_contra_o_baseline[tp1]
82,46 s  test_o_solver_produz_alguma_coisa[tp1]
82,45 s  test_nenhum_validador_quebra_no_projeto[tp1]
```

e em TGD, idem: 46,74 / 46,91 / 46,97 s. Uma fixture de escopo de sessão
por `(project_id, version)` elimina ~2/3 desse tempo — **cerca de 390 s** —
**sem mudar uma única asserção**.

O mesmo padrão aparece em `test_block_arm_role_prism_stagger`: quatro testes
`w010`/`w041`/`w022_w093`/`w076` a ~80 s cada, todos sobre o mesmo TP1.

### 11.5 Outros candidatos a fixture menor

| Situação | Observação |
|---|---|
| `test_block_fit_tolerance_c04.py` (55) + `..._jamb_guard.py` (73) = 128 testes | **nenhum aparece entre os 60 mais lentos** — são baratos; a duplicação aqui é de leitura, não de tempo |
| `test_script.py` (262) | só dois testes caros (`INV_PAIR_002` e `INV_PAIR_003`, ~27,7 s cada), ambos já marcados `slow` |
| `test_golden_benchmark.py` (90) | nenhum entre os mais lentos — **fast gate** |
| `tests/scale_bench.py` | **não é importado por nenhum teste** — ferramenta órfã (320 linhas) |
| `tests/solver_bench.py` | não é teste, mas é o *loader do motor* de 10 arquivos de teste — não remover |

### 11.6 Divisão recomendada, com custo medido

| Gate | Conteúdo | Custo medido / estimado |
|---|---|---|
| **FAST** | 1.206 testes (`not slow` + os 6 remarcados) | **≈ 30 s** |
| **MEDIUM** | FAST + `test_benchmark_baselines` de `piloto` e `tp1` + os 6 de corpus | ≈ 5 min (≈ 3,5 min com a fixture de sessão) |
| **FULL** | suíte inteira + `runner.py --all --check` | **39min40s** hoje; ≈ 33 min com a fixture de sessão |

## 12. Corpus permanente do BUTANTÃ — proposta

Hoje o BUTANTÃ entra na suíte por dois caminhos frágeis:

1. três arquivos de teste leem `docs/checkpoints/evidence/` direto
   (`test_reference_layer_filter`, `test_tie_parity_local_search`,
   `test_block_node_fill_revalidation`); os dois primeiros **pulam
   (`pytest.skip`) se o JSON sumir** — "evidencia de BUTANTA ausente" e
   "fixture ausente";
2. tudo o mais é script avulso em `evidence/_scripts/`.

Evidência de checkpoint é registro datado, não corpus mantido. Proposta:

```
nuvem/benchmark/projects/butanta_r08_lt_1pav/     # corpus de verdade, com metadata.json
  input.json  reference.json  metadata.json  baseline.json
  fixtures/
    b34_alignment/          b34_single_wall.json, b34_pair_courses.json
    channel_window/         window_head_sill.json
    channel_door/           door_head_only.json
    t_with_b54/             t_jamb_on_incoming_face.json
    special_clusters/       c09_c09_upright.json, c04_c04_span.json
    under_window/           sill_joint_1_6cm.json
    opening_adjustment/     strip_20_35cm.json
    support/                small_block_over_empty_course.json
```

Cada fixture, **mínima e fisicamente representativa** (1 a 3 paredes, 2 a 4
fiadas, nunca milhares de elementos):

| Fixture | Defeito real que representa | Tamanho alvo |
|---|---|---|
| `b34_alignment/b34_single_wall` | vazado menor desalinhado entre fiadas vizinhas (1.931 ocorrências na BASE) | 1 parede, 3 fiadas |
| `b34_alignment/b34_pair_courses` | par de B34 em fiadas opostas onde giro individual não resolve | 1 parede, 2 fiadas |
| `channel_window/window_head_sill` | canaleta na verga + sob peitoril, offset 0,00 cm | 1 parede, 1 janela |
| `channel_door/door_head_only` | canaleta na verga, nenhuma abaixo (porta sem peitoril) | 1 parede, 1 porta |
| `t_with_b54/t_jamb_on_incoming_face` | canaleta cruzando o nó T como o humano faz; B54 da principal sobre o vão | 2 paredes, 1 T, 1 vão |
| `special_clusters/c09_c09_upright` | `C09+C09` em pé encostados (11 na BASE, humano = 0) | 1 parede, 1 fiada |
| `special_clusters/c04_c04_span` | `C04+C04` que deve virar o compensador do vão total (§54) | 1 parede, 1 fiada |
| `under_window/sill_joint_1_6cm` | junta de 1,6 cm contada como vazio (`MISSING_UNDER_WINDOW` falso) | 1 parede, 1 janela |
| `opening_adjustment/strip_20_35cm` | faixa de 20–35 cm entre peça de nó e jamba (41 casos censados) | 1 parede, 1 nó, 1 vão |
| `support/small_block_over_empty_course` | peça pequena voando sobre fiada vazia (50 na BASE) | 1 parede, 2 fiadas |

**Métricas permanentes que o corpus precisa publicar** (hoje só existem em
`_scripts/`): vazado menor, especiais por fiada, especiais encostados por par
de códigos, buracos (quantidade e cm), peças sem apoio, `NON_MODULAR`,
`MISSING_REQUIRED_CHANNEL`, `MISSING_UNDER_WINDOW`.

**Pré-condição registrada pela §59 do PR #42:** ligar código novo ao benchmark
faz `new_codes` contar como regressão crítica em BUTANTÃ, TGD e TP1. Portanto
a fiação só pode acontecer **junto** com um `--save-baseline` autorizado, num
commit que declare o que mudou. Não é trabalho de "ligar o validador": é um
CR com autorização de baseline.

## 13. Não-overfit — por que cada fixture é geral

| Princípio | Como está garantido |
|---|---|
| **Nenhum `ElementId`** | O CHANNEL já provou que dá: `test_channel_reinforcement` declara no cabeçalho "fixtures SINTÉTICAS derivadas da física medida no BUTANTÃ (nenhum ElementId, W0xx ou coordenada do corpus)". As fixtures propostas seguem o mesmo padrão: geometria em cm, no referencial local da parede. |
| **Representa um princípio, não um caso** | `strip_20_35cm` não é "a parede 8284543": é *a faixa entre peça de nó e jamba em que um B34 + junta (35 cm) não cabe*. Vale em qualquer projeto com o mesmo catálogo. |
| **Reutilizável** | Cada fixture é `(comprimento de parede, posição dos nós, vão, peitoril, altura)` — o mesmo formato de `input.json`. Trocar as medidas gera o caso equivalente de outro projeto. |
| **Controle vermelho obrigatório** | Cada fixture precisa vir em par: o caso com o defeito (tem que acusar) e o mesmo caso sem ele (não pode acusar) — a regra que `tests/regression/test_validators.py` já aplica e sem a qual "um validador que devolvesse FAIL sempre passaria em todos os testes". |
| **Número medido, não número decorado** | Onde a fixture fixar um contador, ele precisa vir com a medição do humano ao lado (como a §59 fez), para que ninguém transforme preferência em erro. |

## 14. Buracos críticos (ordenados por risco)

| # | Buraco | Por que é crítico |
|---|---|---|
| **B1** | **Nenhum CI executa `pytest`.** 1.243 testes dependem de execução manual. | Toda a §5 desta matriz vale zero enquanto ninguém rodar a suíte. É o buraco que anula todos os outros. |
| **B2** | **O gate de corpus está vermelho na main.** Suíte completa medida em `55e990d`: **2 falharam, 1.241 passaram em 39min40s** — as duas falhas são `test_benchmark_baselines[torre_easy_lo_r00_tp1]` e `[torre_easy_lo_r00_tgd-v2]`. | Um teste que já falha não distingue regressão nova de regressão velha. O único gate de corpus do repositório está, na prática, desligado para dois dos três projetos. |
| **B3** | **O BUTANTÃ não tem corpus.** Todas as métricas das correções físicas em curso vivem em scripts de evidência. | Uma regressão de vazado menor, apoio, especiais ou microajuste **não seria detectada por nenhum teste**. |
| **B4** | **`delta_metrics.py` e `physmetrics.py` não existem no repositório.** A §59 do PR #42 os nomeia como "onde a matriz de não-regressão desta missão foi produzida". | A bancada que produziu os números de aceitação do PR não é versionada. Os números não são reprodutíveis por outra sessão. |
| **B5** | **`OPENING_BLOCK_INSIDE_WINDOW` (NÍVEL 1, crítico) sem nenhum teste.** | Mesma classe de "bloco dentro de porta", que tem 4 arquivos. Bloco dentro de janela é erro físico grave e silencioso. |
| **B6** | **Determinismo de planta inteira sem teste.** Três sensibilidades medidas e classificadas como pré-existentes (§9.2). | "Pré-existente" sem teste vira "permanente sem ninguém saber". |
| **B7** | **§66 (microajuste) sem chamador de produção.** `plan_opening_micro_adjustments` não é chamada por nenhum código do botão; os 5 vãos foram movidos por script. | A regra existe, foi medida no Revit, e não está no fluxo. Nenhum teste de integração pode existir ainda. |
| **B8** | **Duas réguas para o vazado menor** (336 externa × 264 motor no mesmo lote), sem teste que as concilie. | O número que decide a aceitação do PR depende de qual régua se usa. |
| **B9** | **Testes permanentes dependem de `docs/checkpoints/evidence/*.json`** e pulam em silêncio se o arquivo sumir. | `skip` silencioso é pior que falha: a suíte fica verde sem testar. |
| **B11** | **O marcador `slow` está incompleto.** Seis testes de corpus (255 s + 5×~81 s = 741 s) não o têm, então `-m "not slow"` custa 12,8 min em vez de 30 s. | Torna o FAST GATE inviável na prática — e como ninguém roda a suíte, o defeito nunca apareceu. |
| **B10** | **`ERROR_HISTORY.md` desatualizado**: lista `MirrorElement` deixa órfãs como "NÃO corrigido", mas `test_mirror_in_place.py` prova que `MirrorElements(..., mirrorCopies=False)` já corrigiu. | Documento de memória que mente em uma linha perde autoridade nas outras. |

## 15. Testes que hoje dão FALSA CONFIANÇA

| Teste / artefato | Por que a confiança é falsa |
|---|---|
| **"regressão consolidada: 1.296 passaram, 3 falharam = main"** | As 3 falhas incluem **os dois gates de corpus humano** — confirmado aqui: em Linux a main dá exatamente essas 2 (a terceira é a do `perf_trace` em Windows). Dizer "igual à main" é verdade e, ao mesmo tempo, esconde que o gate de não-regressão de TP1 e TGD V2 está inoperante desde antes deste PR. |
| **`test_golden_benchmark.py` (90 testes)** | O maior arquivo depois de `test_script.py`, e o cabeçalho é explícito: *"NÃO importa nada de `core/engine/*` — este benchmark é sobre o formato de SAÍDA, nunca sobre o motor que a produz"*. 90 testes verdes não dizem nada sobre modulação. |
| **`piloto_sintetico_2x2`** | Entra nas 11 parametrizações do gate de corpus e tem `reference_type: SOLVER_GENERATED_ONLY`, `confidence: NONE`. O baseline dele é a saída do próprio solver: prova reprodutibilidade, **nunca correção**. Um terço das linhas do gate de corpus é auto-referente. |
| **Baselines V1 (`LEGACY_BASELINE`)** | O manifesto avisa: *"Snapshot congelado de uma execução ANTERIOR DO PRÓPRIO SOLVER. Prova reprodutibilidade/determinismo, NUNCA correção."* Passar contra baseline não é estar certo. |
| **"Corpora legados TGD V2 e TP1 V1 idênticos, achado por achado"** (PR #42) | Verdadeiro e irrelevante como prova de segurança: as §§60–65 são **só CHANNEL**, e os corpora legados rodam `strategy=None`. O corpus não pode regredir porque **não executa o código novo**. |
| **`test_reference_layer_filter` / `test_tie_parity_local_search`** | `pytest.skip` se a evidência sumir. Verde por ausência. |
| **Métricas do `metrics_summary.json`** | Produzidas por scripts não versionados (`delta_metrics.py`, `physmetrics.py`) ou por scripts de evidência sem teste próprio (`b34rule.py`, `channel_strict_compare.py`). Nenhuma delas é recalculável por `pytest`. |
| **Comparador humano × solver (38/13/3/34)** | Vive em `docs/checkpoints/evidence/_scripts/channel_strict_compare.py`. É a régua que diz "nenhum lado piora de classe" — e nenhum teste a exercita. |
| **Workflow verde no GitHub** | Só valida documentação. Um check verde ao lado de um PR de solver sugere aprovação que o próprio workflow nega no summary. |

## 16. Prioridades para depois do PR #42

| Ordem | Ação | Por quê |
|---|---|---|
| **P0** | Consertar ou classificar formalmente as 2 falhas de baseline (TP1 V1, TGD V2) e criar uma lista versionada de *known failures* conferida por script | Sem isso, nenhum gate de corpus tem significado — e todo checkpoint futuro repete "3 = main" sem conferir |
| **P0** | Acrescentar `@pytest.mark.slow` aos 6 testes de corpus não marcados (§11.2) e ligar o FAST GATE no CI | **Medido: 1.206 testes em ≈ 30 s.** Sem a remarcação o mesmo gate custa 12,8 min |
| **P1** | Fixture de sessão em `test_benchmark_baselines.py` | **Medido: 692,5 s no arquivo, com 3 solves idênticos por projeto (82,95 / 82,46 / 82,45 s em TP1). Economia ≈ 390 s** |
| **P1** | Versionar a bancada de medição (`delta_metrics.py`, `physmetrics.py`, `b34rule.py`, `channel_strict_compare.py`) como pacote em `nuvem/benchmark/` com testes próprios | Sem isso os números de aceitação do PR #42 não são reprodutíveis |
| **P1** | Red/green para `OPENING_BLOCK_INSIDE_WINDOW`, `JUNCTION_HALF_BLOCK_ADJACENT`, `POSITION_OFF_AXIS`, `POSITION_BAD_ORIENTATION`, `PRISM_JOINT_STACK` | Cinco códigos NÍVEL 1 sem teste; o padrão red/green já existe no arquivo |
| **P2** | Criar o corpus BUTANTÃ (§12), começando por `b34_alignment`, `opening_adjustment` e `support` | São as três áreas em desenvolvimento ativo e as três sem nenhuma proteção |
| **P2** | CR de autorização de baseline para ligar os validadores novos (vazado menor, apoio) — `new_codes` conta como regressão crítica | A §59 identificou corretamente o bloqueio; ele exige decisão do usuário, não código |
| **P2** | Teste de determinismo de planta inteira, congelando as três sensibilidades conhecidas como limites superiores | Impede que o pré-existente piore em silêncio |
| **P3** | Substituir as dependências de `docs/checkpoints/evidence/*.json` por fixtures do corpus; eliminar `pytest.skip` silencioso | Verde por ausência é o pior estado possível |
| **P3** | Reconciliar `ERROR_HISTORY.md` (§17.2 já corrigido) e `PROJECT_STATUS.md` (`main` defasado) | Higiene documental que o próprio CI documental já cobra |
| **P3** | Decidir o conflito §10.7 (canaleta na última fiada) ou registrar explicitamente que continua aberto com 3 medições divergentes | Único `NÃO RESOLVIDO` formal do `ERROR_HISTORY` |

## 17. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Regressão física do B34/apoio/microajuste entrar despercebida | **alta** | **alto** | corpus BUTANTÃ (P2) — hoje não há nada |
| As correções §60–65 quebrarem quando forem estendidas do CHANNEL para o legado | **alta** | **alto** | os corpora legados hoje **não** exercitam esse código; exigir baseline novo antes da extensão |
| Métricas de aceitação não reprodutíveis por outra sessão | **certa** hoje | médio | versionar a bancada (P1) |
| Validador novo reprovar o projeto humano de referência | média | **alto** | a régua da §59 (medir o humano antes de definir o nível) precisa virar regra de processo, não achado de uma missão |
| Suíte ser abandonada por custo | **já aconteceu** — 39min40s medidos hoje | médio | FAST/MEDIUM/FULL (P0/P1) + remarcar os 6 + fixture de sessão |
| Baseline ser regravado para "fazer o teste passar" | baixa | **crítico** | já proibido no `DEVELOPMENT_PROCESS.md`; o CI precisa conferir que `baseline.json` só muda em commit que declare o quê |
| Confiança no check verde do GitHub | **alta** | médio | renomear o workflow para deixar claro que é documental, e adicionar o FAST GATE ao lado |
| Duas réguas de vazado menor divergirem | média | médio | teste que concilie `b34rule` externa × contador do motor |

---

## Veredito

**BENCHMARK PARTIAL — GAPS IDENTIFIED**

O que existe é bom e honesto: 1.243 testes, taxonomia de erro com fonte única
e separação nível 1/nível 2 correta, padrão red/green nos validadores,
cobertura de determinismo por invariante ampla, e um corpus CHANNEL
(84 testes) que é o modelo a copiar — fixtures sintéticas derivadas de física
medida, sem `ElementId`, com controle vermelho em cada regra.

O que falta é estrutural, não cosmético:

1. **nenhum CI executa a suíte** — a régua existe e não é usada;
2. **o único gate de corpus está vermelho** para dois dos três projetos, e a
   prática de reportar "3 falhas = main" normalizou isso;
3. **a área em desenvolvimento ativo (B34, apoio, especiais, microajuste) é
   exatamente a que não tem corpus permanente** — as métricas que decidem a
   aceitação do PR #42 vivem em scripts de evidência, e dois dos módulos que
   as produziram não estão no repositório;
4. **o marcador `slow` está incompleto**, o que faz o gate rápido custar
   12,8 min em vez de 30 s — defeito que só não incomoda porque ninguém roda
   a suíte.

A boa notícia da medição: **1.206 dos 1.243 testes rodam em ≈ 28 s.** A
proteção mais valiosa que falta não é cara nem demorada de ligar — é uma
linha de workflow e seis linhas de marcador.

A régua não está errada. Ela está **desligada nos pontos que mais importam
agora**.

---

## Medição

Comando, ambiente e resultado integral da execução que sustenta os números
das seções 1, 11, 14, 16 e 17.

```
$ python3 -m pytest -q --durations=60 -p no:cacheprovider
```

Ambiente: container Linux (`Linux 6.18.44-fc-v33`), CPython 3.11, pytest 9.1.1,
sem paralelismo, `origin/main` = `55e990d962ed22ae1021f0d335db197607bddda1`,
árvore limpa.

Resultado:

```
2 failed, 1241 passed in 2380.72s (0:39:40)

FAILED tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]
FAILED tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]
```

Contagem de seleção:

```
$ python3 -m pytest --collect-only -q                  ->  1243 tests
$ python3 -m pytest --collect-only -q -m "not slow"    ->  1212/1243 (31 deselected)
$ python3 -m pytest --collect-only -q -m "slow"        ->  31/1243
```

### 30 durações mais altas (de `--durations=60`)

```
255.49s call     tests/test_block_node_fill_revalidation.py::test_t18_candidato_aceito_permanece_seguro_no_corpus
221.56s call     tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]
163.90s call     tests/test_block_b19_residual_fill_implementation.py::test_t52_determinismo_duas_execucoes_separadas
162.26s call     tests/test_block_arm_role_prism_stagger.py::test_determinismo_w076_w041_duas_rodadas_identicas
93.18s call     tests/test_cross_band_joint_propagation_cr_g12.py::test_determinismo_da_correcao
93.14s call     tests/test_block_arm_role_candidate_safety_contract.py::test_t16_execucao_repetida_e_deterministica
89.20s call     tests/test_block_b19_residual_fill_implementation.py::test_t49_tp1_fingerprint_identico_com_e_sem_b19
85.92s call     tests/test_cross_band_joint_propagation_cr_g12.py::test_fronteira_de_banda_deixa_de_criar_junta_continua[torre_easy_lo_r00_tp1]
82.95s call     tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]
82.47s call     tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tp1-v2]
82.46s call     tests/regression/test_benchmark_baselines.py::test_o_solver_produz_alguma_coisa[torre_easy_lo_r00_tp1]
82.45s call     tests/regression/test_benchmark_baselines.py::test_nenhum_validador_quebra_no_projeto[torre_easy_lo_r00_tp1]
81.55s call     tests/test_block_arm_role_prism_stagger.py::test_w010_tp1_com_abertura_nenhum_bloco_invade_o_vao
81.53s call     tests/test_block_b19_residual_fill_implementation.py::test_t48_tp1_zero_candidatos_aceitos_apos_gate_de_integridade
80.77s call     tests/test_block_arm_role_prism_stagger.py::test_w041_tp1_prisma_resolvido_de_verdade_nao_so_reportado
80.62s call     tests/test_block_arm_role_prism_stagger.py::test_w022_w093_tp1_cobertura_do_arm_role_consistency_preservada
80.49s call     tests/test_block_arm_role_prism_stagger.py::test_w076_tp1_coincidencia_de_contorno_foi_resolvida_pelo_arm_safe_repair
47.71s call     tests/test_cross_band_joint_propagation_cr_g12.py::test_fronteira_de_banda_deixa_de_criar_junta_continua[torre_easy_lo_r00_tgd]
46.97s call     tests/regression/test_benchmark_baselines.py::test_nenhum_validador_quebra_no_projeto[torre_easy_lo_r00_tgd]
46.91s call     tests/regression/test_benchmark_baselines.py::test_o_solver_produz_alguma_coisa[torre_easy_lo_r00_tgd]
46.74s call     tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]
45.35s call     tests/test_block_arm_role_candidate_safety_contract.py::test_t1_t9_candidato_seguro_e_aceito_no_tgd_real
45.27s call     tests/test_block_arm_role_candidate_safety_contract.py::test_t10_fallback_original_para_candidatos_inseguros_no_tgd_real
45.23s call     tests/test_block_b19_residual_fill_implementation.py::test_t50_tgd_zero_candidatos_elegiveis_limite_de_escopo_conhecido
42.14s call     tests/test_cross_band_joint_propagation_cr_g12.py::test_reproducer_pre_fix_tem_junta_continua_na_fronteira_de_banda[torre_easy_lo_r00_tp1]
27.75s call     tests/test_script.py::test_INV_PAIR_003_desempate_final_invariante_a_renumeracao
27.73s call     tests/test_script.py::test_INV_PAIR_002_2868_linhas_mescladas_invariante_a_permutacao
24.75s call     tests/test_cross_band_joint_propagation_cr_g12.py::test_reproducer_pre_fix_tem_junta_continua_na_fronteira_de_banda[torre_easy_lo_r00_tgd]
6.31s call     tests/test_block_b19_residual_fill_implementation.py::test_t53_arm_role_safe_repair_false_desliga_tudo_contrato_preservado
5.15s call     tools/documentation/test_capture_validation.py::CaptureTests::test_timeout_stops_child_as_well_as_parent
```

O corte da lista de 60 ficou em 0,14 s: **tudo que não aparece nela custa
menos que isso**. Daí a conta da §11.1 — 1.206 testes somam ≈ 28 s.

### Observação sobre a diferença para o número do PR #42

O PR #42 relata `1.296 passaram, 3 falharam em 38 min` (Windows, CPython
3.14.7, sobre o head do PR). Esta medição dá `1.241 passaram, 2 falharam em
39min40s` (Linux, CPython 3.11, sobre a main). As diferenças são explicáveis e
**não indicam divergência**: o head do PR tem ~90 testes a mais, e a terceira
falha de lá (`test_perf_trace_stall_sampler`) é condicionada a
`sys.platform == "win32"` e portanto não ocorre aqui. As **duas** falhas de
baseline são idênticas nos dois relatos.
