"""Estado persistente de uma run.

Layout (secao 15 do pedido):

    .ai-team/runs/<run-id>/
        task.json
        state.json
        claude_round_001.json
        gate_round_001.json
        codex_round_001.json
        ...
        final_result.json

Nada disso e' versionado: `.gitignore` cobre `.ai-team/runs/`. O workflow
sobe o diretorio inteiro como artifact do GitHub Actions, e so' um resumo
enxuto vai para o step summary.

Todo objeto passa por `redact_obj()` antes de tocar o disco.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .redact import redact_obj

RUNS_DIR = Path(".ai-team/runs")


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str, max_len: int = 48) -> str:
    """Slug seguro para nome de branch e de diretorio."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:max_len].rstrip("-")) or "task"


def new_run_id(task: str, now: float | None = None) -> str:
    stamp = datetime.fromtimestamp(now or time.time(), timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{slugify(task, 32)}"


@dataclass
class RunState:
    """Estado de uma run, gravado incrementalmente a cada passo.

    Gravar a cada passo (e nao so' no fim) e' o que faz `NEEDS_REVIT` e
    `TIMEOUT` nao perderem a tarefa: o diretorio ja' esta' no disco quando
    o loop para.
    """

    run_id: str
    task: str
    mode: str
    max_rounds: int
    root: Path
    branch: str = ""
    base_sha: str = ""
    started_at: str = field(default_factory=utcnow)
    finished_at: str = ""
    status: str = "RUNNING"
    rounds: list[dict[str, Any]] = field(default_factory=list)
    claude_calls: int = 0
    codex_calls: int = 0
    total_cost_usd: float = 0.0
    notes: list[str] = field(default_factory=list)

    # ---------- disco ----------

    @property
    def dir(self) -> Path:
        return self.root / self.run_id

    def ensure_dir(self) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        return self.dir

    def write_json(self, name: str, payload: Any) -> Path:
        """Grava `payload` redigido em `<run>/<name>`."""
        self.ensure_dir()
        path = self.dir / name
        path.write_text(
            json.dumps(redact_obj(payload), indent=2, ensure_ascii=False, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def save(self) -> Path:
        return self.write_json("state.json", self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task": self.task,
            "mode": self.mode,
            "max_rounds": self.max_rounds,
            "branch": self.branch,
            "base_sha": self.base_sha,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "claude_calls": self.claude_calls,
            "codex_calls": self.codex_calls,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "rounds": self.rounds,
            "notes": self.notes,
        }

    # ---------- registro ----------

    def note(self, message: str) -> None:
        """Anota um fato do orquestrador (clamp de rota, limite batido, ...)."""
        self.notes.append(f"{utcnow()} {message}")

    def record_round(self, record: dict[str, Any]) -> None:
        self.rounds.append(record)
        self.save()


def create_run(task: str, mode: str, max_rounds: int, root: Path | str = RUNS_DIR,
               run_id: str | None = None) -> RunState:
    state = RunState(
        run_id=run_id or new_run_id(task),
        task=task,
        mode=mode,
        max_rounds=max_rounds,
        root=Path(root),
    )
    state.ensure_dir()
    state.write_json("task.json", {
        "task": task,
        "mode": mode,
        "max_rounds": max_rounds,
        "created_at": state.started_at,
        "run_id": state.run_id,
    })
    state.save()
    return state
