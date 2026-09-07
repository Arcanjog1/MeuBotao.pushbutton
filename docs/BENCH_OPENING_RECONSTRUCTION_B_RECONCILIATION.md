# CR-B — RECONCILIAÇÃO DO GABARITO DE ABERTURAS

> **Etapa de RECONCILIAÇÃO DE DOMÍNIO E EVIDÊNCIA. Nada foi implementado.**
>
> `nuvem/benchmark/projects/**` (`reference.json`, `input.json`,
> `baseline.json`, `reference_score.json`), o solver e
> `nuvem/REGRAS_MODULACAO_BLOCOS.md` estão **intocados** — conferido por
> `git diff --name-only`. Nenhuma constante de produção foi alterada.
> Nenhuma regra normativa foi escrita. C02/C10/Junction/S1/S2 **não
> iniciadas**.

---

## Base / branch / HEAD

| item | valor |
|---|---|
| base obrigatória | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` |
| `origin/main` no início da sessão | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` (**confere**) |
| branch de trabalho | `claude/reconciliacao-gabarito-aberturas-uynv0q` |
| diff | **só documentação e diagnóstico** — `docs/` + `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b/` |
| gabarito | **intocado** |
| merge / PR de produção | **nenhum** |

---

## 1. Fontes de evidência

### 1.1 O que foi lido

- `docs/BENCH_OPENING_RECONSTRUCTION_A_IMPLEMENTATION.md` (integral)
- `docs/PROJECT_STATUS.md` (integral)
- `docs/START_HERE.md`, `docs/REFERENCE_CORPUS.md` (roteamento)
- `nuvem/REGRAS_MODULACAO_BLOCOS.md` — busca por seção (10.6, 10.9, L/T/X,
  reserva de nó), conforme a recuperação progressiva do `CLAUDE.md`
- evidência reproduzível da CR-A:
  `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_a/`
- código de produção: `nuvem/core/engine/opening_audit.py`,
  `nuvem/benchmark/extract/reconstruct.py`

### 1.2 Dois documentos citados que NÃO existem no repositório

Registro de fato, não de opinião — os dois são citados como autoridade pelo
`docs/PROJECT_STATUS.md` e pelo `README` da pasta de evidência da CR-A:

| citado em | arquivo citado | estado |
|---|---|---|
| `PROJECT_STATUS.md` ("Trabalho ativo", CR-A) e `bench_opening_reconstruction_a/README.md` §6 | `docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` | **ausente** — nunca commitado (`git log --all --diff-filter=A` não retorna nada) |
| `PROJECT_STATUS.md` (C04, C3) | `docs/C04_INDEPENDENT_FINAL_REVIEW.md` | **ausente** |

Consequência para esta CR: **a revisão independente da CR-A não pôde ser
lida**. Onde o `PROJECT_STATUS.md` resume as conclusões dela (correção de
overclaim de vocabulário, recontagem de 3→4 deslocamentos de 0,06cm), o
resumo foi usado como registro secundário, **não** como fonte primária.
Nenhuma conclusão desta reconciliação depende desses dois documentos.

### 1.3 As quatro fontes de verdade, separadas

Conforme §3 do enunciado, nunca misturadas nas fichas:

| fonte | de onde vem | disponível em |
|---|---|---|
| **(A) GEOMETRIA MEDIDA DO REVIT** | `input.json` do TGD — 167 paredes e **82 aberturas `confidence="measured"` com `source_element_id`**, extraídas de um documento Revit SEPARADO (`TESTE MODULACAO (2026).rvt`) | **só TGD** |
| **(B) MODULAÇÃO HUMANA** | `reference.json` — `rows`/`blocks` realmente posicionados pela pessoa | TGD e TP1 |
| **(C) RECONSTRUÇÃO DO BENCHMARK** | `reference.json` — `walls`/`openings`/`junctions`, produzidos por `reconstruct.py` a partir de (B) | TGD e TP1 |
| **(D) RESULTADO DO SOLVER** | — | **não usado nesta CR** |

**O `input.json` do TP1 NÃO é fonte medida.** Ele é gerado por
`reconstruct.input_from_reference()` a partir do próprio `reference.json`
do TP1 (96 paredes no input = 96 no reference; **0 aberturas `measured`**).
Nesta CR ele nunca é tratado como evidência independente.

### 1.4 Armadilha de identidade confirmada

`reference.json` e `input.json` do TGD usam **espaços de nomes de parede
diferentes**: 97 vs 167 paredes, **0 pares com mesmo `id` E mesma `key`**,
só 24 `key` em comum. `W003` do reference **não é** `W003` do input.

Isto atinge diretamente a leitura do relatório da CR-A: a linha
`W003 env=[579,765] cons=[594,750] == BURACO MEDIDO [594.0,750.0] entre
W017 e W015` mistura o `W003` do **reference** (hospedeiro) com `W017`/
`W015` do **input** (vizinhas medidas). O script está correto; a frase
induz a erro. **Todas as fichas desta CR usam coordenada de mundo (XY) como
identidade física**, com o `W0xx` só como rótulo auxiliar.

### 1.5 Discrepância 17 × 19 resolvida

`repro_envelope.py` imprime `assinatura_15cm=17`; a doc da CR-A diz **19**.
Não é divergência de dados: é **definição de contador**. O script conta
`spread_inicio == 15.0 AND spread_fim == 15.0` (estrito); a doc e
`repro_axis_gap.py` contam `>= 14,9` nas duas jambas. Os 2 casos da
diferença são, nos dois projetos, `W005` e `W006` em `[309.01, 440.0]`, com
`spread_inicio = 14,99`. `detector_state_b.json` confirma 19 aberturas com
`jamb_spread_cm = 15.0` por projeto. **Os 19 desta CR são o conjunto
`>= 14,9`.**

### 1.6 Evidência nova produzida aqui (reproduzível)

Tudo em `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b/`,
READ-ONLY, sem escrita em `projects/`:

| script | o que mede |
|---|---|
| `case_dossier.py` | ficha por caso: identidade física XY, envelope, consenso, junções, trechos e aberturas medidas no mesmo eixo, peças humanas em cada jamba |
| `void_occupancy.py` | o que ocupa fisicamente o vão — blocos de **qualquer** parede na faixa em planta — e quais eixos perpendiculares cruzam o hospedeiro |
| `lintel_test.py` | **teste da verga**: cobertura do consenso pelas fiadas ACIMA do vão |
| `lintel_discriminates.py` | valida o teste da verga nos 94/92 trechos, estratificado por procedência medida |
| `measured_jamb_confirmation.py` | cada jamba está confirmada por geometria medida (fim de parede colinear OU face de perpendicular)? |
| `measured_vs_human.py` | divergências numéricas entre parede medida e jamba humana |
| `measured_neighbourhood.py` | os 9 casos que o método grosseiro da CR-A não casou |
| `criterion_selectivity.py` | seletividade de um critério estrutural (sem limiar de largura) nos 94/92 trechos |
| `roundtrip_probe.py` | o gabarito é regenerável offline a partir do próprio `reference.json`? |
| `split_threshold_probe.py` | um limiar de `WALL_SPLIT_GAP_CM` consegue separar os 19? |
| `projection_split.py` | projeção estrutural do candidato "duas paredes separadas" |
| `make_tables.py` | gera as tabelas deste documento a partir dos JSON |

---

## 2. O que os 19 casos são, fisicamente

O achado central desta reconciliação, uniforme nos **19 casos e nos dois
projetos**, medido em `void_occupancy.py`:

```
envelope  [579, 765]  ~=  faces EXTERNAS de duas paredes perpendiculares
consenso  [594, 750]  ==  faces INTERNAS dessas mesmas duas paredes
tiras de 15cm         ==  a PEGADA da parede perpendicular (o nó)
```

Para `W003` do TGD (o caso canônico da CR-A), medido:

- junções `T` registradas em `t = 587,0` e `t = 757,0`, com paredes
  perpendiculares de 14,0cm — que ocupam, no eixo do hospedeiro, as faixas
  `[580, 594]` e `[750, 764]`;
- `blocos_no_consenso = 0`: **nenhuma peça humana, de nenhuma parede, em
  nenhuma fiada**, dentro de `[594, 750]`;
- as peças que ocupam as tiras de 15cm pertencem à **parede
  perpendicular** (`B54 - 14x19x54`, `MEIO BLOCO - 14x19x19`), não ao
  hospedeiro — com **uma exceção medida**: `W017` do TGD tem peça própria
  (`CANALETA J` / `MEIO BLOCO` em `t = [735, 754]`) entrando na tira,
  que é a peça de amarração do próprio hospedeiro atravessando o nó.

Isto é a **alternância de amarração em nó L/T** descrita na seção 10.6 das
regras: em fiadas alternadas o nó é ocupado ora pela peça do hospedeiro,
ora pela peça da perpendicular. A diferença de 15,0cm entre as duas
situações é exatamente `B34 − B19 = 34 − 19`, como a CR-A já havia
estabelecido. **Esta CR não altera a regra de X nem a de parede curta, e não
promove 15cm a constante de domínio.**

### 2.1 Teste da verga — e a prova de que ele discrimina

Discriminante físico entre abertura e paredes separadas: **porta/janela tem
alvenaria acima do vão; espaço entre duas paredes não tem.**

`lintel_discriminates.py`, sobre **todos** os trechos detectados:

| grupo | TGD (94) | TP1 (92) |
|---|---|---|
| **A)** com abertura `measured` do Revit casada | n=62 — **60 com verga**, cobertura mediana acima **97%** | n=0 (input reconstruído) |
| **B) os 19 da assinatura ~15cm** | n=19 — **0 com verga**, cobertura máxima acima **0%** | n=19 — **0 com verga**, máxima **0%** |
| **C)** demais | n=13 — 12 com verga, mediana **98%** | n=73 — 71 com verga, mediana **98%** |

- **Nenhum dos 19 casa com qualquer uma das 82 aberturas medidas do
  Revit** (verificado por interseção; `dos 19, quantos casam = 0`).
- Em 14 dos 19 existe pelo menos uma fiada acima do vão e a cobertura dela
  sobre o consenso é **exatamente 0%** — evidência positiva de ausência de
  verga.
- Nos outros 5 (`W004`/`W007` em `[594,750]`, `W015`(TGD)/`W017`(TP1),
  `W046`, `W047`) o vão vai do piso ao topo da parede — **não há fiada
  acima**. Ali o teste é silencioso; a classificação se apoia nos outros
  três sinais.
- **Contraexemplo honesto, registrado:** `W016` do TGD tem duas aberturas
  de altura plena (`226` e `231`cm) **com `source_element_id` medido**
  (`6558473`, `6558472`) e sem verga — porque a parede modelada tem 220cm e
  a verga fica acima da alvenaria modelada. Logo **"sem verga" sozinho não
  prova "não é porta"**; é um sinal entre quatro, e é por isso que os 5
  casos de altura plena não são classificados só por ele.

### 2.2 Confirmação por geometria medida — 19 de 19 (só TGD)

O método da CR-A (`repro_axis_gap.py`) casou **10 de 19** e a branch
diagnóstica relatou **16 de 19**. A causa da diferença foi encontrada e é
metodológica, não substantiva: o filtro de colinearidade de ±3cm descarta
paredes medidas **deslocadas lateralmente** (±13 / ±15cm) e o teste só
procura "buraco entre duas paredes colineares", ignorando o caso "a parede
morre numa perpendicular".

`measured_jamb_confirmation.py` testa cada jamba das duas formas
fisicamente válidas — **fim de parede colinear** OU **face de parede
perpendicular** — e o resultado é:

```
jambas confirmadas: 38 de 38   (29 por FACE_DE_PERPENDICULAR, 9 por FIM_DE_PAREDE_COLINEAR)
casos com as DUAS jambas confirmadas: 19 de 19
resíduo máximo 0,259 cm   mediana 0,001 cm
```

Ampliando só a busca lateral (`measured_neighbourhood.py`), 6 dos 9 casos
"divergentes" da CR-A casam **exatamente** — `W004` e `W007`, três vezes
cada, com paredes medidas curtas (94cm) a −13 / +15cm do eixo
reconstruído, terminando em `594,00` / `750,00` / `919,00` / `425,00`.

---

## 3. Tabela dos 19 casos — TGD e TP1

Gerada por `make_tables.py` a partir dos JSON de evidência. A identidade é
a **coordenada de mundo das duas jambas**; o `id ref` é rótulo auxiliar. As
paredes perpendiculares citadas na coluna "reserva de nó" são ids do
**`reference.json`**; as das colunas "jamba medida" são ids do
**`input.json`** — espaços de nomes distintos (§1.4).


### torre_easy_lo_r00_tgd

| # | id ref | identidade fisica (jamba lo XY -> hi XY, cm) | envelope | consenso | larg | fiadas | perp. lo / hi (reserva de no') | blocos no vao | verga | jamba lo medida | jamba hi medida | classificacao | conf. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `W003` | (-1071.5, 24.0) -> (-1071.5, 180.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 13 | W052@587[580.0, 594.0] / W055@757[750.0, 764.0] | 0 | NAO (1 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W006` +0.001 | FACE_DE_PERPENDICULAR `W007` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 2 | `W004` | (-656.5, -246.0) -> (-656.5, -145.0) | [309.0, 440.0] | [324.0, 425.0] | 101 | 12 | W034@317[310.0, 324.0] / W044@432[425.0, 439.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | FIM_DE_PAREDE_COLINEAR `W047` +0.259 | FACE_DE_PERPENDICULAR `W052` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 3 | `W004` | (-656.5, 24.0) -> (-656.5, 180.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 14 | W052@587[580.0, 594.0] / W055@757[750.0, 764.0] | 0 | n/a (vao de altura plena) | FACE_DE_PERPENDICULAR `W006` +0.001 | FACE_DE_PERPENDICULAR `W007` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 4 | `W004` | (-656.5, 349.0) -> (-656.5, 450.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 12 | W066@912[905.0, 919.0] / W075@1027[1020.0, 1034.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W056` +0.001 | FIM_DE_PAREDE_COLINEAR `W044` -0.257 | DUAS_PAREDES_SEPARADAS | ALTA |
| 5 | `W005` | (-401.5, -246.0) -> (-401.5, -145.0) | [309.01, 440.0] | [324.0, 425.0] | 101 | 8 | W034@317[310.0, 324.0] / W044@432[425.0, 439.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | FIM_DE_PAREDE_COLINEAR `W042` +0.259 | FACE_DE_PERPENDICULAR `W052` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 6 | `W005` | (-401.5, 24.0) -> (-401.5, 180.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 7 | W052@587[580.0, 594.0] / W055@757[750.0, 764.0] | 0 | NAO (10 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W006` +0.001 | FACE_DE_PERPENDICULAR `W007` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 7 | `W005` | (-401.5, 349.0) -> (-401.5, 450.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 8 | W066@912[905.0, 919.0] / W075@1027[1020.0, 1034.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W056` +0.001 | FIM_DE_PAREDE_COLINEAR `W041` -0.257 | DUAS_PAREDES_SEPARADAS | ALTA |
| 8 | `W046` | (-336.5, 24.0) -> (-336.5, 180.0) | [94.0, 280.0] | [109.0, 265.0] | 156 | 13 | W052@102[95.0, 109.0] / W055@272[265.0, 279.0] | 0 | n/a (vao de altura plena) | FACE_DE_PERPENDICULAR `W006` +0.001 | FACE_DE_PERPENDICULAR `W007` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 9 | `W015` | (-146.5, 24.0) -> (-146.5, 180.0) | [564.0, 750.0] | [579.0, 735.0] | 156 | 13 | W052@572[565.0, 579.0] / W055@742[735.0, 749.0] | 0 | n/a (vao de altura plena) | FACE_DE_PERPENDICULAR `W006` +0.001 | FACE_DE_PERPENDICULAR `W007` +0.001 | DUAS_PAREDES_SEPARADAS (R3) | ALTA |
| 10 | `W052` | (-139.5, 17.0) -> (96.5, 17.0) | [924.0, 1190.0] | [939.0, 1175.0] | 236 | 8 | W015@932[925.0, 939.0] / W016@1182[1175.01, 1189.01] | 0 | NAO (7 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W019` -0.003 | FIM_DE_PAREDE_COLINEAR `W005` +0.000 | DUAS_PAREDES_SEPARADAS (R1) | MEDIA-ALTA |
| 11 | `W017` | (338.5, 24.0) -> (338.5, 180.0) | [564.0, 750.0] | [579.0, 735.0] | 156 | 13 | W052@572[565.0, 579.0] / W056@742[735.0, 749.0] | 0 | NAO (1 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W005` +0.001 | FACE_DE_PERPENDICULAR `W008` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 12 | `W047` | (528.5, 24.0) -> (528.5, 180.0) | [94.0, 280.0] | [109.0, 265.0] | 156 | 13 | W052@102[95.0, 109.0] / W056@272[265.0, 279.0] | 0 | n/a (vao de altura plena) | FACE_DE_PERPENDICULAR `W005` +0.001 | FACE_DE_PERPENDICULAR `W008` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 13 | `W006` | (593.5, -246.0) -> (593.5, -145.0) | [309.01, 440.0] | [324.0, 425.0] | 101 | 8 | W035@317[310.0, 324.0] / W045@432[425.0, 439.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | FIM_DE_PAREDE_COLINEAR `W043` +0.259 | FACE_DE_PERPENDICULAR `W053` -0.199 | DUAS_PAREDES_SEPARADAS (R2) | MEDIA-ALTA |
| 14 | `W006` | (593.5, 24.0) -> (593.5, 180.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 7 | W052@587[580.0, 594.0] / W056@757[750.0, 764.0] | 0 | NAO (10 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W005` +0.001 | FACE_DE_PERPENDICULAR `W008` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 15 | `W006` | (593.5, 349.0) -> (593.5, 450.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 8 | W067@912[905.0, 919.0] / W076@1027[1020.0, 1034.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W050` +0.001 | FIM_DE_PAREDE_COLINEAR `W040` -0.257 | DUAS_PAREDES_SEPARADAS | ALTA |
| 16 | `W007` | (848.5, -246.0) -> (848.5, -145.0) | [309.0, 440.0] | [324.0, 425.0] | 101 | 12 | W035@317[310.0, 324.0] / W045@432[425.0, 439.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | FIM_DE_PAREDE_COLINEAR `W045` +0.259 | FACE_DE_PERPENDICULAR `W053` -0.199 | DUAS_PAREDES_SEPARADAS (R2) | MEDIA-ALTA |
| 17 | `W007` | (848.5, 24.0) -> (848.5, 180.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 14 | W052@587[580.0, 594.0] / W056@757[750.0, 764.0] | 0 | n/a (vao de altura plena) | FACE_DE_PERPENDICULAR `W005` +0.001 | FACE_DE_PERPENDICULAR `W008` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |
| 18 | `W007` | (848.5, 349.0) -> (848.5, 450.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 12 | W067@912[905.0, 919.0] / W076@1027[1020.0, 1034.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W050` +0.001 | FIM_DE_PAREDE_COLINEAR `W046` -0.257 | DUAS_PAREDES_SEPARADAS | ALTA |
| 19 | `W008` | (1263.5, 24.0) -> (1263.5, 180.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 13 | W052@587[580.0, 594.0] / W056@757[750.0, 764.0] | 0 | NAO (1 fiada(s) acima, cobertura 0%) | FACE_DE_PERPENDICULAR `W005` +0.001 | FACE_DE_PERPENDICULAR `W008` +0.001 | DUAS_PAREDES_SEPARADAS | ALTA |

### torre_easy_lo_r00_tp1

| # | id ref | identidade fisica (jamba lo XY -> hi XY, cm) | envelope | consenso | larg | fiadas | perp. lo / hi (reserva de no') | blocos no vao | verga | jamba lo medida | jamba hi medida | classificacao | conf. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `W003` | (6607.2, 1127.0) -> (6607.2, 1283.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 13 | W052@587[580.0, 594.0] / W055@757[750.0, 764.0] | 0 | NAO (1 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 2 | `W004` | (7022.2, 857.0) -> (7022.2, 958.0) | [309.0, 440.0] | [324.0, 425.0] | 101 | 12 | W034@317[310.0, 324.0] / W044@432[425.0, 439.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 3 | `W004` | (7022.2, 1127.0) -> (7022.2, 1283.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 14 | W052@587[580.0, 594.0] / W055@757[750.0, 764.0] | 0 | n/a (vao de altura plena) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 4 | `W004` | (7022.2, 1452.0) -> (7022.2, 1553.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 12 | W065@912[905.0, 919.0] / W074@1027[1020.0, 1034.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 5 | `W005` | (7277.2, 857.0) -> (7277.2, 958.0) | [309.01, 440.0] | [324.0, 425.0] | 101 | 8 | W034@317[310.0, 324.0] / W044@432[425.0, 439.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 6 | `W005` | (7277.2, 1127.0) -> (7277.2, 1283.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 7 | W052@587[580.0, 594.0] / W055@757[750.0, 764.0] | 0 | NAO (10 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 7 | `W005` | (7277.2, 1452.0) -> (7277.2, 1553.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 8 | W065@912[905.0, 919.0] / W074@1027[1020.0, 1034.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 8 | `W046` | (7342.2, 1127.0) -> (7342.2, 1283.0) | [94.0, 280.0] | [109.0, 265.0] | 156 | 13 | W052@102[95.0, 109.0] / W055@272[265.0, 279.0] | 0 | n/a (vao de altura plena) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 9 | `W017` | (7532.2, 1127.0) -> (7532.2, 1283.0) | [564.0, 750.0] | [579.0, 735.0] | 156 | 13 | W052@572[565.0, 579.0] / W055@742[735.0, 749.0] | 0 | n/a (vao de altura plena) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS (R3) | MEDIA-ALTA |
| 10 | `W052` | (7539.2, 1120.0) -> (7775.2, 1120.0) | [924.0, 1190.0] | [939.0, 1175.0] | 236 | 8 | W017@932[925.0, 939.0] / W018@1182[1175.01, 1189.01] | 0 | NAO (7 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS (R1) | MEDIA |
| 11 | `W019` | (8017.3, 1127.0) -> (8017.3, 1283.0) | [564.0, 750.0] | [579.0, 735.0] | 156 | 13 | W052@572[565.0, 579.0] / W056@742[735.0, 749.0] | 0 | NAO (1 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 12 | `W047` | (8207.2, 1127.0) -> (8207.2, 1283.0) | [94.0, 280.0] | [109.0, 265.0] | 156 | 13 | W052@102[95.0, 109.0] / W056@272[265.0, 279.0] | 0 | n/a (vao de altura plena) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 13 | `W006` | (8272.2, 857.0) -> (8272.2, 958.0) | [309.01, 440.0] | [324.0, 425.0] | 101 | 8 | W035@317[310.0, 324.0] / W045@432[425.0, 439.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS (R2) | MEDIA |
| 14 | `W006` | (8272.2, 1127.0) -> (8272.2, 1283.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 7 | W052@587[580.0, 594.0] / W056@757[750.0, 764.0] | 0 | NAO (10 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 15 | `W006` | (8272.2, 1452.0) -> (8272.2, 1553.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 8 | W066@912[905.0, 919.0] / W075@1027[1020.0, 1034.0] | 0 | NAO (9 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 16 | `W007` | (8527.2, 857.0) -> (8527.2, 958.0) | [309.0, 440.0] | [324.0, 425.0] | 101 | 12 | W035@317[310.0, 324.0] / W045@432[425.0, 439.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS (R2) | MEDIA |
| 17 | `W007` | (8527.2, 1127.0) -> (8527.2, 1283.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 14 | W052@587[580.0, 594.0] / W056@757[750.0, 764.0] | 0 | n/a (vao de altura plena) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 18 | `W007` | (8527.2, 1452.0) -> (8527.2, 1553.0) | [904.0, 1035.0] | [919.0, 1020.0] | 101 | 12 | W066@912[905.0, 919.0] / W075@1027[1020.0, 1034.0] | 0 | NAO (2 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |
| 19 | `W008` | (8942.2, 1127.0) -> (8942.2, 1283.0) | [579.0, 765.0] | [594.0, 750.0] | 156 | 13 | W052@587[580.0, 594.0] / W056@757[750.0, 764.0] | 0 | NAO (1 fiada(s) acima, cobertura 0%) | sem fonte medida | sem fonte medida | DUAS_PAREDES_SEPARADAS | MEDIA-ALTA |

### Legenda das ressalvas

| ressalva | o que é | onde |
|---|---|---|
| **R1** | parede medida colinear **ultrapassa a jamba humana em 30,01cm** e termina livre (sem perpendicular no fim). A jamba em si está confirmada pela face da perpendicular medida (`W019`, resíduo −0,003cm), mas medido e humano discordam em 30cm sobre onde a parede acaba | `W052` (os dois projetos) |
| **R2** | no nó existe, no CAD medido, um **par de paredes paralelas** (`W053` em `y=−152,151` e `W100` em `y=−138,200`, 13,95cm entre elas). O humano modelou **uma só** (`W045` em `y=−137,952`), com a linha de `W100` e o comprimento de `W053`. A jamba casa com a face de `W053` a −0,199cm, mas pela face OPOSTA à esperada | `W006` e `W007` em `[324,425]` |
| **R3** | a jamba está confirmada, mas o trecho do hospedeiro **depois** do vão (193cm adiante) **não tem parede medida colinear correspondente** — lacuna de extração, não do vão | `W015` (TGD) / `W017` (TP1) |

### Classificação — resumo

| classificação | TGD | TP1 |
|---|---|---|
| `ABERTURA_REAL_MEDIDA` | 0 | 0 |
| `ABERTURA_REAL_RECONSTRUIDA` | 0 | 0 |
| **`DUAS_PAREDES_SEPARADAS`** | **19** | **19** |
| `RESERVA_DE_NO` / `PASSAGEM_ESTRUTURAL` | 0 | 0 |
| `INCONCLUSIVO` | 0 | 0 |

**Nota sobre a categoria `RESERVA_DE_NO`.** Ela descreve corretamente as
**tiras de 15,0cm** de cada jamba — que são a pegada da parede
perpendicular — mas **não** o vão de 101/156/236cm entre elas. Nesta
reconciliação as duas coisas estão separadas: as tiras são reserva de nó
(fato medido, coluna "reserva de nó" das tabelas) e o miolo é o espaço
entre duas paredes. A classificação da tabela é do **miolo**.

Nenhum caso ficou `INCONCLUSIVO` quanto à **natureza** do vão. As
incertezas remanescentes (R1, R2, R3) são sobre **valores de borda e
identidade de parede vizinha**, não sobre "é porta ou não é" — estão em §7.

---

## 4. Pareamento físico entre projetos — demonstrado, não presumido

O enunciado (§5) proíbe copiar a classificação do TGD para o TP1 por
analogia. O pareamento aqui **não é analogia**: é correspondência de
coordenada.

**Fato 1 — mesmo edifício, mesmo arquivo, níveis adjacentes.** Os dois
`metadata.json` declaram o mesmo documento Revit
(`TORRE EASY-LO-R00_desanexado_joaoC9CL7.rvt`): TGD é o nível `04. TGD`,
TP1 é o nível `05. TP1`.

**Fato 2 — a translação está documentada no próprio repositório.** O
`metadata.json` do TGD registra
`transform_input_to_reference.translation_cm = [7678,7371, 1102,9024, 341,0]`,
com resíduo máximo de `0,000141cm` sobre 49.127 segmentos de CAD.

**Fato 3 — medido nesta sessão.** Aplicando essa translação às 38 jambas:

```
pares físicos demonstrados: 19/19     resíduo máximo: 0,100 cm
envelope e consenso idênticos nos 19 pares: SIM (byte a byte)
```

Remapeamento de id que o pareamento revela — e que confirma o alerta de
§1.4: **TGD `W015` ↔ TP1 `W017`**, **TGD `W017` ↔ TP1 `W019`**; os outros
17 mantêm o id.

### 4.1 O que o pareamento transfere — e o que NÃO transfere

| transfere? | o quê |
|---|---|
| **SIM** | a posição física dos 19 vãos (resíduo ≤ 0,10cm) |
| **SIM** | a modulação humana: os 19 do TP1 têm envelope, consenso, largura, nº de fiadas, paredes perpendiculares e contagem de peças nas tiras **idênticos** aos do TGD |
| **NÃO** | a proveniência medida. O `input.json` do TP1 é derivado do próprio gabarito (§1.3). **Nenhuma das 19 classificações do TP1 se apoia em medição do Revit.** |

**O que sustenta o TP1 sem analogia:** os critérios `C1` (reserva de nó nas
duas jambas) e `C2` (sem verga) são calculados **sobre o próprio
`reference.json` do TP1** e dão 19/19 lá também — não são importados do
TGD. Só o critério `C3` (ausência de abertura medida) é indisponível no
TP1. Por isso a confiança do TP1 é **MÉDIA-ALTA**, não ALTA: falta a
confirmação independente do Revit, e ela **não pode ser suprida por
analogia**.

**Contraprova de que os dois níveis não são intercambiáveis** — o
`metadata.json` do TGD documenta que eles **diferem**: "as duas aberturas
que diferenciam TGD de TP1 (uma porta de 121cm em x=7654 e uma abertura de
91cm em x=9400) estão no INPUT exatamente como em TGD. O nível TP1 tem no
lugar uma janela de 71cm com peitoril 160". Os histogramas de largura
confirmam (TGD tem `121.0:1`, `81.0:2`; TP1 não tem). **Os 19 casos não
estão entre essas diferenças** — mas o fato de haver diferenças reais é
exatamente por que o pareamento precisou ser demonstrado caso a caso.

---

## 5. Aberturas reais × paredes separadas

### 5.1 Um limiar de largura NÃO resolve — medido

`split_threshold_probe.py`. O vão que `split_axis_into_walls` de fato
enxerga (união de todas as fiadas — por isso janela, que tem peitoril e
verga, nunca chega ao limiar) nos 19:

```
larguras dos 19:   101,0 cm (x8)   156,0 cm (x10)   236,0 cm (x1)
```

Contra as **82 aberturas medidas do Revit** (TGD), que vão de `1,8` a
`321,0` cm:

- **8 dos 19 têm exatamente `101,0`cm — que é largura de porta MEDIDA real
  no projeto.**
- Um limiar de `101`cm em `WALL_SPLIT_GAP_CM` quebraria também **25 das 82
  aberturas medidas**.
- Os demais 75 trechos têm vãos de união de `0` a `231`cm — faixa que
  **contém inteiramente** a dos 19.

> **Conclusão de §6 do enunciado: nenhum valor de `WALL_SPLIT_GAP_CM`
> separa os 19 sem destruir porta medida real.** A decisão não pode ser uma
> constante. **As constantes não foram alteradas nesta CR.**

### 5.2 O que resolve: um critério ESTRUTURAL, sem largura

`criterion_selectivity.py`, sobre os 94 (TGD) e 92 (TP1) trechos:

| critério | nos 19 | nos demais (TGD 75 / TP1 73) |
|---|---|---|
| **C1** — as duas jambas do consenso coincidem (≤1,0cm) com a face interna de uma parede perpendicular que cruza o eixo | **19/19** | **0/75** e **0/73** |
| **C2** — sem verga (nenhuma fiada acima cobre ≥50% do consenso) | 19/19 | 3/75 e 2/73 |
| **C3** — sem abertura `measured` casada | 19/19 | 13/75 e 73/73 |
| **C1 ∧ C2 ∧ C3** | **19/19** | **0 falsos positivos nos dois projetos** |

**C1 sozinho já é classificador perfeito no corpus: 19/19 acertos, 0 falsos
positivos em 148 trechos de controle**, sem nenhum limiar de largura.

**Honestidade sobre C1.** C1 não é estatisticamente independente da
assinatura de 15cm: os dois nascem do mesmo mecanismo físico (a alternância
da peça de amarração no nó). O que C1 acrescenta é **linguagem**: ele fala
de face de parede perpendicular, não de tolerância de 15cm — e é
verificável contra a geometria medida (§2.2, 19/19). Não é prova de que não
exista contraexemplo fora deste corpus; é medição neste corpus.

### 5.3 Modelo atual × modelo proposto

| | MODELO ATUAL — uma parede com abertura | MODELO PROPOSTO — duas paredes separadas |
|---|---|---|
| representa a geometria original? | **não** — declara vão de 101/156/236cm onde o CAD medido tem duas paredes que terminam ali (38/38 jambas confirmadas) | **sim** |
| representa a modulação humana? | **não** — declara "abertura" onde o humano não pôs verga em nenhuma das 19, e onde 0 blocos ocupam o miolo | **sim** |
| tem procedência medida? | **não** — 0 dos 19 casam com as 82 aberturas medidas; `confidence="reconstructed"`, `source_element_id = null`, parede com `source_element_ids = []` nos 19 dos dois projetos | n/a |
| custo | as métricas de abertura ficam inutilizáveis em valor absoluto (o gabarito viola `OPENING_BLOCK_CROSSES_JAMB` 208/209 vezes) | muda identidade de parede, `evaluation_scope`, pareamento humano e toda métrica por parede |

---

## 6. Projeções e impactos

### 6.1 Pré-requisito técnico verificado: o gabarito é regenerável offline

O dump bruto do Revit **não está versionado** (`revit_dump.py` roda dentro
do Revit via MCP). Isso poderia obrigar a CR-B a reabrir o Revit. Não
obriga — `roundtrip_probe.py` mede:

```
dump sintético reconstruído a partir do próprio reference.json -> build_project()

                      TGD          TP1
paredes           97 -> 97      96 -> 96      (só em A: 0, só em B: 0)
aberturas         94 -> 94      92 -> 92
geometria/contagem de blocos divergente:  0            0
```

As **únicas** diferenças são as 23 paredes por projeto cujas aberturas
mudaram de envelope para consenso — isto é, **exatamente a correção da
CR-A**, porque o round-trip roda contra a `main` de hoje. **A extração é
determinística e reprodutível a partir do gabarito.** A CR-B pode projetar
e regerar offline, sem nova sessão de Revit.

### 6.2 Projeção estrutural do candidato "duas paredes separadas"

`projection_split.py` — candidato gerado em memória/temporário, usando o
código de produção em tudo, com uma única injeção cirúrgica (pontos de
corte vindos de C1). **Nenhuma constante alterada, nenhum arquivo oficial
tocado.**

| | TGD atual | TGD candidato | Δ | TP1 atual | TP1 candidato | Δ |
|---|---|---|---|---|---|---|
| paredes | 97 | 116 | **+19** | 96 | 115 | **+19** |
| aberturas | 94 | 75 | **−19** | 92 | 73 | **−19** |
| **blocos em paredes** | 12508 | **12508** | **0** | 12703 | **12703** | **0** |
| **blocos órfãos** | 0 | **0** | **0** | 0 | **0** | **0** |
| comprimento total (cm) | 45362,8 | 42758,8 | **−2604,0** | 45059,0 | 42455,0 | **−2604,0** |
| junções `T` | 216 | 196 | **−20** | 210 | 190 | **−20** |
| junções `L` | 78 | 126 | **+48** | 76 | 124 | **+48** |
| junções `FREE_END` | 8 | 8 | 0 | 11 | 11 | 0 |

Leitura, item a item:

- **Nenhum bloco humano é perdido nem vira órfão.** O corte só re-rotula
  peças entre duas paredes; a modulação humana fica intacta. É a garantia
  de segurança mais importante da projeção.
- **−2604,0cm é exatamente a soma dos 19 vãos**
  (`8×101 + 10×156 + 1×236 = 2604`). Nenhuma geometria inventada, nenhuma
  perdida.
- **`T` → `L` (−20 / +48) é consequência de domínio, não contabilidade.**
  Um nó que era "perpendicular atravessando parede contínua" (T) passa a
  ser "perpendicular encontrando o FIM da parede" (L). **Isso muda a regra
  de amarração aplicável** (B54/B34, alternância entre fiadas) e é o item
  de maior risco da CR-B. `FREE_END` não muda: as novas pontas não ficam
  livres, encostam na perpendicular.

### 6.3 O que NÃO foi medido — declarado

- **Não há projeção do SOLVER para o candidato "duas paredes separadas".**
  Ela exigiria regerar `input.json`, `evaluation_scope` e
  `reference_score.json`, e é trabalho da CR-B. **Não estimar o resultado
  por dedução a partir da projeção da opção A.**
- A projeção da opção A ("abertura estreita") **já existe e não foi
  refeita** (`projection_torre_easy_lo_r00_tp1.json`, CR-A): `CROSS_JAMB
  168 → 0`, críticos `485 → 327`, mas cobertura `+90` / `+14`.
- **Nenhum número de score foi usado para classificar caso algum.** §8 do
  enunciado é explícito e foi respeitado: a classificação vem de (A), (B) e
  (C); (D) não entrou.

### 6.4 Impacto de identidade — o que a CR-B terá de migrar

| item | impacto medido / previsto |
|---|---|
| identidade das paredes | 11 paredes hospedeiras por projeto viram 30 → `W0xx` **muda para quase todas** as paredes depois delas, porque o id é sequencial. Toda métrica histórica por `W0xx` deixa de ser comparável |
| `evaluation_scope` | `axis_segments_cm` vai de 97 para 116 entradas. As `cells` (8613 no TGD) são derivadas da ocupação física dos blocos, que **não muda** — a expectativa é escopo físico idêntico, **a verificar na CR-B, não assumido** |
| pareamento humano | `matched_inside_scope = 84`, `reference_only = 13`, `solver_only = 68` (TGD) precisam ser recalculados |
| aberturas | −19 por projeto; as 75/73 restantes ficam com a geometria de consenso já em vigor pela CR-A |
| nós T/L/X | **−20 `T`, +48 `L`** por projeto (§6.2) — exige revalidação das regras de amarração nesses nós |
| amarração | as tiras de 15cm deixam de ser "parede a preencher" e passam a ser pegada da perpendicular. Some a origem do `+90/+14` de cobertura da opção A |
| cobertura | esperada melhora relativa à opção A pelo motivo acima — **não medido, não reivindicar** |
| métricas históricas | `baseline.json` e `reference_score.json` deixam de ser comparáveis **em valor absoluto** |

---

## 7. Erros de reconstrução × possíveis erros humanos

Separando fato, inferência e decisão, como pede §7 — **sem criar tolerância
global** e sem estender a aceitação de 0,06cm da CR-A, que continua restrita
aos 4 casos daquela CR (TGD `W082`; TP1 `W029`/`W040`/`W072`).

### 7.1 ERRO DE RECONSTRUÇÃO — comprovado

| # | fato medido | inferência | classificação |
|---|---|---|---|
| 1 | `split_axis_into_walls` só quebra o eixo onde o vazio da **união das fiadas** passa de `WALL_SPLIT_GAP_CM = OPENING_GAP_MAX_CM = 260`. Os 19 vãos medem 101/156/236 | os 19 caem abaixo do limiar e viram "uma parede com abertura" | **ERRO DE RECONSTRUÇÃO** — origem estrutural dos 19 |
| 2 | a `key`/`id` de parede é sequencial e derivada do agrupamento de eixo; 0 de 97 ids do reference batem com o input | qualquer regeração do gabarito renumera paredes | **FRAGILIDADE DE IDENTIDADE** — não é erro, é dívida de esquema |
| 3 | o teste de eixo da CR-A usa colinearidade de ±3cm e só procura buraco entre colineares | subcontou 10/19 onde o correto é 19/19 | **ERRO DE MÉTODO DIAGNÓSTICO** (não de produção) — corrigido aqui |

### 7.2 DIVERGÊNCIA MEDIDO × HUMANO — fato, sem veredito

| # | fato medido | leitura possível | o que falta |
|---|---|---|---|
| **R1** `W052` | parede medida `W006` termina em `t = 969,01`; a jamba humana está em `939,0`. **Sobra de 30,01cm** de parede medida dentro do que o humano deixou vazio. O fim de `W006` é livre — não há perpendicular medida a menos de 37cm | (a) o humano suprimiu uma boneca de 30cm que existe no CAD; (b) o pareamento de eixos do input prolongou a parede. `W052` é também o caso cujo envelope antigo (266cm) **ultrapassava** o próprio `OPENING_GAP_MAX_CM = 260` | **conferência no Revit** |
| **R2** `W006`/`W007` em `[324,425]` | no CAD medido há **duas** paredes paralelas no nó: `W053` (`y = −152,151`) e `W100` (`y = −138,200`), 13,95cm entre si. O humano modelou **uma** (`W045`, `y = −137,952`), com a linha de `W100` e o comprimento de `W053` | (a) parede dupla/shaft no CAD que o humano simplificou; (b) duplicidade do pareamento de eixos. A jamba fica confirmada de qualquer forma (−0,199cm contra a face de `W053`) | **conferência no Revit** |
| **R3** `W015`(TGD)/`W017`(TP1) | depois do vão, **193cm** do eixo do hospedeiro não têm parede medida colinear; o humano construiu blocos ali | lacuna de extração do input (o input do TGD vem de outro documento, com 167 paredes contra 97 do gabarito) | não afeta a classificação do vão; **anotar** |
| 4 | paredes medidas curtas (94cm) a **−13 / +15cm** do eixo reconstruído em `W004`/`W007` | o CAD tem trechos escalonados ou o pareamento produziu eixos deslocados de meia espessura | não afeta a jamba (o **fim** em `t` casa exatamente); **anotar** |
| 5 | jambas com resíduo de **0,257–0,259cm** (`W044`, `W041`, `W040`, `W046`, `W047`, `W042`, `W043`, `W045`) | imprecisão de desenho/extração de mesma ordem da família de 0,11–0,12cm que a CR-A deixou aberta | **não criar tolerância**; registrar |

**Nenhuma dessas cinco muda a classificação de nenhum dos 19.** Em todas, o
miolo do vão permanece: 0 blocos, sem verga, sem procedência medida, com
reserva de nó nas duas jambas.

### 7.3 O que NÃO é erro humano

O projeto humano está **coerente consigo mesmo** nos 19 casos: nenhuma
peça no miolo, nenhuma verga, amarração alternando corretamente no nó, e
o mesmo padrão repetido 19 vezes em dois níveis. **Não há aqui
inconsistência humana a copiar nem a corrigir** — o que existe é uma
reconstrução que leu esse padrão como porta.

---

## 8. Casos inconclusivos

**Quanto à natureza do vão: nenhum.** Os 19, nos dois projetos, têm os
quatro sinais alinhados (0 blocos no miolo, reserva de nó nas duas jambas,
sem verga, sem procedência medida) e, no TGD, 38/38 jambas confirmadas por
geometria medida.

**Quanto a valores de borda e vizinhança, três** — R1, R2, R3 de §7.2.
Nenhuma delas bloqueia a decisão de domínio; todas devem ser conferidas no
Revit **antes de gravar** o gabarito novo, porque afetam **onde** a parede
nova termina, não **se** ela termina.

**Incerteza estrutural do TP1, preservada:** os 19 do TP1 não têm fonte
medida independente (§4.1). Sua confiança é MÉDIA-ALTA e a evidência que
falta é nomeada: extração de aberturas nativas / eixos medidos do nível
`05. TP1`, equivalente ao que o TGD tem.

---

## 9. Decisões necessárias do usuário

Nenhuma foi tomada nesta CR.

| # | decisão | o que a evidência diz | risco de errar |
|---|---|---|---|
| **D1** | Os 19 do **TGD** passam a ser **duas paredes separadas** (opção B), em vez de abertura estreita (opção A)? | evidência **converge para B**: 0 blocos no miolo, 0 vergas, 0 procedência medida, 38/38 jambas confirmadas por Revit, e nenhum limiar de largura consegue separar (§5.1) | baixo para B; manter A mantém as métricas de abertura inutilizáveis em valor absoluto |
| **D2** | Os 19 do **TP1** acompanham? | pareamento físico provado (19/19, ≤0,10cm) e C1/C2 calculados no próprio TP1 dão 19/19 — **mas sem fonte medida independente** | médio: se aceito, é decisão de domínio por evidência (B)+(C), **não** medição. Alternativa: extrair o nível `05. TP1` no Revit antes |
| **D3** | Autoriza alterar o gabarito, aceitando que **`baseline.json` e `reference_score.json` deixam de ser comparáveis em valor absoluto** e que os ids `W0xx` migram? | consequência inevitável de B (§6.4) | alto se não for explícito agora |
| **D4** | R1 (`W052`, sobra medida de 30,01cm), R2 (`W006`/`W007`, par de paredes paralelas no CAD) e R3 (`W015`/`W017`, 193cm sem parede medida) — **conferir no Revit antes de gravar**, ou gravar com o valor humano e registrar a pendência? | são fatos medidos sem veredito; afetam onde a parede nova termina | médio |
| **D5** | O critério de separação vira **regra de domínio** (C1: reserva de nó nas duas jambas + sem verga) em `nuvem/REGRAS_MODULACAO_BLOCOS.md`, ou fica só como heurística de extração desta CR? | C1 acerta 19/19 com 0 falsos positivos em 148 controles — **neste corpus**; não há prova fora dele | alto: promover a regra geral com dois projetos do mesmo edifício é extrapolação |
| **D6** | Recuperar/regerar `docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` e `docs/C04_INDEPENDENT_FINAL_REVIEW.md`, ou corrigir as citações do `PROJECT_STATUS.md`? | os dois são citados como autoridade e não existem (§1.2) | baixo, mas é dívida documental real |

**Preferência de domínio já confirmada pelo usuário** (encontros X:
priorizar B54 e alternância entre fiadas) foi respeitada e **não foi
alterada**. Esta CR **não** transforma os quatro exemplos de passagem do
C02 em regra de parede curta e **não** inicia o C02.

---

## 10. Plano de implementação da CR-B — proposta, NÃO implementada

### 10.1 Escopo

Só se D1–D3 forem autorizadas explicitamente.

**Toca:** `nuvem/benchmark/extract/reconstruct.py`,
`nuvem/benchmark/projects/{tgd,tp1}/reference.json`, `*/input.json`,
`*/reference_score.json`, `*/evaluation_scope.json` + `scope_summary.json`,
`nuvem/REGRAS_MODULACAO_BLOCOS.md` (registro obrigatório do `CLAUDE.md`).

**Não toca:** `baseline.json` (fica para `BENCH-BASELINE-REFRESH`, com
decisão própria), `nuvem/core/engine/**` (o solver), nenhuma constante de
`opening_audit.py`.

### 10.2 Casos por situação

| situação | n (por projeto) | ação |
|---|---|---|
| corrigíveis com evidência suficiente | **19 no TGD** / **19 no TP1 se D2** | dividir em duas paredes; remover a abertura |
| pendentes de conferência no Revit | **3** (R1, R2, R3) | gravar o valor humano e marcar `needs_revit_check`, ou segurar até a conferência (D4) |
| inconclusivos quanto à natureza | **0** | — |

### 10.3 Mudança no extrator

Introduzir a separação **estrutural**, não por limiar:

1. `reconstruct.py` passa a fazer **duas passadas**: (i) constrói eixos e
   paredes como hoje; (ii) para cada abertura reconstruída, avalia C1
   (as duas jambas coincidem com a face interna de uma perpendicular) e C2
   (sem verga) e, quando as duas valem, **corta a parede** e descarta a
   abertura.
2. `WALL_SPLIT_GAP_CM` e `OPENING_GAP_MAX_CM` **permanecem 260,0** —
   medido em §5.1 que mexer nelas destrói porta medida real.
3. Abertura com `source_element_id` **nunca** entra nesse caminho.
4. A tolerância de face (1,0cm) é de **classificação**, não de geometria:
   nenhuma coordenada gravada vem dela.

### 10.4 Esquema e proveniência

- `schema_version` de `reference.json`: `2 → 3`.
- Gravar por abertura o que o detector já produz desde a CR-A e o gabarito
  ainda descarta: `opening_provenance`, `jamb_spread_cm`,
  `x_range_envelope`.
- Campo novo por parede: `split_reason` (`NODE_RESERVE_BOTH_JAMBS`) e
  `provenance` do corte.
- Campo novo por parede: `stable_key` — chave **de coordenada de mundo**,
  imune à renumeração (§7.1, item 2). É o que permite comparar métricas
  entre gabaritos.
- `changelog` por abertura removida e por parede criada.

### 10.5 Preservação do gabarito anterior

- `reference_v2.json` / `input_v2.json` mantidos **lado a lado** por pelo
  menos uma CR, com `README` explicando qual é qual.
- `reference_score.json` recalibrado **na mesma CR** (senão o corpus fica
  incoerente).
- `baseline.json` **não** regravado.

### 10.6 Migração de identidade

1. Gerar a tabela `stable_key` → `W0xx_v2` → `W0xx_v3` para as 97/96
   paredes e as 116/115 novas.
2. Reexpressar `evaluation_scope.json` por `stable_key`.
3. Publicar um conversor para as métricas históricas — não para torná-las
   comparáveis em valor absoluto (não ficam), mas para rastrear **qual
   parede virou qual**.

### 10.7 Testes e hard gates

| gate | como |
|---|---|
| **nenhum bloco humano perdido** | contagem de blocos em paredes + órfãos **idêntica** antes/depois (já medido: 12508/12703, órfãos 0) |
| **comprimento conservado** | `Δ comprimento total == −Σ(larguras dos vãos removidos)` (já medido: −2604,0 exato) |
| **nenhuma abertura medida tocada** | as 82 `measured` do TGD **byte-idênticas** |
| **round-trip determinístico** | `roundtrip_probe.py` em 2 processos novos, saída idêntica |
| `OPENING_BLOCK_CROSSES_JAMB` | contra o **próprio gabarito novo** deve ir de 208/209 para **0** — é o teste de que o gabarito parou de se contradizer |
| `COVERAGE_*`, `PRISM_*`, `JUNCTION_*`, `COMPENSATOR_*` | delta por **identidade geométrica estável**, nunca por contagem, nunca por `W0xx` |
| amarração nos nós `T`→`L` | revalidar as 48 junções `L` novas contra as regras de L/T/X — **é o maior risco da CR-B** |
| suíte completa | `python3 -m pytest -q`; as 2 falhas pré-existentes (C1 do TGD, `JUNCTION_MISSING_BINDING` do TP1) devem continuar sendo **as mesmas 2**, sem novas |

**Proibido**: regravar `baseline.json` para esconder regressão; criar
tolerância global; `skip`/`xfail`; usar redução de críticos como
justificativa de classificação.

### 10.8 Critérios de rollback

Reverter se qualquer um ocorrer:
- algum bloco humano vira órfão ou some;
- alguma abertura `measured` muda de geometria;
- `OPENING_BLOCK_CROSSES_JAMB` contra o gabarito novo **não** zera;
- aparece regressão de amarração nas 48 junções `L` novas;
- round-trip deixa de ser determinístico.

### 10.9 Registro de regra (obrigatório pelo `CLAUDE.md`)

Esta CR **não** alterou `nuvem/REGRAS_MODULACAO_BLOCOS.md` — o enunciado
proíbe alterar regra normativa, e a orientação mais recente do usuário tem
prioridade. Fica a pendência **declarada**, para a CR-B (perto de 10.6 /
10.9):

> **PENDENTE DE REGISTRO — DOCUMENTADO, pendência de código aberta.**
> Um vazio de altura plena cujas **duas** jambas coincidem com a face
> interna de uma parede perpendicular (reserva de nó nos dois lados) e que
> **não tem verga** não é abertura: é o espaço entre **duas paredes que
> terminam no nó**. As tiras de ~15cm de cada lado são a pegada da
> perpendicular, não vão a preencher.
> Rótulo sugerido: **PADRÃO MEDIDO — 19 casos por projeto em 2 níveis do
> mesmo edifício; 0 falsos positivos em 148 trechos de controle**.
> Como foi descoberto: `void_occupancy.py`, `lintel_test.py`,
> `measured_jamb_confirmation.py` e `criterion_selectivity.py` sobre o
> gabarito humano congelado e sobre o `input.json` medido do TGD
> (38/38 jambas confirmadas, resíduo máximo 0,259cm).
> **Não promover a regra geral sem a decisão D5** — dois projetos do mesmo
> edifício não são amostra suficiente.

---

## 11. Próximo passo recomendado

1. **Decidir D1 e D2** (natureza dos 19 no TGD e no TP1). É o único
   bloqueio real: sem isso a CR-B não pode começar.
2. **Decidir D3** (autorização de alterar gabarito e aceitação da perda de
   comparabilidade absoluta das métricas históricas).
3. **Antes de gravar**, conferir no Revit os 3 casos de R1/R2/R3 (D4) —
   sessão MCP curta, três coordenadas nomeadas nas tabelas de §3.
4. Só então abrir a `CR-BENCH-OPENING-RECONSTRUCTION-B` com o plano de §10.

**Não recomendado agora:** implementar §10 sem D1–D3; alterar
`WALL_SPLIT_GAP_CM`/`OPENING_GAP_MAX_CM` (medido em §5.1 que não resolve e
destrói porta real); promover C1 a regra geral sem D5; iniciar
C02/C10/Junction/S1/S2.

---

## 12. Limitações declaradas

1. **Nenhuma medição no Revit ao vivo (MCP)** foi feita nesta sessão. Toda
   a fonte (A) vem do `input.json` do TGD já commitado.
2. **O TP1 não tem fonte medida independente.** Sua classificação apoia-se
   em (B) e (C) próprios mais o pareamento físico — **não** em analogia,
   mas também **não** em medição.
3. **Não há projeção do solver para a opção B** (§6.3). O ganho/custo de
   métrica dela é **desconhecido**, não estimado.
4. **C1 foi validado em 148 trechos de controle de dois níveis do mesmo
   edifício.** Não é prova universal.
5. **A revisão independente da CR-A não pôde ser lida** (§1.2).
6. A família de **0,11–0,12cm** de coordenada fracionária (causa: extração)
   continua **aberta**, e esta CR não a toca. A aceitação de 0,06cm da CR-A
   permanece restrita aos 4 casos daquela CR.
7. Os resíduos de **0,257–0,259cm** em 8 jambas (§7.2, item 5) estão
   registrados e **não** viraram tolerância.
8. `piloto_sintetico_2x2` não tem trecho detectável e ficou fora.
