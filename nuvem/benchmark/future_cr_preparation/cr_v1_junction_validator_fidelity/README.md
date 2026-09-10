# CR-V1 — VALIDADOR DE ENCONTROS POR ELEVAÇÃO FÍSICA — evidência reproduzível

> **Nada aqui é gabarito nem regra normativa.** Estes arquivos são
> reprodutores e evidência da CR-V1. Nenhum arquivo de
> `nuvem/benchmark/projects/**` (`reference.json`, `input.json`,
> `baseline.json`, `reference_score.json`, `evaluation_scope.json`) foi
> alterado por esta CR — conferido por `git diff --name-only` ao fim da
> sessão. O código de PRODUÇÃO alterado é só
> `nuvem/benchmark/validators/validate_junctions.py`.

Fonte diagnóstica original (reconciliação independente do contrato
CR-B): `docs/BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_RECONCILIATION.md`
(branch `claude/cr-b-reconciliacao-contrato-1byigr`, `14926fb`), seções
3 e 10.

## O que cada arquivo é

- `repro_junction_row_unit.py` — reprodutor mínimo determinístico do
  defeito (copiado, sem alteração de conteúdo, da reconciliação
  original). Duas paredes, um canto L, amarração alternada correta;
  acrescentar uma meia-fiada CORTADA a uma delas produzia 2 achados
  falsos antes do fix, 0 depois. `exit 0` quando o defeito ainda existe
  (código atual: `exit 1`, defeito corrigido).
- `repro_solver_l_node_alternation.py` — reprodutor do defeito
  SEPARADO do solver (nó `L` de ponta não alterna) usado só como
  referência de que este outro problema **não** foi tocado por esta CR
  (pertence à CR-S1). Não depende de `collect_nodes`/`validate_node`.
- `reconcile_by_physical_identity.py` — reconciliação STATE_R → STATE_C
  (candidato CR-B) por identidade física, nas três unidades de
  avaliação (ordinal / elevação física / estrita). Roda contra o
  `nuvem.benchmark.validators.validate_junctions` desta mesma árvore —
  ou seja, com o fix aplicado, a linha "por INDICE ORDINAL de fiada
  (validador de hoje)" já reflete o validador CORRIGIDO.
- `evidence/reconciliation_run_postfix.txt` — saída íntegra da rodada
  acima, com o fix aplicado.
- `evidence/reconciliation_physical_identity.json` — mesma rodada, em
  JSON.

## Como reproduzir

```bash
# 1. gerar STATE_R / STATE_C isolados (candidato CR-B, branch
#    claude/candidato-validacao-gabarito-q450yr, worktree separado)
export CR_B_OUT=/tmp/cr_v1_state
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate  # nesta branch so' existe no worktree do candidato
python3 build_candidate.py

# 2. reprodutor minimo (nesta pasta)
cd ../cr_v1_junction_validator_fidelity
python3 repro_junction_row_unit.py            # exit 1 = defeito corrigido

# 3. reconciliacao completa STATE_R -> STATE_C, com o validador desta arvore
python3 reconcile_by_physical_identity.py
```

## Resultado medido (STATE_R → STATE_C, TGD e TP1)

```
JUNCTION_MISSING_BINDING
  por indice ordinal (validador ANTES do fix): TGD +49 (373->422), TP1 +49 (365->414)
  por indice ordinal (validador DEPOIS do fix): TGD +10 (86->96),  TP1 +10 (82->92)
```

Bate exatamente com a classificação da reconciliação independente: dos
+49 antigos, **39 eram defeito do validador** (somem com o fix) e **10
são mudança legítima de unidade de avaliação** (nós recém-registrados
pela fragmentação T→L do candidato CR-B — `identidades estritas NOVAS:
10, dessas em nó que NÃO existia em STATE_R: 10`), **0 defeitos físicos
novos**.

Nenhum outro código de achado (`COVERAGE_*`, `PRISM_*`,
`COMPENSATOR_*`, `OPENING_*`, `JUNCTION_NOT_ALTERNATING`,
`JUNCTION_HALF_BLOCK_ADJACENT`) mudou de valor com este fix, nos dois
projetos — conferido linha a linha na tabela "GABARITO STATE_R ->
STATE_C" da evidência.

## No gabarito OFICIAL (sem CR-B, `reference.json` como está hoje)

```bash
py -3 nuvem/benchmark/runner.py --all --calibrate     # NAO rodar contra a arvore oficial:
                                                        # --calibrate REGRAVA reference_score.json.
                                                        # Rodar so' em copia isolada (fora do
                                                        # working tree oficial) para medir, nunca
                                                        # para gravar nesta CR.
```

Medido em cópia isolada (não gravado em `nuvem/benchmark/projects/**`):
`JUNCTION_MISSING_BINDING` TGD 373 → 86, TP1 365 → 82 — o mesmo defeito
pré-existente, independente de qualquer corte da CR-B. Recalibrar
`reference_score.json` de verdade fica para a CR de integração (gate
G21 do relatório de reconciliação: só depois de G1–G16 aprovados).
