# Scripts diagnósticos — revisão do C04 e preparação das próximas CRs

Ferramentas de **diagnóstico**, não de produção. Não fazem parte do botão
(o loader só baixa `nuvem/core/**`). Rodam em CPython comum, fora do
Revit, com os dublês de `tests/revit_stubs.py`.

**Nenhum deles escreve em `baseline.json`, `reference.json` ou
`input.json`.** `probe_state.py` usa caminho próprio (`write_files=False`
por construção — nunca chama `runner.run_project`).

Copiar para a raiz do worktree antes de rodar (usam
`sys.path.insert(0, dir_do_script)`).

| script | o que faz |
|---|---|
| `probe_state.py` | roda um projeto e emite fingerprint físico + `counts_by_code` + `critical_by_code` + **identidade geométrica** de cada achado. Uso: `python3 probe_state.py <project_id> <out.json>` |
| `compare_states.py` | compara dois/três estados por identidade **normalizada** (remove o rótulo sequencial `W…-R…-B…`, que muda quando uma peça entra antes na fiada e produz falsos "novos"). Uso: `python3 compare_states.py <tgd\|tp1\|piloto> <dir_dos_json>` |
| `classify_exposure.py` | para cada achado novo, diz se a região estava **vazia** em STATE_A (exposição) ou **já tinha peça** (recomposição). É como se testa a etiqueta `EXPECTED_EXPOSURE` em vez de aceitá-la. |
| `trace_c04_guard.py` | instrumenta `_layout_fitted_to_physical_span` **de produção** e registra todo disparo da guarda do C04: `lo`/`hi`, excesso, layout antes/depois, tipo de fronteira (`right_opening`). |
| `probe_c04_guard_fn.py` | 35 sondas de fronteira contra a função real da guarda (trecho exato, limites 0,05/0,30, jamba no início/fim, translação, trecho pequeno demais). |
| `trace_x_room_check.py` | instrumenta `_x_intersection_centered_candidate` e emite a distribuição real de folga (`room_cm`) nos nós X — base da evidência do C02 (27,997 / 27,98 / 27,99 contra teto de 28,00). |
| `profile_arm.py` | `cProfile` cumulativo do solver — base da SPEC de performance do ARM. |

## Atenção ao instrumentar

O motor é carregado como `script_under_test` (via
`solver_bridge.engine()`), mas o dono real dos globals dos call sites é
`sys.modules["core.engine.wall_stepper"]`. **Fazer monkeypatch no módulo
errado não tem efeito nenhum e passa despercebido** — verificar sempre:

```python
ws = sys.modules["core.engine.wall_stepper"]
assert ws._solve_repair_subsegments.__globals__ is ws.__dict__
```

Relatórios que usam estes scripts:
`docs/C04_INDEPENDENT_FINAL_REVIEW.md`,
`docs/FUTURE_BLOCK_CR_PREPARATION.md`.
