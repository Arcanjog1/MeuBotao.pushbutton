# -*- coding: utf-8 -*-
"""Item 31 da missao (D6): metricas de qualidade na ORDEM BASELINE, para
comparar MAIN/WALL GRAPH/FINALIZACAO no mesmo ponto de medicao.

    python3 run_d6_compare.py [project_id]
"""
import sys
import json

import lib_final as F


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else F.PRIMARY_PROJECT_ID
    run = F.run_solver(project_id, input_project=F.load_input(project_id))
    metrics = F.downstream_metrics(run)
    layers, _rows = F.final_layered_fingerprints(run)
    out = {
        "project_id": project_id,
        "pieces": metrics["pieces"],
        "by_placement_reason": metrics["by_placement_reason"],
        "by_code": metrics["coverage_pieces_by_code"],
        "non_modular": metrics["non_modular"],
        "intersection_failures": metrics["intersection_failures"],
        "alignment_conflicts": metrics["alignment_conflicts"],
        "collisions": metrics["collisions"],
        "door_void_violations": metrics["door_void_violations"],
        "n_rows_physical_layout": layers["physical_block_layouts"]["n_rows"],
        "runtime_s": metrics["runtime_s"],
    }
    print(json.dumps(out, sort_keys=True))
    return out


if __name__ == "__main__":
    main()
