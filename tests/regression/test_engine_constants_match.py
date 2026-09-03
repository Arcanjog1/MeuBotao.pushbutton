# -*- coding: utf-8 -*-
"""Guarda contra DIVERGENCIA SILENCIOSA entre o benchmark e o motor.

`benchmark/analysis.py` repete varias constantes de `core/wall_modeling.py`
e `core/engine/*` em vez de importa-las - precisa disso para rodar sobre
JSON puro, sem os dubles do Revit (ver o cabecalho de la').

Numero repetido e' numero que um dia diverge. Este arquivo importa o motor
DE VERDADE e compara valor a valor: se alguem afinar o limite de junta
corrida no solver e esquecer o benchmark, a suite quebra aqui, com o nome
da constante - em vez de o benchmark passar a medir uma regra que nao
existe mais.

Se este teste falhar, a correcao NAO e' copiar o numero novo sem pensar:
e' entender qual dos dois lados mudou e por que."""

import pytest

from benchmark import analysis

try:
    from benchmark import solver_bridge
    ENGINE = solver_bridge.engine()
except Exception as exc:  # pragma: no cover - ambiente sem os dubles
    ENGINE = None
    LOAD_ERROR = exc


pytestmark = pytest.mark.skipif(
    ENGINE is None,
    reason="motor nao carregou (tests/revit_stubs.py indisponivel)",
)

# (nome no benchmark, nome no motor). Onde o nome e' o mesmo, aparece uma
# vez so'.
MIRRORED = [
    "BOND_JOINT_CLUSTER_TOLERANCE_CM",
    "BOND_CONTINUOUS_JOINT_MIN_COURSES",
    "BOND_CONTINUOUS_JOINT_RATIO",
    "BOND_ALTERNATING_JOINT_MIN_COURSES",
    "BOND_ALTERNATING_JOINT_RATIO",
    "BOND_STRIP_CLUSTER_TOLERANCE_CM",
    "BOND_STRIP_MIN_COURSES",
    "BOND_STRIP_RATIO",
    "BOND_STRIP_EDGE_EXEMPT_CM",
    "BOND_STRIP_OPENING_INFLUENCE_CM",
    "BOND_STRIP_NODE_EXEMPT_CM",
    "BOND_MAX_ADJACENT_GAP_CM",
    "HALF_BLOCK_CODE",
    "MAX_COMPENSATORS_PER_TRECHO",
    "MAX_SPECIAL_BOND_PER_TRECHO",
    "OPENING_ALIGNED_EXEMPT_CODES",
    "MIN_JOINT_STAGGER_TARGET_CM",
    "BLOCK_JOINT_CM",
    "BLOCK_OPENING_JOINT_CM",
    "PIER_MODULE_CM",
    "FIRST_COURSE_Z_OFFSET_CM",
]


@pytest.mark.parametrize("name", MIRRORED)
def test_constante_espelhada_bate_com_o_motor(name):
    assert hasattr(ENGINE, name), (
        "'{0}' sumiu do motor - o benchmark ainda depende dela".format(name))
    mine = getattr(analysis, name)
    theirs = getattr(ENGINE, name)
    if isinstance(mine, tuple) or isinstance(theirs, tuple):
        assert tuple(mine) == tuple(theirs), (
            "{0}: benchmark={1} motor={2}".format(name, mine, theirs))
    elif isinstance(mine, str) or isinstance(theirs, str):
        assert mine == theirs, (
            "{0}: benchmark={1} motor={2}".format(name, mine, theirs))
    else:
        assert float(mine) == pytest.approx(float(theirs)), (
            "{0}: benchmark={1} motor={2}".format(name, mine, theirs))


def test_comprimentos_de_bloco_batem_com_o_motor():
    assert tuple(float(v) for v in analysis.BLOCK_LENGTHS_CM) == \
        tuple(float(v) for v in ENGINE.BLOCK_LENGTHS_CM)


def test_codigos_conhecidos_pelo_solver_existem_no_motor():
    """Se o catalogo fixo do motor ganhar (ou perder) um codigo, o filtro
    de catalogo do benchmark tem que acompanhar - senao ele entregaria ao
    solver uma peca que o solver nao sabe usar, ou esconderia dele uma que
    sabe."""
    for code in solver_bridge.SOLVER_KNOWN_CODES:
        assert code in ENGINE.BLOCK_FAMILY_CATALOG_DEFINITIONS, (
            "codigo '{0}' nao esta' mais no catalogo fixo do motor".format(code))
    assert set(solver_bridge.SOLVER_KNOWN_CODES) == \
        set(ENGINE.BLOCK_FAMILY_CATALOG_DEFINITIONS)
