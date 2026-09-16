# -*- coding: utf-8 -*-
"""Render real WinForms offscreen, using fake Revit data. Never opens Revit.

Run with a disposable Windows Python environment containing pythonnet.
This is visual QA, not evidence of an in-Revit smoke test or native DPI.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
from System.Drawing import Bitmap, Rectangle, SizeF
from System.Drawing.Imaging import ImageFormat
from System.Windows.Forms import Application, AutoScaleMode
real_modules = {k: v for k, v in sys.modules.items() if k == "clr" or k == "System" or k.startswith("System.")}

import load_script
m = load_script.load()
import revit_stubs
for name in list(sys.modules):
    if name == "clr" or name == "System" or name.startswith("System."):
        sys.modules.pop(name)
sys.modules.update(real_modules)

source = (ROOT / "nuvem/core/wall_modeling.py").read_text(encoding="utf-8")
ns = dict(m.__dict__)
start = source.index('import clr\nclr.AddReference("System.Windows.Forms")')
end = source.index('def build_report_highlights(', start)
exec(compile(source[start:end], "ui-native-components", "exec"), ns)
tree = ast.parse(source)
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name in ("_PostCreationForm", "_WallReviewForm", "_WallSourceModeForm"):
        exec(compile(ast.Module(body=[node], type_ignores=[]), "ui-native-forms", "exec"), ns)


def sample():
    h = m._PostCreationEventHandler()
    h.walls_to_create = [None] * 34
    h.all_openings = [None] * 44
    h.error_rows = [{"wall_idx": 0, "wall_ids": [7719511],
                     "problem_text": "Trecho requer revisão junto à abertura", "auto_fixable": False}]
    h.opening_reinforcement_strategy = "CHANNEL"
    h.catalog = {}
    h.channel_catalog = {"CHANNEL_U_39": {}, "CHANNEL_U_19": {}}
    h.solve_result = dict(candidates=[{"logical_code": "B39", "course": "A"}],
                          course_candidates={0: [{"logical_code": "B39"}] * 50,
                                             1: [{"logical_code": "CHANNEL_U_39"}] * 8},
                          collisions=[], door_void_violations=[], wall_bond_audits={}, num_courses=2,
                          intersection_failures=[], jamb_exceptions=[], non_modular=[], per_wall=[], validations=[])
    return h


def render(form, output, scale=1.0):
    form.AutoScaleMode = AutoScaleMode(0)
    form.ShowInTaskbar = False
    form.Opacity = 0.0
    form.Show()
    Application.DoEvents()  # Standalone renderer only; never part of the plugin.
    form.CreateControl()
    form.PerformLayout()
    if scale != 1:
        form.Scale(SizeF(scale, scale))
    form.PerformLayout()
    bitmap = Bitmap(form.Width, form.Height)
    form.DrawToBitmap(bitmap, Rectangle(0, 0, form.Width, form.Height))
    bitmap.Save(str(output), ImageFormat.Png)
    bitmap.Dispose()
    return {"width": form.Width, "height": form.Height}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    Application.EnableVisualStyles()
    report = {"kpis": [("Paredes selecionadas", 34, ns["UI_ACCENT"]),
                       ("Aberturas detectadas", 44, ns["UI_TEXT"]), ("Avisos", 1, ns["UI_WARN"])],
              "issues": [], "log": "Dados ilustrativos para conferência visual."}
    forms = []
    forms.append(("01-fonte", ns["_WallSourceModeForm"]()))
    line = revit_stubs.Line.CreateBound
    xyz = revit_stubs.XYZ
    forms.append(("02-configuracao", ns["_SetupForm"]({"PAREDES": [line(xyz(0, 0, 0), xyz(10, 0, 0)),
                                                           line(xyz(0, .4593, 0), xyz(10, .4593, 0))]}, ["Térreo", "Pavimento 1"], {})))
    forms.append(("03-paredes", ns["_WallReviewForm"](report, None, sample(), lambda x: None, None)))
    form = ns["_PostCreationForm"](report, None, sample(), [])
    forms.append(("04-revisao", form))
    results = {}
    for name, window in forms:
        results[name] = render(window, out / (name + ".png"))
    form._ux.solved(form)
    form._solve_console.mark_complete("Análise concluída. Confira o plano de blocos.")
    results["05-plano"] = render(form, out / "05-plano.png")
    form._ux.busy(form, 5)
    form._solve_console.set_status("Criando blocos no Revit")
    form._solve_console.set_progress(38, 58, "Inserindo as peças da fiada 2")
    results["06-criacao"] = render(form, out / "06-criacao.png")
    form._handler.create_result = {"created_count": 58, "failures": []}
    form._solve_console.mark_complete("58 blocos criados no Revit.")
    form._create_button.Enabled = True
    form._ux.completed(form)
    results["07-resultado"] = render(form, out / "07-resultado.png")
    for scale in (1, 1.25, 1.5, 1.75, 2):
        window = ns["_PostCreationForm"](report, None, sample(), [])
        window._ux.solved(window)
        results["scale-" + str(scale)] = render(window, out / ("scale-" + str(scale) + ".png"), scale)
        window.Dispose()
    small = ns["_PostCreationForm"](report, None, sample(), [])
    small.Width, small.Height = 740, 520
    small._ux.solved(small)
    results["small-740x520"] = render(small, out / "small-740x520.png")
    small.Dispose()
    for _, window in forms:
        window.Dispose()
    (out / "render.json").write_text(json.dumps({"kind": "Offscreen WinForms; synthetic data; explicit Scale, not native Windows DPI",
                                                  "renders": results}, indent=2), encoding="utf-8")
    print(json.dumps(results))


if __name__ == "__main__":
    main()
