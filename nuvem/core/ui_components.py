# -*- coding: utf-8 -*-
"""Reusable WinForms presentation. API calls and execution stay with the host.

The small namespace adapter reuses the host's pythonnet enum compatibility
layer. It does not introduce another event loop, thread or framework.
"""
from .ui_state import STEPS, TYPE, TOKENS, ModulationUiState, family_rows, wall_label
from .ui_preview_panel import attach_preview
from .ui_native_style import style_input, style_grid, style_disabled_button


class TabDeck(object):
    """Native keyboard-focusable buttons and panels, without light OS tab chrome."""
    def __init__(self, ui, captions):
        self.panel = ui.panel()
        self.bar = ui.panel("Top", 40)
        self.pages, self.buttons = [], []
        self._selected = 0
        for index, caption in enumerate(captions):
            page = ui.panel()
            page.AutoScroll = True
            page.Padding = ui.ns["Padding"](12)
            self.pages.append(page)
            self.panel.Controls.Add(page)
            button = ui.button(caption, lambda s, e, i=index: setattr(self, "SelectedIndex", i))
            button.Dock = ui.ns["DockStyle"].Left
            button.Width = max(140, len(caption) * 7 + 24)
            button.Height = 36
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
            button.BackColor = self.ui.color("SurfaceAlt" if i == value else "Background")
            button.ForeColor = self.ui.color("TextPrimary" if i == value else "TextSecondary")
            button.FlatAppearance.BorderColor = self.ui.color("Primary" if i == value else "Background")
            button.AccessibleName = button.Text + (" — selecionada" if i == value else "")


class UiComponents(object):
    def __init__(self, ns):
        self.ns = dict(ns)

    def new(self, name):
        return self.ns[name]()

    def color(self, name):
        return self.ns["Color"].FromArgb(*TOKENS[name])

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
        for child in control.Controls:
            # Button colors encode action hierarchy; keep them.
            if type(child).__name__ != "Button":
                self.theme(child)

    def field(self, caption, control, height=58):
        row = self.panel("Top", height)
        row.Padding = self.ns["Padding"](0, 0, 8, 8)
        control.Dock = self.ns["DockStyle"].Top
        control.Height = height - 30
        control.AccessibleName = caption
        title = self.label(caption, 24)
        title.Padding = self.ns["Padding"](0, 2, 0, 2)
        row.Controls.Add(control)
        row.Controls.Add(title)
        self.theme(row)
        return row

    def fit_stack(self, panel):
        def fit(sender=None, args=None):
            panel.Height = sum(c.Height for c in panel.Controls) + 12
        for control in panel.Controls:
            control.SizeChanged += fit
        fit()

    def preview(self, kind, caption="Prévia da estratégia"):
        holder = self.panel("Right")
        holder.Width = 280
        holder.Padding = self.ns["Padding"](16, 12, 12, 12)
        canvas = self.panel()
        attach_preview(canvas, kind)
        holder._canvas = canvas
        holder._set_kind = canvas._set_kind
        holder.Controls.Add(canvas)
        holder.Controls.Add(self.label("Esquema ilustrativo · sem escala\nNão representa o plano calculado.", 48))
        holder.Controls[1].Dock = self.ns["DockStyle"].Bottom
        holder.Controls.Add(self.label(caption, 32, True))
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
        header = self.panel("Top", 108)
        header.Padding = self.ns["Padding"](16, 4, 16, 4)
        title = self.label("Modulação Automática", 36, True)
        title.Font = self.ns["_ui_font"](TYPE["Title"], True)
        header._step_label = self.label("", 28)
        header._step_label.ForeColor = self.ns["UI_MUTED"]
        header._instruction = self.label(instruction, 36)
        header.Controls.Add(header._instruction)
        header.Controls.Add(header._step_label)
        header.Controls.Add(title)
        self.set_step(header, step, instruction)
        return header

    def set_step(self, header, step, instruction):
        header._step_label.Text = "{}  /  6    {}".format(step, STEPS[step - 1])
        header._step_label.AccessibleName = "Etapa {} de 6 — {}".format(step, STEPS[step - 1])
        header._instruction.Text = instruction

    def configure(self, form, width=940, height=680):
        form.Font = self.ns["_ui_font"](TYPE["Body"])
        form.BackColor = self.ns["UI_BG"]
        form.ForeColor = self.ns["UI_TEXT"]
        form.MaximizeBox = False
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
        body.Padding = self.ns["Padding"](12)
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
        project = self.label("Projeto: " + title if isinstance(title, str) and title else "Projeto atual do Revit", 34, True)
        dimensions = self.panel("Top", 58)
        level = self.field("Nível", form._level_combo)
        level.Dock = self.ns["DockStyle"].Fill
        height = self.field("Altura (m)", form._height_box)
        height.Dock = self.ns["DockStyle"].Right
        height.Width = 140
        dimensions.Controls.Add(level)
        dimensions.Controls.Add(height)
        advanced = self.panel()
        advanced.Controls.Add(self.field("Outras espessuras (cm, separadas por ;)", form._extra_box))
        settings.Controls.Add(self.expandable(advanced, "Espessuras adicionais", False, 102))
        settings.Controls.Add(self.field("Espessuras a modelar", form._thickness_list, 96))
        settings.Controls.Add(self.field("Layer estrutural / referência (opcional)", form._reference_combo))
        settings.Controls.Add(self.field("Layer de paredes", form._layer_grid, 150))
        settings.Controls.Add(dimensions)
        settings.Controls.Add(project)
        self.fit_stack(settings)
        # Own parent for each RadioButton group; preserve remembered values.
        openings = self.panel("Top", 60)
        form._openings_auto.Text = "Detectar portas e janelas automaticamente"
        form._openings_pick.Text = "Selecionar portas e janelas no modelo"
        openings.Controls.Add(form._openings_pick)
        openings.Controls.Add(form._openings_auto)
        form._wall_mode_continuous.Text = "Paredes contínuas com recortes de abertura"
        form._wall_mode_segmented.Text = "Paredes segmentadas pelas aberturas"
        modes = self.panel()
        modes.Controls.Add(form._wall_mode_panel)
        strategy_settings = self.panel("Top", 340)
        strategy_page.Controls.Add(strategy_settings)
        strategy_settings.Controls.Add(self.expandable(modes, "Modo avançado: paredes de referência", False, 112))
        strategy_settings.Controls.Add(self.label("As famílias necessárias serão conferidas antes do cálculo.", 48))
        strategy_settings.Controls.Add(self.field("Reforço das aberturas", form._reinforcement_combo))
        strategy_settings.Controls.Add(openings)
        strategy_settings.Controls.Add(self.label("Aberturas", 32, True))
        self.fit_stack(strategy_settings)
        self.theme(settings)
        self.theme(strategy_settings)
        for combo in (form._level_combo, form._reference_combo, form._reinforcement_combo):
            style_input(combo)
        style_grid(form._layer_grid)
        def preview_changed(sender, args):
            preview._set_kind("channel" if form._reinforcement_combo.SelectedIndex == 1 else "none")
        form._reinforcement_combo.SelectedIndexChanged += preview_changed
        form._run_button.Text = "Criar paredes"
        form._run_button.Width = 170
        form.AcceptButton = form._run_button
        form.Controls.Clear()
        form.Controls.Add(body)
        form.Controls.Add(footer)
        form.Controls.Add(self.header(1, "Configure as paredes e confira a estratégia antes de criar."))
        def resize(sender, args):
            width = body.ClientSize.Width
            if isinstance(width, (int, float)) and width > 0:
                preview.Width = max(190, min(280, int(width * .31)))
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
        for control in list(body.Controls):
            choices.Controls.Add(control)
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

    def walls(self, form, report, body, start_bar, footer):
        self.configure(form, 940, 620)
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

    def post(self, form, report, errors_panel, debug_row, review_row):
        self.configure(form)
        form._ux = self
        form._ui_state = ModulationUiState(3, form._handler.opening_reinforcement_strategy)
        form._ui_header = self.header(3, "Confira as pendências e calcule a modulação. Clique na lista para visualizar no Revit.")
        form.Text = "Modulação Automática — revisão e blocos"
        form._fix_button.Text = "Aplicar ajustes disponíveis"
        self.ns["_style_secondary_button"](form._fix_button)
        form._solve_console.set_status("Confira as paredes e selecione Analisar modulação")
        tabs = TabDeck(self, ("Paredes e famílias", "Plano de blocos", "Resultado"))
        form._ui_tabs = tabs
        pages = tabs.pages
        form._ui_pages = pages
        form._ui_analysis_skipped = bool(report.get("wall_analysis_skipped"))
        # Existing error grid, zoom, fix, pause and cancel callbacks preserved.
        errors_panel.Dock = self.ns["DockStyle"].Fill
        pages[0].Controls.Add(errors_panel)
        form._errors_status.Height = 40
        style_grid(form._errors_grid)
        family_box = self.ns["_monospace_textbox"]("")
        family_box.Font = self.ns["_ui_font"](9.5)
        family_box.WordWrap = True
        form._ui_families = family_box
        family_disclosure = self.expandable(family_box, "Famílias e reforço", False, 200)
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
                preview.Visible = width >= 800 and height >= 540
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
        close = self.button("Fechar", lambda s, e: form.Close())
        close.Width = 100
        form._ui_close = close
        copy = self.button("Copiar relatório", lambda s, e: self.ns["_copy_text_to_clipboard"](form._ui_result.Text))
        copy.Width = 155
        copy.Dock = self.ns["DockStyle"].Bottom
        pages[2].Controls.Add(copy)
        form._solve_button.Text = "Analisar modulação"
        form._create_button.Text = "CRIAR BLOCOS NO REVIT"
        for control in (form._create_button, form._solve_button):
            control.Dock = self.ns["DockStyle"].Right
            control.Width = 220
        self.ns["_style_primary_button"](form._solve_button)
        footer.Controls.Add(close)
        footer.Controls.Add(form._solve_button)
        footer.Controls.Add(form._create_button)
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
        lines.extend("{} — {}: {}".format(*row) for row in family_rows(catalog, missing))
        if handler.opening_reinforcement_strategy == "CHANNEL" and not handler.channel_catalog and not handler.channel_catalog_missing:
            lines.append("Canaletas: verificação pendente. O backend confere as famílias antes do cálculo.")
        if missing:
            lines.append("Carregue as famílias indicadas em Inserir > Carregar família e reabra a modulação.")
        form._ui_families.Text = "\r\n".join(lines)

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
        form._plan_preview.Visible = False
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

    def solved(self, form):
        h = form._handler
        state = form._ui_state
        state.solved(h.solve_result, h.catalog_missing, h.channel_catalog_missing)
        form._ui_tabs.bar.Enabled = True
        width, height = form.ClientSize.Width, form.ClientSize.Height
        if isinstance(width, (int, float)) and isinstance(height, (int, float)):
            form._plan_preview.Visible = width >= 800 and height >= 540
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
        form._create_button.Text = "Atualizar modulação" if previous else "CRIAR BLOCOS NO REVIT"
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
        form._ui_result_title.Text = {"success": "Modulação concluída", "warning": "Concluída com pendências",
                                      "error": "Criação não concluída"}[state.status]
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
