# Extração forense do projeto humano no Revit
## Vergas, contravergas, canaletas, blocos especiais e blocos cortados

> **Natureza deste documento**: evidência, não norma. Tudo aqui foi **medido**
> via MCP no documento Revit aberto, em modo **somente leitura** (nenhuma
> transação foi aberta, nada foi criado, movido, apagado ou salvo).
> Nenhum padrão descrito abaixo foi promovido a regra do solver, e nenhum
> arquivo de produção (`nuvem/core/**`, benchmark, baseline) foi tocado.
>
> Data da extração: **2026-09-09**.

---

## A. MODELO ANALISADO

| Item | Valor |
|---|---|
| Documento | `TORRE EASY-LO-R00_desanexado_joaoC9CL7.rvt` |
| Projeto | JARDIM DA COSTA BEACH CLUB (`CIV-`) |
| Caminho | `C:\Users\CIVIX\OneDrive\Documentos\` |
| Versão Revit | 2026 (build 26.3.0.37) |
| Unidade de comprimento do projeto | centímetros |
| Níveis no documento | 21 (`01. TER` … `21. COB`) |
| Elementos não-tipo no documento | 182.677 |
| **Peças de alvenaria (Modelos genéricos)** | **67.712** |
| **Aberturas (Mobiliário)** | **484** (+ 200 furos de tubulação) |
| Paredes (`Walls`) | **0** |
| Portas/Janelas nativas | **0** |

### A.1 Níveis que efetivamente têm modulação

| Nível | `ProjectElevation` (cm) | Peças | Paredes distintas | Aberturas |
|---|---:|---:|---:|---:|
| 01. TER | −760 | 96 | 1 | 0 |
| 02. G02 | −445 | 108 | 1 | 0 |
| 03. G03 | −80 | 126 | 1 | 0 |
| **04. TGD** | **340** | **12.564** | **117** | **91** |
| 05. TP1 | 611 | 12.758 | 116 | 91 |
| 08. TP1 | 1.424 | 12.758 | 116 | 91 |
| 10. TP1 | 1.966 | 12.759 | 116 | 91 |
| 20. TP1 | 4.676 | 12.303 | 116 | 91 |
| 21. COB | 4.947 | 3.701 | 63 | 29 |
| *(sem nível associado)* | — | 539 | 61 | 0 |

O nível **04. TGD** é o gabarito humano do benchmark deste repositório
(91/91 aberturas casam com o input `TESTE MODULAÇÃO`). Os níveis
`05/08/10/20. TP1` são repetições do pavimento-tipo e servem como
**verificação cruzada independente do mesmo padrão**.

### A.2 Descobertas estruturais sobre o modelo (afetam toda leitura futura)

1. **Não existe `Wall` neste documento.** A alvenaria é composta apenas por
   `FamilyInstance` de **Modelos genéricos**. A "parede" existe como
   **parâmetro compartilhado de texto `Parede`** (`PAR1`…`PAR117`), presente
   em **67.712/67.712** peças e em **484/484** aberturas — essa é a chave de
   agrupamento usada pelo humano.
2. **A cota Z interna do elemento é `Level.ProjectElevation + Deslocamento do
   hospedeiro`, não `Level.Elevation`.** Neste documento `Level.Elevation`
   está deslocado **+1510 cm** em relação às coordenadas internas. Ler
   `Elevation` leva a erro de 15 m.
3. **A `BoundingBox` das famílias de bloco tem folga de +1 cm em cada ponta
   do comprimento** (bloco de 39 → bbox de 41). O sólido real tem o
   comprimento nominal. Em `BLOCO 54 CORTADO` a bbox ainda está inflada
   **+10 cm em Z**. Toda medida deste relatório usa a **geometria sólida**,
   não a bbox.
4. **Vergas e contravergas não têm nível associado** (`FAMILY_LEVEL_PARAM =
   -1`, 539/539). O nível delas neste relatório é **inferido pelo Z**.
5. Os parâmetros `Fiada`, `Lintel`, `Arranque` e `Principal` existem em todas
   as peças mas estão **zerados em 67.712/67.712** — o projeto humano **não**
   numera fiadas nem marca verga por parâmetro. Toda classificação é
   geométrica.
6. O modelo é **100% ortogonal**: 67.712/67.712 peças com rotação múltipla
   exata de 90°.

---

## B. FAMÍLIAS DE BLOCOS

57 pares família/tipo. Dimensões **do sólido**, em cm (comprimento × largura ×
altura). Inventário completo em [`01_family_catalog.json`](01_family_catalog.json).

### B.1 Alvenaria comum (as 6 peças que o solver já conhece)

| Código | Família / Tipo | Sólido | Instâncias |
|---|---|---|---:|
| B39 | `BLOCO INTEIRO - 14x19x39` | 39 × 14 × 19 | 26.676 |
| B34 | `BLOCO 34 - 14x19x34` | 34 × 14 × 19 | 15.764 |
| B19 | `MEIO BLOCO - 14x19x19` | 19 × 14 × 19 | 4.019 |
| C09 | `COMPENSADOR 14x19x9` | 9 × 14 × 19 | 2.952 |
| B54 | `BLOCO 54 - 14x19x54` | 54 × 14 × 19 | 2.492 |
| C04 | `PASTILHA - 14x19X4` | 4 × 14 × 19 | 2.395 |

**Largura 14 cm em 67.712/67.712 peças** — espessura de parede única no
projeto inteiro.

### B.2 Peças que o solver **não** conhece

| Grupo | Instâncias | Observação |
|---|---:|---|
| Canaletas (8 tipos) | 6.584 | `CANALETA INTEIRA/34/J/MEIA` + cortadas |
| Blocos cortados (16 tipos) | 3.887 | corte em **altura**, ver seção F |
| Verga `VERGA JANELA` (14 tipos) | 417 | comprimento só no nome do tipo |
| Contraverga `CONTRAVERGA`/`CONTRAVERGA1` (7 tipos) | 122 | idem |
| `COMPENSADOR … (deitado)` | 504 | compensador deitado (9 cm de altura) |
| Tipos `VEDAÇÃO` (alvenaria não estrutural) | 2.382 | **mesma família**, tipo diferente |
| `BLOCO INTEIRO - 14x19x39.0001` | 30 | família duplicada no projeto |

---

## C. VERGAS

**392 peças** assentadas na posição de verga (classificação **por uso**, não
pelo nome). Detalhe em [`03_lintels.json`](03_lintels.json).

| Medida | Resultado | Confiança |
|---|---|---|
| Altura da verga | **9 cm** (539/539 verga+contraverga) | ALTA |
| Largura | 14 cm | ALTA |
| Cota de assentamento | **base da verga = topo do vão, offset 0,00 cm em 392/392** | ALTA |
| Apoio mínimo | **≥ 9 cm de cada lado, em 784/784 apoios medidos** | ALTA |
| Apoio mediano | **19 cm** (486 de 784 apoios) | — |
| Apoio máximo | 44 cm | — |
| Simetria esquerda=direita | 213/392 (54,3%) | BAIXA |
| Comprimento = vão + 19 + 19 | 202/392 (51,5%) | BAIXA |

Distribuição do apoio (cm): `9:40 · 18,9:38 · 19:486 · 19,1:38 · 24:87 ·
25:20 · 29:65 · 34:6 · 39:1 · 44:1`.

**Leitura observacional, sem aprovação normativa**: o invariante nesta amostra é *onde a verga nasce* (exatamente no topo do
vão) e *o apoio mínimo de 9 cm*. O comprimento exato **não** é uma fórmula
fechada — o humano escolhe o tipo de verga já fabricado (`VERGA 109` …
`VERGA 214`, de 5 em 5 cm) que cubra o vão com apoio ≥ 9 cm, e o excedente
cai onde couber.

O comprimento da verga **só existe no nome do tipo** (`VERGA 129` → 129 cm),
confirmado contra o sólido em todos os 14 tipos. Não há parâmetro de
comprimento nessas famílias.

---

## D. CONTRAVERGAS

**147 peças** na posição de contraverga. Detalhe em
[`04_counter_lintels.json`](04_counter_lintels.json).

| Medida | Resultado | Confiança |
|---|---|---|
| Altura | 9 cm | ALTA |
| Cota | **topo da contraverga = peitoril, offset 0,00 cm em 147/147** | ALTA |
| Apoio mínimo | ≥ 11,5 cm em 294/294 apoios | ALTA |
| Apoio mediano | 19 cm | — |
| Apoio máximo | 52,5 cm | — |

### D.1 Achado: 25 peças da família `VERGA JANELA` usadas **como contraverga**

25 instâncias da família `VERGA JANELA` estão assentadas **abaixo do
peitoril**, com o topo exatamente na cota do peitoril (offset 0,00) e apoios
de 19–44 cm — ou seja, **funcionalmente contravergas**. Ocorrem nas paredes
`PAR69`, `PAR70`, `PAR78`, `PAR84`, `PAR85`, em todos os 5 pavimentos
modelados.

Consequência prática: **classificar verga/contraverga pelo nome da família
produz 25 erros (4,6% do total de 539)**. A classificação correta é
geométrica. Os arquivos `03`/`04` já trazem os campos
`classification_pela_familia` e `familia_usada_fora_do_papel_do_nome` para
essa distinção.

---

## E. CANALETAS

**6.584 peças**, 8 tipos. Detalhe em [`05_channels.json`](05_channels.json).

Distribuição por situação de uso:

| Situação | Peças | % |
|---|---:|---:|
| Última fiada da parede (cinta de topo) | 3.303 | 50,2% |
| Última fiada **e** acima de um vão | 1.408 | 21,4% |
| Acima de vão sem ser última fiada | 322 | 4,9% |
| Abaixo de peitoril | 295 | 4,5% |
| Outra situação | 1.256 | 19,1% |

**91% de todas as canaletas do modelo estão na fiada `z_rel = 241 cm`** — a
13ª e última fiada do pé-direito de 271 cm. A canaleta neste projeto é,
predominantemente, **a cinta de amarração do topo da parede**, e não um
sistema de verga.

Resposta à pergunta A/B/C/D/E do escopo: **C (topo das paredes) é dominante**,
com participação secundária em D/A. Não é exclusivamente verga nem
exclusivamente contraverga.

### E.1 CONFLITO 10.7 — medição nova

A seção 10.7 de `REGRAS_MODULACAO_BLOCOS.md` registra o conflito aberto
*"toda parede tem canaleta na última fiada do topo"*, que a medição anterior
sustentava em apenas **39,4% (87/221)**.

Medição agora, sobre **651 paredes** (todos os níveis):

- última fiada **100% canaleta**: **465 paredes (71,4%)**
- última fiada **sem nenhuma canaleta**: 160 paredes
- última fiada **mista**: 26 paredes

No nível gabarito (117 paredes): 85 com canaleta (72,6%), 26 sem, 6 mistas.
As paredes **sem** canaleta no topo terminam majoritariamente em `z_rel =
271 cm` (20 de 26) — encostam na laje — e sua última fiada é de **bloco
cortado de 9 cm** (encunhamento), não de canaleta.

**O conflito continua aberto**: 71,4% é predominante, mas não é universal, e
há um mecanismo alternativo identificável (encunhamento com peça de 9 cm até
a laje). Não implementar nenhum dos dois lados sem decisão explícita.

---

## F. BLOCOS CORTADOS

**3.887 peças.** Detalhe em [`06_cut_blocks.json`](06_cut_blocks.json).

### F.1 Como o Revit representa o corte — **duas estratégias distintas**

**Estratégia 1 — corte na ALTURA, por família dedicada (93,5% dos casos).**
O projeto tem famílias próprias `… CORTADO - 14x9x…` cujo sólido tem
**9 cm de altura** e **o comprimento nominal preservado**:

| Família | Sólido | Instâncias |
|---|---|---:|
| `BLOCO INTEIRO CORTADO - 14x9x39` | 39 × 14 × **9** | 1.341 |
| `MEIO BLOCO CORTADO - 14x9x19` | 19 × 14 × **9** | 914 |
| `BLOCO 34 CORTADO - 14x9x34` | 34 × 14 × **9** | 888 |
| `COMPENSADOR CORTADO - 14xVARx9` | 9 × 14 × **9** | 199 |
| `PASTILHA CORTADA- 14x9X4` | 4 × 14 × **9** | 155 |
| `BLOCO 54 CORTADO - 14x9x54` | 54 × 14 × **9** | 139 |

> **"Cortado" neste projeto NÃO significa bloco serrado no comprimento.**
> Significa bloco **rebaixado de 19 cm para 9 cm de altura**.

**Estratégia 2 — corte no COMPRIMENTO, por parâmetro de instância (251 peças,
6,5%).** Famílias com sufixo `VAR` (`BLOCO CANALETA CORTADO - 14x19xVAR`,
`CANALETA J CORTADA - …xVAR`, `COMPENSADOR CORTADO 14xVARx9 (deitado)`)
carregam `Comprimento_bloco` como **parâmetro de INSTÂNCIA**. Valores
observados: majoritariamente redondos (9, 10, 14, 24 cm), mas também valores
de obra (`8,7913`, `8,9551`, `9,2669`, `23,8718`, `3,0556` cm).

### F.2 Onde os blocos cortados aparecem

| Contexto | Peças | % |
|---|---:|---:|
| `CUT_HEIGHT_ABOVE_OPENING` (acima de um vão) | 1.143 | 29,4% |
| `CUT_HEIGHT_NEAR_JAMB` (≤ 25 cm de uma jamba) | 1.103 | 28,4% |
| `CUT_HEIGHT_WALL_END` (≤ 25 cm da extremidade) | 475 | 12,2% |
| `CUT_HEIGHT_TOP_OF_WALL` (última fiada) | 427 | 11,0% |
| `CUT_HEIGHT_OTHER` | 413 | 10,6% |
| `CUT_LENGTH_VAR` | 251 | 6,5% |
| `CUT_HEIGHT_BELOW_SILL` | 75 | 1,9% |

**2.440 de 3.026 blocos cortados com abertura na mesma parede (80,6%) estão a
menos de 60 cm de uma jamba** — confirma e reforça `REGRAS §10.5` (a medição
anterior era 65%).

### F.3 Mecânica geométrica do corte (medida)

A peça de 9 cm ocupa **metade de uma fiada**: 4.134 de 4.679 peças de 9 cm
(88,4%) assentam ou na base da fiada (`z_rel ≡ +1 mod 20`) ou na meia-fiada
(`z_rel ≡ +11 mod 20`).

> **9 cm + 1 cm de junta + 9 cm = 19 cm** — duas peças cortadas empilhadas
> reconstroem exatamente uma fiada normal. É assim que o humano faz o ajuste
> vertical sem sair da grade de 20 cm.

---

## G. MAPA REVIT → SOLVER

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
| 8 tipos `CANALETA*` (6.584 peças) | — | **NOT_SUPPORTED** |
| 16 tipos `*CORTADO*` (3.887 peças) | — | **NOT_SUPPORTED** |
| 14 tipos `VERGA JANELA` (417 peças) | — | **NOT_SUPPORTED** |
| 7 tipos `CONTRAVERGA*` (122 peças) | — | **NOT_SUPPORTED** |
| `COMPENSADOR … (deitado)` (504 peças) | — | **NOT_SUPPORTED** |
| 13 tipos `VEDAÇÃO` (2.382 peças) | — | **NOT_SUPPORTED** (ver abaixo) |
| `BLOCO INTEIRO - 14x19x39.0001` (30) | — | **NOT_SUPPORTED** |

**Cobertura medida: 54.298 de 67.712 peças (80,19%); 6 de 57 tipos.**

> **Atenção — armadilha de nomenclatura.** 2.121 peças usam uma **família que
> o solver conhece** com um **tipo que ele não conhece** (ex.: família
> `BLOCO INTEIRO - 14x19x39`, tipo `VEDAÇÃO 14x19x39 - BLOCO INTEIRO`). Como o
> casamento é por família **+** tipo exatos, essas peças ficariam invisíveis
> para o catálogo fixo mesmo tendo geometria idêntica à do B39.

---

## H. PADRÕES OBSERVADOS

Íntegra com contagens, exceções e distribuições em
[`09_observed_patterns.json`](09_observed_patterns.json).

| ID | Padrão | Ocorr./Total | % | Confiança |
|---|---|---:|---:|---|
| P02 | Toda PORTA tem verga | 248/248 | 100,00 | ALTA |
| P03 | Nenhuma PORTA tem contraverga | 248/248 | 100,00 | ALTA |
| P07 | Base da verga = topo do vão (offset 0) | 392/392 | 100,00 | ALTA |
| P08 | Topo da contraverga = peitoril (offset 0) | 147/147 | 100,00 | ALTA |
| P09 | Verga apoia ≥ 9 cm de cada lado | 784/784 | 100,00 | ALTA |
| P10 | Contraverga apoia ≥ 9 cm de cada lado | 294/294 | 100,00 | ALTA |
| P13 | Verga/contraverga: 9 cm de altura, 14 de largura | 539/539 | 100,00 | ALTA |
| P14 | Toda peça com 14 cm de largura | 67.712/67.712 | 100,00 | ALTA |
| P15 | Rotação múltipla exata de 90° | 67.712/67.712 | 100,00 | ALTA |
| P19 | Topo do vão de PORTA na cota 221 cm | 247/248 | 99,60 | ALTA |
| P01 | Peça de 19 cm na grade `base+1 + k·20` | 62.621/63.033 | 99,35 | ALTA |
| P04 | JANELA tem verga | 130/134 | 97,01 | MÉDIA |
| P05 | JANELA tem contraverga | 129/134 | 96,27 | MÉDIA |
| P16 | CORTADO = corte na altura 19→9 | 3.636/3.887 | 93,54 | MÉDIA |
| P20 | Peça de 9 cm ocupa meia fiada (9+1+9=19) | 4.134/4.679 | 88,35 | MÉDIA |
| P17 | Bloco cortado a < 60 cm de uma jamba | 2.440/3.026 | 80,63 | MÉDIA |
| P06 | Vão rotulado `ABERTURA` não tem verga nem contraverga | 78/102 | 76,47 | BAIXA |
| P18 | Última fiada da parede é 100% canaleta | 465/651 | 71,43 | BAIXA |
| P11 | Verga simétrica (apoio esq. = dir.) | 213/392 | 54,34 | BAIXA |
| P12 | Verga = vão + 19 + 19 | 202/392 | 51,53 | BAIXA |

### H.1 Classificação porta × janela — o humano rotula explicitamente

O parâmetro compartilhado `Título_abertura` classifica as 484 aberturas:
**PORTA 248 · JANELA 134 · ABERTURA 102**. E o rótulo é **coerente com o
peitoril**: os 248 rótulos `PORTA` têm peitoril 0 (248/248); nenhum rótulo
`JANELA` tem peitoril 0. Isto **confirma independentemente** o critério de
`REGRAS §10.4` (vão que toca a base = porta; não toca = janela).

### H.2 Sequência vertical acima do topo de uma porta (nível 04. TGD)

| Cota (`z_rel`) | Peças | Composição |
|---|---:|---|
| 221 (topo do vão) | 835 | 668 bloco 19 cm · **164 cortado 9 cm** · 3 canaleta |
| 231 | 306 | **306 cortado 9 cm** (fiada fina cheia) |
| 241 | 1.361 | **1.254 canaleta** · 88 cortado · 19 bloco |
| 261 / 262 | 42 / 128 | cortado 9 cm (encunhamento até a laje) |

Isto **reproduz em escala** a sequência que `OPENINGS.md` registrava como
"PADRÃO OBSERVADO, só 2 exemplos": banda de 9 cm parcial → banda de 9 cm
cheia → fiada de canaleta. Agora são centenas de peças por pavimento,
repetidas identicamente em 5 pavimentos.

### H.3 Geometria da grade vertical

Fiadas medidas (`z_rel`, nível 04. TGD e 05. TP1, idênticos):
`1, 21, 41, 61, 81, 101, 121, 141, 161, 181, 201, 221, 241` — 13 fiadas,
passo de 20 cm, primeira em **base + 1 cm**.

Isto **confirma `REGRAS §8`** (`FIRST_COURSE_Z_OFFSET_CM = 1`, passo
`COURSE_JOINT_CM + 19 = 20`) contra o projeto humano real, em dois níveis
independentes.

Bandas finas de 9 cm intercaladas em `111, 131, 151, 171, 191, 211, 231,
251, 261` e a cota irregular `262`.

---

## I. EXCEÇÕES

1. **25 vergas usadas como contraverga** (seção D.1) — família fora do papel
   sugerido pelo nome.
2. **82 aberturas sem nenhuma peça especial associada** (78 `ABERTURA`,
   4 `JANELA`). São majoritariamente vãos grandes (321 cm, 40 casos) e vãos
   pequenos de 60 cm (28 casos) — plausivelmente vãos de sacada/shaft
   resolvidos por estrutura, não por alvenaria. **Não verificado** se há
   viga/estrutura cobrindo esses vãos: o documento não tem `Walls` e a
   categoria `Quadro estrutural` (819 elementos) não foi cruzada.
3. **4 janelas sem verga** e **5 sem contraverga** — 81 × 111 cm com peitoril
   140, presentes nos 4 pavimentos-tipo.
4. **412 peças de 19 cm fora da grade** (0,65%), concentradas em
   `z_rel = 151/171/191/211` (80 peças) e `z_rel = 260/300` (24 peças).
5. **`BLOCO 54 CORTADO`**: os parâmetros de tipo `Altura_bloco` divergem da
   geometria em 3 dos 4 tipos "cortado" testados. **A geometria sólida é a
   fonte confiável; o parâmetro de tipo não é.**
6. **1 porta com topo de vão em 231 cm** (as outras 247 em 221 cm).
7. **1 abertura com `host_offset = −0,5 cm`** e 8 com `−70 cm` — fogem da
   base do nível.

---

## J. DADOS QUE O MCP NÃO CONSEGUIU OBTER

1. **Parede hospedeira real**: não existe. `e.Host` é `None` em todas as
   peças; `Hospedeiro` é o próprio nível. A associação parede↔peça vem do
   parâmetro de texto `Parede`, e a **espessura de 14 cm é INFERIDA** da
   largura medida dos blocos, não lida de um objeto `Wall`.
2. **Nível de vergas e contravergas**: `FAMILY_LEVEL_PARAM = -1` em 539/539.
   O nível reportado é **INFERIDO pelo Z**.
3. **Workset**: legível (`ELEM_PARTITION_PARAM`) mas não extraído por não ser
   relevante à modulação.
4. **Numeração de fiada do humano**: o parâmetro `Fiada` existe e está
   **zerado em 100% das peças**. Toda numeração de fiada neste relatório é
   **calculada por nós** a partir do Z.
5. **Encontros L/T/X**: não foram classificados. Sem `Walls`, isso exige
   reconstruir o grafo de paredes a partir das peças — trabalho que excede o
   escopo desta extração e está registrado como pendência.
6. **Ordem de assentamento / fiada par-ímpar (amarração)**: não analisada
   aqui. Os dados de `07_special_blocks.json` (posição, `hand`, `facing`,
   `mirrored` de 3.526 peças B34/B54 do nível gabarito) são suficientes para
   fazê-la depois.
7. **Limitação de protocolo**: chamadas MCP longas (> ~60 s) estouram o
   timeout do cliente embora continuem executando no Revit; e
   `json.dumps` do IronPython quebra com caracteres não-ASCII
   (`UnicodeDecodeError` em `°`, `Ç`). Ambas contornadas (escrita em disco +
   serializador próprio) e registradas nos scripts em [`_scripts/`](_scripts/README.md).
8. **`LookupParameter` com nome acentuado falha** neste ambiente (retorna
   `None` para `Nível`, `RÔGGA_LOCAL`). Foi preciso usar **GUID de parâmetro
   compartilhado**. Uma leitura ingênua desses parâmetros produz silenciosamente
   "campo vazio" em vez de erro.

---

## K. RECOMENDAÇÕES PARA O ASTRA

### K.1 Fortes o bastante para virar regra (evidência ALTA, sem exceção)

| # | Fato medido | Base |
|---|---|---|
| 1 | Verga nasce **exatamente** no topo do vão (offset 0) | 392/392 |
| 2 | Contraverga termina **exatamente** no peitoril (offset 0) | 147/147 |
| 3 | Verga/contraverga têm **9 cm de altura** e 14 de largura | 539/539 |
| 4 | Apoio **≥ 9 cm** de cada lado da jamba (mediana 19) | 1.078/1.078 |
| 5 | **Toda porta tem verga; nenhuma porta tem contraverga** | 248/248 |
| 6 | Grade vertical `base+1 cm`, passo 20 cm | 62.621/63.033 |
| 7 | Espessura única 14 cm; modelo 100% ortogonal | 67.712/67.712 |
| 8 | `Título_abertura` do humano bate com o critério peitoril=0 de §10.4 | 248/248 |

### K.2 Precisam de decisão, não de mais medição

| # | Assunto | Situação |
|---|---|---|
| 9 | **Canaleta na última fiada**: 71,4%, com alternativa clara (encunhamento em 9 cm até a laje) | CONFLITO 10.7 continua aberto |
| 10 | **Comprimento da verga**: não há fórmula (51,5% em `vão+38`). O humano escolhe de um catálogo de 5 em 5 cm | política a definir |
| 11 | **Simetria do apoio**: só 54,3% | política a definir |
| 12 | **Vãos `ABERTURA`** (102): 76% sem nenhuma peça especial | falta cruzar com `Quadro estrutural` |

### K.3 Lacunas de catálogo a resolver antes de qualquer geração

1. O solver cobre **80,19%** das peças. Canaleta, cortado, verga e
   contraverga **não têm código de bloco** — 11.010 peças.
2. O casamento **família + tipo exatos** perde **2.121 peças** de tipos
   `VEDAÇÃO` cuja geometria é idêntica à de peças conhecidas. Decidir
   explicitamente se alvenaria de vedação entra no escopo do solver.
3. Peça cortada precisa de **duas** representações distintas: corte em
   **altura** (família dedicada de 9 cm) e corte em **comprimento**
   (parâmetro de instância `Comprimento_bloco`).

### K.4 O que NÃO fazer com estes dados

- Não tratar `Fiada`/`Lintel` do Revit como fonte — estão zerados.
- Não classificar verga/contraverga pelo nome da família (25 contraexemplos).
- Não usar `Level.Elevation` para cota (erro de 15 m neste documento).
- Não usar a `BoundingBox` como dimensão da peça (folga de +1 cm por ponta,
  e +10 cm em Z no `BLOCO 54 CORTADO`).
- Não promover P11/P12/P18 a regra: confiança BAIXA, medida.

---

## L. VALIDAÇÃO DA EXTRAÇÃO

| Verificação | Resultado |
|---|---|
| Duplicatas de `ElementId` | 0 |
| Peças sem parâmetro `Parede` | 0 / 67.712 |
| Peças sem `LocationPoint` | 0 / 67.712 |
| Soma por nível == total | ✔ 67.712 |
| Aberturas por nível | 91 · 91 · 91 · 91 · 91 · 29 (consistente entre pavimentos-tipo) |
| Peças sem nível no Revit | 539 — **todas** verga/contraverga (categoria inteira, não amostra) |
| Regra `bbox_h == Peitoril + Altura_abertura` | **484/484** |
| Vergas/contravergas pareadas a uma abertura | **539/539** após reclassificação por uso |
| Geometria sólida × parâmetros de tipo | divergência em 3 tipos `CORTADO` — geometria prevalece |
| Reprodutibilidade | scripts em [`_scripts/`](_scripts/README.md); dados brutos NDJSON regeráveis |

Reconstrução manual conferida em 2 exemplos (parede → abertura →
verga/contraverga → blocos adjacentes), incluindo a `JANELA 6125136`
(`PAR53`, vão 71 × 71 cm, peitoril 160): contraverga `CONTRAVERGA 119` em
`z=[491,500]` com topo exatamente no peitoril (500) e verga `VERGA 119` em
`z=[571,580]` com base exatamente no topo do vão (571), apoios 29/19 nos dois
casos. Números geometricamente coerentes.

---

## M. ARQUIVOS

| Arquivo | Conteúdo | Escopo |
|---|---|---|
| `01_family_catalog.json` | 57 tipos: geometria sólida, bbox, parâmetros, contagem por nível, mapa para o solver | modelo inteiro |
| `02_openings.json` | 484 aberturas + 200 furos | modelo inteiro |
| `03_lintels.json` | 392 vergas (por uso) | modelo inteiro |
| `04_counter_lintels.json` | 147 contravergas (por uso) | modelo inteiro |
| `05_channels.json` | 6.584 canaletas (agregado) + 1.280 instâncias | detalhe: 04. TGD |
| `06_cut_blocks.json` | 3.887 cortados (agregado + contexto) + 784 instâncias | detalhe: 04. TGD |
| `07_special_blocks.json` | 29.460 peças não-B39 (agregado) + 3.526 B34/B54 | detalhe: 04. TGD |
| `08_piece_opening_wall_relations.json` | 539 relações peça↔abertura↔parede | modelo inteiro |
| `09_observed_patterns.json` | 20 padrões com contagem, exceções e confiança | modelo inteiro |
| `_scripts/` | scripts de extração e análise | — |

**Identidade física**: todo registro traz `wall_physical_key` — SHA-1 de
`(nível, eixo, coordenada perpendicular, extensão da parede, cota da base)`.
`ElementId` e `PARxx` ficam como referência **local** ao documento, nunca como
identidade entre datasets, conforme o escopo exigiu.

Instâncias detalhadas de canaleta/cortado/especial ficam restritas ao nível
gabarito **04. TGD** para manter os arquivos versionáveis; os **agregados de
todos esses arquivos cobrem o modelo inteiro**, e os níveis `05/08/10/20. TP1`
são repetições verificadas do mesmo pavimento-tipo.

## Revisão de integração (2026-09-10)

Os limites e correções de interpretação estão em [REVIEW_2026-09-10.md](REVIEW_2026-09-10.md). O JSON é preservado como extraído.

ERRATA: 07 contém 5.536 especiais, incluindo 3.526 B34/B54, sem hand/facing/mirrored. A descrição anterior de formato enxuto e suficiência para orientação é superada pela revisão acima.
