# diagnostics_residual_atlas — CR-BLOCK-SOLVER-RESIDUAL-ROOT-CAUSE-ATLAS

Laboratório **somente diagnóstico** (nenhum script escreve em
`nuvem/core/**` nem em `nuvem/benchmark/projects/*` — `baseline.json`,
`reference.json`, `reference_score.json`, `score.json` intactos). Roda o
solver REAL via `benchmark/solver_bridge.py` (stubs de `tests/revit_stubs.py`)
e mede a geometria que sai dele. Instrumentação só por monkeypatch em
memória, dentro do processo do script.

Relatório: `docs/BLOCK_SOLVER_RESIDUAL_ROOT_CAUSE_ATLAS.md`. Saída
machine-readable: `root_cause_atlas.json`.

```bash
export ATLAS_OUT_DIR=/tmp/atlas_out      # dumps grandes (result/findings/run.pkl) ficam FORA do repo
python3 nuvem/benchmark/diagnostics_residual_atlas/run_state_current.py     # STATE_CURRENT (solver + validadores)
python3 nuvem/benchmark/diagnostics_residual_atlas/inventory.py             # inventario fisico + composicoes solver x humano
python3 nuvem/benchmark/diagnostics_residual_atlas/prism_signatures.py
python3 nuvem/benchmark/diagnostics_residual_atlas/compensator_chains.py
python3 nuvem/benchmark/diagnostics_residual_atlas/coverage_decomposition.py
python3 nuvem/benchmark/diagnostics_residual_atlas/openings_decomposition.py
python3 nuvem/benchmark/diagnostics_residual_atlas/first_divergence.py      # + node_parity.json
python3 nuvem/benchmark/diagnostics_residual_atlas/cluster_assign.py        # clusters causais -> cluster_summary.json
python3 nuvem/benchmark/diagnostics_residual_atlas/run_reproducers.py       # reprodutores minimos R1..R6
python3 nuvem/benchmark/diagnostics_residual_atlas/run_invariance.py        # permutacao / inversao / espelho / rotacao
python3 nuvem/benchmark/diagnostics_residual_atlas/run_determinism.py       # PYTHONHASHSEED em processos novos
python3 nuvem/benchmark/diagnostics_residual_atlas/run_performance.py       # tempo por estagio (wrappers)
python3 nuvem/benchmark/diagnostics_residual_atlas/run_ablation.py --ablation fit_tol_0_3|x_room_slack|no_arm
python3 nuvem/benchmark/diagnostics_residual_atlas/probe_opening_repair.py torre_easy_lo_r00_tp1 35
```

`atlas_lib.py` — carga do motor, `Bundle` (run em cache, contexto por
parede, casamento `wall_idx`↔`W###` pela chave geométrica, união de todas
as paredes humanas colineares para fragmentos), projeção da composição
humana no eixo do solver (sentido invertido tratado), fingerprint físico.

`out/` — só resumos pequenos (JSON de agregados, assinaturas, cadeias,
paridade por nó, composições de paredes-chave). Os dumps completos
(`result.json`, `findings.json`, `run.pkl`, `compositions/`) não são
versionados.

Convenções: `W###` é o id do `result.json` (`model.assign_ids` reordena
geometricamente — no TGD `W###` ≠ `wall_idx+1`); `t` em cm ao longo do eixo
do solver a partir de `start_cm`; peças marcadas `*` são da parede vizinha
(peça de nó) projetadas pela largura; fiada `r00` = `course_index 0` =
família A.
