"""Native WinForms visual/interaction fixtures; synthetic data, no Revit calls."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[2]
preview = runpy.run_path(str(ROOT / "tools/ui_preview.py"))
ns, sample, render = preview["ns"], preview["sample"], preview["render"]
preview["Application"].EnableVisualStyles()
out = ROOT / "docs/ui-premium-preview"
out.mkdir(exist_ok=True)
report = {"kpis": [], "issues": [], "log": "Dados sintéticos de conferência visual."}
results = {}

source = ns["_WallSourceModeForm"]()
source._rb_existing.Checked = True
assert source._source_preview._canvas._preview_kind == "selection"
assert not source._rb_cad.Checked and not source._rb_merge.Checked
source._rb_cad.Checked = True
assert not source._rb_existing.Checked and source._source_preview._canvas._preview_kind == "cad"
source._rb_existing.Checked = True
results["existing"] = render(source, out / "09-paredes-existentes.png")
source.Dispose()

stubs = preview["revit_stubs"]
line, xyz = stubs.Line.CreateBound, stubs.XYZ
setup = ns["_SetupForm"]({"PAREDES": [line(xyz(0, 0, 0), xyz(10, 0, 0)),
                                             line(xyz(0, .4593, 0), xyz(10, .4593, 0))]}, ["Térreo"], {})
setup._reinforcement_combo.SelectedIndex = 1
render(setup, out / "02-configuracao-channel.png")
setup._setup_tabs.buttons[1].PerformClick()
assert setup._setup_tabs.SelectedIndex == 1
assert setup._setup_preview._canvas._preview_kind == "channel"
selector = setup._reinforcement_combo._presentation
selector._build_menu().Items[0].PerformClick()
assert setup._reinforcement_combo.SelectedIndex == 0
assert setup._setup_preview._canvas._preview_kind == "none"
selector._build_menu().Items[1].PerformClick()
assert setup._reinforcement_combo.SelectedIndex == 1
assert "Canaletas" in selector.Text
assert setup._setup_preview._canvas._preview_kind == "channel"
results["channel"] = render(setup, out / "08-channel.png")
# Group isolation matters: wall mode must not uncheck opening detection.
setup._openings_auto.Checked = True
setup._wall_mode_continuous.Checked = True
assert setup._openings_auto.Checked and not setup._openings_pick.Checked
assert setup._wall_mode_continuous.Checked and not setup._wall_mode_segmented.Checked
setup.Dispose()

handler = sample()
handler.catalog_missing = [{"logical_code": "B39", "family_name": "Bloco 39",
                            "type_name": "14 x 19 x 39", "reason": "Família não encontrada"}]
window = ns["_PostCreationForm"](report, None, handler, [])
assert window._ui_family_disclosure._expanded and not window._solve_button.Enabled
results["missing_family"] = render(window, out / "10-familia-ausente.png")
window.Dispose()

handler = sample()
handler.solve_result["beta_preflight"] = {"ok": False, "errors": ["W043 PRISM collision"],
                                         "collisions": [], "opening_violations": []}
window = ns["_PostCreationForm"](report, None, handler, [])
window._ux.solved(window)
assert not window._create_button.Enabled
assert "PRISM" not in window._ui_plan.Text
results["critical_gate"] = render(window, out / "11-gate-critico.png")
window.Dispose()

window = ns["_WallReviewForm"](report, None, sample(), lambda _: None, None)
window._cancel_requested = True
window._on_analyze_done("analyze", None)
assert "interrompida" in window._console._status_label.Text
results["cancelled"] = render(window, out / "12-cancelamento.png")
window.Dispose()

(out / "interaction-checks.json").write_text(json.dumps({
    "kind": "Native WinForms/pythonnet fixtures; synthetic data, not Revit smoke or native DPI",
    "checks": ["native menu selects NONE and CHANNEL through original validation callbacks", "preview follows source and strategy", "tab button changes visible page",
               "radio groups stay independent", "missing family expands inline and blocks solve",
               "backend critical gate disables create", "technical code hidden from friendly report",
               "cancelled wall analysis remains on the same screen"],
    "result": "PASS", "renders": results}, indent=2), encoding="utf-8")
print(json.dumps({"result": "PASS", "renders": results}))
