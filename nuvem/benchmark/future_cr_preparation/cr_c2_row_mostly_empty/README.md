# CR-C2 — diagnóstico de `COVERAGE_ROW_MOSTLY_EMPTY` após divisão de paredes

> **Nada aqui é gabarito oficial e nada aqui é patch.** Esta pasta contém
> apenas os **diagnósticos reprodutíveis** da CR-C2 e da revisão
> independente da CR-C1. `nuvem/benchmark/projects/**`
> (`reference.json`, `input.json`, `baseline.json`,
> `reference_score.json`, `evaluation_scope.json`), o solver
> (`nuvem/core/engine/**`) e os validadores estão **intocados** por esta
> branch — conferido por `git diff --name-only`.

## Como reproduzir

Todo script recebe a **árvore** a medir e o diretório do candidato:

```bash
# 1. reproduzir o candidato CR-B (gerador determinístico da branch
#    claude/candidato-validacao-gabarito-q450yr, commit 5640933)
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate
export CR_B_OUT=/tmp/cr_b_candidate
python3 build_candidate.py

# 2. medir (ARVORE = raiz de um worktree; CR_B_OUT = saída do passo 1)
python3 <script>.py <ARVORE> $CR_B_OUT
```

## Índice

### Revisão independente da CR-C1 (Fase 1)

| script | o que mede |
|---|---|
| `silence.py` | cobertura de `height_cm` e **folga física** de cada parede do gabarito — prova que o 95/94→0 não vem de falta de dado |
| `indep_c1.py` | 14 casos discriminantes **independentes** dos testes da própria CR-C1 (rodam em qualquer árvore) |
| `g16.py` | delta `STATE_R → STATE_C` dos códigos de cobertura |

### CR-C2 (Fase 2)

| script | o que mede |
|---|---|
| `c2_diag.py` | os `+23` por identidade física; refuta a hipótese "fiada vazia" |
| `c2_case.py` | disseca um caso mãe→filho (parede de 1344cm dividida) |
| `c2_phys.py` | **vazios físicos em coordenada global** R × C + teste de contenção |
| `c2_unit.py` | quais achados de C recaem sobre região física já acusada em R |
| `c2_four.py` | disseca os 4 achados residuais (paredes de 169cm) |
| `c2_grid.py` | achados em fiada do passo do grid × **faixa de verga/peitoril** |
| `c2_opts.py` | simulação diagnóstica das opções de correção (**não** é patch) |
| `c2_unidade.py` | **a prova**: STATE_C reavaliado na unidade de parede de STATE_R |

### Reavaliação G12/G16 e contrato (Fases 3 e 4)

| script | o que mede |
|---|---|
| `gates.py` | todos os hard gates, delta R→C, no gabarito |
| `ident.py` | deltas por identidade física usando o **eixo da parede** (mostra por que essa chave é inválida sob divisão) |
| `ident2.py` | deltas por **coordenada global** (chave que sobrevive à divisão) |
| `g12.py` | **G12 na saída do SOLVER** — identidades novas de `PRISM_CONTINUOUS_JOINT` |
| `g18.py` | G18: `stable_key` sem ambiguidade, round-trip, blocos humanos, aberturas medidas |
| `junc.py` / `junc2.py` | `JUNCTION_MISSING_BINDING` por identidade física; efeito da chave incluir o tipo do nó |

## Aviso sobre a chave de identidade

`ident.py` e `ident2.py` existem em par de propósito. Sob **divisão de
parede**, a chave "eixo da parede" reporta **49 identidades novas** de
`PRISM_CONTINUOUS_JOINT` onde a coordenada global reporta **0** — a mesma
junta física muda de eixo sem mudar de lugar. Do mesmo modo, incluir o
**tipo do nó** na chave de `JUNCTION_MISSING_BINDING` reporta 26
identidades novas onde `(ponto, elevação)` reporta 10, porque a divisão
converte nós `T` em nós `L`. **Nenhuma conclusão desta pasta usa `W0xx`
como identidade.**
