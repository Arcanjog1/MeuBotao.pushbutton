"""Pinned package provenance and loader fail-closed behavior without Revit."""
import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package(tmp_path):
    contents = {"Script.py": b"# loader\n", "beta_package.py": b"# verifier\n",
                "core/wall_modeling.py": b"# pinned engine\n", "core/__init__.py": b""}
    for relative, content in contents.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    manifest = {"schema": 1, "controlled_beta": True, "head": "a" * 40,
                "sha256": {p: hashlib.sha256(v).hexdigest() for p, v in contents.items()}}
    (tmp_path / "beta-package.json").write_text(json.dumps(manifest))
    return manifest


def test_verified_package_has_exact_head_and_local_entry(tmp_path):
    package(tmp_path)
    entry, head = load(ROOT / "beta_package.py").verify_beta_package(str(tmp_path))
    assert Path(entry) == tmp_path / "core/wall_modeling.py"
    assert head == "a" * 40


@pytest.mark.parametrize("damage", ["modified", "missing", "extra", "mutable_head", "bytecode", "escape"])
def test_mixed_or_incomplete_packages_are_rejected(tmp_path, damage):
    manifest = package(tmp_path)
    if damage == "modified":
        (tmp_path / "core/wall_modeling.py").write_text("changed")
    elif damage == "missing":
        (tmp_path / "core/wall_modeling.py").unlink()
    elif damage == "extra":
        (tmp_path / "core/extra.py").write_text("changed")
    elif damage == "bytecode":
        (tmp_path / "core/__pycache__").mkdir()
        (tmp_path / "core/__pycache__/wall_modeling.pyc").write_bytes(b"stale")
    else:
        if damage == "mutable_head":
            manifest["head"] = "main"
        else:
            manifest["sha256"]["core/../../outside.py"] = "b" * 64
        (tmp_path / "beta-package.json").write_text(json.dumps(manifest))
    with pytest.raises((ValueError, OSError)):
        load(ROOT / "beta_package.py").verify_beta_package(str(tmp_path))


def test_corrupt_beta_never_falls_back_to_network_or_normal_cache(tmp_path):
    package(tmp_path)
    (tmp_path / "beta_package.py").write_bytes((ROOT / "beta_package.py").read_bytes())
    tree = ast.parse((ROOT / "Script.py").read_text(encoding="utf-8-sig"))
    function, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_load_entry_point"]
    namespace = {"os": os, "io": io, "sys": sys, "_pasta_do_loader": lambda: str(tmp_path),
                 "_get_token": lambda: pytest.fail("Network/cache fallback entered")}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "loader-test", "exec"), namespace)
    with pytest.raises(ValueError, match="hash mismatch"):
        namespace["_load_entry_point"]()


def test_builder_exports_commit_not_dirty_worktree(tmp_path):
    repo, output = tmp_path / "repo", tmp_path / "package"
    repo.mkdir()

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, stderr=subprocess.DEVNULL).decode().strip()

    git("init")
    git("config", "user.name", "Beta Test")
    git("config", "user.email", "test@example.invalid")
    for p in ("Script.py", "beta_package.py", "nuvem/core/wall_modeling.py"):
        target = repo / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# committed\n")
    git("add", ".")
    git("commit", "-m", "fixture")
    head = git("rev-parse", "HEAD")
    (repo / "nuvem/core/wall_modeling.py").write_text("# uncommitted\n")
    builder = load(ROOT / "tools/beta/build_package.py")
    manifest = builder.build(repo, head, output)
    assert manifest["head"] == head
    assert (output / "core/wall_modeling.py").read_text() == "# committed\n"
    with pytest.raises(ValueError, match="exact full commit"):
        builder.build(repo, "HEAD", tmp_path / "mutable")
    with pytest.raises(FileExistsError):
        builder.build(repo, head, output)
