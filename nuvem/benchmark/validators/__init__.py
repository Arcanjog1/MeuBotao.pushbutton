# -*- coding: utf-8 -*-
"""Validadores independentes, um por classe de problema (item 8).

Importar este pacote REGISTRA todos eles (cada modulo chama
`base.register` no fim). `run_all` e' o unico ponto que o runner usa -
nenhum modulo de fora deve chamar um validador direto, senao a lista de
categorias do score sai incompleta sem ninguem notar.
"""

from . import base  # noqa: F401  (re-exportado de proposito)
from . import validate_prism  # noqa: F401
from . import validate_compensators  # noqa: F401
from . import validate_junctions  # noqa: F401
from . import validate_openings  # noqa: F401
from . import validate_wall_coverage  # noqa: F401
from . import validate_block_positions  # noqa: F401


def run_all(project, context=None):
    """Roda TODOS os validadores registrados sobre `project`.

    Devolve `(findings, errors)`. `errors` guarda validador que EXPLODIU -
    nunca engolido: um validador quebrado que devolvesse lista vazia
    apareceria como "categoria sem erro nenhum", que e' exatamente a
    mentira que este pacote existe para evitar."""
    findings = []
    errors = []
    for name, function in base.registered():
        try:
            findings.extend(function(project, context or {}))
        except Exception as exc:  # pragma: no cover - falha de programacao
            import traceback
            errors.append({
                "validator": name,
                "error": "{0}: {1}".format(type(exc).__name__, exc),
                "traceback": traceback.format_exc(),
            })
    return findings, errors


def available():
    return [name for name, _fn in base.registered()]
