# Extração forense do projeto humano nº 2 — BUTANTÃ R08_LT
## Sistema de aberturas resolvido com CANALETAS

> **Natureza deste documento**: **evidência, não norma**. Tudo aqui foi **medido**
> via pyRevit Routes no documento Revit aberto, em modo **somente leitura**
> (nenhuma `Transaction` foi aberta, nada foi criado, movido, apagado ou salvo).
> Nenhum padrão descrito abaixo foi promovido a regra do solver e nenhum arquivo
> de produção (`nuvem/core/**`, benchmark, baseline, gabarito) foi tocado.
>
> Data da extração: **2026-09-09**.
> Projeto A (comparação): `TORRE EASY-LO-R00`, já versionado em
> [`../REPORT_HUMAN_REVIT_MODULATION.md`](../REPORT_HUMAN_REVIT_MODULATION.md).

---

## RESPOSTA DIRETA À HIPÓTESE

O usuário levantou a hipótese de que este projeto **não** usa verga/contraverga
e sim **canaletas**. A hipótese foi tratada como não confirmada e testada
geometricamente.

**A hipótese está CONFIRMADA, com três provas independentes:**

1. **Prova por ausência.** As famílias `VERGA PORTA`, `VERGA JANELA`,
   `VERGA JANELA 3 FUROS` e `CONTRAVERGA` **estão carregadas no documento**
   (69 tipos em Modelos genéricos) e têm **0 (zero) instâncias colocadas**.
   O projeto tinha a ferramenta na mão e escolheu não usá-la.
2. **Prova por presença.** Em **47/47 portas (100%)** e em **58/61 janelas
   (95,1%)** a fiada imediatamente apoiada no topo do vão é composta
   **exclusivamente por famílias de canaleta**. Abaixo do peitoril, **89/89
   (100%)** das aberturas com peitoril têm canaleta.
3. **Prova por cota.** A base da canaleta coincide com o topo do vão com
   **offset 0,00 cm em 135/136** casos, e o topo da canaleta inferior coincide
   com o peitoril com **offset 0,00 cm em 88/89** casos. Não é coincidência de
   posição: é assentamento deliberado.

**Diferença estrutural em relação ao TORRE EASY**: lá a peça especial tem
**9 cm de altura** e é uma peça dedicada (verga). Aqui a peça especial é uma
**fiada inteira de 19 cm** de canaleta, que ocupa a fiada da grade modular.
O reforço deixa de ser um elemento sobreposto e passa a ser **uma fiada da
própria alvenaria**.

---

## A. MODELO ANALISADO

| Item | Valor |
|---|---|
| Documento | `BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO).rvt` |
| Caminho | `T:\EM ANDAMENTO\CIV0495_BUTANTA\PRANCHAS\BIM\REVIT\` |
| Versão Revit | **2026** (build 26.3.0.37) |
| Unidade de comprimento | **centímetros** |
| Workshared | não |
| Níveis no documento | 13 |
| Elementos não-tipo | **203.173** |
| Tipos (`ElementType`) | 3.764 |
| **Peças de alvenaria (Modelos genéricos)** | **65.747** |
| **Aberturas (Mobiliário)** | **142** |
| Paredes (`Wall`) nativas | **0** |
| Portas / Janelas nativas | **0** |

### A.1 Método de acesso (limitação encontrada)

O servidor MCP `revit-pyrevit` aponta para a porta **48884** e não respondeu
(`All connection attempts failed`). O servidor pyRevit Routes desta sessão do
Revit está na porta **48885**. A extração foi feita por `POST` direto em
`http://localhost:48885/revit_mcp/execute_code/`, que é **o mesmo endpoint** que
a ferramenta MCP usa — apenas com a porta correta. Cliente em
[`_scripts/rmcp.py`](_scripts/rmcp.py).

O handler `execute_code` **não abre transação automaticamente** (verificado no
código da extensão antes de usar), e nenhum script enviado abriu uma.

### A.2 Níveis que efetivamente têm modulação

| Nível | Datum Z interno (cm) | Peças | Aberturas instanciadas |
|---|---:|---:|---:|
| PAV. TÉRREO | −350 | 252 | 0 |
| 1º PAVIMENTO | 0 | 6.634 | 44 |
| 2º PAVIMENTO | 272 | 6.727 | 43 |
| 3º PAVIMENTO | 544 | 6.727 | 0 *(clone)* |
| 4º PAVIMENTO | 816 | 6.727 | 0 *(clone)* |
| 5º PAVIMENTO | 1.088 | 6.727 | 0 *(clone)* |
| 6º PAVIMENTO | 1.360 | 6.727 | 0 *(clone)* |
| 7º PAVIMENTO | 1.632 | 6.727 | 0 *(clone)* |
| 8º PAVIMENTO | 1.904 | 6.727 | 0 *(clone)* |
| 9º PAVIMENTO | 2.176 | 6.784 | 43 |
| BARRILETE | 2.448 | 4.292 | 12 |
| COBERTURA | 2.808 | 696 | 0 |

**Pé-direito modular: 272 cm entre pavimentos.**

### A.3 Descobertas estruturais sobre o modelo (afetam toda leitura futura)

1. **Não existe `Wall`, `Door` nem `Window` neste documento** — igual ao
   TORRE EASY. A alvenaria é só `FamilyInstance` de **Modelos genéricos**.
2. **A chave de parede é o parâmetro de texto `Parede`**, presente em
   **65.747/65.747** peças e **142/142** aberturas. O formato aqui é
   `"PARn - <faixa de pavimento>"`, ex.: `PAR20 - 1º PAVIMENTO`,
   `PAR10 - 2º PAVIMENTO AO 8º PAVIMENTO (TIPO)`. São **136 valores distintos**
   (~34 eixos de parede × faixas de pavimento) e **340 grupos** `(Parede, nível)`.
   **Cada grupo tem um único eixo** (0 grupos com eixo misto) — o agrupamento do
   humano é geometricamente limpo.
3. **Os pavimentos 3º a 8º são clones geometricamente exatos do 2º.**
   Comparando a assinatura `(família, bbox com Z relativo ao datum)` de todas as
   peças: **6.727/6.727 idênticas, 0 diferenças, para os 6 pavimentos**.
   Consequência: as 43 aberturas instanciadas no 2º PAVIMENTO valem para os 3º–8º.
   Onde os arquivos de dados usam essa propagação, o campo
   `propagated_from_opening_id` marca o registro como **INFERIDO**.
4. **Toda a modulação é gêmea de uma família de cor.** A categoria *Vegetação*
   tem exatamente uma instância `Cor <peça>` para cada peça de Modelos genéricos
   (65.747 ↔ 65.747). São elementos de representação gráfica, **não** alvenaria,
   e foram excluídos de todas as contagens.
5. **A `BoundingBox` tem +2 cm no comprimento** (1 cm de junta por face): bloco
   de 39 → bbox de 41. Confirmado no sólido de **20/20 famílias**. Em `Z` a bbox
   é exata (19 cm). Todos os apoios deste relatório são publicados nas duas
   formas: `_bbox` (bruto) e `_solid` (−1 cm por ponta, o apoio real de alvenaria).
6. **Divergência bbox × sólido em `BLOCO 54 CORTADO - 14x9x54`**: a bbox informa
   **19 cm** de altura, o sólido tem **9 cm**. Mesma armadilha já registrada no
   TORRE EASY. Quem ler só a bbox classifica errado 18 peças.
7. **Os parâmetros `Lintel` e `Arranque` existem em todas as peças e estão
   zerados em 65.747/65.747.** O projeto **não** marca verga por parâmetro —
   toda classificação tem de ser geométrica.
8. **Modelo 100% ortogonal**: 65.747/65.747 peças com rotação múltipla exata de
   90° (0°, 90°, 180°, 270°).
9. **Espessura única**: 65.747/65.747 peças com 14 cm de largura.

---

## B. COMO O PROJETO REPRESENTA UMA ABERTURA

Uma única família de **Mobiliário** — `Abertura de janela para paredes de blocos`
— representa **todas** as 142 aberturas, com parâmetros de instância:

| Parâmetro | Papel |
|---|---|
| `Título_abertura` | rótulo: `PORTA` (47) · `JANELA` (61) · `ABERTURA` (34) |
| `Largura_abertura` | largura do vão |
| `Altura_abertura` | altura do vão |
| `Altura_peitoril` / `Peitoril` | peitoril |
| `Parede` | chave de agrupamento |

**O rótulo é coerente com a geometria em 134/142 (94,37%)**: todos os 47
`PORTA` têm peitoril 0. As 8 divergências são vãos rotulados `ABERTURA` com
peitoril 0 — que geometricamente são portas.

**A bbox da abertura dá o vão exato no eixo da parede** (não tem a folga de
2 cm dos blocos), e vai de `datum do nível` até `peitoril + altura`. Ou seja:
`bbox.MaxZ` **é** o topo do vão, verificado em 142/142.

### B.1 Cotas dos vãos

| Rótulo | n | Larguras (cm) | Alturas (cm) | Peitoris (cm) | Topo do vão (cm) |
|---|--:|---|---|---|---|
| PORTA | 47 | 91 (35) · 101 (6) · 141 (3) · 121 (2) · 92 (1) | 221 (46) · 181 (1) | 0 (46) · 40 (1) | **221 (47/47)** |
| JANELA | 61 | 141 (30) · 121 (22) · 61 (5) · 66 (3) · 296 (1) | 121 (53) · 61 (4) · 51 (3) · 141 (1) | 100 (53) · 160 (4) · 40 (3) · 80 (1) | 221 (58) · 91 (3) |
| ABERTURA | 34 | 151 (17) · 156 (7) · 61 (7) · 296 (2) · 116 (1) | 141 (19) · 221 (7) · 91 (3) · 61 (4) · 121 (1) | 80 (24) · 0 (7) · 160 (2) · 100 (1) | 221 (29) · 171 (3) · 141 (2) |

**134/142 (94,37%) dos vãos terminam na cota 221 cm** — a 12ª linha da grade
modular (`1 + 11 × 20`). O topo do vão não é livre: é uma fiada.

---

## C. A GRADE MODULAR

Cotas de assentamento (`Deslocamento do hospedeiro`) no 1º pavimento:

```
1 · 21 · 41 · 61 · 81 · 101 · 121 · 141 · 161 · 181 · 201 · 221 · 241
```

Passo de **20 cm** = bloco de 19 + 1 cm de junta horizontal, começando em
**+1 cm** (junta de assentamento). Cotas intermediárias observadas
(`91`, `111`, `171`) e cotas `+0,2` correspondem a ajustes locais.

**Peças de 9 cm de altura**: 852 no modelo. **762 (89,44%)** assentam na base
da fiada (`z ≡ +1 mod 20`) ou na meia-fiada (`z ≡ +11 mod 20`) —
`9 + 1 de junta + 9 = 19`, ou seja, **duas peças de 9 cm reconstroem uma fiada
normal**. Mesmo mecanismo do TORRE EASY.

---

## D. FAMÍLIAS DE BLOCOS

21 pares família/tipo, 65.747 peças. Dimensões **do sólido**, em cm.
Inventário completo em [`01_family_catalog.json`](01_family_catalog.json).

### D.1 Alvenaria comum — as 6 peças que o solver já conhece

| Código | Família / Tipo | Sólido (C×L×A) | Instâncias |
|---|---|---|---:|
| B39 | `BLOCO INTEIRO - 14x19x39` | 39 × 14 × 19 | 31.540 |
| B34 | `BLOCO 34 - 14x19x34` | 34 × 14 × 19 | 15.651 |
| B19 | `MEIO BLOCO - 14x19x19` | 19 × 14 × 19 | 2.700 |
| C04 | `PASTILHA - 14x19X4` | 4 × 14 × 19 | 2.329 |
| C09 | `COMPENSADOR 14x19x9` | 9 × 14 × 19 | 2.129 |
| B54 | `BLOCO 54 - 14x19x54` | 54 × 14 × 19 | 1.614 |

### D.2 Canaletas — 8.931 peças, 6 tipos

| Família | Sólido | Instâncias |
|---|---|---:|
| `CANALETA INTEIRA - 14x19x39` | 39 × 14 × 19 | 5.865 |
| `CANALETA 34 - 14x19x34` | 34 × 14 × 19 | 2.615 |
| `MEIA CANALETA - 14x19x19` | 19 × 14 × 19 | 194 |
| `CANALETA J - 14x9-19x19` | 19 × 14 × 19 | 190 |
| `BLOCO CANALETA CORTADO - 14x19xVAR` | VAR × 14 × 19 | 57 |
| `CANALETA J CORTADA - 14x9-19xVAR` | VAR × 14 × 19 | 10 |

> **A canaleta tem 19 cm de altura — a altura de uma fiada inteira.** É esta a
> diferença de fundo para o TORRE EASY, onde a peça de reforço tem 9 cm.

### D.3 Demais peças

| Família | Instâncias | Observação |
|---|---:|---|
| `COMPENSADOR 14x19x9 (deitado)` | 633 | 19 × 14 × **9** — compensador deitado |
| 9 famílias `*CORTADO*` | 286 | seção G |
| `BLOCO INTEIRO - 14x19x39` \| tipo `BLOCO INTEIRO VEDAÇÃO` | 1 | mesma família, tipo diferente |

### D.4 Elementos de apoio (fora de Modelos genéricos)

| Categoria | Família / Tipo | Instâncias | Papel inferido |
|---|---|---:|---|
| Estruturas temporárias | `SGraute - B` | 10.930 | marcação de graute |
| Quadro estrutural | `GRAUTE HORIZONTAL` 9x16.5 / 9x6.5 | 768 / 117 | **graute dentro da canaleta** |
| Pilares estruturais | `1 FERROS Ø10` (15x9 / 9x9) | 1.564 / 572 | armadura vertical |
| Pilares estruturais | `GRAUTE VERTICAL` | 154 | graute vertical |

A existência de **885 peças de `GRAUTE HORIZONTAL`** com seções 9×16,5 e 9×6,5
é coerente com canaleta grauteada e armada — mas o vínculo peça-a-peça
canaleta ↔ graute **não foi medido** neste levantamento. **NÃO VERIFICADO.**

---

## E. O QUE EXISTE ACIMA DAS ABERTURAS

Detalhe por abertura em [`03_above_openings.json`](03_above_openings.json).

| Rótulo | n | Fiada apoiada no topo do vão é **100% canaleta** | % |
|---|--:|--:|--:|
| **PORTA** | 47 | **47** | **100,00** |
| **JANELA** | 61 | **58** | **95,08** |
| ABERTURA | 34 | 25 | 73,53 |
| **TOTAL** | **142** | **130** | **91,55** |

| Medida | Resultado | Confiança |
|---|---|---|
| Altura da peça acima do vão | **19 cm** (fiada inteira) | ALTA |
| Largura | 14 cm | ALTA |
| Cota de assentamento | **base da canaleta = topo do vão, offset 0,00 cm em 135/136** | ALTA |
| Classificação | `CHANNEL_REINFORCEMENT` | ALTA |
| Nº de peças sobre o vão | mediana 4 (vãos ≤ 119 cm) · 16 (vãos 120–149 cm) | — |

A única exceção do offset (`id=6616547`, PORTA) é artefato: a parede `PAR23` tem
a grade deslocada em +1 cm, e a canaleta está em 222 cm sobre um vão que termina
em 220 cm — **é a mesma solução**, com 1 cm de deslocamento da grade.

### E.1 Composição da fiada acima do vão

| Rótulo | Famílias sobre o vão | n |
|---|---|--:|
| PORTA | `CANALETA 34` + `CANALETA INTEIRA` | 34 |
| PORTA | `CANALETA INTEIRA` só | 7 |
| PORTA | `CANALETA INTEIRA` + `MEIA CANALETA` | 3 |
| PORTA | `CANALETA 34` só | 2 |
| JANELA | `CANALETA INTEIRA` só | 40 |
| JANELA | `CANALETA 34` + `CANALETA INTEIRA` | 13 |
| JANELA | `CANALETA 34` só | 4 |

A canaleta acima do vão **não é uma peça única**: é uma sequência de canaletas
de 39 e 34 cm assentadas na fiada, escolhidas para fechar o comprimento —
exatamente como uma fiada normal, só que com peça canaleta.

---

## F. O QUE EXISTE ABAIXO DO PEITORIL

Detalhe em [`04_below_windows.json`](04_below_windows.json).

**89 aberturas têm peitoril > 0** (61 JANELA + 27 ABERTURA + 1 PORTA com
peitoril 40).

| Medida | Resultado | Confiança |
|---|---|---|
| Canaleta imediatamente sob o peitoril | **89/89 = 100,00%** | **ALTA** |
| Cota | **topo da canaleta = peitoril, offset 0,00 cm em 88/89** | ALTA |
| Altura da peça | 19 cm (fiada inteira) | ALTA |
| Existe uma **segunda** fiada de canaleta abaixo? | **0/89** | ALTA |
| Canaleta J usada abaixo do peitoril? | **0** ocorrências | ALTA |

**Não há junta ou faixa intermediária**: o topo da canaleta *é* a cota do
peitoril. A resposta à pergunta da seção 9 do escopo é
**"topo da canaleta = peitoril"**, sem exceção medida.

Composição sob o peitoril: `CANALETA INTEIRA` só (47) · `CANALETA 34` +
`CANALETA INTEIRA` (32) · `CANALETA 34` só (6) · com `BLOCO CANALETA CORTADO` (3)
· com `MEIA CANALETA` (1).

---

## G. TIPOS DE CANALETA E SEUS PAPÉIS

Inventário completo em [`05_channels.json`](05_channels.json).
**8.931 canaletas.** Contextos (uma peça pode acumular mais de um papel):

| Papel | Peças | % das canaletas |
|---|---:|---:|
| `TOP_BOND_BEAM` (cinta da última fiada) | 4.949 | 55,41 |
| `ABOVE_WINDOW` | 1.064 | 11,91 |
| `BELOW_WINDOW` | 1.049 | 11,75 |
| `ABOVE_DOOR` | 531 | 5,95 |
| `ABOVE_OPENING` | 400 | 4,48 |
| `BELOW_OPENING` | 324 | 3,63 |
| `BELOW_WINDOW_2ND` | 71 | 0,80 |
| `OTHER` (sem contexto atribuído) | 760 | 8,51 |

> **Este projeto usa a canaleta em papéis distintos e acumulativos.**
> A mesma família (`CANALETA INTEIRA - 14x19x39`) aparece como cinta de topo
> (3.154), acima de janela (261), abaixo de janela (250), acima de porta (113)
> e sem contexto (1.917).

### G.1 A distinção que importa: canaleta de abertura × canaleta de topo

Elas **não** são o mesmo elemento, mas em muitos casos são **fiadas vizinhas**:

- topo do vão: **221 cm**
- fiada de canaleta da verga: **221 cm**
- fiada de topo da parede: **241 cm** (em 120 das 142 aberturas)

Ou seja: acima de um vão típico há **duas fiadas de canaleta empilhadas**
(221 e 241), formando uma faixa canaletada de 40 cm — **114/142 (80,28%)** das
aberturas têm a 2ª fiada acima também 100% canaleta. Mas isso é **coincidência
de projeto** (o vão termina uma fiada abaixo do topo da parede), **não** um
sistema de verga dupla: a fiada de 241 existe igualmente em paredes sem abertura.

### G.2 Cinta de topo

| Medida | Resultado |
|---|---|
| Grupos de parede `(Parede, nível)` | **340** |
| Última fiada **100% canaleta** | **251 (73,82%)** |
| Última fiada **sem nenhuma canaleta** | 80 (23,53%) |
| Paredes com **duas** fiadas de canaleta no topo | 27 |

> Comparação direta com o TORRE EASY: lá, 465/651 = **71,43%**.
> Aqui, **73,82%**. Dois projetos independentes, de escritórios e sistemas de
> abertura diferentes, convergem no mesmo patamar. Isso é evidência
> relevante para o **CONFLITO 10.7** de `REGRAS_MODULACAO_BLOCOS.md` —
> mas continua **não sendo universal**, e portanto o conflito **segue aberto**.

### G.3 As 760 canaletas sem contexto

Distribuição por cota relativa: `241` (522) · `21` (63) · `181` (63) ·
`81` (45) · `141` (32) · `101` (17) · `321` (10) · `221` (8).

As 522 em `z = 241` estão em paredes cujo topo está em `261` — são a
**penúltima** fiada em paredes com cinta dupla. As demais (238) são fiadas de
canaleta no meio da parede sem abertura associada a menos de 60 cm.
**Não foram explicadas** neste levantamento — registradas como `OTHER`.

---

## H. BLOCOS CORTADOS

**286 peças (0,44% do modelo).** Detalhe em [`06_cut_blocks.json`](06_cut_blocks.json).

### H.1 Duas estratégias de corte — proporção invertida em relação ao TORRE EASY

**Corte na ALTURA (19 → 9 cm), por família dedicada — 124 peças (43,36%)**

| Família | Sólido | Instâncias |
|---|---|---:|
| `BLOCO 34 CORTADO - 14x9x34` | 34 × 14 × **9** | 44 |
| `MEIO BLOCO CORTADO - 14x9x19` | 19 × 14 × **9** | 28 |
| `BLOCO 54 CORTADO - 14x9x54` | 54 × 14 × **9** | 18 |
| `PASTILHA CORTADA- 14x9X4` | 4 × 14 × **9** | 16 |
| `BLOCO INTEIRO CORTADO - 14x9x39` | 39 × 14 × **9** | 9 |
| `COMPENSADOR CORTADO - 14xVARx9` | 9 × 14 × **9** | 9 |

**Corte no COMPRIMENTO, por parâmetro de instância — 162 peças (56,64%)**

| Família | Comprimentos reais observados | Instâncias |
|---|---|---:|
| `COMPENSADOR CORTADO 14x19x9 (deitado)` | 4 · 9 · 12,7 · 13,5 · 14 · 14,1 cm | 95 |
| `BLOCO CANALETA CORTADO - 14x19xVAR` | 9 · 14 · 24 · 29 cm | 57 |
| `CANALETA J CORTADA - 14x9-19xVAR` | 9 · 14 cm | 10 |

> **Diferença marcante para o TORRE EASY.** Lá o corte na altura respondia por
> **93,54%** dos cortados. Aqui responde por **43,36%** — a maior parte dos
> cortes é **no comprimento**, e mais da metade deles é em peças **de canaleta**
> (67 de 162), justamente para fechar o comprimento das fiadas canaletadas.

### H.2 Onde os blocos cortados aparecem

| Contexto | Peças | % |
|---|---:|---:|
| `TOP_OF_WALL` | 124 | 43,36 |
| `OTHER` | 63 | 22,03 |
| `NEAR_JAMB` (≤ 25 cm de uma jamba) | 57 | 19,93 |
| `INSIDE_OPENING` | 36 | 12,59 |
| `WALL_END` | 21 | 7,34 |
| `BELOW_SILL` | 9 | 3,15 |

Dos 150 cortados que têm alguma abertura na mesma linha de parede, **92 (61,3%)
estão a ≤ 25 cm de uma jamba**; a mediana da distância à jamba mais próxima é
**14 cm**.

---

## I. APOIOS LATERAIS MEDIDOS

Medida: distância da **jamba** até a extremidade da corrida contínua de
canaleta que cruza o vão. Publicada nas duas formas (`_bbox` bruto e `_solid`,
que desconta 1 cm de junta por ponta). Os números abaixo são `_solid`, o apoio
real de alvenaria, tomando o **menor** dos dois lados de cada abertura.

### I.1 Acima do vão (n = 130)

| min | p25 | mediana | p75 | max |
|---:|---:|---:|---:|---:|
| **4,0** | 19,0 | **39,0** | 59,0 | 449,0 |

| Limiar | Aberturas | % |
|---|---:|---:|
| ≥ 4 cm | 130/130 | **100,0** |
| ≥ 9 cm | 125/130 | 96,2 |
| ≥ 14 cm | 125/130 | 96,2 |
| ≥ 19 cm | 112/130 | 86,2 |
| ≥ 24 cm | 94/130 | 72,3 |
| ≥ 34 cm | 73/130 | 56,2 |
| ≥ 39 cm | 70/130 | 53,8 |

### I.2 Abaixo do peitoril (n = 89)

| min | p25 | mediana | p75 | max |
|---:|---:|---:|---:|---:|
| **−1,0** | 19,0 | **24,0** | 39,0 | 74,0 |

| Limiar | Aberturas | % |
|---|---:|---:|
| ≥ 4 cm | 85/89 | 95,5 |
| ≥ 9 cm | 83/89 | 93,3 |
| ≥ 14 cm | 80/89 | 89,9 |
| ≥ 19 cm | 72/89 | 80,9 |
| ≥ 24 cm | 46/89 | 51,7 |

> **O apoio deste projeto NÃO é o do TORRE EASY.** Lá o mínimo medido foi
> **≥ 9 cm em 784/784** apoios. Aqui existe um caso com **−1 cm** (a corrida de
> canaleta sob o peitoril termina 1 cm *dentro* da jamba) e quatro casos abaixo
> de 4 cm. **O apoio não é uma regra dura neste projeto** — porque a canaleta é
> uma fiada da alvenaria e não uma peça apoiada: a continuidade da fiada resolve
> o esforço, não o comprimento de embutimento.
>
> Reforça essa leitura o fato de a **mediana acima ser 39 cm** e o **máximo
> 449 cm**: em fachadas com janelas seguidas, a corrida de canaleta de uma
> janela **se funde com a da vizinha**, formando uma faixa contínua. Os campos
> `run_reaches_wall_start` / `run_reaches_wall_end` marcam quando a corrida
> encosta na extremidade da parede (aí o número não é decisão de apoio).

---

## J. RELAÇÃO ENTRE LARGURA DO VÃO E SOLUÇÃO

| Faixa de largura | n | Com canaleta acima | Nº de canaletas na corrida (mediana) |
|---|--:|--:|--:|
| 60–89 cm | 15 | **9 (60%)** | 3 |
| 90–119 cm | 43 | **43 (100%)** | 4 |
| 120–149 cm | 57 | **57 (100%)** | 16 |
| 150–179 cm | 24 | 18 (75%) | 31 |
| 270–299 cm | 3 | 3 (100%) | 9 |

**Padrão real observado**: vãos de **90 a 149 cm são resolvidos com canaleta em
100% dos casos**. As exceções concentram-se nas pontas — vãos pequenos
(≤ 89 cm) e um grupo específico de vãos de 156 cm (seção K).

---

## K. ABERTURAS QUE NÃO SEGUEM O PADRÃO DOMINANTE

12 das 142 aberturas (8,45%). Duas causas distintas, ambas identificadas:

### K.1 Vão livre até o topo da parede — 6 casos

`PAR28`, rótulo `ABERTURA`, 156 × 221 cm, peitoril 0, nos níveis 1º, 2º(TIPO)
e 9º (ids `6919219`, `6919324`, `6920791`, `6920792`, `6922742`, `6922743`).

Reconstrução vertical mostra que **as fiadas 221 e 241 existem na parede mas
não têm nenhuma peça sobre o vão**: a alvenaria simplesmente termina nas jambas
e o vão sobe livre até o topo. Não é uma falha de modelagem — é uma **passagem
de largura total**, sem nada a apoiar. **Confiança: ALTA.**

### K.2 Vão pequeno resolvido com compensador deitado — 6 casos

| id | Rótulo | Vão | Solução acima |
|---|---|---|---|
| `7719511` | JANELA | 66 × 51, peitoril 40 | 5 × `COMPENSADOR 14x19x9 (deitado)` |
| `7720857` | JANELA | 66 × 51, peitoril 40 | idem |
| `7722851` | JANELA | 66 × 51, peitoril 40 | idem |
| `7739806` | ABERTURA | 61 × 91, peitoril 80 | idem |
| `7742173` | ABERTURA | 61 × 91, peitoril 80 | idem |
| `7743976` | ABERTURA | 61 × 91, peitoril 80 | idem |

Vãos estreitos (61–66 cm) e baixos, em paredes curtas. A fiada sobre o vão é de
**compensador deitado de 9 cm de altura**, não de canaleta. Note que **abaixo**
do peitoril desses mesmos vãos **há canaleta normal** (verificado em
`7719511`: `CANALETA INTEIRA` em z = 21, topo = 40 = peitoril).
**Motivo inferido**: vão curto o suficiente para dispensar a fiada canaletada,
resolvido com peça de meia fiada. **Confiança: MÉDIA** (6 casos).

---

## L. VALIDAÇÃO CRUZADA

| Verificação | Resultado |
|---|---|
| Peças totais | 65.747 |
| ElementIds duplicados | **0** |
| UniqueIds duplicados | **0** |
| Peças sem parâmetro `Parede` | **0** |
| Peças sem posição (x/y/z) | **0** |
| Peças sem BoundingBox | **0** |
| Peças sem nível | **0** |
| Peças sem L/H/W | **0** |
| Peças com largura ≠ 14 cm | **0** |
| Peças com rotação não múltipla de 90° | **0** |
| Aberturas sem parâmetro `Parede` | **0** |
| Aberturas sem linha de parede correspondente | **0** |
| Aberturas com peitoril sem solução abaixo | **0** |
| Aberturas sem solução acima | 12 (seção K, todas explicadas) |
| Canaletas sem contexto atribuído | 760 (8,51%) |
| **Aberturas com rótulo `Parede` de outro nível** | **2** (`7720857`, `7722851` — rótulo `PAR10 - 1º PAVIMENTO` em peças do 2º/9º). Casadas **geometricamente**, não pelo rótulo. |

### L.1 Reconstrução manual (exigida pelo escopo)

Reconstruídas fiada a fiada em [`_scripts/an04_wall.py`](_scripts/an04_wall.py):

**PORTA `6616539`** — `PAR23 - 1º PAVIMENTO`, vão 141 × 221, parede de 1.396 cm:

```
z=201  BLOCO 34/54/INTEIRO/MEIO      (0% canaleta)   2 peças sobre o vão
z=221  CANALETA INTEIRA + CANALETA 34 (82% canaleta)  5 peças  <== TOPO DO VÃO
z=241  CANALETA INTEIRA + CANALETA 34 + MEIA (100%)   5 peças  <== CINTA DE TOPO
```

**JANELA `6588577`** — `PAR34 - 1º PAVIMENTO`, vão 141 × 121, peitoril 100,
parede de 2.931 cm:

```
z= 61  27% canaleta   (2ª faixa canaletada da parede)
z= 81  67% canaleta   5 peças sobre o vão  <== topo em 100 = PEITORIL
z=101  0% canaleta  · 2 peças (jambas)     <== VÃO
 ...   (jambas: BLOCO 34, MEIO BLOCO, COMPENSADOR, PASTILHA)
z=201  0% canaleta  · 2 peças (jambas)
z=221  84% canaleta  · 4 peças sobre o vão <== TOPO DO VÃO
z=241  100% canaleta                       <== CINTA DE TOPO
```

Também reconstruídas: PORTA `6616547`, JANELA `6589819`, e a exceção
`7719511` (seção K.2).

---

## M. MAPA REVIT → SOLVER

Catálogo do solver: `BLOCK_FAMILY_CATALOG_DEFINITIONS`
(`nuvem/core/wall_modeling.py:2311`), casamento por **família + tipo exatos**.

| Revit (família \| tipo) | Código | Status |
|---|---|---|
| `BLOCO INTEIRO - 14x19x39` \| idem | B39 | **SUPPORTED** |
| `BLOCO 34 - 14x19x34` \| idem | B34 | **SUPPORTED** |
| `BLOCO 54 - 14x19x54` \| idem | B54 | **SUPPORTED** |
| `MEIO BLOCO - 14x19x19` \| idem | B19 | **SUPPORTED** |
| `COMPENSADOR 14x19x9` \| idem | C09 | **SUPPORTED** |
| `PASTILHA - 14x19X4` \| idem | C04 | **SUPPORTED** |
| 6 tipos `CANALETA*` (8.931 peças) | — | **NOT_SUPPORTED** |
| 9 tipos `*CORTADO*` (286 peças) | — | **NOT_SUPPORTED** |
| `COMPENSADOR 14x19x9 (deitado)` (633) | — | **NOT_SUPPORTED** |
| `BLOCO INTEIRO - 14x19x39` \| `BLOCO INTEIRO VEDAÇÃO` (1) | — | **PARTIALLY_SUPPORTED** |

**Cobertura medida: 55.963 de 65.747 peças = 85,12%; 6 de 21 tipos = 28,57%.**

> Comparação: no TORRE EASY a cobertura foi **80,19%** das peças e 6 de 57 tipos.
> Este projeto tem um catálogo de peças **muito mais enxuto** (21 tipos contra 57),
> o que eleva a cobertura mesmo o solver não conhecendo nenhuma canaleta.
>
> **A lacuna é a mesma nos dois projetos e é inteiramente a canaleta**: os
> 14,88% não cobertos aqui são 8.931 canaletas (13,58%), 633 compensadores
> deitados (0,96%) e 286 cortados (0,44%).

---

## N. FAMÍLIAS DE VERGA E CONTRAVERGA — CARREGADAS E NÃO USADAS

Busca por `VERGA`, `CONTRAVERGA`, `LINTEL`, `COUNTER LINTEL` no documento
inteiro (evidência em [`evidence/verga_search.json`](evidence/verga_search.json)):

| Família | Categoria | Tipos | **Instâncias** |
|---|---|---:|---:|
| `VERGA JANELA` | Modelos genéricos | 25 | **0** |
| `CONTRAVERGA` | Modelos genéricos | 22 | **0** |
| `VERGA PORTA` | Modelos genéricos | 18 | **0** |
| `VERGA JANELA 3 FUROS` | Modelos genéricos | 4 | **0** |
| **Total** | | **69** | **0** |

Tipos presentes incluem `VERGA PORTA 9X109` … `9X224`, `V 14x9x114` …
`V 14x9x279`, `CONTRAVERGA 114` … `CONTRAVERGA 204` — a mesma biblioteca do
TORRE EASY, na mesma nomenclatura, com o mesmo passo de 5 cm.

Além disso, o parâmetro de instância **`Lintel` está em 0 nas 65.747 peças**.

> **Conclusão da seção 18 do escopo**: o projeto **tinha** o sistema de
> verga/contraverga disponível e **optou por não usá-lo**. A escolha do sistema
> de canaleta é deliberada, não uma limitação de biblioteca.

---

## O. PADRÕES OBSERVADOS

Íntegra com exceções e distribuições em
[`09_observed_patterns.json`](09_observed_patterns.json).

| ID | Padrão | Ocorr./Total | % | Confiança |
|---|---|---:|---:|---|
| BP01 | Toda PORTA tem canaleta apoiada no topo do vão | 47/47 | 100,00 | ALTA |
| BP02 | Toda abertura com peitoril tem canaleta sob o peitoril | 89/89 | 100,00 | ALTA |
| BP10 | `Lintel` zerado em todas as peças | 65.747/65.747 | 100,00 | ALTA |
| BP11 | Toda peça com 14 cm de largura | 65.747/65.747 | 100,00 | ALTA |
| BP12 | Rotação múltipla exata de 90° | 65.747/65.747 | 100,00 | ALTA |
| BP09 | Nenhuma instância de VERGA/CONTRAVERGA (69 tipos carregados) | 0/65.747 | 0,00 | ALTA |
| BP03 | Base da canaleta acima = topo do vão (offset 0) | 135/136 | 99,26 | ALTA |
| BP04 | Topo da canaleta abaixo = peitoril (offset 0) | 88/89 | 98,88 | ALTA |
| BP06 | Toda JANELA tem canaleta acima | 58/61 | 95,08 | ALTA |
| BP08 | Topo do vão na cota 221 cm | 134/142 | 94,37 | ALTA |
| BP18 | Rótulo `Título_abertura` coerente com a geometria | 134/142 | 94,37 | ALTA |
| BP05 | Qualquer abertura tem canaleta acima | 130/142 | 91,55 | ALTA |
| BP15 | Peça de 9 cm ocupa base ou meia-fiada (9+1+9=19) | 762/852 | 89,44 | ALTA |
| BP16 | 2ª fiada acima do vão também é canaleta | 114/142 | 80,28 | MÉDIA |
| BP13 | Última fiada da parede é 100% canaleta | 251/340 | 73,82 | MÉDIA |
| BP07 | Vão rotulado `ABERTURA` tem canaleta acima | 25/34 | 73,53 | MÉDIA |
| BP17 | Canaleta está na fiada de topo da parede | 4.949/8.931 | 55,41 | ALTA |
| BP14 | `CORTADO` = corte na altura (19→9) | 124/286 | 43,36 | MÉDIA |

---

## P. COMPARAÇÃO COM O TORRE EASY

Somente fatos já medidos e versionados — o RVT do TORRE EASY **não foi
reaberto**. Íntegra em [`10_torre_easy_comparison.json`](10_torre_easy_comparison.json).

| Aspecto | TORRE EASY | BUTANTÃ R08_LT |
|---|---|---|
| Porta — acima | **verga** (peça dedicada) | **canaleta** (fiada inteira) |
| Porta — abaixo | nenhum | nenhum |
| Janela — acima | **verga** | **canaleta** |
| Janela — abaixo | **contraverga** | **canaleta** |
| Altura da peça especial | **9 cm** | **19 cm** (fiada inteira) |
| Offset base acima × topo do vão | 0,00 cm (392/392) | 0,00 cm (135/136) |
| Offset topo abaixo × peitoril | 0,00 cm (147/147) | 0,00 cm (88/89) |
| Apoio mínimo | **≥ 9 cm** (784/784) | **≥ 4 cm**; um caso de −1 cm |
| Apoio mediano | 19 cm | 39 cm (acima) · 24 cm (abaixo) |
| Canaleta na fiada de topo | 71,43% (465/651) | **73,82%** (251/340) |
| Cortado = corte em altura | **93,54%** | **43,36%** |
| Cobertura do catálogo (peças) | 80,19% | **85,12%** |
| Cobertura do catálogo (tipos) | 6/57 | 6/21 |
| `Wall` nativas | 0 | 0 |
| Portas/Janelas nativas | 0 | 0 |
| Chave de parede | `Parede` (`PAR1`…`PAR117`) | `Parede` (`PARn - <faixa de pav.>`) |
| Rótulo de abertura | `Título_abertura` | `Título_abertura` |
| bbox +2 cm no comprimento | sim | sim (20/20 famílias) |
| bbox inflada em `BLOCO 54 CORTADO` | sim | sim |
| Famílias de verga | **usadas** (539 instâncias) | **carregadas, 0 instâncias** |

### P.1 O que os dois projetos têm em comum (o invariante)

Apesar de sistemas de abertura **opostos**, os dois projetos concordam em:

- ausência total de `Wall`/`Door`/`Window` nativos;
- `Parede` como chave de agrupamento;
- `Título_abertura` como rótulo porta/janela;
- **offset 0,00 cm** entre a peça de reforço e a borda do vão (acima e abaixo);
- grade de 20 cm, bloco de 19 + junta de 1;
- peça de 9 cm ocupando meia fiada;
- 14 cm de espessura única;
- ortogonalidade total;
- bbox com +2 cm no comprimento e a armadilha do `BLOCO 54 CORTADO`;
- canaleta na última fiada em ~72–74% das paredes.

> **A variável é o sistema de abertura. A gramática da modulação é a mesma.**
> Isso é o que torna viável a arquitetura A/B pedida pelo escopo: o solver não
> precisa de dois motores, precisa de **duas estratégias de preenchimento da
> fiada nas bordas do vão**.

---

## Q. LIMITAÇÕES E DADOS NÃO VERIFICADOS

1. **Porta MCP.** A ferramenta MCP configurada (48884) não respondeu; foi usada
   a porta real do Routes (48885) com o mesmo endpoint. Se a configuração do MCP
   for corrigida, os mesmos scripts funcionam sem alteração.
2. **Unicode na resposta HTTP.** Textos com acento voltam corrompidos no corpo
   da resposta (`BUTANT?`). Contornado gravando **arquivos UTF-8 direto do lado
   do Revit** e lendo-os localmente — nenhum dado deste relatório passou pelo
   canal corrompido.
3. **Aberturas dos pavimentos 3º–8º são INFERIDAS.** Não existem instâncias da
   família de abertura nesses níveis. A propagação está justificada pela
   identidade geométrica exata (6.727/6.727 peças, 0 diferenças), mas continua
   sendo inferência e está marcada como tal (`propagated_from_opening_id`).
4. **Vínculo canaleta ↔ graute NÃO VERIFICADO.** Existem 885 `GRAUTE HORIZONTAL`
   e 154 `GRAUTE VERTICAL`, mas não foi medido quais canaletas recebem graute.
5. **760 canaletas (8,51%) ficaram sem contexto atribuído.** 522 delas são a
   penúltima fiada de paredes com cinta dupla; as outras 238 não foram explicadas.
6. **Encontros L/T/X não foram analisados.** O escopo desta missão é aberturas;
   a amarração de encontros não foi medida neste projeto.
7. **Apoios usam a corrida contínua de canaleta.** Quando duas aberturas vizinhas
   compartilham a mesma faixa canaletada, o "apoio" medido é a distância até o
   fim da faixa, não uma decisão de projeto isolada. Os campos
   `run_reaches_wall_*` permitem filtrar esses casos.
8. **`ElementId.IntegerValue` não existe no Revit 2026** — usar `.Value`.
   O helper `eid()` em [`_scripts/rv_lib.py`](_scripts/rv_lib.py) cobre os dois.
9. **`Element.Name` falha no IronPython** para `FamilySymbol`; usar
   `DB.Element.Name.GetValue(el)` ou `symbol.FamilyName`.
10. **Nenhuma peça ficou sem nível** neste projeto (diferente do TORRE EASY,
    onde 539 vergas não tinham nível).

---

## R. GARANTIAS DE NÃO-INTERFERÊNCIA

- Nenhuma `Transaction` foi aberta. O handler `execute_code` da extensão
  pyRevit **não** abre transação automaticamente (verificado no fonte antes do
  primeiro uso), e nenhum script enviado abriu uma.
- Nada foi criado, movido, apagado ou renomeado no modelo; o RVT **não** foi salvo.
- `nuvem/core/**` — **sem diff de produção**.
- benchmark oficial — **intocado**.
- baseline — **intocado**.
- gabarito — **intocado**.
- `docs/revit_reference_extraction/` do TORRE EASY — **intocado**.
- Nenhuma regra normativa criada ou alterada; nenhuma estratégia `CHANNEL` ou
  `LINTEL` implementada.
