# -*- coding: utf-8 -*-
"""`analyze` roda SINCRONO dentro do Execute(), sem thread de fundo.

A thread de fundo do caminho `analyze` foi retirada em 2026-09-10 depois de
tres congelamentos medidos no Revit real, todos com o worker SEM consumir
CPU e o interpretador inteiro parado:

  execucao 4: 94,167s parados na fronteira de `analyze`
  execucao 5: Application.DoEvents() da thread de fundo levou 2652,285s
  execucao 6: solve_all_intersections levou 1654,774s (27min35s) com o
              worker em ~47ms de CPU no periodo inteiro; threads
              `Running`=0; concluiu em milissegundos ao destravar

Dois processos do Revit morreram (14:24:03 e 14:55:09) depois desses
episodios. Contra isso, `analyze` custa 0,181s medido dentro do Revit no
documento real - nao havia beneficio em manter a thread.

Estes testes fixam o contrato novo: nenhuma thread criada nesse caminho, o
resultado chega a UI, o callback roda uma unica vez, e uma excecao continua
virando `on_done("error", ...)`.
"""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import load_script  # noqa: E402
import revit_stubs  # noqa: E402

m = load_script.load()


def _uiapp_falso():
    uidoc = revit_stubs._Inert()
    uidoc.Document = revit_stubs._Inert()
    uiapp = revit_stubs._Inert()
    uiapp.ActiveUIDocument = uidoc
    return uiapp


class _EspiaoDeThread(object):
    """Substitui `_DotNetThread` no modulo e registra qualquer tentativa de
    criar thread - o contrato e' que NENHUMA seja criada."""

    def __init__(self):
        self.criadas = 0

    def __call__(self, *args, **kwargs):
        self.criadas += 1
        raise AssertionError(
            "thread de fundo criada no caminho analyze - a correcao de "
            "2026-09-10 retirou exatamente isso")


def _trocar_global(h, nome, valor):
    """Troca um nome global do motor de forma que sobreviva ao `Execute()`.

    ARMADILHA REAL (pega escrevendo este arquivo): `Execute()` faz
    `self._fix_all_wall_modulation_errors.__globals__.update(self._g)`, o
    snapshot capturado no `__init__`. Um monkeypatch feito so' no modulo e'
    DESFEITO por essa reinjecao - e um teste que so' contasse chamadas
    passaria pelo motivo errado, porque a thread REAL seria criada em vez da
    falsa. Precisa trocar nos DOIS lugares."""
    setattr(m, nome, valor)
    h._g[nome] = valor


def _handler_analyze(resultado=None, explode=False):
    h = m._PostCreationEventHandler()
    h.action = "analyze"
    h.walls_to_create = []
    h.openings_per_wall = []
    h._refresh_geometry_from_document = lambda app_doc: None

    chamadas = []

    def _analise(*args, **kwargs):
        chamadas.append("analise")
        if explode:
            raise ValueError("falha proposital dentro do analyze")
        return resultado if resultado is not None else []

    h._analyze_created_walls_for_errors = _analise
    return h, chamadas


def test_analyze_nao_cria_thread_de_fundo():
    """O CONTRATO CENTRAL: `ui_invoke_cb` fica None, entao `_execute_analyze`
    toma o ramo sincrono e nenhuma `System.Threading.Thread` nasce."""
    h, chamadas = _handler_analyze(resultado=[{"wall_idx": 0}])
    h.on_done = lambda kind, err: None
    espiao = _EspiaoDeThread()
    original = m._DotNetThread
    _trocar_global(h, "_DotNetThread", espiao)
    try:
        h.Execute(_uiapp_falso())
    finally:
        _trocar_global(h, "_DotNetThread", original)
    assert espiao.criadas == 0, espiao.criadas
    assert chamadas == ["analise"], chamadas


def test_resultado_chega_a_ui_e_callback_roda_uma_unica_vez():
    """`error_rows` preenchido e `on_done("analyze", None)` exatamente uma
    vez - sem BeginInvoke, porque ja' estamos na thread certa."""
    linhas = [{"wall_idx": 0, "problem_text": "x"}]
    h, _ = _handler_analyze(resultado=linhas)
    eventos = []
    h.on_done = lambda kind, err: eventos.append((kind, err))
    h.Execute(_uiapp_falso())
    assert h.error_rows == linhas, h.error_rows
    assert eventos == [("analyze", None)], eventos


def test_analyze_termina_dentro_do_execute_nao_depois():
    """Sincrono de verdade: quando `Execute()` retorna, o resultado JA
    existe. Com a thread de fundo isto era uma corrida."""
    h, _ = _handler_analyze(resultado=[{"wall_idx": 7}])
    eventos = []
    h.on_done = lambda kind, err: eventos.append(kind)
    assert h.error_rows is None or h.error_rows == []
    h.Execute(_uiapp_falso())
    assert eventos == ["analyze"], eventos
    assert h.error_rows == [{"wall_idx": 7}], h.error_rows


def test_excecao_no_analyze_vira_on_done_error_uma_vez():
    """Uma falha dentro do analyze continua chegando a UI como
    kind=="error", com mensagem, e sem rodar o callback duas vezes."""
    h, chamadas = _handler_analyze(explode=True)
    eventos = []
    h.on_done = lambda kind, err: eventos.append((kind, err))
    h.Execute(_uiapp_falso())
    assert chamadas == ["analise"], chamadas
    assert len(eventos) == 1, eventos
    kind, err = eventos[0]
    assert kind == "error", eventos
    assert "falha proposital" in str(err), err


def test_acao_agendada_durante_o_analyze_sincrono_sobrevive():
    """Interacao com a correcao do encadeamento: `_on_analyze_done` abre a
    Tela 2 e ela agenda "solve"/"create" DE DENTRO deste mesmo Execute().
    Essa acao tem de sobreviver - e' o mesmo contrato de
    test_acao_agendada_por_callback_durante_execute_sobrevive, agora com o
    analyze sincrono."""
    h, _ = _handler_analyze(resultado=[])

    def _on_done(kind, err):
        h.action = "solve"          # o que a Tela 2 faz via _raise_action

    h.on_done = _on_done
    h.Execute(_uiapp_falso())
    assert h.action == "solve", h.action


def test_ui_invoke_cb_continua_suportado_para_quem_instalar():
    """O ramo de fundo NAO foi apagado - so' deixou de ser instalado pelo
    produto. Quem passar `ui_invoke_cb` continua tendo o marshaling, para
    nao quebrar nenhum chamador externo."""
    h, _ = _handler_analyze(resultado=[])
    marshaladas = []
    h.ui_invoke_cb = lambda fn: (marshaladas.append(fn), fn())[1]
    eventos = []
    h.on_done = lambda kind, err: eventos.append(kind)

    criadas = []

    class _ThreadFalsa(object):
        def __init__(self, start):
            criadas.append(start)
            self._start = start

        def Start(self):
            self._start()

    original = m._DotNetThread
    original_ts = m._DotNetThreadStart
    _trocar_global(h, "_DotNetThread", _ThreadFalsa)
    _trocar_global(h, "_DotNetThreadStart", lambda fn: fn)
    try:
        h.Execute(_uiapp_falso())
    finally:
        _trocar_global(h, "_DotNetThread", original)
        _trocar_global(h, "_DotNetThreadStart", original_ts)
    assert len(criadas) == 1, criadas
    assert len(marshaladas) == 1, marshaladas
    assert eventos == ["analyze"], eventos


def test_o_produto_nao_instala_mais_ui_invoke_cb():
    """Guarda de producao: se alguem reintroduzir
    `self._handler.ui_invoke_cb = _ui_invoke` em _on_start_click, a thread
    de fundo volta em silencio e os testes acima continuariam passando (eles
    exercitam o handler direto). Este teste le' a fonte."""
    import inspect
    fonte = inspect.getsource(m._WallReviewForm._on_start_click)
    assert "ui_invoke_cb = None" in fonte, (
        "o caminho analyze do produto voltou a instalar ui_invoke_cb - a "
        "thread de fundo retirada em 2026-09-10 foi reintroduzida")
    codigo = [l for l in fonte.splitlines()
              if not l.strip().startswith("#")]
    assert not any("BeginInvoke" in l for l in codigo), (
        "BeginInvoke de volta no CODIGO de _on_start_click: com analyze "
        "sincrono ja' estamos na thread de UI e o marshaling e' desnecessario")
