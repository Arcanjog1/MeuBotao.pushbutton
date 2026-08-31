# Baselines do gate de metricas

Cada arquivo aqui e' uma baseline versionada contra a qual o gate compara
as metricas de uma rodada. E' isto que faz uma regressao numerica
reprovar a run mesmo com o Claude dizendo OK e o Codex dizendo
`APPROVED` (secao 7 do pedido).

## Formato

```json
{
  "<nome da metrica>": {
    "value": 91,
    "direction": "higher_is_better",
    "tolerance": 0
  }
}
```

- `direction`: `higher_is_better` | `lower_is_better` | `exact`
- `tolerance`: folga absoluta antes de considerar regressao (use para
  metricas ruidosas, como tempo de execucao).

## Como ligar

1. Faca a rodada produzir `.ai-team/metrics.json` com os numeros atuais,
   no formato `{"<nome>": <numero>}`.
2. Crie `project_metrics.json` neste diretorio com os valores de
   referencia (o caminho vem de `gates.metrics.baseline_file` na config).

Sem baseline, o check fica `SKIPPED` - o gate **nunca** inventa um numero
que nao mediu, e `SKIPPED` nunca vira `PASS`.

## Exemplo

`project_metrics.json.example` mostra o caso citado no pedido: se
`openings` cair de 91 para 89, o gate reprova a run.
