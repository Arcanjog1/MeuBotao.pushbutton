# CR-B — RECONCILIAÇÃO INDEPENDENTE DO CONTRATO DE AVALIAÇÃO

> **Revisão independente. Nada foi integrado, nada oficial foi alterado.**
>
> `nuvem/benchmark/projects/**` (`reference.json`, `input.json`,
> `baseline.json`, `reference_score.json`, `evaluation_scope.json`), o
> solver (`nuvem/core/**`), os validadores
> (`nuvem/benchmark/validators/**`), `nuvem/REGRAS_MODULACAO_BLOCOS.md`,
> `docs/PROJECT_STATUS.md` e `tests/**` estão **intocados** — conferido
> por `git diff --name-only` ao fim da sessão.
> Nenhum PR de produção, nenhum merge. C02/C10/Junction/S1/S2 **não
> iniciadas**.
>
> Esta sessão **não** reconstruiu os 19 casos, **não** implementou regra
> de modulação, **não** alterou gabarito, solver ou validadores.

---

## Base / branch / HEAD

| item | valor | conferência |
|---|---|---|
| `origin/main` no início desta sessão | `e381992cdc9f5cfd59547de6d385f25bfe6b3050` | **CONFERE** com a base histórica do enunciado |
| a `main` avançou desde a base? | **não** | `git fetch origin` + `git rev-parse origin/main` |
| candidato revisado | `claude/candidato-validacao-gabarito-q450yr` | HEAD medido `56409334a7b273d0e81a13d8cc916ffe0e214654` — **confere** com o informado (`5640933`) |
| relação candidato ↔ base | **1 commit** em cima de `e381992` | `git log --oneline e381992..5640933` = 1 |
| branch desta reconciliação | `claude/cr-b-reconciliacao-contrato-1byigr` | |
| worktree isolado do candidato | `git worktree add … 5640933 --detach` | leitura apenas |
| arquivos oficiais tocados pelo candidato | **nenhum** | `git diff --name-only e381992 5640933 -- nuvem/benchmark/projects nuvem/core nuvem/REGRAS_MODULACAO_BLOCOS.md tests docs/PROJECT_STATUS.md` → **vazio** |

**Reprodução independente do candidato.** `build_candidate.py` foi rodado
do zero num diretório isolado desta sessão. Os **8 `sha256`** dos quatro
arquivos por projeto batem, byte a byte, com os declarados em §8 do
relatório do candidato — quarto processo independente, sessão diferente.
Os quatro `input_*.json` versionados em `evidence/` são **idênticos**
(`cmp`) aos regerados.

---

## 0. Resumo dos vereditos

| item | veredito desta revisão |
|---|---|
| preservação da alvenaria humana | **CONFIRMADA** de forma independente (§2) |
| `+49 JUNCTION_MISSING_BINDING` | **0 defeitos humanos novos.** 39 são **(C) defeito do validador** (unidade = índice ordinal de fiada), 10 são **(D) mudança de unidade** em nós recém-registrados. **Nenhum nó pré-existente piorou.** (§3) |
| `+16 JUNCTION_NOT_ALTERNATING` | **(A/B) defeito REAL do solver.** É **1 (um) nó físico**, contado 16 vezes (uma por par de fiadas consecutivas). O solver **alternava** nesse mesmo nó com a entrada antiga e **para de alternar** com a nova. (§4) |
| demais deltas | reconciliados por identidade física em §5. **Achado novo: `+28 PRISM_CONTINUOUS_JOINT` de severidade CRÍTICA na saída do solver**, escondido pelo saldo `−42`. |
| contrato de input TGD/TP1 | **CONFIRMADO**: o `input.json` do TGD é fonte medida independente e não pode ser regerado (§6) |
| **D6 / dívida documental** | **A CONCLUSÃO DO CANDIDATO ESTÁ ERRADA.** Os dois relatórios **existem** e estão commitados; nunca foram **mesclados na `main`**. (§7) |
| decisão recomendada | **NÃO INTEGRAR AINDA** — três CRs precedem a integração (§9, §10) |

---

## 1. O que foi lido

- `docs/BENCH_OPENING_RECONSTRUCTION_B_CANDIDATE.md` — **integral**
  (1159 linhas), incluindo §6.5 (conferência R1/R2/R3), §9.5 (D4 e D6),
  o plano de integração §9 e as limitações §12.
- `docs/BENCH_OPENING_RECONSTRUCTION_B_RECONCILIATION.md` (`aa5dd1a`) —
  §9 com o texto exato de **D1–D6**.
- Contratos de validação **lidos no código**, não em resumo:
  `validators/validate_junctions.py` (integral), `validate_prism.py`,
  `validate_wall_coverage.py`, `validate_block_positions.py`,
  `validators/base.py` (taxonomia: nível **e** severidade), `scoring.py`.
- Geradores e evidência do candidato: `build_candidate.py`,
  `candidate_lib.py`, `analyze_junctions.py`, `analyze_divergences.py`,
  `project_solver.py`, `evidence/**`, os dois `README.md`.
- `metadata.json` e `input.json` (metadados) dos dois projetos.

**Nenhum documento ausente foi usado como autoridade. Nenhum relatório de
revisão foi fabricado.** Onde este documento cita os dois relatórios de
revisão independente, ele os cita porque **os encontrou no repositório**
(§7) — e diz em que commit.

---

## 2. Preservação já demonstrada — reconferida, não repetida

O processamento caro (reconstrução dos 19, análise nó a nó, projeção do
solver) **não foi refeito por refazer**. O que foi refeito é a
**verificação dos invariantes**, com scripts próprios que não importam
`candidate_lib`:

| invariante | TGD | TP1 | como foi medido aqui |
|---|---|---|---|
| blocos por identidade `type\|x\|y\|z` | 12508 = 12508 = 12508 | 12703 = 12703 = 12703 | `Counter` sobre `reference.json` oficial, STATE_R e STATE_C |
| blocos humanos **perdidos** (R→C) | **0** | **0** | diferença de multiconjuntos |
| blocos humanos **novos** | **0** | **0** | idem |
| blocos **duplicados** | **0** | **0** | contagem > 1 na mesma identidade |
| blocos **órfãos** | 0 → 0 | 0 → 0 | `orphan_blocks` |
| aberturas **removidas** (identidade = jambas em coordenada de mundo) | **19** | **19** | recontagem própria, chave de mundo |
| aberturas **adicionadas** | **0** | **0** | idem |
| aberturas mantidas com **geometria alterada** | **0** | **0** | comparação de largura/altura/peitoril das 75/73 mantidas |
| removidas com `source_element_id` | **0** | **0** | idem |
| larguras removidas | 8×101 + 10×156 + 1×236 = **2604,0 cm** | idem | soma exata |
| comprimento total | −2604,00 cm | −2604,00 cm | soma de `length_cm` |
| determinismo | **8/8 `sha256`** conferem | | processo novo, sessão nova |

A mudança de contagem de paredes (97→116 / 96→115) e de nós (155→169 /
154→168) **não foi tratada como mudança física** em nenhum ponto desta
reconciliação — toda comparação abaixo é por coordenada de mundo e cota.

**Ressalva metodológica registrada:** a identidade `type|x|y|z` é a mesma
usada pelo candidato. Ela prova que **o conjunto** de peças é idêntico;
não prova, sozinha, que a *atribuição* peça→parede é a mesma — e não
precisa provar, porque a atribuição é justamente o que a CR-B muda.

---

## 3. Os `+49 JUNCTION_MISSING_BINDING` humanos

### 3.1 O contrato do validador — a raiz do problema

`validate_junctions.py` agrupa as fiadas de um nó pelo **ÍNDICE ORDINAL**
`row["row"]` (`_rows_of_group` → `_covering_blocks`, linhas 102–120). O
índice ordinal é a **posição da fiada na pilha daquela parede** — não a
cota. Duas paredes que chegam ao mesmo nó com pilhas de tamanhos
diferentes (meia-fiada de peça CORTADA, base diferente) têm o **mesmo
índice apontando para cotas diferentes**.

**Medido no gabarito de hoje, SEM nenhum corte (STATE_R):**

```
TGD  236 de 373 achados de JUNCTION_MISSING_BINDING nascem de um
     indice ordinal que aponta para MAIS DE UMA cota  (63%)
TP1  232 de 365                                        (64%)
```

**O defeito é PRÉ-EXISTENTE.** A CR-B não o cria; ela o amplifica
(255/422 no TGD, 251/414 no TP1).

Reprodutor mínimo:
`nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_reconciliation/repro_junction_row_unit.py`
— duas paredes, um canto `L`, amarração alternada **correta**; acrescentar
uma meia-fiada cortada a uma delas produz **2 achados falsos** sem que
nenhuma peça mude de lugar nem de cota.

### 3.2 O mesmo achado em três unidades de avaliação

| unidade de avaliação | TGD R→C | TP1 R→C |
|---|---|---|
| **índice ordinal de fiada** (o validador de hoje) | 373 → 422 (**+49**) | 365 → 414 (**+49**) |
| **elevação física em cm** | 348 → 343 (**−5**) | 337 → 332 (**−5**) |
| **estrita** (cota presente em **≥2 paredes** do nó — a única em que "faltou amarração" é afirmável) | 86 → 96 (**+10**) | 82 → 92 (**+10**) |

Na unidade estrita: **10 identidades novas, 0 sumidas**, e **as 10 estão
em nós que NÃO existiam em STATE_R**.

### 3.3 O teste mais físico — falha vertical no eixo do nó

Ignora índice ordinal **e** meia-fiada: no eixo vertical do ponto do nó,
existe faixa de altura sem **nenhuma** peça cobrindo o ponto?

| | TGD | TP1 |
|---|---|---|
| nós de amarração avaliáveis | 147 → 161 | 143 → 157 |
| **nós presentes NOS DOIS que PIORARAM** | **0** | **0** |
| nós presentes nos dois que **melhoraram** | 8 | 8 |
| nós novos (com falha) | 15 (12) | 15 (12) |
| nós sumidos | 1 | 1 |

E os 12 nós novos com falha vertical **já tinham exatamente a mesma
falha em STATE_R**, medida no mesmo ponto XY, na mesma faixa `z` fixa
`[0; 280]`, usando **todos** os blocos do projeto:

```
ponto XY                 STATE_R                                    STATE_C                                    IGUAL
(-139.49,17.05)          [(219.0,280.0)]                            [(219.0,280.0)]                            SIM
(96.51,17.05)            [(219.0,280.0)]                            [(219.0,280.0)]                            SIM
(338.52,24.05)           [(259.0,280.0)]                            [(259.0,280.0)]                            SIM
(-656.49,24.05)          [(219.0,230.0),(259.0,280.0)]              idem                                       SIM
(-401.49,24.05)          [(139.0,150.0),(229.0,240.0),(259.0,280.0)] idem                                      SIM
(593.50,24.05)           [(139.0,150.0),(229.0,240.0),(259.0,280.0)] idem                                      SIM
(848.50,24.05)           [(219.0,230.0),(259.0,280.0)]              idem                                       SIM
(528.50,24.05)           [(259.0,280.0)]                            idem                                       SIM
(-656.49,180.05)         [(219.0,230.0),(259.0,280.0)]              idem                                       SIM
(-401.49,180.05)         [(139.0,150.0),(229.0,240.0),(259.0,280.0)] idem                                      SIM
(593.50,180.05)          [(139.0,150.0),(229.0,240.0),(259.0,280.0)] idem                                      SIM
(848.50,180.05)          [(219.0,230.0),(259.0,280.0)]              idem                                       SIM

cobertura vertical do ponto IDENTICA antes/depois: 12 de 12
```

Todas as faixas ficam na banda de topo (`z ≥ 219`, verga/canaleta) ou numa
faixa de 11 cm em `139–150` (meia-fiada). São **falhas pré-existentes da
alvenaria humana**, byte-idênticas, que passam a ser **registradas**
porque o nó passa a existir.

### 3.4 Verificação do pareamento do validador

Hipótese testada e **REFUTADA**: "o achado é falso porque uma peça de
uma parede fora do grupo do nó cobre o ponto".

```
STATE_R  TGD  373 achados, dos quais com peca real cobrindo o ponto
              numa parede FORA do no', na mesma cota:  0  (0%)
STATE_C  TGD  422 achados                            :  0  (0%)
(idem TP1)
```

### 3.5 Classificação das 49 identidades (por projeto)

| categoria | quantas | evidência |
|---|---|---|
| **A — defeito humano físico real, NOVO** | **0** | 0 nós pré-existentes pioraram; cobertura vertical idêntica em 12/12 |
| **B — defeito de reconstrução/topologia** | **0** | alvenaria byte-idêntica; nenhuma peça a mais/a menos em nenhum nó |
| **C — defeito de validador/pareamento** | **39** | 49 − 10; trocar a unidade de ordinal para elevação leva o delta a **−5** |
| **D — mudança legítima de unidade de avaliação** | **10** | as 10 identidades estritas novas, todas em nós recém-registrados; a falha física é pré-existente e inalterada |
| **E — inconclusivo** | **0** | |

**O mesmo encontro está sendo contado mais vezes?** Sim — pelas duas
razões acima, e não porque a alvenaria mudou. **A fragmentação T→L mudou
a unidade de avaliação?** Sim, e é (D): 15 nós que fisicamente já
existiam e já eram (não) amarrados passam a ser registrados. **O
validador associa corretamente os participantes?** Não: além do índice
ordinal, `collect_nodes` só junta paredes que **declaram** a junção — em
`solver_roundtrip` do TGD o nó `(338.52; 187.05)` aparece com **uma
única** parede e é descartado por `len(wall_ids) < 2`, apesar de haver
duas paredes fisicamente amarradas ali.

**Nada foi corrigido nesta sessão.** CR proposta: §10, CR-V1.

---

## 4. Os `+16 JUNCTION_NOT_ALTERNATING` do solver

Solver de **produção**, sem uma linha alterada, rodado nesta sessão sobre
`input_roundtrip.json` e `input_candidate.json` dos dois projetos. Os 13
códigos e os 13 deltas reproduzem **exatamente** os do candidato (§7.2 e
§7.3).

### 4.1 Não são 16 identidades — é UMA

| | TGD | TP1 |
|---|---|---|
| achados `JUNCTION_NOT_ALTERNATING` | 16 → 32 (**+16**) | 0 → 16 (**+16**) |
| **nós físicos distintos** | 1 → 2 (**+1**) | 0 → 1 (**+1**) |
| achados por nó | 16 (= 17 fiadas → 16 pares consecutivos) | idem |

O nó novo é **o mesmo ponto físico nos dois níveis**:

```
TGD  (338.52 ; 187.05)          TP1  (8017.26 ; 1289.95)
     diferenca = [7678.7371 ; 1102.9024]  = a translacao documentada
```

O nó pré-existente no TGD — `(163.51; 237.05)` — **não é afetado** pela
CR-B: o solver já não alternava ali com a entrada antiga, e continua não
alternando. É defeito prévio, fora do escopo desta CR.

### 4.2 A medição decisiva — sem depender do agrupamento do validador

Todas as peças do projeto que alcançam o ponto, cota a cota:

| estado | fiadas com peça | donos distintos | alterna? |
|---|---|---|---|
| **alvenaria humana** STATE_R | 13 | 2 (`W056`↔`W017`) | **SIM** |
| **alvenaria humana** STATE_C | 13 | 2 (`W071`↔`W065`) | **SIM** |
| **solver sobre IN_R** | 17 | 2 (`W017`↔`W056`) | **SIM** |
| **solver sobre IN_C** | 17 | **1** (`W071` em **todas**) | **NÃO** |

*(TP1 idêntico: humano alterna nos dois estados; solver alterna em IN_R e
para de alternar em IN_C.)*

### 4.3 A geometria que muda a avaliação

```
IN_R  W056  [331.5, 187.0] -> [1270.5, 187.0]  L=939  juncoes: T, T
IN_C  W071  [331.5, 187.0] -> [1270.5, 187.0]  L=939  juncoes: L, L
```

**A parede E-O não muda de geometria** — muda o tipo de encontro nas duas
pontas, porque a parede N-S deixa de atravessar e passa a **terminar** no
nó (`W065` começa em `y=180,05`). O solver, que resolvia o `T` alternando,
passa a resolver o `L` com a peça sempre do mesmo lado.

### 4.4 Veredito

**O solver realmente deixou de alternar.** Não é associação incorreta do
validador nem artefato do gabarito novo:

- a medição ignora `collect_nodes` e usa todas as peças do projeto;
- o gabarito humano alterna corretamente **nas duas** topologias;
- o próprio solver alternava **neste mesmo nó** antes do corte.

Classificação: **(A/B) defeito real do solver, exposto — e neste caso
também *causado* — pela mudança de topologia da entrada.**

Reprodutor: `repro_solver_l_node_alternation.py` (reproduz nos 2
projetos, `exit 0`).

**Nesta sessão não foi alterada nenhuma regra `X`/`T`/`L`, nenhuma `B54`
foi forçada, nenhuma exceção de parede curta foi criada e nenhum hard
gate foi relaxado.** CR proposta: §10, CR-S1.

### 4.5 Contabilidade — correção obrigatória

`scoring.py:75` conta `critical_errors` por **severidade**, não por
nível. `JUNCTION_NOT_ALTERNATING` é `level=1` mas `severity=major`:
**ele não entra em `critical_errors`**. Confirmado nos números do
candidato (TP1: `327 = 14+9+18+286`, `262 = 9+9+244`).

Consequência: a queda `327 → 262` **não contém nenhuma piora de
amarração compensada**, porque a piora de amarração nunca esteve nessa
conta. Ela é invisível ali — o que torna **mais** grave, não menos,
tratá-la como custo diluído.

---

## 5. Reconciliação dos demais deltas

Toda a tabela abaixo é por **identidade física** (coordenada de mundo +
elevação), nunca por `W0xx` nem por índice de fiada.

### 5.1 Gabarito — validadores sobre a alvenaria humana (STATE_R → STATE_C)

| código | severidade | delta | novas | sumidas | classificação |
|---|---|---|---|---|---|
| `COVERAGE_GAP_IN_ROW` | major | **−47** | 54 | 101 | **A + D** — ver §5.2 |
| `COVERAGE_MISSING_ROW` | **critical** | **+17** | 26 | 9 | **C** — `expected_rows` é global |
| `COVERAGE_ROW_MOSTLY_EMPTY` | **critical** | **+23** | 38 | 15 | **C + D** — idem |
| `OPENING_MISSING_LINTEL` | major | **−12** | 2 | 14 | **A** — deixa de cobrar verga onde não há porta |
| `JUNCTION_MISSING_BINDING` | critical | **+49** | 82 | 33 | **C (39) + D (10)** — §3 |
| `PRISM_*` (3 códigos) | crit/major/minor | **0 / 0 / 0** | 0 | 0 | inalterado |
| `COMPENSATOR_*` (3 códigos) | major | **0 / 0 / 0** | 0 | 0 | inalterado |
| `POSITION_OVERLAP` | critical | **0** | 0 | 0 | **nenhuma colisão física nova** |
| `JUNCTION_HALF_BLOCK_ADJACENT` | major | **0** | 0 | 0 | inalterado |

`COVERAGE_MISSING_ROW` e `COVERAGE_ROW_MOSTLY_EMPTY` são **severidade
CRÍTICA** e sobem `+17`/`+23` no gabarito. Causa medida: `expected_rows`
é uma configuração **global do projeto**
(`validate_wall_coverage.py:259`), e as paredes filhas têm 13–14 fiadas
contra o alvo 17. Isso é **(C)**, com um resíduo de **(D)**: a agregação
da parede-mãe escondia que um dos trechos não sobe até a última fiada.

### 5.2 `COVERAGE_GAP_IN_ROW` em CENTÍMETROS, não em achados

Contar achados aqui engana: o mesmo buraco físico é **truncado** no
corte e vira outro achado. Medindo a **união dos segmentos** no mundo:

| | TGD | TP1 |
|---|---|---|
| cm cobrados só em STATE_R (deixam de ser cobrados) | **14409,0** | **14409,0** |
| **cm cobrados só em STATE_C (vazio NOVO)** | **0,0** | **0,0** |
| cm cobrados nos dois (mesmo lugar físico) | 82455,5 | 72569,9 |
| segmentos novos ≥ 5 cm | **0** | **0** |

**Zero centímetro de vazio novo no gabarito.** O `−47` é
reenquadramento + o miolo dos 19 vãos e as tiras de 15 cm deixando de ser
cobrados. Categoria **A + D**, sem componente negativa.

### 5.3 Solver — `IN_R × STATE_R` → `IN_C × STATE_C`

| código | severidade | delta | **novas** | **sumidas** | classificação |
|---|---|---|---|---|---|
| `COVERAGE_GAP_IN_ROW` | major | **−122** (TP1) / −101 (TGD) | 0 / 21 | 122 / 122 | **A**; em cm: TP1 **0,0 cm novo**; TGD (hipotético) 419,8 cm |
| `PRISM_CONTINUOUS_JOINT` | **critical** | **−42** | **28** | 70 | **A (70) + B (28) — ver §5.4** |
| `POSITION_OVERLAP` | **critical** | **−9** | **0** | 9 | **A** — 9 preservadas, **0 colisões físicas novas** |
| `COVERAGE_ROW_MOSTLY_EMPTY` | critical | **−14** | 0 | 14 | **A** |
| `PRISM_JOINT_STACK` | major | **−3** | 1 | 4 | **A** com resíduo |
| `PRISM_STAGGER_BELOW_TARGET` | **minor** | **+101** | 486 | 385 | **D/E** — nível 2, não reprova; churn alto |
| `COMPENSATOR_AVOIDABLE` | **minor** | **+17** | 28 | 11 | **E — INCONCLUSIVO**: o achado não emite coordenada; a chave degenera para a parede |
| `COMPENSATOR_CONSECUTIVE` | major | **−56** | 148 | 204 | **D** — churn de 148/204 num delta de 56 |
| `COMPENSATOR_EXCESS_IN_RUN` | major | **+6** | 153 | 147 | **D/E** — churn |
| `COMPENSATOR_VERTICAL_STRIP` | major | **−5** | 31 | 36 | **D** |
| `JUNCTION_NOT_ALTERNATING` | major | **+16** | 16 | 0 | **A/B — §4** |
| `JUNCTION_MISSING_BINDING` | critical | **0** | 0 | 0 | inalterado |

`POSITION_OVERLAP` foi reconciliado pela **coordenada dos blocos que
colidem** (uma chave só de parede daria "9 novas" falsas). Resultado
correto: **9 preservadas, 0 novas, 9 sumidas**.

### 5.4 O achado que o saldo `−42` escondia

`PRISM_CONTINUOUS_JOINT` é **severidade CRÍTICA**. Por identidade física:
**70 sumiram e 28 SÃO NOVAS** — em ambos os projetos.

```
parede W056 (E-O, L=939 cm; geometria IDENTICA em IN_R e IN_C)
  fiadas 7/8, desencontro 0,00 cm, juntas em t = 74,5 / 114,5 / 154,5 /
  194,5 / 234,5 / 274,5 ...  -> junta corrida em faixa
```

**22 das 28 estão em paredes cuja geometria NÃO mudou** — mudou o tipo
de encontro nas pontas (`T`→`L`), o que muda a zona reservada e reordena
toda a solução da parede.

Isto é a mesma causa raiz do §4, aparecendo num código **crítico**. O
relatório do candidato apresenta este item como `−42` limpo, na
categoria "(A) correção de artefato". **Não é.** É `−70 / +28`.

### 5.5 Saldo por severidade, por identidade física (TGD)

| severidade | identidades NOVAS | SUMIDAS | saldo |
|---|---|---|---|
| **critical** | **28** (todas `PRISM_CONTINUOUS_JOINT`) | 102 | **−74** |
| major | 724 | 867 | −143 |
| minor | 479 | 357 | +122 |

O saldo global continua favorável. **Ele não é o argumento**, e não foi
usado como argumento em nenhuma classificação acima.

---

## 6. Contrato de input — TGD e TP1

Reconferido diretamente nos arquivos oficiais (leitura apenas):

| | `torre_easy_lo_r00_tgd` | `torre_easy_lo_r00_tp1` |
|---|---|---|
| `input.json` → `metadata.derived_from` | `wall_modeling_snapshot.json` | **`reference.json`** |
| `metadata.source_kind` | "projeto CRU (CAD + aberturas), passado pelo Wall Modeling headless — **NENHUM bloco do gabarito foi lido**" | "projeto entregue e aprovado" |
| paredes | 167 | 96 |
| aberturas | 82, **todas `confidence="measured"`**, **82/82 com `source_element_id`** | 92, **todas `confidence="reconstructed"`**, **0 com `source_element_id`** |
| documento de origem | `TESTE MODULACAO (2026).rvt`, nível `00. 000` (**documento SEPARADO**) | o próprio gabarito |

**CONFIRMADO: o `input.json` do TGD é independente do gabarito humano e é
a única fonte medida do corpus.** A correção de escopo do candidato ao
plano §10.1 da reconciliação (que listava `*/input.json` no plural) está
**certa**.

### Contrato correto, para a CR de integração

1. **TGD — `input.json` PRESERVADO.** Regenerá-lo a partir de
   `reference.json` destruiria as 82 aberturas `measured` e as 167
   paredes do CAD. **PROIBIDO**, sem exceção. Regravar o gabarito do TGD
   **não muda a entrada do solver** — muda só o pareamento (84 → 98) e o
   `evaluation_scope`, e isso é **(C)**, nunca ganho de solver.
2. **TP1 — qualquer input reconstruído mantém proveniência explícita.**
   Conferido no candidato: os quatro `input_*.json` gerados trazem
   `derived_from`, `candidate_state`, `candidate_of`,
   `candidate_provenance`, `split_reason`, e **nenhuma** abertura marcada
   `measured` (0 `source_element_id` nos quatro). **Nada pode ser
   chamado de `MEASURED`** nesse caminho.
3. **Gabarito humano = referência de MODULAÇÃO**, não fonte automática de
   geometria medida. `reconstructed` nunca vira `measured` por
   regravação.
4. **Armadilha registrada:** o candidato também gera
   `torre_easy_lo_r00_tgd/input_candidate.json` com
   `derived_from = reference.json`. É **artefato de CONTROLE** (§7.3
   hipotético). Gravá-lo sobre o `input.json` oficial do TGD é
   exatamente a destruição do item 1 — vira gate explícito em §9.

**Nenhum arquivo oficial foi sobrescrito nesta sessão.**

---

## 7. D4 / D6 e dívida documental

### 7.1 D4 — texto exato e resolução

> **D4** (reconciliação §9): *"R1 (`W052`, sobra medida de 30,01cm), R2
> (`W006`/`W007`, par de paredes paralelas no CAD) e R3 (`W015`/`W017`,
> 193cm sem parede medida) — **conferir no Revit antes de gravar**, ou
> gravar com o valor humano e registrar a pendência?"*
> Evidência: *"são fatos medidos sem veredito; afetam onde a parede nova
> termina"*. Impacto: **médio**.

| | |
|---|---|
| **decisão solicitada** | conferir no Revit **antes** de gravar, ou gravar o valor humano com pendência rastreável |
| **evidência disponível** | as três divergências foram remedidas pelo candidato de forma independente: **30,007 cm**, **14,458 cm** (≈ uma espessura de 14,0 cm), **192,998 cm**. Nas três, o miolo do vão tem **0 blocos humanos**, **0 verga**, **0 procedência medida**, e as **6 jambas envolvidas estão confirmadas por geometria medida**. O roteiro de conferência (§6.5 do candidato) é concreto: documento, vista, nível, coordenada nos dois frames e parâmetros a ler |
| **resolução proposta** (candidato §9.5) | gravar o valor humano + campo `needs_revit_check` rastreável; conferência como CR curta, não como bloqueio |
| **posição desta revisão** | **CONCORDO**, com duas condições. (a) `needs_revit_check` tem de ser **campo gravado por abertura/parede**, consultável por script — não nota de rodapé. (b) A ressalva do próprio candidato sobre **R2** é real e precisa ficar visível: se a conferência mostrar parede dupla, dois dos 19 mudam **a geometria da jamba** (não a classificação), e a perpendicular `W045` do gabarito está no eixo errado. Isso é **retrabalho de geometria**, não rollback |
| **impacto** | R1 muda o comprimento de `W056`; R2 muda a largura de 2 vãos (101,0 → 86,5) e o eixo de uma perpendicular; R3 muda onde termina o trecho **depois** do vão. Nenhuma muda a classificação de nenhum dos 19 |
| **o que depende do usuário** | **tudo**: D4 não foi decidida, e esta revisão não a decide. Se o usuário preferir conferir antes, o candidato já está pronto e é determinístico — não há custo de espera |

### 7.2 D6 — texto exato, e uma CORREÇÃO ao candidato

> **D6** (reconciliação §9): *"Recuperar/regerar
> `docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` e
> `docs/C04_INDEPENDENT_FINAL_REVIEW.md`, ou corrigir as citações do
> `PROJECT_STATUS.md`?"* Evidência: *"os dois são citados como autoridade
> e não existem (§1.2)"*. Impacto: **baixo, mas é dívida documental real**.

**O candidato afirma (§1.2, §0 item 7, §11) que os dois documentos
"nunca foram commitados em nenhuma ref", com base em 153 commits
varridos. Isso está ERRADO.** Medido nesta sessão, depois de
`git fetch origin` (198 commits em todas as refs):

| documento | commit que adicionou | data | branch | em `main`? | linhas | veredito registrado |
|---|---|---|---|---|---|---|
| `docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` | `d8933cd` | 2026-09-07 06:15 | `origin/claude/opening-detector-review-cr-a-q8bhuk` | **não** | 335 | `APPROVE_WITH_EXPLICIT_CONDITIONS` |
| `docs/C04_INDEPENDENT_FINAL_REVIEW.md` | `418fba1` | 2026-09-07 02:16 | `origin/claude/c04-review-next-cr-prep-wc77d7` | **não** | 785 | `APPROVE_WITH_EXPLICIT_CONDITIONS` |

Os dois **existem**, são substanciais, e os vereditos batem **exatamente**
com o que o `PROJECT_STATUS.md` resume. A dívida não é "documento
inexistente" — é **"revisão feita, commitada e nunca mesclada na `main`"**.

**Causa provável do falso negativo:** o `git log --all` da sessão do
candidato rodou sobre um conjunto de refs locais incompleto (153 contra
198 commits). Esta revisão só encontrou os documentos **depois** de um
`git fetch origin` que trouxe as branches remotas.

*Resolução proposta, revista:*

1. **RECUPERAR, não reescrever.** `d8933cd` é **doc-only** (1 arquivo) —
   cherry-pick trivial, preservando a data original. Para `418fba1`
   (11 arquivos, 2338 linhas), recuperar **ao menos**
   `docs/C04_INDEPENDENT_FINAL_REVIEW.md`; os outros 9 arquivos
   (`FUTURE_BLOCK_CR_*`, `future_cr_preparation/*.py`) também **não
   estão em `main`** e merecem decisão própria.
2. **Não é preciso alterar as citações do `PROJECT_STATUS.md`** — elas
   apontam para o caminho certo. O que falta é o merge.
3. A recomendação anterior ("trocar cada citação por *relatório NÃO
   VERSIONADO*") **deve ser descartada**: registraria como perdida uma
   revisão que existe.

*Nada foi editado no `PROJECT_STATUS.md` nesta sessão* — o enunciado
proíbe, e agora a correção necessária é um merge, não uma edição de texto.

Evidência bruta: `evidence/documental_debt.json`.

### 7.3 Sobre as demais decisões

**D1, D2, D3, D5 não foram decididas nem influenciadas por esta revisão.**
D5 (promover `C1` a regra de domínio) continua com a recomendação
**NÃO** do candidato, e esta revisão concorda: dois níveis do mesmo
edifício não são amostra.

---

## 8. Registro de regra (`CLAUDE.md`)

Esta sessão **não alterou** `nuvem/REGRAS_MODULACAO_BLOCOS.md`, porque o
enunciado proíbe implementar regra de modulação aqui e porque a promoção
de `C1` depende de **D5**.

Conhecimento de **amarração** produzido aqui, que é registro obrigatório
assim que houver CR autorizada para escrever no arquivo de regras
(rótulo: **PADRÃO MEDIDO — DOCUMENTADO, pendência de código e de decisão
aberta**):

> **Amarração de nó `L` em ponta de parede — o solver não alterna.**
> Quando uma parede **termina** num nó `L` em vez de atravessá-lo, o
> solver resolve o encontro sempre com a peça da mesma parede, em todas
> as fiadas. A pessoa **alterna** no mesmo nó (13 fiadas, `B34` ↔ `B19`,
> trocando de dono a cada fiada), e o próprio solver **alternava** ali
> quando a parede atravessava (nó `T`, 17 fiadas, `W017` ↔ `W056`).
> **Como foi descoberto:** rodando o solver de produção sobre
> `input_roundtrip.json` e `input_candidate.json` do candidato CR-B, e
> medindo a ocupação do ponto `(338,52; 187,05)` (TGD) /
> `(8017,26; 1289,95)` (TP1) com **todas** as peças do projeto.
> Reprodutor: `repro_solver_l_node_alternation.py`.
> **DOCUMENTADO — pendência de código aberta (CR-S1).**

> **A junta corrida também piora quando o encontro vira `L`.**
> `PRISM_CONTINUOUS_JOINT` (crítico) ganha **28 identidades físicas
> novas** por projeto na saída do solver, **22 delas em paredes cuja
> geometria não mudou** — só o tipo do encontro nas pontas mudou de `T`
> para `L`, o que reordena a solução inteira da parede.
> **DOCUMENTADO — pendência de código aberta (CR-S1).**

---

## 9. Gates para a CR-B oficial de integração

Os gates de §9.3 do candidato são mantidos e **corrigidos/acrescidos**:

| # | gate | limiar | estado hoje |
|---|---|---|---|
| G1 | blocos humanos perdidos / novos / duplicados / órfãos | **= 0** nos quatro | ✔ verificado independentemente |
| G2 | `z`, centro `XY` e elevação de fiada por bloco | **idênticos** | ✔ 0 divergências |
| G3 | comprimento total | `Δ == −Σ(larguras removidas)` | ✔ −2604,0 exato |
| G4 | aberturas removidas com `source_element_id` | **= 0** | ✔ |
| G5 | aberturas mantidas com geometria alterada | **= 0** | ✔ (75/73 conferidas) |
| G6 | `POSITION_OVERLAP` **pela coordenada dos blocos** | **0 identidades novas** | ✔ 0 novas (a chave por parede daria 9 falsas) |
| G7 | `COVERAGE_GAP_IN_ROW` **em centímetros de união física** | **0 cm de vazio novo** | ✔ gabarito 0,0 cm; solver TP1 0,0 cm |
| G8 | determinismo do gerador | `sha256` idêntico | ✔ 4 processos independentes |
| G9 | ocupação física dos nós alterados | conjunto idêntico | ✔ 38/38 |
| G10 | **falha vertical de amarração em nó pré-existente** | **0 nós pioram** | ✔ 0 (8 melhoram) |
| **G11** | **`JUNCTION_MISSING_BINDING` recontado por ELEVAÇÃO** | delta **≤ 0** | ✔ **−5** (contra +49 na unidade de hoje) |
| **G12** | **`PRISM_CONTINUOUS_JOINT` (crítico) — identidades NOVAS** | **decisão explícita** | ✘ **28 novas por projeto** — hoje NÃO passa |
| **G13** | **`JUNCTION_NOT_ALTERNATING` — nós físicos novos** | **decisão explícita** | ✘ **1 nó novo** — hoje NÃO passa |
| **G14** | `input.json` do **TGD** byte-idêntico ao oficial | **obrigatório** | gate novo, não medido (nada foi gravado) |
| **G15** | nenhum input reconstruído com `confidence="measured"` ou `source_element_id` | **= 0** | ✔ nos quatro `input_*.json` do candidato |
| **G16** | `expected_rows` após o corte | **decisão explícita** | ✘ `+17` `MISSING_ROW` / `+23` `ROW_MOSTLY_EMPTY`, **ambos críticos** |
| **G17** | gabarito anterior lado a lado, versionado, com changelog | obrigatório | ✔ STATE_A / STATE_R / STATE_C existem |
| **G18** | `stable_key` gravado por parede + tabela de migração `W0xx` | obrigatório | ✔ medido (53/86 e 52/85 mudam de id), **não implementado** |
| **G19** | proveniência por abertura (`split_reason`, `needs_revit_check`) | obrigatório | parcial — `split_reason` existe, `needs_revit_check` não |
| **G20** | métricas históricas identificadas por VERSÃO do gabarito | obrigatório | não implementado |
| **G21** | `reference_score` recalibrado **só depois** de G1–G16 aprovados | obrigatório | — |
| **G22** | `baseline.json` preservado, salvo CR própria autorizada | obrigatório | ✔ intocado |
| **G23** | suíte completa: as **mesmas** falhas pré-existentes, 0 novas | obrigatório | não rodada (nenhum arquivo de produção tocado) |

**Não se exige que métricas de topologias diferentes sejam iguais em
valor absoluto.** Exige-se G6/G7/G10/G11 — identidade física — e
explicação escrita de cada mudança relevante.

**Proibido na CR de integração:** regravar `baseline.json` para esconder
regressão; criar tolerância global; `skip`/`xfail`; alterar threshold;
usar a queda de críticos como justificativa de classificação; mexer em
regra de amarração `L`/`T`/`X` sem decisão do usuário; regerar o
`input.json` do TGD.

**Rollback:** bloco humano some ou vira órfão; abertura `measured` muda
de geometria; aparece identidade nova em `POSITION_OVERLAP` (coordenada
de bloco) ou centímetro novo em `COVERAGE_GAP_IN_ROW`; o gerador deixa de
ser determinístico; nó pré-existente piora na falha vertical.

---

## 10. CRs separadas necessárias

Nenhuma delas foi implementada aqui.

| CR | escopo | reprodutor | bloqueia a integração? |
|---|---|---|---|
| **CR-V1 — fidelidade do validador de junções** | trocar a unidade de avaliação de `JUNCTION_MISSING_BINDING` / `JUNCTION_NOT_ALTERNATING` de **índice ordinal** para **elevação em cm**; e fazer `collect_nodes` juntar as paredes que **fisicamente** chegam ao nó, não só as que **declaram** a junção | `repro_junction_row_unit.py` | **SIM** — sem ela o `+49` não é interpretável, e o defeito já contamina 63% dos achados de hoje |
| **CR-S1 — amarração do solver em nó `L` de ponta** | o solver deixa de alternar quando a parede termina no nó (`+16` num nó) e ganha `+28 PRISM_CONTINUOUS_JOINT` críticos em paredes de geometria inalterada | `repro_solver_l_node_alternation.py` | **SIM** — é amarração e é crítico |
| **CR-C1 — `expected_rows` por parede** | `expected_rows` global contra paredes cortadas gera `+17`/`+23` de códigos **críticos** de cobertura | (medido em `reconciliation_run.txt`) | **SIM** |
| **CR-D1 — recuperar os dois relatórios de revisão** | `cherry-pick d8933cd` e o `docs/C04_INDEPENDENT_FINAL_REVIEW.md` de `418fba1`, com a data original | `evidence/documental_debt.json` | não |
| **CR-I1 — identidade estável** | `stable_key` gravado, tabela de migração `W0xx`, versionamento do gabarito e das métricas | §4.4 do candidato | **SIM** |
| **CR-M1 — coordenada nos achados de compensador** | `COMPENSATOR_AVOIDABLE` não emite coordenada; o `+17` é **inconclusivo** por construção | — | não, mas mantém (E) aberto |
| **CR-R1 — conferência Revit de R1/R2/R3** | roteiro pronto em §6.5 do candidato | — | depende de **D4** |

---

## 11. Decisão recomendada

**NÃO INTEGRAR A CR-B AINDA.** O candidato é sólido no que se propôs —
preservação demonstrada, determinismo real, nada oficial tocado — e esta
revisão **confirma** a preservação de forma independente. O que impede a
integração hoje não é o candidato: são três defeitos que ele **expôs** e
**não pode** corrigir sem sair do próprio escopo.

Ordem recomendada:

1. **CR-V1** (validador). Sem a unidade correta, `+49` e `+16` não são
   comparáveis com nada, e 63% dos achados de amarração do gabarito de
   hoje já são suspeitos.
2. **CR-S1** (solver, amarração em `L` de ponta + junta corrida). É o
   núcleo do sistema e é crítico.
3. **CR-C1** (`expected_rows` por parede).
4. **D1 + D2 + D3** pelo usuário. Só então a CR-B oficial, com G1–G23.
5. **CR-D1** e **CR-R1** em paralelo, sem bloquear.

Três correções de fato ao relatório do candidato, que a CR de integração
precisa carregar:

1. **§1.2 / §0.7 / §11 estão errados:** os dois relatórios de revisão
   **existem** e estão commitados; a dívida é de **merge**, não de
   existência. **D6 muda de resposta.**
2. **§7.5-A trata `PRISM_CONTINUOUS_JOINT −42` como artefato corrigido.**
   Por identidade física é **−70 / +28**, e as 28 são **críticas**.
3. **§7.5-B / §7.6 tratam `+101 STAGGER` e `+17 AVOIDABLE` como
   "defeito real do solver" no mesmo plano do `+16` de amarração.** Os
   dois primeiros são **nível 2 / severidade `minor`**; o terceiro é
   `major` e **não entra em `critical_errors`** — o que significa que a
   piora de amarração **não** foi compensada pelo saldo: ela é invisível
   nele.

**Nenhuma decisão D1–D6 foi tomada aqui. Nenhuma aprovação foi
presumida.**

---

## 12. Limitações declaradas

1. **Nenhuma medição no Revit ao vivo (MCP)** nesta sessão. Nenhuma foi
   inventada. R1/R2/R3 não foram remedidas — o roteiro de §6.5 do
   candidato foi lido e é aceito como suficiente para a CR de conferência.
2. A projeção do solver do **TGD** com entrada derivada do gabarito é
   **hipotética** (o TGD não deriva a entrada do gabarito). Onde TGD e
   TP1 divergem — `COVERAGE_GAP_IN_ROW`: 419,8 cm novos no TGD contra
   0,0 no TP1 — **vale o TP1**, que é o caso real.
3. `COMPENSATOR_*` não emitem coordenada suficiente para reconciliação
   por identidade (`COMPENSATOR_AVOIDABLE` não emite nenhuma). Os
   `+17`/`−56`/`+6`/`−5` ficam **(E) inconclusivos** por limitação do
   contrato de achado, não por falta de medição.
4. `PRISM_STAGGER_BELOW_TARGET` tem churn de 486/385 num delta de +101:
   o `+101` é real, mas **não** é "101 lugares novos" — é rearranjo.
5. A **suíte de testes completa não foi rodada**: nenhum arquivo de
   produção ou de teste foi tocado. Ela é gate da CR de integração
   (**G23**), não desta.
6. `piloto_sintetico_2x2` ficou fora, como nas duas sessões anteriores.
7. Esta revisão **não** avaliou o candidato com `evaluation_scope`
   recalculado, e **não** revalidou o critério `C1` — que continua
   heurística de extração deste corpus (**D5** aberta).

---

## Reprodução

```bash
export CR_B_OUT=/tmp/cr_b_candidate
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate
python3 build_candidate.py                       # gera STATE_R e STATE_C
cd ../bench_opening_reconstruction_b_reconciliation
python3 repro_junction_row_unit.py               # §3 - defeito do validador
python3 repro_solver_l_node_alternation.py       # §4 - defeito do solver
python3 reconcile_by_physical_identity.py        # §3, §5 - tabelas completas
```

Saída conferida desta sessão: `evidence/reconciliation_run.txt`,
`evidence/reconciliation_physical_identity.json`,
`evidence/documental_debt.json`.
