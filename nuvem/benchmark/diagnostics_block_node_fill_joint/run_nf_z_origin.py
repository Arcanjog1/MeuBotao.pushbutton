# -*- coding: utf-8 -*-
"""AS DUAS ORIGENS VERTICAIS (item 5 do fechamento) - por que
`OPENING_BLOCK_INSIDE_DOOR` muda e `door_void_violations` nao.

  MOTOR   `_course_z_abs` poe a fiada n em
          `base + FIRST_COURSE_Z_OFFSET_CM + n * passo`  ->  1, 21, ..., 221
          (offset MEDIDO no Revit real - ver PADRAO_MODULACAO.md)

  MODELO  `extract/from_solver.project_from_solver` poe a MESMA fiada em
          `base + n * passo`                              ->  0, 20, ..., 220
          mas mantem `sill_cm`/`head_cm` no Z ABSOLUTO do motor.

As duas coordenadas comparadas por `analysis.opening_active_in_row` vivem,
portanto, em origens 1 cm distantes. Toda porta cuja verga caia EXATAMENTE
numa fronteira de fiada (o caso do `torre_easy_lo_r00_tgd`: verga 221 =
inicio da fiada 11) ganha 1 cm de sobreposicao FANTASMA na fiada de cima.

Este script:
  1. imprime as duas convencoes lado a lado e mostra em qual fiada elas
     discordam;
  2. mede o efeito de ALINHAR as duas origens (monkeypatch em memoria, sem
     tocar em arquivo nenhum) sobre TODOS os codigos do validador.

    python3 run_nf_z_origin.py <saida.json> [project_id]
"""
import os
import sys
import json
import collections

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_NUVEM = os.path.dirname(_BENCH)
for _p in (_NUVEM, _BENCH):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _inside_door_por_fiada(run):
    return dict(sorted(collections.Counter(
        f.get("row") for f in run["findings"]
        if f.get("code") == "OPENING_BLOCK_INSIDE_DOOR").items()))


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    out_path = argv[0] if argv else os.path.join(_HERE, "out_nf_z_origin.json")
    project_id = argv[1] if len(argv) > 1 else "torre_easy_lo_r00_tgd"

    from benchmark import runner, solver_bridge
    from benchmark.extract import from_solver
    engine = solver_bridge.engine()
    import core.wall_modeling as WM

    offset_cm = WM.FIRST_COURSE_Z_OFFSET_CM
    payload = json.load(open(runner.project_paths(project_id)["input"], encoding="utf-8"))
    catalog = solver_bridge.run_solver(payload)[4]
    course_height_ft, _e = WM._course_height_ft(catalog, None)
    block_height_ft, _e2 = WM._block_height_ft(catalog, None)
    to_cm = (lambda ft: ft / engine.FEET_PER_METER * 100.0)

    convencoes = []
    for course_index in range(13):
        z_lo, z_hi = WM._course_z_band(0.0, course_index, course_height_ft, block_height_ft)
        modelo_lo = course_index * to_cm(course_height_ft)
        convencoes.append({
            "fiada": course_index,
            "motor_cm": [round(to_cm(z_lo), 2), round(to_cm(z_hi), 2)],
            "modelo_cm": [round(modelo_lo, 2), round(modelo_lo + to_cm(block_height_ft), 2)],
        })

    base = runner.run_project(project_id, write_files=False)
    original = from_solver._openings_for_wall

    def alinhado(wall_idx, openings_per_wall, base_z_cm):
        """A abertura passa para a MESMA origem nominal das fiadas."""
        out = []
        for opening in original(wall_idx, openings_per_wall, base_z_cm):
            novo = dict(opening)
            novo["sill_cm"] = round(opening["sill_cm"] - offset_cm, 3)
            novo["head_cm"] = round(opening["head_cm"] - offset_cm, 3)
            out.append(novo)
        return out

    from_solver._openings_for_wall = alinhado
    try:
        corrigido = runner.run_project(project_id, write_files=False)
    finally:
        from_solver._openings_for_wall = original

    como_esta = dict(base["score"].get("findings_by_code") or {})
    com_alinhamento = dict(corrigido["score"].get("findings_by_code") or {})
    payload_out = {
        "project_id": project_id,
        "FIRST_COURSE_Z_OFFSET_CM": offset_cm,
        "convencoes_verticais": convencoes,
        "codes_COMO_ESTA": como_esta,
        "codes_ORIGENS_ALINHADAS": com_alinhamento,
        "inside_door_por_fiada_COMO_ESTA": _inside_door_por_fiada(base),
        "inside_door_por_fiada_ALINHADO": _inside_door_por_fiada(corrigido),
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload_out, handle, indent=1, sort_keys=True)
        handle.write("\n")

    print("FIRST_COURSE_Z_OFFSET_CM = %s" % offset_cm)
    print("%-6s | %-20s | %-20s" % ("fiada", "MOTOR", "MODELO benchmark"))
    for linha in convencoes[9:13]:
        print("%-6s | %8.2f .. %-8.2f | %8.2f .. %-8.2f" % (
            linha["fiada"], linha["motor_cm"][0], linha["motor_cm"][1],
            linha["modelo_cm"][0], linha["modelo_cm"][1]))
    print()
    print("%-34s %11s %11s" % ("codigo", "COMO_ESTA", "ALINHADO"))
    for code in sorted(set(como_esta) | set(com_alinhamento)):
        a, b = como_esta.get(code, 0), com_alinhamento.get(code, 0)
        print("%-34s %11s %11s%s" % (code, a, b, "   <<<" if a != b else ""))
    print()
    print("INSIDE_DOOR por fiada, COMO_ESTA: %s" % payload_out["inside_door_por_fiada_COMO_ESTA"])
    print("INSIDE_DOOR por fiada, ALINHADO : %s" % payload_out["inside_door_por_fiada_ALINHADO"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
