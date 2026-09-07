# ROADMAP PÓS-C04 — fila, dependências e decisões humanas

> **Documento de PREPARAÇÃO.** Diff de produção = ZERO. Nenhuma CR abaixo
> foi iniciada. Nenhuma regra normativa alterada — `nuvem/REGRAS_MODULACAO_
> BLOCOS.md` intocado (a seção 35 vigente é a do PR #19, **não** a do
> Atlas).
>
> Base: `main` = `3ebcd9b63875f9114a3d6223aa648e5075e2d35b`. O C04
> (PR #20) **não está mesclado**; onde a base futura é necessária, o texto
> usa o placeholder **`<BASE_POS_C04>`** — nenhuma SHA futura foi
> inventada.
>
> Complementa, **sem duplicar**, `docs/FUTURE_BLOCK_CR_PREPARATION.md` e
> `docs/FUTURE_BLOCK_CR_PROMPTS.md` (branch
> `claude/c04-review-next-cr-prep-wc77d7` @ `54caff7`).

---

## 1. O que mudou desde a preparação anterior

A investigação desta sessão (`nuvem/benchmark/future_cr_preparation/
bench_opening_reconstruction/`) elevou a CR de benchmark de "suspeita forte"
para **causa-raiz localizada com evidência medida**:

| antes | agora |
|---|---|
| "195 achados de 15,0cm no gabarito são assinatura de artefato" | causa-raiz na linha: `detect_wall_openings_from_courses` agrega o vão pela **união** dos vazios por fiada, com tolerância de 15,0cm — a tolerância de *identidade* vaza para a *geometria* |
| impacto desconhecido | **168 → 0** `OPENING_BLOCK_CROSSES_JAMB` no solver do TP1; **−158 erros críticos** |
| "provável offset de jamba" | **16 de 19** consensos coincidem, no TGD, com o **buraco entre duas paredes MEDIDAS** do Revit — não é vão, é fusão indevida de paredes |

Consequência para a fila: a #1 continua sendo a CR de benchmark, e agora
com escopo mais claro — e **maior**, porque toca `opening_audit.py`, que é
**produção**.

---

## 2. Fila recomendada

| # | CR | impacto | risco | confiança | decisão humana | paralelizável | toca produção | depende de `main` pós-C04 | custo aprox. de validação |
|---|---|---|---|---|---|---|---|---|---|
| **1a** | `BENCH-OPENING-RECONSTRUCTION-A` (detector) | **alto** — destrava a métrica de abertura | médio (é produção) | **alta** — causa na linha | não | sim | **sim** (`opening_audit.py`) | não | 3 projetos × STATE_A/B + suíte ≈ 1h30 |
| **1b** | `BENCH-OPENING-RECONSTRUCTION-B` (gabarito) | alto | **alto** — muda a régua | alta | **SIM** — ver §4 | não (depende de 1a) | não | não | recalibração + comparação ≈ 1h |
| **2** | `CR-BLOCK-ROOM-CHECK-ROBUSTNESS` (C02) | **alto** (~1234 amarrações) | médio (mexe em amarração) | alta (causa localizada) | não | não | sim | **sim** | STATE_A/B + invariâncias ≈ 2h |
| **3** | `CR-BLOCK-JUNCTION-NODE-COVERAGE` | médio (9 TP1 + até 23 TGD) | médio | alta (`t_cm = −8,0`) | não | não | sim | **sim** | ≈ 1h30 |
| **4** | `CR-BLOCK-REPAIR-ANCHOR-JOINT` (C10) | médio (−16 críticos) | médio | média | não | **não** — mesmo call site do C04 | sim | **sim, obrigatório** | ≈ 1h30 |
| **5** | `S1` / `S2` — política de composição | **alto** | alto | **baixa** | **SIM** — Q1–Q4 | não | sim | sim | ≈ 2h + validação humana |
| **6** | `CR-BLOCK-ARM-PERFORMANCE` | zero em qualidade | baixo | alta | não | **sim** | sim | não | fingerprint idêntico ≈ 1h |
| **7** | `BENCH-BASELINE-REFRESH` | zero | baixo | alta | **SIM** | **sim** | não | **sim** (só depois do C04) | ≈ 30min |
| **8** | `BENCH-WALLMODEL-FRAGMENTS` | médio | médio | baixa | não | **sim** | não (diagnóstico) | não | ≈ 1h |

### Por que esta ordem

- **#1 primeiro** porque hoje `OPENING_BLOCK_CROSSES_JAMB` **em valor
  absoluto** não é utilizável (o gabarito o viola 208/209×) e o defeito
  chega ao **solver** do TP1, não só à métrica. Toda CR que mexe em
  abertura ou junção fica com gate de baixa qualidade até isso ser
  resolvido.
- **#1a antes de #1b**: corrigir o gabarito com o detector ainda defeituoso
  só reintroduziria o erro na próxima extração.
- **#2 antes de #3/#4** pela razão impacto/risco: causa localizada, número
  medido (1234), e o padrão de correção (tolerância dedicada e separada, sem
  alargar tolerância global) já foi validado pelo próprio C04.
- **#4 obrigatoriamente depois do C04** — mesmo call site
  (`_solve_repair_subsegments`): em paralelo dá conflito garantido.
- **#5 por último entre as de produção** porque depende de Q1–Q4 e é a
  única que pode exigir mudança em `REGRAS_MODULACAO_BLOCOS.md`.
- **#6, #7, #8 paralelizáveis**: #6 tem fingerprint idêntico como critério
  de aceitação, #7 e #8 não tocam produção.

### O que pode mudar esta ordem

1. **Se #1a mostrar que o detector afeta o solver ao vivo** (não só o
   benchmark), ela vira uma CR de produção de risco médio-alto e pode ter de
   ceder a vez para #2.
2. **Depois de #1b**, os números de `COVERAGE_*` mudam nos dois projetos —
   o snapshot pós-C04 precisa ser refeito **antes** de #2/#3/#4 usarem
   cobertura como gate.
3. **Se C1/C2 forem recusadas** (Opção B da seção 7 de
   `docs/PR20_INTEGRATION_READINESS.md`), #5 sobe para a frente de #2, e o
   C04 fica bloqueado até lá.

---

## 3. Plano de execução em sessões

Cada CR mantém **branch própria, `STATE_A`/`STATE_B` próprios, diff
próprio, testes próprios, PR próprio, revisão independente e autorização de
merge separada**. Uma sessão longa pode executar várias em sequência, mas
**nunca** misturar mudanças de produção de CRs diferentes no mesmo commit.

| sessão | conteúdo | pré-requisito |
|---|---|---|
| **A** | `BENCH-OPENING-RECONSTRUCTION-A` → evidência já pronta → correção do detector → STATE_A/B → PR draft → revisão | nenhum (pode rodar antes do merge do C04) |
| **A′** | `BENCH-OPENING-RECONSTRUCTION-B` → gabarito candidato → comparação → **decisão de referência do usuário** | A mesclada + autorização explícita para alterar gabarito |
| **B** | `C02` → STATE_A → implementação → STATE_B → invariâncias (translação/rotação/reversão/espelho) → PR draft | `<BASE_POS_C04>` |
| **C** | `JUNCTION-NODE-COVERAGE` e depois `C10`, **serialmente** (ambas em `wall_stepper.py`) | B mesclada |
| **D** | `S1`/`S2` | respostas Q1–Q4 |
| **E** | `ARM-PERFORMANCE` | pode rodar em paralelo a qualquer uma |

---

## 4. Decisões de domínio pendentes — Q1 a Q4

> **Nada aqui é regra.** Estas perguntas existem para o usuário responder.
> Nenhuma observação foi promovida a regra obrigatória. Contexto medido
> completo: `docs/FUTURE_BLOCK_CR_PREPARATION.md` §20 @ `54caff7`.

As quatro camadas, sempre separadas: **REGRA ATUAL APROVADA** ×
**PADRÃO HUMANO OBSERVADO** × **CONFLITO** × **HIPÓTESE** ×
**DECISÃO PENDENTE**.

### Q1 — parede curta e reserva de pior caso
*(`SHORT_WALL_NODE_POLICY`)*

- **Regra vigente:** em parede curta, a reserva de pior caso mantém 6
  arestas de amarração corretamente **rejeitadas**.
- **Evidência humana:** não coletada especificamente para parede curta.
- **Conflito registrado:** nenhum.
- **Hipótese:** a reserva pode ser conservadora demais, do mesmo jeito que o
  ramo fim-de-região da guarda do C04 é (C3).

> **Em português claro:** hoje, quando a parede é curta, o programa
> **desiste** de colocar a peça de amarração porque *presume* que não vai
> caber. A pergunta é se ele pode passar a **medir a folga real** antes de
> desistir.
>
> **Se SIM:** aparecem amarrações onde hoje não há. Se a medição estiver
> errada em algum caso, duas peças podem se sobrepor — e amarração é o
> núcleo estrutural do sistema.
> **Se NÃO:** as 6 arestas continuam rejeitadas, sem risco novo.

**Q1 — `[SIM / NÃO / SÓ COM MEDIÇÃO NO REVIT]`**

### Q2 — meio-bloco × par de compensadores
*(`FILL_RESIDUE_BETWEEN_TIES`)*

- **Regra vigente:** o resíduo entre amarrações é preenchido pelo catálogo
  comum, sem preferência explícita.
- **Evidência humana (medida):** humano `W016` fiada 0 usa **um B19** em
  15–34; o solver (STATE_C do C04) usa **C09 + C04** no mesmo espaço.
- **Conflito:** o solver prefere 2 compensadores onde o humano usa 1
  meio-bloco.
- **Hipótese:** falta preferência explícita por meio-bloco quando os dois
  cabem.

> **Em português claro:** num vão de 19cm entre duas amarrações, o
> projetista põe **um meio-bloco**. O programa põe **duas pecinhas de
> acerto**, que ficam mais feias e mais caras de assentar. É exatamente o
> que faz o número de compensadores do TGD subir (C1).
>
> **Se SIM:** o desenho fica mais parecido com o humano e C1 melhora.
> **Se NÃO:** C1 continua como está.

**Q2 — `[SIM / NÃO / DEPENDE — especificar]`**

### Q3 — B19 residual perto de nó
*(seção 35 vigente, PR #19)*

- **Regra vigente:** o B19 fecha resíduo de 15–20cm **só** com amarração
  real íntegra no **MESMO nó e MESMA fiada**. Medido: **0 candidatos
  aceitos** no corpus.
- **Evidência humana:** `docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md`.
- **Conflito registrado:** o Atlas antigo (`9834b40`) escreveu uma seção 35
  que **conflita** com a do PR #19 já integrada na `main`. **A vigente é a
  do PR #19.**
- **Hipótese:** a condição "mesma fiada" pode ser restritiva demais —
  **0/102 fiadas** medidas a satisfazem.

> **Em português claro:** o mecanismo existe, foi testado, e **nunca é
> acionado**: a condição é tão estrita que nenhum caso real passa. A
> pergunta é se basta a amarração existir **no mesmo nó, em qualquer
> fiada**.
>
> **Se SIM:** o B19 passa a fechar resíduos que hoje ficam vazios.
> **Se MANTER ESTRITA:** o mecanismo segue correto e sem efeito prático.

**Q3 — `[SIM / NÃO / MANTER ESTRITA]`**

### Q4 — teto de compensadores por fiada

- **Regra vigente:** B34/B54 são peças de amarração; usá-las como fill não
  está explicitamente proibido; não há teto de compensadores.
- **Evidência humana:** humano `W010` usa B34/B39 como fill corrente
  (10–11 peças/fiada).
- **Conflito:** TP1 `W012` — o solver produz **109 compensadores** contra
  **18** do humano.
- **Hipótese:** a função de custo do DP não penaliza compensador o
  suficiente.

> **Em português claro:** numa mesma parede, o humano usa 18 pecinhas de
> acerto e o programa usa 109. A pergunta é se deve existir um **limite**
> (ou uma penalidade forte), **mesmo que isso deixe pedaço de parede sem
> preencher**.
>
> **Se SIM (com teto):** o desenho fica mais limpo, mas volta a ter vazios —
> exatamente o que o C04 acabou de eliminar.
> **Se PENALIDADE SEM TETO:** o programa evita compensador quando existe
> alternativa, mas nunca deixa vazio por causa disso. É o meio-termo.

**Q4 — `[SIM — qual teto / NÃO / PENALIDADE SEM TETO]`**

---

## 5. Fichas de execução dos prompts

Os **9 prompts prontos** estão em `docs/FUTURE_BLOCK_CR_PROMPTS.md`
(@ `54caff7`) e **não foram duplicados aqui**. O que faltava neles era a
ficha operacional; é o que esta tabela acrescenta.

| # | prompt | agente | raciocínio | sessão | MCP Revit | base | revisão independente |
|---|---|---|---|---|---|---|---|
| 1 | `BENCH-OPENING-RECONSTRUCTION` | implementador | **alto** | **nova** | não | `<BASE_POS_C04>` ou `main` atual | **obrigatória** (é produção: `opening_audit.py`) |
| 2 | `C02` room check | implementador | **alto** | nova | **sim, se houver dúvida de folga física** | `<BASE_POS_C04>` | **obrigatória** (mexe em amarração) |
| 3 | `JUNCTION-NODE-COVERAGE` | implementador | **alto** | nova | **sim** (medir o nó `t_cm = −8,0`) | `<BASE_POS_C04>` | **obrigatória** |
| 4 | `C10` repair anchor joint | implementador | médio | nova | não | `<BASE_POS_C04>` | obrigatória |
| 5 | `S1` política de composição | implementador | **alto** | nova | não | `<BASE_POS_C04>` | **obrigatória** + Q1 respondida |
| 6 | `S2` resíduo entre amarrações | implementador | médio | nova | não | `<BASE_POS_C04>` | obrigatória + Q2/Q4 respondidas |
| 7 | `ARM-PERFORMANCE` | implementador | médio | nova | não | qualquer | obrigatória (critério: fingerprint idêntico) |
| 8 | `BENCH-WALLMODEL-FRAGMENTS` | diagnóstico | médio | nova | não | qualquer | dispensável (não toca produção) |
| 9 | `BENCH-BASELINE-REFRESH` | diagnóstico | baixo | nova | não | `<BASE_POS_C04>` | dispensável, **mas exige decisão do usuário** |

**Regras que valem para os nove, sem exceção:**

- worktree isolado obrigatório; nunca trabalhar direto no diretório
  principal;
- `STATE_A` medido **antes** de qualquer alteração; `STATE_B` medido depois;
- comparação por **identidade geométrica**, nunca só por contagem — o
  rótulo sequencial `W…-R…-B…` renumera quando entra peça na fiada e produz
  falso "novo";
- determinismo verificado em **2 processos novos**;
- PR em **draft**; **sem merge automático**; sem marcar ready;
- `baseline.json` / `reference.json` / `input.json` / `reference_score.json`
  **intocados** salvo CR de benchmark com autorização específica;
- proibido reduzir validação, pular teste ou marcar `xfail`/`skip` para
  ficar verde;
- proibido criar check-in horário, monitoramento de PR, polling ou tarefa
  recorrente;
- toda regra nova de modulação/amarração vai para
  `nuvem/REGRAS_MODULACAO_BLOCOS.md` (regra do `CLAUDE.md`);
- **não preencher `<BASE_POS_C04>` antes de existir merge real.**

---

## 6. Specs futuras — o que já está fixado

| CR | causa-raiz | proibições específicas |
|---|---|---|
| **C02** | nós X borderline degradam B54 → B34 por faltar **0,003–0,02cm** do teto de 28,00cm (`half_len 27,0 + junta 1,0`). ~1234 colocações afetadas | **não** transformar 0,003–0,02cm em tolerância global; **não** reusar `PIER_FIT_TOLERANCE_CM` (0,30cm) aqui — cederia 30% da junta de amarração; constante **dedicada** (`ROOM_CHECK_NOISE_TOLERANCE_CM`, candidato 0,05cm), que deliberadamente **não** recupera o caso de 27,9cm (fica para decisão humana) |
| **JUNCTION-NODE-COVERAGE** | TP1 `W039`/`W041`: o ponto físico do nó fica em **`t_cm = −8,0`** no eixo de `W041` — 8cm **antes** do início do eixo. Assimétrico entre participantes: um vê `t` dentro, o outro vê negativo | **não** criar hack por `W039`/`W041`; **não** assumir que B19 substitui peça de amarração (**B19 é FILL, nunca TIE**); separar geometria de entrada × cobertura física do nó × papel estrutural × alternância de fiadas × crédito de parede participante × composição residual |
| **C10** | `recut opening` → `repair` → recria junta da família oposta em `t = 34,5cm`; TP1 `W036`/`W038` e equivalentes, 20 achados confirmados | **não** relaxar `PRISM_CONTINUOUS_JOINT`; **não** tratar como exceção de domínio; implementar **depois** do C04 (mesmo call site) |
| **ARM-PERFORMANCE** | **94%** do tempo cumulativo no ARM; **22 rebuilds** completos a ~7,94s cada. Folhas quentes: `_exact_fill_blocks` (20,5s), `_wall_junction_ts_ft` (13,0s), `_obb_corners`/`_obb_aabb` | **proibido** reduzir validação física para ganhar velocidade; **proibido** mudar política de amarração; critério de aceitação é **fingerprint bit-a-bit idêntico** + `accepted`/`rejected` do ARM idênticos por identidade. **Não** repetir perfilamento longo — os números acima já foram medidos |
| **BENCH-OPENING-RECONSTRUCTION** | ver `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction/CR_SPEC.md` | **não** usar o resultado do solver como gabarito; **não** encurtar vão sem evidência de proveniência própria; alterar gabarito **exige autorização humana específica** |

---

## 7. Correções aos prompts já produzidos

Auditoria de coerência dos 9 prompts de `docs/FUTURE_BLOCK_CR_PROMPTS.md`
(@ `54caff7`) contra o que esta sessão mediu. **Oito continuam corretos.**
Um precisa de correção:

### `PROMPT 1 — BENCH-OPENING-RECONSTRUCTION`

O prompt manda **"achar de onde sai o offset de 15,0cm em
`extract/reconstruct.py` (candidatos: recuo padrão de jamba, meio bloco,
espessura/2)"**. Isso está **superado** e mandaria a próxima sessão procurar
no arquivo errado, atrás de um mecanismo que não existe:

| o que o prompt supunha | o que foi medido |
|---|---|
| um **offset** de 15,0cm aplicado à jamba | **não há offset**: o vão gravado é o **envelope** (união) dos vazios por fiada |
| em `nuvem/benchmark/extract/reconstruct.py` | em `nuvem/core/engine/opening_audit.py::detect_wall_openings_from_courses` (l. 155-165) — que é **produção**, não benchmark |
| origem: recuo de jamba / meio bloco / espessura/2 | origem: `OPENING_RUN_EDGE_MATCH_TOLERANCE_CM = 15,0` usada como *tolerância de identidade* e vazando para a *geometria*; o valor coincide com `B34 − B19 = 15cm`, a alternância do dente de amarração |
| escopo declarado "SÓ BENCHMARK, diff de produção = ZERO" | **impossível manter**: corrigir o detector é mudar produção. Por isso a CR foi partida em **A (detector)** e **B (gabarito)** |
| "as 195 ocorrências de 15,0cm devem desaparecer OU ser provadas reais" | já demonstrado: com o consenso, **195 → 0** no gabarito e **168 → 0** no solver do TP1 — mas ao custo de **+22** `COVERAGE_GAP_IN_ROW` no gabarito e **+90** no solver, porque a correção definitiva provavelmente é **separar a parede**, não estreitar o vão |

**Prompt 1 substituído por:** `nuvem/benchmark/future_cr_preparation/
bench_opening_reconstruction/CR_SPEC.md`, que já traz causa-raiz, evidência,
metodologia, regras de proveniência, testes, hard gates, risco, critério de
aprovação humana e estratégia de versionamento/baseline.

### Os outros oito

| prompt | veredito |
|---|---|
| 2 `C02` | coerente — a faixa 0,003–0,02cm e o teto de 28,00cm foram confirmados; mantida a proibição de reusar `PIER_FIT_TOLERANCE_CM` |
| 3 `JUNCTION-NODE-COVERAGE` | coerente — `t_cm = −8,0` confirmado; independe do desfecho do PR #20 |
| 4 `C10` | coerente — **acrescentar** que depende do C04 mesclado (mesmo call site), já explícito na §2 deste roadmap |
| 5 `S1` / 6 `S2` | coerentes — **acrescentar** que Q1–Q4 continuam **sem resposta** e que C1/C2 do PR #20 alimentam diretamente Q2 e Q4 |
| 7 `ARM-PERFORMANCE` | coerente — os números de perfilamento já estão medidos; **não** repetir o perfilamento longo |
| 8 `BENCH-WALLMODEL-FRAGMENTS` | coerente — e ganha relevância: a fusão indevida de paredes encontrada na §1 é da mesma família |
| 9 `BENCH-BASELINE-REFRESH` | coerente — **reforçar**: não regravar `baseline.json` enquanto o PR #20 estiver em avaliação, sob pena de esconder C1 |
