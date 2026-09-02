# -*- coding: utf-8 -*-
"""Relatorio Markdown do benchmark de referencia (item 23 do CR anterior +
item 46 do CR-BLOCK-REFERENCE-CORPUS: relatorio POR PROJETO e relatorio DO
CORPUS). O JSON completo (`compare.compare(...)`/`corpus.run_corpus(...)`)
e' sempre a fonte da verdade; isto e' so' uma projecao legivel dele - texto
puro, sem template engine nova.
"""

from . import compare as compare_module
from . import corpus as corpus_module
from . import wall_diff as wall_diff_module

_ARROW = "->"


def _fmt_value(entry):
    value = entry.get("current")
    if value is None:
        return "N/D"
    unit = entry.get("unit")
    return "{0}{1}".format(value, (" " + unit) if unit else "")


def _fmt_delta(entry):
    if entry["reference"] is None or entry["current"] is None:
        return "N/D"
    delta = entry["delta_abs"]
    sign = "+" if delta is not None and delta > 0 else ""
    pct = "" if entry["delta_pct"] is None else " ({0}{1}%)".format(
        "+" if entry["delta_pct"] > 0 else "", entry["delta_pct"])
    return "{0}{1}{2}".format(sign, delta, pct)


_STATUS_MARK = {
    compare_module.STATUS_IMPROVED: "MELHOROU",
    compare_module.STATUS_REGRESSED: "PIOROU",
    compare_module.STATUS_UNCHANGED: "igual",
    compare_module.STATUS_INFORMATIONAL: "informativo",
    compare_module.STATUS_NOT_AVAILABLE: "N/D",
}


def _category_table(category_name, category_result):
    lines = ["### {0}".format(category_name), ""]
    lines.append("| metrica | referencia | atual | delta | situacao |")
    lines.append("|---|---:|---:|---:|---|")
    for row in category_result["metrics"]:
        lines.append("| {0} | {1} | {2} | {3} | {4} |".format(
            row["metric"],
            "N/D" if row["reference"] is None else row["reference"],
            "N/D" if row["current"] is None else row["current"],
            _fmt_delta(row),
            _STATUS_MARK.get(row["status"], row["status"]),
        ))
    lines.append("")
    return "\n".join(lines)


def render_comparison(comparison, title=None):
    """Item 23: markdown completo. `comparison` = saida de
    `compare.compare(...)`."""
    lines = []
    lines.append("# {0}".format(title or comparison.get("project_id") or "Golden Benchmark"))
    lines.append("")
    lines.append("**Resultado: {0}**".format(comparison.get("verdict")))
    lines.append("")
    counts = comparison.get("overall_counts") or {}
    lines.append("- metricas melhores: {0}".format(counts.get(compare_module.STATUS_IMPROVED, 0)))
    lines.append("- metricas piores: {0}".format(counts.get(compare_module.STATUS_REGRESSED, 0)))
    lines.append("- metricas iguais: {0}".format(counts.get(compare_module.STATUS_UNCHANGED, 0)))
    lines.append("- metricas informativas: {0}".format(counts.get(compare_module.STATUS_INFORMATIONAL, 0)))
    lines.append("- metricas nao disponiveis: {0}".format(counts.get(compare_module.STATUS_NOT_AVAILABLE, 0)))
    lines.append("")

    critical = comparison.get("critical_invariants")
    lines.append("## Invariantes criticos")
    lines.append("")
    if not critical or not critical.get("available"):
        lines.append("N/D - precisa de `score` dos dois lados (ver `golden/compare.py`).")
    elif critical.get("regressions"):
        lines.append("**REGRESSAO CRITICA** - piorou em:")
        lines.append("")
        for row in critical["regressions"]:
            lines.append("- `{0}`: {1} {2} {3}".format(
                row["code"], row["before"], _ARROW, row["after"]))
    else:
        lines.append("sem regressao critica.")
    lines.append("")

    lines.append("## Metricas por categoria")
    lines.append("")
    for category_name, category_result in sorted((comparison.get("categories") or {}).items()):
        lines.append(_category_table(category_name, category_result))

    return "\n".join(lines)


def render_wall_diff(wall_diff_result, max_walls=20):
    """Secao 'Paredes alteradas' (item 23, exemplo do relatorio)."""
    lines = ["## Paredes alteradas", ""]
    summary = wall_diff_result["summary"]
    lines.append("Paredes com diferenca: {0} | so' no atual: {1} | so' na referencia: {2}".format(
        len(summary["changed"]), len(summary["added_walls"]), len(summary["removed_walls"])))
    lines.append("")
    walls = wall_diff_result["walls"][:max_walls]
    if not walls:
        lines.append("(nenhuma parede com diferenca)")
        return "\n".join(lines)
    lines.append("| parede | referencia | ADDED | REMOVED | MOVED | CHANGED_CODE | similaridade estrutural |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for wall in walls:
        action = wall["by_action"]
        lines.append("| {0} | {1} | {2} | {3} | {4} | {5} | {6}% |".format(
            wall["wall"], wall["reference_wall"] or "-",
            action[wall_diff_module.ACTION_ADDED],
            action[wall_diff_module.ACTION_REMOVED],
            action[wall_diff_module.ACTION_MOVED],
            action[wall_diff_module.ACTION_CHANGED_CODE],
            round(100.0 * (wall["structural_similarity"] or 0.0), 1),
        ))
    if len(wall_diff_result["walls"]) > max_walls:
        lines.append("")
        lines.append("... e mais {0} parede(s) com diferenca.".format(
            len(wall_diff_result["walls"]) - max_walls))
    return "\n".join(lines)


def full_report(comparison, wall_diff_result=None, title=None):
    parts = [render_comparison(comparison, title=title)]
    if wall_diff_result is not None:
        parts.append("")
        parts.append(render_wall_diff(wall_diff_result))
    return "\n".join(parts)


# ======================================================= RELATORIO DO CORPUS
#
# item 46: dois niveis de relatorio - por projeto (acima) e do corpus
# inteiro (abaixo). "REFERENCE CORPUS SUMMARY" e' o exemplo literal do
# pedido (item 18).

def render_corpus_summary(summary):
    lines = []
    lines.append("# REFERENCE CORPUS SUMMARY")
    lines.append("")
    lines.append("Projetos executados: {0}".format(summary["total"]))
    lines.append("")
    counts = summary["counts"]
    lines.append("- IMPROVED: {0}".format(counts.get(compare_module.VERDICT_IMPROVED, 0)))
    lines.append("- NEUTRAL: {0}".format(counts.get(compare_module.VERDICT_NEUTRAL, 0)))
    lines.append("- REGRESSED: {0}".format(counts.get(compare_module.VERDICT_REGRESSED, 0)))
    lines.append("- MIXED: {0}".format(counts.get(compare_module.VERDICT_MIXED, 0)))
    lines.append("- NOT_COMPARABLE: {0}".format(counts.get(corpus_module.NOT_COMPARABLE, 0)))
    lines.append("")
    lines.append("**OVERALL: {0}**".format(summary["overall"]))
    if summary["overall"] == corpus_module.CRITICAL_REGRESSION_PRESENT:
        lines.append("")
        lines.append(
            "Uma media boa NUNCA esconde isto (item 19) - pelo menos um "
            "projeto tem regressao em invariante critico:"
        )
    lines.append("")
    if summary["critical_regressions"]:
        lines.append("## REGRESSOES CRITICAS")
        lines.append("")
        for row in summary["critical_regressions"]:
            lines.append("- **{0}**: `{1}` {2} {3} {4}".format(
                row["project_id"], row["code"], row["before"], _ARROW, row["after"]))
    else:
        lines.append("sem regressao critica em nenhum projeto comparavel.")
    return "\n".join(lines)


def render_corpus_matrix(matrix):
    lines = ["## Matriz projeto x metrica", ""]
    header = "| projeto | " + " | ".join(matrix["columns"]) + " |"
    sep = "|---|" + "---|" * len(matrix["columns"])
    lines.append(header)
    lines.append(sep)
    for row in matrix["rows"]:
        cells = [row["cells"].get(label, "-") for label in matrix["columns"]]
        lines.append("| {0} | {1} |".format(row["project_id"], " | ".join(cells)))
    return "\n".join(lines)


def render_corpus_projects_table(rows):
    lines = ["## Projetos", ""]
    lines.append("| projeto | kind | confidence | comparavel | veredito/motivo |")
    lines.append("|---|---|---|---|---|")
    for row in rows:
        entry = row.get("entry") or {}
        if row["comparable"]:
            outcome = row["comparison"]["verdict"]
        else:
            outcome = row.get("reason") or corpus_module.NOT_COMPARABLE
        lines.append("| {0} | {1} | {2} | {3} | {4} |".format(
            row["project_id"], entry.get("reference_kind", "-"),
            entry.get("confidence", "-"), "sim" if row["comparable"] else "nao",
            outcome))
    return "\n".join(lines)


def full_corpus_report(rows, summary, matrix):
    """Relatorio DO CORPUS inteiro (item 46) - resumo + tabela de projetos
    + matriz projeto x metrica. Para o diagnostico de UM projeto dentro
    disso, usar `full_report(row['comparison'], ...)`."""
    parts = [
        render_corpus_summary(summary),
        "",
        render_corpus_projects_table(rows),
        "",
        render_corpus_matrix(matrix),
    ]
    return "\n".join(parts)
