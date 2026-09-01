"""Teste sintetico ponta a ponta (secao 21 do pedido).

Roda o `python -m ai_team --mode selftest` de verdade - o mesmo caminho
de codigo que o workflow usa - e confere o artefato final. Offline, sem
nenhuma API key, e sem tocar no solver / wall modeling / modulacao
(secao 22): o alvo e' um arquivo de fixture descartavel.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Todo teste deste modulo spawna `python -m ai_team` como subprocesso -
#: nunca pode rodar dentro do proprio gate do `--mode selftest`, senao
#: recursa (AI_TEAM_RUN_ACTIVE ja' estaria "1", herdado pelo subprocesso).
#: O gate escopado automaticamente exclui este marcador; ver
#: ai_team/cli.py::_scope_pytest_gate_for_selftest.
pytestmark = pytest.mark.ai_team_e2e


@pytest.fixture(scope="module")
def run_selftest(tmp_path_factory):
    runs = tmp_path_factory.mktemp("runs")
    summary = runs / "summary.md"
    proc = subprocess.run(
        [sys.executable, "-m", "ai_team",
         "--task", "Teste sintetico do orquestrador AI Team",
         "--mode", "selftest", "--max-rounds", "3", "--no-branch",
         "--runs-dir", str(runs), "--summary-file", str(summary),
         # Gate escopado: a suite inteira inclui ESTE teste, e roda-la aqui
         # dentro seria recursao. O gate completo tem cobertura propria em
         # test_gates.py.
         "--gate-command", json.dumps(
             [sys.executable, "-m", "pytest", "tests/aiteam/test_routing.py", "-q"])],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=900,
    )
    run_dirs = [d for d in runs.iterdir() if d.is_dir()]
    assert len(run_dirs) == 1, proc.stderr
    return proc, run_dirs[0], summary


def test_processo_termina_com_sucesso(run_selftest):
    proc, _, _ = run_selftest
    assert proc.returncode == 0, proc.stderr


def test_resultado_final_e_ready_for_human_review(run_selftest):
    _, run_dir, _ = run_selftest
    final = json.loads((run_dir / "final_result.json").read_text(encoding="utf-8"))
    assert final["status"] == "READY_FOR_HUMAN_REVIEW"
    assert final["do_not_merge"] is False
    assert final["gate"]["passed"] is True


def test_o_loop_encadeou_duas_rodadas_sem_humano(run_selftest):
    _, run_dir, _ = run_selftest
    final = json.loads((run_dir / "final_result.json").read_text(encoding="utf-8"))
    assert final["rounds_used"] == 2
    assert final["claude_calls"] == 2
    assert final["codex_calls"] == 2


def test_o_roteamento_trocou_modelo_e_raciocinio_de_verdade(run_selftest):
    """A prova dos pontos 6 e 7: a rodada 2 rodou no que o Codex escolheu."""
    _, run_dir, _ = run_selftest
    rodada_1 = json.loads((run_dir / "claude_round_001.json").read_text(encoding="utf-8"))
    rodada_2 = json.loads((run_dir / "claude_round_002.json").read_text(encoding="utf-8"))
    decisao_1 = json.loads((run_dir / "codex_round_001.json").read_text(encoding="utf-8"))

    assert rodada_1["model"] == "claude-sonnet-5"
    assert rodada_1["reasoning"] == "medium"

    # o que o revisor pediu...
    assert decisao_1["decision"]["next_model"] == "claude-opus-5"
    assert decisao_1["decision"]["next_reasoning"] == "high"
    # ...foi o que a rodada 2 executou, no argv real:
    argv = rodada_2["invocation"]["argv"]
    assert argv[argv.index("--model") + 1] == "claude-opus-5"
    assert argv[argv.index("--effort") + 1] == "high"


def test_o_next_prompt_do_revisor_chegou_ao_executor(run_selftest):
    """Ponto 5."""
    _, run_dir, _ = run_selftest
    decisao = json.loads((run_dir / "codex_round_001.json").read_text(encoding="utf-8"))
    rodada_2 = json.loads((run_dir / "claude_round_002.json").read_text(encoding="utf-8"))
    assert decisao["decision"]["next_prompt"] in rodada_2["prompt"]


def test_todos_os_artefatos_de_estado_existem(run_selftest):
    _, run_dir, _ = run_selftest
    for nome in ("task.json", "state.json", "final_result.json",
                 "claude_round_001.json", "gate_round_001.json", "codex_round_001.json",
                 "claude_round_002.json", "gate_round_002.json", "codex_round_002.json"):
        assert (run_dir / nome).exists(), f"faltou {nome}"


def test_resumo_markdown_foi_escrito(run_selftest):
    _, _, summary = run_selftest
    texto = summary.read_text(encoding="utf-8")
    assert "READY_FOR_HUMAN_REVIEW" in texto
    assert "claude-opus-5" in texto
    # O teto do sistema esta' dito em voz alta no resumo.
    assert "READY_FOR_HUMAN_REVIEW`" in texto or "humano" in texto


def test_nenhum_segredo_nos_artefatos(run_selftest):
    """Ponto 14, no caminho real de arquivos."""
    from ai_team.redact import contains_secret
    _, run_dir, summary = run_selftest
    for arquivo in list(run_dir.glob("*.json")) + [summary]:
        assert not contains_secret(arquivo.read_text(encoding="utf-8")), arquivo.name


def test_recursao_e_barrada(tmp_path):
    """Uma run do AI Team nunca pode disparar outra run dentro de si."""
    import os
    env = dict(os.environ, AI_TEAM_RUN_ACTIVE="1")
    proc = subprocess.run(
        [sys.executable, "-m", "ai_team", "--task", "x", "--mode", "selftest",
         "--no-branch", "--runs-dir", str(tmp_path)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120, env=env)
    assert proc.returncode == 2
    assert "Recursao abortada" in proc.stderr


def test_o_solver_nao_foi_tocado(run_selftest):
    """Secao 22: esta tarefa e' infraestrutura, nao mexe no motor."""
    proc = subprocess.run(["git", "status", "--porcelain", "Script.py", "nuvem/"],
                          cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert proc.stdout.strip() == ""
