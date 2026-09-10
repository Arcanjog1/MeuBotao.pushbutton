# RELATÓRIO FINAL — NODE-FILL REVALIDATION

`CR-BLOCK-NODE-FILL-REVALIDATION` (2026-09-04, PR `#17`). Revalidação
do fix histórico NODE-FILL (`claude/cr-block-node-fill-joint-9tv0kd`)
sobre a base de medição descrita abaixo. **NÃO MERGEADO** — estado do
PR/branch em `docs/PROJECT_STATUS.md` (não repetido aqui, para este
documento não ficar obsoleto a cada refresh).

> Regra de leitura: tudo aqui foi medido de novo nesta sessão. Os
> números históricos (TGD 702→318, TP1 837→169, piloto 14→0) NÃO são
> baseline de nada — ver "Histórico analisado".

## Base

```
MEASUREMENT_BASE (origin/main no momento da medição):
  68a62693ba4ac3a1def43be8b84d526372a4ee9a   (G1: exato)
  contém: PR #12 (ARM Candidate Safety Contract, SAFE REPAIR ativo),
          PR #13 (Context Optimization V2), START_HERE/PROJECT_STATUS
          current-only, CR-BENCH-Z-ORIGIN (benchmark na mesma origem
          vertical do motor).
```

### Proveniência pós-medição (refresh 2026-09-04, sem remedir)

A `main` avançou depois da medição acima por três merges **docs-only**
(`PR #14` snapshot refresh, `PR #15` Gate-Fidelity spec, `PR #16`
evidência de domínio B19 — os três com diff de produção declarado ZERO
e confirmados via `git diff --stat`). Comparação direta entre
`MEASUREMENT_BASE` e a ponta da `main` no momento deste refresh
(`CURRENT_MAIN_AT_PREMERGE = 789f44227145ecc681c714fb952e10dd1de507d9`)
confirma: **`nuvem/core/**`, `nuvem/benchmark/**` (código/validators),
`tests/**` e todo `baseline.json`/`reference.json` são byte-idênticos**
entre as duas bases — só documentação mudou. `PRODUCTION_EQUIVALENT =
TRUE`: as medições abaixo (STATE_A/STATE_B, todas as métricas, os
testes e a suíte completa) continuam válidas sem remedição. A branch
desta CR foi atualizada com um merge normal de `origin/main` (sem
cherry-pick, sem reconstrução do NODE-FILL) para carregar essa
documentação; nenhum código de produção mudou nesse merge.

## Branch / HEAD

```
branch: claude/cr-block-node-fill-revalidation-iahuyg
        (nome designado pela sessão; o pedido citava
        `claude/cr-block-node-fill-revalidation` — mesmo sufixo de sessão
        que as demais branches `claude/*` do repositório)
base:   origin/main @ 68a62693 (branch NOVA, sem cherry-pick, sem rebase)
```

## Histórico analisado

### branch histórica

`claude/cr-block-node-fill-joint-9tv0kd`, HEAD `bf4054b6`. **Base
histórica ≠ main**: a branch nasce de `2594f6ff` (cross-audit do
`CR-BLOCK-DETERMINISM`, CONTA 3), que contém o wall graph canônico
(`e8f8da8`, `476ff11`, `6dd4753`) — **nenhum desses commits está na
`main`** (`git merge-base --is-ancestor` → não). Entre `2594f6ff` e
`origin/main`, `wall_stepper.py` mudou 1255 linhas (PRISM-STAGGER,
ARM-ROLE, SAFE REPAIR). O patch histórico não aplica (`git apply
--check` falha; `--3way` só com conflitos). Por isso o histórico foi
usado apenas como evidência.

### commit histórico

`d1fc4abb` — "a junta PEÇA DE NÓ | PREENCHIMENTO passa a ser uma junta
de verdade". `bf4054b6` — diagnóstico posterior: a regressão
`OPENING_BLOCK_INSIDE_DOOR` 45→49 era FANTASMA (duas origens verticais no
benchmark; corrigido depois por `CR-BENCH-Z-ORIGIN`, já na `main`).

### diff de produção histórico

Inventário exato de `d1fc4abb` em `wall_stepper.py` (+315/−11):

| item | o que era | o que passou a ser |
|---|---|---|
| `_segment_node_boundary_joints_cm` (nova, pura) | não existia: `_layout_internal_joint_positions_cm` devolve `range(n-1)`, só juntas ENTRE dois blocos do layout | junta de FRONTEIRA do trecho contra peça de nó: `seg_start - J/2` / `seg_end + J/2`, só quando `leading_is_node`/`trailing_is_node` |
| flags `leading_is_node`/`trailing_is_node` | não existiam (`*_is_open` também é False na rede de segurança `oi_left is None`, onde não há nó) | True só nos ramos `WALL_START`/`WALL_END` com `border` de nó e `MIDSPAN_HI`/`MIDSPAN_LO` |
| `_wall_node_boundary_joints_cm` (nova, pura) | não existia | juntas de nó da fiada OPOSTA deduzidas só de `node_candidates_by_wall_end` + `node_midspan_by_wall_course` (a **metade simétrica**) |
| `_node_boundary_joints_backed_by_pieces_cm` (nova, pura) | não existia | descarta junta cuja peça o recorte derrubou (filtro pela geometria final) |
| Fiada A, variante 0 | layout padrão, sem busca | se colide com junta de nó da B: `_pier_layout_avoiding_joints` e troca só se ESTRITAMENTE menos coincidência |
| busca da Fiada B | `course_a_joint_positions_cm + own_family` | + `course_a_node_boundary_joints_cm` + `opposite_node_joints_cm` + `own_family_node_boundary_joints_cm` |
| reparo de abertura (`_recut_openings_and_repair`) | só juntas internas | + juntas de nó (A e própria família) |
| gate | `alignment_conflicts` (B interna × A interna) | + `node_boundary_conflicts` (B interna × A de nó), separado, sem disparar `needs_fix` |
| `per_wall`/`solve_all_wall_fill`/`process_walls_one_by_one` | — | propagam `node_boundary_conflicts` |

## Mecanismo original

O mecanismo histórico NÃO é "ignorar a junta node-fill" (hipótese da
seção 7 do pedido) — é o **contrário**: a junta NÓ|FILL não existia em
lista nenhuma, então a fiada oposta **não a evitava**. O fix a coloca na
lista a evitar (mudança FÍSICA da modulação) e, em separado, a reporta
no gate.

**Hipótese da seção 7 — REFUTADA na direção enunciada, confirmada na
inversa.** Não há caso, nem no histórico nem na `main`, em que uma junta
NÓ|FILL fosse contada "a mais" como junta estrutural: o defeito é ela
ser contada "a menos" (invisível para a busca de desencontro).

**O que a `main` já tem.** `CR-BLOCK-ARM-ROLE-PRISM-STAGGER` (`a519669`,
PR #12) já implementou a metade "A→B": `_pier_boundary_joint_positions_cm`
publica a junta de contorno da Fiada A contra a peça de nó e a busca da
Fiada B a evita (e o gate `alignment_conflicts` a conta). Isso já
capturou o ganho histórico do piloto (14 → 0) e parte do TGD/TP1
(702→444, 837→576 na `main`).

**O que faltava (e é o objeto desta CR).** A **metade simétrica**: a
Fiada A roda PRIMEIRO e nunca vê a junta NÓ|FILL que a Fiada B vai ter.
Assinatura medida no corpus: Fiada A com junta interna `B19|B39` (ou
`B19|B34`) em t = 34,5 cm exatamente em cima da junta `B34(nó)|fill` da
Fiada B — em toda fiada da mesma paridade da parede.

## STATE_A — main atual

Medido em 2026-09-04 com `nuvem/benchmark/runner.evaluate_project`
(mesmo caminho de `run_project`, `write_files=False`), `solve_result`
cru do `solver_bridge` e o instrumento do `CR-BLOCK-01`
(`diagnostics_block_prisma/metrics.py`). Tabela completa em "Métricas
completas". Resumo:

| | TGD | TP1 | Piloto |
|---|---|---|---|
| PRISM_CONTINUOUS_JOINT | 444 | 576 | 0 |
| COVERAGE_MISSING_ROW / ROW_MOSTLY_EMPTY | 258 / 112 | 0 / 18 | 0 / 8 |
| OPENING_BLOCK_INSIDE_DOOR / CROSSES_JAMB | 5 / 108 | 0 / 168 | 0 / 0 |
| collisions | 1043 | 14 | 0 |
| ARM accepted / rejected | 1 / 21 (7 arestas) | 0 / 9 (3 arestas) | 0 / 0 |
| runtime solver | 43,5 s | 24,6 s | 0,07 s |

Determinismo (STATE_A): fingerprint idêntico em 3 execuções
(A, A, A em um processo; A em outro processo).

## STATE_B — NODE-FILL reconstruído

Reconstrução CONTROLADA com flags de módulo em `wall_stepper.py` (fora
da árvore versionada no fim; nenhum `git stash`; STATE_A e cada STATE_B
medidos com o MESMO script, com `flags off` provado bit-idêntico a
STATE_A — fingerprint, códigos, prisma, ARM e colisões iguais):

| estado | conteúdo | PRISM TGD | PRISM TP1 | observação |
|---|---|---|---|---|
| B1 | metade simétrica (A evita nó da B) + lista deduzida também na busca da B | 336 | 256 | TGD: +6 COVERAGE_ROW_MOSTLY_EMPTY (W075), colisões 1043→1046 rearranjadas (paredes sobrepostas W011∥W075, W009∥W070), ARM `23\|SAME_A` deixa de ser necessário |
| B1+GATE | + `node_boundary_conflicts` separado | 336 | 256 | fingerprint IDÊNTICO a B1: só representação; `alignment_conflicts` → 0 nos 3 projetos (toda coincidência residual do gate envolve junta de nó) |
| B1+BACKED | + filtro pela geometria final | 336 | 256 | fingerprint IDÊNTICO a B1: nenhum efeito |
| B1+RECUT | + juntas de nó no reparo de abertura | 336 | 256 | fingerprint muda (W159/W095 compensadores rearranjados), sem ganho de prisma |
| B2 | só metade simétrica no lado A (busca da B intacta) | 336 | 256 | colisões voltam a 1043 (0 assinaturas novas); W075 continua |
| **B3 (final)** | B2 + juntas fantasma (peça que o recorte derruba) não decidem a troca | **336** | **272** | W075 volta; 0 regressão de cobertura/abertura/colisão; ARM idêntico |
| B4 | B3 + metade simétrica no reparo local | 336 | 272 | TGD bit-idêntico a B3; TP1 muda fingerprint sem mudar nenhum finding → descartado por minimalidade |

## Primeira divergência

Caso real, TP1 `W036` (wall_idx 35, 524 cm, T nos dois lados, X no
meio), fiada 0 (A) × fiada 1 (B), banda 0:

```
STATE_A
  B: peça de nó B34 [0..34] (T_INTERSECTION_INCOMING) → fill começa em 35
     → junta NÓ|FILL da B em 34,5   (geometria fixa do nó)
  A: fill começa em 15 (largura da peça do nó vizinho); layout PADRÃO
     [15..34 B19][35..74 B39]... → junta INTERNA da A em 34,5
  A roda primeiro: `course_a_boundary_joint_positions_cm` é publicado
     para a B, mas NADA diz à A onde está a junta de nó da B
  → PRISM_CONTINUOUS_JOINT r0/1 t=34,5 (`B19|B39` × `B34|B19`) em todas
     as fiadas pares×ímpares da banda (8 findings na parede)

STATE_B (metade simétrica)
  antes de resolver A: `_wall_node_boundary_joints_cm(35, "B", ...)`
     = [34,5, 489,5]  (dos `border` de `node_candidates_by_wall_end`)
  layout padrão da A colide (1 junta) → `_pier_layout_avoiding_joints`
     devolve [15..54 B39][55..74 B19]... (0 coincidências) → troca
  B (busca já existente) desencontra das juntas internas da A (54,5, ...)
  → finding desaparece; a fiada A mudou FISICAMENTE (bloco trocado de
     lugar). Humano (reference.json, W036 fiada 10/11): junta em 34,5
     numa fiada e 49,5 na outra — CONFIRMED_BY_HUMAN.
```

Mesma cadeia em `W038`, `W004`, `W007`, `W010`, `W012`, `W028`, `W037`,
`W052`, `W055`, `W056`, `W080`, `W020`, `W031` (TP1) e `W007`, `W028`,
`W073`, `W086`, `W166`, `W113`, `W031`, `W057`, `W105` (TGD) — todos com
t = 34,5 cm (o comprimento do B34 de nó + junta), `B19|B39` ou
`B19|B34` na A contra `B34|fill` na B.

## Classificação N1 / N2 / N3

| classe | contagem | evidência |
|---|---|---|
| **N1 — PHYSICAL_IMPROVEMENT** | TGD 108, TP1 308 findings (por chave `wall,row_a,row_b,t`) | o bloco físico da Fiada A mudou (ex.: `B19|B39` → `B39|B19`); medido na geometria do solver por um medidor independente do benchmark (`node_fill_prism_violations`, tests T3/T4/T20); fingerprint `walls_blocks` muda, `openings`/`junctions` idênticos |
| **N2 — REPRESENTATION_CORRECTION** | 0 no código final | a variante GATE (representação pura, fingerprint idêntico) foi medida e NÃO integrada |
| **N3 — VALIDATOR_MASKING** | **0** | nenhum validador foi alterado; `alignment_conflicts` do motor continua contando as juntas de contorno (T3b); nenhum finding some por reclassificação — TGD: 108 removidos / 0 novos; TP1: 308 removidos / 4 "novos" que são o MESMO par de fiadas (`W036`/`W038` r4/5 e r11/12) trocando de 34,5 para 54,5 cm, **cross-band** (bandas 0/1 e 4/5 — problema aberto 27.7, fora do par A/B) |

Contagens pela chave com códigos de peça (`a`/`b`) dão "removidos 110 /
novos 2" (TGD) e "310 / 6" (TP1): os "novos" adicionais são re-rótulos
do mesmo (`wall,rows,t`) com outra peça adjacente, não juntas novas.

**Reconciliação explícita (item 8 — sem inconsistência matemática
escondida):** o medidor físico independente (N1, por `wall,row_a,row_b,t`)
e o delta do validador `PRISM_CONTINUOUS_JOINT` do benchmark medem a
MESMA coisa por dois caminhos de código diferentes, e batem
aritmeticamente: `removidos − novos = |delta|` em ambos os projetos —
TGD `108 − 0 = 108` (444→336, delta −108) e TP1 `308 − 4 = 304`
(576→272, delta −304). Os "4 novos" do TP1 não são juntas inventadas:
são o MESMO par de fiadas cross-band (`W036`/`W038`) trocando de posição
de coincidência (34,5→54,5 cm) — ainda um `N1`, apenas contado como
"novo" pela chave `wall,row_a,row_b,t` porque `t` mudou.

## Exemplos TGD

(ids do benchmark = `model.assign_ids`, ordenação geométrica —
**não** são `wall_idx`; mapeamento reproduzido pelo mesmo sort no lab)

| # | parede | fiadas | ANTES | DEPOIS | classe | humano |
|---|---|---|---|---|---|---|
| 1 | `W007` (wall_idx 1, 1484 cm, L no início) | 0/1 … 10/11 (19 findings) | A `[15..34 B19][35..74 B39]` junta 34,5 × B `[0..34 B34/L_CORNER][35..54 B19]` junta de nó 34,5 | A `[15..54 B39][55..74 B19]` (54,5); B `[35..69 B34][70..89 B19][90..94 C04]` | N1 | humano `W011` (invertida): fiada 0 junta 54,5, fiada 1 34,5 — CONFIRMED |
| 2 | `W028` | 16 findings, t=34,5 | idem (`B19|B39` × `B34|B19`) | idem | N1 | humano `W028`: 49,5 / 34,5 — CONFIRMED |
| 3 | `W057` (wall_idx 121, 79 cm) e `W105` (124, 79 cm) | 8/9, 10/11 | A `[15..54 B39][55..64 C09]`; B `[0..34 B34/L][35..44 C09][45..79 B34/T]` — coincidência em bandas superiores | fiada A muda só nas bandas com nó/vão ativo | N1 | humano `W048`/`W062`: 34,5 numa fiada, 54,5 na outra — CONFIRMED |
| 4 | `W113` (wall_idx 82, 169 cm) | 14 removidos; 2 "novos" re-rotulados (r6/7, r11/12, t=39,5, cross-band 2/3 e 5/6, já existiam) | A `[15..24 C09][25..34 C09][35..39 C04][40..94 B54/T]` junta 34,5 × B `[0..34 B34/L]` nó 34,5 | A `[15..19 C04][20..29 C09][30..39 C09]` (19,5; 29,5) — mesma cadeia de 3 compensadores, só reordenada (COMPENSATOR_CONSECUTIVE da parede: mesma contagem por fiada) | N1 (junta), compensadores neutros | sem casamento |
| 5 | `W011` (wall_idx 23, 499,6 cm) — a parede do candidato ARM aceito `23\|SAME_A` | 0 findings antes e depois | ANTES: SAFE REPAIR precisou trocar o papel (`SAME_A`, pin em 2 nós) para eliminar o prisma forçado do ORIGINAL | DEPOIS (B3): o ORIGINAL ainda tem o prisma forçado (a peça de nó fica na B, `[0..34 B34/L_CORNER]` fiada B), o SAFE REPAIR aceita o MESMO candidato `23\|SAME_A`, mesmo pin — resultado final idêntico ao da main | — | — |

Regressão investigada e eliminada no caminho: `W075` (wall_idx 20, 584
cm, duas aberturas 33,8–264,8 e 318,8–544,8, nó B34 da B em `[550..584]`).
Em B1/B2 a Fiada A perdia `[550..559 C09][560..569 C09]` (+6
`COVERAGE_ROW_MOSTLY_EMPTY`): a troca de layout era decidida por uma
junta em 549,5 do layout contínuo PRÉ-recorte, cuja peça `[510..549]`
cruza a jamba 544,8 e é derrubada — junta fantasma; o layout trocado
deixava o reparo local sem fechamento. B3 conta só juntas entre peças que
`split_extents_by_openings` mantém (o MESMO critério do recorte) —
`W075` volta ao estado da main.

## Exemplos TP1

| # | parede | fiadas | ANTES | DEPOIS | classe | humano |
|---|---|---|---|---|---|---|
| 1 | `W036` (wall_idx 35, 524 cm) | 0/1, 2/3, 3/4 (banda 0), 4/5→ ver limite | A `[15..34 B19][35..74 B39]` (34,5) × B `[0..34 B34/T][35..54 B19]` nó 34,5 | A `[15..54 B39][55..74 B19]`; B `[35..39 C04][40..59 B19][60..94 B34]` (busca da B, `_pier_forced_bypass_layouts` já existente) | N1 | `W036` humano: 34,5 / 49,5 — CONFIRMED |
| 2 | `W038` (wall_idx 37) | idem | idem | idem | N1 | CONFIRMED |
| 3 | `W052` (wall_idx 51, 2349 cm, 40 findings removidos) | várias | A `[750..769 B19][770..809 B39]` (769,5) × B nó X `[715..769 B54]` → 769,5 | A `[750..784 B34][785..804 B19]` (784,5; 804,5) | N1 | (fiada humana vazia em parte) |
| 4 | `W002` (wall_idx 1, 269 cm) | 11/12, 12/13, 13/14 | A `[15..34 B19][35..74 B39]` × B `[0..34 B34/T]` | A `[15..54 B39][55..74 B19]` | N1 | — |
| 5 | `W004`, `W007`, `W010`, `W012`, `W028` | 16 cada, t=34,5 | mesma assinatura | mesma correção | N1 | 202/310 removidos CONFIRMED no total |

**Limite conhecido (documentado, não mascarado):** em `W036`/`W038`,
fiadas 5–12 (bandas em que a janela está ativa), a coincidência em 34,5
PERMANECE (16 findings). Cadeia: o layout contínuo da A na banda é
`[15..34 B19][35..74 B39]…`; `[35..74]` cruza a jamba (≈70) → o filtro
conservador classifica a junta 34,5 como "adjacente a peça derrubada" e
NÃO troca; o recorte derruba `[35..74]` e o reparo local refaz `[35..69]`
com `B34` a partir da peça mantida `B19 [15..34]` — a junta 34,5
renasce. A troca no reparo (B4) não resolve porque a junta é o CONTORNO
da região de reparo, fixado pela peça mantida. Correção exige o reparo
consciente da junta de nó da fiada oposta E da posição da peça mantida
(fora do mínimo desta CR) — registrado em `REGRAS_MODULACAO_BLOCOS.md`
33.5 como pendência.

**Segundo residual (limite genuíno, não desta CR):** TP1 `W003`/`W008`
(wall_idx 2/7, 1344 cm) e `W061` (wall_idx 60, 79 cm): a Fiada A começa
com `[15..24 C09][25..34 C09][35..44 C09]` contra um `B34` de X/T
DEGRADADO em 45 — 30 cm entre a largura do nó vizinho e a peça degradada,
cuja ÚNICA composição é 3×`C09` (juntas fixas 24,5/34,5/44,5). Nenhuma
troca de layout move a junta 34,5; é o mesmo limite de "geometria fixa"
da seção 30.6 (agora numa cadeia de compensadores). Medido pelo medidor
independente no TP1, banda 0: violações NÓ|FILL 28 → 12; assinatura
34,5/B 16 → 4 (as 4 são estes casos).

## Piloto

PRISM 0 → 0 (o ganho histórico 14→0 já estava na `main` via
PRISM-STAGGER). Única mudança física: `W006` (wall_idx 5), Fiada A
`[15..34 B19][35..74 B39]…` → `[15..49 B34][50..69 B19][70..109 B39]…`,
para não empilhar sobre a junta de nó da B em 34,5 — cuja Fiada B, por
problema PRÉ-EXISTENTE do X degradado (`COVERAGE_ROW_MOSTLY_EMPTY` 8, igual
antes e depois), não tem preenchimento. Troca conservadora ("custa
liberdade de busca, nunca inventa geometria"); nenhum finding muda;
auditoria interna `REPEATED_VERTICAL_COMPENSATOR_STRIP` 13→14 (B19
repetido no meio em vez de na ponta — nível 2 da auditoria do motor, não
finding do benchmark). Determinismo: B,B,A,B idênticos.

## Reference Corpus humano

Comparação de CADA finding removido com `reference.json` (parede casada
por geometria — `start_cm`/`end_cm`, ids NÃO são estáveis; tolerância 1
cm na posição da junta, mesmo `JOINT_ALIGNMENT_TOLERANCE`):

| classe | TGD (110) | TP1 (310) |
|---|---|---|
| CONFIRMED_BY_HUMAN — humano tem junta em t numa das duas fiadas e desencontra na outra | 34 | 192 |
| CONSISTENT_WITH_HUMAN — humano não tem junta em t em nenhuma das duas | 6 | 41 |
| NO_HUMAN_EVIDENCE — fiada humana vazia | 8 | 77 |
| NO_HUMAN_EVIDENCE — parede sem correspondente no reference (TGD: input medido × nível 04) | 62 | 0 |
| **CONFLICTS_WITH_HUMAN — humano também tem a junta corrida** | **0** | **0** |

Padrão humano nos casos casados: a peça de nó `B34` encosta no fill e a
fiada oposta começa com `B34` (junta 49,5) ou `B39` (54,5) — nunca `B19`
(34,5). O solver corrigido escolhe `B39+B19` (54,5) onde o humano usa
`B34+B19` (49,5): composição diferente, mesma amarração (DIFFERENT_VALID).

## Interação com ARM-ROLE

### candidates antes/depois

`repair_arm_role_isolated_edges` percorre as MESMAS arestas isoladas com
prisma forçado (`_wall_has_forced_corner_prism` sobre `wall_bond_audits`
do ORIGINAL). NODE-FILL não toca em `_arm_role_isolated_edges`,
`CORNER_ROLE_CANDIDATE_BITS`, `_set_l_corner_role_bits` nem em
`_evaluate_corner_role_candidate`; só muda o preenchimento comum que o
`rebuild_fn` produz. Paredes com prisma forçado no ORIGINAL: idênticas
antes/depois (TGD 8: 4, 23, 54, 89, 90, 91, 92, 120; TP1 3: 20, 75, 91).

### accepted/rejected

| | ANTES | DEPOIS (B3) |
|---|---|---|
| TGD accepted | `23\|SAME_A` | `23\|SAME_A` |
| TGD rejected | 21 entradas / 7 arestas (4, 54, 89, 90, 91, 92, 120) | 21 / mesmas 7; UMA razão muda: `91\|SAME_B` `closure_regression` → `new_consecutive_compensators:128` (rejeitado nas duas) |
| TP1 accepted | — | — |
| TP1 rejected | 9 / 3 arestas (20, 75, 91), razões idênticas | 9 / idênticas |
| Piloto | no-op | no-op |

Em B1/B2 (sem o filtro de juntas fantasma) `23|SAME_A` deixava de ser
aceito porque o ORIGINAL já saía sem prisma forçado; em B3 o ORIGINAL
volta a ter o prisma (a troca fantasma era o que o eliminava) e o SAFE
REPAIR o resolve como antes. **A melhoria do PR #12 é preservada
literalmente** (mesmo candidato, mesmo pin, mesmo resultado final para a
parede).

### SAFE REPAIR

`ARM_ROLE_SAFE_REPAIR_ENABLED = True` inalterado; hard gates
(`closure` → `collision` → `forced prism in neighbor` → `consecutive
compensators` → `row coverage`) inalterados; nenhum candidato antes
rejeitado passa (T19); todo candidato aceito continua sem prisma forçado
no resultado (T18); `_no_new_collisions` continua verdadeiro (colisões
1043/14/0 idênticas). Testes ARM existentes: ver "Testes ARM".

### _arm_role_pinned

Nós com pin: TGD 2 → 2 (os mesmos, do candidato `23|SAME_A`), TP1 0 → 0,
piloto 0 → 0. `_coordinate_arm_role_nodes` e a persistência entre bandas
não foram tocadas; NODE-FILL lê `node_candidates_by_wall_end`, que já é
calculado POR BANDA a partir dos papéis coordenados — a lista deduzida
respeita o pin por construção.

## Relação com 10 rejected edges

### RELATED

Nenhuma no sentido causal: NODE-FILL não muda quais arestas são
candidatas, a ordem canônica dos bits, os gates nem o hard gate; nenhum
candidato antes rejeitado passa; nenhum antes aceito deixa de passar.

### INDEPENDENT

As 10 arestas (TGD 4, 54, 89, 90, 91, 92, 120; TP1 20, 75, 91) continuam
rejeitadas com as MESMAS razões, exceto `91|SAME_B` (TGD): o rebuild do
candidato com NODE-FILL cai num gate anterior/posterior diferente
(`closure_regression` → `new_consecutive_compensators:128`). É o mesmo
candidato inviável falhando em outro gate porque o preenchimento das
paredes vizinhas mudou — coincidência de qual gate reprova, não relação
causal com a junta NÓ|FILL. `W013` (wall_idx 91, 124 cm) tem prisma
forçado em 89,5 nas duas fiadas antes e depois: `[70..89 B19]|[90..124
B34/L_CORNER]` (A) × `[35..89 B54/X]|[90..109 B19]` (B) — junta de
CONTORNO × junta de CONTORNO, geometria fixa nas duas fiadas (o limite
genuíno já documentado em 30.6: "pier de exatamente 1 bloco entre nós"),
que NODE-FILL por construção não move (só troca juntas INTERNAS da A).

### INCONCLUSIVE

—

## Coverage

`COVERAGE_MISSING_ROW` / `ROW_MOSTLY_EMPTY` / `GAP_IN_ROW` /
`PARTIAL_WALL`: **delta zero** nos três projetos (TGD 258/112/1959/61,
TP1 0/18/327/6, piloto 0/8/16/0). A regressão intermediária de B1/B2
(`W075` +6) foi rastreada até a causa (junta fantasma pré-recorte) e
eliminada em B3 — não por filtro de validador, mas por não trocar o
layout naquela situação.

## Prism

| | TGD | TP1 | Piloto |
|---|---|---|---|
| PRISM_CONTINUOUS_JOINT | 444 → **336** (−108, −24 %) | 576 → **272** (−304, −53 %) | 0 → 0 |
| PRISM_JOINT_STACK | 27 → 20 | 33 → 17 | 0 → 0 |
| PRISM_STAGGER_BELOW_TARGET (nível 2) | 690 → 774 (+84) | 1140 → 1418 (+278) | 14 → 14 |
| FORBIDDEN_JOINT_ALIGNMENT same-band (CR-BLOCK-01) | 0 → 0 | 0 → 0 | 0 → 0 |
| FORBIDDEN_JOINT_ALIGNMENT cross-band | 6 → 6 | 18 → 20 | 0 → 0 |
| `alignment_conflicts` do motor | 397 → 331 | 592 → 449 | 8 → 8 |

`PRISM_STAGGER_BELOW_TARGET` sobe porque uma junta que antes COINCIDIA
(0 cm, nível 1) passa a desencontrar por 5–10 cm (nível 2, "por pouco"):
é a mesma junta trocando de classe para a classe menos grave, não uma
junta nova (o total nível 1 + nível 2 cai: TGD 1134 → 1110, TP1 1716 →
1690). Cross-band TP1 +2: `W036`/`W038` r4/5 e r11/12 (34,5 → 54,5, ver
"Limite conhecido") — o par de fiadas já coincidia antes.

Medição adicional (variante GATE, não integrada): com a coincidência
contra junta de nó separada, `alignment_conflicts` INTERNA×INTERNA é
**zero** nos três projetos — o gate histórico do `CR-BLOCK-01` continua
em zero; todo residual do gate da main envolve uma junta de contorno de
nó (na maioria contorno×contorno em T degradado, que o validador do
benchmark nem enxerga porque a peça de nó da parede vizinha não está nas
`rows` da parede).

## Junctions

`JUNCTION_NOT_ALTERNATING` 303/0/0 e `JUNCTION_MISSING_BINDING` 23/9/0:
**delta zero**. Fingerprint `junctions` idêntico nos três projetos (peças
de nó não são tocadas: NODE-FILL só troca layout de preenchimento).

## Openings

`OPENING_BLOCK_INSIDE_DOOR` 5/0/0, `OPENING_BLOCK_CROSSES_JAMB`
108/168/0, `OPENING_MISSING_LINTEL`/`COUNTER_LINTEL`/`SOLID_BELOW_SILL`:
**delta zero**; `door_void_violations` do motor 290/348/0 idênticos;
`jamb_exceptions` 172/44/4 idênticos; fingerprint `openings` idêntico.
Nenhum bloco em porta, nenhuma jamba cruzada, nenhuma peça de amarração
perdida (`placement_reason` de nó: idênticos; só `STANDARD_FILL` /
`OPENING_REPAIR_FILL` mudam de contagem). T15 cobre porta e janela nas
duas orientações + vão livre na convenção vertical do motor.

## Compensators

| | TGD | TP1 | Piloto |
|---|---|---|---|
| COMPENSATOR_CONSECUTIVE | 410 → 379 (−31) | 1469 → 1461 (−8) | 36 → 36 |
| COMPENSATOR_EXCESS_IN_RUN | 340 → 340 | 1088 → 1084 | 28 → 28 |
| COMPENSATOR_VERTICAL_STRIP | 59 → 56 | 188 → 188 | 18 → 18 |
| COMPENSATOR_AVOIDABLE (nível 2) | 35 → 37 (+2) | 84 → 86 (+2) | 0 |
| pares consecutivos (instrumento CR-BLOCK-01) | 255 → 235 | 898 → 894 | 28 → 28 |
| B39 / B34 / B54 / B19 / C09 / C04 | 4468→4417 / 2568→2633 / 571 / 810→800 / 1133→1114 / 625→656 | 7790→7706 / 1958→2049 / 881 / 1152→1142 / 2482→2475 / 876→965 | iguais |

Mudança física real: a Fiada A troca `B19+B39` por `B39+B19` (ou
`B34+B19`) junto ao nó e a busca da B, já existente, responde com outra
composição (`C04+B19+B34` em `W036`/`W038` — o "bypass de tier" de
`_pier_forced_bypass_layouts`, comportamento da main). Saldo:
`COMPENSATOR_CONSECUTIVE` cai; `COMPENSATOR_AVOIDABLE` (+2/+2) e `C04`
sobem porque a B agora precisa de uma composição alternativa onde antes
copiava a A. Nenhuma cadeia nova de 3+ compensadores
(`COMPENSATOR_EXCESS_IN_RUN` ≤ antes); em `W113` a cadeia de 3 já existia
e só foi reordenada. Gate ARM `_no_new_consecutive_compensators`
inalterado (T16 sintético: sequências ≤ antes).

## Collisions

`POSITION_OVERLAP` 29/18/0 e `collisions` do solver 1043/14/0: **delta
zero**, e o conjunto de ASSINATURAS geométricas (parede, peça, fiada,
extents) é idêntico (0 novas, 0 removidas) nos três projetos. Em B1 (lado
B) havia +3/rearranjo em pares de paredes SOBREPOSTAS (`W011∥W075`,
`W009∥W070`, eixos a 2,4 cm — artefato de extração pré-existente, 1043
colisões na main); eliminado ao restringir a metade simétrica ao lado A.

## Determinismo

- Repetição idêntica: B,B,A,B no mesmo processo e B em processo novo →
  fingerprint `walls_blocks` idêntico em TGD (`4d461b886b13`), TP1
  (`fe1b34274b5f`) e piloto (`c012bb211914`); A depois de B volta ao
  fingerprint de A (nenhum estado de módulo cruza execuções).
- Ordem de entrada / permutação de paredes: grade 2×2 sintética em 4
  ordens — a `main` produz 1–3 violações NÓ|FILL dependendo da ordem
  (medido: `[11..0]` → 1, `[3,7,0,…]` → 2, `[6,0,9,…]` → 3); com o fix,
  0 em todas (T6). A lista nova sai de `border ± J/2` e de
  `_merge_intervals_cm` — sem `wall_idx`, ordem de dict ou
  `GetEndPoint(0)`.
- Ordem de candidatos / da lista a evitar: `_pier_layout_avoiding_joints`
  devolve o mesmo layout para qualquer permutação da lista e para catálogo
  em ordem diferente (T5).
- Fingerprint `openings`/`junctions` estáveis em todos os estados.

## Performance

(preenchido abaixo — medição sequencial, mesmo processo, 2 repetições
por estado, sem carga concorrente)

| projeto | MAIN (s, 2 reps) | NODE-FILL (s, 2 reps) | média MAIN | média NODE-FILL | delta |
|---|---|---|---|---|---|
| TGD | 44.19 / 44.26 | 45.30 / 45.13 | 44.22 s | 45.22 s | +2.2 % |
| TP1 | 24.39 / 24.79 | 25.58 / 26.29 | 24.59 s | 25.93 s | +5.5 % |
| Piloto | 0.06 / 0.05 | 0.06 / 0.06 | 0.06 s | 0.06 s | +9.1 % |

Custo: por fiada, uma dedução O(nós da parede) e, só quando o layout
padrão da Fiada A colide, uma chamada extra a
`_pier_layout_avoiding_joints` (a mesma busca que a Fiada B já faz em
todo trecho). Sem micro-otimização; regressão ≤ 6 % no pior projeto
(TP1), dentro do ruído entre repetições do próprio MAIN (24,4–24,8 s).

## Implementação final

### arquivos

`nuvem/core/engine/wall_stepper.py` — **único arquivo de produção**
(+125 linhas, 0 removidas). Nenhum outro módulo de produção; nenhum
import de `nuvem/benchmark/` (G18: `split_extents_by_openings` é de
`core/engine/continuous_modulation.py`, já importado).

### funções

| símbolo | tipo | papel |
|---|---|---|
| `NODE_FILL_OPPOSITE_COURSE_ENABLED = True` | constante de módulo (mesmo padrão de `ARM_ROLE_SAFE_REPAIR_ENABLED`) | `False` reproduz bit a bit a main — usado pelos testes para provar o defeito e a natureza física da correção |
| `_wall_node_boundary_joints_cm(wall_idx, course, by_end, midspan)` | pura, nova | juntas NÓ\|FILL de uma fiada deduzidas só da geometria do nó (`border ± J/2`, meio de parede `t ∓ J/2`) |
| `_layout_joints_surviving_openings_cm(layout, seg_start, openings)` | pura, nova | juntas internas entre duas peças que `split_extents_by_openings` mantém — o mesmo critério do recorte, sem tolerância nova |
| `solve_wall_free_fill` (2 hunks) | | por fiada: `opposite_node_joints_cm` da fiada oposta; na Fiada A variante 0, se o layout padrão colide (só juntas sobreviventes), tenta `_pier_layout_avoiding_joints` e troca só com ESTRITAMENTE menos coincidência |

Sem heurística de proximidade, sem tolerância nova (reusa
`VERTICAL_JOINT_STAGGER_TOLERANCE_CM` via `_count_joint_coincidences_cm`
e `OPENING_OVERLAP_TOLERANCE_CM` via `split_extents_by_openings`), sem
special-case por projeto/`wall_idx`/coordenada (G26).

### diff

`git diff origin/main -- nuvem/core/engine/wall_stepper.py` (4 hunks:
`__all__`; helpers + constante depois de
`_pier_boundary_joint_positions_cm`; cálculo de `opposite_node_joints_cm`
depois de `boundaries.sort`; troca condicional depois do layout padrão
da Fiada A variante 0).

## Testes novos

`tests/test_block_node_fill_revalidation.py` — T1–T20 (28 casos com
parametrizações):

| teste | cobre | resultado |
|---|---|---|
| T1 / T1b | junta NÓ\|FILL da fiada oposta deduzida da geometria; igual à junta de contorno que `_pier_boundary_joint_positions_cm` publica | pass |
| T2 | ponta livre / abertura não geram junta de nó; L com ponta livre não muda de layout | pass |
| T3 / T3b | medidor independente acusa a violação real (sem o fix, ordens permutadas); gate `alignment_conflicts` do motor não é silenciado | pass |
| T4 | redução é física: mesmo medidor, sem o fix > 0, com o fix = 0 | pass |
| T5 | permutação da lista a evitar e do catálogo → mesmo layout | pass |
| T6 | 4 permutações de paredes → 0 violações | pass |
| T7 | duas execuções idênticas (assinatura de todas as peças) | pass |
| T8 / T9 | horizontal e vertical (célula fechada) — a Fiada A desencontra de TODAS as juntas de nó da B | pass |
| T10 / T11 / T12 | L, T, X isolados | pass |
| T13 / T14 | 150, 230, 350, 430, 590, 1030 cm (nó nas duas pontas) | pass |
| T15 | porta e janela (H e V) na grade 2×2 + célula fechada com porta em 13 fiadas: 0 violação e 0 bloco no vão (convenção vertical do motor) | pass |
| T16 | 355/363/447 cm (compensador forçado): 0 violação e sequências de compensador ≤ antes | pass |
| T17 | SAFE REPAIR ligado: invariante, determinismo, igualdade com SAFE REPAIR desligado quando nada é aceito | pass |
| T18 | corpus TGD+TP1: todo candidato aceito sem prisma forçado; parede antes reparável continua aceita ou sem prisma; colisões ≤ | pass |
| T19 | corpus: nenhum candidato antes rejeitado é aceito; razões reportadas | pass |
| T20 | caso real TP1: assinatura 34,5/`B` 16 → 4 (residual ⊆ antes, todos os 4 = cadeia forçada de compensadores) | pass |

`python3 -m pytest tests/test_block_node_fill_revalidation.py -q` → **28 passed** (143 s, inclui 4 resoluções de corpus).

## Testes ARM

`tests/test_block_arm_role_invariance.py`,
`tests/test_block_arm_role_prism_stagger.py`,
`tests/test_block_arm_role_candidate_safety_contract.py`:

`python3 -m pytest tests/test_block_arm_role_invariance.py tests/test_block_arm_role_prism_stagger.py tests/test_block_arm_role_candidate_safety_contract.py -q` → **39 passed** (340 s). Nenhum ajuste nos testes ARM.

## Suíte completa

`python3 -m pytest tests -q` (código final, arquivo de testes final):

| | ANTES (main, mesma sessão) | DEPOIS |
|---|---|---|
| passed | 565 | 593 (+28 = esta CR) |
| failed | 1 | 1 |
| falha | `tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]` — `JUNCTION_MISSING_BINDING` 8→9 (P3 — BENCHMARK_ARTIFACT, seção 32 das regras) | **a mesma**, mesma mensagem (`JUNCTION_MISSING_BINDING` before 8 / after 9) |

Nenhuma falha nova; nenhum baseline regravado; nenhum teste alterado ou
desabilitado. Tempo: 599 s → 763 s (os 28 testes novos incluem 4
resoluções do corpus real).

## Baseline diff

`git status`: nenhum arquivo em `nuvem/benchmark/projects/**` alterado
(`baseline.json` intacto nos 3 projetos). Toda medição com
`write_files=False` / `evaluate_project` em memória. **diff = ZERO.**

## Reference diff

`reference.json` / `reference_score.json` intactos. **diff = ZERO.**

## Métricas completas

### TGD (`torre_easy_lo_r00_tgd`)

| métrica | ANTES (main) | DEPOIS (NODE-FILL) | DELTA |
|---|---|---|---|
| walls | 167 | 167 | +0 |
| blocks | 10672 | 10686 | +14 |
| COVERAGE_MISSING_ROW | 258 | 258 | +0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 112 | 112 | +0 |
| COVERAGE_GAP_IN_ROW | 1959 | 1959 | +0 |
| COVERAGE_PARTIAL_WALL | 61 | 61 | +0 |
| PRISM_CONTINUOUS_JOINT | 444 | 336 | -108 |
| PRISM_JOINT_STACK | 27 | 20 | -7 |
| PRISM_STAGGER_BELOW_TARGET | 690 | 774 | +84 |
| JUNCTION_NOT_ALTERNATING | 303 | 303 | +0 |
| JUNCTION_MISSING_BINDING | 23 | 23 | +0 |
| OPENING_BLOCK_INSIDE_DOOR | 5 | 5 | +0 |
| OPENING_BLOCK_CROSSES_JAMB | 108 | 108 | +0 |
| COMPENSATOR_CONSECUTIVE | 410 | 379 | -31 |
| COMPENSATOR_EXCESS_IN_RUN | 340 | 340 | +0 |
| COMPENSATOR_VERTICAL_STRIP | 59 | 56 | -3 |
| COMPENSATOR_AVOIDABLE | 35 | 37 | +2 |
| POSITION_OVERLAP | 29 | 29 | +0 |
| FORBIDDEN_JOINT_ALIGNMENT (same-band) | 0 | 0 | +0 |
| FORBIDDEN_JOINT_ALIGNMENT (cross-band) | 6 | 6 | +0 |
| compensadores consecutivos (instrumento CR-BLOCK-01) | 255 | 235 | -20 |
| collisions (solver) | 1043 | 1043 | +0 |
| collisions (assinaturas distintas) | 1043 | 1043 | +0 |
| alignment_conflicts (gate do motor) | 397 | 331 | -66 |
| non_modular | 3039 | 3039 | +0 |
| ARM candidates accepted | 1 | 1 | +0 |
| ARM candidates rejected | 21 | 21 | +0 |
| nós com _arm_role_pinned | 2 | 2 | +0 |
| runtime solver (s, medição do lab) | 43.537 | 44.643 | +1.106 |

Composição por família (candidates do solver):

| peça | ANTES | DEPOIS | DELTA |
|---|---|---|---|
| B39 | 4468 | 4417 | -51 |
| B34 | 2568 | 2633 | +65 |
| B54 | 571 | 571 | +0 |
| B19 | 810 | 800 | -10 |
| C09 | 1133 | 1114 | -19 |
| C04 | 625 | 656 | +31 |

placement_reason: OPENING_REPAIR_FILL 557→552, STANDARD_FILL 6850→6871

fingerprint (walls_blocks): `583ae72833883a5d` → `4d461b886b132ea0`; openings/junctions idênticos: True/True

ARM accepted ANTES: ['23|SAME_A'] | DEPOIS: ['23|SAME_A']

ARM rejected: 21 → 21; só ANTES: ['91|SAME_B|closure_regression']; só DEPOIS: ['91|SAME_B|new_consecutive_compensators:128']

### TP1 (`torre_easy_lo_r00_tp1`)

| métrica | ANTES (main) | DEPOIS (NODE-FILL) | DELTA |
|---|---|---|---|
| walls | 96 | 96 | +0 |
| blocks | 18368 | 18451 | +83 |
| COVERAGE_MISSING_ROW | 0 | 0 | +0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 18 | 18 | +0 |
| COVERAGE_GAP_IN_ROW | 327 | 327 | +0 |
| COVERAGE_PARTIAL_WALL | 6 | 6 | +0 |
| PRISM_CONTINUOUS_JOINT | 576 | 272 | -304 |
| PRISM_JOINT_STACK | 33 | 17 | -16 |
| PRISM_STAGGER_BELOW_TARGET | 1140 | 1418 | +278 |
| JUNCTION_NOT_ALTERNATING | 0 | 0 | +0 |
| JUNCTION_MISSING_BINDING | 9 | 9 | +0 |
| OPENING_BLOCK_INSIDE_DOOR | 0 | 0 | +0 |
| OPENING_BLOCK_CROSSES_JAMB | 168 | 168 | +0 |
| COMPENSATOR_CONSECUTIVE | 1469 | 1461 | -8 |
| COMPENSATOR_EXCESS_IN_RUN | 1088 | 1084 | -4 |
| COMPENSATOR_VERTICAL_STRIP | 188 | 188 | +0 |
| COMPENSATOR_AVOIDABLE | 84 | 86 | +2 |
| POSITION_OVERLAP | 18 | 18 | +0 |
| FORBIDDEN_JOINT_ALIGNMENT (same-band) | 0 | 0 | +0 |
| FORBIDDEN_JOINT_ALIGNMENT (cross-band) | 18 | 20 | +2 |
| compensadores consecutivos (instrumento CR-BLOCK-01) | 898 | 894 | -4 |
| collisions (solver) | 14 | 14 | +0 |
| collisions (assinaturas distintas) | 14 | 14 | +0 |
| alignment_conflicts (gate do motor) | 592 | 449 | -143 |
| non_modular | 274 | 274 | +0 |
| ARM candidates accepted | 0 | 0 | +0 |
| ARM candidates rejected | 9 | 9 | +0 |
| nós com _arm_role_pinned | 0 | 0 | +0 |
| runtime solver (s, medição do lab) | 24.606 | 25.877 | +1.271 |

Composição por família (candidates do solver):

| peça | ANTES | DEPOIS | DELTA |
|---|---|---|---|
| B39 | 7790 | 7706 | -84 |
| B34 | 1958 | 2049 | +91 |
| B54 | 881 | 881 | +0 |
| B19 | 1152 | 1142 | -10 |
| C09 | 2482 | 2475 | -7 |
| C04 | 876 | 965 | +89 |

placement_reason: STANDARD_FILL 11652→11731

fingerprint (walls_blocks): `4236d27b4b6029a0` → `fe1b34274b5fc392`; openings/junctions idênticos: True/True

ARM accepted ANTES: [] | DEPOIS: []

ARM rejected: 9 → 9; só ANTES: []; só DEPOIS: []

### Piloto (`piloto_sintetico_2x2`)

| métrica | ANTES (main) | DEPOIS (NODE-FILL) | DELTA |
|---|---|---|---|
| walls | 12 | 12 | +0 |
| blocks | 772 | 772 | +0 |
| COVERAGE_MISSING_ROW | 0 | 0 | +0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 8 | 8 | +0 |
| COVERAGE_GAP_IN_ROW | 16 | 16 | +0 |
| COVERAGE_PARTIAL_WALL | 0 | 0 | +0 |
| PRISM_CONTINUOUS_JOINT | 0 | 0 | +0 |
| PRISM_JOINT_STACK | 0 | 0 | +0 |
| PRISM_STAGGER_BELOW_TARGET | 14 | 14 | +0 |
| JUNCTION_NOT_ALTERNATING | 0 | 0 | +0 |
| JUNCTION_MISSING_BINDING | 0 | 0 | +0 |
| OPENING_BLOCK_INSIDE_DOOR | 0 | 0 | +0 |
| OPENING_BLOCK_CROSSES_JAMB | 0 | 0 | +0 |
| COMPENSATOR_CONSECUTIVE | 36 | 36 | +0 |
| COMPENSATOR_EXCESS_IN_RUN | 28 | 28 | +0 |
| COMPENSATOR_VERTICAL_STRIP | 18 | 18 | +0 |
| COMPENSATOR_AVOIDABLE | 0 | 0 | +0 |
| POSITION_OVERLAP | 0 | 0 | +0 |
| FORBIDDEN_JOINT_ALIGNMENT (same-band) | 0 | 0 | +0 |
| FORBIDDEN_JOINT_ALIGNMENT (cross-band) | 0 | 0 | +0 |
| compensadores consecutivos (instrumento CR-BLOCK-01) | 28 | 28 | +0 |
| collisions (solver) | 0 | 0 | +0 |
| collisions (assinaturas distintas) | 0 | 0 | +0 |
| alignment_conflicts (gate do motor) | 8 | 8 | +0 |
| non_modular | 32 | 32 | +0 |
| ARM candidates accepted | 0 | 0 | +0 |
| ARM candidates rejected | 0 | 0 | +0 |
| nós com _arm_role_pinned | 0 | 0 | +0 |
| runtime solver (s, medição do lab) | 0.072 | 0.059 | -0.013 |

Composição por família (candidates do solver):

| peça | ANTES | DEPOIS | DELTA |
|---|---|---|---|
| B39 | 220 | 220 | +0 |
| B34 | 82 | 82 | +0 |
| B54 | 0 | 0 | +0 |
| B19 | 26 | 26 | +0 |
| C09 | 32 | 32 | +0 |
| C04 | 26 | 26 | +0 |

placement_reason: 

fingerprint (walls_blocks): `a60a95cb00e0f9d5` → `c012bb211914f325`; openings/junctions idênticos: True/True

ARM accepted ANTES: [] | DEPOIS: []

ARM rejected: 0 → 0; só ANTES: []; só DEPOIS: []

## Gates G1-G26

| gate | status | evidência |
|---|---|---|
| G1 base exata | PASS | `MEASUREMENT_BASE` = `68a62693…`; produção equivalente confirmada contra `CURRENT_MAIN_AT_PREMERGE` = `789f4422…` (ver "Proveniência pós-medição") |
| G2 branch nova da main | PASS | `git log origin/main..HEAD` só commits desta CR |
| G3 fix histórico entendido antes de portar | PASS | "diff de produção histórico" (inventário por função/condição) |
| G4 STATE_A medido | PASS | tabela |
| G5 STATE_B medido | PASS | B1…B4, mesmo script, mesmo processo (A' ≡ A) |
| G6 primeira divergência provada | PASS | cadeia W036 TP1 (e W007/W011 TGD) |
| G7 reduções classificadas | PASS | N1 = 108 + 308; N2 = 0 (variante GATE medida e descartada); N3 = 0 |
| G8 N3 = zero | PASS | nenhum validador tocado, gate do motor preservado, medidor independente |
| G9 interação ARM medida | PASS | accepted/rejected/pinned por estado |
| G10 SAFE REPAIR correto | PASS | mesmo candidato aceito, mesmos gates, colisões idênticas, T17–T19 |
| G11 accepted/rejected compreendidos | PASS | seção "Relação com 10 rejected edges" |
| G12 coverage | PASS | delta zero (B1/B2 tinham +6, eliminado em B3 pela causa) |
| G13 collisions | PASS | delta zero, assinaturas idênticas |
| G14 openings | PASS | delta zero, fingerprint `openings` idêntico |
| G15 compensators | PASS | CONSECUTIVE −31/−8, EXCESS 0/−4; AVOIDABLE +2/+2 (nível 2, explicado) |
| G16 human/reference | PASS | 0 CONFLICTS; 226 CONFIRMED / 47 CONSISTENT |
| G17 escopo | PASS | só `wall_stepper.py` |
| G18 benchmark em runtime | PASS | nenhum import de `nuvem/benchmark` |
| G19 testes NODE-FILL | PASS | 28 passed |
| G20 testes ARM | PASS | 39 passed |
| G21 suíte sem nova regressão | PASS | 1 failed (a conhecida, idêntica) / 593 passed |
| G22 determinismo | PASS | repetição/permutação/ordem de lista |
| G23 performance | PASS | TGD +2,3 %, TP1 +5,5 %, piloto 0 — explicado (uma busca extra só quando a Fiada A colide) |
| G24 baseline diff zero | PASS | `git status` |
| G25 reference diff zero | PASS | `git status` |
| G26 sem special-case | PASS | nenhum `if project`/`wall_idx`/coordenada |

## Veredito

**APROVADO PARA INTEGRAÇÃO**

- Hipótese provada na forma correta (junta NÓ|FILL invisível para a
  busca da fiada oposta; a `main` já tinha o sentido A→B, faltava B→A).
- Redução de prisma é FÍSICA (N1), medida por instrumento independente
  do benchmark, confirmada pelo Reference Corpus humano (0 conflitos).
- N3 = 0; nenhum validador, baseline ou reference tocado.
- Zero regressão hard: cobertura, aberturas, colisões, junções — delta
  zero; ARM accepted/rejected e SAFE REPAIR idênticos; determinismo
  provado; performance ≤ +6 %.
- Escopo: só `wall_stepper.py`; sem special-case; sem import de benchmark.
- Limites documentados (33.5): reparo local junto ao vão e cadeias
  forçadas de compensador — residuais que já existiam, não criados aqui.

**NÃO MERGEAR.** PR em draft; sem monitoramento automático.
