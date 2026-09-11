# Fechamento da etapa — decisões aprovadas pelo usuário (regra B34, reserva de canto por fiada, filtro por layer estrutural, bancada salva, teste real no botão)

```json
{
  "date": "2026-09-11",
  "scope": "current",
  "branch": "claude/revit-scale-autofix",
  "head": "198a639ec3c4d351a51491b45cd5f88c37f85905",
  "base": "41086e43b6b56102ce736b816debad04749fa4bf",
  "main_observada": "21576ee3d0826f362bce1038131603bd2ccf5dc1",
  "pr": "not-created",
  "veredito": "TESTE REAL PASS (16/16 gates, duas criações de 8.399 blocos, idempotente) — decisões A/B/C implementadas; regressão consolidada final e PR: ver seções abaixo.",
  "objective": "Fechar a base do solver antes de verga/contraverga/canaletas: implementar as quatro decisões aprovadas pelo usuário (regra geral da fileira de B34; reserva de canto por fiada; filtro de paredes não estruturais por layer de referência; salvar a bancada) e provar o fluxo real completo BOTÃO → Tela 1 → análise → solver → Tela 2 → criação → UI, no CPython do pyRevit, com as 34 paredes de Butantã.",
  "changes": [
    "A — wall_stepper.py: MAX_SPECIAL_BOND_PER_TRECHO passa a teto de PREFERÊNCIA (regra geral: B39 → B19 em ponta aberta → até 1 B34 → 1 compensador → FILEIRA de B34 → B19 forçado → 2+ compensadores); flag PREFER_B34_ROW_OVER_STACKED_COMPENSATORS removida; bloco 5b incondicional. Regras seção 2 reescrita; testes reescritos para a regra revisada (test_fill_prefers_b34_row..., test_peca_de_amarracao_nao_vira_enchimento_em_trecho_longo, test_tie_parity_local_search).",
    "B — wall_stepper.py: CORNER_RESERVE_PER_COURSE (regra 11.14) — _wall_reserved_range_ft(course=, solved=), _node_lays_bond_on_wall_in_course, _corner_bond_blocking_courses(solved=), solve_l_corner(solved=), solve_all_intersections passa o que já resolveu. Testes tests/test_corner_reserve_per_course.py (antes/depois, invariância a 3 ordens, toco do CAD, controle).",
    "C — wall_pairing.py: clip_axes_to_reference_lines + REFERENCE_LAYER_MIN_COVERAGE=0.30 + REFERENCE_LAYER_LATERAL_SLACK_FT; wall_modeling.py: opção 'Layer de referência estrutural (opcional)' na Tela de Configuração, aplicada em main() após find_wall_pairs, lembrada nos defaults; relatório no output. Regras seção 49. Testes tests/test_reference_layer_filter.py (46 paredes reais × faces reais do projeto pronto).",
    "Infra do teste real — wall_modeling.py: _select_existing_walls_for_modulation oferece usar as Walls já selecionadas (yes/no) antes do PickObjects.",
    "Bancada: 'butanta testes' salvo como C:/Users/twitc/Desktop/CIVIX/BUTANTA_BENCH_SCALE_AUTOFIX.rvt (SaveAs; o original nunca foi sobrescrito; o humano BUTANTÃ R08_LT continua read-only).",
    "Lote persistente (seção 50) — wall_modeling.py: carimbo MODULACAO_AUTOMATICA|parede=<UniqueId>|lote=<etiqueta> em Comentários de cada instância; _discover_previous_lot substitui o lote anterior das mesmas Walls numa sessão nova; avisos engolidos nas transações de criação. Causa do travamento 1 do teste real. Testes tests/test_block_lot_persistence.py."
  ],
  "tests": [
    "Focados (A+B+C+infra): 384 passed / 3 failed no primeiro giro — os 3 eram os controles node_fill t3/t4/t20 (a geração deixou de produzir a junta nó|fill em qualquer fixture/corpus: v_off == v_on medido em TP1 16/16 e TGD 0/0; T_MEIO/X_MEIO/L_LIVRE 0/0) — adaptados e verdes (t20 no corpus TP1: 2 passed). test_corner_reserve_per_course (7), test_reference_layer_filter (4), test_fill_prefers_b34_row (5), test_scale_autofix_rules (13), test_free_end_reserve (3), test_tie_parity_local_search, test_beta_atomic_creation, test_analyze_sincrono_sem_thread: verdes.",
    "Baselines com A+B (tests/regression/test_benchmark_baselines.py): torre_easy_lo_r00_tgd PASSA (nenhuma regressão de categoria nem crítica — a histórica compensators 52→5x desaparece); torre_easy_lo_r00_tp1 só a histórica JUNCTION_MISSING_BINDING 8→9.",
    "11.14 × TIE_PARITY_LOCAL_SEARCH=True em Butantã: 0 colisões, 3 reprovadas (só os tocos), 1 flip — a combinação que na tentativa da sessão fork dava 7 colisões.",
    "Sessão fork (ee34c2a): regressão consolidada no HEAD 2405969 = 3 failed / 1076 passed (2 históricas + guarda de fonte por edição concorrente, verde isolada).",
    "test_block_lot_persistence (5) + test_beta_atomic_creation: 33 passed.",
    "Regressão consolidada final no HEAD desta etapa: ver seção 'Regressão consolidada'."
  ],
  "known_failures": [
    "Butantã 34 paredes (CAD como está): 4 reprovadas pelo auditor — 8079861/62/63 (toco de 34 cm do CAD através da vizinha; com o filtro da seção 49 seriam aparadas e passam) e 8079838 (junta corrida de preenchimento, defeito 1). Com os quatro tocos aparados: 1.",
    "Torre 179 eixos: 12 paredes reprovadas (defeito 1), 270 trechos não modulares (Etapa 3B), 6 colisões de solver nos eixos degenerados do CAD (pré-existentes), preflight ok.",
    "Históricas do benchmark preservadas: TP1 JUNCTION_MISSING_BINDING 8→9 (idêntica a 8cdd33f); TGD agora passa. Nenhum baseline regravado.",
    "O DWG '1 PAV' não tem as faces estruturais (layer ARQ-STR-BLOCO vazio): o filtro da seção 49 não pode ser exercitado neste projeto sem importar o desenho estrutural."
  ],
  "physical_deltas": [
    "butanta testes → SaveAs C:/Users/twitc/Desktop/CIVIX/BUTANTA_BENCH_SCALE_AUTOFIX.rvt (46 Walls, 7.257 blocos do lote anterior no 1º PAVIMENTO, CAD 1 PAV reescalado). Original 'butanta testes.rvt' e humano BUTANTÃ R08_LT intocados em disco.",
    "Janela 'Tela 2' órfã de uma execução CAD→Walls anterior (46 paredes, layer Estrutura _1_) fechada via UI antes do teste real.",
    "TESTE REAL run 1 (pacote c44c7d9): 8.399 instâncias criadas por cima do lote anterior de 7.257 e Commit parado numa caixa modal com 13.940 avisos — cancelada, modelo restaurado a 7.257 (evidence/2026-09-11-teste-real-travamento-1.json). Carimbo retroativo dos 7.257 via MCP (evidence/2026-09-11-bench-retro-stamp.json).",
    "TESTE REAL run 2 (pacote 198a639): lote de 7.257 substituído por 8.399 (16 fiadas), recriado idempotente 8.399 → 8.399, lote único 20260911-134117, 0 duplicatas, 0 sem carimbo, 34 paredes donas; bancada salva (evidence/2026-09-11-teste-real-run2.json)."
  ],
  "decisions_taken": [
    "Regra da fileira de B34 revisada como regra geral (teto de preferência) em vez de flag — decisão do usuário.",
    "Reserva de canto por fiada: a investigação via MCP mostrou que o humano NÃO reserva o canto de forma diferente; a diferença nos 3 T de 99 cm era (a) o toco de 34 cm que o CAD arquitetônico desenha através da vizinha (não é alvenaria no projeto pronto) e (b) a medição de espaço do solver, que reservava 34 cm nas duas fiadas na outra ponta. A regra 11.14 corrige (b) de forma geral; (a) é tratado pelo filtro por layer de referência (seção 49).",
    "Filtro de paredes não estruturais: nenhuma propriedade intrínseca no doc de teste separa as 12 das 34 (mesmo tipo/espessura/altura/topologia); o critério confiável é a cobertura pelo layer de alvenaria estrutural do desenho do projeto pronto (0,42–0,99 × 0,03–0,08). Implementado como mecanismo geral opcional; no DWG deste projeto o layer estrutural está vazio (o erro de layer), então o filtro só se aplica quando o desenho estrutural for importado."
  ],
  "decisions_pending": [
    "TIE_PARITY_LOCAL_SEARCH (Etapa 7, sessão fork): default False; evidência de que ligada melhora TGD (POSITION_OVERLAP 29→23, PRISM 961→262) e TP1 (PRISM 260→192) ao custo de 43 s (Butantã) / 617 s (TP1). Decisão normativa/performance pendente.",
    "Defeito 1 (junta corrida de preenchimento, 8079838 e as 12 da Torre): escalonar preenchimento contra amarração — próxima etapa.",
    "Importar o desenho estrutural na bancada para exercitar o filtro da seção 49 no fluxo CAD→Walls real."
  ],
  "next_steps": [
    "Regressão consolidada final; PR para a main (sem merge)."
  ],
  "references": [
    {"path": "docs/checkpoints/2026-09-11-revit-scale-autofix-final.md"},
    {"path": "docs/checkpoints/evidence/2026-09-11-bench-prestate.json"},
    {"path": "docs/checkpoints/evidence/2026-09-11-teste-real-travamento-1.json"},
    {"path": "docs/checkpoints/evidence/2026-09-11-bench-retro-stamp.json"},
    {"path": "docs/checkpoints/evidence/2026-09-11-teste-real-run2.json"},
    {"path": "tests/test_block_lot_persistence.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/test_corner_reserve_per_course.py"},
    {"path": "tests/test_reference_layer_filter.py"},
    {"path": "tests/test_fill_prefers_b34_row_over_stacked_compensators.py"}
  ]
}
```

## Resultado do teste real (botão CPython, 34 paredes de Butantã)

Fluxo do usuário final, disparado com `UIApplication.PostCommand` do próprio botão
`teste-perf` (mesmo caminho do clique: loader `Script.py` no engine CPython do
pyRevit, pacote verificado `198a639`) e dirigido pelas janelas reais
(Win32/UIA), na bancada `BUTANTA_BENCH_SCALE_AUTOFIX.rvt` com as 34 Walls de
alvenaria pré-selecionadas.

| Etapa | Tempo | Observação |
|---|---|---|
| Botão → diálogo de modo | 1 s | "Utilizar paredes existentes" |
| Seleção → Tela 1 (coleta de 44 aberturas) | 5,1 s | alerta "34 paredes já selecionadas" → Sim |
| Tela 1 → Tela 2 | 1,6 s | "Iniciar Modulação das Paredes" |
| Solver (Lançar Blocos – calcular) | ~15 s | 7.215 candidatos, 0 colisões, 0 vãos violados, 4 reprovadas |
| Criação 1 (automática após o solver) | 319,8 s | procura lote carimbado 1 s; exclusão dos 7.257: 1,9 s; `create_building_blocks` 317,8 s (NewFamilyInstance 32,8 ms × 8.399; RotateElement 6,5 ms × 4.569; Mirror 54); **Commit 8,65 s** |
| Finalização da UI | imediata | modal "Resumo final da Etapa 2", botão "criar" reabilitado, 425 peças marcadas |
| Criação 2 (clique manual, idempotência) | 330,8 s | exclusão dos 8.399: 2,1 s; 8.399 criados; Commit 10,1 s |
| **Total até o fim da criação 1** | **~6,5 min** | |

Gates: **16/16 PASS** — planejado = criado (8.399 = 8.399, 0 falhas, duas vezes);
0 posições duplicadas; 0 órfãos (8.399 carimbados = 8.399 no doc, 54 espelhados
no lugar); 0 colisões; 0 invasões de vão; 34 paredes donas; recriação substitui
N→N (lote único `20260911-134117`); sem crescimento 2N (7.257→8.399 é 14→16
fiadas, altura 3,20 m; 8.399→8.399); paridade Revit × offline a 16 fiadas:
8.399 = 8.399 com as mesmas 4 reprovadas.

Equivalência com a criação via MCP: 36,9 ms/instância (IronPython, 7.257) ×
37,8–39,1 ms/instância (CPython, 8.399) — mesmo gargalo (`NewFamilyInstance`
87 % do laço), Commit 9–10 s.

**Travamento 1 (pacote c44c7d9) — capturado antes de reiniciar:** último
estágio "Transaction.Commit() — regenerando" congelado; thread da UI parada
numa caixa modal do Revit (`#32770`, "0 Erros, 13.940 Avisos: instâncias
idênticas no mesmo local"), CPU 0,2 s/10 s, `Responding=True`; ExternalEvent
`_PostCreationEventHandler` (ação create) dentro da Transaction de criação;
planejado 8.399, criados 8.399 (não confirmados), modelo com 7.257 do lote
anterior por baixo. Causa-raiz: lote anterior só conhecido por memória → seção
50 (carimbo de propriedade + descoberta). Cancelar restaurou 7.257.

## Regressão consolidada

PENDING
