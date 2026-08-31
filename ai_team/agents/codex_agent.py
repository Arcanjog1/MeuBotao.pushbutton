"""Adaptador do OpenAI Codex CLI (reviewer/router, READ-ONLY).

Interface real verificada em v0.151.0 (ver `.ai-team/ARCHITECTURE.md` 1.2):

    codex exec "<prompt>"
        -m <modelo>
        -c model_reasoning_effort="<nivel>"   # RACIOCINIO de verdade
        -s read-only                          # sandbox: Codex NAO escreve
        --output-schema <arquivo.json>
        --json
        --skip-git-repo-check

CUIDADO (armadilha real): o Codex CLI NAO valida `model_reasoning_effort`
do lado do cliente - `-c model_reasoning_effort="bogusvalue"` e' aceito e
so' falha na API. A whitelist de `routing.py` e' a unica barreira, e por
isso `build_argv` exige um `AgentConfig` ja' validado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import Config
from ..routing import AgentConfig
from .base import AgentInvocation, AgentResult
from .executor import CommandOutput

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "codex_decision.schema.json"


def build_argv(cfg: Config, agent_cfg: AgentConfig,
               schema_path: Path | str | None = None,
               output_file: Path | str | None = None) -> list[str]:
    """Monta o argv exato do `codex exec`. Funcao PURA.

    O prompt vai por STDIN (nao como argumento) para nao estourar limite de
    tamanho de argumento: o contexto de revisao carrega o `git diff`.
    """
    schema = Path(schema_path) if schema_path else SCHEMA_PATH
    sandbox = str(cfg.codex.extra.get("sandbox", "read-only"))

    argv = [
        cfg.codex.bin, "exec",
        "-m", agent_cfg.model,
        "-c", f'model_reasoning_effort="{agent_cfg.effort}"',
        "-s", sandbox,
        "--output-schema", str(schema),
        "--skip-git-repo-check",
        "--color", "never",
    ]
    if output_file:
        argv += ["-o", str(output_file)]
    # `-` = ler as instrucoes do stdin.
    argv.append("-")
    return argv


def _first_json_object(text: str) -> dict[str, Any] | None:
    """Extrai o ultimo objeto JSON de nivel superior do texto.

    O `codex exec` escreve a mensagem final no stdout junto de logs; quando
    `-o` esta' disponivel usamos o arquivo, mas isto e' o plano B.
    """
    depth = 0
    start = -1
    candidates: list[str] = []
    in_string = False
    escaped = False
    for i, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    candidates.append(text[start:i + 1])
    for chunk in reversed(candidates):
        try:
            parsed = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "verdict" in parsed:
            return parsed
    return None


def parse_output(out: CommandOutput, agent_cfg: AgentConfig,
                 output_file: Path | str | None = None) -> AgentResult:
    """Le a decisao do Codex, preferindo o arquivo de `--output-last-message`."""
    result = AgentResult(agent="codex", ok=False, config=agent_cfg,
                         exit_code=out.exit_code, duration_ms=out.duration_ms)

    if out.timed_out:
        result.error = f"codex: timeout ({out.stderr})"
        return result

    payload: dict[str, Any] | None = None

    if output_file:
        path = Path(output_file)
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if content:
                try:
                    candidate = json.loads(content)
                    if isinstance(candidate, dict):
                        payload = candidate
                except json.JSONDecodeError:
                    payload = _first_json_object(content)

    if payload is None:
        payload = _first_json_object(out.stdout)

    if payload is None:
        result.error = (f"codex: nenhuma decisao JSON na saida (exit={out.exit_code}); "
                        f"stderr={out.stderr[:400]}")
        result.text = out.stdout[-2000:]
        return result

    result.raw = payload
    result.structured = payload
    result.text = json.dumps(payload, ensure_ascii=False)

    if out.exit_code != 0:
        # Decisao legivel mesmo com exit != 0 ainda vale; registramos o aviso.
        result.error = f"codex: exit={out.exit_code} (decisao lida mesmo assim)"

    result.ok = True
    return result


class CodexAgent:
    """Invoca o Codex em modo read-only e devolve a decisao normalizada."""

    name = "codex"

    def __init__(self, cfg: Config, executor: Any, cwd: str = ".",
                 output_dir: Path | str | None = None) -> None:
        self.cfg = cfg
        self.executor = executor
        self.cwd = cwd
        self.output_dir = Path(output_dir) if output_dir else None

    def invoke(self, prompt: str, agent_cfg: AgentConfig, round_no: int = 0,
               timeout_seconds: int = 1800) -> tuple[AgentResult, AgentInvocation]:
        output_file = None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_file = self.output_dir / f"codex_last_message_{round_no:03d}.json"

        invocation = AgentInvocation(
            agent=self.name,
            argv=build_argv(self.cfg, agent_cfg, output_file=output_file),
            config=agent_cfg,
            prompt=prompt,
            cwd=self.cwd,
            timeout_seconds=timeout_seconds,
            stdin=prompt,
        )
        out = self.executor.run(invocation)
        return parse_output(out, agent_cfg, output_file), invocation
