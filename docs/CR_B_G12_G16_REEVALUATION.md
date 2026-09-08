# CR-B — REAVALIAÇÃO DE G12 E G16 E CONTRATO DE INTEGRAÇÃO

| item | valor |
|---|---|
| base | `main` real **`91258dd`** (conferida por `fetch`; **não** presumida do SHA histórico) |
| projeção | `91258dd` + `wall_stepper.py` da **CR-S1** + `validate_wall_coverage.py` da **CR-C1**, em worktree isolado |
| candidato | reproduzido do gerador determinístico (`5640933`) |
| identidade | **coordenada global** `(x, y, z)`. `W0xx` nunca usado |
| escrita oficial | **nenhuma**. Nenhum merge. Nenhum arquivo de `nuvem/benchmark/projects/**` tocado |

> A projeção é uma **cópia isolada** montada por `git checkout <branch> --
> <arquivo>` num worktree. **Nenhuma branch foi mesclada na `main`** e
> nenhuma branch de CR foi alterada.

---

## 1. G12 — `PRISM_CONTINUOUS_JOINT`, identidades novas

### 1.1 O G12 é medido na saída do SOLVER, não no gabarito

Registro porque me custou uma medição errada: medido **sobre o gabarito**,
o `PRISM_CONTINUOUS_JOINT` do candidato tem **0 identidades novas** por
coordenada global (saldo 0, novas 0, sumiram 0) — o gabarito não passa
pelo solver. O G12 do relatório G1–G23 mede o delta `IN_R → IN_C` na
**saída do solver de produção**. É essa a grandeza abaixo.

### 1.2 Resultado

Solver de produção rodado sobre `input_roundtrip.json` e
`input_candidate.json`, achados casados por **coordenada global da junta +
cotas das duas fiadas** (`g12.py`):

| projeto | árvore | R | C | saldo | **identidades NOVAS** | sumiram |
|---|---|---|---|---|---|---|
| TGD | `91258dd` (**sem** S1) | 314 | 272 | −42 | **28** | 70 |
| TGD | **com S1+C1** | 298 | 240 | −58 | **12** | 70 |
| TP1 | `91258dd` (**sem** S1) | 286 | 244 | −42 | **28** | 70 |
| TP1 | **com S1+C1** | 286 | 228 | −58 | **12** | 70 |

- As **28 identidades novas sem a S1 reproduzem exatamente** o valor
  declarado pela reconciliação da CR-B — confirmação independente.
- **O saldo `−42` esconde o gate.** Só a contagem por identidade física
  revela as 28 juntas contínuas críticas novas.

### 1.3 Veredito do G12

> ### G12 — **CONTINUA NÃO APROVADO**, mesmo com a CR-S1
>
> A CR-S1 reduz as identidades novas de **28 → 12** nos dois projetos —
> uma melhora real de **57%** — mas **não zera**. Restam **12 identidades
> físicas novas de `PRISM_CONTINUOUS_JOINT`, severidade crítica**, em
> ambos os projetos.

Isto **corrige uma expectativa** da preparação da CR-B, que registrava o
G12 como pendente de reavaliação *"com a S1 aplicada"* na hipótese de que
a S1 o resolveria. Reavaliado: **não resolve**. O gate exige decisão
explícita do usuário ou uma CR adicional. Não a iniciei.

Trade-off da S1, declarado e não escondido: `PRISM_STAGGER_BELOW_TARGET`
(minor) sobe de `+105 → +121` (TGD) e `+101 → +117` (TP1). É a troca
crítico→minor que a própria S1 anuncia.

## 2. G13 — a CR-S1 resolve

| projeto | `JUNCTION_NOT_ALTERNATING` sem S1 | com S1 |
|---|---|---|
| TGD | R=16 → C=32 (**+16**) | **delta 0** |
| TP1 | R=0 → C=16 (**+16**) | **delta 0** |

> **G13 resolvido pela CR-S1**, confirmado independentemente nos dois
> projetos. Continua dependendo do **merge autorizado** da S1 — um PR
> draft não é um gate aprovado.

## 3. G16 — `COVERAGE_*`

| componente | sem C1 | **com C1** | quem resolve |
|---|---|---|---|
| `COVERAGE_MISSING_ROW` | **+17** | **+0** | **CR-C1** |
| `COVERAGE_ROW_MOSTLY_EMPTY` | **+23** | **+23** | **CR-C2 — não implementada** |
| `COVERAGE_GAP_IN_ROW` | −47 | −47 | CR-B (melhora) |

> ### G16 — **CONTINUA NÃO APROVADO**
>
> Metade resolvida pela CR-C1. A outra metade está diagnosticada em
> `docs/CR_C2_ROW_MOSTLY_EMPTY_WALL_SPLIT.md`: os `+23` são **100% mudança
> de unidade de avaliação** (na unidade física original o candidato dá
> **−3**, não `+23`), sobre um defeito de validador **pré-existente**
> (faixa de verga contada como fiada). Corrigir **exige decisão
> normativa** — por isso a CR-C2 entrega diagnóstico, não patch.

## 4. Deltas completos por identidade física — todos os hard gates

Delta `STATE_R → STATE_C` no **gabarito**, na projeção S1+C1
(`gates.py`, `ident2.py`, `junc2.py`). Idêntico nos dois projetos salvo
onde indicado.

| código | severidade | saldo | **identidades novas (coord. global)** | classe |
|---|---|---|---|---|
| `PRISM_CONTINUOUS_JOINT` | crítica | **+0** | **0** | — |
| `PRISM_JOINT_STACK` | crítica | +0 | 0 | — |
| `PRISM_STAGGER_BELOW_TARGET` | minor | +0 | 0 | — |
| `JUNCTION_MISSING_BINDING` | crítica | **+10** | **10**, todas em **nó que só existe em C** | **C** — unidade |
| `JUNCTION_NOT_ALTERNATING` | crítica | +0 | 0 | — |
| `JUNCTION_HALF_BLOCK_ADJACENT` | — | +0 | 0 | — |
| `COVERAGE_ROW_MOSTLY_EMPTY` | crítica | **+23** | 38 novas / 15 sumiram | **C** — unidade (CR-C2) |
| `COVERAGE_MISSING_ROW` | crítica | **+0** | 0 | **A** — resolvido pela C1 |
| `COVERAGE_GAP_IN_ROW` | — | **−47** | — | **A** — melhora |
| `COVERAGE_PARTIAL_WALL` | — | +0 | 0 | — |
| `COMPENSATOR_*` (3 códigos) | — | +0 | 0 | — |
| `OPENING_MISSING_LINTEL` | — | **−12** | 2 novas / 14 sumiram | melhora |
| `OPENING_MISSING_COUNTER_LINTEL` | — | +0 | 0 | — |
| `POSITION_OVERLAP` | crítica | +0 | 0 | — |

### 4.1 `JUNCTION_MISSING_BINDING` — cuidado com a chave

Este delta ilustra por que a escolha de identidade decide o resultado:

| chave usada | identidades novas | em nó **pré-existente** |
|---|---|---|
| `(ponto, elevação, **tipo do nó**)` | 26 | TGD 0 / **TP1 16** |
| `(ponto, elevação)` — **a correta** | **10** | **0 nos dois projetos** |

Os 16 "pré-existentes" do TP1 são o **mesmo nó, na mesma cota, com o mesmo
defeito**, cujo **tipo mudou de `T` para `L`** porque a parede foi
dividida (12 pontos com troca T→L medidos). Incluir o tipo do nó na
identidade transforma re-rotulação em regressão fantasma.

> Com a chave correta: **10 identidades novas, 0 sumiram, todas em nós que
> só existem em `STATE_C`. Nenhum nó pré-existente piorou** — confirma
> independentemente o que a reconciliação da CR-B já afirmava.

O mesmo cuidado vale para `PRISM_CONTINUOUS_JOINT` **no gabarito**: pela
chave "eixo da parede" aparecem **49 identidades novas**; por coordenada
global, **0**. A divisão muda o eixo sem mover a junta.

## 5. Atribuição — sem transferir ganho entre CRs

| CR | o que corrige | evidência desta sessão |
|---|---|---|
| **CR-A** (mesclada) | envelope → consenso | fora do escopo; isolada pelo uso de `STATE_R` como controle |
| **CR-V1** (mesclada, `91258dd`) | encontros por elevação física | base de toda medição aqui |
| **CR-S1** (PR #25, draft) | alternância real em nó `L` de ponta | **G13 +16 → 0**; G12 **28 → 12 novas** |
| **CR-C1** (PR #26, draft) | `expected_rows` físico | **`MISSING_ROW` +17 → +0**; delta zero nos demais |
| **CR-C2** (esta sessão) | associação/avaliação de fiadas | diagnóstico: `+23` = unidade; **sem patch** |
| **CR-B** | reconstrução do gabarito | −14.409cm de vazio físico; `GAP_IN_ROW` −47; `OPENING_MISSING_LINTEL` −12 |

Nenhum ganho de uma foi atribuído a outra.

---

## 6. Contrato de integração da CR-B — conferido

Tudo abaixo foi **medido por mim** (`g18.py`), não lido do relatório.

| item | estado | medição |
|---|---|---|
| **G18** — `stable_key` sem ambiguidade | ✔ | TGD 97/97, 116/116; TP1 96/96, 115/115 chaves distintas. **0 chaves ambíguas** nos 3 estados |
| tabela de migração | ✔ | `cr_b_identity_migration/identity_migration.json`, `chaves_ambiguas: []` nas 3 direções, para os 2 projetos |
| **round-trip** `STATE_A → STATE_R` | ✔ | **0 blocos perdidos, 0 novos** (12.508 e 12.703) |
| **blocos humanos** `R → C` | ✔ | **0 perdidos, 0 novos, 0 duplicados** |
| aberturas medidas preservadas | ✔ | 19 removidas, **0 com `source_element_id`**, 0 com geometria alterada |
| **`input.json` do TGD intocado** | ✔ | 167 paredes, **82 aberturas `measured`, todas com `source_element_id`**. Fonte medida independente, não regravada |
| **TP1 com proveniência reconstruída** | ✔ | 96 paredes, **92 aberturas `reconstructed`, 0 com `source_element_id`** |
| arquivos oficiais intocados | ✔ | `git diff --name-only origin/main..<branch> -- nuvem/benchmark/projects/` = **0** nas 3 branches (S1, C1, CR-B prep) |
| `reference_score` separado | ✔ | não regravado; **dívida aberta** |
| baseline refresh separado | ✔ | não regravado; **dívida aberta** |
| versionamento antigo/novo | parcial | `split_reason` existe; **`needs_revit_check` não** (G19) |

### 6.1 Estado real dos gates G1–G23

| gate | estado | mudou nesta sessão? |
|---|---|---|
| G1–G5, G8, G9, G15, G17, G22 | ✔ | não |
| G6, G7, G10 | ✔ | não reexecutados (insumos byte-idênticos) |
| G11 | ✔ | depende da V1, **mesclada** |
| **G12** | ✘ | **sim — reavaliado**: 28 → **12** novas com S1. **Não aprovado** |
| **G13** | ✘ → **resolvido pela S1** | **sim — confirmado** `+16 → 0` nos 2 projetos. Aprovação depende do **merge autorizado** da S1 |
| G14 | não medido | não; `input.json` do TGD não foi regenerado nem tocado |
| **G16** | ✘ | **sim — metade** (`MISSING_ROW`) resolvida pela C1. **Não aprovado** |
| **G18** | ✘ | conferido como artefato ✔; **gravar no oficial depende do usuário** |
| G19 | parcial | não |
| G20 | ✘ | não |
| G21 | — | bloqueado por G1–G16 |
| G23 | n/a | nenhum arquivo de produção tocado nesta branch |

**Nenhum gate foi promovido a aprovado nesta sessão.**

### 6.2 O que não foi feito, de propósito

- Não regravei `reference.json`, `input.json`, `reference_score.json` nem
  `baseline.json`.
- Não promovi a heurística estrutural dos 19 casos a regra geral.
- Não decidi **D1–D5**.
- Não iniciei C02/C10/Junction/ARM nem qualquer CR fora deste escopo.
- Nenhuma medição no Revit ao vivo (MCP) nesta sessão.
