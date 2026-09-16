# -*- coding: utf-8 -*-
"""Paint-only decorators on native, keyboard-accessible WinForms controls."""
from .ui_state import TOKENS, STEPS


def underline(button, is_active):
    try:
        from System.Drawing import Color, SolidBrush
    except ImportError:
        return
    def paint(sender, args):
        if not is_active():
            return
        brush = SolidBrush(Color.FromArgb(*TOKENS["Primary"]))
        try:
            args.Graphics.FillRectangle(brush, 12, button.Height - 3, max(1, button.Width - 24), 3)
        finally:
            brush.Dispose()
    button.Paint += paint


def separator(control, edge="bottom"):
    try:
        from System.Drawing import Color, Pen
    except ImportError:
        return
    def paint(sender, args):
        pen = Pen(Color.FromArgb(*TOKENS["Border"]))
        try:
            y = 0 if edge == "top" else control.Height - 1
            args.Graphics.DrawLine(pen, 0, y, control.Width, y)
        finally:
            pen.Dispose()
    control.Paint += paint


def choice(control):
    """Keep native Checked, events and keyboard; replace only the white glyph."""
    try:
        from System.Drawing import Color, Pen, SolidBrush, Rectangle
        from System.Windows.Forms import TextRenderer, TextFormatFlags
        from System.Drawing.Drawing2D import SmoothingMode
    except ImportError:
        return
    def paint(sender, args):
        g = args.Graphics
        s = max(1.0, control.Font.Height / 15.0)
        d, x = int(14 * s), int(3 * s)
        y = max(1, (control.Height - d) // 2)
        bg = SolidBrush(control.BackColor)
        color = Color.FromArgb(*TOKENS["Primary" if control.Checked else "TextSecondary"])
        pen, fill = Pen(color, max(1.0, s)), SolidBrush(color)
        try:
            g.FillRectangle(bg, control.ClientRectangle)
            g.SmoothingMode = SmoothingMode(4)
            if type(control).__name__ == "RadioButton":
                g.DrawEllipse(pen, x, y, d, d)
                if control.Checked:
                    inset = max(3, int(4 * s))
                    g.FillEllipse(fill, x + inset, y + inset, d - inset * 2, d - inset * 2)
            else:
                g.DrawRectangle(pen, x, y, d, d)
                if control.Checked:
                    g.DrawLine(pen, x + 3, y + d // 2, x + d // 2, y + d - 3)
                    g.DrawLine(pen, x + d // 2, y + d - 3, x + d - 2, y + 3)
            bounds = Rectangle(x + d + int(8*s), 0, max(1, control.Width - x - d - int(8*s)), control.Height)
            TextRenderer.DrawText(g, control.Text, control.Font, bounds, control.ForeColor, TextFormatFlags(4 | 32))
            if control.Focused:
                g.DrawRectangle(pen, 0, 0, control.Width - 1, control.Height - 1)
        finally:
            bg.Dispose()
            pen.Dispose()
            fill.Dispose()
    control.Paint += paint
    control.CheckedChanged += lambda s, e: control.Invalidate()


def stepper(ui):
    strip = ui.panel("Top", 32)
    strip._step = 1
    strip._items = []
    for index, name in enumerate(STEPS):
        item = ui.label("○ " + name, 30)
        item.Dock = getattr(ui.ns["DockStyle"], "None")
        item.Font = ui.ns["_ui_font"](8.25)
        item.Padding = ui.ns["Padding"](0, 6, 0, 0)
        strip.Controls.Add(item)
        strip._items.append(item)
    def layout(sender=None, args=None):
        width = strip.ClientSize.Width
        if not isinstance(width, (int, float)) or width <= 0:
            return
        unit = width / 6.0
        for i, item in enumerate(strip._items):
            item.Left = int(i * unit)
            item.Width = int(unit)
    def update(step):
        strip._step = step
        for i, item in enumerate(strip._items):
            current = i + 1 == step
            symbol = "●" if current else "✓" if i + 1 < step else "○"
            item.Text = symbol + " " + STEPS[i]
            item.ForeColor = ui.color("TextPrimary" if current else "TextSecondary")
            item.AccessibleName = STEPS[i] + (" — atual" if current else " — percorrida" if i+1 < step else " — futura")
        layout()
    strip._set_step = update
    strip.Resize += layout
    separator(strip)
    update(1)
    return strip
