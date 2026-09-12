# Estado Git/GitHub reconciliado em 2026-09-12

Observado por `git fetch origin` e pela API do GitHub (`list_commits`,
`list_pull_requests`, `pull_request_read`) durante a missão de saneamento
pré-Beta 2. Registro datado; fazer fetch antes de retomar. Substitui a
leitura de [2026-09-10](GITHUB_STATE_2026-09-10.md) onde os dois divergem —
aquele arquivo fica como histórico.

## Main

| Item | Valor |
|---|---|
| `origin/main` | `643966994a2552df31e43451b3cb4137a1d3dc59` — merge do **#37** (`claude/revit-scale-autofix`), 2026-09-11T18:09:03Z |
| Antes | `21576ee` (#36), `6c00f7e` (#35), `59c0352` (#33), `aa58d70` (#32) |
| Contém | toda a cadeia do **Beta 1** (`712f221`, `a5081d8`, `41086e4` são ancestrais da main) e a missão `claude/revit-scale-autofix` (`91cc738`, `cf325f2`, `ee34c2a`, `7239946`, `cd4a261`, `af184ee`, `198a639`, `c3eb0a1`, `24a443e`) |

Consequência para os documentos anteriores: as frases "Beta 1 não
mesclado", "não mesclar Beta 1/#31/#34/produção antiga" e "solver oficial =
produção igual à main inicial" **deixaram de valer para o Beta 1, para o #34 e para a
scale-autofix** — os três estão na main desde o #37 (o #34 pela cadeia do Beta 1; ver a correção na tabela abaixo). O gate "uma execução real
no Revit com o pacote" foi cumprido na própria missão scale-autofix (teste
real do botão CPython, 8.399 blocos, `7bb176b`), mas o **PASS Revit do
Beta** continua sendo decisão do usuário, não deste registro.

## PRs

| PR | Estado GitHub | HEAD | Na main? | Observação |
|---|---|---|---|---|
| [#37](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/37) | merged 2026-09-11T18:09:04Z | `24a443e` | **sim** (`6439669`) | scale-autofix + decisões A/B/C + teste real do botão |
| [#34](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/34) | merged 2026-09-11T18:09:05Z (`merged_by` Arcanjog1) | `8a93a27` (código `8cdd33f`) | **sim** — via cadeia do Beta 1 (`8a93a27` → `0ffa8e9` … `41086e4` → `2599355` → #37 `6439669`) | API e Git coerentes: o GitHub marcou o #34 como mesclado um segundo depois do #37 porque o #37 trouxe os commits do #34 para a main. **Correção (revisão do #38, 2026-09-12):** a leitura original desta linha dizia "NÃO ancestral / inconsistência a esclarecer"; ela foi feita num clone raso (`git rev-parse --is-shallow-repository` = true, só 252 commits alcançáveis a partir da main) e `git merge-base --is-ancestor` respondia errado. Após `git fetch --unshallow` (262 commits), `8a93a27` e `8cdd33f` são ancestrais de `6439669`. O CI do #38 (`validate.py`: "candidate already integrated") acusou exatamente isso. |
| [#36](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/36) | merged | `b5ea0eb` | sim (`21576ee`) | consolidação documental |
| [#35](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35) / [#33](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/33) / [#32](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/32) | merged | — | sim | referências humanas / governança |
| [#31](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/31) | open, draft | `5658e9c` | não | NO-GO físico (inalterado desde 2026-09-09) |
| [#30](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/30) | open, draft | `626087b` | não | superseded por #31 |
| [#28](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/28) | open, draft | `0596e78` | não | migração de identidade (débito registrado na régua V2, ver `nuvem/benchmark/projects/*/v2/manifest.json`) |
| [#21](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/21), [#8](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/8), [#7](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/7) | open, draft | — | não | históricos / superseded (classificação de 2026-09-10 mantida) |

## Branch desta missão

`claude/nifty-lovelace-d3ewpi` (nome designado pela sessão; o usuário
sugeriu `claude/pre-beta2-critical-sanitization` — mesmo conteúdo), derivada
de `6439669`. Sem merge; PR [#38](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/38) aberto para revisão (ver checkpoint
[2026-09-12](checkpoints/2026-09-12-pre-beta2-critical-sanitization.md)).

## CI

Único workflow: `check-project-status.yml` (validação documental). Nenhum
`pytest`/`runner --check` no CI — recomendação em
[CI_RECOMMENDATION_2026-09-12.md](CI_RECOMMENDATION_2026-09-12.md).

## Atualização após a revisão do #38 (2026-09-12, mesma data)

| Item | Valor |
|---|---|
| `origin/main` | `ad46c61372ba0292d117e14ba605375af7acd807` — merge normal do **#38** (`claude/nifty-lovelace-d3ewpi`, head `609a8b3`), pais `6439669` + `609a8b3`; sem rebase, sem force-push |
| #38 | merged; CI `check-status-doc` verde no head `609a8b3` (o head anterior `d7dbb94` falhava por "candidate already integrated: 8a93a27" — ver a correção do #34 acima) |
| Revisão | [checkpoint](checkpoints/2026-09-12-pr38-review-merge.md) |
