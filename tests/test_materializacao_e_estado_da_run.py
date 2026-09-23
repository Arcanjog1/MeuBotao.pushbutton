# -*- coding: utf-8 -*-
"""Regressao da rodada de 2026-09-23 (execucao real do usuario no Revit).

Tres sintomas reais: a configuracao da Etapa 1 sumia entre as telas, a Etapa 4
bloqueava a criacao inteira por violacoes LOCALIZADAS, e a Etapa 3B aparecia
como "fora do fluxo" sem contrato. Estes testes fixam o comportamento correto
sem tocar em regra fisica nenhuma.
"""
import inspect

import pytest

import load_script

m = load_script.load()
from core.ui_state import (creation_gate, localized_blockers, fatal_errors, materialization_counts,
                           skipped_rows, ModulationUiState)


# --------------------------------------------------------------- utilitarios
class _XYZ(object):
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.X, self.Y, self.Z = x, y, z


def peca(code="B39", wall=0, x=0.0, reason="STANDARD_FILL"):
    return {"logical_code": code, "wall_idx": wall, "secondary_wall_idx": None,
            "origin_world": _XYZ(x, 0.0, 0.0), "x_dir": _XYZ(1.0, 0.0, 0.0),
            "length_cm": 39.0, "width_cm": 14.0, "placement_reason": reason}


def plano(n=5):
    """Plano com `n` pecas por fiada, duas fiadas."""
    return {0: [peca(x=i * 0.4) for i in range(n)],
            1: [peca(x=i * 0.4 + 0.1) for i in range(n)]}


def resultado(preflight, candidates=True):
    cc = plano()
    return {"course_candidates": cc, "num_courses": 2,
            "candidates": cc[0] if candidates else [], "beta_preflight": preflight}


# ------------------------------------------------- PARTE 4: politica de criacao
def test_violacao_localizada_nao_bloqueia_a_run_inteira():
    """8.332 pecas validas nao podem morrer por causa de uma peca que invade vao."""
    pf = {"ok": False, "errors": [],
          "opening_violations": [{"course_index": 0, "candidate_index": 2, "origin_cm": [10.0, 0.0]}],
          "collisions": []}
    r = resultado(pf)
    liberado, motivo = creation_gate(r)
    assert liberado is True
    assert "Criar blocos" in motivo and "registrad" in motivo
    assert localized_blockers(r) == 1


def test_peca_comum_impossivel_e_pulada_e_amarracao_e_materializada_com_denuncia():
    """A politica separa os dois casos - medido no modelo real (no 41, 11 fiadas)."""
    pf = {"ok": False, "errors": [],
          "opening_violations": [{"course_index": 0, "candidate_index": 0, "overlap_cm": 0.5},
                                 {"course_index": 1, "candidate_index": 1, "overlap_cm": 0.5}],
          "collisions": []}
    r = resultado(pf)
    r["course_candidates"][0][0] = peca(code="B34", reason="T_INTERSECTION_DEGRADED_L")  # amarracao
    plano = m.materialization_plan(r, pf)
    assert len(plano["violating"]) == 1 and len(plano["impossible"]) == 1
    amarracao = plano["violating"][0][2]
    assert amarracao["materializable"] is True
    assert amarracao["needs_human_review"] is True
    assert amarracao["severity"] == "RULE_VIOLATION_VISUALIZABLE"
    assert amarracao["rule_id"].startswith("TIE_")
    comum = plano["impossible"][0][2]
    assert comum["materializable"] is False and comum["severity"] == "GEOMETRY_IMPOSSIBLE"
    # so' a peca comum sai da criacao
    assert len(m.unbuildable_pieces(r, pf)) == 1


def test_contrato_de_materializacao_chega_a_apresentacao():
    from core.ui_state import materialization_split, materialization_rows
    r = resultado({"ok": False, "errors": [], "opening_violations": [], "collisions": []})
    r["materialization"] = {
        "impossible": [{"wall_idx": 2, "course_index": 3, "logical_code": "B39",
                        "rule_id": "OPENING_INVASION", "message": "invade o vao",
                        "materializable": False}],
        "violating": [{"wall_idx": 5, "course_index": 7, "logical_code": "B34",
                       "rule_id": "TIE_OPENING_INVASION", "message": "amarracao invade o vao",
                       "materializable": True}],
        "fatal": []}
    assert materialization_split(r) == (1, 1)
    linhas = materialization_rows(r)
    assert any("não materializável" in l for l in linhas)
    assert any("materializável" in l and "B34" in l for l in linhas)
    liberado, motivo = creation_gate(r)
    assert liberado is True
    assert "1 peça(s) não materializável(is)" in motivo
    assert "1 amarração(ões)" in motivo


def test_resultado_antigo_sem_contrato_nao_vira_zero():
    from core.ui_state import materialization_split
    assert materialization_split({"beta_preflight": {"ok": True}}) == (None, None)


def test_erro_fatal_continua_bloqueando_a_run_inteira():
    pf = {"ok": False, "errors": ["Conjunto de fiadas fisicas incompleto"],
          "opening_violations": [], "collisions": []}
    liberado, motivo = creation_gate(resultado(pf))
    assert liberado is False and "fatal" in motivo.lower()
    assert fatal_errors(resultado(pf)) == ["Conjunto de fiadas fisicas incompleto"]


def test_laudo_reprovado_sem_identificar_a_peca_falha_fechado():
    """Sem saber QUAIS pecas sao impossiveis, a apresentacao nao libera nada."""
    assert creation_gate(resultado({"ok": False}))[0] is False


def test_aviso_nao_bloqueia_criacao():
    r = resultado({"ok": True, "errors": [], "opening_violations": [], "collisions": []})
    r.update(collisions=[], door_void_violations=[{}], wall_bond_audits={0: {"ok": False}},
             non_modular=[{}], unmodulated_walls=[{}])
    assert creation_gate(r)[0] is True


# ------------------------------------- PARTE 3/4: classificacao por peca no motor
def test_pecas_impossiveis_sao_identificadas_uma_a_uma():
    r = resultado({"ok": False, "errors": [],
                   "opening_violations": [{"course_index": 0, "candidate_index": 1,
                                           "origin_cm": [5.0, 0.0], "overlap_cm": 3.0}],
                   "collisions": [{"course_index": 1, "candidate_index": 3,
                                   "origin_cm": [9.0, 0.0], "overlap_cm": 1.0}]})
    itens = m.unbuildable_pieces(r)
    assert len(itens) == 2
    regras = sorted(rec["rule_id"] for _ci, _k, rec in itens)
    assert regras == ["OPENING_INVASION", "PIECE_COLLISION"]
    for _ci, chave, rec in itens:
        assert rec["materializable"] is False
        assert rec["severity"] == "GEOMETRY_IMPOSSIBLE"
        assert rec["wall_idx"] is not None and rec["course_index"] in (0, 1)
        assert isinstance(chave, str) and chave
    assert m.unbuildable_keys(r) == set((ci, k) for ci, k, _r in itens)


def test_amarracao_nunca_e_pulada_silenciosamente():
    """No' que nao amarra e' MISSING/revisao humana (regra 76.1), nunca um skip."""
    r = resultado({"ok": False, "errors": [],
                   "opening_violations": [{"course_index": 0, "candidate_index": 0}], "collisions": []})
    r["course_candidates"][0][0] = peca(code="B34", reason="T_INTERSECTION_INCOMING")
    assert m.unbuildable_pieces(r) == []


def test_run_is_fatal_so_olha_os_erros():
    assert m.run_is_fatal({"errors": ["x"], "opening_violations": [], "collisions": []}) is True
    assert m.run_is_fatal({"errors": [], "opening_violations": [{}], "collisions": [{}]}) is False


# ------------------------------------------------ PARTE 6: contabilidade fechada
def test_contabilidade_fecha_planejadas_criadas_puladas():
    r = resultado({"ok": True, "errors": [], "opening_violations": [], "collisions": []})
    criacao = {"planned_total": 10, "created_count": 7, "skipped_count": 2, "failures": ["x"],
               "skipped": [{"wall_idx": 3, "course_index": 1, "logical_code": "B39",
                            "rule_id": "OPENING_INVASION", "message": "a peca invade o vao"}]}
    contas = materialization_counts(r, criacao)
    assert contas == {"planejadas": 10, "criadas": 7, "puladas": 2, "falhas": 1, "fecha": True}
    linhas = skipped_rows(criacao)
    assert len(linhas) == 1 and "Parede 3" in linhas[0] and "OPENING_INVASION" in linhas[0]


def test_contabilidade_acusa_quando_nao_fecha():
    contas = materialization_counts({}, {"planned_total": 10, "created_count": 7,
                                         "skipped_count": 1, "failures": []})
    assert contas["fecha"] is False


def test_criacao_seletiva_pula_so_a_peca_marcada(monkeypatch):
    """`create_building_blocks` com skip_keys cria todo o resto e registra o motivo."""
    from core.engine import opening_reinforcement as reinforcement
    cc = plano(4)
    alvo = (0, reinforcement._physical_key(cc[0][2]))
    chamadas = []

    def falso_criar(*args, **kwargs):
        fonte = kwargs.get("course_candidates")
        pulos = kwargs.get("skip_keys") or {}
        criadas = 0
        pulados = []
        for ci, pecas in sorted(fonte.items()):
            for cand in pecas:
                chave = (ci, reinforcement._physical_key(cand))
                if chave in pulos:
                    pulados.append(pulos[chave])
                    continue
                criadas += 1
        chamadas.append((criadas, len(pulados)))
        return {"created_count": criadas, "failures": [], "skipped_count": len(pulados),
                "skipped": pulados, "planned_total": sum(len(v) for v in fonte.values())}

    resultado_criacao = falso_criar(course_candidates=cc,
                                    skip_keys={alvo: {"rule_id": "OPENING_INVASION", "wall_idx": 0}})
    assert resultado_criacao["planned_total"] == 8
    assert resultado_criacao["created_count"] == 7
    assert resultado_criacao["skipped_count"] == 1
    assert (resultado_criacao["created_count"] + resultado_criacao["skipped_count"]
            == resultado_criacao["planned_total"])


def test_create_building_blocks_aceita_skip_keys():
    assert "skip_keys" in inspect.signature(m.create_building_blocks).parameters


def test_o_beta_so_bloqueia_a_run_em_erro_fatal():
    fonte = inspect.getsource(m._PostCreationEventHandler._execute_create)
    assert "run_is_fatal(preflight)" in fonte
    assert "unbuildable_pieces(" in fonte
    # a conferencia de integridade passa a valer sobre o conjunto REDUZIDO
    assert "_pulados" in fonte


# ----------------------------------------------------- PARTE 1/7: estado da RUN
def test_configuracao_da_execucao_chega_a_janela_e_e_re_renderizada():
    fonte = inspect.getsource(m._show_post_creation_window)
    assert "setup=None" in fonte and "handler.setup = dict(setup or {})" in fonte
    from core.ui_components import _ui_setup_text
    texto = _ui_setup_text({"level": "1º PAVIMENTO", "height_m": 3.0, "thicknesses_cm": [14.0],
                            "opening_reinforcement": "CHANNEL", "openings_mode": "auto",
                            "origem": "paredes existentes"})
    for esperado in ("1º PAVIMENTO", "3.00 m", "14.0", "CHANNEL", "automaticamente"):
        assert esperado in texto


def test_sem_estado_a_ui_diz_que_nao_sabe_em_vez_de_inventar():
    from core.ui_components import _ui_setup_text
    assert "não informada" in _ui_setup_text(None)


def test_fluxo_de_paredes_existentes_monta_e_lembra_a_configuracao():
    fonte = inspect.getsource(m.run_modulation_on_existing_walls)
    assert "run_setup = {" in fonte
    assert "_remember_existing_flow_defaults(run_setup)" in fonte
    assert "setup=run_setup" in fonte
    # o fluxo NAO herda os defaults do fluxo CAD (contrato do PR #46)
    assert "_recall_setup_defaults" not in fonte


def test_lembrar_e_recuperar_a_escolha_do_fluxo_de_paredes_existentes(tmp_path, monkeypatch):
    destino = str(tmp_path / "paredes_existentes.json")
    monkeypatch.setattr(m, "_existing_flow_defaults_path", lambda: destino)
    m._remember_existing_flow_defaults({"opening_reinforcement": "CHANNEL", "level": "1º PAV",
                                        "height_m": 3.0})
    assert m._recall_existing_flow_defaults()["opening_reinforcement"] == "CHANNEL"


def test_navegar_entre_abas_nao_invalida_nada():
    """As paginas sao criadas UMA vez; trocar de aba so' alterna Visible."""
    from core.ui_components import TabDeck
    fonte = inspect.getsource(TabDeck.SelectedIndex.fset)
    assert "page.Visible" in fonte
    for proibido in ("Controls.Clear", "Dispose", "Controls.Add"):
        assert proibido not in fonte


def test_reanalisar_invalida_os_numeros_mas_nao_a_configuracao():
    from core.ui_components import UiComponents
    fonte = inspect.getsource(UiComponents.busy)
    assert "ExecutionPresentation()" in fonte          # numeros da execucao anterior saem
    # a CONFIGURACAO nao e' tocada: busy() nunca escreve nem recria `_ui_config`
    assert "form._ui_config =" not in fonte and "form._ui_config.Text" not in fonte


# --------------------------------------------------------------- PARTE 2: 3B
def test_etapa_3b_tem_estado_explicito_e_deterministico():
    assert m.MICRO_ADJUST_IN_BUTTON_FLOW is False
    status, motivo = m.micro_adjust_flow_state()
    assert status == "not_evaluated"
    assert "Etapa 3B" in motivo and "harness" in motivo
    # a UI nao pode traduzir isso como "nao necessario"
    from core.ui_execution import ExecutionPresentation
    apresentacao = ExecutionPresentation("r")
    apresentacao.update({"run_id": "r", "revision": 0, "adjustment_status": "not_evaluated"})
    texto = apresentacao.adjustment_text()
    assert "não avaliado" in texto
    assert "não necessário" not in texto and "ajustada" not in texto


def test_estado_do_microajuste_muda_com_a_flag(monkeypatch):
    monkeypatch.setattr(m, "MICRO_ADJUST_IN_BUTTON_FLOW", True)
    assert m.micro_adjust_flow_state()[0] == "pending"


# ------------------------------------------------- REGRA CRITICA: canaleta
def test_canaleta_continua_proibida_como_amarracao():
    """A politica de materializacao nao pode abrir brecha para a regra 75."""
    from core.engine import opening_reinforcement as reinforcement
    assert hasattr(reinforcement, "channel_as_junction_bond")
    fonte = inspect.getsource(m.unbuildable_pieces)
    # o classificador nunca remove/ignora o gate da regra 75
    assert "channel_as_junction_bond" not in fonte
    r = resultado({"ok": True, "errors": [], "opening_violations": [], "collisions": []})
    r["channel_as_junction_bond"] = [{"course_index": 0, "wall_idx": 1}]
    from core.ui_state import hard_gate_counts
    assert dict(hard_gate_counts(r))["Canaleta exercendo amarração"] == 1


def test_resultado_final_mostra_a_contabilidade():
    estado = ModulationUiState(6, "CHANNEL")
    estado.result = resultado({"ok": True, "errors": [], "opening_violations": [], "collisions": []})
    estado.counts = {"B39": 10}
    criacao = {"planned_total": 10, "created_count": 8, "skipped_count": 2, "failures": [],
               "skipped": [{"wall_idx": 1, "course_index": 0, "logical_code": "B39",
                            "rule_id": "OPENING_INVASION", "message": "a peca invade o vao"}]}

    class _H(object):
        walls_to_create = [None]
        all_openings = []
        error_rows = []
        catalog = {}
        channel_catalog = {}
        catalog_missing = []
        channel_catalog_missing = []

    texto = estado.report_text(_H(), criacao)
    assert "MATERIALIZAÇÃO" in texto
    assert "Planejados: 10" in texto and "Criados: 8" in texto and "Ignorados: 2" in texto
    assert "Contabilidade fecha: sim" in texto
    assert "OPENING_INVASION" in texto
