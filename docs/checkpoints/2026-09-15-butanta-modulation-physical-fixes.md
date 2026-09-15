# Missão BUTANTÃ — correções físicas da modulação (2026-09-15, em andamento)

```json
{
  "date": "2026-09-15",
  "scope": "current",
  "branch": "claude/butanta-modulation-physical-fixes",
  "head": "0a0f052e22a0b2c2a5ce3e0667b2740c4c001189",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "main_observada": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "not-created",
  "veredito": "EM ANDAMENTO — entrega parcial versionada; PR draft só ao final da missão",
  "objective": "Corrigir a modulação real no Revit comparando o projeto humano BUTANTÃ R08_LT (somente leitura) com o doc de teste 'butanta testes', sem hardcode, sem mascarar validador e sem corromper a referência humana.",
  "changes": [
    "nuvem/core/engine/small_void_alignment.py (novo): validador do vazado menor entre fiadas e passe de orientação 180° dos B34 que não são peça de nó.",
    "nuvem/core/wall_modeling.py: _orient_small_voids_final nas duas saídas de _solve_building_blocks_all_courses_impl e, com CHANNEL, antes de _unify_candidates_with_courses; resultado em result['small_void_alignment'].",
    "tests/test_b34_small_void_alignment.py (novo): 10 testes (vermelho/verde, nó fixo, rotação rígida, invariâncias, controle do validador).",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: seção 52 nova; seções 6 e 18.5 atualizadas."
  ],
  "tests": [
    "Focados: test_b34_small_void_alignment + test_golden_benchmark + test_block_bonding + test_tie_parity_abutting_ties + test_channel_audit_fixes + test_channel_reinforcement + test_node_bounded_residual = 240 passed.",
    "tests/regression/test_benchmark_baselines.py -m slow: 9 passed / 2 failed, as duas falhas históricas da main (TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62).",
    "Benchmark TGD V1 com e sem o passe: achados idênticos (contorno das peças não muda)."
  ],
  "known_failures": [
    "Herdadas da main: TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62; test_perf_trace_stall_sampler (ctypes, win32)."
  ],
  "physical_deltas": [
    "B34 de meio de parede passa a ser girado 180° quando isso alinha o vazado menor com a fiada vizinha. Bancada offline do doc de teste (34 paredes de alvenaria, 13 fiadas): violações 2.000 -> 294; 46 paredes/17 fiadas: 3.400 -> 590. Contorno, juntas, colisões e cobertura idênticos por construção.",
    "Revit real ainda não executado com este HEAD (gate final da missão)."
  ],
  "decisions_taken": [
    "Regra do usuário (2026-09-15): fiada vizinha preserva o vazado menor do B34; registrada como seção 52 com a evidência humana (2.500/2.541 pares alinhados).",
    "As 12 paredes do doc de teste sem bloco no humano seguem a seção 49 (não estruturais); a comparação física usa as 34 de alvenaria. Consulta somente leitura no humano: nenhum elemento de parede nem bloco no eixo de 11 delas."
  ],
  "decisions_pending": [
    "DECISION-WALL-OUTSIDE-MODULE e COMPENSATOR-LIMIT continuam pendentes.",
    "Regra 30.8 e tolerância de ruído de jamba (51.13/51.14): em avaliação nesta missão com prova de cobertura por fiada."
  ],
  "next_steps": [
    "Buracos em pilaretes/anel de shaft (30.8 + ruído de jamba) com prova no TGD/TP1.",
    "Concentração de especiais, canaletas humano x solver, peça pequena sem apoio, execução real no Revit, idempotência, determinismo, regressão final e PR draft."
  ],
  "references": [
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "nuvem/core/engine/small_void_alignment.py"},
    {"path": "tests/test_b34_small_void_alignment.py"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## 1. Estado de git

- `origin/main` = `55e990d962ed22ae1021f0d335db197607bddda1` (merge do PR
  [#41](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/41)), confirmado por fetch.
- Branch `claude/butanta-modulation-physical-fixes` criada dessa main. Sem merge, sem PR ainda.

## 2. Documentos Revit

- HUMANO (somente leitura): `BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO) (1).rvt`,
  identificado pelo caminho exato; `IsModified=False` antes e depois de cada consulta.
- TARGET: `butanta testes.rvt` (46 paredes de 340 cm, 44 aberturas). Lote anterior do botão
  `20260914-191852` (9.458 peças) feito com uma main anterior.

## 3. Vazado menor do B34 (regra 52)

| Medida | Humano | Lote anterior | Bancada sem passe | Bancada com passe |
|---|---|---|---|---|
| Violações (34 paredes, fiadas 0–12) | 41 | 2.460 | 2.000 | 294 |

As 294 restantes exigem mudar a posição do B34, não a orientação.
