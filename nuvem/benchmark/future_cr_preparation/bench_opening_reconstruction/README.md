# BENCH-OPENING-RECONSTRUCTION — pacote diagnóstico

> **NADA AQUI É REFERÊNCIA APROVADA.** Todos os arquivos deste diretório
> são candidatos/evidência de diagnóstico, produzidos para instruir uma CR
> futura. Nenhum arquivo de
> `nuvem/benchmark/projects/**` foi lido para escrita nem alterado.

## Ordem de execução

```
python3 build_evidence.py      # -> reconstruction_evidence.json
python3 build_candidate.py     # -> candidate_reference_<proj>.json
                               #    candidate_input_<proj>.json (só TP1)
                               #    candidate_provenance.json
python3 compare_candidate.py   # -> comparison_report.json  (validadores)
python3 check_axis_gap.py      # confronta com a geometria MEDIDA do Revit
python3 solver_experiment.py   # -> solver_experiment_<proj>.json (roda o SOLVER)
```

`solver_experiment.py` copia o projeto para um diretório temporário e troca
só o `input.json`; o projeto oficial nunca é tocado.

## Arquivos

| arquivo | o que é |
|---|---|
| `reconstruction_evidence.json` | proveniência de **cada** abertura do gabarito: envelope, consenso, spread por fiada, nó mais próximo, par medido no Revit, trechos de parede medidos no mesmo eixo |
| `candidate_reference_<proj>.json` | gabarito com **só** as 19 aberturas da assinatura corrigidas — blocos, paredes, nós e fiadas idênticos |
| `candidate_input_<proj>.json` | idem para o `input.json` **do TP1** (o do TGD é `measured` e não é afetado) |
| `candidate_provenance.json` | o que foi mudado, de quanto, e com que evidência |
| `comparison_report.json` / `.md` | atual × candidato, por código de achado |
| `solver_experiment_<proj>.json` | efeito no SOLVER (fingerprint físico, contagens) |
| `CR_SPEC.md` | especificação executável da CR futura |

Leitura recomendada: `comparison_report.md` primeiro, depois `CR_SPEC.md`.
