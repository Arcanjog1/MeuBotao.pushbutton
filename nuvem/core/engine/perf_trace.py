# -*- coding: utf-8 -*-
"""Rastreamento TEMPORARIO de tempo do caminho real do botao (DIAGNOSTICO).

Existe por causa de um sintoma medido no primeiro beta controlado
(2026-09-09): a bancada de 2 paredes / 0 aberturas fica minutos em
"Preparando o solver...", enquanto a MESMA entrada resolve em
milissegundos fora do Revit. As medicoes offline nao explicam o sintoma
porque o benchmark offline exercita `_execute_solve` com dubles de XYZ/
Line, e o botao dispara `analyze` com os tipos REAIS do Revit, dentro do
ExternalEvent - dois caminhos e dois ambientes diferentes.

Modulo PURO (sem Revit, sem UI): so' `time`/`os`/`threading`. Escreve uma
linha por marco num arquivo de texto, porque o sintoma e' justamente a UI
nao atualizar - um log que depende da janela nao serviria de prova.

Nao altera NENHUM comportamento: todas as chamadas sao no-op quando
desligado, e cada uma esta' protegida por try/except (uma falha de
instrumentacao nunca pode derrubar o solver, mesma postura de
`dispatch_progress_event`).

Ligar/desligar: variavel de ambiente `MODULACAO_PERF_TRACE=1` (padrao:
ligado em beta controlado, ver `enable`). Arquivo padrao:
`%LOCALAPPDATA%\\MeuBotaoPushbutton\\perf_diag.log`.
"""

import os
import threading
import time

__all__ = [
    "enable", "disable", "is_enabled", "log_path", "mark", "span", "reset",
]

_ENABLED = False
_PATH = None
_LOCK = threading.Lock()
_T0 = None


def _default_path():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or "."
    return os.path.join(base, "MeuBotaoPushbutton", "perf_diag.log")


def enable(path=None):
    """Liga o rastreamento e comeca uma sessao nova (cabecalho no arquivo)."""
    global _ENABLED, _PATH, _T0
    try:
        _PATH = path or _default_path()
        directory = os.path.dirname(_PATH)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        _T0 = time.time()
        _ENABLED = True
        _write("=== SESSAO {} ===".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    except Exception:
        _ENABLED = False


def disable():
    global _ENABLED
    _ENABLED = False


def is_enabled():
    return _ENABLED


def log_path():
    return _PATH


def reset():
    """Zera o relogio relativo sem trocar de arquivo - usado no clique, para
    que todos os marcos de UMA execucao sejam lidos a partir do zero."""
    global _T0
    _T0 = time.time()


def _now():
    return (time.time() - _T0) if _T0 is not None else 0.0


def _write(line):
    try:
        with _LOCK:
            handle = open(_PATH, "a")
            try:
                handle.write(line + "\n")
                handle.flush()
            finally:
                handle.close()
    except Exception:
        pass


def mark(tag, **fields):
    """Um marco pontual: `[PERF] +12.345s tid=7 tag k=v k=v`."""
    if not _ENABLED:
        return
    try:
        extra = " ".join("{}={}".format(k, fields[k]) for k in sorted(fields))
        _write("[PERF] +{:9.3f}s tid={:<5} {} {}".format(
            _now(), threading.current_thread().ident, tag, extra).rstrip())
    except Exception:
        pass


class span(object):
    """Contexto que marca START/END de uma etapa e mede a duracao.

    Usado como `with span("refresh_geometry", walls=2): ...`. Quando
    desligado, o custo e' um `if` - nenhuma escrita, nenhuma formatacao.
    """

    __slots__ = ("_tag", "_fields", "_t0")

    def __init__(self, tag, **fields):
        self._tag = tag
        self._fields = fields
        self._t0 = None

    def __enter__(self):
        if _ENABLED:
            self._t0 = time.time()
            mark(self._tag + " START", **self._fields)
        return self

    def __exit__(self, exc_type, exc_value, traceback_obj):
        if _ENABLED and self._t0 is not None:
            elapsed = time.time() - self._t0
            fields = dict(self._fields)
            fields["dt"] = "{:.3f}s".format(elapsed)
            if exc_type is not None:
                fields["exc"] = exc_type.__name__
            mark(self._tag + " END", **fields)
        return False  # nunca engole excecao
