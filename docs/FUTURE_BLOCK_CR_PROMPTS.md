# PROMPTS PRONTOS — PRÓXIMAS CRs DE BLOCOS

> **Não executar nada disto na sessão que gerou este arquivo.**
>
> Cada prompt é autocontido e pronto para colar numa sessão nova.
> Todos usam o placeholder **`<BASE_POS_C04>`** para a base — **nenhuma
> SHA futura foi inventada**. Substituir por `git rev-parse origin/main`
> no momento de abrir a CR.
>
> Contexto medido que fundamenta cada prompt:
> `docs/FUTURE_BLOCK_CR_PREPARATION.md`.
> Método de revisão de referência: `docs/C04_INDEPENDENT_FINAL_REVIEW.md`.

---

## PREÂMBULO COMUM (vale para TODOS os prompts)

```
REGRAS PERMANENTES DESTA SESSÃO

Responder sempre em português do Brasil.

BASE: <BASE_POS_C04>   (main pós-C04; confirmar com git rev-parse origin/main
                        e PARAR se divergir do que o usuário informou)

WORKTREE ISOLADO obrigatório: git worktree add --detach <dir> <BASE_POS_C04>
Nunca trabalhar direto no diretório principal.

PROIBIDO:
- mergear na main (revogado o "ok" permanente; exige autorização explícita
  PARA AQUELE merge);
- marcar PR como ready;
- alterar nuvem/REGRAS_MODULACAO_BLOCOS.md sem aprovação explícita;
- alterar baseline.json / reference.json / input.json;
- criar check-in horário, monitoramento de PR, polling ou tarefa recorrente;
- reduzir validação para fazer teste passar.

OBRIGATÓRIO:
- STATE_A medido ANTES de qualquer alteração;
- comparação por IDENTIDADE GEOMÉTRICA, nunca só por contagem
  (normalizar o rótulo sequencial W...-R...-B..., que muda quando uma peça
   entra antes na fiada e produz falsos "novos");
- determinismo verificado em 2 processos NOVOS;
- PR em DRAFT;
- toda regra nova de modulação/amarração registrada em
  nuvem/REGRAS_MODULACAO_BLOCOS.md (regra do CLAUDE.md).
```

---

## PROMPT 1 — `BENCH-OPENING-RECONSTRUCTION`

```
CR: BENCH-OPENING-RECONSTRUCTION
Branch: claude/bench-opening-reconstruction-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

PROBLEMA (medido, não suposto)
Rodando os validadores sobre o PRÓPRIO GABARITO HUMANO:
  TGD: OPENING_BLOCK_CROSSES_JAMB = 208
  TP1: OPENING_BLOCK_CROSSES_JAMB = 209
Distribuição nos DOIS projetos: 195 casos em EXATAMENTE 15,0cm,
mais 13-14 casos em <= 0,3cm.

195 ocorrências de um valor redondo idêntico em dois projetos distintos é
assinatura de ARTEFATO DE RECONSTRUÇÃO, não de alvenaria real.
Consequência: o gate OPENING_BLOCK_CROSSES_JAMB em valor ABSOLUTO é hoje
inutilizável; só o delta por identidade é confiável.

ESCOPO — SÓ BENCHMARK. DIFF DE PRODUÇÃO = ZERO.
Permitido: nuvem/benchmark/extract/**, validators, reference_score.json
           (recalibração), documentação.
Proibido:  nuvem/core/**, REGRAS_MODULACAO_BLOCOS.md, baseline.json,
           input.json, reference.json sem aprovação explícita.

STATE_A
Rodar --calibrate nos 3 projetos e guardar a distribuição por magnitude.

INVESTIGAÇÃO
1. Achar de onde sai o offset de 15,0cm em extract/reconstruct.py
   (candidatos: recuo padrão de jamba, meio bloco, espessura/2).
2. Determinar se o erro está no input.json (posição da abertura) ou no
   reference.json (posição das peças).
3. Minimal repro: UMA abertura, UMA fiada, mostrando os 15,0cm.

IMPLEMENTAÇÃO MÍNIMA
Corrigir a reconstrução. Recalibrar reference_score.json.
NÃO alterar produção. NÃO regravar baseline.json.

HARD GATES
- diff de produção = ZERO (verificar com git diff --stat);
- fingerprint físico do solver IDÊNTICO nos 3 projetos antes/depois
  (o benchmark não pode mudar o que o solver produz);
- as 195 ocorrências de 15,0cm devem desaparecer OU ser provadas reais;
- os 13-14 casos <= 0,3cm devem ser classificados separadamente.

VALIDAÇÃO HUMANA
Escolher 3 aberturas e conferir peça a peça contra o gabarito.

TESTES
Teste que trava a reconstrução da jamba (falha antes, passa depois).

BASELINE STRATEGY
Recalibrar SÓ reference_score.json. baseline.json intocado.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 2 — `CR-BLOCK-ROOM-CHECK-ROBUSTNESS` (C02)

```
CR: CR-BLOCK-ROOM-CHECK-ROBUSTNESS
Branch: claude/cr-block-room-check-robustness-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

PROBLEMA (medido instrumentando a função REAL de produção)
Teto atual em _x_intersection_centered_candidate (wall_stepper.py):
    half_len_ft + BLOCK_JOINT_CM(em ft) <= room_ft
Para o B54: 27,0 + 1,0 = 28,00cm de folga exigida em CADA sentido.

Folga real medida em TODAS as avaliações de nó X:
  TGD  2024 avaliações -> room_cm distintos {0,0 ; 27,997}
                          184 casos a 27,997cm  (falta 0,003cm) -> degrada B54->B34
  TP1  1350 avaliações -> {17,0 ; 27,9 ; 27,98 ; 27,99}
                          1050 casos -> degrada B54->B34
  Piloto 4 avaliações  -> {7,0}  (insuficiência real, degradar está certo)

~1234 colocações de AMARRAÇÃO degradam por faltar 0,003-0,02cm.
Mesma família de ruído que o C04 corrigiu para o fit modular, agora no
caminho mais crítico do sistema.

ARGUMENTO FÍSICO
room_ft mede até a BORDA do obstáculo e o teste JÁ desconta 1,0cm de
junta. Aceitar 27,997 deixa 0,997cm de junta em vez de 1,000cm — não há
colisão. Mesmo raciocínio validado em C04_INDEPENDENT_FINAL_REVIEW §8.2C.

ESCOPO DE PRODUÇÃO (máximo)
  nuvem/core/engine/wall_stepper.py
Avaliar se T_INTERSECTION e L_CORNER têm o mesmo defeito (compartilham
T_INTERSECTION_B54_HALF_ROOM_FT) — se tiverem, tratar na MESMA CR, mas
medindo cada um separadamente.

STATE_A
3 projetos, fingerprint físico + counts_by_code + critical_by_code +
distribuição completa de room_cm por tipo de nó.

IMPLEMENTAÇÃO MÍNIMA
Constante NOVA e DEDICADA (mesmo padrão do C04, que separou
PIER_FIT_TOLERANCE_CM de PIER_LAYOUT_TOLERANCE_CM):
    ROOM_CHECK_NOISE_TOLERANCE_CM = 0.05     # candidato
    half_len_ft + joint_ft <= room_ft + tol_ft

PROIBIDO reusar PIER_FIT_TOLERANCE_CM (0,30cm) aqui — cederia 30% da
junta de amarração. Contrato diferente.

Documentar no código POR QUE 0,05 e não 0,30, e por que 27,9 (0,1cm)
NÃO é recuperado — fica para decisão humana.

CLASSIFICAÇÃO EXIGIDA (não aceitar todo borderline)
  27,997 / 27,99 / 27,98  -> RUÍDO NUMÉRICO (recuperar)
  27,9                    -> BORDERLINE (NÃO recuperar; perguntar)
  17,0 / 7,0 / 0,0        -> GEOMETRIA INSUFICIENTE (manter degradação)

HARD GATES
- POSITION_OVERLAP: 0 novas por identidade  <- o gate que pega B54 colidindo
- JUNCTION_MISSING_BINDING: não pode subir
- JUNCTION_NOT_ALTERNATING: 0 novas
- OPENING_BLOCK_CROSSES_JAMB: 0 novas
- COVERAGE_*: sem regressão líquida
- Piloto: fingerprint físico IDÊNTICO
- contar explicitamente quantos B34 -> B54 foram recuperados

INVARIÂNCIA (obrigatória)
translation, rotation, endpoint reversal, mirror: a folga medida tem de
ser IDÊNTICA nas quatro. Se não for, o bug é na MEDIÇÃO, não no teto —
nesse caso PARAR e reportar.

VALIDAÇÃO HUMANA
Nos nós recuperados que tenham parede correspondente no gabarito,
conferir se o humano usa B54.

TESTES
- teste de unidade do teto com 27,997 / 27,99 / 27,98 / 27,9 / 17,0;
- teste de invariância nas 4 transformações;
- regressão de POSITION_OVERLAP.

BASELINE STRATEGY
NÃO regravar baseline.json. Classificar as falhas de --check
explicitamente: novas, pré-existentes, ou exposição.

REGRAS
Registrar a regra do teto de folga de amarração em
nuvem/REGRAS_MODULACAO_BLOCOS.md — é conhecimento de AMARRAÇÃO, registro
OBRIGATÓRIO (CLAUDE.md), com rótulo de confiança e como foi medido.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 3 — `CR-BLOCK-JUNCTION-NODE-COVERAGE`

```
CR: CR-BLOCK-JUNCTION-NODE-COVERAGE
Branch: claude/cr-block-junction-node-coverage-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

PROBLEMA — CAUSA-RAIZ JÁ LOCALIZADA
TP1: TODAS as 9 ocorrências de JUNCTION_MISSING_BINDING estão no MESMO nó,
o L entre W039 e W041 em (6184.25, 949.95):

  W039: start=[5800.25,949.95] end=[6184.25,949.95] len=384.0
        nó L t_cm = 384.0   at_end=True     <- na ponta do eixo
  W041: start=[6177.25,957.95] end=[6177.25,1466.95] len=509.0
        nó L t_cm = -8.0    at_end=True     <- 8cm FORA do eixo

t_cm NEGATIVO: o ponto físico do nó fica 8cm ANTES do início do eixo de
W041. Qualquer lógica que posicione a peça por t e recorte para
[0, length] perde o nó nesse participante.
Achado: "encontro L em (6177.2, 950.0) sem nenhuma peça na fiada N -
paredes W039, W041", em 9 de 17 fiadas.

Confirmado idêntico em STATE_A e no STATE_C do C04 -> independe do C04.

NÃO FAZER HACK POR W039/W041. O defeito é estrutural (nó assimétrico
entre participantes); essas paredes são só a instância que o corpus expõe.

ESCOPO DE PRODUÇÃO (máximo)
  nuvem/core/engine/wall_stepper.py
  nuvem/core/engine/wall_pairing.py   (só se a causa for a construção do nó)

ESTRATÉGIAS A COMPARAR (obrigatório comparar, não escolher direto)
  node ownership            - dono é o participante cujo t está no eixo
  node extension            - estender o eixo até o ponto (ALTO RISCO:
                              muda length_cm e propaga para a modulação)
  alternate corner candidate
  participant coverage      - crédito FÍSICO (precedente: PR #18)
  B19 closure               - PROIBIDO. B19 é FILL, nunca TIE.

Recomendação preliminar da preparação: node ownership + participant
coverage (ambas com precedente aprovado, nenhuma altera geometria de
entrada). Justificar a escolha final com medição.

MINIMAL REPRO
Duas paredes em L cujo ponto do nó caia FORA do eixo de uma delas
(t_cm negativo), 17 fiadas. Critério: JUNCTION_MISSING_BINDING > 0.

CRITÉRIOS FÍSICOS DE ACEITAÇÃO
1. ponto físico do nó geometricamente coberto por peça REAL de amarração
   em todas as fiadas onde a regra exige;
2. POSITION_OVERLAP: 0 novas (a peça não pode invadir a perpendicular);
3. TP1 JUNCTION_MISSING_BINDING: 9 -> 0;
4. JUNCTION_NOT_ALTERNATING não sobe;
5. TGD JUNCTION_MISSING_BINDING (=23): medir. Se for o mesmo padrão, deve
   cair junto; se não cair, INVESTIGAR antes de fechar a CR.

HARD GATES
OPENING_BLOCK_CROSSES_JAMB / POSITION_OVERLAP / COVERAGE_*: 0 novas por
identidade. Piloto: fingerprint IDÊNTICO. Determinismo em 2 processos.

REGRAS
Conhecimento de AMARRAÇÃO -> registro OBRIGATÓRIO em
nuvem/REGRAS_MODULACAO_BLOCOS.md, com rótulo de confiança, como foi
medido, e marcando pendência de código se não implementado.
NÃO criar exceção de domínio sem aprovação explícita do usuário.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 4 — `CR-BLOCK-REPAIR-ANCHOR-JOINT` (C10)

```
CR: CR-BLOCK-REPAIR-ANCHOR-JOINT
Branch: claude/cr-block-repair-anchor-joint-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

DEPENDÊNCIA DURA: implementar SOMENTE depois do C04 mesclado. Toca o
mesmo call site (_solve_repair_subsegments). Em paralelo = conflito certo.

PROBLEMA (medido)
TP1, W036 e W038 (gêmeas: 524,0cm, janelas em t=69-200 e t=324-455, T nos
dois extremos):
  PRISM_CONTINUOUS_JOINT  8 + 8   -> TODAS em t = 34,5cm
  PRISM_JOINT_STACK       1 + 1   -> a junta se repete na coluna inteira
  COMPENSATOR_EXCESS_IN_RUN 18+18, COMPENSATOR_CONSECUTIVE 14+14

t=34,5 é o centro da junta logo após a peça B34 que vai de t=0 (nó T) a
t=34. Idêntico em STATE_A e STATE_C do C04.

CAUSA CONHECIDA (confirmar, não assumir)
recut -> reparo local -> a região é remontada da esquerda para a direita
-> a primeira peça depois da âncora de nó cai no mesmo lugar nas DUAS
fiadas -> junta da família oposta recriada.
O reparo local não herda a restrição de desencontro
(avoid_joint_positions_cm) que o solver principal aplica.
Pendência já registrada como 33.5 / NODE-FILL em docs/PROJECT_STATUS.md.

MINIMAL REPRO
parede reta 524,0cm, espessura 14, nó T em t=0 e t=524,
janela 1 t=69..200, janela 2 t=324..455, 17 fiadas.
Critério: PRISM_CONTINUOUS_JOINT em t=34,5.

FIRST DIVERGENCE (obrigatório localizar antes de alterar código)
1. instrumentar _solve_repair_subsegments e registrar, por fiada, o
   avoid_joint_positions_cm REALMENTE recebido;
2. comparar com o que _pier_layout_avoiding_joints recebe para a mesma
   parede/fiada no solver principal;
3. divergência esperada: o reparo recebe lista vazia ou incompleta;
4. conferir o valor de prefer_avoiding nesse caminho.

IMPLEMENTAÇÃO MÍNIMA
Propagar ao reparo local a MESMA lista de juntas a evitar que o principal
usa. Sem critério novo. Sem mexer no DP de stagger.
Se a lista já chega e é ignorada, o fix é no consumo.
PROIBIDO relaxar PRISM_CONTINUOUS_JOINT ou criar exceção de domínio.

ESCOPO DE PRODUÇÃO (máximo)
  nuvem/core/engine/wall_stepper.py
  nuvem/core/engine/continuous_modulation.py   (só se a lista nascer lá)

HARD GATES
- PRISM_CONTINUOUS_JOINT DEVE CAIR (alvo: -16 no TP1)
- OPENING_BLOCK_CROSSES_JAMB: 0 novas por identidade
- POSITION_OVERLAP: 0 novas
- JUNCTION_*: 0 novas
- COVERAGE_*: sem regressão líquida
- ATENÇÃO ESPECIAL: não reintroduzir as 41 invasões de jamba que o C04
  eliminou — revalidar explicitamente esse conjunto.
- Piloto: fingerprint IDÊNTICO. Determinismo em 2 processos.

TESTES
reproducer sintético; teste de que o reparo recebe a lista da fiada
oposta; regressão de W036/W038 sem junta em t=34,5.

BASELINE STRATEGY
NÃO regravar baseline.json. Classificar falhas explicitamente.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 5 — `S1` — POLÍTICA DE COMPOSIÇÃO (decisão humana primeiro)

```
CR: CR-BLOCK-COMPOSITION-POLICY-S1  (DECISÃO, não implementação)
Branch: claude/cr-block-composition-policy-s1-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

ESTA CR NÃO IMPLEMENTA NADA ATÉ O USUÁRIO RESPONDER Q1-Q4.

EVIDÊNCIA MEDIDA
Humano W016 (TP1/TGD reference), fiada 0:
    B19 15,0-34,0   <- UM meio-bloco, termina EXATAMENTE na jamba (34,0)
Solver no mesmo espaço (STATE_C do C04):
    C09 15-24 + C04 25-29   <- DOIS compensadores, para 5cm antes

TP1 W012: 109 compensadores contra 18 do humano na mesma parede.
TGD W075: 88 compensadores contra 0 do humano.

PERGUNTAS AO USUÁRIO (fazer ANTES de qualquer código)
Q1 - Em parede curta, a reserva de pior caso pode ser substituída por
     medição da folga física real, aceitando peça de amarração hoje
     rejeitada?  [SIM / NÃO / SÓ COM MEDIÇÃO NO REVIT]
Q2 - Quando um B19 E um par C09+C04 cabem no mesmo resíduo, o solver deve
     SEMPRE preferir o B19 (como o humano)?  [SIM / NÃO / DEPENDE]
Q3 - A condição "amarração real íntegra no MESMO nó e MESMA fiada" do B19
     residual (seção 35 vigente, do PR19) deve ser relaxada para "mesmo
     nó, qualquer fiada"? Medição: 0/102 fiadas satisfazem a estrita.
     [SIM / NÃO / MANTER ESTRITA]
Q4 - Deve existir teto explícito de compensadores por fiada (ou penalidade
     forte no DP), mesmo deixando resíduo sem preencher?
     [SIM - qual teto / NÃO / PENALIDADE SEM TETO]

ATENÇÃO — CONFLITO NORMATIVO CONHECIDO
O Atlas antigo (9834b40) escreveu uma seção 35 que CONFLITA com a seção 35
do PR19 já integrada na main. A VIGENTE é a do PR19.
NÃO mesclar a alteração normativa do Atlas. Reaproveitar conteúdo apenas
como EVIDÊNCIA SEPARADA, nunca como regra.

DEPOIS das respostas: implementação mínima, hard gates de sempre
(OPENING/POSITION/JUNCTION 0 novas por identidade, Piloto idêntico,
determinismo em 2 processos), e registro obrigatório da regra aprovada em
nuvem/REGRAS_MODULACAO_BLOCOS.md.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 6 — `S2` — RESÍDUO ENTRE AMARRAÇÕES

```
CR: CR-BLOCK-FILL-RESIDUE-S2
Branch: claude/cr-block-fill-residue-s2-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

DEPENDÊNCIA: só começar depois de Q2 e Q4 do S1 respondidas.

PROBLEMA
O solver preenche resíduo entre amarrações com pares de compensadores
onde o humano usa um meio-bloco. Números medidos no S1.

ESCOPO DE PRODUÇÃO (máximo)
  nuvem/core/engine/wall_stepper.py   (função de custo do DP de pilarete)

IMPLEMENTAÇÃO MÍNIMA
Ajustar SÓ a função de custo/preferência do DP (preferir meio-bloco a par
de compensadores quando ambos cabem). NÃO mexer em amarração, encontro,
abertura ou stagger.

HARD GATES
- COMPENSATOR_CONSECUTIVE / COMPENSATOR_EXCESS_IN_RUN DEVEM CAIR
- COVERAGE_*: NÃO PODE PIORAR (o risco desta CR é trocar compensador por
  vazio — medir cobertura em cm, não só contagem de achados)
- OPENING_BLOCK_CROSSES_JAMB / POSITION_OVERLAP / JUNCTION_*: 0 novas
- PRISM_CONTINUOUS_JOINT: não pode subir
- Piloto: fingerprint IDÊNTICO. Determinismo em 2 processos.

VALIDAÇÃO HUMANA
Comparar peça a peça com o humano em W016, W012 e mais 3 paredes com par.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 7 — `CR-BLOCK-ARM-PERFORMANCE`

```
CR: CR-BLOCK-ARM-PERFORMANCE
Branch: claude/cr-block-arm-performance-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

PODE RODAR EM PARALELO com qualquer CR de qualidade: o critério de
aceitação é fingerprint IDÊNTICO, então um rebase nunca muda o resultado.

PROBLEMA (cProfile JA' EXECUTADO - TGD, main pos-PR19)
186,6s com overhead / 301M chamadas. Concentracao confirmada:

  repair_arm_role_isolated_edges (ARM)   175,5s cum   94,0%   1 chamada
  _rebuild (dentro do ARM)               174,6s cum   93,5%   22 chamadas
  solve_building_blocks                  162,1s cum   86,8%   184
  solve_wall_free_fill                    73,6s cum   39,4%   30728
  _pier_layout_avoiding_joints            46,3s cum   24,8%   67137

O custo real e' o padrao candidato -> pin -> RECONSTRUCAO COMPLETA ->
gates: 22 rebuilds do modelo inteiro, a 7,94s cada.

Folhas quentes (tottime) - alvos diretos:
  _exact_fill_blocks     20,5s    40192 chamadas   (maior tottime isolado)
  _wall_junction_ts_ft   13,0s    23184 chamadas   (0,56ms cada!)
  _obb_aabb / _obb_corners  32,9s / 31,0s cum, 1,0M / 1,45M chamadas
  revit_stubs.__add__    11,5s   10,8M  (so' fora do Revit - ignorar)

ALVO MAIS BARATO E SEGURO: memoizar _wall_junction_ts_ft (entrada estavel
dentro de um rebuild) e o par _obb_corners/_obb_aabb por peca. Nenhum dos
dois altera decisao - so' evita recomputar.

Tempo de parede sem profiler: TGD ~58s, TP1 ~90s, Piloto <0,4s.

ESCOPO DE PRODUÇÃO (máximo)
  nuvem/core/engine/wall_stepper.py
  nuvem/core/wall_modeling.py

FOCO
cache; memoization de gate por assinatura; dirty-wall rebuild (hoje o
padrão candidato -> pin -> reconstrução COMPLETA -> gates reconstrói o
modelo inteiro por candidato); reuso de composição de trecho idêntico;
eliminar rebuilds redundantes.

INVARIANTES OBRIGATÓRIAS — a CR falha se qualquer uma quebrar
- ARM accepted/rejected: conjunto IDÊNTICO por identidade
- fingerprint físico: IDÊNTICO nos 3 projetos
- hard gates: mesmos resultados, mesma ordem de rejeição
- counts_by_code e critical_by_code: IDÊNTICOS
- determinismo: 2 processos NOVOS

PROIBIDO reduzir validação para ganhar velocidade. Se um gate for pulado
por cache, o cache está errado.

CRITÉRIO DE ACEITAÇÃO
Redução de runtime com fingerprint bit-a-bit idêntico. Reportar o ganho
por projeto. Sem mudança de qualidade — é CR puramente de performance.

BASELINE STRATEGY
baseline.json intocado (não deve haver diferença nenhuma a refletir).

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 8 — `BENCH-WALLMODEL-FRAGMENTS`

```
CR: BENCH-WALLMODEL-FRAGMENTS
Branch: claude/bench-wallmodel-fragments-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

PROBLEMA
TGD: COVERAGE_WALL_NOT_MODULATED = 29, IDÊNTICO em STATE_A, STATE_B e
STATE_C do C04 — nenhuma CR de solver mexeu nisso. Suspeita de fragmento
de wall_modeling (FASE A), não de defeito do solver.
Também: pareamento espúrio (474, 2306), eixo de ~43,9m, sem CR atribuído.

OBJETIVO
SEPARAR fragmento de wall_modeling de defeito real de solver, para que o
crédito/débito de cobertura pare de ser contaminado. DIAGNÓSTICO PRIMEIRO
— não corrigir nada antes de classificar as 29.

ESCOPO
Rodar runner.py --wall-modeling-only e comparar o snapshot da FASE A com
as 29 paredes. Classificar cada uma:
   FRAGMENTO_DE_WALL_MODELING | DEFEITO_DE_SOLVER | GEOMETRIA_DE_ENTRADA

DIFF DE PRODUÇÃO = ZERO nesta CR. Se aparecer defeito de solver real,
abrir CR SEPARADA — não misturar correção de benchmark com correção de
produção.

Também documentar quais paredes ficam FORA do evaluation_scope (sem
contraparte humana). Medido nesta preparação: TGD W087, W072, W113, W030
não têm par humano — justamente onde a guarda do C04 mais custa e onde
nasce o crítico novo. Revisões futuras precisam disso explícito.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

## PROMPT 9 — `BENCH-BASELINE-REFRESH` (exige decisão do usuário)

```
CR: BENCH-BASELINE-REFRESH
Branch: claude/bench-baseline-refresh-<sufixo>
Base: <BASE_POS_C04>          Worktree isolado obrigatório.

NÃO EXECUTAR SEM AUTORIZAÇÃO EXPLÍCITA — regravar baseline é ação
normativa: apaga a memória de regressão do projeto.

EVIDÊNCIA DE QUE O BASELINE ESTÁ OBSOLETO (medida)
  métrica                          baseline   main pós-PR19
  TGD PRISM_CONTINUOUS_JOINT          961          320
  TP1 PRISM_CONTINUOUS_JOINT          968          256
  TGD compensators (achados)          950          815
  TP1 JUNCTION_MISSING_BINDING          8            9

O baseline é anterior a PR17/18/19. A main está muito melhor em quase
tudo, o que faz --check produzir sinal de baixa qualidade.

PRÉ-CONDIÇÃO DURA
NÃO regravar enquanto o PR #20 (C04) estiver em avaliação: isso esconderia
a regressão real de compensators do TGD (815 -> 1083) que a revisão
independente identificou como o único custo de produção do C04.

PROCEDIMENTO (se autorizado)
1. congelar a SHA exata da main usada;
2. regravar baseline.json dos 3 projetos numa rodada só;
3. registrar no PR, item a item, TODA métrica que mudou e por quê;
4. anotar explicitamente que TP1 JUNCTION_MISSING_BINDING=9 é
   REAL_SOLVER_DEFECT conhecido, NÃO artefato — o refresh não o resolve,
   só para de reportá-lo como novo.

DIFF DE PRODUÇÃO = ZERO.

ENTREGA: commit + push + PR DRAFT. NÃO MERGEAR. Sem monitoramento.
```

---

*Prompts preparados, não executados. Nenhuma SHA futura inventada.*
