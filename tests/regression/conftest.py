# -*- coding: utf-8 -*-
"""Coloca `nuvem/` no `sys.path` para os testes de regressao importarem
`benchmark.*`.

Mesma busca subindo a arvore de `tests/load_script.py` e
`benchmark/solver_bridge.py` - o repositorio existe em dois layouts (pasta
de extensao do pyRevit e repo independente) e fixar um deles ja' quebrou
duas vezes."""

import os
import sys


def _find_nuvem():
    directory = os.path.dirname(os.path.abspath(__file__))
    tried = []
    for _level in range(6):
        candidate = os.path.join(directory, "nuvem", "benchmark", "__init__.py")
        tried.append(candidate)
        if os.path.isfile(candidate):
            return os.path.join(directory, "nuvem")
        nested = os.path.join(directory, "MinhaAba.tab", "MeuPainel.panel",
                              "MeuBotao.pushbutton", "nuvem", "benchmark", "__init__.py")
        tried.append(nested)
        if os.path.isfile(nested):
            return os.path.dirname(os.path.dirname(nested))
        parent = os.path.dirname(directory)
        if parent == directory:
            break
        directory = parent
    raise RuntimeError("nao achei nuvem/benchmark. Procurei em: " + " | ".join(tried))


NUVEM_DIR = _find_nuvem()
if NUVEM_DIR not in sys.path:
    sys.path.insert(0, NUVEM_DIR)
