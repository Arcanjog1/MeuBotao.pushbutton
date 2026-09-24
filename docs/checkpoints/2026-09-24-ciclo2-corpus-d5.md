# Ciclo 2 (D5): por que o SCRIPT modula 46 eixos e MCP/HUMANO 34 — regra 49 no fluxo de paredes existentes e corpus da RUN (49.1)

```json
{
  "date": "2026-09-24",
  "scope": "current",
  "branch": "main",
  "base": "2ed0410a1675c06dcd363e89a9754856067689b9",
  "head": "74cf2df1daf8a263abf8ef07722e9be8927504aa",
  "pr": "not-created",
  "objective": "Ciclo 2 apos a comparacao forense: provar por que o SCRIPT (TESTE PR49) processou 46 eixos enquanto MCP (butanta testes) e HUMANO (BUTANTA R08) tem alvenaria em 34; caracterizar as 12 diferencas sem trata-las como erradas a priori; encontrar (ou refutar) uma regra geral e verificavel; so entao alterar a selecao ANTES do solver; registrar em toda RUN DETECTED/SELECTED/EXCLUDED com motivo. Sem hardcode, sem baseline regravado, sem ciclo 3.",
  "changes": [
    "MOTOR (nuvem/core/wall_modeling.py): `select_existing_axes_by_reference_layer` aplica a regra 49 (cobertura pelas faces do layer de referencia estrutural, mesma funcao e limiar do fluxo CAD -> Walls) ao fluxo 'Utilizar paredes existentes', SO' descarte (trim=False: a Wall e' do usuario, nunca e' encurtada), reindexando walls_to_create/created_walls_by_axis/wall_ids; `corpus_selection_record`, `_corpus_report_lines`, `_wall_axis_key`, `_wall_id_int`, constantes CORPUS_RULE_REFERENCE_LAYER / CORPUS_RULE_NONE. No fluxo de paredes existentes: prompt opcional (`_ui.reference_layer_prompt`) -> pick do import -> `extract_lines_by_layer` -> escolha do layer -> selecao ANTES das aberturas/grafo/solver; run_setup leva reference_layer, detected_axes e corpus_selection (lembrado nos defaults). No fluxo CAD -> Walls o mesmo registro nasce do relatorio da secao 49. `_execute_solve` copia `corpus_selection` para o solve_result; `_format_block_solve_report` imprime 'CORPUS DA RUN: DETECTED_AXES= SELECTED_AXES= EXCLUDED_AXES= regra= layer=' e uma linha EXCLUDED por eixo (axis_key, wall_id, reason, rule_id, source_layer, length, coverage).",
    "ENGINE (nuvem/core/engine/wall_pairing.py): `clip_axes_to_reference_lines(..., trim=True)` - com trim=False classifica sem aparar (report['trimmed'] vazio, cobertura identica).",
    "UI: `reference_layer_prompt` (ui_components.py, dialogo explicito: 'Sem layer - modular todas' / 'Escolher import e layer' / cancelar, lembra o ultimo layer); `corpus_lines` (ui_state.py) no report_text: 'Eixos: N detectados . M modulados . K excluidos (regra ...)' + uma linha por exclusao.",
    "REGRAS: secao 49.1 nova (evidencia das 12, por que nao ha regra automatica a partir da Wall, a regra geral, o registro do corpus, o proibido).",
    "TESTES: tests/test_corpus_selection_paredes_existentes.py (8): regra geral nas 46 reais (34/12, sem aparar, reindexacao, margem >= 0,10), campos de cada exclusao, sintetico entra/sai/limitrofes (0,25 sai, 0,35 entra intacto), mesmo criterio do CAD, sem referencia = 46/46/0 registrado, relatorio + UI, corpus no solve_result antes do solver (ordem no fonte), ausencia de hardcode (varredura por tokenize do codigo de producao: nenhum ElementId do corpus, EXCLUDED_IDS, wall_id ==, project ==, nome do projeto)."
  ],
  "tests": [
    "Novos: tests/test_corpus_selection_paredes_existentes.py 8 passaram (+ tests/test_reference_layer_filter.py 4). Suite completa sem tests/regression (arvore final): 1710 passaram, 1 pulado, 1 falhou - tests/test_perf_trace_stall_sampler.py (historica, identica na main). tests/regression (arvore final, 19 min): 146 passaram, 2 falharam - identicas a main 2ed0410 (TP1 JUNCTION_MISSING_BINDING 8->9 historica; TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 do ciclo 1, reclassificacao). Secao 48, canaleta, encontros, tolerancias fisicas, aberturas e corpus fazem parte da suite completa."
  ],
  "known_failures": [
    "tests/test_perf_trace_stall_sampler.py (historica). tests/regression TP1 8->9 (historica). tests/regression TGD V2 86->92 (ciclo 1; baseline nao regravado, decisao humana). O clique humano com o prompt do layer de referencia nao foi exercitado (acao humana); o caminho foi provado pela API na copia CICLO2 e pelos testes. A copia CICLO2_butanta_testes.rvt ficou aberta sem salvar; nenhum dos tres RVTs de referencia foi tocado."
  ],
  "physical_deltas": [
    "SOLVER: nenhum - a mudanca e' de SELECAO do corpus antes do solver (46 -> 34 eixos quando o usuario aponta o layer de referencia). Sem layer, nada muda.",
    "BANCADA OFFLINE (46 eixos reais, NONE, 280 cm, 14 fiadas, motor da secao 78) ANTES (46 detectados = 46 selecionados) -> DEPOIS (46 detectados, 34 selecionados pela regra 49 - conjunto identico ao dos 34 do MCP, conferido por geometria): NON_MODULAR_UNRESOLVED 96 -> 0; EMPTY_LENGTH_CM (34 eixos x fiadas 0-11) 9577 -> 30; JAMB_MISSING 154 -> 64; BLOCK_COUNT 8194 -> 7416; match exato vs MCP 45,6% -> 54,7% (<= 5 cm 48,5% -> 57,5%); vs SCRIPT real 94,2% -> 83,2% (o SCRIPT tem os 46); compensadores 1006 (12,3%) -> 864 (11,7%); B34 planejadas invadindo porta 11 -> 0 (preflight ok, 0 pulos).",
    "REVIT (copia CICLO2_butanta_testes.rvt, caminho do PRODUTO com o import preparado na copia): 46 detectados -> 34 selecionados -> 12 excluidos (cobertura 0,033-0,078; coverage e reason no relatorio: CORPUS DA RUN: DETECTED_AXES=46 SELECTED_AXES=34 EXCLUDED_AXES=12 regra=REGRA_49_REFERENCE_LAYER_COVERAGE layer=ARQ-STR-BLOCO). Solver: 7397 candidatos, 0 non_modular, 0 NON_MODULAR_UNRESOLVED, preflight ok, 0 invasoes, 0 pulos. Criacao: 7397 planejadas, 7397 criadas, 0 falhas, 0 puladas, 0 amarracoes nao resolvidas, `structurally_resolved = True` (no ciclo 1, com 46: 8184 criadas, 11 puladas, 96 trechos, False). Regua sobre o modelo criado (34 eixos x fiadas 0-11): EMPTY_LENGTH_CM 9577 -> 30 (SCRIPT real 18666; MCP 473; HUMANO 3064); JAMB_MISSING 154 -> 65 (MCP 59; HUMANO 97); invasoes 0; bonecas 0/0/0/0 cm e 4,7/5,0/2,0/2,0 pecas por fiada (iguais ao ciclo 1). Compensadores 986 (12,0%) -> 835 (11,3%) (MCP 459 = 5,3%; HUMANO 487 = 7,3%). B34 planejadas invadindo porta 11 -> 0: o encontro que as gerava (paredes extras chegando em T na parede da porta) deixou de existir no corpus.",
    "D2 e D3 NAO desaparecem com o corpus correto (medido na copia CICLO2, mesma regua de nos do forense; padrao por fiada 0-11, B = amarracao, x = peca sem amarracao, - = vazio): no 51 (T, principal 8284515, chegada 8284580) ANTES xxxxxxxxxxxB / DEPOIS xxxxxxxxxxxB (pilar 1570-1624 com B19|B19 em 11 fiadas nos dois; MCP e HUMANO BBBBBBBBBBBx com B54 alternado); nos 20 e 26 (T na 8284502) ANTES BBBBxxxxxxxB / DEPOIS BBBBxxxxxxxB (MCP tudo B; HUMANO BBBxBBBBBBBx); no 28 (T na 8284554) ANTES BBBBxxxxxBBB / DEPOIS BBBBxxxxxBBB (MCP tudo B). Sao defeitos do solver no proprio corpus de 34 (fiadas 4-10 sem amarracao no T sob/entre aberturas e pilar fechado com B19|B19 em vez de B54), nao consequencia das 12 - ficam para um ciclo proprio, sem correcao aqui.",
    "BENCHMARK TGD V2 / TP1 apos D5: identicos a main 2ed0410 (a mudanca nao toca o solver): TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 92 (main antes do ciclo 1: 86), COVERAGE_MISSING_ROW 136 (142), COVERAGE_GAP_IN_ROW 1153 (1275), COVERAGE_PARTIAL_WALL 24 (32), categoria compensators 63 (62); TP1 JUNCTION_MISSING_BINDING 9 (8, historica). A piora de compensadores do ciclo 1 e do TGD (corpus proprio do benchmark) - nao era induzida pelas 12 paredes do BUTANTA; no BUTANTA a taxa cai 12,0% -> 11,3% com o corpus correto."
  ],
  "decisions_taken": [
    "As 12 nao sao 'erradas': sao paredes do layer arquitetonico sem alvenaria estrutural no projeto pronto (evidencia: 0-3 pecas no HUMANO, so' a amarracao da parede que as cruza; piso, viga transversal e ferros de graute nas posicoes, nunca fiada). Entram no SCRIPT porque o fluxo de paredes existentes recebe a selecao do usuario (46 Walls) sem filtro; o MCP recebeu 34 por criterio de bancada (>= 20 blocos no humano).",
    "Nenhum atributo da Wall nem layer alinhado do doc separa os dois grupos (8079849 e' alvenaria e suas gemeas de 224 cm nao) -> nenhuma heuristica automatica a partir da Wall. A unica regra geral e verificavel e' a da secao 49 (TP 34 / TN 12 / FP 0 / FN 0, margem >= 0,10), que exige um import de referencia alinhado - escolha explicita do usuario. O doc de teste tem o desenho estrutural a 1/10 e deslocado (erro de layer): preparado na COPIA (escala x10 + reposicao pelo envelope), a regra reproduz 34/12 a partir dos dados do proprio documento.",
    "Nunca aparar Wall existente; nunca excluir sem registro; nunca ID/nome/coordenada/contagem como criterio."
  ],
  "decisions_pending": [
    "Corrigir o import '1 PAV' no doc de teste real (escala e posicao) e usar o layer de referencia no clique humano - a copia CICLO2 mostra o fluxo; o doc original nao foi tocado.",
    "Baseline TGD V2 (regua) continua sem regravar; compensadores (D9) nao corrigidos.",
    "D2 (no 51) e D3 (nos 20/26/28): ver physical_deltas - o que nao desapareceu com o corpus correto fica para um ciclo proprio."
  ],
  "next_steps": [
    "Ciclo 3 somente com nova autorizacao (D6 verga/contraverga, D9-D13, D14, 3B, D16)."
  ],
  "references": [
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_pairing.py"},
    {"path": "nuvem/core/ui_components.py"},
    {"path": "nuvem/core/ui_state.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/test_corpus_selection_paredes_existentes.py"},
    {"path": "tests/test_reference_layer_filter.py"},
    {"path": "docs/checkpoints/evidence/2026-09-10-butanta-cad-lines.json"},
    {"path": "docs/checkpoints/2026-09-11-fechamento-decisoes-aprovadas.md"},
    {"path": "docs/checkpoints/2026-09-23-ciclo1-tolerancias-fisicas.md"}
  ]
}
```

## 1. Por que 46 e por que 34 (COMPROVADO)

- **SCRIPT (TESTE PR49)**: um único lote `20260923-122204` com 7 760 peças carimbadas em **46** Walls distintas — fluxo "Utilizar paredes existentes", seleção do usuário = todas as Walls do doc (criadas do layer `Paredes` do CAD arquitetônico), sem filtro (a seção 49 só existia no fluxo CAD → Walls).
- **MCP (butanta testes)**: lote `20260922-225600`, 8 693 peças em **34** Walls — o harness (`r_butanta.py`, `cfg["ids"]`) recebeu a lista de `masonry34.py`: paredes com ≥ 20 blocos no projeto humano. Critério de bancada, não de produto.
- **HUMANO**: nas 12 posições, 0 blocos (8284575: 3 = amarração da parede que a cruza); ao longo dos eixos só há `Pisos/Floor`, `TQS - Viga retangular1` transversal sob a parede vizinha (fração 0,14–0,26 do eixo, z −80..0) e `1 FERROS Ø10` do pilarete no encontro — nenhuma fiada, nenhum outro sistema de parede.

## 2. Matriz 34 × 12 (o que NÃO discrimina)

| atributo | 34 incluídas | 12 extras | discrimina? |
|---|---|---|---|
| tipo / espessura / altura | `Parede 14cm` / 14 / 340 | idem | não |
| comprimento | 86–2 929 (inclui 224, 209, 264) | 179–344 (inclui 224) | não (8284574 = 224 cm incluída) |
| aberturas hospedadas | 22 sem, 12 com | 12 sem | não |
| pontas livres | 28 sem, 6 com | 11 com uma, 1 com duas | não (6 incluídas têm ponta livre) |
| nós T recebidos | 15 com 0 | 12 com 0 | não |
| layers alinhados do doc (`Paredes`, `Estrutura _1_`, `Substrato _2_`, `Pisos`, `ARQ-STR-PIL`, `ARQ-STR-VIG`) | faces 0,37–1,00 | faces 0,92–0,97 | não |
| **cobertura pelas faces `ARQ-STR-BLOCO` (seção 49)** | **0,42–0,98** | **0,03–0,08** | **SIM** (FP 0 / FN 0, limiar 0,30, separa em 0,08–0,41) |

Hipóteses testadas nas 46: "ponta livre" → 6 FP; "ponta livre ∧ sem abertura ∧ 179–344 cm" → 1 FP (8284574); "≥ 20 blocos no humano" → só existe na bancada. Nenhuma foi implementada.

## 3. Origem CAD

Os cinco imports do doc de teste e seus layers foram lidos ao vivo (somente leitura): `8079028` (`151.06-ARQ-EX-0103-TIP-R02`, alinhado: `Paredes` 2 749, `Estrutura _1_` 1 111, `Substrato _2_` 1 915), `7514688` (estrutural: `ARQ-STR-PIL` 146, `ARQ-STR-VIG` 137, `ARQ-STR-BLOCO` 32 = só o shaft), `7097743` (`1 PAV`: `A-WALL` 4 857, `ARQ-STR-BLOCO` 11 501 — **a 1/10 da escala, envelope 163 × 293 cm em x ≈ 494 m**, escala do tipo 1,0). O layer arquitetônico `Paredes` forma as 46 (faces 0,63–1,00 em todas); o layer estrutural das faces de bloco existe no documento mas não está na escala/posição das paredes — é isso que impede a regra 49 de agir sozinha.

## 4. Validação no Revit (cópia)

`CICLO2_butanta_testes.rvt` (cópia em disco de `butanta testes.rvt`; os três RVTs de referência não foram tocados — `IsModified` idêntico antes/depois). Na cópia, o import `1 PAV` foi preparado como um humano faria (escala do tipo ×10, reposição pelo envelope: 11 499 linhas, peça máxima 54 cm, envelope 0..1629 × 0..2929) e o caminho do PRODUTO rodou: `_build_existing_walls_selection` (46) → `extract_lines_by_layer` → `select_existing_axes_by_reference_layer` → **46 detectados, 34 selecionados, 12 excluídos (cobertura 0,033–0,078)** → solver NONE 280 cm → criação. Ver physical_deltas.
