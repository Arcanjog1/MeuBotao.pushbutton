# -*- coding: utf-8 -*-
"""Reusable WinForms presentation. API calls and execution stay with the host.

The small namespace adapter reuses the host's pythonnet enum compatibility
layer. It does not introduce another event loop, thread or framework.
"""
from .ui_state import STEPS, ModulationUiState, family_rows, wall_label


class UiComponents(object):
    def __init__(self, ns):
        self.ns = dict(ns)

    def new(self, name):
        return self.ns[name]()

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
        label.Font = self.ns["_ui_font"](9.5, bold)
        label.ForeColor = self.ns["UI_TEXT"]
        label.Padding = self.ns["Padding"](8, 6, 8, 4)
        return label

    def button(self, text, callback, primary=False):
        button = self.new("Button")
        button.Text = text
        button.Height = 42
        button.Width = 230
        button.Dock = self.ns["DockStyle"].Right
        self.ns["_style_primary_button" if primary else "_style_secondary_button"](button)
        button.Click += callback
        return button

    def header(self, step, instruction):
        header = self.panel("Top", 132)
        header.Padding = self.ns["Padding"](16, 8, 16, 8)
        title = self.label("MODULAÇÃO AUTOMÁTICA", 34, True)
        header._step_label = self.label("", 30, True)
        header._instruction = self.label(instruction, 44)
        header.Controls.Add(header._instruction)
        header.Controls.Add(header._step_label)
        header.Controls.Add(title)
        self.set_step(header, step, instruction)
        return header

    def set_step(self, header, step, instruction):
        header._step_label.Text = "  ·  ".join(
            ("[{} {}]" if i == step else "{} {}").format(i, name)
            for i, name in enumerate(STEPS, 1))
        header._step_label.AccessibleName = "Etapa {} de 6 — {}".format(step, STEPS[step - 1])
        header._instruction.Text = "Etapa {} de 6 — {}. {}".format(step, STEPS[step - 1], instruction)

    def configure(self, form, width=1060, height=780):
        form.Font = self.ns["_ui_font"](9.5)
        form.Width, form.Height = width, height
        form.MinimumSize = self.ns["Size"](740, 520)
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

    def expandable(self, content, caption="Detalhes da execução", expanded=False, height=240):
        holder = self.panel("Top", 36)
        toggle = self.new("Button")
        self.ns["_style_secondary_button"](toggle)
        toggle.Dock = self.ns["DockStyle"].Top
        toggle.Height = 36
        content.Dock = self.ns["DockStyle"].Fill
        holder._expanded = expanded
        holder._content = content
        holder._toggle = toggle

        def refresh():
            content.Visible = holder._expanded
            holder.Height = height if holder._expanded else 36
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
        strip = self.panel("Top", 84)
        strip.AutoScroll = True
        for caption, value, color in reversed(items):
            card, spacer = self.ns["_build_card"](caption, value, color)
            strip.Controls.Add(spacer)
            strip.Controls.Add(card)
        return strip

    def setup(self, form, body, left, right, footer):
        self.configure(form)
        right.AutoScroll = True
        settings = self.panel("Top")
        controls = list(right.Controls)
        settings.Height = sum(c.Height for c in controls) + 32
        right.Controls.Clear()
        for control in controls:
            settings.Controls.Add(control)
        right.Controls.Add(settings)
        # Keep the controls' existing order/defaults and validation handlers.
        # Scrolling is local to the configuration pane; footer remains fixed.
        form._run_button.Text = "Criar paredes"
        form._run_button.Width = 180
        form.AcceptButton = form._run_button
        form.Controls.Clear()
        form.Controls.Add(body)
        form.Controls.Add(footer)
        form.Controls.Add(self.header(1, "Escolha layers, espessuras, nível e altura. Depois, crie as paredes."))
        document = self.ns.get("doc")
        title = getattr(document, "Title", "")
        if isinstance(title, str) and title:
            left.Controls.Add(self.label("Projeto: " + title, 48, True))

        def resize(sender, args):
            width = getattr(body, "Width", 0)
            if isinstance(width, (int, float)) and width > 0:
                left.Width = max(250, int(width * .38))
        body.Resize += resize
        form._ux = self
        def initial_focus(sender, args):
            form.ActiveControl = form._layer_grid
            right.AutoScrollPosition = self.ns["Point"](0, 0)
        form.Shown += initial_focus
        form._openings_auto.Text = "Detectar portas e janelas automaticamente"
        form._openings_pick.Text = "Selecionar portas e janelas no modelo"
        form._wall_mode_continuous.Text = "Paredes contínuas com recortes de abertura"
        form._wall_mode_segmented.Text = "Paredes segmentadas pelas aberturas"

    def source(self, form, body, footer):
        self.configure(form, 940, 740)
        body.AutoScroll = True
        form._rb_existing.Text = "Usar paredes existentes"
        form._ok_btn.Text = "Continuar"
        form._ok_btn.Width = 200
        form.Controls.Clear()
        form.Controls.Add(body)
        form.Controls.Add(footer)
        form.Controls.Add(self.header(1, "Escolha a fonte das paredes. A próxima tela orienta a seleção no Revit."))
        form.AcceptButton = form._ok_btn

    def walls(self, form, report, body, start_bar, footer):
        self.configure(form)
        form._ux = self
        form._ui_header = self.header(2, "Confira as paredes no modelo. Analise para identificar ajustes e seguir à revisão.")
        form._status_label.Text = "Selecione Analisar paredes quando terminar a conferência no Revit."
        form._start_button.Text = "Analisar paredes"
        form._skip_button.Text = "Usar paredes atuais e continuar"
        form._skip_button.Width = 275
        form._console.set_status("Aguardando análise das paredes")
        body.AutoScroll = True
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
        form._ui_header = self.header(3, "Revise os problemas. Selecionar uma parede na lista mostra o elemento no Revit.")
        form.Text = "Modulação Automática — revisão e blocos"
        form._fix_button.Text = "Aplicar ajustes disponíveis"
        self.ns["_style_secondary_button"](form._fix_button)
        form._solve_console.set_status("Confira as paredes e selecione Analisar modulação")
        tabs = self.new("TabControl")
        tabs.Dock = self.ns["DockStyle"].Fill
        form._ui_tabs = tabs
        pages = []
        for caption in ("Revisão e famílias", "Plano de blocos", "Resultado e relatório"):
            page = self.ns["TabPage"](caption)
            page.AutoScroll = True
            page.Padding = self.ns["Padding"](14)
            tabs.TabPages.Add(page)
            pages.append(page)
        form._ui_pages = pages
        # Existing error grid, zoom, fix, pause and cancel callbacks preserved.
        errors_panel.Dock = self.ns["DockStyle"].Fill
        pages[0].Controls.Add(errors_panel)
        family_box = self.ns["_monospace_textbox"]("")
        family_box.Font = self.ns["_ui_font"](9.5)
        family_box.WordWrap = True
        form._ui_families = family_box
        pages[0].Controls.Add(self.expandable(family_box, "Famílias e reforço", False, 200))

        plan = self.ns["_monospace_textbox"]("Analise a modulação para ver a quantidade de blocos por peça e por todas as fiadas.")
        plan.Font = self.ns["_ui_font"](10)
        plan.WordWrap = True
        form._ui_plan = plan
        plan.Dock = self.ns["DockStyle"].Bottom
        plan.Height = 125
        plan.TabStop = False
        content = self.panel("Top", 430)
        form._ui_piece_grid = self.ns["_styled_listview"]([("Peça", 400), ("Quantidade planejada", 190)])
        content.Controls.Add(form._ui_piece_grid)
        content.Controls.Add(plan)
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
        pages[2].Controls.Add(result)
        advanced = self.panel("Fill")
        for control in (form._delete_button, review_row, debug_row):
            advanced.Controls.Add(control)
        pages[2].Controls.Add(self.expandable(advanced, "Revisão visual e paredes de referência", False, 160))
        pages[2].Controls.Add(self.expandable(form._log_box, "Detalhes da execução e diagnóstico", False, 270))

        footer = self.panel("Bottom", 62)
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
            control.Width = 245
        self.ns["_style_primary_button"](form._solve_button)
        footer.Controls.Add(close)
        footer.Controls.Add(form._solve_button)
        footer.Controls.Add(form._create_button)
        form._create_button.Visible = False
        progress = self.expandable(form._solve_console.panel, "Progresso, tempo e detalhes", False, 180)
        progress.Dock = self.ns["DockStyle"].Bottom
        form._ui_progress = progress
        form.Controls.Clear()
        form.Controls.Add(tabs)
        form.Controls.Add(progress)
        form.Controls.Add(footer)
        form.Controls.Add(form._ui_header)
        form._footer_note.Text = "Relatório e logs disponíveis na aba Resultado e relatório."
        self.update_families(form)
        form._ui_family_disclosure = pages[0].Controls[1]
        if form._handler.catalog_missing:
            form._ui_family_disclosure._set_expanded(True)
            self.set_step(form._ui_header, 3, "Faltam famílias. Carregue os tipos indicados abaixo e reabra a modulação.")
        # Give the result a scrollable content extent so expanding both
        # disclosures cannot reduce the report to zero height.
        result_content = self.panel("Top", 720)
        result_controls = list(pages[2].Controls)
        pages[2].Controls.Clear()
        for control in result_controls:
            result_content.Controls.Add(control)
        pages[2].Controls.Add(result_content)
        form.AcceptButton = form._solve_button
        review_row.Height = 48
        form._review_check.AutoSize = False
        form._review_check.Dock = self.ns["DockStyle"].Fill
        form._review_check.Text = "Conferi os blocos no Revit e concluí a revisão humana."

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
        self.configure(form, 940, 580)
        form.StartPosition = self.ns["FORM_START_POSITION_CENTER_SCREEN"]
        form.result = None
        body = self.panel()
        combo = self.new("ComboBox")
        combo.DropDownStyle = self.ns["ComboBoxStyle"].DropDownList
        combo.Dock = self.ns["DockStyle"].Top
        combo.Items.Add("Sem reforço")
        combo.Items.Add("Canaletas (CHANNEL)")
        combo.SelectedIndex = 0
        body.Controls.Add(self.label("As famílias de canaleta serão conferidas antes do cálculo. Verga / contraverga: em desenvolvimento.", 70))
        body.Controls.Add(combo)
        body.Controls.Add(self.label("Reforço das aberturas", 38, True))
        body.Controls.Add(self.label("{} paredes selecionadas · {} aberturas detectadas\nNível: {} · Altura: {:.2f} m\nNível e altura foram lidos das paredes selecionadas.".format(
            wall_count, opening_count, level_name, height_m), 100))
        footer = self.panel("Bottom", 64)
        def accept(sender, args):
            form.result = "CHANNEL" if combo.SelectedIndex == 1 else "NONE"
            form.Close()
        footer.Controls.Add(self.button("Cancelar", lambda s, e: form.Close()))
        footer.Controls.Add(self.button("Revisar paredes", accept, True))
        form.Controls.Add(body)
        form.Controls.Add(footer)
        form.Controls.Add(self.header(2, "Confira a seleção e escolha a estratégia de reforço desta execução."))
        form.ShowDialog()
        return form.result

    def busy(self, form, step):
        form._ui_state.start(step)
        self.set_step(form._ui_header, step, "Acompanhe a atividade e o progresso abaixo.")
        form._ui_tabs.SelectedIndex = 1
        form._ui_close.Enabled = False
        form._ui_progress._set_expanded(True)
        form.ControlBox = False
        form._fix_button.Enabled = False
        form._create_button.Enabled = False
        form._solve_button.Enabled = False

    def solved(self, form):
        h = form._handler
        state = form._ui_state
        state.solved(h.solve_result, h.catalog_missing, h.channel_catalog_missing)
        self.update_families(form)
        form._ui_plan.Text = state.report_text(h).replace("\n", "\r\n")
        form._ui_plan.SelectionStart = 0
        form._ui_plan.SelectionLength = 0
        form._ui_piece_grid.Items.Clear()
        for code, count in sorted((state.counts or {}).items()):
            row = self.ns["ListViewItem"](code.replace("CHANNEL_U_", "Canaleta ").replace("CHANNEL_", "Canaleta "))
            row.SubItems.Add(str(count))
            form._ui_piece_grid.Items.Add(row)
        # Metric cards are existing controls: update values without rebuilding.
        cards = [c for c in form._ui_plan_metrics.Controls if c.Controls.Count]
        cards[-1].Controls[0].Text = str(sum(state.counts.values())) if state.counts is not None else "—"
        form._ui_banner.Text = ("✓ " if state.can_create else "! ") + state.reason
        form._ui_banner.ForeColor = self.ns["UI_OK" if state.can_create else "UI_ERROR"]
        form._create_button.Enabled = state.can_create
        self.ns["_style_secondary_button"](form._solve_button)
        self.ns["_style_primary_button"](form._create_button)
        self.ns["_set_button_enabled"](form._create_button, state.can_create)
        form._create_button.Visible = True
        form._solve_button.Text = "Reanalisar modulação"
        form._ui_close.Enabled = True
        form._ui_progress._set_expanded(False)
        form.ControlBox = True
        form._ui_tabs.SelectedIndex = 1
        form.AcceptButton = form._create_button
        form._create_button.Focus()
        self.set_step(form._ui_header, 4, state.reason)

    def failed(self, form, detail):
        form._ui_state.failed(detail)
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

    def completed(self, form):
        state, h = form._ui_state, form._handler
        state.completed(h.create_result or {})
        if state.status == "success" and any(not r.get("resolved") for r in h.error_rows or []):
            state.status = "warning"
        text = {"success": "✓ Modulação concluída. Confira os blocos no Revit.",
                "warning": "! Criação concluída com pendências. Revise o relatório.",
                "error": "! A criação não foi concluída. Consulte as falhas no relatório."}[state.status]
        form._ui_result.Text = (text + "\n\n" + state.report_text(h, h.create_result)).replace("\n", "\r\n")
        form._ui_result.Text += "\r\n" + form._solve_console._elapsed_label.Text
        form._ui_tabs.SelectedIndex = 2
        form._ui_close.Enabled = True
        form._ui_progress._set_expanded(False)
        form.ControlBox = True
        form._create_button.Text = "Atualizar modulação"
        self.ns["_style_secondary_button"](form._create_button)
        self.ns["_style_primary_button"](form._ui_close)
        form.AcceptButton = form._ui_close
        form._ui_close.Focus()
        self.set_step(form._ui_header, 6, text)

    def selection_prompt(self, count):
        """Modal preparation only; actual picking remains native Revit."""
        form = self.new("Form")
        form.Text = "Modulação Automática — seleção de paredes"
        self.configure(form, 940, 540)
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
