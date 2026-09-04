# Testes

> **HISTÓRICO.** O texto abaixo e' um snapshot da sessao de 2026-08-26 e
> nao reflete o estado atual do repositorio. Em particular: `tests/`
> (raiz do repo) hoje TEM `run_tests.py` e um `test_script.py` grande -
> a afirmacao "esse arquivo especifico tambem nao existe mais" (final
> deste arquivo) e a afirmacao de que a suite antiga "nao existe mais
> neste repositorio" (abaixo) estao desatualizadas. Para o estado atual
> da suite em `tests/`, ver `tests/README.md`. O caminho local
> `C:\Users\CIVIX\.claude\plans\quiet-painting-petal.md` citado abaixo e'
> de uma maquina especifica de uma sessao anterior - nao e' uma
> dependencia deste repositorio. Preservado aqui como registro do
> raciocinio daquela sessao, nao como documentacao atual.

**Estado atual (2026-08-26):** esta pasta e' NOVA - a suite antiga
referenciada no docstring de `core/wall_modeling.py` (linhas ~107-111,
"`tests/run_tests.py` carrega este arquivo com a API do Revit/WinForms
substituida por dubles... Ver `tests/README.md`") e mencionada no historico
de sessoes anteriores (~130 testes) **nao existe mais neste repositorio** -
nao foi encontrado nenhum arquivo de teste antes desta sessao. Essa
referencia no docstring ficou orfa (aponta para uma suite que foi perdida
em algum momento entre sessoes, nao removida deliberadamente nesta). Nao
foi reconstruida por completo aqui - reconstruir os ~130 casos originais
(deteccao de paredes, grafo de encontros L/T/X, solver de blocos completo,
regras de modulacao, montagem de janelas com dubles de Revit/WinForms)
seria um projeto proprio, maior que o escopo desta sessao (ver plano em
`C:\Users\CIVIX\.claude\plans\quiet-painting-petal.md`).

## O que ESTA' coberto aqui

So' a logica PURA introduzida/alterada nesta sessao (FASE 1/2 do plano
acima), que vive em `core/engine/*.py` - modulos SEM nenhum import de
Revit/WinForms, entao rodam em qualquer Python 3 comum, sem stub nenhum:

- `test_progress.py` - `core/engine/progress.py::dispatch_progress_event`
  (o despachante que substituiu o closure `_progress_cb` que so' tratava 2
  argumentos e causava o travamento "Nao esta respondendo" reportado em
  producao - ver FASE 1 do plano). Cobre as 3 formas de chamada real
  (1/2/4 argumentos) e confirma que uma forma desconhecida nunca lanca.
- `test_modulation_broken_length.py` -
  `core/engine/modulation_math.py::evaluate_wall_block_length` (o campo
  novo `is_clean_cm`, FASE 2 do plano). Cobre especificamente o exemplo
  real que motivou a mudanca: 25,01cm precisa ficar `is_clean_cm=False`
  mesmo sendo `compatible=True` pela tolerancia larga da aritmetica de
  blocos, e 829,99791cm (ruido de geometria ja medido num projeto real,
  ver comentario de MODULATION_WHOLE_CM_TOLERANCE_CM) precisa continuar
  `is_clean_cm=True` (nunca falso-positivo por ruido de ponto flutuante).

## O que NAO esta' coberto (honesto, nao escondido)

Tudo que depende de `core/wall_modeling.py` importar de verdade (a maior
parte do motor - deteccao de paredes a partir do CAD, ETAPA 2-6 completas,
WinForms) precisa de um double/stub de
`pyrevit`/`Autodesk.Revit.DB`/`System.Windows.Forms` para sequer importar
o modulo (17 mil+ linhas, com classes que sub-classam `Form`/`IUpdater`
reais na definicao). Nao construido nesta sessao - validacao dessas partes
continua dependendo de rodar o botao de verdade no Revit (ou via
`mcp__revit-pyrevit__execute_revit_code`, ver memoria de sessoes
anteriores) at\u00e9 que essa infraestrutura de stub seja reconstruida.

## Como rodar

```bash
py -3 -m unittest discover -s tests -p "test_*.py" -v
```

(ou `python3` conforme o interpretador disponivel no seu PATH - ver nota em
`CLAUDE.md` sobre `python3 -m pytest tests/test_script.py -q`: esse arquivo
especifico tambem nao existe mais; use o comando acima ate' a suite ser
reconstruida.)
