# Beta Revit: "Preparando o solver..." travado na bancada de 2 paredes

```json
{
  "date": "2026-09-09",
  "scope": "current",
  "branch": "claude/revit-solver-perf-diagnosis-6dfd89",
  "head": "0ffa8e98bffb0efe3723f2b07f376a9a1e473a73",
  "base": "aa58d70d84c6134216f8f15a131edf060c4dce81",
  "pr": "not-created",
  "objective": "Descobrir onde o tempo e gasto entre o clique em 'Iniciar Modulacao das Paredes' e o primeiro resultado util do solver, na bancada de 2 paredes / 1 encontro em L / 0 aberturas do primeiro beta controlado (8cdd33f), com causa medida e nao hipotetica.",
  "changes": [
    "Nenhuma alteracao de algoritmo, formula, tolerancia, regra normativa, benchmark, baseline ou gabarito. O modelo do Revit nao foi tocado: todo acesso via MCP foi leitura, sem Transaction, sem criar/mover/apagar elemento e sem salvar o RVT.",
    "Acrescentado core/engine/perf_trace.py (modulo puro, sem Revit e sem UI) e sondas [PERF] no caminho real do botao em core/wall_modeling.py e core/engine/wall_stepper.py. As sondas sao no-op enquanto perf_trace.enable() nao for chamado e cada uma esta protegida por try/except; a saida vai para um arquivo porque o sintoma e justamente a UI nao atualizar."
  ],
  "tests": [
    "tests/test_script.py: 260 passed em 68.55s (py -m pytest tests/test_script.py -q), gate nomeado no CLAUDE.md, com a instrumentacao ja aplicada.",
    "Bancada offline com dubles (CPython 3.14.6): _execute_solve 0.010s, _execute_analyze 0.002s; grafo 3 nos, 1 L_CORNER, 2 FREE_END, 0 aberturas.",
    "Motor carregado DENTRO do processo do Revit com XYZ/Line reais: frio import 2.036s, build 1.202s, solve 6.669s, analyze 0.336s; quente build 0.000s, solve 0.026s, analyze 0.012s.",
    "Reproducao fiel do caminho do botao sobre o documento real (mesma montagem de run_modulation_on_existing_walls): refresh_geometry_from_document 0.187s + _execute_analyze 0.181s = 0.37s, 0 linhas de erro, catalogo real com 6 codigos e 8 celulas.",
    "Pacote beta instrumentado gerado e verificado: C:\\Users\\CIVIX\\.codex\\artifacts\\beta-perf-diag-0ffa8e9-20260909, head 0ffa8e98bffb0efe3723f2b07f376a9a1e473a73."
  ],
  "known_failures": [
    "CAUSA-RAIZ AINDA NAO FECHADA. Todas as etapas sob suspeita foram medidas e nenhuma reproduz os minutos relatados; falta a medicao do caminho REAL do botao (ExternalEvent + engine CPython/pythonnet do pyRevit + WinForms), que so pode ser obtida com um clique do usuario no pacote instrumentado. Nao ha correcao implementada nem tempo antes/depois.",
    "A reproducao dentro do Revit rodou no engine IronPython do servidor MCP; o botao roda no engine CPython (cpyengine=3123, shebang '#! python3' em Script.py). A diferenca de interop pythonnet nao foi medida e continua sendo a variavel nao coberta.",
    "A pasta do botao registrada no pyRevit (userextensions) nao contem beta-package.json nem core/, e o espelho pkg_cache foi reescrito por sincronizacao online em 2026-09-09 16:36, depois da criacao do pacote 8cdd33f (14:36). Nao foi possivel confirmar por arquivo qual arvore de codigo produziu a execucao lenta relatada."
  ],
  "physical_deltas": [
    "Nenhum. Nenhuma regra fisica, tolerancia ou geometria esperada foi alterada; a bancada continua 2 paredes, 0 aberturas, 17 fiadas e 187 blocos esperados.",
    "Entrada real x artefato offline: CONGRUENTES. Comprimentos 69.0024/354.0007cm contra 69.0/354.01cm, espessura 14cm, altura 340cm, sobreposicao do L de 6.9959cm contra 7.0cm, base absoluta 612cm nos dois. Nenhum erro de unidade (feet/cm), nenhum Z incorreto, nenhuma coordenada global inflada.",
    "Grafo de encontros medido: 3 nos, 1 L_CORNER, 2 FREE_END, 2 candidatos de intersecao, 0 falhas. Nenhum residuo das 126 paredes / 77 aberturas da execucao anterior."
  ],
  "decisions_taken": [
    "O benchmark offline de 0.1-1.1s NAO cobre o caminho do botao: ele exercita _execute_solve (acao 'solve'), e o botao 'Iniciar Modulacao das Paredes' define handler.action = 'analyze'. Os dois numeros nao sao comparaveis e o de 'solve' nao pode ser usado como expectativa da Tela 1.",
    "Solver descartado como causa por medicao direta, nao por argumento: no documento real, com catalogo real e XYZ/Line reais, analyze custa 0.181s e a etapa silenciosa anterior ao primeiro callback (solve_all_intersections) custa milissegundos.",
    "Hipotese 'XYZ real do Revit e lento' REFUTADA por micro-benchmark: XYZ() 0.877us, DotProduct 0.659us, contra 2.111us de uma classe Python equivalente.",
    "Instrumentar antes de corrigir: nenhuma otimizacao foi feita sem hotspot provado, conforme pedido."
  ],
  "decisions_pending": [
    "Executar UMA vez o pacote instrumentado na MESMA bancada e ler %LOCALAPPDATA%\\MeuBotaoPushbutton\\perf_diag.log; a distancia entre 'ui.external_event.Raise CHAMADO' e 'Execute ENTROU' separa latencia de despacho do ExternalEvent de trabalho real, e fecha a causa-raiz.",
    "Decidir se a janela 'Preparando o solver...' passa a ter ponto de cancelamento: hoje solve_all_intersections, _index_node_candidates_* e order_walls_for_processing nao consultam should_cancel_cb, e o botao Cancelar so tem efeito a partir do laco por parede.",
    "Tratar em CR proprio o achado de origem Z: run_modulation_on_existing_walls usa base_z_abs = Level.Elevation e ignora WALL_BASE_OFFSET (1718.164cm nesta bancada, base real 612cm). E correcao fisica, fora do escopo deste diagnostico.",
    "Definir se o gate operacional desta bancada (<5s aceitavel, 5-15s investigar, 15-60s ruim, >60s falha) vira criterio registrado do beta."
  ],
  "next_steps": [
    "Rodar o beta instrumentado na copia descartavel, com as mesmas 2 Walls (5390468 e 5390548), sem ampliar o recorte e sem iniciar modulacao do projeto inteiro.",
    "Anexar perf_diag.log como evidencia versionada, apontar a etapa dominante e so entao propor a correcao minima, com teste de regressao que falhe antes e passe depois.",
    "Nao mesclar na main: este checkpoint cobre instrumentacao de diagnostico, nao correcao aprovada."
  ],
  "references": [
    {"path": "docs/checkpoints/evidence/2026-09-09-preparing-solver-measurements.json"},
    {"path": "docs/checkpoints/evidence/main-safe-engineering-input.json"},
    {"path": "docs/checkpoints/evidence/main-safe-handler-bench-run.json"},
    {"path": "nuvem/core/engine/perf_trace.py"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "docs/checkpoints/2026-09-09-beta-main-safe.md"}
  ]
}
```

## O que foi medido, e nao suposto

Todos os numeros abaixo estao em
[evidencia](evidence/2026-09-09-preparing-solver-measurements.json).

### 1. Estado real confirmado no Revit

Documento `TESTE MODULACAO`, 33.044 elementos, e exatamente **2 Walls**:

| Wall | Comprimento | Espessura | Altura | Base offset | Nivel |
| --- | --- | --- | --- | --- | --- |
| 5390468 | 354,0007 cm | 14 cm | 340 cm | 1718,164 cm | pb |
| 5390548 | 69,0024 cm | 14 cm | 340 cm | 1718,164 cm | pb |

0 portas, 0 janelas, 0 `DB.Opening`, 0 modelos genericos, 0 pilares.
Nenhuma terceira Wall. O eixo vertical cruza o horizontal com 7 cm de
sobreposicao em cada ponta - o L legitimo, ja esticado ate as faces.

### 2. O caminho do clique, com os nomes reais

```
_WallReviewForm._on_start_click            (thread de UI)
  -> console.set_indeterminate("Preparando o solver...")   <-- texto que trava
  -> ExternalEvent.Raise()
       ~~~ latencia de despacho: Revit so roda o handler quando fica ocioso ~~~
  -> _PostCreationEventHandler.Execute()   (thread PRINCIPAL do Revit)
       -> globals().update(self._g)
       -> uiapp.ActiveUIDocument
       -> _refresh_geometry_from_document(app_doc)
       -> _execute_analyze(app_doc)
            -> System.Threading.Thread(_worker)            (thread de fundo)
                 -> analyze_created_walls_for_errors
                      -> process_walls_one_by_one
                           -> solve_all_intersections      <-- etapa silenciosa
                           -> _index_node_candidates_*
                           -> order_walls_for_processing
                           -> wall_start_cb  ==> primeira linha "ANALISAR: eixo ..."
```

`"Preparando o solver..."` e emitido em
[wall_modeling.py](../../nuvem/core/wall_modeling.py) dentro de
`_on_start_click`, imediatamente antes de `ExternalEvent.Raise()`. A
proxima linha de codigo executada e o proprio `Raise()`; nada entre ele e
`wall_start_cb` escreve no log. Essa e a janela cega inteira.

### 3. Onde o tempo NAO esta

| Etapa | Offline (dubles) | Revit, frio | Revit, quente |
| --- | --- | --- | --- |
| `_execute_solve` | 0,010 s | 6,669 s | 0,026 s |
| `_execute_analyze` | 0,002 s | 0,336 s | 0,012 s |
| `solve_all_intersections` | 0,002 s | - | ms |

Reproducao fiel sobre o documento real, com catalogo real:
`_refresh_geometry_from_document` 0,187 s + `_execute_analyze` 0,181 s =
**0,37 s**, 0 linhas de erro. O catalogo real tem os mesmos 6 codigos e 8
celulas do sintetico - nao ha explosao combinatoria.

O padrao dominante e **primeira chamada**: `load_fixed_block_catalog`
custou 8,793 s na primeira vez e 0,330 s na segunda, no mesmo processo.

### 4. Divergencia de caminho (o achado que muda a leitura do beta)

O replay offline registrado em
[main-safe-handler-bench-run.json](evidence/main-safe-handler-bench-run.json)
chama `h._execute_solve()`. O botao chama `analyze`. Os 0,1-1,1 s medidos
pelo beta offline descrevem outra etapa do pipeline, com dubles de XYZ, em
CPython, fora do Revit - nao a Tela 1.

### 5. Cancelamento

`_cancel_requested` so e consultado via `should_cancel_cb` a partir do laco
por parede de `process_walls_one_by_one`. `solve_all_intersections`,
`_index_node_candidates_*`, `order_walls_for_processing`,
`_refresh_geometry_from_document` e a espera do ExternalEvent **nao tem
ponto de cancelamento**. Enquanto a tela mostra "Preparando o solver...",
o botao Cancelar apenas marca a flag - documentado, nao corrigido aqui.

### 6. Watchdog

`SOLVER_SLOW_WARNING_SECONDS = 8.0`, `SOLVER_WATCHDOG_INTERVAL_MS = 3000`.
Uma parada real acima de 8 s produz, no log da Tela 1, linhas
`Ainda processando (Ns sem atualizacao) - elemento atual: Preparando o
solver...`. Elas sao a medida direta da duracao e devem ser lidas como
evidencia, nao descartadas como ruido.

## Limitacoes

Este checkpoint entrega instrumentacao e a eliminacao medida de seis
hipoteses; **nao entrega causa-raiz fechada nem correcao**. O engine
CPython/pythonnet do pyRevit, onde o botao realmente roda, nao foi medido -
a reproducao dentro do Revit usou o engine IronPython do servidor MCP.
