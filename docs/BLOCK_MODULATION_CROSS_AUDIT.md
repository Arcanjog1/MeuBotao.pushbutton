# CROSS AUDIT — CR-BLOCK-01

> Auditoria cruzada e independente do `CR-BLOCK-01` (CONTA 1, prisma/
> fiadas/amarração vertical), feita pela CONTA 2 usando o MESMO
> laboratório headless já usado para auditar a `main`. Nenhum código de
> produção foi alterado; nenhuma das duas branches originais
> (`claude/block-01-prisma-fiadas-rik42t`, `claude/block-audit-baseline-
> 350nav`) foi tocada. Todos os números foram **recalculados**, nunca
> copiados do relato da CONTA 1.

## Baselines comparados

```
MAIN:         9f3bab41b35f0e2a5f9782583ead8e1ee7755f49
CR-BLOCK-01:  claude/block-01-prisma-fiadas-rik42t @ 3e6d937116466198c79d51b85928788766657a41
CONTA 2:      claude/block-audit-baseline-350nav   @ 22132b3bb57678c99cc10e477518202231b13538
Esta branch:  claude/block-01-cross-audit = checkout(CR-BLOCK-01) + merge(CONTA 2), sem conflito
```

`git diff origin/claude/block-01-prisma-fiadas-rik42t...HEAD --name-only`
mostra só os artefatos read-only da CONTA 2 (`docs/BLOCK_MODULATION_
AUDIT.md`, `nuvem/benchmark/RELATORIO_BASELINE_BLOCOS.md`,
`nuvem/benchmark/diagnostics_block_audit/**`) — confirmado antes de
qualquer censo.

Mudança de produção do CR-BLOCK-01, medida diretamente
(`git diff MAIN...CR-BLOCK-01 -- nuvem/core`): **um único arquivo**,
`nuvem/core/engine/wall_stepper.py` (+303 linhas) — adiciona
`_pier_full_search_layout` (busca exata por programação dinâmica sobre
todas as composições de um trecho de preenchimento, ativada só quando a
busca gulosa antiga ainda deixa a regra #1 e/ou #2 violada) e chama essa
busca como uma tentativa adicional dentro de `_pier_layout_avoiding_
joints`. Nenhuma outra regra, tolerância ou constante geométrica foi
tocada. `tests/test_block_bonding.py` é suíte nova (460 linhas). `tests/
test_script.py`, `nuvem/core/{geometry,wall_pairing,tolerances,
continuous_modulation,modulation_math,opening_audit}.py` e
`nuvem/core/wall_modeling.py` **não foram tocados**.

## Metodologias — CONTA 1 vs CONTA 2

| | CONTA 1 (`diagnostics_block_prisma/`) | CONTA 2 (`diagnostics_block_audit/`) |
|---|---|---|
| Unidade de junta | classifica em `FORBIDDEN_JOINT_ALIGNMENT` / `DOCUMENTED_EXCEPTION` / `UNCLASSIFIED_RULE_CONFLICT` / `NO_ALIGNMENT`, com banda de abertura como eixo (mesma banda × entre bandas) | classifica em `suspect_continuous_vertical_joint` / `exempt_opening_touch_11_8` / `RULE_AMBIGUOUS` / não-coincidente, sem distinguir banda (ver nota abaixo) |
| Escopo de projeto | 3 projetos, 275 paredes agregadas | mesmos 3 projetos; detalhe por projeto (`torre_easy_lo_r00_tgd`) + agregado de 275 paredes (**adicionado nesta fase 2** especificamente para comparar) |
| Determinismo | não reportado nesta rodada da CONTA 1 | 8 execuções (ordem invertida, endpoints invertidos, 5 shuffles com seed fixa), fingerprint por peça chaveado pela geometria da parede |
| Fonte de dados | mesmo solver real (`solve_building_blocks_all_courses`) | idem — a MESMA função de produção, via `solver_bridge` |

**As duas metodologias medem o MESMO fenômeno com definições diferentes.**
Isso já era esperado (a missão pediu explicitamente para não usar os
números da CONTA 1 como verdade) — a seção "Concordâncias" abaixo mostra
que, apesar da definição diferente, várias métricas BRUTAS (não
classificadas) batem exatamente entre as duas.

## Prisma independente

Recontagem própria (`suspect_continuous_vertical_joint`, tolerância
1,0cm, mesma definição do baseline da fase 1), MAIN × CR-BLOCK-01:

| | MAIN | CR-BLOCK-01 | Δ | Δ% |
|---|---|---|---|---|
| pares de fiadas medidos (`tgd`) | 7.444 | 7.434 | −10 | −0,1% |
| **suspeitas de junta contínua (`tgd`)** | **1.086** | **827** | **−259** | **−23,8%** |
| suspeitas de junta contínua (agregado, 275 paredes) | 2.936 | 2.539 | −397 | −13,5% |
| paredes com ≥1 suspeita (`tgd`) | 47 | 46 | −1 | −2,1% |
| stagger médio (`tgd`) | 21,53cm | 22,18cm | +0,65cm | +3,0% |
| stagger mediano (`tgd`) | 15,0cm | 15,0cm | 0 | 0% |

Distribuição de stagger (`tgd`, cm):

| faixa | MAIN | CR-BLOCK-01 | Δ |
|---|---|---|---|
| 0–1 (essencialmente coincidente) | 1.253 | 978 | **−275** |
| 1–3 | 12 | 14 | +2 |
| 3–10 | 1.385 | 1.253 | −132 |
| 10–20 | 3.660 | 4.048 | +388 |
| >20 | 1.134 | 1.141 | +7 |

**Redução real e substancial confirmada de forma independente**: a
melhoria não é um artefato da classificação própria da CONTA 1 — medida
com tolerância/definição diferentes, o mesmo efeito aparece (−23,8% no
projeto principal, −13,5% no agregado de 275 paredes). A massa que sai da
faixa "quase coincidente" (0–1cm, −275) migra majoritariamente para a
faixa "bem separada" (10–20cm, +388), exatamente o comportamento
esperado de uma busca que agora acha composições genuinamente
desencontradas em vez de variações triviais do mesmo layout.

**Divergência de magnitude com a CONTA 1** (−92,1% dela contra −23,8%/
−13,5% aqui): explicada por definição, não por erro. A CONTA 1 mede
`FORBIDDEN_JOINT_ALIGNMENT` só dentro da MESMA banda de abertura (a parte
que o CR realmente ataca) e separa explicitamente as coincidências ENTRE
bandas (que ficam de fora do escopo dela, "182→33" na terminologia dela).
A CONTA 2 não faz essa separação por banda no censo original da fase 1 —
mistura os dois casos. Ou seja, **os dois censos concordam em direção e
em ordem de grandeza real do efeito; a CONTA 1 isolou melhor a fração do
problema que o CR de fato ataca.**

## C09/C04

Recontagem própria de sequências de 2+ compensadores consecutivos
(mesma definição da fase 1 — sem distinguir aqui "puro preenchimento" vs
"tocando nó", que era um refinamento só da fase 1):

| | MAIN | CR-BLOCK-01 | Δ | Δ% |
|---|---|---|---|---|
| C09 total (`tgd`) | 1.185 | 1.171 | −14 | −1,2% |
| C09 sequências 2+ (`tgd`) | 201 | 180 | **−21** | **−10,4%** |
| C09 sequências 2+ (agregado) | 890 | 866 | −24 | −2,7% |
| C04 total (`tgd`) | 584 | 570 | −14 | −2,4% |
| C04 sequências 2+ (`tgd`) | 17 | 13 | **−4** | **−23,5%** |
| C04 sequências 2+ (agregado) | 46 | 42 | −4 | −8,7% |
| C09 faixas verticais (`tgd`) | 25 | 26 | +1 | +4,0% |
| C04 faixas verticais (`tgd`) | 13 | 13 | 0 | 0% |

**Classificação: MELHOROU** (efeito colateral confirmado, direção
consistente em ambos os códigos e nas duas granularidades — projeto
principal e agregado). Não é dramático (não era esperado ser — este CR
não mira compensadores) e não chega perto de zerar a violação, que
continua sendo uma classe de defeito real e não resolvida (ver
`docs/BLOCK_MODULATION_AUDIT.md`, achado P0-1). A mission pediu
explicitamente para não exigir zeragem aqui — não exigida.

## B19

Total (`tgd`): 840 → 853 (+13, +1,5%). Localização por BORDA do bloco
(não centro — refinamento desta fase 2, ver `b19_location_breakdown.py`),
limiar de 5cm:

| | MAIN | CR-BLOCK-01 | Δ |
|---|---|---|---|
| perto de abertura | 197 | 215 | +18 |
| perto de ponta de parede | 118 | 118 | 0 |
| **meio de parede de verdade (>5cm de qualquer borda)** | **525** | **520** | **−5** |
| clusters de alinhamento vertical (2+ fiadas) | 119 | 123 | +4 |

**Classificação: NEUTRA.** B19 não é alvo declarado do CR-BLOCK-01 (o CR
mexe em `_pier_layout_avoiding_joints`/busca de composição, não na regra
do meio-bloco em si), e a medição confirma isso: variação pequena em
ambas as direções, sem padrão consistente de piora ou melhora. O achado
de fundo já registrado na fase 1 (525/853, 61,6%, de B19 genuinamente
longe de qualquer borda — candidato a violação da regra "nunca no meio de
trecho") **continua praticamente do mesmo tamanho** depois do CR — nem
resolvido, nem agravado.

## L/T/X

Recontagem própria (`solve_l_corner`/`solve_t_intersection`/
`solve_x_intersection` + `validate_*`, `tgd`):

| | MAIN | CR-BLOCK-01 | Δ |
|---|---|---|---|
| L_CORNER total / TRUE / falhas únicas | 63 / 62 / 1 | 63 / 62 / 1 | **0 em tudo** |
| T_INTERSECTION total / TRUE / DEGRADED / falhas únicas | 118 / 80 / 23 / 15 | 118 / 80 / 23 / 15 | **0 em tudo** |
| X_INTERSECTION total / TRUE / falhas únicas | 17 / 8 / 9 | 17 / 8 / 9 | **0 em tudo** |

**Confirmado, byte a byte, de forma independente: L/T/X são
IDÊNTICOS entre MAIN e CR-BLOCK-01.** O CR não tocou (e não deveria ter
tocado) `solve_l_corner`/`solve_t_intersection`/`solve_x_intersection` —
confirma tanto a alegação da CONTA 1 ("falhas L/T/X 200→200 inalterado")
quanto o requisito explícito da missão desta fase ("CR-BLOCK-01 NÃO
deveria corrigir X... esperado: problema continua, mas não piora").
**X continua falhando em 9/17 nós (52,9%)** — sem piora, sem melhora,
exatamente como esperado.

## Aberturas

| | MAIN | CR-BLOCK-01 | Δ |
|---|---|---|---|
| bloco DENTRO do vão, extent real (`tgd`) | 5 | 5 | 0 |
| bloco PARCIAL no vão, extent real (`tgd`) | 108 | 108 | 0 |
| `jamb_exceptions` (`tgd`) | 172 | 172 | 0 |
| `alignment_conflicts` (`tgd`) | 30 | **0** | **−30 (−100%)** |
| `alignment_conflicts` (agregado) | 64 | **0** | **−100%** |

`alignment_conflicts` zerar é a confirmação mais direta e mais forte de
todo o CR: é literalmente a lista de "trechos que a regra #1 reprovou e
não foi possível corrigir automaticamente" — cair a zero, nas duas
granularidades, é evidência independente robusta de que a busca completa
resolve exatamente o que se propôs a resolver, sem introduzir NENHUM
novo caso de bloco dentro/parcial de vão (0 e 0 de diferença nos dois).

## Door void

`door_void_violations`: **290 → 290 (`tgd`), 638 → 638 (agregado,
275 paredes) — idêntico nos dois lados, nas duas granularidades.**

Confirma a alegação da CONTA 1. Mais importante: **é uma checagem
cruzada forte de que os dois benchmarks (o da CONTA 1 e o desta CONTA 2,
escritos independentemente, por pessoas/sessões diferentes) estão
medindo exatamente o mesmo fenômeno sobre a mesma execução real do
solver** — a probabilidade de dois códigos totalmente independentes
baterem em 638 por coincidência, sem estarem de fato lendo a mesma
estrutura de dados do mesmo jeito, é desprezível.

## Paredes moduladas

| | MAIN | CR-BLOCK-01 | Δ |
|---|---|---|---|
| paredes moduladas (agregado, 275) | 246 | 246 | 0 |
| paredes NÃO moduladas (agregado) | 29 | 29 | 0 |
| paredes NÃO moduladas (`tgd`) | 29 | 29 | 0 |
| ranking de causa (`tgd`) | `L_T_X_FAILURE`=13, `LENGTH_ARITHMETIC`=9, `OPENING`=7 | idêntico | 0 em cada causa |

**Zero regressão de cobertura, em qualquer granularidade.** Confirma
"paredes com blocos 246/275 → 246/275 (inalterado)" da CONTA 1.

## Non modular +3

Investigado a fundo (`out_non_modular_plus3_detail.json`). O agregado
**3.333 → 3.336 bate exatamente** com o relato da CONTA 1, e **o delta
inteiro vem de um único projeto** (`torre_easy_lo_r00_tp1`; `tgd` e
`piloto_sintetico_2x2` não mudam nada, 0 de diferença nos dois).

Os 3 eventos, identificados por diff exato de `non_modular` chaveado por
(parede, fiada, variante, segmento, posição):

- **Removido**: parede 70, Fiada B, segmento [270cm, 370cm] (100cm) — 3
  ocorrências no bruto (fiadas físicas repetindo a mesma banda). **Este
  segmento passou a fechar** depois do CR.
- **Adicionados**: parede 71, Fiada B, [14cm, 114cm] (100cm) — 3
  ocorrências; parede 39, Fiada B, [14cm, 114cm] (100cm) — 3 ocorrências.
  **Estes dois segmentos passaram a NÃO fechar.**

Todas as três entradas (a removida e as duas novas) carregam o MESMO
padrão degenerado nos campos de diagnóstico
(`lower_valid_cm=0, upper_valid_cm=0, delta_to_lower_cm=0,
delta_to_upper_cm=0`) nos dois lados do código — não é uma condição nova
introduzida pelo CR, é uma condição de contorno pré-existente em
`nearest_block_lengths_cm`/`pier_closes_with_blocks_cm`
(`core/engine/modulation_math.py`, não tocado pelo CR) para um
comprimento remanescente específico (~100cm), que simplesmente mudou de
endereço (de uma parede para duas outras) porque o layout ao redor mudou.

**Impacto em cobertura: ZERO** — `walls_not_modulated` continua 29/29
nas duas versões; as paredes 39/70/71 continuam recebendo blocos no
resto da própria extensão, isto é um resíduo de SEGMENTO parcial, não
perda de parede inteira.

**Classificação: NEUTRO** (não "melhoria colateral" no sentido literal —
duas paredes novas passam a ter um problema que só uma tinha antes, não é
pura redistribuição sem custo — mas também não é regressão: severidade
desprezível, zero impacto em cobertura, causa-raiz pré-existente e fora
do arquivo que o CR tocou). A caracterização da CONTA 1 ("redistribuição
sem perda de paredes") está **factualmente correta na parte que importa
(zero perda de parede)**, mas a frase "redistribuição" esconde que 2
paredes novas passaram a ter o defeito — vale registrar com mais
precisão no PROJECT_STATUS quando/se este CR for revisitado.

## Determinismo global

8 execuções (baseline, invertida, endpoints invertidos, 5 shuffles
seed 1/2/3/10/42), mesmo fingerprint canônico por peça (geometria da
parede, não índice), projeto principal:

| | MAIN | CR-BLOCK-01 |
|---|---|---|
| fingerprints distintos (8 execuções) | **8** | **8** |
| amplitude de peças entre as 8 execuções | 130 | 130 |
| peças por execução | 10.657/10.611/10.635/10.626/10.695/10.706/10.579/10.576 | 10.647/10.601/10.612/10.616/10.685/10.696/10.569/10.566 |

**Determinação: NEUTRA — nem melhora, nem piora.** Mesmo número de
fingerprints distintos (8/8) e mesma amplitude de variação de peças
(130 nos dois). Todo run individual do CR-BLOCK-01 tem cerca de 10-23
peças a menos que o run correspondente da MAIN (mesma ordem de entrada),
consistente com a busca completa às vezes achar uma composição
ligeiramente mais compacta (menos peças) para o mesmo trecho — mas isso é
um efeito de MAGNITUDE, não de SENSIBILIDADE À ORDEM. Confirmado por
inspeção direta: na maioria das permutações testadas, a primeira camada
onde a MAIN e o CR-BLOCK-01 já divergem entre si é a mesma que diverge
internamente em cada um sob permutação — o **grafo de nós**
(`build_wall_graph`/`extend_wall_ends_to_junctions`), que o CR-BLOCK-01
não tocou. **Não há evidência de que o CR piorou o não-determinismo
existente**, que continua sendo um problema real e não-atribuído a este
CR (ver `docs/BLOCK_MODULATION_AUDIT.md`, achado P0-2).

## Teste trim → shift

Investigado por reprodução direta da fixture do teste
(`_one_opening_axis_fixture(162, 80, 158)`) nos dois checkouts, sem
alterar `tests/test_script.py`. Ver `out_trim_vs_shift_investigation.json`
para o dump completo dos dois planos.

**Achado central: a posição FINAL da abertura é idêntica nos dois
planos** (`t_lo`/`t_hi` batem exatamente). A única diferença é a TÉCNICA:
MAIN encurta o eixo em 1cm (`trim`, tier 3 da seção 7 das REGRAS);
CR-BLOCK-01 preserva o comprimento do eixo inteiro e só desloca a
abertura (`shift`, tier 2). **`shift` é estritamente menos invasivo que
`trim` na própria ordem de prioridade já documentada**
(`REGRAS_MODULACAO_BLOCOS.md` seção 7: boneca → shift → trim → widen,
"a MENOR alteração possível primeiro", "nunca aumenta o comprimento total
de um eixo").

Checagem contra o censo agregado (não só este 1 caso sintético): 0
regressão em cobertura (246/275→246/275), 0 regressão em `door_void`
(638→638), MELHORIA em colisões (1083→1048), 0 mudança nas falhas L/T/X.
Nenhuma regra obrigatória violada pelo resultado `shift`.

**Determinação: (A) TESTE DESATUALIZADO.** A asserção antiga
(`plan["tier"] == "trim"`) codificava uma limitação da busca ANTIGA
(que não achava uma composição válida para o tier `shift`, mais barato),
não uma regra de negócio. Não existe em `REGRAS_MODULACAO_BLOCOS.md`
nenhuma exigência de que `trim` deva vencer `shift` quando os dois
fecham — pelo contrário, a ordem documentada prefere `shift`. O resultado
novo é **estritamente melhor ou equivalente** ao antigo: mesma posição
final de abertura, sem custo de comprimento de parede.

## Regressões

Nenhuma regressão confirmada nas métricas medidas nesta auditoria:

| Métrica | Regressão? |
|---|---|
| Cobertura de paredes (moduladas/não moduladas) | Não (0/0) |
| L/T/X (falhas, válidos) | Não (0/0/0) |
| `door_void_violations` | Não (0/0) |
| Bloco dentro/parcial de vão | Não (0/0) |
| Colisões | Não — MELHOROU (−3,2%) |
| Compensadores em sequência | Não — MELHOROU (−10,4%/−23,5% no projeto principal) |
| Determinismo | Não — NEUTRO (mesma amplitude, mesmo nº de fingerprints) |
| `non_modular` | Achado NEUTRO de severidade desprezível (+3 em 3.336, sem perda de cobertura) |
| B19 (uso indevido) | Não — NEUTRO (variação pequena, sem padrão) |
| `alignment_conflicts` | Não — MELHOROU (−100%) |
| Prisma (junta contínua) | Não — MELHOROU (−23,8% no projeto principal, −13,5% agregado) |

## Performance

Solver de blocos, projeto principal: **2,104s → 2,211s (+5,1%)** —
praticamente idêntico ao +5,3% que a CONTA 1 reportou (medido em cenário
de 3 projetos agregados; aqui medido só no projeto principal, mesma
ordem de grandeza). Dentro do custo esperado de uma busca por programação
dinâmica que só ativa quando ainda há violação (`430/5.122` chamadas,
8,4%, segundo a CONTA 1 — não recontado por esta auditoria, mas
consistente com o overhead medido de ~5%).

## Concordâncias entre as duas contas

Confirmadas por recálculo 100% independente (não aceitas por citação):

- `door_void_violations`: 638 → 638 (idêntico, ambas as contas).
- Cobertura: 246/275 paredes moduladas, inalterado (ambas).
- `alignment_conflicts`: cai a 0 (ambas — a CONTA 1 media 64→0, a CONTA 2
  recalculou 64→0 de forma totalmente independente).
- Colisões: melhoram, mesma ordem de grandeza (CONTA 1: 1083→1048, −3,2%;
  CONTA 2: recalculado 1083→1048, **exatamente os mesmos números**).
- L/T/X: falhas inalteradas (ambas: 200→200 entradas brutas; CONTA 2
  também confirma 0 mudança nos NÓS ÚNICOS de cada tipo).
- Prisma melhora substancialmente na direção certa (CONTA 1: −92,1% na
  métrica dela; CONTA 2: −23,8%/−13,5% na métrica própria — direção e
  ordem de grandeza reais concordam, magnitude difere por definição).
- Compensadores melhoram como efeito colateral (CONTA 1: −9,8% agregado;
  CONTA 2: C09 −2,7%/C04 −8,7% agregado — mesma direção, magnitude
  próxima).
- Performance: +5,3% (CONTA 1) vs +5,1% (CONTA 2, projeto principal) —
  praticamente idêntico.
- `non_modular` +3: exatamente o mesmo número (3.333→3.336) nas duas
  contas, e a CONTA 2 localizou os 3 eventos exatos.
- `UNCLASSIFIED_RULE_CONFLICT`: a CONTA 1 mediu 1.518→1.506 (Δ=−12); o
  proxy independente da CONTA 2 (coincidências tocando peça de nó L/T/X)
  mediu 1.642→1.630 (Δ=**−12**, exatamente igual, embora a base absoluta
  seja diferente por definição de categoria) — forte evidência de que as
  duas contas estão de fato vendo o mesmo fenômeno de fundo (o conflito
  estrutural entre regra #1 e a repetição de peça de nó), mesmo com
  taxonomias diferentes.

## Divergências entre as duas contas

- **Magnitude da melhoria de prisma**: CONTA 1 reporta −92,1%
  (`FORBIDDEN_JOINT_ALIGNMENT` total) e −100% dentro da mesma banda; a
  CONTA 2 mede −23,8%/−13,5% com uma definição que NÃO separa banda. Não
  é contradição — é granularidade diferente da mesma melhoria real (ver
  seção "Prisma independente" acima). Recomendação: se a CONTA 1
  reabrir este CR, valeria a pena o próximo censo da CONTA 2 também
  separar por banda, para os dois relatórios ficarem diretamente
  comparáveis.
- **Taxonomia de conflito**: `UNCLASSIFIED_RULE_CONFLICT` é uma categoria
  própria da ferramenta da CONTA 1, sem equivalente 1:1 na CONTA 2 — o
  proxy construído aqui (`node_conflict_breakdown.py`) aproxima bem (Δ
  idêntico), mas os valores absolutos não devem ser tratados como o
  mesmo número.
- **B19**: não reportado pela CONTA 1 (fora do escopo dela); a CONTA 2
  mede e classifica como NEUTRO — sem divergência real, só cobertura
  desigual.

## Problemas fora do escopo confirmados

- **X_INTERSECTION continua falhando em 52,9% dos nós** (9/17) — CR
  não deveria corrigir, e não corrigiu. Confirmado idêntico.
- **Coincidências tocando peça de nó (~64% do resíduo de prisma)** —
  estrutural, exige decisão de regra (qual vale quando #1 e a repetição
  de nó conflitam), não uma busca melhor. Fora do escopo de
  `_pier_layout_avoiding_joints`.
- **Bandas de abertura fragmentam a busca entre fiadas de bandas
  diferentes** — já registrado pela CONTA 1 (REGRAS 27.7) como
  pendência de `core/wall_modeling.py`, fora da área de escrita
  autorizada para este CR.
- **Bloco dentro/parcial de vão (5+108 no projeto principal)** e
  **`door_void_violations` (638 agregado)** — pré-existentes, não
  tocados por este CR, já documentados como P1 na auditoria da fase 1.

## Veredito final

**APROVADO COM CORREÇÃO DE TESTE.**

Fundamentação, item por item do critério da missão:

1. **O resultado `shift` é semanticamente correto** — confirmado por
   reprodução direta: mesma posição final de abertura que o `trim`
   antigo, plano aceito só depois de o solver de blocos real confirmar
   fechamento (mesmo mecanismo de verificação de sempre).
2. **Não viola regra** — confirmado pelo censo agregado de 275 paredes:
   zero regressão em cobertura, L/T/X, `door_void`, bloco-em-vão;
   `alignment_conflicts` cai a zero.
3. **É melhor ou equivalente ao antigo `trim`** — é melhor: preserva o
   comprimento do eixo (`length_delta_cm=0` contra `-1,0cm`), e a própria
   ordem de prioridade documentada (seção 7 das REGRAS) coloca `shift`
   ANTES de `trim`.
4. **A falha é apenas expectativa stale** — confirmado: a asserção
   antiga não corresponde a nenhuma regra de negócio documentada: era
   uma consequência acidental da limitação de busca que este CR corrigiu
   de propósito.

Nenhuma regressão foi encontrada em nenhuma das métricas medidas
independentemente (prisma melhora, compensadores melhoram, colisões
melhoram, `alignment_conflicts` zera; cobertura, L/T/X, `door_void` e
bloco-em-vão ficam idênticos; determinismo fica neutro; o único achado
"novo" — `non_modular` +3 — tem severidade desprezível, causa-raiz
pré-existente e zero impacto em cobertura).

**Ação recomendada para devolver à CONTA 1 (não aplicada aqui):**
atualizar `tests/test_script.py::test_pipeline_lanca_blocos_e_ajusta_na_
mesma_passada` — trocar `assert plan["tier"] == "trim"` por
`assert plan["tier"] == "shift"`, e atualizar o docstring do teste (que
hoje descreve só o comportamento antigo) para registrar que o plano
aceito pode ser `shift` OU `trim`, dependendo de qual tier mais barato a
busca de blocos consegue fechar sem violar a regra #1.

**Pendências que continuam em aberto, não bloqueiam este CR:**
`non_modular` +3 (severidade desprezível, documentado); bandas de
abertura fragmentando a busca entre fiadas (já registrado pela CONTA 1,
REGRAS 27.7); coincidências tocando peça de nó (~64% do resíduo,
conflito estrutural entre regras, precisa de decisão, não de busca
melhor); X_INTERSECTION com 52,9% de falha (fora do escopo deste CR).

---

**CROSS-AUDIT CONCLUÍDA.**
**NENHUM CÓDIGO DE PRODUÇÃO ALTERADO.**
**PARADO ANTES DO MERGE.**
**AGUARDANDO DECISÃO SOBRE CR-BLOCK-01.**
