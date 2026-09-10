# START HERE — recuperação em poucos minutos

Projeto pyRevit de alvenaria estrutural. Main contém código oficial e
propostas documentais; integração não transforma proposta em contrato aprovado.

1. git status; git fetch origin main; comparar HEAD com
   [status](PROJECT_STATUS.md) e [checkpoint](checkpoints/2026-09-10-beta2-consolidation.md).
2. Ler [AGENTS](../AGENTS.md), [CLAUDE](../CLAUDE.md) e [processo](DEVELOPMENT_PROCESS.md).
3. Buscar tema → sinônimo → entidade → heading/símbolo antes de ampliar leitura.

| Pergunta | Fonte |
|---|---|
| Onde está o solver? | [wall_stepper.py](../nuvem/core/engine/wall_stepper.py), [wall_modeling.py](../nuvem/core/wall_modeling.py); Script.py é entrada/loader |
| Quais regras valem? | [Índice](../rules/README.md), autoridade em [REGRAS](../nuvem/REGRAS_MODULACAO_BLOCOS.md), status por seção |
| Decisões do usuário? | [Registros PENDING](decisions/README.md) |
| Benchmark oficial? | [Índice](../benchmark/README.md), [manifesto](../nuvem/benchmark/golden/manifest.json), caminhos preservados |
| Referências humanas? | [TORRE EASY e BUTANTÃ](../reference_projects/README.md), evidência/não norma; [comparação](../reference_projects/COMPARISON.md) |
| Candidato em teste? | Beta 1 síncrono pendente; #34 bancada e #31 N1 são distintos; [SHAs/limites](GITHUB_STATE_2026-09-10.md) |
| Última entrega? | [Checkpoint](checkpoints/2026-09-10-beta2-consolidation.md), [consolidação](CONSOLIDATION_2026-09-10.md) |
| Próximo objetivo? | [Pacote Beta 2](architecture/beta2-implementation-package.md), [backlog A–E](BETA2_BACKLOG.md) |

## Não fazer

Não iniciar Revit nesta missão; não mesclar Beta 1/#31/#34/produção antiga;
não declarar Beta 1 PASS; não implementar CHANNEL/LINTEL, catálogo/cortes/UI,
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
