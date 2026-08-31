# -*- coding: utf-8 -*-
"""Relatorio em texto do benchmark (itens 13, 14 e 15).

Texto puro de proposito: e' o que entra no log, no commit e no terminal
sem depender de nada. O JSON completo continua ao lado (o runner grava os
dois) - este arquivo e' para ler, aquele e' para comparar.
"""

from . import scoring
from .validators import base


def _bar(value, width=28):
    filled = int(round(max(0.0, min(1.0, value)) * width))
    return "#" * filled + "." * (width - filled)


def format_score(score):
    lines = []
    lines.append("=" * 72)
    lines.append("BENCHMARK: {0}  ({1})".format(
        score.get("project_id"), score.get("source")))
    lines.append("=" * 72)
    lines.append("paredes: {0} | blocos: {1}".format(
        score.get("walls"), score.get("blocks")))
    lines.append("")
    lines.append("{0:<18} {1:>6} {2:>6} {3:>8}  {4}".format(
        "CATEGORIA", "PASS", "FAIL", "TAXA", "ACHADOS (n1/n2)"))
    lines.append("-" * 72)
    for entry in score.get("categories") or []:
        lines.append("{0:<18} {1:>6} {2:>6} {3:>7.1f}%  {4} ({5}/{6})".format(
            entry["category"], entry["pass"], entry["fail"],
            100.0 * entry["success_rate"], entry["findings"],
            entry["findings_level_1"], entry["findings_level_2"]))
    lines.append("-" * 72)
    lines.append("TAXA DE SUCESSO (paredes sem erro obrigatorio): {0:.1f}%  {1}".format(
        100.0 * (score.get("success_rate") or 0.0),
        _bar(score.get("success_rate") or 0.0)))
    lines.append("achados: {0} total | {1} obrigatorios (nivel 1) | {2} preferencia (nivel 2)".format(
        score.get("findings_total"), score.get("findings_level_1"),
        score.get("findings_level_2")))
    lines.append("")
    if score.get("blocking"):
        lines.append("!! ERROS CRITICOS: {0} - o benchmark REPROVA, independente da taxa acima".format(
            score.get("critical_errors")))
        for code, count in sorted((score.get("critical_by_code") or {}).items(),
                                  key=lambda kv: -kv[1]):
            lines.append("   {0:<34} {1}".format(code, count))
    else:
        lines.append("sem erros criticos.")
    if score.get("validator_errors"):
        lines.append("")
        lines.append("!! VALIDADOR QUEBRADO (resultado NAO e' confiavel):")
        for entry in score["validator_errors"]:
            lines.append("   {0}: {1}".format(entry["validator"], entry["error"]))
    return "\n".join(lines)


def format_per_wall(score, only_failing=False, limit=None):
    """A tabela do item 15 - uma linha por parede, uma coluna por
    categoria."""
    categories = list(base.ALL_CATEGORIES)
    lines = []
    header = "{0:<8}".format("PAREDE")
    for category in categories:
        header += " {0:>13}".format(category[:13])
    header += " {0:>8}".format("STATUS")
    lines.append(header)
    lines.append("-" * len(header))
    rows = score.get("per_wall") or []
    if only_failing:
        rows = [row for row in rows if row["status"] == "FAIL"]
    if limit:
        rows = rows[:limit]
    for row in rows:
        line = "{0:<8}".format(row["wall"])
        for category in categories:
            line += " {0:>13}".format(row.get(category, "-"))
        line += " {0:>8}".format(row["status"])
        lines.append(line)
    if not rows:
        lines.append("(nenhuma parede a listar)")
    return "\n".join(lines)


def format_findings(findings, limit=40, level=None):
    lines = []
    selected = [f for f in findings if level is None or f.get("level") == level]
    by_code = {}
    for item in selected:
        by_code.setdefault(item["code"], []).append(item)
    for code in sorted(by_code, key=lambda c: -len(by_code[c])):
        items = by_code[code]
        klass = base.error_class(code)
        lines.append("")
        lines.append("[{0}] {1}  ({2} ocorrencia(s), nivel {3}, {4})".format(
            code, klass.summary, len(items), klass.level, klass.severity))
        lines.append("    regra: {0}".format(klass.rule_ref or "-"))
        for item in items[:limit]:
            lines.append("    - {0}: {1}".format(item.get("wall") or "-",
                                                 item.get("detail")))
        if len(items) > limit:
            lines.append("    ... e mais {0}".format(len(items) - limit))
    if not selected:
        lines.append("(nenhum achado)")
    return "\n".join(lines)


def format_comparison(comparison):
    """Resultado x gabarito - similaridade, NAO veredito (item 10)."""
    lines = []
    lines.append("-" * 72)
    lines.append("COMPARACAO COM O GABARITO ({0})".format(
        comparison.get("reference_project_id")))
    lines.append("-" * 72)
    lines.append("paredes casadas: {0} | so' no resultado: {1} | so' no gabarito: {2}".format(
        comparison.get("walls_matched"),
        len(comparison.get("walls_only_in_result") or []),
        len(comparison.get("walls_only_in_reference") or [])))
    totals = comparison.get("totals") or {}
    for name in sorted(totals):
        lines.append("   {0:<26} {1}".format(name, totals[name]))
    lines.append("similaridade exata      : {0:.1f}%".format(
        100.0 * (comparison.get("similarity") or 0.0)))
    lines.append("similaridade estrutural : {0:.1f}%  (conta substituicao equivalente)".format(
        100.0 * (comparison.get("structural_similarity") or 0.0)))
    lines.append("")
    lines.append("LEMBRETE: diferenca do projeto humano NAO e' erro por si so'.")
    lines.append("O que reprova sao os achados de nivel 1 acima.")
    return "\n".join(lines)


def format_run_comparison(delta):
    """BASELINE x NOVA VERSAO (item 14)."""
    lines = []
    lines.append("=" * 72)
    lines.append("BASELINE  x  NOVA VERSAO - {0}".format(delta.get("project_id")))
    lines.append("=" * 72)
    lines.append("{0:<20} {1:>8} {2:>8} {3:>8}  {4}".format(
        "CATEGORIA", "ANTES", "DEPOIS", "DELTA", "SITUACAO"))
    lines.append("-" * 72)
    for row in delta.get("categories") or []:
        lines.append("{0:<20} {1:>8} {2:>8} {3:>+8}  {4}".format(
            row["category"], row["before"], row["after"], row["delta"],
            row["status"]))
    lines.append("-" * 72)
    lines.append("taxa de sucesso: {0:.1f}%  ->  {1:.1f}%".format(
        100.0 * (delta.get("success_rate_before") or 0.0),
        100.0 * (delta.get("success_rate_after") or 0.0)))
    critical = [row for row in delta.get("critical") or []
                if row["status"] != scoring.STATUS_UNCHANGED]
    if critical:
        lines.append("")
        lines.append("ERROS CRITICOS:")
        for row in critical:
            lines.append("   {0:<34} {1} -> {2}   {3}".format(
                row["code"], row["before"], row["after"], row["status"]))
    if delta.get("walls_broken"):
        lines.append("")
        lines.append("PAREDES QUE PASSARAM A FALHAR: {0}".format(
            ", ".join(delta["walls_broken"][:20])))
    if delta.get("walls_fixed"):
        lines.append("PAREDES CORRIGIDAS: {0}".format(
            ", ".join(delta["walls_fixed"][:20])))
    lines.append("")
    lines.append("VEREDITO: {0}".format(delta.get("verdict")))
    if delta.get("verdict") in (scoring.STATUS_REGRESSED,
                                scoring.STATUS_CRITICAL_REGRESSION):
        lines.append("Uma correcao que quebra outra parte NAO deve ser aceita "
                     "(item 14 do pedido).")
    return "\n".join(lines)


def format_noise_floor(score, reference_score):
    """Lado a lado: o MESMO validador no resultado e no projeto humano.

    E' a leitura mais importante do relatorio. O gabarito e' um projeto
    entregue e aprovado - todo achado que os validadores apontam NELE e'
    piso de ruido (limitacao da reconstrucao ou validador exigindo mais do
    que o escritorio pratica). Comparar contra esse piso e' o que separa
    "o solver esta' ruim nisso" de "este validador e' barulhento"."""
    lines = []
    lines.append("-" * 72)
    lines.append("RESULTADO  x  PROJETO HUMANO (mesmo validador nos dois)")
    lines.append("-" * 72)
    mine = score.get("findings_by_code") or {}
    theirs = reference_score.get("findings_by_code") or {}
    lines.append("{0:<38} {1:>9} {2:>9}  {3}".format(
        "CLASSE DE ERRO", "SOLVER", "HUMANO", "LEITURA"))
    for code in sorted(set(mine) | set(theirs),
                       key=lambda c: -(mine.get(c, 0) + theirs.get(c, 0))):
        a, b = mine.get(code, 0), theirs.get(code, 0)
        if b == 0 and a > 0:
            reading = "so' o solver erra"
        elif a > b * 2:
            reading = "solver {0:.1f}x o humano".format(a / float(b))
        elif a < b:
            reading = "ruido do validador (humano erra mais)"
        else:
            reading = "comparavel"
        lines.append("{0:<38} {1:>9} {2:>9}  {3}".format(code, a, b, reading))
    lines.append("")
    lines.append("O projeto humano NAO tem zero achado - ver README do benchmark,")
    lines.append("secao 'piso de ruido'. Numero do solver so' significa alguma")
    lines.append("coisa comparado com a coluna HUMANO.")
    return "\n".join(lines)


def full_report(score, findings, comparison=None, delta=None, reference_score=None):
    parts = [format_score(score), ""]
    parts.append("ACHADOS DE NIVEL 1 (obrigatorios)")
    parts.append(format_findings(findings, level=base.LEVEL_MANDATORY))
    parts.append("")
    parts.append("ACHADOS DE NIVEL 2 (preferencia - nao reprovam)")
    parts.append(format_findings(findings, level=base.LEVEL_PREFERENCE, limit=10))
    parts.append("")
    parts.append("RELATORIO POR PAREDE (so' as que falham)")
    parts.append(format_per_wall(score, only_failing=True, limit=60))
    if reference_score is not None:
        parts.append("")
        parts.append(format_noise_floor(score, reference_score))
    if comparison is not None:
        parts.append("")
        parts.append(format_comparison(comparison))
    if delta is not None:
        parts.append("")
        parts.append(format_run_comparison(delta))
    return "\n".join(parts)
