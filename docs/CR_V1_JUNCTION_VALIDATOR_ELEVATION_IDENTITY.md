# CR-V1 — VALIDADOR DE ENCONTROS POR ELEVAÇÃO FÍSICA

> CR exclusivamente de **fidelidade do validador de benchmark**. Não
> altera o solver, o gabarito oficial nem regra normativa de amarração.
> Não implementa CR-S1, CR-C1 nem a integração oficial da CR-B.

## Base / branch / HEAD

| item | valor |
|---|---|
| `origin/main` no início desta sessão | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` — confere com a base histórica do enunciado; `main` não avançou |
| branch desta CR | `claude/validador-encontros-elevacao-3u21lw`, criada a partir de `e381992` |
| fonte diagnóstica | `docs/BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_RECONCILIATION.md` (branch `claude/cr-b-reconciliacao-contrato-1byigr`, HEAD `14926fb8f8514828b3133ce5c129c80bd60c9890`) |
| candidato CR-B (referência, não integrado) | branch `claude/candidato-validacao-gabarito-q450yr`, HEAD `56409334a7b273d0e81a13d8cc916ffe0e214654` |

## Causa-raiz

`nuvem/benchmark/validators/validate_junctions.py` agrupava as fiadas de
um nó (`_rows_of_group` → `_covering_blocks`) pelo **índice ordinal**
`row["row"]` — a posição da fiada na pilha daquela parede
(`extract/reconstruct.py:group_by_course`, `extract/from_solver.py`),
nunca pensado como identidade comparável **entre paredes diferentes**.

Duas paredes que chegam ao mesmo nó com pilhas de tamanhos diferentes
(meia-fiada de peça CORTADA, `base_z_cm` diferente) têm o **mesmo
índice apontando para cotas diferentes**. O validador comparava fiadas
fisicamente distintas só porque tinham o mesmo número de ordem, e
concluía `JUNCTION_MISSING_BINDING` numa alvenaria perfeitamente
amarrada.

**Medido no gabarito oficial, hoje, sem nenhum corte:** 236 de 373
achados de `JUNCTION_MISSING_BINDING` do TGD (63%) e 232 de 365 do TP1
(64%) já nascem de um índice ordinal que aponta para mais de uma cota —
o defeito é **pré-existente**, a CR-B só o amplifica.

Cada fiada (`model.make_row`) já carrega o campo físico correto,
`elevation_cm` — não foi preciso inventar campo nenhum:

```python
def make_row(index, elevation_cm, blocks=None):
    return {"row": int(index), "elevation_cm": round(float(elevation_cm), 3),
            "blocks": list(blocks or [])}
```

## Contrato físico de elevação

**Antes:** fiada do nó = `row["row"]` igual entre paredes.

**Depois** (`_elevation_groups_of_group`, `validate_junctions.py`):

1. A identidade de fiada, para comparar **entre paredes diferentes** do
   mesmo nó, passa a ser `row["elevation_cm"]`, agrupada por
   proximidade com a **mesma tolerância que o motor já usa** para
   juntar peças em fiada por cota Z — `model.COURSE_Z_TOLERANCE_CM =
   2,0cm` (`extract/reconstruct.py:group_by_course`,
   `analysis.OccupancyIndex`). Nenhuma tolerância nova foi criada.
2. **"Faltou amarração" só é afirmável quando pelo menos duas paredes**
   do nó têm fiada registrada (com peça ou não) naquela cota
   (`_cluster_participant_wall_ids`) — uma banda presente numa única
   parede é dado incompleto **daquela parede** (ela pode não ter curso
   nenhum naquela altura), não uma acusação comparável de amarração
   faltando na vizinha. Confirmado necessário pelo próprio reprodutor
   (ver "Testes" abaixo, caso da meia-fiada exclusiva).
3. O índice ordinal continua disponível como metadado de apresentação
   (`row`, `rows_by_wall` no achado) — nunca mais como chave de
   comparação entre paredes.
4. `JUNCTION_NOT_ALTERNATING` e `JUNCTION_WRONG_PIECE` (nível 2) passam
   a usar a mesma sequência de fiadas físicas — eram a mesma causa-raiz,
   pelos mesmos `_rows_of_group`/`_covering_blocks` buscados.

Nenhuma regra de X/T/L, preferência de B54, regra de B19, critério de
alternância, cobertura, prisma ou compensador foi alterada — só a
identidade de fiada usada para AVALIAR o que já existe.

## Diff de produção

Um arquivo: `nuvem/benchmark/validators/validate_junctions.py`.

- `_rows_of_group(group)` (indexava por ordinal) → removida.
- `_covering_blocks(group, row_index)` → `_covering_blocks(cluster,
  point_cm)`, opera sobre um cluster de elevação em vez de um índice.
- Nova `_elevation_groups_of_group(group)` — clusteriza `(parede, fiada)`
  por `elevation_cm` com `ELEVATION_GROUP_TOLERANCE_CM =
  model.COURSE_Z_TOLERANCE_CM`.
- Nova `_cluster_participant_wall_ids(group, cluster)` — paredes do nó
  com QUALQUER fiada (peça ou não) na banda de cota do cluster.
- `validate_node` e `_node_pieces` passam a iterar clusters de elevação
  em vez de índices ordinais; achados ganham `elevation_cm`,
  `rows_by_wall` (e `elevation_a`/`elevation_b` em
  `JUNCTION_NOT_ALTERNATING`) como campos novos — `row`/`row_a`/`row_b`
  continuam presentes, agora como a posição da fiada física correta na
  sequência do nó (não mais o rótulo ordinal por parede).

## Testes

`tests/regression/test_junction_elevation_identity_cr_v1.py` — 13
casos cobrindo A-G do pedido:

| caso | teste | falha sem o fix? |
|---|---|---|
| A | índices iguais/cotas diferentes não agrupam | não (já funcionava) / sim (variante de cota própria) |
| B | índices diferentes/mesma cota associam corretamente | **sim** |
| C | participantes em bases (`base_z_cm`) diferentes | **sim** |
| D | ausência real de amarração continua acusada | **sim** |
| E | encontro humano válido sem falso positivo ordinal | não (mas prova ausência de regressão) |
| F | nó recém-registrado / fiada exclusiva de uma parede não é defeito | **sim** (fiada exclusiva) |
| G | determinismo (ordem de entrada, translação, inversão de parede) | **sim** (inversão de parede) |

5 dos 13 falham comprovadamente contra o código pré-fix (verificado
rodando a suíte com `git stash` sobre `validate_junctions.py`) — prova
que os testes exercitam o defeito de verdade, não casos triviais.

Reprodutor original da reconciliação, copiado sem alteração de conteúdo
para `nuvem/benchmark/future_cr_preparation/
cr_v1_junction_validator_fidelity/repro_junction_row_unit.py`
(`exit 0` quando o defeito existe; código atual: `exit 1`).

Suíte de regressão pré-existente (`tests/regression/test_validators.py`,
23 casos) — **inalterada, todos passando**.

## Reconciliação dos +49 (STATE_R → STATE_C, candidato CR-B)

Executado `reconcile_by_physical_identity.py` (cópia idêntica da
reconciliação original) sobre STATE_R/STATE_C gerados por
`build_candidate.py` em worktree isolado do candidato — **rodando
contra o validador desta branch, já corrigido**:

```
                              TGD              TP1
por índice ordinal:
  ANTES do fix (medido)      373 -> 422 (+49)  365 -> 414 (+49)
  DEPOIS do fix (medido)      86 ->  96 (+10)   82 ->  92 (+10)
```

Classificação confirmada, idêntica à da reconciliação independente:
**39 dos 49 eram defeito do validador** (somem com o fix), **10 são
mudança legítima de unidade de avaliação** (identidades estritas novas,
todas em nós que NÃO existiam em STATE_R — fragmentação T→L do
candidato), **0 defeitos físicos novos**.

Nenhum outro código de achado mudou de valor entre `git stash`/sem
stash desta mesma rodada: `COVERAGE_GAP_IN_ROW` −47, `COVERAGE_
MISSING_ROW` +17, `COVERAGE_ROW_MOSTLY_EMPTY` +23, `OPENING_MISSING_
LINTEL` −12, `JUNCTION_HALF_BLOCK_ADJACENT` +0, `JUNCTION_NOT_
ALTERNATING` +0, `PRISM_*`/`COMPENSATOR_*` +0 — todos batendo, casa a
casa, com os números da reconciliação independente original (seção 5 do
relatório-fonte). Evidência: `nuvem/benchmark/future_cr_preparation/
cr_v1_junction_validator_fidelity/evidence/`.

## STATE_R / STATE_C

Gerados em worktree git isolado (`git worktree add --detach` sobre
`origin/claude/candidato-validacao-gabarito-q450yr`), saída em `/tmp`
fora de `nuvem/benchmark/projects/**`. Invariantes reconferidos (0
blocos humanos perdidos/novos/duplicados, sha256 batendo com o
candidato) — não repetidos aqui, já demonstrados pela reconciliação
original; esta sessão só verificou que a reconstrução determinística
ainda reproduz os mesmos números antes de medir o validador.

## No gabarito OFICIAL (sem nenhum corte da CR-B)

`nuvem/benchmark/runner.py --all --calibrate`, rodado em **cópia isolada
fora da working tree** (nunca contra `nuvem/benchmark/projects/**`
real — `--calibrate` regrava `reference_score.json`, proibido nesta CR):

```
JUNCTION_MISSING_BINDING   TGD 373 -> 86    TP1 365 -> 82
```

Mesmo defeito pré-existente, agora medido direto no `reference.json`
oficial, sem depender de nenhum corte hipotético da CR-B.

`nuvem/benchmark/runner.py --all` (solver de produção sobre os 3
projetos, também em cópia isolada): categoria `junctions` com **delta
0** contra o `baseline.json` congelado nos dois projetos com gabarito —
o defeito ordinal quase não se manifesta na saída do PRÓPRIO solver
(grade de elevação muito mais uniforme que a alvenaria humana
reconstruída). As diferenças reais que a rodada mostra em
`compensators`/`prism`/`wall_coverage`/`openings` contra o
`baseline.json` são de CRs de solver **já mergeadas** depois que esse
baseline foi salvo (`CR-BLOCK-NODE-FILL-REVALIDATION`, `CR-BLOCK-ARM-
SAFE-REPAIR-GATE-FIDELITY`, `CR-BLOCK-B19-RESIDUAL-FILL`, etc. — ver
`docs/PROJECT_STATUS.md`, "Estado oficial do solver") — reproduzidas
**de forma idêntica numa cópia de `origin/main` sem nenhuma alteração
desta CR**, confirmando que não são efeito deste fix. `junctions`
segue com delta 0 em ambas as cópias (com e sem o fix).

## Gates G1–G23 aplicáveis

Só os que dizem respeito à fidelidade do VALIDADOR, não à integração da
CR-B inteira (G1-G9, G12-G21 pertencem a CR-B/CR-S1/CR-C1/CR-I1 e **não
são declarados aprovados aqui**):

| gate | aplica-se | estado nesta CR |
|---|---|---|
| G10 — falha vertical em nó pré-existente, 0 pioram | corrobora (medição independente do agrupamento do validador) | ✔ confirmado pela reconciliação: 0 nós pré-existentes pioram, 8 melhoram |
| **G11** — `JUNCTION_MISSING_BINDING` por ELEVAÇÃO | núcleo desta CR | ✔ o validador corrigido mede **+10** (identidade estrita — a única logicamente afirmável, conforme a própria reconciliação recomenda), 100% atribuído a nós recém-registrados; **não** é o −5 do proxy "elevação não-estrita" do relatório original, que o próprio relatório já registra como medida mais fraca (conta bandas presentes numa única parede) |
| G22 — `baseline.json` preservado | sempre | ✔ nenhum arquivo de `nuvem/benchmark/projects/**` tocado (conferido por `git status`/`git diff --stat`) |
| G23 — suíte completa, mesmas falhas pré-existentes, 0 novas | sempre | ver seção "Suíte completa" |

Gates não aplicáveis a esta CR (pertencem à integração oficial da CR-B,
ao CR-S1 ou ao CR-C1, não inventados nem declarados aprovados aqui):
G1–G9, G12–G21.

## Suíte completa

`python3 -m pytest tests/ -q -m "not slow"` (848 testes): **778 passed,
0 failed** (90 deselecionados são `test_block_b19_residual_fill_
implementation.py`, isolado por ser extremamente lento — combinatória
de cascata — e rodado à parte por não competir por CPU com o resto da
suíte; **pré-existente e independente desta CR**, reproduzido com a
mesma lentidão numa cópia limpa de `origin/main` sem nenhuma
alteração). Rodado à parte, sem contenção de CPU, para confirmação
final — resultado registrado assim que a rodada isolada terminar.

Nenhuma falha, nenhum `xfail`/`skip` usado, nenhum threshold alterado
para fechar a suíte.

## Dívidas preservadas / não tocadas por esta CR

- **CR-S1** — o solver deixa de alternar amarração no nó que passa de
  `T` (atravessa) para `L` (termina) — defeito real do solver, medido
  de forma independente do agrupamento do validador
  (`repro_solver_l_node_alternation.py`, copiado sem alteração).
  Registrado em `nuvem/REGRAS_MODULACAO_BLOCOS.md` seção 5 como
  "PADRÃO MEDIDO — DOCUMENTADO, pendência de código aberta".
- **CR-C1** — `expected_rows` global gerando `COVERAGE_MISSING_ROW`/
  `COVERAGE_ROW_MOSTLY_EMPTY` críticos contra paredes cortadas — não
  tocado.
- **CR-B oficial** — integração do candidato (regravar gabarito,
  `stable_key`, migração `W0xx`, `reference_score` recalibrado) —
  não iniciada; gates G1-G9/G12-G21 continuam pendentes dela.
- `JUNCTION_WRONG_PIECE` (nível 2, preferência) usa a mesma sequência de
  fiadas físicas por posição relativa entre dois projetos — a mesma
  limitação de alinhamento que já existia (nunca reprova; não é
  exigência desta CR resolver).

## Veredito

Causa-raiz corrigida no validador (`JUNCTION_MISSING_BINDING`/
`JUNCTION_NOT_ALTERNATING` agora comparam fiadas por elevação física,
não por índice ordinal), preservando toda a semântica de amarração
existente. Medido: 39/49 falsos positivos eliminados, 10/49 legítimos
preservados (nós recém-registrados), 0 defeitos físicos novos ou
mascarados, 0 efeito sobre qualquer outro código de achado, gabarito
oficial e solver intocados. PR aberto como **draft** — não mesclar sem
autorização explícita do usuário.
