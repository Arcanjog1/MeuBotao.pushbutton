"""Additional native WinForms error/cancel fixtures; never opens Revit."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
preview = runpy.run_path(str(ROOT / "tools/ui_preview.py"))
ns, sample, render = preview["ns"], preview["sample"], preview["render"]
preview["Application"].EnableVisualStyles()
output = ROOT / "docs/ui-preview"
report = {"kpis": [], "issues": [], "log": "Dados sintéticos para validação visual."}

handler = sample()
handler.catalog_missing = [{"logical_code": "B39", "family_name": "Bloco 39",
                            "type_name": "14 x 19 x 39", "reason": "Família não encontrada"}]
window = ns["_PostCreationForm"](report, None, handler, [])
render(window, output / "08-familia-ausente.png")
window.Dispose()

handler = sample()
handler.solve_result["beta_preflight"] = {"ok": False, "errors": ["Plano requer revisão"],
                                         "collisions": [], "opening_violations": []}
window = ns["_PostCreationForm"](report, None, handler, [])
window._ux.solved(window)
render(window, output / "09-gate-critico.png")
window.Dispose()

window = ns["_WallReviewForm"](report, None, sample(), lambda _: None, None)
window._cancel_requested = True
window._on_analyze_done("analyze", None)
render(window, output / "10-cancelamento.png")
window.Dispose()
print("Rendered missing family, backend gate and cancelled analysis (synthetic data).")
