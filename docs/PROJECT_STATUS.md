# PROJECT STATUS

> Estado **operacional atual** do projeto (Modulação Automática pyRevit).
> Só o que está em vigor agora. Histórico completo de CRs, dívidas
> resolvidas e o log cronológico de atualizações ficam em
> `docs/PROJECT_STATUS_LOG.md`.
>
> Novo numa sessão? Comece por `docs/START_HERE.md`.

## Main atual

```
branch: main
SHA:    c88a031404459ee4cee0f7c36904b8e7b971a471
```

`main` real conferida por `git fetch` em 2026-09-08. Último marco:
**INTEGRAÇÃO CONSOLIDADA** dos quatro PRs revisados, autorizada
explicitamente pelo usuário e feita nesta ordem, com `origin/main`
atualizada entre um merge e o seguinte:

| ordem | PR | CR | HEAD aprovado | merge commit |
|---|---|---|---|---|
| 1 | `#27` | CR-D1 (recuperação documental) | `b852695` | `7cc935d` |
| 2 | `#25` | CR-S1 (alternância em L) | `33d035f` | `32e1c0e` |
| 3 | `#26` | CR-C1 (`expected_rows` físico) | `34bf696` → `b2daca8` | `0c6e8f7` |
| 4 | `#29` | CR-G12 (juntas entre bandas) | `73243e9` → `9531cf0` | `c88a031` |

Os HEADs `b2daca8` (C1) e `9531cf0` (G12) são os **merges de `origin/main`
para dentro da própria branch do PR**, feitos para resolver conflito
**exclusivamente documental** (`docs/PROJECT_STATUS.md` e
`nuvem/REGRAS_MODULACAO_BLOCOS.md`); nenhum arquivo de produção foi
alterado nessa resolução. `nuvem/core/engine/wall_stepper.py` fundiu
**sem conflito** entre CR-S1 e CR-G12. Checkpoint da integração:
`docs/CHECKPOINT_INTEGRACAO_CONSOLIDADA_2026-09-08.md`. O `PR #28`
**permanece `draft` e não foi integrado**.

Marco de PRODUÇÃO anterior: `PR #24` / `CR-V1` — **mesclado** (merge commit
`91258dd627af97fe437a56c0506eb096ca5aa267`). O SHA `62ea7f2` que constava
aqui era o do `PR #22` e estava **desatualizado**; a cadeia intermediária
(`PR #23`, `PR #24`) está em `docs/PROJECT_STATUS_LOG.md`. Antes dele, `PR #23` (registro
pós-merge, `e381992`) e `PR #22` / `CR-BENCH-OPENING-RECONSTRUCTION-A`
(merge commit `62ea7f26b9fb8af72c960b04d08f7b58cd115114`, pais
`3f293d1433e8c16eb186959e33a345b60ac944f9` + HEAD aprovado
`2ee526dc0a3eab9e059b5e22b6f205b39bfa76ff`; ver "Estado oficial do solver"
abaixo). A entrada de `PR #19` logo abaixo (`3ebcd9b`) está desatualizada
quanto ao SHA de `main` — `main` já continha `PR #20` /
`CR-BLOCK-FIT-TOLERANCE-C04` (`3f293d1`) antes deste merge; corrigir a
cadeia completa fica fora do escopo desta atualização (só registra o
merge do `PR #22`). Histórico anterior completo:
`docs/PROJECT_STATUS_LOG.md`.

## Estado oficial do solver

Só o que está realmente mesclado na `main`, na ordem em que foi integrado:

- **CR-2F-E / CR-2F-A / CR-2F-D** — geometria de paredes determinística e
  simétrica (ordem de entrada não muda o resultado); `W097` recuperada.
- **REVIT — SHORT CURVES** — extração do CAD não quebra mais em
  `ShortCurveTolerance` (`nuvem/core/wall_modeling.py`).
- **CR-BLOCK-01** — prisma/fiadas/amarração: coincidência de junta
  proibida dentro da MESMA banda de abertura eliminada (236 → 0).
- **CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT** (`PR #12`) — contrato
  geral de segurança para candidatos de reparo de papel de nó
  (course_a/course_b); SAFE REPAIR ativado em produção
  (`nuvem/core/engine/wall_stepper.py`, `nuvem/core/wall_modeling.py`).
- **CR-BLOCK-NODE-FILL-REVALIDATION** (`PR #17`) — metade simétrica da
  junta NÓ|FILL: a Fiada A passa a desencontrar da junta de nó da Fiada B
  (`wall_stepper.py`, `NODE_FILL_OPPOSITE_COURSE_ENABLED = True`).
  `PRISM_CONTINUOUS_JOINT` TGD 444→336, TP1 576→272, piloto 0→0;
  cobertura/aberturas/colisões/junções/ARM com delta zero; 0 conflitos
  com o Reference Corpus humano. Regras: seção 33 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
- **CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY** (`PR #18`) — os 2 gates do
  SAFE REPAIR (compensador consecutivo, cobertura por fiada) mediam PROXY
  (agregado cross-banda por letra de família; posse local cega à peça de
  canto emprestada de nó), não o defeito real. Corrigidos para
  `course_index` físico (compensador) e crédito FÍSICO de nó com 5
  condições, nos dois sentidos alvo↔vizinha (cobertura). 2 novos
  candidatos ARM aceitos — `TGD wall_idx=91/SAME_B`, `TP1 wall_idx=75/
  SAME_A` — ambos `CONFIRMED_BY_HUMAN`; `PRISM_CONTINUOUS_JOINT` TGD
  336→320, TP1 272→256; cobertura/aberturas/colisões/junções com delta
  zero. Relatório: `docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_
  IMPLEMENTATION.md`; regras: seção 34 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
- **CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION** (`PR #19`, **mesclado**)
  — decisão humana aprovada sobre B19: pode fechar um trecho residual de
  15-20cm quando existir, no MESMO NO e na MESMA FIADA, uma peca de
  amarracao real e integra (B34/B54) cobrindo geometricamente o ponto
  fisico do no, nunca sendo ele mesmo a peca de amarracao. Implementado
  como reparo pos-hoc isolado (`repair_b19_residual_fill`, mesmo padrao
  seguro do SAFE REPAIR do ARM). Medido no corpus: **TP1 8 candidatos
  elegiveis, 0 aceitos** (rejeitados por `no_tie_covering_node`);
  TGD/Piloto 0 candidatos elegiveis - mecanismo correto, zero efeito
  pratico hoje, zero risco de regressao. Relatorio:
  `docs/BLOCK_B19_RESIDUAL_FILL_IMPLEMENTATION.md`; regras: secao 35 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
- **CR-V1 — VALIDADOR DE ENCONTROS POR ELEVAÇÃO FÍSICA** (`PR #24`,
  **mesclado**, merge commit `91258dd`) — fidelidade do **validador de
  benchmark** (`nuvem/benchmark/validators/validate_junctions.py`); não
  toca solver, gabarito oficial nem regra normativa. O validador agrupava
  as fiadas de um nó pelo ÍNDICE ORDINAL `row["row"]` em vez da COTA: duas
  paredes com pilhas de tamanhos diferentes (meia-fiada cortada,
  `base_z_cm` diferente) tinham o mesmo índice apontando para cotas
  diferentes, gerando `JUNCTION_MISSING_BINDING` falso numa alvenaria
  amarrada corretamente (63% dos 373 achados do gabarito nasciam disso).
  Corrigido para agrupar por `row["elevation_cm"]`
  (`model.COURSE_Z_TOLERANCE_CM`, nenhuma tolerância nova), exigindo ≥2
  paredes do nó com fiada naquela cota. Medido em STATE_R→STATE_C:
  `JUNCTION_MISSING_BINDING` +49 → **+10**; nenhum outro código mudou.
  Testes: `tests/regression/test_junction_elevation_identity_cr_v1.py`.
  Regras: seção 5 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`; relatório:
  `docs/CR_V1_JUNCTION_VALIDATOR_ELEVATION_IDENTITY.md`.

- **CR-D1 — RECUPERAÇÃO DOCUMENTAL** (`PR #27`, **mesclado**, merge commit
  `7cc935d`) — só documentação: recupera as duas revisões independentes
  que a `main` citava e não continha
  (`docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md`,
  `docs/C04_INDEPENDENT_FINAL_REVIEW.md`) e registra a recuperação em
  `docs/CR_D1_DOCUMENTAL_RECOVERY.md`. Nenhum arquivo de produção tocado.
- **CR-S1 — O GIRO DO CANTO EM L É A ÚLTIMA SAÍDA** (`PR #25`,
  **mesclado**, merge commit `32e1c0e`) — correção **do solver**
  (`nuvem/core/engine/wall_stepper.py`). `_corner_bond_blocked_by_other_
  node` passa a devolver o CONJUNTO DE FIADAS bloqueadas em vez de um
  booleano, e `solve_l_corner` só sacrifica a alternância quando nenhuma
  fiada resolve. **Decisão do usuário (alternativa A):** preserva a
  amarração correta e ACEITA especificamente os **8 eventos físicos de
  compensadores por projeto** (`+8 COMPENSATOR_CONSECUTIVE` e
  `+8 COMPENSATOR_EXCESS_IN_RUN`) — isso **não** cria permissão geral para
  compensadores consecutivos, **não** implementa B19 como amarração e
  **não** altera a seção 35 nem qualquer threshold. Testes:
  `tests/test_solver_l_node_alternation_cr_s1.py` (16). Regras: seção 36
  de `nuvem/REGRAS_MODULACAO_BLOCOS.md`; relatório:
  `docs/CR_S1_L_NODE_ALTERNATION.md`.
- **CR-C1 — EXPECTATIVA DE FIADA FÍSICA E POR ELEVAÇÃO** (`PR #26`,
  **mesclado**, merge commit `0c6e8f7`) — correção do **contrato de
  validação** (`nuvem/benchmark/validators/validate_wall_coverage.py`);
  não toca o solver, o gabarito oficial, `baseline.json` nem
  `reference_score.json`. `settings.expected_rows` (teto de fiadas do
  PROJETO) deixa de ser a expectativa de CADA parede; a expectativa passa
  a ser física, por elevação e altura da parede. **A detecção de ausências
  reais de fiada é preservada** — a CR entrega as 28 paredes de `h=340`
  que param em `z=301` como defeito real do solver; `expected_rows` não
  vira silenciador de cobertura. Testes:
  `tests/regression/test_validator_coverage_expected_rows_cr_c1.py` (19).
  Regras: seção 37 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`; relatório:
  `docs/CR_C1_COVERAGE_EXPECTED_ROWS_PHYSICAL.md`.
- **CR-G12 — A REGRA #1 VALE NA FRONTEIRA ENTRE BANDAS** (`PR #29`,
  **mesclado**, merge commit `c88a031`) — correção **do solver**
  (`nuvem/core/wall_modeling.py`, `nuvem/core/engine/wall_stepper.py`):
  a proibição de junta vertical coincidente passa a ser avaliada TAMBÉM
  entre fiadas de bandas de abertura diferentes, por um segundo passe que
  só substitui o resultado quando a coincidência cross-band cai
  **estritamente**. Gate **G12 fechado: 12 identidades novas → 0 nos dois
  projetos**, com **zero junta contínua nova por identidade física** e
  delta zero em `COVERAGE_*`/`OPENING_*`/`JUNCTION_*`/`POSITION_*`.
  Trade-offs declarados, não escondidos: `PRISM_STAGGER_BELOW_TARGET`
  +31 no TGD (17 são a troca crítico → nível 2; as outras 16, todas em
  `W074`, são colaterais da mudança de aceitação do ARM SAFE REPAIR),
  `COMPENSATOR_EXCESS_IN_RUN` +2 no TGD no candidato CR-B, e **custo de
  tempo ~2,1×** (95,6% dele nos 22 rebuilds do ARM SAFE REPAIR, que são
  pré-existentes). Residual honesto: 2 identidades cross-band puras no
  TGD (`W069`, `t=649,5`). Testes:
  `tests/test_cross_band_joint_propagation_cr_g12.py` (20, dos quais 9
  `slow`), mais os contratos ajustados de
  `tests/test_block_arm_role_candidate_safety_contract.py` (t1/t9) e
  `tests/test_block_node_fill_revalidation.py` (t20) — **sem `skip`, sem
  `xfail`, sem asserção removida e sem threshold afrouxado**. Regras:
  seção 39 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`; relatórios:
  `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md` e
  `docs/CR_G12_REVISAO_INDEPENDENTE.md`.

Detalhe técnico de cada um: `docs/PROJECT_STATUS_LOG.md`.

## Trabalho ativo

- **CR-C1 — `expected_rows` GLOBAL acusava parede correta** (branch
  `claude/cr-c1-expected-rows-fisico`, base `origin/main` = `91258dd`,
  **`PR #26` MESCLADO em 2026-09-08 — merge commit `0c6e8f7`, HEAD
  aprovado `34bf696` + merge de compatibilidade `b2daca8`**) — correção do **contrato de validação**
  (`nuvem/benchmark/validators/validate_wall_coverage.py`, 1 arquivo de
  produção). Não toca o solver, o gabarito oficial, `baseline.json`,
  `reference_score.json` nem regra normativa de domínio. **NÃO inclui a
  CR-S1.**
  **Causa-raiz provada:** `validate_wall_coverage` lia
  `settings.expected_rows` (= `num_courses`, o TETO de fiadas do PROJETO) e
  comparava com a CONTAGEM de fiadas de CADA parede. As paredes do corpus
  têm alturas diferentes (220/260/270/280/281cm com passo de 20cm) — uma
  parede de 260cm nunca terá 17 fiadas. **Prova independente:** rodando os
  validadores sobre o PRÓPRIO gabarito HUMANO, `COVERAGE_MISSING_ROW` dá
  **95** (TGD) e **94** (TP1) — os mesmos números do `reference_score.json`
  oficial — e **100% deles** vêm desse ramo, ZERO do ramo do meio da pilha.
  **Correção mínima:** a pergunta passa a ser física e por ELEVAÇÃO —
  *ainda cabe uma fiada INTEIRA (próximo passo + corpo da peça) abaixo do
  pé-direito DESTA parede?* Não se calcula onde cada fiada cai: no gabarito
  a fiada do topo NÃO segue o grid (270cm fecha em z=250, 281cm em z=261,
  com canaleta `CJ19` de 29cm e peças `_C` de 9cm), e reproduzir isso no
  validador seria reimplementar a política de empilhamento do solver dentro
  dele. Regra registrada em `nuvem/REGRAS_MODULACAO_BLOCOS.md` **seção 37**
  (a 36 fica RESERVADA para a CR-S1, ainda não mesclada).
  **Medido (todos os validadores, duas árvores, por identidade física):**
  gabarito TGD 95→**0** e TP1 94→**0**; solver TGD 192→**190**; solver TP1
  e piloto sem mudança. **Delta ZERO em TODOS os demais códigos** nas cinco
  unidades — incluindo `COVERAGE_ROW_MOSTLY_EMPTY`, `COVERAGE_GAP_IN_ROW`,
  `POSITION_OVERLAP`, `PRISM_*`, `JUNCTION_*`, `COMPENSATOR_*` e
  `OPENING_*`. **Não é silenciador:** no solver do TGD o ramo do topo cai só
  **30→28** — as 28 preservadas são paredes de `h=340` que param em `z=301`
  (ainda cabe fiada em z=321), defeito REAL; as 2 removidas fecham em
  `z=321` (321+19=340 = topo exato), parede completa. Discriminação de
  **19cm**. O ramo do meio da pilha fica intocado (162→162).
  Testes: `tests/regression/test_validator_coverage_expected_rows_cr_c1.py`
  (**19 casos; 16 falham contra `origin/main` `91258dd`**) — alturas
  diferentes, base Z deslocada (612, o caso do TP1), fiada de topo fora do
  grid, faixas intercaladas de abertura, ausência REAL de fiada
  (anti-tautologia), fiada faltando no meio, parede sem altura declarada,
  invariância à ordem de entrada por identidade física e determinismo.
  Controles `tests/regression/test_validators.py` **23/23**. Suíte completa
  nesta branch: **2 failed, 885 passed** — as 2 falhas são
  `tests/regression/test_benchmark_baselines.py` (TGD `compensators` 52→61;
  TP1 `JUNCTION_MISSING_BINDING` 8→9) e são **PRÉ-EXISTENTES**, com as
  mesmas asserções e os mesmos valores medidos num *worktree* limpo de
  `91258dd` sem o patch. **Zero falhas novas.** A contagem fecha: base 868 +
  19 testes desta CR = 887.
  **Dívidas registradas, não escondidas:** `baseline.json` (TGD 265 / TP1
  16) e `reference_score.json` (95 / 94) ficam desalinhados de propósito —
  recalibração é escrita em arquivo oficial e exige autorização específica;
  os **162** achados do ramo do meio no solver do TGD seguem sem
  diagnóstico próprio (CR separada); as **28** paredes de `h=340` são
  defeito real do solver que esta CR ENTREGA, não corrige.
  **Medido também sobre o CANDIDATO da CR-B** (o estado onde o gate `G16`
  falha, reproduzido do gerador determinístico `5640933`): `STATE_R →
  STATE_C` dá `+17 MISSING_ROW` e `+23 ROW_MOSTLY_EMPTY` — exatamente os
  números do G16 — e com a C1 fica **`+0` / `+23`**. **O `G16` é COMPOSTO e
  esta CR resolve METADE dele:** `COVERAGE_ROW_MOSTLY_EMPTY` não lê
  `expected_rows` (compara as fiadas de uma parede entre si) e o resíduo é
  consequência da **divisão de paredes** da própria CR-B (+19 paredes, 184
  blocos mudaram de fiada). **`G16` continua NÃO aprovado**; a outra metade
  exige CR própria — proposta **CR-C2 (cobertura por segmento após divisão
  de parede)**, não implementada.
  Relatório: `docs/CR_C1_COVERAGE_EXPECTED_ROWS_PHYSICAL.md`.

- **CR-V1 — VALIDADOR DE ENCONTROS POR ELEVAÇÃO FÍSICA** (branch
  `claude/validador-encontros-elevacao-3u21lw`, base `origin/main` =
  `e381992`, `PR #24` **MESCLADO — merge commit `91258dd`**) — fidelidade do
  **validador de benchmark** (`nuvem/benchmark/validators/
  validate_junctions.py`); não toca solver, gabarito oficial nem regra
  normativa. Causa-raiz (achada na reconciliação independente do
  contrato CR-B, `docs/BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_
  RECONCILIATION.md`): o validador agrupava fiadas do nó pelo ÍNDICE
  ORDINAL `row["row"]` (posição na pilha da parede), não pela COTA —
  duas paredes com pilhas de tamanho diferente (meia-fiada cortada,
  `base_z_cm` diferente) tinham o mesmo índice apontando para cotas
  diferentes, gerando `JUNCTION_MISSING_BINDING` falso numa alvenaria
  amarrada corretamente (medido: 63% dos 373 achados do gabarito de hoje
  já nasciam disso). Corrigido para agrupar por `row["elevation_cm"]`
  (mesma tolerância do motor, `model.COURSE_Z_TOLERANCE_CM`, nenhuma
  tolerância nova) e exigir ≥2 paredes do nó com fiada registrada
  naquela cota para afirmar "faltou amarração" — regra explicada em
  `nuvem/REGRAS_MODULACAO_BLOCOS.md` seção 5. Medido em STATE_R→STATE_C
  (candidato CR-B, cópias isoladas, gabarito oficial intocado):
  `JUNCTION_MISSING_BINDING` +49 (defeito, índice ordinal) → **+10**
  (identidade física correta), TGD e TP1 — bate exatamente com a
  classificação independente (39 defeito do validador eliminados, 10
  mudança legítima de unidade em nós recém-registrados pela CR-B, 0
  defeito físico novo). Nenhum outro código de achado mudou de valor
  (`COVERAGE_*`, `PRISM_*`, `COMPENSATOR_*`, `OPENING_*`,
  `JUNCTION_NOT_ALTERNATING`, `JUNCTION_HALF_BLOCK_ADJACENT` — delta
  zero nos dois projetos). Testes novos:
  `tests/regression/test_junction_elevation_identity_cr_v1.py` (13
  casos A-G do pedido, 5 falham comprovadamente contra o código
  pré-fix). Não inicia nem mistura CR-S1 (o solver genuinamente para de
  alternar amarração no nó que muda de T para L — permanece defeito real
  do solver, não tocado), CR-C1 (`expected_rows` global) nem a
  integração oficial da CR-B.
- **CR-S1 — PERDA REAL DE ALTERNÂNCIA EM NÓ L** (branch
  `claude/corrigir-alternancia-no-l-76nnb3`, base `origin/main` =
  `91258dd`, **`PR #25` MESCLADO em 2026-09-08 — merge commit
  `32e1c0e`, HEAD aprovado `33d035f`**) — correção **do solver**
  (`nuvem/core/engine/wall_stepper.py`, 1 arquivo de produção). Não toca
  gabarito oficial, validador, baseline nem regra normativa de domínio.
  **Causa-raiz provada:** `solve_l_corner` gira a peça do canto (as DUAS
  fiadas para a mesma parede, perdendo a alternância) quando um encontro
  vizinho da mesma parede está perto demais; o gate que decide isso,
  `_corner_bond_blocked_by_other_node`, devolvia um BOOLEANO e descartava
  em QUAL FIADA o vizinho realmente ocupa a parede. No nó físico dos dois
  níveis (TGD `(338,52;187,05)` = TP1 `(8017,26;1289,95)`) o vizinho é um
  `T` a 50cm cuja parede PRINCIPAL é a bloqueada — e um T só deita peça na
  principal na **Fiada A**: a Fiada B estava livre o tempo todo. Com a
  topologia corrigida da CR-B esse nó passa de T para L e o solver ficava
  com 17 fiadas de um dono só; o humano alterna nas DUAS topologias. Não é
  "parede curta" (644cm e 939cm) nem artefato do validador.
  **Correção mínima:** o gate passa a devolver o CONJUNTO DE FIADAS
  bloqueadas (mesma geometria, mesma margem; dois alcances — 27cm na
  fiada em que o vizinho deita peça, `_node_default_reservation_cm` na
  outra, nunca zero), e `solve_l_corner` tenta, nesta ordem: (1) não mexer
  se a fiada que a parede bloqueada já tem está livre, (2) TROCAR
  `course_a`↔`course_b`, (3) só então GIRAR. O predicado booleano antigo
  fica bit a bit idêntico. Regra registrada em
  `nuvem/REGRAS_MODULACAO_BLOCOS.md` **seção 36**.
  **Medido (cópias isoladas, gabarito oficial intocado):** `main` atual
  com o `input.json`/`reference.json` oficiais → **delta ZERO por
  identidade física em TODOS os códigos, nos dois projetos** (risco de
  regressão na `main` de hoje = zero medido). Sobre o candidato CR-B
  (`IN_C × STATE_C`): `JUNCTION_NOT_ALTERNATING` **32→0** (TGD) e
  **16→0** (TP1); `PRISM_CONTINUOUS_JOINT` −32/−16 e `PRISM_JOINT_STACK`
  −2/−1 viram `PRISM_STAGGER_BELOW_TARGET` +32/+16 (minor) nas MESMAS
  paredes (TGD `W071`/`W073`, TP1 `W071`) — junta deixou de ser
  coincidente; `COVERAGE_*`, `POSITION_OVERLAP`, `JUNCTION_MISSING_
  BINDING`, `JUNCTION_HALF_BLOCK_ADJACENT` e todos os `OPENING_*` com
  **delta zero**. **Custo real registrado, não escondido:**
  `COMPENSATOR_CONSECUTIVE` **+8** e `COMPENSATOR_EXCESS_IN_RUN` **+8**
  por projeto, na parede N-S do próprio nó (eixo
  `[338,523;180,048]→[338,523;824,048]` no TGD;
  `[8017,26;1282,95]→[8017,26;1926,95]` no TP1 — o rótulo `W0xx` é
  derivado de índice e NÃO é identidade física). **Investigado até o fim
  (relatório §9), sem alterar código:** são **8 eventos físicos, não
  16** (o MESMO par `C04`+`C09` dispara os dois códigos — provado pelos
  `id` dos blocos citados), e a causa é **aritmética**: o trecho da fiada
  ímpar tem 49cm úteis entre o nó (`t=0`) e a reserva do `T` vizinho
  (`t≈50`); com o `B34` de amarração sobram **14cm**, e a enumeração
  exaustiva do catálogo dá **só** `C04+C09` (2) ou `C04+C04+C04` (3) —
  **nenhuma peça fecha 14cm sozinha**, o solver já escolhe o mínimo. Sem
  peça no nó (o giro da `main`) o trecho era de 34cm e fechava com um
  `B34`, zero compensadores: o "lucro" do giro era composição limpa ao
  preço da amarração. **Não existe correção dentro do contrato**; as duas
  saídas conhecidas exigem **decisão normativa** e NÃO foram tomadas —
  (1) `B19` como peça de amarração do canto (é o que o humano faz, 1
  compensador; **proibido pela seção 35**), (2) `B54` do `T` na fiada
  ímpar (mudaria a convenção de `solve_t_intersection` em todo o corpus).
  O `repair_b19_residual_fill` da seção 35 **não se aplica** (mede o
  residual da parede inteira, 610cm, e um `B19` não caberia em 14cm).
  Margem declarada: `COMPENSATOR_VERTICAL_STRIP` fica 2→2, mas por **uma
  fiada** (`8/17 = 0,47` contra limiar `0,50`). Bônus da mesma causa-raiz: o nó pré-existente do TGD
  `(163,51;237,05)` também volta a alternar (`IN_R`:
  `JUNCTION_NOT_ALTERNATING` 16→0). **`JUNCTION_NOT_ALTERNATING` é
  `major` e NÃO entra em `critical_errors`** — o ganho de amarração não
  aparece no saldo crítico e está reportado à parte, de propósito.
  Testes: `tests/test_solver_l_node_alternation_cr_s1.py` (16 casos; **7
  falham comprovadamente contra `origin/main` `91258dd`**), cobrindo o nó
  real do TP1, a geometria equivalente do TGD, as 17 fiadas e os 16 pares
  consecutivos, ausência de colisão, invariância à ordem de entrada,
  inversão de orientação, determinismo e controles de L/T/X já corretos.
  Suíte completa nesta branch: **2 failed, 882 passed** — as 2 falhas são
  `tests/regression/test_benchmark_baselines.py` (TGD `compensators`
  52→61; TP1 `JUNCTION_MISSING_BINDING` 8→9) e são **PRÉ-EXISTENTES,
  formalmente provado**: rodando SÓ esse arquivo num *worktree* limpo de
  `91258dd`, **sem o patch**, falham os mesmos 2 testes com a mesma
  asserção (`2 failed, 7 passed in 375.47s`). A comparação de benchmark
  contra o baseline nas duas árvores também dá resultado **linha por
  linha idêntico**. Nenhum baseline
  regravado, nenhum `--save-baseline`, nenhum `skip`/`xfail`, nenhum
  threshold alterado. Determinismo: `sha256` idêntico em 3 processos
  novos por projeto.
  Relatório: `docs/CR_S1_L_NODE_ALTERNATION.md`. **Não inicia CR-C1,
  CR-B oficial, C02, C10 nem Junction/S1/S2 antigos. Sem monitoramento
  automático.**
- **CR-BLOCK-FIT-TOLERANCE-C04** (branch
  `claude/cr-block-fit-tolerance-c04-n5qsc4`, PR #20 **DRAFT, nao
  mergeado**, veredito **READY_FOR_INDEPENDENT_REVIEW**) - duas
  tolerancias SEPARADAS, uma para cada pergunta:
  `PIER_FIT_TOLERANCE_CM` (0,30cm) decide se a sobra de um trecho PODE ser
  considerada modular (`_pier_remaining_snapped_cm`;
  `pier_closes_with_blocks_cm`), e `PIER_PHYSICAL_FIT_TOLERANCE_CM`
  (0,05cm, = o piso de ruido que ja' existia) decide ONDE a peca pode
  existir de fato - uma GUARDA FISICA impede que o valor snapado
  materialize peca alem de uma fronteira sem junta de argamassa (jamba de
  abertura, ponta livre, reserva de no'), remontando o trecho com o maior
  conteudo modular que cabe (`pier_cm_floored_to_module`).
  `PIER_LAYOUT_TOLERANCE_CM` continua 0,05cm e intocada.
  Resultado medido: `COVERAGE_GAP_IN_ROW` TGD 1959->1649 / TP1 327->214,
  `blocks` TGD +1052 / TP1 +1155 (98,4-100% do ganho da ablacao
  independente), `OPENING_BLOCK_CROSSES_JAMB` com delta **ZERO** nos 3
  projetos (verificado por instancia), `POSITION_OVERLAP`/`JUNCTION_*`/
  demais `OPENING_*` com delta zero, TGD `critical_errors` 884->872.
  Trade-off exposto e nao corrigido (fora de escopo): `COMPENSATOR_*` e
  `PRISM_*` sobem nos trechos recem-destravados. Determinismo (4 seeds) e
  invariancia identicos ao pre-existente. `baseline.json`/`reference.json`
  intocados. Relatorio: `docs/BLOCK_FIT_TOLERANCE_C04_IMPLEMENTATION.md`.
  **Revisao independente concluida** (`docs/C04_INDEPENDENT_FINAL_REVIEW.md`,
  branch `claude/c04-review-next-cr-prep-wc77d7`): veredito
  **APPROVE_WITH_EXPLICIT_CONDITIONS** - NAO e' `APPROVE_FOR_MERGE`. Faltam
  DUAS decisoes explicitas do usuario (C1 e C2 abaixo) e ficam registradas
  DUAS dividas tecnicas (C3 e C4 abaixo). **Aguarda decisao do usuario; sem
  monitoramento automatico.**

  - **C1 - PENDENTE DE DECISAO DO USUARIO.** Regressao real de composicao
    no TGD: a categoria `compensators` sai de **815 achados na `main` de
    hoje** para **1083** com o C04, ultrapassando o baseline congelado
    (950). O teste `tests/regression/test_benchmark_baselines.py`
    **passa** em STATE_A e **falha** em STATE_C - portanto NAO e' artefato
    nem falha pre-existente. Causa medida: o C04 preenche trechos que a
    `main` deixava vazios, e em parte deles o solver monta uma composicao
    PIOR que a humana (medido: humano `W016` f0 usa **um B19** em 15-34;
    o solver usa **C09+C04** e para 5cm antes). Nao regravar `baseline.json`
    para esconder isso.
  - **C2 - PENDENTE DE DECISAO DO USUARIO.** Saldo critico do TP1 piora:
    **469 -> 485** (`+16`), motor `PRISM_CONTINUOUS_JOINT` **256 -> 290**
    (`+34`). Verificado por instancia que **50 de 50** dos prismas novos
    aparecem onde pelo menos uma das duas fiadas nao tinha material nenhum
    em STATE_A (`EXPECTED_EXPOSURE` testado, nao assumido) - mas
    `EXPECTED_EXPOSURE` **nao** e' sinonimo de `ACCEPTABLE` nem de
    `RESOLVED`: sao 34 juntas continuas fisicas reais no resultado final.
  - **C3 - DIVIDA REGISTRADA: ramo overconservative da guarda fisica
    (W087).** A guarda disparou **1205** vezes no corpus, estratificadas
    pelo tipo real de fronteira: **952 em jamba de abertura real**
    (`PHYSICALLY_REQUIRED_GUARD`, junta ZERO por contrato), **138 na
    familia `W087` `[85.242, 94.0]`** (`OVERCONSERVATIVE_GUARD`
    demonstrado) e **115 em outras fronteiras de fim de regiao**
    (`INCONCLUSIVE` - a folga fisica nao foi verificada). Nao classificar
    os 1205 como "todos fisicamente necessarios". No caso `W087` a guarda
    troca um `C09` por um `C04`; o `C09` removido teria **0,758cm de folga
    fisica** ate' a peca de amarracao de `W106` (`T_binding`, mesma fiada)
    - a reserva de no' e' real e ocupada, mas a guarda e' conservadora
    demais ali, porque trata `hi` como fronteira sem folga quando existe
    1,00cm de junta ate' a perpendicular. Custo: **5 vazios** reportados
    (`W087` fiadas 7-11). **NAO resolvido.** Fix minimo ja' especificado e
    **nao implementado**: expor em `region_solid_subsegments` a folga
    fisica real alem de `hi` (ex. `trailing_slack_cm`, derivada da proxima
    ocupacao fisica real e do contrato de junta) e a guarda usar
    `max(PIER_PHYSICAL_FIT_TOLERANCE_CM, trailing_slack_cm)`; em jamba de
    abertura `trailing_slack_cm = 0`, entao as 952 fronteiras criticas
    ficam identicas. Toca `nuvem/core/engine/continuous_modulation.py`,
    **fora** do escopo autorizado do C04: exige CR propria, STATE_A/B
    proprios, revalidacao das 41 e um teste de contrato entre os dois
    modulos. Proibido nesta CR: aumentar tolerancia global, usar folga
    presumida ou criar excecao por `W087`/`wall_id`.
  - **C4 - DIVIDA REGISTRADA: escopo GLOBAL da tolerancia x escopo LOCAL
    da guarda.** `PIER_FIT_TOLERANCE_CM` (0,30cm) foi aplicada em
    `_pier_remaining_snapped_cm`, que e' um mecanismo de composicao
    **global**; a guarda fisica foi aplicada em **um unico ponto de
    chamada**, `_solve_repair_subsegments`. `_pier_ordered_layout` e'
    chamado sem a guarda em outros pontos (l. 4160, 4263, 4290, 4693,
    4713). A revisao independente **nao encontrou escape estrutural novo
    no corpus atual** (`OPENING_BLOCK_CROSSES_JAMB` e `POSITION_OVERLAP`
    restaurados por identidade geometrica, 0 novas), e por isso **nao e'
    bug comprovado**; mas ausencia de regressao no corpus **nao e' prova
    universal**. Verificacao futura exigida: todos os call sites, tipo de
    fronteira, juntas de contorno, contrato de `region_solid_subsegments`,
    colocacao fisica, reversao de orientacao, protecao de abertura e
    protecao de reserva de no'. **Nao generalizar a guarda nesta
    integracao.**
  - **C5 - PRESERVADO.** `baseline.json`, `reference.json`,
    `reference_score.json` e `input.json` **intocados** pelo PR; nenhum
    threshold de regressao alterado; nenhum teste excluido, marcado
    `xfail` ou `skip`. As **2 falhas** da suite completa em STATE_C sao o
    guard-rail `tests/regression/test_benchmark_baselines.py` e ficam
    visiveis de proposito: (a) TGD `compensators` - **regressao real
    causada pelo C04** (C1); (b) TP1 `JUNCTION_MISSING_BINDING` 8->9 -
    **`REAL_SOLVER_DEFECT` pre-existente**, ja' presente em STATE_A (a
    suite da `main` sem C04 falha com a mensagem literalmente identica);
    o C04 nao o introduz nem o agrava. As duas nao podem ser somadas na
    mesma frase: a primeira e' custo deste PR, a segunda nao.

- **CR-BENCH-OPENING-RECONSTRUCTION-A** (branch
  `claude/opening-detector-root-fix-m21hfm`, `PR #22` **MESCLADO** — merge
  commit `62ea7f26b9fb8af72c960b04d08f7b58cd115114`, autorizado
  explicitamente pelo usuário após a revisão independente e a aplicação de
  todas as condições, aceitando SÓ NESTA CR os quatro deslocamentos de
  0,06cm abaixo) — `nuvem/core/engine/opening_audit.py::detect_wall_
  openings_from_courses` respondia duas perguntas diferentes com o mesmo
  número: a tolerância de identidade (`OPENING_RUN_EDGE_MATCH_TOLERANCE_CM`,
  ~15cm) decide se o vazio de duas fiadas é a MESMA abertura, mas a
  geometria gravada virava o ENVELOPE (união) dos vazios, deixando a
  tolerância de identidade vazar para a largura do vão. Corrigido para
  gravar o **consenso** (interseção dos vazios OBSERVADOS em todas as
  fiadas do trecho) em vez do envelope — **separação entre IDENTIDADE
  (tolerância) e GEOMETRIA OBSERVADA (consenso) mantida explicitamente**.
  `opening_provenance` novo (`RECONSTRUCTED_CONSENSUS`/`INCONCLUSIVE`);
  **`RECONSTRUCTED_CONSENSUS` NÃO equivale a `MEASURED`** — o consenso é o
  intervalo comum aos vazios observados, não confirmação de jamba física
  real (revisão independente corrigiu overclaim de vocabulário no código e
  na doc). Diff de produção: 1 arquivo, só docstring/comentário desde a
  revisão (nenhuma linha executável mudou — AST idêntica antes/depois,
  ignorando docstrings, reconfirmado pós-merge contra a nova `main`). HEAD
  de produção mesclado `2ee526dc0a3eab9e059b5e22b6f205b39bfa76ff`
  corresponde ao HEAD revisado pela revisão independente. 44 testes focados
  (`tests/test_opening_reconstruction_cr_a.py`) passando; última suíte
  completa (medida antes da revisão, sem efeito no diff documental
  posterior): **871 passed / 2 failed** — as 2 falhas são as mesmas
  dívidas já conhecidas do `PR #20` (`C1`: `compensators` do TGD; `TP1`
  `JUNCTION_MISSING_BINDING` 8→9), não novas, não agravadas (score do
  solver byte-idêntico entre STATE_A/STATE_B). Solver dos 3 projetos com
  delta ZERO (gabarito congelado não chama o detector). Desvio de hard
  gate declarado: **4 aberturas reconstruídas** do corpus (TGD `W082`; TP1
  `W029`/`W040`/`W072`) têm deslocamento de centro de 0,06cm por
  coordenada fracionária de extração — nenhuma tem `source_element_id`
  correspondente, aceito só para estes 4 casos e para esta CR, não como
  regra geral. Registro técnico em `nuvem/REGRAS_MODULACAO_BLOCOS.md`
  seção 10.9 (só adição). Relatórios:
  `docs/BENCH_OPENING_RECONSTRUCTION_A_IMPLEMENTATION.md` e
  `docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` (veredito
  **APPROVE_WITH_EXPLICIT_CONDITIONS**, condições já aplicadas).
  **Mesclada à `main` com autorização explícita do usuário** (merge normal,
  sem squash/rebase; commit `62ea7f26b9fb8af72c960b04d08f7b58cd115114`).
  Autorização cobriu, só para esta CR, os 4 deslocamentos de 0,06cm acima —
  **não** cria tolerância geral de 0,06cm, **não** altera abertura medida
  do Revit, **não** trata geometria reconstruída como jamba física
  confirmada. Pendências declaradas, **não resolvidas por este merge**:
  `CR-BENCH-OPENING-RECONSTRUCTION-B` (decisão humana entre "abertura
  estreita" e "duas paredes separadas" para os 19 casos por projeto com
  assinatura de 15cm) **não iniciada**; família de 0,11–0,12cm de
  coordenada fracionária (causa é a extração, não o detector) **não
  resolvida**; guard defensivo de `INCONCLUSIVE` em
  `audit_existing_masonry_openings` **registrado, não implementado**
  (mudaria comportamento de produção). `baseline.json`/`reference.json`/
  `reference_score.json`/`input.json` intocados; nenhum threshold, `skip`
  ou `xfail` alterado. **Ganho de métrica projetado pela CR-B (`CROSS_JAMB`
  168→0, críticos 485→327) NÃO é ganho integrado** — o solver com gabarito
  congelado permanece com delta ZERO nesta CR-A; só se materializa se/quando
  a CR-B regravar o gabarito.

`PR #9` (`CR-BLOCK-ARM-ROLE-INVARIANCE`, **CLOSED, não mesclado** —
NECESSITA AJUSTE, branch histórica preservada) e `PR #11`
(`CR-BLOCK-ARM-ROLE-HUMAN-POLICY`, **CLOSED, mesclado** — docs-only,
conteúdo de produção idêntico ao já presente via `PR #9`/histórico,
superseded pela integração posterior) não são trabalho ativo — ver
`docs/PROJECT_STATUS_LOG.md` para o registro completo dessa série.

## Reference Corpus

3 projetos de benchmark (`torre_easy_lo_r00_tgd`, `torre_easy_lo_r00_tp1`,
`piloto_sintetico_2x2`) em `nuvem/benchmark/projects/`. Documento vivo com
o significado de cada métrica e o procedimento de medição:
`docs/REFERENCE_CORPUS.md`.

## Snapshot atual

Fotografia legível do último estado oficialmente medido da `main`:
`docs/CURRENT_REFERENCE_SNAPSHOT.md` (substituível — não é histórico,
não é append-only).

## Problemas abertos

- **Alinhamento cross-band** (entre bandas de abertura) — 33 casos
  residuais, fora do escopo do `CR-BLOCK-01`; exige mudança em
  `wall_modeling.py`. Ver `nuvem/REGRAS_MODULACAO_BLOCOS.md` 27.7.
  Próximo CR recomendado: `CR-BLOCK-DETERMINISM`.
- **Determinismo global do wall graph** — não determinístico antes e
  depois do `CR-BLOCK-01` (8 execuções, 8 fingerprints distintos); causa
  é anterior ao preenchimento de blocos.
- **Compensadores/pastilhas repetidos (C09/C04)** — melhoraram como
  efeito colateral, não resolvidos.
- **Degradação de encontros em X, exclusão de bloco em vão de porta,
  reparo de abertura (`non_modular` +3)** — pendentes, sem CR aberto.
- **Arestas rejeitadas no `CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT`**
  (7 no TGD, 3 no TP1) — diagnosticadas em `docs/BLOCK_ARM_REJECTED_
  EDGES_DIAGNOSIS.md`. `CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY` (branch
  em aberto, ver "Trabalho ativo") corrigiu os 2 gates de proxy e
  resolveu 2/10 (`TGD 91`, `TP1 75`); as 6 restantes (TGD 89/90/92/120,
  TP1 20/91) continuam corretamente rejeitadas por causa física real
  (Grupo B — reserva pior-caso em parede curta; espelho de paridade —
  fora do escopo desta CR); 2 (TGD 4/54) são `OUT_OF_SCOPE_ROTATED_
  CORNER`. Próximo passo, se priorizado: `CR-BLOCK-SHORT-WALL-NODE-
  PIECES` (Grupo B, exige decisão de regra — ver diagnóstico).
- **Pareamento `(474, 2306)`** — eixo espúrio de ~43,9 m continua no
  resultado; sem CR atribuído.
- **Regra do meio-bloco (B19) perto de amarração** — evidência de domínio
  coletada (`docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md`) e decisão
  aprovada IMPLEMENTADA (e corrigida em revisão pós-review) em branch
  separada, não mesclada (`CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION`,
  PR #19, ver "Trabalho ativo") — B19 como fill residual de 15-20cm só
  quando o MESMO nó/MESMA fiada tem amarração real íntegra cobrindo o
  ponto físico, nunca substituindo B34/B54. Resultado medido no corpus
  atual: **0 candidatos aceitos em TP1/TGD/Piloto** (o padrão de
  alternância par/ímpar do canto L nunca satisfaz a condição de mesma
  fiada) — mecanismo correto e testado, mas sem efeito físico hoje; zero
  risco de regressão. Regra na `main` **ainda não alterada** (aguarda
  merge autorizado).
- **Detector de espessuras da UI** amostra só as primeiras 900 linhas
  cruas do layer — não limita o solver real, mas pode ocultar espessuras
  raras na sugestão da tela. Dívida de UX, não corrigida por decisão
  explícita do usuário.
- **Teste visual INTEGRADO completo no Revit** (extração → paredes
  criadas → inspeção visual) — adiado por decisão do usuário; retomar
  quando priorizado.

- **Guarda fisica do C04 - ramo overconservative em fim de regiao**
  (C3 acima, `docs/C04_INDEPENDENT_FINAL_REVIEW.md` 8.3/8.5) - 138
  disparos da familia `W087` sao conservadores demais; 115 disparos em
  outras fronteiras de fim de regiao seguem **inconclusivos**. Fix minimo
  especificado (`trailing_slack_cm` em `region_solid_subsegments`),
  **nao implementado**, fora do escopo do C04.
- **Assimetria escopo global/local da tolerancia de fit** (C4 acima) -
  `PIER_FIT_TOLERANCE_CM` e' global, a guarda e' local a
  `_solve_repair_subsegments`; outros call sites de
  `_pier_ordered_layout` nao passam pela guarda. Sem contraexemplo no
  corpus atual; divida arquitetural aberta, nao bug comprovado.
- **Metrica `OPENING_BLOCK_CROSSES_JAMB` em valor ABSOLUTO nao e'
  confiavel** - rodando os validadores sobre o PROPRIO gabarito humano:
  TGD **208**, TP1 **209**, com **195 ocorrencias de exatamente 15,0cm**
  nos dois projetos. Assinatura de artefato de reconstrucao do
  benchmark. So' o **delta por identidade geometrica** (o solver contra
  ele mesmo) e' valido hoje - foi assim que a revisao do C04 usou o
  gate. CR de benchmark proposta: `BENCH-OPENING-RECONSTRUCTION`.

**Nenhuma divida registrada aqui equivale a autorizacao para pioras
futuras.** Registrar C1-C4 documenta o custo conhecido de UMA integracao
especifica; nao cria licenca para novas regressoes de composicao, de
amarracao ou de cobertura em CRs seguintes, nem dispensa os hard gates
por identidade geometrica.

Detalhe/causa-raiz de cada item: `docs/PROJECT_STATUS_LOG.md`.

## Próximos passos

0. **Varredura ampla do benchmark em dois blocos** — próxima etapa
   definida pelo usuário depois da integração consolidada de 2026-09-08,
   a ser feita em **sessão nova** e **sem exigir perfeição**. Pendências
   que a integração deixou explicitamente em aberto: **G16 continua
   pendente da CR-C2**; a **CR-B NÃO está oficialmente aprovada**; o
   `PR #28` continua `draft` e não integrado; as **duas falhas históricas
   de `tests/regression/test_benchmark_baselines.py`** continuam
   registradas como pré-existentes (o refresh de `baseline.json` é CR
   própria, não foi feito); a dívida de desempenho **~2,1×** da CR-G12
   segue declarada, com a alavanca real nos 22 rebuilds do ARM SAFE
   REPAIR.
1. `CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY` — branch em aberto (ver
   "Trabalho ativo"); merge só com autorização explícita do usuário.
2. Aguardar autorização/priorização do usuário para o próximo CR de
   engine (candidatos: `CR-BLOCK-DETERMINISM`, alinhamento cross-band,
   compensadores/pastilhas, `CR-BLOCK-SHORT-WALL-NODE-PIECES` para as 6
   arestas do Grupo B/espelho de paridade que Gate Fidelity deixou
   corretamente rejeitadas).
3. Pendência registrada (33.5, NODE-FILL): o reparo local junto ao vão
   ainda recria a junta 34,5 em `W036`/`W038` (TP1, bandas com janela).
4. Teste visual integrado no Revit — retomar quando o usuário priorizar.

## Não reabrir sem evidência de regressão

Áreas já resolvidas e validadas (simetria de pairing/merge/dedup,
determinismo da passada 1 do merge, `ShortCurveTolerance`, amarração
same-band do `CR-BLOCK-01`) não devem ser alteradas só para "melhorar" —
exige evidência objetiva de regressão. Lista completa e o motivo de cada
uma: `docs/PROJECT_STATUS_LOG.md` (seção 8 do histórico).

Evitar mudanças sem necessidade concreta em `create_centerline`,
`find_wall_pairs`, `tolerances.py`.

## Regra permanente de atualização

Ao concluir qualquer CR de engine, **este documento e o
`docs/PROJECT_STATUS_LOG.md` devem ser atualizados antes de encerrar o
trabalho** — não é opcional. `PROJECT_STATUS.md` recebe só o resumo do
estado atual (seções acima); a entrada completa (o que foi alterado,
testes, invariantes, benchmarks, dívidas novas, próximo passo) vai para o
log cronológico em `PROJECT_STATUS_LOG.md`, sem apagar entradas
anteriores. Há um lembrete automático
(`.github/workflows/check-project-status.yml`) que sinaliza quando
`nuvem/core/engine/**` muda sem que `docs/PROJECT_STATUS.md` seja tocado
no mesmo diff — não bloqueia push/merge, só avisa.

## Sessão multifase CR-C2 / revisão C1 / reavaliação CR-B (2026-09-08)

> Tudo abaixo é **trabalho em PR draft ou diagnóstico**. **Nenhum merge
> foi feito, nenhum PR foi marcado `ready`, nenhum arquivo oficial foi
> regravado e nenhum monitoramento automático foi criado.**

### PRs abertos — estado real

| PR | CR | branch / HEAD | estado |
|---|---|---|---|
| #25 | **CR-S1** — alternância em nó `L` de ponta | `claude/corrigir-alternancia-no-l-76nnb3` `33d035f` | **draft**, não mesclado |
| #26 | **CR-C1** — `expected_rows` físico | `claude/cr-c1-expected-rows-fisico` `34bf696` | **draft**, não mesclado |
| #27 | **CR-D1** — recuperação documental | `claude/cr-d1-recuperacao-documental` `b852695` | **draft**, não mesclado |
| #28 | **CR-B preparação** — identidade/G18 | `claude/cr-b-preparacao-identidade` `0596e78` | **draft**, não mesclado |
| — | **CR-C2** — diagnóstico (sem patch) | `claude/multifase-cr-c2-c1-b-ikr8jc` | esta branch |

Um PR **draft não é um gate aprovado**. A revisão da CR-C1 registrada em
`docs/CR_C1_INDEPENDENT_REVIEW.md` é uma **revisão por medição própria em
worktree isolado — não é um review formal do GitHub** e não substitui um.
As execuções de `pytest` citadas são **locais nesta sessão — não são
checks de CI**.

### Entregas desta sessão

- `docs/CR_C1_INDEPENDENT_REVIEW.md` — revisão independente do PR #26.
  Veredito **APPROVE**, sem patch proposto. Merge continua **pendente de
  autorização explícita**.
- `docs/CR_C2_ROW_MOSTLY_EMPTY_WALL_SPLIT.md` — causa-raiz dos `+23`
  `COVERAGE_ROW_MOSTLY_EMPTY`. **Diagnóstico concluído, SEM PATCH**: a
  correção exige decisão normativa do usuário.
- `docs/CR_B_G12_G16_REEVALUATION.md` — G12 e G16 reavaliados sobre a
  projeção `S1 + C1`, e contrato de integração da CR-B conferido por
  medição própria.
- `nuvem/REGRAS_MODULACAO_BLOCOS.md` §38 — registro obrigatório do
  conhecimento, rotulado como **pendência de decisão**, não como regra
  aprovada.
- `nuvem/benchmark/future_cr_preparation/cr_c2_row_mostly_empty/` —
  diagnósticos reprodutíveis.
- `docs/CR_C2_DECISAO_FISICA.md` — as 3 opções da C2 com contrato
  integral, busca do fundamento normativo de cada uma e **duas correções
  da análise anterior**. **Nenhum patch**: nem A nem B implementam
  contrato existente. Recomendação revista: **opção C isolada**.
- `docs/CR_G12_CROSS_BAND.md` — tabela física das 12 identidades do G12,
  causa-raiz e escopo da **CR-G12** (preparada, **não iniciada**).
- `docs/CHECKPOINT_SESSAO_MULTIFASE_C2.md` — checkpoint da sessão.
  **Gravado em `docs/` de propósito:** `.gitignore` linha 8 ignora
  `.claude/*`, então um checkpoint escrito em `.claude/checkpoints/`
  **nunca é commitado** e se perde com o contêiner — foi o que
  aconteceu com `sessao-multifase-s1-c1-b-d1.md`, que esta sessão
  recebeu como insumo e não existe em nenhuma branch.

### Gates — estado real após esta sessão

| gate | estado | nota |
|---|---|---|
| **G12** (`PRISM_CONTINUOUS_JOINT`) | ✘ **não aprovado** | reavaliado: **28 → 12** identidades novas com a S1. A S1 melhora 57% mas **não zera**. **Causa-raiz localizada** (fronteira de banda de abertura, §27.7/§39): `docs/CR_G12_CROSS_BAND.md`. **12 de 12 são defeito físico real** — não compensados por melhora em outros códigos |
| **G13** (`JUNCTION_NOT_ALTERNATING`) | resolvido pela **S1** (`+16 → 0`) | aprovação depende do **merge autorizado** da S1 |
| **G16** (`COVERAGE_*`) | ✘ **não aprovado** | `MISSING_ROW` `+17 → +0` pela C1; `ROW_MOSTLY_EMPTY` `+23` continua |
| **G18** (identidade) | artefato ✔, oficial ✘ | 0 chaves ambíguas nos 3 estados; gravar no oficial depende do usuário |

**Nenhum gate foi promovido a aprovado nesta sessão.**

### Dívidas e decisões pendentes do usuário

- **Decisão normativa da CR-C2** — 3 opções em
  `docs/CR_C2_DECISAO_FISICA.md`. **Recomendação: opção C isolada**
  (A é normativa nova; **B foi retirada** — contradiz a tese física da
  própria CR-B). Sem decisão, a CR-C2 não pode ser implementada.
- **G12** — autorizar ou não a **CR-G12** (`docs/CR_G12_CROSS_BAND.md`).
  As 12 identidades são **defeito físico real**, com causa-raiz conhecida
  (§27.7/§39) e correção já proposta lá. Exige escrever
  `nuvem/core/wall_modeling.py` e abre dívida de **refresh de
  `baseline.json`**. **Não iniciada.**
- **Merge da CR-S1 (#25)** e **da CR-C1 (#26)** — pendentes.
- **`reference_score.json`** — recalibração pendente (escrita oficial).
- **`baseline.json`** — refresh pendente (CR própria, autorizada).
  Há **2 falhas de baseline PRÉ-EXISTENTES na `main`**, reproduzidas nas
  duas árvores com os mesmos valores (TP1: `JUNCTION_MISSING_BINDING`
  8 → 9). Não são regressão de nenhuma CR desta sessão.
- **D1–D5** — não decididas; nenhuma foi tomada, influenciada ou presumida.

### Ordem de integração recomendada (não executada)

1. **CR-S1** (#25) — resolve G13, melhora G12.
2. **CR-C1** (#26) — resolve metade do G16. *(S1 e C1 tocam a mesma
   posição de `REGRAS_MODULACAO_BLOCOS.md` — conflito de merge previsível
   e trivial: §36 e §37.)*
3. **Decisão normativa da CR-C2** → só então implementação.
4. **Decisão sobre o G12 residual.**
5. **D1/D2/D3** pelo usuário → só então a CR-B oficial.
6. **CR-D1** (#27) — documental, independente, não bloqueia.

## Sessão CR-G12 — correção do mecanismo cross-band (2026-09-08)

> **SUPERADA em 2026-09-08 pela integração consolidada:** a CR-G12 foi
> **mesclada** na `main` pelo `PR #29` (merge commit `c88a031`). O texto
> abaixo é o registro da sessão de desenvolvimento e continua válido como
> histórico; a linha "nenhum merge" descreve **aquela** sessão, não o
> estado atual. Nenhum arquivo oficial foi regravado
> (`baseline.json`/`reference_score.json`/gabarito intocados) nem antes
> nem durante a integração.

| item | valor |
|---|---|
| branch | `claude/cross-band-mechanism-fix-ab76jv` |
| base | `main` `91258dd` + o diagnóstico de `claude/multifase-cr-c2-c1-b-ikr8jc` (`a25f846`) |
| arquivos de produção | `nuvem/core/wall_modeling.py`, `nuvem/core/engine/wall_stepper.py` |
| relatório | `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md` |
| regras | `nuvem/REGRAS_MODULACAO_BLOCOS.md` §27.7 (status) e §39.3/§39.4 |

### O que mudou

A regra #1 (junta vertical nunca coincide entre fiadas vizinhas) passa a
ser avaliada **também na fronteira entre bandas de abertura**. Cada banda
publica as juntas **reais** de cada fiada física; a banda seguinte recebe
essas juntas como semente e só troca de composição quando há **ganho
estrito** e nenhuma piora nas regras que já valiam. Dois passes
(Gauss-Seidel), com **aceitação global** — o segundo só substitui o
primeiro se a coincidência cross-band total cair estritamente.
Desligável por `CROSS_BAND_JOINT_PROPAGATION_ENABLED` (default `True`);
desligado, é bit-a-bit o comportamento anterior.

### Reproducer

**3 paredes REAIS** do `input.json` oficial do TGD (índices 55/82/124),
obtidas por *delta-debugging* — não por proximidade. Falha no código
anterior pelo **mesmo mecanismo físico** (junta em `t=39,5` presa à borda
de um `B54` de `T_INTERSECTION_MIDSPAN`, desencontro 0,00cm) e some com a
correção. `nuvem/benchmark/future_cr_preparation/cr_g12_cross_band/repro_g12d_minimo.py`.

### Resultado físico

| projeto | identidades NOVAS do G12 sem o patch | **com o patch** |
|---|---|---|
| TGD (candidato CR-B + S1+C1) | 12 | **0** |
| TP1 (candidato CR-B + S1+C1) | 12 | **0** |

`PRISM_CONTINUOUS_JOINT` **não sobe** — cai: corpus oficial TGD 336→322,
TP1 290→260, piloto 0→0; candidato −42/−48/−26/−32. **Zero** juntas
contínuas novas. `COVERAGE_*`, `OPENING_*`, `JUNCTION_*` e
`POSITION_OVERLAP` com **delta 0**.

**Trade-offs declarados:** `PRISM_STAGGER_BELOW_TARGET` sobe (+31 TGD,
+25 TP1 — nível 2, troca crítico→menor); `COMPENSATOR_EXCESS_IN_RUN` +2
no TGD do candidato; solver **~2× mais lento** (48s → 94s por resolução
completa do TGD); sobram **2** identidades cross-band residuais no TGD
(nenhuma entre as 12 do G12).

### Gates após esta sessão

| gate | estado |
|---|---|
| **G12** | **12 → 0 nos dois projetos.** Pronto para revisão humana; **não** declarado aprovado por conta própria |
| **G13** | inalterado (delta 0 em `JUNCTION_*`); continua dependendo do merge da S1 |
| **G16** | ✘ **continua não aprovado** — a **CR-C2 continua pendente** de decisão normativa. Esta CR não o destrava |
| **G18** | inalterado |

### Suíte completa

| árvore | resultado |
|---|---|
| `main` `91258dd` **sem patch** (cópia isolada) | **2 failed, 884 passed** |
| `main` **+ CR-G12** | **4 failed, 882 passed** |
| `tests/test_cross_band_joint_propagation_cr_g12.py` | **20 passed** |

As **2 pré-existentes** são as de `test_benchmark_baselines` (TGD
`compensators` 52→61, TP1 `JUNCTION_MISSING_BINDING` 8→9) — idênticas nas
duas árvores, dívida de refresh de `baseline.json`. As **2 novas** são
asserções de *magnitude de reparo* que falham **por melhoria**
(`test_t1_t9_...` e `test_t20_...`): o resultado físico final é idêntico
nos dois casos. **Nenhuma foi alterada, nenhum `skip`/`xfail` foi usado** —
ver `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md` §7.2.

### Dívidas que continuam abertas

- `baseline.json` e `reference_score.json` — **não** regravados.
- §27.8 item 2 (`UNCLASSIFIED_RULE_CONFLICT`, junta de peça de
  **amarração** repetida) — sem decisão normativa, **fora** desta CR.
- Decisão normativa da **CR-C2**; merge da **CR-S1 (#25)** e da
  **CR-C1 (#26)**; **D1–D5**.
- Custo de tempo do segundo passe e as 2 identidades residuais do TGD.

## Entradas de contexto

- `docs/START_HERE.md` — roteador de onboarding por domínio.
- `docs/PROJECT_STATUS_LOG.md` — histórico completo de CRs e log
  cronológico.
- `docs/DEVELOPMENT_PROCESS.md` — processo de engenharia (fluxo de CR).
- `docs/REFERENCE_CORPUS.md` — corpus de benchmark.
- `docs/CURRENT_REFERENCE_SNAPSHOT.md` — última medição oficial.
- `nuvem/REGRAS_MODULACAO_BLOCOS.md` — regras técnicas de modulação e
  amarração (fonte de domínio, não duplicada aqui).
