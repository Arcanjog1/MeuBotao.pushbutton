# RELATÓRIO FINAL — CR-BENCH-Z-ORIGIN

> Este CR e' exclusivamente de infraestrutura de BENCHMARK.
> Produção alterada: **ZERO**. `wall_stepper.py`, `wall_pairing.py`,
> `continuous_modulation.py`, `modulation_math.py`, `geometry.py`,
> `wall_modeling.py`, `tolerances.py`: **intactos**.
> `baseline.json` / `reference.json` / `reference_score.json`: **não
> tocados**. **NENHUM MERGE FEITO.**

## Git

```
branch deste CR: claude/cr-bench-z-origin-42vxcx
base:            origin/main @ 21add6ec1f6cad220bdf3ff8651adb90b63d6e1b
                 (mesmo commit da branch antes de qualquer alteração)
```

## Bug

O benchmark (`nuvem/benchmark/extract/from_solver.py::project_from_solver`)
reconstrói a cota Z de cada fiada com uma fórmula diferente da que o
motor usa para posicionar as peças de verdade. As duas convenções
concordam em tudo, exceto num detalhe que muda TUDO: o offset da
primeira fiada.

## Convenção vertical do motor

`nuvem/core/wall_modeling.py::_course_z_abs` (produção, só LIDA neste
CR, nunca reescrita):

```python
FIRST_COURSE_Z_OFFSET_CM = 1.0   # (linha 3977 do motor)

def _course_z_abs(base_z_abs, course_index, course_height_ft):
    return base_z_abs + _cm_to_ft(FIRST_COURSE_Z_OFFSET_CM) + course_index * course_height_ft
```

A Fiada 1 (`course_index=0`) NÃO nasce em `base_z_abs` — nasce 1cm
acima (junta de assentamento entre a base/contrapiso e o primeiro
bloco), regra confirmada ao vivo no Revit em 2026-08-21 (ver comentário
no próprio motor). Esta mesma fórmula também decide, dentro do
`solve_building_blocks_all_courses`, em qual fiada física uma abertura
está ativa (`_course_z_band`/`_group_course_indices_by_opening_band`) —
ou seja, o próprio SOLVER já usa a convenção com offset para decidir
onde recortar cada abertura.

## Convenção vertical antiga do benchmark

`nuvem/benchmark/extract/from_solver.py::project_from_solver` (antes
deste CR):

```python
elevation_cm = base_z_cm + course_index * course_step_cm
```

Sem `FIRST_COURSE_Z_OFFSET_CM`. `base_z_cm` vem do MESMO `base_z_abs_ft`
que o runner (`nuvem/benchmark/runner.py::run_project`) passa ao
solver — ou seja, as duas fórmulas partem exatamente da mesma origem
`base_z_abs`, e só divergem por esse offset de 1cm perdido.

Enquanto isso, `sill_cm`/`head_cm` das aberturas (`_openings_for_wall`)
continuam vindo direto do dado bruto (`openings_per_wall`, medido no
Revit real ou repassado do `input.json`) — ou seja, no Z ABSOLUTO
correto (o mesmo que o motor usa). O modelo do benchmark misturava
duas réguas: fiadas 1cm "cedo demais", aberturas na régua certa.

## Causa-raiz

Localizada em UM único ponto:
`nuvem/benchmark/extract/from_solver.py`, dentro do laço de
`project_from_solver` que monta `rows` por parede — a linha que
calcula `elevation_cm` para cada `course_index` nunca somava
`FIRST_COURSE_Z_OFFSET_CM`.

## Fix

Uma única fórmula nova, central, em `nuvem/benchmark/analysis.py` (o
módulo que já espelha deliberadamente constantes de produção para
poder rodar sobre JSON puro, sem os dublês do Revit — mesmo padrão de
`BLOCK_JOINT_CM`, `PIER_MODULE_CM` etc., guardado por
`tests/regression/test_engine_constants_match.py`):

```python
# nuvem/benchmark/analysis.py
FIRST_COURSE_Z_OFFSET_CM = 1.0    # espelha core/wall_modeling.py

def course_z_abs_cm(base_z_cm, course_index, course_step_cm_value):
    """Mesma formula/convencao do motor (_course_z_abs), em cm."""
    return base_z_cm + FIRST_COURSE_Z_OFFSET_CM + course_index * course_step_cm_value
```

`from_solver.py` passa a chamar essa única função em vez de repetir a
conta local:

```python
# nuvem/benchmark/extract/from_solver.py
elevation_cm = analysis.course_z_abs_cm(base_z_cm, course_index, course_step_cm)
```

`FIRST_COURSE_Z_OFFSET_CM` foi adicionada à lista `MIRRORED` de
`tests/regression/test_engine_constants_match.py`, que importa o motor
de verdade e falha se os dois valores algum dia divergirem — a mesma
rede de segurança que já protege as outras 18 constantes espelhadas.

**Sem hardcode**: nenhum número mágico (1cm, 221cm, "fiada 11"),
nenhum ID de parede/porta/projeto entra na lógica do fix. A fórmula é
genérica em `base_z_cm`, `course_index` e `course_step_cm` — funciona
para qualquer base elevation, qualquer curso, qualquer pavimento,
qualquer projeto (testado explicitamente com base negativa/subsolo,
ver seção Testes).

## Reprodução (antes de qualquer alteração)

`nuvem/benchmark/diagnostics_bench_z_origin/reproduce_before.py` monta
uma peça e uma porta sintéticas (nenhuma dependência do NODE-FILL) e
chama `from_solver.project_from_solver` de verdade — sem
reimplementar a fórmula. Rodado ANTES do fix, contra o código
original de `main`:

```
MOTOR (_course_z_abs, produção, só lida): fiada 10 = 201.00 .. 220.00 cm
porta: head_cm = 201.00 cm  (fisicamente TANGENTE à fiada - overlap físico = 0)

BENCHMARK (from_solver.project_from_solver, real, sem fix): fiada 10 = 200.00 .. 219.00 cm

DIFERENÇA (motor - benchmark) = 1.00 cm  (= FIRST_COURSE_Z_OFFSET_CM)

validate_openings.validate_wall(...) achados: ['OPENING_BLOCK_INSIDE_DOOR', 'OPENING_MISSING_LINTEL']
  -> FANTASMA: a peça só TOCA o head da porta, mas o benchmark (sem fix)
     a via ENTRANDO no vão.
```

Depois do fix, o mesmo script (mantido no repositório, agora como
regressão executável — os `assert` finais viraram "diferença tem que
ser ZERO" / "sem achado fantasma de overlap") dá:

```
MOTOR: fiada 10 = 201.00 .. 220.00 cm
BENCHMARK (com fix): fiada 10 = 201.00 .. 220.00 cm
DIFERENÇA = 0.00 cm
achados: ['OPENING_MISSING_LINTEL']   (esperado - nenhuma peça de verga no cenário, nada a ver com Z)
overlap de abertura: nenhum
```

## Tangência = overlap zero

Coberto por `test_peca_que_apenas_toca_o_head_da_porta_tem_overlap_zero`
(`tests/test_bench_z_origin.py`): uma peça cujo `origin_world`/base
está posicionada exatamente no `head_cm` da porta (`row["elevation_cm"]
== opening["head_cm"]`) não pode gerar `OPENING_BLOCK_INSIDE_DOOR` nem
`OPENING_BLOCK_CROSSES_JAMB` — a checagem em
`analysis.opening_active_in_row`/`validate_openings.py` já usa
comparação estrita (`<`, não `<=`) nos dois limites, então bastava a
origem Z estar correta para a tangência parar de virar overlap
fantasma. Contraprova no mesmo arquivo
(`test_peca_que_realmente_invade_o_vao_continua_sendo_achado`): uma
peça que REALMENTE cai dentro do vão continua sendo achado depois do
fix — o fix não apaga overlap real junto com o fantasma.

## Métricas afetadas — auditoria completa

Todas as métricas abaixo dependem, direta ou indiretamente, de
`row["elevation_cm"]` (via `analysis.opening_active_in_row`,
`active_opening_intervals`, `_row_covering_elevation` ou
`modulable_intervals`). Medido rodando os 3 projetos reais
(`piloto_sintetico_2x2`, `torre_easy_lo_r00_tgd`,
`torre_easy_lo_r00_tp1`) com `runner.py --run <id>` (sem
`--save-baseline`), comparando o `score.json` novo contra o
`baseline.json` antigo (NÃO tocado):

**Prova de que o SOLVER não mudou**: contagem de paredes idêntica nos
3 projetos (12/167/96); a pequena variação de contagem de blocos entre
a rodada e o `baseline.json` antigo (piloto 768→772, tgd 10657→10647,
tp1 18092→18088) é **PRÉ-EXISTENTE e não-relacionada a este CR** —
reproduzida rodando o código SEM o fix (`git stash` das 3 alterações):
o mesmo drift aparece (piloto 768→772 idêntico), confirmando que
`baseline.json` já estava desatualizado em relação ao `main` atual
antes deste CR sequer começar (`main` avançou desde a última vez que
alguém rodou `--save-baseline`). Classificado como **UNRELATED**.

| projeto | métrica | OLD baseline | NEW measurement | delta | causa |
|---|---|---:|---:|---:|---|
| tgd | `OPENING_BLOCK_INSIDE_DOOR` | 45 | **5** | −40 | **BENCHMARK_MEASUREMENT_FIX** |
| tgd | `OPENING_BLOCK_CROSSES_JAMB` | 147 | 108 | −39 | **BENCHMARK_MEASUREMENT_FIX** |
| tgd | `COVERAGE_ROW_MOSTLY_EMPTY` | 171 | 129 | −42 | **BENCHMARK_MEASUREMENT_FIX** |
| tgd | `COVERAGE_GAP_IN_ROW` | 1944 | 1935 | −9 | **BENCHMARK_MEASUREMENT_FIX** |
| tgd | `COVERAGE_PARTIAL_WALL` | 56 | 59 | +3 | **BENCHMARK_MEASUREMENT_FIX** |
| tgd | `OPENING_MISSING_LINTEL` | 82 | 82 | 0 | (sem mudança) |
| tgd | critical_errors | 1671 | 1291 | −380 | **BENCHMARK_MEASUREMENT_FIX** (soma dos achados acima) |
| tp1 | `OPENING_MISSING_LINTEL` | 92 | **0** | −92 | **BENCHMARK_MEASUREMENT_FIX** (ver seção própria abaixo — achado já era estruturalmente inválido) |
| tp1 | `OPENING_BLOCK_CROSSES_JAMB` | 168 | 168 | 0 | (sem mudança) |
| tp1 | `COVERAGE_GAP_IN_ROW` | 289 | 293 | +4 | **BENCHMARK_MEASUREMENT_FIX** |
| tp1 | critical_errors | 1205 | 1074 | −131 | **BENCHMARK_MEASUREMENT_FIX** |
| piloto | (nenhuma métrica vertical mudou) | — | — | 0 | — |

Nenhuma linha é `REAL_SOLVER_CHANGE` — o solver não foi tocado e o
censo de peças por parede é idêntico (fora o drift pré-existente de
`baseline.json`, classificado `UNRELATED` acima). Nenhuma linha é
`UNKNOWN`: toda mudança tem explicação mecânica rastreada até
`row["elevation_cm"]`.

## TGD — `OPENING_BLOCK_INSIDE_DOOR`

```
baseline (régua errada):  45
medido agora (régua certa): 5
```

Confirma exatamente o que o diagnóstico do NODE-FILL já havia
apontado (commit `bf4054b` naquela branch, não alterado por este CR):
as 40 ocorrências a mais eram peças que só TOCAVAM o head da porta
(nasciam exatamente onde a verga termina), classificadas como "dentro
do vão" só porque a fiada do benchmark nascia 1cm cedo demais.

## CROSSES_JAMB

`OPENING_BLOCK_CROSSES_JAMB` (tgd): 147 → 108 (−39). Mesma causa
mecânica: uma peça cujo overlap real com o vão era pequeno (por
tangência incorreta) caía na faixa "atravessa a jamba" em vez de "sem
overlap". Nenhuma peça nova entra na lista; a régua só para de contar
overlap onde não existe.

## OPENING_MISSING_LINTEL

`tp1`: 92 (baseline) → **0**. Investigado a fundo (item 10 do CR
original) — a causa **não é só a origem Z corrigida**, é um achado
COMPOSTO de dois problemas:

1. **`block_role()` (`from_solver.py`) nunca atribui
   `model.ROLE_LINTEL`/`ROLE_CHANNEL_BLOCK`** a nenhuma peça extraída
   do solver — esses papéis só existem no vocabulário de `model.py`
   para dados HUMANOS (`reference.json`). `PLACEMENT_REASON_TO_ROLE`
   não tem entrada nenhuma que resulte nesses dois papéis. Isso é
   **pré-existente, não introduzido por este CR** e está fora do
   escopo (mexer em `block_role()`/papéis de peça não é "origem Z").
2. **Boundary check da procura de verga**
   (`validate_openings._row_covering_elevation`) usa intervalo
   meio-aberto `[row_lo, row_lo+height)`. Medido nas 92 aberturas do
   TP1: os `head_cm` reais caem **exatamente** na fronteira entre duas
   fiadas (ex.: `head_cm=872.0`, fiada 12 = `[853,872)`, fiada 13 =
   `[873,892)` — 872 não está em NENHUM dos dois intervalos, cai
   exatamente na junta de 1cm entre fiadas, por DESENHO do sistema
   construtivo).

**Antes do fix** (régua errada, todas as fiadas 1cm "cedo"), o mesmo
`head_cm=872` caía DENTRO do intervalo deslocado de alguma fiada
(medido: 92/92 aberturas encontravam alguma fiada) → `head_row` não
era `None` → como nenhuma peça tem papel de verga (item 1 acima),
`OPENING_MISSING_LINTEL` disparava **sempre** (92 = 100% das aberturas
do TP1). **Depois do fix** (régua certa), `head_cm` cai exatamente na
junta entre fiadas para as 92/92 aberturas → `_row_covering_elevation`
devolve `None` para todas → o achado é **pulado silenciosamente**
(`if head_row is not None:` em `validate_openings.py`) → 0.

**Conclusão**: o baseline antigo de 92 já era um artefato da origem
errada (100% de falso-positivo — o achado nunca refletiu ausência real
de verga, só a coincidência da régua errada com o layout de fiadas). O
0 atual TAMBÉM não é uma medição confiável de "toda porta tem verga" —
é o sintoma de uma limitação pré-existente e diferente
(`_row_covering_elevation` não sabe procurar verga quando o head cai
exatamente na junta, e `block_role()` nunca marca papel de verga a
partir do solver). **Registrado aqui como achado, não corrigido neste
CR** (fora de escopo: não é "origem Z", é lógica de busca/papel de
peça — mexer nisso é uma decisão de produto separada). Sugestão de
tarefa futura enviada via `spawn_task` (ver final do relatório).

`tgd` não mostra esse efeito (`OPENING_MISSING_LINTEL` 82→82,
inalterado) — os `head_cm` de TGD não caem sistematicamente nas
junções fiada-a-fiada como em TP1.

## COVERAGE (vertical)

`COVERAGE_ROW_MOSTLY_EMPTY` (tgd): 171 → 129 (−42). Mesma causa:
`modulable_intervals`/`active_opening_intervals` decidem quais fiadas
"deveriam" estar cobertas com base em `row["elevation_cm"]"; a régua
errada classificava fiadas como parcialmente vazias por overlap
fantasma com abertura. `COVERAGE_GAP_IN_ROW` também se move nos dois
projetos (tgd −9, tp1 +4) pela mesma cadeia — nenhuma novidade fora
dessas 4 métricas de cobertura.

## Reference Corpus

`py -3 nuvem/benchmark/tools/run_reference_corpus.py --all`
(`--reference baseline --current score`, os defaults), rodado depois
do fix:

```
IMPROVED: 1 (piloto_sintetico_2x2)
NEUTRAL: 0
REGRESSED: 0
MIXED: 2 (torre_easy_lo_r00_tgd, torre_easy_lo_r00_tp1)
NOT_COMPARABLE: 2 (os dois ANALYSIS_ONLY, sem dado executável)

OVERALL: MIXED — sem regressão crítica em nenhum projeto comparável.
```

Matriz projeto × métrica: `openings` **IMPROVED** em tgd, `prism`
**IMPROVED** nos 3 projetos comparáveis (efeito de `analysis.py`
compartilhado — `course_step_cm`/`block_height_of` não mudaram, mas
alguns achados de prisma também consultam posição vertical de junta
via `row["elevation_cm"]`), `compensators` IMPROVED em tgd/tp1,
`coverage`/`L-T-X`/`collisions`/`non_modular` **UNCHANGED** nos 3.
Nenhum `CRITICAL_REGRESSION_PRESENT`.

`score.json`/`reports/*.txt` gerados durante a auditoria foram
restaurados com `git checkout` depois de capturar os números acima —
`git status` fica limpo (mesmo padrão do CR-BLOCK-NODE-FILL-JOINT).

## Baselines afetados

**NÃO ATUALIZADOS.** `baseline.json` de nenhum dos 3 projetos foi
tocado (`git status` confirma). Tabela completa na seção "Métricas
afetadas" acima — toda linha computada como `NEW measurement` veio de
`runner.py --run <id>` **sem** `--save-baseline`.

## Testes

`tests/test_bench_z_origin.py` (novo, 18 testes, todos headless):

```
course_z_abs_cm bate com o motor (_course_z_abs) — fiada 0/1/5/10/27
course_z_abs_cm bate com o motor — base_elevation 0 / 305.5 / -12.0 (subsolo)
primeira fiada nasce em base + offset, uma única vez
offset da primeira fiada aplicado uma única vez (passo entre fiadas = course_step, nunca +offset de novo)
row elevation do projeto extraído bate com o motor — fiada 0/1/8
peça que só TOCA o head da porta -> overlap ZERO (teste crítico do item 11 original)
peça que REALMENTE invade o vão -> achado continua existindo (contraprova)
janela usa a mesma origem vertical da porta
lintel: _row_covering_elevation acha a fiada que o motor realmente usou
ordenação de endpoint da parede é irrelevante para a origem Z
```

Confirmado que os testes REALMENTE discriminam: rodados contra o
código sem o fix (`git stash` das 3 alterações), **15 de 18 falham**
com o valor antigo (ex.: `assert 200.0 == 201.0 ± 1e-6`); com o fix,
**18/18 passam**.

Suítes existentes, sem alteração de comportamento esperado:

```
tests/test_golden_benchmark.py ................ 90 passed
tests/regression/test_engine_constants_match.py  23 passed (+1: FIRST_COURSE_Z_OFFSET_CM)
tests/ -m "not slow" .......................... 498 passed
tests/ (árvore inteira, incl. slow) ........... 509 passed, 0 failed
```

## Performance

`from_solver.project_from_solver` isolado (TGD real, warmup 5 +
mediana de 50 chamadas):

```
SEM fix: 217.26 ms/chamada
COM fix: 218.30 ms/chamada   (+0,5% — ruído de medição, não custo real)
```

O fix acrescenta uma soma e uma chamada de função por fiada por
parede — custo desprezível frente ao resto da extração. "Praticamente
grátis", como o item 17 exigia.

## Arquivos alterados

```
nuvem/benchmark/analysis.py                              +constante e função course_z_abs_cm
nuvem/benchmark/extract/from_solver.py                   1 linha (usa analysis.course_z_abs_cm)
tests/regression/test_engine_constants_match.py          +1 constante na lista MIRRORED
tests/test_bench_z_origin.py                             NOVO — 18 testes
nuvem/benchmark/diagnostics_bench_z_origin/reproduce_before.py   NOVO — reprodução/regressão executável
docs/BENCH_Z_ORIGIN.md                                    NOVO — este relatório
```

## Arquivos de produção alterados

```
ZERO.
```

Confirmado: `nuvem/core/**` (incluindo `wall_stepper.py`,
`wall_pairing.py`, `continuous_modulation.py`, `modulation_math.py`,
`geometry.py`, `wall_modeling.py`, `tolerances.py`) sem nenhuma
diferença contra `origin/main`.

## Validação contra NODE-FILL

Per item 15 do CR original / item 11 da retomada: a branch
`claude/cr-block-node-fill-joint-9tv0kd` (SHA `bf4054b`, não alterada
por este CR — commit de topo é o próprio diagnóstico que motivou este
CR) foi usada só como leitura, num `git worktree` separado. O fix de
Z-origin (`analysis.py`+`from_solver.py`) foi copiado para dentro
desse worktree **sem commit** (arquivos locais apenas), os 3 projetos
rodados com o `runner.py` de LÁ (que já inclui o fix do NODE-FILL em
`wall_stepper.py`), e o worktree descartado depois via `git worktree
remove` — nenhuma alteração permanece na branch NODE-FILL.

```
                          esperado (relatório NODE-FILL)   medido agora (Z corrigido)
tgd  PRISM_CONTINUOUS_JOINT      562 -> 318                        318   ✓
tp1  PRISM_CONTINUOUS_JOINT      730 -> 169                        169   ✓
piloto PRISM_CONTINUOUS_JOINT     14 -> 0                        (ausente = 0)  ✓
tgd  OPENING_BLOCK_INSIDE_DOOR    45 -> 49 (regressão suspeita)      5   ✓ (== MAIN com fix)
```

**Confirmado**: com a régua corrigida, o NODE-FILL preserva o ganho de
prisma (mesmos números do relatório original) e a "regressão" de
`OPENING_BLOCK_INSIDE_DOOR` (45→49) **desaparece por completo** — o
mesmo valor (5) que a `main` corrigida mede. Ou seja: o NODE-FILL
nunca introduziu violação física nova de abertura; o que existia era
só o mesmo defeito de régua deste CR, medido sobre o resultado do
NODE-FILL.

## Veredito

```
G1  origem Z incorreta reproduzida .......... APROVADO (reproduce_before.py, sem NODE-FILL)
G2  causa localizada no benchmark ........... APROVADO (from_solver.py, 1 linha)
G3  solver permanece intocado ............... APROVADO (diff de produção = zero)
G4  benchmark usa convenção do motor ........ APROVADO (analysis.course_z_abs_cm)
G5  sem hardcode ............................. APROVADO (nenhum número/ID mágico na lógica)
G6  tangência = overlap zero ................. APROVADO (teste dedicado + contraprova)
G7  consumidores verticais auditados ......... APROVADO (7 métricas, tabela completa)
G8  TGD/TP1/piloto reavaliados ............... APROVADO
G9  baselines não atualizados ................ APROVADO (baseline.json intocado nos 3)
G10 testes sintéticos passam ................. APROVADO (18/18, discriminam de verdade)
G11 NODE-FILL reavaliado como validação ...... APROVADO (prism preservado, INSIDE_DOOR 45→49 vira 5=5)
G12 production code diff = ZERO .............. APROVADO
```

**PARE ANTES DO MERGE** — como o CR pede. Nenhum push para `main`,
nenhuma PR aberta, nenhum baseline regravado. A decisão de regenerar
`baseline.json`/`reference.json` para refletir a régua corrigida (e a
investigação separada de `OPENING_MISSING_LINTEL`, item próprio acima)
fica para o usuário decidir depois deste relatório.
