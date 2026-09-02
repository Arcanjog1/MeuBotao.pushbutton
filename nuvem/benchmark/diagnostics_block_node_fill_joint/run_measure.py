# -*- coding: utf-8 -*-
"""Medicao completa do CR-BLOCK-NODE-FILL-JOINT num ponto do codigo.

    python3 nuvem/benchmark/diagnostics_block_node_fill_joint/run_measure.py \
        --out .../out_nf_head.json [--project piloto_sintetico_2x2]
"""
import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import lib_nf as NF  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=NF.out_path("out_nf.json"))
    parser.add_argument("--project", action="append", default=None)
    args = parser.parse_args(argv)
    project_ids = tuple(args.project) if args.project else NF.PROJECT_IDS

    payload = NF.measure_all(project_ids)
    NF.write_json(args.out, payload)

    print("gravado em {0}".format(args.out))
    for pid in project_ids:
        row = payload["projects"][pid]
        print("\n== {0}".format(pid))
        for name, value in sorted(row["codes"].items()):
            if value:
                print("   {0:<34} {1}".format(name, value))
        print("   {0:<34} {1}".format("alignment_conflicts", row["solve"]["alignment_conflicts"]))
        print("   {0:<34} {1}".format("node_boundary_conflicts", row["solve"]["node_boundary_conflicts"]))
        print("   {0:<34} {1}".format("collisions", row["solve"]["collisions"]))
        print("   {0:<34} {1}".format("door_void_violations", row["solve"]["door_void_violations"]))
        print("   {0:<34} {1}".format("jamb_exceptions", row["solve"]["jamb_exceptions"]))
        print("   tempo(s) {0}".format(row["timing_s"]))
    band = payload["cr_block_01"]["totals"]["forbidden_by_band"]
    print("\n== CR-BLOCK-01 (totais)")
    print("   same-band forbidden  {0}".format(band.get("same_band")))
    print("   cross-band forbidden {0}".format(band.get("cross_band")))
    print("   compensadores consec {0}".format(
        payload["cr_block_01"]["totals"]["consecutive_compensator_pairs"]))
    print("   joint_classes {0}".format(payload["cr_block_01"]["totals"]["joint_classes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
