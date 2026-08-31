"""Agentes do AI Team: Claude (executor) e Codex (reviewer/router)."""

from .base import AgentInvocation, AgentResult
from .claude_agent import ClaudeAgent
from .codex_agent import CodexAgent
from .executor import CommandOutput, ScriptedExecutor, SubprocessExecutor

__all__ = [
    "AgentInvocation", "AgentResult", "ClaudeAgent", "CodexAgent",
    "CommandOutput", "ScriptedExecutor", "SubprocessExecutor",
]
