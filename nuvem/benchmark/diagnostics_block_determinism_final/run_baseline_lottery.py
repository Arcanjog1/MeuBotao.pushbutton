# -*- coding: utf-8 -*-
"""Item 34 da missao: o valor gravado em `baseline.json` e' uma PROPRIEDADE
do projeto ou apenas o resultado de UMA ordem de entrada?

Roda o MESMO projeto nas 24 ordens da bateria e reporta, para cada codigo
critico, a FAIXA (min/max/spread) e o valor do baseline. Um baseline cujo
valor so' aparece em uma fracao das ordens - e cuja faixa e' larga - nao e'
uma referencia canonica: e' a fotografia de um sorteio.

As variantes sao separadas em dois grupos, porque nem toda variante da
bateria e' valida em todo projeto:

  - PERMUTACAO (19): so' reordenam a lista. Sempre validas.
  - REVERSAO (5): invertem o SENTIDO de desenho e REPARAMETRIZAM as
    aberturas contra o comprimento do `input.json`. So' sao geometricamente
    equivalentes quando `settings.walls_already_extended` e' True; com
    False, `extend_wall_ends_to_junctions` alonga o eixo e as aberturas
    passam a ser medidas contra um comprimento MAIOR - a reversao entao
    desloca fisicamente cada vao em 2x a extensao (medido: 14cm no
    piloto_sintetico_2x2, exatamente uma espessura de parede). Nesse caso o
    grupo REVERSAO compara projetos DIFERENTES e nao mede determinismo.

    python3 run_baseline_lottery.py [project_id]
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

import lib_final as F
import variants as V

from benchmark import runner, solver_bridge          # noqa: E402
from benchmark.extract import from_solver            # noqa: E402

REVERSAL_VARIANTS = (
    "endpoint_reversal", "reverse_horizontal_only", "reverse_vertical_only",
    "random_endpoint_reversal_seed_1", "random_endpoint_reversal_seed_2",
)


def critical_by_code(project_id, input_project, reference):
    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, _notes) = solver_bridge.run_solver(input_project)
    result_project = from_solver.project_from_solver(
        project_id, solve_result, walls_to_create, nodes, openings_per_wall,
        catalog, base_z_ft, num_courses, metadata={})
    _findings, score, _cmp = runner.evaluate_project(result_project, reference)
    return dict(score.get("critical_by_code") or {})


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else F.PRIMARY_PROJECT_ID
    paths = runner.project_paths(project_id)
    base_project = F.load_input(project_id)
    already_extended = bool((base_project.get("settings") or {}).get("walls_already_extended"))

    reference = None
    if os.path.isfile(paths["reference"]):
        with open(paths["reference"], "r", encoding="utf-8") as handle:
            reference = json.load(handle)
    baseline = {}
    if os.path.isfile(paths["baseline"]):
        with open(paths["baseline"], "r", encoding="utf-8") as handle:
            baseline = (json.load(handle) or {}).get("critical_by_code") or {}

    runs = [("baseline", base_project)] + list(V.build_all_variants(base_project))
    per_variant = {}
    for name, project in runs:
        per_variant[name] = critical_by_code(project_id, project, reference)

    codes = set(baseline)
    for values in per_variant.values():
        codes.update(values)

    def group_range(names, code):
        values = [per_variant[n].get(code, 0) for n in names]
        return {"min": min(values), "max": max(values),
                "spread": max(values) - min(values), "distinct": len(set(values))}

    permutation = [n for n, _p in runs if n not in REVERSAL_VARIANTS]
    reversal = [n for n, _p in runs if n in REVERSAL_VARIANTS]

    report = {
        "project_id": project_id,
        "walls_already_extended": already_extended,
        "reversal_variants_are_valid_here": already_extended,
        "n_permutation_variants": len(permutation),
        "n_reversal_variants": len(reversal),
        "codes": {},
    }
    for code in sorted(codes):
        row = {
            "baseline_json": baseline.get(code, 0),
            "current_baseline_order": per_variant["baseline"].get(code, 0),
            "permutation": group_range(permutation, code),
        }
        if reversal:
            row["reversal"] = group_range(reversal, code)
        report["codes"][code] = row
        print("%-30s baseline.json=%-5s ordem_atual=%-5s permutacao=%s%s" % (
            code, row["baseline_json"], row["current_baseline_order"],
            row["permutation"],
            (" reversao=%s" % row["reversal"]) if reversal else ""))
    F.write_json(F.out_path("out_baseline_lottery_%s.json" % project_id), report)
    return report


if __name__ == "__main__":
    main()
