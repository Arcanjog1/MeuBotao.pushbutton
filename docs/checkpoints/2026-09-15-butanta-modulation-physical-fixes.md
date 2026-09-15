# Missão BUTANTÃ — correções físicas da modulação (2026-09-15, em andamento)

```json
{
  "date": "2026-09-15",
  "scope": "current",
  "branch": "claude/butanta-modulation-physical-fixes",
  "head": "4823114462c74091ae053fbb36501673735c83e0",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "main_observada": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "not-created",
  "veredito": "EM ANDAMENTO — entrega parcial versionada; PR draft só ao final da missão",
  "objective": "Corrigir a modulação real no Revit comparando o projeto humano BUTANTÃ R08_LT (somente leitura) com o doc de teste 'butanta testes', sem hardcode, sem mascarar validador e sem corromper a referência humana.",
  "changes": [
    "nuvem/core/engine/small_void_alignment.py (novo): validador do vazado menor entre fiadas e passe de orientação 180° dos B34 que não são peça de nó.",
    "nuvem/core/wall_modeling.py: _orient_small_voids_final nas duas saídas de _solve_building_blocks_all_courses_impl e, com CHANNEL, antes de _unify_candidates_with_courses; resultado em result['small_void_alignment'].",
    "tests/test_b34_small_void_alignment.py (novo): 10 testes (vermelho/verde, nó fixo, rotação rígida, invariâncias, controle do validador).",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: seção 52 nova; seções 6 e 18.5 atualizadas.",
    "nuvem/core/engine/wall_stepper.py: physical_tolerance_trial (30.8 e ruido de jamba com tentativa por parede: assenta mais sem coincidencia nova e sem deixar a familia oposta vazia), fuse_adjacent_equal_compensators (C04+C04 -> C09 depois do reparo de vao).",
    "nuvem/core/engine/continuous_modulation.py: contador/supressao da tolerancia de ruido de jamba para a tentativa.",
    "nuvem/core/engine/physical_support.py (novo): validador somente leitura UNSUPPORTED_SMALL_BLOCK/UNSUPPORTED_BLOCK.",
    "nuvem/core/wall_modeling.py: CHANNEL_PHYSICAL_TOLERANCES_ENABLED (tolerancias com tentativa so' na estrategia CHANNEL) e _physical_support_final no resultado final.",
    "tests/test_physical_tolerance_trial.py e tests/test_physical_support_audit.py (novos); tests/test_node_bounded_residual.py: o vermelho desliga tambem a ativacao na CHANNEL.",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 30.8 (status), 30.9, 53 e 54 novas."
  ],
  "tests": [
    "Focados: B34 + golden + block_bonding + tie_parity + channel_audit_fixes + channel_reinforcement + node_bounded_residual + physical_tolerance_trial + physical_support_audit: todos passando (144 + 115 + 19 nesta rodada).",
    "tests/regression/test_benchmark_baselines.py -m slow no HEAD de codigo: 9 passed / 2 failed, as duas falhas historicas da main (TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62).",
    "Corpus por parede (TGD/TP1 V1/V2, script de prova de cobertura): fusao sozinha nao muda veredito; tolerancias com tentativa ligadas no legado medidas e NAO ativadas (TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 por reclassificacao).",
    "Revit real, IronPython, so' calculo, 34 paredes/17 fiadas CHANNEL: 9.088 pecas, NON_MODULAR 0, colisoes 0, preflight ok, MISSING_REQUIRED_CHANNEL 0, sem apoio 0; humano IsModified False antes/depois.",
    "Paridade Revit x offline: identica com as coordenadas exatas lidas no Revit; com as coordenadas do JSON (ruido 1,4e-14 ft) 39 pecas de uma parede trocam B34 do inicio para o fim do trecho - pre-existente na main (mesmo resultado com as mudancas desta branch desligadas)."
  ],
  "known_failures": [
    "Herdadas da main: TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62; test_perf_trace_stall_sampler (ctypes, win32)."
  ],
  "physical_deltas": [
    "B34 de meio de parede passa a ser girado 180° quando isso alinha o vazado menor com a fiada vizinha. Bancada offline do doc de teste (34 paredes de alvenaria, 13 fiadas): violações 2.000 -> 294; 46 paredes/17 fiadas: 3.400 -> 590. Contorno, juntas, colisões e cobertura idênticos por construção.",
    "Revit real ainda não executado com este HEAD (gate final da missão).",
    "Bancada BUTANTA (CHANNEL, 34 paredes, 13 fiadas): buracos 94 (3.754 cm) -> 10 (872 cm, os mesmos vazios do humano); NON_MODULAR 78 -> 0; pecas sem apoio 50 -> 0; C04+C04 encostados 7 -> 0; MISSING_REQUIRED_CHANNEL 1 -> 0.",
    "Legado (estrategia None): so' a fusao C04+C04 muda pecas; tolerancias continuam desligadas."
  ],
  "decisions_taken": [
    "Regra do usuário (2026-09-15): fiada vizinha preserva o vazado menor do B34; registrada como seção 52 com a evidência humana (2.500/2.541 pares alinhados).",
    "As 12 paredes do doc de teste sem bloco no humano seguem a seção 49 (não estruturais); a comparação física usa as 34 de alvenaria. Consulta somente leitura no humano: nenhum elemento de parede nem bloco no eixo de 11 delas.",
    "Tolerancias fisicas (30.8 e jamba) ligadas com tentativa somente na estrategia CHANNEL: preserva o motivo da opcao B da auditoria (legado identico) e fecha os buracos que o humano fecha no caminho usado no BUTANTA."
  ],
  "decisions_pending": [
    "DECISION-WALL-OUTSIDE-MODULE e COMPENSATOR-LIMIT continuam pendentes.",
    "Regra 30.8 e tolerância de ruído de jamba (51.13/51.14): em avaliação nesta missão com prova de cobertura por fiada.",
    "Levar as tolerancias com tentativa ao legado exige decisao sobre a regua (TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 por reclassificacao; categoria compensadores 62->63).",
    "Robustez numerica: empates de composicao decididos por ruido de 1e-14 ft (pre-existente)."
  ],
  "next_steps": [
    "Buracos em pilaretes/anel de shaft (30.8 + ruído de jamba) com prova no TGD/TP1.",
    "Concentração de especiais, canaletas humano x solver, peça pequena sem apoio, execução real no Revit, idempotência, determinismo, regressão final e PR draft."
  ],
  "references": [
    {
      "path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"
    },
    {
      "path": "nuvem/core/engine/small_void_alignment.py"
    },
    {
      "path": "tests/test_b34_small_void_alignment.py"
    },
    {
      "path": "docs/PROJECT_STATUS.md"
    }
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

## 4. Buracos, apoio e compensadores (regras 30.9, 53, 54)

| Métrica (34 paredes, 13 fiadas) | Sem as correções | Com as correções | Humano |
|---|---|---|---|
| Buracos | 94 (3.754 cm) | 10 (872 cm) | 71 (2.953 cm) |
| NON_MODULAR | 78 | 0 | — |
| Peças sem apoio | 50 | 0 | 9 |
| C04+C04 encostados | 7 | 0 | 0 |

Os 10 buracos restantes são vazios que o humano também deixa: passagem livre
até o topo e pilaretes de 5 e 15 cm.
