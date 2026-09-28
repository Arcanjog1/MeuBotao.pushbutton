# Ciclo 11 — convergência SCRIPT ↔ MCP: §83 (a §68 no caminho geral, com guarda de junta e de tier)

```json
{
  "date": "2026-09-28",
  "scope": "current",
  "branch": "main",
  "base": "1db4876e9fa6dcd1a7608efa6952364ae6c3362d",
  "head": "71e2fbc019985551f41758d35727955eabe54ce1",
  "pr": "not-created",
  "objective": "Ciclo 11: nova baseline SCRIPT x MCP x HUMANO sobre a main 1db4876; descobrir por que o MCP (butanta testes) ficou melhor e transformar a decisao em regra geral reproduzivel; corrigir SOMENTE a classe de diferenca comprovada de maior impacto; sem copiar o MCP onde o HUMANO prova o contrario; sem reabrir D1-D16; sem hardcode.",
  "changes": [
    "71e2fbc SECAO 83: GENERAL_REPAIR_PREFER_CLEAN_ENABLED liga a secao 68 (melhor composicao da faixa jamba->ancora) no caminho geral (NONE), no ponto unico _solve_building_blocks_all_courses_impl, com duas guardas so' do caminho geral: OPENING_REPAIR_JOINT_GUARD_ACTIVE (qualidade = (juntas coincidentes com a familia oposta, compensadores, meio blocos, especiais, pecas); juntas de referencia = busca + contorno no'|preenchimento da familia oposta; isencao de peca pequena so' contra abertura; janela expandida com coincidencia refeita desencontrando tambem a guarda, _repair_guarded_window_solution) e OPENING_REPAIR_TIER_GATE_ACTIVE (_repair_tier_gate_blocks: 1 compensador antes da fileira de B34 na faixa jamba->ancora, por subtrecho, com _repair_strip_codes). CHANNEL mantem a 68 historica (assinatura identica a' main). Resultado expoe general_repair_prefer_clean.",
    "TESTES: tests/test_reparo_68_guarda_junta.py (novo, 25); contratos atualizados em test_opening_structural_reinforcement (espiao NONE: 68 com guarda), test_paridade_contextual_t (68 so' com a chave da 83), test_regras_gerais_composicao (81 medida isolada, 83 desligada nos dois lados), test_channel_reinforcement (LEGADO_HISTORICO desliga a 83), tools/audit/s74_corpus.py (legado historico com a 83 desligada).",
    "DOCS: REGRAS secao 83 (+ notas em 68, 81, 82), este checkpoint, evidencias em docs/checkpoints/evidence/2026-09-28-ciclo11-convergencia/, PROJECT_STATUS, LOG, START_HERE."
  ],
  "tests": [
    "tests/test_reparo_68_guarda_junta.py + tests/test_opening_repair_clean_composition.py: 32 passaram (vermelho sem guarda: junta continua nova em 2 fixtures genericas T+porta achadas por varredura; nunca junta a prumo nova; nunca mais compensador que o legado; janela refeita = B39 B19; ganho mantido = 0 compensador onde o legado tinha C04+C09; guarda de tier: pilarete de 69 cm entre dois vaos fica B39 C09 B19 e nao B34 B34, pilarete de 75 cm com 2 compensadores ganha a fileira; qualidade e gate como funcoes puras; isencao so' contra abertura; CHANNEL identico; chave desligada = legado; determinismo; espelhamento; sem hardcode).",
    "Relacionados (espioes NONE/CHANNEL, paridade contextual, regras gerais de composicao, CHANNEL, regras fisicas de encontro, tie parity, vazado menor): 201 passaram.",
    "1 903 passaram, 1 falha histórica (test_perf_trace_stall_sampler), 1 pulado (pool de 4 processos por arquivo; test_block_arm_role_prism_stagger 5/5 e test_block_b19_residual_fill_implementation 76/76 rodados à parte, 67 e 66 min — a candidata terminou antes da main nos dois)",
    "Corpus da secao 74 (tools/audit/s74_corpus.py, legado historico = main): 41 passaram na candidata anterior a' guarda de tier (DEV5); test_regra76_corpus_butanta 20 passaram (DEV5); os dois arquivos entram na suite completa acima.",
    "Assinatura fisica: CHANNEL BUTANTA identico a' main (100 % exato, 5 914 pecas nas fiadas 0-11); pecas de no' do motor NONE identicas (472 B34 + 218 B54 + 3 C09 = 693)."
  ],
  "known_failures": [
    "tests/test_perf_trace_stall_sampler.py (historica).",
    "tests/regression: TP1 V1 JUNCTION_MISSING_BINDING 8->9 e TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 (anteriores; baseline nao regravado; vereditos REGRESSAO CRITICA do TP1 V1 e TGD V2 identicos a' main).",
    "BUTANTA: 3 fiadas dos cantos L 55/56 sem amarracao (decisao do usuario); LINTEL_UNRESOLVED HEAD_OFF_GRID_51_8 em 8079026/8079027 e SILL RULE_75_TIE_OVER_SPAN em 8079026 (pendencias registradas)."
  ],
  "physical_deltas": [
    "BUTANTA NONE offline (34 eixos, 280 cm, regua forense, fiadas 0-13; main -> 83): compensadores 479 -> 413 (6,72 -> 5,84 %; MCP 400, HUMANO 487); junto de abertura 230 -> 179; junto de no' 202 -> 192; colunas >= 4 fiadas 63 -> 54; pares de especiais 326 -> 276; B39 4 032 -> 4 020; B34 1 707 -> 1 743 (BOND 472 -> 477 pela regua, pecas de no' identicas); B19 377 -> 362; C04 210 -> 165; C09 269 -> 248; juntas continuas >= 3 fiadas por identidade 46 -> 46 (0 novas); coincidentes 5,54 -> 5,61 %; MCP 72,6 -> 77,4 % exato (75,2 -> 79,9 % <= 5 cm); HUMANO 23,3 -> 23,6 %; verga/contraverga por papel 95,5 % (igual), geometrica MCP 63,6 -> 75,0 %; T 37/37, L 3, NMU 0, pecas em porta 0, canaleta como amarracao 0, paridade identica (8 inversoes).",
    "Revit copia CICLO14_CAND83_butanta_testes (caminho do produto, NONE, 280 cm): 7 068 planejadas = criadas, 0 puladas/falhas/invasoes, 0 trechos nao resolvidos; contra CICLO11 (main): compensadores 468 -> 402, junto de abertura 219 -> 168, MCP 74,7 -> 79,6 % (75,9 -> 80,7 % <= 5 cm), HUMANO 23,1 -> 23,4 %, juntas continuas 46 -> 46, unidades de diferenca MCP x SCRIPT 237 -> 160 (jamba 112 -> 50); T 37/37 (bond_trace 690), L 3 (nos 47/48), gates 75/76 0; solve 547 s + criacao 391 s (IronPython). Referencias butanta testes e TESTE PR49 intocadas.",
    "Benchmark (baseline nao regravado): compensators piloto 6 = 6, TGD V1 51 = 51, TGD V2 59 -> 57, TP1 V1/V2 65 = 65; prism igual em todos; PRISM_CONTINUOUS_JOINT sem identidade nova; criticos iguais; COMPENSATOR_CONSECUTIVE TGD V1 136 -> 114, TGD V2 270 -> 240, TP1 453 -> 419; PRISM_STAGGER_BELOW_TARGET piloto 15 -> 29 e TGD V1 730 -> 765 (nivel 2), TGD V2 651 -> 601, TP1 1 823 -> 1 763; TGD V2: inversoes da 82 11 -> 14 (2 revertidas pela 82.1 em vez de 5).",
    "Sem a guarda de junta (68 crua no NONE): 1 junta continua nova (8284522, t = 434, 11 fiadas). Sem a guarda de tier: 390 compensadores, mas pilaretes entre dois vaos virando fileira de B34 (secao 2 violada)."
  ],
  "decisions_taken": [
    "Origem do MCP COMPROVADA: butanta testes = CHANNEL do motor 37a0150 (lote 20260922-094142, 340 cm, microajuste 66 em 3 aberturas); reproduzido offline em 96,8 % exato. O MCP nao foi manual.",
    "Classe corrigida: CURRENT_DIFF_006 (68 ausente no NONE) - a maior classe atribuivel a uma unica alavanca (100/237 trechos), comprovada por ablacao nos dois sentidos, sem decisao humana pendente; gate CURRENT_DIFF_001 (junta a prumo do MCP em W03) tratado pela guarda de junta.",
    "NAO copiado: paridade 72 calibrada do CHANNEL (87 trechos; decisao D11/82 aprovada; ligada no NONE piora 479 -> 509 compensadores e cria junta a prumo em W11); fileira de B34 com 1 compensador nos pilaretes entre dois vaos (secao 2; CONFLITO 68 x 2/70 registrado).",
    "Guarda de tier: duas formas medidas e rejeitadas antes da final (por subtrecho da primeira janela: barrava a W02; por regiao inteira: liberava o pilarete)."
  ],
  "decisions_pending": [
    "CURRENT_DIFF_008: fileira de B34 (MCP/CHANNEL) x 1 compensador (secao 2, HUMANO, SCRIPT) nos pilaretes fechados por dois vaos.",
    "CURRENT_DIFF_005: estender a passagem livre 51.9 ao NONE (portas de 156 cm entre T na W02; exige presolve + pos-passe 80 + contrato de testes).",
    "CURRENT_DIFF_002: topo fora da grade 51.8 (peca da camada fina; canaleta acima obrigatoria?).",
    "CURRENT_DIFF_010: reabrir a 82 para inversao em bloco de T acoplados (-67 compensadores medidos na BUTANTA; TGD/TP1 nao medidos; T28 perde verga).",
    "CURRENT_DIFF_007/009/013/016/019: posicao do compensador, C09+C09 no canto L55, transpasse da canaleta, tocos de 99 cm, cinta de topo (DECISION-TOP-BOND-BEAM).",
    "Estender a guarda de junta ao CHANNEL (hoje ele mantem a 68 historica e a junta a prumo do MCP em W03)."
  ],
  "next_steps": ["PARAR. Proxima classe (paridade 72 x 82 / decisoes acima) depende do usuario."],
  "references": [
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/test_reparo_68_guarda_junta.py"},
    {"path": "tools/audit/s74_corpus.py"},
    {"path": "docs/checkpoints/evidence/2026-09-28-ciclo11-convergencia/current_diff_table.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-28-ciclo11-convergencia/casos_revit_ciclo14.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-28-ciclo11-convergencia/cmp12_ciclo14_resumo.txt"},
    {"path": "docs/checkpoints/evidence/2026-09-28-ciclo11-convergencia/atribuicao_por_regra.txt"}
  ]
}
```

## Pergunta

Depois de D1–D16, o que ainda separa o SCRIPT (main `1db4876`, NONE) do MCP (`butanta testes`), e qual
decisão do MCP é uma regra geral reproduzível que o HUMANO não desminta?

## Método

1. **Recuperação e baseline** (2 desligamentos do PC no meio do ciclo): estado reconstruído do Git, dos
   artefatos e das cópias RVT; nada refeito além do que se perdeu em memória. Baseline no Revit em cópia
   controlada (`CICLO11_BASE_main1db4876_butanta_testes`, 7.126/7.126 peças) e extração fresca das três
   referências (somente leitura, `IsModified` False antes e depois).
2. **Origem do MCP:** o lote carimbado nas peças (`20260922-094142`) levou à execução e ao motor exatos
   (`37a0150`, CHANNEL, 340 cm). Reprodução offline: 96,8 % exato / 98,6 % ≤ 5 cm.
3. **Ablação por regra** (motor da main offline, 12 configurações NONE ± §68/§58.2/§72cal/X e CHANNEL −
   regra): cada um dos 237 trechos de diferença MCP × SCRIPT recebeu a lista de configurações que o
   reproduzem exatamente (`atribuicao_por_regra.txt`).
4. **Tabela CURRENT_DIFF_001–021** por 6 analistas (jamba/§68, paridade dos T, versão do motor,
   aberturas, composição/prisma, HUMANO × MCP) com verificação adversarial por diferença e síntese
   (`current_diff_table.txt`). Classes A–G e prioridade 1–10 conforme o pedido.
5. **Correção da 006** em ciclos: guarda de junta (DEV1 → DEV5: isenção só contra abertura; janela
   expandida refeita, forma conservadora), guarda de tier (DEV6 → DEV8: por subtrecho da faixa
   jamba→âncora), cada passo medido offline na BUTANTÃ e nas fixtures genéricas.
6. **Pipeline progressivo:** testes focados → relacionados → benchmarks (piloto, TGD V1/V2, TP1 V1/V2,
   `main` × `c83`, identidades de `PRISM_CONTINUOUS_JOINT`) → suíte completa → Revit em cópia (CICLO14).

## Casos (Revit, CICLO11 = main × CICLO14 = §83 × MCP × HUMANO; `casos_revit_ciclo14.txt`)

- **W03 8284522, T15 → porta (guarda de junta):** fiadas ímpares ficam `B34 B34 B19` (junta a 449; legado)
  e não `B34 B19 B34` (junta a 434,5 sobre a face do B54 — MCP, 11 fiadas a prumo). 0 juntas novas.
- **W12 8284554, jamba 8079008 → T16:** `B39 B39 C09 C04` → `B39 B34 B19` = HUMANO = MCP (classe A).
- **W02 8284515, jamba 8079007 → B54 do nó 11:** `B19 C04 B39 B39 B39 C09` → `B34 B39 B39 B39` = MCP (a faixa
  tinha 2 compensadores; a fileira intermediária da §68 é recomposta pelo arranjo §61).
- **W01 8284502, pilarete de 69 cm entre 8078985 e 8079017 (guarda de tier):** fica `B39 C09 B19` (legado,
  §2, HUMANO `B39 B19 C09`), não `B34 B34` (MCP) — CONFLITO §68 × §2/§70 para o usuário.

## Top 10 diferenças atuais (depois da §83; da tabela CURRENT_DIFF)

001 junta a prumo do MCP em W03 (G no MCP/CHANNEL; o SCRIPT está correto) · 002 §51.8 topo fora da grade
(F, decisão E pendente) · 003 regra 75/D16 (F) · 004 contraverga L55/L56 (F) · 005 §51.9 no NONE (F,
decisão) · 006 §68 no NONE (**corrigida**) · 007 posição do compensador (B+F, decisão) · 008 pilaretes:
fileira × compensador (F+B, CONFLITO) · 010 paridade em bloco dos 15 T (F+D, decisão) · 012 paridade §72 ×
§82 (F, D11 aprovada — não copiar).
