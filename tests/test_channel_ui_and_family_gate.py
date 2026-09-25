# -*- coding: utf-8 -*-
"""Tela de Configuracao (estrategia de reforco) e bloqueio por familia de
canaleta faltante ANTES de calcular/criar.

Auditoria independente 2026-09-14: CHANNEL NUNCA e' default - so' com escolha
explicita; a escolha desta execucao chega ao handler pelo chamador, nunca
relida do disco; falha ao salvar preferencia nao troca a escolha.

    python3 -m pytest tests/test_channel_ui_and_family_gate.py -q
"""
import inspect
import json
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


def _run(form):
    assert form._validate() is True
    form._on_run(None, None)
    return form.result


def test_default_is_none_and_old_installation_stays_legacy():
    """Instalacao antiga (preferencia sem a chave) -> NONE -> legado."""
    assert m.DEFAULT_OPENING_REINFORCEMENT_UI_VALUE == "NONE"
    form = _form({"layer": "PAREDES", "height_m": 2.8})
    assert form._reinforcement_combo.SelectedIndex == _index_of("NONE")
    result = _run(form)
    assert result["opening_reinforcement"] == "NONE"
    assert m._opening_reinforcement_strategy_from_ui_value(result["opening_reinforcement"]) is None
    for missing in (None, "", "LIXO"):
        assert m._opening_reinforcement_strategy_from_ui_value(missing) is None


def test_user_chose_none_is_none():
    form = _form({"opening_reinforcement": "CHANNEL"})
    form._reinforcement_combo.SelectedIndex = _index_of("NONE")
    result = _run(form)
    assert m._opening_reinforcement_strategy_from_ui_value(result["opening_reinforcement"]) is None


def test_user_chose_channel_is_channel():
    form = _form()
    form._reinforcement_combo.SelectedIndex = _index_of("CHANNEL")
    result = _run(form)
    assert m._opening_reinforcement_strategy_from_ui_value(result["opening_reinforcement"]) == "CHANNEL"


def test_unimplemented_lintel_is_hidden_and_injected_value_blocks_execution():
    form = _form()
    assert form._reinforcement_combo.Items.Count == 2
    form._reinforcement_combo.SelectedIndex = _index_of("LINTEL_COUNTERLINTEL")
    assert form._validate() is False
    assert form._run_button.Enabled is False
    assert "nao implementado" in form._status.Text
    form._on_run(None, None)
    assert form.result is None
    with pytest.raises(ValueError):
        m._opening_reinforcement_strategy_from_ui_value("LINTEL_COUNTERLINTEL")


@pytest.mark.parametrize("chosen,expected", [("NONE", None), ("CHANNEL", "CHANNEL")])
def test_failed_persistence_preserves_the_current_choice(tmp_path, monkeypatch, chosen, expected):
    """Disco com a escolha ANTERIOR oposta e gravacao falhando: a execucao usa
    a escolha feita agora."""
    stale = tmp_path / "prefs.json"
    stale.write_text(json.dumps({"opening_reinforcement": "CHANNEL" if chosen == "NONE" else "NONE"}))
    monkeypatch.setattr(m, "_setup_defaults_path", lambda: str(stale))

    class _FakeForm(object):
        def __init__(self, *_a):
            self.result = None

        def ShowDialog(self):
            self.result = {"layer": "PAREDES", "level": "Nivel 1", "height_m": 2.8,
                           "opening_reinforcement": chosen}

    def _broken_open(*_a, **_k):
        raise IOError("disco somente leitura")

    monkeypatch.setattr(m, "_SetupForm", _FakeForm)
    import builtins
    real_open = builtins.open
    monkeypatch.setattr(builtins, "open",
                        lambda path, mode="r", *a, **k: _broken_open() if "w" in mode and str(path) == str(stale)
                        else real_open(path, mode, *a, **k))
    setup = m.ask_setup({"PAREDES": []}, ["Nivel 1"])
    assert m._opening_reinforcement_strategy_from_ui_value(setup.get("opening_reinforcement")) == expected
    assert json.loads(stale.read_text())["opening_reinforcement"] != chosen  # gravacao falhou mesmo


def test_execution_receives_the_form_choice_never_the_disk():
    src = inspect.getsource(m._show_post_creation_window)
    assert "_recall_setup_defaults" not in src
    assert "handler.opening_reinforcement_strategy = opening_reinforcement_strategy" in src
    main_src = inspect.getsource(m.main)
    assert 'opening_reinforcement_strategy=_opening_reinforcement_strategy_from_ui_value(' in main_src
    assert 'setup.get("opening_reinforcement")' in main_src
    assert "opening_reinforcement_strategy=None" in inspect.signature(m._show_post_creation_window).__str__()


def test_missing_channel_families_with_none_keeps_legacy_working():
    """SECAO 80 (decisao do usuario 2026-09-25): 'Sem reforco adicional' tem
    verga/contraverga em canaleta, entao as familias de canaleta sao CONFERIDAS
    (uma vez), mas a ausencia NAO bloqueia: a modulacao segue com blocos comuns
    e a verga/contraverga sai *_UNRESOLVED (CHANNEL_FAMILY_MISSING)."""
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = None
    chamadas = []
    missing = [{"logical_code": "CHANNEL_U_CUT", "family_name": "x", "type_name": "x", "reason": "MISSING"}]
    handler._load_channel_family_catalog = lambda doc: chamadas.append(1) or ({}, missing)
    handler._ensure_opening_reinforcement_catalog(SimpleNamespace())
    assert chamadas == [1]
    assert handler._opening_structural_channel_available() is False
    assert handler._creation_catalog() is handler.catalog
    # sem a secao 80 o None volta a nao carregar nada
    antes = m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED
    m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = False
    try:
        outro = m._PostCreationEventHandler()
        outro.opening_reinforcement_strategy = None
        outro._load_channel_family_catalog = lambda doc: (_ for _ in ()).throw(AssertionError("nao deveria carregar"))
        outro._ensure_opening_reinforcement_catalog(SimpleNamespace())
        assert outro._creation_catalog() is outro.catalog
    finally:
        m.OPENING_STRUCTURAL_REINFORCEMENT_ENABLED = antes


def test_missing_channel_families_with_channel_raises_explicit_error():
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
