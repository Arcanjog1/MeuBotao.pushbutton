"""O loop autonomo Claude -> gate -> Codex -> Claude.

Uma rodada e' sempre, nesta ordem:

    1. CLAUDE       executa (unico escritor)
    2. GATE         julga tecnicamente (pytest, metricas, invariantes)
    3. CODEX        revisa e roteia (read-only), JA' vendo o gate
    4. RESOLVE      combina os tres, com o gate tendo VETO

O passo 4 e' o que impede a secao 7 do pedido de virar letra morta: um
gate HARD vermelho nunca termina como READY_FOR_HUMAN_REVIEW, mesmo com
Claude OK e Codex APPROVED.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import repo
from .agents import ClaudeAgent, CodexAgent
from .agents.base import AgentResult
from .config import Config
from .gates import GateResult, run_gates
from .redact import redact_obj
from .prompts_render import render_claude_continue, render_claude_initial, render_codex_review
from .routing import AgentConfig, CodexDecision, parse_codex_decision, route_from_class
from .state import RunState

#: Estados terminais do sistema (secao 9 do pedido).
TERMINAL_STATUSES = (
    "READY_FOR_HUMAN_REVIEW", "NEEDS_HUMAN", "NEEDS_REVIT",
    "FAILED", "MAX_ROUNDS", "TIMEOUT", "ERROR",
)


@dataclass
class LoopOutcome:
    status: str
    summary: str = ""
    do_not_merge: bool = False
    human_question: str = ""
    revit_capture_request: list[str] = field(default_factory=list)
    last_gate: GateResult | None = None
    rounds_used: int = 0


@dataclass
class Orchestrator:
    """Dono do estado, das chamadas, dos limites e da parada."""

    cfg: Config
    state: RunState
    claude: ClaudeAgent
    codex: CodexAgent
    cwd: str = "."
    base_branch: str = "main"
    base_sha_snapshot: str = ""
    deadline: float | None = None

    # ---------------- limites ----------------

    def _budget_stop(self) -> str:
        """Devolve o motivo de parada por limite, ou "" se ainda pode rodar."""
        if self.deadline and time.monotonic() > self.deadline:
            return "TIMEOUT"
        if self.state.claude_calls >= self.cfg.max_claude_calls:
            return "MAX_CLAUDE_CALLS"
        if self.state.codex_calls >= self.cfg.max_codex_calls:
            return "MAX_CODEX_CALLS"
        return ""

    # ---------------- passos ----------------

    def _run_claude(self, prompt: str, agent_cfg: AgentConfig, round_no: int) -> AgentResult:
        result, invocation = self.claude.invoke(prompt, agent_cfg)
        self.state.claude_calls += 1
        self.state.total_cost_usd += result.cost_usd
        payload = result.to_dict()
        payload["invocation"] = invocation.describe()
        payload["prompt"] = prompt
        self.state.write_json(f"claude_round_{round_no:03d}.json", payload)
        return result

    def _run_gate(self, round_no: int) -> GateResult:
        gate = run_gates(
            self.cfg, cwd=self.cwd,
            expected_branch=self.state.branch,
            base_sha_before=self.base_sha_snapshot,
            base_branch=self.base_branch,
        )
        self.state.write_json(f"gate_round_{round_no:03d}.json", gate.to_dict())
        return gate

    def _run_codex(self, claude_result: AgentResult, gate: GateResult,
                   round_no: int) -> tuple[CodexDecision, AgentResult]:
        # Revisao critica sobe o raciocinio do proprio revisor (secao 5).
        effort = str(self.cfg.codex.extra.get("escalated_effort", "high")) \
            if not gate.passed else self.cfg.codex.default_effort
        codex_cfg = AgentConfig(self.cfg.codex.default_model, effort)

        prompt = render_codex_review(
            cfg=self.cfg, state=self.state, round_no=round_no,
            claude_result=claude_result, gate=gate, cwd=self.cwd,
        )
        result, invocation = self.codex.invoke(prompt, codex_cfg, round_no=round_no)
        self.state.codex_calls += 1

        decision = parse_codex_decision(result.structured, self.cfg)
        if not result.ok:
            # Sem decisao legivel, o seguro e' escalar para humano - nunca
            # continuar as cegas nem aprovar.
            decision.verdict = "NEEDS_HUMAN"
            decision.why = f"o revisor nao devolveu decisao utilizavel: {result.error}"
            decision.overrides.append("codex sem saida valida -> NEEDS_HUMAN")

        payload = {
            "decision": decision.to_dict(),
            "agent": result.to_dict(include_raw=False),
            "invocation": invocation.describe(),
            "prompt": prompt,
        }
        self.state.write_json(f"codex_round_{round_no:03d}.json", payload)
        return decision, result

    # ---------------- resolucao (o gate vence) ----------------

    def resolve(self, decision: CodexDecision, gate: GateResult,
                round_no: int, is_last_round: bool) -> tuple[str, str]:
        """Combina Codex + gate. Devolve (status, motivo).

        Status "CONTINUE" significa seguir para a proxima rodada.
        """
        verdict = decision.verdict

        if verdict in ("NEEDS_HUMAN", "NEEDS_REVIT"):
            return verdict, decision.why or f"revisor pediu {verdict}"

        if verdict == "FAILED":
            return "FAILED", decision.why or "revisor reprovou a rodada"

        if not gate.passed:
            # O FATO vence a OPINIAO. Com rodadas sobrando, damos ao Claude
            # a chance de consertar; na ultima, e' reprovacao.
            if is_last_round:
                return "FAILED", (
                    f"gate deterministico vermelho na ultima rodada "
                    f"(veredito do revisor era {verdict}): {gate.summary()}"
                )
            self.state.note(
                f"rodada {round_no}: veredito {verdict} rebaixado para CONTINUE "
                f"pelo gate vermelho"
            )
            return "CONTINUE", f"gate vermelho: {gate.summary()}"

        if verdict == "APPROVED":
            return "READY_FOR_HUMAN_REVIEW", decision.why or "revisor aprovou e gate verde"

        return "CONTINUE", decision.why or "revisor pediu continuacao"

    # ---------------- loop ----------------

    def run(self, initial_config: AgentConfig | None = None) -> LoopOutcome:
        max_rounds = self.state.max_rounds
        agent_cfg = initial_config or route_from_class(self.cfg, "standard")
        prompt = render_claude_initial(self.cfg, self.state, round_no=1,
                                       base_branch=self.base_branch)
        last_gate: GateResult | None = None
        decision: CodexDecision | None = None
        rounds_used = 0

        for round_no in range(1, max_rounds + 1):
            stop = self._budget_stop()
            if stop:
                self.state.note(f"parada por limite antes da rodada {round_no}: {stop}")
                status = "TIMEOUT" if stop == "TIMEOUT" else "NEEDS_HUMAN"
                return LoopOutcome(
                    status=status,
                    summary=f"limite atingido: {stop}",
                    do_not_merge=True,
                    last_gate=last_gate,
                    rounds_used=rounds_used,
                    human_question=("O limite de chamadas foi atingido antes de concluir. "
                                    "Aumente o limite ou reduza o escopo da tarefa."
                                    if status == "NEEDS_HUMAN" else ""),
                )

            rounds_used = round_no
            is_last = round_no == max_rounds
            round_record: dict[str, Any] = {
                "round": round_no,
                "claude": {"model": agent_cfg.model, "reasoning": agent_cfg.effort},
            }

            # 1. Claude executa
            claude_result = self._run_claude(prompt, agent_cfg, round_no)
            round_record["claude"].update({
                "ok": claude_result.ok,
                "status": claude_result.structured.get("status"),
                "summary": claude_result.structured.get("summary"),
                "cost_usd": claude_result.cost_usd,
                "duration_ms": claude_result.duration_ms,
                "error": claude_result.error,
            })

            if not claude_result.ok:
                self.state.record_round(round_record)
                return LoopOutcome(
                    status="FAILED",
                    summary=f"o executor falhou na rodada {round_no}: {claude_result.error}",
                    do_not_merge=True, last_gate=last_gate, rounds_used=rounds_used,
                )

            # Claude pode escalar sozinho, sem gastar uma revisao.
            claude_status = str(claude_result.structured.get("status") or "")
            if claude_status in ("NEEDS_REVIT", "NEEDS_HUMAN"):
                self.state.record_round(round_record)
                blockers = claude_result.structured.get("blockers") or []
                return LoopOutcome(
                    status=claude_status,
                    summary=str(claude_result.structured.get("summary") or ""),
                    do_not_merge=True,
                    human_question="; ".join(str(b) for b in blockers),
                    revit_capture_request=[str(b) for b in blockers]
                    if claude_status == "NEEDS_REVIT" else [],
                    last_gate=last_gate, rounds_used=rounds_used,
                )

            # 2. Gate deterministico
            gate = self._run_gate(round_no)
            last_gate = gate
            round_record["gate"] = {"status": gate.status, "passed": gate.passed,
                                    "summary": gate.summary()}

            # 3. Codex revisa e roteia
            decision, _ = self._run_codex(claude_result, gate, round_no)
            round_record["codex"] = {
                "verdict": decision.verdict,
                "next_model": decision.next_claude.model,
                "next_reasoning": decision.next_claude.effort,
                "routing_reason": decision.routing_reason,
                "routing_overrides": decision.overrides,
            }

            # 4. Resolucao (o gate tem veto)
            status, reason = self.resolve(decision, gate, round_no, is_last)
            round_record["resolution"] = {"status": status, "reason": reason}
            self.state.record_round(round_record)

            if status != "CONTINUE":
                return LoopOutcome(
                    status=status, summary=reason,
                    do_not_merge=(status != "READY_FOR_HUMAN_REVIEW"),
                    human_question=(decision.why if status == "NEEDS_HUMAN" else ""),
                    revit_capture_request=[
                        str(x) for x in (decision.raw.get("revit_capture_request") or [])
                    ] if status == "NEEDS_REVIT" else [],
                    last_gate=gate, rounds_used=rounds_used,
                )

            if is_last:
                break

            # O roteamento do Codex vira a configuracao REAL da proxima
            # invocacao: modelo e nivel de raciocinio mudam de verdade.
            agent_cfg = decision.next_claude
            prompt = render_claude_continue(
                self.cfg, self.state, round_no=round_no + 1,
                decision=decision, gate=gate, base_branch=self.base_branch,
            )

        summary = "MAX_ROUNDS atingido sem aprovacao"
        if decision is not None:
            summary += f" (ultimo veredito do revisor: {decision.verdict})"
        return LoopOutcome(status="MAX_ROUNDS", summary=summary, do_not_merge=True,
                           last_gate=last_gate, rounds_used=rounds_used)


def build_final_result(state: RunState, outcome: LoopOutcome, cwd: str = ".") -> dict[str, Any]:
    """Monta o `final_result.json` conforme o schema."""
    payload: dict[str, Any] = {
        "run_id": state.run_id,
        "status": outcome.status,
        "do_not_merge": outcome.do_not_merge,
        "task": state.task,
        "mode": state.mode,
        "branch": state.branch,
        "base_sha": state.base_sha,
        "head_sha": repo.head_sha(cwd),
        "rounds_used": outcome.rounds_used,
        "max_rounds": state.max_rounds,
        "total_cost_usd": round(state.total_cost_usd, 6),
        "claude_calls": state.claude_calls,
        "codex_calls": state.codex_calls,
        "gate": outcome.last_gate.to_dict() if outcome.last_gate else {"status": "NOT_RUN"},
        "rounds": state.rounds,
        "summary": outcome.summary,
        "notes": state.notes,
        "commits": repo.commits(state.base_sha, cwd),
    }
    if outcome.human_question:
        payload["human_question"] = outcome.human_question
    if outcome.revit_capture_request:
        payload["revit_capture_request"] = outcome.revit_capture_request
    return redact_obj(payload)
