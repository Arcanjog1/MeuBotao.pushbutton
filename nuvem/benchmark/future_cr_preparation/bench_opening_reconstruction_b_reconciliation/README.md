# CR-B — RECONCILIAÇÃO INDEPENDENTE (diagnóstico)

> **Nada aqui é gabarito, regra ou produção.** Só reprodutores e
> evidência da revisão independente do candidato da CR-B.
> `nuvem/benchmark/projects/**`, `nuvem/core/**`,
> `nuvem/benchmark/validators/**`, `nuvem/REGRAS_MODULACAO_BLOCOS.md`,
> `docs/PROJECT_STATUS.md` e `tests/**` estão **intocados**.

| item | valor |
|---|---|
| base | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` (= `origin/main`) |
| candidato revisado | `claude/candidato-validacao-gabarito-q450yr` @ `56409334a7b273d0e81a13d8cc916ffe0e214654` |
| relatório | `docs/BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_RECONCILIATION.md` |

## Arquivos

| arquivo | o que faz |
|---|---|
| `repro_junction_row_unit.py` | **reprodutor mínimo** (sintético, 2 paredes): `JUNCTION_MISSING_BINDING` agrupa as fiadas do nó pelo **índice ordinal**, não pela cota — uma meia-fiada cortada numa das paredes produz achados falsos sem que nada mude de lugar. **CR-V1.** |
| `repro_solver_l_node_alternation.py` | **reprodutor** no corpus real: no nó `(338,52; 187,05)` (TGD) / `(8017,26; 1289,95)` (TP1) o solver **alterna** com a entrada antiga e **para de alternar** quando a parede passa a terminar no nó. A pessoa alterna nas duas topologias. **CR-S1.** |
| `reconcile_by_physical_identity.py` | reconcilia todos os códigos entre STATE_R→STATE_C (gabarito) e IN_R→IN_C (solver) por **coordenada de mundo + elevação**; reconta `MISSING_BINDING` em três unidades; mede `COVERAGE_GAP_IN_ROW` em **centímetros de união física**; reconcilia `POSITION_OVERLAP` pela coordenada dos blocos |
| `evidence/reconciliation_run.txt` | saída conferida desta sessão |
| `evidence/reconciliation_physical_identity.json` | a mesma coisa, estruturada |
| `evidence/documental_debt.json` | os dois relatórios de revisão independente: **existem**, em que commit, em que branch, e que **nunca foram mesclados na `main`** |

## Como reproduzir

```bash
export CR_B_OUT=/tmp/cr_b_candidate
cd ../bench_opening_reconstruction_b_candidate && python3 build_candidate.py && cd -
python3 repro_junction_row_unit.py
python3 repro_solver_l_node_alternation.py     # roda o solver de producao se faltar
python3 reconcile_by_physical_identity.py
```

`build_candidate.py` é determinístico: os 8 `sha256` foram reconferidos
nesta sessão contra os declarados pelo candidato (4º processo
independente).

## Por que identidade FÍSICA

`W0xx` é id **sequencial**: 53 de 86 (TGD) e 52 de 85 (TP1) paredes que
não mudam nada recebem outro id no candidato. E o índice de fiada
`row["row"]` é a posição na pilha **daquela parede** — 184 blocos por
projeto mudam de índice sem mudar de cota. Qualquer reconciliação que use
um dos dois compara coisas diferentes.

A chave usada aqui é sempre **coordenada de mundo + `elevation_cm`**, e
onde o achado não emite coordenada (`COMPENSATOR_AVOIDABLE`,
`COVERAGE_MISSING_ROW`, `COVERAGE_ROW_MOSTLY_EMPTY`,
`OPENING_MISSING_*`) a saída marca a chave como **FRACA** em vez de
fingir que reconciliou.
