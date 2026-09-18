# Auditoria final independente do corpus da §74

**Data:** 2026-09-18 · **Auditor:** sessão independente ("Conta 2")
**HEAD auditado:** `f7c208bc6b2499470646379bb1449f3411f39478` (PR #42)
**Corpus:** `730ec5295ca1eada097851216ead6880cfb42352`
**Motor §74:** `2c55211632b96fbe1d3f31e9481df3ec8055cd6f`
**Método:** worktree isolado em `f7c208b`. Produção, `wall_stepper.py`,
`wall_modeling.py`, regras, golden, baseline e PR #42 **não tocados**.
Nenhum Revit.

---

## 0. Confirmação do objeto

```
$ git rev-parse origin/pr42-audit        → f7c208bc6b2499470646379bb1449f3411f39478
$ git branch -a --contains 730ec52       → butanta-modulation-physical-fixes, pr42-audit
$ git branch -a --contains 2c55211       → butanta-modulation-physical-fixes, pr42-audit
```

O README foi lido **primeiro**, antes de qualquer JSON. Ele é o documento
mais honesto do conjunto: declara a circularidade residual, a lacuna da
perna B34 e o limite de regeneração **antes** de o auditor perguntar.

---

## 1. Os verificadores, rodados por mim

| Comando | Reportado | **Medido por mim** |
|---|---|---|
| `tools/audit/audit_s74_corpus.py` | 40 casos, 40 PASS | **40 casos, 40 PASS, 0 FAIL, 93,6 s** |
| `pytest test_s74_corpus_butanta.py` | 39 passed | **39 passed, 163,96 s** |
| idem `-m "not slow"` | 33 rápidos | **33 passed, 6 deselected, 0,27 s** |

---

## 2. Auditoria estrutural independente

`tools/audit/audit_s74_independente.py` (novo, desta auditoria) **não
importa** `tools/audit/s74_corpus.py` nem o motor. Lê os JSON crus.

**`geometry.json` é input, não resultado:** 34 paredes, 44 aberturas,
espessura 14,0 em todas, chaves `W01…W34`, `input_order` sequencial e
declarado como parte do input, **0 aberturas órfãs** (recalculado por
distância ponto-segmento), 155 de 170 coordenadas com fração sub-cm
preservada (até 19 casas) — **sem arredondamento destrutivo**. Varredura
por `room_ok`, `expected`, `shortfall`, `divergen`, `veredito`:
**nenhum campo de resultado**.

**Governança:** `STATUS: EVIDENCE_NOT_NORM` nos quatro arquivos.

---

## 3. Os 37 T, os casos e os controles

`10` reprovam com a flag desligada, `7` com ela ligada, **exatamente 3
mudam: 24, 44, 46**.

| Nó | Principal | Falta B54 | OFF | ON |
|---|---|---|---|---|
| **24** | W04 | **0,012000 cm** | False | **True** |
| **44** | W02 | **0,003487 cm** | False | **True** |
| **46** | W02 | **0,003487 cm** | False | **True** |
| 12 (controle) | W02 | **−0,003487 cm** (sobra) | True | True |
| 26 (controle) | W04 | **−0,012000 cm** (sobra) | True | True |

**Simetria caso ↔ controle confirmada:** mesma parede principal, magnitude
idêntica ao 1e-9, sinal contrário — nos três pares.

**As 7 faltas materiais** reprovam nos dois estados: nós 19/20/39 a
**4,001054 cm**, 30 a **15,012000**, 18 a **14,996539**, 28 a
**20,004794**, 22 a **19,996513**.

---

## 4. ANCORA EXTERNA — a lacuna do README, fechada

O README declara:

> *"Quem quiser fechar o círculo por completo precisa ancorar `room_min`
> de pelo menos um nó contra uma medição independente do motor."*

**Feito.** Aritmética 2D pura sobre `geometry.json` — projeta cada abertura
no eixo da principal, acha a borda mais próxima em cada sentido. Sem
motor, sem `extend_wall_ends_to_junctions`, sem `tools/audit/s74_corpus.py`:

| Nó | Principal | `room_min` corpus | `room_min` independente | delta |
|---|---|---|---|---|
| 24 | W04 | 26,988000 | **26,988000** | 3,9e−14 |
| 44 | W02 | 26,996513 | **26,996513** | 2,5e−14 |
| 46 | W02 | 26,996513 | **26,996513** | 2,5e−14 |
| 12 | W02 | 27,003487 | **27,003487** | 1,2e−13 |
| 26 | W04 | 27,012000 | **27,012000** | 1,9e−13 |

A aritmética que fecha cada um:

```
nó 24  t(nó)=  642,000000   borda=  615,012000  → 26,988000   falta +0,012000
nó 26  t(nó)=  987,000000   borda= 1014,012000  → 27,012000   sobra −0,012000
nó 44  t(nó)= 1806,992005   borda= 1779,995492  → 26,996513   falta +0,003487
nó 46  t(nó)= 1596,995492   borda= 1569,998979  → 26,996513   falta +0,003487
nó 12  t(nó)= 1386,995492   borda= 1413,998979  → 27,003487   sobra −0,003487
```

**O achado físico:** em W04 os nós estão em `t` **exatamente redondo**
(642,000000 e 987,000000) e as bordas das aberturas carregam o
`+0,012`. Ou seja — a margem submilimétrica **vem da posição das
aberturas na planta**, não de arredondamento do motor. É precisamente a
alegação da §74, agora verificada fora dela.

Cobertura da âncora nos 37 T: `room_plus` casa em **26**, `room_minus` em
**24**, ao menos um lado em **30 de 37**. Onde não casa (7 nós), o limite
vem da reserva de outro nó — lógica do motor que esta aritmética não
replica de propósito.

---

## 5. A justificativa dos 0,05 cm

```
variação máxima de modelagem : 0,013251 cm
tolerância                   : 0,05 cm      = 3,77× a variação
próxima falta material       : 4,001054 cm  = 80,0× a tolerância
separação                    : 3,987802 cm de faixa vazia
```

Razões recalculadas por mim e conferidas contra as declaradas no corpus.

**A saturação não justifica o valor**, e o corpus diz isso sozinho — tanto
no README quanto na nota impressa pelo próprio runner oficial
(*"saturacao NAO justifica o valor 0,05 — só mostra que não há precipício
na fronteira"*). Concordo, e era a ressalva da minha auditoria anterior:
ela foi **absorvida no corpus**, não contornada.

---

## 6. Parede 8284580, hash, legado e portões

**Divergência recalculada por mim** pela definição versionada
(`100·comp/tot_h + 2·livre + 1·esp`), a partir das contagens medidas:

| | Composição do solver | comp | livre | esp | div |
|---|---|---|---|---|---|
| `flag_off` | 14 B39 + 51 B34 + 5 C09 + 1 B19 | 79 | 34 | 5 | **204,7** |
| `flag_on` | 48 B39 + 11 B34 + 1 B19 | 2 | 0 | 0 | **3,3** |

Confere com o gravado. Os números saem do motor (casos 10.off/10.on do
runner, que rodei), não de expectativa hardcoded.

**Nenhum teste promove o humano a gabarito.** Verifiquei
`test_a_parede_8284580_muda_de_composicao_com_a_secao_74`: não há
`divergência <= X` contra o humano nem `solver == humano`. O que existe é
igualdade com o valor **medido** mais uma comparação **relativa** entre os
dois estados.

**Hash `S74_SNAPSHOT_V1`** — li a normalização: uma linha por peça com
fiada, chave lógica da parede (`W01…W34`, **não** ElementId), código,
x/y, direção, comprimento e espelhamento; ordenadas. **Sem run id, sem
timestamp, sem ponteiro, sem ElementId, sem índice de lista.**

| Caso | Peças | sha256 |
|---|---|---|
| `flag_off` | 8750 | `b152406adb779655…` |
| `tol_0_05` | 8723 | `0a42e2ec4fee65a4…` |
| `tol_0_10` | 8723 | **o mesmo** |
| `tol_0_30` | 8723 | **o mesmo** |

O digest antigo `bc261fe485de635a` está gravado **marcado como não
oficial**, com a nota de que vinha do formato ad-hoc da bancada.

**Legado:** `strategy_none_flag_off` e `strategy_none_flag_on` — **8939
peças** e **o mesmo** `3ba22aa08913ac5d9582ba2e5920da8d42f8daff…` nos
dois. Não coincide com nenhum caso CHANNEL. A §74 não vaza para fora do
CHANNEL.

**Hard gates:** `0/0/0/0` nos **6** casos CHANNEL, incluindo a variante
pós-§66.

---

## 7. Não-circularidade, medida por mutação

Prendi `_t_intersection_room_ok` num valor fixo, por plugin pytest fora do
worktree:

| Mutação | Reportado pela Conta 1 | **Medido por mim** |
|---|---|---|
| preso em `True` | 16 falhas | **17 falhas** (12 rápidas + 5 lentas) |
| preso em `False` | 10 falhas | **11 falhas** |

Diferença de exatamente **+1** em cada direção — método de injeção
diferente, provavelmente o
`test_o_legado_e_identico_com_e_sem_a_flag_da_secao_74`, que na minha
mutação global também quebra (o hash versionado do legado muda). A
**direção e a magnitude confirmam**, e mais fortemente do que o
reportado.

As 12 falhas rápidas sob `True` são exatamente as fisicamente
significativas: a função do veredito, os três nós de fronteira, as sete
faltas materiais e o *"exatamente três mudam"*. **Um teste tautológico
não quebraria em nenhuma das duas direções.**

---

## 8. Limitações — o que continua aberto

1. **Circularidade residual da medição, reduzida mas não eliminada.** Os
   campos `room_*` foram produzidos pelo motor. Eu **fechei a âncora nos
   5 nós de fronteira** (seção 4) — que são os que decidem a §74. Os 7
   nós cujo limite vem de reserva de nó **continuam sem âncora externa**.
   Para esta auditoria isso é suficiente: a fronteira está ancorada. Para
   uma regeneração futura do corpus, não é.
2. **A perna do B34 não é exercitada.** `_t_intersection_room_ok` é uma
   conjunção; a boneca mais apertada dos 37 T tem **69,0002 cm** contra
   **34** exigidos — confirmado por mim. O corpus **declara** a lacuna em
   `t_nodes.json → coverage` e a confere por teste próprio. A §74 muda
   só a perna do B54, então isto não impede o veredito **sobre a §74** —
   mas é lacuna de cobertura da **função completa** e assim fica.
3. **Entradas brutas não versionadas.** Os quatro `sha256` de proveniência
   existem e são válidos. Regenerar exige a bancada; **auditar não** —
   auditei inteiramente sem elas.
4. **Ordem de entrada é input.** Repetição determinística confirmada
   (runner e pytest, processos separados, mesmos hashes; três solves de
   tolerância diferente com o mesmo sha). Translação e inversão cobertas e
   estáveis (casos 09.1/09.2). **Permutação não é alegada como
   invariante** — e não é testada como tal. Correto.

### Imprecisões documentais encontradas (não afetam o veredito)

- **Hard gates do legado.** O README diz que os portões *"ficam 0/0/0/0 em
  todos os casos gravados"*. Os dois casos de legado, gravados no mesmo
  arquivo, têm `non_modular=78` e `unsupported=67` — o estado
  pré-existente da `main`, que o CHANNEL corrige. **Idênticos** com a
  flag ligada e desligada, que é o que a §74 precisa provar. A frase
  merece o recorte "nos casos CHANNEL".
- **`target_s72.clean.json`.** O README diz *"que não tem hash gravado"* —
  mas ele **tem** `sha256 c96fa533e7c8fc26…`. E o total com a variante é
  **12,2 MB**, não *"cerca de 9 MB"*. Erros conservadores: o corpus tem
  mais proveniência do que declara.

---

## 9. Veredito

### `SUPPORTED BY INDEPENDENT AUDIT`

A limitação material da minha auditoria anterior — *"os números de corpus
não são reproduzíveis neste repositório"* — **está removida**. Reproduzi
tudo sem Revit, sem a bancada e sem as entradas brutas: os 37 T, os casos
24/44/46, os controles 12/26, as faltas de 4/15/20 cm, a parede 8284580,
os hashes normalizados, a saturação, os portões duros e o legado.

E fui além do que o corpus pedia: **ancorei `room_min` fora do motor** nos
cinco nós que decidem a questão, fechando a lacuna que o próprio README
declarava aberta. A margem submilimétrica vem da posição das aberturas na
planta — verificado por aritmética, não por inspeção do motor.

A não-circularidade da **decisão** está demonstrada por mutação (17/11
falhas). A circularidade da **medição** está declarada pelo corpus,
reduzida por mim na fronteira, e o que resta está dito com todas as
letras.

O veredito é **sobre a alegação específica da §74 no BUTANTÃ**. A ausência
de cobertura da perna do B34 permanece registrada como limitação de
cobertura da função completa — não da §74.

---

## 10. Respostas obrigatórias

| # | Pergunta | Resposta |
|---|---|---|
| 1 | Abriu o README primeiro? | **Sim**, antes de qualquer JSON |
| 2 | HEAD auditado? | `f7c208bc6b2499470646379bb1449f3411f39478` |
| 3 | Corpus commit? | `730ec5295ca1eada097851216ead6880cfb42352` |
| 4 | 40/40 audit? | **Sim** — 40 PASS, 0 FAIL, 93,6 s |
| 5 | 39/39 pytest? | **Sim** — 39 passed; 33 rápidos em 0,27 s |
| 6 | 24/44/46 reproduzidos? | **Sim**, e ancorados fora do motor |
| 7 | 12/26 reproduzidos? | **Sim**, com simetria de sinal confirmada |
| 8 | Faltas 4/15/20 reproduzidas? | **Sim**, reprovam nos dois estados |
| 9 | 8284580 reproduzida? | **Sim** — 204,7 → 3,3, divergência recalculada por mim |
| 10 | Hash reproduzido? | **Sim** — `0a42e2ec4fee65a4…` idêntico em 0,05/0,10/0,30 |
| 11 | Legado idêntico? | **Sim** — 8939 peças, `3ba22aa08913ac5d…` nos dois |
| 12 | Hard gates verdes? | **Sim** nos 6 casos CHANNEL. Legado é 78/67 — pré-existente e inalterado |
| 13 | Decisão é circular? | **Não** — mutação quebra 17 (True) e 11 (False) |
| 14 | Medição é circular? | **Parcialmente**, e declarado. **Fechei a âncora nos 5 nós de fronteira** |
| 15 | Isso compromete o veredito? | **Não** — a fronteira é o que decide, e está ancorada |
| 16 | Perna B34 coberta? | **Não** — boneca mínima 69,0002 cm vs 34. Declarado no corpus |
| 17 | Raw input ausente compromete? | **Não** — auditei sem ele. Limita regeneração, não auditoria |
| 18 | **Veredito final** | **`SUPPORTED BY INDEPENDENT AUDIT`** |
