# -*- coding: utf-8 -*-
"""`_ProgressConsole._pump_ui`: `Application.DoEvents()` SOMENTE na thread de UI.

CAUSA-RAIZ do congelamento da Tela 1, medida ao vivo no Revit real
(2026-09-10). Do perf_diag.log da execucao, com a instrumentacao ligada:

    +   94.983s tid=25324 console.set_progress DoEvents START
    + 2747.268s tid=25324 console.set_progress DoEvents END dt=2652.285s

`Application.DoEvents()` levou **2652,285s (44 minutos)** para retornar,
chamado de `tid=25324` - a THREAD DE FUNDO do solver (Dummy-1), nao a de
UI. A pilha capturada no mesmo instante:

    wall_modeling.py:10443 _worker
    wall_modeling.py:7757  analyze_created_walls_for_errors
    wall_stepper.py:7782   process_walls_one_by_one
    wall_modeling.py:12644 _progress_cb
    progress.py:52         dispatch_progress_event
    wall_modeling.py:8741  set_progress

Durante o periodo NENHUMA linha [PERF] de NENHUMA thread apareceu (o
amostrador acusou `parado=2652,323s`), e a amostragem feita de FORA do
processo - que nao depende da GIL - mostrou a thread do SO 5932
(MainThread) `Running` com 44,2s de CPU, 6x a segunda colocada, todas as
outras em `Wait`.

POR QUE o guarda antigo nao pegava: `_invoke_if_needed` decide por
`Control.InvokeRequired`, que devolve False quando o controle NAO TEM
HANDLE VIVO - nao apenas quando ja' se esta' na thread de UI. Com a janela
fechada/descartada (ou antes do handle existir), a thread de fundo caia no
corpo do metodo e chamava `DoEvents()` numa thread SEM bomba de mensagens.
Confirmado no mesmo log: `ui_invoke.direto (ja na thread de UI)` foi
registrado a partir de tid=25324, isto e', `Form.InvokeRequired` era False
para a thread de fundo.

Estes testes fixam o contrato do guarda sem precisar de Revit: o
`_pump_ui` real e' exercitado com um `Application` de mentira, checando os
dois lados - bombeia na thread dona, nao bombeia em nenhuma outra.
"""

import os
import sys
import threading

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import load_script  # noqa: E402

m = load_script.load()


class _ApplicationFalso(object):
    """Conta as chamadas de DoEvents e de qual thread vieram."""

    def __init__(self):
        self.chamadas = []

    def DoEvents(self):
        self.chamadas.append(threading.current_thread().name)


class _ThreadFalsa(object):
    """Substitui `_DotNetThread` para controlar o ManagedThreadId visto pelo
    console, sem depender do CLR."""

    def __init__(self, ident):
        self.ManagedThreadId = ident

    @property
    def CurrentThread(self):
        return self


def _console_minimo(ui_thread_id):
    """Uma instancia de `_ProgressConsole` sem construir WinForms: so' os
    atributos que `_pump_ui` realmente le'. Evita depender de handles de
    controle, que e' justamente o que o guarda antigo lia errado."""
    console = m._ProgressConsole.__new__(m._ProgressConsole)
    console._closed = False
    console._ui_thread_id = ui_thread_id
    return console


def _com_ambiente(app, thread_atual_id, fn):
    """Roda `fn` com Application/_DotNetThread trocados no modulo."""
    app_original = m.Application
    thread_original = m._DotNetThread
    m.Application = app
    m._DotNetThread = _ThreadFalsa(thread_atual_id)
    try:
        return fn()
    finally:
        m.Application = app_original
        m._DotNetThread = thread_original


def test_bombeia_na_thread_que_construiu_o_console():
    """Na thread de UI o comportamento e' o de sempre - `DoEvents()` roda.
    E' o que permite a janela repintar durante trabalho longo; sem isto a
    correcao teria trocado um congelamento por uma UI congelada."""
    app = _ApplicationFalso()
    console = _console_minimo(ui_thread_id=7)
    _com_ambiente(app, 7, console._pump_ui)
    assert len(app.chamadas) == 1, app.chamadas


def test_nao_bombeia_em_thread_diferente_da_de_ui():
    """O CASO REAL: a thread de fundo do solver chamando set_progress. Com o
    guarda antigo (`InvokeRequired` False por falta de handle) esta chamada
    chegava ao `Application.DoEvents()` e levou 2652s no Revit."""
    app = _ApplicationFalso()
    console = _console_minimo(ui_thread_id=7)
    _com_ambiente(app, 999, console._pump_ui)
    assert app.chamadas == [], (
        "DoEvents() foi chamado de uma thread que nao e' a de UI - e' "
        "exatamente o congelamento de 2652s: %r" % (app.chamadas,))


def test_console_fechado_nunca_bombeia():
    """Janela fechada/descartada: nem na propria thread de UI faz sentido
    bombear, e era justamente o estado em que `InvokeRequired` mentia."""
    app = _ApplicationFalso()
    console = _console_minimo(ui_thread_id=7)
    console._closed = True
    _com_ambiente(app, 7, console._pump_ui)
    assert app.chamadas == [], app.chamadas


def test_falha_ao_ler_a_thread_nao_bombeia_nem_propaga():
    """Se `ManagedThreadId` lancar (CLR indisponivel, objeto trocado), o
    guarda tem de FALHAR FECHADO - nao bombear - e nunca derrubar o solver.
    Uma falha de feedback de tela jamais pode parar a modulacao."""
    app = _ApplicationFalso()
    console = _console_minimo(ui_thread_id=7)

    class _Explode(object):
        @property
        def CurrentThread(self):
            raise RuntimeError("sem CLR")

    app_original, thread_original = m.Application, m._DotNetThread
    m.Application, m._DotNetThread = app, _Explode()
    try:
        console._pump_ui()   # nao pode levantar
    finally:
        m.Application, m._DotNetThread = app_original, thread_original
    assert app.chamadas == [], app.chamadas


def test_todos_os_metodos_do_console_passam_pelo_guarda():
    """Nenhum `Application.DoEvents()` solto pode sobrar dentro do
    `_ProgressConsole`: o unico permitido e' o de dentro do proprio
    `_pump_ui`. Sem esta checagem, um metodo novo (ou um merge) reintroduz
    o congelamento sem que nenhum outro teste perceba."""
    import inspect
    fonte = inspect.getsource(m._ProgressConsole)
    linhas = [l.strip() for l in fonte.split("\n")]
    soltos = [l for l in linhas if l == "Application.DoEvents()"]
    guardados = [l for l in linhas if l == "self._pump_ui()"]
    assert len(soltos) == 1, (
        "esperado exatamente 1 DoEvents (dentro de _pump_ui), achei %d" % len(soltos))
    assert len(guardados) >= 6, (
        "os metodos do console deveriam bombear via _pump_ui; achei %d" % len(guardados))
