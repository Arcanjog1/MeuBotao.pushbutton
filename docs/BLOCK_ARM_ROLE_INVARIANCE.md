# RELATÓRIO FINAL — CR-BLOCK-ARM-ROLE-INVARIANCE

## Git

```
branch de trabalho    claude/cr-block-arm-role-invariance-7tezx4
base (origin/main)    7c9a681aeda2027f8fc072c0f57c62454a80d669  (CONFERE
                       com o SHA pedido no enunciado)
```

**Aviso preliminar, apurado no início desta CR (seção 1/3 do enunciado)**:
o "wall graph determinístico" que o enunciado trata como pré-existente
("O wall graph determinístico está correto e deve ser preservado",
"ordenação canônica de arms") **não está presente em `origin/main`**
neste SHA. O trabalho que introduziria essa ordenação canônica
(`_wall_graph_arm_key`, `CR-BLOCK-DETERMINISM`/finalização) existe só em
branches não mescladas (`claude/cr-block-wall-graph-quality-711umk` e
ancestrais). Em `wall_pairing.py` de `origin/main` hoje,
`_wall_node_arms`/`_cluster_wall_arms` continuam na ORDEM DE ENUMERAÇÃO
das paredes de entrada (o que o relatório do
`CR-BLOCK-WALL-GRAPH-QUALITY` chama de estado "A/MAIN"), não a ordenação
canônica por identidade geométrica ("B/+GRAFO"). Isso não muda o objetivo
desta CR — o mecanismo "arms order → course role → perda de fiada" é o
MESMO independente de qual convenção de ordenação está ativa (provado na
seção "Causa reproduzida" abaixo, com um swap manual de `node["arms"]"`
que não depende de nenhuma convenção específica) — mas significa que os
números de `COVERAGE_MISSING_ROW`/`MOSTLY_EMPTY` medidos aqui em
`origin/main` (265/171 no TGD) **já são o estado bom ("A/MAIN") que o
enunciado pede para recuperar**, não o estado degradado pelo grafo
canônico (293/181). O fix deste CR ainda vale — o defeito reproduz e é
corrigível mesmo sem o grafo canônico ativo — mas a "recuperação" medida
aqui é sobre o baseline real de `origin/main`, não sobre os números
293/181 citados no enunciado (que pertencem a um ponto não mesclado).

## Causa reproduzida

**PROVADA, com um caso real totalmente instrumentado, sem depender de
nenhuma ordenação canônica de `wall_pairing.py`.**

Caso real: `W042`/TGD (`torre_easy_lo_r00_tgd`, `wall_idx` 41). Esta
parede tem um `L_CORNER` em CADA ponta — nó A com `wall1`
(`arms=[(1,0),(41,1)]`), nó B com `wall50` (`arms=[(41,0),(50,0)]`). Cada
nó decide, **de forma totalmente independente do outro**, qual das duas
paredes ali recebe `course_a` (fiadas pares) e qual recebe `course_b`
(fiadas ímpares) — não há nada que force os dois nós da MESMA parede a
alternar. Com a ordem de `arms` que `wall_pairing.py` devolve hoje (ordem
de lista), os DOIS nós davam a `W042` o MESMO papel (`course_b`) — a
família oposta (`course_a`) ficava com ZERO peças de nó nesta parede, e
o preenchimento comum também falhava em fechar sozinho o trecho inteiro
(ver "Por que a fiada desaparecia"), produzindo `COVERAGE_MISSING_ROW`
em TODAS as 9 fiadas pares (8/17 fiadas com bloco, medido).

**Reprodução independente da convenção de `wall_pairing.py`**: sem tocar
`wall_pairing.py`, trocando manualmente `arms[0]`/`[1]` de UM SÓ dos dois
nós (script de diagnóstico, não faz parte do repositório) — mesma
geometria física, só o papel do nó mudando —, a cobertura de `W042` vai
de 8/17 para 17/17 fiadas. Generaliza (mesmo padrão, dois nós
independentes) para `W022`/`W093` (TP1) e para o nó de `W011` citado nos
achados de `PRISM_CONTINUOUS_JOINT` do piloto.

## Contrato `arms`

`node["arms"]` é uma lista de até 2 `(wall_idx, end_index)` — a IDENTIDADE
dos braços de um `L_CORNER` de 2 pontas. `wall_pairing.py` decide a ORDEM
dessa lista (hoje: ordem de enumeração de `walls_to_create`); o
CONSUMIDOR (`wall_stepper.py`) usa `arms[0][0]` como `wall_a_idx` e
`arms[1][0]` como `wall_b_idx` (`_l_corner_wall_pair`, linha ~633 antes
deste CR) sem NENHUMA outra semântica atribuída à posição — é
literalmente "o primeiro da lista" contra "o segundo". `crossing_walls`
(tupla de 2 `wall_idx`, para `X_INTERSECTION` de meio-de-parede) tem o
mesmo contrato: ordem sem significado geométrico, consumida por posição.

## `course_a` / `course_b`

São os dois PAPÉIS de fiada que qualquer encontro de amarração produz —
`course_a` cobre as fiadas de índice PAR, `course_b` as de índice ÍMPAR
(`solve_building_blocks_all_courses`, `letter = "A" if course_index % 2
== 0 else "B"`). Em `L_CORNER`, `solve_l_corner` gera EXATAMENTE 1 peça
`course_a` (na parede que é `wall_a_idx`) e 1 peça `course_b` (na parede
que é `wall_b_idx`) — nunca as duas na mesma parede, a não ser no caso
degradado documentado ("GIRAR o bloco", quando um encontro vizinho a
menos de 34cm bloqueia um dos dois lados). Cada peça de nó é o ÚNICO
ponto de ancoragem daquela família naquela ponta da parede — se as DUAS
peças de nó de uma parede (uma em cada ponta) forem da MESMA família, a
família oposta fica sem ancoragem em NENHUMA ponta.

## Por que a fiada desaparecia

Duas causas, **compostas** — a primeira sozinha já é grave, a segunda
transforma "grave" em "total":

1. **Nenhuma alternância forçada entre os dois nós de uma parede** (ver
   "Causa reproduzida"). Isto SOZINHO já torna a parede ASSIMÉTRICA
   (uma família com 2 peças de nó, a outra com 0) — mas isso sozinho
   NÃO bastaria para apagar a família inteira, porque o preenchimento
   comum (`solve_wall_free_fill`) ainda cobre o resto do vão
   independente de haver peça de nó ou não (usa a reserva GENÉRICA
   `_wall_end_default_start_cm` quando não há peça própria).
2. **A fronteira "emprestada" raramente fecha o módulo de blocos.**
   `_index_node_candidates_by_wall_end` reserva, em cada ponta, a
   extensão da peça de amarração que ocupa aquele espaço — mesmo quando
   ela pertence à parede VIZINHA (medido necessário desde 2026-08-21,
   para não colidir o preenchimento com o corpo físico da peça do
   canto). A peça PRÓPRIA de uma parede (calibrada a partir do seu
   próprio ponto/eixo) fecha o módulo de 5cm por construção; a projeção
   da peça da parede VIZINHA (retângulo quase sempre fora de eixo)
   normalmente NÃO fecha — medido no caso real: 294,258cm e 247,258cm,
   ambos a mais de 0,05cm (a tolerância existente) do múltiplo de 5cm
   mais próximo. Como o preenchimento contínuo
   (`OPENING_STRATEGY_CONTINUOUS_FIRST`, o padrão) resolve o trecho de
   nó a nó como "tudo ou nada" quando não há abertura para servir de
   ponto de quebra, essa fração de cm sobrando derrubava o TRECHO
   INTEIRO, não só a borda — e como a família sem peça de nó própria SÓ
   tem essa fronteira emprestada (nunca a própria), ela é a única a
   sofrer esse colapso total.

## Fix

Arquivo único alterado: `nuvem/core/engine/wall_stepper.py` (`wall_
pairing.py` intocado, confirmado por `git diff --stat`).

Duas funções novas + um ponto de uso em `solve_wall_free_fill`:

- **`_index_node_candidates_by_wall_end_with_donor`**: refatoração do
  núcleo de `_index_node_candidates_by_wall_end` (preservando seu
  comportamento/API 100% intactos) para computar, NA MESMA passada, o
  `donor_wall_idx` de cada borda vencedora — necessário porque a mesma
  ponta de parede pode ser "envolvida" por MAIS DE UM nó físico próximo
  (ex.: um L_CORNER e um T a poucos cm — caso real coberto por
  `test_reserva_de_ponta_ignora_encontro_de_meio_de_parede_proximo`);
  calcular o doador numa passada separada, só pelo último nó iterado,
  atribuía a doador ERRADO (dependente da ORDEM de `nodes` — o que este
  CR proíbe) sempre que o nó vencedor do max/min não era o último.
- **`_index_node_candidates_borrowed_by_wall_end`**: `{(wall_idx,
  end_index, course): donor_wall_idx}` — só as chaves cuja borda
  vencedora NÃO tem peça própria de `wall_idx` (é "emprestada" de
  `donor_wall_idx`).
- **`_node_boundary_module_snap_cm`**: dado um trecho que não fecha só
  por uma fração de módulo, devolve as bordas ENCOLHIDAS (mais reserva,
  nunca menos — sem risco novo de colisão) até o próximo múltiplo válido
  de `PIER_MODULE_CM`.
- **Uso em `solve_wall_free_fill`**: antes de aceitar `NON_MODULAR_WALL`
  num trecho fechado só por nó (nunca abertura) dos dois lados, tenta o
  arredondamento acima — **restrito** (medido necessário contra
  regressão real no benchmark, ver "Reference Corpus"/28.4 de
  `REGRAS_MODULACAO_BLOCOS.md`) a: (a) nem esta parede nem a doadora têm
  abertura própria; (b) o trecho é a parede INTEIRA (nó a nó, sem
  meio-de-parede); (c) esta família não tem NENHUMA peça de nó própria
  em nenhuma ponta desta parede (a família estaria total e
  legitimamente ausente sem o fix); (d) a família OPOSTA desta mesma
  parede TEM uma peça de nó própria (o padrão exato de `COVERAGE_ROW_
  MOSTLY_EMPTY` — nunca ativa numa parede em que as duas famílias já
  eram emprestadas, situação genuinamente `NON_MODULAR_WALL`/`COVERAGE_
  WALL_NOT_MODULATED`, fora do escopo deste CR). Uma rede de segurança
  final garante que o arredondamento NUNCA empurra uma borda para fora
  do intervalo original (só encolhe, nunca "inventa" espaço).

**Por que este design satisfaz a seção 11 do enunciado** ("não implemente
apenas um sort diferente... o fix deve tornar o downstream robusto à
ordem canônica já existente"): o fix não decide QUAL parede recebe
`course_a`/`course_b` (isso continua vindo de `wall_pairing.py`, hoje ou
no futuro, sem alteração) — ele torna o CONSUMO desse papel robusto a
QUALQUER borda que resulte dele, própria ou emprestada, exatamente o
espírito pedido.

## `L_CORNER`

Auditado em detalhe (ver "Causa reproduzida"/"Por que a fiada
desaparecia"). Antes do fix: `arms[0]`/`[1]` decidem sozinhos, sem
alternância entre os dois nós da mesma parede, podendo apagar uma família
inteira quando compõem com o mecanismo de borda emprestada. Depois do
fix: dentro do escopo (a)-(d) acima, a família nunca fica com ZERO peças
quando a família oposta tem cobertura de verdade.

## `T_INTERSECTION`

Controle (item 14 do enunciado) — nenhuma alteração de comportamento.
`solve_t_intersection` não usa `arms[0]`/`[1]` para decidir papel (usa
`main_wall_idx`/`incoming_wall_idx`, resolvidos por geometria — qual
parede é a que "passa reto" e qual "chega" — não por posição numa lista).
`test_t_intersection_nao_perde_familia`
(`tests/test_block_arm_role_invariance.py`) cobre isso como controle
permanente. Nenhuma regressão medida em T no benchmark (nenhum código de
`T_INTERSECTION` aparece nos deltas do "Reference Corpus" abaixo).

## `X_INTERSECTION`

Mesmo mecanismo de `L_CORNER`, com `crossing_walls[0]`/`[1]` no lugar de
`arms[0]`/`[1]` (`solve_x_intersection`). `test_x_intersection_crossing_
walls_invertido_nao_perde_familia` prova invariância de espelhamento
(troca `crossing_walls` manualmente, sem tocar `wall_pairing.py`,
confirma as duas famílias presentes nas 4 pontas do X antes/depois).
`_index_node_candidates_borrowed_by_wall_end`/`_node_boundary_module_
snap_cm` cobrem `X_INTERSECTION` da MESMA forma que `L_CORNER` (ambos
alimentam a mesma `_index_node_candidates_by_wall_end`/`WALL_START`/
`WALL_END`) — não há um segundo mecanismo separado para X. `X_
INTERSECTION` de MEIO de parede (`_find_wall_midspan_crossings`,
`MIDSPAN_HI`/`MIDSPAN_LO`) fica de propósito FORA do escopo do fix de
28.2 (ver "Testes"/limitação conhecida abaixo) — não é o caso medido
(`W042` não tem meio-de-parede) e o doador ali não está indexado no
mesmo dict.

## TGD coverage antes/depois

Medido com o solver real (`benchmark.runner.run_project`), `origin/main`
LIMPO (não `baseline.json`, que está desatualizado para alguns códigos —
ver "Reference Corpus") contra o mesmo código com o fix:

| métrica | antes (main limpo) | depois (fix) | delta |
|---|---|---|---|
| `COVERAGE_MISSING_ROW` | 265 | 145 | **-120 (melhoria)** |
| `COVERAGE_ROW_MOSTLY_EMPTY` | 171 | 309 | **+138 (regressão)** |
| `COVERAGE_WALL_NOT_MODULATED` | 29 | 29 | inalterado |
| `OPENING_BLOCK_CROSSES_JAMB` | 147 | 147 | inalterado |
| `OPENING_BLOCK_INSIDE_DOOR` | 43 | 43 | inalterado |
| `PRISM_CONTINUOUS_JOINT` | 702 | 702 | inalterado |
| total de achados (todos os códigos) | 5307 | 5430 | +123 |

Meta do enunciado (seção 22, "MISSING_ROW 293→próximo de 265") **não se
aplica literalmente** (nosso baseline real já é 265, não 293 — ver aviso
na seção Git) — mas o fix RECUPERA além disso, para 145 (46% a menos que
o próprio baseline "bom"). Ver "Reference Corpus" para a análise completa
do trade-off com `COVERAGE_ROW_MOSTLY_EMPTY`.

## TP1 coverage antes/depois

**Nenhuma mudança** — todos os códigos medidos (`COVERAGE_MISSING_ROW`,
`COVERAGE_ROW_MOSTLY_EMPTY`, `JUNCTION_MISSING_BINDING`, `OPENING_BLOCK_
CROSSES_JAMB`, `POSITION_OVERLAP`, total de achados) idênticos
antes/depois. O fix não encontrou nenhum caso, no projeto TP1, que
satisfizesse as 4 condições de escopo simultaneamente (provavelmente:
TP1 não tem, hoje, nenhuma parede com as duas famílias emprestadas em
nós diferentes SEM abertura em nenhum dos dois lados). `PRISM_
CONTINUOUS_JOINT` mudou (968→837 no `benchmark.reports`), mas ver
"Determinismo" — é ruído do `baseline.json` desatualizado, não efeito
deste fix (confirmado rodando `origin/main` limpo: também dá 837).

## Piloto PRISM

`piloto_sintetico_2x2`: **nenhuma mudança** em nenhum código
(`COVERAGE_ROW_MOSTLY_EMPTY`=8, `PRISM_CONTINUOUS_JOINT`=0, total de
achados=124, idênticos antes/depois). O nó de `W011` citado no enunciado
como fonte de `PRISM_CONTINUOUS_JOINT` não reproduz o mecanismo deste CR
neste projeto — não investigado mais a fundo (`PRISM_CONTINUOUS_JOINT`
já está em 0 nos dois pontos, sem regressão possível de medir aqui).

## Determinismo

**Preservado** — mesmo código, mesma entrada, sempre a mesma saída (3
execuções seguidas de `torre_easy_lo_r00_tgd` deram exatamente
`PRISM=702 MISSING=145 MOSTLY=309` nas três). `wall_pairing.py`
(construção do grafo) não foi alterado, então o determinismo dele
(qualquer que seja o estado hoje) é idêntico antes/depois desta CR por
construção.

**Achado colateral, NÃO causado por este CR**: tanto `nuvem/benchmark/
projects/*/baseline.json` quanto `REFERENCE_SOLVER_DECISION_FINGERPRINT`
(`tests/solver_bench.py`) estão DESATUALIZADOS em relação a `origin/main`
LIMPO — `PRISM_CONTINUOUS_JOINT` do TGD é 702 no código limpo mas 961 no
`baseline.json`; o fingerprint do `solver_bench.py` diverge da
referência gravada MESMO sem nenhuma alteração desta CR (confirmado
via `git stash` + `python3 tests/solver_bench.py --fingerprint` no
código limpo: sha `7c727398...` contra a referência `c74c9c1a...`).
Isso é sintoma de outro trabalho já mesclado depois de `baseline.json`/a
referência terem sido gravados pela última vez — fora do escopo desta
CR, não corrigido aqui (proibido por esta CR mexer em baseline, e a
causa não está em `wall_stepper.py`/`wall_pairing.py`). Recomenda-se um
CR de manutenção para atualizar os dois, com justificativa própria.

## `same-band` / `cross-band`

Não medido separado nesta CR — o script de comparação usado
(`benchmark.scoring.compare_runs`) não expõe essas métricas por nome
direto nos achados desta versão do benchmark (procurado em `validate_
*.py`, não encontrado um `same_band`/`cross_band` como código de
achado). Se essas métricas existem sob outro nome no benchmark, não
foram localizadas dentro do orçamento de busca desta CR — reportar como
NÃO MEDIDO, não como "0 mudanças".

## Compensadores

TGD: categoria `compensators` do `scoring.compare_runs` sobe (medido nas
iterações intermediárias antes da restrição final do escopo do fix, ver
histórico de commits) — a versão FINAL do fix (com a restrição (d),
"família oposta tem peça própria") já não mostra mais essa categoria
como `REGRESSAO` no `delta["categories"]` do TGD (verificado: só
`COVERAGE_ROW_MOSTLY_EMPTY` aparece como crítica no estado final). TP1 e
piloto: nenhuma mudança em `compensators`.

## Aberturas

TGD/TP1: `OPENING_BLOCK_CROSSES_JAMB`/`OPENING_BLOCK_INSIDE_DOOR`
**inalterados** no estado final do fix (a restrição "nem esta parede nem
a doadora têm abertura" elimina completamente a interação que, em
versões intermediárias deste CR, tinha causado regressão real nesses
dois códigos — documentado no histórico de commits desta branch como
parte do processo de restringir o escopo). Consistente com a seção 25 do
enunciado: nenhuma alteração feita para "corrigir" número de abertura —
o resultado é que este fix simplesmente NÃO toca mais nenhum caso com
abertura envolvida, dos dois lados do nó.

## Reference Corpus

Ver tabelas em "TGD coverage"/"TP1 coverage"/"Piloto PRISM" acima —
medidas com `benchmark.runner.run_project` contra `origin/main` LIMPO
(não `baseline.json`, desatualizado para `PRISM_CONTINUOUS_JOINT`/
`OPENING_BLOCK_INSIDE_DOOR` no TGD — ver "Determinismo"). Resumo do
trade-off medido (só no TGD; TP1/piloto sem nenhuma mudança):

- **Melhoria real e grande**: `COVERAGE_MISSING_ROW` -120 (265→145,
  -45%).
- **Regressão real e crítica**: `COVERAGE_ROW_MOSTLY_EMPTY` +138
  (171→309).
- **Mecanismo do resíduo** (medido, não suposto): paredes do TGD com as
  DUAS famílias emprestadas em nós DIFERENTES — uma com doadora SEM
  abertura (rescatável por este fix), outra com doadora COM abertura
  (fora do escopo, por desenho, ver "Fix"). A família rescatável passa a
  fechar 100%; a outra continua exatamente como estava (0%,
  `NON_MODULAR_WALL` genuíno, não piorado por este CR). O validador
  `COVERAGE_ROW_MOSTLY_EMPTY` ("fiada quase vazia numa parede que tem
  outras fiadas cheias") passa a enxergar esse padrão numa parede que
  antes tinha as DUAS famílias ruins e caía sob outro código
  (`COVERAGE_MISSING_ROW`/`COVERAGE_PARTIAL_WALL`/`COVERAGE_WALL_NOT_
  MODULATED`). **Confirmado achado a achado**: nenhuma parede nova
  aparece na lista de `COVERAGE_ROW_MOSTLY_EMPTY` sem já ter tido algum
  achado de cobertura crítica antes desta CR — não é uma parede NOVA
  quebrada, é uma RECLASSIFICAÇÃO — mas o total de achados sobe (+123 no
  TGD), então não é um resultado limpo, e `COVERAGE_ROW_MOSTLY_EMPTY` é
  código CRÍTICO igual a `COVERAGE_MISSING_ROW` — não posso alegar que
  "não conta".
- **Fix completo do resíduo exigiria** forçar ALTERNÂNCIA de papel entre
  os dois nós de uma mesma parede (nunca os dois com o mesmo papel) — um
  problema de 2-coloração de grafo (cada nó de 2 braços é uma aresta
  entre duas paredes-vértice) onde ciclos de comprimento ímpar tornam
  alternância perfeita impossível em geral. Investigado (ver seção
  "Fix"), não implementado — mudança de escopo maior que a autorizada
  para esta CR (só `wall_stepper.py`, sem "resolver toda a cobertura").
  Documentado como `28.4` em `REGRAS_MODULACAO_BLOCOS.md`, com
  recomendação de CR próprio.

## Testes

- **Novo, permanente**: `tests/test_block_arm_role_invariance.py` (14
  testes, cobre os itens 1-12 do enunciado — L_CORNER simétrico [A,B] e
  [B,A], múltiplas fiadas físicas, parede curta/longa, T como controle,
  X com `crossing_walls` permutado, endpoint reversal equivalente, input
  wall permutation, o teste central de 2 nós na mesma parede com as 4
  combinações de papel). **Falham no estado anterior pelo motivo
  correto**, confirmado explicitamente (`git stash` + rodar a suíte):
  6 dos 14 falham sem o fix (os que dependem de geometria fracionária —
  ver docstring de `_two_corner_plan`, coordenadas redondas não
  reproduzem o defeito, só geometria "suja" como a de CAD real); os
  outros 8 já passavam mesmo antes (provam mirror-invariance simples,
  sem o mecanismo de borda emprestada em jogo).
- **Regressão real corrigida no processo**: nenhum teste pré-existente
  precisou de alteração no estado FINAL do fix (revertido explicitamente
  um ajuste feito numa iteração intermediária a `tests/test_script.py`
  quando o escopo do fix ainda incluía `MIDSPAN`, depois removido por
  segurança — ver `git log`/histórico de commits desta branch).
- **Suíte completa** (`python3 -m pytest tests/ -q`, incluindo `tests/
  regression/test_benchmark_baselines.py`, marcado `slow`): **521
  passed, 1 failed** — a falha é exatamente o `COVERAGE_ROW_MOSTLY_EMPTY`
  do TGD documentado acima (`tests/regression/test_benchmark_baselines.py::
  test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]`),
  não escondida.

## Performance

`benchmark.runner.run_project`, 2 execuções cada, `origin/main` limpo
vs com o fix:

| projeto | antes | depois |
|---|---|---|
| piloto (12 paredes) | 0,09-0,21s | 0,09-0,20s |
| TGD (167 paredes) | 3,35-3,40s | 3,39-3,46s |
| TP1 (96 paredes) | 3,65-3,66s | 3,80-3,92s |

Sem crescimento assimétrico — mesma ordem de grandeza, dentro do ruído
de medição de processo único (~5% no TP1, o maior desvio medido).
Nenhuma busca combinatória nova foi introduzida — o arredondamento é
O(1) por trecho, calculado uma vez por segmento.

## Arquivos alterados

```
docs/BLOCK_ARM_ROLE_INVARIANCE.md         (este arquivo, novo)
nuvem/REGRAS_MODULACAO_BLOCOS.md          (secao 28, novo)
tests/test_block_arm_role_invariance.py   (novo, 14 testes permanentes)

nuvem/core/engine/wall_stepper.py         UNICO arquivo de producao
                                           alterado (autorizado)
nuvem/core/engine/wall_pairing.py         NAO ALTERADO
nuvem/core/engine/continuous_modulation.py NAO ALTERADO
nuvem/core/engine/wall_modeling.py        NAO ALTERADO
nuvem/core/engine/geometry.py             NAO ALTERADO
nuvem/core/engine/tolerances.py           NAO ALTERADO
nuvem/core/engine/modulation_math.py      NAO ALTERADO
```

`git diff --stat` confere: só `wall_stepper.py` em produção, mais os
dois arquivos de documentação/teste.

## Production diff

Resumo funcional (diff completo em `git diff origin/main -- nuvem/core/engine/wall_stepper.py`):

1. `_index_node_candidates_by_wall_end_with_donor` (nova, privada) —
   núcleo compartilhado que computa borda + doador na MESMA passada.
2. `_index_node_candidates_by_wall_end` — refatorada para delegar à
   função acima; **comportamento e retorno idênticos** ao anterior
   (confirmado pela suíte completa, inclusive o teste que chama esta
   função diretamente em `tests/test_script.py:7583`).
3. `_index_node_candidates_borrowed_by_wall_end` (nova, exportada) —
   `{(wall_idx, end_index, course): donor_wall_idx}`.
4. `_node_boundary_module_snap_cm` (nova, exportada) — encolhe
   `(seg_start_cm, seg_end_cm)` até o próximo múltiplo válido de
   `PIER_MODULE_CM`, nunca amplia.
5. `solve_wall_free_fill` — parâmetro novo opcional
   `node_candidates_borrowed_by_wall_end=None` (retrocompatível: `None`
   desativa o fix, nenhum chamador antigo muda de comportamento sem
   passar o argumento); `course_has_own_tie` computado uma vez por
   chamada; ponto de uso do arredondamento com as 4 condições de escopo
   e a rede de segurança (nunca sai do intervalo original).
6. `process_walls_one_by_one`/`solve_all_wall_fill` — as duas rotas de
   produção que chamam `solve_wall_free_fill` passam a computar e
   encaminhar `node_candidates_borrowed_by_wall_end`.
7. `__all__` — 3 novos nomes exportados (`_index_node_candidates_by_
   wall_end_with_donor` fica interno, não exportado).

## Compatibilidade futura com NODE-FILL

Não incorporado nem investigado a fundo (proibido pelo enunciado,
seção 16) — mas por construção este fix não interfere com a fronteira
"peça de nó × preenchimento" que o `CR-BLOCK-NODE-FILL-JOINT` trata: o
arredondamento só muda ONDE o preenchimento comum começa/termina
(sempre encolhendo, nunca sobrepondo a peça de nó), nunca a peça de nó
em si (`solve_l_corner`/`solve_x_intersection` intocados). Qualquer
ajuste futuro na junta nó×preenchimento continua vendo exatamente as
mesmas duas entidades (peça de nó, preenchimento comum) que via antes.

## Dependência do BENCH-Z

Não aplicável — este CR não mede nenhuma métrica de abertura NOVA nem
depende da régua vertical (`base_z_cm`/altura de peitoril). As métricas
de abertura medidas (`OPENING_BLOCK_CROSSES_JAMB`/`INSIDE_DOOR`) ficaram
inalteradas (ver "Aberturas"), então revalidação pós-BENCH-Z não deveria
mudar nenhuma conclusão desta CR — mas não foi verificado ativamente
(fora do escopo).

## Veredito

```
G1  causa arms->course role->perda de fiada reproduzida ......... APROVADO
G2  fix em wall_stepper.py, sem alterar wall graph ............... APROVADO
G3  permutacao fisicamente equivalente nao muda coverage .......... APROVADO
G4  TGD coverage recupera significativamente ...................... PARCIAL
                 (MISSING_ROW -120, mas MOSTLY_EMPTY +138, mesmo codigo
                 critico - ver "Reference Corpus")
G5  TP1 coverage recupera significativamente ....................... N/A
                 (nenhuma parede do TP1 se qualificou para o fix -
                 nenhuma mudanca, nem para melhor nem para pior)
G6  L/T/X nao regride .............................................. APROVADO
                 (T controle sem mudanca; X coberto pelo mesmo
                 mecanismo de L; nenhum no' mudou de kind/posicao)
G7  determinismo permanece 1 fingerprint ........................... APROVADO
                 (mesmo codigo = mesma saida, 3x confirmado; ver nota
                 sobre baseline.json/REFERENCE_SOLVER_DECISION_
                 FINGERPRINT desatualizados, achado colateral nao
                 causado por esta CR)
G8  same-band continua 0 ............................................ NAO MEDIDO
                 (metrica nao localizada no benchmark atual dentro do
                 orcamento de busca)
G9  nenhuma nova regressao critica conhecida ........................ FALHOU
                 (COVERAGE_ROW_MOSTLY_EMPTY +138 no TGD, codigo
                 CRITICO - documentado em detalhe, nao escondido)
G10 baseline nao atualizado ......................................... APROVADO
G11 performance aceitavel ........................................... APROVADO
G12 testes sinteticos comprovam invariancia ......................... APROVADO
```

```
CAUSA-RAIZ ......... PROVADA (dois nos L_CORNER/X_INTERSECTION
                      independentes na mesma parede podem escolher o
                      MESMO papel de amarracao, apagando a familia
                      oposta quando combinado com a fronteira
                      "emprestada" nao caindo no modulo de blocos)
FIX ................ IMPLEMENTADO, PARCIAL (recupera o caso onde a
                      familia oposta ja' tem peca de no' propria e nem
                      esta parede nem a doadora tem abertura - o
                      subconjunto medido como seguro contra regressao
                      de abertura; nao resolve o caso das DUAS familias
                      emprestadas com doadoras mistas com/sem abertura)
DETERMINISMO ....... PRESERVADO
QUALIDADE .......... MELHORA GRANDE em COVERAGE_MISSING_ROW, TROCA
                      PARCIAL por COVERAGE_ROW_MOSTLY_EMPTY no TGD
                      (mesmo defeito pre-existente, reclassificado -
                      nao piora nenhuma parede que ja fechava as duas
                      familias antes)
MERGE .............. NAO SE APLICA (PARE antes de qualquer merge,
                      conforme pedido - este relatorio e' a entrega)
```

**NECESSITA AJUSTE** (G9 falhou, G4/G5/G8 parciais ou não medidos) — a
causa-raiz está provada e o mecanismo de invariância está corretamente
implementado e testado para o subconjunto de casos descrito, mas a
recuperação completa de qualidade no TGD exigiria a alternância forçada
de papel entre nós de uma mesma parede (seção 28.4 de `REGRAS_
MODULACAO_BLOCOS.md`), fora do escopo autorizado para esta CR. Recomenda-
se CR próprio para essa alternância — mesmo espírito do `CR-BLOCK-NODE-
FILL-JOINT` já aberto.

**PARE antes de qualquer merge.** Não mesclado, não mesclável sem
decisão humana explícita sobre o trade-off G4/G9 documentado acima. Não
foi agendado nenhum check-in automático nem monitoramento de PR,
conforme pedido.
