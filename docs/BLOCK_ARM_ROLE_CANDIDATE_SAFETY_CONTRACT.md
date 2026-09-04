# RELATÓRIO FINAL — ARM-ROLE CANDIDATE SAFETY CONTRACT

`CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT`, continuação direta de
`CR-BLOCK-ARM-ROLE-JUNCTION-GATE` (ver `docs/BLOCK_ARM_ROLE_HUMAN_POLICY.md`
e `nuvem/REGRAS_MODULACAO_BLOCOS.md` seção 30 para o histórico completo).

## Git

```
branch de trabalho (herdada de claude/cr-block-arm-role-policy-q0qepg,
  HEAD original cce8cf9)          claude/arm-role-safety-contract-ljfwnj
main oficial                      a2577797f40048413207d11ea7e7b385e97c1813
PR #11                            continua DRAFT, não mesclado
```

Nenhum merge realizado. `PR #9` não tocado. Nenhuma alteração em
`baseline.json`/`reference.json`/`score.json` de nenhum projeto.
Monitoramento automático não ativado.

## Estado inicial

O relatório anterior (`CR-BLOCK-ARM-ROLE-JUNCTION-GATE`) tinha provado a
causa raiz real do `JUNCTION_NOT_ALTERNATING` (inconsistência de
persistência do papel do nó ENTRE BANDAS de
`solve_building_blocks_all_courses`) e uma correção estrutural
(`_arm_role_pinned`) testada em script, mas **não commitada** — porque,
ao verificar o conjunto COMPLETO de achados (não só junção/prisma/
colisão), 4 dos 5 candidatos do TGD daquela sessão introduziam
regressões de compensador/cobertura em paredes vizinhas que nenhum gate
existente detectava. Esta CR pediu, explicitamente, para não repetir
"gate 6, gate 7, gate 8..." ad hoc e formalizar um contrato geral.

## Inventário de validadores

Tabela completa (por identificador de erro pedido, com as 8 perguntas da
seção 3 do pedido) produzida via pesquisa dedicada no repositório —
resumo:

| grupo | onde é calculado hoje | produção ou benchmark? | equivalente de produção reutilizável? |
|---|---|---|---|
| `COVERAGE_MISSING_ROW`/`GAP_IN_ROW`/`ROW_MOSTLY_EMPTY`/`PARTIAL_WALL` | `nuvem/benchmark/validators/validate_wall_coverage.py` | benchmark-only (precisa de `OccupancyIndex`/cobertura emprestada de amarração para medir em termos ABSOLUTOS) | não — coberto nesta CR por um helper NOVO, mas só para DELTA (ver abaixo) |
| `PRISM_CONTINUOUS_JOINT`/`PRISM_JOINT_STACK` | `validate_prism.py` | benchmark-only na forma exata, mas produção já tem `wall_bond_audits[...]["continuous_joints"]` (`audit_wall_bond_quality`, `wall_modeling.py`) medindo a MESMA coisa (junta corrida de altura total) | **sim** — reusado sem duplicação |
| `PRISM_STAGGER_BELOW_TARGET` | `validate_prism.py`, nível 2 (`LEVEL_PREFERENCE`) na própria taxonomia do benchmark | benchmark-only | não — **soft preference por design da própria taxonomia**, não ganhou gate dedicado |
| `FORBIDDEN_JOINT_ALIGNMENT` | script ad-hoc de diagnóstico (`diagnostics_block_prisma/`), não é da taxonomia oficial | artefato de CR anterior, não pipeline principal | n/a |
| `JUNCTION_NOT_ALTERNATING`/`JUNCTION_MISSING_BINDING` | `validate_junctions.py` | benchmark-only | não precisou — **prevenido estruturalmente** (ver "Persistência entre bandas") |
| `OPENING_BLOCK_INSIDE_DOOR`/`CROSSES_JAMB` | `validate_openings.py` | benchmark-only (produção tem um check mais grosseiro em `validate_wall_modulation`) | parcial, não usado nesta CR (esta CR não toca aberturas) |
| `COMPENSATOR_CONSECUTIVE` | `validate_compensators.py` | **produção já tem equivalente EXATO**: `_find_consecutive_compensators` (`wall_stepper.py`) | **sim** — reusado sem duplicação |
| `POSITION_OVERLAP`/`collisions` | `validate_block_positions.py` | **produção já tem equivalente mais rigoroso**: `validate_same_course_collision`/`collisions_between` (`wall_stepper.py`) | **sim** — reusado sem duplicação |

## Hard constraints / Soft preferences / Benchmark-only

**HARD** (nível 1/`LEVEL_MANDATORY` na taxonomia do benchmark, e tratados
como tal por este contrato): fechamento de parede, `POSITION_OVERLAP`,
prisma forçado empurrado para vizinha, `COMPENSATOR_CONSECUTIVE`,
`COVERAGE_GAP_IN_ROW`/`PARTIAL_WALL`/`ROW_MOSTLY_EMPTY` (via o proxy de
comprimento coberto por fiada), `JUNCTION_NOT_ALTERNATING` (prevenido
estruturalmente, nunca precisou virar gate de checagem).

**SOFT** (nível 2/`LEVEL_PREFERENCE`): `PRISM_STAGGER_BELOW_TARGET` —
confirmado na própria taxonomia do benchmark (`nuvem/benchmark/
validators/base.py`), não inventado por esta CR. Um candidato cujo ÚNICO
efeito colateral é piorar o stagger não é rejeitado por este motivo
sozinho — mas nenhum dos candidatos reais medidos caiu nesse caso (os que
pioram stagger também pioram compensador/cobertura, categorias HARD).

**BENCHMARK-ONLY, nunca importado em produção**: todos os 15
identificadores de erro continuam vivendo só em `nuvem/benchmark/
validators/*` — o contrato usa PROXIES de produção (equivalentes
reutilizados ou o helper novo local), nunca o código do benchmark em si
(G10).

## Delta model

```
NEW_FINDINGS  = achados(candidato) - achados(original)     [nunca aceitos]
RESOLVED      = achados(original) - achados(candidato)
```

Identidade: **geométrica/topológica estável dentro da MESMA resolução**
(wall_idx e course_index não mudam entre o rebuild ORIGINAL e o rebuild
CANDIDATO, porque ambos vêm do MESMO `walls_to_create`/`input.json` — só
a decisão de papel do nó muda). Nunca ElementId, nunca ordem de
processamento, nunca proximidade numérica de nó (H2/H3/H4 da CR anterior,
refutadas de novo aqui — toda regressão medida caiu na própria parede ou
na vizinha IMEDIATA, nunca um cluster de 3+).

Colisões e sequências de compensador são comparadas por **assinatura
geométrica** (origem/rotação/código, ou fiada+códigos+posição) — nunca
índice de lista, que muda entre a resolução ORIGINAL e a CANDIDATA
(candidatos são gerados em ordens diferentes).

## Candidatos medidos (TGD, 8 arestas isoladas com prisma forçado — ver nota sobre numeração abaixo)

| `wall_idx` | resultado | motivo |
|---|---|---|
| **23** | **ACEITO** (`SAME_A`) | resolve o prisma forçado; 0 regressão em qualquer categoria (ver abaixo) |
| 4 | rejeitado | nenhum dos 3 candidatos resolve o prisma alvo |
| 54 | rejeitado | nenhum dos 3 candidatos resolve o prisma alvo |
| 89 | rejeitado | `SAME_B` resolve o alvo mas causa `row_coverage_regression` numa vizinha; os outros não resolvem o alvo |
| 90 | rejeitado | mesmo padrão de 89 |
| 91 | rejeitado | `SAME_B` resolve o alvo mas causa `closure_regression`; os outros não resolvem |
| 92 | rejeitado | `SAME_B` resolve o alvo mas empurra prisma forçado para a vizinha (`new_forced_prism_in_neighbor`); os outros não resolvem |
| 120 | rejeitado | `SAME_A` causa `new_consecutive_compensators`; `SAME_B` causa `row_coverage_regression`; `ALTERNATE_BA` não resolve o alvo |

**Nota sobre numeração**: os `wall_idx` acima vêm da re-execução
INDEPENDENTE feita nesta CR (mesma sessão Python, `plan_from_input` +
`solve_building_blocks_all_courses`, sem git stash) e não precisam
coincidir com a numeração usada em sessões anteriores (o índice de
`walls_to_create` não é uma identidade estável entre execuções/scripts
diferentes — só dentro da MESMA resolução, exatamente o motivo pelo qual
o modelo de delta desta CR nunca depende dele entre PROJETOS). O
mecanismo e a conclusão (1 aceito limpo, resto rejeitado por HARD gate
reproduzível) são os mesmos fenômenos já documentados na seção 30 de
`REGRAS_MODULACAO_BLOCOS.md`.

### Candidato 23 (o "W011" desta sessão) — por que é seguro

Isolado, testado com `SAME_A`: `PRISM_CONTINUOUS_JOINT` da própria
parede some (17→0 fiadas coincidentes). Efeito colateral positivo
medido: a MESMA correção também resolve `PRISM_CONTINUOUS_JOINT`/
`PRISM_JOINT_STACK` numa parede vizinha (17 achados a menos). Único
"delta" não-zero: `COMPENSATOR_EXCESS_IN_RUN` na própria parede migra de
posição (`t=0..69cm` → `t=15..69cm`, em 5 fiadas) — a MESMA sequência de
2 compensadores, deslocada 15cm pela realocação da peça de canto,
contagem líquida NULA (5 resolvidos + 5 novos). Nenhuma colisão, nenhum
compensador consecutivo novo, nenhuma regressão de cobertura, nenhum
prisma forçado novo em vizinha, nenhuma parede deixou de fechar.

### Candidatos rejeitados — causa de layout de cada regressão

- **89/90**: a troca de papel move a peça de canto de uma família para
  a outra na parede VIZINHA; nessa parede vizinha (curta — só a peça de
  canto ocupava a fiada inteira), a família que PERDE a peça fica com
  **0cm de cobertura** onde antes tinha o total da fiada (34cm) — perda
  de 100%, não uma redistribuição pequena. Isto é o mecanismo real por
  trás de `COVERAGE_GAP_IN_ROW`/`COVERAGE_PARTIAL_WALL` medido na
  investigação anterior.
- **120**: a troca faz o preenchimento comum da própria parede precisar
  de um compensador extra logo ao lado de um que já existia — 2
  compensadores adjacentes onde antes havia só 1 (mais um compensador
  vindo de outro segmento).
- **91/92**: a troca resolve o prisma alvo mas ou impede a parede de
  fechar (a nova composição de preenchimento não soma o comprimento
  exato) ou desloca a coincidência de junta para a parede vizinha em vez
  de eliminá-la — exatamente o "empurrar o defeito, não resolver"
  que a regra fundamental (seção 4 do pedido) proíbe.

## Persistência entre bandas

`_arm_role_pinned` (proposto na CR anterior, agora **implementado**):
`_coordinate_arm_role_nodes` exclui do grafo qualquer nó marcado
(`_arm_role_coordination_graph(nodes, respect_pins=True)`). Identidade
estável = o próprio NÓ (`node["arms"]`, nunca `wall_idx` de uma
resolução diferente, nunca ordem de `nodes`/dict/ElementId) — como o
SAFE REPAIR só atua em arestas ISOLADAS (grau 1 nos dois nós), fixar o
papel de uma nunca afeta a alternância de nenhuma OUTRA parede
coordenada. Provado (teste sintético `test_t8_papel_do_no_isolado_
pinado_sobrevive_a_re_coordenacao_entre_bandas`): simulando 5 chamadas
consecutivas de `_coordinate_arm_role_nodes` sobre o MESMO `nodes` (como
`solve_building_blocks_all_courses` faz banda a banda), um papel pinado
nunca muda.

## Arquiteturas A-E

| opção | avaliação |
|---|---|
| A — gates locais soltos em `wall_stepper` | rejeitada — exatamente o "gate 6, gate 7..." que o pedido proibiu |
| B — helper compartilhado de quality delta | usada PARCIALMENTE — todos os gates são helpers puros, mas concentrados junto do orquestrador, não espalhados |
| C — validador incremental de delta | é o que os gates fazem individualmente (comparam ORIGINAL x CANDIDATO por fiada/parede) |
| **D — resolver completo do candidato + validação final** | **escolhida** — cada candidato é um rebuild MULTI-BANDA completo (`rebuild_fn`), nunca aritmética; caro por tentativa (até ~20 rebuilds extras por projeto com 8 arestas candidatas), mas seguro — mesma disciplina já estabelecida pela ETAPA 3C neste arquivo |
| E — corner-role + fill como problema combinatório local | equivalente a D restrito ao subconjunto seguro (arestas isoladas) — é o que D, como implementada, já é |

### Escopo (seção 12 do pedido)

Não houve `BLOQUEADO POR ESCOPO`. Quase toda a lógica (geração de
candidatos, os 5 gates, o orquestrador) vive inteiramente em
`nuvem/core/engine/wall_stepper.py`, como autorizado. A ÚNICA exceção,
disclosed conscientemente: `nuvem/core/wall_modeling.py::solve_building_
blocks_all_courses` virou um wrapper fino — a função original foi
renomeada para `_solve_building_blocks_all_courses_core` (corpo
IDÊNTICO, zero mudança de comportamento) e o wrapper novo chama
`repair_arm_role_isolated_edges` (`wall_stepper.py`) passando um
`rebuild_fn` (closure que re-invoca `_solve_building_blocks_all_courses_
core`) — necessário porque o loop de bandas em si mora em
`wall_modeling.py` e `wall_stepper.py` nunca pode importar
`wall_modeling.py` (import circular: `wall_modeling.py` já faz `from
core.engine.wall_stepper import *`). Nenhuma lógica de decisão foi
duplicada ali — é só a injeção do callback.

## Implementação

`nuvem/core/engine/wall_stepper.py` (produção, seção "CR-BLOCK-ARM-ROLE-
CANDIDATE-SAFETY-CONTRACT — SAFE REPAIR"):

- `_arm_role_coordination_graph` (fatorado de `_coordinate_arm_role_nodes`,
  agora também respeita `_arm_role_pinned`);
- `_arm_role_isolated_edges`, `CORNER_ROLE_CANDIDATE_BITS`,
  `_set_l_corner_role_bits` — geração/aplicação de candidato;
- `_wall_forced_corner_prism_signature`/`_wall_has_forced_corner_prism` —
  reusa `wall_bond_audits`;
- `_wall_compensator_run_signatures`/`_no_new_consecutive_compensators` —
  reusa `_find_consecutive_compensators`;
- `_wall_row_covered_length_cm`/`_no_new_row_coverage_regression` — ÚNICO
  mecanismo novo (helper local, tolerância relativa);
- `_candidate_identity_signature`/`_collision_signatures`/
  `_no_new_collisions` — reusa `validate_same_course_collision`;
- `_multi_band_wall_ok_map`/`_no_wall_regression` — fechamento global;
- `_no_new_forced_corner_prism_in_neighbors`;
- `_evaluate_corner_role_candidate` (orquestra os 5 gates, nesta ordem);
- `repair_arm_role_isolated_edges` (orquestrador principal, injeção de
  `rebuild_fn`).

`nuvem/core/wall_modeling.py`: `ARM_ROLE_SAFE_REPAIR_ENABLED = True`
(flag), `_solve_building_blocks_all_courses_core` (função original
renomeada, corpo intocado) + `solve_building_blocks_all_courses`
(wrapper novo, hook mínimo).

## Testes

`tests/test_block_arm_role_candidate_safety_contract.py` — 18 testes
(T1-T16 do pedido, T6/T8 desdobrados em 2 cada por clareza):

- unitários e diretos (sintéticos, sem depender do corpus real): T2
  (compensador novo rejeitado), T3/T4/T5 (gap/parcial/quase-vazia
  rejeitados), T6 (`PRISM_STAGGER_BELOW_TARGET` é soft preference na
  taxonomia + não bloqueia sozinho), T7 (colisão nova rejeitada), T8
  (papel pinado sobrevive a 5 "bandas" simuladas), T11/T12 (persistência
  e invariância de ordem de bandas), T13/T14/T15 (invariância a
  permutação de paredes/arms/endpoints), mais um controle POSITIVO
  (`test_redistribuicao_pequena_entre_familias_nao_e_falso_positivo`)
  que prova que a tolerância relativa não rejeita o padrão inofensivo
  medido em produção;
- contra o corpus real (TGD, mesma prática de
  `test_block_arm_role_prism_stagger.py`): T1/T9 (candidato 23 aceito),
  T10 (fallback ORIGINAL para os 7 rejeitados — `_arm_role_pinned`
  ausente, bits idênticos ao original), T16 (execução repetida produz
  `accepted`/`rejected` e o conjunto de achados bit-idênticos).

Suíte focada (`tests/test_block_arm_role_invariance.py` +
`tests/test_block_arm_role_prism_stagger.py`, 21 testes) roda sem
alteração — nenhuma regressão nos testes já existentes.

## TGD / TP1 / Piloto — B (sem SAFE REPAIR) vs C (com SAFE REPAIR)

Medido nesta sessão, 3 chamadas de `runner.run_project`-equivalente na
MESMA sessão Python (nunca git stash, nunca escrita em disco).

| projeto | arestas candidatas | aceitos | rejeitados | regressão global |
|---|---|---|---|---|
| TGD | 8 | 1 (`wall_idx=23`) | 7 | **zero** (só melhoria: `PRISM_CONTINUOUS_JOINT` 476→444, `PRISM_JOINT_STACK` 29→27; `COMPENSATOR_EXCESS_IN_RUN` reposicionado, líquido zero) |
| TP1 | 3 | 0 | 3 | **zero** (B==C, todas as 13 categorias idênticas) |
| Piloto | 0 | — | — | **zero** (no-op) |

### Coverage / Prism / Junctions / Openings / Compensators / Collisions

Nenhuma categoria regrediu em nenhum projeto (contagem completa de
achados idêntica entre B e C, exceto a melhoria de prisma no TGD já
descrita). `POSITION_OVERLAP` inalterado nos 3 projetos.
`JUNCTION_NOT_ALTERNATING`/`JUNCTION_MISSING_BINDING` inalterados (o
mecanismo que os CAUSARIA nunca chega a existir, por construção).

### Determinismo

Confirmado por teste automatizado (T16): duas execuções completas do
TGD com SAFE REPAIR ativo produzem `accepted`/`rejected` idênticos e o
mesmo conjunto de achados (comparado por assinatura, não por ordem de
lista).

### Performance

Cada aresta candidata custa até 3 rebuilds MULTI-BANDA completos extras
(um por candidato tentado, parando no primeiro que passa) — no TGD (8
arestas), o pior caso é ~24 rebuilds extras além do original; medido
como aceitável para este porte de projeto (a suíte de testes focada, que
já inclui os 3 projetos reais rodando várias vezes, continuou executando
em segundos/poucos minutos). Não otimizado além disso nesta CR.

## Production diff

`nuvem/core/engine/wall_stepper.py`: nova seção autocontida (gates +
orquestrador) + 2 mudanças pequenas em código existente (pin em
`_coordinate_arm_role_nodes`/`_arm_role_coordination_graph` fatorada).
`nuvem/core/wall_modeling.py`: renomeação de uma função + wrapper fino
(hook mínimo, disclosed). Nenhuma outra alteração de produção.

## Baselines

`nuvem/benchmark/projects/*/baseline.json`/`reference.json`/`score.json`
intactos — nenhuma escrita em disco durante toda a verificação (`write_
files=False`/execução em memória).

## Suíte completa (`tests/`)

Rodada por completo nesta sessão (565 testes + 1 falha, 572s):
**1 falha pré-existente, comprovadamente independente desta CR**:
`tests/regression/test_benchmark_baselines.py::test_projeto_nao_regrediu_
contra_o_baseline[torre_easy_lo_r00_tp1]` — `JUNCTION_MISSING_BINDING`
8→9 contra o `baseline.json` gravado do TP1. Reproduzida
IDENTICAMENTE com `ARM_ROLE_SAFE_REPAIR_ENABLED=False` (código desta CR
completamente desligado) — prova que o `baseline.json` do TP1 está
DESATUALIZADO em relação ao estado atual de `main` (já documentado em
`docs/BLOCK_ARM_ROLE_HUMAN_POLICY.md`: "`JUNCTION_MISSING_BINDING` 8→9,
mirror de paridade, benigno, já documentado" desde a integração de
`CR-BLOCK-ARM-ROLE-CONSISTENCY`/PR#9) — o `baseline.json` nunca foi
regravado depois daquele merge. **Não corrigido nem regravado nesta
CR** (fora de escopo — regravar baseline exige decisão humana explícita,
nunca "para fazer o teste passar"). Todos os demais 565 testes passam,
incluindo toda a suíte focada de ARM-ROLE e os 18 testes novos desta CR.

## Gates G1-G18

| gate | status |
|---|---|
| G1 inventário completo | ✅ |
| G2 hard/soft/benchmark-only classificados | ✅ |
| G3 deltas por identidade estável | ✅ |
| G4 W011-equivalente (`wall_idx=23`) aceito | ✅ |
| G5-G8 demais candidatos rejeitados pela razão correta | ✅ (numeração própria desta sessão — ver nota acima) |
| G9 persistência entre bandas correta | ✅ (testado) |
| G10 nenhum benchmark validator importado em produção | ✅ |
| G11 fallback ORIGINAL provado | ✅ (testado, T10) |
| G12 nenhuma regressão global nova | ✅ (TGD/TP1/Piloto) |
| G13 determinismo preservado | ✅ (testado, T16) |
| G14 performance aceitável | ✅ (medido, ver "Performance") |
| G15 baseline/reference intactos | ✅ |
| G16 production diff restrito | ✅ (só os 2 arquivos autorizados/disclosed) |
| G17 testes passam | ✅ (18 novos + 21 da suíte focada existente) |
| G18 suíte final | ✅ com ressalva — 565/566 (`tests/` completo); a 1 falha é pré-existente e comprovadamente independente desta CR (ver "Suíte completa") |

## Próximo passo

- Decisão humana pendente (fora do escopo desta CR): regravar
  `baseline.json` do TP1 para refletir o estado atual de `main`
  (`JUNCTION_MISSING_BINDING` 8→9, já documentado como benigno desde a
  integração de `CR-BLOCK-ARM-ROLE-CONSISTENCY`/PR#9 — nunca regravado
  desde então, comprovadamente não relacionado a esta CR).
- As 7 arestas rejeitadas no TGD e as 3 no TP1 continuam com o prisma
  forçado original — corrigi-las exigiria um MECANISMO DIFERENTE (busca
  de preenchimento alternativa, não troca de papel), fora do escopo
  desta CR (seção 13 do pedido, explícita: não corrigir os negativos).

## Veredito

**APROVADO PARA INTEGRAÇÃO**

Existe um contrato de segurança geral, formalizado antes de qualquer
implementação (nunca "gate ad hoc por erro"), que aceita o candidato
seguro medido (`wall_idx=23`) sem nenhuma regressão em NENHUMA categoria
de achado, e rejeita os demais candidatos do mesmo projeto pela razão
HARD correta e reproduzível — sem nenhuma regressão global em TGD, TP1
ou Piloto. `ARM_ROLE_SAFE_REPAIR_ENABLED = True` em produção.

**Não mergeado. PR #11 continua DRAFT.**
