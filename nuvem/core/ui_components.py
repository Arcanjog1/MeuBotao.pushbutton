# -*- coding: utf-8 -*-
"""Reusable WinForms presentation. API calls and execution stay with the host.

The small namespace adapter reuses the host's pythonnet enum compatibility
layer. It does not introduce another event loop, thread or framework.
"""
from .ui_state import STEPS, TYPE, TOKENS, ModulationUiState, family_rows, wall_label
from .ui_preview_panel import attach_preview
from .ui_native_style import style_input, style_grid, style_disabled_button
from .ui_chrome import underline, separator, choice, stepper


class TabDeck(object):
    """Native keyboard-focusable buttons and panels, without light OS tab chrome."""
    def __init__(self, ui, captions):
        self.panel = ui.panel()
        self.bar = ui.panel("Top", 36)
        separator(self.bar)
        self.pages, self.buttons = [], []
        self.changed = []
        self._selected = 0
        for index, caption in enumerate(captions):
            page = ui.panel()
            page.AutoScroll = True
            page.Padding = ui.ns["Padding"](8)
            self.pages.append(page)
            self.panel.Controls.Add(page)
            button = ui.button(caption, lambda s, e, i=index: setattr(self, "SelectedIndex", i))
            button.Dock = ui.ns["DockStyle"].Left
            button.Width = max(140, len(caption) * 7 + 24)
            button.Height = 36
            button.FlatAppearance.BorderSize = 0
            button.TabIndex = index
            underline(button, lambda i=index: self._selected == i)
            self.buttons.append(button)
        for button in reversed(self.buttons):
            self.bar.Controls.Add(button)
        self.panel.Controls.Add(self.bar)
        self.ui = ui
        self.SelectedIndex = 0

    @property
    def SelectedIndex(self):
        return self._selected

    @SelectedIndex.setter
    def SelectedIndex(self, value):
        self._selected = value
        for i, (page, button) in enumerate(zip(self.pages, self.buttons)):
            page.Visible = i == value
            button.BackColor = self.ui.color("Surface")
            button.ForeColor = self.ui.color("TextPrimary" if i == value else "TextSecondary")
            button.FlatAppearance.BorderColor = self.ui.color("Primary" if i == value else "Background")
            button.AccessibleName = button.Text + (" — selecionada" if i == value else "")
            button.Invalidate()
        for callback in self.changed:
            callback(value)


class UiComponents(object):
    def __init__(self, ns):
        self.ns = dict(ns)

    def new(self, name):
        return self.ns[name]()

    def color(self, name):
        return self.ns["Color"].FromArgb(*TOKENS[name])

    def display_scale(self, control):
        try:
            return max(1.0, float(control.Font.SizeInPoints) / TYPE["Body"])
        except (TypeError, ValueError, AttributeError):
            return 1.0

    def theme(self, control):
        """Set local control colors only. No host theme/DPI/thread changes."""
        control.BackColor = self.ns["UI_PANEL"]
        control.ForeColor = self.ns["UI_TEXT"]
        kind = type(control).__name__
        if kind in ("TextBox", "ComboBox", "CheckedListBox"):
            control.BackColor = self.color("SurfaceAlt")
            control.Font = self.ns["_ui_font"](TYPE["Body"])
        if kind == "ComboBox":
            control.FlatStyle = self.ns["FlatStyle"].Flat
        if kind in ("RadioButton", "CheckBox"):
            control.UseVisualStyleBackColor = False
            if not getattr(control, "_premium_choice", False):
                choice(control)
                control._premium_choice = True
        for child in control.Controls:
            # Button colors encode action hierarchy; keep them.
            if type(child).__name__ != "Button":
                self.theme(child)

    def field(self, caption, control, height=60):
        row = self.panel("Top", height)
        row.Padding = self.ns["Padding"](0, 0, 8, 8)
        control.Dock = self.ns["DockStyle"].Top
        control.Height = height - 30
        control.AccessibleName = caption
        title = self.label(caption, 24)
        title.ForeColor = self.color("TextSecondary")
        title.Padding = self.ns["Padding"](0, 2, 0, 2)
        input_kind = type(control).__name__
        if input_kind in ("ComboBox", "TextBox"):
            shell = self.panel("Top", 30)
            shell.BackColor = self.color("SurfaceAlt")
            control.Dock = getattr(self.ns["DockStyle"], "None")
            if input_kind == "TextBox":
                try:
                    from System.Windows.Forms import BorderStyle
                    control.BorderStyle = BorderStyle(0)
                except ImportError:
                    pass
            shell.Controls.Add(control)
            # Retain the original input and all its handlers. Cropping native
            # combo edges and drawing a local arrow does not replace selection.
            arrow = None
            if input_kind == "ComboBox":
                crop = self.panel()
                crop.Dock = getattr(self.ns["DockStyle"], "None")
                crop.BackColor = self.color("SurfaceAlt")
                crop.Controls.Add(control)
                shell.Controls.Add(crop)
                arrow = self.button("⌄", lambda s, e: setattr(control, "DroppedDown", True))
                arrow.Dock = self.ns["DockStyle"].Right
                arrow.Width = 28
                arrow.TabStop = False
                arrow.FlatAppearance.BorderSize = 0
                arrow.BackColor = self.color("SurfaceAlt")
                arrow.AccessibleName = "Abrir " + caption
                shell.Controls.Add(arrow)
            def layout_input(sender=None, args=None):
                width = shell.ClientSize.Width
                if not isinstance(width, (int, float)) or width <= 0:
                    return
                control.Left = -1 if input_kind == "ComboBox" else 8
                control.Top = max(2, (shell.Height - control.Height) // 2)
                control.Width = max(30, width + 2 if arrow else width - 16)
                if arrow:
                    crop.Left = 0
                    crop.Top = max(2, (shell.Height - control.Height) // 2)
                    crop.Width = max(30, width - arrow.Width)
                    crop.Height = max(18, control.Height - 2)
                    control.Top = -1
                    control.Width = crop.Width + arrow.Width + 2
            shell.Resize += layout_input
            # Mask top/bottom native border without obstructing text or input.
            if arrow:
                for dock in ("Top", "Bottom"):
                    edge = self.panel(dock, 1)
                    edge.BackColor = self.color("SurfaceAlt")
                    shell.Controls.Add(edge)
            row.Controls.Add(shell)
        else:
            row.Controls.Add(control)
        row.Controls.Add(title)
        self.theme(row)
        if input_kind in ("ComboBox", "TextBox"):
            shell.BackColor = self.color("SurfaceAlt")
        return row

    def fit_stack(self, panel):
        def fit(sender=None, args=None):
            panel.Height = sum(c.Height for c in panel.Controls) + 12
        for control in panel.Controls:
            control.SizeChanged += fit
        fit()

    def preview(self, kind, caption="PRÉVIA ILUSTRATIVA"):
        holder = self.panel("Right")
        holder.Width = 288
        holder.Padding = self.ns["Padding"](16, 12, 12, 12)
        holder.BackColor = self.color("Background")
        canvas = self.panel()
        canvas.BackColor = self.color("Background")
        attach_preview(canvas, kind)
        holder._canvas = canvas
        context = self.panel("Bottom", 108)
        context.BackColor = self.color("Background")
        holder._strategy = self.label("", 30, True)
        holder._families = self.label("○ Famílias ainda não verificadas", 40)
        holder._families.ForeColor = self.color("TextSecondary")
        context.Controls.Add(holder._families)
        context.Controls.Add(holder._strategy)
        context.Controls.Add(self.label("ESTRATÉGIA", 28))
        separator(context, "top")
        def set_kind(value):
            canvas._set_kind(value)
            holder._strategy.Text = {"channel": "Canaletas", "none": "Sem reforço", "cad": "Paredes a partir do CAD",
                                     "selection": "Paredes existentes", "blocks": "Plano de blocos"}.get(value, value)
        holder._set_kind = set_kind
        set_kind(kind)
        holder.Controls.Add(canvas)
        holder.Controls.Add(context)
        note = self.label("ⓘ Geometria final calculada a partir do modelo.", 46)
        note.Font = self.ns["_ui_font"](TYPE["Caption"])
        note.ForeColor = self.color("TextSecondary")
        note.Dock = self.ns["DockStyle"].Bottom
        holder.Controls.Add(note)
        holder.Controls.Add(self.label(caption, 32, True))
        def fit_context(sender=None, args=None):
            height = holder.ClientSize.Height
            if isinstance(height, (int, float)) and height > 0:
                # Drawing gets priority. Never leave a tiny blank canvas between
                # fixed title/context/footer at the minimum window height.
                scale = self.display_scale(holder)
                context.Visible = height >= 350 * scale
                note.Visible = height >= 300 * scale
        holder.Resize += fit_context
        return holder

    def panel(self, dock="Fill", height=None):
        p = self.new("Panel")
        p.Dock = getattr(self.ns["DockStyle"], dock)
        p.BackColor = self.ns["UI_PANEL"]
        if height is not None:
            p.Height = height
        return p

    def label(self, text, height=44, bold=False):
        label = self.new("Label")
        label.Text = text
        label.Dock = self.ns["DockStyle"].Top
        label.Height = height
        label.Font = self.ns["_ui_font"](TYPE["Body"], bold)
        label.ForeColor = self.ns["UI_TEXT"]
        label.Padding = self.ns["Padding"](8, 6, 8, 4)
        return label

    def button(self, text, callback, primary=False):
        button = self.new("Button")
        button.Text = text
        button.Height = 36
        button.Width = 190
        button.Dock = self.ns["DockStyle"].Right
        self.ns["_style_primary_button" if primary else "_style_secondary_button"](button)
        button.Click += callback
        return button

    def header(self, step, instruction):
        header = self.panel("Top", 126)
        header.Padding = self.ns["Padding"](24, 8, 24, 0)
        title = self.label("Modulação Automática", 32, True)
        title.Padding = self.ns["Padding"](0)
        title.Font = self.ns["_ui_font"](TYPE["Title"], True)
        header._step_label = self.label("", 22)
        header._step_label.Padding = self.ns["Padding"](0)
        header._step_label.ForeColor = self.ns["UI_MUTED"]
        header._instruction = self.label(instruction, 28)
        header._instruction.Padding = self.ns["Padding"](0, 2, 0, 0)
        header._stepper = stepper(self)
        header.Controls.Add(header._stepper)
        header.Controls.Add(header._instruction)
        header.Controls.Add(header._step_label)
        header.Controls.Add(title)
        self.set_step(header, step, instruction)
        return header

    def set_step(self, header, step, instruction):
        header._step_label.Text = "Etapa {} de 6 · {}".format(step, STEPS[step - 1])
        header._step_label.AccessibleName = "Etapa {} de 6 — {}".format(step, STEPS[step - 1])
        header._instruction.Text = instruction
        header._stepper._set_step(step)

    def configure(self, form, width=860, height=640):
        form.Font = self.ns["_ui_font"](TYPE["Body"])
        form.BackColor = self.ns["UI_BG"]
        form.ForeColor = self.ns["UI_TEXT"]
        form.MaximizeBox = False
        form.KeyPreview = True
        def disabled_styles(sender, args):
            def walk(control):
                if type(control).__name__ == "Button":
                    style_disabled_button(control)
                for child in control.Controls:
                    walk(child)
            walk(form)
        form.Shown += disabled_styles
        form.MinimumSize = self.ns["Size"](740, 520)
        form.Width, form.Height = width, height
        # Design dimensions are logical pixels at 96 DPI. Do not change the
        # Revit process DPI mode; respect the host and scale this Form only.
        try:
            from System.Windows.Forms import AutoScaleMode, Screen
            from System.Drawing import SizeF
            form.AutoScaleDimensions = SizeF(96.0, 96.0)
            form.AutoScaleMode = AutoScaleMode(2)  # Dpi; same enum workaround as host.

            def fit(sender, args):
                area = Screen.FromControl(form).WorkingArea
                form.MinimumSize = self.ns["Size"](min(form.MinimumSize.Width, area.Width),
                                                    min(form.MinimumSize.Height, area.Height))
                form.Size = self.ns["Size"](min(form.Width, area.Width), min(form.Height, area.Height))
            form.Shown += fit
        except ImportError:
            # Offline tests use controls without a Windows display.
            pass

    def expandable(self, content, caption="Detalhes técnicos", expanded=False, height=240):
        holder = self.panel("Top", 32)
        toggle = self.new("Button")
        self.ns["_style_secondary_button"](toggle)
        toggle.Dock = self.ns["DockStyle"].Top
        toggle.Height = 32
        toggle.FlatAppearance.BorderSize = 0
        toggle.ForeColor = self.ns["UI_MUTED"]
        content.Dock = self.ns["DockStyle"].Fill
        holder._expanded = expanded
        holder._content = content
        holder._toggle = toggle

        def refresh():
            content.Visible = holder._expanded
            holder.Height = height if holder._expanded else 32
            toggle.Text = ("▾ " if holder._expanded else "▸ ") + caption
            toggle.AccessibleName = toggle.Text

        def clicked(sender, args):
            holder._expanded = not holder._expanded
            refresh()
        def set_expanded(value):
            holder._expanded = bool(value)
            refresh()
        holder._set_expanded = set_expanded
        toggle.Click += clicked
        holder.Controls.Add(content)
        holder.Controls.Add(toggle)
        refresh()
        return holder

    def metric_strip(self, items):
        strip = self.panel("Top", 46)
        strip._summary = self.label("  ·  ".join("{} {}".format(value, caption.lower())
                                               for caption, value, color in items), 44, True)
        strip.Controls.Add(strip._summary)
        return strip

    def setup(self, form, body, left, right, footer):
        self.configure(form)
        form.Text = "Modulação Automática — configuração"
        form._ux = self
        body.Controls.Clear()
        body.Padding = self.ns["Padding"](12, 0, 12, 0)
        deck = TabDeck(self, ("Projeto e CAD", "Aberturas e reforço"))
        form._setup_tabs = deck
        preview = self.preview("channel" if form._reinforcement_combo.SelectedIndex == 1 else "cad")
        form._setup_preview = preview
        body.Controls.Add(deck.panel)
        body.Controls.Add(preview)
        page, strategy_page = deck.pages
        settings = self.panel("Top", 450)
        page.Controls.Add(settings)
        document = self.ns.get("doc")
        title = getattr(document, "Title", "")
        project = self.label("Projeto: " + title if isinstance(title, str) and title else "Projeto atual do Revit", 28, True)
        dimensions = self.panel("Top", 60)
        level = self.field("Nível", form._level_combo)
        level.Dock = self.ns["DockStyle"].Fill
        height = self.field("Altura (m)", form._height_box)
        height.Dock = self.ns["DockStyle"].Right
        height.Width = 140
        dimensions.Controls.Add(level)
        dimensions.Controls.Add(height)
        advanced = self.panel()
        advanced.Controls.Add(self.field("Outras espessuras (cm, separadas por ;)", form._extra_box))
        settings.Controls.Add(self.expandable(advanced, "Opções avançadas", False, 102))
        settings.Controls.Add(self.field("Espessuras de parede", form._thickness_list, 64))
        settings.Controls.Add(self.field("Layer estrutural / referência (opcional)", form._reference_combo))
        settings.Controls.Add(self.field("Layer de paredes", form._layer_grid, 90))
        settings.Controls.Add(dimensions)
        settings.Controls.Add(project)
        self.fit_stack(settings)
        # Own parent for each RadioButton group; preserve remembered values.
        openings = self.panel("Top", 60)
        form._openings_auto.Text = "Detectar automaticamente"
        form._openings_pick.Text = "Selecionar no modelo"
        openings.Controls.Add(form._openings_pick)
        openings.Controls.Add(form._openings_auto)
        form._wall_mode_continuous.Text = "Paredes contínuas com recortes de abertura"
        form._wall_mode_segmented.Text = "Paredes segmentadas pelas aberturas"
        modes = self.panel()
        modes.Controls.Add(form._wall_mode_panel)
        strategy_settings = self.panel("Top", 340)
        strategy_page.Controls.Add(strategy_settings)
        strategy_settings.Controls.Add(self.expandable(modes, "Opções avançadas", False, 112))
        helper = self.label("", 70)
        helper.ForeColor = self.color("TextSecondary")
        strategy_settings.Controls.Add(helper)
        strategy_settings.Controls.Add(self.field("Reforço das aberturas", form._reinforcement_combo))
        strategy_settings.Controls.Add(self.label("REFORÇO", 32, True))
        strategy_settings.Controls.Add(openings)
        strategy_settings.Controls.Add(self.label("ABERTURAS", 32, True))
        self.fit_stack(strategy_settings)
        self.theme(settings)
        self.theme(strategy_settings)
        for combo in (form._level_combo, form._reference_combo, form._reinforcement_combo):
            style_input(combo)
        style_grid(form._layer_grid)
        def preview_changed(sender, args):
            preview._set_kind("channel" if form._reinforcement_combo.SelectedIndex == 1 else "none")
            helper.Text = ("Canaleta superior em portas e janelas.\nCanaleta inferior em janelas com peitoril."
                           if form._reinforcement_combo.SelectedIndex == 1 else
                           "Aberturas sem reforço por canaletas.\nAs demais regras de modulação são mantidas.")
        form._reinforcement_combo.SelectedIndexChanged += preview_changed
        preview_changed(None, None)
        def page_changed(index):
            if index == 0:
                preview._set_kind("cad")
            else:
                preview_changed(None, None)
        deck.changed.append(page_changed)
        page_changed(0)
        form._run_button.Text = "Criar paredes"
        form._run_button.Width = 170
        form.AcceptButton = form._run_button
        for control in footer.Controls:
            if type(control).__name__ == "Button" and control != form._run_button:
                form.CancelButton = control
        separator(footer, "top")
        form.Controls.Clear()
        form.Controls.Add(body)
        form.Controls.Add(footer)
        form.Controls.Add(self.header(1, "Configure as paredes e a estratégia antes de iniciar."))
        def resize(sender, args):
            width = body.ClientSize.Width
            if isinstance(width, (int, float)) and width > 0:
                scale = self.display_scale(form)
                preview.Visible = width >= 720 * scale
                preview.Width = max(int(220 * scale), min(int(288 * scale), int(width * .34)))
        body.Resize += resize
        def initial_focus(sender, args):
            form.ActiveControl = deck.buttons[0]
            page.AutoScrollPosition = self.ns["Point"](0, 0)
        form.Shown += initial_focus

    def source(self, form, body, footer):
        self.configure(form, 860, 570)
        form.Text = "Modulação Automática — origem das paredes"
        form._rb_existing.Text = "Usar paredes existentes"
        form._ok_btn.Text = "Continuar"
        form._ok_btn.Width = 160
        other_buttons = [c for c in footer.Controls if c != form._ok_btn]
        footer.Controls.Clear()
        for control in other_buttons:
            footer.Controls.Add(control)
        footer.Controls.Add(form._ok_btn)
        choices = self.panel()
        choices.AutoScroll = True
        choices.Padding = self.ns["Padding"](0, 0, 16, 0)
        stack = self.panel("Top", 270)
        merge = self.panel()
        merge.Controls.Add(self.label("Reconstrói paredes segmentadas e preserva os vazios existentes.", 56))
        merge.Controls.Add(form._rb_merge)
        form._rb_merge.Text = "Unir paredes existentes"
        stack.Controls.Add(self.expandable(merge, "Opções avançadas", False, 134))
        for radio, caption, description in reversed((
                (form._rb_cad, "Criar a partir do CAD", "Transforme as linhas da planta em paredes no nível escolhido."),
                (form._rb_existing, "Usar paredes existentes", "Selecione as paredes no Revit e confirme a seleção."))):
            section = self.panel("Top", 94)
            section.Padding = self.ns["Padding"](8, 8, 8, 8)
            radio.Text = caption
            radio.Height = 32
            radio.Font = self.ns["_ui_font"](10, True)
            helper = self.label(description, 42)
            helper.ForeColor = self.color("TextSecondary")
            helper.Padding = self.ns["Padding"](26, 0, 4, 0)
            section.Controls.Add(helper)
            section.Controls.Add(radio)
            separator(section)
            stack.Controls.Add(section)
        self.fit_stack(stack)
        choices.Controls.Add(stack)
        self.theme(choices)
        body.Controls.Clear()
        preview = self.preview("cad", "Como funciona")
        preview.Width = 250
        body.Controls.Add(choices)
        body.Controls.Add(preview)
        radios = (form._rb_cad, form._rb_existing, form._rb_merge)
        def update(chosen):
            # Native WinForms groups radios by direct parent; these choices
            # live in separate section panels. GroupName is not a WinForms API.
            if not chosen.Checked:
                return
            for radio in radios:
                if radio is not chosen:
                    radio.Checked = False
            preview._set_kind("cad" if form._rb_cad.Checked else "selection")
        for radio in radios:
            radio.CheckedChanged += lambda s, e, r=radio: update(r)
        form._source_preview = preview
        form.Controls.Clear()
        form.Controls.Add(body)
        form.Controls.Add(footer)
        form.Controls.Add(self.header(1, "Escolha como preparar as paredes desta modulação."))
        form.AcceptButton = form._ok_btn
        separator(footer, "top")
        for control in other_buttons:
            if type(control).__name__ == "Button":
                form.CancelButton = control

    def walls(self, form, report, body, start_bar, footer):
        self.configure(form, 860, 620)
        form.Text = "Modulação Automática — paredes"
        form._ux = self
        form._ui_header = self.header(2, "Confira as paredes no modelo. Depois, inicie a análise.")
        form._status_label.Text = "A seleção e a navegação continuam disponíveis no Revit."
        form._start_button.Text = "Analisar paredes"
        form._start_button.Dock = self.ns["DockStyle"].Right
        form._start_button.Width = 170
        start_controls = [c for c in start_bar.Controls if c != form._start_button]
        start_bar.Controls.Clear()
        for control in start_controls:
            start_bar.Controls.Add(control)
        start_bar.Controls.Add(form._start_button)
        form._skip_button.Text = "Continuar sem analisar"
        form._skip_button.Width = 190
        form._console.set_status("Aguardando análise das paredes")
        body.AutoScroll = True
        preview = self.preview("selection", "Paredes no modelo")
        preview.Width = 260
        body.Controls.Add(preview)
        form.Controls.Clear()
        form.Controls.Add(body)
        form.Controls.Add(start_bar)
        form.Controls.Add(footer)
        form.Controls.Add(self.metric_strip(report.get("kpis") or []))
        form.Controls.Add(form._ui_header)
        separator(start_bar, "top")

    def post(self, form, report, errors_panel, debug_row, review_row):
        self.configure(form)
        form._ux = self
        form._ui_state = ModulationUiState(3, form._handler.opening_reinforcement_strategy)
        form._ui_header = self.header(3, "Confira as pendências e calcule a modulação.")
        form.Text = "Modulação Automática — revisão e blocos"
        form._fix_button.Text = "Aplicar ajustes disponíveis"
        self.ns["_style_secondary_button"](form._fix_button)
        form._solve_console.set_status("Confira as paredes e selecione Analisar modulação")
        tabs = TabDeck(self, ("Paredes e famílias", "Plano de blocos", "Resultado"))
        form._ui_tabs = tabs
        pages = tabs.pages
        form._ui_pages = pages
        form._ui_analysis_skipped = bool(report.get("wall_analysis_skipped"))
        # Optional future presentation data, without generating adjustment plans.
        adjustments = report.get("automatic_adjustments")
        form._ui_adjustments = self.label("", 34)
        form._ui_adjustments.Visible = bool(adjustments)
        if adjustments:
            form._ui_adjustments.Text = "✓ {} ajuste(s) automático(s) informado(s).".format(len(adjustments))
        # Existing error grid, zoom, fix, pause and cancel callbacks preserved.
        errors_panel.Dock = self.ns["DockStyle"].Fill
        pages[0].Controls.Add(errors_panel)
        pages[0].Controls.Add(form._ui_adjustments)
        form._errors_status.Height = 40
        style_grid(form._errors_grid)
        family_box = self.ns["_monospace_textbox"]("")
        family_box.Font = self.ns["_ui_font"](9.5)
        family_box.WordWrap = True
        form._ui_families = family_box
        family_grid = self.ns["_styled_listview"]([("Estado", 86), ("Família", 170)])
        style_grid(family_grid)
        form._ui_family_grid = family_grid
        family_disclosure = self.expandable(family_grid, "Famílias e reforço", False, 190)
        pages[0].Controls.Add(family_disclosure)
        form._ui_technical_issues = self.ns["_monospace_textbox"]("")
        pages[0].Controls.Add(self.expandable(form._ui_technical_issues, "Detalhes técnicos das paredes", False, 160))

        plan = self.ns["_monospace_textbox"]("Analise a modulação para ver a quantidade de blocos por peça e por todas as fiadas.")
        plan.Font = self.ns["_ui_font"](10)
        plan.WordWrap = True
        form._ui_plan = plan
        plan.Dock = self.ns["DockStyle"].Fill
        plan.TabStop = False
        content = self.panel()
        pages[1].AutoScroll = False
        form._ui_piece_grid = self.ns["_styled_listview"]([("Peça", 200), ("Quantidade", 100)])
        style_grid(form._ui_piece_grid)
        piece_panel = self.panel()
        piece_panel.Controls.Add(form._ui_piece_grid)
        piece_panel.Controls.Add(self.expandable(plan, "Resumo e avisos", False, 180))
        content.Controls.Add(piece_panel)
        preview = self.preview("blocks", "Modulação de alvenaria")
        preview.Width = 270
        form._plan_preview = preview
        content.Controls.Add(preview)
        def fit_preview(sender, args):
            width, height = form.ClientSize.Width, form.ClientSize.Height
            if isinstance(width, (int, float)) and isinstance(height, (int, float)):
                scale = self.display_scale(form)
                preview.Visible = width >= 800 * scale and height >= 540 * scale
        form.SizeChanged += fit_preview
        form.Shown += fit_preview
        metrics = self.metric_strip([("Blocos planejados", "—", self.ns["UI_ACCENT"]),
                                     ("Paredes selecionadas", len(form._handler.walls_to_create), self.ns["UI_TEXT"]),
                                     ("Aberturas detectadas", len(form._handler.all_openings), self.ns["UI_TEXT"])])
        form._ui_plan_metrics = metrics
        content.Controls.Add(metrics)
        pages[1].Controls.Add(content)
        form._ui_banner = self.label("Aguardando análise.", 58, True)
        pages[1].Controls.Add(form._ui_banner)

        result = self.ns["_monospace_textbox"]("O resultado será exibido após a criação dos blocos.")
        result.WordWrap = True
        result.Font = self.ns["_ui_font"](10)
        result.TabStop = False
        form._ui_result = result
        result_disclosure = self.expandable(result, "Ver relatório completo", False, 340)
        pages[2].Controls.Add(result_disclosure)
        advanced = self.panel("Fill")
        for control in (form._delete_button, review_row, debug_row):
            advanced.Controls.Add(control)
        pages[2].Controls.Add(self.expandable(advanced, "Revisão visual e paredes de referência", False, 160))
        pages[2].Controls.Add(self.expandable(form._log_box, "Detalhes técnicos", False, 270))

        footer = self.panel("Bottom", 60)
        form._ui_footer = footer
        footer.Padding = self.ns["Padding"](14, 10, 14, 10)
        form._ui_busy_note = self.label("Operação em andamento. Acompanhe o progresso acima.", 36)
        form._ui_busy_note.Dock = self.ns["DockStyle"].Fill
        form._ui_busy_note.Visible = False
        footer.Controls.Add(form._ui_busy_note)
        close = self.button("Fechar", lambda s, e: form.Close())
        close.Width = 100
        form._ui_close = close
        copy = self.button("Copiar relatório", lambda s, e: self.ns["_copy_text_to_clipboard"](form._ui_result.Text))
        copy.Width = 155
        copy.Dock = self.ns["DockStyle"].Bottom
        pages[2].Controls.Add(copy)
        form._solve_button.Text = "Analisar modulação"
        form._create_button.Text = "Criar blocos no Revit"
        for control in (form._create_button, form._solve_button):
            control.Dock = self.ns["DockStyle"].Right
            control.Width = 220
        self.ns["_style_primary_button"](form._solve_button)
        footer.Controls.Add(close)
        footer.Controls.Add(form._solve_button)
        footer.Controls.Add(form._create_button)
        separator(footer, "top")
        form._create_button.Visible = False
        progress = self.expandable(form._solve_console.panel, "Atividade e progresso", False, 190)
        progress.Dock = self.ns["DockStyle"].Bottom
        form._ui_progress = progress
        form.Controls.Clear()
        form.Controls.Add(tabs.panel)
        form.Controls.Add(progress)
        form.Controls.Add(footer)
        form.Controls.Add(form._ui_header)
        form._footer_note.Text = "Relatório e logs disponíveis na aba Resultado e relatório."
        self.update_families(form)
        # Hold the original Python wrapper: retrieving Controls[index] may
        # produce a new pythonnet wrapper without our presentation attributes.
        form._ui_family_disclosure = family_disclosure
        family_grid.AccessibleName = "Famílias verificadas: disponíveis e ausentes"
        if form._handler.catalog_missing:
            form._ui_family_disclosure._set_expanded(True)
            self.set_step(form._ui_header, 3, "Faltam famílias. Carregue os tipos indicados abaixo e reabra a modulação.")
        # Give the result a scrollable content extent so expanding both
        # disclosures cannot reduce the report to zero height.
        result_content = self.panel("Top", 550)
        result_controls = list(pages[2].Controls)
        pages[2].Controls.Clear()
        for control in result_controls:
            result_content.Controls.Add(control)
        form._ui_result_notes = self.label("O resumo será exibido após a criação.", 64)
        result_content.Controls.Add(form._ui_result_notes)
        form._ui_result_counts = self.label("", 58, True)
        result_content.Controls.Add(form._ui_result_counts)
        form._ui_result_title = self.label("Resultado da modulação", 42, True)
        form._ui_result_title.Font = self.ns["_ui_font"](14, True)
        result_content.Controls.Add(form._ui_result_title)
        self.fit_stack(result_content)
        pages[2].Controls.Add(result_content)
        form.AcceptButton = form._solve_button
        review_row.Height = 48
        form._review_check.AutoSize = False
        form._review_check.Dock = self.ns["DockStyle"].Fill
        form._review_check.Text = "Conferi os blocos no Revit e concluí a revisão humana."
        self.theme(errors_panel)
        self.theme(advanced)
        self.refresh_issues(form)
        def reset_scroll(sender, args):
            for page in pages:
                page.AutoScrollPosition = self.ns["Point"](0, 0)
        form.Shown += reset_scroll

    def refresh_issues(self, form):
        rows = form._handler.error_rows or []
        pending = sum(not row.get("resolved") for row in rows)
        automatic = sum(bool(row.get("auto_fixable")) and not row.get("resolved") for row in rows)
        form._errors_status.Text = ("{} pendência(s) · {} ajuste(s) disponível(is). Clique para visualizar no Revit."
                                    .format(pending, automatic) if rows else
                                    "Nenhuma pendência de paredes informada nesta etapa.")
        if form._ui_analysis_skipped:
            form._errors_status.Text = "Análise das paredes não executada. Confira o modelo antes de calcular."
        form._ui_technical_issues.Text = "\r\n".join("{} — {}".format(wall_label(row), row.get("problem_text", "")) for row in rows)

    def update_families(self, form):
        handler = form._handler
        catalog = dict(handler.catalog or {})
        catalog.update(handler.channel_catalog or {})
        missing = list(handler.catalog_missing or []) + list(handler.channel_catalog_missing or [])
        lines = ["Reforço: " + ("Canaletas (CHANNEL)" if handler.opening_reinforcement_strategy == "CHANNEL" else "Sem reforço")]
        rows = family_rows(catalog, missing)
        lines.extend("{} — {}: {}".format(*row) for row in rows)
        form._ui_family_grid.Items.Clear()
        for status, name, detail in rows:
            row = self.ns["ListViewItem"]("✓ Pronta" if status == "OK" else "✕ Ausente")
            row.SubItems.Add(name)
            row.ToolTipText = detail
            row.ForeColor = self.color("Success" if status == "OK" else "Danger")
            form._ui_family_grid.Items.Add(row)
        form._ui_family_grid.ShowItemToolTips = True
        if handler.opening_reinforcement_strategy == "CHANNEL" and not handler.channel_catalog and not handler.channel_catalog_missing:
            lines.append("Canaletas: verificação pendente. O backend confere as famílias antes do cálculo.")
        if missing:
            lines.append("Carregue as famílias indicadas em Inserir > Carregar família e reabra a modulação.")
        form._ui_families.Text = "\r\n".join(lines)
        if hasattr(form, "_plan_preview"):
            form._plan_preview._families.Text = ("✕ {} família(s) ausente(s)".format(len(missing)) if missing else
                "✓ {} família(s) disponível(is)".format(len(catalog)) if catalog else "○ Famílias ainda não verificadas")

    def existing_setup(self, wall_count, level_name, height_m, opening_count):
        form = self.new("Form")
        form.Text = "Modulação Automática — paredes existentes"
        self.configure(form, 860, 580)
        form.StartPosition = self.ns["FORM_START_POSITION_CENTER_SCREEN"]
        form.result = None
        body = self.panel()
        combo = self.new("ComboBox")
        combo.DropDownStyle = self.ns["ComboBoxStyle"].DropDownList
        combo.Dock = self.ns["DockStyle"].Top
        combo.Items.Add("Sem reforço")
        combo.Items.Add("Canaletas (CHANNEL)")
        combo.SelectedIndex = 0
        style_input(combo)
        body.Controls.Add(self.label("As famílias de canaleta serão conferidas antes do cálculo. Verga / contraverga: em desenvolvimento.", 70))
        body.Controls.Add(combo)
        self.theme(combo)
        body.Controls.Add(self.label("Reforço das aberturas", 38, True))
        body.Controls.Add(self.label("{} paredes selecionadas · {} aberturas detectadas\nNível: {} · Altura: {:.2f} m\nNível e altura foram lidos das paredes selecionadas.".format(
            wall_count, opening_count, level_name, height_m), 100))
        footer = self.panel("Bottom", 64)
        def accept(sender, args):
            form.result = "CHANNEL" if combo.SelectedIndex == 1 else "NONE"
            form.Close()
        footer.Controls.Add(self.button("Cancelar", lambda s, e: form.Close()))
        footer.Controls.Add(self.button("Revisar paredes", accept, True))
        preview = self.preview("none")
        body.Controls.Add(preview)
        combo.SelectedIndexChanged += lambda s, e: preview._set_kind("channel" if combo.SelectedIndex == 1 else "none")
        form.Controls.Add(body)
        form.Controls.Add(footer)
        form.Controls.Add(self.header(1, "Confira a seleção e escolha a estratégia de reforço desta execução."))
        form.ShowDialog()
        return form.result

    def busy(self, form, step):
        form._ui_state.start(step)
        message = "Criando blocos no Revit…" if step == 5 else "Calculando modulação…"
        self.set_step(form._ui_header, step, message)
        form._ui_banner.Text = message
        form._ui_banner.ForeColor = self.ns["UI_MUTED"]
        form._ui_tabs.SelectedIndex = 1
        form._ui_tabs.bar.Enabled = False
        form._ui_tabs.panel.Visible = False
        form._ui_progress.Dock = self.ns["DockStyle"].Fill
        form._ui_progress.Padding = self.ns["Padding"](24, 16, 24, 16)
        form._ui_busy_note.Visible = True
        for control in (form._ui_close, form._solve_button, form._create_button):
            control.Visible = False
        form._plan_preview.Visible = False
        form._ui_piece_grid.Visible = step == 5
        form._ui_plan_metrics.Visible = step == 5
        form._ui_close.Enabled = False
        form._ui_progress._set_expanded(True)
        form.ControlBox = False
        form._fix_button.Enabled = False
        for control in (form._errors_grid, form._delete_button, form._review_check,
                        form._debug_color_check, form._debug_filter_both,
                        form._debug_filter_a, form._debug_filter_b):
            control.Enabled = False
        form._create_button.Enabled = False
        form._solve_button.Enabled = False

    def end_busy_view(self, form):
        form._ui_tabs.panel.Visible = True
        form._ui_progress.Dock = self.ns["DockStyle"].Bottom
        form._ui_progress.Padding = self.ns["Padding"](0)
        form._ui_busy_note.Visible = False
        form._ui_close.Visible = True
        form._solve_button.Visible = True

    def solved(self, form):
        self.end_busy_view(form)
        h = form._handler
        state = form._ui_state
        state.solved(h.solve_result, h.catalog_missing, h.channel_catalog_missing)
        form._ui_tabs.bar.Enabled = True
        form._ui_piece_grid.Visible = True
        form._ui_plan_metrics.Visible = True
        width, height = form.ClientSize.Width, form.ClientSize.Height
        if isinstance(width, (int, float)) and isinstance(height, (int, float)):
            scale = self.display_scale(form)
            form._plan_preview.Visible = width >= 800 * scale and height >= 540 * scale
        self.update_families(form)
        form._ui_plan.Text = state.report_text(h).replace("\n", "\r\n")
        form._ui_plan.SelectionStart = 0
        form._ui_plan.SelectionLength = 0
        form._ui_piece_grid.Items.Clear()
        for code, count in sorted((state.counts or {}).items()):
            row = self.ns["ListViewItem"](code.replace("CHANNEL_U_", "Canaleta ").replace("CHANNEL_", "Canaleta "))
            row.SubItems.Add(str(count))
            form._ui_piece_grid.Items.Add(row)
        total = sum(state.counts.values()) if state.counts is not None else "—"
        form._ui_plan_metrics._summary.Text = "{} paredes · {} aberturas · {} blocos planejados".format(
            len(h.walls_to_create or []), len(h.all_openings or []), total)
        form._ui_banner.Text = "Modulação pronta. " + state.reason if state.can_create else state.reason
        form._ui_banner.ForeColor = self.ns["UI_OK" if state.can_create else "UI_ERROR"]
        form._create_button.Enabled = state.can_create
        self.ns["_style_secondary_button"](form._solve_button)
        self.ns["_style_primary_button"](form._create_button)
        self.ns["_set_button_enabled"](form._create_button, state.can_create)
        form._create_button.Visible = True
        form._solve_button.Visible = True
        self.ns["_style_secondary_button"](form._ui_close)
        previous = (h.create_result or {}).get("created_count")
        form._create_button.Text = "Atualizar modulação" if previous else "Criar blocos no Revit"
        if previous:
            form._ui_banner.Text = "Modulação existente: {} blocos. O lote anterior será substituído.".format(previous)
        form._solve_button.Text = "Reanalisar modulação"
        form._ui_close.Enabled = True
        form._ui_progress._set_expanded(False)
        form.ControlBox = True
        form._ui_tabs.SelectedIndex = 1
        form.AcceptButton = form._create_button
        form._create_button.Focus()
        self.set_step(form._ui_header, 4, state.reason)
        form._ui_pages[1].AutoScrollPosition = self.ns["Point"](0, 0)
        form._errors_grid.Enabled = True
        self.refresh_issues(form)
        form._review_check.Enabled = True
        # A new plan still needs creation and human review before deletion.
        form._review_check.Checked = False
        form._delete_button.Enabled = False

    def failed(self, form, detail):
        self.end_busy_view(form)
        form._ui_state.failed(detail)
        form._ui_tabs.bar.Enabled = True
        self.update_families(form)
        form._ui_banner.Text = "! " + form._ui_state.reason
        form._ui_banner.ForeColor = self.ns["UI_ERROR"]
        form._ui_plan.Text = form._ui_state.reason + "\r\n\r\nConsulte Revisão e famílias ou Detalhes da execução."
        form._append_log(str(detail))
        form._create_button.Enabled = False
        form._ui_close.Enabled = True
        form.ControlBox = True
        form._ui_tabs.SelectedIndex = 1
        self.set_step(form._ui_header, form._ui_state.step, form._ui_state.reason)
        form._errors_grid.Enabled = True

    def completed(self, form):
        self.end_busy_view(form)
        state, h = form._ui_state, form._handler
        form._ui_tabs.bar.Enabled = True
        state.completed(h.create_result or {})
        if state.status == "success" and any(not r.get("resolved") for r in h.error_rows or []):
            state.status = "warning"
        text = {"success": "✓ Modulação concluída. Confira os blocos no Revit.",
                "warning": "! Criação concluída com pendências. Revise o relatório.",
                "error": "! A criação não foi concluída. Consulte as falhas no relatório."}[state.status]
        form._ui_result.Text = (text + "\n\n" + state.report_text(h, h.create_result)).replace("\n", "\r\n")
        form._ui_result.Text += "\r\n" + form._solve_console._elapsed_label.Text
        created = h.create_result or {}
        form._ui_result_title.Text = {"success": "✓ Modulação concluída", "warning": "! Concluída com pendências",
                                      "error": "✕ Criação não concluída"}[state.status]
        form._ui_result_title.ForeColor = self.ns["UI_OK" if state.status == "success" else "UI_WARN" if state.status == "warning" else "UI_ERROR"]
        form._ui_result_counts.Text = "{} blocos criados · {} paredes · {} aberturas\n{} falha(s) de criação".format(
            created.get("created_count", 0), len(h.walls_to_create or []), len(h.all_openings or []), len(created.get("failures") or []))
        pending = sum(not row.get("resolved") for row in h.error_rows or [])
        form._ui_result_notes.Text = "{} parede(s) ainda requer(em) revisão.\n{}\nConfira o modelo e consulte o relatório antes de concluir.".format(
            pending, form._solve_console._elapsed_label.Text)
        form._ui_tabs.SelectedIndex = 2
        form._ui_close.Enabled = True
        form._ui_progress._set_expanded(False)
        form.ControlBox = True
        form._create_button.Text = "Atualizar modulação"
        form._create_button.Visible = True
        form._solve_button.Visible = False
        self.ns["_style_secondary_button"](form._create_button)
        self.ns["_style_primary_button"](form._ui_close)
        form._ui_footer.Controls.Clear()
        form._ui_footer.Controls.Add(form._create_button)
        form._ui_footer.Controls.Add(form._solve_button)
        form._ui_footer.Controls.Add(form._ui_close)
        form.AcceptButton = form._ui_close
        form._ui_close.Focus()
        self.set_step(form._ui_header, 6, text)
        form._ui_pages[2].AutoScrollPosition = self.ns["Point"](0, 0)
        form._errors_grid.Enabled = True
        form._review_check.Enabled = True
        form._update_delete_enabled()

    def selection_prompt(self, count):
        """Modal preparation only; actual picking remains native Revit."""
        form = self.new("Form")
        form.Text = "Modulação Automática — seleção de paredes"
        self.configure(form, 860, 550)
        form.StartPosition = self.ns["FORM_START_POSITION_CENTER_SCREEN"]
        form.result = None
        form.Controls.Add(self.label(
            "1. Clique em Selecionar no Revit.\n2. Selecione as paredes e clique em Concluir na barra do Revit.\n"
            "3. As aberturas serão detectadas automaticamente.\n4. Confira as paredes e inicie a análise.\n\n"
            "Esc durante a seleção cancela esta operação.", 180))
        footer = self.panel("Bottom", 64)
        def choose(value):
            form.result = value
            form.Close()
        footer.Controls.Add(self.button("Cancelar", lambda s, e: choose(None)))
        footer.Controls.Add(self.button("Selecionar no Revit", lambda s, e: choose("pick"), not count))
        if count:
            footer.Controls.Add(self.button("Confirmar {} parede(s)".format(count), lambda s, e: choose("current"), True))
        form.Controls.Add(footer)
        form.Controls.Add(self.header(2, "Confirme a seleção atual ou selecione as paredes no modelo."))
        form.ShowDialog()
        return form.result
