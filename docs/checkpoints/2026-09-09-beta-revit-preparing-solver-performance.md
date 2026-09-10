# Primeiro beta Revit: criacao real, falso positivo do auditor e o congelamento da Tela 1

```json
{
  "date": "2026-09-09",
  "scope": "current",
  "branch": "claude/revit-solver-perf-diagnosis-6dfd89",
  "head": "96c89b570d05f736546cacdbd28c174e3295b2d5",
  "base": "aa58d70d84c6134216f8f15a131edf060c4dce81",
  "pr": "not-created",
  "objective": "Fechar o primeiro beta controlado do Revit na bancada de 2 paredes / 1 encontro em L / 0 aberturas: achar por medicao onde o fluxo travava, corrigir somente hotspots provados, eliminar o vermelho falso da auditoria de amarracao sem silenciar o auditor, e decidir merge por gates.",
  "changes": [
    "BUG REAL 1 - CORRIGIDO: acao 'create' perdida. _PostCreationEventHandler.Execute() passa a CONSUMIR a acao no inicio e despachar por copia local, em vez de zera-la no `finally`. Preserva a acao que um callback agenda durante o proprio Execute().",
    "BUG REAL 2 - CORRIGIDO: falso positivo REPEATED_VERTICAL_COMPENSATOR_STRIP. `_longest_adjacent_course_run` + BOND_STRIP_MIN_ADJACENT_COURSES=2: faixa vertical passa a exigir fiadas ADJACENTES. Somente o auditor foi tocado.",
    "ACHADO Z - RECLASSIFICADO como comportamento esperado, por decisao do usuario. NENHUMA alteracao de codigo. Regra registrada em nuvem/REGRAS_MODULACAO_BLOCOS.md secao 8a.",
    "Instrumentacao [PERF] (core/engine/perf_trace.py + sondas) do caminho real: clique, ExternalEvent, Execute, refresh, analyze, solve, criacao e retorno para a UI. Cada marco traz CPU do processo e contagem de threads.",
    "Nenhuma regra fisica, tolerancia, baseline, reference, input oficial ou threshold foi alterado. Nenhum skip/xfail introduzido. Nenhum detector removido.",
    "INSTRUMENTO DO GATE 5: perf_trace.start_stall_sampler() - thread PYTHON pura, ligada no clique e desligada em _on_analyze_done, que ao detectar um salto registra 'CONGELAMENTO detectado pelo amostrador parado=Ns' e despeja o topo da pilha de TODAS as threads. Torna a leitura binaria: se o amostrador congela junto, a GIL estava retida por um chamador NATIVO; se continua tiquetaqueando, e starvation especifica da thread do solver."
  ],
  "tests": [
    "tests/test_bond_strip_adjacent_courses.py: 6 passed - controles negativos (bancada real do beta) e positivos (empilhamento adjacente de 17 fiadas e de 2 fiadas), sem skip/xfail.",
    "Regressao verificada nos DOIS sentidos: revertendo somente o `if` da adjacencia, os dois controles negativos FALHAM; com a correcao, passam. Os controles positivos passam nos dois casos (a deteccao real foi preservada).",
    "tests/test_script.py + test_beta_atomic_creation.py + test_controlled_beta_preflight.py: 312 passed (HEAD anterior, com a instrumentacao).",
    "tests/test_bond_strip_adjacent_courses.py + tests/test_block_bonding.py: 38 passed no HEAD atual.",
    "Regressao do encadeamento: test_acao_agendada_por_callback_durante_execute_sobrevive e test_execute_despacha_pela_acao_do_inicio_mesmo_se_callback_trocar - falham antes, passam depois.",
    "Solve end-to-end offline no HEAD atual: 17 fiadas, 22 candidatos, 187 instancias fisicas, 0 colisoes, 0 vaos, 0 nao modulares, preflight ok, 0 paredes reprovadas.",
    "REGRESSAO DE AMARRACAO no codigo corrigido: 420 passed em 2366.84s (39min26s), exit 0 - test_script.py + test_block_bonding.py + test_block_b19_residual_fill_implementation.py + test_block_node_fill_revalidation.py + test_block_arm_role_invariance.py + test_bond_strip_adjacent_courses.py. Que a versao CORRIGIDA estava carregada e comprovado pelos 6 testes novos terem passado dentro dessa mesma rodada (com a logica antiga, dois deles falham).",
    "CONFIRMACAO no HEAD commitado: 366 passed em 2257.45s (37min37s), exit 0 - test_script.py + test_block_b19_residual_fill_implementation.py + test_block_node_fill_revalidation.py.",
    "REGRESSAO CONSOLIDADA no escopo CORRETO (raiz, 1037 testes coletados): 1035 passed / 2 failed em 5576.96s (1h32m56s), exit 1. As DUAS falhas sao as HISTORICAS ja registradas para o beta 8cdd33f, com numeros IDENTICOS: TGD compensators 52->61 (delta 9) e TP1 JUNCTION_MISSING_BINDING 8->9 (delta 1). ZERO falha nova.",
    "ERRO DE ESCOPO CORRIGIDO: a primeira consolidada rodou `pytest tests/` (1003 testes) e deixou 34 de fora (nuvem/tests/ e tools/documentation/). Refeita a partir da raiz. Que a raiz e o escopo oficial esta confirmado pela contagem: 8cdd33f tinha 1029 coletados, a raiz de hoje tem 1037 - exatamente +8, os testes acrescentados nesta entrega.",
    "GATE 3 FECHADO OFFLINE: rodando o SOLVER REAL e trocando as letras A/B, a logica antiga produz a mensagem IDENTICA a do relato ('B34 repetido(s) em X~37.0cm, em 9 fiadas (0, 2, 4, 6, 8, 10, 12, 14, 16)') e a nova nao reprova nenhuma parede. tests/test_bond_strip_adjacent_courses.py: 9 passed; 3 failed ao reverter BOND_STRIP_MIN_ADJACENT_COURSES para 0.",
    "CI (gate 12) simulado localmente, identico ao workflow check-project-status.yml: passo 1 (unittest discover em tools/documentation) 16 tests OK em 16.1s; passo 2 (validate.py --base merge-base --main origin/main --require-current-main) PASS.",
    "tests/test_perf_trace_stall_sampler.py: 4 passed em 2,59s - controle negativo (laco Python apertado NAO dispara, porque o CPython entrega a GIL a cada ~5ms) e positivo (ctypes.PyDLL, que nao libera a GIL, dispara com cpu=0.000s durante o salto - a MESMA assinatura vista no Revit) mais o despejo de pilhas identificando a thread do amostrador."
  ],
  "known_failures": [
    "BUG REAL 3 - CAUSA-RAIZ NAO FECHADA, BLOQUEADOR DE MERGE: o interpretador CPython dentro do processo do Revit congela por 19,6s (execucao 3) e por 100,2s (execucao 2) na mesma fronteira - entre `plan_failures = {}` e o `def plan_hook`, um trecho sem calculo nenhum. Durante o congelamento NENHUMA linha [PERF] de NENHUMA thread aparece (nem o watchdog), enquanto o CPU do processo anda 1,67s fora do Python. Nao e o solver, nao e a instrumentacao (0,285ms/marco medido) e nao e callback perdido. Nao consegui provar que o congelamento e limitado.",
    "FALHAS HISTORICAS PRESERVADAS (nao introduzidas por esta entrega, identicas as de 8cdd33f): tests/regression/test_benchmark_baselines.py falha para torre_easy_lo_r00_tgd (compensators 52->61) e torre_easy_lo_r00_tp1 (JUNCTION_MISSING_BINDING 8->9). Nenhum baseline, reference ou threshold foi tocado para escondê-las.",
    "GATE 3 - residuo: a eliminacao do vermelho falso esta provada por reproducao EXATA com o solver real (mensagem identica a do relato), mas nao foi reconfirmada com um clique no Revit, porque o usuario ficou sem acesso ao Revit. O risco residual e baixo: a reproducao usa o solver de producao, nao candidatos montados a mao."
  ],
  "physical_deltas": [
    "187 FamilyInstances de bloco criadas e medidas no Revit: 34 B34 + 136 B39 + 17 B19, em 17 fiadas de 11 pecas, Z de -1105,2cm a -785,2cm com passo 20cm, rotacoes 0 / 1,5708 / 4,7124 rad. 0 falhas, 0 colisoes, 0 violacoes de vao, 0 trechos nao modulares.",
    "22 candidatos do par A/B NAO sao instancias finais: 22 candidatos -> 11 pecas por fiada fisica -> 17 fiadas -> 187 instancias.",
    "Encontro em L medido e CORRETO: fiadas pares a parede LONGA vira o canto com B34; fiadas impares a CURTA vira (rot 4,7124).",
    "Amarracao medida e CORRETA: parede longa com juntas defasadas 20cm entre fiadas adjacentes e 19,05cm de sobreposicao; parede curta com 15cm de defasagem. Nenhuma junta corrida, nenhuma quebra de prisma.",
    "Recriacao: a segunda criacao substituiu o lote (187 criados, 0 falhas, 0,634s) e o total no documento permaneceu 187 - sem duplicata.",
    "Nenhuma regra fisica alterada. A logica vertical continua intacta (regra 8a)."
  ],
  "decisions_taken": [
    "BUG 1 provado por log e corrigido: 'Execute ENTROU action=solve' -> 'Execute SAIU action=create' -> 'Execute ENTROU action=None'. Nao era lentidao; era acao perdida. Depois da correcao o log mostra 'Execute SAIU action=solve pendente=create' e a criacao acontece.",
    "BUG 2 provado por MCP ANTES de tocar no codigo, conforme exigido: a modulacao esta fisicamente correta e o auditor e que errava. Corrigido SOMENTE o auditor.",
    "O auditor NAO foi silenciado: o padrao de mesma paridade continua enxergado e reportado em `alternating_strips` como dado, sem penalidade - mesmo tratamento ja dado a `alternating_joints`. Nenhum threshold afrouxado.",
    "ACHADO Z reclassificado como comportamento esperado por decisao do usuario; nenhum CR de Z aberto e nenhuma linha de codigo vertical alterada.",
    "Laco de criacao auditado e LIMPO: nenhum Regenerate por bloco, nenhuma busca de familia/tipo nem varredura global por bloco, Activate+Regenerate uma unica vez fora do laco. Nao havia hotspot de criacao a otimizar.",
    "Retorno para a UI PROVADO SAUDAVEL: worker TERMINOU -> BeginInvoke aceito -> ui._finish -> ui._on_analyze_done em 28ms. O `ui._finish` ausente na execucao 2 foi consequencia de o usuario ter fechado a janela congelada (BeginInvoke em Form descartado lanca) - nao um segundo defeito.",
    "ACHADO NOVO (2026-09-10): a atribuicao das letras A/B depende do REFERENCIAL DE COORDENADAS - o mesmo caso resolvido offline e no Revit troca qual paridade recebe qual layout. As duas solucoes sao fisicamente equivalentes, mas o detector era SENSIVEL A PARIDADE: 8 fiadas de 17 = 0,471 (abaixo de BOND_STRIP_RATIO=0,5) contra 9 de 17 = 0,529 (acima). O limiar caia exatamente entre os dois e o veredito virava cara-ou-coroa - o que tambem explica por que o defeito sobreviveu a todas as rodadas offline. A correcao por adjacencia torna o auditor INVARIANTE a paridade, que e a propriedade correta. Registrado em nuvem/REGRAS_MODULACAO_BLOCOS.md secao 8d.",
    "GATES 3, 4, 8, 10, 11 e 12 FECHADOS. Gate 5/15 continua ABERTO.",
    "NAO MERGEAR: o unico bloqueador restante e o gate 5/15 - o congelamento do interpretador CPython dentro do Revit, sem causa-raiz e sem limite provado. A instrucao do usuario e explicita: se a Tela 1 puder ficar infinita, nao mergear."
  ],
  "decisions_pending": [
    "Fechar a causa-raiz do congelamento (gate 5/15) com UMA execucao do botao TESTE-PERF (head 96c89b5), que ja carrega o amostrador. Sinal extra a ler no despejo: uma thread bloqueada dentro de uma chamada nativa NAO aparece em sys._current_frames() - ausencia no despejo ja aponta retentor nativo.",
    "Reexecutar no Revit com o pacote 2d8d0b1 para fechar o gate 3 (vermelho falso eliminado na pratica).",
    "Decidir o caso peitoril/verga da secao 15.3 das regras (conflito registrado com a 8a)."
  ],
  "next_steps": [
    "Uma execucao do TESTE-PERF (head 96c89b5) nas mesmas 2 Walls, com o amostrador ligado.",
    "Uma execucao do botao TESTE-PERF (head 2d8d0b1) nas mesmas 2 Walls, confirmando que nenhuma peca recebe vermelho.",
    "Nao mesclar na main ate que os gates 3, 5, 8, 10 e 12 fechem."
  ],
  "references": [
    {
      "path": "docs/checkpoints/evidence/2026-09-09-beta-fechamento-mcp.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-09-perf-diag-run1-etapa5.log"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-09-perf-diag-run2-stall-analyze.log"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-09-perf-diag-run3-fluxo-completo.log"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-09-preparing-solver-measurements.json"
    },
    {
      "path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"
    },
    {
      "path": "nuvem/core/engine/perf_trace.py"
    },
    {
      "path": "nuvem/core/wall_modeling.py"
    },
    {
      "path": "tests/test_bond_strip_adjacent_courses.py"
    },
    {
      "path": "tests/test_script.py"
    },
    {
      "path": "docs/checkpoints/2026-09-09-beta-main-safe.md"
    }
  ]
}
```

## Bug real 1 - acao `create` perdida pelo `finally` (CORRIGIDO)

```
+6.298s Execute ENTROU action=solve
+6.561s Execute SAIU   action=create    <- o callback agendou "create"
+6.573s Execute ENTROU action=None      <- e o finally ja' tinha apagado
```

`_execute_solve` chama `on_done("solve")` de dentro de `Execute()`; o
callback encadeia `_raise_action("create")`. O `finally` apagava a acao. O
despacho seguinte nao casava com nenhum ramo, nao chamava `on_done` e
voltava em silencio - a Etapa 5 ficava para sempre em "criando as
instancias de bloco no Revit...", com zero bloco criado e zero erro.

Correcao: consumir a acao no inicio e despachar por copia local. Depois
dela, o log da execucao 3 mostra `Execute SAIU action=solve pendente=create`
e a criacao acontece.

## Achado Z - NAO E BUG

Decisao do usuario: os blocos nascem a partir do **nivel de referencia**;
`WALL_BASE_OFFSET` de uma Wall existente e' arbitrario e nao redefine a
origem vertical da modulacao. Nesta bancada sao as **Walls** que estao
deslocadas. **Nenhuma linha de codigo alterada.** Regra em
[REGRAS_MODULACAO_BLOCOS.md](../../nuvem/REGRAS_MODULACAO_BLOCOS.md),
secao 8a; conflito com a secao 15.3 registrado la', nao apagado.

## Bug real 2 - falso positivo do auditor (CORRIGIDO, provado por MCP)

Medicao dos 187 blocos REAIS criados:

| | parede CURTA (69cm) | parede LONGA (354cm) |
| --- | --- | --- |
| fiada par (A) | `B19[t 0..19]` `B34[t 20..54]` | `B34[1910,7..1944,7]` + 8x B39 |
| fiada impar (B) | `B34[t 0..34]` `B34[t 35..69]` | `B39[1925,7..1964,7]` ... |
| junta par | t~19,5 | x~1945,2 |
| junta impar | t~34,5 | x~1965,2 |
| **defasagem** | **15 cm** | **20 cm** |

Sobreposicao horizontal medida na parede longa: **19,05 cm**. Encontro em
L: fiadas pares a LONGA vira o canto, impares a CURTA (rot 4,7124) -
alternancia classica. Nenhuma junta corrida, nenhuma quebra de prisma.

**Causa-raiz**: o detector contava `len(courses)` sem exigir ADJACENCIA.
Como o solver resolve **um** par A/B e o repete em toda fiada par e toda
impar, qualquer peca especial da fiada A aparece por construcao em 100%
das pares (9/17 = 0,53 >= `BOND_STRIP_RATIO`). E' a mesma causa-raiz ja
corrigida para `ALTERNATING_JOINT_PATTERN`. Agravante: o cluster e' formado
pelo **centro** da peca, e o centro do B34 impar (t=52) cai dentro de
`BOND_STRIP_EDGE_EXEMPT_CM = 25` - por isso a peca impar que de fato cobre
t~37 nao entrava no cluster.

**Correcao**: `_longest_adjacent_course_run` + `BOND_STRIP_MIN_ADJACENT_COURSES = 2`.
Repeticao so' na mesma paridade da corrida 1 e sai em `alternating_strips`
(dado, sem penalidade). Empilhamento adjacente continua reprovando.

## Bug real 3 - congelamento da Tela 1 (NAO FECHADO - BLOQUEADOR)

```
+ 0.060s cpu=0.062s  analyze.trecho: plan_failures criado
+19.648s cpu=1.734s  analyze.trecho: plan_hook definido
```

19,59 s para executar um `def`. Entre as duas sondas ha' exatamente tres
instrucoes: um `if` falso, um dict vazio e um `def`.

**Durante os 19,59 s nenhuma linha [PERF] de nenhuma thread do processo do
Revit aparece** - nem o watchdog (`System.Threading.Timer`, dispara a cada
3 s apos 8 s parado), nem a thread de UI, nem o worker. O interpretador
CPython inteiro ficou congelado, enquanto o CPU do **processo** andou
1,67 s fora do Python. Na execucao 2 a mesma fronteira congelou 100,2 s.

Descartados por medicao: solver, instrumentacao (0,285 ms/marco), callback
perdido. O retorno para a UI e' **saudavel**: `worker TERMINOU` ->
`BeginInvoke aceito` -> `ui._finish` -> `ui._on_analyze_done` em 28 ms.

Hipotese principal, **nao provada**: a GIL do pythonnet permanece retida
pela thread principal do Revit ao retornar de
`IExternalEventHandler.Execute`, enquanto o Revit executa trabalho proprio.
Enquanto o interpretador esta congelado, **nenhuma mitigacao em Python
funciona** - watchdog, barra, log e checagem de Cancelar sao todos Python.

## Contagem, geometria e recriacao

187 instancias (34 B34 + 136 B39 + 17 B19), 17 fiadas x 11 pecas, Z de
-1105,2 a -785,2 cm com passo 20 cm. Criacao em 1,667 s (laco 0,738 s,
commit 0,560 s, 187 `NewFamilyInstance`, 34 rotacoes, 0 espelhamentos).
Recriacao em 0,634 s, 187 criados, total no documento permanece **187** -
substituicao correta, sem duplicata.

## Veredito

**O primeiro beta NAO esta PASS.** Dois defeitos reais foram corrigidos e
provados; o terceiro esta aberto e e' bloqueador. Merge nao executado.
