"""Regressoes do hotfix "AI Team cloud selftest" (branch
fix/ai-team-cloud-selftest).

Reproduz exatamente os dois bugs vistos no primeiro selftest REAL do
GitHub Actions:

    ERRO 1 - o gate pytest do proprio `--mode selftest` colecionava
             `tests/aiteam/test_selftest_e2e.py`, que tenta iniciar outro
             `python -m ai_team --mode selftest` de dentro do gate. A
             guarda de recursao (`AI_TEAM_RUN_ACTIVE`) barra corretamente
             - mas isso derrubava o gate por um motivo que nao e' uma
             regressao real.
    ERRO 2 - `repo_invariants` reprovava HARD porque HEAD fica em `main`
             quando o workflow chama o selftest com `--no-branch` (nao ha'
             branch nova nem agente real - o objetivo e' so' validar o
             encanamento offline).

IMPORTANTE (secao 22 do pedido): nenhum destes testes toca Script.py,
nuvem/**, wall modeling, solver ou modulacao. Todos rodam contra o
proprio motor do AI Team, com o mesmo alvo de fixture descartavel usado
por `test_selftest_e2e.py`.

Como este proprio modulo spawna `python -m ai_team` como subprocesso,
ele tambem carrega o marcador `ai_team_e2e` (ver pytest.ini e
`ai_team/cli.py::_scope_pytest_gate_for_selftest`), para nunca rodar
dentro do gate de um `--mode selftest` - senao recursaria nele mesmo.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ai_team.cli import (AI_TEAM_E2E_MARKER, RUN_ACTIVE_ENV,
                         _allow_protected_head, write_summary)
from ai_team.gates import run_gates, run_repo_invariants_check
from ai_team.config import load_config

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.ai_team_e2e


# ---------------------------------------------------------------------
# SELFTEST-CLOUD-001 / 004 / 005 - selftest ponta a ponta, sem
# --gate-command explicito (a UI nao passa isso), reproduzindo o
# caminho exato do workflow.
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def run_selftest_sem_gate_command_explicito(tmp_path_factory):
    """Mesmo caminho do workflow: `--mode selftest --no-branch`, SEM
    `--gate-command`. Prova que o escopo do gate e' automatico.

    NUNCA remove `AI_TEAM_RUN_ACTIVE` do ambiente se ele ja' estiver
    definido - isso seria desligar a propria guarda de recursao que este
    teste existe para provar. Este modulo carrega `ai_team_e2e` e o gate
    escopado do selftest ja' o exclui (ver
    `_scope_pytest_gate_for_selftest`); se mesmo assim este fixture for
    exercitado dentro de uma run ja' ativa, o seguro e' pular o teste, nao
    mascarar a guarda.
    """
    if os.environ.get(RUN_ACTIVE_ENV):
        pytest.skip(
            f"{RUN_ACTIVE_ENV} ja' esta' definido - rodando dentro de uma "
            "run do AI Team ativa. Este teste so' faz sentido no nivel "
            "raiz (SELFTEST-CLOUD-001 exige AI_TEAM_RUN_ACTIVE AUSENTE no "
            "inicio); nunca removemos a guarda para forcar o cenario, "
            "senao estariamos desligando a propria protecao contra "
            "recursao que este teste existe para provar."
        )
    runs = tmp_path_factory.mktemp("runs")
    summary = runs / "summary.md"
    env = os.environ.copy()  # AI_TEAM_RUN_ACTIVE genuinamente ausente aqui.
    proc = subprocess.run(
        [sys.executable, "-m", "ai_team",
         "--task", "Hotfix selftest cloud - reproduzir bug do runner real",
         "--mode", "selftest", "--max-rounds", "3", "--no-branch",
         "--runs-dir", str(runs), "--summary-file", str(summary)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=1800, env=env,
    )
    run_dirs = [d for d in runs.iterdir() if d.is_dir()]
    assert len(run_dirs) == 1, proc.stderr
    return proc, run_dirs[0], summary


def test_selftest_cloud_001_gate_nao_recursa_e_termina_com_sucesso(
        run_selftest_sem_gate_command_explicito):
    """AI_TEAM_RUN_ACTIVE comeca ausente; o proprio orquestrador o define,
    roda o gate, e o gate NAO tenta iniciar outro AI Team. PASS."""
    proc, run_dir, _ = run_selftest_sem_gate_command_explicito
    assert proc.returncode == 0, proc.stderr

    final = json.loads((run_dir / "final_result.json").read_text(encoding="utf-8"))
    assert final["status"] == "READY_FOR_HUMAN_REVIEW"
    assert final["do_not_merge"] is False
    assert final["gate"]["passed"] is True
    assert final["gate"]["status"] == "PASS"

    gate_1 = json.loads((run_dir / "gate_round_001.json").read_text(encoding="utf-8"))
    pytest_check = next(c for c in gate_1["checks"] if c["name"] == "pytest")
    assert pytest_check["status"] == "PASS"
    # A recursao, se tivesse acontecido, apareceria no detalhe do check
    # (a mensagem de stderr do subprocesso barrado por AI_TEAM_RUN_ACTIVE).
    assert "Recursao abortada" not in pytest_check["detail"]


def test_selftest_cloud_005_exatamente_duas_rodadas_sem_rodada_3(
        run_selftest_sem_gate_command_explicito):
    """Rodada 1 sonnet/medium -> Codex CONTINUE (opus/high) -> rodada 2
    opus/high -> Codex APPROVED -> gate PASS -> READY_FOR_HUMAN_REVIEW.
    Exatamente 2 invocacoes de cada agente, nenhuma rodada 3."""
    _, run_dir, _ = run_selftest_sem_gate_command_explicito
    final = json.loads((run_dir / "final_result.json").read_text(encoding="utf-8"))

    assert final["rounds_used"] == 2
    assert final["claude_calls"] == 2
    assert final["codex_calls"] == 2
    assert not (run_dir / "claude_round_003.json").exists()
    assert not (run_dir / "codex_round_003.json").exists()

    rodada_1 = json.loads((run_dir / "claude_round_001.json").read_text(encoding="utf-8"))
    decisao_1 = json.loads((run_dir / "codex_round_001.json").read_text(encoding="utf-8"))
    rodada_2 = json.loads((run_dir / "claude_round_002.json").read_text(encoding="utf-8"))
    decisao_2 = json.loads((run_dir / "codex_round_002.json").read_text(encoding="utf-8"))

    assert rodada_1["model"] == "claude-sonnet-5"
    assert rodada_1["reasoning"] == "medium"
    assert decisao_1["decision"]["verdict"] == "CONTINUE"
    assert decisao_1["decision"]["next_model"] == "claude-opus-5"
    assert decisao_1["decision"]["next_reasoning"] == "high"
    assert rodada_2["model"] == "claude-opus-5"
    assert rodada_2["reasoning"] == "high"
    assert decisao_2["decision"]["verdict"] == "APPROVED"


def test_selftest_cloud_004_recursao_continua_barrada(tmp_path):
    """AI_TEAM_RUN_ACTIVE=1 -> nova invocacao do AI Team continua
    retornando erro de recursao. A protecao NAO foi enfraquecida."""
    env = dict(os.environ, **{RUN_ACTIVE_ENV: "1"})
    proc = subprocess.run(
        [sys.executable, "-m", "ai_team", "--task", "x", "--mode", "selftest",
         "--no-branch", "--runs-dir", str(tmp_path)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120, env=env)
    assert proc.returncode == 2
    assert "Recursao abortada" in proc.stderr
    # Confirma que a run realmente nao produziu artefato nenhum.
    assert list(tmp_path.iterdir()) == []


def test_selftest_cloud_006_relatorio_nunca_mostra_custo_sintetico_como_real(
        run_selftest_sem_gate_command_explicito, tmp_path):
    """O custo sintetico de `claude_stdout(cost=0.02)` nunca pode ser
    apresentado como cobranca real de API."""
    _, run_dir, summary_path = run_selftest_sem_gate_command_explicito
    final = json.loads((run_dir / "final_result.json").read_text(encoding="utf-8"))

    assert final["api_cost_usd"] == 0.0
    assert final["simulated_cost_usd"] > 0.0  # o cenario roteirizado usa cost=0.02 x2
    assert final["claude_calls_simulated"] is True
    assert final["codex_calls_simulated"] is True

    texto = summary_path.read_text(encoding="utf-8")
    assert "Custo API real:** US$ 0.0 (selftest offline)" in texto
    assert "SIMULATED INVOCATIONS" in texto
    # Nao pode aparecer como se fosse o custo real sem qualificacao.
    assert "**Custo (Claude):**" not in texto


def test_selftest_cloud_006b_write_summary_isolado(tmp_path):
    """Mesma prova acima, sem depender do subprocesso - direto na funcao."""
    final = build_final_result_stub()
    path = tmp_path / "summary.md"
    write_summary(str(path), final)
    texto = path.read_text(encoding="utf-8")
    assert "Custo API real:** US$ 0.0 (selftest offline)" in texto
    assert "custo simulado (fixture): US$ 0.04" in texto
    assert "SIMULATED INVOCATIONS" in texto


def build_final_result_stub() -> dict:
    return {
        "status": "READY_FOR_HUMAN_REVIEW", "task": "x", "mode": "selftest",
        "branch": "main", "rounds_used": 2, "max_rounds": 3,
        "gate": {"status": "PASS", "summary": "GATE PASS"},
        "total_cost_usd": 0.04, "api_cost_usd": 0.0, "simulated_cost_usd": 0.04,
        "claude_calls": 2, "codex_calls": 2,
        "claude_calls_simulated": True, "codex_calls_simulated": True,
        "do_not_merge": False, "summary": "ok", "rounds": [],
    }


# ---------------------------------------------------------------------
# SELFTEST-CLOUD-002 / 003 - repo_invariants: a excecao de HEAD protegido
# so' vale para (mode=selftest, no_branch=True), e mesmo assim a SHA da
# main tem que ficar intacta.
# ---------------------------------------------------------------------

class TestAllowProtectedHead:
    """`_allow_protected_head` e' a UNICA porta de entrada da excecao -
    testa-la isolada prova que nenhum input de usuario chega direto nela."""

    def test_selftest_com_no_branch_libera(self):
        assert _allow_protected_head("selftest", True) is True

    def test_selftest_sem_no_branch_nao_libera(self):
        """selftest com branch de verdade (nao e' o caso do workflow, mas
        se acontecer) continua com HEAD protegido reprovando."""
        assert _allow_protected_head("selftest", False) is False

    @pytest.mark.parametrize("mode", ["full", "implement", "diagnose",
                                      "review", "benchmark"])
    def test_selftest_cloud_003_modos_reais_nunca_liberam(self, mode):
        """SELFTEST-CLOUD-003: prova que a excecao NAO vazou para runs
        reais, mesmo se alguem passasse --no-branch manualmente."""
        assert _allow_protected_head(mode, True) is False
        assert _allow_protected_head(mode, False) is False


class TestRepoInvariantsComExcecaoDoSelftest:
    def test_selftest_cloud_002_pass_com_head_em_main_e_sha_intacta(self, monkeypatch):
        """repo_invariants deve PASSAR pelo fato de HEAD estar em `main`
        SOMENTE quando allow_protected_head=True (selftest+no-branch),
        desde que a main nao tenha se mexido nem a working tree sujado."""
        def fake_git(args, cwd="."):
            if "--abbrev-ref" in args:
                return "main"
            if args[:2] == ["rev-parse", "main"]:
                return "a" * 40
            if args[:1] == ["rev-parse"] and args[1:2] == ["HEAD"]:
                return "a" * 40
            if args[:1] == ["status"]:
                return ""
            return ""
        monkeypatch.setattr("ai_team.gates._git", fake_git)

        result = run_repo_invariants_check(
            {"hard": True, "protected_branches": ["main"], "_base_branch": "main"},
            base_sha_before="a" * 40, allow_protected_head=True,
            head_sha_before="a" * 40)
        assert result.status == "PASS"
        assert result.data["allow_protected_head"] is True

    def test_selftest_cloud_002_fail_se_a_main_mudou_mesmo_com_excecao(self, monkeypatch):
        """A excecao NUNCA cobre a main se mexendo - isso continua HARD FAIL."""
        def fake_git(args, cwd="."):
            if "--abbrev-ref" in args:
                return "main"
            if args[:2] == ["rev-parse", "main"]:
                return "b" * 40  # main andou
            if args[:1] == ["rev-parse"] and args[1:2] == ["HEAD"]:
                return "b" * 40
            if args[:1] == ["status"]:
                return ""
            return ""
        monkeypatch.setattr("ai_team.gates._git", fake_git)

        result = run_repo_invariants_check(
            {"hard": True, "protected_branches": ["main"], "_base_branch": "main"},
            base_sha_before="a" * 40, allow_protected_head=True,
            head_sha_before="a" * 40)
        assert result.status == "FAIL"
        assert "mudou" in result.detail

    def test_selftest_cloud_002_fail_se_working_tree_sujou(self, monkeypatch):
        """Mesmo sem a main se mexer, working tree suja durante o selftest
        e' HARD FAIL (nenhum agente real deveria ter alterado nada)."""
        def fake_git(args, cwd="."):
            if "--abbrev-ref" in args:
                return "main"
            if args[:2] == ["rev-parse", "main"]:
                return "a" * 40
            if args[:1] == ["rev-parse"] and args[1:2] == ["HEAD"]:
                return "a" * 40
            if args[:1] == ["status"]:
                return " M ai_team/fixtures/sandbox_target.txt"
            return ""
        monkeypatch.setattr("ai_team.gates._git", fake_git)

        result = run_repo_invariants_check(
            {"hard": True, "protected_branches": ["main"], "_base_branch": "main"},
            base_sha_before="a" * 40, allow_protected_head=True,
            head_sha_before="a" * 40)
        assert result.status == "FAIL"
        assert "working tree" in result.detail

    def test_selftest_cloud_002_fail_se_head_avancou_sem_a_main_mover(self, monkeypatch):
        """Um commit local (mesmo sem afetar `main`) durante o selftest
        tambem e' proibido: nenhum commit deveria ter sido criado."""
        def fake_git(args, cwd="."):
            if "--abbrev-ref" in args:
                return "main"
            if args[:2] == ["rev-parse", "main"]:
                return "a" * 40
            if args[:1] == ["rev-parse"] and args[1:2] == ["HEAD"]:
                return "c" * 40  # HEAD avancou
            if args[:1] == ["status"]:
                return ""
            return ""
        monkeypatch.setattr("ai_team.gates._git", fake_git)

        result = run_repo_invariants_check(
            {"hard": True, "protected_branches": ["main"], "_base_branch": "main"},
            base_sha_before="a" * 40, allow_protected_head=True,
            head_sha_before="a" * 40)
        assert result.status == "FAIL"
        assert "commit" in result.detail

    def test_selftest_cloud_003_sem_excecao_head_em_main_continua_hard_fail(self, monkeypatch):
        """SELFTEST-CLOUD-003: sem `allow_protected_head` (o caminho de
        toda run real), HEAD em `main` continua reprovando - exatamente o
        comportamento anterior ao hotfix, intacto."""
        monkeypatch.setattr("ai_team.gates._git",
                            lambda args, cwd=".": "main" if "--abbrev-ref" in args else "")
        result = run_repo_invariants_check(
            {"hard": True, "protected_branches": ["main"]})
        assert result.status == "FAIL"
        assert "protegida" in result.detail

        # E via run_gates(), com o default (allow_protected_head=False):
        # confirma que nenhum modo real recebe a excecao por acidente.
        #
        # ATENCAO: `run_gates()` chama o check de pytest com o COMANDO REAL
        # da config (a suite inteira `tests/`), sem passar pelo escopo
        # automatico do `--mode selftest` (isso so' acontece dentro de
        # `cli.py::main`, nao dentro de `run_gates()`). Rodar isso aqui
        # literalmente executaria a suite inteira de novo, DENTRO deste
        # proprio teste, sem a guarda `AI_TEAM_RUN_ACTIVE` - ou seja,
        # recursao de verdade e' descontrolada (foi exatamente isto que
        # produziu uma explosao de processos ao escrever este teste).
        # Desligamos o check de pytest aqui porque o unico check que
        # importa para esta asserção e' `repo_invariants`.
        cfg = load_config()
        cfg.raw["gates"]["pytest"]["enabled"] = False
        gate = run_gates(cfg, expected_branch="main")
        invariants = next(c for c in gate.checks if c.name == "repo_invariants")
        assert invariants.status == "FAIL"


# ---------------------------------------------------------------------
# Marcador ai_team_e2e continua registrado e escopando o gate de verdade.
# ---------------------------------------------------------------------

def test_marcador_ai_team_e2e_esta_registrado_no_pytest_ini():
    texto = (REPO_ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert AI_TEAM_E2E_MARKER in texto


def test_o_solver_nao_foi_tocado():
    """Secao 22 do pedido: esta tarefa e' infraestrutura, nao mexe no motor."""
    proc = subprocess.run(["git", "status", "--porcelain", "Script.py", "nuvem/"],
                          cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert proc.stdout.strip() == ""
