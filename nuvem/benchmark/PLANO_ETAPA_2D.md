# PLANO DA CORRECAO DO CR-1 - ETAPA 2D (find_wall_pairs / face stealing / espessura correta)

> **NADA FOI IMPLEMENTADO NESTA SESSAO.** Zero edicao em `nuvem/core/**`,
> no solver, no Wall Modeling, em tolerancias, aberturas, catalogo ou nos
> testes existentes. Esta sessao produziu: este plano, os scripts de
> simulacao offline em `nuvem/benchmark/diagnostics_2d/` e a secao 26 de
> `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
>
> Convencao herdada da Etapa 2C: **FATO MEDIDO** = numero que saiu de
> execucao real nesta sessao. **HIPOTESE** = leitura plausivel, nao provada.
> **LIMITACAO** = o que nao foi possivel medir com os artefatos do repo.

- Base: `origin/main` = `41b526cbcd8ed5e36153c73665b3d00afac40bdc`
- Projeto: `torre_easy_lo_r00_tgd`
- Motor: `nuvem/core/engine/wall_pairing.py` (`wall_modeling_engine_sha256 = f0171249...`)
- **Baseline reproduzido bit a bit nesta sessao:** `merge 9258 -> 2868`,
  `589 candidatos -> 209 aceitos / 380 descartados`, `dedup -42 -> 167`,
  `77/209 na espessura exata`, `31 paredes < 50 cm`, `70/97 cobertas`,
  `76/167 no eixo certo`, `82/91 aberturas atribuidas`. Identico ao
  `wall_modeling_snapshot.json` e ao relatorio 2C.

---

## RESUMO EXECUTIVO EM 7 LINHAS

1. O problema **e' de ranking**, e o ranking sozinho resolve quase tudo.
2. Trocando a chave de ordenacao para "erro de espessura primeiro,
   sobreposicao depois", **sem mudar mais nada**: espessura exata
   `37% -> 60%`, eixo correto `76 -> 96` paredes, cobertura do gabarito
   `70 -> 87` de 97, roubos de face `52 -> 7`, e as **9 aberturas passam a
   91 de 91 atribuidas**.
3. **Nenhuma parede hoje coberta deixa de ser coberta** (R10 = zero
   regressao medida).
4. **Matching global NAO e' necessario:** medido, ele empata exatamente
   com o guloso corrigido (176 pares / 122 exatos / 87 cobertas / 96 eixos
   nos dois). Com bonus de cardinalidade ele fica **pior** que o guloso.
5. **Nao mexer em `overlap_ratio` nem por um piso de `r_long`:** medido,
   qualquer piso de sobreposicao pela linha mais longa mata paredes reais
   (W001, W068 tem `r_long = 0,28`) e devolve 4 aberturas para o limbo.
6. As linhas de esquadria **melhoram mas nao somem** so' com o ranking
   (pares curta x longa `30 -> 20`). A segunda protecao generalizavel e' um
   corte por **erro de espessura**, nao por comprimento.
7. A correcao e' **uma expressao** em `find_wall_pairs`, custo de execucao
   irrelevante (a ordenacao de 589 candidatos leva 0,4 ms; a varredura
   O(n^2) de 5,5 s nao muda).

---

# A. O ALGORITMO ATUAL, PASSO A PASSO

`nuvem/core/engine/wall_pairing.py::find_wall_pairs` (linhas 266-443).

### 1. Como os candidatos sao encontrados

Uma unica varredura `O(n^2)` sobre `lines_to_process` (as 2.868 linhas que
sobraram do `merge_collinear_fragments`), todos os pares `(i, j)` com
`i < j`. A geometria de cada linha e' pre-calculada uma vez em
`_line_geom_cache`. **FATO MEDIDO:** 4.111.278 pares avaliados, 5,55 s.

### 2. Condicoes de elegibilidade (todas obrigatorias, na ordem)

| # | teste | constante | efeito |
|---|---|---|---|
| 1 | `_are_parallel_cached(i, j)` | `PARALLEL_TOLERANCE` | descarta nao-paralelas |
| 2 | `MIN_WALL_THICKNESS_FT <= dist <= MAX_WALL_THICKNESS_FT` | 5 cm / 35 cm | faixa fisica |
| 3 | `_closest_target_thickness_ft(dist, alvos, tol) is not None` | `tol` | **unico filtro de espessura** |
| 4 | `overlap_ft >= MIN_WALL_SEGMENT_ABS_FLOOR_FT` | **2,0 cm** | piso absoluto |
| 5 | `min(len_i, len_j) >= 1e-9` | - | degenerada |
| 6 | `overlap_ratio >= MIN_WALL_SEGMENT_OVERLAP_RATIO` | **0,6** | correm lado a lado |

**FATO MEDIDO:** sobram **589 candidatos**.

### 3. Como as espessuras selecionadas entram

`_closest_target_thickness_ft(dist, target_thicknesses_ft, tolerance_ft)`
devolve, entre as espessuras escolhidas, a **mais proxima** de `dist`
desde que `|dist - t| <= tolerance_ft`; senao `None`.

Ou seja: **`matched_thickness` ja' existe hoje, e o erro de espessura ja'
esta' calculado dentro dessa funcao - e' descartado no `return`.** A
correcao nao precisa inventar o conceito, so' preserva-lo.

`tolerance_ft` vem de `compute_detection_tolerance_ft`: `2,5 cm` quando ha'
**uma** espessura; `min(2,5 cm, gap_minimo/2)` quando ha' duas ou mais.

**FATO MEDIDO:** com `thicknesses_cm = [14.0]` a tolerancia e' 2,5 cm - a
faixa `11,5 .. 16,5 cm` inteira e' "valida", e a espessura gravada e'
sempre 14,0 exatos, independentemente da distancia medida.

### 4. Como o overlap e' calculado

`_line_pair_overlap_ft_cached` devolve `(overlap_ft, len_i, len_j)`;
`overlap_ratio = overlap_ft / min(len_i, len_j)` - **normalizado pela linha
MAIS CURTA**.

**FATO MEDIDO:** **494 dos 589 candidatos tem `overlap_ratio = 1,0000`
exato.** Uma linha de 4,445 cm inteiramente contida na projecao de uma
face de 1.456 cm tambem da' 1,0000. Isto e' o CR-2 do relatorio 2C:
**84% dos candidatos empatam no criterio primario.**

### 5. Como os candidatos sao ordenados

```python
candidates.append(((-overlap_ratio, dist), i, j, matched_thickness))   # ~437
...
candidates.sort(key=lambda c: c[0])                                    # ~440
```

Ascendente: maior `overlap_ratio` primeiro; **no empate, MENOR `dist`
primeiro**. Nao ha' desempate final; a estabilidade do `sort` do Python faz
o resultado depender da ordem de geracao dos candidatos, que por sua vez
depende da ordem das linhas de entrada.

### 6. Quando uma face e' marcada como usada

```python
for _, i, j, matched_thickness in candidates:
    if used[i] or used[j]:
        continue
    centerline = create_centerline(...)
    if centerline:
        ...
        if centerline is not None:
            walls_to_create.append(...)
    used[i] = True          # <-- FORA do `if centerline`
    used[j] = True
```

**As duas faces sao consumidas mesmo que nenhuma parede nasca** (se
`create_centerline` devolver `None`, ou se `clip_centerline_to_caps`
devolver `None`). E' um caminho de roubo silencioso.

**FATO MEDIDO:** neste projeto ele **nao dispara** - 209 pares aceitos
geraram 209 paredes; sob a estrategia corrigida, 203 -> 203. **Defeito
latente, nao ativo.** Registrado, nao corrigido agora.

### 7. Quando um candidato posterior deixa de poder existir

No `if used[i] or used[j]: continue`. Nao ha' repescagem, nao ha' segunda
rodada, nao ha' redistribuicao. **FATO MEDIDO:** 380 candidatos morrem
assim; **52 deles eram pares verdadeiros** (`|d-14| <= 0,05` e `r >= 0,9`).

### 8. Como `locked_ends` entram

Depois do `create_centerline`, `clip_centerline_to_caps` recorta o eixo nas
"testas" desenhadas no CAD e devolve `locked_ends`. **Nao participa do
ranking** - e' aplicado ao vencedor ja' escolhido. A correcao do CR-1 nao o
toca.

### 9. Como as closing lines entram

Sao as mesmas `cap_candidate_lines` (na producao, `lines_to_process`
inteiro). Entram so' em `find_cap_positions` / `clip_centerline_to_caps`,
depois da selecao. **Fora do escopo do CR-1.**

### 10. Como multiplas espessuras sao tratadas hoje

Apenas em dois pontos: `_closest_target_thickness_ft` (elegibilidade +
qual espessura gravar) e `compute_detection_tolerance_ft` (aperta a
tolerancia). **O ranking e' totalmente cego a espessura.** E' exatamente
esse o furo.

---

# B. ONDE, EXATAMENTE, OCORRE O FACE STEALING

Uma unica linha, `wall_pairing.py:437`, combinada com `:440`:

```python
candidates.append(((-overlap_ratio, dist), i, j, matched_thickness))
```

O roubo precisa dos tres ao mesmo tempo, e so' o terceiro decide:

| # | condicao | de onde vem | papel |
|---|---|---|---|
| 1 | varias distancias diferentes sao "validas" | `tol = 2,5 cm` com espessura unica (CR-4) | **cria** a disputa |
| 2 | o candidato errado empata no topo | `overlap_ratio` pela linha mais curta (CR-2) | **coloca** o errado na disputa |
| 3 | **no empate ganha o de MENOR `dist`** | `sort_key[1] = dist` (**CR-1**) | **entrega a vitoria** |
| 4 | a face perdida nunca volta | `used[i] = True` sem repescagem (CR-3) | **torna a perda definitiva** |

**FATO MEDIDO (reproducao minima, `diagnostics_2d/dbg6.py`, caso PAIR-006):**

```
linhas: A = face longa   y=0,     x de    0 a 1456
        B = face real    y=14,    x de    0 a 1681   (par verdadeiro, d=14,000)
        F = folha de porta y=12,1, x de 700 a 704,445 (4,445 cm = 1,75")

candidatos:  A x B  d=14,000  err=0,000  r=1,0000  r_long=0,8662
             A x F  d=12,100  err=1,900  r=1,0000  r_long=0,0031

BASELINE: escolhe A x F  ->  parede com eixo em y = 6,050   (0,95 cm fora)
                             linha B fica ORFA
RANKING CORRIGIDO: escolhe A x B -> parede com eixo em y = 7,000  (exato)
                             linha F fica ORFA
```

Repare que a parede errada **nao e' curta** - `create_centerline` usa as
duas linhas inteiras, entao ela nasce com o comprimento da face longa,
so' que **deslocada de meia espessura**. E' essa a assinatura do pico de
`10-16 cm` de erro de eixo medido na secao K3 da Etapa 2C.

---

# C. OPCOES DE CORRECAO CONSIDERADAS

| id | ideia | atacada |
|---|---|---|
| BASELINE | `(-r, d)` | - |
| A | `(-r, err)` - overlap continua primario, espessura so' desempata | CR-1 parcial |
| B | `(err, -r)` - espessura primaria, erro continuo | CR-1 |
| B2 | `(qerr, -r)` - espessura primaria em baldes de 0,05 cm | CR-1 + determinismo |
| C | `(qerr, -r_long)` - secundario normalizado pela linha mais LONGA | CR-1 + CR-2 |
| C2 | `(qerr, -overlap_absoluto)` | CR-1 + CR-2 |
| C3 | `(qerr, -r_long, -overlap)` | CR-1 + CR-2 |
| E | `(err_normalizado, -r)` - erro relativo a' espessura alvo | CR-1 multi-espessura |
| D | matching global de peso maximo, peso com bonus de cardinalidade | CR-1 + CR-3 |
| D2 | matching global de peso maximo, **sem** bonus de cardinalidade | CR-1 + CR-3 + corte |
| G* | qualquer um acima **+ filtro de qualidade** (`err <= X`, `r_long >= Y`) | CR-2 / CR-4 |

Todos foram simulados sobre **o mesmo conjunto de 589 candidatos**, com o
resto do pipeline real (`create_centerline`, `clip_centerline_to_caps`,
`deduplicate_walls`, `extend_wall_ends_to_junctions`, `build_wall_graph`,
`assign_openings_to_walls`).

---

# D. RESULTADOS DAS SIMULACOES OFFLINE

**FATO MEDIDO** (`diagnostics_2d/run_sim.py` e `run_sim2.py`).
`steal` = candidatos verdadeiros (`err <= 0,05`, `r >= 0,9`) descartados por
ponta ja' usada. `cober` = paredes do gabarito com cobertura `>= 0,85`.

| estrategia | aceit | exato | %exa | err med | err P95 | steal | walls | <50 | %5==4 | cober | ausen | eixoOK | 10-16 | ops |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **BASELINE `(-r,d)`** | 209 | 77 | 37% | 0,842 | 2,032 | **52** | 167 | 31 | 109 | **70** | 11 | **76** | 33 | **82** |
| A `(-r, err)` | 205 | 109 | 53% | 0,483 | 1,535 | 20 | 155 | 29 | 120 | 82 | 5 | 91 | 12 | **91** |
| B `(err, -r)` | 203 | 122 | 60% | 0,394 | 1,500 | 7 | 154 | 25 | 127 | **87** | 4 | **96** | 4 | **91** |
| B2 `(qerr, -r)` | 203 | 122 | 60% | 0,394 | 1,500 | 7 | 154 | 25 | 127 | 87 | 4 | 96 | 4 | 91 |
| C `(qerr, -r_long)` | 203 | 122 | 60% | 0,394 | 1,500 | 7 | 154 | 25 | 127 | 87 | 4 | 96 | 4 | 91 |
| C2 `(qerr, -ov_abs)` | 203 | 122 | 60% | 0,394 | 1,500 | 7 | 154 | 25 | 127 | 87 | 4 | 96 | 4 | 91 |
| C3 `(qerr,-r_long,-ov)` | 203 | 122 | 60% | 0,394 | 1,500 | 7 | 154 | 25 | 127 | 87 | 4 | 96 | 4 | 91 |
| E `(err_n, -r)` | 203 | 122 | 60% | 0,394 | 1,500 | 7 | 154 | 25 | 127 | 87 | 4 | 96 | 4 | 91 |
| **D matching (cardinal)** | 219 | 111 | 51% | 0,578 | 1,996 | 18 | 171 | 39 | 132 | 85 | 6 | 85 | 25 | 91 |
| **D2 matching (qualidade)** | 176 | 122 | 69% | 0,265 | 1,001 | 7 | 133 | 11 | 115 | **87** | 4 | **96** | 2 | **91** |
| GABARITO HUMANO | - | - | - | - | - | - | **97** | **0** | **96** | 97 | 0 | 97 | 0 | 91 |

### D1. As tres leituras que mudam a decisao

**(1) B, B2, C, C2, C3 e E dao resultado IDENTICO.** Assim que o erro de
espessura vira criterio primario, **o criterio secundario deixa de
importar** neste projeto.

**FATO MEDIDO** (`run_sim3.py`): das 286 linhas disputadas por dois ou mais
candidatos, **224 (78%) sao decididas pelo erro de espessura sozinho**;
so' 62 chegam a ter dois candidatos no mesmo balde de 0,05 cm. E nessas 62,
qualquer um dos secundarios testados escolhe o mesmo par.

**Consequencia pratica: nao ha' motivo medido para trocar `overlap_ratio`
por `r_long`.** Trocar so' adiciona risco (ver D2 abaixo). Mantem-se o
`overlap_ratio` atual, apenas rebaixado a criterio secundario.

**(2) O ganho de D2 nao vem do matching global - vem de um FILTRO.** O peso
usado em D2 (`10*r_long - 100*err_n`) e' negativo para candidatos ruins,
entao o matching simplesmente **os recusa**. Separando os dois efeitos:

| | aceit | exato | cober | eixoOK | espur | ops |
|---|---|---|---|---|---|---|
| **guloso** `(qerr,...)` + o mesmo filtro | 176 | 122 | 87 | 96 | 2 | 91 |
| **matching global** com o mesmo peso | 176 | 122 | 87 | 96 | 2 | 91 |

**Sao o mesmo resultado.** O guloso com ranking corrigido ja' encontra o
otimo global neste conjunto de candidatos. **Matching global nao acrescenta
nada** (item F).

**(3) Piso de `r_long` (a "correcao do CR-2") faz MAL.**

| filtro | cober | ops | paredes do gabarito PERDIDAS vs baseline |
|---|---|---|---|
| nenhum | 87 | 91 | 0 |
| `err <= 1,5` | 87 | 91 | 0 |
| `err <= 1,0` | 86 | 91 | 1 (**W074**) |
| **`r_long >= 0,30`** | 83 | **87** | 2 (**W001, W068**) |
| **`r_long >= 0,50`** | 82 | **87** | 3 (W001, W037, W068) |

**FATO MEDIDO - por que:** W001 e W068 (424 cm cada) sao formadas por uma
face de **1.513,15 cm** contra uma de **424,00 cm** -> `r_long = 0,2802`,
`r = 1,0000`, `d = 13,999`. Sao paredes **legitimas e perfeitas na
espessura**, e qualquer piso de `r_long` as mata. **O docstring atual, que
avisa que o desempate existia para nao roubar a face de uma boneca curta,
estava certo sobre o risco - so' errado sobre o remedio.**

**FATO MEDIDO - W074:** seu **unico** candidato plausivel tem
`d = 15,060 cm` (`err = 1,060`), `r = 1,0000`, `r_long = 1,0000`. E' uma
parede real desenhada com 15,06 cm de vao entre faces. Um corte em
`err <= 1,0` a elimina; `err <= 1,5` a preserva.

### D2. Recuperacao das 6 paredes do trace das 9 aberturas (criterio R3 da Etapa 2C)

**FATO MEDIDO** - cobertura, `0,00` = nao existe:

| parede | L (cm) | BASELINE | ranking corrigido | + `err<=1,5` | + `err<=1,0` |
|---|---|---|---|---|---|
| W012 | 1484 | 0,00 | **1,00** | 1,00 | 1,00 |
| W036 | 524 | 0,01 | **1,00** | 1,00 | 1,00 |
| W038 | 524 | 0,01 | **1,00** | 1,00 | 1,00 |
| W057 | 304 | 0,00 | **0,99** | 0,99 | 0,99 |
| W072 | 384 | 0,00 | **1,00** | 1,00 | 1,00 |
| W073 | 384 | 0,00 | **1,00** | 1,00 | 1,00 |

**As 6 sao recuperadas apenas pelo ranking.**

### D3. Nao-regressao (criterio R10 da Etapa 2C)

**FATO MEDIDO** - das 70 paredes do gabarito hoje COBERTAS, quantas deixam
de ser:

| estrategia | cobertas | perdidas vs baseline | ganhas |
|---|---|---|---|
| ranking corrigido | 87 | **0** | 17 |
| + `err <= 1,5` | 87 | **0** | 17 |
| + `err <= 1,0` | 86 | 1 (W074) | 17 |
| + `r_long >= 0,30` | 83 | 2 (W001, W068) | 15 |
| matching global (cardinal) | 85 | 0 | 15 |

### D4. Distribuicao de comprimento das paredes finais

**FATO MEDIDO:**

| faixa | BASELINE | ranking | + err<=1,5 | + err<=1,0 | GABARITO |
|---|---|---|---|---|---|
| < 20 cm | 22 | 19 | 18 | 8 | **0** |
| 20-50 cm | 9 | 6 | 2 | 3 | **0** |
| 50-100 | 29 | 25 | 25 | 25 | 13 |
| 100-200 | 38 | 33 | 31 | 30 | 19 |
| 200-400 | 42 | 38 | 38 | 38 | 31 |
| > 400 | 27 | 33 | 33 | 33 | 34 |
| **total** | 167 | 154 | 147 | 137 | **97** |
| **soma (cm)** | 43.033 | 46.373 | 45.878 | 45.642 | **45.363** |
| `len % 5 == 4` | 109 | 127 | 125 | 121 | **96** |

O ranking corrigido aproxima **todas** as faixas do gabarito e leva a soma
de comprimento de `-2.330 cm` para `+1.010 cm` do alvo. As paredes < 50 cm
caem de 31 para 25 - **melhoram, mas nao acabam** (item J).

### D5. Tempo de execucao

**FATO MEDIDO:** nenhuma estrategia mexe no custo dominante.

| etapa | tempo |
|---|---|
| `merge_collinear_fragments` (9258 -> 2868) | 12,37 s |
| varredura O(n^2) de candidatos (4.111.278 pares) | **5,55 s** |
| ordenacao dos 589 candidatos - BASELINE | 0,00042 s |
| ordenacao dos 589 candidatos - ranking corrigido | 0,00045 s |
| matching global exato (133 componentes, maior = 25 arestas) | +0,5 s |

---

# E. RECOMENDACAO

**Adotar o ranking B2/C3 (erro de espessura primario, em baldes de
0,05 cm; `overlap_ratio` atual como secundario), guloso, sem filtro
adicional, num commit isolado.**

Justificativa medida:

1. **Maior efeito por menor mudanca.** Uma expressao. Nao muda o conjunto
   de candidatos, nao muda nenhuma tolerancia, nao muda nenhuma constante
   de geometria, nao muda `overlap_ratio`.
2. **Zero regressao medida** (D3): as 70 paredes hoje cobertas continuam
   cobertas, as 82 aberturas hoje atribuidas continuam atribuidas.
3. **Resolve as 9 aberturas por completo** e as **6 paredes do trace**.
4. **Nao introduz risco de boneca** - `overlap_ratio` continua sendo o
   criterio de qualidade, exatamente como o docstring queria.
5. Deixa o proximo passo (filtro por `err <= 1,5`) medivel de forma
   isolada, como a Etapa 2C exigiu ("nunca dois de uma vez").

**Rejeitados, com o motivo medido:**

| opcao | por que nao |
|---|---|
| A `(-r, err)` | so' 53% de espessura exata e 82 cobertas - o overlap continua sequestrando o topo (494 candidatos empatam em `r = 1,0000`) |
| C/C2/C3 com `r_long` | resultado identico a B2 neste projeto, mas troca uma metrica testada por outra sem ganho medido |
| D (matching, cardinalidade) | **pior** que o guloso: 85 cobertas, 25 eixos a 10-16 cm, 39 paredes < 50 cm |
| D2 / matching com peso de qualidade | empata com o guloso + filtro; complexidade sem ganho (item F) |
| qualquer piso de `r_long` | mata W001, W068 e 4 aberturas (D1.3) |
| `err <= 1,0` | mata W074 (unico candidato a 15,06 cm) |

---

# F. GULOSO CORRIGIDO E' SUFICIENTE? MATCHING GLOBAL E' NECESSARIO?

**Nao e' necessario. FATO MEDIDO.**

Sob o **mesmo** conjunto de candidatos e o **mesmo** criterio de qualidade,
o guloso e o matching global de peso maximo produzem **exatamente o mesmo
resultado** (176 pares / 122 exatos / 87 cobertas / 96 eixos corretos /
2 espurias / 91 aberturas).

Motivo estrutural, medido: o grafo de candidatos e' **quase uma uniao de
casamentos triviais**. 589 arestas em **133 componentes conexas**; a maior
tem 25 arestas; 38 componentes tem 1 aresta so'. Nessas condicoes um guloso
com ordem correta e' otimo na pratica.

E o matching global **piora** quando o peso premia cardinalidade
(estrategia D): 219 pares, 39 paredes < 50 cm, 25 eixos a 10-16 cm. Isso e'
esperado - maximizar o numero de pares e' o objetivo errado; queremos
maximizar a *qualidade* dos pares.

**Conclusao:** manter guloso. Matching global fica registrado como
alternativa avaliada e descartada **por evidencia**, nao por preferencia.

---

# G. FORMULA EXATA DE RANKING PROPOSTA

```python
# constante nova, em nuvem/core/engine/tolerances.py
# Baldes de erro de espessura para o ranking de find_wall_pairs. Dois pares
# cujo erro de espessura difere menos que isto sao considerados IGUALMENTE
# corretos em espessura, e o desempate volta a ser a sobreposicao.
# 0,05 cm e' o mesmo limiar que o benchmark usa para "espessura exata".
THICKNESS_RANK_BUCKET_M  = 0.0005          # 0,05 cm
THICKNESS_RANK_BUCKET_FT = THICKNESS_RANK_BUCKET_M * FEET_PER_METER
```

```python
# em find_wall_pairs, no lugar do append atual (~437)
thickness_error = abs(dist - matched_thickness)
thickness_rank  = int(thickness_error / THICKNESS_RANK_BUCKET_FT)

sort_key = (
    thickness_rank,      # 1o  - o par que MEDE a espessura pedida vence
    -overlap_ratio,      # 2o  - entre igualmente corretos, o que corre mais lado a lado
    -overlap_ft,         # 3o  - sobreposicao absoluta (desempate util)
    i, j,                # 4o  - determinismo total
)
candidates.append((sort_key, i, j, matched_thickness))
```

`candidates.sort(key=lambda c: c[0])` fica como esta'.

**O que MUDA:** so' a expressao do `sort_key`.
**O que NAO muda:** os 6 testes de elegibilidade, `overlap_ratio`,
`MIN_WALL_SEGMENT_OVERLAP_RATIO`, `MIN_WALL_SEGMENT_ABS_FLOOR_FT`,
`WALL_DETECTION_TOLERANCE_FT`, `compute_detection_tolerance_ft`,
`create_centerline`, `clip_centerline_to_caps`, `deduplicate_walls`,
`assign_openings_to_walls`, e o consumo `used[i] = used[j] = True`.

### Por que balde inteiro e nao o erro continuo

Medido: `(err, -r)` e `(qerr, -r)` dao resultado identico. O balde e'
preferido por dois motivos **de projeto**, nao de resultado:

1. Com erro continuo (float), empate exato quase nunca acontece -> o
   criterio de sobreposicao viraria letra morta. O balde faz o secundario
   voltar a decidir nos 62 casos em que ele deve decidir.
2. Ruido de ponto flutuante de `1e-12 cm` deixa de reordenar o ranking.

---

# H. TRATAMENTO DE MULTIPLAS ESPESSURAS

`matched_thickness` **ja' e' o `closest_allowed_thickness`** - vem de
`_closest_target_thickness_ft`, que ja' escolhe, entre as espessuras
selecionadas, a mais proxima dentro da tolerancia.

Definicao formal proposta:

```
target_thickness  = _closest_target_thickness_ft(dist, thicknesses, tol)   # ja' existe
thickness_error   = abs(dist - target_thickness)                            # ABSOLUTO, em pes
thickness_rank    = int(thickness_error / THICKNESS_RANK_BUCKET_FT)
```

Exemplo pedido: `dist = 13,9 cm`, `allowed = [9, 14, 19]` ->
`target = 14`, `thickness_error = 0,1 cm`, `rank = 2`.
`dist = 16,4 cm` -> `target = 14` (`19` esta' a 2,6 cm, fora da tolerancia
de 2,5) -> `error = 2,4 cm`, `rank = 48`. **Ele nao ganha de ninguem so'
por ser geometricamente valido** - fica 46 baldes atras do de 13,9.

### Absoluto ou normalizado (`err / target`)?

**Recomendacao: ABSOLUTO.** Motivos:

1. **FATO MEDIDO:** com `[14.0]` as duas formas dao resultado identico
   (estrategia E == estrategia B). Este projeto **nao consegue
   discriminar** - a escolha tem que ser por argumento, e o argumento e'
   declarado, nao escondido.
2. **Argumento geometrico:** o erro que se esta' medindo e' imprecisao de
   desenho no CAD (posicao da linha em mm). E' um erro **absoluto**, nao
   proporcional. Uma parede de 9 cm e uma de 24 cm desenhadas com o mesmo
   descuido erram os mesmos milimetros.
3. **A separacao entre espessuras ja' esta' garantida a montante:**
   `compute_detection_tolerance_ft` limita a tolerancia a metade do menor
   intervalo entre espessuras escolhidas. Com `[9,14,19]` a tolerancia e'
   2,5 cm; com `[12,14]` ela cai para 1,0 cm. **Nenhum candidato pode ser
   ambiguo entre dois alvos** - logo o ranking nunca precisa comparar
   erros de alvos diferentes em escalas diferentes.
4. Normalizar favoreceria sistematicamente as paredes **grossas** num
   projeto misto (`0,5 cm` em 24 vale menos que `0,5 cm` em 9), sem que
   ninguem tenha pedido isso.

**PENDENCIA (nao bloqueia):** quando existir um projeto real com duas ou
mais espessuras no mesmo layer, re-medir absoluto x normalizado. Registrado
em `nuvem/REGRAS_MODULACAO_BLOCOS.md` secao 26.

**FATO MEDIDO** (fixture sintetica, `run_sim4.py`):

| caso | espessuras | resultado esperado | BASELINE | proposto |
|---|---|---|---|---|
| PAIR-004 | `[9,14,19]`, uma parede de 9 e uma de 14 | 9 e 14 | OK | OK |
| PAIR-011 | `[19,9,14]` (ordem embaralhada) | 9 e 14 | OK | OK |
| PAIR-012 | `[12,14]` (tol aperta para 1,0 cm) | escolhe 12 | OK | OK |

---

# I. COMPORTAMENTO EM EMPATES

Ordem de decisao, do primario ao ultimo:

1. **`thickness_rank`** - decide 78% das disputas sozinho (medido).
2. **`-overlap_ratio`** - decide os 62 casos restantes de disputa.
3. **`-overlap_ft`** - sobreposicao absoluta; separa "toco totalmente
   contido" de "face longa totalmente lado a lado" quando `overlap_ratio`
   tambem empata em 1,0000.
4. **`(i, j)`** - desempate final **deterministico e total**. Garante que
   duas execucoes sobre a mesma entrada dao o mesmo resultado byte a byte,
   independentemente da estabilidade do `sort`.

O item 4 e' novo: **hoje nao existe desempate final**, e a Etapa 2C ja'
tinha registrado a instabilidade (o replay devolvia 208 em vez de 209 so'
por ordem de insercao). Com `(i, j)` isso acaba.

---

# J. TRATAMENTO DAS LINHAS DE ESQUADRIA

**FATO MEDIDO** (`run_sim3.py`) - pares aceitos com uma linha curta:

| | aceitos | com linha < 20 cm | curta(<20) x longa(>=100) | paredes < 20 cm |
|---|---|---|---|---|
| BASELINE | 209 | 51 | **30** | 22 |
| ranking corrigido | 203 | 43 | **20** | 19 |
| + `err <= 1,0` | 165 | 22 | **9** | 8 |

**Resposta direta: o ranking corrigido MELHORA mas NAO RESOLVE.** Sobram
20 pares curta x longa, dos quais **10 estao a `err = 1,5 cm`** (faces a
12,5 ou 15,5 cm). Como estao todos no mesmo balde alto de erro, eles so'
vencem quando **nao ha' concorrente melhor para aquela face** - isto e', ja'
nao roubam mais nada; apenas criam paredes espurias proprias.

**A segunda protecao, quando for a hora, deve ser um corte por ERRO DE
ESPESSURA, nao por comprimento de linha.** Justificativa medida:

- e' generalizavel: nao cita 4,445 nem 5,08; funciona para qualquer
  espessura e qualquer esquadria;
- **nao mata boneca legitima**: `err <= 1,5` preserva W001, W068 e W074, e
  mantem cobertura 87 e 91/91 aberturas;
- um piso de comprimento ou de `r_long` **mata** paredes reais (D1.3) -
  esta' medido, nao e' teoria.

**PROIBIDO** (registrado para a proxima sessao): filtro por `4,445`, por
`5,08`, por "comprimento de folha de porta", ou qualquer numero extraido
deste projeto especifico. Isso e' overfitting ao `torre_easy_lo_r00_tgd`.

**Numeros do candidato de segunda etapa (`err <= 1,5 cm`), ja' medidos:**
192 pares aceitos, 122 exatos (64%), `err` medio 0,322, P95 **1,020**,
147 paredes, **20** paredes < 50 cm, 87 cobertas, 96 eixos corretos,
91/91 aberturas, **zero regressao R10**.

---

# K. IMPACTO ESPERADO NAS 9 ABERTURAS

**FATO MEDIDO: as 9 sao resolvidas, 91 de 91 atribuidas.**

| abertura | classificacao 2C | com o ranking corrigido |
|---|---|---|
| 6558406 | `WALL_PAIRING_FACE_STOLEN` (W012) | **atribuida** - W012 passa a cobertura 1,00 |
| 6558407 | `WALL_PAIRING_FACE_STOLEN` (W012) | **atribuida** |
| 6558433 | `WALL_PAIRING_FACE_STOLEN` (W012) | **atribuida** |
| 6558426 | `WALL_PAIRING_FACE_STOLEN` (W036) | **atribuida** - W036 cobertura 1,00 |
| 6558458 | `WALL_PAIRING_FACE_STOLEN` (W038) | **atribuida** - W038 cobertura 1,00 |
| 6558411 | `WALL_PAIRING_WRONG_AXIS` (W072) | **atribuida** - eixo volta ao lugar |
| 6558461 | `WALL_PAIRING_WRONG_AXIS` (W073) | **atribuida** |
| 6558475 | `WALL_PAIRING_WRONG_AXIS` (W057) | **atribuida** |
| 6558476 | `WALL_PAIRING_WRONG_AXIS` (W057) | **atribuida** |

Mais a 6558432, que o baseline tambem perdia (a lista medida de nao
atribuidas do baseline e' `6558406, 6558407, 6558411, 6558426, 6558432,
6558458, 6558461, 6558475, 6558476`). Total: **82 -> 91**.

**`assign_openings_to_walls` NAO e' tocado.** As 9 passam como
*consequencia* de a parede existir no eixo certo, exatamente como a Etapa
2C previu.

---

# L. IMPACTO ESPERADO NAS 167 WALLS

| metrica | hoje | depois (medido) | gabarito |
|---|---|---|---|
| paredes finais | 167 | **154** | 97 |
| paredes < 50 cm | 31 | **25** | 0 |
| paredes < 20 cm | 22 | **19** | 0 |
| eixo correto (<= 0,5 cm) | 76 (45,5%) | **96 (62%)** | 97 |
| eixo a 10-16 cm (assinatura do defeito) | 33 | **4** | 0 |
| espurias (sem eixo de gabarito por perto) | 5 | 6 | 0 |
| `len % 5 == 4` | 109 | **127** | 96 de 97 |
| soma de comprimento | 43.033 cm | **46.373 cm** | 45.363 cm |
| duplicatas removidas por `deduplicate_walls` | 42 | 49 | - |

Leitura honesta: **o resultado nao vira o gabarito.** 154 nao e' 97, e
25 paredes < 50 cm continuam existindo. O que muda e' que **as paredes que
existem passam a estar no lugar certo** (eixo 10-16 cm cai de 33 para 4) e
**as que faltavam passam a existir** (cobertura 70 -> 87). O excesso
remanescente e' materia do CR-2/CR-4, nao do CR-1.

---

# M. IMPACTO ESPERADO EM PERFORMANCE

**Nenhum mensuravel.**

| | BASELINE | proposto |
|---|---|---|
| complexidade da varredura | `O(n^2)` | `O(n^2)` **inalterada** |
| pares avaliados | 4.111.278 | 4.111.278 |
| tempo da varredura | 5,55 s | 5,55 s |
| tempo da ordenacao (589 candidatos) | 0,42 ms | 0,45 ms |
| operacoes novas por candidato | - | 1 subtracao, 1 `abs`, 1 divisao, 1 `int` |
| pico de memoria | 589 tuplas de 4 | 589 tuplas de 4 (chave com 5 campos em vez de 2) |

O custo dominante do Wall Modeling continua sendo
`merge_collinear_fragments` (12,4 s) e a varredura `O(n^2)` (5,5 s) -
**nenhum dos dois e' tocado**.

Matching global, se algum dia for necessario: 133 componentes conexas,
maior com 25 arestas, custo medido +0,5 s com busca exata por componente.
Fica registrado que **e' barato**, so' que **inutil** (item F).

---

# N. ARQUIVOS E FUNCOES QUE A IMPLEMENTACAO DEVERA ALTERAR

| arquivo | ponto | mudanca |
|---|---|---|
| `nuvem/core/engine/tolerances.py` | fim do bloco de constantes de pareamento | **acrescentar** `THICKNESS_RANK_BUCKET_M/_FT` com comentario explicativo |
| `nuvem/core/engine/wall_pairing.py` | import de `tolerances` (~29-39) | acrescentar a constante nova a' lista |
| `nuvem/core/engine/wall_pairing.py` | `find_wall_pairs`, `candidates.append` (~437) | **a mudanca** - novo `sort_key` |
| `nuvem/core/engine/wall_pairing.py` | docstring de `find_wall_pairs` (~289-297) | reescrever o paragrafo do desempate: hoje ele descreve o comportamento **oposto** ao correto |
| `tests/test_script.py` | novos casos | acrescentar PAIR-001..012 + CR-1 (item O/P) |
| `nuvem/benchmark/projects/torre_easy_lo_r00_tgd/baselines/baseline_real_v1.json` | `wall_modeling_engine_sha256` | **re-emitir de proposito**, em commit separado |

**NAO alterar** (fora do escopo do CR-1, confirmado por medicao):

- `scan_possible_missed_bonecas` - tem o mesmo `(-overlap_ratio, dist)`,
  mas **nao tem espessura alvo** (varre deliberadamente fora das
  espessuras escolhidas) e **nao cria parede nenhuma**, so' reporta.
  `thickness_error` nao esta' definido ali. **Deixar como esta'.**
- `compute_detection_tolerance_ft`, `WALL_DETECTION_TOLERANCE_FT` (CR-4)
- `MIN_WALL_SEGMENT_OVERLAP_RATIO`, `MIN_WALL_SEGMENT_ABS_FLOOR_FT` (CR-2)
- `deduplicate_walls` (CR-6)
- `merge_collinear_fragments`, `assign_openings_to_walls`, catalogo,
  compensadores, prisma, amarracoes, tolerancias de abertura
- `used[i] = used[j] = True` fora do `if centerline` - defeito latente,
  medido como **inativo** neste projeto (A.6). Anotar como pendencia.

---

# O. LISTA DE TESTES MINIMOS

Todos headless, com os stubs de `tests/revit_stubs.py`, no formato dos
testes que ja' existem em `tests/test_script.py`.

| # | caso | montagem | criterio |
|---|---|---|---|
| PAIR-001 | par unico exato | faces a `y=0` e `y=14`, 400 cm | 1 parede, esp 14, eixo `y=7,0` |
| PAIR-002 | 12 x 14 disputando a mesma face | `y=0`, `y=12`, `y=14` | vence o de 14; eixo `y=7,0`; a linha de `y=12` fica orfa |
| PAIR-003 | 14 x 16 disputando a mesma face | `y=0`, `y=14`, `y=16` | vence o de 14; eixo `y=7,0` |
| PAIR-004 | `[9,14,19]`, uma parede de 9 e outra de 14 | duas paredes separadas | 2 paredes, esp 9 e 14, cada uma no seu eixo |
| PAIR-005 | face central compartilhada | `y=0`, `y=14`, `y=28` | **documenta o comportamento atual**: 1 parede so'; a face central e' exclusiva. NAO e' requisito de CR-1 - e' CR-3 |
| PAIR-006 | **CR-1** | ver item P | ver item P |
| PAIR-007 | encontro em T | duas paredes de 14 formando T | 2 paredes, eixos corretos |
| PAIR-008 | encontro em L | duas paredes de 14 formando L | 2 paredes, eixos corretos |
| PAIR-009 | boneca curta perto de porta | face de 1.513 cm x face de 424 cm a `d=14` (`r_long = 0,28`), mais um toco a `d=12` | **a boneca vence** - blindagem contra a tentacao de por piso de `r_long` (caso real: W001/W068) |
| PAIR-010 | ordem das linhas embaralhada | PAIR-002 com as 3 linhas em outra ordem | resultado identico ao PAIR-002 |
| PAIR-011 | ordem das espessuras embaralhada | PAIR-004 com `[19, 9, 14]` | resultado identico ao PAIR-004 |
| PAIR-012 | espessuras vizinhas | `[12, 14]`, faces a `y=0`, `y=12`, `y=14`; tolerancia cai para 1,0 cm | forma a parede de 12; nenhuma ambiguidade |
| PAIR-013 | espessura verdadeira fora do balde 0 | face unica a `d = 15,06` com `[14]` | **cria** a parede (esp 14) - blindagem contra a tentacao de por corte em `err <= 1,0` (caso real: W074) |
| PAIR-014 | determinismo | qualquer caso com 3+ candidatos, executado 2x | resultado byte a byte identico |

**FATO MEDIDO:** PAIR-001, 002, 003, 004, 007, 010, 011 e 012 **ja' passam
hoje** no baseline (o defeito nao aparece em geometria limpa) - e devem
continuar passando. Os que **so'** passam depois da correcao sao PAIR-006
e PAIR-009/013 na variante com concorrencia.

Os 3 testes de `find_wall_pairs` que ja' existem em `tests/test_script.py`
**continuam passando** com o `sort_key` proposto - verificado por analise:

- `test_par_de_linhas_vira_uma_parede_no_eixo`: candidato unico.
- `test_espessura_fora_da_tolerancia_nao_vira_parede`: nenhum candidato.
- `test_find_wall_pairs_prioridade_preservada_apos_otimizacao_de_performance`:
  A-B (`d=14`, `r=1,0`) e B-D (`d=14`, `r=0,5`) tem **o mesmo**
  `thickness_rank = 0`; o desempate cai em `-overlap_ratio` e A-B vence,
  como hoje. **Este teste continua verde e vira, de brinde, o teste do
  criterio secundario.**

---

# P. TESTE MINIMO ESPECIFICO DE CR-1 (PAIR-006)

**Desenho conceitual - ja' validado nesta sessao em
`diagnostics_2d/dbg6.py`:**

```
      y = 14,0   B ---------------------------------------------  (0 .. 1681)   face verdadeira
      y = 12,1                   F ---                            (700 .. 704,445)   folha de porta
      y =  0,0   A ------------------------------                 (0 .. 1456)   face longa

      espessuras escolhidas: [14,0]      tolerancia de deteccao: 2,5 cm
```

Candidatos gerados (medidos):

| par | `dist` | `thickness_error` | `overlap_ratio` | `r_long` |
|---|---|---|---|---|
| A x B | 14,000 | **0,000** | 1,0000 | 0,8662 |
| A x F | 12,100 | 1,900 | **1,0000** | 0,0031 |

Os dois empatam em `overlap_ratio = 1,0000` - e' por isso que o desempate
decide sozinho.

| | ordem de avaliacao | parede criada | linha orfa |
|---|---|---|---|
| **hoje** | A x F primeiro (`d` menor) | eixo em **`y = 6,050`** | **B** (a face verdadeira) |
| **corrigido** | A x B primeiro (`err` menor) | eixo em **`y = 7,000`** | F (a folha de porta) |

**Assercoes do teste:**

```
1. len(walls) == 1
2. abs(to_cm(eixo.Y) - 7.0) < 0.01        # <-- FALHA hoje: da' 6,050
3. abs(to_cm(thickness_ft) - 14.0) < 0.01
4. unused == [F]                          # <-- FALHA hoje: da' [B]
```

**Atencao ao redigir:** o discriminante e' a **posicao do eixo** e **qual
linha sobrou**, NAO o comprimento da parede. `create_centerline` usa as
duas linhas inteiras, entao a parede errada tambem nasce com 1.456 cm - um
teste que so' olhasse comprimento **passaria nos dois casos** e nao provaria
nada. (Foi exatamente esse o erro cometido na primeira versao desta
fixture nesta sessao, e o motivo de ele estar escrito aqui.)

---

# Q. TESTES DE INVARIANCIA

**FATO MEDIDO nesta sessao** (`run_sim4.py`), aplicando a transformacao as
2.868 linhas ja' mescladas e destransformando o resultado:

| transformacao | BASELINE | ranking corrigido |
|---|---|---|
| rotacao 90 graus | identico | **identico** |
| rotacao 180 graus | identico | **identico** |
| rotacao 270 graus | identico | **identico** |
| translacao (+1234,5 / -411,5 pes) | **DIFERE** (-28/+27 paredes) | **identico** |
| inversao de endpoints | **DIFERE** (6 pares diferentes) | **identico** (0 pares diferentes) |
| ordem das linhas embaralhada | **DIFERE** (-50/+52) | DIFERE (-25/+23) |

**Duas leituras importantes:**

1. **O ranking corrigido e' MAIS invariante que o atual**, nao menos.
   Translacao e inversao de endpoints deixam de mudar o resultado.
2. **A nao-invariancia a' ordem das linhas nao e' do `find_wall_pairs`.**
   Medido: embaralhar as 9.258 linhas de entrada muda a saida do
   `merge_collinear_fragments` (`2868 -> 2879 / 2873`) e o proprio numero
   de candidatos (`589 -> 609 / 586`). Embaralhando so' as 2.868 linhas ja'
   mescladas, o numero de candidatos ainda oscila (`589 -> 583`), o que
   indica **assimetria em `i`/`j` nos predicados geometricos**
   (`_are_parallel_cached` / `_line_pair_overlap_ft_cached`).
   **PENDENCIA NOVA, fora do escopo do CR-1, registrada como
   `ORDER_DEPENDENCE_MERGE_COLLINEAR_FRAGMENTS`** (secao 26.6 das regras) -
   registrar, nao corrigir agora, nao misturar num futuro commit de core
   junto com CR-1 nem com qualquer outra correcao.

**Testes a escrever:**

| # | teste | criterio |
|---|---|---|
| INV-01 | rotacao 90/180/270 graus da planta | pares escolhidos identicos; eixos identicos apos destransformar |
| INV-02 | translacao arbitraria | idem |
| INV-03 | inversao dos endpoints de todas as linhas | **pares escolhidos identicos** (hoje falha) |
| INV-04 | espelhamento em X e em Y | idem |
| INV-05 | `thicknesses_cm` em ordem embaralhada | resultado identico (`[9,14,19]` == `[19,9,14]`) |
| INV-06 | mesma entrada, duas execucoes | byte a byte identico |
| INV-07 | ordem das linhas ja' mescladas embaralhada | **marcar `xfail` com o motivo**: `ORDER_DEPENDENCE_MERGE_COLLINEAR_FRAGMENTS`, pendencia separada. NAO tentar consertar dentro do CR-1 |

INV-01..06 devem ser HARD. INV-07 entra como `xfail` documentado para nao
mascarar um defeito real nem bloquear o CR-1.

---

# R. CRITERIOS **HARD** DE APROVACAO

Todos medidos sobre `torre_easy_lo_r00_tgd`, FASE A headless. Os numeros de
hoje estao entre parenteses. **Qualquer um que falhe reprova a correcao.**

| # | requisito | hoje | alvo HARD |
|---|---|---|---|
| H1 | **Nao-regressao de cobertura**: nenhuma das 70 paredes do gabarito hoje COBERTAS deixa de ser | 70 | **>= 70, com as mesmas 70 dentro** |
| H2 | **Nao-regressao de abertura**: nenhuma das 82 hoje atribuidas fica sem parede | 82 | **as mesmas 82 continuam atribuidas** |
| H3 | **PAIR-006** (item P) passa | falha | **passa** |
| H4 | **PAIR-009 e PAIR-013** (boneca `r_long=0,28` e parede a 15,06 cm) passam | passam | **continuam passando** |
| H5 | Todos os testes de `tests/test_script.py` continuam verdes | verde | **verde** |
| H6 | Determinismo (INV-06): duas execucoes -> `wall_modeling_snapshot.json` byte a byte igual | instavel (208/209) | **estavel** |
| H7 | Invariancia INV-01..05 | translacao e inversao falham | **passam** |
| H8 | Eixo correto (<= 0,5 cm) | 76/167 | **>= 90 paredes** |
| H9 | Eixo a 10-16 cm (assinatura do defeito) | 33 | **<= 8** |
| H10 | As 6 paredes do trace com cobertura >= 0,85 | 0 de 6 | **6 de 6** |
| H11 | Espessura exata entre os pares aceitos | 77 (37%) | **>= 55%** |
| H12 | Runtime da FASE A nao piora mais de 10% | ~18 s | **<= 20 s** |
| H13 | `find_wall_pairs` continua `O(n^2)` | sim | **sim** |
| H14 | Nenhuma edicao fora dos arquivos do item N | - | **nenhuma** |

**Valores medidos da estrategia recomendada:** H1 = 87 (0 perdidas),
H2 = 82 de 82, H3 passa, H8 = **96**, H9 = **4**, H10 = **6 de 6**,
H11 = **60%**, H12 ~18 s. **Todos os HARD sao atendidos com folga.**

# S. METRICAS **SOFT** DE MELHORIA

Nao reprovam sozinhas; sao a evidencia de que a direcao esta' certa.

| # | metrica | hoje | esperado (medido) | gabarito |
|---|---|---|---|---|
| S1 | paredes do gabarito COBERTAS | 70 | **87** | 97 |
| S2 | paredes do gabarito AUSENTES | 11 | **4** | 0 |
| S3 | aberturas atribuidas | 82 | **91** | 91 |
| S4 | erro medio de espessura dos aceitos | 0,842 cm | **0,394 cm** | 0 |
| S5 | erro P95 de espessura | 2,032 cm | **1,500 cm** | 0 |
| S6 | roubos de face (pares verdadeiros descartados) | 52 | **7** | 0 |
| S7 | paredes < 50 cm | 31 | **25** | 0 |
| S8 | paredes finais | 167 | **154** | 97 |
| S9 | `len % 5 == 4` | 109 | **127** | 96 |
| S10 | pares "curta(<20) x longa(>=100)" | 30 | **20** | 0 |
| S11 | soma de comprimento | 43.033 cm | **46.373 cm** | 45.363 cm |

**PROIBIDO usar `success_rate` do solver como criterio nesta etapa.** Hoje
ele e' 0,0659 medido sobre 167 paredes, 31 das quais nao deveriam existir.
Criando W012 (1.484 cm) entram milhares de blocos novos e o numero
provavelmente **piora** - o que seria uma leitura errada de uma geometria
que ficou melhor. Avaliar por S1/S2/S3 enquanto a FASE A estiver mudando
(regra ja' registrada na Etapa 2C, secao S).

---

# T. RISCOS DE REGRESSAO

| risco | severidade | evidencia | mitigacao |
|---|---|---|---|
| **Perder boneca curta legitima** (o motivo pelo qual o desempate por menor `dist` existia) | **alta** se mal feita | W001/W068: `r_long = 0,28`, `r = 1,0`, `d = 13,999`. Um piso de `r_long >= 0,30` as mata e leva 4 aberturas junto | **nao mexer em `overlap_ratio`**; PAIR-009 como teste travado; H1 |
| **Perder parede real fora do balde 0** | media | W074: unico candidato a `d = 15,060` | **nao introduzir corte por `err`** neste commit; PAIR-013; H4 |
| **Empates instaveis / nao determinismo** | media | replay ja' devolvia 208 vs 209 por ordem de insercao | desempate final `(i, j)`; H6/INV-06 |
| **Quebrar `wall_modeling_engine_sha256` e o baseline** | certa | `f0171249...` muda com qualquer edicao no motor | re-emitir `baseline_real_v1` **num commit separado**, guardando o par antigo/novo no commit message |
| **`success_rate` cair e ser lido como piora** | alta (interpretacao) | 0,0659 e' medido sobre paredes que nao deveriam existir | S-regra: avaliar por cobertura, nao por `success_rate` |
| **Mais paredes = mais blocos = mais tempo no solver** | media | 46.373 cm vs 43.033 cm | H12 mede a FASE A; medir o solver a parte |
| **Corrigir CR-1 e CR-2/CR-4 juntos** | alta | o benchmark nao consegue atribuir credito | **um por commit**, com medicao entre eles (regra da Etapa 2C, secao P) |
| **Achar que o problema acabou** | media | sobram 25 paredes < 50 cm, 154 != 97, 6 espurias | S7/S8 ficam como pendencia explicita para CR-2/CR-3 |
| Regressao em projeto que hoje funciona bem | **desconhecida** | ver item U (cross-project) | rodar a suite completa + PAIR-001..014 |

---

# T2. CLASSIFICACAO DA SOLUCAO - NAO E' PROVA UNIVERSAL

Para nao supergeneralizar o resultado da secao D:

**O ranking corrigido foi validado PROFUNDAMENTE no caso real
`torre_easy_lo_r00_tgd`** (589 candidatos reais, 6 paredes do trace, 9
aberturas, R10 de nao-regressao, invariancia geometrica) **e em fixture
sintetica cobrindo T/L/multi-espessura/ordem embaralhada (item O/P)**.

**Isso NAO e' prova de que a solucao funciona em qualquer projeto.** So'
existe **um** projeto no repositorio com `segments` de CAD suficientes para
exercitar `find_wall_pairs` (item U) - nao ha' segundo caso real para
confirmar ou refutar a generalizacao.

**Classificacao correta: solucao FORTEMENTE SUPORTADA pelo benchmark atual
mais os testes sinteticos planejados (item O) - NAO "universalmente
comprovada", NAO "valida para qualquer CAD".** A confirmacao cross-project
fica como pendencia explicita (item U.3) para a proxima captura real.

---

# U. BENCHMARK CROSS-PROJECT - **LIMITACAO REGISTRADA**

**FATO MEDIDO: nao e' possivel validar cross-project com os artefatos que
existem hoje no repositorio.**

| projeto | tem `input_real.json`? | `segments` de CAD | `openings` | serve para testar `find_wall_pairs`? |
|---|---|---|---|---|
| `torre_easy_lo_r00_tgd` | **sim** | 9.258 no Layer 'Arquitetura' | 91 | **sim** - e' o unico |
| `torre_easy_lo_r00_tp1` | nao (`input.json` com 96 `walls` prontas) | **0** | 0 | **nao** |
| `piloto_sintetico_2x2` | nao (`input.json` com 12 `walls` prontas) | **0** | 0 | **nao** |

Os outros dois projetos entram no pipeline **depois** do Wall Modeling -
comecam de paredes ja' construidas. Eles **nao exercitam `find_wall_pairs`
em nenhuma linha de codigo**, e por isso nao podem confirmar nem refutar a
generalizacao.

**Nao ha' evidencia cross-project nesta sessao, e nenhuma foi inventada.**

O que substitui a generalizacao empirica, enquanto isso:

1. **Fixture sintetica** (PAIR-001..014): cobre multiplas espessuras, T, L,
   ordem embaralhada, tolerancia apertada - nenhuma delas usa numero do
   `torre_easy_lo_r00_tgd`.
2. **Argumento estrutural:** a mudanca nao filtra nada e nao muda nenhuma
   tolerancia; ela so' reordena um conjunto de candidatos ja' aprovado
   pelos mesmos 6 testes de elegibilidade. **O conjunto de pares
   POSSIVEIS e' identico ao de hoje.** Um projeto onde o baseline acerta
   hoje e' um projeto onde o par correto ja' esta' no topo - e ele tem
   `thickness_error` menor ou igual ao dos concorrentes, logo continua no
   topo.
3. **PENDENCIA (proxima captura):** ao capturar o proximo projeto real,
   gravar `input_real.json` **com os `segments` do CAD**, para o benchmark
   ganhar um segundo caso de FASE A. Registrado na secao 26 das regras.

---

# V. PLANO PASSO A PASSO PARA A PROXIMA SESSAO

**Regra de ouro herdada da Etapa 2C: uma causa raiz por commit, com
medicao entre elas.**

### Passo 0 - travar o baseline (antes de qualquer edicao)
- `git fetch origin main`, `git pull`, confirmar HEAD.
- Rodar `python -m pytest tests/test_script.py -q` e guardar a saida.
- Rodar a FASE A e guardar `wall_modeling_snapshot.json` como
  `snapshot_antes_cr1.json` fora do repo (ou em `diagnostics_2d/`).
- Anotar o par `wall_modeling_engine_sha256` / `solver_decision_fingerprint`
  atuais (`f0171249...` / `c74c9c1a...`).

### Passo 1 - escrever os testes ANTES da correcao
- Acrescentar PAIR-001..014 e INV-01..07 em `tests/test_script.py`.
- **Rodar e confirmar que PAIR-006 FALHA** e que os demais passam
  (exceto INV-03 e INV-07, que devem falhar/`xfail` por motivos ja'
  documentados nos itens Q e N).
- Commit: `test(wall_pairing): casos minimos de pareamento e CR-1 (falha esperada)`.

### Passo 2 - a correcao, sozinha
- `tolerances.py`: acrescentar `THICKNESS_RANK_BUCKET_M/_FT`.
- `wall_pairing.py`: acrescentar a constante ao import; trocar o `sort_key`
  pela formula do item G; **reescrever o paragrafo do desempate no
  docstring** (hoje ele descreve o comportamento oposto ao correto e foi a
  origem da confusao).
- **Nada mais.**
- Rodar `pytest`: tudo verde, PAIR-006 e INV-03 agora passam.
- Commit: `fix(wall_pairing): desempatar pelo erro de espessura, nao pela menor distancia (CR-1)`.

### Passo 3 - medir
- Rodar a FASE A e o benchmark completo.
- Conferir **um por um** os HARD H1..H14 do item R contra os valores
  medidos neste plano (87 / 82 / 96 / 4 / 6 de 6 / 60% / 91 aberturas).
- Se **qualquer** HARD falhar: **parar e reportar**, nao ajustar o
  criterio para caber.

### Passo 4 - re-emitir o baseline, num commit proprio
- Regerar `baselines/baseline_real_v1.json` com o novo
  `wall_modeling_engine_sha256`.
- Commit separado, com o par antigo/novo de fingerprints na mensagem, para
  que a mudanca de numero fique rastreavel e nunca pareca espontanea.

### Passo 5 - registrar nas regras
- Atualizar `nuvem/REGRAS_MODULACAO_BLOCOS.md` secao 26: trocar
  `DOCUMENTADO - pendencia de codigo aberta` por `IMPLEMENTADO` com os
  numeros **medidos depois** (nao os previstos aqui).

### Passo 6 - so' entao, a proxima causa raiz
Ordem sugerida, uma por vez, sempre com medicao entre elas:

1. **CR-2/CR-4 via corte por erro de espessura** (`err <= 1,5 cm`) -
   candidato ja' medido: 147 paredes, 20 abaixo de 50 cm, cobertura 87,
   91 aberturas, zero regressao. **Nunca por piso de `r_long` nem por
   comprimento de linha** (item J).
2. **CR-3** - repescagem das faces orfas (245 linhas com candidato valido
   sobram sem par).
3. **`used[i] = used[j] = True` fora do `if centerline`** - defeito latente
   (A.6).
4. **`ORDER_DEPENDENCE_MERGE_COLLINEAR_FRAGMENTS`** (assimetria `i`/`j` nos
   predicados geometricos) - pendencia nova do item Q, secao 26.6 das
   regras. **Causa raiz propria - nunca no mesmo commit que CR-1 nem que
   nenhuma outra correcao de core.**
5. **CR-6** (`deduplicate_walls` com angulo levemente diferente).
6. **CR-7** (`_classify_unused_line`, so' diagnostico).

### Plano de rollback

A correcao e' **uma expressao em uma linha** e **uma constante nova**.

- Rollback imediato: `git revert` do commit do Passo 2. Nada mais depende
  dele - `sort_key` e' local a `find_wall_pairs`, nao e' exportado, nao e'
  serializado, nao aparece em nenhum JSON.
- O commit do Passo 4 (baseline) tambem precisa ser revertido, na ordem
  inversa, para o `wall_modeling_engine_sha256` voltar a bater.
- Os testes do Passo 1 **podem ficar** - eles documentam o defeito; basta
  marcar PAIR-006 como `xfail` enquanto o revert estiver em vigor.
- Nao ha' migracao de dado, nao ha' estado persistido, nao ha' formato de
  arquivo alterado. **O rollback e' de custo zero.**

---

# ANEXO 1 - COMO REPRODUZIR AS MEDICOES DESTA SESSAO

Scripts em `nuvem/benchmark/diagnostics_2d/` (somente leitura do repo,
nenhum toca `nuvem/core/**`):

```bash
cd MinhaAba.tab/MeuPainel.panel/MeuBotao.pushbutton
export D2OUT=/caminho/temporario
py nuvem/benchmark/diagnostics_2d/run_sim.py    # 10 estrategias, tabela comparativa
py nuvem/benchmark/diagnostics_2d/run_sim2.py   # ranking x filtro, matching, R10, determinismo
py nuvem/benchmark/diagnostics_2d/run_sim3.py   # empates, esquadria, W074, invariancia de ordem
py nuvem/benchmark/diagnostics_2d/run_sim4.py   # invariancia geometrica + fixture multi-espessura
py nuvem/benchmark/diagnostics_2d/run_sim5.py   # 6 paredes do trace, consumo silencioso, performance
py nuvem/benchmark/diagnostics_2d/dbg6.py       # PAIR-006 passo a passo + inversao de endpoints
```

`simlib.py` e' a biblioteca comum: reconstroi `merge -> candidatos` e roda
o pipeline real com a politica de selecao trocada.

# ANEXO 2 - NUMEROS DE REFERENCIA (para a proxima sessao nao remedir)

```
merge                 9258 -> 2868 linhas          (12,4 s)
candidatos validos    589                          (5,55 s, 4.111.278 pares)
   por erro de espessura: <=0,05: 131 | 0,05-0,5: 95 | 0,5-1,0: 111
                          1,0-1,5: 60 | 1,5-2,0: 102 | >2,0: 90
   com overlap_ratio == 1,0000 exato: 494 de 589   (84%)
   com linha curta (<20 cm): 229 ; curta x longa(>=100): 162
grafo de candidatos   133 componentes conexas, maior = 25 arestas
disputas              286 linhas com 2+ candidatos; 62 com empate de balde

BASELINE   209 aceitos / 77 exatos / 167 walls / 31 <50cm / 70 cobertas
           76 eixos OK / 33 a 10-16 cm / 82 aberturas / 52 roubos
RANKING    203 aceitos / 122 exatos / 154 walls / 25 <50cm / 87 cobertas
           96 eixos OK /  4 a 10-16 cm / 91 aberturas /  7 roubos
+err<=1,5  192 aceitos / 122 exatos / 147 walls / 20 <50cm / 87 cobertas
           96 eixos OK /  3 a 10-16 cm / 91 aberturas /  7 roubos
GABARITO    97 walls /  0 <50cm / 96 de 97 com len%5==4 / 45.363 cm

paredes de blindagem (nao podem morrer):
   W001, W068  faces 1513,15 x 424,00 cm  d=13,999  r=1,0000  r_long=0,2802
   W074        faces  161,01 x 161,01 cm  d=15,060  err=1,060 r_long=1,0000
```

---

## Estado ao fim desta sessao

- **Nada foi corrigido.** Zero edicao em `nuvem/core/**`, solver, Wall
  Modeling, tolerancias, catalogo, aberturas, compensadores, prisma,
  amarracoes, e nos testes existentes.
- Arquivos novos: este plano, `nuvem/benchmark/diagnostics_2d/*` e a secao
  26 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
- A proxima sessao **implementa** o Passo 1 e o Passo 2 do item V.
