# Benchmark, aprendizado e regressão da modulação

Infraestrutura para transformar **projeto Revit já entregue e aprovado**
em **base de referência estruturada, mensurável e reutilizável** — e para
medir objetivamente se o solver está melhorando ou piorando.

> Este pacote **não faz parte do botão**. O loader (`Script.py`) só baixa
> `nuvem/core/**`; `nuvem/benchmark/` é ferramenta de desenvolvimento,
> roda em CPython comum, fora do Revit, sobre arquivos JSON.

## O ciclo

```
projeto Revit correto
   └─ extract/revit_dump.py  (READ-ONLY, dentro do Revit via MCP)
      └─ dump bruto .json
         └─ extract/reconstruct.py  (puro)
            ├─ reference.json   ← a solução humana
            └─ input.json       ← o problema, sem nenhuma peça

input.json
   └─ solver_bridge.py → solve_building_blocks_all_courses (SOLVER REAL)
      └─ extract/from_solver.py
         └─ result.json      ← mesmo schema do gabarito

result.json
   ├─ validators/     → achados classificados (nível 1 / nível 2)
   ├─ comparator/     → diferenças contra o gabarito (NÃO veredito)
   ├─ scoring.py      → score por categoria e por parede, críticos à parte
   └─ report.py       → relatório + baseline × nova versão
```

## Comandos

```bash
py -3 nuvem/benchmark/runner.py --list
```

```bash
py -3 nuvem/benchmark/runner.py --run torre_easy_lo_r00_tp1
```

```bash
py -3 nuvem/benchmark/runner.py --all --save-baseline
```

```bash
py -3 nuvem/benchmark/runner.py --all --check
```

`--check` sai com código 1 se algum projeto regrediu contra o baseline ou
tem erro crítico — é o modo para CI/pré-commit.

```bash
py -3 nuvem/benchmark/runner.py --all --calibrate
```

Roda os validadores **no próprio gabarito** e grava o piso de ruído (ver
abaixo).

```bash
py -3 -m pytest tests/regression -q
```

## Wall Modeling (Etapa 2A) - FASE A

Premissa arquitetural (confirmada antes da Etapa 2A, vale para toda sessao
futura): **a Revit Wall nativa NAO e' entrada do solver - e' so'
materializacao**. `Wall.Create` acontece dentro de uma `Transaction`, bem
depois de tudo que decide geometria. O Wall Modeling de verdade - o que
calcula os EIXOS, os NOS de encontro (L/T/X) e qual abertura pertence a
qual parede - roda ANTES de qualquer `Transaction`, sobre linhas de CAD e
dicts de abertura, e e' isso que o solver consome (`nodes`,
`walls_to_create`, `end_to_node`, `openings_per_wall`). Nenhum arquivo de
entrada do benchmark deve exigir Wall nativa.

```
input_real.json
   └─ wall_modeling_bridge.run_wall_modeling()   (headless, mesma ordem da producao)
      │   merge_collinear_fragments -> find_wall_pairs -> deduplicate_walls
      │   -> extend_wall_ends_to_junctions -> build_wall_graph
      │   -> assign_openings_to_walls
      └─ extract/wall_modeling_snapshot.py
         └─ wall_modeling_snapshot.json
            └─ (proxima etapa) solver_bridge.run_solver -> result.json
```

`wall_modeling_bridge.py` reutiliza DIRETO as funcoes de
`core/engine/geometry.py`/`core/engine/wall_pairing.py` (via
`solver_bridge.engine()`, o mesmo motor carregado com os dubles de
`tests/revit_stubs.py`) - nao reimplementa nenhuma regra geometrica, nao
abre `Transaction`, nao acessa `doc`, nao cria Wall.

`setup_frozen` (dentro de `input_real.json`) e' a versao CONGELADA das
escolhas que `ask_setup` faz interativamente no botao real (layer,
espessuras, nivel, altura, `openings_mode`, `wall_mode`) - o benchmark
nunca pode depender de um clique. Campos obrigatorios: `layer`,
`thicknesses_cm`, `openings_mode`, `wall_mode`, `level`, `base_z_cm`,
`wall_height_cm`. Falta um deles -> `WallModelingBridgeError` explicito,
nunca um default silencioso (um default errado mudaria a geometria).

`wall_modeling_snapshot.json` grava as paredes DEPOIS de
`extend_wall_ends_to_junctions` (`settings.walls_already_extended: true`,
respeitado por `solver_bridge.plan_from_input` - sem isso a mesma ponta
seria esticada duas vezes) e guarda tambem a geometria de ANTES da
extensao (`walls[].before_extension`), os nos do grafo L/T/X/FREE_END, as
aberturas ja atribuidas por parede e as linhas do Layer que NAO viraram
parede (`unused_lines[].reason`, reconstruido geometricamente depois do
fato, sem mexer na assinatura de `find_wall_pairs`).

```bash
py -3 nuvem/benchmark/runner.py --run <project_id> --wall-modeling-only
```

roda so' a FASE A (le' `input_real.json`, grava
`wall_modeling_snapshot.json`) - sem o solver de blocos.

**Limitacao explicita desta etapa:** a extracao REAL de `input_real.json`
a partir de um projeto Revit (via MCP) e a execucao do pipeline completo
(`wall_modeling_snapshot -> solver -> result.json`) ficam para a proxima
sessao. Nesta etapa so' o CONTRATO e os testes headless foram
implementados.

## Como extrair um projeto correto

1. Abrir o `.rvt` no Revit (`open_document`, `detach=True` se workshared).
2. Gerar o código do extrator e rodá-lo via MCP:

```bash
py -3 -c "import sys; sys.path.insert(0,'nuvem'); from benchmark.extract import revit_dump; print(revit_dump.build_code('PREFIXO DO DOC', '05. TP1'))"
```

   Passar a saída como `code` para `mcp__revit-pyrevit__execute_revit_code`.
   O script **não abre nenhuma Transaction** e só escreve um `.json` no
   `%TEMP%` — o contrato de segurança está no cabeçalho de
   `extract/revit_dump.py`.
3. Ler o `.json` do caminho impresso (`OUT_PATH=...`).
4. Converter:

```python
from benchmark.extract import reconstruct
from benchmark import model
ref = reconstruct.build_project(dump, "meu_projeto")
model.save(ref, "nuvem/benchmark/projects/meu_projeto/reference.json")
model.save(reconstruct.input_from_reference(ref),
           "nuvem/benchmark/projects/meu_projeto/input.json")
```

5. Escrever `metadata.json` (origem, nível, confiabilidade, limitações).
6. `runner.py --run meu_projeto --save-baseline`.

## Como adicionar outro projeto

Mesma sequência acima. Um projeto = uma pasta em `projects/` com
`input.json` + `metadata.json`; `reference.json` é opcional (sem ele o
benchmark ainda roda os validadores de nível 1, só não compara).

Depois de 2+ projetos de referência, os padrões passam a valer como
"padrão de escritório":

```bash
py -3 -c "import sys; sys.path.insert(0,'nuvem'); from benchmark import model, patterns; print(patterns.format_report(patterns.learn([model.load('nuvem/benchmark/projects/A/reference.json'), model.load('nuvem/benchmark/projects/B/reference.json')])))"
```

## Nível 1 × nível 2 — regra obrigatória × preferência

| | |
|---|---|
| **Nível 1 — obrigatório** | prisma, vão livre, amarração válida, sem sobreposição, cobertura, geometria válida, limites de compensador. **Falhar aqui é erro.** |
| **Nível 2 — preferência** | peça escolhida, sequência, quantidade de compensadores, solução preferencial. **Divergir do projeto humano não é erro** se todo o nível 1 passar. |

O nível é propriedade da **classe de erro**, definida uma única vez em
`validators/base.py`. `knowledge/error_classes.json` é **gerado** a partir
dali — nunca editado à mão.

## Piso de ruído — por que o gabarito não tem zero achado

Rodar os validadores no **projeto humano aprovado** é parte do método, não
curiosidade. Todo achado que aparece nele é ou (a) limitação da
reconstrução geométrica, ou (b) validador exigindo mais do que o
escritório de fato pratica. Nos dois casos é o **piso de ruído** daquele
validador.

Sem esse piso, "o solver tem 968 erros de prisma" não significa nada. Com
ele:

```
CLASSE DE ERRO                            SOLVER    HUMANO  LEITURA
COMPENSATOR_CONSECUTIVE                     1567        52  solver 30.1x o humano
PRISM_CONTINUOUS_JOINT                       968       122  solver 7.9x o humano
COVERAGE_GAP_IN_ROW                          289       615  ruído do validador
JUNCTION_MISSING_BINDING                       8       365  ruído do validador
```

Uma linha em que o humano "erra mais" que o solver é sempre um sinal sobre
o **validador** (ou sobre a reconstrução), nunca sobre o projetista.

## Identidade sem ElementId

`ElementId` muda entre arquivos e some quando as paredes de referência são
apagadas — que é exatamente o que o processo real faz. Todas as chaves
aqui são geométricas (`model.wall_stable_key` e família), e o casamento
gabarito × resultado é por tolerância geométrica
(`comparator/match.py`), em três níveis: pontas iguais → mesma reta com
sobreposição → sem par (registrado, nunca casado à força).

## Validadores disponíveis

| Validador | Cobre |
|---|---|
| `validate_prism` | junta vertical corrida entre fiadas consecutivas, faixa vertical de juntas, desencontro abaixo do alvo |
| `validate_compensators` | compensadores consecutivos, excesso no trecho, faixa vertical, uso evitável (nível 2) |
| `validate_junctions` | L/T/X: existe amarração, alterna entre fiadas, meio-bloco encostado, peça diferente da humana (nível 2) |
| `validate_openings` | bloco dentro de porta/janela, bloco atravessando jamba, fiada abaixo do peitoril, verga e contraverga |
| `validate_wall_coverage` | parede não modulada, fiada faltando, fiada quase vazia, buraco fora de vão, blocos órfãos |
| `validate_block_positions` | sobreposição, peça fora da parede, desvio do eixo, orientação, comprimento incoerente |

Cada um é independente: nenhum chama outro, nenhum depende da ordem. Um
validador que levanta exceção aparece em `validator_errors` e no
relatório — **nunca** é engolido, porque um validador quebrado devolveria
lista vazia, que se parece com "nenhum erro".

## Nada aqui usa IA como validador

Toda regra que dá para conferir com geometria ou aritmética está em
código determinístico. A IA serve para descobrir padrão, interpretar
diferença e investigar causa — a validação final é sempre calculada.

## Limitações atuais (explícitas)

- **O gabarito do projeto piloto é RECONSTRUÍDO.** O `.rvt` entregue não
  tem mais `Wall` nem `Door`/`Window` (0 de cada): eixos, vãos e encontros
  vêm do layout dos blocos. As aberturas saem com
  `confidence: "reconstructed"`. Um projeto que ainda tenha paredes
  nativas dá um gabarito bem mais fiel — o extrator já lê os dois.
- **Células (furos) das peças não são extraídas** nesta rodada
  (`EdgeLoops`); `solver_bridge` as reconstrói simetricamente e registra
  isso em `solver_notes.cells_reconstructed`. O que se perde é o
  alinhamento fino de célula de B34/B54.
- **O solver só conhece 6 códigos.** O projeto real tem 33 tipos
  (canaleta, canaleta J, verga, contraverga, cortado, vedação). O
  benchmark entrega ao solver o catálogo dele e registra o resto em
  `solver_notes.catalog_codes_dropped` — é escopo pendente, não erro de
  modulação. Sem esse filtro o solver recusa o catálogo inteiro
  ("alturas diferentes") e gera zero peça.
- **Um projeto de referência só.** `patterns.py` nunca promove nada a
  `PREFERENCIAL` com menos de 2 projetos — com um só, tudo sai
  `OBSERVADO`.
- **Detecção de encontros não testa cruzamento eixo×eixo**, só
  ponta×eixo. Duas paredes que se cruzam sem que nenhuma termine ali
  ainda não viram nó.

## Próximos passos

1. Extrair um segundo projeto (e um com paredes nativas ainda presentes),
   para os padrões saírem de `OBSERVADO` para `PREFERENCIAL`.
2. Atacar os dois maiores desvios medidos, nessa ordem:
   compensadores (30× o humano) e prisma (7,9×).
3. Reduzir o piso de ruído de `COVERAGE_GAP_IN_ROW` e
   `JUNCTION_MISSING_BINDING` melhorando a reconstrução de encontros.
4. Extrair as células reais das peças (`EdgeLoops`) na próxima extração.
5. Ligar `runner.py --all --check` num hook de pré-commit.
