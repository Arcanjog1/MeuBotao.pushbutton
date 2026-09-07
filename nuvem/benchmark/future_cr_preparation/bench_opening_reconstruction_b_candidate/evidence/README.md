# Evidência do candidato — o que está aqui e o que NÃO está

Tudo neste diretório é **derivado e reprodutível** a partir do gabarito
oficial em modo leitura. Nada aqui é gabarito.

## Commitado

| arquivo | o que é |
|---|---|
| `candidate_manifest.json` | versão, proveniência, os 19 casos `C1`, invariantes por bloco, mapa de identidade (`stable_key` → `W0xx`), linhagem hospedeira → filhas, e o **`sha256` esperado** dos 4 arquivos por projeto |
| `junction_analysis.json` | todo nó cujo tipo muda (`T→L`, `AUSENTE→T/L`, `T→AUSENTE`): geometria antes/depois, participantes, e a ocupação física do nó **fiada a fiada**, com dono de cada peça |
| `divergences.json` | R1/R2/R3 com as quatro fontes lado a lado (medido / humano / reconstrução atual / candidato) |
| `solver_projection.json` | validadores sobre os 3 gabaritos + solver de produção sobre as 3 entradas por projeto, achados por código |
| `<proj>/input_candidate.json` | a **entrada do solver** derivada do candidato (115/116 paredes) |
| `<proj>/input_roundtrip.json` | a entrada de **controle** (STATE_R, sem corte) |

## NÃO commitado — reproduzível por comando

`<proj>/reference_candidate.json` e `<proj>/reference_roundtrip.json`
(~8,5 MB cada). Regenere com:

```bash
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate
CR_B_OUT=/tmp/cr_b_candidate python3 build_candidate.py
sha256sum /tmp/cr_b_candidate/*/*.json      # confira contra candidate_manifest.json
```

Determinismo verificado em 3 processos novos: os 8 `sha256` batem.
