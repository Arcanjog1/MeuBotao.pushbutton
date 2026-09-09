# Beta Revit: Etapa 5 travada - acao "create" perdida no ExternalEvent

```json
{
  "date": "2026-09-09",
  "scope": "current",
  "branch": "claude/revit-solver-perf-diagnosis-6dfd89",
  "head": "07f43f2f8b7a6dc71b0b8af81a42d807db747591",
  "base": "aa58d70d84c6134216f8f15a131edf060c4dce81",
  "pr": "not-created",
  "objective": "Descobrir onde o tempo e gasto entre o clique em 'Iniciar Modulacao das Paredes' e o primeiro resultado util, na bancada de 2 paredes / 1 encontro em L / 0 aberturas do primeiro beta controlado (8cdd33f), com causa medida e nao hipotetica; corrigir apenas o hotspot provado.",
  "changes": [
    "Nenhuma alteracao de algoritmo, formula, tolerancia, regra normativa, benchmark, baseline ou gabarito. Nenhum auditor foi silenciado. Todo acesso ao modelo via MCP foi leitura.",
    "core/engine/perf_trace.py (modulo puro, sem Revit e sem UI) e sondas [PERF] no caminho real: clique, latencia do ExternalEvent, Execute, refresh de geometria, analyze, solve e todo o caminho de criacao (preflight, TransactionGroup, Activate+Regenerate, Transaction, progresso/ultima peca, laco, Commit, rollback, resultado).",
    "CORRECAO MINIMA em _PostCreationEventHandler.Execute(): a acao passa a ser CONSUMIDA no inicio e despachada por copia local, em vez de zerada no `finally`. Isso preserva a acao que um callback agenda DURANTE o proprio Execute()."
  ],
  "tests": [
    "tests/test_script.py + test_beta_atomic_creation.py + test_controlled_beta_preflight.py: 312 passed em 64.38s, ja com as sondas finas.",
    "test_beta_atomic_creation.py + test_controlled_beta_preflight.py: 50 passed.",
    "Regressao verificada nos DOIS sentidos: revertendo somente a correcao (mantendo a instrumentacao), test_acao_agendada_por_callback_durante_execute_sobrevive e test_execute_despacha_pela_acao_do_inicio_mesmo_se_callback_trocar FALHAM; com a correcao, passam.",
    "Bancada offline com dubles: _execute_solve 0.010s, _execute_analyze 0.002s. Reproducao fiel dentro do Revit sobre o documento real: refresh 0.187s + analyze 0.181s = 0.37s.",
    "Pacote beta construido e verificado a partir da PASTA DO BOTAO: head 07f43f2f8b7a6dc71b0b8af81a42d807db747591.",
    "Custo da propria instrumentacao MEDIDO, para nao ser confundido com o sintoma: mark() custa 0.285ms na mediana, 0.329ms no p95 e 0.508ms no pior caso de 300 chamadas."
  ],
  "known_failures": [
    "PENDENCIA FISICA ABERTA - REPEATED_VERTICAL_COMPENSATOR_STRIP: o solve desta bancada reprovou 1 parede na auditoria de amarracao entre fiadas. Por decisao de 2026-08-26 isso nao bloqueia a criacao (as pecas saem marcadas em vermelho), e NADA foi silenciado aqui. Continua sendo reprovacao fisica em aberto.",
    "DEFEITO NOVO E ABERTO - stall da thread de fundo: na execucao 2 (18:18, ja com a correcao), o analyze levou 100.204s, com 97.3s parados entre a entrada de analyze_created_walls_for_errors e process_walls_one_by_one - trecho que so tem um `if` falso, um dict vazio e um `def`. Houve ainda um salto de 2.16s entre dois marcos adjacentes. Nao e custo de instrumentacao (0.285ms/marco, medido) nem calculo. A thread de fundo nao estava rodando.",
    "CORRECAO DE UMA CONCLUSAO MINHA ANTERIOR: eu havia dado o analyze por descartado com base nas execucoes em que ele nao travou (0.065s na execucao 1, 0.181s na reproducao dentro do Revit). A execucao 2 mostra que ele TRAVA de forma intermitente. O solver continua computando rapido; o que trava e a thread, nao a conta.",
    "Tempo de criacao, quantidade criada e repetibilidade do beta seguem SEM medicao: a execucao 2 nunca chegou a solve/create.",
    "A suite consolidada nao foi concluida nesta sessao (interrompida duas vezes de proposito, para nao contaminar o arquivo de rastreamento que a medicao no Revit usa)."
  ],
  "physical_deltas": [
    "Nenhum. Nenhuma regra fisica, tolerancia ou geometria esperada foi alterada; a bancada continua 2 paredes, 0 aberturas, 17 fiadas e 187 blocos esperados.",
    "Estado do modelo apos a execucao instrumentada: 0 FamilyInstance de bloco criada (as 52 existentes sao carimbos/legendas). A Etapa 5 nunca chegou a rodar.",
    "Entrada real x artefato offline: CONGRUENTES (69.0024/354.0007cm, espessura 14cm, altura 340cm, sobreposicao do L 6.9959cm). Sem erro de unidade e sem Z incorreto: a cota de criacao segue o NIVEL por regra (secao 8a).",
    "Grafo: 3 nos, 1 L_CORNER, 2 FREE_END, 2 candidatos, 0 falhas, sem residuo das 126 paredes / 77 aberturas."
  ],
  "decisions_taken": [
    "CAUSA-RAIZ FECHADA e nao e lentidao: a acao 'create' era PERDIDA. _execute_solve chama on_done('solve') de dentro de Execute(); o callback _on_solve_done encadeia _on_create_click -> _raise_action('create'), que define handler.action='create' e Raise(); o `finally` de Execute() apagava essa acao; o despacho seguinte entrava com action=None, nao casava com nenhum ramo, nao chamava on_done e voltava em silencio.",
    "Latencia do ExternalEvent MEDIDA e descartada: 47ms entre 'ui.external_event.Raise CHAMADO' (+0.126s) e 'Execute ENTROU action=analyze' (+0.173s). No encadeamento solve->create foram 12ms (+6.561s -> +6.573s).",
    "Solver descartado como CAUSA DE CALCULO: analyze 0.065s, solve 0.255s e 0.136s na execucao 1, e 0.181s na reproducao dentro do Revit. Isso nao o isenta do relogio de parede - ver o stall da execucao 2 nas falhas conhecidas.",
    "Laco de criacao auditado e LIMPO: nenhum Regenerate por bloco, nenhuma busca de familia/tipo nem varredura global por bloco (o symbol vem do catalogo pronto), Activate+Regenerate uma unica vez fora do laco. Nao havia hotspot de criacao a otimizar.",
    "O benchmark offline de 0.1-1.1s exercita _execute_solve; o botao dispara analyze e depois encadeia create. Os numeros nunca foram comparaveis.",
    "ORIGEM VERTICAL DA MODULACAO (decisao do usuario, 2026-09-09): o que eu havia classificado como bug de WALL_BASE_OFFSET NAO e bug - e o funcionamento desejado. Os blocos nascem a partir do NIVEL de referencia; o offset de base de uma Wall existente e arbitrario e nao pode redefinir a cota inicial da modulacao. Nesta bancada sao as Walls que estao deslocadas. A logica de Z foi PRESERVADA sem nenhuma alteracao, o achado foi retirado da lista de bugs/CRs e a regra ficou registrada em nuvem/REGRAS_MODULACAO_BLOCOS.md secao 8a.",
    "CONFLITO REGISTRADO, nao apagado: a secao 15.3 das regras (peitoril/verga, 2026-08-28) afirma o contrario para paredes com offset de base. A secao 8a prevalece (orientacao mais recente); o caso peitoril/verga ficou como pendencia de decisao do usuario, com aviso no proprio 15.3.",
    "docs/checkpoints/2026-09-09-beta-main-safe.md reclassificado para 'historical' porque o HEAD avancou; nenhuma afirmacao, numero ou decisao dele foi alterada."
  ],
  "decisions_pending": [
    "Decidir o caso peitoril/verga da secao 15.3 das regras: aplicar a 8a literalmente (pecas de verga nascem a partir do nivel) ou tratar esse cenario como excecao com agrupamento por (altura, offset_de_base). Nao implementar o agrupamento sem essa resposta.",
    "Decidir o destino da reprovacao REPEATED_VERTICAL_COMPENSATOR_STRIP desta bancada - decisao de dominio, nao de codigo.",
    "Decidir se a janela 'Preparando o solver...'/'Preparando a criacao dos blocos...' passa a ter ponto de cancelamento: hoje o botao Cancelar so tem efeito a partir do laco por parede.",
    "Avaliar se um Execute() que recebe uma acao desconhecida/None deve avisar em vez de voltar em silencio - foi o silencio que escondeu este defeito por duas execucoes inteiras.",
    "Concluir a suite consolidada depois da medicao no Revit."
  ],
  "next_steps": [
    "Rodar o botao TESTE-PERF (head 07f43f2) uma vez, nas mesmas 2 Walls. As sondas finas devem dizer, sozinhas, se o stall e espera (cpu parado) ou trabalho, e se DoEvents/watchdog participam.",
    "Ler o perf_diag.log da nova execucao e anexar como evidencia versionada.",
    "Nao mesclar na main: esta entrega cobre um defeito de integracao corrigido e UMA pendencia fisica em aberto (REPEATED_VERTICAL_COMPENSATOR_STRIP)."
  ],
  "references": [
    {"path": "docs/checkpoints/evidence/2026-09-09-perf-diag-run1-etapa5.log"},
    {"path": "docs/checkpoints/evidence/2026-09-09-perf-diag-run2-stall-analyze.log"},
    {"path": "docs/checkpoints/evidence/2026-09-09-preparing-solver-measurements.json"},
    {"path": "docs/checkpoints/evidence/main-safe-engineering-input.json"},
    {"path": "docs/checkpoints/evidence/main-safe-handler-bench-run.json"},
    {"path": "nuvem/core/engine/perf_trace.py"},
    {"path": "nuvem/core/wall_modeling.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "tests/test_script.py"},
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
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

## Execucao 2 (18:18): a correcao funcionou, e um defeito NOVO apareceu

[Log da execucao 2](evidence/2026-09-09-perf-diag-run2-stall-analyze.log).
O pacote usado ja era o corrigido (o campo `pendente=` so existe nele), e
`Execute SAIU action=analyze pendente=None` confirma que nenhuma acao se
perdeu. Mas:

```
+  0.030s analyze_created_walls_for_errors START
+ 97.368s process_walls_one_by_one START        <- 97,3s de nada
+ 98.049s solve_all_intersections END dt=0.680s
+100.212s solve_all_intersections RESULTADO     <- 2,16s entre marcos vizinhos
+100.234s analyze_created_walls_for_errors END dt=100.204s
```

Entre os dois primeiros marcos existem exatamente tres instrucoes: um `if`
falso, `plan_failures = {}` e um `def`. **Nao ha calculo possivel ali.** E
nao e a instrumentacao: `mark()` custa 0,285ms na mediana e 0,508ms no pior
caso de 300 chamadas medidas.

O `ui._finish` nunca apareceu porque o usuario fechou a janela travada -
`BeginInvoke` num Form ja descartado lanca, e a excecao era engolida sem
deixar rastro. Isso agora e marcado (`ui_invoke.FALHOU`).

**Isto corrige uma conclusao minha anterior.** Eu havia descartado o analyze
com base nas execucoes em que ele nao travou. Ele trava, de forma
intermitente, e e' o sintoma original ("Preparando o solver..." por
minutos) finalmente capturado com timestamp.

## Origem vertical e pendencia fisica

### Origem vertical: decisao registrada, nao e defeito

Eu havia classificado como bug o fato de `base_z_abs` vir de
`selected_level.Elevation` sem somar `WALL_BASE_OFFSET`. **Estava errado.**
O usuario esclareceu em 2026-09-09 que esse e' o funcionamento desejado: os
blocos devem nascer a partir do **nivel de referencia**, e o offset de base
de uma Wall existente e' arbitrario - deixar a modulacao segui-lo
propagaria o erro do modelo para dentro da regra.

Nesta bancada, o nivel `pb` esta em -1106,16cm e as Walls tem
`WALL_BASE_OFFSET` de +1718,164cm: sao **as paredes** que estao "voando"
em relacao a' planta. Os blocos nascem colados ao nivel, que e' a posicao
**correta**. Os 1718,164cm ate' a base das Walls medem o desvio das
paredes, nao um erro da modulacao.

**Nenhuma linha da logica de Z foi alterada.** A regra ficou registrada em
[REGRAS_MODULACAO_BLOCOS.md](../../nuvem/REGRAS_MODULACAO_BLOCOS.md),
secao 8a, com o conflito contra a secao 15.3 (peitoril/verga, 2026-08-28)
anotado no proprio 15.3 em vez de apagado - a 8a prevalece, e o caso
peitoril/verga ficou como pendencia de decisao do usuario.

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

A unica pendencia fisica em aberto desta bancada e a reprovacao
`REPEATED_VERTICAL_COMPENSATOR_STRIP`. A cota Z **nao** e pendencia: e
comportamento decidido (secao 8a das regras).
