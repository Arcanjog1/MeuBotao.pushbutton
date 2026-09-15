# Missão BUTANTÃ — correções físicas da modulação (2026-09-15)

```json
{
  "date": "2026-09-15",
  "scope": "current",
  "branch": "claude/butanta-modulation-physical-fixes",
  "head": "23dfcb7f494b4568980339784ece17b6fb70a668",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "main_observada": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42",
  "veredito": "PARTIAL — REMAINING LIMITATIONS PRECISELY EXPLAINED",
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
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 30.8 (status), 30.9, 53 e 54 novas.",
    "nuvem/core/engine/small_void_alignment.py: giro em par dos B34 (commit 23dfcb7); tests/test_b34_small_void_alignment.py: vermelho/verde do par.",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 52 (giro em par), 55 (especiais junto da jamba, documentado), nota 30.9 CHANNEL x legado.",
    "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/: resumo das execucoes no Revit, metricas, comparador por lado de vao, regressao final e scripts."
  ],
  "tests": [
    "Regressao completa final (HEAD 2eca44c, codigo 23dfcb7): 1237 passed / 3 failed em 42 min 37 s - as tres historicas da main (TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62; test_perf_trace_stall_sampler ctypes/win32). Nenhuma falha nova.",
    "Novos testes: test_b34_small_void_alignment (12), test_physical_tolerance_trial (14), test_physical_support_audit (5).",
    "Revit real (IronPython via MCP, handler real _execute_solve/_execute_create, 34 paredes, 17 fiadas, CHANNEL): run1 (4823114) 9.088 criadas apos purgar 9.458 do lote antigo; run2/run3b/run4 (23dfcb7) assinatura identica 5f6dc513, 9.088 -> 9.088, 0 falhas, 0 divergencias de releitura, humano IsModified False antes e depois de todas.",
    "Paridade Revit x offline: identica com as coordenadas exatas lidas no Revit.",
    "Determinismo offline: 3 processos identicos; inversao de pontas, permutacao e translacao alteram o resultado - pre-existente na main (medido com as mudancas desligadas)."
  ],
  "known_failures": [
    "Herdadas da main: TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62; test_perf_trace_stall_sampler (ctypes, win32).",
    "Especiais junto da jamba: humano 500 x lote final 808 (fiadas 0-11); comparador por lado de vao: 51 SOLVER_WORSE de 88 (secao 55, pendente).",
    "Vazado menor do B34: humano 41 x lote final 336 (validador externo, fiadas 0-12); restantes exigem mudanca de posicao.",
    "Determinismo: resultado depende do sentido das paredes, da ordem de entrada e de ruido de 1e-14 ft (pre-existente).",
    "CHANNEL_ALIGNMENT_ERROR nao foi criado como validador separado: a canaleta usa as pecas da propria fiada (51.3) e a validacao CHANNEL existente e a auditoria de prisma cobrem o caso; cinta de topo (decisao F) continua pendente."
  ],
  "physical_deltas": [
    "Revit real, lote anterior -> lote final [humano] (34 paredes, fiadas 0-12): buracos 215 (22.451 cm) -> 10 (872 cm) [71 (2.953 cm)]; pecas sem apoio fora de vao 116 -> 0 [7]; vaos com sub-preenchimento sob janela 11 -> 0 [0]; violacoes do vazado menor do B34 2.460 -> 336 [41].",
    "Motor: B34 de meio de parede orientado pelo vazado menor (individual e em par); tolerancias 30.8/jamba com tentativa por parede so na CHANNEL; validador de apoio fisico; C04+C04 -> C09.",
    "Legado: so a fusao C04+C04 muda pecas (COMPENSATOR_CONSECUTIVE TP1 936->881, TGD V2 472->464; vereditos iguais)."
  ],
  "decisions_taken": [
    "Regra do usuário (2026-09-15): fiada vizinha preserva o vazado menor do B34; registrada como seção 52 com a evidência humana (2.500/2.541 pares alinhados).",
    "As 12 paredes do doc de teste sem bloco no humano seguem a seção 49 (não estruturais); a comparação física usa as 34 de alvenaria. Consulta somente leitura no humano: nenhum elemento de parede nem bloco no eixo de 11 delas.",
    "Tolerancias fisicas (30.8 e jamba) ligadas com tentativa somente na estrategia CHANNEL: preserva o motivo da opcao B da auditoria (legado identico) e fecha os buracos que o humano fecha no caminho usado no BUTANTA.",
    "Re-solucao do pilarete inteiro junto da jamba NAO integrada: todas as variantes reduzem especiais trocando por violacao do vazado menor do B34 ou quebram o contrato 51.3; medicoes na secao 55 e em metrics_summary.json."
  ],
  "decisions_pending": [
    "DECISION-WALL-OUTSIDE-MODULE e COMPENSATOR-LIMIT continuam pendentes.",
    "Regra 30.8 e tolerância de ruído de jamba (51.13/51.14): em avaliação nesta missão com prova de cobertura por fiada.",
    "Levar as tolerancias com tentativa ao legado exige decisao sobre a regua (TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 por reclassificacao; categoria compensadores 62->63).",
    "Robustez numerica: empates de composicao decididos por ruido de 1e-14 ft (pre-existente).",
    "Prioridade entre a regra 52 (vazado menor) e a reducao de especiais junto da jamba (secao 55).",
    "Decisao F (cinta de topo) e 51.8 (topo/peitoril fora da grade) continuam pendentes."
  ],
  "next_steps": [
    "Revisao do PR draft pelo usuario; nenhuma integracao sem autorizacao.",
    "Secao 55: criterio conjunto especiais + vazado menor + pecas de no + bandas.",
    "Robustez numerica e independencia de ordem e sentido do motor (pre-existente)."
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
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/revit_runs_summary.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/metrics_summary.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/comparator_rows_final.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/regressao_final.txt"
    },
    {
      "path": "tests/test_physical_tolerance_trial.py"
    },
    {
      "path": "tests/test_physical_support_audit.py"
    }
  ]
}
```

## 1. Estado de git

- `origin/main` = `55e990d962ed22ae1021f0d335db197607bddda1` (merge do PR
  [#41](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/41)), confirmado por fetch.
- Branch `claude/butanta-modulation-physical-fixes` criada dessa main. PR draft [#42](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42), sem merge.

## 2. Documentos Revit

- HUMANO (somente leitura): `BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO) (1).rvt`,
  identificado pelo caminho exato; `IsModified=False` antes e depois de cada consulta.
- TARGET: `butanta testes.rvt` (46 paredes de 340 cm, 44 aberturas). Lote anterior do botão
  `20260914-191852` (9.458 peças) feito com uma main anterior.

## 3. Vazado menor do B34 (regra 52)

| Medida | Humano | Lote anterior | Bancada sem passe | Bancada com passe |
|---|---|---|---|---|
| Violações (34 paredes, fiadas 0–12) | 41 | 2.460 | 2.000 | 264 (com giro em par) |

No lote final do Revit o validador externo mede 336. As restantes exigem mudar a posição do B34, não a orientação.

## 4. Buracos, apoio e compensadores (regras 30.9, 53, 54)

| Métrica (34 paredes, 13 fiadas) | Sem as correções | Com as correções | Humano |
|---|---|---|---|
| Buracos | 94 (3.754 cm) | 10 (872 cm) | 71 (2.953 cm) |
| NON_MODULAR | 78 | 0 | — |
| Peças sem apoio | 50 | 0 | 9 |
| C04+C04 encostados | 7 | 0 | 0 |

Os 10 buracos restantes são vazios que o humano também deixa: passagem livre
até o topo e pilaretes de 5 e 15 cm.

## 5. Revit real — lote final

| Execução | Código | Peças | Substituição | Falhas | Releitura | Humano modificado |
|---|---|---|---|---|---|---|
| run1 | 4823114 | 9.088 | 9.458 purgadas → 9.088 | 0 | 0 divergências | não |
| run2 | 23dfcb7 | 9.088 | 9.088 → 9.088 | 0 | 0 divergências | não |
| run3b | 23dfcb7 | 9.088 | 9.083 → 9.088 | 0 | 0 divergências | não |
| run4 | 23dfcb7 | 9.088 | 9.088 → 9.088 | 0 | 0 divergências | não |

O run3 original foi descartado: carregou o motor enquanto um patch experimental
estava na árvore de trabalho. Runs 2, 3b e 4 têm a mesma assinatura.

| Métrica (34 paredes, fiadas 0–12) | Humano | Lote anterior | Lote final |
|---|---|---|---|
| Buracos | 71 (2.953 cm) | 215 (22.451 cm) | 10 (872 cm) |
| Peças sem apoio fora de vão | 7 | 116 | 0 |
| Vãos com sub-preenchimento sob janela | 0 | 11 | 0 |
| Violações do vazado menor do B34 | 41 | 2.460 | 336 |
| Compensadores + pastilhas (fiadas 0–11) | 500 | 686 | 808 |

Validação CHANNEL no Revit: 40/40 canaletas superiores e 23/23 inferiores,
nenhuma faltante, extra, em fiada errada, invadindo vão ou colidindo.

## 6. Limitações restantes

- **Especiais junto da jamba** (seção 55): 51 de 88 lados de vão com dois ou mais
  especiais acima do humano. Toda correção medida trocava erro.
- **Vazado menor do B34**: 336 × 41 do humano; o resíduo pede mudança de posição.
- **Determinismo**: sentido das paredes, ordem de entrada e ruído numérico mudam
  empates de composição — pré-existente na main.
- **Regressão final**: 1.237 passaram, 3 falhas históricas da main.
