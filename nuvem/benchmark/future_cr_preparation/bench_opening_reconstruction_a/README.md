# CR-BENCH-OPENING-RECONSTRUCTION-A — evidência reproduzível

> **Nada aqui é gabarito.** Estes arquivos são medição e reprodução da
> CR-A. Nenhum arquivo de `nuvem/benchmark/projects/**` foi alterado —
> todos os scripts rodam com `write_files=False` ou sobre cópia temporária.

Documento da CR: `docs/BENCH_OPENING_RECONSTRUCTION_A_IMPLEMENTATION.md`.

## Ordem de execução

```bash
# FASE 2 - reproduzir o defeito no codigo real (instrumentado, nao e' producao)
python3 repro_envelope.py                 # envelope x consenso x spread, por trecho
python3 repro_axis_gap.py                 # consenso x paredes MEDIDAS no mesmo eixo

# FASE 1 / FASE 5 - STATE_A e STATE_B
python3 state_detector.py STATE_A detector_state_a.json   # motor SEM a correcao
python3 state_detector.py STATE_B detector_state_b.json   # motor COM a correcao
python3 state_solver.py   STATE_A solver_state_a.json     # 3 projetos, solver inteiro
python3 state_solver.py   STATE_B solver_state_b.json

python3 compare_states.py detector_state_a.json detector_state_b.json
python3 compare_states.py --solver solver_state_a.json solver_state_b.json

# projecao (NAO aplicada) do efeito no solver, via CR-B
python3 projection_experiment.py
```

`state_*.py` e `repro_*.py` aceitam `REPO_ROOT` no ambiente; o padrão é o
diretório corrente.

## Arquivos

| arquivo | o que é |
|---|---|
| `repro_envelope.py` | replica o agrupamento do `STATE_A` linha a linha e mede, por trecho, **envelope × consenso × desacordo** |
| `repro_envelope.json` | saída do reproducer: os 94/92 trechos com envelope, consenso, desacordo e as bordas de **cada fiada** |
| `repro_axis_gap.py` | confronta o consenso com os trechos de parede **medidos** no mesmo eixo (`input.json` do TGD) |
| `state_detector.py` | roda o detector sobre a geometria real do gabarito humano dos 3 projetos |
| `state_solver.py` | roda o solver inteiro nos 3 projetos; identidade dos achados = `(code, wall, detail)`, **nunca** `block_id` |
| `compare_states.py` | STATE_A × STATE_B por identidade geométrica estável |
| `detector_state_a.json` / `detector_state_b.json` | saída do detector antes/depois |
| `detector_state_delta.json` | delta do detector (0 alargadas, 31 estreitadas por projeto) |
| `solver_state_delta.json` | delta do solver (**zero** em fingerprint, score e achados) |
| `projection_experiment.py` | mede, em cópia temporária, o efeito no solver **se** o gabarito fosse regerado (CR-B) |
| `projection_torre_easy_lo_r00_tp1.json` | resultado dessa projeção (`CROSS_JAMB 168 → 0`, críticos `485 → 327`, cobertura `+90/+14`) |

`solver_state_a.json` / `solver_state_b.json` (≈1,3MB cada, com a lista
completa de achados) **não** entram no repositório: `compare_states.py`
regenera o delta a partir deles, e `solver_state_delta.json` guarda o
resultado.
