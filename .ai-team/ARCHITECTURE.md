# AI Team Cloud - Arquitetura (V1)

Sistema de loop autonomo Claude (executor) -> Codex (reviewer/router) ->
Claude, rodando 100% em GitHub Actions, sem interacao humana entre as
rodadas e sem depender da maquina do usuario.

Este documento e' a entrega da **FASE A** (arquitetura). O codigo da
**FASE B** vive em `ai_team/` e `.github/workflows/ai-team.yml`.

---

## 1. Capabilities REAIS verificadas (nao inventadas)

Tudo abaixo foi verificado executando os binarios de verdade nesta
sessao, nao lido de memoria. Onde a plataforma nao oferece um controle,
a limitacao esta' registrada na secao 12.

### 1.1 Claude Code CLI - v2.1.252

Verificado com `claude --help` e com chamadas reais.

| Necessidade | Flag oficial | Verificado |
|---|---|---|
| Modo nao interativo | `-p` / `--print` | sim |
| Modelo | `--model <alias\|nome>` (`sonnet`, `opus`, `claude-opus-5`) | sim |
| **Nivel de raciocinio** | `--effort <low\|medium\|high\|xhigh\|max>` | sim |
| Saida estruturada | `--output-format json` + `--json-schema <schema>` | sim |
| Restricao de ferramentas | `--tools`, `--allowedTools`, `--disallowedTools` | sim |
| Permissoes | `--permission-mode <acceptEdits\|dontAsk\|plan\|...>` | sim |
| Teto de custo | `--max-budget-usd <valor>` | sim (help) |
| Hooks / settings | `--settings <arquivo-ou-json>` | sim (help) |
| Instrucao extra de sistema | `--append-system-prompt` | sim (help) |

**Prova de que `--effort` e' real** (mesmo prompt, mesmo modelo
`sonnet`, so' mudando a flag):

```
--effort low   -> usage.output_tokens_details.thinking_tokens = 0    (163 output tokens)
--effort high  -> usage.output_tokens_details.thinking_tokens = 371  (602 output tokens)
```

Ou seja: o raciocinio e' configurado **de verdade** na invocacao, nao
"pedindo no prompt para pensar mais". Esse era um requisito explicito
(secao 3 do pedido).

**Forma real do JSON de saida** (`--output-format json`), campos que o
orquestrador consome:

```
{
  "type": "result", "subtype": "success", "is_error": false,
  "result": "<texto>",
  "structured_output": { ... },        <- objeto ja' validado contra --json-schema
  "num_turns": 2, "duration_ms": 1948,
  "total_cost_usd": 0.021335,
  "usage": { "input_tokens", "output_tokens",
             "output_tokens_details": { "thinking_tokens" }, ... },
  "modelUsage": { "<modelo>": { "costUSD", "inputTokens", ... } },
  "permission_denials": [], "session_id": "...", "terminal_reason": "completed"
}
```

`structured_output` e' a chave: com `--json-schema`, o CLI devolve o
objeto ja' validado. O orquestrador **nao** faz parsing heuristico de
texto livre.

### 1.2 OpenAI Codex CLI - v0.151.0

Verificado com `codex exec --help` e com uma invocacao real.

| Necessidade | Flag oficial | Verificado |
|---|---|---|
| Modo nao interativo | `codex exec` | sim |
| Modelo | `-m` / `--model <MODEL>` | sim |
| **Nivel de raciocinio** | `-c model_reasoning_effort="<nivel>"` | sim |
| Saida estruturada | `--output-schema <arquivo.json>` | sim |
| Mensagem final em arquivo | `-o` / `--output-last-message <FILE>` | sim |
| Sandbox READ-ONLY | `-s read-only` | sim |
| Eventos JSONL | `--json` | sim |
| Ignorar config do usuario | `--ignore-user-config` | sim |

Chave `model_reasoning_effort` confirmada dentro do binario e no
cabecalho de sessao impresso pelo proprio Codex:

```
$ codex exec -s read-only -c model_reasoning_effort="high" ...
--------
model: gpt-5.6-sol
approval: never
sandbox: read-only
reasoning effort: high      <- aplicado de verdade
--------
```

**ATENCAO / armadilha encontrada:** o Codex CLI **nao valida** o valor
de `model_reasoning_effort` do lado do cliente. Passando
`-c model_reasoning_effort="bogusvalue"` ele imprime
`reasoning effort: bogusvalue` e so' falha depois, na API. Por isso o
orquestrador **obrigatoriamente** valida contra uma whitelist antes de
montar o argv (secao 5.3). Valores encontrados no binario:
`minimal, low, medium, high, xhigh, max, ultra` - a config so' libera
os cinco primeiros por padrao.

### 1.3 GitHub Actions - actions oficiais

| Action | O que oferece | Decisao |
|---|---|---|
| `anthropics/claude-code-action` | **Nao tem input `model` nem `effort`.** Tudo passa por `claude_args`, que e' repassado cru ao CLI. E' orientada a eventos do GitHub (comentario `@claude`, PR, issue), com `trigger_phrase`, `use_sticky_comment`, `track_progress`. | **Nao usar.** Para um loop generico ela so' adicionaria a camada de comentario/PR que nao queremos, e o controle de modelo/effort acabaria em `claude_args` do mesmo jeito. Usamos o CLI direto. |
| `openai/codex-action` | Tem inputs de primeira classe: `model`, **`effort`**, `output-schema`, `sandbox`, `codex-args`, `output-file`, `allow-users`, `safety-strategy`. | **Nao usar na V1, mas e' a alternativa oficial.** Usamos `codex exec` direto para manter os dois agentes sob o mesmo orquestrador e o mesmo formato de estado. A paridade de flags esta' garantida. |

**Decisao de arquitetura:** o workflow instala os dois CLIs e o
orquestrador Python os invoca como subprocessos. Motivo: um unico ponto
de controle para estado, roteamento, gates, redacao de segredos e
limites de custo - que e' exatamente o que a secao 1 do pedido exige
("orquestrador deterministico no meio").

---

## 2. Fluxo

```
                 workflow_dispatch (task, mode, max_rounds, ...)
                              |
                              v
                   +----------------------+
                   |    ORCHESTRATOR      |   (deterministico, Python)
                   |  ai_team/orchestrator|
                   +----------------------+
                              |
        ROUND N               v
     +----------------------------------------------+
     | 1. CLAUDE (executor, ESCRITOR)               |
     |    claude -p --model M --effort E            |
     |           --json-schema claude_result        |
     |           --output-format json               |
     |    -> claude_round_NNN.json                  |
     +----------------------------------------------+
                              |
     +----------------------------------------------+
     | 2. DETERMINISTIC GATE (juiz tecnico)         |
     |    pytest + metricas vs baseline             |
     |    -> gate_round_NNN.json                    |
     +----------------------------------------------+
                              |
     +----------------------------------------------+
     | 3. CODEX (reviewer/router, READ-ONLY)        |
     |    codex exec -s read-only -m M              |
     |      -c model_reasoning_effort=E             |
     |      --output-schema codex_decision          |
     |    recebe: tarefa, rodada, saida do Claude,  |
     |    git diff, arquivos, testes, gate, commits |
     |    -> codex_round_NNN.json                   |
     +----------------------------------------------+
                              |
     +----------------------------------------------+
     | 4. RESOLVE (gate tem veto sobre a IA)        |
     |    verdict final da rodada                   |
     +----------------------------------------------+
                    |                    |
              CONTINUE               terminal
                    |                    |
     next_model / next_effort /          v
     next_prompt aplicados de       final_result.json
     verdade no proximo argv        + artifacts + branch
                    |
                    +--> ROUND N+1
```

---

## 3. Estrutura de arquivos

Desvio consciente da sugestao da secao 16 do pedido (que permitia
melhorar): o codigo Python fica em `ai_team/`, **nao** em `.ai-team/`.

Motivo tecnico: `.ai-team` nao e' um nome de pacote Python importavel
(ponto e hifen), o que obrigaria a giria de `sys.path` em todo teste.
Com `ai_team/` os testes rodam na suite normal do projeto
(`python3 -m pytest tests/ -q`) sem nenhum truque.

`.ai-team/` continua existindo, mas com o papel que faz sentido: **doc
de arquitetura + estado de execucao** (que e' ignorado pelo git).

```
.github/workflows/ai-team.yml       # entrada pela UI do GitHub

ai_team/                            # PACOTE PYTHON (versionado, testavel)
  __init__.py
  __main__.py                       # python -m ai_team
  cli.py                            # parsing de argumentos / entrypoint
  config.py                         # carrega e VALIDA config.yaml
  config.yaml                       # politica: modelos, efforts, limites, gates
  state.py                          # run dir, state.json, registro por rodada
  redact.py                         # redacao de segredos (tudo passa por aqui)
  routing.py                        # valida/clampa a decisao do Codex
  loop.py                           # o loop autonomo
  gates.py                          # gate deterministico (juiz final)
  safety.py                         # operacoes git proibidas
  agents/
    __init__.py
    base.py                         # AgentInvocation / AgentResult
    executor.py                     # SubprocessExecutor + ScriptedExecutor
    claude_agent.py                 # monta argv do claude + parseia JSON
    codex_agent.py                  # monta argv do codex + parseia JSON
  prompts/
    claude_initial.md
    claude_continue.md
    codex_review.md
  schemas/
    claude_result.schema.json
    codex_decision.schema.json
    final_result.schema.json
  guard/
    pretooluse_git_guard.py         # hook que BLOQUEIA git perigoso
    claude_settings.json            # registra o hook no CLI

.ai-team/
  ARCHITECTURE.md                   # este arquivo (versionado)
  runs/<run-id>/                    # estado de execucao (NAO versionado)
    task.json  state.json
    claude_round_001.json  gate_round_001.json  codex_round_001.json
    ...
    final_result.json

tests/ai_team/                      # suite do orquestrador
```

---

## 4. Contratos (schemas)

### 4.1 `claude_result.schema.json` - o que o Claude devolve

Aplicado via `--json-schema`, entao vem validado em
`structured_output`.

```json
{
  "summary":        "o que foi feito nesta rodada",
  "status":         "DONE | PARTIAL | BLOCKED | NEEDS_REVIT | NEEDS_HUMAN",
  "changed_files":  ["..."],
  "commits":        ["sha curto + assunto"],
  "tests_run":      "comando + resultado",
  "root_cause":     "a causa raiz tratada nesta rodada",
  "remaining_work": ["..."],
  "blockers":       ["..."],
  "confidence":     "LOW | MEDIUM | HIGH"
}
```

### 4.2 `codex_decision.schema.json` - o que o Codex devolve

Aplicado via `--output-schema`.

```json
{
  "verdict":        "CONTINUE | APPROVED | NEEDS_HUMAN | NEEDS_REVIT | FAILED",
  "next_agent":     "claude",
  "next_model":     "claude-sonnet-5",
  "next_reasoning": "medium",
  "next_prompt":    "instrucao completa para a proxima rodada do Claude",
  "issues":         [{"severity": "...", "file": "...", "detail": "..."}],
  "routing_reason": "POR QUE mudou o modelo/reasoning",
  "why":            "justificativa do verdict"
}
```

`routing_reason` e' **obrigatorio** - a secao 5 do pedido exige que o
Codex justifique cada mudanca de modelo/raciocinio.

### 4.3 `final_result.schema.json`

Resultado consolidado da run: status final, rodadas, custo, modelos
usados por rodada com a justificativa, resultado do gate, branch, SHA.

---

## 5. Roteamento: como modelo e raciocinio mudam de verdade

### 5.1 A politica (nao e' "baseada em palavras")

Vive em `ai_team/config.yaml`, explicita, versionada, auditavel. O Codex
recebe a politica dentro do prompt e precisa justificar qualquer
mudanca em `routing_reason`.

| Classe de trabalho | Modelo | Effort |
|---|---|---|
| `mechanical` - renomear, formatar, ajuste obvio de teste | `claude-haiku-4-5` | `low` |
| `standard` - implementacao normal, correcao localizada | `claude-sonnet-5` | `medium` |
| `deep` - causa raiz, arquitetura, invariancia, regressao teimosa | `claude-opus-5` | `high` |
| `critical` - falha de gate que ja' resistiu a uma rodada | `claude-opus-5` | `xhigh` |

O mesmo vale para o proprio Codex: revisao de rotina em `medium`,
revisao critica/arquitetural (ou gate vermelho) em `high`.

### 5.2 Aplicacao real

`ClaudeAgent.build_argv()` e `CodexAgent.build_argv()` sao funcoes
**puras**: recebem a decisao roteada e devolvem a lista de argumentos.
O executor apenas executa essa lista. Isso torna a exigencia
"o modelo/reasoning selecionado e' aplicado" **testavel sem chamar a
API** - a suite afirma sobre o argv exato:

```
["claude", "-p", "--model", "claude-opus-5", "--effort", "high", ...]
["codex", "exec", "-m", "gpt-5.6-sol", "-c", 'model_reasoning_effort="high"', ...]
```

### 5.3 Whitelist obrigatoria (defesa)

O Codex e' um modelo: a string que ele devolve **nunca** entra no argv
sem passar por `routing.py`:

1. regex `^[A-Za-z0-9._-]+$` (impede injecao de argumento);
2. pertencer a `allowed_models` / `allowed_efforts` da config;
3. se falhar qualquer um dos dois -> **clampa** para o default da classe
   e registra `routing_override` no estado, com o valor recusado.

O loop nunca aborta por um roteamento invalido - ele degrada e registra.

---

## 6. O gate deterministico e' o juiz final

Tres niveis, como pede a secao 7:

```
Claude   = executor          (opiniao)
Codex    = reviewer/router   (opiniao)
GATE     = juiz tecnico      (FATO)  <- vence os dois
```

O gate roda **depois do Claude e antes do Codex**, e o resultado dele
entra no prompt do Codex. Checagens:

- **`pytest`** (HARD): `python3 -m pytest tests/ -q -m "not slow"`.
  Vermelho = HARD FAIL, sem discussao.
- **metricas vs baseline** (HARD quando ha' baseline): compara um JSON
  de metricas com `ai_team/baselines/<nome>.json`, por metrica, com
  direcao (`higher_is_better` / `lower_is_better`) e tolerancia.
  E' aqui que entra o caso `openings: 91/91 -> 89/91` da secao 7:
  regressao numerica = FAILED, mesmo com Claude OK e Codex APPROVED.
- **invariantes de repositorio** (HARD): a branch e' a branch da tarefa?
  `main` continua no mesmo SHA? nao ha' arquivo de segredo novo?

Precedencia final (implementada em `loop.py`):

| Gate | Codex | Resultado |
|---|---|---|
| PASS | APPROVED | `READY_FOR_HUMAN_REVIEW` |
| **FAIL** | **APPROVED** | **`FAILED` / `DO_NOT_MERGE`** (o gate vence) |
| FAIL | CONTINUE | continua, com a falha injetada no proximo prompt |
| PASS | CONTINUE | continua |
| qualquer | NEEDS_HUMAN / NEEDS_REVIT / FAILED | termina nesse estado |

Refinamento util: um gate vermelho com rodadas sobrando **rebaixa**
`APPROVED` para `CONTINUE` (dando ao Claude a chance de consertar) e
sobe o Codex para `high`. Na ultima rodada, ou se o gate seguir
vermelho, o resultado e' `FAILED`. Um gate HARD vermelho **nunca** pode
terminar como `READY_FOR_HUMAN_REVIEW`.

---

## 7. Estados

| Estado | Quando | O que o sistema faz |
|---|---|---|
| `READY_FOR_HUMAN_REVIEW` | Codex APPROVED + gate verde | branch + commits + PR pronta; merge continua humano |
| `CONTINUE` | ha' trabalho e rodadas | proxima rodada, automatica |
| `NEEDS_HUMAN` | decisao arquitetural, mudanca de requisito, gate HARD sem solucao pre-aprovada, discordancia teimosa, acao perigosa | para, preserva estado, explica a pergunta |
| `NEEDS_REVIT` | precisa de Revit vivo / MCP local | para, preserva estado, escreve **exatamente o que capturar** para retomar depois |
| `FAILED` | gate HARD vermelho no fim, ou erro irrecuperavel | para, `DO_NOT_MERGE` |
| `MAX_ROUNDS` / `TIMEOUT` | limites | para, preserva estado |
| `HEADLESS_OK` | flag interna: tudo que a tarefa precisa esta' no snapshot do git | segue sozinho |

`NEEDS_REVIT` grava `revit_capture_request` em `final_result.json`, com
a lista do que precisa ser medido - a tarefa nao se perde.

---

## 8. Modos

`diagnose` (read-only, sem commit) - `implement` - `review` (so' Codex) -
`benchmark` (gate + metricas) - `full` (Claude -> Codex -> ... -> gate ->
PR pronta) - `selftest` (secao 11).

---

## 9. Git

- Uma branch por tarefa: `ai/<slug-da-tarefa>` (ex.:
  `ai/cr-2fe-centerline-invariance`).
- **Claude e' o unico agente escritor.** Codex roda com `-s read-only`,
  imposto pelo proprio sandbox do Codex, nao por instrucao no prompt.
- `concurrency` no workflow impede duas runs no mesmo working tree.
- O **orquestrador** faz o push, nao o Claude - o hook de guarda bloqueia
  `git push` vindo do agente.
- **Um commit por causa raiz** (secao 11): o prompt exige, e o gate roda
  entre rodadas, entao correcao A e correcao B caem em rodadas/commits
  separados com gate no meio.
- **Nunca merge automatico em `main`** (secao 12). O teto e'
  `READY_FOR_HUMAN_REVIEW`.

---

## 10. Seguranca

### 10.1 Bloqueio real de comandos perigosos

Nao e' instrucao no prompt - e' um **hook `PreToolUse`** do Claude Code
(`ai_team/guard/pretooluse_git_guard.py`, registrado via
`--settings`), que inspeciona todo comando `Bash` antes de executar e
devolve `permissionDecision: "deny"` para:

```
git reset --hard          git clean -fd            git push --force / -f
git push (qualquer)       git branch -D main       git checkout main
git merge (em main)       rm -rf /                 alteracao de secrets
curl/wget de $ANTHROPIC_API_KEY / $OPENAI_API_KEY / tokens
```

Reforco em profundidade: `--disallowedTools` no argv + verificacao de
invariantes de repositorio no gate (SHA de `main` inalterado).

### 10.2 Segredos

- Vivem **somente** em GitHub Actions Secrets: `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`. `GITHUB_TOKEN` e' o do proprio runner.
- `ai_team/redact.py` e' aplicado a **todo** texto antes de ir para
  disco, para o log ou para o step summary: valores exatos das
  variaveis de ambiente sensiveis + padroes (`sk-...`, `sk-ant-...`,
  `ghp_...`, `github_pat_...`, `gho_...`, chaves privadas PEM).
- Nenhuma chave e' passada ao Codex/Claude dentro de prompt.
- O prompt do Codex e' montado a partir de `git diff` e do estado - e
  passa pela mesma redacao antes de ser gravado.

---

## 11. Teste sintetico (secao 21 do pedido)

Requisito explicito: **nao** testar com mudanca real no wall modeling.

O orquestrador tem um `ScriptedExecutor`: mesma interface do
`SubprocessExecutor`, mas devolve respostas de fixture. Com ele o loop
inteiro roda **offline, sem nenhuma API key**, exercitando o codigo de
producao (routing, gates, estado, parada, redacao) - so' a fronteira do
subprocesso e' trocada.

A tarefa sintetica mexe apenas num arquivo de fixture descartavel
(`ai_team/fixtures/sandbox_target.txt`), nunca no solver.

Os 14 pontos exigidos viram asserts na suite `tests/ai_team/`.

---

## 12. Limitacoes conhecidas (honestas)

1. **`claude` CLI v2.1.252 nao tem `--max-turns`.** O controle de custo
   por invocacao e' `--max-budget-usd` (suportado) + `max_rounds` /
   `max_claude_calls` / `timeout_minutes` no orquestrador.
2. **O Codex CLI nao valida `model_reasoning_effort` no cliente.** Um
   valor invalido so' falha na API. Mitigado pela whitelist (5.3).
3. **Custo do Codex:** o `codex exec` nao expoe um campo de custo por
   run equivalente ao `total_cost_usd` do Claude. Registramos duracao,
   modelo e effort; o custo do Claude vem completo (`total_cost_usd`,
   `usage`, `modelUsage`).
4. **`NEEDS_REVIT` nao retoma sozinho na V1.** Ele preserva o estado e
   descreve a captura necessaria; a retomada com um snapshot novo fica
   para a V2.
5. **Comando por Issue (`/ai implement ...`) nao entra na V1** (secao
   18 do pedido permite adiar). A arquitetura ja' separa "gatilho" de
   "orquestrador", entao adicionar um `on: issue_comment` e' so' um
   novo job chamando o mesmo `python -m ai_team`.
6. **O ambiente desta sessao nao alcanca `api.openai.com`** (bloqueado
   pelo proxy de egress: `HTTP CONNECT 403`). Portanto o loop **live**
   Claude+Codex nao pode ser executado daqui - so' no runner do GitHub
   Actions, que tem egress aberto. O que foi provado aqui: as flags e o
   formato de saida reais do Claude (chamadas de verdade), as flags
   reais do Codex (invocacao de verdade, ate' o cabecalho de sessao), e
   o loop completo com o `ScriptedExecutor`.
7. **Merge em `main` continua humano por decisao de projeto** (secao 12
   do pedido), mesmo o `CLAUDE.md` do repositorio autorizando merge
   direto para trabalho manual.

---

## 13. O que foi verificado ao vivo (nao so' em fixture)

Alem da suite offline, estes pontos foram exercitados contra os binarios
reais nesta sessao:

| Verificacao | Como | Resultado |
|---|---|---|
| `--effort` muda o raciocinio de verdade | mesmo prompt/modelo, `low` vs `high` | 0 vs 371 thinking tokens |
| O adaptador do Claude casa com o CLI real | `ClaudeAgent` + `SubprocessExecutor` + `claude` de verdade | `structured_output` no schema, `ok=True`, custo capturado |
| O argv leva modelo e effort | mesma chamada real | `--model claude-haiku-4-5 --effort low` |
| **O hook de guarda BLOQUEIA de verdade** | pedido real ao Claude para rodar `git push origin HEAD --dry-run` | negado, com `permission_denials` preenchido e a razao do guard chegando ao modelo |
| `$CLAUDE_PROJECT_DIR` e' expandido no comando do hook | mesma prova, com o caminho absoluto | bloqueio manteve-se; o hook nao depende do cwd |
| Flags do Codex sao aceitas | `codex exec -s read-only -c model_reasoning_effort=...` | cabecalho de sessao confirmou modelo, sandbox e effort |
| O Codex CLI nao valida o effort | `-c model_reasoning_effort="bogusvalue"` | aceito pelo cliente -> por isso a whitelist e' obrigatoria |
| Loop completo encadeia sozinho | `--mode selftest`, offline | rodada 1 `sonnet/medium` -> revisor pede `opus/high` -> rodada 2 executa em `opus/high` -> `READY_FOR_HUMAN_REVIEW` |

O que **nao** pode ser provado deste ambiente: o loop live com o Codex
real, porque `api.openai.com` esta' bloqueado pelo proxy de egress
(`HTTP CONNECT 403`). Isso e' limitacao do ambiente desta sessao, nao do
sistema - o runner do GitHub Actions tem egress aberto.
