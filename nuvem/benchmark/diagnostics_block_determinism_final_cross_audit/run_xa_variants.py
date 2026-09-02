# -*- coding: utf-8 -*-
"""Bateria INDEPENDENTE de determinismo do cross-audit final.

Roda, por projeto:
  baseline + 20 variantes de PERMUTACAO + 10 de REVERSAO (5 subconjuntos x
  {ingenua, geometrica}), e agrupa por fingerprint EM CADA CAMADA.

Classifica cada variante como VALID_METAMORPHIC_VARIANT ou
INVALID_METAMORPHIC_VARIANT medindo a planta FISICA que ela produz (posicao
de mundo do centro de cada abertura + eixo esticado de cada parede),
NUNCA por confianca no nome da variante.

    python3 run_xa_variants.py <project_id>
"""
import os
import sys
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_xa as X          # noqa: E402
import variants_xa as V     # noqa: E402


def physical_plan_signature(project):
    """Assinatura da PLANTA FISICA que este `input.json` produz no motor:
    eixos esticados (pontas ordenadas) + centro de mundo de cada abertura.
    Duas entradas com a MESMA assinatura descrevem o mesmo predio."""
    _nodes, walls, _e2n, openings = X.plan_only(project)
    axes = sorted(X.wall_key(walls, i) for i in range(len(walls)))
    centers = []
    for wall_idx in range(len(walls)):
        line, _t, _l = walls[wall_idx]
        p0 = line.GetEndPoint(0)
        p1 = line.GetEndPoint(1)
        length = math.hypot(p1.X - p0.X, p1.Y - p0.Y)
        if length <= 0:
            continue
        ux, uy = (p1.X - p0.X) / length, (p1.Y - p0.Y) / length
        for opening in openings[wall_idx] or []:
            mid = (opening[0] + opening[1]) / 2.0
            centers.append((
                round((p0.X + ux * mid) * X.FT_TO_CM, 2),
                round((p0.Y + uy * mid) * X.FT_TO_CM, 2),
                round((opening[1] - opening[0]) * X.FT_TO_CM, 2),
                round(opening[2] * X.FT_TO_CM, 2),
                round(opening[3] * X.FT_TO_CM, 2),
            ))
    return {"axes": axes, "openings": sorted(centers)}


def main():
    project_id = sys.argv[1]
    base = X.load_input(project_id)
    already_extended = bool((base.get("settings") or {}).get("walls_already_extended"))
    lengths_cm = V.engine_axis_lengths_cm(base, X.plan_only)

    cases = [("baseline", base)]
    cases += V.build_permutation_variants(base)
    cases += V.build_reversal_variants(base, lengths_cm)

    base_sig = physical_plan_signature(base)

    rows = []
    for name, project in cases:
        sig = physical_plan_signature(project)
        same_axes = sig["axes"] == base_sig["axes"]
        same_openings = sig["openings"] == base_sig["openings"]
        valid = same_axes and same_openings
        shift = None
        if not same_openings:
            worst = 0.0
            for (bx, by, bw, bs, bh), (ox, oy, ow, os_, oh) in zip(
                    base_sig["openings"], sig["openings"]):
                worst = max(worst, math.hypot(bx - ox, by - oy))
            shift = round(worst, 4)
        run = X.run_solver(project_id, input_project=project)
        layers, _rows = X.fingerprints(run)
        rows.append({
            "variant": name,
            "family": ("permutacao" if name == "baseline" or not name.startswith("reversal")
                       else ("reversao_ingenua" if "_naive_" in name else "reversao_geometrica")),
            "validity": "VALID_METAMORPHIC_VARIANT" if valid else "INVALID_METAMORPHIC_VARIANT",
            "eixos_iguais": same_axes,
            "aberturas_iguais": same_openings,
            "maior_deslocamento_de_abertura_cm": shift,
            "layers": dict((k, v["fingerprint"]) for k, v in layers.items()),
            "n_rows": dict((k, v["n_rows"]) for k, v in layers.items()),
            "elapsed_s": round(run["elapsed_s"], 3),
        })
        print("  %-42s %-28s %s" % (name, rows[-1]["validity"],
                                    rows[-1]["layers"]["global_result"][:12]))

    valid_rows = [r for r in rows if r["validity"] == "VALID_METAMORPHIC_VARIANT"]
    by_layer = {}
    for layer in [name for name, _f in X.LAYERS] + ["global_result"]:
        groups = {}
        for row in valid_rows:
            groups.setdefault(row["layers"][layer], []).append(row["variant"])
        by_layer[layer] = {"n_fingerprints": len(groups),
                           "grupos": dict((fp[:12], sorted(names))
                                          for fp, names in groups.items())}

    invalid_groups = {}
    for row in rows:
        if row["validity"] != "VALID_METAMORPHIC_VARIANT":
            invalid_groups.setdefault(row["layers"]["global_result"][:12],
                                      []).append(row["variant"])

    report = {
        "project_id": project_id,
        "walls_already_extended": already_extended,
        "n_variantes": len(rows),
        "n_validas": len(valid_rows),
        "n_invalidas": len(rows) - len(valid_rows),
        "fingerprints_por_camada_SOMENTE_VARIANTES_VALIDAS": by_layer,
        "variantes_invalidas": invalid_groups,
        "detalhe": rows,
    }
    X.write_json(X.out_path("out_xa_variants_%s.json" % project_id), report)
    print(json.dumps({
        "project_id": project_id,
        "walls_already_extended": already_extended,
        "validas": len(valid_rows), "invalidas": len(rows) - len(valid_rows),
        "fingerprints_por_camada": dict(
            (k, v["n_fingerprints"]) for k, v in by_layer.items()),
    }, indent=2))
    return report


if __name__ == "__main__":
    main()
