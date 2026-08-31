# ETAPA 2F — Diagnóstico de causa raiz de `ORDER_DEPENDENCE_MERGE_COLLINEAR_FRAGMENTS`

**Data:** 2026-08-31
**Base:** `origin/main` @ `0a2724b5ec6629b44dce6a0c3583022faa22f013` (CR-1 já integrado)
**Escopo:** DIAGNÓSTICO. Nada em `nuvem/core/**` foi alterado. Nenhuma correção
foi implementada. Nenhum merge foi feito.
**Suíte:** `378 passed` (`py -3 -m pytest -q`), sem alteração de core nesta sessão.
**Scripts reproduzíveis:** `nuvem/benchmark/diagnostics_2f/`

> **Nota de contagem:** o pedido cita "360 pytest passando". A `main` atual
> (`0a2724b`) coleta **378** testes (234 em `tests/test_script.py` + 144 nos
> demais). Todos passam. Nenhum teste foi adicionado nesta sessão.

---

## Resumo executivo — o que foi encontrado

Foram encontradas **quatro** causas independentes, não uma. Três estão
confirmadas com caso mínimo real medido; uma foi procurada e **não** se
confirmou.

| ID | Nome | Onde | Confirmada | Caso mínimo |
|---|---|---|---|---|
| **2F-A** | `MERGE_RELATION_ASYMMETRY` | `merge_collinear_fragments` (passada 1) | **SIM** | **2 segmentos** |
| **2F-B** | `PAIR_PREDICATE_ASYMMETRY` | `find_wall_pairs` (geração de candidatos) | **SIM** | **2 linhas mescladas** |
| **2F-C** | `PAIR_GREEDY_INDEX_DEPENDENCE` | desempate `(i, j)` do CR-1 | **SIM** | 2 candidatos empatados |
| **2F-D** | `MERGE_CLUSTER_NON_TRANSITIVITY` | `merge_collinear_fragments` (passada 1) | **SIM** | **3 segmentos** |
| — | `MERGE_OUTPUT_REFERENCE_DEPENDENCE` | `_merge_collinear_cluster` | **NÃO** (procurada, não reproduzida) | — |

Além disso, o diagnóstico de 2F-A expôs um defeito **maior que a dependência
de ordem** e presente **já na ordem original de produção**: o teste de
colinearidade agrupa fragmentos que estão a **1,27 m** e **26 m** de
distância um do outro, e a fusão então **desloca lateralmente** fragmentos
reais em até **99,55 cm**. Ver seção O.

---

## A. Baseline reproduzido

`nuvem/benchmark/diagnostics_2f/run_a_baseline.py`, primeira linha
(`seed = orig`). Estado congelado: `torre_easy_lo_r00_tgd`, layer
`Arquitetura`, espessura única de 14,0 cm, `tolerance = 2,5 cm`, 91 aberturas.

| | medido nesta sessão | registrado em §26.1 (Etapa 2E) |
|---|---|---|
| segmentos de entrada | **9.258** | 9.258 |
| linhas após `merge_collinear_fragments` | **2.868** | 2.868 |
| candidatos válidos | **589** | 589 |
| pares aceitos | **203** | 203 |
| removidas pelo dedup | **49** | — |
| paredes finais | **154** | 154 |
| paredes do gabarito cobertas | **87 de 97** | 87 de 97 |
| paredes do gabarito ausentes | **4** | 4 |
| eixo correto (≤0,5 cm) | **96 de 154** | 96 de 154 |
| eixo 10–16 cm fora | **4** | 4 |
| paredes < 50 cm | **25** | 25 |
| paredes < 20 cm | **19** | 19 |
| aberturas atribuídas | **91 de 91** | 91 de 91 |
| comprimento total | **46.373 cm** | 46.373 cm |
| tempo do merge | 12,29 s | — |

**Baseline reproduzido campo a campo.** A cadeia de replicação usada nos
scripts (`raw_clusters` + `_bridge_clusters_via_openings` +
`_merge_collinear_cluster`) devolve o **mesmo fingerprint geométrico**
(`278e458e0077b696`) que `merge_collinear_fragments` do motor — ou seja, a
replicação é fiel, não uma reimplementação aproximada.

---

## B. Múltiplas sementes (embaralhando as 9.258 linhas CRUAS)

`run_a_baseline.py`. Só a ordem da lista muda; a geometria de entrada é
idêntica em todas as execuções.

| seed | merge | fp(1 mm) | cand. | aceitos | dedup | walls | cobertas | ausentes | eixo ok | 10–16 cm | espúrias | <50 cm | <20 cm | compr. total | aberturas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **orig** | **2868** | `34c04d4e…` | **589** | **203** | 49 | **154** | **87** | 4 | 96 | 4 | 6 | 25 | 19 | 46.373 | 91/91 |
| 1 | 2872 | `5b8f069f…` | 613 | 210 | 51 | 159 | 87 | 4 | 96 | 5 | 7 | 28 | 21 | 47.344 | 91/91 |
| 2 | 2876 | `3d098242…` | 583 | 201 | 42 | 159 | 87 | 4 | 96 | 5 | 7 | 29 | 22 | 52.992 | 91/91 |
| 3 | 2874 | `85d9bec5…` | 613 | 205 | 46 | 159 | 87 | 4 | 96 | 6 | 8 | 29 | 23 | 47.496 | 91/91 |
| 10 | 2869 | `b8577c81…` | 595 | 208 | 50 | 158 | **86** | 4 | 96 | 4 | 7 | 29 | 24 | 47.384 | 91/91 |
| 42 | 2874 | `37799a20…` | 610 | 211 | 48 | 163 | **85** | **6** | 95 | **10** | 7 | 28 | 23 | 48.580 | 91/91 |

**Nenhuma execução embaralhada reproduz o baseline.** Nem em contagem, nem em
fingerprint, nem em conjunto geométrico. Diferença de conjunto (a 1 mm, ou
seja, muito acima de qualquer ruído de arredondamento): entre **85 e 123**
linhas mescladas existem numa saída e não na outra, em cada seed.

O que muda a jusante: `cobertas` cai de 87 para 85 (seed 42), `ausentes` sobe
de 4 para 6, e `eixo 10–16 cm fora` sobe de 4 para 10. As aberturas
resistiram (91/91 em todas as seeds) **nesta fase** — mas não na Fase B (ver
item J/P).

---

## C. Fingerprint geométrico canônico

Implementado em `lib2f.canon()` / `lib2f.fp()`. **Não** foi introduzido em
`nuvem/core/**` — vive só no benchmark, como pede o item 4.

Normalização, por segmento e independente da lista:

1. coordenadas convertidas para **cm** (unidade do domínio, não pés);
2. arredondadas a `nd` casas (`nd=2` → 0,01 cm = 0,1 mm; `nd=1` → 1 mm);
3. **endpoint menor primeiro** (`(a,b) if a <= b else (b,a)`) → independente
   do sentido em que a `Line` foi construída;
4. conjunto **ordenado por geometria** e serializado;
5. `sha256` do blob.

Isso permite distinguir os três casos exigidos:

- **mesma geometria / ordem diferente** → mesmo fingerprint;
- **geometria realmente diferente** → fingerprint diferente **e**
  `diff_sets()` mostra quais segmentos entraram/saíram;
- **ruído numérico** → o fingerprint muda a 0,1 mm mas **não** a 1 mm.

**Calibração do ruído:** o cache em disco das 2.868 linhas mescladas
(`out_merged_baseline.json`) faz um round-trip pés→cm→pés. O desvio máximo de
coordenada medido é **1,0 × 10⁻⁶ cm** (10 nanômetros); ele muda 19 chaves a
0,1 mm e **zero** a 1 mm. Por isso todas as conclusões deste relatório foram
verificadas **também a 1 mm** — e nenhuma delas depende do arredondamento.

---

## D. Diferenças do merge (Teste A — merge isolado)

`run_c_merge_isolate.py`. Mesmos objetos `Line` (identidade preservada),
só a ordem da lista muda. Comparação de **partições**, não de contagens.

| ordem | clusters (passada 1) | clusters (após bridge) | linhas mescladas |
|---|---|---|---|
| orig | **1704** | 1702 | 2868 |
| s1 | 1700 | 1699 | 2872 |
| s2 | 1705 | 1700 | 2876 |
| s3 | 1705 | 1700 | 2874 |
| s10 | 1703 | 1700 | 2869 |
| s42 | 1700 | 1698 | 2874 |

Respondendo às oito perguntas do item 5 do pedido:

1. **Os clusters mudam?** Sim. A partição da passada 1 **nunca** é igual à do
   baseline, em nenhuma das 5 seeds.
2. **Quais segmentos mudam de cluster?** Isolando por componentes conexas da
   união das duas partições: **28 / 22 / 25 / 26 / 27** "blocos divergentes"
   por seed, envolvendo **330 / 183 / 228 / 248 / 294** segmentos crus.
3. **Quais segmentos existem numa saída e não na outra?** 85 a 123 linhas
   mescladas por seed (a 1 mm) — item B.
4. **Quais extremos mudam?** Mudam tanto os extremos (o intervalo fundido)
   quanto a **posição lateral** da reta reconstruída — ver o caso mínimo (E)
   e a severidade (O).
5. **Quantos casos divergentes?** 128 blocos no total nas 5 seeds; tamanhos
   de **2** a **51** segmentos.
6. **A divergência acontece perto de aberturas?** 100% dos blocos divergentes
   estão a ≤100 cm de alguma abertura — **mas isso não significa nada**: no
   Layer inteiro, **85,9%** de todas as 9.258 linhas também estão. Sem esse
   controle, a conclusão seria falsa. **Não há evidência de correlação com
   abertura.**
7. **Depende de linha curta?** 100% dos blocos divergentes contêm alguma
   linha < 20 cm — **mas, de novo, 77,3% de todo o Layer é < 20 cm** (mediana
   de comprimento: **4,44 cm**). A mediana da menor linha nos blocos
   divergentes é 1,96 cm contra 4,44 cm do Layer. Há um **indício** de que
   linhas muito curtas concentram o problema (e a mecânica da causa raiz
   explica por quê — ver E/N), mas o dado bruto sozinho não prova nada.
8. **Acontece longe de abertura?** Não foi observado nenhum bloco a mais de
   100 cm de abertura — pelo motivo estatístico acima, isso **não** é
   informativo.

A passada 2 (`_bridge_clusters_via_openings`) **não corrige nada**: as
partições continuam diferentes depois dela (25 a 29 blocos divergentes).

---

## E. Primeiro/menor cluster divergente

`run_d_min_case.py`. O menor bloco divergente encontrado tem **2 segmentos**
(seed 1):

```
L3469   ( 61.9124, 265.5834) -> ( 65.7409, 265.1860)   len = 3.8491 cm
L5694   (-565.0587, 330.7485) -> (-569.3569, 331.1459) len = 4.3165 cm
```

Distância entre eles: ~627 cm em X, ~65 cm em Y.

```
ordem 1 (L3469 primeiro):   L3469 sozinho  /  L5694 sozinho
ordem 2 (L5694 primeiro):   L3469 + L5694 no MESMO cluster
```

**Matriz da relação** (tolerância = 0,2 cm):

| | perpendicular medida | compatível? |
|---|---|---|
| `d(L3469, L5694)` | **7,188096 cm** | **NÃO** |
| `d(L5694, L3469)` | **0,060519 cm** | **SIM** |

A relação de agrupamento **não é simétrica**. É essa a origem da divergência.

**Consequência geométrica:** quando eles caem no mesmo cluster, a fusão move
`L3469` de `y ≈ 265,58` para `y ≈ 269,35` (**+3,76 cm**) e `L5694` de
`y ≈ 331,15` para `y ≈ 327,77` (**−3,37 cm**). Não é uma diferença de
contagem: é geometria de parede deslocada.

---

## F. Trace passo a passo (as duas ordens)

```
ORDEM ['L3469', 'L5694']  ->  fp = d46a9d316123461a
  base=L3469  cand=L5694  paralela=True  perp=7.188096 cm  tol=0.200000 cm -> separa
  cluster ['L3469'] -> [(( 61.9124, 265.5834), ( 65.7409, 265.1860))]
  cluster ['L5694'] -> [((-569.3569, 331.1459), (-565.0587, 330.7485))]

ORDEM ['L5694', 'L3469']  ->  fp = 4347e2ae514aa2b6
  base=L5694  cand=L3469  paralela=True  perp=0.060519 cm  tol=0.200000 cm -> MERGE
  cluster ['L5694', 'L3469'] -> [((-569.6688, 327.7720), (-565.3706, 327.3746)),
                                 ((  62.2602, 269.3455), (  66.0927, 268.9912))]
```

**Ponto exato da divergência:** o primeiro e único predicado avaliado. O laço
de `merge_collinear_fragments` só compara `base` contra `other`; quem é
`base` decide de que lado a distância assimétrica é medida.

---

## G. Testes de simetria dos predicados

`run_b_symmetry.py`. Censo sobre a geometria REAL (pré-filtro vetorizado só
para achar os pares; o veredito é sempre do **código do motor**, nas duas
direções).

### G.1 Sintéticos

| caso | `d(A,B)` | `d(B,A)` | simétrico? | `ov(A,B)` | `ov(B,A)` | simétrico? |
|---|---|---|---|---|---|---|
| SYM-01 paralelas exatas | 14,000000 | 14,000000 | **SIM** | 400,000000 | 400,000000 | **SIM** |
| SYM-02 paralelas exatas, comprimentos diferentes | 14,000000 | 14,000000 | **SIM** | 424,000000 | 424,000000 | **SIM** |
| SYM-03 quase-paralelas (0,5°) | 15,744774 | 15,745374 | **NÃO** | 400,000000 | 399,862598 | **NÃO** |
| SYM-04 quase-paralelas (2,0°) | 20,971371 | 20,984154 | **NÃO** | 400,000000 | 399,267738 | **NÃO** |
| SYM-05 quase-paralelas + comprimentos muito diferentes | 15,736446 | 15,746038 | **NÃO** | 100,000000 | 100,060954 | **NÃO** |
| SYM-06 endpoints invertidos | 14,000000 | 14,000000 | **SIM** | 400,000000 | 400,000000 | **SIM** |
| SYM-07 sem sobreposição no eixo | 14,000000 | 14,000000 | **SIM** | 0,000000 | 0,000000 | **SIM** |

**Regra:** os predicados são simétricos **se e somente se** as duas linhas
forem **exatamente** paralelas. `_are_parallel_cached` aceita até
`|cross| < 0,05` (≈ **2,87°**), então a simetria não é garantida em nenhum par
real.

### G.2 Censo real

| predicado | escopo | resultado |
|---|---|---|
| `_are_parallel_cached(A,B)` vs `(B,A)` | 121.272 pares crus + 60.556 mesclados | **SIMÉTRICO** — 0 divergências (usa `abs(cross.Z)`) |
| `_distance_between_parallel_cached(A,B)` vs `(B,A)` | 121.272 pares crus | **NÃO SIMÉTRICO** — máx. `|Δ|` = **173,381937 cm** |
| `_distance_between_parallel_cached(A,B)` vs `(B,A)` | 60.556 pares mesclados | **NÃO SIMÉTRICO** — máx. `|Δ|` = **182,862929 cm** |
| `_line_pair_overlap_ft_cached(A,B)` vs `(B,A)` | 60.556 pares mesclados | **NÃO SIMÉTRICO** — 799 pares diferem, máx. `|Δ|` = **1,264796 cm** |
| relação de cluster do merge (`paralela ∧ d ≤ 2 mm`) | 121.272 pares crus | **NÃO SIMÉTRICA** — **393** pares invertem o veredito |

Exemplos reais de inversão na relação do merge (tolerância 0,2 cm):

```
i=23   j=4634   d(i,j)=0,189222 cm   d(j,i)=61,104150 cm
i=27   j=5877   d(i,j)=0,129563 cm   d(j,i)=56,901600 cm
i=66   j=3851   d(i,j)=0,182605 cm   d(j,i)=58,401750 cm
```

### G.3 Veredito de candidato de `find_wall_pairs` — `(i,j)` contra `(j,i)`

Sobre as **2.868 linhas mescladas congeladas**:

| | |
|---|---|
| pares varridos | 60.556 |
| válidos nas **duas** direções | **562** |
| válidos **só** como `(i,j)` | **27** |
| válidos **só** como `(j,i)` | **13** |
| `thickness_rank` (CR-1) **difere** entre as direções | **27** |

**`562 + 27 = 589` — exatamente o número de candidatos do baseline.** A
aritmética fecha: na ordem baseline, os 27 pares "só `(i,j)`" são enumerados
na direção que os aceita, e os 13 "só `(j,i)`" na direção que os rejeita.
Embaralhar redistribui esses **40** pares direcionais e o total cai para
perto de `562 + 40/2 = 582` — que é exatamente a faixa medida (580–587).

Exemplos:

```
i=16  j=295   d(i,j)=11,83063 cm   d(j,i)= 8,99700 cm   -> candidato só como (i,j)
i=17  j=300   d(i,j)= 8,75645 cm   d(j,i)=11,50485 cm   -> candidato só como (j,i)
i=17  j=302   d(i,j)=14,33173 cm   d(j,i)=11,50287 cm   -> rank 6 vs 49  (CR-1)
```

---

## H. Testes de transitividade

A relação de compatibilidade do merge é:

- **reflexiva:** SIM (`d(A,A) = 0`);
- **simétrica:** **NÃO** (item G);
- **transitiva:** **NÃO**.

### H.1 Prova sintética (MERGE-011)

Três fragmentos idênticos, empilhados a 0,15 cm um do outro (tolerância =
0,2 cm):

```
A: (0, 0.00) -> (400, 0.00)
B: (0, 0.15) -> (400, 0.15)
C: (0, 0.30) -> (400, 0.30)

A ~ B  = true   (0,15 cm)
B ~ C  = true   (0,15 cm)
A ~ C  = FALSE  (0,30 cm)
```

Resultado das 6 permutações — **3 partições distintas e 3 geometrias
distintas**:

| permutação | saída |
|---|---|
| `ABC`, `ACB` | 2 linhas: `y = 0,075` e `y = 0,300` |
| `BAC`, `BCA` | **1 linha**: `y = 0,150` |
| `CAB`, `CBA` | 2 linhas: `y = 0,000` e `y = 0,225` |

Como o agrupamento é **estrela** (só `base` × `other`, nunca `other` ×
`other`), quem inicia o cluster decide o resultado. É exatamente o cenário
antecipado no item 14 do pedido.

### H.2 Classificação dos 128 blocos divergentes reais

`run_g_classify.py` — para cada bloco, conta pares assimétricos e triplas não
transitivas:

| classificação | blocos |
|---|---|
| **AMBAS** (assimetria **e** não transitividade) | **66** |
| **ASSIMETRIA** apenas | **30** |
| **NÃO TRANSITIVA** apenas | **32** |
| total | **128** |

Por seed: s1 `{AMBAS 13, ASSIM 8, NTRANS 7}`, s2 `{11, 5, 6}`,
s3 `{13, 5, 7}`, s10 `{14, 6, 6}`, s42 `{15, 6, 6}`.

**As duas causas são reais e independentes.** Corrigir só a simetria deixa 32
blocos divergentes; corrigir só a transitividade deixa 30.

---

## I. Teste com o merge CONGELADO

`run_e_frozen_merge.py`. Parte das **2.868 linhas mescladas do baseline** e
**não** executa `merge_collinear_fragments`. Só a ordem dessa lista muda.

| ordem | cand. | aceitos | dedup | walls | cobertas | eixo ok | 10–16 | <50 cm | <20 cm | compr. | aberturas | Δcand (só base/só aqui) | Δwalls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **orig** | **589** | **203** | 49 | **154** | **87** | 96 | 4 | 25 | 19 | 46.373 | **91/91** | — | — |
| **orig (2ª vez)** | 589 | 203 | 49 | 154 | 87 | 96 | 4 | 25 | 19 | 46.373 | 91/91 | **0 / 0** | **0 / 0** |
| s1 | 580 | 201 | 47 | 154 | 86 | 99 | 4 | 21 | 13 | 50.958 | 91/91 | 12 / 3 | 32 / 32 |
| s2 | 583 | 201 | 42 | 151 | 87 | 96 | 4 | 19 | 13 | 47.954* | 91/91 | 13 / 7 | 32 / 29 |
| s3 | 587 | 201 | 50 | 151 | 86 | 96 | 3 | 19 | 13 | 47.954 | 91/91 | 13 / 11 | 30 / 27 |
| s10 | 584 | 203 | 47 | 156 | 86 | 97 | 4 | 23 | 19 | 51.049 | 91/91 | 12 / 7 | 26 / 28 |
| s42 | 582 | 201 | 48 | 153 | **85** | 99 | 4 | 21 | 17 | 46.443 | **90/91** | 12 / 5 | 36 / 35 |

\* valores de comprimento por seed conforme `out_e_frozen_merge.json`.

Os `Δ` foram calculados **a 0,1 mm e a 1 mm** e deram **idênticos** — não são
ruído de arredondamento.

**`589 → 583` da Etapa 2D foi reproduzido** (seed 2 devolve exatamente 583).
E o problema **não foi eliminado pelo CR-1**.

---

## J. Comportamento de `find_wall_pairs`

Com o merge congelado, embaralhar a lista muda:

- **candidatos:** 589 → 580 / 583 / 587 / 584 / 582 (variação de **−9 a −2**);
- **pares aceitos:** 203 → 201 / 201 / 201 / 203 / 201;
- **paredes finais:** 154 → 154 / 151 / 151 / 156 / 153;
- **cobertura do gabarito:** 87 → 86 / 87 / 86 / 86 / **85**;
- **aberturas:** 91/91 → 91 / 91 / 91 / 91 / **90**.

Onde ocorre, mecanismo por mecanismo:

| possibilidade levantada no item 11 do pedido | veredito medido |
|---|---|
| geração de candidatos assimétrica | **CONFIRMADA** — `_distance_between_parallel_cached` (40 pares direcionais) e `_line_pair_overlap_ft_cached` (799 pares) |
| cache indexado por `(i,j)` de forma direcional | **NÃO** — `_line_geom_cache` é por linha, não por par; não há cache de par |
| predicado não simétrico | **CONFIRMADA** (acima) |
| consumo guloso dependente dos índices | **CONFIRMADA** — ver K |
| desempate `(i,j)` dependente da ordem original | **CONFIRMADA** — ver K |

Note o sinal oposto entre as duas fases: embaralhando as **cruas**, os
candidatos **sobem** (589 → 610/613), porque o merge devolve **mais** linhas
(2.872–2.876 em vez de 2.868); embaralhando as **mescladas**, os candidatos
**caem** (589 → 580–587), porque só a assimetria direcional age. São duas
causas somando-se na Fase A completa.

---

## K. Efeito isolado do `(i, j)` do CR-1

`run_h_cr1_effect.py`. Congela o **conjunto de candidatos** (geometria fixa,
589 candidatos) e **só renumera os índices**, reordenando pelo mesmo
`sort_key` do CR-1 e repetindo o mesmo consumo guloso.

| | |
|---|---|
| grupos de empate em `(rank, −overlap_ratio, −overlap_ft)` | **106** (envolvendo 433 candidatos) |
| grupos de empate que **disputam a mesma linha** | **14** |
| pares aceitos (ordem baseline) | 203 |

| renumeração | aceitos | idêntico ao baseline? | difere em |
|---|---|---|---|
| seed 1 | 203 | **SIM** | — |
| seed 2 | 203 | **NÃO** | 2 pares |
| seed 3 | 203 | **NÃO** | 1 par |
| seed 10 | 203 | **NÃO** | 1 par |
| seed 42 | 203 | **SIM** | — |

**Conclusão exigida pelo item 10/11 do pedido:** o `(i, j)` do CR-1 garante
**determinismo** para a mesma lista, mas **não sobrevive à renumeração**.
Duas geometrias idênticas com índices diferentes podem ser escolhidas
diferentemente. Isso é uma causa **própria e menor** (1–2 pares), separada da
assimetria dos predicados (12–13 candidatos) — e **não foi introduzida** pelo
CR-1: antes dele o desempate final era a menor distância bruta, igualmente
sensível à ordem de inserção (registrado em §26.1 e no item Q da 2D).

---

## L. Determinismo × invariância — registrados separadamente

| propriedade | definição | veredito medido | evidência |
|---|---|---|---|
| **DETERMINISMO** | mesma lista → mesmo resultado, sempre | **PASSA** | `orig` vs `orig (2ª vez)`: 0 diferenças em candidatos e em paredes (item I) |
| **INVARIÂNCIA À ORDEM (merge)** | mesma geometria, ordem diferente → mesma geometria | **FALHA** | 5/5 seeds, 85–123 linhas de diferença (item B/D) |
| **INVARIÂNCIA À ORDEM (pareamento)** | idem, com merge congelado | **FALHA** | 5/5 seeds, 12–13 candidatos e 26–36 paredes de diferença (item I) |
| **INVARIÂNCIA À RENUMERAÇÃO (`(i,j)`)** | mesmo conjunto de candidatos, índices trocados | **FALHA** | 3/5 seeds, 1–2 pares (item K) |

O CR-1 melhorou o determinismo (§26.1). A Etapa 2F mede a **invariância** —
e ela falha nos três níveis.

---

## M. Casos sintéticos

`run_f_synthetic.py`. Todas as permutações de cada caso; comparação por
fingerprint geométrico a 0,001 cm.

| caso | descrição | perms | partições | saídas | veredito |
|---|---|---|---|---|---|
| MERGE-001 | 3 colineares perfeitos sobrepostos | 6 | 1 | 1 | **OK** |
| MERGE-002 | 3 colineares, gaps de 10 cm (< 40 cm tolerados) | 6 | 1 | 1 | **OK** |
| MERGE-003 | curto (5 cm) entre dois longos (400 cm) | 6 | 1 | 1 | **OK** |
| MERGE-004 | offsets 0,05 cm (**abaixo** da tolerância) | 6 | 1 | 1 | **OK** |
| MERGE-005 | offsets 0,5 cm (**acima** da tolerância) | 6 | 1 | 1 | **OK** |
| MERGE-006 | gap de 80 cm explicado por abertura real de 80 cm | 2 | 1 | 1 | **OK** |
| MERGE-007 | endpoints invertidos | 6 | 1 | 1 | **OK** |
| MERGE-008 | rotação 90° | 6 | 1 | 1 | **OK** |
| MERGE-009 | translação (+1234,5 / −987,6) | 6 | 1 | 1 | **OK** |
| MERGE-010 | 5 fragmentos, 120 permutações | 120 | 1 | 1 | **OK** |
| **MERGE-011** | **cadeia não transitiva (offsets 0,15 cm)** | 6 | **3** | **3** | **DIVERGE** |
| MERGE-012 | dois fragmentos de mesmo comprimento, offsets opostos | 2 | 1 | 1 | **OK** |
| **MERGE-013** | **quase-paralelas (0,02°) empilhadas** | 6 | **3** | **3** | **DIVERGE** |

**Leitura importante:** os 10 casos "normais" do pedido (MERGE-001..010) são
**todos invariantes**. A dependência de ordem só aparece quando a relação
deixa de ser uma relação de equivalência — cadeia dentro da tolerância
(MERGE-011) ou desalinhamento angular (MERGE-013). Isso confirma que o
defeito é **estrutural na relação**, não um bug de laço.

### M.2 `_merge_collinear_cluster` isolado (cluster fixo, ordem interna variada)

| caso | saídas distintas | veredito |
|---|---|---|
| CLU-01 empate de comprimento, offsets opostos | 1 | **OK** |
| CLU-02 empate de comprimento, quase-paralelas | 1 | **OK** |
| CLU-03 três fragmentos, dois empatados no maior comprimento | 1 | **OK** |
| CLU-04 comprimentos distintos | 1 | **OK** |
| CLU-05 empate exato de comprimento, direções diferentes | 1 | **OK** |
| CLU-06 empate exato, três fragmentos | 1 | **OK** |

**`MERGE_OUTPUT_REFERENCE_DEPENDENCE` NÃO foi reproduzida.** O risco teórico
existe (`base = max(cluster, key=comprimento)` devolve o **primeiro** máximo,
então um empate exato mudaria a direção de referência), mas em ponto flutuante
um empate **exato** de comprimento entre fragmentos **quase-paralelos** é
inalcançável: qualquer diferença angular altera o comprimento. Registrado como
**risco residual documentado, não confirmado** — não deve receber correção
sem uma reprodução real.

O somatório ponderado (`weighted_offset_sum +=` na ordem do cluster) é
sensível à ordem por não-associatividade do ponto flutuante, mas o efeito
medido está abaixo de 10⁻⁴ cm (invisível a 0,001 cm). **Irrelevante.**

---

## N. Casos mínimos reais (minimização — item 20)

Redução `9258 → bloco → mínimo`:

### N.1 Caso mínimo de **2F-A (assimetria)** — **2 segmentos**

```
L3469   ( 61.9124, 265.5834) -> ( 65.7409, 265.1860)   len = 3.8491 cm
L5694   (-565.0587, 330.7485) -> (-569.3569, 331.1459) len = 4.3165 cm

d(L3469, L5694) = 7,188096 cm   -> NÃO compatível
d(L5694, L3469) = 0,060519 cm   -> compatível
razão de assimetria: 119×
```

### N.2 Caso mínimo **mais extremo** de 2F-A — **2 segmentos**

Extraído do cluster de 10 fragmentos descrito no item O:

```
L1076   ( 2066.420, 457.248) -> ( 2068.620, 457.248)   len = 2.20 cm   ang =  0,0000°
L5682   ( -569.275, 330.546) -> ( -573.490, 330.343)   len = 4.22 cm   ang =  2,7499°

d(L1076, L5682) =   0,0504 cm   -> compatível  (!!)
d(L5682, L1076) = 126,8034 cm   -> NÃO compatível
razão de assimetria: 2.515×
```

Os dois segmentos estão a **26,4 metros** um do outro em X e a **1,27 metro**
em Y. São julgados "colineares dentro de 2 mm".

**Mecânica:** `L5682` tem 4,22 cm de comprimento e 2,75° de inclinação. A
reta **infinita** dele, prolongada 2.638 cm até o X de `L1076`, sobe
`2638 · tan(2,75°) ≈ 126,7 cm` e passa **exatamente** sobre `L1076`. Como
`_distance_between_parallel_cached` mede a distância do **ponto médio de
uma** linha à **reta infinita da outra**, o teste aprova.

Um fragmento de 2–4 cm tem sua direção estimada sobre 2–4 cm: um erro de
desenho de 0,1 mm já vale ~0,15° de inclinação, e 0,15° prolongados por 40 m
valem mais de 10 cm.

### N.3 Caso mínimo de **2F-D (não transitividade)** — **3 segmentos**

MERGE-011 (item H.1). Existem 32 blocos reais puramente não-transitivos e
66 mistos; o menor bloco puramente não-transitivo tem 3 segmentos.

### N.4 Caso mínimo de **2F-B (assimetria no pareamento)** — **2 linhas mescladas**

```
linha 16 x linha 295 :  d(16,295) = 11,83063 cm   d(295,16) =  8,99700 cm
```
Com espessura alvo 14 cm e tolerância 2,5 cm, a janela aceita é
`[11,5 ; 16,5]`: como `(i,j)` o par é candidato; como `(j,i)` não é.

### N.5 Caso mínimo de **2F-C (`(i,j)` guloso)** — 2 candidatos empatados

14 grupos de empate reais disputam a mesma linha (item K).

---

## O. Impacto downstream — e um achado maior que a dependência de ordem

`run_i_downstream.py` e `run_g_classify.py`.

### O.1 Fase A completa (embaralhando as 9.258 cruas)

| seed | cobertura | **paredes do gabarito perdidas** | ganhas | eixo ok | 10–16 cm | espúrias | aberturas órfãs |
|---|---|---|---|---|---|---|---|
| s1 | 87 → 87 | — | — | 96 | 5 | 7 | 0 |
| s2 | 87 → 87 | — | — | 96 | 5 | 7 | 0 |
| s3 | 87 → 87 | — | — | 96 | 6 | 8 | 0 |
| s10 | 87 → **86** | **W037** | — | 96 | 4 | 7 | 0 |
| s42 | 87 → **85** | **W053, W054** | — | 95 | **10** | 7 | 0 |

### O.2 Merge congelado (embaralhando só as 2.868 mescladas)

| seed | cobertura | **paredes do gabarito perdidas** | **aberturas que viram órfãs** | eixo ok | 10–16 cm |
|---|---|---|---|---|---|
| s1 | 87 → **86** | **W037** | — | 99 | 4 |
| s2 | 87 → 87 | — | — | 96 | 4 |
| s3 | 87 → **86** | **W037** | — | 96 | 3 |
| s10 | 87 → **86** | **W001** | — | 97 | 4 |
| s42 | 87 → **85** | **W010, W037** | **`element_id 6558457`** | 99 | 4 |

Nenhuma parede é **ganha** em nenhum cenário: a permutação só **perde**
cobertura. W037 é a mais frágil (3 de 5 seeds); W001 é justamente a parede
de 424 cm com `r_long = 0,2802` já documentada em §26.2.

### O.3 **Severidade geométrica na ordem ORIGINAL de produção**

Este é o achado mais grave da sessão e **não depende de embaralhar nada**.

Medindo, para cada um dos 9.258 fragmentos crus, o quanto ele é deslocado
lateralmente da própria posição pela reta que o cluster produziu
(ordem original, pipeline de produção):

| | |
|---|---|
| deslocamento mediano | **0,0000 cm** |
| fragmentos deslocados **acima da própria tolerância** (0,2 cm) | **136** |
| fragmentos deslocados **acima de 1 cm** | **82** |
| fragmentos deslocados **acima de 3 cm** | **60** |
| **deslocamento máximo** | **99,5479 cm** |

Cluster responsável pelo pior caso (10 fragmentos, ordem original):

```
BASE idx=1076  ( 2066.420, 457.248)->( 2068.620, 457.248)  len=2.20cm  ang=0,0000°
     idx=1081  ( 2068.620, 457.248)->( 2064.220, 457.248)  len=4.40cm  ang=0,0000°  d(base,x)=0,0000
     idx=1085  ( 2068.620, 457.248)->( 2064.220, 457.248)  len=4.40cm  ang=0,0000°  d(base,x)=0,0000
     idx=1100  ( 2068.620, 457.248)->( 2064.220, 457.248)  len=4.40cm  ang=0,0000°  d(base,x)=0,0000
     idx=1308  (-1872.180, 457.248)->(-1876.580, 457.248)  len=4.40cm  ang=0,0000°  d(base,x)=0,0000
     idx=1310  (-1874.380, 457.248)->(-1876.580, 457.248)  len=2.20cm  ang=0,0000°  d(base,x)=0,0000
     idx=1318  (-1876.580, 457.248)->(-1872.180, 457.248)  len=4.40cm  ang=0,0000°  d(base,x)=0,0000
     idx=1331  (-1876.580, 457.248)->(-1872.180, 457.248)  len=4.40cm  ang=0,0000°  d(base,x)=0,0000
     idx=5682  ( -569.275, 330.546)->( -573.490, 330.343)  len=4.22cm  ang=2,7499°  d(base,x)=0,0504   d(x,base)=126,8034
     idx=5696  ( -569.275, 330.546)->( -565.059, 330.748)  len=4.22cm  ang=2,7513°  d(base,x)=0,0120   d(x,base)=126,6009
```

O cluster tem **39,45 m de extensão em X** e **1,27 m em Y**, com variação
angular de **2,75°**, e é tratado como uma única reta. Os dois últimos
fragmentos são reposicionados em mais de 1 metro.

**Conclusão do item 16 do pedido:** nem toda diferença intermediária é
crítica — mas esta é. A dependência de ordem é um **sintoma**; o
agrupamento errado é o defeito, e ele já está na saída de produção de hoje.

---

## P. Aberturas afetadas

- **Fase A completa (5 seeds):** nenhuma abertura perdida — 91/91 em todas.
- **Merge congelado, seed 42:** **1** abertura perde a parede
  (`element_id 6558457`), 91/91 → 90/91.

Ou seja: a conquista de "91 de 91" do CR-1 (§26.1) **não é uma propriedade
estável** — ela depende da ordem em que as linhas chegam.

## Q. Paredes afetadas

Paredes do gabarito que **desaparecem** só por causa da ordem:
**W001, W010, W037, W053, W054** (5 paredes distintas, nunca mais de 2 por
execução). Nenhuma parede é ganha.

Além disso, entre 26 e 36 das ~154 paredes finais (≈ **20%**) são
geometricamente diferentes em cada permutação, mesmo quando a contagem
coincide.

---

## R. Causas raiz encontradas

### CAUSA 2F-A — `MERGE_RELATION_ASYMMETRY`

```
A relação de compatibilidade usada por merge_collinear_fragments para formar
clusters é:

    _are_parallel_cached(base, other)  AND
    _distance_between_parallel_cached(base, other) <= COLLINEAR_MATCH_TOLERANCE_FT

_distance_between_parallel_cached(A, B) mede a distância do PONTO MÉDIO de A
até a RETA INFINITA de B. Isso NÃO é simétrico quando as duas linhas não são
exatamente paralelas — e `_are_parallel_cached` aceita até 2,87° de diferença.

Caso mínimo: 2 segmentos.
    d(L1076, L5682) =   0,0504 cm  -> compatível
    d(L5682, L1076) = 126,8034 cm  -> NÃO compatível
    razão 2.515x, segmentos a 26,4 m um do outro

Censo real: 393 pares assimétricos entre 121.272 pares crus avaliados;
            |Δ| máximo de 173,38 cm.

Impacto: 1704 -> 1700..1705 clusters; 2868 -> 2869..2876 linhas mescladas;
         85 a 123 linhas de diferença geométrica por seed;
         E, já na ordem de produção: 136 fragmentos deslocados acima da
         própria tolerância, 60 acima de 3 cm, máximo 99,55 cm.
```

### CAUSA 2F-B — `PAIR_PREDICATE_ASYMMETRY`

```
Na varredura O(n^2) de find_wall_pairs, o par é sempre avaliado como (i, j)
com i < j. Dois predicados dessa varredura são direcionais:

    _distance_between_parallel_cached(cache_i, cache_j)   (máx. |Δ| = 182,86 cm)
    _line_pair_overlap_ft_cached(cache_i, cache_j)        (799 pares, máx. |Δ| = 1,26 cm)

Caso mínimo: 2 linhas mescladas.
    linha 16 x linha 295:  d(16,295)=11,83063 cm  d(295,16)=8,99700 cm
    (janela aceita para 14 cm +/- 2,5 cm = [11,5 ; 16,5])

Censo real, com o merge CONGELADO:
    562 pares válidos nas duas direções
     27 válidos SÓ como (i,j)
     13 válidos SÓ como (j,i)
     27 com thickness_rank (CR-1) diferente entre as direções
    562 + 27 = 589 = exatamente o baseline

Impacto: 589 -> 580..587 candidatos; 26 a 36 paredes finais diferentes;
         W001/W010/W037 perdidas; 1 abertura órfã (seed 42).
NÃO foi eliminada pelo CR-1.
```

### CAUSA 2F-C — `PAIR_GREEDY_INDEX_DEPENDENCE`

```
O sort_key do CR-1 termina em (i, j). Isso garante DETERMINISMO para a mesma
lista, mas (i, j) são posições na lista, não identidade geométrica: renumerar
as linhas muda o desempate.

Caso mínimo: 2 candidatos com (rank, -overlap_ratio, -overlap_ft) idênticos
disputando a mesma linha.

Censo real: 106 grupos de empate (433 candidatos), 14 deles disputando a
mesma linha. Com o MESMO conjunto de 589 candidatos, renumerar os índices
muda 1 a 2 pares aceitos em 3 de 5 seeds.

Impacto: o MENOR das quatro causas. Não é regressão do CR-1 (o critério
anterior — menor distância bruta — era igualmente sensível).
```

### CAUSA 2F-D — `MERGE_CLUSTER_NON_TRANSITIVITY`

```
Mesmo tornando a relação simétrica, ela continua NÃO TRANSITIVA: dois
fragmentos podem estar a 0,15 cm de um terceiro e a 0,30 cm entre si, com
tolerância de 0,20 cm. E o agrupamento é ESTRELA (só base x other), então o
cluster é {base} união {x : x ~ base} — quem inicia decide.

Caso mínimo: 3 segmentos (MERGE-011).
    A~B true, B~C true, A~C false
    -> 6 permutações produzem 3 partições e 3 geometrias distintas.

Censo real: dos 128 blocos divergentes, 32 são puramente não transitivos e
66 combinam não transitividade com assimetria.
```

### NÃO CONFIRMADA — `MERGE_OUTPUT_REFERENCE_DEPENDENCE`

Procurada explicitamente (item 15 do pedido) com 6 casos sintéticos,
incluindo empates exatos de comprimento. `_merge_collinear_cluster` foi
**invariante** em todos. Registrada como risco teórico documentado, sem
correção associada.

---

## S. Prioridade das causas

Ordenadas por (1) impacto na geometria, (2) frequência, (3) paredes
afetadas, (4) aberturas afetadas, (5) risco da correção:

| # | causa | impacto geométrico | frequência | paredes | aberturas | risco da correção |
|---|---|---|---|---|---|---|
| **1** | **2F-A** `MERGE_RELATION_ASYMMETRY` | **deslocamento de até 99,55 cm, já em produção** | 393 pares / 96 dos 128 blocos | até 2 por execução | 0 (nesta fase) | **alto** (muda a saída de produção e o custo da FASE A) |
| **2** | **2F-D** `MERGE_CLUSTER_NON_TRANSITIVITY` | muda clusters, 3 geometrias por 6 permutações | 98 dos 128 blocos | idem 2F-A | idem | **alto** (a escolha entre estrela e fecho transitivo muda o comportamento) |
| **3** | **2F-B** `PAIR_PREDICATE_ASYMMETRY` | 12–13 candidatos, 26–36 paredes | 40 pares direcionais + 27 de rank | W001/W010/W037 | **1** | **médio** |
| **4** | **2F-C** `PAIR_GREEDY_INDEX_DEPENDENCE` | 1–2 pares | 14 grupos de empate | — | — | **baixo** |

2F-A e 2F-D são **a mesma função** e devem ser resolvidas na mesma revisão de
projeto da relação — mas em **commits separados**, com medição isolada de
cada uma, conforme o item 19 do pedido.

---

## T. Possíveis estratégias de correção (apenas planejamento — item 24)

Custo de referência medido nesta sessão: `merge_collinear_fragments` =
**11,35–14,60 s**; FASE A completa = **~25 s** (§26.1). A passada 1 faz
≈ 9.258 × 1.704 / 2 ≈ **7,9 M** avaliações de predicado.

| estratégia | resolve | complexidade | custo estimado | observação |
|---|---|---|---|---|
| **T1. Ordenação canônica da entrada** antes de agrupar | invariância à ordem (2F-A/2F-D como *sintoma*) | `O(n log n)` ≈ 120 k ops | **~10 ms** (desprezível) | **Fecha o ticket, não conserta a geometria.** Continua deslocando fragmentos em 99 cm — só que sempre igual. Registrar explicitamente como **paliativo**, nunca como correção |
| **T2. Simetrizar o predicado** (`max(d(A,B), d(B,A)) <= tol`) | 2F-A | mesma `O(n·k)`, ~2× aritmética por par | **+30 a 50%** no merge (12,3 s → ~16–18 s); FASE A ~25 s → ~29–31 s | **Estoura o requisito HARD H12 (≤10%)** do plano da 2D. Precisa de poda antes |
| **T3. Testar os DOIS endpoints** do candidato contra a reta da base (em vez do ponto médio) | 2F-A **e** o deslocamento de 99 cm | ~2× aritmética | idem T2 | É o teste **geometricamente correto** de "colinear". Também **poda** clusters absurdos → pode ficar mais barato que T2 na prática (clusters menores). **Precisa ser medido, não assumido** |
| **T4. Fecho transitivo com Union-Find** sobre a relação simetrizada | 2F-D | requer todos os pares: `O(n²)` = 42,8 M | **inaceitável** sem índice (>60 s) | Só viável com T6 |
| **T5. Clustering global por chave canônica de reta** (θ, ρ quantizados) | 2F-A e 2F-D de uma vez | `O(n log n)` | **~0,1 s** | **Elegante e barato, mas frágil:** depende da direção estimada, que é justamente o que fragmentos de 2 cm não têm. Precisa de um estimador de direção robusto antes |
| **T6. Índice espacial/angular** (grade + faixa de ângulo) para pré-filtrar | viabiliza T2/T3/T4 | `O(n log n)` de construção, ~`O(n·c)` de consulta | o pré-filtro NumPy usado nesta sessão reduziu 42,8 M pares para **121.272** (350×) em <1 s | Já **provado** nesta sessão (`run_b_symmetry.near_pairs`) |
| **T7. Piso de comprimento para servir de BASE** de cluster | atenua 2F-A | `O(n)` | desprezível | Um fragmento de 2 cm não deveria ditar a direção de uma reta de 40 m. **Atenua, não corrige** |
| **T8. Chave geométrica canônica no `sort_key`** (em vez de `(i,j)`) | 2F-C | `O(cand log cand)` | +0,5 ms sobre 589 candidatos (§26.1: 0,45 ms) | Correção isolada, barata e de baixo risco |

**Combinação recomendada para estudo:** T6 (índice) + T3 (endpoints) para a
causa 1/2, e T8 para a causa 4. T1 **não** deve ser adotada sozinha.

---

## U. Riscos

1. **Toda correção em 2F-A/2F-D muda a saída de produção.** O baseline de
   §26.1 (87 cobertas, 91/91 aberturas, 154 paredes) foi obtido **com** o
   agrupamento defeituoso. Corrigir o agrupamento pode piorar esses números
   antes de melhorá-los, e isso **não** significa que a correção está errada.
   Nenhuma correção pode ser julgada só pelo placar do gabarito.
2. **Risco de performance real.** T2/T3 sozinhos estouram o requisito
   HARD H12 (≤10%) herdado do plano da 2D. O índice (T6) tem que vir junto,
   ou o requisito precisa ser renegociado com o usuário.
3. **Fecho transitivo pode fundir demais.** Tornar a relação transitiva por
   Union-Find junta cadeias de fragmentos a 0,15 cm sucessivos — exatamente o
   "deslocamento lateral" que a tolerância apertada de 2 mm foi introduzida
   para eliminar (ver a nota em `COLLINEAR_MATCH_TOLERANCE_M`). É uma troca,
   não uma melhoria automática.
4. **`solver_decision_fingerprint`** (`c74c9c1a…`) deve ser reavaliado: ele
   ficou inalterado no CR-1, mas uma correção de geometria da FASE A pode
   legitimamente mudá-lo.
5. **Risco de mascarar com o gabarito.** Duas variantes podem cobrir o
   gabarito igualmente e ainda assim uma delas violar a invariância. A
   propriedade a proteger é **mesma geometria de entrada → mesma geometria de
   saída**, independente do humano (item 17 do pedido).
6. **Um único projeto exercita a FASE A** (item W). Qualquer correção será
   validada contra uma amostra de tamanho 1.

---

## V. Testes de regressão futuros (a criar JUNTO da correção, não antes)

| id | causa | fixture | critério |
|---|---|---|---|
| `INV-MERGE-001` | 2F-A | os 2 segmentos de N.2 (`L1076`/`L5682`) | `compat(A,B) == compat(B,A)`; e os dois **não** podem cair no mesmo cluster |
| `INV-MERGE-002` | 2F-A | os 2 segmentos de N.1 (`L3469`/`L5694`) | idem |
| `INV-MERGE-003` | 2F-D | MERGE-011 (3 segmentos, offsets 0,15 cm) | as 6 permutações produzem **o mesmo** fingerprint geométrico |
| `INV-MERGE-004` | 2F-D | MERGE-013 (quase-paralelas 0,02°) | idem |
| `INV-MERGE-005` | regressão | MERGE-001..010 | continuam invariantes (já são hoje) |
| `INV-MERGE-006` | 2F-A | cluster de 10 fragmentos do item O.3 | nenhum fragmento pode ser deslocado mais que `COLLINEAR_MATCH_TOLERANCE` |
| `INV-PAIR-001` | 2F-B | linhas 16/295 do item N.4 | o veredito de candidato não pode depender da direção |
| `INV-PAIR-002` | 2F-B | as 2.868 mescladas, 5 seeds | mesmo conjunto geométrico de candidatos |
| `INV-PAIR-003` | 2F-C | 589 candidatos congelados, índices renumerados | mesmo conjunto de pares aceitos |
| `INV-FASEA-001` | integração | 9.258 segmentos, 5 seeds | mesmo fingerprint geométrico da saída (marcado `slow`) |

Os fixtures sintéticos já existem em `diagnostics_2f/run_f_synthetic.py` e os
reais em `out_c_merge_isolate.json` / `out_d_min_case.json`. **Nenhum foi
promovido a teste permanente nesta sessão**, conforme o item 13 do pedido.

---

## W. Limitação cross-project (reconfirmada)

Medido de novo nesta sessão:

| projeto | arquivo | `segments` de CAD | walls | openings |
|---|---|---|---|---|
| `torre_easy_lo_r00_tgd` | `input_real.json` | **9.258** | 0 | 91 |
| `torre_easy_lo_r00_tp1` | `input.json` | **0** | 96 | 0 |
| `piloto_sintetico_2x2` | `input.json` | **0** | 12 | 0 |

**Continua verdadeiro:** só existe **um** projeto capaz de executar a FASE A.
Nenhuma validação cross-project foi inventada. A exigência de §26.7 (capturar
`input_real.json` **com** os `segments` do Layer de CAD em todo projeto novo)
segue em aberto e agora bloqueia **quatro** correções, não uma.

---

## X. Recomendação da PRIMEIRA correção a implementar

**`CR-2F-B` — `PAIR_PREDICATE_ASYMMETRY` em `find_wall_pairs`.**

Não é a causa de maior impacto (essa é 2F-A). É a que deve vir **primeiro**,
por quatro razões medidas:

1. **É isolável.** Com o merge congelado, ela é a **única** causa em jogo
   (2F-C responde por 1–2 pares dos 12–13 candidatos que mudam). O teste B
   desta sessão já é o harness de verificação, pronto.
2. **Não mexe na geometria de saída do merge.** O conjunto das 2.868 linhas
   não muda, então o baseline de §26.1 permanece comparável campo a campo —
   ao contrário de 2F-A, que muda tudo de uma vez e destrói a base de
   comparação.
3. **Tem impacto downstream concreto e verificável:** recupera a estabilidade
   de W001/W010/W037 e da abertura `6558457`, e as métricas de aceitação já
   existem (87 cobertas / 91 aberturas / 96 eixos).
4. **Risco e custo baixos.** A correção provável é medir a distância e a
   sobreposição de forma **simétrica** (por exemplo, a média ou o máximo das
   duas direções, ou medir contra a linha **mais longa** do par, que é a de
   direção mais confiável) — dentro do laço O(n²) que já roda, sem estrutura
   nova. A ordenação de 589 candidatos custa 0,45 ms (§26.1): há folga.

Ordem sugerida das correções seguintes, **uma por commit** (item 19):

```
CR-2F-B   PAIR_PREDICATE_ASYMMETRY        (primeira - recomendada aqui)
CR-2F-C   PAIR_GREEDY_INDEX_DEPENDENCE    (barata, fecha o pareamento)
CR-2F-A   MERGE_RELATION_ASYMMETRY        (a mais grave; exige T6 + T3 e
                                           renegociar o requisito de tempo)
CR-2F-D   MERGE_CLUSTER_NON_TRANSITIVITY  (depende da decisão de projeto
                                           tomada em CR-2F-A)
```

**Antes de CR-2F-A**, é obrigatório decidir com o usuário: o objetivo é
apenas **invariância** (T1 resolve em 10 ms) ou **corrigir o agrupamento**
(fragmentos a 26 m deixarem de ser "colineares")? São objetivos diferentes,
com custos e riscos diferentes, e o item O.3 mostra que o segundo é o que
realmente importa.

---

## Apêndice — scripts desta etapa

Todos em `nuvem/benchmark/diagnostics_2f/`. **Somente leitura** de
`nuvem/core/**`; nenhuma função geométrica foi reimplementada (todas são
importadas ao vivo do motor via `solver_bridge.engine()`).

| script | item do pedido | saída |
|---|---|---|
| `lib2f.py` | infraestrutura, fingerprint canônico | — |
| `run_a_baseline.py` | A, B, C | `out_a_baseline.json` |
| `run_b_symmetry.py` | G | `out_b_symmetry.json` |
| `run_c_merge_isolate.py` | D, E (Teste A) | `out_c_merge_isolate.json` |
| `run_d_min_case.py` | E, F, N, item 20 | `out_d_min_case.json` |
| `run_e_frozen_merge.py` | I, J, L (Teste B) | `out_e_frozen_merge.json` |
| `run_f_synthetic.py` | M (MERGE-001..013, CLU-01..06) | `out_f_synthetic.json` |
| `run_g_classify.py` | H, O.3, controles estatísticos | `out_g_classify.json` |
| `run_h_cr1_effect.py` | K | `out_h_cr1_effect.json` |
| `run_i_downstream.py` | O, P, Q | `out_i_downstream.json` |

Reprodução completa:

```bash
py -3 nuvem/benchmark/diagnostics_2f/run_a_baseline.py
py -3 nuvem/benchmark/diagnostics_2f/run_b_symmetry.py
py -3 nuvem/benchmark/diagnostics_2f/run_c_merge_isolate.py
py -3 nuvem/benchmark/diagnostics_2f/run_d_min_case.py
py -3 nuvem/benchmark/diagnostics_2f/run_e_frozen_merge.py
py -3 nuvem/benchmark/diagnostics_2f/run_f_synthetic.py
py -3 nuvem/benchmark/diagnostics_2f/run_g_classify.py
py -3 nuvem/benchmark/diagnostics_2f/run_h_cr1_effect.py
py -3 nuvem/benchmark/diagnostics_2f/run_i_downstream.py
```

`run_c` depende de nada; `run_d` depende de `out_c_merge_isolate.json`;
os demais são independentes. Tempo total ≈ 12 min.
