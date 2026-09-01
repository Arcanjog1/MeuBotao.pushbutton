# -*- coding: utf-8 -*-
"""CR-BLOCK-01 - ANTES x DEPOIS x DELTA x DELTA%.

    python3 nuvem/benchmark/diagnostics_block_prisma/compare.py \
        --before out_baseline.json --after out_after.json \
        --out compare_before_after.json
"""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

# Metricas em que CRESCER e' regressao (gates da secao 19 do CR).
LOWER_IS_BETTER = (
    "FORBIDDEN_JOINT_ALIGNMENT", "UNCLASSIFIED_RULE_CONFLICT",
    "consecutive_compensator_pairs", "blocks_inside_opening", "collisions",
    "door_void_violations", "non_modular", "alignment_conflicts",
    "walls_audit_failed", "walls_without_blocks", "intersection_failures",
)
# Metricas em que ENCOLHER e' regressao.
HIGHER_IS_BETTER = ("walls_with_blocks",)


def _flat(project):
    out = {}
    for key, value in project.items():
        if key in ("joint_classes", "blocks_by_code", "audit_problems",
                   "consecutive_compensator_runs_by_len"):
            for name, count in (value or {}).items():
                out["{0}.{1}".format(key, name)] = count
        elif isinstance(value, (int, float)):
            out[key] = value
    stagger = project.get("stagger") or {}
    for name in ("min_cm", "mean_cm", "count"):
        if stagger.get(name) is not None:
            out["stagger.{0}".format(name)] = stagger[name]
    return out


def _delta_rows(before, after):
    rows = {}
    for key in sorted(set(before) | set(after)):
        b = before.get(key, 0)
        a = after.get(key, 0)
        delta = a - b
        pct = None if not b else round(delta * 100.0 / b, 2)
        verdict = "igual"
        if delta:
            short = key.split(".")[-1]
            if short in LOWER_IS_BETTER:
                verdict = "melhorou" if delta < 0 else "REGREDIU"
            elif short in HIGHER_IS_BETTER:
                verdict = "melhorou" if delta > 0 else "REGREDIU"
            else:
                verdict = "mudou"
        rows[key] = {"antes": b, "depois": a, "delta": round(delta, 3),
                     "delta_pct": pct, "veredito": verdict}
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", default=os.path.join(_HERE, "out_baseline.json"))
    parser.add_argument("--after", default=os.path.join(_HERE, "out_after.json"))
    parser.add_argument("--out", default=os.path.join(_HERE, "compare_before_after.json"))
    args = parser.parse_args(argv)

    with open(args.before) as handle:
        before = json.load(handle)
    with open(args.after) as handle:
        after = json.load(handle)

    result = {"totals": _delta_rows(_flat(before["totals"]), _flat(after["totals"])),
              "projects": {}, "fingerprints": {}}
    for pid in sorted(set(before["projects"]) | set(after["projects"])):
        b = before["projects"].get(pid) or {}
        a = after["projects"].get(pid) or {}
        result["projects"][pid] = _delta_rows(_flat(b), _flat(a))
        result["fingerprints"][pid] = {
            "antes": (b.get("fingerprint") or {}).get("sha256"),
            "depois": (a.get("fingerprint") or {}).get("sha256"),
            "mudou": (b.get("fingerprint") or {}).get("sha256")
                     != (a.get("fingerprint") or {}).get("sha256"),
        }

    regressions = sorted(k for k, v in result["totals"].items()
                         if v["veredito"] == "REGREDIU")
    result["regressoes"] = regressions

    with open(args.out, "w") as handle:
        json.dump(result, handle, indent=1, sort_keys=True)
        handle.write("\n")

    print("gravado em {0}".format(args.out))
    for key, row in sorted(result["totals"].items()):
        if row["delta"]:
            print("  {0:<52} {1} -> {2}  ({3:+g}{4})  {5}".format(
                key, row["antes"], row["depois"], row["delta"],
                "" if row["delta_pct"] is None else ", {0:+g}%".format(row["delta_pct"]),
                row["veredito"]))
    print("regressoes: {0}".format(regressions or "nenhuma"))
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())
