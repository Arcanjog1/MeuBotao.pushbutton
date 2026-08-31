# ETAPA 2G — PLANO DA CORREÇÃO `CR-2F-B` (`PAIR_PREDICATE_ASYMMETRY`)

**Data:** 2026-08-31
**Base:** `origin/main` @ `c895272f0ef1a93445c7c129b84a801a874f4598` (Etapa 2F concluída)
**Escopo:** PROJETO E VALIDAÇÃO OFFLINE. **Nada em `nuvem/core/**` foi alterado.**
Nenhuma correção foi implementada. Nenhum teste foi promovido para
`tests/**`. Nenhum merge foi feito.
**Suíte:** `378 passed` (`py -3 -m pytest -q`) — inalterada nesta sessão.
**Registro de regras:** `nuvem/REGRAS_MODULACAO_BLOCOS.md` §26.8 (novo) e §26.6
(atualizado) foram escritos nesta sessão, como manda o registro obrigatório
do CLAUDE.md/AGENTS.md — conhecimento não fica só no plano.
**Scripts reproduzíveis:** `nuvem/benchmark/diagnostics_2g/`

> **Como as estratégias foram medidas sem tocar no motor:** cada estratégia
> é injetada **em memória** dentro do `find_wall_pairs` REAL, trocando os
> dois predicados no dict de globais do módulo `core.engine.wall_pairing`
> (`find_wall_pairs.__globals__`) e desfazendo a troca ao sair. O pipeline
> que roda em seguida é o de produção (`wall_modeling_bridge`), não uma
> reimplementação. Os arquivos do motor no disco continuam byte a byte
> iguais aos de `c895272`.

---

## RESUMO EXECUTIVO

1. A causa do `CR-2F-B` foi **localizada com precisão** e é uma só: os dois
   predicados da varredura de candidatos medem **a partir de uma das duas
   linhas**, e essa escolha é o índice da lista.
2. Sete definições simétricas foram construídas e medidas. **Todas as sete
   são exatamente simétricas** (0 divergências em 4.111.278 pares) e
   **todas as sete tornam o conjunto de candidatos perfeitamente invariante
   à ordem da lista** (0 diferenças em 5 permutações). O `cur` falha nas duas.
3. A vencedora é **`E_ovl`** — a folga perpendicular média medida **apenas
   onde as duas faces realmente se encaram**. Ela vence não por ser
   simétrica (todas são), mas por ser a única que é simétrica **porque a
   medição está certa**, e não porque um empate foi resolvido.
4. **Achado NOVO, não previsto na 2F:** `create_centerline(a, b)` também é
   assimétrico — **47 dos 199 pares aceitos** mudam de eixo só invertendo a
   ordem dos argumentos, com desvio máximo de **2.421,34 cm**. Isso é uma
   causa **própria** (batizada aqui `2F-E`), **maior** que o `CR-2F-B` em
   impacto geométrico, e **fora do escopo desta correção**.
5. **Consequência obrigatória para os critérios HARD:** o `CR-2F-B` entrega
   invariância do **conjunto de candidatos** (que é exatamente o que o
   pedido define como alvo). Ele **NÃO** entrega, sozinho, paredes finais
   invariantes — e **nenhum critério de aceitação pode exigir isso dele**,
   porque as causas restantes (`2F-C` e `2F-E`) são outras. Isso está
   medido, não suposto (item F).

**Veredito:** `IMPLEMENTATION_READY` — com o escopo e os critérios HARD
definidos no item M. Ver a ressalva do item M.3.

---

## A. CAUSA PRECISA

A varredura de `find_wall_pairs` sempre avalia o par como `(i, j)` com
`i < j` (`nuvem/core/engine/wall_pairing.py:369-371`). Dois predicados dessa
varredura tomam **uma das duas linhas como régua**:

### A.1 — `_distance_between_parallel_cached` (`geometry.py:115-125`)

```python
midpoint1 = cache1[4]
p0_2, direction2 = cache2[0], cache2[2]
w = midpoint1 - p0_2
proj_dist = w.DotProduct(direction2)
proj_point = p0_2 + direction2 * proj_dist
return midpoint1.DistanceTo(proj_point)
```

Algebricamente isso é, com `n₂` = normal de `direction2`:

```
d(1,2) = | n₂ · (mid₁ − mid₂) |
d(2,1) = | n₁ · (mid₁ − mid₂) |
```

**O vetor medido é o mesmo; muda só a NORMAL sobre a qual ele é projetado.**
As duas normais só coincidem se as retas forem **exatamente** paralelas — e
`_are_parallel_cached` aceita até `|cross| < 0,05` (**≈ 2,87°**). Essa é a
causa raiz, escrita em uma linha:

> **a "distância entre as duas linhas" é definida em relação à direção de
> UMA delas, e a escolha de qual é o índice na lista.**

O erro cresce com a **distância entre os pontos médios**: um desvio angular
de 2,75° projetado ao longo de 30 m vale mais de 1,4 m. Por isso o `|Δ|`
máximo medido é de **185,21 cm** — não é ruído numérico, é geometria.

### A.2 — `_line_pair_overlap_ft_cached` (`geometry.py:127-142`)

```python
p0, _p1, direction, length1, _mid = cache1     # <- eixo = linha 1
...
overlap_lo = max(0.0, t2_lo)
overlap_hi = min(length1, t2_hi)               # <- recorte = linha 1
```

A sobreposição é projetada **na direção de `cache1`** e recortada em
`[0, length1]`. Trocar a ordem troca o eixo de projeção e o intervalo de
recorte. `|Δ|` máximo medido: **99,77 cm**.

### A.3 — o que NÃO é a causa (verificado, não suposto)

| suspeita | veredito medido |
|---|---|
| `_are_parallel_cached` | **SIMÉTRICO** — usa `abs(cross.Z)`; 0 divergências |
| `_closest_target_thickness_ft` | função pura de `dist`; simétrica assim que `dist` for |
| `thickness_rank` | idem |
| cache indexado por par | não existe: `_line_geom_cache` é por linha |
| direção dos endpoints (`p0`/`p1`) | **JÁ É INVARIANTE**, inclusive hoje — item F.2 |

---

## B. FUNÇÃO / PREDICADO RESPONSÁVEL — e o escopo real

`_distance_between_parallel_cached` tem **quatro** chamadores:

| arquivo:linha | função | pertence a |
|---|---|---|
| `geometry.py:546` | `_bridge_clusters_via_openings` (merge, passada 2) | **CR-2F-A** |
| `geometry.py:633` | `merge_collinear_fragments` (passada 1) | **CR-2F-A** |
| `wall_pairing.py:374` | **`find_wall_pairs`** | **CR-2F-B** ✅ |
| `wall_pairing.py:506` | `scan_possible_missed_bonecas` | diagnóstico (não cria parede) |

`_line_pair_overlap_ft_cached` tem dois: `wall_pairing.py:390`
(**`find_wall_pairs`** ✅) e `wall_pairing.py:510` (mesmo diagnóstico).

> **DECISÃO DE PROJETO OBRIGATÓRIA:** é **PROIBIDO** simetrizar
> `_distance_between_parallel_cached` **no lugar**. Isso mudaria o
> `merge_collinear_fragments` no mesmo commit — exatamente o que o recorte
> desta etapa proíbe, e exatamente o que a 2F mandou separar (item S).
> A correção **cria funções novas** e troca **apenas as duas chamadas
> dentro de `find_wall_pairs`**. As funções antigas ficam intactas,
> servindo o merge até o `CR-2F-A`.

---

## C. OPÇÕES TESTADAS

Todas as sete alternativas foram construídas e medidas em pé de igualdade.
Nenhuma foi descartada por "ser difícil de implementar".

| id | definição |
|---|---|
| `cur` | **atual** — mede a partir da linha `i` (baseline de comparação) |
| `A_mean` | média aritmética das duas direções |
| `B_min` | mínimo das duas direções |
| `C_max` | máximo das duas direções |
| `D_long` | a linha **mais longa** é a régua (a direção mais confiável) |
| `E_bis` | **intrinsecamente simétrica:** projeta sobre a normal da **bissetriz** |
| `E_ovl` | **intrinsecamente simétrica:** folga média **sobre a sobreposição mútua** |
| `F_lex` | orientação canônica por chave **lexicográfica** das coordenadas |

`E_bis` e `E_ovl` não escolhem uma das duas medições nem fazem média delas:
elas **substituem a medição por uma construção que não tem lado**. `F_lex`
é a estratégia "resolve o empate por uma regra determinística" — incluída
de propósito, porque é a saída óbvia e barata, para ser medida em vez de
suposta.

---

## D. RESULTADOS QUANTITATIVOS

### D.0 Validação da instrumentação (sem isso nada abaixo vale)

`run_a_census.py`, item 0. A camada vetorizada foi conferida contra o motor:

| | |
|---|---|
| candidatos (motor `L.build_candidates`) | **589** |
| candidatos (camada vetorizada) | **589** |
| mesmo conjunto de pares | **SIM** |
| pior `|Δ|` em `d` | **7,05 × 10⁻¹⁵ ft** (≈ 2 × 10⁻¹³ cm) |
| pior `|Δ|` em `overlap` / `ratio` | **0,0 exato** |
| `thickness_rank` divergentes | **0** |
| **veredito** | **PASS** |

O baseline de produção também foi reproduzido campo a campo: **589
candidatos → 203 aceitos → 154 paredes → 87/97 cobertas → 96 eixos
corretos → 91/91 aberturas**, batendo com §26.1 e com a Etapa 2F.

### D.1 Censo de simetria — 4.111.278 pares (`i<j`), 1.332.676 paralelos

A direção oposta **não foi deduzida da fórmula**: cada bloco foi recalculado
chamando o mesmo código como `(B,A)` e comparado transposto.

| estratégia | máx `|Δd|` | pares assimétricos | máx `|Δov|` | pares assimétricos |
|---|---:|---:|---:|---:|
| **`cur`** | **185,206785 cm** | **118.307** | **99,771653 cm** | **15.858** |
| `A_mean` | 0,000000 | **0** | 0,000000 | **0** |
| `B_min` | 0,000000 | **0** | 0,000000 | **0** |
| `C_max` | 0,000000 | **0** | 0,000000 | **0** |
| `D_long` | 0,000000 | **0** | 0,000000 | **0** |
| `E_bis` | 0,000000 | **0** | 0,000000 | **0** |
| `E_ovl` | 0,000000 | **0** | 0,000000 | **0** |
| `F_lex` | 0,000000 | **0** | 0,000000 | **0** |

> A 2F mediu 182,86 cm sobre um pré-filtro de 60.556 "near pairs". O censo
> exaustivo desta etapa acha **185,21 cm** — o número da 2F estava certo,
> só era um limite inferior.

### D.2 Caso mínimo real da 2F — linhas 16 × 295

```
linha 16  : comprimento 152,01 cm
linha 295 : comprimento   8,43 cm      desvio angular = 2,7535°
janela aceita para 14 cm ± 2,5 cm = [11,50 ; 16,50] cm
```

| estratégia | `d(16,295)` | `d(295,16)` | `|Δ|` | veredito `ij` / `ji` |
|---|---:|---:|---:|---|
| **`cur`** | **11,830631** | **8,997001** | **2,834 cm** | **aceita / recusa** ❌ |
| `A_mean` | 10,413816 | 10,413816 | 0 | recusa / recusa |
| `B_min` | 8,997001 | 8,997001 | 0 | recusa / recusa |
| `C_max` | 11,830631 | 11,830631 | 0 | **aceita / aceita** |
| `D_long` | 8,997001 | 8,997001 | 0 | recusa / recusa |
| `E_bis` | 10,416823 | 10,416823 | 0 | recusa / recusa |
| **`E_ovl`** | **8,999600** | **8,999600** | 0 | recusa / recusa |
| `F_lex` | 11,830631 | 11,830631 | 0 | **aceita / aceita** |

**Leitura geométrica.** O par é um **fragmento de 8,43 cm inclinado 2,75°**
ao lado de uma face de 152 cm. A folga real, medida onde os dois de fato se
encaram, é **9,00 cm** — não é uma parede de 14 cm. O valor `11,83` só
aparece porque a reta **infinita** do fragmento de 8 cm foi prolongada até o
ponto médio da face longa. `C_max` e `F_lex` **eternizam o valor errado**;
`E_ovl` e `D_long` devolvem o certo.

### D.3 Invariância (`run_b_invariance.py`) — 2.868 linhas

Diferença simétrica do conjunto de pares candidatos (0 = invariante).

| eixo | `cur` | `A_mean` | `B_min` | `C_max` | `D_long` | `E_bis` | `E_ovl` | `F_lex` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **ordem da lista** (5 seeds) | **15/20/24/19/17** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **direção dos endpoints** (3 casos) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **controle IDENT** (ida-e-volta ft→cm→ft) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rotação 0,5° / 37° / 90° / 180° | 7/17/2/3 | 14/20/3/3 | 7/11/2/2 | 14/24/3/4 | 7/13/2/2 | 14/20/3/3 | **4/8/0/1** | 13/27/19/17 |
| translação 1 m / 120 m / 10 km | 12/28/40 | 12/28/40 | 12/28/40 | 12/28/40 | 12/28/40 | 12/28/40 | 12/28/40 | 12/28/40 |

**A contagem sozinha enganaria.** Por isso cada par que virou foi medido
pela **margem até a fronteira de decisão mais próxima**:

| transformação | pior margem, `E_ovl` | pior margem, `F_lex` |
|---|---:|---:|
| rotação 37° | **9,3 × 10⁻¹⁴ cm** | **2,20 cm** |
| rotação 90° | **0** | **2,47 cm** |
| rotação 180° | 1,7 × 10⁻¹⁵ cm | **2,21 cm** |
| translação 10 km | 1,8 × 10⁻¹⁰ cm | 1,8 × 10⁻¹⁰ cm |
| combinado | 1,8 × 10⁻¹² cm | 2,20 cm |

**Conclusões que isso força:**

1. **Rotação e translação NÃO são invariâncias que a simetrização entrega,
   nem falhas que ela cause.** Para todas as estratégias exceto `F_lex`, os
   pares que viram estavam **exatamente em cima** da fronteira (margem
   `~10⁻¹³ cm`) — é a comparação `<= tolerância` em ponto flutuante, não o
   predicado. A translação dá **exatamente os mesmos 12/28/40 para todas as
   oito**, inclusive a atual: é condicionamento numérico das coordenadas,
   um problema **independente** e não resolvível por simetria.
2. **`F_lex` está ELIMINADA por evidência.** Ela vira pares com **2,2 a
   2,5 cm de folga** — longe de qualquer fronteira. A chave lexicográfica
   depende das coordenadas, então girar a planta **reordena os pares** e
   troca a medição escolhida. É a única estratégia com falha **estrutural**
   de invariância a movimento rígido. (Rotação de 90°: 19 pares mudam,
   contra 0–3 de todas as outras.)
3. **`cur` no teste combinado** tem pior margem de **2,38 cm** — assimetria
   estrutural, como esperado.

### D.4 Downstream real (`run_c_downstream.py`) — motor de produção

Merge **congelado** (2.868 linhas), ordem de produção:

| estratégia | cand | aceitos | paredes | cobertas | ausentes | eixo ✓ | eixo 10-16 | espúrias | <50cm | <20cm | compr. total | aberturas | balde 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`cur`** | 589 | 203 | 154 | **87** | 4 | **96** | 4 | 6 | 25 | 19 | 46.373 | **91** | 122 |
| `A_mean` | 588 | 199 | 149 | **87** | 4 | **96** | 3 | 4 | 23 | 16 | 46.066 | **91** | 123 |
| `B_min` | 591 | 199 | 148 | **87** | 4 | **96** | 3 | 4 | 23 | 16 | 45.876 | **91** | 122 |
| `C_max` | 573 | 203 | 154 | **87** | 4 | **96** | 4 | 6 | 25 | 19 | 46.373 | **91** | 122 |
| `D_long` | 569 | 199 | 148 | **87** | 4 | **96** | 3 | 4 | 23 | 16 | 45.876 | **91** | 122 |
| `E_bis` | 588 | 199 | 149 | **87** | 4 | **96** | 3 | 4 | 23 | 16 | 46.066 | **91** | 123 |
| **`E_ovl`** | **569** | **199** | **148** | **87** | **4** | **96** | **3** | **4** | **23** | **16** | **45.876** | **91** | 122 |
| `F_lex` | 589 | 202 | 153 | **87** | 4 | **96** | 3 | 6 | 26 | 22 | 45.975 | **91** | 122 |

**Nenhuma estratégia regride a cobertura (87), o eixo (96) nem as aberturas
(91/91).** Todas as sete paredes vigiadas — **W001, W010, W037, W053, W054,
W068, W074** — continuam cobertas em **todas as oito**, e a abertura
**6558457** continua atribuída em todas as oito, na ordem de produção.

> **O comprimento total cai de 46.373 para 45.876 cm (−497 cm, −1,07%) e
> isso NÃO é regressão.** As paredes com menos de 50 cm caem de 25 para 23 e
> as com menos de 20 cm de 19 para 16, com a cobertura intacta em 87: os
> 497 cm que somem são exatamente as paredinhas espúrias (6 → 4). Ver §26.4
> — o critério é espessura, e a espessura ficou melhor medida.

### D.5 O que a simetrização entrega, camada por camada (`run_d_locate.py`)

Esta é a medição mais importante do plano. Com o espião em
`create_centerline` capturando os pares realmente aceitos:

| camada | `cur` | `A_mean` / `E_bis` | `D_long` / `E_ovl` |
|---|---|---|---|
| **1. conjunto de pares aceitos** (dif. em 5 seeds) | 12, 12, 16, 12, 16 | **0, 2, 4, 4, 2** | **0, 2, 4, 4, 2** |
| nº de aceitos (5 seeds) | 201–203 (**varia**) | **199 em todas** | **199 em todas** |
| **2. eixos diferentes** entre os pares comuns | 17–22 | **18–26** | **19–26** |
| **3. fingerprint das paredes finais** | difere sempre | **difere sempre** | **difere sempre** |

**Leitura obrigatória:**

- O `CR-2F-B` derruba a instabilidade do conjunto de pares aceitos de
  **12–16 para 0–4** (−75%) e **congela a contagem em 199**. Não a zera.
- O que sobra na camada 1 é o **`2F-C`** (desempate `(i,j)` do CR-1):
  medidos **81 a 87 grupos de empate** por estratégia, **10 deles disputando
  a mesma linha** — e esse número é **10 para todas as oito estratégias**,
  confirmando que é causa independente do predicado.
- A camada 2 **não melhora nada** com a simetrização, porque a causa dela é
  outra (item E).

---

## E. ACHADO NOVO — `2F-E` `CENTERLINE_ARGUMENT_ASYMMETRY`

**Não previsto na Etapa 2F. Fora do escopo desta correção. Registrado aqui
para não se perder.**

`find_wall_pairs` chama `create_centerline(pending[i], pending[j], …)`
(`wall_pairing.py:415`). Medido sobre os **199 pares aceitos** por `E_bis`
(predicado já simétrico), trocando **só a ordem dos argumentos**:

| | |
|---|---|
| pares testados | **199** |
| eixos que MUDAM | **47 (23,6%)** |
| pior desvio | **2.421,3403 cm (24,2 m)** |

**Mecanismo, medido** (`run_e_finalists.py`, item 1). `CENTERLINE_MAX_EXTENSION
= 40,00 cm`. O eixo é ancorado em `p0` de **`l1`** e o intervalo começa em
`[0, len(l1)]`; `l2` só **estende**, e no máximo 40 cm por ponta:

| par | `len(a)` | `len(b)` | eixo`(a,b)` | eixo`(b,a)` | Δ |
|---|---:|---:|---:|---:|---:|
| [89, 1350] | 1456,01 | 1532,00 | 1470,01 | 1532,00 | 61,99 cm |
| [90, 1349] | 1456,01 | 1922,22 | 1456,01 | 1922,22 | **255,00 cm** |
| [92, 265] | **5,09** | 174,00 | **5,09** | 174,00 | 84,46 cm |
| [94, 264] | **5,09** | 174,00 | **9,09** | 174,00 | **164,91 cm** |

Ou seja: **quem entra como `l1` decide o comprimento da parede.** É
exatamente o caso do §26.2 (W001/W068: face de 1.513 cm contra face de
424 cm). Note que o docstring de `create_centerline` já afirma que a função
"deveria ser simétrica entre as duas faces da parede" — a **direção** foi
simetrizada (bissetriz), mas a **âncora e o alcance** não.

**Prioridade sugerida:** entre `CR-2F-C` e `CR-2F-A`. É a maior causa
restante de instabilidade geométrica do pareamento.

---

## F. DETERMINISMO × INVARIÂNCIA — registrados separadamente

| propriedade | definição | hoje (`cur`) | com `CR-2F-B` (`E_ovl`) |
|---|---|---|---|
| **DETERMINISMO** | mesma lista → mesmo resultado | **PASSA** (2F, item L) | **PASSA** |
| **INVARIÂNCIA — predicado** | `f(A,B) == f(B,A)` | **FALHA** (185,21 cm) | **PASSA** (0 exato, 4,1 M pares) |
| **INVARIÂNCIA — direção dos endpoints** | inverter `p0`/`p1` | **PASSA** (já hoje) | **PASSA** |
| **INVARIÂNCIA — ordem da lista (candidatos)** | permutar as 2.868 | **FALHA** (15–24) | **PASSA** (0 em 5 seeds) |
| **INVARIÂNCIA — ordem da lista (pares aceitos)** | idem | **FALHA** (12–16) | **PARCIAL** (0–4; resta `2F-C`) |
| **INVARIÂNCIA — ordem da lista (paredes)** | idem | **FALHA** | **FALHA** (resta `2F-E`) |
| **INVARIÂNCIA — rotação / translação** | movimento rígido | falha por fronteira (`~10⁻¹³ cm`) | **igual** — causa numérica, independente |

> **O alvo do pedido — "o mesmo conjunto GEOMÉTRICO de candidatos para a
> mesma geometria" — é atingido integralmente.** As linhas em cinza acima
> não são falhas do `CR-2F-B`: são as causas `2F-C` e `2F-E`, e a
> condicionamento numérico, que este commit **não** promete resolver e
> **não pode** ser cobrado de resolver.

---

## G. ESTRATÉGIA VENCEDORA: `E_ovl`

### G.1 Como as outras caíram

| estratégia | por que NÃO |
|---|---|
| `F_lex` | **eliminada por evidência:** falha **estrutural** de invariância a rotação (2,2–2,5 cm de folga, 19 pares em 90°). E mantém o falso candidato 16×295. |
| `C_max` | **eterniza a pior das duas medições.** Mantém o falso candidato 16×295; downstream idêntico ao `cur` (154 paredes, 6 espúrias, 25 paredes < 50 cm). Simétrica, mas simétrica no valor errado. |
| `B_min` | sem justificativa geométrica: escolher o menor **enviesa a espessura para baixo** e faz **mais** pares entrarem na janela ±2,5 cm (591 candidatos, o maior de todos). Bom resultado por acidente, não por definição. |
| `A_mean` | média de duas medições quando **uma delas pode ser lixo** (o caso 16×295: média entre 8,99 e 11,83 = 10,41, um número que não corresponde a nada físico). Resultado idêntico ao `E_bis`, mas sem construção geométrica por trás. |
| `D_long` | correta na intuição (a linha longa tem direção confiável) e **downstream idêntico ao `E_ovl`** — mas privilegia uma das faces e mede no **ponto médio**, que pode estar longe de onde as faces se encaram. Fica perigosamente perto da ideia proibida pelo §26.2. **Suplente aceitável.** |
| `E_bis` | construção geométrica legítima (normal da bissetriz — a mesma direção que `create_centerline` já usa) e a mais barata das intrinsecamente simétricas. **Perde para `E_ovl` na correção da medição** (item G.3) e na robustez numérica. **Suplente pré-aprovado** (item M.3). |

### G.2 Por que `E_ovl` vence

1. **É a única definição que mede o que a grandeza significa.** "Espessura
   da parede" é a folga entre as duas faces **onde elas são as duas faces
   da mesma parede** — não no ponto médio de uma delas, que pode estar
   metros fora do trecho comum.
2. **É simétrica por construção, não por desempate.** O referencial
   (bissetriz + origem no meio dos dois pontos médios) não tem lado.
   Medido: 0 divergências em 4.111.278 pares.
3. **É a mais robusta numericamente.** Rotação: **4 / 8 / 0 / 1** pares de
   diferença, contra 14 / 20 / 3 / 3 de `E_bis` e `A_mean`. Motivo
   estrutural: medindo dentro da sobreposição, os valores ficam **longe**
   das fronteiras, então o ponto flutuante tem menos a que virar.
4. **É a que produz o resultado mais limpo:** 148 paredes (o menor),
   **4 espúrias** (contra 6 do `cur`), **23** paredes < 50 cm (contra 25),
   **16** < 20 cm (contra 19) — mantendo **87 cobertas / 96 eixos / 91 de 91
   aberturas** e as 7 paredes vigiadas.
5. **Não viola o §26.2:** o denominador do `overlap_ratio` continua sendo
   `min(length1, length2)`. Nenhum piso por `r_long` é introduzido. Nenhuma
   linha é filtrada por comprimento.
6. **Cabe no orçamento** (item J): **+0,51%** na FASE A.

### G.3 A prova de que `E_ovl` mede melhor que `E_bis`

`run_e_finalists.py`, item 2. Os dois conjuntos de candidatos diferem em
**29 pares** — e os dois lados contam a mesma história:

**Os 24 que só `E_bis` aceita** (mediana do menor comprimento: **8,44 cm**;
máximo **20,80 cm**; ângulo mediano **2,75°**):

| par | `len_i` | `len_j` | `d_bis` | `d_ovl` |
|---|---:|---:|---:|---:|
| [128, 379] | 830,00 | **8,44** | 16,27 | **18,51** |
| [423, 1193] | **8,61** | 1114,01 | 13,37 | **18,51** |
| [602, 2082] | 484,00 | **8,61** | 16,48 | **18,51** |

São **fragmentos de 8 cm inclinados 2,75°** contra faces de 4 a 11 metros.
A folga real onde eles se encaram é **18,5 cm** — fora da janela [11,5;16,5].
`E_bis` os aceita porque mede no ponto médio, a metros de distância;
`E_ovl` os recusa porque mede onde importa. **`E_ovl` está certa.**

**Os 5 que só `E_ovl` aceita** (`d_bis` 10,13–11,36 → fora por baixo;
`d_ovl` 11,51–12,46 → dentro): mesma mecânica, sinal invertido. `E_bis`
subestimava; `E_ovl` mede 11,5–12,5 cm, dentro da janela — e o §26.3 já
registra que existe parede real medindo 15,06 cm (erro de 1,06 cm), então
erros de 1,5 a 2,5 cm são explicitamente admissíveis como **candidato**.

**Fallback de `E_ovl`** (`run_e_finalists.py`, item 3): dos 1.332.676 pares
paralelos, **92,74%** não têm sobreposição mútua e caem no ramo de fallback
(`= E_bis`) — mas **0 dos 569 candidatos** o exercem, porque o filtro
`overlap_ratio >= 0,60` já exige sobreposição. **O fallback é guarda
defensiva, nunca caminho normal.** (É também a razão do custo: ele roda no
laço quente. Ver item J.)

---

## H. FÓRMULA EXATA PROPOSTA

Tudo em **float puro sobre os componentes do cache** — nenhum objeto `XYZ`
intermediário é criado (isso não é micro-otimização: é o que faz o custo
caber no H12; ver item J).

### H.1 Referencial simétrico do par

```
_pair_frame_cached(c1, c2) -> (bx, by, nx, ny, ox, oy)

    d1 = c1[2] ; d2 = c2[2] ; m1 = c1[4] ; m2 = c2[4]

    s  = +1.0 se (d1.X*d2.X + d1.Y*d2.Y) >= 0.0 senao -1.0
    bx = d1.X + d2.X*s
    by = d1.Y + d2.Y*s
    nb = hypot(bx, by)
    se nb < 1e-9:  bx, by = d1.X, d1.Y            # antiparalelas exatas
    senao:         bx, by = bx/nb, by/nb

    nx, ny = -by, bx                              # normal da bissetriz
    ox, oy = (m1.X + m2.X)*0.5, (m1.Y + m2.Y)*0.5 # origem sem lado
```

**Prova de simetria (exata em IEEE-754, não aproximada):** trocar `c1`↔`c2`
dá `s` idêntico (o produto escalar é comutativo) e `(bx,by)` idêntico se
`s=+1` (a soma de floats é comutativa) ou exatamente negado se `s=−1`
(`b−a == −(a−b)` é exato em IEEE-754). `hypot` é par. `(ox,oy)` é
invariante. Logo o referencial ou é o mesmo, ou é o mesmo com os dois
eixos negados — e todos os consumidores abaixo usam `abs()` ou diferenças
de projeções, que absorvem essa negação. **Medido: 0 divergências em
4.111.278 pares.**

### H.2 Sobreposição simétrica — substitui `_line_pair_overlap_ft_cached` **só em `find_wall_pairs`**

```
_pair_symmetric_overlap_ft_cached(c1, c2) -> (overlap_ft, length1, length2)

    bx, by, _, _, ox, oy = _pair_frame_cached(c1, c2)
    t(p) = bx*(p.X - ox) + by*(p.Y - oy)

    ai, zi = ordenado( t(c1[0]), t(c1[1]) )
    aj, zj = ordenado( t(c2[0]), t(c2[1]) )

    lo = max(ai, aj)
    hi = min(zi, zj)
    overlap_ft = hi - lo se hi > lo senao 0.0

    devolve (overlap_ft, c1[3], c2[3])
```

`length1`/`length2` continuam sendo os comprimentos **originais** — o
denominador `min(length1, length2)` do `overlap_ratio` não muda (§26.2).

### H.3 Espessura simétrica — substitui `_distance_between_parallel_cached` **só em `find_wall_pairs`**

```
_pair_symmetric_thickness_ft_cached(c1, c2) -> float

    bx, by, nx, ny, ox, oy = _pair_frame_cached(c1, c2)
    t(p) = bx*(p.X - ox) + by*(p.Y - oy)
    g(p) = nx*(p.X - ox) + ny*(p.Y - oy)

    ti0, si0 = t(c1[0]), g(c1[0])
    ti1, si1 = t(c1[1]), g(c1[1])
    tj0, sj0 = t(c2[0]), g(c2[0])
    tj1, sj1 = t(c2[1]), g(c2[1])

    lo = max( min(ti0,ti1), min(tj0,tj1) )
    hi = min( max(ti0,ti1), max(tj0,tj1) )

    se (hi - lo) <= 1e-12:                        # sem sobreposicao mutua
        devolve abs( nx*(m1.X-m2.X) + ny*(m1.Y-m2.Y) )      # = E_bis

    # s_k(t) e' AFIM ao longo de t: interpola linearmente
    sa(t0,s0,t1,s1,t) = s0                      se |t1-t0| < 1e-12
                      = s0 + (s1-s0)*(t-t0)/(t1-t0)   caso contrario

    g_lo = abs( sa(ti0,si0,ti1,si1,lo) - sa(tj0,sj0,tj1,sj1,lo) )
    g_hi = abs( sa(ti0,si0,ti1,si1,hi) - sa(tj0,sj0,tj1,sj1,hi) )

    devolve (g_lo + g_hi) * 0.5
```

**Sentido físico:** a folga perpendicular entre as duas faces é uma função
**afim** de `t` (duas retas). `(g_lo + g_hi)/2` é a folga **média sobre o
trecho em que as duas faces se encaram** — e, quando não há cruzamento, é
exatamente a folga no meio desse trecho.

**Limitação registrada (não é bug, é escopo):** se as duas retas se cruzarem
**dentro** do trecho de sobreposição, `(g_lo+g_hi)/2` não é a média de `|g|`
(é a média de `g` em módulo nas pontas). Para o cruzamento acontecer dentro
da sobreposição com `|ângulo| ≤ 2,87°` e folga da ordem de 14 cm, seria
preciso uma sobreposição maior que ~5,6 m com as faces se tocando — caso em
que o par não é uma parede de 14 cm de qualquer forma. **Nenhuma ocorrência
entre os 569 candidatos medidos.** Fica documentado.

---

## I. ARQUIVOS QUE DEVERÃO MUDAR

| # | arquivo | mudança | linhas |
|---|---|---|---|
| 1 | `nuvem/core/engine/geometry.py` | **ACRESCENTAR** `_pair_frame_cached`, `_pair_symmetric_overlap_ft_cached`, `_pair_symmetric_thickness_ft_cached` (junto de `_distance_between_parallel_cached`, ~linha 142) e os três nomes em `__all__` (~linha 36). **NÃO alterar** `_distance_between_parallel_cached` nem `_line_pair_overlap_ft_cached` — o merge depende delas. | +~70 |
| 2 | `nuvem/core/engine/wall_pairing.py` | **DUAS** linhas de chamada em `find_wall_pairs`: `374` (`dist = …`) e `390` (`overlap_ft, length1, length2 = …`). Mais o bloco de docstring explicando por que a medição é simétrica e por que ela é feita sobre a sobreposição mútua. | 2 + docstring |
| 3 | `tests/test_script.py` | `INV-PAIR-001`, `INV-PAIR-002`, `INV-PAIR-003` (item K) | +~90 |
| 4 | `nuvem/REGRAS_MODULACAO_BLOCOS.md` | **JÁ ESCRITO NESTA SESSÃO** (§26.8 novo + §26.6 atualizado de "PADRÃO OBSERVADO AINDA NÃO CONFIRMADO" para "CONFIRMADO E MEDIDO"), conforme a regra de registro obrigatório do CLAUDE.md/AGENTS.md. Na implementação basta virar o rótulo de §26.8.3 de `DOCUMENTADO - pendência de código aberta` para **IMPLEMENTADO** | já feito |
| 5 | `nuvem/benchmark/RELATORIO_ETAPA_2G.md` | medição pós-implementação (criado **depois** de aplicar) | novo |

**Explicitamente NÃO mudam:** `tolerances.py` (nenhuma constante),
`merge_collinear_fragments`, `_bridge_clusters_via_openings`,
`create_centerline`, `scan_possible_missed_bonecas`, `deduplicate_walls`,
`extend_wall_ends_to_junctions`, o `sort_key` do CR-1, o solver.

---

## J. CUSTO — medido com baseline JUSTO (`run_f_cost.py`, 5 repetições)

Comparar as candidatas contra o `cur` **do motor** seria injusto nos dois
sentidos: as candidatas entram como float puro, e a atual usa objetos `XYZ`
(`CrossProduct`/`DotProduct` alocam). Por isso o baseline correto é
**`cur_py`** — a fórmula de hoje reescrita no mesmo estilo.

| estratégia | `find_wall_pairs` (mediana) | vs `cur` (motor) | vs `cur_py` (justo) | FASE A (25,42 s, §26.1) |
|---|---:|---:|---:|---:|
| `cur` (motor, hoje) | 8,90 s | +0,0% | +72,1% | +0,00% |
| `cur_py` (mesma fórmula, float) | **5,17 s** | −41,9% | +0,0% | −14,66% |
| `A_mean` | 6,20 s | −30,3% | +19,9% | −10,62% |
| `B_min` | 5,86 s | −34,2% | +13,3% | −11,96% |
| `C_max` | 5,91 s | −33,6% | +14,3% | −11,75% |
| `D_long` | 6,02 s | −32,3% | +16,4% | −11,32% |
| `E_bis` | 7,01 s | −21,3% | +35,5% | −7,45% |
| **`E_ovl`** | **9,03 s** | **+1,5%** | **+74,6%** | **+0,51%** |

**Leitura honesta e obrigatória:** simetrizar por `E_ovl` custa **+74,6%**
de aritmética. O que salva o orçamento é a reescrita em **float puro**, que
sozinha vale **−41,9%**. **As duas coisas têm que andar juntas.** Se
`_pair_symmetric_thickness_ft_cached` for implementada com objetos `XYZ`,
o custo salta para ~+75% no pareamento (~+26% na FASE A) e **estoura o
requisito HARD H12 (≤10%)**. Isso é uma **exigência de implementação**, não
uma sugestão.

Com a reescrita em float, `E_ovl` fica em **+0,51%** na FASE A — folga
confortável dentro do H12.

---

## K. TESTES NECESSÁRIOS

Prototipados e **executados** em `run_g_invpair.py`. Os dois **reprovam a
fórmula de hoje** (senão não testariam nada) e **aprovam a vencedora**.

### `INV-PAIR-001` — caso mínimo, 2 linhas, coordenadas literais

Fixture congelada em cm (não depende de rodar o merge nem de ler
`input_real.json`):

```
A = Line(-1082.980000, 220.548800) -> (-1234.988600, 220.548800)   # 152,01 cm
B = Line(-1095.572500, 229.343304) -> (-1103.993200, 229.748299)   #   8,43 cm, 2,75°
```

Quatro asserções:

1. `espessura(A,B) == espessura(B,A)` — igualdade **exata** de float;
2. `overlap(A,B) == overlap(B,A)` — igualdade exata;
3. o **veredito de candidato** é o mesmo nas duas direções;
4. as três valem também com os **endpoints invertidos** em ambas as linhas.

**Resultado medido:**

| estratégia | `d(A,B)` | `d(B,A)` | cand `AB` | cand `BA` | veredito |
|---|---:|---:|---|---|---|
| **`cur`** | 11,830630 | 8,997002 | sim | não | **FAIL** ✅ (tem que reprovar) |
| `E_ovl` | 8,999600 | 8,999600 | não | não | **PASS** |
| (as outras 6) | — | — | — | — | PASS |

### `INV-PAIR-002` — 2.868 linhas mescladas, 5 permutações

Asserção: o conjunto de pares candidatos, traduzido de volta para a
**identidade** das linhas, é idêntico em todas as ordens.

| estratégia | baseline | s1 | s2 | s3 | s10 | s42 | veredito |
|---|---:|---:|---:|---:|---:|---:|---|
| **`cur`** | 589 | 15 | 20 | 24 | 19 | 17 | **FAIL** ✅ |
| **`E_ovl`** | **569** | **0** | **0** | **0** | **0** | **0** | **PASS** |

**Forma de implementação:** marcado `slow` (carrega o estado congelado do
`torre_easy_lo_r00_tgd`), no padrão dos testes `INV_xx` que já existem em
`tests/test_script.py`.

### `INV-PAIR-003` — censo de simetria (novo, recomendado)

Sobre um subconjunto amostrado das 2.868 linhas (para caber em teste
rápido): `espessura(i,j) == espessura(j,i)` e `overlap(i,j) == overlap(j,i)`
para **todos** os pares paralelos da amostra. Hoje reprova com
`|Δ|` de até 185,21 cm.

### Regressão do CR-1 — obrigatória no mesmo commit

Rodar `nuvem/benchmark/diagnostics_2d/run_real_cr1.py` e confirmar, contra
§26.1: **87 cobertas, 4 ausentes, 96 eixos, 91/91 aberturas, 0 paredes do
gabarito perdidas.** Já medido offline: **PASS** para `E_ovl`.

---

## L. CRITÉRIOS HARD

| id | critério | como medir | valor exigido | já medido offline |
|---|---|---|---|---|
| **H2G-1** | predicado exatamente simétrico | censo `run_a_census.py` | `|Δ| == 0` em **todos** os 4.111.278 pares | ✅ 0 |
| **H2G-2** | conjunto de candidatos invariante à ordem | `INV-PAIR-002`, 5 seeds | **0** diferenças | ✅ 0/0/0/0/0 |
| **H2G-3** | invariante à direção dos endpoints | `INV-PAIR-001` item 4 | **0** diferenças | ✅ 0 |
| **H2G-4** | `INV-PAIR-001` passa; e **reprova** a fórmula anterior | pytest | PASS / FAIL | ✅ |
| **H2G-5** | **sem regressão de cobertura** | pipeline real | `cobertas >= 87` | ✅ **87** |
| **H2G-6** | **sem regressão de eixo** | pipeline real | `eixo_ok >= 96` | ✅ **96** |
| **H2G-7** | **sem regressão de aberturas** | pipeline real | **91 de 91** | ✅ **91/91** |
| **H2G-8** | nenhuma parede do gabarito perdida | conjunto coberto vs §26.1 | **0** perdidas | ✅ 0 (W001/W010/W037/W053/W054/W068/W074 mantidas) |
| **H2G-9** | abertura `6558457` atribuída | `open_diag` | não órfã | ✅ ok |
| **H2G-10** | espúrias não pioram | pipeline real | `<= 6` | ✅ **4** |
| **H2G-11** | **CR-1 intacto** | `run_real_cr1.py` | §26.1 campo a campo | ✅ |
| **H2G-12** | **custo** | `run_f_cost.py` | FASE A **≤ +10%** | ✅ **+0,51%** |
| **H2G-13** | suíte | `py -3 -m pytest -q` | **378 + novos**, todos passando | a medir na implementação |

### Critérios que **NÃO** podem ser exigidos deste commit

| não exigir | por quê | dono |
|---|---|---|
| conjunto de **pares aceitos** invariante | resta o desempate `(i,j)`; medido 0–4 | `CR-2F-C` |
| **eixos** invariantes | `create_centerline(a,b) != (b,a)`; 47/199, até 2.421 cm | `2F-E` (novo) |
| **fingerprint das paredes** invariante | consequência dos dois acima | `CR-2F-C` + `2F-E` |
| invariância a **rotação/translação** | é condicionamento de ponto flutuante na fronteira `<=`; idêntica para as 8 estratégias, inclusive a atual | causa própria, ainda sem CR |
| `solver_decision_fingerprint` inalterado | a FASE A muda de 154 para 148 paredes; mudar é **legítimo** | — |

---

## M. RECOMENDAÇÃO

### M.1 Veredito

**`IMPLEMENTATION_READY`** para `CR-2F-B` com a estratégia **`E_ovl`**,
fórmula do item H, escopo do item I, critérios HARD do item L.

A comprovação é: 8 estratégias construídas, censo exaustivo de 4.111.278
pares, 5 permutações × 8 estratégias no pipeline real, 4 rotações,
3 translações, 3 inversões de endpoints, um controle de identidade, análise
de margem de fronteira separando ruído numérico de assimetria estrutural, e
custo medido contra baseline justo. A camada de medição foi validada contra
o motor antes de qualquer conclusão (589 candidatos idênticos, `|Δ| = 7e-15`).

### M.2 O que a implementação NÃO vai entregar

Paredes finais invariantes à ordem. **Isso é esperado e está medido**
(item D.5/F). Quem for medir o resultado precisa saber disso **antes**, ou
vai ler `E_ovl` como fracasso quando o fingerprint das paredes continuar
mudando entre seeds.

### M.3 Ressalva única

`E_ovl` custa **+74,6%** de aritmética sobre a fórmula equivalente, e só
cabe no H12 **porque vem junto com a reescrita em float puro**. Se, na
implementação real, a medição de custo der acima de **+10%** na FASE A, a
troca pré-aprovada é **`E_bis`** (item H.3 sem o ramo da sobreposição:
`abs(nx*(m1.X-m2.X) + ny*(m1.Y-m2.Y))`), que custa **−7,45%** e mantém
**87 cobertas / 96 eixos / 91 aberturas / 4 espúrias / 149 paredes**. A
perda é a de G.3: 24 pares de fragmento a 2,75° voltam a ser candidatos.
**Não trocar por `C_max`, `F_lex` ou `B_min` em nenhuma hipótese.**

### M.4 Ordem das correções seguintes (atualizada pelo achado 2F-E)

```
CR-2F-B   PAIR_PREDICATE_ASYMMETRY         <- ESTE plano
CR-2F-C   PAIR_GREEDY_INDEX_DEPENDENCE     (barata; 10 grupos de empate disputados)
CR-2F-E   CENTERLINE_ARGUMENT_ASYMMETRY    (NOVA; 47/199 eixos, ate' 2.421 cm)
CR-2F-A   MERGE_RELATION_ASYMMETRY         (a mais grave; exige T6+T3)
CR-2F-D   MERGE_CLUSTER_NON_TRANSITIVITY   (depende da decisao de projeto de 2F-A)
```

---

## N. RISCOS

1. **Um único projeto exercita a FASE A** (§26.7). `torre_easy_lo_r00_tp1` e
   `piloto_sintetico_2x2` têm zero `segments` de CAD. Amostra de tamanho 1.
   **Mitigação:** os argumentos de G.2 são geométricos e independentes do
   projeto; e `INV-PAIR-001`/`002` testam a **propriedade** (simetria), não
   o placar do gabarito.
2. **A saída de produção muda:** 154 → 148 paredes, 46.373 → 45.876 cm.
   Cobertura, eixo e aberturas ficam idênticos, e as métricas de qualidade
   melhoram — mas quem olhar só "número de paredes" e "comprimento total"
   vai ler como regressão. **Está medido e explicado em D.4.**
3. **`solver_decision_fingerprint`** (`c74c9c1a…`) deve mudar. Ficou intacto
   no CR-1; aqui a geometria da FASE A muda de verdade. Mudar é o
   comportamento **correto** — o que seria alarmante é ele **não** mudar.
4. **Risco de mascarar com o gabarito** (§2F/U.5): duas variantes podem
   cobrir o gabarito igualmente e ainda assim uma violar a invariância. Por
   isso os critérios H2G-1 a H2G-4 são **propriedades**, medidas sem o
   gabarito, e vêm antes dos H2G-5 a H2G-10.
5. **Custo** — ver M.3. É o único risco com plano B pré-aprovado.
6. **Divergência dos dois repositórios** (MeuBotao × AbrirModeladorExterno):
   `core/engine/geometry.py` existe nos dois. Se o segundo repositório tiver
   cópia dessas funções, a correção precisa ir para os dois **ou** ficar
   registrado que divergiram — já aconteceu três vezes.
7. **A instrumentação desta etapa usa monkeypatch.** Na implementação real
   as funções são chamadas diretamente. A equivalência foi checada pela
   validação D.0, mas a medição de custo deve ser **refeita** sobre o código
   real antes de fechar o H2G-12.

---

## O. ROLLBACK

O commit é **aditivo e cirúrgico**: três funções novas em `geometry.py` e
**duas linhas de chamada** em `find_wall_pairs`. As funções antigas
permanecem no arquivo, íntegras e ainda em uso pelo merge.

| cenário | ação |
|---|---|
| reverter tudo | `git revert <sha>` — nada mais depende das funções novas |
| reverter só o comportamento, mantendo as funções | trocar de volta as **duas** linhas `wall_pairing.py:374` e `:390` |
| custo estourou o H12 | trocar `E_ovl` por `E_bis` dentro da própria função (item M.3) — sem mexer em `wall_pairing.py` |

Não há migração de dados, não há estado persistido, não há mudança de
constante em `tolerances.py`. O `out_merged_baseline.json` (2.868 linhas
congeladas) não é tocado — o merge não muda.

---

## P. PLANO PASSO A PASSO DA IMPLEMENTAÇÃO

**Um problema por vez. Um commit.**

| # | passo | critério de parada |
|---|---|---|
| 1 | Branch `claude/cr-2f-b-pair-predicate-symmetry` a partir de `main` atualizada (`git fetch origin main` + fast-forward) | `git status` limpo |
| 2 | Rodar `py -3 -m pytest -q` **antes** de qualquer edição e anotar o número | **378 passed** |
| 3 | `geometry.py`: acrescentar `_pair_frame_cached`, `_pair_symmetric_overlap_ft_cached`, `_pair_symmetric_thickness_ft_cached` (item H) em **float puro**, com docstring explicando a assimetria que elas corrigem e por que as antigas continuam existindo | funções novas isoladas; nenhuma antiga tocada |
| 4 | `geometry.py`: acrescentar os três nomes em `__all__` | `import *` continua funcionando |
| 5 | Rodar a suíte | ainda **378 passed** (nada usa as funções novas ainda) |
| 6 | `wall_pairing.py`: trocar **só** as linhas `374` e `390` dentro de `find_wall_pairs`; atualizar a docstring | 2 linhas de lógica |
| 7 | Rodar a suíte | anotar **exatamente** o que quebrou; testes que fixam a contagem de paredes podem legitimamente precisar de atualização — cada um justificado por escrito |
| 8 | Escrever `INV-PAIR-001` em `tests/test_script.py` e conferir que ele **reprova** se as duas linhas do passo 6 forem revertidas | PASS agora, FAIL antes |
| 9 | Escrever `INV-PAIR-002` (`slow`) e `INV-PAIR-003` | mesma checagem do passo 8 |
| 10 | Rodar `nuvem/benchmark/diagnostics_2g/run_c_downstream.py` **com a estratégia `cur`** (que passa a ser o código real) e conferir contra a linha `E_ovl` da tabela D.4 | 569 / 199 / 148 / 87 / 96 / 91 campo a campo |
| 11 | Rodar `nuvem/benchmark/diagnostics_2d/run_real_cr1.py` | H2G-11: §26.1 intacto |
| 12 | Rodar `nuvem/benchmark/diagnostics_2g/run_f_cost.py` sobre o **código real** | H2G-12: FASE A ≤ +10% |
| 13 | Se o passo 12 falhar: aplicar M.3 (`E_bis`), refazer 10–12 | H2G-12 |
| 14 | `nuvem/REGRAS_MODULACAO_BLOCOS.md`: §26.8 **já existe** (escrito na 2G). Virar o rótulo de §26.8.3 de `DOCUMENTADO — pendência de código aberta` para **IMPLEMENTADO**, com os números reais medidos nos passos 10–12 | rótulo atualizado, sem regra duplicada nem contraditória |
| 15 | Conferir que §26.8.5 (`CENTERLINE_ARGUMENT_ASYMMETRY`, 47/199, 2.421 cm) **continua** marcado como pendência aberta — este commit **não** a resolve | pendência preservada |
| 16 | `nuvem/benchmark/RELATORIO_ETAPA_2G.md` com a medição **pós**-implementação | números reais, não os deste plano |
| 17 | Suíte completa verde; merge direto na `main` conforme CLAUDE.md (fetch + fast-forward + testes + push) | `378 + 3 passed` |

**Não fazer, em nenhum passo:** mexer em `merge_collinear_fragments`, no
`sort_key` do CR-1, em `create_centerline`, em qualquer constante de
`tolerances.py`, nas aberturas ou no solver. Se algum deles parecer
necessário, **parar e registrar** — é outro CR.

---

## Apêndice — scripts desta etapa

Todos em `nuvem/benchmark/diagnostics_2g/`. **Somente leitura** de
`nuvem/core/**`; nenhuma função geométrica do motor foi reimplementada como
verdade — as estratégias são injetadas no motor real e a camada vetorizada
é validada contra ele antes de qualquer conclusão.

| script | o que mede | saída |
|---|---|---|
| `lib2g.py` | infraestrutura: camada NumPy, monkeypatch, movimento rígido | — |
| `run_a_census.py` | validação D.0, caso mínimo D.2, censo D.1, conjuntos de candidatos | `out_a_census.json`, `out_a_candidates.json` |
| `run_b_invariance.py` | invariância D.3 + margens de fronteira | `out_b_invariance.json` |
| `run_c_downstream.py` | downstream real D.4, 8 estratégias × 6 ordens | `out_c_downstream.json` |
| `run_d_locate.py` | camadas D.5, assimetria de `create_centerline` (E), empates | `out_d_locate.json` |
| `run_e_finalists.py` | mecanismo de 2F-E, diferencial `E_bis`×`E_ovl`, fallback | `out_e_finalists.json` |
| `run_f_cost.py` | custo J, com baseline justo `cur_py` | `out_f_cost.json` |
| `run_g_invpair.py` | protótipos `INV-PAIR-001` / `INV-PAIR-002` | `out_g_invpair.json` |

Reprodução completa (≈ 9 min; `run_c`…`run_g` dependem de
`out_a_candidates.json`):

```bash
py -3 nuvem/benchmark/diagnostics_2g/run_a_census.py
py -3 nuvem/benchmark/diagnostics_2g/run_b_invariance.py
py -3 nuvem/benchmark/diagnostics_2g/run_c_downstream.py
py -3 nuvem/benchmark/diagnostics_2g/run_d_locate.py
py -3 nuvem/benchmark/diagnostics_2g/run_e_finalists.py
py -3 nuvem/benchmark/diagnostics_2g/run_f_cost.py
py -3 nuvem/benchmark/diagnostics_2g/run_g_invpair.py
```

> **Nota de ambiente:** o processo Python desta máquina tem teto de
> **~240 MB**. `lib2g.py` fixa `OPENBLAS_NUM_THREADS=1` e trabalha em blocos
> 2-D por isso — materializar a matriz 2868×2868 de um predicado (66 MB)
> derruba o interpretador. Não é detalhe de estilo: sem isso os scripts
> falham com `_ArrayMemoryError`.
