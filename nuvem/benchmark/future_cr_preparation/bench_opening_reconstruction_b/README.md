# CR-B — RECONCILIAÇÃO DO GABARITO DE ABERTURAS — evidência reproduzível

> **Nada aqui é gabarito.** Todos os scripts são READ-ONLY: nenhum escreve
> em `nuvem/benchmark/projects/**`, nenhum altera constante de produção,
> nenhum chama o solver. `projection_split.py` gera o candidato em
> memória/temporário e o descarta.

Documento da CR: `docs/BENCH_OPENING_RECONSTRUCTION_B_RECONCILIATION.md`.

## Pré-requisito

Os scripts leem `repro_envelope.json` da pasta da CR-A, que **não é
versionado** (decisão da revisão independente do PR #22 — é regenerável
determinística e trivialmente). Regere primeiro:

```bash
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_a
REPO_ROOT=<raiz do repo> python3 repro_envelope.py
```

Todos os scripts aceitam `REPO_ROOT` no ambiente (padrão:
`/home/user/MeuBotao.pushbutton`).

## Ordem de execução

```bash
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b

# 1. ficha por caso: identidade fisica XY, envelope, consenso, juncoes,
#    trechos e aberturas MEDIDAS no mesmo eixo, pecas humanas nas jambas
python3 case_dossier.py

# 2. o que ocupa FISICAMENTE o vao (blocos de QUALQUER parede) e quais
#    eixos perpendiculares cruzam o hospedeiro
python3 void_occupancy.py

# 3. TESTE DA VERGA - porta tem alvenaria acima do vao; espaco entre duas
#    paredes nao tem
python3 lintel_test.py
python3 lintel_discriminates.py     # valida o teste nos 94/92 trechos

# 4. cada jamba esta confirmada por geometria MEDIDA? (so' TGD)
python3 measured_jamb_confirmation.py
python3 measured_vs_human.py
python3 measured_neighbourhood.py   # os 9 que o metodo da CR-A nao casou

# 5. um criterio ESTRUTURAL (sem limiar de largura) isola os 19?
python3 criterion_selectivity.py

# 6. o gabarito e' regeravel offline a partir dele mesmo?
python3 roundtrip_probe.py

# 7. um limiar de WALL_SPLIT_GAP_CM resolveria? (medido: nao)
python3 split_threshold_probe.py

# 8. projecao estrutural do candidato "duas paredes separadas"
python3 projection_split.py

# 9. tabelas markdown do documento da CR
python3 make_tables.py
```

## Arquivos

| arquivo | o que é |
|---|---|
| `case_dossier.py` / `.json` | ficha dos 19 casos por projeto, com as quatro fontes de verdade separadas |
| `void_occupancy.py` / `.json` | ocupação física do vão + eixos perpendiculares cruzando (a **reserva de nó**) |
| `lintel_test.py` / `.json` | cobertura do consenso pelas fiadas ACIMA, fiada a fiada |
| `lintel_discriminates.py` / `.json` | o teste da verga estratificado por procedência medida — prova que discrimina |
| `measured_jamb_confirmation.py` / `.json` | **19/19** com as duas jambas confirmadas por geometria medida (fim colinear OU face de perpendicular), resíduo ≤ 0,259cm |
| `measured_vs_human.py` / `.json` | divergências numéricas medido × humano (R1/R2/R3 da CR) |
| `measured_neighbourhood.py` / `.json` | por que o teste de eixo da CR-A casou só 10 de 19 (filtro de colinearidade de ±3cm) |
| `criterion_selectivity.py` / `.json` | C1/C2/C3 nos 94/92 trechos — **19/19 acertos, 0 falsos positivos** |
| `roundtrip_probe.py` / `.json` | o gabarito é reprodutível a partir do próprio `reference.json` — habilita a CR-B offline |
| `split_threshold_probe.py` / `.json` | nenhum `WALL_SPLIT_GAP_CM` separa os 19 sem destruir porta medida real |
| `projection_split.py` / `.json` | candidato "duas paredes separadas": +19 paredes, −19 aberturas, **0 blocos perdidos**, T→L |
| `make_tables.py` | gera as tabelas de §3 do documento |

## Tolerâncias de ANÁLISE usadas aqui

Não são tolerâncias de domínio e **não entram em nenhum arquivo de
produção**. Estão explícitas no topo de cada script:

| símbolo | valor | para quê |
|---|---|---|
| `COLLINEAR_OFFSET_CM` | 3,0 | "mesmo eixo" ao projetar parede do input |
| `LATERAL_CM` | 45,0 | busca ampliada de parede medida paralela deslocada |
| `PERP_REACH_CM` | 60,0 | até onde procurar eixo perpendicular cruzando |
| `FACE_TOL_CM` / `TOL_CM` | 1,0 / 0,3 | casar jamba com face de parede (classificação, nunca geometria gravada) |
| `HALF_BAND_CM` | 9,0 | meia espessura 7,0 + folga, para ocupação em planta |
