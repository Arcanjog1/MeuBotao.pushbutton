# -*- coding: utf-8 -*-
"""CR-BENCH-Z-ORIGIN (item 11) - testes headless da origem vertical unica
do benchmark.

NAO importa nem exercita `wall_stepper.py`/`wall_pairing.py` - o alvo
aqui e' exclusivamente `nuvem/benchmark/extract/from_solver.py` (via
`analysis.course_z_abs_cm`, a UNICA formula de origem vertical do
benchmark depois deste CR) e a leitura desse Z pelos validadores de
abertura/cobertura.

Onde o teste precisa comparar contra a formula REAL do motor
(`core/wall_modeling.py::_course_z_abs`), o motor e' carregado de verdade
via `benchmark.solver_bridge` (mesmos dubles de `tests/revit_stubs.py` de
`tests/regression/test_engine_constants_match.py`) - nunca reimplementado
aqui. Esses testes pulam (`skipif`) se o motor nao carregar; os demais
(so' `analysis`/`from_solver`/`validators`, sem o motor) rodam sempre."""

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_NUVEM_DIR = os.path.join(os.path.dirname(_HERE), "nuvem")
if os.path.isfile(os.path.join(_NUVEM_DIR, "benchmark", "__init__.py")) \
        and _NUVEM_DIR not in sys.path:
    sys.path.insert(0, _NUVEM_DIR)

from benchmark import analysis, model  # noqa: E402
from benchmark.extract import from_solver  # noqa: E402
from benchmark.validators import validate_openings  # noqa: E402

try:
    from benchmark import solver_bridge
    ENGINE = solver_bridge.engine()
except Exception:  # pragma: no cover - ambiente sem os dubles
    ENGINE = None

needs_engine = pytest.mark.skipif(
    ENGINE is None, reason="motor nao carregou (tests/revit_stubs.py indisponivel)")


BLOCK_HEIGHT_CM = 19.0
COURSE_STEP_CM = BLOCK_HEIGHT_CM + analysis.BLOCK_JOINT_CM  # 20.0


def _build_project(course_index, base_z_cm=0.0, opening_kind="touch_head",
                   num_courses=None):
    """Projeto minimo com UMA parede, UMA peca na fiada `course_index` e
    UMA abertura, via `from_solver.project_from_solver` real (nunca
    reimplementado). `opening_kind`:

    - "touch_head": porta cujo head cai EXATAMENTE onde a fiada comeca
      (teste critico do item 11 - so' TOCAR nao e' invadir);
    - "window": janela com peitoril > base (abertura nao esvazia a base);
    - "inside": porta cujo vao cobre a fiada inteira (overlap real).
    """
    module = ENGINE
    _ft = solver_bridge._ft

    line = module.Line.CreateBound(
        module.XYZ(0.0, 0.0, 0.0), module.XYZ(_ft(300.0), 0.0, 0.0))
    walls_to_create = [(line, _ft(14.0), (False, False))]
    nodes = []
    catalog = {
        "B39": {"length_cm": 39.0, "height_cm": BLOCK_HEIGHT_CM, "width_cm": 14.0,
                "is_special_bond": False, "is_compensator": False},
    }

    motor_z_lo_ft = module._course_z_abs(
        _ft(base_z_cm), course_index, _ft(COURSE_STEP_CM))
    motor_z_lo_cm = motor_z_lo_ft / module.FEET_PER_METER * 100.0

    candidate = {
        "wall_idx": 0,
        "origin_world": module.XYZ(_ft(140.0), 0.0, 0.0),
        "logical_code": "B39",
        "length_cm": 39.0,
        "rotation_deg": 0.0,
        "placement_reason": "STANDARD_FILL",
    }
    course_candidates = {course_index: [candidate]}

    if opening_kind == "touch_head":
        sill_cm, head_cm = 0.0, motor_z_lo_cm
    elif opening_kind == "inside":
        sill_cm, head_cm = 0.0, motor_z_lo_cm + BLOCK_HEIGHT_CM
    elif opening_kind == "window":
        sill_cm, head_cm = motor_z_lo_cm - 5.0, motor_z_lo_cm
    else:
        raise ValueError(opening_kind)

    openings_per_wall = [[
        (_ft(100.0), _ft(180.0), _ft(sill_cm), _ft(head_cm)),
    ]]

    solve_result = {"course_candidates": course_candidates}
    project = from_solver.project_from_solver(
        "p", solve_result, walls_to_create, nodes, openings_per_wall,
        catalog, _ft(base_z_cm), num_courses or (course_index + 1),
    )
    return project, motor_z_lo_cm


# ======================================================= course_z_abs_cm
@needs_engine
@pytest.mark.parametrize("course_index", [0, 1, 5, 10, 27])
def test_course_z_abs_cm_bate_com_o_motor_em_qualquer_fiada(course_index):
    """`analysis.course_z_abs_cm` (benchmark) tem que dar o MESMO valor de
    `_course_z_abs` (motor, so' lido, nunca reimplementado) - primeira
    fiada, fiada intermediaria e fiada tardia."""
    module = ENGINE
    base_z_cm = 0.0
    motor_ft = module._course_z_abs(
        solver_bridge._ft(base_z_cm), course_index, solver_bridge._ft(COURSE_STEP_CM))
    motor_cm = motor_ft / module.FEET_PER_METER * 100.0
    bench_cm = analysis.course_z_abs_cm(base_z_cm, course_index, COURSE_STEP_CM)
    assert bench_cm == pytest.approx(motor_cm, abs=1e-6)


@needs_engine
@pytest.mark.parametrize("base_z_cm", [0.0, 305.5, -12.0])
def test_course_z_abs_cm_bate_com_o_motor_para_base_elevation_diferente_de_zero(base_z_cm):
    """Item 11: pavimento com base_elevation != 0 (inclusive negativa -
    subsolo) tem que continuar batendo com o motor."""
    module = ENGINE
    course_index = 4
    motor_ft = module._course_z_abs(
        solver_bridge._ft(base_z_cm), course_index, solver_bridge._ft(COURSE_STEP_CM))
    motor_cm = motor_ft / module.FEET_PER_METER * 100.0
    bench_cm = analysis.course_z_abs_cm(base_z_cm, course_index, COURSE_STEP_CM)
    assert bench_cm == pytest.approx(motor_cm, abs=1e-6)


def test_primeira_fiada_nasce_em_base_mais_offset_uma_unica_vez():
    """Fiada 1 (course_index=0): base + FIRST_COURSE_Z_OFFSET_CM, nao base."""
    z0 = analysis.course_z_abs_cm(100.0, 0, COURSE_STEP_CM)
    assert z0 == pytest.approx(100.0 + analysis.FIRST_COURSE_Z_OFFSET_CM)


def test_offset_da_primeira_fiada_aplicado_uma_unica_vez_ao_longo_das_fiadas():
    """O offset entra so' na origem (course_index=0) - o PASSO entre fiadas
    consecutivas e' sempre `course_step_cm`, nunca `course_step_cm` +
    offset de novo (isso indicaria o offset sendo somado a cada fiada)."""
    base_z_cm = 50.0
    zs = [analysis.course_z_abs_cm(base_z_cm, i, COURSE_STEP_CM) for i in range(6)]
    for i in range(1, len(zs)):
        assert zs[i] - zs[i - 1] == pytest.approx(COURSE_STEP_CM)
    assert zs[0] - base_z_cm == pytest.approx(analysis.FIRST_COURSE_Z_OFFSET_CM)


# ================================================== extracao (from_solver)
@needs_engine
@pytest.mark.parametrize("course_index", [0, 1, 8])
def test_row_elevation_do_projeto_extraido_bate_com_o_motor(course_index):
    project, motor_z_lo_cm = _build_project(course_index, opening_kind="window")
    row = project["walls"][0]["rows"][course_index]
    assert row["elevation_cm"] == pytest.approx(motor_z_lo_cm, abs=1e-6)


@needs_engine
def test_peca_que_apenas_toca_o_head_da_porta_tem_overlap_zero():
    """Item 11, teste CRITICO: uma peca cujo pe' encosta EXATAMENTE no
    head da porta (nasce onde a verga termina) nao pode ser classificada
    como dentro da abertura - overlap fisico = 0, nao 1cm fantasma."""
    project, motor_z_lo_cm = _build_project(10, opening_kind="touch_head")
    wall = project["walls"][0]
    row = wall["rows"][10]
    assert row["elevation_cm"] == pytest.approx(motor_z_lo_cm, abs=1e-6)

    findings = validate_openings.validate_wall(wall, BLOCK_HEIGHT_CM)
    overlap_codes = [f["code"] for f in findings
                     if f["code"] in ("OPENING_BLOCK_INSIDE_DOOR",
                                      "OPENING_BLOCK_CROSSES_JAMB")]
    assert overlap_codes == [], (
        "peca so' TOCA o head da porta - nao pode virar achado de overlap: "
        "{0}".format(findings))


@needs_engine
def test_peca_que_realmente_invade_o_vao_continua_sendo_achado():
    """Contraprova do teste anterior: quando a peca REALMENTE cai dentro
    do vao (nao so' toca a ponta), o achado tem que continuar existindo -
    o fix nao pode silenciar overlap real junto com o fantasma."""
    project, _motor_z_lo_cm = _build_project(10, opening_kind="inside")
    wall = project["walls"][0]
    findings = validate_openings.validate_wall(wall, BLOCK_HEIGHT_CM)
    codes = [f["code"] for f in findings]
    assert "OPENING_BLOCK_INSIDE_DOOR" in codes


@needs_engine
def test_janela_usa_a_mesma_origem_vertical_da_porta():
    """Abertura tipo janela (peitoril > base) tambem tem que usar
    `course_z_abs_cm` - nao ha' um segundo caminho de calculo de Z so'
    para janela."""
    project, motor_z_lo_cm = _build_project(6, opening_kind="window")
    row = project["walls"][0]["rows"][6]
    assert row["elevation_cm"] == pytest.approx(motor_z_lo_cm, abs=1e-6)
    opening = project["walls"][0]["openings"][0]
    assert opening["kind"] == model.OPENING_WINDOW


@needs_engine
def test_lintel_procura_a_verga_na_fiada_que_o_motor_realmente_usou():
    """`OPENING_MISSING_LINTEL` (item 10 - delta de ~-92 no TP1) depende de
    `_row_covering_elevation(wall, opening['head_cm'], ...)` achar a fiada
    certa. Antes do fix, o head (calculado pelo MOTOR) podia cair 1cm
    ACIMA de onde a fiada extraida pelo benchmark realmente comecava -
    `_row_covering_elevation` continuava achando ALGUMA fiada (a busca e'
    por faixa, nao por igualdade exata), so' que a fiada ERRADA, uma
    abaixo da que o motor de fato usou. Depois do fix as duas colunas
    (fiada em que o motor fisicamente para', fiada em que o validador
    procura a verga) apontam pro MESMO indice."""
    course_index = 10
    project, motor_z_lo_cm = _build_project(course_index, opening_kind="touch_head")
    wall = project["walls"][0]
    opening = wall["openings"][0]
    assert opening["head_cm"] == pytest.approx(motor_z_lo_cm, abs=1e-6)

    head_row = validate_openings._row_covering_elevation(
        wall, opening["head_cm"], BLOCK_HEIGHT_CM)
    assert head_row is not None
    assert head_row["row"] == course_index


@needs_engine
def test_ordenacao_de_endpoint_da_parede_e_irrelevante_para_a_origem_z():
    """A convencao vertical nao depende de qual ponta da parede foi
    desenhada primeiro (GetEndPoint(0) vs GetEndPoint(1)) - Z e' ortogonal
    ao eixo X/Y da parede."""
    module = ENGINE
    _ft = solver_bridge._ft
    base_z_cm = 0.0
    course_index = 3
    catalog = {"B39": {"length_cm": 39.0, "height_cm": BLOCK_HEIGHT_CM,
                       "width_cm": 14.0, "is_special_bond": False,
                       "is_compensator": False}}
    candidate = {
        "wall_idx": 0,
        "origin_world": module.XYZ(_ft(140.0), 0.0, 0.0),
        "logical_code": "B39",
        "length_cm": 39.0,
        "rotation_deg": 0.0,
        "placement_reason": "STANDARD_FILL",
    }
    solve_result = {"course_candidates": {course_index: [candidate]}}

    forward = module.Line.CreateBound(
        module.XYZ(0.0, 0.0, 0.0), module.XYZ(_ft(300.0), 0.0, 0.0))
    backward = module.Line.CreateBound(
        module.XYZ(_ft(300.0), 0.0, 0.0), module.XYZ(0.0, 0.0, 0.0))

    project_fwd = from_solver.project_from_solver(
        "p", solve_result, [(forward, _ft(14.0), (False, False))], [], [[]],
        catalog, _ft(base_z_cm), course_index + 1,
    )
    project_bwd = from_solver.project_from_solver(
        "p", solve_result, [(backward, _ft(14.0), (False, False))], [], [[]],
        catalog, _ft(base_z_cm), course_index + 1,
    )
    z_fwd = project_fwd["walls"][0]["rows"][course_index]["elevation_cm"]
    z_bwd = project_bwd["walls"][0]["rows"][course_index]["elevation_cm"]
    assert z_fwd == pytest.approx(z_bwd, abs=1e-9)
