# Regras de modulação de blocos — referência oficial

> Este arquivo é a **fonte de conhecimento oficial** das regras de modulação
> implementadas em `core/wall_modeling.py` (`Script.py` hoje é só um loader
> que baixa esse arquivo do GitHub). Qualquer alteração de comportamento do
> solver de blocos deve manter este documento atualizado — é a referência
> que qualquer pessoa (ou qualquer sessão futura de trabalho neste
> projeto) deve consultar antes de mexer na lógica de modulação.
>
> **A partir da seção 10, este documento deixa de documentar SÓ o que o
> solver já implementa** e passa a registrar também conhecimento
> construtivo real (vergas, contravergas, canaletas, blocos cortados,
> encontros) extraído por medição direta em projetos Revit reais via MCP
> — ainda NÃO implementado no solver. Cada item é rotulado por confiança:
> **REGRA OBRIGATÓRIA** (medida e repetida, sem exceção contrária
> encontrada), **REGRA PREFERENCIAL** (padrão dominante, mas com exceções
> legítimas conhecidas), **EXCEÇÃO PERMITIDA** (desvio aceitável de uma
> regra obrigatória/preferencial, sob condição específica), **PADRÃO
> OBSERVADO AINDA NÃO CONFIRMADO** (visto em poucos exemplos, precisa de
> mais casos antes de virar regra). Nunca alterar uma regra já consolidada
> em silêncio — um exemplo que contradiz uma regra existente é registrado
> como CONFLITO (ver seção 10.7), nunca resolvido por suposição.
>
> Última atualização: 2026-08-28 — nova EXCEÇÃO à regra #1 (seção 11.8:
> C04/C09/B19 encostados numa abertura podem ficar alinhados entre fiadas),
> bug real corrigido no `STRAIGHT_CONTINUATION` (seção 11.9) e nova seção 15
> (paredes de peitoril/verga têm altura e cota de base próprias — origem dos
> nós `AMBIGUOUS` e das colisões em massa). Tudo medido ao vivo via MCP
> contra o projeto `TESTE MODULAÇÃO`, a partir de uma parede que o usuário
> modulou à mão para servir de referência.
>
> **Mudanças da sessão de 2026-08-25** (pedido explícito do usuário, com
> log de execução real e imagens): regra #1 (alinhamento vertical) deixou
> de ser best-effort e virou obrigatória e bloqueante (ver seção 2 e a
> nova seção 11); regra #2 (meio-bloco perto de amarração) ganhou uma
> segunda rede de segurança independente (nova seção 11); regra #3
> (orientação do compensador) foi implementada pela primeira vez (nova
> seção 12); o pipeline análise→correção→modulação→validação→criação foi
> integrado de fato, com relatório final consolidado (nova seção 13); e um
> bug real de reposicionamento parcial ("parte da parede andou, parte
> ficou parada" ao recalcular) foi corrigido tornando "Lançar Blocos -
> criar" idempotente (nova seção 13.4).

## 1. Catálogo de blocos

Família única "14x19", 6 peças, identificadas automaticamente por
família+tipo exatos (`BLOCK_FAMILY_CATALOG_DEFINITIONS`, `load_fixed_block_catalog`)
— nunca por comprimento deduzido:

| Código | Peça real | Comprimento | Papel |
|---|---|---|---|
| B39 | BLOCO INTEIRO - 14x19x39 | 39cm | Peça padrão do preenchimento comum — sempre a primeira prioridade |
| B34 | BLOCO 34 - 14x19x34 | 34cm | Amarração especial (canto L, encontro T degradado) **e** preenchimento comum de meio de parede |
| B54 | BLOCO 54 - 14x19x54 | 54cm | Amarração especial (T verdadeiro, X) |
| B19 | MEIO BLOCO - 14x19x19 | 19cm | Meio-bloco — **último recurso**, só em ponta aberta |
| C09 | COMPENSADOR 14x19x9 | 9cm | Compensador — só quando necessário, nunca em sequência |
| C04 | PASTILHA - 14x19X4 | 4cm | Pastilha — mesma regra do compensador |

Todas as peças têm o mesmo comprimento local (0,0) = centro geométrico do
bloco. B34 e B54 têm células **assimétricas** (um "vão menor"); B39 e B19
têm células simétricas; C09/C04 são maciços (sem células).

Junta de assentamento: `BLOCK_JOINT_CM = 1` (entre blocos e entre bloco e
parede); `BLOCK_OPENING_JOINT_CM = 0` (entre bloco e abertura, ou ponta
livre de parede sem amarração). `PIER_MODULE_CM = 5` (mdc de bloco+junta
de todas as peças) — todo trecho só fecha em blocos se seu comprimento
(descontadas as juntas de contorno) for múltiplo de 5cm.

## 2. Prioridade de preenchimento comum (trechos livres)

Implementada em `_pier_ordered_layout` (Script.py). Ordem de tentativa,
**a MENOR alteração possível primeiro**, cada uma só tentada se a
anterior não fechar o trecho:

1. **Só B39** (nenhum meio-bloco, nenhum B34, nenhum compensador).
2. **1 único B19**, encostado numa **ponta ABERTA** do trecho (abertura ou
   extremidade de parede sem amarração), preenchendo o resto com B39.
   Tenta a ponta de entrada primeiro, depois a de saída.
3. **B39 + B34** (sem B19, sem compensador) — o B34 pode cair em
   **qualquer posição** do trecho, inclusive no meio, quando isso reduz o
   uso de compensadores. *(Alinhamento de vão entre fiadas para B34 de
   meio-de-parede: ver limitação na seção 6.)*
4. **1 único B19** numa ponta aberta, preenchendo o resto com B39+B34.
5. **1 único B19 mesmo sem ponta aberta** (ainda fecha com zero
   compensadores — prioridade maior que qualquer compensador).
6. **B39 (+B34) + no máximo 1 compensador/pastilha** (`MAX_COMPENSATORS_PER_TRECHO = 1`).
7. Compensador acima do teto, se for a única solução existente.
8. Último recurso irrestrito (nunca reporta `NON_MODULAR_WALL` quando uma
   solução — mesmo "feia" — existe).

### Regra do meio-bloco (B19)

- **Nunca no meio de um trecho** — quebra o ritmo/prisma da alvenaria
  (desloca o padrão de junta vertical do resto do trecho). Esta proibição
  é **incondicional**: vale mesmo quando as duas pontas do trecho estão
  abertas (`_merge_adjacent_compensator_pairs` nunca funde um par de
  compensadores adjacentes em B19 quando o par não está numa das duas
  PONTAS do trecho — ver REGRA CRÍTICA #2 mais abaixo).
- Só é usado como **solução de fechamento**, nunca como peça de
  preenchimento comum.
- Só pode encostar numa **ponta aberta**: vão de abertura, ou extremidade
  de parede **sem amarração** (ponta livre de verdade). Uma boneca/pilar
  de encontro (L/T/X) **não conta como ponta aberta**, mesmo quando
  degradada (ver seção 5) — ali a regra do B34 tem prioridade.
- **Prioridade rebaixada em 2026-08-25** (pedido explícito do usuário —
  "não utilizar meio bloco... como recurso para fechar uma amarração"):
  quando um trecho tem as DUAS pontas fechadas (contra um nó L/T/X, sem
  onde B19 encostar de verdade) e nem B39 nem B39+B34 fecham sozinhos, o
  solver agora tenta **compensador(es) primeiro** (tier 5) e só recorre a
  B19 sem ponta aberta (tier 6) como **últimíssimo recurso**, se nem o
  compensador fechar dentro do teto de 1. Antes disto (2026-08-21 a
  2026-08-24), essa ordem era invertida — B19 sem ponta aberta vinha
  ANTES do compensador — o que colocava meio-bloco encostado direto num nó
  de amarração sempre que o compensador também teria fechado.
- **REGRA CRÍTICA #2** (bug real corrigido 2026-08-25): a fusão "9+9→19"
  (ver regra dos compensadores abaixo) é uma otimização que só conhece o
  par de compensadores, não a parede inteira — sem uma guarda extra, ela
  conseguia "nascer" um B19 encostado num nó fechado só porque a
  aritmética batia (2 compensadores do mesmo código, span igual a 19cm),
  by-passando a checagem de ponta aberta que todo o resto do arquivo
  respeita. `_merge_adjacent_compensator_pairs` agora só aceita B19 como
  substituto quando o par está numa das duas PONTAS do array **e** aquele
  lado é uma ponta aberta de verdade (`leading_open`/`trailing_open`,
  passados por todo chamador) — no meio do trecho, nunca, mesmo com as
  duas pontas do trecho abertas.
- **Rede de segurança independente** (regra #2, ver seção 11): mesmo com
  as duas garantias acima na geração, `audit_wall_bond_quality` confere de
  novo, a partir da posição REAL de cada B19 já lançado, se ele está perto
  de uma amarração (nó L/T/X, ponta ou meio de parede) — e bloqueia a
  criação da parede se estiver (`HALF_BLOCK_NEAR_TIE`).

### Regra dos compensadores/pastilhas (C09/C04)

- **Proibido usar 2 ou mais em sequência** no mesmo trecho — nunca uma
  solução recorrente, só pontual.
- `MAX_COMPENSATORS_PER_TRECHO = 1`: acima disso, o solver prefere B34 (se
  couber em qualquer posição) ou 1 B19 numa ponta aberta a empilhar
  compensadores.
- Continuam sendo o **último recurso por construção** (o guloso sempre
  tenta a maior peça primeiro) — nunca substituem B39/B34 quando eles
  fecham sozinhos.
- **Orientação obrigatória** (regra #3, implementada 2026-08-25 — ver
  seção 12): o compensador tem um lado aberto e um lado fechado: o lado
  fechado tem que ficar voltado para a abertura, quando o compensador
  encosta numa de verdade. Antes desta sessão o catálogo tratava C09/C04
  como peças totalmente maciças/simétricas, sem nenhuma noção de
  orientação.

## 3. Zona de exclusão absoluta — porta sem peitoril

Regra **absoluta**, sem exceção: nenhum bloco, compensador ou pastilha
pode invadir o vão real de uma porta sem peitoril (peitoril ≈ 0,
`DOOR_NO_SILL_MAX_SILL_CM = 1.0`).

- `find_door_void_violations` mede a sobreposição real (OBB) entre cada
  candidato de bloco e o vão real de cada porta sem peitoril — roda como
  rede de segurança **explícita e geométrica**, não confia apenas na
  lógica de fronteiras dos trechos.
- Qualquer violação **bloqueia a criação dos blocos** (mesmo mecanismo de
  gate que colisões) — nunca é ignorada ou aplicada "mesmo assim".
- Janelas (peitoril > 0 de verdade) **não** entram nesta regra — o vão
  delas só é excluído na faixa vertical real (ver seção 4).

## 4. Janela não interrompe a fiada abaixo do peitoril

Uma janela só é vazia **na faixa vertical real do seu vão**
(`sill_z_abs` até `head_z_abs`, lidos de `Peitoril`/`Altura_abertura` da
família real — o "X" da vista em elevação). Fiadas inteiramente abaixo do
peitoril ou acima da verga continuam **sólidas**, com blocos normais.

- `_opening_active_in_course_band`: testa se o vão real de uma abertura
  aparece na faixa vertical de UMA fiada física.
- `_group_course_indices_by_opening_band`: agrupa as fiadas físicas pelo
  conjunto de aberturas ativas (normalmente 2-3 grupos distintos, não 14
  solves diferentes).
- `solve_building_blocks_all_courses`: roda o solver uma vez por grupo,
  monta `course_candidates` = `{course_index: [candidatos daquela banda]}`.
- `create_building_blocks(..., course_candidates=...)`: cada fiada usa os
  candidatos da própria banda em vez de repetir cegamente o mesmo par A/B.

Portas (peitoril ≈ 0) não são afetadas por esta regra na prática — o vão
delas cobre praticamente todas as fiadas do pé-direito de qualquer forma.

## 5. Encontros L / T / X

### L_CORNER (`solve_l_corner`)

**Sempre** B34 nas duas fiadas — um por parede, com a ponta do **vão
menor** encostada no nó (`_asymmetric_bond_origin_and_axis` +
`_block_smaller_cell_sign`). O ponto de contato de cada parede é o
`arm_point` (calculado por `extend_wall_ends_to_junctions`): a ponta da
parede estendida até a **face oposta** da parede perpendicular — nunca o
centro geométrico do nó, que deixaria meia espessura do canto vazia.

**Prova geométrica obrigatória** (`validate_l_corner`): os vãos MENORES
das duas fiadas devem ficar **sobrepostos em projeção XY** (mesma posição
em planta, fiadas diferentes/níveis diferentes) — é isso que faz a
amarração realmente "travar" no canto.

### T_INTERSECTION (`solve_t_intersection`) — 3 níveis de prioridade

**Nunca força B54/B34 só porque um nó foi identificado como T** — antes
de tudo, verifica se há espaço físico real (`_t_intersection_room_ok`):

- **T_INTERSECTION_B54_HALF_ROOM_FT** = 27cm (metade do B54) — precisa
  desse espaço **dos dois lados** do nó, na parede principal (mainWall),
  sem invadir nenhuma abertura.
- **CORNER_B34_ROOM_FT** = 34cm — precisa desse espaço na boneca
  (incomingWall), no sentido que se afasta do nó.

**Nível 1 — T verdadeiro**: cabe o espaço acima → B54 centrado no nó
(Fiada A, parede principal) + B34 na boneca (Fiada B), célula central do
B54 alinhada com o vão menor do B34 (`validate_t_intersection`).

**Nível 2 — degrada para L com boneca**: não cabe o T verdadeiro, mas a
boneca tem os 34cm do B34 **e** a parede principal tem 34cm em **ao menos
um** dos dois sentidos a partir do nó → vira, na prática, um canto em L:
B34 na parede principal (esticando só para o lado que TEM espaço) + B34
na boneca. **"Amarração em L usa o bloco de 34 sempre"** — nunca um
elemento menor quando o B34 cabe. Mesma prova geométrica do L_CORNER
(`validate_l_corner` — vãos menores sobrepostos) se aplica aqui.

  - O ponto de contato do B34 da parede principal é calculado à mão
    (`contact_main = point - l_dir * (espessura_da_boneca / 2)`, com o
    bloco se estendendo de volta em `l_dir`) — reproduz exatamente a
    mesma convenção geométrica de `arm_point` que um L_CORNER de verdade
    usa, medida contra um L real via `validate_l_corner` (a primeira
    versão desta correção deslocava para o lado errado e foi pega pelo
    próprio teste).

**Nível 3 — 1 único elemento na boneca**: nem o B34 cabe na boneca (menos
de 34cm reais) → **1 único compensador ou pastilha** (nunca B19 — a
boneca continua sendo um encontro/amarração, não uma ponta livre, então a
regra da seção 2 sobre B19 não se aplica aqui) fecha a boneca sozinho,
**sem nenhuma peça na parede principal** (o preenchimento comum dela, já
existente, cuida do trecho até a ponta com bloco comum, reservando só a
metade da espessura da parede mais larga do nó —
`_node_default_reservation_cm` — para não colidir).

**Sem solução**: nem o C04 (4cm) cabe na boneca → nó reportado em
`intersection_failures`, nunca inventa peça. Precisa de ajuste de
geometria (mover abertura / crescer a boneca) antes.

### X_INTERSECTION (`solve_x_intersection`)

Dois B54 a 90°, ambos centrados no ponto do nó, células centrais
alinhadas (`validate_x_intersection`). Cobre tanto o cruzamento no meio
de duas paredes contínuas quanto o caso raro de 4 pontas coincidindo.

## 6. Limitações conhecidas (não são bugs, são escopo pendente)

- **B34 de meio-de-parede** (seção 2, nível 3) **não** alinha ainda o vão
  menor entre Fiada A e Fiada B quando usado como preenchimento comum
  arbitrário (fora de um encontro L/T) — a orientação usada é uma
  convenção fixa, não otimizada por alinhamento cruzado entre fiadas.
  Diferente do L_CORNER/T-degradado, onde o alinhamento É garantido e
  validado (seção 5).
- **Desencontro de junta vertical** entre Fiada A e Fiada B nos trechos de
  preenchimento comum (`_pier_layout_avoiding_joints`) — **ATUALIZADO
  2026-08-25**: deixou de ser best-effort. Ver seção 11 para a regra
  completa (agora obrigatória e bloqueante) e a prova de que, com
  compensador disponível, SEMPRE existe alternativa sem coincidência para
  um trecho fechado dos dois lados que fecha como múltiplo exato de B39 —
  o caso que motivava esta limitação. O que **continua** sendo apenas
  best-effort, genuinamente sem garantia matemática possível dentro deste
  catálogo (ex.: `allow_compensators=False`, ou um caso ainda não mapeado):
  nesse resíduo a parede é **reportada como não resolvida** no relatório
  final (seção 13), nunca aceita em silêncio.

## 7. Ajuste geométrico automático pós-criação (Etapa 3B)

Quando a modulação de um eixo não fecha, o script tenta **a menor
alteração geométrica possível** antes de desistir (`plan_axis_opening_fix`),
NESTA ordem — nunca aumenta o comprimento total de um eixo (regra
absoluta, 3 barreiras independentes: `_build_axis_opening_plan`,
`validate_wall_modulation`, `apply_axis_opening_fix`):

1. **"boneca"**: quando uma ponta do eixo encosta num encontro L/T/X real
   (não uma ponta livre), cresce o pilarete dessa ponta em ~1-2cm
   (`BONECA_ADJUST_MAX_CM = 2.0`), desloca a(s) abertura(s) no MESMO
   sentido, e encolhe o pilarete da ponta OPOSTA do MESMO eixo pelo mesmo
   valor — o comprimento do eixo inteiro fica idêntico. Reproduz o
   procedimento manual mais comum do usuário.
2. **"shift"**: desloca só as aberturas (posição), redistribuindo
   livremente entre TODOS os pilaretes do eixo, até
   `AXIS_OPENING_SHIFT_MAX_CM = 5cm`.
3. **"trim"**: encurta (nunca estica) uma ponta LIVRE do eixo, até
   `AXIS_TRIM_MAX_CM = 5cm`.
4. **"widen"**: aumenta (nunca reduz) a largura de uma ou mais aberturas,
   até `OPENING_WIDTH_INCREASE_MAX_CM = 5cm` — último recurso.

Cada tentativa só é aceita se o **solver de blocos de verdade** confirmar
que a modulação fecha (`verify` callback) — nunca aplica geometria às
cegas. Acima dos tetos automáticos, o eixo vai para revisão manual —
nunca aplica um ajuste maior sem autorização explícita do usuário.

## 8. Criação no Revit — cotas e alternância de fiadas

- **Fiada 1** nasce em `base_z_abs + FIRST_COURSE_Z_OFFSET_CM` (1cm acima
  da cota bruta do nível — nunca em 0cm).
- **Passo entre fiadas** = `COURSE_JOINT_CM + altura do bloco` = 20cm
  (19cm de bloco + 1cm de junta). Fiada 1 → 1cm, Fiada 2 → 21cm, Fiada 3 →
  41cm... Confirmado ao vivo pelo usuário direto no Revit (2026-08-21) —
  **não alternar esta fórmula de novo sem reconfirmar antes** (já
  inverteu 2x na mesma sessão).
- `course_index` na criação é a **fiada FÍSICA** (par=A, ímpar=B) — cada
  índice só recebe os candidatos da LETRA correspondente (bug real
  corrigido 2026-08-21: antes empilhava A e B na mesma cota).
- `NewFamilyInstance(XYZ, FamilySymbol, Level, StructuralType)` trata o Z
  do ponto como **offset relativo ao Level**, não absoluto — o Revit soma
  a elevação do nível por conta própria (mesma convenção do parâmetro
  "Offset da base" de `Wall.Create`). Passar a cota já absoluta duplicava
  a elevação (bug real corrigido 2026-08-21).

## 8b. Modo de geração das paredes de referência (2026-08-28)

A janela de configuração (`_SetupForm`, seção *"6. Como gerar as
paredes"*) oferece **duas alternativas independentes**, para poder
comparar as duas no mesmo projeto. Constantes em
`core/wall_modeling.py`: `WALL_BUILD_MODE_SEGMENTED` (padrão) e
`WALL_BUILD_MODE_CONTINUOUS`.

| | Segmentado (padrão, histórico) | Contínuo com recortes (novo) |
|---|---|---|
| Elementos `Wall` por eixo | vários (pilarete, peitoril, verga, pilarete…) | **1**, do nível até a altura cheia |
| Como a abertura aparece | ausência de parede entre os trechos | **recorte nativo** (`Opening`) na parede |
| API usada | `Wall.Create` por trecho | `Wall.Create` do eixo inteiro + `Document.Create.NewOpening(wall, p1, p2)` |
| Funções | `build_wall_segments` | `build_wall_segments(..., wall_build_mode=…)` + `build_wall_opening_cuts` + `create_wall_opening_cuts` |

Ordem obrigatória no modo contínuo (é o que o usuário pediu, e também o
que o Revit exige para o recorte cair no lugar certo):

1. cria a parede **inteira**, ignorando portas/janelas;
2. desliga o auto-join e realinha a parede pelo **núcleo**
   (`WallLocationLine.CoreCenterline` + reescrita da `LocationCurve`) —
   os mesmos dois passos de sempre;
3. só **depois** do `doc.Regenerate()` desse realinhamento é que cada
   abertura vira um `Opening`. Criar o recorte antes o posicionaria
   contra a parede antiga, reintroduzindo o desvio de ~0,5cm que o passo
   2 existe para eliminar.

Cada recorte respeita exatamente **posição, largura, altura e peitoril**
lidos da abertura. A única folga aplicada é
`OPENING_CUT_EDGE_OVERSHOOT_M = 0.01` (1cm), e **só** na aresta que encosta na
base ou no topo da parede (porta com peitoril 0, verga que alcança o
pé-direito) — sem ela o Revit pode tratar o retângulo como tangente e não
atravessar o sólido. Arestas internas (peitoril de janela, verga com
parede em cima) ficam na cota exata.

### O que NÃO muda entre os dois modos

- **A modulação de blocos inteira.** `solve_building_blocks_all_courses`
  trabalha sobre os EIXOS (`walls_to_create`) e sobre `openings_per_wall`
  — nunca sobre os elementos `Wall` criados. Nível de inserção,
  alternância de fiadas, encontros L/T/X, amarrações, compensadores e
  zonas de exclusão de porta seguem idênticos. Conferível com
  `python tests/solver_bench.py --fingerprint`: a assinatura sha256 não
  se altera.
- **A ETAPA 3B** (ajuste pós-criação de parede + abertura). Como no modo
  contínuo não existem pilaretes como elementos separados,
  `_classify_continuous_wall_axis` os **sintetiza** a partir do eixo +
  intervalos das aberturas, marcados `"virtual": True`. O planejador
  (`plan_axis_opening_fix`) é o mesmo — ele só enxerga comprimentos de
  pilarete e larguras de vão. Na aplicação
  (`apply_axis_opening_fix`), pilarete virtual é **pulado** (a parede
  contínua nunca é reescrita) e o que se move é a instância da abertura
  **mais o `Opening` que a recorta**, pelo mesmo deslocamento.
- **A revalidação pós-ajuste** continua existindo, mas medindo a coisa
  certa: no modo contínuo o comprimento da parede não muda quando a
  abertura desloca, então `fix_all_wall_modulation_errors` revalida os
  **pilaretes do plano**, não o comprimento da parede inteira (senão todo
  eixo cujo total por acaso não fecha em blocos teria suas correções boas
  desfeitas).

### Escopo consciente

- Os `ElementId` dos recortes **não** entram em `created_wall_ids_all`
  nem em `created_walls_by_axis` — aquelas listas são de paredes
  (`evaluate_wall_modulation` lê `LocationCurve`, "Finalizar/Deletar
  Paredes" apaga o que está lá, o realce azul/vermelho pinta aquilo). Os
  recortes vivem em `created_cuts_by_axis`, consultado só pela ETAPA 3B.
  Apagar a parede já leva os recortes dela junto — são hospedados nela.
- O realce azul/vermelho de comprimento (`evaluate_wall_modulation`) mede
  o comprimento **total** do eixo no modo contínuo, não os pilaretes. Ele
  sempre foi uma pré-checagem permissiva para a vista; quem decide de
  verdade continua sendo o solver de blocos rodado eixo a eixo.
- Aumentar a largura da abertura (OPÇÃO 3 de `plan_axis_opening_fix`)
  segue **desligada** nos dois modos. No contínuo há um motivo a mais: um
  `Opening` é transladado, nunca redimensionado — mudar a largura exigiria
  recriar o recorte, e `apply_axis_opening_fix` reporta falha (com
  RollBack) em vez de adivinhar.

## 9. Testes automatizados

`tests/run_tests.py` (`py -3 tests/run_tests.py`, a partir da raiz do
repo `Scripts.extension`) — cobre todas as regras acima que são
puramente geométricas/aritméticas (roda fora do Revit). Funções que
escrevem de verdade no modelo (`create_building_blocks`,
`apply_axis_opening_fix`, etc.) só são verificáveis ao vivo via MCP
(`mcp__revit-pyrevit__execute_revit_code`) — ver `tests/README.md`.

## 10. Aberturas: vergas, contravergas e canaletas — conhecimento extraído de projeto real

> **Status de sincronia com o código**: 10.1/10.4/10.5 já implementados
> em `core/wall_modeling.py` (secão "AUDITORIA DE ABERTURAS EM ALVENARIA
> JA CONSTRUIDA", antes da Etapa 1) — leitura/diagnóstico apenas, ainda
> não gera geometria nova. 10.2/10.3/10.6/10.7 continuam só documentados
> (ver Status de cada um). Cada item traz um campo
> **Status**: `DOCUMENTADO (aguardando confirmação)` ou `PRONTO PARA
> IMPLEMENTAR` (regra obrigatória, bem confirmada, sem conflito aberto —
> candidata à próxima sincronização doc+código+teste) ou `IMPLEMENTADO
> (commit X)` uma vez codificado. Por acordo com o usuário (2026-08-24):
> nenhuma regra nova entra no script sem estar documentada aqui primeiro,
> e nenhuma regra documentada aqui fica sem o código correspondente por
> muito tempo SE ela já estiver confirmada — itens ainda `PADRÃO
> OBSERVADO AINDA NÃO CONFIRMADO` ou com `CONFLITO` aberto **não** devem
> ser implementados até virarem `REGRA OBRIGATÓRIA`/`PREFERENCIAL` de
> verdade (implementar em cima de conhecimento não confirmado violaria a
> própria regra de não inventar a partir de casos isolados).

> **Metodologia**: tudo nesta seção foi medido via
> `mcp__revit-pyrevit__execute_revit_code` (100% leitura, nenhuma
> `Transaction` aberta) contra `TORRE EASY-LO-R00.rvt` (projeto JARDIM DA
> COSTA BEACH CLUB, Revit 2026.3, ~90 mil instâncias de bloco/canaleta/
> verga). É **1 de N projetos** diagnosticados — ver
> [PADRAO_MODULACAO.md](PADRAO_MODULACAO.md) e
> [diagnosticos/TORRE_EASY-LO-R00.md](diagnosticos/TORRE_EASY-LO-R00.md)
> para o registro bruto completo. Como as portas/janelas nativas do Revit
> já tinham sido excluídas deste projeto, as aberturas foram detectadas
> geometricamente (vazios verticais persistentes em várias fiadas
> consecutivas de uma mesma linha de parede reconstruída a partir das
> instâncias de bloco), não a partir de elementos `Door`/`Window`.

### 10.1 — Dois sistemas de tratamento de abertura, segregados por contexto

- **Status**: **IMPLEMENTADO (commit da sessão 2026-08-24)** — detecção/
  seleção de sistema via `detect_opening_system_for_level` em
  `core/wall_modeling.py` (100% leitura, nunca mistura os dois sistemas:
  devolve `OPENING_SYSTEM_UNKNOWN` se ambos aparecerem no mesmo nível). A
  **geração** de geometria de cada sistema continua NÃO implementada —
  depende de 10.2/10.3, que ainda não estão confirmados. Testes offline:
  `test_family_name_matchers_da_secao_10` (`tests/test_script.py`).
- **Regra**: existem dois sistemas distintos para resolver o vão de uma
  abertura, e um projeto pode usar os dois — mas **não misturados no
  mesmo trecho/nível**:
  - **Sistema 1 (verga/contraverga convencional)**: famílias dedicadas
    `VERGA JANELA` (acima do vão) e `CONTRAVERGA`/`CONTRAVERGA1` (abaixo).
  - **Sistema 2 (canaleta substituindo verga/contraverga)**: o vão é
    fechado por uma sequência de fiadas especiais em bloco-canaleta (ver
    10.2), sem nenhuma instância de `VERGA JANELA`/`CONTRAVERGA`.
- **Motivo**: são soluções construtivas alternativas para o mesmo
  problema estrutural (vencer o vão); a escolha entre elas parece ser uma
  decisão de projeto/pavimento, não uma regra geométrica universal.
- **Onde se aplica**: TORRE EASY-LO-R00 usa Sistema 1 **exclusivamente no
  nível "01. TER"** (térreo) — as 539 instâncias de `VERGA JANELA`/
  `CONTRAVERGA`/`CONTRAVERGA1` encontradas no projeto inteiro estão TODAS
  nesse nível. Os pavimentos-tipo (`TP1`, amostrados em vários níveis
  05-15) usam exclusivamente Sistema 2.
- **Exceções**: nenhuma encontrada até agora (a segregação por nível foi
  100% consistente na amostra).
- **Prioridade**: **REGRA OBRIGATÓRIA para o script** — nunca aplicar
  Sistema 1 e Sistema 2 no mesmo trecho automaticamente; a escolha do
  sistema deve ser uma configuração explícita (por nível ou por projeto),
  nunca inferida silenciosamente peça a peça.
- **Exemplos observados**: ver posições brutas em
  `diagnosticos/TORRE_EASY-LO-R00.md`.
- **Impacto na modulação**: um futuro solver de aberturas precisa
  primeiro DETECTAR qual sistema o trecho/nível usa (por amostragem local
  ou configuração do usuário) antes de decidir como fechar um vão —
  aplicar o sistema errado quebraria o padrão do pavimento inteiro.

### 10.2 — Sequência de fiadas do Sistema 2 (verga em canaleta)

- **Status**: DOCUMENTADO (aguardando confirmação — só 2 exemplos).
- **Regra**: quando o sistema é canaleta (10.1), a verga de uma abertura
  não é uma peça única — é uma **sequência de 2-3 fiadas especiais**,
  medida identicamente em dois vãos reais distintos (uma janela de 166cm
  e uma porta de 121cm, mesmo pavimento, trechos diferentes):
  1. Fiada fina (9cm, peça `CORTADO`) **só nas duas jambas** — apoio de
     transição, não atravessa o vão.
  2. Fiada fina (9cm, peça `CORTADO`) **cheia**, atravessando toda a
     largura da verga (jamba a jamba) — nivelamento antes da canaleta.
  3. Fiada de **canaleta** (`CANALETA J`/`CANALETA 34`/`CANALETA
     INTEIRA`/`MEIA CANALETA`, conforme o vão de largura restante),
     também cheia — a verga estrutural propriamente dita (presumivelmente
     grauteada, não confirmado por não haver acesso ao conteúdo interno).
  Depois da fiada de canaleta, a alvenaria comum retoma.
- **Motivo (inferido, não confirmado com o usuário)**: a canaleta (bloco
  U) precisa apoiar numa superfície plana e nivelada nas duas jambas antes
  de receber graute/armadura; as duas fiadas de `CORTADO` corrigem a
  diferença entre o topo real do vão (que raramente cai exatamente num
  múltiplo de 20cm) e a cota onde a canaleta pode assentar.
- **Onde se aplica**: Sistema 2 (canaleta), confirmado em janela e porta.
- **Exceções**: nenhuma vista ainda — só 2 exemplos inspecionados em
  detalhe. **Não generalizar a proporção exata (9+9+altura-canaleta) sem
  medir mais casos.**
- **Prioridade**: **PADRÃO OBSERVADO, FORTE MAS AINDA NÃO CONFIRMADO**
  (2 exemplos concordantes, mas a amostra é pequena pra virar
  "obrigatória" — próximo passo natural é medir mais vãos antes de
  codificar esse layout exato no solver).
- **Exemplos observados**: vão 6829-6995cm (janela, larg. 166cm, nível
  TP1) e vão 7594-7715cm (porta, larg. 121cm, mesmo nível) — coordenadas
  brutas e dump completo fiada-a-fiada arquivados na sessão (não
  persistidos em arquivo ainda, só nesta conversa — **pendente**: salvar
  esse dump em `diagnosticos/`).
- **Impacto na modulação**: um bloco `CORTADO` encontrado logo acima ou
  abaixo de um vão, nas jambas ou atravessando toda a largura, **não é um
  erro de modulação** — é a execução correta do apoio da verga. O script
  NÃO deveria sinalizar isso como incompatibilidade.

### 10.3 — Verga se apoia além da largura do vão (comprimento de apoio)

- **Status**: DOCUMENTADO (aguardando confirmação — só 1 exemplo com
  medição de comprimento).
- **Regra**: a fiada de canaleta da verga (10.2) se estende **além** das
  duas jambas do vão, apoiando na alvenaria sólida adjacente — no exemplo
  da porta de 121cm, a canaleta mediu ~319cm (bem mais larga que o vão),
  ultrapassando a jamba em pelo menos um bloco/canaleta inteiro de cada
  lado.
- **Motivo**: prática padrão de alvenaria — uma verga/lintel precisa de
  comprimento de apoio nas duas extremidades, não pode "flutuar" exatamente
  na largura do vão.
- **Onde se aplica**: Sistema 2 (canaleta), possivelmente também Sistema 1
  (não verificado ainda para `VERGA JANELA`/`CONTRAVERGA`).
- **Exceções**: não encontradas ainda.
- **Prioridade**: **PADRÃO OBSERVADO AINDA NÃO CONFIRMADO** — só 1 exemplo
  com medição clara de comprimento de apoio; precisa de mais casos, e
  medir o comprimento de apoio em cm (não só "mais largo que o vão") antes
  de virar regra numérica.
- **Exemplos observados**: vão-porta 7594-7715cm, canaleta medida
  7525-7844cm.
- **Impacto na modulação**: ao dimensionar/posicionar uma verga, o
  trecho de canaleta não deve ser cortado exatamente na largura do vão —
  precisa reservar apoio nas duas pontas.

### 10.4 — Porta não tem contraverga; janela pode ter verga e contraverga

- **Status**: **IMPLEMENTADO (commit da sessão 2026-08-24)** —
  `detect_wall_openings_from_courses` em `core/wall_modeling.py` classifica
  `tipo_provavel` como `PORTA`/`JANELA` por essa exata regra (vão toca a
  fiada mais baixa da linha vs não toca). Testes offline:
  `test_detect_wall_openings_classifica_porta_quando_toca_a_base`,
  `test_detect_wall_openings_classifica_janela_quando_nao_toca_a_base`
  (`tests/test_script.py`).
- **Regra**: confirmando a hipótese do usuário — em toda porta observada
  (vão chega à fiada mais baixa do trecho, "toca o chão"), não existe
  nenhuma peça/fiada especial ABAIXO do vão (nem canaleta, nem
  `CONTRAVERGA`). Em toda janela observada (vão não toca a base), a MESMA
  sequência de 10.2 (cortado-fino + cortado-cheio + canaleta) aparece
  tanto ACIMA quanto ABAIXO do vão.
- **Motivo**: fisicamente não há alvenaria abaixo de uma porta pra vencer
  (o vão vai até o piso); a janela tem peitoril, que também precisa de
  apoio nivelado como a verga.
- **Onde se aplica**: ambos os sistemas (Sistema 1: `CONTRAVERGA`/
  `CONTRAVERGA1` só emparelhados com `VERGA JANELA` em janelas, nunca
  encontrados sozinhos = candidato a porta; Sistema 2: confirmado
  diretamente no vão-janela de 166cm, que tem a sequência de 10.2
  simetricamente acima E abaixo).
- **Exceções**: nenhuma vista ainda.
- **Prioridade**: **REGRA OBRIGATÓRIA** — critério direto pra
  classificar automaticamente um vão detectado como porta vs janela: se
  o vão toca a fiada mais baixa do trecho → porta (nunca esperar/exigir
  contraverga); senão → janela (esperar verga E contraverga).
- **Impacto na modulação**: um validador que exigisse contraverga em toda
  abertura estaria errado; a ausência de contraverga só é erro quando o
  vão NÃO toca a base do trecho.

### 10.5 — Blocos cortados perto de aberturas não são aleatórios

- **Status**: **IMPLEMENTADO (commit da sessão 2026-08-24)** —
  `is_cut_block_justified_by_opening`/`nearest_opening_jamb_distance_cm`
  em `core/wall_modeling.py`, usadas por `audit_existing_masonry_openings`
  pra marcar cada bloco `CORTADO` encontrado como `justificado_por_
  abertura` (True/False) em vez de reportá-lo direto como erro. Teste
  offline: `test_is_cut_block_justified_by_opening_perto_vs_longe`
  (`tests/test_script.py`).
- **Regra**: confirmado estatisticamente — de 1.698 instâncias de blocos
  `CORTADO` amostradas (todas as linhas de parede substanciais do
  prédio), **65% ficam a menos de 60cm de uma jamba de vão detectado**
  (40% encostam mesmo, <25cm). Blocos cortados concentram-se
  fortemente perto de aberturas, não estão espalhados aleatoriamente
  pela parede.
- **Motivo**: cortes servem pra criar apoio nivelado pra verga/contraverga
  (10.2) e resolver a diferença dimensional entre o vão real e a grade
  modular de 20cm — não são "gambiarra" genérica.
- **Onde se aplica**: toda a alvenaria do projeto.
- **Exceções**: os ~30% restantes (>150cm de qualquer vão detectado) —
  parte é limitação da própria detecção de vão (não pega 100% dos vãos
  reais), parte pode ser ajuste de pé-direito/nível (visto na fiada de
  topo em `MEIO BLOCO CORTADO` sem vão nenhum perto, na parede
  inspecionada manualmente na sessão anterior) — **não investigado a
  fundo, não assumir que é sempre justificado**.
- **Prioridade**: **REGRA OBRIGATÓRIA para o script**: antes de reportar
  um bloco cortado como suspeito/erro de modulação, verificar se ele está
  perto de uma jamba de abertura (ou de um encontro L/T/X) — só reportar
  como erro genuíno quando não houver justificativa geométrica próxima.
- **Impacto na modulação**: reduz falsos positivos de "erro de
  modulação" em qualquer validador futuro que rode sobre um modelo já
  construído.

### 10.6 — Desencontro de junta vertical entre fiadas consecutivas (medido)

- **Status**: DOCUMENTADO (aguardando confirmação — 1 par de fiadas só).
- **Regra**: o deslocamento horizontal entre juntas de fiadas
  consecutivas, medido diretamente nos dados já coletados (comparando
  posições de bloco entre duas fiadas adjacentes no vão-porta de 10.2),
  foi de **~15cm** — consistente com o objetivo já documentado na seção 6
  ("desencontro de junta vertical... best-effort") de nunca deixar juntas
  verticais contínuas entre Fiada A e Fiada B.
- **Motivo**: amarração estrutural da alvenaria (prisma) — juntas
  verticais alinhadas entre fiadas adjacentes enfraquecem a parede.
- **Onde se aplica**: geral.
- **Exceções**: não medidas ainda de forma sistemática (só 1 par de
  fiadas comparado).
- **Prioridade**: **PADRÃO OBSERVADO AINDA NÃO CONFIRMADO** como valor
  numérico fixo — precisa medir a distribuição completa do deslocamento
  em várias paredes antes de tratar "15cm" como constante.
- **Impacto na modulação**: dá um alvo numérico real pra validar/guiar o
  `_pier_layout_avoiding_joints` já existente no solver (seção 6 do
  documento).

### 10.7 — CONFLITO REGISTRADO: "canaleta sempre na última fiada do topo de toda parede"

- **Status**: CONFLITO ABERTO — não implementar nenhum dos dois lados
  até resolver.
- **Hipótese do usuário**: toda parede deve ter canaleta na última fiada
  do topo, independentemente de aberturas.
- **Medição real**: testando a fiada mais alta de 221 linhas de parede
  substanciais (≥60 peças) do prédio inteiro, só **39,4% (87/221)** têm
  a fiada do topo predominantemente composta por canaleta. Um
  contraexemplo grande e não-trivial: a linha `(nível=03.G03, rot=0,
  perp=1120.0)`, com **51 peças** na fiada do topo, **nenhuma canaleta**
  (100% `BLOCO INTEIRO`/`BLOCO 34`/`COMPENSADOR`).
- **Contexto do conflito**: a taxa de 39-55% (variou conforme o método de
  agrupamento usado nas duas medições desta sessão) é baixa demais pra
  simplesmente confirmar a regra como obrigatória, mas o contraexemplo é
  grande demais (51 peças) pra ser só ruído de medição.
- **Hipóteses não verificadas para o conflito** (nenhuma delas testada
  ainda, listadas para a próxima sessão):
  1. Limitação do método: a "linha" reconstruída (agrupamento por
     coordenada perpendicular arredondada em 5cm) pode estar cortando a
     parede real antes da fiada de canaleta verdadeira, ou juntando duas
     paredes diferentes numa só linha, mascarando o topo real.
  2. A regra pode ser real mas não universal: parede de vedação/divisória
     que não chega à laje pode legitimamente não precisar de canaleta de
     cinta (só paredes estruturais que apoiam laje precisariam).
  3. Nível "03. G03" (onde está o contraexemplo, um pavimento de garagem)
     pode ter um padrão construtivo diferente dos pavimentos-tipo
     residenciais — não verificado se é uma exceção só desse tipo de
     pavimento.
- **Prioridade**: **NÃO RESOLVIDO — próximo passo obrigatório antes de
  qualquer implementação**: inspecionar visualmente (via
  `get_revit_view` com `CropBox`) a linha `(03.G03, rot=0, perp=1120.0)`
  no Revit de verdade, e comparar mais contraexemplos antes de decidir se
  a regra é OBRIGATÓRIA COM EXCEÇÃO (ex.: só paredes que apoiam laje) ou
  se o método de detecção precisa ser refeito.
- **NÃO tratar esta regra como confirmada no script até este conflito
  ser investigado.**

### 10.8 — Pendências explícitas (não investigado ainda nesta rodada)

Para não passar a falsa impressão de cobertura completa — itens que o
usuário pediu e que **ainda não foram medidos**:
- Comportamento fino de fiadas pares/ímpares além do desencontro de junta
  (10.6) — ex.: rotação/espelhamento de peças especiais.
- Bonecas específicas de porta/janela (o pilar que encosta na jamba) —
  observadas de relance nos dumps (ex. `BLOCO 34`/`MEIO BLOCO` variando
  entre fiadas nas jambas dos vãos de 10.2/10.3), não caracterizadas
  sistematicamente.
- Início/fim de parede (ponta livre) como caso distinto de encontro
  L/T/X — não isolado ainda.
- Confirmação estatística (não só geométrica) de B34 em L e B54 em T/X
  em ENCONTROS REAIS detectados no modelo (a geometria das peças bate,
  seção 1; o USO real em nós de verdade só foi visto qualitativamente).
- Repetição destes padrões em OUTROS projetos (esta seção inteira vem de
  1 projeto só, TORRE EASY-LO-R00 — ver preâmbulo desta seção).
- Persistir os dumps fiada-a-fiada usados nesta análise em
  `diagnosticos/`, hoje só existem no histórico da conversa.

## 11. Regra #1 — alinhamento vertical obrigatório entre fiadas (2026-08-25)

> **Status**: IMPLEMENTADO (sessão 2026-08-25). Substitui o antigo "best
> effort" descrito na seção 6. Pedido explícito do usuário, a partir de um
> log de execução real (128 paredes, 120 reprovadas na auditoria de
> amarração) e imagens: "a junta vertical de uma fiada não pode coincidir
> com a junta vertical da fiada imediatamente acima ou abaixo, em hipótese
> alguma... essa regra tem prioridade sobre qualquer tentativa de
> simplesmente preencher o comprimento da parede... não pode ser
> flexibilizada".

### 11.1 — Causa-raiz corrigida: `_pier_ordered_layout` ignorava `first_code` quando um tier mais cedo já fechava

`_pier_layout_avoiding_joints` tentava desencontrar a junta da Fiada B
forçando códigos diferentes como primeiro bloco (`first_code`), mas
`_pier_ordered_layout` sempre tenta seus próprios tiers em ordem fixa (1:
só B39; 3: B39+B34; ...) e devolve o resultado do **primeiro que
fechar** — o `first_code` só é honrado quando pertence ao pool desse
tier. Pedir `first_code="B34"` não tinha NENHUM efeito sempre que o
trecho já fechava só com B39 no tier 1 (o pool do tier 1 nem contém B34).
Como muitos trechos entre dois encontros L/T/X (as duas pontas fechadas,
sem onde B19 encostar) fecham exatamente como um múltiplo de 40cm (só
B39), a Fiada B saía **idêntica** à Fiada A — 100% das juntas
coincidindo, em toda a altura da parede.

`_pier_forced_bypass_layouts` (nova função) contorna isso chamando
`_greedy_fill_blocks` **direto**, com o pool e o primeiro bloco já
escolhidos — alcança de verdade uma composição alternativa mesmo quando
um tier mais cedo também fecharia. **Prova**: para um trecho fechado dos
dois lados que fecha como múltiplo exato de 40cm (só B39), colocar 1 B34
no início e preencher o resto com B39 (guloso normal) sempre sobra
**exatamente 5cm** no fim — e 5cm é exatamente 1 C04 (4cm+1cm de junta).
Fecha para QUALQUER comprimento de trecho ≥40cm, com 1 único B34 + 1
único C04 (dentro do teto de 1 compensador) — nunca precisa dos 8 B34
"puros" que a solução sem compensador exigiria (inviável na prática).

### 11.2 — Causa-raiz corrigida: prioridade de `_score` invertida (bug real achado pelos próprios testes)

`_pier_layout_avoiding_joints` comparava candidatos por
`(alinhamento_de_vazio, coincidência_de_junta)`, alinhamento PRIMEIRO.
Isso é inofensivo na maioria dos casos (com deslocamento de meio módulo
os dois objetivos andam juntos), mas dá resultado **errado** exatamente
quando o layout padrão (sem forçar nada) da Fiada B é **idêntico** ao da
Fiada A — o que acontece sempre que as duas fiadas têm o mesmo pilarete e
as mesmas juntas de contorno (nenhuma abertura no meio para diferenciar
as duas). Comparado contra si mesmo, o alinhamento de vazio sai
**perfeito por construção** (é o mesmo vazio no mesmo lugar), mas junto
com a **pior** coincidência de junta possível (também consigo mesmo, 100%)
— com alinhamento primeiro, essa "cópia idêntica" vencia qualquer
alternativa real que evitasse a junta mas não alinhasse vazio nenhum.
Corrigido invertendo a prioridade: `(coincidência_de_junta,
-alinhamento_de_vazio)` — coincidência de junta é o critério PRIMÁRIO/
ABSOLUTO agora, alinhamento de vazio só desempata entre candidatos que já
têm zero coincidência.

### 11.3 — Ordem B19-sem-ponta-aberta vs. compensador invertida (ver seção 2)

Ver a subseção "Prioridade rebaixada em 2026-08-25" da regra do
meio-bloco, seção 2: para um trecho fechado dos dois lados, o solver
agora tenta compensador ANTES de B19 sem ponta aberta — regra #2, não
regra #1, mas resolvida na mesma sessão pelo mesmo motivo (as duas regras
se cruzam nesse tier).

### 11.4 — Validação obrigatória e escalada para ajuste geométrico

`solve_wall_free_fill` registra, para cada trecho da Fiada B, se a
composição final (mesmo depois da busca melhorada acima) ainda tem
alguma coincidência de junta residual (`alignment_conflicts`).
`validate_wall_modulation` trata isso como um check BLOQUEANTE
(`sem_alinhamento_vertical`), e `process_walls_one_by_one` agora dispara
o mesmo mecanismo de ajuste geométrico automático (Etapa 3B — seção 7)
para um trecho com conflito de alinhamento, não só para trechos que não
fecham aritmeticamente ou colidem. Um deslocamento de poucos centímetros
na abertura muda a aritmética do trecho o suficiente para desbloquear uma
composição sem coincidência.

### 11.5 — Segunda validação independente: `audit_wall_bond_quality` volta a bloquear a criação

`audit_wall_bond_quality`/`audit_all_walls_bond_quality` (Etapa 4C) fazem
a checagem final, vendo a parede INTEIRA (todas as fiadas físicas de uma
vez, não só o par A/B), depois de tudo já lançado — a segunda verificação
independente pedida pelo usuário (regra #7). Em 2026-08-24 esta auditoria
tinha sido mudada para "não bloquear mais a criação, só marcar em
vermelho depois" (pedido do usuário na época). Em 2026-08-25 essa decisão
foi **revertida especificamente para esta auditoria** (nunca para
colisão entre blocos, que continua "cria e marca em vermelho"): uma
parede reprovada em `CONTINUOUS_VERTICAL_JOINT`, `REPEATED_VERTICAL_
COMPENSATOR_STRIP` ou `HALF_BLOCK_NEAR_TIE` **não recebe bloco nenhum**
em "Lançar Blocos - criar" — só a(s) parede(s) envolvida(s) ficam de fora
(nunca a planta inteira, ver seção 13) e a própria parede de referência
fica marcada em vermelho na vista (nenhuma peça existe para marcar). Isso
só voltou a ser viável depois de corrigir dois falsos positivos reais que
inflavam a contagem de reprovações:

> **CORREÇÃO 2026-08-26** (achado de forma independente em duas frentes no
> mesmo dia: nesta auditoria de conformidade, seção 14, e em `c975a36`/PR
> #26, que corrigiu o mesmo teste desatualizado por outro caminho — os
> dois concordam):
> `ALTERNATING_JOINT_PATTERN` **não bloqueia mais** desde `abb46b5`
> (2026-08-25, commit POSTERIOR ao parágrafo acima no mesmo dia — este
> parágrafo nunca tinha sido atualizado depois desse commit, uma
> divergência real entre este documento e o código, agora corrigida aqui).
> Causa: sob a arquitetura de `solve_building_blocks_all_courses` (um par
> de fiadas A/B repetido fisicamente em toda fiada da mesma paridade),
> `ALTERNATING_JOINT_PATTERN` é **tautologicamente verdadeiro** — é o
> próprio funcionamento correto de fiadas alternadas (a junta da fiada A é
> coberta pelo corpo do bloco da fiada B logo acima/abaixo), não um
> defeito. O defeito real — a MESMA junta coincidindo nas DUAS paridades —
> já é coberto por `CONTINUOUS_VERTICAL_JOINT`, que continua bloqueando
> normalmente. `alternating_joints` continua sendo calculado e devolvido
> (dado de diagnóstico), mas nunca mais soma penalidade nem entra em
> `problems`. Ver também seção 11.7 abaixo — a correção por lá (`variants_
> per_course`, K=3) continua válida e reduz a repetição na prática, só
> deixou de ser a única forma de uma parede passar na auditoria.

- **Nó de meio de parede** (T_INTERSECTION principal, X_INTERSECTION):
  a peça de amarração do nó repete na mesma posição X em toda fiada, por
  construção — isso é correto (seção 5), não uma falha, mas sem saber
  onde estão os nós de meio de parede a auditoria não tinha como
  distinguir isso de uma faixa vertical repetitiva de verdade
  (`BOND_STRIP_NODE_EXEMPT_CM`, o mesmo raio de influência já usado para
  aberturas).
- **Junta corrida "fantasma" no meio de uma abertura** — já corrigido
  antes desta sessão (`BOND_MAX_ADJACENT_GAP_CM`), continua valendo.

### 11.6 — Rede de segurança para meio-bloco perto de amarração (regra #2)

`audit_wall_bond_quality` também confere, independentemente da geração,
se algum B19 já lançado está a menos de `HALF_BLOCK_TIE_ADJACENCY_CM`
(≈2cm) de uma amarração real (ponta L/T/X da própria parede, via
`_axis_corner_end_sides`, ou nó de meio de parede) — `HALF_BLOCK_NEAR_
TIE`, com a MAIOR penalidade de toda a auditoria
(`PENALTY_HALF_BLOCK_NEAR_TIE`, acima até de junta corrida) porque o
usuário pediu para "penalizar fortemente". Diferente das checagens de
faixa repetitiva (que exigem um padrão em várias fiadas), esta dispara
com uma ÚNICA ocorrência — a regra #2 é uma proibição incondicional por
peça, não uma busca por padrão.

### 11.7 — Causa-raiz do bug real "118/128 paredes reprovadas": geração de
apenas 2 layouts fixos ("A"/"B") repetidos para sempre, contra uma
auditoria que exige variação (2026-08-25)

**Sintoma medido em produção** (CAD real, 128 paredes): a Etapa 3B
("Ajustar Erros") corrigia paredes normalmente, mas o relatório final
mostrava só 2/128 paredes moduladas — as outras 118 eram reprovadas por
`audit_wall_bond_quality`/`ALTERNATING_JOINT_PATTERN` (seção 11.5) e não
recebiam bloco nenhum.

**Causa-raiz** (não era um bug na auditoria — a auditoria continua
absoluta, nada nela mudou): `solve_building_blocks_all_courses`
(`wall_modeling.py`) agrupa as fiadas físicas de uma parede em "bandas"
por conjunto de aberturas ativas (`_group_course_indices_by_opening_
band`) e, para CADA banda, chamava `solve_building_blocks` **uma única
vez**, produzindo um único par de layouts "A" (fiadas pares) / "B"
(fiadas ímpares) e repetindo cada um **em 100% das fiadas físicas da sua
paridade**:

```python
for course_index in course_indices:
    letter = "A" if course_index % 2 == 0 else "B"
    course_candidates[course_index] = [c for c in result["candidates"] if c["course"] == letter]
```

`ALTERNATING_JOINT_PATTERN` (`audit_wall_bond_quality`, `BOND_
ALTERNATING_JOINT_RATIO = 0.6`, `BOND_ALTERNATING_JOINT_MIN_COURSES = 3`)
reprova qualquer junta que recorra em ≥60% das fiadas de UMA paridade
(pares e ímpares contados separadamente). Como o layout "A" era **sempre
idêntico** em 100% das fiadas pares (e "B" em 100% das ímpares) — não
60%, **100%** — qualquer parede com ≥1 junta interna e pé-direito normal
(10–16 fiadas) disparava a reprovação quase por construção. É por isso
que a taxa medida (118/128 ≈ 92%) é alta demais para ser defeito de obra
genuíno: é um descompasso estrutural entre "gera 2 padrões para sempre" e
"a auditoria proíbe ≥60% de repetição dentro da mesma paridade", não um
caso de borda sutil. Não havia teste algum que afirmasse "uma parede
comprida (≥6 fiadas), com A e B genuinamente diferentes entre si, não
dispara `ALTERNATING_JOINT_PATTERN`" — o cenário simplesmente nunca foi
exercitado ponta a ponta.

**Correção** (só no lado da geração — a auditoria e seus limiares/
bloqueio de criação em `_execute_create`/`_on_solve_done` não foram
tocados): em vez de 1 layout fixo por família par/impar,
`solve_wall_free_fill` agora aceita `variants_per_course` (K) e gera até
K composições DISTINTAS por família, cada uma evitando a união das
juntas internas de todas as composições anteriores da mesma busca
(reaproveita `_pier_layout_avoiding_joints`, que já existia para a Fiada
B evitar a Fiada A — generalizado para uma composição evitar TODAS as
anteriores, inclusive dentro da própria família). `solve_opening_jamb`
recebeu o mesmo tratamento (`variant_count`, `_jamb_build_course_
variants`): sem variar também o bloco de jamb, a junta logo após ele
continuava idêntica em toda fiada da mesma paridade e a correção não
bastava para paredes com abertura (a maioria das paredes reais) — a
variante 0 de cada família é sempre exatamente o resultado histórico
(`course_a`/`course_b`), e nenhum código de uma variante da família A
repete em NENHUMA variante da família B (generalização da regra crítica
#1 de um único par A/B para todo par cruzado entre variantes).
`solve_building_blocks_all_courses` passou a escolher, para cada fiada
física, `variant_index = (course_index // 2) % K` dentro da família
par/impar de `course_index` (nunca `course_index % K` direto — isso
quebraria a separação par/ímpar de que nós/cantos L/T/X e jambs
dependem para decidir qual das duas fiadas "A"/"B" cada fiada física
usa).

**Por que K=3 basta** (verificado por força bruta, não suposto — ver
`PIER_LAYOUT_VARIANTS_PER_COURSE`): com K composições por família e passo
1 dentro da paridade, a fração máxima que uma única composição ocupa
dentro da sua paridade é `ceil(total_da_paridade / K) / total_da_paridade`.
Calculado para todo `num_courses` de 3 a 39 (cobre qualquer pé-direito
real), o pior caso com K=3 é **42,9%** (3 de 7 fiadas) — quase 20 pontos
percentuais abaixo do limite de 60%. K=2 é exatamente o bug original
(100% de repetição); K=3 é o menor K que resolve com margem confortável,
por isso foi o escolhido (não K=4 ou mais, que gastariam mais tempo de
busca sem necessidade).

**Retrocompatibilidade**: `variants_per_course`/`variant_count` têm
default 1 em toda a cadeia (`solve_wall_free_fill`, `solve_opening_jamb`,
`solve_building_blocks`, `process_walls_one_by_one`,
`solve_building_blocks_all_courses`) — reduz exatamente ao comportamento
histórico (nenhuma mudança de resultado) para todo chamador existente,
inclusive os usados pela Etapa 3B/"Ajustar Erros" (correção geométrica),
que **continuam em K=1** de propósito (não precisam de variação — só
verificam se o trecho fecha aritmeticamente, o que independe de K). Só o
chamador de produção da Etapa 4C (`_execute_solve`, "Lançar Blocos -
resolver") passa `variants_per_course=PIER_LAYOUT_VARIANTS_PER_COURSE`
explicitamente.

**Caso residual que continua reprovando, e é CORRETO reprovar** (não é
regressão desta correção): um trecho de preenchimento comum muito longo
e sem nenhuma abertura/nó no meio (um pilarete "puro" com uma sequência
longa de blocos do mesmo tamanho) pode ter juntas internas espaçadas de
forma tão regular que nenhuma composição alternativa do catálogo evita
TODAS as coincidências simultaneamente contra a composição anterior —
nesse caso `CONTINUOUS_VERTICAL_JOINT` (que olha a parede inteira,
independente de paridade, não é afetado por K) continua disparando
corretamente, e o trecho residual aparece em `alignment_conflicts` (a
mesma rede de segurança da seção 11.5, nunca aceita em silêncio) para o
pipeline tentar um ajuste geométrico — exatamente o comportamento que a
regra #1 exige.

### 11.8 — EXCEÇÃO PERMITIDA: peça pequena de fechamento encostada numa abertura pode ficar alinhada (2026-08-28)

- **Status**: **IMPLEMENTADO (sessão 2026-08-28)** —
  `OPENING_ALIGNED_EXEMPT_CODES` + o parâmetro
  `leading_is_open`/`trailing_is_open` de
  `_layout_internal_joint_positions_cm` (`core/engine/wall_stepper.py`), e
  `_joint_is_opening_aligned_exempt` (`core/wall_modeling.py`, usada por
  `audit_wall_bond_quality`). Testes:
  `test_junta_de_peca_pequena_encostada_em_abertura_e_isenta_da_regra_1` e
  `test_auditoria_isenta_junta_de_pastilha_encostada_no_vao`.
- **Regra** (pedido explícito do usuário, a partir de uma parede que ele
  modulou **à mão** no Revit para servir de referência): *"os blocos B4, B9
  e B19 podem ficar alinhados quando estão encostados nas aberturas,
  principalmente o b4 e o b9"*. Ou seja: a junta que separa uma
  **pastilha (C04)**, **compensador (C09)** ou **meio-bloco (B19)** do seu
  vizinho **pode coincidir** entre a Fiada A e a Fiada B **quando essa peça
  encosta num vão** — não conta como a "junta corrida" que a regra #1
  proíbe.
- **Motivo**: essas três são peças de **ajuste do fechamento contra o vão**,
  não blocos de preenchimento do corpo da parede. A junta corrida que a
  regra #1 combate é a do corpo da alvenaria (onde ela realmente enfraquece
  a amarração); a última junta contra a abertura é consequência do vão ter
  uma posição fixa nas duas fiadas.
- **"Encostada num vão" cobre dois casos**, ambos medidos no projeto real:
  a borda da peça coincide com a borda de uma abertura **deste** eixo, ou
  com a **ponta do próprio eixo** — o segundo é o caso da parede de
  referência, em que a janela pertence ao eixo **colinear vizinho** e por
  isso nem aparece em `openings_per_wall` deste.
- **A exceção vale na VALIDAÇÃO, nunca na BUSCA.** `_pier_layout_avoiding_
  joints` e as listas `course_a_joint_positions_cm`/`own_family_joint_
  positions_cm` continuam contando **todas** as juntas: a regra diz que
  essa junta *pode* coincidir, não que deva ser ignorada. Assim o solver
  continua preferindo uma composição que desencontra de verdade quando ela
  existe, e a exceção só impede que o resultado seja **reprovado** quando
  não existe. (Aplicar a isenção também na busca quebrou dois testes
  existentes — `test_fiada_b_desencontra_junta_vertical_da_fiada_a` e
  `test_solve_building_blocks_all_courses_variantes_evitam_alternating_
  joint_pattern` — porque o layout idêntico ao da Fiada A passava a
  empatar com as alternativas reais e vencia por ser o baseline.)
- **Prioridade**: **EXCEÇÃO PERMITIDA** à regra #1 (seção 11), que continua
  obrigatória e bloqueante para todo o resto.

### 11.9 — Bug real corrigido: `STRAIGHT_CONTINUATION` reservava espaço de uma amarração inexistente (2026-08-28)

- **Status**: **CORRIGIDO (sessão 2026-08-28)** —
  `_wall_end_default_start_cm` (`core/engine/wall_stepper.py`). Teste:
  `test_straight_continuation_nao_reserva_espaco_de_amarracao`.
- **Sintoma**: o usuário modulou **à mão** uma parede de 319cm (`L_CORNER`
  de um lado, `STRAIGHT_CONTINUATION` do outro) que fecha perfeitamente, e
  o solver a reportava como "modulação não fecha" por poucos centímetros
  nas duas fiadas.
- **Causa-raiz**: `_wall_end_default_start_cm` só isentava `FREE_END` —
  qualquer outro tipo de nó reservava meia espessura da parede mais larga
  (`_node_default_reservation_cm`) mais uma junta. Essa reserva existe para
  cobrir o **corpo de uma peça de amarração da parede vizinha** que
  atravessa a região; numa **continuação reta essa peça não existe**:
  `solve_all_intersections` ignora explicitamente
  `FREE_END`/`STRAIGHT_CONTINUATION`/`AMBIGUOUS` ("não são encontros de
  amarração especial") e nunca gera candidato ali. O solver reservava ~8cm
  para o nada, e o trecho livre deixava de fechar.
- **Prova**: com a reserva zerada, a Fiada A da parede de referência passou
  a sair **idêntica à do usuário, peça por peça e posição por posição**:
  `B34 + 7×B39 + C04` em X = 857,7 / 895,2 / 935,2 / 975,2 / 1015,2 /
  1055,2 / 1095,2 / 1135,2 / 1157,7.
- **`AMBIGUOUS` continua reservando, de propósito**: neste projeto ele
  aparece onde **duas paredes ocupam o mesmo eixo em planta em faixas de
  altura diferentes** (peitoril × acima da verga — ver seção 15), e ali
  existe peça de verdade. Zerar a reserva nesses nós **dobrou as colisões**
  na medição ao vivo (44 mil → 73 mil) e quase dobrou as paredes reprovadas
  na auditoria de amarração (62 → 116).

## 12. Orientação dos compensadores (regra #3, 2026-08-25)

> **Status**: IMPLEMENTADO (sessão 2026-08-25), com uma premissa física
> **não confirmada** — ver `COMPENSATOR_CLOSED_SIDE_IS_PLUS_X_WHEN_
> UNMIRRORED` em `core/wall_modeling.py`. Esta sessão não teve acesso ao
> Revit/à família real do compensador para medir qual extremidade da peça
> é de fato o "lado fechado" antes de qualquer espelhamento — o catálogo
> sempre tratou C09/C04 como maciços, sem nenhuma noção de orientação
> (seção 1). Confirme contra a família real na próxima sessão com acesso
> ao Revit; se sair invertido, é UMA constante para trocar.

Pedido explícito do usuário: "o compensador possui um lado aberto e um
lado fechado... o lado fechado deve estar sempre voltado para a
abertura... ele precisa manter o mesmo sentido construtivo de um bloco
cortado... a orientação deve ser determinada automaticamente de acordo
com a posição da abertura... o algoritmo também deve validar a
orientação dos compensadores e corrigir automaticamente qualquer um que
esteja invertido".

- `orient_compensator_candidates` (ETAPA 4D) roda **depois** de todo o
  preenchimento comum de todas as bandas (nunca durante a geração) — um
  passo dedicado de VALIDAÇÃO+CORREÇÃO, exatamente como pedido: para todo
  compensador (C09/C04) de toda parede, recalcula do zero se ele está
  encostado numa abertura de verdade e, se estiver, em qual lado — e
  escreve/CORRIGE `candidate["mirrored"]` de acordo, mesmo que já
  tivesse um valor de uma rodada anterior. Não há distinção entre
  "definir pela primeira vez" e "corrigir": é a mesma operação, sempre a
  fonte da verdade final.
- Só compensadores **encostados de verdade** numa abertura (sem junta de
  argamassa — `COMPENSATOR_OPENING_ADJACENCY_TOLERANCE_CM`) recebem uma
  orientação exigida; um compensador de preenchimento comum longe de
  qualquer abertura fica com `mirrored=False`, nunca espelhado sem
  motivo (a regra é especificamente sobre aberturas, seção 3).
- Aplicado no Revit em `create_building_blocks` via
  `ElementTransformUtils.MirrorElement` (plano com normal = `x_dir` da
  peça, passando pelo ponto de inserção) — o mesmo padrão já usado para
  `rotation_deg`/`RotateElement`.

## 13. Pipeline integrado e relatório final (itens 4–7 do pedido do usuário, 2026-08-25)

> Pedido explícito: "análise, correção, modulação e validação funcionem
> como um único algoritmo inteligente e iterativo", com um relatório
> final indicando quantas paredes foram analisadas, quantas tinham erro,
> quantas foram corrigidas, quantas modularam com sucesso, quantas
> ficaram sem solução e o motivo de cada uma.

### 13.1 — O pipeline já era integrado na parte de aritmética/geometria (Etapa 3B)

`process_walls_one_by_one` já processava uma parede por vez, lançando os
blocos, verificando se fechou e só então pedindo um ajuste geométrico
quando necessário (regras #3/#4/#5 do usuário, 2026-08-21) — isso não
mudou. O que estava faltando era a auditoria de amarração (Etapa 4C, uma
passada por cima de TODAS as paredes já lançadas) participar do MESMO
ciclo de correção — resolvido na seção 11.4 (um conflito de alinhamento
agora dispara o mesmo `plan_hook` que um trecho não-modular).

### 13.2 — `build_final_modulation_report`: relatório único, juntando as duas fontes de problema

Antes desta sessão não existia um relatório único: `error_rows` (Etapa
3B: a modulação aritmética de algum trecho não fecha) e `wall_bond_
audits` (Etapa 4C: a amarração entre fiadas reprova) eram reportados
separadamente, e nada impedia uma leitura contraditória ("a parede
passou na análise" vs. "a parede não recebeu bloco"). `build_final_
modulation_report` (chamado em `_on_create_done`, o último passo da
janela única, quando as duas fontes já existem) consolida:

- **Paredes analisadas** = `len(walls_to_create)` (todos os eixos).
- **Inicialmente com erro** = `len(error_rows)` (Etapa 3B, antes de
  qualquer correção — o tamanho da lista nunca muda, só o status
  `resolved` de cada linha).
- **Corrigidas automaticamente** = quantas linhas de `error_rows` têm
  `resolved=True` depois de "Ajustar Erros".
- **Moduladas com sucesso** = paredes que NÃO aparecem nem em
  `error_rows` sem `resolved` nem em `wall_bond_audits` reprovado — só
  conta como sucesso quando passa nas DUAS etapas (regra #5: nunca faz
  sentido uma parede estar "correta" numa análise e "com problema" na
  outra ao mesmo tempo).
- **Sem solução** = o resto, cada uma com o motivo exato de cada etapa
  que reprovou (prefixado "Etapa 3B"/"Etapa 4C" — uma parede pode
  aparecer nas duas listas de motivo ao mesmo tempo).

### 13.3 — Nenhuma parede é ignorada silenciosamente, mas também nenhuma "sem solução" é escondida

Regra #4 do usuário: "o processo deve garantir que... caso uma parede
não possa ser modulada diretamente, o sistema deve tentar primeiro
aplicar as pequenas correções geométricas permitidas. Somente depois de
esgotar as possibilidades válidas a parede poderá ser marcada como não
resolvida... nenhuma parede deve simplesmente ser ignorada
silenciosamente". A auditoria de amarração agora **exclui da criação**
(seção 11.5) as poucas paredes que sobrevivem a tudo isso — mas a parede
de referência NUNCA é apagada nesse caso (ver 13.4), e o relatório final
sempre lista o motivo exato. "Sem solução" é um resultado honesto e
esperado para um resíduo pequeno de casos, não um bug — o que seria
errado é escondê-lo atrás de um "sucesso" que não é real.

### 13.4 — Bug real corrigido: "Lançar Blocos - criar" não era idempotente

Reportado pelo usuário com uma imagem: parte da modulação de uma parede
"andava" (posição nova) e parte "ficava parada" (posição antiga) depois
de recalcular. Causa: `create_building_blocks` nunca apaga nada, só cria
— e os dois botões de "Lançar Blocos" ficam habilitados de novo depois de
cada uso (ex.: recalcular depois de "Ajustar Erros" mudar uma abertura, e
criar de novo). Um segundo clique em "criar" empilhava um SEGUNDO lote de
instâncias por cima do primeiro: as peças de encontro L/T/X (que não
mudam de posição entre dois cálculos — o nó é o mesmo ponto físico)
ficavam perfeitamente sobrepostas (invisíveis, pareciam "não ter
mudado"), enquanto o preenchimento comum (que muda quando uma abertura se
deslocou) sobrava DUPLICADO nas duas posições ao mesmo tempo.
`_execute_create` agora apaga o lote anterior POR COMPLETO antes de criar
o novo — cada clique em "criar" é uma SUBSTITUIÇÃO atômica, nunca uma
soma. Pela mesma razão, "Finalizar - Excluir paredes de referência" nunca
apaga a parede de referência de um eixo que ficou sem bloco (seção 11.5)
— isso deixaria o vão completamente vazio, nem parede nem bloco.

## 14. Auditoria de conformidade (sessão 2026-08-26) — o script atende ao que
este documento descreve?

> Pedido explícito do usuário: complementar/confirmar os padrões já
> documentados (ver `PADRAO_MODULACAO.md`, agora com um 2º projeto
> diagnosticado — `diagnosticos/CHACARA-TORRE-EASY-LO.md`) e **confirmar se
> o script (`core/wall_modeling.py`) atende a esses padrões**, antes de
> qualquer alteração de código. Esta seção é esse relatório. **Nenhuma
> mudança de comportamento foi feita em `wall_modeling.py` nesta sessão** —
> só leitura/grep/checagem de existência das funções citadas pelas seções
> 1-13 acima e rastreamento dos pontos onde cada uma é chamada.

### 14.1 — Metodologia

Duas checagens, ambas só leitura (grep + leitura pontual, não o arquivo de
~17.000 linhas inteiro): (a) toda função citada por nome nas seções 1-13
acima existe de fato em `core/wall_modeling.py`, com a assinatura/papel
compatível com a descrição; (b) rastreamento de TODOS os call-sites das
funções centrais do solver de blocos (`solve_opening_modulation`,
`pack_pier_with_blocks`, `wall_length_closes_with_blocks_cm`,
`evaluate_wall_modulation`) para confirmar de onde, no pipeline, a
modulação é de fato consultada.

### 14.2 — Resultado (a): funções citadas existem, rótulos batem

Toda função citada como `IMPLEMENTADO` nas seções 1-13 (catálogo/
`load_fixed_block_catalog`; prioridade de preenchimento/`_pier_ordered_
layout`+`_pier_forced_bypass_layouts`; meio-bloco/`_merge_adjacent_
compensator_pairs`; zona de exclusão de porta/`find_door_void_
violations`; L-T-X/`solve_l_corner`+`solve_t_intersection`+`solve_x_
intersection`+respectivos `validate_*`; alinhamento vertical obrigatório/
`_pier_layout_avoiding_joints`; orientação de compensador/`orient_
compensator_candidates`; pipeline+relatório/`build_final_modulation_
report`, não listada aqui por já estar coberta pela seção 13; seção 10.1/
10.4/10.5/`detect_opening_system_for_level`+`detect_wall_openings_from_
courses`+`is_cut_block_justified_by_opening`+`audit_existing_masonry_
openings`) **existe no arquivo, com o nome exato citado**. Nenhuma
divergência (função citada como implementada que não existe, ou existe
com comportamento visivelmente diferente do descrito) foi encontrada.

Os itens marcados `DOCUMENTADO (aguardando confirmação)` ou `PADRÃO
OBSERVADO AINDA NÃO CONFIRMADO` (10.2 sequência de fiadas da verga em
canaleta, 10.3 comprimento de apoio da verga, 10.6 valor fixo de
desencontro de junta) e o `CONFLITO ABERTO` (10.7, canaleta na última
fiada) **de fato não têm nenhuma função correspondente no arquivo** —
checado por grep de termos como "canaleta.*sequ", "bearing"/"apoio_
verga" sem ocorrência de geração de geometria nova para esses casos.
Correto: o código não implementa regra que a própria documentação marca
como não confirmada — nenhuma correção necessária aqui.

**Veredito 14.2**: ✅ **atende** — o que este documento descreve como
implementado está implementado; o que descreve como pendente está, de
fato, pendente. Documentação e código não divergem.

### 14.3 — Resultado (b): a CRIAÇÃO das paredes (antes de `Wall.Create`) não
consulta nenhuma regra de modulação — achado central, não é bug

Rastreando os 4 call-sites de `solve_opening_modulation`/`pack_pier_with_
blocks`/`wall_length_closes_with_blocks_cm`/`evaluate_wall_modulation`:
todos ficam dentro do próprio solver (`evaluate_wall_block_length`,
`solve_opening_jamb`, `_solve_axis_width_increase`) ou são chamados pela
primeira vez em `evaluate_wall_modulation(created_wall_ids_all, doc)`
(`core/wall_modeling.py:16278`) — **depois** que o loop de criação
(`Wall.Create`, `core/wall_modeling.py:16132`, dentro da `Transaction`
iniciada em `core/wall_modeling.py:16101`) já terminou de rodar sobre
`walls_to_create`, uma lista montada só a partir da geometria do CAD
(`find_wall_pairs`, `extend_wall_ends_to_junctions`, `deduplicate_walls`,
`assign_openings_to_walls`, `clip_centerline_to_caps` — nenhuma dessas
chama qualquer função do solver de blocos).

Isso **não é uma divergência entre documento e código** — o próprio
docstring do módulo já descreve exatamente isso: a criação preserva "a
prioridade e' sempre preservar exatamente a geometria e o comprimento
calculados a partir do CAD", e só depois "a MODULACAO DE BLOCOS
ESTRUTURAIS e' o proximo passo". `PADRAO_MODULACAO.md`/este documento
também nunca afirmaram o contrário. **É o gap real entre o que existe
hoje e o pedido original desta sessão** (paredes já nascerem "pensando"
na modulação): hoje a modulação é **100% reativa** (roda depois de criar,
corrige com o menor ajuste possível quando não fecha — ETAPA 3B/seção 7);
não existe nenhum **pré-check proativo** antes de `Wall.Create` que
consulte o catálogo/regras de amarração para preferir, dentre geometrias
de CAD equivalentes, a que fecha modulação sem precisar de ajuste depois.

**Veredito 14.3**: ⚠️ **não atende** (mas por desenho, não por descuido) —
construir esse pré-check é trabalho novo, não um gap pequeno e mecânico
(critério da seção "Abordagem" combinado para esta sessão: só implementar
correção quando o gap reaproveita função já existente sem inventar
aritmética nova). Fica **documentado como pendência para uma sessão
dedicada**, não implementado agora. Esboço de desenho, para quando for
autorizado: um novo módulo `core/engine/modulation_patterns.py` (mesmo
padrão de `core/engine/tolerances.py`/`geometry.py`, só dados/funções
puras) centralizando os limiares hoje espalhados em `wall_modeling.py`
(`T_INTERSECTION_B54_HALF_ROOM_FT`, `CORNER_B34_ROOM_FT`, `PIER_MODULE_
CM`, `BONECA_ADJUST_MAX_CM`, `AXIS_OPENING_SHIFT_MAX_CM`, `AXIS_TRIM_MAX_
CM`, `OPENING_WIDTH_INCREASE_MAX_CM`), consultado por um novo passo entre
`walls_to_create` já montado e o início da `Transaction` de criação —
reaproveitando a MESMA hierarquia boneca→shift→trim→widen e o mesmo
`verify` contra o solver real que `plan_axis_opening_fix` já usa, só
chamada mais cedo (antes de criar) em vez de só depois (ETAPA 3B).

### 14.4 — Resumo objetivo desta auditoria

- Regras confirmadas em 2 projetos distintos nesta sessão: 4 (catálogo
  núcleo, passo de fiada 20cm, offset de 1ª fiada +1cm, fluxo operacional
  paredes→blocos→excluir) — ver `PADRAO_MODULACAO.md`.
- Funções citadas como implementadas e verificadas existentes: todas as
  citadas nas seções 1-13 (nenhuma divergência).
- Gaps entre documentação e código encontrados: **zero** (documentação e
  código concordam em tudo que foi checado).
- Gap entre o pedido original do usuário e o estado atual do código: **1**
  (criação de parede não é modulation-aware ainda) — documentado acima,
  **não implementado nesta sessão** por decisão explícita do usuário de
  auditar/confirmar primeiro.

## 15. Paredes de peitoril e de verga: altura e cota de base variam por parede (2026-08-28)

> **Status**: **DOCUMENTADO — pendência de código aberta.** Medido ao vivo
> via MCP no projeto `TESTE MODULAÇÃO` (306 paredes). O solver e a criação
> já sabem trabalhar por faixa vertical (`course_candidates`, seção 4); o
> que **não** existe ainda é derivar `num_courses` e `base_z_abs` **por
> parede** — hoje os dois são globais.

### 15.1 — O achado

Nem toda parede da seleção vai do nível ao pé-direito. Num projeto real de
alvenaria estrutural, o trecho **abaixo do peitoril** e o trecho **acima da
verga** costumam ser paredes SEPARADAS, cada uma com sua própria
`WALL_USER_HEIGHT_PARAM` e seu próprio `WALL_BASE_OFFSET`. Medição no
projeto de referência:

| Altura | Offset da base | Qtd | O que é |
|---|---|---|---|
| 300cm | 0cm | 203 | parede cheia (piso ao teto) |
| 80cm | 220cm | 57 | trecho acima da verga |
| 100cm | 0cm | 20 | peitoril (abaixo da janela) |
| 60cm | 240cm | 10 | trecho acima da verga |
| outras (20–160cm) | 140–260cm | 16 | mistas |

Duas dessas paredes podem ocupar **exatamente o mesmo eixo em planta** (um
peitoril de 0–100cm e um trecho de verga de 220–300cm no mesmo lugar) sem
serem duplicatas: elas não se tocam, porque vivem em faixas de altura
diferentes. Uma varredura ingênua por "mesmo eixo em planta" as acusa como
duplicadas — **não são**, e `deduplicate_walls` (que só olha planta) as
apagaria indevidamente. Note que `deduplicate_walls` hoje só roda no fluxo
clássico do CAD (`main()`), nunca em `run_modulation_on_existing_walls`.

### 15.2 — Consequência para o grafo de encontros: os `AMBIGUOUS`

É essa sobreposição em planta que produz a maioria dos nós `AMBIGUOUS`.
Medição: dos 92 nós `AMBIGUOUS` do projeto, apenas **4** são o caso
documentado de duas paredes num ângulo oblíquo (nem 90° nem 180°); os
outros **88 têm 3 a 7 pontas de parede chegando ao mesmo ponto**, e em
**todos** eles duas pontas apontam para a **mesma direção** (0° entre si) —
a assinatura de peitoril + verga colineares terminando juntos. Com braços a
mais, o nó deixa de casar com os padrões de `T_INTERSECTION` (duas pontas
colineares opostas + uma perpendicular) e de `X_INTERSECTION` (dois pares
colineares perpendiculares entre si), e cai no ramo final `AMBIGUOUS`.

Por isso `AMBIGUOUS` **continua reservando** espaço de amarração (seção
11.9): ali existe peça de verdade, só que na outra faixa de altura.

### 15.3 — Pendência: `num_courses`/`base_z_abs` são globais

`_select_existing_walls_for_modulation` devolve **um** `max_height_ft` (a
MAIOR altura entre as paredes selecionadas) e
`run_modulation_on_existing_walls` usa **um** `base_z_abs`
(`selected_level.Elevation`) para toda a modulação. Numa seleção
homogênea isso é correto; numa seleção com peitoris/vergas, não:

- uma parede de 80cm recebe as mesmas 15 fiadas de uma de 300cm — **~11
  fiadas a mais do que cabem nela**;
- uma parede com `base_offset` de 220cm tem os blocos criados a partir da
  cota do NÍVEL, e não de 220cm acima dele — o lote inteiro nasce **220cm
  abaixo** do lugar certo, atravessando as paredes vizinhas.

Medido: com altura/base globais, o solver acusou **43.988 colisões** no
projeto de 306 paredes. As peças de peitoril/verga fora de lugar são a
fonte dominante.

**Desenho combinado com o usuário (2026-08-28)**: agrupar as paredes por
`(altura, offset_de_base)` e rodar solver + criação **uma vez por grupo**,
cada um com seu próprio `num_courses` e sua própria cota inicial. Isso
reaproveita todo o pipeline existente sem mexer na arquitetura. A correção
definitiva — derivar altura e base **por parede** dentro de um único
solve — fica registrada como pendência para uma sessão dedicada.

## 16. Regra #2 tem prioridade sobre o desencontro, e o guloso não é suficiente (2026-08-28)

> **Status**: **IMPLEMENTADO (sessão 2026-08-28)**. Dois bugs distintos,
> os dois medidos ao vivo via MCP sobre o projeto `TESTE MODULAÇÃO` (126
> paredes, todas conectadas e com altura 300cm). Testes:
> `test_desencontro_de_junta_nunca_empilha_compensadores` e
> `test_busca_exata_fecha_trecho_que_o_guloso_nao_fecha`.

### 16.1 — `_score` do desencontro ignorava a regra #2

`_pier_layout_avoiding_joints` comparava candidatos só por
`(coincidência_de_junta, -alinhamento_de_vazio)`. Num trecho de 29cm
fechado dos dois lados, o baseline `B19+C09` coincidia a junta com a Fiada
A, e a busca trocava por **`C04+C09+C09+C04`** — quatro compensadores em
sequência — só porque desencontrava. Esse layout é reprovado logo em
seguida por `validate_wall_modulation`
(`sem_compensadores_consecutivos`): não era uma solução melhor, era uma
**não-solução** que só parecia boa no critério errado.

`_score` agora é `(excesso_de_compensadores_em_sequência,
coincidência_de_junta, -alinhamento_de_vazio)` — a regra #2 na frente
(`_layout_compensator_run_excess`, medida contínua para preferir a menor
violação quando toda alternativa viola). Trocar uma junta coincidente —
que o pipeline registra em `alignment_conflicts` e escala para ajuste
geométrico (seção 11.4) — por uma parede **reprovada** nunca é um bom
negócio.

### 16.2 — O guloso nunca volta atrás: trechos com solução limpa caíam no tier dos compensadores

`_greedy_fill_blocks` pega sempre a maior peça que ainda cabe e não faz
backtracking. Consequência medida: **33 eixos** reprovados pela regra #2
tinham **todos** uma composição sem nenhum compensador disponível — o
tier 3 (B39+B34) falhava e a parede caía no tier 5.

- Trecho de **469cm**: o guloso põe 11×B39, sobram 29cm, o B34 não cabe
  mais e o tier 3 devolve `None` → o tier 5 fecha com `11×B39 + 3×C09`.
  Mas `10×B39 + 2×B34` fecha os mesmos 469cm com **zero** compensadores
  (existem 5 composições limpas para esse trecho).
- Trecho de **139cm**: fecha com **4×B34 e nenhum B39** — nenhuma escolha
  de *primeiro* bloco leva o guloso até lá.

Correção em duas camadas, ambas usadas pelos tiers 3 e 5
(`_greedy_fill_blocks_any_first`):

1. se o guloso puro não fechar, tentar cada código do pool como **primeiro
   bloco** (resolve o caso de 469cm);
2. se ainda assim não fechar, `_exact_fill_blocks` — **programação
   dinâmica** em décimos de centímetro, critério "menos peças primeiro"
   (que naturalmente prefere as peças maiores, mesma intenção do guloso),
   peças ordenadas da maior para a menor (resolve o caso de 139cm).

Nenhuma das duas altera um caso em que o guloso puro já fecha — só
ampliam o alcance dos tiers **bons**, evitando que a parede desça para um
tier pior sem necessidade. Resultado medido no projeto real: eixos com
problema caíram de **82 para 72**, e os reprovados por compensadores
adjacentes de **40 para 24**.
