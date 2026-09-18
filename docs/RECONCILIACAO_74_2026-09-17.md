# Reconciliação factual — §74, as duas guardas e a escala do ruído

**Data:** 2026-09-17 · **Sessão:** auditoria independente (a que o pedido
chama de **Conta 2**) · **Branch:** `claude/jolly-ritchie-0bq5f6` ·
**HEAD:** `27b1a3c231a1b6055432217c8851195a5c91d6d7`

---

## 0. Correção de premissa — esta sessão É a Conta 2

O pedido foi endereçado a quem **implementou a §74** e está prestes a
rodar um apply no Revit. **Esta sessão não é essa.** Esta é a auditoria
independente. Concretamente:

| | |
|---|---|
| Commits desta sessão | `3d4c687`, `709ef47`, `27b1a3c` — **os três só de auditoria** |
| Arquivos tocados | 2 de teste/ferramenta + 3 de documentação |
| `git diff origin/main..HEAD -- nuvem/` | **vazio** |
| Patch §74 | **não existe aqui** — nunca escrevi um |
| Apply no Revit | **nunca rodei nenhum**, e não tenho acesso ao Revit nesta sessão |

Portanto os itens 1, 4 e 9 do pedido — "mostre o commit da §74", "mostre o
diff", "se §74 muda room_ok, pare e me mostre" — **não têm resposta minha
que não seja esta**: não há o que mostrar, porque o patch não está aqui.
Quem tem o patch é a outra sessão.

**Não há apply para parar.** A ordem "PARE ANTES DO PRÓXIMO APPLY" precisa
chegar à sessão que de fato ia rodá-lo.

---

## 1. §74 — estado factual (item 1)

| Campo pedido | Valor |
|---|---|
| branch atual | `claude/jolly-ritchie-0bq5f6` |
| HEAD atual | `27b1a3c231a1b6055432217c8851195a5c91d6d7` |
| commit que implementa §74 | **nenhum** |
| arquivo | — |
| função | — |
| diff | — |
| pushado ou local? | **nem um nem outro** |

**Não está "apenas local".** Em clone **completo** (`is-shallow` = false,
**482 commits**), verificado de novo agora:

- nenhuma ref (local ou remota) tem `## 74.` em `nuvem/REGRAS_MODULACAO_BLOCOS.md`;
- maior seção na `main` (`55e990d`) = **§51**; na branch do PR #42 (`759bcd4`) = **§72**;
- `git log --all -S"_t_intersection_room_ok" -- nuvem/core/engine/wall_stepper.py`
  → últimos toques são `5ddcd7c` e `30f4466`, **ambos já na `main`**, nenhum recente;
- `r_reset_vaos.py` nunca existiu em commit algum.

Se a §74 existe, ela está **na árvore de trabalho não commitada da outra
sessão**. Só aquela sessão pode informar SHA e diff.

---

## 2. As duas guardas, separadas (item 2)

São funções diferentes, em pontos diferentes do pipeline, respondendo a
perguntas diferentes. **Nenhuma das duas foi alterada por esta sessão.**

### A) `_t_intersection_room_ok` — "o B54 cabe aqui?"

- **Onde:** `nuvem/core/engine/wall_stepper.py:1408`
- **Quando:** **antes** de decidir a amarração, sobre geometria de eixo.
- **O que compara:** espaço livre medido na parede contra `27 cm` para
  cada lado (metade do B54) e `34 cm` na boneca (B34).
- **Tolerância:** `1e-6` **pés** = **3,048e-05 cm**, embutida na
  comparação (`+ 1e-6 <` / `+ 1e-6 >=`). **Não** usa
  `PIER_PHYSICAL_FIT_TOLERANCE_CM`.
- **Consequência do `False`:** não é erro — o solver **degrada** para
  `B34|B34`, que é o que o projeto humano BUTANTÃ faz nos 3 nós T sem
  espaço medidos.

### B) `_layout_fitted_to_physical_span` — "o que já foi materializado invade?"

- **Onde:** `nuvem/core/engine/wall_stepper.py:6131`
- **Quando:** **depois** de montar o layout, sobre peças com posição real.
- **O que compara:** onde a última peça **termina** contra o fim físico do
  trecho, e **só** quando a ponta não tem junta de argamassa
  (`trailing_open`).
- **Tolerância:** `PIER_PHYSICAL_FIT_TOLERANCE_CM` = **0,05 cm**.
- **Consequência:** acima de 0,05 cm o trecho é **remontado** com o maior
  conteúdo modular que cabe; se nem isso couber, devolve `None` (trecho
  vazio em vez de peça dentro do vão).

### Por que os números são diferentes

A guarda **B** existe porque o **fit modular** usa
`PIER_FIT_TOLERANCE_CM = 0,30 cm` para absorver ruído acumulado de
encontro ao decidir a **composição** — e esse comprimento *snapado*
depois também **posiciona** as peças. A guarda B é o freio: o valor
snapado pode mudar o que fecha, **nunca** o que atravessa. Ela é
calibrada contra a **diferença entre 0,30 e o real** (as 41 invasões de
0,12 a 0,267 cm medidas no corpus), não contra ruído de ponto flutuante.

A guarda **A** não tem snap nenhum antes dela. Ela mede eixo contra eixo.
O ruído que ela enxerga é só o de conversão — e esse é **microscópico**
(seção 4). Por isso a folga dela pode ser, e é, milhares de vezes menor.

> **Reutilizar 0,05 cm em A seria importar a calibração de um problema
> que A não tem.**

**A sua §74 mudou A para usar a tolerância de B?** Não sei, e não posso
saber: não tenho o patch. Só a outra sessão responde.

---

## 3. O veredito não valida a §74 (item 3)

**Concordo integralmente**, e é o que o relatório já dizia. Da seção 12 de
`AUDITORIA_INDEPENDENTE_GUARDA_ESPACO_T.md`:

> **Ressalva 1 — o veredito não cobre a §74 por nome.** (…) Para carimbar
> a §74 em si, é preciso o texto dela (arquivo + SHA).

O `SUPPORTED BY INDEPENDENT AUDIT` vale para **o código em `55e990d`**, a
`main` atual — não para nenhum patch que eu não vi. Registrado aqui para
não haver dúvida.

**"A Conta 2 auditou exatamente este patch?"** → **NÃO.**

---

## 4. Prova de escala do ruído (item 5)

Medição nova: nós T com espaço **exatamente 27,000 cm** (e 34,000 na
boneca), sob 12 ângulos × 6 origens × 6 origens × 2 sentidos =
**2.592 amostras**, comparando o que o motor mede contra o valor exato.

```
pior desvio do valor exato : 9,5923e-12 cm   (= 9,59e-11 mm)
```

Esse é **o ruído real** que a guarda A enxerga. Lado a lado:

| Escala | cm | mm | × sobre o ruído |
|---|---|---|---|
| ruído medido (pior caso) | 9,59e-12 | 9,59e-11 | 1× |
| **tolerância ATUAL (1e-6 pés)** | **3,048e-05** | **3,048e-04** | **3.177.540×** |
| 0,035 mm | 0,0035 | 0,035 | 3,6e+08× |
| 0,12 mm | 0,012 | 0,12 | 1,3e+09× |
| **`PIER_PHYSICAL_FIT_TOLERANCE_CM`** | **0,05** | **0,5** | **5,2e+09×** |
| menor falta física real | 4,0 | 40 | 4,2e+11× |

### Os casos, sob a tolerância de hoje e sob a hipotética de 0,05 cm

| Caso | falta (cm) | HOJE (1e-6 ft) | SE fosse 0,05 |
|---|---|---|---|
| ruído puro de cálculo | 9,6e-12 | APROVA | APROVA |
| **0,035 mm** | 0,0035 | **REPROVA** | **APROVA** |
| **0,12 mm** | 0,012 | **REPROVA** | **APROVA** |
| **0,05 cm (0,5 mm)** | 0,050 | **REPROVA** | **APROVA** |
| 1 mm | 0,100 | REPROVA | REPROVA |
| falta real | 4,0 | REPROVA | REPROVA |
| falta real | 15,0 | REPROVA | REPROVA |
| falta real | 20,0 | REPROVA | REPROVA |

### Leitura

1. **A tolerância atual já é folgada** para o ruído: **3,2 milhões de
   vezes** acima do pior desvio medido. Não há ruído numérico sendo
   confundido com falta física hoje.
2. **0,05 cm não é justificado pela escala do ruído** em A: seria
   **5,2 bilhões** de vezes o ruído medido.
3. A faixa em que as duas discordam — falta entre 3,05e-05 cm e
   0,05 cm — **não é ruído**. São faltas **reais** de até meio milímetro.
   Trocar a tolerância ali **é mudança semântica da fronteira
   "cabe/não cabe"**, não saneamento numérico.
4. Os casos fisicamente reais (**4, 15, 20 cm**) reprovam nas duas — a
   mudança não os afeta. Ela age **só** na faixa submilimétrica.

> Se a intenção da §74 era absorver ruído, **os dados dizem que não há
> ruído a absorver em A**. Se o objetivo é outro (aceitar meio milímetro
> de falta real por alguma razão de projeto), é uma decisão física que
> precisa ser declarada como tal — e justificada pela fiada, não pelo
> ponto flutuante.

Reproduz com `tests/audit_t_room_physical_guard.py` (fronteiras por
bissecção) e a tabela acima em
`tests/test_t_room_physical_guard_independent_audit.py`.

---

## 5. Purge safety — implementado (item 6)

`tools/preflight/purge_guard.py` (+ `test_purge_guard.py`, 7 testes).
Python puro, roda em CPython e IronPython, **não importa Revit nem
solver**. `assert_purge_clean(...)` **aborta** com `PurgeNotCleanError`
se:

- **`remaining != 0`** ← o pedido central;
- `removed` ≠ contagem inicial de bancada;
- o total de `FamilyInstance` caiu mais que `removed` (a purga alcançou
  algo que não era da bancada);
- `human_modified` verdadeiro.

**Onde NÃO coloquei, e por quê:** o harness vive em
`docs/checkpoints/evidence/2026-09-14-channel-revit/_harness/`, que é o
**registro versionado de uma entrega passada**. Editar ali corromperia o
checkpoint. O guard ficou em `tools/preflight/` e a integração é de duas
linhas, no lugar do `step("PURGE", ...)`:

```python
from tools.preflight.purge_guard import assert_purge_clean
report = assert_purge_clean(
    removed=len(olds), remaining=len(bench_instances()),
    expected_removed=n_before, total_before=total_before,
    total_after=total_after, human_modified=H.IsModified)
step("PURGE", **report)          # levanta antes daqui se sujo
```

Se preferir que eu edite o `_harness` mesmo assim, ou que ele seja
copiado para fora do checkpoint antes, me diga — não fiz por conta
própria. **Solver intocado**, como pedido.

---

## 6. O que NÃO foi feito, conforme instruído

| Item | Estado |
|---|---|
| 7. `capture_export.py:57` | **não corrigido**; fica para PR separado, fora do #42 |
| 8. `REGRAS_MODULACAO_BLOCOS.md` com §74 | **não atualizado** |
| — apply no Revit | **não rodado** (nem nesta sessão, nem antes) |
| — PR #42 | **não tocado** |
| — solver / regras físicas / baseline | **não tocados** |

---

## 7. Entrega da reconciliação (item 9)

| Campo | Resposta |
|---|---|
| **HEAD** | `27b1a3c231a1b6055432217c8851195a5c91d6d7` |
| **COMMIT §74** | **não existe** nesta sessão nem em ref alguma (482 commits) |
| **DIFF §74** | **indisponível** — o patch não está aqui |
| **SEMÂNTICA ANTES** | `room_ok` exige 27 cm/lado e 34 cm na boneca, folga `1e-6` ft |
| **SEMÂNTICA DEPOIS** | **desconhecida** — depende do patch que não tenho |
| **QUAL GUARDA USA 0,05 cm** | `_layout_fitted_to_physical_span` (jamba, pós-materialização) |
| **QUAL GUARDA USA 1e-6 ft** | `_t_intersection_room_ok` (nó T, pré-decisão) |
| **POR QUÊ** | B freia o snap de 0,30 cm do fit modular (invasões reais de 0,12–0,267 cm); A não tem snap antes dela e só vê ruído de conversão, medido em **9,6e-12 cm** |
| **STATUS PUSHED/LOCAL** | §74: **nenhum dos dois**. Esta reconciliação: pushada em `claude/jolly-ritchie-0bq5f6` |
| **A Conta 2 auditou exatamente este patch?** | **NÃO.** |

### Conclusão operacional

**Não rodar Revit ainda** — e a razão é mais simples do que a do pedido:
o patch §74 não está em nenhuma referência versionada. Antes de qualquer
apply, a outra sessão precisa **commitar e pushar** a §74 para que exista
um SHA auditável. Com esse SHA, reauditar é rápido: a bateria já está
escrita e roda contra qualquer HEAD.
