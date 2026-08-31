"""Adaptador do Claude Code CLI (executor, unico agente ESCRITOR).

Interface real verificada em v2.1.252 (ver `.ai-team/ARCHITECTURE.md` 1.1):

    claude -p "<prompt>"
        --model <modelo>            # modelo de verdade
        --effort <nivel>            # RACIOCINIO de verdade (nao e' texto no prompt)
        --output-format json
        --json-schema <schema>      # devolve `structured_output` ja' validado
        --permission-mode acceptEdits
        --disallowedTools ...
        --settings <hook de guarda>
        --max-budget-usd <teto>

Prova de que `--effort` e' real (mesmo prompt, mesmo modelo):
    low  -> thinking_tokens = 0
    high -> thinking_tokens = 371
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import Config
from ..routing import AgentConfig
from .base import AgentInvocation, AgentResult
from .executor import CommandOutput

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "claude_result.schema.json"
SETTINGS_PATH = Path(__file__).resolve().parent.parent / "guard" / "claude_settings.json"


def build_argv(cfg: Config, agent_cfg: AgentConfig, prompt: str,
               settings_path: Path | str | None = None,
               schema_path: Path | str | None = None,
               max_budget_usd: float | None = None) -> list[str]:
    """Monta o argv exato. Funcao PURA - e' o que os testes verificam.

    `agent_cfg` ja' vem validado por `routing.py`; nenhuma string crua de
    modelo chega aqui.
    """
    schema = Path(schema_path) if schema_path else SCHEMA_PATH
    settings = Path(settings_path) if settings_path else SETTINGS_PATH

    argv = [
        cfg.claude.bin,
        "-p", prompt,
        "--model", agent_cfg.model,
        "--effort", agent_cfg.effort,
        "--output-format", "json",
        "--json-schema", schema.read_text(encoding="utf-8"),
        "--permission-mode", str(cfg.claude.extra.get("permission_mode", "acceptEdits")),
    ]

    disallowed = cfg.claude.extra.get("disallowed_tools") or []
    if disallowed:
        argv += ["--disallowedTools", *[str(t) for t in disallowed]]

    # O hook PreToolUse e' o bloqueio REAL de git perigoso (secao 13 do
    # pedido); `--disallowedTools` acima e' so' a redundancia.
    if settings.exists():
        argv += ["--settings", str(settings)]

    budget = max_budget_usd
    if budget is None:
        budget = cfg.limits.get("max_budget_usd_per_claude_call")
    if budget:
        argv += ["--max-budget-usd", str(budget)]

    return argv


def parse_output(out: CommandOutput, agent_cfg: AgentConfig) -> AgentResult:
    """Le o JSON de `--output-format json`.

    Campos conferidos contra uma execucao real (ARCHITECTURE.md 1.1):
    `structured_output`, `result`, `is_error`, `subtype`, `total_cost_usd`,
    `usage`, `duration_ms`.
    """
    result = AgentResult(agent="claude", ok=False, config=agent_cfg,
                         exit_code=out.exit_code, duration_ms=out.duration_ms)

    if out.timed_out:
        result.error = f"claude: timeout ({out.stderr})"
        return result

    payload: Any = None
    text = out.stdout.strip()
    if text:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            # Alguns ambientes prefixam ruido; tenta a ultima linha que seja JSON.
            for line in reversed(text.splitlines()):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        payload = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue

    if not isinstance(payload, dict):
        result.error = (f"claude: saida nao e' JSON (exit={out.exit_code}); "
                        f"stderr={out.stderr[:400]}")
        return result

    result.raw = payload
    result.text = str(payload.get("result") or "")
    result.cost_usd = float(payload.get("total_cost_usd") or 0.0)
    result.usage = payload.get("usage") or {}

    duration = payload.get("duration_ms")
    if isinstance(duration, (int, float)):
        result.duration_ms = int(duration)

    structured = payload.get("structured_output")
    if isinstance(structured, dict):
        result.structured = structured

    is_error = bool(payload.get("is_error"))
    if is_error or out.exit_code != 0:
        result.error = (f"claude: is_error={is_error} exit={out.exit_code} "
                        f"subtype={payload.get('subtype')!r} "
                        f"api_error={payload.get('api_error_status')!r}")
        return result

    if not result.structured:
        result.error = "claude: resposta sem `structured_output` (schema nao satisfeito)"
        return result

    result.ok = True
    return result


class ClaudeAgent:
    """Invoca o Claude e devolve um `AgentResult` normalizado."""

    name = "claude"

    def __init__(self, cfg: Config, executor: Any, cwd: str = ".") -> None:
        self.cfg = cfg
        self.executor = executor
        self.cwd = cwd

    def invoke(self, prompt: str, agent_cfg: AgentConfig,
               timeout_seconds: int = 3600) -> tuple[AgentResult, AgentInvocation]:
        invocation = AgentInvocation(
            agent=self.name,
            argv=build_argv(self.cfg, agent_cfg, prompt),
            config=agent_cfg,
            prompt=prompt,
            cwd=self.cwd,
            timeout_seconds=timeout_seconds,
        )
        out = self.executor.run(invocation)
        return parse_output(out, agent_cfg), invocation
