# PREPARAÇÃO DAS PRÓXIMAS CRs DE BLOCOS

> **Documento de PREPARAÇÃO. Nada aqui está implementado.**
>
> Produzido na mesma sessão da revisão independente do C04
> (`docs/C04_INDEPENDENT_FINAL_REVIEW.md`), mas **totalmente separado
> dela**: nenhuma conclusão deste documento foi usada para justificar a
> aprovação do PR #20.
>
> **Diff de produção = ZERO.** Nenhuma regra normativa foi alterada.
> `nuvem/REGRAS_MODULACAO_BLOCOS.md` está intocado.

---

## 16. BASE DA PREPARAÇÃO

| item | valor |
|---|---|
| base medida | `main` pós-PR19 = `3ebcd9b63875f9114a3d6223aa648e5075e2d35b` |
| C04 (PR #20) | **NÃO MESCLADO** — tratado como ausente |
| STATE_C do C04 | usado só onde declarado explicitamente |

**Regra que vale para TODAS as specs abaixo:**

> **Revalidar sobre a `main` pós-C04 antes de implementar.** Nenhuma SHA
> futura foi inventada; onde a base futura é necessária, o texto usa o
> placeholder `<BASE_POS_C04>`.

### 16.1 Verificação de independência do C04

Medi cada alvo nos estados A e C. Resultado:

| alvo | STATE_A | STATE_C | independe do C04? |
|---|---|---|---|
| C10 — `W036`/`W038` junta 34,5 | `PRISM_CONTINUOUS_JOINT` 8+8, `JOINT_STACK` 1+1 | **idêntico** | **SIM** |
| Junction coverage — `W039`/`W041` | `JUNCTION_MISSING_BINDING` 9 | **idêntico** | **SIM** |
| C02 — X room check | 27,997 / 27,98 / 27,99cm | não medido em C | **SIM** (não toca esse caminho) |

**As três CRs podem ser especificadas e implementadas independentemente
do desfecho do PR #20.**

---

## 17. `CR-BLOCK-REPAIR-ANCHOR-JOINT` (C10)

### 17.1 Sintoma medido

TP1, `W036` e `W038` (paredes gêmeas: mesmo comprimento 524,0cm, mesmas
duas janelas em `t = 69–200` e `324–455`, T nos dois extremos):

| código | `W036` | `W038` |
|---|---|---|
| `PRISM_CONTINUOUS_JOINT` | **8** | **8** |
| `PRISM_JOINT_STACK` | 1 | 1 |
| `COMPENSATOR_EXCESS_IN_RUN` | 18 | 18 |
| `COMPENSATOR_CONSECUTIVE` | 14 | 14 |

**Todas as 16 juntas contínuas estão em `t = 34,5cm`**, entre pares de
fiadas consecutivas (0/1, 5/6, 10/11, …). `PRISM_JOINT_STACK` confirma
que a junta se repete na coluna inteira.

`t = 34,5` é o **centro da junta** logo após uma peça B34 que começa em
`t = 0` (nó T) e termina em `t = 34`.

### 17.2 Causa conhecida (a confirmar na implementação)

```
recut do trecho junto ao vão
    -> reparo local (_solve_repair_subsegments / opening_repair_regions)
        -> a região reparada é remontada da esquerda para a direita
            -> a primeira peça depois da âncora de nó cai sempre no
               mesmo lugar nas DUAS fiadas
                -> junta da família oposta recriada em t=34,5
```

O reparo local **não herda** a restrição de desencontro (`avoid_joint_
positions_cm`) da fiada oposta que o solver principal aplica. É a
pendência já registrada como **33.5 / NODE-FILL** em
`docs/PROJECT_STATUS.md`.

### 17.3 Minimal reproducer proposto

Sintético, sem depender do corpus:

```
parede reta 524,0cm, espessura 14
nó T em t=0 e em t=524
janela 1: t = 69 .. 200
janela 2: t = 324 .. 455
17 fiadas, alternância par/ímpar padrão
```

Critério de reprodução: `PRISM_CONTINUOUS_JOINT` em `t = 34,5` entre pelo
menos um par de fiadas consecutivas.

### 17.4 Investigação exigida (first divergence)

1. Instrumentar `_solve_repair_subsegments` e registrar, por fiada, o
   `avoid_joint_positions_cm` **realmente recebido**.
2. Comparar com o que o solver principal (`_pier_layout_avoiding_joints`)
   recebe para a mesma parede/fiada.
3. **Primeira divergência esperada:** o reparo recebe lista vazia (ou
   sem as juntas da fiada oposta) enquanto o principal recebe a lista
   completa.
4. Confirmar que `prefer_avoiding` está `False` no caminho do reparo, ou
   que está `True` mas com a lista errada.

### 17.5 Estratégia mínima

Propagar para o reparo local **a mesma** lista de juntas a evitar que o
solver principal usa para aquela fiada — sem inventar critério novo, sem
mudar o DP de stagger. Se a lista já chega e é ignorada, o fix é no
consumo, não na propagação.

**NÃO** relaxar `PRISM_CONTINUOUS_JOINT`. **NÃO** tratar como exceção de
domínio.

### 17.6 Hard gates

| gate | exigência |
|---|---|
| `OPENING_BLOCK_CROSSES_JAMB` | **0 novas** por identidade geométrica |
| `POSITION_OVERLAP` | **0 novas** |
| `JUNCTION_MISSING_BINDING` / `JUNCTION_NOT_ALTERNATING` | **0 novas** |
| `COVERAGE_*` | sem regressão líquida |
| `PRISM_CONTINUOUS_JOINT` | **deve cair** (alvo: −16 no TP1) |
| Piloto | fingerprint físico **idêntico** |
| determinismo | fingerprint estável em 2 processos novos |

### 17.7 Testes

- reproducer sintético de §17.3 (falha antes, passa depois);
- teste de que o reparo recebe a lista de juntas da fiada oposta;
- regressão: `W036`/`W038` sem junta em `t = 34,5`.

### 17.8 Arquivos / dependências

`nuvem/core/engine/wall_stepper.py` (`_solve_repair_subsegments`,
`opening_repair_regions`) e possivelmente
`nuvem/core/engine/continuous_modulation.py`
(`region_solid_subsegments`).

**Dependência:** conflita fisicamente com o C04 no mesmo call site
(`_solve_repair_subsegments`). **Implementar DEPOIS do C04**, nunca em
paralelo.

**Impacto esperado:** TP1 `PRISM_CONTINUOUS_JOINT` 256 → ~240 (−16);
`PRISM_JOINT_STACK` −2. Sem efeito em cobertura.

---

## 18. `CR-BLOCK-ROOM-CHECK-ROBUSTNESS` (C02)

### 18.1 O teto exato

Localizado em `wall_stepper.py`:

```python
X_INTERSECTION_B54_HALF_ROOM_FT = T_INTERSECTION_B54_HALF_ROOM_FT
# _x_intersection_centered_candidate:
#   half_len_ft + BLOCK_JOINT_CM(em ft) <= room_ft
```

Para o **B54**: `half_len = 27,0cm` + `BLOCK_JOINT_CM = 1,0cm` =
**28,00cm** de folga exigida em cada sentido.

### 18.2 Distribuição real medida (instrumentação da função de produção)

Instrumentei `_x_intersection_centered_candidate` e capturei **todas** as
avaliações de folga em nó X:

| projeto | avaliações | `room_cm` distintos | peça escolhida |
|---|---|---|---|
| TGD | 2024 | `{0,0 ; 27,997}` | `B34`: **184**, nenhuma: 1840 |
| TP1 | 1350 | `{17,0 ; 27,9 ; 27,98 ; 27,99}` | `B34`: **1050**, `C09`: 300 |
| Piloto | 4 | `{7,0}` | — |

### 18.3 Classificação do borderline — **não** "aceitar tudo"

| `room_cm` | falta para 28,00 | n | classificação proposta |
|---|---|---|---|
| **27,997** | **0,003cm** | 184 (TGD) | **RUÍDO NUMÉRICO** — mesma ordem do 0,00209cm já documentado |
| **27,99** | 0,01cm | TP1 | **RUÍDO NUMÉRICO** |
| **27,98** | 0,02cm | TP1 | **RUÍDO NUMÉRICO** |
| **27,9** | 0,10cm | TP1 | **BORDERLINE — decidir** (excede o piso de ruído de 0,05cm) |
| 17,0 | 11,0cm | 300 | **GEOMETRIA INSUFICIENTE** — degradar está correto |
| 7,0 / 0,0 | — | — | **GEOMETRIA INSUFICIENTE** |

**≈ 1234 colocações de amarração em X degradam B54 → B34 por faltar
0,003–0,02cm.** É a mesma família de defeito que o C04 corrigiu para o
fit modular, agora no caminho de amarração — o mais crítico do sistema.

### 18.4 Argumento físico (paralelo direto ao W087 do C04)

`room_ft` mede até a **borda** do próximo obstáculo, e o teste já desconta
1,0cm de junta. Aceitar 27,997cm significa deixar 0,997cm de junta em vez
de 1,000cm. **Não há colisão** — exatamente o raciocínio validado em
`C04_INDEPENDENT_FINAL_REVIEW.md` §8.2C.

### 18.5 Estratégia mínima proposta

Introduzir `ROOM_CHECK_NOISE_TOLERANCE_CM`, **dedicada e separada**
(mesmo padrão que o C04 usou para não alargar tolerância global):

```
half_len_ft + joint_ft <= room_ft + ROOM_CHECK_NOISE_TOLERANCE_CM(em ft)
```

Valor candidato: **0,05cm** (`PIER_LAYOUT_TOLERANCE_CM`, o piso de ruído
que o projeto já usa). Isso recupera 27,98 / 27,99 / 27,997 e
**deliberadamente NÃO recupera 27,9** — que fica para decisão humana
explícita.

**Proibido:** reusar `PIER_FIT_TOLERANCE_CM` (0,30cm) aqui. É contrato
diferente — 0,30cm cederia 30% da junta de amarração.

### 18.6 Hard gates

| gate | exigência |
|---|---|
| `POSITION_OVERLAP` | **0 novas** — é o gate que pega B54 colidindo |
| `JUNCTION_MISSING_BINDING` | **não pode subir** |
| `JUNCTION_NOT_ALTERNATING` | **0 novas** |
| `OPENING_BLOCK_CROSSES_JAMB` | **0 novas** |
| B54 recuperados | contar explicitamente quantos `B34 → B54` |
| validação humana | conferir se o humano usa B54 nesses nós |

### 18.7 Testes de invariância exigidos

`translation`, `rotation`, `endpoint reversal`, `mirror` — a folga medida
deve ser **idêntica** sob as quatro transformações. Se não for, o bug real
é na medição, não no teto.

### 18.8 Arquivos

`nuvem/core/engine/wall_stepper.py`
(`_x_intersection_centered_candidate`, `_x_intersection_wall_room_ft`,
`X_INTERSECTION_B54_HALF_ROOM_FT`). Avaliar se `T_INTERSECTION` e
`L_CORNER` têm o mesmo problema — provavelmente **sim**, já que
compartilham `T_INTERSECTION_B54_HALF_ROOM_FT`.

**Impacto esperado:** recuperação de até ~1234 peças de amarração B54.
**Alto impacto, risco médio** (mexe em amarração — o núcleo do sistema).

---

## 19. `CR-BLOCK-JUNCTION-NODE-COVERAGE`

### 19.1 Causa-raiz LOCALIZADA (não hipótese)

TP1: **todas as 9** ocorrências de `JUNCTION_MISSING_BINDING` estão no
**mesmo nó** — L entre `W039` e `W041` em `(6184.25, 949.95)`:

```
W039: start=[5800.25, 949.95]  end=[6184.25, 949.95]  len=384.0
      no L ponto=[6184.25, 949.95]  t_cm = 384.0   at_end=True    <- na ponta

W041: start=[6177.25, 957.95]  end=[6177.25, 1466.95]  len=509.0
      no L ponto=[6184.25, 949.95]  t_cm = -8.0    at_end=True    <- FORA DO EIXO
```

**`t_cm = −8,0` — o ponto físico do nó fica 8cm ANTES do início do eixo
de `W041`.** Confirma exatamente a hipótese do enunciado: "nós cujo ponto
físico fica fora do início/fim do eixo de uma parede participante".

O achado reporta: *"encontro L em (6177.2, 950.0) sem nenhuma peça na
fiada N — paredes W039, W041"* em **9 de 17 fiadas**.

### 19.2 Por que é geral, não um hack de W039/W041

O nó é assimétrico entre participantes: um vê `t` dentro do eixo, o outro
vê `t` negativo. Qualquer lógica que posicione a peça por `t` e recorte
para `[0, length]` perde o nó nesse participante. **Isso é estrutural** —
`W039`/`W041` são só a instância que o corpus expõe.

### 19.3 Comparação de estratégias exigida

| estratégia | descrição | risco |
|---|---|---|
| **node ownership** | eleger o participante cujo `t` está dentro do eixo como dono da peça | baixo — não muda geometria |
| **node extension** | estender o eixo de `W041` até o ponto do nó | alto — muda `length_cm`, propaga para modulação |
| **alternate corner candidate** | aceitar a peça do outro participante como cobertura do nó | médio |
| **B19 closure** | **PROIBIDO** — B19 é FILL, nunca TIE |
| **participant coverage** | crédito físico de cobertura, no espírito do PR #18 | baixo — já existe precedente |

**Recomendação preliminar:** combinar **node ownership** + **participant
coverage**. Ambas já têm precedente aprovado (Gate Fidelity, PR #18) e
nenhuma altera a geometria de entrada.

### 19.4 Regras que NÃO podem ser tocadas

- **B19 é FILL, nunca TIE** — sem exceção.
- Nenhuma exceção de domínio nova sem aprovação explícita do usuário.
- Alternância par/ímpar de canto L preservada.

### 19.5 Critérios físicos de aceitação

1. O ponto físico do nó fica **geometricamente coberto** por peça real de
   amarração em **todas** as fiadas onde a regra exige.
2. `POSITION_OVERLAP` **0 novas** — a peça não pode invadir a perpendicular.
3. `JUNCTION_MISSING_BINDING` TP1 **9 → 0**.
4. `JUNCTION_NOT_ALTERNATING` não sobe.
5. TGD (`JUNCTION_MISSING_BINDING` = 23) — medir; se forem o mesmo padrão,
   devem cair junto. Se não caírem, **investigar antes de fechar a CR**.

### 19.6 Arquivos

`nuvem/core/engine/wall_stepper.py` (`solve_l_corner`,
`_t_of_point_on_wall`, `_wall_reserved_range_ft`),
`nuvem/core/engine/wall_pairing.py` (construção do nó, `t_cm` negativo).

---

## 20. S1 / S2 — POLÍTICA DE COMPOSIÇÃO (decisão humana necessária)

> **Nada aqui é regra.** Este bloco existe para o usuário aprovar ou
> rejeitar. **Não** promovi nenhuma observação do Atlas a regra
> obrigatória. `nuvem/REGRAS_MODULACAO_BLOCOS.md` **não foi alterado**.

### 20.1 `SHORT_WALL_NODE_POLICY`

| camada | conteúdo |
|---|---|
| **REGRA VIGENTE** | Grupo B (reserva de pior caso em parede curta) mantém 6 arestas ARM corretamente rejeitadas — `docs/BLOCK_ARM_REJECTED_EDGES_DIAGNOSIS.md` |
| **EVIDÊNCIA HUMANA** | não coletada especificamente para parede curta |
| **CONFLITO** | nenhum registrado |
| **HIPÓTESE** | a reserva de pior caso pode ser conservadora demais, do mesmo jeito que a guarda do C04 é no ramo fim-de-região |
| **DECISÃO NECESSÁRIA** | **Q1** abaixo |

### 20.2 `FILL_RESIDUE_BETWEEN_TIES`

| camada | conteúdo |
|---|---|
| **REGRA VIGENTE** | resíduo entre amarrações é preenchido pelo catálogo comum |
| **EVIDÊNCIA HUMANA (medida nesta sessão)** | humano `W016` f0 usa **um B19** em `15–34`; o solver (STATE_C do C04) usa **C09 + C04** no mesmo espaço |
| **CONFLITO** | solver prefere 2 compensadores onde o humano usa 1 meio-bloco |
| **HIPÓTESE** | falta preferência explícita por meio-bloco sobre par de compensadores quando os dois cabem |
| **DECISÃO NECESSÁRIA** | **Q2** |

### 20.3 `B19 perto de nó`

| camada | conteúdo |
|---|---|
| **REGRA VIGENTE** | seção 35 — B19 fecha resíduo de 15–20cm só com amarração real íntegra no MESMO nó/MESMA fiada; **0 candidatos aceitos** no corpus |
| **EVIDÊNCIA HUMANA** | `docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md` |
| **CONFLITO** | **ATENÇÃO** — o Atlas antigo escreveu uma seção 35 que **conflita** com a seção 35 do PR19 já integrada na `main`. **A da `main` (PR19) é a vigente.** |
| **HIPÓTESE** | condição "mesma fiada" pode ser restritiva demais (0/102 fiadas medidas) |
| **DECISÃO NECESSÁRIA** | **Q3** |

### 20.4 `B34 como fill` / `B54` / compensadores

| camada | conteúdo |
|---|---|
| **REGRA VIGENTE** | B34/B54 são peças de amarração; uso como fill não está proibido explicitamente |
| **EVIDÊNCIA HUMANA** | humano `W010` usa B34/B39 como fill corrente (10–11 peças/fiada) |
| **CONFLITO** | solver produz muito mais compensador que o humano — TP1 `W012`: **109 compensadores contra 18** do humano |
| **HIPÓTESE** | função de custo do DP não penaliza compensador o suficiente |
| **DECISÃO NECESSÁRIA** | **Q4** |

### 20.5 Perguntas objetivas para o usuário

> **Q1** — Em parede curta, a reserva de pior caso pode ser substituída
> por medição da folga física real (como o fix mínimo proposto para a
> guarda do C04), aceitando peça de amarração que hoje é rejeitada?
> `[SIM / NÃO / SÓ COM MEDIÇÃO NO REVIT]`

> **Q2** — Quando um meio-bloco B19 **e** um par de compensadores
> (C09+C04) cabem no mesmo resíduo, o solver deve **sempre** preferir o
> B19 (como o humano faz)? `[SIM / NÃO / DEPENDE — especificar]`

> **Q3** — A condição "amarração real íntegra no MESMO nó e MESMA fiada"
> para o B19 residual (seção 35 vigente) deve ser relaxada para "no mesmo
> nó, em qualquer fiada"? Medição atual: **0/102 fiadas** satisfazem a
> condição estrita. `[SIM / NÃO / MANTER ESTRITA]`

> **Q4** — Deve existir um **teto explícito de compensadores por fiada**
> (ou penalidade forte no DP), mesmo ao custo de deixar resíduo sem
> preencher? Referência: TP1 `W012` 109 vs 18 do humano.
> `[SIM — qual teto / NÃO / PENALIDADE SEM TETO]`

---

## 21. `CR-BLOCK-ARM-PERFORMANCE`

### 21.1 Situação — `cProfile` executado nesta sessão (TGD, STATE_A)

Tempo de parede sem profiler: **TGD ≈ 58s**, **TP1 ≈ 90s**,
**Piloto < 0,4s**. `cProfile` do TGD (186,6s com overhead, 301M chamadas):

| função | cumtime | % do total | ncalls |
|---|---|---|---|
| `solve_building_blocks_all_courses` | 183,3s | 98,2% | 1 |
| **`repair_arm_role_isolated_edges` (ARM)** | **175,5s** | **94,0%** | 1 |
| `_rebuild` (dentro do ARM) | 174,6s | 93,5% | **22** |
| `solve_building_blocks` | 162,1s | 86,8% | 184 |
| `solve_wall_free_fill` | 73,6s | 39,4% | 30 728 |
| `_pier_layout_avoiding_joints` | 46,3s | 24,8% | 67 137 |

**Confirma os ~95–96% relatados: 94,0% cumulativo no ARM.**

O custo real é o padrão candidato → pin → **reconstrução completa** →
gates: **22 rebuilds do modelo inteiro, a 7,94s cada**.

Folhas quentes (`tottime` — alvos diretos de memoização):

| função | tottime | ncalls | observação |
|---|---|---|---|
| `_exact_fill_blocks` | **20,5s** | 40 192 | maior `tottime` isolado (11%) |
| `_wall_junction_ts_ft` | **13,0s** | 23 184 | 0,56ms/chamada — recomputa `t` dos nós a cada checagem de corner bond |
| `revit_stubs.__add__` | 11,5s | **10 847 739** | só nos testes/benchmark, não no Revit real |
| `_obb_aabb` | 3,7s (32,9s cum) | 1 021 911 | geometria de colisão |
| `_obb_corners` | 1,6s (31,0s cum) | 1 450 223 | idem |

**Alvo mais barato e mais seguro:** memoizar `_wall_junction_ts_ft`
(entrada estável dentro de um rebuild) e o par `_obb_corners`/`_obb_aabb`
por peça. Nenhum dos dois altera decisão — só evita recomputar.

### 21.2 Foco autorizado

| técnica | descrição |
|---|---|
| **cache** | memoizar avaliação de candidato por `(wall_idx, course, node)` |
| **memoization** | resultado de gate por assinatura de entrada |
| **dirty-wall rebuild** | reconstruir só as paredes afetadas pelo candidato, não o modelo inteiro |
| **reuso de composição** | reaproveitar layout de trecho idêntico já resolvido |
| **evitar rebuilds redundantes** | o padrão candidato→pin→reconstrução completa→gates reconstrói tudo por candidato |

### 21.3 Invariantes OBRIGATÓRIAS

**Nenhuma otimização pode alterar o resultado.** Exigências:

| invariante | verificação |
|---|---|
| ARM `accepted`/`rejected` | conjunto **idêntico**, por identidade |
| fingerprint físico | **idêntico** nos 3 projetos |
| hard gates | mesmos resultados, mesma ordem de rejeição |
| determinismo | 2 processos novos, fingerprint estável |
| `counts_by_code` | idêntico |

**PROIBIDO: reduzir validação para ganhar velocidade.** Se um gate for
pulado por cache, o cache está errado.

### 21.4 Critério de aceitação

Redução de runtime **com fingerprint bit-a-bit idêntico**. Sem ganho de
qualidade, sem mudança de resultado — é CR puramente de performance.

---

## 22. BENCHMARK / GEOMETRIA DE REFERÊNCIA

> **Regra dura: não misturar correção de benchmark com correção de
> produção na mesma CR.** E **não** regravar `reference/input/baseline`
> sem CR própria e aprovação.

### 22.1 `BENCH-OPENING-RECONSTRUCTION` — evidência nova e forte

Rodei os validadores sobre o **próprio gabarito humano**:

| projeto | `OPENING_BLOCK_CROSSES_JAMB` no gabarito | distribuição |
|---|---|---|
| TGD | **208** | **195 em exatamente 15,0cm**; 13 em ≤ 0,3cm |
| TP1 | **209** | **195 em exatamente 15,0cm**; 14 em ≤ 0,3cm |

**195 casos de exatamente 15,0cm, idênticos nos dois projetos**, é
assinatura inequívoca de **artefato de reconstrução**, não de alvenaria
real. Provável origem: offset de jamba (meio bloco / recuo padrão)
aplicado na reconstrução `input.json` ↔ `reference.json`.

**Consequência:** o gate `OPENING_BLOCK_CROSSES_JAMB` **em valor
absoluto** não é confiável. Só o **delta por identidade** (solver contra
si mesmo) é válido — foi assim que a revisão do C04 o usou.

**CR proposta:** investigar o offset de 15,0cm no pipeline
`extract/reconstruct.py`, corrigir a reconstrução, **recalibrar**
`reference_score.json`. **Não tocar produção.**

### 22.2 `BENCH-BASELINE-REFRESH` — baseline congelado está obsoleto

| métrica | baseline | `main` hoje (STATE_A) |
|---|---|---|
| TGD `PRISM_CONTINUOUS_JOINT` | 961 | **320** |
| TP1 `PRISM_CONTINUOUS_JOINT` | 968 | **256** |
| TGD `compensators` (achados) | 950 | **815** |
| TGD `COVERAGE_MISSING_ROW` | 265 | 258 |
| TP1 `JUNCTION_MISSING_BINDING` | 8 | **9** |

O baseline é anterior a PR17/18/19. A `main` está **muito melhor** em
quase tudo. Isso faz o `--check` produzir sinal de baixa qualidade.

**Requer decisão do usuário** — regravar baseline é ação normativa.
Recomendação: **não** regravar enquanto o PR #20 estiver em avaliação,
porque isso esconderia a regressão real de `compensators` (§13.2 da
revisão).

### 22.3 `BENCH-WALLMODEL-FRAGMENTS` (TGD Phase A)

`COVERAGE_WALL_NOT_MODULATED` = 29 no TGD, **idêntico em A, B e C** —
nenhuma CR de solver mexeu nisso. Também o pareamento espúrio
`(474, 2306)` de ~43,9m, já registrado. Separar fragmento de
`wall_modeling` de defeito de solver antes de creditar/descontar
cobertura.

### 22.4 `foreign-node coverage credit`

Paredes sem contraparte humana (`W087`, `W072`, `W113`, `W030` no TGD)
não recebem crédito nem débito na métrica SCOPED. Documentar
explicitamente quais paredes estão fora do `evaluation_scope`, para que
revisões futuras não concluam "sem validação humana" onde na verdade é
"fora do escopo do gabarito".

---

## 23. ROADMAP PÓS-C04

### 23.1 Fila recomendada

| # | CR | impacto | risco | confiança | decisão humana? | paralelizável |
|---|---|---|---|---|---|---|
| **1** | `BENCH-OPENING-RECONSTRUCTION` | alto (destrava métrica) | **baixo** (não toca produção) | **alta** | não | **SIM** |
| **2** | `CR-BLOCK-ROOM-CHECK-ROBUSTNESS` (C02) | **alto** (~1234 amarrações) | médio (mexe em amarração) | **alta** (causa localizada) | não | não |
| **3** | `CR-BLOCK-JUNCTION-NODE-COVERAGE` | médio (9 TP1 + até 23 TGD) | médio | **alta** (`t_cm = −8,0`) | não | não |
| **4** | `CR-BLOCK-REPAIR-ANCHOR-JOINT` (C10) | médio (−16 críticos) | médio | média | não | **não** (mesmo call site do C04) |
| **5** | S1/S2 política de composição | **alto** | alto | **baixa** | **SIM — Q1–Q4** | não |
| **6** | `CR-BLOCK-ARM-PERFORMANCE` | zero em qualidade | baixo | alta | não | **SIM** |
| **7** | `BENCH-BASELINE-REFRESH` | zero | baixo | alta | **SIM** | **SIM** |
| **8** | `BENCH-WALLMODEL-FRAGMENTS` | médio | médio | baixa | não | **SIM** |

### 23.2 Por que esta ordem (não é pelo número bruto de achados)

- **#1 primeiro** porque hoje **não dá para confiar em
  `OPENING_BLOCK_CROSSES_JAMB` absoluto** (§22.1). Toda CR que mexe em
  abertura fica com gate de baixa qualidade até isso ser resolvido. Não
  toca produção ⇒ risco quase nulo, e destrava as demais.
- **#2 antes de #3/#4** porque tem a maior razão impacto/risco: causa
  localizada, número medido (1234), e o padrão de correção já foi
  validado pelo próprio C04.
- **#4 depois do C04** obrigatoriamente — mesmo call site
  (`_solve_repair_subsegments`); implementar em paralelo garante conflito.
- **#5 por último entre as de produção** porque depende de Q1–Q4 e é a
  única que pode exigir mudança em `REGRAS_MODULACAO_BLOCOS.md`.
- **#6 e #7 podem rodar em paralelo** com qualquer coisa: #6 tem
  fingerprint idêntico como critério, #7 não toca produção.

### 23.3 Agrupamento por natureza

| grupo | CRs |
|---|---|
| **sequencial em produção** | #2 → #3 → #4 → #5 |
| **exige decisão de domínio** | #5 (Q1–Q4), #7 |
| **depende de benchmark corrigido** | #5 (usa evidência humana), qualquer uma que meça abertura |
| **paralelizável (não toca produção)** | #1, #6, #7, #8 |

---

## 24. PROMPTS PRONTOS

Os prompts completos, prontos para colar, estão em
**`docs/FUTURE_BLOCK_CR_PROMPTS.md`**.

---

## 25. AVISO SOBRE A SEÇÃO 35 DO ATLAS

> O Atlas antigo (`claude/block-solver-residual-root-cause-gwcmqa`,
> `9834b40`) escreveu uma **seção 35** de
> `nuvem/REGRAS_MODULACAO_BLOCOS.md` que **conflita** com a seção 35 do
> PR19 **já integrada na `main`**.
>
> **A seção 35 vigente é a do PR19 (`main`).**
>
> **NÃO mesclar a alteração normativa do Atlas.** Se algum conteúdo for
> reaproveitado, preservar a regra vigente e manter as observações não
> aprovadas como **evidência separada**, nunca como regra.
>
> Esta sessão **não alterou** `nuvem/REGRAS_MODULACAO_BLOCOS.md`.

---

*Preparação diagnóstica. Diff de produção = ZERO. Nenhuma regra
normativa alterada. Nenhum baseline/reference tocado.*
