# Beta Revit: Etapa 5 travada - acao "create" perdida no ExternalEvent

```json
{
  "date": "2026-09-09",
  "scope": "current",
  "branch": "claude/revit-solver-perf-diagnosis-6dfd89",
  "head": "686320a70cf07fa079246b376751455b002ce908",
  "base": "aa58d70d84c6134216f8f15a131edf060c4dce81",
  "pr": "not-created",
  "objective": "Descobrir onde o tempo e gasto entre o clique em 'Iniciar Modulacao das Paredes' e o primeiro resultado util, na bancada de 2 paredes / 1 encontro em L / 0 aberturas do primeiro beta controlado (8cdd33f), com causa medida e nao hipotetica; corrigir apenas o hotspot provado.",
  "changes": [
    "Nenhuma alteracao de algoritmo, formula, tolerancia, regra normativa, benchmark, baseline ou gabarito. Nenhum auditor foi silenciado. Todo acesso ao modelo via MCP foi leitura.",
    "core/engine/perf_trace.py (modulo puro, sem Revit e sem UI) e sondas [PERF] no caminho real: clique, latencia do ExternalEvent, Execute, refresh de geometria, analyze, solve e todo o caminho de criacao (preflight, TransactionGroup, Activate+Regenerate, Transaction, progresso/ultima peca, laco, Commit, rollback, resultado).",
    "CORRECAO MINIMA em _PostCreationEventHandler.Execute(): a acao passa a ser CONSUMIDA no inicio e despachada por copia local, em vez de zerada no `finally`. Isso preserva a acao que um callback agenda DURANTE o proprio Execute()."
  ],
  "tests": [
    "tests/test_script.py: 262 passed em 67.81s (260 anteriores + 2 novos de regressao).",
    "test_beta_atomic_creation.py + test_controlled_beta_preflight.py: 50 passed.",
    "Regressao verificada nos DOIS sentidos: revertendo somente a correcao (mantendo a instrumentacao), test_acao_agendada_por_callback_durante_execute_sobrevive e test_execute_despacha_pela_acao_do_inicio_mesmo_se_callback_trocar FALHAM; com a correcao, passam.",
    "Bancada offline com dubles: _execute_solve 0.010s, _execute_analyze 0.002s. Reproducao fiel dentro do Revit sobre o documento real: refresh 0.187s + analyze 0.181s = 0.37s.",
    "Pacote beta corrigido construido e verificado a partir da PASTA DO BOTAO: head 686320a70cf07fa079246b376751455b002ce908."
  ],
  "known_failures": [
    "PENDENCIA FISICA ABERTA - WALL_BASE_OFFSET: no fluxo de paredes existentes, base_z_abs = selected_level.Elevation e ignora WALL_BASE_OFFSET. Na bancada, o nivel 'pb' esta em -1106.16cm e as Walls tem offset de base de 1718.164cm (base real 612cm). Como o caminho de criacao usa course_offset = course_z_abs - base_z_abs, base_z_abs se CANCELA e as pecas nascem em level.Elevation + 1cm + n*20cm - ou seja, 1718.164cm ABAIXO da base das paredes. A posicao Z das pecas NAO esta aprovada e nao pode ser aprovada por esta entrega.",
    "PENDENCIA FISICA ABERTA - REPEATED_VERTICAL_COMPENSATOR_STRIP: o solve desta bancada reprovou 1 parede na auditoria de amarracao entre fiadas. Por decisao de 2026-08-26 isso nao bloqueia a criacao (as pecas saem marcadas em vermelho), e NADA foi silenciado aqui. Continua sendo reprovacao fisica em aberto.",
    "A execucao pos-correcao ainda nao foi feita: tempo de criacao, quantidade criada e repetibilidade do beta seguem sem medicao.",
    "A suite consolidada nao foi concluida nesta sessao (interrompida duas vezes de proposito, para nao contaminar o arquivo de rastreamento que a medicao no Revit usa)."
  ],
  "physical_deltas": [
    "Nenhum. Nenhuma regra fisica, tolerancia ou geometria esperada foi alterada; a bancada continua 2 paredes, 0 aberturas, 17 fiadas e 187 blocos esperados.",
    "Estado do modelo apos a execucao instrumentada: 0 FamilyInstance de bloco criada (as 52 existentes sao carimbos/legendas). A Etapa 5 nunca chegou a rodar.",
    "Entrada real x artefato offline: CONGRUENTES (69.0024/354.0007cm, espessura 14cm, altura 340cm, sobreposicao do L 6.9959cm, base absoluta 612cm). Sem erro de unidade e sem Z incorreto NA ENTRADA - o erro de Z esta na criacao, nao na captura.",
    "Grafo: 3 nos, 1 L_CORNER, 2 FREE_END, 2 candidatos, 0 falhas, sem residuo das 126 paredes / 77 aberturas."
  ],
  "decisions_taken": [
    "CAUSA-RAIZ FECHADA e nao e lentidao: a acao 'create' era PERDIDA. _execute_solve chama on_done('solve') de dentro de Execute(); o callback _on_solve_done encadeia _on_create_click -> _raise_action('create'), que define handler.action='create' e Raise(); o `finally` de Execute() apagava essa acao; o despacho seguinte entrava com action=None, nao casava com nenhum ramo, nao chamava on_done e voltava em silencio.",
    "Latencia do ExternalEvent MEDIDA e descartada: 47ms entre 'ui.external_event.Raise CHAMADO' (+0.126s) e 'Execute ENTROU action=analyze' (+0.173s). No encadeamento solve->create foram 12ms (+6.561s -> +6.573s).",
    "Solver descartado por medicao: analyze 0.065s, solve 0.255s e 0.136s na execucao real dentro do Revit.",
    "Laco de criacao auditado e LIMPO: nenhum Regenerate por bloco, nenhuma busca de familia/tipo nem varredura global por bloco (o symbol vem do catalogo pronto), Activate+Regenerate uma unica vez fora do laco. Nao havia hotspot de criacao a otimizar.",
    "O benchmark offline de 0.1-1.1s exercita _execute_solve; o botao dispara analyze e depois encadeia create. Os numeros nunca foram comparaveis.",
    "docs/checkpoints/2026-09-09-beta-main-safe.md reclassificado para 'historical' porque o HEAD avancou; nenhuma afirmacao, numero ou decisao dele foi alterada."
  ],
  "decisions_pending": [
    "Abrir CR proprio para WALL_BASE_OFFSET no fluxo de paredes existentes, com teste de regressao de cota, ANTES de qualquer aprovacao da posicao Z das pecas.",
    "Decidir o destino da reprovacao REPEATED_VERTICAL_COMPENSATOR_STRIP desta bancada - decisao de dominio, nao de codigo.",
    "Decidir se a janela 'Preparando o solver...'/'Preparando a criacao dos blocos...' passa a ter ponto de cancelamento: hoje o botao Cancelar so tem efeito a partir do laco por parede.",
    "Avaliar se um Execute() que recebe uma acao desconhecida/None deve avisar em vez de voltar em silencio - foi o silencio que escondeu este defeito por duas execucoes inteiras.",
    "Concluir a suite consolidada depois da medicao no Revit."
  ],
  "next_steps": [
    "Rodar o botao TESTE-PERF (head 686320a) uma vez, nas mesmas 2 Walls, e medir tempo de criacao e quantidade criada.",
    "Ler o perf_diag.log da nova execucao e anexar como evidencia versionada.",
    "Nao mesclar na main: esta entrega cobre um defeito de integracao corrigido e duas pendencias fisicas em aberto."
  ],
  "references": [
    {"path": "docs/checkpoints/evidence/2026-09-09-perf-diag-run1-etapa5.log"},
    {"path": "docs/checkpoints/evidence/2026-09-09-preparing-solver-measurements.json"},
    {"path": "docs/checkpoints/evidence/main-safe-engineering-input.json"},
    {"path": "docs/checkpoints/evidence/main-safe-handler-bench-run.json"},
    {"path": "nuvem/core/engine/perf_trace.py"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "tests/test_script.py"},
    {"path": "docs/checkpoints/2026-09-09-beta-main-safe.md"}
  ]
}
```

## A prova

[Log da execucao instrumentada](evidence/2026-09-09-perf-diag-run1-etapa5.log),
sha256 `211e146c3c3b938c127ea0d1853cb37aab7acce2873961892eb1fe01940abf32`:

```
+6.298s Execute ENTROU action=solve
+6.560s _execute_solve END dt=0.255s
+6.561s Execute SAIU   action=create    <- o callback agendou "create"
+6.573s Execute ENTROU action=None      <- e o finally ja' tinha apagado
+6.575s Execute SAIU   action=None
```

A mesma sequencia se repete em `+147.977s`, quando o usuario tentou de
novo. Duas tentativas, zero bloco criado, nenhum erro na tela.

## O mecanismo

```
Execute(action="solve")                       (thread principal do Revit)
  _execute_solve()
    on_done("solve", None)
      -> _PostCreationForm._on_solve_done
           -> _on_create_click            (log "Etapa 5: criando as instancias...")
                -> _raise_action("create")
                     handler.action = "create"    <-- DENTRO de Execute()
                     external_event.Raise()       <-- fica na fila
  finally: self.action = None                     <-- APAGA a acao agendada
Execute(action=None)                              <-- nenhum ramo casa
  (nao chama on_done; a UI espera para sempre)
```

O docstring de `_raise_action` afirma que `Raise()` "roda no thread da UI,
FORA do `Execute()` do ExternalEvent". Isso deixou de ser verdade em
2026-08-27, quando o encadeamento automatico solve -> create foi
introduzido a pedido do usuario ("os blocos precisam ser fisicamente
inseridos no modelo"). O defeito nasceu ali e ficou invisivel porque um
`Execute()` sem ramo correspondente volta em silencio.

## A correcao

Consumir a acao no inicio de `Execute()` e despachar por copia local:

```python
action = self.action
self.action = None      # a acao que um callback agendar agora sobrevive
try:
    if action == "analyze": ...
```

Uma linha de comportamento. Nenhuma regra fisica tocada.

## Tempos medidos na execucao real (dentro do Revit)

| Etapa | Tempo |
| --- | --- |
| Latencia do ExternalEvent (Raise -> Execute) | 0,047 s |
| `refresh_geometry_from_document` | 0,062 s |
| `analyze_created_walls_for_errors` | 0,065 s |
| `_execute_solve` | 0,255 s / 0,136 s |
| Latencia do Raise encadeado (solve -> create) | 0,012 s |
| **Etapa 5 (criacao)** | **nunca executou** |

## O laco de criacao esta limpo

Auditado item a item, conforme pedido:

- **`Regenerate()` por bloco:** nao existe. Ha um unico `Regenerate()`,
  dentro da transacao de `Activate()`, fora do laco.
- **Busca de familia/tipo ou varredura global por bloco:** nao existe. O
  `FamilySymbol` vem de `catalog[cand["logical_code"]]["symbol"]`, montado
  uma vez.
- **`Activate()`:** uma vez por codigo usado, antes do laco.
- **Espera/lock:** nenhuma. O unico ponto de espera do caminho e o proprio
  ExternalEvent - que era exatamente onde a acao se perdia.
- **Excecao engolida:** nao havia excecao. Havia um despacho sem ramo
  correspondente, que e' pior: nem sucesso, nem erro, nem log.

## Pendencias fisicas preservadas

### WALL_BASE_OFFSET - a cota Z das pecas NAO esta aprovada

`run_modulation_on_existing_walls` faz `base_z_abs = selected_level.Elevation`
e ignora `WALL_BASE_OFFSET`. O padrao correto ja existe no proprio arquivo
(`base_z_abs = level_elevation + base_offset`).

| Grandeza | Valor |
| --- | --- |
| Elevacao do nivel `pb` | -1106,16 cm |
| `WALL_BASE_OFFSET` das Walls | +1718,164 cm |
| Base real das paredes | 612 cm |
| `base_z_abs` usado hoje | -1106,16 cm |
| Z da 1a fiada como sera criada | -1105,16 cm |
| Z esperado da 1a fiada | 613 cm |
| **Erro** | **1718,164 cm** |

Como o caminho de criacao calcula `course_offset = course_z_abs -
base_z_abs`, o valor se cancela e o erro aparece integralmente na posicao
final. `controlled_beta_preflight` nao compara Z de peca com base de
parede, entao **nao bloqueia**. Qualquer execucao de criacao feita antes
do CR de Z serve para medir tempo e quantidade, **nunca para aprovar
geometria vertical**.

### REPEATED_VERTICAL_COMPENSATOR_STRIP

O solve desta bancada reprovou 1 parede na auditoria de amarracao entre
fiadas. Por decisao registrada em 2026-08-26, isso nao bloqueia a criacao -
as pecas saem marcadas em vermelho para revisao. **O auditor nao foi
tocado, nem seu resultado suprimido.** Continua sendo reprovacao fisica em
aberto, a ser decidida no dominio.

## Limitacoes

A correcao esta provada por teste de regressao offline (falha antes, passa
depois) mas **ainda nao foi exercitada no Revit**. Tempo de criacao,
quantidade criada e repetibilidade do beta continuam sem medicao ate a
proxima execucao.
