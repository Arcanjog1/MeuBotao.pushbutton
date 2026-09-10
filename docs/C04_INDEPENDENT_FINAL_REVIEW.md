# C04 — REVISÃO INDEPENDENTE FINAL (PR #20)

> Revisão **adversarial e independente** do `CR-BLOCK-FIT-TOLERANCE-C04`.
> Não é a continuação da sessão implementadora: todos os números abaixo
> foram medidos do zero, com driver próprio, em worktrees isolados, sem
> reaproveitar nenhum artefato do relatório do implementador.
>
> **Nada de produção foi alterado por esta revisão.** Diff de produção
> desta branch = ZERO.

---

## 1. BASE / HEAD — identidade confirmada

| item | esperado (prompt) | medido | status |
|---|---|---|---|
| `origin/main` | `3ebcd9b63875f9114a3d6223aa648e5075e2d35b` | `3ebcd9b6…5e2d35b` | **CONFERE** |
| HEAD do PR #20 | `dde0261ea87f5680155b9303fddedb95106fd447` | `dde0261e…6fd447` | **CONFERE** |
| commit anterior C04 | `03e6817a3dc89d3b8eb93b5d8eff31b287eac03a` | ancestral de `dde0261` | **CONFERE** |

Sem divergência. Revisão autorizada a prosseguir sobre este HEAD.

Commits do PR (4):

```
03e6817  fix: tolerancia de fit modular 0,30cm            <- STATE_B
f31461f  fix: guarda fisica de fronteira (2a volta)
bb73e7c  test: guarda de jamba no ramo prefer_avoiding
dde0261  docs: resultado da suite completa                <- STATE_C
```

### Estados comparados

| estado | HEAD | significado |
|---|---|---|
| **STATE_A** | `3ebcd9b` | `main` pós-PR19, **sem** C04 |
| **STATE_B** | `03e6817` | C04 **sem** a guarda física (hard blocker) |
| **STATE_C** | `dde0261` | C04 **com** a guarda física (o que se propõe mesclar) |

---

## 2. AUDITORIA DO DIFF

O PR inteiro toca **6 arquivos**:

| arquivo | tipo |
|---|---|
| `nuvem/core/engine/modulation_math.py` | **produção (autorizado)** |
| `nuvem/core/engine/wall_stepper.py` | **produção (autorizado)** |
| `tests/test_block_fit_tolerance_c04.py` | teste (novo) |
| `tests/test_block_fit_tolerance_c04_jamb_guard.py` | teste (novo) |
| `docs/BLOCK_FIT_TOLERANCE_C04_IMPLEMENTATION.md` | docs |
| `docs/PROJECT_STATUS.md` | docs |

**Escopo de produção confirmado: exatamente os 2 arquivos autorizados.**
Nenhum arquivo de regra normativa (`nuvem/REGRAS_MODULACAO_BLOCOS.md`),
nenhum `baseline.json`, `reference.json`, `input.json` ou
`reference_score.json` foi tocado — verificado por `git diff --name-only`
sobre o range inteiro `3ebcd9b..dde0261`.

**Nenhuma regra de domínio foi alterada.** O fallback da guarda reusa a
composição que o próprio solver já montaria para um trecho um módulo
menor (`pier_cm_floored_to_module` → `_pier_ordered_layout`), sem
introduzir critério novo de amarração, de família de peça ou de encontro.

### 2.1 Dependência fora do escopo (observação, não bloqueio)

A guarda depende do contrato de `region_solid_subsegments`, que vive num
**terceiro** módulo de produção — `nuvem/core/engine/continuous_modulation.py`
— **não tocado** pelo PR. Auditei esse contrato (secção 4.1): ele está
correto para o que a guarda assume. Registro a dependência porque uma
alteração futura ali quebra a guarda silenciosamente, e não há teste que
amarre os dois módulos.

---

## 3. CONTRATO DE TOLERÂNCIAS — auditado por CONSUMIDOR, não por constante

### 3.1 As três constantes

```python
PIER_FIT_TOLERANCE_CM          = 0.30                        # NOVA
PIER_PHYSICAL_FIT_TOLERANCE_CM = PIER_LAYOUT_TOLERANCE_CM    # NOVA = 0.05
PIER_LAYOUT_TOLERANCE_CM       = MODULATION_WHOLE_CM_TOLERANCE_CM = 0.05  # inalterada
```

### 3.2 Onde o 0,30cm realmente entrou

Varredura de **todos** os consumidores de `PIER_LAYOUT_TOLERANCE_CM` em
STATE_A vs STATE_C:

| local | STATE_A | STATE_C | veredito |
|---|---|---|---|
| `_pier_remaining_snapped_cm` (3 comparações) | 0.05 | **0.30** | **alvo da CR — correto** |
| `_pier_layout_avoiding_joints` (peça equivalente) | 0.05 | 0.05 | preservado |
| checagem SEM_ESPAÇO / colisão (l. 3139, 3616, 3695, 5326) | 0.05 | 0.05 | preservado |
| consistência do DP de stagger (l. 3936, 3950) | 0.05 | 0.05 | preservado |
| adjacência de compensador (l. 5810, 6196) | 0.05 | 0.05 | preservado |
| `HALF_BLOCK_TIE_ADJACENCY_CM` (`wall_modeling.py`) | 0.05 | 0.05 | preservado |
| `COMPENSATOR_OPENING_ADJACENCY_TOLERANCE_CM` (`wall_modeling.py`) | 0.05 | 0.05 | preservado |

**Nenhuma tolerância de colisão, encontro, abertura, adjacência ou
stagger foi alargada.** A separação declarada é real.

### 3.3 As duas mudanças de default da API pública

`pier_closes_with_blocks_cm` e `wall_length_closes_with_blocks_cm`
tiveram o default trocado de `0.05` para `PIER_FIT_TOLERANCE_CM` (0,30).
Isso alcança 3 consumidores externos ao mecanismo alvo. Auditei cada um
e **os três são comportamentalmente inertes**, por prova aritmética:

| consumidor | entrada | por que é inerte |
|---|---|---|
| `_wall_length_snap_targets_cm` (l. 394) | alvos **inteiros** | `remaining` é inteiro ⇒ `\|remaining−snapped\| ∈ {0,1,2}`. Nem 0,05 nem 0,30 admite 1 ou 2. Conjunto idêntico. |
| `evaluate_wall_block_length` (l. 579) | protegido por `is_whole_cm` (≤0,05 de inteiro) | `\|remaining−snapped\|` fica em `{0,1,2}±0,05`. Só o ramo ~0 passa nos dois valores. Realce VERMELHO inalterado. |
| `wall_stepper.py` l. 8405 (pré-filtro de ajuste) | `new_len_cm` inteiro | mesmo argumento do primeiro. |

Ou seja: o alargamento **não escapou** para o validador ao vivo nem para
o realce de "comprimento quebrado".

### 3.4 Correção de ponto flutuante (mérito real do PR)

`pier_closes_with_blocks_cm` deixou de dividir por `PIER_MODULE_CM` antes
de comparar e passou a comparar em cm — **a mesma conta** que
`_pier_remaining_snapped_cm` sempre fez. Isso elimina uma divergência
real entre pré-checagem e solver no valor exatamente no limite. Correção
legítima e bem justificada no comentário.

---

## 4. A GUARDA FÍSICA — auditoria direta

```python
def _layout_fitted_to_physical_span(layout, pier_cm, sub, layout_for_span):
    if layout is None: return None
    if not sub.get("trailing_open"): return layout        # junta absorve
    end_cm = _layout_physical_end_cm(layout)
    if end_cm is None or end_cm - pier_cm <= PIER_PHYSICAL_FIT_TOLERANCE_CM:
        return layout
    floored_cm = pier_cm_floored_to_module(pier_cm, 0.0, 0.0)
    if floored_cm is None or floored_cm <= 0: return None
    fitted = layout_for_span(floored_cm)
    ...
```

### 4.1 Qual fronteira é considerada aberta — contrato verificado

Li `region_solid_subsegments` (`continuous_modulation.py` l. 254-312).
O contrato é:

```python
hi_cm = region["hi"] - (joint_cm if region["right_anchor_is_block"] else 0.0)
...
"trailing_open": not region.get("right_anchor_is_block")   # último trecho
"trailing_open": True                                      # trecho que termina em vão
```

**Consequência decisiva:** sempre que `trailing_open` é `True`, a junta de
argamassa **não** foi descontada, logo `sub["hi"]` **é** a fronteira física
real. A guarda compara contra `pier_cm = hi − lo`, ou seja, contra a
fronteira real. **O valor snapado nunca substitui a fronteira real** — ele
só é usado para montar o layout, e o layout é medido contra `pier_cm`.

Quando `trailing_open` é `False`, `hi` já vem 1cm antes do bloco âncora:
o excesso de até 0,30cm cai dentro de uma junta de 1,00cm. Pular a guarda
aí está **correto**.

### 4.2 Início vs fim, e orientação

O solver de pilarete é chamado com juntas de contorno `(0.0, 0.0)` e o
layout começa em `0.0`. O erro de snap só se acumula **para o fim**: a
primeira peça nunca recua antes de `lo`. Por isso checar apenas
`trailing_open` é geometricamente suficiente — **não é um esquecimento**.
A assinatura relatada `LEADING_JAMB` refere-se à jamba de ENTRADA da
abertura seguinte, que é justamente a ponta de SAÍDA do pilarete.

Confirmado empiricamente: nos 1205 disparos reais no corpus, a guarda
disparou tanto com `leading_open=True` (1136) quanto `False` (69) — o
predicado é só o de saída, como documentado.

### 4.3 Sondas independentes sobre a função REAL de produção

35 sondas contra `_layout_fitted_to_physical_span` /
`pier_cm_floored_to_module` carregadas do módulo de produção
(`core.engine.wall_stepper`), não reimplementadas:

| caso | resultado |
|---|---|
| trecho exato (9 / 19 / 34cm) | INALTERADO, invasão 0,0 |
| menor que o módulo, excesso 0,01–0,04cm | INALTERADO (tratado como ruído) |
| excesso 0,05–0,29cm | **REMONTADO**, sobra 4,71–4,95cm |
| excesso ≥ 0,30cm | o fit já rejeita antes (sem layout) |
| trecho **maior** que o módulo | INALTERADO, nunca invade |
| `trailing_open=False`, excesso 0,242cm | INALTERADO — **por projeto** (junta de 1cm absorve) |
| jamba no início / fim / duas fronteiras abertas | comportamento correto em todos |
| trecho pequeno demais (3,758 / 3,9cm) | devolve `None` → trecho vazio |
| multi-peça com juntas (48,758 / 98,733 / 168,88) | REMONTADO, sobra 4,73–4,88cm |
| translação de `lo` (0 / 100 / −250,5 / 1e5) | **saída idêntica** — invariante a translação |

**Contrato de `pier_cm_floored_to_module` verificado:** quando a guarda
dispara, a sobra deixada contra a fronteira fica sempre em
`[PIER_MODULE_CM − PIER_FIT_TOLERANCE_CM, PIER_MODULE_CM)` = `[4,70; 5,00)`.
O docstring está correto.

### 4.4 O fallback remove uma peça necessária?

Instrumentei a função real e capturei **todos** os disparos no corpus:

| projeto | disparos | REMONTADO | `None` (esvaziou) |
|---|---|---|---|
| TGD | 1081 | **1081** | **0** |
| TP1 | 124 | **124** | **0** |
| Piloto | 0 | 0 | 0 |

**A guarda nunca esvaziou um trecho no corpus inteiro.** O caminho
`return None` existe e é alcançável (sondado em `pier=3,758` e `3,9`),
mas nesses mesmos valores o STATE_A **também** não produzia peça — o
fallback restaura exatamente o comportamento pré-C04, como documentado.

### 4.5 A guarda aceita alguma peça que não cabe?

Não, dentro do seu ponto de aplicação. Excesso disparador medido: apenas
`{0,12; 0,242; 0,243; 0,267}` cm; sobra final sempre negativa (peça
termina **antes** da fronteira).

**Risco residual estrutural (registrado, não bloqueante):** o alargamento
para 0,30cm foi feito em `_pier_remaining_snapped_cm`, que é **global**,
enquanto a guarda foi aplicada em **um único ponto de chamada**
(`_solve_repair_subsegments`). `_pier_ordered_layout` é chamado sem a
guarda em outros pontos (l. 4160, 4263, 4290, 4693, 4713). Empiricamente
não houve escape (§6 mostra `OPENING_BLOCK_CROSSES_JAMB` e
`POSITION_OVERLAP` restaurados por identidade), mas a assimetria
"risco global / mitigação local" é uma dívida real para a próxima CR.

---

## 5. REPRODUÇÃO DO HARD BLOCKER — as 41 regressões

Método: identidade geométrica **normalizada** (código + parede + fiada +
descrição geométrica, com o rótulo sequencial `W…-R…-B…` removido — sem
essa normalização, a simples inserção de uma peça a mais na fiada
renumera as seguintes e produz 12 falsos "novos" no TGD).

### 5.1 STATE_B — hard blocker reproduzido

| projeto | `OPENING_BLOCK_CROSSES_JAMB` A → B | instâncias NOVAS |
|---|---|---|
| TGD | 108 → 144 | **36** |
| TP1 | 168 → 173 | **5** |
| **total** | | **41** |

**Reproduz exatamente os 41 relatados.**

Assinatura confirmada: paredes TGD `W044`(2), `W072`(5), `W075`(24),
`W113`(5); TP1 `W029`(5).

### 5.2 Relação entre excesso físico e arredondamento da jamba

| população | magnitude da invasão |
|---|---|
| 41 invasões NOVAS do STATE_B | **0,1 – 0,3 cm** |
| 108 pré-existentes do TGD (STATE_A) | 72 em 1–5cm, 36 em >5cm |
| 168 pré-existentes do TP1 (STATE_A) | **todas** >5cm |

As 41 são uma **classe qualitativamente nova** de defeito: sobra de snap
materializada dentro do vão, na ordem de 1–3 mm. Não existia antes do C04.
Casa exatamente com o excesso medido na guarda (`0,12`/`0,242`/`0,267`).

### 5.3 STATE_C — eliminação por IDENTIDADE, não por contagem

| projeto | A | B | C | **novas em C vs A** | **sumidas de A** |
|---|---|---|---|---|---|
| TGD | 108 | 144 | 108 | **0** | **0** |
| TP1 | 168 | 173 | 168 | **0** | **0** |

**O conjunto de STATE_C é elemento-a-elemento idêntico ao de STATE_A.**
As 41 desapareceram; nenhuma nova apareceu; nenhuma pré-existente foi
removida colateralmente (o que teria mascarado uma nova). Não há
compensação de contagens.

---

## 6. GATES ESTRUTURAIS — STATE_A vs STATE_C (identidade geométrica)

| código | TGD A→C | novas | TP1 A→C | novas | Piloto |
|---|---|---|---|---|---|
| `OPENING_BLOCK_CROSSES_JAMB` | 108→108 | **0** | 168→168 | **0** | 0→0 |
| `POSITION_OVERLAP` | 29→29 | **0** | 18→18 | **0** | 0→0 |
| `OPENING_BLOCK_INSIDE_DOOR` | 5→5 | **0** | — | — | 0→0 |
| `OPENING_MISSING_LINTEL` | 82→82 | **0** | — | — | 0→0 |
| `OPENING_MISSING_COUNTER_LINTEL` | 25→25 | **0** | 21→21 | **0** | 4→4 |
| `OPENING_SOLID_BELOW_SILL_MISSING` | 32→32 | **0** | — | — | 0→0 |
| `JUNCTION_MISSING_BINDING` | 23→23 | **0** | 9→9 | **0** | 0→0 |
| `JUNCTION_NOT_ALTERNATING` | 303→303 | **0** | — | — | 0→0 |
| `COVERAGE_WALL_NOT_MODULATED` | 29→29 | **0** | — | — | — |

**Todos os gates de abertura, colisão e junção estão preservados por
identidade geométrica.** Zero instâncias novas em qualquer um deles.

**Piloto: fingerprint físico idêntico em A, B e C** (`844900ccc1de`) —
delta zero comprovado no nível da peça, não no nível da contagem.

---

## 7. GANHO C04 — números reproduzidos

| métrica | esperado (relatório) | medido | status |
|---|---|---|---|
| TGD blocos | 11731 | **11731** | confere |
| TGD `COVERAGE_GAP_IN_ROW` | 1649 | **1649** | confere |
| TGD `COVERAGE_MISSING_ROW` | 192 | **192** | confere |
| TGD `COVERAGE_PARTIAL_WALL` | 48 | **48** | confere |
| TGD críticos | 872 | **872** | confere |
| TP1 blocos | 19572 | **19572** | confere |
| TP1 `COVERAGE_GAP_IN_ROW` | 214 | **214** | confere |
| TP1 `COVERAGE_PARTIAL_WALL` | 0 | **0** | confere |
| TP1 `COVERAGE_ROW_MOSTLY_EMPTY` | 0 | **0** | confere |
| Piloto | delta zero | **fingerprint idêntico** | confere |

Ganho bruto de cobertura: TGD **10679 → 11731 peças (+1052)**,
TP1 **18417 → 19572 (+1155)**.

**Retenção do ganho após a guarda:** TGD `11735 → 11731` = **99,6%**;
TP1 `19572 → 19572` = **100%**. Coerente com o 98,4–100% relatado.

### 7.1 Um crítico que o relatório não destaca

| projeto | críticos A | B | C |
|---|---|---|---|
| TGD | 884 | 908 | **872** (melhora) |
| TP1 | 469 | 490 | **485** (**piora +16**) |

O TP1 **regride em erros críticos**. O motor é
`PRISM_CONTINUOUS_JOINT` (§9). Isso precisa estar explícito na decisão —
não estava.

---

## 8. W087 — a decisão mais importante

### 8.1 O que a guarda faz ali (dado autoritativo, da função real)

```json
{"lo": 85.242, "hi": 94.0, "pier_cm": 8.758,
 "leading_open": true, "trailing_open": true,
 "right_opening": null,
 "excesso_cm": 0.242,
 "layout_in":  [["C09", 0.0, 9.0]],
 "layout_out": [["C04", 0.0, 4.0]]}
```

138 eventos idênticos (uma por fiada×parede afetada). A guarda troca um
**C09 (9cm) por um C04 (4cm)**, deixando 4,758cm livres. O vazio
reportado é de 5,8cm porque o validador mede até 95,0 (inclui a junta de
1cm).

### 8.2 Resposta geométrica às sete perguntas

**A) A reserva corresponde a ocupação física real do nó? — SIM.**
Mapeei o eixo de W087 para coordenadas absolutas (`y = 180,049 + t`,
`x = 593,518`) e varri **todas** as paredes na zona `t = 94…110`:

```
W106 f7 C09  centro (596.018, 282.049)  role = T_binding    <- peça de amarração
W106 f7 B34  centro (573.518, 282.049)  role = standard
```

**B) Existe peça da parede perpendicular cobrindo esse espaço na MESMA
fiada? — SIM.** `W106` C09 `T_binding`, na fiada 7 (mesmo `z = 141,0`).
A reserva é real e ocupada, não uma aproximação.

**C) A peça removida causaria sobreposição física real? — NÃO.**
O C09 removido iria de `y = 265,291` a `y = 274,291`. A face da peça de
amarração de W106 está em `y = 275,049`. **Folga de 0,758cm.** Nenhuma
sobreposição. A fronteira defendida (`hi = 94,0` ⇒ `y = 274,049`) já está
**1,00cm** antes da peça perpendicular — há junta de argamassa ali, ao
contrário do que o docstring da guarda assume para "reserva de nó".

**D) O humano usa peça equivalente nesse trecho? — INDETERMINADO.**
`W087` **não tem parede correspondente** no gabarito humano
(`match_walls` → `None`). Mesmo para `W072`, `W113` e `W030`. Essas
paredes estão fora da região com gabarito humano.

**E) A reserva é aproximação conservadora do solver? — NÃO a reserva;
SIM a guarda.** A reserva (94→110) é ocupação real. O que é conservador é
tratar `hi = 94,0` como fronteira sem folga, quando existe 1,00cm até a
peça perpendicular.

**F) Existe forma de preservar a peça sem violar a geometria real? — SIM,
em princípio.** Ver §8.4 — mas não é uma mudança de uma linha.

**G) É consistente com as regras de amarração? — SIM, sem conflito.**
A guarda não altera papel de peça, família, alternância nem cobertura de
nó. Ela só encurta o preenchimento. `JUNCTION_*` ficou com delta zero por
identidade (§6).

### 8.3 Classificação

Estratifiquei **todos** os 1205 disparos pelo tipo real de fronteira
(`right_opening`):

| tipo de fronteira | TGD | TP1 | classificação |
|---|---|---|---|
| **jamba de abertura real** (`right_opening` ≠ null) | 828 | 124 | **PHYSICALLY_REQUIRED_GUARD** |
| fim de região sem âncora de bloco — família W087 `[85.242, 94.0]` | 138 | 0 | **OVERCONSERVATIVE_GUARD** (provado em §8.2C) |
| fim de região sem âncora — `[17.0, 30.758]` e `[149.442, 173.2]` | 115 | 0 | **INCONCLUSIVE** (não verifiquei a folga física) |

### VEREDITO W087: **MIXED**

Predominantemente **PHYSICALLY_REQUIRED** (952 de 1205 = 79% dos
disparos protegem vão de abertura real, com junta ZERO por contrato).
A parcela overconservative está **confinada e é barata**.

### 8.4 Custo real da parcela overconservative

Atribuí o custo de composição por tipo de fronteira:

| fronteira | transições | efeito |
|---|---|---|
| **jamba** (414 eventos) | `B19 → [C09, C04]` | troca meio-bloco por **dois compensadores** — é o preço de não invadir o vão |
| **fim de região** (253 eventos) | `C09→C04`, `[C09,C04]→C09`, `[C04,B19]→B19` | **só remove**, nunca adiciona compensador |

Ou seja: o aumento de compensadores causado pela guarda vem **inteiro** do
ramo fisicamente necessário. O ramo overconservative custa apenas
cobertura: 253 × ~4,8cm, dos quais **somente 5 instâncias** (W087 fiadas
7–11) ultrapassam o limiar de reporte de vazio.

### 8.5 Fix mínimo recomendado — NÃO IMPLEMENTADO

Não recomendo aplicá-lo dentro desta CR (relaxar a guarda para recuperar
5 vazios é exatamente o que o prompt proíbe). Registrado para uma CR
futura:

> Expor, em `region_solid_subsegments`, a **folga física real** além de
> `hi` (distância até a próxima ocupação, própria ou de parede
> participante) como `trailing_slack_cm`. A guarda passaria a usar
> `max(PIER_PHYSICAL_FIT_TOLERANCE_CM, trailing_slack_cm)` como limite,
> em vez de `PIER_PHYSICAL_FIT_TOLERANCE_CM` fixo. Em jamba de abertura
> `trailing_slack_cm = 0` (contrato `BLOCK_OPENING_JOINT_CM = 0`), então
> o comportamento nas 952 fronteiras críticas fica **idêntico**.
>
> Toca `continuous_modulation.py` — **fora** do escopo autorizado do C04.
> Exige STATE_A/B próprios e revalidação das 41.

**Trade-off aceitável enquanto isso:** 5 vazios reportados, todos numa
parede sem gabarito humano, contra a eliminação de 41 invasões de vão
real. Aceitável — mas deve ficar registrado como dívida, não como
"resolvido".

---

## 9. TRADE-OFF DE COMPOSIÇÃO — a etiqueta EXPECTED_EXPOSURE foi TESTADA

Não aceitei o rótulo. Para cada achado novo em C, classifiquei o estado
da região em **STATE_A**: se a fiada tinha material ali, é recomposição
(candidato a regressão real); se estava vazia, é exposição.

### 9.1 `PRISM_CONTINUOUS_JOINT` (crítico) — +16 TGD, +34 TP1

| projeto | novos | estado em STATE_A das DUAS fiadas |
|---|---|---|
| TGD | 16 | 16× `FORA_DO_PREENCHIDO` + `VAZIO_LOCAL` |
| TP1 | 34 | 18× `FORA_DO_PREENCHIDO`+`VAZIO_LOCAL`, 16× ambas `FORA_DO_PREENCHIDO` |

**50 de 50** ocorrem onde **pelo menos uma das duas fiadas não tinha
material nenhum** em STATE_A. **Zero** casos em que as duas fiadas já
tinham peça e o alinhamento é novo.

**EXPECTED_EXPOSURE — verificado, não assumido.** A junta contínua não
podia existir antes porque não havia parede ali. É defeito de composição
**pré-existente do solver**, agora visível porque o C04 preencheu.

Não é isenção: são **+50 críticos reais** no modelo final, e o TP1 fica
com saldo crítico pior que a `main` (§7.1). Custo que **fica para a
próxima CR** (candidato natural: S1/S2 — política de composição).

### 9.2 `PRISM_STAGGER_BELOW_TARGET` (nível 2) — +67 TGD, +136 TP1

Majoritariamente exposição também. Exceções que merecem registro no TGD:
**3 casos** (`W083 t=49.4`) com `INTERIOR_DE_PECA` + `JUNTA_JA_EXISTIA` —
as duas fiadas já tinham material. São os únicos candidatos a
recomposição genuína encontrados em todo o corpus, e são de severidade
menor.

### 9.3 `COMPENSATOR_*` — +268 TGD, +110 TP1

Comparação com o humano (`W075` ↔ humano `W016`), fiada 0:

```
HUMANO :  B19 15–34            (meio-bloco único, encosta na jamba 34,0)
STATE_A:  (vazio)              <- não preenchia nada
STATE_C:  C09 15–24 + C04 25–29  <- dois compensadores, para 5cm antes
```

**Classificação honesta: composição de qualidade PIOR que a humana**, mas
sobre região que STATE_A deixava **vazia**. Não é regressão contra a
`main`; é dívida de qualidade nova exposta pelo preenchimento. Registrada
como custo para a próxima CR — não é "aumento aceitável porque coverage
melhorou".

### 9.4 `COVERAGE_GAP_IN_ROW` +13 novos no TGD

- **8 em `W165`**: vazio de 343,5cm. **Reclassificação, não regressão** —
  `W165` fiada 1 estava **completamente vazia** em STATE_A (contava como
  `COVERAGE_MISSING_ROW`, que caiu 66). Em C ela tem 3 B39. Cobertura da
  parede: **792cm → 2430cm**, 9 → 17 fiadas com material.
- **5 em `W087`**: custo real da guarda (§8).

---

## 10. VALIDAÇÃO HUMANA — parcial, com uma ressalva importante

### 10.1 O humano mantém a jamba exata? — SIM, confirmado

Humano `W016` (portas em 34,0–260,0 e 314,0–545,0), fiada 0:

```
B19  15,0 – 34,0     <- termina EXATAMENTE na jamba
B19 260,0 – 279,0
B19 295,0 – 314,0    <- termina EXATAMENTE na jamba
B34 545,0 – 579,0
```

**A premissa da guarda é validada diretamente pelo gabarito humano**, em
nível de parede — não por métrica agregada.

### 10.2 Ressalva: a métrica agregada NÃO sustenta essa leitura

Rodei os validadores sobre o **próprio gabarito humano**:

| projeto | `OPENING_BLOCK_CROSSES_JAMB` no humano | distribuição |
|---|---|---|
| TGD | **208** | 195 em **exatamente 15,0cm**; 13 em ≤0,3cm |
| TP1 | **209** | 195 em **exatamente 15,0cm**; 14 em ≤0,3cm |

Os 195 casos de **exatamente 15,0cm** são assinatura de **artefato de
reconstrução do benchmark** (valor redondo, repetido, idêntico nos dois
projetos), não de alvenaria real — confirma a suspeita já registrada
sobre "TP1 opening reconstruction". Consequência para esta revisão:

- o gate `OPENING_BLOCK_CROSSES_JAMB` **em valor absoluto** não é
  confiável (o gabarito o viola 208×);
- mas o gate **em delta por identidade** (que é como usei) continua
  válido, porque compara o solver contra ele mesmo;
- a decisão de manter a guarda em 0,05cm — **mais apertada** que o
  `OVERLAP_TOLERANCE_CM = 0,1cm` do validador — está **certa**: a guarda
  é física, não um ajuste para caber na régua.

### 10.3 Cobertura da validação humana

| parede | par humano | observação |
|---|---|---|
| TGD `W044` | `W010` | humano preenche 10–11 peças/fiada; A **e** C quase vazios — falha pré-existente, C04 não piora |
| TGD `W075` | `W016` | §10.1 e §9.3 |
| TGD `W165` | `W097` | grande melhora de cobertura |
| TGD `W019` | `W023` | — |
| TGD `W087`, `W072`, `W113`, `W030` | **nenhum** | **fora da região com gabarito humano** |

**Limitação declarada:** justamente as paredes onde a guarda custa mais
(`W087`) e onde nasce o novo crítico (`W030`) **não têm contraparte
humana**. A validação humana desta revisão é **parcial por construção do
corpus**, não por falta de esforço. Não inventei regra a partir de parede
isolada.

---

## 11. DETERMINISMO / INVARIÂNCIA

Reexecutei os 3 projetos nos 3 estados em **processos novos e
concorrentes** (o CPython randomiza o hash seed por processo por padrão,
então isto é um teste real de determinismo):

| estado | Piloto | TGD | TP1 |
|---|---|---|---|
| A | `438644e335ed` | `c81b2e15694e` | `b157b81701c8` |
| B | `438644e335ed` | `d80a51a9ca6a` | `fcf2fc5a1669` |
| C | `438644e335ed` | `1f1d1c050a5c` | `03a4f4ec7b96` |

**9/9 fingerprints idênticos entre as duas rodadas.** Contagem de blocos,
`counts_by_code` e `critical_by_code` idênticos em todas.

**Invariância a translação** verificada diretamente na guarda: `lo`
deslocado para 0 / 100 / −250,5 / 100000 produz layout **idêntico**
(§4.3). A guarda opera em coordenadas locais ao trecho, portanto é
estruturalmente invariante a translação, rotação e espelhamento — não há
caminho pelo qual coordenada absoluta entre na decisão.

**Dependências pré-existentes:** o não-determinismo global do wall graph
já registrado em `PROJECT_STATUS.md` é anterior a esta CR e não foi
reintroduzido nem agravado — as fiadas/peças saíram idênticas.

---

## 12. REGRESSÕES PR17 / PR18 / PR19

Todas preservadas por identidade geométrica no benchmark:

| gate | evidência |
|---|---|
| NODE-FILL (PR #17) | `PRISM_CONTINUOUS_JOINT` não teve nenhuma instância pré-existente removida; `JUNCTION_*` delta zero |
| ARM Gate Fidelity (PR #18) | `JUNCTION_MISSING_BINDING` TGD 23→23, TP1 9→9, **0 novas / 0 sumidas** |
| B19 residual fill (PR #19) | Piloto/TGD/TP1 com fingerprint estável; nenhum candidato novo aceito |
| `arm_role_safe_repair` | inalterado — o PR não toca nenhum símbolo de ARM |

---

## 13. SUÍTE COMPLETA / BASELINE

### 13.1 Baseline e reference — INTACTOS

Verificado em `git status --porcelain` nos três worktrees, restrito a
`*baseline.json`, `*reference.json`, `*input*.json`,
`*reference_score.json`: **vazio nos três**. O PR também não os toca.

### 13.2 Suíte completa executada nos DOIS estados

Executei a suíte inteira em STATE_C **e** o teste de baseline em STATE_A:

| estado | resultado |
|---|---|
| **STATE_C** (`dde0261`) | **809 passed, 2 failed** em 43min24s |
| **STATE_A** (`3ebcd9b`, `tests/regression/test_benchmark_baselines.py`) | **8 passed, 1 failed** em 8min17s |

> Meço `809 passed`, não os `797` relatados pelo implementador. A
> diferença não altera nenhuma conclusão, mas reporto o meu número.

**O PR leva a suíte de 1 falha para 2 falhas.** As duas falhas são o
mesmo teste (`test_projeto_nao_regrediu_contra_o_baseline`), em projetos
diferentes e por assertivas diferentes:

| projeto | linha da assertiva | tipo | STATE_A | STATE_C |
|---|---|---|---|---|
| TGD | `:58` | regressão de **categoria** | **PASSA** | **FALHA** |
| TP1 | `:50` | regressão **crítica** | **FALHA** | **FALHA** |

Classificação independente:

#### Falha 1 — TGD, categoria `compensators` contra baseline congelado

**REGRESSÃO REAL, CAUSADA PELO C04** — o teste **passa** em STATE_A e
**falha** em STATE_C.

| | achados de `compensators` |
|---|---|
| baseline congelado | 950 |
| STATE_A (`main` hoje) | **815** — passa |
| STATE_C | **1083** — falha |

O C04 leva a categoria de 815 para 1083 e ultrapassa o baseline. É o
custo de composição de §9.3, e é **legítimo chamá-lo de regressão**.
Exige decisão do usuário: aceitar como dívida registrada, ou exigir
correção antes do merge.

#### Falha 2 — TP1 `JUNCTION_MISSING_BINDING` 8 → 9

**NÃO É CAUSADA PELO C04 — provado por execução direta do teste.**

Rodei `tests/regression/test_benchmark_baselines.py` na **STATE_A**
(`main` pós-PR19, sem C04). Resultado:

```
FAILED test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]
AssertionError: REGRESSAO CRITICA em torre_easy_lo_r00_tp1:
  [{'code': 'JUNCTION_MISSING_BINDING', 'before': 8, 'after': 9,
    'delta': 1, 'status': 'REGRESSAO CRITICA'}]
1 failed, 8 passed
```

**Mensagem literalmente idêntica à do STATE_C.** E o TGD **passa** em
STATE_A — ou seja, o teste distingue perfeitamente as duas falhas.

| estado | valor |
|---|---|
| baseline congelado | 8 |
| **STATE_A (`main` pós-PR19, SEM C04)** | **9 — já falha** |
| STATE_B | 9 |
| STATE_C | 9 |

O defeito **já está na `main`**, idêntico por identidade geométrica nos
três estados (0 novas, 0 sumidas). Continua sendo um
`REAL_SOLVER_DEFECT` — não o rebaixo a "artefato de benchmark" — mas
**este PR não o introduz nem o agrava**. O que está desatualizado é o
baseline congelado, que é anterior a PR17/18/19.

> Evidência de que o baseline está globalmente obsoleto:
> `PRISM_CONTINUOUS_JOINT` TGD baseline **961** vs `main` hoje **320**;
> TP1 baseline **968** vs **256**. A `main` está muito melhor que o
> baseline em quase tudo — e pior só em `compensators`.

### 13.3 Nenhum baseline foi atualizado

Não atualizei `baseline.json` nem `reference.json` para fazer teste
passar, e **recomendo explicitamente não fazê-lo** dentro desta CR:
regravar o baseline agora esconderia a Falha 1, que é o único custo real
de produção deste PR.

---

## 14. DEFEITO DE JUNÇÃO REAL CONHECIDO

`TP1 JUNCTION_MISSING_BINDING = 9` permanece classificado como
**REAL_SOLVER_DEFECT com precondição de geometria de entrada**. Esta
revisão **confirma** a classificação e acrescenta o dado novo de que ele
é **anterior ao C04** (presente em STATE_A). Fica para
`CR-BLOCK-JUNCTION-NODE-COVERAGE` (ver preparação da Parte B).

---

## 15. VEREDITO INDEPENDENTE

### `APPROVE_WITH_EXPLICIT_CONDITIONS`

**Não é `APPROVE_FOR_MERGE`** porque duas das condições exigidas não são
plenamente satisfeitas:

| critério exigido | resultado |
|---|---|
| guarda física correta | **SIM** — contrato verificado, 1205 disparos auditados |
| 41 regressões eliminadas | **SIM** — por identidade, 0 novas, 0 colaterais |
| W087 compreendido | **SIM** — classificado MIXED com evidência física |
| ganho C04 material preservado | **SIM** — 99,6% / 100% |
| nenhum hard blocker estrutural novo | **SIM** — todos os gates críticos por identidade |
| trade-offs classificados com evidência | **SIM** — exposição testada, não assumida |
| determinismo preservado | **SIM** — 9/9 |
| produção dentro do escopo | **SIM** — exatamente os 2 arquivos |
| baseline/reference intactos | **SIM** |
| falhas remanescentes compreendidas | **SIM** — mas **1 é regressão real de produção** |

**As duas condições que faltam:**

1. **Regressão de `compensators` do TGD (815 → 1083) contra baseline** —
   é um custo real de produção, não artefato. Precisa de aceitação
   **explícita** do usuário como dívida registrada.
2. **TP1 fica com saldo crítico pior que a `main` (469 → 485)**, via
   `PRISM_CONTINUOUS_JOINT` +34. Verifiquei que é exposição legítima
   (§9.1), mas o número final é pior e isso precisa ser decisão
   consciente, não efeito colateral silencioso.

### Condições para o merge

- [ ] **C1** — Usuário aceita explicitamente a regressão de
      `compensators` do TGD (815→1083) como dívida, com CR de composição
      (S1/S2) na fila.
- [ ] **C2** — Usuário aceita explicitamente `TP1 críticos 469 → 485`
      (`PRISM_CONTINUOUS_JOINT` +34 por exposição verificada).
- [ ] **C3** — Registrar em `docs/PROJECT_STATUS.md` que a guarda tem
      ramo **overconservative** confinado a fronteiras de fim-de-região
      (§8.3/§8.5), com o fix mínimo já especificado e **não** implementado.
- [ ] **C4** — Registrar a dívida de escopo: tolerância alargada é
      global, guarda é local a um call site (§4.5).
- [ ] **C5** — **Não** regravar `baseline.json` para fazer os 2 testes
      passarem.

Satisfeitas C1–C5, **o PR #20 pode ser mesclado**. A guarda física está
correta, é a solução certa para o problema certo, e o ganho de cobertura
é grande e real.

### Não há FIX REQUEST

Não identifiquei defeito de implementação que exija correção na sessão
implementadora. Os dois pontos abertos são **decisões de trade-off do
usuário**, não bugs. O ramo overconservative do W087 é uma limitação
conhecida e barata, cujo fix correto está **fora** do escopo autorizado
desta CR.

---

## 16. CORREÇÕES AO ENUNCIADO DA REVISÃO

Registro, por honestidade de método, três pontos em que a medição
independente diverge do que o prompt afirmava:

1. **`TP1 JUNCTION_MISSING_BINDING 8→9` não é do C04** — já está em
   STATE_A (§13.2). Continua sendo defeito real do solver.
2. **A afirmação "o humano mantém a jamba exata" é verdadeira em nível de
   parede, mas o gabarito dispara o mesmo validador 208/209 vezes**
   (§10.2), com 195 casos de exatamente 15,0cm — artefato de
   reconstrução do benchmark.
3. **`docs/PROJECT_STATUS.md` na `main` está desatualizado**: declara
   `SHA: 209695d…` quando a `main` está em `3ebcd9b` (pós-PR19).

---

*Revisão independente executada sobre worktrees isolados. Diff de
produção desta revisão: ZERO.*
