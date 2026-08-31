"""Roteamento: transforma a decisao do Codex numa configuracao SEGURA.

Este e' o ponto onde uma string vinda de um modelo poderia virar um
argumento de linha de comando. Nada passa direto:

1. formato seguro (`^[A-Za-z0-9._-]+$`) - barra injecao de argumento;
2. pertencer a whitelist da config;
3. se falhar, CLAMPA para o default e registra `routing_override` com o
   valor recusado - o loop degrada, nunca aborta por rota invalida.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import SAFE_TOKEN_RE, AgentPolicy, Config

VERDICTS = ("CONTINUE", "APPROVED", "NEEDS_HUMAN", "NEEDS_REVIT", "FAILED")


@dataclass(frozen=True)
class AgentConfig:
    """O que efetivamente vira argv."""

    model: str
    effort: str


@dataclass
class RoutingResult:
    config: AgentConfig
    overrides: list[str] = field(default_factory=list)

    @property
    def clamped(self) -> bool:
        return bool(self.overrides)


def _pick(value: Any, allowed: tuple[str, ...], default: str, label: str,
          overrides: list[str]) -> str:
    """Aceita `value` se for seguro e permitido; senao clampa para `default`."""
    if value is None or value == "":
        return default
    if not isinstance(value, str):
        overrides.append(f"{label}: tipo invalido ({type(value).__name__}) -> {default}")
        return default
    if not SAFE_TOKEN_RE.match(value):
        # Nao ecoa o valor inteiro num argv; so' um trecho, ja' truncado.
        overrides.append(f"{label}: formato inseguro {value[:40]!r} -> {default}")
        return default
    if value not in allowed:
        overrides.append(f"{label}: {value!r} fora da whitelist -> {default}")
        return default
    return value


def route_agent(policy: AgentPolicy, model: Any = None, effort: Any = None) -> RoutingResult:
    """Valida um par (modelo, effort) contra a politica do agente."""
    overrides: list[str] = []
    return RoutingResult(
        config=AgentConfig(
            model=_pick(model, policy.allowed_models, policy.default_model, "model", overrides),
            effort=_pick(effort, policy.allowed_efforts, policy.default_effort, "effort", overrides),
        ),
        overrides=overrides,
    )


def route_from_class(cfg: Config, work_class: str) -> AgentConfig:
    """Resolve uma classe da `routing_policy` (mechanical/standard/deep/critical)."""
    entry = cfg.routing_policy.get(work_class)
    if not isinstance(entry, dict):
        return AgentConfig(cfg.claude.default_model, cfg.claude.default_effort)
    return route_agent(cfg.claude, entry.get("model"), entry.get("effort")).config


def normalize_verdict(value: Any, overrides: list[str]) -> str:
    """Verdict desconhecido vira NEEDS_HUMAN - o seguro e' parar, nao seguir."""
    if isinstance(value, str) and value.upper() in VERDICTS:
        return value.upper()
    overrides.append(f"verdict: {value!r} invalido -> NEEDS_HUMAN")
    return "NEEDS_HUMAN"


@dataclass
class CodexDecision:
    """Decisao do Codex, ja' normalizada e segura para uso."""

    verdict: str
    next_prompt: str
    next_claude: AgentConfig
    routing_reason: str
    why: str
    issues: list[dict[str, Any]] = field(default_factory=list)
    overrides: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "next_model": self.next_claude.model,
            "next_reasoning": self.next_claude.effort,
            "next_prompt": self.next_prompt,
            "routing_reason": self.routing_reason,
            "why": self.why,
            "issues": self.issues,
            "routing_overrides": self.overrides,
        }


def parse_codex_decision(payload: Any, cfg: Config) -> CodexDecision:
    """Normaliza a saida do Codex. Nunca levanta: entrada ruim vira NEEDS_HUMAN."""
    overrides: list[str] = []
    if not isinstance(payload, dict):
        overrides.append(f"decisao nao e' um objeto JSON ({type(payload).__name__})")
        payload = {}

    verdict = normalize_verdict(payload.get("verdict"), overrides)
    routed = route_agent(cfg.claude, payload.get("next_model"), payload.get("next_reasoning"))
    overrides.extend(routed.overrides)

    next_prompt = payload.get("next_prompt")
    if not isinstance(next_prompt, str):
        next_prompt = ""
    # CONTINUE sem instrucao para a proxima rodada e' inutil: vira NEEDS_HUMAN
    # em vez de mandar o Claude rodar sem saber o que fazer.
    if verdict == "CONTINUE" and not next_prompt.strip():
        overrides.append("verdict CONTINUE sem next_prompt -> NEEDS_HUMAN")
        verdict = "NEEDS_HUMAN"

    issues = payload.get("issues")
    if not isinstance(issues, list):
        issues = []

    return CodexDecision(
        verdict=verdict,
        next_prompt=next_prompt,
        next_claude=routed.config,
        routing_reason=str(payload.get("routing_reason") or ""),
        why=str(payload.get("why") or ""),
        issues=[i for i in issues if isinstance(i, dict)],
        overrides=overrides,
        raw=payload,
    )
