"""Export an immutable commit for offline controlled beta. Does not install or run Revit.

Nome canonico do pacote (2026-09-23): `modulacao-<branch>-<sha curto>.zip`
(ex.: modulacao-main-1a2b3c4.zip) - o pacote e' a versao canonica da branch
no commit, nunca "a versao de um PR". O manifest registra `head` (SHA
completo), `branch` e `package_name`; o loader mostra o SHA no banner."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def package_name(branch, head):
    return "modulacao-{}-{}.zip".format(branch.replace("/", "-"), head[:7])


def build(repo, revision, output, branch="main"):
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
    manifest = {"schema": 1, "controlled_beta": True, "head": head, "branch": branch,
                "package_name": package_name(branch, head),
                "created_utc": datetime.now(timezone.utc).isoformat(), "sha256": hashes,
                "status": "ENGINEERING_CANDIDATE_NOT_BETA_APPROVAL"}
    (output / "beta-package.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def zip_package(output, zip_path=None):
    """Zipa a pasta exportada (raiz do zip = conteudo da pasta do botao)."""
    output = Path(output)
    manifest = json.loads((output / "beta-package.json").read_text(encoding="utf-8"))
    zip_path = Path(zip_path) if zip_path else output.parent / manifest["package_name"]
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                archive.write(str(path), path.relative_to(output).as_posix())
    return zip_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--zip", action="store_true", help="tambem gera modulacao-<branch>-<sha>.zip ao lado")
    args = parser.parse_args()
    manifest = build(args.repo, args.head, args.output, branch=args.branch)
    print(json.dumps(manifest, indent=2))
    if args.zip:
        print(zip_package(args.output))


if __name__ == "__main__":
    main()
