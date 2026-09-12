# Recomendação de CI — pytest e `runner --check` (2026-09-12)

**Estado observado** (`.github/workflows/check-project-status.yml`, main
`6439669`): o único workflow valida a **entrega documental**
(`tools/documentation/validate.py` + seus `unittest`). Nenhum teste do
solver e nenhum benchmark roda no CI. A suíte completa (`pytest tests`)
leva ~1h em máquina local (regressões consolidadas de 2026-09-11: 1h05);
os testes marcados `slow` são o benchmark real (TP1 ~3,5 min, TGD ~2,2 min
por rodada, várias rodadas por teste).

**Recomendação** (PR separado, não incluído na missão de saneamento para
não ampliar o risco):

1. Job rápido em todo PR/push: `python -m pytest tests -m "not slow" -q`
   (poucos minutos, sem Revit; `tests/revit_stubs.py` supre a API).
2. Job lento manual/agendado (`workflow_dispatch` + `schedule` noturno):
   `python nuvem/benchmark/runner.py --all --check` (régua V1, histórica)
   e `python nuvem/benchmark/runner.py --all --check --version v2`
   (régua V2, topologia do motor atual).
3. Só depois disso, tornar o job rápido *required check* (configuração
   administrativa de proteção de branch, fora do repositório).

Esboço:

```yaml
name: Testes do solver e benchmark
on:
  pull_request: { branches: [main] }
  push: { branches: [main, 'claude/**', 'codex/**'] }
  workflow_dispatch:
  schedule: [{ cron: '0 3 * * *' }]
permissions: { contents: read }
jobs:
  fast:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install pytest
      - run: python -m pytest tests -m "not slow" -q
  benchmark:
    if: github.event_name == 'workflow_dispatch' || github.event_name == 'schedule'
    runs-on: ubuntu-latest
    timeout-minutes: 90
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: python nuvem/benchmark/runner.py --all --check
      - run: python nuvem/benchmark/runner.py --all --check --version v2
```

Observações: `--check` sai com 1 em regressão contra o baseline; V1 e V2
são réguas independentes (ver `nuvem/benchmark/README.md`, "Réguas
versionadas"). Falhas históricas conhecidas da V1 (registradas nos
checkpoints) precisam ser resolvidas ou explicitamente listadas antes de
o job lento virar bloqueante.
