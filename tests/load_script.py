# -*- coding: utf-8 -*-
"""Importa core/wall_modeling.py como modulo, com a API do Revit substituida
pelos dubles de revit_stubs - ver o cabecalho de la'.

Ate' 2026-08-24 este modulo carregava Script.py, que continha toda a logica
do motor. Desde entao Script.py virou so' um loader (baixa wall_modeling.py
do GitHub via System.Net/System.Security, que revit_stubs.py nao simula) e
a logica real passou para core/wall_modeling.py - e' isso que os testes
precisam exercitar."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT_PATH = os.path.join(ROOT, "core", "wall_modeling.py")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import revit_stubs  # noqa: E402

revit_stubs.install()


def load():
    """Devolve o modulo do Script.py ja importado (uma unica vez)."""
    if "script_under_test" in sys.modules:
        return sys.modules["script_under_test"]
    import types
    module = types.ModuleType("script_under_test")
    module.__file__ = SCRIPT_PATH
    with open(SCRIPT_PATH, "rb") as handle:
        source = handle.read().decode("utf-8")
    sys.modules["script_under_test"] = module
    exec(compile(source, SCRIPT_PATH, "exec"), module.__dict__)
    return module
