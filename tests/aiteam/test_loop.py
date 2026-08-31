"""O loop autonomo.

Cobre os pontos 1-13 da secao 21 do pedido: Claude roda, a saida e'
capturada, o Codex recebe automaticamente, produz JSON valido, o
`next_prompt` e' lido, o modelo e o raciocinio escolhidos sao APLICADOS,
o Claude roda de novo sem humano, e o loop para corretamente em cada
condicao de parada.
"""

from __future__ import annotations

import pytest

from ai_team.gates import CheckResult, GateResult
from ai_team.loop import Orchestrator
from ai_team.agents import ClaudeAgent, CodexAgent
from ai_team.routing import AgentConfig
from ai_team.selftest import (ScenarioExecutor, ScenarioStep, argv_value,
                              claude_stdout, codex_stdout)


def gate_verde() -> GateResult:
    return GateResult([CheckResult("pytest", "PASS", True, "exit=0")])


def gate_vermelho(detail: str = "openings: 91 -> 89") -> GateResult:
    return GateResult([CheckResult("metrics", "FAIL", True, detail)])


def make_orchestrator(cfg, state, executor, gate: GateResult, monkeypatch,
                      gates_por_rodada: list[GateResult] | None = None):
    """Orquestrador com o gate controlado (o gate real tem teste proprio)."""
    orch = Orchestrator(
        cfg=cfg, state=state,
        claude=ClaudeAgent(cfg, executor),
        codex=CodexAgent(cfg, executor),
    )
    fila = list(gates_por_rodada) if gates_por_rodada else None

    def fake_gate(round_no: int) -> GateResult:
        resultado = fila.pop(0) if fila else gate
        state.write_json(f"gate_round_{round_no:03d}.json", resultado.to_dict())
        return resultado

    monkeypatch.setattr(orch, "_run_gate", fake_gate)
    # O contexto do revisor le' o git; aqui a branch e' sintetica.
    monkeypatch.setattr("ai_team.prompts_render.repo.changed_files", lambda *a, **k: ["x.py"])
    monkeypatch.setattr("ai_team.prompts_render.repo.diff", lambda *a, **k: "diff sintetico")
    monkeypatch.setattr("ai_team.prompts_render.repo.commits", lambda *a, **k: ["abc123 fix"])
    return orch


class TestLoopEncadeiaSozinho:
    """Pontos 1-9: o ciclo completo, sem humano no meio."""

    def test_duas_rodadas_com_roteamento_aplicado(self, cfg, run_state, monkeypatch):
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("rodada 1", status="PARTIAL")),
            ScenarioStep("codex", codex_stdout(
                "CONTINUE", next_model="claude-opus-5", next_reasoning="xhigh",
                next_prompt="INSTRUCAO-DA-RODADA-2",
                routing_reason="causa raiz -> deep")),
            ScenarioStep("claude", claude_stdout("rodada 2", status="DONE")),
            ScenarioStep("codex", codex_stdout("APPROVED", why="pronto")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)

        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        # 1/8: o Claude rodou duas vezes, sem intervencao humana.
        assert len(executor.configs_for("claude")) == 2
        # 3/9: o Codex foi invocado automaticamente apos cada rodada.
        assert len(executor.configs_for("codex")) == 2
        # 6/7: o modelo E o raciocinio da rodada 2 sao os que o Codex escolheu.
        assert executor.configs_for("claude") == [
            ("claude-sonnet-5", "medium"), ("claude-opus-5", "xhigh")]
        # e isso chegou de fato no argv do subprocesso:
        argv_r2 = executor.argv_for("claude")[1]
        assert argv_value(argv_r2, "--model") == "claude-opus-5"
        assert argv_value(argv_r2, "--effort") == "xhigh"
        # 5: o `next_prompt` do Codex e' o que o Claude recebeu.
        assert "INSTRUCAO-DA-RODADA-2" in executor.calls[2].prompt
        # 10: parou corretamente, no estado certo.
        assert outcome.status == "READY_FOR_HUMAN_REVIEW"
        assert outcome.do_not_merge is False

    def test_saida_do_claude_chega_ao_prompt_do_codex(self, cfg, run_state, monkeypatch):
        """Ponto 2 e 3: a saida e' capturada e entregue ao revisor."""
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("MARCADOR-UNICO-DA-RODADA")),
            ScenarioStep("codex", codex_stdout("APPROVED")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        prompt_codex = executor.calls[1].prompt
        assert "MARCADOR-UNICO-DA-RODADA" in prompt_codex
        # o gate tambem vai junto - o revisor decide vendo o fato medido
        assert "pytest" in prompt_codex
        # e a politica de roteamento e as whitelists
        assert "claude-opus-5" in prompt_codex

    def test_estado_persistido_por_rodada(self, cfg, run_state, monkeypatch):
        """Ponto 15 do pedido: toda execucao deixa estado."""
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("r1", status="PARTIAL")),
            ScenarioStep("codex", codex_stdout("CONTINUE", next_prompt="segue")),
            ScenarioStep("claude", claude_stdout("r2", status="DONE")),
            ScenarioStep("codex", codex_stdout("APPROVED")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        for nome in ("task.json", "state.json",
                     "claude_round_001.json", "gate_round_001.json", "codex_round_001.json",
                     "claude_round_002.json", "codex_round_002.json"):
            assert (run_state.dir / nome).exists(), f"faltou {nome}"


class TestCondicoesDeParada:
    """Pontos 10-13: MAX_ROUNDS, NEEDS_HUMAN, FAILED."""

    def test_max_rounds_para_o_loop(self, cfg, run_state, monkeypatch):
        """Ponto 11: nunca loop infinito."""
        run_state.max_rounds = 2
        steps = []
        for _ in range(6):
            steps.append(ScenarioStep("claude", claude_stdout("segue", status="PARTIAL")))
            steps.append(ScenarioStep("codex", codex_stdout("CONTINUE", next_prompt="mais")))
        executor = ScenarioExecutor(steps=steps)
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)

        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        assert outcome.status == "MAX_ROUNDS"
        assert outcome.rounds_used == 2
        assert len(executor.configs_for("claude")) == 2
        assert outcome.do_not_merge is True

    def test_needs_human_para_imediatamente(self, cfg, run_state, monkeypatch):
        """Ponto 12."""
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("r1", status="PARTIAL")),
            ScenarioStep("codex", codex_stdout(
                "NEEDS_HUMAN", why="decisao de arquitetura: trocar o formato do snapshot")),
            ScenarioStep("claude", claude_stdout("nao deveria rodar")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        assert outcome.status == "NEEDS_HUMAN"
        assert "arquitetura" in outcome.human_question
        assert len(executor.configs_for("claude")) == 1  # nao seguiu adiante

    def test_failed_para_imediatamente(self, cfg, run_state, monkeypatch):
        """Ponto 13."""
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("r1", status="PARTIAL")),
            ScenarioStep("codex", codex_stdout("FAILED", why="regressao real sem conserto")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        assert outcome.status == "FAILED"
        assert outcome.do_not_merge is True

    def test_needs_revit_preserva_o_pedido_de_captura(self, cfg, run_state, monkeypatch):
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout(
                "precisa medir no Revit", status="NEEDS_REVIT",
                blockers=["medir o vao menor do B34 na fiada 3 da parede W-12"])),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        assert outcome.status == "NEEDS_REVIT"
        assert outcome.revit_capture_request == [
            "medir o vao menor do B34 na fiada 3 da parede W-12"]

    def test_claude_quebrado_reprova_a_run(self, cfg, run_state, monkeypatch):
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", "isso nao e' json", exit_code=1),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))
        assert outcome.status == "FAILED"

    def test_codex_sem_saida_valida_escala_para_humano(self, cfg, run_state, monkeypatch):
        """Nunca continuar as cegas nem aprovar quando o revisor falhou."""
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("r1", status="PARTIAL")),
            ScenarioStep("codex", "o revisor explodiu", exit_code=1),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))
        assert outcome.status == "NEEDS_HUMAN"

    def test_limite_de_chamadas_para_o_loop(self, cfg, run_state, monkeypatch):
        """Secao 14 do pedido: controle de custo."""
        run_state.max_rounds = 8
        run_state.claude_calls = cfg.max_claude_calls  # ja' no teto
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("nao deveria rodar")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch)
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        assert outcome.status == "NEEDS_HUMAN"
        assert executor.configs_for("claude") == []


class TestGateTemVeto:
    """Secao 7: as IAs nao sao o juiz final."""

    def test_gate_vermelho_vence_codex_approved_na_ultima_rodada(
            self, cfg, run_state, monkeypatch):
        """O caso literal do pedido: Claude OK + Codex APPROVED + openings 91->89."""
        run_state.max_rounds = 1
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("tudo certo", status="DONE")),
            ScenarioStep("codex", codex_stdout("APPROVED", why="parece bom")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_vermelho(), monkeypatch)
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        assert outcome.status == "FAILED"
        assert outcome.do_not_merge is True
        assert "openings: 91 -> 89" in outcome.summary

    def test_gate_vermelho_rebaixa_approved_para_continue_com_rodadas_sobrando(
            self, cfg, run_state, monkeypatch):
        """Com rodada sobrando, o Claude ganha a chance de consertar."""
        run_state.max_rounds = 2
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("r1", status="DONE")),
            ScenarioStep("codex", codex_stdout("APPROVED", why="parece bom")),
            ScenarioStep("claude", claude_stdout("r2 consertou", status="DONE")),
            ScenarioStep("codex", codex_stdout("APPROVED", why="agora sim")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_verde(), monkeypatch,
                                 gates_por_rodada=[gate_vermelho(), gate_verde()])
        outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        assert len(executor.configs_for("claude")) == 2
        assert outcome.status == "READY_FOR_HUMAN_REVIEW"

    def test_gate_vermelho_nunca_vira_ready_for_human_review(
            self, cfg, run_state, monkeypatch):
        run_state.max_rounds = 1
        for verdict in ("APPROVED", "CONTINUE"):
            executor = ScenarioExecutor(steps=[
                ScenarioStep("claude", claude_stdout("r1", status="DONE")),
                ScenarioStep("codex", codex_stdout(verdict, next_prompt="segue")),
            ])
            state = run_state
            state.rounds = []
            orch = make_orchestrator(cfg, state, executor, gate_vermelho(), monkeypatch)
            outcome = orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))
            assert outcome.status != "READY_FOR_HUMAN_REVIEW"

    def test_gate_vermelho_escala_o_raciocinio_do_revisor(self, cfg, run_state, monkeypatch):
        """Secao 5: revisao critica roda com raciocinio mais alto."""
        run_state.max_rounds = 1
        executor = ScenarioExecutor(steps=[
            ScenarioStep("claude", claude_stdout("r1", status="DONE")),
            ScenarioStep("codex", codex_stdout("FAILED", why="x")),
        ])
        orch = make_orchestrator(cfg, run_state, executor, gate_vermelho(), monkeypatch)
        orch.run(initial_config=AgentConfig("claude-sonnet-5", "medium"))

        modelo, effort = executor.configs_for("codex")[0]
        assert effort == cfg.codex.extra["escalated_effort"] == "high"
