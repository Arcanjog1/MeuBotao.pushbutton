"""Carga e validacao da politica (`config.yaml`).

Sem dependencia de PyYAML: o parser abaixo cobre o subconjunto de YAML que
esta' config usa (mapas aninhados por indentacao, listas, escalares, listas
inline `[a, b]`). Motivo: o runner do GitHub Actions nao deve precisar de
`pip install` so' para ler a propria politica, e o formato do arquivo esta'
sob nosso controle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"

#: Modelo/effort so' entram num argv se casarem com isto. Barra qualquer
#: tentativa de injecao de argumento vinda de uma resposta de modelo.
SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class ConfigError(ValueError):
    """Politica invalida - erro de programacao/configuracao, nao de agente."""


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ""
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in inner.split(",")]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    low = text.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", "none"):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _parse_yaml(text: str) -> dict[str, Any]:
    """Le o subconjunto de YAML usado por `config.yaml`.

    Um bloco aberto (`chave:` sem valor) comeca como dict e vira list assim
    que a primeira linha filha chega com `- `.
    """
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, Any, str | None]] = [(-1, root, None, None)]

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        _, container, parent, key_in_parent = stack[-1]

        if line.startswith("- "):
            value = _parse_scalar(line[2:])
            if isinstance(container, dict) and not container and parent is not None:
                # O bloco aberto era uma lista, nao um dict: converte.
                container = []
                parent[key_in_parent] = container
                stack[-1] = (stack[-1][0], container, parent, key_in_parent)
            if not isinstance(container, list):
                raise ConfigError(f"item de lista fora de lista na linha {lineno}")
            container.append(value)
            continue

        if ":" not in line:
            raise ConfigError(f"linha sem ':' na linha {lineno}: {raw_line!r}")
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if " #" in rest:
            rest = rest.split(" #", 1)[0].strip()

        if not isinstance(container, dict):
            raise ConfigError(f"chave dentro de lista na linha {lineno}: {raw_line!r}")

        if rest == "":
            child: dict[str, Any] = {}
            container[key] = child
            stack.append((indent, child, container, key))
        else:
            container[key] = _parse_scalar(rest)

    return root


@dataclass(frozen=True)
class AgentPolicy:
    """Politica de um agente (Claude ou Codex)."""

    bin: str
    allowed_models: tuple[str, ...]
    allowed_efforts: tuple[str, ...]
    default_model: str
    default_effort: str
    extra: dict[str, Any] = field(default_factory=dict)

    def validate(self, name: str) -> None:
        if not self.allowed_models:
            raise ConfigError(f"{name}.allowed_models vazio")
        if not self.allowed_efforts:
            raise ConfigError(f"{name}.allowed_efforts vazio")
        if self.default_model not in self.allowed_models:
            raise ConfigError(f"{name}.default_model fora da whitelist")
        if self.default_effort not in self.allowed_efforts:
            raise ConfigError(f"{name}.default_effort fora da whitelist")
        for token in (*self.allowed_models, *self.allowed_efforts):
            if not SAFE_TOKEN_RE.match(token):
                raise ConfigError(f"{name}: token inseguro na whitelist: {token!r}")


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any]
    claude: AgentPolicy
    codex: AgentPolicy

    # ---- limites ----
    @property
    def limits(self) -> dict[str, Any]:
        return self.raw.get("limits", {})

    @property
    def max_rounds_ceiling(self) -> int:
        return int(self.limits.get("max_rounds_ceiling", 8))

    @property
    def default_max_rounds(self) -> int:
        return int(self.limits.get("max_rounds", 3))

    @property
    def timeout_minutes(self) -> int:
        return int(self.limits.get("timeout_minutes", 90))

    @property
    def max_claude_calls(self) -> int:
        return int(self.limits.get("max_claude_calls", 8))

    @property
    def max_codex_calls(self) -> int:
        return int(self.limits.get("max_codex_calls", 8))

    @property
    def routing_policy(self) -> dict[str, Any]:
        return self.raw.get("routing_policy", {})

    @property
    def gates(self) -> dict[str, Any]:
        return self.raw.get("gates", {})

    @property
    def git(self) -> dict[str, Any]:
        return self.raw.get("git", {})


def _agent_policy(raw: dict[str, Any], key: str) -> AgentPolicy:
    section = raw.get(key)
    if not isinstance(section, dict):
        raise ConfigError(f"secao '{key}' ausente em config.yaml")
    extra = {k: v for k, v in section.items()
             if k not in ("bin", "allowed_models", "allowed_efforts",
                          "default_model", "default_effort")}
    policy = AgentPolicy(
        bin=str(section.get("bin", key)),
        allowed_models=tuple(section.get("allowed_models") or ()),
        allowed_efforts=tuple(section.get("allowed_efforts") or ()),
        default_model=str(section.get("default_model", "")),
        default_effort=str(section.get("default_effort", "")),
        extra=extra,
    )
    policy.validate(key)
    return policy


def load_config(path: Path | str | None = None) -> Config:
    """Le e valida a politica. Levanta `ConfigError` se estiver incoerente."""
    cfg_path = Path(path) if path else CONFIG_PATH
    raw = _parse_yaml(cfg_path.read_text(encoding="utf-8"))

    cfg = Config(raw=raw, claude=_agent_policy(raw, "claude"), codex=_agent_policy(raw, "codex"))

    if cfg.default_max_rounds > cfg.max_rounds_ceiling:
        raise ConfigError("limits.max_rounds acima de limits.max_rounds_ceiling")
    if cfg.git.get("allow_merge_to_main"):
        raise ConfigError(
            "git.allow_merge_to_main=true e' proibido na V1 "
            "(o teto do sistema e' READY_FOR_HUMAN_REVIEW)"
        )
    for cls_name, cls in cfg.routing_policy.items():
        if cls.get("model") not in cfg.claude.allowed_models:
            raise ConfigError(f"routing_policy.{cls_name}.model fora da whitelist do Claude")
        if cls.get("effort") not in cfg.claude.allowed_efforts:
            raise ConfigError(f"routing_policy.{cls_name}.effort fora da whitelist do Claude")
    return cfg
