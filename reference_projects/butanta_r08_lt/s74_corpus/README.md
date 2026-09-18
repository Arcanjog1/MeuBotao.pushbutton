# BUTANTÃ R08_LT — corpus auditável da seção 74
STATUS: EVIDÊNCIA / NÃO NORMA.

Geometria mínima do 1º PAVIMENTO do BUTANTÃ, versionada em 2026-09-17, para que as
alegações da seção 74 possam ser refeitas por quem não tem o arquivo do Revit.

## Por que este corpus existe

Uma auditoria independente sustentou a seção 74 (SUPPORTED WITH LIMITATIONS) com
uma limitação material: os números foram medidos sobre a geometria real do projeto,
que **não estava versionada**. Sem ela, ninguém de fora conseguia reproduzir os nós
24/44/46, os controles 12/26, a parede 8284580 nem o hash do snapshot. Este corpus
fecha essa limitação. Ele não acrescenta argumento novo — torna o argumento
conferível.

A seção 74 (commit `2c55211`) mudou UMA comparação em
[`nuvem/core/engine/wall_stepper.py`](../../../nuvem/core/engine/wall_stepper.py),
dentro de `_t_intersection_room_ok`: o teste "cabe um B54 centrado no nó?" comparava
com `+ 1e-6` pés (0,3 micrômetro, epsilon de ponto flutuante) e passou a comparar com
a tolerância física `PIER_PHYSICAL_FIT_TOLERANCE_CM = 0,05 cm`, que o motor já
definia. A mudança é **semântica e deliberada**: a fronteira histórica de
cabe/não-cabe foi ampliada em até 0,05 cm. Não é correção de ruído de cálculo — o
erro aritmético puro é minúsculo; o que existe na planta é variação submilimétrica
REAL de modelagem (máxima observada aqui: 0,013251 cm). A flag nasce desligada; só o
fluxo CHANNEL a liga.

## Arquivos

| Arquivo | Papel |
|---|---|
| [geometry.json](geometry.json) | INPUT GEOMETRY — a planta que entra no motor |
| [t_nodes.json](t_nodes.json) | FATOS FÍSICOS ESPERADOS — os 37 encontros T |
| [wall_8284580.json](wall_8284580.json) | SAÍDA MEDIDA — o caso da parede |
| [snapshot_v1.json](snapshot_v1.json) | SAÍDA MEDIDA — conjunto físico por tolerância |

### geometry.json — INPUT GEOMETRY

- `schema_version`, `status` (`EVIDENCE_NOT_NORM`).
- `provenance`: `source_project`, `source_file`, `source_version`, `extraction_date`,
  `units`, `coordinate_system`, `level`, `wall_population`, `courses_solved` (17),
  `courses_ruler` (12), `wall_height_cm` (340,0), `extraction_script`,
  `engine_commit_s74`, `repo_commit_at_extraction`, `raw_inputs_not_versioned`
  (`file` / `sha256` / `bytes` das entradas brutas) e
  `input_order_is_part_of_the_input`.
- `walls` — 34 paredes de alvenaria, na ordem em que o Revit as entregou:
  `key` (`W01`…`W34`, a chave usada em todo o corpus), `p0_cm` / `p1_cm` (as duas
  pontas do eixo, em cm), `thickness_cm` (14,0 nas 34), `length_cm` e
  `provenance` (`revit_element_id`, `input_order`).
- `openings` — 44 aberturas: `key` (o ElementId), `center_cm` (centro do vão pela
  bounding box), `insertion_cm` (ponto de inserção da família), `hand` (vetor
  unitário), `width_cm`, `sill_cm` (peitoril), `head_cm` (peitoril + altura) e
  `provenance` (`revit_element_id`, `input_order`).
- `opening_variants.post_micro_adjustment_s66` — três aberturas com `center_cm`,
  `insertion_cm` e `delta_cm` (10,0 cm cada): o estado DEPOIS do microajuste da
  seção 66. As duas variantes estão versionadas para que os dois conjuntos de
  totais sejam reproduzíveis.
- `catalog` — as 6 famílias reais do projeto (`B19`, `B34`, `B39`, `B54`, `C04`,
  `C09`) com `length_cm`, `width_cm`, `height_cm`, `is_special_bond`,
  `is_compensator` e `cells_local` (`center_local`, `size_local`). `cells_local` não
  tem sufixo `_cm`: vem do catálogo lido no Revit e é entregue ao motor como está
  (ver `catalog()` em [`tools/audit/s74_corpus.py`](../../../tools/audit/s74_corpus.py)).

Nada em `geometry.json` diz "cabe" ou "não cabe". É só planta.

### t_nodes.json — FATOS FÍSICOS ESPERADOS

- `measured_with`: `engine_commit_s74`, `b54_half_room_cm` (27,0), `b34_room_cm`
  (34,0) e `physical_tolerance_cm` (0,05) — lidos das constantes do motor, não
  redigitados.
- `modeling_variation`: `max_modeling_deviation_cm` = **0,013251** com sua
  `max_modeling_deviation_definition` (maior afastamento do centímetro inteiro
  observado na geometria) e `max_modeling_deviation_by_source_cm`
  (`wall_length` 0,013251, `wall_endpoint` 0,013054, `t_room_min` 0,013251);
  `boundary_definition` e `boundary_nodes` (5) para os T em que a variação chega a
  decidir o veredito; `max_abs_deviation_at_boundary_cm` (0,012);
  `next_materially_insufficient_cm` (**4,001054**);
  `ratio_tolerance_over_max_modeling_deviation` (3,77) e
  `ratio_next_over_tolerance` (80,0).
- `t_nodes` — os 37 encontros T, ordenados por falta decrescente:
  - `key` — chave lógica `T@x,y` pela posição arredondada; não depende de ElementId,
    de índice de lista nem da ordem de entrada.
  - `position_cm`, `main_wall_key` (parede principal), `incoming_wall_key` (parede
    que chega).
  - `room_plus_cm` / `room_minus_cm` — espaço livre na principal de cada lado do nó;
    `room_min_cm` é o menor dos dois (é ele que decide o B54);
    `room_incoming_cm` é o espaço na parede que chega.
  - `shortfall_b54_cm` = 27,0 − `room_min_cm` e `shortfall_b34_cm` = 34,0 −
    `room_incoming_cm`. **Positivo = falta; negativo = sobra.**
  - `expected_ok_flag_off` / `expected_ok_flag_on` — o veredito de
    `_t_intersection_room_ok` com a flag desligada e ligada.
  - `provenance`: `bench_node_index` (o índice citado no relatório e nos testes),
    `main_revit_element_id`, `incoming_revit_element_id`.

O que os 37 dizem: **10** T reprovam o teste de espaço com a flag desligada e **7**
continuam reprovando com ela ligada. Exatamente **3** mudam de veredito:

| Nó (bancada) | Principal | Falta para o B54 | Controle na MESMA principal |
|---|---|---|---|
| 24 | W04 | 0,012 cm | 26 — sobra 0,012 cm, já passava |
| 44 | W02 | 0,003487 cm | 12 — sobra 0,003487 cm, já passava |
| 46 | W02 | 0,003487 cm | 12 — sobra 0,003487 cm, já passava |

Os controles são o argumento central: mesma parede principal, mesma magnitude, sinal
contrário. Os 7 que seguem reprovando nos dois estados faltam 4,001054 cm (nós 19,
20 e 39), 15,012000 / 14,996539 cm (nós 30 e 18) e 20,004794 / 19,996513 cm (nós 28
e 22).

Daí a justificativa do valor 0,05 cm: ele fica **3,8×** acima de toda a variação de
modelagem observada (0,013251 cm) e **80×** abaixo do primeiro caso materialmente
insuficiente (4,001054 cm). A saturação registrada em `snapshot_v1.json` NÃO
justifica o valor — ela prova apenas que não há precipício perto da fronteira.

### wall_8284580.json — o caso da parede

- `wall_key` (`W27`, o mesmo elemento 8284580) e `provenance` (`revit_element_id`,
  `human_source`, `nota`).
- `human_counts` — a composição humana desta parede: 48 `B39` + 12 `B34`, ou seja 60
  peças; `Z_END_ZONE` 12 é a classificação geométrica dos B34 pela régua, não peça
  extra.
- `metric` — a definição da divergência, implementada em
  [`tools/audit/s74_corpus.py`](../../../tools/audit/s74_corpus.py).
- `expected.flag_off` / `expected.flag_on` — `solver_counts`, `divergence`
  (`div`, `comp_delta`, `free_mid_delta`, `esp_delta`, `human_pieces`), `hard_gates`
  e `pieces_in_ruler`:

| | Composição do solver | Divergência |
|---|---|---|
| sem a seção 74 | 14 B39 + 51 B34 + 5 C09 + 1 B19 | 204,7 |
| com a seção 74 | 48 B39 + 11 B34 + 1 B19 | 3,3 |

### snapshot_v1.json — SAÍDA MEDIDA

- `normalization` (`S74_SNAPSHOT_V1`) e `normalization_note` com o formato exato da
  linha: uma linha por peça, `<fiada>|<parede>|<código>|<x>|<y>|<dx>|<dy>|
  <comprimento>|<espelhada>`, ordenadas, sem nenhum identificador de execução, tempo
  ou índice — só física.
- `legacy_bench_hash` — `bc261fe485de635a`, o hash citado no checkpoint; vinha do
  formato ad-hoc da bancada, que não está versionado. O hash auditável é o
  S74_SNAPSHOT_V1.
- `cases` — `label`, `tolerance_cm`, `pieces`, `sha256`, `ruler_pieces`,
  `ruler_codes` e `hard_gates`:

| Caso | Peças | sha256 |
|---|---|---|
| `flag_off` | 8746 | `c06f91a0b9848681…` |
| `tol_0_05` | 8719 | `320ba395683cc762…` |
| `tol_0_10` | 8719 | o MESMO `320ba395683cc762…` |
| `tol_0_30` | 8719 | o MESMO `320ba395683cc762…` |

- `opening_variant_cases` — a mesma medida sobre a variante
  `post_micro_adjustment_s66` (8733 peças com a flag desligada, 8706 com 0,05 cm).

Os portões duros (colisões, não-modular, sem apoio, invasão de vão) ficam
**0 / 0 / 0 / 0** em todos os casos gravados.

## Por que este teste não é circular

1. **A geometria é a entrada.** `geometry.json` traz eixos, espessuras, aberturas e
   catálogo. Nenhum campo ali decide se um B54 cabe.
2. **A decisão vem do motor real.** Os testes chamam
   `_t_intersection_room_assessment` e `_t_intersection_room_ok` de
   `nuvem/core/engine/wall_stepper.py`, e o solve completo liga a seção 74 pela flag
   do produto (`CHANNEL_T_ROOM_PHYSICAL_TOLERANCE_ENABLED`) — o mesmo caminho que o
   botão percorre no Revit. Nada disso é reimplementado em `tools/audit/`.
3. **A regra é conferida contra aritmética declarada, não contra si mesma.**
   `test_o_veredito_e_funcao_exata_do_espaco_medido_e_da_tolerancia` não compara o
   veredito do motor com um veredito gravado: compara com a própria semântica
   declarada da §74 — *o espaço medido mais a tolerância alcança a exigência?* —
   aplicada aos números medidos. Medido por mutação: prendendo
   `_t_intersection_room_ok` em `True` quebram **16** testes; prendendo em `False`,
   **10**. Um teste que só se autoconfirmasse não quebraria em nenhum dos dois.
4. **A régua é medida, não juízo.** O que `tools/audit/s74_corpus.py` implementa —
   contagem por parede, zona do B34, divergência, normalização do snapshot — opera
   sobre a saída do motor, nunca dentro dela.

### Onde a auditoria É circular, dito com todas as letras

A **decisão** não é circular (item 3). A **medição** é: todo campo de `t_nodes.json`
(`room_*`, `shortfall_*`) foi produzido chamando o próprio motor em
`extract_butanta_corpus.py`. Se a medição do espaço estivesse fisicamente errada e o
corpus fosse regerado com esse mesmo motor, os testes continuariam verdes — isso foi
verificado por mutação, não suposto.

O que limita esse círculo, e é real: os índices dos nós de interesse — 24/44/46 como
casos, 12/26 como controles — e a simetria de sinal entre caso e controle estão
escritos **no teste**, não no corpus. Um erro sistemático da ordem de 0,02 cm na
medição quebra cinco testes mesmo com o corpus regerado. Ou seja: **perto da
fronteira de 0,05 cm existe âncora; longe dela, não existe.** Quem quiser fechar o
círculo por completo precisa ancorar `room_min` de pelo menos um nó contra uma
medição independente do motor.

Limite honesto: `expected_*` é uma fotografia do comportamento em `2c55211`.
Documenta o que o motor decide, não o que ele deveria decidir. O juízo sobre o valor
0,05 cm está no argumento físico acima (variação de modelagem × falta real), não
nestes arquivos.

### O que este corpus não exercita

`_t_intersection_room_ok` é uma **conjunção**: espaço para o B54 na parede principal
**e** espaço para o B34 na que chega. Neste corpus só a primeira perna é exercida —
a boneca mais apertada dos 37 T tem **69,0002 cm** contra **34 cm** exigidos. A
segunda perna **não tem cobertura de regressão aqui**, e isso está declarado no bloco
`coverage` de `t_nodes.json` e conferido por
`test_o_corpus_declara_que_nao_exerce_a_perna_do_B34`, em vez de ficar invisível. A
perna do B54 é a que a §74 muda.

## Como reproduzir

Sem Revit, sem a bancada, sem entrada bruta — só o repositório:

```bash
python3 tools/audit/audit_s74_corpus.py            # PASS/FAIL caso a caso, sai 0 ou 1
python3 tools/audit/audit_s74_corpus.py --rapido   # pula só os 3 casos que resolvem
python3 -m pytest tests/test_s74_corpus_butanta.py -q
python3 -m pytest tests/test_s74_corpus_butanta.py -q -m "not slow"
```

O runner imprime uma linha por verificação com o valor medido ao lado do valor do corpus;
medido em 2026-09-17: **40 casos, 40 PASS, 0 FAIL, ~112 s** (0,3 s com `--rapido`); cada
configuração do solver leva cerca de 30 s nesta máquina.

São 39 testes no pytest; os 6 marcados `slow` são os que rodam o solve completo das 34
paredes (a parede 8284580, os portões duros, a saturação e a variante pós-microajuste) —
medido: **39 passaram**; os 33 rápidos passam em 0,3 s com `-m "not slow"`. O runner da
suíte antiga do motor, [`python3 tests/run_tests.py`](../../../tests/run_tests.py), não
cobre este corpus — ele roda os casos de `test_script.py`.

## Como regerar o corpus

```bash
MB_BENCH=<pasta da bancada> python3 tools/audit/extract_butanta_corpus.py
```

[`tools/audit/extract_butanta_corpus.py`](../../../tools/audit/extract_butanta_corpus.py)
reescreve os quatro JSON. As **entradas brutas NÃO estão versionadas**: são a
extração do Revit na bancada (`target_1pav.clean.json`, `human_1pav.clean.json`,
`rv/r_run4.json` — 7.908.044 bytes somados, cerca de 9 MB com a variante
`target_s72.clean.json`, que não tem hash gravado). O que o repositório guarda é o
`sha256` de cada uma, em `geometry.json` →
`provenance.raw_inputs_not_versioned`. Regerar exige a bancada; **auditar não**.

## Proveniência e limites

Extração read-only de `butanta testes.rvt` (cópia de trabalho do TARGET), Revit 2026,
2026-09-17. Unidades em **cm**; direção como vetor unitário; **coordenadas internas
do projeto Revit**, plano XY. **1º PAVIMENTO**, 34 paredes de alvenaria (seleção da
missão), todas de 14 cm, 44 aberturas, pé-direito 340 cm; o solve roda 17 fiadas e a
régua de comparação usa as 12 primeiras.

- A **ordem de entrada faz parte do input**: é a ordem em que o Revit entregou as
  paredes e as aberturas, e permutá-la muda o resultado do solver — comportamento
  anterior a esta missão, não introduzido por ela. Os testes de invariância cobrem
  translação e inversão das pontas da parede principal, não permutação.
- Duas **variantes de abertura**: a `original` (o que está em `openings`) e a
  `post_micro_adjustment_s66`, em que três aberturas andaram 10 cm.
- Esta é a planta **mínima** para a seção 74: eixo, espessura, abertura e catálogo.
  Não traz as peças humanas do pavimento (só as da parede do caso), nem pavimentos
  repetidos, nem sólidos — para isso, o acervo em
  [BUTANTÃ R08_LT](../README.md).
- IDs são locais do arquivo do Revit; `bench_node_index` é o índice da bancada,
  usado só para casar com o relatório e os testes.

## Este corpus não promove a modulação humana a norma

A única composição humana versionada aqui é a de **uma** parede (8284580 / `W27`), e
ela está no arquivo para medir a divergência daquele caso — não é gabarito, GOLDEN,
meta de convergência nem norma. Nenhum teste exige que o solver reproduza o humano.
O que os testes exigem é que o motor decida, sobre a geometria gravada, o que
decidiu, e que os portões duros continuem zerados. A queda de 204,7 para 3,3 é a
medida do caso, não um alvo aprovado.

[Portal do BUTANTÃ](../README.md) · [Referências humanas](../../README.md) ·
[inventário/hashes](../../inventory.json).
