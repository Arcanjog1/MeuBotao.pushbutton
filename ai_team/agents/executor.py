"""Fronteira de execucao.

Um unico ponto onde o orquestrador toca o sistema operacional. Trocar o
executor por `ScriptedExecutor` permite exercitar TODO o codigo de
producao (roteamento, gates, estado, parada, redacao) offline e sem
nenhuma API key - que e' exatamente o teste sintetico pedido na secao 21.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, Protocol

from .base import AgentInvocation


@dataclass
class CommandOutput:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False


class Executor(Protocol):
    def run(self, invocation: AgentInvocation) -> CommandOutput: ...


class SubprocessExecutor:
    """Executa o CLI de verdade."""

    def run(self, invocation: AgentInvocation) -> CommandOutput:
        env = dict(os.environ)
        env.update(invocation.env)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                invocation.argv,
                cwd=invocation.cwd,
                env=env,
                input=invocation.stdin,
                capture_output=True,
                text=True,
                timeout=invocation.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandOutput(
                exit_code=124,
                stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
                stderr=f"timeout apos {invocation.timeout_seconds}s",
                duration_ms=int((time.monotonic() - started) * 1000),
                timed_out=True,
            )
        except FileNotFoundError:
            return CommandOutput(
                exit_code=127,
                stdout="",
                stderr=f"executavel nao encontrado: {invocation.argv[0]!r}",
                duration_ms=int((time.monotonic() - started) * 1000),
            )
        return CommandOutput(
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            duration_ms=int((time.monotonic() - started) * 1000),
        )


@dataclass
class ScriptedExecutor:
    """Executor de fixture: devolve respostas roteirizadas, em ordem.

    Guarda cada `AgentInvocation` recebida em `self.calls`, o que permite
    aos testes afirmarem sobre o argv EXATO que teria sido executado.
    """

    #: Uma resposta por invocacao. Item pode ser um `CommandOutput` ou um
    #: callable que recebe a invocacao e devolve um `CommandOutput`.
    responses: list[object] = field(default_factory=list)
    calls: list[AgentInvocation] = field(default_factory=list)

    def run(self, invocation: AgentInvocation) -> CommandOutput:
        self.calls.append(invocation)
        if not self.responses:
            return CommandOutput(1, "", "ScriptedExecutor: sem resposta roteirizada", 0)
        item = self.responses.pop(0)
        if isinstance(item, CommandOutput):
            return item
        if callable(item):
            return item(invocation)
        raise TypeError(f"resposta roteirizada invalida: {type(item).__name__}")

    def argv_for(self, agent: str) -> list[list[str]]:
        """Todos os argv de um agente, na ordem em que foram invocados."""
        return [c.argv for c in self.calls if c.agent == agent]


def json_response(payload: str, exit_code: int = 0, duration_ms: int = 5) -> CommandOutput:
    return CommandOutput(exit_code=exit_code, stdout=payload, stderr="", duration_ms=duration_ms)


ResponseFactory = Callable[[AgentInvocation], CommandOutput]
