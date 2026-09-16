# -*- coding: utf-8 -*-
"""Presentation contracts, with backend callbacks mocked only at the boundary."""
import inspect
import pytest
import load_script

m = load_script.load()
from core.ui_state import ModulationUiState, creation_gate, planned_counts, friendly_error, wall_label


def result(**extra):
    data = dict(candidates=[{"logical_code": "B39", "course": "A"}],
                course_candidates={0: [{"logical_code": "B39"}], 1: [{"logical_code": "B19"}]},
                collisions=[], door_void_violations=[], wall_bond_audits={}, num_courses=2,
                intersection_failures=[], jamb_exceptions=[], non_modular=[], per_wall=[], validations=[])
    data.update(extra)
    return data


def form(strategy=None):
    handler = m._PostCreationEventHandler()
    handler.opening_reinforcement_strategy = strategy
    window = m._PostCreationForm({"kpis": [], "issues": [], "log": ""}, None, handler, [])
    return window, handler


def test_plan_counts_physical_courses_not_representative_pair():
    r = result(course_candidates={0: [{"logical_code": "B39"}] * 10,
                                  1: [{"logical_code": "CHANNEL_U_39"}] * 4,
                                  2: [{"logical_code": "B19"}] * 3})
    assert planned_counts(r) == {"B39": 10, "CHANNEL_U_39": 4, "B19": 3}
    assert planned_counts({"candidates": r["candidates"]}) is None


@pytest.mark.parametrize("reason", [{"error": "altura inválida"},
                                   {"beta_preflight": {"ok": False}}, {"candidates": []}])
def test_backend_critical_gate_disables_creation(reason):
    assert creation_gate(result(**reason))[0] is False


def test_diagnostics_do_not_become_new_physical_gate():
    assert creation_gate(result(collisions=[(0, 1)], door_void_violations=[{}],
                                wall_bond_audits={0: {"ok": False}}))[0]


@pytest.mark.parametrize("strategy", [None, "CHANNEL"])
def test_solve_presents_preview_never_auto_creates(strategy):
    window, handler = form(strategy)
    handler.solve_result = result()
    calls = []
    window._on_create_click = lambda *args: calls.append(args)
    window._on_solve_done("solve", None, auto_create=True)
    assert calls == []
    assert window._ui_state.step == 4
    assert "2 blocos planejados" in window._ui_plan.Text
    assert window._create_button.Enabled is True


def test_preflight_error_is_visible_and_click_cannot_dispatch():
    window, handler = form()
    handler.solve_result = result(beta_preflight={"ok": False, "opening_violations": [],
                                                  "collisions": [], "errors": ["Parede modificada"]})
    window._on_solve_done("solve", None)
    assert window._create_button.Enabled is False
    assert "Crítico: Parede modificada" in window._ui_plan.Text
    window._on_create_click(None, None)
    assert handler.action is None


def test_declining_replace_does_not_dispatch_or_change_previous_lot(monkeypatch):
    window, handler = form()
    handler.solve_result = result()
    previous = {"created_count": 17, "created_instances": [{"id": 12}]}
    handler.create_result = previous
    prompts = []
    monkeypatch.setattr(m.forms, "alert", lambda text, **kw: prompts.append(text) or False)
    window._on_create_click(None, None)
    assert handler.action is None
    assert handler.create_result is previous
    assert "17" in prompts[0] and "substituído" in prompts[0]


def test_failed_channel_load_is_actionable_and_no_create():
    window, handler = form("CHANNEL")
    handler.channel_catalog_missing = [{"logical_code": "CHANNEL_U_19", "family_name": "Canaleta 19", "type_name": "19"}]
    window._on_solve_done("error", "CHANNEL BLOQUEADO: familia ausente")
    assert not window._create_button.Enabled
    assert "Canaleta 19" in window._ui_families.Text
    assert "carregue" in window._ui_plan.Text.lower()
    assert window._ui_close.Enabled


def test_catalog_gate_and_default_none():
    assert ModulationUiState(strategy="unknown").strategy == "NONE"
    assert creation_gate(result(), catalog_missing=[{}])[0] is False
    assert creation_gate(result(), channel_missing=[{}])[0] is False


@pytest.mark.parametrize("creation,expected", [
    ({"created_count": 20, "failures": []}, "success"),
    ({"created_count": 0, "failures": []}, "error"),
    ({"created_count": 15, "failures": ["faltou peça"]}, "warning"),
    ({"created_count": 20, "skipped_wall_count": 1}, "warning"),
    ({"created_count": 20, "colliding_instance_count": 1}, "warning"),
])
def test_completion_does_not_hide_failures(creation, expected):
    state = ModulationUiState()
    state.completed(creation)
    assert state.step == 6 and state.status == expected


def test_cancelled_wall_analysis_does_not_claim_success_or_advance():
    handler = m._PostCreationEventHandler()
    calls = []
    window = m._WallReviewForm({"kpis": [], "log": ""}, None, handler, calls.append, None)
    window._cancel_requested = True
    window._on_analyze_done("analyze", None)
    assert calls == []
    assert window._start_button.Enabled
    assert "interrompida" in window._console._status_label.Text


def test_unknown_progress_is_indeterminate_and_logs_collapsed():
    console = m._ProgressConsole()
    console.set_progress(0, 0, "Atualizando geometria")
    assert str(console._progress_bar.Style) == str(m.ProgressBarStyle.Marquee)
    assert console._details._expanded is False
    console._details._toggle.PerformClick()
    assert console._details._expanded is True
    console.set_progress(86, 120, "Verificando aberturas")
    assert "86 de 120" in console._detail_label.Text and "72%" in console._detail_label.Text
    assert "Tempo decorrido" in console._elapsed_label.Text


def test_wall_identity_uses_existing_id_not_unstable_index():
    assert wall_label({"wall_idx": 0, "wall_ids": [7719511]}) == "Parede 7719511"
    assert "temporário" in wall_label({"wall_idx": 0})


def test_existing_selection_cancel_skips_native_picker(monkeypatch):
    monkeypatch.setattr(m._ui, "selection_prompt", lambda count: None)
    assert m._select_existing_walls_for_modulation() == (None, None, None, None, None, 0)


def test_existing_strategy_flows_explicitly_and_invalidates_incompatible_cache():
    source = inspect.getsource(m.run_modulation_on_existing_walls)
    assert "opening_reinforcement_strategy=execution_strategy" in source
    assert "cached_strategy != execution_strategy" in source
    assert "_recall_setup_defaults" not in source


def test_stale_geometry_error_has_next_action():
    text = friendly_error("BETA BLOQUEADO: eixo deslocado/rotacionado")
    assert "selecione as paredes novamente" in text and "reanalise" in text


def test_busy_blocks_competing_actions_and_new_plan_requires_new_review():
    window, handler = form()
    window._review_check.Checked = True
    window._delete_button.Enabled = True
    window._ux.busy(window, 4)
    assert not window._delete_button.Enabled
    assert not window._errors_grid.Enabled
    assert not window._debug_color_check.Enabled
    assert not window._review_check.Enabled
    handler.solve_result = result()
    window._on_solve_done("solve", None)
    assert window._errors_grid.Enabled
    assert window._review_check.Enabled
    assert not window._review_check.Checked
    assert not window._delete_button.Enabled
