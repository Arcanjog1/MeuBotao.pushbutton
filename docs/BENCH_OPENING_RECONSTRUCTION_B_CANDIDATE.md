# CR-B — CANDIDATO E VALIDAÇÃO ESTRUTURAL DO GABARITO

> **Etapa de CANDIDATO ISOLADO E VALIDAÇÃO. Nada foi integrado.**
>
> `nuvem/benchmark/projects/**` (`reference.json`, `input.json`,
> `baseline.json`, `reference_score.json`, `evaluation_scope.json`), o
> solver (`nuvem/core/**`) e `nuvem/REGRAS_MODULACAO_BLOCOS.md` estão
> **intocados** — conferido por `git diff --name-only` no fim da sessão.
> Nenhuma constante de produção foi alterada. Nenhuma regra normativa foi
> escrita. Nenhum PR de produção, nenhum merge.
> C02/C10/Junction/S1/S2 **não iniciadas**.

---

## Base / branch / HEAD

| item | valor |
|---|---|
| base obrigatória | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` |
| `origin/main` no início da sessão | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` (**confere**) |
| branch de trabalho | `claude/candidato-validacao-gabarito-q450yr` |
| fonte diagnóstica | `claude/reconciliacao-gabarito-aberturas-uynv0q` (`aa5dd1a9`) |
| versão do candidato | `cand-B-2026-09-07.1` |
| diff | só `docs/` + `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate/` |
| gabarito oficial | **intocado** |

---

## 0. Resumo executivo — o que esta CR provou e o que não provou

**Provado, medido nesta sessão:**

1. O candidato **preserva a geometria humana integralmente**: 0 blocos
   perdidos, 0 duplicados, 0 órfãos, 0 deslocados — cota `z`, centro `XY`
   e elevação da fiada **idênticos** para os 12.508 (TGD) / 12.703 (TP1)
   blocos. §4.
2. O corte remove **exatamente as 19 aberturas** do critério estrutural
   `C1` e **nenhuma outra**; **0** das removidas tem `source_element_id`;
   **0** aberturas ganham geometria nova ou alterada. §4.
3. O comprimento total cai **−2604,0 cm exatos** nos dois projetos — a
   soma aritmética dos 19 vãos. Nenhuma geometria inventada. §4.
4. **A mudança T→L não é artefato de fragmentação nem perda de
   amarração**: nos **38 nós por projeto** que mudam de tipo, o conjunto
   de peças humanas que ocupa a pegada do nó é **byte-idêntico** antes e
   depois. Nenhuma amarração humana foi removida, nenhuma B54 foi
   forçada, nenhuma parede curta foi criada (menor parede nova: 109 cm).
   §5.
5. O candidato é **determinístico**: 3 processos novos produzem os quatro
   arquivos com `sha256` idêntico. §8.
6. As três divergências (R1/R2/R3) foram remedidas de forma independente
   e **confirmadas**: 30,007 cm, 14,458 cm (≈ uma espessura de parede),
   192,998 cm. Nenhuma delas muda a classificação de nenhum dos 19. §6.
7. Os dois documentos de revisão independente citados pelo
   `PROJECT_STATUS.md` **nunca existiram em nenhuma ref** — verificado
   por `git log --all --diff-filter=A` sobre os 153 commits do repositório.
   §1.2.

**NÃO provado — declarado como limite:**

- Esta CR **não** demonstra que o critério `C1` seja regra de domínio
  válida fora deste corpus (dois níveis do mesmo edifício). Continua
  **heurística de extração validada neste corpus**. Decisão **D5** aberta.
- Esta CR **não** resolve R1/R2/R3. Elas são fatos medidos sem veredito e
  exigem conferência no Revit (§6.5) — decisão **D4** aberta.
- O candidato **não** foi gravado em nenhum arquivo oficial e **não** tem
  autorização para ser gravado (decisão **D3** aberta).

---

## 1. Base e documentação

### 1.1 O que foi lido

- `docs/BENCH_OPENING_RECONSTRUCTION_B_RECONCILIATION.md` **integral**
  (718 linhas), da branch diagnóstica — incluindo a §9 com D1–D6.
- `CLAUDE.md`, `docs/START_HERE.md`, `docs/PROJECT_STATUS.md` (integral),
  `docs/REFERENCE_CORPUS.md` (roteamento).
- Código de produção lido, **não alterado**:
  `nuvem/benchmark/extract/reconstruct.py`, `nuvem/benchmark/runner.py`,
  `nuvem/benchmark/scoring.py`, `nuvem/benchmark/validators/*`.
- `nuvem/benchmark/projects/*/metadata.json` (procedência das duas fontes).

O Atlas e os diagnósticos já concluídos **não foram repetidos**. Onde a
reconciliação já mediu (teste da verga, ocupação do vão, seletividade de
`C1`, sondagem de limiar), este documento **cita** e não remede — exceto
onde a remedição era o próprio objeto desta CR (invariantes por bloco,
T→L, R1/R2/R3, projeção do solver).

### 1.2 Dívida documental — CONFIRMADA de forma independente

A reconciliação registrou que dois documentos citados como autoridade não
existem. **Reverificado aqui**, e o resultado é mais forte do que
"ausente do working tree":

```
git log --all --oneline --diff-filter=A -- docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md
   -> vazio
git log --all --oneline --diff-filter=A -- docs/C04_INDEPENDENT_FINAL_REVIEW.md
   -> vazio
(153 commits varridos em TODAS as refs; nenhum arquivo com "independent"
 ou "review" no nome, exceto ai_team/prompts/codex_review.md)
```

| citado em | arquivo | estado |
|---|---|---|
| `PROJECT_STATUS.md` (CR-A) e `bench_opening_reconstruction_a/README.md` §6 | `docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` | **nunca commitado em nenhuma ref** |
| `PROJECT_STATUS.md` (C04 / C3) | `docs/C04_INDEPENDENT_FINAL_REVIEW.md` | **nunca commitado em nenhuma ref** |

Todos os demais documentos citados pelo `PROJECT_STATUS.md` existem.

**Consequência aplicada nesta CR:** nenhuma conclusão depende desses dois
documentos. Onde o `PROJECT_STATUS.md` resume as conclusões deles, o
resumo é tratado como **registro secundário**, nunca como fonte primária.
Nada foi inventado a respeito do conteúdo ausente. A resolução proposta
está em **D6** (§9).

### 1.3 As quatro fontes de verdade — e uma correção de escopo

| fonte | de onde vem | disponível em |
|---|---|---|
| **(A) GEOMETRIA MEDIDA** | `input.json` do TGD — 167 paredes, **82 aberturas `confidence="measured"` com `source_element_id`**, extraídas do documento Revit SEPARADO `TESTE MODULACAO (2026).rvt` | **só TGD** |
| **(B) MODULAÇÃO HUMANA** | `reference.json` — `rows`/`blocks` posicionados pela pessoa | TGD e TP1 |
| **(C) RECONSTRUÇÃO** | `reference.json` — `walls`/`openings`/`junctions`, saída de `reconstruct.py` sobre (B) | TGD e TP1 |
| **(D) RESULTADO DO SOLVER** | rodado nesta CR sobre cópias isoladas | §7 |

**Correção de escopo ao plano §10.1 da reconciliação — medida aqui.**
O plano de implementação proposto pela reconciliação lista
`*/input.json` (plural, os dois projetos) entre os arquivos que a CR-B
tocaria. Isso está **errado para o TGD** e a diferença é grande:

```
TGD  input.json  metadata.derived_from = "wall_modeling_snapshot.json"
                 167 paredes, 82 aberturas measured  -> NÃO deriva do gabarito
TP1  input.json  metadata.derived_from = "reference.json"
                  96 paredes,  0 aberturas measured  -> DERIVA do gabarito
```

Portanto: regravar o gabarito do **TGD não muda a entrada do solver**, só
o gabarito de comparação, o `evaluation_scope` e o piso de ruído. No
**TP1**, muda a entrada do solver. As duas situações têm naturezas
diferentes e são separadas em §7. Regenerar o `input.json` do TGD a
partir do gabarito **destruiria a única fonte medida independente do
corpus** e está **proibido** no plano de integração (§9.3).

---

## 2. Decisões de domínio adotadas para o candidato

Conforme §2 do enunciado, e **sem promover nada a regra normativa**:

| item | decisão adotada NESTE CANDIDATO | procedência | confiança |
|---|---|---|---|
| **TGD** — os 19 casos | tratados como **duas paredes separadas** | geometria medida (38/38 jambas confirmadas no `input.json` do TGD) + os quatro sinais convergentes da reconciliação | **ALTA** |
| **TP1** — os 19 casos | mesma classificação, como **reconstrução** | pareamento físico 19/19 + `C1`/`C2` calculados sobre o **próprio** `reference.json` do TP1 | **MÉDIA-ALTA** |

**O pareamento físico foi remedido nesta sessão**, não herdado:

```
translação documentada (metadata.json do TGD):  [7678,7371 , 1102,9024] cm
pares físicos:            19 / 19
resíduo máximo:           0,0004 cm
largura idêntica nos 19:  SIM
t_range idêntico nos 19:  SIM
remapeamento de id:       TGD W015 <-> TP1 W017 ; TGD W017 <-> TP1 W019
```

**O TP1 continua sem geometria medida independente.** Não é declarada
nenhuma. A confiança MÉDIA-ALTA vem de (B)+(C) próprios mais o
pareamento — **não** de analogia e **não** de medição. A evidência que
falta é nomeada: extração de eixos/aberturas nativas do nível `05. TP1`,
equivalente ao que o TGD tem.

**Estatuto do critério.** `C1` (as duas jambas coincidem com a face
interna de uma perpendicular) é **heurística de extração validada neste
corpus** — 19/19 acertos, 0 falsos positivos em 148 trechos de controle.
**Não** é regra normativa geral de modulação e **não** foi escrita em
`nuvem/REGRAS_MODULACAO_BLOCOS.md`.

**O que NÃO foi feito, por proibição explícita do enunciado:**
nenhum limiar de largura foi usado para separar porta de parede;
`WALL_SPLIT_GAP_CM` e `OPENING_GAP_MAX_CM` permanecem **260,0**.

---

## 3. Preservação do gabarito

O candidato vive **fora** de `nuvem/benchmark/projects/**`, num diretório
apontado por `$CR_B_OUT`. Nenhum dos quatro arquivos protegidos foi
tocado:

```
$ git status --porcelain
?? nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate/

$ git diff --name-only -- nuvem/benchmark/projects nuvem/core \
                          nuvem/REGRAS_MODULACAO_BLOCOS.md tests
(vazio)
```

`baseline.json`, `reference.json`, `reference_score.json`, `input.json`,
`evaluation_scope.json`: **intocados**. Regras normativas: **intocadas**.
Solver: **intocado**.

### 3.1 Os três estados — e por que o controle importa

| estado | o que é |
|---|---|
| **STATE_A** | `reference.json` oficial, como está em disco hoje |
| **STATE_R** | round-trip do gabarito **sem corte** — o **controle** |
| **STATE_C** | STATE_R **+ corte estrutural `C1`** nos 19 casos — o **candidato** |

**Todo delta reivindicado por esta CR é `STATE_C − STATE_R`.** Medir
`STATE_C − STATE_A` somaria dois efeitos independentes. Medido aqui:

```
aberturas com a MESMA identidade física entre STATE_A e STATE_R:
     TGD  63 de 94        TP1  61 de 92
aberturas cuja geometria muda de ENVELOPE para CONSENSO:
     TGD  31              TP1  31
```

Essas 31 por projeto são a **CR-A, já mesclada na `main`** e ainda **não
propagada** para o gabarito congelado — não são efeito desta CR. Confundir
as duas coisas inflaria o ganho reivindicado aqui.

### 3.2 Identificação do candidato

Gravada em `metadata` de cada `reference_candidate.json`:

```
candidate_state       STATE_C
candidate_version     cand-B-2026-09-07.1
candidate_of          reference.json (schema_version=2)
candidate_criterion   C1 estrutural: as DUAS jambas do vao coincidem
                      (<=1,0cm) com a face interna de uma parede
                      perpendicular (reserva de no'). SEM limiar de largura.
candidate_provenance  gerado offline por build_candidate.py a partir do
                      proprio reference.json oficial; WALL_SPLIT_GAP_CM /
                      OPENING_GAP_MAX_CM inalterados (260,0); nenhuma
                      constante de producao alterada
split_reason          NODE_RESERVE_BOTH_JAMBS
```

Caminho de reprodução, changelog por identidade física e `sha256` de cada
arquivo: `candidate_manifest.json` e o `README.md` da pasta do candidato.

---

## 4. Reconstrução dos 19 casos — e os invariantes por bloco

### 4.1 O que o candidato faz

Para cada um dos 19 vãos que satisfazem `C1`, o eixo é cortado nas duas
jambas e a abertura é descartada. **Tudo o mais é preservado por
construção**, porque o corte só re-rotula peças entre duas paredes: não
move, não cria, não remove nenhuma peça.

| | TGD | TP1 |
|---|---|---|
| casos `C1` | **19** | **19** |
| paredes | 97 → **116** (+19) | 96 → **115** (+19) |
| aberturas | 94 → **75** (−19) | 92 → **73** (−19) |
| **blocos em paredes** | 12508 → **12508** (0) | 12703 → **12703** (0) |
| **blocos órfãos** | 0 → **0** | 0 → **0** |
| comprimento total (cm) | 45362,8 → **42758,8** (**−2604,0**) | 45059,01 → **42455,01** (**−2604,0**) |
| junções `T` | 216 → 196 (**−20**) | 210 → 190 (**−20**) |
| junções `L` | 78 → 126 (**+48**) | 76 → 124 (**+48**) |
| junções `FREE_END` | 8 → 8 (0) | 11 → 11 (0) |

`−2604,0 = 8×101 + 10×156 + 1×236`, exato nos dois projetos.

### 4.2 Invariantes medidos por IDENTIDADE FÍSICA de bloco

Identidade de bloco = `type_name | center_x | center_y | z`. Não é
contagem: é conjunto.

| invariante | TGD | TP1 |
|---|---|---|
| blocos humanos **perdidos** | **0** | **0** |
| blocos humanos **novos** (inventados) | **0** | **0** |
| blocos **duplicados** | **0** | **0** |
| blocos **órfãos** | 0 → **0** | 0 → **0** |
| blocos com **cota `z` alterada** | **0** | **0** |
| blocos com **centro `XY` alterado** | **0** | **0** |
| blocos com **elevação de fiada alterada** | **0** | **0** |
| aberturas removidas | 19 (**= exatamente os 19 casos `C1`**) | 19 (idem) |
| aberturas **adicionadas** | **0** | **0** |
| aberturas com **geometria alterada** | **0** | **0** |
| aberturas removidas **com `source_element_id`** | **0** | **0** |
| paredes fora do escopo com **espessura alterada** | **0** | **0** |

**Nenhum bloco humano foi perdido, duplicado, deslocado ou ficou órfão.**

### 4.3 A única mudança de esquema que aparece — declarada, não escondida

**184 blocos por projeto mudam de ÍNDICE ORDINAL de fiada** (`row`), sem
mudar de cota:

```
deslocamentos ordinais (antigo -> novo):  9->8 (36)   11->9 (32)
                                         13->10 (36)  15->11 (32)  16->12 (48)
elevação em cm de todos eles:  IDÊNTICA
```

Causa: `reconstruct.py` define `row` como a **posição da fiada na pilha
daquela parede**, não como `(z − base)/passo` — decisão de produção
documentada no próprio módulo (meias-fiadas legítimas de peça CORTADA
fora da grade de 20 cm). Ao cortar a parede, o trecho novo tem menos
cotas distintas e os ordinais comprimem. **Não é deslocamento físico**;
é re-indexação.

**Consequência a migrar (não a esconder):** qualquer métrica ou
diagnóstico histórico chaveado por `(wall_id, row)` deixa de ser
comparável. `fiadas_total` sobe de 1379 → 1645 (TGD) e 1365 → 1631 (TP1)
pelo mesmo motivo: a mesma cota física passa a existir em duas paredes.

### 4.4 Mapeamento de identidade — antiga → nova

`W0xx` **não é** identidade física estável e não foi usado como tal. A
identidade usada é `stable_key` = as duas pontas em coordenada de mundo,
ordenadas, a 0,01 cm.

**11 paredes hospedeiras por projeto** dão origem a **30 paredes novas**:

| projeto | mantidas | sumiram | surgiram | **mantidas que mudam de `W0xx` sem mudar de geometria** |
|---|---|---|---|---|
| TGD | 86 | 11 | 30 | **53 de 86** |
| TP1 | 85 | 11 | 30 | **52 de 85** |

Isto **quantifica** a fragilidade de identidade que a reconciliação
apontou como dívida de esquema: mais de 60% das paredes que não mudaram
nada recebem outro `W0xx`, porque o id é sequencial. Sem `stable_key`,
nenhuma comparação por parede sobrevive à regravação.

Inventário das paredes novas (idêntico nos dois projetos):

```
30 paredes novas   comprimento min 109,0 / mediano 324,0 / máximo 1174,0 cm
paredes novas com menos de 100 cm:  0        (nenhuma boneca, nenhum pilarete)
fiadas por parede nova:  mínimo 13, máximo 17
espessura:  14,0 cm em todas as 30
```

Nenhuma parede curta foi criada, portanto **nenhuma exceção de parede
curta foi necessária** — coerente com a proibição do enunciado §5.

### 4.5 Linhagem completa (TGD; o TP1 é o mesmo conjunto físico)

| hospedeira (`W0xx` / `stable_key`) | comp. | aberturas | filhas | soma | vão removido |
|---|---|---|---|---|---|
| `W003` `S-1071.49,-569.95>-1071.49,774.05` | 1344,0 | 1 | `W003`(594,0) + `W060`(594,0) | 1188,0 | 156,0 |
| `W004` `S-656.49,-569.95>-656.49,774.05` | 1344,0 | 3 | `W042`(169,0)+`W004`(324,0)+`W061`(169,0)+`W090`(324,0) | 986,0 | 358,0 |
| `W005` `S-401.49,-569.95>-401.49,774.05` | 1344,0 | 3 | `W043`(169,0)+`W005`(324,0)+`W062`(169,0)+`W091`(324,0) | 986,0 | 358,0 |
| `W006` `S593.50,-569.95>593.50,774.05` | 1344,0 | 3 | `W044`(169,0)+`W006`(324,0)+`W067`(169,0)+`W092`(324,0) | 986,0 | 358,0 |
| `W007` `S848.50,-569.95>848.50,774.05` | 1344,0 | 3 | `W045`(169,0)+`W007`(324,0)+`W068`(169,0)+`W093`(324,0) | 986,0 | 358,0 |
| `W008` `S1263.50,-569.95>1263.50,774.05` | 1344,0 | 1 | `W008`(594,0) + `W069`(594,0) | 1188,0 | 156,0 |
| `W015` `S-146.49,-554.95>-146.49,824.05` | 1379,0 | 1 | `W015`(579,0) + `W064`(644,0) | 1223,0 | 156,0 |
| `W017` `S338.52,-554.95>338.52,824.05` | 1379,0 | 1 | `W017`(579,0) + `W065`(644,0) | 1223,0 | 156,0 |
| `W046` `S-336.49,-84.95>-336.49,289.05` | 374,0 | 1 | `W050`(109,0) + `W063`(109,0) | 218,0 | 156,0 |
| `W047` `S528.50,-84.95>528.50,289.05` | 374,0 | 1 | `W051`(109,0) + `W066`(109,0) | 218,0 | 156,0 |
| `W052` `S-1078.49,17.05>1270.50,17.05` | 2348,99 | 3 | `W056`(939,0) + `W057`(1173,99) | 2112,99 | 236,0 |

Soma dos vãos removidos: `156+358+358+358+358+156+156+156+156+156+236 = 2604,0`.

As **aberturas que sobram** nas filhas são as portas reais: `W052` cede
1 abertura de 91 cm para cada filha (`W056`, `W057`) — as duas com
`measured` correspondente no `input.json` do TGD
(`6558435` e `6558465`). **Nenhuma porta medida foi consumida pelo corte.**

### 4.6 As 19 identidades físicas — tabela completa

Identidade = coordenada de mundo das duas jambas. `W0xx` é rótulo
auxiliar. Resíduos da coluna "perp." são **dentro do modelo humano**
(reconstrução × reconstrução); os resíduos contra a geometria **medida**
(0,001 a 0,259 cm, 38/38 jambas) estão na §2.2/§3 da reconciliação e não
foram remedidos aqui.

#### torre_easy_lo_r00_tgd — confiança ALTA (geometria medida disponível)

| # | identidade física do vão (jamba lo XY → hi XY, cm) | larg | hospedeira antiga | perp. lo | perp. hi | paredes novas |
|---|---|---|---|---|---|---|
| 1 | (-1071.5, 24.0) → (-1071.5, 180.0) | 156.0 | `W003` |`W052` +0.000 | `W055` +0.000 | `W003` + `W060` |
| 2 | (-656.5, -246.0) → (-656.5, -145.0) | 101.0 | `W004` |`W034` +0.000 | `W044` +0.000 | `W042` + `W004` + `W061` + `W090` |
| 3 | (-656.5, 24.0) → (-656.5, 180.0) | 156.0 | `W004` |`W052` +0.000 | `W055` +0.000 | `W042` + `W004` + `W061` + `W090` |
| 4 | (-656.5, 349.0) → (-656.5, 450.0) | 101.0 | `W004` |`W066` +0.000 | `W075` +0.000 | `W042` + `W004` + `W061` + `W090` |
| 5 | (-401.5, -246.0) → (-401.5, -145.0) | 101.0 | `W005` |`W034` +0.000 | `W044` +0.000 | `W043` + `W005` + `W062` + `W091` |
| 6 | (-401.5, 24.0) → (-401.5, 180.0) | 156.0 | `W005` |`W052` +0.000 | `W055` +0.000 | `W043` + `W005` + `W062` + `W091` |
| 7 | (-401.5, 349.0) → (-401.5, 450.0) | 101.0 | `W005` |`W066` +0.000 | `W075` +0.000 | `W043` + `W005` + `W062` + `W091` |
| 8 | (-336.5, 24.0) → (-336.5, 180.0) | 156.0 | `W046` |`W052` +0.000 | `W055` +0.000 | `W050` + `W063` |
| 9 | (-146.5, 24.0) → (-146.5, 180.0) | 156.0 | `W015` |`W052` +0.000 | `W055` +0.000 | `W015` + `W064` |
| 10 | (-139.5, 17.0) → (96.5, 17.0) | 236.0 | `W052` |`W015` +0.000 | `W016` +0.010 | `W056` + `W057` |
| 11 | (338.5, 24.0) → (338.5, 180.0) | 156.0 | `W017` |`W052` +0.000 | `W056` +0.000 | `W017` + `W065` |
| 12 | (528.5, 24.0) → (528.5, 180.0) | 156.0 | `W047` |`W052` +0.000 | `W056` +0.000 | `W051` + `W066` |
| 13 | (593.5, -246.0) → (593.5, -145.0) | 101.0 | `W006` |`W035` +0.000 | `W045` +0.000 | `W044` + `W006` + `W067` + `W092` |
| 14 | (593.5, 24.0) → (593.5, 180.0) | 156.0 | `W006` |`W052` +0.000 | `W056` +0.000 | `W044` + `W006` + `W067` + `W092` |
| 15 | (593.5, 349.0) → (593.5, 450.0) | 101.0 | `W006` |`W067` +0.000 | `W076` +0.000 | `W044` + `W006` + `W067` + `W092` |
| 16 | (848.5, -246.0) → (848.5, -145.0) | 101.0 | `W007` |`W035` +0.000 | `W045` +0.000 | `W045` + `W007` + `W068` + `W093` |
| 17 | (848.5, 24.0) → (848.5, 180.0) | 156.0 | `W007` |`W052` +0.000 | `W056` +0.000 | `W045` + `W007` + `W068` + `W093` |
| 18 | (848.5, 349.0) → (848.5, 450.0) | 101.0 | `W007` |`W067` +0.000 | `W076` +0.000 | `W045` + `W007` + `W068` + `W093` |
| 19 | (1263.5, 24.0) → (1263.5, 180.0) | 156.0 | `W008` |`W052` +0.000 | `W056` +0.000 | `W008` + `W069` |

#### torre_easy_lo_r00_tp1 — confiança MÉDIA-ALTA (sem fonte medida independente)

| # | identidade física do vão (jamba lo XY → hi XY, cm) | larg | hospedeira antiga | perp. lo | perp. hi | paredes novas |
|---|---|---|---|---|---|---|
| 1 | (6607.2, 1127.0) → (6607.2, 1283.0) | 156.0 | `W003` |`W052` +0.000 | `W055` +0.000 | `W060` + `W003` |
| 2 | (7022.2, 857.0) → (7022.2, 958.0) | 101.0 | `W004` |`W034` +0.000 | `W044` +0.000 | `W061` + `W089` + `W004` + `W042` |
| 3 | (7022.2, 1127.0) → (7022.2, 1283.0) | 156.0 | `W004` |`W052` +0.000 | `W055` +0.000 | `W061` + `W089` + `W004` + `W042` |
| 4 | (7022.2, 1452.0) → (7022.2, 1553.0) | 101.0 | `W004` |`W065` +0.000 | `W074` +0.000 | `W061` + `W089` + `W004` + `W042` |
| 5 | (7277.2, 857.0) → (7277.2, 958.0) | 101.0 | `W005` |`W034` +0.000 | `W044` +0.000 | `W062` + `W090` + `W005` + `W043` |
| 6 | (7277.2, 1127.0) → (7277.2, 1283.0) | 156.0 | `W005` |`W052` +0.000 | `W055` +0.000 | `W062` + `W090` + `W005` + `W043` |
| 7 | (7277.2, 1452.0) → (7277.2, 1553.0) | 101.0 | `W005` |`W065` +0.000 | `W074` +0.000 | `W062` + `W090` + `W005` + `W043` |
| 8 | (7342.2, 1127.0) → (7342.2, 1283.0) | 156.0 | `W046` |`W052` +0.000 | `W055` +0.000 | `W050` + `W063` |
| 9 | (7532.2, 1127.0) → (7532.2, 1283.0) | 156.0 | `W017` |`W052` +0.000 | `W055` +0.000 | `W064` + `W017` |
| 10 | (7539.2, 1120.0) → (7775.2, 1120.0) | 236.0 | `W052` |`W017` +0.000 | `W018` +0.010 | `W056` + `W057` |
| 11 | (8017.3, 1127.0) → (8017.3, 1283.0) | 156.0 | `W019` |`W052` +0.000 | `W056` +0.000 | `W065` + `W019` |
| 12 | (8207.2, 1127.0) → (8207.2, 1283.0) | 156.0 | `W047` |`W052` +0.000 | `W056` +0.000 | `W051` + `W066` |
| 13 | (8272.2, 857.0) → (8272.2, 958.0) | 101.0 | `W006` |`W035` +0.000 | `W045` +0.000 | `W067` + `W091` + `W006` + `W044` |
| 14 | (8272.2, 1127.0) → (8272.2, 1283.0) | 156.0 | `W006` |`W052` +0.000 | `W056` +0.000 | `W067` + `W091` + `W006` + `W044` |
| 15 | (8272.2, 1452.0) → (8272.2, 1553.0) | 101.0 | `W006` |`W066` +0.000 | `W075` +0.000 | `W067` + `W091` + `W006` + `W044` |
| 16 | (8527.2, 857.0) → (8527.2, 958.0) | 101.0 | `W007` |`W035` +0.000 | `W045` +0.000 | `W068` + `W092` + `W007` + `W045` |
| 17 | (8527.2, 1127.0) → (8527.2, 1283.0) | 156.0 | `W007` |`W052` +0.000 | `W056` +0.000 | `W068` + `W092` + `W007` + `W045` |
| 18 | (8527.2, 1452.0) → (8527.2, 1553.0) | 101.0 | `W007` |`W066` +0.000 | `W075` +0.000 | `W068` + `W092` + `W007` + `W045` |
| 19 | (8942.2, 1127.0) → (8942.2, 1283.0) | 156.0 | `W008` |`W052` +0.000 | `W056` +0.000 | `W069` + `W008` |

---

## 5. RISCO PRINCIPAL — a mudança de topologia T → L

Este era o item de maior risco declarado pela reconciliação (§6.2): −20
`T` / +48 `L` por projeto muda **qual regra de amarração se aplica** ao
nó. Foi investigado nó a nó.

**Nenhuma regra de amarração em X, T ou L foi alterada nesta CR.**
Nenhuma `B54` foi forçada. Nenhuma amarração humana foi removida.
Nenhuma exceção de parede curta foi criada.

### 5.1 O balanço por NÓ (e não por entrada de parede)

Contagem de nós físicos distintos (agrupados por coordenada, mesma
tolerância de `detect_junctions`), idêntica nos dois projetos:

| transição | TGD | TP1 | leitura |
|---|---|---|---|
| `T` → `L` | **22** | **22** | a perpendicular deixa de atravessar: encontra o FIM da parede |
| `AUSENTE` → `T` | **13** | **13** | nó **novo** na ponta nova, onde ela encosta no meio de uma parede |
| `AUSENTE` → `L` | **2** | **2** | as duas pontas do corte de 236 cm |
| `T` → `AUSENTE` | **1** | **1** | **relocação**, não perda — ver §5.4 |
| `T` → `T` / `L` → `L` | 34 / 12 | 34 / 12 | **mesmo tipo**, mas a lista de paredes participantes mudou de `stable_key` (a hospedeira foi cortada em outro ponto) |
| nós sem nenhuma mudança | 86 | 85 | não entram na contagem acima |
| **total de nós** | 155 → **169** | 154 → **168** | |

Reconciliação com a contagem por entrada de parede: cada nó `L` gera 2
entradas → `+24 nós × 2 = +48 L`; os nós `T` caem `−22 −1 +13 = −10` →
`−10 × 2 = −20 T`. **Confere.**

### 5.2 O TESTE DECISIVO — a ocupação física do nó

Se a mudança T→L fosse artefato da fragmentação, ela apareceria como
mudança na alvenaria do nó: peça a mais, peça a menos, peça trocada.

Medido, para **todos** os nós que mudam de tipo, o conjunto de peças
humanas que cobre fisicamente a pegada do nó (retângulo real de cada
bloco, fiada a fiada):

```
nós com tipo alterado:                                   38  (por projeto)
                        dos quais com o conjunto de peças
                        físicas BYTE-IDÊNTICO antes/depois:  38  (100%)
peças só ANTES:   0        peças só DEPOIS:   0
```

**A alvenaria humana no nó não muda em nenhum dos 38.** O que muda é o
rótulo topológico que a reconstrução dá ao nó — e ele muda **porque a
parede hospedeira realmente termina ali**, não porque foi fragmentada.

### 5.3 Nó exemplar `T` → `L` — `(-1078,487 ; 17,048)` (TGD)

Geometria, antes e depois:

| | ANTES (STATE_R) | DEPOIS (STATE_C) |
|---|---|---|
| tipo | `T` | `L` |
| parede que TERMINA no nó | `S-1078.49,17.05 > 1270.50,17.05` (E-O, 2348,99 cm) | `S-1078.49,17.05 > -139.49,17.05` (E-O, 939,0 cm) |
| parede perpendicular | `S-1071.49,-569.95 > -1071.49,774.05` (N-S, **1344,0 cm, contínua**) | `S-1071.49,-569.95 > -1071.49,24.05` (N-S, **594,0 cm, termina 7 cm além do nó**) |
| braços | 1 (fim) + 2 (travessia) = **3** → `T` | 2 → `L` |

Blocos humanos na pegada do nó — **as duas fiadas alternadas**:

| cota | ANTES | DEPOIS |
|---|---|---|
| z=0 | `B34` de `W052` @ (−1061,49; 17,05) | `B34` de `W056` @ (−1061,49; 17,05) |
| z=20 | `B34` de `W003` @ (−1071,49; 7,05) | `B34` de `W003` @ (−1071,49; 7,05) |
| z=40 | `B34` de `W052` | `B34` de `W056` |
| z=60 | `B34` de `W003` | `B34` de `W003` |
| … | alternância perfeita nas 11 fiadas | idem |
| z=200 | `B34` de `W052` | `B34` de `W056` |

**Ownership:** a peça de amarração alterna fiada a fiada entre o
hospedeiro E-O e a perpendicular N-S — a alternância de nó descrita na
seção 10.6 das regras. As **mesmas 11 peças `B34`, nas mesmas
coordenadas**, com o mesmo dono físico. A troca `W052 → W056` é só o novo
rótulo do trecho oeste da parede cortada 2,3 km de coordenada adiante.

**Veredito para este nó: a mudança representa a geometria real.** Antes
do corte, a reconstrução declarava que a parede N-S *atravessava* o nó e
seguia até `y=774`. Ela não segue: entre `y=24` e `y=180` há um vão de
156 cm com **0 blocos humanos em 13 fiadas**. A continuidade era o
artefato; o `L` é a descrição correta.

### 5.4 Os nós NOVOS não são nós sem amarração

Exemplo `AUSENTE` → `T`, `(-336,487 ; 180,048)` (TGD): a ponta nova
`S-336.49,180.05>-336.49,289.05` encosta no meio da parede E-O
`S-1078.49,187.05>-139.49,187.05`.

```
z=0   B34 (parede N-S)      z=20  B54 (parede E-O)
z=40  B34                   z=60  B54
...                         ...
z=220 B54                   z=240 CAN34 (canaleta de topo)
```

**12 das 13 fiadas com peça de amarração real (`B34`/`B54`), alternando
corretamente entre as duas paredes.** A 13ª é a canaleta de topo. Esse nó
**já existia fisicamente** na alvenaria humana e já estava amarrado — o
que não existia era o **registro** dele, porque a parede hospedeira era
descrita como contínua e a ponta não terminava ali.

Mesma leitura para `AUSENTE` → `L` em `(96,513 ; 17,048)`: 11 fiadas,
todas `B34`, alternando `W016` ↔ `W057`.

### 5.5 O único nó que "some" é uma RELOCAÇÃO

`T` → `AUSENTE` em `(103,523 ; 24,048)` (TGD) / `(7782,26 ; 1126,95)`
(TP1). Não é perda: o mesmo canto físico passa a ser registrado a
**9,91 cm** dali, em `(96,513 ; 17,048)`, como `L` — porque a parede E-O
cortada agora **começa** em `x=96,51` em vez de atravessar. As 11 peças
`B34` são as mesmas.

Verificação de continuidade, feita para todos os nós:

```
nós que existem em STATE_R e não em STATE_C:  1  (por projeto)
   e desse 1, quantos NÃO têm nó equivalente em STATE_C a ≤20 cm:  0
nós que existem em STATE_C e não em STATE_R:  15 (por projeto)
```

**Nenhum nó com amarração humana ficou órfão.**

### 5.6 O que isto NÃO resolve

- O candidato **não** revalida as 48 junções `L` novas contra o
  comportamento do **solver** em nó `L` — só contra a alvenaria humana.
  A regra de amarração aplicável muda, e o solver de produção passa a
  resolver `L` onde resolvia `T`. O efeito disso está em §7 e é
  **categoria C** (mudança de escopo de avaliação) no TGD e **A+B+C** no
  TP1.
- **Se a integração da CR-B exigir mudar a regra de amarração em `L`,
  `T` ou `X` para acomodar esses nós, isso é PARADA OBRIGATÓRIA e
  decisão do usuário.** Nesta CR nada disso foi tocado, e a evidência
  medida diz que não é necessário: a alvenaria humana nos 38 nós já está
  amarrada corretamente, com `B34`/`B54` alternando, sem nenhuma peça
  fora do lugar.

---

## 6. As três divergências pendentes — R1, R2, R3

Remedidas nesta sessão, de forma independente, sobre o `input.json`
**medido** do TGD (167 paredes, documento Revit separado). O `input.json`
do TP1 **não** é fonte medida e não foi usado como evidência.

**Nada foi corrigido por suposição.** O candidato grava, nas três, o
**valor humano** — a mesma escolha que a decisão **D4** coloca ao usuário.

### 6.1 R1 — `W052`: sobra medida de 30,01 cm dentro do vão

Identidade física do vão: `(-139,487 ; 17,048) → (96,513 ; 17,048)`,
236,0 cm. Coordenadas no frame `TESTE MODULACAO (2026)`; a coluna TORRE é
o mesmo ponto no documento do gabarito (`+[7678,7371 ; 1102,9024]`).

| o que | frame INPUT (cm) | frame TORRE `04. TGD` (cm) |
|---|---|---|
| jamba lo — fim da alvenaria humana | (−139,487 ; 17,048) | (7539,250 ; 1119,950) |
| **fim MEDIDO de `W006` (a sobra)** | **(−109,480 ; 17,049)** | **(7569,257 ; 1119,951)** |
| jamba hi — início humano **e** início medido de `W005` | (96,513 ; 17,048) | (7775,250 ; 1119,950) |
| perpendicular medida `W019` (eixo) | (−146,490 ; 24,049) | (7532,247 ; 1126,951) |
| perpendicular medida `W021` (eixo) | (103,517 ; 24,049) | (7782,254 ; 1126,951) |

**FATO (medido).** `W006` (medida, colinear, `s = 0,001 cm`) vai de
`t = −939,006` a `t = +30,007` — **30,007 cm além** da jamba humana.
`W005` (medida, colinear) começa em `t = 236,000` — **residual 0,000**
contra a jamba hi humana. As duas jambas estão confirmadas por
perpendicular medida: `W019` face interna em `t = −0,003`; `W021` face
interna em `t = +236,004`. A ponta de `W006` em `t = +30,007` é **livre**:
a perpendicular medida mais próxima (`W019`) está 37 cm atrás.

**FATO (humano).** `0` blocos humanos em qualquer fiada no intervalo
`[0 ; 236]` — inclusive em `[0 ; 30]`, onde estaria a sobra.

**INFERÊNCIA (não veredito).** Duas leituras seguem abertas, e nenhuma
evidência local decide entre elas: (a) existe no CAD uma boneca de ~30 cm
que a pessoa optou por não modular; (b) o pareamento de eixos do
`input.json` prolongou a linha medida. Observação nova, que **não**
decide: `30,007 cm` não é comprimento modular deste catálogo
(`B39=39`, `B34=34`, `B19=19`) nem soma de dois deles — o que enfraquece
um pouco a leitura (a), sem excluí-la.

**INCERTEZA.** Onde a parede oeste realmente termina: `t = 0` (humano) ou
`t = 30,007` (medido). **Afeta o comprimento da parede nova `W056`, não a
classificação do vão.**

**O que o candidato faz:** grava `t = 0` (o valor humano) e a diferença
fica registrada. Não corrige.

### 6.2 R2 — `W006`/`W007` em `[324,425]`: par de paredes paralelas no CAD

Identidade física: `(593,513 ; −246,0) → (593,513 ; −145,0)`, 101,0 cm.
Origem `t = 0` na jamba lo.

| o que | `t` (cm) | frame TORRE `04. TGD` (cm) |
|---|---|---|
| `W043` medida, colinear — **termina** em | `+0,307` | (8272,25 ; 856,90) |
| `W084` medida, colinear — **recomeça** em | `+86,849` | (8272,26 ; 943,75) |
| `W053` medida, PERPENDICULAR (eixo `y = −152,151`) | `+93,849` | (8272,26 ; 950,75) |
| `W100` medida, PERPENDICULAR (eixo `y = −138,201`, `x` 711,5…842,5) | `+107,799` | (8390,25 ; 964,70) |
| `W045` HUMANA, perpendicular (eixo `y = −137,952`) | `+108,048` | (8272,25 ; 964,95) |
| jamba hi humana | `+101,0` | (8272,25 ; 957,90) |

**FATO (medido), novo nesta sessão.** O vão **medido** neste eixo é
`86,849 − 0,307 = 86,542 cm`. O vão **humano** é `101,0 cm`. A diferença
é **14,458 cm** — praticamente uma espessura de parede (14,0 cm).
`W053` e `W100` estão a 13,95 cm uma da outra. **`W100` não alcança o eixo
do hospedeiro**: seu `x` vai de 711,5 a 842,5, enquanto o hospedeiro está
em `x = 593,5`. Quem toca o hospedeiro é só `W053` (`x` 586,5…855,5).

**FATO (humano).** A perpendicular humana `W045` tem **a extensão de
`W053`** (`x` 586,5…855,5, 269 cm) **na linha de `W100`**
(`y = −137,952` contra `−138,201`, 0,25 cm). `0` blocos humanos no vão.

**INFERÊNCIA (não veredito), mais precisa que a da reconciliação.** As
duas linhas medidas a 13,95 cm de distância têm exatamente a assinatura
de **duas FACES da mesma parede de 14 cm** que o pareamento de eixos não
juntou numa única linha de centro (que ficaria em `y = −145,176`). Se
essa leitura estiver certa, o eixo real está ~7 cm de cada lado das duas,
e tanto o eixo medido de `W053` quanto o humano de `W045` estão
deslocados — em sentidos opostos. Leitura alternativa que **não** foi
excluída: parede dupla / shaft real no CAD, simplificado pela pessoa.

**INCERTEZA.** A largura do vão: `101,0` (humano) ou `86,5` (medido); e
qual é o eixo verdadeiro da perpendicular. A jamba **fica confirmada nas
duas leituras** (resíduo −0,151 cm contra a face de `W053`; −0,201 cm
contra a face de `W100`) — por isso a classificação dos dois casos não
muda.

**O que o candidato faz:** grava `101,0` (o valor humano).

### 6.3 R3 — `W015` (TGD) / `W017` (TP1): 193 cm sem parede medida

Identidade física: `(-146,487 ; 24,048) → (-146,487 ; 180,048)`, 156,0 cm.

| o que | `t` (cm) | frame TORRE `04. TGD` (cm) |
|---|---|---|
| `W019` medida, colinear — termina em | `+0,001` | (7532,25 ; 1126,95) |
| jamba hi — face da perpendicular medida `W007` | `+156,001` | (7532,25 ; 1282,95) |
| **primeiro elemento medido depois do vão** (`W113`, deslocado `s = −13,0`) | `+373,046` | (7545,25 ; 1475,95) |
| fim da alvenaria humana neste eixo | `+824,0` | (7532,25 ; 1926,95) |

**FATO (medido).** `373,046 − 180,048 = 192,998 cm` — os 193 cm,
confirmados de forma independente. Nesse intervalo não há **nenhuma**
parede medida colinear (`|s| ≤ 8 cm`). Os elementos medidos mais próximos
estão a `s = −7,0` (`W137`, 15 cm) e `s = −13,0` (`W113`, 104 cm), e só a
partir de `t = 348,998`.

**FATO (humano).** A pessoa construiu alvenaria contínua de `t = 156` até
`t = 824`. As duas jambas do vão **estão confirmadas** por geometria
medida (`W019` termina em `+0,001`; face de `W007` em `+156,001`).

**INFERÊNCIA.** Lacuna de extração do `input.json`, não do vão: o input
do TGD vem de outro documento, com 167 paredes contra 97 do gabarito, e
já se sabe que a cobertura de eixos não é total.

**INCERTEZA.** Se falta parede no CAD medido ou se a pessoa construiu
onde o CAD não pedia. **Não afeta o vão** — afeta o trecho **depois**
dele.

**O que o candidato faz:** grava a parede humana `t = [156 ; 800]`
(644 cm) inteira.

### 6.4 Nenhuma das três muda a classificação

Em R1, R2 e R3, o miolo do vão continua com: **0 blocos humanos**, **sem
verga**, **sem procedência medida**, **reserva de nó nas duas jambas**.
As três são divergências sobre **onde a parede acaba** e **qual é o eixo
da vizinha** — não sobre "é porta ou não é".

### 6.5 Conferência no Revit — o que inspecionar, exatamente

Sessão MCP curta, **somente leitura**, no documento
`TORRE EASY-LO-R00_desanexado_joaoC9CL7.rvt`, nível **`04. TGD`**, e no
documento `TESTE MODULACAO (2026).rvt`, nível **`00. 000`** (o CAD de
entrada). **Nenhuma medição ao vivo foi inventada aqui.**

| # | documento / vista | coordenada (cm) | o que medir | o que a resposta decide |
|---|---|---|---|---|
| **R1** | `TESTE MODULACAO (2026)`, planta `00. 000`, layer `Arquitetura` | linha em `y ≈ 17,05`, entre `x = −139,49` e `x = −109,48` | existe linha de CAD nesse trecho de 30,01 cm? termina livre ou encosta em quê? | se existe e é parede → a pessoa suprimiu uma boneca; se não existe → o pareamento prolongou o eixo |
| **R1** | `TORRE`, `04. TGD` | (7539,25 ; 1119,95) a (7569,26 ; 1119,95) | há bloco humano nesses 30 cm em **qualquer** fiada? | confirma/refuta o `0` medido no gabarito |
| **R2** | `TESTE MODULACAO (2026)`, planta `00. 000`, layer `Arquitetura` | linhas em `y = −152,151` e `y = −138,201`, faixa `x` 586…856 | as duas linhas são as **faces** de uma única parede de 14 cm, ou são duas paredes? há terceira linha em `y ≈ −145,18`? | decide entre "pareamento não juntou as faces" e "parede dupla/shaft real" |
| **R2** | `TESTE MODULACAO (2026)` | linha em `x ≈ 593,52`, entre `y = −159,15` e `y = −145,0` | existe CAD nesses 14,15 cm que o humano deixou vazio? | decide se o vão real é 86,5 ou 101,0 cm |
| **R3** | `TESTE MODULACAO (2026)`, planta `00. 000` | eixo `x ≈ −146,49`, faixa `y` de 180,05 a 373,05 | existe alguma linha de `Arquitetura` nesses 193 cm (inclusive deslocada ±13 cm)? | confirma lacuna de extração ou revela parede humana sem CAD |
| **R3** | `TORRE`, `04. TGD` | (7532,25 ; 1282,95) a (7545,25 ; 1475,95) | a alvenaria humana ali é contínua? em que fiadas? | confirma o trecho de 644 cm do candidato |

Parâmetros a ler em cada elemento: `Location` (curva), `Width`/espessura,
`Level`, `Comments`/`Type Name`, e — nas famílias de abertura — os três
parâmetros de vão (`Largura_abertura`, `Altura_abertura`, `Peitoril`),
que são os que a extração já usa.

---

## 7. Projeção real do solver

Solver de **produção**, sem uma linha alterada, rodado sobre cópias
isoladas. Nada escrito em `nuvem/benchmark/projects/**`. Tempo total:
10m40s para as 6 execuções.

### 7.1 A assimetria que muda tudo — TGD ≠ TP1

```
TGD  input.json = wall_modeling_snapshot (CAD medido, 167 paredes, 82 aberturas measured)
     -> regravar o GABARITO NÃO MUDA A ENTRADA DO SOLVER
TP1  input.json = derivado do reference.json (96 paredes, 0 measured)
     -> regravar o gabarito MUDA A ENTRADA DO SOLVER
```

Medido, e é categórico:

| TGD — solver sobre `input.json` OFICIAL | contra STATE_A | contra STATE_R | contra STATE_C |
|---|---|---|---|
| blocos colocados | 11731 | 11731 | 11731 |
| erros críticos | 872 | 872 | 872 |
| **paredes pareadas com o gabarito** | 84 | 84 | **98** |
| `similarity` | 0,0493 | 0,0493 | **0,0566** |

**O resultado do solver do TGD é byte-idêntico nos três casos.** Trocar o
gabarito do TGD **não melhora nem piora o solver** — melhora o
**pareamento** (84 → 98 paredes casadas, +17%) e o `evaluation_scope`.
Isso é **categoria C**, mudança de escopo de avaliação, e não pode ser
apresentado como ganho de solver.

### 7.2 TP1 — onde o gabarito realmente entra no solver

Três entradas, todas derivadas do gabarito, comparáveis entre si:

| | `IN_OFICIAL` | `IN_R` (CR-A propagada) | `IN_C` (candidato) | (R−OF) | **(C−R)** |
|---|---|---|---|---|---|
| paredes de entrada | 96 | 96 | **115** | 0 | +19 |
| aberturas de entrada | 92 | 92 | **73** | 0 | −19 |
| **blocos colocados** | 19572 | 19286 | 19364 | **−286** | **+78** |
| **erros críticos** | 485 | 327 | **262** | **−158** | **−65** |
| paredes pareadas | 96 | 96 | 115 | 0 | +19 |
| `OPENING_BLOCK_CROSSES_JAMB` | 168 | **0** | 0 | **−168** | 0 |
| `COVERAGE_GAP_IN_ROW` | 214 | 304 | **182** | **+90** | **−122** |
| `COVERAGE_ROW_MOSTLY_EMPTY` | 0 | 14 | **0** | **+14** | **−14** |
| `PRISM_CONTINUOUS_JOINT` | 290 | 286 | **244** | −4 | **−42** |
| `PRISM_JOINT_STACK` | 18 | 18 | 15 | 0 | −3 |
| **`PRISM_STAGGER_BELOW_TARGET`** | 1506 | 1444 | **1545** | −62 | **+101** |
| `POSITION_OVERLAP` | 18 | 18 | **9** | 0 | **−9** |
| `COMPENSATOR_CONSECUTIVE` | 1480 | 1466 | 1410 | −14 | −56 |
| `COMPENSATOR_VERTICAL_STRIP` | 190 | 187 | 182 | −3 | −5 |
| **`COMPENSATOR_AVOIDABLE`** | 87 | 87 | **104** | 0 | **+17** |
| `COMPENSATOR_EXCESS_IN_RUN` | 1135 | 1128 | 1134 | −7 | +6 |
| **`JUNCTION_NOT_ALTERNATING`** | 0 | 0 | **16** | 0 | **+16** |
| `JUNCTION_MISSING_BINDING` | 9 | 9 | 9 | 0 | **0** |

**A coluna `(R−OF)` NÃO é ganho desta CR.** Ela é a **CR-A já mesclada na
`main`** finalmente propagada para o gabarito: `CROSS_JAMB 168 → 0`,
`críticos 485 → 327`, `cobertura +90 / +14` — exatamente os números que o
`PROJECT_STATUS.md` registra como *"ganho projetado pela CR-B que NÃO é
ganho integrado"*. Confirmado aqui: ele se materializa ao **propagar a
CR-A**, não ao cortar os 19.

### 7.3 O mesmo experimento no TGD (hipotético, para controle)

O TGD **não** deriva a entrada do gabarito, mas rodar o mesmo experimento
lá é o controle de que o efeito do corte é o mesmo edifício, não um
acidente do TP1. `IN_R` → `IN_C`:

| código | `IN_R` | `IN_C` | Δ | TP1 (mesmo Δ) |
|---|---|---|---|---|
| erros críticos | 355 | **290** | **−65** | −65 |
| `COVERAGE_GAP_IN_ROW` | 283 | 182 | −101 | −122 |
| `COVERAGE_ROW_MOSTLY_EMPTY` | 14 | 0 | −14 | −14 |
| `PRISM_CONTINUOUS_JOINT` | 314 | 272 | −42 | −42 |
| `PRISM_JOINT_STACK` | 20 | 17 | −3 | −3 |
| `POSITION_OVERLAP` | 18 | 9 | −9 | −9 |
| `COMPENSATOR_CONSECUTIVE` | 1470 | 1414 | −56 | −56 |
| **`PRISM_STAGGER_BELOW_TARGET`** | 1486 | **1591** | **+105** | +101 |
| **`JUNCTION_NOT_ALTERNATING`** | 16 | **32** | **+16** | +16 |
| **`COMPENSATOR_AVOIDABLE`** | 88 | **105** | **+17** | +17 |
| blocos | 19392 | 19433 | +41 | +78 |

Os deltas coincidem quase peça a peça nos dois níveis — é o mesmo
edifício, como o pareamento físico 19/19 já indicava.

### 7.4 Os validadores sobre o PRÓPRIO gabarito (piso de ruído)

Aqui não há solver: são os validadores rodando sobre a alvenaria humana.

| código | TGD A | TGD R | TGD C | **(C−R)** | TP1 A | TP1 R | TP1 C | **(C−R)** |
|---|---|---|---|---|---|---|---|---|
| **`OPENING_BLOCK_CROSSES_JAMB`** | **208** | **0** | **0** | **0** | **209** | **0** | **0** | **0** |
| `OPENING_MISSING_LINTEL` | 56 | 60 | 48 | **−12** | 53 | 57 | 45 | **−12** |
| `COVERAGE_GAP_IN_ROW` | 626 | 648 | 601 | **−47** | 615 | 637 | 590 | **−47** |
| **`COVERAGE_MISSING_ROW`** | 95 | 95 | **112** | **+17** | 94 | 94 | **111** | **+17** |
| **`COVERAGE_ROW_MOSTLY_EMPTY`** | 85 | 85 | **108** | **+23** | 120 | 120 | **143** | **+23** |
| **`JUNCTION_MISSING_BINDING`** | 373 | 373 | **422** | **+49** | 365 | 365 | **414** | **+49** |
| `JUNCTION_NOT_ALTERNATING` | 9 | 9 | 9 | 0 | 9 | 9 | 9 | 0 |
| `JUNCTION_HALF_BLOCK_ADJACENT` | 264 | 264 | 264 | 0 | 259 | 259 | 259 | 0 |
| `PRISM_*` (3 códigos) | 126/8/101 | 129/8/101 | 129/8/101 | **0/0/0** | 122/8/101 | 125/8/101 | 125/8/101 | **0/0/0** |
| `COMPENSATOR_*` (3 códigos) | 52/57/26 | idem | idem | **0/0/0** | 52/54/26 | idem | idem | **0/0/0** |
| `POSITION_OVERLAP` | 0 | 0 | 0 | **0** | 1 | 1 | 1 | **0** |
| `COVERAGE_PARTIAL_WALL` | 4 | 4 | 4 | 0 | — | — | — | — |

**Achado que corrige uma expectativa da reconciliação.** O gate proposto
em §10.7 dela era: *"`OPENING_BLOCK_CROSSES_JAMB` contra o gabarito novo
deve ir de 208/209 para **0**"*. Ele **passa** — mas o zero já acontece em
**STATE_R**, o round-trip **sem corte**. Ou seja: **as 208/209 violações
que o gabarito comete contra si mesmo são inteiramente explicadas pela
CR-A (envelope → consenso), não pelos 19 cortes.** Atribuir esse zero à
CR-B seria erro de contabilidade. O corte contribui `0` nesse código.

**`POSITION_OVERLAP` com delta ZERO nos dois projetos, no gabarito e no
solver-sobre-o-gabarito: nenhuma colisão física nova.**

### 7.5 Decomposição A / B / C / D — sem somar o que não se soma

**(A) Correção de artefato do gabarito** — o gabarito para de se
contradizer:

- `−19` aberturas por projeto que nunca foram aberturas: `0` blocos no
  miolo em 13 fiadas, `0` verga, `0` procedência medida, reserva de nó nas
  duas jambas.
- `OPENING_MISSING_LINTEL` no gabarito: **−12** por projeto — o gabarito
  deixa de ser acusado de "porta sem verga" onde não há porta.
- `COVERAGE_GAP_IN_ROW` no gabarito: **−47** por projeto — as tiras de
  15 cm e o miolo deixam de ser cobrados como "parede a preencher".
- **NÃO pertence a esta categoria:** o `CROSS_JAMB 208/209 → 0`. Ele é da
  **CR-A**, medido em §7.4.

**(B) Defeito real do solver, recém-exposto** — o candidato não o cria,
torna-o mensurável:

- **`JUNCTION_NOT_ALTERNATING` `+16`** nos dois projetos. É exatamente o
  risco T→L se materializando **na saída do solver**: nos nós que passam
  a ser `L`, o solver não alterna a peça de amarração entre as fiadas como
  a pessoa alterna. §5.3 mostra que a **alvenaria humana alterna
  perfeitamente** (11 fiadas, `B34` ↔ `B34`, `B34` ↔ `B54`); o solver não
  reproduz isso. **É defeito do solver, e é o item mais importante desta
  projeção.**
- `PRISM_STAGGER_BELOW_TARGET` **+101 / +105**: o desencontro de junta cai
  nas pontas novas.
- `COMPENSATOR_AVOIDABLE` **+17**: mais compensador evitável nos trechos
  recém-delimitados.

Nenhum dos três foi corrigido aqui. **Cada um exige CR própria**, com
STATE_A/B próprios. Corrigi-los dentro da CR-B seria misturar
"reconstruir o gabarito" com "consertar o solver".

**(C) Mudança de escopo de avaliação** — o número muda porque a unidade
mudou, não porque a alvenaria mudou:

- **TGD inteiro**: solver byte-idêntico; muda o pareamento (84 → 98) e o
  `evaluation_scope`.
- `JUNCTION_MISSING_BINDING` **+49** no gabarito, com a alvenaria
  **byte-idêntica** nos 38 nós que mudam de tipo (§5.2). Dedup por
  `(ponto, fiada)`: 78 achados novos, **62 deles em nós cujo tipo mudou**.
  No nó exemplar `(-1078,5 ; 17,0)` a contagem é a **mesma** antes e
  depois (5 achados, fiadas 8/10/12/13/14) — só o rótulo vai de `T` para
  `L`. **Nenhuma peça humana some**; o que muda é a unidade avaliada.
  Isto carrega uma **suspeita de categoria (B)**: o crédito de amarração
  de nó pode ser sensível ao rótulo `T`/`L` e ao dono da peça. **Não foi
  investigado nem corrigido nesta CR** (proibido mexer em regra de
  amarração) e vira **gate explícito** da CR de integração.
- `COVERAGE_MISSING_ROW` **+17** e `COVERAGE_ROW_MOSTLY_EMPTY` **+23** no
  gabarito. Causa medida: `expected_rows = 17` é **global**, e as paredes
  novas têm 13–14 fiadas (`W003` 14, `W005` 13, `W006` 13…). Antes, a
  parede-mãe exibia 17 porque **somava** as fiadas dos dois lados do vão.
  **Isto não é puro artefato**: revela um fato real do projeto humano que
  a agregação escondia — um dos trechos não sobe até a última fiada. É
  mudança de unidade que **expõe** informação, e precisa de decisão sobre
  o que `expected_rows` deve significar depois do corte.
- `fiadas_total` 1379 → 1645 e a re-indexação ordinal de 184 blocos (§4.3).

**(D) Divergência humana ainda inconclusiva** — R1, R2, R3 (§6). Nenhuma
delas entra em nenhuma das contagens acima como "corrigida".

### 7.6 A frase honesta sobre o saldo

**Há transferência de defeito entre categorias.** O corte troca

```
−122 COVERAGE_GAP_IN_ROW   −42 PRISM_CONTINUOUS_JOINT   −14 ROW_MOSTLY_EMPTY
 −9 POSITION_OVERLAP       −56 COMPENSATOR_CONSECUTIVE   −3 PRISM_JOINT_STACK
```

por

```
+101 PRISM_STAGGER_BELOW_TARGET   +16 JUNCTION_NOT_ALTERNATING
 +17 COMPENSATOR_AVOIDABLE         +6 COMPENSATOR_EXCESS_IN_RUN
```

O saldo de `critical_errors` (327 → 262, **−65**) é favorável, **e mesmo
assim não deve ser usado como argumento de classificação** — §8 do
enunciado da reconciliação é explícito, e foi respeitado: nenhum dos 19
casos foi classificado por número de score. A classificação vem de (A),
(B) e (C); (D) só aparece aqui, depois de tudo decidido.

**`+16 JUNCTION_NOT_ALTERNATING` é amarração.** Não é aceitável tratá-lo
como custo diluído num saldo positivo: é o domínio central do sistema, e
está registrado como **pendência que a CR de integração precisa resolver
ou aceitar explicitamente**.

---

## 8. Invariantes — conferidos, um a um

| invariante do enunciado §8 | resultado | onde |
|---|---|---|
| nenhum bloco humano perdido ou órfão | **OK** — 0 perdidos, 0 novos, 0 duplicados, 0 órfãos; `z`/`XY`/elevação idênticos em 12508 e 12703 blocos | §4.2 |
| nenhuma abertura medida alterada | **OK** — 0 das 19 removidas tem `source_element_id`; as 82 `measured` do TGD nem são tocadas (vivem no `input.json`, que não muda) | §4.2 |
| nenhuma parede fora do escopo modificada | **OK** — 86/85 paredes mantidas com `stable_key` idêntico e espessura idêntica; só as 11 hospedeiras mudam | §4.4 |
| nenhuma nova colisão física | **OK** — `POSITION_OVERLAP` delta **0** no gabarito (TGD 0→0, TP1 1→1); no solver o código **cai** 18→9 | §7.4 |
| identidades estáveis | **OK** para `stable_key`; **FRÁGIL** para `W0xx`: 53/86 (TGD) e 52/85 (TP1) paredes inalteradas mudam de id | §4.4 |
| determinismo | **OK** — 3 processos novos, `sha256` idêntico nos 4 arquivos dos 2 projetos | abaixo |
| gabarito antigo preservado | **OK** — STATE_A e STATE_R lado a lado com o candidato | §3.1 |
| baseline oficial intocado | **OK** — `git diff` vazio em `nuvem/benchmark/projects/**` | §3 |
| regras normativas intocadas | **OK** — `nuvem/REGRAS_MODULACAO_BLOCOS.md` sem diff | §3 |
| solver de produção intocado | **OK** — `nuvem/core/**` sem diff; o solver foi **executado**, nunca alterado | §3 / §7 |

Determinismo, verificado em 3 execuções independentes:

```
torre_easy_lo_r00_tgd/reference_candidate.json  88ae24a2e0b83abeb6ab82b80382a8828f8f17796eb8ba92ccb00e81993541e4
torre_easy_lo_r00_tgd/input_candidate.json      4df72e97bda56dc5825d07571bda58122a7e4329f99ad0b49669f7a6f94f5af8
torre_easy_lo_r00_tgd/reference_roundtrip.json  73464483286826cfa8b78b337301c71cacacf050db48cab7d83647d4b300bc66
torre_easy_lo_r00_tgd/input_roundtrip.json      d9e1bcb95ce488a2cc9f9bfd4875f6dd94c05d75232b68458817b3e17e907d99
torre_easy_lo_r00_tp1/reference_candidate.json  705503719f20294c5eac1d8433a98a7137c500142cbec358d2c3fa88a9fc3d58
torre_easy_lo_r00_tp1/input_candidate.json      4d1ee239ab9e19e0930d57aea95af05faf336d10cc493c4a6a168f4282403442
torre_easy_lo_r00_tp1/reference_roundtrip.json  6efa88f8f7a8c00efc4d8cc99556cec977bddc7ffb077e93cb9120b1b7df6383
torre_easy_lo_r00_tp1/input_roundtrip.json      c4b630f8202bd16bcf0e6c072569098fd799d5d0ba372d3ad5a4b0f433ddff17
```

**Nada foi regravado para fazer teste passar. Nenhum `skip`, `xfail` ou
threshold foi tocado — nenhum arquivo de teste foi sequer aberto para
edição** (`git diff -- tests` vazio).

### 8.1 O que os invariantes NÃO cobrem

- Não há gate para `JUNCTION_NOT_ALTERNATING` no solver: ele **piora
  +16** (§7.5-B) e nenhum invariante desta CR o proíbe, porque é
  comportamento do solver, não do candidato.
- Não há gate para `expected_rows` depois do corte (§7.5-C).
- Não há gate para R1/R2/R3: elas ficam gravadas com o valor humano.

---

## 9. Plano de integração — proposta, NÃO autorizada

**Nenhum arquivo oficial foi alterado nesta sessão e nada aqui é
autorização.** Este plano só existe se **D1**, **D2** e **D3** forem
decididas explicitamente pelo usuário.

### 9.1 Separação obrigatória em CRs distintas

| CR | escopo | pré-requisito |
|---|---|---|
| **A — reconstrução e versionamento do gabarito** | `reconstruct.py` (segunda passada `C1`), `reference.json` v3 + `stable_key`, `input.json` **só do TP1**, `evaluation_scope.json`, `scope_summary.json`, changelog e tabela de migração de identidade | **D1 + D2 + D3** |
| **B — recalibração de `reference_score`** | `reference_score.json` / `scoped_reference_score.json` recalculados no gabarito novo | sai junto de (A), senão o corpus fica incoerente |
| **C — `baseline refresh`** | `baseline.json` | **CR própria, decisão própria.** Proibido nesta |
| **D — correções reais do solver** | `JUNCTION_NOT_ALTERNATING` +16 nos nós `L` novos; `PRISM_STAGGER_BELOW_TARGET` +101; `COMPENSATOR_AVOIDABLE` +17 | **CRs separadas**, uma por defeito, cada uma com seu STATE_A/B |
| **E — dívida documental** | `PROJECT_STATUS.md` e `bench_opening_reconstruction_a/README.md` | **D6** |

### 9.2 Correção obrigatória ao plano §10.1 da reconciliação

O plano original lista `*/input.json` (os dois projetos). **Medido em
§1.3: o `input.json` do TGD NÃO deriva do gabarito** — é a única fonte
medida independente do corpus (167 paredes, 82 aberturas `measured` de um
documento Revit separado). Regenerá-lo a partir do gabarito destruiria
essa fonte. **Proibido.** Só o `input.json` do TP1 é regerado.

### 9.3 Gates explícitos da CR de integração

| gate | limiar | já medido aqui |
|---|---|---|
| blocos humanos: perdidos / novos / duplicados / órfãos | **= 0** nos quatro | ✔ 0/0/0/0 |
| `z`, centro `XY` e elevação de fiada por bloco | **idênticos** | ✔ 0 divergências |
| comprimento total | `Δ == −Σ(larguras removidas)` | ✔ −2604,0 exato |
| aberturas com `source_element_id` removidas | **= 0** | ✔ 0 |
| aberturas com geometria alterada | **= 0** (fora as 19 removidas) | ✔ 0 |
| `POSITION_OVERLAP` (colisão física) | **Δ ≤ 0** | ✔ 0 no gabarito, −9 no solver |
| determinismo do gerador | `sha256` idêntico em 2 processos novos | ✔ 3 processos |
| ocupação física dos nós alterados | **conjunto idêntico** de peças | ✔ 38/38 |
| **`JUNCTION_NOT_ALTERNATING` do solver** | **decisão explícita** — hoje `+16` | ✔ medido, **não resolvido** |
| **`JUNCTION_MISSING_BINDING` do gabarito** | **decisão explícita** — hoje `+49` com alvenaria idêntica | ✔ medido, **não resolvido** |
| **`expected_rows` após o corte** | **decisão explícita** — `+17`/`+23` de `COVERAGE_*` | ✔ medido, **não resolvido** |
| suíte completa | as **mesmas 2** falhas pré-existentes, sem novas | **não rodada nesta CR** (nenhum arquivo de produção foi tocado) |

**Proibido na CR de integração:** regravar `baseline.json` para esconder
regressão; criar tolerância global; usar `skip`/`xfail`; alterar
threshold; usar a queda de críticos como justificativa de classificação;
mexer em regra de amarração `L`/`T`/`X` sem decisão do usuário.

### 9.4 Critérios de rollback

Reverter se qualquer um ocorrer: bloco humano some ou vira órfão;
abertura `measured` muda de geometria; aparece `POSITION_OVERLAP` novo;
o gerador deixa de ser determinístico; ou a alvenaria humana em qualquer
nó alterado deixa de ser idêntica.

### 9.5 D4 e D6 — resolução apresentada (decisão continua do usuário)

**D4 — R1/R2/R3: conferir no Revit antes de gravar, ou gravar o valor
humano com pendência?**

*Resolução proposta:* **gravar o valor humano e marcar
`needs_revit_check`**, com a conferência de §6.5 como CR curta e
independente, **não** como bloqueio da reconstrução. Fundamento medido:
as três afetam **onde a parede nova termina** (R1: 30,007 cm; R2:
14,458 cm; R3: 192,998 cm), **nunca se ela termina** — as seis jambas
envolvidas estão confirmadas por geometria medida, e nas três o miolo tem
`0` blocos, `0` verga e `0` procedência medida. Bloquear 19 casos × 2
projetos por 3 valores de borda custa mais do que registrar a pendência.

*Ressalva honesta:* isto **presume** que R2 não é parede dupla real. Se
a conferência mostrar que é, a perpendicular `W045` do gabarito está no
eixo errado e **dois** dos 19 casos precisam de nova geometria de jamba —
não de nova classificação. Por isso `needs_revit_check` tem de ser campo
gravado e rastreável, não nota de rodapé.

**Isto NÃO é aprovação presumida.** Se o usuário preferir conferir antes,
a CR de integração espera — o candidato já está pronto e é
determinístico.

**D6 — recuperar os dois documentos de revisão independente, ou corrigir
as citações?**

*Resolução proposta:* **corrigir as citações**, não fabricar os
documentos. Fundamento: §1.2 mostra que eles **nunca existiram em nenhuma
ref** — não há o que recuperar, e regerá-los agora produziria um
documento novo com data de hoje se passando por revisão feita à época,
o que seria pior que a lacuna. O mínimo honesto:

1. Em `docs/PROJECT_STATUS.md`, trocar cada citação por
   `revisão independente CONCLUÍDA, relatório NÃO VERSIONADO (dívida
   documental aberta)`, preservando os vereditos já registrados
   (`APPROVE_WITH_EXPLICIT_CONDITIONS`) como **resumo de segunda mão**.
2. Mesma correção em
   `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_a/README.md` §6.
3. Se o usuário tiver os originais fora do repo, commitá-los **com a
   data original**, e aí a dívida se fecha de verdade.

Isso toca `docs/` e um `README` de evidência — **não** foi feito nesta
sessão, porque o enunciado proíbe alterar arquivos oficiais aqui, e
`PROJECT_STATUS.md` é registro oficial do projeto.

### 9.6 Registro de regra — pendência declarada, não escrita

O `CLAUDE.md` obriga a registrar em `nuvem/REGRAS_MODULACAO_BLOCOS.md`
toda correção de modulação. **Esta CR não alterou o arquivo**, porque o
enunciado proíbe escrever regra normativa aqui e porque a promoção do
critério a regra depende de **D5**. A pendência fica declarada, com o
rótulo de confiança que ela merece:

> **PADRÃO MEDIDO — DOCUMENTADO, pendência de código e de decisão
> aberta (D5).** Um vazio cujas **duas** jambas coincidem com a face
> interna de uma parede perpendicular (reserva de nó nos dois lados) e
> que **não tem verga** não é abertura: é o espaço entre **duas paredes
> que terminam no nó**. As tiras de ~15 cm de cada lado são a pegada da
> perpendicular, não vão a preencher.
> **Evidência acrescentada por esta CR:** nos 38 nós por projeto cujo
> tipo muda com o corte, a alvenaria humana é **byte-idêntica** — 11 a 13
> fiadas com `B34`/`B54` alternando entre hospedeiro e perpendicular
> (`void_occupancy` + ocupação física medida em
> `analyze_junctions.py`). Nenhuma amarração humana é criada ou destruída
> pela reclassificação.
> **Não promover a regra geral sem D5** — dois níveis do mesmo edifício
> não são amostra suficiente.

---

## 10. Riscos remanescentes

1. **`JUNCTION_NOT_ALTERNATING` +16 no solver** (§7.5-B). Amarração é o
   núcleo do sistema. O candidato **expõe** o defeito; não o cria e não o
   corrige. Sem CR própria, integrar a CR-B piora a amarração medida.
2. **`JUNCTION_MISSING_BINDING` +49 no gabarito com alvenaria idêntica**
   (§7.5-C). Pode ser mudança de unidade de avaliação, pode ser crédito
   de nó sensível a `T`/`L`. **Não investigado** — decisão explícita
   necessária.
3. **Migração de identidade.** 53/86 e 52/85 paredes inalteradas mudam de
   `W0xx`. Sem `stable_key` gravado, toda métrica histórica por parede
   morre em silêncio.
4. **Re-indexação ordinal de fiada** em 184 blocos por projeto (§4.3).
   Diagnósticos chaveados por `(wall_id, row)` deixam de casar.
5. **TP1 sem fonte medida independente.** A confiança continua
   MÉDIA-ALTA. A evidência que falta tem nome: extração dos eixos e
   aberturas nativas do nível `05. TP1`.
6. **`C1` validado em 148 trechos de controle de dois níveis do mesmo
   edifício.** Não é prova universal. **D5** aberta.
7. **R1, R2, R3 não resolvidas** (§6). O candidato grava o valor humano.
8. **Dívida documental** (§1.2): dois documentos citados como autoridade
   nunca existiram. **D6** aberta.
9. **`expected_rows` global** contra paredes cortadas (§7.5-C).
10. A família de **0,11–0,12 cm** de coordenada fracionária continua
    aberta; a aceitação de **0,06 cm** da CR-A continua restrita aos 4
    casos daquela CR. Esta CR **não** criou nenhuma tolerância nova — a
    única tolerância usada (1,0 cm) é de **classificação** e não produz
    coordenada gravada.

---

## 11. Estado das decisões D1–D6

| # | decisão | estado ao fim desta CR |
|---|---|---|
| **D1** | os 19 do TGD são duas paredes separadas? | **evidência reforçada** (invariantes, T→L, projeção). **Não decidida** |
| **D2** | os 19 do TP1 acompanham? | pareamento remedido 19/19 a **0,0004 cm**; confiança **MÉDIA-ALTA** mantida. **Não decidida** |
| **D3** | autoriza alterar o gabarito, aceitando a perda de comparabilidade absoluta e a migração de `W0xx`? | custo **quantificado** (§4.4, §7). **Não decidida** |
| **D4** | R1/R2/R3: conferir no Revit ou gravar o valor humano? | **resolução proposta** em §9.5 (gravar humano + `needs_revit_check` + CR curta de conferência com §6.5). **Não decidida** |
| **D5** | `C1` vira regra de domínio? | **recomendação: NÃO** por enquanto — segue heurística de extração deste corpus. **Não decidida** |
| **D6** | recuperar os dois documentos ou corrigir as citações? | **resolução proposta** em §9.5 (corrigir as citações; não fabricar). **Não decidida** |

**Nenhuma aprovação foi presumida. Nenhum arquivo oficial foi alterado.
Nenhum merge, nenhum PR de produção. C02/C10/Junction/S1/S2 não
iniciadas.**

---

## 12. Limitações declaradas

1. **Nenhuma medição no Revit ao vivo (MCP)** nesta sessão. Toda a fonte
   (A) vem do `input.json` do TGD já commitado.
2. **A revisão independente da CR-A continua ilegível** — nunca existiu.
3. A **suíte de testes completa não foi rodada**: nenhum arquivo de
   produção ou de teste foi tocado, então não há o que ela pudesse
   detectar desta CR. Ela é gate da CR de integração, não desta.
4. A projeção do solver do **TGD** com entrada derivada do gabarito
   (§7.3) é **hipotética** — serve de controle, não de previsão do que
   aconteceria em produção, porque o TGD não deriva a entrada do gabarito.
5. O candidato **não** foi avaliado com `evaluation_scope` recalculado —
   §7 usa o pareamento direto. O escopo recalculado é trabalho da CR de
   integração.
6. O `piloto_sintetico_2x2` não tem trecho detectável e ficou fora, como
   na reconciliação.
7. `coverage_pct` sai `None` em todas as execuções — o campo não é
   preenchido por este caminho de avaliação; a cobertura foi lida pelos
   códigos `COVERAGE_*`, que são os que os hard gates usam.
