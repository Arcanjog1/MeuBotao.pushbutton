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
recuperada. **PRÓXIMO PASSO: TESTE VISUAL NO REVIT.** A modulação de
blocos em si (o objetivo final do produto) ainda não foi
retomada — ela está registrada como roadmap futuro (seção 10), a ser
iniciada somente depois que a geometria das paredes estiver estável e
determinística.

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

## 6. Dívidas técnicas conhecidas

- ~~**Não-determinismo residual do agrupamento**~~ — **RESOLVIDO** pelo
  CR-2F-D (seção 5): 6 → 1 no merge, 3 → 1 nas paredes.
- ~~**Perda da `W097`**~~ — **RESOLVIDA** pelo CR-2F-D (seção 5).
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
3. **TESTE VISUAL NO REVIT** — próximo passo imediato. É a primeira
   validação da geometria determinística no modelo real, e não é
   substituível pelo benchmark headless.
4. Depois que a geometria das paredes estiver estável e determinística
   **e confirmada visualmente no Revit**, avançar para a revisão/correção
   da **modulação dos blocos** — ver roadmap na seção 10.

## 10. Modulação dos blocos — roadmap futuro

Estes itens são **roadmap**, não trabalho em andamento. Não devem ser
implementados antes de a geometria das paredes (CR-2F-D) estar fechada e
estável, exceto se o usuário pedir explicitamente uma exceção pontual.

- prisma entre fiadas;
- evitar blocos verticalmente alinhados indevidamente;
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
