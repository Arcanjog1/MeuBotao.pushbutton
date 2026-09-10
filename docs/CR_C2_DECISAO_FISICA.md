# CR-C2 — FECHAMENTO: quadro exato das opções e decisão física

> **Complementa** `docs/CR_C2_ROW_MOSTLY_EMPTY_WALL_SPLIT.md` (diagnóstico).
> Aqui: o contrato de cada opção, a busca em camadas pelo fundamento
> normativo de cada uma, e **duas correções da minha própria análise
> anterior**.
>
> **Nenhum patch aplicado.** Nada de produção tocado.

| item | valor |
|---|---|
| base | `main` real **`91258dd`** (conferida por `fetch`) |
| candidato | `5640933`, regerado pelo gerador determinístico |
| projeção | `91258dd` + `wall_stepper.py` (S1) + `validate_wall_coverage.py` (C1) |
| identidade | coordenada global. `W0xx` nunca usado |

---

## 1. As três opções — contrato integral, uma a uma

Transcritas dos originais e completadas com o que a Fase 1 exigiu. **Não
são variantes de uma mesma solução: A, B e C avaliam unidades físicas
diferentes e respondem a perguntas diferentes.**

### OPÇÃO A — `ROW_MOSTLY_EMPTY` só em fiada no passo do grid

> *Contrato que ela cria:* **uma faixa fora do passo do grid não é fiada
> de parede para efeito de cobertura.**

| aspecto | conteúdo |
|---|---|
| **unidade física avaliada** | a **fiada individual**, como hoje — muda só quais fiadas são *elegíveis* |
| **parede dividida** | não trata. A unidade continua sendo `(parede, fiada)`, então o segmento continua sendo contado por si |
| **fiada** | elegível quando `(z − base_z)` cai no passo do grid (com ou sem o `FIRST_COURSE_Z_OFFSET_CM` de 1cm) |
| **verga / peitoril** | **inelegível** — sai da contagem |
| **detecção de vazio real** | intacta e **1:1** por `COVERAGE_GAP_IN_ROW` (§3) |
| **elimina** | TGD 85→**24**, TP1 120→**52** no gabarito humano (−72% / −57%) |
| **preserva** | os 24 / 52 achados em fiadas de grid, incluindo todos os de parede realmente vazia |
| **delta G16** | **`+7`** — **não aprova o gate** |
| **fundamento em regra existente** | **NÃO — ver §2.1.** É definição normativa nova |

### OPÇÃO B — avaliar na unidade da parede física agregada

> *Contrato que ela cria:* **segmentos colineares resultantes de uma
> divisão são uma única unidade de cobertura.**

| aspecto | conteúdo |
|---|---|
| **unidade física avaliada** | a **parede-mãe agregada** (os segmentos colineares somados) |
| **parede dividida** | é o alvo: reagrupa os segmentos antes de avaliar |
| **fiada** | inalterada — toda fiada continua elegível |
| **verga / peitoril** | inalterado — continua contando como fiada |
| **detecção de vazio real** | intacta e 1:1 por `GAP_IN_ROW` |
| **elimina** | nada no gabarito humano (piso de ruído inalterado) |
| **preserva** | todos os 85 / 120 |
| **delta G16** | **`−3`** — aprovaria |
| **fundamento em regra existente** | **NÃO — e ver §2.2: B contradiz a tese da própria CR-B** |

### OPÇÃO C — manter o código e medir o G16 por vazio físico global

> *Contrato que ela cria:* **o gate mede geometria, não contagem de
> achados.**

| aspecto | conteúdo |
|---|---|
| **unidade física avaliada** | o **vazio físico em coordenada global**, independente de parede e de fiada |
| **parede dividida** | **imune por construção** — a métrica não conhece o particionamento |
| **fiada** | irrelevante para a métrica |
| **verga / peitoril** | irrelevante para a métrica |
| **detecção de vazio real** | **é** a métrica |
| **elimina** | nenhum achado — não mexe em validador nenhum |
| **preserva** | todos |
| **delta G16** | **−14.409,0cm** de vazio físico; 601 vazios contra 648 — aprovaria |
| **fundamento em regra existente** | **PARCIAL — ver §2.3.** Não altera código; redefine o critério de um gate |

---

## 2. Busca em camadas pelo fundamento normativo

Feita antes de concluir ausência de regra, conforme `CLAUDE.md`: termo
exato → sinônimos pt-BR/EN → entidades relacionadas → `rg "^#"` →
símbolo de código.

### 2.1 Opção A — **sem fundamento; e a caracterização anterior estava errada**

Buscados: `verga`, `contraverga`, `peitoril` (56 ocorrências), `banda de
abertura`, `faixa`, `bloco cortado`, seção 15, seção 27.7,
`_group_course_indices_by_opening_band`.

O que **existe**: o conceito de **banda** — `solve_building_blocks_all_
courses` agrupa fiadas físicas *"por conjunto de aberturas ativas"*
(seções 27.7 e a causa-raiz da §1130). É do **solver**, para decidir
layout A/B, e **não** define o que é fiada para efeito de cobertura.

> ### CORREÇÃO DA MINHA ANÁLISE ANTERIOR
>
> Eu havia caracterizado as fiadas fora do passo como *"faixas de
> verga/peitoril"*. **Medido, isso é falso para a maioria delas.**
>
> | medição (candidato, TGD) | valor |
> |---|---|
> | fiadas fora do passo | 116 |
> | dessas, **com abertura ativa** naquela cota | **34 (29%)** |
> | dessas, **sem abertura nenhuma** | **82 (71%)** |
> | peças dominantes | `B39_C` 137, `B34_C` 94, `B19_C` 67, `B54_C` 18 — **peças CORTADAS**, sufixo `_C` |
>
> São majoritariamente **fiadas de peças cortadas**, não vergas. A
> hipótese "verga" cobre menos de um terço. Corrijo isso também em
> `REGRAS_MODULACAO_BLOCOS.md` §38.2.

Isso levou a um contrato **que de fato existe** e é textual:

> `solver_bridge.solver_supported_catalog`: *"O gabarito tem 9 códigos a
> mais (`B19_C`, `B34_C`, `B39_C`, `B54_C`, `C09_C`, `CAN34`, `CAN39`,
> `CJ19`, `CM19` — peças cortadas e canaletas), que o solver de hoje não
> implementa. **As peças excluídas continuam no gabarito: o comparador as
> mostra como diferença (nível 2), que é o que elas são — escopo pendente
> do solver, não erro de modulação.**"*

Composição das fiadas acusadas (`acusadas.py`):

| | TGD R | TGD C | TP1 R | TP1 C |
|---|---|---|---|---|
| fiada **100% de peças que o solver não implementa** | 53 | **64** | 60 | **71** |
| fiada mista | 20 | 22 | 28 | 30 |
| fiada **100% de peças suportadas** | 12 | **22** | 32 | **42** |

**Por que esse contrato não resolve, mesmo assim:** ele governa a
comparação **solver × gabarito** (nível 2, escopo pendente). O G16 compara
`STATE_R × STATE_C`, **os dois gabarito humano** — o contrato não se
aplica. E o número decide: aplicado como filtro, o delta cairia de `+23`
para `+12` (`+2` mistas `+10` suportadas), **ainda longe de zero**.

> **`10` dos `23` estão em fiadas 100% compostas de peças que o solver
> implementa.** Nenhum argumento de escopo de catálogo os alcança.

**Conclusão: A é definição normativa nova.**

### 2.2 Opção B — **sem fundamento, e há argumento físico CONTRA**

Buscados: `colinear`, `unidade de avaliação`, `parede física`,
`fragmentação`, `split_reason`, `deduplicate_walls`, seções 15, 23.5, 24.9.

O único texto próximo é a seção **23.5**: *"com a parede recortada antes,
qualquer etapa que leia a geometria REAL (…) enxerga a parede já
fragmentada pelo vão (…). **A parede inteira tem de existir no modelo
enquanto os blocos são decididos.**"* — mas isso é **ordem de operações no
Revit** (recortar depois de modular), não unidade de avaliação do
benchmark.

> ### CORREÇÃO DA MINHA RECOMENDAÇÃO ANTERIOR
>
> Eu havia recomendado **A + B**. Retiro a recomendação de **B**, por um
> argumento físico que não considerei:
>
> A tese central da CR-B, medida e documentada, é que os 19 casos **não
> são aberturas**: são *"o espaço entre DUAS PAREDES QUE TERMINAM NO NÓ"*
> — quatro sinais convergentes, incluindo o teste da verga (60 de 62
> aberturas reais do TGD têm verga; dos 19, **zero**).
>
> Se isso está certo, os segmentos **são paredes fisicamente distintas** —
> e a unidade de avaliação correta em `STATE_C` **é o segmento**. A opção
> B reagruparia justamente o que a CR-B acabou de separar por evidência
> física. Na prática, minha própria implementação da medição (`c2_unidade.py`)
> reagrupa usando as paredes de `STATE_R` como molde: ela é, literalmente,
> **desfazer a divisão da CR-B para efeito de avaliação**.
>
> Adotar B seria afirmar, na avaliação, o contrário do que a CR-B afirma
> na geometria. **B é normativa nova e provavelmente incorreta.**

O valor de `c2_unidade.py` permanece — como **prova diagnóstica** de que
os `+23` são unidade e não geometria. Ele não é uma correção proposta.

### 2.3 Opção C — o único caminho sem regra nova de domínio

C não altera validador, solver, gabarito, baseline ou limiar. Ela diz
apenas que **o G16 não pode ser medido comparando contagens de achados
entre dois estados com particionamento de parede diferente** — o que a
própria §38.1 das regras já registra como consequência medida.

Ainda assim é **decisão do usuário**, porque redefine o critério de um
gate. Não a adotei.

---

## 3. A prova dos `+23` — reconfirmada, e o que ela **não** diz

| prova | TGD | TP1 |
|---|---|---|
| vazios físicos ≥5cm, R → C | 648 → **601** | 637 → **590** |
| comprimento de vazio físico | **−14.409,0cm** | **−14.409,0cm** |
| vazios que aparecem só em C | 58 | 58 |
| **contidos** num vazio de R | **58 de 58** | **58 de 58** |
| **geometria nova** | **0** | **0** |
| mesmos blocos na unidade original | **−3** (vs `+23`) | **−3** (vs `+23`) |

### 3.1 Ressalva explícita — contido **não** quer dizer falso

O alerta é justo e eu o adoto como limite da conclusão:

> **Estar contido num vazio anterior prova apenas que a CR-B não criou
> geometria nova. NÃO prova que o vazio seja falso, nem que a ausência não
> seja real.** Os 58 são vazios **reais**; eram reais em `STATE_R` e
> continuam reais em `STATE_C`.

E foi por isso que medi a detecção, em vez de assumi-la
(`vazio_real.py`):

| estado | vazios físicos ≥5cm | `COVERAGE_GAP_IN_ROW` | **vazios SEM achado** |
|---|---|---|---|
| TGD R | 648 | 648 | **0** |
| TGD C | 601 | 601 | **0** |
| TP1 R | 637 | 637 | **0** |
| TP1 C | 590 | 590 | **0** |

> **Correspondência 1:1 perfeita, nos quatro estados.** Todo vazio físico
> real é acusado — por `COVERAGE_GAP_IN_ROW`, não por
> `ROW_MOSTLY_EMPTY`. O `ROW_MOSTLY_EMPTY` é um **agregador secundário do
> mesmo fato geométrico** que o `GAP_IN_ROW` já reporta integralmente.

Consequência para qualquer decisão futura: **nenhuma das três opções pode
perder detecção de vazio real**, porque nenhuma toca o `GAP_IN_ROW`. O que
está em jogo é o que o `ROW_MOSTLY_EMPTY` deve *significar*, não se o
vazio é visto.

---

## 4. Decisão — e por que a Fase 2 não produziu patch

A condição era: *"se A+B apenas implementarem um contrato normativo já
existente e inequívoco, aplique o menor patch"*.

| opção | contrato já existente e inequívoco? | patch? |
|---|---|---|
| **A** | **não** — nenhuma regra define fiada por passo do grid; o conceito de banda é do solver e 71% das fiadas fora do passo não têm abertura ativa | **não** |
| **B** | **não** — e contradiz a tese física da própria CR-B (§2.2) | **não** |
| **C** | não altera código; **redefine um gate** | **não** |

> ### NENHUM PATCH APLICADO — a condição da Fase 2 não se cumpriu.
>
> Nem A nem B implementam contrato existente. **A** cria uma definição
> nova de fiada; **B** cria uma definição nova de parede que colide com a
> evidência física da CR-B. Frente C2 permanece **bloqueada em decisão
> normativa** — e a frente G12 seguiu, como instruído.

### 4.1 Recomendação revista

**Opção C**, isolada — não A+B.

É a única que (i) não inventa definição de fiada, (ii) não contradiz a
tese física da CR-B, (iii) não toca validador, solver, gabarito, baseline
ou limiar, e (iv) mede exatamente o que o gate quer saber: *a
reconstrução piorou a alvenaria?* Resposta medida: **não — −14.409cm de
vazio e 47 vazios a menos por projeto.**

Se, ainda assim, o `ROW_MOSTLY_EMPTY` precisar ficar mais limpo como
métrica própria, **A é defensável isoladamente** — mas exige a decisão
normativa, muda `baseline.json` e `reference_score.json` (escrita oficial)
e **não aprova o G16 sozinha** (`+7`).

**Nada disso foi executado.** A decisão é do usuário.
