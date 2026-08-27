#! python3
# -*- coding: utf-8 -*-
"""LOADER - Modulacao Automatica.

Este arquivo NAO contem mais a logica do script. Ele autentica com um
Personal Access Token (PAT) do GitHub e baixa a versao mais recente do
"motor" real (o PACOTE core/, nao mais um arquivo unico - ver secao
"SINCRONIZACAO DA ARVORE core/" abaixo) direto do repositorio no GitHub,
antes de executar core/wall_modeling.py.

O shebang `#! python3` na PRIMEIRA linha deste arquivo (obrigatorio ser a
linha 1 - ver docs do pyRevit sobre engines) faz o pyRevit rodar este
botao no engine CPython em vez do IronPython padrao. O restante do
loader (autenticacao/DPAPI/WebClient) usa `clr.AddReference` normalmente -
o modulo `clr` tambem existe no engine CPython do pyRevit (via pythonnet),
entao nada nessa parte precisou mudar.

REMOVIDO (2026-08-26, pedido do usuario): a UI interativa em PySide6/Qt
(instalacao extra no Python embutido do pyRevit, download de um sub-pacote
a mais, criacao de QApplication) foi tirada do projeto inteiro - ela era a
maior causa de demora/erros ao abrir o botao. Toda a interface agora usa
so' WinForms (ja' disponivel em qualquer engine, sem instalar nada), com
um layout modernizado (cores, tipografia e cartoes - ver `_SetupForm`,
`UI_BG`/`UI_PANEL`/`_style_primary_button` etc. em core/wall_modeling.py)
- ver INTERACTIVE_MODULATION_UI em core/wall_modeling.py, agora fixo em
False.

Por que um loader?
    - O codigo real existe em UM lugar so' (GitHub). Um "git push" la'
      atualiza automaticamente todos os computadores que clicam neste
      botao - ninguem precisa copiar arquivo manualmente em cada PC.
    - O repositorio pode ficar PRIVADO. So' quem tiver um token valido
      com permissao de leitura consegue baixar e rodar o script.

O token e' pedido uma unica vez (janela do pyRevit) e depois fica salvo
criptografado neste computador, associado a conta do Windows do usuario
(DPAPI - System.Security.Cryptography.ProtectedData), em:
    %LOCALAPPDATA%\\MeuBotaoPushbutton\\token.dat

Se a internet cair, o token expirar ou o GitHub estiver fora do ar, o
loader cai para a ULTIMA sincronizacao completa baixada com sucesso
(espelho local em %LOCALAPPDATA%\\MeuBotaoPushbutton\\pkg_cache\\core\\...),
avisando que a versao pode estar desatualizada - o botao nunca fica
"quebrado" so' por falta de rede.

Ver LOADER_SETUP.md (nesta mesma pasta) para o passo a passo de como
gerar o token no GitHub.
"""

import io
import os
import sys
import json
import shutil
import traceback

import clr
clr.AddReference("System")
clr.AddReference("System.Security")

from System.Net import ServicePointManager, SecurityProtocolType, WebClient, WebException
from System.Security.Cryptography import ProtectedData, DataProtectionScope
from System.Text import Encoding
from System.IO import File as DotNetFile

from pyrevit import forms

# Garante TLS 1.2 - sem isso, em algumas maquinas o .NET tenta um
# protocolo mais antigo que o GitHub recusa, e a chamada falha sem
# explicacao clara.
try:
    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12
except Exception:
    pass


# --------------------------------------------------------------------
# COMPATIBILIDADE forms.* NO ENGINE CPYTHON
#
# O modulo `pyrevit.forms` desta instalacao do pyRevit NAO suporta o
# engine CPython: QUALQUER atributo acessado nele (forms.alert,
# forms.ask_for_string, forms.SelectFromList, etc.) levanta
# `PyRevitCPythonNotSupported` via um `__getattr__` no
# pyrevit/forms/__init__.py (ver traceback "pyrevit.forms.{} is not
# currently supported under CPython"). Como este botao roda inteiro em
# CPython (`#! python3`, ver topo do arquivo) - tanto este loader quanto
# o motor baixado em core/wall_modeling.py, que usa forms.alert /
# forms.ask_for_string / forms.SelectFromList em varios pontos - toda
# chamada a essas funcoes quebraria o script.
#
# Solucao: reimplementar so' essas 3 funcoes usando System.Windows.Forms
# (WinForms, disponivel via `clr` em qualquer engine) e atribui-las
# diretamente no OBJETO do modulo `pyrevit.forms` (o mesmo objeto que
# fica em sys.modules). Como wall_modeling.py roda no mesmo processo
# (via exec() mais abaixo) e faz `from pyrevit import ... forms ...`, ele
# automaticamente enxerga estas versoes compativeis - sem precisar tocar
# em nenhuma das dezenas de chamadas forms.* espalhadas pelo motor.
# --------------------------------------------------------------------
def _dump_winforms_diagnostics(form_type):
    """Diagnostico de UMA VEZ (nunca derruba o script - tudo em try/except)
    para a serie de AttributeError reais em producao neste engine CPython
    (2026-08-27: FormStartPosition.CenterScreen, depois FormBorderStyle.
    FixedDialog, depois Control.SetBounds, depois Control.Controls - cada
    correcao pontual revela o proximo membro quebrado). Escreve num
    arquivo de texto (nao depende de NENHUMA UI, ja' que a propria UI e'
    o que esta' quebrado) qual assembly de System.Windows.Forms esta'
    carregada de verdade e quais membros basicos do Form existem - para
    decidir se da' para seguir corrigindo membro a membro ou se o
    problema e' estrutural (assembly errada/incompleta neste pyRevit)."""
    try:
        # Calculado aqui (em vez de usar APP_DATA_DIR/_ensure_app_data_dir,
        # definidos mais abaixo no arquivo) porque esta funcao roda no
        # module-level `_patch_pyrevit_forms_for_cpython()` logo no topo do
        # loader, ANTES daquelas definicoes existirem.
        app_data_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "MeuBotaoPushbutton"
        )
        if not os.path.isdir(app_data_dir):
            os.makedirs(app_data_dir)
        diag_path = os.path.join(app_data_dir, "loader_diagnostico.txt")
        lines = []
        probe = None
        try:
            probe = form_type()
            asm = probe.GetType().Assembly
            lines.append("Assembly.FullName: {0}".format(asm.FullName))
            lines.append("Assembly.Location: {0}".format(asm.Location))
        except Exception as probe_error:
            lines.append("Falha ao instanciar/inspecionar Form: {0}".format(probe_error))
        if probe is not None:
            for member_name in ("Controls", "SetBounds", "Text", "Width", "Height",
                                 "BackColor", "StartPosition", "FormBorderStyle"):
                try:
                    has_it = hasattr(probe, member_name)
                except Exception as attr_error:
                    has_it = "erro: {0}".format(attr_error)
                lines.append("hasattr(Form(), '{0}') = {1}".format(member_name, has_it))
        try:
            import System
            lines.append("System.Environment.Version: {0}".format(System.Environment.Version))
        except Exception:
            pass
        try:
            clr.AddReference("Microsoft.VisualBasic")
            from Microsoft.VisualBasic import Interaction as _VbInteraction
            lines.append("Microsoft.VisualBasic.Interaction: disponivel")
        except Exception as vb_error:
            lines.append("Microsoft.VisualBasic.Interaction: INDISPONIVEL ({0})".format(vb_error))
        with io.open(diag_path, "w", encoding="utf-8") as diag_file:
            diag_file.write("\n".join(lines))
    except Exception:
        pass


def _patch_pyrevit_forms_for_cpython():
    try:
        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
    except Exception:
        # Sem WinForms disponivel nao ha' como mostrar nada - deixa o
        # modulo original (que so' vai levantar PyRevitCPythonNotSupported
        # nas primeiras chamadas) para nao mascarar o problema real.
        return

    from System.Windows.Forms import (
        Form, Label, TextBox, Button, ListBox, DialogResult,
        FormStartPosition, FormBorderStyle, MessageBox, MessageBoxButtons,
        MessageBoxIcon, SelectionMode, SaveFileDialog, OpenFileDialog,
        FolderBrowserDialog,
    )
    from System.Drawing import Point, Size
    from System import Enum as _DotNetEnum

    def _enum(enum_type, int_value):
        """Converte um inteiro no ENUM DE VERDADE do tipo pedido. Nenhum
        MEMBRO por nome (`FormStartPosition.CenterScreen`) e' acessado aqui
        - so' o TIPO (que importa sem problema neste engine) + o inteiro
        padrao do .NET - ver comentario extenso abaixo de onde isto e'
        chamado pela 1a vez. Tenta o jeito recomendado pelo proprio erro do
        Python.NET 3.0 ("Use Enum(int_value)") primeiro; `Enum.ToObject`
        (reflection de baixo nivel, nao depende dessa conversao implicita
        do pythonnet) e' o 2o fallback; o inteiro cru (comportamento de
        antes desta correcao) e' o ultimo recurso, so' para nunca travar a
        construcao da constante."""
        try:
            return enum_type(int_value)
        except Exception:
            try:
                return _DotNetEnum.ToObject(enum_type, int_value)
            except Exception:
                return int_value

    _dump_winforms_diagnostics(Form)

    # "Controls" (a colecao de filhos de QUALQUER Control/Form) tambem nao
    # resolve neste engine - "'Form' object has no attribute 'Controls'"
    # (real, 2026-08-27). Sem Controls.Add nao da' para montar NENHUM
    # formulario customizado aqui (nem este loader, nem a UI completa
    # de core/wall_modeling.py, que depende disso o tempo todo). Em vez
    # de continuar montando um Form manualmente, o pedido do token usa
    # `Microsoft.VisualBasic.Interaction.InputBox` - uma caixa de
    # entrada de texto PRONTA do .NET (parte do proprio Windows, mesma
    # usada por scripts VBA/VBScript classicos), que nao depende de
    # criar nenhum Control/Form a mao - contorna o problema inteiro para
    # este caso especifico. Guardado atras de try/except: se nem isso
    # existir neste ambiente (bem improvavel - vem com qualquer instalacao
    # do .NET no Windows), cai pro Form manual de antes.
    try:
        clr.AddReference("Microsoft.VisualBasic")
        from Microsoft.VisualBasic import Interaction as _VbInteraction, MsgBoxStyle as _MsgBoxStyle
    except Exception:
        _VbInteraction = None
        _MsgBoxStyle = None
    # Nenhum MEMBRO por nome de ENUM do System.Windows.Forms
    # (FormStartPosition.CenterScreen, FormBorderStyle.FixedDialog,
    # DialogResult.OK, MessageBoxButtons.YesNo, SelectionMode.One, ...) e'
    # acessado por atributo aqui, DE PROPOSITO: no engine CPython (pythonnet)
    # desta instalacao do pyRevit, `from System.Windows.Forms import
    # <EnumType>` importa um TIPO que resolve normalmente, mas acessar um
    # MEMBRO dele por nome (`EnumType.Membro`) e' que nao resolve -
    # AttributeError real medido em producao (2026-08-27), primeiro em
    # `FormStartPosition.CenterScreen`, depois (apos corrigir so' aquele) em
    # `FormBorderStyle.FixedDialog` - cada enum tocado quebrava do mesmo
    # jeito, sempre travando aqui no loader, ANTES de core/wall_modeling.py
    # sequer baixar.
    #
    # Os valores inteiros abaixo sao' os valores PADRAO, documentados e
    # estaveis do .NET para cada enum - mas passar o INT CRU direto (o que
    # esta correcao fazia antes) tambem quebra, so' que de um jeito
    # DIFERENTE: "since Python.NET 3.0 int can not be converted to Enum
    # implicitly. Use Enum(int_value)" (erro real medido em producao,
    # 2026-08-27, em `listbox.SelectionMode = SELECTION_MODE_ONE`) -
    # atribuir um int Python a uma propriedade .NET tipada como enum nao
    # converte implicitamente nesta versao do pythonnet, ao contrario do
    # que se assumia. `_enum(TipoDoEnum, int)` (definida acima) segue
    # exatamente a recomendacao do proprio erro - `TipoDoEnum(int)` -
    # construindo o enum de VERDADE uma unica vez aqui, para toda
    # atribuicao a uma propriedade .NET usar direto o objeto ja' convertido.
    FORM_START_POSITION_CENTER_SCREEN = _enum(FormStartPosition, 1)   # .CenterScreen
    FORM_BORDER_STYLE_FIXED_DIALOG = _enum(FormBorderStyle, 3)        # .FixedDialog
    DIALOG_RESULT_OK = _enum(DialogResult, 1)                         # .OK
    DIALOG_RESULT_CANCEL = _enum(DialogResult, 2)                     # .Cancel
    MESSAGE_BOX_BUTTONS_OK = 0                  # MessageBoxButtons.OK
    MESSAGE_BOX_BUTTONS_YES_NO = 4              # MessageBoxButtons.YesNo
    MESSAGE_BOX_ICON_QUESTION = 32              # MessageBoxIcon.Question
    MESSAGE_BOX_ICON_INFORMATION = 64           # MessageBoxIcon.Information
    SELECTION_MODE_ONE = _enum(SelectionMode, 1)              # .One
    SELECTION_MODE_MULTI_EXTENDED = _enum(SelectionMode, 3)   # .MultiExtended

    # `MessageBox.Show` (usado antes aqui) QUEBROU do mesmo jeito que os
    # enums acima, so' que no METODO em vez de um CAMPO: "type object
    # 'MessageBox' has no attribute 'Show'" (AttributeError real medido em
    # producao, 2026-08-27). A tentativa seguinte (trocar para
    # `Microsoft.VisualBasic.Interaction.MsgBox`, achando que era "a MESMA
    # classe ja' usada por InputBox, comprovadamente funcional") tambem nao
    # se sustentou: em producao (mesmo dia), `Microsoft.VisualBasic`
    # simplesmente NAO carrega em toda maquina/sessao do Revit (o
    # `except Exception: _VbInteraction = None` acima realmente disparou),
    # E quando o fallback tentava `MessageBox.Show(texto, titulo, INT, INT)`
    # com os inteiros crus dos enums, o erro mudou para "No method matches
    # given arguments" - pythonnet, ao contrario do que se esperava, NAO
    # converte automaticamente um int Python para o parametro tipado como
    # enum (MessageBoxButtons/MessageBoxIcon) nesta versao/engine.
    #
    # Solucao definitiva (sem depender de qual das duas classes carrega
    # nesta maquina): tenta MsgBox se `_VbInteraction` existir; senao (ou
    # se MsgBox falhar em tempo de chamada) cai para `MessageBox.Show` com
    # valores de enum DE VERDADE, construidos via `System.Enum.ToObject`
    # (recebe o TIPO do enum - que importa sem problema, so' os MEMBROS
    # por nome e' que nao resolvem - + o inteiro padrao) em vez de
    # `MessageBoxButtons.YesNo` (atributo, quebrado) OU do int cru sozinho
    # (nao bate com o overload, quebrado tambem). Cada camada e' tentada
    # dentro de try/except - a proxima so' roda se a anterior falhar de
    # verdade, nunca decidido so' pela presenca de `_VbInteraction`.
    MSGBOX_RESULT_YES = 6                       # MsgBoxResult.Yes

    def _real_message_box_show(msg, caption, buttons_value, icon_value):
        buttons_enum = _enum(MessageBoxButtons, buttons_value)
        icon_enum = _enum(MessageBoxIcon, icon_value)
        return MessageBox.Show(msg, caption, buttons_enum, icon_enum)

    def _msgbox_show(msg, caption, buttons_value, icon_value):
        if _VbInteraction is not None and _MsgBoxStyle is not None:
            try:
                # `Interaction.MsgBox` tambem tem o 2o parametro tipado
                # como enum (MsgBoxStyle, de Microsoft.VisualBasic) - MESMO
                # bug de conversao implicita, so' que numa classe diferente;
                # combina os dois estilos (botoes | icone) como int PRIMEIRO
                # (bit-a-bit funciona igual entre ints ou entre enums) e so'
                # DEPOIS converte pro enum de verdade, ver `_enum` acima.
                style = _enum(_MsgBoxStyle, buttons_value | icon_value)
                return _VbInteraction.MsgBox(msg, style, caption)
            except Exception:
                pass
        try:
            return _real_message_box_show(msg, caption, buttons_value, icon_value)
        except Exception:
            # Ultimo recurso: caixa so' com OK, sem icone/botoes customizados -
            # overload de 1 argumento nao depende de NENHUM enum.
            MessageBox.Show(msg)
            return DIALOG_RESULT_OK

    # Mesma familia de bug (AttributeError real medido em producao,
    # 2026-08-27): `Control.SetBounds(x, y, w, h)` (herdado por
    # Label/TextBox/Button/ListBox) tambem nao resolve neste engine -
    # "'Label' object has no attribute 'SetBounds'". As propriedades
    # simples `.Location`/`.Size` (que `form.Width`/`form.Height` ja'
    # provam funcionar sem problema aqui) fazem o mesmo efeito sem
    # depender desse metodo especifico.
    def _set_bounds(control, x, y, width, height):
        control.Location = Point(x, y)
        control.Size = Size(width, height)

    def _txt(value):
        return value if isinstance(value, str) else str(value)

    def _is_dialog_yes(result):
        """Compara o retorno de MsgBox/MessageBox.Show contra 'Sim' de
        forma robusta neste engine CPython (pythonnet) - bug real
        reportado pelo usuario (2026-08-27): clicar em 'Sim' num dialogo
        `forms.alert(..., yes=True, no=True)` nao fazia NADA (mesmo
        efeito de ter clicado 'Nao'), porque `_compat_alert` comparava o
        enum .NET devolvido (`System.Windows.Forms.DialogResult.Yes` OU
        `Microsoft.VisualBasic.MsgBoxResult.Yes` - dois tipos .NET
        DIFERENTES, dependendo de qual caminho `_msgbox_show` usou, ambos
        com valor 6) direto contra o INT CRU `MSGBOX_RESULT_YES = 6`
        (`resultado == 6`) - a MESMA familia de bug de conversao
        implicita int<->Enum do Python.NET 3.0 documentada no topo deste
        arquivo (a razao de existir `_enum()`), so' que na comparacao de
        SAIDA em vez da atribuicao de ENTRADA, entao nunca foi coberta
        pelas correcoes anteriores. Tenta 3 formas, da mais direta a mais
        robusta - a ultima (nome do membro via ToString(), sempre
        disponivel para um enum .NET) nao depende de nenhuma conversao
        numerica implicita."""
        try:
            if result == MSGBOX_RESULT_YES:
                return True
        except Exception:
            pass
        try:
            if int(result) == MSGBOX_RESULT_YES:
                return True
        except Exception:
            pass
        try:
            return _txt(result).strip().lower() == "yes"
        except Exception:
            return False

    def _compat_alert(msg, title=None, exitscript=False, yes=False, no=False, **kwargs):
        caption = _txt(title) if title else "Modulacao Automatica"
        if yes or no:
            result = _msgbox_show(
                _txt(msg), caption, MESSAGE_BOX_BUTTONS_YES_NO, MESSAGE_BOX_ICON_QUESTION
            )
            return _is_dialog_yes(result)
        _msgbox_show(_txt(msg), caption, MESSAGE_BOX_BUTTONS_OK, MESSAGE_BOX_ICON_INFORMATION)
        if exitscript:
            sys.exit()
        return None

    def _manual_input_form(default, prompt, title):
        # Fallback (Microsoft.VisualBasic indisponivel/instavel nesta
        # maquina - ver comentario em `_compat_ask_for_string`): Form manual
        # de antes. Se `Controls`/`SetBounds` estiverem quebrados neste
        # ambiente (ver _dump_winforms_diagnostics), este caminho tambem vai
        # falhar - mas nesse caso ja' nao ha' alternativa dentro de WinForms
        # puro.
        form = Form()
        form.Text = _txt(title) if title else "Modulacao Automatica"
        form.StartPosition = FORM_START_POSITION_CENTER_SCREEN
        form.FormBorderStyle = FORM_BORDER_STYLE_FIXED_DIALOG
        form.MinimizeBox = False
        form.MaximizeBox = False
        form.Width = 460
        form.Height = 180

        label = Label()
        label.Text = _txt(prompt) if prompt else ""
        _set_bounds(label, 12, 12, 420, 60)
        label.AutoSize = False
        form.Controls.Add(label)

        textbox = TextBox()
        _set_bounds(textbox, 12, 78, 420, 24)
        textbox.Text = _txt(default) if default else ""
        form.Controls.Add(textbox)

        ok_button = Button()
        ok_button.Text = "OK"
        ok_button.DialogResult = DIALOG_RESULT_OK
        _set_bounds(ok_button, 276, 112, 75, 28)
        form.Controls.Add(ok_button)

        cancel_button = Button()
        cancel_button.Text = "Cancelar"
        cancel_button.DialogResult = DIALOG_RESULT_CANCEL
        _set_bounds(cancel_button, 357, 112, 75, 28)
        form.Controls.Add(cancel_button)

        form.AcceptButton = ok_button
        form.CancelButton = cancel_button

        result = form.ShowDialog()
        if result == DIALOG_RESULT_OK:
            return textbox.Text
        return None

    def _compat_ask_for_string(default="", prompt="", title="", **kwargs):
        # `Microsoft.VisualBasic.Interaction.InputBox` e' o caminho
        # preferido (nao precisa montar Form/Controls a mao - ver
        # comentario em `_msgbox_show`), mas nao e' garantido: a mesma
        # sessao que mostrou este InputBox com sucesso na 1a execucao
        # voltou com `_VbInteraction` None (ou o proprio InputBox falhando)
        # depois de reiniciar o Revit (real, 2026-08-27) - carregar
        # `Microsoft.VisualBasic` nao e' estavel entre sessoes nesta
        # maquina. Por isso o try/except aqui tambem, em vez de decidir so'
        # pela presenca de `_VbInteraction` (mesmo padrao de `_msgbox_show`).
        if _VbInteraction is not None:
            try:
                # `InputBox` devolve string vazia (nunca None) quando o
                # usuario cancela/fecha.
                result = _VbInteraction.InputBox(
                    _txt(prompt) if prompt else "",
                    _txt(title) if title else "Modulacao Automatica",
                    _txt(default) if default else "",
                )
                return result if result else None
            except Exception:
                pass
        return _manual_input_form(default, prompt, title)

    def _compat_select_from_list(items, title="", button_name="OK", multiselect=False, **kwargs):
        items = list(items)
        if not items:
            return [] if multiselect else None

        form = Form()
        form.Text = _txt(title) if title else "Modulacao Automatica"
        form.StartPosition = FORM_START_POSITION_CENTER_SCREEN
        form.FormBorderStyle = FORM_BORDER_STYLE_FIXED_DIALOG
        form.MinimizeBox = False
        form.MaximizeBox = False
        form.Width = 420
        form.Height = 420

        listbox = ListBox()
        _set_bounds(listbox, 12, 12, 380, 300)
        listbox.SelectionMode = (
            SELECTION_MODE_MULTI_EXTENDED if multiselect else SELECTION_MODE_ONE
        )
        for item in items:
            listbox.Items.Add(_txt(item))
        listbox.SetSelected(0, True)
        form.Controls.Add(listbox)

        ok_button = Button()
        ok_button.Text = _txt(button_name) if button_name else "OK"
        ok_button.DialogResult = DIALOG_RESULT_OK
        _set_bounds(ok_button, 216, 324, 75, 28)
        form.Controls.Add(ok_button)

        cancel_button = Button()
        cancel_button.Text = "Cancelar"
        cancel_button.DialogResult = DIALOG_RESULT_CANCEL
        _set_bounds(cancel_button, 297, 324, 75, 28)
        form.Controls.Add(cancel_button)

        form.AcceptButton = ok_button
        form.CancelButton = cancel_button

        result = form.ShowDialog()
        if result != DIALOG_RESULT_OK:
            return None

        selected_indices = list(listbox.SelectedIndices)
        if not selected_indices:
            return None
        selected_items = [items[i] for i in selected_indices]
        return selected_items if multiselect else selected_items[0]

    class _CompatSelectFromList(object):
        @staticmethod
        def show(items, **kwargs):
            return _compat_select_from_list(items, **kwargs)

    def _compat_save_file(file_ext="", default_name="", title="", **kwargs):
        dialog = SaveFileDialog()
        dialog.Title = _txt(title) if title else "Salvar arquivo de captura"
        if file_ext:
            ext = _txt(file_ext).lstrip(".")
            dialog.Filter = "{0} files (*.{1})|*.{1}|All files (*.*)|*.*".format(ext.upper(), ext)
            dialog.DefaultExt = ext
            dialog.AddExtension = True
        else:
            dialog.Filter = "All files (*.*)|*.*"
        if default_name:
            dialog.FileName = _txt(default_name)
        dialog.RestoreDirectory = True
        result = dialog.ShowDialog()
        if result == DialogResult.OK:
            return dialog.FileName
        return None

    def _compat_pick_file(file_ext="", title="", **kwargs):
        dialog = OpenFileDialog()
        dialog.Title = _txt(title) if title else "Selecionar arquivo"
        if file_ext:
            ext = _txt(file_ext).lstrip(".")
            dialog.Filter = "{0} files (*.{1})|*.{1}|All files (*.*)|*.*".format(ext.upper(), ext)
            dialog.DefaultExt = ext
        else:
            dialog.Filter = "All files (*.*)|*.*"
        dialog.RestoreDirectory = True
        result = dialog.ShowDialog()
        if result == DialogResult.OK:
            return dialog.FileName
        return None

    def _compat_pick_folder(title="", **kwargs):
        dialog = FolderBrowserDialog()
        if title:
            dialog.Description = _txt(title)
        result = dialog.ShowDialog()
        if result == DialogResult.OK:
            return dialog.SelectedPath
        return None

    # Atribuir direto no objeto do modulo: isso preenche o __dict__ do
    # modulo, que tem prioridade sobre o __getattr__ (PEP 562) usado pelo
    # pyRevit para bloquear estes nomes no engine CPython.
    forms.alert = _compat_alert
    forms.ask_for_string = _compat_ask_for_string
    forms.SelectFromList = _CompatSelectFromList
    forms.save_file = _compat_save_file
    forms.pick_file = _compat_pick_file
    forms.pick_folder = _compat_pick_folder


_patch_pyrevit_forms_for_cpython()


# --------------------------------------------------------------------
# CONFIGURACAO DO REPOSITORIO
# --------------------------------------------------------------------
GITHUB_OWNER = "Arcanjog1"
GITHUB_REPO = "MeuBotao.pushbutton"
GITHUB_BRANCH = "main"

# Prefixo (relativo a' raiz do repositorio) de TUDO que o loader precisa
# sincronizar - nao e' mais so' um arquivo. `core/` agora e' um PACOTE
# (engine/, alem do wall_modeling.py de sempre - o sub-pacote da antiga UI
# interativa em PySide6 foi removido, ver docstring deste arquivo). Qualquer
# arquivo .py novo adicionado dentro dessa pasta no GitHub passa a ser
# baixado automaticamente, sem precisar mexer neste loader de novo.
CORE_REPO_PREFIX = "core/"
ENTRY_POINT_REPO_PATH = CORE_REPO_PREFIX + "wall_modeling.py"

TREE_API_URL = "https://api.github.com/repos/{0}/{1}/git/trees/{2}?recursive=1".format(
    GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH
)


def _contents_api_url(repo_path):
    return "https://api.github.com/repos/{0}/{1}/contents/{2}?ref={3}".format(
        GITHUB_OWNER, GITHUB_REPO, repo_path, GITHUB_BRANCH
    )


APP_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "MeuBotaoPushbutton"
)
TOKEN_FILE = os.path.join(APP_DATA_DIR, "token.dat")

# Espelho local da ARVORE `core/` inteira (nao mais um unico arquivo em
# cache) - e' o que fica em sys.path para os `from core.xxx import yyy`
# dentro de wall_modeling.py resolverem. `PKG_CACHE_DIR` e' sempre a
# ULTIMA sincronizacao COMPLETA e bem-sucedida (ver _sync_core_package) -
# nunca fica pela metade: a sincronizacao roda inteira num diretorio
# temporario e so' substitui `PKG_CACHE_DIR` se TODOS os arquivos baixarem
# com sucesso.
PKG_CACHE_DIR = os.path.join(APP_DATA_DIR, "pkg_cache")
PKG_CACHE_TMP_DIR = os.path.join(APP_DATA_DIR, "pkg_cache_tmp")


# --------------------------------------------------------------------
# TOKEN - guardado criptografado (DPAPI, ligado ao usuario do Windows)
# --------------------------------------------------------------------
def _ensure_app_data_dir():
    if not os.path.isdir(APP_DATA_DIR):
        os.makedirs(APP_DATA_DIR)


def _save_token(token):
    _ensure_app_data_dir()
    # `Encoding.UTF8` (propriedade estatica) sofre do MESMO bug de
    # resolucao de membro estatico por atributo medido em producao nos
    # enums do WinForms (ver comentarios em _patch_pyrevit_forms_for_cpython)
    # - "type object 'Encoding' has no attribute 'UTF8'" real, 2026-08-27 -
    # so' que aqui em System.Text, fora do WinForms: o bug nao e' exclusivo
    # de enum/WinForms, e' generico deste engine CPython (pythonnet) para
    # QUALQUER membro estatico sem argumento acessado por atributo.
    # `Encoding.GetEncoding("UTF-8")` e' um METODO (nao uma propriedade) e
    # nao depende dessa resolucao quebrada.
    raw_bytes = Encoding.GetEncoding("UTF-8").GetBytes(token)
    protected_bytes = ProtectedData.Protect(raw_bytes, None, DataProtectionScope.CurrentUser)
    DotNetFile.WriteAllBytes(TOKEN_FILE, protected_bytes)


def _load_token():
    if not os.path.isfile(TOKEN_FILE):
        return None
    try:
        protected_bytes = DotNetFile.ReadAllBytes(TOKEN_FILE)
        raw_bytes = ProtectedData.Unprotect(protected_bytes, None, DataProtectionScope.CurrentUser)
        return Encoding.GetEncoding("UTF-8").GetString(raw_bytes)
    except Exception:
        # Token corrompido, gerado por outro usuario/maquina, etc. -
        # forca pedir um novo em vez de travar o script.
        return None


def _ask_for_token():
    token = forms.ask_for_string(
        default="",
        prompt=(
            "Cole aqui o seu GitHub Personal Access Token (fine-grained, "
            "somente leitura de 'Contents' no repositorio {0}/{1}).\n\n"
            "Ele sera' salvo criptografado neste computador (ligado a sua "
            "conta do Windows) e nao sera' pedido de novo.\n\n"
            "Passo a passo para gerar o token: ver LOADER_SETUP.md."
        ).format(GITHUB_OWNER, GITHUB_REPO),
        title="Modulacao Automatica - autenticacao necessaria",
    )
    if token:
        token = token.strip()
    if not token:
        return None
    _save_token(token)
    return token


def _get_token(force_reprompt=False):
    token = None if force_reprompt else _load_token()
    if not token:
        token = _ask_for_token()
    return token


def _forget_token():
    try:
        if os.path.isfile(TOKEN_FILE):
            os.remove(TOKEN_FILE)
    except Exception:
        pass


# --------------------------------------------------------------------
# BUSCA NO GITHUB (com fallback para cache local)
# --------------------------------------------------------------------
def _raise_for_web_exception(web_error, context):
    status_code = None
    if web_error.Response is not None:
        try:
            status_code = int(web_error.Response.StatusCode)
        except Exception:
            status_code = None
    if status_code == 401:
        raise RuntimeError("Token invalido ou expirado (HTTP 401).")
    if status_code == 403:
        raise RuntimeError(
            "Acesso negado - token sem permissao de leitura neste "
            "repositorio, ou limite de requisicoes do GitHub atingido "
            "(HTTP 403)."
        )
    if status_code == 404:
        raise RuntimeError(
            "{0} nao encontrado no repositorio (HTTP 404) - confira "
            "GITHUB_OWNER/GITHUB_REPO/GITHUB_BRANCH no loader.".format(context)
        )
    raise RuntimeError("Falha ao contatar o GitHub ({0}): {1}".format(context, web_error.Message))


def _new_web_client(token, accept):
    client = WebClient()
    client.Encoding = Encoding.GetEncoding("UTF-8")  # ver comentario em _save_token
    # O repositorio ficou PUBLICO (2026-08-27, confirmado com o usuario) -
    # `token` agora e' OPCIONAL: sem ele, a API do GitHub responde do mesmo
    # jeito (so' com um limite de requisicoes mais baixo por IP). So' manda
    # o cabecalho Authorization quando ha' um token de verdade salvo/
    # informado, para nao mandar "Bearer " vazio (que o GitHub rejeitaria
    # com 401 mesmo num repo publico).
    if token:
        client.Headers.Add("Authorization", "Bearer " + token)
    client.Headers.Add("Accept", accept)
    client.Headers.Add("User-Agent", "MeuBotaoPushbutton-Loader")
    client.Headers.Add("X-GitHub-Api-Version", "2022-11-28")
    return client


def _list_remote_core_files(token):
    """Lista (recursivamente) todos os arquivos .py sob CORE_REPO_PREFIX no
    branch configurado, via a API de arvore do Git (uma unica chamada, em
    vez de uma por pasta) - devolve os PATHS completos (relativos a' raiz
    do repositorio)."""
    client = _new_web_client(token, "application/vnd.github+json")
    try:
        raw = client.DownloadString(TREE_API_URL)
    except WebException as web_error:
        _raise_for_web_exception(web_error, "listagem da arvore core/")
        return []  # nunca alcancado - _raise_for_web_exception sempre levanta

    data = json.loads(raw)
    if data.get("truncated"):
        raise RuntimeError(
            "A API do GitHub truncou a listagem da arvore do repositorio - "
            "avise o mantenedor (o pacote core/ ficou grande demais para "
            "uma unica chamada 'recursive=1')."
        )
    files = [
        entry["path"] for entry in data.get("tree", [])
        if entry.get("type") == "blob"
        and entry.get("path", "").startswith(CORE_REPO_PREFIX)
        and entry.get("path", "").endswith(".py")
    ]
    if ENTRY_POINT_REPO_PATH not in files:
        raise RuntimeError(
            "core/wall_modeling.py nao apareceu na listagem do GitHub - "
            "abortando (para nao rodar so' metade do motor)."
        )
    return files


def _fetch_file_raw(token, repo_path):
    client = _new_web_client(token, "application/vnd.github.raw")
    try:
        return client.DownloadString(_contents_api_url(repo_path))
    except WebException as web_error:
        _raise_for_web_exception(web_error, repo_path)


def _sync_core_package(token):
    """Baixa TODOS os .py de core/ (ver _list_remote_core_files) para
    PKG_CACHE_TMP_DIR, mantendo a mesma estrutura de pastas (core/...), e
    so' substitui PKG_CACHE_DIR de verdade se TODOS baixarem com sucesso -
    uma falha no meio do caminho nunca deixa o cache local pela metade
    (quem chama continua podendo usar a ultima sincronizacao boa
    anterior). Devolve o path local de core/wall_modeling.py dentro do
    cache atualizado.
    """
    files = _list_remote_core_files(token)

    if os.path.isdir(PKG_CACHE_TMP_DIR):
        shutil.rmtree(PKG_CACHE_TMP_DIR)
    os.makedirs(PKG_CACHE_TMP_DIR)

    for repo_path in files:
        relative = repo_path  # "core/xxx/yyy.py"
        local_path = os.path.join(PKG_CACHE_TMP_DIR, *relative.split("/"))
        local_dir = os.path.dirname(local_path)
        if not os.path.isdir(local_dir):
            os.makedirs(local_dir)
        content = _fetch_file_raw(token, repo_path)
        with io.open(local_path, "w", encoding="utf-8") as fh:
            fh.write(content)

    # so' agora, com TUDO baixado, troca o cache "de verdade" pelo novo -
    # esta e' a unica secao que pode deixar PKG_CACHE_DIR num estado
    # inconsistente se falhar no meio (rmtree ja' comecou); na pratica o
    # risco e' minimo (duas operacoes de sistema de arquivos locais, sem
    # rede envolvida).
    if os.path.isdir(PKG_CACHE_DIR):
        shutil.rmtree(PKG_CACHE_DIR)
    os.rename(PKG_CACHE_TMP_DIR, PKG_CACHE_DIR)

    return os.path.join(PKG_CACHE_DIR, "core", "wall_modeling.py")


def _entry_point_from_existing_cache():
    """Fallback: usa a ultima sincronizacao local bem-sucedida (sem tentar
    o GitHub de novo) - equivalente ao antigo `_load_cache()`, agora
    apontando para a arvore inteira em vez de um unico arquivo."""
    entry_point = os.path.join(PKG_CACHE_DIR, "core", "wall_modeling.py")
    if os.path.isfile(entry_point):
        return entry_point
    return None


def _load_entry_point():
    """Sincroniza a arvore core/ inteira e devolve o path LOCAL de
    core/wall_modeling.py pronto para exec() - com fallback para a ultima
    sincronizacao boa em cache, na mesma ordem/logica de antes (so' que
    por arvore de arquivos, nao mais um arquivo unico - ver
    _sync_core_package).

    O repositorio ficou PUBLICO (2026-08-27) - o token NAO e' mais exigido
    de saida: tenta baixar sem autenticacao primeiro (um token salvo de
    antes de virar publico e' usado se existir, mas nunca e' pedido aqui).
    So' pede um token na tela se o download sem token falhar com 401/403
    (limite de requisicoes do IP atingido, ou o repositorio ter voltado a
    ficar privado)."""
    token = _load_token()
    try:
        return _sync_core_package(token)
    except Exception as first_error:
        # 401/403 sem token pode ser rate limit do IP ou o repo ter voltado
        # a ser privado; com token salvo, pode ter expirado/sido revogado -
        # nos dois casos, pede um (novo) token antes de desistir e cair no
        # cache.
        error_text = str(first_error)
        if "401" in error_text or "403" in error_text:
            if token:
                _forget_token()
            retry_token = _get_token(force_reprompt=True)
            if retry_token:
                try:
                    return _sync_core_package(retry_token)
                except Exception as second_error:
                    first_error = second_error

        cached_entry = _entry_point_from_existing_cache()
        if cached_entry:
            forms.alert(
                "Nao foi possivel baixar a versao mais recente do GitHub:\n\n"
                "{0}\n\nRodando a ultima copia em cache (pode estar "
                "desatualizada).".format(first_error),
                title="Modulacao Automatica - usando cache",
            )
            return cached_entry
        forms.alert(
            "Nao foi possivel baixar o script do GitHub e nao ha' copia em "
            "cache neste computador:\n\n{0}".format(first_error),
            title="Modulacao Automatica - erro",
        )
        sys.exit()


# --------------------------------------------------------------------
# EXECUCAO - roda o motor baixado dentro do namespace deste loader, para
# que ele enxergue os globais que o proprio pyRevit injeta (__revit__,
# __window__, etc.) exatamente como se fosse o Script.py de sempre.
#
# Diferenca em relacao ao loader antigo (que baixava um UNICO arquivo em
# memoria e so' fazia exec() do texto): agora core/ e' um PACOTE, entao a
# pasta sincronizada (PKG_CACHE_DIR) precisa estar em sys.path ANTES do
# exec(), para que os `from core.xxx import yyy` dentro de
# wall_modeling.py resolvam de verdade - e `__file__` precisa ser
# preenchido nos globais (exec() nao faz isso sozinho), porque
# wall_modeling.py usa `os.path.dirname(os.path.abspath(__file__))` para
# achar sua propria pasta (ver bloco de import guardado perto de
# _ACTIVE_MODELESS_WINDOWS).
# --------------------------------------------------------------------
_entry_point_path = _load_entry_point()

# Se o engine deste botao ficar "persistente" entre cliques (ver
# ARQUITETURA_INTERATIVA.md - nao ligamos isso por padrao, mas protege
# tambem contra qualquer outro botao que tenha deixado algo em
# sys.modules), qualquer `core`/`core.*` de uma sincronizacao ANTERIOR
# precisa ser descartado antes do proximo exec() - senao um
# `import core.xxx` dentro do wall_modeling.py recem-baixado pegaria a
# versao VELHA ja' cacheada em memoria em vez de ler o arquivo novo do
# disco.
for _mod_name in list(sys.modules.keys()):
    if _mod_name == "core" or _mod_name.startswith("core."):
        del sys.modules[_mod_name]

_pkg_cache_root = os.path.dirname(os.path.dirname(_entry_point_path))  # .../pkg_cache
if _pkg_cache_root not in sys.path:
    sys.path.insert(0, _pkg_cache_root)

with io.open(_entry_point_path, "r", encoding="utf-8") as _fh:
    _source_code = _fh.read()

globals()["__file__"] = _entry_point_path

try:
    exec(compile(_source_code, _entry_point_path, "exec"), globals())
except SystemExit:
    raise
except Exception:
    forms.alert(
        "O script baixado do GitHub encontrou um erro ao executar:\n\n{0}".format(
            traceback.format_exc()
        ),
        title="Modulacao Automatica - erro na execucao",
    )
    raise
