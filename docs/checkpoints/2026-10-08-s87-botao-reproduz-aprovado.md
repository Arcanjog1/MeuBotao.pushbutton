# §87 — o botão reproduz a modulação aprovada do BUTANTÃ a partir do arquivo cru

Estado CANDIDATO da branch `claude/script-modulation-blocks-469ec2` (= `claude/revit-butanta-modulation-8611b5`
+ §87). PR [#50](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/50) — MERGED na main em 2026-10-09 (fast-forward até c9e30e0), autorizado pelo usuário. **Resultado no Revit: 6 526/6 526 peças iguais ao aprovado.** Não é estado oficial nem aprovação normativa.

```json
{
  "date": "2026-10-08",
  "scope": "current",
  "branch": "claude/script-modulation-blocks-469ec2",
  "head": "7cafca2e2326b27c66e980524d67ae1de0980013",
  "base": "894e3f5278ffa9cb030efe01a70c7305b252af15",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/50",
  "objective": "Fazer o fluxo normal do botao (CAD -> Walls) gerar, a partir do arquivo cru 'butanta testes cru.rvt', a mesma modulacao aprovada pelo usuario em 2026-10-08 (lote 20261008-143828, 6 526 pecas, motor 06ecb87), sem ajustes posteriores via MCP e sem copiar coordenadas da planta.",
  "changes": [
    "87.1 (configuracao, documentado): o layer de paredes do CAD arquitetonico e' 'Estrutura _1_' (46 pares = 46 paredes historicas); 'Paredes' e' acabamento e fragmenta (52 eixos).",
    "87.2 wall_modeling.py: collect_reference_layers_from_document / reference_layer_label / cad_import_display_name; ask_setup(..., reference_layers) e _SetupForm(..., reference_layers) listam layers de TODOS os imports ('<import> | <layer>'); em main() a regra 49 roda depois de dedupe+extend com trim=False (so' classificacao) e o setup (corpus 49.1, tocos) passa ao handler da Tela 2.",
    "87.3 wall_pairing.py: find_wall_end_stubs(..., ignore_locks) / trim_wall_end_stubs(..., ignore_locks=None): no modo sobra de CAD (<= 10 cm) a testa nao protege a ponta; main() NAO apara (Walls fieis ao CAD): o corte acontece no primeiro refresh do handler (86.9); aparar antes de criar as Walls fazia o refresh devolver +5 cm as aberturas da W8 (medido).",
    "87.4 wall_pairing.py: OPENING_SILL_BELOW_BASE_SNAP_CM = 2.0 e snap_openings_to_wall_base(): peitoril ate' 2 cm abaixo da base sobe para a base com a altura do vao preservada; chamada nos dois fluxos.",
    "main(): len([...]) no lugar de sum(gerador) no contador de eixos fora da planta (quebrava no IronPython do caminho MCP).",
    "tests/revit_stubs.py: ImportInstance; tests/test_cad_flow_butanta_s87.py (17 testes) + evidencia docs/checkpoints/evidence/2026-10-08-s87-cad-flow/ (linhas CAD, aberturas, 34 eixos aprovados).",
    "DOCS: REGRAS §87 (+ notas nas §49 e §86.9), este checkpoint, PROJECT_STATUS, START_HERE."
  ],
  "tests": [
    "HEAD 2a18c54: py -3 -m pytest tests/test_cad_flow_butanta_s87.py tests/test_stub_trim_86_9.py tests/test_reference_layer_filter.py tests/test_corpus_selection_paredes_existentes.py tests/test_channel_ui_and_family_gate.py -q -> 65 passaram (17 novos + 48).",
    "HEAD 7cafca2: py -3 -m pytest tests/test_script.py tests/test_sem_meia_canaleta_86_14.py tests/test_b54_cinta_86_16.py tests/test_channel_grid_follow_86_12.py tests/test_top_bond_beam.py tests/test_junta_no_toco_86_15.py tests/test_compensator_at_jamb_face_86_13.py tests/test_stub_trim_86_9.py tests/test_loader_provenance.py tests/test_regras_gerais_composicao.py -q -> 456 passaram, 1 falhou (test_dois_compensadores_evitaveis_viram_meio_bloco, ja' falhava na base), 13 min 12 s.",
    "HEAD 7cafca2: tests/test_cad_flow_butanta_s87.py + test_channel_ui_and_family_gate.py + test_corpus_selection_paredes_existentes.py -> 35 passaram.",
    "HEAD 7cafca2: tests/test_s74_corpus_butanta.py + tests/test_regra76_corpus_butanta.py -> 54 passaram, 7 falharam em 33 min (hashes/snapshots historicos: test_a_tolerancia_satura_o_conjunto_fisico_e_por_isso_nao_ha_precipicio, test_o_contrafactual_anterior_a_regra_76_continua_reproduzivel, test_a_variante_pos_microajuste_reproduz_os_totais_medidos, test_o_legado_e_identico_com_e_sem_a_flag_da_secao_74, test_a_secao_77_e_uma_variante_nova_do_snapshot_e_o_historico_continua_intacto, test_a_regra_76_1_so_classifica_as_pecas_sao_as_do_corpus, test_o_legado_nao_ganha_os_gates_nem_muda).",
    "BASE 2c301ac (worktree temporaria, mesmos 2 arquivos): os MESMOS 7 falham e 54 passam (32 min) -> falhas PRE-EXISTENTES da branch 85/86 (cuja suite completa nunca tinha sido rodada), nao da secao 87. Pendencia separada: decidir se os snapshots historicos do corpus sao regravados apos as secoes 85/86.",
    "Calculo offline (CPython 3.14, tools/audit/s74_corpus, 13 fiadas) sobre a geometria exportada do handler do botao: 1055 s, 6 526 pecas, gates 0/0/0/0/0; comparado com sol_r7_13 (aprovado): 6 526/6 526 pecas iguais (fiada, codigo, origem a 0,5 cm, rotacao, comprimento), 0 divergencias."
  ],
  "known_failures": [
    "tests/test_regras_gerais_composicao.py::test_dois_compensadores_evitaveis_viram_meio_bloco (ja' falhava na base).",
    "7 snapshots historicos do corpus (test_s74_corpus_butanta / test_regra76_corpus_butanta) - ja' falhavam na base 2c301ac (secoes 85/86); ver tests.",
    "Revit (historico da sessao): a 1a tentativa de 'Criar blocos' (b4) rodou com OUTRO documento ativo (o usuario trocou para COBERTURA BALCONY) e falhou peca a peca ('The level does not exist') sem criar nada; a 2a tentativa (documento de teste ativado pelo script) derrubou a conexao e o Revit foi reiniciado (sem crash dump analisado; BALCONY nao modificado). Depois do reinicio e da correcao do aparo (7cafca2), a criacao rodou ate o fim - ver physical_deltas.",
    "Analisador da Etapa 3B: 21 avisos (junta coincidente A/B, compensadores adjacentes, trecho que nao fecha) - informativos, do solver legado de 2 fiadas."
  ],
  "physical_deltas": [
    "Entrada do solver pelo botao (cru -> main() real headless): 34 eixos (0,0 cm) e 44 aberturas (0 divergencia) iguais aos da referencia aprovada; antes (layer Paredes, sem referencia, aparando): 52 eixos fragmentados, 46 modulados sem o filtro 49, 33 eixos aparados, W8 5 cm deslocada, porta 8078997 -1/220.",
    "REVIT, fluxo do botao no arquivo cru (copia TESTE S87, HEAD 7cafca2): Etapa 1 real (main) 10,3 s -> 145 Walls / 34 eixos / 55 nos; Analisar 11,4 s (21 avisos legados); refresh do handler apara a W8 (5,0 cm) e reancora; solucao do mesmo motor injetada (geometria conferida <= 0,5 cm); Criar blocos 289,7 s -> 6 526 planejadas / 6 526 criadas / 0 falhas / 0 colisoes / 3 vergas nao resolvidas (igual ao aprovado); leitura de volta e comparacao GEOMETRICA com o aprovado (codigo + posicao a 0,5 cm + rotacao a 1 grau + espelho): 6 526/6 526 iguais, 0 so no aprovado, 0 so no teste. Arquivo salvo: butanta testes cru - TESTE S87 2026-10-08.rvt.",
    "Solucao: 6 526 pecas identicas ao lote aprovado (B39 3162, B34 1544, B19 352, U39 544, U34 288, C09 228, B54 200, C04 167, U19 23, U_CUT 18)."
  ],
  "decisions_taken": [
    "Regra 49 no fluxo CAD passa a so' classificar (o aparo ao envelope da §49 esta' revogado nos fluxos de produto) - coerente com a §86.9 (tocos modulados) e com a referencia aprovada.",
    "A testa do CAD nao protege a sobra de ate' 10 cm (87.3); peitoril ate' 2 cm abaixo da base e' tolerancia de modelagem (87.4).",
    "Preservacao: 'butanta testes' (aprovado, em memoria) salvo como 'butanta testes - APROVADO S86 r7 2026-10-08.rvt' (6 526 pecas); testes em 'butanta testes cru - TESTE S87 2026-10-08.rvt' (copia do cru). Originais intocados; COBERTURA BALCONY (aberto pelo usuario na mesma instancia) intocado."
  ],
  "decisions_pending": [
    "Merge na main (o loader do botao baixa a main) - exige autorizacao especifica do usuario.",
    "Analisador da Etapa 3B (solver legado de 2 fiadas) reporta 21 avisos nesta planta que a Tela 2 nao tem - revisar/aposentar."
  ],
  "next_steps": ["Revisao do PR pelo usuario; apos o merge, clicar no botao no arquivo cru seguindo a §87.6 e conferir."],
  "references": [
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_pairing.py"},
    {"path": "tests/test_cad_flow_butanta_s87.py"},
    {"path": "docs/checkpoints/evidence/2026-10-08-s87-cad-flow/README.json"},
    {"path": "docs/checkpoints/2026-10-08-s86-correcoes-usuario.md"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Causa da diferença (medida no arquivo cru)

Ver REGRAS §87 (seis pontos): layer errado (`Paredes` em vez de `Estrutura _1_`), referência estrutural só do
próprio import, regra 49 aparando, sobra de 5 cm da W8 protegida pela testa, porta 8078997 a −1 cm do nível e
`setup` perdido no handler da Tela 2.

## Evidências

- `docs/checkpoints/evidence/2026-10-08-s87-cad-flow/`: `cad_estrutura_1_lines_cm.json`, `cad_paredes_lines_cm.json`,
  `ref_arq_str_bloco_lines_cm.json`, `openings_cm.json`, `approved_axes_cm.json`, `README.json`.
- Rascunho local (nao versionado) em `%LOCALAPPDATA%/Temp/claude/.../scratchpad/`: `sol_s87_offline.json` (solucao do
  botao, 6 526 pecas), `b2_handler_geo.json` (geometria exportada do handler), `readback_aprovado.json` (6 526 pecas do
  aprovado), `stageA*.json`, `solve_offline.log`, `pytest_suite1.log`, scripts `revit/b1_main.py … b4_create.py`,
  `revit_http.py`, `solve_offline.py`, `compare_sol.py`, `compare_readback.py`.

## Estado final no Revit (2026-10-08, retomado e concluido)

1. `butanta testes cru - TESTE S87 2026-10-08.rvt` **salvo** com as 145 Walls do `main()` real e as **6 526 pecas**
   criadas pela acao "Criar blocos" do handler (lote unico), identicas ao aprovado (comparacao geometrica acima).
2. `butanta testes - APROVADO S86 r7 2026-10-08.rvt` preservado (6 526 pecas, lote 20261008-143828). Documentos do
   usuario (COBERTURA BALCONY, IFC) intocados.
3. O que NAO foi feito: o "Calcular" dentro do Revit pelo engine IronPython da rota MCP (nao representa o CPython do
   botao e bloquearia o Revit por muito tempo) - a solucao foi calculada fora com o MESMO motor sobre a geometria
   exportada do proprio handler e injetada; a identidade das pecas e' a prova. A suite ampla de testes (s74/regra76)
   fica registrada em `tests` quando terminar.
4. **Para o usuario rodar no botao:** depois do merge do PR #50 na `main`, abrir o arquivo cru e seguir a §87.6.
