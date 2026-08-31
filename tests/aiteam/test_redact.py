"""Ponto 14 da secao 21: segredos nao aparecem nos logs.

A defesa que importa e' a primeira: se a chave esta' no ambiente, qualquer
eco dela some. Os padroes sao a rede de seguranca para um segredo que o
orquestrador nunca viu.
"""

from __future__ import annotations

import json

from ai_team.gates import CheckResult, GateResult
from ai_team.redact import PLACEHOLDER, contains_secret, redact, redact_obj
from ai_team.state import create_run

CHAVE_ANTHROPIC = "sk-ant-api03-" + "A1b2C3d4E5f6G7h8" * 3
CHAVE_OPENAI = "sk-proj-" + "Z9y8X7w6V5u4T3s2" * 2
TOKEN_GITHUB = "ghp_" + "abcdefghij1234567890ABCD"
AMBIENTE = {"ANTHROPIC_API_KEY": CHAVE_ANTHROPIC, "OPENAI_API_KEY": CHAVE_OPENAI,
            "GITHUB_TOKEN": TOKEN_GITHUB}


class TestRedacao:
    def test_valor_do_ambiente_e_removido(self):
        texto = f"chamando a API com {CHAVE_ANTHROPIC} agora"
        saida = redact(texto, environ=AMBIENTE)
        assert CHAVE_ANTHROPIC not in saida
        assert PLACEHOLDER in saida

    def test_todos_os_segredos_do_ambiente(self):
        texto = f"{CHAVE_ANTHROPIC} {CHAVE_OPENAI} {TOKEN_GITHUB}"
        saida = redact(texto, environ=AMBIENTE)
        assert not contains_secret(saida, environ=AMBIENTE)

    def test_padroes_sem_ambiente(self):
        """Segredo que o orquestrador nunca viu tambem e' apagado."""
        texto = "sk-ant-api03-DESCONHECIDA1234567890abcdef e ghp_ZZZZ1111YYYY2222XXXX"
        saida = redact(texto, environ={})
        assert "sk-ant-api03-DESCONHECIDA" not in saida
        assert "ghp_ZZZZ1111YYYY2222XXXX" not in saida

    def test_chave_privada_pem(self):
        pem = ("-----BEGIN RSA PRIVATE KEY-----\nMIIEabc123\n"
               "-----END RSA PRIVATE KEY-----")
        assert "MIIEabc123" not in redact(pem, environ={})

    def test_token_de_url_do_runner(self):
        url = "https://x-access-token:ghs_SEGREDO1234567890abcd@github.com/o/r.git"
        saida = redact(url, environ={})
        assert "ghs_SEGREDO1234567890abcd" not in saida
        assert "github.com" in saida

    def test_variavel_vazia_ou_curta_nao_apaga_tudo(self):
        """Um valor curto nao pode transformar o log inteiro em [REDACTED]."""
        saida = redact("texto normal com a letra a", environ={"GITHUB_TOKEN": "a"})
        assert saida == "texto normal com a letra a"

    def test_nao_strings_passam_intactos(self):
        assert redact(42) == 42
        assert redact(None) is None


class TestRedacaoRecursiva:
    def test_dict_aninhado(self):
        payload = {"cfg": {"key": CHAVE_ANTHROPIC},
                   "lista": [{"t": TOKEN_GITHUB}, "limpo"],
                   "n": 7}
        saida = redact_obj(payload, environ=AMBIENTE)
        texto = json.dumps(saida)
        assert not contains_secret(texto, environ=AMBIENTE)
        assert saida["n"] == 7
        assert saida["lista"][1] == "limpo"


class TestEstadoNaoVazaSegredo:
    """O caminho real: tudo que vai a disco passa pela redacao."""

    def test_arquivo_de_estado_nao_contem_segredo(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", CHAVE_ANTHROPIC)
        monkeypatch.setenv("OPENAI_API_KEY", CHAVE_OPENAI)

        state = create_run("tarefa", "full", 2, root=tmp_path / "runs")
        state.write_json("claude_round_001.json", {
            "prompt": f"use a chave {CHAVE_ANTHROPIC}",
            "raw": {"stderr": f"falhou com {CHAVE_OPENAI}"},
        })

        for arquivo in state.dir.glob("*.json"):
            conteudo = arquivo.read_text(encoding="utf-8")
            assert CHAVE_ANTHROPIC not in conteudo, arquivo.name
            assert CHAVE_OPENAI not in conteudo, arquivo.name

    def test_resumo_do_gate_e_redigido(self):
        check = CheckResult("pytest", "FAIL", True, f"erro: {CHAVE_ANTHROPIC}")
        assert CHAVE_ANTHROPIC not in json.dumps(check.to_dict())

    def test_step_summary_e_redigido(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", CHAVE_ANTHROPIC)
        from ai_team.cli import write_summary
        destino = tmp_path / "summary.md"
        write_summary(str(destino), {
            "status": "FAILED", "task": f"tarefa com {CHAVE_ANTHROPIC}",
            "mode": "full", "branch": "ai/x", "rounds_used": 1, "max_rounds": 3,
            "gate": GateResult().to_dict(), "total_cost_usd": 0.1,
            "claude_calls": 1, "codex_calls": 1, "do_not_merge": True,
            "summary": f"falhou: {CHAVE_ANTHROPIC}", "rounds": [],
        })
        assert CHAVE_ANTHROPIC not in destino.read_text(encoding="utf-8")
