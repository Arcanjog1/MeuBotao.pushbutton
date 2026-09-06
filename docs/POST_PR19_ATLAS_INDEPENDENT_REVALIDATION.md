# POST-PR19 ATLAS INDEPENDENT REVALIDATION — FINAL

Revalidação independente dos achados acionáveis do `BLOCK_SOLVER_RESIDUAL_
ROOT_CAUSE_ATLAS` sobre a `main` oficial pós-PR19. Nenhum arquivo de
produção foi alterado nesta sessão; todas as medições abaixo foram
**reexecutadas do zero** (solver real, sem reaproveitar número do Atlas
como verdade) num worktree isolado.

## Main

`origin/main` = `3ebcd9b63875f9114a3d6223aa648e5075e2d35b` — confirmado por
`git rev-parse origin/main` após `git fetch origin`. Worktree isolado
criado a partir deste commit (branch local
`claude/post-pr19-atlas-independent-revalidation`, depois consolidado na
branch de trabalho desta sessão). Zero merge, zero alteração de produção.

## Atlas HEAD

`claude/block-solver-residual-root-cause-gwcmqa` = `9834b40d745b8209
d39bbb3efa235ce64bcbb911`, um único commit sobre a base histórica
`209695d5559b53fe4cc8a92300779a8ae73b7c1d` (confirmado via
`git merge-base origin/main origin/claude/block-solver-residual-root-
cause-gwcmqa`). O Atlas nunca viu o código do PR #19 — coerente com a
premissa da tarefa.

## Current-state compatibility

`run_state_current.py` (scripts do Atlas, copiados para um diretório
diagnóstico novo, `nuvem/benchmark/diagnostics_residual_atlas/`, e
reexecutados sobre a `main` atual) reproduziu **exatamente** os números
do Atlas e do enunciado desta tarefa:

| métrica | TGD (esperado / medido) | TP1 (esperado / medido) | Piloto |
|---|---|---|---|
| walls | 167 / **167** | 96 / **96** | 12 / **12** |
| blocks | 10 679 / **10 679** | 18 417 / **18 417** | 772 / **772** |
| PRISM_CONTINUOUS_JOINT | 320 / **320** | 256 / **256** | — |
| COVERAGE_GAP_IN_ROW | 1 959 / **1 959** | 327 / **327** | 16 / **16** |
| COMPENSATOR_CONSECUTIVE | 379 / **379** | 1 443 / **1 443** | 36 / **36** |
| fingerprint físico | `09bc1b0c…` idêntico | `8d08d591…` idêntico | `e66bcd80…` idêntico |

**Zero divergência.** PR #19 (`CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION`)
tem efeito físico **zero** no corpus atual, confirmando o que o próprio
PR já reportava (0 candidatos aceitos nas 3 revisões) — o Atlas pode ser
tratado como medido diretamente sobre a árvore oficial atual, sem
reinterpretação.

## C04 reproduction

Ablação `fit_tol_0_3` (`PIER_LAYOUT_TOLERANCE_CM`/`MODULATION_WHOLE_
CM_TOLERANCE_CM` 0.05→0.30cm, monkeypatch em memória, script
`run_ablation.py` do próprio Atlas) reexecutada sobre a `main` atual:

| | TGD base→ablado (Δ) | TP1 base→ablado (Δ) |
|---|---|---|
| COVERAGE_GAP_IN_ROW | 1959→1644 (**-315**) | 327→214 (**-113**) |
| COVERAGE_PARTIAL_WALL | 61→48 (**-13**) | 6→0 (**-6**) |
| COVERAGE_MISSING_ROW | 258→192 (**-66**) | — |
| COVERAGE_ROW_MOSTLY_EMPTY | 112→150 (+38) | 18→0 (**-18**) |
| blocks | 10679→11735 (+1056) | 18417→19572 (+1155) |

Números **idênticos, casa a casa**, aos reportados pelo Atlas (`TGD GAP
-315/MISSING_ROW -66/PARTIAL -13`; `TP1 GAP -113/PARTIAL -6/ROW_MOSTLY_
EMPTY -18`). **Classificação: CONFIRMED.**

## C04 tolerance sweep

Matriz 0.05/0.10/0.15/0.20/0.25/0.30cm (script novo,
`run_ablation_sweep.py`, mesma técnica de monkeypatch) — achado que o
Atlas **não tinha medido** (só testou o extremo 0.30):

| tolerância | TGD blocks (Δ) | TGD achados que mudam | TP1 blocks (Δ) | TP1 achados que mudam |
|---|---|---|---|---|
| 0.05 (produção) | 10679 (0) | — | 18417 (0) | — |
| 0.10 | 10771 (+92) | GAP -96, MOSTLY_EMPTY +18, PARTIAL -2 | 19192 (+775) | GAP -33, PARTIAL -4, +COMPENSATOR/PRISM |
| 0.15 | 10771 (+92) | **idêntico a 0.10** | 19572 (+1155) | **já satura — idêntico a 0.30** |
| 0.20 | 10771 (+92) | **idêntico a 0.10/0.15** | 19572 (+1155) | idêntico a 0.30 |
| 0.25 | 11012 (+333) | GAP -185, MISSING_ROW **-16** (1º movimento), +COMPENSATOR | 19572 (+1155) | idêntico a 0.30 |
| 0.30 | 11735 (+1056) | GAP -315, MISSING_ROW **-66** (efeito pleno) | 19572 (+1155) | idêntico a 0.30 |

**Achado novo, não coberto pelo Atlas original**: os dois corpora
**não saturam no mesmo ponto**. TP1 satura em **0.15cm** (0.20/0.25/0.30
são idênticos a 0.15 — nenhum ganho adicional, nenhum custo adicional).
TGD tem um platô pequeno e estável entre 0.10-0.20cm (só GAP -96 de
-315 possíveis, **MISSING_ROW não se move nada** nesse platô) e só
desbloqueia a maior parte do ganho (MISSING_ROW -66, GAP -315) em
**0.30cm** — 0.25cm já é parcial (MISSING_ROW só -16) mas incompleto.

**Implicação para a faixa candidata**: um valor abaixo de ~0.25cm deixaria
o TGD com menos de 30% do ganho de cobertura possível (e ainda assim já
pagando parte do custo de COMPENSATOR/COMPENSATOR_EXCESS); **0.30cm é o
menor valor testado que entrega o efeito pleno nos dois corpora
simultaneamente** sem exigir tolerância diferente por projeto. Não há,
dentro da matriz testada, um ponto "melhor que 0.30" — 0.30 não é apenas
"seguro", é **necessário** para o TGD.

## C04 physical/human validation

Trace de composição real (`wall_course_items`/`compose`) comparado ao
gabarito humano (`reference.json`) em dois exemplos:

- **TP1 W012** (1484cm): no baseline a composição já é densa (B54/B34/C09
  reais espalhados), mas um trecho inteiro do meio (entre dois nós) fica
  **sem nenhum item** (ausente da string composta) — isso é exatamente o
  "família inteira vazia" do C04. Na ablação, esse trecho aparece
  preenchido com uma sequência B39/B54/B34/C09 plausível. O humano cobre
  a parede **inteira** (1484cm, praticamente sem vazio) com B39/B34/B54
  reais na mesma região — confirma que o vazio do baseline era
  **preenchimento físico correto perdido por tolerância** (classe A).
- **TP1 W022** (123.97cm, trecho curto): a ablação preenche a fiada 1 com
  `C09 C09 C09` novos (cadeia de compensadores) onde o humano tem
  `B19[34.99-53.99] B19[69.99-88.99]` — o trecho realmente precisa ser
  preenchido (não é vazio físico legítimo), mas a composição escolhida
  pelo solver depois de destravado **não é a do humano**: em vez de B19,
  produz compensador. Confirma a advertência do próprio Atlas ("efeito
  colateral: paredes preenchidas trazem seus próprios defeitos").

**Classificação do blast radius: MIXED (A predominante, B presente em
trechos curtos)** — a maior parte do volume novo é preenchimento físico
correto (coerente com o ganho líquido de COVERAGE), mas uma fração
recorrente vira COMPENSATOR/PRISM novo porque a lógica de composição
(`_pier_ordered_layout`/tiers, C07/S2) ainda não escolhe a peça que o
humano escolheria. **Isto não invalida C04** — apenas confirma que o
"ganho" de C04 deve ser medido junto com o aumento esperado (e já
documentado) de COMPENSATOR_CONSECUTIVE/EXCESS/PRISM, nunca escondido.

## C02 result

Reproduzido **por chamada direta da função de produção real**
(`wall_stepper._x_intersection_wall_room_ft`, sem monkeypatch, no nó real
do TP1 — nó 154, X_INTERSECTION em t=61.98cm do W003, ponto
`(216.77, 19.52)` em pés): `room_minus_ft` → **27.98/27.99cm**, abaixo do
limiar `28.00cm` (27 + 1cm de junta) por **0.01-0.02cm** — confirma
exatamente o "27,99 < 28,00" do Atlas.

**Teste de translação** (deslocando o ponto de consulta ao longo do eixo
em incrementos de 0.01cm, mesma função real): o resultado degrada
(`< 28.0`) em shift 0, +0.01 e -0.01cm, e deixa de degradar em +0.1cm —
ou seja, a fronteira física fica entre 0.02 e 0.09cm de deslocamento.
Confirma **ORDER/POSITION-SENSITIVE a ~0.01cm**, exatamente como o Atlas
descreve (R2b muda com translação). **Classificação: CONFIRMED.**

## C10 result

`probe_opening_repair.py` (trace real, sem monkeypatch de lógica, só
instrumentação) rodado em TP1 W036 (wall_idx 35) sobre a `main` atual
reproduziu a sequência completa: `_recut_openings_and_repair` derruba
`[35-74 B39]`; a Fiada A repara com `avoid_joint_positions_cm=[]` (vazio)
e produz `B34[35-69]` — **junta 34.5 renasce**; a Fiada B repara com
`avoid_joint_positions_cm=[34.5, ...]` e evita, produzindo
`C09[55-64]+C04[65-69]`. A junta 34.5 da Fiada A coincide com a junta
NÓ|FILL da Fiada B (`B34 T_INCOMING [0-34]`), reproduzindo o defeito
exatamente como descrito.

Comparação humana (`reference.json` W036): row 0 tem junta em **49.5**
(`B34[15-49]|B39[50-89]`), row 1 tem junta em **34.5**
(`B34[0-34]|B34[35-69]`) — cada família com **uma única** junta,
diferente entre si — confirma `CONFIRMED_BY_HUMAN`.

Contagem de findings relacionados verificada diretamente nos
`findings.json` reais: **20 PRISM_CONTINUOUS_JOINT** nos exatos muros
citados pelo Atlas (W036×8, W038×8, W023×1, W042×1, W043×1, W085×1).
**Classificação: CONFIRMED** (mecanismo, contagem e comparação humana,
todos batendo exatamente).

## JUNCTION_MISSING_BINDING reconciliation

Inspeção geométrica direta (sem depender do relatório do Atlas) do nó 64
do TP1 (L_CORNER entre W039 e W041, ponto físico `(6177.25, 949.95)`):

- W039 (comprimento 384cm): a ponta que toca o nó fica em `t=377`, ou
  seja, o corpo da própria parede **continua 7cm além do ponto do nó**.
  Na Fiada A (fiadas 0,2,4,...,16), o único candidato próximo ao nó é uma
  peça **da parede vizinha** (W041, projetada), sem nenhuma peça própria
  de W039 nessa fiada; na Fiada B, W039 tem `B34[350-384]` própria.
- W041 (comprimento 509cm): a ponta que toca o nó fica em `t=-8` no eixo
  próprio de W041 — ou seja, **o eixo de W041 só começa 8cm depois do
  ponto físico do nó**. O `B34` de canto da Fiada A de W041 nasce em
  `t=0` (own) e por isso **não alcança** o quadrado do canto (que fica
  8cm antes). Na Fiada B, W041 tem um `B34[-15,-1]` que **cobre** o
  quadrado (estende para trás do próprio início do eixo).
- Achados reais lidos de `findings.json` (não do Atlas): **exatamente 9**
  `JUNCTION_MISSING_BINDING`, nas fiadas 0,2,4,6,8,10,12,14,16 (todas
  pares = Fiada A) — bate 100% com a análise geométrica acima.
- Referência humana (`reference.json`, wall `W039`, rows 0/1/2
  verificadas): `B19[365-384]` presente em **todas** as fiadas checadas,
  cobrindo o canto **nas duas famílias**.

**Respostas às 4 perguntas do item 9**:
1. Existe buraco físico real no solver? **SIM** — 9 fiadas pares sem
   nenhuma peça própria cobrindo o quadrado do canto, confirmado
   geometricamente, não só por finding.
2. O humano realmente cobre esse trecho? **SIM** — B19[365-384] presente
   em ambas as famílias, todas as fiadas checadas.
3. A diferença 8→9 é causada por artefato de benchmark, defeito de
   solver, ou ambos? **Defeito de solver com precondição de entrada**:
   o desalinhamento de 7/8cm entre o ponto do nó e o início dos eixos de
   W039/W041 vem da geometria de entrada (Fase A), mas o solver não
   detecta essa condição nem gera uma peça alternativa (ex.: um B19 como
   o humano) para cobrir o quadrado do canto quando o B34 padrão não
   alcança.
4. O validator está apontando para a parede/nó certo? **SIM** — mesmo
   ponto físico, mesmas paredes, mesmas fiadas.

**Classificação: REAL_SOLVER_DEFECT** (com precondição de entrada) —
concordando com a reclassificação do Atlas e **divergindo** da
classificação histórica `PRE_EXISTING/P3/BENCHMARK_ARTIFACT`. Este item
NÃO deve voltar a ser tratado como artefato de benchmark.

## REGRAS_MODULACAO_BLOCOS audit

`git diff origin/main..origin/claude/block-solver-residual-root-cause-
gwcmqa -- nuvem/REGRAS_MODULACAO_BLOCOS.md` mostra a seção 35 sendo
**substituída**: o texto antigo (`CR-BLOCK-B19-RESIDUAL-FILL-
IMPLEMENTATION`, o relatório do PR #19) desaparece e um texto novo
(`CR-BLOCK-SOLVER-RESIDUAL-ROOT-CAUSE-ATLAS`) aparece no lugar. **Isto
não é uma remoção deliberada de conhecimento** — é um artefato de
divergência de branch: o Atlas foi criado a partir de `209695d` (ANTES
do PR #19 existir) e escreveu sua própria seção 35 nesse ponto da
história; o PR #19 escreveu uma seção 35 diferente, mais tarde, já
mergeada na `main`. Um merge direto do Atlas geraria **conflito de
numeração de seção** nesse arquivo — a ser resolvido (renumerando a
seção do Atlas, por exemplo para 36) **somente se e quando** a branch do
Atlas for de fato integrada. Nenhuma ação necessária agora.

Conteúdo novo do Atlas (35.1–35.6), classificado conforme pedido:

- **(A) regras já aprovadas pelo usuário**: nenhuma. O Atlas não propõe
  nem marca nada como regra nova aprovada — corretamente.
- **(B) observações humanas medidas (MEDIDO)**: 35.5 (junta NÓ|FILL
  recriada pelo reparo, confirmada por trace) e 35.6 (JUNCTION_MISSING_
  BINDING W039/W041 é buraco físico, confirmado nesta sessão de forma
  independente — ver seção acima).
- **(C) hipóteses / padrões ainda não confirmados**: 35.2 (parede curta
  entre dois nós — humano concentra os dois cantos na mesma família) e
  35.3 (boneca ≤70cm e X de parede curta sem amarração) — ambos
  explicitamente rotulados `PADRÃO OBSERVADO AINDA NÃO CONFIRMADO` /
  `DOCUMENTADO — decisão de regra aberta`, com N=1 planta (TGD/TP1 são o
  mesmo projeto).
- **(D) conflitos com regras OBRIGATÓRIAS vigentes**: 35.1 (humano usa
  B19 encostado em amarração — contradiz a regra #2) e 35.4 (B34 como
  enchimento em fileira — contradiz a seção 23.6 "GANHO: B34/B54 como
  enchimento 2460→0"). Ambos rotulados `CONFLITO REGISTRADO` e o texto
  do Atlas já afirma explicitamente que a regra vigente **continua
  valendo** até decisão humana em contrário — tratamento correto.

**Recomendação**: manter como está. Nenhum item do Atlas foi promovido a
`OBRIGATÓRIA` sem aprovação — o processo do `CLAUDE.md` foi seguido. A
única pendência é a colisão de número de seção com o relatório do PR #19,
relevante apenas no dia de um merge real (não agora).

## S1/S2 domain dependencies

Confirmado por leitura: nem `SHORT_WALL_NODE_POLICY`, nem
`FILL_B34_MODULE`, nem "B19 encostado", nem qualquer nova política de
amarração foram implementados nesta sessão (nenhum arquivo de produção
foi tocado — ver "Production diff" abaixo). As duas causas-raiz S1
(política de peça de nó em nós apertados) e S2 (regras de composição do
fill) permanecem corretamente marcadas como dependentes de decisão de
domínio (conflitam com as regras #2 e 23.6 vigentes) e **não devem
preceder C04** — confirmado: nenhuma delas concorre com C04 por arquivo
(`wall_stepper.py`/`modulation_math.py` são tocados por ambas as frentes,
mas C04 mexe em constantes de tolerância enquanto S1/S2 mexem em lógica
de decisão de peça — sequenciável, não excludente).

## ARM performance confirmation

Ablação `no_arm` (`ARM_ROLE_SAFE_REPAIR_ENABLED=False`) reexecutada:

| projeto | com ARM | sem ARM | fração do runtime |
|---|---|---|---|
| TGD | 40.9s | 2.2s | **ARM ≈ 95%** do tempo |
| TP1 | 61.3s | 2.4s | **ARM ≈ 96%** do tempo |

Ordem de grandeza idêntica ao Atlas (40,9/2,7s TGD; 61,3/2,9s TP1 — a
pequena diferença de wall-clock é ruído de execução, não de mecanismo).
`PRISM_CONTINUOUS_JOINT` sobe sem ARM (+27 TGD, +16 TP1), confirmando que
o ARM não é só custo — ele resolve prismas reais. **Confirma "ARM SAFE
REPAIR domina o runtime"** — não bloqueia C04.

## Recommended next CR

**APPROVE_C04_WITH_CONSTRAINTS**

`CR-BLOCK-FIT-TOLERANCE` é o próximo CR correto — reprodução independente
100% consistente (mecanismo, magnitude, ordem de saturação) — mas com
duas condições que a investigação desta sessão adiciona ao que o Atlas já
recomendava:

- **causa**: `_pier_remaining_snapped_cm`/`_pier_remaining_cm`
  (`wall_stepper.py`) rejeitam (`None`) qualquer resto de trecho que
  desvie mais que `PIER_LAYOUT_TOLERANCE_CM` (hoje 0.05cm,
  `modulation_math.py`) de um múltiplo de 5cm, derrubando a família
  inteira do trecho.
- **função afetada**: `MODULATION_WHOLE_CM_TOLERANCE_CM` /
  `PIER_LAYOUT_TOLERANCE_CM` (`modulation_math.py`); consumidores em
  `wall_stepper.py` (`_pier_remaining_snapped_cm`, `_pier_remaining_cm` e
  todo lugar que compara contra a tolerância — ver `grep` acima, ~14
  pontos de uso).
- **faixa de tolerância candidata**: **0.30cm** (não um valor menor) — a
  varredura mostrou que o TGD só atinge o efeito pleno (MISSING_ROW -66,
  GAP -315) em 0.30cm; 0.15-0.25cm deixam o TGD com boa parte do ganho de
  cobertura ainda escondido. TP1 satura em 0.15cm mas não regride com
  0.30cm (resultado idêntico) — portanto **0.30cm serve aos dois
  corpora sem trade-off entre eles**.
- **hard gates obrigatórios** (antes de aceitar a implementação):
  1. Nenhuma mudança em `baseline.json`/`reference.json`/`reference_
     score.json` sem autorização explícita do usuário PARA ESSA
     atualização específica (`STATE_A → implementação → STATE_B →
     comparação física/humana → só então decidir baseline`, conforme
     pedido no item 17 desta tarefa).
  2. Medir e **relatar explicitamente** (nunca esconder) o aumento
     esperado de `COMPENSATOR_CONSECUTIVE`/`COMPENSATOR_EXCESS_IN_RUN`/
     `PRISM_CONTINUOUS_JOINT`/`PRISM_STAGGER_BELOW_TARGET` como
     trade-off aceito, não como regressão oculta — a ablação mostrou
     esses aumentos acontecendo nos dois corpora e no TGD já a partir de
     0.10cm.
  3. Validação humana amostral obrigatória num conjunto de paredes antes
     de fechar (o exemplo W022 mostrou que a composição pós-tolerância
     pode divergir do humano em qualidade, mesmo cobrindo fisicamente).
  4. Determinismo (fingerprint idêntico em processos novos,
     `PYTHONHASHSEED` distintos) deve continuar valendo — não verificado
     de novo nesta sessão para o valor final 0.30 além do que o Atlas já
     tinha medido; deve ser revalidado na implementação real.
- **métricas que podem melhorar**: `COVERAGE_GAP_IN_ROW`,
  `COVERAGE_MISSING_ROW`, `COVERAGE_PARTIAL_WALL`,
  `COVERAGE_ROW_MOSTLY_EMPTY`, `COVERAGE_WALL_NOT_MODULATED`.
- **métricas que NÃO podem regredir sem trade-off explícito e
  documentado**: nenhuma tem gate de "zero regressão" absoluto (isso
  contradiria o próprio mecanismo), mas qualquer aumento em
  `POSITION_OVERLAP`, `JUNCTION_*`, `OPENING_BLOCK_INSIDE_DOOR` (achados
  estruturais/críticos que não apareceram na ablação, mas devem ser
  revalidados na implementação real, não só na ablação em memória) deve
  travar o CR até investigação — a ablação atual não mexeu nesses
  códigos em nenhum valor testado, o que é um bom sinal, mas não é uma
  prova formal para a implementação final (código de produção pode
  interagir diferente do monkeypatch isolado).
- **corpus**: TGD + TP1 (ambos obrigatórios — são os dois que mostram
  efeito; Piloto como controle de regressão/determinismo).
- **testes necessários**: (a) unitário da fórmula de tolerância na matriz
  completa de restos (como já existe em outros CRs, ex.
  `test_block_b19_residual_fill_implementation.py` T2); (b) determinismo
  em processo novo; (c) teste de invariância a ordem/espelho/rotação
  (reaproveitando `run_invariance.py`); (d) amostra de comparação humana
  documentada (`W012`, `W022`, `W093-W095` do Atlas + os que a
  implementação real tocar).
- **baseline strategy**: **NÃO atualizar baseline na implementação
  inicial.** Seguir STATE_A → implementação → STATE_B → comparação
  física/humana → só depois decidir se e como atualizar baseline/
  reference — exatamente como pedido no item 17, e como o próprio PR #19
  (B19 residual fill) já demonstrou ser o padrão seguro deste projeto
  (found zero effect, integrated with zero risk, baseline update never
  needed).

Constraint adicional herdada do Atlas, não deste relatório: **C04 deve
rodar primeiro e sozinho** — S1/S2/C03 e as demais CRs precisam ser
medidas sobre a base pós-C04 (paredes hoje vazias escondem outros
defeitos que só aparecem depois do fix de tolerância).

## Production diff

```
$ git diff origin/main --name-only
(vazio)
```

Zero arquivos de produção alterados. Único diretório novo:
`nuvem/benchmark/diagnostics_residual_atlas/` (scripts diagnósticos
copiados do Atlas + `run_ablation_sweep.py`, novo, só para a varredura de
tolerância do item 6) e este documento.

## Baseline/reference diff

Zero alteração. Nenhum script escreveu em
`nuvem/benchmark/projects/*/baseline.json`,
`nuvem/benchmark/projects/*/reference.json` ou
`nuvem/benchmark/projects/*/reference_score.json` — confirmado por
inspeção do código (`atlas_lib.py`/`run_ablation.py`/
`run_ablation_sweep.py` nunca chamam `write_json` para esses caminhos,
só para `ATLAS_OUT_DIR`, que fica fora do diretório de projetos) e por
`git status`/`git diff` no worktree.

## Verdict

**APPROVE_C04_NEXT (com as constraints listadas acima:
APPROVE_C04_WITH_CONSTRAINTS).**

A revalidação independente confirma, sem exceção, todos os achados
acionáveis do Atlas testados nesta sessão: compatibilidade pós-PR19
(exata), C04 (exata, e refinada com a varredura de tolerância que faltava
no Atlas original), C02 (confirmada por chamada direta da função real),
C10 (confirmada por trace real + comparação humana), JUNCTION_MISSING_
BINDING W039/W041 (confirmada como REAL_SOLVER_DEFECT por inspeção
geométrica independente, não só leitura do relatório), e a performance do
ARM SAFE REPAIR (confirmada em ordem de grandeza). A auditoria de
REGRAS_MODULACAO_BLOCOS.md não encontrou nenhuma promoção indevida de
observação para regra obrigatória.

**PARE.** Nenhum fix foi implementado. Nenhum merge foi feito. Nenhum
monitoramento foi armado.
