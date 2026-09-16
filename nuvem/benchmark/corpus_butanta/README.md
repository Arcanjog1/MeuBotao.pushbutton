# Corpus BUTANTÃ — área de preparo

Estrutura das fixtures mínimas dos defeitos físicos reais do BUTANTÃ.
**Não é gabarito** e **não entra no portão de corpus** enquanto o PR #42
estiver mudando a física.

## O problema que isto resolve

Vazado menor do B34, apoio físico, especiais encostados, canaleta e
microajuste de abertura são a área de desenvolvimento ativo — e a que
**não tem nenhuma fixture permanente**. O que existe é script avulso em
`docs/checkpoints/evidence/_scripts/`, que é registro datado de uma
sessão, não corpus mantido: se sumir, nada quebra, e uma regressão em
qualquer um desses defeitos passa despercebida.

## O que tem aqui

```
fixtures/<grupo>/<caso>/
    input.json               geometria de entrada, schema_version 2 do benchmark
    expected.PENDING.json    o princípio e a asserção que vai valer — sem número de saída
```

| Grupo | Caso | Princípio |
|---|---|---|
| `b34_alignment` | `b34_single_wall` | vazado menor do B34 alinhado entre fiadas vizinhas (§52) |
| `b34_alignment` | `b34_pair_courses` | há configuração em que só o giro do PAR alinha |
| `channel_window` | `window_head_sill` | canaleta na verga + uma única sob o peitoril (§41) |
| `channel_door` | `door_head_only` | porta: canaleta na verga, nenhuma abaixo |
| `t_with_b54` | `t_jamb_on_incoming_face` | canaleta cruza o nó T; B54 sobre o vão é dividido (§51) |
| `special_clusters` | `c09_c09_upright` | `C09+C09` em pé encostados são proibidos (§56.2) |
| `special_clusters` | `c04_c04_span` | `C04+C04` vira o compensador do vão total (§54) |
| `under_window` | `sill_joint_1_6cm` | junta de ~1,6 cm é argamassa, não vazio |
| `opening_adjustment` | `strip_20_35cm` | faixa de 20–35 cm entre peça de nó e jamba (§66) |
| `support` | `small_block_over_empty_course` | peça pequena não fica suspensa sobre fiada vazia (§53) |

Geradas por `build_fixtures.py`, que é determinístico — rodar de novo não
muda byte nenhum (provado em `tests/test_corpus_butanta_fixtures.py`).

## O que deliberadamente NÃO tem

**Gabarito.** Nenhum `expected.json`, nenhum `baseline.json`, nenhum
número de saída do solver. Enquanto o #42 muda a física, congelar a saída
corrente transformaria um estado em movimento em "verdade" — e
`golden/compare.py::_critical_regressions` conta código novo como
**regressão crítica**, o que faria BUTANTÃ, TGD e TP1 aparecerem
vermelhos de uma vez.

Cada caso traz, no lugar, um `expected.PENDING.json` que diz em texto
**qual asserção vai valer** quando houver referência autorizada. O teste
`test_expected_declarado_como_pendente_e_nao_como_gabarito` quebra se
alguém gravar um `expected.json` ou `baseline.json` aqui sem passar pela
autorização.

## Por que fica fora de `projects/`

`runner.list_projects()` varre `nuvem/benchmark/projects/` e devolve todo
diretório com `input.json`. Um projeto novo ali entraria **hoje** nas
parametrizações de `tests/regression/test_benchmark_baselines.py` e
mudaria o portão de corpus com o #42 em voo. O teste
`test_fixtures_nao_entram_no_portao_de_corpus` fixa isso: a lista
continua sendo exatamente `piloto_sintetico_2x2`, `torre_easy_lo_r00_tgd`
e `torre_easy_lo_r00_tp1`.

## Não overfit

Nenhuma fixture usa `ElementId`, nome `W0xx`, coordenada de projeto ou
qualquer identidade do BUTANTÃ — há teste que reprova se entrar. As
paredes se chamam `A`/`B`, as medidas são em cm no referencial local, e o
catálogo é o catálogo real do domínio (B39/B34/B54/B19/C09/C04), não uma
invenção da fixture. Trocar as medidas gera o caso equivalente de outro
projeto: o que a fixture fixa é a **relação física**, não o número.

Cada fixture cabe em 1–3 paredes e no máximo 2 aberturas, e há teste que
reprova se crescer — o valor delas está em caber num portão rápido.

## Próximo passo (missão separada)

Depois que o #42 estabilizar: medir cada caso, decidir o nível de cada
asserção **medindo o projeto humano antes** (a régua da §59 — um validador
que reprova o projeto humano de referência está errado, não o projeto),
capturar a referência com `--save-baseline` autorizado e migrar os casos
para `projects/butanta_r08_lt_1pav/`.
