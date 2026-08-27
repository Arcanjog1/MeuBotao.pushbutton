# Arquitetura interativa — acompanhamento visual + pausar/continuar/cancelar

> **OBSOLETO (2026-08-26):** a UI interativa em PySide6/Qt descrita neste
> documento foi **removida** a pedido do usuário (era a maior causa de
> demora/erros ao abrir o botão — instalação extra do PySide6 no Python
> embutido do pyRevit, download de um sub-pacote a mais, criação de
> QApplication). Os pacotes `core/ui_pyside/`, `core/ui_legacy/`,
> `core/controller/`, `core/execution_state/`, `core/revit_bridge/`,
> `core/revit_services/` e `core/engine/wall_stepper.py` citados abaixo
> não existem mais no repositório. O fluxo atual é sempre o WinForms de
> sempre (`ask_setup`/`_SetupForm` em `core/wall_modeling.py`), com layout
> modernizado (cores/tipografia/cartões), sem nenhuma dependência binária
> extra. Este documento fica só como registro histórico da tentativa.

Este documento acompanha o plano em `jazzy-nibbling-hanrahan.md` (sessão de
implementação). Resume o que foi entregue, como ligar, e o que falta.

## O que foi entregue

Novo pacote `core/`, em camadas, ao lado do motor existente
(`core/wall_modeling.py`, **regras estruturais inalteradas**):

```
core/execution_state/   state_machine.py (IDLE→ANALYZING→MODULATING→
                         VALIDATING→PAUSED/COMPLETED/CANCELLED/ERROR) +
                         session.py (ModulationSession, snapshot serializável)
core/engine/             wall_stepper.py — versão pausável, parede-a-parede,
                         da FASE DE ANALISE/AJUSTE de process_walls_one_by_one
                         (mesma aritmética, injeção de dependência nas regras
                         que continuam em wall_modeling.py)
core/revit_bridge/       command_queue.py (fila thread-safe) +
                         external_event.py (único IExternalEventHandler,
                         generaliza o padrão já usado em
                         _PostCreationEventHandler)
core/revit_services/     view_service.py (zoom/realce por parede, usado a
                         cada passo) + wall_service.py (exclusão das
                         paredes de referência, botão "Finalizar") +
                         block_service.py (criação por parede — pronto
                         para uma Fase futura, ver "Por que a criação não
                         é por parede" abaixo; NÃO é chamado pelo laço
                         principal hoje)
core/controller/         orchestrator.py — laço parede-a-parede numa
                         threading.Thread própria, nunca toca a API do
                         Revit diretamente; ao terminar a última parede,
                         roda a ETAPA 3C (`group_shift_fn`, uma vez) e só
                         então chama `finalize_fn` UMA VEZ para criar os
                         blocos; `request_delete_reference_walls()` (thread
                         própria, sob pedido explícito da UI) exclui as
                         paredes de referência já substituídas por blocos
core/ui_pyside/          main_window.py (janela PySide6: parede atual,
                         etapa, progresso, avisos, Pausar/Continuar/
                         Cancelar/Passo-a-passo/Finalizar) + app.py
                         (bootstrap do QApplication, bombeado via
                         UIApplication.Idling — nunca chama
                         QApplication.exec() bloqueante)
```

Todas as camadas puras (`execution_state`, `revit_bridge/command_queue`,
`engine/wall_stepper`, `controller/orchestrator` com fakes) têm testes
isolados em `tests/test_interactive_architecture.py` (rode com
`python tests/run_interactive_tests.py`) e **não dependem do Revit nem do
Qt** para rodar — inclusive o laço completo do `ModulationController`
(pausar/continuar/passo-a-passo/cancelar/completar) é exercitado com um
`ExternalEvent` falso.

`core/wall_modeling.py` ganhou:
- um bloco de import guardado (try/except) perto de `_ACTIVE_MODELESS_WINDOWS`,
  que nunca quebra a execução se o pacote novo não estiver disponível;
- `run_interactive_modulation(...)`, que monta o `ModulationController` + a
  janela PySide6, injetando as próprias funções de regra deste módulo
  (`_GlobalsRulesProvider`), um `plan_hook` real (`plan_axis_opening_fix`,
  a MESMA função que o botão "Ajustar Erros" de sempre usa) e um
  `finalize_fn` real (ver abaixo) — nenhuma fórmula foi copiada ou
  reescrita;
- um gancho (`INTERACTIVE_MODULATION_UI`, perto de `_ACTIVE_MODELESS_WINDOWS`)
  no lugar onde `main()` hoje chama `analyze_created_walls_for_errors(...)`
  de forma síncrona/bloqueante — **ligado** (pedido explícito do usuário,
  2026-08-25): se o ambiente não tiver CPython+PySide6 prontos, o próprio
  bloco de import guardado deixa `_interactive_modulation_available = False`
  e o gancho nunca dispara, caindo automaticamente no fluxo WinForms de
  sempre — o botão não quebra mesmo sem o ambiente pronto.

## Por que a criação de blocos NÃO é por parede

A primeira versão desta arquitetura criava os blocos de cada parede assim
que ela terminava de ser analisada (uma `Transaction` por parede). Ao
investigar o caminho de criação real (`_execute_solve`/`_execute_create`,
o botão "Lançar Blocos" de sempre), ficou claro que isso seria uma
**regressão silenciosa**: a criação de verdade não roda sobre o resultado
do `process_walls_one_by_one` puro — ela roda sobre
`solve_building_blocks_all_courses`, que:

1. resolve o preenchimento **por banda de fiadas** (grupos de fiadas com o
   mesmo conjunto de aberturas ativas — uma janela só fica vazia na faixa
   vertical real do seu vão, fiadas abaixo do peitoril continuam sólidas);
2. só DEPOIS roda `audit_all_walls_bond_quality`, que audita a amarração
   entre fiadas **olhando a parede inteira, todas as fiadas de uma vez**
   (junta corrida, padrão alternado, faixa vertical repetitiva de peça
   especial) — uma auditoria que não existe, e não pode ser replicada
   corretamente, olhando uma parede/fiada isolada.

Criar por parede, sem essas duas etapas, poderia colocar no modelo uma
combinação de blocos que a auditoria de amarração (regra #1, absoluta)
teria reprovado. Em vez de reimplementar ou simplificar essa lógica dentro
do controller, a arquitetura final faz:

- o laço interativo (parede-a-parede, pausável) cuida só de
  **analisar + ajustar + validar** cada parede (exatamente o que
  `process_walls_one_by_one` sempre fez) — **nada é escrito no Revit
  durante essa fase**;
- ao terminar a última parede, o controller chama `finalize_fn` **uma
  única vez**, que roda literalmente a mesma sequência do botão "Lançar
  Blocos" de sempre (`solve_building_blocks_all_courses` + filtro pela
  auditoria de amarração + `create_building_blocks`), agora sobre a
  geometria já ajustada pelo laço interativo.

Consequência prática: "Cancelar" durante a fase de análise não tem nada
para desfazer (nada foi criado ainda) — os blocos só existem depois que a
barra de progresso chega a 100% e a etapa "Criando blocos no Revit..."
aparece. `core/revit_services/block_service.py` (criação por parede, uma
`Transaction` cada) fica pronto para uma Fase futura que porte também a
banda/auditoria para o modelo por-parede — não é usado pelo laço principal
hoje, para não arriscar uma criação incompleta.

## ETAPA 3C (deslocamento de parede vizinha) — integrada

`find_wall_group_shift_fixes` (desloca uma parede vizinha CONECTADA, ou
alonga/encurta a própria ponta livre, quando o ajuste de abertura sozinho
não fecha uma parede) roda **uma única vez**, depois que a ÚLTIMA parede
termina o laço interativo (nunca por parede — ela re-resolve a planta
INTEIRA a cada tentativa, cara demais para rodar dentro do passo-a-passo).
O cálculo em si é puro (roda no thread do controller); a ESCRITA de
verdade no modelo (`apply_wall_group_shift`, a mesma função de sempre)
acontece via `ExternalEvent`, com a mesma disciplina de
`fix_all_wall_modulation_errors` — `SubTransaction` por grupo,
`Regenerate()` + revalidação com `evaluate_wall_modulation` antes do
`Commit`, `RollBack` se a revalidação ainda apontar erro, e só escreve a
nova geometria em `session.working_walls` depois do commit ter
acontecido. A janela mostra o progresso ("ETAPA 3C: tentativa X/Y...").

Durante essa integração, um segundo bug real apareceu e foi corrigido:
`session.working_walls`/`working_openings` (a cópia de trabalho que
`finalize_fn`/`group_shift_fn` recebem) nunca eram de fato escritos no
objeto `session` — só existiam dentro do `stepper` interno. Um
`finalize_fn` de verdade teria recebido `None` e quebrado. Agora
`orchestrator._run()` mantém os dois sincronizados a cada parede. Coberto
por teste (`test_controller_runs_to_completion_and_finalizes_exactly_once`).

## Prévia com Walls nativas + "Modular por parede" x "Modular planta inteira"

Exigência do usuário (2026-08-25): a prévia/modulação temporária
**continua usando Walls nativas do Revit** (nunca um elemento à parte) e
fica **sempre sincronizada** com o estado atual do cálculo — não só a
geometria inicial — mesmo com a lógica iterativa de correção
parede-a-parede. Responsabilidades continuam separadas: Walls nativas =
representação visual; motor de modulação (`wall_stepper.py`, inalterado)
= testa blocos/acha conflito/calcula ajuste/valida; blocos estruturais =
resultado definitivo, só após validação (ver "Por que a criação de blocos
NÃO é por parede" acima — isso não muda). A prévia nunca bloqueia nem
marca erro — falha em sincronizá-la vira aviso em `session.warnings`,
nunca interrompe o motor.

`_plan_hook` (ver acima) já calculava, por parede, o menor ajuste possível
de abertura/pilar — mas so' em memória (`working_walls`/`working_openings`
do stepper): as Walls REAIS nunca eram tocadas até `finalize_fn` (só no
final, e só para lançar os blocos). Isso deixava a previa (as Walls
visíveis no Revit) sempre com a geometria INICIAL durante todo o laço, e
criava uma inconsistência latente: `_plan_hook` de uma parede POSTERIOR
que dependa da posição real de um pilar/peitoril de uma parede já
ajustada (via `created_walls_by_axis`, lido do modelo de verdade) via
`plan_axis_opening_fix` enxergaria a geometria PRÉ-ajuste.

Correção: `sync_wall_plan_fn` (novo, montado em `run_interactive_modulation`
junto com `_plan_hook`/`_group_shift_fn`/`_finalize_fn`) — chamado pelo
`orchestrator` logo depois que o stepper ACEITA um plano de abertura/pilar
para uma parede (`verify()` já confirmou, em memória, que fecha a
modulação), ANTES de seguir para a próxima parede. Aplica o MESMO plano
nas Walls reais via `apply_axis_opening_fix` (a mesma função que
`fix_all_wall_modulation_errors` já usa no fluxo em lote — nenhuma lógica
de escrita nova), numa `Transaction` própria, via `ExternalEvent` (nunca
direto). Corrige os dois problemas de uma vez: a previa visível acompanha
o cálculo o tempo todo, e `_plan_hook` de paredes posteriores volta a ler
geometria real e atualizada.

**"Modular por parede" x "Modular planta inteira"**: escolha simples
exposta em `SetupDialog`/`_SetupForm` (seção "6. Modo de execução"),
guardada em `modulation_mode` (junto com Layer/Nível/altura/aberturas, nos
mesmos dois arquivos de preferências — `setup_prefs.py` e
`_remember_setup_defaults`). Vira `stepwise` no `ModulationController`:
`stepwise=True` pausa sozinho em TODA borda segura entre paredes (mesmo
mecanismo de Pausar/Continuar/Passo-a-passo já existente — o usuário só
precisa clicar Continuar); `stepwise=False` roda até o fim sem pausar por
conta própria. A ordem de processamento (horizontais cima→baixo/esq→dir,
depois verticais baixo→cima/esq→dir, pela posição real na planta) é a
regra #5 já existente (`order_walls_for_processing`) — os dois modos usam
a MESMA ordem, só diferem em pausar ou não entre paredes.

Testado (`tests/test_interactive_architecture.py`, sem Revit/Qt):
`test_controller_stepwise_pauses_on_every_wall_boundary`,
`test_controller_whole_plan_never_pauses_by_itself`,
`test_controller_syncs_wall_plan_before_moving_on` (ciclo completo
tentativa → conflito → menor correção → prévia sincronizada → validação)
e `test_controller_sync_wall_plan_failure_is_a_warning_not_a_crash`
(previa nunca bloqueia o motor). **Sem validação dentro de um Revit real
ainda** — mesma ressalva do resto desta arquitetura (ver "Pendências
conhecidas" abaixo).

## Fase 0 — engine CPython e loader

- **Engine CPython**: `Script.py` começa com `#! python3` (linha 1,
  obrigatório) — o pyRevit passa a rodar o botão no engine CPython em vez
  do IronPython padrão (confirmado via documentação/exemplos oficiais do
  pyRevit — o shebang é o mecanismo real de seleção de engine por script).
  `clr.AddReference` continua funcionando igual (pythonnet também roda sob
  CPython) — a autenticação/DPAPI do loader não mudou.
- **Loader sincroniza a árvore `core/` inteira**, não mais um arquivo
  único: lista os arquivos via API de árvore do Git (uma chamada,
  recursiva), baixa cada `.py`, espelha em
  `%LOCALAPPDATA%\MeuBotaoPushbutton\pkg_cache\core\...`, e só troca o
  cache antigo pelo novo depois que **todos** baixarem com sucesso. Ver
  [`LOADER_SETUP.md`](LOADER_SETUP.md).

## Como validar no ambiente real (`INTERACTIVE_MODULATION_UI` já ligada)

1. Instalar o PySide6 no CPython **embutido do pyRevit** (não no Python do
   sistema): rode `pyrevit env` para achar o caminho do interpretador, e
   então `"<caminho>\python.exe" -m pip install PySide6`.
2. Rodar o botão: se o ambiente já tiver CPython+PySide6 prontos, a janela
   PySide6 abre modeless assim que as paredes forem criadas, processando
   parede-a-parede com zoom/realce ao vivo, e cria os blocos de verdade
   (com o mesmo solver/auditoria de sempre) assim que a última parede
   termina.
3. Se o ambiente ainda não estiver pronto (engine ainda IronPython,
   PySide6 não instalado, `core/` ainda não sincronizado pelo loader), o
   botão cai automaticamente no fluxo WinForms de sempre, sem nenhum erro
   visível — nada quebra, só não aparece a janela nova. Se isso acontecer
   e você esperava a janela nova, confira o passo 1 e rode o botão de novo
   (o loader se auto-corrige na sincronização seguinte).
4. Para voltar ao fluxo WinForms de propósito (ex.: comparar os dois
   lado a lado), mude `INTERACTIVE_MODULATION_UI` de volta para `False`
   em `core/wall_modeling.py`.

## Tela de configuração — migrada para PySide6

`core/ui_pyside/setup_dialog.py` (`SetupDialog`) reproduz `_SetupForm`
campo a campo (Layer ordenado por nº de linhas, espessuras detectadas +
campo livre, Nível, altura, modo de detecção de aberturas), com a MESMA
validação e o mesmo formato de `result`. É modal (`QDialog.exec()`) — bloquear
aqui é o comportamento certo, igual `Form.ShowDialog()`: nada existe no
modelo ainda, então não há o que o usuário precisaria ver responsivo
enquanto configura. A varredura de espessuras (`scan_candidate_thicknesses_cm`)
chega por injeção de dependência, sem importar `wall_modeling` de dentro
do pacote `ui_pyside` — mantém a regra de camadas (UI nunca depende do
motor). As preferências lembradas entre execuções usam o MESMO arquivo
que a versão WinForms (`core/execution_state/setup_prefs.py`, mesmo path,
duplicado de propósito para as duas UIs não dependerem uma da outra).

Só é usada quando `INTERACTIVE_MODULATION_UI` está ligada (`ask_setup`
escolhe entre PySide6 e WinForms pela mesma flag que liga a execução
interativa — não faz sentido misturar as duas UIs numa mesma execução);
com a flag desligada, ou qualquer falha ao montar a janela PySide6, cai
automaticamente para `_SetupForm` (WinForms) e depois para
`_ask_setup_legacy`, exatamente como antes.

## Pendências conhecidas (não escondidas)

- A grade de erros/"Ajustar Erros"/"Lançar Blocos" manuais do
  `_PostCreationForm` (WinForms) continuam como estão — a execução
  interativa (quando ligada) já cobre analisar, ajustar (`plan_hook` +
  ETAPA 3C) e criar automaticamente, então essa tela WinForms só é
  exercitada quando `INTERACTIVE_MODULATION_UI` está desligada.
- O `ModulationController.cancel(keep_done=False)` (desfazer tudo) existe
  na API mas hoje é equivalente a `keep_done=True`, porque nada é criado
  antes do fim (ver seção acima) — só passa a fazer diferença de verdade
  se/quando a criação também virar incremental.
- **Teste real dentro do Revit não foi feito nesta sessão** (não há Revit
  nem pyRevit disponíveis neste ambiente de desenvolvimento) — o esqueleto
  está testado isoladamente (22 testes em `tests/run_interactive_tests.py`,
  incluindo o laço completo do controller com pausar/continuar/passo/
  cancelar/excluir paredes/ETAPA 3C/previa com Walls nativas) e a suíte
  existente (130 testes em `tests/run_tests.py`) continua verde, mas a
  integração fim-a-fim (engine CPython real + PySide6
  real + Idling pump real + `ActiveUIDocument`/`ExternalEvent` reais, e o
  `SetupDialog`/`main_window` — nenhum widget Qt real pôde ser exercitado
  aqui, o PySide6 nem está instalado neste ambiente) só se confirma
  rodando no Revit — isso fica para você validar.

## Extração física do motor (regras `#1-#9`) — iniciada, não completa

`wall_modeling.py` tem ~9000 linhas de regras estruturais fortemente
interligadas (funções que chamam outras por nome dentro do mesmo módulo,
constantes compartilhadas). O `wall_stepper.py` já isola inteiramente a
**lógica de controle** (parede-a-parede, pausável) das **regras**
(acessadas por injeção de dependência) — a extração física, além disso,
foi começada de verdade nesta entrega:

- `core/engine/tolerances.py`: `FEET_PER_METER` e as tolerâncias de
  geometria (`COLLINEAR_MATCH_TOLERANCE_*`, `MIN_WALL_SEGMENT_*`,
  `OPENING_BRIDGE_TOLERANCE_*`) — copiadas verbatim (valor + comentário
  original). `wall_modeling.py` importa daqui com fallback inline
  (try/except) para nunca quebrar se o pacote ainda não tiver sido
  sincronizado.
- `core/engine/geometry.py`: `are_lines_parallel`, `get_line_midpoint`,
  `project_point_on_line`, `get_distance_between_parallel_lines`, os
  caches de geometria (`_line_geom_cache` e variantes `_cached`),
  `_xy_deviation_ft`, `_axis_offset_error_ft`, `create_centerline`, os
  ajudantes de religamento por abertura (`_opening_bridges_gap` e
  família), `merge_collinear_fragments`, `_line_pair_overlap_ft` e
  `lines_overlap_enough` — ~670 linhas movidas verbatim.
  `wall_modeling.py` importa tudo via `from core.engine.geometry import *`
  (sem fallback — essa dependência é obrigatória; `__all__` inclui os
  nomes com underscore, que `import *` ignoraria por padrão).

Verificado end-to-end pela suíte de 127 testes existente (nenhuma fórmula
mudou) + os 18 testes da arquitetura interativa.

**Por que parou aqui, e não nas ~9000 linhas todas**: esse trecho
(geometria pura) era um bloco CONTÍGUO com zero dependência de funções
externas ao bloco — o cenário ideal para mover com corte de linhas e
baixo risco de erro. O próximo agrupamento natural (aritmética de
blocos/vãos em cm — `pack_pier_with_blocks`, `solve_opening_modulation`,
`nearest_block_lengths_cm`, etc.) já NÃO é contíguo: está intercalado, no
arquivo, com funções que leem `doc` de verdade (cache de vãos por
abertura, auditoria ao vivo). Extrair um conjunto espalhado de funções
sob pressa é mais chance de esquecer uma referência cruzada ou reordenar
algo por engano — exatamente o tipo de "solução improvisada só para
aparentar completa" que não deveria acontecer. Continuar essa extração é
seguro e mecânico, mas função por função (ou pequeno grupo contíguo por
vez), sempre validando com `tests/run_tests.py` antes de avançar para o
próximo trecho — o padrão está provado, falta repeti-lo.
