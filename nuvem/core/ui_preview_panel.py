# -*- coding: utf-8 -*-
"""Illustrative drawing only. No model reads, layout solver or physical rules."""
from .ui_state import TOKENS


def attach_preview(canvas, kind="cad"):
    canvas._preview_kind = kind
    canvas.AccessibleName = "Prévia ilustrativa, sem escala; não representa o plano calculado"

    def set_kind(value):
        canvas._preview_kind = value
        canvas.Invalidate()
    canvas._set_kind = set_kind
    try:
        from System.Drawing import Color, Pen, SolidBrush, Rectangle
    except ImportError:
        return  # Test doubles do not provide a drawing surface.

    def paint(sender, args):
        g = args.Graphics
        w, h = canvas.ClientSize.Width, canvas.ClientSize.Height
        if w < 80 or h < 80:
            return
        scale = min((w - 32) / 240.0, (h - 32) / 200.0)
        x0, y0 = (w - 240 * scale) / 2, (h - 200 * scale) / 2
        mode = canvas._preview_kind
        brushes = {k: SolidBrush(Color.FromArgb(*TOKENS[k]))
                   for k in ("SurfaceAlt", "Background", "Primary", "TextSecondary")}
        pen = Pen(Color.FromArgb(*TOKENS["Border"]), max(1.0, scale))
        accent = Pen(Color.FromArgb(*TOKENS["Primary"]), max(2.0, 2 * scale))
        def rect(x, y, width, height):
            return Rectangle(int(x0 + x * scale), int(y0 + y * scale),
                             max(1, int(width * scale)), max(1, int(height * scale)))
        def fill(key, x, y, width, height):
            g.FillRectangle(brushes[key], rect(x, y, width, height))
        def outline(p, x, y, width, height):
            g.DrawRectangle(p, rect(x, y, width, height))
        try:
            if mode == "cad":
                for x in (10, 18, 100, 108):
                    outline(pen, x, 32, 2, 120)
                for y in (32, 40, 144, 152):
                    outline(pen, 10, y, 100, 2)
                fill("Primary", 144, 32, 14, 126)
                fill("Primary", 144, 32, 80, 14)
                fill("Primary", 144, 144, 80, 14)
                fill("TextSecondary", 119, 92, 15, 3)
            else:
                # A schematic wall silhouette, not a generated bond pattern.
                fill("SurfaceAlt", 12, 24, 216, 150)
                outline(pen, 12, 24, 216, 150)
                if mode in ("blocks", "channel", "none"):
                    for y in range(24, 174, 25):
                        for x in range(12, 228, 36):
                            outline(pen, x, y, 36, 25)
                fill("Background", 86, 65, 68, 62)
                outline(pen, 86, 65, 68, 62)
                if mode == "channel":
                    fill("Primary", 65, 49, 110, 14)
                    fill("Primary", 65, 129, 110, 14)
                if mode == "selection":
                    outline(accent, 6, 18, 228, 162)
                    for x in (2, 230):
                        for y in (14, 176):
                            fill("Primary", x, y, 8, 8)
        finally:
            pen.Dispose()
            accent.Dispose()
            for brush in brushes.values():
                brush.Dispose()
    canvas.Paint += paint
    canvas.Resize += lambda sender, args: canvas.Invalidate()
