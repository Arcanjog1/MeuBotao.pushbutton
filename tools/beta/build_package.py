"""Export an immutable commit for offline controlled beta. Does not install or run Revit."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def build(repo, revision, output):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo)

    head = git("rev-parse", "--verify", revision + "^{commit}").decode().strip()
    if revision != head:
        raise ValueError("Use the exact full commit SHA, not a mutable branch or abbreviation")
    paths = git("ls-tree", "-rz", "--name-only", head).decode("utf-8").split("\0")
    source_paths = [p for p in paths if p in ("Script.py", "beta_package.py") or
                    (p.startswith("nuvem/core/") and p.endswith(".py"))]
    if not {"Script.py", "beta_package.py", "nuvem/core/wall_modeling.py"}.issubset(source_paths):
        raise ValueError("Commit does not contain the beta loader and verifier")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for source in source_paths:
        relative = source[len("nuvem/"):] if source.startswith("nuvem/") else source
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        content = git("show", head + ":" + source)
        target.write_bytes(content)
        hashes[relative] = hashlib.sha256(content).hexdigest()
    manifest = {"schema": 1, "controlled_beta": True, "head": head,
                "created_utc": datetime.now(timezone.utc).isoformat(), "sha256": hashes,
                "status": "ENGINEERING_CANDIDATE_NOT_BETA_APPROVAL"}
    (output / "beta-package.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.repo, args.head, args.output), indent=2))


if __name__ == "__main__":
    main()
