# Laboratório de auditoria independente — modulação de blocos (CONTA 2)

Auditoria **independente** do estado da modulação de blocos na `main`
baseline (`9f3bab41b35f0e2a5f9782583ead8e1ee7755f49`), feita em paralelo
ao `CR-BLOCK-01` (CONTA 1, sobre prisma/fiadas) e **sem ler a branch da
CONTA 1**. Ver o produto principal desta auditoria em
[`docs/BLOCK_MODULATION_AUDIT.md`](../../../docs/BLOCK_MODULATION_AUDIT.md)
e o relatório de dados em
[`../RELATORIO_BASELINE_BLOCOS.md`](../RELATORIO_BASELINE_BLOCOS.md).

## Contrato desta pasta

- **Só leitura** do motor (`nuvem/core/wall_modeling.py`,
  `nuvem/core/engine/**`) e da infraestrutura de benchmark já existente em
  `nuvem/benchmark/*` (reaproveitada via `import`, nunca copiada nem
  editada).
- **Nenhum arquivo fora desta pasta é escrito.** Em particular, nenhum
  script aqui grava em `nuvem/benchmark/projects/**` — todo `run_solver`
  desta pasta chama a ponte oficial (`benchmark.solver_bridge`) com
  `write_files` implicitamente desligado (os scripts nunca chamam
  `runner.run_project(..., write_files=True)`).
- **100% headless.** Sem MCP, sem Revit aberto — roda sobre os projetos já
  versionados em `nuvem/benchmark/projects/` (`torre_easy_lo_r00_tgd`,
  `torre_easy_lo_r00_tp1`, `piloto_sintetico_2x2`), usando os mesmos dubles
  de Revit que `tests/solver_bench.py` e o benchmark oficial usam
  (`tests/revit_stubs.py`).
- **Não corrige nada.** Nenhum script aqui muda uma regra, uma tolerância
  ou uma constante do motor — só mede e classifica o que já existe.
- Métrica que genuinamente não dá pra obter headless é marcada
  `"NOT_HEADLESS_OBSERVABLE"` no JSON — nunca inventada.

## Projeto principal do censo

`torre_easy_lo_r00_tgd` — é o único dos três projetos de benchmark cujo
`input.json` é **medido** (extraído via MCP de um Revit real), não
reconstruído a partir do próprio gabarito (ver
`nuvem/benchmark/README.md`, seção "Baseline REAL"). Os outros dois
(`torre_easy_lo_r00_tp1`, `piloto_sintetico_2x2`) entram como comparação
de escala no resumo consolidado, não no censo detalhado.

## Arquivos

| Arquivo | O que faz | Item da missão |
|---|---|---|
| `lib_audit.py` | biblioteca compartilhada: carrega/roda o solver, converte geometria pé→cm, fingerprint canônico por peça, spans ao longo do eixo da parede | infra |
| `run_course_bond_census.py` | prisma/fiadas: coincidência de junta entre fiadas físicas consecutivas, stagger, soluções alternativas por variante | 8, 22 (leve) |
| `run_special_block_census.py` | C09, C04, B19, B34, B54: contagem, sequências consecutivas, faixa vertical repetitiva, distância a abertura/nó | 9-13, 19 |
| `run_intersection_census.py` | encontros L/T/X: classificação TRUE/DEGRADED/sem solução, chama `solve_*`/`validate_*` de produção como objeto de estudo numa amostra | 14-16 |
| `run_opening_census.py` | portas/janelas, censo independente de bloco-dentro-de-vão por EXTENT real (com filtro de banda vertical), cross-check contra `classify_extent_against_openings` | 17-18 |
| `run_coverage_census.py` | paredes não moduladas com ranking de causa, + performance/hotspots | 21, 23 |
| `run_determinism_census.py` | roda o solver de blocos várias vezes (ordem invertida, embaralhada com 5 seeds, endpoints invertidos) e compara fingerprints | 20 |
| `run_full_census.py` | orquestra todos acima sobre o projeto principal, roda os dois projetos secundários em resumo, escreve `out_full_census.json` | 7 (consolidado) |
| `out_*.json` | saídas geradas (reproduzíveis — rodar de novo sobre a mesma `main` reproduz os mesmos números, exceto onde a própria medição é sobre variação de ordem) | — |

## Como rodar

```bash
cd nuvem/benchmark/diagnostics_block_audit
python3 run_full_census.py            # tudo, ~40s
python3 run_course_bond_census.py     # só prisma
python3 run_special_block_census.py   # só C09/C04/B19/B34/B54
python3 run_intersection_census.py    # só L/T/X
python3 run_opening_census.py         # só aberturas
python3 run_coverage_census.py        # só paredes nao moduladas + performance
python3 run_determinism_census.py     # só determinismo (roda o solver 8x, ~30s)
```

Cada script aceita um `project_id` opcional como primeiro argumento
posicional (default `torre_easy_lo_r00_tgd`):

```bash
python3 run_coverage_census.py torre_easy_lo_r00_tp1
```

## Metodologia — pontos importantes para ler os números certo

- **"Materializado" = `course_candidates`, nunca `candidates` bruto.** O
  agregado `solve_result["candidates"]` mistura TODAS as variantes/bandas
  que o solver considerou — nunca coexistem de verdade numa fiada física.
  Todo censo usa `lib_audit.physical_course_candidates`, que é exatamente
  o que `create_building_blocks` materializaria no Revit (já passou por
  `_drop_fill_colliding_with_ties`, regra 18.7).
- **Prisma é medido só entre peças PARALELAS ao eixo da própria parede**
  (`x_dir` colinear a `wall_dir`, `dot >= 0.99`). Uma peça de nó travada a
  90° faz parte da sequência da parede VIZINHA, não desta.
- **"Bloco dentro do vão" respeita a banda vertical da fiada** (seção 4 das
  REGRAS): uma abertura só é vazio na faixa Z real do seu vão — comparar
  contra TODAS as aberturas da parede sem filtrar por fiada superestima
  muito o achado (a primeira versão deste censo tinha esse bug: 660+1222
  → 5+108 depois do filtro; ver histórico do commit).
- **`RULE_AMBIGUOUS`**: quando a documentação não deixa claro se um caso é
  exceção (ex.: junta perto de abertura mas não comprovadamente encostada
  na borda), o caso fica marcado como ambíguo e o dado bruto é preservado
  — nunca promovido a violação nem descartado.
- **Determinismo do solver de BLOCOS é uma pergunta DIFERENTE do
  determinismo do motor de PAREDES** (CR-2F-D, já resolvido e mergeado).
  Este censo permuta a ordem das paredes já resolvidas (`input.json`,
  saída da Fase A) e mede o resultado do grafo de nós +
  `solve_building_blocks_all_courses` — uma camada acima do que o CR-2F-D
  cobriu. Ver `docs/BLOCK_MODULATION_AUDIT.md`, seção Determinismo, para o
  resultado e a camada exata onde a primeira divergência aparece.
