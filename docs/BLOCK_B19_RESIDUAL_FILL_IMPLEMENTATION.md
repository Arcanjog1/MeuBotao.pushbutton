# RELATÓRIO FINAL — B19 RESIDUAL FILL (versão corrigida pós-revisão)

`CR-BLOCK-B19-RESIDUAL-FILL-IMPLEMENTATION` (2026-09-05, corrigida na
revisão final de integração do PR #19). Implementa a decisão humana
aprovada sobre B19 em cima da evidência de domínio já coletada em
`docs/BLOCK_B19_JUNCTION_DOMAIN_EVIDENCE.md` (investigação apenas,
`REQUIRES_HUMAN_DOMAIN_APPROVAL`, nenhum código tocado na época). Regras:
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, seção 35 (fonte oficial e completa —
este relatório é o resumo narrativo, a seção 35 é a autoridade em caso
de divergência).

## HISTÓRICO — por que este relatório foi reescrito

A primeira versão desta CR (commit inicial do PR #19) reportava "8/8
candidatos aceitos no TP1, APROVADO PARA INTEGRAÇÃO". Uma revisão
independente (`cr-verification`) auditou essa alegação diretamente contra
os dados do rebuild real e encontrou uma falha crítica na condição de
domínio: **nenhum dos 8 candidatos aceitos tinha uma peça de amarração
real cobrindo o MESMO nó na MESMA fiada onde o B19 estava** (0 de 102
fiadas auditadas). A condição realmente verificada pela primeira versão
era mais fraca do que a decisão aprovada — bastava a OUTRA ponta da
mesma parede fechar com peça real, o que não corresponde ao que foi
autorizado. Esta versão do relatório documenta a implementação corrigida
e o resultado honesto medido depois da correção.

## Base

```
origin/main = 209695d5559b53fe4cc8a92300779a8ae73b7c1d  (confirmado)
```

Contém: NODE-FILL (PR #17), ARM SAFE REPAIR GATE FIDELITY (PR #18),
`NODE_FILL_OPPOSITE_COURSE_ENABLED = True`, `ARM_ROLE_SAFE_REPAIR_ENABLED
= True`.

## Branch / HEAD

```
branch: claude/cr-block-b19-residual-fill-uythsk
base:   origin/main @ 209695d5 (branch nova, sem cherry-pick)
```

## Regra B19 anterior (histórica, ainda vale fora da condição nova)

Estrita e incondicional: B19 nunca perto de amarração (nó L/T/X, ponta ou
meio de parede), só em vão de abertura ou ponta livre de verdade —
`_corner_single_element_candidate` nunca oferece B19 fora dessa condição
nova, e a rede de segurança `audit_wall_bond_quality`/`HALF_BLOCK_NEAR_
TIE` bloqueia qualquer B19 lançado perto de amarração sem prova
geométrica direta.

## Regra B19 nova (versão final aprovada — ver seção 35.1 das regras)

B19 é FILL, **nunca TIE**. Para toda fiada física onde exista um B19
marcado como fill residual, tem que existir, no **MESMO NÓ** e na
**MESMA FIADA**, uma peça de amarração real e íntegra (B34/B54) cobrindo
geometricamente o ponto físico do nó — vinda de qualquer parede
participante do nó (a própria ou a perpendicular). B19 nunca é a peça de
amarração, nunca ocupa o ponto físico do nó da OUTRA ponta, nunca
substitui B34/B54. Depende do TRECHO RESIDUAL medido, nunca do
comprimento total da parede. **Não basta a outra ponta da mesma parede
fechar com peça real** — essa era a condição insuficiente da primeira
versão, corrigida nesta revisão.

## Causa-raiz (duas camadas — ver seção 35.2 das regras)

**Camada 1** (bug de implementação, corrigido): `_wall_reserved_range_ft`
reservava um valor FIXO (20cm, o topo da faixa aprovada) na ponta oposta
— isso só produzia o room correto de 34cm na ponta TIE quando o resíduo
real era exatamente 20cm (coincidência do TP1, paredes de 54cm). Para
qualquer resíduo entre 15-19cm a reserva fixa teria subestimado a
necessidade da ponta TIE, deixando-a ainda degradada. Corrigido com
reserva **dinâmica** (`length_ft - CORNER_B34_ROOM_FT`, por parede).

**Camada 2** (achado de domínio, o motivo real do resultado zero mesmo
após a correção da camada 1): mesmo com a reserva corrigida, medir o TP1
real mostrou que a ponta TIE e a ponta FILL da mesma parede são nós
DIFERENTES — e o nó de FILL nunca é amarrado por nenhuma peça em nenhuma
fiada onde o B19 esteja. O nó É amarrado, mas pela parede perpendicular,
em fiadas de PARIDADE OPOSTA à do B19 (padrão de alternância par/ímpar
do canto L). Medido explicitamente: **0 de 102 fiadas** com
`B19_RESIDUAL_FILL` (nos 8 candidatos que a versão original aceitava)
tinham amarração real cobrindo o MESMO nó na MESMA fiada.

## Implementação corrigida

Reparo pós-hoc isolado (`repair_b19_residual_fill`,
`nuvem/core/engine/wall_stepper.py`), mesmo padrão seguro de
`repair_arm_role_isolated_edges` — candidato → pin → reconstrução REAL
multi-banda via `rebuild_fn` → hard gates → aceita ou reverte.
Detalhamento completo das 9 correções: seção 35.3 das regras. Resumo:

1. Fórmula única de resíduo (`_b19_residual_span_cm`), usada em
   elegibilidade, reserva e colocação (antes havia 3 fórmulas
   quase-iguais).
2. Reserva DINÂMICA por parede (não mais uma constante fixa).
3. **Gate de integridade do nó** (`_b19_tie_integrity_ok`, novo, central
   desta revisão) — exige peça de amarração real cobrindo geometricamente
   o MESMO nó na MESMA fiada, vinda de qualquer parede do nó; falha em
   qualquer fiada rejeita o candidato inteiro.
4. Estado por nó como CONJUNTO (`_b19_residual_fill_for_walls`), nunca
   mais escalar único.
5. Ordem de tentativa canônica geométrica (`_canonical_node_sort_key`),
   nunca por `end_index`/orientação de desenho.
6. Escopo dos hard gates ampliado (`_b19_candidate_dirty_scope`) —
   paredes perpendiculares dos dois nós envolvidos entram nos gates de
   compensador consecutivo e cobertura (mesmo padrão do SAFE REPAIR do
   ARM); pega uma regressão real que a versão original deixaria passar
   em `wall_idx=93` do TP1 (18 sequências novas de compensador
   consecutivo).
7. Revalidação final pós-combinação — garante `accepted[] ⟹ efeito
   físico presente no resultado final entregue`.
8. `audit_wall_bond_quality` (`wall_modeling.py`): isenção do
   `HALF_BLOCK_NEAR_TIE` agora verifica a condição geométrica
   diretamente (defesa em profundidade), nunca confia só na etiqueta
   `placement_reason`.
9. Contrato de `arm_role_safe_repair=False` restaurado — volta a
   desligar TODO o pós-processamento (ARM e B19), idêntico ao
   comportamento anterior a esta CR.

## RESULTADO MEDIDO — zero efeito no corpus atual

Com o gate de integridade do nó corretamente implementado, **os 8
candidatos que a versão original aceitava no TP1 passam a ser
rejeitados** (`no_tie_covering_node`, nas 16 tentativas — 8 paredes × 2
atribuições cada). TGD e Piloto continuam com 0 candidatos elegíveis:

| projeto | candidatos elegíveis | aceitos | rejeitados | fingerprint com B19 vs sem B19 |
|---|---|---|---|---|
| TP1 | 8 | **0** | 16 (todos `no_tie_covering_node`) | idêntico |
| TGD | 0 | 0 | 0 | idêntico |
| Piloto | 0 | 0 | 0 | idêntico |

**O mecanismo, corretamente implementado e testado, não produz NENHUM
efeito físico no corpus de referência atual.** Nenhuma parede do TGD,
TP1 ou Piloto tem hoje uma atribuição fill/tie onde o nó de fill fique
coberto por amarração real na MESMA fiada — o padrão de alternância
par/ímpar do canto L sistematicamente amarra o nó só nas fiadas
complementares às que o B19 ocuparia. Consequências:

- **Zero risco de regressão**: fingerprint `walls_blocks` idêntico nos
  três projetos, com e sem `B19_RESIDUAL_FILL_REPAIR_ENABLED`.
- **Zero ganho prático hoje**: os números de melhoria reportados na
  primeira versão deste relatório (`COMPENSATOR_CONSECUTIVE` −168 no
  TP1, `COVERAGE_GAP_IN_ROW` −18, etc.) vinham exatamente dos 8
  candidatos agora corretamente rejeitados — retirados desta versão por
  não se sustentarem sob a condição de domínio correta.
- O mecanismo fica pronto, correto e testado para o dia em que o corpus
  tiver um caso onde a condição de domínio seja fisicamente satisfeita,
  ou para uma CR futura (decisão de domínio à parte, não autorizada
  aqui) que trate a alternância par/ímpar como amarração válida "ao
  longo da altura".

## Achado adicional não bloqueante

`B19_RESIDUAL_FILL_MIN_CM = 15.0` permite elegibilidade de parede para
resíduos tão baixos quanto 15cm, mas B19 é um bloco de catálogo fixo de
19cm — nunca cabe fisicamente em menos de 19cm de room. Paredes com
resíduo 15-18cm nunca produzem um B19 real na colocação (o candidato é
tentado, custando um rebuild extra, mas nunca é aceito porque
`_b19_tie_integrity_ok` exige `saw_any_fill=True`, que nunca ocorre). Não
é um bug de comportamento incorreto — decisão do usuário se vale a pena
estreitar a constante para ~19cm ou manter como está (documentado,
inofensivo). Ver seção 35.5 das regras.

## Casos negativos (continuam válidos, verificados por teste direto)

- 69cm L-L (resíduo 34cm — o par humano `B34+B34` exato, zero B19): fora
  da faixa, nunca vira candidato.
- Resíduo 11cm / 39cm: fora da faixa, nunca vira candidato.
- Parede com nó de MEIO (main wall de T/X que atravessa): desqualificada
  por topologia.
- Ponta FREE_END: desqualificada.
- Resíduo compatível mas as pontas já fecham com peça real: nunca tenta
  reparar o que já funciona.
- Nó marcado para OUTRA `wall_idx`: nunca vaza — a reserva e a
  preferência por B19 ficam isoladas por parede.
- Sem marca (`nodes=None`) — nunca gera B19, comportamento antigo
  intacto para todo chamador que não passa pelo reparo.

## Tests

`tests/test_block_b19_residual_fill_implementation.py` — reescrita
completa na revisão (T1-T53): **65 rápidos + 5 `slow`, todos passing**.
Cobre topologia; fórmula única de resíduo na matriz completa
(14,9/15/18/19/20/20,1cm); reserva dinâmica (prova 34cm de room para
qualquer resíduo na faixa); isolamento do estado por `(nó, parede)` via
conjunto; preferência B19 só quando marcado E com room fisicamente
suficiente (19-20cm); o gate de integridade do nó em 11 variações
(próprio nó/parede perpendicular, fiada errada, nó errado, peça
não-amarração, peça longe demais, B54 também conta, B19 sozinho
rejeita, uma fiada sem tie reprova a parede inteira, corpo inteiro da
peça); os hard gates; orquestração com `rebuild_fn` falso
(reversibilidade, `accepted ⟹ efeito no resultado final`, revalidação
pós-combinação, ordem canônica); invariância à reversão dos endpoints;
`HALF_BLOCK_NEAR_TIE` com defesa em profundidade; corpus real
(TP1/TGD/Piloto, resultado honesto de zero aceitos, determinismo,
contrato de `arm_role_safe_repair=False` preservado).

## Full suite

Ver relatório de revisão final (seção "Full suite" do report entregue ao
usuário) para os números definitivos desta sessão. Nenhum teste
desabilitado; nenhuma falha NOVA além da já conhecida
(`test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]`,
`JUNCTION_MISSING_BINDING` 8→9, P3 — BENCHMARK_ARTIFACT, seção 32).

## Production diff

Dois arquivos de produção tocados (autorizado explicitamente pelo
usuário, com relato antes de cada extensão de escopo):

- `nuvem/core/engine/wall_stepper.py` — bloco "CR-BLOCK-B19-RESIDUAL-
  FILL-IMPLEMENTATION" reescrito na revisão (nova fórmula única, novo
  gate de integridade geométrica do nó, estado por conjunto, ordem
  canônica, escopo de gates ampliado, revalidação final) + 2 funções
  existentes estendidas (`_wall_reserved_range_ft`,
  `_corner_single_element_candidate`) com desvio ADITIVO.
- `nuvem/core/wall_modeling.py` — `B19_RESIDUAL_FILL_REPAIR_ENABLED` +
  fiação em `solve_building_blocks_all_courses` (contrato de
  `arm_role_safe_repair=False` restaurado nesta revisão) +
  `audit_wall_bond_quality` com defesa em profundidade geométrica na
  isenção `HALF_BLOCK_NEAR_TIE`.

Sem mudança em `wall_pairing.py`, `solve_l_corner`/`solve_t_intersection`
(lógica de decisão em si), tolerâncias, ou special-case por
`wall_idx`/projeto.

## Baseline diff

`baseline.json` do TP1 **NÃO foi tocado** por esta CR. Como o resultado
medido do mecanismo corrigido é fingerprint-idêntico ao estado sem o
reparo (zero candidatos aceitos em todo o corpus), não há nenhuma
melhoria nem regressão real a refletir no baseline — a atualização de
baseline reportada como pendente na primeira versão deste relatório
deixou de fazer sentido: não há diferença nenhuma para aprovar.

## Reference diff

ZERO — nenhum `reference.json`/`reference_score.json` tocado.

## Deferred / out-of-scope

- NODE-FILL e Gate Fidelity: não tocados (flags inalteradas, testes
  próprios intactos).
- Rotated corners (`OUT_OF_SCOPE_ROTATED_CORNER`): não tocados.
- `W039`↔`W041`: não tocado.
- TGD sem casos reais desta regra na reconstrução atual: limite de
  escopo documentado, não um defeito.
- Alternância par/ímpar do canto L como amarração válida "ao longo da
  altura": possível CR futura, decisão de domínio separada, NÃO
  autorizada aqui.

## Veredito

O mecanismo implementa exatamente a decisão de domínio aprovada (B19
nunca é amarração; exige peça real cobrindo o MESMO nó na MESMA fiada,
prova geométrica contra o rebuild real, nunca só a etiqueta), com todos
os hard gates do SAFE REPAIR mais os acréscimos desta revisão
(integridade do nó, escopo de vizinhas, revalidação final), determinismo
provado, NODE-FILL/Gate Fidelity/rotated corners/`W039`-`W041`
preservados intactos, `baseline.json`/`reference.json` intocados (diff
zero). **Efeito medido no corpus de referência atual: ZERO** (0
candidatos aceitos em TGD/TP1/Piloto) — risco de integração é, por isso,
também zero, mas o benefício prático imediato também é zero até que o
corpus tenha um caso fisicamente compatível com a condição de domínio
aprovada.

**NÃO MESCLADO. Aguarda autorização explícita do usuário para merge.
Nenhum monitoramento automático ativado.** Veredito formal desta revisão
entregue separadamente ao usuário no relatório de fechamento do PR #19.
