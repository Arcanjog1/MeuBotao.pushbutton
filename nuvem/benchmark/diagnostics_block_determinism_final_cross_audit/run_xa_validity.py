# -*- coding: utf-8 -*-
"""VALIDADE METAMORFICA de cada variante (item 7 da missao), medida so' na
PLANTA (planejamento do motor), sem rodar o solver.

Uma variante e' VALID_METAMORPHIC_VARIANT quando o predio que ela descreve
para o motor e' FISICAMENTE o mesmo do baseline:

  - o conjunto de eixos ESTICADOS (pontas ordenadas + espessura) e' igual;
  - cada abertura fica no MESMO ponto de mundo, com a mesma largura,
    peitoril e verga.

A comparacao usa tolerancia FISICA (0,05 cm = meio milimetro), nao
igualdade exata de float: `t' = L - t` reintroduz ruido de ultimo bit que
nao muda nada construtivo e nao pode ser confundido com "outra planta".

    python3 run_xa_validity.py [project_id ...]
"""
import os
import sys
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_xa as X          # noqa: E402
import variants_xa as V     # noqa: E402

TOL_CM = 0.05


def plan_signature(project):
    _nodes, walls, _e2n, openings = X.plan_only(project)
    axes = sorted(X.wall_key(walls, i) for i in range(len(walls)))
    entries = []
    for wall_idx in range(len(walls)):
        line, _t, _l = walls[wall_idx]
        p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
        length = math.hypot(p1.X - p0.X, p1.Y - p0.Y)
        if length <= 0:
            continue
        ux, uy = (p1.X - p0.X) / length, (p1.Y - p0.Y) / length
        for opening in openings[wall_idx] or []:
            mid = (opening[0] + opening[1]) / 2.0
            entries.append((
                (p0.X + ux * mid) * X.FT_TO_CM, (p0.Y + uy * mid) * X.FT_TO_CM,
                (opening[1] - opening[0]) * X.FT_TO_CM,
                opening[2] * X.FT_TO_CM, opening[3] * X.FT_TO_CM,
            ))
    entries.sort(key=lambda e: (round(e[0], 3), round(e[1], 3), round(e[2], 3)))
    return axes, entries


def compare(base, other):
    axes_a, openings_a = base
    axes_b, openings_b = other
    if axes_a != axes_b:
        return False, None, "eixos diferentes"
    if len(openings_a) != len(openings_b):
        return False, None, "numero de aberturas diferente (%d x %d)" % (
            len(openings_a), len(openings_b))
    worst_pos = 0.0
    worst_dim = 0.0
    for a, b in zip(openings_a, openings_b):
        worst_pos = max(worst_pos, math.hypot(a[0] - b[0], a[1] - b[1]))
        worst_dim = max(worst_dim, abs(a[2] - b[2]), abs(a[3] - b[3]), abs(a[4] - b[4]))
    ok = worst_pos <= TOL_CM and worst_dim <= TOL_CM
    return ok, round(worst_pos, 6), ("deslocamento maximo %.4f cm / diferenca de "
                                     "dimensao %.4f cm" % (worst_pos, worst_dim))


def main():
    project_ids = sys.argv[1:] or ["piloto_sintetico_2x2", "torre_easy_lo_r00_tgd",
                                   "torre_easy_lo_r00_tp1"]
    report = {}
    for project_id in project_ids:
        base = X.load_input(project_id)
        lengths_cm = V.engine_axis_lengths_cm(base, X.plan_only)
        base_sig = plan_signature(base)
        rows = []
        cases = ([("baseline", base)] + V.build_permutation_variants(base)
                 + V.build_reversal_variants(base, lengths_cm))
        for name, project in cases:
            ok, shift, detail = compare(base_sig, plan_signature(project))
            rows.append({"variant": name,
                         "validity": "VALID_METAMORPHIC_VARIANT" if ok
                                     else "INVALID_METAMORPHIC_VARIANT",
                         "deslocamento_cm": shift, "detalhe": detail})
        report[project_id] = {
            "walls_already_extended": bool(
                (base.get("settings") or {}).get("walls_already_extended")),
            "tolerancia_cm": TOL_CM,
            "n_validas": sum(1 for r in rows if r["validity"].startswith("VALID")),
            "n_invalidas": sum(1 for r in rows if r["validity"].startswith("INVALID")),
            "invalidas": [r for r in rows if r["validity"].startswith("INVALID")],
            "detalhe": rows,
        }
        print(project_id, "validas=%d invalidas=%d" % (
            report[project_id]["n_validas"], report[project_id]["n_invalidas"]))
        for r in report[project_id]["invalidas"]:
            print("   INVALIDA:", r["variant"], "-", r["detalhe"])
    X.write_json(X.out_path("out_xa_validity.json"), report)
    return report


if __name__ == "__main__":
    main()
