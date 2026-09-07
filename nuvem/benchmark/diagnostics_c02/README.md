# Diagnósticos — `CR-BLOCK-ROOM-CHECK-ROBUSTNESS` (C02), MODO A

Preparação **somente leitura** do C02. **Zero alteração de produção**: toda
medição é feita por *monkey-patch em memória* que **chama a função real** e
apenas registra — nenhuma reimplementação do solver, nenhum arquivo de
`nuvem/core/**` tocado.

Base: `origin/main` @ `3ebcd9b63875f9114a3d6223aa648e5075e2d35b` (pós-PR #19).
O C04 (PR #20) **não** estava mergeado quando isto foi medido.

Relatório completo: [`docs/BLOCK_ROOM_CHECK_C02_PREPARATION.md`](../../../docs/BLOCK_ROOM_CHECK_C02_PREPARATION.md).

## Como reproduzir

Todos os scripts rodam a partir da raiz do repositório, em CPython comum
(os dublês de `tests/revit_stubs.py` fazem a geometria):

```bash
python3 nuvem/benchmark/diagnostics_c02/tools_c02_instrument.py   # X + T: toda avaliação de room check
python3 nuvem/benchmark/diagnostics_c02/tools_c02_lcorner.py      # L_CORNER (teto de 34cm)
python3 nuvem/benchmark/diagnostics_c02/tools_c02_origin.py       # de ONDE vem o déficit
python3 nuvem/benchmark/diagnostics_c02/minimal_reproducers.py    # sintéticos + invariância

# comparação de estratégias — UMA variante por processo:
for v in baseline x005 x030 xt005; do
  python3 nuvem/benchmark/diagnostics_c02/tools_c02_strategy.py $v
done
```

Os scripts gravam os JSON brutos no diretório de onde rodam; os arquivos
versionados aqui são a versão **consolidada e enxuta** (sem dumps grandes).

## O que cada arquivo responde

| arquivo | pergunta |
|---|---|
| `room_distribution.json` | Quantas avaliações, quantas **identidades físicas**, qual a folga medida e de onde vem o déficit — separado por X / T / L. |
| `first_divergence.json` | Exatamente **em que nó** e por **quantos centímetros** o solver deixa de escolher B54, e quantos B54 uma tolerância de 0,05cm recuperaria **como peça final**. |
| `candidate_strategy_comparison.json` | `baseline` × `x005` × `x030` × `xt005`, medido em peças finais por identidade geométrica. |
| `minimal_reproducers.py` / `minimal_reproducers_output.json` | Escada de folgas (28,10 → 0,00cm) e as cinco transformações de invariância, em planta sintética independente do corpus. |
| `human_reference_check.json` | O humano usa B54 nos nós que a tolerância recuperaria? |

## As duas armadilhas de contagem

1. **Avaliação ≠ peça.** O solver refaz a resolução dos nós a cada
   rebuild/banda, então o mesmo nó é medido centenas de vezes. As 2024
   avaliações do TGD são **10 nós**; as 1350 do TP1 são **8**. Os JSON
   sempre trazem `evaluations` e `unique_*` lado a lado — só o segundo
   vira peça no modelo.
2. **Identidade tem de ser geométrica.** Toda chave usada aqui é
   coordenada em cm (nó, e parede pelo par ordenado de extremidades) —
   nunca `wall_idx`, `block_id` ou ordem de lista, que mudam entre
   execuções e entre variantes.
