# CR-G12 — as 12 identidades críticas de `PRISM_CONTINUOUS_JOINT`

> **CR PREPARADA — DIAGNÓSTICO E ESCOPO. NENHUM PATCH APLICADO.**
> Solver, validadores, gabarito, baseline e `reference_score` **intocados**.

| item | valor |
|---|---|
| medido sobre | projeção isolada `91258dd` + S1 (`wall_stepper.py`) + C1 (`validate_wall_coverage.py`) |
| candidato | `5640933`, regerado |
| grandeza | `PRISM_CONTINUOUS_JOINT` na **saída do solver**, delta `IN_R → IN_C` |
| identidade | **(ponto global da junta, cotas físicas das duas fiadas, espessura)**. Nunca `W0xx`, nunca eixo isolado, nunca tipo de nó |
| diagnósticos | `nuvem/benchmark/future_cr_preparation/cr_g12_cross_band/` |

> **Nota de escopo.** O enunciado desta fase pede *"motivo exato do
> `MISSING_BINDING`"* para as 12 identidades do G12. São duas grandezas
> distintas: o **G12 é `PRISM_CONTINUOUS_JOINT`** (12 identidades, saída do
> solver) e o `JUNCTION_MISSING_BINDING` tem **10** identidades novas, no
> gabarito. As duas estão analisadas aqui — §1 a §4 o G12, §5 o
> `MISSING_BINDING`.

---

## 1. Tabela física das 12 identidades — G12

Idêntica nos dois projetos, o que por si já indica mecanismo único.

### TGD (base Z = 0)

| # | ponto global | cotas (z_A, z_B) | parede | eixo novo? | desencontro | humano tem junta? |
|---|---|---|---|---|---|---|
| 1 | `(-1004.0, 17.0)` | **141,0 / 161,0** | 939,0cm | sim | **0,00cm** | **não** (R e C) |
| 2 | `(-1004.0, 187.0)` | 141,0 / 161,0 | 939,0cm | **não** | 0,00cm | não |
| 3 | `(-964.0, 17.0)` | 141,0 / 161,0 | 939,0cm | sim | 0,00cm | não |
| 4 | `(-964.0, 187.0)` | 141,0 / 161,0 | 939,0cm | **não** | 0,00cm | não |
| 5 | `(-924.0, 17.0)` | 141,0 / 161,0 | 939,0cm | sim | 0,00cm | não |
| 6 | `(-924.0, 187.0)` | 141,0 / 161,0 | 939,0cm | **não** | 0,00cm | não |
| 7 | `(-884.0, 17.0)` | 141,0 / 161,0 | 939,0cm | sim | 0,00cm | não |
| 8 | `(-884.0, 187.0)` | 141,0 / 161,0 | 939,0cm | **não** | 0,00cm | não |
| 9 | `(-844.0, 17.0)` | 141,0 / 161,0 | 939,0cm | sim | 0,00cm | não |
| 10 | `(-844.0, 187.0)` | 141,0 / 161,0 | 939,0cm | **não** | 0,00cm | não |
| 11 | `(-804.0, 17.0)` | 141,0 / 161,0 | 939,0cm | sim | 0,00cm | não |
| 12 | `(-804.0, 187.0)` | 141,0 / 161,0 | 939,0cm | **não** | 0,00cm | não |

### TP1 (base Z = 612)

Mesma estrutura, **mesmas cotas relativas**: `753,0 − 612 = 141,0` e
`773,0 − 612 = 161,0`.

| # | ponto global | cotas | parede | eixo novo? | desenc. | humano? |
|---|---|---|---|---|---|---|
| 1–12 | `(6674.8 … 6874.8, 1120.0 / 1290.0)`, passo **40cm** | **753,0 / 773,0** | 939,0cm | 6 sim / 6 não | **0,00cm** | **não** |

**Estrutura comum, nos dois projetos:** 2 paredes de 939cm × 6 juntas
espaçadas de exatamente **40cm** (39cm do B39 + 1cm de junta), nas
**mesmas duas cotas**, todas com desencontro **0,00cm**.

## 2. Participantes e peças reais — o caso decisivo

O par mais informativo é a parede de **geometria idêntica** nos dois
estados (eixo `y=187,048`, `x=−1078,5 → −139,5`, 939cm, **a mesma porta**
`t=314..405`, `head=160`):

| | `STATE_R` (`W055`) | `STATE_C` (`W070`) |
|---|---|---|
| geometria do eixo | idêntica | idêntica |
| abertura | porta `t=314..405`, `head=160` | **a mesma** |
| nós de ponta | **`T`** em t=7 e t=932 | **`L`** em t=7 e t=932 |
| fiadas z=1 … **z=141** | — | **idênticas às de R** |
| fiada z=161 | `B39(15-54)`, **`B39(55-94)`**, `B39(95-134)`… | `B39(15-54)`, **`B19(55-74)`**, `B39(75-114)`… |
| fiadas z=181 … z=321 | — | **todas diferem** |

**A divergência começa exatamente em z=161** — a **primeira fiada acima
da verga da porta** (`head_cm = 160`).

Na fiada z=141 as juntas caem em `34,5 / 74,5 / 114,5 / 154,5 …`; em
`STATE_R` a fiada z=161 responde com `54,5 / 94,5 / 134,5 …` (desencontro
de 20cm, **amarração correta**), mas em `STATE_C` o `B19` de 19cm consome
20cm em vez de 40cm e **recoloca a fiada em fase**: `74,5 / 114,5 / 154,5
/ 194,5 / 234,5 / 274,5` — as 6 juntas contínuas acusadas.

## 3. Causa-raiz — fronteira de banda de abertura

As cotas `141 / 161` **não são um par qualquer**: são a **última fiada da
banda da porta** e a **primeira fiada da banda acima da verga**. É a
fronteira entre duas bandas de abertura.

Isso é **exatamente o defeito já documentado** em
`REGRAS_MODULACAO_BLOCOS.md` **§27.7** — *"NECESSIDADE DE ESCOPO ADICIONAL
— as BANDAS de abertura fragmentam a memória entre fiadas"*:

> *"`solve_building_blocks_all_courses` agrupa as fiadas físicas em bandas
> por conjunto de aberturas ativas e chama `solve_building_blocks` uma vez
> por banda. Cada banda resolve seu próprio par A/B **do zero**: a fiada A
> da banda 2 nunca vê a fiada B da banda 1, embora sejam fisicamente
> vizinhas. **Na fronteira entre duas bandas a regra #1 simplesmente não é
> avaliada.**"*
>
> *"**Medição**: das 33 coincidências proibidas que sobram depois do
> `CR-BLOCK-01`, **as 33 são cross-band** (…) tipicamente entre as fiadas
> 11 e 12."*
>
> *"**Correção proposta (não implementada)**: propagar as juntas/vazios da
> ÚLTIMA fiada física da banda anterior para a primeira busca da banda
> seguinte."*

> **As 12 identidades do G12 são uma instância desse defeito conhecido.**
> A conversão de nó `T → L` provocada pela divisão de paredes da CR-B faz
> a banda de cima escolher outro layout; como a regra #1 não é avaliada na
> fronteira, nada impede que o layout escolhido fique **em fase** com a
> banda de baixo.

**A CR-B não criou o defeito — ela expôs um caso dele.** O `STATE_R` só
escapava porque o layout que a banda de cima escolhia ali *calhava* de
desencontrar.

## 4. Classificação — **A, defeito físico real. Todas as 12**

| classe | quantidade | por quê |
|---|---|---|
| **A — defeito físico real** | **12 de 12** | desencontro **0,00cm** contra limite de 1,50cm; e o **gabarito humano não tem junta em nenhum desses pontos**, em `STATE_R` nem em `STATE_C` |
| B — erro de avaliação | 0 | a junta existe, medida em coordenada global |
| C — unidade nova legítima | **0** | **corrijo aqui uma classificação intermediária minha**: 6 das 12 estão em parede cujo eixo só existe em `STATE_C`, e cheguei a marcá-las como "unidade nova". **Está errado** — o eixo é novo, o **defeito de composição é o mesmo**, e a parede irmã de geometria **inalterada** exibe as outras 6 com a mesma assinatura. Todas são A |
| D — inconclusivo | 0 | — |

> **Não aceito as 12 por serem novas, e não as compenso** com o `−58` de
> saldo, com o `−101` de `COVERAGE_GAP_IN_ROW` nem com nenhuma outra
> melhora. São 12 juntas contínuas críticas em alvenaria estrutural.
> **G12 continua REPROVADO.**

## 5. As 10 identidades de `JUNCTION_MISSING_BINDING` — motivo exato

Grandeza diferente (gabarito, não solver), incluída porque o enunciado a
pede. Critério real do validador: *nenhuma peça **cobre** o ponto do nó
naquela banda de cota*, com ≥2 paredes participantes.

Assinatura uniforme nos **20** achados (10 por projeto): a peça mais
próxima está a **~8,0cm** do ponto do nó — nunca 0, nunca longe.

Geometria medida no caso `(-401,5, 24,1)`, z=140:

- a parede que **termina** ali (`W043`, 169cm) tem o ponto **a 0,05cm** da
  sua ponta;
- a parede **passante** (`W056`, 939cm) tem o ponto **a 7,05cm do seu
  eixo** — exatamente **meia espessura** (7,0cm). O ponto do nó é onde o
  eixo de uma encontra a **face** da outra;
- e, decisivo: na fiada z=140 de `W056` existe um **vazio de 16,0cm em
  t=669..685**, com o ponto do nó em **t=677 — o centro exato do vazio**.

**O mesmo vazio de 16,0cm, em t=669..685, existe em `STATE_R`** (na parede
`W052`, de 2348,99cm, ponto em t=677). Idêntico.

> **Motivo exato:** o nó novo foi registrado **no centro de um vazio de
> 16cm que sempre existiu**. A alvenaria não mudou; o que mudou é que
> agora existe ali um nó a quem cobrar amarração.
>
> **Classificação: C — unidade nova legítima, 10 de 10.** Todas em pontos
> que **não existiam** em `STATE_R`; **nenhum nó pré-existente piorou** —
> confirma independentemente a reconciliação da CR-B. O vazio subjacente é
> **real, pré-existente e já acusado** por `COVERAGE_GAP_IN_ROW`.

Duas das 20 (uma por projeto) caem em cota de **canaleta** (`CAN34`,
`CAN39`, `CM19` — peças que o solver não implementa), o que as coloca
também sob o contrato de *"escopo pendente do solver"* do
`solver_supported_catalog`.

## 6. Reproducer — **não obtido em forma reduzida**

Três tentativas, todas versionadas **por terem falhado**:

| tentativa | cenário | resultado |
|---|---|---|
| `repro_g12.py` | parede 939cm, nó de ponta `T` × `L`, **sem abertura** | **0 × 0** — não reproduz |
| `repro_g12b.py` | idem **com a banda de abertura real** (porta `t=314..405`, `head=160`) | **0 × 0** — não reproduz |
| `repro_g12c.py` | **subprojeto real isolado** (parede alvo + vizinhas do nó) | **inválido**: isolar muda o resultado — o solver resolve em função do contexto global, então o subprojeto não é o mesmo problema |

Isso delimita o que **não** é a causa isolada: nem o tipo do nó sozinho,
nem a banda de abertura sozinha, nem a vizinhança imediata. O efeito
depende do **contexto global do projeto**, o que é coerente com um defeito
de escolha de layout por banda.

**Reproducer válido hoje: o projeto completo**, determinístico
(determinismo conferido) e reprodutível pelo README da pasta.

## 7. Por que **não** há patch mínimo nesta entrega

| motivo | |
|---|---|
| **sem reprodução reduzida** | não há como demonstrar que um patch ataca a causa e não o sintoma. Patch sem reproducer é especulação |
| **arquivo fora do escopo autorizado** | a correção conhecida (§27.7) exige `nuvem/core/wall_modeling.py` — e a própria §27.7 registra que esse arquivo *"o CR desta branch não autoriza escrever"* |
| **efeito no corpus inteiro** | propagar juntas entre bandas muda o layout de **toda** parede com abertura nos 3 projetos. Validar isso exige a suíte completa e **refresh de `baseline.json`** — escrita oficial, vedada sem autorização |
| **proibição explícita** | não alterar solver, gabarito, baseline ou threshold para obter verde |

## 8. CR-G12 — escopo proposto (não iniciada)

| item | conteúdo |
|---|---|
| **título** | `CR-G12` — propagar juntas e vazios entre bandas de abertura |
| **causa** | §27.7: cada banda resolve o par A/B do zero; a regra #1 não é avaliada na fronteira |
| **correção** | a já proposta na §27.7: alimentar a primeira busca da banda seguinte com as juntas/vazios da **última fiada física** da banda anterior |
| **arquivo** | `nuvem/core/wall_modeling.py` (`solve_building_blocks_all_courses`) |
| **critério de aceite** | as **12 identidades → 0** nos dois projetos; `PRISM_CONTINUOUS_JOINT` **não sobe** no corpus oficial; `PRISM_STAGGER_BELOW_TARGET` declarado; determinismo; suíte completa |
| **dependências** | CR-S1 mesclada (ela já leva 28 → 12) |
| **dívida que abre** | **refresh de `baseline.json`** dos 3 projetos — CR própria e autorizada |
| **risco** | alto: muda o layout de toda parede com abertura |
| **estado** | **não iniciada.** Requer autorização explícita |
