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
SHA:    789f44227145ecc681c714fb952e10dd1de507d9
```

Último marco de PRODUÇÃO: `PR #12` / `CR-BLOCK-ARM-ROLE-CANDIDATE-
SAFETY-CONTRACT` ("SAFE REPAIR ativado") — detalhes completos em
`docs/BLOCK_ARM_ROLE_CANDIDATE_SAFETY_CONTRACT.md`. Desde então só
merges **docs-only** (`PR #13` onboarding; `PR #14` snapshot refresh;
`PR #15` Gate-Fidelity spec; `PR #16` evidência de domínio B19) — todos
com diff de produção declarado ZERO. `nuvem/core/**`,
`nuvem/benchmark/**` (código/validators), `tests/**` e todo
`baseline.json`/`reference.json` seguem idênticos ao estado do `PR
#12`. Histórico anterior completo: `docs/PROJECT_STATUS_LOG.md`.

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

Detalhe técnico de cada um: `docs/PROJECT_STATUS_LOG.md`.

## Trabalho ativo

- **CR-BLOCK-NODE-FILL-REVALIDATION** (`PR #17`, branch
  `claude/cr-block-node-fill-revalidation-iahuyg`, **open/draft, não
  mergeado**, `mergeable_state: clean`) — metade simétrica da junta
  NÓ|FILL: a Fiada A passa a desencontrar da junta de nó da Fiada B
  (`wall_stepper.py`, `NODE_FILL_OPPOSITE_COURSE_ENABLED`). Medido
  contra a base de medição `68a62693` — produção equivalente à `main`
  atual (só `PR #14`/`#15`/`#16`, docs-only, entraram depois; ver
  "Main atual" acima), medições continuam válidas sem remedição:
  `PRISM_CONTINUOUS_JOINT` TGD 444→336, TP1 576→272, piloto 0→0;
  cobertura, aberturas, colisões, junções e ARM accepted/rejected com
  delta zero; 0 conflitos com o Reference Corpus humano. Relatório e
  gates: `docs/BLOCK_NODE_FILL_REVALIDATION.md`; regras: seção 33 de
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`. Aguarda autorização de merge; sem
  monitoramento automático.

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
  (7 no TGD, 3 no TP1) — fora de escopo daquela CR; diagnosticadas em
  `docs/BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md`. Spec de preimplementação
  para 2 dos gates (compensador agregado por banda, cobertura local
  cega a crédito de nó) pronta em
  `docs/BLOCK_ARM_SAFE_REPAIR_GATE_FIDELITY_SPEC.md`
  (`CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY-PREIMPLEMENTATION`,
  READY_FOR_IMPLEMENTATION_AFTER_NODE_FILL) — implementação aguarda
  `CR-BLOCK-NODE-FILL-JOINT` mesclar primeiro.
- **Pareamento `(474, 2306)`** — eixo espúrio de ~43,9 m continua no
  resultado; sem CR atribuído.
- **Regra do meio-bloco (B19) perto de amarração** — evidência de domínio
  coletada (`docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md`): a regra atual
  estrita diverge do corpus humano em 259 ocorrências (TP1); proposta de
  flexibilização mínima aguarda `REQUIRES_HUMAN_DOMAIN_APPROVAL`. Regra
  **não alterada**.
- **Detector de espessuras da UI** amostra só as primeiras 900 linhas
  cruas do layer — não limita o solver real, mas pode ocultar espessuras
  raras na sugestão da tela. Dívida de UX, não corrigida por decisão
  explícita do usuário.
- **Teste visual INTEGRADO completo no Revit** (extração → paredes
  criadas → inspeção visual) — adiado por decisão do usuário; retomar
  quando priorizado.

Detalhe/causa-raiz de cada item: `docs/PROJECT_STATUS_LOG.md`.

## Próximos passos

1. Aguardar autorização/priorização do usuário para o próximo CR de
   engine (candidatos: `CR-BLOCK-DETERMINISM`, alinhamento cross-band,
   compensadores/pastilhas, arestas rejeitadas do SAFETY-CONTRACT).
2. `NODE-FILL` — revalidado em `CR-BLOCK-NODE-FILL-REVALIDATION` (PR
   draft); merge só com autorização explícita. Pendência registrada
   (33.5): o reparo local junto ao vão ainda recria a junta 34,5 em
   `W036`/`W038` (TP1, bandas com janela).
3. Teste visual integrado no Revit — retomar quando o usuário priorizar.

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
