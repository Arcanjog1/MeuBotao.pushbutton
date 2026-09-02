# -*- coding: utf-8 -*-
"""Motor de comparacao PURO e headless (item 9 do pedido): recebe
RESULTADO A (referencia) e RESULTADO B (atual) e devolve uma comparacao
estruturada - JSON + resumo legivel (via `report_md.py`).

Nao decide sozinho o que e' "melhor" quando a metrica nao tem regra de
dominio (item 12: nao inventar julgamento onde nao existe regra). O que
decide isso e' `metrics.py` (a DIRECAO de cada metrica); este modulo so'
aplica a direcao.

Reaproveita, nao reinventa: a classificacao de REGRESSAO CRITICA por
codigo de erro (item 14) delega para `benchmark.scoring.compare_runs`,
que ja e' testado e ja usa `validators/base.py` (SEVERITY_CRITICAL) como
fonte - nunca uma lista de invariantes inventada aqui.
"""

from .. import scoring as core_scoring
from . import metrics as golden_metrics

# ------------------------------------------------------------ status
STATUS_IMPROVED = "IMPROVED"
STATUS_REGRESSED = "REGRESSED"
STATUS_UNCHANGED = "UNCHANGED"
STATUS_INFORMATIONAL = "INFORMATIONAL"
STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"

# ----------------------------------------------------------- veredito
#
# Item 13: nunca uma nota unica cega. Estes quatro valores sao o
# resumo geral - sempre acompanhados das categorias (item 13) e da secao
# de criticos a parte (item 14), nunca sozinhos.
VERDICT_IMPROVED = "IMPROVED"
VERDICT_NEUTRAL = "NEUTRAL"
VERDICT_REGRESSED = "REGRESSED"
VERDICT_MIXED = "MIXED"


def _metric_status(direction, reference_value, current_value):
    if reference_value is None or current_value is None:
        return STATUS_NOT_AVAILABLE
    if direction in (golden_metrics.INFORMATIONAL, golden_metrics.CONTEXT_DEPENDENT):
        return STATUS_INFORMATIONAL
    if current_value == reference_value:
        return STATUS_UNCHANGED
    if direction == golden_metrics.HIGHER_IS_BETTER:
        improved = current_value > reference_value
    elif direction == golden_metrics.LOWER_IS_BETTER:
        improved = current_value < reference_value
    else:
        return STATUS_INFORMATIONAL
    return STATUS_IMPROVED if improved else STATUS_REGRESSED


def _deltas(reference_value, current_value):
    if reference_value is None or current_value is None:
        return None, None
    try:
        delta_abs = current_value - reference_value
    except TypeError:
        return None, None
    delta_pct = None
    if reference_value not in (0, 0.0):
        delta_pct = round(100.0 * delta_abs / float(reference_value), 2)
    elif current_value not in (0, 0.0):
        # De zero para algo: percentual nao existe (divisao por zero) -
        # informativo, nao inventado como +inf nem escondido como None.
        delta_pct = None
    return delta_abs, delta_pct


def compare_metric_entry(name, reference_entry, current_entry):
    reference_entry = reference_entry or {}
    current_entry = current_entry or {}
    direction = current_entry.get("direction") or reference_entry.get("direction") \
        or golden_metrics.INFORMATIONAL
    unit = current_entry.get("unit") or reference_entry.get("unit")
    ref_val = reference_entry.get("value")
    cur_val = current_entry.get("value")
    delta_abs, delta_pct = _deltas(ref_val, cur_val)
    return {
        "metric": name,
        "direction": direction,
        "unit": unit,
        "reference": ref_val,
        "current": cur_val,
        "delta_abs": delta_abs,
        "delta_pct": delta_pct,
        "status": _metric_status(direction, ref_val, cur_val),
    }


def compare_category(reference_category, current_category):
    reference_category = reference_category or {}
    current_category = current_category or {}
    keys = sorted(set(reference_category) | set(current_category))
    rows = [
        compare_metric_entry(key, reference_category.get(key), current_category.get(key))
        for key in keys
    ]
    counts = {STATUS_IMPROVED: 0, STATUS_REGRESSED: 0, STATUS_UNCHANGED: 0,
             STATUS_INFORMATIONAL: 0, STATUS_NOT_AVAILABLE: 0}
    for row in rows:
        counts[row["status"]] += 1
    return {"metrics": rows, "counts": counts}


def compare_bundles(reference_metrics, current_metrics):
    """Compara dois bundles ja' calculados por `metrics.compute_metrics`.
    Puro: nenhum dos dois lados precisa ser um projeto/score de verdade -
    da' pra comparar dois bundles montados a mao (util em teste)."""
    categories = sorted(set(reference_metrics or {}) | set(current_metrics or {}))
    result = {}
    for category in categories:
        result[category] = compare_category(
            (reference_metrics or {}).get(category),
            (current_metrics or {}).get(category),
        )
    return result


def _overall_counts(categories_result):
    total = {STATUS_IMPROVED: 0, STATUS_REGRESSED: 0, STATUS_UNCHANGED: 0,
            STATUS_INFORMATIONAL: 0, STATUS_NOT_AVAILABLE: 0}
    for entry in categories_result.values():
        for status, count in entry["counts"].items():
            total[status] += count
    return total


def _critical_regressions(reference_score, current_score):
    """Delega para `scoring.compare_runs` (item 14): a fonte de
    REGRAS_MODULACAO_BLOCOS.md por codigo ja e' `validators/base.py`, e o
    calculo "critico que piorou = regressao critica, mesmo que o total
    tenha caido" ja esta' testado la'. So' disponivel quando os dois
    lados tem `score` (formato `scoring.score_project`/`score.json`/
    `baseline.json`)."""
    if reference_score is None or current_score is None:
        return None
    delta = core_scoring.compare_runs(reference_score, current_score)
    regressions = [row for row in delta["critical"]
                  if row["status"] == core_scoring.STATUS_CRITICAL_REGRESSION]
    return {
        "available": True,
        "regressions": regressions,
        "fixed_codes": delta["fixed_codes"],
        "new_codes": delta["new_codes"],
        "walls_broken": delta["walls_broken"],
        "walls_fixed": delta["walls_fixed"],
        "core_scoring_verdict": delta["verdict"],
    }


def _summarize_verdict(overall_counts, critical):
    if critical and critical.get("available") and critical.get("regressions"):
        return VERDICT_REGRESSED
    improved = overall_counts[STATUS_IMPROVED]
    regressed = overall_counts[STATUS_REGRESSED]
    if improved == 0 and regressed == 0:
        return VERDICT_NEUTRAL
    if improved > 0 and regressed == 0:
        return VERDICT_IMPROVED
    if regressed > 0 and improved == 0:
        return VERDICT_REGRESSED
    return VERDICT_MIXED


def compare(reference, current):
    """API principal (item 9). `reference`/`current` sao dicts com
    QUALQUER subconjunto de: `project`, `score`, `findings`,
    `timing_seconds`, `by_stage_seconds`, `project_id`. Nao exige nenhum
    campo especifico - o que faltar vira NOT_AVAILABLE nas metricas
    (item 26), nunca erro.
    """
    reference = reference or {}
    current = current or {}

    reference_metrics = golden_metrics.compute_metrics(
        project=reference.get("project"), score=reference.get("score"),
        findings=reference.get("findings"),
        timing_seconds=reference.get("timing_seconds"),
        by_stage_seconds=reference.get("by_stage_seconds"),
    )
    current_metrics = golden_metrics.compute_metrics(
        project=current.get("project"), score=current.get("score"),
        findings=current.get("findings"),
        timing_seconds=current.get("timing_seconds"),
        by_stage_seconds=current.get("by_stage_seconds"),
    )

    categories = compare_bundles(reference_metrics, current_metrics)
    overall_counts = _overall_counts(categories)
    critical = _critical_regressions(reference.get("score"), current.get("score"))
    verdict = _summarize_verdict(overall_counts, critical)

    project_id = (current.get("project_id") or reference.get("project_id")
                 or (current.get("score") or {}).get("project_id")
                 or (reference.get("score") or {}).get("project_id"))

    return {
        "schema_version": 1,
        "project_id": project_id,
        "verdict": verdict,
        "overall_counts": overall_counts,
        "categories": categories,
        "critical_invariants": critical,
        "reference_metrics": reference_metrics,
        "current_metrics": current_metrics,
    }
