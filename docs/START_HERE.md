# START HERE — recuperação em poucos minutos

Projeto pyRevit de alvenaria estrutural. Main contém código oficial e
propostas documentais; integração não transforma proposta em contrato aprovado.

1. git status; git fetch origin main; comparar HEAD com
   [status](PROJECT_STATUS.md) e [checkpoint](checkpoints/2026-09-10-beta2-consolidation.md).
2. Ler [AGENTS](../AGENTS.md), [CLAUDE](../CLAUDE.md) e [processo](DEVELOPMENT_PROCESS.md).
3. Buscar tema → sinônimo → entidade → heading/símbolo antes de ampliar leitura.

| Pergunta | Fonte |
|---|---|
| Onde está o solver? | reforço de aberturas CHANNEL: [opening_reinforcement.py](../nuvem/core/engine/opening_reinforcement.py) ([arquitetura](architecture/channel-strategy-implementation.md)); [wall_stepper.py](../nuvem/core/engine/wall_stepper.py), [wall_modeling.py](../nuvem/core/wall_modeling.py); Script.py é entrada/loader |
| Quais regras valem? | [Índice](../rules/README.md), autoridade em [REGRAS](../nuvem/REGRAS_MODULACAO_BLOCOS.md), status por seção |
| Decisões do usuário? | [Registros PENDING](decisions/README.md) |
| Benchmark oficial? | [Índice](../benchmark/README.md), [manifesto](../nuvem/benchmark/golden/manifest.json), caminhos preservados |
| Referências humanas? | [TORRE EASY e BUTANTÃ](../reference_projects/README.md), evidência/não norma; [comparação](../reference_projects/COMPARISON.md) |
| Candidato em teste? | PR #40 `claude/butanta-channel-reference-implementation` (estratégia CHANNEL, regras 30.8/51), ready for review, sem merge. #39 (fill|tie), #38, #37 e Beta 1 **já estão na main**; #31 N1 continua NO-GO; [estado 2026-09-12](GITHUB_STATE_2026-09-12.md) |
| Última entrega? | [CHANNEL — correções da auditoria (2026-09-14)](checkpoints/2026-09-14-channel-audit-fixes.md): 30.8 off (legado = main), FREE_TO_TOP pré-solve, paridade do T, UI default NONE, comparador endurecido; antes [fechamento revogado](checkpoints/2026-09-14-channel-ready-closure.md), [implementação CHANNEL](checkpoints/2026-09-14-butanta-channel-implementation.md); antes [Defeito 1 fill|tie](checkpoints/2026-09-12-fill-tie-running-joint.md) |
| Benchmark V2? | [Réguas versionadas](../nuvem/benchmark/README.md): V1 raiz = HISTORICAL, `v2/` = topologia do motor atual (`runner.py --version v2`) |
| Próximo objetivo? | [Pacote Beta 2](architecture/beta2-implementation-package.md), [backlog A–E](BETA2_BACKLOG.md) |
| Beta 1: causas e correcoes? | [checkpoint do fechamento](checkpoints/2026-09-09-beta-revit-preparing-solver-performance.md) - solve->create, falso positivo do auditor, `_pump_ui`, analyze sincrono |

## Não fazer

Não iniciar Revit nesta missão; não mesclar #31 (Beta 1, #34 e scale-autofix
já estão na main pelo #37 — não reverter nem "re-mesclar");
não declarar Beta 1 PASS; não implementar LINTEL (CHANNEL é estratégia oficial candidata no PR #40, regra 51),
N1/C2/CR-B por causa de documento integrado. Não regravar benchmark para
ocultar falha, promover observação a regra ou transportar apoio TORRE EASY
para CHANNEL. Nenhum monitoramento agendado.

## Busca por domínio e histórico

Pairing/geometria: core/engine/geometry.py, wall_pairing.py e tolerances.py.
UI/Revit: wall_modeling.py; API 2027 ao usar a API.
Benchmark: REFERENCE_CORPUS/README pertinente. Bug: reproduzir → primeira
divergência → causa → fix mínimo → testes.
[Log](PROJECT_STATUS_LOG.md), [arquivo](archive/README.md) e
[status antigo](PROJECT_STATUS_2026-09-09_HISTORICAL.md) não substituem este estado.

Seções numéricas podem colidir entre branches: citar arquivo + SHA.
Ler erratas/escopo dos dumps humanos antes de reutilizar. Sem migração de imports.
