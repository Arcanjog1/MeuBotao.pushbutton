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

# CPU do PROCESSO (todas as threads somadas). E' o discriminador decisivo
# entre "esta thread esta calculando devagar" e "esta thread nao esta
# rodando": se o relogio de parede anda 97s e o CPU do processo anda ~0s,
# ninguem no processo computou nada - a thread ficou PARADA (starvation/
# bloqueio), nao lenta. Ausente no IronPython 2.7 (o engine do servidor
# MCP); presente no CPython 3.x, que e' onde o botao roda.
try:
    _process_cpu = time.process_time
except AttributeError:  # pragma: no cover - IronPython 2.7
    try:
        _process_cpu = time.clock
    except AttributeError:
        _process_cpu = None

__all__ = [
    "enable", "disable", "is_enabled", "log_path", "mark", "span", "reset",
    "start_stall_sampler", "stop_stall_sampler",
]

_ENABLED = False
_PATH = None
_LOCK = threading.Lock()
_T0 = None
_CPU0 = 0.0


def _default_path():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or "."
    return os.path.join(base, "MeuBotaoPushbutton", "perf_diag.log")


def enable(path=None):
    """Liga o rastreamento e comeca uma sessao nova (cabecalho no arquivo)."""
    global _ENABLED, _PATH, _T0, _CPU0
    try:
        _PATH = path or _default_path()
        directory = os.path.dirname(_PATH)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        _T0 = time.time()
        _CPU0 = _process_cpu() if _process_cpu is not None else 0.0
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
    global _T0, _CPU0
    _T0 = time.time()
    _CPU0 = _process_cpu() if _process_cpu is not None else 0.0


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
    """Um marco pontual:
    `[PERF] +12.345s cpu=3.210s thr=9 tid=7 tag k=v k=v`.

    `cpu` e' o tempo de CPU do PROCESSO inteiro desde o inicio da sessao -
    comparar a variacao dele com a variacao de `+Ns` entre dois marcos
    responde, sozinho, se houve calculo ou espera. `thr` e' o numero de
    threads Python vivas."""
    if not _ENABLED:
        return
    try:
        extra = " ".join("{}={}".format(k, fields[k]) for k in sorted(fields))
        cpu = ""
        if _process_cpu is not None:
            try:
                cpu = "cpu={:8.3f}s ".format(_process_cpu() - _CPU0)
            except Exception:
                cpu = ""
        _write("[PERF] +{:9.3f}s {}thr={:<3} tid={:<5} {} {}".format(
            _now(), cpu, threading.active_count(),
            threading.current_thread().ident, tag, extra).rstrip())
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


# ---------------------------------------------------------------------
# AMOSTRADOR DE CONGELAMENTO
#
# Instrumento decisivo para o congelamento medido no primeiro beta
# (2026-09-09): o interpretador para por 19,6s / 100,2s entre duas
# instrucoes que nao computam nada, e NENHUMA linha [PERF] de NENHUMA
# thread aparece durante o periodo - nem o watchdog do _ProgressConsole,
# que e' um System.Threading.Timer.
#
# Este amostrador e' uma thread PYTHON pura (nao um timer do .NET) que so'
# acorda, anota a hora e volta a dormir. Ele responde a pergunta que
# nenhuma sonda anterior conseguiu responder:
#
#   - se o amostrador TAMBEM congela, ninguem em Python rodou -> a GIL
#     estava retida por um chamador .NET (hipotese principal: a thread
#     principal do Revit, ainda dentro de um frame do pythonnet, enquanto
#     o Revit faz trabalho proprio);
#   - se o amostrador continua tiquetaqueando enquanto a thread do solver
#     nao anda, o problema e' especifico daquela thread (starvation de
#     escalonamento), nao da GIL.
#
# Ao detectar um salto, despeja o topo da pilha de TODAS as threads
# (`sys._current_frames()`), que mostra onde cada uma estava.
# ---------------------------------------------------------------------

_SAMPLER = None
_SAMPLER_STOP = None


def _formatar_pilhas(limite_por_thread=6):
    """Topo da pilha de cada thread Python viva, uma linha por frame."""
    try:
        import sys as _sys
        import traceback as _tb
        nomes = {}
        for t in threading.enumerate():
            nomes[t.ident] = t.name
        linhas = []
        for ident, frame in _sys._current_frames().items():
            linhas.append("    --- tid={} ({}) ---".format(ident, nomes.get(ident, "?")))
            pilha = _tb.extract_stack(frame)[-limite_por_thread:]
            for entrada in pilha:
                linhas.append("      {}:{} {}".format(
                    os.path.basename(entrada.filename), entrada.lineno, entrada.name))
        return "\n".join(linhas)
    except Exception as exc:
        return "    (falha ao ler as pilhas: {})".format(exc)


def start_stall_sampler(interval_s=0.25, threshold_s=2.0):
    """Liga o amostrador. Seguro chamar mais de uma vez (para/recria)."""
    global _SAMPLER, _SAMPLER_STOP
    stop_stall_sampler()
    if not _ENABLED:
        return
    parar = threading.Event()

    def _laco():
        anterior = time.time()
        while True:
            parado = parar.wait(interval_s)
            # MEDE ANTES de olhar a flag de parada. Endurecimento, nao
            # correcao de defeito observado: a versao anterior checava a flag
            # primeiro e, se `stop_stall_sampler()` fosse chamado no instante
            # em que o congelamento terminasse, descartaria justamente a
            # ultima medicao - a que interessa. Nao ha' registro desse caso
            # ter acontecido; a ordem trocada e' de graca e fecha a corrida.
            agora = time.time()
            salto = agora - anterior - interval_s
            if salto >= threshold_s:
                # O PROPRIO amostrador ficou parado: prova de congelamento
                # global do interpretador, nao de uma thread especifica.
                mark("CONGELAMENTO detectado pelo amostrador",
                     parado="{:.3f}s".format(salto))
                _write(_formatar_pilhas())
            anterior = agora
            if parado or parar.is_set():
                break

    thread = threading.Thread(target=_laco, name="perf-stall-sampler")
    thread.daemon = True
    try:
        thread.start()
    except Exception:
        return
    _SAMPLER, _SAMPLER_STOP = thread, parar
    mark("amostrador de congelamento LIGADO",
         intervalo="{:.2f}s".format(interval_s), limiar="{:.1f}s".format(threshold_s))


def stop_stall_sampler():
    global _SAMPLER, _SAMPLER_STOP
    if _SAMPLER_STOP is not None:
        try:
            _SAMPLER_STOP.set()
        except Exception:
            pass
    _SAMPLER, _SAMPLER_STOP = None, None
