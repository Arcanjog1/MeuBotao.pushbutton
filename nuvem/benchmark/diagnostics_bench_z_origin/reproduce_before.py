# -*- coding: utf-8 -*-
"""CR-BENCH-Z-ORIGIN, item 3: reproducao MINIMA do defeito.

Rodado uma primeira vez, ANTES de qualquer correcao (evidencia gravada em
`docs/BENCH_Z_ORIGIN.md`): mostrava fiada do motor em 201.00cm x fiada do
benchmark em 200.00cm, 1cm de diferenca, e um achado FANTASMA
(`OPENING_BLOCK_INSIDE_DOOR`) numa peca que so' TOCA o head da porta.

Mantido no repositorio (nome do arquivo preservado por rastreabilidade)
como teste de nao-regressao executavel: depois do fix em
`extract/from_solver.py` (reuso de `analysis.course_z_abs_cm`), a mesma
conta agora tem que dar DIFERENCA ZERO e NENHUM achado fantasma - e' o
que os dois `assert` finais verificam.

NAO depende do NODE-FILL (`claude/cr-block-node-fill-joint-9tv0kd`) - usa
so' uma peca sintetica, uma porta sintetica e as duas formulas que estao
em desacordo:

    MOTOR      (`nuvem/core/wall_modeling.py::_course_z_abs`, PRODUCAO,
                nao tocada por este script - so' lida via `solver_bridge`)
    BENCHMARK  (`nuvem/benchmark/extract/from_solver.py::project_from_solver`,
                tambem NAO tocada por este script - chamada de verdade,
                sem reimplementar a formula dela)

Roda fora do Revit (dubles de `tests/revit_stubs.py`, mesmo caminho de
`solver_bridge.py`). Uso:

    py -3 nuvem/benchmark/diagnostics_bench_z_origin/reproduce_before.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_NUVEM_DIR = os.path.dirname(os.path.dirname(_HERE))
if _NUVEM_DIR not in sys.path:
    sys.path.insert(0, _NUVEM_DIR)

from benchmark import solver_bridge  # noqa: E402
from benchmark.extract import from_solver  # noqa: E402
from benchmark.validators import validate_openings  # noqa: E402


def main():
    module = solver_bridge.engine()
    _ft = solver_bridge._ft  # mesma conversao cm->ft que o benchmark usa

    # -------------------------------------------------- peca/parede sinteticas
    block_height_cm = 19.0
    course_step_cm = block_height_cm + module.BLOCK_JOINT_CM  # 20.0 (regra do motor)
    course_index = 10  # fiada intermediaria qualquer - nada de magico em "11"
    base_z_abs_cm = 0.0

    catalog = {
        "B39": {
            "length_cm": 39.0, "height_cm": block_height_cm, "width_cm": 14.0,
            "is_special_bond": False, "is_compensator": False,
        },
    }

    wall_length_cm = 300.0
    line = module.Line.CreateBound(
        module.XYZ(0.0, 0.0, 0.0), module.XYZ(_ft(wall_length_cm), 0.0, 0.0))
    walls_to_create = [(line, _ft(14.0), (False, False))]
    nodes = []

    # -------------------------------------------------- a peca da FIADA n
    # Colocada encostada no fim do vao (t=100..180cm), igual ao caso medido
    # (peca logo acima da porta).
    candidate_origin = module.XYZ(_ft(140.0), 0.0, 0.0)  # centro em t=140cm
    course_candidates = {
        course_index: [{
            "wall_idx": 0,
            "origin_world": candidate_origin,
            "logical_code": "B39",
            "length_cm": 39.0,
            "rotation_deg": 0.0,
            "placement_reason": "STANDARD_FILL",
        }],
    }
    solve_result = {"course_candidates": course_candidates}

    # -------------------------------------------------- a "PORTA" que TOCA
    # (nao invade) a fiada `course_index`, segundo o MOTOR.
    #
    # Z verdadeira da fiada n, segundo o MOTOR (formula de producao,
    # `_course_z_abs`, so' LIDA aqui - nao reimplementada):
    motor_course_height_ft = _ft(course_step_cm)
    motor_z_lo_ft = module._course_z_abs(_ft(base_z_abs_cm), course_index,
                                         motor_course_height_ft)
    motor_z_lo_cm = motor_z_lo_ft / module.FEET_PER_METER * 100.0
    motor_z_hi_cm = motor_z_lo_cm + block_height_cm

    door_head_cm = motor_z_lo_cm  # a verga termina EXATAMENTE onde a fiada comeca
    openings_per_wall = [[
        (_ft(100.0), _ft(180.0), _ft(0.0), _ft(door_head_cm)),
    ]]

    print("=" * 70)
    print("CR-BENCH-Z-ORIGIN - reproducao (item 3) / regressao pos-fix")
    print("=" * 70)
    print("block_height_cm ......... {0}".format(block_height_cm))
    print("course_step_cm (motor) ... {0}".format(course_step_cm))
    print("FIRST_COURSE_Z_OFFSET_CM . {0}".format(module.FIRST_COURSE_Z_OFFSET_CM))
    print("course_index ............. {0}".format(course_index))
    print("base_z_abs_cm ............ {0}".format(base_z_abs_cm))
    print("")
    print("MOTOR (_course_z_abs, producao, so' lida): fiada {0} = "
         "{1:.2f} .. {2:.2f} cm".format(course_index, motor_z_lo_cm, motor_z_hi_cm))
    print("porta: head_cm = {0:.2f} cm  (fisicamente TANGENTE a fiada -"
         " overlap fisico = 0)".format(door_head_cm))
    print("")

    # -------------------------------------------------- BENCHMARK (real, sem fix)
    project = from_solver.project_from_solver(
        "repro_bench_z_origin", solve_result, walls_to_create, nodes,
        openings_per_wall, catalog, _ft(base_z_abs_cm), course_index + 1,
    )
    wall = project["walls"][0]
    row = wall["rows"][course_index]
    bench_z_lo_cm = row["elevation_cm"]
    bench_z_hi_cm = bench_z_lo_cm + block_height_cm
    print("BENCHMARK (from_solver.project_from_solver, real, sem fix): "
         "fiada {0} = {1:.2f} .. {2:.2f} cm".format(
             course_index, bench_z_lo_cm, bench_z_hi_cm))
    diff_cm = motor_z_lo_cm - bench_z_lo_cm
    print("")
    print("DIFERENCA (motor - benchmark) = {0:.2f} cm  "
         "(esperado APOS o fix: 0.00 cm - mesma origem vertical)".format(diff_cm))
    assert abs(diff_cm) < 1e-9, (
        "motor e benchmark ainda divergem na origem vertical - fix "
        "incompleto ou revertido")

    # -------------------------------------------------- validador real, achado FANTASMA
    findings = validate_openings.validate_wall(wall, block_height_cm)
    codes = sorted(set(f["code"] for f in findings))
    # `OPENING_MISSING_LINTEL` e' esperado neste cenario sintetico (nenhuma
    # peca de verga foi colocada de proposito) - nao tem nada a ver com a
    # origem vertical. O achado FANTASMA deste CR e' o de OVERLAP: a peca
    # "entrando" no vao so' porque a fiada nasceu 1cm cedo demais.
    overlap_codes = sorted(c for c in codes
                           if c in ("OPENING_BLOCK_INSIDE_DOOR",
                                    "OPENING_BLOCK_INSIDE_WINDOW",
                                    "OPENING_BLOCK_CROSSES_JAMB"))
    print("")
    print("validate_openings.validate_wall(...) achados: {0}".format(codes))
    if overlap_codes:
        print("  -> FANTASMA: o benchmark ainda enxerga a peca ENTRANDO no "
             "vao da porta, mas fisicamente (Z do motor) ela nasce exatamente "
             "no head da porta - overlap fisico real = 0.")
    else:
        print("  -> nenhum achado de overlap - peca TOCA o head da porta, "
             "overlap = 0, exatamente como o item 11 do CR exige "
             "(OPENING_MISSING_LINTEL acima e' esperado: nenhuma peca de "
             "verga foi colocada neste cenario sintetico, nao tem relacao "
             "com a origem vertical).")
    assert not overlap_codes, (
        "achado fantasma de overlap sobrevive ao fix: {0}".format(overlap_codes))

    print("")
    print("VEREDITO: fix confere (origem vertical unica, sem achado fantasma)")


if __name__ == "__main__":
    main()
