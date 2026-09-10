# CHECKPOINT — INTEGRAÇÃO CONSOLIDADA DOS PRs #27, #25, #26 e #29

> Checkpoint **versionado** da sessão de integração de 2026-09-08.
> Registro append-only: descreve o que foi feito, com que evidência, e o
> que **não** foi feito. Não substitui os relatórios de cada CR.

| item | valor |
|---|---|
| `main` inicial | `91258dd627af97fe437a56c0506eb096ca5aa267` (`PR #24` / CR-V1) |
| `main` final desta integração | `c88a031404459ee4cee0f7c36904b8e7b971a471` (`PR #29` / CR-G12) |
| `main` real ao fechar o checkpoint | `40155643d1fd79664cc262c7b74f4a137db9dec7` — ver §9 |
| PRs integrados | `#27`, `#25`, `#26`, `#29` — nesta ordem |
| PR **não** integrado | `#28` (permanece `draft`, por instrução explícita) |
| autorização | merge dos quatro PRs autorizado explicitamente pelo usuário |
| método de merge | merge normal (`merge commit`), sem squash, sem rebase, sem force-push, sem bypass de proteção |

---

## 1. Estado real conferido antes de integrar

`git fetch origin --prune` em 2026-09-08. Os quatro PRs tinham
`merge-base` **exatamente** em `91258dd` (nenhum estava desatualizado em
relação à base revisada) e todos estavam `draft`.

| PR | CR | HEAD de referência | HEAD real conferido | bate? |
|---|---|---|---|---|
| `#27` | CR-D1 | `b852695` | `b8526954106a3d4ec12711e43a2f109ca3e7c130` | sim |
| `#25` | CR-S1 | `33d035f` | `33d035f84e61dd8162e5f3aeebb0bdd6284e5159` | sim |
| `#26` | CR-C1 | `34bf696` | `34bf6962f25aac12a2844e7b6c3cc5336c6459d6` | sim |
| `#29` | CR-G12 | confirmar, incluindo `a7c7f98` | `73243e980bd93e44ea515e9d21f0a08e6e478942` | sim — a cadeia é `b3dcf0a` → `777960c` → **`a7c7f98`** → `73243e9` |

**Nenhum PR mudou materialmente após a revisão.** Não havia commit
posterior não revisado em nenhuma das quatro branches.

**Checks do GitHub:** o repositório tem um único workflow,
`.github/workflows/check-project-status.yml`, que é um **lembrete
técnico, não um veto** (avisa quando `nuvem/core/engine/**` muda sem
`docs/PROJECT_STATUS.md` no mesmo diff). Nenhum status estava publicado
nos HEADs no momento da conferência (`total_count: 0`); a verificação
real foi feita rodando as suítes localmente, registradas na §4.

---

## 2. Ordem de integração e SHAs

| ordem | PR | CR | HEAD aprovado | HEAD integrado | merge commit |
|---|---|---|---|---|---|
| 1 | `#27` | CR-D1 — recuperação documental | `b852695` | `b852695` | **`7cc935d`** |
| 2 | `#25` | CR-S1 — alternância em L | `33d035f` | `33d035f` | **`32e1c0e`** |
| 3 | `#26` | CR-C1 — `expected_rows` físico | `34bf696` | **`b2daca8`** | **`0c6e8f7`** |
| 4 | `#29` | CR-G12 — juntas entre bandas | `73243e9` | **`9531cf0`** | **`c88a031`** |

`origin/main` foi atualizada e reconferida antes de cada merge seguinte.
Cada merge foi confirmado com `merged: true` e o SHA devolvido pela API.

---

## 3. Conflitos resolvidos

Os únicos conflitos foram **documentais**. **Nenhum arquivo de produção
entrou em conflito** — em particular, `nuvem/core/engine/wall_stepper.py`
fundiu **sem conflito** entre a CR-S1 (gate do canto em L) e a CR-G12
(troca de layout cross-band), exatamente como a revisão independente da
G12 havia medido na fusão a 3 vias.

### 3.1 `#26` / CR-C1 — HEAD de compatibilidade `b2daca8`

Merge de `origin/main` (já com `#27` e `#25`) para dentro da branch da
C1. Conflitos em `docs/PROJECT_STATUS.md` e
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, resolvidos por **união**:

- `PROJECT_STATUS.md` — as entradas de "Trabalho ativo" da C1 e da S1 são
  aditivas e passam a coexistir.
- `REGRAS_MODULACAO_BLOCOS.md` — **não houve colisão de numeração**: a S1
  numerou sua seção como **36** e a C1 como **37**. As duas foram
  preservadas na íntegra e apenas **reordenadas** para a sequência
  `35 → 36 (S1) → 37 (C1)`. **Os dois contratos ficaram preservados**,
  como o enunciado exigia para §36/§37.

Conferência: `git diff 34bf696 b2daca8 -- nuvem/benchmark/` vazio — o
validador da C1 saiu do merge **intacto**.

### 3.2 `#29` / CR-G12 — HEAD de compatibilidade `9531cf0`

Merge de `origin/main` (já com `#27`, `#25` e `#26`) para dentro da
branch da G12. `wall_stepper.py` fundiu sozinho. Conflitos apenas em:

- `REGRAS_MODULACAO_BLOCOS.md` — de novo **sem colisão de numeração**:
  S1 = 36, C1 = 37, C2 (documentação, **decisão pendente**) = 38,
  G12 = 39. As quatro seções preservadas na íntegra, na ordem
  `36 → 37 → 38 → 39`.
- `PROJECT_STATUS.md` — preservada a nota da G12 sobre o SHA
  desatualizado `62ea7f2` e adotada a redação corrente do marco de
  produção (`PR #24` / CR-V1).

Conferência: `git diff 73243e9 9531cf0 -- nuvem/core/ tests/` mostra
**apenas** a entrada do `wall_stepper.py` da S1 e os dois arquivos de
teste novos da S1 e da C1 — nada da G12 foi alterado pela resolução.

### 3.3 Condição C2 da revisão independente da G12 — aplicada

`docs/CR_G12_REVISAO_INDEPENDENTE.md` §7.2/§13 exigia corrigir a §6.3
item 1 de `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md`, que atribuía as
**+31** ocorrências líquidas novas de `PRISM_STAGGER_BELOW_TARGET`
inteiras à troca crítico → nível 2. A correção foi aplicada no commit
`9531cf0`: **17** são essa troca (6 paredes que perderam junta contínua);
as outras **16**, todas em `W074`, são **colaterais da mudança de
aceitação do ARM SAFE REPAIR** — provado pela medição da geração pura,
onde `W074` **não** aparece entre as 11 paredes com blocos diferentes.
**Só texto** — nenhum código, teste, threshold ou baseline tocado.

---

## 4. Testes e gates

Todas as medições em **worktrees isolados**, com `pytest` instalado no
ambiente da sessão.

| # | o que | árvore | resultado |
|---|---|---|---|
| 1 | `tests/test_solver_l_node_alternation_cr_s1.py` | `#25` + `main` | **16 passed** (0,6 s) |
| 2 | `tests/regression/test_validator_coverage_expected_rows_cr_c1.py` + a suíte da S1 | `b2daca8` | **35 passed** (2,2 s) |
| 3 | `tests/test_cross_band_joint_propagation_cr_g12.py` (rápidos) | `9531cf0` | **11 passed, 9 deselected** (0,3 s) |
| 4 | `test_cross_band_joint_propagation_cr_g12.py` (20, com os 9 `slow`) + `test_block_arm_role_candidate_safety_contract.py` (t1/t9) + `test_block_node_fill_revalidation.py` (t20) | `9531cf0` | **66 passed** (25 min 27 s) |
| 5 | `tests/regression/test_benchmark_baselines.py` — **base histórica** | `91258dd` isolado | **2 failed, 7 passed** (6 min 56 s) |
| 6 | **regressão consolidada, suíte inteira** | `c88a031` isolado | **2 failed, 921 passed** (1 h 13 min 20 s) |

### 4.1 Separação exigida pelo enunciado

**Falhas pré-existentes — as mesmas duas, com os mesmíssimos números nas
duas árvores:**

| falha | base `91258dd` | `main` final `c88a031` |
|---|---|---|
| `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]` — categoria `compensators` | `52 → 61` (delta **9**) | `52 → 61` (delta **9**) |
| `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]` — `JUNCTION_MISSING_BINDING` | `8 → 9` | `8 → 9` |

**Falhas novas: NENHUMA.** A contagem sobe de 868 para 923 testes
coletados (**+55** = 16 da S1 + 19 da C1 + 20 da G12) e as duas únicas
falhas continuam sendo as históricas.

**Mudanças legítimas de contrato:** as duas do commit `a7c7f98` da G12
(t1/t9 e t20), que trocam *mecanismo* por *resultado físico* e
**acrescentam** asserções. **Nenhum `skip`, nenhum `xfail`, nenhuma
asserção removida, nenhum threshold alterado.**

**Regressões físicas reais: nenhuma detectada.** Os trade-offs medidos
(`PRISM_STAGGER_BELOW_TARGET`, `COMPENSATOR_*`, desempenho) estão
declarados na §5.

> **Nota de método, registrada por honestidade:** a primeira execução da
> suíte na base foi feita no diretório principal enquanto a `main` local
> era trocada a cada merge, então a árvore mudou embaixo dela. Ela
> devolveu as mesmas duas falhas, mas **não** é a medição citada acima:
> a base foi **remedida em worktree isolado e limpo** (linha 5 da tabela),
> e é essa que vale.

### 4.2 Gates

| gate | estado após a integração |
|---|---|
| **G12** — 12 identidades novas → 0 nos dois projetos | **FECHADO**, com zero junta contínua nova por identidade física |
| **G13** (alternância, preservado pela S1) | **PRESERVADO** — `JUNCTION_NOT_ALTERNATING` 303 → 303 no corpus oficial |
| **G16** | **CONTINUA PENDENTE DA CR-C2** — não destravado, não tentado |
| **G18** | **PRESERVADO** — nenhum código de chave/identidade tocado |
| determinismo | **CONFIRMADO** — toda iteração da semente cross-band é ordenada |
| `COVERAGE_*` / `OPENING_*` / `JUNCTION_*` / `POSITION_*` | **delta zero por identidade** |

O saldo global de `critical_errors` **não** foi usado para esconder
defeito: a verificação da CR-G12 é por **identidade física**, achado a
achado.

---

## 5. Decisões do usuário registradas nesta integração

### 5.1 CR-S1 — alternativa A, aceita

Preservar a amarração correta e **aceitar especificamente os 8 eventos
físicos de compensadores por projeto**, correspondentes a
`+8 COMPENSATOR_CONSECUTIVE` e `+8 COMPENSATOR_EXCESS_IN_RUN`.

Isso **NÃO**:

- cria permissão geral para compensadores consecutivos;
- implementa B19 como amarração;
- altera a seção 35 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`;
- altera qualquer threshold ou regra normativa.

Observação medida: no **corpus oficial da `main`** a categoria
`compensators` do TGD ficou em `52 → 61`, **idêntica à da base** — os 8
eventos aceitos foram medidos sobre a projeção do candidato CR-B, não
sobre o corpus oficial.

### 5.2 CR-C1 — aprovada independentemente, sem patch adicional

A detecção de **ausências reais de fiada** está preservada:
`expected_rows` **não** virou silenciador de cobertura. A CR entrega as
**28 paredes de `h=340` que param em `z=301`** como defeito real do
solver, agora corretamente acusado.

### 5.3 Baselines

`input.json`, `reference.json`, `reference_score.json` e `baseline.json`
**não foram regravados**. Nenhum `--save-baseline`. As duas falhas
históricas continuam registradas como pré-existentes — **não se regravou
baseline para obter verde**.

---

## 6. Trade-offs que ficam documentados (não escondidos)

1. **`PRISM_STAGGER_BELOW_TARGET` +31 no TGD** (nível 2, nunca crítico):
   17 são a troca crítico → nível 2 nas 6 paredes que perderam junta
   contínua; **16 são colaterais do ARM SAFE REPAIR** em `W074` (§3.3).
2. **`COMPENSATOR_EXCESS_IN_RUN` +2 no TGD** no candidato CR-B; no corpus
   oficial esse código **melhora** (−1 TGD, −2 TP1).
3. **Desempenho ~2,1×** na resolução completa do TGD. **95,6% do tempo
   está nos 22 rebuilds do ARM SAFE REPAIR**, que são pré-existentes — a
   alavanca real é estreitá-los com `dirty_wall_idxs`, e isso é **outra
   CR**, não iniciada. Não se exigiu perfeição de benchmark para
   integrar, e nenhuma regressão crítica nova foi escondida.
4. **2 identidades cross-band residuais no TGD** (`W069`, `t=649,5`) —
   confirmadas, não zeradas.
5. **A garantia "zero junta contínua nova" é empírica, não estrutural** —
   a aceitação entre passes usa uma métrica líquida. Travada por teste de
   identidade nos dois projetos reais, não por invariante.

---

## 7. Limites respeitados

- `PR #28` **não integrado** (segue `draft`).
- **C2 não decidida** — a §38 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`
  documenta o problema e registra explicitamente `DECISÃO FÍSICA
  PENDENTE — nenhuma opção adotada`.
- **D1–D5 da CR-B não decididas**; a **CR-B não é declarada oficialmente
  aprovada**.
- Nenhum arquivo oficial regravado (§5.3).
- Nenhuma regra normativa alterada além da aceitação específica da S1.
- **C02, C10, Junction, ARM e outras CRs não iniciadas.**
- **Nenhum teste real no Revit.**
- **Nenhum monitoramento automático criado** — sem check-in, sem
  polling, sem subscrição de PR, sem tarefa recorrente.

---

## 8. Pendências restantes

1. **Varredura ampla do benchmark em dois blocos** — próxima etapa, em
   **sessão nova**, sem exigir perfeição.
2. **G16 pendente da CR-C2**; CR-B **não** oficialmente aprovada.
3. **`PR #28`** continua `draft`.
4. **Refresh de `baseline.json`** — CR própria, não iniciada; as duas
   falhas históricas continuam vermelhas de propósito.
5. **Dívida de desempenho ~2,1×** da CR-G12 (§6.3).
6. **2 identidades cross-band residuais** no TGD.
7. **`prior_course_joints` recebe o ÚLTIMO passe, não o MELHOR** — inócuo
   com 2 passes, vira inconsistência latente se alguém subir para 3+.
8. **Erro no passe 2 descarta um passe 1 válido** — alcançável só se o
   passe 2 falhar e o 1 não; teórico.

---

## 9. Commit posterior na `main` por sessão paralela — `4015564`

Ao reconferir o estado depois da integração, `origin/main` **não** estava
mais em `c88a031`: havia um commit posterior, **`4015564`**
(`docs(status): reconcilia PROJECT_STATUS com a main real apos os merges
#25/#26/#27`), autorado por outra sessão às 18:43 UTC, com **pai
`c88a031`** — ou seja, empilhado corretamente **em cima** desta
integração, sem reescrever nada dela.

| item | verificação |
|---|---|
| escopo | **só `docs/PROJECT_STATUS.md`** (99 inserções, 115 remoções) |
| código / gabarito / `baseline.json` / `reference_score.json` / validador / regra normativa | **nada tocado** |
| relação com esta integração | **aditiva** — os quatro merges e seus SHAs continuam intactos |

**O que ele conserta, e que esta sessão não tinha visto:** o merge da
CR-C1 (cuja branch partia de `91258dd`) **ressuscitou sem conflito** uma
entrada obsoleta da CR-V1 dizendo `PR #24 DRAFT, NAO mesclado`, ao lado
da entrada correta. A página ficou com **duas** CR-V1 contraditórias.
`4015564` removeu a duplicata — é um artefato real de merge, e a correção
está certa.

**O que ele ainda não cobria:** o texto do commit foi escrito contra
`0c6e8f7` (antes do `PR #29`); o conteúdo final já lista os cinco marcos,
mas o "Estado oficial do solver" não tinha entrada para **CR-D1**,
**CR-C1** nem **CR-G12**, não apontava para este checkpoint, não
registrava os HEADs de compatibilidade (`b2daca8`, `9531cf0`) e mantinha
"Alinhamento cross-band" como problema aberto de 33 casos, sem a CR-G12.

**Resolução adotada:** `origin/main` foi mesclada nesta branch e o
conflito em `docs/PROJECT_STATUS.md` foi resolvido **adotando a versão da
`main` como base** (preservando a remoção da CR-V1 duplicata) e
**reaplicando por cima** apenas o que era exclusivo desta sessão. Nenhuma
das duas correções foi perdida e a CR-V1 duplicada **não** voltou
(conferido: uma única ocorrência do título na página).

---

## 10. Estado dos processos de segundo plano ao fechar

Diagnóstico feito às 20:08 UTC, a pedido do usuário.

**Nenhum processo de teste estava ativo** — as quatro suítes já haviam
terminado e seus resultados já estavam colhidos (§4). O que sobrava eram
**5 monitores de espera travados**, todos a **0,0% de CPU**, entre 1 h 31
e 1 h 58 de idade, nenhum avançando log:

| tarefa | idade | padrão do `until ! pgrep -f` |
|---|---|---|
| `bxgisz3w5` | 1 h 58 | `pytest tests/ -q --no-header` |
| `b64akwybr` | 1 h 58 | `cross_band_joint_propagation_cr_g12.py tests` |
| `b2xdci4z8` | 1 h 34 | idem — **duplicata** de `b64akwybr` |
| `br3wvq36l` | 1 h 31 | `test_benchmark_baselines.py -q` |
| `b31ab5jwa` | 1 h 31 | `pytest tests/ -q --no-header` — **duplicata** de `bxgisz3w5` |

**Causa-raiz:** o `pgrep -f` de cada monitor casava com a **própria linha
de comando do monitor**, então a condição de saída nunca podia ser
satisfeita — laço infinito por auto-referência, não teste travado. Os
cinco foram encerrados com `SIGTERM` (processo e `sleep` filho). **Nenhum
log foi perdido** e **nenhum teste foi reexecutado**: os quatro
resultados da §4 vieram dos logs já gravados.

*Lição registrada: um monitor `until ! pgrep -f "<padrão>"` precisa
excluir a si mesmo (por exemplo casando o binário real, `pgrep -f
"python3 -m pytest"`, ou filtrando o próprio PID).*

