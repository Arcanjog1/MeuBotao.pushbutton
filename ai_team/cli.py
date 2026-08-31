"""Entrada do orquestrador: `python -m ai_team`.

Chamado pelo workflow do GitHub Actions com os inputs da UI. Nao tem
estado proprio - tudo vive em `.ai-team/runs/<run-id>/`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from . import repo
from .agents import ClaudeAgent, CodexAgent, SubprocessExecutor
from .config import Config, ConfigError, load_config
from .loop import Orchestrator, build_final_result
from .redact import redact
from .routing import route_agent, route_from_class
from .selftest import ScenarioExecutor, ScenarioStep, claude_stdout, codex_stdout
from .state import RUNS_DIR, create_run, slugify, utcnow

MODES = ("diagnose", "implement", "review", "benchmark", "full", "selftest")

#: Marca uma run em andamento no processo, para barrar recursao.
RUN_ACTIVE_ENV = "AI_TEAM_RUN_ACTIVE"


def build_selftest_executor() -> ScenarioExecutor:
    """Cenario padrao do `--mode selftest`: 2 rodadas e aprovacao.

    A rodada 1 volta PARTIAL e o revisor escala para `deep`
    (opus/high); a rodada 2 conclui e o revisor aprova. Serve para provar,
    num runner limpo e sem segredo nenhum, que o loop encadeia sozinho e
    que o roteamento troca modelo e raciocinio de verdade.
    """
    return ScenarioExecutor(steps=[
        ScenarioStep("claude", claude_stdout(
            "rodada 1 sintetica: alvo de fixture inspecionado", status="PARTIAL")),
        ScenarioStep("codex", codex_stdout(
            "CONTINUE", next_model="claude-opus-5", next_reasoning="high",
            next_prompt="Rodada 2 sintetica: concluir o alvo de fixture.",
            routing_reason="restou analise de causa raiz -> classe deep")),
        ScenarioStep("claude", claude_stdout(
            "rodada 2 sintetica: alvo de fixture concluido", status="DONE")),
        ScenarioStep("codex", codex_stdout(
            "APPROVED", routing_reason="tarefa concluida, nada a rotear",
            why="fixture concluida e gate verde")),
    ])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-team",
        description="Orquestrador deterministico Claude <-> Codex (AI Team Cloud).",
    )
    parser.add_argument("--task", required=True, help="Descricao da tarefa.")
    parser.add_argument("--mode", default="full", choices=MODES)
    parser.add_argument("--max-rounds", type=int, default=None,
                        help="Default vem de config.yaml; o teto e' max_rounds_ceiling.")
    parser.add_argument("--preferred-model", default="",
                        help="Modelo do Claude na rodada 1 (o Codex pode mudar depois).")
    parser.add_argument("--preferred-reasoning", default="",
                        help="Nivel de raciocinio na rodada 1.")
    parser.add_argument("--branch", default="", help="Nome da branch; default: ai/<slug>.")
    parser.add_argument("--base-branch", default="", help="Branch base; default: config.")
    parser.add_argument("--config", default="", help="Caminho alternativo de config.yaml.")
    parser.add_argument("--runs-dir", default=str(RUNS_DIR))
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--no-branch", action="store_true",
                        help="Nao criar/trocar de branch (usado pelo selftest).")
    parser.add_argument("--summary-file", default="",
                        help="Escreve um resumo markdown (GITHUB_STEP_SUMMARY).")
    parser.add_argument("--gate-command", default="",
                        help='Substitui o comando do gate pytest, como lista JSON '
                             '(ex.: \'["python3","-m","pytest","tests/x.py","-q"]\'). '
                             "Usado pelo teste ponta a ponta para nao rodar a suite "
                             "inteira dentro de si mesma. JSON evita que argparse "
                             "confunda um `-m` do comando com uma flag propria.")
    return parser


def resolve_max_rounds(cfg: Config, requested: int | None) -> tuple[int, str]:
    """Aplica o teto absoluto. A UI nunca consegue passar do ceiling."""
    if requested is None or requested <= 0:
        return cfg.default_max_rounds, ""
    ceiling = cfg.max_rounds_ceiling
    if requested > ceiling:
        return ceiling, f"max_rounds {requested} acima do teto {ceiling} -> usando {ceiling}"
    return requested, ""


def write_summary(path: str, final: dict) -> None:
    """Resumo markdown para o step summary do GitHub. Ja' redigido."""
    gate = final.get("gate") or {}
    lines = [
        f"## AI Team - `{final.get('status')}`",
        "",
        f"- **Tarefa:** {final.get('task')}",
        f"- **Modo:** `{final.get('mode')}`  |  **Branch:** `{final.get('branch')}`",
        f"- **Rodadas:** {final.get('rounds_used')}/{final.get('max_rounds')}",
        f"- **Gate:** `{gate.get('status')}` - {gate.get('summary', '')}",
        f"- **Custo (Claude):** US$ {final.get('total_cost_usd', 0)}",
        f"- **Chamadas:** claude={final.get('claude_calls')} codex={final.get('codex_calls')}",
        f"- **DO_NOT_MERGE:** {final.get('do_not_merge')}",
        "",
        f"**Resumo:** {final.get('summary', '')}",
        "",
    ]
    rounds = final.get("rounds") or []
    if rounds:
        lines += ["### Rodadas", "",
                  "| # | modelo | raciocinio | gate | veredito | motivo do roteamento |",
                  "|---|---|---|---|---|---|"]
        for record in rounds:
            claude = record.get("claude", {})
            codex = record.get("codex", {})
            gate_r = record.get("gate", {})
            lines.append(
                f"| {record.get('round')} | `{claude.get('model')}` | "
                f"`{claude.get('reasoning')}` | {gate_r.get('status', '-')} | "
                f"{codex.get('verdict', '-')} | "
                f"{str(codex.get('routing_reason', ''))[:90]} |"
            )
        lines.append("")
    if final.get("human_question"):
        lines += ["### Precisa de decisao humana", "", str(final["human_question"]), ""]
    if final.get("revit_capture_request"):
        lines += ["### Precisa de captura no Revit", ""]
        lines += [f"- {item}" for item in final["revit_capture_request"]]
        lines.append("")
    lines += ["", "> Merge em `main` continua sendo humano. O teto do sistema e' "
              "`READY_FOR_HUMAN_REVIEW`."]
    Path(path).write_text(redact("\n".join(lines)), encoding="utf-8")


#: Status que o workflow deve tratar como falha (exit != 0).
FAILURE_STATUSES = ("FAILED", "ERROR", "TIMEOUT")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        cfg = load_config(args.config or None)
    except (ConfigError, OSError) as exc:
        print(f"ERRO de configuracao: {exc}", file=sys.stderr)
        return 2

    # Uma run do orquestrador roda a suite de testes; se a suite disparasse
    # outra run, a recursao nao teria fim. A guarda e' estrutural.
    if os.environ.get(RUN_ACTIVE_ENV):
        print(f"ERRO: ja' existe uma run do AI Team ativa neste processo "
              f"({RUN_ACTIVE_ENV} definido). Recursao abortada.", file=sys.stderr)
        return 2
    os.environ[RUN_ACTIVE_ENV] = "1"

    if args.gate_command:
        try:
            comando = json.loads(args.gate_command)
        except json.JSONDecodeError as exc:
            print(f"ERRO: --gate-command nao e' JSON valido: {exc}", file=sys.stderr)
            return 2
        if not isinstance(comando, list) or not all(isinstance(c, str) for c in comando):
            print("ERRO: --gate-command deve ser uma lista JSON de strings",
                  file=sys.stderr)
            return 2
        pytest_gate = cfg.gates.get("pytest")
        if isinstance(pytest_gate, dict):
            pytest_gate["command"] = comando

    max_rounds, clamp_note = resolve_max_rounds(cfg, args.max_rounds)
    state = create_run(args.task, args.mode, max_rounds, root=args.runs_dir)
    if clamp_note:
        state.note(clamp_note)

    base_branch = args.base_branch or str(cfg.git.get("base_branch", "main"))
    state.base_sha = repo.head_sha(args.cwd)
    snapshot_main = repo.rev_parse(base_branch, args.cwd)

    # Branch propria por tarefa (secao 10 do pedido).
    if not args.no_branch:
        default_branch = repo.branch_name(
            str(cfg.git.get("branch_prefix", "ai/")), slugify(args.task))
        if args.branch:
            safe, resultado = repo.sanitize_branch_name(args.branch)
            if safe:
                branch = resultado
            else:
                # --branch veio do input `branch_name` da UI: nunca cru no
                # git. Invalido degrada para a branch gerada, e o desvio
                # fica registrado - mesmo principio de routing.py.
                state.note(f"--branch {args.branch!r} recusado ({resultado}) "
                          f"-> usando {default_branch!r}")
                branch = default_branch
        else:
            branch = default_branch
        ok, message = repo.ensure_branch(branch, base_branch, args.cwd)
        state.note(f"branch: {message}")
        if not ok:
            state.status = "ERROR"
            state.save()
            print(f"ERRO ao preparar a branch: {message}", file=sys.stderr)
            return 2
        state.branch = branch
    else:
        state.branch = repo.current_branch(args.cwd)
    state.save()

    # Rodada 1: preferencia da UI, validada pela whitelist. O Codex pode
    # mudar a partir da rodada 2.
    if args.preferred_model or args.preferred_reasoning:
        routed = route_agent(cfg.claude, args.preferred_model or None,
                             args.preferred_reasoning or None)
        for override in routed.overrides:
            state.note(f"preferencia da UI ajustada -> {override}")
        initial = routed.config
    else:
        initial = route_from_class(cfg, "standard")

    if args.mode == "selftest":
        # Offline, sem API key: exercita o codigo de producao com agentes
        # roteirizados (secao 21 do pedido).
        executor = build_selftest_executor()
        state.note("modo selftest: agentes roteirizados, nenhuma API chamada")
    else:
        executor = SubprocessExecutor()
    orchestrator = Orchestrator(
        cfg=cfg,
        state=state,
        claude=ClaudeAgent(cfg, executor, cwd=args.cwd),
        codex=CodexAgent(cfg, executor, cwd=args.cwd, output_dir=state.dir),
        cwd=args.cwd,
        base_branch=base_branch,
        base_sha_snapshot=snapshot_main,
        deadline=time.monotonic() + cfg.timeout_minutes * 60,
    )

    try:
        outcome = orchestrator.run(initial_config=initial)
    except KeyboardInterrupt:
        state.status = "ERROR"
        state.save()
        print("interrompido", file=sys.stderr)
        return 130

    state.status = outcome.status
    state.finished_at = utcnow()
    state.save()

    final = build_final_result(state, outcome, args.cwd)
    state.write_json("final_result.json", final)

    if args.summary_file:
        write_summary(args.summary_file, final)

    print(json.dumps({
        "status": final["status"],
        "run_id": final["run_id"],
        "branch": final["branch"],
        "rounds_used": final["rounds_used"],
        "gate": (final.get("gate") or {}).get("status"),
        "do_not_merge": final["do_not_merge"],
        "run_dir": str(state.dir),
    }, indent=2, ensure_ascii=False))

    return 1 if final["status"] in FAILURE_STATUSES else 0


if __name__ == "__main__":
    raise SystemExit(main())
