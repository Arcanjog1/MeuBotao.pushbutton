# `diagnostics_2k` — verificação do `CR-2F-D` (determinismo + `W097`)

**SOMENTE LEITURA de `nuvem/core/**`.** Nenhum script daqui altera o motor.
O comportamento "antes" é obtido injetando **em memória** a passada 1
anterior do merge — mesma técnica das Etapas 2G, 2I e 2J.

Regra registrada: [`../../REGRAS_MODULACAO_BLOCOS.md`](../../REGRAS_MODULACAO_BLOCOS.md) §26.10.
Diagnóstico visual da `W097`: [`../diagnostics_2d/render_w097.py`](../diagnostics_2d/render_w097.py).

## Como rodar

```bash
pip install numpy matplotlib
python3 nuvem/benchmark/diagnostics_2k/run_a_census.py       # ~1 min
python3 nuvem/benchmark/diagnostics_2k/run_b_downstream.py   # ~7 min
```

> Ao redirecionar a saída, **não** use `| head` — o `SIGPIPE` mata o script
> antes de ele gravar o JSON. Redirecione para um arquivo.

## Arquivos

| script | mede | saída |
|---|---|---|
| `run_a_census.py` | assimetria do merge e da relação de duplicidade **completa**; censo do discriminador sobre as 57 remoções | `out_a_census.json` |
| `run_b_downstream.py` | 3 variantes da passada 1 × produção + 5 seeds; identidade da partição; runtime | `out_b_downstream.json`, `out_b_downstream.txt` |

`run_a_census.py` sai com código 0 somente se as duas assimetrias derem **0**.

## Resultado registrado (2026-09-01)

| | antes | depois |
|---|---|---|
| fingerprints distintos das **paredes** (6 ordens) | **3** | **1** |
| fingerprints distintos do merge (6 ordens) | 6 | **1** |
| pares aceitos / paredes | 201 / 144 | 201 / **145** |
| cobertura | 86/97 | **87/97** |
| eixos / aberturas / monitoradas / espúrias | 96 / 91-91 / 7-7 / 4 | 96 / 91-91 / 7-7 / 4 |
| `W097` | ausente | **recuperada** |
| assimetria merge | 393 (primitiva antiga) | **0** / 281.162 |
| assimetria dedup (relação completa) | — | **0** / 1.646 |
| remoções acima de 2 cm no trecho comum | **1** (a da `W097`, 3,7952 cm) | pior legítima: **1,5306 cm** |
| runtime da passada 1 | 9,15 s | **8,67 s (−5,2 %)** |

### Atribuição das duas correções

A tabela `ANTES` do `out_b_downstream.txt` reverte **apenas a passada 1**;
as canonizações de `_merge_collinear_cluster` continuam ativas. Ela mostra
que, sozinhas, já bastam para o **fingerprint das paredes** (1 em 6 ordens),
enquanto o **fingerprint do merge** só colapsa com a ordem canônica das
bases (6 → 1). As duas correções são necessárias: a primeira estabiliza a
partição, a segunda estabiliza a geometria reconstruída dentro de cada
cluster.
