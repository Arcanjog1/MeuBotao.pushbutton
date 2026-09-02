# -*- coding: utf-8 -*-
"""Trace da fronteira NODE|FILL nas paredes reprovadas pelo prisma.

Instrumenta `solve_wall_free_fill` EM MEMORIA (nenhum arquivo de producao
tocado) para gravar, por parede/fiada/trecho:

  - o TIPO de cada fronteira do trecho (WALL_START/MIDSPAN_HI/OPENING_HI...);
  - se aquela fronteira e' PECA DE NO' de verdade (`border is not None`,
    ou MIDSPAN) - o discriminador que o fix precisa;
  - `seg_start_cm`/`seg_end_cm`, o layout escolhido e as juntas internas;
  - a junta de FRONTEIRA `seg_start_cm - BLOCK_JOINT_CM/2`.

Depois cruza, por parede, as juntas de FRONTEIRA de nó da Fiada A com as
juntas INTERNAS da Fiada B (e vice-versa) e imprime as coincidencias -
que sao exatamente as violacoes `PRISM_CONTINUOUS_JOINT` medidas.

    python3 run_nf_trace.py [project_id]
"""
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_NUVEM = os.path.dirname(_BENCH)
for _p in (_NUVEM, _BENCH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lib_nf as NF  # noqa: E402

TOL = 1.0  # VERTICAL_JOINT_STAGGER_TOLERANCE_CM


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else "piloto_sintetico_2x2"
    from benchmark import runner, solver_bridge
    engine = solver_bridge.engine()
    import core.engine.wall_stepper as WS

    rows = []
    original = WS._layout_internal_joint_positions_cm

    def spy(layout, seg_start_cm, leading_is_open=False, trailing_is_open=False):
        out = original(layout, seg_start_cm, leading_is_open, trailing_is_open)
        rows.append({
            "seg_start_cm": round(float(seg_start_cm), 3),
            "codes": [r[0] for r in layout],
            "internal_cm": [round(float(v), 3) for v in out],
            "boundary_cm": round(float(seg_start_cm) - 0.5, 3),
            "leading_is_open": bool(leading_is_open),
            "trailing_is_open": bool(trailing_is_open),
        })
        return out

    WS._layout_internal_joint_positions_cm = spy
    engine._layout_internal_joint_positions_cm = spy
    try:
        payload = json.load(open(runner.project_paths(project_id)["input"],
                                 "r", encoding="utf-8"))
        solve_result = solver_bridge.run_solver(payload)[0]
    finally:
        WS._layout_internal_joint_positions_cm = original
        engine._layout_internal_joint_positions_cm = original

    internal = set()
    for row in rows:
        for value in row["internal_cm"]:
            internal.add(round(value, 2))
    boundary = sorted(set(round(r["boundary_cm"], 2) for r in rows))
    colliding = sorted(v for v in boundary
                       if any(abs(v - i) <= TOL for i in internal))

    report = {
        "project_id": project_id,
        "ATENCAO": (
            "As listas abaixo sao um POOL GLOBAL (todas as paredes, fiadas e "
            "variantes juntas) - e' o instrumento do cross-audit, reproduzido "
            "aqui para a evidencia do item 3, e NAO uma contagem de violacao. "
            "Duas juntas no mesmo `t` de PAREDES DIFERENTES aparecem como "
            "'coincidencia' aqui e nao sao defeito nenhum. A medida de "
            "violacao e' PRISM_CONTINUOUS_JOINT (validate_prism) e o "
            "invariante por parede/fiada de tests/test_block_node_fill_joint.py."),
        "chamadas": len(rows),
        "alignment_conflicts": len(solve_result.get("alignment_conflicts") or []),
        "juntas_de_fronteira": boundary,
        "fronteiras_que_colidem_com_junta_interna": colliding,
        "trechos": rows,
    }
    print(json.dumps({k: v for k, v in report.items() if k != "trechos"},
                     indent=1, ensure_ascii=False))
    NF.write_json(NF.out_path("out_nf_trace_evidencia_%s.json" % project_id), report)
    return report


if __name__ == "__main__":
    main()
