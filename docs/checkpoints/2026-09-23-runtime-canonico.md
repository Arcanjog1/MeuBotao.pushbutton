# Runtime canônico: regra 48 nos dois canais, loader rastreável, pacote da main

```json
{
  "date": "2026-09-23",
  "scope": "current",
  "branch": "main",
  "base": "4bb88bba5e9cf10cd9f4181243d613851a07d906",
  "head": "8968693b857be85e9f2ba6f617c06e8fdd27072e",
  "pr": "not-created",
  "objective": "Runtime canonico depois do merge do PR #49: a regra 48 (OPCAO A) vale igual nos dois canais de distribuicao (BETA offline e ONLINE) por um unico gate; o loader online prova o commit que roda (SHA resolvido, download pinado, cache com manifest e hashes); pacote beta canonico gerado da main (modulacao-main-<sha7>.zip); instrucoes para os dois PCs mostrarem o mesmo SHA. Trabalho direto na main, sem force push. NAO iniciar a comparacao dos tres Revit.",
  "changes": [
    "REGRA 48 UNIFICADA (nuvem/core/wall_modeling.py): novo `_PostCreationEventHandler._materialization_gate` (laudo -> FATAL bloqueia a RUN -> plano por peca -> conferencia do que fica) chamado por `_execute_create` ANTES de qualquer ramo beta/online; `_execute_solve` calcula laudo/assinatura/contrato nos dois canais; `_execute_delete` e o botao Finalizar usam `finalize_allowed` nos dois canais (alias `beta_finalize_allowed` mantido). Mensagens 'BETA BLOQUEADO (erro fatal...)' viraram 'RUN BLOQUEADA (...)'. O que difere entre canais e' SO' o grupo transacional do beta.",
    "ONLINE §48 ANTES: sem preflight - peca na porta era criada e marcada em vermelho (regra de 2026-08-26). DEPOIS: mesma politica do beta - nao criada; amarracao rejeitada = BOND_UNRESOLVED com parede/no'/fiada/rule_id/sobreposicao/revisao humana; demais pecas criadas; so' FATAL bloqueia.",
    "PROVENIENCIA: `runtime_provenance()`/`runtime_provenance_line()` no motor; linha 'Versao: canal= branch= commit= cache=' no relatorio (ui_state) e no cabecalho do log do solver; `handler.runtime_provenance`.",
    "LOADER (Script.py): `_resolve_branch_commit` (API commits/<branch>, SHA completo obrigatorio); arvore listada e baixada PINADA no SHA (`ref=<sha>`), nunca no nome da branch; cache com `manifest.json` (commit, branch, sha256 por arquivo, package_sha); `_verify_cache` (hash de cada arquivo + nenhum .py extra); `cache=VALIDATED` sem download quando o commit e' o mesmo; `MISS` ressincroniza; sem rede so' roda cache VERIFICADO como `OFFLINE_FALLBACK` dizendo o commit; cache sem manifest nao roda. Banner `MODULACAO AUTOMATICA canal= branch= commit= cache=` + CHANNEL/SOURCE_BRANCH/RESOLVED_COMMIT/PACKAGE_SHA/CACHE_STATUS/LOADER_PATH/CORE_PATH; no beta offline `canal=BETA_OFFLINE commit= package_verified=true`. PACKAGE_SHA cobre so' core/ e e' igual nos dois canais para o mesmo commit (cache escrito com newline='' para bater com `git show`).",
    "PACOTE: tools/beta/build_package.py grava `branch` e `package_name` no manifest e gera `modulacao-<branch>-<sha7>.zip` (--branch/--zip). `pacote_pr49.zip` (09cfdd0) declarado OBSOLETO.",
    "DOCS: docs/RUNTIME_CANONICO.md (contrato, banner, geracao do pacote, instalacao nos dois PCs, checklist do clique humano); REGRAS §48 (escopo unificado) e §3; nuvem/LOADER_SETUP.md (cache com manifest e banner); docs/BETA_MAIN_SAFE_RUNBOOK.md (banner novo).",
    "TESTES: tests/test_materializacao_e_estado_da_run.py roda os casos A..H, 76.1, canaleta, colisao, Z e Finalizar uma vez por canal (fixture `beta` parametrizada em CANAIS); novos `test_regra_48_tem_um_unico_gate_para_os_dois_canais` e `test_canal_online_e_beta_produzem_o_mesmo_laudo_e_o_mesmo_plano`; tests/test_loader_provenance.py (11: download pinado + manifest, VALIDATED sem download, main mudou -> MISS, cache adulterado/faltando/extra -> ressincroniza, sem rede -> OFFLINE_FALLBACK com commit, cache legado sem manifest nao roda, banner nos dois canais, PACKAGE_SHA igual, beta offline sem rede). 5 testes legados do test_script (mecanica do lote anterior com plano degenerado) e 1 de retencao passaram a dublar explicitamente o gate/assinatura - sem enfraquecer asserções."
  ],
  "tests": [
    "Suite completa sem tests/regression (arvore = 8968693): 1691 passaram, 1 pulado, 1 falhou - tests/test_perf_trace_stall_sampler.py (historica, identica na main 4bb88bb). Focados: casos A..H x 2 canais + loader + pacote + preflight + criacao atomica + retencao + lote + espelho + UI: 198 passaram. Mutante 'gate so no beta' derruba 12 testes do canal ONLINE (codigo restaurado, sha256 conferido). tests/regression nao re-executado: engine/ sem diferenca em relacao a 4bb88bb (mesmas 2 falhas historicas medidas em ba66c13)."
  ],
  "known_failures": [
    "Falha historica identica na main: tests/test_perf_trace_stall_sampler.py::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas (UnboundLocalError de ctypes no proprio teste, Windows).",
    "tests/regression: 2 falhas historicas identicas na main (TP1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62) - solver nao tocado nesta etapa (engine/ sem diferenca).",
    "O banner do loader so' pode ser observado dentro do pyRevit: o ONLINE contra o GitHub real e o clique humano no botao NAO foram executados nesta sessao (clique e' acao humana). A logica foi provada com dubles de rede (tests/test_loader_provenance.py) e o pacote offline pelo verificador oficial.",
    "PC CIVIX: nenhuma evidencia de SHA carregado ate' o usuario instalar o pacote e ler o banner."
  ],
  "physical_deltas": [
    "SOLVER: nenhum - nuvem/core/engine/* sem diferenca em relacao a' main inicial (git diff --quiet).",
    "MATERIALIZACAO no canal ONLINE mudou (por decisao do usuario): a peca que ocupa o volume real de abertura (>0,1 cm em planta e altura) ou colide nao e' mais criada; identica ao beta. No beta nada mudou em relacao a 4bb88bb."
  ],
  "decisions_taken": [
    "Uma fonte de verdade, dois modos de carregamento: nenhuma politica por canal.",
    "Cache nunca silencioso: commit resolvido antes de tudo; cache sem manifest ou com hash divergente nao roda.",
    "Pacote canonico nomeado por branch+SHA, nunca por PR."
  ],
  "decisions_pending": [
    "Clique humano no botao real (documento de teste em copia) para observar o banner e o fluxo completo com a OPCAO A.",
    "Instalar o pacote no PC CIVIX e ler o banner (commit=) - so' assim os dois PCs provam o mesmo SHA."
  ],
  "next_steps": [
    "Gerar modulacao-main-<sha7>.zip a partir do MAIN FINAL (apos o push) com tools/beta/build_package.py --zip e verificar com beta_package.verify_beta_package.",
    "Depois do clique humano e da comprovacao do SHA nos dois PCs: comparacao forense dos tres Revit (nao iniciada)."
  ],
  "references": [
    {
      "path": "nuvem/core/wall_modeling.py"
    },
    {
      "path": "nuvem/core/ui_state.py"
    },
    {
      "path": "Script.py"
    },
    {
      "path": "tools/beta/build_package.py"
    },
    {
      "path": "tests/test_loader_provenance.py"
    },
    {
      "path": "tests/test_materializacao_e_estado_da_run.py"
    },
    {
      "path": "docs/RUNTIME_CANONICO.md"
    },
    {
      "path": "nuvem/LOADER_SETUP.md"
    },
    {
      "path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"
    }
  ]
}
```

## 1. Por que existiam dois comportamentos

`_execute_create` só rodava `controlled_beta_preflight` dentro de `if self.controlled_beta:`; o ramo
`else` chamava `_execute_create_batch` direto, herdado da regra de 2026-08-26 ("o diagnóstico não pode
impedir a geração"). O laudo e o contrato de materialização também só eram calculados no beta em
`_execute_solve`, e o Finalizar usava dois critérios (backend beta × botão legado por colisões/door_void).

## 2. Como ficou

`_materialization_gate` é o único lugar da regra 48; `_execute_create` o chama antes de qualquer ramo,
`_execute_solve` sempre publica `beta_preflight`/`materialization`, `_execute_delete` e o botão usam
`finalize_allowed`. O beta mantém apenas o grupo transacional externo. Os casos A–H rodam uma vez por
canal; um mutante "gate só no beta" derruba 12 testes do canal ONLINE.

## 3. Loader

Ordem: `commits/main` → SHA completo → cache com manifest do mesmo SHA e hashes íntegros?
`VALIDATED` (0 downloads) : árvore pinada no SHA → `MISS`. Sem rede: cache verificado →
`OFFLINE_FALLBACK` com o commit do cache no banner e no alerta; sem manifest → não roda. O
`PACKAGE_SHA` (só `core/`) é igual nos dois canais para o mesmo commit, porque o cache é escrito com os
bytes do blob (LF).

## 4. Pacote e PCs

Ver [RUNTIME_CANONICO.md](../RUNTIME_CANONICO.md). O pacote é gerado do MAIN FINAL (após o push) e
verificado pelo `beta_package.py`; o nome é `modulacao-main-<sha7>.zip`. `pacote_pr49.zip` está
obsoleto. Cada PC prova a versão pelo `commit=` do banner — sem banner lido, não há prova.
