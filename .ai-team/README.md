# AI Team Cloud - guia de operacao

Loop autonomo **Claude (executor) -> gate -> Codex (revisor/roteador) ->
Claude**, rodando inteiramente no GitHub Actions. Voce inicia UMA tarefa;
as rodadas seguintes acontecem sozinhas, com seu computador desligado.

A arquitetura e as capabilities verificadas estao em
[`ARCHITECTURE.md`](ARCHITECTURE.md). Este arquivo e' o manual de uso.

---

## 1. Secrets necessarios

Em **Settings -> Secrets and variables -> Actions -> New repository secret**:

| Secret | Para que serve | Obrigatorio |
|---|---|---|
| `ANTHROPIC_API_KEY` | invocar o Claude (executor) | sim, exceto no modo `selftest` |
| `OPENAI_API_KEY` | invocar o Codex (revisor/roteador) | sim, exceto no modo `selftest` |

`GITHUB_TOKEN` e' fornecido pelo proprio runner - nao crie um.

As chaves nunca saem dos Secrets: nao vao para arquivo do repositorio,
nao entram em prompt, e qualquer eco delas e' apagado por
`ai_team/redact.py` antes de ir para o disco, para o log ou para o
resumo.

Se um secret faltar, o workflow **falha no primeiro passo** com a
mensagem certa, em vez de gastar meia hora de runner para descobrir
depois.

---

## 2. Como iniciar

**Actions -> AI Team -> Run workflow.**

| Campo | O que colocar |
|---|---|
| `task` | A tarefa. Seja especifico: o que investigar/corrigir **e como saber que ficou pronto**. |
| `mode` | `full` na duvida. Veja a tabela de modos abaixo. |
| `max_rounds` | `3` e' o default. O teto absoluto (`8`) vem da config e a UI nao consegue passar dele. |
| `preferred_model` | Opcional. So' vale para a **rodada 1** - o Codex escolhe da rodada 2 em diante. |
| `preferred_reasoning` | Opcional, mesma regra. |
| `branch_name` | Opcional. Vazio = `ai/<slug-da-tarefa>`. |

### Primeira vez: rode o `selftest`

Antes de gastar uma run de verdade, rode com `mode: selftest`. Ele
exercita o loop inteiro com agentes roteirizados, **offline e sem
nenhuma API key**, e prova que o encanamento esta' de pe' no runner.

---

## 3. Modos

| Modo | O que faz |
|---|---|
| `full` | Claude -> gate -> Codex -> ... -> PR pronta para revisao humana. |
| `implement` | Foco em implementar; mesmo loop. |
| `diagnose` | Investigar e relatar, sem esperar correcao. |
| `review` | Enfase na revisao do que ja' existe. |
| `benchmark` | Enfase no gate de metricas. |
| `selftest` | Ensaio offline do orquestrador. Nao chama API, nao cria branch. |

---

## 4. Como o modelo e o raciocinio mudam sozinhos

Depois de cada rodada, o Codex recebe automaticamente a tarefa, a
resposta do Claude, o `git diff`, os arquivos alterados, os commits, o
resultado do gate e o historico. Ele devolve um JSON com, entre outros:

```json
{"verdict": "CONTINUE",
 "next_model": "claude-opus-5",
 "next_reasoning": "high",
 "next_prompt": "...",
 "routing_reason": "por que este modelo e este nivel"}
```

O orquestrador **aplica isso de verdade** na proxima invocacao:

```
claude -p "<next_prompt>" --model claude-opus-5 --effort high ...
```

Nao e' "pedir no prompt para pensar mais": `--effort` e' uma flag real do
CLI. Medido nesta maquina, mesmo prompt e mesmo modelo:
`--effort low` -> 0 thinking tokens; `--effort high` -> 371.

A politica das classes (`mechanical`/`standard`/`deep`/`critical`) esta'
em `ai_team/config.yaml`. Nada que o Codex devolve entra numa linha de
comando sem passar pela whitelist - valor invalido e' rebaixado para o
default e o desvio fica registrado.

---

## 5. Estados finais

| Status | Significa | O que fazer |
|---|---|---|
| `READY_FOR_HUMAN_REVIEW` | Tarefa completa **e** gate verde. PR aberta. | Revisar e mesclar (o merge e' sempre humano). |
| `NEEDS_HUMAN` | Decisao de arquitetura, mudanca de requisito, gate sem solucao aprovada, ou discordancia teimosa. | Ler `human_question` no resumo e decidir. |
| `NEEDS_REVIT` | Precisa de medicao num Revit vivo / MCP local. | Ler `revit_capture_request`: diz exatamente o que capturar. O estado fica preservado. |
| `FAILED` | Regressao real ou gate HARD vermelho no fim. **DO_NOT_MERGE.** | Ver o gate no resumo. |
| `MAX_ROUNDS` | Acabaram as rodadas sem aprovacao. | Aumentar `max_rounds` ou fatiar a tarefa. |
| `TIMEOUT` | Estourou o relogio. | Reduzir escopo. |

---

## 6. O gate deterministico vence as IAs

```
Claude = executor      (opiniao)
Codex  = revisor       (opiniao)
GATE   = juiz tecnico  (FATO)  <- vence os dois
```

Se `pytest` estiver vermelho, ou uma metrica regredir contra a baseline
(`ai_team/baselines/`), o resultado e' `FAILED` / `DO_NOT_MERGE` -
mesmo com o Claude dizendo OK e o Codex dizendo `APPROVED`. Um gate HARD
vermelho **nunca** termina como `READY_FOR_HUMAN_REVIEW`.

Com rodadas sobrando, um gate vermelho rebaixa `APPROVED` para
`CONTINUE`: o Claude ganha a chance de consertar, e o Codex passa a
revisar com raciocinio mais alto.

---

## 7. Seguranca

- **Claude e' o unico agente escritor.** O Codex roda em `-s read-only`,
  imposto pelo sandbox dele, nao por instrucao no prompt.
- Um hook `PreToolUse` (`ai_team/guard/`) **bloqueia**, na fronteira da
  ferramenta: `git reset --hard`, `git clean -f`, force push, qualquer
  `git push` (quem empurra e' o orquestrador), apagar `main`, `merge`,
  `rebase`, `gh pr merge`, alterar secrets, `rm -rf /` e leitura de
  chave de API. O agente tambem nao consegue editar a propria politica.
- O workflow confere que `origin/main` **nao se moveu** durante a run.
- **Nunca ha' merge automatico em `main`.** O teto do sistema e'
  `READY_FOR_HUMAN_REVIEW`. Ligar `allow_merge_to_main` na config e' um
  erro de configuracao, recusado na carga.

---

## 8. Onde ficam os resultados

- **Resumo:** na propria pagina da run (step summary), com a tabela de
  rodadas, modelo, raciocinio e o motivo de cada escolha.
- **Estado completo:** artifact `ai-team-run-<id>`, com
  `task.json`, `state.json`, `claude_round_NNN.json`,
  `gate_round_NNN.json`, `codex_round_NNN.json` e `final_result.json`.
- **Codigo:** na branch `ai/<slug>`, e a PR quando o status for
  `READY_FOR_HUMAN_REVIEW`.

Nada disso e' versionado: `.ai-team/runs/` esta' no `.gitignore`, para o
log nao poluir o repositorio.

---

## 9. Custo

Controlado por `ai_team/config.yaml`: `max_rounds` (+ teto),
`timeout_minutes`, `max_claude_calls`, `max_codex_calls` e
`max_budget_usd_per_claude_call` (flag real `--max-budget-usd`).

Cada rodada registra modelo, raciocinio, motivo da escolha, duracao e -
para o Claude - o custo real (`total_cost_usd` e `usage`, vindos do
proprio CLI). O `codex exec` nao expoe custo por run; registramos
duracao, modelo e effort.

---

## 10. Rodar localmente

```bash
python3 -m pip install pytest
python3 -m pytest tests/aiteam/ -q          # suite do orquestrador
python3 -m ai_team --task "..." --mode selftest --no-branch \
    --gate-command '["python3","-m","pytest","tests/aiteam/test_routing.py","-q"]'
```
