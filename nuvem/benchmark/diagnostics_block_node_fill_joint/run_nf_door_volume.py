# -*- coding: utf-8 -*-
"""MATERIAL fisico dentro do vao de porta (item 6 do fechamento).

`OPENING_BLOCK_INSIDE_DOOR` conta PECAS e depende da fronteira de 90% do
validador (`INSIDE_RATIO`): a MESMA quantidade de material, cortada em mais
pedacos, muda a contagem sem mudar o predio. Este script mede o que nao
depende dessa fronteira - comprimento e AREA (comprimento x altura real da
interseccao vertical) de bloco dentro do vazio de porta.

Separa tambem por ALTURA da interseccao: uma fiada que so' toca 1 cm do vao
e uma que esta' 19 cm dentro dele nao sao o mesmo defeito.

    python3 run_nf_door_volume.py <saida.json> [project_id]
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

BLOCK_HEIGHT_CM = 19.0


def measure(project_id):
    from benchmark import runner, analysis, model
    run = runner.run_project(project_id, write_files=False)
    proj = run["result"]

    total = {"overlap_len_cm": 0.0, "overlap_area_cm2": 0.0, "blocks": 0}
    por_altura = collections.defaultdict(
        lambda: {"len_cm": 0.0, "blocks": 0, "rows": set()})
    for wall in proj.get("walls") or []:
        for row in model.rows_sorted(wall):
            z_lo = float(row["elevation_cm"])
            z_hi = z_lo + BLOCK_HEIGHT_CM
            for opening in wall.get("openings") or []:
                if opening.get("kind") != model.OPENING_DOOR:
                    continue
                dz = min(z_hi, float(opening["head_cm"])) - max(z_lo, float(opening["sill_cm"]))
                if dz <= 1e-6:
                    continue
                for block in row.get("blocks") or []:
                    if block.get("role") in (model.ROLE_LINTEL, model.ROLE_COUNTER_LINTEL,
                                             model.ROLE_CHANNEL_BLOCK):
                        continue
                    overlap = analysis.interval_overlap_cm(
                        (block["t_start_cm"], block["t_end_cm"]),
                        (opening["t_start_cm"], opening["t_end_cm"]))
                    if overlap <= model.OVERLAP_TOLERANCE_CM:
                        continue
                    total["overlap_len_cm"] += overlap
                    total["overlap_area_cm2"] += overlap * dz
                    total["blocks"] += 1
                    bucket = por_altura[round(dz, 2)]
                    bucket["len_cm"] += overlap
                    bucket["blocks"] += 1
                    bucket["rows"].add(row["row"])
    return {
        "project_id": project_id,
        "totais": dict((k, round(v, 3)) for k, v in total.items()),
        "por_altura_da_interseccao_cm": dict(
            (str(k), {"len_cm": round(v["len_cm"], 2), "blocks": v["blocks"],
                      "fiadas": sorted(v["rows"])})
            for k, v in sorted(por_altura.items())),
    }


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    out_path = argv[0] if argv else os.path.join(_HERE, "out_nf_door_volume.json")
    project_id = argv[1] if len(argv) > 1 else "torre_easy_lo_r00_tgd"

    payload = measure(project_id)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
