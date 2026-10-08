# §86 — aproximação do projeto humano BUTANTÃ R08_LT: regras R2–R10 integradas e pavimento recriado no Revit

Estado CANDIDATO local da branch `claude/revit-butanta-modulation-8611b5` — sem PR, sem push, sem merge. Não é
estado oficial nem aprovação normativa; as decisões pendentes abaixo são do usuário.

```json
{
  "date": "2026-10-05",
  "scope": "historical",
  "branch": "claude/revit-butanta-modulation-8611b5",
  "head": "cfb8a60cfd33a969dec204f37169d2b639571e90",
  "base": "894e3f5278ffa9cb030efe01a70c7305b252af15",
  "pr": "not-created",
  "objective": "Pedido do usuario (2026-10-01): chegar o mais perto possivel do projeto humano BUTANTA R08_LT (1o pavimento) ajustando as regras e o calculo de modulacao, sem copiar pecas; recriar o pavimento inteiro no butanta testes, com vistas e relatorio. Pedido de 2026-10-02: terminar e integrar a cinta, as jambas e os tocos medindo cada uma contra o humano.",
  "changes": [
    "00cb84d merge R3 (86.3): faixa de B34 equilibrada entre as duas ancoras nas corridas no-a-no sem abertura (wall_stepper).",
    "1c63adf merge R2/R4 (86.2): relacao de fase por trecho com busca exata por componente (inclui cantos L) + espelho pela convencao de fachada (wall_stepper, wall_modeling).",
    "3c0aaf3 merge R7A/R8 (86.7/86.8): cinta de topo variante A (bloco de amarracao no quadrado do no'), passagem livre sem CHANNEL, apoio preferencial de 40 cm em verga de vao >= 140 cm (opening_reinforcement, wall_modeling); ajustes de integracao nos testes.",
    "7988968 merge R9 (86.9): tocos de eixo <= 40 cm alem da face da parede que cruza aparados antes do grafo (wall_pairing, wall_modeling, s74_corpus, ui_state).",
    "98b159f merge R6/R10 (86.6/86.10): catalogo da sobra na jamba, guarda C09|B34 -> C04|B39, forma A (chave), orientacao do C09 pelo humano (b34_run_arrangement, wall_modeling).",
    "cfb8a60 86.6: trava de prisma por parede (JAMB_B34_GUARD_PRISM_GATE) - a guarda B34+compensador tirava do orcamento a grade de B34 do pilarete da W4 desenhado pelo usuario (85.9).",
    "DOCS: REGRAS 86.0 (tabela de evolucao), 86.11 (estado), subsecoes 86.2-86.10; este checkpoint; evidencias em docs/checkpoints/evidence/2026-10-05-s86-revit/; PROJECT_STATUS.",
    "REVIT (butanta testes, 2a instancia porta 48885; referencia e COBERTURA BALCONY intocados): lote 20260929-155403 substituido pelo lote 20261005-094454 (6 428 pecas); 35 vistas S86 (34 elevacoes + 3D com caixa de corte); arquivo NAO salvo; copia previa 'butanta testes - BACKUP antes S86 rodada4 2026-10-05.rvt'."
  ],
  "tests": [
    "HEAD cfb8a60: py -3 -m pytest tests/test_script.py tests/test_jamb_remnant_catalog.py tests/test_jamb_compensator_alignment.py tests/test_b34_run_arrangement.py tests/test_b34_balanced_strip.py tests/test_top_bond_beam.py tests/test_stub_trim_86_9.py -q -> 424 passaram (6 min 43 s).",
    "98b159f (antes da trava): test_script + jamb_remnant_catalog + jamb_compensator_alignment + b34_run_arrangement + regras_gerais_composicao + reparo_68_guarda_junta + b34_balanced_strip + top_bond_beam + fase_relacao_86 + stub_trim_86_9 -> 513 passaram, 3 falhas ja' existentes em 88a67c8.",
    "3c0aaf3: test_script + top_bond_beam + d16 + regras_fisicas + bond_strip + fase_relacao_86 + b34_balanced_strip + opening_structural + channel_reinforcement -> 512 passaram; 7988968: 411 passaram nos modulos da 86.9.",
    "Suite completa NAO executada (memoria curta da maquina; modulos pesados de corpus/benchmark e regressao TGD/TP1 nao rodados).",
    "Calculo completo offline (export_r4.py + r4_score.py) a cada regra; leitura de volta do Revit: 6 428 pecas, 0 sem parede, celulas identicas ao calculo (0,0 cm)."
  ],
  "known_failures": [
    "tests/test_regras_gerais_composicao.py::test_dois_compensadores_evitaveis_viram_meio_bloco (ja' falhava em 88a67c8: assert 28 > 0 and 7 == 0).",
    "tests/test_reparo_68_guarda_junta.py::test_red_secao_68_sem_guarda_cria_junta_a_prumo[474.0] e [489.0] (ja' falhavam em 88a67c8).",
    "Revit: 3 verga/contraverga nao resolvidas (topo fora da grade, 51.8) - revisao humana."
  ],
  "physical_deltas": [
    "F1 de pecas contra o humano (6 634 pecas): Revit anterior 20,8 % -> aberturas originais 13 fiadas 26,4 % -> R3 35,3 % -> R2/R4 50,6 % -> R7A/R8 54,4 % -> R9 54,5 % -> R6/R10 com trava 56,2 % (precisao 57,1 %, revocacao 55,4 %; 3 672 iguais).",
    "Qualidade f0-11 (regua independente r2_eval): furos quebrados 467 (Revit anterior) / 630 (base) -> 417 (humano 407); septos sem apoio 265 / 239 -> 107 (humano 60); vazado menor sobre principal 12 (humano 33); pastilhas 360 (humano 486); juntas coincidentes nao isentas 0 (humano 13).",
    "Cinta (f12): 549 pecas, 0 canaleta em no' (variante A); humano 559.",
    "Pecas: 6 428 (B39 3 156, B34 1 554, B19 347, B54 194, C09 211, C04 149, U39 601, U34 203, U_CUT 11, U19 2); calculo offline 854 s."
  ],
  "decisions_taken": [
    "Usuario (2026-10-01): aproximar do humano ajustando regras, sem copiar; pode alterar qualquer coisa no butanta testes; canaleta nunca serve de amarracao (por isso cinta variante A).",
    "Integracao: prisma primeiro (pedido do usuario na rodada 2 / 85.10) - a guarda C09|B34 so' fica numa parede se nao aumentar as celulas quebradas (trava cfb8a60)."
  ],
  "decisions_pending": [
    "R4 x 30.5 (alternancia de papel obrigatoria): humano na mesma fiada em 9/9 paredes entre dois L.",
    "Cinta variante B (canaleta sobre 48/50 nos, como o humano) x variante A atual.",
    "Forma A da jamba (vazado menor do B34 sobre a faixa macica) - ligada, sem efeito neste pavimento; conflita com 84 item 3 / 85.8.",
    "Shaft W27/W33: solucao humana x excecao B54+C09 da 85.8.",
    "Calco de C09 deitado (8 paredes do nucleo a 270 cm) e fiada partida H9 (51.8).",
    "R10: confirmar o lado fechado do C09 pela geometria solida da familia."
  ],
  "next_steps": [
    "Aguardar a revisao do usuario no Revit (vistas S86) e as decisoes pendentes; merge so' com autorizacao especifica."
  ],
  "references": [
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "nuvem/core/engine/b34_run_arrangement.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/core/engine/wall_pairing.py"},
    {"path": "docs/checkpoints/2026-10-01-s86-aproximacao-humano-etapa1.md"},
    {"path": "docs/checkpoints/evidence/2026-10-05-s86-revit/readback_r4_final.json"},
    {"path": "docs/checkpoints/evidence/2026-10-05-s86-revit/placar_r6gate_13.txt"},
    {"path": "docs/checkpoints/evidence/2026-10-05-s86-revit/s5_create_r4.out"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Onde está cada coisa

- Regras: `nuvem/REGRAS_MODULACAO_BLOCOS.md` §86 (86.0–86.11).
- Evidência versionada: `docs/checkpoints/evidence/2026-10-05-s86-revit/` — leitura de volta do Revit
  (`readback_r4_final.json`), placares de cada etapa (`placar_*.txt`, inclusive os A/B das chaves da R6), saída da
  criação, scripts do Revit (`r4_*.py`), gerador do relatório (`gen_report.py` + `meta_final.json`), vista 3D e
  elevação da W4.
- Solução injetada no Revit: `sol_final.json` (SHA-256 `23e00dd75226a7b2d9604eff358d853c058c3977c880256dc3f536a8fcaac7a3`),
  só no rascunho local `.claude/checkpoints/2026-10-01-s86-humano/` com as 35 imagens das vistas e o relatório HTML.
- Revit: vistas `S86 W00 … S86 W33` (elevação de cada parede) e `S86 Pavimento 3D` no `butanta testes`.
