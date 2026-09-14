# Estratégia CHANNEL (canaletas) — BUTANTÃ humano × cru, Revit real + MCP (2026-09-14)

```json
{
  "date": "2026-09-14",
  "scope": "current",
  "branch": "claude/butanta-channel-reference-implementation",
  "head": "26cf5d2e1419cdaa988cefa6a78c919afad902da",
  "base": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "main_observada": "0e41c8efe2b141b836bb4873f5219e4da0b1d03c",
  "pr": "not-created",
  "veredito": "__VEREDITO__",
  "objective": "Implementar e validar a estratégia de reforço de aberturas CHANNEL (canaletas) no motor comum, seguindo de forma geral o sistema físico do projeto humano BUTANTÃ R08_LT, sem verga/contraverga; validar offline e no Revit real (bancada 'butanta testes', HUMANO somente leitura), com comparação humano × solver, escada de escala, idempotência e regressão.",
  "changes": [
    "nuvem/core/engine/opening_reinforcement.py (novo): plan_channel_reinforcement (demanda por abertura acima/abaixo, corridas compostas pelas peças da fiada, fusão de compensadores em LENGTH_CUT, apoio preferencial 19 cm, travessia de T com apoio <= 0, conversão de amarração ao longo sobre o vão ou com apoio < 9 cm incluindo divisão do B54, passagem livre até o topo, achados) e validate_channel_reinforcement (validador independente). IronPython 2.7.",
    "nuvem/core/wall_modeling.py: solve_building_blocks_all_courses(opening_reinforcement_strategy=None|'CHANNEL', opening_reinforcement_policy) com _apply_opening_reinforcement (pós-passe + validação + re-auditoria); CHANNEL_FAMILY_CATALOG_DEFINITIONS, load_channel_family_catalog (MISSING_FAMILY_MAPPING), channel_logical_catalog; create_building_blocks grava Comprimento_bloco de instância (apaga e reporta se falhar); handler com opening_reinforcement_strategy/channel_catalog/_creation_catalog e estratégia na assinatura beta; _channel_covers_node e exceção HALF_BLOCK_NEAR_TIE para o B19 da travessia (prova dupla).",
    "nuvem/benchmark/extract/from_solver.py: papel T_binding para T_INTERSECTION_INCOMING_CHANNEL_ABUTMENT.",
    "tests/test_channel_reinforcement.py (novo, 30 testes).",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: seção 51 (51.1–51.12) e ponteiro em 41.4.",
    "docs: docs/architecture/channel-strategy-implementation.md; este checkpoint; PROJECT_STATUS, START_HERE, PROJECT_STATUS_LOG; evidências docs/checkpoints/evidence/2026-09-14-channel-* e _scripts/2026-09-14-channel-*."
  ],
  "tests": [
    "tests/test_channel_reinforcement.py: 30 passed (HEAD 26cf5d2, Windows, CPython 3.14, pytest 9.1.1). RED na main 0e41c8e: erro de coleta (módulo inexistente) — evidence/2026-09-14-channel-red-on-main.txt.",
    "Focados existentes após a integração: test_controlled_beta_preflight, test_block_lot_persistence, test_mirror_in_place, test_beta_atomic_creation, test_room_probe_inside_opening, test_tie_parity_abutting_ties: 95 passed.",
    "Bancada offline legado × CHANNEL (evidence/2026-09-14-channel-bench-{1,3,5,10,20,34}.json): ver seção Escala.",
    "Determinismo: 34 paredes em 3 processos (PYTHONHASHSEED 0/1/2): legado 94541746…, CHANNEL ec8d5258… idênticos (evidence/2026-09-14-channel-determinism.txt); teste de 3 processos na suíte.",
    "Paridade Revit (IronPython) × offline (CPython) com as MESMAS entradas e o catálogo real lido no Revit: 34 paredes, 7.229 peças, assinatura idêntica e validação idêntica (_scripts/2026-09-14-channel-revit-parity.py sobre evidence/2026-09-14-channel-revit/r_ladder_34_run2.json).",
    "Revit real: casos A/B/D/F e escada 1/3/5/10/20/34 com criação, releitura por instância e idempotência (evidence/2026-09-14-channel-revit/).",
    "__REGRESSAO__"
  ],
  "known_failures": [
    "__FALHAS__",
    "7719511 (parede de 115 cm): canaleta sob o peitoril ausente — o preenchimento legado deixa o trecho [14,81] vazio (não modular) e o canto L cobre a jamba; ACTUAL_ERROR registrado, causa anterior ao CHANNEL.",
    "6627438: apoio de 4 cm do lado do T (a paridade do motor põe a transversal nessa fiada; o humano usou a paridade oposta) — SOLVER_WORSE.",
    "Recorte isolado de 3 paredes (8079777 + 8079833 + 8079837): as duas paredes que chegam ficam reprovadas por CONTINUOUS_VERTICAL_JOINT na face do T (consequência da travessia, 51.6); no plano de 34 paredes não reprovam."
  ],
  "physical_deltas": [
    "Legado (strategy None): assinatura física idêntica à main em todas as escalas (34 paredes: 94541746…).",
    "CHANNEL 34 paredes/44 vãos (offline, aberturas do acervo): 7.250 → 7.225 peças (−25: 20 peças acima das duas passagens livres, fusões de compensador); 313–319 canaletas; top 40/40, bottom 22/23; 4 travessias de T; 2 passagens livres; PRISM_CONTINUOUS_JOINT 0 = 0; paredes reprovadas 3 = 3; delta benchmark COVERAGE_GAP_IN_ROW +6, PRISM_STAGGER_BELOW_TARGET +1; demais códigos iguais.",
    "Revit 34 paredes (aberturas detectadas pelo plugin, 2º PAV da bancada): 7.229 peças criadas, 319 canaletas (6 cortadas por parâmetro de instância), 0 falhas, releitura 7.229/0 divergências, preflight ok, 0 invasão/0 colisão.",
    "Nenhum baseline/reference/threshold/validador de junta alterado; nenhum skip/xfail. HUMANO não modificado (IsModified=false em todas as execuções); TARGET não salvo."
  ],
  "decisions_taken": [
    "Modular o TARGET no 2º PAVIMENTO (nível das 44 aberturas; CAD TIP no mesmo nível) e comparar com o 1º PAV humano: as 44 aberturas batem 44/44 em posição/largura/altura/peitoril com o 1º PAV humano (2º PAV humano: 36/44).",
    "CHANNEL como pós-passe de troca de tipo sobre as fiadas resolvidas (sem segundo solver, sem junta nova); estratégia opt-in, legado intacto.",
    "Catálogo de canaletas separado do catálogo de preenchimento; canaleta J não usada.",
    "Travessia de T (51.6), conversão de amarração ao longo (51.7) e passagem livre (51.9) implementadas pela evidência humana medida, com parâmetros de política e achados — registradas como EXCEÇÃO/PADRÃO OBSERVADO, não como regra aprovada.",
    "Cinta de topo e topo/peitoril fora da grade não implementados (conflito 10.7 e 10.2 × K.2).",
    "Paredes da bancada não criadas no TARGET: o dono do lote é a chave física do eixo (prefixo CHANNELBENCH-), exercitando o mesmo mecanismo de carimbo/descoberta da seção 50."
  ],
  "decisions_pending": [
    "Aprovar a estratégia CHANNEL e a escolha A/B (DECISION-OPENING-REINFORCEMENT, PENDING) e a UI de seleção (não implementada).",
    "Aceitar a face-junta na parede que chega em 3 fiadas quando a canaleta atravessa o T (51.6).",
    "Confirmar apoio preferencial 19 cm, limiar 9 cm de conversão de amarração ao longo e a passagem livre até o topo.",
    "Regra para topo/peitoril fora da grade (compensador deitado × fiadas de 9 cm cortadas).",
    "Cinta de topo (conflito 10.7)."
  ],
  "next_steps": [
    "Revisão humana do PR draft; sem merge sem autorização específica.",
    "Não iniciar LINTEL_COUNTERLINTEL nesta linha."
  ],
  "references": [
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "tests/test_channel_reinforcement.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "docs/architecture/channel-strategy-implementation.md"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-runs.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-solver.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-human-vs-revit-34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-bench-34.json"},
    {"path": "docs/checkpoints/evidence/2026-09-14-channel-revit/README.md"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## 1. Git e documentos

- `origin/main` inicial = final observada: `0e41c8e` (merge do #39). Branch nova
  `claude/butanta-channel-reference-implementation` a partir dela.
- A pasta do pyRevit (`…/MeuBotao.pushbutton` na extensão) não é repositório git;
  conteúdo idêntico a `origin/main` (ignorando CRLF). O trabalho foi feito num
  clone limpo e o motor foi carregado no Revit direto do clone.
- **HUMANO** `BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO) (1).rvt`: 65.747
  Modelos genéricos, 142 aberturas, 0 Walls — idêntico à extração versionada.
  Somente leitura: nenhum script abriu Transaction nele; `IsModified=false` checado
  antes e depois de cada execução (e `assert` antes de qualquer escrita).
- **TARGET** `butanta testes.rvt`: 0 blocos, 0 Walls, 44 aberturas no 2º PAVIMENTO,
  todas as famílias de canaleta carregadas (inventário `q02`).

## 2. Catálogo CHANNEL

| Lógico | Família/tipo | Humano 1º PAV / total | TARGET |
|---|---|---|---|
| CHANNEL_U_39 | CANALETA INTEIRA - 14x19x39 | 587 / 5.865 | carregada |
| CHANNEL_U_34 | CANALETA 34 - 14x19x34 | 270 / 2.615 | carregada |
| CHANNEL_U_19 | MEIA CANALETA - 14x19x19 | 19 / 194 | carregada |
| CHANNEL_U_CUT | BLOCO CANALETA CORTADO - 14x19xVAR (`Comprimento_bloco` de instância) | 6 / 57 | carregada |
| (não usada) | CANALETA J - 14x9-19x19 / J CORTADA | 13+1 / 190+10 | carregada |

Origem no centro, eixo X no comprimento, 19×14 cm (medido no humano, `q03`).
`MISSING_FAMILY_MAPPING`: 0.

## 3. Casos mínimos no Revit real

| Caso | Recorte | Peças | Canaletas | Resultado |
|---|---|---|---|---|
| A porta | 8079827 | 240 | 4 (corrida [485,644], apoio 19/49) | criado, releitura 0, rerun 240→240 |
| B/C janela sup+inf | 8079821 | 358 | 6 (fiadas 11 e 7) | criado, releitura 0 |
| D T + travessia | 8079777, 8079833, 8079837 | 1.240 | 124 (4 cortadas 14 cm) | criado, releitura 0; 4 travessias |
| E corte | escada 10/34 | — | KV 4/14 cm | parâmetro e sólido conferidos (KV 4: sólido 4,000 cm) |
| F passagem livre | 8079790, 8079854, 8079855 | 737 | 22 | 1 passagem (a outra depende do T de 8079821, fora do recorte) |

## 4. Escala (Revit real, criação + releitura por instância)

| Paredes | Aberturas | Peças | Canaletas | top | bottom | Invasão/colisão | Falhas | Releitura | Criação |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 7 | 520 | 72 | 7/7 | 7/7 | 0/0 | 0 | 0 | 12 s |
| 3 | 11 | 1.410 | 90 | 11/11 | 8/8 | 0/0 | 0 | 0 | 36 s |
| 5 | 16 | 1.891 | 122 | 15/15 | 9/9 | 0/0 | 0 | 0 | 50 s |
| 10 | 17 | 2.748 | 128 | 16/16 | 9/9 | 0/0 | 0 | 0 | 80 s |
| 20 | 22 | 3.916 | 155 | 20/20 | 10/11 | 0/0 | 0 | 0 | 143 s |
| 34 | 44 | 7.229 | 319 | 40/40 | 22/23 | 0/0 | 0 | 0 | 318 s |
| 34 (sessão nova) | 44 | 7.229 → 7.229 | 319 | idem | idem | 0/0 | 0 | 0 | 324 s |

Tempos (34): solve 19,7 s no Revit (plano CHANNEL 0,01–0,07 s; re-auditoria ≈1 s);
criação 36–39 ms/instância (`NewFamilyInstance` 280 s, commit 5,7 s). Bancada
offline equivalente: legado 2,3 s × CHANNEL 3,4 s.

## 5. Humano × solver

Offline (aberturas do acervo, 67 papéis): 15 EXACT_MATCH, 44
PHYSICALLY_EQUIVALENT, 4 SOLVER_BETTER, 1 SOLVER_WORSE, 2 NOT_COMPARABLE,
1 ACTUAL_ERROR. Revit (aberturas do plugin, 44/44 casadas): 4 EXACT, 55
EQUIVALENT, 4 BETTER, 1 WORSE, 2 NOT_COMPARABLE, 1 ACTUAL_ERROR. Detalhe em
`2026-09-14-channel-human-vs-solver.json` e `…-human-vs-revit-34.json`.
Cinta de topo humana (fiada 241) não entra na conta (51.10).

## 6. Gates

| Gate | Resultado |
|---|---|
| OPENING_BLOCK_INSIDE_DOOR/WINDOW (preflight) | 0 / 0 |
| MISSING_REQUIRED_CHANNEL | 1 (7719511, causa no preenchimento legado) |
| EXTRA_CHANNEL / CHANNEL_WRONG_COURSE / CHANNEL_INVADES_OPENING / CHANNEL_COLLISION | 0 / 0 / 0 / 0 |
| PRISM_CONTINUOUS_JOINT (fill|tie, nó|fill) | 0 (legado 0) |
| Paredes reprovadas na auditoria | 3 = legado (as de 99 cm, históricas) |
| non_modular | 78 = legado |
| Determinismo / paridade Revit | 3 processos idênticos / assinatura idêntica |
| Idempotência | 240→240; 7.229→7.229 |

## 7. Regressão consolidada

__REGRESSAO_TEXTO__

## 8. Veredito

__VEREDITO_TEXTO__
