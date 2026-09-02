# -*- coding: utf-8 -*-
"""REFERENCE CORPUS (item 14 do CR-BLOCK-REFERENCE-CORPUS): a colecao
versionada de projetos usados para testar o solver, e a execucao AGREGADA
de comparacao sobre ela (itens 17-20).

`ReferenceCorpus` e' so' uma fachada de leitura sobre `manifest.json` - a
classificacao continua sendo 100% de `manifest.py`/`manifest.json` (humana,
nunca inferida aqui). O que este modulo acrescenta e' ORQUESTRACAO:
"rode a comparacao em todo mundo que puder ser comparado, e me diga, sem
esconder nada atras de media, o que melhorou/piorou/nao pode ser
comparado" (item 43: camada de orquestracao/agregacao, nao um motor novo).

NUNCA roda o solver e NUNCA regrava artefato nenhum (item 51) - so' le'
o que ja' esta' gravado em disco (`score.json`, `baseline.json`, etc,
pelos MESMOS nomes que `tools/run_golden_compare.py` ja usa)."""

import os

from .. import runner as benchmark_runner
from . import compare as compare_module
from . import manifest as manifest_module


class ReferenceCorpus(object):
    """Fachada sobre um manifesto carregado. `list_projects`/`get_project`/
    `filter_by_*` (item 14) - nada aqui decide confiabilidade, so' consulta."""

    def __init__(self, manifest_data):
        self._manifest = manifest_data

    @classmethod
    def load_default(cls):
        return cls(manifest_module.load_default())

    @property
    def manifest(self):
        return self._manifest

    def list_projects(self):
        return [e["project_id"] for e in self._manifest.get("projects") or []]

    def all_entries(self):
        return list(self._manifest.get("projects") or [])

    def get_project(self, project_id):
        return manifest_module.get(self._manifest, project_id)

    def filter_by_capability(self, capability):
        return [e for e in self.all_entries()
               if capability in (e.get("capabilities") or [])]

    def filter_by_reference_kind(self, kind):
        return manifest_module.filter_by_reference_kind(self._manifest, kind)

    def filter_by_confidence(self, minimum=None, exact=None):
        return manifest_module.filter_by_confidence(self._manifest, minimum=minimum, exact=exact)

    def reproducible_projects(self):
        return [e for e in self.all_entries() if e.get("reproducible")]

    def human_reference_projects(self):
        return self.filter_by_reference_kind(manifest_module.KIND_HUMAN)

    def golden_projects(self):
        return self.filter_by_confidence(exact=manifest_module.CONFIDENCE_GOLDEN)

    def analysis_only_projects(self):
        return self.filter_by_reference_kind(manifest_module.KIND_ANALYSIS_ONLY)


# ------------------------------------------------------- execucao agregada
NOT_COMPARABLE = "NOT_COMPARABLE"

# "overall" do corpus (item 18/19) - inclui os 4 vereditos de compare.py
# mais este quinto, que NUNCA e' escondido atras de media (item 19).
CRITICAL_REGRESSION_PRESENT = "CRITICAL_REGRESSION_PRESENT"


def compare_project_artifacts(project_id, reference_artifact="baseline",
                              current_artifact="score"):
    """Compara dois artefatos JA' GRAVADOS de um projeto - `None` quando
    falta artefato de QUALQUER lado (o projeto vira NOT_COMPARABLE, nunca
    um erro escondido). Reaproveita o mesmo carregador/deteccao de formato
    de `tools/run_golden_compare.py` - um so' lugar que sabe ler
    score/baseline/result/reference/findings."""
    from ..tools import run_golden_compare as cli  # import tardio evita ciclo golden<->tools

    paths = benchmark_runner.project_paths(project_id)
    directory = paths["dir"]
    ref_filename = cli.PROJECT_ARTIFACT_FILES.get(reference_artifact)
    cur_filename = cli.PROJECT_ARTIFACT_FILES.get(current_artifact)
    if ref_filename is None or cur_filename is None:
        return None
    if not (os.path.isfile(os.path.join(directory, ref_filename))
           and os.path.isfile(os.path.join(directory, cur_filename))):
        return None

    reference_side, _ = cli._load_project_artifact(project_id, reference_artifact)
    current_side, _ = cli._load_project_artifact(project_id, current_artifact)
    reference_side.setdefault("project_id", project_id)
    current_side.setdefault("project_id", project_id)
    return compare_module.compare(reference_side, current_side)


def run_corpus(corpus, project_ids=None, reference_artifact="baseline",
               current_artifact="score"):
    """Roda a comparacao em TODO O CORPUS, ou no subconjunto `project_ids`
    (item 17: um projeto so', ou --all). Cada linha do resultado diz
    `comparable` - um projeto `ANALYSIS_ONLY`/nao reproduzivel, ou sem os
    dois artefatos em disco, entra como `NOT_COMPARABLE` com o motivo
    (`reason`), nunca e' descartado em silencio."""
    ids = project_ids if project_ids is not None else corpus.list_projects()
    rows = []
    for project_id in ids:
        entry = corpus.get_project(project_id)
        comparison = None
        comparable = False
        reason = None
        if entry is None:
            reason = "projeto nao esta' no manifesto"
        elif not entry.get("reproducible"):
            missing = ", ".join(entry.get("missing_requirements") or []) or "sem dado executavel"
            reason = "reference_kind={0} nao e' reproduzivel ({1})".format(
                entry.get("reference_kind"), missing)
        else:
            try:
                comparison = compare_project_artifacts(
                    project_id, reference_artifact, current_artifact)
            except (RuntimeError, ValueError) as exc:
                reason = "erro ao carregar artefatos: {0}".format(exc)
                comparison = None
            comparable = comparison is not None
            if not comparable and reason is None:
                reason = "faltam os artefatos '{0}'/'{1}' em disco para este projeto".format(
                    reference_artifact, current_artifact)
        rows.append({
            "project_id": project_id,
            "entry": entry,
            "comparable": comparable,
            "reason": reason,
            "comparison": comparison,
        })
    return rows


def _overall_from_counts(counts):
    if counts.get(compare_module.VERDICT_REGRESSED, 0) > 0:
        return compare_module.VERDICT_REGRESSED
    if counts.get(compare_module.VERDICT_MIXED, 0) > 0:
        return compare_module.VERDICT_MIXED
    if counts.get(compare_module.VERDICT_IMPROVED, 0) > 0:
        return compare_module.VERDICT_IMPROVED
    return compare_module.VERDICT_NEUTRAL


def summarize_corpus_run(rows):
    """REFERENCE CORPUS SUMMARY (item 18). Regra dura do item 19: se
    QUALQUER projeto comparavel tiver regressao critica, `overall` e'
    SEMPRE `CRITICAL_REGRESSION_PRESENT` - nunca "11 melhoraram, 1 quebrou
    porta -> overall improved"."""
    counts = {
        compare_module.VERDICT_IMPROVED: 0,
        compare_module.VERDICT_NEUTRAL: 0,
        compare_module.VERDICT_REGRESSED: 0,
        compare_module.VERDICT_MIXED: 0,
        NOT_COMPARABLE: 0,
    }
    critical_regressions = []
    for row in rows:
        if not row["comparable"]:
            counts[NOT_COMPARABLE] += 1
            continue
        verdict = row["comparison"]["verdict"]
        counts[verdict] = counts.get(verdict, 0) + 1
        critical = row["comparison"].get("critical_invariants") or {}
        for regression in critical.get("regressions") or []:
            entry = dict(regression)
            entry["project_id"] = row["project_id"]
            critical_regressions.append(entry)

    overall = (CRITICAL_REGRESSION_PRESENT if critical_regressions
              else _overall_from_counts(counts))
    return {
        "total": len(rows),
        "counts": counts,
        "overall": overall,
        "critical_regressions": critical_regressions,
    }


# ---------------------------------------------- matriz projeto x metrica
#
# item 20. Colunas default = os exemplos citados no pedido (coverage,
# prism, openings, L/T/X, collisions, non_modular, compensators) -
# qualquer uma existe hoje em `metrics.py`. Passar outra lista de colunas
# pra' quem quiser outra vista.
DEFAULT_MATRIX_COLUMNS = (
    ("walls", "coverage_pct", "coverage"),
    ("prism", "alignment_conflicts", "prism"),
    ("openings", "blocks_inside_door", "openings"),
    ("junctions", "missing_binding", "L/T/X"),
    ("quality", "collisions", "collisions"),
    ("quality", "non_modular_walls", "non_modular"),
    ("quality", "consecutive_compensators", "compensators"),
)


def _metric_row(categories, category, metric_key):
    for row in (categories.get(category) or {}).get("metrics") or []:
        if row["metric"] == metric_key:
            return row
    return None


def build_matrix(rows, columns=DEFAULT_MATRIX_COLUMNS):
    """Projeto x metrica (item 20): cada celula e' o `status` daquela
    metrica (`IMPROVED`/`REGRESSED`/`UNCHANGED`/`INFORMATIONAL`/
    `NOT_AVAILABLE`) para aquele projeto, ou `NOT_COMPARABLE` quando o
    projeto inteiro nao pode ser comparado."""
    matrix_rows = []
    for row in rows:
        labels = [label for _c, _m, label in columns]
        if not row["comparable"]:
            cells = dict((label, NOT_COMPARABLE) for label in labels)
        else:
            categories = row["comparison"]["categories"]
            cells = {}
            for category, metric_key, label in columns:
                metric_row = _metric_row(categories, category, metric_key)
                cells[label] = metric_row["status"] if metric_row else compare_module.STATUS_NOT_AVAILABLE
        matrix_rows.append({"project_id": row["project_id"], "cells": cells})
    return {"columns": [label for _c, _m, label in columns], "rows": matrix_rows}
