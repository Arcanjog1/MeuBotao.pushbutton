# Missão claude/revit-scale-autofix — fechamento: escala, comparação humana e criação real

```json
{
  "date": "2026-09-11",
  "scope": "current",
  "branch": "claude/revit-scale-autofix",
  "head": "91cc73833c188ca618c86e59cade4f62e6b0a125",
  "base": "41086e43b6b56102ce736b816debad04749fa4bf",
  "main_observada": "21576ee3d0826f362bce1038131603bd2ccf5dc1",
  "pr": "not-created",
  "veredito": "PARTIAL SCALE PASS — LIMITE CONHECIDO E EXPLICADO. Planta inteira passa o gate de criação; 7.257 blocos criados e recriados no Revit sem duplicata; restam 5 paredes reprovadas pelo auditor (junta corrida na fronteira preenchimento|amarração), que o projeto humano não produz.",
  "objective": "Recriar o cenário de escala a partir da bancada de 2 paredes, achar a primeira diferença que faz o fluxo falhar, corrigir com prova, e — a pedido do usuário — validar/derrubar cada regra contra o projeto humano pronto BUTANTÃ R08_LT e extrair regras novas.",
  "changes": [
    "wall_stepper.py: _reject_overlapping_node_ties (rede de segurança: nunca dois sólidos no mesmo espaço); _clip_range_by_midspan_neighbours (T sem espaço degrada para B34|B34 — regra 11.10 revisada pela evidência humana); fileira de B34 antes de compensadores empilhados em _pier_ordered_layout (bug contra a seção 2 das regras).",
    "wall_modeling.py: boneca absorvida em _drop_fill_colliding_with_ties (11.11); _level_internal_elevation_ft = ProjectElevation em 9 usos (8a.1); MirrorElements(..., mirrorCopies=False) no lugar de MirrorElement (12.1).",
    "tests/revit_stubs.py: MirrorElements com a semântica real. Testes novos: test_scale_autofix_rules (12), test_level_internal_elevation (3), test_fill_prefers_b34_row_over_stacked_compensators (4), test_mirror_in_place (2); tests/scale_bench.py (escada de escala offline sobre eixos reais).",
    "REGRAS_MODULACAO_BLOCOS.md: 8a.1, 11.10 (+revisão), 11.11, 12.1, correção de implementação na seção 2.",
    "Doc de teste 'butanta testes' (não salvo): import '1 PAV' reescalado ×10 e reposicionado (DWG em cm importado como mm); 7.257 blocos criados no 1º PAVIMENTO pelo caminho real (_execute_create, modo beta).",
    "Evidência em docs/checkpoints/evidence/ (Torre: prestate/axes; Butantã: blocos humanos, walls, sequências, diff, CAD, eixos A-WALL) e _scripts/ reprodutíveis."
  ],
  "tests": [
    "Focados no HEAD: test_scale_autofix_rules + test_level_internal_elevation + test_fill_prefers_b34_row_over_stacked_compensators + test_mirror_in_place + test_beta_atomic_creation + test_controlled_beta_preflight + test_bond_strip_adjacent_courses + test_block_fit_tolerance_c04 + test_block_bonding: todos passando (52 + 130 nas duas últimas rodadas).",
    "Prova causal na planta inteira da Torre (179 eixos): com as regras 0 colisões de preflight; sem 11.10 = 7; sem 11.11 = 42; sem as duas = 49.",
    "Paridade Revit × offline: motor da branch carregado no Revit (IronPython) resolve as 34 paredes de Butantã com 7.257 peças, preflight ok, ifail 0, nmod 78, bond 5 — idêntico ao CPython offline.",
    "Regressão consolidada (raiz, pytest -q) sobre a árvore final: EM EXECUÇÃO no momento deste checkpoint; resultado registrado na seção 'Regressão consolidada' abaixo quando terminar. As 2 falhas históricas de test_benchmark_baselines (TGD compensators 52→61, TP1 binding 8→9) já apareceram nas mesmas posições."
  ],
  "known_failures": [
    "Butantã, 34 paredes, mesmo auditor e mesmas aberturas: solver reprova 5 paredes (9 juntas corridas, todas na fronteira preenchimento|amarração); humano reprova 2 (3× B19 residual, exceção já prevista). O usuário decidiu manter reprovando; o trabalho restante é no layout do gerador perto dos nós.",
    "3 nós T em parede de 99 cm com canto nas duas pontas saem C09|C09 (humano B34|B34): reserva de canto por fiada pendente.",
    "Torre, planta inteira: 21 paredes reprovadas (defeito 1) e 260 trechos não modulares (material da Etapa 3B, não exercitada).",
    "Performance de CRIAÇÃO: 36,9 ms por NewFamilyInstance no doc de Butantã (146 mil elementos) — 7.257 peças = 295 s; estoura o timeout HTTP do MCP, e no botão real aparecerá como Tela 2 longa. Solve: 18–21 s.",
    "main() sob IronPython (harness MCP) parava em wall_modeling.py:15570 no TESTE MODULAÇÃO — limite do harness, não atribuído a produção; não reproduzido em Butantã porque a Etapa 1 lá foi 'paredes existentes'.",
    "Trecho curto ponta-livre→T (defeito 1 pela evidência humana): inconclusivo — as pontas medidas são pilares de concreto, não alvenaria.",
    "11.11 (boneca absorvida) não é testada pelo humano (caso não ocorre no pavimento)."
  ],
  "physical_deltas": [
    "TESTE MODULAÇÃO (Torre): 2 Walls + 154 blocos do lote anterior apagados com autorização (pré-estado em evidence/prestate.json). Nenhuma parede recriada lá (harness).",
    "butanta testes: import 1 PAV corrigido (fator de escala do tipo ×10 + translação; 93% dos eixos A-WALL alinhados a ≤2 cm do layer Paredes). 7.257 blocos criados no 1º PAVIMENTO em 14 fiadas z=1..261 cm (passo 20), simbolos B39 4269 / B34 1716 / B19 288 / B54 195 / C09 492 / C04 297; 0 colisões; 54 compensadores espelhados NO LUGAR. RECRIAÇÃO: lote substituído por exatamente 7.257, 0 órfãs, 0 posições duplicadas (idempotência PASS). Antes do fix 12.1 a primeira criação deixara 54 cópias espelhadas órfãs (7.311 no doc), removidas com prova.",
    "Documento de teste NÃO salvo (IsModified=True) — decisão do usuário."
  ],
  "decisions_taken": [
    "Projeto humano prevalece sobre respostas rápidas (instrução do usuário): 11.10 revisada (degradar antes de deixar sem modular).",
    "Auditor não foi tocado: ele concorda com o humano (0 juntas corridas humanas com vãos reais).",
    "Escada de escala em CPython (semântica de '/') e criação física pelo caminho real dentro do Revit.",
    "Bug de API (MirrorElement) corrigido como implementação, não como regra.",
    "Nenhum baseline/reference/threshold alterado; nenhum skip/xfail; nenhum merge na main."
  ],
  "decisions_pending": [
    "Reserva de canto por fiada (parede curta com canto nas duas pontas).",
    "Filtro de paredes não estruturais no fluxo CAD→Walls (12/46 do layer 'Paredes' não são alvenaria).",
    "Salvar ou descartar o doc 'butanta testes' com os 7.257 blocos e o CAD corrigido.",
    "Deploy do pacote beta com o HEAD desta branch no botão teste-perf (hoje em 712f221).",
    "PR e merge: decisão do usuário."
  ],
  "next_steps": [
    "Defeito 1 no gerador: escalonar o preenchimento contra a amarração (o humano usa corridas de B34 para mudar a fase).",
    "Reserva de canto por fiada; medir com as três paredes de 99 cm de Butantã.",
    "Um clique real no botão com o pacote do HEAD (CPython) nas 34 paredes: Tela 1 → Tela 2, medir tempos e comparar com os 7.257.",
    "Estender a comparação humana aos demais pavimentos (2º é matriz dos clones) e ao TORRE EASY."
  ],
  "references": [
    {"path": "docs/checkpoints/2026-09-10-revit-scale-autofix.md"},
    {"path": "docs/checkpoints/2026-09-10-butanta-human-comparison.md"},
    {"path": "docs/checkpoints/evidence/2026-09-10-butanta-ref-1pav-blocks.json"},
    {"path": "docs/checkpoints/evidence/2026-09-10-butanta-solver-vs-human.json"},
    {"path": "docs/checkpoints/evidence/2026-09-10-scale-autofix-axes.json"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/scale_bench.py"}
  ]
}
```

## Matriz de escala (Torre, 179 eixos) — antes e depois

| K | preflight antes | preflight depois | observação |
|---|---|---|---|
| 2 | ok | ok | bancada: 154 peças, igual ao Revit real (offline dava 168 com compensador) |
| 5 | ok (bond 1) | ok (bond 1) | junta corrida — defeito 1 |
| 7 | **FALHA** (7 colisões) | ok | dois T a 27 cm: antes B54×B54; agora degradam para B34\|B34 |
| 10–100 | FALHA | ok | bonecas atravessando: absorvidas |
| 179 | **FALHA** (49 colisões) | **ok** | 10.129 peças, 7,7 s |

## Comparação com o projeto humano (Butantã, 34 paredes, vãos reais)

| Métrica | Humano | Solver antes | Solver depois |
|---|---|---|---|
| Paredes reprovadas pelo auditor do repo | 2 | 12 | **5** |
| Faixas de compensador | 0 | 7 | **0** |
| B34 / C09 (fiadas 0..12) | 1615 / 242 | 846 / 739 | **1557 / 467** |
| Parede de 494 cm | B34 + 9×B39 + B34 B34 | 11×B39 + C09 C09 C04 | 9×B39 + 3×B34 |
| Nós T com espaço | B54\|B34 (30/34) | igual | igual |
| Nós L | B34\|B34 (13/13) | igual | igual |

## Regressão consolidada

Preenchido ao término da execução (ver commit seguinte a este checkpoint).
