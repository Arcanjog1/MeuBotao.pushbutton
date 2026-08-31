# AI Team - Claude executor (rodada {round}/{max_rounds})

Continuacao automatica. O revisor (Codex) analisou a rodada anterior e
escreveu a instrucao abaixo. Nenhum humano intervem entre as rodadas.

## Tarefa original

{task}

## Instrucao do revisor para ESTA rodada

{next_prompt}

## Por que o revisor decidiu assim

{routing_reason}

## Resultado do gate deterministico na rodada anterior

{gate_summary}

## Contexto

- Branch: `{branch}` | Base: `{base_branch}` @ `{base_sha}`
- Rodada {round} de {max_rounds}
- Rodadas anteriores: {history}

## Regras obrigatorias

As mesmas da rodada 1, e valem sempre:

1. Uma causa raiz por commit.
2. Commite o que fizer (senao se perde).
3. Nada de `git push` / `merge` / `rebase` / `reset --hard` / `checkout main`.
4. Rode `python3 -m pytest tests/ -q -m "not slow"` antes de dizer `DONE`.
5. Nao mexa no solver/modulacao se a tarefa nao pedir.
6. `NEEDS_REVIT` / `NEEDS_HUMAN` quando for o caso, com o detalhe em `blockers`.

**Se o gate acima estiver vermelho, consertar o gate e' a prioridade
desta rodada** - antes de qualquer trabalho novo.

## Saida

Responda no schema JSON exigido.
