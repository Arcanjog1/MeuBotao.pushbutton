# CR-C1 — REVISÃO INDEPENDENTE (PR #26, HEAD `34bf696`)

| item | valor |
|---|---|
| revisado | `claude/cr-c1-expected-rows-fisico` `34bf696` |
| contra | `main` real `91258dd` (conferida por `git fetch`, não presumida do SHA histórico) |
| método | **medição própria** em worktrees isolados; o relatório da CR-C1 foi lido **depois** de reproduzir os números, nunca como fonte |
| identidade | `model.wall_stable_key` / eixo em coordenada global. **`W0xx` não foi usado como identidade em nenhuma medição** |
| escrita oficial | **nenhuma**. `git diff --name-only origin/main..34bf696 -- nuvem/benchmark/projects/` = **0 arquivos** |

## Veredito

> ### APPROVE
>
> A causa-raiz está correta, o novo contrato é físico e não-tautológico, o
> `95/94 → 0` é **prova geométrica** e não silenciamento, a capacidade de
> detectar ausência real **melhora** em vez de piorar, e o delta em todos
> os outros códigos é **zero**, medido e não presumido.
>
> Nenhuma correção é necessária. **Nenhum patch proposto.**

Ressalvas que **não** bloqueiam o merge estão em §6. O merge continua
**pendente de autorização explícita do usuário** — esta revisão não o
autoriza, não marca o PR `ready` e não o mescla.

---

## 1. Causa-raiz — confirmada

`settings.expected_rows` vem de `settings.num_courses`: o **teto de fiadas
do projeto inteiro**. O validador comparava esse número global com a
contagem ordinal de fiadas de **cada** parede:

```python
if expected_rows and indices and len(indices) < expected_rows:   # ANTES
```

As paredes do corpus real têm alturas diferentes (220/260/270/280/281cm).
Uma parede baixa **nunca** terá o número de fiadas do teto do projeto —
ela estava correta e era acusada assim mesmo.

O novo critério (`missing_course_above_cm`) pergunta o que é fisicamente
verificável: **ainda cabe uma fiada inteira abaixo do pé-direito desta
parede?** — `próximo passo + corpo da peça ≤ base_z + height`.

Dois pontos de projeto que confirmei no código e considero corretos:

- **Não é tautológico.** A altura vem de `height_cm` declarado, não é
  inferida das fiadas existentes. Se fosse inferida, o critério viraria
  "espera-se o que já está lá" e nunca acusaria nada.
- **Não reimplementa a política de empilhamento.** O critério não tenta
  dizer *onde* a próxima fiada cai — só se *cabe*. Um validador que
  duplica a regra que fiscaliza deixa de fiscalizar.

## 2. O `95/94 → 0` é prova física, não silenciamento

Esta era a pergunta central da revisão. Um zero pode vir de dois lugares
muito diferentes: da geometria, ou de o critério ter ficado **cego** (por
exemplo, `height_cm` ausente ⇒ sem veredito). Medi qual dos dois é
(`silence.py`):

| projeto | paredes | sem `height_cm` | sem blocos | **com veredito** |
|---|---|---|---|---|
| TGD | 97 | **0** | 0 | **97 (100%)** |
| TP1 | 96 | **0** | 0 | **96 (100%)** |

**Nenhuma parede ficou sem veredito.** O zero não vem de dado faltando.

A folga física de cada parede — `topo − z_da_fiada_mais_alta − altura da
peça` — medida nas 193 paredes dos dois projetos:

| | valor |
|---|---|
| folga mínima | **1,0 cm** |
| folga máxima | **1,0 cm** |
| distribuição | **1,0 cm em 193 de 193 paredes** |
| limiar para acusar | **20,0 cm** (o passo entre fiadas) |

No gabarito humano toda parede fecha o pé-direito com exatamente 1cm
sobrando — a junta. **Não cabe fiada nenhuma em nenhuma delas**, e a
margem até o limiar é de 19cm. O zero é geometria.

Reprodução do resultado nos dois lados (`g16.py` / execução direta dos
validadores sobre `reference.json`):

| projeto | árvore | `MISSING_ROW` | demais códigos de cobertura |
|---|---|---|---|
| TGD | `91258dd` | 95 | `ROW_MOSTLY_EMPTY` 85, `GAP_IN_ROW` 626, `PARTIAL_WALL` 4 |
| TGD | `34bf696` | **0** | **85 / 626 / 4 — idênticos** |
| TP1 | `91258dd` | 94 | `ROW_MOSTLY_EMPTY` 120, `GAP_IN_ROW` 615 |
| TP1 | `34bf696` | **0** | **120 / 615 — idênticos** |

O cenário de risco da skill `cr-verification` — um código cair enquanto
outro sobe — **não se materializou**: `ROW_MOSTLY_EMPTY` tem delta **zero**
nos dois projetos.

## 3. Casos discriminantes — bateria independente

Escrevi 14 casos **do zero** (`indep_c1.py`), sem reutilizar os testes da
própria CR-C1, e rodei a mesma bateria nas duas árvores. Comparação por
identidade física (`wall_stable_key`), nunca por `W0xx`.

| # | caso | esperado | `91258dd` | `34bf696` |
|---|---|---|---|---|
| 1 | parede completa até z=340 (h=340, topo em z=321) | sem achado | ✔ 0 | ✔ 0 |
| 2 | parede que para em z=301 e admite fiada em z=321 | **com achado** | ✔ 1 | ✔ 1 |
| 3a | base Z = 612 (caso real do TP1), completa | sem achado | ✘ **1** | ✔ 0 |
| 3b | base Z = 612, truncada | com achado | ✔ 1 | ✔ 1 |
| 4 | meia-fiada no topo | sem `MISSING_ROW` | ✘ **1** | ✔ 0 |
| 4b | topo cobrindo metade do comprimento | sem `MISSING_ROW` | ✘ **1** | ✔ 0 |
| 5 | parede com abertura + faixa de verga intercalada | sem achado | ✘ **1** | ✔ 0 |
| 6 | parede dividida em 2 segmentos completos | sem achado | ✘ **2** | ✔ 0 |
| 7a | **ausência real** — parou na metade | com achado | ✔ 1 | ✔ 1 |
| 7b | **ausência real** — falta exatamente a última | com achado | ✔ 1 | ✔ 1 |
| 7c | `expected_rows=1` não pode esconder truncamento real | com achado | ✘ **0** | ✔ 1 |
| 7d | `expected_rows=999` não pode inventar achado | sem achado | ✘ **1** | ✔ 0 |
| 8a | invariância à ordem de entrada | igual | ✔ | ✔ |
| 8b | determinismo (3 execuções) | igual | ✔ | ✔ |

**7 casos falham na `main`; os 14 passam na CR-C1.**

Os casos **1 e 2** são o par discriminante exato: mesma altura, mesma
espessura, mesmo projeto, separados por **19cm** na cota da última fiada —
e o critério separa os dois corretamente nas duas árvores.

### As 28 ausências reais continuam detectáveis

Este era o segundo risco central: um critério que zera o gabarito pode ter
zerado tudo. Não zerou.

- **7a, 7b e 7c continuam acusando** na CR-C1 — a detecção de ausência
  real está preservada.
- **7c é uma melhora, não uma regressão**: na `main`, um `expected_rows`
  baixo **escondia** um truncamento real (0 achados); com a CR-C1 o
  truncamento é acusado. O critério físico não pode ser silenciado por um
  parâmetro global.
- Na saída do solver do TGD, o ramo do topo cai apenas **30 → 28**: 28 dos
  30 achados são defeitos reais e **continuam acusados**. Reproduzi a
  discriminação: as 2 que saem fecham em `z=321` (`321+19 = 340` = topo
  exato); as 28 que ficam param em `z=301` e ainda admitem fiada em
  `z=321`. A separação entre as duas classes é de **19cm**.
- **Zero paredes passaram a ser acusadas.**

## 4. Testes da CR-C1

`tests/regression/test_validator_coverage_expected_rows_cr_c1.py`:
**19 passam** em `34bf696` (executado por mim). O relatório da CR-C1
declara 16 falhando na base — coerente com os 7 casos da minha bateria
independente que falham em `91258dd`.

## 5. As duas falhas de baseline — conferidas nas duas árvores

Executei `tests/regression/test_benchmark_baselines.py` **inteiro** nas
duas árvores, separadamente:

| árvore | resultado | asserção do TP1 |
|---|---|---|
| `91258dd` (**sem** o patch) | **2 failed, 7 passed** (453s) | `JUNCTION_MISSING_BINDING` 8 → 9, delta 1, `REGRESSAO CRITICA` |
| `34bf696` (**com** o patch) | **2 failed, 7 passed** (465s) | **mesma asserção, mesmos valores** |

**As 2 falhas são pré-existentes e nenhuma é nova.** São os mesmos dois
testes (`[torre_easy_lo_r00_tgd]` e `[torre_easy_lo_r00_tp1]`), com a
mesma mensagem e os mesmos números, na árvore **sem** o patch.

Não reexecutei a suíte completa de ~48min: a evidência acima é direta
sobre o arquivo que falha, e o único arquivo de produção tocado pela CR-C1
é `validate_wall_coverage.py`.

## 6. Ressalvas que **não** bloqueiam o merge

Nenhuma altera o veredito. Registradas para não se perderem.

1. **`expected_rows` continua na assinatura de `validate_wall` sem
   decidir nada.** É deliberado (compatibilidade com chamadores antigos) e
   está comentado no código. Fica como parâmetro morto — candidato a
   remoção numa limpeza futura, não nesta CR.

2. **Consumidores de `rows_expected`: nenhum.** O finding deixou de
   emitir `rows_expected` e passou a emitir `highest_course_z_cm` /
   `missing_course_z_cm` / `wall_top_z_cm`. Procurei consumidores
   (`git grep`): fora dos extratores que *produzem* `settings.expected_rows`
   e de `solver_bridge.py` (que lê `settings`, não o finding), **nenhum
   gate, relatório ou score lê `rows_expected`**. Não há quebra.

3. **Parede sem `height_cm` fica sem veredito.** É a escolha certa (o
   contrário seria inferir a altura das fiadas e virar tautologia), e no
   corpus real o caso **não ocorre** (0 de 193). Mas é um ponto cego
   silencioso: se um extrator futuro parar de preencher `height_cm`, o
   ramo do topo apaga sem avisar. Sugestão para uma CR futura — **não para
   esta**: emitir um achado informativo de cobertura ausente.

4. **Divergência de documentação, sem efeito em código.** O docstring diz
   *"a maior folga LEGÍTIMA medida no gabarito humano é 11cm"*; a folga que
   o critério de fato usa é **1,0cm** (as duas medidas diferem por usar o
   corpo da peça `_C` de 9cm em vez do bloco de 19cm). O código está certo
   e a margem real é **maior** que a documentada — a documentação é que é
   conservadora demais.

## 7. O que esta revisão não faz

- **Não marca o PR #26 `ready`.**
- **Não mescla nada.** Merge na `main` exige autorização explícita do
  usuário para aquele merge específico.
- **Não propõe patch** — não há correção necessária.
- **Não mistura nada da CR-C2**, que corre em branch e documento próprios.
