# AUDITORIA INDEPENDENTE — MODULAÇÃO DE BLOCOS (CONTA 2)

> Auditor independente + laboratório de benchmark, rodando em PARALELO ao
> `CR-BLOCK-01` (CONTA 1, sobre prisma/fiadas). Este documento audita
> **exclusivamente a `main` original**, sem ler a branch da CONTA 1.
> Nenhuma correção foi implementada — **só medição e classificação**.
>
> **Baseline auditada:** `main` @
> `9f3bab41b35f0e2a5f9782583ead8e1ee7755f49`.
> **Branch desta auditoria:** `claude/block-audit-baseline-350nav`.
> **Laboratório reproduzível:**
> `nuvem/benchmark/diagnostics_block_audit/` (ver o `README.md` de lá para
> como rodar de novo).
> **Projeto de censo:** `torre_easy_lo_r00_tgd` (o único com `input.json`
> **medido** via MCP, não reconstruído do próprio gabarito — ver
> `nuvem/benchmark/README.md`), com `torre_easy_lo_r00_tp1` e
> `piloto_sintetico_2x2` como comparação de escala.

## Sumário executivo

O motor de **paredes** (`core/engine/{geometry,wall_pairing}.py`) está
estabilizado e determinístico (CR-2F-E/A/D, já mergeados). O motor de
**blocos** (`core/wall_modeling.py` + `core/engine/{wall_stepper,
continuous_modulation,modulation_math,opening_audit}.py`) nunca passou
pelo mesmo tratamento de determinismo, e este censo confirma isso com
dados: **o solver de blocos NÃO é determinístico sob permutação da ordem
de entrada das paredes** (ver seção "Determinismo"). Fora isso, a
infraestrutura de benchmark já existente (`nuvem/benchmark/`) já mede,
desde 2026-08-31, que o solver diverge muito do projeto humano aprovado em
duas classes específicas — compensadores consecutivos/excesso e junta
corrida (prisma) — e este censo **confirma essas duas classes de forma
totalmente independente**, com métrica e código próprios, chegando à
mesma ordem de grandeza.

Três achados novos desta auditoria, não documentados antes:

1. **`PIER_LAYOUT_VARIANTS_PER_COURSE` (K) já é 1 em produção, não 3** — a
   seção 11.7 do `REGRAS_MODULACAO_BLOCOS.md` descreve K=3 como a
   constante "escolhida" com uma prova por força bruta; a seção 18.4 (mais
   recente, 2026-08-28) já registra que o usuário revogou essa decisão de
   volta para K=1, com o conflito **já anotado no próprio documento**. Não
   é uma descoberta desta auditoria que os documentos escondiam — é uma
   confirmação de que o conflito documentado é real no código hoje, e que
   a análise de qualquer achado de "faixa vertical repetitiva" precisa
   levar isso em conta.
2. **O solver de blocos não é determinístico sob permutação de entrada**
   (nunca medido antes — o CR-2F-D mediu só a camada de baixo, a formação
   das paredes). A primeira camada onde a divergência aparece, na maior
   parte dos casos testados, é o **grafo de nós** (`build_wall_graph`/
   `extend_wall_ends_to_junctions`), ANTES do solver de blocos rodar —
   ver seção "Determinismo".
3. **`find_door_void_violations` pegou 290 candidatos** (em 41 das 167
   paredes, 24,6%) que invadem o vão real de uma porta sem peitoril —
   a regra absoluta da seção 3 das REGRAS funciona como rede de segurança
   REATIVA (barra a criação daquelas paredes), mas a geração do layout não
   respeita a zona de exclusão **por construção** nesses casos.

## Como reproduzir todos os números deste documento

```bash
cd nuvem/benchmark/diagnostics_block_audit
python3 run_full_census.py
```

Escreve `out_full_census.json` (consolidado) e um `out_<censo>.json` por
censo. Sem MCP, sem Revit — 100% headless, ~40s.

---

## 1. Mapa completo do pipeline

Fronteira clara entre **motor puro** (nunca importa `Autodesk.Revit.DB`
fora dos tipos injetados por `tests/revit_stubs.py`/o Revit real) e
**integração Revit** (abre `Transaction`, cria `FamilyInstance`/`Wall`):
tudo em `core/engine/**` é motor puro; em `core/wall_modeling.py`, as
funções `solve_*`/`audit_*`/`evaluate_*`/`classify_*` são puras (só
recebem `nodes`/`walls_to_create`/`catalog`/`candidates`), e a fronteira
começa exatamente em `create_building_blocks`/`create_wall_opening_cuts`/
`_execute_create` (abrem `Transaction`) e nas classes de UI (`_SetupForm`,
`_PostCreationForm`, os `IExternalEventHandler`).

```
PAREDES (CAD/linhas)
  │  core/wall_modeling.py: extract_lines_by_layer, get_or_create_wall_type
  │  core/engine/geometry.py: merge_collinear_fragments, create_centerline
  │  core/engine/wall_pairing.py: find_wall_pairs, deduplicate_walls
  ▼
GRAFO (nós de encontro)
  │  core/wall_modeling.py: extend_wall_ends_to_junctions
  │  core/engine/wall_stepper.py: build_wall_graph (via *)
  ▼
CLASSIFICAÇÃO L / T / X / FREE_END / STRAIGHT_CONTINUATION / AMBIGUOUS
  │  build_wall_graph classifica pelo NÚMERO DE BRAÇOS por ponta, não por
  │  contagem de paredes (bug real já corrigido — REGRAS seção 24.6)
  ▼
BLOCOS DE AMARRAÇÃO (L/T/X)
  │  core/engine/wall_stepper.py: solve_l_corner, solve_t_intersection,
  │  solve_x_intersection, solve_all_intersections (orquestra os 3)
  │  validação: validate_l_corner, validate_t_intersection,
  │  validate_x_intersection
  ▼
ABERTURAS (associação parede↔porta/janela)
  │  core/wall_modeling.py: collect_opening_instances,
  │  classify_unassociated_opening_reason
  ▼
FIADA (bandas verticais por conjunto de abertura ativo)
  │  core/wall_modeling.py: _group_course_indices_by_opening_band,
  │  _opening_active_in_course_band, _course_z_band
  ▼
JAMB  (modo split_first, LEGADO — ver nota abaixo)
  │  core/engine/wall_stepper.py: solve_opening_jamb,
  │  _jamb_build_course_variants
  ▼
TRECHO LIVRE (preenchimento comum de um segmento entre 2 fronteiras)
  │  core/engine/wall_stepper.py: _pier_ordered_layout,
  │  _pier_layout_avoiding_joints, _continuous_segment_layout
  │  core/engine/modulation_math.py: pack_pier_with_blocks,
  │  nearest_block_lengths_cm, pier_closes_with_blocks_cm
  ▼
LAYOUT (monta um eixo inteiro — modo padrão continuous_first)
  │  core/engine/wall_stepper.py: solve_wall_free_fill
  │  core/engine/continuous_modulation.py: classify_extent_against_openings,
  │  split_extents_by_openings, opening_repair_regions,
  │  region_solid_subsegments
  ▼
COMPENSADORES (C09/C04, tier 6-7 do preenchimento)
  │  core/engine/wall_stepper.py: dentro de _pier_ordered_layout/
  │  _merge_adjacent_compensator_pairs; orientação:
  │  core/wall_modeling.py: orient_compensator_candidates
  ▼
REPARO DE ABERTURA (continuous_first: derruba peça inteira, nunca corta)
  │  core/engine/wall_stepper.py: _recut_openings_and_repair,
  │  _solve_repair_subsegments
  ▼
VALIDAÇÃO
  │  core/engine/wall_stepper.py: validate_wall_modulation,
  │  collisions_between, validate_same_course_collision,
  │  find_door_void_violations
  │  core/wall_modeling.py: audit_wall_bond_quality,
  │  audit_all_walls_bond_quality (2ª rede de segurança, olha a PAREDE
  │  INTEIRA depois de tudo já resolvido)
  ▼
CANDIDATOS FINAIS
  │  core/wall_modeling.py: solve_building_blocks,
  │  solve_building_blocks_all_courses (orquestra por banda de fiadas;
  │  devolve course_candidates = o que SERIA de fato materializado)
  ▼
MATERIALIZAÇÃO REVIT  ── FRONTEIRA MOTOR PURO → INTEGRAÇÃO REVIT ──
     core/wall_modeling.py: create_building_blocks (Transaction),
     create_wall_opening_cuts (Transaction, DEPOIS dos blocos — seção
     23.5b das REGRAS), build_report_issues/build_final_modulation_report
```

**Nota — dois modos de abertura coexistem no código.** `OPENING_STRATEGY_
CONTINUOUS_FIRST` é o padrão de produção desde 2026-08-28 (seção 23 das
REGRAS): a parede inteira é modulada primeiro, as aberturas são recortadas
depois, e `solve_opening_jamb` **não roda mais** nesse modo
(`jamb_exceptions` sai vazio). `OPENING_STRATEGY_SPLIT_FIRST` (o pipeline
"JAMB" do diagrama acima) continua no código só para comparação lado a
lado — não é mais o caminho principal. Este censo mede o comportamento
REAL de produção (`continuous_first`); mesmo assim, `jamb_exceptions`
apareceu com 172 entradas no censo (ver seção Aberturas) — a investigar
se é degradação para `split_first` (seção 23.5 das REGRAS, "único caminho
de volta") ou resíduo de outro caminho de código.

| Etapa | Arquivo | Entrada | Saída | Responsabilidade |
|---|---|---|---|---|
| Extração CAD | `wall_modeling.py::extract_lines_by_layer` | geometria bruta do CAD (Revit) | linhas por layer | filtra `ShortCurveTolerance`, agrupa por layer |
| Merge/pareamento | `geometry.py::merge_collinear_fragments`, `wall_pairing.py::find_wall_pairs`, `deduplicate_walls` | linhas do CAD | `walls_to_create` | forma eixos de parede a partir de pares de face — **fora do escopo desta auditoria** (motor de paredes, CR-2F-*) |
| Grafo | `wall_modeling.py::extend_wall_ends_to_junctions`, `wall_stepper.py::build_wall_graph` (via geometry) | `walls_to_create` | `nodes`, `end_to_node` | classifica L/T/X/FREE_END/STRAIGHT_CONTINUATION/AMBIGUOUS |
| Amarração L/T/X | `wall_stepper.py::solve_l_corner/t_intersection/x_intersection` | `nodes`, `catalog`, `openings_per_wall` | candidatos de nó | decide B34/B54/degradação/falha por nó |
| Aberturas | `wall_modeling.py::collect_opening_instances` | portas/janelas (Revit ou dict) | `openings_per_wall` | associa abertura à parede |
| Bandas de fiada | `wall_modeling.py::_group_course_indices_by_opening_band` | `openings_per_wall`, altura | grupos de `course_index` | agrupa fiadas por conjunto de vão ativo |
| Trecho livre/layout | `wall_stepper.py::solve_wall_free_fill`, `_pier_ordered_layout`, `_continuous_segment_layout` | geometria do eixo + nós + aberturas | candidatos de preenchimento | prioridade B39→B19→B34→compensador (seção 2 das REGRAS) |
| Reparo de abertura | `wall_stepper.py::_recut_openings_and_repair` | candidatos + `openings_per_wall` | candidatos ajustados + `non_modular` | derruba peça inteira, nunca corta (seção 23.2) |
| Validação | `wall_stepper.py::validate_wall_modulation`, `find_door_void_violations`; `wall_modeling.py::audit_wall_bond_quality` | candidatos | `alignment_conflicts`, `door_void_violations`, reprovações | 2 redes de segurança independentes |
| Candidatos finais | `wall_modeling.py::solve_building_blocks_all_courses` | tudo acima | `course_candidates` | o que É de fato materializado, por fiada física |
| Materialização | `wall_modeling.py::create_building_blocks` | `course_candidates` | `FamilyInstance` no Revit | única etapa que abre `Transaction` |

---

## 2. Catálogo de blocos

Família única "14x19", 6 peças (`BLOCK_FAMILY_CATALOG_DEFINITIONS`,
identificação por família+tipo exatos, nunca por comprimento deduzido —
`REGRAS_MODULACAO_BLOCOS.md` seção 1):

| Código | Comprimento | Papel documentado | L | T | X | Abertura | Meio de parede | Extremidade | Transição entre fiadas |
|---|---|---|---|---|---|---|---|---|---|
| **B39** | 39cm | **REGRA OBRIGATÓRIA** — peça padrão, sempre 1ª prioridade | não usado | não usado | não usado | preenchimento comum até a jamba | sim, dominante | sim | sem regra própria |
| **B34** | 34cm | **REGRA OBRIGATÓRIA** em L/T-degradado (célula menor sempre encostada no nó); **PREFERENCIAL** como filler tier-3 | sempre (2×B34) | degradado (nível 2) | não usado | jamb legado (modo split_first) | sim (tier 3, `pode cair em qualquer posição`) | via nó | **PADRÃO OBSERVADO AINDA NÃO CONFIRMADO** — alinhamento de vão entre fiadas garantido só em L/T-degradado (seção 5/6); no meio de parede, "convenção fixa, não otimizada" (limitação documentada) |
| **B54** | 54cm | **REGRA OBRIGATÓRIA** em T-verdadeiro/X (célula central alinhada) | não usado | nível 1 (T verdadeiro) | sempre (2×B54) | não | **nunca observado** neste censo (0 ocorrência `MID_WALL_FILL`) | via nó | garantido e validado (`validate_t_intersection`/`validate_x_intersection`) |
| **B19** | 19cm | **REGRA OBRIGATÓRIA** — último recurso, só em ponta ABERTA (nunca meio, nunca nó de amarração mesmo degradado) | não (nó nunca usa B19) | não | não | jamb/reparo, ponta aberta | **PROIBIÇÃO INCONDICIONAL** (seção 2) — mas ver achado abaixo | sim, único uso legítimo | sem regra própria (isento da regra #1 quando encostado em vão, seção 11.8) |
| **C09** | 9cm | **PREFERENCIAL** — compensador, último recurso, nunca 2+ em sequência | não | boneca nível-3 (único elemento) | não | frequente (seção 25.3, 31,7% dos encostes) | sim, tier 6-7 | sim, encostado em vão | isento da regra #1 quando encostado em vão (11.8) |
| **C04** | 4cm | mesma regra do C09 (pastilha) | não | boneca nível-3 (único elemento) | não | frequente (seção 25.3) | sim | sim | isento da regra #1 quando encostado em vão (11.8) |

**Catálogo real vs catálogo do solver** — o projeto humano usa **33
tipos** (canaleta, canaleta J, verga, contraverga, vedação, variantes
CORTADO); o solver conhece só os 6 acima. Escopo pendente, não erro (seção
24.5 das REGRAS) — `solver_supported_catalog` filtra e descarta o resto
(`notes.catalog_codes_dropped`, vazio nesta rodada porque `input.json`
já vem filtrado para os 6 do solver).

### Achado do censo sobre o catálogo (não estava nas REGRAS)

O censo mediu, para o projeto principal (`torre_easy_lo_r00_tgd`, 10.657
peças materializadas):

| Código | Total | `NODE_TRUE` | `NODE_DEGRADED` | `MID_WALL_FILL` |
|---|---|---|---|---|
| B39 | (não censado por código — é o preenchimento base, sem exceção) | — | — | — |
| B34 | 2530 | 1423 (56,2%) | 443 (17,5%) | 664 (26,2%) |
| B54 | 636 | 636 (100%) | 0 | 0 |
| B19 | 840 | 0 | 0 | 840 (100%, sempre `STANDARD_FILL`) |
| C09 | 1185 | 0 | 287 (24,2%, boneca nível-3) | 898 (75,8%) |
| C04 | 584 | 0 | 152 (26,0%) | 432 (74,0%) |

- **B54 nunca aparece fora de nó** — confirma, com dado real (não
  sintético), a afirmação da seção 23.6 das REGRAS de que peça de
  amarração deixou de ser usada como enchimento depois do `continuous_
  first` (medido lá em cenário sintético; aqui é o mesmo padrão num
  projeto real de 167 paredes).
- **B19 — 100 das 840 ocorrências (11,9%) ficam a mais de 60cm de
  qualquer borda de abertura ou ponta de parede** (`mid_wall_far_from_
  edge_count`). A regra diz que B19 só pode encostar numa ponta ABERTA
  — não necessariamente que precisa estar a menos de 60cm dela (esse raio
  é o mesmo `BOND_STRIP_OPENING_INFLUENCE_CM` usado para isentar faixa
  repetitiva, reaproveitado aqui só como sinalizador de distância, não
  como prova de violação). **Marcado como achado a investigar, não como
  violação confirmada** — precisa de uma segunda medição (a peça está de
  fato ENCOSTADA em alguma ponta aberta, mesmo que ela seja longe de
  QUALQUER OUTRA abertura da parede?) antes de virar item do backlog
  P0/P1. Ver `run_special_block_census.py` para os 100 casos brutos.

---

## 3. Prisma / fiadas (censo independente)

Método: para cada parede, cada par de fiadas físicas consecutivas
(mesma banda de abertura), junta = ponto médio entre peças vizinhas
paralelas ao eixo; junta da fiada N é "coincidente" com a fiada N+1 se a
mais próxima está a ≤1,0cm.

| Métrica | Valor |
|---|---|
| Pares de fiadas consecutivas medidos | 7.444 |
| Juntas coincidentes suspeitas (`CONTINUOUS_VERTICAL_JOINT`) | **1.086** |
| Isentas por encoste em abertura (seção 11.8) | 10 |
| Ambíguas (perto da borda, encoste não confirmado) — `RULE_AMBIGUOUS` | 157 |
| Não-coincidentes | 6.191 |
| Paredes com ≥1 junta suspeita | 47 / 167 (28,1%) |
| Stagger mediano | 15,0cm |
| Stagger médio | 21,5cm |

Comparação com o validador oficial já existente
(`nuvem/benchmark/validators/validate_prism.py`, medição de 2026-08-31,
seção 24.2 das REGRAS): `PRISM_CONTINUOUS_JOINT` = 961 no solver (medido
sobre o mesmo tipo de projeto, metodologia diferente — o validador oficial
usa peça inteira/faixa, este censo usa junto ponto-médio). As duas
medições **independentes** (código, tolerância e definição diferentes)
concordam em ordem de grandeza (961 vs 1.086) — evidência cruzada de que
o problema de prisma é real e não um artefato de um validador específico.

**Alternativas não escolhidas (item 22 da missão, medição parcial):** a
produção roda com `variants_per_course=1` (seção 18.4 das REGRAS — ver
Sumário executivo), então o agregado `candidates` desta rodada não carrega
variantes alternativas para comparar. Rodar o mesmo censo com
`variants_per_course=3` é possível (`run_solver(..., variants_per_course=3)`
já suportado pela biblioteca do laboratório) mas fica registrado como
**PENDÊNCIA DESTE CENSO**, não executado por prioridade de tempo.

---

## 4. Compensadores C09

| Métrica | Valor |
|---|---|
| Total | 1.185 |
| Sequências de 2+ consecutivos | **201** |
| Sequências de 3+ consecutivos | 71 |
| — das quais só de preenchimento comum (`MID_WALL_FILL` puro) | **183** |
| — das quais tocam uma peça de nó (adjacência legítima) | 18 |
| Faixas verticais (≥3 fiadas físicas na mesma posição X) | 25 |
| Distância até abertura/ponta (mediana) | 19,5cm |
| Uso "longe" de abertura/extremidade (>60cm, preenchimento comum) | 147 / 1.185 |

**183 sequências de 2+ C09 consecutivos, só de preenchimento comum, é
violação direta e inequívoca** da regra "proibido usar 2 ou mais em
sequência" (`REGRAS_MODULACAO_BLOCOS.md` seção 2) — não é ambíguo, não
depende de exceção de abertura, é o padrão de USO PLAUSÍVEL DE AJUSTE
(seção 25.3 das REGRAS confirma que compensador encostado em abertura é
legítimo) contra **FAIXA REPETITIVA SUSPEITA** (183 sequências que não
são isso). Compatível em ordem de grandeza com `COMPENSATOR_CONSECUTIVE`
já documentado (497 no validador oficial da mesma classe de projeto —
seção 24.2 das REGRAS, 1567 vs 52 do humano).

---

## 5. Pastilhas C04

| Métrica | Valor |
|---|---|
| Total | 584 |
| Sequências de 2+ consecutivos | 17 |
| — só de preenchimento comum | 11 |
| — tocando peça de nó | 6 |
| Faixas verticais | 13 |
| Distância até abertura/ponta (mediana) | 12,0cm |
| Uso "longe" (>60cm) | 8 / 584 |

C04 é usado majoritariamente perto de abertura/extremidade (mediana
12cm, só 8 casos >60cm) — muito mais disciplinado que C09 na prática
medida, apesar de ter a mesma regra formal. Repetição horizontal (11
sequências puras) é bem menor que a de C09 (183), proporcionalmente à
contagem total também (584 vs 1.185) — mas ainda assim uma violação
real onde ocorre.

---

## 6. Meio bloco B19

| Métrica | Valor |
|---|---|
| Total | 840 |
| `reason_bucket` | 100% `MID_WALL_FILL` (nunca peça de nó — confirma a regra) |
| Sequências de 2+ consecutivos | 40 (todas `MID_WALL_FILL` — ver nota abaixo) |
| Faixas verticais | 4 |
| Distância até abertura/ponta (mediana) | 24,5cm |
| >60cm de qualquer borda | **100 / 840 (11,9%)** |

**Nota sobre "sequências de 2+"**: um "B19 seguido de B19" na mesma
sequência espacial **não é**, por si, uma violação da regra do meio-bloco
— a regra proíbe B19 **no meio de um trecho**, não proíbe dois B19
adjacentes quando ambos estão perto de bordas do MESMO trecho curto (ex.:
um trecho fechado nas duas pontas por aberturas, cada ponta recebendo seu
próprio B19). Este censo não distingue os dois casos automaticamente —
os 40 casos brutos estão em `run_special_block_census.py::run_examples_ge2`
para inspeção manual antes de qualquer CR.

O achado mais forte aqui continua sendo os **100 casos >60cm de qualquer
borda** (seção 2 acima) — candidato a investigação prioritária, porque a
regra do meio-bloco é rotulada como **incondicional** nas REGRAS.

---

## 7. B34 (amarração especial + preenchimento comum)

| Métrica | Valor |
|---|---|
| Total | 2.530 |
| `NODE_TRUE` (L_CORNER/T_INTERSECTION_MAIN/INCOMING/X — X não usa B34) | 1.423 (56,2%) |
| `NODE_DEGRADED` (T degradado para L, boneca nível-3 não usa B34) | 443 (17,5%) |
| `MID_WALL_FILL` (tier 3 do preenchimento comum) | 664 (26,2%) |
| Sequências de 2+ consecutivos (todas) | 424 |
| — só de preenchimento comum | **40** |
| — tocando peça de nó (adjacência legítima nó+filler) | 384 |
| Faixas verticais | 21 |

A maior parte das "sequências" de B34 (384/424) é adjacência legítima
entre a peça de nó e um B34 de preenchimento vizinho — **não** é o
problema que `MAX_SPECIAL_BOND_PER_TRECHO=1` (seção 23.4 das REGRAS) foi
criado para evitar. Os **40 casos de sequência PURA de preenchimento
comum** (sem nenhuma peça de nó no meio) são o subconjunto que de fato
contraria essa regra — muito menor que os 424 brutos, mas real. Sem essa
distinção (que este censo faz e o validador oficial pode ou não fazer —
não verificado aqui), qualquer contagem bruta de "B34 repetido" superestima
o problema em ~10×.

Alinhamento do vão menor entre fiadas: garantido e testado em L/T-degradado
(`validate_l_corner`, ver seção 8 abaixo); **não garantido** no B34 de
meio de parede (limitação já documentada, seção 6 das REGRAS — este censo
não mede alinhamento de célula fora de nó, ficaria como pendência de
próxima rodada).

---

## 8. B54 (T verdadeiro + X)

| Métrica | Valor |
|---|---|
| Total | 636 |
| `NODE_TRUE` | 636 (100%) |
| `MID_WALL_FILL` | **0** |
| Sequências de 2+ consecutivos | 115 (100% tocando nó) |
| Sequências de 3+ | 49 |
| Faixas verticais | 0 |

B54 nunca aparece como preenchimento comum — confirma a regra do
catálogo com dado real. As "sequências" de B54 são inteiramente
adjacências legítimas de nó (mesma peça repetindo em fiadas físicas
consecutivas da mesma paridade, por construção — seção 11.5 das REGRAS,
isento de propósito). Nenhum achado de violação aqui.

---

## 9. Encontros L

`solve_l_corner` / `validate_l_corner`, usados também como objeto de
estudo direto (chamados pela auditoria numa amostra, além da leitura do
resultado real):

| Métrica | Valor |
|---|---|
| Total de nós L_CORNER | 63 |
| Classificados `TRUE` (B34 nos dois lados) | 62 (98,4%) |
| Classificados `DEGRADED` | 0 |
| Sem candidato nenhum | 1 |
| Nós únicos com falha reportada (`intersection_failures`) | 1 |

L_CORNER é, de longe, o encontro mais bem resolvido: 62/63 fecham com a
solução TRUE documentada, e a amostra re-validada diretamente com
`validate_l_corner` confirma `ok: True` sem problema nos casos
verificados. O 1 caso sem candidato está registrado em
`out_intersection_census.json::L_CORNER.failures_sample` para
reprodução.

---

## 10. Encontros T

| Métrica | Valor |
|---|---|
| Total de nós T_INTERSECTION | 118 |
| `TRUE` (nível 1, B54+B34) | 80 (67,8%) |
| `DEGRADED` (nível 2, vira L com 2×B34) | 23 (19,5%) |
| Sem candidato (nível 3 não gerou/nível 4 sem solução) | 15 (12,7%) |
| Nós únicos com falha reportada | 15 |
| Entradas em `intersection_failures` (não únicas — por tentativa/banda) | 120 |

**Achado de metodologia, não de bug**: `validate_t_intersection` reprova
100% dos nós `DEGRADED` quando aplicada ingenuamente (ela exige o par
B54+B34 do T verdadeiro) — não é o validador certo para esse caso.
`validate_l_corner` é a prova geométrica correta para um T degradado
(mesma lógica de amarração de um L, ver seção 5 das REGRAS), e ao usá-la
a validação **passa** nos casos degradados amostrados. Corrigido neste
censo (`_resolve_and_validate_sample` escolhe o validador certo por
`degraded`); registrado aqui porque é exatamente o tipo de armadilha que
um auditor descuidado cairia — "reprovar cegamente" um nó correto porque
usou o validador errado.

---

## 11. Encontros X

| Métrica | Valor |
|---|---|
| Total de nós X_INTERSECTION | 17 |
| `TRUE` (2×B54) | 8 (47,1%) |
| `DEGRADED` | 0 (X não degrada — solve_x_intersection não tem esse caminho) |
| Sem candidato | 9 (52,9%) |
| Nós únicos com falha | 9 |

**Taxa de falha mais alta dos três tipos de nó (52,9%)** — quase metade
dos cruzamentos não recebe solução alguma. Como X não tem degradação (ao
contrário de T), quando o espaço não cabe para 2×B54 o nó vai direto para
`intersection_failures`, sem fallback. Candidato forte a P1/P2 do backlog
— ver seção de priorização.

---

## 12. Aberturas

| Métrica | Valor |
|---|---|
| Total (input) | 82 |
| Porta sem peitoril (`sill ≤ 1cm`) | 57 (69,5%) |
| Janela (`sill > 1cm`) | 25 (30,5%) |
| Largura mediana | 91,0cm |
| `non_modular` (segmentos que não fecharam em blocos) | 3.023, em 124 paredes distintas |
| `alignment_conflicts` (residual da regra #1) | 30 |
| `jamb_exceptions` | 172 (ver nota sobre `continuous_first` na seção 1) |
| `door_void_violations` (candidato dentro do vão de porta sem peitoril) | **290**, em 41 paredes distintas (24,6%) |

`jamb_exceptions=172` no modo `continuous_first` é inesperado à luz da
documentação ("`solve_opening_jamb` não é mais chamado no modo contínuo" —
seção 23.2) — **investigar antes do CR seguinte**: ou é resíduo do
mecanismo de degradação para `split_first` (seção 23.5, "único caminho de
volta", quando o eixo inteiro não fecha), e nesse caso é esperado, ou é
um caminho de código não coberto pela documentação atual. Registrado como
achado, não resolvido aqui.

**290 `door_void_violations`** é a rede de segurança REATIVA da seção 3
das REGRAS funcionando — bloqueia a criação das paredes envolvidas — mas
significa que a geração do layout, nesses 41 casos, não respeita a zona
de exclusão absoluta **por construção**; depende inteiramente da checagem
posterior. Isso é consistente com o pipeline `continuous_first` tratar
aberturas como recorte POSTERIOR ao layout (seção 23 das REGRAS) — o
preço dessa arquitetura é justamente este: nenhuma garantia geométrica a
priori contra vão de porta, só auditoria a posteriori.

### Bloco dentro do vão — censo independente por EXTENT real

Item 18 da missão: classificação por **corpo real** da peça
(`[t_start_cm, t_end_cm]`), nunca por ponto central, com filtro de
**banda vertical** (uma janela só é vazio na fiada certa — seção 4 das
REGRAS; a primeira versão deste censo não filtrava por banda e
superestimou o achado em ~10× — ver `README.md` do laboratório).

| Classificação | Contagem |
|---|---|
| FORA | 3.502 |
| DENTRO | **5** |
| PARCIAL | **108** |

Cross-check contra a função de produção `classify_extent_against_openings`
(`core/engine/continuous_modulation.py`), numa amostra de 60 casos
DENTRO/PARCIAL: **60/60 concordam** — a implementação de produção bate com
a definição documentada (seção 23.2 das REGRAS) nos casos amostrados; não
é um bug de fórmula. Os 113 casos (5 DENTRO + 108 PARCIAL) que
sobreviveram no `course_candidates` final (ou seja, o reparo de abertura
não os removeu) são achado real — pequeno em proporção (113/3.615 = 3,1%
das peças perto de alguma abertura), mas contraria a regra "bloco nunca é
criado dentro do vão" (item 10 da seção 23 das REGRAS) quando acontece.

---

## 13. Paredes não moduladas

Critério (deliberadamente fraco — só marca "não modulada" o caso grave de
zero peça na parede inteira):

| Métrica | Valor |
|---|---|
| Total de paredes | 167 |
| Sem nenhuma peça materializada | **29 (17,4%)** |
| Com ≥1 segmento `non_modular` (mas moduladas em parte) | 124 |

Ranking de causa (só das 29 sem nenhuma peça):

| Causa | Contagem |
|---|---|
| `L_T_X_FAILURE` (parede toca um nó sem solução) | 13 |
| `LENGTH_ARITHMETIC` (não fecha em blocos, sem abertura/nó envolvido) | 9 |
| `OPENING` (non_modular perto de uma abertura da própria parede) | 7 |
| `COLLISION` | 0 |
| `UNKNOWN` | 0 |

**29/167 bate EXATAMENTE com `COVERAGE_WALL_NOT_MODULATED=29`**, já medido
pelo benchmark oficial (`nuvem/benchmark/validators/validate_wall_
coverage.py`) na mesma classe de rodada — forte confirmação cruzada, com
metodologia e código totalmente independentes, de que este número está
certo e não é artefato de um validador específico.

`L_T_X_FAILURE` sendo a causa dominante (13/29, 44,8%) aponta para os
nós T/X sem solução (seção 10/11 acima) como o gargalo real de cobertura
— mais que problema aritmético de comprimento (9/29) ou abertura (7/29).

---

## 14. Determinismo

**Pergunta testada**: o `solve_building_blocks_all_courses` (o solver de
BLOCOS) é invariante à ordem de entrada das paredes já resolvidas
(`input.json`, saída da Fase A)? Isto é uma camada ACIMA do que o CR-2F-D
já corrigiu (merge/pareamento/dedup de segmentos CAD) — nunca medido
antes.

8 rodadas do solver real sobre o mesmo projeto (`torre_easy_lo_r00_tgd`):
baseline, ordem invertida, endpoints de toda parede invertidos, e 5
embaralhamentos com seed fixa (1, 2, 3, 10, 42 — mesmas seeds do censo de
determinismo do CR-2F-D, só para comparabilidade).

| Rodada | Peças materializadas | Fingerprint (16 primeiros chars) |
|---|---|---|
| baseline | 10.657 | `fb521bcd8fc12598` |
| reversed | 10.611 | `2ba28e9d45267f36` |
| endpoint_reversal | 10.635 | `4f22d62c23dddb26` |
| shuffle seed 1 | 10.626 | `50ddb9dac74a43fb` |
| shuffle seed 2 | 10.695 | `98238ce850349137` |
| shuffle seed 3 | 10.706 | `731939426d75f49e` |
| shuffle seed 10 | 10.579 | `f5f1c421067a7601` |
| shuffle seed 42 | 10.576 | `c1e7ebc1a5354001` |

**8 fingerprints distintos em 8 rodadas — NÃO determinístico.** Variação
de até 130 peças (~1,2%) só por reordenar a entrada, sem mudar nenhuma
geometria.

**Localização da primeira camada que diverge** (fingerprint por peça,
chaveado pela geometria da PRÓPRIA parede — não pelo índice, que muda com
a permutação):

- `reversed` e `shuffle_seed_1`: já divergem no **grafo de nós**
  (`build_wall_graph`/`extend_wall_ends_to_junctions`) — a contagem de
  `T_INTERSECTION` muda (118 → 119 ou 120) **antes** do solver de blocos
  rodar. Ou seja, parte desta não-determinância **não é do solver de
  blocos** — é herdada de uma camada anterior que também depende da ordem
  de entrada, e que o CR-2F-D não cobriu (aquele CR tratou
  `merge_collinear_fragments`/`deduplicate_walls`, não `extend_wall_ends_
  to_junctions`/`build_wall_graph`).
- `endpoint_reversal`: o grafo de nós bate (mesma contagem por tipo), mas
  a contagem de peças POR PAREDE já diverge — aqui a causa está mais
  provavelmente no solver de blocos em si (ou em alguma função que usa o
  SENTIDO do eixo, não só os pontos).

**Implicação para o CR-BLOCK-01**: qualquer correção de prisma/fiadas que
não resolva também esta camada continuará produzindo resultados
diferentes dependendo da ordem de processamento das paredes — mesmo que
o prisma em si melhore. Recomendado tratar como CR **separado**, depois
de mapear se a causa está no grafo de nós ou no solver — ver backlog.

---

## 15. Performance

| Métrica | Valor |
|---|---|
| `solve_building_blocks_all_courses` (rodada única) | 3,47s |
| Fiadas físicas | 17 |
| Bandas de abertura | 8 |
| Candidatos agregados (todas as variantes/bandas) | 10.158 |
| Peças materializadas | 10.657 |

Não medido em profundidade nesta rodada (não é o foco desta missão, e o
hotspot já está documentado): `merge_collinear_fragments` +
`find_wall_pairs` (Fase A, O(n²) sobre os candidatos de pareamento,
ANTES deste solver) é o gargalo já registrado em
`REGRAS_MODULACAO_BLOCOS.md` seção 26.1 (item M do plano da correção do
CR-1) — ~25s medidos lá, contra os ~3,5s do solver de blocos em si.
`run_determinism_census.py` (8 rodadas do solver de blocos) levou ~30s no
total — o solver de blocos sozinho não é o hotspot do pipeline completo.

---

## 16. Matriz — regras documentadas × implementação

Cobertura das regras mais centrais (não exaustiva — `REGRAS_MODULACAO_
BLOCOS.md` tem >26 seções). `CUMPRIDA` aqui significa "o censo mediu
evidência de cumprimento na amostra real", não "prova formal".

| Regra | Fonte | Confiança | Função | Teste existente? | Cumprida? |
|---|---|---|---|---|---|
| B39 é a peça padrão, 1ª prioridade | REGRAS §2 | OBRIGATÓRIA | `_pier_ordered_layout` tier 1 | sim (`tests/test_script.py`) | sim (não medido por código, mas base do preenchimento) |
| B19 nunca no meio de trecho | REGRAS §2 | OBRIGATÓRIA (incondicional) | `_merge_adjacent_compensator_pairs` + `audit_wall_bond_quality` (`HALF_BLOCK_NEAR_TIE`) | sim | **PARCIAL** — 100/840 (11,9%) a >60cm de qualquer borda (achado §6 acima, não confirmado como violação de fato) |
| Compensador nunca 2+ em sequência | REGRAS §2 | OBRIGATÓRIA | `MAX_COMPENSATORS_PER_TRECHO=1` na geração; sem auditoria pós-fato equivalente medida aqui | parcial | **NÃO CUMPRIDA** — 183 sequências puras de C09, 11 de C04 (§4/§5 acima) |
| L_CORNER sempre B34, vão menor sobreposto | REGRAS §5 | OBRIGATÓRIA | `solve_l_corner` + `validate_l_corner` | sim | **CUMPRIDA** — 62/63 TRUE, amostra validada |
| T_INTERSECTION: 3 níveis por espaço real | REGRAS §5 | OBRIGATÓRIA | `solve_t_intersection`/`_t_intersection_room_ok` | sim | **CUMPRIDA** — 80 TRUE + 23 DEGRADED coerentes com espaço; 15 sem solução |
| X_INTERSECTION: 2×B54 centrado | REGRAS §5 | OBRIGATÓRIA | `solve_x_intersection` | sim | **PARCIAL** — 8/17 TRUE, 9/17 (52,9%) sem solução — taxa de falha alta |
| Regra #1 — sem junta corrida entre fiadas | REGRAS §11 | OBRIGATÓRIA, bloqueante | `_pier_layout_avoiding_joints`, `validate_wall_modulation`, `audit_wall_bond_quality` | sim, extenso | **PARCIAL** — 1.086 suspeitas (censo independente); ordem de grandeza compatível com `PRISM_CONTINUOUS_JOINT=961` já documentado |
| Exceção 11.8 — peça pequena encostada em vão pode alinhar | REGRAS §11.8 | EXCEÇÃO PERMITIDA | `OPENING_ALIGNED_EXEMPT_CODES`, `_joint_is_opening_aligned_exempt` | sim | medida (10 casos isentos no censo), sem contradição encontrada |
| `PIER_LAYOUT_VARIANTS_PER_COURSE` = K=3 | REGRAS §11.7 | **DESATUALIZADA** — revogada pela §18.4 | `PIER_LAYOUT_VARIANTS_PER_COURSE = 1` (código) | sim (`test_fiadas_de_mesma_paridade_repetem_com_o_default`) | **CONFLITO JÁ REGISTRADO** no próprio documento (§18.4) — K real em produção é 1, não 3 |
| Porta sem peitoril — zona de exclusão absoluta | REGRAS §3 | OBRIGATÓRIA, sem exceção | `find_door_void_violations` (reativo) | sim | **REATIVA, NÃO PREVENTIVA** — 290 candidatos pegos pela rede de segurança em 41/167 paredes (§12 acima); a regra é cumprida no sentido de "nunca cria", mas não é respeitada pela geração do layout |
| Janela só é vazia na faixa vertical do vão | REGRAS §4 | OBRIGATÓRIA | `_opening_active_in_course_band`, `_group_course_indices_by_opening_band` | sim | **CUMPRIDA** — usada corretamente pelo pipeline (confirmado ao reproduzir a mesma filtragem no censo de aberturas) |
| Bloco nunca fica dentro do vão (extent real) | REGRAS §23.2 | OBRIGATÓRIA | `classify_extent_against_openings`, `split_extents_by_openings`, `_recut_openings_and_repair` | sim | **QUASE CUMPRIDA** — 113/3.615 (3,1%) sobrevivem DENTRO/PARCIAL no resultado final; fórmula em si confirmada correta (60/60 cross-check) |
| Ordem `continuous_first`: parede completa antes dos blocos | REGRAS §23.5b | OBRIGATÓRIA (processo, não só solver) | `build_wall_segments` sem `create_wall_opening_cuts`; ordem em `_execute_create` | sim | **NOT_HEADLESS_OBSERVABLE** — é uma regra sobre ORDEM DE CHAMADAS no Revit real, não sobre o resultado do solver puro; este laboratório não abre Revit |
| Motor determinístico (paredes) | REGRAS §26.10 (CR-2F-D) | OBRIGATÓRIA | `merge_collinear_fragments`, `deduplicate_walls` | sim, 11 invariantes | **CUMPRIDA** (fora do escopo desta auditoria — não remedido, já confirmado por CR-2F-D) |
| Motor determinístico (blocos) | nunca documentada explicitamente como regra | — | nenhuma | não | **NÃO CUMPRIDA** — achado novo desta auditoria (§14 acima) |

---

## 17. Backlog priorizado

Frequência e severidade vêm diretamente dos censos acima; risco de
regressão é uma estimativa qualitativa baseada em quantos testes/
invariantes já cobrem a área hoje.

### P0 — quebra de regra obrigatória, com dado real

| # | Achado | Frequência | Evidência | Função provável | CR sugerido | Risco de regressão |
|---|---|---|---|---|---|---|
| P0-1 | Compensador C09/C04 em sequência (2+), só preenchimento comum | 183 (C09) + 11 (C04) | §4/§5 | `_pier_ordered_layout`, `_merge_adjacent_compensator_pairs` | CR-COMPENSADORES | médio — mexe no tier 6-7 do preenchimento, área já bem testada |
| P0-2 | Solver de blocos não determinístico sob permutação de entrada | 8/8 fingerprints distintos | §14 | `build_wall_graph`/`extend_wall_ends_to_junctions` (camada que diverge primeiro na maioria dos casos) + possivelmente o próprio solver | CR-BLOCK-DETERMINISM | alto — toca grafo de nós, usado por TUDO depois |
| P0-3 | Junta corrida entre fiadas (regra #1) ainda residual | 1.086 suspeitas, 47/167 paredes | §3 | `_pier_layout_avoiding_joints` | **provavelmente já é o CR-BLOCK-01** (CONTA 1) | — (fora do escopo desta conta) |

### P1 — modulação tecnicamente errada, frequente

| # | Achado | Frequência | Evidência | Função provável | CR sugerido | Risco |
|---|---|---|---|---|---|---|
| P1-1 | X_INTERSECTION sem solução em mais da metade dos nós | 9/17 (52,9%) | §11 | `solve_x_intersection`, falta de degradação (X não tem fallback como T) | CR-X-DEGRADACAO | médio — precisa de uma nova regra de degradação, não só ajuste de tolerância |
| P1-2 | Bloco sobrevive DENTRO/PARCIAL de vão real depois do reparo | 113 casos (5 DENTRO + 108 PARCIAL) | §12 | `_recut_openings_and_repair`/`opening_repair_regions` | CR-OPENING-REPAIR | médio |
| P1-3 | `door_void_violations` só reativo — 41/167 paredes (24,6%) afetadas | 290 candidatos | §12 | geração do layout não conhece o vão de porta sem peitoril a priori | CR-DOOR-EXCLUSION-PREVENTIVA | médio-alto — mudar de "detectar depois" para "nunca gerar" é mais invasivo |
| P1-4 | 13/29 (44,8%) paredes não moduladas por falha em L/T/X | 13 | §13 | mesma raiz de P1-1 (X) + falhas T sem solução | (mesmo CR de P1-1, ou dependente dele) | — |

### P2 — uso ruim de peças especiais

| # | Achado | Frequência | Evidência | Função provável | CR sugerido | Risco |
|---|---|---|---|---|---|---|
| P2-1 | B19 a >60cm de qualquer abertura/ponta (achado a confirmar) | 100/840 (11,9%) | §6 | `_pier_ordered_layout` tier 2/4/5 | investigar antes de virar CR | baixo — é medição, não correção |
| P2-2 | B34 em sequência PURA de preenchimento (não tocando nó) | 40/2.530 | §7 | `_pier_ordered_layout` tier 3, `MAX_SPECIAL_BOND_PER_TRECHO` | avaliar se já é coberto pela regra existente | baixo |
| P2-3 | `jamb_exceptions=172` em modo `continuous_first` (inesperado pela doc) | 172 | §12 | investigar se é degradação (§23.5) ou resíduo | investigar antes de CR | baixo (só investigação) |

### P3 — qualidade/otimização

| # | Achado | Evidência | CR sugerido |
|---|---|---|---|
| P3-1 | `PIER_LAYOUT_VARIANTS_PER_COURSE=1` (conflito §18.4/§11.7 já registrado) — decidir se K volta a variar SÓ nos trechos com compensador, como a "solução fina" já cogitada nas REGRAS | §2 (Sumário) | CR-VARIANT-TARGETED (pendência já nomeada nas REGRAS, seção 18.4/23.7) |
| P3-2 | Performance da Fase A (`merge_collinear_fragments`/`find_wall_pairs`, O(n²)) — já documentado, fora do escopo de blocos | §15 | fora do escopo desta auditoria (motor de paredes) |

### P4 — UX/diagnóstico

| # | Achado | Evidência | CR sugerido |
|---|---|---|---|
| P4-1 | Nenhum validador atual distingue "sequência de peça especial tocando nó" (legítima) de "sequência pura de preenchimento" (violação) — este censo faz essa distinção (§7), o benchmark oficial pode não fazer | §7 | melhorar `validate_compensators`/`validate_junctions` com o mesmo critério |
| P4-2 | `intersection_failures` é uma lista por TENTATIVA (banda/fiada), não por nó único — fácil de super-contar se lido ingenuamente | §10 (nota de metodologia) | documentar em `REGRAS_MODULACAO_BLOCOS.md` |

---

## 18. Sequência de CRs recomendada

Baseada nos dados acima, não numa ordem assumida a priori:

1. **CR-BLOCK-01 (CONTA 1, em andamento)** — prisma/fiadas. Maior volume
   de achados (P0-3, 1.086 suspeitas) e já em progresso.
2. **CR-BLOCK-DETERMINISM** (P0-2) — antes de qualquer outro CR de blocos
   ganhar um benchmark de "antes/depois" confiável, o solver de blocos
   precisa produzir o MESMO resultado em toda rodada. Sem isso, qualquer
   comparação de números entre versões corre risco de estar medindo
   ruído de ordem, não a correção em si. Recomendado logo depois do
   CR-BLOCK-01 (ou em paralelo, se a mesma pessoa não estiver
   ocupada com prisma).
3. **CR-COMPENSADORES** (P0-1) — segunda maior classe de violação
   obrigatória, já isolada por este censo (distinção mid-wall-puro vs
   tocando-nó).
4. **CR-X-DEGRADACAO** (P1-1/P1-4) — taxa de falha de 52,9% em X é alta
   demais para não ter prioridade; contribui diretamente para paredes não
   moduladas.
5. **CR-DOOR-EXCLUSION-PREVENTIVA** (P1-3) — mover a checagem de "réptil"
   para "preventiva" reduziria as 41 paredes afetadas por
   `door_void_violations`.
6. **CR-OPENING-REPAIR** (P1-2) — os 113 casos residuais de bloco em vão.
7. P2/P3/P4 — depois dos P0/P1, por ordem de esforço vs impacto.

Não incluído aqui porque fora do escopo de blocos: vergas, contravergas,
canaletas, blocos cortados (catálogo de 33 tipos ainda não suportado pelo
solver — seção 24.5 das REGRAS) — todos legítimos candidatos a CR futuro,
mas sem dado de frequência medido nesta auditoria (o solver de blocos hoje
nem tenta usá-los).

---

## 19. Limitações desta auditoria (explícitas)

- Censo detalhado rodado só sobre `torre_easy_lo_r00_tgd` (o único
  projeto com `input.json` medido, não reconstruído). `torre_easy_lo_
  r00_tp1` e `piloto_sintetico_2x2` entraram só no resumo de escala
  (`out_full_census.json::secondary_projects_summary`).
- Alinhamento de célula (vão menor) de B34 de meio-de-parede não foi
  medido — precisa de acesso a `cells_world` por par de fiadas, não feito
  aqui por prioridade de tempo.
- Item 22 da missão (soluções alternativas não escolhidas) só foi medido
  de forma leve, dependente de `variants_per_course>1`, que não é o modo
  de produção — ver nota na seção 3.
- A regra "ordem de chamadas no Revit real" (seção 23.5b das REGRAS) é
  `NOT_HEADLESS_OBSERVABLE` por definição — não dá pra confirmar sem abrir
  o Revit.
- Este documento audita a MAIN original; não leu nem comparou com a
  branch da CONTA 1 (`CR-BLOCK-01`) em nenhum momento.

**ARQUIVOS DE PRODUÇÃO ALTERADOS NESTA AUDITORIA: ZERO.**
