"""Tipos comuns aos dois agentes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..redact import redact_obj
from ..routing import AgentConfig


@dataclass(frozen=True)
class AgentInvocation:
    """Uma invocacao concreta: o argv exato mais o contexto para o log.

    `argv` e' produzido por uma funcao PURA (`build_argv`). E' isso que
    torna verificavel, sem chamar API nenhuma, que o modelo e o nivel de
    raciocinio escolhidos pelo roteador foram mesmo aplicados.
    """

    agent: str
    argv: list[str]
    config: AgentConfig
    prompt: str
    cwd: str = "."
    timeout_seconds: int = 3600
    env: dict[str, str] = field(default_factory=dict)
    stdin: str | None = None

    def describe(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "model": self.config.model,
            "reasoning": self.config.effort,
            "argv": list(self.argv),
        }


@dataclass
class AgentResult:
    """Resultado normalizado de uma invocacao."""

    agent: str
    ok: bool
    config: AgentConfig
    structured: dict[str, Any] = field(default_factory=dict)
    text: str = ""
    error: str = ""
    duration_ms: int = 0
    cost_usd: float = 0.0
    usage: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_raw: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "agent": self.agent,
            "ok": self.ok,
            "model": self.config.model,
            "reasoning": self.config.effort,
            "structured": self.structured,
            "text": self.text,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "cost_usd": self.cost_usd,
            "usage": self.usage,
            "exit_code": self.exit_code,
        }
        if include_raw:
            payload["raw"] = self.raw
        return redact_obj(payload)
