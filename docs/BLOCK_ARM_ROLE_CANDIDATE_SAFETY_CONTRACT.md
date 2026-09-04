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

**Não mergeado. PR #12 continua DRAFT.**

============================================================

# CONTINUAÇÃO — PRE-INTEGRATION AUDIT (2026-09-04)

Auditoria final antes de qualquer integração do PR #12, pedida
explicitamente: (A) sincronizar a branch com `origin/main`; (B)
determinar exatamente o que significa `JUNCTION_MISSING_BINDING` 8→9 no
TP1 antes de qualquer decisão sobre `baseline.json`.

## Git

```
main anterior (merge-base)   a2577797f40048413207d11ea7e7b385e97c1813
main atual (origin/main)     0ff784e70869ae48b232f416ac0784f45f7f1703
                              (1 commit: "docs: define reviewed
                              geometry proposals" - docs-only,
                              nuvem/REGRAS_MODULACAO_BLOCOS.md)
branch antes                 69153f59f65dc21cdd7091b8cf4987c6eefa8a9d
branch depois (merge)        5bb5553 (merge commit, MERGE normal -
                              nunca rebase)
```

## Conflitos

Um único conflito, em `nuvem/REGRAS_MODULACAO_BLOCOS.md`: `origin/main`
adicionou uma NOVA seção `## 29.` ("assistente de propostas
geométricas") no mesmo ponto onde esta branch já tinha `## 29.
CR-BLOCK-ARM-ROLE-INVARIANCE` (renumerada de 28→29 pelo PR#9, antes
desta CR). Resolvido preservando os DOIS lados integralmente: a seção
nova da main manteve o número 29; as três seções ARM-ROLE desta branch
foram renumeradas 29→30, 30→31, 31→32 (incluindo as subseções 29.1-29.7
→ 30.1-30.7 e todas as referências cruzadas internas - "ver seção 30"
→ "ver seção 31", etc.). Nenhum conteúdo apagado. Nenhum outro arquivo
conflitou.

## Regra nova da main preservada

Confirmado: `## 29. REGRA OBRIGATÓRIA — assistente de propostas
geométricas, com aprovação explícita` (5 itens sobre propor alterações
geométricas com aprovação humana explícita) está intacta, verbatim, no
arquivo final.

## `JUNCTION_MISSING_BINDING` — investigação completa

### A — origin/main (0ff784e)

8 ocorrências, TODAS no mesmo nó físico: encontro L em `(6177.25,
949.95)`, paredes `W039`↔`W041`, fiadas **ÍMPARES** (1, 3, 5, 7, 9, 11,
13, 15).

### B — branch, SAFE REPAIR OFF

9 ocorrências, MESMO nó físico, fiadas **PARES** (0, 2, 4, 6, 8, 10, 12,
14, 16).

### C — branch, SAFE REPAIR ON

Idêntico a B (9 ocorrências, mesmas fiadas pares) — confirma que o
Candidate Safety Contract não participa deste achado.

## 9ª ocorrência (na verdade: TODAS as ocorrências de B são "novas" em
relação a A, por identidade geométrica — nó + fiada)

`NEW_BINDING_FINDINGS = findings(B) - findings(A)` por identidade
geométrica (ponto do nó + índice de fiada, nunca posição de lista nem
`wall_idx`, que é só diagnóstico): as 9 fiadas pares de B são todas
"novas" em relação às 8 fiadas ímpares de A (nenhuma delas coincide) —
e as 8 fiadas ímpares de A deixam de aparecer em B (resolvidas). Não há
uma "9ª ocorrência isolada": é o MESMO defeito espelhado de paridade
por completo.

- **Projeto**: `torre_easy_lo_r00_tp1`.
- **Parede geométrica**: encontro L entre `W039` e `W041`, ponto
  `(6177.25, 949.95)` (nó `node_index=64` do grafo do solver, `arms:
  [[38,1],[40,0]]` — `wall_idx` 38/40 só como diagnóstico, instável
  entre execuções).
- **Fiadas**: pares (0,2,4,6,8,10,12,14,16) em B/C; ímpares
  (1,3,5,7,9,11,13,15) em A.
- **Encontro**: tipo `L` (`L_CORNER`, dois braços).
- **Paredes envolvidas**: `W039` (o único lado que algum dia cobre o
  ponto) e `W041` (nunca cobre, em nenhum estado).
- **Node**: `node_index=64` do grafo de `wall_pairing.py`/
  `wall_stepper.py` (o mesmo nó em A e B/C — geometria idêntica, walls_
  to_create idêntico, só a decisão de papel do nó muda).
- **Geometria**: `block_covers_point` (a MESMA função do validador,
  chamada diretamente) prova que `W041` fica sistematicamente ~8cm
  curta do ponto do nó em TODAS as fiadas, em TODOS os estados (A, B,
  C) — nunca cobre. Só `W039` cobre, e só na fiada cuja família foi
  ancorada nesse nó pela coordenação de papel.
- **Blocos envolvidos**: em A, fiadas pares de `W039` têm `C09`/`B34`
  (papel `L_binding`) cobrindo o ponto; fiadas ímpares não têm NENHUM
  bloco a menos de ~120cm do ponto (buraco real de preenchimento, não
  só "falta uma peça específica"). Em B/C, o padrão inverte (ímpares
  cobertas, pares com o buraco).
- **Binding esperado vs produzido**: esperado - alguma peça de amarração
  cobrindo o ponto em TODA fiada; produzido - cobertura alternada por
  família (metade das fiadas cobertas, metade não), em AMBOS os
  estados A e B/C - o defeito em si não é novo, só a paridade afetada.
- **Regra que dispara o validator**: `JUNCTION_MISSING_BINDING`
  (`nuvem/benchmark/validators/validate_junctions.py:validate_node`,
  "alguma fiada em que NENHUMA parede do nó pôs peça no encontro").

## Primeira introdução

Isolado por commit, comparação DIRETA (nunca `git stash`) via `git
worktree` para cada um dos 3 commits do PR#9 aplicados sobre
`origin/main`:

| commit | `JUNCTION_MISSING_BINDING` (TP1) |
|---|---|
| `a2577797` (main, antes de qualquer ARM-ROLE) | 8 |
| `963aa9b` (`CR-BLOCK-ARM-ROLE-INVARIANCE`) | 8 (inalterado) |
| `d813f45` (`CR-BLOCK-ARM-ROLE-CONSISTENCY` — introduz `_coordinate_arm_role_nodes`) | **9** |
| `77bda14` (`CR-BLOCK-ARM-ROLE-PRISM-STAGGER`) | 9 (inalterado) |

**Primeiro commit/mecanismo**: `d813f45`, especificamente
`_coordinate_arm_role_nodes` decidindo qual família ancora o nó 64 (a
ponta distante de `W039`). Este commit já estava integrado nesta branch
ANTES de qualquer trabalho desta CR (`CR-BLOCK-ARM-ROLE-CANDIDATE-
SAFETY-CONTRACT`) — nenhum commit desta CR participa.

## Causa

`W041` nunca fisicamente alcança o ponto do nó (gap sistemático de
~8cm, presente em TODOS os estados testados — não introduzido por
nenhum commit ARM-ROLE). A cobertura deste encontro depende 100% de
`W039` ter uma peça de amarração real na sua ponta distante (nó 64) na
fiada em questão — decisão que `_coordinate_arm_role_nodes` faz por
família (par/ímpar), não por fiada individual. `W039` tem 17 fiadas
(9 pares, 8 ímpares) — qualquer coordenação de papel necessariamente
deixa UMA das duas famílias sem a peça nesse nó específico (o vão livre
da família não-ancorada simplesmente não fecha até a ponta, um limite
de busca de preenchimento pré-existente, não uma regra de amarração
nova). Antes de `d813f45` não havia coordenação nenhuma (o resultado
"por acaso" deixava a família ímpar sem peça); depois, a coordenação
determinística escolhe a família PAR para ancorar esse nó especifico -
inverte QUAL família sofre, não CRIA o sofrimento.

## Humano × Solver

Nó físico casado geometricamente (`match_walls`-equivalente por
proximidade, nunca por `id`): humano tem o MESMO nó em
`(6184.25, 949.95)` (offset 7cm, dentro da tolerância de reconstrução).

- **O humano possui binding nesse encontro?** Parcialmente - sim na
  maioria das fiadas (0-7, 9-11), mas **NÃO** nas fiadas 8 e 12
  (`JUNCTION_MISSING_BINDING` real no PRÓPRIO gabarito aprovado).
- **Qual parede ocupa o encontro por fiada?** Só `W039`, em TODAS as
  fiadas onde há alguma peça - `W041` nunca aparece, exatamente como no
  solver.
- **Qual peça faz a amarração?** Um MEIO-BLOCO (`B19`) repetido, quase
  sempre o MESMO em fiadas consecutivas - dispara `JUNCTION_NOT_
  ALTERNATING` no próprio gabarito humano (10 ocorrências medidas) e
  `JUNCTION_HALF_BLOCK_ADJACENT` (11 ocorrências) - o humano não trata
  este encontro como uma amarração B34/B54 alternada "de livro".
- **O solver novo reproduz ou diverge do humano?** Reproduz o padrão
  estrutural central (só `W039` cobre, nunca `W041`) mas diverge no
  detalhe (solver alterna B34/C09 por família; humano repete B19 sem
  alternar). Nenhum dos dois fecha 100% das fiadas.
- **Seria erro real na modulação aprovada?** O PRÓPRIO gabarito humano
  tem 2 fiadas sem binding neste encontro e falha `JUNCTION_NOT_
  ALTERNATING` nele - a régua "toda fiada deve alternar com peça de
  amarração real" já não se aplica de forma limpa a este encontro
  específico, nem no projeto aprovado.

## Classificação P1-P5

**P3 — BENCHMARK_ARTIFACT.**

Não é P1 (`PHYSICAL_REGRESSION`): nada foi perdido - o mesmo defeito
(uma família sem peça neste nó específico) já existia em `origin/main`,
só na paridade ímpar; `d813f45` apenas inverteu QUAL paridade sofre,
nunca criou um defeito novo. Não é P2 (`EXPECTED_RULE_CHANGE`): nenhum
dos dois estados (A ou B/C) é "fisicamente correto" neste encontro -
os dois têm o mesmo tipo de buraco, só em fiadas diferentes; não há uma
"solução nova correta" substituindo uma "antiga errada". Não é P5
(inconclusivo): a causa foi isolada por commit E por geometria, com
evidência direta e reproduzível.

O que É um artefato: o DELTA "8→9" tratado por `scoring.compare_runs`
como `REGRESSAO CRITICA`. Ele conta o mesmo mecanismo de defeito como
se fosse "uma unidade a mais de dano" quando na verdade é o mesmo
defeito relocado de paridade, e a contagem bruta muda de 8 para 9 só
porque este prédio tem uma fiada par a mais que ímpar (17 fiadas totais)
- um artefato de contagem por paridade desigual, não uma nova extensão
de defeito físico. Reforçado pela prova humano×solver: o próprio
gabarito aprovado já falha a regra de alternância "de livro" neste
encontro específico.

## Decisão sobre baseline

`baseline.json` do TP1 **NÃO regravado** (nem nesta auditoria, nem na
CR anterior). Por ser P3 (não P2), não se aplica sequer
`BASELINE_UPDATE_RECOMMENDED` no sentido de "a nova solução é a
correta, adote-a" - o achado é documentado como o artefato que é;
regravar o baseline exigiria decisão humana sobre COMO tratar este
encontro atípico (aceitar meio-bloco repetido como o humano faz? exigir
peça de amarração real nas 17 fiadas, o que nem o humano cumpre?) -
fora do escopo desta auditoria.

## Candidate Safety Contract

Sem alteração de comportamento em relação ao relatório anterior -
confirmado por reexecução completa pós-merge (ver TGD/TP1/Piloto
abaixo): SAFE REPAIR nunca toca este nó (não é uma aresta isolada do
grafo de coordenação relevante para nenhum candidato do TGD/TP1) e
produz B==C idêntico também para `JUNCTION_MISSING_BINDING`.

## TGD / TP1 / Piloto (reexecutado pós-merge, números NOVOS)

| projeto | aceitos/rejeitados | regressão global |
|---|---|---|
| TGD | 1 (`wall_idx=23`, `SAME_A`) / 7 | zero (`PRISM_CONTINUOUS_JOINT` 476→444, `PRISM_JOINT_STACK` 29→27; `COMPENSATOR_EXCESS_IN_RUN` reposicionado em W011, líquido zero) |
| TP1 | 0 / 3 | zero (B==C idêntico em todas as 13 categorias, incluindo `JUNCTION_MISSING_BINDING`=9 nos dois) |
| Piloto | — / — | zero (no-op, 0 arestas candidatas) |

Números idênticos aos medidos antes do merge da main - confirma que
sincronizar `origin/main` (mudança docs-only) não afetou o mecanismo.

## Testes focados

`tests/test_block_arm_role_invariance.py` + `tests/test_block_arm_role_
prism_stagger.py` + `tests/test_block_arm_role_candidate_safety_
contract.py`: **39 passaram** (287.80s), reexecutados do zero
pós-merge.

## Suíte completa

`tests/` completo reexecutado do zero pós-merge: **565 passaram / 1
falhou** (534.22s) - resultado NUMERICAMENTE IDÊNTICO ao medido antes
do merge (não reaproveitado, reexecutado). A única falha é a já
investigada e classificada P3 acima (`test_projeto_nao_regrediu_contra_
o_baseline[torre_easy_lo_r00_tp1]`).

## Determinismo

Confirmado por teste automatizado (T16, reexecutado nesta sessão dentro
da suíte completa) e pela reexecução B/C pós-merge produzindo números
byte-idênticos aos pré-merge.

## Performance

Suíte completa: 534s (~8min54s). Testes focados ARM: 288s. Sem
degradação perceptível em relação à medição anterior.

## Production diff (contra `origin/main`)

```
nuvem/core/engine/wall_stepper.py   | 811 ++++++++++++++++++++++++++-
nuvem/core/wall_modeling.py         |  89 ++-
```

Exatamente os dois arquivos esperados, nenhum outro arquivo de
PRODUÇÃO. Dois arquivos adicionais aparecem no diff completo mas são
NÃO-produção e PRÉ-EXISTENTES a esta CR (confirmado via `git log
origin/main..HEAD -- <arquivo>`, ambos introduzidos por commits do
PR#9 - `5327d61`/outros - muito antes de qualquer commit desta CR):
`docs/PROJECT_STATUS.md` (documentação) e `tests/test_script.py` (teste
- atualizado quando `_coordinate_arm_role_nodes` mudou o comportamento
de um teste antigo de colisão em L_CORNER).

## Baseline diff / Reference diff

```
git diff --stat origin/main HEAD -- '**/baseline.json' '**/reference.json'
```

**ZERO** em ambos - confirmado, nenhum arquivo de baseline/reference
tocado por esta branch em nenhum momento.

## Gates G1-G18

| gate | status |
|---|---|
| G1 branch sincronizada com origin/main atual | ✅ |
| G2 regra nova de propostas geométricas preservada integralmente | ✅ |
| G3 nenhum conflito de produção escondido | ✅ (conflito único foi documental, resolvido preservando os dois lados) |
| G4 main TP1 JUNCTION_MISSING_BINDING medido | ✅ (8) |
| G5 branch SAFE OFF medido | ✅ (9) |
| G6 branch SAFE ON medido | ✅ (9, idêntico a OFF) |
| G7 ocorrências novas identificadas geometricamente | ✅ (mesmo nó, paridade espelhada - não uma "9ª" isolada) |
| G8 primeiro commit/mecanismo identificado | ✅ (`d813f45`) |
| G9 comparação humano × solver feita | ✅ |
| G10 classificação P1-P5 justificada | ✅ (P3) |
| G11 baseline intacto | ✅ |
| G12 reference intacto | ✅ |
| G13 SAFE REPAIR sem regressão própria | ✅ |
| G14 TGD/TP1/Piloto reexecutados | ✅ (números idênticos aos pré-merge) |
| G15 determinismo passa | ✅ |
| G16 testes focados passam | ✅ (39/39) |
| G17 suíte completa executada | ✅ (565/566, mesma falha pré-existente e já classificada) |
| G18 production diff compreendido | ✅ |

## Veredito

**APROVADO PARA MERGE**

Branch sincronizada com `origin/main` por merge normal (sem rebase),
conflito documental resolvido preservando 100% do conteúdo dos dois
lados. `JUNCTION_MISSING_BINDING` 8→9 no TP1 investigado até a causa
raiz geométrica e classificado `P3 — BENCHMARK_ARTIFACT`: o mesmo
defeito pré-existente (uma família sem amarração real num encontro L
atípico onde até o gabarito humano falha a regra de alternância),
apenas espelhado de paridade por um commit já integrado antes desta CR
(`d813f45`, `CR-BLOCK-ARM-ROLE-CONSISTENCY`) - nenhuma alteração desta
CR participa. Nenhuma atualização de baseline necessária ou realizada.
Nenhuma regressão nova em TGD/TP1/Piloto. Suíte completa reexecutada do
zero: 565/566 (mesma falha pré-existente e já compreendida). Production
diff restrito aos dois arquivos esperados.

**Não mergeado. PR #12 continua DRAFT.** `PR #9`/`#11` intocados.
Arestas rejeitadas (7 no TGD, 3 no TP1) não investigadas nesta
auditoria (fora de escopo). NODE-FILL não iniciado. Monitoramento
automático não ativado.
