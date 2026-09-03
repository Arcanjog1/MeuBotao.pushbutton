# -*- coding: utf-8 -*-
"""Tabela PECA A PECA dos blocos que invadem vao de PORTA (itens 3 e 4 do
fechamento do CR-BLOCK-NODE-FILL-JOINT).

Uma linha por achado `OPENING_BLOCK_INSIDE_DOOR` / `OPENING_BLOCK_CROSSES_JAMB`
de porta, com: parede, fiada, cota da fiada, abertura e seu intervalo, codigo
e intervalo do bloco, sobreposicao, e o ESTAGIO que criou a peca
(`placement_reason` - STANDARD_FILL / OPENING_REPAIR_FILL / L_CORNER / ...).

Rodar nos dois pontos de codigo e comparar da' o antes/depois exigido.

    python3 run_nf_door_table.py <saida.json> [project_id]
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

DOOR_CODES = ("OPENING_BLOCK_INSIDE_DOOR", "OPENING_BLOCK_CROSSES_JAMB")


def build(project_id):
    from benchmark import runner
    run = runner.run_project(project_id, write_files=False)
    proj = run["result"]

    index = {}
    for wall in proj.get("walls") or []:
        for row in wall.get("rows") or []:
            for block in row.get("blocks") or []:
                index[block.get("id")] = (row, block)

    rows = []
    for finding in run["findings"]:
        if finding.get("code") not in DOOR_CODES:
            continue
        if finding.get("opening_kind") != "door":
            continue
        block_id = (finding.get("blocks") or [None])[0]
        row, block = index.get(block_id, ({}, {}))
        rows.append({
            "code": finding["code"],
            "wall": finding.get("wall"),
            "row": finding.get("row"),
            "elevation_cm": row.get("elevation_cm"),
            "opening": finding.get("opening"),
            "opening_t_cm": finding.get("opening_t_cm"),
            "block_id": block_id,
            "block_code": block.get("code"),
            "block_t_cm": finding.get("block_t_cm"),
            "overlap_cm": finding.get("overlap_cm"),
            "placement_reason": block.get("placement_reason"),
            "role": block.get("role"),
        })
    rows.sort(key=lambda r: (r["wall"] or "", r["row"] or 0, (r["block_t_cm"] or [0])[0]))
    return rows


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    out_path = argv[0] if argv else os.path.join(_HERE, "out_nf_door_table.json")
    project_id = argv[1] if len(argv) > 1 else "torre_easy_lo_r00_tgd"

    rows = build(project_id)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=1, sort_keys=True)
        handle.write("\n")

    dentro = [r for r in rows if r["code"] == "OPENING_BLOCK_INSIDE_DOOR"]
    print("%s: %d achados de porta (%d INSIDE, %d JAMB)"
          % (project_id, len(rows), len(dentro), len(rows) - len(dentro)))
    print("  INSIDE_DOOR por fiada : %s"
          % dict(sorted(collections.Counter(r["row"] for r in dentro).items())))
    print("  INSIDE_DOOR por estagio: %s"
          % dict(collections.Counter(r["placement_reason"] for r in dentro)))
    print("gravado em %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
