# RELATÓRIO FINAL — ARM SAFE REPAIR GATE FIDELITY

`CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY` (2026-09-04). Implementação dos
dois gates especificados em `docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_
SPEC.md` sobre a main pós-NODE-FILL. Continuação direta de
`CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT` (seção 32 de
`nuvem/REGRAS_MODULACAO_BLOCOS.md`) e `CR-BLOCK-NODE-FILL-REVALIDATION`
(seção 33).

## Base

```
origin/main = 4344c76225f12569b3776b0121bbfc1b49f7256a  (confirmado)
```

Contém: ARM Candidate Safety Contract (`PR #12`), diagnóstico das
rejected edges, Gate Fidelity PREIMPLEMENTATION spec (`PR #15`), evidência
B19 (`PR #16`), NODE-FILL integrado (`PR #17`).

## Branch / HEAD

```
branch: claude/cr-block-arm-safe-repair-gate-fidelity-ne5cdz
base:   origin/main @ 4344c76 (branch NOVA, sem cherry-pick)
```

## STATE_A pós-NODE-FILL

Medido nesta sessão com `nuvem/benchmark/solver_bridge.run_solver` +
`from_solver.project_from_solver` + `validators.run_all` (mesmo caminho
real do benchmark, `write_files=False`), sobre a `main` pura (mudanças
desta CR retiradas via `git stash` durante a medição, restauradas depois).

| | TGD | TP1 | Piloto |
|---|---|---|---|
| ARM accepted | 1 (`23\|SAME_A`) | 0 | 0 |
| ARM rejected | 21 (7 arestas) | 9 (3 arestas) | 0 |
| findings_total | 4968 | 5093 | 124 |
| runtime solver | 39.5–40.5 s | 20.9–24.2 s | 0.04–0.05 s |
| `_arm_role_pinned` nós | 2 | 0 | 0 |

Razões medidas nesta sessão para as 10 arestas conhecidas (TGD 4, 54, 89,
90, 91, 92, 120; TP1 20, 75, 91) — confirmando que NODE-FILL já havia
mudado uma razão (TGD 91) sem mudar aceitação, exatamente como
`docs/BLOCK_NODE_FILL_REVALIDATION.md` já registrava:

- TGD 89/90 `SAME_B`: `row_coverage_regression:<89|90>` (proxy LOCAL da
  própria parede, cego à peça de canto emprestada pela vizinha).
- TGD 91 `SAME_B`: `new_consecutive_compensators:128` — o mesmo bug do
  agregado cross-banda (fantasma), reportado sobre a parede vizinha 128.
- TGD 92 `SAME_B`: `new_forced_prism_in_neighbor` (gate 3, não tocado por
  esta CR).
- TGD 120 `SAME_A`: `new_consecutive_compensators:88` (REAL); `SAME_B`:
  `row_coverage_regression:37`.
- TGD 4/54: `does_not_resolve_target` em todos os candidatos (canto
  girado, `_corner_bond_blocked_by_other_node` — bit de papel sem
  alavanca).
- TP1 20 `SAME_B`: `new_consecutive_compensators:13` (REAL).
- TP1 75 `SAME_A`: `new_consecutive_compensators:81` — **fantasma
  confirmado** (7 bandas, mesmo `C04` solitário, `course` letra agrupando
  cross-banda).
- TP1 91 `SAME_B`: `new_consecutive_compensators:88` (REAL).

## Compensator gate

### causa

`_no_new_consecutive_compensators`/`_wall_compensator_run_signatures`
(`wall_stepper.py`) recebiam `result["candidates"]` — a concatenação de
TODAS as bandas de abertura (`_solve_building_blocks_all_courses_core`,
`wall_modeling.py`). Cada candidato carrega `c["course"]` como a LETRA de
família ("A"/"B"), que se repete em toda banda — nunca o `course_index`
físico. `_find_consecutive_compensators` agrupava por essa letra: o MESMO
compensador solitário, repetido em N bandas na mesma posição X, virava
uma cadeia fantasma de N "consecutivos".

### implementação

Novo helper `_find_consecutive_compensators_in_course` (variante pura de
`_find_consecutive_compensators` sem agrupamento por letra — a lista de
entrada já é UMA fiada física isolada). `_wall_compensator_run_signatures`
passou a receber `course_candidates` + `num_courses` e iterar
`range(num_courses)`, chamando o helper novo por `course_index`
explícito, com a assinatura `(course_index, codes, start_cm)` em vez de
`(letra, codes, start_cm)`. `_no_new_consecutive_compensators` ganhou
`num_courses` no lugar de operar sobre `candidates` agregado. Nenhuma
mudança na definição de compensador (`entry["is_compensator"]`) nem na
tolerância (`BLOCK_JOINT_CM + PIER_LAYOUT_TOLERANCE_CM`).

`validate_wall_modulation`/`_find_consecutive_compensators` (usados fora
do SAFE REPAIR) **não foram tocados** — fora do escopo desta CR.

### prova física

- **T1** (sintético): mesmo `C09` isolado repetido em 7 `course_index`
  diferentes, mesma posição X → 0 sequências (antes seria 1 sequência
  fantasma de 7).
- **T2/T3**: compensadores REALMENTE consecutivos na mesma fiada física
  continuam detectados (1 e 3 elementos).
- **T4**: permutar a ordem dos itens dentro de uma fiada não muda o
  resultado.
- **Corpus real**: `TP1 wall_idx=75/SAME_A`, antes rejeitado por
  `new_consecutive_compensators:81`; com o fix, o candidato passa deste
  gate e é avaliado pelos seguintes → **ACEITO** (ver STATE_B). Delta de
  achados do projeto TP1 inteiro: **exatamente −102** (bate com o número
  medido no diagnóstico original `docs/BLOCK_ARM_REJECTED_EDGES_
  DIAGNOSIS.md`, sem nenhum outro candidato ARM ter mudado nesta rodada).
- `TGD wall_idx=91/SAME_B`: razão muda de `new_consecutive_compensators:
  128` (fantasma) para... **ACEITO** (o candidato passa o gate 4 e o gate
  5 credita corretamente a vizinha — ver seção seguinte).

## Coverage gate

### causa

`_wall_row_covered_length_cm` filtrava só `c.get("wall_idx") == wall_idx`.
Numa troca de papel ARM, a peça de canto de um nó L/T/X muda de `wall_idx`
dono nos dados sem sair fisicamente do nó — a parede que "perde" a posse
via proxy local cai de perto de 100% para perto de 0%, mesmo a região
física continuando coberta.

### implementação

Contrato de crédito de nó com 5 condições (nenhuma heurística de
proximidade/`wall_idx` vizinho/distância arbitrária):

1. **mesmo nó** — `wall_credit_node_indices` é construído pelo chamador
   (`repair_arm_role_isolated_edges`, que conhece `node_p`/`node_q` da
   aresta isolada), nunca deduzido por distância. O crédito flui nos DOIS
   SENTIDOS: o ALVO (`wall_idx` da aresta) recebe os DOIS nós isolados do
   candidato (`[node_p, node_q]`); cada VIZINHA recebe só o nó que a liga
   ao alvo. **Achado desta sessão** (não estava na spec original, que só
   previa o sentido vizinha→alvo): o mecanismo real precisa dos DOIS
   sentidos — em TGD 89/90/91/92 é o próprio ALVO que perde a peça de
   canto para a vizinha, não o contrário.
2. **mesma região geométrica** — `_wall_row_node_credit_cm` recorta
   (`max`/`min`) o crédito contra `missing_intervals` (o trecho que
   REALMENTE deixou de ser coberto — `_subtract_intervals_cm(before_own,
   after_own)`), nunca "a peça existe em algum lugar da parede". A
   projeção usa `_candidate_extent_on_wall_axis` (a mesma função que
   `_index_node_candidates_by_wall_end` já usa para o corpo de uma peça
   de canto invadir a parede vizinha pela LARGURA).
3. **mesma fiada física** — `course_index` explícito, nunca letra.
4. **peça realmente presente** — sempre lida de `trial_course_candidates`
   (resultado REAL do rebuild), nunca hipótese.
5. **ausência de gap físico** — não verificado à parte: o crédito nunca
   excede `missing_intervals` por construção; se ainda sobrar gap real
   depois do crédito, `_no_new_row_coverage_regression` continua
   rejeitando.

`_wall_row_covered_length_cm_with_node_credit` substitui a chamada
`after = _wall_row_covered_length_cm(...)` do lado DEPOIS; o lado ANTES
continua a medida simples (é a base contra a qual o gap é calculado,
nunca precisa de crédito). `_evaluate_corner_role_candidate` ganhou o
parâmetro `wall_credit_node_indices` (dict `{wall_idx: [node_index,...]}`).

### prova física

- **T5/T6** (sintético, dois conjuntos de medidas): proxy LOCAL cairia a
  zero (falso positivo de regressão); com o crédito, a fiada recupera o
  suficiente para passar a tolerância — contraste explícito
  `node_indices=None` (rejeita, comportamento antigo) ×
  `node_indices=[...]` (aceita).
- **T7**: peça REALMENTE ausente (nenhum candidato cobre a região, nem no
  mesmo nó) continua bloqueado — o crédito nunca inventa geometria.
- **T8**: peça presente mas em outra fiada física (`course_index`
  diferente) não recebe crédito.
- **T9**: peça presente mas em outro nó (`node_index` diferente) não
  recebe crédito.
- **T10**: peça credora pequena demais (geometria insuficiente) não fecha
  o gap — perda física real continua bloqueada mesmo com o crédito
  habilitado.
- **T_WIRING** (dois testes): `_evaluate_corner_role_candidate` só credita
  quando `wall_credit_node_indices` liga a parede ao nó certo — sem o
  mapeamento, mesmo bug antigo (rejeita); com o mapeamento, aceita — nos
  DOIS sentidos (vizinha credita do alvo E alvo credita da vizinha).
- **Corpus real**: `TGD wall_idx=91/SAME_B` — o gate 4 (compensador) já
  deixa de rejeitar (fix acima); o gate 5 (cobertura), com o crédito nos
  dois sentidos, também aprova → candidato **ACEITO**, composição final
  idêntica ao gabarito humano (ver "Reference Corpus" abaixo). `TGD
  wall_idx=89/90`: a razão do gate MUDA (de `row_coverage_regression:
  <89|90>`, medindo o próprio alvo, para `row_coverage_regression:<132|
  133>`, medindo a vizinha que efetivamente não fecha) — o gate agora
  mede o mecanismo real do defeito (Grupo B: reserva pior-caso degrada a
  vizinha curta, um problema PRÉ-EXISTENTE fora do escopo desta CR), mas
  o crédito não é suficiente para fechar o gap físico real — **candidato
  continua corretamente rejeitado**, sem forçar aceitação.

## 10 rejected edges

| caso | before gate | after gate | resultado | motivo final | relação com humano | classificação |
|---|---|---|---|---|---|---|
| TGD 4 | `does_not_resolve_target` (3/3) | igual | rejeitado | `does_not_resolve_target` | sem gabarito (par humano ausente) | `OUT_OF_SCOPE_ROTATED_CORNER` |
| TGD 54 | `does_not_resolve_target` (3/3) | igual | rejeitado | `does_not_resolve_target` | sem gabarito | `OUT_OF_SCOPE_ROTATED_CORNER` |
| TGD 89 | `row_coverage_regression:89` | `row_coverage_regression:132` | rejeitado | proxy corrigido, gap físico real | vizinha curta — Grupo B (fora de escopo) | `CORRECTLY_REJECTED_OTHER_GATE` |
| TGD 90 | `row_coverage_regression:90` | `row_coverage_regression:133` | rejeitado | idem | idem | `CORRECTLY_REJECTED_OTHER_GATE` |
| **TGD 91** | `new_consecutive_compensators:128` (fantasma) | — | **ACEITO** (`SAME_B`) | — | `CONFIRMED_BY_HUMAN` (composição idêntica ao gabarito, seção 30.7) | `FIXED_BY_COMPENSATOR_GATE` |
| TGD 92 | `new_forced_prism_in_neighbor` | igual | rejeitado | gate 3 (não tocado) | vizinha 129 — Grupo B | `CORRECTLY_REJECTED_OTHER_GATE` |
| TGD 120 | `SAME_A`: comp. REAL; `SAME_B`: coverage (espelho paridade) | igual | rejeitado | idem | espelho de paridade — Option A mantida (fora de escopo) | `CORRECTLY_REJECTED_OTHER_GATE` |
| TP1 20 | `new_consecutive_compensators:13` (REAL) | igual | rejeitado | idem | espelho de paridade | `CORRECTLY_REJECTED_OTHER_GATE` |
| **TP1 75** | `new_consecutive_compensators:81` (fantasma) | — | **ACEITO** (`SAME_A`) | — | `CONFIRMED_BY_HUMAN` (composição idêntica; ver "Solver × Humano" no diagnóstico) | `FIXED_BY_COMPENSATOR_GATE` |
| TP1 91 | `new_consecutive_compensators:88` (REAL) | igual | rejeitado | idem | espelho de paridade | `CORRECTLY_REJECTED_OTHER_GATE` |

Nenhum caso `DEFERRED_B19_DOMAIN_IMPLEMENTATION` ou `INCONCLUSIVE` — B19
não participa de nenhuma das 10 arestas nesta rodada (consistente com a
seção 8, fora de escopo).

## ARM accepted / rejected

| | STATE_A (antes) | STATE_B (depois) |
|---|---|---|
| TGD accepted | `23\|SAME_A` (1) | `23\|SAME_A`, `91\|SAME_B` (2) |
| TGD rejected | 21 (7 arestas) | 19 (6 arestas) |
| TP1 accepted | — (0) | `75\|SAME_A` (1) |
| TP1 rejected | 9 (3 arestas) | 6 (2 arestas) |
| Piloto | 0/0 | 0/0 |
| `_arm_role_pinned` TGD | 2 | 4 |
| `_arm_role_pinned` TP1 | 0 | 2 |

Todos os motivos de rejeição continuam reportados (auditoria — nenhum
`None`/silencioso).

## NODE-FILL preservation

`NODE_FILL_OPPOSITE_COURSE_ENABLED = True` inalterado. `docs/BLOCK_NODE_
FILL_REVALIDATION.md`/`tests/test_block_node_fill_revalidation.py`
continuam passando integralmente (33 passed, junto com `test_block_arm_
role_prism_stagger.py`). Um teste daquela suíte (`test_t19_candidato_
rejeitado_nao_e_liberado_indevidamente`) precisou de atualização — ver
"Production diff" e "Tests NODE-FILL" abaixo; o mecanismo em si (metade
simétrica da junta NÓ|FILL) não foi tocado.

## Reference Corpus

- `TGD wall_idx=91/SAME_B` — `docs/BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md`,
  seção "Solver × Humano": para as 6 paredes de 124cm L–X–L do TGD/TP1
  (entre elas a equivalente a esta aresta), "o humano usa, nas 6, a MESMA
  composição... os dois B34 de canto na MESMA família" — exatamente
  `SAME_B`. → **CONFIRMED_BY_HUMAN**.
- `TP1 wall_idx=75/SAME_A` — mesma seção, paredes de 69cm: "= `SAME_A`,
  exatamente. Humano: `PRISM_CONTINUOUS_JOINT ×1` (borda de altura) +
  `JUNCTION_MISSING_BINDING ×5`" (residual pré-existente do humano, não
  causado pelo solver). → **CONFIRMED_BY_HUMAN**.
- Nenhum `CONFLICTS_WITH_HUMAN` identificado nos dois candidatos
  recém-aceitos.

## Coverage

`COVERAGE_MISSING_ROW`/`COVERAGE_ROW_MOSTLY_EMPTY`/`COVERAGE_GAP_IN_ROW`/
`COVERAGE_PARTIAL_WALL`: delta **zero** nos três projetos (TGD
258/112/1959/61, TP1 0/18/327/6, piloto 0/8/16/0 — idênticos antes/
depois). A troca de posse local nas paredes 89/90/92/120 não altera
contagem global de cobertura (o candidato continua rejeitado nesses
casos — nenhum efeito no resultado final).

## Prism

| | TGD antes→depois | TP1 antes→depois | Piloto |
|---|---|---|---|
| `PRISM_CONTINUOUS_JOINT` | 336 → **320** (−16) | 272 → **256** (−16) | 0 → 0 |
| `PRISM_JOINT_STACK` | 20 → 19 (−1) | 17 → 16 (−1) | 0 → 0 |
| `PRISM_STAGGER_BELOW_TARGET` (nível 2) | — | 1418 → 1370 (−48) | — |
| `alignment_conflicts` (motor) | 331 → 323 | 449 → 442 | 8 → 8 |

Cada aresta recém-aceita resolve exatamente o prisma forçado da própria
parede (16 fiadas + 1 = −16/−17 findings) — o mesmo padrão já medido para
`wall_idx=23` no PR #12.

## Compensators

| | TGD antes→depois | TP1 antes→depois |
|---|---|---|
| `COMPENSATOR_CONSECUTIVE` | 379 → 379 (+0) | 1461 → **1443** (−18) |
| `COMPENSATOR_EXCESS_IN_RUN` | 340 → 341 (+1) | 1084 → **1067** (−17) |
| `COMPENSATOR_VERTICAL_STRIP` | 56 → 58 (+2) | 188 → 186 (−2) |
| `COMPENSATOR_AVOIDABLE` | 37 → 37 (+0) | 86 → 86 (+0) |

TP1 (`wall_idx=75`, o caso `SAME_A`/fantasma) melhora diretamente
(−18/−17/−2 — bate com a ordem de grandeza "0 novos/102 resolvidos" do
diagnóstico original, incluindo os achados de compensador). TGD
(`wall_idx=91`) tem efeito colateral pequeno (+1/+2) na composição da
vizinha 128 (nova composição de fill sem coincidência de junta, trade-off
esperado e já documentado como "custa liberdade de busca, nunca inventa
geometria" — mesmo padrão do NODE-FILL).

## Junctions

`JUNCTION_NOT_ALTERNATING`/`JUNCTION_MISSING_BINDING`: delta zero nos
projetos onde nenhum candidato mudou de aceito (TGD 303/23 idênticos; TP1
`JUNCTION_MISSING_BINDING` já tinha a falha histórica conhecida contra o
baseline — ver "Full suite").

## Openings

`OPENING_BLOCK_INSIDE_DOOR`/`OPENING_BLOCK_CROSSES_JAMB`: delta zero (TGD
5/108, TP1 0/168, piloto 0/0 — idênticos).

## Collisions

`POSITION_OVERLAP`/`collisions` (solver): delta zero nos três projetos
(TGD 29/1043, TP1 18/14, piloto 0/0).

## Determinism

- Repetição em processos NOVOS separados (STATE_B medido duas vezes, TGD
  e TP1): fingerprint `walls_blocks` idêntico
  (`c66b14a534f29022`/`2d107366ad6b81a2`), mesma contagem de blocos
  (10679/18417), mesmo ARM accepted em ambas as rodadas.
- `T4`/`T_HV` (unitários): permutação da ordem dos itens dentro de uma
  fiada e orientação H/V não mudam o resultado dos dois gates.

## Performance

| projeto | STATE_A (s) | STATE_B (s) | delta |
|---|---|---|---|
| TGD | 39.5–40.5 | 36.3–38.7 | ≈ 0 a −8% (dentro do ruído; menos rebuilds descartados por fantasma) |
| TP1 | 20.9–24.2 | 20.3–21.1 | ≈ 0 a −13% |
| Piloto | 0.04–0.05 | 0.04–0.05 | ≈ 0 |

Nenhum crescimento de rebuilds: o número de candidatos testados por
aresta continua o mesmo (4 bits canônicos, pula o ORIGINAL); os gates
apenas leem `course_candidates` (já calculado) em vez de `candidates`
agregado — mesma ordem de custo.

## Tests Gate Fidelity

`tests/test_block_arm_safe_repair_gate_fidelity.py` — T1-T10 (identidade
de fiada física do compensador; 5 condições de crédito de nó da
cobertura) + 2 testes de wiring (crédito nos dois sentidos) + 1 teste
H/V: **13 passed** (0.14s — só sintético/puro, sem corpus).

## Tests ARM

`tests/test_block_arm_role_candidate_safety_contract.py` (T2 atualizado
para `course_candidates`/`num_courses`, mesmo comportamento coberto):
**18 passed** (161s, inclui corpus real — `wall_idx=23`/W011 continua
aceito, T1).

## Tests NODE-FILL

`tests/test_block_node_fill_revalidation.py` +
`tests/test_block_arm_role_prism_stagger.py`: **33 passed** (252s).
Dois testes precisaram de atualização, ambos por causa de mudanças
FÍSICAS reais e corretas (não regressões — ver "Production diff"):

- `test_w076_tp1_coincidencia_de_contorno_e_geometricamente_forcada_mas_
  agora_visivel` → renomeado `..._foi_resolvida_pelo_arm_safe_repair`:
  W076/TP1 (== `wall_idx=75`) deixa de ter a coincidência de junta de
  contorno porque o ARM SAFE REPAIR agora resolve essa aresta (antes,
  a coincidência era "geometricamente forçada" só porque o papel do nó
  ficava fixo — o próprio comentário original do teste já previa que só
  trocar a peça escolhida resolveria, "fora do escopo daquela CR").
- `test_t19_candidato_rejeitado_nao_e_liberado_indevidamente`: um flip
  genuíno (`TGD wall_idx=91/SAME_B`, rejeitado sem NODE-FILL por
  `closure_regression`, aceito com NODE-FILL) precisou ser documentado
  explicitamente (`KNOWN_INTERACTIONS`) em vez de silenciosamente
  permitido — o teste continua bloqueando qualquer flip NÃO explicado.

## Full suite

`python3 -m pytest tests -q`:

| | ANTES desta CR (main, `docs/BLOCK_NODE_FILL_REVALIDATION.md`) | DEPOIS (medido nesta sessão) |
|---|---|---|
| passed | 593 | **606** (+13 = `test_block_arm_safe_repair_gate_fidelity.py`) |
| failed | 1 | 1 (a mesma) |
| falha conhecida | `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]` — `JUNCTION_MISSING_BINDING` 8→9 (P3 — BENCHMARK_ARTIFACT, seção 32) | idêntica, mesma mensagem |

Rodada completa medida nesta sessão com o fix aplicado (`python3 -m
pytest tests -q`): **606 passed, 1 failed, 641.6s**. Antes de corrigir os
2 testes desatualizados (ver "Tests NODE-FILL"), a mesma rodada dava
**604 passed, 3 failed** — os 2 extras eram consequência FÍSICA correta
do fix (documentados e corrigidos, não escondidos). Nenhum teste foi
desabilitado; nenhuma falha nova além da já conhecida.

## Production diff

Único arquivo de produção tocado: `nuvem/core/engine/wall_stepper.py`
(seção "CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT — SAFE REPAIR"). Sem
mudança em `wall_pairing.py`, `solve_l_corner`/`solve_t_intersection`,
canonical ordering, tolerâncias, ou special-case por `wall_idx`/projeto.

Novos símbolos (todos adicionados a `__all__`):
`_find_consecutive_compensators_in_course`, `_wall_row_own_extents_cm`,
`_subtract_intervals_cm`, `_wall_row_node_credit_cm`, `_wall_row_covered_
length_cm_with_node_credit`. Assinaturas alteradas: `_wall_compensator_
run_signatures`/`_no_new_consecutive_compensators` (ganharam
`num_courses`, trocaram `candidates` por `course_candidates`);
`_no_new_row_coverage_regression` (ganhou `node_indices`);
`_evaluate_corner_role_candidate` (ganhou `wall_credit_node_indices`).

Testes: `tests/test_block_arm_safe_repair_gate_fidelity.py` (novo),
`tests/test_block_arm_role_candidate_safety_contract.py` (T2 adaptado),
`tests/test_block_arm_role_prism_stagger.py` (1 teste atualizado),
`tests/test_block_node_fill_revalidation.py` (T19 atualizado).

## Baseline diff

ZERO — nenhum `baseline.json` regravado (`--save-baseline` não usado).

## Reference diff

ZERO — nenhum `reference.json`/`reference_score.json` tocado.

## Deferred B19

Não implementado (fora de escopo, seção 8 do pedido). Nenhuma das 10
arestas caiu em `DEFERRED_B19_DOMAIN_IMPLEMENTATION` nesta rodada.

## Out-of-scope rotated corners

TGD 4 e 54 permanecem `OUT_OF_SCOPE_ROTATED_CORNER` — `does_not_resolve_
target` em todos os candidatos, `_corner_bond_blocked_by_other_node`
decide a peça antes da coordenação de papel entrar em jogo (não tocado
por esta CR).

## Gates / veredito

| gate | status | evidência |
|---|---|---|
| STATE_A medido | PASS | tabela acima, main pura via `git stash` |
| causa-raiz compensador provada | PASS | leitura de código + T1/T11(TP1 75 real) |
| causa-raiz cobertura provada | PASS | leitura de código + T5-T10 + TGD 91/89/90 real |
| mudança mínima (reúso `course_candidates`) | PASS | nenhuma arquitetura nova |
| crédito de nó só sob as 5 condições | PASS | T7-T10 (ausência/fiada errada/nó errado/geometria insuficiente bloqueiam) |
| B19 fora de escopo | PASS | não tocado, seção 8 |
| rotated corners fora de escopo | PASS | não tocado, seção 9 |
| NODE-FILL preservado | PASS | flag inalterada, suíte 33 passed |
| TP1 75 caso de prova | PASS | 0 novos/−102 no projeto, ACEITO, `CONFIRMED_BY_HUMAN` |
| TGD 89/90 caso de prova | PASS | razão migra para a vizinha real (132/133); crédito tentado e insuficiente — corretamente rejeitado, não forçado |
| candidate safety contract preservado | PASS | 18/18 safety-contract passed, T1 (`wall_idx=23`) intacto |
| testes Gate Fidelity T1-T10 | PASS | 13/13 |
| suíte completa | PASS (1 falha conhecida) | 606 passed / 1 failed (idêntica à main) |
| determinismo | PASS | fingerprint idêntico em processos novos |
| performance | PASS | delta ≤ 0%, sem crescimento de rebuilds |
| diff de produção restrito | PASS | só `wall_stepper.py` |
| sem special-case | PASS | nenhum `if project`/`wall_idx`/coordenada |
| baseline/reference diff zero | PASS | `git status` |

**APROVADO PARA INTEGRAÇÃO**

Os dois gates do SAFE REPAIR (compensador, cobertura) foram corrigidos
para medir fidelidade física em vez de proxy de representação, com causa-
raiz comprovada por leitura de código E por medição ao vivo contra o
corpus real. Resultado: 2 novos candidatos ARM aceitos (`TGD wall_idx=91/
SAME_B`, `TP1 wall_idx=75/SAME_A`), ambos confirmados pelo Reference
Corpus humano, ambos resolvendo prisma forçado sem nenhuma regressão de
cobertura/abertura/colisão/junção. 6 arestas continuam corretamente
rejeitadas (proxy corrigido, mas a causa física real — Grupo B/espelho de
paridade — está fora do escopo desta CR, como esperado). 2 arestas
continuam `OUT_OF_SCOPE_ROTATED_CORNER`. Suíte completa sem regressão
nova (1 falha pré-existente e já conhecida). Determinismo e performance
provados.

**NÃO MESCLADO. Aguarda autorização explícita do usuário para merge.**
