# Inventario de fontes para agentes

GERADO por `python3 tools/documentation/context_pack.py inventory --write` a partir de
[CONTEXT_MANIFEST.json](CONTEXT_MANIFEST.json). Nao editar a mao: editar o manifesto.
Catalogo de navegacao; a autoridade continua em cada fonte listada. Nenhum arquivo foi movido.

| id | caminho | papel | autoridade | status | carga | fonte unica de | proposta |
|---|---|---|---|---|---|---|---|
| AGENTS | `AGENTS.md` | instruction | USER_INSTRUCTION | CURRENT | auto | instrucoes de sessao para Codex (merge, monitoramento, regras de registro) | preservar; manter alinhado a CLAUDE.md; ordem de 2026-09-10 anotada como escopo encerrado |
| CLAUDE | `CLAUDE.md` | instruction | USER_INSTRUCTION | CURRENT | auto | instrucoes de sessao para Claude Code (idioma, merge, busca progressiva, registro de amarracao) | preservar; adaptador do host, sem copiar este protocolo |
| START_HERE | `docs/START_HERE.md` | onboarding | NAVIGATION | CURRENT | full | roteamento estavel e invariantes permanentes; nao guarda noticia | reconciliado em 2026-09-24: roteador + secao Historico com escopo |
| STATUS | `docs/PROJECT_STATUS.md` | status | DATED_STATE | CURRENT | summarized | estado corrente datado: main observada, PRs oficiais/candidatos, ultimo checkpoint, bloqueadores, proximo objetivo | preservar; state/pack extraem JSON e linhas-chave |
| PROCESS | `docs/DEVELOPMENT_PROCESS.md` | process | PROCESS | CURRENT | full | fluxo de CR, entrega documental verificavel, recuperacao de sessao | preservar como processo central; nao criar processo concorrente |
| RULES | `nuvem/REGRAS_MODULACAO_BLOCOS.md` | rule_authority | APPROVED_DOMAIN_RULE | CURRENT | by_section | regras de modulacao (status por secao) | preservar autoridade; indexar por numero+heading+sha256; numeros repetidos recebem @n |
| CONTEXT_README | `docs/agents/README.md` | navigation | NAVIGATION | CURRENT | on_demand | uso e limites do manifesto/pacote de contexto | novo (F1) |
| MANIFEST | `docs/agents/CONTEXT_MANIFEST.json` | navigation | NAVIGATION | CURRENT | on_demand | catalogo de fontes, dominios, aliases, secoes obrigatorias e espelhos de skills | novo (F1); fonte do inventario gerado |
| EVALS | `docs/agents/RETRIEVAL_EVALS.json` | navigation | NAVIGATION | CURRENT | on_demand | perguntas de recuperacao com resposta esperada | novo (F1); rodado por test_context_pack.py |
| RULES_INDEX | `rules/README.md` | rule_index | NAVIGATION | CURRENT | on_demand | indice das regras por natureza (regra/evidencia/decisao) | preservar como indice, sem copias de regra |
| DECISIONS | `docs/decisions/README.md` | decision | DECISION_RECORD | PENDING | full | decisoes do usuario pendentes/aprovadas (STATUS por registro) | preservar |
| DECISION_OPENING_REINFORCEMENT | `docs/decisions/DECISION-OPENING-REINFORCEMENT.md` | decision | DECISION_RECORD | PENDING | full | arquitetura de reforco de aberturas (CHANNEL aprovada; LINTEL pendente) | preservar; STATUS no proprio registro |
| DECISION_TOP_BOND_BEAM | `docs/decisions/DECISION-TOP-BOND-BEAM.md` | decision | DECISION_RECORD | PENDING | full | cinta de topo | preservar; STATUS no proprio registro |
| DECISION_COMPENSATOR_LIMIT | `docs/decisions/DECISION-COMPENSATOR-LIMIT.md` | decision | DECISION_RECORD | PENDING | full | teto/sequencia de compensadores | preservar; STATUS no proprio registro |
| DECISION_CATALOG_SCOPE | `docs/decisions/DECISION-CATALOG-SCOPE.md` | decision | DECISION_RECORD | PENDING | full | catalogo e cortes | preservar; STATUS no proprio registro |
| DECISION_WALL_OUTSIDE_MODULE | `docs/decisions/DECISION-WALL-OUTSIDE-MODULE.md` | decision | DECISION_RECORD | PENDING | full | parede fora do modulo | preservar; STATUS no proprio registro |
| DECISION_C2_G16 | `docs/decisions/DECISION-C2-G16.md` | decision | DECISION_RECORD | PENDING | full | criterio de vazio fisico global (C2/G16) | preservar; STATUS no proprio registro |
| DECISION_CR_B | `docs/decisions/DECISION-CR-B.md` | decision | DECISION_RECORD | PENDING | full | CR-B D1-D5 e escrita oficial | preservar; STATUS no proprio registro |
| CHECKPOINTS | `docs/checkpoints/` | checkpoint_set | DELIVERY_RECORD | CURRENT | on_demand | evidencia imutavel por entrega (JSON validado); o ultimo e resolvido pelo status | preservar; nunca editar checkpoint de outra sessao |
| EVIDENCE | `docs/checkpoints/evidence/` | evidence | DELIVERY_RECORD | CURRENT | on_demand | logs curtos com hash de validacoes capturadas | preservar |
| LOG | `docs/PROJECT_STATUS_LOG.md` | log | HISTORICAL_RECORD | HISTORICAL | on_demand | historico cronologico de CRs (indice para checkpoints) | preservar; so indices novos |
| STATUS_2026_09_09 | `docs/PROJECT_STATUS_2026-09-09_HISTORICAL.md` | status | HISTORICAL_RECORD | HISTORICAL | on_demand | painel anterior a 2026-09-09 | preservar como historico |
| REFERENCE_CORPUS | `docs/REFERENCE_CORPUS.md` | benchmark_contract | BENCHMARK_CONTRACT | CURRENT | on_demand | contrato do corpus de referencia do benchmark | preservar |
| SNAPSHOT | `docs/CURRENT_REFERENCE_SNAPSHOT.md` | benchmark_snapshot | HISTORICAL_RECORD | HISTORICAL | on_demand | ultimo estado medido oficialmente na data do snapshot (declara-se HISTORICAL) | preservar; o nome "CURRENT" e historico; linha 29 ainda diz ATUALIZADO (contradicao interna registrada) |
| BENCH_INDEX | `benchmark/README.md` | benchmark_index | NAVIGATION | CURRENT | on_demand | portal do benchmark e escritas protegidas | preservar como indice |
| BENCH_MANUAL | `nuvem/benchmark/README.md` | benchmark_manual | BENCHMARK_CONTRACT | CURRENT | on_demand | pipeline, comandos, reguas V1/V2, identidade e limitacoes do benchmark | preservar; revisar secoes historicas sem confundir com funcionamento atual |
| BENCH_MANIFEST | `nuvem/benchmark/golden/manifest.json` | benchmark_manifest | BENCHMARK_CONTRACT | CURRENT | on_demand | projetos oficiais do benchmark | preservar; escrita so com autorizacao |
| KNOWLEDGE | `nuvem/benchmark/knowledge/` | knowledge_data | GENERATED_DATA | CURRENT | on_demand | error_classes.json (gerado) e observed_patterns.json | preservar; nao editar o catalogo gerado a mao |
| PATTERNS | `nuvem/benchmark/patterns.py` | pattern_learning | CODE | CURRENT | on_demand | aprendizagem de padroes das referencias humanas (rejeita source=="solver") | preservar guarda anti-circular; dedupe por linhagem e desempate estavel ficam para a fatia F4 |
| REFS | `reference_projects/README.md` | reference_evidence | EVIDENCE_NOT_NORM | CURRENT | on_demand | portais das referencias humanas TORRE EASY / BUTANTA | preservar; evidencia, nao norma |
| REFS_INVENTORY | `reference_projects/inventory.json` | reference_evidence | EVIDENCE_NOT_NORM | CURRENT | on_demand | caminhos e hashes dos JSON primarios | preservar; verify_reference_inventory.py |
| REFS_PRIMARY | `docs/revit_reference_extraction/` | reference_evidence | EVIDENCE_NOT_NORM | CURRENT | on_demand | JSON primarios extraidos do Revit (somente leitura) | preservar; sem copias concorrentes |
| RUNTIME | `docs/RUNTIME_CANONICO.md` | runtime | IMPLEMENTATION_DOC | CURRENT | on_demand | loader rastreavel, gate unico de materializacao, pacote canonico | preservar |
| ARCH | `docs/architecture/README.md` | architecture | PROPOSAL | PENDING | on_demand | arquitetura proposta (nao aprovada por integracao) | preservar; linha 2 "Nada implementado" e anterior ao CHANNEL implementado (channel-strategy-implementation.md) |
| ARCH_CHANNEL | `docs/architecture/channel-strategy-implementation.md` | architecture | IMPLEMENTATION_DOC | CURRENT | on_demand | implementacao da estrategia CHANNEL (regra 51) | preservar |
| ARCH_REINFORCEMENT | `docs/architecture/opening-reinforcement-strategies.md` | architecture | PROPOSAL | CURRENT | on_demand | estrategias de reforco de aberturas | preservar |
| ARCH_CATALOG | `docs/architecture/extended-block-catalog.md` | architecture | PROPOSAL | CURRENT | on_demand | catalogo estendido proposto | preservar |
| ARCH_FAMILY | `docs/architecture/revit-family-mapping.md` | architecture | PROPOSAL | CURRENT | on_demand | mapeamento catalogo logico x familia Revit | preservar |
| ARCH_BETA2 | `docs/architecture/beta2-implementation-package.md` | architecture | PROPOSAL | CURRENT | on_demand | pacote de implementacao Beta 2 | preservar |
| BACKLOG | `docs/BETA2_BACKLOG.md` | backlog | PROPOSAL | PENDING | on_demand | backlog A-E do solver como snapshot de 2026-09-10 (base 6c00f7e) | preservar; reclassificar itens apos #37-#49 e ciclos 1/2 em entrega propria |
| CI_RECOMMENDATION | `docs/CI_RECOMMENDATION_2026-09-12.md` | governance | PROPOSAL | PENDING | on_demand | recomendacao de pytest + runner --check no CI (nao aplicada) | preservar; aplicacao exige autorizacao |
| CI_WORKFLOW | `.github/workflows/check-project-status.yml` | governance | CODE | CURRENT | on_demand | check documental unico (unittest das ferramentas + validate.py) | preservar; alteracao exige revisao especifica |
| DOC_TOOLS | `tools/documentation/` | tool | CODE | CURRENT | on_demand | validate.py, capture_validation.py, audit_inventory.py, verify_reference_inventory.py, context_pack.py | estender; nao duplicar validador |
| TESTS | `tests/README.md` | test_suite | CODE | CURRENT | on_demand | como rodar os testes do motor fora do Revit | preservar |
| TESTS_REGRESSION | `tests/regression/` | test_suite | CODE | CURRENT | on_demand | regressao do benchmark (longa; falhas historicas registradas no checkpoint) | preservar |
| LOADER_SETUP | `nuvem/LOADER_SETUP.md` | runtime | IMPLEMENTATION_DOC | CURRENT | on_demand | configuracao do loader e rastreabilidade (2026-09-23) | preservar; RUNTIME_CANONICO e o resumo corrente |
| UI_PREMIUM_DESIGN | `docs/UI_PREMIUM_DESIGN.md` | ui_doc | IMPLEMENTATION_DOC | CURRENT | on_demand | decisoes do redesign premium (#46, integrado pelo #49) | preservar; linha 5 "nenhum merge" e historica |
| UI_POST_PR42 | `docs/UI_POST_PR42.md` | ui_doc | IMPLEMENTATION_DOC | HISTORICAL | on_demand | preparacao da UI pos-#42 (integracao ocorreu pelo #49) | preservar como historico da integracao |
| UI_REDESIGN | `docs/UI_REDESIGN.md` | ui_doc | HISTORICAL_RECORD | SUPERSEDED | on_demand | redesign do #44 (superado pelo #46) | preservar |
| UI_VISUAL_REFERENCE | `docs/UI_VISUAL_REFERENCE.md` | ui_doc | HISTORICAL_RECORD | SUPERSEDED | on_demand | referencia visual anterior (#44) | preservar |
| DEBT | `docs/agents/KNOWN_DEBT.json` | debt_index | NAVIGATION | CURRENT | summarized | indice de divida conhecida aberta (id, verificacao exata, caso, valores, evidencia); nao e aceite | novo (F1); checkpoints continuam sendo a evidencia |
| TESTS_RUNNER | `tests/run_tests.py` | test_suite | CODE | CURRENT | on_demand | runner historico (so test_script.CASES); suite completa via pytest | preservar |
| NUVEM_TESTS | `nuvem/tests/README.md` | test_suite | HISTORICAL_RECORD | HISTORICAL | on_demand | suite antiga (banner aponta tests/README.md) | preservar |
| SCRIPT | `Script.py` | entry | CODE | CURRENT | on_demand | entrada/loader do botao pyRevit | preservar; nao migrar imports nesta fatia |
| README | `README.md` | onboarding | NAVIGATION | CURRENT | on_demand | portal do repositorio | reconciliado: estado de Beta aponta para o status |
| DESTINO | `DESTINO_GITHUB.md` | governance | NAVIGATION | CURRENT | on_demand | mapeamento pasta local pyRevit -> repositorio | preservar |
| SKILLS_CLAUDE | `.claude/skills/` | skill | PROCEDURE | CURRENT | on_demand | skills do Claude (pesquisa, debugging, checkpoint, verificacao, modulacao) | preservar; espelho verificado |
| SKILLS_AGENTS | `.agents/skills/` | skill | PROCEDURE | CURRENT | on_demand | skills do Codex (espelho) | preservar; diferencas por host declaradas no manifesto |
| ARCHIVE | `docs/archive/` | historical | HISTORICAL_RECORD | HISTORICAL | on_demand | auditorias e benchmark antigos | preservar |

## Familias de arquivos (por padrao)

| padrao | arquivos | papel | status | nota |
|---|---|---|---|---|
| `docs/CR_*.md` | 11 | cr_report | HISTORICAL | relatorios de CRs encerradas; a regra vigente esta nas REGRAS |
| `docs/BLOCK_*.md` | 10 | cr_report | HISTORICAL | relatorios finais de CRs de bloco |
| `docs/BENCH_*.md` | 3 | cr_report | HISTORICAL | CRs do benchmark |
| `docs/C04_*.md` | 1 | cr_report | HISTORICAL | revisao independente do PR #20 |
| `docs/CHECKPOINT_*.md` | 3 | checkpoint_legacy | HISTORICAL | checkpoints anteriores ao formato JSON de docs/checkpoints/ |
| `docs/GITHUB_STATE_*.md` | 2 | github_snapshot | HISTORICAL | estado Git/GitHub datado; o status e a fonte corrente |
| `docs/AUDITORIA_*.md` | 1 | audit | HISTORICAL | auditoria datada (declara-se HISTORICAL) |
| `docs/BETA_MAIN_SAFE*.md` | 2 | runbook | HISTORICAL | bancada main-safe de 2026-09-09 |
| `docs/CONSOLIDATION_*.md` | 1 | consolidation | HISTORICAL | consolidacao de 2026-09-10 (PR #36) |

## Dominios

| dominio | regras obrigatorias | aliases |
|---|---|---|
| amarracao | , 5, 11, 11.10, 18.7, 18.10, 33.9, 35.1, 36.3, 52, 75, 76, 77, 77.1 | amarração, amarrações, amarracao, amarrar, encontro, encontros, encontro em L, encontro em T, encontro em X, canto em L, cruzamento, junção, peça de amarração, peça de nó, vão menor, vazado menor, paridade do nó, giro do canto, B34, B54, bond, bonding, tie, ties, junction, junctions, corner, L_CORNER, T_INTERSECTION, X_INTERSECTION, JUNCTION_MISSING_BINDING, MISSING_REQUIRED_JUNCTION_BOND, NO_FUNCTIONAL_JUNCTION, BOND_UNRESOLVED |
| prisma_fiadas | 8, 8d, , 11, 11.5, 11.8, 18.4, 27.6, 33.1, 39.4, 57.1 | prisma, junta vertical, juntas verticais, junta corrida, junta contínua, junta empilhada, desencontro, travamento, alinhamento vertical, regra #1, fiadas pares, fiadas ímpares, Fiada A, Fiada B, banda de abertura, prism, stagger, vertical joint, continuous joint, PRISM_CONTINUOUS_JOINT, CONTINUOUS_VERTICAL_JOINT, FORBIDDEN_JOINT_ALIGNMENT |
| bonecas_pilaretes | , 11.11, 11.13, 18.8, 18.12, 25.1, 35.1, 76.1, 78 | boneca, bonecas, pilarete, pilaretes, trecho curto, trechos curtos, parede curta, paredes curtas, ponta livre, ponta aberta, jamba, jambas, meio-bloco, meio bloco, B19, pier, piers, free end, jamb, half block, B19_RESIDUAL_FILL |
| aberturas | 3, 4, 11.8, 23, 23.2, 23.5b, 25.1, 25.2, 48, 66.2, 78 | abertura, aberturas, vão, vãos, porta, portas, janela, janelas, peitoril, zona de exclusão, invasão, invade, sonda de vão, regra 48, OPÇÃO A, microajuste, opening, openings, door, window, sill, OPENING_VOID_INVASION |
| canaletas | 10.1, 10.7, 48, 51, 51.1, 51.2, 51.3, 51.4, 51.6, 51.7, 51.8, 51.10, 75, 78 | canaleta, canaletas, bloco canaleta, bloco U, meia canaleta, corrida de canaleta, reforço de aberturas, reforço de abertura, CHANNEL, U-block, CHANNEL_AS_JUNCTION_BOND, OPENING_REINFORCEMENT_CHANNEL, FREE_TO_TOP |
| vergas_lintel_cinta | 10.1, 10.4, 10.7, 40.2, 40.7, 41.3, 41.4, 51.10, 75 | verga, vergas, contraverga, contravergas, cinta de topo, cinta, encunhamento, lintel, lintels, counterlintel, LINTEL_COUNTERLINTEL, bond beam, TOP_BOND_BEAM |
| compensadores | 2, 11.8, 12, 33.8, 54, 56, 58, 58.3, 76 | compensador, compensadores, pastilha, pastilhas, C09, C04, peça de acerto, peça de ajuste, compensator, compensators, COMPENSATOR_AS_JUNCTION_BOND, COMPENSATOR_CONSECUTIVE, ADJACENT_COMPENSATORS |
| catalogo | 1, , , 24.9, 40.9, 51.11, 52 | catálogo, catálogo de blocos, família, famílias, tipo de bloco, B39, bloco inteiro, bloco cortado, célula, células, catalog, family mapping, FamilySymbol, LogicalBlockType |
| tolerancias_fechamento | 78, 30.8, 30.9, 74, 51.13, 18.12, 18.8 | tolerância física, tolerâncias físicas, tolerância, tolerâncias, folga, resíduo, fora do módulo, trecho não modular, regra 78, absorção, NON_MODULAR_UNRESOLVED, NON_MODULAR_WALL, physical tolerance, PHYSICAL_MODULATION_TOLERANCES_ENABLED |
| corpus_selecao | 49, 49.1, 8c, 15.3 | corpus da RUN, seleção de paredes, paredes existentes, unir paredes, união de paredes, layer de referência, regra 49, eixos excluídos, existing walls, reference layer, corpus selection, ARQ-STR-BLOCO, DETECTED_AXES, SELECTED_AXES, EXCLUDED_AXES |
| wall_modeling | 26, 26.1, 26.2, 26.3, 26.4, 26.8.1, 26.8.2, 26.8.6, 26.8.7.2, 26.8.7.6, 26.8.7.7, 26.8.8.3, 26.9.1, 26.9.2, 26.10.2, 26.10.3, 26.10.4, 26.10.5, 26.10.7, 8b, 15 | pareamento, pareamento de faces, par de faces, espessura, linha de centro, colinear, colineares, duplicata, duplicatas, deduplicação, grafo de encontros, linhas de esquadria, wall modeling, wall pairing, pairing, centerline, collinear, deduplicate, wall graph, find_wall_pairs, merge_collinear_fragments |
| criacao_revit | 8, 8a, 15.3, 23.5b, 48, 50, UX-20260916 | criação no Revit, criar blocos, lançar blocos, materialização, materializar, cota, cotas, nível de referência, origem vertical, lote persistente, carimbo, idempotência, idempotente, espelhamento, NewFamilyInstance, ProjectElevation, materialization gate, preflight |
| ui_revisao | UX-20260916 | UI, interface, tela, tela de configuração, revisão antes da criação, contrato de revisão, prévia, stepper, tema escuro, relatório final, WinForms, ui_state, ui_components, ui_chrome, UX-20260916 |
| runtime_loader | 48 | loader, runtime, runtime canônico, pacote beta, pacote canônico, banner, proveniência, cache do pacote, token cifrado, Script.py, beta_package, BETA_OFFLINE, pyRevit, pushbutton, botão |
| benchmark | 24, 59 | benchmark, gabarito, baseline, baselines, corpus de referência, régua V1, régua V2, piso de ruído, regressão, score, golden, runner.py, save-baseline, calibrate, TGD, TP1, reference corpus, fingerprint |
| governanca | — | governança, processo, fluxo de CR, checkpoint, checkpoints, status do projeto, PROJECT_STATUS, START_HERE, onboarding, merge, PR, pull request, CI, validador documental, validate.py, recuperação de contexto, pacote de contexto, manifesto de contexto, handoff, nova sessão, AGENTS.md, CLAUDE.md, context_pack, skills, decisões pendentes, entrega |

## Espelhos de skills

`.claude/skills` ↔ `.agents/skills`: arquivos iguais, exceto:
- `cr-checkpoint/SKILL.md`: troca de host: Codex/AGENTS.md/.Codex/checkpoints no espelho x Claude Code/CLAUDE.md/.claude/checkpoints (deriva registrada: .Codex/checkpoints nao e ignorado pelo .gitignore; corrigir em entrega propria)
- `revit-block-modulation/SKILL.md`: troca de host: AGENTS.md no espelho x CLAUDE.md (linhas 95 e 125)
