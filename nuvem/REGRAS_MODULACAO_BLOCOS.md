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
> Última atualização: 2026-08-31 — nova seção 24 (BENCHMARK: projeto
> entregue vira gabarito medível, com o piso de ruído medido contra o
> projeto humano, o CONFLITO da regra #2 registrado em 24.3 e as medições
> novas de 24.5). Antes disso, 2026-08-28 — nova EXCEÇÃO à regra #1 (seção 11.8:
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

## 8c. Unir paredes já existentes no Revit (2026-08-28)

Terceira opção **independente** da tela *"Preparação das paredes"*
(`_WallSourceModeForm` → `_ask_wall_source_mode` → `run()`), pedida pelo
usuário para poder **comparar dois caminhos** que chegam ao mesmo lugar
(uma parede contínua com recortes nativos) por rotas opostas. Nenhuma das
opções anteriores foi alterada ou removida:

| Opção da tela | O que faz | Fonte da geometria |
|---|---|---|
| Criar paredes a partir da planta (CAD) | `main()` — com a sub-opção 8b (segmentado **ou** contínuo com recortes) | planta baixa (DWG) |
| Utilizar paredes existentes | `run_modulation_on_existing_walls()` — só modula, nunca cria/apaga | Walls já modeladas |
| **Unir paredes existentes** | `run_merge_existing_walls()` — reconstrói as Walls fatiadas como **uma parede contínua** e recria os vazios como Abertura de Parede | **Walls já modeladas** |

### Regra: nesta opção a planta baixa NÃO é usada

Toda a análise sai do próprio modelo — `Location.Curve`, `Wall.Width`,
`WallType`, Nível, deslocamentos de base/topo, Linha de Referência, flip e
uso estrutural (`read_existing_wall_for_merge`). Nada é lido do CAD.

### Continuidade lógica — quando duas paredes podem ser unidas

`wall_merge_compatibility_key` + `walls_share_infinite_line` +
`group_existing_walls_for_merge`. Duas paredes só entram no mesmo grupo se
**todas** estas condições valerem:

- mesmo **Nível** de base;
- mesmo **WallType** e mesma **espessura**
  (`WALL_MERGE_THICKNESS_TOLERANCE_M = 0.002`);
- mesma **Linha de Referência** (a curva de localização de duas paredes só
  é comparável quando medida no mesmo plano de referência);
- mesmo **uso estrutural**;
- sobre a **mesma reta em planta** — paralelas dentro de
  `WALL_MERGE_ANGLE_TOLERANCE_DEG = 0.25` e sem desvio lateral acima de
  `WALL_MERGE_LATERAL_TOLERANCE_M = 0.005`;
- **encostadas/sobrepostas** ao longo dessa reta, ou separadas por um vão
  de no máximo `WALL_MERGE_MAX_AXIAL_GAP_M = 3.0`.

Paredes em **arco** ficam de fora (não podem virar um único segmento reto
contínuo), assim como paredes sem eixo, curtas demais ou sem altura
determinável — cada recusa vai ao relatório com o motivo, nunca some em
silêncio.

O limite de vão axial só entra em cena quando **nenhum** trecho do grupo
cobre aquele intervalo — é o caso das paredes separadas nas laterais de uma
abertura que vai do piso ao teto. Quando existe verga acima da porta ou
peitoril abaixo da janela, a continuidade já está provada pela geometria e
o vão nem chega a aparecer. Atravessar um vão desses **não muda a geometria
final**: o vazio vira um recorte de altura cheia na parede contínua.

### Os vazios são calculados, não adivinhados

`compute_wall_merge_voids` é a operação **inversa** de
`build_wall_segments`: lá as aberturas fatiam a parede em trechos; aqui os
trechos existentes revelam onde estavam as aberturas. Dado o retângulo
cheio (comprimento total × da base mais baixa ao topo mais alto) e os
retângulos que os trechos ocupavam, o complemento exato é decomposto em
retângulos — corta o eixo nas faixas delimitadas pelas pontas dos trechos,
tira o complemento vertical dentro de cada faixa e junta faixas vizinhas
com o mesmo conjunto de vazios (um vão único sai como **um** retângulo).
Vazios abaixo de `MIN_SEGMENT_LENGTH_FT`/`MIN_SEGMENT_HEIGHT_FT` são
descartados — o Revit recusaria o recorte.

### Ordem obrigatória (`execute_wall_merge_plan`)

1. lê o que estava **hospedado** nas paredes antigas (portas/janelas e
   `Opening`s) — antes de mexer em qualquer coisa;
2. cria **uma** parede contínua, do nível de base até a altura total
   (`Wall.Create` com o WallType, o Nível, o offset de base e a altura das
   originais);
3. desliga o auto-join das duas pontas, fixa a **mesma Linha de
   Referência** das originais (aqui o alvo é reproduzir onde a parede **já
   estava**, não um eixo medido no CAD — diferença deliberada em relação ao
   fluxo do CAD, que alinha pelo núcleo) e reescreve a `LocationCurve`;
4. `doc.Regenerate()`;
5. só **então** abre os recortes dos vazios, com a **mesma**
   `create_wall_opening_cuts` do modo contínuo (item 8b) — inclusive a
   folga `OPENING_CUT_EDGE_OVERSHOOT_M` de 1cm, só na aresta que encosta na
   base/topo da parede;
6. recria na parede contínua o que estava hospedado
   (`recreate_wall_inserts`);
7. `Regenerate` + **valida**;
8. **só se passar**, apaga as paredes antigas e faz `Commit`.

### Preservação das aberturas

- **Vazios entre trechos** → `Opening` retangular novo, com a posição, a
  largura, a altura e o peitoril que a geometria dos trechos definia.
- **`Opening`s que já existiam** nas paredes antigas → recriados na parede
  contínua com os **mesmos dois cantos** (`Opening.BoundaryRect`). Um
  `Opening` de contorno **não retangular** reprova a união daquele grupo em
  vez de ser perdido.
- **Portas/janelas hospedadas** → recriadas na parede contínua com o mesmo
  símbolo, o mesmo ponto de inserção, o mesmo Nível, a mesma orientação
  (facing/hand) e os parâmetros de instância `Largura_abertura`,
  `Altura_abertura` e `Peitoril` copiados. Sem isso, apagar a parede
  hospedeira apagaria a porta junto.

### Validar antes de apagar — e nunca deixar estado intermediário

`validate_merged_wall` mede **de volta no próprio Revit**: a parede existe
e é válida, tem eixo, o comprimento bate, as duas pontas caem onde o plano
mandou (em planta), base e topo batem, todos os recortes planejados foram
abertos e nenhuma reinserção falhou — tudo dentro de
`WALL_MERGE_VALIDATION_TOLERANCE_M = 0.005`.

Cada continuidade roda na **sua própria `Transaction`** (todas dentro de um
`TransactionGroup`, para o Ctrl+Z desfazer a operação inteira de uma vez).
Reprovou → `RollBack`: as paredes originais daquela continuidade continuam
**intactas**, e as demais continuidades seguem normalmente. Se só parte das
paredes antigas puder ser apagada, também é `RollBack` — parede antiga
sobrevivente por baixo da contínua seria exatamente a duplicata/sobreposição
que as regras proíbem.

Uma parede que já está inteira (sozinha no grupo e sem nenhum vazio) **não
gera plano**: não é recriada nem apagada, só reportada como intocada.

### Depois da união

O fluxo oferece seguir direto para a modulação dos blocos sobre as paredes
contínuas recém-criadas, reusando `run_modulation_on_existing_walls
(preselected=...)` — e é isso que permite comparar este caminho com o modo
contínuo do fluxo do CAD (8b) no mesmo projeto. A modulação em si continua
idêntica: o solver trabalha sobre os eixos e sobre `openings_per_wall`,
nunca sobre os elementos `Wall` (fingerprint de `tests/solver_bench.py`
inalterado).

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

## 17. Dois bugs de RELATÓRIO já diagnosticados e ainda NÃO corrigidos (2026-08-28)

> **Status**: **DIAGNOSTICADO — pendência de código aberta.** Nenhum dos
> dois afeta a geometria dos blocos criados: os dois estragam o que o
> usuário VÊ depois (o realce vermelho e a contagem de peças). Medidos ao
> vivo via MCP no projeto `TESTE MODULAÇÃO` (126 paredes, 13.766 blocos).

### 17.1 — `_colliding_created_instance_ids` infla o realce em ~127×

`solve_building_blocks_all_courses` gera `variants_per_course`
(`PIER_LAYOUT_VARIANTS_PER_COURSE`) composições ALTERNATIVAS para a mesma
fiada e as agrega todas em `candidates`; `course_candidates` é que decide
qual delas vira peça em cada fiada física. A detecção de colisão roda
sobre `candidates` INTEIRO, então ela compara candidatos que **nunca
coexistem no modelo** — duas variantes da mesma fiada ocupam o mesmo
espaço por construção.

`_colliding_created_instance_ids` marca uma instância criada se o seu
`candidate_key` aparecer em QUALQUER par de colisão, sem verificar se o
OUTRO lado do par também foi criado, nem se os dois caíram na mesma fiada
física. Medição real:

| | |
|---|---|
| pares de colisão reportados | 52.575 |
| descartados: um dos lados nunca foi criado | 50.210 |
| descartados: os dois existem, mas em fiadas diferentes | 2.310 |
| **colisões REAIS** | **55** (88 peças) |
| peças que o cálculo atual marcava | 11.211 |

Com isso o realce cobria **91%** das peças e não informava nada; o
critério correto marca **0,6%**. **Correção pendente**: exigir que os DOIS
lados do par tenham sido criados E compartilhem o mesmo `course_index`
antes de marcar (foi o critério usado manualmente para produzir o realce
útil desta sessão). O mesmo vale para `collisions` quando ele é usado como
número no relatório final — hoje ele mede candidatos, não peças.

### 17.2 — `MirrorElement` deixa peças órfãs a cada lançamento

`create_building_blocks` usa `MirrorElement` para orientar compensadores
(regra #3, seção 12). Essa API **cria uma cópia** em vez de espelhar no
lugar, e a cópia não entra em `created_instances`. Consequências:

- o documento fica com mais blocos do que `created_count` informa (medido:
  14.276 no modelo × 13.766 registrados = **510 órfãs**, exatamente o
  `mirror_calls` do perfil de tempo);
- a exclusão do lote anterior em `_execute_create` (seção 13.4) apaga por
  Id e portanto **nunca remove as órfãs** — elas se acumulam a cada clique
  em "Lançar Blocos - criar", que é o mesmo cenário do bug de
  reposicionamento parcial de 2026-08-25 entrando pela porta dos fundos.

**Correção pendente**: registrar em `created_instances` o Id devolvido
pelo espelhamento (ou usar o overload que espelha sem copiar) e apagar a
peça original quando a cópia a substituir. Enquanto isso não existe, a
limpeza correta é apagar TODA instância das famílias do catálogo cujo Id
não esteja em `created_instances`.

## 18. Revisão geral pedida pelo usuário a partir de prints do Revit (2026-08-28)

> **Origem**: o usuário mandou 9 capturas do modelo `TESTE MODULAÇÃO` já
> modulado (13.768 blocos, 126 paredes) apontando erros, junto de um
> documento com 11 exigências. Esta seção registra **todas** elas, cada uma
> com o status real de implementação — nenhuma foi implementada em
> silêncio, e nenhuma foi descartada. A ordem de prioridade que o usuário
> definiu está em 18.10 e vale para qualquer decisão futura do solver.

### 18.1 — Amarração em cruz: B54 correto, sem peça sobreposta

- **Status**: `PARCIAL` — o X_INTERSECTION já usa dois B54 a 90° com
  células centrais alinhadas e prova geométrica (`validate_x_intersection`,
  seção 5). O que **falha** é a convivência com o preenchimento e com nós
  vizinhos: ver 18.7.
- **Regra**: toda cruz usa B54; o vão menor resultante fica alinhado; não
  pode existir peça adicional ocupando o mesmo volume; a amarração tem de
  se manter nas fiadas seguintes. Uma solução que só parece certa
  visualmente, sem a geometria correta, é erro.

### 18.2 — Pilarete entre duas portas é modulado de forma independente

- **Status**: **IMPLEMENTADO (2026-08-28)** — `plan_pier_opening_nudges`
  (`core/wall_modeling.py`) + `PIER_NUDGE_MAX_CM = 3.0`. Teste:
  `test_pilarete_entre_aberturas_propoe_deslocamento_pequeno`.
- **Causa-raiz do que faltava**: `plan_axis_opening_fix` trabalha no EIXO
  INTEIRO e desiste com "topologia do eixo fora do escopo do ajuste
  automático" sempre que uma abertura encosta na ponta/junção. Medido ao
  vivo: as 77 aberturas do projeto real encostam na ponta do seu segmento,
  então **nenhum** eixo com abertura conseguia plano — 0 auto-corrigíveis
  em 72 eixos com erro. O novo planejador não depende da topologia do
  eixo: olha um trecho por vez e o que o cerca. Resultado medido: **7
  eixos passaram a ter proposta**, com deslocamentos de 1 a 2cm.
- **Escopo**: só propõe mover uma borda que seja de ABERTURA (um nó de
  amarração nunca se move por aqui) e só até `PIER_NUDGE_MAX_CM` — o
  "empurrão" mínimo que o usuário descreveu, bem abaixo dos 5cm do ajuste
  de eixo inteiro. Calcula, nunca aplica.
- **Regra**: o trecho entre duas aberturas tem de ser resolvido **por si**,
  não como sobra do prisma geral da parede. Um pilarete de ~50cm deve
  buscar a melhor combinação para aquele trecho (ex.: B39 + C09 com as
  juntas), e **se faltar pouco**, o sistema pode deslocar uma das portas
  dentro da tolerância (ex.: 1cm) para permitir a modulação.
- **Ordem**: primeiro tentar modular o pilarete como está; só depois
  considerar mover a abertura adjacente. Nunca deixar o pilarete sem
  modulação apenas porque a posição original da abertura não fecha.
- **Relação com o que existe**: `plan_axis_opening_fix` (seção 7) já sabe
  deslocar abertura, mas só é acionado quando o eixo TEM abertura e falha
  como um todo — não a partir do pilarete individual.

### 18.3 — Alinhamento obrigatório de faces em aberturas e pontas

- **Status**: `DOCUMENTADO — pendência de verificação.`
- **REGRA OBRIGATÓRIA**: as faces dos blocos devem coincidir exatamente
  com (1) a face lateral das aberturas, (2) o fim das paredes e (3) as
  faces definidas pelos encontros. É proibido bloco ultrapassando a face
  do vão, terminando antes dela, ou com desalinhamento pequeno na
  extremidade. A modulação junto de uma abertura é calculada a partir dos
  limites geométricos exatos dela.

### 18.4 — Padronização das fiadas: ímpares iguais entre si, pares iguais entre si

- **Status**: **IMPLEMENTADO (2026-08-28)** —
  `PIER_LAYOUT_VARIANTS_PER_COURSE` voltou de 3 para **1**. Teste:
  `test_fiadas_de_mesma_paridade_repetem_com_o_default`.
- **Medição da troca K=3 → K=1** no projeto real (126 paredes, 15 fiadas):
  junta corrida **95 → 80** (melhorou — é a regra #1, absoluta), faixa de
  compensador repetida **28 → 108** (piorou), paredes reprovadas na
  amarração 61 → 65. A fiada 2 passou a ser **idêntica** à 4; as fiadas 0 e
  2 diferem em **uma única peça**, e essa diferença vem das BANDAS de
  abertura (seção 4) — ou seja, exatamente a "razão geométrica" que a
  própria regra admite como exceção.
- **TRADE-OFF REGISTRADO**: a faixa vertical de compensador repetida é
  consequência direta de repetir o layout, e segue sendo reportada pela
  auditoria. A solução fina — variar a composição APENAS nos trechos que
  usam compensador, mantendo o resto repetido — fica como pendência.
- **Regra**: Fiada 1 ≡ Fiada 3 ≡ Fiada 5…, e Fiada 2 ≡ Fiada 4 ≡ Fiada 6…
  Dois padrões alternados (A e B), repetidos até o topo. O sistema não
  deve inventar uma solução diferente por fiada sem uma razão geométrica
  (abertura naquela faixa vertical) ou uma regra que exija.
- **Conflito registrado com a seção 11.7**: `PIER_LAYOUT_VARIANTS_PER_COURSE`
  (K=3) foi criado justamente para VARIAR o preenchimento entre fiadas de
  mesma paridade, para escapar de `ALTERNATING_JOINT_PATTERN`. Medido em
  2026-08-28: as 15 fiadas usam as variantes 0,0,1,1,2,2,0,0,1,1,2,2,0,0,1
  — ou seja, a fiada 1 **não** é igual à 3. Como `ALTERNATING_JOINT_PATTERN`
  deixou de bloquear (ver 11.5), a razão original de K>1 caiu. **A
  orientação mais recente do usuário tem prioridade**: o padrão deve voltar
  a repetir. Pendência: reavaliar K=1 medindo o efeito em
  `CONTINUOUS_VERTICAL_JOINT`.

### 18.5 — B34 só entra com o vão menor sob controle

- **Status**: `PARCIAL` — garantido e validado em L_CORNER e T degradado
  (seção 5); **não** garantido no B34 de meio de parede (limitação já
  registrada na seção 6).
- **Regra**: sempre que houver B34 na amarração, o vão menor entre os
  blocos envolvidos fica alinhado. O B34 não pode ser usado só para
  preencher espaço de forma arbitrária — a posição dele faz parte da
  lógica contínua da amarração e das fiadas.

### 18.6 — Transição B34 para B39 exige olhar a fiada seguinte

- **Status**: **IMPLEMENTADO (2026-08-28)** —
  `_layout_min_joint_stagger_cm` + `MIN_JOINT_STAGGER_TARGET_CM = 10.0`
  (`core/engine/wall_stepper.py`), como critério de desempate em
  `_pier_layout_avoiding_joints`. Teste:
  `test_desempate_prefere_a_composicao_que_trava_melhor`.
- **Como foi resolvido**: o que faltava não era prever a fiada seguinte, e
  sim medir o TRAVAMENTO. Duas composições podem ter zero coincidência de
  junta (as duas passam na regra #1) e ainda assim uma travar muito melhor
  que a outra — a que deixa a junta mais longe da junta oposta é a que
  "permite a continuidade do prisma". O score agora é
  `(excesso_de_compensador, coincidência_de_junta, -travamento,
  -alinhamento_de_vazio)`, com o travamento saturando no alvo de 10cm.
- **Valor do alvo**: conservador de propósito, abaixo dos ~15cm medidos num
  projeto real (seção 10.6), que continuam rotulados como PADRÃO OBSERVADO
  AINDA NÃO CONFIRMADO. É preferência, nunca bloqueio.
- **Regra**: a troca de B34 para B39 só pode acontecer quando a próxima
  fiada tiver vão suficiente para o B39 encaixar mantendo a continuidade
  do prisma. O procedimento é: ler a posição do B34 na fiada atual →
  analisar a fiada seguinte → verificar o vão → só então permitir a
  transição. A modulação precisa considerar mais de uma fiada ao mesmo
  tempo.

### 18.7 — Proibido bloco dentro do volume de outro (colisão medida)

- **Status**: **DETECTADO, mas NÃO bloqueia a criação** (regra de
  2026-08-26: o diagnóstico não pode impedir a geração dos blocos).
- **Medição 2026-08-28** (`validate_same_course_collision` sobre uma fiada
  física real, OBB/SAT — não bounding box): **9 colisões por fiada A**,
  zero nas fiadas B:
  - 4x **B34 do preenchimento dentro do B54** de um T_INTERSECTION;
  - 4x **B19 do preenchimento dentro do B54** de um T_INTERSECTION;
  - 1x **B54 x B54** de dois nós em T diferentes na MESMA parede, próximos
    demais para os dois caberem.
- **REGRA OBRIGATÓRIA**: nenhum bloco pode ser inserido dentro do volume
  de outro. A única sobreposição legítima é a prevista pelas regras de
  amarração (peças de fiadas diferentes). Qualquer outra é erro e a peça
  não deve ser criada.
- **Cuidado de método**: medir com **OBB (SAT)**, nunca com bounding box
  alinhado aos eixos — o AABB de um bloco em parede diagonal ou rotacionada
  superestima muito. Uma medição por AABB nesta mesma sessão acusou 10.319
  pares onde o teste correto encontra ~9 por fiada.

### 18.8 — Nenhuma parede pode ficar sem modulação sem motivo registrado

- **Status**: `PARCIAL` — `build_final_modulation_report` (seção 13.2) já
  separa moduladas com sucesso de sem solução com o motivo, mas por EIXO;
  não há o estado intermediário por trecho.
- **Regra**: cada parede ou trecho (incluindo pilaretes, bonecas, trechos
  curtos, finais de parede e regiões perto de cruzamentos) recebe um de
  três estados: **(1) Modulado com sucesso**; **(2) Necessita ajuste
  geométrico** — fecha se uma abertura/elemento adjacente for deslocado
  dentro da tolerância; **(3) Não modulável** — e aí o sistema informa
  exatamente qual regra impediu. É proibido deixar parede sem modelagem
  sem identificar o motivo.

### 18.9 — T sem espaço vira L usando C09/C04

- **Status**: `IMPLEMENTADO PARCIALMENTE` — o Nível 3 de
  `solve_t_intersection` (seção 5) já fecha a boneca com **1 único** C09 ou
  C04 quando nem o B34 cabe. A novidade do usuário é tratar isso
  explicitamente como **reinterpretação em L**, e não como degradação.
- **Regra**: se a boneca de um T não tem comprimento para acomodar a
  lógica do B54, então: não forçar o B54; não criar sobreposição; não
  deixar sem modulação; reinterpretar como amarração em L, usando C09 ou
  C04 para finalizar a geometria.

### 18.10 — Ordem de prioridade quando a situação é difícil

Definida pelo usuário, vale para qualquer decisão do solver:

1. **Manter as amarrações corretas** — nunca sacrificar uma amarração para
   preencher espaço.
2. **Garantir a modulação completa** — toda parede, pilarete, boneca e
   trecho é analisado.
3. **Manter o padrão entre fiadas** — ímpares entre si, pares entre si.
4. **Alinhar faces** — portas, aberturas, finais de parede e encontros.
5. **Ajustar aberturas quando permitido** — dentro da tolerância.
6. **Evitar soluções improvisadas** — não usar bloco aleatório só para
   fechar um vão pequeno.

### 18.11 — Checklist da validação final

Antes de dar a modulação por concluída: todas as paredes processadas, sem
paredes parcialmente moduladas nem trechos sem bloco; faces alinhadas com
as aberturas e nenhum bloco invadindo vão; pilaretes modulados; cruzes com
B54 correto e vãos menores alinhados; B34 respeitando o alinhamento; T sem
espaço reinterpretado como L; nenhuma sobreposição inválida e nenhum bloco
dentro de outro; Fiada 1 igual à Fiada 3 e Fiada 2 igual à Fiada 4, com
continuidade lógica entre elas.

> **Objetivo declarado pelo usuário**: o sistema não é um preenchedor de
> paredes com blocos — é um motor de modulação que analisa ao mesmo tempo
> geometria, comprimentos, aberturas, pilaretes, bonecas, amarrações L/T/X,
> continuidade vertical, repetição entre fiadas, alinhamento de faces e os
> ajustes de abertura permitidos. Correções devem virar **regra geral**,
> nunca conserto do exemplo específico.
### 18.12 — Fechamento contra o vão: a junta de contorno junto à abertura é negociável (2026-08-28)

- **Status**: **IMPLEMENTADO (2026-08-28)** — fallback de junta em
  `_pier_ordered_layout` (`core/engine/wall_stepper.py`, parâmetro interno
  `_allow_opening_joint_fallback`).
- **Regra (palavras do usuário)**: *"lembre-se da regra dos vão, nesses
  casos você pode colocar bloco de 34 até o final e uma pastilha ou um
  compensador dependendo da fiada"* — ou seja, um trecho que morre num vão
  não pode ficar VAZIO: fecha-se com peça inteira até o fim e a peça de
  ajuste (C04 ou C09) que couber naquela fiada.
- **Causa-raiz do que impedia isso**: `_pier_remaining_snapped_cm` exige que
  o trecho, descontadas as juntas de contorno, seja múltiplo de
  `PIER_MODULE_CM` (5cm). A junta de contorno é 0cm contra abertura e 1cm
  contra bloco/nó — e essa escolha era **fixa**. Com as duas pontas em
  abertura (0 e 0), trechos perfeitamente preenchíveis eram reprovados e
  ficavam **sem nenhuma peça**: os vazios que o usuário fotografou.
- **O que mudou**: quando o trecho não fecha E a ponta é de ABERTURA, o
  solver tenta a junta alternativa daquele lado (0 ↔ 1) antes de desistir —
  encostar a peça direto no vão ou deixar a junta de assentamento normal.
  Contra um **nó de amarração a junta continua fixa**: ali ela é estrutural
  e não se negocia.
- **Medição (mesmos trechos, antes → depois)**: 5cm `None` → `C04`;
  10cm → `C09`; 25cm → `B19+C04`; 30cm → `B19+C09`; 55cm → `B19+B34`;
  75cm → `B39+B34`; 85cm → `B39+B39+C04`. No projeto real, os eixos
  reprovados por "trecho fora de módulo" caíram de **18 para 10**, e o
  total de eixos com erro de 73 para **71**.
- **Nota sobre o alcance da regra**: a formulação "B34 até o final" cobre os
  trechos GRANDES; medindo os casos reais, a maioria dos vazios era **menor
  que um B34** (5 a 37cm), e ali quem fecha é B19/C09/C04. A implementação
  cobre os dois, porque libera a junta e deixa a hierarquia normal da
  seção 2 escolher a peça.
- **Prioridade**: **REGRA OBRIGATÓRIA** — um trecho contra vão nunca pode
  ficar sem peça só por causa da junta de contorno.

### 18.13 — Ajuste do pilarete: ALARGAR a abertura, não deslocá-la (2026-08-28)

- **Status**: **IMPLEMENTADO (2026-08-28)** —
  `plan_pier_opening_widenings` / `apply_pier_opening_widenings`
  (`core/wall_modeling.py`), com `PIER_MIN_USEFUL_CM = 5.0` como piso.
- **Regra (pedido do usuário)**: *"pode alterar a dimensão das aberturas,
  de preferência aumentando elas"*. Por isso o alvo do ajuste é sempre o
  módulo válido **inferior** — alargar o vão, nunca estreitá-lo.
- **Por que alargar é melhor que deslocar** (medido ao vivo): a família
  `Abertura de janela para paredes de blocos` cresce **por um lado só**
  (largura +2cm ⇒ centro anda 1cm), então a borda oposta fica parada e o
  trecho do outro lado não é afetado. **Deslocar movia as duas bordas**, e
  como há paredes "gêmeas" que compartilham a mesma abertura, o empurrão que
  consertava um eixo quebrava o vizinho — medido: o eixo 4 pedia −1cm
  exatamente no trecho em que o eixo 6 pedia +1cm, impossível satisfazer os
  dois movendo. O deslocamento aplicado foi revertido e substituído por
  alargamento.
- **Proteções obrigatórias**: (1) set `ja_alargadas` compartilhado entre
  eixos, para a mesma abertura nunca ser alargada duas vezes — sem ele, dois
  eixos gêmeos aplicavam +1cm cada e o vão crescia o dobro do planejado
  (bug real medido nesta sessão); (2) `PIER_MIN_USEFUL_CM` recusa qualquer
  alvo que zere o pilarete — um eixo chegou a propor "4cm → 0cm", que não é
  modular, é apagar a parede naquele ponto; (3) `Regenerate()` +
  `IsValidObject` + RollBack por abertura, a mesma rede de segurança do
  `MoveElement` (ver o bug de 2026-08-24 em que 8 aberturas sumiram em
  silêncio).
- **Parâmetro alterado**: `Largura_abertura`, de **instância** e editável —
  não exige criar tipos novos na família.

## 19. Edição dinâmica no Modelador Externo (2026-08-28)

> **Status**: **IMPLEMENTADO no `AbrirModeladorExterno.pushbutton`**. Esta
> regra é de interação do preview externo; ela não grava uma edição no
> documento Revit até que exista um fluxo explícito de aprovação/importação.

- Parede, abertura, encontro/amarração e blocos são dependências do mesmo
  modelo: uma alteração geométrica nunca pode manter candidatos de blocos
  calculados para a geometria anterior.
- Ao arrastar uma Wall contínua, suas extremidades podem ser movidas ou o
  eixo inteiro pode ser transladado. Quando o eixo representa vários
  fragmentos colineares de origem, todos são transformados na mesma razão
  paramétrica, impedindo fendas entre fragmentos.
- Aberturas hospedadas acompanham a alteração da Wall na mesma posição
  relativa ao eixo. Uma abertura arrastada ou editada numericamente só pode
  permanecer inteiramente dentro do prisma da sua hospedeira. Posição no
  eixo, largura, altura e peitoril são propriedades explícitas do usuário e
  devem ser validadas em conjunto, de forma atômica. A edição explícita não
  é revertida só por piorar a pontuação do solver; uma geometria válida que
  não module deve permanecer aplicada e expor o diagnóstico correspondente.
- Mover, redimensionar, duplicar ou excluir uma abertura e regenerar seus
  blocos constitui **uma única operação de histórico**. Desfazer/refazer
  restaura juntos a captura editada e o resultado calculado, sem deixar
  blocos pertencentes a uma revisão anterior.
- Toda edição válida chama o **mesmo** `solve_capture_block_candidates` da
  modulação inicial. Não há um algoritmo simplificado para pós-edição:
  portas, vãos, vergas, quinas, amarrações, tolerâncias e catálogo são
  recalculados pelas regras originais.
- A atualização identifica a componente L/T/X conectada e informa as Walls
  afetadas. O motor continua isolando o cálculo por nível e faixa de base,
  para que uma alteração não seja tratada como mudança no projeto inteiro.
- Nenhuma Wall sem resultado pode ser omitida: o payload expõe por Wall um
  estado (`MODULABLE`, `NON_MODULAR`, `ALIGNMENT_CONFLICT`,
  `VALIDATION_FAILURE` ou `NOT_PROCESSED`) e o motivo concreto mostrado no
  inspetor do visualizador.

## 20. Calculadora manual de alternativas de modulação (2026-08-28)

> **Status**: **IMPLEMENTADO no `AbrirModeladorExterno.pushbutton`** para
> parede individual e lista de paredes independentes. O motor fica separado
> da interface e recebe o catálogo exportado do Revit quando há uma captura
> carregada; sem captura usa o catálogo oficial padrão B54/B39/B34/B19/C09/C04.

- A entrada é comprimento, amarração esquerda/direita, fiada, catálogo,
  restrições e critério de ordenação. A composição sempre é validada por
  `soma dos blocos + juntas internas de 1cm`; nunca por soma nominal ou por
  uma subtração manual de reserva.
- Uma ponta L/quina exige B34; cruzamento exige B54. Um T sem o papel
  geométrico declarado apresenta as duas hipóteses possíveis — parede
  principal com B54 e boneca com B34 — marcadas explicitamente como hipótese,
  nunca como certeza geométrica.
- B19 só pode fechar uma ponta livre; não entra no meio nem junto de L/T/X.
  C09/C04 não podem ser consecutivos e há no máximo um compensador por trecho.
- Todas as soluções retornadas são classificadas por validade construtiva,
  número de compensadores/pastilhas/meio-blocos, peças especiais e quantidade
  total de blocos. A calculadora mostra várias ordens das peças, suas posições
  e o motivo das hipóteses/rejeições.
- O modo de lista calcula cada Wall de forma independente. **Otimização global
  ainda é pendência intencional**: ela só será marcada como resolvida quando a
  calculadora receber o grafo L/T/X da captura e chamar o solver completo; não
  pode fingir consistência global com comprimentos isolados.

## 21. Motor único no Modelador Externo e recálculo incremental (2026-08-28)

> **Status**: **IMPLEMENTADO no `AbrirModeladorExterno.pushbutton`**. A
> calculadora deixa de ser o motor simplificado da captura: para um modelo
> carregado ela chama a mesma entrada canônica `solve_building_blocks` do
> `core.engine.wall_stepper` usada na modulação inicial e depois das edições.

- A fonte de verdade é única: catálogo da captura/Revit, `wall_stepper`,
  validações e as regras deste documento. A tela não decide blocos, juntas,
  amarrações ou exceções; apenas pede o solve e apresenta o resultado.
- O cálculo completo recebe geometria, nível/base Z, bandas reais de
  aberturas, fiadas A/B, setores de parede e grafo L/T/X. Assim portas,
  janelas, pilaretes, quinas, cruzamentos, alinhamento vertical e restrições
  de peças são reavaliados no mesmo pipeline, nunca por uma combinação
  aritmética paralela.
- Cada edição determina a componente de Walls conectadas e as faixas
  independentes `(nível, base_z)`. Só essas faixas são recalculadas; os
  candidatos e estados de grupos sem dependência são preservados. Se uma
  amarração estiver na componente, a região é expandida em favor da correção.
- Durante o arraste, a interface solicita uma prévia com debounce de 180ms.
  A prévia é efêmera e não altera o modelo salvo; ao soltar, o solver executa
  novamente e só então o resultado é aplicado. Cancelar restaura o último
  estado confirmado.
- A renderização pode reconstruir somente as Walls da componente afetada,
  mas isso é uma otimização de apresentação: não autoriza simplificar nem
  duplicar as regras do solver na interface. Revisões antigas ou respostas
  de prévia fora de ordem são descartadas e nunca substituem um estado mais
  recente.
- A saída do motor expõe blocos escolhidos, setores/recortes por abertura,
  grafo de dependências, estados por Wall e regiões sem solução com motivo.
  Uma região inválida nunca é preenchida por aproximação silenciosa.
- A calculadora de comprimento isolado permanece apenas como explorador de
  alternativas sem geometria. Ela não pode ser declarada validação global nem
  substituir o solve da captura.

## 22. Diagnóstico visual obrigatório para regiões reprovadas (2026-08-28)

> **Status**: **IMPLEMENTADO no `AbrirModeladorExterno.pushbutton`**.

- Nenhuma Wall ou trecho sem solução pode desaparecer do modelo externo. A
  Wall recebe estado e motivo explícitos; candidatos que ainda pertençam a
  uma Wall reprovada permanecem visíveis em **vermelho**.
- O vermelho é diagnóstico, não aprovação: os blocos continuam vinculados ao
  código/motivo (`NON_MODULAR`, `ALIGNMENT_CONFLICT` ou
  `VALIDATION_FAILURE`) para que o usuário localize a região e aplique apenas
  os ajustes permitidos. Blocos de Walls válidas mantêm a cor do catálogo.
- A prioridade é tentar todas as alternativas permitidas pelo solver —
  inclusive o fechamento contra vão da seção 18.12 — antes de sinalizar a
  região. Quando ainda não houver solução, informar é obrigatório; inventar
  uma modulação proibida continua vedado.
## 23. PIPELINE OFICIAL DE ABERTURAS — parede completa primeiro (2026-08-28)

**REGRA OBRIGATÓRIA — muda a ORDEM do algoritmo, não um parâmetro dele.**
Pedido explícito do usuário, com fluxo desenhado item a item ("essa passa a
ser a nova ordem oficial de processamento… não voltar à lógica anterior…
essa abordagem deve ser abandonada como estratégia principal").

### 23.1 A ordem, antes e agora

| | ANTES (`split_first`) | AGORA (`continuous_first`, padrão) |
|---|---|---|
| 1 | detectar paredes | analisar a arquitetura |
| 2 | criar paredes | **gerar as paredes completas** |
| 3 | detectar portas/janelas | analisar as amarrações |
| 4 | **recortar as paredes nas aberturas** | **modular os blocos na parede completa** |
| 5 | modular cada trecho isolado | validar a modulação |
| 6 | ajustar | **recortar as aberturas** |
| 7 | — | identificar e **deletar** os blocos sobre o vão |
| 8 | — | **ajustar a parede o mínimo possível** |
| 9 | — | **recalcular só o que for necessário** |
| 10 | — | validação final |

Constantes e funções: `core/engine/continuous_modulation.py`
(`OPENING_STRATEGY_CONTINUOUS_FIRST` = `DEFAULT_OPENING_STRATEGY`,
`OPENING_STRATEGY_SPLIT_FIRST` só para comparar as duas ordens no mesmo
projeto). Integração: `solve_wall_free_fill(..., opening_strategy=...)` e
`_recut_openings_and_repair`, em `core/engine/wall_stepper.py`.

### 23.2 O que exatamente mudou no solver

- **As aberturas deixaram de ser fronteira do preenchimento.** No modo
  contínuo, `base_boundaries` tem só `WALL_START`, `MIDSPAN_LO/HI` (encontro
  no meio da parede) e `WALL_END`. Um eixo de 8m com duas portas é **um**
  problema de 8m, não três de 2m.
- **As amarrações continuam intocadas.** Encontros L/T/X são resolvidos
  ANTES (`solve_all_intersections`, inalterado) e reservam o mesmo espaço de
  sempre — eles nunca foram fronteira de abertura, e continuam sendo
  fronteira de trecho. A abertura não pode fazer uma amarração ser perdida.
- **O recorte é geométrico, por volume real** (item 18 do pedido): uma peça
  é derrubada se o CORPO dela (`[t_start, t_end]`, via
  `_candidate_t_range_on_wall`) invade o vão em mais de
  `OPENING_OVERLAP_TOLERANCE_CM` (0,2cm) — nunca pelo ponto central. Peça
  que só ENCOSTA na borda (junta de abertura = 0cm) continua valendo.
- **Bloco nunca é cortado nem redimensionado** (item 10): é removido
  INTEIRO. `split_extents_by_openings` classifica em `FORA` / `DENTRO` /
  `PARCIAL`; os dois últimos saem.
- **Só a região afetada é recalculada** (item 22). As peças derrubadas
  contíguas viram uma REGIÃO de reparo, ancorada na face da peça que
  sobreviveu de cada lado (`opening_repair_regions`); os trechos sólidos
  dentro dela (`region_solid_subsegments`) são re-resolvidos pelo solver de
  pilarete DE SEMPRE (`_pier_ordered_layout` / `_pier_layout_avoiding_joints`)
  — nenhuma regra de layout nova. Fora da região, a modulação contínua fica
  intacta.
- **Duas aberturas próximas caem na MESMA região** (item 16, pilarete entre
  aberturas): quando não sobra peça inteira entre elas, o pilarete só pode
  ser decidido olhando as duas de uma vez.
- **A região cresce uma peça por vez, e só pelo lado que falhou**
  (`OPENING_REPAIR_MAX_EXTRA_BLOCKS = 3`). Se no fim nada fechar, **as peças
  engolidas pela busca voltam**: derrubar bloco bom sem colocar nada no
  lugar seria abrir um buraco para "resolver" um problema que continua sem
  solução.
- **`solve_opening_jamb` não é mais chamado no modo contínuo.** Não existe
  mais uma "peça de jamb" decidida antes do resto — a peça que encosta no
  vão é a que o reparo local escolheu, com as mesmas prioridades. O
  alinhamento de vazio entre as fiadas junto ao vão continua garantido pelo
  critério PRINCIPAL de `_pier_layout_avoiding_joints`
  (`target_void_positions_cm`), que sempre cobriu a parede inteira.
  `jamb_exceptions` sai vazio nesse modo.

### 23.3 Ajuste mínimo (itens 11 a 14) — e a ordem de prioridade

`plan_minimum_opening_adjustment` só é consultado **depois** de o recálculo
local ter falhado — porque o item 24 põe a POSIÇÃO DA ABERTURA (4º) acima da
MODULAÇÃO DOS BLOCOS (5º): mexer na arquitetura é o último recurso, não o
primeiro.

1. `{"kind": "none"}` — já compatível: **não alterar nada** (item 13);
2. `{"kind": "shift"}` — menor translação rígida do vão (largura preservada),
   até `AXIS_OPENING_SHIFT_MAX_CM` (5cm);
3. `{"kind": "widen"}` — alargar o mínimo, até
   `OPENING_WIDTH_INCREASE_MAX_CM` (5cm). **Nunca reduzir** o vão;
4. `None` — nenhuma solução dentro dos tetos: reportar CONFLITO
   (`"conflict": "ABERTURA_NAO_COMPATIVEL"`), nunca fabricar modulação
   errada (teste 9).

O mínimo é mínimo de verdade: a busca varre os deslocamentos que as FACES
reais geram, em ordem de `|delta|` — não "tenta 1cm, 2cm, 3cm". As faces de
referência são as do layout **contínuo inteiro** (antes do recorte), nunca as
do que sobrou: usar o que sobrou empurraria a proposta para a junta seguinte
e faria o motor "descobrir" que precisa de 13cm quando a junta certa está a
1cm.

### 23.4 Duas correções de REGRA que a nova ordem tornou necessárias

Não são ajustes cosméticos — sem elas a nova ordem PIORA a amarração, e
foram medidas, não supostas.

**(a) `MAX_SPECIAL_BOND_PER_TRECHO = 1`** (`wall_stepper.py`). O trecho agora
vai de nó a nó, e o tier 3 de `_pier_ordered_layout` (B39+B34, sem limite de
quantidade) fechava a sobra com uma FILEIRA de B34 no meio da parede —
medido: `4×B39 + 3×B34` seguidos em [475, 579] numa parede de 6m, que a
própria auditoria reprovava logo depois
(`REPEATED_VERTICAL_COMPENSATOR_STRIP`, B34 repetido em 8 fiadas). Mesmo teto
e mesmo espírito de `MAX_COMPENSATORS_PER_TRECHO`: peça de acerto é PONTUAL,
nunca sequência. É a regra #2 do usuário aplicada também na GERAÇÃO, e não só
na auditoria. Com trechos curtos (a ordem antiga) isso quase nunca aparecia.

**(b) `_continuous_segment_layout`** — entre composições **igualmente
válidas** do mesmo trecho, prefere a que coloca a peça de acerto
(compensador/pastilha/meio bloco/peça especial) onde ela é natural: perto de
uma abertura ou perto da ponta da parede, usando exatamente as zonas que a
auditoria já isenta (`BOND_STRIP_OPENING_INFLUENCE_CM = 60`,
`BOND_STRIP_EDGE_EXEMPT_CM = 25`, movidas para `continuous_modulation.py`
para não viverem em dois arquivos). Nenhuma peça nova, nenhuma prioridade de
tier alterada — só a POSIÇÃO da sobra. Necessário porque o guloso empurra a
sobra para o FIM do trecho, e o fim de um trecho contínuo é um encontro de
amarração: o pior lugar possível para um compensador.

### 23.5 Degradação controlada — o único caminho de volta ao `split`

A nova ordem resolve o eixo inteiro de uma vez, o que também significa que um
eixo cujo COMPRIMENTO TOTAL não fecha em blocos não lançaria **nada**, nem
nos pedaços que fechariam. Quando (e só quando) isso acontece, aquele trecho
é refeito usando as aberturas como ponto de quebra — a ordem antiga, aplicada
como degradação LOCAL e registrada em `continuity_degraded` (chave sempre
presente no retorno de `solve_wall_free_fill`, vazia no caminho normal).
Mesma disciplina dos encontros degradados (`L_CORNER_DEGRADED` e família):
melhor uma solução pior e rotulada do que nenhuma solução. Isso **não** é a
lógica anterior de volta: ela nunca é o caminho principal, e nunca acontece
em silêncio.

### 23.5b A ordem vale para a GEOMETRIA também, não só para o solver

**REGRA OBRIGATÓRIA — correção do usuário, medida ao vivo (2026-08-28).** Na
primeira execução real deste pipeline via MCP, as 128 paredes foram criadas
**já com os 77 recortes de abertura**, na mesma transação, antes de existir um
único bloco — e só depois a modulação foi resolvida. O usuário interrompeu:
*"você gerou as paredes com recortes sem lançar os blocos antes"*.

Estava certo. Ter o solver na ordem nova não basta: a ordem é do **processo
inteiro**, e a geometria de referência (as `Wall` e seus `Opening`) faz parte
dela. A sequência obrigatória ao gerar no Revit é:

1. criar as paredes **completas** — `build_wall_segments(...,
   WALL_BUILD_MODE_CONTINUOUS)`, altura cheia, **sem chamar
   `create_wall_opening_cuts`**;
2. resolver a modulação (`solve_building_blocks_all_courses`) e **lançar os
   blocos** (`create_building_blocks`);
3. **só então** abrir os recortes (`create_wall_opening_cuts`) sobre as
   paredes já moduladas;
4. validar que nenhum bloco ocupa o vão.

`build_wall_opening_cuts` (que só CALCULA os retângulos) pode rodar antes — é
`create_wall_opening_cuts` (que ESCREVE no modelo) que precisa esperar. O
requisito antigo de recortar depois do realinhamento pelo núcleo (seção 8b)
continua valendo: agora ele é o piso, não o teto — o recorte vem depois do
núcleo **e** depois dos blocos.

Por que importa, mesmo o solver já ignorando os recortes: com a parede
recortada antes, qualquer etapa que leia a geometria REAL (a prévia, a
validação pós-criação, `evaluate_wall_modulation`, o realce por comprimento)
enxerga a parede já fragmentada pelo vão — exatamente o estado que a nova
ordem existe para evitar. A parede inteira tem de existir no modelo enquanto
os blocos são decididos.

### 23.6 O que foi MEDIDO (não suposto)

Varredura de 481 combinações reais (eixo de 300 a 800cm × posição de porta de
80cm, passo 20cm), mesmas paredes nas duas estratégias:

| | `split_first` | `continuous_first` |
|---|---|---|
| casos que fecham | 481 (100%) | 481 (100%) |
| **B34/B54 como enchimento** | **2460** | **0** |
| **B39 (bloco inteiro)** | 9587 | **11570 (+21%)** |
| B19 (meio bloco) | 1453 | 1430 |
| C09/C04 (compensador) | 1200 | **1924 (+60%)** |
| blocos dentro do vão | 0 | 0 |

Numa planta fechada de 4 paredes com 3 aberturas, 15 fiadas:

| | `split_first` | `continuous_first` |
|---|---|---|
| paredes reprovadas na amarração | 3/4 | 3/4 |
| **`CONTINUOUS_VERTICAL_JOINT`** (regra #1, absoluta) | **1** | **0** |
| `REPEATED_VERTICAL_COMPENSATOR_STRIP` | 2 | 5 |

**TRADE-OFF REGISTRADO.** O ganho é grande e está no lugar certo: peça de
amarração deixou de ser usada como enchimento (2460 → 0 — era exatamente o
que produzia as faixas verticais de peça especial), bloco inteiro subiu 21%,
e a junta corrida (regra #1, absoluta) zerou. O custo é +60% de
compensador/pastilha, e com `variants_per_course = 1` (regra 18.4) cada um
deles vira uma faixa vertical repetida em todas as fiadas da mesma paridade.
Continua sendo reportado pela auditoria para revisão manual.

### 23.7 Pendência aberta (DOCUMENTADO — pendência de código)

`_continuous_segment_layout` só atua na **variante 0 da fiada A**. A fiada B
é decidida por `_pier_layout_avoiding_joints`, cujo critério primário é o
desencontro de junta (regra #1, absoluta, que não pode ser rebaixada) — então
a peça de acerto de B ainda pode cair no meio da parede e formar faixa
vertical sozinha. A correção fina é gerar os candidatos reordenados DENTRO da
busca de `_pier_layout_avoiding_joints`, para que a posição da peça de acerto
entre como desempate **depois** do desencontro, nunca antes. Medido no
cenário de 4 paredes: sobram 5 faixas, das quais 3 na mesma parede.
Relacionada à pendência já registrada na regra 18.4 ("variar a composição
apenas nos trechos que usam compensador").

### 23.8 Critérios de aceitação — cobertos por teste

`tests/test_script.py`, seção "SECAO 19 - PIPELINE OFICIAL". Os 9 testes do
pedido, um a um: parede sem abertura (1), parede com porta sem bloco no vão
(2), porta na extremidade sem perder a amarração (3), pilarete pequeno entre
aberturas (4), cruzamento (5), mover a abertura (6), mover a parede (7),
ajuste mínimo de 1cm (8), solução impossível reportada como conflito (9).
Mais: peça removida inteira e nunca cortada, bloco bom devolvido quando o
reparo falha, teto de peça especial, posição da peça de acerto, e degradação
registrada.

`tests/solver_bench.py --fingerprint`: a assinatura MUDOU de propósito
(`9413aad0…` → `c74c9c1a…`) — é uma mudança de regra, não de desempenho.

## 24. BENCHMARK: projeto entregue vira gabarito medível (2026-08-31)

Pedido explícito do usuário: transformar projeto Revit já modulado e
aprovado em **base de referência estruturada, mensurável e reutilizável**,
com validadores independentes, comparação entre versões e testes de
regressão — para que "cada erro corrigido vire conhecimento permanente" e
o mesmo problema não seja corrigido duas vezes.

Implementação: `nuvem/benchmark/` (ver o `README.md` de lá para os
comandos, o formato e o passo a passo de extração). Fora de
`nuvem/core/**` de propósito — o loader do botão não baixa nem executa
nada disto.

### 24.1 — Princípio: regra OBRIGATÓRIA ≠ preferência

Uma solução diferente da do projetista humano **não é erro** se cumprir
todas as regras obrigatórias. Por isso todo achado do benchmark carrega
um nível:

- **NÍVEL 1 (obrigatório)** — prisma, vão livre, amarração válida, sem
  sobreposição, cobertura da parede, geometria válida, limite de
  compensadores. Falhar aqui é erro.
- **NÍVEL 2 (preferência)** — peça escolhida, sequência, quantidade de
  compensadores, solução preferencial. Divergir do humano aqui é
  informação, nunca reprovação.

O nível é propriedade da CLASSE DE ERRO, definida uma única vez em
`benchmark/validators/base.py`; `benchmark/knowledge/error_classes.json`
é **gerado** dali, nunca escrito à mão (28 classes hoje).

### 24.2 — O gabarito também é medido: o "piso de ruído"

**REGRA DE MÉTODO (nova).** Os validadores rodam também sobre o PRÓPRIO
GABARITO. O projeto humano foi entregue e aprovado, então todo achado que
aparece nele é (a) limitação da reconstrução geométrica ou (b) validador
exigindo mais do que o escritório pratica — nos dois casos, o piso de
ruído daquele validador.

Nenhum número do solver deve ser citado sem a coluna do humano ao lado.
Medido em TORRE EASY-LO-R00, nível 05. TP1 (12.758 peças reais, extração
100% leitura em 2026-08-31), com o MESMO código nos dois lados:

| Classe | Solver | Humano | Leitura |
|---|---|---|---|
| COMPENSATOR_CONSECUTIVE | 1567 | 52 | solver 30,1× |
| COMPENSATOR_EXCESS_IN_RUN | 1038 | 54 | solver 19,2× |
| PRISM_CONTINUOUS_JOINT | 968 | 122 | solver 7,9× |
| PRISM_STAGGER_BELOW_TARGET | 687 | 101 | solver 6,8× |
| COMPENSATOR_VERTICAL_STRIP | 180 | 26 | solver 6,9× |
| POSITION_OVERLAP | 18 | 1 | solver 18× |
| COVERAGE_GAP_IN_ROW | 289 | 615 | ruído do validador |
| JUNCTION_MISSING_BINDING | 8 | 365 | ruído do validador |
| JUNCTION_HALF_BLOCK_ADJACENT | 0 | 259 | ruído do validador |

Blocos: humano 12.703, solver 18.092 na mesma planta. Similaridade exata
10,9%; estrutural (contando substituição equivalente) 11,8%.

**PENDÊNCIA DE CÓDIGO ABERTA** — os dois maiores desvios reais medidos,
nesta ordem de prioridade: (1) compensadores consecutivos/excesso, (2)
junta corrida entre fiadas. Nenhum dos dois foi corrigido nesta sessão:
esta entrega é a INFRAESTRUTURA DE MEDIÇÃO, não a correção.

### 24.3 — CONFLITO REGISTRADO: regra #2 (meio-bloco perto da amarração)

`JUNCTION_HALF_BLOCK_ADJACENT` aparece **259 vezes no projeto humano
aprovado** e **0 vezes no solver**. A regra #2 (seção 11.6) diz que
meio-bloco não pode ficar encostado na amarração; o projeto de referência
faz isso sistematicamente.

Não é resolvido por suposição. Registrado como CONFLITO: ou a regra #2 é
mais restrita do que a prática real do escritório, ou a reconstrução de
encontros está marcando como "encontro" pontos que não são. **Pendência
de investigação** — decidir com o usuário e/ou com um segundo projeto
antes de mexer na regra ou no validador. Até lá o validador continua como
está (nível 1), e o piso de ruído documenta o desvio.

### 24.4 — Identidade nunca é ElementId

`ElementId` muda entre arquivos e **some** quando as paredes de referência
são apagadas — que é exatamente o que o processo real faz (Walls/Doors/
Windows = 0 nos projetos entregues, já registrado em PADRAO_MODULACAO.md).
Toda chave do benchmark é geométrica (`model.wall_stable_key` e família,
invariante ao sentido do desenho), e o casamento gabarito × resultado é
por tolerância geométrica em três níveis: pontas iguais → mesma reta com
sobreposição ≥60% → sem par (registrado, nunca casado à força).

### 24.5 — Medições novas confirmadas neste projeto (leitura, sem alterar o .rvt)

- **Passo de fiada = 20cm** — confirmado pela terceira vez, agora medido
  sobre as cotas Z povoadas do nível inteiro. ✅ bate com
  PADRAO_MODULACAO.md.
- **Meias-fiadas de ajuste FORA da grade de 20cm são legítimas**: 359 peças
  do nível 05. TP1 estão em cotas intermediárias (722, 742, 762, 782, 802,
  822, 842, 872), todas de peça CORTADA de 9cm — é o ajuste de altura
  antes da canaleta de topo. Confirma e detalha o "~+11cm na última fiada"
  que estava como PADRÃO OBSERVADO em PADRAO_MODULACAO.md. Consequência de
  código: a fiada é a POSIÇÃO na pilha, nunca `(z - base) / passo` (pelo
  índice de grade, 712 e 722 caíam na mesma fiada e uma apagava a outra).
- **Catálogo real tem 33 tipos**, o solver conhece 6. Canaleta, canaleta J,
  verga, contraverga, vedação e as variantes CORTADO continuam fora do
  escopo do solver. Entregar o catálogo cru a ele faz o solver recusar
  tudo ("os blocos usados têm alturas diferentes: 9, 19, 29cm") e gerar
  ZERO peça — o benchmark filtra e registra em
  `solver_notes.catalog_codes_dropped`.
- **Padrão de amarração observado** (1 projeto, rótulo OBSERVADO — não vira
  regra com uma amostra só): canto L resolvido com **B34 em 80% das fiadas
  ímpares** e 64% das pares, com B19 aparecendo como exceção real em 16%.
  Isso é evidência independente a favor da regra #5 já implementada
  (L = 2×B34).

### 24.6 — Todo erro corrigido vira teste

`tests/regression/` (84 testes, pytest). Os que nasceram de defeito real
medido, e que existem para o defeito não voltar em silêncio:

- fiada quase vazia ao lado de fiada cheia (o solver perdeu uma das
  famílias A/B numa parede — medido no piloto sintético);
- amarração conferida no NÓ e não na parede (a primeira versão reprovou
  120 encontros corretos, porque num canto L a peça que amarra está na
  parede vizinha);
- vazio preenchido por peça de OUTRA parede não é buraco (1.619 falsos
  positivos no projeto humano, corrigido com `analysis.OccupancyIndex`);
- passo de fiada ignora cotas pouco povoadas (dava 10cm em vez de 20);
- ponta encostada no meio de outra parede é T, não L (um pavimento
  inteiro saiu com 286 "L" e nenhum T por contar paredes em vez de
  braços);
- solver que gera zero peça é catálogo recusado, não parede não modulada.

`tests/regression/test_engine_constants_match.py` importa o motor de
verdade e falha se qualquer constante espelhada em
`benchmark/analysis.py` divergir — o benchmark repete os números do solver
para poder rodar sem Revit, e número repetido é número que um dia diverge.

### 24.7 — Score nunca esconde erro crítico

`benchmark/scoring.py`: contagem PASS/FAIL por categoria, taxa de sucesso
por parede, e `critical_errors`/`blocking` **fora da média**. Um score de
98% com 3 paredes não moduladas continua reprovando. `compare_runs`
classifica cada categoria em MELHORIA / REGRESSÃO / INALTERADO, e erro
crítico novo é **REGRESSÃO CRÍTICA** mesmo que o total de erros caia —
uma correção que quebra outra parte não pode ser aceita.

### 24.8 — O INPUT do benchmark passa a ser MEDIDO, não reconstruído

Correção do usuário (2026-08-31): há **dois documentos Revit abertos na
mesma instância** — o projeto CRU e o projeto JÁ MODULADO. O benchmark não
pode mais tomar `ActiveUIDocument.Document` como entrada, e o `input.json`
não pode mais ser deduzido do próprio gabarito (era circular: o problema
saía da solução).

**REGRA OBRIGATÓRIA — todo extrator recebe o `Document` explícito.**
`benchmark/extract/revit_input_real_dump.py` exige `DOC_TITLE_PREFIX` e
levanta se ele casar com zero ou com mais de um documento; não existe
fallback para o documento ativo. Trocar de aba no Revit no meio da
extração não pode mudar de onde os dados vieram.

**REGRA OBRIGATÓRIA — todo artefato carrega `source_document`**
(`title`, `path`, `role`). Dados dos dois documentos nunca podem se
misturar em silêncio.

**REGRA OBRIGATÓRIA — provar o par antes de comparar.** Mesmo projeto não
implica mesmo referencial. Medido em 2026-08-31 (MCP, read-only):

- os dois documentos contêm o MESMO CAD, `'T01 LIMPA'` — 9 layers, mesma
  contagem por layer (19533/13146/9258/2972/2153/1142/528/391/4) e mesmo
  comprimento total até 0,1 cm;
- **49.127 de 49.127 segmentos casam** com translação pura de
  `(7678,7371 ; 1102,9024) cm`, resíduo máximo **0,000141 cm**, rotação
  identidade, escala 1,000000000 (momentos de 2ª ordem iguais até a 9ª
  casa);
- Z: a base dos blocos do gabarito (341,0 cm) é exatamente o Z do
  `ImportInstance` do CAD naquele documento — **o plano do CAD é o plano
  da 1ª fiada**.

**PADRÃO OBSERVADO / CONFIRMADO — qual nível é o par.** O input casa
**91 de 91 aberturas com o nível `04. TGD`** e apenas 89 de 91 com os
`TP1`. As duas que diferenciam: uma porta de 121 cm (x=7654, coord. nativa
da TORRE) que no TP1 vira janela de 71 cm com peitoril 160, e uma abertura
de 91 cm deslocada 29 cm. Ou seja: **`torre_easy_lo_r00_tp1`, já existente
no repo, NÃO é o par deste input** — o par correto é
`torre_easy_lo_r00_tgd`. Escolher nível por nome de arquivo é erro de
método; escolher por conteúdo é a regra.

**MEDIÇÃO — o layer de parede é `Arquitetura`.** Descoberto por medição,
não pelo nome: é o único layer que explica os eixos do gabarito — 95,22%
dos pontos amostrados nos eixos caem a ≤ 8 cm de uma linha dele, e só
23,95% a ≤ 1 cm (o eixo passa ENTRE as duas faces, como tem de ser numa
parede de 14 cm). O segundo colocado, `Mobiliário`, fica em 6,84%.

**MEDIÇÃO — as aberturas são famílias de Mobiliário.** As 91 aberturas do
input são `FamilyInstance` de categoria Mobiliário hospedadas em Nível,
identificadas só pelos parâmetros `Largura_abertura` / `Altura_abertura` /
`Peitoril` (é o modo `auto` de `collect_opening_instances`). Não há nenhuma
Porta/Janela nativa em nenhum dos dois documentos.

**MEDIÇÃO — gabarito 04. TGD:** 12.564 instâncias, 97 paredes, todas de
14,0 cm, 17 fiadas, passo de 20 cm, altura dominante 260 cm (69 das 97).

**DOIS FINGERPRINTS DIFERENTES — não confundir.** São coisas distintas e
ambas legítimas. Desde 2026-08-31 os nomes na infraestrutura são
EXPLÍCITOS, justamente porque já foram confundidos uma vez:

- **`solver_decision_fingerprint`** =
  `c74c9c1ae0e3f169f76e05fe53c01a858fce0af5b4e9d5f1b86fd71e92d2a316` —
  `py tests/solver_bench.py --fingerprint`, constante
  `REFERENCE_SOLVER_DECISION_FINGERPRINT`. Mede as PEÇAS que o solver
  decide; só muda quando a modulação muda de resultado.
- **`wall_modeling_engine_sha256`** =
  `f017124964a806fba8d4249add34db665f86282ae2a8c6fecb1018713d3bad8a` —
  campo do `wall_modeling_snapshot.json`. Mede o sha256 do ARQUIVO
  `nuvem/core/wall_modeling.py`; muda a cada edição do fonte, mesmo que o
  resultado seja idêntico.

Os nomes antigos (`fingerprint`, `engine_fingerprint`,
`REFERENCE_FINGERPRINT`) não existem mais —
`tests/regression/test_wall_modeling_snapshot_serialization.py` falha se
`engine_fingerprint` reaparecer no snapshot.

**PENDÊNCIA DE CÓDIGO ABERTA — 167 paredes contra 97.** (A explicação dada neste parágrafo foi MEDIDA e REFUTADA na seção 24.9 — não é região extra, é fragmentação. Mantido aqui para o histórico.) O Wall Modeling
sobre o CAD cru forma 167 paredes; a pessoa modulou 97. O layer
`Arquitetura` cobre área maior que a região modulada (o input chega a
Y = −739 cm, o gabarito para em Y = −570 cm). Ainda **não está decidido**
se isso é recorte de escopo do projetista ou falha de filtro do benchmark
— não tratar como erro do solver antes de decidir. Na mesma rodada, 9 das
91 aberturas não foram atribuídas a nenhuma parede pela FASE A.


### 24.9 - Hardening da baseline real (Etapa 2B.1)

Correcao do usuario (2026-08-31), aplicada ANTES de congelar qualquer
numero como historico. Tres contaminacoes metodologicas foram removidas.

**REGRA OBRIGATORIA - o catalogo NUNCA pode vir do gabarito.** A primeira
rodada (2B) montou o catalogo do solver a partir do `reference.json`, ou
seja, das pecas que a PESSOA usou. Isso e' vazamento da solucao para dentro
da entrada. O catalogo agora sai dos `FamilySymbol` CARREGADOS no proprio
documento INPUT (`benchmark/extract/revit_catalog_dump.py`), pelos nomes
exatos de `BLOCK_FAMILY_CATALOG_DEFINITIONS`, sem depender de nenhuma
instancia colocada e sem `Activate()` (que exigiria Transaction).

MEDIDO: os 6 codigos (B19/B34/B39/B54/C04/C09) estavam todos carregados no
INPUT, com os simbolos ja ativos, entao ate' as CELULAS vieram da geometria
real (B19=1, B34=2, B39=2, B54=3, compensadores=0) - nada reconstruido.
Comparando com o catalogo do gabarito: **zero divergencia dimensional** nos
6 codigos. O gabarito tem 9 codigos a mais (B19_C, B34_C, B39_C, B54_C,
C09_C, CAN34, CAN39, CJ19, CM19 - pecas cortadas e canaletas), que o solver
de hoje nao implementa e que `solver_supported_catalog` ja descartava.

**REGRA OBRIGATORIA - separar EXECUTION SCOPE de EVALUATION SCOPE.** O
solver roda sobre o INPUT INTEIRO, sempre. A comparacao com o gabarito so'
vale onde existe gabarito. `benchmark/evaluation_scope.py` grava esse
escopo em `evaluation_scope.json`, derivado do gabarito e aplicado SO'
DEPOIS do solver. Fazer o contrario (`REFERENCE -> recortar INPUT ->
solver`) vazaria a solucao humana para a execucao.

**CORRECAO DE UM DIAGNOSTICO ANTERIOR (secao 24.8).** Estava escrito ali
que as 70 paredes a mais viriam de o layer `Arquitetura` cobrir area maior
que a regiao modulada. **MEDIDO e REFUTADO**: das 167 paredes, 164 tem 100%
da extensao dentro da mascara de ocupacao do gabarito; o comprimento total
das duas leituras bate a 5% (43.033 cm contra 45.363 cm); e 96,5% da
extensao dos eixos do input cai a <= 15 cm de um eixo do gabarito. A
diferenca 167 x 97 e' **FRAGMENTACAO**, nao regiao extra: mediana de 169 cm
contra 269 cm, mais uma cauda de lascas de 8 a 16 cm. Por isso o escopo tem
DOIS criterios - ocupacao E suporte de eixo. Com os dois, 152 paredes ficam
dentro e 15 fora (926,5 cm, 2,2% do comprimento), todas por
`sem_eixo_de_gabarito_por_baixo`.

**PADRAO OBSERVADO - as 9 aberturas nao atribuidas sao todas de FASE A.**
Classificadas uma a uma (`benchmark/unassigned_openings.py`): 9 de 9 sao
`WALL_MODELING_ERROR`. Todas dentro do escopo, todas com eixo do gabarito a
0,00-0,24 cm por baixo (a pessoa construiu parede exatamente ali), e nenhuma
parede da FASE A cobre o vao - em 3 casos nem existe parede dentro da
distancia perpendicular. Nenhuma e' erro do solver de blocos.
`DOCUMENTADO - pendencia de codigo aberta`, junto com a fragmentacao (e' o
mesmo defeito visto de outro angulo).

**NUMEROS DA BASELINE OFICIAL `baseline_real_v1` (2026-08-31).** A rodada
anterior (score 6,6% com catalogo do gabarito) fica marcada como
PROVISIONAL/DIAGNOSTIC ONLY em `provisional_2b/` e NAO e' historico oficial.

| | FULL | SCOPED |
|---|---|---|
| taxa de sucesso | 6,6% | 5,9% |
| erros criticos | 1.671 | 1.584 |
| achados nivel 1 | 4.986 | 4.782 |
| paredes | 167 | 152 |
| blocos | 10.657 | 10.237 |

SCOPED sair MENOR que FULL nao e' contradicao: o recorte tira 15 paredes
curtas que passavam nas checagens sem esforco, entao a media cai. O que
importa e' a coluna do humano ao lado.

**Piso de ruido DENTRO do escopo** (mesmo validador nos dois lados):
`JUNCTION_NOT_ALTERNATING` 287 x 9 (31,9x), `COMPENSATOR_CONSECUTIVE`
444 x 52 (8,5x), `PRISM_CONTINUOUS_JOINT` 897 x 126 (7,1x),
`COVERAGE_PARTIAL_WALL` 56 x 4 (14x). Continuam classificados como
**validador ruidoso** (o humano incide mais): `JUNCTION_MISSING_BINDING`
24 x 373 e `JUNCTION_HALF_BLOCK_ADJACENT` 0 x 264.

## 25. ABERTURAS E BONECAS: o que o projeto humano realmente faz (2026-08-31)

Conhecimento extraido da Etapa 2C do benchmark, projeto
`torre_easy_lo_r00_tgd` (nivel 04. TGD). Medicao completa em
`nuvem/benchmark/RELATORIO_ETAPA_2C.md`. Registro obrigatorio (CLAUDE.md:
"todo conhecimento de AMARRACAO deve ser guardado").

### 25.1 REGRA OBRIGATORIA - a abertura NAO se move para a modulacao fechar

**CONFLITO RESOLVIDO.** A hipotese de trabalho anterior era que o
projetista humano deslocava portas/janelas alguns cm ao longo da parede
(aumentando uma boneca e diminuindo a outra) para a modulacao fechar.
**Isso esta' REFUTADO com medicao.**

Como foi descoberto: casamento estrito INPUT (CAD) x HUMANO (fiadas reais
reconstruidas) das 91 aberturas, 75 pares.

- deslocamento AO LONGO da parede: **maximo 0,2442 cm em 75 de 75 pares**
  (media 0,0807; mediana 0,0047). Nao ha' um unico caso acima do piso de
  ruido de 0,5 cm.
- largura: `dw = 0` em **74 de 75**; peitoril: `dsill = 0` em **75 de 75**.
- bonecas: **150 bonecas medidas** (2 por abertura), diferenca maxima
  **0,244 cm**, nenhuma acima de 0,5 cm.
- o residuo de 0,24 cm e' um offset rigido global (`dy = -0,243 cm`) da
  reconstrucao do gabarito, nao movimento.

**Consequencia para o solver:** e' PROIBIDO mover uma abertura para fechar
a modulacao. A abertura e' dado de entrada fixo.

### 25.2 REGRA OBRIGATORIA - a abertura e' fronteira dura da fiada

**FATO MEDIDO:** distancia da lateral do vao ate' a junta vertical humana
mais proxima = **0,000 cm de maximo**, nos dois lados, em todas as fiadas
de todas as paredes com abertura. A fiada humana **para exatamente** na
lateral do vao - nunca atravessa, nunca sobra, nunca falta.

### 25.3 PADRAO OBSERVADO CONFIRMADO - o residuo e' absorvido por compensador ENCOSTADO na abertura

**FATO MEDIDO** (1.582 encostes de bloco em lateral de vao, fiada a fiada):

| bloco encostado na lateral do vao | esquerda | direita |
|---|---|---|
| B19 | 262 | 268 |
| **C04** | **147** | **151** |
| B39 | 105 | 108 |
| **C09** | **97** | **94** |
| B34 | 74 | 64 |
| B54 | 39 | 37 |

**502 dos 1.582 encostes (31,7%) sao compensador (C04/C09).**

Ou seja: o humano nao move a abertura - ele **encosta o compensador na
lateral do vao**. Essa e' a manobra real que fecha a modulacao ao redor de
portas e janelas.

Isso NAO autoriza compensadores consecutivos (regra existente continua
valendo); autoriza compensador **na lateral do vao**, que e' posicao
legitima e frequente no projeto humano.

### 25.4 REGRA OBRIGATORIA (verificacao) - a malha modular do projeto

**FATO MEDIDO** no gabarito humano:

| grandeza | regra medida |
|---|---|
| comprimento de parede | **96 de 97 sao `comprimento % 5 == 4` cm** |
| largura de abertura | **91 de 91 (INPUT) sao `largura % 5 == 1` cm** |
| boneca (lateral do vao ate' o vizinho) | **as 26 distintas sao `% 5 == 4` cm** |

Valores de boneca efetivamente encontrados: 19, 24, 34, 39, 44, 49, 54,
59, 64, 69, 74, 124, 134, 159, 164, 204, 274, 289, 309, 314, 519, 534,
754, 1024 cm.

**Uso obrigatorio:** `comprimento % 5 == 4` e' teste de sanidade barato
para qualquer parede reconstruida do CAD. Hoje **so' 82 das 167 paredes**
do Wall Modeling passam nesse teste (o gabarito passa em 96 de 97) - as 85
restantes sao suspeitas de pareamento errado.

**DOCUMENTADO - pendencia de codigo aberta:** esse teste ainda nao existe
no validador nem no benchmark.

### 25.5 REGRA OBRIGATORIA - a geometria esta' errada ANTES do solver

**FATO MEDIDO.** As 9 aberturas hoje rotuladas `WALL_MODELING_ERROR` nao
sao erro de abertura: 5 estao em paredes que o Wall Modeling **nao criou**
e 4 estao a 12,8-13,0 cm de um eixo que ficou **13 cm fora do lugar**.
Causa raiz: o desempate de `find_wall_pairs` premia a MENOR distancia
entre faces em vez da distancia mais proxima da espessura pedida (em
**71 de 72** disputas medidas o par vencedor tinha espessura pior).

**Consequencia para toda analise de modulacao:** enquanto isso nao for
corrigido, medir `COMPENSATOR_CONSECUTIVE`, `PRISM_CONTINUOUS_JOINT` ou
`JUNCTION_NOT_ALTERNATING` sobre este projeto **mede ruido** - 31 das 167
paredes nao deveriam existir e 27 das 97 paredes reais estao faltando.

**DOCUMENTADO - pendencia de codigo aberta.** Nenhuma correcao foi
aplicada; o plano e' tratado em sessao propria.

## 26. PAREAMENTO DE FACES: a espessura decide, nao a proximidade (2026-08-31)

Conhecimento extraido da Etapa 2D (PLANO da correcao do CR-1). Medicao
completa em `nuvem/benchmark/PLANO_ETAPA_2D.md`; scripts de reproducao em
`nuvem/benchmark/diagnostics_2d/`. Nenhuma correcao foi aplicada ainda.

### 26.1 REGRA OBRIGATORIA - entre duas faces candidatas, vence a que MEDE a espessura pedida

Ao escolher com qual linha parear uma face de parede, o criterio primario
e' o **erro de espessura** (`|distancia_medida - espessura_escolhida|`), e
so' depois a sobreposicao. O criterio anterior - "no empate de
sobreposicao, vence a MENOR distancia" - esta' **REVOGADO**.

Como foi descoberto: simulacao offline sobre os 589 candidatos reais do
`torre_easy_lo_r00_tgd`, trocando apenas a chave de ordenacao.

**FATO MEDIDO** (o mesmo pipeline, so' o ranking diferente):

| | criterio antigo | criterio novo |
|---|---|---|
| pares com espessura exata | 77 de 209 (37%) | **122 de 203 (60%)** |
| paredes do gabarito reproduzidas | 70 de 97 | **87 de 97** |
| paredes no eixo certo | 76 de 167 | **96 de 154** |
| paredes com eixo 10-16 cm fora | 33 | **4** |
| aberturas atribuidas | 82 de 91 | **91 de 91** |
| roubos de face | 52 | **7** |
| paredes do gabarito PERDIDAS | - | **0** |

**DOCUMENTADO - pendencia de codigo aberta.** A formula aprovada esta' no
item G do plano; a implementacao e' a proxima sessao.

### 26.2 REGRA OBRIGATORIA - NUNCA por piso de sobreposicao pela linha mais longa

E' PROIBIDO filtrar candidatos por `overlap / comprimento_da_linha_mais_longa`
(`r_long`) ou por comprimento minimo de linha, para tentar eliminar linhas
de esquadria.

**FATO MEDIDO - por que:** as paredes **W001** e **W068** (424 cm, reais,
com `d = 13,999` cm, sobreposicao total) sao formadas por uma face de
**1.513,15 cm** contra uma de **424,00 cm** -> `r_long = 0,2802`. Um piso
de `r_long >= 0,30` mata as duas e devolve 4 aberturas para o limbo. Com
`r_long >= 0,50`, morre W037 junto.

Isso confirma, com numero, o aviso que ja' estava no docstring de
`find_wall_pairs`: uma boneca legitima pode ter sobreposicao pequena em
relacao a' face longa vizinha. O aviso estava certo; o remedio (desempate
por menor distancia) e' que estava errado.

### 26.3 EXCECAO PERMITIDA - existe parede real com 15,06 cm entre faces

**FATO MEDIDO:** a parede **W074** (189 cm no gabarito) tem como **unico**
candidato um par a `d = 15,060 cm` (`erro = 1,060 cm` para a espessura
pedida de 14). Ela e' uma parede legitima do projeto humano.

**Consequencia:** qualquer corte por erro de espessura tem que ser
`> 1,06 cm`. O valor medido como seguro e' **1,5 cm** (preserva W074, W001,
W068, mantem 87 paredes cobertas e 91 de 91 aberturas). Um corte em
`1,0 cm` **mata W074** - esta' medido.

### 26.4 REGRA OBRIGATORIA - as linhas de esquadria sao combatidas por ESPESSURA, nunca por numero

O Layer 'Arquitetura' mistura face de parede com folha de porta
(4,445 cm = 1,75"), marco (5,08 cm = 2"), batente e testa. E' PROIBIDO
criar filtro que cite esses valores: seria overfitting ao
`torre_easy_lo_r00_tgd`.

**FATO MEDIDO:** so' corrigir o ranking ja' reduz os pares "linha curta
(<20 cm) x face longa (>=100 cm)" de **30 para 20**, e as paredes com menos
de 20 cm de 22 para 19. Um corte adicional por erro de espessura
(`<= 1,0 cm`) levaria esses pares a **9**. A propriedade usada e'
generalizavel (erro de espessura), nao o comprimento da linha.

### 26.5 PADRAO OBSERVADO CONFIRMADO - guloso basta; matching global nao acrescenta

**FATO MEDIDO:** sob o mesmo conjunto de candidatos e o mesmo criterio de
qualidade, o pareamento guloso com ranking corrigido e o matching global de
peso maximo produzem **exatamente o mesmo resultado** (176 pares /
122 exatos / 87 paredes cobertas / 96 eixos corretos / 91 aberturas).
Com peso que premia cardinalidade, o matching global fica **pior** que o
guloso (85 cobertas, 25 eixos a 10-16 cm, 39 paredes < 50 cm).

Motivo estrutural medido: o grafo de candidatos tem **133 componentes
conexas**, a maior com 25 arestas, e 38 com uma aresta so'.

**Consequencia:** nao introduzir matching global. Fica registrado como
alternativa avaliada e descartada por evidencia.

### 26.6 PADRAO OBSERVADO AINDA NAO CONFIRMADO - ORDER_DEPENDENCE_MERGE_COLLINEAR_FRAGMENTS

**Identificador da pendencia:** `ORDER_DEPENDENCE_MERGE_COLLINEAR_FRAGMENTS`.

**FATO MEDIDO:** embaralhar a ordem das 9.258 linhas de entrada muda a
saida do `merge_collinear_fragments` (**2868 -> 2879 / 2873** linhas
mescladas, em duas sementes distintas), sem mudar nenhuma geometria de
verdade. Embaralhar so' as 2.868 linhas ja' mescladas tambem muda o numero
de candidatos validos gerados por `find_wall_pairs` (**589 -> 583**),
indicando que `_are_parallel_cached` e/ou `_line_pair_overlap_ft_cached`
nao sao simetricos em `i`/`j`.

**Nao e' o CR-1, NAO deve ser corrigida no mesmo commit que ele, e NAO deve
ser misturada com nenhuma outra correcao futura de `core`** - e' uma causa
raiz propria (provavelmente em `merge_collinear_fragments`, fora de
`find_wall_pairs`), precisa da sua propria medicao isolada antes de
qualquer edicao.

**DOCUMENTADO - pendencia de codigo aberta**, registrada independentemente
do plano do CR-1 em `nuvem/benchmark/PLANO_ETAPA_2D.md` (item Q).

### 26.7 LIMITACAO REGISTRADA - so' existe UM projeto que exercita o pareamento

**FATO MEDIDO:** `torre_easy_lo_r00_tp1` e `piloto_sintetico_2x2` tem
`input.json` com paredes **ja' construidas** (96 e 12 walls) e **zero**
`segments` de CAD. Eles entram no pipeline depois do Wall Modeling e nao
executam `find_wall_pairs` em nenhuma linha.

**Consequencia obrigatoria para as proximas capturas:** todo projeto novo
capturado do Revit deve gravar `input_real.json` **com os `segments` do
Layer de CAD**, senao o benchmark continua com um unico caso de FASE A e
nenhuma correcao de pareamento podera' ser validada cross-project.
