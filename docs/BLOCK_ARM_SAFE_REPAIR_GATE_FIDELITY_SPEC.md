# RELATÓRIO FINAL — ARM SAFE REPAIR GATE FIDELITY PREIMPLEMENTATION

`CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY-PREIMPLEMENTATION`. SPEC + TEST
PLAN. **Nenhum código de produção alterado nesta CR.**

## Base

```
main = 68a62693ba4ac3a1def43be8b84d526372a4ee9a (confirmado, HEAD atual)
branch de trabalho = claude/cr-block-arm-safe-repair-spec-gjkvm3
```

## Evidências herdadas do diagnóstico

O pedido desta CR presume um documento
`docs/BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md` de uma sessão anterior.
**Esse arquivo não existe no repositório** (`git log --all` confirma que
nunca foi commitado sob esse nome nem um equivalente) — busca em camadas
completa (termo exato, sinônimos "rejected"/"diagnosis"/"diagnóstico",
`docs/`, `docs/archive/`, histórico completo de commits) não encontrou o
arquivo. As conclusões A-D do pedido (TP1 `wall_idx=75`, TGD 89/90, "8 de
10 arestas com candidato compatível", NODE-FILL independente) são,
portanto, tratadas como **hipóteses herdadas a verificar**, não fatos já
provados — e foram reverificadas nesta sessão diretamente contra o
código de produção atual e o relatório commitado mais próximo,
`docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md` (`PR #12`, que já
documenta 7 arestas rejeitadas no TGD + 3 no TP1 = 10, e explicita que a
numeração de `wall_idx` **não é estável entre sessões/scripts diferentes
de reexecução** — por isso os números "75"/"89"/"90"/"91"/"120"/"20" do
pedido não precisam bater com os números do relatório do PR #12, que usa
sua própria reexecução independente com `wall_idx` 4/23/54/89/90/91/92/120).

O mecanismo por trás de cada achado (A, B) foi **reconfirmado por leitura
direta do código de produção atual** (não apenas herdado por citação) —
ver seções "Compensator gate" e "Coverage gate" abaixo, com linha exata.
O achado (D) foi confirmado como CR aberto e documentado
(`CR-BLOCK-NODE-FILL-JOINT`, citado em `nuvem/REGRAS_MODULACAO_BLOCOS.md`
seção 30.4/`docs/BLOCK_ARM_ROLE_INVARIANCE.md`) — não iniciado, não
tocado nesta sessão. O achado (C) ("8 de 10 arestas rejeitadas têm
candidato ARM compatível com o humano") **não foi reverificado** nesta
sessão (exigiria comparação humano×solver por aresta, fora do escopo
"não alterar produção, só especificar contrato" — ver "Expected Gain").

---

## Compensator gate

### bug atual

Confirmado por leitura direta, causa-raiz exata:

`_no_new_consecutive_compensators` (`wall_stepper.py:5988-5995`), chamado
pelo orquestrador `_evaluate_corner_role_candidate`
(`wall_stepper.py:6190-6194`), recebe `baseline_result["candidates"]` /
`trial_result["candidates"]` — a chave `"candidates"` de
`_solve_building_blocks_all_courses_core` é `all_candidates`
(`wall_modeling.py:3231`), a **concatenação de `result["candidates"]` de
TODAS as bandas de abertura** (`wall_modeling.py:3189`,
`all_candidates.extend(result["candidates"])`, uma vez por banda — ver
docstring da própria função, `wall_modeling.py:3172-3187`).

Cada candidato individual carrega `c["course"]` como a **LETRA de
família** (`"A"`/`"B"`, par/ímpar — atribuída dentro de
`solve_building_blocks`, uma resolução por banda), **nunca o
`course_index` físico** (0..`num_courses`-1). Uma banda cobre
tipicamente VÁRIAS fiadas físicas (todas as fiadas com o mesmo conjunto
de aberturas ativas na faixa vertical — `_group_course_indices_by_opening_
band`, `wall_modeling.py:2964`), e o MESMO compensador (mesma posição X
ao longo do eixo da parede) tende a se repetir em MÚLTIPLAS bandas
distintas, porque a necessidade geométrica do compensador não depende de
qual abertura está ativa naquela faixa vertical — só da geometria
horizontal da parede.

`_find_consecutive_compensators` (`wall_stepper.py:5585-5626`) agrupa
`by_course` usando exatamente essa chave (`c.get("course")`,
`wall_stepper.py:5611`) — com só 2 valores possíveis (`"A"`/`"B"`) em vez
de `num_courses` valores. Quando o candidato `SAME_A` (ou qualquer
candidato ARM que force uma família a repetir a mesma composição em mais
fiadas) faz o mesmo compensador aparecer em 7 bandas diferentes, todos
com `course="A"` e posição X quase idêntica (mesmo compensador,
horizontalmente, reaparecendo banda a banda), `_find_consecutive_
compensators` os enxerga como um único grupo `by_course["A"]`, ordena por
posição X, mede o "gap" entre eles (que é ~0, porque são a MESMA posição
horizontal repetida, não fiadas adjacentes empilhadas) e **os classifica
como uma sequência consecutiva de compensadores na MESMA fiada física** —
quando na realidade são 7 fiadas físicas DIFERENTES (course_index
diferentes), cada uma com um único compensador isolado, nunca adjacente
a outro na mesma fiada real.

Isto é EXATAMENTE o mecanismo do achado (A): `SAME_A` no candidato de
`wall_idx=75`(TP1, numeração da sessão anterior) força mais fiadas a
"A", multiplicando quantas bandas contribuem `course="A"` para aquela
posição — e o gate, cego a `course_index`, soma-as como se fossem uma
única fiada com 7 compensadores emendados.

A estrutura CORRETA (identidade de fiada física) **já existe e já é
usada por outro gate no mesmo arquivo**: `course_candidates`
(`wall_modeling.py:3120-3171`, `dict {course_index: [candidatos JÁ
filtrados pela letra/variante certa E deduplicados por
`_drop_fill_colliding_with_ties`]}`) — é exatamente o que
`_wall_row_covered_length_cm`/`_no_new_row_coverage_regression`
(`wall_stepper.py:5998-6080`) já recebem e usam (chamados com
`baseline_result["course_candidates"]`/`trial_result["course_candidates"]`
em `wall_stepper.py:6196-6198`, duas linhas depois do gate de
compensador que usa a estrutura ERRADA).

### identidade correta de fiada

Uma FIADA FÍSICA real é identificada por `course_index` (inteiro
`0..num_courses-1`), nunca por `course` (letra de família `"A"`/`"B"`,
que se repete em toda banda) nem por índice de lista/ordem de banda. A
estrutura `course_candidates[course_index]` (produzida em
`_solve_building_blocks_all_courses_core`) já é essa identidade —
population por fiada física, com deduplicação de colisão já aplicada
(`_drop_fill_colliding_with_ties`), pronta para reúso.

### mudança mínima proposta

Trocar a fonte de dados de `_no_new_consecutive_compensators` (e do
helper `_wall_compensator_run_signatures` que ele usa,
`wall_stepper.py:5976-5985`) de `candidates` agregado
(`baseline_result["candidates"]`/`trial_result["candidates"]`) para
`course_candidates` (mesma estrutura que o gate de cobertura já usa),
iterando por `course_index` real e chamando `_find_consecutive_
compensators`-equivalente **por fiada física isolada** (não mais
agrupando por letra através de `by_course`).

Concretamente, sem implementar: `_find_consecutive_compensators`
precisaria de uma variante (ou parâmetro novo) que recebe
`course_candidates[course_index]` (lista já de UMA fiada física só) em
vez de `candidates` + agrupamento interno por `c.get("course")` — porque
agrupar por `course_index` explícito, um de cada vez, elimina o
agrupamento cross-banda por construção (cada chamada já é uma fiada só).
`_wall_compensator_run_signatures` passaria a iterar
`range(num_courses)` chamando essa variante por `course_index`, análogo
ao loop que `_no_new_row_coverage_regression` já faz
(`wall_stepper.py:6070`). Nenhuma arquitetura nova — reúso do padrão já
estabelecido pelo gate de cobertura no mesmo arquivo.

Risco de regressão da mudança (não implementada, só avaliado): candidatos
2+ compensadores REALMENTE adjacentes que hoje são corretamente
detectados porque calham de vir da MESMA banda continuam detectados
(mesma fiada física, mesmo `course_index`, mesma lista) — o único
comportamento que muda é deixar de agregar posições entre `course_index`
DIFERENTES, que nunca deveria ter agregado.

---

## Coverage gate

### proxy atual

`_no_new_row_coverage_regression` (`wall_stepper.py:6038-6080`), chamado
por fiada `dirty_wall_idxs` (`wall_stepper.py:6195-6199`), mede
`_wall_row_covered_length_cm(wall_idx, course_index, course_candidates,
walls_to_create)` — soma o comprimento coberto (união de extents ao
longo do eixo) só dos candidatos cujo `c.get("wall_idx") == wall_idx`
(`wall_stepper.py:6015`). Compara ANTES × DEPOIS com tolerância relativa
10% (`ROW_COVERAGE_RELATIVE_TOLERANCE`) ou piso absoluto de `5 ×
BLOCK_JOINT_CM` (`ROW_COVERAGE_ABSOLUTE_FLOOR_CM`), o que for maior.

### cobertura física

Em um nó L (encontro entre duas paredes), a peça de canto (quadrado ou
retangular de amarração) fica fisicamente sobre o VÉRTICE — seu volume
tipicamente estende sobre o eixo de AMBAS as paredes por uma distância
curta a partir do nó (é o que torna a peça uma peça de amarração e não
um bloco comum). O candidato dessa peça, no entanto, é registrado com um
único `wall_idx` "dono" (a parede escolhida como âncora do nó pela
coordenação de papel — `_coordinate_arm_role_nodes`). Quando um
candidato ARM troca a família ancorada, a peça de canto muda de
`wall_idx` "dono" na estrutura de dados — mesmo que sua GEOMETRIA
(posição/volume real) permaneça fisicamente presente e continue tocando
a mesma região do nó em ambas as paredes.

`_wall_row_covered_length_cm`, ao filtrar só por `c.get("wall_idx") ==
wall_idx`, credita a cobertura da peça de canto SÓ à parede que hoje a
"possui" nos dados — nunca ao ponto físico que ela ocupa. Numa parede
vizinha CURTA onde a peça de canto ocupava a fiada inteira, perder a
posse (não a presença física) faz a cobertura LOCAL medida cair de
100% para 0%, disparando `row_coverage_regression` mesmo que a região
física continue coberta (agora "pertencendo", nos dados, à parede do
outro lado do nó).

**Mapeamento genérico do mecanismo** (a instância específica TGD 89/90
citada no pedido não foi reexecutada nesta sessão — o mecanismo abaixo é
o mesmo já documentado, com números medidos, em
`_no_new_row_coverage_regression.__doc__`, `wall_stepper.py:6047-6065`,
para o candidato `wall_idx=89` da reexecução do `PR #12`: fiada vizinha
cai de 34cm para 0cm):

- **cobertura alvo antes**: fiada física da parede vizinha CURTA = 100%
  (só a peça de canto ocupava toda a fiada).
- **cobertura alvo depois**: 0% medido LOCALMENTE (a peça de canto
  passou a ter `wall_idx` da OUTRA parede do nó).
- **quadrado de canto removido**: não removido fisicamente — só
  reatribuído de `wall_idx` (dono de dados), permanece no `trial_result`
  inteiro, só não aparece mais no filtro `wall_idx==<vizinha>`.
- **parede vizinha que recebe essa cobertura**: a parede alvo do próprio
  candidato ARM (`target_wall_idx` de `_evaluate_corner_role_candidate`)
  — a peça migra de dono precisamente porque o candidato reancorou o nó
  nela.
- **cobertura física global do nó**: inalterada — a MESMA peça, na MESMA
  posição geométrica, continua presente no resultado; só a atribuição de
  posse mudou.

### regra de crédito proposta

Uma troca de papel ARM **não deve ser rejeitada só porque a cobertura
LOCAL (por `wall_idx` dono) cai**, quando a mesma região física continua
coberta por uma peça presente no resultado do candidato — mas o crédito
só é válido sob TODAS as condições abaixo (nunca por proximidade de
`wall_idx`/heurística de vizinhança):

1. **mesmo nó** — a peça candidata a dar crédito precisa estar ancorada
   no MESMO `node_index` (grafo de `_coordinate_arm_role_nodes`) que
   conecta a parede vizinha ao alvo — nunca "qualquer peça perto".
2. **mesma região geométrica** — o intervalo `[t_lo_cm, t_hi_cm]` da peça
   candidata, projetado no EIXO da parede vizinha (não no eixo da parede
   dona), precisa sobrepor (ou tocar, com a mesma tolerância de junta já
   usada em `_wall_row_covered_length_cm`, `1e-6`) o trecho da fiada da
   vizinha que ficou sem cobertura — nunca "a peça existe em algum lugar
   da parede".
3. **mesma fiada física** — mesmo `course_index` (nunca letra de
   família, pela mesma razão do gate de compensador acima).
4. **peça realmente presente** — a peça precisa aparecer em
   `trial_result["course_candidates"][course_index]` (o resultado REAL
   do rebuild do candidato, nunca hipótese/estimativa) com `wall_idx`
   igual ao da parede que agora a possui — nunca inventar geometria.
5. **ausência de gap físico** — depois de somar o crédito, o comprimento
   coberto total da fiada da vizinha (cobertura própria + a fração
   projetada da peça de canto que fisicamente alcança seu eixo) precisa
   preencher o trecho sem sobra de vão descoberto acima da MESMA
   tolerância relativa/absoluta que o gate já usa — se ainda sobrar um
   gap real, a regressão continua válida e o candidato continua
   rejeitado.

Condição explícita: o crédito **nunca** pode ser concedido só porque
"existe uma peça na parede vizinha" (isso reabriria a heurística por
`wall_idx` que o pedido proíbe) — precisa ser a MESMA peça geométrica que
a fiada da parede alvo perdeu, verificada por overlap de intervalo no
eixo da vizinha, não por adjacência de `wall_idx` no grafo.

Mudança mínima proposta (não implementada): um helper novo,
`_wall_row_covered_length_cm_with_node_credit(wall_idx, course_index,
course_candidates, walls_to_create, node_index, ...)` que, além da soma
atual (candidatos com `wall_idx` próprio), soma também candidatos do
MESMO `course_index` cujo `wall_idx` é o do nó vizinho relevante MAS cujo
intervalo geométrico, projetado no eixo de `wall_idx`, sobrepõe a região
descoberta — usado só dentro de `_no_new_row_coverage_regression`
quando o gate roda para uma parede que É a vizinha imediata de um nó do
candidato (nunca para paredes fora do grafo do candidato).

---

## Parity identity

Achado (E) do pedido: `TGD 120/SAME_B`, `TP1 20/SAME_B`, `TP1 91/SAME_B`
teriam sido classificados como PROVÁVEL espelho de paridade sem aumento
real de achados. Essa classificação específica não foi reverificada
nesta sessão (o diagnóstico de origem não existe no repo — ver "Evidências
herdadas"), mas o MECANISMO de espelho de paridade **já está documentado
e provado** para um caso adjacente: `JUNCTION_MISSING_BINDING` 8→9 no TP1
(`docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md`, seção "CONTINUAÇÃO —
PRE-INTEGRATION AUDIT", classificado `P3 — BENCHMARK_ARTIFACT`: as 9
fiadas pares "novas" do candidato são, uma a uma, a MESMA fiada ímpar
resolvida — não um cluster de defeito novo, só o mesmo defeito espelhado
de paridade por completo). O modelo de identidade hoje em vigor no
Candidate Safety Contract já é, textualmente, "geométrica/topológica
estável dentro da MESMA resolução" por `(wall_idx, course_index)`
(`docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md`, seção "Delta
model") — ou seja, **já é mais fino que assinatura por course exata**
(inclui posição), mas ainda mais fino que identidade semântica
(parede, código, geometria física) quando a ÚNICA diferença entre dois
achados é qual fiada (par/ímpar) carrega o defeito.

### OPTION A — manter identidade atual (assinatura exata por course/posição)

- **Benefício**: nenhuma mudança de comportamento; nenhum risco de
  masking; já provado (18 testes, `T13`-`T15` de invariância de ordem
  cobrem justamente isto).
- **Risco**: candidatos que só espelham paridade (mesmo defeito, fiada
  diferente) continuam contando como "regressão nova" mesmo quando o
  número líquido de defeitos físicos não muda — pode rejeitar
  candidatos seguros por um artefato de contagem (exatamente o padrão
  já medido e documentado como `P3` para `JUNCTION_MISSING_BINDING`).
- **Masking**: nenhum — é a opção mais conservadora.

### OPTION B — identidade por parede/código

Comparar achados agregando por `(wall_idx, logical_code)`, ignorando
`course_index`/posição exata.

- **Benefício**: absorve espelhos de paridade automaticamente (um
  defeito que só migra de fiada par para ímpar na MESMA parede deixa de
  contar como novo).
- **Risco**: **grosseiro demais** — duas ocorrências REAIS e
  independentes do mesmo `logical_code` na mesma parede (por exemplo,
  dois compensadores novos em fiadas DIFERENTES, por razões
  DIFERENTES) colapsariam na mesma identidade e uma delas seria
  invisível ao delta.
- **Masking**: ALTO — esconde contagem real de achados novos sempre que
  há mais de um achado do mesmo tipo na mesma parede, mesmo sem relação
  de paridade nenhuma. Não recomendado sozinho.

### OPTION C — identidade geométrica mais específica

Comparar achados por identidade geométrica plena, mas com uma
NORMALIZAÇÃO explícita de paridade só quando o padrão for
comprovadamente um espelho: `(wall_idx, logical_code, região geométrica
ao longo do eixo — t arredondado)`, e SÓ colapsar duas entradas em uma
quando (a) mesma parede, (b) mesmo código, (c) mesma posição
`t`/região, (d) `course_index` de paridades OPOSTAS, (e) o total de
achados daquele tipo na parede não muda (N antes == N depois, só
paridade inverte) — nunca colapsar por suposição, sempre por prova de
bijeção completa entre o conjunto ANTES (paridade X) e o conjunto DEPOIS
(paridade Y).

- **Benefício**: resolve o artefato de contagem SEM esconder achados
  reais novos (a condição (e) — bijeção completa — é o que distingue
  "só espelhou" de "aumentou").
- **Risco**: mais complexo de implementar e testar corretamente (exige
  provar a bijeção, não só contar); maior superfície para bug sutil no
  próprio gate de comparação.
- **Masking**: BAIXO, se a bijeção for exigida estritamente — um
  candidato que troca 3 achados de paridade por 4 (mesmo que pareça
  "quase" espelho) NÃO se qualifica e conta como regressão real.

### Recomendação

**OPTION C**, mas só implementar quando houver evidência de que o
padrão de espelho de paridade realmente afeta candidatos ARM úteis (não
só `JUNCTION_MISSING_BINDING`, que já está fora do escopo desta CR por
ser P3 pré-existente, não causado por nenhum candidato ARM). Sem essa
reverificação (que exigiria reexecutar TGD/TP1 e olhar
`wall_idx=120/SAME_B` etc. — não feito nesta CR, "só especificar"), a
OPTION A permanece o padrão seguro por omissão; a decisão de trocar
para C é do CR de implementação, não desta spec.

---

## B19

**DEFERRED DOMAIN DECISION.**

O pedido cita um conflito entre humano e regra atual ("nunca B19 como
recurso de amarração") em paredes curtas vizinhas — mesmo padrão já
registrado para o encontro `W039`↔`W041` do TP1 em
`docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md` (seção "Humano ×
Solver": o gabarito humano aprovado repete `B19` sem alternar naquele
nó, e o solver diverge alternando `B34`/`C09`). Não pertence a este CR.
Regra de amarração (B19) **não alterada**. Solver **não adaptado**.

---

## Cantos girados

**OUT_OF_SCOPE_GEOMETRY/JUNCTION_CASE.**

`_corner_bond_blocked_by_other_node` (`wall_stepper.py:837-865`) veta
rotacionar/posicionar a peça de amarração de um canto quando outro
encontro da MESMA parede cai perto o suficiente para colidir (margem
`span_ft + T_INTERSECTION_B54_HALF_ROOM_FT`, deliberadamente
superestimada — "mais seguro rotacionar a mais do que colidir"). Esse
veto roda ANTES/INDEPENDENTE de qualquer candidato ARM (é geometria pura
de proximidade entre nós na mesma parede, não decisão de papel
`course_a`/`course_b`) — nos casos TGD 4/54, o bit de papel ARM do
candidato não muda a saída porque o bloqueio geométrico já decide a
peça antes da coordenação de papel entrar em jogo. Corrigir isso exigiria
mudar a MEDIÇÃO/decisão de espaço físico do canto (não o SAFE REPAIR),
fora do escopo deste CR. **Não corrigido aqui.** Recomenda-se CR
posterior dedicado, se priorizado, escopado só em
`_corner_bond_blocked_by_other_node`/`_room_at_t_on_wall` e funções de
posicionamento de canto correlatas — nunca junto do Gate Fidelity.

---

## Test Plan T1-T16

Todos os testes abaixo são PROPOSTOS para o CR de implementação — nenhum
foi escrito nesta sessão (spec-only). Convenção herdada de
`tests/test_block_arm_role_candidate_safety_contract.py` (sintéticos
diretos quando possível; contra o corpus real só quando o teste depende
de geometria real do TGD/TP1).

**Compensator gate (identidade de fiada física)**

- **T1** — sintético: um `C04` isolado, repetido em 7 bandas
  diferentes (mesma posição X, `course="A"` em todas, `course_index`
  diferentes) NÃO produz um `run` em `_find_consecutive_compensators`-
  equivalente-por-fiada (0 sequências detectadas).
- **T2** — sintético: dois `C04`/`C09` REALMENTE adjacentes dentro da
  MESMA fiada física (`course_index` idêntico) continuam detectados como
  sequência (regressão do comportamento atual não pode acontecer).
- **T3** — sintético: sequência real de 3+ compensadores na mesma fiada
  física continua detectada.
- **T4** — sintético: embaralhar a ORDEM em que as bandas são
  processadas (permutação de `groups` antes do loop) não muda o
  resultado do gate (mesmo veredito, mesma assinatura).

**Coverage gate (crédito de nó)**

- **T5** — corpus real (TGD, aresta equivalente ao `89`/`90` da
  reexecução do PR #12, a re-identificar por geometria nesta sessão de
  implementação, nunca por número de `wall_idx` fixo): cobertura LOCAL
  da vizinha cai, cobertura FÍSICA do nó (própria + peça de canto
  projetada) preservada → candidato NÃO rejeitado por proxy local falso.
- **T6** — mesmo mecanismo do T5, segunda aresta do mesmo padrão
  (equivalente ao `90`).
- **T7** — sintético: remoção REAL de cobertura (peça removida do
  `trial_result`, sem nenhuma peça de canto vizinha cobrindo a mesma
  região) continua classificada como regressão.
- **T8** — sintético: peça vizinha PRESENTE mas em OUTRA fiada física
  (`course_index` diferente) NÃO pode dar crédito.
- **T9** — sintético: peça vizinha PRESENTE mas em OUTRO nó (`node_index`
  diferente do nó que conecta a parede vizinha ao alvo) NÃO pode dar
  crédito.
- **T10** — sintético: gap físico real (nenhuma peça, de nenhuma parede,
  cobre a região) continua rejeitado mesmo depois de habilitar o
  crédito de nó (a condição 5 — ausência de gap — precisa realmente
  filtrar).

**Regressão/reprodução de ponta a ponta**

- **T11** — corpus real: reproduzir o bug ATUAL (gate errado, código de
  produção tal como está hoje) na aresta equivalente ao `TP1 wall_idx=75`
  do pedido (a re-identificar por geometria/assinatura na sessão de
  implementação) — confirma `COMPENSATOR_CONSECUTIVE` falso antes do
  fix.
- **T12** — corpus real: MESMA aresta do T11, com o gate corrigido
  (identidade de fiada física) — 0 achados novos nessa parede; o número
  de achados resolvidos precisa ser MEDIDO na sessão de implementação
  (não assumido como "102", número não reverificado nesta CR — ver
  "Expected Gain").
- **T13** — corpus real: o candidato ACEITO hoje em produção
  (`wall_idx=23`/`SAME_A` no relatório do PR #12) continua aceito depois
  da mudança nos dois gates (nenhuma regressão no único candidato que já
  passa).
- **T14** — sintético: um candidato REALMENTE inseguro (ex.: remove
  cobertura sem nenhuma peça de nó compensando, ou cria compensador
  consecutivo REAL na mesma fiada) continua rejeitado com os gates
  corrigidos.
- **T15** — sintético: permutação da ORDEM de `walls_to_create`/`nodes`
  processados não altera o veredito de nenhum gate (reusa o padrão de
  `test_t13_paredes_permutadas_...`/`test_t15_endpoints_invertidos_...`
  já existentes).
- **T16** — corpus real: repetição determinística — duas execuções
  completas do TGD com os gates corrigidos produzem `accepted`/
  `rejected` idênticos e o mesmo conjunto de achados por assinatura
  (reusa o padrão do `T16` já existente na suíte atual).

---

## Expected Gain

### PROVADO

- O mecanismo do bug do compensator gate (agregação cross-banda por
  `course` = letra, não `course_index`) é real e está no código de
  produção atual, confirmado por leitura direta de
  `wall_stepper.py:5988-5995`/`6190-6194` e
  `wall_modeling.py:3143-3189` — não depende do diagnóstico ausente.
- O mecanismo do bug do coverage gate (filtro por `wall_idx` dono, cego
  a presença física da peça de canto no nó) é real e está no código de
  produção atual, confirmado por leitura direta de
  `wall_stepper.py:6015`/`6038-6080` — reforçado pelo exemplo já medido
  e documentado (`wall_idx=89`, fiada 34cm→0cm) em
  `docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md`.
- A estrutura de dados correta para os dois fixes (`course_candidates`,
  chave `course_index`) já existe em produção e já é usada por um dos
  dois gates (cobertura) — não precisa de arquitetura nova.

### PROVÁVEL

- Corrigir o compensator gate deve permitir que candidatos ARM
  hoje rejeitados por `new_consecutive_compensators` (falso positivo)
  passem a ser avaliados pelos gates seguintes (cobertura, colisão) em
  vez de serem descartados prematuramente — mas ISSO NÃO GARANTE que
  eles sejam aceitos (podem ainda falhar um gate real).
- Corrigir o coverage gate com crédito de nó restrito (5 condições)
  deve reduzir rejeições por `row_coverage_regression` especificamente
  nos casos onde a "perda" é só reatribuição de posse da peça de canto
  — sem abrir a porta para candidatos que causam gap físico real
  (a condição 5 preserva a rejeição correta).
- O padrão TP1 `wall_idx=75`/`SAME_A` do pedido é consistente com o
  mecanismo comprovado do compensator gate (mesma assinatura: `SAME_A`
  força repetição de família em mais bandas) — mas a aresta específica
  não foi reidentificada nem reexecutada nesta sessão.

### NÃO GARANTIDO

- Número global de achados resolvidos ("102 resolvidos" citado no
  pedido) — **não medido nesta sessão, não prometido**. Só pode ser
  determinado executando o CR de implementação contra o corpus real.
- Que os 8 de 10 casos "compatíveis com humano" citados no pedido (E)
  realmente ficam aceitáveis depois dos dois fixes — depende de gates
  não relacionados a este CR (colisão, fechamento, prisma forçado em
  vizinha) que continuam vetando candidatos independentemente do fix de
  fidelidade.
- Qualquer resultado numérico do TGD/TP1/Piloto pós-fix — requer rebuild
  completo, fora do escopo "read-only/spec" desta sessão.

---

## Interação com NODE-FILL

`CR-BLOCK-NODE-FILL-JOINT` está em outra sessão, não tocado aqui (só
citado em `nuvem/REGRAS_MODULACAO_BLOCOS.md` seção 30.4 e
`docs/BLOCK_ARM_ROLE_INVARIANCE.md` como recomendação de CR futuro —
sem relatório de implementação commitado ainda neste branch).

### arquivos em comum

- `nuvem/core/engine/wall_stepper.py` — ambos os CRs operam sobre a
  mesma seção "CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT — SAFE
  REPAIR" (Gate Fidelity edita os gates existentes;
  NODE-FILL, por natureza — preencher lacunas de amarração em nós —
  provavelmente adiciona geração de candidato NOVA na mesma vizinhança
  de `_arm_role_isolated_edges`/`_evaluate_corner_role_candidate`).
- `nuvem/core/wall_modeling.py` — `_solve_building_blocks_all_courses_
  core`/`course_candidates`/`wall_bond_audits` são a base de dados que
  os dois CRs leem; NODE-FILL, se mexer em cobertura de nó, também usa
  `audit_all_walls_bond_quality`/`wall_bond_audits`.
- Potencialmente `nuvem/REGRAS_MODULACAO_BLOCOS.md` (seção 30, ambos
  registram achados na mesma seção de amarração).

### risco de conflito

MÉDIO-ALTO se as duas CRs editarem `wall_stepper.py` em paralelo sem
sincronizar: Gate Fidelity muda a ASSINATURA/fonte de dados de
`_no_new_consecutive_compensators`/`_no_new_row_coverage_regression`
(gates JÁ existentes); se NODE-FILL também alterar esses mesmos gates
(por exemplo, para reconhecer uma peça de preenchimento de nó nova como
"presente"), um merge sequencial simples pode reintroduzir o bug que
Gate Fidelity corrigiu, ou vice-versa quebrar a geração de candidato de
NODE-FILL. Baixo risco de conflito TEXTUAL direto (funções diferentes),
mas risco SEMÂNTICO real (mesma seção do arquivo, mesmos dados de
entrada `course_candidates`).

### ordem recomendada

**NODE-FILL primeiro → atualizar main → rebase/recriar Gate Fidelity
sobre a main nova → implementar os gates.** Confirma a preferência já
declarada no pedido: evita que o Gate Fidelity precise reconciliar sua
correção de identidade de fiada com uma geração de candidato nova que
ainda não existe, e permite que os testes T5/T6 (crédito de nó) sejam
escritos já cientes de qualquer peça de nó nova que NODE-FILL introduzir
(que poderia, ela mesma, ser uma fonte legítima de crédito na condição 4
do coverage gate).

---

## Production diff

ZERO — confirmar antes de qualquer commit desta CR:
`git diff origin/main -- 'nuvem/**' ':!nuvem/benchmark/**'` deve
devolver vazio (só `docs/` alterado nesta sessão).

## Baseline diff

ZERO — nenhum `baseline.json`/`reference.json`/`score.json` tocado.

## Reference diff

ZERO — nenhuma execução com escrita em disco realizada nesta sessão.

## Próximo passo após NODE-FILL

1. Aguardar `CR-BLOCK-NODE-FILL-JOINT` mesclar em `main` (decisão/
   priorização do usuário, fora do escopo desta CR).
2. Recriar/rebasear esta branch sobre a `main` pós-NODE-FILL.
3. Implementar a mudança mínima do compensator gate (identidade de
   fiada física via `course_candidates`).
4. Implementar a regra de crédito de nó do coverage gate (5 condições),
   com o helper novo restrito a paredes vizinhas imediatas do grafo do
   candidato.
5. Escrever e rodar T1-T16; medir o ganho real (nunca prometer número
   antes de medir).
6. Reexecutar TGD/TP1/Piloto completos; atualizar
   `docs/PROJECT_STATUS.md`/`PROJECT_STATUS_LOG.md`/
   `REGRAS_MODULACAO_BLOCOS.md` conforme o procedimento obrigatório do
   `CLAUDE.md`.
7. Autorização explícita do usuário antes de qualquer merge.

## Veredito

**READY_FOR_IMPLEMENTATION_AFTER_NODE_FILL**

O contrato técnico dos dois gates (compensador, cobertura) tem causa-
raiz comprovada por leitura direta do código de produção atual, mudança
mínima proposta identificada (reúso de `course_candidates`, sem
arquitetura nova), e plano de testes T1-T16 cobrindo os dois mecanismos
mais os controles de invariância/determinismo já estabelecidos pelo CR
anterior. Os itens não verificáveis sem execução (número global de
achados resolvidos, reidentificação exata das arestas citadas no pedido)
estão explicitamente marcados como NÃO GARANTIDO, não prometidos. B19 e
cantos girados corretamente deferidos para fora deste CR. NODE-FILL não
tocado; ordem de integração recomendada e pontos de conflito de arquivo
mapeados.

**NÃO IMPLEMENTADO. NÃO MESCLADO.**
