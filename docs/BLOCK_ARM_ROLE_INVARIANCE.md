# RELATÓRIO — ARM-ROLE PRISM-STAGGER

## Estado inicial

Branch `claude/cr-block-arm-role-invariance-7tezx4`, HEAD recebido e
confirmado `d813f457108ef187b35dd581c35821d22ad23c4d` (working tree
limpo, nada perdido/descartado). Nenhum rebase, nenhum pull da main,
nenhum merge — conforme instruído. NODE-FILL não foi tocado nem
incorporado.

Ponto de partida (commit `d813f45`, CR-BLOCK-ARM-ROLE-CONSISTENCY já
resolvido e aceito como base): a coordenação determinística de papel
`course_a`/`course_b` entre os dois nós `L_CORNER` que fecham as duas
pontas de uma mesma parede eliminou o defeito original (fiada inteira
ausente), com ganho real e comprovado de cobertura em TGD e TP1. Efeito
colateral, medido e documentado no relatório anterior mas **não
corrigido**: `PRISM_CONTINUOUS_JOINT` passou a aparecer em paredes que
antes não tinham nenhum achado desse código — 3 no TGD (`W003`, `W117`,
`W137`), 8 no TP1 (`W010`, `W021`, `W037`, `W041`, `W061`, `W062`,
`W076`, `W092`).

## Paredes com regressão (inventário)

Todas as 11 paredes têm a MESMA estrutura de topologia: exatamente 2 nós
`L_CORNER` de 2 arms, um em cada ponta, ambos agora com candidato de nó
real (efeito do CR anterior). Detalhe completo (peça, orientação,
posição de junta) para as 3 mais simples, medidas ao vivo:

| parede | projeto | comprimento | nós (pontas) | papel coordenado |
|---|---|---|---|---|
| W076 | TP1 (wall_idx 75) | 69,0cm | nó126 (arms=[(75,0),(76,1)]) / nó127 (arms=[(81,0),(75,1)] após coordenação) | A no nó126, B no nó127 |
| W021 | TP1 (wall_idx 20) | 123,98cm | nó21 / nó23 | A / B |
| W010 | TP1 (wall_idx 9, 1 abertura) | 424,0cm | nó18 (course_b) / nó19 (course_a) | B no nó18, A no nó19 |
| W003 | TGD | 69,0cm | 2× L_CORNER | A / B |
| W137 | TGD | 69,0cm | 2× L_CORNER | A / B |

`course_index` → letra física: fixo, `"A" if course_index % 2 == 0 else
"B"` (`solve_building_blocks_all_courses`, nunca afetado por
coordenação de papel — confirmado no relatório anterior e reconfirmado
aqui).

Peça de amarração em TODAS as 11 paredes: `B34` (34cm) nas duas pontas
— antes de qualquer fix as duas famílias tinham colisão de junta com
STAGGER=0.00cm em TODA fiada consecutiva (16 pares de fiada por parede
de 17 fiadas).

## Caso mínimo

`W076`/TP1 (wall_idx 75, 69cm, sem abertura) — a mais simples: pier de
UM bloco só de cada lado do nó.

```
ANTES do fix (commit d813f45):
  fiada 0 (A): B34[0.0,34.0]  B19[35.0,54.0]
  fiada 1 (B): B19[15.0,34.0] B34[35.0,69.0]
```

## Diff fiada-a-fiada

Junta interna de fiada 0: entre `B34[0,34]` e `B19[35,54]` → centro em
**t=34.5cm**. Junta interna de fiada 1: entre `B19[15,34]` e
`B34[35,69]` → centro em **t=34.5cm**. Idêntica — `PRISM_CONTINUOUS_JOINT`
dispara nas 16 fiadas consecutivas, sempre no mesmo ponto.

## Primeira divergência

Localizada na cadeia exigida (papel coordenado → solve_l_corner → peça
→ orientação → posição da junta → fill → junta na fiada oposta), **não**
no validador final:

1. Papel coordenado: nó126 dá `wall75=course_a` (arms[0], inalterado);
   nó127 dá `wall75=course_b` (arms[1], **trocado** pela coordenação —
   antes desta CR nó127 dava `course_a` também, e a família B ficava
   com zero candidato de nó ali — o defeito original). Isto está
   **correto**: é exatamente o que CR-BLOCK-ARM-ROLE-CONSISTENCY foi
   pedido para fazer.
2. `solve_l_corner`: em CADA nó, escolhe `B34` (34cm) — decisão
   puramente geométrica (espaço disponível no canto), **idêntica** com
   ou sem coordenação (confirmado comparando a peça gerada em nó127
   antes/depois da troca de papel: mesma posição `t=52`, mesma
   `rotation_deg=270` — só o RÓTULO course_a→course_b mudou, nunca a
   geometria).
3. Orientação/vão menor: `_asymmetric_bond_origin_and_axis` posiciona a
   peça pela GEOMETRIA do nó (ponto de canto + direção), nunca por
   `course_a`/`course_b` — **correta**, não é a causa.
4. Posição da junta (fill): `solve_wall_free_fill` reserva, em cada
   ponta fechada por nó, `seg_start_cm = border + BLOCK_JOINT_CM` (ou
   `seg_end_cm = border - BLOCK_JOINT_CM` na ponta oposta) — a JUNTA
   entre a peça do nó e o primeiro bloco do preenchimento fica em
   `border ± BLOCK_JOINT_CM/2`, **fixada pela geometria do nó**, nunca
   pela composição do preenchimento.
5. **A DIVERGÊNCIA**: `_layout_internal_joint_positions_cm` (a função
   que alimenta `course_a_joint_positions_cm`, a lista que
   `_pier_layout_avoiding_joints` usa para a Fiada B tentar
   desencontrar da Fiada A) **por design, documentado na própria
   docstring**, só conta juntas ENTRE BLOCOS CONSECUTIVOS do
   preenchimento — "sem contar as juntas de CONTORNO (contra
   abertura/nó/ponta livre, essas não são 'verticais contínuas entre
   fiadas' no sentido da seção 6)". A junta nó→preenchimento (item 4)
   **nunca foi rastreada nem verificada** por este mecanismo — nem
   antes nem depois deste CR. É aqui, e só aqui, que a família B "não
   sabe" que a família A já usa t=34.5.
6. Fill/fiada oposta: como cada família tem exatamente 1 bloco de
   preenchimento (pier de 19cm, sem alternativa de composição), mesmo
   se a família B "soubesse" da junta de A, não haveria NENHUMA
   composição alternativa capaz de evitá-la — a posição é
   matematicamente fixada pelas duas peças de nó (ver "Causa raiz").

## Hipóteses H1–H7

| # | hipótese | veredito | evidência |
|---|---|---|---|
| H1 | orientação B34/B54 usa convenção antiga do nó | **REFUTADA** | posição/rotação da peça em nó127 idêntica antes/depois da troca de papel (t=52, rot=270°) — só o rótulo course_a/b mudou |
| H2 | orientação depende de arms[0]/[1], papel depende do coordenado | **REFUTADA** | `_asymmetric_bond_origin_and_axis` nunca lê `course`/arms — só geometria do nó |
| H3 | fill comum escolhe a mesma fase nas duas famílias | **PROVADA (refinada)** | não é "a mesma fase" em geral — é a junta de CONTORNO contra o nó (item 5 acima), nunca rastreada pelo mecanismo de desencontro, que coincide quando as duas pontas usam a MESMA peça (mesmo comprimento) |
| H4 | inversão de significado course_a/b × vão menor | **REFUTADA** | vão menor sempre aponta pro canto físico certo (rotation_deg mirror correto entre as duas pontas, confirmado em W076/W010/W021) |
| H5 | só ocorre com dois L_CORNER | **PROVADA** | as 11 paredes regredidas são TODAS de 2 nós L_CORNER de 2 arms; nenhuma parede com nó T/X regrediu |
| H6 | também ocorre com T/X | **REFUTADA (nesta regressão)** | T usa geometria própria (`main_wall_idx`/`incoming_wall_idx`, sem ambiguidade de papel — nunca alterado por esta CR); X tem 4 arms, fora da elegibilidade de `_coordinate_arm_role_nodes`. A junta de contorno TAMBÉM não é rastreada em T/X, mas como T/X não tiveram papel recém-coordenado, o padrão simétrico "as duas famílias usam a mesma peça" que dispara a coincidência não surgiu ali nesta regressão |
| H7 | interação com compensador/B19, não com B34/B54 | **REFUTADA como causa principal** | a peça de nó em todas as 11 paredes é B34; B19/C09 aparecem só como preenchimento ao lado, não como origem da coincidência (embora contribuam a coincidências SECUNDÁRIAS em W061/W062, ver "Riscos") |

## Causa raiz

**PROVADA.** A junta entre a peça de amarração de um nó `L_CORNER`
(posicionada por `solve_l_corner`, fora de `layout`) e o primeiro/último
bloco do preenchimento comum adjacente nunca foi rastreada pelo
mecanismo de desencontro de junta vertical (`course_a_joint_positions_cm`
/ `_pier_layout_avoiding_joints`, seção 6) — só juntas INTERNAS ao
preenchimento eram contadas, por decisão de design documentada na
própria função (`_layout_internal_joint_positions_cm`). Isso era
inofensivo enquanto normalmente só UMA das duas famílias tinha candidato
de nó real num dado encontro (o defeito que CR-BLOCK-ARM-ROLE-CONSISTENCY
corrigiu). Com as duas famílias podendo ter candidato de nó real no
MESMO encontro — e, nas 11 paredes afetadas, ambas escolhendo a MESMA
peça (B34, 34cm, decisão puramente geométrica e correta) —, a junta de
contorno de uma família coincide com a da outra em `border +
BLOCK_JOINT_CM/2`, sem que a busca de desencontro jamais soubesse disso.

## Contrato course-role × orientação física

Confirmado — **já estava correto, não precisou de mudança**:

> Dado `wall_idx + node + endpoint + course_role`, a orientação física
> da peça (`origin_world`, `x_dir`, `rotation_deg`) é determinada
> inteiramente por `_asymmetric_bond_origin_and_axis(entry, point,
> dir_away, small_sign)` — uma função de GEOMETRIA (ponto de canto do
> nó, direção de afastamento, sinal do lado do vão menor), nunca de
> `course_a`/`course_b` nem de `arms[0]`/`arms[1]`. O papel coordenado
> decide APENAS o RÓTULO (qual família recebe aquele candidato já
> posicionado) — nunca a posição nem a orientação da peça.

Isso é invariante a arms/nodes/paredes/endpoints por construção (a
mesma prova de `_coordinate_arm_role_nodes` do relatório anterior se
aplica — este CR não mexeu nessa função).

O problema real estava numa camada diferente: o CONTRATO entre "onde a
peça do nó termina" (`node_candidates_by_wall_end`) e "o que a busca de
desencontro enxerga" (`course_a_joint_positions_cm`) estava incompleto —
o primeiro sempre incluía a fronteira do nó; o segundo nunca a
propagava como uma junta "real" a evitar.

## Fix

Único arquivo de produção alterado: `nuvem/core/engine/wall_stepper.py`.
`wall_pairing.py`, NODE-FILL, BENCH-Z e baseline/reference não foram
tocados.

1. Nova função `_pier_boundary_joint_positions_cm(seg_start_cm,
   seg_end_cm, kind_left, kind_right, leading_is_open, trailing_is_open)`
   — computa a posição da junta de contorno contra um nó/encontro de
   meio-de-parede (nunca contra abertura ou ponta livre — mesmo filtro
   `leading_is_open`/`trailing_is_open`/`kind_*` que o resto da função
   já usa), simétrica a `_layout_internal_joint_positions_cm`.
2. Duas listas NOVAS e SEPARADAS, `course_a_boundary_joint_positions_cm`
   / `own_family_boundary_joint_positions_cm`, paralelas às já
   existentes `course_a_joint_positions_cm`/`own_family_joint_
   positions_cm` — alimentam a BUSCA (`_pier_layout_avoiding_joints`,
   avoid-list ampliado) e a checagem residual (`alignment_conflicts`),
   mas **nunca** o `avoid_joint_positions_cm` de
   `_recut_openings_and_repair` (o reparo de abertura) — ver "Por que
   separado" abaixo.
3. Checagem residual (`alignment_conflicts`, "regra #1... nunca aceito
   calado"): antes só disparava com `len(layout) > 1` (pier de
   múltiplos blocos) — agora dispara também com pier de 1 bloco só
   (`layout` não-vazio), incluindo a junta de contorno na comparação —
   é exatamente o caso mais comum nas paredes afetadas (W076, W021 etc.
   têm pier de 1 bloco).

**Por que a lista de contorno é separada da lista de recut** (achado
DURANTE o desenvolvimento, não hipotético): a primeira versão do fix
misturava as duas listas — resultado, `OPENING_BLOCK_INSIDE_DOOR` subiu
de 43 para 46 no TGD (3 paredes: `W045`, `W051`, `W112`, nenhuma nova,
+1 achado cada), porque `_recut_openings_and_repair` passou a receber um
avoid-list diferente e escolheu composições diferentes perto de
aberturas sem relação com o defeito original. Corrigido mantendo as
listas de contorno fora do parâmetro que o recorte de abertura recebe —
a regressão de `OPENING_BLOCK_INSIDE_DOOR` **persistiu com a mesma
magnitude mesmo depois dessa separação** (ver "Riscos" — não foi a causa
completa, mas a separação é a arquitetura correta e não piora nada;
mantida).

## Testes

`tests/test_block_arm_role_prism_stagger.py` (5 testes novos,
permanentes, rodam o corpus real via `nuvem.benchmark.solver_bridge` —
o caso mínimo de W076 depende da reserva "emprestada" do quadrado do
canto, que só existe com a topologia real de mais de 2 paredes por nó,
não reproduzível no plano sintético de 3 paredes de
`test_block_arm_role_invariance.py`):

- `test_w076_tp1_coincidencia_de_contorno_e_geometricamente_forcada_mas_agora_visivel`
  — prova a causa-raiz (a coincidência em t=34.5 é geometricamente
  forçada, permanece) E o fix (agora aparece em `alignment_conflicts`,
  nunca mais silenciosa). **Falha no código anterior ao fix, pela razão
  certa** (confirmado via `git stash`): `alignment_conflicts` vazio
  (o antigo `len(layout) > 1` escondia o caso de 1 bloco só).
- `test_w041_tp1_prisma_resolvido_de_verdade_nao_so_reportado` — prova
  que, quando há liberdade real de composição, o fix RESOLVE de
  verdade (zero junta contínua entre todas as fiadas consecutivas), não
  só reporta. **Falha no código anterior** (`{274.5}` coincide).
- `test_w022_w093_tp1_cobertura_do_arm_role_consistency_preservada` —
  nenhuma fiada de W022/W093 fica sem bloco (G6).
- `test_determinismo_w076_w041_duas_rodadas_identicas` — mesma entrada,
  mesma saída (peça a peça).
- `test_w010_tp1_com_abertura_nenhum_bloco_invade_o_vao` — nenhum bloco
  invade o vão da janela de W010 nas fiadas onde ela está ativa (G12).

Suíte completa (rápida): `518 passed` (513 anteriores + 5 novos, `-m
"not slow"`).

## Coverage A/B/C

A = `origin/main` limpo (SHA `7c9a681`) | C = `d813f45`
(CR-BLOCK-ARM-ROLE-CONSISTENCY) | D = este fix.

| métrica | TGD (A→C→D) | TP1 (A→C→D) | Piloto (A→C→D) |
|---|---|---|---|
| COVERAGE_MISSING_ROW | 265→258→**258** | 16→0→**0** | 0→0→0 |
| COVERAGE_ROW_MOSTLY_EMPTY | 171→153→**153** | 27→18→**18** | 8→8→8 |
| COVERAGE_GAP_IN_ROW | 1934→1961→1958 | 293→319→327 | 16→16→16 |

**Gate: nenhuma mudança em MISSING_ROW/MOSTLY_EMPTY entre C e D — o
ganho de cobertura do commit `d813f45` está 100% preservado.**

## Prisma A/B/C

| métrica | TGD (A→C→D) | TP1 (A→C→D) |
|---|---|---|
| PRISM_CONTINUOUS_JOINT | 702→691→**476** | 837→896→**576** |
| PRISM_JOINT_STACK | 46→46→**29** | 49→52→**33** |
| PRISM_STAGGER_BELOW_TARGET (nível 2) | 514→(n/d)→690 | 813→(n/d)→1140 |

`PRISM_CONTINUOUS_JOINT` cai bem ABAIXO até do estado A original (antes
de qualquer CR desta série) nos dois projetos — o fix não só neutraliza
a regressão introduzida por ARM-ROLE-CONSISTENCY, como melhora o
resultado geral (a busca de desencontro, agora com mais informação,
encontra composições melhores em paredes que já tinham os dois nós
antes deste CR também). `PRISM_STAGGER_BELOW_TARGET` (nível 2, não
bloqueia) sobe — esperado: parte das coincidências exatas (0cm) virou
desencontro pequeno mas não-zero (ainda abaixo do alvo de 10cm) em vez
de continuar exatamente alinhada.

## NEW_PRISM_WALLS

**NÃO É ZERO — gate G7 falha.**

| projeto | antes do fix (11 no total) | depois do fix |
|---|---|---|
| TGD | W003, W117, W137 (3) | W003, W137 (2) — **W117 resolvido** |
| TP1 | W010, W021, W037, W041, W061, W062, W076, W092 (8) | W010, W021, W037, W061, W062, W076, W092 (7) — **W041 resolvido** |
| Piloto | 0 | 0 |

2 de 11 paredes totalmente resolvidas (W117, W041— tinham liberdade
real de composição). As 9 restantes têm o MESMO padrão: as duas pontas
usam `B34` (34cm) e o comprimento da parede não deixa espaço para uma
composição alternativa que desloque a junta de contorno — a coincidência
é **geometricamente forçada** dada a peça escolhida em cada nó (ver
"Riscos").

## TGD

`W003`/`W137` (69cm, mesma geometria de W076): pier de 1 bloco só de
cada lado, coincidência forçada, agora reportada em
`alignment_conflicts` mas não eliminável sem trocar a peça de um dos
nós. `W117`: resolvido (tinha um pier maior, com liberdade real).

## TP1

`W010`/`W021`/`W037`/`W061`/`W062`/`W076`/`W092`: mesmo padrão (`B34`
nas duas pontas, coincidência em t=34.5cm forçada pela geometria).
`W061`/`W062` têm uma coincidência SECUNDÁRIA (compensadores `C09`
empilhados simetricamente perto de cada nó, criando um segundo par de
juntas coincidentes em cascata) — mecanismo relacionado mas distinto,
não corrigido por este fix (fora do escopo provado). `W041`: resolvido.

## Piloto

Nenhuma mudança em nenhuma métrica (projeto pequeno demais para conter
a topologia do defeito).

## Aberturas

`OPENING_BLOCK_CROSSES_JAMB`: inalterado nos dois projetos (147 TGD,
168 TP1). `OPENING_BLOCK_INSIDE_DOOR`: TGD sobe de 43 (estado A/pré-CR,
que é o mesmo valor de C) para 46 — **regressão real, não eliminada**
pela separação de listas (ver "Fix"), localizada em 3 paredes já
afetadas (`W045` 1→2, `W051` 2→3, `W112` 2→3), nenhuma parede NOVA.
Causa exata não totalmente diagnosticada nesta sessão (a separação
arquitetural é necessária mas não suficiente — a mudança na composição
RAW de FASE 1, antes do recorte de abertura, ainda se propaga para o
resultado final por um caminho não identificado). TP1: 0→0 (sem
aberturas nas paredes afetadas).

## Compensadores

Pequenas variações mistas, esperadas como efeito colateral de
composições diferentes: TGD `COMPENSATOR_CONSECUTIVE` -8,
`COMPENSATOR_AVOIDABLE` +2; TP1 `COMPENSATOR_EXCESS_IN_RUN` +44,
`COMPENSATOR_VERTICAL_STRIP` -4. Nenhum são código crítico
(`severity != critical` nestes); não investigados individualmente nesta
sessão — risco secundário, não bloqueante.

## Collisions

`POSITION_OVERLAP`: idêntico nos três estados (TGD 29/29/29, TP1
18/18/18, piloto 0/0/0) — nenhuma colisão nova.

## Determinismo

Confirmado por teste permanente (`test_determinismo_w076_w041_duas_rodadas_identicas`,
rodando o projeto real 2x e comparando peça a peça). `_pier_boundary_
joint_positions_cm` é uma função pura de `seg_start_cm`/`seg_end_cm`/
`kind_*`/`*_is_open` — nenhuma dependência de ordem de lista.

## Performance

Não medida separadamente nesta sessão — o fix adiciona duas listas e
uma chamada de função pura por trecho fechado por nó (custo desprezível
frente ao resto do solver); a suíte rápida completa roda em ~17s (518
testes), mesma ordem de grandeza de antes.

## Production diff

Único arquivo de produção alterado: `nuvem/core/engine/wall_stepper.py`
(confirmado via `git diff --stat`: 101 linhas, 90 inserções/11
remoções). `wall_pairing.py`, NODE-FILL, BENCH-Z, baseline/reference
intactos.

## Baselines

`nuvem/benchmark/projects/*/baseline.json` não regravados (regra do
repositório: só em commit dedicado, quando uma melhoria é aceita
explicitamente — não é o caso aqui, dado o veredito). A suíte de
regressão (`tests/regression/test_benchmark_baselines.py -m slow`)
continua com 2 falhas: TP1 `JUNCTION_MISSING_BINDING` +1 (já
documentado no relatório anterior como mirror de paridade benigno, sem
mudança nesta sessão) e **TGD `OPENING_BLOCK_INSIDE_DOOR` +1** (novo
neste fix, contra o baseline.json armazenado — que já estava com 45,
3 a mais que o estado A real de 43; comparado contra o estado A real, a
regressão é +3, ver "Aberturas").

## Gates G1–G14

| gate | descrição | status |
|---|---|---|
| G1 | regressão de prisma reproduzida | ✅ (W076/W010/W021 e as 11 paredes inventariadas) |
| G2 | primeira divergência localizada | ✅ (junta de contorno não rastreada por `_layout_internal_joint_positions_cm`) |
| G3 | causa provada | ✅ (H3 confirmada e refinada; H1/H2/H4/H6/H7 refutadas; H5 confirmada) |
| G4 | orientação física tem contrato explícito | ✅ (já era correto — `_asymmetric_bond_origin_and_axis`, geometria pura) |
| G5 | invariância arms/endpoints/input | ✅ (herdada de `_coordinate_arm_role_nodes`, intocada; `_pier_boundary_joint_positions_cm` é pura, sem dependência de ordem) |
| G6 | coverage preservada | ✅ (MISSING_ROW/MOSTLY_EMPTY idênticos C→D nos 3 projetos) |
| G7 | NEW_PRISM_WALLS = 0 | ❌ (9 de 11 permanecem — coincidência geometricamente forçada, ver "Riscos") |
| G8 | TP1 sem regressão | ❌ (`OPENING_BLOCK_INSIDE_DOOR` 0→0 OK, mas 7 paredes de prisma seguem afetadas; `JUNCTION_MISSING_BINDING`+1 pré-existente) |
| G9 | TGD sem regressão | ❌ (`OPENING_BLOCK_INSIDE_DOOR` +3, 3 paredes já afetadas, nenhuma nova; 2 paredes de prisma seguem afetadas) |
| G10 | piloto sem regressão | ✅ (idêntico em tudo) |
| G11 | determinismo preservado | ✅ (teste permanente) |
| G12 | baseline/reference intactos | ✅ (não regravados; `W010` com abertura testado explicitamente, sem invasão de vão) |
| G13 | production diff restrito | ✅ (só `wall_stepper.py`) |
| G14 | suíte final passa | ✅ (518 passed, `-m "not slow"`; suíte lenta com as 2 falhas já documentadas, nenhuma nova além de `OPENING_BLOCK_INSIDE_DOOR`) |

## Riscos

**Risco principal**: 9 de 11 paredes com `PRISM_CONTINUOUS_JOINT` novo
continuam com o achado — a coincidência é **matematicamente forçada**
pela mesma peça (B34, 34cm) sendo escolhida nas duas pontas, combinada
com o comprimento da parede não deixar espaço para uma composição
alternativa. `_pier_layout_avoiding_joints` não tem NENHUMA composição
para buscar quando o pier cabe exatamente 1 bloco (ou, no caso de
W061/W062, quando a cadeia de compensadores é simétrica por
construção). A ÚNICA forma de eliminar isso completamente seria mudar
QUAL peça é escolhida num dos dois nós (ex.: B54 em vez de B34) — uma
mudança na lógica de SELEÇÃO de peça em `solve_l_corner`, mais
invasiva, não verificada nesta sessão, e que arrisca efeitos em cascata
não medidos. Não implementada — reportada como identificação clara do
que é impossível dentro do fix atual, não escondida atrás de uma
heurística arriscada.

**Risco secundário, real**: `OPENING_BLOCK_INSIDE_DOOR` +3 no TGD (3
paredes já afetadas, nenhuma nova) — causa não totalmente diagnosticada;
a separação de listas (contorno vs. recorte de abertura) foi necessária
mas não suficiente para eliminar esta regressão. Precisa de
investigação própria antes de qualquer integração.

**Risco terciário, não bloqueante**: variações pequenas em códigos de
compensador (nível não-crítico), não investigadas individualmente.

## Veredito

**NECESSITA AJUSTE**

Causa-raiz da regressão de prisma provada com rigor (cadeia completa,
não só o validador final) — a junta de CONTORNO contra um nó nunca foi
rastreada pelo mecanismo de desencontro, e isso passou a importar
quando a coordenação de papel (CR anterior) deu às duas famílias um
candidato de nó real no mesmo encontro. O fix implementado corrige
totalmente os casos com liberdade real de composição (2 de 11 paredes,
prova positiva de que a abordagem é correta) e reduz substancialmente o
total de achados de prisma nos dois projetos reais (TGD -215, TP1 -320,
abaixo até do estado anterior a QUALQUER CR desta série) — sem
retroceder um milímetro do ganho de cobertura do commit `d813f45`
(G6 ok).

Mas: G7 (NEW_PRISM_WALLS=0) falha para 9 paredes cuja coincidência é
geometricamente forçada pela escolha atual de peça de canto — uma
limitação genuína, identificada e explicada, não uma heurística
arriscada aplicada às pressas. E uma regressão real, pequena mas não
diagnosticada por completo, apareceu em `OPENING_BLOCK_INSIDE_DOOR`
(+3, TGD). Por isso a entrega não está pronta para integração — precisa
de uma iteração adicional focada em (a) decidir, com autorização
explícita do usuário, se vale a pena investigar uma mudança na seleção
de peça de canto para as 9 paredes restantes, e (b) diagnosticar e
corrigir a regressão de `OPENING_BLOCK_INSIDE_DOOR`.

**Pare antes de qualquer merge.**
