# Laboratório do CROSS-AUDIT FINAL do `CR-BLOCK-DETERMINISM`

CONTA 3. Relatório: `docs/BLOCK_DETERMINISM_FINAL_CROSS_AUDIT.md`.

**Contrato desta pasta:** só LEITURA do motor e da infraestrutura de
benchmark. Nenhuma linha de produção alterada, nenhum `baseline.json`
tocado, nenhum `out_*.json` de outra pasta de diagnóstico sobrescrito,
nenhuma branch da CONTA 1 modificada.

Escrita do zero — **não** reusa `lib_det` / `lib_final` / `lib_cross` das
auditorias anteriores. As camadas de fingerprint, as variantes e a
classificação de validade nascem aqui de novo, porque o pedido é prova
INDEPENDENTE.

## Bibliotecas

| arquivo | o que é |
|---|---|
| `lib_xa.py` | roda o solver real via `benchmark/solver_bridge`; identidade GEOMÉTRICA (nunca `wall_idx`); 10 camadas de fingerprint, com a peça identificada pelo CONJUNTO DE CÉLULAS em coordenadas de mundo |
| `variants_xa.py` | 31 entradas por projeto: 21 de PERMUTAÇÃO + 10 de REVERSÃO de endpoint, cada reversão nas duas versões (`_naive` = `t' = L_input − t`, `_geometric` = `t' = L_esticado − t`) |

## Scripts

| script | responde a |
|---|---|
| `run_xa_variants.py <projeto>` | itens 5 e 6 — bateria de determinismo, fingerprints por camada |
| `run_xa_validity.py [projetos]` | item 7 — cada variante é `VALID_METAMORPHIC_VARIANT` ou não, medido na PLANTA com tolerância de 0,05 cm |
| `run_xa_prism_diff.py <label> <projeto>` | itens 8 e 9 — uma linha por violação `PRISM_CONTINUOUS_JOINT`, com blocos, nó próximo e causa |
| `run_xa_nodefill.py [projeto]` | item 10 — instrumenta `_layout_internal_joint_positions_cm` em memória e prova que a junta nó/fill nunca entra na lista |
| `run_xa_order.py` | itens 18 e 19 — ordem oficial e `continuous_first`, testados sobre plantas sintéticas |

## Saídas

`out_xa_variants_<projeto>.json` (ponto `+FINAL`),
`out_xa_variants_CONTROLE_{MAIN,GRAFO}_<projeto>.json` (os dois pontos
anteriores, para provar que a bateria não é vazia),
`out_xa_validity.json`, `out_xa_prism_diff_{main,before,head}_*.json`,
`out_xa_nodefill_*.json`, `out_xa_order.json`,
`out_xa_three_point_measurements.json` (CR-BLOCK-01 + placement reasons +
validadores nos três pontos) e `out_xa_reference_corpus.{json,md}`.

## Os três pontos de medição

```
MAIN     21add6ec   origin/main - sem wall graph, sem finalizacao
+GRAFO   cb9ef99    MAIN + nuvem/core/engine/wall_pairing.py (wall graph canonico)
+FINAL   228d68af   +GRAFO + nuvem/core/engine/wall_stepper.py (esta CR)
```

Os pontos anteriores foram medidos em `git worktree` separados, sem
alterar a árvore de trabalho.
