# -*- coding: utf-8 -*-
"""Secao 78 (ciclo 1, 2026-09-23): as tolerancias FISICAS de fechamento (30.8
absorcao no no' + 51.13 ruido de jamba, com a tentativa 30.9) valem para
QUALQUER estrategia de reforco de abertura - "Sem reforco" (None) inclusive.

Causa medida na comparacao forense BUTANTA (SCRIPT x MCP x HUMANO): com a
estrategia None o caminho legado transformava um residuo de poucos centimetros
em TRECHO INTEIRO VAZIO (224 trechos NON_MODULAR, 18.935 cm de parede sem bloco
em 12 fiadas); com CHANNEL os mesmos trechos fechavam. Reforco de abertura e
tolerancia fisica sao conceitos separados.

Os casos 1..8 sao os pedidos pelo usuario. Fixtures por geometria (anel de shaft
115 x 86 cm de test_node_bounded_residual, planta de grade do benchmark, parede
com porta) - nunca por ElementId.

    python3 -m pytest tests/test_tolerancias_fisicas_gerais.py -q
"""
import contextlib
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402
from test_node_bounded_residual import ring_lines, ring_window, solve, NUM_COURSES  # noqa: E402

m = sb.m
ft = sb.ft
seg = sb.seg
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402
from core.engine import continuous_modulation as cm  # noqa: E402
from core.ui_state import review_items, creation_gate, ModulationUiState  # noqa: E402


@contextlib.contextmanager
def tolerancias_fisicas(enabled):
    before = m.PHYSICAL_MODULATION_TOLERANCES_ENABLED
    m.PHYSICAL_MODULATION_TOLERANCES_ENABLED = enabled
    try:
        yield
    finally:
        m.PHYSICAL_MODULATION_TOLERANCES_ENABLED = before


def pieces_of(res, wall_idx):
    return [c for ci in sorted(res["course_candidates"]) for c in res["course_candidates"][ci] if c.get("wall_idx") == wall_idx]


def laid_cm(res, wall_idx, course):
    return sum(float(c.get("length_cm") or 0.0) for c in res["course_candidates"].get(course, []) if c.get("wall_idx") == wall_idx)


def keys(res):
    return [(ci, orf._physical_key(c)) for ci in sorted(res["course_candidates"]) for c in res["course_candidates"][ci]]


def anel_86(lines):
    """indices das paredes de 86 cm do anel (as verticais)"""
    return [i for i, l in enumerate(lines) if abs(l.GetEndPoint(0).X - l.GetEndPoint(1).X) < 1e-6]


# --------------------------------------------------------------- defaults
def test_interruptor_vale_para_toda_estrategia_e_chaves_do_modulo_seguem_desligadas():
    assert m.PHYSICAL_MODULATION_TOLERANCES_ENABLED is True
    assert m.CHANNEL_PHYSICAL_TOLERANCES_ENABLED is True          # alias do nome antigo
    # fora de uma chamada do solver, as chaves globais continuam desligadas
    assert ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED is False
    assert cm.JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED is False
    res, _w = solve(ring_lines(), [[], [], [], []], strategy=None)
    assert res["physical_modulation_tolerances"] is True
    assert ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED is False      # restaurado no finally
    assert cm.JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED is False


# ------------------------------------------------------------------ CASO 1
def test_caso_1_none_trecho_modular_resultado_igual():
    """Planta de grade (fecha em modulo): com e sem as tolerancias, as paredes
    que ja' fechavam e nao receberam absorcao ficam com EXATAMENTE as mesmas pecas."""
    runs = []
    for enabled in (False, True):
        nodes, walls, e2n, openings = sb.make_plan(3, 3)
        with tolerancias_fisicas(enabled):
            res = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings, sb.CATALOG, 0.0, NUM_COURSES,
                                                      variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
        runs.append((res, walls))
    (before, walls), (after, _w) = runs
    closed = set(range(len(walls))) - set(s["wall_idx"] for s in before["non_modular"])
    touched = set(a["wall_idx"] for a in after.get("residual_absorptions") or [])
    keep = closed - touched
    assert keep, "a grade tem paredes modulares"
    for wi in keep:
        assert [orf._physical_key(c) for c in pieces_of(before, wi)] == [orf._physical_key(c) for c in pieces_of(after, wi)]
    assert not [s for s in after["non_modular"] if s["wall_idx"] in keep]


# ------------------------------------------------------------------ CASO 2
def test_caso_2_none_residuo_pequeno_fecha_o_trecho():
    """Anel 115 x 86 (miolos 1 e 2 cm fora do modulo): com "Sem reforco" as
    paredes de 115 (folga 1 cm) fecham em TODAS as fiadas."""
    res, walls = solve(ring_lines(), [[], [], [], []], strategy=None)
    longas = [i for i in range(4) if i not in anel_86(ring_lines())]
    assert not [s for s in res["non_modular"] if s["wall_idx"] in longas]
    assert res["unresolved_spans"] == []
    for wi in longas:
        for ci in range(NUM_COURSES):
            assert laid_cm(res, wi, ci) >= 60.0, (wi, ci)
    assert res.get("residual_absorptions"), "a 30.8 absorveu a folga (com a tentativa 30.9)"


# ------------------------------------------------------------------ CASO 3
def test_caso_3_none_boneca_86_nao_deixa_buraco_grande():
    """Boneca de 86 cm entre dois cantos (miolo 70 cm, 2 cm fora do modulo):
    o MCP fecha com duas B34 e junta fisica. Com "Sem reforco" nenhuma fiada
    fica com buraco grande (antes: anel INTEIRO vazio)."""
    res, walls = solve(ring_lines(), [[], [], [], []], strategy=None)
    for wi in anel_86(ring_lines()):
        for ci in range(NUM_COURSES):
            assert laid_cm(res, wi, ci) >= 60.0, (wi, ci, laid_cm(res, wi, ci))
    assert not [s for s in res["non_modular"] if s["wall_idx"] in anel_86(ring_lines())]


def test_caso_3_antes_da_secao_78_o_anel_ficava_vazio():
    """Prova do problema: com o interruptor desligado, o mesmo anel fica sem bloco."""
    with tolerancias_fisicas(False):
        antes, _w = solve(ring_lines(), [[], [], [], []], strategy=None)
    depois, _w = solve(ring_lines(), [[], [], [], []], strategy=None)
    assert set(s["wall_idx"] for s in antes["non_modular"]) == set(range(4))   # as 4 paredes fora do modulo
    assert depois["non_modular"] == []
    # so' as pecas de canto sobravam: menos da metade da parede assentada
    assert sum(laid_cm(antes, wi, 0) for wi in range(4)) < 0.5 * sum(laid_cm(depois, wi, 0) for wi in range(4))


# ------------------------------------------------------------------ CASO 4
def test_caso_4_none_trecho_impossivel_fica_explicitamente_nao_resolvido():
    """Anel com paredes de 118 cm: folga de 4 cm (> 2 cm da 30.8). Nao inventa
    bloco, nao forca geometria: registra NON_MODULAR_UNRESOLVED com os campos,
    revisao humana, e a parede continua retida."""
    lines = [seg(537, 1000, 655, 1000), seg(537, 928, 655, 928), seg(544, 921, 544, 1007), seg(648, 921, 648, 1007)]
    res, walls = solve(lines, [[], [], [], []], strategy=None)
    longas = [s for s in res["non_modular"] if s["wall_idx"] in (0, 1)]
    assert longas, "4 cm continua fora da tolerancia fisica"
    spans = [s for s in res["unresolved_spans"] if s["wall_idx"] in (0, 1)]
    assert spans and len(spans) == len(longas)
    for span in spans:
        assert span["status"] == m.NON_MODULAR_UNRESOLVED_STATUS == "NON_MODULAR_UNRESOLVED"
        assert span["rule_id"] == m.NON_MODULAR_SPAN_RULE_ID and span["requires_human_review"] is True
        for campo in ("wall_idx", "wall_id", "course", "course_indices", "start_cm", "end_cm", "length_cm", "residual_cm", "reason"):
            assert campo in span, campo
        assert span["length_cm"] > 0 and span["end_cm"] > span["start_cm"]
        assert span["residual_cm"] is not None and span["residual_cm"] > ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_MAX_CM
        assert span["course_indices"], "fiadas fisicas do trecho"
    # nao some: aparece na revisao humana e a parede de referencia fica retida
    textos = [r["text"] for r in review_items(res)]
    assert any(u"Trecho NÃO resolvido" in t and "Eixo 0" in t for t in textos)
    m._record_unmodulated_walls(res, walls)
    assert any(w["wall_idx"] == 0 and w["reason"] == "NON_MODULAR_SPANS" for w in res["unmodulated_walls"])
    # e' pendencia localizada: nao bloqueia a RUN, mas avisa
    res["beta_preflight"] = {"ok": True, "errors": [], "opening_violations": [], "collisions": []}
    res["candidates"] = res["course_candidates"][0]
    liberado, motivo = creation_gate(res)
    assert liberado is True and u"NÃO resolvido" in motivo


# ------------------------------------------------------------------ CASO 5
def test_caso_5_channel_continua_valido():
    """Mesmos invariantes do teste verde do anel (regra 75: o canto fica, a
    canaleta nao assume amarracao) + os trechos que sobram sao so' os do
    recorte do vao, e vem registrados com `conflict`."""
    res, walls = solve(ring_lines(), ring_window(), strategy="CHANNEL")
    counts = res["opening_reinforcement"]["validation"]["counts"]
    assert counts["MISSING_REQUIRED_CHANNEL"] == 2 and counts["CHANNEL_INVADES_OPENING"] == 0
    assert res["channel_as_junction_bond"] == [] and res["opening_reinforcement"]["tie_conversions"] == []
    assert not [s for s in res["non_modular"] if s.get("conflict") is None]
    assert all(span["conflict"] is not None and "conflito com o recorte do vao" in span["reason"]
               for span in res["unresolved_spans"])
    assert res["residual_absorptions"]
    assert res.get("missing_required_junction_bond") is not None      # auditorias do fluxo CHANNEL


# ------------------------------------------------------------------ CASO 6
def test_caso_6_trocar_reforco_nao_muda_a_capacidade_fisica_de_fechar():
    sem, _w = solve(ring_lines(), [[], [], [], []], strategy=None)
    com, _w = solve(ring_lines(), [[], [], [], []], strategy="CHANNEL")
    assert sem["non_modular"] == [] and com["non_modular"] == []
    assert sem["unresolved_spans"] == [] and com["unresolved_spans"] == []
    for wi in range(4):
        for ci in range(NUM_COURSES):
            assert laid_cm(sem, wi, ci) >= 60.0 and laid_cm(com, wi, ci) >= 60.0


# ------------------------------------------------------------------ CASO 7
def test_caso_7_fechamento_com_tolerancia_nunca_invade_porta():
    """Parede com porta e residuo: as tolerancias nunca poem peca no vao
    (a jamba e a ponta ficam onde estao; regra 48 no laudo)."""
    lines = [seg(0, 0, 601, 0), seg(0, 0, 0, 300), seg(601, 0, 601, 300)]
    openings = [[(ft(200), ft(301), ft(0), ft(221))], [], []]
    res, walls = solve(lines, openings, strategy=None)
    pf = m.controlled_beta_preflight(res, walls, openings, sb.CATALOG, 0.0)
    assert pf["opening_violations"] == [] and pf["errors"] == []
    # o vao e' dado no eixo LOCAL da parede (que foi estendida ate' as faces dos
    # cantos): em mundo, o vao comeca em x0 + 200
    x0 = walls[0][0].GetEndPoint(0).X / sb.F * 100
    lo, hi = x0 + 200.0, x0 + 301.0
    for ci in range(11):
        for c in res["course_candidates"].get(ci, []):
            if c.get("wall_idx") != 0:
                continue
            x = c["origin_world"].X / sb.F * 100; half = float(c["length_cm"]) / 2.0
            assert x + half <= lo + 0.1 or x - half >= hi - 0.1, (ci, c["logical_code"], x, lo, hi)


# ------------------------------------------------------------------ CASO 8
def test_caso_8_canaleta_como_amarracao_continua_zero():
    sem, _w = solve(ring_lines(), ring_window(), strategy=None)
    com, _w = solve(ring_lines(), ring_window(), strategy="CHANNEL")
    assert orf.channel_as_junction_bond(sem["course_candidates"]) == []
    assert orf.channel_as_junction_bond(com["course_candidates"]) == []
    assert com.get("channel_as_junction_bond", []) == []


# ------------------------------------------------------------- relatorio/UI
def test_trecho_nao_resolvido_aparece_no_relatorio_e_no_estado_estrutural():
    lines = [seg(537, 1000, 655, 1000), seg(537, 928, 655, 928), seg(544, 921, 544, 1007), seg(648, 921, 648, 1007)]
    res, walls = solve(lines, [[], [], [], []], strategy=None)
    texto = m._format_block_solve_report(res, sb.CATALOG)
    texto = texto[0] if isinstance(texto, tuple) else texto
    assert "TRECHOS NAO RESOLVIDOS (NON_MODULAR_UNRESOLVED" in texto and "UNRESOLVED wall_id=" in texto
    estado = ModulationUiState(6, "NONE")
    res["beta_preflight"] = {"ok": True, "errors": [], "opening_violations": [], "collisions": []}
    estado.result = res

    class _H(object):
        walls_to_create = walls; all_openings = []; error_rows = []; catalog = {}; channel_catalog = {}
        catalog_missing = []; channel_catalog_missing = []
    criacao = {"planned_total": 1, "created_count": 1, "skipped_count": 0, "failed_count": 0, "failures": [],
               "skipped": [], "structurally_resolved": False, "unresolved_spans": res["unresolved_spans"]}
    rel = estado.report_text(_H(), criacao)
    assert u"Trechos NÃO resolvidos (sem bloco, revisão humana obrigatória): {}".format(len(res["unresolved_spans"])) in rel
    assert u"Modulação estruturalmente resolvida: NÃO" in rel
