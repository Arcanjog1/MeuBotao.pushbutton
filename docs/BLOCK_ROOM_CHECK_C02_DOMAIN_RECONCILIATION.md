# C02 — RECONCILIAÇÃO DE DOMÍNIO

> **Veredito: `NODE_RECOGNITION_FIX_REQUIRED`** — o defeito não é o room
> check. É o solver não distinguir **dois padrões humanos diferentes de
> cruzamento em X**. Detalhe por ramo em §8.

Base: `origin/main` @ `3ebcd9b6…`, HEAD anterior `b70ba5d`.
Zero produção, zero regras normativas, zero baseline/reference/input.
Artefatos: `nuvem/benchmark/diagnostics_c02/`.

---

## 1. O que a rodada anterior deixou de pé (preservado)

Tudo abaixo continua valendo e **não** foi revisitado por inércia:

- o déficit vem de **coordenadas de entrada** (parede de 593,997 / 123,98cm),
  não de erro de float;
- **~1234 avaliações ≠ 1234 peças** — são 7 identidades físicas;
- **X @ 0,05cm recupera 51 B54 finais em 4 nós**;
- a medição do room check é **invariante** (translação, rotação exata,
  espelho, reversão, permutação);
- **T e L têm contratos físicos diferentes do X** (27cm e 34cm, sem junta).

O que esta rodada **corrige** da anterior está marcado em §5.

---

## 2. O nó X é real — não é artefato

Reconstrução completa em `node_reconciliation.json`. Para os 5 nós
investigados, antes **e** depois de `extend_wall_ends_to_junctions`:

| | TP1 (6607,25; 594,93) | TGD (1263,518; −507,951) |
|---|---|---|
| parede longa | 1344,00cm — **ATRAVESSA** o ponto (t=61,98) | 593,997cm — **ATRAVESSA** (t=61,997) |
| parede curta | 123,98cm — **ATRAVESSA** o ponto (t=61,99) | 124,005cm — **ATRAVESSA** (t=62,002) |
| extend mudou algo? | **não** (`walls_already_extended`) | **não** |
| nó do solver | `X_INTERSECTION`, `crossing_walls=[2, 20]` | `X_INTERSECTION`, `crossing_walls=[17, 91]` |
| gabarito tem as mesmas 2 paredes? | **sim** (W003 1344,00 / W021 123,98) | não (fragmentação — ver §7) |

**Classificação: (A) encontro X estrutural real.** Duas paredes contínuas
se cruzando no meio. Não é (B) T/L disfarçado, não é (D) fragmentação
artificial, não é (E) artefato de reconstrução — no TP1 o gabarito registra
**as mesmas duas paredes com os mesmos comprimentos**.

> O gabarito não registra `junction` no ponto do cruzamento (W003 só tem 6
> junções T, todas em pontas; W021 só tem 2 L, nas pontas). Isso é
> **limitação da representação** `junctions` do `reference.json`, que grava
> junções de ponta — **não** é prova de que o humano não vê o cruzamento.
> A prova do que ele faz está nas peças, §3.

---

## 3. O vão de 16cm é a passagem física da transversal

`16,0cm = 14,0 (espessura da parede que passa) + 1,0 + 1,0 (junta dos dois
lados)`. Exato, nos quatro casos do TP1.

O que o **gabarito** faz em W021 (123,98cm), nas duas primeiras fiadas:

```
fiada 0:  B39 [14,99–53,99]                      B39 [69,99–108,99]
fiada 1:  B34 [0–34] B19 [34,99–53,99]           B19 [69,99–88,99] B34 [89,98–123,98]
                          └──── vão 16,0cm, centrado em t=61,99 ────┘
                                  (= o ponto do cruzamento)
```

E na parede longa W003, **nas duas fiadas**, há bloco cobrindo t=61,98
(`B39 [55–94]` na fiada 0, `B39 [35–74]` na fiada 1).

**A longa passa cheia sempre; a curta abre o vão sempre. Não há alternância.**

### Prova de ownership, por fiada, em todos os 43 nós X

`x_ownership_evidence.json` mede quem ocupa o ponto do cruzamento em cada
fiada, no solver e no gabarito:

| | nós comparáveis | gabarito |
|---|---|---|
| transversal **longa** (≥200cm) | 22 | **`ALTERNA` em 22/22** (amarração em X) |
| transversal **curta** (~124cm) | 4 | **`PASSAGEM` em 4/4** (a longa é dona) |

**Separação perfeita, zero contraexemplos** — mas o lado `PASSAGEM` tem
**n=4**, o que sustenta a conclusão sem torná-la definitiva sozinha (§6).

E a assinatura numérica fecha com a geométrica: os **8** nós X do corpus
cujo padrão é passagem são **exatamente** os 8 com `room` entre **27,90 e
28,002cm** — nenhum outro nó X do corpus cai nessa faixa (os de amarração
têm `room ≥ 38,01cm`). Não é coincidência: uma parede de ~124cm com
amarração nas duas pontas dá `124/2 − 34 = 28,0cm` de folga por definição.

### Respostas às 7 perguntas da §3 do pedido

1. **O solver cria um X que não existe no modelo humano?** Não. O X existe:
   as duas paredes atravessam o ponto, e o gabarito tem as duas com a mesma
   geometria. O que difere é o **tratamento**, não o reconhecimento.
2. **O humano representa por paredes fragmentadas?** Não no TP1 (mesmas
   paredes, mesmos comprimentos). No TGD sim — ver §7.
3. **A transversal ocupa fisicamente o vão?** **Sim**, exatamente:
   16,0cm = espessura + 2 juntas.
4. **Há amarração em outra parede que garanta o nó?** **Não neste padrão.**
   A longa passa cheia nas duas fiadas — não se reveza com a curta. Essa
   ausência de alternância é o que define `PASSAGEM`.
5. **Um B54 centrado criaria sobreposição ou substituiria solução humana
   válida?** **Não cria sobreposição** (§5) — **substitui uma solução humana
   válida**, e ocupa mais do vão que o humano deixa livre (54cm contra os
   34cm de hoje).
6. **O B34 atual também está errado nesses casos?** **Sim** — pela mesma
   razão, e já hoje: nas fiadas ímpares o solver cobre o cruzamento com B34
   onde o humano deixa vão. O B54 erraria **mais**, não diferente.
7. **A correção correta é de quê?** **Reconhecimento / ownership do nó X.**
   Não é room check, não é fragmentação, não é composição de trecho.

---

## 4. O room check de hoje não tem critério — é loteria de desenho

Os 8 nós de padrão passagem são fisicamente equivalentes. O solver os trata
de forma **diferente**, e a diferença é imprecisão de desenho:

| `room` medido | nós | decisão do solver | falta para 28,00 |
|---|---|---|---|
| 28,000 – 28,002 | **3** | **aceita B54** | — (sobra 0,000–0,002) |
| 27,900 – 27,997 | **5** | **degrada para B34** | 0,003 – 0,100 |

Mesmo tipo de nó, mesma função estrutural, peças diferentes — decidido por
**0,005cm**. Nenhum critério estrutural participa da escolha.

Aplicar `+0,05cm` tornaria os 8 **uniformes com B54** — uniformemente
divergentes do gabarito. Corrigiria a inconsistência **na direção errada**.

---

## 5. Correção da rodada anterior

A rodada anterior classificou os nós afetados como `QUALITY_REGRESSION_RISK`
sugerindo que o B54 "invadiria" o vão humano. Duas precisões, medidas agora:

- **Não há colisão.** `x_ownership_evidence.json`: **0 colisões** em 43 nós.
  Em cada fiada, exatamente uma das duas paredes ocupa o cruzamento. A
  alternância do solver é geometricamente válida — é amarração em X legítima
  pela regra vigente.
- **A divergência já existe hoje**, com B34. O epsilon a **aumenta em grau**
  (34 → 54cm no vão que o humano deixa livre), não em espécie.

O risco continua real, mas o enunciado correto é: *o epsilon amplia uma
divergência de padrão existente e uniformiza os 8 nós na direção contrária
ao gabarito* — não *o epsilon introduz uma invasão nova*.

---

## 6. Separação das camadas de confiança

| camada | conteúdo |
|---|---|
| **REGRA ATUAL APROVADA** | `REGRAS_MODULACAO_BLOCOS.md` §5 e §18.1: *"toda cruz usa B54"* — dois B54 a 90°, centrados no nó, células centrais alinhadas, validado por `validate_x_intersection`. |
| **EVIDÊNCIA HUMANA** | 22/22 cruzamentos de transversal longa: amarração alternada (**confirma a regra**). 4/4 cruzamentos de transversal ~124cm: passagem sem amarração na curta (**contradiz a regra**). |
| **INTERPRETAÇÃO GEOMÉTRICA** | Numa parede de ~124cm com B34 nas duas pontas sobram 56cm centrais; um B54 ocuparia 54 deles, e a parede inteira viraria três peças de amarração encostadas, sem enchimento. O humano prefere gastar o meio com a passagem da transversal. |
| **HIPÓTESE** | O critério de passagem é *"a transversal é curta demais para amarrar no meio além das duas pontas"* — mensurável como `room ≈ metade − 34cm` (o que hoje é exatamente o caso `room ≈ 28cm`). |
| **DECISÃO HUMANA NECESSÁRIA** | Qual é o critério real (§9). Não inventado aqui. |

### CONFLITO REGISTRADO (não resolvido, regra não alterada)

> A regra §18.1 (`toda cruz usa B54`) e a evidência humana medida **divergem**
> em 4 de 26 cruzamentos comparáveis do corpus — todos com parede transversal
> de ~124cm. A regra **não foi alterada**: registrar o conflito e aguardar a
> decisão do usuário é o que o `CLAUDE.md` exige ("nunca apagar uma regra
> anterior em silêncio"; "a orientação mais recente do usuário tem
> prioridade"). Enquanto não houver decisão, **a regra vigente continua
> sendo a regra**.

---

## 7. Por que o TGD é inconclusivo

No TGD as paredes do nó afetado **não existem** no gabarito com a mesma
geometria: o solver vê uma vertical de 593,997cm; o gabarito registra
W008 com **1344,00cm** (a mesma parede, sem os cortes do solver). É a
fragmentação já catalogada como `BENCH-WALLMODEL-FRAGMENTS`.

Por isso a evidência confiável desta reconciliação é **só do TP1**, e os
4 nós de passagem do TGD entram como `SEM_PAREDE`, não como confirmação.

---

## 8. Reavaliação do C02

| ramo | classificação | por quê |
|---|---|---|
| **C02 / X (room check)** | **(D) não implementar no corpus atual** | 100% da evidência do C02 em X está nos nós de padrão **passagem**. Se o reconhecimento de passagem for implementado, **restam ZERO** identidades X com déficit ≤0,05cm no corpus — o C02/X perde todo o seu corpus de evidência. |
| **Reconhecimento do nó X** | **(B) substitui o C02** | É a correção que reproduz a geometria correta, e de quebra elimina a loteria de §4. |
| **C02 / T (12 B54 no TGD)** | **(E) inconclusivo** | Corpus independente (6 identidades TGD + 4 TP1), com contrato diferente (27cm, sem junta), **não reconciliado** nesta rodada. Não herda nem a aprovação nem a reprovação do ramo X. |
| **C02 / L** | não implementar | 1 identidade no corpus inteiro; risco desproporcional. |

Nenhuma opção foi escolhida por produzir mais B54 — a opção que produz
mais B54 (epsilon em X) é justamente a rejeitada.

---

## 9. COMO ESSE ENCONTRO DEVE SER MODULADO?

Dois padrões distintos aparecem no corpus. O primeiro está resolvido; o
segundo depende de você.

### PADRÃO 1 — cruzamento com transversal longa (≥200cm) — **resolvido, nada a decidir**

```
             │ longa                    fiada par:  a peça da horizontal ocupa o cruzamento
   ══════════╪══════════ longa          fiada ímpar: a peça da vertical ocupa o cruzamento
             │                          (as duas se revezam = amarração)
```

| | |
|---|---|
| solver hoje | `ALTERNA` — dois B54 a 90°, centrados, alternando entre fiadas |
| humano | `ALTERNA` — o mesmo |
| diferença | **nenhuma**, em 22 de 22 nós comparáveis |
| recomendação | manter. A regra §18.1 está **confirmada** para este padrão. |

### PADRÃO 2 — cruzamento com transversal curta (~124cm) — **decisão sua**

```
             │ longa (1344cm)
   ═══╡  16 ╞═══   curta (123,98cm), com B34 de amarração nas DUAS pontas
             │                 vão de 16,0cm = 14 (espessura) + 2 juntas
```

| | |
|---|---|
| **solver hoje** | `ALTERNA`: fiada par deixa o vão de 16cm; **fiada ímpar cobre o cruzamento** com B34 (5 nós) ou B54 (3 nós) — a peça decidida por 0,005cm de imprecisão de desenho |
| **humano** | `PASSAGEM`: a longa passa cheia nas **duas** fiadas; a curta deixa o vão de 16cm nas **duas**. Nunca amarra no meio. |
| **diferença** | nas fiadas ímpares o solver põe peça de amarração onde o humano deixa a passagem livre |
| **recomendação técnica** | reconhecer o padrão de passagem e **não amarrar no meio da transversal curta** — nem B54, nem B34. Isso também elimina a inconsistência de §4. |

**As duas perguntas objetivas:**

> **P1.** Numa parede curta (~124cm) que já tem amarração B34 nas duas
> pontas e é cruzada no meio por outra parede, o correto é **deixar a
> passagem livre** (como no gabarito) ou **amarrar também no meio** (como a
> regra §18.1 diz hoje)?

> **P2.** Se for deixar livre: o critério é o **comprimento da transversal**
> (ex.: abaixo de ~150cm), é **não sobrar espaço para amarrar no meio além
> das duas pontas** (`room < 28cm + folga`), ou é outro que você usa em
> projeto?

Sem P1 respondida, nada muda em produção: nem o epsilon do C02, nem o
reconhecimento de passagem.

---

## 10. Se ainda houver um caso legítimo de room check

Registrado para não se perder, **sem implementar**:

- tolerância **dedicada**, nunca `PIER_FIT_TOLERANCE_CM = 0,30cm`;
- **27,9cm continua fora** — é descentralização real do nó, não imprecisão;
- absorção **só contra fronteira COM junta**, provada caso a caso;
- proibido invadir abertura, ponta livre, reserva estrutural sem folga, ou
  peça de outra parede;
- o nome não pode ser "noise": o que se absorve é imprecisão de desenho.

---

## 11. Entregáveis

Novos em `nuvem/benchmark/diagnostics_c02/`:

| arquivo | conteúdo |
|---|---|
| `node_reconciliation.json` | geometria completa dos 5 nós: input cru, pós-extend, nó do solver, paredes e peças do gabarito, aberturas |
| `x_node_human_pattern.json` | os 43 nós X classificados (`AMARRACAO` / `PASSAGEM` / `OUTRO`) + vãos por fiada |
| `x_ownership_evidence.json` | quem ocupa o cruzamento em cada fiada, solver × gabarito, e o teste de colisão |
| `tools_c02_reconcile.py`, `tools_c02_x_pattern.py`, `tools_c02_ownership.py` | reprodutíveis, read-only |

Produção: **zero**. `REGRAS_MODULACAO_BLOCOS.md`: **não alterado** (conflito
registrado aqui, §6). `baseline.json` / `reference.json` /
`reference_score.json` / `input.json`: **zero alterações**.

---

## 12. Veredito e próxima CR

**`NODE_RECOGNITION_FIX_REQUIRED`**, com:

- **`DO_NOT_IMPLEMENT_C02`** para o ramo X (room check) — o corpus de
  evidência dele desaparece quando o reconhecimento estiver certo;
- **`DOMAIN_DECISION_REQUIRED`** para destravar: P1 e P2 de §9;
- **`INCONCLUSIVE`** para o ramo T — corpus independente, não reconciliado.

**Próxima CR correta:** `CR-BLOCK-X-NODE-PASSAGE-RECOGNITION` — ensinar
`solve_x_intersection` a distinguir cruzamento-com-amarração de
cruzamento-de-passagem, e não amarrar no meio da transversal curta.

Por quê, e não o epsilon:
1. ataca a causa (padrão do nó), não o sintoma (0,003cm de folga);
2. elimina a loteria de §4 — hoje o mesmo nó recebe B54 ou B34 por 0,005cm;
3. aproxima do gabarito nos 4 casos comparáveis, em vez de afastar;
4. torna o C02/X desnecessário, em vez de acumular duas correções que se
   anulam.

**Pré-requisito absoluto: P1 respondida.** Ela decide se a regra §18.1 vale
sem exceção ou ganha um caso de passagem — e isso é decisão de domínio, não
de código.

**PAREI.** Nada implementado, nenhuma outra CR iniciada, nenhum
monitoramento criado.
