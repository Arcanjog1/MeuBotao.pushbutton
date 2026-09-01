# PROJECT_STATUS — Modulação Automática (pyRevit)

Estado do trabalho em curso. Atualizado em **2026-09-01**.

## CR em andamento

| | |
|---|---|
| CR | **CR-2F-D** — determinismo do merge + recuperação da `W097` |
| Branch | `claude/cr-2f-d-determinism-ewnru5` |
| Baseline | `c21a4297a6ff372358cbb81da5ca6a65f91a955b` (`main`, CR-2F-A aprovado) |
| Estado | **IMPLEMENTADO — parado antes do merge, aguardando autorização** |

## Resultado (produção + 5 seeds, `torre_easy_lo_r00_tgd`)

| métrica | baseline | CR-2F-D |
|---|---|---|
| fingerprints distintos das **paredes** | **3** | **1** ← gate |
| fingerprints distintos do merge | 6 | 1 |
| pares aceitos | 201 | 201 |
| paredes | 144 | **145** |
| cobertura | 86/97 | **87/97** |
| eixos corretos | 96 | 96 |
| aberturas | 91/91 | 91/91 |
| monitoradas | 7/7 | 7/7 |
| espúrias | 4 | 4 |
| `W097` | ausente | **recuperada** (y ≈ 815,049) |
| remoções no `deduplicate_walls` | 57 | 56 |

Ausentes: `W004`, `W005`, `W006`, `W007`, `W025`, `W026`, `W046`, `W047`,
`W084`, `W085` — as mesmas de antes, sem a `W097`, sem perda nova.

## Suítes

| | |
|---|---|
| `tests/test_script.py` | **256 passed** (245 antigos + 11 novos) |
| `tests/regression` | **113 passed** |
| 11 invariantes anteriores | preservados, sem edição |
| `solver_decision_fingerprint` | `c74c9c1a…a316` — inalterado |
| assimetria merge | **0** / 281.162 pares |
| assimetria dedup (relação completa) | **0** / 1.646 candidatos |

## O que mudou no motor

- `nuvem/core/engine/geometry.py`
  - `merge_collinear_fragments` — base da passada 1 escolhida pela geometria
    (mais longa primeiro, desempate `_line_span_key`) + varredura `taken`;
  - `_merge_collinear_cluster` — membros em ordem canônica e sentido da
    direção de referência canônico;
  - `_pair_symmetric_axis_gap_ft_cached` / `symmetric_axis_gap_ft` — novos.
- `nuvem/core/engine/wall_pairing.py`
  - `deduplicate_walls` — novo critério em **conjunção** com o do CR-2F-A;
    desempate do representante por `_line_span_key`.
- `tests/test_script.py` — `INV-DET-001..007`, `INV-DEDUP-D-001..004`.
- `nuvem/REGRAS_MODULACAO_BLOCOS.md` — §26.10 (inclui a correção de
  atribuição de §26.8.7.8/§26.8.8.4 e o gate `H6'` de volta a 87/97).
- `nuvem/benchmark/diagnostics_2k/` — censo e bateria (laboratório).
- `nuvem/benchmark/diagnostics_2d/render_w097.py` + 2 PNG — diagnóstico
  visual da `W097`, aprovado pelo usuário antes da implementação.

**Não tocados**: `create_centerline`, `find_wall_pairs`,
`core/engine/tolerances.py`.

## Divergência gabarito × CAD registrada (`W097`)

```
CAD:            faces em y = 808,049 e 822,050  (14,000 cm)
eixo calculado: y = 815,049                      (centrado, correto)
reference.json: y = 817,048                      (faces 810,048 / 824,048)
```

Não existe segmento do CAD em 810,048 nem 824,048, e o eixo do gabarito
dista 5,001/8,999 cm das faces (deveria ser 7/7). **É PROIBIDO mover a
parede para satisfazer o gabarito** — ver REGRAS §26.10.6. Consequência
aceita: a `W097` conta como coberta mas não entra no `eixo_ok` (≤ 0,5 cm).

## Performance

Passada 1 do merge, 3 amostras cada (`diagnostics_2k/run_b_downstream.py`):

| variante | média |
|---|---|
| antes (ordem de entrada + `rest`) | 9,15 s |
| só a ordem canônica (sem a otimização) | 9,64 s |
| **produção** (ordem canônica + `taken`) | **8,67 s** (−5,2 %) |

Partição idêntica entre `rest` e `taken` nas 6 ordens (1.714 clusters).

## PENDENTE

- [ ] **Autorização do usuário para o merge na `main`. Nada foi mesclado.**
- [x] Bateria completa (3 variantes × produção + 5 seeds), censo de
      assimetria, 256 + 113 testes, fingerprint do solver — todos
      executados; resultados em `nuvem/benchmark/diagnostics_2k/`.

## Dívida conhecida (fora do escopo do CR-2F-D)

- Pareamento `(474, 2306)`: face de 155,61 cm × linha auxiliar de
  4.394,45 cm inclinada 1,1125° → eixo espúrio de 43,9 m. **Continua no
  resultado**, como uma das 4 espúrias. É problema de *pareamento*, sem CR
  atribuído.
- As 10 paredes ausentes acima — nenhuma perseguida, nenhuma recuperada.
- Possível deslocamento do `reference.json` em outras paredes além da
  `W097`; convém verificar antes de usar `eixo_ok` como métrica fina.
