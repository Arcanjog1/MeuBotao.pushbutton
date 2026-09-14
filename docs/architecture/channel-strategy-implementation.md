# Estratégia CHANNEL — implementação
STATUS: IMPLEMENTADO — ESTRATÉGIA OFICIAL (decisão do usuário 2026-09-14, item A); LINTEL_COUNTERLINTEL não implementada.
Contrato de origem: [um motor e duas estratégias](opening-reinforcement-strategies.md) ·
[decisão](../decisions/DECISION-OPENING-REINFORCEMENT.md) (A–F registradas em 2026-09-14) ·
regras: seção 51 de [REGRAS](../../nuvem/REGRAS_MODULACAO_BLOCOS.md).

## Onde encaixa no motor comum

```
solve_building_blocks_all_courses(..., opening_reinforcement_strategy=None|"CHANNEL")
  -> free_to_top_openings + openings_extended_to_top           (so' CHANNEL: passagem livre ANTES do solve)
  -> solve por bandas + paridade                                (inalterado)
  -> _channel_tie_parity_trials                                 (so' CHANNEL: paridade do T com gates, 51.14)
  -> SAFE REPAIR + B19 residual                                 (inalterado)
  -> _record_unmodulated_walls                                  (inalterado)
  -> _apply_opening_reinforcement                               (só se CHANNEL; timing_s plan/validate/reaudit)
       plan_channel_reinforcement(course_candidates, walls, openings, course_band, ...)
       validate_channel_reinforcement(...)                      (validador independente)
       audit_all_walls_bond_quality(... catálogo + canaletas lógicas)
  -> result["opening_reinforcement"] = plano + achados + validação
```

`None` devolve o resultado **sem tocar em nada** (assinatura física idêntica —
`test_legacy_strategy_none_is_byte_identical_and_has_no_channel` e a bancada
Butantã: `94541746…` antes e depois). Nenhum segundo solver: o CHANNEL não resolve
nós, fiadas nem preenchimento; recebe as fiadas físicas já resolvidas.

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Regra física / planejamento | `nuvem/core/engine/opening_reinforcement.py` | demandas por abertura, corridas, fusão/cortes, travessia de T, divisão de B54, passagem livre, achados, validação |
| Catálogo lógico | `CHANNEL_LOGICAL_TYPES` (mesmo módulo) | `CHANNEL_U_39/_34/_19/_CUT`, dimensões nominais, realização |
| Mapeamento Revit | `CHANNEL_FAMILY_CATALOG_DEFINITIONS`, `load_channel_family_catalog` (`wall_modeling.py`) | família/tipo exatos, `Comprimento_bloco` de instância, `MISSING_FAMILY_MAPPING` |
| Criação | `create_building_blocks` | grava o comprimento de instância; se não gravar, apaga a instância e reporta |
| Handler | `_PostCreationEventHandler.opening_reinforcement_strategy`, `channel_catalog`, `_creation_catalog()`, `_ensure_opening_reinforcement_catalog()` | solve com a estratégia; **bloqueio antes de calcular/criar** com a lista de famílias/tipos de canaleta faltantes; criação com catálogo fixo + canaletas; assinatura beta inclui a estratégia |
| Tela de Configuração | `OPENING_REINFORCEMENT_UI_OPTIONS`, `_SetupForm._reinforcement_combo`, `_show_post_creation_window(opening_reinforcement_strategy=...)` | seção "7. Reforço de aberturas": Sem reforço (**padrão**), CHANNEL só explícito, VERGA/CONTRAVERGA visível e não executável; a estratégia da execução vem do formulário (preferência salva só pré-seleciona) |
| Fonte única | `_unify_candidates_with_courses` | após o pós-passe `candidates`/`collisions` = peças físicas de `course_candidates` |

O catálogo de canaletas **nunca** entra no catálogo de preenchimento (o solver
escolheria canaleta como bloco comum). Nomes de família não aparecem no módulo
físico.

## Contrato das peças planejadas

Cada canaleta é um candidato normal (mesmos campos de `_make_block_candidate`) com:

- `logical_code` ∈ `CHANNEL_U_39 | CHANNEL_U_34 | CHANNEL_U_19 | CHANNEL_U_CUT`;
- `length_cm` final; `instance_length_cm` só para `CHANNEL_U_CUT`;
- `cells_world = []`, `mirrored = False`;
- `reinforcement = {strategy, roles, run_id, opening_indices, source_codes, cut, policy_version}`;
  `cut = {kind: LENGTH_CUT, axis: LOCAL_U, original_dimension_cm: 39, final_dimension_cm}`.

`HEIGHT_CUT` não é usado pelo CHANNEL (a canaleta ocupa a fiada inteira); o caso
que o exigiria (topo fora da grade, 51.8) fica `NEEDS_RULE`.

Candidatos compartilhados entre fiadas (o motor reutiliza o mesmo dict em várias
fiadas da banda) **não são mutados**: toda troca cria dict novo
(`course_candidates_before_reinforcement` preserva o original).

## Política (`DEFAULT_CHANNEL_POLICY`)

| Chave | Valor | Evidência |
|---|---|---|
| `min_support_cm` | 19 | 119/126 lados humanos |
| `grid_tolerance_cm` / `grid_joint_allowance_cm` | 0,5 / 1,0 | 6616547 (220→221) |
| `merge_compensators`, `max_channel_length_cm` | sim / 39 | cortes humanos 9/14/24/29 |
| `observed_min_cut_length_cm` | 9 | menor KV humana |
| `free_to_top_tie_bounded_passages`, `tie_bounded_max_jamb_to_node_cm` | sim / 28,5 | PAR28 (27/27 cm) |
| `cross_tee_when_support_at_most_cm` | 0 | 3 vãos × 2 papéis cruzam; 6672349 (4 cm) não |
| `convert_blocking_along_ties`, `convert_along_tie_when_support_below_cm` | sim / 9 | 6627438 (4 cm) cruza; 6620076/6621711 (14 cm) não |
| `tie_split_lengths_cm`, `tie_split_min_stagger_cm` | 39…9 / 1,5 | comprimentos humanos; tolerância de junta |
| `contiguous_gap_cm` | 2,0 (+ ε) | junta de 1 cm + até 1 cm da folga da regra 30.8 |

Todos são parâmetros explícitos de política — nenhum é regra aprovada pelo
usuário; o `policy_version` acompanha cada peça.

## Achados e validação

Planejador: `MISSING_REQUIRED_CHANNEL` (com motivo `NO_PIECES_OVER_SPAN`,
`SPAN_NOT_COVERED`, `INELIGIBLE_PIECE_OVER_SPAN`, `TIE_OVER_SPAN`),
`CHANNEL_SUPPORT_LIMITED`, `CHANNEL_HEAD_OFF_GRID`, `CHANNEL_SILL_OFF_GRID`,
`CHANNEL_CUT_BELOW_OBSERVED_MIN`, `CHANNEL_THROUGH_T_SUPPORTED_PATTERN` (travessia de T, `SUPPORTED_PATTERN`, decisão D),
`CHANNEL_CROSSING_NO_ABUTMENT_PIECE`, `CHANNEL_TIE_SPLIT_NO_STAGGER`.

Validador independente (recalcula a demanda a partir das aberturas):
`MISSING_REQUIRED_CHANNEL`, `EXTRA_CHANNEL`, `CHANNEL_WRONG_COURSE`,
`CHANNEL_INVADES_OPENING`, `CHANNEL_COLLISION`, `CHANNEL_SUPPORT_BELOW_POLICY`
+ contagens `channel_top/bottom_expected/matched`.

## Limites conhecidos

- Cinta de topo não gerada (conflito 10.7, decisão F pendente).
- Topo/peitoril fora da grade sem solução (51.8, decisão E pendente).
- Travessia de T produz junta na face da parede que chega em 3 fiadas (51.6),
  como no humano; aceita (decisão D) sem relaxar a auditoria global.
- Apoio limitado é classificado pelo **assentamento real** na fiada de baixo
  (`bearing_*_cm`, 51.4): 6627438 apoia 4 cm sobre a pastilha C04 — VALID_ALTERNATIVE.
- Folga residual entre nós (30.8) e tolerância de ruído da pastilha (51.13)
  existem mas estão DESLIGADAS (auditoria 2026-09-14): 7719511 é limitação
  conhecida.
- Passagem livre abre só o vão (regra do usuário); o humano abre até as faces dos
  nós — conflito registrado em 51.9.
- A tentativa de paridade reconstrói o motor por nó candidato (Revit BUTANTÃ:
  solve 44,6 s × 17 s sem ela).
- Validador: `CHANNEL_OPENING_OVERCUT`, `CHANNEL_FREE_TO_TOP_NOT_OPEN`,
  `CHANNEL_ORPHAN_PIECE`; chaves físicas canônicas (sem `id()`).
- Canaleta J não usada.
