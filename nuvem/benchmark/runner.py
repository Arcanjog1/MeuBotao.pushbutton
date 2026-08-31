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
        # Etapa 2A: FASE A do pipeline de Wall Modeling (ver
        # `wall_modeling_bridge.py`/`extract/wall_modeling_snapshot.py`) -
        # `input_real.json` e' o problema (linhas do CAD por Layer, aberturas,
        # setup_frozen); `wall_modeling_snapshot.json` e' a saida, ainda
        # ANTES do solver de blocos.
        "input_real": os.path.join(directory, "input_real.json"),
        "wall_modeling_snapshot": os.path.join(directory, "wall_modeling_snapshot.json"),
        # Etapa 2B.1: a regiao onde EXISTE gabarito humano. Derivada do
        # reference, aplicada SO' depois do solver (ver `evaluation_scope.py`).
        "evaluation_scope": os.path.join(directory, "evaluation_scope.json"),
        "scoped_score": os.path.join(directory, "scoped_score.json"),
        "scoped_comparison": os.path.join(directory, "scoped_comparison.json"),
        "scope_summary": os.path.join(directory, "scope_summary.json"),
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


def run_wall_modeling_only(project_id, write_files=True):
    """FASE A isolada (Etapa 2A): `input_real.json` -> `wall_modeling_bridge`
    -> `wall_modeling_snapshot.json`. NAO roda o solver de blocos - e' o
    modo para medir/depurar so' a etapa de eixos/encontros/aberturas, sem
    esperar o pipeline inteiro."""
    from . import wall_modeling_bridge
    from .extract import wall_modeling_snapshot

    paths = project_paths(project_id)
    input_real = _read_json(paths["input_real"])
    if input_real is None:
        raise RuntimeError(
            "projeto '{0}' nao tem input_real.json (ver "
            "benchmark/README.md, secao Wall Modeling).".format(project_id)
        )
    bridge_result = wall_modeling_bridge.run_wall_modeling(input_real)
    snapshot = wall_modeling_snapshot.build_snapshot(bridge_result, project_id)
    if write_files:
        wall_modeling_snapshot.save(snapshot, paths["wall_modeling_snapshot"])

    # FASE B (Etapa 2B.1): snapshot + catalogo -> input.json do solver. So'
    # acontece quando `input_real.json` traz catalogo PROPRIO - o benchmark
    # nao cai no catalogo do `reference.json`, que seria a solucao humana
    # vazando para dentro da entrada.
    catalog = input_real.get("catalog")
    if catalog and write_files:
        from .extract import input_from_snapshot

        snapshot_for_input = dict(snapshot)
        settings = dict(snapshot_for_input.get("settings") or {})
        if settings.get("course_step_cm") is None:
            # A FASE A decide GEOMETRIA de parede, nunca fiada - o passo vem
            # do `setup_frozen`, medido no projeto, nunca de um default.
            settings["course_step_cm"] = (
                input_real.get("setup_frozen", {}).get("course_step_cm"))
        snapshot_for_input["settings"] = settings

        input_project = input_from_snapshot.build_input(
            snapshot_for_input, catalog, project_id,
            catalog_source=input_real.get("metadata", {}).get("catalog_source"))
        input_project["source_document"] = input_real.get("source_document")
        input_project["metadata"]["pair"] = input_real.get("metadata", {}).get("pair")
        model.save(input_project, paths["input"])

    return snapshot


def run_scoped_evaluation(project_id, write_files=True):
    """Metrica SCOPED (Etapa 2B.1): compara o resultado JA PRONTO do solver
    contra o gabarito, considerando so' a regiao onde existe gabarito.

    NAO roda o solver e NAO toca no `input.json` - de proposito. O escopo e'
    derivado do reference, e derivar entrada a partir do gabarito vazaria a
    solucao humana para dentro da execucao (ver `evaluation_scope.py`). Le'
    o `result.json` da rodada FULL e recorta DEPOIS.

    A rodada FULL continua sendo o resultado oficial do solver; as paredes de
    fora do escopo aparecem no resumo, apenas nao sao chamadas de erro."""
    from . import evaluation_scope as scope_module

    paths = project_paths(project_id)
    result_project = _read_json(paths["result"])
    reference = _read_json(paths["reference"])
    if result_project is None or reference is None:
        raise RuntimeError(
            "projeto '{0}' precisa de result.json (rode --run antes) e "
            "reference.json para a metrica SCOPED.".format(project_id))

    scope = _read_json(paths["evaluation_scope"])
    if scope is None:
        scope = scope_module.build_scope(reference)
        if write_files:
            scope_module.save(scope, paths["evaluation_scope"])

    summary = scope_module.summarize(scope, result_project, reference)
    classification = summary.pop("classification")
    reference_class = scope_module.classify_walls(scope, reference)

    scoped_result = scope_module.scoped_project(result_project, classification)
    scoped_reference = scope_module.scoped_project(reference, reference_class)

    matching = matcher.match_walls(scoped_result, scoped_reference)
    summary["matched_inside_scope"] = len(matching["pairs"])
    summary["solver_only_inside_scope"] = (
        summary["walls_inside_evaluation_scope"] - len(matching["pairs"]))
    summary["reference_only_inside_scope"] = (
        len(scoped_reference["walls"]) - len(matching["pairs"]))

    findings, score, comparison = evaluate_project(scoped_result, scoped_reference)
    score["evaluation_scope"] = summary
    score["is_scoped_evaluation"] = True

    # Piso de ruido DENTRO do mesmo recorte - sem isso a coluna do humano
    # contaria paredes que o solver nem foi avaliado em.
    reference_findings, reference_errors = validators.run_all(scoped_reference, {})
    reference_score = scoring.score_project(
        scoped_reference, reference_findings, reference_errors)
    reference_score["is_reference_calibration"] = True
    reference_score["is_scoped_evaluation"] = True

    if write_files:
        _write_json(paths["scoped_score"], score)
        _write_json(paths["scope_summary"], summary)
        if comparison is not None:
            _write_json(paths["scoped_comparison"], comparison)
        _write_json(os.path.join(paths["dir"], "scoped_reference_score.json"),
                    reference_score)
        text = report_module.full_report(score, findings, comparison, None,
                                         reference_score)
        if not os.path.isdir(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)
        with open(os.path.join(REPORTS_DIR, "{0}_scoped.txt".format(project_id)),
                  "w", encoding="utf-8") as handle:
            handle.write(text)

    return {
        "project_id": project_id,
        "scope": scope,
        "summary": summary,
        "score": score,
        "reference_score": reference_score,
        "comparison": comparison,
        "findings": findings,
    }


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
    parser.add_argument("--wall-modeling-only", action="store_true",
                        help="roda so' a FASE A (input_real.json -> wall_modeling_snapshot.json), sem o solver")
    parser.add_argument("--scoped", action="store_true",
                        help="metrica SCOPED: compara o result.json ja pronto contra o "
                             "gabarito so' na regiao com gabarito humano (evaluation_scope)")
    args = parser.parse_args(argv)

    if args.scoped:
        if not (args.run or args.all):
            print("--scoped precisa de --run <project_id> ou --all")
            return 1
        for project_id in (list_projects() if args.all else [args.run]):
            try:
                outcome = run_scoped_evaluation(project_id)
            except RuntimeError as exc:
                print("{0}: {1}".format(project_id, exc))
                continue
            summary = outcome["summary"]
            score = outcome["score"]
            print("{0} [SCOPED]: {1:.1f}% | criticos {2} | achados n1 {3}".format(
                project_id, (score.get("success_rate") or 0.0) * 100.0,
                score.get("critical_errors"), score.get("findings_level_1")))
            for key in ("walls_total_solver", "walls_inside_evaluation_scope",
                        "walls_outside_evaluation_scope", "reference_walls",
                        "reference_walls_inside_scope", "matched_inside_scope",
                        "solver_only_inside_scope", "reference_only_inside_scope"):
                print("   {0:<34} {1}".format(key, summary[key]))
        return 0

    if args.wall_modeling_only:
        if not (args.run or args.all):
            print("--wall-modeling-only precisa de --run <project_id> ou --all")
            return 1
        targets = list_projects() if args.all else [args.run]
        for project_id in targets:
            try:
                snapshot = run_wall_modeling_only(project_id)
            except RuntimeError as exc:
                print("{0}: {1}".format(project_id, exc))
                continue
            print("{0}: {1} parede(s), {2} no(s), {3} linha(s) nao usada(s)".format(
                project_id, len(snapshot["walls"]), len(snapshot["nodes"]),
                len(snapshot["unused_lines"])))
        return 0

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
