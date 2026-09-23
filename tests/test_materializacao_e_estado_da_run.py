# -*- coding: utf-8 -*-
"""Regressao da rodada de 2026-09-23 (execucao real do usuario no Revit) e a
politica da OPCAO A escolhida pelo usuario para o PR #49.

Regra 48 SEM EXCECAO: nenhuma peca (B19/B34/B39/B54/compensador/canaleta/
comum/amarracao) ocupa o volume real de uma abertura. A peca que invade NAO e'
criada; se era amarracao, o no'/fiada fica AMARRACAO NAO RESOLVIDA com revisao
humana obrigatoria. Erro FATAL do plano continua bloqueando a RUN inteira.
"RUN executavel" e "modulacao estruturalmente resolvida" sao coisas diferentes.

Os casos A..H pedidos pelo usuario estao nomeados um a um. Os de materializacao
rodam o handler REAL (`_execute_create`) com dubles transacionais e uma porta
real na geometria, e medem o que de fato foi criado.
"""
import inspect
from types import SimpleNamespace

import pytest

import load_script

m = load_script.load()
import Autodesk.Revit.DB as DB
from core.engine import opening_reinforcement as reinforcement
from core.engine import wall_stepper as stepper
from core.ui_state import (creation_gate, localized_blockers, fatal_errors, materialization_counts,
                           skipped_rows, ModulationUiState)
from test_beta_atomic_creation import Transaction, Document
from test_controlled_beta_preflight import CATALOG, ft, seg


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


# ---- geometria REAL: parede de 199 cm com uma PORTA sem peitoril em x=30..80
PORTA = (30, 80, 0, 210)
COMPRIMENTO = {"B19": 19, "B34": 34, "B39": 39, "B54": 54, "C09": 9, "C04": 4}
TIE = "T_INTERSECTION_DEGRADED_L"          # papel de no' dado pelo solver (no' 41 real)


def bloco(x, code="B34", reason=TIE, node=5, wall=0):
    return {"wall_idx": wall, "logical_code": code, "length_cm": COMPRIMENTO[code],
            "width_cm": 14, "course": "A", "course_variant": 0,
            "origin_world": m.XYZ(ft(x), 0, 0), "x_dir": m.XYZ(1, 0, 0), "y_dir": m.XYZ(0, 1, 0),
            "node_index": node, "placement_reason": reason}


def cenario(pecas_por_fiada, porta=PORTA):
    fiadas = len(pecas_por_fiada)
    cc = dict((ci, list(p)) for ci, p in enumerate(pecas_por_fiada))
    result = {"num_courses": fiadas, "candidates": cc[0], "course_candidates": cc}
    walls = [(seg(0, 0, 199, 0), ft(14), (False, False))]
    openings = [[tuple(ft(v) for v in porta)]] if porta else [[]]
    return result, walls, openings


@pytest.fixture
def beta(monkeypatch):
    """Handler REAL do beta com dubles transacionais (mesmos de test_beta_atomic_creation)."""
    status = SimpleNamespace(**{s: s for s in ("Started", "Committed", "RolledBack", "Uninitialized")})
    monkeypatch.setattr(DB, "TransactionStatus", status, raising=False)
    monkeypatch.setattr(m, "Transaction", Transaction)
    monkeypatch.setattr(m, "TransactionGroup", Transaction)

    def montar(pecas_por_fiada, porta=PORTA):
        handler = m._PostCreationEventHandler()
        handler.controlled_beta = True
        result, walls, openings = cenario(pecas_por_fiada, porta)
        handler.solve_result, handler.walls_to_create, handler.openings_per_wall = result, walls, openings
        handler.catalog = dict((k, dict(v, symbol=SimpleNamespace(IsActive=True))) for k, v in CATALOG.items())
        handler.create_result = {"created_count": 1, "created_instances": [{"id": 99}]}
        result["beta_input_signature"] = handler._beta_input_signature()
        handler._save_modulation_state_cache = lambda: None
        handler.on_done = lambda *args: None
        return handler
    return montar


def pecas_criadas(handler):
    """(fiada, candidato) de cada instancia que o Revit (duble) realmente recebeu."""
    chaves = set((i["course_index"], i["candidate_key"]) for i in handler.create_result["created_instances"])
    return [(ci, c) for ci, pecas in handler.solve_result["course_candidates"].items()
            for c in pecas if (ci, id(c)) in chaves]


def invasoes_de_porta(handler, criadas):
    """Medicao independente do plano: OBB de cada peca CRIADA contra o vao real."""
    vaos = [m._door_void_obb(wi, handler.walls_to_create, op[0], op[1])
            for wi, ops in enumerate(handler.openings_per_wall) for op in ops]
    return [(ci, c["logical_code"]) for ci, c in criadas for vao in vaos
            if m._obb_min_overlap(m._candidate_obb(c), vao) > m.BOND_COLLISION_EPS_FT]


def conta_fecha(criacao):
    return criacao["planned_total"] == (criacao["created_count"] + criacao["skipped_count"]
                                        + criacao["failed_count"])


CAMPOS_DO_PULO = ("wall_idx", "course_index", "logical_code", "rule_id", "message", "overlap_cm",
                  "opening_index", "structural_role", "requires_human_review")


# ======================================================= OPCAO A - casos A..H
def test_caso_A_peca_comum_que_invade_porta_nao_e_criada(beta):
    handler = beta([[bloco(40, "B39", "STANDARD_FILL"), bloco(100, "B39", "STANDARD_FILL")]])
    handler._execute_create(Document())
    criacao = handler.create_result
    assert criacao["created_count"] == 1 and criacao["skipped_count"] == 1
    pulo, = criacao["skipped"]
    assert pulo["rule_id"] == m.OPENING_INVASION_RULE_ID and pulo["created"] is False
    assert pulo["structural_role"] is None and pulo["requires_human_review"] is False
    assert criacao["unresolved_bonds"] == [] and criacao["structurally_resolved"] is True
    assert invasoes_de_porta(handler, pecas_criadas(handler)) == []


def test_caso_B_amarracao_real_que_invade_porta_nao_e_criada_e_fica_nao_resolvida(beta):
    """O no' 41 do modelo real: B34 T_INTERSECTION_DEGRADED_L, 0,5 cm dentro da porta."""
    handler = beta([[bloco(40, node=41), bloco(100, "B39", "STANDARD_FILL")],
                    [bloco(40, node=41), bloco(100, "B39", "STANDARD_FILL")]])
    handler._execute_create(Document())
    criacao = handler.create_result
    assert criacao["created_count"] == 2 and criacao["skipped_count"] == 2
    assert all(c["logical_code"] == "B39" for _ci, c in pecas_criadas(handler))
    assert criacao["structurally_resolved"] is False
    assert sorted(b["course_index"] for b in criacao["unresolved_bonds"]) == [0, 1]
    for pendencia in criacao["unresolved_bonds"]:
        assert pendencia["status"] == m.BOND_UNRESOLVED_STATUS
        assert pendencia["requires_human_review"] is True
        assert pendencia["node_index"] == 41 and pendencia["structural_role"] == TIE
        assert pendencia["rejected_rule"] == m.OPENING_INVASION_RULE_ID
        assert pendencia["overlap_cm"] > 0 and pendencia["opening_index"] == 0
    for pulo in criacao["skipped"]:
        for campo in CAMPOS_DO_PULO:
            assert campo in pulo, campo
        assert pulo["requires_human_review"] is True and pulo["structural_role"] == TIE
    assert invasoes_de_porta(handler, pecas_criadas(handler)) == []


def test_caso_C_b34_sem_papel_de_amarracao_nao_e_amarracao():
    for razao in ("STANDARD_FILL", "OPENING_JAMB", "", None):
        assert m.structural_bond_role({"logical_code": "B34", "placement_reason": razao}) is None
    assert m.structural_bond_role({"logical_code": "B34", "placement_reason": TIE}) == TIE


def test_caso_D_b54_sem_papel_de_amarracao_nao_e_amarracao():
    assert m.structural_bond_role({"logical_code": "B54", "placement_reason": "STANDARD_FILL"}) is None
    assert m.structural_bond_role({"logical_code": "B54", "placement_reason": "L_CORNER"}) == "L_CORNER"


def test_casos_C_D_fechamento_b34_b54_invadindo_porta_e_so_pulado(beta):
    handler = beta([[bloco(40, "B34", "STANDARD_FILL")], [bloco(40, "B54", "STANDARD_FILL")]])
    handler._execute_create(Document())
    criacao = handler.create_result
    assert criacao["created_count"] == 0 and criacao["skipped_count"] == 2
    assert criacao["unresolved_bonds"] == []
    assert all(p["structural_role"] is None for p in criacao["skipped"])


def test_caso_E_compensador_da_regra_76_1_nao_e_amarracao():
    razao = stepper.JUNCTION_UNRESOLVED_FILL_REASON
    for code in ("B34", "B54", "C09", "C04", "B19"):
        assert m.structural_bond_role({"logical_code": code, "placement_reason": razao}) is None
    # outros codigos com razao de no' tambem nao amarram (regra 76: so' B34/B54)
    for code in ("B19", "B39", "C09", "C04", "CHANNEL_U_39"):
        assert m.structural_bond_role({"logical_code": code, "placement_reason": TIE}) is None


def test_caso_E_compensador_76_1_invadindo_porta_e_pulado_sem_virar_amarracao(beta):
    handler = beta([[bloco(40, "C09", stepper.JUNCTION_UNRESOLVED_FILL_REASON, node=41),
                     bloco(100, "B39", "STANDARD_FILL")]])
    handler._execute_create(Document())
    criacao = handler.create_result
    assert criacao["skipped_count"] == 1 and criacao["created_count"] == 1
    assert criacao["unresolved_bonds"] == []
    assert criacao["skipped"][0]["structural_role"] is None


def test_caso_F_erro_localizado_de_porta_nao_derruba_as_demais_pecas(beta):
    validas = [bloco(100, "B39", "STANDARD_FILL"), bloco(150, "B39", "STANDARD_FILL")]
    handler = beta([[bloco(40)] + validas, [bloco(40, "B39", "STANDARD_FILL")] + validas])
    handler._execute_create(Document())
    criacao = handler.create_result
    assert criacao["planned_total"] == 6
    assert criacao["created_count"] == 4 and criacao["skipped_count"] == 2
    assert conta_fecha(criacao)
    assert handler.create_result["created_instances"][0]["id"] != 99   # lote novo publicado


def test_caso_G_erro_fatal_continua_bloqueando_a_run_inteira(beta):
    handler = beta([[bloco(100, "B39", "STANDARD_FILL")]])
    anterior = handler.create_result
    handler.solve_result["course_candidates"] = {}          # plano fisico incompleto -> FATAL
    handler.solve_result["beta_input_signature"] = handler._beta_input_signature()
    doc = Document()
    with pytest.raises(ValueError, match="erro fatal do plano"):
        handler._execute_create(doc)
    assert handler.create_result is anterior and set(doc.elements) == {99}
    assert doc.transactions == []                             # nem abriu transacao


def test_caso_G_classificacao_errada_vira_fatal_e_nunca_criacao_parcial(beta, monkeypatch):
    """Invariante: se o conjunto que sobra ainda invade porta, nada e' criado."""
    handler = beta([[bloco(40), bloco(100, "B39", "STANDARD_FILL")]])
    anterior = handler.create_result
    monkeypatch.setattr(m, "materialization_plan",
                        lambda *a, **k: {"skip": [], "unresolved_bonds": [], "fatal": []})
    doc = Document()
    with pytest.raises(ValueError, match="ainda invadem abertura"):
        handler._execute_create(doc)
    assert handler.create_result is anterior and set(doc.elements) == {99}


def test_caso_H_nenhuma_peca_ocupa_porta_depois_da_materializacao(beta):
    """Uma peca de cada tipo, todas invadindo a porta, em fiadas distintas."""
    fiadas = [[bloco(40, code, razao), bloco(100, "B39", "STANDARD_FILL")] for code, razao in (
        ("B34", TIE), ("B54", "X_INTERSECTION"), ("B34", "STANDARD_FILL"), ("B54", "STANDARD_FILL"),
        ("B39", "STANDARD_FILL"), ("B19", "OPENING_JAMB"), ("C09", stepper.JUNCTION_UNRESOLVED_FILL_REASON),
        ("C04", "STANDARD_FILL"))]
    handler = beta(fiadas)
    antes = m.controlled_beta_preflight(handler.solve_result, handler.walls_to_create,
                                        handler.openings_per_wall, handler.catalog, 0.0)
    assert len(antes["opening_violations"]) == 8               # a porta e' invadida de fato
    handler._execute_create(Document())
    criadas = pecas_criadas(handler)
    assert len(criadas) == 8 and all(c["logical_code"] == "B39" for _ci, c in criadas)
    assert invasoes_de_porta(handler, criadas) == []           # PECAS EM PORTA = ZERO
    assert len(handler.create_result["unresolved_bonds"]) == 2   # so' as duas amarracoes reais
    assert conta_fecha(handler.create_result)


# ------------------------------------------------- politica (sem Revit)
def test_violacao_localizada_nao_bloqueia_a_run_inteira():
    pf = {"ok": False, "errors": [],
          "opening_violations": [{"course_index": 0, "candidate_index": 2, "origin_cm": [10.0, 0.0]}],
          "collisions": []}
    r = resultado(pf)
    liberado, motivo = creation_gate(r)
    assert liberado is True
    assert "Criar blocos" in motivo and "registrad" in motivo
    assert localized_blockers(r) == 1


def test_toda_invasao_de_abertura_vira_pulo_sem_excecao_de_amarracao():
    pf = {"ok": False, "errors": [],
          "opening_violations": [{"course_index": 0, "candidate_index": 0, "overlap_cm": 0.5,
                                  "opening_index": 1},
                                 {"course_index": 1, "candidate_index": 1, "overlap_cm": 0.5,
                                  "opening_index": 1}],
          "collisions": []}
    r = resultado(pf)
    r["course_candidates"][0][0] = dict(peca(code="B34", reason=TIE), node_index=41)
    plano_m = m.materialization_plan(r, pf)
    assert set(plano_m) == {"skip", "unresolved_bonds", "fatal"}
    assert len(plano_m["skip"]) == 2                  # as duas saem, amarracao inclusive
    for _ci, _k, rec in plano_m["skip"]:
        assert rec["materializable"] is False and rec["created"] is False
        assert rec["rule_id"] == m.OPENING_INVASION_RULE_ID
    pendencia, = plano_m["unresolved_bonds"]
    assert pendencia["node_index"] == 41 and pendencia["course_index"] == 0
    assert pendencia["requires_human_review"] is True and pendencia["overlap_cm"] == 0.5
    assert pendencia["opening_index"] == 1


def test_colisao_pula_uma_peca_e_preserva_a_amarracao_se_a_outra_nao_for():
    pf = {"ok": False, "errors": [], "opening_violations": [],
          "collisions": [{"course_index": 0, "candidate_index": 0, "other_candidate_index": 1,
                          "overlap_cm": 1.0}]}
    r = resultado(pf)
    r["course_candidates"][0][0] = peca(code="B34", reason=TIE)
    (ci, _k, rec), = m.unbuildable_pieces(r, pf)
    assert rec["rule_id"] == m.PIECE_COLLISION_RULE_ID and rec["structural_role"] is None
    assert rec["collides_with_candidate_index"] == 0
    assert m.materialization_plan(r, pf)["unresolved_bonds"] == []


def test_mesma_peca_com_dois_motivos_e_pulada_uma_vez():
    pf = {"ok": False, "errors": [],
          "opening_violations": [{"course_index": 0, "candidate_index": 2}],
          "collisions": [{"course_index": 0, "candidate_index": 2, "other_candidate_index": 3}]}
    (_ci, _k, rec), = m.unbuildable_pieces(resultado(pf), pf)
    assert rec["rules"] == [m.OPENING_INVASION_RULE_ID, m.PIECE_COLLISION_RULE_ID]


def test_pecas_impossiveis_sao_identificadas_uma_a_uma():
    r = resultado({"ok": False, "errors": [],
                   "opening_violations": [{"course_index": 0, "candidate_index": 1,
                                           "origin_cm": [5.0, 0.0], "overlap_cm": 3.0}],
                   "collisions": [{"course_index": 1, "candidate_index": 3,
                                   "origin_cm": [9.0, 0.0], "overlap_cm": 1.0}]})
    itens = m.unbuildable_pieces(r)
    assert len(itens) == 2
    regras = sorted(rec["rule_id"] for _ci, _k, rec in itens)
    assert regras == [m.OPENING_INVASION_RULE_ID, m.PIECE_COLLISION_RULE_ID]
    for _ci, chave, rec in itens:
        assert rec["severity"] == "GEOMETRY_IMPOSSIBLE"
        assert rec["wall_idx"] is not None and rec["course_index"] in (0, 1)
        assert isinstance(chave, str) and chave
    assert m.unbuildable_keys(r) == set((ci, k) for ci, k, _r in itens)


def test_run_is_fatal_so_olha_os_erros():
    assert m.run_is_fatal({"errors": ["x"], "opening_violations": [], "collisions": []}) is True
    assert m.run_is_fatal({"errors": [], "opening_violations": [{}], "collisions": [{}]}) is False


def test_resultado_antigo_sem_contrato_nao_vira_zero():
    from core.ui_state import materialization_split
    assert materialization_split({"beta_preflight": {"ok": True}}) == (None, None)


def test_erro_fatal_continua_bloqueando_na_apresentacao():
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


def test_contrato_de_materializacao_chega_a_apresentacao():
    from core.ui_state import materialization_split, materialization_rows, review_items
    r = resultado({"ok": False, "errors": [], "opening_violations": [], "collisions": []})
    r["materialization"] = {
        "skipped": [{"wall_idx": 2, "course_index": 3, "logical_code": "B39",
                     "rule_id": "OPENING_VOID_INVASION", "message": "invade o vao", "overlap_cm": 0.5,
                     "structural_role": None},
                    {"wall_idx": 5, "course_index": 7, "logical_code": "B34",
                     "rule_id": "OPENING_VOID_INVASION", "message": "invade o vao", "overlap_cm": 0.5,
                     "structural_role": TIE}],
        "unresolved_bonds": [{"node_index": 41, "course_index": 7, "logical_code": "B34",
                              "structural_role": TIE, "rejected_rule": "OPENING_VOID_INVASION"}],
        "fatal": []}
    assert materialization_split(r) == (2, 1)
    linhas = materialization_rows(r)
    assert len(linhas) == 2 and all("não será criada" in l for l in linhas)
    assert any("AMARRAÇÃO" in l and "revisão humana" in l for l in linhas)
    liberado, motivo = creation_gate(r)
    assert liberado is True
    assert "2 peça(s) não serão criadas" in motivo
    assert "1 amarração(ões) ficarão NÃO RESOLVIDAS" in motivo
    assert any("NÃO resolvida (nó 41), fiada 7" in item["text"] for item in review_items(r))


def test_o_beta_so_bloqueia_a_run_em_erro_fatal():
    fonte = inspect.getsource(m._PostCreationEventHandler._execute_create)
    assert "run_is_fatal(preflight)" in fonte
    assert "materialization_plan(" in fonte and "verify_materialization(" in fonte


# ------------------------------------------------ contabilidade fechada
def test_contabilidade_fecha_planejadas_criadas_puladas_falhas():
    r = resultado({"ok": True, "errors": [], "opening_violations": [], "collisions": []})
    criacao = {"planned_total": 10, "created_count": 7, "skipped_count": 2, "failed_count": 1,
               "failures": ["x"],
               "skipped": [{"wall_idx": 3, "course_index": 1, "logical_code": "B39",
                            "rule_id": "OPENING_VOID_INVASION", "message": "a peca invade o vao"}]}
    contas = materialization_counts(r, criacao)
    assert contas == {"planejadas": 10, "criadas": 7, "puladas": 2, "falhas": 1, "fecha": True}
    linhas = skipped_rows(criacao)
    assert len(linhas) == 1 and "Parede 3" in linhas[0] and "OPENING_VOID_INVASION" in linhas[0]


def test_contabilidade_acusa_quando_nao_fecha():
    contas = materialization_counts({}, {"planned_total": 10, "created_count": 7,
                                         "skipped_count": 1, "failures": []})
    assert contas["fecha"] is False


def test_falha_contada_por_peca_e_nao_por_mensagem():
    contas = materialization_counts({}, {"planned_total": 10, "created_count": 5, "skipped_count": 2,
                                         "failed_count": 3, "failures": ["3 pecas falharam"]})
    assert contas["falhas"] == 3 and contas["fecha"] is True


def test_familia_ausente_e_pulo_registrado_e_amarracao_fica_nao_resolvida():
    """Sem catalogo para o tipo, a peca vira pulo com motivo - nunca some calada."""
    from test_script import revit_stubs, _real_catalog_entry
    candidatos = [bloco(100, "B39", "STANDARD_FILL"), bloco(150, "B34", TIE, node=7)]
    criacao = m.create_building_blocks(
        revit_stubs._StubDoc(), candidatos, {"B39": _real_catalog_entry("B39")}, base_z_abs=0.0,
        selected_level=revit_stubs._Inert(), num_courses=1, course_candidates={0: candidatos})
    assert criacao["created_count"] == 1 and conta_fecha(criacao)
    pulo, = criacao["skipped"]
    assert pulo["rule_id"] == "MISSING_FAMILY" and pulo["requires_human_review"] is True
    assert pulo["structural_role"] == TIE and pulo["node_index"] == 7


def test_create_building_blocks_aceita_skip_keys():
    assert "skip_keys" in inspect.signature(m.create_building_blocks).parameters


# ------------------------------------------------- REGRA CRITICA: canaleta
def test_canaleta_nunca_vira_amarracao_na_materializacao():
    """Regra 75: a canaleta nao ganha papel de amarracao nem com razao de no'."""
    for code in sorted(reinforcement.CHANNEL_LOGICAL_TYPES):
        assert m.structural_bond_role({"logical_code": code, "placement_reason": TIE}) is None
    fonte = inspect.getsource(m.materialization_plan) + inspect.getsource(m.structural_bond_role)
    assert "channel_as_junction_bond" not in fonte       # o gate da regra 75 nao e' tocado


def test_gate_da_regra_75_continua_acusando_canaleta_com_papel_de_no():
    cc = {0: [{"logical_code": "CHANNEL_U_39", "placement_reason": TIE, "wall_idx": 0}]}
    violacoes = reinforcement.channel_as_junction_bond(cc)
    assert violacoes and violacoes[0]["kind"] == "CHANNEL_PIECE_WITH_TIE_ROLE"
    r = resultado({"ok": True, "errors": [], "opening_violations": [], "collisions": []})
    r["channel_as_junction_bond"] = [{"course_index": 0, "wall_idx": 1}]
    from core.ui_state import hard_gate_counts
    assert dict(hard_gate_counts(r))["Canaleta exercendo amarração"] == 1


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
    assert "form._ui_config =" not in fonte and "form._ui_config.Text" not in fonte


# --------------------------------------------------------------- PARTE 2: 3B
def test_etapa_3b_tem_estado_explicito_e_deterministico():
    assert m.MICRO_ADJUST_IN_BUTTON_FLOW is False
    status, motivo = m.micro_adjust_flow_state()
    assert status == "not_evaluated"
    assert "Etapa 3B" in motivo and "harness" in motivo
    from core.ui_execution import ExecutionPresentation
    apresentacao = ExecutionPresentation("r")
    apresentacao.update({"run_id": "r", "revision": 0, "adjustment_status": "not_evaluated"})
    texto = apresentacao.adjustment_text()
    assert "não avaliado" in texto
    assert "não necessário" not in texto and "ajustada" not in texto


def test_estado_do_microajuste_muda_com_a_flag(monkeypatch):
    monkeypatch.setattr(m, "MICRO_ADJUST_IN_BUTTON_FLOW", True)
    assert m.micro_adjust_flow_state()[0] == "pending"


# ------------------------------------------------ resultado final na tela
class _H(object):
    walls_to_create = [None]
    all_openings = []
    error_rows = []
    catalog = {}
    channel_catalog = {}
    catalog_missing = []
    channel_catalog_missing = []


def test_resultado_final_mostra_a_contabilidade_e_o_estado_estrutural():
    estado = ModulationUiState(6, "CHANNEL")
    estado.result = resultado({"ok": True, "errors": [], "opening_violations": [], "collisions": []})
    estado.result["materialization"] = {
        "skipped": [], "fatal": [],
        "unresolved_bonds": [{"node_index": 41, "course_index": 0, "logical_code": "B34",
                              "structural_role": TIE, "rejected_rule": "OPENING_VOID_INVASION"}]}
    estado.counts = {"B39": 10}
    criacao = {"planned_total": 10, "created_count": 8, "skipped_count": 2, "failed_count": 0,
               "failures": [], "structurally_resolved": False,
               "skipped": [{"wall_idx": 1, "course_index": 0, "logical_code": "B39",
                            "rule_id": "OPENING_VOID_INVASION", "message": "a peca invade o vao"}]}
    texto = estado.report_text(_H(), criacao)
    assert "MATERIALIZAÇÃO" in texto
    assert "Planejados: 10" in texto and "Criados: 8" in texto and "Ignorados: 2" in texto
    assert "Contabilidade fecha: sim" in texto
    assert "OPENING_VOID_INVASION" in texto
    assert "ESTADO ESTRUTURAL" in texto and "RUN executada: sim" in texto
    assert "Modulação estruturalmente resolvida: NÃO" in texto
    assert "NÃO resolvida (nó 41)" in texto
