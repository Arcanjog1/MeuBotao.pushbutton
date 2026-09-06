# -*- coding: utf-8 -*-
"""CR-BLOCK-FIT-TOLERANCE-C04 - GUARDA FISICA DE FRONTEIRA (resolucao do
hard blocker `OPENING_BLOCK_CROSSES_JAMB`).

O C04 alargou a tolerancia de FIT para 0,30cm (`PIER_FIT_TOLERANCE_CM`), o
que destrava trechos reais que o ruido geometrico acumulado fazia o solver
rejeitar. Mas o comprimento SNAPADO tambem posiciona as pecas: quando o
trecho real e' um pouco MENOR que o multiplo aceito, a ultima peca termina
DEPOIS do fim fisico do trecho. Contra uma junta de argamassa isso e'
inofensivo (a junta de 1cm cede a fracao de milimetro); contra uma
fronteira SEM junta - jamba de abertura, ponta livre, reserva de no' - a
peca invade o vao. Medido no corpus: 41 invasoes novas de 0,12 a 0,267cm.

A guarda separa as duas perguntas (ver PIER_PHYSICAL_FIT_TOLERANCE_CM):

    FIT/FEASIBILIDADE  0,30cm  "este trecho PODE ser modular?"
    COLOCACAO FISICA   0,05cm  "onde a peca PODE existir de fato?"

Esta suite exercita as FUNCOES DE PRODUCAO (`pier_cm_floored_to_module`,
`_layout_fitted_to_physical_span`, `_solve_repair_subsegments`) e o solver
COMPLETO (`solve_building_blocks_all_courses`) - nunca um helper inventado
so' para o teste. As geometrias usadas sao as MEDIDAS no corpus real
(TGD W044/W072/W075/W113, TP1 W029).

    python3 -m pytest tests/test_block_fit_tolerance_c04_jamb_guard.py -q
"""

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import load_script  # noqa: E402
import revit_stubs  # noqa: E402

m = load_script.load()
XYZ = revit_stubs.XYZ
Line = revit_stubs.Line

F = m.FEET_PER_METER
JOINT = m.BLOCK_JOINT_CM
MODULE = m.PIER_MODULE_CM
FIT_TOL = m.PIER_FIT_TOLERANCE_CM
PHYS_TOL = m.PIER_PHYSICAL_FIT_TOLERANCE_CM


def ft(cm):
    return cm / 100.0 * F


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _block(code, length_cm, is_compensator=False):
    return {
        "symbol": None, "logical_code": code, "length_cm": float(length_cm),
        "height_cm": 19.0, "width_cm": 14.0, "cells_local": [],
        "is_special_bond": code in ("B34", "B54"),
        "is_compensator": is_compensator, "source_instance_id": None,
    }


CATALOG = {
    "B39": _block("B39", 39), "B34": _block("B34", 34), "B54": _block("B54", 54),
    "B19": _block("B19", 19),
    "C09": _block("C09", 9, is_compensator=True),
    "C04": _block("C04", 4, is_compensator=True),
}

# Geometrias REAIS medidas no corpus (span do subsegmento de reparo, em cm,
# e a invasao que o C04 produzia antes da guarda).
CORPUS_SPANS = {
    "TGD_W044_W072_B19_C04": (23.757, 0.243),
    "TGD_W075_B19": (18.757, 0.243),
    "TGD_W113_C09": (8.733, 0.267),
    "TGD_W075_O02_C09": (8.758, 0.242),
    "TP1_W029_C09": (8.88, 0.12),
    "TGD_C04_C09": (13.758, 0.242),
}


def sub(lo_cm, hi_cm, leading_open=True, trailing_open=True,
        left_opening=None, right_opening=0):
    """Um subsegmento solido de reparo no MESMO formato que
    `region_solid_subsegments` devolve."""
    return {"lo": lo_cm, "hi": hi_cm, "leading_open": leading_open,
            "trailing_open": trailing_open,
            "left_opening": left_opening, "right_opening": right_opening}


def solve_repair(sub_entry):
    """Chama a FUNCAO DE PRODUCAO `_solve_repair_subsegments` com um plano
    de uma unica sobra solida."""
    plan = {"segments": [sub_entry], "undersized": []}
    solved, failures = m._solve_repair_subsegments(
        plan, CATALOG, True, [], [], False)
    return solved, failures


def layout_end_cm(layout):
    return m._layout_physical_end_cm(layout)


def unguarded_content_end_cm(span_cm):
    """Onde a ultima peca terminaria SEM a guarda (o que o fit sozinho
    manda montar) - None quando nem o fit aceita o trecho."""
    remaining = m._pier_remaining_snapped_cm(span_cm, 0.0, 0.0)
    if remaining is None:
        return None
    return remaining - JOINT


# =====================================================================
# 0. Aritmetica pura da guarda (`pier_cm_floored_to_module`)
# =====================================================================

class TestFlooredToModule(object):
    @pytest.mark.parametrize("span,esperado", [
        (23.757, 19.0), (18.757, 14.0), (13.758, 9.0),
        (8.88, 4.0), (8.733, 4.0), (4.0, 4.0),
    ])
    def test_maior_conteudo_modular_que_cabe(self, span, esperado):
        assert m.pier_cm_floored_to_module(span, 0.0, 0.0) == pytest.approx(esperado)

    def test_conteudo_reduzido_sempre_cabe_no_trecho_real(self):
        for span, _inv in CORPUS_SPANS.values():
            floored = m.pier_cm_floored_to_module(span, 0.0, 0.0)
            assert floored is not None
            assert floored <= span + PHYS_TOL

    def test_trecho_curto_demais_nao_tem_o_que_montar(self):
        assert m.pier_cm_floored_to_module(3.0, 0.0, 0.0) is None

    def test_sobra_deixada_fica_abaixo_do_menor_vazio_reportavel(self):
        """Como o modulo vale 5cm e o fit so' aceita ate' 0,30cm de ruido, a
        sobra contra a fronteira fica sempre em [4,70; 5,00) - abaixo dos
        5,0cm que a auditoria de cobertura considera reportavel."""
        for span, _inv in CORPUS_SPANS.values():
            floored = m.pier_cm_floored_to_module(span, 0.0, 0.0)
            sobra = span - floored
            assert MODULE - FIT_TOL <= sobra < MODULE


# =====================================================================
# 1. A guarda em si, sobre a funcao de producao `_solve_repair_subsegments`
# =====================================================================

class TestGuardaFisicaNoReparo(object):
    # ---- item 3/4/5/9: trecho dentro do fit terminando em JAMBA ----
    @pytest.mark.parametrize("nome", sorted(CORPUS_SPANS))
    def test_geometria_real_do_corpus_nao_invade_a_jamba(self, nome):
        span, invasao = CORPUS_SPANS[nome]
        # o regime existe mesmo: SEM a guarda o conteudo passaria do fim
        # fisico do trecho exatamente pela invasao medida no corpus.
        sem_guarda = unguarded_content_end_cm(span)
        assert sem_guarda is not None
        assert sem_guarda - span == pytest.approx(invasao, abs=1e-3)
        assert sem_guarda - span > PHYS_TOL
        # COM a guarda: o que for montado cabe dentro do trecho.
        solved, _failures = solve_repair(sub(0.0, span))
        assert len(solved) == 1
        _s, layout = solved[0]
        assert layout_end_cm(layout) <= span + PHYS_TOL

    # ---- item 2: dentro do fit, mas SEM abertura (ancora com argamassa) ----
    @pytest.mark.parametrize("nome", sorted(CORPUS_SPANS))
    def test_ancora_com_argamassa_mantem_o_snap_do_fit(self, nome):
        span, _invasao = CORPUS_SPANS[nome]
        solved, _f = solve_repair(sub(0.0, span, trailing_open=False,
                                      right_opening=None))
        assert len(solved) == 1
        _s, layout = solved[0]
        # a junta de 1cm da ancora absorve o excesso: o layout continua
        # sendo o do fit (nao foi reduzido).
        assert layout_end_cm(layout) == pytest.approx(unguarded_content_end_cm(span))

    # ---- item 1/14: trecho EXATAMENTE modular nao muda nada ----
    @pytest.mark.parametrize("span", [4.0, 9.0, 14.0, 19.0, 24.0, 39.0, 79.0])
    def test_trecho_exatamente_modular_e_intocado(self, span):
        solved, _f = solve_repair(sub(0.0, span))
        assert len(solved) == 1
        _s, layout = solved[0]
        assert layout_end_cm(layout) == pytest.approx(span)
        assert layout_end_cm(layout) == pytest.approx(unguarded_content_end_cm(span))

    # ---- item 6: EXATAMENTE no limite do fit ----
    def test_no_limite_do_fit_comportamento_definido(self):
        """`span` EXATAMENTE FIT_TOL abaixo do modulo (24,0 - 0,30 = 23,7).

        Comportamento DEFINIDO, nao acidental: `24,7 - 25` vale
        -0,3000000000000007 em ponto flutuante, um epsilon ACIMA da
        tolerancia - entao o fit NAO aceita este trecho como modular, e o
        pre-check e o empacotador real dizem exatamente a MESMA coisa (a
        invariante que o C04 ja' tinha estabelecido). Nada e' montado, logo
        nada pode invadir - o teste existe para travar esse comportamento,
        seja qual for o lado do limite em que ele caia."""
        span = 24.0 - FIT_TOL
        fecha = m.pier_closes_with_blocks_cm(span + JOINT, JOINT, 0.0)
        snapped = m._pier_remaining_snapped_cm(span, 0.0, 0.0)
        assert fecha is (snapped is not None)   # pre-check == empacotador
        assert snapped is None                  # o limite exato NAO fecha
        # e um epsilon DENTRO do limite fecha, e ai' a guarda e' que protege
        span_dentro = 24.0 - FIT_TOL + 1e-6
        assert m._pier_remaining_snapped_cm(span_dentro, 0.0, 0.0) is not None
        solved, _f = solve_repair(sub(0.0, span_dentro))
        assert len(solved) == 1
        _s, layout = solved[0]
        assert layout_end_cm(layout) <= span_dentro + PHYS_TOL
        assert layout_end_cm(layout) == pytest.approx(19.0)

    # ---- item: excesso DENTRO da tolerancia fisica continua passando ----
    def test_excesso_dentro_da_tolerancia_fisica_e_ruido_e_passa(self):
        span = 24.0 - (PHYS_TOL / 2.0)
        solved, _f = solve_repair(sub(0.0, span))
        assert len(solved) == 1
        _s, layout = solved[0]
        assert layout_end_cm(layout) == pytest.approx(24.0)

    # ---- item 7: fora da tolerancia de fit -> nao fecha (nem com guarda) ----
    @pytest.mark.parametrize("span", [24.0 - 0.35, 24.0 - 0.5, 24.0 - 1.0])
    def test_fora_do_fit_nao_snapa(self, span):
        assert unguarded_content_end_cm(span) != pytest.approx(24.0)

    # ---- item 8: abertura na ponta de ENTRADA ----
    def test_abertura_na_ponta_de_entrada_nao_e_invadida(self):
        """As pecas comecam no `lo` do trecho e crescem para a direita:
        uma abertura na ponta de ENTRADA nunca e' invadida - e a guarda
        continua protegendo a ponta de saida."""
        span, _inv = CORPUS_SPANS["TGD_W075_B19"]
        solved, _f = solve_repair(sub(0.0, span, leading_open=True,
                                      left_opening=0, right_opening=1))
        assert len(solved) == 1
        _s, layout = solved[0]
        assert min(start for _c, start, _e in layout) >= -PHYS_TOL
        assert layout_end_cm(layout) <= span + PHYS_TOL

    # ---- item 10: DUAS fronteiras de abertura ----
    def test_duas_fronteiras_de_abertura(self):
        span, _inv = CORPUS_SPANS["TGD_W044_W072_B19_C04"]
        solved, _f = solve_repair(sub(0.0, span, leading_open=True,
                                      trailing_open=True,
                                      left_opening=0, right_opening=1))
        assert len(solved) == 1
        _s, layout = solved[0]
        assert min(start for _c, start, _e in layout) >= -PHYS_TOL
        assert layout_end_cm(layout) <= span + PHYS_TOL

    # ---- trecho onde NEM o conteudo reduzido cabe -> vazio, nunca invasao --
    def test_quando_nada_cabe_o_trecho_fica_vazio(self):
        """Melhor o trecho vazio (o que acontecia ANTES do C04) do que uma
        peca dentro do vao."""
        layout = m._layout_fitted_to_physical_span(
            [("B19", 0.0, 19.0)], 3.0, sub(0.0, 3.0), lambda _span: None)
        assert layout is None

    # ---- a guarda nao inventa peca: usa composicao que o solver ja' monta --
    def test_composicao_reduzida_e_a_do_proprio_solver(self):
        span, _inv = CORPUS_SPANS["TGD_W044_W072_B19_C04"]
        solved, _f = solve_repair(sub(0.0, span))
        _s, layout = solved[0]
        floored = m.pier_cm_floored_to_module(span, 0.0, 0.0)
        esperado = m._pier_ordered_layout(floored, CATALOG, 0.0, 0.0,
                                          leading_open_override=True,
                                          trailing_open_override=True)
        assert [c for c, _a, _b in layout] == [c for c, _a, _b in esperado]


# =====================================================================
# 2. SOLVER COMPLETO - orientacao, reversao de ponta, fiadas
# =====================================================================

NUM_COURSES = 4
# offsets de jamba que REPRODUZEM o regime C04 (span do reparo cai a menos
# de 0,30cm abaixo de um multiplo de 5) - medidos por varredura.
JAMB_OFFSETS_CM = [118.757, 123.733, 123.757, 124.75, 128.88]


def solve_walls(lines, openings_per_wall, thickness_cm=14.0):
    walls = [(line, ft(thickness_cm), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(
        walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    result = m.solve_building_blocks_all_courses(
        nodes, walls, end_to_node, openings_per_wall, CATALOG, 0.0, NUM_COURSES)
    return result, walls


def jamb_crossings(result, walls, openings_per_wall, tolerance_cm=None):
    """Toda peca que entra no vao livre de uma abertura, por fiada - medido
    na GEOMETRIA FINAL, nunca por dentro do solver."""
    if tolerance_cm is None:
        tolerance_cm = PHYS_TOL
    out = []
    for course_index, cands in (result.get("course_candidates") or {}).items():
        for cand in cands:
            wall_idx = cand.get("wall_idx")
            if wall_idx is None:
                continue
            p0, _p1, wall_dir, _len, _t = m._wall_axis_and_length(walls, wall_idx)
            a, b = m._candidate_extent_on_wall_axis(cand, p0, wall_dir)
            lo, hi = min(a, b), max(a, b)
            for (t0, t1, _sill, _head) in (openings_per_wall[wall_idx]
                                           if wall_idx < len(openings_per_wall) else []):
                v0, v1 = m._ft_to_cm(t0), m._ft_to_cm(t1)
                overlap = min(hi, v1) - max(lo, v0)
                if overlap > tolerance_cm:
                    out.append((wall_idx, course_index, cand.get("logical_code"),
                                round(lo, 3), round(hi, 3), round(overlap, 4)))
    return sorted(set(out))


def door_at(t0_cm, width_cm=91.0):
    return [(ft(t0_cm), ft(t0_cm + width_cm), ft(0.0), ft(210.0))]


class TestSolverCompleto(object):
    # ---- item 12: HORIZONTAL ----
    @pytest.mark.parametrize("t0", JAMB_OFFSETS_CM)
    def test_parede_horizontal_nenhuma_peca_no_vao(self, t0):
        result, walls = solve_walls([seg(0, 0, 500, 0)], [door_at(t0)])
        assert not result.get("error")
        assert jamb_crossings(result, walls, [door_at(t0)]) == []

    # ---- item 12: VERTICAL ----
    @pytest.mark.parametrize("t0", JAMB_OFFSETS_CM)
    def test_parede_vertical_nenhuma_peca_no_vao(self, t0):
        result, walls = solve_walls([seg(0, 0, 0, 500)], [door_at(t0)])
        assert not result.get("error")
        assert jamb_crossings(result, walls, [door_at(t0)]) == []

    # ---- item 11: REVERSAO DE PONTA ----
    @pytest.mark.parametrize("t0", JAMB_OFFSETS_CM)
    def test_reversao_de_ponta_nenhuma_peca_no_vao(self, t0):
        """A MESMA parede desenhada no sentido contrario (e a abertura
        re-parametrizada) continua sem peca dentro do vao - a guarda e'
        geometrica, nao depende do sentido do desenho."""
        comprimento = 500.0
        t1 = t0 + 91.0
        openings = [[(ft(comprimento - t1), ft(comprimento - t0),
                      ft(0.0), ft(210.0))]]
        result, walls = solve_walls([seg(500, 0, 0, 0)], openings)
        assert not result.get("error")
        assert jamb_crossings(result, walls, openings) == []

    # ---- item 13: TODAS as fiadas ----
    def test_todas_as_fiadas_ficam_limpas(self):
        t0 = 123.757
        result, walls = solve_walls([seg(0, 0, 500, 0)], [door_at(t0)])
        cruzam = jamb_crossings(result, walls, [door_at(t0)])
        assert cruzam == []
        fiadas = set((result.get("course_candidates") or {}).keys())
        assert len(fiadas) == NUM_COURSES

    # ---- item 14: geometria SEM o regime C04 nao muda nada ----
    @pytest.mark.parametrize("t0", [120.0, 125.0, 130.0])
    def test_jamba_em_posicao_modular_nao_e_afetada(self, t0):
        result, walls = solve_walls([seg(0, 0, 500, 0)], [door_at(t0)])
        assert not result.get("error")
        assert jamb_crossings(result, walls, [door_at(t0)]) == []

    # ---- o cenario REPRODUZ mesmo o defeito quando a guarda e' desligada --
    @pytest.mark.parametrize("t0", JAMB_OFFSETS_CM)
    def test_sem_a_guarda_o_defeito_volta(self, t0, monkeypatch):
        """Rede de seguranca contra a guarda virar no-op silencioso: com ela
        desligada, ESTE MESMO cenario produz pecas dentro do vao."""
        import core.engine.wall_stepper as wall_stepper
        monkeypatch.setattr(
            wall_stepper, "_layout_fitted_to_physical_span",
            lambda layout, pier_cm, sub_entry, layout_for_span: layout)
        result, walls = solve_walls([seg(0, 0, 500, 0)], [door_at(t0)])
        assert jamb_crossings(result, walls, [door_at(t0)]) != []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
