# -*- coding: utf-8 -*-
"""Regra 12.1: o espelhamento do compensador (orientacao, regra #3) tem de
acontecer NO LUGAR - uma instancia por candidato, nunca uma copia espelhada
ao lado do original.

Bug real medido em BUTANTA R08_LT (2026-09-10): ElementTransformUtils.
MirrorElement cria uma COPIA e deixa o original; 54 compensadores/pastilhas
ficaram duplicados, a copia orfa sobrevivia a' troca de lote e quebrava a
idempotencia. Fix: MirrorElements(doc, [id], plane, mirrorCopies=False)."""
from types import SimpleNamespace

import pytest

from test_beta_atomic_creation import Document, Transaction, setup  # noqa: F401  (fixture)
from test_controlled_beta_preflight import m, fixture, piece, CATALOG


def _mirrored_setup(handler):
    result, walls, openings = fixture([dict(piece(40), logical_code="C09", length_cm=9, mirrored=True),
                                       piece(100)], opening=None)
    handler.solve_result, handler.walls_to_create = result, walls
    handler.openings_per_wall = openings
    handler.catalog = {key: dict(value, symbol=SimpleNamespace(IsActive=True)) for key, value in CATALOG.items()}
    result["beta_input_signature"] = handler._beta_input_signature()
    return result


def test_candidato_espelhado_gera_uma_unica_instancia_no_lugar(setup):
    handler, previous, events = setup
    _mirrored_setup(handler)
    doc = Document()
    m.ElementTransformUtils.calls = []
    handler._execute_create(doc)
    # exatamente as duas pecas - nenhuma copia espelhada a mais
    assert set(doc.elements) == {100, 101}, doc.elements
    assert handler.create_result["created_count"] == 2
    mirrors = [c for c in m.ElementTransformUtils.calls if c[0] == "mirror"]
    copies = [c for c in m.ElementTransformUtils.calls if c[0] == "mirror_copy"]
    assert len(mirrors) == 1 and mirrors[0][3] is False, m.ElementTransformUtils.calls
    assert copies == [], "MirrorElement (copia) nunca mais pode ser usado: %r" % (copies,)
    assert mirrors[0][1] == 100, "espelha a propria instancia criada"
    assert handler.create_result["perf"]["mirror_calls"] == 1


def test_recriacao_substitui_o_lote_sem_deixar_orfas(setup):
    """Idempotencia (13.4) com peca espelhada: criar duas vezes deixa o mesmo
    numero de instancias, e todas rastreadas em created_instances."""
    handler, previous, events = setup
    _mirrored_setup(handler)
    doc = Document()
    handler._execute_create(doc)
    first = set(doc.elements)
    handler._execute_create(doc)
    second = set(doc.elements)
    assert len(first) == len(second) == 2
    tracked = {item["id"] for item in handler.create_result["created_instances"]}
    assert tracked == second, (tracked, second)
