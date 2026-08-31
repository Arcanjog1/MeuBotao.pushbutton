"""Teste sintetico do orquestrador (secao 21 do pedido).

Requisito explicito: **nao** testar com mudanca real no wall modeling.
Aqui o alvo e' um arquivo de fixture descartavel e os agentes sao
roteirizados - o que roda e' o codigo de PRODUCAO (roteamento, gates,
estado, parada, redacao); so' a fronteira do subprocesso e' trocada.

Isso permite provar o loop inteiro no runner do GitHub Actions **sem
nenhuma API key**, o que tambem faz do `selftest` um smoke test barato
antes de gastar uma run de verdade.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from .agents.base import AgentInvocation
from .agents.executor import CommandOutput

#: Resposta do Claude no formato REAL do `--output-format json`
#: (campos conferidos contra uma execucao de verdade).
def claude_stdout(summary: str, status: str = "PARTIAL", cost: float = 0.02,
                  changed: list[str] | None = None,
                  commits: list[str] | None = None,
                  blockers: list[str] | None = None) -> str:
    return json.dumps({
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 3,
        "duration_ms": 1800,
        "total_cost_usd": cost,
        "session_id": "selftest-session",
        "usage": {"input_tokens": 10, "output_tokens": 120,
                  "output_tokens_details": {"thinking_tokens": 0}},
        "result": summary,
        "structured_output": {
            "summary": summary,
            "status": status,
            "root_cause": "fixture sintetica do selftest",
            "changed_files": changed or ["ai_team/fixtures/sandbox_target.txt"],
            "commits": commits or [],
            "tests_run": "python3 -m pytest tests/ -q -m 'not slow'",
            "remaining_work": [],
            "blockers": blockers or [],
            "confidence": "HIGH",
        },
    })


def codex_stdout(verdict: str, next_model: str = "claude-sonnet-5",
                 next_reasoning: str = "medium", next_prompt: str = "",
                 routing_reason: str = "fixture", why: str = "fixture") -> str:
    return json.dumps({
        "verdict": verdict,
        "next_agent": "claude",
        "next_model": next_model,
        "next_reasoning": next_reasoning,
        "next_prompt": next_prompt,
        "issues": [],
        "routing_reason": routing_reason,
        "why": why,
    })


@dataclass
class ScenarioStep:
    """Uma resposta roteirizada, escolhida pelo agente que invocou."""

    agent: str
    stdout: str
    exit_code: int = 0


@dataclass
class ScenarioExecutor:
    """Executor que responde por AGENTE, nao por posicao.

    Mais robusto que uma fila cega: se o loop parar antes (o que e'
    exatamente o que alguns cenarios testam), as respostas restantes
    simplesmente nao sao consumidas.
    """

    steps: list[ScenarioStep] = field(default_factory=list)
    calls: list[AgentInvocation] = field(default_factory=list)
    on_call: Callable[[AgentInvocation], None] | None = None

    def run(self, invocation: AgentInvocation) -> CommandOutput:
        self.calls.append(invocation)
        if self.on_call:
            self.on_call(invocation)
        for i, step in enumerate(self.steps):
            if step.agent == invocation.agent:
                self.steps.pop(i)
                return CommandOutput(step.exit_code, step.stdout, "", 5)
        return CommandOutput(1, "", f"selftest: sem resposta para {invocation.agent}", 0)

    def argv_for(self, agent: str) -> list[list[str]]:
        return [c.argv for c in self.calls if c.agent == agent]

    def configs_for(self, agent: str) -> list[tuple[str, str]]:
        """(modelo, effort) de cada invocacao - o que foi realmente aplicado."""
        return [(c.config.model, c.config.effort) for c in self.calls if c.agent == agent]


def argv_value(argv: list[str], flag: str) -> str | None:
    """Valor que segue `flag` no argv. Usado para provar o que foi aplicado."""
    try:
        return argv[argv.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def codex_effort_from_argv(argv: list[str]) -> str | None:
    """Extrai o effort de `-c model_reasoning_effort="X"`."""
    for item in argv:
        if item.startswith("model_reasoning_effort="):
            return item.split("=", 1)[1].strip('"')
    return None
