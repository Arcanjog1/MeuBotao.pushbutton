# Contexto para agentes — manifesto, pacote por tarefa e avaliação de recuperação

STATUS: NAVEGAÇÃO DERIVADA / NÃO É NORMA. A autoridade de domínio continua em
[REGRAS_MODULACAO_BLOCOS.md](../../nuvem/REGRAS_MODULACAO_BLOCOS.md); o estado
corrente continua em [PROJECT_STATUS.md](../PROJECT_STATUS.md); o processo em
[DEVELOPMENT_PROCESS.md](../DEVELOPMENT_PROCESS.md). Nada aqui aprova regra,
benchmark, solver ou merge.

Primeira fatia (F0/F1) do protocolo de memória técnica: organizar e tornar
verificável o conhecimento que já existe, sem alterar solver, imports,
baselines ou RVTs. Memória estruturada, experimentos e influência em produção
são etapas posteriores, que exigem autorização própria.

## Arquivos

| Arquivo | Papel |
|---|---|
| [CONTEXT_MANIFEST.json](CONTEXT_MANIFEST.json) | Catálogo único: fontes (papel, autoridade, status, carga), domínios (aliases pt-BR/EN, seções obrigatórias das REGRAS, código, testes, checks) e espelhos de skills. |
| [SOURCE_INVENTORY.md](SOURCE_INVENTORY.md) | Inventário legível, **gerado** do manifesto (`inventory --write`); não editar à mão. |
| [RETRIEVAL_EVALS.json](RETRIEVAL_EVALS.json) | Perguntas com resposta esperada; executadas por `test_context_pack.py` contra o checkout real. |
| [context_pack.py](../../tools/documentation/context_pack.py) | Ferramenta (somente leitura nas fontes). |

## Comandos (implementados e testados)

```bash
# recibo de sessão: HEAD, main, status, último checkpoint, dívida, próximo passo, inconsistências
python3 tools/documentation/context_pack.py state
# pacote para uma tarefa (domínios detectados por aliases, ou --domain explícito)
python3 tools/documentation/context_pack.py pack --task "canaleta pode servir de amarração?"
python3 tools/documentation/context_pack.py pack --task "..." --domain amarracao --budget 6000 --format json --output .cache/agent_context/TAREFA.json
# conferir se um pacote salvo ainda corresponde ao checkout (SHA, hashes de fontes e seções)
python3 tools/documentation/context_pack.py verify .cache/agent_context/TAREFA.json
# integridade do manifesto (também roda dentro de validate.py e, portanto, no CI)
python3 tools/documentation/context_pack.py check
python3 tools/documentation/context_pack.py inventory --check
python3 tools/documentation/context_pack.py domains
```

Opções globais vêm antes do subcomando (`context_pack.py --root <repo> state`).
No Windows, trocar `python3` por `py -3`. `--output` nunca sobrescreve;
`.cache/` é ignorado pelo Git (pacote é derivado e reconstruível).

## Contratos

- **Cobertura das regras duras.** Todo heading das REGRAS rotulado
  "REGRA OBRIGATÓRIA" ou "REGRA DO USUÁRIO" precisa estar num domínio
  (obrigatória ou relacionada) ou em `unmapped_rules` com motivo; regra nova
  sem mapeamento quebra `check`/`validate.py`.
- **Regras obrigatórias por caminho determinístico.** Cada domínio lista
  seções por número + trecho do heading. A resolução exige correspondência
  única; número repetido no arquivo (ex.: `66.3`, `66.4`) recebe sufixo de
  ocorrência (`66.3@2`) e precisa de `heading_contains`. Heading renomeado
  quebra `check`/`validate.py` com mensagem explícita, em vez de sumir.
- **Nunca truncar obrigatório.** O orçamento (padrão 6000 tokens, estimativa
  `chars/4`) só limita as relacionadas achadas por ranking de aliases; as
  relacionadas curadas no manifesto sempre saem (como ponteiros) e todas as
  candidatas fora da meta são listadas. Se o obrigatório excede a meta, o
  pacote marca `mandatory_over_budget` e `expansion_reason`. Cada seção traz
  os rótulos do heading (`labels`: CONFLITO, PENDENTE, DESLIGADO...).
- **Busca não prova ausência.** Termos sem resultado aparecem em
  `zero_hit_terms`; tarefa sem domínio reconhecido vira
  `INSUFFICIENT_CONTEXT` com os domínios disponíveis.
- **Identidade citável.** Cada seção sai com `rule_id`, linhas, `sha256` do
  texto (LF) e `source_commit`; `verify` acusa pacote velho.
- **Estado por fonte corrente.** Último checkpoint = link da linha
  "Último checkpoint" do status, conferido contra o checkpoint `current` de
  data mais recente. PRs oficiais/candidatos vêm do JSON do status. `verify`
  também acusa pacote gerado com outra `origin/main` ou antes de uma
  inconsistência nova.
- **Texto é dado.** O texto da tarefa e das fontes não amplia escopo:
  `--allow production|revit_write|merge` exige `--authorization-ref`
  (onde o usuário autorizou). Com `--include-text`, as seções saem
  delimitadas como DADOS.
- **Determinismo.** Sem timestamp no pacote; mesma árvore → mesmo JSON.
- **Memória de casos (F2) explícita.** `memory.status = NOT_AVAILABLE_F2`:
  `related_cases`, `counterexamples` e `rejected_experiments` vazios não
  significam ausência.
- **Espelhos de skills.** Diferenças `.claude/skills` × `.agents/skills` são
  declaradas como substituições exatas; qualquer outra deriva quebra o `check`.

## Checagens de consistência

`state`/`pack` relatam (e `validate.py` bloqueia os dois primeiros):

| id | severidade | significado |
|---|---|---|
| `START_HERE_PR_STATE` | ERROR | START_HERE cita número de PR (`#N` ou `PR#N`) fora do "Histórico", em qualquer redação (a mensagem diz se o status o lista como oficial ou candidato). Contrato final após seis rodadas de revisão: detectar "estado" em prosa não convergia (negação, pontuação, tabelas, quebra de linha), proibir o número converge. Não contam como PR: `#N` qualificado por "regra(s)/seção/item/passo/etapa/fiada(s)" (inclusive "regras #1 e #2"), âncoras de link e código inline |
| `START_HERE_CHECKPOINT_LINK` | ERROR | START_HERE aponta checkpoint específico fora de uma seção cujo título começa com "Histórico" (a isenção vale até o próximo heading de nível igual ou maior; blocos de código são ignorados) |
| `STATUS_MAIN_BEHIND` / `STATUS_MAIN_DIVERGED` | WARN / ERROR | main observada no status ≠ `origin/main` buscada |
| `CHECKPOINT_NEWER_THAN_STATUS` | WARN | existe checkpoint `current` mais novo que o declarado no status: data maior, ou mesma data com `head` avaliado estritamente descendente do `head` declarado (imune a renomear/copiar/restaurar arquivos). Limite: checkpoint do mesmo dia com o mesmo `head` (entrega só documental) não é detectado |
| `STATUS_NO_LAST_CHECKPOINT`, `LAST_CHECKPOINT_UNREADABLE` | ERROR | status sem checkpoint resolvível |
| `MAIN_UNKNOWN` | WARN | `origin/main` indisponível (rodar `git fetch origin main`) |

São checagens estruturais: detectam os padrões catalogados, não provam que o
texto está semanticamente correto.

## Manutenção

Ao criar/renomear fonte, domínio ou seção obrigatória: editar o manifesto,
rodar `inventory --write`, `check` e
`python3 -m unittest discover -s tools/documentation -p 'test_*.py'`.
Adicionar pergunta a `RETRIEVAL_EVALS.json` quando um erro de recuperação
for encontrado (erro de recuperação corrigido vira caso permanente).

## Fora desta fatia (propostas, não implementadas)

Registros estruturados de casos/experiências, importação idempotente com
linhagem, índice SQLite derivado, registro de experimentos e gates
diferenciais, evolução de `nuvem/benchmark/patterns.py`, modo sombra e
qualquer influência da memória no solver. Ver o protocolo de 2026-09-24
citado no checkpoint desta entrega.
