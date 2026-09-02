# -*- coding: utf-8 -*-
"""CLI do CORPUS DE REFERENCIA (itens 17-20 do CR-BLOCK-REFERENCE-CORPUS):
roda a comparacao em UM projeto, ou em TODO O CORPUS, e mostra o resumo
agregado sem esconder regressao critica atras de media (item 19).

Zero dependencia nova - so' biblioteca padrao + `nuvem/benchmark/*`.
NUNCA roda o solver e NUNCA regrava artefato nenhum (item 51): compara
so' o que ja' esta' gravado em disco (por default, `baseline.json` contra
`score.json` de cada projeto - os mesmos dois artefatos que
`tools/run_golden_compare.py --project <id>` usa por default).

USO:

    py -3 nuvem/benchmark/tools/run_reference_corpus.py --project torre_easy_lo_r00_tgd
    py -3 nuvem/benchmark/tools/run_reference_corpus.py --all
    py -3 nuvem/benchmark/tools/run_reference_corpus.py --all --capability CAN_COMPARE_TO_HUMAN
    py -3 nuvem/benchmark/tools/run_reference_corpus.py --all --out-json corpus.json --out-md corpus.md
"""

import argparse
import json
import sys
import os

if __package__ in (None, ""):  # rodando como script solto
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    __package__ = "benchmark.tools"

from ..golden import capabilities as capabilities_module  # noqa: E402
from ..golden import corpus as corpus_module  # noqa: E402
from ..golden import report_md  # noqa: E402
from .run_golden_compare import PROJECT_ARTIFACT_FILES  # noqa: E402


def build_argparser():
    parser = argparse.ArgumentParser(
        description="Reference corpus: roda a comparacao baseline x score "
                    "em um projeto ou em todo o corpus (item 17-20)")
    parser.add_argument("--project", metavar="PROJECT_ID", action="append",
                        help="roda so' este(s) projeto(s) (repita a flag para varios)")
    parser.add_argument("--all", action="store_true", help="roda o corpus inteiro")
    parser.add_argument("--capability", choices=capabilities_module.ALL_CAPABILITIES,
                        help="dentro de --all, roda so' projetos com esta capability")
    parser.add_argument("--reference", default="baseline",
                        choices=sorted(PROJECT_ARTIFACT_FILES),
                        help="artefato de referencia dentro de cada projeto (default: baseline)")
    parser.add_argument("--current", default="score",
                        choices=sorted(PROJECT_ARTIFACT_FILES),
                        help="artefato atual dentro de cada projeto (default: score)")
    parser.add_argument("--out-json", metavar="PATH", help="grava o resultado completo em JSON")
    parser.add_argument("--out-md", metavar="PATH", help="grava o relatorio do corpus em Markdown")
    parser.add_argument("--quiet", action="store_true", help="so' o resumo, sem a matriz")
    return parser


def main(argv=None):
    args = build_argparser().parse_args(argv)
    if not args.project and not args.all:
        print("informe --project <id> (pode repetir) ou --all")
        return 2

    corpus = corpus_module.ReferenceCorpus.load_default()

    if args.project:
        project_ids = list(args.project)
    elif args.capability:
        project_ids = [e["project_id"] for e in corpus.filter_by_capability(args.capability)]
    else:
        project_ids = corpus.list_projects()

    rows = corpus_module.run_corpus(
        corpus, project_ids=project_ids,
        reference_artifact=args.reference, current_artifact=args.current)
    summary = corpus_module.summarize_corpus_run(rows)
    matrix = corpus_module.build_matrix(rows)

    if args.out_json:
        payload = {
            "summary": summary,
            "matrix": matrix,
            "projects": [
                {
                    "project_id": row["project_id"],
                    "comparable": row["comparable"],
                    "reason": row["reason"],
                    "comparison": row["comparison"],
                }
                for row in rows
            ],
        }
        with open(args.out_json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=1)
        print("JSON gravado em {0}".format(args.out_json))

    if args.quiet:
        text = report_md.render_corpus_summary(summary)
    else:
        text = report_md.full_corpus_report(rows, summary, matrix)

    if args.out_md:
        with open(args.out_md, "w", encoding="utf-8") as handle:
            handle.write(text)
        print("Markdown gravado em {0}".format(args.out_md))

    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
