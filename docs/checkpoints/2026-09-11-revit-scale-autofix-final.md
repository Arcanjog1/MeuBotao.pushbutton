# Missão claude/revit-scale-autofix — fechamento: escala, comparação humana e criação real

```json
{
  "date": "2026-09-11",
  "scope": "current",
  "branch": "claude/revit-scale-autofix",
  "head": "cf325f2e78130d8aa54b464e0ac0599b897ff750",
  "base": "41086e43b6b56102ce736b816debad04749fa4bf",
  "main_observada": "21576ee3d0826f362bce1038131603bd2ccf5dc1",
  "pr": "not-created",
  "veredito": "PARTIAL SCALE PASS — LIMITE CONHECIDO E EXPLICADO. Planta inteira passa o gate de criação; 7.257 blocos criados e recriados no Revit sem duplicata; benchmark TGD melhora com a configuração final; restam 5 (flag humana) / 12 (default da regra #2) paredes reprovadas pelo auditor em Butantã e uma decisão normativa pendente (fileira de B34).",
  "objective": "Recriar o cenário de escala a partir da bancada de 2 paredes, achar a primeira diferença que faz o fluxo falhar, corrigir com prova, e — a pedido do usuário — validar/derrubar cada regra contra o projeto humano pronto BUTANTÃ R08_LT e extrair regras novas.",
  "changes": [
    "wall_stepper.py: _clip_range_by_midspan_neighbours (T sem espaço degrada para B34|B34 — 11.10 revisada; reserva no vizinho = meia espessura genérica: a reserva de meio B54 foi REVERTIDA em 2026-09-11 pela bissecção TP1, OPENING_BLOCK_INSIDE_DOOR 0→7); _reject_overlapping_node_ties mantida mas DESLIGADA por padrão (REJECT_OVERLAPPING_NODE_TIES=False — regressão crítica no TGD); fileira de B34 antes de compensadores empilhados atrás de PREFER_B34_ROW_OVER_STACKED_COMPENSATORS, DEFAULT False (regra #2 documentada; decisão do usuário pendente).",
    "wall_modeling.py: boneca absorvida em _drop_fill_colliding_with_ties (11.11); _level_internal_elevation_ft = ProjectElevation em 9 usos (8a.1); MirrorElements(..., mirrorCopies=False) no lugar de MirrorElement (12.1).",
    "tests/revit_stubs.py: MirrorElements com a semântica real. Testes novos: test_scale_autofix_rules (12), test_level_internal_elevation (3), test_fill_prefers_b34_row_over_stacked_compensators (4), test_mirror_in_place (2); tests/scale_bench.py (escada de escala offline sobre eixos reais).",
    "REGRAS_MODULACAO_BLOCOS.md: 8a.1, 11.10 (+revisão), 11.11, 12.1, correção de implementação na seção 2.",
    "Doc de teste 'butanta testes' (não salvo): import '1 PAV' reescalado ×10 e reposicionado (DWG em cm importado como mm); 7.257 blocos criados no 1º PAVIMENTO pelo caminho real (_execute_create, modo beta).",
    "Evidência em docs/checkpoints/evidence/ (Torre: prestate/axes; Butantã: blocos humanos, walls, sequências, diff, CAD, eixos A-WALL) e _scripts/ reprodutíveis."
  ],
  "tests": [
    "Focados no HEAD final: test_scale_autofix_rules (13, inclui o limite conhecido 34–54 cm) + test_fill_prefers_b34_row_over_stacked_compensators (5, flag explícita) + test_mirror_in_place (2) + test_level_internal_elevation (4) + test_beta_atomic_creation + test_controlled_beta_preflight + test_block_node_fill_revalidation + test_peca_de_amarracao_nao_vira_enchimento_em_trecho_longo + união de paredes (29): todos passando.",
    "REGRESSÃO CONSOLIDADA 1 (árvore com rede ligada e fileira de B34 ligada): 20 failed / 1055 passed em 2h21. Diagnóstico por grupo: 13 união de paredes (ProjectElevation aceitava objeto inerte do dublê — corrigido, só número vale); 2 guardas de fonte (artefato: editei wall_modeling.py durante a suíte; passam em processo limpo); 4 (regra #2 + controles node_fill) causados pela fileira de B34 — flag desligada por padrão; 1 TGD crítica (JUNCTION_MISSING_BINDING 24→253) causada pela rede de rejeição — desligada.",
    "BISSECÇÃO TGD (runner.run_project, 6 configurações): HEAD crítica 253; sem clip 253; SEM REDE → MELHORIA (23, PRISM_CONTINUOUS_JOINT 961→324, POSITION_OVERLAP 29→24, OPENING_BLOCK_INSIDE_DOOR 45→5); sem fileira B34 253 (indiferente); sem boneca 253; tudo desligado = falha histórica (compensators 52→61).",
    "BISSECÇÃO TP1 (runner.run_project, 7 configurações, evidence/2026-09-11-bisect-tp1.txt): HEAD 09ce2a7, rede ligada, fileira B34 e sem boneca = crítica OPENING_BLOCK_INSIDE_DOOR 0→7; com a reserva antiga (meia espessura), sem clip e tudo desligado = sem INSIDE_DOOR (só a histórica JUNCTION 8→9 e compensators 74→78 de categoria). Culpado: reserva de meio B54 em _clip_range_by_midspan_neighbours — revertida (as melhorias CROSSES_JAMB 168→161 e POSITION_OVERLAP 18→0 vinham junto com ela e são abandonadas); o clip com a reserva genérica fica, porque é ele que degrada o par de T da Torre em vez de deixá-lo sem modular.",
    "Prova causal na Torre (179 eixos): com as regras 0 colisões de preflight; sem 11.10 = 7; sem 11.11 = 42; sem as duas = 49.",
    "Paridade Revit × offline: motor da branch no Revit (IronPython) resolve as 34 paredes de Butantã com 7.257 peças, preflight ok, ifail 0, nmod 78, bond 5 — idêntico ao CPython offline.",
    "Baseline TGD/TP1 e REGRESSÃO CONSOLIDADA 2 com a configuração final: ver seção 'Regressão consolidada' abaixo."
  ],
  "known_failures": [
    "Butantã, 34 paredes, mesmo auditor e mesmas aberturas: com PREFER_B34_ROW_OVER_STACKED_COMPENSATORS=True (comportamento humano) o solver reprova 5 paredes (9 juntas corridas na fronteira preenchimento|amarração); com o DEFAULT False (regra #2 documentada) reprova 12 (as mesmas 5 + 7 faixas de compensador nas paredes de 494 cm, que o humano fecha com 3×B34). Humano: 2 (3× B19 residual, exceção prevista).",
    "3 nós T em parede de 99 cm com canto nas duas pontas saem C09|C09 (humano B34|B34): reserva de canto por fiada pendente.",
    "Torre, planta inteira (tests/scale_bench.py, 179 eixos, HEAD final): preflight ok, 0 colisões de preflight, 4 intersection_failures e 6 colisões de solver nos eixos degenerados do CAD (mesmos 4/6 do HEAD 09ce2a7), 22 paredes reprovadas (defeito 1) e 260 trechos não modulares (material da Etapa 3B, não exercitada).",
    "Performance de CRIAÇÃO: 36,9 ms por NewFamilyInstance no doc de Butantã (146 mil elementos) — 7.257 peças = 295 s; estoura o timeout HTTP do MCP, e no botão real aparecerá como Tela 2 longa. Solve: 18–21 s.",
    "main() sob IronPython (harness MCP) parava em wall_modeling.py:15570 no TESTE MODULAÇÃO — limite do harness, não atribuído a produção; não reproduzido em Butantã porque a Etapa 1 lá foi 'paredes existentes'.",
    "Trecho curto ponta-livre→T (defeito 1 pela evidência humana): inconclusivo — as pontas medidas são pilares de concreto, não alvenaria.",
    "11.11 (boneca absorvida) não é testada pelo humano (caso não ocorre no pavimento).",
    "LIMITE CONHECIDO 11.10: dois T na mesma principal entre 34 e 54 cm ainda passam no teste de espaço (reserva genérica de meio de vão) e os B54 se interpenetram; o par é barrado pelo gate de colisão do preflight (BETA BLOQUEADO), nunca em silêncio. A reserva de meio B54 que resolveria isso foi medida no TP1 e causa 7 blocos dentro de porta (regressão crítica) — revertida. Teste registra o limite (test_11_10_limite_conhecido_...).",
    "Falhas históricas do benchmark preservadas: torre_easy_lo_r00_tgd compensators 52→61 e torre_easy_lo_r00_tp1 JUNCTION_MISSING_BINDING 8→9 (idênticas às de 8cdd33f); no HEAD final medem 52→55 (TGD) e 8→9 (TP1), sem nenhuma crítica nova; nenhum baseline regravado."
  ],
  "physical_deltas": [
    "TESTE MODULAÇÃO (Torre): 2 Walls + 154 blocos do lote anterior apagados com autorização (pré-estado em evidence/prestate.json). Nenhuma parede recriada lá (harness).",
    "butanta testes: import 1 PAV corrigido (fator de escala do tipo ×10 + translação; 93% dos eixos A-WALL alinhados a ≤2 cm do layer Paredes). 7.257 blocos criados no 1º PAVIMENTO em 14 fiadas z=1..261 cm (passo 20), simbolos B39 4269 / B34 1716 / B19 288 / B54 195 / C09 492 / C04 297; 0 colisões; 54 compensadores espelhados NO LUGAR. RECRIAÇÃO: lote substituído por exatamente 7.257, 0 órfãs, 0 posições duplicadas (idempotência PASS). Antes do fix 12.1 a primeira criação deixara 54 cópias espelhadas órfãs (7.311 no doc), removidas com prova.",
    "Documento de teste NÃO salvo (IsModified=True) — decisão do usuário."
  ],
  "decisions_taken": [
    "Projeto humano prevalece sobre as respostas rápidas (instrução do usuário): 11.10 revisada (degradar antes de deixar sem modular).",
    "Rede de rejeição em par DESLIGADA por padrão: benchmark TGD prova que ela destrói amarrações legítimas; o gate duro de colisão do preflight permanece.",
    "Fileira de B34 (evidência humana) mantida atrás de flag com DEFAULT na regra #2 documentada: trocar regra documentada do usuário sem o usuário presente não é decisão do agente — registrada como pendente com as duas medições.",
    "Auditor não foi tocado: ele concorda com o humano (0 juntas corridas humanas com vãos reais).",
    "Nenhum baseline/reference/threshold alterado; nenhum skip/xfail; nenhum merge na main."
  ],
  "decisions_pending": [
    "PREFER_B34_ROW_OVER_STACKED_COMPENSATORS: ligar (projeto humano; 494 cm = 9×B39 + 3×B34; TGD indiferente) ou manter a regra #2 (teto de 1 peça especial por trecho; 494 cm = 11×B39 + C09 C09 C04, que a própria seção 2 proíbe). As duas regras documentadas conflitam nesse comprimento.",
    "Reserva de canto por fiada (parede curta com canto nas duas pontas — 3 nós T de 99 cm em Butantã saem C09|C09; humano B34|B34).",
    "Filtro de paredes não estruturais no fluxo CAD→Walls (12/46 do layer 'Paredes' não são alvenaria).",
    "Salvar ou descartar o doc 'butanta testes' (7.257 blocos + CAD corrigido, não salvo).",
    "Pacote beta com o HEAD final instalado em teste-perf.pushbutton: um clique real (CPython) nas 34 paredes; PR e merge."
  ],
  "next_steps": [
    "Defeito 1 no gerador: escalonar o preenchimento contra a amarração (o humano usa corridas de B34 para mudar a fase).",
    "Reserva de canto por fiada; medir com as três paredes de 99 cm de Butantã.",
    "Um clique real no botão com o pacote do HEAD (CPython) nas 34 paredes: Tela 1 → Tela 2, medir tempos e comparar com os 7.257.",
    "Estender a comparação humana aos demais pavimentos (2º é matriz dos clones) e ao TORRE EASY."
  ],
  "references": [
    {
      "path": "docs/checkpoints/2026-09-10-revit-scale-autofix.md"
    },
    {
      "path": "docs/checkpoints/2026-09-10-butanta-human-comparison.md"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-ref-1pav-blocks.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-solver-vs-human.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-scale-autofix-axes.json"
    },
    {
      "path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"
    },
    {
      "path": "tests/scale_bench.py"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-11-bisect-tgd.txt"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-11-bisect-tp1.txt"
    }
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
| 179 | **FALHA** (49 colisões) | **ok** | 10.479 peças, 4,2 s (HEAD final); 4 ifail / 6 colisões de solver nos eixos degenerados do CAD já existiam antes |

## Comparação com o projeto humano (Butantã, 34 paredes, vãos reais)

| Métrica | Humano | Solver antes | Solver depois |
|---|---|---|---|
| Paredes reprovadas pelo auditor do repo | 2 | 12 | **5** com a fileira de B34 ligada / 12 no default (regra #2) |
| Faixas de compensador | 0 | 7 | **0** (flag ligada) / 7 (default) |
| B34 / C09 (fiadas 0..12) | 1615 / 242 | 846 / 739 | **1557 / 467** (flag ligada) / 846 / 739 (default) |
| Parede de 494 cm | B34 + 9×B39 + B34 B34 | 11×B39 + C09 C09 C04 | 9×B39 + 3×B34 (flag ligada) / igual ao antes (default) |
| Nós T com espaço | B54\|B34 (30/34) | igual | igual |
| Nós L | B34\|B34 (13/13) | igual | igual |

## Regressão consolidada

Preenchido ao término da execução (ver commit seguinte a este checkpoint).
