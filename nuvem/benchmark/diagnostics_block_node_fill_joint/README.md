# Laboratório do `CR-BLOCK-NODE-FILL-JOINT`

Relatório: `docs/BLOCK_NODE_FILL_JOINT.md`.
Regras: `nuvem/REGRAS_MODULACAO_BLOCOS.md` §31.

**Contrato desta pasta:** só LEITURA do motor. Nenhum `baseline.json`,
`reference.json` ou `reference_score.json` é tocado; `run_measure.py` roda
sempre com `write_files=False`, então `projects/**/score.json` também não é
regravado. Nenhum `out_*.json` de outra pasta de diagnóstico é sobrescrito.

## Scripts

| script | responde a |
|---|---|
| `run_measure.py` | itens 7, 9, 10, 11, 12 do CR — códigos dos validadores, `solve_result`, censo de `placement_reason` e de peça, CR-BLOCK-01 (same-band / cross-band / compensadores), tempo por fase |
| `run_nf_trace.py` | item 3 — reproduz a evidência: instrumenta `_layout_internal_joint_positions_cm` em memória e lista as juntas de FRONTEIRA que coincidem com uma junta interna |
| `run_nf_performance.py` | item 16 — tempo por fase (grafo / solver / total), N repetições, mediana |

`lib_nf.py` reusa `diagnostics_block_prisma/metrics.py` (o instrumento do
próprio `CR-BLOCK-01`) em vez de reimplementar a taxonomia de junta.

## Pontos de medição

```
MAIN    21add6ec   origin/main
HEAD    2594f6ff   claude/cr-block-determinism-final-cross-audit (PR #7, auditoria)
DEPOIS  esta branch
```

MAIN e HEAD foram medidos em `git worktree` separados, sem alterar a árvore
de trabalho.

## Saídas

| arquivo | ponto |
|---|---|
| `out_nf_MAIN.json` | MAIN |
| `out_nf_before_HEAD.json` | HEAD (antes) |
| `out_nf_after.json` | DEPOIS |
| `out_nf_determinism_<projeto>.json` | bateria metamórfica (31 entradas/projeto) DEPOIS |
| `out_nf_performance_before_HEAD.json` / `out_nf_performance_after.json` | item 16 |
| `out_nf_reference_corpus_after.{json,md}` | item 15 |
| `out_nf_trace_<projeto>.json` | reprodução da evidência |
| `out_nf_experimento_gate_cego.json` | prova de que tornar o gate honesto NÃO muda geometria nenhuma |
| `out_nf_experimento_troca_so_trecho_fechado.json` | prova de que a troca simétrica só acontece em trecho fechado dos dois lados |
| `out_nf_intermediario_so_sentido_A_para_B.json` | versão intermediária (só o sentido "nó da A → junta da B"), medida para isolar o ganho do sentido simétrico |
| `out_nf_trace_evidencia_{HEAD,DEPOIS}_piloto_sintetico_2x2.json` | antes/depois do instrumento do cross-audit (pool GLOBAL — ver o campo `ATENCAO` dentro do arquivo) |

## Fechamento (2026-09-03) — o gate `OPENING_BLOCK_INSIDE_DOOR`

Relatório: `docs/BLOCK_NODE_FILL_JOINT_FECHAMENTO.md`. Regras: §32.

| script | responde a |
|---|---|
| `run_nf_door_table.py` | itens 3 e 4 — tabela PEÇA A PEÇA dos blocos que invadem vão de porta, com o ESTÁGIO (`placement_reason`) que criou cada um |
| `run_nf_door_volume.py` | item 6 — MATERIAL físico dentro do vão (comprimento e área), separado por ALTURA da interseção; não depende da fronteira de 90 % do validador |
| `run_nf_z_origin.py` | item 5 — as DUAS origens verticais e o efeito de alinhá-las em TODOS os códigos |

| arquivo | ponto |
|---|---|
| `out_nf_door_table_{before_HEAD,after}.json` | tabela peça a peça |
| `out_nf_door_volume_{before_HEAD,after}.json` | material físico |
| `out_nf_z_origin_{before_HEAD,after}.json` | origens verticais + efeito do alinhamento |

**Resultado:** 44 dos 49 achados são fantasma de 1 cm (fiada 11 do modelo do
benchmark contra uma verga de 221 cm que, no motor, é a própria fronteira da
fiada). Com as origens alinhadas: **5 antes, 5 depois**. Nenhuma linha de
produção foi alterada nesta etapa.
