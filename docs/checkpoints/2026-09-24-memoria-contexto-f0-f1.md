# Checkpoint — Memória técnica F0/F1: contexto e recuperação (2026-09-24)

STATUS: CANDIDATO na branch `claude/new-session-9raf0t` — sem PR e sem merge até
autorização explícita do usuário. Primeira fatia do protocolo "Memória técnica,
agentes e evolução controlada" (documento entregue pelo usuário em 2026-09-24,
auditoria fixada em `15bacec`; o documento não foi versionado no repositório).

```json
{
  "date": "2026-09-24",
  "scope": "current",
  "branch": "claude/new-session-9raf0t",
  "head": "95f368d4cad98ab791d43a875fb8e0bc3ba8d77e",
  "base": "15bacec9d5edc58beaf969c78c7c8d0802f8979e",
  "pr": "not-created",
  "objective": "Primeira fatia (F0 reconciliacao + F1 contexto) do protocolo de memoria tecnica entregue pelo usuario em 2026-09-24: START_HERE como roteador sem estado contraditorio, inventario de fontes com fonte unica por informacao, pacote de contexto por tarefa (origem, SHA, secoes, regras aplicaveis, divida, proximo passo), extensao do validador documental e demonstracao de recuperacao por sessao limpa. Sem mudar solver, imports, baselines ou RVT.",
  "changes": [
    "tools/documentation/context_pack.py (novo): state/pack/verify/check/inventory/domains; indice das REGRAS com rule_id estavel (numero, slug, @n), faixas e sha256; selecao de dominio por aliases (palavra inteira, sem acento); obrigatorias por caminho deterministico e nunca truncadas; relacionadas curadas sempre listadas; divida por dominio; checagens de consistencia (START_HERE, status x main, ultimo checkpoint); verify de pacote velho.",
    "tools/documentation/validate.py: passa a rodar a integridade do manifesto, do registro de divida, dos espelhos de skills, a cobertura de toda secao REGRA OBRIGATORIA/REGRA DO USUARIO e o roteador START_HERE (link de checkpoint especifico e numero de PR fora do Historico bloqueiam). Workflow do CI inalterado.",
    "tools/documentation/test_context_pack.py (novo): repos Git temporarios, clone limpo, regressao de cada achado das revisoes e 24 perguntas de recuperacao sobre o checkout real.",
    "docs/agents/: CONTEXT_MANIFEST.json (fontes, 16 dominios, espelhos), KNOWN_DEBT.json (15 entradas com verificacao exata e evidencia), RETRIEVAL_EVALS.json, SOURCE_INVENTORY.md (gerado), README.md.",
    "docs/START_HERE.md: roteador estavel; PR #40 'sem merge' e checkpoints antigos movidos para secao Historico com escopo; invariantes permanentes extraidas com fonte.",
    "docs/PROJECT_STATUS.md: main 15bacec; #43/#45/#47/#48 como candidatos; #42/#44/#46 integrados via #49; Beta 1 historico; ciclo 2/D4 explicitos; falhas conhecidas por id; esta entrega como CANDIDATO.",
    "README.md, AGENTS.md, CLAUDE.md, docs/decisions/README.md, docs/architecture/README.md: notas datadas de escopo (sem apagar texto); .gitignore: .cache/ (pacotes derivados)."
  ],
  "tests": [
    "python3 -m unittest discover -s tools/documentation -p 'test_*.py' no HEAD final da entrega (com este checkpoint): ver 'Validacao final' no corpo; antes do checkpoint, unica falha esperada era test_state_is_recoverable_and_consistent (LAST_CHECKPOINT_UNREADABLE: o status ja apontava para este checkpoint).",
    "python3 tools/documentation/context_pack.py check / inventory --check: PASS.",
    "python3 tools/documentation/validate.py --base 15bacec9d5edc58beaf969c78c7c8d0802f8979e --main origin/main --require-current-main: ver 'Validacao final'.",
    "python3 tools/documentation/verify_reference_inventory.py --protected-base 15bacec9d5edc58beaf969c78c7c8d0802f8979e: PASS (27 JSON, caminhos protegidos intocados, REGRAS preservadas).",
    "python3 -m pytest tests -q --ignore=tests/regression no HEAD a82dc0b (produto identico ao HEAD avaliado; diff de nuvem/, tests/, Script.py, beta_package.py e .gitignore vazio): 1711 passed, 1 skipped, exit 0, 3044 s - docs/checkpoints/evidence/2026-09-24-memoria-f1-suite-sem-regression.json (log sha256 4eb2f17a...).",
    "Reproducao da divida no HEAD 0dfc7c0 (produto identico): TP1 V1 e TGD V2 falham como registrado; stall sampler e regra 76 (pre-77) passam; 521,7 s - docs/checkpoints/evidence/2026-09-24-memoria-f1-divida-conhecida.json.",
    "Testes do produto citados por KD-10/11/12 (secao 77 ligada, caso B do no 41, estado da Etapa 3B): 5 passed, exit 0 - docs/checkpoints/evidence/2026-09-24-memoria-f1-secao77-produto.json.",
    "Recuperacao por sessao limpa (clone novo do origin, ambiente vazio): ver evidencia de sessao limpa no corpo."
  ],
  "known_failures": [
    "tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]: JUNCTION_MISSING_BINDING 8->9 (KD-01, historica, reproduzida).",
    "tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]: COVERAGE_ROW_MOSTLY_EMPTY 86->92 (KD-02, reproduzida; mascara compensators 61->63, KD-03).",
    "tests/test_perf_trace_stall_sampler.py::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas: registrada como historica nos checkpoints anteriores, PASSOU em Linux/Python 3.11.15 (KD-04 NEEDS_REVIEW, nao declarada corrigida).",
    "Demais dividas abertas indexadas em docs/agents/KNOWN_DEBT.json (KD-05..KD-14, KD-DOC-01), sem mudanca nesta entrega."
  ],
  "physical_deltas": [
    "Nao aplicavel: nenhuma mudanca de solver, catalogo, baseline, corpus ou RVT; diff de produto vazio."
  ],
  "decisions_taken": [
    "Escopo definido pelo usuario ao entregar o protocolo (2026-09-24, 'Primeira entrega solicitada ao executor'): implementar a fatia de organizacao e recuperacao de contexto em branch isolada, sem solver/imports/baselines/RVT.",
    "Registro de divida em docs/agents/KNOWN_DEBT.json como INDICE (evidencia continua nos checkpoints); status de PR e ultimo checkpoint so no PROJECT_STATUS (START_HERE vira roteador).",
    "Nenhuma decisao normativa: nenhuma regra de modulacao criada, alterada ou promovida."
  ],
  "decisions_pending": [
    "Autorizar (ou nao) PR/merge desta fatia na main.",
    "Proxima fatia do protocolo (F2 memoria estruturada: casos, linhagem, importacao idempotente) - exige nova autorizacao.",
    "Tornar o check documental obrigatorio e proteger a main (mudanca administrativa).",
    "Carregadas do ciclo 2: corrigir o import '1 PAV' do doc de teste; baseline TGD V2 (regravar ou manter a falha); D2/D3 em ciclo proprio.",
    "Divida documental KD-DOC-01 (espelho .Codex/checkpoints, heading 30.8 x regra 78, snapshot, rules/junctions, tests/README, backlog) em entregas proprias."
  ],
  "next_steps": [
    "Revisao humana desta fatia e decisao sobre PR/merge.",
    "Ciclo 3 do solver somente com nova autorizacao (D6 verga/contraverga, D9-D13, D14, 3B, D16); D2/D3 em ciclo proprio."
  ],
  "references": [
    {
      "path": "docs/PROJECT_STATUS.md"
    },
    {
      "path": "docs/START_HERE.md"
    },
    {
      "path": "docs/agents/README.md"
    },
    {
      "path": "docs/agents/CONTEXT_MANIFEST.json"
    },
    {
      "path": "docs/agents/KNOWN_DEBT.json"
    },
    {
      "path": "docs/agents/RETRIEVAL_EVALS.json"
    },
    {
      "path": "docs/agents/SOURCE_INVENTORY.md"
    },
    {
      "path": "tools/documentation/context_pack.py"
    },
    {
      "path": "tools/documentation/test_context_pack.py"
    },
    {
      "path": "tools/documentation/validate.py"
    },
    {
      "path": "docs/checkpoints/2026-09-24-ciclo2-corpus-d5.md"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-24-memoria-f1-divida-conhecida.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-24-memoria-f1-secao77-produto.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-24-memoria-f1-suite-sem-regression.json"
    }
  ]
}
```

## Relatório final (formato do protocolo, Anexo B.3)

**STATUS: CONCLUÍDO NO ESCOPO** da primeira fatia (F0 reconciliação + F1 contexto).
As fatias F2–F7 não foram iniciadas.

### 1. Identidade
Repositório `Arcanjog1/MeuBotao.pushbutton`, branch `claude/new-session-9raf0t`,
base/merge-base `15bacec` (= `origin/main` buscada em 2026-09-24), HEAD avaliado
no JSON acima. Host: Claude Code na nuvem. Modelo configurado da sessão:
`claude-opus-5-5`; o modelo efetivo de cada turno não é verificável pelo
repositório (registrado como UNVERIFIED nos pacotes).

### 2. Estado anterior (verificado)
Já existiam: instruções de agente (`AGENTS.md`/`CLAUDE.md`), busca progressiva,
`START_HERE` (com estado contraditório: PR #40 "sem merge" apesar de mesclado em
`61d4f6c`), `PROJECT_STATUS` com JSON oficial/candidatos e contradições internas
(#42/#44/#46 como draft apesar do #49; Beta 1 "não ancestral"; ciclo 2 "não
iniciado"), checkpoints com JSON validado (28), `validate.py` no CI, inventário de
referências humanas com hash, `patterns.py` com a barreira `source == "solver"`.
Não existia: catálogo de fontes por domínio, pacote de contexto por tarefa,
índice de dívida com verificação exata, avaliação de recuperação.

### 3. Reaproveitamento
Estendidos, não substituídos: `tools/documentation/validate.py` (mesmo CI, sem
alterar o workflow), `capture_validation.py` (evidências), `metadata()`/`git()`
do validador (importados pelo novo módulo), `START_HERE`/`PROJECT_STATUS`
(reconciliados, histórico preservado com escopo), `rules/`, `benchmark/`,
`reference_projects/` (catalogados como índices/evidência). Nenhum arquivo movido.

### 4. Implementação (funcional e testada)
- `tools/documentation/context_pack.py`: `state`, `pack`, `verify`, `check`,
  `inventory`, `domains`.
- `docs/agents/CONTEXT_MANIFEST.json` (fontes, 16 domínios, seções obrigatórias por
  número + heading, espelhos de skills), `KNOWN_DEBT.json`, `RETRIEVAL_EVALS.json`,
  `SOURCE_INVENTORY.md` (gerado), `README.md` (uso e limites).
- `validate.py`: integridade do manifesto/dívida/espelhos, cobertura de toda
  "REGRA OBRIGATÓRIA"/"REGRA DO USUÁRIO" e roteador `START_HERE` sem número de
  PR nem checkpoint específico fora do "Histórico".
- Proposta, não implementada: memória de casos, importação com linhagem, índice
  SQLite, experimentos, gates diferenciais, evolução de `patterns.py`, modo sombra.

### 5. Memória e contexto
Pacote cita cada fonte com sha256 no commit avaliado e cada seção das REGRAS com
`rule_id` estável (número, ou slug do título; `@n` para números repetidos, ex.
`66.3@2`), linhas, sha256 e rótulos do heading. Obrigatórias nunca são cortadas
pelo orçamento; relacionadas curadas sempre listadas; candidatas fora da meta
listadas. `verify` acusa pacote velho (HEAD, hashes, main movida, inconsistência
nova). Continuidade: `state` numa sessão limpa recupera HEAD, main, último
checkpoint, dívida e próximo passo (demonstrado em clone limpo — evidência abaixo).

### 6. Aprendizagem
Nenhum caso importado, nenhuma linhagem registrada, nenhuma hipótese promovida.
**A memória não influencia a produção** (nenhum arquivo de `nuvem/`, `tests/`,
`Script.py` ou baseline mudou — diff de produto vazio).

### 7. Avaliação
Ver `tests` no JSON (comandos, SHA, exit codes, logs com hash em
`docs/checkpoints/evidence/`).

### 8. Benchmark
Não executado por completo (sem mudança comportamental). Reproduzidos os casos
da dívida: TP1 V1 `JUNCTION_MISSING_BINDING` 8→9 e TGD V2
`COVERAGE_ROW_MOSTLY_EMPTY` 86→92 falham como registrado; compensators não
reavaliado (assert crítico falha antes). Corpus inalterado.

### 9. Segurança
Nenhuma credencial, RVT ou dado privado adicionado. Texto da tarefa não amplia
escopo (`--allow` exige `--authorization-ref`; teste SEC-01). Proteção da main
e checks obrigatórios continuam **não configurados** (mudança administrativa
separada, não feita). Nenhum agendamento/monitoramento criado.

### 10. Revit
NÃO EXECUTADO / NÃO NECESSÁRIO NESTA ETAPA.

### 11. Desempenho
Custo de contexto medido (estimativa chars/4, obrigatório por domínio isolado):
| domínio | seções obrigatórias | relacionadas curadas | tokens obrigatórios (inclui ~4,4 mil do nível 0) |
|---|---|---|---|
| amarracao | 17 | 13 | 23 276 |
| compensadores | 9 | 7 | 16 347 |
| aberturas | 12 | 17 | 14 114 |
| canaletas | 14 | 11 | 12 269 |
| tolerancias_fechamento | 7 | 7 | 11 580 |
| wall_modeling | 21 | 14 | 10 755 |
| bonecas_pilaretes | 9 | 8 | 10 445 |
| criacao_revit | 7 | 7 | 9 644 |
| prisma_fiadas | 10 | 23 | 9 626 |
| vergas_lintel_cinta | 9 | 7 | 8 976 |
| catalogo | 7 | 12 | 8 970 |
| benchmark | 2 | 9 | 8 507 |
| corpus_selecao | 4 | 7 | 8 187 |
| runtime_loader | 1 | 2 | 6 039 |
| ui_revisao | 1 | 12 | 4 815 |
| governanca | 0 | 7 | 4 406 |
Meta proposta de 4–8 mil tokens por pacote não é atingida nos domínios críticos;
nada é truncado e o excesso é marcado (`mandatory_over_budget`). Runtime do
produto: não medido (sem mudança).

### 12. Entrega Git
Commits na branch: WIP `0dfc7c0`, `a82dc0b`, correções das revisões `92d7a5a`,
`642c521`, `4f22b05`, `626e54a`, `0e05235`, `4e0fc8c`, `efe4d13`, `1c34afa`, `95f368d` (HEAD avaliado), evidência `4b7bf15` e
este checkpoint. PR: NÃO CRIADO. Merge: NÃO REALIZADO. O check documental do CI fica
vermelho nos pushes intermediários (entrega sem checkpoint) e deve passar neste.

### 13. Limitações e decisões pendentes
Checagens de consistência são estruturais (não provam semântica); `#N` não
qualificado conta como PR no roteador; checkpoint do mesmo dia com o mesmo `head`
não é detectado como mais novo. Aliases e seções
obrigatórias são curadoria: regra nova rotulada obrigatória sem mapeamento quebra
o `check`, mas regra sem rótulo depende de curadoria. Dívida documental residual
em KD-DOC-01. KD-04 passou nesta reprodução (Linux/Python 3.11.15) e precisa ser
reproduzida no ambiente em que falhava. Carregadas do ciclo 2: import '1 PAV',
baseline TGD V2 (decisão humana), D2/D3.

### 14. Próximo passo limitado
Revisão humana desta fatia e decisão sobre abrir PR/merge. Qualquer fatia seguinte
(F2 memória estruturada) e o ciclo 3 do solver só com nova autorização.

## Validação final (HEAD da entrega, com este checkpoint)

Executado em 2026-09-24 sobre o HEAD avaliado `95f368d` com este checkpoint no
índice (só documentação muda depois do HEAD avaliado), `origin/main` = `15bacec`:

| comando | resultado |
|---|---|
| `python3 -m unittest discover -s tools/documentation -p 'test_*.py'` | 71 testes, OK (inclui as 24 perguntas de `RETRIEVAL_EVALS.json` e a recuperação de estado do checkout real) |
| `python3 tools/documentation/validate.py --base 15bacec9d5edc58beaf969c78c7c8d0802f8979e --main origin/main --require-current-main` | PASS, exit 0 |
| `python3 tools/documentation/verify_reference_inventory.py --protected-base 15bacec9d5edc58beaf969c78c7c8d0802f8979e` | PASS (27 JSON; `Script.py`, `nuvem/core`, `nuvem/benchmark`, `tests`, `.github/workflows` intocados; REGRAS preservadas por prefixo) |
| `python3 tools/documentation/context_pack.py check` / `inventory --check` | PASS / PASS |
| `python3 tools/documentation/context_pack.py state --strict` | exit 0 (nenhum ERROR/CONTRADICTION) |
| `git diff 15bacec HEAD -- nuvem tests Script.py beta_package.py` | vazio (única mudança fora de docs/ferramentas: `.cache/` no `.gitignore`) |

## Evidência de sessão limpa

__SESSAO__

## Revisão adversarial

Cada rodada: revisor(es) somente leitura + verificador independente tentando
refutar cada achado; só achados reproduzidos foram corrigidos, sempre com teste de
regressão (`ReviewRegressionTests`).

| rodada | alvo | achados | confirmados | correção |
|---|---|---|---|---|
| 1 | `a82dc0b` (4 dimensões: código/CI, protocolo, documentos, manifesto) | 35 | 26 | `92d7a5a` |
| 2 | delta `a82dc0b..92d7a5a` | 16 | 12 | `642c521` |
| 3 | delta `92d7a5a..642c521` | 3 | 3 | `4f22b05` |
| 4 | delta `642c521..4f22b05` | 5 | 5 | `626e54a` (troca de desenho) |
| 5 | delta `4f22b05..626e54a` | 4 | 3 | `0e05235` |
| 6 | delta `626e54a..0e05235` | 7 | 7 | `4e0fc8c` (contrato final) |
| 7 | delta `0e05235..4e0fc8c` | 4 | 4 | `efe4d13` |
| 8 | delta `4e0fc8c..efe4d13` (critério: falha fechada) | 6 | 6 | `1c34afa` |
| 9 | delta `efe4d13..1c34afa` (última; critério de parada declarado) | 3 | 2 + 1 doc | `95f368d` (não revisado depois) | |

Lição registrada: a detecção de "estado de PR" por heurística de prosa no
`START_HERE` não convergiu (negação, pontuação, plural, tabelas, quebra de linha,
vocabulário) e a ordenação de checkpoints por histórico git não resistiu a
renomear/copiar/restaurar. Os contratos finais são objetivos: o roteador não cita
número de PR fora do "Histórico"; checkpoint mais novo no mesmo dia = `head`
avaliado estritamente descendente.
