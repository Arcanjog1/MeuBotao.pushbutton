# D11: paridade contextual dos encontros T (§82 / §82.1)

```json
{
  "date": "2026-09-25",
  "scope": "current",
  "branch": "main",
  "base": "4b5c9e3ae5cf974dcf0473febaa66cdf2b559f98",
  "head": "632fb14dc62a302bb0726acf7f1b190bbb0d4c7b",
  "pr": "not-created",
  "objective": "Ciclo D11: achar a regra GERAL de escolha da paridade dos T dirigida por funcao objetivo - sem copiar MCP, sem copiar HUMANO por id, sem simplesmente ligar a §72 no NONE - com restricoes duras primeiro, sem §68, sem D14/Etapa 3B, sem mexer em D6, D16/regra 75 e cantos L55/L56, sem regravar baseline.",
  "changes": [
    "632fb14 SECAO 82: GENERAL_TIE_PARITY_ENABLED liga a busca de paridade pelo preenchimento (72) sem reforco adicional, com: veto estrutural antes do custo (falha de no', conflito de papel, interpenetracao de pecas de no'); custo por parede com DESENCONTRO entre as fiadas (_tie_parity_fill_stagger_cost) e ordem compensadores -> pecas nao-inteiras -> pecas (TIE_PARITY_FILL_COST_ORDER); aberturas ativas na banda so' vetam (modo veto); so' encontros T (TIE_PARITY_FILL_NODE_KINDS); guarda de verga mantida; decisao unica por planta visivel nas bandas seguintes (tie_parity_fill_flips / tie_parity_fill_rejected).",
    "SECAO 82.1: o preenchimento REAL, comparado com o da convencao (o mesmo pipeline sem a busca, resolvido uma vez quando ha' inversao, estado dos nos restaurado), tem a ultima palavra - T invertido que piora a sua regiao (paredes do no', 60 cm) em junta a prumo (#1), fiada vazia (cobertura) ou compensadores aglomerados (#2) volta a' convencao e o pipeline re-resolve (<= 2 rodadas); tie_parity_prism_check no resultado.",
    "CHANNEL inalterado (custo calibrado da 72, T e X, sem 82.1).",
    "TESTES: tests/test_paridade_contextual_t.py (novo, 40); contrato atualizado em test_tie_parity_fill_balance (decisao unica devolvida sem nova busca), test_opening_structural_reinforcement (espiao NONE: 72/82 gerais, 68 nunca), test_regras_gerais_composicao e test_regras_fisicas_de_encontro (espioes com a 82), test_b34_small_void_alignment (secao 52 medida sobre a MESMA paridade), test_channel_reinforcement (LEGADO_HISTORICO desliga a 82), test_block_b19_residual_fill_implementation (t48: paredes 88/90 do TP1 saem do conjunto elegivel do B19 residual pela paridade invertida dos T 149/153 - 8 tentativas nas paredes 12-15, contrato igual), tools/audit/s74_corpus.py (legado historico com a 82 desligada)."
  ],
  "tests": [
    "tests/test_paridade_contextual_t.py (novo): 40 passaram - chaves, principio no preenchimento real (sala fechada: menos compensadores, sem encontro faltando, sem NMU/colisao, sem junta a prumo nova), sem ganho fica a convencao, observabilidade, determinismo, espelhamento, chave desligada = convencao, CHANNEL com o custo calibrado da 72, so' T no caminho geral, X na convencao (fixture com dois X), §68 nao executa, custo com desencontro puro, ordem do custo, bloco inteiro do catalogo, veto estrutural, 82.1 (junta, fiada vazia, aglomeracao, comparacao com a convencao, convencao interna = solve com a chave desligada peca a peca, limite de rodadas), sem hardcode (13 funcoes).",
    "Arquivos relacionados (paridade, NONE espiao, regras gerais, encontros, vazado menor, CHANNEL): 200 passaram.",
    "Suite completa sem tests/regression (10 processos por arquivo): 1923 passaram, 1 pulado, 2 falharam - test_perf_trace_stall_sampler (historica) e test_t48_tp1_zero_candidatos_aceitos_apos_gate_de_integridade (contagem exata: os T 149 e 153 do TP1 passam a ter a paridade invertida e as paredes 88/90 saem do conjunto elegivel do B19 residual; atualizado para 8 tentativas nas paredes 12-15 com a explicacao, contrato do gate igual; passou isolado).",
    "tests/regression: 146 passaram, 2 falharam (as mesmas da main: TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92).",
    "Estresse sintetico (278 salas fechadas limpas): 7 melhores, 0 piores, -168 compensadores.",
    "Assinatura fisica forte: CHANNEL bc9331b84fd0df5e = main; U NONE = U CHANNEL e11ca611f07eeff6 = main; BUTANTA NONE fb42c2a9f9bd3ddd (7 131 pecas, muda por decisao desta secao). Convencao interna da 82.1 identica peca a peca ao NONE da main (7 225 pecas)."
  ],
  "known_failures": [
    "tests/test_perf_trace_stall_sampler.py (historica).",
    "tests/regression: TP1 V1 JUNCTION_MISSING_BINDING 8->9 e TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 (anteriores; baseline nao regravado).",
    "BUTANTA: 3 fiadas dos cantos L 55/56 sem amarracao (decisao do usuario)."
  ],
  "physical_deltas": [
    "BUTANTA NONE (motor offline, regua forense, 34 eixos): compensadores 555->479 (7,68->6,72 %; HUMANO 487, MCP 397); junto de no' 292->202; B39 3841->4032; B34 1898->1707 (amarracao 472->472); B19 392->377; C04 255->210; C09 300->269; juntas continuas 46->46 (0 novas); MCP 57,0->71,7 %, HUMANO 21,1->23,3 %; T 37/37, L 3, NMU 0, vazio 30, invasoes 0, gates 75/76 0. 8 T invertidos (f3 2, 4, 33, 34, 35, 48, 50, 58), 0 revertidos.",
    "22 eixos: B34 930->702, B39 1281->1491, COMP 132->108.",
    "Paridade (38 T): convencao 0/37/1 -> 8 par / 29 impar / 1 misto (HUMANO 17/20/1, MCP 11/26/1); consenso HUMANO=MCP 20 -> segue 18; divergencia 18 -> MCP 15, HUMANO 3.",
    "D10 = arranjo do MCP (4 B39 + o B34 da amarracao por fiada, 0 compensador; o HUMANO e' o espelho equivalente).",
    "Benchmark (baseline nao regravado): compensators TGD V1 52->51, TGD V2 60->59, TP1 V1/V2 66->65, piloto 6->6; prism e PRISM_CONTINUOUS_JOINT iguais (0 identidades novas); criticos iguais. TGD V2 COMPENSATOR_CONSECUTIVE 262->270 e EXCESS_IN_RUN 369->377 (residuo); TP1 PRISM_STAGGER_BELOW_TARGET 1734->1823 (nao critico). Solve 2,7-4x a main.",
    "Revit copia CICLO10 (caminho do produto, NONE): 7 126 planejadas = criadas, 0 puladas/falhas; contra CICLO9: compensadores 550->468, junto de no' 292->202, juntas continuas 46->46 (0 novas), MCP 58,7->73,8 %; referencias intocadas. Motor final (82.1 comparativa) resolvido de novo no Revit: mesmas contagens por codigo e inversoes; solve 612 s no IronPython.",
    "Assinatura fisica: CHANNEL bc9331b84fd0df5e = main; U NONE = U CHANNEL e11ca611f07eeff6 = main; BUTANTA NONE fb42c2a9f9bd3ddd (7 131 pecas; muda por decisao desta secao)."
  ],
  "decisions_taken": [
    "§72 classificada MIXED: principio GERAL, calibracao CHANNEL_SPECIFIC (custo continuo sem desencontro, pecas primeiro, dependente do reparo de jamba da §68).",
    "Regra geral = §82 + §82.1 (acima); ordem do custo compensadores primeiro pela regua do projeto humano (fase 7: HUMANO 25/25 arestas T-T, MCP 23/25, convencao 14/25).",
    "X fica na convencao no caminho geral (sem evidencia humana; medido nocivo no TGD).",
    "§68 NAO executada; D14/Etapa 3B nao iniciados; baselines NAO regravados."
  ],
  "decisions_pending": [
    "Residuo de compensadores encostados no TGD V2 (+8 CONSECUTIVE/+8 EXCESS_IN_RUN) - a 82.1 compara a contagem por fiada junto do no', nao a adjacencia.",
    "Custo de tempo (segundo solve da convencao): 612 s no Revit para a BUTANTA.",
    "f3 15 (consenso HUMANO=MCP=par) depende da §68 para nao deixar junta a prumo na jamba.",
    "X no caminho geral; §68 com guarda de junta; D14/Etapa 3B."
  ],
  "next_steps": ["PARAR. §68 e D14/Etapa 3B nao iniciados."],
  "references": [
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/test_paridade_contextual_t.py"},
    {"path": "tools/audit/s74_corpus.py"}
  ]
}
```

## Pergunta

A paridade dos T era uma convenção fixa por papel (a principal hospeda sempre na mesma fiada): 37 ímpar
/ 1 misto contra HUMANO 17 par / 20 ímpar e MCP 11 / 26. A §72 escolhia a paridade pelo que ela deixa para
preencher, mas só no CHANNEL. Existe uma regra GERAL, explicável, determinística e estruturalmente segura?

## Método (fases 1–19)

1. **Inventário** dos 37 T avaliáveis: paridade HUMANO/MCP/SCRIPT, as duas paridades simuladas com o
   pipeline completo (S1 = só o nó invertido; S2 = solução da 72 com o nó trocado), composição,
   compensadores, B39/B34, junto de nó, junta nova, penalidades de abertura.
2. **Auditoria da §72** (candidatos, escala, custo, desempate, lados, aberturas, prisma, vizinhos) e
   ablação NONE × NONE+72: MIXED (ver REGRAS §82).
3. **Régua do projeto humano** (fase 7, verificada por refutação): compensadores primeiro, depois peças
   não-B39 — HUMANO 25/25 arestas T–T; divergência HUMANO×MCP = soluções espelhadas + 2 decisões de aresta.
4. **Função objetivo**: restrições duras (veto estrutural, verga) → custo com desencontro, compensadores
   primeiro → aberturas só vetam → preenchimento real comparado com a convenção (82.1).
5. **Estresse** (278 salas fechadas limpas): 7 melhores, 0 piores, −168 compensadores.
6. **Benchmarks** TGD V1/V2, TP1 V1/V2, piloto — cada variante medida (tabela abaixo).
7. **Revit** em cópia controlada.

## Variantes medidas nos benchmarks (categoria compensators, TGD V1 / TGD V2; main 52 / 60)

| Variante | TGD V1 | TGD V2 | Achado que a derrubou |
|---|---|---|---|
| 72 simples no NONE (peças primeiro, sem desencontro) | — | — | junta a prumo nova na BUTANTÃ (jamba, sem §68) |
| 82 inicial (aberturas da banda + veto estrutural, sem desencontro) | — | — | TGD/TP1: 144/32 juntas contínuas novas, todas a 27–28 cm de um T invertido |
| 82 T+X, peças primeiro, prisma absoluto | 53 | 62 | compensadores |
| 82 T+X, compensadores primeiro, prisma absoluto | 53 | 60 | TGD V1 `COVERAGE_MISSING_ROW` 232 → 240 (crítico) |
| + cobertura | 54 | 60 | X: corrida de compensador junto de jamba (2 paredes) |
| só T | 52 | 61 | TGD V2 `C09 C04` encostados junto do T (+17/+19) |
| **só T + 82.1 comparativa (final)** | **51** | **59** | — |

## Casos no Revit (CICLO10 × CICLO9 × HUMANO × MCP)

- **D10** (8284580): `B34 B39 B34 B34 B34 | B34×5` → `B34 B39 B39 B39 | B39 B39 B39 B39` = MCP; HUMANO é o
  espelho (`B39 B39 B39 B39 | B34 B39 B39 B39`).
- **T com HUMANO = MCP** (f3 2, 8284551): `B39 B39 B39 C04 B54 B39 B39 B39 C09` → `B39 B34 B34 B34 B34 B39
  B39 B34` = MCP; compensadores junto do nó 14 → 0.
- **T com HUMANO ≠ MCP** (f3 48, 8284563/8284579): segue o MCP (fase relativa igual à do HUMANO, absoluta
  espelhada).
- **Dois T próximos na mesma parede** (f3 50 e 48, 8284563, 210 cm): os dois B54 na mesma fiada, como o
  MCP; fiada 0 `B39 B39 B39 B34 B39 B39 B39 B39`.
- **Abertura perto de T** (f3 4, porta a 47 cm): o C04 sai da parede que chega (`C04 B39 …` → `B34 B39 …`)
  e vira fechamento de jamba na principal; é um dos 2 consensos HUMANO = MCP que a regra quebra
  (compensadores primeiro).
