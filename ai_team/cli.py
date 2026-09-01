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

#: Marcador pytest (registrado em pytest.ini) para qualquer teste que
#: spawna `python -m ai_team` como subprocesso. O gate escopado do
#: selftest (`_scope_pytest_gate_for_selftest`) exclui este marcador -
#: sem isso, o gate do proprio `--mode selftest` colecionaria esses
#: testes e tentaria iniciar outra run do AI Team dentro de si mesma.
AI_TEAM_E2E_MARKER = "ai_team_e2e"


def _allow_protected_head(mode: str, no_branch: bool) -> bool:
    """Unica condicao que libera HEAD em branch protegida no gate.

    So' verdadeiro quando as DUAS coisas valem ao mesmo tempo:
    `mode == "selftest"` E `no_branch` (o `--no-branch` interno usado pelo
    workflow para o selftest). Nenhuma delas sozinha libera nada, e nenhuma
    vem de um input que o usuario controle diretamente para os modos reais
    (diagnose/implement/review/benchmark/full sempre usam branch propria).
    """
    return mode == "selftest" and no_branch


def _scope_pytest_gate_for_selftest(cfg: Config) -> str:
    """Escopa o gate pytest do MODO selftest para nao recursar em si mesmo.

    O `--mode selftest` roda 100% offline (agentes roteirizados), mas o
    gate dele continua rodando a suite pytest de verdade - e' isso que
    prova que o encanamento (roteamento, gate, estado, parada) funciona de
    ponta a ponta. O problema: a propria suite contem testes marcados
    `AI_TEAM_E2E_MARKER` que spawnam `python -m ai_team` como subprocesso
    para se testar. Rodar esses testes DENTRO do gate de uma run que ja'
    esta' com `AI_TEAM_RUN_ACTIVE=1` faria cada um deles tentar iniciar
    outra run - a guarda de recursao (corretamente) aborta, e o teste
    reportaria falha, derrubando o gate por um motivo que nao e' uma
    regressao real.

    A correcao e' escopar por MARCADOR pytest (`-m "... and not
    ai_team_e2e"`), nao por nome de arquivo: qualquer teste futuro que
    tambem spawne `python -m ai_team` so' precisa herdar o marcador para
    ficar automaticamente fora do proprio gate do selftest, sem precisar
    tocar nesta funcao de novo.

    So' mexe na config quando o usuario NAO passou `--gate-command` (isso
    continua tendo prioridade absoluta - e' o que o teste ponta a ponta
    usa para escopar ainda mais, para `tests/aiteam/test_routing.py`
    isolado). Devolve uma nota para o log da run, ou "" se nao mexeu em
    nada.
    """
    pytest_gate = cfg.gates.get("pytest")
    if not isinstance(pytest_gate, dict) or not pytest_gate.get("enabled"):
        return ""
    command = [str(c) for c in (pytest_gate.get("command") or [])]
    if not command:
        return ""

    marker_expr = f"not {AI_TEAM_E2E_MARKER}"
    # A marcacao `-m` do PYTEST (o filtro de markers) nao e' o primeiro
    # `-m` do comando: `python3 -m pytest ... -m "not slow"` tem DOIS, e o
    # primeiro e' o `-m modulo` do proprio interpretador Python. Por isso
    # procuramos o `-m` que vem DEPOIS do token `pytest`, nunca o primeiro
    # que aparecer cru na lista.
    scoped = list(command)
    try:
        pytest_idx = scoped.index("pytest")
    except ValueError:
        pytest_idx = -1
    marker_flag_idx = next(
        (i for i in range(pytest_idx + 1, len(scoped)) if scoped[i] == "-m"), None)
    if marker_flag_idx is not None and marker_flag_idx + 1 < len(scoped):
        scoped[marker_flag_idx + 1] = f"({scoped[marker_flag_idx + 1]}) and {marker_expr}"
    else:
        scoped += ["-m", marker_expr]

    pytest_gate["command"] = scoped
    return (f"mode=selftest: gate pytest escopado automaticamente para "
            f"-m \"{marker_expr}\" (evita recursao do proprio AI Team "
            f"dentro do seu gate)")


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
    is_selftest = final.get("mode") == "selftest"
    if is_selftest:
        # Secao 23 do pedido: nunca apresentar o custo sintetico dos
        # agentes roteirizados como se fosse cobranca real de API.
        custo_linha = (
            f"- **Custo API real:** US$ {final.get('api_cost_usd', 0.0)} (selftest offline) "
            f"| custo simulado (fixture): US$ {final.get('simulated_cost_usd', 0)}"
        )
        chamadas_linha = (
            f"- **Chamadas (SIMULATED INVOCATIONS, nenhuma API real):** "
            f"claude={final.get('claude_calls')} codex={final.get('codex_calls')}"
        )
    else:
        custo_linha = f"- **Custo (Claude):** US$ {final.get('total_cost_usd', 0)}"
        chamadas_linha = (
            f"- **Chamadas:** claude={final.get('claude_calls')} "
            f"codex={final.get('codex_calls')}"
        )
    lines = [
        f"## AI Team - `{final.get('status')}`",
        "",
        f"- **Tarefa:** {final.get('task')}",
        f"- **Modo:** `{final.get('mode')}`  |  **Branch:** `{final.get('branch')}`",
        f"- **Rodadas:** {final.get('rounds_used')}/{final.get('max_rounds')}",
        f"- **Gate:** `{gate.get('status')}` - {gate.get('summary', '')}",
        custo_linha,
        chamadas_linha,
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

    gate_scope_note = ""
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
    elif args.mode == "selftest":
        # Automatico: a UI/workflow nao precisa (nem deve) passar
        # --gate-command para o selftest funcionar. So' entra aqui quando
        # o usuario nao escolheu um gate-command proprio.
        gate_scope_note = _scope_pytest_gate_for_selftest(cfg)

    max_rounds, clamp_note = resolve_max_rounds(cfg, args.max_rounds)
    state = create_run(args.task, args.mode, max_rounds, root=args.runs_dir)
    if clamp_note:
        state.note(clamp_note)
    if gate_scope_note:
        state.note(gate_scope_note)

    base_branch = args.base_branch or str(cfg.git.get("base_branch", "main"))
    state.base_sha = repo.head_sha(args.cwd)
    snapshot_main = repo.rev_parse(base_branch, args.cwd)
    # Snapshot da working tree ANTES da run: o invariante do selftest
    # compara contra ISTO (nao contra "vazio"), para nao confundir
    # alteracoes locais preexistentes (fora do selftest) com algo que a
    # run produziu.
    dirty_snapshot = repo.git(["status", "--porcelain"], args.cwd)

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
        allow_protected_head=_allow_protected_head(args.mode, args.no_branch),
        dirty_before=dirty_snapshot,
        head_sha_before=state.base_sha,
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
