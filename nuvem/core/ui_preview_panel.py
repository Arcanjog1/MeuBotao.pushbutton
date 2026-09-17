# -*- coding: utf-8 -*-
"""Local vector illustration. Never reads Revit or runs physical layout rules."""
from .ui_state import TOKENS


def attach_preview(canvas, kind="cad"):
    canvas._preview_kind = kind
    canvas.AccessibleName = "Prévia ilustrativa; não representa o plano calculado. A geometria final será calculada a partir do modelo."

    def set_kind(value):
        canvas._preview_kind = value
        canvas.Invalidate()
    canvas._set_kind = set_kind
    try:
        from System import Array
        from System.Drawing import Color, Pen, SolidBrush, RectangleF, PointF, Font, FontStyle
        from System.Drawing.Drawing2D import SmoothingMode
    except ImportError:
        return

    def paint(sender, args):
        g = args.Graphics
        w, h = canvas.ClientSize.Width, canvas.ClientSize.Height
        if w < 80 or h < 80:
            return
        scale = min((w - 16) / 280.0, (h - 16) / 245.0)
        x0, y0 = (w - 280 * scale) / 2, min(32, max(8, (h - 245 * scale) / 3))
        state = g.Save()
        g.TranslateTransform(float(x0), float(y0))
        g.ScaleTransform(float(scale), float(scale))
        g.SmoothingMode = SmoothingMode(4)
        brushes = {k: SolidBrush(Color.FromArgb(*v)) for k, v in TOKENS.items()}
        pens = {k: Pen(Color.FromArgb(*TOKENS[k]), 1.0) for k in ("Border", "Background", "TextSecondary", "Reinforcement")}
        font = Font("Segoe UI", 9.0, FontStyle(0))
        def polygon(key, points):
            g.FillPolygon(brushes[key], Array[PointF]([PointF(float(x), float(y)) for x, y in points]))
        def rect(key, x, y, width, height):
            g.FillRectangle(brushes[key], RectangleF(float(x), float(y), float(width), float(height)))
        def line(key, x, y, xx, yy):
            g.DrawLine(pens[key], float(x), float(y), float(xx), float(yy))
        def text(value, x, y, key="TextSecondary"):
            g.DrawString(value, font, brushes[key], PointF(float(x), float(y)))
        try:
            mode = canvas._preview_kind
            polygon("Background", [(16, 193), (232, 193), (270, 172), (56, 172)])
            for y in (42, 76, 110, 144, 178):
                line("Border", 8, y, 272, y)
            if mode == "cad":
                for x in (20, 28, 96, 104):
                    line("TextSecondary", x, 58, x, 156)
                for y in (58, 66, 148, 156):
                    line("TextSecondary", 20, y, 104, y)
                line("Reinforcement", 119, 108, 144, 108)
                line("Reinforcement", 137, 102, 144, 108)
                line("Reinforcement", 137, 114, 144, 108)
                rect("Stone", 158, 58, 18, 106)
                rect("Stone", 158, 58, 83, 18)
                rect("Stone", 158, 146, 83, 18)
                polygon("StoneTop", [(158, 58), (174, 46), (257, 46), (241, 58)])
                polygon("StoneSide", [(241, 58), (257, 46), (257, 64), (241, 76)])
                text("01  Desenho CAD", 12, 203)
                text("02  Paredes", 156, 203)
            else:
                # Generic elevation, not computed bond or a construction detail.
                polygon("StoneSide", [(241, 48), (259, 35), (259, 174), (241, 187)])
                polygon("StoneTop", [(25, 48), (43, 35), (259, 35), (241, 48)])
                rect("Stone", 25, 48, 216, 139)
                for row in range(7):
                    y = 48 + row * 20
                    line("Background", 25, y, 241, y)
                    offset = 0 if row % 2 == 0 else 18
                    for x in range(25 + offset, 242, 36):
                        line("Background", x, y, x, min(187, y + 20))
                rect("Background", 93, 90, 76, 59)
                polygon("StoneSide", [(93, 90), (105, 82), (105, 141), (93, 149)])
                polygon("StoneTop", [(93, 149), (105, 141), (181, 141), (169, 149)])
                if mode == "channel":
                    for y in (70, 150):
                        rect("Reinforcement", 61, y, 144, 18)
                        polygon("Primary", [(61, y), (71, y - 7), (215, y - 7), (205, y)])
                        for x in (97, 133, 169):
                            line("Background", x, y + 1, x, y + 17)
                    line("Reinforcement", 206, 78, 266, 78)
                    line("Reinforcement", 206, 158, 266, 158)
                    text("01", 246, 60, "TextPrimary")
                    text("02", 246, 160, "TextPrimary")
                    text("01  Canaleta superior", 25, 206)
                    text("02  Canaleta inferior", 25, 225)
                elif mode == "selection":
                    for x, y in ((21, 44), (237, 44), (21, 183), (237, 183)):
                        rect("Primary", x, y, 8, 8)
                    text("Seleção de paredes no modelo", 25, 212)
                elif mode == "none":
                    text("Alvenaria sem reforço de abertura", 25, 212)
                else:
                    text("Composição ilustrativa da alvenaria", 25, 212)
        finally:
            g.Restore(state)
            font.Dispose()
            for pen in pens.values():
                pen.Dispose()
            for brush in brushes.values():
                brush.Dispose()
    canvas.Paint += paint
    canvas.Resize += lambda sender, args: canvas.Invalidate()
