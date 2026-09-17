"""WinForms layout stress test: scaled bounds AND fonts; never changes OS DPI.

The virtual workareas are constraints, not claims that these monitors exist.
Screenshots contain synthetic data and are not an in-Revit smoke test.
"""
import json
from pathlib import Path
import runpy
import argparse

ROOT = Path(__file__).resolve().parents[2]
p = runpy.run_path(str(ROOT / "tools/ui_preview.py"))
from System.Drawing import Font, Size, SizeF, Bitmap, Rectangle
from System.Drawing.Imaging import ImageFormat
from System.Windows.Forms import AutoScaleMode, Application

parser = argparse.ArgumentParser()
parser.add_argument("--out", default="docs/ui-premium-preview/matrix")
out = ROOT / parser.parse_args().out
out.mkdir(parents=True, exist_ok=True)
Application.EnableVisualStyles()
ns = p["ns"]
s = p["revit_stubs"]
line, xyz = s.Line.CreateBound, s.XYZ
report = {"kpis": [], "issues": [], "log": ""}
results = []


def walk(control):
    yield control
    for child in control.Controls:
        yield from walk(child)


for resolution in ((1366, 768), (1920, 1080), (2560, 1440)):
    for scale in (1, 1.25, 1.5, 1.75, 2):
        for name in ("setup", "review"):
            if name == "setup":
                f = ns["_SetupForm"]({"PAREDES": [line(xyz(0, 0, 0), xyz(10, 0, 0)),
                           line(xyz(0, .4593, 0), xyz(10, .4593, 0))]}, ["Térreo"], {})
                f._reinforcement_combo.SelectedIndex = 1
                f._setup_tabs.SelectedIndex = 1
                primary = f._run_button
            else:
                f = ns["_PostCreationForm"](report, None, p["sample"](), [])
                f._ux.solved(f)
                primary = f._create_button
            f.AutoScaleMode = AutoScaleMode(0)
            f.ShowInTaskbar, f.Opacity = False, 0
            f.Show()
            Application.DoEvents()  # Standalone QA process only.
            fonts = [(c, c.Font) for c in walk(f)]
            if scale != 1:
                f.Scale(SizeF(scale, scale))
                for c, font in fonts:
                    c.Font = Font(font.FontFamily, float(font.SizeInPoints * scale), font.Style)
            f.MinimumSize = Size(0, 0)
            f.Size = Size(min(round(860 * scale), resolution[0] - 24),
                          min(round(640 * scale), resolution[1] - 64))
            f.PerformLayout()
            Application.DoEvents()
            # Essential action must remain visible and fully inside its parent.
            bounds, area = primary.Bounds, primary.Parent.ClientRectangle
            action_fits = bounds.X >= 0 and bounds.Y >= 0 and bounds.Right <= area.Right and bounds.Bottom <= area.Bottom
            label_fits = primary.Width >= 120 * scale and primary.Height >= 24 * scale
            filename = "{}-{}x{}-{}pct.png".format(name, *resolution, int(scale * 100))
            bitmap = Bitmap(f.Width, f.Height)
            f.DrawToBitmap(bitmap, Rectangle(0, 0, f.Width, f.Height))
            bitmap.Save(str(out / filename), ImageFormat.Png)
            bitmap.Dispose()
            results.append({"screen": name, "resolution": resolution, "scale": scale,
                            "size": [f.Width, f.Height], "primary_visible": bool(primary.Visible),
                            "primary_inside_footer": action_fits, "primary_minimum_size": label_fits,
                            "screenshot": filename})
            f.Dispose()

data = {"kind": "Synthetic WinForms bounds+font stress test, NOT native Windows DPI or Revit smoke",
        "cases": results, "action_checks_pass": all(r["primary_visible"] and r["primary_inside_footer"] and r["primary_minimum_size"] for r in results)}
(out / "results.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print(json.dumps({"cases": len(results), "action_checks_pass": data["action_checks_pass"]}))
