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

### 2026-09-04 — `CR-BLOCK-ARM-ROLE-HUMAN-POLICY` (continuação SAFE REPAIR) NECESSITA AJUSTE (não mesclado, nenhum código alterado)

```
data:          2026-09-04
CR:            CR-BLOCK-ARM-ROLE-HUMAN-POLICY, continuação SAFE REPAIR
status:        NECESSITA AJUSTE — docs/BLOCK_ARM_ROLE_HUMAN_POLICY.md,
               seção "CONTINUAÇÃO — SAFE REPAIR"

resumo: corrigido o gap de colisão da tentativa anterior (causa: nó
  duplicado no RESOLVE PARCIAL, não a vizinhança de 1 salto) reusando
  `result["collisions"]` (já completa, já existente) como gate. 3
  paredes (W021/W092/W076, TP1) reparadas com seguranca TOTAL medida
  (fechamento + colisão global + prisma em vizinhas). Um SEGUNDO gap,
  diferente, foi achado ao testar W137/TGD: introduz
  JUNCTION_NOT_ALTERNATING (nível 1) em 2 paredes vizinhas antes limpas,
  via um agrupamento de nó por proximidade que o benchmark faz e
  wall_stepper.py não replica. Revertido por completo de novo (nenhum
  código de produção no estado entregue) — sem 5º gate que cubra isso,
  nem os 3 candidatos "limpos" do TP1 têm prova de que ficariam limpos
  sempre.

próximo passo: construir esse 5º gate (replicar o agrupamento por
  proximidade localmente) ou obter autorização explícita de escopo para
  reusar nuvem/benchmark/validators/validate_junctions.py como
  dependência de produção.
```

### 2026-09-04 — `CR-BLOCK-ARM-ROLE-HUMAN-POLICY` (primeira tentativa) NECESSITA AJUSTE (não mesclado, nenhum código alterado no estado final)

```
data:          2026-09-04
CR:            CR-BLOCK-ARM-ROLE-HUMAN-POLICY (continuação de
               CR-BLOCK-ARM-ROLE-RESIDUALS, entrada abaixo)
branch:        claude/cr-block-arm-role-policy-q0qepg (esta branch, não
               PR #9) — main + cherry-pick dos 3 commits de produção do
               PR #9 (963aa9b/d813f45/77bda14) + 997ce46 (docs)
status:        NECESSITA AJUSTE — relatório completo
               docs/BLOCK_ARM_ROLE_HUMAN_POLICY.md (gates G1-G18)

resumo: causa provada (não mais hipótese) do prisma forçado em paredes
  curtas isoladas (6 das 9 residuais): quando as duas pontas usam a
  mesma peça de canto e o vão restante não tem composição alternativa,
  a alternância "sempre-diferente" força a mesma junta nas 17 fiadas.
  Política formal escrita. Implementação tentada em wall_stepper.py
  (detector de arestas isoladas + prisma forçado, provado correto
  contra os projetos reais) mas REVERTIDA antes do commit: o reparo (a
  troca de papel) usava verificação local de 1 salto que não checava
  colisão, e introduzia POSITION_OVERLAP real (medido: 18→74270 no
  TP1) quando ativo. Nenhum código de produção no estado final
  entregue (idêntico ao já relatado em CR-BLOCK-ARM-ROLE-RESIDUALS).

próximo passo recomendado: reimplementar o reparo com verificação
  completa (estilo ETAPA 3C — reconstruir e resolver de novo, checando
  `result["collisions"]`) em vez do resolve parcial de 1 salto.
```

### 2026-09-03 — `CR-BLOCK-ARM-ROLE-RESIDUALS` BLOQUEADO POR ESCOPO (não mesclado, nenhum código alterado)

```
data:          2026-09-03
CR:            CR-BLOCK-ARM-ROLE-RESIDUALS (continuação de
               CR-BLOCK-ARM-ROLE-PRISM-STAGGER, entrada anterior abaixo)
branch:        claude/cr-block-arm-role-invariance-7tezx4 (PR #9, draft)
HEAD:          77bda141df0038c973971075b09f3320e274adb2 (inalterado -
               nenhum código de producao mudou nesta continuacao)
status:        BLOQUEADO POR ESCOPO

resumo: investigou as duas pendencias do CR anterior. (1)
  OPENING_BLOCK_INSIDE_DOOR +3 no TGD: causa provada - artefato
  pre-existente de opening_active_in_row (fiada de fronteira contada
  como "ativa" por so' 5% da sua altura); as mesmas 3 paredes ja'
  tinham este achado no estado limpo antes de qualquer CR desta serie -
  nao e' invasao fisica nova, e' problema de medicao do benchmark, nao
  tocado em producao. (2) as 9 paredes de prisma residual: comparadas
  sistematicamente contra o Reference Corpus humano (casamento
  geometrico correto, nao por id) - 8 de 9 tem correspondente humano, e
  NENHUMA tem junta coincidente na referencia; o humano evita a
  coincidencia concentrando as duas pecas de canto na MESMA fiada (nao
  alternando como a coordenacao atual faz) ou usando composicao mais
  rica. Corrigir isso exigiria revisar a POLITICA de desempate da
  coordenacao deterministica - explicitamente fora do escopo autorizado
  desta continuacao ("nao desfazer a coordenacao A/B").

detalhe completo: docs/BLOCK_ARM_ROLE_INVARIANCE.md (gates G1-G16,
  classificacao das 9 paredes, caso W076 detalhado). Nova secao 29.7 de
  REGRAS_MODULACAO_BLOCOS.md registra o padrao observado (ainda nao
  confirmado, nao promovido a regra).

proximo passo: (1) decisao humana sobre regravar baseline.json do TGD
  ou refinar opening_active_in_row; (2) nova CR, com autorizacao
  explicita, para revisar o desempate da coordenacao a luz da
  evidencia humana. PR #9 (draft) permanece; NAO MESCLADO.
```

### 2026-09-03 — `CR-BLOCK-ARM-ROLE-PRISM-STAGGER` NECESSITA AJUSTE (não mesclado)

```
data:          2026-09-03
CR:            CR-BLOCK-ARM-ROLE-PRISM-STAGGER (continuação de
               CR-BLOCK-ARM-ROLE-CONSISTENCY, entrada anterior abaixo)
branch:        claude/cr-block-arm-role-invariance-7tezx4 (PR #9, draft,
               não mesclado)
SHA inicial:   d813f457108ef187b35dd581c35821d22ad23c4d
SHA final:     ver commit desta entrega, topo do log
status:        NECESSITA AJUSTE (gates G7/G8/G9 falharam - ver relatorio
               completo docs/BLOCK_ARM_ROLE_INVARIANCE.md, reescrito
               para este CR)

o que foi investigado: a regressao de PRISM_CONTINUOUS_JOINT introduzida
  por CR-BLOCK-ARM-ROLE-CONSISTENCY (11 paredes reais - 3 TGD, 8 TP1 -
  que antes nao tinham nenhum achado de prisma passaram a ter TODAS as
  juntas entre fiadas consecutivas alinhadas). Causa-raiz provada por
  cadeia completa (papel coordenado -> solve_l_corner -> peca ->
  orientacao -> posicao da junta -> fill -> junta na fiada oposta), nao
  so' pelo validador final: a junta entre a peca de canto de um no' e o
  primeiro/ultimo bloco do preenchimento comum adjacente NUNCA foi
  rastreada pelo mecanismo de desencontro de junta vertical (secao 6,
  `_layout_internal_joint_positions_cm` so' conta juntas INTERNAS ao
  preenchimento, por design documentado) - inofensivo enquanto so' uma
  familia tinha candidato de no' real num dado encontro; a coordenacao
  de papel deu as duas familias um candidato real no MESMO encontro, e
  quando ambas escolhem a MESMA peca (B34, decisao geometrica correta,
  independente da coordenacao) a junta de contorno coincide sem a busca
  de desencontro saber. Hipotese inicial (vao menor B34/B54
  dessincronizado da paridade par/impar) REFUTADA - a orientacao/posicao
  da peca de canto e' sempre determinada por geometria pura, nunca por
  course_a/course_b.

fix implementado (nuvem/core/engine/wall_stepper.py, unica alteracao de
  producao): `_pier_boundary_joint_positions_cm` computa a posicao da
  junta de contorno contra um no'; duas listas NOVAS e SEPARADAS
  (`course_a_boundary_joint_positions_cm`/`own_family_boundary_joint_
  positions_cm`) alimentam a busca de desencontro e a checagem residual
  (`alignment_conflicts`, que agora tambem dispara para pier de 1 bloco
  so', antes escondido por `len(layout) > 1`) - mas NUNCA o reparo de
  abertura (`_recut_openings_and_repair`), separacao necessaria depois
  de medir uma regressao real em OPENING_BLOCK_INSIDE_DOOR na primeira
  versao do fix (misturando as listas).

testes: 5 testes novos e permanentes
  (tests/test_block_arm_role_prism_stagger.py), rodando o corpus real
  via nuvem.benchmark.solver_bridge (o caso minimo de W076 depende da
  reserva "emprestada" do quadrado do canto, so' existe com topologia
  real de mais de 2 paredes por no'). 2 deles falham no codigo anterior
  ao fix pela razao certa (confirmado via git stash). Suite rapida
  completa: 518 passed (513 + 5 novos).

benchmarks (torre_easy_lo_r00_tgd/tp1/piloto_sintetico_2x2, comparacao
  A=origin/main limpo (7c9a681) / C=d813f45 (ARM-ROLE-CONSISTENCY) /
  D=este fix):
    - coverage (MISSING_ROW/MOSTLY_EMPTY): IDENTICO entre C e D nos 3
      projetos - o ganho de cobertura do commit d813f45 esta' 100%
      preservado;
    - PRISM_CONTINUOUS_JOINT: TGD 702(A)->691(C)->476(D); TP1
      837(A)->896(C)->576(D) - cai ABAIXO ate' do estado anterior a
      qualquer CR desta serie nos dois projetos reais;
    - NEW_PRISM_WALLS: 11 antes do fix -> 9 depois (W117/TGD e
      W041/TP1 resolvidos por completo - tinham liberdade real de
      composicao; as 9 restantes tem o pier cabendo EXATAMENTE 1 bloco,
      coincidencia matematicamente forcada pela mesma peca B34 nas duas
      pontas - detectada e reportada via alignment_conflicts, mas nao
      eliminavel sem mudar qual peca e' escolhida num dos dois nos,
      mudanca mais invasiva nao implementada);
    - OPENING_BLOCK_INSIDE_DOOR (TGD): 43(A)->43(C)->46(D) - REGRESSAO
      REAL, +3, em 3 paredes ja' afetadas (nenhuma nova), causa exata
      nao totalmente diagnosticada mesmo apos a separacao de listas;
    - POSITION_OVERLAP (colisoes): identico nos 3 estados, nenhuma
      mudanca.

novas dividas: (1) 9 paredes com PRISM_CONTINUOUS_JOINT geometricamente
  forcado - eliminar exigiria mudar a selecao de peca de canto em
  solve_l_corner (B54 em vez de B34), decisao que precisa de
  autorizacao explicita do usuario antes de qualquer tentativa; (2)
  regressao de OPENING_BLOCK_INSIDE_DOOR (+3, TGD) precisa de
  investigacao propria. Documentado como secao 29.6 (atualizada) de
  REGRAS_MODULACAO_BLOCOS.md.

itens resolvidos: causa-raiz completa da regressao de prisma provada
  (cadeia completa, hipoteses H1-H7 testadas e documentadas); 2 de 11
  paredes com prisma novo resolvidas por completo; reducao substancial
  do total de PRISM_CONTINUOUS_JOINT nos dois projetos reais.

itens ainda pendentes: as 9 paredes com coincidencia geometricamente
  forcada; a regressao de OPENING_BLOCK_INSIDE_DOOR.

proximo passo recomendado: decidir, com o usuario, se vale a pena
  investigar mudanca na selecao de peca de canto para as 9 paredes
  restantes; diagnosticar a regressao de OPENING_BLOCK_INSIDE_DOOR antes
  de qualquer nova tentativa. Ver docs/BLOCK_ARM_ROLE_INVARIANCE.md para
  o relatorio completo, gate a gate. PR #9 (draft) permanece; NAO
  MESCLADO.
```

### 2026-09-03 — `CR-BLOCK-ARM-ROLE-CONSISTENCY` NECESSITA AJUSTE (não mesclado)

```
data:          2026-09-03
CR:            CR-BLOCK-ARM-ROLE-CONSISTENCY (continuação de
               CR-BLOCK-ARM-ROLE-INVARIANCE, entrada anterior abaixo)
branch:        claude/cr-block-arm-role-invariance-7tezx4 (PR #9, draft,
               não mesclado)
SHA inicial:   963aa9b227d0e635ee020494c9891591af18531d
SHA final:     ver commit desta entrega, topo do log
status:        NECESSITA AJUSTE (gate G10 falhou — ver relatório completo
               docs/BLOCK_ARM_ROLE_INVARIANCE.md, agora reescrito para
               este CR)

o que foi alterado: o workaround "reserva de fronteira emprestada"
  (29.2/entrada anterior deste histórico) foi REMOVIDO — o usuário
  rejeitou esse fix por só reclassificar COVERAGE_MISSING_ROW em
  COVERAGE_ROW_MOSTLY_EMPTY, sem resolver a causa raiz. No lugar,
  implementado `_coordinate_arm_role_nodes` (nuvem/core/engine/
  wall_stepper.py, única alteração de produção): coordena
  deterministicamente, via 2-coloring de grafo (formalizado ANTES de
  assumir essa estrutura — ver relatório, seção "Contrato formal"), o
  papel course_a/course_b entre os DOIS nós L_CORNER de 2 braços que
  fecham as duas pontas da MESMA parede, para que nunca escolham papéis
  contraditórios. Raiz e ordem de visita do BFS sempre por identidade
  geométrica do nó (nunca por ordem de lista), garantindo invariância a
  arms/paredes de entrada/reversão de endpoint.

  Prova combinatória (não apenas geométrica) de que ciclos — pares OU
  ímpares — de nós L_CORNER de 2 braços são SEMPRE 2-coloráveis (soma
  XOR de paridade ao redor de qualquer ciclo é sempre 0, por
  telescopagem): o ramo de conflito residual da coordenação é
  matematicamente inalcançável para esta regra de elegibilidade, mantido
  como rede de segurança determinística.

testes: 16 testes em tests/test_block_arm_role_invariance.py (2 novos:
  retângulo fechado real / ciclo par sem conflito; prova geral de ciclo
  par-ou-ímpar sem conflito residual, por construção, várias
  combinações de ordem de arms) + 1 teste atualizado em
  tests/test_script.py (colisão de mesma-fiada deixa de ocorrer + as
  duas pontas da parede curta passam a alternar A/B). Suíte rápida
  completa: 513 passed. Suíte lenta (regressão contra baseline.json):
  2 failed (TGD, TP1 — ver "novas dívidas" abaixo, não escondido).

benchmarks (torre_easy_lo_r00_tgd/tp1/piloto_sintetico_2x2, comparação
  A=origin/main limpo (7c9a681) / B=workaround anterior (963aa9b) /
  C=este estado):
    - TGD: COVERAGE_MISSING_ROW 265→258 (-7); COVERAGE_ROW_MOSTLY_EMPTY
      171→153 (-18, a regressão de +138 do workaround anterior NÃO
      ocorre mais); TOTAL_COVERAGE_CRITICAL 436→411 (-25);
      PRISM_CONTINUOUS_JOINT por parede 39→41 (+2, ver "novas dívidas");
    - TP1: COVERAGE_MISSING_ROW 16→0 (eliminado); COVERAGE_ROW_
      MOSTLY_EMPTY 27→18 (-9); TOTAL_COVERAGE_CRITICAL 43→18 (-58%);
      PRISM_CONTINUOUS_JOINT por parede 50→53 (+3, defeito NOVO em 8
      paredes, não reclassificação — ver "novas dívidas");
      JUNCTION_MISSING_BINDING 8→9 (+1, confirmado mesma junção
      W039/W041, mirror de paridade, não é uma junção nova);
    - piloto: nenhuma mudança em nenhuma métrica.
  Casos nomeados verificados individualmente: W022/TP1 e W093/TP1 —
  COVERAGE_MISSING_ROW/MOSTLY_EMPTY eliminados, substituídos por
  COVERAGE_GAP_IN_ROW (severidade menor, reclassificação explícita);
  W011/piloto — nenhuma mudança (fora da topologia do defeito).

novas dívidas: PRISM_CONTINUOUS_JOINT regride em paredes que antes não
  tinham NENHUM achado desse código (8 no TP1 com TODAS as junções de
  fiada alinhadas, 2-3 no TGD) — hipótese não confirmada de que a
  coordenação desincroniza a alternância do vão menor (B34/B54) da
  regra fixa de paridade par/ímpar das fiadas. Documentado como seção
  29.6 de REGRAS_MODULACAO_BLOCOS.md ("DOCUMENTADO — pendência de código
  aberta"). Este é o motivo do veredito NECESSITA AJUSTE.

itens resolvidos: causa-raiz completa do mecanismo "arms order → course
  role → perda de fiada" (o workaround anterior só mitigava parte dela);
  a regressão COVERAGE_ROW_MOSTLY_EMPTY do fix anterior não existe mais.

itens ainda pendentes: root-cause e fix do efeito colateral em
  PRISM_CONTINUOUS_JOINT (seção 29.6); baseline.json não regravado
  (não deve ser, dado o veredito).

próximo passo recomendado: confirmar/corrigir a hipótese de 29.6 antes
  de qualquer nova iteração. PR #9 (draft) permanece; NÃO MESCLADO.
```

### 2026-09-03 — `CR-BLOCK-ARM-ROLE-INVARIANCE` NECESSITA AJUSTE (não mesclado)

```
data:          2026-09-03
CR:            CR-BLOCK-ARM-ROLE-INVARIANCE
branch:        claude/cr-block-arm-role-invariance-7tezx4 (PR #9, draft,
               não mesclado)
SHA inicial:   7c9a681aeda2027f8fc072c0f57c62454a80d669 (origin/main)
SHA final:     963aa9b227d0e635ee020494c9891591af18531d
status:        NECESSITA AJUSTE (gate G9 falhou — ver relatório completo
               docs/BLOCK_ARM_ROLE_INVARIANCE.md)

o que foi alterado: causa-raiz provada (caso real W042/TGD, wall_idx 41)
  de que dois nós L_CORNER/X_INTERSECTION de UMA MESMA parede decidem o
  papel course_a/course_b de forma totalmente independente entre si —
  sem alternância forçada, podem escolher o MESMO papel nas duas pontas,
  apagando a família oposta inteira quando combinado com a fronteira
  "emprestada" de uma parede vizinha raramente caindo no módulo de 5cm
  de blocos (preenchimento contínuo, tudo-ou-nada sem abertura para
  servir de ponto de quebra). Fix restrito a
  nuvem/core/engine/wall_stepper.py (wall_pairing.py intocado, conforme
  exigido pelo CR): arredonda a reserva "para dentro" (nunca menos) até
  o próximo múltiplo de PIER_MODULE_CM quando a família não tem NENHUMA
  peça de nó própria em nenhuma ponta, a família oposta TEM, e nem esta
  parede nem a doadora têm abertura própria.

  AVISO: o "wall graph determinístico"/ordenação canônica de arms que um
  CR anterior (CR-BLOCK-WALL-GRAPH-QUALITY) documentou NÃO está mesclado
  em origin/main neste SHA — só em branches não mescladas. O mecanismo e
  o fix são os mesmos independente disso (reproduzido manipulando
  node["arms"] em memória, sem depender de nenhuma convenção específica
  de wall_pairing.py).

testes: 14 testes sintéticos novos e permanentes
  (tests/test_block_arm_role_invariance.py) — 6 falham no estado
  anterior pelo motivo correto (confirmado via git stash). Suíte
  completa: 521 passed, 1 failed (a regressão documentada abaixo, não
  escondida).

invariantes: determinismo preservado (mesmo código/entrada → mesma
  saída, 3x confirmado); performance na mesma ordem de grandeza
  (TGD/TP1/piloto, ver relatório); wall_pairing.py/continuous_
  modulation.py/wall_modeling.py/geometry.py/tolerances.py/modulation_
  math.py NÃO alterados (git diff --stat confere).

benchmarks (torre_easy_lo_r00_tgd, contra origin/main LIMPO — não
  baseline.json, que está desatualizado para PRISM_CONTINUOUS_JOINT/
  OPENING_BLOCK_INSIDE_DOOR neste projeto, achado colateral não causado
  por este CR):
    - COVERAGE_MISSING_ROW: 265 → 145 (-120, melhoria grande);
    - COVERAGE_ROW_MOSTLY_EMPTY: 171 → 309 (+138, REGRESSÃO CRÍTICA —
      reclassificação medida de paredes que já tinham as duas famílias
      ruins: uma fica rescatável pelo fix, a outra continua exatamente
      como estava, nenhuma parede NOVA quebra, mas o total de achados
      sobe +123);
    - OPENING_BLOCK_CROSSES_JAMB/INSIDE_DOOR/PRISM_CONTINUOUS_JOINT:
      inalterados;
    - torre_easy_lo_r00_tp1 e piloto_sintetico_2x2: NENHUMA mudança em
      nenhum código (nenhuma parede desses dois projetos se qualificou
      para o escopo restrito do fix).

novas dívidas: resolução completa do resíduo COVERAGE_ROW_MOSTLY_EMPTY
  exige forçar ALTERNÂNCIA de papel entre os DOIS nós de uma mesma
  parede (problema de 2-coloração de grafo — cada nó de 2 braços é uma
  aresta entre duas paredes-vértice; ciclos de comprimento ímpar tornam
  alternância perfeita impossível em geral) — fora do escopo autorizado
  desta CR (só wall_stepper.py, sem "resolver toda a cobertura").
  Documentado como seção 29.4 de REGRAS_MODULACAO_BLOCOS.md.
  baseline.json e REFERENCE_SOLVER_DECISION_FINGERPRINT
  (tests/solver_bench.py) confirmados DESATUALIZADOS em relação a
  origin/main limpo (não causado por esta CR) — recomenda-se CR de
  manutenção próprio para atualizar os dois.

itens resolvidos: causa-raiz do mecanismo "arms order → course role →
  perda de fiada" provada e corrigida para o subconjunto de casos sem
  abertura envolvida nos dois lados do nó.

itens ainda pendentes: alternância de papel forçada entre nós da mesma
  parede (ver "novas dívidas"); resolução do caso com abertura numa das
  duas paredes do nó (fora do escopo, intencionalmente).

próximo passo recomendado: CR próprio para a alternância de papel
  (2-coloração), mesmo espírito do CR-BLOCK-NODE-FILL-JOINT já aberto —
  ver docs/BLOCK_ARM_ROLE_INVARIANCE.md para o relatório completo,
  gate a gate. PR #9 (draft) aberto para registro; NÃO MESCLADO — decisão
  humana explícita necessária sobre o trade-off G4/G9 documentado.
```

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
