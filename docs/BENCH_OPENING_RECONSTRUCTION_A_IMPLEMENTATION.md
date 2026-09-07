# CR-BENCH-OPENING-RECONSTRUCTION-A — correção do detector de aberturas

> **Escopo: PRODUÇÃO, um único arquivo.** `nuvem/core/engine/opening_audit.py`.
>
> **Gabarito INTOCADO.** `baseline.json`, `reference.json`,
> `reference_score.json`, `input.json` e `nuvem/REGRAS_MODULACAO_BLOCOS.md`
> **não** foram alterados — verificado por `git diff --name-only`.
>
> **NÃO MERGEAR** sem autorização explícita do usuário para este merge.

| item | valor |
|---|---|
| base obrigatória | `3f293d1433e8c16eb186959e33a345b60ac944f9` (= `origin/main`, conferido) |
| branch | `claude/opening-detector-root-fix-m21hfm` |
| diff de produção | `nuvem/core/engine/opening_audit.py` (**1 arquivo**) |
| fonte diagnóstica | `claude/pr20-integration-readiness-ec5xk1` @ `4654898` |
| CR seguinte (gabarito) | `BENCH-OPENING-RECONSTRUCTION-B` — **não iniciada**, §9 |

---

## 1. Causa-raiz — confirmada no código real, não citada

`detect_wall_openings_from_courses` respondia **duas perguntas diferentes com
o mesmo número**:

```python
if (abs(gs2 - run_start) <= OPENING_RUN_EDGE_MATCH_TOLERANCE_CM      # 15,0cm
        and abs(ge2 - run_end) <= OPENING_RUN_EDGE_MATCH_TOLERANCE_CM):
    ...
run_start = min(run_start, gs2)      # <-- UNIÃO (envelope)
run_end   = max(run_end,  ge2)       # <-- UNIÃO (envelope)
```

A tolerância existe para decidir **identidade** — "o vazio desta fiada é a
*mesma* abertura do vazio da fiada anterior?", absorvendo o desencontro de
junta entre fiadas (seção 10.6 das regras). O defeito está na linha
seguinte: a **geometria gravada** virava o **envelope** (união) dos vazios de
todas as fiadas do trecho. Assim a tolerância de identidade passava direto
para a largura do vão.

Onde a jamba coincide com um nó T/L, as fiadas alternam entre "reserva de nó
vazia" e "peça de amarração atravessa o nó" — diferença de exatamente
`B34 − B19 = 34 − 19 = 15,0cm`.

### 1.1 A primeira divergência, medida no corpus

`repro_envelope.py` replica o agrupamento do `STATE_A` linha a linha e
registra **todos** os vazios de fiada que entraram em cada trecho. Rodado
sobre o gabarito humano congelado (`reference.json`):

| | TGD | TP1 |
|---|---|---|
| trechos detectados | 94 | 92 |
| com desacordo entre fiadas | 31 | 31 |
| com a assinatura `≈15,0cm` nas **duas** jambas | **19** | **19** |
| desacordo máximo observado | 15,0cm | 15,0cm |
| consenso abaixo de `OPENING_GAP_MIN_CM` | **0** | **0** |
| consenso invertido | **0** | **0** |

`W003` do TGD, fiada a fiada (medido, não hipótese):

```
fiada  0  ...  C09 570–579          <- reserva de nó VAZIA nesta fiada
fiada  1  ...  B34 560–594          <- peça de amarração ATRAVESSA o nó
fiada  2  ...  C09 570–579
fiada  3  ...  B34 560–594
                   ^^^ 594 − 579 = 15,0cm = B34 − B19

envelope (STATE_A, gravado) : [579, 765]  = 186,0cm
consenso (STATE_B, gravado) : [594, 750]  = 156,0cm
```

Rodando o mesmo teste de invasão que o validador `OPENING_BLOCK_CROSSES_JAMB`
faz, sobre o vão do `STATE_A`:

```
peca BLOCO 34 - 14x19x34 [560.0,594.0] da fiada z=20.0
    invade o vao gravado [579.0,765.0]
```

Isto é: **o vão gravado declarava vazio um ponto onde a fiada tinha peça.**

### 1.2 Duas consequências que o envelope produzia e ninguém tinha medido

1. **Largura fora do próprio domínio do módulo.** `W052` do TGD: cada vazio
   de fiada cabe em `OPENING_GAP_MAX_CM = 260,0cm`, mas o envelope gravou
   **266,0cm** — uma abertura que o próprio detector teria recusado como
   "outra parede". O consenso grava 236,0cm.
2. **Larguras que não existem no Revit.** No `input.json` **medido** do TGD
   (82 aberturas `confidence="measured"`, com `source_element_id`), as
   larguras 186,0cm e 131,0cm aparecem **0 vez**; 101,0cm aparece. E
   `186 − 2×15 = 156`, `131 − 2×15 = 101`.

---

## 2. A correção — mínima, um arquivo

O agrupamento (**identidade**) **não mudou uma linha**: o casamento de borda
continua sendo feito contra o envelope corrente do trecho, com a mesma
tolerância de 15,0cm. Portanto **nenhum trecho muda de composição, nenhuma
abertura aparece ou some**.

O que mudou é só a resposta à **segunda** pergunta:

```python
consensus_start = max(gap_starts)   # a borda que TODA fiada respeita
consensus_end   = min(gap_ends)
```

e o desacordo passa a ser **dado gravado**, não arredondamento silencioso:

| campo novo | o que é |
|---|---|
| `x_range` | **consenso** — a geometria física do vão (era o envelope) |
| `x_range_envelope` | o envelope antigo, preservado para diagnóstico |
| `jamb_spread_start_cm` / `jamb_spread_end_cm` | desacordo medido, por jamba |
| `jamb_spread_cm` | o maior dos dois |
| `opening_provenance` | `RECONSTRUCTED_CONSENSUS` ou `INCONCLUSIVE` |

Vocabulário de proveniência exportado (`__all__`), para os dois lados da
fronteira: `MEASURED`, `RECONSTRUCTED_CONSENSUS`, `RECONSTRUCTED_ENVELOPE`
(legado, rotulável mas não mais emitido) e `INCONCLUSIVE`.

### 2.1 Invariante que a correção passa a garantir

> `x_range` está contido em **todos** os vazios de fiada do trecho.

O detector nunca mais declara vazio um ponto onde alguma fiada tem peça —
testado no reproducer sintético **e** no corpus inteiro dos dois projetos
reais.

### 2.2 O ramo `INCONCLUSIVE` — o que ele NÃO faz

Quando `min(fins) − max(inícios)` cai abaixo de `OPENING_GAP_MIN_CM`, não
existe consenso válido. A função **não** volta ao envelope (era exatamente o
defeito) e **não** apaga a abertura: grava o consenso não-invertido e marca
`INCONCLUSIVE`, deixando a decisão para quem consome.

Com as constantes de hoje esse ramo é **inalcançável** no domínio real, e
isso é demonstrável, não empírico:

```
toda borda observada fica a no máximo TOL do envelope corrente
todo vazio de fiada tem no mínimo GAP_MIN de largura
  =>  consenso >= GAP_MIN - 2*TOL = 50,0 - 30,0 = 20,0cm > 0
```

Coerente com a medição: **0 ocorrências** em TGD e TP1. O grampo existe para
o dia em que uma dessas duas constantes mudar, e tem teste próprio (que
rebaixa `GAP_MIN` só dentro do teste).

### 2.3 O que a CR-A deliberadamente NÃO fez

- **Não estreitou vãos por atacado.** Onde as fiadas concordam, envelope ==
  consenso e a geometria é byte-idêntica (63 de 94 no TGD, 61 de 92 no TP1).
- **Não transformou dois trechos de parede em uma parede com abertura**, nem
  o contrário. `WALL_SPLIT_GAP_CM` / `OPENING_GAP_MAX_CM` e
  `nuvem/benchmark/extract/reconstruct.py` **não** foram tocados (§9).
- **Não mexeu em abertura medida.** O detector só reconstrói; abertura com
  `source_element_id` não passa por ele.
- **Não propagou proveniência para o gabarito.** Isso muda o schema de
  `reference.json` e é CR-B.
- **Não alterou `nuvem/REGRAS_MODULACAO_BLOCOS.md`** — proibido nesta CR
  pelo enunciado. Ver §10: há registro pendente.

---

## 3. STATE_A → STATE_B — nível DETECTOR

`state_detector.py` roda o detector sobre a geometria real do gabarito
humano dos 3 projetos. Comparação por **identidade geométrica estável**
`(wall, z_range, n_courses, ENVELOPE)` — o envelope é o que não muda com a
correção, então serve de chave; `block_id` sequencial **não** foi usado.

| | TGD | TP1 |
|---|---|---|
| aberturas `STATE_A` → `STATE_B` | 94 → **94** | 92 → **92** |
| só em A / só em B | **0 / 0** | **0 / 0** |
| geometria alterada | 31 | 31 |
| **alargadas** | **0** | **0** |
| estreitadas | 31 | 31 |
| contida no envelope antigo | **sim** | **sim** |
| proveniência resultante | `CONSENSUS` 94 | `CONSENSUS` 92 |

Redução de largura, por família (cm → nº de aberturas):

| redução | TGD | TP1 | o que é |
|---|---|---|---|
| **30,00** | 17 | 17 | assinatura `B34 − B19` nas duas jambas |
| **29,99** | 2 | 2 | idem, com 14,99cm de um lado |
| 0,23 / 0,12 | 1 / 1 | — / 3 | família de coordenada fracionária (§5) |
| 0,02 / 0,01 | 1 / 9 | 1 / 8 | idem |

Larguras: `186,0 → 156,0` (10 aberturas por projeto), `131,0 → 101,0` (10),
`266,0 → 236,0` (1). **101,0cm é largura medida real no Revit; 186,0 e
131,0 não existem lá.**

`jamb_spread_cm` gravado no `STATE_B` — o desacordo deixou de ser apagado:

| spread | TGD | TP1 |
|---|---|---|
| 0,0 | 63 | 61 |
| 0,01–0,12 | 12 | 12 |
| **15,0** | **19** | **19** |

---

## 4. STATE_A → STATE_B — nível SOLVER (o resultado que importa)

Rodada completa dos **3 projetos**, `runner.run_project`, sem escrita em
`projects/` nem em `reports/`:

| projeto | fingerprint A | fingerprint B | peças | críticos | achados só em A / só em B |
|---|---|---|---|---|---|
| `piloto_sintetico_2x2` | `b7f14bc3baa7` | `b7f14bc3baa7` | 772 → 772 | 8 → 8 | 0 / 0 |
| `torre_easy_lo_r00_tgd` | `e81973ab2447` | `e81973ab2447` | 11731 → 11731 | 872 → 872 | 0 / 0 |
| `torre_easy_lo_r00_tp1` | `27d61b5c2e7b` | `27d61b5c2e7b` | 19572 → 19572 | 485 → 485 | 0 / 0 |

**Delta ZERO em tudo:** fingerprint físico, score inteiro, e o conjunto de
achados comparado por identidade `(code, wall, detail)` — não por contagem.

Os números do `STATE_A` conferem, peça a peça, com o `STATE_C` do PR #20
(TGD 11731 blocos / 872 críticos; TP1 19572 / 485): o ambiente reproduz a
`main` pós-C04 exatamente.

### 4.1 Por que zero, e por que isso é o resultado correto

O detector tem **dois** consumidores:

| consumidor | quando roda | efeito da CR-A |
|---|---|---|
| `nuvem/benchmark/extract/reconstruct.py:411` | só na **extração** do gabarito | vale na próxima extração — **CR-B** |
| `nuvem/core/wall_modeling.py:2259` (`audit_existing_masonry_openings`) | auditoria de alvenaria **já construída** no Revit | vale **já**, no relatório ao vivo |

O solver dos 3 projetos lê `input.json` **congelado**, e não chama o
detector. Portanto delta zero era o resultado esperado — e é o que garante
que **nenhum defeito real do solver foi apagado por esta CR**. O ganho de
métrica não pode ser reivindicado aqui: ele depende da CR-B.

**Hard gates do C04, NODE-FILL, ARM e B19 preservados por construção**:
delta zero em todos os achados implica delta zero em `OPENING_BLOCK_CROSSES_
JAMB`, `POSITION_OVERLAP`, `JUNCTION_*`, `COVERAGE_*`, `PRISM_*`,
`COMPENSATOR_*`. **C1 e C2 continuam dívidas conhecidas do PR #20, não
resolvidas e não agravadas** (compensadores do TGD e saldo crítico do TP1
idênticos ao `STATE_A`).

### 4.2 Projeção medida do efeito no solver — o que a CR-B destravaria

Delta zero hoje **não** quer dizer que a correção é inócua: quer dizer que
ela está bloqueada pelo gabarito congelado. Para medir o efeito real sem
aplicar nada, `projection_experiment.py` copia o TP1 para um diretório
temporário e reescreve **só** as bordas das aberturas já existentes do
`input.json` com o consenso que o **detector corrigido** calcula sobre a
geometria do `reference.json`. Nenhuma abertura é criada, apagada ou movida
de parede; nenhuma parede é dividida; **nenhum arquivo oficial é tocado**.

Só o TP1 entra: o `input.json` do TGD carrega 82 aberturas `measured` do
Revit, e **abertura medida é preservada** (a regra é verificada no próprio
script — `medidas preservadas` seria > 0 se houvesse).

```
aberturas alteradas=31  inalteradas=61  medidas preservadas=0  sem par=0
OFICIAL    fingerprint=27d61b5c2e7b  pecas=19572  criticos=485
PROJETADO  fingerprint=081e5e4696eb  pecas=19286  criticos=327
```

| código | oficial | projetado | delta |
|---|---|---|---|
| `OPENING_BLOCK_CROSSES_JAMB` | 168 | **0** | **−168** |
| `PRISM_STAGGER_BELOW_TARGET` | 1506 | 1444 | −62 |
| `COMPENSATOR_CONSECUTIVE` | 1480 | 1466 | −14 |
| `COMPENSATOR_EXCESS_IN_RUN` | 1135 | 1128 | −7 |
| `PRISM_CONTINUOUS_JOINT` | 290 | 286 | −4 |
| `COMPENSATOR_VERTICAL_STRIP` | 190 | 187 | −3 |
| `COVERAGE_GAP_IN_ROW` | 214 | **304** | **+90** |
| `COVERAGE_ROW_MOSTLY_EMPTY` | 0 | **14** | **+14** |
| **críticos** | **485** | **327** | **−158** |

**As 168 invasões de jamba do TP1 são 100% consequência da abertura
inflada** — somem inteiras quando o vão recebe a largura de consenso.

E **isso não é de graça, que é a parte importante:** a cobertura piora
(+90/+14), porque as tiras de 15,0cm da reserva de nó deixam de ser
"abertura" e passam a ser parede a preencher — e 15cm não comporta nem um
B19 (19cm). **Estreitar o vão troca um artefato por outro, menor. Não fecha
a conta.** É por isso que a leitura provável ("ali não há parede, são dois
trechos separados") é decisão de gabarito, e é da CR-B (§9).

> **Reprodução independente.** Estes números foram obtidos nesta sessão,
> sobre a base pós-C04, aplicando o **detector corrigido** — e não o
> candidato editado à mão da branch diagnóstica. Conferem com o que ela
> relatou (`168 → 0`, **−158** críticos, `+90` / `+14` de cobertura,
> `−62` de stagger), a partir de um caminho diferente. Isso **valida a
> medição**; não é aprovação da leitura de domínio.

> **A redução de `CROSS_JAMB` não vem de redefinir o vão.** Cada jamba
> gravada é uma borda de vazio **observada** em alguma fiada (teste
> `test_no_TL_na_jamba_a_borda_gravada_e_uma_borda_OBSERVADA`), e o vão
> gravado não contém peça de fiada nenhuma no corpus inteiro (teste
> `test_corpus_vao_gravado_nao_contem_peca_de_nenhuma_fiada`).

---

---

## 5. Caso humano que a CR-A NÃO resolve — a família de 0,11–0,12cm

13 aberturas no TGD e 14 no TP1 têm desacordo de 0,01 a 0,23cm, vindo de
coordenada fracionária na extração (jamba em `18,88` contra peça em
`19,00`), logo acima do `OVERLAP_TOLERANCE_CM = 0,1cm` do validador.

A CR-A **estreita também essas**, porque o consenso não tem exceção por
tamanho — e isso desloca o centro de 3 aberturas em **0,06cm** (0,6mm), e de
outras 11 em ≤ 0,01cm.

> **Desvio de hard gate declarado, não escondido.** O gate pedia centro
> preservado com deslocamento < 0,01cm "salvo evidência medida em
> contrário". Aqui há evidência medida: o deslocamento vem de coordenada de
> peça realmente presente no corpus, e está gravado em `jamb_spread_cm`.
> Nenhuma tolerância participa. Ainda assim, 0,06cm > 0,01cm: **é desvio, e
> está sendo apresentado como desvio.**

A alternativa seria um piso de ruído ("abaixo de X, mantenha o envelope") —
que é literalmente o defeito outra vez, só que menor. Foi recusada.

A causa dessa família é a **extração**, não o detector, e continua aberta.

---

## 6. Testes — `tests/test_opening_reconstruction_cr_a.py`

44 testes, exercitando a função de produção pelo mesmo caminho do motor
(`load_script.load()` → `wall_modeling` → `from core.engine.opening_audit
import *`).

```
STATE_A (motor sem a correção):  37 failed, 7 passed
STATE_B (motor com a correção):  44 passed
```

A suíte foi escrita para **coletar nos dois estados** (as constantes novas
entram por `getattr` com padrão), de modo que as falhas do `STATE_A` sejam
de **comportamento** — geometria gravada — e não um `ImportError` que não
prova nada. A falha canônica no `STATE_A`:

```
AssertionError: peca BLOCO 34 - 14x19x34 [560.0,594.0] da fiada z=20.0
    invade o vao gravado [579.0,765.0]
```

Cobertura pedida pela CR:

| exigência | teste |
|---|---|
| abertura real com jamba exata | `test_abertura_real_com_jamba_exata_permanece_identica` |
| nó T/L na jamba + alternância de fiadas | `test_no_TL_na_jamba_grava_o_vao_fisico_e_nao_o_envelope` |
| **ausência de invasão física** | `test_no_TL_na_jamba_nenhuma_peca_medida_invade_o_vao_gravado`, `test_corpus_vao_gravado_nao_contem_peca_de_nenhuma_fiada` |
| **redução não é vão redefinido** | `test_no_TL_na_jamba_a_borda_gravada_e_uma_borda_OBSERVADA` — cada jamba gravada tem de ser uma borda **medida** em alguma fiada |
| desencontros de 0 a 14,9cm | `test_tolerancia_de_identidade_nao_desloca_a_borda_gravada` (11 casos: 0 · 0,01 · 0,12 · 1 · 5 · 7,5 · 10 · 14 · 14,89 · 14,9 · 14,99) |
| a tolerância continua decidindo identidade | `test_desencontro_acima_da_tolerancia_nao_forma_um_unico_trecho` |
| desacordo registrado | `test_desacordo_entre_fiadas_e_gravado_nas_duas_bordas` |
| paredes separadas com espaço entre elas | `test_espaco_grande_demais_continua_nao_sendo_abertura`, `test_dois_trechos_separados_nao_ganham_abertura_por_consenso`, `test_vao_gravado_nunca_ultrapassa_OPENING_GAP_MAX_CM` |
| abertura medida × reconstruída | `test_detector_nunca_declara_abertura_MEASURED`, `test_vocabulario_de_proveniencia_exportado` |
| determinismo | `test_determinismo_repeticao_e_ordem_de_entrada`, `test_corpus_determinismo_em_duas_passadas` |
| translação / rotação / espelho / reversão | `test_invariancia_a_translacao_do_eixo` (5 casos), `test_invariancia_a_reversao_do_eixo`, `test_invariancia_a_espelho_da_ordem_das_fiadas` |
| regressão das 19 aberturas do corpus | `test_corpus_assinatura_de_15cm_some_e_o_desacordo_fica_registrado` |
| nenhuma abertura alargada / criada / apagada | `test_corpus_nenhuma_abertura_alargada_nem_fora_do_envelope` |

> **Nota de aplicabilidade.** O detector trabalha em coordenada **axial 1-D**
> (`t_cm` ao longo da parede). Rotação no plano e espelhamento da parede se
> reduzem, nesse domínio, a translação e reversão do eixo — que são o que os
> testes exercitam. Rotação 2-D não tem efeito próprio a testar aqui.

---

## 7. Determinismo

| verificação | resultado |
|---|---|
| detector, 5 repetições no mesmo processo | saída idêntica |
| detector, entrada com fiadas em ordem invertida | saída idêntica (a função ordena por `z`) |
| detector, 2 passadas sobre o corpus | idêntico |
| detector, 2 processos novos (TGD + TP1) | idêntico |
| solver, `STATE_A` e `STATE_B` em processos separados | fingerprints idênticos nos 3 projetos |

---

## 8. Classificação do efeito medido — por família, não em bloco

| família | n (por projeto) | classificação | base |
|---|---|---|---|
| 19 aberturas com assinatura `≈15,0cm` | 19 | **DEFEITO REAL CORRIGIDO** | união provada no código (§1); peça medida invadindo o vão gravado (§1.1); largura 186/131 inexistente no Revit medido (§1.2) |
| `W052` do TGD, envelope 266 > `GAP_MAX` 260 | 1 | **DEFEITO REAL CORRIGIDO** | o vão gravado violava o limite de domínio do próprio módulo |
| 12–13 aberturas de 0,01–0,23cm | 12–13 | **MUDANÇA LEGÍTIMA, com desvio declarado** | consenso correto, mas a causa é a extração; centro desloca até 0,06cm (§5) |
| 63 / 61 aberturas sem desacordo | 63 / 61 | **INALTERADAS** | envelope == consenso |
| solver dos 3 projetos | — | **ARTEFATO DE BENCHMARK: nenhum** | delta zero; nada foi apagado nem introduzido (§4) |
| leitura "abertura estreita" × "duas paredes separadas" | 19 | **INCONCLUSIVO — decisão da CR-B** | §9 |
| C1 (compensadores TGD) e C2 (saldo crítico TP1) | — | **DÍVIDAS CONHECIDAS, intactas** | idênticas ao `STATE_A` |

**Nenhuma regressão física nova.**

---

## 9. Onde a CR-A parou — e o que fica para a CR-B

A evidência aponta que, em boa parte dos 19 casos, aquilo **não é uma porta**:
é o espaço entre **duas paredes fisicamente separadas** que a reconstrução
fundiu numa parede só (`WALL_SPLIT_GAP_CM = OPENING_GAP_MAX_CM = 260cm` faz
um vão de 156cm caber abaixo do teto e virar "abertura").

Confrontando o consenso com os trechos de parede **medidos** no mesmo eixo
do `input.json` do TGD, re-derivado nesta sessão (`repro_axis_gap.py`,
independente da branch diagnóstica):

```
W003  env=[579,765]  cons=[594,750]  == BURACO MEDIDO [594.0,750.0] entre W017 e W015
W005  env=[309,440]  cons=[324,425]  == BURACO MEDIDO [324.3,425.0] entre W042 e W081
W046  env=[94,280]   cons=[109,265]  == BURACO MEDIDO [109.0,265.0] entre W104 e W102
...
>> consenso == buraco entre paredes MEDIDAS: 10 | divergente: 9 | sem geometria medida: 0
```

> **Honestidade de método:** a re-derivação desta sessão usa um agrupamento
> de eixo mais grosseiro que o da branch diagnóstica (que reporta **16 de
> 19**). Onde os dois divergem, a diferença é de método, não de conclusão:
> em ambos os casos a maioria dos consensos coincide **exatamente** com um
> buraco entre duas paredes medidas. **Nenhum dos dois números foi tratado
> como aprovação automática.**

**Isso é ampliação de escopo, e a CR-A parou aqui.** Separar uma parede em
duas muda `reference.json`/`input.json`, muda `evaluation_scope`, muda toda
métrica por parede e muda o pareamento humano. Exige:

1. autorização explícita para alterar o gabarito;
2. decisão de domínio: para os 19 casos, vale **abertura estreita** ou
   **duas paredes separadas**? (a evidência medida do TGD aponta para a
   segunda);
3. decisão sobre os casos do TP1, que **não têm fonte medida** e hoje são
   adjudicados só por analogia com o TGD.

Arquivos que a CR-B teria de tocar, e que a CR-A **não** tocou:
`nuvem/benchmark/extract/reconstruct.py` (propagação de `opening_provenance`
e `jamb_spread_cm` para o gabarito, `WALL_SPLIT_GAP_CM`),
`nuvem/benchmark/projects/*/reference.json`, `*/input.json`,
`*/reference_score.json`.

### 9.1 Pré-requisito técnico já entregue pela CR-A

A CR-B precisa de proveniência por abertura para versionar o gabarito. O
detector agora **produz** essa informação (`opening_provenance`,
`jamb_spread_cm`, `x_range_envelope`); falta só o consumidor gravá-la — o
que é mudança de schema, e por isso é da CR-B.

---

## 10. Registro de regra — PENDÊNCIA DECLARADA

O `CLAUDE.md` deste projeto exige que toda correção de modulação seja
registrada em `nuvem/REGRAS_MODULACAO_BLOCOS.md`. O enunciado desta CR
**proíbe** alterar esse arquivo. Conforme a própria regra de precedência
("a orientação mais recente do usuário tem prioridade"), o arquivo **não**
foi tocado — e a pendência fica registrada aqui, explícita:

> **PENDENTE DE REGISTRO em `nuvem/REGRAS_MODULACAO_BLOCOS.md`** (seção 10,
> perto de 10.6): *a tolerância de desencontro de junta entre fiadas
> (`OPENING_RUN_EDGE_MATCH_TOLERANCE_CM`, ~15cm, medida como `B34 − B19`)
> decide **identidade** de abertura entre fiadas e **nunca** a geometria da
> jamba; a borda gravada é o **consenso** entre as fiadas, e o desacordo é
> registrado (`jamb_spread_cm`), não absorvido.*
> Rótulo sugerido: **REGRA OBRIGATÓRIA — implementada nesta CR**.
> Como foi descoberto: medição no gabarito humano congelado dos dois
> projetos reais (19 aberturas por projeto com desacordo de exatamente
> 15,0cm nas duas jambas), mais reprodução da primeira divergência no
> código.

Também **não** foi alterado nada em 10.6 (o valor de ~15cm continua
`PADRÃO OBSERVADO AINDA NÃO CONFIRMADO`); esta CR não promove esse número a
constante de domínio — ela apenas impede que ele decida geometria.

---

## 11. Limitações declaradas

1. **O ganho de métrica não é desta CR.** No corpus atual o solver não muda
   (§4). O efeito só aparece quando o gabarito for regerado — CR-B.
2. **A família de 0,11–0,12cm não foi resolvida** e a CR-A a desloca em até
   0,06cm (§5). A causa é a extração (coordenada fracionária), não o
   detector.
3. **O TP1 não tem geometria medida**: os 19 casos dele seguem adjudicados
   por analogia com o TGD.
4. **Nenhuma medição no Revit ao vivo (MCP)** foi feita nesta sessão.
5. **`piloto_sintetico_2x2` não tem abertura detectável** pelo detector
   (0 trechos) — entra só como controle de fingerprint do solver.
6. **A criação de trechos (identidade) não foi endurecida.** O envelope
   ainda pode "andar" ao longo das fiadas (deriva de identidade). Como a
   geometria agora é consenso, essa deriva não desloca mais o vão gravado —
   mas ela existe, e endurecê-la mudaria a composição dos trechos, o que
   estaria fora do escopo mínimo desta CR.

---

## 12. Validação — suíte completa, sem maquiagem

### 12.1 Testes focados

```
tests/test_opening_reconstruction_cr_a.py     44 passed   (1,2s)
```

### 12.2 Suíte completa (`python3 -m pytest -q`, raiz do repositório)

```
2 failed, 871 passed in 2204.25s (0:36:44)
```

> **A suíte NÃO está verde, e não será descrita como tal.**

As duas falhas:

| falha | classificação |
|---|---|
| `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tgd]` — `compensators` 52 → 61 | **PRÉ-EXISTENTE — dívida C1 do PR #20** (regressão causada pelo C04, aceita como pendência de decisão do usuário) |
| `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]` — `JUNCTION_MISSING_BINDING` 8 → 9 | **PRÉ-EXISTENTE — `REAL_SOLVER_DEFECT`, documentado em C5 do PR #20** |

**Prova de que nenhuma das duas é da CR-A, e não por citação:** o `score`
do solver é **byte-idêntico** entre `STATE_A` e `STATE_B` nos 3 projetos
(§4). O teste de baseline compara exatamente esse `score` contra
`baseline.json`. Score idêntico ⇒ resultado do teste idêntico. A CR-A não
pode ter introduzido nem agravado nenhuma das duas.

### 12.3 O que NÃO foi feito para passar

| | |
|---|---|
| threshold alterado | **não** |
| `skip` / `xfail` adicionado | **não** |
| teste removido, pulado ou enfraquecido | **não** |
| `baseline.json` regravado | **não** |
| `reference.json` / `reference_score.json` / `input.json` alterados | **não** |
| `nuvem/REGRAS_MODULACAO_BLOCOS.md` alterado | **não** |
| resultado do solver usado como gabarito humano | **não** |

Conferido por `git diff --name-only`: o único arquivo de produção alterado é
`nuvem/core/engine/opening_audit.py`.

---

## 13. Proposta da CR-B — `BENCH-OPENING-RECONSTRUCTION-B`

> **Não iniciada.** Depende de decisão humana explícita. Descrita aqui só
> para que a decisão possa ser tomada com a evidência à mão.

### 13.1 A pergunta, sem jargão

Em 19 lugares por projeto, o desenho de referência diz que existe uma
**porta larga** (186cm ou 131cm). A geometria medida no Revit diz outra
coisa: ali não há porta nenhuma — há **duas paredes separadas**, com um
espaço de 156cm (ou 101cm) entre elas. As larguras 186cm e 131cm **não
existem** no modelo real; 101cm existe.

Hoje o programa trata esse espaço como "buraco numa parede só". Por isso ele
tenta preencher as tiras de 15cm da reserva de nó, e por isso a peça de
amarração parece estar "invadindo a porta".

### 13.2 As opções

| | o que significa | custo |
|---|---|---|
| **A — abertura estreita** | manter uma parede só, com o vão do consenso (156 / 101cm) | mede-se agora: `−168` invasões de jamba e `−158` críticos no TP1, mas `+90` / `+14` de cobertura (as tiras de 15cm viram parede a preencher, e 15cm não comporta nem um B19) |
| **B — duas paredes separadas** | reconstruir dois trechos, sem abertura entre eles | é o que a geometria medida do TGD indica na maioria dos casos; as tiras de 15cm deixam de ser cobertura devida e o `+90` / `+14` some sozinho. Mas muda a estrutura do gabarito (uma parede vira duas), muda `evaluation_scope`, o pareamento humano e **toda métrica por parede** |
| **C — não decidir agora** | manter o gabarito como está | as métricas de abertura continuam inutilizáveis em valor absoluto (o gabarito viola `OPENING_BLOCK_CROSSES_JAMB` 208/209 vezes) |

**Nenhuma foi escolhida.** A evidência medida aponta para **B**; a decisão é
do usuário e precisa ser explícita.

### 13.3 O que a CR-B teria de entregar

1. autorização explícita para alterar gabarito, e aceitação de que **as
   métricas históricas deixam de ser comparáveis em valor absoluto**;
2. resposta para os 19 casos: **abertura estreita** ou **duas paredes**;
3. decisão sobre o TP1, que **não tem fonte medida** (hoje adjudicado só por
   analogia com o TGD);
4. `reference.json` com `schema_version` incrementado, changelog por
   abertura, e `opening_provenance` / `jamb_spread_cm` gravados (o detector
   já produz — §9.1);
5. `reference_score.json` recalibrado **na mesma CR**;
6. `baseline.json` **não** regravado (fica para `BENCH-BASELINE-REFRESH`,
   com decisão própria);
7. gabarito antigo mantido lado a lado por pelo menos uma CR.

---

## 14. Estado da entrega

| | |
|---|---|
| diff de produção | 1 arquivo (`nuvem/core/engine/opening_audit.py`) |
| testes novos | `tests/test_opening_reconstruction_cr_a.py` — 44, falham antes / passam depois |
| evidência reproduzível | `nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_a/` |
| gabarito | **intocado** |
| hard gates C04 / NODE-FILL / ARM / B19 | **preservados** (delta zero no solver) |
| C1 / C2 | **dívidas conhecidas, intactas** — não resolvidas, não agravadas |
| suíte completa | **2 failed, 871 passed** — as 2 são pré-existentes (§12.2) |
| merge | **NÃO AUTORIZADO** — PR draft, sem merge |
| CR-B, C02, C10, Junction, S1/S2 | **não iniciadas** |
