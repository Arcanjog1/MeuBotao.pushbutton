# CHECKPOINT — série CR-N1 (b/c/e/f) — 2026-09-09

> Checkpoint **reproduzível** do candidato. Nada aqui está na `main`.

## Estado

| item | valor |
|---|---|
| `main` | `08495d9` (**inalterada**) |
| branch candidata | `claude/sleepy-turing-rf4s7o` |
| **HEAD** | **`420dbcc`** |
| tag | `checkpoint/cr-n1f-420dbcc` |
| PR | [#31](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/31) — **draft**, não mesclado |
| PR anterior | [#30](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/30) — CR-N1, `626087b`, **draft** |
| Revit | **não iniciado** |
| arquivos oficiais | `input.json`, `reference.json`, `reference_score.json`, `baseline.json` **não regravados** |

## Testes

`pytest tests/ -q -n 4 --dist loadfile` → **1003 passed, 2 failed** (39min).

| | passed | failed |
|---|---|---|
| base conhecida | 921 | 2 |
| CR-N1 `626087b` | 930 | **5** |
| CR-N1b `67083b0` | 964 | 2 |
| **CR-N1c/e/f `420dbcc`** | **1003** | **2** |

As 2 falhas, de `tests/regression/test_benchmark_baselines.py` contra o
`baseline.json` antigo (refresh é CR própria):

| projeto | o que reprova | nível | origem |
|---|---|---|---|
| TGD | categoria `compensators` 52→66 | REGRESSÃO (não crítica) | esta série |
| TP1 | `JUNCTION_MISSING_BINDING` 8→9 | crítica | **anterior à `main`** (9 em `08495d9`, na N1 e aqui; baseline diz 8) |
| TP1 | `OPENING_BLOCK_INSIDE_DOOR` 0→7 | crítica | CR-N1 — **reclassificação**, ver seção 47.6 |

O TGD **deixou de reprovar por regressão crítica** (era
`JUNCTION_MISSING_BINDING` 24→40; a CR-N1c fechou).

## Deltas físicos — identidade física, `main` × candidato

| | `main` `08495d9` | **candidato `420dbcc`** |
|---|---|---|
| TGD identidades | 852 | **789** |
| TP1 identidades | 961 | **900** |
| TGD blocos | 11 749 | **11 837** |
| TP1 blocos | 19 572 | **19 647** |
| `POSITION_OVERLAP` TGD/TP1 | 6/1 | **0/0** |
| TGD `JUNCTION_MISSING_BINDING` (ocorr.) | 23 | **23** |
| TGD `COMPENSATOR_CONSECUTIVE` (ident.) | 101 | **75** |
| TP1 `COMPENSATOR_CONSECUTIVE` (ident.) | 200 | **171** |
| TGD `door_void` OBB | 1074 | **1038** |
| TP1 `door_void` OBB | 2094 | **2094** |
| TGD paredes vazias | 29 | 29 |
| TP1 paredes vazias | 0 | 0 |
| **TGD colisões do solver** | **1160** | **1197** ⚠ |
| **TP1 colisões do solver** | **14** | **0** ✔ |
| TGD `intersection_failures` | 200 | 200 |
| TP1 `intersection_failures` | 0 | 0 |

⚠ **TGD colisões +37 (+3,2%)** — declarado, não escondido. Não foi
possível separar por identidade física: o registro de `collisions` não
expõe os campos que a chave física exige. **Investigar antes de qualquer
uso do TGD no Revit.**

## Regressões corrigidas nesta série

1. **Encontro T sem nenhuma peça** (`CR-N1c`) — o ponto médio doava espaço
   a um vizinho com alcance `0,00cm`; a parede
   `W|-140.5,470.0|5.5,470.0|t14.0` perdia o `C04` que amarrava o T
   (58 → 41 blocos, 17 fiadas). `JUNCTION_MISSING_BINDING` 40 → 23.
2. **`POSITION_OVERLAP`** — 6/1 → **0/0**, preservado em toda a série.
3. **Dupla contagem da reserva de ponta** (`CR-N1b`) — duas paredes de
   69cm com `C09` no papel de peça de amarração de canto voltaram ao B34.
4. **Compensadores em sequência** (`CR-N1e`) — mesma composição,
   reordenada; `COMPENSATOR_CONSECUTIVE` −26 (TGD) e −29 (TP1).
5. **Desempenho** (`CR-N1f`) — 176,4s → **127,0s** no TGD, com conjunto
   de identidades **idêntico**.

## Decisões pendentes — do usuário

### Seção 41 — compensador × peça especial
Metade já aplicada (ordenação, `CR-N1e`). **Falta decidir** a metade
normativa: rebaixar `MAX_COMPENSATORS_PER_TRECHO` de teto a preferência,
com `COMPENSATOR_EXCESS_IN_RUN` mudando de régua junto. Alternativas 1/2/3
enumeradas na 41.5 (2 457 composições do trecho `TP1/W003`).

### Seção 42 — parede fora do módulo
`pier_cm_floored_to_module` **delimita** o uso ao caso em que o trecho
fecha (sobra garantida em `[4,70; 5,00)cm`). Nos 197,943cm o trecho **não
fecha** e a sobra seria 3,94cm. Ligar ali é **estender o contrato**, não
reusá-lo. **Decisão do usuário.**

### Seção 45/47 — nó cujo eixo cai dentro do vão
- 281 ocorrências = **49 identidades físicas**; `CROSSES_JAMB` e
  `INSIDE_DOOR` são **o mesmo defeito** classificado por razão.
- Pelo **OBB** (a régua da regra absoluta), **68% do TP1 é
  `STANDARD_FILL`**, não peça de nó — a 45.3 valia só para o validador.
- **Candidata NÃO deve ser implementada**: deixa 92,6% das violações de
  OBB de pé e cria **68 `intersection_failures`** novos no TP1.
- **Decisão do usuário**: reconciliar as duas réguas (OBB × validador) ou
  tratá-las como contratos separados.

## Dívidas que continuam abertas

- Seção 43.5 — nó de meio com peça centrada (4 paredes de 124cm).
- Seção 42.6 — fusão reserva-de-ponta × reserva-de-midspan (segmento
  negativo); ganho seria de relatório.
- Refresh de `baseline.json` — CR própria.
- `JUNCTION_HALF_BLOCK_ADJACENT` e `door_void_violations` ×
  `OPENING_BLOCK_INSIDE_DOOR` — suspeita de erro de **avaliação**.
- C2/G16 e CR-B — preservados, não tocados.
- `CR-PERF-1` — re-solve por escopo (ataca os 22 rebuilds em si).
