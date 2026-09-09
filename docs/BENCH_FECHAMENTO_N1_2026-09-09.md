# FECHAMENTO DA N1 + CORREÇÕES DE ALTO IMPACTO — 2026-09-09

Base: `main` `08495d9`. Branch N1: `claude/fervent-mccarthy-lhwoai`
HEAD `626087b` (PR #30, draft). Trabalho desta sessão:
`claude/sleepy-turing-rf4s7o`, partindo de `626087b`.

**Sem Revit. Sem monitoramento automático. Sem merge na `main`.**
`input.json`, `reference.json`, `reference_score.json` e `baseline.json`
**não** foram regravados. C2/G16 e CR-B intocados.

Toda medição por **identidade física** (`W|x0,y0|x1,y1|tE`, pontas
ordenadas). Nunca `W0xx` cruzado entre input e result.

---

## 1. N1 — as três falhas novas de teste: FECHADAS

Investigadas uma a uma: contrato original lido, base e patch
reproduzidos nas **duas árvores** (`origin/main` `08495d9` ×
`626087b`), resultado físico final comparado. As três eram **asserções
de mecanismo obsoletas**, não regressão física — e isso foi **provado**,
não suposto.

### 1.1 `test_t1_t9_candidato_seguro_e_aceito_no_tgd_real` (TGD)

| | base | CR-N1 |
|---|---|---|
| parede aceita `W\|1201.5,-508.0\|1325.5,-508.0\|t14.0` — repairable | SIM | **NÃO** |
| … aceita pelo reparo | SIM | NÃO |
| … prisma forçado FINAL | **NÃO** | **NÃO** |
| paredes repairable | 7 | 2 (**5 saíram, 0 entraram**) |
| prisma forçado FINAL | 29 | **27** |

O resultado **físico** daquela parede é idêntico; mudou a **rota**
(reparo aceito → geração já correta). Nenhuma parede entrou na lista de
reparáveis.

### 1.2 `test_w076_tp1_...` (TP1)

`W076` é a **mesma parede física** no input e no result
(`W|7677.2,1568.0|7677.2,1637.0|t14.0`) — conferido, e agora com
asserção própria no teste.

| | base | CR-N1 |
|---|---|---|
| W076 repairable / aceita | SIM / SIM | **NÃO / NÃO** |
| W076 coincidência de contorno | `[]` | `[]` |
| W076 prisma forçado FINAL | NÃO | NÃO |
| paredes repairable no TP1 | 5 | **0** |
| prisma forçado FINAL no TP1 | 29 | **24** |

### 1.3 O que mudou nos testes (só o obsoleto; o físico foi FORTALECIDO)

- T1/T9: `assert accepted` → as paredes que o SAFE REPAIR já aceitou como
  candidato seguro (23 na CR-G12, 91 na CR-N1) terminam **sem prisma
  forçado**, localizadas pela **chave física** e não pelo índice — o teste
  passa a falhar também se a parede sumir do plano.
- W076: `assert accepted_here` → coincidência resolvida em **todos** os
  pares de fiadas vizinhas (antes só o par 0/1) + **sem prisma forçado** +
  guarda de identidade física input×result.
- Que o gate **continua aceitando** candidato seguro está provado **sem
  depender do corpus** por `test_wiring_neighbor_credita_do_alvo` e
  `test_wiring_alvo_credita_da_vizinha` (`assert ok_with_map is True`).

Nenhum `skip`, `xfail`, teste removido ou threshold afrouxado.

### 1.4 `test_reproducer_minimo_falha_no_codigo_anterior` (CR-G12)

O defeito da CR-G12 **não sumiu**: com a propagação desligada o TGD
inteiro ainda tem **10 identidades cross-band puras**, e os quatro testes
de **corpus** seguem verdes. O que a CR-N1 invalidou foi a **redução**.

Refeita pelo mesmo método (vizinhança geométrica + delta-debugging), agora
com predicado **duplo**: reproduz com a flag OFF **e** zera com a flag ON.
Subplano novo `(4, 83, 119)` — três paredes do mesmo `input.json`, mesma
topologia (principal de 1174cm com abertura + duas bonecas de 183,2cm e
94cm). Medido: OFF → 21 identidades, entre elas o alvo `(621,0; 17,0)`
cotas 121/141 marcado **cross-band**; ON → **zero**; peças de
amarração/abertura **idênticas** nas duas rodadas (40 × 40). As três
asserções do trio continuam literalmente as mesmas.

---

## 2. O `+30 COMPENSATOR_VERTICAL_STRIP` do TGD: era REGRESSÃO FÍSICA

O pedido era separar evento físico novo de mudança de identidade/contagem.
Separado, por identidade física, comparando as 79 faixas da base com as
109 da CR-N1:

| classe | faixas |
|---|---|
| parede que estava vazia e passou a ter blocos | 0 |
| parede que ganhou fiadas preenchidas | 5 |
| faixa que cresceu no mesmo `t` | 3 |
| **faixa NOVA em parede estável** | **33** |

Não era artefato de contagem. Paredes que tinham **0 compensadores**
passaram a ter **34–50**, e a peça de amarração do canto virou um **C09 de
9cm**:

```
W|-1.5,463.0|-1.5,532.0|t14.0   (69cm)   0 -> 34 compensadores
fiada 0  BASE : B34[0,34] L_CORNER          + B19[35,54] STANDARD_FILL
fiada 0  CR-N1: C09[0,9]  L_CORNER_DEGRADED + B39[10,49] + C04[50,54]
```

### 2.1 Causa-raiz: DUPLA CONTAGEM da reserva de ponta (corrigida)

`_wall_reserved_range_ft` já reserva, para **cada ponta**, o pior caso
`CORNER_B34_ROOM_FT` = 34cm medido da ponta **física**. A CR-N1 passou a
cobrar **também** o ponto médio até o nó vizinho — e para os nós que estão
**nas pontas** os dois descontam a **mesma** reserva.

| parede de 69cm, nós em t=7,0 e t=62,0 | room |
|---|---|
| histórico (só reserva de ponta) | **28,00cm** |
| CR-N1 (mínimo com o ponto médio 34,5cm) | **27,50cm** |

Meio centímetro que **cruza limiar**: com eixo de 81cm são 40,00 × 33,50cm
contra `CORNER_B34_ROOM_FT` = 34cm — o canto deixa de receber B34.

**Correção (`CR-N1b`, commit próprio, revertível isoladamente)**:
`_room_at_t_on_wall` ganha `end_to_node` e, quando `safe_range_ft` foi
informado, isenta os nós das duas **pontas**. Nós de **meio de parede**
(T/X) — os que produziam os `POSITION_OVERLAP` — continuam limitando.

**Verificado**: as duas paredes de 69cm voltam ao conjunto de achados
**exatamente igual ao da base**; `POSITION_OVERLAP` continua **0/0**.

### 2.2 Trade-off DECLARADO

| | base | CR-N1 | CR-N1b |
|---|---|---|---|
| TGD total (identidades físicas) | 798 | **783** | 801 |
| TGD `COMPENSATOR_VERTICAL_STRIP` | 79 | 109 | **102** |
| TGD `COMPENSATOR_EXCESS_IN_RUN` | 70 | 85 | **82** |
| TGD `PRISM_STAGGER_BELOW_TARGET` | 181 | **156** | 168 |
| TP1 total | 862 | 862 | 867 |
| `POSITION_OVERLAP` TGD/TP1 | 6/1 | **0/0** | **0/0** |

Das 77 identidades que a CR-N1b acrescenta sobre a CR-N1 no TGD, **48 são
o RETORNO** de identidades que a base já tinha (a parede voltou ao estado
correto) e **29 são genuinamente novas** — as 29 estão **todas** nas
quatro paredes de 124cm da pendência aberta abaixo.

**Leitura honesta**: o placar da CR-N1 estava melhor em parte porque a
amarração degradada gera peças pequenas que desencontram junta com
facilidade — ganho no validador de junta, perda na amarração. A hierarquia
do projeto põe amarração acima de estética de junta, e dupla contagem é
**defeito**, não preferência. Se o usuário preferir o placar,
`git revert 417341c` basta.

### 2.3 PENDÊNCIA aberta — nó de MEIO com peça CENTRADA

Quatro paredes reais de **124cm** com um `X_INTERSECTION` de travessia em
t=62,0 continuam com ~50 compensadores. Ali o limitador não é a ponta.
Medido: na base o L punha **B34 em [0,34]** e o X **B54 em [35,89]** — 1cm
de folga, **sem colisão**; o B34 só usa **27cm** para frente do contato,
mas o teste exige `CORNER_B34_ROOM_FT` = 34cm *a partir do contato*; e
`NEIGHBOR_NODE_BOND_CLEARANCE_FT` = 68cm supõe **dois** nós ancorados,
enquanto um nó de travessia lança peça **centrada** (alcance ≤ 27cm).
Duas correções candidatas registradas na seção 43.5 das regras — nenhuma
implementada, as duas mexem no núcleo da amarração.

---

## 2.4 DUAS REGRESSÕES CRÍTICAS da CR-N1 que estavam ESCONDIDAS

Achadas ao conferir **o conteúdo** das duas falhas históricas de
`tests/regression/test_benchmark_baselines.py`. Elas já falhavam antes, e
por isso a piora de dois códigos **críticos** ficou atrás de uma falha
pré-existente. **Nenhuma foi introduzida pela CR-N1b** — os números são
idênticos em `626087b` e nesta branch.

| código | base | CR-N1 | CR-N1b | identidades físicas |
|---|---|---|---|---|
| TGD `JUNCTION_MISSING_BINDING` | 23 | **40** | 40 | **1** (17 fiadas) |
| TP1 `OPENING_BLOCK_INSIDE_DOOR` | 0 | **7** | 7 | **1** (7 fiadas) |

**(a) TGD** — o encontro T em `(−139,5; 470,0)` fica **sem nenhuma peça**.
Na parede principal `W|-140.5,470.0|5.5,470.0|t14.0` os nós 142
(`T_INTERSECTION`, t=1,00cm) e 185 (`L_CORNER`, t=7,00cm) estão a **6,0cm**
um do outro; a fronteira do ponto médio cai em t=4,0cm e deixa o T com
**3,0cm** — nem a menor peça cabe. O nó 185 é de **meio de parede**, então
a isenção da CR-N1b não o alcança.

**(b) TP1** — um **B34 dentro do vão da porta** `W019-O01`
(`t = 564..750cm`), na mesma parede W019 onde a CR-N1 corrigiu os
`POSITION_OVERLAP`. Bloco dentro de vão de porta é erro grosseiro.

Os dois apontam para a mesma causa da seção 43.5: a fronteira do ponto
médio é simétrica demais e, no limite, deixa **os dois** lados sem solução
em vez de dar a peça inteira a um deles. **A decisão de manter ou reverter
a CR-N1 tem de ser tomada com estes dois números na mesa**, ao lado do
ganho `POSITION_OVERLAP` 6→0 / 2→0.

---

## 3. Paredes fora do módulo — reproduzido, etapa exata, decisão pendente

### 3.1 Etapa exata

```
_pier_remaining_snapped_cm(pier, lead, trail)        wall_stepper.py
    remaining = pier - lead - trail + BLOCK_JOINT_CM
    snapped   = 5 * round(remaining / 5)
    |remaining - snapped| > PIER_FIT_TOLERANCE_CM (0,30cm)  ->  None
_pier_ordered_layout  tenta o fallback de junta de ABERTURA (as 3
    combinações de junta de contorno), nenhuma fecha, devolve None
o chamador registra `non_modular` e NÃO lança peça em NENHUMA fiada.
```

### 3.2 Fronteira medida

Fecham `…, 194, 195, 196, 199, 200, 201, …` — **múltiplo de 5cm ± 1cm**
(as três combinações de junta deslocam o alvo 1cm para cada lado), mais
0,30cm de tolerância. `197,943cm` cai no buraco entre 196 e 199.

### 3.3 Achado NOVO — são TRÊS paredes reais, não duas

A terceira é de **99,754cm** (`W|1807.2,-145.1|1813.6,-244.6|t14.0`) e
**não é da seção 42**: 99,754cm **fecha** (junta 1/0 dá resto a 0,25cm do
múltiplo) e uma parede livre desse comprimento recebe **6 peças**. Ela sai
vazia porque o plano real põe nela um nó `AMBIGUOUS` em t=91,55cm **e dois
`X_INTERSECTION` a 0,30cm um do outro** (t=78,83 e t=79,13). Pendência de
código própria, registrada em 42.4.

### 3.4 A decisão que falta

O mecanismo da **opção 2** (modular com folga) **já existe e é testado**:
`pier_cm_floored_to_module(197.943, 0, 0)` = **194cm** (folga de 3,94cm,
menos de um módulo). Ele só não está ligado neste caminho — hoje serve à
guarda física da `CR-BLOCK-FIT-TOLERANCE-C04`. **A opção 2 é ligar
mecanismo existente, não escrever código novo.** Falta a decisão: ligar
significa que o modelo passa a entregar parede com folga declarada em vez
de parede vazia — mudança de contrato, não de implementação.

Reprodutor permanente com controles: `tests/test_non_modular_wall_coverage.py`
(22 testes; 11 controles positivos de medidas vizinhas). **Nenhuma
tolerância nova, nenhum arredondamento de geometria.**

---

## 4. Compensadores × peças especiais — alternativas e custos (SEM decidir)

Enumeração **exaustiva** de `TP1/W003 [170, 474]` (span 304cm, juntas 1/1,
`remaining` = 303cm = 61 módulos): **2 457 composições** fecham.

| opção | melhor composição | comp. | esp. | B19 | peças |
|---|---|---|---|---|---|
| tetos ATUAIS (comp≤1 **e** esp≤1) | **NÃO EXISTE** | — | — | — | — |
| 1 — manter | `B39×6 + B34×1 + C09×3` | 3 | 1 | 0 | 10 |
| 2 — inverter 7/7b | `B39×5 + B34×3` | 0 | 3 | 0 | 8 |
| 3 — liberar 1 B19 | `B39×6 + B34×1 + B19×1 + C09×1` | **1** | 1 | 1 | 9 |

Confirma a contradição normativa: com os dois tetos juntos **não existe
solução**.

**Opção 4 — achado novo desta sessão.** A regra ESCRITA é *"**Proibido
usar 2 ou mais em sequência** no mesmo trecho"*; `MAX_COMPENSATORS_PER_
TRECHO = 1` é uma implementação **mais restritiva** que ela. A melhor
composição da opção 1 admite ordenação em que **nenhum compensador encosta
em outro** (7 peças não-compensadoras para intercalar 3 compensadores). O
que o solver entrega hoje — `B39×7 + C09×2 + C04×1`, os **3 em
sequência** — viola a regra escrita; a **mesma contagem intercalada** não
violaria. Rebaixar `MAX_COMPENSATORS_PER_TRECHO` a preferência forte
faria a família `COMPENSATOR_CONSECUTIVE` (101 TGD / 200 TP1) sumir por
construção. **Atenção**: `COMPENSATOR_EXCESS_IN_RUN` também teria de
passar a medir sequência.

**Nenhuma das quatro foi aplicada.** Registrado em 41.5.

---

## 5. Desempenho — a alavanca real, medida

TGD, mesmo processo, mesmo hardware, sem concorrência:

| | tempo total | rebuilds multi-banda | ARM aceitos | ARM rejeitados |
|---|---|---|---|---|
| base `08495d9` | **99,3s** | 22 | 1 | 19 |
| CR-N1 `626087b` | **47,8s** | 7 | 0 | 6 |
| CR-N1b (esta branch) | **65,0s** | 10 | 0 | 9 |

**A alavanca efetiva não era cache nem triagem barata — era reduzir os
candidatos propostos, e isso vem de consertar a GERAÇÃO.** Cada parede que
deixa de ter prisma forçado no baseline economiza um rebuild inteiro
(~6,5s). A CR-N1 cortou 52% do tempo assim; a CR-N1b devolve parte dele
(restaurar o B34 nos cantos faz três paredes voltarem a ser candidatas),
e ainda fica **35% mais rápida que a base**.

Isto **não substitui** a `CR-PERF-1` (re-solve por escopo com
`dirty_wall_idxs`), que continua sendo a otimização estrutural — mas
mostra que o caminho barato é o mesmo caminho da correção física.

---

## 5.1 Regressão consolidada

`python3 -m pytest tests/ -q` na árvore desta branch:
**964 passed, 2 failed (58min31s)**.

| | passed | failed |
|---|---|---|
| base conhecida | 921 | 2 |
| CR-N1 (`626087b`) | 930 | **5** |
| **esta branch** | **964** | **2** |

As 2 falhas são **as mesmas duas históricas** de
`tests/regression/test_benchmark_baselines.py` (refresh de `baseline.json`
é CR própria) — mas **o conteúdo delas mudou**, e é isso que a seção 2.4
registra: não basta ver "continuam sendo 2".

As 3 falhas novas da CR-N1 estão fechadas; nenhuma nova apareceu. O
aumento de testes vem dos 31 testes novos desta sessão (9 em
`test_neighbor_node_bond_collision.py`, 22 em
`test_non_modular_wall_coverage.py`).

---

## 6. Dívidas que continuam abertas

- **Seção 41** (compensador × peça especial): 4 opções documentadas com
  custo; **decisão do usuário**.
- **Seção 42** (parede fora do módulo): mecanismo pronto, **decisão do
  usuário**.
- **Seção 43.5**: nó de meio com peça centrada — 4 paredes de 124cm com
  amarração degradada; 2 correções candidatas, nenhuma implementada.
- **Seção 43.6 (CRÍTICO, herdado da CR-N1)**: um encontro T sem nenhuma
  peça no TGD e um B34 dentro do vão de porta no TP1 — mesma causa da
  43.5, e o motivo pelo qual a decisão sobre a CR-N1 não é só sobre o
  ganho de `POSITION_OVERLAP`.
- **Seção 42.4**: a parede de 99,754cm com nó `AMBIGUOUS` + dois X a
  0,30cm — investigação própria.
- **2 falhas históricas** de `tests/regression/test_benchmark_baselines.py`
  (refresh de `baseline.json` é CR própria).
- `JUNCTION_HALF_BLOCK_ADJACENT` e a divergência `door_void_violations` ×
  `OPENING_BLOCK_INSIDE_DOOR`: suspeita de erro de **avaliação**, não
  medida a fundo (herdada da varredura).
- C2/G16, CR-B: preservados, não tocados.

---

## 7. Próximos passos objetivos

1. **Decidir a seção 42** — é ligar `pier_cm_floored_to_module`, uma
   linha de contrato; desbloqueia 2 paredes reais visíveis no Revit.
2. **Decidir a seção 41** — a **opção 4** é a única que não contraria
   nenhuma regra escrita; desbloqueia a família compensador inteira
   (64% das identidades do TP1).
3. **Seções 43.5 + 43.6 (prioridade sobre as demais)** — corrigir a
   fronteira contra nó de meio: devolve as 4 paredes de 124cm, apaga as 29
   identidades genuinamente novas da CR-N1b e, principalmente, resolve o
   encontro T sem peça e o bloco dentro do vão de porta.
4. **Seção 42.4** — a parede de 99,754cm (dois X a 0,30cm um do outro).
5. Só então `CR-PERF-1` (re-solve por escopo).
