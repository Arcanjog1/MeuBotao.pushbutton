# CR-G12 — revisão independente, contratos de teste e desempenho

> **Nenhum merge. Nenhum arquivo oficial regravado. Nenhum monitoramento
> criado. Nenhuma outra CR iniciada.**

| item | valor |
|---|---|
| base histórica | `91258dd627af97fe437a56c0506eb096ca5aa267` (`main` real, conferida por `fetch`) |
| branch revisada | `claude/cross-band-mechanism-fix-ab76jv` |
| HEAD revisado | `777960c8d14d58b7507c00d4130ce6ad3e3d7fee` |
| `git merge-base main <branch>` | `91258dd` — a branch está **exatamente** sobre a base informada |
| commits da branch | `b3dcf0a` (código + docs + testes) e `777960c` (docs) — **2** |
| branch desta revisão | `claude/cr-g12-independent-review-w93jf8`, montada **sobre `777960c`** (proveniência e separação de commits preservadas) |
| veredito | **APPROVE_WITH_EXPLICIT_CONDITIONS** (§13) |

## 1. Método

Toda medição foi feita em **cópias isoladas** montadas por `git archive`
(nenhum merge, nenhuma branch alterada):

| árvore | conteúdo |
|---|---|
| `base` | `91258dd` puro |
| `patch` | `777960c` |
| `s1c1_off` | `91258dd` + `wall_stepper.py` da CR-S1 (`33d035f`) + `validate_wall_coverage.py` da CR-C1 (`34bf696`) |
| `s1c1_on` | idem + `wall_modeling.py` da G12 e `wall_stepper.py` **fundido a 3 vias** (`base=91258dd` / `S1` / `G12`) |

Os três HEADs auxiliares foram conferidos por `fetch` e batem com o
relatório: CR-S1 `33d035f`, CR-C1 `34bf696`, candidato CR-B `5640933`. A
fusão a 3 vias do `wall_stepper.py` foi refeita nesta revisão: **sem
conflito**, como o relatório afirma.

O candidato CR-B **não foi regerado**: os `input_candidate.json` /
`input_roundtrip.json` já estão versionados em `5640933`
(`.../bench_opening_reconstruction_b_candidate/evidence/`) e foram usados
como estão. **A CR-B, a C2 e os 19 casos não foram reabertos.**

### 1.1 Escopo do diff — conferido

Arquivos de produção tocados: **apenas** `nuvem/core/wall_modeling.py` e
`nuvem/core/engine/wall_stepper.py`. Nada em
`nuvem/benchmark/projects/**`, `baseline.json`, `reference_score.json`,
`nuvem/benchmark/validators/**`, `pytest.ini` ou `conftest`. Nenhum
`skip`/`xfail`, nenhum threshold alterado.

---

## 2. Veredito do mecanismo — **correto**

Revisão linha a linha de `_cross_band_swapped_layout` (`wall_stepper.py`)
e do laço de passes (`wall_modeling.py`), confrontada com medição.

| exigência do enunciado | veredito | evidência |
|---|---|---|
| propagação de juntas entre bandas | **OK** | `_cross_band_seed_for_band` usa `letter = "A" if course_index % 2 == 0 else "B"`, **a mesma** expressão do laço de bandas em `_solve_building_blocks_all_courses_pass` — a paridade nunca pode divergir. Vizinha da própria banda é descartada por `band_of_course`. |
| preservação das peças de amarração fixas | **OK** | a troca só substitui um **layout de trecho livre** devolvido por `_pier_layout_avoiding_joints` para o **mesmo `pier_cm`**; peça de nó/canto nunca entra. Provado no reproducer mínimo (`test_reproducer_minimo_nao_move_peca_de_amarracao_nem_abertura`). |
| troca conservadora e ganho estrito | **OK** | `if not cross_band_joints_cm: return layout` (semente vazia devolve intacto); `if not antes_cross: return layout` (não mexe em quem já está certo); `if ... >= antes_cross: return layout` (**nunca troca por empate**). |
| proteção das regras #1 e #2 | **OK** | guarda #3 rejeita se a coincidência com `same_band_avoid_cm` **piorar**; guarda #4 rejeita se `_layout_compensator_run_excess` **piorar**. Ambas permitem empate — “não piorar”, como documentado. |
| dois passes e aceitação global | **OK** | `_solve_building_blocks_all_courses_core` só substitui o resultado se `_cross_band_coincidence_total` cair **estritamente**; empate mantém o passe anterior. |
| comportamento com mecanismo desligado | **OK — provado fisicamente** | ver §2.1 |
| determinismo | **OK** | toda iteração da semente é `sorted(...)`; `test_determinismo_da_correcao` (suíte da CR) passou nesta revisão. |
| ausência de regressão nas bandas já corretas | **OK com ressalva** | zero junta contínua nova por identidade física (§10); a ressalva de STAGGER está em §10.2. |

### 2.1 Mecanismo desligado ≡ comportamento anterior (prova física)

Rodei a árvore `patch` com `CROSS_BAND_JOINT_PROPAGATION_ENABLED = False`
e comparei com a árvore `base`, **identidade a identidade**:

```
TGD, achados do benchmark:        4916  x  4916   IDENTICOS (lista igual)
prisma forçado ORIGINAL:          31 paredes, as mesmas (inclui a 23)
repairable ORIGINAL:              [4,23,54,89,90,91,92,120], igual
ARM accepted:                     [23/SAME_A, 91/SAME_B], igual
ARM rejected:                     19, mesmos motivos
prisma forçado FINAL:             29 paredes, lista igual
campos divergentes:               NENHUM
```

Não é “praticamente igual”: é a **mesma saída**.

### 2.2 Reprodução do caso mínimo de três paredes

`tests/test_cross_band_joint_propagation_cr_g12.py` — **20 passed**
(878 s nesta máquina), incluindo os 3 testes do subplano de 3 paredes
reais (falha pré-fix pela identidade `(-401,5, 309,5)` cotas 121/141,
desencontro 0,00cm; zero junta contínua pós-fix; peças de amarração e de
reparo de abertura no mesmo lugar). **Falha pré-fix e passa pós-fix pelo
mesmo mecanismo físico**, confirmado.

### 2.3 Os 12 achados e as duas residuais do TGD — reproduzidos

Medição independente sobre o candidato CR-B com S1+C1, nas duas árvores:

| projeto | árvore | `R` | `C` | saldo | **novas** | sumiram |
|---|---|---|---|---|---|---|
| TGD | S1+C1 **sem** G12 | 298 | 240 | −58 | **12** | 70 |
| TGD | S1+C1 **+ G12** | 256 | 192 | −64 | **0** | 64 |
| TP1 | S1+C1 **sem** G12 | 286 | 228 | −58 | **12** | 70 |
| TP1 | S1+C1 **+ G12** | 260 | 196 | −64 | **0** | 64 |

As 12 identidades do TGD saíram nos **mesmos 12 pontos e cotas** do
relatório (`(-1004…-804, 17/187)`, cotas `141/161`, espessura 14,0).
**Não são** as 10 `JUNCTION_MISSING_BINDING`: código, grandeza e conjunto
de identidade diferentes (defeito antigo, não regressão nova).

**Residual honesto conferido** — no corpus oficial da `main` (TGD),
classificando cada `PRISM_CONTINUOUS_JOINT` por fronteira de banda:

```
BASE   total=336  cross-band=156  cross-band PURAS=16
PATCH  total=322  cross-band=142  cross-band PURAS= 2
residuais: W069 t=649,5 fronteiras (6,7) e (11,12)
```

Exatamente as **2** residuais que o relatório declara, no ponto que ele
declara. Nenhuma delas está entre as 12 do G12.

---

## 3. Análise contratual das duas falhas novas

### 3.1 `test_t1_t9_candidato_seguro_e_aceito_no_tgd_real`

**Contrato que a asserção protege.** T1/T9 é o *controle positivo* do
gate do SAFE REPAIR: provar que ele **não é vacuamente conservador** —
existe um candidato seguro medido (`wall_idx=23`) e ele é **aceito**.

**Reprodução nas duas árvores** (`_run_tgd(enabled=True)`, TGD real):

| | base `91258dd` | base + CR-G12 |
|---|---|---|
| prisma forçado no resultado **ORIGINAL** | 31 paredes, **inclui a 23** | 30 paredes, **sem a 23** |
| `repairable` (arestas isoladas com prisma forçado) | `[4,23,54,89,90,91,92,120]` | `[4,54,89,90,91,92,120]` |
| `accepted` | `[23/SAME_A, 91/SAME_B]` | `[91/SAME_B]` |
| `rejected` | 19, com os mesmos motivos | 19, com os mesmos motivos |
| **prisma forçado no resultado FINAL** | **29 paredes** | **as MESMAS 29 paredes, lista idêntica** |

**Comparação do resultado físico final, não de chamadas internas:** o
conjunto de paredes com prisma forçado ao fim é **o mesmo conjunto**, não
apenas o mesmo tamanho. E o delta por identidade física dos achados
(§10) não traz nenhum defeito novo de cobertura/abertura/encontro/posição.

**Classificação: MELHORIA que tornou uma expectativa histórica
obsoleta.** `repair_arm_role_isolated_edges` só propõe aresta isolada
cuja parede **tem prisma forçado no baseline**; com a CR-G12 a parede 23
já nasce correta na geração, então não chega a ser candidata. O SAFE
REPAIR não foi enfraquecido — o defeito que ele consertava ali deixou de
existir. Mesmo precedente já registrado na §27.9.

### 3.2 `test_t20_caso_real_tp1_junta_b19_b39_em_cima_da_peca_de_no`

**Significado exato dos termos.** `v_off`/`v_on` = todas as juntas
NÓ|FILL de uma fiada que a fiada oposta empilha, medidas na geometria
final, com a metade simétrica NÓ|FILL **desligada** / **ligada**.
`sig_off`/`sig_on` = o subconjunto da **assinatura real do defeito**
(`t = 34,5 cm`, nó na fiada B). O “contrafactual” é o estado
`v_off`/`sig_off` — o mundo **sem** a metade simétrica. A razão 2×
(`len(sig_on) * 2 <= len(sig_off)`) mede **eficácia relativa da
estratégia** contra esse contrafactual — **não** mede desempenho e **não**
mede o estado de produção.

**Reprodução nas duas árvores** (TP1 real, 2 resoluções por árvore):

| | `v_off` | `v_on` | `sig_off` | `sig_on` | razão 2× |
|---|---|---|---|---|---|
| base `91258dd` | 31 | **14** | 16 | **4** | `4×2 ≤ 16` ✔ |
| base + CR-G12 | 16 | **14** | 5 | **4** | `4×2 ≤ 5` ✘ |

**O estado de produção é idêntico — e não só em contagem:** o conjunto
físico `v_on` é **o mesmo conjunto** nas duas árvores (as mesmas 14
violações, mesmas paredes e posições; diferença simétrica vazia), e
`sig_on` são as mesmas 4 (`paredes 2, 7, 60, 70`, todas em `t=34,5`,
fiada B). Só o **contrafactual** melhorou, porque a CR-G12 retira antes,
na geração, parte do mesmo defeito.

**Classificação: MELHORIA que tornou obsoleta a expectativa histórica** —
especificamente, a razão media a estratégia contra uma referência que
deixou de ser a mesma. Não é regressão: nenhuma violação nova
(`set(sig_on) ⊆ set(sig_off)` continua valendo), e a asserção que prova
que a metade simétrica ainda ajuda (`len(v_on) < len(v_off)`) continua
passando.

---

## 4. Alterações de teste — commit `a7c7f98`

Só as duas asserções acima. **Nenhum teste removido, nenhum
`skip`/`xfail`, nenhum threshold afrouxado.** As duas trocam
*mecanismo* por *resultado físico* e **acrescentam** asserções.

**t1/t9** — sai `any(a["wall_idx"] == 23 for a in accepted)`; entram três:

1. `assert accepted` — o gate continua não podendo ser vacuo;
2. todo candidato **aceito** resolve o prisma forçado do próprio alvo;
3. a parede 23 termina **sem prisma forçado**, pelas duas rotas (reparo
   aceito, ou geração já correta).

**t20** — sai a razão 2×; entram três, mais fortes porque **absolutas**:

1. `len(sig_on) < len(sig_off)` — a metade simétrica ainda tem efeito
   próprio sobre esta assinatura (4 < 5 com G12; 4 < 16 sem);
2. `len(sig_on) <= 4` — o **residual genuíno já documentado** no próprio
   comentário do teste (cadeias de 3 compensadores, juntas fixas em
   24,5/34,5/44,5, REGRAS 30.6/33.5). Não é um número conveniente: é o
   limite físico medido, e **igual nas duas árvores**;
3. `len(v_on) <= 14` — o mesmo, no total NÓ|FILL.

A razão nunca travou o estado de produção (uma redução de 100 para 50
também a satisfaria); os tetos absolutos travam.

**Prova de que os ajustes não codificam o patch — os dois passam nas
duas árvores:**

| teste | base `91258dd` | base + CR-G12 |
|---|---|---|
| `test_t1_t9...` + `test_t10_fallback...` | **2 passed** (133 s) | **2 passed** (255 s) |
| `test_t20...` | **1 passed** (259 s) | **1 passed** (513 s) |

---

## 5. Resultado pré-fix × pós-fix (corpus oficial da `main`, TGD)

Comparação feita **na mesma árvore**, só virando a flag — o que é
legítimo porque a árvore com a flag desligada é bit-a-bit a `base` (§2.1).

| código | pré-fix | pós-fix | Δ |
|---|---|---|---|
| `PRISM_CONTINUOUS_JOINT` | 336 | **322** | **−14** |
| — dos quais **cross-band** | 156 | 142 | −14 |
| — **cross-band puras** | **16** | **2** | **−14** |
| `PRISM_JOINT_STACK` | 20 | 20 | 0 |
| `COMPENSATOR_CONSECUTIVE` | 523 | **511** | **−12** |
| `COMPENSATOR_EXCESS_IN_RUN` | 440 | **439** | **−1** |
| `COMPENSATOR_VERTICAL_STRIP` | 81 | **79** | **−2** |
| `PRISM_STAGGER_BELOW_TARGET` (nível 2) | 841 | 872 | **+31** |
| `COVERAGE_*` / `OPENING_*` / `JUNCTION_*` / `POSITION_*` | — | — | **0** |
| **total** | 4.916 | 4.918 | **+2** |

`piloto_sintetico_2x2`: **124 achados idênticos, identidade a
identidade**, e tempo inalterado (0,08 s → 0,08 s) — a banda única faz o
corte antecipado (`best_score == 0`) pular o segundo passe.

---

## 6. Desempenho

Medido em processos isolados, mesma entrada, mesma configuração, mesma
máquina (4 vCPU).

| medição | base `91258dd` | + CR-G12 | razão |
|---|---|---|---|
| geração multi-banda (`_solve_..._core`), TGD | **2,75 s** | **5,64 s** | 2,05× |
| **resolução completa** (geração + ARM SAFE REPAIR + B19), TGD | **62,6 s** | **134,2 s** | **2,14×** |
| `tests/regression/test_benchmark_baselines.py` (3 projetos) | 594 s | 1.198 s | 2,02× |
| resolução TP1 (metade simétrica desligada) | 115,9 s | 236,7 s | 2,04× |
| resolução TP1 (metade simétrica ligada) | 144,0 s | 268,0 s | 1,86× |
| `piloto_sintetico_2x2` completo | 0,08 s | 0,08 s | **1,00×** |

### 6.1 Onde o tempo está — decomposição

A **geração** é só **2,75 s dos 62,6 s** (4,4%) da resolução completa. Os
outros **95,6%** são os **22 rebuilds** do ARM SAFE REPAIR — pré-existente
a esta CR — (21 tentativas de candidato + 1 rebuild final), e **cada
rebuild é uma geração multi-banda inteira**. A CR-G12 dobra o custo
unitário da geração; o pipeline inteiro dobra junto. **O segundo passe é
a causa; o multiplicador é o SAFE REPAIR.**

Memória: não é fator — o laço de passes retém no máximo **dois** dicts de
resultado, do mesmo tamanho que o pipeline já aloca por rebuild.

### 6.2 Bandas e paredes afetadas

| projeto | bandas | fronteiras | fronteiras **com** coincidência | paredes afetadas |
|---|---|---|---|---|
| TGD | 8 — `[0-4] [5] [6] [7] [8-10] [11] [12] [13-16]` | 7 | **7 de 7** (35/35/41/39/39/33/26 = 248) | 37 |
| TP1 | 7 | 6 | **6 de 6** (53/53/54/47/28/25 = 260) | 52 |

No resultado final do TGD, **apenas 12 das 167 paredes** mudam de layout
(`W007 W011 W046 W069 W070 W072 W074 W075 W087 W090 W113 W160`), e 11
delas já na geração pura.

### 6.3 Otimização investigada — **não implementada, com motivo medido**

O enunciado pede investigar se os dois passes podem atuar **só nas bandas
afetadas por juntas de fronteira**. Medi, e a resposta é **não economiza
nada**:

1. **Todas** as fronteiras dos dois projetos reais carregam coincidência
   (7 de 7 no TGD, 6 de 6 no TP1). Logo **toda** banda é vizinha de pelo
   menos uma fronteira afetada — um segundo passe seletivo por banda
   ainda resolveria as 8 (TGD) / 7 (TP1).
2. Um cache por banda com chave “semente igual à do passe anterior”
   **também não dispara**: no segundo passe toda banda, exceto a do topo,
   ganha uma componente de vizinha **de cima** que o primeiro passe não
   tinha. A semente muda por construção.
3. O atalho “semente sem coincidência ⇒ resultado idêntico, reaproveita”
   **não é provadamente equivalente**: a troca compara as juntas
   **internas do layout**, enquanto as juntas publicadas pela banda vêm
   da **geometria lançada** depois do recorte de abertura e do reparo —
   uma junta do layout pode ter sido recortada, então o conjunto lançado
   **não é superconjunto** do conjunto do layout. Implementar isso
   arriscaria divergência física por um ganho limitado.

O corte antecipado que **já existe** (`best_score == 0 → break`) funciona
e está medido: no `piloto_sintetico_2x2` (banda única) o custo é
**exatamente o mesmo** com e sem o mecanismo.

> **Conclusão: nenhuma otimização pequena e segura dentro do contrato
> desta CR.** O verdadeiro alavanca é ortogonal e pré-existente —
> estreitar os 22 rebuilds do ARM SAFE REPAIR, cada um disparado por um
> candidato que toca 1–3 paredes, com a maquinaria `dirty_wall_idxs` que
> `process_walls_one_by_one` **já tem**. Isso é refatoração ampla e de
> outra CR. **Registrado como dívida (§12.5), não misturado aqui.**

---

## 7. Trade-offs identificados FISICAMENTE

### 7.1 `PRISM_STAGGER_BELOW_TARGET` +31 no TGD — **atribuição corrigida**

33 ocorrências novas, 2 sumiram. Por parede e por par de fiadas:

| origem | n | atribuição física |
|---|---|---|
| 6 paredes que **perderam junta contínua** (`W046 W069 W070 W072 W087 W113`) | **17** | a troca **crítico → nível 2** esperada: onde havia junta empilhada (0,00 cm) agora há desencontro real de 5,0 cm. 24 das 33 caem em par de **fronteira de banda**. |
| **`W074`** | **16** | **NÃO é a troca cross-band.** Ver §7.2. |

### 7.2 As 16 de `W074` são colaterais do ARM, não do mecanismo

Medição decisiva — comparando a **geração pura** (sem ARM SAFE REPAIR nem
B19), flag desligada × ligada:

```
CORE  paredes com blocos diferentes: 11
      W007 W011 W046 W069 W070 W072 W075 W087 W090 W113 W160   <- W074 NAO esta' aqui
FULL  paredes com blocos diferentes: 12
      ... W074 ...                                             <- so' aparece com o ARM
```

`W074` **só muda no pipeline completo**. A causa é a mudança no conjunto
aceito pelo ARM SAFE REPAIR (§3.1): com a flag desligada o candidato
`23/SAME_A` é aceito, e o pin que ele instala também melhorava, de
tabela, a amarração de `W074`; com a flag ligada esse candidato não é
proposto e o benefício colateral se perde. `W074` passa de desencontro
≥ 10 cm para **5,0 cm** em `t=49,5`/`t=54,5` ao longo de toda a altura —
**nível 2, nunca crítico**, sem junta contínua e sem mexer em
cobertura/abertura/encontro/posição.

> **Condição C2 (§13):** a §6.3 item 1 do relatório da CR descreve as +31
> inteiras como “onde antes havia junta empilhada agora há desencontro
> pequeno”. Isso vale para **17**; as outras **16** são colaterais da
> mudança de aceitação do ARM. O texto deve ser corrigido.

### 7.3 `COMPENSATOR_*` — saldo por parede (TGD, off × on)

```
W075  -19    W007  -2    W069  -1    W072 0   W087 0   W113 0   W011 0
W046   +1    W070  +2    W090  +5    W074 +16 (STAGGER, §7.2)
```

`COMPENSATOR_CONSECUTIVE` −12, `EXCESS_IN_RUN` −1 e `VERTICAL_STRIP` −2
no corpus oficial; no candidato CR-B, `CONSECUTIVE` melhora nos quatro
estados (−21/−15/−6/−6) e `EXCESS_IN_RUN` piora **+2** só no TGD
(`R` 1140→1142, `C` 1159→1161) e melhora −2 no TP1. Trade-off pequeno,
real, e declarado pelo relatório.

---

## 8. Deltas por identidade física — nenhum defeito novo

Comparação **identidade a identidade** (não por contagem) dos 4.916 ×
4.918 achados do TGD:

| | novas | sumiram |
|---|---|---|
| `PRISM_CONTINUOUS_JOINT` | **0** | 14 |
| `PRISM_JOINT_STACK` | **0** | 0 |
| `PRISM_STAGGER_BELOW_TARGET` | 33 | 2 |
| `COMPENSATOR_CONSECUTIVE` | 12 | 24 |
| `COMPENSATOR_EXCESS_IN_RUN` | 11 | 12 |
| `COMPENSATOR_VERTICAL_STRIP` | 4 | 6 |
| `OPENING_BLOCK_CROSSES_JAMB` | 6 | 6 |
| `COVERAGE_*`, `JUNCTION_*`, `POSITION_*` | **0** | **0** |

**As 6 de `OPENING_BLOCK_CROSSES_JAMB` não são defeito novo:** mesma
parede `W090`, mesma abertura `W090-O01`, mesmas 6 fiadas (0,2,4,6,8,10),
mesmo código `B34`, mesma invasão de **5,0 cm** — muda **apenas o
identificador ordinal do bloco** (`B011` ↔ `B009`), porque o
preenchimento antes dele mudou. Fisicamente é o **mesmo** achado. Vale a
observação de método: identidade por ordinal de bloco viola a §38.5; o
teste da CR compara **contagem**, e por isso acerta.

---

## 9. Gates

| gate | veredito desta revisão | evidência independente |
|---|---|---|
| **G12** — 12 identidades novas → 0 nos dois projetos | **CONFIRMADO** | TGD `298→256 / 240→192`, novas `12 → 0`; TP1 `286→260 / 228→196`, novas `12 → 0`. **Não aprovado só pela contagem:** zero identidade `PRISM_CONTINUOUS_JOINT` nova, e residual honesto de 2 cross-band puras no TGD (`W069 t=649,5`) |
| **G13** preservado pela S1 | **PRESERVADO** | `JUNCTION_NOT_ALTERNATING` 303 → 303 no corpus oficial; delta 0 em `JUNCTION_*` também no candidato |
| **G16** continua pendente da C2 | **CONTINUA NÃO APROVADO** | `COVERAGE_*` delta 0 por identidade — a CR **não** o destrava, e não tenta |
| **G18** preservado | **PRESERVADO** | o diff não toca nenhum código de chave/identidade (só `wall_modeling.py` e `wall_stepper.py`, na composição do preenchimento) |
| zero juntas contínuas novas | **CONFIRMADO** | por identidade física, nos dois projetos |
| zero regressões `COVERAGE`/`OPENING`/`JUNCTION`/`POSITION` | **CONFIRMADO** | contagem delta 0; a única troca de identidade é o ordinal de bloco da §8 |
| trade-offs STAGGER/COMPENSATOR identificados fisicamente | **FEITO — com correção** | §7 |
| determinismo | **CONFIRMADO** | `test_determinismo_da_correcao` passou; toda iteração da semente é ordenada |
| duas falhas históricas de `test_benchmark_baselines.py` | **CONTINUAM PRÉ-EXISTENTES** | §10 |

**Saldo de `critical_errors` não foi usado para esconder nada**: a
verificação é por identidade, achado a achado.

---

## 10. `test_benchmark_baselines.py` — pré-existentes, sem recalibrar

Rodado nas **duas** árvores, arquivo inteiro:

| árvore | resultado | falhas |
|---|---|---|
| base `91258dd` | **2 failed, 7 passed** (594 s) | TGD categoria `compensators` **52 → 61** (delta 9); TP1 `JUNCTION_MISSING_BINDING` **8 → 9** |
| base + CR-G12 | **2 failed, 7 passed** (1.198 s) | **as mesmas duas, com os mesmíssimos números** |

`baseline.json` **não foi regravado** nesta revisão. Dívida de refresh
mantida como estava.

---

## 11. Estado da suíte

| item | resultado |
|---|---|
| `tests/test_cross_band_joint_propagation_cr_g12.py` (11 rápidos + 9 `slow`) | **20 passed** (878 s) |
| `test_t1_t9...` + `test_t10_fallback...` **com o ajuste** | base **2 passed** · CR-G12 **2 passed** |
| `test_t20...` **com o ajuste** | base **1 passed** · CR-G12 **1 passed** |
| `tests/regression/test_benchmark_baselines.py` | 2 failed pré-existentes nas duas árvores |

Com os dois ajustes do commit `a7c7f98`, as **duas falhas novas
desaparecem sem `skip`, sem `xfail` e sem afrouxar nada** — e as duas
pré-existentes continuam registradas como pré-existentes.

---

## 12. Riscos e dívidas

1. **A garantia “zero junta contínua nova” é EMPÍRICA, não estrutural.**
   A aceitação entre passes usa `_cross_band_coincidence_total`, uma
   métrica **líquida**: nada na estrutura impede que um passe conserte 10
   fronteiras e crie 1 em outro lugar. Nos três projetos medidos isso não
   acontece (0 identidades novas), e o teste `slow` da própria CR trava
   isso por identidade nos dois projetos reais — mas é uma trava de
   **teste**, não de **invariante**. Risco baixo; deve ficar escrito.
2. **`prior_course_joints` recebe o ÚLTIMO passe, não o MELHOR.** Inócuo
   com `CROSS_BAND_JOINT_PROPAGATION_PASSES = 2` (só o passe 2 consome, e
   consome o passe 1). Vira inconsistência latente se alguém subir para
   3+.
3. **Erro no passe 2 descarta um passe 1 válido** — `if result.get("error")
   is not None: return result` devolve o resultado com erro mesmo havendo
   `best` bom. Só alcançável se o passe 2 falhar e o 1 não; teórico.
4. **§6.3 item 1 do relatório da CR está incompleto** — ver §7.2 e a
   condição C2.
5. **Custo ~2× (dívida de desempenho).** A alavanca real são os 22
   rebuilds do ARM SAFE REPAIR (95,6% do tempo), não os dois passes.
   Estreitá-los com `dirty_wall_idxs` é **outra CR** (§6.3).
6. **2 identidades cross-band residuais no TGD** (`W069`, `t=649,5`,
   fronteiras (6,7) e (11,12)). Confirmadas, não zeradas — o guard recusa
   corretamente qualquer alternativa que pioraria a regra #1 dentro da
   banda.
7. **Refresh de `baseline.json`** — CR própria, não iniciada.
8. **CR-S1 (#25) e CR-C1 (#26) continuam `draft`.** O gate G12 é medido
   sobre a projeção das duas; a aprovação do gate pressupõe o merge delas.
9. **Observação de método:** o teste `test_cobertura_aberturas_amarracao_e
   _posicao_com_delta_zero` compara **contagem por código**. Uma versão
   por identidade **física** (§38.5 — ponto, cotas, espessura; nunca o
   ordinal do bloco) seria mais forte. Não alterado aqui: está fora do
   que esta revisão autoriza mexer, e a contagem já cobre o gate.

---

## 13. Veredito

> ## **APPROVE_WITH_EXPLICIT_CONDITIONS**

O mecanismo está **correto**, é **desligável com equivalência física
provada**, **determinístico**, ataca a causa-raiz registrada na §27.7, é
reproduzido por um caso mínimo de 3 paredes reais que **falha pré-fix e
passa pós-fix pelo mesmo mecanismo físico**, e entrega o gate G12
(**12 → 0 nos dois projetos**) sem criar **nenhuma** junta contínua nova
e sem tocar cobertura, abertura, encontro ou posição. As duas falhas
novas da suíte são **melhoria**, não regressão — medido nos dois lados,
com o resultado físico final **idêntico** nos dois casos.

**Condições explícitas:**

**C1.** Aceitar os dois ajustes de contrato do commit `a7c7f98` (ou
equivalente que preserve o contrato físico). Sem eles a suíte fica em
`4 failed` por asserções que medem mecanismo obsoleto.

**C2.** Corrigir a §6.3 item 1 de
`docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md`: das 31 ocorrências líquidas
novas de `PRISM_STAGGER_BELOW_TARGET`, **17** são a troca crítico → nível
2 descrita; as outras **16** (todas em `W074`) são **colaterais da
mudança de aceitação do ARM**, não da troca cross-band (§7.2).

**C3.** Aceitar explicitamente o custo **~2,1×** como dívida declarada do
beta (§6), **ou** autorizar a CR separada que estreita os rebuilds do ARM
SAFE REPAIR — que é onde estão 95,6% do tempo.

**C4.** G16 continua **não aprovado** e a CR-C2 continua pendente. A
aprovação do G12 como gate pressupõe o **merge autorizado** da CR-S1 e da
CR-C1, sobre cuja projeção ele foi medido.

**C5.** As duas falhas de `test_benchmark_baselines.py` continuam
registradas como **pré-existentes** (mesmos números nas duas árvores); o
refresh de `baseline.json` continua sendo CR própria.

**Não é `DO_NOT_MERGE` nem `NEEDS_FIX`:** não encontrei regressão física,
nem defeito de mecanismo, nem teste afrouxado. As condições são de
**registro e decisão humana**, não de código.
