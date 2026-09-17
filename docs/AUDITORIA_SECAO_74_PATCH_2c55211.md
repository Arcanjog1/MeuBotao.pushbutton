# Auditoria independente do patch real da §74 — `2c55211`

**Data:** 2026-09-17 · **Auditor:** sessão independente ("Conta 2")
**SHA auditado:** `2c55211632b96fbe1d3f31e9481df3ec8055cd6f`
**Contido em:** `origin/claude/butanta-modulation-physical-fixes`, `origin/pr42-audit`
**Método:** worktree isolado em `2c55211`. Produção, solver e PR #42 não tocados.

---

## 0. Correção — meu relatório anterior auditou referência desatualizada

Minha conclusão anterior (*"a §74 não existe"*) valia para o snapshot que eu
tinha: `759bcd4`, buscado por fetch às 17:2x. A branch avançou para
`6b04475` e **`2c55211` existe**. Após `git fetch origin --prune` e
`git fetch origin pull/42/head`:

```
$ git cat-file -t 2c55211      → commit
$ git branch -a --contains 2c55211
  remotes/origin/claude/butanta-modulation-physical-fixes
  remotes/origin/pr42-audit
```

**A conclusão anterior está retirada.** O que segue audita o patch real.

Também corrijo um argumento meu que estava **errado** — ver seção 4: eu
havia concluído que *"não há ruído a absorver"*. Essa medição usava cenas
sintéticas de coordenadas exatas. **Na planta real há ruído**, e ele está
na escala que a §74 cita.

---

## 1. O diff exato (itens A–E)

### A. A linha que mudou em `_t_intersection_room_ok`

```diff
-    if min(assessment["room_plus_ft"], assessment["room_minus_ft"]) + 1e-6 < T_INTERSECTION_B54_HALF_ROOM_FT:
+    tolerancia_ft = _t_intersection_room_tolerance_ft()   # SECAO 74
+    if min(assessment["room_plus_ft"], assessment["room_minus_ft"]) + tolerancia_ft < T_INTERSECTION_B54_HALF_ROOM_FT:
         return False
-    return assessment["room_incoming_ft"] + 1e-6 >= CORNER_B34_ROOM_FT
+    return assessment["room_incoming_ft"] + tolerancia_ft >= CORNER_B34_ROOM_FT
```

Duas comparações; o resto da função é idêntico. Nova função:

```python
T_ROOM_PHYSICAL_TOLERANCE = False

def _t_intersection_room_tolerance_ft():
    if not T_ROOM_PHYSICAL_TOLERANCE:
        return 1e-6
    return PIER_PHYSICAL_FIT_TOLERANCE_CM / 100.0 * FEET_PER_METER
```

### B. Como a flag chega

`wall_modeling.py:4121-4124`, dentro de
`_solve_building_blocks_all_courses_impl`:

```python
saved_room_tol = _stepper_repair.T_ROOM_PHYSICAL_TOLERANCE
_stepper_repair.T_ROOM_PHYSICAL_TOLERANCE = bool(
    kwargs.get("opening_reinforcement_strategy") is not None
    and CHANNEL_T_ROOM_PHYSICAL_TOLERANCE_ENABLED)
```

restaurada no `finally`. `_stepper_repair` é o import local da linha 4106
(`from core.engine import wall_stepper as _stepper_repair`).
**Verificado funcionalmente:** é o mesmo objeto de módulo em que a guarda
vive, e escrever a flag ali muda a tolerância lida
(`1,000e-06` → `1,640e-03` pés).

### C. O valor usado

`PIER_PHYSICAL_FIT_TOLERANCE_CM / 100 × FEET_PER_METER`. Medido:
**exatamente 0,05 cm**. **Nenhuma constante nova** — confere.

### D. Padrão histórico quando `flag=False`

`T_ROOM_PHYSICAL_TOLERANCE = False` por padrão no módulo, e `OFF` devolve
**exatamente `1e-6`** (identidade de ponto flutuante verificada, não
aproximação). Comportamento histórico preservado.

### E. `strategy=None`

`bool(None is not None and True)` = `False` → tolerância histórica.
**Legado idêntico.**

**Risco verificado e descartado:** a string `"NONE"` passaria em
`is not None` e ligaria a §74. Mas
`_opening_reinforcement_strategy_from_ui_value` faz
`return None if key == "NONE" else key` — a UI **normaliza para `None`
antes** do motor. O caminho está limpo.

---

## 2. A semântica muda? **SIM** (item 6)

Falta de espaço no lado do B54, OFF vs ON:

| falta (cm) | OFF | ON | divergem |
|---|---|---|---|
| 0,0000 | True | True | |
| 0,0010 | False | **True** | **SIM** |
| 0,0035 | False | **True** | **SIM** |
| 0,0100 | False | **True** | **SIM** |
| 0,0120 | False | **True** | **SIM** |
| 0,0200 | False | **True** | **SIM** |
| 0,0490 | False | **True** | **SIM** |
| 0,0500 | False | False | |
| 0,0510 / 0,10 / 0,30 / 1,00 / 4,001 | False | False | |

A fronteira **se move**, e move-se **só na faixa `(0 ; 0,05)` cm**.
Acima de 0,05 cm nada muda. Não é "só ruído numérico" no sentido de
float — é uma faixa submilimétrica real. A questão é se essa faixa é
**ruído de modelagem**, e a seção 4 responde.

---

## 3. Existe faixa física segura? **SIM** (item 4)

### O erro do meu relatório anterior

Minha medição anterior (9,6e-12 cm) montava o nó T **de coordenadas
exatas**. Repeti agora passando por `extend_wall_ends_to_junctions`, com
entrada limpa: **9,4e-13 cm** — a extensão de encontro **não amplifica**
ruído. Portanto o ruído relevante **não é de cálculo**: é da **geometria
da planta**.

### A medição certa — ruído da planta real

Corpus versionado `2026-09-10-butanta-test-walls.json` (46 paredes,
48 encontros T), desvio de cada espaço medido ao meio-centímetro mais
próximo:

```
medições                        : 144
com desvio > 1e-9 cm            : 107 de 144
MAIOR desvio                    : 0,013251 cm  (0,1325 mm)
mediana dos desvios não-nulos   : 0,001054 cm  (0,0105 mm)
```

Valores individuais: `625,013251` · `460,012198` · `273,990071` ·
`460,009000` · `224,008939` · `222,992005` …

**Os casos que a §74 cita (0,035 mm e 0,12 mm) caem exatamente dentro
desta faixa** — e esta medição é sobre geometria que a §74 **não usou**.
Corroboração independente.

### A faixa segura

| Escala | cm | relação |
|---|---|---|
| ruído de float | 9,6e-12 | — |
| **ruído da planta real (máx. medido)** | **0,013251** | — |
| tolerância OFF (`1e-6` pés) | 0,00003048 | **0,002× o ruído — NÃO cobre** |
| **tolerância ON (0,05 cm)** | **0,05** | **3,8× o ruído — cobre** |
| **menor falta real deste corpus** | **4,001054** | **80× a tolerância** |

> **Existe faixa vazia entre `0,0133` e `4,0011` cm**, e 0,05 cm fica
> dentro dela: **3,8× acima** do maior ruído medido e **80× abaixo** do
> próximo caso materialmente inválido.

O diagnóstico da §74 — de que `1e-6` pés é epsilon de float e **não**
tolerância de planta — **está correto e medido**.

---

## 4. Saturação (item 7) — confirma-se, mas não é o que parece

### No nível da guarda, isolada: **NÃO satura**

Sweep de 0 a 4,001 cm em passos de 0,0005 cm (8.002 pontos), variando a
constante:

```
tol=0,05 cm -> 100 aprovam, fronteira em 0,0495 cm
tol=0,10 cm -> 201 aprovam, fronteira em 0,1000 cm
tol=0,30 cm -> 600 aprovam, fronteira em 0,2995 cm
```

São fronteiras **diferentes**. A saturação **não é propriedade da
tolerância**.

### No corpus real: **satura, e a razão é a faixa vazia**

Sobre os 48 T do corpus versionado:

| tolerância | T reprovados | vs. 0,05 |
|---|---|---|
| 0,05 cm | 5 | — |
| 0,10 cm | 5 | idêntico |
| 0,30 cm | 5 | idêntico |
| 1,00 cm | 5 | idêntico |
| 2,00 cm | 5 | idêntico |
| 4,00 cm | 5 | idêntico |
| **4,01 cm** | **2** | **DIFERE** |

**A saturação confirma-se** — e quebra exatamente ao alcançar a menor
falta real (4,0011 cm). Mas note: **4,00 cm "satura" tanto quanto 0,05**.

> **Leitura correta:** a saturação prova que **não há precipício perto de
> 0,05 cm** — o que é verdade e é importante. Ela **não seleciona** 0,05
> como o número certo. Quem justifica 0,05 é a **escala do ruído**
> (seção 3), não a saturação.

**A assinatura `sha256 bc261fe485de635a` não pôde ser reproduzida** — ver
seção 6.

---

## 5. Bateria adversarial contra `2c55211`

Todas com a §74 **LIGADA**, contra o oráculo físico `min(lados) ≥ 27−tol
e boneca ≥ 34−tol` recalculado do zero:

| Teste | Resultado |
|---|---|
| monotonicidade por eixo (5→120 cm, passo 0,05) | **OK** nos 3 eixos |
| monotonicidade conjunta (117.649 pares) | **OK**, zero violações |
| fuzz 1.500 (rotação, translação, inversão, permutação) | **OK**, zero divergências |
| faltas de 4 / 15 / 20 cm, nos 3 eixos, OFF e ON | **reprovam sempre** |
| 4,001 cm | **reprova** OFF e ON |
| legado `openings_per_wall=None`, OFF e ON | **True** (retrocompatível) |
| testes próprios da §74 (`test_t_room_physical_tolerance.py`) | **10 passaram** |
| suíte completa em `2c55211` (`-m "not slow"`) | **1.313 passaram, 0 falharam**, 31 desselecionados |

**Ponta a ponta**, solver real no corpus versionado (46 paredes, 6 fiadas):

```
OFF : 1161 peças  sha=d63ce811c8b381c8  hard gates (col/nmod/vão/T) = (0, 28, 0, 0)
ON  : 1161 peças  sha=d63ce811c8b381c8  hard gates (col/nmod/vão/T) = (0, 28, 0, 0)
```

Saída **byte-idêntica**, composição idêntica
(`B39 713 · B34 316 · B54 45 · C09 41 · C04 32 · B19 14`), **hard gates
inalterados**. Coerente: nenhum T deste corpus cai na faixa
`(0 ; 0,05]` cm, então o patch é **inerte** aqui. Confirma que ele age
**só** na faixa submilimétrica. (Os 28 `non_modular` são pré-existentes,
idênticos nos dois.)

---

## 6. O que NÃO pude reproduzir — e por quê

A geometria dos eixos `8284xxx` **não está versionada**. Busca em toda a
HEAD do PR #42 (`6b04475`): `8284580` aparece em 4 arquivos
(o checkpoint, a regra, `wall_stepper.py` e `test_compensator_adjacency.py`),
**nenhum deles com `p0`/`p1`**. O `2026-09-10-butanta-test-walls.json`
contém ids `8079xxx` — **outro conjunto** (48 T, não 37). A lista de ids
das 34 paredes vive em `r_cfg.json`, na máquina Windows.

Logo, **não verificados independentemente**:

| Alegação da §74 | Status |
|---|---|
| 37 encontros T; 10 reprovam; 7 por margem real | **não reproduzível aqui** |
| nós 24 / 44 / 46 com falta de 0,12 / 0,035 / 0,035 mm | **não reproduzível aqui** |
| nós 12 / 26 passando com a margem de sinal oposto | **não reproduzível aqui** |
| `sha256 bc261fe485de635a` (saturação 0,05/0,10/0,30) | **não reproduzível aqui** |
| 8284580: divergência 204,7 → 3,3 | **não reproduzível aqui** |
| hard gates 0/0/0/0 no corpus de 34 paredes | **não reproduzível aqui** |
| legado 8.939 peças, assinatura `0a2704e4faaf` | **não reproduzível aqui** |

Isto **não é refutação** — é ausência de dado. O **mecanismo** por trás de
cada uma dessas alegações foi confirmado em geometria independente
(seções 3 e 4). Para fechar, basta versionar os eixos das 34 paredes
(`p0`/`p1` em pés, como o JSON de 2026-09-10).

---

## 7. Veredito sobre o patch real

### `SUPPORTED WITH LIMITATIONS`

**Sustentado:** o diagnóstico está correto e medido — `1e-6` pés é
epsilon de float (0,002× o ruído real da planta) e não cobria o ruído de
modelagem, que medi em até **0,1325 mm** em corpus independente. Existe
**faixa fisicamente segura** entre o ruído (0,0133 cm) e o próximo caso
inválido (4,0011 cm), e **0,05 cm fica dentro dela** com 3,8× e 80× de
margem. A mecânica é correta e conservadora: flag `False` por padrão,
legado byte-idêntico, restauração em `finally`, nenhuma constante nova,
monotonicidade e invariância preservadas, faltas reais de 4/15/20 cm
seguem reprovando, hard gates inalterados onde pude medir.

**Limitações:**

1. **Os números de corpus da §74 não são reproduzíveis neste repositório**
   (seção 6) — a geometria `8284xxx` não está versionada. Confirmei o
   mecanismo, não os valores.
2. **O argumento de saturação é mais fraco do que aparenta** (seção 4):
   0,05, 0,30 **e 4,00 cm** saturam igualmente. A saturação mostra
   ausência de precipício, **não** que 0,05 seja o número certo. Quem
   justifica 0,05 é a escala do ruído — e essa justificativa se sustenta.
3. **A semântica muda, sim**, na faixa `(0 ; 0,05)` cm. A medição apoia
   chamar essa faixa de ruído de modelagem, mas isso é **decisão física
   declarada**, não saneamento numérico. Convém que a §74 diga isso com
   essas palavras.

---

## 8. Respostas diretas

| # | Pergunta | Resposta |
|---|---|---|
| 1 | Auditou `2c55211`? | **Sim**, em worktree isolado |
| 2 | Diff exato da §74? | Seção 1 — 2 comparações, 1 função nova, 1 flag, wiring em `wall_modeling` |
| 3 | 0,05 cm muda semântica? | **Sim**, e só na faixa `(0 ; 0,05)` cm |
| 4 | A mudança é segura no corpus medido? | **Sim** no corpus que pude medir: 3,8× acima do ruído, 80× abaixo da menor falta real |
| 5 | 0,05 / 0,10 / 0,30 saturam? | **Sim no corpus, não na guarda.** 4,00 cm satura igual — a saturação não seleciona 0,05 |
| 6 | 4 / 15 / 20 cm continuam reprovando? | **Sim**, nos 3 eixos, OFF e ON, e com ruído favorável somado |
| 7 | Legado continua idêntico? | **Sim.** `strategy=None` → `False` → `1e-6` exato. UI `"NONE"` normalizada para `None` |
| 8 | Algum hard gate piora? | **Não** onde pude medir: `(0, 28, 0, 0)` idêntico OFF e ON |
| 9 | Reproduziu 8284580 204,7→3,3? | **Não** — geometria não versionada (seção 6) |
| 10 | Seu veredito anterior muda? | **Sim.** "§74 não existe" está **retirado**; "não há ruído a absorver" está **corrigido** — havia, e na escala citada |
