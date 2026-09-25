# D6: verga e contraverga como reforço ESTRUTURAL da abertura, independentes da estratégia CHANNEL (seção 80)

```json
{
  "date": "2026-09-25",
  "scope": "current",
  "branch": "main",
  "base": "bf0c7d06eb2b4a06cf20622245fe071f4e9dc1e9",
  "head": "8df42be396cb4c73115930906e48b2c0c6549399",
  "pr": "not-created",
  "objective": "Decisao do usuario (2026-09-25) sobre o D6: verga e contraverga passam a ser requisitos estruturais da modulacao, independentes da estrategia CHANNEL/NONE. NONE = 'Sem reforco adicional' (sem a estrategia ADICIONAL CHANNEL), sem trocar o default, sem exigir escolha manual e sem ligar o pacote CHANNEL (51.9, 51.14, 58.2, 68, 71, 72, 60-65). Extrair SO' verga, contraverga e a classificacao estrutural da canaleta de abertura, reaproveitando a implementacao provada do CHANNEL; topo fora da grade -> LINTEL_UNRESOLVED; contraverga impedida por amarracao -> SILL_REINFORCEMENT_UNRESOLVED (regra 75 absoluta); sem minimo novo de apoio; D16 so' registrado.",
  "changes": [
    "MOTOR (nuvem/core/wall_modeling.py): OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = True. Com strategy=None, _apply_opening_reinforcement chama _apply_opening_structural_reinforcement: vazado menor (secao 52) decidido ANTES da conversao; plan_channel_reinforcement(..., free_to_top=[]) com a politica saneada (51.6/51.7 nunca religadas); validate_channel_reinforcement; reauditoria com o catalogo logico de canaletas; fonte unica candidates/collisions; gate channel_as_junction_bond; violacoes do vazado menor relidas nas fiadas finais. Nenhum solver novo, nenhuma dimensao nova. O CHANNEL ganha so' o rastreio.",
    "RASTREIO (os dois caminhos): result['opening_structural_trace'] por abertura (opening_id, wall_id, type DOOR/WINDOW, lintel_*/sill_*: required, status, course, codes, start/end e run_id/run_opening_indices da corrida, left/right_support, bearing, support_classification, stopped_by_junction, junction_ids, course_grid_cm, reason, requires_human_review; strategy), result['channel_stopped_by_junction'] (junction_id, opening_id, role, side, remaining_support_cm, bearing_cm, reason RULE_75) e opening_structural_summary. Status LINTEL_CREATED/NOT_REQUIRED/UNRESOLVED e SILL_REINFORCEMENT_*; motivos NO_MASONRY_ABOVE_REACHES_WALL_TOP, FREE_TO_TOP_PASSAGE_51_9 (so' CHANNEL), HEAD/SILL_OFF_GRID_51_8 (com a grade real), HEAD/SILL_IN_COURSE_RULE_48, RULE_75_TIE_OVER_SPAN, CHANNEL_FAMILY_MISSING, SUPPORT_ACTUAL_ERROR, NO_SILL_OPENING_TOUCHES_BASE e SILL_WITHIN_LOWEST_COURSE_10_4 (peitoril dentro da primeira fiada = porta).",
    "HOST: familias de canaleta conferidas sem bloquear no NONE (relidas enquanto faltar; altura conferida contra a dos blocos); indisponiveis -> nenhuma conversao e *_UNRESOLVED (CHANNEL_FAMILY_MISSING). _execute_solve passa opening_structural_channel_available, preenche os ElementIds e reconcilia o rastreio com o plano de materializacao (_opening_trace_apply_materialization: corrida com peca pulada pela regra 48 vira *_UNRESOLVED REGRA_48_<regra>), tambem no gate de criacao. create_result: unresolved_opening_reinforcement (entra em structurally_resolved) e opening_reinforcement_review (51.4 ACTUAL_ERROR - so' aviso, sem minimo novo). Assinatura BETA com identidade estavel da canaleta; cache NONE sem o escopo da secao 80 e' rejeitado. Microajuste 66: SUPPORT_BELOW_POLICY nao e' portao no reforco estrutural.",
    "UI (ui_components, ui_state, ui_preview_panel): 'Sem reforco adicional'; ajuda e preview dizem que verga/contraverga em canaleta existem nas duas opcoes; revisao lista verga/contraverga NAO resolvida, criada sem assentamento e canaleta nao criada; a criacao avisa (sem bloquear) quantas ficaram sem solucao.",
    "REGRAS: secao 80 (decisao, fronteira de responsabilidades, implementacao, status, campos, regra 75, host/UI, medido) e 80.1 (revisao adversarial); nota datada na 78 (a lista 'so' CHANNEL' esta' superada) e na 51.",
    "TESTES: tests/test_opening_structural_reinforcement.py (53) - porta/janela NONE e CHANNEL, espelhamento, vao ate' o topo, passagem (51.9 so' no CHANNEL; NONE cria verga na fiada 11 sobre o vao), topo fora da grade, canto L 55/56 (regra 75), T (parada RULE_75), canaleta nunca amarra (4 geometrias x 2 estrategias + prova nao vacua com os dois gates + planejador defeituoso no NONE), NONE nao liga 72/71/68/58.2/51.14/60-65/51.9 (espioes), NONE = motor sem a 80 + planejador (assinatura completa com rotacao), politica saneada, CHANNEL identico (assinatura completa), familias ausentes/altura divergente/relidas, host passa a disponibilidade, regra 48 (topo 221,3 / peitoril 99,7) e reconciliacao com a materializacao pelo _execute_solve, peitoril 0,6/1/10/19 = porta e 20 = contraverga, ACTUAL_ERROR na revisao sem virar pendencia, estado estrutural do CHANNEL so' com a 80, microajuste, sem hardcode, IronPython 2.7 por AST. Ajustados para o contrato novo: test_channel_reinforcement (LEGADO_HISTORICO desliga 79 e 80), test_channel_audit_fixes, test_channel_ui_and_family_gate, test_regra76_corpus_butanta, test_s74_corpus_butanta (reforco_estrutural=False no historico); tools/audit/s74_corpus.py ganha reforco_estrutural."
  ],
  "tests": [
    "tests/test_opening_structural_reinforcement.py + test_channel_reinforcement + test_channel_audit_fixes + test_channel_ui_and_family_gate: 141 passaram.",
    "Suite completa sem tests/regression (codigo final - inicio 11:16:21, ultima modificacao de codigo/teste 11:13:23): 1824 passaram, 1 pulado, 1 falhou - tests/test_perf_trace_stall_sampler.py (historica, a mesma da main).",
    "tests/regression (codigo final, 20 min): 145 passaram, 3 falharam - IDENTICAS a' main bf0c7d0 (mesmo arquivo rodado numa worktree da main): TGD V1 compensators 52->54 (ciclo 3), TP1 JUNCTION_MISSING_BINDING 8->9 (historica), TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 (ciclo 1). Medido a parte: TGD V1 compensators 54 -> 54, TGD V2 66 -> 66. Baseline nao regravado.",
    "Revisao adversarial do codigo (antes do commit): 33 achados, 30 confirmados e corrigidos (secao 80.1), 3 refutados.",
    "Revit: copia CICLO8 do 'butanta testes' (caminho do produto: import preparado, 46 -> 34 eixos, NONE, familias de canaleta conferidas): 7357/7357 criadas, 0 puladas, 0 falhas, 0 invasoes; 44/44 aberturas com opening_id e wall_id; bond_trace 690 RESOLVED (todas B34/B54) / 7 NO_FUNCTIONAL_JUNCTION / 3 NOT_GENERATED (cantos L 55/56); structurally_resolved = false (3 fiadas L + 3 verga/contraverga sem solucao). Os tres RVTs de referencia nao foram tocados."
  ],
  "known_failures": [
    "tests/test_perf_trace_stall_sampler.py (historica).",
    "tests/regression: TP1 8->9 (historica); TGD V2 86->92 (ciclo 1); TGD V1 compensators 52->54 (ciclo 3). Nenhuma nova.",
    "BUTANTA: 3 fiadas dos cantos L 55/56 sem amarracao (decisao do usuario: BOND_UNRESOLVED)."
  ],
  "physical_deltas": [
    "CHANNEL: assinatura fisica COMPLETA (posicao, codigo, rotacao, espelhamento, razao, no', comprimento de instancia + gates 76/76.1 + trechos) identica a' main bf0c7d0 no BUTANTA 34 eixos (7026 pecas, sha bc9331b8...) e no U dos cantos 55/56 (e11ca611...).",
    "NONE x main (bancada, 34 eixos): 321 pecas trocadas 1:1 (267 B39 -> U39, 52 B34 -> U34, 2 C04 -> U_CUT), TODAS dentro das corridas de verga/contraverga (fiadas 3, 4, 7, 11); 0 pecas mudam fora delas (nem rotacao). Revit CICLO8 x CICLO6b (main): 7034 pecas identicas com orientacao, 323 trocadas 1:1 (266 U39, 53 U34, 4 U_CUT no lugar de 2 C04 + 2 C09) nas cotas 61/81/141/221.",
    "AUDITORIA DAS 44 ABERTURAS (Revit, geometria de cada modelo): verga em canaleta HUMANO 40 / MCP 40 / SCRIPT antes 0 (bloco 44) / SCRIPT depois 42 (bloco 2 = topos 91 e 171); contraverga em canaleta 23 / 22 / 0 (bloco 23) / 22 (bloco 1 = canto L 55/56). OPENING MATCH por papel MCP/SCRIPT 2,3 % -> 95,5 %, HUMANO/SCRIPT 0 % -> 93,2 %; geometrico (5 cm) MCP 2,3 % -> 56,8 % (bancada 59,1 %), HUMANO 0 % -> 18,2 %. Categorias depois: 41 MATCH_ALL, 2 HUMAN_MCP_MATCH_SCRIPT_DIFF (portas de 156 cm: passagem livre 51.9 so' no CHANNEL), 1 MCP_SCRIPT_MATCH_HUMAN_DIFF (contraverga do canto 55/56, regra 75). Invasoes 0 em todos.",
    "STATUS (NONE): LINTEL 42 CREATED / 0 NOT_REQUIRED / 2 UNRESOLVED (8079027 topo 171, grade [161, 181]; 8079026 topo 91, grade [81, 101]); SILL 22 CREATED / 21 NOT_REQUIRED (portas) / 1 UNRESOLVED (8079026, RULE_75_TIE_OVER_SPAN, no' 48 do motor); 14 corridas paradas pela regra 75; 6 criadas sem assentamento num lado (8078987/8078988/8079016, verga e contraverga, junto aos T 22/28) -> revisao. CHANNEL: 40/2/2 e 22/21/1, 13 paradas.",
    "APOIO LATERAL (menor lado por papel em canaleta): SCRIPT depois mediana 29 cm, 6 < 4 cm, 8 < 19 cm (igual ao MCP); HUMANO mediana 29, 0 < 4, 6 < 19. Sem minimo novo.",
    "METRICAS QUE NAO PODIAM REGREDIR (bancada NONE): T 37/37, fiadas L sem amarracao 3, NON_MODULAR_UNRESOLVED 0, vazio 30 cm, invasoes 0, colisoes 0, canaleta como amarracao 0, compensador como amarracao 0. Compensadores 828 -> 826 (Revit 800 -> 796). Canaletas em regiao de no' pela auditoria geometrica: Revit 36 / MCP 33 / HUMANO 51 - as do SCRIPT e do MCP todas em nos das paredes arquitetonicas EXCLUIDAS do corpus; o HUMANO atravessa 3 T reais (20, 26, 28 - D16)."
  ],
  "decisions_taken": [
    "Decisao do usuario (2026-09-25): verga/contraverga estruturais nas duas opcoes; NONE = 'Sem reforco adicional'; default continua NONE; pacote CHANNEL nao ligado no NONE; sem minimo novo de apoio (nem 4 nem 19 cm); D16 so' registrado; TGD V1/V2 nao regravados.",
    "Implementacao: apoio sem assentamento (51.4 ACTUAL_ERROR) fica CRIADO com revisao humana e fora de structurally_resolved (tornar pendencia seria o minimo proibido). Peitoril abaixo do topo da primeira fiada = porta (10.4). No CHANNEL a mudanca de estado (verga sem solucao entra em structurally_resolved) e' intencional; as pecas nao mudam."
  ],
  "decisions_pending": [
    "Topos/peitoris fora da grade (51.8): 2 vergas e o canto 55/56 continuam UNRESOLVED com revisao humana (o HUMANO usa compensador deitado).",
    "D16: corridas paradas na amarracao de T vizinho (6 papeis sem assentamento num lado); o HUMANO atravessa o no' com canaleta - decisao de engenharia pendente.",
    "Portas de 156 cm entre dois T: HUMANO/MCP deixam passagem livre (51.9, so' CHANNEL); o NONE mantem a alvenaria acima e cria verga.",
    "Regras gerais ainda presas ao CHANNEL (58.2, 68, 71, 72, 60-65) - territorio D9-D13.",
    "A bancada de papel por bloco (benchmark block_role) nao reconhece codigos de canaleta."
  ],
  "next_steps": [
    "PARAR. D9-D13, D14 / Etapa 3B e D16 so' com nova autorizacao."
  ],
  "references": [
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/core/ui_components.py"},
    {"path": "nuvem/core/ui_state.py"},
    {"path": "nuvem/core/ui_preview_panel.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/test_opening_structural_reinforcement.py"}
  ]
}
```

## Arquitetura (fronteira de responsabilidades)

- **Reforço estrutural da abertura — as duas opções:** verga (51.1) e contraverga (51.2/10.4) em
  canaleta pelo planejador provado do CHANNEL, classificação `ABOVE_OPENING`/`BELOW_SILL`, gate da
  regra 75, validação e reauditoria da canaleta, rastreio por abertura.
- **Estratégia ADICIONAL CHANNEL — só com CHANNEL:** 51.9, 51.14, 58.2, 68, 71, 72, 60–65, memo.
- **Sempre:** §78 (tolerâncias físicas), §79 (regras de encontro), regra 48, regra 75, gates 76/76.1.

## Auditoria das 44 aberturas (Revit: HUMANO, MCP, SCRIPT antes = cópia CICLO6 da main, SCRIPT depois = cópia CICLO8)

`canaleta fN (+esq/+dir)`: fiada e quanto a corrida passa de cada jamba (cm; negativo = para antes
da jamba, na amarração do T vizinho — regra 75).

| abertura | tipo | parede | L × H | peit. | topo | verga HUMANO | verga MCP | verga SCRIPT antes | verga SCRIPT depois | status verga | contraverga HUMANO | contraverga MCP | contraverga SCRIPT antes | contraverga SCRIPT depois | status contraverga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8078984 | janela | 8284502 | 141 × 121 | 100 | 221 | canaleta f11 (+264/+49) | canaleta f11 (+259/+39) | bloco f11 | canaleta f11 (+254/+39) | CREATED | canaleta f4 (+209/+29) | canaleta f4 (+239/+59) | bloco f4 | canaleta f4 (+239/+59) | CREATED |
| 8078985 | janela | 8284502 | 121 × 121 | 100 | 221 | canaleta f11 (+269/+259) | canaleta f11 (+239/+239) | bloco f11 | canaleta f11 (+239/+239) | CREATED | canaleta f4 (+19/+239) | canaleta f4 (+59/+259) | bloco f4 | canaleta f4 (+59/+259) | CREATED |
| 8078986 | janela | 8284502 | 141 × 121 | 100 | 221 | canaleta f11 (+49/+264) | canaleta f11 (+24/+269) | bloco f11 | canaleta f11 (+59/+239) | CREATED | canaleta f4 (+29/+244) | canaleta f4 (+39/+214) | bloco f4 | canaleta f4 (+39/+219) | CREATED |
| 8078987 | janela | 8284502 | 151 × 141 | 80 | 221 | canaleta f11 (+244/+249) | canaleta f11 (+239/-1) | bloco f11 | canaleta f11 (+239/-1) | CREATED (SUPPORT_ACTUAL_ERROR) | canaleta f3 (+19/+214) | canaleta f3 (+49/-1) | bloco f3 | canaleta f3 (+39/-1) | CREATED (SUPPORT_ACTUAL_ERROR) |
| 8078988 | janela | 8284502 | 151 × 141 | 80 | 221 | canaleta f11 (+239/+254) | canaleta f11 (-1/+244) | bloco f11 | canaleta f11 (-1/+234) | CREATED (SUPPORT_ACTUAL_ERROR) | canaleta f3 (+199/+19) | canaleta f3 (-1/+34) | bloco f3 | canaleta f3 (-1/+34) | CREATED (SUPPORT_ACTUAL_ERROR) |
| 8078989 | janela | 8284502 | 141 × 121 | 100 | 221 | canaleta f11 (+49/+259) | canaleta f11 (+49/+244) | bloco f11 | canaleta f11 (+49/+244) | CREATED | canaleta f4 (+29/+204) | canaleta f4 (+29/+224) | bloco f4 | canaleta f4 (+29/+229) | CREATED |
| 8078990 | janela | 8284502 | 121 × 121 | 100 | 221 | canaleta f11 (+259/+269) | canaleta f11 (+259/+204) | bloco f11 | canaleta f11 (+259/+204) | CREATED | canaleta f4 (+239/+14) | canaleta f4 (+239/+34) | bloco f4 | canaleta f4 (+239/+39) | CREATED |
| 8078991 | janela | 8284526 | 141 × 121 | 100 | 221 | canaleta f11 (+29/+269) | canaleta f11 (+49/+244) | bloco f11 | canaleta f11 (+49/+244) | CREATED | canaleta f4 (+49/+209) | canaleta f4 (+29/+229) | bloco f4 | canaleta f4 (+29/+229) | CREATED |
| 8078992 | janela | 8284526 | 121 × 121 | 100 | 221 | canaleta f11 (+239/+239) | canaleta f11 (+259/+239) | bloco f11 | canaleta f11 (+259/+239) | CREATED | canaleta f4 (+259/+19) | canaleta f4 (+239/+39) | bloco f4 | canaleta f4 (+239/+39) | CREATED |
| 8078993 | janela | 8284526 | 141 × 121 | 100 | 221 | canaleta f11 (+59/+74) | canaleta f11 (+54/+44) | bloco f11 | canaleta f11 (+54/+44) | CREATED | canaleta f4 (+74/+94) | canaleta f4 (+34/+24) | bloco f4 | canaleta f4 (+34/+24) | CREATED |
| 8078994 | janela | 8284526 | 121 × 121 | 100 | 221 | canaleta f11 (+239/+239) | canaleta f11 (+239/+239) | bloco f11 | canaleta f11 (+239/+239) | CREATED | canaleta f4 (+19/+259) | canaleta f4 (+19/+259) | bloco f4 | canaleta f4 (+19/+259) | CREATED |
| 8078995 | janela | 8284526 | 141 × 121 | 100 | 221 | canaleta f11 (+269/+29) | canaleta f11 (+269/+29) | bloco f11 | canaleta f11 (+269/+29) | CREATED | canaleta f4 (+209/+49) | canaleta f4 (+209/+49) | bloco f4 | canaleta f4 (+209/+49) | CREATED |
| 8078996 | porta | 8284534 | 141 × 221 | 0 | 221 | canaleta f11 (+74/+59) | canaleta f11 (+59/+39) | bloco f11 | canaleta f11 (+44/+54) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8078997 | porta | 8284534 | 141 × 221 | 0 | 221 | canaleta f11 (+59/+74) | canaleta f11 (+34/+24) | bloco f11 | canaleta f11 (+44/+54) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8078998 | janela | 8284534 | 141 × 121 | 100 | 221 | canaleta f11 (+74/+59) | canaleta f11 (+39/+19) | bloco f11 | canaleta f11 (+44/+54) | CREATED | canaleta f4 (+94/+74) | canaleta f4 (+59/+39) | bloco f4 | canaleta f4 (+24/+34) | CREATED |
| 8078999 | porta | 8284534 | 141 × 221 | 0 | 221 | canaleta f11 (+59/+74) | canaleta f11 (+39/+19) | bloco f11 | canaleta f11 (+39/+19) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079000 | porta | 8284539 | 121 × 221 | 0 | 221 | canaleta f11 (+19/+19) | canaleta f11 (+24/+54) | bloco f11 | canaleta f11 (+24/+54) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079001 | janela | 8284546 | 61 × 61 | 160 | 221 | canaleta f11 (+39/+14) | canaleta f11 (+44/+24) | bloco f11 | canaleta f11 (+44/+24) | CREATED | canaleta f7 (+39/+14) | canaleta f7 (+44/+24) | bloco f7 | canaleta f7 (+44/+24) | CREATED |
| 8079002 | porta | 8284543 | 91 × 221 | 0 | 221 | canaleta f11 (+39/+49) | canaleta f11 (+34/+49) | bloco f11 | canaleta f11 (+34/+49) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079003 | porta | 8284543 | 91 × 221 | 0 | 221 | canaleta f11 (+54/+39) | canaleta f11 (+34/+34) | bloco f11 | canaleta f11 (+54/+39) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079004 | porta | 8284515 | 91 × 221 | 0 | 221 | canaleta f11 (+34/+24) | canaleta f11 (+39/+29) | bloco f11 | canaleta f11 (+59/+44) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079005 | porta | 8284515 | 91 × 221 | 0 | 221 | canaleta f11 (+24/+34) | canaleta f11 (+34/+34) | bloco f11 | canaleta f11 (+54/+54) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079006 | porta | 8284515 | 91 × 221 | 0 | 221 | canaleta f11 (+44/+19) | canaleta f11 (+29/+39) | bloco f11 | canaleta f11 (+54/+54) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079007 | porta | 8284515 | 91 × 221 | 0 | 221 | canaleta f11 (+14/+44) | canaleta f11 (+44/+24) | bloco f11 | canaleta f11 (+44/+24) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079008 | porta | 8284554 | 101 × 221 | 0 | 221 | canaleta f11 (+39/+34) | canaleta f11 (+4/+34) | bloco f11 | canaleta f11 (+4/+34) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079009 | porta | 8284522 | 91 × 221 | 0 | 221 | canaleta f11 (+34/+34) | canaleta f11 (+34/+34) | bloco f11 | canaleta f11 (+39/+54) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079010 | porta | 8284522 | 91 × 221 | 0 | 221 | canaleta f11 (+34/+24) | canaleta f11 (+44/+24) | bloco f11 | canaleta f11 (+44/+24) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079011 | porta | 8284522 | 91 × 221 | 0 | 221 | canaleta f11 (+24/+19) | canaleta f11 (+24/+39) | bloco f11 | canaleta f11 (+24/+39) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079012 | porta | 8284548 | 91 × 221 | 0 | 221 | canaleta f11 (+19/+39) | canaleta f11 (+54/+54) | bloco f11 | canaleta f11 (+49/+39) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079013 | janela | 8284502 | 141 × 121 | 100 | 221 | canaleta f11 (+244/+49) | canaleta f11 (+244/+49) | bloco f11 | canaleta f11 (+244/+49) | CREATED | canaleta f4 (+224/+29) | canaleta f4 (+224/+29) | bloco f4 | canaleta f4 (+229/+29) | CREATED |
| 8079014 | janela | 8284502 | 121 × 121 | 100 | 221 | canaleta f11 (+239/+259) | canaleta f11 (+204/+259) | bloco f11 | canaleta f11 (+204/+259) | CREATED | canaleta f4 (+34/+239) | canaleta f4 (+34/+239) | bloco f4 | canaleta f4 (+39/+239) | CREATED |
| 8079015 | janela | 8284502 | 121 × 121 | 100 | 221 | canaleta f11 (+259/+259) | canaleta f11 (+224/+204) | bloco f11 | canaleta f11 (+259/+204) | CREATED | canaleta f4 (+239/+54) | canaleta f4 (+239/+34) | bloco f4 | canaleta f4 (+239/+39) | CREATED |
| 8079016 | janela | 8284502 | 151 × 141 | 80 | 221 | canaleta f11 (+234/+264) | canaleta f11 (+239/-1) | bloco f11 | canaleta f11 (+239/-1) | CREATED (SUPPORT_ACTUAL_ERROR) | canaleta f3 (+34/+184) | canaleta f3 (+49/-1) | bloco f3 | canaleta f3 (+39/-1) | CREATED (SUPPORT_ACTUAL_ERROR) |
| 8079017 | janela | 8284502 | 151 × 141 | 80 | 221 | canaleta f11 (+239/+254) | canaleta f11 (+19/+269) | bloco f11 | canaleta f11 (+19/+234) | CREATED | canaleta f3 (+204/+29) | canaleta f3 (+19/+29) | bloco f3 | canaleta f3 (+19/+34) | CREATED |
| 8079018 | porta | 8284548 | 91 × 221 | 0 | 221 | canaleta f11 (+39/+19) | canaleta f11 (+54/+49) | bloco f11 | canaleta f11 (+39/+49) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079019 | porta | 8284552 | 91 × 221 | 0 | 221 | canaleta f11 (+4/+19) | canaleta f11 (+4/+54) | bloco f11 | canaleta f11 (+4/+24) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079020 | porta | 8284515 | 156 × 221 | 0 | 221 | vazio | vazio | bloco f11 | canaleta f11 (+19/+19) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079021 | porta | 8284515 | 156 × 221 | 0 | 221 | vazio | vazio | bloco f11 | canaleta f11 (+19/+19) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079022 | janela | 8284526 | 151 × 141 | 80 | 221 | canaleta f11 (+269/+19) | canaleta f11 (+269/+19) | bloco f11 | canaleta f11 (+269/+19) | CREATED | canaleta f3 (+29/+19) | canaleta f3 (+29/+19) | bloco f3 | canaleta f3 (+29/+19) | CREATED |
| 8079023 | janela | 8284526 | 151 × 141 | 80 | 221 | canaleta f11 (+19/+269) | canaleta f11 (+19/+254) | bloco f11 | canaleta f11 (+19/+254) | CREATED | canaleta f3 (+19/+29) | canaleta f3 (+19/+49) | bloco f3 | canaleta f3 (+19/+49) | CREATED |
| 8079024 | porta | 8284539 | 121 × 221 | 0 | 221 | canaleta f11 (+49/+29) | canaleta f11 (+19/+59) | bloco f11 | canaleta f11 (+19/+59) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079025 | porta | 8284539 | 296 × 221 | 0 | 221 | canaleta f11 (+39/+24) | canaleta f11 (+39/+19) | bloco f11 | canaleta f11 (+39/+19) | CREATED | — | — | — | — | NOT_REQUIRED (NO_SILL_OPENING_TOUCHES_BASE) |
| 8079026 | janela | 8284584 | 66 × 51 | 40 | 91 | bloco f5 | bloco f5 | bloco f5 | bloco f5 | UNRESOLVED (HEAD_OFF_GRID_51_8) | canaleta f1 (+4/+9) | bloco f1 | bloco f1 | bloco f1 | UNRESOLVED (RULE_75_TIE_OVER_SPAN) |
| 8079027 | janela | 8284554 | 61 × 91 | 80 | 171 | bloco f8 | bloco f9 | bloco f9 | bloco f9 | UNRESOLVED (HEAD_OFF_GRID_51_8) | canaleta f3 (+19/+34) | canaleta f3 (+39/+19) | bloco f3 | canaleta f3 (+39/+19) | CREATED |
