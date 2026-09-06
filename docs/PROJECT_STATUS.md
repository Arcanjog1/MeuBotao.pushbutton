# PROJECT STATUS

> Estado **operacional atual** do projeto (Modulação Automática pyRevit).
> Só o que está em vigor agora. Histórico completo de CRs, dívidas
> resolvidas e o log cronológico de atualizações ficam em
> `docs/PROJECT_STATUS_LOG.md`.
>
> Novo numa sessão? Comece por `docs/START_HERE.md`.

## Main atual

```
branch: main
SHA:    3ebcd9b63875f9114a3d6223aa648e5075e2d35b
```

Último marco de PRODUÇÃO: `PR #19` / `CR-BLOCK-B19-RESIDUAL-FILL-
IMPLEMENTATION` — **mesclado** (a `main` avançou de `209695d` para
`3ebcd9b`; ver "Estado oficial do solver" abaixo). Antes dele, `PR #18` /
`CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY`. Histórico anterior completo:
`docs/PROJECT_STATUS_LOG.md`.

## Estado oficial do solver

Só o que está realmente mesclado na `main`, na ordem em que foi integrado:

- **CR-2F-E / CR-2F-A / CR-2F-D** — geometria de paredes determinística e
  simétrica (ordem de entrada não muda o resultado); `W097` recuperada.
- **REVIT — SHORT CURVES** — extração do CAD não quebra mais em
  `ShortCurveTolerance` (`nuvem/core/wall_modeling.py`).
- **CR-BLOCK-01** — prisma/fiadas/amarração: coincidência de junta
  proibida dentro da MESMA banda de abertura eliminada (236 → 0).
- **CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT** (`PR #12`) — contrato
  geral de segurança para candidatos de reparo de papel de nó
  (course_a/course_b); SAFE REPAIR ativado em produção
  (`nuvem/core/engine/wall_stepper.py`, `nuvem/core/wall_modeling.py`).
- **CR-BLOCK-NODE-FILL-REVALIDATION** (`PR #17`) — metade simétrica da
  junta NÓ|FILL: a Fiada A passa a desencontrar da junta de nó da Fiada B
  (`wall_stepper.py`, `NODE_FILL_OPPOSITE_COURSE_ENABLED = True`).
  `PRISM_CONTINUOUS_JOINT` TGD 444→336, TP1 576→272, piloto 0→0;
  cobertura/aberturas/colisões/junções/ARM com delta zero; 0 conflitos
  com o Reference Corpus humano. Regras: seção 33 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
- **CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY** (`PR #18`) — os 2 gates do
  SAFE REPAIR (compensador consecutivo, cobertura por fiada) mediam PROXY
  (agregado cross-banda por letra de família; posse local cega à peça de
  canto emprestada de nó), não o defeito real. Corrigidos para
  `course_index` físico (compensador) e crédito FÍSICO de nó com 5
  condições, nos dois sentidos alvo↔vizinha (cobertura). 2 novos
  candidatos ARM aceitos — `TGD wall_idx=91/SAME_B`, `TP1 wall_idx=75/
  SAME_A` — ambos `CONFIRMED_BY_HUMAN`; `PRISM_CONTINUOUS_JOINT` TGD
  336→320, TP1 272→256; cobertura/aberturas/colisões/junções com delta
  zero. Relatório: `docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_
  IMPLEMENTATION.md`; regras: seção 34 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
- **CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION** (`PR #19`, **mesclado**)
  — decisão humana aprovada sobre B19: pode fechar um trecho residual de
  15-20cm quando existir, no MESMO NO e na MESMA FIADA, uma peca de
  amarracao real e integra (B34/B54) cobrindo geometricamente o ponto
  fisico do no, nunca sendo ele mesmo a peca de amarracao. Implementado
  como reparo pos-hoc isolado (`repair_b19_residual_fill`, mesmo padrao
  seguro do SAFE REPAIR do ARM). Medido no corpus: **TP1 8 candidatos
  elegiveis, 0 aceitos** (rejeitados por `no_tie_covering_node`);
  TGD/Piloto 0 candidatos elegiveis - mecanismo correto, zero efeito
  pratico hoje, zero risco de regressao. Relatorio:
  `docs/BLOCK_B19_RESIDUAL_FILL_IMPLEMENTATION.md`; regras: secao 35 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`.

Detalhe técnico de cada um: `docs/PROJECT_STATUS_LOG.md`.

## Trabalho ativo

- **CR-BLOCK-FIT-TOLERANCE-C04** (branch
  `claude/cr-block-fit-tolerance-c04-n5qsc4`, **nao mergeado**,
  **veredito NEEDS_FIX**) - tolerancia dedicada `PIER_FIT_TOLERANCE_CM`
  (0,30cm, separada de `PIER_LAYOUT_TOLERANCE_CM`/
  `MODULATION_WHOLE_CM_TOLERANCE_CM`, que continuam em 0,05cm) para o
  mecanismo que decide se a sobra de um trecho e' modular/snapavel
  (`_pier_remaining_snapped_cm` em `wall_stepper.py`;
  `pier_closes_with_blocks_cm`/`wall_length_closes_with_blocks_cm` em
  `modulation_math.py`). Destrava cobertura real: `COVERAGE_GAP_IN_ROW`
  TGD 1959->1644/TP1 327->214, `blocks` TGD +1056/TP1 +1155 - bate a'
  unidade com a ablacao independente que aprovou o valor. MAS introduz
  um hard blocker medido: `OPENING_BLOCK_CROSSES_JAMB` TGD 108->144 (+36
  genuinos)/TP1 168->173 (+5 genuinos) - pecas recem-destravadas
  invadindo 0,12-0,267cm o vao livre de portas, acima do piso de ruido
  do proprio validador (0,1cm). Confirmado independentemente pelo
  guard-rail de regressao do benchmark
  (`tests/regression/test_benchmark_baselines.py`: TP1 falha como
  `REGRESSAO CRITICA` contra `baseline.json`, intocado por decisao da
  CR; suite completa 736 passed / 2 failed, ambas conhecidas). Relatorio
  completo:
  `docs/BLOCK_FIT_TOLERANCE_C04_IMPLEMENTATION.md`. **Aguarda decisao
  humana sobre o hard blocker antes de qualquer autorizacao de merge;
  sem monitoramento automatico.**

`PR #9` (`CR-BLOCK-ARM-ROLE-INVARIANCE`, **CLOSED, não mesclado** —
NECESSITA AJUSTE, branch histórica preservada) e `PR #11`
(`CR-BLOCK-ARM-ROLE-HUMAN-POLICY`, **CLOSED, mesclado** — docs-only,
conteúdo de produção idêntico ao já presente via `PR #9`/histórico,
superseded pela integração posterior) não são trabalho ativo — ver
`docs/PROJECT_STATUS_LOG.md` para o registro completo dessa série.

## Reference Corpus

3 projetos de benchmark (`torre_easy_lo_r00_tgd`, `torre_easy_lo_r00_tp1`,
`piloto_sintetico_2x2`) em `nuvem/benchmark/projects/`. Documento vivo com
o significado de cada métrica e o procedimento de medição:
`docs/REFERENCE_CORPUS.md`.

## Snapshot atual

Fotografia legível do último estado oficialmente medido da `main`:
`docs/CURRENT_REFERENCE_SNAPSHOT.md` (substituível — não é histórico,
não é append-only).

## Problemas abertos

- **Alinhamento cross-band** (entre bandas de abertura) — 33 casos
  residuais, fora do escopo do `CR-BLOCK-01`; exige mudança em
  `wall_modeling.py`. Ver `nuvem/REGRAS_MODULACAO_BLOCOS.md` 27.7.
  Próximo CR recomendado: `CR-BLOCK-DETERMINISM`.
- **Determinismo global do wall graph** — não determinístico antes e
  depois do `CR-BLOCK-01` (8 execuções, 8 fingerprints distintos); causa
  é anterior ao preenchimento de blocos.
- **Compensadores/pastilhas repetidos (C09/C04)** — melhoraram como
  efeito colateral, não resolvidos.
- **Degradação de encontros em X, exclusão de bloco em vão de porta,
  reparo de abertura (`non_modular` +3)** — pendentes, sem CR aberto.
- **Arestas rejeitadas no `CR-BLOCK-ARM-ROLE-CANDIDATE-SAFETY-CONTRACT`**
  (7 no TGD, 3 no TP1) — diagnosticadas em `docs/BLOCK_ARM_REJECTED_
  EDGES_DIAGNOSIS.md`. `CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY` (branch
  em aberto, ver "Trabalho ativo") corrigiu os 2 gates de proxy e
  resolveu 2/10 (`TGD 91`, `TP1 75`); as 6 restantes (TGD 89/90/92/120,
  TP1 20/91) continuam corretamente rejeitadas por causa física real
  (Grupo B — reserva pior-caso em parede curta; espelho de paridade —
  fora do escopo desta CR); 2 (TGD 4/54) são `OUT_OF_SCOPE_ROTATED_
  CORNER`. Próximo passo, se priorizado: `CR-BLOCK-SHORT-WALL-NODE-
  PIECES` (Grupo B, exige decisão de regra — ver diagnóstico).
- **Pareamento `(474, 2306)`** — eixo espúrio de ~43,9 m continua no
  resultado; sem CR atribuído.
- **Regra do meio-bloco (B19) perto de amarração** — evidência de domínio
  coletada (`docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md`) e decisão
  aprovada IMPLEMENTADA (e corrigida em revisão pós-review) em branch
  separada, não mesclada (`CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION`,
  PR #19, ver "Trabalho ativo") — B19 como fill residual de 15-20cm só
  quando o MESMO nó/MESMA fiada tem amarração real íntegra cobrindo o
  ponto físico, nunca substituindo B34/B54. Resultado medido no corpus
  atual: **0 candidatos aceitos em TP1/TGD/Piloto** (o padrão de
  alternância par/ímpar do canto L nunca satisfaz a condição de mesma
  fiada) — mecanismo correto e testado, mas sem efeito físico hoje; zero
  risco de regressão. Regra na `main` **ainda não alterada** (aguarda
  merge autorizado).
- **Detector de espessuras da UI** amostra só as primeiras 900 linhas
  cruas do layer — não limita o solver real, mas pode ocultar espessuras
  raras na sugestão da tela. Dívida de UX, não corrigida por decisão
  explícita do usuário.
- **Teste visual INTEGRADO completo no Revit** (extração → paredes
  criadas → inspeção visual) — adiado por decisão do usuário; retomar
  quando priorizado.

Detalhe/causa-raiz de cada item: `docs/PROJECT_STATUS_LOG.md`.

## Próximos passos

1. `CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY` — branch em aberto (ver
   "Trabalho ativo"); merge só com autorização explícita do usuário.
2. Aguardar autorização/priorização do usuário para o próximo CR de
   engine (candidatos: `CR-BLOCK-DETERMINISM`, alinhamento cross-band,
   compensadores/pastilhas, `CR-BLOCK-SHORT-WALL-NODE-PIECES` para as 6
   arestas do Grupo B/espelho de paridade que Gate Fidelity deixou
   corretamente rejeitadas).
3. Pendência registrada (33.5, NODE-FILL): o reparo local junto ao vão
   ainda recria a junta 34,5 em `W036`/`W038` (TP1, bandas com janela).
4. Teste visual integrado no Revit — retomar quando o usuário priorizar.

## Não reabrir sem evidência de regressão

Áreas já resolvidas e validadas (simetria de pairing/merge/dedup,
determinismo da passada 1 do merge, `ShortCurveTolerance`, amarração
same-band do `CR-BLOCK-01`) não devem ser alteradas só para "melhorar" —
exige evidência objetiva de regressão. Lista completa e o motivo de cada
uma: `docs/PROJECT_STATUS_LOG.md` (seção 8 do histórico).

Evitar mudanças sem necessidade concreta em `create_centerline`,
`find_wall_pairs`, `tolerances.py`.

## Regra permanente de atualização

Ao concluir qualquer CR de engine, **este documento e o
`docs/PROJECT_STATUS_LOG.md` devem ser atualizados antes de encerrar o
trabalho** — não é opcional. `PROJECT_STATUS.md` recebe só o resumo do
estado atual (seções acima); a entrada completa (o que foi alterado,
testes, invariantes, benchmarks, dívidas novas, próximo passo) vai para o
log cronológico em `PROJECT_STATUS_LOG.md`, sem apagar entradas
anteriores. Há um lembrete automático
(`.github/workflows/check-project-status.yml`) que sinaliza quando
`nuvem/core/engine/**` muda sem que `docs/PROJECT_STATUS.md` seja tocado
no mesmo diff — não bloqueia push/merge, só avisa.

## Entradas de contexto

- `docs/START_HERE.md` — roteador de onboarding por domínio.
- `docs/PROJECT_STATUS_LOG.md` — histórico completo de CRs e log
  cronológico.
- `docs/DEVELOPMENT_PROCESS.md` — processo de engenharia (fluxo de CR).
- `docs/REFERENCE_CORPUS.md` — corpus de benchmark.
- `docs/CURRENT_REFERENCE_SNAPSHOT.md` — última medição oficial.
- `nuvem/REGRAS_MODULACAO_BLOCOS.md` — regras técnicas de modulação e
  amarração (fonte de domínio, não duplicada aqui).
