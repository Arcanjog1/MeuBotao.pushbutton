# -*- coding: utf-8 -*-
"""CR-BLOCK-01 - benchmark HEADLESS reproduzivel de prisma/fiadas.

Roda o solver REAL sobre os projetos de `benchmark/projects/` e grava a
medicao em JSON. Nao usa Revit/MCP; nao inventa numero nenhum.

    python3 nuvem/benchmark/diagnostics_block_prisma/run_baseline.py \
        --out nuvem/benchmark/diagnostics_block_prisma/out_baseline.json

Depois da correcao, o MESMO comando com `--out out_after.json` produz a
medicao comparavel, e `compare.py` gera o antes/depois."""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import metrics  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.join(_HERE, "out_baseline.json"))
    parser.add_argument("--project", action="append", default=None,
                        help="mede so' este project_id (repetivel)")
    parser.add_argument("--variants", type=int, default=None,
                        help="variants_per_course (default: o do motor)")
    args = parser.parse_args(argv)

    project_ids = tuple(args.project) if args.project else metrics.PROJECT_IDS
    result = metrics.measure_all(project_ids, variants_per_course=args.variants)
    with open(args.out, "w") as handle:
        json.dump(result, handle, indent=1, sort_keys=True)
        handle.write("\n")

    totals = result["totals"]
    print("gravado em {0}".format(args.out))
    print("paredes com blocos: {0}/{1}".format(
        totals["walls_with_blocks"], totals["walls_considered"]))
    print("juntas internas: {0}".format(totals["internal_joints_total"]))
    for name in ("FORBIDDEN_JOINT_ALIGNMENT", "DOCUMENTED_EXCEPTION",
                 "UNCLASSIFIED_RULE_CONFLICT", "NO_ALIGNMENT"):
        print("  {0}: {1}".format(name, totals["joint_classes"].get(name, 0)))
    print("compensadores consecutivos: {0}".format(totals["consecutive_compensator_pairs"]))
    print("blocos dentro de abertura: {0}".format(totals["blocks_inside_opening"]))
    print("runtime total: {0}s".format(totals["runtime_s"]))
    for pid, project in sorted(result["projects"].items()):
        print("  {0}: fingerprint {1}".format(pid, project["fingerprint"]["sha256"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
