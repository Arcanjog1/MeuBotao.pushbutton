# BENCH-OPENING-RECONSTRUCTION — evidência e experimento controlado

> **Diagnóstico.** Diff de produção = ZERO. Nenhum
> `reference.json` / `input.json` / `baseline.json` / `reference_score.json`
> oficial foi alterado. O candidato deste diretório **não** é referência
> aprovada.

---

## 1. O sintoma que motivou a investigação

Rodando os validadores sobre o **próprio gabarito humano**
(`reference.json`), medido nesta sessão e idêntico ao relatado pela
revisão independente do C04:

| projeto | `OPENING_BLOCK_CROSSES_JAMB` no gabarito | distribuição |
|---|---|---|
| `torre_easy_lo_r00_tgd` | **208** | 187 em 15,000cm + 8 em 14,990cm + 7 em 0,120cm + 6 em 0,110cm |
| `torre_easy_lo_r00_tp1` | **209** | 187 em 15,000cm + 8 em 14,990cm + 14 em 0,120cm |

Ou seja: **195 achados de ~15,0cm em cada projeto**, todos em **porta**,
todos em peças `B34` (185), `B34_C` (4) e `B19` (6).

---

## 2. Causa-raiz — LOCALIZADA, não hipótese

`nuvem/core/engine/opening_audit.py`,
`detect_wall_openings_from_courses` (l. 145-179):

```python
if (abs(gs2 - run_start) <= OPENING_RUN_EDGE_MATCH_TOLERANCE_CM      # 15.0
        and abs(ge2 - run_end) <= OPENING_RUN_EDGE_MATCH_TOLERANCE_CM):
    ...
run_start = min(run_start, gs2)      # <-- UNIÃO
run_end   = max(run_end,  ge2)       # <-- UNIÃO
```

A tolerância existe para reconhecer que o vazio de duas fiadas vizinhas é
**a mesma abertura** apesar do desencontro de junta — propósito legítimo,
documentado no próprio comentário. **O defeito é a agregação:** o vão
gravado vira o **ENVELOPE** (união) dos vazios de todas as fiadas, então a
tolerância de *identidade* vaza para a *geometria* do vão.

Onde a jamba coincide com um nó T/L, as fiadas alternam:

```
W003 (TGD), vão gravado [579,765]:
  fiada  0  ... C09 570–579          <- reserva de nó VAZIA nesta fiada
  fiada  1  ... B34 560–594          <- peça de amarração ATRAVESSA o nó
  fiada  2  ... C09 570–579
  fiada  3  ... B34 560–594
                    ^^^ 594 − 579 = 15,0cm = B34 − B19 = 34 − 19
```

O envelope pega `579`; o consenso (interseção) pega `594`. As peças das
fiadas ímpares passam então a "invadir" exatamente **15,0cm** — o valor da
própria tolerância.

**Medição:** 19 aberturas por projeto têm `spread_inicio = spread_fim =
15,0cm` (arquivo `reconstruction_evidence.json`). Em 116 dos 195 achados o
nó T/L está a **8,0cm** da jamba gravada e a peça "invasora" **cobre o
ponto do nó**.

---

## 3. Confronto com a geometria MEDIDA do Revit — o dado decisivo

O `input.json` do **TGD** carrega aberturas `confidence="measured"`, com
`source_element_id` do Revit. O do TP1 é inteiramente reconstruído.

### 3.1 As larguras da assinatura não existem no modelo real

| largura de porta | no `input.json` MEDIDO (TGD) | no gabarito reconstruído |
|---|---|---|
| 91,0cm | **38** | 34 |
| 186,0cm | **0** | **10** |
| 131,0cm | **0** | **6** |
| 101,0cm | 2 | 0 |

`186 − 2×15 = 156`; `131 − 2×15 = 101`. **101cm é largura medida real**;
186 e 131 **não existem** no Revit.

### 3.2 O consenso é o espaço entre DUAS PAREDES separadas

Confrontando o consenso com os trechos de parede **medidos** no mesmo eixo
(`check_axis_gap.py`):

| projeto | consenso == buraco entre paredes medidas | divergente | sem geometria medida |
|---|---|---|---|
| TGD | **16 de 19** | 3 | 0 |
| TP1 | 0 | 19 | 0 (o TP1 **não tem** geometria medida) |

Exemplos (TGD):

```
W003-O01  gravado [579,765]  consenso [594,750]  == BURACO MEDIDO [594.0,750.0] entre W017 e W015
W004-O03  gravado [904,1035] consenso [919,1020] == BURACO MEDIDO [919.0,1019.7] entre W108 e W044
W046-O01  gravado [94,280]   consenso [109,265]  == BURACO MEDIDO [109.0,265.0] entre W104 e W102
```

**Conclusão:** naqueles 16 casos aquilo **não é uma porta**. É o espaço
entre **duas paredes fisicamente separadas** que a reconstrução fundiu numa
parede só (`WALL_SPLIT_GAP_CM = OPENING_GAP_MAX_CM = 260cm` — um vão de
156cm fica abaixo do teto e vira "abertura" em vez de separação).

---

## 4. Classificação exigida (A/B/C/D/E) — por família, não em bloco

| família | n (por projeto) | classificação | base |
|---|---|---|---|
| **195 × 15,0cm** | 195 | **(A) ERRO DE RECONSTRUÇÃO DA REFERÊNCIA** | envelope provado (§2) + largura inexistente no Revit (§3.1) + 16/19 consensos == buraco entre paredes medidas (§3.2) |
| **13–14 × 0,11–0,12cm** | 13 (TGD) / 14 (TP1) | **(D) MISTO / limiar** | são aberturas **reais** (par medido a ≤0,24cm do centro, largura 91,0 ≡ 91,0). Invasão de ~1,2mm vinda de coordenada fracionária de extração (jamba em 18,88 contra peça em 19,00), logo acima do `OVERLAP_TOLERANCE_CM = 0,1cm` do validador |
| **3 divergentes do TGD** (`W006-O01`, `W015-O01`, `W052-O02`) | 3 | **(E) INCONCLUSIVO** | têm a assinatura de envelope, mas o buraco medido no eixo não bate exatamente com o consenso (paredes medidas fragmentadas ali) |
| **TP1 inteiro** | 19 aberturas | **(E) INCONCLUSIVO por falta de fonte** | assinatura idêntica à do TGD (mesmos `wall_id`, mesmos vãos), mas o TP1 **não carrega geometria medida** para adjudicar |

**Nenhuma invasão foi declarada falsa em bloco.** A revisão do C04 provou
que 41 regressões novas eram físicas reais; aqui o critério é a evidência
por família, não o volume.

---

## 5. Experimento controlado — o candidato

Correção aplicada **somente** às 19 aberturas com a assinatura: jamba do
**envelope** → **consenso**. Blocos, paredes, nós e fiadas do gabarito
**intocados**.

### 5.1 Invariantes de segurança verificadas

| invariante | TGD | TP1 |
|---|---|---|
| paredes / fiadas / blocos / aberturas idênticos | **sim** (97 / 1379 / 12508 / 94) | **sim** (96 / 1365 / 12703 / 92) |
| aberturas intocadas | 75 | 73 |
| aberturas **estreitadas** (nunca alargadas) | 19 | 19 |
| aberturas **deslocadas** (centro movido) | 2 — deslocamento de **0,005cm** cada (as duas com spread 14,99/15,00) | 2, idem |

Nenhuma abertura foi apagada, criada, alargada ou movida de parede.

### 5.2 Efeito sobre os validadores, no próprio gabarito

| código | TGD atual → candidato | TP1 atual → candidato |
|---|---|---|
| `OPENING_BLOCK_CROSSES_JAMB` | 208 → **13** (**−195**) | 209 → **14** (**−195**) |
| `OPENING_BLOCK_INSIDE_DOOR` / `_WINDOW` | 0 → 0 | 0 → 0 |
| `OPENING_SOLID_BELOW_SILL_MISSING` | 0 → 0 | 0 → 0 |
| `OPENING_MISSING_COUNTER_LINTEL` | 21 → 21 | 21 → 21 |
| `OPENING_MISSING_LINTEL` | 56 → **60** (+4) | 53 → **57** (+4) |
| `COVERAGE_GAP_IN_ROW` | 626 → **648** (+22) | 615 → **637** (+22) |
| `PRISM_CONTINUOUS_JOINT` | 126 → **129** (+3) | 122 → **125** (+3) |

**O candidato não é grátis, e isso é a parte importante.** Os 22
`COVERAGE_GAP_IN_ROW` novos são, medidos um a um, **exatamente as tiras de
15,0cm** que a reserva de nó deixa vazias nas fiadas alternadas:

```
W003 fiada 11 | vazio de 15.0cm em t=579.0..594.0cm ... fora de abertura e fora de zona de amarracao
W003 fiada 11 | vazio de 15.0cm em t=750.0..765.0cm ... fora de abertura e fora de zona de amarracao
```

Isto é, estreitar a abertura **troca um artefato por outro, menor**: o
validador de cobertura não reconhece a tira como zona de amarração de nó.

### 5.3 Efeito sobre o SOLVER (TP1) — o custo real do defeito

O `input.json` do TP1 carrega as **mesmas** aberturas reconstruídas, então o
defeito chega ao solver, não só à métrica. Rodando o solver com o
`input.json` oficial e com o candidato (projeto copiado para diretório
temporário; **nada oficial alterado**):

| | `input.json` atual | `candidate_input` |
|---|---|---|
| fingerprint físico | `7e420377e657` | `0d2786a1635d` |
| peças | 18417 | 18131 (−286) |
| **erros críticos** | **469** | **311** (**−158**) |
| `OPENING_BLOCK_CROSSES_JAMB` | **168** | **0** (**−168**) |
| `PRISM_CONTINUOUS_JOINT` | 256 | 252 (−4) |
| `PRISM_STAGGER_BELOW_TARGET` | 1370 | 1308 (−62) |
| `COMPENSATOR_CONSECUTIVE` | 1443 | 1429 (−14) |
| `COVERAGE_GAP_IN_ROW` | 327 | **417** (**+90**) |
| `COVERAGE_ROW_MOSTLY_EMPTY` | 18 | **32** (**+14**) |

**As 168 invasões de jamba do TP1 são 100% consequência da abertura
inflada** — desaparecem inteiras quando o vão recebe a largura de consenso.
Em troca, a cobertura piora (+90/+14), pela mesma razão da §5.2: as tiras
de 15cm passam a ser parede a preencher, e 15cm não comporta nem um B19
(19cm).

**Isto NÃO prova que o candidato é a correção certa** — prova que o defeito
de reconstrução é grande e mensurável, e que corrigi-lo **só** estreitando a
abertura não fecha a conta.

---

## 6. O que a evidência diz sobre a correção definitiva

Em 16 de 19 casos do TGD, a geometria medida diz que ali **não há parede**:
são dois trechos separados. Portanto a correção correta provavelmente **não
é** "estreitar a abertura", e sim **separar a parede** — e com a parede
separada as tiras de 15cm deixam de ser cobertura devida e os +90/+22
somem sozinhos.

Isso muda a estrutura do gabarito (uma parede vira duas), tem impacto em
`evaluation_scope`, em pareamento humano e em toda métrica por parede.
**É decisão de gabarito, exige autorização humana explícita, e é o motivo
de esta sessão parar aqui.**

---

## 7. Limitações declaradas

1. O TP1 **não tem geometria medida**: os 19 casos dele são adjudicados por
   analogia com o TGD (mesmos `wall_id`, mesmos vãos, mesma assinatura),
   não por evidência própria. Dado que falta: um dump `measured` do TP1
   (equivalente ao `input.json` do TGD) ou o `input_real.json` do TP1.
2. Três casos do TGD (`W006-O01`, `W015-O01`, `W052-O02`) ficam
   **INCONCLUSIVE**: têm a assinatura, mas o eixo medido está fragmentado e
   o buraco não bate exatamente.
3. A família de 0,11–0,12cm **não** foi corrigida por este candidato e
   permanece aberta: precisa de decisão sobre coordenada fracionária na
   extração (18,88 vs 19,00), não sobre o detector de aberturas.
4. Nenhuma medição foi feita no Revit ao vivo (MCP) nesta sessão.
5. O `piloto_sintetico_2x2` não tem gabarito humano e ficou fora.
