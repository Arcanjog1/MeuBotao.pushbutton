# Ciclo 1: tolerâncias físicas de fechamento não dependem mais do reforço CHANNEL (regra 78)

```json
{
  "date": "2026-09-23",
  "scope": "current",
  "branch": "main",
  "base": "ca014aafa78522fc2f115c1d45fa46c4fef46df8",
  "head": "9376a36feacec1a545e23f78333a29530c5e1ec9",
  "pr": "not-created",
  "objective": "Primeiro ciclo de correcao apos a comparacao forense dos tres Revit (MCP = butanta testes, SCRIPT = TESTE PR49, HUMANO = BUTANTA R08). Causa raiz de maior impacto nos casos D1, D2, D3, D7 e D8: o SCRIPT (reforco 'Sem reforco' = NONE) deixava trechos inteiros de parede VAZIOS quando o comprimento nao fechava exatamente, porque as tolerancias fisicas de fechamento (30.8 e 51.13) so eram ligadas junto com a estrategia CHANNEL. Separar OPENING_REINFORCEMENT_STRATEGY de PHYSICAL_MODULATION_TOLERANCES sem trocar NONE por CHANNEL, sem hardcode e sem tolerancia nova; trecho realmente impossivel passa a ser registrado como NON_MODULAR_UNRESOLVED com revisao humana. Trabalho direto na main, sem force push; PARAR ao fim deste ciclo.",
  "changes": [
    "MOTOR (nuvem/core/wall_modeling.py): novo interruptor PHYSICAL_MODULATION_TOLERANCES_ENABLED = True (CHANNEL_PHYSICAL_TOLERANCES_ENABLED virou alias). O wrapper de estrategia (`solve_building_blocks_all_courses`) NAO liga mais as tolerancias por estrategia; `_solve_building_blocks_all_courses_impl` (ponto unico dos dois canais) liga RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED (30.8, <= 2,0 cm) e JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED (51.13, PIER_PHYSICAL_FIT_TOLERANCE_CM) para QUALQUER estrategia e restaura no finally. Nenhum valor de tolerancia foi alterado; os portoes da 30.9 (`physical_tolerance_trial`) continuam os mesmos. As demais chaves CHANNEL-only (76, 76.1, 77, 58.2, 68, 71, 72, 74) continuam so no CHANNEL.",
    "REGISTRO (wall_modeling.py): `_unresolved_spans(result)` converte cada `non_modular` remanescente em registro NON_MODULAR_UNRESOLVED (status, rule_id=NON_MODULAR_SPAN, requires_human_review=true, wall_idx, wall_id, course, course_indices, variant_index, segment_index, start_cm, end_cm, length_cm, residual_cm, shortfall_cm, lower/upper_valid_cm, conflict, reason). `_execute_solve` preenche wall_id; `_execute_create` expoe `unresolved_spans` e `structurally_resolved` passa a considerar trechos nao resolvidos; `_format_block_solve_report` lista 'TRECHOS NAO RESOLVIDOS (NON_MODULAR_UNRESOLVED, revisao humana obrigatoria)'.",
    "UI (nuvem/core/ui_state.py): `unresolved_spans`, `span_text`, itens de revisao, `creation_gate` (avisa, nao bloqueia: o trecho fica sem bloco e o restante e criado) e `report_text` mostram os trechos NAO resolvidos.",
    "REGRAS: secao 78 nova (tolerancias fisicas de fechamento nao dependem do reforco de abertura; ordem de tentativas: combinacao modular -> tolerancias fisicas permitidas -> ajuste estrutural/residual -> NON_MODULAR_UNRESOLVED); escopo da 30.9 marcado como superado pela 78.",
    "TESTES: tests/test_tolerancias_fisicas_gerais.py (11 testes: casos 1-8 do enunciado + interruptor + relatorio/UI); tests/test_node_bounded_residual.py: o context manager `absorption()` tambem desliga a 78 para continuar medindo o motor sem absorcao. tools/audit/s74_corpus.py ganhou `tolerancias_fisicas=None` (flag do PRODUTO, mesmo padrao de `papel_por_fiada`): os casos HISTORICOS do legado em tests/test_s74_corpus_butanta.py e tests/test_regra76_corpus_butanta.py continuam medidos contra o snapshot gravado (78 desligada), e o legado do PRODUTO (78 ligada) e verificado nas invariantes (sem gates da regra 76; a secao 74 nao o alcanca). Nenhum snapshot/golden/threshold foi regravado.",
    "DEFEITO CORRIGIDO DURANTE O CICLO (primeira versao do patch): `_solve_building_blocks_all_courses_pass` copiava cada trecho `non_modular` (`dict(span, course_indices=...)`) e `_non_modular_by_physical_course` reconhece a banda de cada trecho por `id(entry)` - a copia fazia todo trecho valer para TODAS as fiadas da familia e o gate 76.1 acusava `BOND_PIECE_NON_MODULAR` em fiadas sem trecho (2 testes de tests/test_regra76_d1_t_degradado.py). Agora `course_indices` e gravado no proprio objeto. So' o registro/auditoria mudou: as pecas da bancada sao identicas antes e depois desta correcao (96/9577/154/8194 e 0/30/64/7416)."
  ],
  "tests": [
    "Focados (arvore final): tests/test_tolerancias_fisicas_gerais.py + test_node_bounded_residual + test_regra76_d1_t_degradado + test_regra761_revisao_do_gate + test_secao77_papel_por_fiada + test_physical_tolerance_trial + test_t_room_physical_tolerance + test_physical_support_audit: 117 passaram, 1 pulado. Corpus: tests/test_regra76_corpus_butanta.py + tests/test_s74_corpus_butanta.py: 61 passaram (snapshots historicos intactos).",
    "Suite completa sem tests/regression (arvore final): 1702 passaram, 1 pulado, 1 falhou - tests/test_perf_trace_stall_sampler.py (historica, identica na main ca014aa). Antes da correcao do id(entry) a mesma suite tinha 7 falhas (2 do D1 + 2 do legado historico + 3 nao listadas pelo tail); todas desapareceram com a correcao e com a medicao do legado historico com a 78 desligada.",
    "tests/regression (arvore final, 19 min): 146 passaram, 2 falharam - TP1 JUNCTION_MISSING_BINDING 8->9 (historica, identica na main) e TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 (NOVA na regua, reclassificacao provada em physical_deltas; na main o TGD V2 falhava por 'compensators 61->62')."
  ],
  "known_failures": [
    "tests/test_perf_trace_stall_sampler.py::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas - historica (ctypes no proprio teste, Windows), identica na main.",
    "tests/regression TP1: JUNCTION_MISSING_BINDING 8->9 - historica, identica na main.",
    "tests/regression TGD V2: COVERAGE_ROW_MOSTLY_EMPTY 86->92 - efeito desta etapa na REGUA (reclassificacao; nenhuma fiada perdeu cobertura; compensadores 2217->2451). Baseline nao regravado (proibido pelo enunciado). O verdict do projeto passa de 'REGRESSAO' (compensators 61->62) para 'REGRESSAO CRITICA'.",
    "96 trechos NON_MODULAR_UNRESOLVED no BUTANTA com 46 eixos (todos induzidos pelos nos T das 12 paredes extras - D5, fora do escopo deste ciclo); com os 34 eixos de alvenaria: 0.",
    "D2 (pilar do no 51) e D3 (nos 20/26/28): sem mudanca neste ciclo.",
    "A copia CICLO1_butanta_testes.rvt ficou ABERTA no Revit sem salvar (IsModified=true) para inspecao humana; o arquivo em disco e' copia identica do original. Nenhum dos tres RVTs de referencia foi tocado ou salvo."
  ],
  "physical_deltas": [
    "SOLVER com estrategia NONE (bancada offline, 46 eixos reais, 280 cm, 14 fiadas): NON_MODULAR_SPANS 224 -> 96; EMPTY_LENGTH_CM (34 eixos x fiadas 0-11, vaos >= 5 cm) 18935 -> 9577; JAMB_MISSING 198 -> 154; BLOCK_COUNT 7762 -> 8194; match exato vs MCP 43,6% -> 45,6% (<= 5 cm: 46,1% -> 48,5%); match vs SCRIPT real 95,8% -> 94,2%. Nos 34 eixos sem as 12 paredes extras (D5): 78 -> 0 trechos, 2637 -> 30 cm vazios. CHANNEL (34 eixos) inalterado: 0 trechos / 451 cm / 96,8% vs MCP.",
    "REVIT (copia em disco CICLO1_butanta_testes.rvt, motor da main + patch, NONE, 46 paredes, 44 aberturas): 8195 planejadas, 8184 criadas, 0 falhas, 11 puladas pela regra 48 (mesmas 11 amarracoes rejeitadas = BOND_UNRESOLVED), 96 trechos NON_MODULAR_UNRESOLVED. Regua sobre o modelo criado: EMPTY_LENGTH_CM 9577 (SCRIPT real 18666; MCP 473; HUMANO 3064), JAMB_MISSING 154 (SCRIPT 192; MCP 59; HUMANO 97), invasoes de abertura 0 (SCRIPT 6; MCP 0; HUMANO 21), bonecas 8284584/8284591/8284589/8284590 vazio 681/804/456/456 -> 0/0/0/0 cm e pecas por fiada 1,0 -> 4,7/5,0/2,0/2,0 (MCP 3,9/4,0/2,0/2,0; HUMANO 3,8/3,5/3,5/3,5). Por eixo (D1): 8284526 7006 -> 5662; 8284502 3620 -> 2105; 8284546 3806 -> 842; 8284539 1597 -> 938.",
    "SEM MUDANCA neste ciclo (medido, nao inferido): D2 (pilar do no 51 em 8284515, 1570-1624 cm) e D3 (nos 20/26/28) - a regua nao mostrou diferenca entre ANTES e DEPOIS; os 96 trechos restantes (todos em 8284526, 8284502, 8284546, 8284539) sao induzidos pelos nos T das 12 paredes extras (D5) e ficam registrados para revisao humana.",
    "MATERIALIZACAO: nenhuma mudanca na regra 48; canaleta como amarracao = 0 (caso 8).",
    "BENCHMARK (tests/regression, solver_bridge com estrategia None = legado, agora com a 78): TGD V2 e o unico projeto cuja regua critica muda. Medido com a chave 78 desligada (= main ca014aa, conferido em worktree limpo C:/int42_main) e ligada, no MESMO motor: COVERAGE_MISSING_ROW 142 -> 136, COVERAGE_GAP_IN_ROW 1275 -> 1153, COVERAGE_PARTIAL_WALL 32 -> 24 (paredes W005, W012, W027, W028, W075, W086, W129, W130 deixam de ser 'parcial'), categoria wall_coverage 70 -> 61 paredes reprovadas; blocos 16218 -> 17249, comprimento assentado 535697 -> 566241 cm; das 187 fiadas medidas nas 11 paredes que mudaram de classe, 109 ganharam cobertura, 78 ficaram iguais e NENHUMA perdeu. COVERAGE_ROW_MOSTLY_EMPTY 86 -> 92 e' RECLASSIFICACAO da regua: as fiadas 12/14/16 de W027/W028/W129/W130 tem 162/814 cm ANTES e DEPOIS (identicas); so' passaram a ser acusadas porque a melhor fiada dessas paredes subiu de <90% para 96-97% (a regra do validador so' acusa 'fiada quase vazia' quando outra fiada fechou) - e as 6 fiadas de W020 (0..10 pares) sairam da lista porque fecharam (166 -> 348 cm). Efeito colateral REAL, nao critico: compensadores 2217 -> 2451 pecas (13,7% -> 14,2% das pecas), COMPENSATOR_EXCESS_IN_RUN 428 -> 503, categoria compensators 62 -> 63 paredes (a historica ja era 61 -> 62 na main); PRISM_STAGGER_BELOW_TARGET 712 -> 749 (categoria prism 23 -> 5, inalterada em relacao a' main). TP1 V1: regua critica identica a' main (JUNCTION_MISSING_BINDING 8 -> 9 historica), GAP_IN_ROW 336 -> 302, compensadores +2%. E' exatamente a decisao pendente registrada em 2026-09-15 ('TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 por reclassificacao; compensadores 62->63'): baseline NAO regravado nesta etapa (proibido pelo enunciado) - decisao humana."
  ],
  "decisions_taken": [
    "Tolerancia fisica de fechamento e propriedade da modulacao, nao do reforco de abertura: um interruptor proprio (78), nao a troca de NONE por CHANNEL.",
    "Trecho impossivel nunca fica silencioso: NON_MODULAR_UNRESOLVED com campos e revisao humana obrigatoria, sem bloquear a criacao do restante."
  ],
  "decisions_pending": [
    "Ciclo 2 (nao iniciado, por ordem do usuario): D5 (12 eixos extras que induzem os 96 trechos restantes), D4 (B34 em porta), D6 (verga/contraverga), D9-D13 (paridade/composicao/compensadores), D16 (canaleta em no), etapa 3B.",
    "Regua do benchmark TGD V2: regravar o baseline (runner.py --save-baseline) num commit proprio dizendo o que melhorou (cobertura) e o que piorou (compensadores), ou manter a falha 'REGRESSAO CRITICA' documentada. Decisao humana - nao tomada aqui."
  ],
  "next_steps": [
    "Gerar modulacao-main-<sha7>.zip do MAIN FINAL e ler o banner nos dois PCs.",
    "Ciclo 2 somente com nova autorizacao."
  ],
  "references": [
    {
      "path": "nuvem/core/wall_modeling.py"
    },
    {
      "path": "nuvem/core/ui_state.py"
    },
    {
      "path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"
    },
    {
      "path": "tests/test_tolerancias_fisicas_gerais.py"
    },
    {
      "path": "tests/test_node_bounded_residual.py"
    },
    {
      "path": "tools/audit/s74_corpus.py"
    },
    {
      "path": "tests/test_s74_corpus_butanta.py"
    },
    {
      "path": "tests/test_regra76_corpus_butanta.py"
    },
    {
      "path": "docs/checkpoints/2026-09-15-butanta-modulation-physical-fixes.md"
    }
  ]
}
```

## 1. Causa raiz

O SCRIPT (lote `20260923-122204`, 46 eixos, 280 cm, estratégia "Sem reforço") foi reproduzido offline a 96,4 % com o motor da main. Os buracos de D1/D7 não vinham de um solver diferente: eram `non_modular` (trecho que não fecha exatamente com o catálogo) deixados **vazios** porque as tolerâncias físicas de fechamento — absorção limitada no nó (30.8, ≤ 2,0 cm) e ruído de segmento na jamba (51.13) — só eram ligadas pelo wrapper de estratégia quando `CHANNEL` estava ativo. Com `NONE`, uma parede de 86 cm ou um resíduo de 1 cm viravam trecho inteiro sem bloco.

Experimento de isolamento na bancada (46 eixos): só RESIDUAL → 120 trechos / 9 964 cm; só JAMB → 200 / 18 548; RESIDUAL + JAMB → 96 / 9 577; RESIDUAL + JAMB + T_ROOM → 96 / 9 577 (T_ROOM não acrescenta nada). Conjunto mínimo = 30.8 + 51.13.

## 2. Como a dependência de CHANNEL foi removida

- `PHYSICAL_MODULATION_TOLERANCES_ENABLED` é um interruptor **da modulação**, lido no ponto único `_solve_building_blocks_all_courses_impl` (os dois canais passam por ele). O wrapper `solve_building_blocks_all_courses` continua decidindo apenas o que é reforço (CHANNEL/NONE).
- Os valores das tolerâncias não mudaram (`RESIDUAL_NODE_BOUNDED_MAX_CM`, `PIER_PHYSICAL_FIT_TOLERANCE_CM`) e continuam sob os mesmos portões da 30.9 (`physical_tolerance_trial`). Nada disso se mistura com a regra 48: a peça que invade abertura continua não sendo criada (Revit: invasões 0).
- Ordem por trecho: combinação modular → fechamento com tolerâncias físicas → ajuste estrutural/residual → `NON_MODULAR_UNRESOLVED` (visível no relatório, no `report_text`, nos itens de revisão e no `create_result`).

## 3. Validação no Revit (cópia)

`C:/Users/twitc/Desktop/CIVIX/butanta testes.rvt` copiado para `CICLO1_butanta_testes.rvt`, aberto com `OpenAndActivateDocument`, motor carregado de `C:/int42` (`wm.doc` apontado para a cópia). `IsModified` dos três documentos de referência é idêntico antes e depois (butanta testes `true`, BUTANTÃ `true`, TESTE PR49 `false` — estado pré-existente, não tocado); nenhum deles foi salvo. A cópia ficou aberta **sem salvar** (`IsModified=true`) para inspeção humana; o arquivo em disco é igual ao original.

## 4. O que fica para o ciclo 2

Os 96 trechos restantes concentram-se nos 4 eixos onde as 12 paredes extras (D5) criam nós T que fragmentam a parede em segmentos que não fecham; são registrados, não escondidos. D2 (pilar do nó 51) e D3 (nós 20/26/28) não mudaram neste ciclo.
