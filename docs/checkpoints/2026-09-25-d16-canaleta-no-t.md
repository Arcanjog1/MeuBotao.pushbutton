# D16: verga/contraverga que para no encontro T — investigação medida (regra 75), revisão humana

```json
{
  "date": "2026-09-25",
  "scope": "current",
  "branch": "main",
  "base": "00f2afe4d7413c1759a0e37f72e0c3734bc7d76a",
  "head": "af247a73c7a4127571c6bb12bb876a8eff0c05bc",
  "pr": "not-created",
  "objective": "Ciclo D16: descobrir por que as corridas de verga/contraverga em canaleta param em certos nos T no SCRIPT/MCP enquanto o HUMANO atravessa a regiao do encontro e ganha apoio lateral, e se existe uma regra geral segura (canaleta continua + amarracao B34/B54 independente + sem colisao + regra 48) que aproxime o produto do HUMANO sem canaleta como amarracao. Sem D9-D13, sem D14/Etapa 3B, sem regravar TGD, sem mexer na regra 48 nem nos cantos L55/L56.",
  "changes": [
    "NENHUMA MUDANCA DE CODIGO DE PRODUTO. A investigacao provou que nao existe travessia segura; a regra 75 atual esta' correta para o BUTANTA.",
    "TESTES: tests/test_d16_canaleta_no_t.py (19) fixa a evidencia - T20-like (jamba na face), T26-like (jambas nas duas faces, pilar = no'), T28-like (jamba a 5 cm), NONE e CHANNEL, espelho: a parada acontece na amarracao selecionada da fiada; a canaleta estendida colide com ela; o mutante 51.6 tira a amarracao (no' sem B34/B54, gate 75 acusa), tambem com limite de 4 cm; modelo A literal deixa 0 travessias; canaleta no lugar da amarracao nunca resolve o no'; no' nao resolvido (U 55/56) continua nao resolvido; regra 48; sem hardcode. Mutacao (51.6 ligada por padrao) derruba 3 testes do CHANNEL; o NONE e' protegido pela secao 80.1.",
    "REGRAS: secao 75.1 (D16 medido, divergencias documentais, decisao pendente) e nota de estado na 51.6 (SUSPENSA desde 2026-09-18). DECISION-OPENING-REINFORCEMENT (decisao D: nota de suspensao/conflito) e channel-strategy-implementation (nota nos limites conhecidos)."
  ],
  "tests": [
    "tests/test_d16_canaleta_no_t.py: 19 passaram; rodado antes das suites relacionadas na mesma sessao (isolamento): 358 passaram (test_opening_structural_reinforcement, test_channel_reinforcement, test_channel_never_bonds, test_channel_audit_fixes, test_channel_ui_and_family_gate, test_regras_fisicas_de_encontro, test_missing_required_junction_bond, test_bond_trace_l).",
    "Suite completa sem tests/regression (inicio 13:09:17, arquivo de teste de 13:07:22; nenhum codigo de produto mudou): 1843 passaram (1824 + 19 novos), 1 pulado, 1 falhou - tests/test_perf_trace_stall_sampler.py (historica).",
    "Verificacao adversarial (3 ceticos independentes: geometria/catalogo, dados HUMANO, regras/modelos): nenhum refutou; ressalvas incorporadas.",
    "Regressao/benchmark: sem mudanca de codigo de produto em relacao a' main 00f2afe (medidos no D6: 145 ok / 3 falhas conhecidas, TGD V1 compensators 54, V2 66)."
  ],
  "known_failures": [
    "tests/test_perf_trace_stall_sampler.py (historica).",
    "tests/regression: TP1 8->9, TGD V2 86->92, TGD V1 compensators 52->54 (anteriores; baseline nao regravado).",
    "BUTANTA: 3 fiadas dos cantos L 55/56 sem amarracao (decisao do usuario)."
  ],
  "physical_deltas": [
    "NENHUMA PECA MUDA (sem mudanca de codigo de produto).",
    "INVENTARIO (motor offline na main 00f2afe = Revit CICLO8, mesmas chaves e apoios): 14 paradas no NONE, 13 no CHANNEL (a porta 8079021 do T51 e' passagem livre 51.9 so' no CHANNEL). 13 param numa B34 T_INTERSECTION_INCOMING transversal e 1 (contraverga 8079026, L56) numa B34 L_CORNER ao longo sobre o vao. Em 27/27 o bloqueador e' a amarracao SELECIONADA do no' naquela fiada (bond_trace BOND_RESOLVED; origem do candidato aceito a 0,0 cm) e a unica peca do quadrado do no'; 0 em NO_FUNCTIONAL_JUNCTION, 0 no C09 JUNCTION_UNRESOLVED_FILL. Continuar colide em 27/27 (3724 cm3 = 14x14x19 em cada T; 9044 cm3 no L56). SAFE CHANNEL CROSSINGS = 0.",
    "RESERVA GEOMETRICA: varredura de 515 configuracoes por parada (penetracao da chegada -1..14 cm; B19/B34/B39/B54 da principal deslocados +-30 cm): as 123 que cumprem a 76.1 deixam a canaleta entrar no maximo 0,1 cm. Pecas de meia altura e canaleta J so' no acervo humano (familia nova) e 9+1+19 cm > fiada de 20 cm. Com amarracao mantida o apoio medido ja' e' o maximo fisico nas 13 paradas de T.",
    "MODELOS (bancada BUTANTA, NONE): C (main) paradas 14, apoio<4 7, T 37/37, gate75 0. B (51.6 religada) paradas 14->8, apoio<4 7->1, T 37->35 (motor 22/28 x fiadas 3/11 NO_BOND_PIECE), gate75 4 CHANNEL_CROSSED_NODE_TIE. B4 (limite 4 cm, como o HUMANO no T28) apoio<4 0, T 37->33, gate75 6. A literal (51.6 com veto de toda travessia que tire amarracao) = 0 travessias = main. 51.7 isolada no L56: fiadas L sem amarracao 3->4. Nenhum modelo de travessia preserva T e L.",
    "HUMANO: 89 canaletas em regiao de no', 89/89 em fiada sem B34/B54 (0 bloco penetrando, 0 peca da principal cobrindo o no'). Categorias: CHANNEL_CROSSES_UNRESOLVED_T 29 (TOP_BELT 22, LINTEL 3, SILL 3, OTHER 1), CHANNEL_ARRIVING_ENTERS_T 16 (TOP_BELT), CHANNEL_CROSSES_L_UNRESOLVED 12 (TOP_BELT), NODE_OUTSIDE_CORPUS 32 (TOP_BELT 15, LINTEL 8, SILL 9), CHANNEL_CROSSES_RESOLVED_T 0, STOPS_BEFORE 0, TOUCHES_ONLY 0. Comparaveis ao D16: 5 (T20 c3/c11, T26 c3/c11 = mecanismo 51.6, B34 da chegada recuada para B19; T28 c11 = mecanismo 51.7, peca de no' da principal virou canaleta) - cobrem 9 das 14 paradas; em T22 e T16 o HUMANO tambem para; T51 c11 sem canaleta; L56 o HUMANO usa a paridade inversa (nao e' travessia). Jambas humanas no mesmo lugar (0,00-0,01 cm).",
    "T20 (motor 22): SCRIPT/MCP/motor - fiadas 3 e 11 com a B34 da chegada penetrando +7; verga/contraverga da 8078987 com -1,0 cm (ACTUAL_ERROR) e da 8079017 com 18,99 cm. HUMANO - CHCUT [-7,17] (c3) e CH39 [-17,22] (c11) sobre o no', chegada B19 a -8, sem amarracao; apoio 34 cm. T26 (motor 28): pilar = no' (14 cm); SCRIPT -1,0 / -1,0 cm nas 8078988 e 8079016 (c3 e c11); HUMANO CH34 [-27,7] sobre o no', B19 a -8, apoio 14 cm. T28 (motor 30): SCRIPT verga da porta 8079008 3,99 cm (KNOWN_LIMITATION), contraverga da 8079027 19,01; HUMANO CH34 [-7,27] c3/c11, B39 a -8, apoio 39 cm (porta) e 34 (janela)."
  ],
  "decisions_taken": [
    "Regra 75 mantida: nao existe regra geral segura de travessia (canaleta continua + amarracao independente + sem colisao + regra 48). O codigo de produto nao foi alterado para aproximar o HUMANO.",
    "4 e 19 cm seguem so' como metricas; a 51.4 continua como estava."
  ],
  "decisions_pending": [
    "D16 (usuario): (1) manter a regra 75 - os 6 lados com jamba na face do T (8078987, 8078988, 8079016; verga e contraverga) continuam criados com apoio -1 cm (SUPPORT_ACTUAL_ERROR, revisao) e 2 com ~4 cm (KNOWN_LIMITATION); (2) reativar a 51.6 (e/ou 51.7) aceitando fiada de T sem B34/B54 (BOND_UNRESOLVED; T amarrados 37->35 ou 33) - conflito da decisao D (2026-09-14) com a regra 75 (2026-09-18); (3) resolver pela posicao da abertura (Etapa 3B, fora deste ciclo).",
    "Rastreio da secao 80: 7 das 14 paradas rotuladas RULE_75 ja' existiam antes da politica da 75 (5 a 0,003-0,012 cm dos 19 cm; 2 com ~4 cm); campos propostos para um ciclo de rastreio: channel_crosses_junction, bond_piece, bond_resolved, channel_collision_with_bond, channel_allowed_to_continue, continuation_rule_id, support_before/after, stop_reason (medidos aqui para as 27 paradas).",
    "Fixture sintetica T26-like: o NONE deixa 3 fiadas FREE_END_NOT_COMPOSED entre as janelas onde o CHANNEL classifica NO_FUNCTIONAL_JUNCTION - independente da canaleta (igual com a secao 80 desligada); no BUTANTA o T26 da' NO_FUNCTIONAL_JUNCTION nos dois caminhos.",
    "Cinta de topo (10.7, decisao F): 65 das 89 canaletas humanas em no' sao a cinta da fiada 12, todas sem B34/B54 - se a cinta for implementada sobre os nos, a 76.1 acusara' NO_BOND_PIECE."
  ],
  "next_steps": [
    "PARAR. D9-D13 e D14/Etapa 3B nao iniciados; o destino da 51.6 e' decisao do usuario."
  ],
  "references": [
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "docs/decisions/DECISION-OPENING-REINFORCEMENT.md"},
    {"path": "docs/architecture/channel-strategy-implementation.md"},
    {"path": "tests/test_d16_canaleta_no_t.py"}
  ]
}
```

## Resposta à pergunta principal

**Não.** No BUTANTÃ nenhuma canaleta de verga/contraverga pode atravessar a região de um
T funcional sem deixar de haver B34/B54 naquela fiada. A região do nó (14 × 14 cm) é
ocupada inteira pela amarração da fiada (76.1): continuar a canaleta ou colide com ela, ou
exige retirá-la. É exatamente isso que o HUMANO faz (fiada de T sem amarração por bloco),
e é o que a regra 75 proíbe.

- **Regra de papel × ocupação.** A parada em peça de nó é a 51.4 original (2026-09-14). A
  §75 (2026-09-18) só desligou as exceções 51.6/51.7 e criou o gate por função. No BUTANTÃ
  a implementação não é mais restritiva que a intenção de papel: todas as paradas estão
  na amarração real.
- **Rastreio.** O rótulo `RULE_75` do rastreio (§80) cobre 14 paradas. Só 7 delas são efeito
  da política da §75: os 6 lados com a jamba na face em T20/T26 e o `TIE_OVER_SPAN` do L56.

## Paradas no NONE (motor = Revit CICLO8)

| caso | abertura | parede | nó motor (f3) | fiada | papel/lado | peça de amarração que parou | resolvido | colisão | apoio atual | apoio só removendo a amarração | 51.4 | parava antes da §75 | HUMANO na fiada |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W0-o2-LINTEL-R | 8079017 | 8284502 | 22 (T20) | 11 | LINTEL R | B34 T_INTERSECTION_INCOMING (8284558) | sim | 3724 cm³ | 18,988 | 33,988 | VALID_ALTERNATIVE | sim | atravessa, sem amarração |
| W0-o2-SILL-R | 8079017 | 8284502 | 22 (T20) | 3 | SILL R | B34 T_INTERSECTION_INCOMING (8284558) | sim | 3724 cm³ | 18,988 | 33,988 | VALID_ALTERNATIVE | sim | atravessa, sem amarração |
| W0-o3-LINTEL-L | 8078987 | 8284502 | 22 (T20) | 11 | LINTEL L | B34 T_INTERSECTION_INCOMING (8284558) | sim | 3724 cm³ | −0,997 | 54,003 | ACTUAL_ERROR | não | atravessa, sem amarração |
| W0-o3-SILL-L | 8078987 | 8284502 | 22 (T20) | 3 | SILL L | B34 T_INTERSECTION_INCOMING (8284558) | sim | 3724 cm³ | −0,997 | 54,003 | ACTUAL_ERROR | não | atravessa, sem amarração |
| W0-o8-LINTEL-R | 8078988 | 8284502 | 28 (T26) | 11 | LINTEL R | B34 T_INTERSECTION_INCOMING (8284562) | sim | 3724 cm³ | −0,987 | 49,013 | ACTUAL_ERROR | não | atravessa, sem amarração |
| W0-o8-SILL-R | 8078988 | 8284502 | 28 (T26) | 3 | SILL R | B34 T_INTERSECTION_INCOMING (8284562) | sim | 3724 cm³ | −0,987 | 49,013 | ACTUAL_ERROR | não | atravessa, sem amarração |
| W0-o9-LINTEL-L | 8079016 | 8284502 | 28 (T26) | 11 | LINTEL L | B34 T_INTERSECTION_INCOMING (8284562) | sim | 3724 cm³ | −1,005 | 48,995 | ACTUAL_ERROR | não | atravessa, sem amarração |
| W0-o9-SILL-L | 8079016 | 8284502 | 28 (T26) | 3 | SILL L | B34 T_INTERSECTION_INCOMING (8284562) | sim | 3724 cm³ | −1,005 | 48,995 | ACTUAL_ERROR | não | atravessa, sem amarração |
| W1-o4-LINTEL-R | 8079021 | 8284515 | 46 (T51) | 11 | LINTEL R | B34 T_INTERSECTION_INCOMING (8284580) | sim | 3724 cm³ | 18,997 | 33,997 | VALID_ALTERNATIVE | sim | sem canaleta nem amarração |
| W3-o2-LINTEL-R | 8079023 | 8284526 | 24 (T22) | 11 | LINTEL R | B34 T_INTERSECTION_INCOMING (8284559) | sim | 3724 cm³ | 18,988 | 33,988 | VALID_ALTERNATIVE | sim | amarrado, para |
| W3-o2-SILL-R | 8079023 | 8284526 | 24 (T22) | 3 | SILL R | B34 T_INTERSECTION_INCOMING (8284559) | sim | 3724 cm³ | 18,988 | 33,988 | VALID_ALTERNATIVE | sim | amarrado, para |
| W10-o0-LINTEL-L | 8079019 | 8284552 | 18 (T16) | 11 | LINTEL L | B34 T_INTERSECTION_INCOMING (8284554) | sim | 3724 cm³ | 4,003 | 19,003 | KNOWN_LIMITATION | sim | amarrado, para |
| W11-o0-LINTEL-R | 8079008 | 8284554 | 30 (T28) | 11 | LINTEL R | B34 T_INTERSECTION_INCOMING (8284563) | sim | 3724 cm³ | 3,989 | 58,988 | KNOWN_LIMITATION | sim | atravessa, sem amarração |
| W27-o0-SILL-SPAN | 8079026 | 8284584 | 48 (L56) | 1 | SILL (vão) | B34 L_CORNER (8284584) | sim | 9044 cm³ | — | 19,512 / 29,488 | — | não | amarrado (paridade inversa) |

"Apoio só removendo a amarração" é o apoio que a corrida alcançaria atravessando o nó. Só é
possível tirando a B34/B54 daquela fiada, que é a 51.6/51.7.

## Métrica D16

| métrica | valor |
|---|---|
| HUMAN D16 CASES | 5. Cobrem 9 das 14 paradas |
| SCRIPT MATCH BEFORE / AFTER | 0/5 / 0/5 (intencional) |
| SAFE CHANNEL CROSSINGS | 0 |
| BLOCKED CROSSINGS | 14 no NONE, 13 no CHANNEL |
| BOND RESOLVED WITH INDEPENDENT PIECE | 14/14 no NONE, 27/27 somando os dois caminhos |
| BOND UNRESOLVED DESPITE CHANNEL | 0 |
| COLLISIONS PREVENTED | 14/14 no NONE, 27/27 somando os dois caminhos |

## Evidência (scratchpad do ciclo, fora do repositório)

- `d16/inventario.json`: as 27 paradas, com envelopes e colisões.
- `d16/trace_d16.json`: campos da fase 12 medidos por parada.
- `d16/humano_travessias.json`: as 89 travessias do HUMANO.
- `d16/t20_26_28.json`: fiada a fiada, em 5 modelos.
- `d16/r75_audit.json`: auditoria da regra 75.
- `d16/modelos_v1.json` e `d16/verif_modelos.json`: modelos A/B/B4/C.
- `d16/verif_humano.json`, `d16/cet_geo.json` e `d16/cet_modeloA3.json`: saídas dos céticos.
