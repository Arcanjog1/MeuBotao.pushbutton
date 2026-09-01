"""Ponto 14 da auditoria pre-merge: nomes de branch vindos de input externo
(o campo `branch_name` da UI do workflow) sao sanitizados antes de tocar
o git.

Sem isto, `--branch` chegaria cru em `git checkout -B <nome> <base>`. O
argv e' uma lista (sem shell), entao injecao de shell nao e' o risco -
o risco real e' um nome comecando com `-` sendo lido pelo git como FLAG
do comando, ou o nome ser literalmente `main`/`master`, desviando o
checkout para a branch protegida.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ai_team import repo

REPO_ROOT = Path(__file__).resolve().parents[2]

NOMES_PERIGOSOS = [
    "main", "Main", "MASTER", "HEAD", "head",
    "refs/heads/main",
    "--upload-pack=touch /tmp/pwned",
    "-x",
    "--force",
    "a/../../etc/passwd",
    "a//b",
    "/a", "a/",
    "feature.lock",
    "a@{yesterday}",
    "a" * 300,
    "",
    "  ",
    "a\\b",
]

NOMES_SEGUROS = [
    "ai/cr-2fe-centerline-invariance",
    "ai/tarefa-simples",
    "ai/CR-2F-A_v2",
]


class TestSanitizeBranchName:
    @pytest.mark.parametrize("nome", NOMES_PERIGOSOS)
    def test_nomes_perigosos_sao_recusados(self, nome):
        ok, _ = repo.sanitize_branch_name(nome)
        assert ok is False, f"deveria recusar: {nome!r}"

    @pytest.mark.parametrize("nome", NOMES_SEGUROS)
    def test_nomes_seguros_passam(self, nome):
        ok, resultado = repo.sanitize_branch_name(nome)
        assert ok is True, f"deveria aceitar: {nome!r}"
        assert resultado == nome


class TestEnsureBranchSegundaCamada:
    """Defesa em profundidade: `ensure_branch` recusa protegidas por si so',
    mesmo se um chamador pulasse a sanitizacao."""

    @pytest.mark.parametrize("nome", ["main", "Main", "MASTER"])
    def test_recusa_branch_protegida_mesmo_sem_sanitizar_antes(self, nome, tmp_path):
        ok, message = repo.ensure_branch(nome, "main", cwd=str(tmp_path))
        assert ok is False
        assert "protegida" in message


@pytest.mark.ai_team_e2e
class TestCliRecusaNomePerigosoDeVerdade:
    """Prova pela CLI real: `--branch` hostil nunca chega ao `git checkout`.

    Spawna `python -m ai_team` de verdade - por isso carrega
    `ai_team_e2e`: se isto rodar DENTRO do gate de uma run que ja' esta'
    com `AI_TEAM_RUN_ACTIVE=1` (ex.: o gate escopado do `--mode
    selftest`), a guarda de recursao aborta o subprocesso (corretamente),
    e o teste falharia por um motivo que nao e' uma regressao real. Ver
    `ai_team/cli.py::_scope_pytest_gate_for_selftest`.
    """

    def _run(self, tmp_path, branch: str) -> subprocess.CompletedProcess:
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=repo_dir, check=True)
        (repo_dir / "x.txt").write_text("x")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo_dir, check=True)

        runs = tmp_path / "runs"
        return subprocess.run(
            [sys.executable, "-m", "ai_team", "--task", "tarefa de teste",
             "--mode", "selftest",
             # `--branch=valor` (nao `--branch valor`): um valor comecando
             # com `--` seria lido pelo PROPRIO argparse como outra flag -
             # comportamento padrao de qualquer CLI, nao um bug daqui. O
             # teste simula como o valor chega de fato (env var no
             # workflow, nunca token solto).
             f"--branch={branch}",
             "--runs-dir", str(runs), "--cwd", str(repo_dir),
             "--gate-command", '["python3","-c","pass"]'],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120,
        )

    def test_branch_main_e_recusada_e_degrada_para_a_gerada(self, tmp_path):
        proc = self._run(tmp_path, "main")
        assert proc.returncode == 0, proc.stderr
        # a branch efetivamente usada NAO pode ser "main"
        assert '"branch": "main"' not in proc.stdout
        assert "tarefa-de-teste" in proc.stdout or "ai/" in proc.stdout

    def test_branch_com_flag_e_recusada(self, tmp_path):
        proc = self._run(tmp_path, "--upload-pack=x")
        assert proc.returncode == 0, proc.stderr
        assert "--upload-pack" not in proc.stdout
