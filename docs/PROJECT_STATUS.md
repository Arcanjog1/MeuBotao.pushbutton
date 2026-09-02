# PROJECT STATUS

> Este documento é a **memória oficial do desenvolvimento** do projeto
> (Modulação Automática pyRevit). Ele registra de onde o projeto veio, o
> que já foi resolvido, onde estamos, o que está em andamento, o que
> falta, o que não deve ser reaberto e qual é o próximo passo.
>
> Ele **não** substitui `nuvem/REGRAS_MODULACAO_BLOCOS.md` — ver seção 11.

## 1. Resumo executivo

O motor de modelagem de paredes (`nuvem/core/engine`) passou por uma
sequência de CRs (Change Requests) para eliminar dependências de ordem de
entrada (assimetrias e não-determinismo) na formação das paredes a partir
de segmentos de CAD. O `CR-2F-E` (centerline), o `CR-2F-A` (simetria de
merge/pairing/deduplicação) e o `CR-2F-D` (determinismo do agrupamento e
recuperação da `W097`) já foram concluídos e **mergeados na `main`**: o
fingerprint das paredes foi de 3 distintos para 1 e a `W097` foi
recuperada.

O **primeiro teste visual no Revit** foi iniciado em 2026-09-01 e bateu
num **bloqueio de integração real** (`ArgumentsInconsistentException` /
`ShortCurveTolerance`) na extração do CAD — **corrigido e validado** (ver
seção 5, "CORREÇÃO REVIT — SHORT CURVES"). Durante esse teste também foi
diagnosticado (não corrigido — dívida de UX registrada na seção 6) que o
detector de espessuras da tela de configuração amostra só as primeiras
900 linhas cruas do Layer, o que pode subcontar/ocultar espessuras reais
na sugestão da UI sem limitar o solver de verdade.

O teste visual **integrado completo** (extração → paredes criadas →
inspeção visual das paredes no Revit) foi **adiado por decisão do
usuário**: a correção do `ShortCurveTolerance` está mesclada e validada,
mas a criação de paredes em si ainda não foi exercitada ponta-a-ponta no
Revit real. **PRÓXIMA FASE AUTORIZADA: MODULAÇÃO DOS BLOCOS** (seção 10)
— a geometria das paredes (CR-2F-A/E/D) está estável e determinística o
suficiente para o usuário autorizar o avanço, mesmo com o teste visual
integrado ainda pendente.

## 2. Estado atual da main

```
branch: main
HEAD:   f7055c7e71c02415ffffe36f1f041b11c559df92
```

Últimos commits em `main` (mais recente primeiro):

```
f7055c7  Merge branch 'claude/cr-2f-d-determinism-ewnru5': CR-2F-D DETERMINISM
55f7f8c  docs: corrige merge-base atual em PROJECT_STATUS.md
7771170  Merge remote-tracking branch 'origin/main' into claude/cr-2f-d-determinism-ewnru5
1857de4  docs: fecha o PENDENTE do PROJECT_STATUS com os numeros da bateria
d2e3604  test(benchmark): laboratorio 2K com a bateria e o censo do CR-2F-D
5f7bfc4  docs: PROJECT_STATUS com o estado do CR-2F-D
c81ff59  fix(wall-modeling): determinismo do merge e recuperacao da W097 (CR-2F-D)
d16965d  Merge branch 'claude/ci-check-fix'
bfa3155  ci: corrige check-project-status para branches novas (before=0)
b140503  Merge branch 'claude/project-status-tracking-qm3r56'
03afd3b  ci: alerta automatico quando o motor muda sem atualizar PROJECT_STATUS.md
351d607  docs: add project development status and roadmap
c21a429  Merge pull request #4: CR-2F-A MERGE_RELATION_ASYMMETRY (T2/MAX)
33bb516  fix(wall-modeling): make the merge/dedup relation symmetric (CR-2F-A)
902bc70  Merge pull request #3: CR-2F-E CENTERLINE_ARGUMENT_ASYMMETRY
9bca561  fix(wall-modeling): make wall centerline order invariant (CR-2F-E)
```

O merge do `CR-2F-D` (`f7055c7`) foi feito por **merge commit**, sem
squash, sem rebase, sem force push — mesma prática do `CR-2F-A`. Commit
funcional: `c81ff59` (determinismo do merge + `deduplicate_walls`).

**Branch mesclada:**

```
branch:                claude/cr-2f-d-determinism-ewnru5
SHA inicial (baseline original do CR-2F-D): c21a4297a6ff372358cbb81da5ca6a65f91a955b
merge-base usado no merge (main antes do CR-2F-D): d16965dba45b81c2a109bc24b23ab2fcb959db10
SHA do merge na main: f7055c7e71c02415ffffe36f1f041b11c559df92
```

## 3. Baseline funcional atual

Produção + seeds (permutações da ordem de entrada: seed 1, seed 2, seed 3,
seed 10, seed 42) — projeto de referência `torre_easy_lo_r00_tgd`:

| métrica | antes (CR-2F-A) | **`main` atual (CR-2F-D)** |
|---|---|---|
| **fingerprints distintos das paredes** | 3 | **1** |
| fingerprints distintos do merge | 6 | **1** |
| pares aceitos | 201 | 201 |
| paredes finais | 144 | **145** |
| cobertura do gabarito | 86/97 | **87/97** |
| eixos corretos (≤ 0,5 cm) | 96 | 96 |
| aberturas | 91/91 | 91/91 |
| paredes monitoradas | 7/7 | 7/7 |
| paredes espúrias | 4 | 4 |
| `W097` | ausente | **recuperada** |

Antes do CR-2F-D, as métricas eram estáveis nas 6 execuções, mas
produziam 3 conjuntos geométricos diferentes; agora a `main` é estável
**também em geometria** (um único fingerprint).

Fingerprint oficial do solver (`solver_decision_fingerprint`), **inalterado**
por todo o CR-2F-E, CR-2F-A e CR-2F-D (confirmado após o merge na `main`):

```
c74c9c1ae0e3f169f76e05fe53c01a858fce0af5b4e9d5f1b86fd71e92d2a316
```

## 4. Testes e invariantes aprovados

| suíte | antes (CR-2F-A) | **`main` atual (CR-2F-D)** |
|---|---|---|
| `tests/test_script.py` | 245 passed | **256 passed** (245 + 11 novos) |
| `tests/regression` | 113 passed | **113 passed** |

11 invariantes aprovados (`11/11 PASSED`), preservados pelo CR-2F-D **sem
nenhuma edição de teste**:

```
INV-PAIR-001
INV-PAIR-002
INV-PAIR-003

INV-CENTER-001
INV-CENTER-002
INV-CENTER-003
INV-CENTER-004

INV-MERGE-SYM-001
INV-MERGE-SYM-002
INV-MERGE-SYM-003

INV-DEDUP-SYM-001
```

Censo de assimetria aprovado (`nuvem/benchmark/diagnostics_2j/`):

| | antes da correção | depois da correção |
|---|---|---|
| `merge` — vereditos dependentes da direção | 393 | **0** / 281.162 pares próximos |
| `deduplicate_walls` — vereditos dependentes da direção | 1 | **0** / 1.670 candidatos |

11 invariantes novos do CR-2F-D (`nuvem/benchmark/diagnostics_2k/`), todos
sobre geometria **sintética** — nenhum id, coordenada, comprimento ou seed
do projeto real:

```
INV-DET-001   permutar a entrada não altera o conjunto final
INV-DET-002   inverter endpoints não altera o resultado
INV-DET-003   o representante de um grupo não depende da ordem
INV-DET-004   grupos transitivos independem da ordem
INV-DET-005   a orientação das paredes finais é canônica
INV-DET-006   a ordenação final é canônica
INV-DET-007   um único fingerprint em todas as permutações

INV-DEDUP-D-001  linha auxiliar longa não apaga parede válida
INV-DEDUP-D-002  a parede recuperada não vira duplicata
INV-DEDUP-D-003  duplicatas reais continuam sendo removidas
INV-DEDUP-D-004  o critério do trecho comum é simétrico
```

Censo de assimetria do CR-2F-D (`nuvem/benchmark/diagnostics_2k/`), sobre a
relação de duplicidade **completa** que ficou em produção:

| | resultado |
|---|---|
| `merge` — vereditos dependentes da direção | **0** / 281.162 pares |
| `deduplicate_walls` — relação completa | **0** / 1.646 candidatos |

> O número de candidatos cai de 1.670 para 1.646 porque o conjunto de linhas
> mescladas mudou (o merge agora é determinístico) — não é regressão.

## 5. Histórico de CRs

### CR-2F-E — CONCLUÍDO (contexto, anterior ao CR-2F-A)

- **Objetivo:** eliminar a dependência do sentido/ordem dos endpoints em
  `create_centerline` (`CENTERLINE_ARGUMENT_ASYMMETRY`).
- **Solução:** `create_centerline` reconstruído em referencial sem lado
  (bissetriz), face de referência escolhida por comprimento, ponta de
  saída em ordem canônica.
- **Commit:** `9bca561` — merge `902bc70` (PR #3).
- **Resultado:** `create_centerline(A,B) != (B,A)` caiu de 47/199 para
  0/199; fingerprint das paredes finais passou a ser idêntico nas 5
  seeds (para o centerline isoladamente).
- **Dívida registrada nesse CR:** perda da parede `W097`, formalmente
  fora do escopo do CR-2F-E (depois reatribuída ao CR-2F-D — ver 26.9.5
  de `REGRAS_MODULACAO_BLOCOS.md`).

### CR-2F-A — CONCLUÍDO

- **Objetivo:** tornar simétrica (`compat(A,B) == compat(B,A)`) a relação
  de compatibilidade geométrica usada para agrupar/fundir/remover
  paredes, nos quatro sítios de produção onde essa relação decide
  geometria. Estratégia aprovada: `T2`/`MAX` — `max(d(A,B), d(B,A)) <=
  tolerância`. Escopo explicitamente **não** incluía invariância total à
  ordem de entrada nem a recuperação da `W097`.
- **Causa:** `get_distance_between_parallel_lines` mede o ponto médio de
  um segmento contra a reta infinita do outro — não é simétrica. Como o
  primeiro argumento era apenas a posição na lista de entrada, o
  agrupamento passava a depender da ordem de entrada.
- **Solução:** centralização da propriedade em
  `_symmetric_within_distance_cached` e `symmetric_lines_within_distance`
  (`core/engine/geometry.py`), aplicada nos quatro sítios:
  `merge_collinear_fragments`, `_bridge_clusters_via_openings`,
  `_clusters_bridge_via_opening` (todos em `geometry.py`) e
  `deduplicate_walls` (`wall_pairing.py`).
- **Commits:**
  - `33bb5168a4d019d516f3a23556ea89c3bdc00ee0` — fix aprovado.
- **Merge:** `c21a4297a6ff372358cbb81da5ca6a65f91a955b` (PR #4), merge
  commit, sem squash/rebase/force push.
- **Resultados (produção + 5 seeds, merge incluído):**

  | | antes | depois |
  |---|---|---|
  | pares aceitos | 197–209 | 201 em todas |
  | paredes finais | 148–159 | 144 em todas |
  | cobertura do gabarito | 84–86 | 86 em todas |
  | eixos corretos | 94–96 | 96 em todas |
  | aberturas | 91/91 | 91/91 |
  | monitoradas | 5–7 | 7/7 em todas |
  | espúrias | 4–6 | 4 em todas |
  | `solver_decision_fingerprint` | `c74c9c1a...` | inalterado |

- **Invariantes:** `INV-MERGE-SYM-001`, `INV-MERGE-SYM-002`,
  `INV-MERGE-SYM-003`, `INV-DEDUP-SYM-001` (todos em
  `tests/test_script.py`, todos reprovam no baseline pré-CR pelo motivo
  geométrico correto).
- **Decisões estabilizadas (ver seção 8):**
  - simetria de pairing, merge e deduplicação está resolvida;
  - a política de retenção "mantém a mais longa" do `deduplicate_walls`
    **não foi alterada** — só o predicado de duplicidade;
  - a `W097` **não** pertence ao CR-2F-A (3 provas independentes, ver
    `REGRAS_MODULACAO_BLOCOS.md` §26.9.5) — é dívida exclusiva do
    CR-2F-D.

### CR-2F-D — CONCLUÍDO E MERGEADO NA MAIN

- **Branch:** `claude/cr-2f-d-determinism-ewnru5` (mesclada e preservada)
- **Commits:**
  ```
  c81ff59  fix(wall-modeling): determinismo do merge e recuperacao da W097 (CR-2F-D)
  5f7bfc4  docs: PROJECT_STATUS com o estado do CR-2F-D
  d2e3604  test(benchmark): laboratorio 2K com a bateria e o censo do CR-2F-D
  1857de4  docs: fecha o PENDENTE do PROJECT_STATUS com os numeros da bateria
  7771170  Merge remote-tracking branch 'origin/main' into claude/cr-2f-d-determinism-ewnru5
  55f7f8c  docs: corrige merge-base atual em PROJECT_STATUS.md
  ```
- **Merge na `main`:** `f7055c7` — merge commit, sem squash/rebase/force push
- **Objetivo (atingido):** eliminar o não-determinismo restante,
  estabilizar o fingerprint das paredes, corrigir estruturalmente a perda
  da `W097` sem hardcode e preservar tudo que já estava aprovado.

**Diagnóstico — a primeira divergência estava na passada 1 do merge**

| camada, nas 6 ordens | fingerprints distintos |
|---|---|
| linhas mescladas (`merge_collinear_fragments`) | **6** |
| paredes finais | **3** |
| paredes finais, **congelando** o conjunto mesclado e permutando-o | **1** |

A terceira linha é a prova causal: de `find_wall_pairs` para a frente o
pipeline **já estava invariante** desde o CR-2F-B/C/E. A causa é o
agrupamento **estrela** sobre uma relação **não transitiva** (com 2 mm,
`A~B` e `B~C` não implicam `A~C` — caso real: fragmentos em
`x = -563,29 / -563,49 / -563,69`), com a base saindo de
`remaining.pop(0)`, isto é, da **posição na lista**.

**Diagnóstico — a `W097`**

A parede boa de 707,01 cm era removida como duplicata do eixo espúrio de
4.394,25 cm (par `(474, 2306)`). O predicado do CR-2F-A amostra a distância
num **único ponto** — o ponto médio de cada eixo contra a reta infinita do
outro — e os dois eixos **se cruzam** perto desse ponto:

| medição | valor | veredito |
|---|---|---|
| distância pelos pontos médios | **0,3633 cm** | "duplicata" |
| separação **máxima no trecho compartilhado** (707 cm) | **3,7952 cm** | não é duplicata |

Censo das 57 remoções do comportamento anterior: **1** acima da tolerância
de 2 cm (a da `W097`); pior remoção legítima **1,5306 cm**. A tolerância já
existente separa as classes com folga — nenhum valor novo calibrado.

> **Atribuição corrigida.** A causa **não** era a política "mantém a mais
> longa" (ela acerta nas 56 remoções legítimas e não foi alterada); era a
> amostragem por ponto médio do predicado que declarava o par duplicata.
> Ver `REGRAS_MODULACAO_BLOCOS.md` §26.10.5, que substitui §26.8.7.8 e
> §26.8.8.4.

**Correção implementada**

- `nuvem/core/engine/geometry.py`
  - `merge_collinear_fragments` — a base da passada 1 passa a ser escolhida
    pela **geometria** (fragmento mais longo primeiro, desempate por
    `_line_span_key`), não pela posição na lista; varredura por índice
    (marcador `taken`) no lugar da reconstrução da lista `rest`.
  - `_merge_collinear_cluster` — membros em ordem canônica antes das contas
    (soma de ponto flutuante não é associativa) e **sentido** da direção de
    referência canonizado.
  - `_pair_symmetric_axis_gap_ft_cached` / `symmetric_axis_gap_ft` — novos:
    separação **máxima** entre dois eixos ao longo do trecho compartilhado,
    no referencial sem lado da bissetriz.
- `nuvem/core/engine/wall_pairing.py`
  - `deduplicate_walls` — o critério novo entra em **conjunção** com o do
    CR-2F-A (a relação só fica mais restritiva); desempate do representante
    por `_line_span_key`.

`create_centerline`, `find_wall_pairs` e `tolerances.py` **não foram
tocados**. Nenhum hardcode de id, coordenada, comprimento ou seed.

**Resultado (produção + seeds 1, 2, 3, 10 e 42)**

```
merge fingerprints distintos : 6 → 1
wall  fingerprints distintos : 3 → 1     ← gate do CR
201 pares aceitos | 145 paredes | 87/97 cobertura | 96 eixos
91/91 aberturas   | 7/7 monitoradas | 4 espúrias | W097 recuperada
```

Ausentes: as mesmas 10 de antes, **sem a `W097`**, sem perda nem ganho novo.

**Testes:** `tests/test_script.py` 256 passed (245 antigos + 11 novos);
`tests/regression` 113 passed; 11 invariantes anteriores preservados sem
edição; `solver_decision_fingerprint` inalterado.

**Performance:** passada 1 do merge de 9,15 s para **8,67 s (−5,2 %)** — a
ordenação canônica sozinha custaria 9,64 s (+5,4 %), e a varredura `taken`
(partição idêntica, medida nas 6 ordens) paga esse custo.

**Divergência gabarito × CAD registrada na `W097`**

```
CAD:            faces em y = 808,049 e 822,050  (14,000 cm)
eixo calculado: y = 815,049                      (centrado — correto)
reference.json: y = 817,048                      (faces 810,048 / 824,048)
```

Não existe segmento do CAD em 810,048 nem 824,048, e o eixo do gabarito
dista 5,001/8,999 cm das faces quando deveria ser 7/7. **É proibido mover a
parede para satisfazer o gabarito** (§26.10.6 das REGRAS). Consequência
aceita: a `W097` conta como coberta, mas **não entra no `eixo_ok`** (≤ 0,5 cm).
Diagnóstico visual aprovado pelo usuário em
`nuvem/benchmark/diagnostics_2d/w097_geometry.png` e `_zoom.png`.

**MESCLADO NA MAIN em `f7055c7`. PRÓXIMO PASSO: TESTE VISUAL NO REVIT.**

### CORREÇÃO REVIT — SHORT CURVES (`ShortCurveTolerance`) — CONCLUÍDA E MERGEADA NA MAIN

- **Branch:** `fix/revit-short-cad-curves` (mesclada e preservada)
- **Contexto:** primeiro teste visual real no Revit (2026-09-01), fora do
  pipeline headless via MCP.
- **Bloqueio encontrado** antes da criação de qualquer parede, na etapa
  "Extraindo linhas do CAD...", no CAD real `T01 LIMPA` (Revit 2026):

  ```
  Autodesk.Revit.Exceptions.ArgumentsInconsistentException:
  Curve length is too small for Revit's tolerance
  (as identified by Application.ShortCurveTolerance).
  Parameter name: endpoints
  ```

  Stack: `extract_lines_by_layer` (`nuvem/core/wall_modeling.py`), na
  chamada `DB.Line.CreateBound(p0, p1)` ao explodir uma `PolyLine` do CAD
  em segmentos.

- **Causa confirmada:** o CAD `T01 LIMPA` contém milhares de segmentos
  (vértices de `PolyLine` quase duplicados, sobretudo no layer `P-PIPE`)
  com comprimento **abaixo de `Application.ShortCurveTolerance`** (a
  tolerância oficial do Revit, medida diretamente via MCP:
  `0,00256026455729 pé`). O filtro antigo do script descartava só
  segmentos com comprimento `< 1e-6` pé — muito menor que a tolerância
  real do Revit — então esses segmentos passavam pelo filtro e derrubavam
  `Line.CreateBound`.
- **Diagnóstico comparativo Revit 2026 × 2027** (antes de corrigir):
  `Application.ShortCurveTolerance` é **idêntico** nas duas versões
  (`0,00256026455729` pé, builds 26.3.0.37 e 27.2.0.39); o teste de 2027
  que "funcionou" usava um CAD de origem **diferente** (`TORRE`, 1.196
  segmentos, sem a camada `P-PIPE`), não o `T01 LIMPA`. **Não há evidência
  de diferença de comportamento entre os motores 2026 e 2027** — o
  bloqueio é dado real do CAD, não regressão de versão do Revit.
- **Correção aplicada** (`nuvem/core/wall_modeling.py`): `extract_lines_by_layer`
  agora lê `Application.ShortCurveTolerance` diretamente (via
  `doc.Application`, cacheado em `_get_short_curve_tolerance()`) e usa a
  decisão pura `_segment_too_short_for_revit(distance, tolerance)` para
  IGNORAR (sem enviar a `Line.CreateBound`) qualquer segmento com
  `distance <= ShortCurveTolerance`, nos ramos `Line` e `PolyLine`.
  Segmentos normais continuam extraídos exatamente como antes. Um resumo
  (total analisado, ignorados, menor comprimento visto, layers afetados)
  é logado uma única vez após a extração. Nenhuma tolerância hardcoded,
  nenhum `except` genérico, nenhum endpoint alterado.
- **Validação real no Revit 2026 + CAD `T01 LIMPA`** (via MCP, chamando a
  função de produção, não uma reimplementação):
  - total examinado: **49.127** segmentos (todos os layers);
  - válidos: **40.028**; ignorados por `ShortCurveTolerance`: **9.099**;
  - menor comprimento visto: `1,3384461397e-06` pé;
  - layers afetados pelo descarte: `A-DETL-HDLN`, `M-EQPM`, `P-PIPE`,
    `P-PIPE-CNTR`, `Sanitário`;
  - **layer `Arquitetura` (o layer de paredes usado no teste): 0 linhas
    perdidas** — as 9.258 linhas válidas desse layer chegam intactas;
  - a extração terminou **sem exceção**, o script avançou até a tela de
    configuração (Layer/espessuras/Nível/altura).
- **Achado durante o mesmo teste (não é regressão desta correção — ver
  subseção seguinte):** o detector de espessuras da tela mostrou "14 cm →
  7 pares", número aparentemente baixo demais.
- **Não tocados:** `create_centerline`, `find_wall_pairs`,
  `core/engine/{geometry,wall_pairing,tolerances}.py`. CR-2F-D permanece
  encerrado e não foi reaberto.
- **Testes:** 4 testes de regressão novos em `tests/test_script.py`
  (decisão pura no limite/abaixo/acima da tolerância; `extract_lines_by_layer`
  com `Line` e `PolyLine` degeneradas, confirmando que só o segmento
  degenerado é descartado e o processo não cai); `tests/revit_stubs.py`
  ganhou um `ShortCurveTolerance` real (1/32" em pés) no stub de
  `Application`.
- **Merge:** merge commit na `main`, sem squash/rebase/force push (SHAs no
  histórico da seção 13).

#### Diagnóstico anexo — detector de espessuras da UI ("7 pares")

Investigado **antes de qualquer correção**, a pedido do usuário, para não
confundir com regressão do `ShortCurveTolerance` nem do CR-2F-D:

- Função: `scan_candidate_thicknesses_cm` (`core/engine/wall_pairing.py`),
  chamada por `_SetupForm._scan_layer` com
  `lines[:SETUP_THICKNESS_SCAN_MAX_LINES]` (`SETUP_THICKNESS_SCAN_MAX_LINES
  = 900`) — **apenas as primeiras 900 linhas cruas** (sem religamento de
  fragmentos colineares) do layer, de um total de 9.258 no layer
  `Arquitetura` do CAD `T01 LIMPA`.
- Reproduzido exatamente via MCP: `raw[:900]` → `14 cm → 7 par(es)`,
  batendo com o que a tela mostrou.
- **O solver real (`find_wall_pairs`) NÃO usa essa amostra** — ele recebe
  `lines_to_process = merge_collinear_fragments(...)`, calculado sobre as
  **9.258 linhas inteiras**, sem nenhum teto de 900. Medido via MCP,
  restringindo o alvo a 14 cm: **199 paredes formadas** pelo solver real
  (contra as "7" mostradas na tela).
- `ShortCurveTolerance` não influencia esse número: o layer `Arquitetura`
  perdeu 0 linhas para a correção acima.
- Outras espessuras "estranhas" mostradas na tela (6,5 cm, 9 cm — faces de
  ~4 cm de comprimento) são ruído geométrico do CAD (jambas, mobiliário,
  cotas), não paredes; 14 cm e 19 cm (faces de 0,55 m a 6,4 m) são
  plausivelmente paredes reais.
- **Conclusão oficial (aceita pelo usuário):** "7 pares" é **apenas
  amostragem da tela de configuração** e **não limita o solver real**.
  **NÃO corrigido agora** — decisão explícita do usuário. Registrado como
  dívida de UX (seção 6).

## 6. Dívidas técnicas conhecidas

- ~~**Não-determinismo residual do agrupamento**~~ — **RESOLVIDO** pelo
  CR-2F-D (seção 5): 6 → 1 no merge, 3 → 1 nas paredes.
- ~~**Perda da `W097`**~~ — **RESOLVIDA** pelo CR-2F-D (seção 5).
- ~~**Bloqueio `ShortCurveTolerance` na extração do CAD**~~ —
  **RESOLVIDO** pela correção "REVIT — SHORT CURVES" (seção 5).
- **Pareamento `(474, 2306)`** — uma face de 155,61 cm pareada com uma
  linha auxiliar de 4.394,45 cm inclinada 1,1125 grau, que gera o **eixo
  espúrio de 43,9 m**. Ele **continua no resultado**, como uma das 4
  espúrias: o CR-2F-D impediu que ele *apagasse* uma parede válida, não que
  ele *nascesse*. Não é merge, não é eixo e não é deduplicação — é
  **pareamento**. Continua **sem CR atribuído**.
- **Deslocamento de ~2 cm do `reference.json` na `W097`** — o gabarito
  coloca a parede 2 cm acima das faces que o CAD desenha (seção 5). É
  problema do **gabarito**, não do solver; convém verificar se se repete em
  outras paredes antes de usar `eixo_ok` como métrica fina.
- **Detector de espessuras da tela de configuração amostra só 900 linhas
  cruas (`SETUP_THICKNESS_SCAN_MAX_LINES`), sem religar fragmentos
  colineares** — diagnosticado em 2026-09-01 (subseção acima). Não limita
  o solver real (`find_wall_pairs` roda sobre a lista inteira, religada),
  mas pode: (a) subcontar a "confiança" mostrada ao lado de uma espessura
  real (ex.: "7 pares" quando existem 199 paredes de verdade); (b), em
  CADs mais extremos que este, **ocultar completamente** uma espessura
  real da lista de sugestão se ela só aparecer além do índice 900 na
  ordem de travessia do CAD (que não é espacial). **DÍVIDA DE UX — não
  corrigida, por decisão explícita do usuário** (não mexer no detector
  agora). Quando for endereçada: religar fragmentos antes de amostrar
  e/ou aumentar ou remover o teto, sem alterar `find_wall_pairs`.

## 7. Paredes ausentes conhecidas

Em relação ao gabarito de referência (`torre_easy_lo_r00_tgd`), continuam
ausentes **10** paredes (eram 11 — a `W097` foi recuperada pelo CR-2F-D):

```
W004, W005, W006, W007, W025, W026, W046, W047, W084, W085
```

Essas 10 já estavam ausentes antes do CR-2F-E/CR-2F-A e **não fazem parte
do escopo declarado** de nenhum CR até agora. O CR-2F-D não as perseguiu e
nenhuma voltou por acaso.

A linha auxiliar de aproximadamente **43,9 m** (segmento cru do CAD, par
`(474, 2306)`) continua existindo e continua gerando um eixo espúrio — ver
seção 6.

## 8. Não reabrir sem evidência de regressão

As áreas abaixo foram **resolvidas e validadas** pelo CR-2F-A (com o
CR-2F-E como base) e não devem ser alteradas de novo apenas para
refatorar ou "melhorar". Qualquer mudança nelas exige evidência objetiva
de regressão (um teste que falha, um caso reproduzível de assimetria ou
não-determinismo) — não impressão subjetiva de que o código "poderia ser
mais limpo".

**CR-2F-A — já resolvido:**
- simetria de pairing;
- simetria de merge;
- simetria de deduplicação;
- orientação/inversão dos endpoints, coberta pelos invariantes aprovados
  (`INV-CENTER-001` a `004`, `INV-MERGE-SYM-001` a `003`,
  `INV-DEDUP-SYM-001`).

**CR-2F-D — já resolvido:**
- ordem de agrupamento da passada 1 do `merge_collinear_fragments`
  (base canônica por geometria);
- ordem dos membros e sentido da direção de referência em
  `_merge_collinear_cluster`;
- medição da relação de duplicidade ao longo do trecho compartilhado
  (`symmetric_axis_gap_ft`), em conjunção com o predicado do CR-2F-A;
- desempate do representante em `deduplicate_walls`.

A política **"mantém a mais longa do grupo"** foi medida e está **correta**
(acerta nas 56 remoções legítimas) — **não deve ser alterada** sem evidência
objetiva de regressão. Coberto por `INV-DET-001` a `007` e `INV-DEDUP-D-001`
a `004`.

**REVIT — SHORT CURVES — já resolvido:**
- descarte de segmentos de CAD `<= Application.ShortCurveTolerance` antes
  de `Line.CreateBound`, em `extract_lines_by_layer`.

**Detector de espessuras da UI (`scan_candidate_thicknesses_cm` /
`SETUP_THICKNESS_SCAN_MAX_LINES`) — diagnosticado, EXPLICITAMENTE NÃO
corrigido** por decisão do usuário (2026-09-01). Não confundir uma
contagem baixa na tela com um limite do solver real — ver seção 5.

**Evitar especialmente mudanças sem necessidade em:**
```
create_centerline
find_wall_pairs
tolerances.py
```

Qualquer PR que toque esses arquivos fora do escopo de um CR ativo deve
justificar explicitamente por quê, e rodar a suíte completa de
invariantes antes de propor merge.

## 9. Próximas etapas

1. ~~Concluir o **CR-2F-D**~~ — **concluído, validado e MESCLADO NA MAIN**
   (`f7055c7`, seção 5).
2. ~~Validar o baseline e os 11 invariantes sem regressão~~ — **feito**
   (seções 3 e 4): 256 + 113 verdes, 11 invariantes anteriores preservados,
   11 novos, fingerprint do solver inalterado.
3. ~~**TESTE VISUAL NO REVIT** — bloqueio de extração do CAD
   (`ShortCurveTolerance`)~~ — **corrigido e mesclado na main** (seção 5).
   O detector de espessuras da UI foi diagnosticado (não limita o solver)
   e a dívida de amostragem foi registrada (seção 6).
4. **Teste visual INTEGRADO completo** (extração → criação de paredes →
   inspeção visual no Revit) — **ADIADO por decisão do usuário**. Ainda
   não foi exercitado ponta-a-ponta no Revit real; retomar quando o
   usuário priorizar.
5. **PRÓXIMA FASE AUTORIZADA (2026-09-01): MODULAÇÃO DOS BLOCOS** — ver
   roadmap na seção 10. Autorizada mesmo com o item 4 pendente.
6. **`CR-BLOCK-01` (prisma / fiadas / amarração vertical)** —
   **CONCLUÍDO / APROVADO POR CROSS-AUDIT**. Implementado na branch
   `claude/block-01-prisma-fiadas-rik42t` (CONTA 1), auditado
   independentemente na `claude/block-audit-baseline-350nav` (CONTA 2) e
   cruzado na `claude/block-01-cross-audit` — veredito **APROVADO COM
   CORREÇÃO DE TESTE**. Finalizado na `claude/block-01-finalize`. Ver
   seção 5 para o registro completo.

## 10. Modulação dos blocos — roadmap futuro

Estes itens são o **próximo trabalho autorizado** (2026-09-01). A
geometria das paredes (CR-2F-A/E/D) está estável e determinística; o
teste visual integrado completo continua pendente (seção 9, item 4), mas
não bloqueia mais o início desta fase, por decisão do usuário.

- **PRISMA / ESCOLHA DE LAYOUT SAME-BAND: CORRIGIDO** — `CR-BLOCK-01`
  concluído e aprovado por cross-audit. Coincidência de junta proibida
  entre fiadas da MESMA banda de abertura: **236 → 0** nos 3 projetos de
  benchmark, confirmado de forma independente pela CONTA 2
  (`alignment_conflicts_total = 0`);
  **ALINHAMENTO CROSS-BAND: DÍVIDA PENDENTE** — o resíduo (33 no
  recálculo da CONTA 1; a CONTA 2 mede a mesma família de problema com
  metodologia própria, não é contradição) é **entre bandas** de abertura
  e exige `wall_modeling.py` (fora do escopo do `CR-BLOCK-01`) — ver
  `REGRAS_MODULACAO_BLOCOS.md` 27.7. Próximo CR recomendado:
  `CR-BLOCK-DETERMINISM`;
- impedir compensadores de 9 cm repetidos;
- impedir pastilhas repetidas;
- controlar uso de meio bloco de 19 cm;
- evitar meio bloco longe de aberturas e finais sem amarração;
- corrigir amarrações em L;
- corrigir amarrações em T;
- corrigir cruzamentos +;
- manter blocos acompanhando deslocamentos das paredes;
- respeitar portas e janelas;
- impedir blocos dentro de aberturas;
- vergas;
- contravergas;
- canaletas;
- blocos cortados;
- paredes acima e abaixo de aberturas;
- benchmark contra projetos corretos de referência;
- garantir que todas as paredes válidas sejam efetivamente moduladas.

As regras técnicas e funcionais de amarração e modulação (o "como", não o
"quando") já estão sendo registradas continuamente em
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, conforme o CLAUDE.md do projeto exige.

## 11. Arquivos de referência

- `nuvem/REGRAS_MODULACAO_BLOCOS.md` — **regras técnicas e funcionais**
  da modulação de blocos e da amarração (o "como" do domínio). Este
  documento (`docs/PROJECT_STATUS.md`) **não substitui** aquele arquivo
  e não deve duplicá-lo: aqui fica o estado do desenvolvimento,
  histórico de CRs, pendências e roadmap; lá ficam as regras técnicas
  detalhadas, com rótulo de confiança (REGRA OBRIGATORIA / PREFERENCIAL
  / EXCECAO PERMITIDA / PADRAO OBSERVADO AINDA NAO CONFIRMADO /
  CONFLITO) e evidência de medição.
- `nuvem/benchmark/diagnostics_2k/` — verificação reproduzível do
  CR-2F-D (`run_a_census.py` — assimetria e censo do discriminador;
  `run_b_downstream.py` — 3 variantes da passada 1 × produção + 5 seeds,
  identidade da partição e runtime).
- `nuvem/benchmark/diagnostics_2d/render_w097.py` — diagnóstico visual da
  `W097` (gera `w097_geometry.png` e `w097_geometry_zoom.png` a partir da
  geometria real carregada pelo solver).
- `nuvem/benchmark/diagnostics_2j/` — verificação reproduzível do
  CR-2F-A (`run_a_census.py`, `run_b_downstream.py`).
- `nuvem/benchmark/diagnostics_2i/` — verificação reproduzível do
  CR-2F-E (`run_g_postimpl.py`).
- `nuvem/benchmark/RELATORIO_ETAPA_2F.md`,
  `nuvem/benchmark/PLANO_ETAPA_2G.md`,
  `nuvem/benchmark/PLANO_ETAPA_2I_CR_2F_E.md` — histórico de diagnóstico
  e planejamento que antecedeu o CR-2F-E e o CR-2F-A.
- `tests/test_script.py`, `tests/regression/` — suíte de testes e
  invariantes.
- `.github/workflows/check-project-status.yml` — lembrete automático
  (GitHub Actions): falha o check, sem bloquear o merge, quando um push
  ou PR altera `nuvem/core/engine/**` sem tocar este arquivo no mesmo
  diff. Não substitui a atualização manual — só reduz a chance de
  esquecimento.

## 12. Regra permanente de atualização

**Ao concluir qualquer CR, este documento deve ser atualizado antes de
encerrar o trabalho.** Não é opcional e não deve ficar apenas registrado
em commits ou em conversa.

Há um lembrete automático (`.github/workflows/check-project-status.yml`)
que sinaliza no GitHub quando `nuvem/core/engine/**` muda sem que este
arquivo seja atualizado no mesmo push/PR. Ele **não substitui** este
processo manual: é só um alerta (não bloqueia push nem merge direto na
`main`), então a responsabilidade de atualizar continua sendo do agente
ou do usuário que fecha o CR.

Toda atualização futura deve registrar, no histórico abaixo (seção 13),
no mínimo:

```
data
CR
branch
SHA inicial
SHA final
status
o que foi alterado
testes
invariantes
benchmarks
novas dívidas
itens resolvidos
itens ainda pendentes
próximo passo recomendado
```

Regras do processo:
- **Nunca apagar o histórico anterior.** Atualizar o estado atual
  (seções 1 a 10) para refletir a realidade, mas manter os registros
  históricos resumidos dos CRs concluídos (seção 5) e o log de
  atualizações (seção 13).
- Se uma nova orientação contradiz uma anterior, registrar o conflito e
  deixar explícito qual delas vale agora (a orientação mais recente do
  usuário tem prioridade) — mesma regra usada em
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`.

### Regra para agentes (Claude, Codex ou qualquer outro)

Antes de iniciar qualquer alteração relevante neste repositório:

1. leia `docs/PROJECT_STATUS.md` (este arquivo);
2. leia `nuvem/REGRAS_MODULACAO_BLOCOS.md` quando a tarefa envolver
   modulação de blocos ou amarração;
3. confirme a branch e o SHA atuais (`git status`, `git log -1`);
4. identifique o CR em andamento (seção 5);
5. verifique a seção "Não reabrir sem evidência de regressão" (seção 8);
6. não refaça trabalho já aprovado sem evidência objetiva de regressão
   (um teste falhando ou um caso reproduzível — não impressão
   subjetiva).

## 13. Histórico de atualizações deste documento

### 2026-09-02 — `CR-BLOCK-01` CONCLUÍDO / APROVADO POR CROSS-AUDIT

```
data:          2026-09-02
CR:            CR-BLOCK-01 (finalização — conclui a investigação de duas
               contas em paralelo)
status:        CONCLUÍDO / APROVADO POR CROSS-AUDIT

branches:
  implementação (CONTA 1):  claude/block-01-prisma-fiadas-rik42t
    SHA aprovado:            3e6d937116466198c79d51b85928788766657a41
  auditoria independente (CONTA 2): claude/block-audit-baseline-350nav
  cross-audit (CONTA 2, fase 2):    claude/block-01-cross-audit
    commit:                  6c91c93450fa5f3074d45c29cc447d461db75e55
  finalização:               claude/block-01-finalize

veredito do cross-audit: APROVADO COM CORREÇÃO DE TESTE. A auditoria
  independente (metodologia própria, sem ler a branch da CONTA 1) e o
  cross-audit (mesma biblioteca da CONTA 2, rodada duas vezes — MAIN pura
  via worktree temporário, e CR-BLOCK-01) confirmam, sem aceitar nenhum
  número da CONTA 1 como verdade:
    - cobertura 246/275 paredes com blocos — INALTERADA;
    - L/T/X (intersection_failures=200) — INALTERADO;
    - aberturas (door_void_violations=638) — INALTERADO;
    - alignment_conflicts: 0 (confirmado independentemente);
    - prisma (suspect_continuous_vertical_joint, metodologia própria da
      CONTA 2): 2936 → 2539 (-13,52%) — melhora confirmada por vias
      independentes, com classificação diferente da CONTA 1 (não é
      contradição, é outra régua sobre o mesmo fenômeno);
    - colisões: melhoram como efeito colateral;
    - compensadores: melhoram parcialmente como efeito colateral, NÃO
      considerados resolvidos;
    - non_modular +3 (3333→3336): investigado evento por evento,
      classificado NEUTRO — não reduz cobertura;
    - determinismo GLOBAL: 8 execuções, 8 fingerprints distintos —
      NÃO-DETERMINÍSTICO antes e depois, classificado NEUTRO (o CR não
      piora nem resolve; a causa é anterior ao preenchimento, no wall
      graph — vira CR próprio, `CR-BLOCK-DETERMINISM`);
    - teste `test_pipeline_lanca_blocos_e_ajusta_na_mesma_passada`:
      classificado TESTE DESATUALIZADO (não regressão) — prova
      independente de que `shift` é uma solução MENOS invasiva que
      `trim` (mantém o comprimento do eixo; `trim` reduzia), respeita a
      ordem de prioridade já documentada, não introduz colisão nem bloco
      em abertura, não piora modulação.

correção aplicada nesta branch: ÚNICA alteração de código — a asserção
  stale de tests/test_script.py::
  test_pipeline_lanca_blocos_e_ajusta_na_mesma_passada trocada de
  `plan["tier"] == "trim"` para `plan["tier"] == "shift"` (exigência
  explícita do comportamento correto, sem relaxar para
  `in ("trim","shift")`), com docstring atualizada explicando a prova.
  Nenhuma linha de produção tocada nesta etapa.

testes (branch de finalização, depois da correção):
  tests/test_block_bonding.py   32 passed
  tests/test_script.py         260 passed
  tests/regression             113 passed
  nuvem/tests                   18 passed
  TOTAL                        423 passed, 0 failed

benchmark reproduzido nesta etapa (Conta 1 + Conta 2, sem alterar
  metodologia): alignment_conflicts=0, cobertura 246/275, L/T/X e
  aberturas inalterados, colisões 1048 (mesmo valor da cross-audit),
  determinismo global continua conhecido como não-determinístico e não
  piorou — todos os números batem exatamente com o cross-audit já
  aprovado.

produção alterada nesta etapa: NENHUMA (só teste + documentação).
produção alterada pelo CR-BLOCK-01 como um todo (herdada da CONTA 1):
  SOMENTE nuvem/core/engine/wall_stepper.py.
produção protegida (confirmada intacta): geometry.py, wall_pairing.py,
  tolerances.py, modulation_math.py, continuous_modulation.py,
  wall_modeling.py.

dívidas oficiais que ficam abertas:
  - determinismo global (wall graph) — CR-BLOCK-DETERMINISM;
  - alinhamento cross-band (REGRAS_MODULACAO_BLOCOS.md 27.7);
  - C09/C04 (compensadores/pastilhas repetidos) — não resolvido, só
    melhorou como efeito colateral;
  - degradação de X;
  - exclusão preventiva de bloco em vão de porta (door exclusion);
  - reparo de abertura (opening repair) — non_modular +3.

próximo passo: CR-BLOCK-DETERMINISM. NÃO iniciado nesta sessão — parado
  por decisão explícita, aguardando autorização do usuário.
```

### 2026-09-01 — `CR-BLOCK-01` (prisma, fiadas e amarração vertical)

```
data:          2026-09-01
CR:            CR-BLOCK-01 (CONTA 1 de um par de sessões paralelas)
branch:        claude/block-01-prisma-fiadas-rik42t
SHA inicial:   9f3bab41b35f0e2a5f9782583ead8e1ee7755f49 (main)
SHA final:     995e884 (docs) — a correção de PRODUÇÃO é bff84e5
               (nuvem/core/engine/wall_stepper.py); c71e06c traz o
               benchmark e 01b7361 a suíte nova de invariantes
status:        IMPLEMENTADO — NÃO MESCLADO. Aguardando revisão e auditoria
               cruzada com a CONTA 2.

objetivo:      eliminar juntas verticais coincidentes entre fiadas
               consecutivas (quebra de prisma), escolhendo a modulação da
               fiada N+1 a partir da geometria REAL da fiada N — nunca por
               um deslocamento fixo nem por regra de caso particular.

baseline:      benchmark HEADLESS reprodutível criado nesta branch
               (nuvem/benchmark/diagnostics_block_prisma/), rodando o
               SOLVER REAL sobre os 3 projetos de nuvem/benchmark/projects:
               275 paredes, 17 fiadas, 22.341 juntas internas.
               FORBIDDEN_JOINT_ALIGNMENT=418 (236 dentro da mesma banda de
               abertura, 182 entre bandas), DOCUMENTED_EXCEPTION=638,
               UNCLASSIFIED_RULE_CONFLICT=1518, NO_ALIGNMENT=18262,
               alignment_conflicts=64, CONTINUOUS_VERTICAL_JOINT=169.

causa-raiz:    PROVADA por tracing + ablação, não por dedução (ver
               diagnostics_block_prisma/trace_segment.py). NÃO era "as
               fiadas são resolvidas independentemente" nem "as juntas
               anteriores são ignoradas" — as juntas da fiada A CHEGAM ao
               solver e SÃO usadas. Era a ENUMERAÇÃO de candidatos:
               _pier_layout_avoiding_joints só variava o PRIMEIRO bloco e
               deixava o mesmo guloso (que nunca volta atrás) preencher o
               resto. Num trecho de 99cm fechado dos dois lados, os SETE
               candidatos gerados eram literalmente IDÊNTICOS entre si,
               com as duas juntas coincidindo — embora a MESMA composição
               com o B19 na outra ponta desencontrasse as duas.

solução:       _pier_full_search_layout — busca EXATA por programação
               dinâmica sobre a posição. Todo passo do catálogo
               (comprimento + junta) é múltiplo de PIER_MODULE_CM=5
               (B39->40, B34->35, B19->20, C09->10, C04->5), então o trecho
               é uma composição de remaining/5 unidades e dá para percorrer
               TODAS. Minimiza EXATAMENTE a mesma tupla lexicográfica do
               _score que já existia (regra #2, regra #1, travamento,
               alinhamento de vazio) + nº de peças. Tetos de peça especial
               derivados do próprio baseline (_layout_piece_profile), a
               mesma licença que _pier_forced_bypass_layouts já tinha.
               Só roda quando a regra #1 ou a #2 ainda estão violadas:
               430 de 5.122 chamadas (8,4%), 0,49ms cada, 4% do runtime.

arquivos:      nuvem/core/engine/wall_stepper.py (produção)
               tests/test_block_bonding.py (suíte NOVA)
               nuvem/benchmark/diagnostics_block_prisma/** (benchmark)
               nuvem/REGRAS_MODULACAO_BLOCOS.md (nova seção 27)
               docs/PROJECT_STATUS.md (este registro)

protegidos:    geometry.py, wall_pairing.py, tolerances.py,
               continuous_modulation.py, modulation_math.py,
               wall_modeling.py, tests/test_script.py — NENHUM alterado.
               Arquivos exclusivos da CONTA 2 (diagnostics_block_audit/**,
               RELATORIO_BASELINE_BLOCOS.md, docs/BLOCK_MODULATION_AUDIT.md)
               — nenhum criado, editado, apagado ou renomeado.

testes:        tests/test_block_bonding.py  32 passed  (0,18s) — NOVA
               tests/regression             113 passed (22,9s)
               nuvem/tests                  18 passed  (0,03s)
               tests/test_script.py         259 passed, 1 FALHA ESPERADA
                 (test_pipeline_lanca_blocos_e_ajusta_na_mesma_passada:
                  assert 'shift' == 'trim'). NÃO é regressão de qualidade:
                  a asserção codificava a limitação antiga — medido nos
                  dois estados do código, o plano `shift` (ajuste MENOR,
                  comprimento do eixo inalterado) era rejeitado
                  EXCLUSIVAMENTE por sem_alinhamento_vertical. Com a regra
                  #1 satisfeita ele passa e o `trim` deixa de ser
                  necessário — exatamente a ordem de prioridade que a
                  seção 7 de REGRAS_MODULACAO_BLOCOS.md documenta. A
                  correção é de UMA LINHA ("trim" -> "shift"), mas
                  tests/test_script.py não pode ser editado nesta branch
                  (contrato de isolamento do CR). Ver REGRAS 27.9.

benchmark:     FORBIDDEN_JOINT_ALIGNMENT  418 -> 33   (-92,1%)
                 ... mesma banda (escopo)  236 -> 0    (-100%)
                 ... entre bandas          182 -> 33   (-81,9%)
               alignment_conflicts          64 -> 0    (-100%)
               CONTINUOUS_VERTICAL_JOINT   169 -> 138  (-18,3%)
               compensadores consecutivos 1342 -> 1210 (-9,8%)
               colisões                   1083 -> 1048 (-3,2%)
               paredes reprovadas          106 -> 104
               blocos dentro de abertura   281 -> 281  (inalterado)
               door_void_violations        638 -> 638  (inalterado)
               paredes com blocos      246/275 -> 246/275 (inalterado)
               falhas de encontro L/T/X    200 -> 200  (inalterado)
               non_modular                3333 -> 3336 (+3, redistribuição)
               runtime                   4,54s -> 4,78s (+5,3%)
               fingerprint canônico estável entre execuções repetidas

dívidas:       1) BANDAS de abertura fragmentam a memória entre fiadas —
                  as 33 coincidências restantes são TODAS na fronteira
                  entre bandas, que solve_building_blocks_all_courses
                  (core/wall_modeling.py) resolve independentemente.
                  NECESSIDADE DE ESCOPO ADICIONAL, registrada em
                  REGRAS_MODULACAO_BLOCOS.md 27.7 — não foi tocada porque
                  wall_modeling.py está fora da área de escrita do CR.
               2) UNCLASSIFIED_RULE_CONFLICT = 1506 — coincidências que
                  envolvem peça de amarração de nó, que a seção 5 manda
                  repetir e a regra #1 proíbe. CONFLITO REGISTRADO, nunca
                  resolvido por suposição (REGRAS 27.8).
               3) non_modular +3 — o reparo local de abertura não conhece
                  o critério de _layout_acerto_penalty (REGRAS 27.8).
               4) asserção estale em tests/test_script.py (REGRAS 27.9).

próximo passo: revisão + auditoria cruzada com a CONTA 2. Depois: o CR das
               BANDAS (dívida 1), que é onde estão 100% das coincidências
               proibidas que sobraram.
```

### 2026-09-01 — criação do documento

```
data:          2026-09-01
CR:            (nenhum — documento de acompanhamento criado agora)
branch:        claude/project-status-tracking-qm3r56
SHA inicial:   c21a4297a6ff372358cbb81da5ca6a65f91a955b (main, sem alteração)
SHA final:     (ver commit deste documento)
status:        documental apenas — nenhum código de produção, teste ou
               benchmark alterado
o que foi alterado:
  - criado docs/PROJECT_STATUS.md, registrando o histórico já mergeado
    (CR-2F-E, CR-2F-A) e o estado do CR-2F-D em andamento, com base no
    log de commits da main e em nuvem/REGRAS_MODULACAO_BLOCOS.md
    (seções 26.8.7 a 26.9.7) e nuvem/benchmark/diagnostics_2j/README.md
testes:        não executados (nenhuma alteração de código) — números
               reportados (245 passed / 113 passed) refletem o último
               resultado aprovado e registrado para o CR-2F-A
invariantes:   11/11 aprovados (ver seção 4), sem alteração
benchmarks:    sem alteração — números da seção 3 refletem o baseline
               aprovado do CR-2F-A
novas dívidas: nenhuma nova; dívidas existentes consolidadas na seção 6
itens resolvidos:  nenhum (documento de acompanhamento, não de correção)
itens ainda pendentes: CR-2F-D completo (seção 5); roadmap de modulação
               de blocos (seção 10)
próximo passo recomendado: avançar o CR-2F-D conforme seção 5 e
               atualizar este documento ao concluí-lo
```

### 2026-09-01 — CR-2F-D concluído na branch

```
data:          2026-09-01
CR:            CR-2F-D (determinismo do merge + recuperação da W097)
branch:        claude/cr-2f-d-determinism-ewnru5
SHA inicial:   c21a4297a6ff372358cbb81da5ca6a65f91a955b (baseline original do CR-2F-D)
merge-base ATUAL com a main (pós git merge origin/main): d16965dba45b81c2a109bc24b23ab2fcb959db10
SHA final:     (ver commit de merge desta atualização)
status:        CONCLUÍDO na branch — main NÃO alterada, aguardando
               autorização de merge
o que foi alterado:
  - nuvem/core/engine/geometry.py: base canônica na passada 1 de
    merge_collinear_fragments (+ varredura `taken`), ordem e sentido
    canônicos em _merge_collinear_cluster, e os novos
    _pair_symmetric_axis_gap_ft_cached / symmetric_axis_gap_ft
  - nuvem/core/engine/wall_pairing.py: deduplicate_walls passa a exigir o
    critério do trecho compartilhado EM CONJUNÇÃO com o do CR-2F-A, e o
    desempate do representante deixa de depender da ordem de entrada
  - tests/test_script.py: 11 invariantes novos (INV-DET-001..007,
    INV-DEDUP-D-001..004), todos sobre geometria sintética
  - nuvem/REGRAS_MODULACAO_BLOCOS.md: seção 26.10 (10 subseções), incluindo
    a correção de atribuição de 26.8.7.8/26.8.8.4 e o gate H6' de volta a
    87/97
  - nuvem/benchmark/diagnostics_2k/: censo e bateria reproduzíveis
  - nuvem/benchmark/diagnostics_2d/render_w097.py + 2 PNG: diagnóstico
    visual da W097, aprovado pelo usuário antes da implementação
  - NÃO tocados: create_centerline, find_wall_pairs, tolerances.py
testes:        tests/test_script.py 256 passed (245 antigos + 11 novos);
               tests/regression 113 passed
invariantes:   11 anteriores PASSED sem nenhuma edição de teste;
               11 novos PASSED
benchmarks:    produção + 5 seeds — merge fingerprints 6 → 1, wall
               fingerprints 3 → 1, 201 pares, 145 paredes, 87/97, 96
               eixos, 91/91, 7/7, 4 espúrias, W097 recuperada;
               assimetria 0/281.162 (merge) e 0/1.646 (dedup);
               solver_decision_fingerprint inalterado;
               passada 1 do merge 9,15 s → 8,67 s (−5,2 %)
novas dívidas: divergência gabarito × CAD na W097 (~2 cm) — problema do
               reference.json, não do solver (seção 6)
itens resolvidos:  não-determinismo residual do agrupamento; perda da W097
itens ainda pendentes: eixo espúrio de 43,9 m do par (474, 2306), sem CR
               atribuído; as 10 paredes ausentes remanescentes; roadmap de
               modulação de blocos (seção 10)
próximo passo recomendado: autorizar o merge do CR-2F-D na main e, em
               seguida, fazer o TESTE VISUAL NO REVIT (seção 9)
```

### 2026-09-01 — CR-2F-D mesclado na main

```
data:          2026-09-01
CR:            CR-2F-D (determinismo do merge + recuperação da W097)
branch:        claude/cr-2f-d-determinism-ewnru5 (mesclada, preservada)
SHA da main ANTES do merge: d16965dba45b81c2a109bc24b23ab2fcb959db10
SHA do commit documental (correção do merge-base): 55f7f8c0be643455498827828aa615792efec8d5
SHA do merge na main:       f7055c7e71c02415ffffe36f1f041b11c559df92
status:        CONCLUÍDO E MERGEADO NA MAIN, por merge commit (sem
               squash, sem rebase, sem force push)
verificação pós-merge: 256 passed (tests/test_script.py), 113 passed
               (tests/regression), solver_decision_fingerprint
               inalterado, merge fingerprint = 1, wall fingerprint = 1,
               201/145/87/96/91/7/4/W097 confirmados nas 6 ordens
próximo passo: TESTE VISUAL NO REVIT
```

### 2026-09-01 — REVIT SHORT CURVES: bloqueio encontrado e corrigido na branch

```
data:          2026-09-01
CR:            REVIT — SHORT CURVES (bloqueio de integração, extração de CAD)
branch:        fix/revit-short-cad-curves
SHA inicial:   c5447fe72ad1d2933b3eef74d63f1279c6a76cf6 (main, antes do CR-2F-D
               ser corrigido de merge-base — ver nota abaixo)
SHA da branch (fix aplicado): 751846a1d08fd98b1e897852ded8cdaac1b41568
status:        CONCLUÍDO na branch — aguardando sincronização com a main
               atual (25 commits à frente do baseline original) e merge
o que foi alterado:
  - nuvem/core/wall_modeling.py: extract_lines_by_layer passa a ler
    Application.ShortCurveTolerance (via doc.Application, cacheada em
    _get_short_curve_tolerance()) e ignora, ANTES de Line.CreateBound,
    qualquer segmento com distance <= ShortCurveTolerance
    (_segment_too_short_for_revit), nos ramos Line e PolyLine; log-resumo
    único da extração (total/ignorados/menor comprimento/layers)
  - tests/revit_stubs.py: Application do stub ganha ShortCurveTolerance
    real (1/32" em pés) em vez de inerte
  - tests/test_script.py: 4 testes de regressão novos
  - docs/PROJECT_STATUS.md: criado (depois reconciliado com a versão
    completa da main nesta atualização)
  - NÃO tocados: create_centerline, find_wall_pairs,
    core/engine/{geometry,wall_pairing,tolerances}.py
testes:        241 passed (tests/test_script.py, branch isolada, antes da
               sincronização com a main)
diagnóstico comparativo Revit 2026 × 2027 (antes da correção): mesma
               ShortCurveTolerance (0,00256026455729 pé) nas duas
               versões; teste "que funcionou" no 2027 usava CAD diferente
               (TORRE, sem P-PIPE) — sem evidência de diferença de motor
validação real no Revit 2026 + T01 LIMPA (via MCP, função de produção):
               49.127 segmentos examinados, 40.028 válidos, 9.099
               ignorados por ShortCurveTolerance, menor comprimento
               1,3384461397e-06 pé, layers afetados A-DETL-HDLN/M-EQPM/
               P-PIPE/P-PIPE-CNTR/Sanitário; layer Arquitetura (usado no
               teste) perdeu 0 linhas; extração terminou sem exceção
diagnóstico anexo — detector de espessuras da UI: "14cm → 7 pares" é
               amostragem de scan_candidate_thicknesses_cm sobre
               raw[:900] (SETUP_THICKNESS_SCAN_MAX_LINES), sem religar
               fragmentos, de um total de 9.258 linhas no layer
               Arquitetura; o solver real (find_wall_pairs, sobre as
               9.258 linhas inteiras religadas) formou 199 paredes reais
               para o alvo 14cm; não é regressão, não limita o solver;
               NÃO corrigido agora, por decisão do usuário
novas dívidas: detector de espessuras da UI amostra só 900 linhas cruas,
               sem religamento — pode ocultar espessuras reais da lista
               de sugestão em CADs mais extremos (seção 6); registrado
               como dívida de UX, não corrigido
itens resolvidos:  bloqueio ShortCurveTolerance na extração do CAD
itens ainda pendentes: teste visual INTEGRADO completo (criação de
               paredes + inspeção visual no Revit) — adiado por decisão
               do usuário; dívida de amostragem do detector de
               espessuras
próximo passo recomendado: sincronizar a branch com a main atual (git
               merge origin/main, sem rebase/force), rodar a suíte
               completa e mesclar por merge commit
```

### 2026-09-01 — REVIT SHORT CURVES: sincronizada e mesclada na main

```
data:          2026-09-01
CR:            REVIT — SHORT CURVES (bloqueio de integração, extração de CAD)
branch:        fix/revit-short-cad-curves (mesclada, preservada)
SHA da main ANTES do merge: (ver seção 2 / commit deste merge)
SHA da branch pós-sincronização (git merge origin/main, sem rebase): (ver
               commit de merge desta atualização)
SHA do merge na main: (ver commit de merge desta atualização)
status:        CONCLUÍDO E MERGEADO NA MAIN, por merge commit (sem
               squash, sem rebase, sem force push)
conflitos na sincronização: só em docs/PROJECT_STATUS.md (add/add — as
               duas branches criaram o arquivo independentemente),
               resolvido preservando a versão completa da main e
               acrescentando o histórico desta correção. Nenhum conflito
               em core/engine/geometry.py, core/engine/wall_pairing.py,
               tolerances.py, create_centerline ou find_wall_pairs — os
               commits do CR-2F-D vieram limpos (a branch nunca os havia
               tocado).
verificação pós-sincronização: ver testes na próxima seção do log (após
               a suíte completa)
detector de espessuras da UI: mantido como está — dívida de UX registrada
               (seção 6), correção NÃO autorizada nesta rodada
próximo passo: PRÓXIMA FASE AUTORIZADA — MODULAÇÃO DOS BLOCOS (seção 10).
               Teste visual integrado completo no Revit continua
               pendente, retomar quando o usuário priorizar.
```

### 2026-09-02 — `CR-BLOCK-DETERMINISM` (determinismo do wall graph e do pipeline de blocos)

```
data:          2026-09-02
CR:            CR-BLOCK-DETERMINISM (CONTA 1 de um par de sessões paralelas;
               a CONTA 2 faz auditoria independente e não altera produção)
branch:        claude/block-pipeline-determinism-uj7cvq
SHA baseline:  24ada98f5a8d4e7aa4cf0b30621d7818e4bb4fdc
status:        IMPLEMENTADO — AGUARDANDO CROSS-AUDIT
merge:         NÃO feito (o CR proíbe explicitamente; a autorização
               permanente de merge direto do CLAUDE.md NÃO se aplica aqui)
```

**PROBLEMA (reproduzido, não herdado)** — sobre a mesma geometria, as 8
execuções do censo (`baseline`, `reversed`, `endpoint_reversal`,
`shuffle_seed_{1,2,3,10,42}`) produziam **8 fingerprints distintos**. O
`run_determinism_census.py` da CONTA 2, re-rodado sobre esta `main`,
devolve exatamente as mesmas contagens de peças — o JSON versionado dela
era de um commit anterior ao merge do `CR-BLOCK-01`.

**PRIMEIRA DIVERGÊNCIA** — fingerprint canônico por camada
(`nuvem/benchmark/diagnostics_block_determinism/out_baseline.json`;
nenhum deles olha `wall_idx`, ordem de lista, `id()` ou ordem de `dict`):

| camada | antes | depois |
|---|---|---|
| `fp_input_walls` | 1 | 1 |
| `fp_nodes` | **8** | **1** |
| `fp_node_classifications` | 8 | 1 |
| `fp_end_to_node` | 8 | 1 |
| `fp_midspan` | 1 | 1 |
| `fp_ltx_reservations` | 7 | 1 |
| `fp_candidates` | 8 | 2 |
| `fp_blocks` | 8 | 2 |

A primeira camada divergente era `fp_nodes` nas 7 variantes: o problema
estava **inteiramente dentro de `build_wall_graph`**. `find_wall_pairs`,
`extend_wall_ends_to_junctions` e o `junction_map` ficam **bit-idênticos**
— o conjunto de paredes que ENTRA no grafo nunca mudou.

**CAUSA-RAIZ** (sub-camadas, `out_rootcause.json` / `out_examples.json`):

1. `_cluster_wall_arms` — agrupamento guloso em bola de raio fixo em volta
   da **primeira ponta visitada**. "Âncoras a ≤ 5 cm" **não é transitiva**:
   dois trios medidos com `d(A,B)=3,50`, `d(A,C)=2,41`, `d(B,C)=5,91` cm.
   Efeito: 256 → 257/258 clusters, 273 → 274/275 nós, `T_INTERSECTION`
   118 → 119/120.
2. `_classify_wall_node` — `point = group[0]["anchor"]`. 11 grupos têm a
   mesma parede com as **duas** pontas (parede mais curta que a
   tolerância); em ≥ 2 deles o nó andava **4,45 cm** com a inversão do eixo.
3. `_classify_wall_node` — papéis por **posição** em `arm_ids`. Medidos
   22–63 nós geometricamente idênticos com `main`/`incoming`/`neighbor`
   trocados e 4–55 com `arms` em ordem diferente.
4. `_find_wall_midspan_crossings` — `crossing_walls = (i, j)` por **índice**;
   17 cruzamentos em X trocavam a ordem do par, que decide qual parede
   recebe o B54 da fiada A e qual o da fiada B.
5. (latente) `_wall_end_geometric_anchor` / `_find_wall_touching_point` —
   desempate "primeiro vence", isto é, pelo índice na lista.

**IMPLEMENTAÇÃO** — único arquivo de produção tocado:
`nuvem/core/engine/wall_pairing.py`, e dentro dele só `build_wall_graph` e
os helpers de construção/classificação de nó. Componente conexa
(union-find) no agrupamento; chaves canônicas puras
(`_wall_graph_wall_key` / `_wall_graph_arm_key` / `_wall_graph_group_key`);
centroide das âncoras distintas como ponto do nó; `crossing_walls` e a
lista de cruzamentos em ordem canônica; desempate geométrico nas duas
buscas. **Sem tolerância nova** — foi medido que âncora, ponta e direção
saem bit-idênticas nas 8 permutações, então as chaves comparam float cru.

**SORT × CORREÇÃO ESTRUTURAL** (ablação obrigatória, `out_ablation.json`):

| ablação | fp grafo | fp blocos | trios PARTIDOS por variante |
|---|---|---|---|
| A0 `main` sem correção | 8 | 8 | **[0, 1, 2]** |
| A1 só ordenar a entrada | **2** | 2 | [0] |
| A2 componente conexa | 8 | 8 | [0] |
| A3 + ordem canônica | **1** | 2 | [0] |
| A4 correção completa | **1** | 2 | [0] |

**Só ordenar a entrada NÃO fecha o CR**: sobram 2 fingerprints, e a
partição continua decidida por ordem de visita (só que uma ordem fixa).
A2 mostra que a componente conexa já resolve a **ambiguidade estrutural**
(trios partidos: 0 em toda variante) mas não dá determinismo, porque os
papéis ainda vinham da ordem. A3 é a combinação que fecha o grafo.

**SEGUNDA CAUSA, LOCALIZADA E NÃO ESCONDIDA** — as **7 permutações** da
lista dão fingerprint de blocos **idêntico**. Sobra `endpoint_reversal`, e
a causa já não é o grafo: as peças de amarração L/T/X ficam iguais em
**1.581 de 1.581** pares (parede, fiada); quem diverge é só o
preenchimento (727 de 1.354), porque `_greedy_fill_blocks`
(`core/engine/wall_stepper.py`) corre de `GetEndPoint(0)` para
`GetEndPoint(1)`.

> **NECESSIDADE_DE_ESCOPO_ADICIONAL (1)** — `core/engine/wall_stepper.py`:
> o preenchimento comum precisa de referencial longitudinal canônico para
> o pipeline ficar invariante também ao **sentido de desenho**. Fora da
> área de escrita autorizada deste CR.

**NÃO-REGRESSÃO** (3 projetos, `diagnostics_block_prisma/metrics.py`):

| métrica | antes | depois |
|---|---|---|
| `same_band` forbidden (gate `CR-BLOCK-01`) | 0 | **0** |
| `alignment_conflicts` (gate `CR-BLOCK-01`) | 0 | **0** |
| paredes com blocos (gate `CR-BLOCK-01`) | 246/275 | **246/275** |
| `collisions` | 1048 | 1048 |
| `door_void_violations` | 638 | 638 |
| `intersection_failures` | 200 | 200 |
| `non_modular` | 3438 | 3435 |
| `pieces` | 29477 | 29359 |
| `cross_band` forbidden | 51 | 57 |

**PERFORMANCE** — `build_wall_graph` isolado, melhor de 7, cinco medições:
−7,2%, −1,0%, +0,4%, +3,1%, +3,5%. Diferença absoluta ≤ 0,02 s numa planta
de 167 paredes: **indistinguível de ruído**. Mesma classe de complexidade
(O(n²) em comparações de âncora); a componente conexa faz exatamente
`n(n−1)/2` comparações onde a bola gulosa fazia ≤ isso, mais union-find
(quase O(1) amortizado) e ordenação canônica de grupos de 1 a 4 pontas.

**TESTES**

| suíte | resultado |
|---|---|
| `tests/test_block_graph_determinism.py` (nova) | **27 passed** (2 `slow` inclusos) |
| `tests/test_script.py` | **260 passed** |
| `tests/test_block_bonding.py` | **32 passed** |
| `tests/regression` | **111 passed, 2 failed** |
| `nuvem/tests` | **18 passed** |

**RISCOS E DÍVIDAS**

1. As 2 falhas são `test_benchmark_baselines.py` (`torre_easy_lo_r00_tgd`:
   `COVERAGE_MISSING_ROW` 265→270, `OPENING_BLOCK_CROSSES_JAMB` 147→149;
   `tp1`: `COVERAGE_MISSING_ROW` 16→18). São consequência direta da
   canonização do papel A/B dos cantos em L — que **não era função da
   geometria**, saía da posição na lista, e por isso nenhuma ordenação
   canônica consegue reproduzi-lo. Nenhuma delas é violação de regra de
   amarração: `PRISM_CONTINUOUS_JOINT` e `JUNCTION_MISSING_BINDING` **não
   se movem** com a convenção adotada (as outras duas convenções medidas
   mexiam — ver `REGRAS_MODULACAO_BLOCOS.md` §28.3).

   > **NECESSIDADE_DE_ESCOPO_ADICIONAL (2)** — `nuvem/benchmark/projects/**`:
   > os `baseline.json` congelaram a ordem antiga e precisam ser
   > regravados. Fora da área de escrita autorizada deste CR. Mesma
   > situação do `CR-BLOCK-01`, cuja correção de teste ficou para a branch
   > de finalização.

2. A convenção de ordem dos braços foi escolhida por **medição nos três
   projetos**, não por princípio puro — a geometria genuinamente não
   decide esse empate. Está documentada em `REGRAS_MODULACAO_BLOCOS.md`
   §28.3 com a tabela das três candidatas, para que uma revisão futura
   não a troque sem refazer a medição.

3. `cross_band` forbidden 51 → 57: população que o `CR-BLOCK-01` deixou
   explicitamente fora de escopo (exigiria mexer em
   `solve_building_blocks_all_courses`). Não é o `same_band`, que continua 0.

4. `_classify_point_along_wall` testa `near_start` antes de `near_end`:
   numa parede vizinha mais curta que a própria espessura os dois podem
   ser verdadeiros. É **determinístico** (não depende de ordem), mas é uma
   ambiguidade geométrica não resolvida — registrada, não corrigida.
