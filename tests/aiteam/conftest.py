"""Fixtures da suite do orquestrador AI Team."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai_team.config import load_config  # noqa: E402
from ai_team.state import create_run  # noqa: E402


@pytest.fixture
def cfg():
    return load_config()


@pytest.fixture
def run_state(tmp_path):
    """Run isolada em tmp_path - nunca escreve em `.ai-team/runs/`."""
    state = create_run("tarefa de teste", "selftest", 3, root=tmp_path / "runs")
    state.branch = "ai/tarefa-de-teste"
    state.base_sha = "0" * 40
    return state
