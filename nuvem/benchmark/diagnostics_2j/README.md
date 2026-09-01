# `diagnostics_2j` — verificação do `CR-2F-A` (`MERGE_RELATION_ASYMMETRY`)

**SOMENTE LEITURA de `nuvem/core/**`.** Nenhum script deste diretório altera
o motor. O comportamento "antes" é obtido injetando **em memória** a relação
assimétrica de volta nos quatro sítios (as primitivas antigas continuam no
motor, intactas e em uso pelos diagnósticos) — mesma técnica das Etapas 2G e
2I.

Regra registrada: [`../../REGRAS_MODULACAO_BLOCOS.md`](../../REGRAS_MODULACAO_BLOCOS.md) §26.9.

## Escopo do `CR-2F-A`

```
relação de compatibilidade  →  compat(A,B) == compat(B,A)
```

Estratégia `T2`/`MAX`: `max(d(A,B), d(B,A)) <= tolerância`, nos quatro
sítios de produção que criam ou removem geometria com essa relação.

**O `CR-2F-A` NÃO entrega invariância do merge à ordem da lista.** A relação
continua não transitiva e o agrupamento continua sendo estrela — isso é o
`CR-2F-D`. Ver §26.9.4.

## Como rodar

```bash
pip install numpy pytest
python3 nuvem/benchmark/diagnostics_2j/run_a_census.py       # ~2 min
python3 nuvem/benchmark/diagnostics_2j/run_b_downstream.py   # ~4 min
```

> Ao redirecionar a saída, **não** use `| head` — o `SIGPIPE` mata o script
> antes de ele gravar o JSON. Redirecione para um arquivo.

## Arquivos

| script | mede | saída |
|---|---|---|
| `run_a_census.py` | censo de assimetria do veredito, antes × depois, no merge e no `deduplicate_walls` | `out_a_census.json` |
| `run_b_downstream.py` | pipeline real (merge incluído) em produção + 5 permutações, e o runtime da passada afetada | `out_b_downstream.json` |

`run_a_census.py` sai com código 0 somente se o censo pós-correção der
**0 violações** nos dois lugares.

## Resultado registrado (2026-09-01)

| | antes | depois |
|---|---|---|
| vereditos dependentes da direção — merge | **393** | **0** |
| vereditos dependentes da direção — `deduplicate_walls` | **1** | **0** |
| pior `\|d(A,B) − d(B,A)\|` | 182,9642 cm | — |
| cobertura nas 5 seeds | 84–86 | **86 em todas** |
| eixos corretos nas 5 seeds | 94–96 | **96 em todas** |
| 7 monitoradas nas 5 seeds | 5–7 | **7/7 em todas** |
| aberturas nas 5 seeds | 91/91 | **91/91** |
| custo de `merge_collinear_fragments` | 10,13 s | **9,48 s (−6,4 %)** |
