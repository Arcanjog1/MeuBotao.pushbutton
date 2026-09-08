# CR-G12 — implementação: a regra #1 passa a ser avaliada na **fronteira entre bandas de abertura**

> **Desenvolvimento e testes em branch isolada. Nenhum merge.**
> `baseline.json`, `reference_score.json`, gabarito e qualquer arquivo de
> `nuvem/benchmark/projects/**` **intocados**. Nenhum validador, threshold,
> `skip`/`xfail` ou regra normativa alterado.

| item | valor |
|---|---|
| base histórica | `91258dd627af97fe437a56c0506eb096ca5aa267` (`main` real, conferida por `fetch`) |
| diagnóstico reutilizado | `claude/multifase-cr-c2-c1-b-ikr8jc`, HEAD `a25f846` (conferido) |
| branch desta CR | `claude/cross-band-mechanism-fix-ab76jv` |
| arquivos de produção tocados | `nuvem/core/wall_modeling.py`, `nuvem/core/engine/wall_stepper.py` |
| identidade física | **(ponto global da junta, cotas físicas das duas fiadas, espessura)** — nunca `W0xx`, nunca o eixo, nunca o tipo de nó (regra §38.5) |

---

## 1. Estado e evidência

### 1.1 HEADs reais

```
main                                        91258dd   (não avançou)
claude/multifase-cr-c2-c1-b-ikr8jc          a25f846   (diagnóstico da CR-G12)
claude/corrigir-alternancia-no-l-76nnb3     33d035f   (CR-S1, draft)
claude/cr-c1-expected-rows-fisico           34bf696   (CR-C1, draft)
claude/candidato-validacao-gabarito-q450yr  5640933   (gerador do candidato CR-B)
```

`git merge-base main claude/multifase-cr-c2-c1-b-ikr8jc = 91258dd` — o
diagnóstico está exatamente sobre a base informada.

### 1.2 Os 12 achados do G12 são distintos dos 10 `JUNCTION_MISSING_BINDING`

Confirmado por **medição independente**, não por leitura do relatório
anterior (`g12_ident.py` sobre o candidato CR-B com S1+C1):

| | grandeza | onde é medido | quantidade | pontos |
|---|---|---|---|---|
| **G12** | `PRISM_CONTINUOUS_JOINT` | **saída do solver**, delta `IN_R → IN_C` | **12 por projeto** | TGD `(-1004…-804, 17/187)`, cotas **141/161**; TP1 `(6674,8…6874,8; 1120/1290)`, cotas **753/773** |
| `MISSING_BINDING` | `JUNCTION_MISSING_BINDING` | **gabarito** | 10 por projeto | ex.: `(-401,5, 24,1)`, cota **140** |

Códigos diferentes, grandezas diferentes, **conjuntos de identidade
disjuntos**. As 12 do G12 reproduziram **exatamente** a tabela de
`docs/CR_G12_CROSS_BAND.md` (mesmos 12 pontos, mesmas cotas, `R=298 C=240
saldo −58 novas=12 sumiram=70` no TGD; `R=286 C=228 saldo −58 novas=12
sumiram=70` no TP1) — confirmação independente do diagnóstico.

**Não** reiniciei a reconciliação dos 19 casos da CR-B. **Não** repeti a
investigação da C2.

---

## 2. Reprodução fiel

### 2.1 Por que cada simplificação anterior deixou de reproduzir

As três tentativas versionadas foram reexecutadas nesta sessão e
continuam negativas. A causa é a mesma nas três, e agora está medida:

| tentativa | o que tinha | por que não reproduz |
|---|---|---|
| `repro_g12.py` | parede 939cm, nó T×L, **sem abertura** | sem abertura só existe **uma banda** — não há fronteira nenhuma para a regra #1 deixar de avaliar |
| `repro_g12b.py` | idem **com a porta real** (`t=314..405`, verga 160) | com **uma** porta de peitoril 0 as bandas são só `{abaixo da verga}` e `{acima}`. A banda de cima resolve o **mesmo problema** da de baixo menos o recorte do vão, então `banda2.A ≈ banda1.A`; e `banda1.B` já desencontra de `banda1.A` **dentro da banda**. O desencontro sai de graça, por acaso estrutural — medido: `z=141` com juntas em 34,5/74,5… e `z=161` em 49,5/89,5… (15cm de desencontro) |
| `repro_g12c.py` | subprojeto real isolado | isolar mudava o resultado — mas o relatório concluiu daí que **nenhuma** redução seria válida. **Essa conclusão estava errada**: o que faltava era escolher *quais* paredes manter por medição, não por proximidade |

Acrescentei duas varreduras paramétricas próprias, também negativas, que
fecham o diagnóstico da redução **sintética**:

| varredura | cenários | resultado |
|---|---|---|
| `sweep2_janela.py` | 1.952 combinações: porta + **janela** (peitoril > 0) variando comprimento, posição, peitoril e verga | **0** juntas contínuas cross-band |
| `sweep3_no_de_meio.py` | 430 combinações com **encontro T no meio do eixo** | **0** juntas contínuas — em nenhum cenário sintético o solver produz junta contínua |

> **Conclusão medida:** o mecanismo **não é reproduzível numa planta
> sintética pequena**. Numa planta inventada o solver simplesmente não
> produz junta contínua nenhuma — as três tentativas anteriores e as duas
> minhas medem a mesma coisa. O caminho da redução **não** era inventar
> geometria; era **remover** geometria real.

### 2.2 Reproducer mínimo — 3 paredes REAIS

`reduzir.py` faz *delta-debugging* sobre o `input.json` **oficial**:
parte das 167 paredes do `torre_easy_lo_r00_tgd` e remove parede enquanto
a **identidade física alvo** continuar sendo acusada com a correção
desligada. Sobraram **três**:

| índice no `input.json` | eixo | abertura |
|---|---|---|
| 55 | 79,01cm | — |
| 82 | 269,01cm | porta `t=19,00..110,00`, verga 221 |
| **124** | **169,00cm** (parede alvo) | **janela `t=83,73..134,76`, peitoril 150, verga 231** |

Nenhuma coordenada inventada: geometria, espessura, cotas, aberturas e
parâmetros vêm do arquivo oficial, intocado. O subplano preserva tudo que
o enunciado exige que seja preservado:

- **bandas abaixo, dentro e acima da abertura**: `[0..6] [7..10] [11] [12..16]`
  — inclusive a banda de **uma fiada só** (a 11), onde o peitoril atravessa a fiada;
- **estado das fiadas vizinhas** (z=121 e z=141);
- **peças de amarração e reservas de nó**: `L_CORNER` na ponta e o **B54 de
  `T_INTERSECTION_MIDSPAN`** em `t=40..94` da fiada z=121;
- **reparo e recálculo posteriores** (`OPENING_REPAIR_FILL` nas duas fiadas);
- **geometria e parâmetros reais da abertura**.

Rodando (`repro_g12d_minimo.py`):

```
### CROSS_BAND_JOINT_PROPAGATION_ENABLED = False  | bandas: [[0..6], [7..10], [11], [12..16]]
    junta ponto=(-401.5, 309.5) cotas=(121.0, 141.0) t=39.50 desencontro=0.00cm cross_band=True
    junta ponto=(-401.5, 309.5) cotas=(221.0, 241.0) t=39.50 desencontro=0.00cm cross_band=True

### CROSS_BAND_JOINT_PROPAGATION_ENABLED = True
    (nenhuma junta continua)
```

É o **mesmo mecanismo físico**, não a mesma contagem: desencontro
**0,00cm**, na fronteira entre a banda `[11]` e a banda `[12..16]`.

---

## 3. Causa-raiz

### 3.1 A primeira etapa em que a junta contínua é criada

`_solve_building_blocks_all_courses_core` (`wall_modeling.py`) agrupa as
fiadas físicas em **bandas** por conjunto de aberturas ativas
(`_group_course_indices_by_opening_band`) e chama `solve_building_blocks`
**uma vez por banda**. Dentro de uma banda, `solve_wall_free_fill`
(`wall_stepper.py`) resolve a família `"A"` primeiro e a família `"B"`
depois, com `course_a_joint_positions_cm` — é ali que a regra #1 vive.

Essa lista **nasce vazia a cada banda**. Duas fiadas fisicamente vizinhas
que caem em bandas diferentes nunca se veem: a regra #1 **não é
avaliada** ali. É exatamente o defeito registrado na **§27.7** e nunca
implementado.

Medido no subplano mínimo, fiada a fiada:

```
z=121 (banda 2, fiada 11)  ... C09(30..39) | B54(40..94, T_INTERSECTION_MIDSPAN)
z=141 (banda 3, fiada 12)  ... C04(35..39) | C09(40..49)      <- PRÉ-FIX, junta em 39,5
```

A junta de `z=121` em `t=39,5` é a **borda da peça de amarração**: sua
posição não depende de layout nenhum e o preenchimento **não tem como
movê-la**. Quem tinha de sair da frente era a fiada de cima — que está em
outra banda.

### 3.2 Por que a auditoria do próprio solver não pegava

`audit_wall_bond_quality` (`wall_modeling.py`) só acusa junta corrida
quando o *cluster* tem `>= BOND_CONTINUOUS_JOINT_MIN_COURSES` (4) fiadas
**e** `>= BOND_CONTINUOUS_JOINT_RATIO` (60%) delas. Um par isolado de
fiadas vizinhas na fronteira de banda **nunca** atinge esse limite — é
invisível para o solver, e só o `PRISM_CONTINUOUS_JOINT` do benchmark
(que compara fiadas **consecutivas**, par a par) o enxerga. Por isso o
defeito atravessava geração **e** auditoria.

### 3.3 Por que o efeito depende do contexto global

O que decide se as duas bandas ficam **em fase** é a peça de amarração e
a reserva de nó — que dependem da planta inteira. Daí a impressão, no
diagnóstico anterior, de que "isolar muda o resultado": muda mesmo, se as
paredes forem escolhidas por proximidade. Escolhidas por **medição**
(delta-debugging), o subplano de 3 paredes reproduz.

### 3.4 O que **não** é a causa

- **não** é o tipo do nó (`T`→`L`) por si: no candidato CR-B a conversão é o
  *gatilho* que muda o layout escolhido pela banda de cima, mas o defeito
  aparece na `main` com o `input.json` **oficial**, sem candidato nenhum
  (medido: 16 identidades cross-band puras no TGD, 22 no TP1);
- **não** é a escolha `B39→B19` em si: ela é a *consequência* de a banda de
  cima resolver do zero;
- **não** é o reparo B19 residual nem o SAFE REPAIR do ARM: os dois
  reconstroem via `rebuild_fn`, que passa pelo mesmo laço de bandas.

---

## 4. Correção — o menor patch que ataca a causa

Duas peças, dentro das regras existentes. Nenhuma regra de domínio nova.

### 4.1 `wall_stepper.py` — a regra #1 ganha uma terceira origem de junta

`_cross_band_swapped_layout` (novo): **troca conservadora**, no mesmo
padrão já usado pela metade simétrica da junta NÓ|FILL
(`CR-BLOCK-NODE-FILL-REVALIDATION`). O layout que o caminho normal
escolheu continua sendo o primeiro e o normal; só é trocado quando

1. ele de fato empilha junta sobre a fiada vizinha de outra banda; **e**
2. existe composição do **mesmo trecho** com **estritamente** menos
   coincidência cross-band; **e**
3. essa composição **não piora** a coincidência com a família oposta da
   própria banda (regra #1 intra-banda, que já valia); **e**
4. **não piora** a regra #2 (compensadores em sequência).

Nunca troca por empate. Com semente vazia devolve o layout **intacto** —
é exatamente o comportamento anterior a esta CR.

A semente entra por um parâmetro novo, `cross_band_joint_seed`,
encadeado `solve_building_blocks` → `process_walls_one_by_one` →
`solve_wall_free_fill`. Default `None` em todos: **nenhum chamador
existente muda de comportamento**.

### 4.2 `wall_modeling.py` — o laço de bandas passa a ter memória

- `_course_joint_positions_by_wall`: as juntas de **uma fiada física já
  montada**, medidas na geometria **real** das peças lançadas
  (`joint_positions_from_extents`) — nunca no "layout", que depois do
  recorte e do reparo já não descreve o que ficou na parede. Duas peças
  separadas por um vão não formam junta.
- `_cross_band_seed_for_band`: monta `{wall_idx: {"A": [...], "B": [...]}}`
  com as juntas das fiadas **fisicamente vizinhas que estão em outra
  banda**. Vizinha da própria banda **nunca** entra (lá a regra #1 já é
  avaliada).
- `_solve_building_blocks_all_courses_core` virou um **laço de passes**
  sobre a função original (renomeada `_..._pass`, sem mudança no que faz).

**Por que mais de um passe.** As bandas são resolvidas de baixo para
cima, então no primeiro passe uma banda só enxerga a vizinha de **baixo**.
Isso basta para a maioria das fronteiras, mas não para uma banda
**espremida** entre duas outras — o caso comum de uma banda de uma fiada
só: a fiada de cima pode ter a junta presa a uma peça de amarração, que
não se move; quem tinha de sair da frente era a de baixo, e no primeiro
passe ela ainda não sabia disso. O segundo passe roda com o resultado do
primeiro como vizinhança de cima (Gauss-Seidel).

**Aceitação global, nunca otimista:** o resultado de um passe só substitui
o anterior se a coincidência cross-band **total**
(`_cross_band_coincidence_total`) diminuir **estritamente**. Essa métrica
usa a tolerância **do próprio motor**
(`VERTICAL_JOINT_STAGGER_TOLERANCE_CM = 1,0cm`), não a do benchmark
(1,5cm): nenhum threshold foi criado nem alterado. Na prática é
indiferente — das 156 coincidências cross-band medidas no TGD, **149 têm
desencontro 0,00cm** e as outras 7, 0,01cm. Empate mantém
o passe anterior — o mais conservador. Medido no TGD: um passe só resolvia
10 identidades e **criava 5 novas**; com o segundo passe são **14
resolvidas e 0 novas**.

`CROSS_BAND_JOINT_PROPAGATION_ENABLED` (default `True`) e
`CROSS_BAND_JOINT_PROPAGATION_PASSES` (2) seguem o padrão de
`ARM_ROLE_SAFE_REPAIR_ENABLED`/`B19_RESIDUAL_FILL_REPAIR_ENABLED`:
desligado, roda **um** passe sem semente nenhuma, idêntico ao
comportamento anterior.

**Não** há exceção para coordenada nenhuma. **Não** copiei a solução
humana: o gabarito não passa pelo solver.

---

## 5. Resultado físico — as 12 identidades

Candidato CR-B (`5640933`) sobre a projeção isolada `91258dd` + CR-S1
(`wall_stepper.py`) + CR-C1 (`validate_wall_coverage.py`), em **cópias
isoladas** montadas por `git archive` + `git show` (nenhum merge, nenhuma
branch alterada). O `wall_stepper.py` do estado "com G12" é a fusão
3-vias `base=main / S1 / G12` — **sem conflito**.

| projeto | árvore | R | C | saldo | **identidades NOVAS** |
|---|---|---|---|---|---|
| TGD | S1+C1 **sem** G12 | 298 | 240 | −58 | **12** |
| TGD | S1+C1 **+ G12** | 256 | 192 | −64 | **0** |
| TP1 | S1+C1 **sem** G12 | 286 | 228 | −58 | **12** |
| TP1 | S1+C1 **+ G12** | 260 | 196 | −64 | **0** |

> **As 12 identidades físicas → 0 nos dois projetos.** E o
> `PRISM_CONTINUOUS_JOINT` **não sobe**: cai em valor absoluto nos quatro
> estados (−42, −48, −26, −32).

---

## 6. Deltas completos

### 6.1 Corpus oficial na `main` — mesma árvore, correção desligada × ligada

| código | TGD antes | TGD depois | Δ | TP1 antes | TP1 depois | Δ | piloto |
|---|---|---|---|---|---|---|---|
| `PRISM_CONTINUOUS_JOINT` | 336 | **322** | **−14** | 290 | **260** | **−30** | 0 → 0 |
| — dos quais **cross-band** | 156 | 142 | −14 | 124 | 98 | −26 | 0 |
| — **cross-band puras** (só existem por causa da fronteira) | **16** | **2** | **−14** | **22** | **0** | **−22** | 0 |
| `PRISM_JOINT_STACK` | 20 | 20 | 0 | 18 | **16** | **−2** | 0 |
| `COMPENSATOR_CONSECUTIVE` | 523 | **511** | **−12** | 1480 | **1474** | **−6** | 0 |
| `COMPENSATOR_EXCESS_IN_RUN` | 440 | **439** | **−1** | 1135 | **1133** | **−2** | 0 |
| `COMPENSATOR_VERTICAL_STRIP` | 81 | **79** | **−2** | 190 | 190 | 0 | 18 → 18 |
| `PRISM_STAGGER_BELOW_TARGET` (nível 2) | 841 | 872 | **+31** | 1506 | 1531 | **+25** | 0 |
| `COVERAGE_*`, `OPENING_*`, `JUNCTION_*`, `POSITION_OVERLAP` | — | — | **0** | — | — | **0** | **0** |

**Total de achados (todos os códigos):** TGD 4.916 → 4.918 (**+2**, e são
`PRISM_STAGGER_BELOW_TARGET` de nível 2 trocando por críticos removidos);
TP1 5.049 → **5.034** (**−15**); piloto 124 → 124.

**Juntas contínuas NOVAS (por identidade física, em qualquer ponto):
ZERO** nos dois projetos. Nenhuma identidade que não existisse antes.
`piloto_sintetico_2x2`: **delta zero em todos os códigos**.

### 6.2 Candidato CR-B com S1+C1 — sem G12 × com G12

| código | TGD `R` | TGD `C` | TP1 `R` | TP1 `C` |
|---|---|---|---|---|
| `PRISM_CONTINUOUS_JOINT` | 298 → **256** | 240 → **192** | 286 → **260** | 228 → **196** |
| `PRISM_JOINT_STACK` | 19 → **16** | 15 → **12** | 18 → **16** | 14 → **12** |
| `COMPENSATOR_CONSECUTIVE` | 1470 → **1449** | 1422 → **1407** | 1466 → **1460** | 1418 → **1412** |
| `COMPENSATOR_EXCESS_IN_RUN` | 1140 → 1142 (**+2**) | 1159 → 1161 (**+2**) | 1128 → **1126** | 1142 → **1140** |
| `PRISM_STAGGER_BELOW_TARGET` | 1502 → 1523 (**+21**) | 1623 → 1650 (**+27**) | 1444 → 1465 (**+21**) | 1561 → 1574 (**+13**) |
| todos os demais códigos | **delta 0** | **delta 0** | **delta 0** | **delta 0** |

### 6.3 Trade-offs — declarados, não escondidos

1. **`PRISM_STAGGER_BELOW_TARGET` sobe** (+13 a +31). É **nível 2**: não
   reprova nada, registra que o desencontro ficou abaixo do alvo de 10cm.
   É a troca **crítico → menor** esperada: onde antes havia junta
   empilhada (0,00cm) agora há desencontro pequeno mas real. Declarado
   como o critério de aceite da §8 de `docs/CR_G12_CROSS_BAND.md` exige.
2. **`COMPENSATOR_EXCESS_IN_RUN` +2 no TGD** (nos dois estados do
   candidato). Pequena piora real, não compensada com as melhoras: fica
   registrada. No corpus oficial da `main` esse mesmo código **melhora**
   (−1 TGD, −2 TP1), e `COMPENSATOR_CONSECUTIVE` melhora em todos os
   estados medidos.
3. **Custo de tempo: o solver fica ~2× mais lento** (TGD: 48s → 94s por
   resolução completa) por causa do segundo passe. O segundo passe é
   pulado quando o primeiro já zera a coincidência cross-band, mas nos
   projetos reais ele roda. É a dívida de desempenho desta CR.

### 6.4 Residual honesto — 2 identidades no TGD

Sobram **2** identidades cross-band puras no TGD (zero no TP1), as duas
no mesmo ponto de um eixo de 969cm, `t=649,5`, nas fronteiras `(121/141)`
e `(221/241)`. Nenhuma delas está entre as 12 do G12 — o G12 fecha em
**0**. Não forcei nada para zerá-las: qualquer alternativa que as
resolvesse pioraria a regra #1 **dentro** da banda, e o guard recusa
corretamente. Fica registrado como pendência aberta, não como sucesso.

---

## 7. Testes

`tests/test_cross_band_joint_propagation_cr_g12.py` — **11 testes
rápidos** (0,3s) e **9 marcados `slow`** (corpus real).

| grupo | o que prova |
|---|---|
| unidade (7) | semente vazia no primeiro passe; vizinha da própria banda ignorada; paridade correta (A recebe de B); Gauss-Seidel do segundo passe; troca não mexe em quem já está certo; troca desencontra quando há alternativa; guard não piora a regra #1 intra-banda |
| **reproducer mínimo (3)** | **pré-fix**: as 3 paredes reais acusam a identidade `(-401,5, 309,5)` cotas 121/141, desencontro 0,00cm; **pós-fix**: zero junta contínua; e **nenhuma peça de amarração ou de reparo de abertura muda de lugar** |
| corpus `slow` (9) | reproducer pré-fix nos 2 projetos; identidades cross-band puras resolvidas e **nenhuma nova**; **nenhuma junta contínua nova em lugar nenhum**; **delta zero** em `COVERAGE_*`/`OPENING_*`/`JUNCTION_*`/`POSITION_*`; **determinismo** (duas execuções, peças idênticas na mesma ordem) |

Todo asserto de "resolvido" **falha se o patch for revertido** (a flag
deixa de existir, ou, forçada a `False`, o defeito volta).

Resultado: **20 passed** (`python3 -m pytest
tests/test_cross_band_joint_propagation_cr_g12.py -q`, 10min17s).

### 7.1 Suíte completa — pré-existentes × novas

Duas execuções da suíte inteira (`pytest tests nuvem/tests -q`), a de
controle numa **cópia isolada da `main` `91258dd`** montada por
`git archive`:

| árvore | resultado | tempo |
|---|---|---|
| `main` `91258dd` **sem patch** | **2 failed, 884 passed** | 34min20s |
| `main` **+ CR-G12** | **4 failed, 882 passed** | 1h04min46s |

**2 falhas PRÉ-EXISTENTES**, idênticas nas duas árvores, com os **mesmos
valores** (reconferidas rodando só esse arquivo com o patch):

| teste | motivo | antes | depois |
|---|---|---|---|
| `test_benchmark_baselines[torre_easy_lo_r00_tgd]` | categoria `compensators` | 52 | 61 |
| `test_benchmark_baselines[torre_easy_lo_r00_tp1]` | `JUNCTION_MISSING_BINDING` | 8 | 9 |

São a dívida de **refresh de `baseline.json`** já registrada (o baseline é
anterior às correções de prisma). **Não pioraram com o patch** — os
números são exatamente os mesmos.

### 7.2 Duas falhas NOVAS — as duas por MELHORIA, nenhuma por regressão física

Ambas são asserções que travam a **magnitude de um reparo pós-hoc**. A
CR-G12 remove o defeito **antes**, então o reparo tem menos o que
consertar — e o **estado final de produção é idêntico**. Medido, não
suposto:

**(a) `test_block_arm_role_candidate_safety_contract.py::test_t1_t9_candidato_seguro_e_aceito_no_tgd_real`**

Espera que o candidato ARM `wall_idx=23` seja **aceito** no TGD. Com o
patch ele não é sequer **proposto**:

| | sem CR-G12 | com CR-G12 |
|---|---|---|
| parede 23 tem **prisma forçado no resultado ORIGINAL** (o que torna a aresta "reparável") | **sim** | **não** |
| candidatos ARM aceitos | `23/SAME_A`, `91/SAME_B` | `91/SAME_B` |
| candidatos ARM rejeitados | 19 | 19 |
| parede 23 com prisma forçado no resultado **FINAL** | **não** | **não** |
| **conjunto de paredes com prisma forçado no FINAL** | 29 paredes | **as MESMAS 29 paredes** |

> O SAFE REPAIR não foi enfraquecido: **o defeito que ele consertava
> naquela parede deixou de existir na geração**. O resultado físico final
> é **idêntico**, parede por parede. A asserção registra o *mecanismo*
> ("este candidato foi aceito"), não o *resultado físico* ("a parede não
> tem prisma forçado").

**(b) `test_block_node_fill_revalidation.py::test_t20_caso_real_tp1_junta_b19_b39_em_cima_da_peca_de_no`**

Trava uma redução de **pelo menos 2×** produzida pela metade simétrica
NÓ|FILL (`assert len(sig_on) * 2 <= len(sig_off)`):

| | `v_off` | `v_on` | `sig_off` | `sig_on` | asserção |
|---|---|---|---|---|---|
| sem CR-G12 | 31 | 14 | 16 | 4 | `4×2 ≤ 16` ✔ |
| com CR-G12 | **16** | 14 | **5** | 4 | `4×2 ≤ 5` ✘ |

> **O estado de produção (`v_on` = 14, `sig_on` = 4) é EXATAMENTE o mesmo.**
> O que mudou foi o **contrafactual**: com a CR-G12 ligada, o estado "sem
> a metade simétrica" já é muito melhor (31 → 16), então não sobra espaço
> para uma redução de 2×. A asserção `len(v_on) < len(v_off)` — a que
> prova que a metade simétrica ainda ajuda — **continua passando**.

**O que NÃO fiz, de propósito:** não toquei em nenhuma das duas
asserções. Ajustar teste de outra CR para obter verde está fora do que
esta CR autoriza, e a mudança tem peso de contrato (o contrato do SAFE
REPAIR e o da metade simétrica). **Decisão do usuário.** A correção que
eu proporia, se autorizado, é trocar a asserção de *mecanismo* por
*resultado físico* — o mesmo precedente já registrado na §27.9
(`test_pipeline_lanca_blocos_e_ajusta_na_mesma_passada`, cuja asserção
"registrava um artefato do bug"):

- em (a): exigir que a parede 23 **não tenha prisma forçado no resultado
  final**, aceitando as duas rotas (reparo ARM, ou geração já correta);
- em (b): manter `len(v_on) < len(v_off)` e trocar o fator 2× por
  asserções nos números medidos, declarando que a CR-G12 já retira 15 das
  31 violações antes de a metade simétrica agir.

---

## 8. Gates

| gate | antes | agora |
|---|---|---|
| **G12** (`PRISM_CONTINUOUS_JOINT`, identidades novas `IN_R→IN_C`) | **REPROVADO** — 12 por projeto | **12 → 0 nos dois projetos**, com o absoluto caindo |
| **G13** (`JUNCTION_NOT_ALTERNATING`) | resolvido pela CR-S1 | **inalterado** — delta 0 em `JUNCTION_*` |
| **G16** (`COVERAGE_*`) | **REPROVADO** — a metade `ROW_MOSTLY_EMPTY` depende da **CR-C2**, que continua pendente de decisão normativa | **NÃO declarado aprovado.** Delta 0 em `COVERAGE_*` — esta CR não mexe nele e **não** o destrava |

> **G16 continua não aprovado. A C2 continua pendente.**

---

## 9. Dívidas preservadas (nenhuma resolvida por suposição)

1. **`baseline.json` dos 3 projetos** — não regravado. É escrita oficial,
   vedada nesta CR. Como o baseline atual é anterior às correções de
   prisma (registra `PRISM_CONTINUOUS_JOINT = 961` no TGD contra os 322
   medidos agora), `tests/regression/test_benchmark_baselines.py` continua
   passando: ele só reprova **piora**.
2. **`UNCLASSIFIED_RULE_CONFLICT` / §27.8 item 2** — junta de peça de
   **amarração** repetida na mesma posição X. Continua sem decisão
   normativa e **fora** desta CR: a semente cross-band não tenta
   resolvê-la (o preenchimento não pode mover a borda de uma peça de nó, e
   o guard recusa a troca).
3. **CR-C2** — decisão física em `docs/CR_C2_DECISAO_FISICA.md`, intocada.
4. **CR-S1 (#25) e CR-C1 (#26)** — continuam `draft`, não mescladas.
5. **Custo de tempo ~2×** (§6.3 item 3).
6. **2 identidades cross-band residuais no TGD** (§6.4).

---

## 10. Veredito de prontidão

> **Pronta para revisão humana; NÃO pronta para merge.**

- a causa-raiz está isolada, medida e reproduzida por um reproducer
  mínimo de **3 paredes reais** que falha no código anterior **pelo mesmo
  mecanismo físico**;
- o patch é mínimo, desligável, e com semente vazia é bit-a-bit o
  comportamento anterior;
- as **12 identidades → 0** nos dois projetos, com `PRISM_CONTINUOUS_JOINT`
  caindo em absoluto e **zero** junta contínua nova;
- geometria, aberturas, amarração L/T/X, cobertura, compensadores,
  determinismo e os demais nós/bandas preservados (delta 0 nos códigos de
  cobertura/abertura/encontro/posição);
- **falta**: decisão humana sobre (i) o trade-off do §6.3, (ii) as **duas
  asserções do §7.2** — as duas falham por melhoria, com o resultado
  físico final idêntico, e eu **não** as alterei —, (iii) o merge da CR-S1
  e da CR-C1, e (iv) a CR própria de refresh de `baseline.json`.

**Estado da suíte, sem maquiagem:** `4 failed, 882 passed`. Duas falhas
são **pré-existentes na `main`** (mesmos valores, §7.1) e duas são as
asserções de magnitude do §7.2. **Nenhuma delas é regressão física** — e
nenhuma foi contornada com `skip`, `xfail` ou ajuste de threshold.

**Não** marquei `ready`. **Não** mesclei. **Não** criei monitoramento.
**Não** iniciei C2, C02, C10, Junction, ARM nem qualquer outra CR.
