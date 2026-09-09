"""Verify a controlled offline beta package before importing any solver code."""
import hashlib
import json
import os
import re


def verify_beta_package(directory):
    directory = os.path.realpath(directory)
    with open(os.path.join(directory, "beta-package.json"), "r") as handle:
        manifest = json.load(handle)
    if manifest.get("schema") != 1 or manifest.get("controlled_beta") is not True:
        raise ValueError("Invalid controlled beta manifest")
    if not re.match(r"^[0-9a-f]{40}$", manifest.get("head", "")):
        raise ValueError("Beta requires an exact commit SHA")
    hashes = manifest.get("sha256")
    if not isinstance(hashes, dict) or not {"Script.py", "beta_package.py", "core/wall_modeling.py"}.issubset(hashes):
        raise ValueError("Incomplete beta package")
    for relative, expected in hashes.items():
        if relative not in ("Script.py", "beta_package.py") and not relative.startswith("core/"):
            raise ValueError("Unexpected beta path: " + relative)
        if "\\" in relative or ".." in relative.split("/") or not relative.endswith(".py"):
            raise ValueError("Invalid beta path: " + relative)
        target = os.path.realpath(os.path.join(directory, *relative.split("/")))
        if not target.startswith(directory + os.sep):
            raise ValueError("Beta path escapes package: " + relative)
        with open(target, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        if actual != expected:
            raise ValueError("Beta package hash mismatch: " + relative)
    core_files = set()
    for parent, _dirs, files in os.walk(os.path.join(directory, "core")):
        # Bytecode must never replace a verified source file.
        for name in files:
            if not name.endswith(".py"):
                raise ValueError("Unexpected compiled/data file in beta core: " + name)
            if name.endswith(".py"):
                core_files.add(os.path.relpath(os.path.join(parent, name), directory).replace(os.sep, "/"))
    if core_files != {p for p in hashes if p.startswith("core/")}:
        raise ValueError("Beta core contains missing or unexpected modules")
    return os.path.join(directory, "core", "wall_modeling.py"), manifest["head"]
