# -*- coding: utf-8 -*-
"""Tela de Configuracao (estrategia de reforco) e bloqueio por familia de
canaleta faltante ANTES de calcular/criar.

    python3 -m pytest tests/test_channel_ui_and_family_gate.py -q
"""
import os
import sys
from types import SimpleNamespace

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
seg = sb.seg


def _form(defaults=None):
    form = m._SetupForm({"PAREDES": [seg(0, 0, 400, 0), seg(0, 14, 400, 14)]}, ["Nivel 1"], defaults or {})
    form._thickness_list.SetItemChecked(0, True)
    return form


def _index_of(key):
    return [k for k, _l, _i in m.OPENING_REINFORCEMENT_UI_OPTIONS].index(key)


def test_setup_form_offers_channel_selected_by_default():
    form = _form()
    labels = [str(form._reinforcement_combo.Items[i]) for i in range(len(m.OPENING_REINFORCEMENT_UI_OPTIONS))]
    assert any(label.startswith("CHANNEL") for label in labels)
    assert form._reinforcement_combo.SelectedIndex == _index_of("CHANNEL")
    assert form._validate() is True
    form._on_run(None, None)
    assert form.result["opening_reinforcement"] == "CHANNEL"


def test_unimplemented_lintel_is_visible_but_blocks_execution():
    form = _form()
    form._reinforcement_combo.SelectedIndex = _index_of("LINTEL_COUNTERLINTEL")
    assert form._validate() is False
    assert form._run_button.Enabled is False
    assert "nao implementado" in form._status.Text
    form._on_run(None, None)
    assert form.result is None


def test_remembered_choice_is_restored_and_mapped_to_engine_strategy():
    form = _form({"opening_reinforcement": "NONE"})
    assert form._reinforcement_combo.SelectedIndex == _index_of("NONE")
    assert m._opening_reinforcement_strategy_from_ui_value("NONE") is None
    assert m._opening_reinforcement_strategy_from_ui_value("CHANNEL") == "CHANNEL"
    with pytest.raises(ValueError):
        m._opening_reinforcement_strategy_from_ui_value("LINTEL_COUNTERLINTEL")


def test_missing_channel_family_blocks_before_solve_and_create():
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = "CHANNEL"
    missing = [{"logical_code": "CHANNEL_U_CUT", "family_name": "BLOCO CANALETA CORTADO - 14x19xVAR",
                "type_name": "BLOCO CANALETA CORTADO - 14x19xVAR", "reason": "MISSING_FAMILY_MAPPING: x"}]
    handler._load_channel_family_catalog = lambda doc: ({"CHANNEL_U_39": {}}, missing)
    with pytest.raises(ValueError) as info:
        handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    text = str(info.value)
    assert "CHANNEL BLOQUEADO" in text and "CHANNEL_U_CUT" in text and "BLOCO CANALETA CORTADO" in text


def test_complete_channel_catalog_passes_and_is_loaded_once():
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = "CHANNEL"
    calls = []

    def _load(doc):
        calls.append(doc)
        return {"CHANNEL_U_39": {"length_cm": 39.0}}, []

    handler._load_channel_family_catalog = _load
    handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    assert len(calls) == 1
    assert "CHANNEL_U_39" in handler._creation_catalog()


def test_legacy_strategy_never_loads_channel_families():
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = None
    handler._load_channel_family_catalog = lambda doc: (_ for _ in ()).throw(AssertionError("nao deveria carregar"))
    handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    assert handler._creation_catalog() is handler.catalog
