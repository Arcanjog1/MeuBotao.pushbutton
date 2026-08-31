# -*- coding: utf-8 -*-
"""Runner do benchmark - o laco completo do item 1, em um comando.

    input.json -> solver real -> result.json -> validadores -> score
                                             -> comparacao com reference.json
                                             -> relatorio -> baseline/regressao

Uso:

    py -3 nuvem/benchmark/runner.py --list
    py -3 nuvem/benchmark/runner.py --run <project_id>
    py -3 nuvem/benchmark/runner.py --all
    py -3 nuvem/benchmark/runner.py --all --save-baseline
    py -3 nuvem/benchmark/runner.py --all --check     # falha se houver regressao

`--check` e' o modo para CI/pre-commit: sai com codigo 1 se qualquer
projeto regrediu contra o baseline gravado, ou se apareceu erro critico
novo. E' o que garante o item 12 (uma correcao nova nao pode destruir uma
solucao antiga).
"""

import argparse
import datetime
import json
import os
import sys

if __package__ in (None, ""):  # rodando como script solto
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "benchmark"

from . import model  # noqa: E402
from . import report as report_module  # noqa: E402
from . import scoring  # noqa: E402
from . import validators  # noqa: E402
from .comparator import compare_projects as comparator  # noqa: E402
from .comparator import match as matcher  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(HERE, "projects")
REPORTS_DIR = os.path.join(HERE, "reports")


def list_projects():
    if not os.path.isdir(PROJECTS_DIR):
        return []
    names = []
    for name in sorted(os.listdir(PROJECTS_DIR)):
        if os.path.isfile(os.path.join(PROJECTS_DIR, name, "input.json")):
            names.append(name)
    return names


def project_paths(project_id):
    directory = os.path.join(PROJECTS_DIR, project_id)
    return {
        "dir": directory,
        "input": os.path.join(directory, "input.json"),
        "reference": os.path.join(directory, "reference.json"),
        "metadata": os.path.join(directory, "metadata.json"),
        "result": os.path.join(directory, "result.json"),
        "baseline": os.path.join(directory, "baseline.json"),
    }


def _read_json(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)
    return path


def evaluate_project(project, reference=None):
    """Valida + compara UM projeto ja' em memoria. Separado de
    `run_project` de proposito: os testes de regressao chamam isto direto,
    sem tocar em disco nem rodar o solver."""
    context = {}
    comparison = None
    if reference is not None:
        matching = matcher.match_walls(project, reference)
        context = {"reference": reference, "wall_pairs": matching["pairs"]}
    findings, validator_errors = validators.run_all(project, context)
    score = scoring.score_project(project, findings, validator_errors)
    if reference is not None:
        comparison = comparator.compare_projects(project, reference)
        # `pairs` carrega os dicts inteiros das paredes - util em memoria,
        # impossivel de serializar sem duplicar o projeto todo.
        comparison.pop("pairs", None)
    return findings, score, comparison


def calibrate_project(project_id, write_files=True):
    """Roda os validadores no PROPRIO GABARITO e grava o score.

    Isto nao e' curiosidade: o gabarito e' um projeto entregue e aprovado
    por gente, entao todo achado que os validadores apontam nele e' ou
    (a) uma limitacao da reconstrucao geometrica, ou (b) um validador
    exigindo mais do que o escritorio de fato pratica. Nos dois casos e' o
    PISO DE RUIDO daquele validador naquele projeto.

    Sem esse piso, "o solver tem 122 erros de prisma" nao quer dizer nada -
    com ele, da' para dizer "o solver tem 968 contra 122 do projeto
    humano medido pelo MESMO codigo", que e' uma afirmacao verificavel."""
    paths = project_paths(project_id)
    reference = _read_json(paths["reference"])
    if reference is None:
        return None
    findings, validator_errors = validators.run_all(reference, {})
    score = scoring.score_project(reference, findings, validator_errors)
    score["is_reference_calibration"] = True
    if write_files:
        _write_json(os.path.join(paths["dir"], "reference_score.json"), score)
        _write_json(os.path.join(paths["dir"], "reference_findings.json"), findings)
    return score


def run_project(project_id, save_baseline=False, write_files=True):
    """Roda o ciclo inteiro de um projeto. Devolve um dict com score,
    achados, comparacao e delta contra o baseline."""
    from . import solver_bridge
    from .extract import from_solver

    paths = project_paths(project_id)
    input_project = _read_json(paths["input"])
    if input_project is None:
        raise RuntimeError("projeto '{0}' nao tem input.json".format(project_id))

    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(input_project)

    result_project = from_solver.project_from_solver(
        project_id, solve_result, walls_to_create, nodes, openings_per_wall,
        catalog, base_z_ft, num_courses,
        metadata={"generated_at": datetime.datetime.now().isoformat(),
                  "from_input": os.path.basename(paths["input"]),
                  "solver_notes": notes},
    )

    reference = _read_json(paths["reference"])
    findings, score, comparison = evaluate_project(result_project, reference)
    reference_score = _read_json(os.path.join(paths["dir"], "reference_score.json"))
    if reference is not None and reference_score is None:
        reference_score = calibrate_project(project_id, write_files=write_files)

    baseline = _read_json(paths["baseline"])
    delta = scoring.compare_runs(baseline, score) if baseline else None

    if write_files:
        model.save(result_project, paths["result"])
        _write_json(os.path.join(paths["dir"], "findings.json"), findings)
        _write_json(os.path.join(paths["dir"], "score.json"), score)
        if comparison is not None:
            _write_json(os.path.join(paths["dir"], "comparison.json"), comparison)
        text = report_module.full_report(score, findings, comparison, delta,
                                         reference_score)
        if not os.path.isdir(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)
        with open(os.path.join(REPORTS_DIR, "{0}.txt".format(project_id)),
                  "w", encoding="utf-8") as handle:
            handle.write(text)
        if save_baseline:
            _write_json(paths["baseline"], score)

    return {
        "project_id": project_id,
        "result": result_project,
        "findings": findings,
        "score": score,
        "reference_score": reference_score,
        "comparison": comparison,
        "delta": delta,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark da modulacao automatica")
    parser.add_argument("--list", action="store_true", help="lista os projetos")
    parser.add_argument("--run", metavar="PROJECT_ID", help="roda um projeto")
    parser.add_argument("--all", action="store_true", help="roda todos os projetos")
    parser.add_argument("--save-baseline", action="store_true",
                        help="grava o score desta rodada como baseline")
    parser.add_argument("--check", action="store_true",
                        help="sai com codigo 1 se houver regressao ou erro critico")
    parser.add_argument("--quiet", action="store_true", help="so' o resumo")
    parser.add_argument("--calibrate", action="store_true",
                        help="roda os validadores no GABARITO e grava o piso de ruido")
    args = parser.parse_args(argv)

    if args.list or not (args.run or args.all):
        names = list_projects()
        print("projetos em {0}:".format(PROJECTS_DIR))
        for name in names:
            paths = project_paths(name)
            marks = []
            if os.path.isfile(paths["reference"]):
                marks.append("gabarito")
            if os.path.isfile(paths["baseline"]):
                marks.append("baseline")
            print("  {0:<40} {1}".format(name, ", ".join(marks) or "-"))
        if not names:
            print("  (nenhum - ver benchmark/README.md para adicionar)")
        return 0

    targets = list_projects() if args.all else [args.run]
    failures = []
    if args.calibrate:
        for project_id in targets:
            score = calibrate_project(project_id)
            if score is None:
                print("{0}: sem reference.json - nada a calibrar".format(project_id))
                continue
            print(report_module.format_score(score))
            print("")
        return 0
    for project_id in targets:
        outcome = run_project(project_id, save_baseline=args.save_baseline)
        score = outcome["score"]
        if args.quiet:
            print("{0}: {1:.1f}% | criticos {2} | achados n1 {3}".format(
                project_id, 100.0 * score["success_rate"],
                score["critical_errors"], score["findings_level_1"]))
        else:
            print(report_module.full_report(
                score, outcome["findings"], outcome["comparison"], outcome["delta"],
                outcome.get("reference_score")))
            print("")
        if args.check:
            if score.get("blocking"):
                failures.append("{0}: {1} erro(s) critico(s)".format(
                    project_id, score["critical_errors"]))
            delta = outcome["delta"]
            if delta and delta["verdict"] in (scoring.STATUS_REGRESSED,
                                              scoring.STATUS_CRITICAL_REGRESSION):
                failures.append("{0}: {1}".format(project_id, delta["verdict"]))

    if args.check:
        if failures:
            print("")
            print("BENCHMARK REPROVADO:")
            for line in failures:
                print("  - {0}".format(line))
            return 1
        print("")
        print("BENCHMARK OK - sem regressao e sem erro critico.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
