# CR-C1 — `expected_rows` GLOBAL acusava parede correta (correção do validador)

> Corrige o **contrato de validação** de `COVERAGE_MISSING_ROW`. Não toca
> o solver, não toca o gabarito oficial, não toca `baseline.json`,
> `reference.json`, `input.json` nem `reference_score.json`, e não muda
> nenhuma regra normativa de modulação. Não integra a CR-B e não inclui a
> CR-S1.

## Base / branch / HEAD

| item | valor |
|---|---|
| base | `91258dd627af97fe437a56c0506eb096ca5aa267` (`origin/main`, confirmada por `git fetch`) |
| branch | `claude/cr-c1-expected-rows-fisico` |
| arquivo de produção tocado | **1** — `nuvem/benchmark/validators/validate_wall_coverage.py` |
| regras | seção **37** de `nuvem/REGRAS_MODULACAO_BLOCOS.md` |

> **Numeração das seções:** a **36** fica RESERVADA para a `CR-S1`
> (PR #25), que ainda **não foi mesclada** — esta CR nasceu da `main`
> `91258dd`, onde a 36 ainda não existe. As duas podem ser mescladas em
> qualquer ordem sem renumerar nenhuma.

---

## 1. O defeito, reproduzido antes de tocar em código

`validate_wall_coverage.validate` lia `settings.expected_rows` — que sai de
`settings.num_courses`, o **teto de fiadas do PROJETO** — e comparava com a
**contagem** de fiadas de **cada** parede:

```python
if expected_rows and indices and len(indices) < expected_rows:  # acusa
```

As paredes do corpus real têm alturas **diferentes**:

| altura | TGD | TP1 |
|---|---|---|
| 220cm | 1 | 1 |
| 260cm | 69 | 69 |
| 270cm | 1 | — |
| 280cm | 8 | 8 |
| 281cm | 18 | 18 |

Com passo de 20cm e peça de 19cm, uma parede de 260cm **nunca** vai ter 17
fiadas. Ela estava correta e era acusada assim mesmo.

### A prova que não depende de opinião: o validador acusava a própria referência

Rodando os validadores sobre o **gabarito HUMANO** (`reference.json`, que é
a referência de correção do projeto):

```
torre_easy_lo_r00_tgd   COVERAGE_MISSING_ROW = 95   (ramo do topo: 95 | ramo do meio: 0)
torre_easy_lo_r00_tp1   COVERAGE_MISSING_ROW = 94   (ramo do topo: 94 | ramo do meio: 0)
```

Os mesmos números que o `reference_score.json` **oficial** já registra
(`COVERAGE_MISSING_ROW: 95` / `94`) — ou seja, não é artefato desta
medição. **100% deles vêm do ramo do pé-direito e ZERO do ramo do meio da
pilha.**

---

## 2. Causa-raiz

Duas coisas erradas no mesmo `if`, e é importante separá-las:

1. **A grandeza**: comparava **contagem ordinal** de fiadas, não geometria.
2. **O escopo**: o número comparado é **global do projeto**, aplicado
   igualmente a paredes de alturas diferentes.

Etapa exata: `validate_wall_coverage.validate_wall`, ramo do pé-direito —
**depois** de o solver ter terminado, dentro do validador. Nenhuma linha de
solver participa do defeito.

### Por que a expectativa NÃO pode ser "quantas fiadas cabem"

A tentação é trocar `expected_rows` por `floor(altura / passo)`. Medido no
gabarito humano, isso **não** reproduz a realidade: a fiada do topo **não
segue o passo do grid**, ela é encostada no pé-direito.

| altura | última cota do gabarito | observação |
|---|---|---|
| 220cm | z=200 | grid |
| 260cm | z=240 | grid |
| 270cm | z=**250** | fora do grid |
| 280cm | z=260 | grid |
| 281cm | z=**261** | fora do grid |

E há fiadas **intercaladas** em cotas não-modulares (z=150/170/190/210/230),
que são vergas/contravergas de abertura — a `W005` do TGD tem 17 fiadas numa
parede de 260cm por causa de três portas com `head` 140/160/160.

Reproduzir aqui **onde** cada fiada cai seria reimplementar a política de
empilhamento do solver **dentro do validador** — e um validador que duplica
a regra que ele fiscaliza deixa de fiscalizar.

---

## 3. A correção mínima

Um arquivo, `nuvem/benchmark/validators/validate_wall_coverage.py`. Nenhuma
constante de domínio nova, nenhuma tolerância nova, nenhuma severidade
alterada, nenhum código de achado novo ou removido.

A pergunta passa a ser **física e por elevação**, parede a parede:

> ainda cabe uma fiada **inteira** (próximo passo + corpo da peça) abaixo do
> pé-direito **desta** parede?

```python
next_course_cm = highest_cm + course_step_cm
if next_course_cm + block_height_cm <= base_z_cm + height_cm:   # acusa
```

- `missing_course_above_cm` — o predicado físico, com a prova no docstring;
- `wall_top_z_cm` — `base_z + height`, ou `None` quando a parede não declara
  altura (único caso sem veredito: chutar a altura a partir das fiadas
  existentes tornaria o critério **tautológico**);
- `validate()` deixa de ler `settings.expected_rows` e passa o passo de
  fiada do projeto (`analysis.course_step_cm`, que já existia);
- `expected_rows` continua na assinatura de `validate_wall` para não quebrar
  chamador antigo, e **não decide mais** o achado — está documentado no
  código.

O achado continua sendo **`COVERAGE_MISSING_ROW`**, mesma categoria e mesma
severidade: a CR corrige *quando* ele dispara, não *o que ele vale*. Os
campos novos (`highest_course_z_cm`, `missing_course_z_cm`,
`wall_top_z_cm`) são físicos; `rows_found` foi preservado.

### Margem: o critério é conservador de propósito

Folga real no topo medida no gabarito humano, por parede:

| folga | TGD | TP1 | leitura |
|---|---|---|---|
| −9cm | 24 | 24 | canaleta `CJ19` (29cm) ultrapassa o topo declarado |
| +1cm | 63 | 62 | junta |
| +11cm | 10 | 10 | maior folga **legítima** |

O limiar é o passo inteiro (**20cm**) — margem de **9cm** contra a maior
folga legítima observada. Nenhuma parede do gabarito é acusada, e o critério
ainda pega quem parou uma fiada antes.

---

## 4. Matriz de comparação — por identidade física

Todos os validadores, nas duas árvores (`91258dd` sem C1 × esta branch),
sobre o **gabarito humano** e sobre a **saída do solver de produção**.

| unidade | `COVERAGE_MISSING_ROW` | demais códigos |
|---|---|---|
| TGD **gabarito** | 95 → **0** (−95) | **delta zero** (15 códigos) |
| TP1 **gabarito** | 94 → **0** (−94) | **delta zero** (15 códigos) |
| TGD **solver** | 192 → **190** (−2) | **delta zero** (18 códigos) |
| TP1 **solver** | 0 → 0 | **delta zero** (11 códigos) |
| piloto **solver** | 0 → 0 | **delta zero** (7 códigos) |

Delta **zero** — verificado, não presumido — em `COVERAGE_GAP_IN_ROW`,
`COVERAGE_ROW_MOSTLY_EMPTY`, `COVERAGE_PARTIAL_WALL`,
`COVERAGE_WALL_NOT_MODULATED`, `POSITION_OVERLAP`, todos os `PRISM_*`,
todos os `JUNCTION_*`, todos os `COMPENSATOR_*` e todos os `OPENING_*`.

> Registro explícito do risco que **não** se materializou: o cenário de
> referência da skill `cr-verification` é justamente
> `COVERAGE_MISSING_ROW` cair enquanto `COVERAGE_ROW_MOSTLY_EMPTY` sobe.
> Medido aqui: `COVERAGE_ROW_MOSTLY_EMPTY` com **delta zero** nas cinco
> unidades. Não há troca de um código por outro.

### Decomposição por ramo — a prova de que não é um silenciador

| unidade | topo (sem→com) | meio (sem→com) |
|---|---|---|
| TGD gabarito | 95 → **0** | 0 → 0 |
| TP1 gabarito | 94 → **0** | 0 → 0 |
| TGD **solver** | 30 → **28** | 162 → **162** |

No solver do TGD o ramo do topo cai apenas **30 → 28**: **28 dos 30 achados
são defeitos REAIS e continuam acusados**. O ramo do meio da pilha
(162) fica **intocado** — não foi alterado por esta CR.

### Classificação dos casos (A–F, exigida pelo diagnóstico)

| caso | classe | evidência |
|---|---|---|
| 95/94 do gabarito humano | **B** — fiada que não pertence à altura daquela parede | paredes de 220/260/270/280/281cm contra um teto global de 17 |
| 2 paredes do solver TGD que deixaram de ser acusadas | **B** | `h=340`, última fiada em `z=321`; `321+19 = 340` = topo exato — **parede fechada** |
| 28 paredes do solver TGD ainda acusadas | **A** — fiada fisicamente esperada e ausente | `h=340`, última fiada em `z=301`; ainda cabe fiada em `z=321` (`321+19 = 340 ≤ 340`) |
| 162 do ramo do meio | fora do escopo desta CR | ramo não tocado |
| faixas intercaladas (z=150/170/190/210/230) | **C** — faixa de abertura real | vergas/contravergas; nunca são a fiada do topo |

A discriminação entre as 2 (classe B) e as 28 (classe A) é de **19cm** —
mesma altura, mesma espessura, mesmo projeto; só muda a cota da última
fiada. **Zero paredes passaram a ser acusadas.**

---

## 4-bis. Matriz sobre o CANDIDATO da CR-B — o estado onde o gate G16 falha

A medição acima é sobre o corpus **oficial**. O gate **G16** da
reconciliação da CR-B (`docs/BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_
RECONCILIATION.md` §9) mede outra coisa: o delta `STATE_R → STATE_C` do
**candidato**, onde as paredes foram divididas. Foi ele que originou esta
CR, então a medição foi refeita lá.

Candidato reproduzido do gerador determinístico
(`claude/candidato-validacao-gabarito-q450yr` `5640933`,
`build_candidate.py`, `CR_B_OUT=/tmp/cr_b_candidate`) — invariantes
reconferidos: 0 blocos humanos perdidos / novos / duplicados / órfãos, 19
aberturas removidas, comprimento −2604,0cm exato. **Nada oficial tocado.**

| projeto | árvore | `MISSING_ROW` (R→C) | `ROW_MOSTLY_EMPTY` (R→C) |
|---|---|---|---|
| TGD | **sem** C1 | **+17** | **+23** |
| TGD | **com** C1 | **+0** | **+23** |
| TP1 | **sem** C1 | **+17** | **+23** |
| TP1 | **com** C1 | **+0** | **+23** |

Os números `+17` / `+23` **reproduzem exatamente** o que o G16 registra —
confirmação independente de que esta CR está medindo a mesma grandeza que
o gate.

Em valor absoluto sobre o `STATE_C`: `COVERAGE_MISSING_ROW` **112 → 0**
(TGD) e **111 → 0** (TP1), 100% do ramo do topo, com **delta zero em todos
os outros 14 códigos**.

### O G16 é composto — esta CR resolve METADE dele

| componente do G16 | esta CR | causa |
|---|---|---|
| `+17 COVERAGE_MISSING_ROW` | **resolvido** (+17 → +0) | `expected_rows` global |
| `+23 COVERAGE_ROW_MOSTLY_EMPTY` | **NÃO resolvido** (+23 → +23) | **outra causa** |

**Isto está declarado de propósito, e não foi contornado.**
`COVERAGE_ROW_MOSTLY_EMPTY` não lê `expected_rows` em nenhum momento: ele
compara as fiadas de uma parede **entre si**
(`ratio < ROW_MOSTLY_EMPTY_RATIO and best_ratio >= MIN_COVERAGE_RATIO`).

Diagnóstico mínimo do resíduo (TGD, saldo +23 = **38 novos − 15 que
sumiram**): as fiadas novas acusadas cobrem **6% a 30%** do trecho
modulável enquanto a melhor fiada da **mesma** parede cobre **100%**
(`best_row_ratio = 1.0`) — por exemplo, uma parede de 169cm com **zero**
aberturas cujas fiadas 10/12/14 cobrem 9cm de 146cm. **34 dos 38 casos
estão em paredes sem abertura nenhuma**, e os comprimentos se concentram
em 169cm (24 casos).

Classe: **D/E** — consequência da **divisão de paredes** feita pela
própria CR-B (o manifesto do candidato registra `+19` paredes e **184
blocos que mudaram de fiada**): quando um eixo é partido, os blocos
humanos são redistribuídos entre os segmentos e uma fiada de um pedaço
fica legitimamente esvaziada. **Não é defeito de `expected_rows` e não é
desta CR.**

> **Consequência para a CR-B: o gate G16 continua NÃO aprovado.** Metade
> dele foi resolvida aqui; a outra metade precisa de uma CR própria —
> proposta como **CR-C2 — cobertura por segmento após divisão de
> parede** (diagnosticar se o `ROW_MOSTLY_EMPTY` em segmento partido é
> defeito real de cobertura, artefato de *ownership* entre segmentos, ou
> critério do validador inadequado para segmentos curtos).
> **Não implementada. Não ampliei esta CR para cobri-la.**

---

## 5. Testes

`tests/regression/test_validator_coverage_expected_rows_cr_c1.py` —
**19 casos**.

| árvore | resultado |
|---|---|
| `91258dd` (**sem** o patch) | **16 falham**, 3 passam |
| esta branch (**com** o patch) | **19 passam** |

Os 3 que passam nas duas árvores são controles legítimos (parede sem bloco
nenhum, invariância à ordem de entrada, determinismo).

Cobertura:

- paredes de **alturas diferentes** (220/260/280) no mesmo projeto;
- **base Z deslocada** (`base_z_cm = 612`, o caso real do TP1) — completa e
  truncada;
- fiada do topo **fora do grid** (281cm fechando em z=261);
- **faixas intercaladas** de abertura (verga/contraverga);
- **ausência real** de fiada no topo — anti-tautologia, três variações
  (parou na metade, falta exatamente a última, `expected_rows` baixo não
  esconde mais o truncamento);
- fiada faltando **no meio da pilha** (controle: ramo não tocado);
- parede **sem altura declarada** (fica sem veredito, de propósito);
- parede **sem bloco nenhum** (continua `COVERAGE_WALL_NOT_MODULATED`);
- `expected_rows` global **não decide mais** (1 e 999 dão o mesmo veredito);
- invariância à ordem de entrada — comparada por **identidade física**
  (eixo da parede), nunca pelo rótulo `W0xx`, que `assign_ids` deriva da
  ordem geométrica;
- determinismo (3 execuções);
- **corpus real**: o gabarito humano dos dois projetos não pode ter fiada
  de topo acusada (falha antes com 95 e 94).

Controles de regressão: `tests/regression/test_validators.py` **23/23**.

### Suíte completa

`python3 -m pytest tests/ -q -rf` nesta branch (inclui os `slow`):

```
2 failed, 885 passed in 2889.47s (0:48:09)
```

**As 2 falhas são PRÉ-EXISTENTES e nenhuma é nova.** São as mesmas de
`tests/regression/test_benchmark_baselines.py`, com as **mesmas asserções e
os mesmos valores** já medidos por execução direta num *worktree* limpo de
`91258dd` **sem** este patch:

| teste | asserção | base `91258dd` | esta branch |
|---|---|---|---|
| `[torre_easy_lo_r00_tgd]` | `compensators` 52 → 61 (delta 9), `REGRESSAO` | igual | igual |
| `[torre_easy_lo_r00_tp1]` | `JUNCTION_MISSING_BINDING` 8 → 9 (delta 1), `REGRESSAO CRITICA` | igual | igual |

A contagem de testes também fecha: a base tem 868 testes, esta CR
acrescenta **19** → `2 + 885 = 887`.

Nenhum baseline regravado, nenhum `--save-baseline`, nenhum `skip`/`xfail`,
nenhum threshold e nenhuma severidade alterados. **A suíte NÃO está verde e
não está sendo declarada verde** — está no mesmo estado da base.

---

## 6. Preservação

- `nuvem/benchmark/projects/**` — **intocado** (`input.json`,
  `reference.json`, `baseline.json`, `reference_score.json`).
- Nenhum `--save-baseline`, nenhum `skip`/`xfail`, nenhum threshold
  alterado, nenhuma severidade alterada.
- Solver (`nuvem/core/**`) — **intocado**. A CR-S1 **não** está neste diff.
- `validate_junctions.py` (CR-V1) — **intocado**. A identidade física por
  elevação da V1 é preservada e reforçada: este achado também passa a ser
  por cota física, nunca por índice ordinal.

---

## 7. Dívidas e o que esta CR NÃO resolve

- **`baseline.json` fica desalinhado de propósito.** O baseline registra
  `COVERAGE_MISSING_ROW` TGD **265** / TP1 **16**, medidos numa versão
  anterior do pipeline; a medição de hoje na base limpa já dá 192 / 0
  **antes** desta CR. O baseline **não foi regravado** — refresh de
  baseline é trabalho separado e precisa de autorização específica, depois
  de classificar honestamente as regressões reais.
- **`reference_score.json` vai mudar quando for recalibrado** (95→0 e
  94→0). Não foi recalibrado aqui: é escrita em arquivo oficial e exige
  decisão do usuário.
- **Os 162 achados do ramo do meio da pilha no solver do TGD** continuam
  sem diagnóstico próprio. Não foram tocados; podem ser defeito real,
  artefato de reconstrução, ou mistura. **CR separada.**
- **As 28 paredes de `h=340` que param em `z=301`** são defeito real do
  solver, agora corretamente acusado. Não é escopo desta CR corrigi-lo —
  é um achado que esta CR **entrega**, não esconde.
- O TGD oficial produz **167 paredes** contra 97 do gabarito: dívida de
  topologia pré-existente, registrada na CR-B, fora de escopo aqui.
