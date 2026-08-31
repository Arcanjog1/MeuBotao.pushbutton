"""Leitura do repositorio para montar o contexto do revisor.

Tudo aqui e' read-only e passa por redacao antes de virar prompt.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .redact import redact

#: Teto do diff enviado ao revisor. Um diff gigante estoura contexto e
#: custo sem melhorar a revisao; truncamos avisando que truncamos.
MAX_DIFF_CHARS = 60_000


def git(args: list[str], cwd: str = ".", timeout: int = 120) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                              text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return (proc.stdout or "").rstrip() if proc.returncode == 0 else ""


def current_branch(cwd: str = ".") -> str:
    return git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)


def head_sha(cwd: str = ".") -> str:
    return git(["rev-parse", "HEAD"], cwd)


def rev_parse(ref: str, cwd: str = ".") -> str:
    return git(["rev-parse", ref], cwd)


def changed_files(base_sha: str, cwd: str = ".") -> list[str]:
    """Arquivos alterados desde a base (commitados + working tree)."""
    files: list[str] = []
    if base_sha:
        committed = git(["diff", "--name-only", f"{base_sha}..HEAD"], cwd)
        files.extend(line for line in committed.splitlines() if line)
    dirty = git(["status", "--porcelain"], cwd)
    for line in dirty.splitlines():
        name = line[3:].strip()
        if name and name not in files:
            files.append(name)
    return files


def diff(base_sha: str, cwd: str = ".", max_chars: int = MAX_DIFF_CHARS) -> str:
    """Diff acumulado da branch, truncado e redigido."""
    if not base_sha:
        return "(sem base_sha - diff indisponivel)"
    text = git(["diff", f"{base_sha}..HEAD"], cwd)
    dirty = git(["diff"], cwd)
    if dirty:
        text = f"{text}\n\n# --- alteracoes nao commitadas ---\n{dirty}"
    text = text.strip()
    if not text:
        return "(nenhuma alteracao)"
    if len(text) > max_chars:
        omitted = len(text) - max_chars
        text = text[:max_chars] + f"\n\n[... diff truncado: {omitted} caracteres omitidos ...]"
    return redact(text)


def commits(base_sha: str, cwd: str = ".") -> list[str]:
    if not base_sha:
        return []
    text = git(["log", "--oneline", f"{base_sha}..HEAD"], cwd)
    return [line for line in text.splitlines() if line]


def has_uncommitted_changes(cwd: str = ".") -> bool:
    return bool(git(["status", "--porcelain"], cwd))


def ensure_branch(name: str, base: str, cwd: str = ".") -> tuple[bool, str]:
    """Cria (ou entra em) a branch da tarefa. Devolve (ok, mensagem)."""
    if not name:
        return False, "nome de branch vazio"
    existing = current_branch(cwd)
    if existing == name:
        return True, f"ja' na branch {name}"
    proc = subprocess.run(["git", "checkout", "-B", name, base], cwd=cwd,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return False, redact((proc.stderr or proc.stdout).strip())
    return True, f"branch {name} criada a partir de {base}"


def branch_name(prefix: str, slug: str) -> str:
    return f"{prefix}{slug}"


def workspace_snapshot(cwd: str = ".") -> dict[str, str]:
    """Foto do repositorio, usada para provar que a `main` nao se moveu."""
    return {
        "branch": current_branch(cwd),
        "head": head_sha(cwd),
        "main": rev_parse("main", cwd),
    }


def file_head(path: str | Path, max_chars: int = 4000) -> str:
    p = Path(path)
    if not p.exists():
        return f"(arquivo ausente: {path})"
    text = p.read_text(encoding="utf-8", errors="replace")
    return redact(text[:max_chars])
