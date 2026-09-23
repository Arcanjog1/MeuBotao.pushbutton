"""Native presentation fixtures only; all movement confirmations are synthetic."""
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
p = runpy.run_path(str(ROOT / "tools/ui_preview.py"))
p["Application"].EnableVisualStyles()
out = ROOT / "docs/ui-post42-preview"
out.mkdir(exist_ok=True)
results = {}
for status in ("planned", "applying", "confirmed", "not_required", "failed", "cancelled"):
    payload = dict(run_id="synthetic-run", revision=0, walls_analyzed=34,
                   openings_moved=2 if status == "confirmed" else None,
                   adjustment_status=status, warnings=1, hard_gates=0,
                   detail="DADOS SINTÉTICOS. Exemplo: abertura 101 / parede 201; deslocamento confirmado de 10 mm. Nenhum modelo foi alterado.")
    report = dict(kpis=[], issues=[], log="Fixture sintética", ui_execution=payload)
    h = p["sample"]()
    f = p["ns"]["_PostCreationForm"](report, None, h, [])
    results[status] = p["render"](f, out / ("microajuste-" + status + ".png"))
    assert ("ajustada automaticamente" in f._ui_adjustments.Text) == (status == "confirmed")
    if status == "confirmed":
        f._ux.solved(f)
        results["confirmed-plan"] = p["render"](f, out / "microajuste-plano.png")
        h.create_result = dict(created_count=58, failures=[])
        f._ux.completed(f)
        assert "Aberturas movidas: 2" in f._ui_result.Text
        results["confirmed-result"] = p["render"](f, out / "microajuste-resultado.png")
    f.Dispose()

for state in ("gate", "error", "progress"):
    h = p["sample"]()
    f = p["ns"]["_PostCreationForm"](dict(kpis=[], issues=[], log=""), None, h, [])
    if state == "gate":
        h.solve_result["beta_preflight"] = dict(ok=False, errors=["Colisão detectada"])
        f._ux.solved(f)
        assert not f._create_button.Enabled
    elif state == "error":
        f._ux.busy(f, 3)
        f._ux.failed(f, "Falha sintética de cálculo")
        assert not f._create_button.Enabled and f._ui_close.Enabled
    else:
        f._ux.busy(f, 3)
        f._solve_console.set_progress(12, 34, "12 de 34 paredes processadas — dados sintéticos")
        assert not f._ui_tabs.bar.Enabled
    results[state] = p["render"](f, out / (state + ".png"))
    f.Dispose()
(out / "states.json").write_text(json.dumps(dict(kind="Synthetic native WinForms; no Revit operations", renders=results), indent=2), encoding="utf-8")
print("11 native presentation fixtures PASS")
