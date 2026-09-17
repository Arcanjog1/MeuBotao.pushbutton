# Auditoria adversarial independente — guarda de ESPAÇO FÍSICO do nó T

**Data:** 2026-09-17
**Branch:** `claude/jolly-ritchie-0bq5f6`
**HEAD auditado:** `55e990d` (merge do PR #41 na `main`)
**Postura:** tentar REFUTAR. Produção, solver e PR #42 intocados.
**Artefatos:** `tests/test_t_room_physical_guard_independent_audit.py`
(11 verificações, pytest) e `tests/audit_t_room_physical_guard.py`
(mesma bateria + fronteiras medidas, roda sem pytest).

---

## 0. Ressalva de escopo — a §74 não foi localizada

A missão pede o veredito sobre a **§74**. Busca em camadas, conforme
`CLAUDE.md` (termo exato → sinônimos → entidades relacionadas → headings
→ símbolo de código), em **todas** as referências buscadas por fetch:

| Onde | Resultado |
|---|---|
| `nuvem/REGRAS_MODULACAO_BLOCOS.md` na `main` (`55e990d`) | maior seção = **§51** |
| mesma regra na branch do PR #42 (`759bcd4`) | maior seção = **§72** |
| todas as branches remotas / todos os PRs abertos (#7…#47) | nenhuma §73 ou §74 |
| `git log --all` por "seção 73/74" | nenhum commit |
| `r_reset_vaos.py` em todo o histórico e no disco | **não existe** |

Não inventei a regra (proibição explícita do `CLAUDE.md`). O que foi
auditado é o **objeto físico que os dez itens da missão descrevem**: a
guarda de espaço no nó T (`_t_intersection_room_ok`) e a guarda física de
jamba (`PIER_PHYSICAL_FIT_TOLERANCE_CM`). O veredito da seção 12 vale
para **essa** tese; se a §74 afirmar algo além disso, ela precisa ser
apresentada (arquivo + SHA) para o veredito ser reemitido.

---

## 1. Independência do método

As constantes físicas foram **redigitadas a partir do bloco**, nunca
lidas do motor para serem comparadas consigo mesmas:

```
B54 = 54 cm  →  27 cm exigidos para CADA lado do nó
B34 = 34 cm  →  34 cm exigidos na boneca
tolerância física de jamba = 0,05 cm
```

O oráculo é recalculado do zero em `physics_says_ok()`:
`min(direita, esquerda) >= 27 and boneca >= 34`.

A geometria é montada em **coordenadas de mundo** e só depois convertida
para o parâmetro `t` de cada parede. Isso importa: numa primeira versão
desta auditoria, o gerador passou coordenada de mundo direto como `t` e
produziu **10 "refutações"** de invariância. Eram defeito do auditor, não
do motor — `t` é medido desde `p0` (`_t_of_point_on_wall`). Fica
registrado porque é exatamente o falso positivo que uma auditoria
adversarial precisa descartar antes de acusar.

---

## 2. Conversões cm ↔ pés (item 1)

| Verificação | Medido |
|---|---|
| `_ft_to_cm(1)` | 30,48 cm (exato até 1e-9) |
| `_cm_to_ft(30.48)` | 1,0 (exato até 1e-12) |
| pior erro round-trip cm→pés→cm em [0, 2000] cm | **4,55e-13 cm** |
| `FEET_PER_METER` em `tolerances`/`modulation_math`/`wall_stepper` | idêntico, `1/0,3048` |

O ruído de conversão é **11 ordens de grandeza** menor que a tolerância
física de 0,05 cm. A guarda não é ruído de ponto flutuante disfarçado.

`PIER_PHYSICAL_FIT_TOLERANCE_CM = 0,05` < `PIER_FIT_TOLERANCE_CM = 0,30`,
como a documentação da CR-C04 afirma: a guarda física é a mais apertada.

---

## 3. ACHADO — as duas guardas têm tolerâncias diferentes por 1640x

Este é o achado central da auditoria, e ele **corrige uma leitura
plausível** do enunciado da missão (que trata "0,05 cm" e
`_t_intersection_room_ok` como se fossem a mesma fronteira).

| Guarda | Pergunta | Folga interna |
|---|---|---|
| `_t_intersection_room_ok` | "**cabe** a amarração especial aqui?" | `1e-6` **pés** = **3,048e-05 cm** |
| `_layout_fitted_to_physical_span` | "o que **já foi materializado** invade a jamba?" | `PIER_PHYSICAL_FIT_TOLERANCE_CM` = **0,05 cm** |

Razão entre elas: **1640x**.

Fronteira real do nó T, medida por bissecção a 1e-7 cm:

```
B54, lado direito : exige 26,999970 cm  (desvio -3,05e-05 cm do nominal)
B54, lado esquerdo: exige 26,999970 cm  (desvio -3,05e-05 cm)
B34, boneca       : exige 33,999970 cm  (desvio -3,05e-05 cm)
```

**Consequência:** no nó T, uma falta de **0,001 cm já reprova**. A guarda
do nó T **não absorve 0,05 cm** — e não deveria: quem precisa absorver
ruído acumulado de encontro é a decisão de *composição*, não a de
*ocupação*. Os itens 3 e 4 da missão foram executados nos dois lugares
separadamente, e cada um se comporta como a sua própria pergunta exige.

---

## 4. Casos exatamente abaixo/acima de 0,05 cm (item 3)

**Nó T** — falta de 0,001 / 0,049 / 0,050 / 0,051 / 0,10 cm: **reprova em
todos**, nos três eixos. Sobra dos mesmos valores: aprova em todos.

**Jamba** (onde os 0,05 cm valem) — fronteira inclusiva medida:

| Excesso sobre o limite físico | Resultado |
|---|---|
| 0,0 / 0,01 / 0,049 / **0,050** | layout **mantido** (tratado como ruído) |
| **0,0500001** / 0,051 / 0,10 / 0,30 | **remontado ou recusado** |

O remontado nunca termina além de `limite + 0,05 cm` — verificado em cada
caso. Com junta de argamassa na ponta (`trailing_open=False`), excesso de
até 1 cm passa intacto, como o contrato diz: a junta cede.

---

## 5. Sweep fino −0,10 → +0,10 cm (item 4)

Varredura de 0,001 em 0,001 cm em torno dos três limites do nó T
(201 pontos cada):

- nenhum ponto com **falta** de espaço aprovou;
- nenhum ponto com **sobra** de espaço reprovou;
- **exatamente uma** transição por eixo, a menos de 0,001 cm do nominal.

Nenhuma faixa cinzenta, nenhuma oscilação.

---

## 6. Monotonicidade (item 5)

**Por eixo:** varredura de 5 a 120 cm, passo 0,05 cm, nos três eixos —
uma vez aprovado, nunca mais reprova.

**Conjunta:** grade de 7³ = 343 pontos, **117.649 pares** comparados. Para
todo par (A, B) com todo espaço de B ≥ o de A: nenhum caso de
`room_ok(A)=True` e `room_ok(B)=False`.

**Sob geometria aleatória:** 800 cenários girados, acrescentando espaço
aleatório em cada eixo — nenhuma violação.

> Mais espaço físico **nunca** piorou `room_ok`. A propriedade se sustenta.

A guarda de jamba também é monótona: trecho físico de 95 a 105 cm, passo
0,01 cm, nunca passou de aceito para rejeitado.

---

## 7. Ruído positivo vs. negativo (item 6)

Em torno de cada limite, ruído de sinal oposto (0,001 / 0,01 / 0,03 /
0,05 / 0,1 cm): o lado seguro **sempre** aprova, o inseguro **sempre**
reprova. Longe do limite (folga de 1 cm), o sinal do ruído não muda nada.
Não existe assimetria dependente de sinal.

---

## 8. Faltas reais de 4, 15 e 20 cm (item 7)

Nos três eixos, para cada falta:

| Falta | Nó T | Com ruído favorável de 0,05 cm somado |
|---|---|---|
| 4 cm | reprova | **ainda reprova** |
| 15 cm | reprova | **ainda reprova** |
| 20 cm | reprova | **ainda reprova** |

Casos históricos da suíte preservados: porta a 5 cm do nó reprova; boneca
de 20 cm reprova.

---

## 9. Inversão, translação, rotação e permutação (item 8)

75 sondas × 8 transformações (inversão da principal, da boneca, das duas,
permutação de índices, três translações, e a composição de todas), mais
**1.200 cenários de fuzz** com paredes fora dos eixos (9 ângulos, origem
aleatória em ±500 cm, pontas e índices sorteados).

- **Veredito:** idêntico em todos os casos.
- **Medição:** idêntica a menos de 1e-6 cm.
- **Fuzz contra a física:** os 1.200 casos bateram com
  `min(dir, esq) >= 27 and boneca >= 34` recalculado independentemente —
  **zero divergências**.

---

## 10. Legado / `strategy=None` (item 9)

- `openings_per_wall=None` → `True` (retrocompatibilidade preservada).
- Lista **vazia** `[[], []]` **não** é tratada como `None`: a guarda
  continua ativa e reprova boneca de 20 cm.
- Nó sem `main_wall_idx` → `True` no veredito, `None` no assessment.
- **Nem `_t_intersection_room_ok` nem `_t_intersection_room_assessment`
  recebem `strategy`.** A guarda é puramente geométrica — nenhuma
  variação de estratégia do solver (CHANNEL, legado, ou futura) pode
  mover esta fronteira. Isso é mais forte do que "o legado não regrediu":
  o legado **não tem como** regredir por aqui.

---

## 11. Procedimento purge + preflight (item 10)

`r_reset_vaos.py` **não existe** no repositório nem no histórico. O
procedimento de purga que existe de fato é `purge_bench` / `purge_only`,
em `docs/checkpoints/evidence/2026-09-14-channel-revit/_harness/r_channel.py`
(linhas 84-98) e `q08_diag.py` (linhas 65-79).

### O que o procedimento garante (lido do código)

Dupla trava antes de apagar qualquer coisa:
1. o texto precisa começar com `BLOCK_LOT_MARKER + "|"` (carimbo do
   plugin — `_parse_block_lot_stamp`); **e**
2. o `wall_uid` precisa começar com `CHANNELBENCH-`.

Instância humana sem carimbo do plugin é inatingível pelas duas. O
documento HUMANO (`H`) é distinto do alvo (`T`), e `H.IsModified` é
registrado na saída.

### Lacuna encontrada — preflight independente

`step("PURGE", removed=..., remaining=...)` **registra** `remaining` mas
**não afirma** que ele é zero. Se a exclusão falhar parcialmente
(elementos pinados, membros de grupo, instâncias em outro nível), o run
segue sobre modelo sujo e o resíduo só aparece depois, como divergência
de contagem.

### Checklist de preflight (independente, para conferir a cada rodada)

Antes:
- [ ] `H.IsModified == False` no início — HUMANO intocado.
- [ ] `T` e `H` são documentos distintos.
- [ ] `len(bench_instances())` registrado como contagem **inicial**.
- [ ] Contagem total de `FamilyInstance` em `T` registrada — é o
      denominador que prova que a purga não foi larga demais.

Depois da purga, **barrar o run** se qualquer uma falhar:
- [ ] **`remaining == 0`** ← hoje só é registrado, não afirmado.
- [ ] `removed == contagem inicial de bench` — nem mais, nem menos.
- [ ] total de `FamilyInstance` caiu **exatamente** `removed`.
- [ ] `H.IsModified == False` ainda.
- [ ] nenhuma instância sem carimbo `CHANNELBENCH-` desapareceu.

Depois do run:
- [ ] `planned == created`.
- [ ] zero divergências de readback.
- [ ] lote único.
- [ ] idempotência: reaplicar move zero aberturas.

---

## 12. Veredito

### `SUPPORTED BY INDEPENDENT AUDIT`

— com o escopo e as duas ressalvas abaixo.

A tese física **"o motor só força a amarração especial no nó T quando o
espaço físico existe, e as tolerâncias envolvidas são ruído de cálculo,
nunca licença para invadir vão"** sobreviveu a todas as tentativas de
refutação: 11 verificações, ~1.200 casos de fuzz geométrico, 117.649
pares de monotonicidade, sweep de 0,001 cm e bissecção a 1e-7 cm.
**Nenhuma contradição encontrada.**

### Ressalva 1 — o veredito não cobre a §74 por nome

A §74 não existe em nenhuma referência buscada por fetch (seção 0). O
veredito vale para a **tese física** que os dez itens descrevem. Para
carimbar a §74 em si, é preciso o texto dela (arquivo + SHA).

### Ressalva 2 — uma leitura do enunciado é refutada

Se a §74 afirmar que **`_t_intersection_room_ok` absorve 0,05 cm**, essa
afirmação é **FALSA** e está medida na seção 3: a guarda do nó T usa
`1e-6` pés (3,048e-05 cm), **1640x mais apertada**. Os 0,05 cm vivem na
guarda de jamba, que responde a outra pergunta. Isso **não** enfraquece a
tese física — torna-a mais forte, porque o nó T é ainda mais rigoroso do
que se supunha. Mas o número, escrito no lugar errado, seria um erro
documental.

---

## 13. Achado colateral (fora do escopo, não bloqueia nada)

`nuvem/core/capture_export.py:57` — fallback de `ImportError`:

```python
except ImportError:
    FEET_PER_METER = 0.3048      # todas as outras 6 definições: 1.0 / 0.3048
```

Com `_ft_to_cm(v) = v * 100.0 / FEET_PER_METER`, o fallback devolve
**328,08 cm por pé** em vez de 30,48 — erro de fator 10,76 (= 1/0,3048²).
Só é alcançável fora do layout real do botão (o import normal funciona e
o teste `nuvem/tests/test_capture_export.py` lê a constante do próprio
módulo, então não detecta a inversão). Não afeta a guarda auditada e não
foi corrigido aqui — a missão proíbe tocar produção. Registrado para
decisão do usuário.

---

## 14. Reprodução

```bash
python3 -m pytest tests/test_t_room_physical_guard_independent_audit.py -q
python3 tests/audit_t_room_physical_guard.py     # + fronteiras medidas
```

Na HEAD auditada, com os artefatos desta auditoria presentes:

| Suíte | Resultado |
|---|---|
| `tests/test_script.py` | **262 passaram, 0 falharam** |
| `tests/ -m "not slow"` (suíte completa) | **1.189 passaram, 0 falharam**, 31 desselecionados |
| desta auditoria | **11 passaram** |

Nenhum arquivo sob `nuvem/` foi modificado (`git diff HEAD -- nuvem/`
vazio). Os únicos arquivos criados são os dois de teste/ferramenta e este
relatório.
