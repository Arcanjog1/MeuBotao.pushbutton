# -*- coding: utf-8 -*-
"""Local native-control painting; never changes the Revit theme or message loop."""
from .ui_state import TOKENS


def style_disabled_button(button):
    try:
        from System.Drawing import Color, Pen, SolidBrush
        from System.Windows.Forms import TextRenderer, TextFormatFlags
    except ImportError:
        return
    def paint(sender, args):
        if button.Enabled:
            return
        fill = SolidBrush(Color.FromArgb(*TOKENS["SurfaceAlt"]))
        pen = Pen(Color.FromArgb(*TOKENS["Border"]))
        try:
            args.Graphics.FillRectangle(fill, button.ClientRectangle)
            args.Graphics.DrawRectangle(pen, 0, 0, max(1, button.Width - 1), max(1, button.Height - 1))
            TextRenderer.DrawText(args.Graphics, button.Text, button.Font, button.ClientRectangle,
                                  Color.FromArgb(*TOKENS["TextSecondary"]), TextFormatFlags(1 | 4 | 32))
        finally:
            fill.Dispose()
            pen.Dispose()
    button.Paint += paint


def style_input(control):
    try:
        from System.Drawing import Color, SolidBrush
        from System.Windows.Forms import DrawMode, TextRenderer, TextFormatFlags
    except ImportError:
        return
    control.DrawMode = DrawMode(1)  # OwnerDrawFixed
    control.ItemHeight = 18
    def draw(sender, args):
        selected = bool(int(args.State) & 1)
        bg = SolidBrush(Color.FromArgb(*TOKENS["Primary" if selected else "SurfaceAlt"]))
        try:
            args.Graphics.FillRectangle(bg, args.Bounds)
            text = str(control.Items[args.Index]) if args.Index >= 0 else str(control.Text)
            TextRenderer.DrawText(args.Graphics, text, control.Font, args.Bounds,
                                  Color.FromArgb(*TOKENS["TextPrimary"]),
                                  TextFormatFlags(4 | 32))  # VerticalCenter | SingleLine
            args.DrawFocusRectangle()
        finally:
            bg.Dispose()
    control.DrawItem += draw


def style_grid(grid):
    try:
        from System.Drawing import Color, SolidBrush
        from System.Windows.Forms import TextRenderer, TextFormatFlags
    except ImportError:
        return
    grid.OwnerDraw = True
    def header(sender, args):
        brush = SolidBrush(Color.FromArgb(*TOKENS["SurfaceAlt"]))
        try:
            args.Graphics.FillRectangle(brush, args.Bounds)
            TextRenderer.DrawText(args.Graphics, args.Header.Text, grid.Font, args.Bounds,
                                  Color.FromArgb(*TOKENS["TextSecondary"]), TextFormatFlags(4 | 32))
        finally:
            brush.Dispose()
    grid.DrawColumnHeader += header
    grid.DrawItem += lambda sender, args: setattr(args, "DrawDefault", False)
    def cell(sender, args):
        selected = bool(args.Item.Selected)
        brush = SolidBrush(Color.FromArgb(*TOKENS["Primary" if selected else "Surface"]))
        try:
            args.Graphics.FillRectangle(brush, args.Bounds)
            color = Color.FromArgb(*TOKENS["TextPrimary"]) if selected else args.Item.ForeColor
            if color.IsEmpty:
                color = Color.FromArgb(*TOKENS["TextPrimary"])
            bounds = args.Bounds
            bounds.X += 6
            bounds.Width = max(1, bounds.Width - 8)
            TextRenderer.DrawText(args.Graphics, args.SubItem.Text, grid.Font, bounds,
                                  color, TextFormatFlags(4 | 32 | 32768))
        finally:
            brush.Dispose()
    grid.DrawSubItem += cell
    def fit(sender, args):
        if grid.Columns.Count:
            occupied = sum(grid.Columns[i].Width for i in range(grid.Columns.Count - 1))
            grid.Columns[grid.Columns.Count - 1].Width = max(90, grid.ClientSize.Width - occupied)
    grid.Resize += fit
    grid.HandleCreated += fit
    grid.VisibleChanged += fit
    fit(None, None)
