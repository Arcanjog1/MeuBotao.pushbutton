# PR #20 — PRONTIDÃO DE INTEGRAÇÃO (gate pré-merge)

> **ESTADO: `PRE_MERGE_READY_WITH_PENDING_DECISIONS`.**
>
> **NÃO MERGEAR.** Não existe, neste ciclo, autorização explícita do
> usuário nem para aceitar os trade-offs C1/C2 nem para o merge. A
> recomendação técnica de um assistente **não é** aceitação do usuário.
>
> Diff de produção desta branch diagnóstica: **ZERO**.

---

## 1. Identidade canônica — conferida antes de qualquer escrita

| item | esperado | medido (`git fetch origin`) | status |
|---|---|---|---|
| `origin/main` | `3ebcd9b63875f9114a3d6223aa648e5075e2d35b` | idem | **CONFERE** |
| HEAD do PR #20 | `dde0261ea87f5680155b9303fddedb95106fd447` | idem | **CONFERE** |
| commit anterior (hard blocker) | `03e6817a3dc89d3b8eb93b5d8eff31b287eac03a` | ancestral de `dde0261` | **CONFERE** |
| branch da revisão independente | `claude/c04-review-next-cr-prep-wc77d7` | `54caff7781e76be0fe1b8c9e77636d43038dc70b` | **CONFERE** |
| snapshot pós-PR19 | `claude/post-pr19-reference-snapshot-s01rhc` | `97a6e72d0635dea6911e25ed6865d801e6ce401a` | **CONFERE** |
| Atlas de causa-raiz | `claude/block-solver-residual-root-cause-gwcmqa` | `9834b40d745b8209d39bbb3efa235ce64bcbb911` | **CONFERE** |
| revalidação do Atlas | `claude/post-pr19-atlas-revalidation-7jsxxj` | `d8961e246969fbf531371f5e0f0cd0e7d8c0d718` | **CONFERE** |
| PR #20 | open / draft / merged=false | open / draft / merged=false | **CONFERE** |

Sem divergência: a integração pôde prosseguir. Nenhuma branch histórica foi
mesclada; `nuvem/REGRAS_MODULACAO_BLOCOS.md` **não** foi alterado (a seção
35 vigente continua sendo a do PR #19, não a do Atlas).

## 2. Escopo de produção do PR — reauditado

```
git diff --name-only 3ebcd9b dde0261
  docs/BLOCK_FIT_TOLERANCE_C04_IMPLEMENTATION.md      docs
  docs/PROJECT_STATUS.md                              docs
  nuvem/core/engine/modulation_math.py                PRODUÇÃO (autorizado)
  nuvem/core/engine/wall_stepper.py                   PRODUÇÃO (autorizado)
  tests/test_block_fit_tolerance_c04.py               teste
  tests/test_block_fit_tolerance_c04_jamb_guard.py    teste
```

**Exatamente os 2 arquivos de produção autorizados.** Nenhum
`*.json` de benchmark tocado (`baseline` / `reference` / `reference_score` /
`input` **intactos**).

O HEAD remoto do PR continua em `dde0261` — **o código de produção é
byte-idêntico ao auditado pela revisão independente**, verificado por hash
de blob. Por isso a suíte completa de ~40min **não foi reexecutada**: a
evidência independente permanece válida. Foram reexecutados só os testes
focados do C04 (seção 6).

## 3. C04 — resumo técnico (números canônicos preservados)

Três estados distintos, que **não** podem ser confundidos:

| estado | HEAD | o que é |
|---|---|---|
| `STATE_A` | `3ebcd9b` | `main` pós-PR19, **sem** C04 |
| `STATE_B_BLOCKED` | `03e6817` | C04 com fit 0,30cm, **antes** da guarda física |
| `STATE_C` | `dde0261` | C04 **com** a guarda física — o que se propõe mesclar |

Duas tolerâncias separadas, uma por pergunta:

```
PIER_FIT_TOLERANCE_CM          = 0,30cm   "este trecho PODE ser modular?"      (modularidade)
PIER_PHYSICAL_FIT_TOLERANCE_CM = 0,05cm   "onde a peça PODE existir de fato?"  (colocação física)
PIER_LAYOUT_TOLERANCE_CM       = 0,05cm   inalterada
```

### `STATE_A → STATE_C`

| TGD | A | C | | TP1 | A | C |
|---|---|---|---|---|---|---|
| blocks | 10679 | **11731** | | blocks | 18417 | **19572** |
| `COVERAGE_GAP_IN_ROW` | 1959 | **1649** | | `COVERAGE_GAP_IN_ROW` | 327 | **214** |
| `COVERAGE_MISSING_ROW` | 258 | **192** | | `COVERAGE_PARTIAL_WALL` | 6 | **0** |
| `COVERAGE_PARTIAL_WALL` | 61 | **48** | | `COVERAGE_ROW_MOSTLY_EMPTY` | 18 | **0** |
| `OPENING_BLOCK_CROSSES_JAMB` | 108 | **108** | | `OPENING_BLOCK_CROSSES_JAMB` | 168 | **168** |
| críticos | 884 | **872** | | `JUNCTION_MISSING_BINDING` | 9 | **9** |
| | | | | críticos | 469 | **485** |

Piloto: fingerprint e métricas físicas **inalterados**.

Hard blocker da 1ª volta **resolvido por identidade física**, não por
contagem: 41 novas `OPENING_BLOCK_CROSSES_JAMB` no `STATE_B_BLOCKED`
(TGD 36 + TP1 5) → **ZERO** novas no `STATE_C`, e **nenhuma instância
pré-existente removida colateralmente**. `block_id` sequencial **não** foi
usado como identidade (ele renumera quando entra peça na fiada e produziria
12 falsos "novos" no TGD).

> Estes números são a referência da revisão independente, **não** valores a
> forçar. Uma reexecução que divergir deve ser investigada antes de
> classificada.

## 4. Condições C1–C5

| | assunto | estado |
|---|---|---|
| **C1** | regressão de `compensators` no TGD (815 → 1083) | **`PENDING_USER_DECISION`** |
| **C2** | saldo crítico do TP1 (469 → 485) | **`PENDING_USER_DECISION`** |
| **C3** | dívida W087 / guarda overconservative | **DOCUMENTADA** em `docs/PROJECT_STATUS.md` |
| **C4** | dívida de escopo global/local | **DOCUMENTADA** em `docs/PROJECT_STATUS.md` |
| **C5** | baseline / reference / input | **PRESERVADOS** |

### C1 — compensadores do TGD

| | achados da categoria `compensators` |
|---|---|
| `baseline.json` congelado | 950 |
| `STATE_A` (`main` de hoje) | **815** — o teste **passa** |
| `STATE_C` | **1083** — o teste **falha** |

O teste `tests/regression/test_benchmark_baselines.py` passa em `STATE_A` e
falha em `STATE_C`. Portanto **não é artefato, não é falha pré-existente, e
não pode ser chamado de "suíte verde"**. Grande parte da piora aparece em
regiões antes vazias, agora preenchidas — mas o solver ainda usa composição
pior que a humana em parte delas (humano `W016` f0: **um B19** em 15–34; o
solver: **C09 + C04**, parando 5cm antes). É dívida real de qualidade de
composição.

**Não pode ser escondida regravando `baseline.json`.**

### C2 — saldo crítico do TP1

`469 → 485` (**+16**), motor `PRISM_CONTINUOUS_JOINT` `256 → 290`
(**+34**). Verificado por instância: **50 de 50** dos prismas novos ocorrem
onde pelo menos uma das duas fiadas **não tinha material nenhum** em
`STATE_A`. Isso explica a causa, **mas não torna os prismas corretos**:
são juntas contínuas físicas reais no resultado final.

`EXPECTED_EXPOSURE` **não** é sinônimo de `ACCEPTABLE` nem de `RESOLVED`.

### C3 — W087 / guarda overconservative

Os **1205** disparos da guarda no corpus, estratificados pelo tipo real de
fronteira:

| fronteira | n | classificação |
|---|---|---|
| jamba de abertura real | **952** | `PHYSICALLY_REQUIRED_GUARD` |
| família `W087` `[85.242, 94.0]` | **138** | `OVERCONSERVATIVE_GUARD` (demonstrado) |
| outras fronteiras de fim de região | **115** | **`INCONCLUSIVE`** — folga física não verificada |

**Não classificar os 1205 como "todos fisicamente necessários".**

Em `W087` a guarda troca um `C09` por um `C04` e deixa sobra; em cinco
fiadas isso vira vazio reportado. O `C09` removido teria **0,758cm de folga
física** até a peça de amarração de `W106` (`T_binding`, mesma fiada): a
reserva de nó é **real e ocupada**, mas a guarda é conservadora demais ali.

**W087 NÃO está resolvido.** Fix futuro proposto e **não implementado**:
expor a folga física real além de `hi` em `region_solid_subsegments`
(ex. `trailing_slack_cm`), a guarda usando
`max(PIER_PHYSICAL_FIT_TOLERANCE_CM, trailing_slack_cm)`; em jamba
`trailing_slack_cm = 0`, então as 952 fronteiras críticas ficam idênticas.
Dependência provável: `nuvem/core/engine/continuous_modulation.py` + um
teste de contrato entre os dois módulos (hoje inexistente).

**Proibido:** aumentar tolerância global, usar folga presumida, criar
exceção por `W087` ou por `wall_id`.

### C4 — escopo global × local

`PIER_FIT_TOLERANCE_CM` alarga um mecanismo de composição **global**
(`_pier_remaining_snapped_cm`); a guarda física está em **um único call
site** (`_solve_repair_subsegments`). Outros call sites de
`_pier_ordered_layout` (l. 4160, 4263, 4290, 4693, 4713) **não** passam
pela guarda.

A revisão **não encontrou escape estrutural novo no corpus atual** — logo
**não é bug comprovado**. Mas ausência de regressão no corpus **não é prova
universal**. Verificação futura exigida: todos os call sites, tipo de
fronteira, juntas de contorno, contrato de `region_solid_subsegments`,
colocação física, reversão de orientação, proteção de abertura, proteção de
reserva de nó. **Não generalizar a guarda nesta integração.**

### C5 — baseline / reference preservados

Nada regravado, nenhum threshold alterado, nenhum teste excluído nem marcado
`xfail`/`skip`. As **2 falhas** da suíte em `STATE_C` são separadas de
propósito:

| falha | classificação |
|---|---|
| TGD, categoria `compensators` | **REGRESSÃO REAL CAUSADA PELO C04** (C1) — passa em A, falha em C |
| TP1, `JUNCTION_MISSING_BINDING` 8→9 | **`REAL_SOLVER_DEFECT` PRÉ-EXISTENTE** — a suíte da `main` sem C04 já falha com mensagem literalmente idêntica |

A primeira **não** pode ser tratada como pré-existente; a segunda **não** é
motivo para culpar o C04.

> Evidência de que o baseline congelado está globalmente obsoleto (anterior
> a PR17/18/19): `PRISM_CONTINUOUS_JOINT` TGD baseline **961** × `main`
> **320**; TP1 **968** × **256**. Regravá-lo agora **esconderia C1** — por
> isso não foi feito.

## 5. Gate pré-merge — resultado item a item

| verificação | resultado |
|---|---|
| `main` canônica | **OK** — `3ebcd9b` |
| HEAD auditado inalterado | **OK** — `dde0261`, blobs de produção idênticos |
| estado do PR | **OK** — open, draft, merged=false |
| escopo de produção | **OK** — exatamente os 2 arquivos |
| documentação | **OK** — C3/C4 registradas (commit docs-only no PR) |
| `baseline`/`reference`/`input`/`reference_score` | **OK** — intactos |
| regras normativas (`REGRAS_MODULACAO_BLOCOS.md`) | **OK** — intocadas |
| 41 `CROSSES_JAMB` novas = ZERO | **OK** — por identidade geométrica |
| demais hard gates por identidade | **OK** — `POSITION_OVERLAP`, `JUNCTION_*`, `OPENING_*`, `COVERAGE_WALL_NOT_MODULATED`: delta ZERO |
| determinismo | **OK** — 9/9 fingerprints estáveis em processos novos; invariância a permutação idêntica entre A e C |
| testes focados | **OK** — reexecutados nesta sessão sobre `dde0261` (seção 6) |
| falhas da suíte completa | **CONHECIDAS** — 2, explicadas em C5. **A suíte NÃO está verde** |
| comentários de revisão pendentes | nenhum comentário de revisão aberto no PR |
| CI do HEAD atual | **verde** — `check-status-doc` `success` (2 execuções) |
| checks obrigatórios | o repositório tem **um** workflow (`check-project-status.yml`), **não bloqueante** por projeto |
| **C1 / C2** | **PENDENTES DE DECISÃO DO USUÁRIO** |

`mergeable_state = clean` no GitHub. **Isso não significa que o usuário
autorizou merge.** Nenhum bypass, `--admin`, force-push, alteração de
proteção de branch ou desativação de CI foi usado — nem seria.

**Bloqueio remanescente:** exclusivamente as decisões humanas C1 e C2. Não
há bloqueio técnico.

## 6. Testes reexecutados nesta sessão

Sobre o HEAD auditado `dde0261`, em worktree isolado:

```
tests/test_block_fit_tolerance_c04.py
tests/test_block_fit_tolerance_c04_jamb_guard.py
nuvem/tests/test_modulation_broken_length.py
```

Resultado: **134 passed** (73 do arquivo da guarda de jamba + 61 dos outros
dois), em 0,55s.

### 6.1 Guard-rail de baseline — reexecutado nos DOIS estados

`tests/regression/test_benchmark_baselines.py` roda o solver nos 3 projetos
e compara contra o `baseline.json` congelado. Executado nesta sessão, em
worktrees separados:

| estado | resultado | falhas |
|---|---|---|
| `STATE_A` (`3ebcd9b`, `main` **sem** C04) | **1 failed, 8 passed** (7min36) | **só** TP1 |
| `STATE_C` (`dde0261`, C04) | **2 failed, 7 passed** (9min15) | TP1 **e** TGD |

A falha do TP1 é, nos dois estados, literalmente a mesma mensagem:

```
AssertionError: REGRESSAO CRITICA em torre_easy_lo_r00_tp1:
  [{'code': 'JUNCTION_MISSING_BINDING', 'before': 8, 'after': 9,
    'delta': 1, 'status': 'REGRESSAO CRITICA'}]
```

**Isto fecha C1 e C5 por execução direta, não por citação:**

- o TGD **passa** em `STATE_A` e **falha** em `STATE_C` ⇒ a regressão de
  `compensators` é **causada pelo C04** (C1) — não é artefato nem
  pré-existente;
- o TP1 **falha nos dois** com a mesma mensagem ⇒
  `JUNCTION_MISSING_BINDING` 8→9 é **pré-existente** (C5), e o C04 não o
  introduz nem o agrava.

**A suíte NÃO está verde, e não deve ser descrita como tal.**

A suíte completa (~40min por estado) **não** foi reexecutada — a produção é byte-idêntica à auditada e
a evidência independente (`STATE_A` 682 passed / 1 failed; `STATE_C` 809
passed / 2 failed) permanece válida.

## 7. Decisões que faltam para integrar o C04

*(explicação sem jargão — as duas únicas coisas que dependem do usuário)*

**C1 — os compensadores do TGD.**
O programa passou a preencher paredes que antes deixava vazias. Em alguns
trechos, porém, ele monta o preenchimento com **compensadores demais**
(pecinhas de acerto) onde o projetista humano usaria **um meio-bloco só**.
O número de avisos dessa categoria subiu de 815 para 1083.

**C2 — a amarração entre fiadas no TP1.**
Algumas paredes do TP1 agora **têm blocos** onde antes não tinha nada. Só
que a **amarração entre uma fiada e a de cima** ainda não ficou boa nesses
trechos novos: aparecem juntas alinhadas na vertical, que a alvenaria
estrutural não aceita. Por isso o total de problemas graves do TP1 subiu de
469 para 485.

Em ambos os casos: **o desenho ficou mais completo, e ao mesmo tempo
apareceu um defeito de qualidade que antes estava escondido porque o trecho
nem era desenhado.**

### As duas opções

| | o que significa | custo |
|---|---|---|
| **OPÇÃO A** — aceitar as dívidas agora e integrar o C04 | fica-se com **+1052 peças no TGD e +1155 no TP1**, e com os defeitos de composição registrados na fila de correção | o TP1 fica com 16 problemas graves a mais até a próxima CR; o teste de baseline continua vermelho de propósito, para não esquecer |
| **OPÇÃO B** — não aceitar e exigir a correção de composição antes | integra-se só quando a composição estiver boa | amplia o escopo do trabalho (vira também S1/S2 — política de composição), exige nova validação completa, e o ganho de cobertura fica parado até lá |

**Nenhuma das duas foi escolhida.** A escolha é do usuário, e precisa ser
explícita — mencionando a aceitação dos trade-offs **e** o merge do PR #20.
Nenhuma regra obrigatória de domínio será alterada para resolver o impasse.

## 8. Documentos relacionados

| documento | onde |
|---|---|
| revisão independente do C04 | `docs/C04_INDEPENDENT_FINAL_REVIEW.md` @ `54caff7` (branch `claude/c04-review-next-cr-prep-wc77d7`) |
| preparação das próximas CRs | `docs/FUTURE_BLOCK_CR_PREPARATION.md` @ `54caff7` |
| prompts das próximas CRs | `docs/FUTURE_BLOCK_CR_PROMPTS.md` @ `54caff7` |
| implementação do C04 | `docs/BLOCK_FIT_TOLERANCE_C04_IMPLEMENTATION.md` @ `dde0261` |
| roadmap consolidado pós-C04 | `docs/POST_C04_ROADMAP.md` (esta branch) |
| evidência da CR de benchmark | `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction/` (esta branch) |
