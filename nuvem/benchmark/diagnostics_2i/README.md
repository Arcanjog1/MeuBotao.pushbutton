# `diagnostics_2i` — laboratório do `CR-2F-E` (`CENTERLINE_ARGUMENT_ASYMMETRY`)

**SOMENTE LEITURA de `nuvem/core/**`.** Nenhum arquivo do motor é alterado
por esta etapa. As alternativas de eixo são definidas em `lib2i.py` e
injetadas em memória dentro do `find_wall_pairs` **real**
(`lib2i.patched`, pelo dict de globais de `core.engine.wall_pairing`),
exatamente como a Etapa 2G fez com os predicados do par.

Relatório e plano: [`../PLANO_ETAPA_2I_CR_2F_E.md`](../PLANO_ETAPA_2I_CR_2F_E.md)

## Escopo

`find_wall_pairs` fica **congelado** (predicados `CR-2F-B`, desempate
`CR-2F-C`). O alvo é só:

```
par geométrico já aceito  →  eixo da parede
```

## Vocabulário

| | |
|---|---|
| **ARGUMENT ORDER** | `create_centerline(A,B)` × `create_centerline(B,A)` |
| **ENDPOINT DIRECTION** | `Line(p0,p1)` × `Line(p1,p0)` da mesma face |

São invariâncias **diferentes** e são medidas separadamente.

## Estratégias

| | nome | |
|---|---|---|
| `cur` | produção atual | baseline |
| `S1` | `CANONICAL_ARGUMENT_ORDER` | eliminada — piora a centralização 7× |
| `S2` | `LONGEST_REFERENCE` | eliminada — idem, e falha `H2` |
| `S3` | `SYMMETRIC_BISECTOR` | suplente |
| `S4` | `MUTUAL_OVERLAP_CENTERLINE` | eliminada — muda 86/152 pares unívocos |
| `S5` | `ENDPOINT_AVERAGING` | eliminada — idem |
| `S6` | `SYMMETRIC_UNION_CLAMPED` | suplente (resultado idêntico ao `S3`) |
| **`S7`** | **`SYMMETRIC_LONGEST_SPAN`** | **vencedora** |
| `S8` | `SYMMETRIC_BANDED_SPAN` | eliminada |

## Como rodar

```bash
pip install numpy pytest          # numpy só é usado pelo lib2g importado
python3 nuvem/benchmark/diagnostics_2i/run_a_baseline_census.py   # ~1 min
python3 nuvem/benchmark/diagnostics_2i/run_b_invariance.py        # ~1 min
python3 nuvem/benchmark/diagnostics_2i/run_c_rootcause.py         # ~30 s
python3 nuvem/benchmark/diagnostics_2i/run_d_downstream.py        # ~7 min
python3 nuvem/benchmark/diagnostics_2i/run_e_finalists.py         # ~30 s
python3 nuvem/benchmark/diagnostics_2i/run_f_gates.py             # ~1 min  (lê out_d/out_e)
```

`run_f_gates.py` depende de `out_d_downstream.json` e `out_e_finalists.json`.

> Ao redirecionar a saída, **não** use `| head` — o `SIGPIPE` mata o script
> antes de ele gravar o JSON. Redirecione para um arquivo.

## Arquivos

| script | item do pedido | saída |
|---|---|---|
| `lib2i.py` | biblioteca: estratégias, `patched`, espião, métricas | — |
| `run_a_baseline_census.py` | 0 (baseline), 5 (caso mínimo), 6 (censo) | `out_a_baseline_census.json` |
| `run_b_invariance.py` | 3 (dissecação operação a operação), 7 (as duas invariâncias) | `out_b_invariance.json` |
| `run_c_rootcause.py` | 3 (ablação: qual mecanismo responde por quais divergências) | `out_c_rootcause.json` |
| `run_d_downstream.py` | 8 (camada por camada), 9, 11 (benchmark humano) | `out_d_downstream.json` |
| `run_e_finalists.py` | 9, 10 (correção geométrica, não só simetria) | `out_e_finalists.json` |
| `run_f_gates.py` | 12 (gates `H1`–`H11`), atribuição causal, runtime | `out_f_gates.json` |

## Métricas novas desta etapa

- **`excess_len_cm`** — comprimento de eixo que não cai sobre nenhuma parede
  do gabarito. A cobertura do benchmark mede só do lado do gabarito e por
  isso **não enxerga eixo que dispara**.
- **`axis_centering_error_cm`** — envelopa `_axis_offset_error_ft`, a
  autoverificação que o próprio motor já roda. É o critério que elimina as
  ordenações canônicas: elas tornam o resultado determinístico **piorando**
  a geometria (1,14 cm → 21,33 cm no pior caso).

A referência humana é lida **apenas para avaliar depois**. Nenhuma
estratégia tem acesso a ela.
