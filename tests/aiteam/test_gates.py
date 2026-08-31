"""O gate deterministico - o juiz tecnico final (secao 7 do pedido)."""

from __future__ import annotations

import json

from ai_team.gates import (CheckResult, GateResult, compare_metrics,
                           run_metrics_check, run_pytest_check,
                           run_repo_invariants_check)


class TestComparacaoDeMetricas:
    BASELINE = {
        "openings": {"value": 91, "direction": "higher_is_better", "tolerance": 0},
        "critical_errors": {"value": 1205, "direction": "lower_is_better", "tolerance": 0},
        "walls": {"value": 96, "direction": "exact", "tolerance": 0},
    }

    def test_o_caso_do_pedido_openings_91_para_89(self):
        regressoes = compare_metrics(
            {"openings": 89, "critical_errors": 1205, "walls": 96}, self.BASELINE)
        assert regressoes == ["openings: 91 -> 89 (piorou)"]

    def test_sem_regressao_passa(self):
        assert compare_metrics(
            {"openings": 91, "critical_errors": 1100, "walls": 96}, self.BASELINE) == []

    def test_melhora_nao_e_regressao(self):
        assert compare_metrics(
            {"openings": 95, "critical_errors": 900, "walls": 96}, self.BASELINE) == []

    def test_metrica_lower_is_better_piorando(self):
        regressoes = compare_metrics(
            {"openings": 91, "critical_errors": 1400, "walls": 96}, self.BASELINE)
        assert regressoes == ["critical_errors: 1205 -> 1400 (piorou)"]

    def test_metrica_exata_desviando(self):
        regressoes = compare_metrics(
            {"openings": 91, "critical_errors": 1205, "walls": 95}, self.BASELINE)
        assert "walls" in regressoes[0]

    def test_metrica_ausente_e_regressao(self):
        """Sumir com a metrica nao pode ser um jeito de passar no gate."""
        regressoes = compare_metrics({"openings": 91}, self.BASELINE)
        assert len(regressoes) == 2
        assert all("ausente" in r for r in regressoes)

    def test_tolerancia_absorve_ruido(self):
        baseline = {"runtime_s": {"value": 10, "direction": "lower_is_better",
                                  "tolerance": 2}}
        assert compare_metrics({"runtime_s": 11.5}, baseline) == []
        assert compare_metrics({"runtime_s": 13}, baseline) != []


class TestCheckDeMetricas:
    def test_sem_baseline_fica_skipped_nao_pass(self, tmp_path):
        """O gate nunca inventa um numero que nao mediu."""
        result = run_metrics_check(
            {"hard": True, "metrics_file": "m.json", "baseline_file": "b.json"},
            cwd=str(tmp_path))
        assert result.status == "SKIPPED"

    def test_metricas_ausentes_ficam_skipped(self, tmp_path):
        (tmp_path / "b.json").write_text(json.dumps({"x": {"value": 1}}))
        result = run_metrics_check(
            {"hard": True, "metrics_file": "m.json", "baseline_file": "b.json"},
            cwd=str(tmp_path))
        assert result.status == "SKIPPED"

    def test_regressao_reprova(self, tmp_path):
        (tmp_path / "b.json").write_text(json.dumps(
            {"openings": {"value": 91, "direction": "higher_is_better"}}))
        (tmp_path / "m.json").write_text(json.dumps({"openings": 89}))
        result = run_metrics_check(
            {"hard": True, "metrics_file": "m.json", "baseline_file": "b.json"},
            cwd=str(tmp_path))
        assert result.status == "FAIL"
        assert result.hard is True
        assert "91 -> 89" in result.detail


class TestCheckDePytest:
    def test_suite_verde_passa(self, tmp_path):
        result = run_pytest_check(
            {"hard": True, "command": ["python3", "-c", "raise SystemExit(0)"]},
            cwd=str(tmp_path))
        assert result.status == "PASS"

    def test_suite_vermelha_reprova(self, tmp_path):
        result = run_pytest_check(
            {"hard": True, "command": ["python3", "-c", "raise SystemExit(1)"]},
            cwd=str(tmp_path))
        assert result.status == "FAIL"
        assert result.hard is True

    def test_nenhum_teste_coletado_nao_vira_pass(self, tmp_path):
        """exit 5 = nada coletado. Nao e' regressao, mas nao prova nada."""
        result = run_pytest_check(
            {"hard": True, "command": ["python3", "-c", "raise SystemExit(5)"]},
            cwd=str(tmp_path))
        assert result.status == "SKIPPED"

    def test_executavel_ausente_reprova(self, tmp_path):
        result = run_pytest_check(
            {"hard": True, "command": ["binario-que-nao-existe-xyz"]}, cwd=str(tmp_path))
        assert result.status == "FAIL"


class TestInvariantesDoRepositorio:
    def test_reprova_se_head_esta_na_main(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ai_team.gates._git",
                            lambda args, cwd=".": "main" if "--abbrev-ref" in args else "")
        result = run_repo_invariants_check({"hard": True, "protected_branches": ["main"]})
        assert result.status == "FAIL"
        assert "protegida" in result.detail

    def test_reprova_se_a_branch_nao_e_a_esperada(self, monkeypatch):
        monkeypatch.setattr("ai_team.gates._git",
                            lambda args, cwd=".": "outra" if "--abbrev-ref" in args else "")
        result = run_repo_invariants_check(
            {"hard": True, "protected_branches": ["main"]}, expected_branch="ai/tarefa")
        assert result.status == "FAIL"

    def test_reprova_se_a_main_se_moveu(self, monkeypatch):
        def fake_git(args, cwd="."):
            if "--abbrev-ref" in args:
                return "ai/tarefa"
            if args[:1] == ["rev-parse"]:
                return "b" * 40
            return ""
        monkeypatch.setattr("ai_team.gates._git", fake_git)
        result = run_repo_invariants_check(
            {"hard": True, "protected_branches": ["main"], "_base_branch": "main"},
            expected_branch="ai/tarefa", base_sha_before="a" * 40)
        assert result.status == "FAIL"
        assert "mudou" in result.detail


class TestAgregacaoDoGate:
    def test_falha_hard_reprova_o_gate(self):
        gate = GateResult([CheckResult("pytest", "PASS", True),
                           CheckResult("metrics", "FAIL", True, "regressao")])
        assert gate.passed is False
        assert gate.status == "FAIL"

    def test_falha_soft_nao_reprova(self):
        gate = GateResult([CheckResult("pytest", "PASS", True),
                           CheckResult("lint", "FAIL", False, "estilo")])
        assert gate.passed is True
        assert gate.status == "FAIL_SOFT"

    def test_tudo_skipped_nao_e_pass(self):
        gate = GateResult([CheckResult("metrics", "SKIPPED", True)])
        assert gate.status == "SKIPPED"
