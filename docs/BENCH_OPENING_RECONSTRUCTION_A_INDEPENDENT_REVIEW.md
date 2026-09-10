# Revisão independente — PR #22 (CR-BENCH-OPENING-RECONSTRUCTION-A)

> **Revisão apenas. Nenhum código de produção foi alterado nesta sessão.**
> Feita em worktree isolado, sem tocar na branch do PR.

| item | valor |
|---|---|
| repositório | `Arcanjog1/MeuBotao.pushbutton` |
| PR revisado | #22 — CR-BENCH-OPENING-RECONSTRUCTION-A |
| branch do PR | `claude/opening-detector-root-fix-m21hfm` |
| HEAD revisado (confirmado) | `b61474d5542f813b5675f70d5bf25387c769b23f` |
| base (confirmada, ancestral do HEAD) | `3f293d1433e8c16eb186959e33a345b60ac944f9` |
| branch desta revisão | `claude/opening-detector-review-cr-a-q8bhuk` |
| diff de produção do PR | 1 arquivo — `nuvem/core/engine/opening_audit.py` (88 linhas) |
| gabarito | intocado (verificado: `git diff --name-only` não toca `nuvem/benchmark/projects/**` nem `nuvem/REGRAS_MODULACAO_BLOCOS.md`) |

**Veredito: `APPROVE_WITH_EXPLICIT_CONDITIONS`** (não `APPROVE`, não `NEEDS_FIX` de lógica, não `DO_NOT_MERGE`). Detalhe no §7.
**NÃO MERGEADO. NÃO iniciada CR-B, C02, C10, Junction, S1/S2.**

---

## 1. Contrato do detector — separação IDENTIDADE / GEOMETRIA / PROVENIÊNCIA

Reproduzi o algoritmo linha a linha (`opening_audit.py:143-262`) e confirmei que as
quatro perguntas do enunciado são de fato respondidas por partes distintas do código:

| pergunta | resposta no código | mudou nesta CR? |
|---|---|---|
| **Identidade** — mesma abertura entre fiadas? | `abs(gs2-run_start) <= TOL` contra o **envelope corrente** (`run_start`/`run_end`) | **não** — mesma linha de antes |
| **Geometria observada** — o que toda fiada do trecho respeita? | `consensus_start=max(gap_starts)`, `consensus_end=min(gap_ends)` — interseção dos vazios OBSERVADOS por fiada | **novo** — antes era o envelope (união) |
| **Geometria física** (jamba real) | **não é respondida pelo detector** — nenhuma peça de verga/porta/janela do Revit entra aqui | inalterado: o módulo não tem esse dado |
| **Proveniência** | `opening_provenance` ∈ {`RECONSTRUCTED_CONSENSUS`, `INCONCLUSIVE`}; `MEASURED`/`RECONSTRUCTED_ENVELOPE` só vocabulário, nunca emitidos por este módulo | novo campo |

### 1.1 Achado — a "geometria observada" é rotulada como "geometria física" em dois lugares

O código e a doc **não** cometem o erro de tratar consenso como abertura confirmada em
nenhum consumidor (ver §2), mas usam a palavra errada para descrever o que o consenso
*é*:

```
nuvem/core/engine/opening_audit.py:172
  2. "quais sao as JAMBAS FISICAS dessa abertura?" -> decidida pelo CONSENSO...

docs/BENCH_OPENING_RECONSTRUCTION_A_IMPLEMENTATION.md:114
  | `x_range` | **consenso** — a geometria física do vão (era o envelope) |
```

O consenso é **interseção de vazios observados em todas as fiadas do trecho** — uma
propriedade estritamente mais forte e mais segura que o envelope (nunca declara vazio
onde há peça), mas **não é, por si, uma jamba física confirmada**: nenhuma peça de
porta/janela real do Revit (`source_element_id`) participa do cálculo. É exatamente a
promoção que o enunciado desta revisão pede para não deixar passar
("consenso = jamba física verdadeira").

**Risco:** nenhum, hoje — nenhum consumidor lê essa string, e nenhum teste depende dela.
É puramente uma questão de precisão de vocabulário que pode induzir um leitor futuro
(ou a própria CR-B) a tratar `RECONSTRUCTED_CONSENSUS` como prova de porta/janela real.

**Correção mínima recomendada (documental/comentário, zero mudança de comportamento):**
trocar "JAMBAS FISICAS" (linha 172 do `.py`) e "geometria física do vão" (linha 114 do
`.md`) por algo como "a borda que toda fiada observada respeita" / "geometria
reconstruída por consenso entre fiadas" — preservando a distinção que o resto do
código já faz corretamente entre `MEASURED` (Revit) e `RECONSTRUCTED_*` (deduzido).

---

## 2. Consumidores reais — nenhum trata consenso ou INCONCLUSIVE como abertura medida

Rastreei os dois consumidores de produção citados no PR, mais um terceiro que a doc não
lista explicitamente como consumidor do *detector* (mas é o consumidor real da
geometria de abertura no **solver**):

| consumidor | chama o detector? | usa `opening_provenance`? | risco de INCONCLUSIVE virar MEASURED |
|---|---|---|---|
| `nuvem/core/wall_modeling.py:2259` `audit_existing_masonry_openings` (auditoria ao vivo) | sim | **não** — usa `x_range` direto via `nearest_opening_jamb_distance_cm`/`is_cut_block_justified_by_opening` | nenhum consumidor filtra por proveniência; **hoje inofensivo só porque INCONCLUSIVE é matematicamente inalcançável** (ver §3.1) |
| `nuvem/benchmark/extract/reconstruct.py:411` (extração de gabarito) | sim | **não** — grava `confidence="reconstructed"` fixo, não propaga `opening_provenance`/`jamb_spread_cm` (correto: é trabalho da CR-B, §9.1 da doc) | mesmo caso: se INCONCLUSIVE ocorresse, viraria uma abertura de largura zero no gabarito, não medida, mas também não sinalizada — `model.make_opening` não tem guarda contra isso |
| `nuvem/benchmark/validators/validate_openings.py` (valida blocos do solver contra vão) | **não** — lê `wall["openings"]` já congelado em `reference.json`, nunca chama `detect_wall_openings_from_courses` | n/a | confirma a alegação do PR: o solver não é afetado por esta CR (§4 da doc) |

Nenhum consumidor promove consenso a "medido", e nenhum teste (`test_detector_nunca_declara_abertura_MEASURED`) permite que o detector se autodeclare `MEASURED`. **Contrato de INCONCLUSIVE respeitado** — mas por ausência de uso, não por checagem explícita.

**Recomendação não-bloqueante (defensiva, não é lógica nova):** `audit_existing_masonry_openings` já roda em produção hoje (diferente de `reconstruct.py`, que é explicitamente CR-B). Vale um `if op["opening_provenance"] == OPENING_PROVENANCE_INCONCLUSIVE: continue` (ou reportar separadamente) antes de usar a abertura no relatório ao vivo, como cinto-e-suspensório para o dia em que `OPENING_GAP_MIN_CM`/`OPENING_RUN_EDGE_MATCH_TOLERANCE_CM` mudarem. Não bloqueia esta CR.

### 3.1 Prova independente de que INCONCLUSIVE é inalcançável hoje

Refiz a prova algébrica do §2.2 da doc de implementação, não apenas conferi a conclusão:

- `run_start` só decresce (ou mantém) ao longo do trecho e nasce do gap da **fiada-âncora** (a primeira do trecho); logo, para toda fiada `i` do trecho, `gs_i <= run_start_no_momento_do_match + TOL <= gs_âncora + TOL`.
- Por simetria, `ge_i >= ge_âncora - TOL` para toda fiada `i`.
- Logo `consenso = min(ge_i) - max(gs_i) >= (ge_âncora - TOL) - (gs_âncora + TOL) = largura_âncora - 2·TOL >= GAP_MIN - 2·TOL = 50 - 30 = 20,0cm > 0`.

Isto vale **para qualquer número de fiadas no trecho**, não só para trechos curtos — a
âncora é sempre a primeira fiada do trecho, não uma fiada "corrente" que poderia
"andar" indefinidamente. A alegação do PR está correta, e é uma invariante do algoritmo,
não uma observação empírica do corpus atual. `test_consenso_tem_piso_matematico_de_GAP_MIN_menos_duas_tolerancias` só confere a aritmética (`GAP_MIN - 2*TOL > 0`), não a prova; a prova em si não está escrita em lugar nenhum — vale registrá-la (comentário) porque é ela, e não o teste, que garante que o ramo é morto.

---

## 3. Hard gate de centro (0,01cm) — reprodução dos casos reais

Usando os artefatos já commitados (`detector_state_a.json` / `detector_state_b.json`),
recalculei eu mesmo (chave de identidade `(wall, z_range, n_courses, envelope)`, igual
à de `compare_states.py`) todo deslocamento de centro entre STATE_A e STATE_B.

**Achado: são 4 aberturas com deslocamento > 0,01cm, não 3** (a doc, §5 e §8, diz "3
aberturas... 0,06cm"). As 4:

| projeto | parede (id em `reference.json`) | A `x_range` | B `x_range` (consenso) | Δcentro |
|---|---|---|---|---|
| TGD | W082 | `[19.0, 110.0]` | `[19.12, 110.0]` | 0,06cm |
| TP1 | W029 | `[18.88, 109.88]` | `[19.0, 109.88]` | 0,06cm |
| TP1 | W040 | `[19.0, 110.0]` | `[19.12, 110.0]` | 0,06cm |
| TP1 | W072 | `[19.0, 110.0]` | `[19.12, 110.0]` | 0,06cm |

(mais 2 casos, um por projeto, em exatamente 0,01cm — fronteira do gate, não incluídos
na tabela acima por não estarem *acima* de 0,01cm; e 22 casos em 0,005cm, dentro do
gate.)

Para os 4 casos acima, fui até `reference.json` (o gabarito congelado) checar o campo
`openings` da própria parede:

```
TGD  W082: {"t_start_cm": 19.0,  "t_end_cm": 110.0, "confidence": "reconstructed",
            "source_element_id": None}   source_element_ids da parede: []
TP1  W029: {"t_start_cm": 18.88, "t_end_cm": 109.88,"confidence": "reconstructed",
            "source_element_id": None}   source_element_ids da parede: []
TP1  W040: {"t_start_cm": 19.0,  "t_end_cm": 110.0, "confidence": "reconstructed",
            "source_element_id": None}   source_element_ids da parede: []
TP1  W072: {"t_start_cm": 19.0,  "t_end_cm": 110.0, "confidence": "reconstructed",
            "source_element_id": None}   source_element_ids da parede: []
```

E fui à peça real na fiada (`reference.json`, elevação 0,0 de `W082`): há um
`MEIO BLOCO - 14x19x19` em `[0.12, 19.12]` numa fiada e presumivelmente `[0, 19.0]` na
fiada alternada — a origem do desacordo de 0,12cm é uma coordenada fracionária de
**bloco realmente colocado no corpus**, não um número inventado. Isso confere com a
"família 0,11–0,12cm" descrita no §5 da doc.

**Mas** — e este é o ponto que muda a leitura do gate — **nenhuma das 4 tem
`source_element_id`, e a própria parede não tem `source_element_ids`**. A abertura
gravada em `reference.json` para esses 4 casos é `confidence: "reconstructed"`,
**e o valor `[19.0, 110.0]` (ou `[18.88,109.88]`) que ali está gravado é,
ele mesmo, o produto do detector ANTIGO (envelope) rodando sobre o mesmo corpus** —
confirmei que esse valor é byte-idêntico ao `x_range` que `state_detector.py STATE_A`
calcula para essas 4 paredes. Ou seja: o "gabarito" para esses 4 casos não é uma
medição independente do Revit — é a saída congelada do defeito que esta CR está
corrigindo (`reconstruct.py:411` roda exatamente esta função na extração).

### 3.2 Determinação pedida no enunciado (A/B/C/D)

- **(A) existe evidência medida que justifica o novo centro?** Não. Existe evidência de
  **peça real colocada no corpus** (o bloco em `[0.12, 19.12]`), o que é mais forte que
  "arredondamento" — mas não é medição Revit independente, porque o próprio valor antigo
  do gabarito para esses 4 vãos também não é medição Revit independente (é saída do
  detector antigo). Não há terceiro ponto de referência para arbitrar entre `19.00` e
  `19.12`.
- **(B) a geometria deve permanecer INCONCLUSIVE?** Não — o consenso está bem formado
  (90,88cm, dentro do domínio, longe do piso de 20cm do §3.1); marcar INCONCLUSIVE aqui
  seria o "piso de ruído" que o enunciado proíbe criar.
- **(C) o detector precisa preservar a distinção entre intervalo observado e abertura
  física?** **Sim, e já preserva** — o código nunca chama esses 4 casos de `MEASURED`,
  e o consenso continua contido em todas as fiadas (verificado). O que falha é a
  **descrição em prosa** (§1.1 desta revisão e a doc do PR), que chama esse deslocamento
  de "evidência medida" quando na verdade é "evidência de peça reconstruída, sem
  contrapartida medida no Revit".
- **(D) existe outro defeito de extração que exige CR separada?** Sim — e a própria doc
  do PR já classifica isso corretamente como problema de **extração** (coordenada
  fracionária), não do detector, e o marca como aberto (§5, §11.2). Concordo com essa
  classificação; não é escopo da CR-A resolver.

**Conclusão do gate:** o desvio de 0,06cm nos 4 casos é real, pequeno (0,6mm, abaixo de
qualquer tolerância construtiva), direcionalmente seguro (estreita para dentro do vazio
observado, nunca inventa), e não tem como ser resolvido com mais certeza dentro do
escopo desta CR — mas a **alegação de "evidência medida" para justificá-lo está
incorreta** e precisa ser corrigida no texto (não no código), e a **contagem "3
aberturas" precisa virar "4"**, pelos números que os próprios artefatos commitados do
PR mostram.

---

## 4. Registro de regra (§10 da doc de implementação)

Revisei o texto proposto para pendência de registro em
`nuvem/REGRAS_MODULACAO_BLOCOS.md` (não escrito nesta CR, por proibição do enunciado —
confirmei via `git diff` que o arquivo está intocado, e que a seção 10.6 já está
rotulada `PADRÃO OBSERVADO AINDA NÃO CONFIRMADO`, como a doc afirma).

O texto pendente (§10) é uma descrição do contrato **já implementado e testado** nesta
CR (tolerância decide identidade, nunca geometria; borda gravada é consenso; desacordo
é dado) — não introduz regra de domínio nova, não toca a regra de amarração em X, não
toca a seção 35 do B19, e explicitamente **recusa-se** a promover os 15cm a constante de
domínio. Isso está correto e é apenas documentação de contrato aprovado — diff mínimo,
sem necessidade de decisão humana adicional **desde que** a frase seja ajustada para não
reintroduzir "jamba física" (mesmo problema do §1.1):

> sugestão de ajuste na frase final do registro pendente: trocar "a borda gravada é o
> **consenso** entre as fiadas" (já está correto, manter) e evitar, no texto de
> implementação/comentário que a acompanha, a formulação "geometria física" — usar
> "geometria reconstruída por consenso" ou "borda observada em todas as fiadas do
> trecho".

Não vejo necessidade de bloquear o registro por isso — é o mesmo ajuste de vocabulário
do §1.1, replicado aqui por completude.

---

## 5. Testes e escopo

Rodei a suíte do CR-A isoladamente e o toggle STATE_A/STATE_B eu mesmo, no meu worktree:

```
HEAD (STATE_B, com a correção):        44 passed em 1,49s
opening_audit.py revertido ao base
(STATE_A, sem a correção), testes intactos:  37 failed, 7 passed em 1,66s
```
Bate exatamente com o que a doc do PR relata em §6/§12.1.

Também rodei `repro_envelope.py` e `repro_axis_gap.py` (rápidos, sem solver) e conferi
que reproduzem exatamente os números citados na doc — inclusive a linha `W003 env=[579,765] cons=[594,750] == BURACO MEDIDO [594.0,750.0] entre W017 e W015` e o resumo final `consenso == buraco entre paredes MEDIDAS: 10 | divergente: 9 | sem geometria medida: 0`.

**Não rodei a suíte completa (36min) nem o solver dos 3 projetos** — não era necessário
para responder a nenhuma dúvida nova: `validate_openings.py` (o único caminho pelo qual
o solver poderia ser afetado) não chama o detector (confirmado por leitura de código,
§2), e o próprio PR já commitou `solver_state_delta.json` com fingerprint/score/achados
idênticos nos 3 projetos — conferi esse arquivo e ele é consistente com a alegação de
delta zero. Se alguém quiser uma reprodução independente do solver também, é um
`python3 nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_a/state_solver.py STATE_A ...` e `STATE_B ...` — não fiz por não agregar dúvida nova, só tempo.

### 5.1 Qualidade dos testes — o ponto que o enunciado pediu para vigiar

- Agrupamento de identidade: **não mudou** (confirmado lendo o diff: o bloco de match
  por `run_start`/`run_end` é byte-idêntico ao anterior).
- Aberturas medidas: **não são tocadas** — o detector nunca produz `MEASURED`
  (`test_detector_nunca_declara_abertura_MEASURED`), e os arquivos com aberturas
  medidas (`input.json`) não são lidos por este módulo.
- Novos campos não quebram consumidor existente: confirmado — `x_range` continua no
  mesmo formato/posição no dict; os campos novos são aditivos.
- INCONCLUSIVE não é tratado como MEASURED em teste nenhum, e é inalcançável em
  produção (prova independente no §3.1 acima).
- Nenhuma abertura real apagada/encurtada sem proveniência: `test_corpus_nenhuma_
  abertura_alargada_nem_fora_do_envelope` e o par so_em_A/so_em_B = 0/0 sustentam isso.
- Os 2 fails da suíte completa citados (§12.2 da doc) — não rodei a suíte completa
  (ver acima), mas a alegação de que são pré-existentes é logicamente sólida
  (score byte-idêntico entre STATE_A/STATE_B ⇒ o teste que compara score contra
  `baseline.json` não pode ter mudado de resultado) e é consistente com o que
  `solver_state_delta.json` (committed) mostra.
- `test_no_TL_na_jamba_a_borda_gravada_e_uma_borda_OBSERVADA` — **é quase tautológico**:
  `max(gap_starts)` é, por definição, um dos `gap_starts`; o teste confere isso, não
  prova nada além da própria fórmula. Não é um problema — é uma proteção de regressão
  legítima — mas não deve ser lido como "prova de jamba física", exatamente a ressalva
  que o enunciado desta revisão pediu para não deixar passar. É o mesmo ponto do §1.1,
  agora do lado dos testes: "borda observada em alguma fiada" ⇒ o teste confirma isso;
  "jamba física medida no Revit" ⇒ nenhum teste afirma isso, e nenhum deveria, porque
  não é verdade para os 4 casos do §3.

---

## 6. Higiene do PR

`git diff --stat` (base → HEAD): 16 arquivos, +24303/-3. A esmagadora maioria
(14.965 linhas, ~178KB) é `repro_envelope.json`, dentro de
`nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_a/`.

- O próprio `README.md` da pasta (linha 48-51) documenta que `solver_state_a.json`/
  `solver_state_b.json` (~1,3MB cada) foram **deliberadamente excluídos** do
  repositório por serem regeneráveis via `state_solver.py` + `compare_states.py`.
- `repro_envelope.json` é igualmente regenerável — é a saída determinística de
  `repro_envelope.py` rodado sobre `reference.json` dos dois projetos, ambos já
  versionados. Rodei eu mesmo (`python3 repro_envelope.py`) e o arquivo é
  reproduzido byte a byte (mesmos contadores, mesma estrutura).
- Comparando com o precedente do repositório (`nuvem/benchmark/diagnostics_bench_z_origin/`,
  de uma CR anterior: 12KB), esta pasta de evidência (356KB) é ~30× maior — quase
  inteiramente por causa deste um arquivo.
- Não é dado único: não há medição manual, nem print, nem nada que só exista nesta
  sessão — é puro artefato determinístico do algoritmo sobre dado já versionado.

**Recomendação (não bloqueante para a correção, mas deveria ser resolvido antes do
merge):** aplicar ao `repro_envelope.json` o mesmo tratamento que já foi dado a
`solver_state_a/b.json` — remover do commit (ou substituir por um resumo agregado, como
já existe em `detector_state_delta.json`) e deixar o `README.md` instruir a regeração.
Nenhum outro arquivo do diff chamou atenção por tamanho ou por conter dado que deveria
estar fora do versionamento.

---

## 7. Veredito e condições

**`APPROVE_WITH_EXPLICIT_CONDITIONS`**

A correção em si — separar identidade de geometria, gravar consenso em vez de
envelope, não apagar desacordo, não inventar geometria no ramo sem consenso — está
correta, minimamente escopada (1 arquivo de produção), não regride o solver (por
construção: nenhum consumidor do solver chama o detector), tem 44 testes que
exercitam a função de produção pelo caminho real, e a alegação de que os hard gates
C04/NODE-FILL/ARM/B19 estão preservados é logicamente sólida.

As condições abaixo são **documentais/de higiene**, não mudam o comportamento do
detector, e por isso não implementei nada — ficam como instrução precisa para quem for
aplicar na branch `claude/opening-detector-root-fix-m21hfm` do PR #22:

1. **`nuvem/core/engine/opening_audit.py:172`** — trocar "JAMBAS FISICAS" por uma
   formulação que não implique confirmação física (ex.: "qual é a borda que TODA fiada
   observada respeita?").
2. **`docs/BENCH_OPENING_RECONSTRUCTION_A_IMPLEMENTATION.md:114`** — trocar "a
   geometria física do vão" por algo como "a geometria reconstruída por consenso entre
   fiadas".
3. **Mesma doc, §5 e §8** — corrigir a contagem de "3 aberturas" deslocadas em 0,06cm
   para **4** (TGD: `W082`; TP1: `W029`, `W040`, `W072` — nomes de parede em
   `reference.json`), e ajustar a frase "há evidência medida" para deixar explícito que,
   para esses 4 casos especificamente, não há `source_element_id`/abertura `measured`
   correspondente — a evidência é a peça reconstruída no próprio corpus, não medição
   Revit independente (ver §3 desta revisão para os números exatos).
4. **Higiene**: remover `repro_envelope.json` do commit (regenerável via
   `repro_envelope.py`, mesmo tratamento já dado a `solver_state_a/b.json` no README da
   pasta) ou substituí-lo por um resumo agregado.
5. *(Recomendado, não bloqueante, pode ir na CR-B)*: em
   `audit_existing_masonry_openings` (`nuvem/core/wall_modeling.py:2259`), pular ou
   sinalizar separadamente aberturas com `opening_provenance == OPENING_PROVENANCE_
   INCONCLUSIVE` antes de usá-las no relatório ao vivo — defensivo, já que esse
   consumidor roda em produção hoje (diferente de `reconstruct.py`, que é CR-B).

Nenhuma dessas condições exige tocar no gabarito, no agrupamento de identidade, ou em
qualquer arquivo fora de `opening_audit.py` (comentário) e a própria doc do PR.

## 8. Pendências que pertencem à CR-B (não desta revisão)

Confirmo a lista do §9/§13 da doc do PR: decisão entre "abertura estreita" (opção A) e
"duas paredes separadas" (opção B) para os 19 casos por projeto com assinatura de
15,0cm; regravar `opening_provenance`/`jamb_spread_cm` no gabarito
(`reconstruct.py:411`); recalibrar `reference_score.json`; decisão sobre o TP1 (sem
fonte medida, hoje só por analogia com o TGD). Nada disso foi tocado nesta CR, e nada
disso deveria ser — está corretamente fora de escopo.

---

**PARADO AQUI. Não mergeado. Nenhuma outra CR iniciada.**
