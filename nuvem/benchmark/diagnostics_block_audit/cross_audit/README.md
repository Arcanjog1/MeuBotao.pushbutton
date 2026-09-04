# Cross audit — CR-BLOCK-01 (CONTA 2, fase 2)

Auditoria cruzada do `CR-BLOCK-01` (CONTA 1, branch
`claude/block-01-prisma-fiadas-rik42t`), rodada nesta branch de
integração exclusiva para auditoria (`claude/block-01-cross-audit`,
criada a partir da branch da CONTA 1 + merge dos artefatos read-only da
CONTA 2). Produto principal:
**`docs/archive/BLOCK_MODULATION_CROSS_AUDIT.md`**.

## Contrato

Mesmo contrato da auditoria da fase 1 (`../README.md`): só leitura do
motor, nada de MCP/Revit, não corrige nada. Escrita restrita a esta
pasta (`cross_audit/**`) e a `docs/archive/BLOCK_MODULATION_CROSS_AUDIT.md`.
`nuvem/core/**`, `tests/test_script.py`, `tests/test_block_bonding.py`,
`nuvem/REGRAS_MODULACAO_BLOCOS.md` e `docs/PROJECT_STATUS.md` não foram
tocados.

## Método — MESMA biblioteca, dois checkouts

Todo número deste diretório vem da mesma `lib_audit.py`/`run_*_census.py`
da CONTA 2 (trazidos por merge, não modificados), rodados duas vezes:

1. **MAIN** — um `git worktree` temporário de
   `9f3bab41b35f0e2a5f9782583ead8e1ee7755f49`, com os scripts do
   laboratório copiados para dentro (nunca commitados lá), rodado e
   descartado (`git worktree remove`).
2. **CR-BLOCK-01** — o checkout desta própria branch (que já é a branch
   da CONTA 1 com as ferramentas da CONTA 2 mescladas por cima).

Nenhum número da CONTA 1 foi aceito como verdade — tudo foi recalculado.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `run_block01_census.py` | roda os censos da fase 1 (prisma, blocos especiais, L/T/X, aberturas, cobertura, determinismo) sobre os 3 projetos de benchmark nesta branch |
| `out_block01_full_census.json` | saída consolidada do acima (CR-BLOCK-01) |
| `out_main_aggregate_full_census.json` | a MESMA saída, mas rodada sobre a MAIN pura (via worktree temporário) |
| `node_conflict_breakdown.py` / `out_node_conflict_breakdown_{MAIN,BLOCK01}.json` | proxy independente da categoria `UNCLASSIFIED_RULE_CONFLICT` da CONTA 1 — decompõe as juntas coincidentes suspeitas por tipo de nó tocado (L/T/X/abertura/nenhum) |
| `b19_location_breakdown.py` / `out_b19_location_*.json` | detalha B19 por borda do BLOCO (não centro) — perto de abertura / perto de ponta / meio de parede de verdade |
| `out_non_modular_plus3_detail.json` | os 3 eventos exatos por trás do `non_modular` agregado 3333→3336 |
| `out_trim_vs_shift_investigation.json` | reprodução direta do caso do teste `test_pipeline_lanca_blocos_e_ajusta_na_mesma_passada` nos dois checkouts |
| `out_test_suite_results.json` | resultado literal das 4 suítes de teste, sem alterar nenhuma |
| `build_compare.py` / `compare_main_vs_block01.json` | consolidação MAIN × CR-BLOCK-01 × DELTA × DELTA% de todas as métricas acima |

## Como reproduzir

```bash
cd nuvem/benchmark/diagnostics_block_audit/cross_audit
python3 run_block01_census.py            # ~28s, roda sobre ESTA branch
python3 node_conflict_breakdown.py
python3 b19_location_breakdown.py torre_easy_lo_r00_tgd
python3 build_compare.py
```

Para reproduzir o lado MAIN, é necessário um `git worktree` temporário do
SHA `9f3bab41b35f0e2a5f9782583ead8e1ee7755f49` com os mesmos scripts
copiados para dentro (não versionados lá) — ver o histórico de comandos
usado nesta sessão para o passo a passo exato, ou simplesmente reexecutar
o mesmo censo em qualquer checkout limpo da `main` nesse SHA.
