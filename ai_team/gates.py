"""Gate deterministico - o JUIZ FINAL tecnico (secao 7 do pedido).

Tres niveis:

    Claude  = executor          (opiniao)
    Codex   = reviewer/router   (opiniao)
    GATE    = juiz tecnico      (FATO)   <- vence os dois

O caso citado no pedido:

    Claude = OK, Codex = APPROVED, mas openings 91/91 -> 89/91
    => FAILED / DO_NOT_MERGE

E' exatamente o que `MetricsCheck` implementa: uma regressao numerica
contra a baseline reprova, independentemente do que as IAs acharem.

Um check pode terminar em tres estados:
    PASS    - verificado e aprovado
    FAIL    - verificado e reprovado
    SKIPPED - nao havia como verificar (ex.: sem arquivo de metricas).

SKIPPED nunca vira PASS: o gate nao inventa numero que nao mediu.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Config
from .redact import redact


@dataclass
class CheckResult:
    name: str
    status: str            # PASS | FAIL | SKIPPED
    hard: bool
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "hard": self.hard,
                "detail": redact(self.detail), "data": self.data}


@dataclass
class GateResult:
    checks: list[CheckResult] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def hard_failures(self) -> list[CheckResult]:
        return [c for c in self.checks if c.hard and c.status == "FAIL"]

    @property
    def passed(self) -> bool:
        """Verde = nenhum check HARD reprovado."""
        return not self.hard_failures

    @property
    def status(self) -> str:
        if self.hard_failures:
            return "FAIL"
        if any(c.status == "FAIL" for c in self.checks):
            return "FAIL_SOFT"
        if all(c.status == "SKIPPED" for c in self.checks) and self.checks:
            return "SKIPPED"
        return "PASS"

    def summary(self) -> str:
        if self.passed:
            parts = [f"{c.name}={c.status}" for c in self.checks]
            return "GATE PASS: " + ", ".join(parts) if parts else "GATE PASS (nenhum check)"
        return "GATE FAIL: " + "; ".join(f"{c.name}: {c.detail}" for c in self.hard_failures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "hard_failures": [c.name for c in self.hard_failures],
            "checks": [c.to_dict() for c in self.checks],
            "summary": self.summary(),
        }


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def run_pytest_check(spec: dict[str, Any], cwd: str = ".") -> CheckResult:
    """Roda a suite do projeto. Vermelho = HARD FAIL."""
    hard = bool(spec.get("hard", True))
    command = [str(c) for c in (spec.get("command") or [])]
    if not command:
        return CheckResult("pytest", "SKIPPED", hard, "sem comando configurado")

    try:
        proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                              timeout=int(spec.get("timeout_seconds", 1800)))
    except FileNotFoundError:
        return CheckResult("pytest", "FAIL", hard, f"executavel ausente: {command[0]!r}")
    except subprocess.TimeoutExpired:
        return CheckResult("pytest", "FAIL", hard, "timeout na suite de testes")

    tail = (proc.stdout or "")[-3000:] + (proc.stderr or "")[-1500:]
    if proc.returncode == 0:
        return CheckResult("pytest", "PASS", hard, f"exit=0 :: {tail.strip()[-300:]}")
    # exit 5 = "nenhum teste coletado". Nao e' regressao, mas tambem nao e'
    # prova de nada: fica SKIPPED em vez de PASS.
    if proc.returncode == 5:
        return CheckResult("pytest", "SKIPPED", hard, "nenhum teste coletado")
    return CheckResult("pytest", "FAIL", hard,
                       f"exit={proc.returncode} :: {tail.strip()[-1500:]}")


def compare_metrics(current: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    """Compara metricas com a baseline. Devolve a lista de regressoes.

    Formato da baseline, por metrica:

        {"openings": {"value": 91, "direction": "higher_is_better", "tolerance": 0}}

    `direction`: `higher_is_better` | `lower_is_better` | `exact`.
    `tolerance`: folga absoluta aceita antes de considerar regressao.
    """
    regressions: list[str] = []
    for name, spec in baseline.items():
        if not isinstance(spec, dict) or "value" not in spec:
            continue
        if name not in current:
            regressions.append(f"{name}: ausente nas metricas atuais (baseline={spec['value']})")
            continue
        try:
            now = float(current[name])
            was = float(spec["value"])
        except (TypeError, ValueError):
            regressions.append(f"{name}: valor nao numerico (atual={current[name]!r})")
            continue

        direction = str(spec.get("direction", "higher_is_better"))
        tol = float(spec.get("tolerance", 0))

        if direction == "higher_is_better" and now < was - tol:
            regressions.append(f"{name}: {was:g} -> {now:g} (piorou)")
        elif direction == "lower_is_better" and now > was + tol:
            regressions.append(f"{name}: {was:g} -> {now:g} (piorou)")
        elif direction == "exact" and abs(now - was) > tol:
            regressions.append(f"{name}: {was:g} -> {now:g} (deveria ser exato)")
    return regressions


def run_metrics_check(spec: dict[str, Any], cwd: str = ".") -> CheckResult:
    """Compara metricas com a baseline versionada."""
    hard = bool(spec.get("hard", True))
    metrics_path = Path(cwd) / str(spec.get("metrics_file", ""))
    baseline_path = Path(cwd) / str(spec.get("baseline_file", ""))

    if not baseline_path.exists():
        return CheckResult("metrics", "SKIPPED", hard,
                           f"sem baseline em {baseline_path} - nada a comparar")
    if not metrics_path.exists():
        return CheckResult("metrics", "SKIPPED", hard,
                           f"a rodada nao produziu {metrics_path} - metricas nao medidas")

    try:
        current = json.loads(metrics_path.read_text(encoding="utf-8"))
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return CheckResult("metrics", "FAIL", hard, f"metricas ilegiveis: {exc}")

    if not isinstance(current, dict) or not isinstance(baseline, dict):
        return CheckResult("metrics", "FAIL", hard, "metricas ou baseline nao sao objetos JSON")

    regressions = compare_metrics(current, baseline)
    data = {"current": current, "baseline": baseline, "regressions": regressions}
    if regressions:
        return CheckResult("metrics", "FAIL", hard,
                           "regressao numerica: " + "; ".join(regressions), data)
    return CheckResult("metrics", "PASS", hard,
                       f"{len(baseline)} metrica(s) sem regressao", data)


def _git(args: list[str], cwd: str = ".") -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                              text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return (proc.stdout or "").strip() if proc.returncode == 0 else ""


def run_repo_invariants_check(spec: dict[str, Any], cwd: str = ".",
                              expected_branch: str = "",
                              base_sha_before: str = "",
                              allow_protected_head: bool = False,
                              dirty_before: str = "",
                              head_sha_before: str = "") -> CheckResult:
    """Invariantes do repositorio: main intocada e branch correta.

    `allow_protected_head` e' a UNICA excecao aceita para HEAD estar numa
    branch protegida, e so' o orquestrador decide quando ela vale - nunca a
    config nem input de usuario (ver `cli.py::_allow_protected_head`). Mesmo
    com a excecao ligada, o resto do invariante continua HARD: nenhum commit
    pode ter sido criado (HEAD nao pode ter se mexido) e a working tree do
    motor tem que continuar exatamente como estava (`dirty_before`) -
    comparamos contra os snapshots de ANTES da run, nao contra "vazio": um
    checkout de desenvolvimento pode ja' ter alteracoes locais legitimas
    (fora do selftest) que nao sao culpa desta run.

    `base_sha_before` e `head_sha_before` sao DELIBERADAMENTE dois campos
    diferentes: `base_sha_before` e' o snapshot da BRANCH PROTEGIDA (ex.:
    `main`), que pode divergir do HEAD atual (o checkout local pode estar
    numa branch de tarefa cujo ref local de `main` esta' desatualizado -
    isso e' normal em dev e NAO e' o commit que o invariante de "nenhum
    commit foi criado" precisa vigiar). `head_sha_before` e' o HEAD de
    verdade no INICIO desta run - e' contra ele, nao contra o snapshot de
    `main`, que comparamos para saber se a run criou um commit.
    """
    hard = bool(spec.get("hard", True))
    protected = [str(b) for b in (spec.get("protected_branches") or ["main"])]
    problems: list[str] = []

    current_branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if current_branch and current_branch in protected and not allow_protected_head:
        problems.append(f"HEAD esta' na branch protegida {current_branch!r}")
    if expected_branch and current_branch and current_branch != expected_branch:
        problems.append(f"branch esperada {expected_branch!r}, atual {current_branch!r}")

    # A branch base nao pode ter se mexido durante a run.
    if base_sha_before:
        for name in protected:
            now = _git(["rev-parse", name], cwd)
            if now and now != base_sha_before and name == (spec.get("_base_branch") or "main"):
                problems.append(f"{name} mudou de {base_sha_before[:8]} para {now[:8]}")

    # Selftest sem branch: nada deveria ter se mexido no motor. Nem HEAD
    # (nenhum commit deveria ter sido criado), nem a working tree (nenhum
    # agente real rodou, entao nenhuma alteracao NOVA deveria existir).
    if allow_protected_head and head_sha_before:
        head_now = _git(["rev-parse", "HEAD"], cwd)
        if head_now and head_now != head_sha_before:
            problems.append(
                f"HEAD mudou de {head_sha_before[:8]} para {head_now[:8]} "
                "durante o selftest (nenhum commit deveria ter sido criado)"
            )
        # `.strip()` normaliza os DOIS lados antes de comparar: `_git()`
        # (interno deste modulo) tira o espaco inicial da PRIMEIRA linha
        # de `git status --porcelain` (o formato usa um espaco antes da
        # letra de status, ex.: " M arquivo"); `repo.git()` (usado por
        # `cli.py` para capturar o snapshot ANTES da run) so' faz
        # `.rstrip()` e preserva esse espaco. Sem normalizar os dois
        # lados do mesmo jeito, a comparacao dava falso-positivo mesmo
        # quando a working tree nao mudou nada.
        dirty_now = _git(["status", "--porcelain"], cwd)
        if dirty_now.strip() != dirty_before.strip():
            problems.append(
                "working tree do motor mudou durante o selftest (nenhuma "
                f"alteracao real deveria ter sido produzida): {dirty_now[:200]!r}"
            )

    data = {"branch": current_branch, "protected": protected,
            "allow_protected_head": allow_protected_head}
    if problems:
        return CheckResult("repo_invariants", "FAIL", hard, "; ".join(problems), data)
    return CheckResult("repo_invariants", "PASS", hard,
                       f"branch={current_branch or '?'}, main intocada", data)


def run_gates(cfg: Config, cwd: str = ".", expected_branch: str = "",
              base_sha_before: str = "", base_branch: str = "main",
              allow_protected_head: bool = False, dirty_before: str = "",
              head_sha_before: str = "") -> GateResult:
    """Roda todos os checks habilitados na config."""
    started = time.monotonic()
    result = GateResult()
    specs = cfg.gates

    pytest_spec = specs.get("pytest") or {}
    if pytest_spec.get("enabled"):
        result.checks.append(run_pytest_check(pytest_spec, cwd))

    invariants_spec = dict(specs.get("repo_invariants") or {})
    if invariants_spec.get("enabled"):
        invariants_spec["_base_branch"] = base_branch
        result.checks.append(
            run_repo_invariants_check(invariants_spec, cwd, expected_branch, base_sha_before,
                                      allow_protected_head=allow_protected_head,
                                      dirty_before=dirty_before,
                                      head_sha_before=head_sha_before)
        )

    metrics_spec = specs.get("metrics") or {}
    if metrics_spec.get("enabled"):
        result.checks.append(run_metrics_check(metrics_spec, cwd))

    result.duration_ms = int((time.monotonic() - started) * 1000)
    return result
