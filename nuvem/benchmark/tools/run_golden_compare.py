# -*- coding: utf-8 -*-
"""CLI do golden benchmark (item 24 do pedido): compara RESULTADO A x
RESULTADO B e imprime/gera JSON + relatorio Markdown.

Zero dependencia nova (item 24) - so' a biblioteca padrao + o que ja
existe em `nuvem/benchmark/*`.

USO 1 - dentro de um projeto existente (`nuvem/benchmark/projects/<id>/`),
comparar o baseline gravado contra a ultima rodada:

    py -3 nuvem/benchmark/tools/run_golden_compare.py \\
        --project torre_easy_lo_r00_tgd \\
        --reference baseline --current score

USO 2 - dois arquivos quaisquer (score.json, baseline.json, result.json,
reference.json, findings.json - o formato e' detectado sozinho):

    py -3 nuvem/benchmark/tools/run_golden_compare.py \\
        --reference-file A/score.json --current-file B/score.json \\
        --reference-project-file A/result.json --current-project-file B/result.json

`--reference-project-file`/`--current-project-file` sao OPCIONAIS: sem
eles, as metricas de BLOCOS por codigo e o diff por parede/fiada/bloco
saem NOT_AVAILABLE (item 26) - o resto (prisma, juncoes, aberturas,
qualidade, criticos) ja funciona so' com score.json.
"""

import argparse
import json
import os
import sys

if __package__ in (None, ""):  # rodando como script solto
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    __package__ = "benchmark.tools"

from .. import runner as benchmark_runner  # noqa: E402
from ..golden import compare as compare_module  # noqa: E402
from ..golden import report_md  # noqa: E402
from ..golden import wall_diff as wall_diff_module  # noqa: E402


PROJECT_ARTIFACT_FILES = {
    "score": "score.json",
    "result": "result.json",
    "baseline": "baseline.json",
    "reference_score": "reference_score.json",
    "scoped_score": "scoped_score.json",
    "scoped_reference_score": "scoped_reference_score.json",
    "reference": "reference.json",
    "findings": "findings.json",
}


def _read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _detect_side(data):
    """Descobre se um JSON e' um `score` (saida de `scoring.score_project`
    / `score.json` / `baseline.json`), um `project` (`result.json`/
    `reference.json`, formato `model.py`) ou uma lista de `findings`."""
    if isinstance(data, list):
        return "findings"
    if isinstance(data, dict):
        if "categories" in data and "project_id" in data:
            return "score"
        if "walls" in data and isinstance(data.get("walls"), list):
            return "project"
    return "unknown"


def _load_generic(path):
    """Carrega um arquivo e classifica sozinho o que ele e' - devolve o
    dict pronto para `compare.compare(...)` (`{"score": ...}` ou
    `{"project": ...}` ou `{"findings": ...}`)."""
    data = _read_json(path)
    kind = _detect_side(data)
    if kind == "unknown":
        raise ValueError(
            "{0}: nao reconheci o formato (nem score.json, nem projeto "
            "model.py, nem lista de findings)".format(path))
    return {kind: data}, kind


def _load_project_artifact(project_id, artifact_name):
    filename = PROJECT_ARTIFACT_FILES.get(artifact_name)
    if filename is None:
        raise ValueError("artefato desconhecido: {0!r} (opcoes: {1})".format(
            artifact_name, sorted(PROJECT_ARTIFACT_FILES)))
    paths = benchmark_runner.project_paths(project_id)
    directory = paths["dir"]
    path = os.path.join(directory, filename)
    if not os.path.isfile(path):
        raise RuntimeError(
            "{0}: projeto '{1}' nao tem {2} - rode o runner.py primeiro "
            "ou aponte outro artefato com --reference/--current.".format(
                path, project_id, filename))
    data = _read_json(path)
    kind = _detect_side(data)
    return {kind: data}, path


def _merge_side(base, extra):
    merged = dict(base or {})
    merged.update(extra or {})
    return merged


def build_argparser():
    parser = argparse.ArgumentParser(
        description="Golden benchmark: compara RESULTADO A x RESULTADO B "
                    "(item 9 do CR-BLOCK-GOLDEN-BENCHMARK)")
    parser.add_argument("--project", metavar="PROJECT_ID",
                        help="projeto em nuvem/benchmark/projects/<id>/ - usa "
                             "--reference/--current para escolher os artefatos "
                             "de dentro dele")
    parser.add_argument("--reference", default="baseline",
                        choices=sorted(PROJECT_ARTIFACT_FILES),
                        help="artefato de referencia dentro de --project (default: baseline)")
    parser.add_argument("--current", default="score",
                        choices=sorted(PROJECT_ARTIFACT_FILES),
                        help="artefato atual dentro de --project (default: score)")
    parser.add_argument("--reference-file", metavar="PATH",
                        help="arquivo de referencia (score/project/findings), fora de --project")
    parser.add_argument("--current-file", metavar="PATH",
                        help="arquivo atual (score/project/findings), fora de --project")
    parser.add_argument("--reference-project-file", metavar="PATH",
                        help="result.json/reference.json da referencia - habilita "
                             "metricas de bloco por codigo e diff por parede/fiada")
    parser.add_argument("--current-project-file", metavar="PATH",
                        help="result.json/reference.json do atual")
    parser.add_argument("--reference-findings-file", metavar="PATH",
                        help="findings.json da referencia - habilita quebra L/T/X")
    parser.add_argument("--current-findings-file", metavar="PATH",
                        help="findings.json do atual")
    parser.add_argument("--out-json", metavar="PATH", help="grava a comparacao em JSON")
    parser.add_argument("--out-md", metavar="PATH", help="grava o relatorio em Markdown")
    parser.add_argument("--max-walls", type=int, default=20,
                        help="limite de paredes no relatorio de diff (default: 20)")
    parser.add_argument("--quiet", action="store_true", help="so' o veredito final")
    return parser


def _assemble_side(args, which):
    """`which` = 'reference' ou 'current'. Junta o que vier de --project e
    o que vier de --*-file/--*-project-file/--*-findings-file - os
    arquivos explicitos TEM PRIORIDADE sobre o que --project resolveria."""
    side = {}
    if args.project:
        artifact = getattr(args, which)
        loaded, _path = _load_project_artifact(args.project, artifact)
        side = _merge_side(side, loaded)
        side.setdefault("project_id", args.project)

    generic_file = getattr(args, "{0}_file".format(which))
    if generic_file:
        loaded, _kind = _load_generic(generic_file)
        side = _merge_side(side, loaded)

    project_file = getattr(args, "{0}_project_file".format(which))
    if project_file:
        side["project"] = _read_json(project_file)

    findings_file = getattr(args, "{0}_findings_file".format(which))
    if findings_file:
        side["findings"] = _read_json(findings_file)

    return side


def main(argv=None):
    args = build_argparser().parse_args(argv)
    if not args.project and not (args.reference_file and args.current_file):
        print("informe --project <id>, ou --reference-file e --current-file")
        return 2

    reference = _assemble_side(args, "reference")
    current = _assemble_side(args, "current")

    comparison = compare_module.compare(reference, current)

    wall_diff_result = None
    if reference.get("project") is not None and current.get("project") is not None:
        raw_diff = wall_diff_module.compute_wall_diff(current["project"], reference["project"])
        wall_diff_result = wall_diff_module.wall_diff_report(raw_diff, max_walls=args.max_walls)

    if args.out_json:
        payload = dict(comparison)
        if wall_diff_result is not None:
            payload["wall_diff"] = wall_diff_result
        with open(args.out_json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=1)
        print("JSON gravado em {0}".format(args.out_json))

    report_text = report_md.full_report(comparison, wall_diff_result,
                                        title=comparison.get("project_id"))
    if args.out_md:
        with open(args.out_md, "w", encoding="utf-8") as handle:
            handle.write(report_text)
        print("Markdown gravado em {0}".format(args.out_md))

    if args.quiet:
        print("{0}: {1}".format(comparison.get("project_id"), comparison.get("verdict")))
    else:
        print(report_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
