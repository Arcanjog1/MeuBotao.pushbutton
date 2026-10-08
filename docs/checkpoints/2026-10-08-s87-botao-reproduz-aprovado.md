# §87 — o botão reproduz a modulação aprovada do BUTANTÃ a partir do arquivo cru

Estado CANDIDATO da branch `claude/script-modulation-blocks-469ec2` (= `claude/revit-butanta-modulation-8611b5`
+ §87). PR [#50](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/50) (draft) para revisão; sem merge. Não é estado oficial nem aprovação normativa.

```json
{
  "date": "2026-10-08",
  "scope": "current",
  "branch": "claude/script-modulation-blocks-469ec2",
  "head": "2a18c547824407f9fba5191127a6fc625da17403",
  "base": "894e3f5278ffa9cb030efe01a70c7305b252af15",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/50",
  "objective": "Fazer o fluxo normal do botao (CAD -> Walls) gerar, a partir do arquivo cru 'butanta testes cru.rvt', a mesma modulacao aprovada pelo usuario em 2026-10-08 (lote 20261008-143828, 6 526 pecas, motor 06ecb87), sem ajustes posteriores via MCP e sem copiar coordenadas da planta.",
  "changes": [
    "87.1 (configuracao, documentado): o layer de paredes do CAD arquitetonico e' 'Estrutura _1_' (46 pares = 46 paredes historicas); 'Paredes' e' acabamento e fragmenta (52 eixos).",
    "87.2 wall_modeling.py: collect_reference_layers_from_document / reference_layer_label / cad_import_display_name; ask_setup(..., reference_layers) e _SetupForm(..., reference_layers) listam layers de TODOS os imports ('<import> | <layer>'); em main() a regra 49 roda depois de dedupe+extend com trim=False (so' classificacao) e o setup (corpus 49.1, tocos) passa ao handler da Tela 2.",
    "87.3 wall_pairing.py: find_wall_end_stubs(..., ignore_locks) / trim_wall_end_stubs(..., ignore_locks=None): no modo sobra de CAD (<= 10 cm) a testa nao protege a ponta; main() apara a sobra na ordem assign -> peitoril -> trim -> extend -> grafo (mesma do fluxo de paredes existentes).",
    "87.4 wall_pairing.py: OPENING_SILL_BELOW_BASE_SNAP_CM = 2.0 e snap_openings_to_wall_base(): peitoril ate' 2 cm abaixo da base sobe para a base com a altura do vao preservada; chamada nos dois fluxos.",
    "main(): len([...]) no lugar de sum(gerador) no contador de eixos fora da planta (quebrava no IronPython do caminho MCP).",
    "tests/revit_stubs.py: ImportInstance; tests/test_cad_flow_butanta_s87.py (17 testes) + evidencia docs/checkpoints/evidence/2026-10-08-s87-cad-flow/ (linhas CAD, aberturas, 34 eixos aprovados).",
    "DOCS: REGRAS §87 (+ notas nas §49 e §86.9), este checkpoint, PROJECT_STATUS, START_HERE."
  ],
  "tests": [
    "HEAD 2a18c54: py -3 -m pytest tests/test_cad_flow_butanta_s87.py tests/test_stub_trim_86_9.py tests/test_reference_layer_filter.py tests/test_corpus_selection_paredes_existentes.py tests/test_channel_ui_and_family_gate.py -q -> 65 passaram (17 novos + 48).",
    "HEAD 2a18c54: suite ampla (test_script + 86.x + s74/regra76 corpus) INTERROMPIDA a pedido do usuario ('PARE') com 97 % rodado: 5-6 falhas marcadas (F) no trecho test_junta_no_toco_86_15 / test_compensator_at_jamb_face_86_13 / test_s74_corpus_butanta / test_regra76_corpus_butanta - nomes NAO capturados (o pytest so' lista no fim). PENDENTE: rodar esses arquivos um a um e classificar (ja' falhavam na base 2c301ac? test_dois_compensadores_evitaveis_viram_meio_bloco ja' falhava).",
    "Calculo offline (CPython 3.14, tools/audit/s74_corpus, 13 fiadas) sobre a geometria exportada do handler do botao: 1055 s, 6 526 pecas, gates 0/0/0/0/0; comparado com sol_r7_13 (aprovado): 6 526/6 526 pecas iguais (fiada, codigo, origem a 0,5 cm, rotacao, comprimento), 0 divergencias."
  ],
  "known_failures": [
    "tests/test_regras_gerais_composicao.py::test_dois_compensadores_evitaveis_viram_meio_bloco (ja' falhava na base).",
    "Revit: a 1a tentativa de 'Criar blocos' (b4) rodou com OUTRO documento ativo (o usuario trocou para COBERTURA BALCONY) e falhou peca a peca ('The level does not exist') sem criar nada; a 2a tentativa (documento de teste ativado pelo script) derrubou a conexao e o Revit foi reiniciado (sem crash dump analisado; BALCONY nao modificado). Nenhum bloco foi criado no Revit nesta sessao.",
    "Analisador da Etapa 3B: 21 avisos (junta coincidente A/B, compensadores adjacentes, trecho que nao fecha) - informativos, do solver legado de 2 fiadas."
  ],
  "physical_deltas": [
    "Entrada do solver pelo botao (cru -> main() real headless): 34 eixos (0,0 cm) e 44 aberturas (0 divergencia) iguais aos da referencia aprovada; antes (layer Paredes, sem referencia, aparando): 52 eixos fragmentados, 46 modulados sem o filtro 49, 33 eixos aparados, W8 5 cm deslocada, porta 8078997 -1/220.",
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

## Onde parou (2026-10-08, interrompido a pedido do usuario)

1. Codigo + testes + evidencia commitados em `2a18c54`; docs neste commit. Branch empurrada; PR aberto (ver `pr`).
2. No Revit (porta 48884): `butanta testes cru - TESTE S87 2026-10-08` aberto e ativo com **145 Walls (34 eixos) criadas
   pelo `main()` real e NAO salvas**; handler da Tela 2 em memoria (`wm._MCP_STATE["h2"]`) com analyze feito; a
   injecao da solucao (b3) foi interrompida; **nenhum bloco criado**. COBERTURA BALCONY e os IFC do usuario intocados.
3. **Para retomar:** (a) ativar o documento de teste; se o Revit foi fechado, reabrir a copia (0 Walls) e rodar
   `b1_main.py` + `b2_analyze_export.py`; (b) `b3_inject.py` (carrega `sol_s87_offline.json`, gate liberado com o aviso
   das 3 vergas nao resolvidas, igual ao aprovado); (c) `b4_create.py` (~10 min, Revit bloqueado - nao trocar de
   documento); (d) `rb_teste.py` + `compare_readback.py readback_aprovado.json readback_teste_s87.json
   approved_axes_cm.json`; (e) opcional: `h2.action = "solve"` no Revit para medir o tempo do solve no caminho do botao
   (o calculo offline ja' provou a identidade das pecas); (f) rodar os arquivos de teste restantes e classificar as
   falhas; (g) fechar o checkpoint (PR, testes) e pedir autorizacao de merge.
