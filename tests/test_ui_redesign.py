# -*- coding: utf-8 -*-
"""Presentation contracts, with backend callbacks mocked only at the boundary."""
import inspect
import pytest
import load_script

m = load_script.load()
from core.ui_state import ModulationUiState, creation_gate, planned_counts, friendly_error, wall_label


def test_family_list_distinguishes_verified_missing_and_pending():
    window, handler = form("CHANNEL")
    handler.catalog = {"B39": {}}
    handler.channel_catalog_missing = [{"logical_code": "CHANNEL_U_19", "family_name": "Canaleta 19", "type_name": "14"}]
    window._ux.update_families(window)
    rows = list(window._ui_family_grid.Items)
    assert rows[0].Text == "✓ Pronta"
    assert rows[1].Text == "✕ Ausente"
    assert "ausente" in window._plan_preview._families.Text
    handler.catalog = {}
    handler.channel_catalog_missing = []
    window._ux.update_families(window)
    assert "ainda não verificadas" in window._plan_preview._families.Text
    handler.catalog = {"B39": {}}
    window._ux.update_families(window)
    assert "ainda não verificadas" in window._plan_preview._families.Text
    assert list(window._ui_family_grid.Items)[-1].Text == "○ Pendente"


def test_reanalysis_hides_stale_quantities_until_new_result():
    window, handler = form()
    handler.solve_result = result()
    window._ux.solved(window)
    window._ux.busy(window, 3)
    assert not window._ui_piece_grid.Visible
    assert not window._ui_plan_metrics.Visible
    assert not window._ui_tabs.bar.Enabled
    window._ux.solved(window)
    assert window._ui_piece_grid.Visible
    assert window._ui_plan_metrics.Visible


def test_stepper_updates_with_review_and_creation_state():
    window, handler = form()
    handler.solve_result = result()
    window._ux.solved(window)
    assert window._ui_header._stepper._step == 4
    assert "atual" in window._ui_header._stepper._items[3].AccessibleName
    window._ux.busy(window, 5)
    assert window._ui_header._stepper._step == 5
    assert "futura" in window._ui_header._stepper._items[5].AccessibleName


def test_future_adjustment_summary_is_absent_without_evidence():
    window, handler = form()
    assert "Aberturas movidas: —" in window._ui_adjustments.Text
    report = {"kpis": [], "issues": [], "log": "", "automatic_adjustments": [{"id": "example"}]}
    window = m._PostCreationForm(report, None, handler, [])
    assert "Aberturas movidas: —" in window._ui_adjustments.Text
    assert "ajustada automaticamente" not in window._ui_adjustments.Text


def test_execution_snapshot_requires_confirmation_and_rejects_stale_events():
    window, handler = form()
    payload = dict(run_id="run-1", revision=0, walls_analyzed=34, openings_moved=2,
                   adjustment_status="planned", warnings=1, hard_gates=0)
    assert window._ux.present_execution(window, payload, new_run=True)
    assert "Aberturas movidas: —" in window._ui_adjustments.Text
    payload.update(revision=1, adjustment_status="confirmed")
    assert window._ux.present_execution(window, payload)
    assert "Aberturas movidas: 2" in window._ui_adjustments.Text
    assert not window._ux.present_execution(window, dict(payload, revision=0))
    assert not window._ux.present_execution(window, dict(payload, run_id="old", revision=10))
    window._ux.busy(window, 3)
    assert "Aberturas movidas: —" in window._ui_adjustments.Text
    assert not window._ux.present_execution(window, dict(payload, revision=2))


@pytest.mark.parametrize("value", [None, -1, True, "4", 1.5])
def test_invalid_counts_do_not_claim_confirmed_movement(value):
    from core.ui_execution import ExecutionPresentation
    state = ExecutionPresentation("run")
    state.update(dict(run_id="run", revision=0, adjustment_status="confirmed", openings_moved=value))
    assert "Aberturas movidas: —" in state.summary()
    assert "ajustada automaticamente" not in state.summary()


def test_presentation_cannot_release_a_physical_gate():
    window, handler = form()
    handler.solve_result = result(beta_preflight={"ok": False})
    window._ux.solved(window)
    window._ux.present_execution(window, dict(run_id="run", revision=0, hard_gates=0,
                                 adjustment_status="confirmed", openings_moved=1), new_run=True)
    assert not window._create_button.Enabled


def test_activity_translates_actual_events_without_fake_percentages():
    from core.ui_state import activity_text
    assert activity_text("building junction graph") == "Organizando os encontros entre paredes…"
    assert activity_text("loading catalog") == "Verificando as famílias disponíveis…"


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


def test_missing_family_opens_inline_details_on_construction():
    handler = m._PostCreationEventHandler()
    handler.catalog_missing = [{"logical_code": "B39", "family_name": "Bloco 39",
                                "type_name": "39", "reason": "Ausente"}]
    window = m._PostCreationForm({"kpis": [], "issues": [], "log": ""}, None, handler, [])
    assert window._ui_family_disclosure._expanded
    assert "Faltam famílias" in window._ui_header._instruction.Text
    assert not window._solve_button.Enabled


def test_dark_review_keeps_ids_and_internal_codes_only_in_details():
    window, handler = form()
    handler.error_rows = [{"wall_idx": 42, "wall_ids": [7719511], "problem_text": "W043 PRISM collision",
                           "auto_fixable": False}]
    window._populate_error_rows(handler.error_rows)
    item = window._errors_grid.Items[0]
    assert item.Text == "Parede 1"
    assert item.Tag == [7719511]
    assert "sobreposição" in str(item.SubItems[1])
    assert "7719511" in window._ui_technical_issues.Text
    assert "W043 PRISM collision" in window._ui_technical_issues.Text


def test_skipped_analysis_never_looks_like_clean_validation():
    handler = m._PostCreationEventHandler()
    window = m._PostCreationForm({"kpis": [], "issues": [], "log": "", "wall_analysis_skipped": True}, None, handler, [])
    assert "não executada" in window._errors_status.Text


def test_busy_disables_tabs_and_replaces_ready_banner():
    window, handler = form()
    handler.solve_result = result()
    window._ux.solved(window)
    window._ux.busy(window, 5)
    assert window._ui_state.status == "creating"
    assert not window._ui_tabs.bar.Enabled
    assert "Criando" in window._ui_banner.Text
    window._ux.failed(window, "erro")
    assert window._ui_tabs.bar.Enabled


def test_repeated_plan_shows_cached_lot_without_model_query():
    window, handler = form()
    handler.solve_result = result()
    handler.create_result = {"created_count": 123}
    window._ux.solved(window)
    assert window._create_button.Text == "Atualizar modulação"
    assert "123" in window._ui_banner.Text
    assert "substituído" in window._ui_banner.Text


def test_preview_tracks_strategy_without_changing_configuration():
    from core.ui_components import UiComponents
    ui = UiComponents(m.__dict__)
    preview = ui.preview("none")
    preview._set_kind("channel")
    assert preview._canvas._preview_kind == "channel"
    assert "não representa o plano" in preview._canvas.AccessibleName


def test_final_summary_preserves_failures_and_secondary_report():
    window, handler = form()
    handler.solve_result = result()
    window._ux.solved(window)
    handler.create_result = {"created_count": 12, "failures": ["PRISM W043"]}
    window._ux.completed(window)
    assert "pendências" in window._ui_result_title.Text
    assert "1 falha" in window._ui_result_counts.Text
    assert "PRISM" not in window._ui_result.Text
