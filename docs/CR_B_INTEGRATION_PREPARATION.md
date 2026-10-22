# CR-B — preparação da integração oficial versionada

> **Preparação e diagnóstico. Nada oficial foi tocado.**
> `nuvem/benchmark/projects/**` (`input.json`, `reference.json`,
> `baseline.json`, `reference_score.json`) está intocado — conferido por
> `git status --short`. Nenhuma decisão `D1`–`D6` foi tomada, nenhum gate
> foi declarado aprovado por saldo global, e nenhuma escrita em arquivo
> oficial foi feita.

| item | valor |
|---|---|
| base | `91258dd627af97fe437a56c0506eb096ca5aa267` (`origin/main`) |
| branch | `claude/cr-b-preparacao-identidade` |
| candidato reproduzido de | `claude/candidato-validacao-gabarito-q450yr` (`5640933`), `build_candidate.py` |
| contrato lido | `claude/cr-b-reconciliacao-contrato-1byigr` (`14926fb`), §9 (G1–G23) e §7 (D4/D6) |
| arquivo de produção tocado | **nenhum** |

---

## 1. Candidato reproduzido — invariantes reconferidos

`build_candidate.py` com `CR_B_OUT=/tmp/cr_b_candidate`, fora de
`projects/`. Invariantes que o próprio gerador reporta, reconferidos nesta
sessão para os dois projetos:

| invariante | valor |
|---|---|
| blocos humanos **perdidos** | **0** |
| blocos humanos **novos** | **0** |
| blocos **duplicados** no `STATE_C` | **0** |
| **órfãos** (`STATE_R` / `STATE_C`) | **0 / 0** |
| aberturas **adicionadas** | **0** |
| aberturas com **geometria alterada** | **0** |
| aberturas removidas **com `source_element_id`** | **0** |
| aberturas removidas | **19** (= casos C1) |
| comprimento total | **−2604,0cm** exato |
| blocos que **mudaram de fiada** | 184 |

Blocos humanos preservados: **12.703** (TP1). Nenhum invariante de
preservação foi assumido a partir do relatório anterior — todos saíram da
execução desta sessão.

---

## 2. G18 — tabela de migração de identidade (entregue)

**O que faltava:** o G18 exige `stable_key` gravado por parede **e** a
tabela de migração `W0xx`. Medição anterior: *"53/86 e 52/85 mudam de id,
**não implementado**"*.

**O que já existia e foi confirmado:** o `stable_key` **já é gravado** —
campo `key` em **97/97** paredes do gabarito do TGD (e nas aberturas),
produzido por `model.wall_stable_key` (eixo canônico + espessura, nunca o
`ElementId`). O arquivo também já carrega `schema_version: 2`.

**O que esta preparação acrescenta:**
`nuvem/benchmark/future_cr_preparation/cr_b_identity_migration/build_identity_migration.py`
— gerador determinístico da tabela, por identidade **física**, e o
artefato `identity_migration.json`.

| par de estados | PRESERVADA | MUDOU_DE_ROTULO | SUMIU | NOVA | paredes | chaves ambíguas |
|---|---|---|---|---|---|---|
| TGD `STATE_A → STATE_R` | **97** | 0 | 0 | 0 | 97 → 97 | **0** |
| TGD `STATE_A → STATE_C` | 33 | **53** | 11 | 30 | 97 → 116 | **0** |
| TP1 `STATE_A → STATE_R` | **96** | 0 | 0 | 0 | 96 → 96 | **0** |
| TP1 `STATE_A → STATE_C` | 33 | **52** | 11 | 30 | 96 → 115 | **0** |

Três leituras que o G18 pedia e agora estão medidas:

1. **`53` / `52` reproduz exatamente** o número que a reconciliação
   registrou — confirmação independente do gerador.
2. **O round-trip é perfeito**: `STATE_A → STATE_R` dá **97/97** e
   **96/96 PRESERVADA**, zero mudança de rótulo. Toda a diferença de
   identidade vem do **corte**, nunca da ida e volta pelo extrator.
3. **A aritmética do corte fecha**: `SUMIU = 11` paredes e `NOVA = 30`
   segmentos, com **30 = 11 + 19** (as 19 aberturas removidas partem 11
   eixos), e `97 − 11 + 30 = 116`. Nenhum eixo aparece ou some sem causa.

**Ambiguidade de `stable_key`: ZERO** em todos os pares, nos dois
projetos — a chave geométrica é injetiva neste corpus. O tratamento de
ambiguidade fica implementado no gerador (a chave mapeia para uma
**lista** de rótulos, nunca um escalar, para que uma colisão futura
apareça em vez de sobrescrever em silêncio), mas **não há nenhum caso
hoje**.

> **G18 continua NÃO aprovado**, e de propósito: a tabela existe como
> artefato de preparação e o `stable_key` já é gravado, mas **gravar a
> tabela no gabarito oficial e versionar as métricas por versão (G20) é
> escrita em arquivo oficial** e depende de decisão do usuário.

---

## 3. G16 — resolvido pela metade pela CR-C1, e por que continua reprovado

Medido nesta sessão sobre o candidato (`STATE_R → STATE_C`), nos dois
projetos, com e sem a CR-C1 (branch `claude/cr-c1-expected-rows-fisico`):

| componente do G16 | sem C1 | com C1 |
|---|---|---|
| `COVERAGE_MISSING_ROW` | **+17** | **+0** |
| `COVERAGE_ROW_MOSTLY_EMPTY` | **+23** | **+23** |

Os `+17` / `+23` **reproduzem exatamente** o G16 da reconciliação.

`COVERAGE_ROW_MOSTLY_EMPTY` **não lê** `expected_rows` — compara as fiadas
de uma parede entre si. O resíduo (TGD: 38 novos − 15 que sumiram) são
fiadas cobrindo 6–30% do trecho modulável numa parede cuja melhor fiada
cobre 100%; **34 dos 38 em paredes sem abertura nenhuma**, concentrados em
paredes de 169cm. Classe **D/E**: consequência da própria divisão de
paredes (184 blocos mudaram de fiada).

> **G16 continua NÃO aprovado.** Metade de um gate composto não aprova o
> gate, e o componente resolvido **não compensa** o outro. Proposta:
> **CR-C2 — cobertura por segmento após divisão de parede**. Não
> implementada.

---

## 4. Estado dos gates, reconciliado com V1 / S1 / C1

`CR-V1` está **mesclada** (`PR #24`, `91258dd`). `CR-S1` (`PR #25`) e
`CR-C1` são **PR draft, não mescladas** — e um PR draft **não** é um gate
aprovado.

| gate | estado hoje | reconciliação com V1/S1/C1 |
|---|---|---|
| G1–G5, G8, G9, G15, G22 | ✔ | reconferidos nesta sessão pelo gerador |
| G6, G7, G10 | ✔ | identidade física; não reexecutados aqui (evidência anterior suficiente, insumos idênticos) |
| G11 | ✔ | depende da **V1**, que está **mesclada** |
| **G12** (`PRISM_CONTINUOUS_JOINT`, 28 identidades novas) | ✘ | a **S1** age exatamente aqui: mede `PRISM_CONTINUOUS_JOINT` −32/−16 virando `PRISM_STAGGER_BELOW_TARGET` (minor). **Não reavaliado** com a S1 aplicada — exige a matriz `candidato + S1`, e a S1 não está mesclada |
| **G13** (`JUNCTION_NOT_ALTERNATING`, 1 nó novo) | ✘ → **resolvido pela S1, ainda não homologado** | a S1 leva esse nó de `32→0` (TGD) e `16→0` (TP1). O gate só pode ser dado como aprovado **depois** do merge autorizado da S1 |
| G14 (`input.json` do TGD byte-idêntico) | não medido | nada foi gravado; **o `input.json` do TGD não foi regenerado nem tocado** |
| **G16** | ✘ | **metade** resolvida pela C1 (§3). Continua reprovado |
| **G18** | ✘ | tabela entregue como artefato (§2); gravar no oficial depende do usuário |
| G17 | ✔ | `STATE_A`/`STATE_R`/`STATE_C` existem e são reproduzíveis |
| G19 (`needs_revit_check`) | parcial | `split_reason` existe; `needs_revit_check` **não** |
| G20 (métricas por versão) | ✘ | não implementado |
| G21 (`reference_score` recalibrado) | — | **bloqueado por G1–G16**; a C1 mudará 95→0 e 94→0 quando recalibrado |
| G23 (suíte completa) | não aplicável aqui | nenhum arquivo de produção tocado **nesta branch** |

**Nenhum gate foi promovido a aprovado nesta sessão.** G12, G13, G16, G18,
G19, G20 continuam pendentes; G13 tem correção pronta e não mesclada.

---

## 5. Fonte medida — preservada

- **`input.json` do TGD é fonte MEDIDA independente** (167 paredes, 82
  aberturas `measured` com `source_element_id`, vindas de documento Revit
  separado). **Não foi regenerado, não foi sobrescrito e não foi lido como
  derivado do gabarito.**
- **TP1 deriva do gabarito** — proveniência diferente, registrada.
- Nenhum input reconstruído recebeu `confidence="measured"` nem
  `source_element_id` (G15 ✔).
- Nenhuma abertura medida foi alterada (G4/G5 ✔).
- **`W0xx` não foi usado como identidade** em nenhuma medição desta
  sessão; toda comparação é por `key` geométrica ou por eixo.

---

## 6. Decisões que continuam com o usuário

Nenhuma foi tomada, influenciada ou presumida aqui.

| decisão | estado |
|---|---|
| **D1, D2, D3, D5** | **não decididas** |
| **D4** (conferência R1/R2/R3 no Revit) | **não decidida**; roteiro pronto, candidato determinístico, sem custo de espera |
| **D6** (recuperar os dois relatórios) | a resposta **muda**: os relatórios **existem**, a dívida era de **merge**. Recuperação preparada em `claude/cr-d1-recuperacao-documental` (PR próprio, só documentação) |
| merge da `CR-S1` (`PR #25`) | **pendente** |
| merge da `CR-C1` | **pendente** |
| aceitação da alternativa A (compensadores da S1) | **pendente** |
| recalibrar `reference_score.json` | **pendente** — escrita oficial |
| refresh de `baseline.json` | **pendente** — CR própria, autorizada |

---

## 7. Ordem de integração recomendada (não executada)

1. **CR-S1** (`PR #25`) — amarração; resolve **G13**. Depende da
   aceitação da alternativa A.
2. **CR-C1** — `expected_rows` físico; resolve **metade do G16**.
3. **CR-C2** (a criar) — a outra metade do G16.
4. **Reavaliar G12** com S1 + C1 aplicadas sobre o candidato.
5. **D1/D2/D3** pelo usuário → só então a CR-B oficial, com G1–G23.
6. **CR-D1** (documental) e **CR-R1** (Revit) em paralelo, sem bloquear.

`CR-D1` já está pronta e independente das demais.

---

## 8. Limitações declaradas

1. **Nenhuma medição no Revit ao vivo (MCP)** nesta sessão.
2. **G6/G7/G10 não foram reexecutados** — a evidência anterior é
   suficiente e os insumos são byte-idênticos (gerador determinístico).
3. **G12 não foi reavaliado com a S1 aplicada.** Exige montar
   `candidato + S1` e remedir `PRISM_CONTINUOUS_JOINT` por identidade
   física; a S1 não está mesclada e não foi aplicada a nenhuma cópia
   nesta sessão.
4. A tabela de migração cobre **paredes**. Migração de **aberturas** e de
   **nós** não foi gerada.
5. Nada aqui autoriza integração. **Nenhum PR foi marcado `ready`,
   nenhum merge foi feito, nenhum monitoramento automático foi criado.**
