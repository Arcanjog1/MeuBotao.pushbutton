# -*- coding: utf-8 -*-
"""Amostrador de congelamento de `core/engine/perf_trace.py`.

Existe porque acertar este amostrador exigiu tres tentativas, e as duas
primeiras falharam por um motivo que vale registrar: um laco Python
apertado e um `int()` gigante NAO retem a GIL no CPython 3.14 - o
amostrador continuava tiquetaqueando e nao detectava nada. So' uma
retencao NATIVA (`ctypes.PyDLL`, que ao contrario de `WinDLL` nao libera a
GIL) reproduz o fenomeno. Sem este teste, o amostrador poderia ir para o
Revit parecendo funcional e nunca disparar.

O amostrador e' o instrumento que decide a causa do congelamento medido no
primeiro beta no Revit (19,6s e 100,2s entre duas instrucoes que nao
computam nada):

- se o amostrador TAMBEM congela, ninguem em Python rodou -> a GIL estava
  retida por um chamador NATIVO;
- se ele continua tiquetaqueando enquanto a thread do solver nao anda, o
  problema e' de escalonamento daquela thread.

Por isso os dois lados sao testados: um laco Python apertado NAO pode
disparar o amostrador (o CPython troca de thread a cada ~5ms), e uma
retencao nativa de GIL TEM de disparar.
"""

import ctypes
import io
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NUVEM = os.path.join(ROOT, "nuvem")
if NUVEM not in sys.path:
    sys.path.insert(0, NUVEM)

from core.engine import perf_trace  # noqa: E402


def _ler(caminho):
    with io.open(caminho, encoding="utf-8") as handle:
        return handle.read()


def _preparar(tmp_path, limiar):
    alvo = str(tmp_path / "perf.log")
    perf_trace.enable(alvo)
    perf_trace.reset()
    perf_trace.start_stall_sampler(interval_s=0.05, threshold_s=limiar)
    return alvo


def test_laco_python_apertado_nao_dispara_o_amostrador(tmp_path):
    """CONTROLE NEGATIVO: uma thread Python queimando CPU nao retem a GIL -
    o CPython a entrega a cada ~5ms. Se isto disparasse, o amostrador
    acusaria congelamento em qualquer solver pesado e nao serviria para
    nada."""
    alvo = _preparar(tmp_path, limiar=0.5)
    try:
        def queimar():
            fim = time.time() + 1.2
            while time.time() < fim:
                pass

        thread = threading.Thread(target=queimar, name="laco-apertado")
        thread.start()
        thread.join()
        time.sleep(0.2)
    finally:
        perf_trace.stop_stall_sampler()
    assert "CONGELAMENTO detectado" not in _ler(alvo)


def test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas(tmp_path):
    """CONTROLE POSITIVO: `ctypes.PyDLL` (ao contrario de `WinDLL`) NAO
    libera a GIL na chamada estrangeira - e' o analogo exato da hipotese
    sobre o congelamento no Revit. O amostrador tem de acordar, medir o
    salto e despejar as pilhas.

    NAO distingue as duas versoes do laco (a antiga tambem passa aqui - o
    endurecimento da ordem medir/checar fecha uma corrida de encerramento
    que este teste nao exercita). O que ele distingue, junto com o controle
    negativo acima, e' o que importa: trabalho Python pesado nao dispara,
    retencao nativa dispara."""
    alvo = _preparar(tmp_path, limiar=0.3)
    try:
        # PORTABILIDADE (2026-09-12): a retencao nativa e' a mesma ideia em
        # qualquer SO - uma chamada estrangeira via `PyDLL` (GIL retida) que
        # dorme 900ms. No Windows e' `kernel32.Sleep(ms)`; fora dele
        # `libc.usleep(us)`. Ate' entao o teste so' abria `kernel32` e
        # quebrava em Linux com OSError - falha de portabilidade do teste,
        # nunca do amostrador nem do solver.
        if sys.platform == "win32":
            nativo = ctypes.PyDLL("kernel32", use_last_error=True)

            def reter():
                nativo.Sleep(900)
        else:
            import ctypes.util
            nativo = ctypes.PyDLL(ctypes.util.find_library("c") or "libc.so.6")

            def reter():
                nativo.usleep(900 * 1000)

        thread = threading.Thread(target=reter, name="retentor-nativo")
        thread.start()
        thread.join()
        time.sleep(0.2)
    finally:
        perf_trace.stop_stall_sampler()

    texto = _ler(alvo)
    assert "CONGELAMENTO detectado pelo amostrador" in texto, texto
    # o salto medido tem de ser da ordem da retencao, nao do intervalo
    linha = [l for l in texto.splitlines() if "CONGELAMENTO detectado" in l][0]
    assert "parado=" in linha, linha
    parado = float(linha.split("parado=")[1].split("s")[0])
    assert parado >= 0.3, linha
    # e o despejo de pilhas tem de identificar a thread do proprio amostrador
    assert "perf-stall-sampler" in texto, texto
    assert "_laco" in texto, texto


def test_marco_traz_cpu_do_processo_e_contagem_de_threads(tmp_path):
    """O campo `cpu` e' o discriminador entre 'calculou devagar' e 'ficou
    parado'. Sem ele no marco, a leitura do log inteiro muda."""
    alvo = str(tmp_path / "perf.log")
    perf_trace.enable(alvo)
    perf_trace.reset()
    perf_trace.mark("teste", chave="valor")
    perf_trace.disable()
    linha = [l for l in _ler(alvo).splitlines() if "teste" in l][0]
    assert "cpu=" in linha, linha
    assert "thr=" in linha, linha
    assert "chave=valor" in linha, linha


def test_desligado_nao_escreve_nada(tmp_path):
    """Contrato central: com o rastreamento desligado, nenhuma sonda pode
    tocar o disco - e' o que permite deixar as chamadas no codigo de
    producao."""
    alvo = str(tmp_path / "perf.log")
    perf_trace.enable(alvo)
    perf_trace.disable()
    antes = os.path.getsize(alvo)
    for _ in range(50):
        perf_trace.mark("nao deveria aparecer")
    with perf_trace.span("nem esta"):
        pass
    assert os.path.getsize(alvo) == antes
    assert "nao deveria aparecer" not in _ler(alvo)
