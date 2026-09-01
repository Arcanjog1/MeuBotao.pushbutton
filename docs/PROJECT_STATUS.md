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
de segmentos de CAD. O `CR-2F-E` (centerline) e o `CR-2F-A` (simetria de
merge/pairing/deduplicação) já foram concluídos e mergeados na `main`. O
CR em andamento é o `CR-2F-D`, que ataca o não-determinismo residual
(agrupamento em estrela, não transitivo) e a perda da parede `W097`. A
modulação de blocos em si (o objetivo final do produto) ainda não foi
retomada — ela está registrada como roadmap futuro (seção 10), a ser
iniciada somente depois que a geometria das paredes estiver estável e
determinística.

## 2. Estado atual da main

```
branch: main
HEAD:   c21a4297a6ff372358cbb81da5ca6a65f91a955b
```

Últimos commits em `main` (mais recente primeiro):

```
c21a429  Merge pull request #4: CR-2F-A MERGE_RELATION_ASYMMETRY (T2/MAX)
33bb516  fix(wall-modeling): make the merge/dedup relation symmetric (CR-2F-A)
902bc70  Merge pull request #3: CR-2F-E CENTERLINE_ARGUMENT_ASYMMETRY
9bca561  fix(wall-modeling): make wall centerline order invariant (CR-2F-E)
```

O merge do CR-2F-A foi feito por **merge commit** (sem squash, sem rebase,
sem force push).

## 3. Baseline funcional atual

Produção + seeds (permutações da ordem de entrada: seed 1, seed 2, seed 3,
seed 10, seed 42) — projeto de referência `torre_easy_lo_r00_tgd`:

| métrica | valor (estável nas 6 execuções) |
|---|---|
| pares aceitos | 201 |
| paredes finais | 144 |
| cobertura do gabarito | 86/97 |
| eixos corretos (≤ 0,5 cm) | 96 |
| aberturas | 91/91 |
| paredes monitoradas | 7/7 |
| paredes espúrias | 4 |

Fingerprint oficial do solver (`solver_decision_fingerprint`), **inalterado**
por todo o CR-2F-A e CR-2F-E:

```
c74c9c1ae0e3f169f76e05fe53c01a858fce0af5b4e9d5f1b86fd71e92d2a316
```

## 4. Testes e invariantes aprovados

```
tests/test_script.py : 245 passed
tests/regression      : 113 passed
```

11 invariantes aprovados (`11/11 PASSED`):

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

### CR-2F-D — EM ANDAMENTO

- **Objetivo:**
  1. eliminar o não determinismo restante;
  2. estabilizar o fingerprint das paredes;
  3. investigar a causa da perda da `W097`;
  4. corrigir a classe estrutural do problema sem hardcode;
  5. preservar integralmente os resultados já aprovados (baseline da
     seção 3 e invariantes da seção 4).
- **Problema atual:** mesmo com a relação de compatibilidade já
  simétrica (CR-2F-A), permutar a ordem de entrada ainda muda o
  conjunto de linhas mescladas. Causa identificada: a relação continua
  **não transitiva** e o agrupamento continua sendo por **estrela**
  (quem sai do `pop(0)` vira a `base` e arrasta quem for compatível
  *com ela*, não com o cluster inteiro).
- **Fingerprint:** hoje as métricas (pares, paredes, cobertura, eixo,
  aberturas, monitoradas) são **idênticas** entre as seeds, mas existem
  **3 fingerprints distintos** das paredes finais entre as 6 execuções
  (produção + 5 seeds). Meta do CR-2F-D: **3 → 1** — o mesmo conjunto
  geométrico de entrada deve produzir sempre a mesma saída,
  independentemente da ordem de entrada.
- **W097:** parede do gabarito (`(-153,5; 817,0) -> (345,5; 817,0)`, 499
  cm) formalmente atribuída ao CR-2F-D. A parede boa que a cobre (707 cm
  em y=815, cobertura 1,000 antes do `deduplicate_walls`) é removida por
  ele, tratada como duplicata de uma parede **espúria de ~43,9 m**
  (`4.394,2 cm`, par `(474, 2306)`) — um segmento **cru do CAD** (cluster
  de 1 fragmento, não fabricado pelo merge). A causa raiz é a política
  de retenção "mantém a mais longa do grupo": quando o eixo passou a ser
  melhor centralizado (CR-2F-E), a espúria caiu a 0,363 cm da parede boa
  (abaixo de `DUPLICATE_AXIS_TOLERANCE` = 2 cm) e "venceu" por ser mais
  longa. Essa política histórica **não deve ser alterada de forma
  arbitrária** — o CR-2F-D deve primeiro demonstrar a causa real antes
  de propor qualquer mudança nela.
- **Critérios de conclusão** (mínimo esperado, sujeitos a validação do
  usuário ao fechar o CR):
  - fingerprint das paredes finais idêntico nas 6 execuções (produção +
    5 seeds) — 3 → 1;
  - causa estrutural do não-determinismo corrigida sem hardcode
    (não é permitido "fixar" a ordem de entrada como paliativo);
  - decisão explícita e documentada sobre a `W097` (recuperada com
    justificativa geométrica, ou mantida ausente com a causa
    formalmente registrada — não é permitido simplesmente ignorar);
  - todo o baseline da seção 3 e todos os 11 invariantes da seção 4
    continuam passando sem regressão;
  - `tests/test_script.py` e `tests/regression` verdes.

## 6. Dívidas técnicas conhecidas

- **Não-determinismo residual do agrupamento** (não transitividade +
  agrupamento em estrela) — objeto central do CR-2F-D (seção 5).
- **Perda da `W097`** — objeto do CR-2F-D (seção 5 e seção 7).
- **Pareamento `(474, 2306)`** — uma face de 155,61 cm pareada com uma
  linha auxiliar de 4.394,45 cm inclinada 1,1125 grau; não é merge, não
  é `deduplicate_walls` em si, é um dado bruto do CAD que interage mal
  com a política de retenção. Acompanha a investigação da `W097`.

## 7. Paredes ausentes conhecidas

Em relação ao gabarito de referência (`torre_easy_lo_r00_tgd`), continuam
ausentes 11 paredes:

```
W004, W005, W006, W007, W025, W026, W046, W047, W084, W085, W097
```

A `W097` é a única atribuída formalmente ao CR-2F-D (as outras 10 já
estavam ausentes antes do CR-2F-E/CR-2F-A e não fazem parte do escopo
declarado desses CRs). Existe também uma linha auxiliar de
aproximadamente **43,9 m** (segmento cru do CAD, par `(474, 2306)`) que
precisa ser considerada durante a investigação da `W097`.

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

1. Concluir o **CR-2F-D** (não-determinismo, fingerprint 3→1, causa da
   `W097`), respeitando os critérios da seção 5.
2. Validar o baseline completo (seção 3) e os 11 invariantes (seção 4)
   sem regressão.
3. Depois que a geometria das paredes estiver estável e determinística,
   avançar para a revisão/correção da **modulação dos blocos** — ver
   roadmap na seção 10.

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
