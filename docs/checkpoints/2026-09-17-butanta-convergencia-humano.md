# PR #42 — Convergência com o projeto humano (2026-09-17)

Branch `claude/butanta-modulation-physical-fixes`, base `2521d1e` (§71), último commit de motor
`2c55211` (§74). **Não mergeado, PR continua draft.** **Status: READY FOR FINAL REVIT SMOKE** — todo
o offline está verde; a aplicação real no Revit ficou PENDENTE por bloqueio modal sem acesso humano
(§7.10). Legado (`strategy=None`) byte-idêntico do começo
ao fim: 8.939 peças, assinatura `0a2704e4faaf`.

Régua de tudo neste documento: **as 34 paredes de alvenaria do BUTANTÃ R08_LT, 1º PAV, fiadas
0–11**, humano e solver medidos pela MESMA função geométrica (`scratchpad/corpus.py` — nenhum campo
do motor entra na classificação).

---

## 0. VEREDITO — CAUSA-RAIZ FINAL

**A narrativa não mudou: o maior erro sistêmico restante era — e continua sendo — a distribuição
dos comprimentos dos trechos, provocada pela posse da região dos nós.**

Nada maior apareceu. Duas rodadas de investigação depois, com a correção (§72) já aplicada e medida
na geometria real do Revit, essa causa ainda explica **15 das 20** paredes mais divergentes. As
outras cinco se dividem entre um especial genuinamente exigido pelo comprimento (1), distribuição de
B34 (1), padrão humano não aprovado (1) e duas paredes de 99 cm que, olhadas peça a peça, são
**diferença de escopo entre os documentos** — o humano não constrói metade daquelas paredes.

**20% da divergência que resta não é defeito de modulação**: 100 pontos são as três paredes de 99 cm
que o humano não constrói inteiras, e 248 são duas paredes em que o solver está *melhor* que o
humano (fecha com um B34 onde ele usa `C04+C09`).

O que a correção alcançou: divergência de composição por parede **3.080 (main) → 2.575 → 1.727**,
com **zero** regressão de hard gate e o solve **mais rápido** que antes.

O que sobra e por quê:

- **8284580** (205 dos 1.727 pontos) — a parede CHEGA nos dois T, então preenche os 209 cm inteiros
  em toda fiada. Medido: na banda em que a decisão é tomada, o nó não concede amarração a nenhuma
  das duas fiadas e o par de comprimentos é **invariante** à inversão — não há ganho de paridade a
  extrair. A alavanca é o **papel no T**, mudança arquitetural, não feita.
- **3 paredes** dependem do padrão humano de coluna de compensador na jamba, que **não foi
  codificado** por conflitar com a regra #1.

---

## 1. ROOT CAUSES ENCONTRADAS

### 1.1 A composição de um trecho é função EXATA do comprimento

Com junta de 1 cm, fechar um trecho de L cm com n peças exige
`soma(comprimento_i + 1) = L + 1` — ou seja, trocar `L+1` em moedas de
**B39=40, B34=35, B19=20, C09=10, C04=5**. O resto módulo 40 decide sozinho quanto do trecho **não
pode** ser B39:

| resto | composição mínima |
|---|---|
| 0 | só B39 |
| 35 | 1 B34 |
| 30 | 2 B34 (ou B19+C09) |
| 25 | 3 B34 (ou B19+C04) |
| 20 | 4 B34 (ou 1 B19) |
| 15 | 5 B34 (ou C09+C04) |
| 10 | 6 B34 (ou 1 C09) |
| 5 | 7 B34 (ou 1 C04) |

**O preenchimento do solver já estava certo.** Medido contra o mínimo aritmético dos seus próprios
trechos: solver **+411** peças não-B39 acima do mínimo, humano **+381**. Quem estava errado era o
**conjunto de comprimentos**.

### 1.2 Quem define o comprimento é a paridade do nó — e ela era uma convenção global

Num encontro, só UMA das duas paredes ocupa a região do nó em cada fiada. Qual fiada de qual parede
é uma escolha **livre** (as duas alternativas são amarrações corretas), mas ela decide o comprimento
que sobra para cada fiada preencher. O motor fixava isso por PAPEL (no T, a principal hospeda sempre
na mesma fiada).

- **parede 8284579** (209 cm, T nas duas pontas): o humano dá o nó da esquerda a uma fiada e o da
  direita à outra — as duas ficam com **159 cm**, que fecham com **4 B39 exatos**. O solver dava os
  dois nós à mesma fiada: 179 cm de um lado (4 B34) e 174 do outro (5 B34). Mesma parede, mesma
  amarração, **8 B34 no lugar de 0**.
- **parede 8284557** (514 cm, 3 T): humano 4 trechos de 234/194 cm (1 B34 cada), solver 4 trechos de
  214 cm (5 B34 cada) — **132 B34 contra 36**.
- no corpus humano a paridade é **23 nós numa fiada e 23 na outra (50/50)**; no solver era **37/10**.

→ implementado como **§72** (três commits).

### 1.3 A métrica global escondia o problema

Antes da correção, as contagens por código do solver e do humano eram quase idênticas
(B39 3.066 × 3.061, B34 1.660 × 1.619) **enquanto paredes individuais estavam 132 B34 × 36**. O erro
se compensava entre paredes. A métrica que enxerga isso é a **divergência de composição por parede**
(soma, sobre as 34 paredes, de `|Δcódigo|` normalizada pelas peças humanas da parede, mais peso para
B34 em meio de parede e para especiais).

---

## 2. PADRÕES HUMANOS APRENDIDOS (medidos, viraram régua)

1. **Taxa de troca compensador × B34.** Entre composições que fecham o MESMO trecho, o humano usa a
   limpa (só B39/B34) **apenas quando ela custa ZERO B34 a mais**: 628 trechos limpos contra 22 com
   especial nesse caso; com custo ≥1 B34, **0 de 105** foram limpos. O solver faz o mesmo (99,3%).
2. **B54 é peça funcional de amarração.** Humano: **172, todos em T, todos a menos de 20 cm de um
   nó**. Solver: 168, idem. Nenhum B54 suspeito em nenhum dos dois.
3. **Paridade de nó escolhida caso a caso** (50/50), nunca por regra global.

---

## 3. REGRAS IMPLEMENTADAS

### §72 — A paridade do nó é escolhida pelo que ela deixa para preencher

`_search_tie_parity_fill_balance` roda depois de `_apply_abutting_tie_parity` (regra #1, que
continua tendo a última palavra) e varre os nós T/X em ordem geométrica, invertendo os que **reduzem
estritamente** o custo dos trechos livres que deixam. Cada trecho é montado com o layout PADRÃO do
sistema de tiers e o custo é

```
(trechos que não fecham, excesso da regra #2, nº de peças, especiais, B34)
```

comparação lexicográfica, sem pesos. **Decisão única por planta** (monotonia); a regra #1 roda de
novo depois dela.

**Guarda do alcance da verga:** um nó a menos de um bloco da jamba de uma abertura **não** é
invertido — ali a canaleta converte/recua a amarração e a paridade não é livre.

Detalhamento, evidência e as três ordens comparadas: `nuvem/REGRAS_MODULACAO_BLOCOS.md` §72.

---

## 4. MÉTRICAS — HUMANO × MAIN × PR42 ANTES × FINAL

Fiadas 0–11, 34 paredes de alvenaria.

| | HUMANO | MAIN (`55e990d`) | PR42 ANTES (`2521d1e`) | FINAL (`cf0277e`) |
|---|---|---|---|---|
| peças | 6.018 | 6.115 | 6.026 | **5.971** |
| B39 | 3.061 | 3.140 | 3.066 | 3.175 |
| B34 | 1.619 | 1.487 | 1.660 | 1.548 |
| B54 | 172 | 168 | 168 | 168 |
| B19 | 328 | 291 | 364 | 371 |
| C09 | 254 | 422 | 272 | **247** |
| C04 | 244 | 292 | 177 | **150** |
| especiais (B19+C09+C04) | 826 | 1.005 | 813 | **768** |
| cobertura de B39 | 61,8% | 63,6% | 61,3% | 63,4% |
| B39 por metro de fiada | 1,146 | — | 1,147 | 1,188 |
| B34 por metro de fiada | 0,606 | — | 0,621 | 0,579 |
| **divergência por parede (soma)** | 0 | 3.080 | 2.575 | **1.706** |
| trechos livres com resto bom (0/35) | 33,5% | — | 33,3% | **38,3%** |
| trechos com especial existindo alternativa limpa | **105** | — | 137 | **105** |
| B34 a menos de 20 cm de um nó | 50,3% | — | 45,1% | **51,2%** |
| B34 em meio de parede livre | 42,4% | — | 43,1% | 37,1% |
| B34 enterrado no meio do trecho | 6,3% | — | 20,0% | 12,4% |
| B54 em T / cruz / outro | 172/0/0 | — | 168/0/0 | 168/0/0 |
| junta isolada coincidente (não estrutural, fiadas 0–11) | 169 | — | 1 | 1 |
| junta vertical contínua ≥4 fiadas (régua geométrica, exclui verticais estruturais) | **21** | 0 | 0 | 0 |
| maior corrida de junta (mesma régua) | 12 | — | 2 | 2 |
| **paredes reprovadas pelo auditor do motor (17 fiadas, inclui contorno de nó)** | — | — | **4** | **4** |
| incompatibilidade de vazado do B34 | 41 (2,5%) | — | 71 (4,3%) | 76 (4,9%) |
| aglomerado de especiais | 0 | — | 11 | 17 |
| colisões / não-modular / sem apoio / invasão | — | 0/**78**/0/0 | 0/0/0/0 | **0/0/0/0** |
| tempo do solve (bancada) | — | 3 s | 27 s | **21 s** |

---

## 5. TOP 20 PAREDES — ANTES E DEPOIS

Soma do top 20: **2.268 → 1.604 (−29%)**. Seis paredes saíram do top 20:

| parede | antes | depois | |
|---|---|---|---|
| 8284557 | 302,0 | 0,0 | saiu |
| 8284579 | 222,0 | 0,0 | saiu |
| 8284567 | 164,2 | 0,0 | saiu |
| 8284551 | 162,7 | 12,0 | saiu |
| 8284563 | 142,1 | 3,2 | saiu |
| 8284554 | 70,6 | 3,1 | saiu |
| 8284548 | 70,0 | 84,2 | **piorou** |
| 8284522 | 69,2 | 81,3 | **piorou** |

Entraram no top 20 (já estavam logo abaixo): 8284580, 8284591, 8284586, 8284587, 8284588, 8284584.

As duas que pioraram, olhadas peça a peça:

- **8284522** piorou de verdade: B39 262 → 234 (humano 264), B34 82 → 116 (humano 87),
  C04 22 → 11 (humano 40). A paridade escolhida ali afastou a parede do humano — é o preço local do
  ganho global de −29% no top 20.
- **8284548** é artefato da métrica: a composição praticamente não mudou
  (B39 76 → 77, B34 64 → 63, B19 17 → 15, C09 5 → 5); o que subiu foi o termo de B34 em meio de
  parede dentro da fórmula da divergência.

---

## 6. EXPERIMENTOS REJEITADOS

| experimento | resultado | por que foi rejeitado |
|---|---|---|
| §70 fileira de B34 antes do compensador | B34 1.632 → 2.008 (humano 1.619), vazado 4,2% → 8,7% | vira B34 em todo trecho com sobra; com teto de 2 peças ainda custava 88 violações de vazado contra 68 |
| §72 com custo aritmético (ótimo teórico do comprimento) | divergência 1.841; C09 289 | só prevê o resultado real em 10 das 34 paredes (erro médio 7 peças) — ignora tiers e desencontro |
| §72 com B34 antes de especiais na ordem do custo | divergência 2.606 | pior que não fazer nada (2.575): maximiza B39 além do humano e paga em compensador |
| §72 avaliando só as paredes do nó (busca local) | divergência 1.970, 22 s | 40% mais rápido mas perde 160 pontos de divergência; resolvido com memo de layout (23 s, 1.809) |
| §72 estendida aos cantos L | divergência 1.706 → 1.761, especiais 768 → 775 | piora medida; revertido |
| §73 B34 perto da ponta como desempate | resultado IDÊNTICO | os 103 B34 enterrados no meio são `STANDARD_FILL` decididos pelo comprimento, não por empate — o desempate nunca dispara |
| §72 avaliada com o conjunto COMPLETO de aberturas (em vez da fatia da banda) | divergência 1.706 → 2.142; a 8284579 volta a 222 | com todas as aberturas os nós degradam a amarração e o modelo perde a informação que fazia a decisão certa; a fatia da banda 0 (a mais restrita) decide melhor |

---

## 7. LIMITAÇÕES CONHECIDAS (medidas, não escondidas)

0. **Quatro paredes continuam reprovadas pelo auditor de amarração do motor** — igual antes e
   depois da §72, então não é regressão desta missão, mas continua em aberto:
   - **8284522**: `CONTINUOUS_VERTICAL_JOINT` em X≈434,5 cm, 14 fiadas;
   - **8284586 / 8284587 / 8284588** (três paredes gêmeas de 99 cm, entre um canto e um T):
     junta corrida em X≈49,5 cm nas **17 fiadas**. Aqui o solver escolhe `B34+B34` onde o humano usa
     `C04+C09` alternando de posição por fiada — a escolha "mais limpa" do solver é justamente a que
     cria a junta corrida, e a do humano é a que a evita. **É um caso concreto de compensador
     NECESSÁRIO**, e o auditor o pega.

     Geometria da 8284586 (99 cm, canto em 7, T em 57, ponta livre em 99):
     ```
     solver  f0  B34@15-49  B34@50-84  C09@85-94  C04@95-99     -> junta em 49,5
     solver  f1  B34@0-34   C04@35-39  C09@40-49  [nó] B34@65-99 -> contorno em 49,5
     humano  f0  C04@15-19  C09@20-29  B34@30-64
     humano  f1  B34@0-34   C04@35-39  C09@40-49
     ```
     Não é paridade: o custo da §72 dá exatamente o mesmo valor `(0, 2, 6, 4, 2)` nas duas
     paridades dos nós dessa parede, e um dos três nós é canto L (fora do alcance da §72) e outro é
     ponta livre. É o preenchimento desta topologia (99 cm entre canto, T e ponta livre) que precisa
     ser revisto.

1. **Parede 8284580 — 205 dos 1.706 pontos de divergência restantes.** Ela é a parede que CHEGA nos
   dois T (`incoming_wall_idx` nos dois nós), então preenche os 209 cm inteiros em toda fiada (resto
   10 → 6 B34). O humano alterna qual ponta cede e fica com 159/194 cm. A §72 não resolve: o modelo
   de trechos livres reporta o MESMO par de comprimentos para as duas paridades. A alavanca aqui é o
   **papel no T** (quem é principal e quem chega), não a paridade — mudança arquitetural, fora do
   escopo desta missão.
2. **Conflito canaleta × amarração (pré-existente).** Invertendo um T a 27 cm da jamba na parede
   8284526, a contraverga da fiada 3 ficou com 615–644 no lugar da amarração 635–669 e a fiada 4
   ficou com um B34 com 41% de apoio. O defeito é da conversão em `plan_channel_reinforcement` e
   existe independentemente da §72; enquanto não for corrigido, a §72 não exercita a combinação
   (guarda do alcance da verga).
3. **Dependência da ordem de entrada das paredes (pré-existente).** Repetir o solve dá geometria
   idêntica; permutar a ordem das paredes de entrada muda o resultado — base `2521d1e`:
   8.837 → 8.836/8.851; final: 8.750 → 8.746/8.768. Mesma ordem de grandeza antes e depois.
4. **Vazado menor do B34: 4,3% → 4,9%** (humano 2,5%). A §72 piorou em 5 violações absolutas.
   O `alignment_conflicts` do motor (trechos em que nenhuma composição evitava a coincidência) subiu
   de 70 para 82 — sem efeito na geometria final: a régua geométrica dá 1 coincidência isolada e
   0 juntas contínuas nos dois estados.
5. **Aglomerado de especiais: 11 → 17** (humano 0).
6. **Microajuste (§66) pode escolher pior que offset 0.** Mapa medido na parede 8284534 movendo as
   4 aberturas juntas: offset 0 e −5 dão 1 C09; **+5 dá 7 C09**; ±10 dão 54–62 C09. Só múltiplos de
   5 fecham (`PIER_MODULE_CM`).

---

## 7.1 A PRÓXIMA CAUSA SISTÊMICA (diagnosticada, não corrigida)

Os dois maiores resíduos — a 8284580 (205 dos 1.706 pontos) e as três gêmeas de 99 cm — têm a
**mesma** causa: o modelo de trechos livres que a §72 usa
(`_wall_course_free_segments_cm`) devolve o MESMO par de comprimentos para as duas paridades,
enquanto o preenchimento realizado fica com comprimentos diferentes.

- **8284580**: o modelo diz A=184 / B=164 cm; o preenchimento real fica com 139 e 184 cm. Inverter
  qualquer um dos dois nós não muda o custo — a §72 fica cega.
- **8284586/7/8**: o modelo dá `(0, 2, 6, 4, 2)` idêntico nas duas paridades; o preenchimento real
  tem 8 peças, não 6.

O motor JÁ registra o resíduo: `alignment_conflicts` aponta exatamente essas quatro paredes
(índices 2, 28, 29, 30), curso B, `coincidence_count: 1` cada. No caso da 8284586 o trecho da fiada
B tem **14 cm** (35 → 49) e a coincidência é o PRÓPRIO FIM do trecho — nenhuma composição de 14 cm
a evita. Na fiada A existiria alternativa (`B39+B19+C09`, juntas em 54,5 e 74,5, sem tocar os
49,5), mas ela põe um B19 fora de ponta aberta, que a regra da §2 proíbe. **É um conflito real entre
a regra #1 e a regra do meio-bloco**, e o motor resolve a favor da regra do meio-bloco e registra.

**O que ficou sem explicação.** Não consegui, nesta sessão, isolar POR QUE as duas visões
divergem. Descartei: eixo estendido (a 8284580 e a 8284586 têm eixo estendido igual ao original,
sem deslocamento), memo de preenchimento (resultado idêntico com o memo forçado a errar sempre) e
não-idempotência de `solve_all_intersections` (sete chamadas seguidas dão candidatos idênticos).
Fica como a primeira coisa a investigar.

**Recomendação para a próxima rodada:** fazer o modelo de trechos da §72 usar a extensão REAL das
peças de nó (inclusive quando o encontro degrada) em vez das reservas padrão. Sem isso a §72 não
enxerga ganho nessas paredes. A alternativa — mudar o PAPEL no T (quem é principal e quem chega) —
é mudança arquitetural e não deve ser feita sem decisão sua.

---

## 7.2 SUÍTE COMPLETA

`pytest tests/ -q --ignore=tests/regression` no HEAD `cf0277e`:
**1 falha, 797 passaram em 27 min 33 s** (a corrida parou na falha por causa do `-x`).

A falha é **HERDADA e não tem relação com o motor**:
`tests/test_perf_trace_stall_sampler.py::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas`
quebra com `UnboundLocalError: cannot access local variable 'ctypes'` — o próprio teste importa
`ctypes` dentro de um ramo e usa noutro. Reproduzida idêntica em `main` (`55e990d`) e na base do PR
(`2521d1e`): **1 falha, 3 passaram** nos três. Não foi corrigida aqui por estar fora do escopo desta
missão; fica registrada, não escondida.

Corrida completa desselecionando só esse teste, na HEAD final (com os 10 testes novos de
`test_node_region_ownership.py`): **1.185 passaram, 0 falharam, 1 desselecionado, em 27 min 54 s.**
Nenhum teste, baseline ou golden foi alterado para passar.

---

## 7.3 EXECUÇÃO REAL NO REVIT

Três aplicações encadeadas no documento `butanta testes` (46 paredes, 34 de alvenaria), partindo das
aberturas devolvidas às posições ORIGINAIS do arquivo (as marcas de microajuste da entrega anterior
foram apagadas antes, para a execução começar do mesmo estado da bancada).

| | run 1 | run 2 | run 3 |
|---|---|---|---|
| lote anterior removido | 8.866 (1 lote) | 8.743 (1 lote) | 8.737 (1 lote) |
| peças resolvidas | 8.750 | 8.743 | 8.737 |
| microajuste: exigidas / aplicadas / bloqueadas | 24 / **2** / 1 | 24 / **1** / 0 | 24 / **0** / 0 |
| peças após remover/recolocar | 8.743 | 8.737 | 8.737 |
| **criadas** | **8.743** | **8.737** | **8.737** |
| falhas de criação | **0** | **0** | **0** |
| readback conferido / divergências | 8.743 / **0** | 8.737 / **0** | 8.737 / **0** |
| `planned == created` | **sim** | **sim** | **sim** |
| lote único | `20260917-015101` | `20260917-020931` | `20260917-022526` |
| HUMANO modificado | **não** | **não** | **não** |
| tempo | 18 min 25 s | 18 min 22 s | 15 min 52 s |

**Idempotência provada:** o run 3 moveu **zero** aberturas e criou exatamente as mesmas 8.737 peças
do run 2. A convergência foi 2 → 1 → 0 deslocamentos (a §66 examina no máximo 6 aberturas por
execução). Deslocamento total: **3 aberturas**, sem acúmulo.

**Geometria real conferida contra a bancada** (extração do lote final, mesma régua de fiadas 0–11):

| | bancada | Revit real |
|---|---|---|
| peças | 5.971 | 5.958 |
| B39 | 3.175 | 3.189 |
| B34 | 1.548 | 1.534 |
| B19 | 371 | 380 |
| C09 | 247 | **223** |
| C04 | 150 | 151 |
| divergência por parede | 1.706 | 1.739 |
| juntas contínuas (régua geométrica) | 0 | 0 |

A diferença são exatamente as 3 aberturas que a §66 moveu (a bancada resolve com as posições
originais). O resultado real ficou **melhor em compensador**: C09 223 contra 254 do humano.

O TARGET ficou **aberto, ativo, modificado e NÃO salvo**, como pedido. O HUMANO nunca recebeu
Transaction: `IsModified` = False antes e depois das três execuções e de toda a extração.

### Comparação visual — interrompida por um diálogo do Revit

Os 10 enquadramentos (T, cruz, porta, janela, B54, B34, aglomerado de especiais, pano liso e as duas
paredes com defeito conhecido) foram montados e a captura começou; saíram as duas primeiras imagens
(`A_T_8284579_target.png` e `A_T_8284579_humano.png`). Na segunda, o Revit abriu o lembrete modal
**"Projeto não recentemente salvo"**, que bloqueia a API — nenhuma chamada MCP responde enquanto ele
estiver na tela.

As quatro opções do diálogo são: *Salvar o projeto*, *Salvar o projeto e definir intervalos de
lembrete*, *Não salve e defina intervalos de lembrete* e *Cancelar*. **Duas delas salvariam o
TARGET**, contra a regra explícita da missão. Dispensá-lo por automação de janela foi bloqueado
pela política de permissões desta sessão, e por dentro do Revit não dá — é ele que trava o MCP.

**O lote NÃO corre risco**: as 8.737 peças estão no documento aberto e o diálogo não altera nada.
Basta clicar em **Cancelar** (ou *Não salve e defina intervalos de lembrete*) para liberar o Revit e
a captura recomeça de onde parou com `py -3 shoot_all72.py`.

---

## 7.4 MÉTRICAS FINAIS — SOBRE A GEOMETRIA REAL DO REVIT

Fiadas 0–11, 34 paredes de alvenaria. A coluna FINAL é a **geometria extraída do lote criado no
Revit**, não a da bancada.

| | HUMANO | MAIN | PR42 ANTES | FINAL |
|---|---|---|---|---|
| peças | 6.018 | 6.115 | 6.026 | **5.958** |
| B39 | 3.061 | 3.140 | 3.066 | 3.189 |
| B34 | 1.619 | 1.487 | 1.660 | 1.534 |
| B54 | 172 | 168 | 168 | 168 |
| B19 | 328 | 291 | 364 | 380 |
| C09 | 254 | 422 | 272 | **223** |
| C04 | 244 | 292 | 177 | 151 |
| especiais (B19+C09+C04) | 826 | 1.005 | 813 | **754** |
| **divergência total** | 0 | 3.080 | 2.575 | **1.727** |
| divergência média por parede | 0 | 90,6 | 75,7 | **50,8** |
| cobertura de B39 | 61,8% | 63,6% | 61,3% | 63,6% |
| B34 end-zone | 35,4% | — | 35,1% | 38,3% |
| B34 junction-zone | 1,9% | — | 0,0% | 0,4% |
| B34 center-junction-zone | 11,0% | — | 7,4% | 9,6% |
| B34 free-mid-wall | 42,4% | — | 43,1% | 37,4% |
| **B34 a menos de 20 cm de um nó** | 50,3% | — | 45,1% | **50,2%** |
| B54 em T / cruz / outro | 172 / 0 / 0 | 168/0/0 | 168/0/0 | **168 / 0 / 0** |
| compensador a ≤20 cm de um B54 | 6,2% | — | 11,8% | 10,2% |
| B19+B34 no envelope de um B54 | 107 | — | 139 | 149 |
| aberturas deslocadas / cm total | 0 | — | — | **3 / 30 cm** |
| junta isolada coincidente (régua geométrica) | 169 | — | 1 | 1 |
| maior corrida de junta (idem) | 12 | — | 2 | 2 |
| junta contínua ≥4 fiadas (idem) | 21 | 0 | 0 | 0 |
| **paredes reprovadas pelo auditor do motor** | — | — | 4 | **4** |
| incompatibilidade de vazado do B34 | 41 (2,5%) | — | 71 (4,3%) | 65 (4,2%) |
| B19 em meio de parede | 103 | — | 20 | 63 |
| aglomerado de especiais | 0 | — | 11 | 17 |
| colunas de compensador (peças / % dos especiais) | 27 (230 / 28%) | — | 12 (103 / 13%) | 13 (114 / 15%) |
| colisões / não-modular / sem apoio / invasão | — | 0/**78**/0/0 | 0/0/0/0 | **0/0/0/0** |
| tempo do solve (bancada) | — | 3 s | 27 s | **21 s** |

**Efeito medido da correção sobre os comprimentos** (é a cadeia causal, não correlação):

- **208 das 406 fiadas-parede (51%)** mudaram o conjunto de comprimentos dos seus trechos livres;
- trechos com resto bom (fecham só com bloco inteiro, ou com 1 B34): **33,3% → 38,7%** (+64);
- **245 trechos passaram a exigir MENOS bloco de ajuste**, 103 passaram a exigir mais (líquido +142).

---

## 7.5 A REGRA DE POSSE DA REGIÃO DO NÓ — AUDITORIA

**Como o motor decide.** Duas decisões encadeadas, as duas puramente geométricas:

1. **O papel**, em `wall_pairing.py`: quando a PONTA de uma parede encosta no MEIO do vão de outra
   (`_classify_point_along_wall` → `T_INTERSECTION`), a que continua vira `main_wall_idx` e a que
   encosta vira `incoming_wall_idx`. Perto de uma ponta da outra, vira `L_CORNER`. Não olha
   ElementId, ordem de entrada, camada nem sentido do eixo — só a posição do ponto de encontro ao
   longo do vão da vizinha.
2. **A fiada**, em `solve_t_intersection`: convenção fixa **por papel** — `B54` na principal vai
   para a **Fiada A**, `B34` na que chega vai para a **Fiada B**. Está escrito na própria docstring
   que "a inversão A/B que a seção 11 permite fica para a Etapa 7 decidir".

**Por que dava 37/10.** A fase é função pura do PAPEL, e o papel é função pura da geometria. Uma
parede que é principal em vários T hospeda sempre na mesma fiada. No BUTANTÃ, 8284515 é principal
em 6 T, 8284502 e 8284522 em 4 cada: a fase fica correlacionada pela planta inteira e o balanço
global vai para 37/10. O humano decide nó a nó e fica em **23/23**.

**Qual informação física a §72 usa.** Só o comprimento que cada paridade deixa para preencher, e
o layout padrão do sistema de tiers sobre esse comprimento. Não usa id, nem ordem, nem orientação.

**Sensibilidades, medidas:**

| a decisão depende de… | resposta | como foi medido |
|---|---|---|
| ordem de entrada das paredes | **não** (na fixture) | 5 permutações → assinatura física idêntica |
| inversão das pontas do eixo | **não** | mesma assinatura lida ao contrário |
| translação da planta | **não** | mesma assinatura |
| repetição | **não** | mesma geometria |
| ElementId / wall id | **não** | a fixture sintética não tem id nenhum |
| **banda de fiadas em que roda** | **SIM** | ver abaixo |

**A dependência de banda é real e é física.** `_t_intersection_room_ok` consulta as aberturas para
decidir se a peça de amarração cabe, e `openings_per_wall` chega fatiado por banda de altura. Na
parede de 209 cm entre dois T o contorno da ponta muda com a fatia:

| aberturas vistas | contorno da ponta 1 (A / B) |
|---|---|
| todas | 200 / 200 |
| nenhuma | 195 / 175 |
| fatia da banda 0 | 200 / 200 |

Isso está **certo**: a amarração não cabe onde há porta, e cabe acima da verga. A consequência é que
a §72, que decide uma vez para a planta inteira, decide na banda mais restrita. **Testei avaliar a
decisão com o conjunto COMPLETO de aberturas: piora** (divergência 1.706 → 2.142, e a 8284579
volta a 222). Rejeitado — está na tabela de experimentos.

---

## 7.6 TOP 20 NO ESTADO FINAL, COM A CAUSA CLASSIFICADA

Sobre a geometria REAL do Revit (divergência total 1.727):

| parede | div | nós com fase ≠ humano | causa |
|---|---|---|---|
| 8284580 | 204,7 | 1 | NODE_REGION_OWNERSHIP |
| 8284589 | 124,0 | 1 | NODE_REGION_OWNERSHIP |
| 8284590 | 124,0 | 0 | REQUIRED_SPECIAL |
| 8284561 | 112,0 | 1 | NODE_REGION_OWNERSHIP |
| 8284552 | 109,9 | 2 | NODE_REGION_OWNERSHIP + B54_CONTEXT |
| 8284502 | 105,0 | 1 | NODE_REGION_OWNERSHIP + OPENING_OFFSET |
| 8284539 | 93,3 | 1 | NODE_REGION_OWNERSHIP + PROJECT_SPECIFIC_HUMAN_PATTERN |
| 8284574 | 90,9 | 1 | NODE_REGION_OWNERSHIP + PROJECT_SPECIFIC_HUMAN_PATTERN |
| 8284548 | 84,2 | 1 | NODE_REGION_OWNERSHIP |
| 8284515 | 82,5 | 5 | NODE_REGION_OWNERSHIP + B54_CONTEXT |
| 8284522 | 81,3 | 1 | NODE_REGION_OWNERSHIP |
| 8284562 | 76,6 | 1 | NODE_REGION_OWNERSHIP |
| 8284558 | 59,3 | 0 | B34_DISTRIBUTION |
| 8284546 | 58,1 | 4 | NODE_REGION_OWNERSHIP + OPENING_OFFSET |
| 8284526 | 44,6 | 2 | NODE_REGION_OWNERSHIP + B54_CONTEXT |
| 8284591 | 42,9 | 1 | NODE_REGION_OWNERSHIP |
| 8284586 | 33,3 | 0 | UNEXPLAINED |
| 8284587 | 33,3 | 0 | UNEXPLAINED |
| 8284588 | 33,3 | 1 | NODE_REGION_OWNERSHIP |
| 8284584 | 32,3 | 0 | PROJECT_SPECIFIC_HUMAN_PATTERN |

**Contagem:** NODE_REGION_OWNERSHIP **15**, B54_CONTEXT 3, PROJECT_SPECIFIC_HUMAN_PATTERN 3,
OPENING_OFFSET 2, UNEXPLAINED 2, REQUIRED_SPECIAL 1, B34_DISTRIBUTION 1.

### Correção: parte do resíduo não é defeito

Depois de classificar, fui olhar peça a peça as duas linhas `UNEXPLAINED` e encontrei outra coisa.

**8284586 / 8284587 / 8284588 — o humano não constrói a parede inteira.** Medido diretamente nas
peças (não pela atribuição de parede): no trecho 60 → 99 cm dessas paredes, nas fiadas 0 e 1, o
humano tem **ZERO peças** e o solver tem 4. Somando as 12 fiadas, o humano cobre **588 cm** de cada
uma e o solver **1.002 cm** — ele constrói cerca de **metade** do eixo. Não é qualidade de
amarração: é **diferença de escopo entre os dois documentos**. As três somam **100 dos 1.727**
pontos (5,8%) e devem ser lidas como `HUMAN_PROJECT_SPECIFIC`, não como defeito do solver.

**8284589 / 8284590 — o solver está melhor.** H = `{B39:6, B34:12, C09:12, C04:12}` (42 peças),
S = `{B34:24}` (24 peças): o humano fecha com `C04+C09` onde o solver fecha com um B34, **sem
nenhum especial**. Divergência de 124 cada, mas a favor do solver. São mais **248 pontos (14,4%)**
que não são defeito.

**Ou seja: 348 dos 1.727 pontos (20%) da divergência que resta não são erro de modulação.** A
cobertura total é praticamente idêntica (humano 210.461 cm, solver 212.243 cm, **+0,8%**), e a
diferença está concentrada nessas três paredes.

**A causa-raiz continua sendo a mesma** — e ela ainda responde por 15 das 20 piores paredes.

### Por que a 8284580 não tem mais ganho por paridade

Medido na fatia da banda 0: o nó de t=202 **não concede amarração a nenhuma das duas fiadas**
(contorno 200/200 nas duas), porque a parede vizinha tem portas nessa altura. Inverter qualquer um
dos dois nós apenas troca os rótulos nas pontas — o par de comprimentos {184, 164} é **invariante**
e o custo dá exatamente igual, `(0, 0, 10, 1, 3)` antes e depois. Nas bandas acima das vergas o nó
passa a conceder, mas a decisão já está congelada (é única por planta, por construção).

O resíduo dessa parede **não é de paridade**: ela é a que CHEGA nos dois T
(`incoming_wall_idx` nos dois), então preenche os 209 cm inteiros em toda fiada. A alavanca é o
**papel no T**, que é mudança arquitetural e não foi feita.

---

## 7.7 O CASO 75 cm → 70 cm (§13) — RESOLVIDO

Parede 8284534, região entre o vão que termina em 595 e o T em 697. A abertura ficou em **offset 0**
e a composição saiu **peça por peça igual à do humano**, apenas trocada entre as famílias de fiada
(o que não é físico):

```
HUMANO f0   B39@595-634  B34@635-669  B54@670-724  B34@725-759
FINAL  f1   B39@595-634  B34@635-669  B54@670-724  B34@725-759
HUMANO f1   B19@595-614  B39@615-654  B34@655-689  B34@705-739  B39@740-779
FINAL  f0   B19@595-614  B39@615-654  B34@655-689  B34@705-739  B39@740-779
```

É exatamente o `B39 + B34` junto da amarração `B54` que a missão pedia. As aberturas dessa parede
**não são mais movidas** pela §66.

---

## 7.8 MICROAJUSTE (§66) — SWEEP COM O MOTOR FINAL

Deslocando SÓ a abertura 8079001 (parede 8284546, a que a §66 moveu na execução real), de −10 a
+10 cm em passos de `PIER_MODULE_CM`, e medindo a parede inteira depois do solve completo:

| offset | peças | B39 | B34 | B19 | C09 | C04 | especiais | não-modular | colisões |
|---|---|---|---|---|---|---|---|---|---|
| −10 | 291 | 195 | 57 | 3 | 9 | 3 | 15 | 0 | 0 |
| −5 | 290 | 191 | 62 | 2 | 11 | 0 | 13 | 0 | 0 |
| **0** | 292 | 193 | 60 | 0 | **13** | 2 | 15 | 0 | 0 |
| +5 | 291 | 192 | 60 | 3 | 10 | 0 | 13 | 0 | 0 |
| **+10 (a §66 escolheu este)** | 291 | **195** | 57 | 3 | **7** | 3 | **13** | 0 | 0 |

**O offset escolhido é o melhor da faixa**: empata em B39 com o extremo oposto e tem quase metade
dos C09 do offset 0. Offset 0 era candidato real e perdeu por mérito, não por arredondamento.

O caso que motivou a suspeita na rodada anterior (parede 8284534, +5 com 7 C09 contra 1 no offset 0)
**deixou de existir**: a §66 não move mais as aberturas dessa parede (ver §7.6).

---

## 7.9 DESEMPENHO E DETERMINISMO

**Custo da §72, medido por dentro:** a busca de paridade gasta **1,51 s** de um solve de 29,5 s
(**5,1%**), em 56 chamadas — só a primeira faz a busca, as outras 55 batem na guarda de decisão
única. O solve completo na bancada é **21 s**, contra 27 s antes da seção (o memo de layout por
trecho pagou o custo com folga).

**Determinismo:** repetir o solve dá geometria byte-idêntica. Permutar a ordem de entrada das
paredes muda o resultado — **mas isso é anterior a esta missão**: base `2521d1e` 8.837 → 8.836/8.851;
final 8.750 → 8.746/8.768, mesma ordem de grandeza. Na fixture sintética a §72 é invariante a cinco
permutações, à inversão das pontas, à translação e à repetição (`tests/test_node_region_ownership.py`),
então a sensibilidade residual do projeto real **não vem da regra de posse do nó**.

---

## 7.10 RESTAURAÇÃO CONTROLADA DO TARGET — PASSO 1 FEITO, 2 a 10 BLOQUEADOS

Autorização de 2026-09-17: tratar o purge/reset do TARGET como **restauração controlada** (10
checagens obrigatórias) e só então aplicar a §74 no Revit (run 1 / run 2 / run 3 se preciso).

**Executado: só o passo 1.** Os passos 2 a 10 e a aplicação **não foram executados**. O Revit
bloqueou o canal MCP com um modal e o usuário não estava na máquina para dispensá-lo. **Nada foi
salvo, nada foi apagado, nada foi movido** — o arquivo em disco continua exatamente como estava.

### PRE_RESET — leitura real feita às 14:21, ANTES do modal (`q_preflight.py`, só leitura)

| campo | valor |
|---|---|
| TARGET | `butanta testes` — `C:\Users\twitc\Desktop\CIVIX\butanta testes.rvt` |
| `IsModified` do TARGET | `true` (memória diverge do disco; o disco tem a modulação salva) |
| HUMANO | `BUTANTÃ - R08_LT (...) (1)` — **`IsModified = false`** |
| documento ativo (na leitura) | o HUMANO — por isso `q_activate.py` foi chamado em seguida |
| lotes carimbados | **1 lote**, `20260917-022526`, **8.737 peças** |
| paredes | 46 |
| marcas `MICROAJUSTE off=` | 3 — `8078984 +10,0`, `8078986 +10,0`, `8079001 +10,0` |
| transação no TARGET | possível (`Transaction.Start()/RollBack()` OK) |

**Deslocamento das aberturas vigiadas, conferido contra `aberturas_originais.json`:**

| abertura | original (cm) | estado atual (cm) | Δ |
|---|---|---|---|
| 8078992 / 93 / 94 / 95 | — | idêntico | **0,000** |
| 8078996 / 97 | — | idêntico | **0,000** |
| 8079002 | — | idêntico | **0,000** |
| **8079001** | 363,99 · 1137,00 | 373,99 · 1137,00 | **+10,000** |

Ou seja: das 44 aberturas, **3 estão deslocadas 10 cm** (as três com marca), total 30 cm — é
exatamente o que a §66 aplicou nas execuções de madrugada. É esse deslocamento que o
`r_reset_vaos.py` desfaria.

### Check 1 — cópia de segurança do TARGET salvo: **FEITO E VERIFICADO**

```
C:\Users\twitc\Desktop\CIVIX\_backup_missao_s74\butanta testes (BACKUP pre-reset 2026-09-17).rvt
181.641.216 bytes · mtime preservado 2026-09-17 09:40:09
sha256 30cdec3bae86f34cfa735f08921e0b747d9509cd984091171b53518a27dfd2f1  (idêntico ao original)
```

O Revit ainda mantém os próprios backups rotativos na pasta (`butanta testes.0001..0007.rvt`);
o `.0007` é de 16/09 20:12, **anterior** ao lote atual — não foi usado nem tocado.

### O bloqueio — evidência, não suposição

`journal.0078.txt`, 17-Sep-2026 14:21:58, logo depois do `Jrn.Activate "[butanta testes.rvt]"`:

```
Jrn.Data "Interrupt" , "SaveReminder" , ""
' TaskDialog "Você não salvou seu projeto recentemente. O que deseja fazer?"
'Id : TaskDialog_Project_Not_Saved_Recently
'CommonButtons : Cancel
'Command Links: 1001 Salvar o projeto | 1002 Salvar e definir intervalos | 1003 Não salve e defina intervalos
'DefaultButton : 1001
```

O modal roda no laço de mensagens do Revit e **congela o evento externo do pyRevit** — toda
chamada MCP fica enfileirada. O censo PRE_RESET ficou 13 min na fila sem executar; um `ping`
trivial também não voltou. Não há saída pela API: quem está bloqueado é o próprio canal.

Duas tentativas de dispensar o modal por automação de UI (P/Invoke e depois UI Automation, esta
última **só para enumerar** as janelas) foram **negadas pelo classificador de permissões**. Não
insisti nem tentei contornar.

### Checagens 2 a 10 — não executadas

| # | checagem | status |
|---|---|---|
| 1 | cópia de segurança do TARGET salvo | ✅ **feito**, sha256 conferido |
| 2 | remover SOMENTE elementos carimbados/owned | ⏸ pendente — script pronto: `rv/r_purga.py` |
| 3 | confirmar 0 peças owned restantes | ⏸ pendente |
| 4 | confirmar 0 lotes antigos/órfãos | ⏸ pendente — órfão = instância de família do catálogo do plugin SEM carimbo |
| 5 | executar `r_reset_vaos.py` | ⏸ pendente |
| 6 | provar as 44 aberturas na coordenada original | ⏸ pendente — `rv/q_censo_estado.py` mede Δ por abertura |
| 7 | confirmar 0 deslocamentos residuais | ⏸ pendente |
| 8 | não alterar o HUMANO | ✅ até aqui: `IsModified = false` em toda leitura |
| 9 | preflight/fingerprint do estado resetado | ⏸ pendente |
| 10 | só prosseguir se tudo bater | ⏸ **não prossegui** |

### O que falta rodar, na ordem (tudo já escrito e revisado)

```bash
sh rv/run.sh q_activate.py        # ativa o TARGET (o r_apply exige doc ativo)
sh rv/run.sh q_censo_estado.py    # PRE_RESET: carimbadas, lotes, órfãos, Δ das 44 aberturas
sh rv/run.sh r_purga.py           # checks 2-4 (mesma regra de carimbo do r_apply)
sh rv/run.sh r_reset_vaos.py      # check 5
sh rv/run.sh q_censo_estado.py    # POST_RESET: checks 6-7 (0 deslocamento, 0 marca)
sh rv/run.sh q_preflight.py       # check 9
sh rv/run.sh r_apply.py           # §74 run 1  (~17 min)
sh rv/run.sh r_apply.py           # §74 run 2  (~17 min)
sh rv/run.sh r_apply.py           # run 3 só se a run 2 ainda mover abertura
```

`r_purga.py` é novo nesta rodada e usa **exatamente** `wm._parse_block_lot_stamp` — a mesma
definição de "peça do plugin" que o `r_apply.py` usa — para não sobrar órfão nem tocar em nada do
humano. Ele aborta antes de qualquer escrita se `H.IsModified` não for `False`.

**A aplicação real da §74 no Revit continua PENDENTE.** Nenhum número de Revit desta seção foi
estimado: o que está aqui foi lido do modelo às 14:21 ou do journal.

---

## 7.11 VALIDAÇÃO OFFLINE DA §74 — TUDO VERDE (HEAD `2c55211`)

Com o Revit fora do ar, tudo que **não** depende dele foi refeito na HEAD atual.

### Auditoria do código — a mudança é uma linha de comparação

| pergunta | resposta |
|---|---|
| quantos pontos do motor usam a tolerância nova? | **um** — `wall_stepper.py:1494`, dentro de `_t_intersection_room_ok` |
| alguma constante mudou? | **nenhuma**. `PIER_PHYSICAL_FIT_TOLERANCE_CM = PIER_LAYOUT_TOLERANCE_CM = MODULATION_WHOLE_CM_TOLERANCE_CM = 0,05 cm`, intocadas desde `2521d1e` |
| constante nova? | **não** |
| padrão do motor | `T_ROOM_PHYSICAL_TOLERANCE = False` — sem a flag, o epsilon histórico `1e-6` ft |
| quem liga | só `wall_modeling`, e só quando `opening_reinforcement_strategy is not None` **e** `CHANNEL_T_ROOM_PHYSICAL_TOLERANCE_ENABLED`; salva/restaura no `finally` |
| algum hard gate foi tocado? | **não** — colisão, não-modular, apoio físico e invasão de vão não passam por essa função |

### A folga real dos 37 T — hoje reproduzível pelo corpus versionado (§7.12)

| nó | principal | chega | espaço mín. | falta p/ B54 | veredito |
|---|---|---|---|---|---|
| 28 | 8284502 | 8284562 | 6,9952 cm | **20,0048 cm** | reprova — e continua reprovando |
| 22 | 8284502 | 8284558 | 7,0035 cm | **19,9965 cm** | reprova |
| 30 | 8284554 | 8284563 | 11,9880 cm | **15,0120 cm** | reprova |
| 18 | 8284552 | 8284554 | 12,0035 cm | **14,9965 cm** | reprova |
| 19 | 8284588 | 8284557 | 22,9989 cm | **4,0011 cm** | reprova |
| 20 | 8284586 | 8284557 | 22,9989 cm | **4,0011 cm** | reprova |
| 39 | 8284587 | 8284573 | 22,9989 cm | **4,0011 cm** | reprova |
| **24** | 8284526 | 8284559 | 26,9880 cm | **0,012 cm** (0,12 mm) | variação de modelagem → passa com a §74 |
| **44** | 8284515 | 8284579 | 26,9965 cm | **0,003487 cm** (35 µm) | variação de modelagem → passa com a §74 |
| **46** | 8284515 | 8284580 | 26,9965 cm | **0,003487 cm** (35 µm) | variação de modelagem → passa com a §74 |
| 12 | 8284515 | 8284546 | 27,0035 cm | **sobra 35 µm** | já passava |
| 26 | 8284526 | 8284560 | 27,0120 cm | **sobra 0,12 mm** | já passava |

O argumento inteiro está nas quatro últimas linhas: **nas MESMAS paredes principais** (8284515 e
8284526) há nós que passam e nós que reprovam **pela mesma magnitude, só que com o sinal
contrário**. Não é geometria decidindo — é variação submilimétrica de modelagem.

**A §74 é mudança semântica e deliberada, não conserto de ruído numérico.** Ela introduz uma
tolerância física controlada de **0,05 cm** na decisão de `room_ok` e com isso **amplia em até
0,05 cm a fronteira histórica de cabe/não-cabe**. O epsilon anterior de `1e-6` ft (0,3 µm)
continua sendo a descrição correta do que havia antes — só que ele era epsilon de ponto flutuante,
enquanto o que a geometria traz é variação REAL de modelagem, na casa do centésimo de milímetro.

**Por que 0,05 cm — a justificativa:** a maior variação de modelagem observada no corpus é
**0,013251 cm**; a tolerância adotada é **3,8×** isso. O primeiro caso materialmente insuficiente
exige **4,001054 cm** — razão de **80×** entre a tolerância e a falta real seguinte. É essa
separação que justifica o valor.

### Saturação — provada peça a peça, não por totais

| tolerância | T que passam | peças | divergência | 8284580 | hard gates | digest da bancada (16 hex) |
|---|---|---|---|---|---|---|
| base `1e-6` ft | 27 | 5.971 | 1.707,7 | 204,7 | 0/0/0/0 | `18debf95e200c057` |
| 0,01 cm | 29 | 5.948 | 1.502,2 | 3,3 | 0/0/0/0 | `c677f313beb18acd` |
| **0,05 cm** | **30** | **5.944** | **1.502,2** | **3,3** | 0/0/0/0 | **`bc261fe485de635a`** |
| 0,10 cm | 30 | 5.944 | 1.502,2 | 3,3 | 0/0/0/0 | **`bc261fe485de635a`** |
| 0,30 cm | 30 | 5.944 | 1.502,2 | 3,3 | 0/0/0/0 | **`bc261fe485de635a`** |

0,05 / 0,10 / 0,30 cm produzem o **mesmo conjunto de peças, byte a byte**. Multiplicar a
tolerância por 6 não muda uma única peça — porque o próximo caso está a 4 cm.

> **Os digests desta tabela são da bancada, não do repositório.** Têm 16 hex (não são
> sha256) e vêm do formato ad-hoc de `scratchpad/corpus.dump`, que não é versionado. A
> versão auditável destes mesmos fatos está em §7.12, com `S74_SNAPSHOT_V1` e sha256
> completo. A coluna de divergência também é medição de bancada: reproduzi-la exigiria a
> composição humana das 34 paredes, que o corpus deliberadamente não versiona (§8).

**O que a saturação prova e o que ela não prova.** Prova que **não há precipício perto da
fronteira**: o resultado é insensível à tolerância numa faixa de 6×. **Não** justifica o valor
0,05 cm — a justificativa é a acima: variação de modelagem máxima **0,013251 cm**, tolerância
**3,8×** essa variação, primeiro caso materialmente insuficiente **4,001054 cm**, razão de **80×**.

### A flag implementada É a tolerância medida

O snapshot gerado pelo caminho real da §74 (`snap_s74.json`, flag do motor ligada pelo
`wall_modeling`) tem o **mesmo sha256** `bc261fe485de635a` do snapshot gerado pelo monkeypatch de
0,05 cm. A implementação não é "parecida" com o que foi medido: é idêntica. Hard gates do
snapshot: **colisões 0 · não-modular 0 · sem apoio 0 · invasão de vão 0**.

### Legado — byte-idêntico

```
strategy=None      pecas=8939   assinatura=0a2704e4faaf   (igual à baseline pré-§74)
strategy=CHANNEL   pecas=8723   assinatura=af8df620f686
```

### Determinismo

```
repeticao 1        pecas=8723 assinatura=ead54a24a375 IGUAL
repeticao 2        pecas=8723 assinatura=ead54a24a375 IGUAL
ordem invertida    pecas=8728 assinatura=fce75125ebe7 DIFERENTE
ordem embaralhada  pecas=8750 assinatura=d5a135154cb1 DIFERENTE
```

Repetir dá geometria idêntica. A sensibilidade à ordem de entrada é **anterior a esta missão** e
da mesma ordem de grandeza de sempre (base `2521d1e` 8.837 → 8.836/8.851; antes da §74
8.750 → 8.746/8.768; agora 8.723 → 8.728/8.750) — ver §7.9.

### Suíte

```
tests/ (sem regression)   1195 passaram · 0 falharam · 1 desmarcado · 28m43s
focada (4 arquivos)         58 passaram · 4m26s
```

O único teste desmarcado é `test_perf_trace_stall_sampler.py::test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas`,
que falha com `UnboundLocalError: ctypes` **igual em `main` (55e990d) e na base do PR (`2521d1e`)** —
defeito herdado, fora do escopo, não escondido.

### Comparação com o humano, no estado final offline

| | peças | B39 | B34 | B54 | B19 | C09 | C04 |
|---|---|---|---|---|---|---|---|
| HUMANO | 6.018 | 3.061 | 1.619 | 172 | 328 | 243 | 244 |
| solver antes da §74 | 5.971 | 3.175 | 1.548 | 168 | 371 | 247 | 150 |
| **solver com a §74** | **5.944** | **3.209** | **1.498** | **184** | **349** | **242** | **150** |

Os 184 B54 continuam **todos em encontro T** (`B54ctx={'TEE': 184}`) — nenhum foi parar fora de
amarração. A parede **8284580 saiu do top 20** (divergência 204,7 → 3,3); o novo topo é
8284589/8284590 com 124,0, que são o caso já documentado em §7 (o humano não constrói essas
paredes inteiras).

---

## 7.12 CORPUS DA §74 VERSIONADO — EVIDÊNCIA, NÃO NORMA

A auditoria independente do commit `2c55211` fechou em **SUPPORTED WITH LIMITATIONS**. A única
limitação material era esta: a geometria do BUTANTÃ sobre a qual todos os números da §74 foram
medidos **não estava versionada**, então nada disso era reproduzível de fora do ambiente. É
exatamente essa limitação que esta missão fecha.

| item | caminho |
|---|---|
| corpus (geometria mínima) | `reference_projects/butanta_r08_lt/s74_corpus/` — `geometry.json`, `t_nodes.json`, `wall_8284580.json`, `snapshot_v1.json` |
| biblioteca que lê o corpus e chama o motor REAL | `tools/audit/s74_corpus.py` |
| extrator (regera o corpus) | `tools/audit/extract_butanta_corpus.py` |
| testes | `tests/test_s74_corpus_butanta.py` |
| runner de auditoria | `tools/audit/audit_s74_corpus.py` — `python tools/audit/audit_s74_corpus.py` imprime PASS/FAIL caso a caso |

**STATUS: EVIDÊNCIA / NÃO NORMA.** O corpus existe para reproduzir as medições da §74. A modulação
humana ali registrada **não** vira golden: o projeto humano continua sendo referência medida e,
onde viola regra do produto, não é copiado (§8.1).

Nenhuma decisão de "cabe / não cabe" é reimplementada na bancada: a biblioteca entrega o corpus às
funções reais do motor (`assign_openings_to_walls`, `extend_wall_ends_to_junctions`,
`build_wall_graph`, `_t_intersection_room_assessment`, `_t_intersection_room_ok`,
`solve_building_blocks_all_courses`). Diff de motor desta missão: **zero** — nenhum `.py` sob
`nuvem/` foi tocado e `PIER_PHYSICAL_FIT_TOLERANCE_CM` continua intocada.

### Reproduzido pelo corpus versionado

34 paredes de alvenaria · 44 aberturas · 37 encontros T. Dez T reprovam o teste de espaço sem a
§74; **três passam a caber com ela** — nós de bancada **24, 44 e 46**, faltando respectivamente
**0,012 cm**, **0,003487 cm** e **0,003487 cm**. Os controles na MESMA parede principal já
passavam pela mesma magnitude com sinal contrário: nó **12** (sobra 0,003487 cm, mesma principal
dos nós 44/46) e nó **26** (sobra 0,012 cm, mesma principal do nó 24). Os **sete** restantes
continuam reprovando: **4,001054 cm** (nós 19/20/39), **15,012** e **14,997 cm** (nós 30 e 18),
**20,005** e **19,997 cm** (nós 28 e 22).

Parede 8284580 (chave `W27` no corpus): humano `48 B39 + 12 B34` (60 peças); solver **sem** a §74
`14 B39 + 51 B34 + 5 C09 + 1 B19`, divergência **204,7**; solver **com** a §74 `48 B39 + 11 B34 +
1 B19`, divergência **3,3**.

Saturação sobre o conjunto físico das 17 fiadas (hash `S74_SNAPSHOT_V1`):

| tolerância | peças | sha256 do conjunto físico |
|---|---|---|
| flag desligada | 8.750 | `b152406adb779655cf0f3d8fcc960f490ba3b8706bac090918de9e3cc3c60067` |
| **0,05 cm** | **8.723** | `0a42e2ec4fee65a441dd749f5df555ae3be17c54bfd3d652952a803d8328ff13` |
| 0,10 cm | 8.723 | **o mesmo sha256** |
| 0,30 cm | 8.723 | **o mesmo sha256** |

Hard gates **0/0/0/0** (colisões · não-modular · sem apoio · invasão de vão) em todos os casos.
Legado (`strategy=None`) byte-idêntico: **8.939 peças, assinatura `0a2704e4faaf`**. Suíte completa
do repo com o corpus: **1.234 passaram · 0 falharam** (eram 1.195 antes destes testes).

**O legado ficou auditável.** `strategy=None` não entra no fluxo CHANNEL, então a §74 não
pode alcançá-lo. Isso era alegação de bancada; agora está no corpus como dois casos
(`legacy_cases`): **8.939 peças, `sha256 3ba22aa08913ac5d…`, idêntico com a flag ligada e
desligada**.

**O que este corpus NÃO cobre, declarado no próprio corpus.** `_t_intersection_room_ok` é
uma **conjunção**: exige espaço para o B54 na parede principal **e** espaço para o B34 na
que chega. Aqui só a primeira perna é exercida — a boneca mais apertada dos 37 T tem
**69,0002 cm** contra **34 cm** exigidos, folga de 35 cm. A segunda perna não tem cobertura
de regressão neste corpus; o bloco `coverage` de `t_nodes.json` declara isso e um teste
confere a declaração. A perna do B54 é justamente a que a §74 muda.

**A regra histórica continua intacta.** O verificador do acervo
(`tools/documentation/verify_reference_inventory.py`) exige que
`nuvem/REGRAS_MODULACAO_BLOCOS.md` seja *append-only* em relação à base protegida. Conferido:
o arquivo de hoje ainda **começa exatamente** pelo conteúdo de `2521d1e`, a base deste PR — a
§74 foi reescrita dentro do texto que este próprio PR acrescentou, não sobre regra herdada.

**Método: um grafo novo por solve.** O motor grava nos próprios nós a marca de decisão
única da §72. Reaproveitar o mesmo grafo entre configurações faria a busca de paridade
rodar de verdade só na primeira e ser curto-circuitada nas seguintes — compararia coisas
diferentes. Medido: com grafo novo por solve os hashes são **os mesmos**, ou seja, isto não
muda resultado nenhum; muda a validade do método.

A maior variação de modelagem medida neste corpus é **0,013251 cm** (comprimento de parede
0,013251 cm · ponta de parede 0,013054 cm · espaço medido no T 0,013251 cm). A tolerância de
0,05 cm é **3,8×** esse valor e fica **80×** abaixo do primeiro caso materialmente insuficiente
(4,001054 cm).

### O que isto NÃO declara

- **O smoke real no Revit continua PENDENTE.** O bloqueio é o modal
  `TaskDialog_Project_Not_Saved_Recently`, sem acesso de operador para dispensá-lo (§7.10).
  Nenhum número de Revit foi estimado aqui.
- **Nada disto declara a §74 "totalmente auditada".** Versionar o corpus remove a limitação
  material apontada; o veredito sobre o corpus novo cabe à **auditoria independente**, que ainda
  não se pronunciou sobre ele. Até lá, o status permanece **SUPPORTED WITH LIMITATIONS**, com o
  smoke de Revit em aberto.

---

## 8. PADRÕES HUMANOS DESCOBERTOS — PENDENTES DE APROVAÇÃO

Nenhum destes foi codificado.

| padrão | frequência | exemplos | impacto | interpretação sugerida |
|---|---|---|---|---|
| **Coluna vertical de compensador** | 27 colunas, **230 peças = 28% de todos os especiais dele**; 26 ancoradas numa JAMBA, 1 numa ponta, **0 no meio da parede** | 8284574 x=220 C04 em 12 fiadas; 8284515 x=970 C04 em 11 fiadas | o solver tem 13 colunas (15%), **2 delas no meio da parede** | COMMON_PATTERN. O humano empurra a sobra não-modular para uma coluna encostada numa vertical que JÁ existe e mantém o resto do pano limpo. Implicaria aceitar junta corrida controlada ali — contraria a regra #1 como está escrita |
| **Junta coincidente tolerada** | 4,6% das juntas do humano coincidem com a fiada de baixo; **21 juntas contínuas ≥4 fiadas, máx 12** | 8284526 seis verticais de 7 fiadas | solver tem 0 | A regra #1 do produto é MAIS dura que o projeto de referência |
| **B19 no meio da parede** | humano 103, solver 22 | — | — | já registrado na §56.3; confirma que não é defeito |
| **Compensadores encostados** | humano 97 pares (C04+C09), solver 42 | — | — | consequência das colunas |
| **B34 nas pontas do trecho** | humano 93,7% na 1ª/2ª/penúltima/última posição, 6,3% no meio | — | solver 12,4% no meio | COMMON_PATTERN, mas o desempate não alcança (ver §73 rejeitada): depende do comprimento do trecho, não de escolha entre empates |

---

## 8.1 PADRÕES PENDENTES — LISTA CONSOLIDADA

Nenhum destes foi codificado. Todos conflitam com uma regra atual do produto ou dependem de
decisão sua.

| # | padrão | evidência | conflito |
|---|---|---|---|
| 1 | **Coluna vertical de compensador ancorada na jamba** | 27 colunas, 230 peças = **28% de todos os especiais do humano**; 26 em jamba, 1 em ponta, **0 em meio de parede** | implica aceitar junta vertical controlada — conflita com a regra #1 |
| 2 | **Junta contínua tolerada** | humano tem **21 juntas de 4+ fiadas (máx 12)** e 4,6% das juntas coincidindo com a fiada de baixo; solver tem 0 | a regra #1 do produto é MAIS dura que o projeto de referência |
| 3 | **Compensadores encostados** | humano 97 pares (C04+C09), solver 38 | consequência do padrão 1; conflita com a regra #2 |
| 4 | **B19 em meio de parede** | humano 103, solver 63 | já registrado como não-defeito na §56.3; sem conflito, só divergência |
| 5 | **B34 nas pontas do trecho** | humano 93,7% na 1ª/2ª/penúltima/última posição | não é codificável como desempate — ver §73 rejeitada |

**Decisão do produto que este relatório registra explicitamente:** a regra #1 (junta vertical
contínua proibida) permanece como está. O produto pode ser mais restritivo que a referência; o
projeto humano não é gabarito quando viola regra do produto. Os casos ficam classificados como
`HUMAN_PROJECT_SPECIFIC` / `PENDING_PRODUCT_DECISION`, nunca copiados.

---

## 9. RESPOSTAS OBRIGATÓRIAS — FECHAMENTO

1. **A posse da região dos nós era realmente a maior causa sistêmica?**
   **Sim, e continua sendo.** Ela explica **15 das 20** paredes mais divergentes no estado final.
   A convenção era fixa por papel (B54 → Fiada A na principal, B34 → Fiada B na que chega), o que
   correlaciona a fase pela planta inteira: 37/10 contra 23/23 do humano.

2. **Quanto da divergência caiu por causa dela?**
   Divergência total **2.575 → 1.727 (−33%)**; média por parede **75,7 → 50,8**. Contra a `main`
   (3.080) a queda é de **44%**. Seis das 20 piores saíram do top 20 (8284557 302→0, 8284579 222→0,
   8284567 164→0).

3. **Quantos trechos mudaram de comprimento?**
   **208 das 406 fiadas-parede (51%)** mudaram o conjunto de comprimentos dos seus trechos livres.

4. **Quantos passaram a aceitar mais B39?**
   **245 trechos passaram a exigir MENOS bloco de ajuste** (103 passaram a exigir mais, líquido
   +142). Trechos com resto bom: **33,3% → 38,7%**.

5. **Onde os B34 ficaram depois da correção?**
   38,3% em ponta de parede, 9,6% em nó central, 0,4% em nó de extremidade, 14,3% em vão,
   37,4% em meio de parede livre. **A menos de 20 cm de um nó: 50,2% — o humano tem 50,3%.**

6. **B54 continua restrito a T/+?**
   **Sim. 168 peças, todas em T, todas a menos de 20 cm de um nó.** Zero em cruz, zero fora de
   amarração. O humano: 172, idêntico. A nova divisão dos trechos não alterou nenhum contexto.

7. **Quantos C09/C04 próximos de B54 ainda existem e por quê?**
   Dos 374 compensadores, **10,2% estão a ≤20 cm de um B54** (humano 6,2%; antes da correção 11,8%).
   A causa é o comprimento residual do trecho entre a amarração e a próxima fronteira — são
   consequência do comprimento, não de regra de nó nem de microajuste: nos 105 trechos em que
   sobrou especial existindo alternativa limpa, a alternativa custaria ≥1 B34 a mais, e o próprio
   humano nunca paga isso (0 de 105 casos dele).

8. **O §66 ainda move alguma abertura para uma posição com modulação final pior?**
   **Não, nos casos medidos.** Sweep completo da abertura que ele moveu (8079001): o offset escolhido
   (+10) tem **7 C09 contra 13 no offset 0** e mais B39. O caso que levantou a suspeita
   (parede 8284534) deixou de existir: ele não move mais aquelas aberturas, e a composição saiu
   peça por peça igual à do humano.

8.5 **Quanto do resíduo não é defeito?**
   **20% dos 1.727 pontos.** 100 são as três paredes de 99 cm que o humano **não constrói
   inteiras** (ele cobre 588 cm de cada, o solver 1.002 cm — medido peça a peça, não por
   atribuição), e 248 são duas paredes em que o **solver está melhor** (fecha com um B34 onde o
   humano usa `C04+C09`). A cobertura total é praticamente igual: +0,8%.

9. **Quantas diferenças restantes são peculiaridades humanas não aprovadas?**
   **3 das 20** piores paredes têm `PROJECT_SPECIFIC_HUMAN_PATTERN` como causa (coluna de
   compensador na jamba). No total da planta, o padrão responde por **28% dos especiais do humano**
   (230 de 826 peças) contra 15% do solver — é a maior diferença estrutural que sobra e depende de
   decisão sua.

10. **Alguma nova violação de hard gate foi introduzida?**
    **NÃO.** Colisões 0, não-modular 0, peças sem apoio 0, invasão de abertura 0 — nas três
    execuções reais no Revit e na bancada. A `main` tinha 78 não-modular. As 4 paredes que o auditor
    de amarração reprova são **as mesmas antes e depois** desta missão.

---

## 9.1 RESPOSTAS DA RODADA ANTERIOR (mantidas)

1. **B39 virou o bloco predominante?** Sim: cobertura 61,3% → 63,4% (humano 61,8%), 3.175 peças
   contra 3.061 do humano.
2. **B54 está restrito a T/cruz?** Sim: 168, **todos em T**, todos a menos de 20 cm de um nó.
3. **B54 suspeito fora desses contextos?** **Nenhum**, nem no solver nem no humano.
4. **Onde os B34 estão?** 37,7% em ponta de parede, 10,5% em nó central, 14,3% em vão, 37,1% em meio
   de parede livre; 51,2% a menos de 20 cm de um nó.
5. **Aproximaram-se da distribuição humana?** Sim em todas as bandas: 0–20 cm de um nó 45,1% →
   51,2% (humano 50,3%); >100 cm 10,5% → 8,1% (humano 7,4%).
6. **Quantos B34 no meio sem justificativa?** 103 enterrados no meio do trecho (12,4%), contra 65
   (6,3%) do humano — 38 a mais.
7. **Compensadores evitáveis removidos?** Trechos com especial existindo alternativa limpa:
   137 → 105, **exatamente o número do humano**.
8. **Quantos dos restantes são necessários?** Dos 105, **todos** pela régua do próprio humano (a
   alternativa limpa custaria ≥1 B34 a mais, e ele nunca paga isso). Mais 399 trechos em que
   nenhuma composição só de B39/B34 fecha o comprimento.
9. **Compensadores perto de B54?** 8,3% a menos de 20 cm de um B54 (antes 11,8%; humano 6,2%).
10. **B19+B34 que poderiam ser B54?** 121 no envelope de 54 cm (humano 107, antes 139) — a diferença
    é pequena e o humano também faz.
11. **O microajuste move para pior que offset 0?** **Sim**, medido: na 8284534, +5 dá 7 C09 contra 1
    em offset 0.
12. **A 8284522 ainda viola a regra #1?** **Sim, pelo auditor do motor** — `CONTINUOUS_VERTICAL_JOINT`
    em X≈434,5 cm, 14 fiadas. Inalterado pela §72 (era assim antes também). Pela régua geométrica
    deste relatório (fiadas 0–11, excluindo verticais estruturais) ela aparece limpa: **as duas
    réguas medem coisas diferentes e as duas estão no relatório** — a do auditor inclui o contorno
    da peça de nó, que é onde essa junta está.
13. **Taxa de incompatibilidade do B34?** 4,9% (76 de 1.548); humano 2,5%.
14. **Custo de desempenho?** Nenhum: solve 27 s → 21 s na bancada.
15. **O que falta depende de regra não aprovada?** Sim, o maior item: a **coluna de compensador na
    jamba** (28% dos especiais do humano) e a tolerância dele a junta corrida controlada.

---

## 10. ENTREGA

**Branch** `claude/butanta-modulation-physical-fixes` · último commit de motor `2c55211` (§74) ·
**PR** [#42](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42) — **OPEN, draft, NÃO mergeado**.

Arquivos tocados desde `2521d1e` (base desta missão):

```
 docs/checkpoints/2026-09-17-butanta-convergencia-humano.md  |  730 +++++++++++++
 nuvem/REGRAS_MODULACAO_BLOCOS.md                            |  220 +++++
 nuvem/core/engine/wall_stepper.py                           |  343 ++++++-
 nuvem/core/wall_modeling.py                                 |   26 +
 tests/test_node_region_ownership.py                         |  255 +++++
 tests/test_t_room_physical_tolerance.py                     |  183 +++++
 tests/test_tie_parity_fill_balance.py                       |  238 +++++
 7 files changed, 1993 insertions(+), 2 deletions(-)
```

### Estado do Revit — congelado, não tocado

Última leitura possível: **17/09 14:21**, antes do modal. Documento `butanta testes` aberto, com o
lote único `20260917-022526` de 8.737 peças (a modulação **anterior** à §74, gerada na madrugada) e
3 aberturas deslocadas 10 cm pela §66. **Esse arquivo foi salvo em disco** — o lembrete de
salvamento que travou a sessão da madrugada foi dispensado por uma opção de salvar, não por
*Cancelar*. Existe agora uma cópia de segurança verificada por sha256 (§7.10).

Desde então: **nenhuma escrita, nenhum purge, nenhum reset, nenhum save**. O modal
`TaskDialog_Project_Not_Saved_Recently` continua aberto e o canal MCP continua congelado. O HUMANO
nunca recebeu Transaction — `IsModified = false` em todas as leituras.

### STATUS: **READY FOR FINAL REVIT SMOKE**

| frente | estado |
|---|---|
| motor (§72 + §74) | implementado, medido, auditado |
| suíte completa | 1.234 passaram, 0 falharam (1.195 antes do corpus) |
| suíte focada | 58 passaram |
| legado (`strategy=None`) | byte-idêntico — `0a2704e4faaf` |
| hard gates | 0 / 0 / 0 / 0 |
| saturação da tolerância | provada peça a peça (0,05 = 0,10 = 0,30) |
| determinismo | repetição byte-idêntica |
| convergência com o humano | divergência 1.707,7 → 1.502,2; 8284580 204,7 → 3,3 |
| **restauração controlada do TARGET** | **passo 1 de 10 feito — 2 a 10 PENDENTES** |
| **aplicação da §74 no Revit (run 1/2/3)** | **PENDENTE — bloqueio modal, sem acesso humano** |
| **readback / screenshots / lote único no Revit** | **PENDENTE** |

**Não está pronto para merge** e não foi declarado como tal. O que falta é execução real no Revit,
não código: a sequência exata está em §7.10. Quando o modal for dispensado em *Cancelar* /
*Não salvar*, retomar por `q_activate.py` e seguir a lista.

**Capturas:** 22 imagens (11 casos × HUMANO/TARGET) em `scratchpad/shots/`, com realce local
aplicado (`*_hi.png`) — são do estado **anterior** à §74; as de depois fazem parte do smoke pendente.
