# Consolidação do GitHub e arquitetura Beta 2
STATUS: entrega documental; arquitetura PENDING USER APPROVAL.

Main inicial aa58d70d84c6134216f8f15a131edf060c4dce81.
#33: 59c0352e4a3f66349a08b1d3f1ac5b079ce72bf9. #35: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9.
[Auditoria/PRs/checks](GITHUB_STATE_2026-09-10.md).
PR de reorganização: not-created; merge posterior consultável no PR.
Checkpoint registra HEAD avaliado anterior ao commit documental; um commit
não pode gravar seu próprio SHA.

## Estrutura

Antes: entrada apenas START_HERE, status extenso, referências aninhadas,
regras e benchmark em nuvem. Depois: README raiz, painel, portais semânticos,
comparação, sete decisões pequenas, arquitetura e backlog completo.

~~~
/
├── README.md, AGENTS.md, CLAUDE.md
├── nuvem/core/                       produção sem mudança
├── nuvem/REGRAS_MODULACAO_BLOCOS.md   autoridade preservada
├── nuvem/benchmark/                  pacote/dados oficiais
├── rules/
│   └── modulation/, openings/, junctions/, catalog/    índices
├── benchmark/
│   └── official/, validators/, reproducers/, diagnostics/    índices
├── reference_projects/
│   ├── README.md, COMPARISON.md, inventory.json
│   ├── torre_easy_lo_r00/README.md
│   └── butanta_r08_lt/README.md
├── docs/
│   ├── START_HERE.md, PROJECT_STATUS.md, PROJECT_STATUS_LOG.md
│   ├── DEVELOPMENT_PROCESS.md, BETA2_BACKLOG.md
│   ├── architecture/, decisions/, checkpoints/, archive/
│   └── revit_reference_extraction/   primários em caminho legado
├── tests/, tools/documentation/
└── .github/workflows/                governança #32
~~~

**Arquivos movidos: nenhum.** Portais por projeto oferecem relatório,
catálogo, aberturas, peças, relações, padrões, scripts e proveniência.
JSON/checkpoints/scripts mantêm caminhos históricos, sem cópias concorrentes.
Organização por índices foi escolhida pelo baixo risco permitido no pedido.
Status anterior preservado como HISTORICAL, sem apagar conteúdo.

## Compatibilidade e governança

Imports, assinaturas de produção e caminhos oficiais intactos. Workflow #32
continua único; não há agendamento. Verificador offline adicional confere
hashes/contagens/vínculos do acervo e guarda de árvore protegida; chamado
explicitamente, sem substituir o validador/documentação existente.

Links das referências corrigidos em #33/#35 para arquivos versionados:
_scripts/README e evidência de verga. Links novos passam no mesmo validador.
Scripts com raw/intermediários ausentes foram qualificados, não regenerados
com dados inventados.

## Entregas técnicas

[Comparação](../reference_projects/COMPARISON.md): gramática comum e
denominadores/exceções.
[A/B](architecture/opening-reinforcement-strategies.md): plano/reservas comuns,
A dedicado 9 cm, B corrida 19 cm.
[Catálogo/cortes](architecture/extended-block-catalog.md): tipo lógico↔mapping,
HEIGHT_CUT/LENGTH_CUT/pose distintos.
[UI/famílias](architecture/revit-family-mapping.md): escolha antes de calcular,
validação e erro explícito se faltar tipo.
[Backlog A–E](BETA2_BACKLOG.md) e [decisões PENDING](decisions/README.md).

## Validação proporcional

260 testes passaram em #33 e em #35, logs por HEAD. Reorganização exige
260 novamente antes de merge, testes da governança, validador de links/SHAs
e verificador do acervo/árvore. Resultado final no
[checkpoint](checkpoints/2026-09-10-beta2-consolidation.md).
Sem regressão de 50 minutos porque não houve mudança física.

## Limites e próximo objetivo

Beta 1 **CANDIDATO — VALIDAÇÃO REVIT PENDENTE**. Branch de desempenho
não localizada; API do SHA 422. Nada apagado, sobrescrito ou integrado.
Não foi certificado Revit real, read-only histórico, L/T/X das referências
ou regeneração integral dos raw ausentes.

Recomendação: [pacote incremental](architecture/beta2-implementation-package.md),
recuperar/validar Beta 1, aprovar contratos e então catálogo/mapping/planos
com gates físicos. N1/C2/CR-B em trilhas próprias. Ao concluir, parar.
