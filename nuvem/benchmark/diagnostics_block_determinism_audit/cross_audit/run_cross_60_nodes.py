# -*- coding: utf-8 -*-
"""CROSS-AUDIT item 6 — re-audita ESPECIFICAMENTE as 60 identidades de nó
que o baseline (`out_divergent_nodes.json`, rodado na MAIN antes de
conhecer a CONTA 1) tinha encontrado divergentes entre as 24 ordens.

Roda a MESMA bateria de 24 ordens contra o código da CONTA 1 e verifica,
para cada uma das 60 identidades: quantas posições/tipos distintos elas
têm AGORA. Os 6 casos que "sumiam" em até 19/24 variantes são um gate
crítico à parte (missão item 6) — confirma explicitamente que agora
existem nas 24 ordens, com a mesma posição, mesmos braços, mesmo tipo, e
batem com o oráculo.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

import lib_det as L  # noqa: E402
import oracle as O  # noqa: E402
import variants as V  # noqa: E402
import run_oracle_divergence as ROD  # noqa: E402


def main():
    project_id = L.PRIMARY_PROJECT_ID

    with open(os.path.join(_PARENT, "out_divergent_nodes.json"), "r", encoding="utf-8") as fh:
        baseline_divergent = json.load(fh)["divergent_nodes"]

    baseline_identities = set()
    baseline_missing = []
    for e in baseline_divergent:
        identity = (e["identity_kind"], tuple(tuple(k) for k in e["identity_arm_wall_keys"]))
        baseline_identities.add(identity)
        if e["missing_in_variants"]:
            baseline_missing.append(identity)

    print("rodando bateria completa (24 ordens) no codigo da CONTA 1...")
    runs = ROD._run_all(project_id)  # noqa: SLF001 (reuso deliberado do baseline)
    cross_divergent = ROD.find_divergent_nodes(runs)

    cross_identities = set()
    for e in cross_divergent:
        identity = (e["identity_kind"], tuple(e["identity_arm_wall_keys"]))
        cross_identities.add(identity)

    still_divergent = baseline_identities & cross_identities
    fixed = baseline_identities - cross_identities
    new_divergent = cross_identities - baseline_identities

    # -------- os 6 casos "somem" (gate critico) --------
    baseline_walls = runs["baseline"]["walls_to_create"]
    wall_geom_rows = L.all_wall_geom_keys(baseline_walls)
    by_identity_per_run = dict((name, ROD._collect_nodes_by_identity(run))  # noqa: SLF001
                                for name, run in runs.items())

    missing_case_reports = []
    for identity in baseline_missing:
        kind, arm_keys = identity
        present_in_all = True
        points = set()
        kinds = set()
        for name, per_run in by_identity_per_run.items():
            entries = per_run.get(identity)
            if not entries:
                present_in_all = False
                continue
            points.add(entries[0]["point_cm"])
            kinds.add(entries[0]["kind"])
        oracle_verdicts = []
        for p in points:
            r = O.classify_point(O.walls_from_geom_rows(wall_geom_rows), p)
            oracle_verdicts.append({"point_cm": p, "oracle_kind": r["kind"],
                                     "agrees_with_engine": r["kind"] in kinds})
        missing_case_reports.append({
            "identity_kind": kind,
            "identity_arm_wall_keys": arm_keys,
            "present_in_all_24_now": present_in_all,
            "n_distinct_points_now": len(points),
            "n_distinct_kinds_now": len(kinds),
            "single_canonical_point": (len(points) == 1),
            "single_kind": (len(kinds) == 1),
            "oracle_verdicts": oracle_verdicts,
        })

    out = {
        "project_id": project_id,
        "n_baseline_divergent_identities": len(baseline_identities),
        "n_baseline_missing_case_identities": len(baseline_missing),
        "n_still_divergent_now": len(still_divergent),
        "n_fixed_now": len(fixed),
        "n_new_divergent_now": len(new_divergent),
        "still_divergent_identities": [
            {"kind": k, "arm_wall_keys": list(a)} for k, a in sorted(still_divergent, key=str)
        ],
        "new_divergent_identities": [
            {"kind": k, "arm_wall_keys": list(a)} for k, a in sorted(new_divergent, key=str)
        ],
        "n_cross_divergent_total_now": len(cross_identities),
        "missing_case_gate": {
            "n_cases": len(missing_case_reports),
            "n_now_present_in_all_24_with_single_point_and_kind": sum(
                1 for r in missing_case_reports
                if r["present_in_all_24_now"] and r["single_canonical_point"] and r["single_kind"]
            ),
            "cases": missing_case_reports,
        },
    }
    L.write_json(os.path.join(_HERE, "out_cross_60_nodes.json"), out)

    print("baseline: 60 identidades divergentes, das quais 6 'somem' em ate' 19/24 variantes")
    print("agora (codigo da CONTA 1):")
    print("  ainda divergentes:", len(still_divergent))
    print("  corrigidas (nao divergem mais):", len(fixed))
    print("  NOVAS divergencias (nao existiam no baseline):", len(new_divergent))
    print("  total de identidades divergentes agora (24 ordens, qualquer causa):", len(cross_identities))
    print()
    print("gate critico (6 nos que sumiam):")
    mc = out["missing_case_gate"]
    print("  ", mc["n_now_present_in_all_24_with_single_point_and_kind"], "/", mc["n_cases"],
          "agora presentes em TODAS as 24 ordens com posicao E tipo unicos")


if __name__ == "__main__":
    main()
