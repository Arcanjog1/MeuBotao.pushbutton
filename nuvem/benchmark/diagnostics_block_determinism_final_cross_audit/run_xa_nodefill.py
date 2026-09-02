# -*- coding: utf-8 -*-
"""PROVA da hipotese da CONTA 1 (item 10 da missao): a junta entre a PECA
DE NO' e o PRIMEIRO BLOCO DO PREENCHIMENTO nao entra na lista de juntas a
evitar da fiada oposta.

Instrumenta o motor EM MEMORIA (monkeypatch de
`_layout_internal_joint_positions_cm`, nenhum arquivo de producao e'
tocado) para capturar, parede por parede e fiada por fiada:

  - `seg_start_cm` de cada trecho de preenchimento;
  - as juntas INTERNAS que o trecho registra;
  - a junta de FRONTEIRA `seg_start_cm - BLOCK_JOINT_CM/2` (a junta contra
    o que estiver antes do trecho - peca de no', vao ou ponta livre), que
    e' justamente a que NAO e' registrada.

    python3 run_xa_nodefill.py [project_id]
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_xa as X  # noqa: E402

CAPTURE = []


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else "piloto_sintetico_2x2"
    engine = X.engine()
    # O motor e' montado com `from core.engine.wall_stepper import *`, entao
    # o nome que o SOLVER resolve vive no modulo `core.engine.wall_stepper`,
    # nao na fachada `wall_modeling`. Patch nos dois.
    import core.engine.wall_stepper as WS
    original = WS._layout_internal_joint_positions_cm

    def spy(layout, seg_start_cm, leading_is_open=False, trailing_is_open=False):
        out = original(layout, seg_start_cm, leading_is_open, trailing_is_open)
        CAPTURE.append({
            "seg_start_cm": round(float(seg_start_cm), 4),
            "layout_codes": [row[0] for row in layout],
            "internal_joints_cm": [round(float(v), 4) for v in out],
            "boundary_joint_cm": round(float(seg_start_cm)
                                       - engine.BLOCK_JOINT_CM / 2.0, 4),
            "leading_is_open": bool(leading_is_open),
            "trailing_is_open": bool(trailing_is_open),
        })
        return out

    WS._layout_internal_joint_positions_cm = spy
    engine._layout_internal_joint_positions_cm = spy
    try:
        run = X.run_solver(project_id)
    finally:
        WS._layout_internal_joint_positions_cm = original
        engine._layout_internal_joint_positions_cm = original

    conflicts = run["solve_result"].get("alignment_conflicts") or []

    # Todas as juntas de FRONTEIRA que nunca sao registradas, e quais delas
    # coincidem com uma junta INTERNA registrada por outro trecho.
    internal = set()
    for row in CAPTURE:
        for value in row["internal_joints_cm"]:
            internal.add(round(value, 2))
    boundary = sorted(set(round(row["boundary_joint_cm"], 2) for row in CAPTURE))
    colliding = sorted(v for v in boundary if v in internal)

    report = {
        "project_id": project_id,
        "n_chamadas_layout": len(CAPTURE),
        "alignment_conflicts_reportados": len(conflicts),
        "juntas_de_fronteira_distintas": boundary,
        "juntas_de_fronteira_que_coincidem_com_junta_interna": colliding,
        "amostra_trechos": CAPTURE[:12],
        "veredito": (
            "A junta de fronteira (peca de no'/vao | primeiro bloco do "
            "trecho) NUNCA entra em `_layout_internal_joint_positions_cm` - "
            "a funcao so' devolve juntas ENTRE blocos do mesmo layout. "
            "Logo ela nunca chega a `course_a_joint_positions_cm` nem ao "
            "`_count_joint_coincidences_cm` que alimenta `alignment_conflicts`."
        ),
    }
    print(json.dumps({k: v for k, v in report.items() if k != "amostra_trechos"},
                     indent=2, ensure_ascii=False)[:2500])
    X.write_json(X.out_path("out_xa_nodefill_%s.json" % project_id), report)
    return report


if __name__ == "__main__":
    main()
