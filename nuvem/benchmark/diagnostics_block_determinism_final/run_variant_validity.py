# -*- coding: utf-8 -*-
"""PROVA de que a variante `endpoint_reversal` da bateria NAO e'
geometricamente valida em projeto com `walls_already_extended: False`.

A variante reparametriza as aberturas contra o comprimento do `input.json`
(`t' = L_input - t`). Mas o motor roda `extend_wall_ends_to_junctions`
ANTES de medir `t`, entao o eixo dele e' MAIOR: o vao invertido cai num
lugar FISICO diferente. Este script mede o deslocamento, em cm, de cada
abertura de cada parede - e roda a bateria separando os dois grupos, para
mostrar que o grupo de PERMUTACAO (sempre valido) converge.

    python3 run_variant_validity.py [project_id]
"""
import sys
import json

import lib_final as F
import variants as V

REVERSAL_VARIANTS = (
    "endpoint_reversal", "reverse_horizontal_only", "reverse_vertical_only",
    "random_endpoint_reversal_seed_1", "random_endpoint_reversal_seed_2",
)


def opening_world_positions(run_data):
    """{chave geometrica da parede: [(x_cm, y_cm) do centro de cada vao]} -
    a posicao FISICA de cada abertura, comparavel entre duas execucoes."""
    engine = F.L.engine()
    walls = run_data["walls_to_create"]
    openings = run_data["openings_per_wall"]
    out = {}
    for wall_idx in range(len(walls)):
        entries = engine.openings_for_wall(openings, wall_idx)
        if not entries:
            continue
        p0, _p1, direction, _length_ft, _th = engine._wall_axis_and_length(walls, wall_idx)
        centers = []
        for opening in entries:
            mid_ft = (opening[0] + opening[1]) / 2.0
            centers.append((round((p0.X + direction.X * mid_ft) * F.L.FT_TO_CM, 3),
                            round((p0.Y + direction.Y * mid_ft) * F.L.FT_TO_CM, 3)))
        out[str(F.L.wall_geom_key(walls, wall_idx))] = sorted(centers)
    return out


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else "piloto_sintetico_2x2"
    base_project = F.load_input(project_id)
    already_extended = bool((base_project.get("settings") or {}).get("walls_already_extended"))

    base_run = F.run_solver(project_id, input_project=base_project)
    base_positions = opening_world_positions(base_run)

    reversed_project = V.endpoint_reversal(base_project)
    reversed_run = F.run_solver(project_id, input_project=reversed_project)
    reversed_positions = opening_world_positions(reversed_run)

    shifts = []
    for key, centers in sorted(base_positions.items()):
        other = reversed_positions.get(key)
        if other is None or len(other) != len(centers):
            shifts.append({"wall": key, "erro": "conjunto de aberturas diferente"})
            continue
        for (bx, by), (rx, ry) in zip(centers, other):
            distance = ((bx - rx) ** 2 + (by - ry) ** 2) ** 0.5
            if distance > 1e-6:
                shifts.append({"wall": key, "base_cm": (bx, by),
                               "endpoint_reversal_cm": (rx, ry),
                               "deslocamento_cm": round(distance, 4)})

    # bateria separada por grupo
    groups = {"permutacao": {}, "reversao": {}}
    for name, project in [("baseline", base_project)] + list(V.build_all_variants(base_project)):
        run = F.run_solver(project_id, input_project=project)
        layers, _rows = F.final_layered_fingerprints(run)
        bucket = "reversao" if name in REVERSAL_VARIANTS else "permutacao"
        groups[bucket].setdefault(layers["global_result"]["fingerprint"], []).append(name)

    report = {
        "project_id": project_id,
        "walls_already_extended": already_extended,
        "variantes_de_reversao_sao_validas_aqui": already_extended,
        "n_aberturas_deslocadas_pela_reversao": len(shifts),
        "deslocamentos_distintos_cm": sorted(set(
            row["deslocamento_cm"] for row in shifts if "deslocamento_cm" in row)),
        "amostra_deslocamentos": shifts[:6],
        "fingerprints_por_grupo": {
            "permutacao": {"n_variantes": sum(len(v) for v in groups["permutacao"].values()),
                            "distintos": len(groups["permutacao"]),
                            "grupos": dict((fp[:12], names)
                                            for fp, names in groups["permutacao"].items())},
            "reversao": {"n_variantes": sum(len(v) for v in groups["reversao"].values()),
                          "distintos": len(groups["reversao"]),
                          "grupos": dict((fp[:12], names)
                                          for fp, names in groups["reversao"].items())},
        },
    }
    report["veredito"] = (
        "As variantes de reversao sao VALIDAS neste projeto (nenhuma abertura "
        "se desloca) - o grupo de reversao mede determinismo de verdade."
        if not shifts else
        "As variantes de reversao NAO sao geometricamente equivalentes neste "
        "projeto: %d abertura(s) mudam de lugar fisico (deslocamento %s cm). "
        "Comparar esse grupo NAO mede determinismo - ele compara plantas "
        "diferentes. So' o grupo de PERMUTACAO e' conclusivo aqui." % (
            len(shifts), report["deslocamentos_distintos_cm"])
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str)[:2000])
    F.write_json(F.out_path("out_variant_validity_%s.json" % project_id), report)
    return report


if __name__ == "__main__":
    main()
