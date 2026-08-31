"""Renderizacao dos prompts.

Os templates vivem em `ai_team/prompts/*.md` e usam `str.format`. Tudo
que vem do repositorio (diff, arquivos, commits) passa por redacao antes
de entrar no texto - o prompt do revisor e' gravado no disco e vai para
os artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import repo
from .agents.base import AgentResult
from .config import Config
from .gates import GateResult
from .redact import redact
from .routing import CodexDecision
from .state import RunState

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _template(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _history(state: RunState, limit: int = 6) -> str:
    if not state.rounds:
        return "(esta e' a primeira rodada)"
    lines = []
    for record in state.rounds[-limit:]:
        claude = record.get("claude", {})
        codex = record.get("codex", {})
        gate = record.get("gate", {})
        lines.append(
            f"- rodada {record.get('round')}: "
            f"claude[{claude.get('model')}/{claude.get('reasoning')}] "
            f"status={claude.get('status')} | gate={gate.get('status')} | "
            f"codex={codex.get('verdict')} -> "
            f"{codex.get('next_model')}/{codex.get('next_reasoning')}"
        )
    return "\n".join(lines)


def _routing_policy_text(cfg: Config) -> str:
    lines = []
    for name, entry in cfg.routing_policy.items():
        if not isinstance(entry, dict):
            continue
        lines.append(f"- `{name}`: {entry.get('description', '')}\n"
                     f"  -> next_model=`{entry.get('model')}`, "
                     f"next_reasoning=`{entry.get('effort')}`")
    return "\n".join(lines) or "(politica vazia)"


def render_claude_initial(cfg: Config, state: RunState, round_no: int,
                          base_branch: str = "main") -> str:
    return _template("claude_initial.md").format(
        task=state.task,
        mode=state.mode,
        round=round_no,
        max_rounds=state.max_rounds,
        branch=state.branch or "(nao definida)",
        base_branch=base_branch,
        base_sha=state.base_sha[:12] or "(desconhecida)",
    )


def render_claude_continue(cfg: Config, state: RunState, round_no: int,
                           decision: CodexDecision, gate: GateResult,
                           base_branch: str = "main") -> str:
    return _template("claude_continue.md").format(
        task=state.task,
        next_prompt=decision.next_prompt,
        routing_reason=decision.routing_reason or "(o revisor nao justificou)",
        gate_summary=gate.summary(),
        round=round_no,
        max_rounds=state.max_rounds,
        branch=state.branch or "(nao definida)",
        base_branch=base_branch,
        base_sha=state.base_sha[:12] or "(desconhecida)",
        history=_history(state),
    )


def _gate_report(gate: GateResult) -> str:
    lines = [f"status: {gate.status} (passed={gate.passed})"]
    for check in gate.checks:
        marker = {"PASS": "OK", "FAIL": "REPROVADO", "SKIPPED": "nao medido"}.get(
            check.status, check.status)
        hard = "HARD" if check.hard else "soft"
        lines.append(f"- [{hard}] {check.name}: {marker}")
        if check.detail:
            lines.append(f"    {redact(check.detail)[:900]}")
    return "\n".join(lines)


def render_codex_review(cfg: Config, state: RunState, round_no: int,
                        claude_result: AgentResult, gate: GateResult,
                        cwd: str = ".") -> str:
    files = repo.changed_files(state.base_sha, cwd)
    return _template("codex_review.md").format(
        task=state.task,
        mode=state.mode,
        round=round_no,
        max_rounds=state.max_rounds,
        claude_result=json.dumps(claude_result.structured, indent=2, ensure_ascii=False),
        gate_report=_gate_report(gate),
        changed_files="\n".join(f"- {f}" for f in files) or "(nenhum arquivo alterado)",
        git_diff=repo.diff(state.base_sha, cwd),
        commits="\n".join(f"- {c}" for c in repo.commits(state.base_sha, cwd))
                or "(nenhum commit nesta branch)",
        history=_history(state),
        routing_policy=_routing_policy_text(cfg),
        allowed_models=", ".join(f"`{m}`" for m in cfg.claude.allowed_models),
        allowed_efforts=", ".join(f"`{e}`" for e in cfg.claude.allowed_efforts),
    )
