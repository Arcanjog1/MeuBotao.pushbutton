"""Leitura do repositorio para montar o contexto do revisor.

Tudo aqui e' read-only e passa por redacao antes de virar prompt.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .redact import redact

#: Nomes que nunca podem ser a branch da tarefa - checkout para eles
#: pisaria na referencia local que o resto do sistema trata como protegida.
PROTECTED_BRANCH_NAMES = ("main", "master", "head")

#: Um segmento de ref valido: comeca por alfanumerico, so' tem
#: alfanumerico/._- depois. Bloqueia por constucao um nome que comece
#: com '-' (que o git leria como flag de `checkout -B <isto>`).
SAFE_BRANCH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

#: Teto de tamanho generoso, so' para nao deixar passar algo absurdo.
MAX_BRANCH_LEN = 200

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


def sanitize_branch_name(name: str) -> tuple[bool, str]:
    """Valida um nome de branch vindo de fora (input da UI do workflow).

    Retorna (True, nome) se seguro, ou (False, motivo) caso contrario. E'
    uma WHITELIST, no mesmo espirito de `routing.SAFE_TOKEN_RE`: em vez de
    tentar listar tudo que e' perigoso, so' aceita o que sabidamente e'
    seguro.

    Sem isto, `--branch` (que vem do input `branch_name` da UI) chegaria
    cru em `git checkout -B <nome> <base>`. Como o argv e' uma lista (nao
    passa por shell), injecao de shell nao e' o risco - o risco real e' um
    nome comecando com `-` sendo lido pelo git como FLAG do comando
    (`git checkout -B --upload-pack=... main` seria isso), ou o nome ser
    literalmente `main`/`master`, o que desviaria o checkout para a
    branch protegida em vez de criar a branch da tarefa.
    """
    if not name:
        return False, "vazio"
    if len(name) > MAX_BRANCH_LEN:
        return False, f"maior que {MAX_BRANCH_LEN} caracteres"
    if name.lower() in PROTECTED_BRANCH_NAMES or name.lower().startswith("refs/"):
        return False, f"nome protegido ou reservado: {name!r}"
    if ".." in name or name.endswith(".lock") or "@{" in name or "\\" in name:
        return False, "contem sequencia proibida em nome de ref do git"
    if name.startswith("/") or name.endswith("/") or "//" in name:
        return False, "barra invalida (inicio/fim/dupla)"
    segments = name.split("/")
    for segment in segments:
        if not SAFE_BRANCH_SEGMENT_RE.match(segment):
            return False, f"segmento invalido: {segment!r}"
    return True, name


def ensure_branch(name: str, base: str, cwd: str = ".") -> tuple[bool, str]:
    """Cria (ou entra em) a branch da tarefa. Devolve (ok, mensagem)."""
    if not name:
        return False, "nome de branch vazio"
    # Segunda camada, independente de quem chamou: mesmo um `name` que
    # tenha escapado da sanitizacao no chamador nao consegue fazer o git
    # tocar numa branch protegida por aqui.
    if name.lower() in PROTECTED_BRANCH_NAMES:
        return False, f"recusando criar/entrar na branch protegida {name!r}"
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
