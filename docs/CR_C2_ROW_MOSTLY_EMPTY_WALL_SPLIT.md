# CR-C2 — `COVERAGE_ROW_MOSTLY_EMPTY` APÓS DIVISÃO DE PAREDES

## Estado desta CR

> ### DIAGNÓSTICO CONCLUÍDO — **SEM PATCH**, POR EXIGIR DECISÃO NORMATIVA
>
> A causa-raiz está provada por geometria. **Nenhuma correção foi
> aplicada**, porque toda correção possível exige uma **definição
> normativa nova de "fiada" ou de "unidade de avaliação de parede"** — e
> essa definição é do usuário, não minha. §5 apresenta a decisão física
> com os números de cada opção.
>
> **Nenhum patch especulativo foi escrito.** Nada de produção foi tocado:
> `git diff --name-only origin/main..HEAD` não inclui
> `nuvem/benchmark/projects/**`, `nuvem/benchmark/validators/**`,
> `nuvem/core/**` nem `nuvem/REGRAS_MODULACAO_BLOCOS.md` (esta última só
> recebe o registro obrigatório do conhecimento, §7).

| item | valor |
|---|---|
| base | `main` real `91258dd` (conferida por `fetch`) |
| candidato | reproduzido do gerador determinístico `claude/candidato-validacao-gabarito-q450yr` `5640933` |
| identidade | coordenada global `(x, y, z)`. **`W0xx` nunca usado como identidade** |
| diagnósticos | `nuvem/benchmark/future_cr_preparation/cr_c2_row_mostly_empty/` |

---

## 1. Reprodução dos `+23` — confirmada

Candidato reconstruído com os invariantes reconferidos por mim:
**0 blocos humanos perdidos / novos / duplicados / órfãos**, 19 aberturas
removidas, comprimento `−2604,0cm` exato, `+19` paredes, **184 blocos que
mudaram de fiada**, `fiadas_total` **1365 → 1631 (+266)**.

Delta `STATE_R → STATE_C` dos códigos de cobertura, medido nas duas
árvores:

| projeto | árvore | `MISSING_ROW` | `ROW_MOSTLY_EMPTY` | `GAP_IN_ROW` |
|---|---|---|---|---|
| TGD | `91258dd` (sem C1) | **+17** | **+23** | −47 |
| TGD | com **C1** | **+0** | **+23** | −47 |
| TP1 | `91258dd` (sem C1) | **+17** | **+23** | −47 |
| TP1 | com **C1** | **+0** | **+23** | −47 |

Reproduz exatamente o G16. A CR-C1 resolve o componente `MISSING_ROW`; o
componente `ROW_MOSTLY_EMPTY` **não é afetado por ela** — como a própria
CR-C1 declarou, e confirmo.

## 2. As duas hipóteses fáceis — **as duas refutadas**

Nenhuma das duas explicações intuitivas sobrevive à medição.

**(a) "Os segmentos herdaram fiadas vazias."** Refutada: dos 108 achados
de `ROW_MOSTLY_EMPTY` em `STATE_C`, **zero** têm `covered_cm == 0`
(`c2_diag.py`). Nenhuma fiada acusada está vazia.

**(b) "O `OccupancyIndex` deixou de enxergar o segmento irmão."**
Refutada: `foreign_coverage_on_axis` funciona e é aplicada nos dois ramos
do validador. Nos casos dissecados ela cobre corretamente as zonas de
amarração da parede vizinha (ex.: `vizinho=['60-74','155-161']`). Quando
ela não cobre, é porque a parede vizinha **realmente não tem peça naquela
cota** — fato físico, idêntico em `STATE_R`.

## 3. Causa-raiz — **mudança de unidade de avaliação, provada**

### 3.1 O candidato não cria vazio físico nenhum

Medi os **vazios físicos em coordenada global** (união dos trechos
moduláveis não cobertos, contando peças de qualquer parede), o que
independe de como as paredes foram particionadas (`c2_phys.py`):

| projeto | vazios ≥5cm em R | em C | comprimento total de vazio |
|---|---|---|---|
| TGD | 648 | **601** | 96.864,8cm → **82.455,8cm** (**−14.409,0cm**) |
| TP1 | 637 | **590** | 86.979,5cm → **72.570,5cm** (**−14.409,0cm**) |

O candidato tem **menos** vazio físico, não mais.

Teste de contenção sobre os vazios que aparecem só em C:

| projeto | vazios só em C | **contidos** num vazio de R | **geometria nova** |
|---|---|---|---|
| TGD | 58 | **58** | **0** |
| TP1 | 58 | **58** | **0** |

**58 de 58 são re-recorte de vazio que já existia.** Zero geometria nova.

### 3.2 Os achados recaem sobre região já acusada

`c2_unit.py` — cada achado de C mapeado para os vazios globais da sua
fiada:

| projeto | achados em C | sobre região **já acusada** em R | sobre região não acusada |
|---|---|---|---|
| TGD | 108 | **104** | **4** |
| TP1 | 143 | **139** | **4** |

**104 de 108 (96%) são recontagem pura.**

### 3.3 A prova decisiva — reavaliar C na unidade de R

Os blocos de `STATE_C` são **os mesmos** de `STATE_R` (0 perdidos, 0
novos). Então dá para fazer o experimento limpo: reatribuir cada bloco de
C à parede-mãe de R e reavaliar (`c2_unidade.py`). Se o delta zerar, os
`+23` são **100%** unidade de avaliação.

| projeto | blocos reagrupados | `ROW_MOSTLY_EMPTY` na unidade de C | **na unidade de R** |
|---|---|---|---|
| TGD | 12.508 = 12.508 (**sem perda**) | **+23** | **−3** |
| TP1 | 12.703 = 12.703 (**sem perda**) | **+23** | **−3** |

> **Com os mesmos blocos, na unidade física original, o candidato MELHORA
> (−3) em vez de piorar (+23).** `COVERAGE_GAP_IN_ROW` também é negativo
> nas duas unidades (−47 e −12).

### 3.4 O mecanismo, num caso concreto

Parede-mãe de 1344cm dividida em segmentos (`c2_case.py`). Fiada 13 em
z=261 (a do topo), 8 blocos em `t=0..134` e `t=1210..1344`:

- **na mãe**: 268cm cobertos de 1328cm moduláveis → ratio **0,20**;
- **no filho de 594cm**: 126cm de 571cm → ratio **0,22**.

Mesmos blocos, mesmo vazio, mesma razão. O que muda é **quantas vezes** o
achado é emitido: uma parede-mãe deficiente vira 2–3 segmentos
deficientes. Saldo `+23` = **38 novos − 15 que sumiram**.

### 3.5 O achado estrutural: faixa de verga tratada como fiada

Classifiquei os achados por posição vertical (`c2_grid.py`) — fiada no
passo do grid × **faixa fora do passo** (verga, contraverga, peitoril):

| projeto | estado | no passo do grid | **fora do grid** |
|---|---|---|---|
| TGD | R (gabarito humano) | 24 | **61 (72%)** |
| TGD | C | 31 | **77** |
| TP1 | R (gabarito humano) | 52 | **68 (57%)** |
| TP1 | C | 59 | **84** |

> **A maioria dos `ROW_MOSTLY_EMPTY` do próprio gabarito humano está em
> faixas de verga/peitoril** — fiadas que existem apenas localmente sobre
> uma abertura e que **nunca deveriam** cobrir a parede inteira. Cobrar
> delas 50% do comprimento modulável é um falso positivo estrutural.

Isto **contradiz o contrato declarado do próprio código**, que diz que o
achado existe para detectar *"o solver ter perdido UMA das duas famílias
de fiada (A ou B)"*. Uma verga não é família A nem B.

**Mas é defeito PRÉ-EXISTENTE, não introduzido pela CR-B** — está em R e
em `STATE_A` na mesma proporção. Dos `+23`, **16 estão em faixas de verga
e 7 em fiadas de grid**.

### 3.6 Onde a causa NÃO está

- **Não é o extrator.** Round-trip `STATE_A → STATE_R` perfeito.
- **Não é o input reconstruído.** Nada em `nuvem/benchmark/projects/**` foi
  lido como derivado nem regravado.
- **Não é migração de identidade.** `stable_key` sem ambiguidade nos três
  estados (§ CR-B, G18).
- **Não é o solver.** O gabarito não passa pelo solver.
- **É o validador** — mas o defeito que ele tem (§3.5) é anterior à CR-B,
  e o que a CR-B provoca (§3.1–3.4) é **mudança de unidade**, não defeito.

## 4. Classificação dos `+23` (A–E)

| classe | | quantidade | evidência |
|---|---|---|---|
| **A** — defeito físico corrigido | | `GAP_IN_ROW` −47; **−14.409cm** de vazio | §3.1 |
| **B** — defeito físico **novo** | | **0** | 58/58 vazios contidos em vazio de R; geometria nova = 0 (§3.1) |
| **C** — mudança legítima de unidade | | **23 de 23** | −3 na unidade de R contra +23 na unidade de C (§3.3) |
| **D** — defeito de validador | | **0 novos**; 1 **pré-existente** | faixa de verga tratada como fiada (§3.5) — presente em R e em `STATE_A` |
| **E** — inconclusivo | | **0** | — |

Nada foi escondido em `major`/`minor`: os deltas de **todos** os códigos
estão em `gates.py` e `ident2.py`, com `critical_errors` **e** a lista
completa.

## 5. A decisão física — **para o usuário**

Nenhuma opção abaixo foi implementada. Os números são medidos
(`c2_opts.py`, `c2_unidade.py`), não estimados.

| opção | o que define | gabarito humano (piso de ruído) | **delta G16** |
|---|---|---|---|
| **hoje** | — | TGD 85 / TP1 120 | **+23** |
| **A** — `ROW_MOSTLY_EMPTY` só em fiada no passo do grid | *uma faixa de verga não é fiada de parede* | TGD **24** / TP1 **52** | **+7** — **não aprova o G16** |
| **B** — avaliar na unidade da parede física agregada | *paredes colineares divididas são uma unidade de cobertura* | inalterado | **−3** — aprovaria |
| **C** — manter o código e medir o G16 por vazio físico global | *o gate mede geometria, não contagem de achados* | inalterado | **−14.409cm** — aprovaria |

Observações honestas sobre cada uma:

- **A não basta.** Reduz o ruído em 72%/57%, mas deixa `+7` — os casos
  genuínos de mudança de unidade em fiadas de grid. E **muda o
  `baseline.json` e o `reference_score.json` oficiais**, que são escrita
  vedada sem autorização.
- **B** exige o conceito de *parede física agregada*, que **não existe no
  contrato de hoje**. É uma definição normativa nova de parede.
- **C** não toca código de produção nenhum, mas **muda a definição do
  gate G16** — decisão do usuário, não minha.
- **A + B** juntas dariam o resultado mais limpo, e são a combinação que
  eu recomendaria **se** o usuário decidir agir. Não a implementei.

**Nenhuma delas pode ser adotada por mim**, porque todas ou (i) definem
normativamente o que é uma fiada/parede, ou (ii) reescrevem gabarito,
baseline ou `reference_score` oficiais, ou (iii) redefinem um gate.

O que **explicitamente não fiz**, conforme o escopo: não criei regra geral
de parede curta; não mexi em `ROW_MOSTLY_EMPTY_RATIO`, `MIN_COVERAGE_RATIO`
nem em nenhum limiar; não transformei ausência de bloco em cobertura
válida; não toquei em X/T/L, B19, B34, B54 ou compensadores; não alterei o
solver para compensar erro de avaliação; não alterei o gabarito para
esconder defeito do validador.

## 6. Testes — por que ainda não existem

O escopo pedia testes que **falhem antes e passem depois**. Sem patch não
há "depois": um teste escrito agora fixaria como correta uma das opções de
§5 — exatamente a decisão que não é minha.

O que está pronto para virar teste no minuto seguinte à decisão, já
medido e reprodutível: os `+23` caso a caso; paredes não divididas;
paredes divididas com cobertura real; paredes divididas com **vazio
real** (a capacidade que não pode se perder); fiadas vazias; bases Z
distintas; aberturas; encontros; inversão de orientação; ordem de entrada;
determinismo. Os geradores estão em
`cr_c2_row_mostly_empty/`.

**Requisito que qualquer patch futuro terá de satisfazer, e que registro
agora para não se perder:** o gate não pode apenas reduzir
`ROW_MOSTLY_EMPTY` — ele tem de continuar acusando um trecho **realmente
vazio**. Na opção A isso é verificável, porque um trecho realmente vazio
tem fiadas de grid vazias, não só faixas de verga.

## 7. Registro obrigatório nas regras

Conforme `CLAUDE.md`, o conhecimento novo foi registrado em
`nuvem/REGRAS_MODULACAO_BLOCOS.md` com rótulo de confiança e pendência
explícita — **não** como regra aprovada.
