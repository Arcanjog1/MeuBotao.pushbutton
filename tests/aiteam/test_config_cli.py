"""Politica, limites e a entrada de linha de comando."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_team.config import ConfigError, load_config
from ai_team.cli import MODES, build_parser, resolve_max_rounds

CONFIG_FILE = Path(__file__).resolve().parents[2] / "ai_team" / "config.yaml"


class TestPolitica:
    def test_config_do_projeto_e_valida(self, cfg):
        assert cfg.claude.default_model in cfg.claude.allowed_models
        assert cfg.codex.default_effort in cfg.codex.allowed_efforts

    def test_merge_automatico_em_main_e_proibido(self, cfg, tmp_path):
        """Secao 12 do pedido: a V1 nunca faz merge em main."""
        assert cfg.git.get("allow_merge_to_main") is False

        # E ligar isso na config e' um erro de configuracao, nao uma opcao.
        texto = CONFIG_FILE.read_text(encoding="utf-8").replace(
            "allow_merge_to_main: false", "allow_merge_to_main: true")
        ruim = tmp_path / "cfg.yaml"
        ruim.write_text(texto, encoding="utf-8")
        with pytest.raises(ConfigError, match="allow_merge_to_main"):
            load_config(ruim)

    def test_codex_e_read_only(self, cfg):
        assert cfg.codex.extra["sandbox"] == "read-only"

    def test_toda_classe_de_roteamento_usa_a_whitelist(self, cfg):
        for nome, entrada in cfg.routing_policy.items():
            assert entrada["model"] in cfg.claude.allowed_models, nome
            assert entrada["effort"] in cfg.claude.allowed_efforts, nome

    def test_gates_hard_estao_ligados(self, cfg):
        assert cfg.gates["pytest"]["enabled"] is True
        assert cfg.gates["pytest"]["hard"] is True
        assert cfg.gates["repo_invariants"]["hard"] is True


class TestLimites:
    def test_teto_de_rodadas_e_absoluto(self, cfg):
        """A UI do GitHub nao consegue passar do teto."""
        valor, nota = resolve_max_rounds(cfg, 999)
        assert valor == cfg.max_rounds_ceiling
        assert "acima do teto" in nota

    def test_default_quando_nao_informado(self, cfg):
        assert resolve_max_rounds(cfg, None)[0] == cfg.default_max_rounds
        assert resolve_max_rounds(cfg, 0)[0] == cfg.default_max_rounds

    def test_valor_dentro_do_teto_e_respeitado(self, cfg):
        assert resolve_max_rounds(cfg, 2)[0] == 2


class TestParser:
    def test_task_e_obrigatoria(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args([])

    def test_modo_invalido_e_recusado(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["--task", "x", "--mode", "inventado"])

    def test_modos_suportados(self):
        assert set(MODES) == {"diagnose", "implement", "review",
                              "benchmark", "full", "selftest"}

    def test_defaults(self):
        args = build_parser().parse_args(["--task", "fazer X"])
        assert args.mode == "full"
        assert args.max_rounds is None
