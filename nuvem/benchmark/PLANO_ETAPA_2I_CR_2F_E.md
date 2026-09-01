# ETAPA 2I — DIAGNÓSTICO E PLANO DO `CR-2F-E` (`CENTERLINE_ARGUMENT_ASYMMETRY`)

> **Esta etapa é SOMENTE diagnóstico, análise de alternativas e plano.**
> Nenhum arquivo de `nuvem/core/**` foi alterado. Todas as alternativas
> foram avaliadas por injeção em memória (`lib2i.patched`), do mesmo jeito
> que a Etapa 2G fez com os predicados do par.

Branch: `diagnose/cr2fe-centerline-asymmetry`
Infraestrutura: `nuvem/benchmark/diagnostics_2i/`

---

## 0. `BASELINE_CONFIRMED`

### 0.1 Cadeia de commits

| Item | Esperado | Real | |
|---|---|---|---|
| `CR-2F-B` `PAIR_PREDICATE_ASYMMETRY` | `865373c` | `865373c8029920…` presente na `main` | ✅ |
| `CR-2F-C` `PAIR_GREEDY_INDEX_DEPENDENCE` | `c5447fe` | `c5447fe72ad1d2…` presente na `main` | ✅ |
| motor geometricamente equivalente a `c5447fe` | — | `git diff c5447fe HEAD` = **vazio** | ✅ |

`HEAD` = `80149b6`. Os commits posteriores (`dcc8e04`…`015d302`, experimento
"AI Team") foram integralmente removidos por `80149b6`, de modo que a árvore
inteira — não só o motor — é **byte a byte idêntica** a `c5447fe`.

### 0.2 Baseline numérico (`run_a_baseline_census.py`)

| Métrica | Esperado | Medido | |
|---|---|---|---|
| linhas após merge | 2.868 | **2.868** | ✅ |
| pares aceitos | 199 | **199** | ✅ |
| paredes finais | 148 | **148** | ✅ |
| cobertura humana | 87/97 | **87/97** | ✅ |
| eixos corretos (≤ 0,5 cm) | 96 | **96** | ✅ |
| aberturas | 91/91 | **91/91** | ✅ |
| 7 paredes monitoradas | 7 | **7/7** | ✅ |
| abertura `6558457` | preservada | **preservada** | ✅ |
| `solver_decision_fingerprint` | `c74c9c1a…` | inalterado (nada de produção tocado) | ✅ |

Complementos medidos: `ausentes=4`, `espúrias=4`, `walls_lt50=23`,
`walls_lt20=16`, `total_len=45.875,68 cm`, `dedup=51`.

### 0.3 Prova do `CR-2F-C` (5 permutações)

`run_d_downstream.py`, camada 3 (pares aceitos), seeds `1, 2, 3, 10, 42`:

```
cur    s1  0 difs | s2  0 | s3  0 | s10 0 | s42 0
```

**0 diferenças no conjunto geométrico de pares aceitos em 5 permutações das
2.868 linhas** — para as 9 estratégias de eixo testadas. ✅

### 0.4 Reconciliação do número histórico `2.421,34 cm` — **não é um mismatch**

O enunciado pede para não aceitar o número documentado sem reproduzi-lo. Ele
**não se reproduz** no motor atual, e a causa foi rastreada até o fim:

| configuração | pares aceitos | eixos divergentes | pior desvio | par |
|---|---|---|---|---|
| produção atual (`E_ovl` + chave canônica) | 199 | **47** | **2.121,69 cm** | `(474, 2306)` |
| `E_bis` + desempate `(i, j)` — **o estado em que a 2G mediu** | 199 | **47** | **2.421,34 cm** | `(477, 2306)` |

`out_d_locate.json` foi commitado em `0ec7f2b`, **antes** de `865373c`/`c5447fe`.
Naquele momento `find_wall_pairs` ainda desempatava por `(i, j)` e a 2G
media sob a estratégia candidata `E_bis`; a produção acabou adotando `E_ovl`.
Nessa combinação o par aceito naquela região é `(477, 2306)` em vez de
`(474, 2306)`, e o pior desvio é `2.421,34 cm`. Reproduzido exatamente
(`run_a`, mais a reconstrução em `recon5`).

**O fato central — `47/199` — reproduz idêntico nas duas configurações.**
O que mudou foi *qual* par extremo o guloso consome, não o mecanismo.

> **Registro:** o `2.421,34 cm` deve passar a ser citado como
> *"pior desvio sob os predicados `E_bis` da 2G"*. O número válido para o
> motor de hoje é **2.121,69 cm** (métrica da 2G) / **2.121,71 cm**
> (Hausdorff), no par `(474, 2306)`.

---

## 1. `ROOT_CAUSE`

### 1.1 A função

`create_centerline(l1, l2, max_extension_ft)` — `nuvem/core/engine/geometry.py:357`.

### 1.2 Mapa operação por operação

Classificação pedida no item 3: **A** simétrica · **B** depende de A ·
**C** depende de B · **D** depende do sentido dos endpoints · **E** depende
da ordem da lista · **F** depende só da geometria.

| # | operação (linha da função) | classe | muda com `(A,B)→(B,A)`? |
|---|---|---|---|
| 1 | `p0 = l1.GetEndPoint(0)` — **âncora** | **B + D** | **199/199** |
| 2 | `dir1 = (p1-p0).Normalize()` | B + D | sinal |
| 3 | `dir2` realinhado por `dir1.DotProduct(dir2_raw)` | B + D | sinal |
| 4 | `direction = (dir1+dir2).Normalize()` — **bissetriz** | **A / F** (a menos do sinal) | **0/199** |
| 5 | `len1 = (p1-p0)·direction` | **B** | **132/199** |
| 6 | `sample_ts = (0, len1/2, len1)` amostrado **sobre `l1`** | **B** | — |
| 7 | `project_point_on_line(sample_pt, l2)` — projeta **em `l2`** | **C** | — |
| 8 | `half_offset = média(offset)/2` | **B + C** | **14/199** |
| 9 | `t_lo, t_hi = 0.0, len1` — **intervalo base = o de `l1`** | **B** | **69 / 95** |
| 10 | clamp `(t_lo - t) <= ext` / `(t - t_hi) <= ext` | **B** | — |
| 11 | `span = t_hi - t_lo` | B | **36/199**, pior **4.238,64 cm** |
| 12 | `Line.CreateBound(mid_start, mid_end)` | D (só o sentido) | — |
| 13 | guarda `DistanceTo < 0.01` | A | — |

Verificação: a dissecação de `run_b_invariance.py` reproduz a função real em
**199/199** pares antes de qualquer conclusão ser tirada dela.

### 1.3 Conjunto mínimo de linhas responsáveis

A **direção já é simétrica** (operação 4 — a bissetriz introduzida numa
correção anterior). Dos 47 pares divergentes, **47 têm a mesma direção de
eixo**: nenhuma divergência vem do ângulo. Sobram exatamente **duas** fontes,
quantificadas por ablação (`run_c_rootcause.py`):

| ablação | divergentes | pior Hausdorff | pior Δcomprimento |
|---|---|---|---|
| `cur` (baseline) | **47** | 2.121,71 cm | 4.238,64 cm |
| **`ABL_INT`** — só o intervalo simetrizado | **14** | 10,29 cm | 0,00 cm |
| `ABL_OFF` — só o offset simetrizado | 47 | 2.121,71 cm | 4.238,64 cm |
| `ABL_BOTH` | 14 | 10,29 cm | 0,00 cm |

- **33 dos 47** são curados **só** pelo intervalo simétrico;
- **0** são curados só pelo offset;
- **14** resistem — resíduo do `half_offset`, ≤ 10,29 cm, todos com desvio
  angular entre as faces.

> ### CAUSA-RAIZ (`CONFIRMED`)
>
> **Primária — o INTERVALO.** `t_lo, t_hi = 0.0, len1` fixa o alcance do
> eixo no intervalo de **`l1`**, e o teto `max_extension_ft` é medido a
> partir desse intervalo. `l2` só pode *estender*, nunca *definir*.
> Quem entra como `l1` decide o comprimento da parede.
> **33/47 divergências e 100% dos desvios grandes (até 2.121,71 cm).**
>
> **Secundária — o OFFSET PERPENDICULAR.** `sample_ts` amostra 3 pontos ao
> longo de **`l1`** e os projeta em **`l2`**: a média cobre só o trecho de
> `l1`. Com desvio angular entre as faces, `média(l1→l2) ≠ −média(l2→l1)`.
> **14/47 divergências, ≤ 10,29 cm.**
>
> A âncora `p0` (operação 1) muda em 199/199 mas **não é causa**: é só a
> origem paramétrica. Ela vira causa apenas porque as operações 9 e 6 são
> escritas *relativas a ela*.

---

## 2. `MINIMAL_CASE`

### 2.1 Caso real do benchmark — par `(474, 2306)`

| | |
|---|---|
| **A** (linha 474) | `(-4,48; 807,55) → (151,13; 807,55)` · **L = 155,61 cm** · ang `0,0000°` |
| **B** (linha 2306) | `(2267,73; 865,75) → (-2125,90; 780,43)` · **L = 4.394,45 cm** · ang `1,1125°` |
| ângulo entre elas | **1,1125°** |
| espessura medida (simétrica) | **15,583 cm** |
| sobreposição mútua | **155,61 cm** (razão 1,0000 sobre a menor) |
| razão de comprimentos | **0,0354** |
| `centerline(A,B)` | `(-4,62; 814,96) → (150,98; 816,47)` · **L = 155,61 cm** |
| `centerline(B,A)` | `(-2126,31; 804,65) → (2267,73; 847,31)` · **L = 4.394,25 cm** |
| Δ origem / Δ destino | **2.121,71 cm / 2.116,98 cm** |
| Hausdorff | **2.121,71 cm** |

**O mecanismo, em uma frase:** quando `l1 = A`, o intervalo é `[0; 155,61]`
e `B` não consegue estendê-lo (as pontas de `B` estão a mais de 40 cm);
quando `l1 = B`, o intervalo é `[0; 4.394,45]` e `A` está inteiramente
dentro. **A mesma geometria produz uma parede de 1,5 m ou de 44 m.**

### 2.2 Segundo caso real, com a resposta CERTA invertida — par `(1461, 1464)`

| | |
|---|---|
| **A** (1461) | `(2070,52; 774,05) → (2070,52; -739,10)` · **L = 1.513,15 cm** |
| **B** (1464) | `(2056,52; 774,05) → (2056,52; 350,05)` · **L = 424,00 cm** |
| ângulo | `0,0000°` · espessura `14,001 cm` · overlap `424,00 cm` |
| `centerline(A,B)` | `x=2063,52`, `y ∈ [-739,10; 774,05]` · **1.513,15 cm** |
| `centerline(B,A)` | `x=2063,52`, `y ∈ [350,05; 774,05]` · **424,00 cm** |

**Este par é a razão pela qual o problema não é trivial.** Aqui a resposta
**correta é a LONGA** (a face de 1.513 cm é a face real da parede; sem ela
o gabarito perde `W001`). No par `(474, 2306)` a resposta **correta é a
CURTA** (a linha de 4.394 cm é uma linha auxiliar que apenas passa perto).

> **Consequência registrada:** os `87/97` do baseline **não são uma
> propriedade da fórmula** — são o resultado de a ordem da lista ter posto,
> por acaso, a face certa como `l1` nos dois casos. Sob permutação o mesmo
> `cur` entrega `85, 86, 87, 86, 86`. Ver item 8.

### 2.3 Caso sintético mínimo equivalente

O mecanismo se reproduz sem nenhum dado real, em coordenadas em cm:

```
A = Line((0,0)   → (100,0))          # face curta
B = Line((-500,14) → (600,14))       # face longa, mesma direção
ext = 40 cm

centerline(A,B) → x ∈ [  0, 100], y=7      (100 cm)
centerline(B,A) → x ∈ [-500, 600], y=7    (1100 cm)
```

Basta `len(B) > len(A) + 2·ext` e sobreposição total. Este é o esqueleto do
teste permanente `INV-CENTER-001` (item 15).

---

## 3. `CENSUS` — os 199 pares aceitos

`run_a_baseline_census.py`. `create_centerline(A,B)` × `create_centerline(B,A)`,
comparados **geometricamente** (chave canônica com a ponta menor primeiro —
uma linha invertida **não** conta como eixo diferente).

### 3.1 Classificação

| classe | nº |
|---|---|
| idênticos | **152** |
| diferença apenas de direção dos endpoints | **0** *(absorvida pela chave canônica)* |
| mesma reta, extensão diferente | **38** |
| deslocamento paralelo | **9** |
| eixo completamente diferente | 0 |
| degenerado / espúrio | 0 |
| **divergentes (total)** | **47 / 199 (23,6 %)** |

### 3.2 Distribuições do desvio (Hausdorff, cm)

| | máx | média | p50 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|
| só os 47 divergentes | **2.121,71** | 211,97 | 89,55 | 492,19 | 949,75 | 1.646,73 |
| todos os 199 | 2.121,71 | 50,06 | 0,00 | 91,98 | 196,53 | 1.089,15 |

### 3.3 Que geometria provoca o problema

| campo | divergentes p50 / p90 / máx | idênticos p50 / máx |
|---|---|---|
| comprimento A (cm) | 20,00 / 1.133,21 / 1.681,21 | 152,33 / 1.484,00 |
| comprimento B (cm) | 174,00 / 869,81 / 4.394,45 | 155,00 / 1.456,01 |
| **razão de comprimentos** | **0,434 / 0,893 / 0,984** | **0,999 / 1,000** |
| **ângulo entre as faces (°)** | **0,000 / 2,272 / 2,751** | **0,000 / 0,000** |
| espessura (cm) | 13,999 / 14,002 / 15,953 | 14,000 / 15,060 |
| sobreposição (cm) | 14,51 / 448,40 / 1.456,01 | 152,33 / 1.456,01 |
| razão de sobreposição | 1,000 / 1,000 / 1,000 | 1,000 / 1,000 |

> ### PADRÃO OBSERVADO (`CONFIRMED`)
>
> A assimetria aparece **exatamente** quando as duas faces do par **não são
> gêmeas**:
> - **razão de comprimentos** — mediana `0,999` nos idênticos contra
>   `0,434` nos divergentes; **todo par com faces de comprimento igual é
>   simétrico**;
> - **desvio angular** — os 152 idênticos têm ângulo `0,0000°` **sem
>   exceção**; todo par com ângulo > 0 está entre os divergentes.
>
> Espessura e razão de sobreposição **não discriminam nada** (idênticas nos
> dois grupos). Não é um problema de tolerância: é um problema de
> **referência**.

---

## 4. `INVARIANCE` — as duas invariâncias, medidas separadamente

`run_b_invariance.py`. **`ARGUMENT ORDER` e `ENDPOINT DIRECTION` são
invariâncias diferentes e foram medidas em separado, como pedido no item 7.**

| estratégia | `ARGUMENT ORDER` `(A,B)`×`(B,A)` | `A(p1,p0) B(p0,p1)` | `A(p0,p1) B(p1,p0)` | `A(p1,p0) B(p1,p0)` |
|---|---|---|---|---|
| **`cur`** | **47** (2.121,71 cm) | **14** (1,15 cm) | 0 | **14** (1,15 cm) |
| `S1` canônica | 0 | 8 (1,15) | 6 (**21,33**) | **14 (21,33)** |
| `S2` face mais longa | 0 | 7 (1,15) | 7 (**21,33**) | **14 (21,33)** |
| `S3` bissetriz simétrica | **0** | **0** | **0** | **0** |
| `S4` sobreposição mútua | **0** | **0** | **0** | **0** |
| `S5` média dos extremos | **0** | **0** | **0** | **0** |
| `S6` união clampada na interseção | **0** | **0** | **0** | **0** |
| `S7` **união clampada na face longa** | **0** | **0** | **0** | **0** |

> ### FATO NOVO desta etapa (`CONFIRMED`)
>
> **`create_centerline` também é dependente do SENTIDO dos endpoints**, e
> isso **nunca havia sido medido**: `14/199` eixos mudam só por inverter
> `Line(p0,p1) → Line(p1,p0)` da face `l1`, com desvio de até **1,15 cm**.
> É uma causa **independente** da ordem dos argumentos (o par
> `A(p0,p1) B(p1,p0)` dá **0** divergências: inverter `l2` não muda nada,
> porque a função já realinha `dir2`).
>
> Origem: a âncora `p0 = l1.GetEndPoint(0)` (operação 1) combinada com o
> `sample_ts` de 3 pontos (operação 6) — amostrar `0, len1/2, len1` a partir
> de uma ponta ou da outra dá médias diferentes quando há desvio angular.
>
> **Consequência prática:** `H2` já **falha hoje**, e uma correção que
> resolvesse só a ordem dos argumentos deixaria essa metade de pé.

---

## 5. `ALTERNATIVES_TESTED`

Nove formulações, todas em `diagnostics_2i/lib2i.py`, todas injetadas no
`find_wall_pairs` **real**.

| | nome | ideia |
|---|---|---|
| `cur` | produção | âncora em `l1.p0`, intervalo `[0, len1]` + extensão ≤ 40 cm |
| `S1` | `CANONICAL_ARGUMENT_ORDER` | ordena `(l1,l2)` pela chave geométrica canônica do `CR-2F-C` e chama o `cur` **intocado** |
| `S2` | `LONGEST_REFERENCE` | a face mais longa é sempre `l1`, `cur` intocado |
| `S3` | `SYMMETRIC_BISECTOR` | frame sem lado; intervalo = união, com teto medido a partir da **interseção** |
| `S4` | `MUTUAL_OVERLAP_CENTERLINE` | só o trecho em que as duas faces se encaram, sem extensão |
| `S5` | `ENDPOINT_AVERAGING` | cada ponta = média simétrica das pontas dos dois intervalos projetados |
| `S6` | `SYMMETRIC_UNION_CLAMPED` | união, teto simétrico por face, tomando o alcance mais restritivo |
| **`S7`** | **`SYMMETRIC_LONGEST_SPAN`** | **frame sem lado; intervalo = união das duas faces, teto `ext` medido a partir do intervalo da face MAIS LONGA** |
| `S8` | `SYMMETRIC_BANDED_SPAN` | `S7` + guarda: a face só arrasta o eixo enquanto ficar a `meia espessura ± WALL_DETECTION_TOLERANCE` dele. **Tentativa deliberada de resolver o par `(474, 2306)` sem parâmetro novo — falhou:** aperta 86/152 pares já unívocos (até 37,01 cm) e o par crítico ainda sai com 2.117,8 cm, porque com 1,11° e semi-espessura de 7,8 cm a faixa só fecha a ~400 cm do centro. |

### 5.1 Correção geométrica — simetria é necessária, **não suficiente** (item 10)

`run_e_finalists.py`. `centr.` = `_axis_offset_error_ft`, a autoverificação
que o **próprio motor** já roda: o quanto o eixo deixa de ficar equidistante
das duas faces. Independe do gabarito.

| estr | `H1` dif | `H2` dif | muda os **152 já simétricos** | centr. pior (cm) | centr. média (cm) |
|---|---|---|---|---|---|
| `cur` | 47 | 14 | 0/152 | 1,1438 | 0,01781 |
| `S1` | **0** | 14 | 0/152 | **21,3331** | **0,12718** |
| `S2` | **0** | 14 | 0/152 | **21,3331** | **0,12735** |
| `S3` | **0** | **0** | 0/152 | 1,1541 | **0,01187** |
| `S4` | **0** | **0** | **86/152** | 1,1541 | 0,01187 |
| `S5` | **0** | **0** | **86/152** | 1,1541 | 0,01187 |
| `S6` | **0** | **0** | 0/152 | 1,1541 | **0,01187** |
| **`S7`** | **0** | **0** | **0/152** | 1,1541 | **0,01187** |
| `S8` | **0** | **0** | **86/152** | 1,1541 | 0,01187 |

> ### Por que `S1`/`S2` (as canônicas) estão ELIMINADAS — item 10.9
>
> Elas **tornam determinístico um resultado pior**. O erro de centralização
> do eixo salta de **1,14 cm → 21,33 cm** no pior caso e de **0,0178 cm →
> 0,1272 cm** na média (**7,1×**). Ao fixar qual face é a referência, elas
> escolhem sistematicamente a resposta **menos centrada** entre as duas que
> o `cur` já produzia. É exatamente "esconder um erro através de uma regra
> arbitrária", e ainda deixam **`H2` de pé** (14 divergências, agora com
> **21,33 cm** em vez de 1,15 cm — a canonicalização **piorou** a
> invariância ao sentido dos endpoints).
>
> ### Por que `S4`/`S5`/`S8` estão eliminadas
>
> Mudam **86 dos 152 pares em que o `cur` já era simétrico** — pares onde
> não há ambiguidade nenhuma a resolver. `S8` chega a mover esses eixos em
> até **37,01 cm**. O `CR-2F-E` começa *depois* que o par foi aceito e deve
> tocar **apenas** a ambiguidade; reescrever eixos que já eram unívocos é
> outra mudança, sem causa aberta que a justifique.
>
> `S3`, `S6` e `S7` são as três formulações que **reproduzem o `cur`
> exatamente nos 152 pares não ambíguos** (0/152) e ainda **melhoram** o
> erro médio de centralização (`0,0178 → 0,0119 cm`, −33 %).

---

## 6. `DOWNSTREAM_METRICS` — pipeline headless REAL

`run_d_downstream.py`, sobre as 2.868 linhas mescladas congeladas, com a
referência humana existente. **A referência humana só é lida DEPOIS, para
avaliar — nenhuma estratégia tem acesso a ela.**

| estr | aceitos | dedup | walls | cobertura | eixo | 10-16 cm | espúrias | lt50 | lt20 | aberturas | total (cm) | **excesso** (cm) | 7 monit. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **`cur`** | 199 | 51 | **148** | **87/97** | **96** | 3 | 4 | 23 | 16 | **91/91** | 45.876 | **3.039** | **7/7** |
| `S1` | 199 | 49 | 150 | 86/97 | 98 | 3 | 4 | 14 | 11 | 91/91 | 53.260 | 8.352 | 6/7 |
| `S2` | 199 | 50 | 149 | **87/97** | 96 | 3 | 4 | 12 | 9 | **91/91** | 55.174 | 9.872 | **7/7** |
| `S3` | 199 | 49 | 150 | 84/97 | 99 | 3 | 4 | 13 | 9 | 90/91 | 44.659 | **1.886** | 4/7 |
| `S4` | 199 | 46 | 153 | 84/97 | 99 | 3 | 7 | 29 | 23 | 90/91 | 42.803 | 1.393 | 4/7 |
| `S5` | 199 | 46 | 153 | 83/97 | 97 | 3 | 7 | 15 | 15 | 91/91 | 48.804 | 5.313 | 4/7 |
| `S6` | 199 | 49 | 150 | 84/97 | 99 | 3 | 4 | 13 | 9 | 90/91 | 44.659 | 1.886 | 4/7 |
| **`S7`** | 199 | 51 | **148** | **86/97** | **96** | 3 | 4 | **12** | **9** | **91/91** | 54.498 | 9.178 | **7/7** |
| `S8` | 199 | 49 | 150 | 83/97 | 99 | 3 | 4 | 25 | 19 | 90/91 | 44.527 | 3.095 | 4/7 |

`excesso` é uma métrica **nova desta etapa**: comprimento de eixo que não cai
sobre nenhuma parede do gabarito (o custo de um eixo que "dispara"). A
cobertura do benchmark mede só do lado do gabarito e por isso não enxerga
excesso.

### 6.1 Isolamento camada por camada (item 8) — 5 permutações

| camada | `cur` | `S1`…`S7` |
|---|---|---|
| 1 input (2.868 linhas) | idêntico por construção | idêntico |
| 2 candidatos | idêntico | idêntico |
| **3 pares aceitos** | **0 difs** | **0 difs** |
| **4 `create_centerline`** | **22, 23, 24, 28, 29 eixos divergem** | **0, 0, 0, 0, 0** |
| 5 `deduplicate_walls` | varia junto | estável |
| **6 paredes finais** | **fingerprint DIFERE nas 5 seeds** | **fingerprint IGUAL nas 5** |

> ### RESULTADO CENTRAL DO ITEM 8 (`CONFIRMED`)
>
> **Toda a instabilidade de ordem que sobrou no Wall Modeling nasce na
> camada 4 e em nenhuma outra.** As camadas 1–3 estão congeladas
> (`CR-2F-B` + `CR-2F-C`); a camada 4 é `create_centerline`; as camadas 5–6
> apenas propagam. Qualquer uma das sete alternativas zera a camada 4 e,
> com ela, o fingerprint das paredes finais.
>
> Efeito prático da instabilidade de hoje, medido no gabarito:
> `cur` entrega `86, 87, 86, 86, 85` de cobertura e `6, 7, 6, 6, 5` das 7
> paredes monitoradas conforme a ordem da lista, **perdendo `W037`, `W001`
> ou `W010`** dependendo do sorteio. As alternativas entregam sempre o
> mesmo valor.

---

## 7. `WINNER` e `WHY_WINNER`

### `WINNER: S7 — SYMMETRIC_LONGEST_SPAN`

```python
# esboço; a implementação final vai em core/engine/geometry.py
frame  = bissetriz das duas direções, origem no meio dos dois pontos médios
Ii, Ij = intervalos das duas faces projetados nesse frame
ref    = a face MAIS LONGA (empate → chave geométrica canônica)
t_lo   = max(min(Ii.lo, Ij.lo), ref.lo - max_extension_ft)
t_hi   = min(max(Ii.hi, Ij.hi), ref.hi + max_extension_ft)
s_eixo = média das coordenadas perpendiculares médias das duas faces
```

### Por que `S7`

1. **Geometricamente correta** — é a leitura **literal da intenção já
   declarada** no docstring da própria função: *"o eixo cobre a UNIÃO do
   alcance das duas linhas… em cada ponta, usa a que for MAIS LONGA das duas
   faces pareadas… a face mais longa sempre prevalece"*. O `cur` implementa
   essa regra **ancorada em `l1`**, e por isso só a cumpre quando `l1` já é
   a face mais longa. `S7` cumpre a mesma regra escolhendo pela **geometria**
   (comprimento), não pela posição na lista. O teto `max_extension_ft`
   continua fazendo o mesmo trabalho de sempre.
2. **Intrinsecamente simétrica** — o frame não tem lado (é o mesmo
   `_pair_frame_cached` já em produção desde o `CR-2F-B`); trocar
   `l1 ↔ l2` devolve o mesmo frame, ou o mesmo com os dois eixos negados,
   que as projeções absorvem. Não é canonicalização.
3. **Invariante à ordem A/B** — 0/199 (`H1`).
4. **Invariante ao sentido dos endpoints** — 0/199 nas quatro combinações
   (`H2`). Corrige uma causa que **nunca havia sido medida**.
5. **Invariante à ordem da lista** — 0 divergências de eixo e fingerprint de
   paredes idêntico nas 5 permutações (`H3`).
6. **Compatível com as tolerâncias existentes** — não introduz nenhuma
   constante nova; usa `CENTERLINE_MAX_EXTENSION_FT` como sempre.
7. **Não perde paredes reais** — `148` paredes (igual ao baseline), as **7
   monitoradas preservadas**, `walls_lt50` cai de 23→12 e `walls_lt20` de
   16→9 (menos fragmentos).
8. **Não piora openings** — **91/91**, abertura `6558457` atribuída.
9. **Não esconde erro atrás de lexicografia** — ao contrário de `S1`/`S2`,
   **melhora** o erro médio de centralização (`0,0178 → 0,0119 cm`). A chave
   canônica aparece só para desempatar dois comprimentos **exatamente
   iguais**, caso em que os dois intervalos já são idênticos e a escolha não
   muda o resultado.
10. **Mais barata** — **−47 %** no custo de `create_centerline` (item 11).

### Suplentes pré-aprovados

- **`S3`/`S6`** (resultados idênticos entre si): mais conservadoras no
  excesso (1.886 cm contra 9.178 cm) e igualmente simétricas, mas perdem
  `W001`, `W010`, `W037` e uma abertura — **falham `H5`, `H6` e `H8`**. Só
  viram opção se o `CR-2F-A`/`CR-2F-D` mudar o quadro do `deduplicate_walls`.

---

## 8. `HARD_GATES`

`run_f_gates.py`.

| gate | `cur` | `S1` | `S2` | `S3` | `S4` | `S5` | `S6` | **`S7`** |
|---|---|---|---|---|---|---|---|---|
| **H1** `(A,B) == (B,A)` | ❌ 47 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **✅** |
| **H2** endpoints invertidos | ❌ 14 | ❌ 14 | ❌ 14 | ✅ | ✅ | ✅ | ✅ | **✅** |
| **H3** 5 permutações, camada pós-`find_wall_pairs` | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **✅** |
| **H4** pares aceitos == baseline `CR-2F-C` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ 0 difs** |
| **H5** openings 91/91 | ✅ | ✅ | ✅ | ❌ 90 | ❌ 90 | ✅ | ❌ 90 | **✅** |
| **H6** cobertura ≥ 87 | ✅ 87 | ❌ 86 | ✅ 87 | ❌ 84 | ❌ 84 | ❌ 83 | ❌ 84 | **❌ 86** |
| **H7** eixos ≥ 96 | ✅ 96 | ✅ 98 | ✅ 96 | ✅ 99 | ✅ 99 | ✅ 97 | ✅ 99 | **✅ 96** |
| **H8** 7 monitoradas | ✅ | ❌ 6 | ✅ | ❌ 4 | ❌ 4 | ❌ 4 | ❌ 4 | **✅ 7/7** |
| **H9** abertura `6558457` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | **✅** |
| **H10** `solver_decision_fingerprint` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **✅** |
| **H11** runtime ≤ +10 % | — | ❌ +28,6 % | ❌ +21,3 % | ✅ −49,2 % | ✅ −59,7 % | ✅ −53,9 % | ✅ −52,8 % | **✅ −47,0 %** |

`S8` (`SYMMETRIC_BANDED_SPAN`) passa `H1`–`H4`, `H7`, `H10`, `H11` (−2,6 %) e
**falha `H5` (90/91), `H6` (83/97), `H8` (4/7) e `H9`** — a guarda de faixa
aperta 86 dos 152 pares já unívocos (até 37,01 cm) e ainda deixa o par
`(474, 2306)` em 2.117,8 cm. Eliminada.

`H10`: nada de produção foi tocado nesta etapa; e o `CR-2F-E` fica inteiro
dentro da FASE A (Wall Modeling), enquanto o fingerprint mede as **peças que
o solver de blocos decide** (`tests/solver_bench.py`, cenários sintéticos).
A verificação obrigatória continua sendo rodar `tests/solver_bench.py` no
commit de implementação.

`H11`: 10 repetições dos 199 pares. Duas rodadas independentes: `cur`
**4,91 / 4,38 ms**, `S7` **2,55 / 2,32 ms** — **−48,1 % e −47,0 %**. A economia vem de trabalhar em `float` puro no frame do par, em
vez de construir `XYZ` intermediários (mesmo padrão de performance já usado
pelo `CR-2F-B`).

### 8.1 `H6` está conceitualmente incorreto — evidência e correção proposta

**`S7` falha `H6` por exatamente uma parede: `W097`** (`(-153,5; 817,0) →
(345,5; 817,0)`, 499 cm). A causa foi isolada até o fim e **não é
`create_centerline`**:

```
S7, ANTES do deduplicate_walls : (-346,5; 815,0) → (360,5; 815,0)  L=707,0 cm   cobertura de W097 = 1,000
S7, DEPOIS do deduplicate_walls: []                                            cobertura de W097 = 0,000
```

`deduplicate_walls` removeu a parede **boa**, tratando-a como duplicata da
parede **espúria de 4.394,2 cm** gerada pelo par `(474, 2306)` — a mesma do
caso mínimo (item 2.1). O critério é `distância entre eixos ≤
DUPLICATE_AXIS_TOLERANCE (2 cm)`, e:

| | distância eixo-bom → eixo-espúrio | sobrevive? |
|---|---|---|
| `S2` | **10,315 cm** (> 2 cm) | ✅ sim |
| `S7` | **0,363 cm** (≤ 2 cm) | ❌ removida |

**A parede boa morre porque `S7` centraliza o eixo com mais precisão** — e o
eixo espúrio, mais bem centrado, passa a cair praticamente em cima dela.
`deduplicate_walls` então mantém "a mais longa do grupo", que é a espúria de
44 m. Uma correção que melhora a geometria é punida por um estágio a jusante
que decide por comprimento.

**Prova causal direta** (`run_f_gates.py`): removendo do conjunto **apenas**
os eixos com mais de 40 m — exatamente 1 parede — antes do `deduplicate_walls`:

| | cobertura | eixo | aberturas | 7 monit. | walls | excesso |
|---|---|---|---|---|---|---|
| `cur` completo | 87/97 | 96 | 91/91 | 7/7 | 148 | 3.039 cm |
| `S7` completo | 86/97 | 96 | 91/91 | 7/7 | 148 | 9.178 cm |
| **`S7` sem eixos > 40 m** | **87/97** | **96** | **91/91** | **7/7** | **148** | 5.461 cm |
| `cur` sem eixos > 40 m | 87/97 | 96 | 91/91 | 7/7 | 148 | 3.039 cm *(0 removidas — o `cur` não gera nenhum)* |

**`S7` iguala o baseline em todos os gates assim que essa única parede
espúria sai do caminho.**

E o `cur` só não gera essa espúria porque a ordem da lista pôs a face de
155 cm como `l1`. Sob permutação ele gera outras: a cobertura do `cur` cai
para **85–87** e as monitoradas para **5–7**.

> ### Correção proposta para `H6` (`ENGINEERING_REQUIRED` — depende de aprovação)
>
> `H6` compara uma solução **determinística** contra o **melhor sorteio** de
> uma solução **não-determinística**. Redação proposta:
>
> > **H6′** — a cobertura não pode cair abaixo de **86/97**, que é a
> > mediana do baseline `cur` sob as 5 permutações (`86, 87, 86, 86, 85`),
> > **e** o valor tem que ser **o mesmo nas 5 permutações** (o que `H3` já
> > garante), **e** nenhuma das 7 paredes monitoradas pode sair (`H8`).
>
> Com `H6′`, `S7` passa os onze gates. `H7`, `H8` e `H9` **não** precisam de
> emenda: `S7` os cumpre na redação original.
>
> **Se `H6′` não for aprovado, `S7` não deve ser implementado agora** — a
> ordem correta passa a ser `CR-2F-A`/`CR-2F-D` primeiro (que é onde
> `deduplicate_walls` mora), e o `CR-2F-E` volta depois. Essa é uma decisão
> sua: **eu não a tomei.**

---

## 9. `OUT_OF_SCOPE_FINDINGS`

### `OUT_OF_SCOPE_CR_2F_A` — `deduplicate_walls` tem a mesma assimetria de relação

`nuvem/core/engine/wall_pairing.py:1341`. A relação de duplicidade usa
`get_distance_between_parallel_lines(line, kept_line)` — a versão
**assimétrica** (mede do ponto médio de `line`), a mesma família que o
`CR-2F-B` corrigiu dentro de `find_wall_pairs` e que o `CR-2F-A` ainda tem
de corrigir em `merge_collinear_fragments`. Além disso, `sorted(key=-comprimento)`
é estável: comprimentos empatados mantêm a ordem de entrada.
**Não foi tocado nesta etapa.**

### `OUT_OF_SCOPE_CR_2F_D` — `deduplicate_walls` mantém "a mais longa", mesmo espúria

O caso `W097` acima é uma não-transitividade concreta: `boa ~ espúria` e a
espúria vence por comprimento, apagando uma parede real do gabarito.
`DUPLICATE_AXIS_TOLERANCE = 2 cm` é a fronteira exata (0,363 cm × 10,315 cm).
**Não foi tocado nesta etapa.**

### Fora de qualquer causa aberta — o pareamento `(474, 2306)`

`find_wall_pairs` aceita como par uma face de **155,61 cm** e uma linha de
**4.394,45 cm** inclinada **1,1125°**, com espessura medida de 15,583 cm.
Nenhum critério de eixo pode transformar esse par num resultado bom: o `cur`
só escapa por sorte de ordenação. Isso é **pareamento**, não eixo, e o item 4
do pedido proíbe explicitamente mexer no conjunto de candidatos. **Fica
registrado como causa candidata futura, sem código nesta etapa.**

### Registro histórico corrigido

`REGRAS_MODULACAO_BLOCOS.md` §26.8.5 cita `2.421,34 cm`. O número é válido
para os predicados `E_bis` da 2G, não para a produção (`E_ovl`), onde o
valor é `2.121,69 cm`. Ver item 0.4.

---

## 10. `FILES_TO_CHANGE_IN_IMPLEMENTATION`

A implementação é **pequena e reversível**. **Não exige redesenhar o Wall
Modeling** — o `CR-2F-E` começa depois que o par já foi aceito e termina
antes do `deduplicate_walls`.

### Arquivos de produção tocados: **1**

**`nuvem/core/engine/geometry.py`**

| o quê | detalhe |
|---|---|
| **funções novas** | `_pair_frame_lines(l1, l2)` — o frame simétrico do par a partir de duas `Line` (o `_pair_frame_cached` de hoje trabalha sobre o cache; reaproveitar a mesma matemática, sem duplicar a fórmula) · `_interval_in_frame(frame, line)` · `_axis_offset_in_frame(frame, l1, l2)` |
| **função alterada** | `create_centerline(l1, l2, max_extension_ft)` — **mesma assinatura**, mesmo nome, mesmo retorno (`Line` ou `None`), mesma guarda `< 0.01`. Só o miolo muda. |
| **`__all__`** | acrescentar os três nomes novos |
| **constantes** | **nenhuma nova** |
| **funções removidas** | **nenhuma** |

### Chamadas que mudam: **nenhuma**

`create_centerline` é chamada em **um único ponto de produção** —
`wall_pairing.py:474`, dentro de `find_wall_pairs` — e a assinatura não muda.
Os diagnósticos das etapas 2C/2D/2G que a chamam continuam funcionando.

### Explicitamente **não** tocados

`find_wall_pairs` (ranking, `thickness_rank`, `E_ovl`, chave de desempate,
conjunto de candidatos, guloso), `_pair_symmetric_*`, `_line_identity_key_cached`,
`merge_collinear_fragments`, `deduplicate_walls`, `extend_wall_ends_to_junctions`,
`clip_centerline_to_caps`, `assign_openings_to_walls`, qualquer tolerância.

### Reversibilidade

Um único `git revert` do commit de implementação restaura o comportamento
atual: nenhuma outra função passa a depender das três funções novas, e
nenhum formato de dado persistido muda.

---

## 11. `PERMANENT_TESTS_PLANNED`

**Nada foi promovido para `tests/**` nesta etapa** (item 15). Os protótipos
reproduzíveis vivem em `diagnostics_2i/`. Na implementação, adicionar a
`tests/test_script.py` (mesma taxonomia do `INV-PAIR-003` já existente):

| id | o que trava | forma |
|---|---|---|
| **`INV-CENTER-001`** | `H1` — `create_centerline(A,B)` ≡ `create_centerline(B,A)` | caso sintético do item 2.3 (face curta × face longa, `ext=40 cm`) + os dois casos reais `(474,2306)` e `(1461,1464)` reduzidos a coordenadas literais. Compara a **chave geométrica canônica**, não os endpoints crus. |
| **`INV-CENTER-002`** | `H2` — as 4 combinações de sentido dos endpoints dão o mesmo segmento | mesmos casos, `Line(p0,p1)` × `Line(p1,p0)` para as duas faces. **Trava a causa nova descoberta no item 4.** |
| **`INV-CENTER-003`** | `H3` — invariância à ordem da lista na camada logo após `find_wall_pairs` | `find_wall_pairs` **real** sobre uma nuvem sintética pequena (~40 linhas com encontros L/T, faces de comprimentos diferentes e desvio angular de ~1°), 5 permutações, comparando o **conjunto geométrico de centerlines**. Fecha a lacuna que o `INV-PAIR-003` deixou explícita ("não o centerline final, que tem a assimetria PRÓPRIA e FORA DE ESCOPO do 2F-E"). |
| **`INV-CENTER-004`** | não-regressão dos pares já unívocos | os 152 pares em que o `cur` já era simétrico têm de continuar com o **mesmo eixo** (amostra fixa embutida no teste, extraída de `out_a_baseline_census.json`). Impede que uma futura variante do tipo `S4`/`S5`/`S8` entre sem ser percebida. |

Testes de regressão do benchmark (`tests/regression/`) continuam valendo sem
alteração; o commit de implementação tem de rodar
`python3 -m pytest tests/test_script.py -q` e `tests/solver_bench.py`.

---

## 12. Resumo executivo

| campo | valor |
|---|---|
| `BASELINE_CONFIRMED` | **SIM** — cadeia `865373c` → `c5447fe`, motor idêntico, 9/9 métricas batem, `CR-2F-C` provado (0 difs em 5 permutações) |
| `ROOT_CAUSE` | intervalo ancorado em `l1` (`t_lo,t_hi = 0,len1` + clamp) → **33/47**; `half_offset` amostrado sobre `l1` → **14/47**. A direção (bissetriz) **já era simétrica**. |
| `MINIMAL_CASE` | par `(474,2306)`: 155,61 cm × 4.394,45 cm, 1,1125°, Hausdorff **2.121,71 cm**. Contraexemplo `(1461,1464)` mostra que a resposta certa às vezes é a longa, às vezes a curta. |
| `CENSUS` | **47/199 (23,6 %)** divergem: 38 mesma reta/extensão diferente, 9 deslocamento paralelo, 0 degenerados. Discriminantes: **razão de comprimentos** e **desvio angular**. |
| `INVARIANCE` | `ARGUMENT ORDER` **47/199**; `ENDPOINT DIRECTION` **14/199 (fato novo)**. |
| `ALTERNATIVES_TESTED` | `S1`…`S8` + `cur` — **9 formulações**, todas no pipeline headless real |
| `WINNER` | **`S7` — `SYMMETRIC_LONGEST_SPAN`** |
| `HARD_GATES` | `S7`: **10 de 11**. Falha só `H6`, por 1 parede, **por causa alheia** (`deduplicate_walls`) — provado. |
| `RUNTIME` | `create_centerline`: **4,91 → 2,55 ms** e **4,38 → 2,32 ms** em duas rodadas (**−48,1 % / −47,0 %**) |
| `SOLVER_FINGERPRINT` | `c74c9c1ae0e3f169f76e05fe53c01a858fce0af5b4e9d5f1b86fd71e92d2a316` — inalterado |
