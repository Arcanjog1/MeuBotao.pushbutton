# CR-BLOCK-01 — prisma, fiadas e amarração vertical (CONTA 1)

Diretório **exclusivo da CONTA 1**. Contém o mapa do pipeline, o benchmark
headless reprodutível e as medições antes/depois.

* `metrics.py` — medição headless (roda o solver REAL, mede a geometria
  que sai dele; nenhuma reimplementação, nenhum Revit/MCP).
* `run_baseline.py` — CLI que grava `out_baseline.json` / `out_after.json`.
* `compare.py` — gera `compare_before_after.json` (ANTES/DEPOIS/DELTA/Δ%).
* `trace_segment.py` — tracing de um trecho isolado (prova por ablação).

```bash
python3 nuvem/benchmark/diagnostics_block_prisma/run_baseline.py \
    --out nuvem/benchmark/diagnostics_block_prisma/out_baseline.json
```

---

## 1. Mapa do pipeline — parede → fiada → junta → escolha → posicionamento

Tudo abaixo foi levantado por leitura + *tracing* do código real, não pelo
nome das funções.

```
extend_wall_ends_to_junctions / build_wall_graph        (geometry.py, wall_pairing.py)
  └─ nodes, end_to_node                                  ← INPUT desta fase, não se toca
     │
     ├─ solve_all_intersections(nodes, ...)               wall_stepper.py:1303
     │    ├─ solve_x_intersection  → B54 centrado
     │    ├─ solve_t_intersection  → B54 / B34 / C09-C04 degradado
     │    └─ solve_l_corner        → B34 (vão menor alinhado entre A e B)
     │    ⇒ `intersection_candidates` = PEÇAS DE AMARRAÇÃO DE NÓ.
     │      Já carregam `course` ("A"/"B") e `node_index`. São RESTRIÇÃO:
     │      o preenchimento nunca as move.
     │
     ├─ _index_node_candidates_by_wall_end   :3693  → fronteira das PONTAS
     └─ _index_node_candidates_midspan       :3843  → fronteiras de MEIO de parede
          (chave (wall_idx, course) — PODE diferir entre A e B)
             │
process_walls_one_by_one :5283  (uma parede por vez, ordem geométrica)
  └─ solve_wall_free_fill(wall_idx, ...) :4289      ◀── O CORAÇÃO DESTE CR
       │
       │  boundaries = WALL_START | (OPENING_LO/HI) | MIDSPAN_LO/HI | WALL_END
       │  `continuous_first` (padrão): as ABERTURAS NÃO entram em boundaries
       │
       └─ for course in ("A", "B"):            ← A) e B) do CR
            for variant_index in range(variants_per_course):   (K = 1 hoje)
              for seg_i in trechos:
                 ┌ seg_start_cm / seg_end_cm, lead_cm / trail_cm,
                 │ leading_is_open / trailing_is_open (nó ⇒ False)
                 │
                 ├ course "A", variante 0:
                 │    _continuous_segment_layout :3961   (ou _pier_ordered_layout)
                 │    ⇒ NENHUMA informação da outra fiada — A é a referência
                 │
                 └ course "B" (e variantes A≥1):
                      _pier_layout_avoiding_joints :3399  ◀── ESCOLHA ENTRE CANDIDATOS
                          avoid  = course_a_joint_positions_cm + own_family_...
                          target = course_a_void_positions_cm
              [continuous_first] _recut_openings_and_repair :4092
                          → recorta os vãos, remove peças inteiras,
                            _solve_repair_subsegments :4053 chama de novo
                            _pier_layout_avoiding_joints na região afetada
              flush: as juntas/vazios PUBLICADOS são os da geometria FINAL
                     (`joint_positions_from_extents`), nunca os da fase 1
       ⇒ validate_wall_modulation :5038  (sem_alinhamento_vertical, regra #2…)
          audit_wall_bond_quality (wall_modeling.py:3591) — 2ª verificação,
          parede INTEIRA, todas as fiadas físicas
```

`solve_building_blocks_all_courses` (`core/wall_modeling.py:3053`) roda o
bloco acima **uma vez por BANDA** de fiadas (conjunto de aberturas ativas
naquela faixa vertical) e replica o par A/B da banda em todas as fiadas
físicas dela: `letter = "A" if course_index % 2 == 0 else "B"`.

### Respostas diretas às perguntas A–K do CR

| | Resposta medida |
|---|---|
| **A) onde a FIADA 1 é resolvida** | `solve_wall_free_fill`, iteração `course == "A"`, `variant_index == 0` — `_continuous_segment_layout` (com abertura) ou `_pier_ordered_layout` (sem). |
| **B) onde a FIADA 2 é resolvida** | Mesma função, iteração `course == "B"` — sempre `_pier_layout_avoiding_joints`. |
| **C) que informação da fiada anterior é passada** | `course_a_joint_positions_cm` (juntas internas absolutas, cm, no eixo da parede) e `course_a_void_positions_cm` (centros das células internas). No modo contínuo são publicadas só **depois** do recorte/reparo. |
| **D) as juntas anteriores chegam ao solver?** | **Sim.** `avoid_positions_cm` chega a `_pier_layout_avoiding_joints` e é usado em `_count_joint_coincidences_cm` / `_layout_min_joint_stagger_cm`. |
| **E) chegam mas não influenciam a escolha?** | Influenciam — só que **não há o que escolher**: a lista de candidatos é pequena demais (ver §3). O critério existe e funciona; o espaço de busca é que é incompleto. |
| **F) há múltiplos layouts candidatos?** | Sim, mas todos derivados de **variar apenas o PRIMEIRO bloco**: baseline + `_half_block_leading_layout` + `_pier_forced_bypass_layouts` + `_pier_ordered_layout(first_code=…)` para cada código de `OPENING_JAMB_BLOCK_CODES` (que **não contém B34**). Nenhum candidato reordena as peças de um mesmo conjunto. |
| **G) como o vencedor é escolhido** | `_score` lexicográfico: `(excesso de compensador em sequência, coincidência de junta, −travamento, −alinhamento de vazio)`, MENOR melhor, com `<` **estrito** (empate mantém o baseline ⇒ dependência de ordem de enumeração). |
| **H) onde compensadores entram no desempate** | Primeiro componente do `_score` (`_layout_compensator_run_excess`, regra #2, seção 16.1) e como *bypass de tier* em `_pier_forced_bypass_layouts` (B34/C09/C04 forçados como primeiro bloco). |
| **I) onde meio bloco entra** | `_half_block_leading_layout` (só quando há alvo de vazio **e** `leading_is_open`); tiers 2/4 de `_pier_ordered_layout` (ponta aberta); tier 6 (últimíssimo recurso, ponta fechada); e `_merge_adjacent_compensator_pairs` (9+9→19, só em ponta aberta). |
| **J) como aberturas alteram o processo** | Modo `continuous_first`: a abertura **não** é fronteira — a parede é modulada inteira e depois recortada (`_recut_openings_and_repair`), e o reparo volta a chamar `_pier_layout_avoiding_joints`. As bandas verticais (`_group_course_indices_by_opening_band`) fatiam as fiadas por conjunto de aberturas ativas. |
| **K) como L/T/X reservam espaço** | `solve_all_intersections` roda ANTES; os candidatos de nó viram `border` (`node_candidates_by_wall_end`) e `MIDSPAN_LO/HI` (`node_midspan_by_wall_course`). O trecho de preenchimento começa/termina depois deles, com `leading_is_open/trailing_is_open = False` — o preenchimento nunca ocupa nem desloca o espaço do nó. |

---

## 2. Definição geométrica de junta usada na medição

Idêntica à do motor, no **referencial longitudinal da parede**:

* posição de cada peça = projeção do corpo no eixo
  (`_candidate_extent_on_wall_axis`), em cm a partir de `p0`;
* duas peças consecutivas separadas por no máximo
  `BOND_MAX_ADJACENT_GAP_CM` (5cm) formam junta — acima disso há um vão, não
  uma junta (mesma proteção da auditoria oficial);
* coincidência = distância ≤ `VERTICAL_JOINT_STAGGER_TOLERANCE_CM` (1cm),
  a mesma tolerância que o próprio solver usa.

Nunca se compara índice de bloco, ordem de lista, ElementId nem coordenada
global crua. A isenção da seção 11.8 é avaliada pela **função do motor**
(`_joint_is_opening_aligned_exempt`), nunca por uma cópia.

## 3. Classificação (seção 10 do CR)

| Classe | Quando |
|---|---|
| `FORBIDDEN_JOINT_ALIGNMENT` | juntas coincidem e nenhuma regra documentada permite (violação da regra #1) |
| `DOCUMENTED_EXCEPTION` | seção 11.8 — C04/C09/B19 encostado numa borda de abertura ou na ponta do eixo |
| `UNCLASSIFIED_RULE_CONFLICT` | a coincidência envolve uma peça de amarração de nó, que a seção 5 manda repetir na mesma posição em toda fiada da mesma paridade. Duas regras documentadas se cruzam e o documento não diz qual vence — **registrado, nunca resolvido por suposição** |
| `NO_ALIGNMENT` | sem coincidência |
