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


def dropdown(ui, source, caption):
    """Native menu/button presentation over the unchanged ComboBox data contract.

    All existing validation and selection handlers still run on `source`.
    No replacement configuration store or backend query is introduced.
    """
    def open_menu():
        return None  # Offline controls have no native menu surface.
    button = ui.button("", lambda s, e: open_menu())
    button.Dock = ui.ns["DockStyle"].Top
    button.Height = 32
    button.AccessibleName = caption
    button._source_combo = source
    source.Visible = False
    button.Controls.Add(source)
    button.FlatAppearance.BorderColor = ui.color("Border")
    button.BackColor = ui.color("SurfaceAlt")

    def sync(sender=None, args=None):
        selected = source.SelectedItem
        button.Text = str(selected) if selected is not None else str(source.Text or "Selecionar")
    source.SelectedIndexChanged += sync
    sync()
    try:
        from System.Drawing import ContentAlignment, Point, Color, Pen
        from System.Windows.Forms import ContextMenuStrip, ToolStripMenuItem, AccessibleRole, Keys
    except ImportError:
        return button
    button.TextAlign = ContentAlignment(16)  # MiddleLeft
    button.Padding = ui.ns["Padding"](8, 0, 28, 0)
    button.AccessibleRole = AccessibleRole(46)  # ComboBox
    source.EnabledChanged += lambda s, e: setattr(button, "Enabled", source.Enabled)
    button.Enabled = source.Enabled
    menu = ContextMenuStrip()
    menu.BackColor, menu.ForeColor = ui.color("SurfaceAlt"), ui.color("TextPrimary")
    menu.ShowImageMargin = False
    button._menu = menu

    def choose(index):
        source.SelectedIndex = index
        button.Focus()

    def build_menu():
        for item in list(menu.Items):
            item.Dispose()
        menu.Items.Clear()
        menu.Font = button.Font
        for i in range(source.Items.Count):
            item = ToolStripMenuItem(str(source.Items[i]))
            item.Checked = source.SelectedIndex == i
            item.BackColor, item.ForeColor = menu.BackColor, menu.ForeColor
            item.Click += lambda s, e, index=i: choose(index)
            menu.Items.Add(item)
        return menu
    button._build_menu = build_menu

    def open_menu():
        build_menu().Show(button, Point(0, button.Height))

    def key(sender, args):
        code = int(args.KeyCode)
        if args.Alt and code == int(Keys(40)):
            open_menu()
        elif code in (38, 40) and source.Items.Count:
            choose(max(0, min(source.Items.Count - 1, source.SelectedIndex + (1 if code == 40 else -1))))
        else:
            return
        args.Handled, args.SuppressKeyPress = True, True
    button.KeyDown += key
    button.GotFocus += lambda s, e: setattr(button.FlatAppearance, "BorderColor", ui.color("Primary"))
    button.LostFocus += lambda s, e: setattr(button.FlatAppearance, "BorderColor", ui.color("Border"))
    def arrow(sender, args):
        pen = Pen(ui.color("TextSecondary"), 1.4)
        try:
            x, y = button.Width - 18, button.Height // 2
            args.Graphics.DrawLine(pen, x - 4, y - 2, x, y + 2)
            args.Graphics.DrawLine(pen, x, y + 2, x + 4, y - 2)
        finally:
            pen.Dispose()
    button.Paint += arrow
    button.Disposed += lambda s, e: menu.Dispose()
    return button
