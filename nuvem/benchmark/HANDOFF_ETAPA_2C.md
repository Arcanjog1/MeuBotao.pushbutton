# HANDOFF - ETAPA 2C (diagnostico de causa raiz) - INTERROMPIDA

> Documento de CHECKPOINT. A sessao foi encerrada por limite de tokens no
> meio da analise. Nada foi corrigido: nenhum arquivo de `nuvem/core/**`,
> do solver, do Wall Modeling, de tolerancias, de catalogo ou de aberturas
> foi tocado nesta sessao.
>
> Convencao usada em todo o documento:
> **FATO MEDIDO** = numero que saiu de execucao real nesta sessao.
> **HIPOTESE** = leitura plausivel, ainda nao provada.
> **PENDENTE** = nao foi executado.

---

## 1. Objetivo original da Etapa 2C

Diagnostico de causa raiz (SEM correcao) de tres coisas, no projeto
`torre_easy_lo_r00_tgd`:

1. as 9 aberturas (de 91) que a FASE A do Wall Modeling nao atribuiu a
   nenhuma parede, hoje rotuladas `WALL_MODELING_ERROR` - rotulo que a
   Etapa 2C tinha ordem explicita de NAO preservar por heranca;
2. a hipotese prioritaria do usuario: **o projetista humano teria movido
   portas/janelas ao longo da parede (1 cm, alguns cm, aumentando uma
   boneca e diminuindo a outra) para a modulacao fechar** - e por isso o
   INPUT e o REFERENCE nao bateriam;
3. a fragmentacao das 167 walls do Wall Modeling contra as ~97 do
   gabarito humano, com atencao especial a fragmentos de 8-16 cm.

Entrega pedida: relatorio A-S (ver secao 18 deste handoff).
Restricoes: nao investigar o solver de blocos (COMPENSATOR_CONSECUTIVE,
PRISM_CONTINUOUS_JOINT, JUNCTION_NOT_ALTERNATING) - sao downstream.

---

## 2. Commit / HEAD usado nesta sessao

- HEAD no inicio da sessao: `eb9dfc220be46a623ff22b318102d2877c75a57f`
  (= `origin/main` naquele momento) - **confirmado**, era o commit pedido.
- **FATO MEDIDO:** durante a sessao o HEAD local mudou sozinho para
  `7dea3562b0c878f8aefd7831fd143e87ac031733`
  (`docs: formalize atomic external editor rules`), vindo de fora desta
  sessao (provavelmente o watcher de sincronizacao). O diff
  `eb9dfc22..7dea356` toca **um unico arquivo**,
  `nuvem/REGRAS_MODULACAO_BLOCOS.md` (+15/-4). **Nenhum** artefato do
  benchmark usado na analise mudou, entao todas as medicoes abaixo
  continuam validas para os dois commits.

## 3. `solver_decision_fingerprint`

```
c74c9c1ae0e3f169f76e05fe53c01a858fce0af5b4e9d5f1b86fd71e92d2a316
```

Conferido em `projects/torre_easy_lo_r00_tgd/baselines/baseline_real_v1.json`.
Mede **as pecas que o solver decide** (`tests/solver_bench.py`).

## 4. `wall_modeling_engine_sha256`

```
f017124964a806fba8d4249add34db665f86282ae2a8c6fecb1018713d3bad8a
```

Conferido no campo homonimo de `wall_modeling_snapshot.json` e em
`baselines/baseline_real_v1.json`. Mede o **sha256 do arquivo
`nuvem/core/wall_modeling.py`**. Nao confundir com o de cima.

---

## 5. Arquivos do benchmark que foram lidos

Contexto minimo:

- `CLAUDE.md` (raiz do pushbutton e raiz de `Scripts.extension`)
- `AGENTS.md`
- `nuvem/benchmark/README.md` (integral, 338 linhas)

Artefatos de `nuvem/benchmark/projects/torre_easy_lo_r00_tgd/`:

- `metadata.json` (integral)
- `scope_summary.json` (integral)
- `baselines/baseline_real_v1.json` (integral)
- `provisional_2b/README.txt` (integral)
- `unassigned_openings_audit.json` (integral - as 9 aberturas)
- `input_real.json` (schema + 9258 segmentos + 91 aberturas + catalogo)
- `reference.json` (97 walls, openings/junctions/rows; schema + geometria)
- `wall_modeling_snapshot.json` (167 walls, 272 nodes, 82 openings_per_wall,
  2450 unused_lines, diagnostics)

Codigo lido (somente leitura, nada alterado):

- `nuvem/benchmark/wall_modeling_bridge.py` (integral)
- `nuvem/core/engine/wall_pairing.py` -> `find_wall_pairs` (linhas 266-445)
- `nuvem/core/engine/tolerances.py` (constantes)
- `nuvem/core/engine/opening_audit.py` (constantes)
- `nuvem/benchmark/extract/revit_dump.py`, `extract/reconstruct.py` (greps)

Fora do repo (dumps brutos que ainda existem em `%TEMP%`, uteis para a
proxima sessao - ver secao 13):
`C:\Users\CIVIX\AppData\Local\Temp\6e9fa79d-e629-4af1-9c3d-3fac6b806f23\`

**NAO foram lidos** (grandes, nao precisou ate' o ponto de parada):
`comparison.json`, `scoped_comparison.json`, `findings.json`,
`score.json`, `scoped_score.json`, `reference_findings.json`,
`catalog_comparison.json`, `evaluation_scope.json`, `input.json`.

---

## 6. Comandos executados

Todos com `py -3` (nesta maquina `python`/`python3` sao o atalho quebrado
da Store). Scripts de diagnostico escritos em scratchpad e depois copiados
para `nuvem/benchmark/diagnostics_2c/` (ainda **nao commitados**).

| # | comando | o que fez |
|---|---|---|
| 1 | `git log -1`, `git rev-parse origin/main`, `git status` | confirmar HEAD |
| 2 | inspecao de schema dos JSON (script inline) | mapear `input_real`, `reference`, `wall_modeling_snapshot` |
| 3 | `diagnostics_2c/op_match.py` | 1o casamento INPUT x HUMANO (janela larga, 400 cm) |
| 4 | `inspect2.py` (*) | listar pares com centro > 1 cm e vizinhancas dos sem-par |
| 5 | `diagnostics_2c/op_match2.py` | casamento ESTRITO + along/perp + limites + bonecas |
| 6 | `inspect3.py` (*) | residuo sistematico, dsill/dhead, 16 sem contraparte |
| 7 | `diagnostics_2c/frag.py` | distribuicao de comprimento das 167/97 walls + fragmentos |
| 8 | `diagnostics_2c/trace_stage.py` | **re-executa a FASE A headless** e grava os estados intermediarios |
| 9 | `diagnostics_2c/trace9.py` | trace geometrico das 9 aberturas (CAD bruto / merge / unused / walls) |
| 10 | `diagnostics_2c/unused.py` | 2450 `unused_lines` por motivo, linhas longas perdidas |
| 11 | `diagnostics_2c/provenance.py` | provenance CAD -> wall: qual par (i,j) gerou cada parede |
| 12 | `diagnostics_2c/prov2.py` | quantificacao global do roubo de face + pares verdadeiros perdidos |

(*) `inspect2.py` e `inspect3.py` ficaram so' no scratchpad; a saida deles
esta' integralmente transcrita neste handoff (secoes 8 e 12).

**A FASE A foi reproduzida BIT A BIT**: `trace_stage.py` devolveu
`merge 9258 -> 2868`, `find_wall_pairs -> 209 paredes / 2450 sobrando`,
`dedup -42 -> 167`, e o mesmo `diagnostics.wall_pairing`
(`parallel_pairs=1332676`, `offset_suspect_count=6`, `cap_clipped_count=11`)
que ja' estava gravado em `wall_modeling_snapshot.json`. Ou seja: o
snapshot do repo e' reproduzivel headless e serve de base segura.

## 7. Os dois comandos que falharam (e por que)

1. **`inspect1.py` - `Permission denied` / `can't open file 'C:\Program Files\Git\inspect1.py'`.**
   Causa: a variavel `$TMPD` nao existia naquele shell (cada chamada do
   Bash abre um shell novo; o `export` da chamada anterior nao persiste).
   O heredoc tentou escrever em `/inspect1.py`. **Corrigido** re-emitindo
   o comando com `export TMPD=...` na mesma linha. Sem impacto no
   resultado.

2. **`provenance.py` (1a execucao) - `ModuleNotFoundError: No module named 'wall_pairing'`.**
   Causa: tentei `import wall_pairing as wp` diretamente. O motor headless
   e' carregado por `solver_bridge.engine()` como UM modulo unico chamado
   `script_under_test`, que ja' reexporta os helpers privados de
   `wall_pairing`. **Corrigido** com `wp = mod`. Verificado antes de
   re-rodar que `mod` expoe `_line_geom_cache`, `_are_parallel_cached`,
   `_distance_between_parallel_cached`, `_closest_target_thickness_ft`,
   `_line_pair_overlap_ft_cached`, `MIN_WALL_THICKNESS_FT`,
   `MIN_WALL_SEGMENT_ABS_FLOOR_FT`, `MIN_WALL_SEGMENT_OVERLAP_RATIO`,
   `create_centerline`, `clip_centerline_to_caps`.

(Uma terceira falha, ja' resolvida e sem efeito na analise: a tentativa de
escrever ESTE handoff por heredoc estourou o limite de argumento do shell
(`ENAMETOOLONG: uv_spawn`); o arquivo foi escrito pela ferramenta de
escrita direta.)

---

## 8. O QUE JA FOI EFETIVAMENTE MEDIDO

### 8.1 As 91 aberturas - INPUT x HUMANO

**FATO MEDIDO.** O `reference.json` tem **94** aberturas, nao 91, e todas
com `confidence: "reconstructed"` / `openings_source: "reconstructed_from_blocks"`.
O dump bruto do documento REFERENCE
(`benchmark_dump_TORRE_..._20260831_111855.json`) tem `walls: []` e
`openings: []` - **o lado humano nao tem abertura nativa nenhuma**; toda
abertura do gabarito e' inferida dos vazios do layout de blocos por
`core/engine/opening_audit.detect_wall_openings_from_courses`.
Consequencia metodologica: "a posicao humana da abertura" e' na verdade
"onde os blocos do humano param".

**FATO MEDIDO.** As coordenadas de `reference.json` ja' estao no
referencial do INPUT (`source_document.frame_transform_applied`), entao
**nao foi refeito nenhum alinhamento global** - a transformacao registrada
(`translation_cm = [7678.7371, 1102.9024, 341.0]`, rotacao 0, escala 1) ja'
estava aplicada.

Casamento ESTRITO (mesma reta `|perp| <= 15 cm`, `|along| <= 60 cm`,
`|dw| <= 20 cm`, guloso pelo melhor score):

| | n |
|---|---|
| aberturas do INPUT | 91 |
| aberturas reconstruidas do HUMANO | 94 |
| **pares INPUT x HUMANO** | **75** |
| INPUT sem contraparte humana | 16 |
| HUMANO sem contraparte no INPUT | 19 |

### 8.2 Deslocamento INPUT x HUMANO (secoes 4, 5, 6, 7 do pedido)

**FATO MEDIDO - este e' o resultado central da sessao.**
Deslocamento AO LONGO da parede, nos 75 pares:

| faixa | n |
|---|---|
| 0 - 0,5 cm | **75 (100%)** |
| 0,5 - 1 cm | 0 |
| 1 - 2 cm | 0 |
| 2 - 5 cm | 0 |
| 5 - 10 cm | 0 |
| 10 - 20 cm | 0 |
| 20 - 50 cm | 0 |
| > 50 cm | 0 |

- media **0,0807 cm**; mediana **0,0047 cm**; P90 **0,2432 cm**; maximo **0,2442 cm**.
- perpendicular: media 0,2325; mediana 0,2432; **maximo 5,2408 cm** (um
  unico caso: `6558443` x `W060-O01`).
- **Residuo sistematico:** o vetor (dx, dy) e' praticamente constante em
  todos os 75 pares: **dx ~ 0,00 cm e dy = -0,243 cm**. Isso e' um offset
  global unico do lado da reconstrucao, nao movimento de abertura. **Piso
  de ruido adotado nesta analise: 0,5 cm.**
- **Largura:** `dw = 0` em 74 dos 75 pares; o unico desvio e' `6558460`
  com `dw = +0,11 cm`.
- **Peitoril:** `dsill = 0,0` em **75 de 75**. Nenhuma abertura teve
  peitoril alterado.
- **Verga (head):** `dhead` = -1,0 (43x), +9,0 (22x), -61,0 (8x), -6,0 (2x).
  **HIPOTESE (nao provada):** isso e' quantizacao da reconstrucao - o topo
  do vao reconstruido e' a ultima fiada com falha, e verga/canaleta
  fecham antes do topo real. Nao ha' evidencia de que o humano tenha
  mudado altura de vao.
- Classificacao de limites (secao 5 do pedido): **75 de 75 = `NO_CHANGE`**
  nos dois limites (o sufixo `+Z_CHANGE` vem so' do `dhead` acima).
  **Zero** `TRANSLATION`, **zero** `WIDTH_CHANGE`, **zero** `TYPE_CHANGE`.

### 8.3 82 atribuidas x 9 nao atribuidas (secao 6 do pedido)

**FATO MEDIDO.** Resposta direta a pergunta "as 9 problematicas tem maior
deslocamento humano?": **NAO.**

| grupo | n com par | media \|along\| | mediana | P90 | max |
|---|---|---|---|---|---|
| A. atribuidas pelo Wall Modeling | 68 | 0,0747 cm | 0,0047 | 0,2432 | 0,2442 |
| B. **NAO** atribuidas (das 9) | 7 | 0,1397 cm | 0,2408 | 0,2422 | 0,2422 |

Os dois grupos estao **inteiramente dentro do piso de ruido de 0,25 cm** -
duas ordens de grandeza abaixo da menor peca do catalogo (C04 = 4 cm).
As outras 2 das 9 (`6558406`, `6558407`, largura 321 cm) nao tem
contraparte humana e por isso nao entram na estatistica.

Detalhe das 9, uma a uma (**FATO MEDIDO**):

| abertura | par humano | larg. | along | perp | dw | dsill | dhead | classe |
|---|---|---|---|---|---|---|---|---|
| 6558406 | (sem) | 321,0 | - | - | - | - | - | sem contraparte |
| 6558407 | (sem) | 321,0 | - | - | - | - | - | sem contraparte |
| 6558411 | W072-O01 | 91,0 | +0,002 | -0,242 | 0,000 | 0,0 | -61,0 | NO_CHANGE |
| 6558426 | W036-O02 | 131,0 | -0,242 | -0,001 | 0,000 | 0,0 | +9,0 | NO_CHANGE |
| 6558433 | W012-O02 | 131,0 | +0,005 | -0,243 | 0,000 | 0,0 | +9,0 | NO_CHANGE |
| 6558458 | W038-O02 | 131,0 | -0,242 | -0,004 | 0,000 | 0,0 | +9,0 | NO_CHANGE |
| 6558461 | W073-O01 | 91,0 | -0,005 | -0,241 | 0,000 | 0,0 | -61,0 | NO_CHANGE |
| 6558475 | W057-O01 | 81,0 | -0,241 | -0,003 | 0,000 | 0,0 | +9,0 | NO_CHANGE |
| 6558476 | W057-O02 | 81,0 | -0,241 | -0,003 | 0,000 | 0,0 | +9,0 | NO_CHANGE |

### 8.4 As 16 aberturas do INPUT sem contraparte humana

**FATO MEDIDO.** Por largura: 8 de 321 cm, 4 de 31 cm, 4 de ~51 cm.
Todas tem eixo de parede do gabarito por baixo (distancia 0,00 a 0,24 cm) -
ou seja, **o humano construiu parede ali**; o que falta e' o VAO na
reconstrucao.

**FATO MEDIDO** (constantes lidas de `core/engine/opening_audit.py`):
`OPENING_GAP_MIN_CM = 50.0`, `OPENING_GAP_MAX_CM = 260.0`,
`OPENING_MIN_CONSEC_COURSES = 4`.

**HIPOTESE (coerente com os numeros, ainda nao provada bloco a bloco):**
as 16 sao limitacao do reconstrutor do gabarito, nao divergencia real -
as de 31 cm caem abaixo de `OPENING_GAP_MIN_CM`, as de 321 cm passam de
`OPENING_GAP_MAX_CM` (e viram *divisao de parede*, nao vao), e as de 51 cm
ficam no limite de `OPENING_MIN_CONSEC_COURSES`. **PENDENTE:** confirmar
olhando as fiadas reais do gabarito nesses trechos.

As 19 aberturas humanas sem par estao concentradas em W004, W005, W006,
W007 (todas com 1344 cm), W015/W017 (1379 cm) e W052 (2349 cm) - paredes
longas demais para o padrao do projeto. **HIPOTESE:** sao falsos positivos
do reconstrutor (vaos entre paredes distintas que a reconstrucao juntou
numa parede so'). **PENDENTE:** confirmar.

### 8.5 Bonecas (secoes 8 e 9 do pedido)

**FATO MEDIDO parcial.** `op_match2.py` ja' calcula e grava, para os 75
pares, `boneca_left_input`, `boneca_right_input`, `boneca_left_human`,
`boneca_right_human` (distancia da lateral do vao ate' o vizinho - outra
abertura da mesma parede ou a ponta da parede do gabarito). Os valores
estao em `nuvem/benchmark/diagnostics_2c/openings_strict.json`.

**Consequencia aritmetica direta e ja' garantida:** como `along` <= 0,25 cm
e `dw` = 0 em 74/75, `boneca_left_human - boneca_left_input` e
`boneca_right_human - boneca_right_input` sao necessariamente <= ~0,25 cm.
**Nao existe no projeto o caso "11 cm / 144 cm -> 10 cm / 145 cm"** que o
pedido queria detectar.

**PENDENTE:** a tabela formatada boneca a boneca (entrega F) e toda a
secao 9 (testar se a posicao humana permite B39/B34/B19/C09/C04, reduz
residuo, reduz compensadores) - **nao foi executada**. Observacao honesta:
com deslocamento humano medido em zero, a secao 9 perde o proposito
original (nao ha' movimento para explicar), mas ainda vale como
caracterizacao das bonecas que o humano recebeu prontas.

### 8.6 Fragmentacao das 167 walls (secao 13 do pedido)

**FATO MEDIDO.** Distribuicao de comprimento:

| faixa | 167 walls DEPOIS da extensao | 167 walls ANTES da extensao | 97 walls do GABARITO |
|---|---|---|---|
| < 20 cm | **22** (13,2%) | **31** (18,6%) | **0** |
| 20-50 cm | 9 (5,4%) | 0 | **0** |
| 50-100 cm | 29 (17,4%) | 39 | 13 (13,4%) |
| 100-200 cm | 38 (22,8%) | 34 | 19 (19,6%) |
| 200-400 cm | 42 (25,1%) | 36 | 31 (32,0%) |
| > 400 cm | 27 (16,2%) | 27 | 34 (35,1%) |
| **total** | 43.032,7 cm | 41.456,3 cm | 45.362,8 cm |

**O gabarito humano nao tem NENHUMA parede abaixo de 50 cm. O Wall
Modeling tem 31.**

Fragmentos na faixa 8-16 cm pedida: indices 136 (15,0), 144 (15,71),
146 (8,27), 147 (8,0), 148 (14,0), 149 (8,0), 150 (8,0), 152 (15,73),
166 (14,01).

Fragmentos de 4,45 cm: indices 159, 160, 161, 162, 163, 164, 165.
De 5,08 cm: 155, 156, 157, 158.

**FATO MEDIDO - descoberta importante:** para TODOS os 31 fragmentos
< 50 cm, a vizinha colinear mais proxima esta' a **700 cm ou mais**. Ou
seja: **esses fragmentos NAO sao pedacos de uma parede longa quebrada
pelo merge** - sao paredes espurias isoladas. Isso **afasta**
`merge_collinear_fragments` como causa da fragmentacao curta.

**FATO MEDIDO:** as walls 151, 152, 153, 154 tem angulo **3,8 / 183,8 /
176,2 graus** num projeto onde todo o resto e' 0/90/180/270 - e ficam
praticamente em cima das walls 144/145 (duplicatas que o `deduplicate_walls`
nao removeu porque o angulo difere).

### 8.7 Provenance CAD -> wall (secao 17 do pedido)

**FATO MEDIDO.** Reconstruido sem alterar assinatura do core: o laco de
`find_wall_pairs` foi replicado em `prov2.py`/`provenance.py` chamando
**as mesmas funcoes do motor**, so' que guardando qual par (i, j) de linhas
gerou cada parede. Resultado gravado em
`nuvem/benchmark/diagnostics_2c/provenance_walls.json` (167 entradas com
`line_i`, `line_j`, `overlap_ratio`, `dist_cm`).

Numeros do funil:

```
9258 linhas do layer 'Arquitetura'
  -> merge_collinear_fragments   -> 2868 linhas
  -> 589 pares candidatos validos
  -> 209 pares aceitos  |  380 candidatos descartados (ponta ja usada)
  -> deduplicate_walls  -42     -> 167 paredes
  -> 2450 linhas sobrando (unused_lines)
```

### 8.8 `merge_collinear_fragments` (secao 15 do pedido)

**FATO MEDIDO.** 9258 -> 2868 linhas. Nao produziu a fragmentacao curta
(ver 8.6). **FATO MEDIDO colateral:** o merge produz faces MAIS LONGAS que
a parede real - ex.: a face `y = -570` foi unida ate' `x = 2267,7`,
enquanto a parede humana correspondente (W012) termina em `x = 2070,5`.
**HIPOTESE:** isso nao impede o par (o overlap ratio e' normalizado pela
linha mais curta), mas contribui para o eixo cobrir mais que a parede.
**PENDENTE:** medir quantas faces ficaram mais longas que a parede real.

### 8.9 `find_wall_pairs` (secao 16 do pedido) - **o achado principal**

**FATO MEDIDO** (leitura do codigo, `wall_pairing.py:266-445`): o ranking
guloso e' `sort_key = (-overlap_ratio, dist)`, com
`overlap_ratio = overlap / min(len_i, len_j)` - **normalizado pela linha
MAIS CURTA** - e **cada linha e' usada em no maximo um par, sem rodada de
repescagem para as faces que ficaram orfas**.

**FATO MEDIDO** - composicao dos 209 pares aceitos:

| composicao do par | n |
|---|---|
| ambas as linhas >= 50 cm | 155 |
| **linha curta (< 20 cm) x linha longa (>= 100 cm)** | **30** |
| curta x curta (ambas < 20 cm) | 21 |
| 20-50 cm x qualquer | 3 |

**FATO MEDIDO** - distancia perpendicular REAL dos 209 pares aceitos
(a espessura gravada e' sempre 14,0, mas a distancia medida nao e'):

| dist. medida | n | dist. medida | n |
|---|---|---|---|
| 11,8 | 7 | 13,7 | 8 |
| 11,9 | 2 | **14,0** | **77** |
| 12,0 | 25 | 14,4 | 1 |
| 12,1 | 8 | 14,5 | 13 |
| 12,3 | 1 | 15,0 | 28 |
| 12,4 | 2 | 15,1 | 2 |
| 12,5 | 10 | 15,5 | 2 |
| 12,8 | 1 | 16,0 | 6 |
| 13,0 | 7 | 16,5 | 2 |
| 13,4 | 1 | | |
| 13,5 | 6 | | |

Ou seja: **so' 77 de 209 pares aceitos estao de fato a 14,0 cm.** Os
outros 132 entraram pela tolerancia de deteccao
(`compute_detection_tolerance_ft` devolveu **2,5 cm**, faixa aceita
11,5-16,5 cm).

**FATO MEDIDO** - **52 pares "verdadeiros" foram PERDIDOS**: pares com
distancia 14,00 +- 0,05 cm e `overlap_ratio >= 0,9` que nunca viraram
parede porque uma das duas faces ja' tinha sido consumida antes. Entre os
maiores perdidos:

```
d=13,999 r=1,0000 | 1681,21 cm (2267,7,-570,0)->(586,5,-570,0)  x  1456,00 cm (2056,5,-556,0)->(600,5,-556,0)
d=14,001 r=1,0000 | 1456,01 cm (-1864,5,760,0)->(-408,5,760,0)  x  1532,00 cm (-346,5,774,0)->(-1878,5,774,0)
d=14,001 r=1,0000 | 1456,01 cm (600,5,760,0)->(2056,5,760,0)    x  1922,22 cm (2267,7,774,0)->(345,5,774,0)
d=14,000 r=1,0000 |  844,00 cm x 830,01 cm   (4 ocorrencias, os 4 lados do miolo)
d=14,000 r=1,0000 |  496,00 cm (-1813,5,350,1)->(-1813,5,-145,9) x 524,00 cm (-1799,5,-159,9)->(-1799,5,364,1)
d=14,000 r=1,0000 |  496,00 cm (2005,5,-145,9)->(2005,5,350,1)   x 524,00 cm (1991,5,364,1)->(1991,5,-159,9)
d=14,000 r=1,0000 |  384,00 cm (-1878,5,350,1)->(-1494,5,350,1)  x 370,01 cm (-1494,5,364,1)->(-1864,5,364,1)
d=14,001 r=1,0000 |  290,00 cm (170,5,228,1)->(170,5,518,0)      x 338,00 cm (156,5,518,0)->(156,5,180,1)
... (52 no total)
```

### 8.10 Trace individual das 9 aberturas (secao 11 do pedido)

**FATO MEDIDO.** O trace foi ate' `find_wall_pairs` e ja' e' conclusivo
para as 9. As etapas seguintes (`deduplicate_walls`,
`extend_wall_ends_to_junctions`, `build_wall_graph`) nao criam parede
nova, entao o destino ja' estava selado ali.

| abertura | mecanismo medido |
|---|---|
| 6558406 / 6558407 / 6558433 | a face `y=-556,0` (1456 cm) foi consumida por um par com uma linha de **4,44 cm**, gerando a parede `w=41` de **4,45 cm** no eixo `y=-562,0`. O parceiro verdadeiro, `y=-570,0` (1681,21 cm, d=13,999, r=1,0000), ficou orfao. **A parede de ~1484 cm (gabarito W012) simplesmente NAO EXISTE nas 167.** |
| 6558426 | a face `x=-1799,5` (524 cm) foi consumida por um par com uma linha de **4,44 cm** (d=12,095), gerando a parede `w=36` de **4,45 cm** no eixo `x=-1805,53`. O parceiro verdadeiro `x=-1813,5` (496 cm, d=14,000, r=1,0000) ficou orfao. Gabarito W036 (524 cm) nao existe. |
| 6558458 | identico, espelhado: face `x=1991,5` (524 cm) roubada por linha de 4,44 cm (d=12,105) -> parede `w=43` de 4,45 cm no eixo `x=1997,57`; parceiro `x=2005,5` (496 cm) orfao. |
| 6558411 | a face `y=364,1` (370,01 cm) foi pareada com uma linha de **18,52 cm a 12,000 cm** de distancia -> parede `w=21` com eixo em **`y=370,05`**. O eixo verdadeiro e' `y=357,05`. A abertura fica a **12,76 cm** do eixo criado, acima do limite de 12,0 cm -> rejeitada. Face `y=350,1` (384 cm) orfa. |
| 6558461 | identico, espelhado (parede `w=20`, eixo `y=370,05`, abertura a 12,76 cm). |
| 6558475 / 6558476 | a face `x=156,5` (338 cm) foi pareada com uma linha de **94,0 cm** a ~12,0 cm -> parede `w=16` com eixo em **`x=150,52`**, quando o eixo verdadeiro e' `x=163,5`. As aberturas ficam a **12,99 cm** -> rejeitadas. Face `x=170,5` (290 cm, par verdadeiro d=14,001 r=1,0000) orfa. |

**FATO MEDIDO** sobre `unused_lines` (2450 no total):
`distancia_fora_das_espessuras_escolhidas` 1431, `sem_linha_paralela_com_sobreposicao`
852, `perdeu_rodada_para_outro_par` 167. **Atencao:** essa classificacao e'
enganosa - `_classify_unused_line` compara a linha contra os EIXOS ja'
formados, nao contra outras linhas. Por isso as faces roubadas aparecem
como "distancia fora das espessuras" com `esp_medida = 7,95` (que e' meia
espessura ate' um eixo), e nao como "perdeu rodada". **Nao usar essa
coluna como diagnostico sem ler este paragrafo.**

---

## 9. Hipoteses CONFIRMADAS nesta sessao

1. **[CONFIRMADA - FATO MEDIDO]** A FASE A e' reproduzivel headless bit a
   bit a partir de `input_real.json` (167 walls, 2450 unused, -42 dedup,
   mesmos diagnostics). O snapshot do repo e' confiavel como base.
2. **[CONFIRMADA - FATO MEDIDO]** As 9 aberturas nao atribuidas nascem em
   **`find_wall_pairs`**, nao em `merge_collinear_fragments`, nao em
   `assign_openings_to_walls`, e nao em movimento humano.
3. **[CONFIRMADA - FATO MEDIDO]** Existe roubo de face por fragmento
   curto: 30 dos 209 pares aceitos sao "curta < 20 cm x longa >= 100 cm",
   e 52 pares verdadeiros (14,00 cm, ratio >= 0,9) foram perdidos.
4. **[CONFIRMADA - FATO MEDIDO]** O gabarito humano nao tem parede abaixo
   de 50 cm; o Wall Modeling tem 31.
5. **[CONFIRMADA - FATO MEDIDO]** Os fragmentos curtos nao sao pedacos de
   parede quebrada (vizinha colinear mais proxima a >= 700 cm).

## 10. Hipoteses REJEITADAS nesta sessao

1. **[REJEITADA - FATO MEDIDO]** *"O projetista humano moveu portas/janelas
   ao longo da parede para a modulacao fechar."*
   Em 75 de 75 pares o deslocamento longitudinal e' <= **0,2442 cm**, com
   residuo sistematico constante de dy = -0,243 cm. O peitoril e' identico
   em 75/75 (`dsill = 0,0`) e a largura e' identica em 74/75. **Nao ha'
   uma unica abertura deslocada, alargada ou estreitada pelo humano neste
   projeto.** A hipotese prioritaria do pedido esta' refutada com dado.
2. **[REJEITADA - FATO MEDIDO]** *"As 9 problematicas tem deslocamento
   humano maior que as 82."* Ambos os grupos estao dentro do piso de ruido
   (0,0747 cm x 0,1397 cm de media, ambos < 0,25 cm).
3. **[REJEITADA - FATO MEDIDO]** *"A fragmentacao curta vem de
   `merge_collinear_fragments` falhando em religar colineares."* Nenhum
   fragmento < 50 cm tem vizinha colinear a menos de 700 cm.
4. **[REJEITADA por consequencia aritmetica]** *"O humano ajustou boneca
   (11/144 -> 10/145) para fechar."* Com `along <= 0,25 cm` e `dw = 0`, a
   diferenca de boneca e' forcosamente <= ~0,25 cm.

## 11. Hipoteses AINDA NAO TESTADAS (PENDENTE)

1. **[PENDENTE]** Que os 132 pares aceitos fora de 14,0 cm (tolerancia de
   deteccao 2,5 cm) produzam paredes com eixo errado em outros lugares
   alem dos 4 casos ja' rastreados. Nao foi feita varredura sistematica
   "eixo criado x eixo do gabarito".
2. **[PENDENTE]** Quantas das 97 paredes do gabarito **nao tem nenhuma
   parede correspondente** nas 167 (paredes faltantes). O
   `scope_summary.json` ja' registra `reference_only_inside_scope: 13`,
   mas nao foi cruzado com os 52 pares perdidos.
3. **[PENDENTE]** A origem exata de cada fragmento curto: quais linhas de
   CAD (4,44 / 5,08 / 8,0 cm) sao - porta, hachura, mobiliario, testa? O
   `provenance_walls.json` ja' tem `line_i`/`line_j` de todos os 167, so'
   falta ler e classificar.
4. **[PENDENTE]** Secao 10 do pedido (lateral da abertura x blocos
   humanos: bloco adjacente, junta vertical mais proxima, distancia,
   celula/furo, amarracao proxima). **Nao foi iniciada.** Observacao: com
   deslocamento humano = 0, essa secao vira caracterizacao, nao
   descoberta de regra de movimento.
5. **[PENDENTE]** Secao 14 (cenario A x cenario B da opening) -
   **prejudicada**: sem movimento humano, nao existe cenario B distinto.
   Precisa ser reformulada na proxima sessao.
6. **[PENDENTE]** Confirmar as 3 hipoteses do reconstrutor do gabarito
   (16 aberturas sem par, 19 aberturas fantasma, `dhead` quantizado)
   olhando as fiadas reais.
7. **[PENDENTE]** Efeito do `clip_centerline_to_caps` (`cap_clipped_count = 11`)
   e dos `offset_suspect_count = 6` - nao investigados.
8. **[PENDENTE]** Por que `deduplicate_walls` nao removeu as walls
   151-154 (angulos 3,8 / 176,2 / 183,8 graus sobre as walls 144/145).

---

## 12. Resultados intermediarios importantes, com numeros

Numeros do estado conhecido, todos re-conferidos nesta sessao:

- `scope_summary.json`: 167 walls do solver, 152 no escopo, 15 fora
  (926,5 cm), 97 walls de gabarito, `matched_inside_scope = 84`,
  `solver_only_inside_scope = 68`, `reference_only_inside_scope = 13`.
- `unassigned_openings_audit.json`: 91 aberturas, 82 atribuidas, 9 nao,
  `opening_assoc_tolerance_cm = 5,0`, `min_segment_length_cm = 1,0`,
  `max_perp_allowed_cm = 12,0` (= 14/2 + 5).
- `baseline_real_v1`: full `success_rate 0,0659`, 1671 criticos, 4986
  findings nivel 1, 167 walls, 10657 blocos; scoped `0,0592`, 1584
  criticos, 4782 findings, 152 walls, 10237 blocos.
- FASE A re-executada: `merge 9258 -> 2868` (12,3 s),
  `find_wall_pairs -> 209 / 2450` (8,1 s), `dedup -42 -> 167`,
  `detection_tolerance = 2,5 cm`, `parallel_pairs = 1.332.676`,
  `offset_suspect_count = 6`, `offset_suspect_max = 0,0782 ft`,
  `cap_clipped_count = 11`.
- 589 pares candidatos validos / 209 aceitos / 380 descartados.
- 2450 unused_lines somam **71.180,3 cm** de linha nao aproveitada.
- Entre as linhas longas (> 200 cm) que sobraram: 57 no total, sendo as
  maiores 1922,2 / 1681,2 / 1532,0 / 1513,2 / 1304,0 cm.

---

## 13. Scripts e artefatos temporarios criados

Scratchpad da sessao (some quando a sessao for limpa - **ja' foram
copiados para o repo**):
`C:\Users\CIVIX\AppData\Local\Temp\claude\...\scratchpad\diag2c\`

Copiados para `nuvem/benchmark/diagnostics_2c/` (**NAO commitados** -
ficam para revisao da proxima sessao):

| arquivo | o que e' |
|---|---|
| `op_match.py` | 1o casamento INPUT x HUMANO (janela 400 cm) |
| `op_match2.py` | casamento ESTRITO + along/perp + limites + bonecas |
| `frag.py` | distribuicao de comprimento e vizinhas colineares |
| `trace_stage.py` | re-executa a FASE A e grava estados intermediarios |
| `trace9.py` | trace geometrico das 9 aberturas |
| `unused.py` | 2450 unused_lines por motivo |
| `provenance.py` | provenance CAD -> wall (par (i,j) de cada parede) |
| `prov2.py` | quantificacao do roubo de face + pares verdadeiros perdidos |
| `openings_match.json` | saida do casamento largo (91 linhas) |
| `openings_strict.json` | **saida do casamento estrito - inclui as bonecas** |
| `provenance_walls.json` | 167 paredes com `line_i`/`line_j`/`overlap_ratio`/`dist_cm` |

Ficaram **so' no scratchpad** (nao copiados, sao grandes e regeneraveis
por `trace_stage.py` em ~25 s): `stage_raw_lines.json`,
`stage_merged_lines.json`, `stage_unused_lines.json`, `stage_pairs.json`,
`stage_dedup.json`, `stage_extended.json`, `stage_pairing_diag.json`.
Tambem ficaram so' no scratchpad `inspect1.py` (o que falhou),
`inspect2.py`, `inspect3.py` - a saida deles esta' transcrita aqui.

Dumps brutos do Revit ainda presentes em
`C:\Users\CIVIX\AppData\Local\Temp\6e9fa79d-e629-4af1-9c3d-3fac6b806f23\`
(**uteis, nao apagar**): `benchmark_dump_TORRE_..._20260831_111855.json`
(nivel 04. TGD), `..._20260831_100502.json` (nivel 05. TP1),
`input_real_dump_TESTE_..._20260831_112427.json`,
`catalog_dump_TESTE_..._20260831_113932.json`, `cad_TESTE_T01LIMPA_cm.json`,
`cad_TORRE_T01LIMPA_cm.json`.

## 14. Arquivos MODIFICADOS nesta sessao

**Nenhum arquivo existente foi modificado.** Zero edicao em
`nuvem/core/**`, no solver, no Wall Modeling, em tolerancias,
compensadores, prisma, amarracoes ou catalogo.

Arquivos NOVOS criados por esta sessao:

- `nuvem/benchmark/HANDOFF_ETAPA_2C.md` (este arquivo) - **unico a ser
  commitado**;
- `nuvem/benchmark/diagnostics_2c/` (11 arquivos, listados em 13) -
  **deixados intactos e NAO commitados**, para revisao.

`.agents/` ja' estava sem rastreio antes desta sessao e nao foi tocado.

## 15. `git status` no momento do checkpoint

```
?? .agents/
?? nuvem/benchmark/diagnostics_2c/
```

HEAD local = `origin/main` = `7dea3562b0c878f8aefd7831fd143e87ac031733`
(ver secao 2 sobre a mudanca de HEAD durante a sessao).

## 16. Ponto EXATO onde a investigacao foi interrompida

A sessao parou **imediatamente apos** a execucao de
`diagnostics_2c/prov2.py`, cuja saida completa esta' transcrita nas secoes
8.7 e 8.9 (composicao dos 209 pares aceitos, os 30 casos de roubo de face,
os 52 pares verdadeiros perdidos, e o histograma de distancia real dos
pares aceitos).

O que estava sendo feito no instante da parada: **agrupar as causas raiz
(secao 18 do pedido) a partir desses numeros**. Nada disso chegou a ser
escrito como conclusao - e, por ordem explicita do usuario, **nao deve ser
inventado agora**. As causas raiz estao SUGERIDAS pelos dados das secoes
8.6/8.9/8.10, mas **nao foram formalizadas, nem contadas caso a caso, nem
cruzadas com a cadeia causal (secao 19 do pedido)**.

## 17. Proxima acao recomendada (para nao repetir trabalho)

1. Ler este handoff inteiro e **nao refazer** nada das secoes 8.1-8.10.
2. Reaproveitar direto os artefatos ja' prontos em
   `nuvem/benchmark/diagnostics_2c/`: `openings_strict.json` (aberturas +
   bonecas) e `provenance_walls.json` (par de linhas de cada parede).
   Regenerar os `stage_*.json` com
   `py -3 nuvem/benchmark/diagnostics_2c/trace_stage.py` (~25 s) so' se
   precisar.
3. **Primeira analise que falta e' barata e fecha o diagnostico:** cruzar
   as 97 paredes do gabarito com as 167 do Wall Modeling e com os 52
   pares perdidos, para responder "quantas paredes do gabarito o Wall
   Modeling deixou de criar, e quantas dessas o roubo de face explica".
   Isso da' as entregas K, L, M, N e P de uma vez.
4. So' depois formalizar as causas raiz (secao 18 do pedido), a cadeia
   causal (19), os casos minimos (21) e os riscos (22-S).
5. **Continuar sem corrigir nada.** A Etapa 2C termina em diagnostico.

## 18. O que ainda falta para completar o relatorio A-S

| entrega | estado |
|---|---|
| A. distribuicao de movimento das 91 openings | **PRONTA** (8.2) |
| B. 82 atribuidas x 9 nao atribuidas | **PRONTA** (8.3) |
| C. openings realmente deslocadas pelo humano | **PRONTA** - resposta: **nenhuma** (8.2, 10.1) |
| D. magnitude e direcao | **PRONTA** (8.2: along/perp, residuo dy = -0,243) |
| E. mudancas de largura/altura/peitoril | **PRONTA** (8.2) |
| F. bonecas INPUT x HUMANO | **PARCIAL** - calculadas e gravadas, tabela final PENDENTE (8.5) |
| G. bonecas x modulos de blocos | **PENDENTE** (secao 9 do pedido, nao iniciada) |
| H. lateral da abertura x juntas/blocos humanos | **PENDENTE** (secao 10 do pedido, nao iniciada) |
| I. trace das 9 openings | **PRONTA** (8.10) |
| J. reclassificacao das 9 | **PARCIAL** - a evidencia esta' toda em 8.10, mas os rotulos finais **nao foram atribuidos** e nao devem ser inventados agora |
| K. distribuicao das 167 walls | **PRONTA** (8.6) |
| L. origem dos fragmentos curtos | **PARCIAL** - provado que nao sao merge (8.6); falta identificar as linhas de CAD de origem uma a uma |
| M. fragmentos explicados por openings | **PENDENTE** |
| N. causas raiz agrupadas | **PENDENTE** (era o que estava sendo feito na hora da parada) |
| O. cadeia causal | **PENDENTE** |
| P. primeira causa raiz a tratar | **PENDENTE** |
| Q. funcoes/arquivos envolvidos | **PARCIAL** - ja' localizados: `core/engine/wall_pairing.py::find_wall_pairs` (266-445), `_classify_unused_line` em `benchmark/wall_modeling_bridge.py`, constantes em `core/engine/tolerances.py` e `core/engine/opening_audit.py` |
| R. casos minimos de regressao | **PENDENTE** |
| S. riscos de uma futura correcao | **PENDENTE** |

---

## Avisos para quem continuar

- **Nao preservar o rotulo `WALL_MODELING_ERROR` por heranca** - mas
  tambem nao trocar por outro sem escrever a evidencia junto.
- **Nao usar a coluna `reason` de `unused_lines` como diagnostico** sem
  ler o aviso no fim de 8.10.
- **Nao confundir os dois fingerprints** (secoes 3 e 4).
- **Nao investigar o solver de blocos** nesta etapa.
- A conclusao mais forte ja' medida - e a que muda o plano das proximas
  etapas - e' que **a geometria entregue ao solver esta' errada antes do
  solver**: parede de 1484 cm que nao existe, parede de 524 cm que virou
  toco de 4,45 cm, e eixos 13 cm fora do lugar. Enquanto isso nao for
  resolvido, medir prisma e compensador mede ruido.
