# D9/D10/D12/D13: regras gerais de composição (§81) + rótulo da parada D16

```json
{
  "date": "2026-09-25",
  "scope": "current",
  "branch": "main",
  "base": "19f7e99105dc1add40e296af95656eb9c38d0844",
  "head": "a57ddc258aaaf99de6db89d26e257115ba5d7c51",
  "pr": "not-created",
  "objective": "Ciclo D9/D10/D12/D13 com a decisao D16 do usuario: manter a regra 75 (51.6 nao volta) e corrigir SO' o rotulo da parada; investigar e corrigir o excesso de B34/compensadores e a composicao inferior do SCRIPT extraindo do CHANNEL somente as regras gerais de qualidade (sem NONE->CHANNEL, sem D11/§72, sem verga/contraverga, sem D14/Etapa 3B), sem regravar baseline.",
  "changes": [
    "532c1b9 D16 (so' rastreio): a parada da verga/contraverga em peca de no' e' rotulada pela causa - CHANNEL_STOP_RULE_75 / CHANNEL_STOP_SUPPORT_RULE / CHANNEL_STOP_EXISTING_JUNCTION_PIECE / CHANNEL_STOP_GEOMETRY (+ blocker_code, placement_reason, along); resumo com CHANNEL_STOPS_AT_JUNCTION e cada causa; TIE_OVER_SPAN so' e' RULE_75_TIE_OVER_SPAN quando a causa e' a 75. Nenhuma peca muda.",
    "a57ddc2 SECAO 81: GENERAL_COMPOSITION_QUALITY_ENABLED liga a 71 (compensadores no desempate) e o arranjo 60-65 em QUALQUER estrategia, com a aceitacao exata por parede do CHANNEL (auditoria de amarracao + auditoria FINAL de encontro 76.1/77 + apoio fisico + plano de verga/contraverga); no NONE roda depois da conversao de verga/contraverga. 68, 58.2 e 72 continuam so' no CHANNEL.",
    "SECAO 81.1: guarda de IDENTIDADE de junta no arranjo geral (arrange_b34_runs(joint_identity_guard=True)) - nenhuma troca cria junta coincidente entre fiadas vizinhas numa posicao nova; o CHANNEL mantem a aceitacao historica.",
    "Validador por parede (compartilhado): a auditoria final de encontro entra na aceitacao - no CHANNEL so' muda a fixture D3 de dois lados (3 FREE_END_NOT_COMPOSED -> 0); BUTANTA e U identicos a' main.",
    "TESTES: tests/test_regras_gerais_composicao.py (novo); contrato atualizado em test_opening_structural_reinforcement (espiao NONE: 71 e 60-65 gerais; §80 isolada com a chave desligada), test_channel_reinforcement (sentinela LEGADO_HISTORICO desliga tambem a §81; §80 isolada), test_b34_small_void_alignment (§52 isolada + teste novo), test_s74/test_regra76 (legado historico com regras_gerais=False em tools/audit/s74_corpus.py).",
    "REGRAS: §81 e §81.1; notas de estado nas §60-65 e 71 (gerais), 68 e 58.3 (so' CHANNEL), 80.1 (ordem da orientacao) e decisao D16 + rotulo na §75.1; DECISION-OPENING-REINFORCEMENT e channel-strategy-implementation."
  ],
  "tests": [
      "tests/test_regras_gerais_composicao.py: 24 passaram (composicao exata, preferencia B39, B19 sobre 2xC09, B34 necessario/desnecessario, compensador inevitavel, dois evitaveis, coluna vertical, ponta de trecho, jamba, T com amarracao preservada, prisma, espelhamento, NONE espiao, CHANNEL inalterado, 72 desligada no NONE, guarda de junta, aceitacao por parede nunca cria encontro faltando, sem hardcode).",
      "Arquivos relacionados (legado historico, corpus s74/regra76, amarracao, encontros, arranjo): 477 passaram. CR-G12 (TGD/TP1 reais): 20 passaram - inclusive test_nenhuma_junta_continua_nova_em_lugar_nenhum[torre_easy_lo_r00_tp1], que falhava antes da secao 81.1.",
      "Suite completa sem tests/regression (worktree com este codigo, 17:01-18:18): 1875 passaram, 1 pulado, 7 falharam - 6 testes de inspecao de fonte (inspect.getsource) quebrados por uma edicao de COMENTARIO em wall_modeling.py feita durante a execucao; com o arquivo estavel os 6 e seus 4 arquivos passaram (124). Resta 1 falha historica (test_perf_trace_stall_sampler).",
      "tests/regression: 146 passaram, 2 falharam (anteriores: TP1 JUNCTION_MISSING_BINDING 8->9; TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92). A falha TGD V1 compensators 52->54 da main deixou de existir.",
      "Arvore da main com o codigo commitado: 195 passaram (regras gerais, D16, secao 80, secao 52, CHANNEL, arranjo).",
      "Assinatura fisica forte (x_dir/espelho/comprimento): BUTANTA NONE ba678854a0190241 (7 225 pecas; identica com e sem a guarda 81.1), CHANNEL bc9331b84fd0df5e = main, U NONE = U CHANNEL e11ca611f07eeff6 = main. Rotulo D16: NONE/CHANNEL/U identicos a' main."
  ],
  "known_failures": [
      "tests/test_perf_trace_stall_sampler.py (historica).",
      "tests/regression: TP1 V1 JUNCTION_MISSING_BINDING 8->9 e TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 (anteriores; criticos identicos com e sem a secao 81; baseline nao regravado).",
      "BUTANTA: 3 fiadas dos cantos L 55/56 sem amarracao (decisao do usuario); D10/D12 por paridade (D11)."
  ],
  "physical_deltas": [
      "D16 (rotulo): nenhuma peca muda.",
      "BUTANTA NONE (motor offline, regua forense, 34 eixos): B39 3930->3841, B34 1797->1898 (amarracao 472->472), B19 283->392, C04 366->255, C09 460->300; compensadores 826->555 (11,2->7,68 %; HUMANO 487/7,34 %, MCP 397/5,65 %); colunas de compensador >=4 117->73; faixas verticais >=4 11->3; C09+C09 9->2; vazado menor 251->35; juntas coincidentes 5,27->5,41 %; juntas continuas >=3 fiadas por identidade 46->46 (0 novas); MCP 53,0->57,0 %, HUMANO 19,3->21,1 %; estrutura identica (T 37/37, L 3, NMU 0, vazio 30, invasoes 0, gate 75/76 0, verga/contraverga mesmo resumo).",
      "CHANNEL: assinatura identica a' main na BUTANTA e no U; a auditoria final de encontro no validador compartilhado muda so' a fixture D3 de dois lados (3 FREE_END_NOT_COMPOSED -> 0).",
      "Revit copia CICLO9 (caminho do produto, NONE): 7 220 planejadas = criadas, 0 puladas/falhas; contra CICLO8 (main): compensadores 796->550, colunas >=4 111->72, MCP 54,3->58,7 %; amarracao por no'/fiada identica (T 462, L 141). Tres RVTs de referencia intocados."
  ],
  "decisions_taken": [
    "D16 (usuario): regra 75 mantida; 51.6/51.7 nao voltam; AMARRACAO VALIDA > CONTINUIDADE/APOIO; apoio insuficiente segue REVISAO HUMANA / KNOWN_LIMITATION.",
    "Extraidas do CHANNEL (GENERAL_MODULATION_QUALITY, sem dependencia de canaleta): 60, 61, 62, 63, 64, 65, 71. Mantidas so' no CHANNEL: 68 (AMBIGUOUS - cria junta a prumo), 58.2 (regressao TP1), 72 (D11).",
    "Guarda de identidade de junta so' no caminho geral; estender ao CHANNEL fica pendente (mudaria a assinatura CHANNEL).",
    "Baselines NAO regravados."
  ],
  "decisions_pending": [
    "§68 com guarda de junta (555 -> 449 compensadores medidos na ablacao) - proximo candidato.",
    "D10/D12 sao paridade (§72) - D11, fora deste ciclo.",
    "Estender a guarda 81.1 ao CHANNEL.",
    "D14/Etapa 3B nao iniciados."
  ],
  "next_steps": ["PARAR. D11 e D14/Etapa 3B nao iniciados."],
  "references": [
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/b34_run_arrangement.py"},
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/test_regras_gerais_composicao.py"},
    {"path": "tests/test_d16_canaleta_no_t.py"},
    {"path": "tools/audit/s74_corpus.py"}
  ]
}
```

## Resposta

**Sim, a composição do NONE melhora, com a estrutura intacta, o prisma não degrada e os
benchmarks resolvem as duas regressões de compensadores.** A melhoria vem de regras que já existiam
e só estavam presas ao CHANNEL. Nenhuma lê canaleta: a 71 e o arranjo 60–65 foram extraídos como
regras gerais de composição (§81). A 68 fica só no CHANNEL, porque cria junta a prumo, e a 72 é
paridade (D11). Durante o ciclo apareceu um defeito de prisma na aceitação herdada, e ele foi
corrigido antes do commit (§81.1).

Arquitetura: **solver base + regras gerais de qualidade (§81) + estratégia CHANNEL opcional**
(51.x, 58.2, 68, 72).

## D16 — decisão e rastreio

- A regra 75 foi mantida e a 51.6/51.7 não volta: AMARRAÇÃO VÁLIDA > CONTINUIDADE/APOIO. Continuam 37/37 T amarrados e 0 canaletas como amarração.
- Rastreio: a parada passou a trazer a causa. No NONE ficam 7 `CHANNEL_STOP_RULE_75`, 5 `CHANNEL_STOP_SUPPORT_RULE`, 2 `CHANNEL_STOP_EXISTING_JUNCTION_PIECE` e 0 `CHANNEL_STOP_GEOMETRY`; no CHANNEL, 7 / 4 / 2 / 0.
- Nenhuma peça muda: as assinaturas NONE, CHANNEL e U são idênticas às da main (commit do rótulo).

## Inventário §60–§65, §71 (fases 1, 9, 10)

| Regra | Função | Chave | Onde o CHANNEL liga | Lê canaleta? | Classificação | Efeito medido (BUTANTÃ NONE, "sem X" = §81 − X) |
|---|---|---|---|---|---|---|
| 60 | reordenação das corridas (vazado menor) | `B34_RUN_ARRANGEMENT_ENABLED` | `_orient_small_voids_final(arrange=True)` no pós-passe | não (canaleta excluída das corridas) | GENERAL | base de 61–65; sem 60–65: COMP 809, vazado 265 |
| 61 | composição de mesmo comprimento | `B34_RUN_COMPOSITION_ENABLED` | idem | não | GENERAL | sem ela COMP 555 → 809 |
| 62 | orientação exata (DP) | `B34_ORIENTATION_DP_ENABLED` | idem | não | GENERAL | sem ela vazado 35 → 68 |
| 63 | orientação conjunta (vizinhos/pares) | `NEIGHBOUR_FLIPS_ENABLED`, `PAIR_FLIPS_ENABLED` | idem | não | GENERAL | sem ela COMP 662, vazado 47 |
| 64 | reparo de abertura móvel | `B34_RUN_OPENING_REPAIR_MOVABLE` | idem | não | GENERAL | sem ela COMP 752, vazado 107 |
| 65 | passes | `B34_RUN_ARRANGEMENT_PASSES` | idem | não | GENERAL | sem eles COMP 579, vazado 45 |
| 71 | compensadores no desempate | `CHANNEL_COMPENSATOR_TIEBREAK_ENABLED` | `_solve_building_blocks_all_courses_impl` (`strategy is not None`) | não | GENERAL | sozinha 826 → 809; sem ela 555 → 579 |
| 68 | melhor composição do reparo | `CHANNEL_REPAIR_PREFER_CLEAN_ENABLED` | idem | não | AMBIGUOUS | junta a prumo 11 fiadas (8284522); TGD V2 PCJ 53 → 108 — **não extraída** |
| 58.2 | peça de canto degradado | `CHANNEL_CORNER_DEGRADED_TIE_BLOCK_ENABLED` | idem | não | GENERAL (nó) | inerte na BUTANTÃ; TP1 PCJ 16 → 32 — **não extraída** |

## Métricas BUTANTÃ (régua forense, 34 eixos, NONE)

| | HUMANO | MCP | SCRIPT antes (main) | SCRIPT depois (§81) |
|---|---|---|---|---|
| B39 | 3.060 | 4.014 | 3.930 | 3.841 |
| B34 | 1.615 | 1.739 | 1.797 | 1.898 (amarração 472 → 472) |
| B19 | 324 | 356 | 283 | 392 |
| C04 | 245 | 166 | 366 | 255 |
| C09 | 242 | 231 | 460 | 300 |
| compensadores | 487 | 397 | 826 | **555** |
| taxa de compensador | 7,34 % | 5,65 % | 11,2 % | **7,68 %** |
| faixas verticais de compensador ≥ 4 fiadas | 26 | 3 | 11 | 3 |
| colunas de compensador ≥ 4 (mesma posição) | 64 | 53 | 117 | 73 |
| aderência ao MCP (exato/≤ 5 cm) | 22,6/33,9 | — | 53,0/56,2 | 57,0/59,9 |
| aderência ao HUMANO (exato/≤ 5 cm) | — | 22,7/33,9 | 19,3/28,4 | 21,1/30,3 |
| juntas coincidentes com a fiada de baixo | 9,19 % | 5,81 % | 5,27 % | 5,41 % |
| juntas repetidas em 3 fiadas seguidas (régua forense) | 82 | 48 | 46 | 46 (por identidade ≥ 3 fiadas: 0 novas) |
| `C09+C09` onde cabe B19 | 0 | 2 | 9 | 2 |
| vazado menor desalinhado | — | — | 251 | 35 |

**22 eixos equivalentes (fiadas 0–11):** HUMANO B34 715 / B39 1.436 / COMP 158; MCP 686 / 1.503 / 113;
SCRIPT antes 906 / 1.299 / 168; SCRIPT depois 930 / 1.281 / 132; CHANNEL − 72 925 / 1.285. Aderência
ao MCP 43,7/44,9 → 47,0/47,2 %, ao HUMANO 16,1/35,6 → 16,4/36,1 %. O excesso de B34 nesses eixos é da
paridade dos T (§72, D11) e não da composição.

## D9 — compensadores por contexto (feição mais próxima a 45 cm)

| contexto | HUMANO | MCP | SCRIPT antes | SCRIPT depois |
|---|---|---|---|---|
| junto de abertura | 284 | 148 | 394 | 221 |
| junto de nó | 185 | 207 | 369 | 292 |
| ponta livre | 13 | 42 | 56 | 42 |
| miolo | 5 | 0 | 7 | 0 |

**B34 por papel (fase 5):** amarração 472 → 472; miolo 846 → 876; fechamento 332 → 392; jamba
120 → 117; ponta livre 27 → 41. A correção é de composição, não de amarração.

## D10 (8284580, fiada 0)

- HUMANO: `B39 B39 B39 B39 B34`; MCP: `B34 B39 B39 B39 B39`.
- SCRIPT antes: `B39 B34 B34 B34 B34`; SCRIPT depois: `B34 B39 B34 B34 B34`.
- O mecanismo é paridade: os dois T usam a mesma fiada no NONE, e só a §72 alterna. **D10 não se resolve neste ciclo (D11).**

## Fase 4 — B19 sobre 2×C09

- O motor já funde `C09+C09` em B19 só na ponta aberta (`_merge_adjacent_compensator_pairs`). A composição de mesmo comprimento (61) faz o resto: 9 → 2 na BUTANTÃ (MCP 2, HUMANO 0).
- Nenhuma regra nova foi criada.

## Fase 7 — função de qualidade (código)

- `_pier_layout_avoiding_joints._score` = (excesso de compensador #2, juntas coincidentes #1, nº de compensadores §71, −trava, −alinhamento).
- Reparo §68: `_repair_solution_quality` = (compensadores, B19, B34/B54, peças), **sem critério de junta**. Por isso a 68 não foi extraída.
- Arranjo: guardas (contagens de juntas coincidentes, compensadores encostados, compensador longo na ponta, meio bloco junto de amarração, juntas empilhadas) antes do vazado menor. Com a §81.1 soma-se a identidade de junta.
- Estrutura (amarração, encontro, apoio, verga/contraverga) é aceitação dura por parede.

## Benchmarks (baseline NÃO regravado)

| Projeto | `compensators` baseline | antes (main) | **depois (§81)** | `prism` antes → depois | `PRISM_CONTINUOUS_JOINT` | `PRISM_STAGGER_BELOW_TARGET` | `COMPENSATOR_CONSECUTIVE` | `COMPENSATOR_VERTICAL_STRIP` |
|---|---|---|---|---|---|---|---|---|
| TGD V1 | 52 | 54 | **52** | 11 → 11 | 231 → 215 | 802 → 772 | 296 → 138 | 80 → 71 |
| TGD V2 | 61 | 66 | **60** | 5 → 5 | 53 → 53 | 769 → 740 | 428 → 262 | 110 → 103 |
| TP1 V1 | 74 | 76 | **66** | 8 → 4 | 16 → 4 | 1690 → 1734 | 851 → 471 | 149 → 132 |
| TP1 V2 | 77 | 76 | **66** | 8 → 4 | 16 → 4 | 1690 → 1734 | 851 → 471 | 149 → 132 |
| piloto 2x2 | 10 | 10 | **6** | 1 → 1 | 3 → 3 | 15 → 15 | 36 → 0 | 18 → 9 |

As duas regressões de compensadores abertas desde o ciclo 3 ficam resolvidas (TGD V1 54 → 52 = baseline;
TGD V2 66 → 60, abaixo do baseline 61) e o TP1 cai 76 → 66. Categoria `prism` não piora em nenhum projeto
(TP1 8 → 4); `PRISM_CONTINUOUS_JOINT` não sobe em nenhum (TGD V1 231 → 215, TP1 16 → 4 — com a guarda
§81.1). Custo medido: `PRISM_STAGGER_BELOW_TARGET` do TP1 1.690 → 1.734 (+2,6 %; nível 2, não reprova;
nos TGD cai). Os achados CRÍTICOS de cada projeto são idênticos com e sem a seção (as regressões críticas
conhecidas — TGD V2 e TP1 V1 — são anteriores e não mudam).

`tests/regression`: 146 passaram, 2 falharam. As duas falhas já existiam antes deste ciclo:
- TP1 `JUNCTION_MISSING_BINDING` 8 → 9;
- TGD V2 `COVERAGE_ROW_MOSTLY_EMPTY` 86 → 92.

Na main eram 145 / 3. A terceira falha, TGD V1 `compensators` 52 → 54, **deixou de falhar**.

## Revit (cópia `CICLO9_butanta_testes`, motor desta entrega, caminho do produto, NONE)

A criação fechou 7.220 planejadas = 7.220 criadas, com 0 puladas e 0 falhas. Também deu 0 invasões, 0 trechos não resolvidos, gate 75 = 0 e gate 76 = 0. As pendências (3 fiadas L) são as mesmas do CICLO8. Paradas: 7 / 5 / 2 / 0. Os três RVTs de referência não foram tocados (`IsModified` igual antes e depois).

Contra a cópia CICLO8 (main, mesmo caminho):
- compensadores 796 → 550;
- colunas ≥ 4 fiadas 111 → 72;
- aderência ao MCP 54,3 → 58,7 %;
- juntas coincidentes 5,23 → 5,39 %;
- amarração por nó/fiada pela régua forense: T 462 → 462, L 141 → 141, nenhuma perdida. As 10 fiadas-nó com peça diferente são nós de paredes fora do corpus, sem amarração nos dois.

Casos conferidos peça a peça:
- **Ponta com compensador** (8284574, fiada 0, fim): `B39 B39 C09` → `B39 B34 B19`, igual ao MCP (HUMANO `B34 B39 B39 C04`). 7 pontas deixaram de terminar em compensador.
- **Sequência vertical** (8284502, t ≈ 1.682, fiadas 6–10): a coluna `B39 C09 C04` virou `B34 B19`, igual ao MCP (HUMANO `C09 C04 B39`). 44 colunas ≥ 4 sumiram.
- **Jamba** (8284502, abertura 8078987, t = 800, fiada 6): `C09 B39 C04` → `B19 B34`, igual ao MCP (HUMANO `B39 C04 C09`). Compensadores a ≤ 45 cm de jamba: 528 → 335 (HUMANO 337, MCP 242).
- **Perto de T**: a peça do nó e a penetração são idênticas em 722/732 fiadas-nó; muda só o preenchimento seguinte (ex.: B39 [15,54] → B34 [15,49]).
- **D10**: `B39 B34 B34 B34 B34` → `B34 B39 B34 B34 B34` (paridade, igual ao offline).
