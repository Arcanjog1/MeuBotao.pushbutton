"""Evaluate saved diagnostic geometry with the official reference, without a solve or writes to the benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite evidence")
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "nuvem"))
    from benchmark.runner import evaluate_project
    data = json.loads(args.artifact.read_text(encoding="utf-8"))
    project = data.get("result_project") or data.get("full", {}).get("project")
    if project is None:
        parser.error("Artifact has no saved result geometry")
    reference_path = root / "nuvem/benchmark/projects" / args.project / "reference.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    findings, score, comparison = evaluate_project(project, reference)
    payload = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
               "artifact": str(args.artifact), "artifact_sha256": hashlib.sha256(args.artifact.read_bytes()).hexdigest(),
               "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
               "scope": "Saved geometry; all validators with official reference context. Region boundaries may differ.",
               "findings": findings, "score": score, "comparison": comparison}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, separators=(",", ":"))
    print(json.dumps({"findings": score["findings_by_code"], "validator_errors": score["validator_errors"]}))


if __name__ == "__main__":
    main()
