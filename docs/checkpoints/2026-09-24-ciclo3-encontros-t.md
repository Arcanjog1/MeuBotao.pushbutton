# Ciclo 3 (D2/D3): amarração dos encontros T — regras físicas de encontro sem depender do reforço (seção 79) e rastreio `bond_trace`

```json
{
  "date": "2026-09-24",
  "scope": "current",
  "branch": "main",
  "base": "15bacec9d5edc58beaf969c78c7c8d0802f8979e",
  "head": "367eb0c86f2136ef5da4b957d5d0be6dfcc49439",
  "pr": "not-created",
  "objective": "Ciclo 3 apos a comparacao forense: corrigir D2 (no 51, pilar de 54 cm entre duas portas) e D3 (nos 20/26 na 8284502 e 28 na 8284554) - encontros T sem amarracao que continuavam iguais depois dos ciclos 1 e 2 com o corpus correto de 34 eixos. Rastrear cada candidato de amarracao por no'/fiada, distinguir candidato NAO GERADO de candidato GERADO E REJEITADO, provar a causa antes de mexer, sem paridade (72), sem hardcode, regra 48 intacta, sem tocar D6/D9-D13/3B/D16/baseline.",
  "changes": [
    "MOTOR (nuvem/core/wall_modeling.py): JUNCTION_PHYSICAL_RULES_ENABLED = True (secao 79). No caminho SEM reforco, `_solve_building_blocks_all_courses_impl` (ponto unico das duas portas) liga as regras fisicas de encontro que ja' existiam e so' valiam no CHANNEL: T_ROOM_PHYSICAL_TOLERANCE (74), T_DEGRADED_L_ROOM_FROM_CONTACT (76 D1), JUNCTION_ROLE_BY_COURSE (77) e COMPENSATOR_NODE_PIECE_UNDESIGNATED (76.1), com restauracao no finally. No CHANNEL continuam as chaves CHANNEL_* de sempre. Nenhum valor/tolerancia novo. Continuam so' CHANNEL: 58.2, 68, 71 e a paridade 72.",
    "GATES (wall_modeling.py): `_attach_junction_gates` - o mesmo codigo anexa ao resultado, nos DOIS caminhos, o gate 76 (COMPENSATOR_AS_JUNCTION_BOND), o 76.1 (MISSING_REQUIRED_JUNCTION_BOND + junction_bond_audit), o relatorio da 77 e o rastreio. Sem reforco isso so' acontece com a secao 79 ligada (desligada = motor anterior, testado). A auditoria usa o papel por fiada com a MESMA chave do solve (`role_by_course`).",
    "RASTREIO (wall_stepper.py + wall_modeling.py): BOND_TRACE/BOND_TRACE_BAND (contexto); `solve_t_intersection` virou invólucro de `_solve_t_intersection_steps` e anexa `trace` com os testes fisicos na ordem (T_B54_B34 com espaco medido x exigido e tolerancia, T_DEGRADED_L_B34, T_DEGRADED_L_FROM_CONTACT, T_SINGLE_ELEMENT); `solve_all_intersections` grava o passo de cada no' L/T/X (so' a passada principal); cada passada do solver leva o PROPRIO rastreio (`_solve_building_blocks_all_courses_pass` invólucro) - o resultado escolhido (melhor passada, reconstrucao de paridade, reparo aceito) descreve a si mesmo; `junction_bond_audit` devolve tambem `resolved` (a peca que amarrou); `_bond_trace_from_result` monta, por no'/fiada fisica: papel, paredes, espaco medido, candidatos gerados (codigo, origem, rotacao, razao, familia FISICA e `accepted` na fiada, casamento por codigo + origem a <= 0,05 cm), testes reprovados, peca selecionada, bond_resolved e a classificacao BOND_RESOLVED / NO_FUNCTIONAL_JUNCTION / BOND_CANDIDATE_NOT_GENERATED / BOND_CANDIDATE_GENERATED_BUT_REJECTED (DROPPED_AFTER_NODE_STEP, AUDIT_*, REGRA_48_*); `_bond_trace_apply_materialization` (regra 48) roda ja' no `_execute_solve`, antes do relatorio; `_format_block_solve_report` lista 'AMARRACAO POR NO'/FIADA (bond_trace, secao 79)' + pendencias.",
    "REGRAS: secao 79 nova.",
    "TESTES: tests/test_regras_fisicas_de_encontro.py (21): interruptor e chaves que nao vazam; paridade 72 nunca roda sem reforco (espiao) e liga no CHANNEL (controle); D2-like (pilar de 54 cm - 0,08 mm entre duas portas -> B54/B34 em todas as fiadas; antes: C09 e rastreio NOT_GENERATED com o motivo); D3 um lado (B34 do contato nas fiadas da janela); D3 dois lados (NO_FUNCTIONAL_JUNCTION na faixa, ponta livre composta); impossivel (MISSING + C09 JUNCTION_UNRESOLVED_FILL + rastreio NOT_GENERATED com 7,000/20,000 + revisao humana, 0 invasao); normal identico com e sem a 79; paridade preservada abaixo das janelas; canaleta nunca amarra (com prova nao vacua: canaleta no lugar do B54 -> auditoria acusa); CHANNEL continua resolvendo; as duas falhas do rastreio; casamento por tolerancia; campos + relatorio; regra 48 no rastreio pelo `_execute_solve`; papel da auditoria com a chave CHANNEL desligada; detalhe culpa o lado certo; rastreio por passada; familia do rastreio = fiada fisica; banda de uma so fiada nao inventa descarte; anti-hardcode (tokenize de wall_modeling e wall_stepper). Testes que fixavam o HISTORICO do legado passaram a usar a sentinela `tcr.LEGADO_HISTORICO` (secao 79 desligada) e o legado do produto ganhou asserts proprios (test_channel_reinforcement, test_compensator_never_bonds, test_missing_required_junction_bond, test_regra761_revisao_do_gate, test_regra76_d1_t_degradado, test_regra76_corpus_butanta, test_s74_corpus_butanta; tools/audit/s74_corpus.py ganhou `regras_de_encontro=None`). Nenhum golden/snapshot/threshold/xfail/skip alterado."
  ],
  "tests": [
    "Ciclo 3: tests/test_regras_fisicas_de_encontro.py 21 passaram. Arquivos adaptados (legado historico por sentinela): test_channel_reinforcement, test_compensator_never_bonds, test_missing_required_junction_bond, test_regra761_revisao_do_gate, test_regra76_d1_t_degradado - 359 passaram, 1 pulado; test_regra76_corpus_butanta + test_s74_corpus_butanta - 61 passaram (snapshots historicos byte a byte com 78 e 79 desligadas); test_cross_band_joint_propagation_cr_g12 - 20 passaram.",
    "Suite completa sem tests/regression (motor final): 1727 passaram, 1 pulado, 2 falharam - tests/test_perf_trace_stall_sampler.py (historica, identica na main) e tests/test_cross_band_joint_propagation_cr_g12.py::test_reproducer_minimo_falha_no_codigo_anterior (o reproducer PRE-FIX da CR-G12 deixou de reproduzir porque a secao 79 muda as pecas de no' do subplano; passou a medir o motor em que o defeito existia - sem CR-G12 e sem 79 - e o arquivo passa 20/20). Os testes acrescentados depois do inicio da suite (6 do ciclo 3) passam no arquivo.",
    "tests/regression (motor final, 20 min): 145 passaram, 3 falharam - TP1 JUNCTION_MISSING_BINDING 8->9 (historica), TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 (ciclo 1) e TGD V1 categoria compensators 52->54 (NOVA, deste ciclo: 100% da 76 D1, ver physical_deltas). Baseline nao regravado.",
    "Revisao adversarial (workflow, 3 revisores + verificador por achado): 18 achados, 14 confirmados e corrigidos (rastreio e testes vacuos; nenhum mudava peca), 4 refutados. Bancada e Revit re-medidos depois das correcoes: pecas identicas (assinatura dos 50 nos igual)."
  ],
  "known_failures": [
    "tests/test_perf_trace_stall_sampler.py (historica).",
    "tests/regression TP1 8->9 (historica); TGD V2 86->92 (ciclo 1, reclassificacao); TGD V1 compensators 52->54 e TGD V2 compensators 63->66 (deste ciclo, 76 D1; troca por +27/+32 fiadas-no' amarradas) - decisao humana sobre baseline/escopo.",
    "BUTANTA: 3 fiadas de cantos L (55/56) sem amarracao continuam - agora visiveis sem reforco (structurally_resolved = False); pendencia da secao 76 (casos 47/48).",
    "O clique humano no botao nao foi exercitado (acao humana); o caminho foi provado pela API nas copias CICLO3/CICLO3b, deixadas abertas sem salvar. Nenhum dos tres RVTs de referencia foi tocado."
  ],
  "physical_deltas": [
    "CAUSA (rastreio por no'/fiada, BUTANTA 34 eixos, NONE): o passo do no' T roda ANTES do preenchimento livre e mede o espaco sozinho (abertura + reserva de no' vizinho; nunca peca de preenchimento) - a hipotese de o preenchimento ocupar o envelope do encontro foi descartada. Os 4 nos reprovavam no proprio passo do no' e caiam no C09 da escada (BOND_CANDIDATE_NOT_GENERATED): no 51 - B54 precisa de 27 cm de cada lado e ha' 27,000/26,997 (reprovado pelo epsilon de ponto flutuante; a 74 da' 0,05 cm); no 28 - B34 degradado medido do PONTO precisa de 34 num lado e ha' 27,01/11,99 (a D1 mede do CONTATO: 27 + 7 cabem); no 20 - 7,00/26,99 (D1 + tolerancia 74); no 26 - janela a 7,00/7,01 dos DOIS lados nas fiadas 4-10: o T nao existe ali (77). As quatro regras eram so' CHANNEL. Paridade nao e' causa (os 4 nos perdiam a amarracao nas duas familias).",
    "BANCADA (34 eixos, NONE, 280 cm, 14 fiadas; ANTES = secao 79 desligada = main 15bacec) ANTES -> DEPOIS: T 37 total, amarrados 33 -> 37, sem amarracao 4 -> 0; fiadas de T sem amarracao (0-11) 30 -> 0 (auditoria total 33 -> 3: as 3 restantes sao dos cantos L 55/56 = casos 47/48 da secao 76, iguais); no 51 xxxxxxxxxxxB -> BBBBBBBBBBBB; no 20 BBBBxxxxxxxB -> BBBBBBBBBBBB; no 26 BBBBxxxxxxxB -> BBBB-------B (7 fiadas NO_FUNCTIONAL_JUNCTION); no 28 BBBBxxxxxBBB -> BBBBBBBBBBBB; gate 76 (compensador designado amarracao) 33 -> 0; juntas verticais continuas >= 3 fiadas 4 -> 0 (a de 11 fiadas no pilar do no 51 some); compensadores 864 -> 828 (11,7% -> 11,2%); jambas sem peca 64 -> 60; vazio 30 -> 30 cm; NON_MODULAR_UNRESOLVED 0 -> 0; invasoes 0; colisoes 0; coincidencia exata com o MCP 51,7% -> 53,9% (<= 5 cm 55,4% -> 57,1%). Nos com peca de no' alterada: 6 de 50 (os 4 alvos + 22 e 49, T com falta submilimetrica da 74 que ja' degradavam para B34+B19 e passam a B54 alternado, como HUMANO e MCP); nenhum L/X muda.",
    "REVIT (copias CICLO3 e CICLO3b de 'butanta testes', import preparado na copia, 46 -> 34 eixos pela 49.1, NONE): 7357 planejadas = 7357 criadas, 0 falhas, 0 puladas, 0 invasoes, 0 amarracoes nao resolvidas; bond_trace 690 BOND_RESOLVED / 7 NO_FUNCTIONAL_JUNCTION / 3 NOT_GENERATED (cantos L 47/48); `structurally_resolved = False` porque o gate 76.1 agora vai no resultado sem reforco e expoe as 3 fiadas dos cantos L que antes ficavam silenciosas (CICLO2: True sem o gate). Regua sobre o modelo criado (CICLO2 -> CICLO3): vazio 30 -> 30 cm, jambas sem peca 65 -> 61, compensadores 835 (11,3%) -> 800 (10,9%), coincidencia exata com o MCP real 53,2% -> 55,4% (<= 5 cm 56,1% -> 57,8%), bonecas iguais, B34 invasoras planejadas 0 -> 0.",
    "TGD V2 (benchmark legado) com a secao 79: criticos identicos (COVERAGE_ROW_MOSTLY_EMPTY 92, MISSING_ROW 136, GAP_IN_ROW 1153, PARTIAL_WALL 24, PRISM_CONTINUOUS_JOINT 53); categoria compensators 63 -> 66 paredes (COMPENSATOR_VERTICAL_STRIP 104 -> 110 em W060/W061/W098/W099, faixas em fiadas ALTERNADAS em t=59,5 cm; AVOIDABLE 58 -> 57, CONSECUTIVE 434 -> 428, EXCESS_IN_RUN 503 -> 499; PRISM_STAGGER_BELOW_TARGET 749 -> 767). Atribuido por sub-regra: 100% da 76 D1 (sem a D1 o TGD V2 fica identico); a D1 amarra 32 fiadas-no' a mais (5 T que tinham C09 no lugar da amarracao; MISSING_REQUIRED_JUNCTION_BOND 935 -> 903). TGD V1: compensators 52 -> 54 (W057/W105/W106 entram, W031 sai), PRISM_CONTINUOUS_JOINT 232 -> 231, D1 amarra 27 fiadas-no' a mais (4 T; 1708 -> 1681). TP1: nenhum achado muda. Baseline NAO regravado.",
    "D4: B34 planejadas invadindo porta 0 -> 0 (ja' resolvido pelo corpus do ciclo 2; a regra 48 fica intacta). Canaleta como amarracao: 0."
  ],
  "decisions_taken": [
    "A mesma regra estrutural da secao 78: o que responde 'a peca de amarracao existe e cabe fisicamente?' e' geometria do encontro, nao reforco de abertura - as regras 74, 76 D1, 76.1 e 77 ja' provadas no CHANNEL passam a valer sem reforco por um interruptor proprio. Nenhuma regra nova de geometria, nenhuma tolerancia nova, nenhum ID.",
    "No' sem amarracao nunca fica silencioso: os gates 76/76.1 vao no resultado dos dois caminhos e o rastreio diz, por fiada, se a amarracao nao foi gerada (com o teste fisico que reprovou) ou foi gerada e rejeitada (com a regra).",
    "Trocar compensador designado por amarracao real vence a categoria de compensadores do benchmark (ordem aprovada do projeto: portoes duros antes de qualidade); a troca fica registrada para decisao humana."
  ],
  "decisions_pending": [
    "TGD V1/V2 categoria de compensadores (+2/+3 paredes, so' da 76 D1): aceitar e regravar baseline num commit proprio, ou pedir escopo diferente para a D1 no legado. Nao regravado aqui.",
    "Cantos L 55/56 (casos 47/48 da secao 76): 3 fiadas sem amarracao, agora visiveis no caminho sem reforco (structurally_resolved = False no BUTANTA). Pendentes de decisao desde 2026-09-18 (JUNCTION_BOND_B19_FALLBACK / L_CORNER_OTHER_ARM_OWNS).",
    "Paridade dos T (D11): o no 51 ficou com a paridade do MCP (B54 nas fiadas pares); o HUMANO usa a oposta. Amarracao resolvida nos dois; paridade nao foi tocada."
  ],
  "next_steps": [
    "Ciclo seguinte somente com nova autorizacao (D6 verga/contraverga, D9-D13, D14, 3B, D16)."
  ],
  "references": [
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "tests/test_regras_fisicas_de_encontro.py"},
    {"path": "tests/test_channel_reinforcement.py"},
    {"path": "tests/test_compensator_never_bonds.py"},
    {"path": "tests/test_missing_required_junction_bond.py"},
    {"path": "tests/test_regra761_revisao_do_gate.py"},
    {"path": "tests/test_regra76_d1_t_degradado.py"},
    {"path": "tests/test_regra76_corpus_butanta.py"},
    {"path": "tests/test_s74_corpus_butanta.py"},
    {"path": "tools/audit/s74_corpus.py"},
    {"path": "docs/checkpoints/2026-09-24-ciclo2-corpus-d5.md"}
  ]
}
```

## 1. Nós D2/D3 fiada a fiada (0–11)

P = peças da principal na região ±27 cm do nó (posições relativas ao nó, cm); C = última peça da parede que chega e quanto passa do eixo do nó. ANTES = cópia CICLO2 (main 15bacec); DEPOIS = cópia CICLO3.

**Nó 51 (8284515 × 8284580, pilar de 54 cm entre duas portas).** HUMANO e MCP alternam `B54[-27,27]` com `B19|B19 + B34` da chegada (paridades opostas entre si). ANTES: `B19|B19` + C09 da chegada nas fiadas 0–10 (sem amarração, junta contínua de 11 fiadas no eixo do nó). DEPOIS: `B54` nas pares + `B19|B19` com `B34>7` da chegada nas ímpares — idêntico ao MCP.

**Nó 20 (8284502 × 8284558, janela a 7 cm de um lado).** Fiadas 0–3 e 11 iguais nos quatro. Fiadas 4–10: HUMANO = MCP = `B34[-27,7]` (pares) / `B19[-27,-8]` + `B34>7` (ímpares). ANTES: `B19` + C09 em todas. DEPOIS: idêntico a HUMANO e MCP.

**Nó 26 (8284502 × 8284562, janela a 7 cm dos dois lados).** Fiadas 4–10: a principal não existe (HUMANO e MCP: nada em ±27 cm; a chegada vai até a face oposta com B19/B34 ou B19/B39). ANTES: C09 na ponta da chegada, contado como nó sem amarração. DEPOIS: ponta livre composta (B39/B19 alternados até a face) e as 7 fiadas classificadas `NO_FUNCTIONAL_JUNCTION`.

**Nó 28 (8284554 × 8284563, porta a 12 cm e janela a 27 cm).** Fiadas 4–8: MCP = `B34[-7,27]` (pares), HUMANO = `B34[-7,27]` (ímpares). ANTES: `B19[8,27]` + C09. DEPOIS: `B34[-7,27]` nas pares — idêntico ao MCP.

## 2. As duas falhas, separadas pelo rastreio

- `BOND_CANDIDATE_NOT_GENERATED` — os 30 casos do BUTANTÃ ANTES: o passo do nó reprovou T (B54/B34), L degradado (B34 do ponto) e — com a D1 desligada — o L do contato; a escada fechou com C09.
- `BOND_CANDIDATE_GENERATED_BUT_REJECTED` — peça gerada e ausente do resultado final (`DROPPED_AFTER_NODE_STEP`), presente mas reprovada pela auditoria 76.1 (`AUDIT_*`), ou pulada pela regra 48 (`REGRA_48_*`). Não ocorre no BUTANTÃ depois da correção.

## 3. Revisão adversarial

Três revisores independentes (motor, rastreio, testes) + um verificador por achado tentando refutar: 18 achados, 14 confirmados (todos no rastreio e em testes vácuos; nenhum mudava peça), 4 refutados. Os 14 foram corrigidos e 7 deles ganharam teste de regressão próprio (rastreio da passada vencedora, casamento por tolerância, família da peça = fiada física, banda de uma só fiada sem descarte inventado, regra 48 no rastreio pelo `_execute_solve`, papel por fiada da auditoria, lado culpado no detalhe); os testes vácuos (paridade 72, canaleta, guarda de não-vacuidade do item 13) foram reescritos para falhar de verdade.
