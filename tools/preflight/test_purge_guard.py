# -*- coding: utf-8 -*-
"""Testes da proteção operacional da purga (`tools/preflight/purge_guard.py`)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

import pytest  # noqa: E402

from tools.preflight.purge_guard import (  # noqa: E402
    PurgeNotCleanError, assert_purge_clean, check_purge)


def test_purga_limpa_passa():
    report = assert_purge_clean(removed=12, remaining=0, expected_removed=12,
                                total_before=500, total_after=488,
                                human_modified=False)
    assert report["violations"] == []
    assert report["removed"] == 12


def test_remaining_diferente_de_zero_aborta():
    """O caso central do pedido: sobrou instância carimbada -> ABORTAR."""
    with pytest.raises(PurgeNotCleanError) as exc:
        assert_purge_clean(removed=10, remaining=2)
    assert "remaining=2" in str(exc.value)

    ok, report = check_purge(removed=10, remaining=2)
    assert ok is False
    assert len(report["violations"]) == 1


def test_removed_diferente_da_contagem_inicial_aborta():
    with pytest.raises(PurgeNotCleanError) as exc:
        assert_purge_clean(removed=9, remaining=0, expected_removed=12)
    assert "de menos ou de mais" in str(exc.value)


def test_total_caiu_mais_do_que_o_removido_aborta():
    """A purga alcançou elemento que não era da bancada."""
    with pytest.raises(PurgeNotCleanError) as exc:
        assert_purge_clean(removed=12, remaining=0, total_before=500,
                           total_after=480)
    assert "NAO era da bancada" in str(exc.value)


def test_humano_tocado_aborta():
    with pytest.raises(PurgeNotCleanError) as exc:
        assert_purge_clean(removed=12, remaining=0, human_modified=True)
    assert "HUMANO" in str(exc.value)


def test_varias_violacoes_sao_todas_relatadas():
    ok, report = check_purge(removed=9, remaining=3, expected_removed=12,
                             total_before=500, total_after=470,
                             human_modified=True)
    assert ok is False
    assert len(report["violations"]) == 4


def test_zero_instancias_de_bancada_e_purga_valida():
    """Modelo já limpo: nada a remover, nada sobrando."""
    report = assert_purge_clean(removed=0, remaining=0, expected_removed=0,
                                total_before=500, total_after=500,
                                human_modified=False)
    assert report["violations"] == []
