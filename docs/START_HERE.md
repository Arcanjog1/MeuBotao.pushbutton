# START HERE — recuperação em poucos minutos

Projeto pyRevit de alvenaria estrutural. Este arquivo é um **roteador
estável**: não guarda notícia (último checkpoint, estado de PR, candidato).
O estado corrente, datado e com a main observada, fica em
[PROJECT_STATUS.md](PROJECT_STATUS.md). Main contém código oficial e propostas
documentais; integração não transforma proposta em contrato aprovado.

1. `git status`; `git fetch origin main`; depois
   `python3 tools/documentation/context_pack.py state` — recibo com HEAD,
   main, status, último checkpoint, dívida conhecida, próximo passo e
   inconsistências detectadas. Sem Python: ler o [status](PROJECT_STATUS.md)
   e o checkpoint da linha "Último checkpoint".
2. Ler [AGENTS](../AGENTS.md), [CLAUDE](../CLAUDE.md) e [processo](DEVELOPMENT_PROCESS.md).
3. Para a tarefa: `python3 tools/documentation/context_pack.py pack --task "..."`
   ([uso e limites](agents/README.md)), ou buscar tema → sinônimo → entidade →
   heading/símbolo antes de ampliar leitura. Busca sem resultado não prova
   que a regra não existe.

| Pergunta | Fonte |
|---|---|
| Estado atual, PRs oficiais/candidatos, última entrega? | [PROJECT_STATUS](PROJECT_STATUS.md): JSON `official`/`candidates`, linhas "Último checkpoint" e "Bloqueadores"; `context_pack.py state` |
| Onde está o solver? | reforço de aberturas CHANNEL: [opening_reinforcement.py](../nuvem/core/engine/opening_reinforcement.py) ([arquitetura](architecture/channel-strategy-implementation.md)); [wall_stepper.py](../nuvem/core/engine/wall_stepper.py), [wall_modeling.py](../nuvem/core/wall_modeling.py); Script.py é entrada/loader ([runtime canônico](RUNTIME_CANONICO.md)) |
| Quais regras valem? | [Índice](../rules/README.md), autoridade em [REGRAS](../nuvem/REGRAS_MODULACAO_BLOCOS.md), status por seção |
| Que contexto carregar por domínio? | [Manifesto](agents/CONTEXT_MANIFEST.json) e [inventário de fontes](agents/SOURCE_INVENTORY.md) (navegação, não norma) |
| Decisões do usuário? | [Registros PENDING](decisions/README.md) |
| Benchmark oficial? | [Índice](../benchmark/README.md), [manifesto](../nuvem/benchmark/golden/manifest.json), caminhos preservados |
| Benchmark V2? | [Réguas versionadas](../nuvem/benchmark/README.md): V1 raiz = HISTORICAL, `v2/` = topologia do motor atual (`runner.py --version v2`) |
| Referências humanas? | [TORRE EASY e BUTANTÃ](../reference_projects/README.md), evidência/não norma; [comparação](../reference_projects/COMPARISON.md) |
| Próximo objetivo? | Linha "Próximo objetivo" do [status](PROJECT_STATUS.md); [pacote Beta 2](architecture/beta2-implementation-package.md), [backlog A–E](BETA2_BACKLOG.md) |

## Invariantes permanentes (sem prazo)

- Merge na `main` só com autorização explícita do usuário para aquele merge
  ([CLAUDE](../CLAUDE.md)); testes verdes tornam elegível, não autorizam.
- Não regravar benchmark/baseline para ocultar falha; `--save-baseline` e
  `--calibrate` exigem autorização específica. Não promover observação ou
  evidência humana a regra; não transportar apoio TORRE EASY para CHANNEL.
- Nenhum check-in, polling ou monitoramento agendado por iniciativa própria.
- Não iniciar Revit nem escrever em RVT sem autorização da missão; teste
  headless, handler via MCP e clique no botão são evidências diferentes.
  PASS do Beta é decisão do usuário.
- Documento integrado não autoriza implementar estratégia pendente (LINTEL /
  verga-contraverga, N1, C2, CR-B): ver [decisões](decisions/README.md).
- Sem migração de imports. Seções numéricas colidem entre branches e até
  dentro das REGRAS (ex.: `66.3`): citar arquivo + SHA + heading.
- Este roteador não aponta checkpoint específico nem estado de PR fora da
  seção Histórico; `validate.py` bloqueia a contradição.

## Busca por domínio e histórico

Pairing/geometria: core/engine/geometry.py, wall_pairing.py e tolerances.py.
UI/Revit: wall_modeling.py; API 2027 ao usar a API.
Benchmark: REFERENCE_CORPUS/README pertinente. Bug: reproduzir → primeira
divergência → causa → fix mínimo → testes.
[Log](PROJECT_STATUS_LOG.md), [arquivo](archive/README.md) e
[status antigo](PROJECT_STATUS_2026-09-09_HISTORICAL.md) não substituem o status corrente.
Ler erratas/escopo dos dumps humanos antes de reutilizar.

## Histórico — conteúdo anterior do roteador (preservado com escopo e validade)

Reconciliado em 2026-09-24 (main observada `15bacec`). O texto abaixo era
verdadeiro quando escrito (missão de consolidação de 2026-09-10 e atualizações
até 2026-09-14) e **não descreve o estado atual**: o PR #40 (CHANNEL, regra 51)
foi mesclado em `61d4f6c` (2026-09-14), o #41 em `55e990d` e o #49 em `4bb88bb`
(2026-09-23); a última entrega corrente está no status. As proibições sem prazo
foram extraídas para "Invariantes permanentes"; a ordem "não implementar
LINTEL" continua valendo porque a decisão segue pendente, não por esta missão.

- Passo 1 antigo: comparar HEAD com o status e o
  [checkpoint da consolidação](checkpoints/2026-09-10-beta2-consolidation.md).
- "Candidato em teste?" (até 2026-09-14): PR #40
  `claude/butanta-channel-reference-implementation` (estratégia CHANNEL,
  regras 30.8/51), ready for review, sem merge. #39 (fill|tie), #38, #37 e
  Beta 1 já estavam na main; #31 N1 continuava NO-GO;
  [estado 2026-09-12](GITHUB_STATE_2026-09-12.md).
- "Última entrega?" (2026-09-14):
  [CHANNEL — fechamento final](checkpoints/2026-09-14-channel-final-merge.md)
  (passagem livre contínua, desempenho 44,6→24,2 s, merge do PR #40); antes
  [auditoria](checkpoints/2026-09-14-channel-audit-fixes.md),
  [fechamento revogado](checkpoints/2026-09-14-channel-ready-closure.md),
  [implementação CHANNEL](checkpoints/2026-09-14-butanta-channel-implementation.md),
  [Defeito 1 fill|tie](checkpoints/2026-09-12-fill-tie-running-joint.md).
- "Beta 1: causas e correções?":
  [checkpoint do fechamento](checkpoints/2026-09-09-beta-revit-preparing-solver-performance.md)
  — solve->create, falso positivo do auditor, `_pump_ui`, analyze síncrono.
- "Não fazer" da missão de 2026-09-10: "Não iniciar Revit nesta missão; não
  mesclar #31 (Beta 1, #34 e scale-autofix já estão na main pelo #37 — não
  reverter nem 're-mesclar'); não declarar Beta 1 PASS; não implementar
  LINTEL (CHANNEL é estratégia oficial candidata no PR #40, regra 51), N1/C2/CR-B
  por causa de documento integrado. Não regravar benchmark para ocultar falha,
  promover observação a regra ou transportar apoio TORRE EASY para CHANNEL.
  Nenhum monitoramento agendado."
