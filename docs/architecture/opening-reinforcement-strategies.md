# Um motor e duas estratégias de reforço de aberturas
STATUS: PROPOSED / PENDING USER APPROVAL.
Base: 6c00f7e8198c9e6abea1880ee8a3a4cae473c8d9.
[Decisão](../decisions/DECISION-OPENING-REINFORCEMENT.md) ·
[Evidências](../../reference_projects/COMPARISON.md).

## Arquitetura atual e fronteiras

wall_modeling.py orquestra solve_building_blocks_all_courses,
_group_course_indices_by_opening_band, passes cross-band e callbacks de
rebuild do ARM SAFE REPAIR. wall_stepper.py resolve L/T/X,
solve_wall_free_fill e solve_building_blocks; _make_block_candidate monta
candidatos. create_building_blocks/load_fixed_block_catalog fazem a ponte Revit.

opening_strategy já significa split_first/continuous_first, definido em
continuous_modulation.py. Não reutilizar esse enum para reforço.
A propriedade nova proposta é opening_reinforcement_strategy, ortogonal
à política de preencher/recortar vãos. Preservar os dois contratos.

O motor atual usa objetos geométricos/ft e comprimentos de catálogo em cm;
não é todo puro ou em cm. O planejador novo recebe DTOs sem objetos Revit,
com conversão explícita na fronteira. Não reescrever o motor nesta etapa.

## Interface proposta

~~~
OpeningReinforcementStrategy:
    LINTEL_COUNTERLINTEL
    CHANNEL

plan_reinforcement(context, strategy_config, catalog_capabilities)
    -> ReinforcementPlan
validate_reinforcement(plan, solved_wall, openings, junctions)
    -> findings
~~~

Contexto imutável: projeto/revisão, geometria e identidade canônica de paredes,
aberturas medidas (tipo declarado separado do geométrico), prismas reais de
vão, cotas absolutas/datum, vizinhos L/T/X, grade, juntas e políticas aprovadas.
Unidades explícitas cm; eixo u ao longo da parede, v transversal, z vertical,
com transformação de mundo. Não usar W0xx ou chaves das extrações como
identidade universal; verificar unicidade e migração entre particionamentos.

Configuração: enum obrigatório nas novas sessões futuras, versão de contrato,
apoio/comprimento por estratégia, cortes permitidos, escopo estrutural e
hash do mapping. Sem fallback A/B. Setup antigo pode ser inspecionado no modo
legado identificado; nova geração exige escolha explícita. Campo ausente
não significa CHANNEL ou LINTEL aprovado.

| Saída comum | Conteúdo |
|---|---|
| plan_id / schema_version / input_hash | Identidade/proveniência determinísticas |
| strategy / policy_version / catalog_hash | Configuração efetivamente usada |
| members | Peças dedicadas ou corridas, com tipo lógico e papel |
| reservations | Intervalos u e faixa z ocupados, paredes/aberturas associadas |
| support_demands | Requisitos dos lados e origem da política |
| course_slices | Fiada física, subfaixa, cota e altura próprias |
| findings | Código, gravidade, localização, causa, observado/esperado |
| unresolved | Motivo e entidades; nenhuma parede some silenciosamente |

Papéis: ABOVE_OPENING, BELOW_SILL, TOP_BOND_BEAM. O último tem política
separada. Peça compartilhada satisfaz vários papéis sem duplicar volume,
identidade, quantidade ou crédito de cobertura.

## Fluxo comum

~~~
entrada + configuração + catálogo validado
 → grafo e intervalos físicos dos vãos
 → plano de reforço + reservas + subfaixas de fiada
 → alocação conjunta de encontros, reforços e preenchimento
 → auditorias físicas globais e cross-band
 → resultado com retenções/falhas explícitas
 → adaptador de materialização Revit
~~~

Planejar antes de preencher os intervalos reservados. Não inserir peças depois
do solve e apagar colisões. Reserva restringe preenchimento; não permite
remover amarração, atravessar jamba ou invadir vão. Conflito com B34/B54,
T/X, trecho curto, topo ou outra abertura exige inviabilidade ou replanejamento
limitado com os mesmos gates, sem inventar prioridade normativa.
Rebuild de ARM recebe o mesmo contexto e revalida todo o plano após mudar nó.

Usar course_index + z_lo/z_hi + subcourse_id, distinguindo variante A/B de
fiada física. A/B não é cota. Auditorias same-band/cross-band usam volumes,
faces e vizinhança efetivos, inclusive 9 cm. Não aprovar por soma de bandas
alternativas que jamais seriam construídas juntas.

## A — LINTEL_COUNTERLINTEL

Porta geométrica que toca a base: acima. Janela: acima e abaixo.
ABERTURA e rótulo divergente exigem classificação/revisão explícita;
casos humanos sem reforço não viram exceções automáticas.

Para vão [u0,u1] × [zs,zh], membro superior h=9 cm observado ocupa
[zh,zh+h]; inferior [zs-h,zs]. Extensão [u0-bL,u1+bR] e comprimento
L=(u1-u0)+bL+bR. Catálogo oferece comprimentos discretos; política escolhe
apoio, simetria/excedente e desempate determinísticos.
≥9 cm é evidência TORRE EASY, não default aprovado.
Sem tipo/apoio viável: CATALOG_LENGTH_UNAVAILABLE ou LINTEL_NO_FEASIBLE_SUPPORT.

A faixa de 9 cm subdivide a fiada física. Peças adjacentes respeitam altura,
junta e interface com cortados. 9+1+9=19 pode fechar uma fiada; não generalizar
empilhamento a toda a parede. Validar suporte em alvenaria sólida real,
espaço lateral e altura disponível contra aberturas, extremos, nós e topo.
Nunca apoio fictício em vazio.

Família chamada VERGA pode exercer BELOW_SILL quando explicitamente mapeada
e apta. Tipo lógico, papel e nome da família permanecem separados.

## B — CHANNEL

Corrida de canaletas ocupa faixa de 19 cm: acima [zh,zh+19], abaixo [zs-19,zs].
Não é verga com família trocada: possui juntas entre peças, composição de
comprimento, continuidade e interação com o grafo na própria fiada.

ChannelRun: run_id, componentes sólidos contíguos, z_band, perfil U/J,
apoios, peças e conjunto opening_ids. Demandas vizinhas na mesma parede/faixa
podem compartilhar corrida apenas quando o intervalo intermediário é
materializável e passa os gates. Ordenação e união determinísticas evitam
duplicação. Lacunas mantêm componentes separados; envelope min/max não prova
continuidade nem capacidade estrutural.

Composição admite canais de 39/34/19 cm e variantes/cortes aprovados.
C39/C34/C19 podem ser rótulos; IDs CHANNEL_U_39/_34/_19 evitam confusão
com compensadores C09/C04. Canaleta J possui perfil/orientação próprios,
não substitui U só por dimensão semelhante.

Cotas fora da grade, inclusive offset humano de 1 cm, viram achado;
não deslocar vão nem ampliar tolerância. Apoio CHANNEL é política independente.
O mínimo negativo observado não autoriza suporte negativo.
Graute/armadura não foram relacionados peça a peça; não certificar
dimensionamento a partir da geometria de canaleta.

Corrida pode continuar além de um vão ou coincidir com topo apenas sob
política TOP_BOND_BEAM aprovada, com uma única ocupação e papéis múltiplos.
Escolher CHANNEL não cria cinta universal.

## Aceitação, falhas e determinismo

Nenhum volume no prisma de vão, sobreposição não permitida, comprimento
não positivo/não finito, largura incompatível, material sem mapping ou
crédito de cobertura duplicado. Juntas e amarração auditadas nas transições.
Rejeição preserva entradas/achados. Contexto incompleto, família faltante,
apoio insuficiente, grade incompatível e conflito de nó são erros distintos.

Cache inclui geometria, aberturas/vizinhos, ambas as políticas de estratégia,
catálogo, mapping e cortes. Provar cache on/off, ordem permutada e replay
no mesmo contrato. Nenhum cache novo ou ajuste de performance nesta missão.
