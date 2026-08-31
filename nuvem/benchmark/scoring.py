# -*- coding: utf-8 -*-
"""Score do benchmark (item 13) e comparacao entre versoes (item 14).

A exigencia que define o formato: *"nao esconda erros criticos atras de
uma media"*. Um score de 98% com 3 paredes nao moduladas continua sendo
um problema grave.

Por isso o score NUNCA e' um numero so'. `score_project` devolve:

* contagem PASS/FAIL por categoria (uma linha por validador);
* `critical_errors` a parte, fora da media;
* `blocking` - booleano: verdadeiro se houver QUALQUER erro critico,
  independentemente da taxa de sucesso;
* `per_wall` - a tabela por parede do item 15.

E `compare_runs` (item 14) classifica cada categoria em MELHORIA /
REGRESSAO / INALTERADO, com uma regra dura: **regressao em erro critico
e' REGRESSAO CRITICA**, mesmo que o total de erros tenha caido.

O que conta como "unidade avaliada" em cada categoria: a PAREDE. Uma
parede sem nenhum achado daquela categoria e' um PASS; com pelo menos um,
e' um FAIL. Contar achados em vez de paredes daria peso enorme a uma
unica parede ruim com 300 juntas alinhadas e esconderia 50 paredes com um
problema cada.
"""

from .validators import base

STATUS_IMPROVED = "MELHORIA"
STATUS_REGRESSED = "REGRESSAO"
STATUS_CRITICAL_REGRESSION = "REGRESSAO CRITICA"
STATUS_UNCHANGED = "INALTERADO"


def _wall_ids(project):
    return [wall.get("id") for wall in project.get("walls") or []]


def score_project(project, findings, validator_errors=None):
    wall_ids = _wall_ids(project)
    total_walls = len(wall_ids) or 1

    # ---- por categoria -------------------------------------------------
    failing_walls = dict((category, set()) for category in base.ALL_CATEGORIES)
    findings_by_category = dict((category, []) for category in base.ALL_CATEGORIES)
    for item in findings:
        category = item.get("validator")
        if category not in findings_by_category:
            findings_by_category[category] = []
            failing_walls[category] = set()
        findings_by_category[category].append(item)
        # Erro de nivel 2 NAO reprova a parede - e' preferencia (item 10).
        if item.get("level") == base.LEVEL_MANDATORY and item.get("wall"):
            failing_walls[category].add(item["wall"])

    categories = []
    for category in sorted(findings_by_category):
        failed = len(failing_walls[category])
        categories.append({
            "category": category,
            "pass": max(0, len(wall_ids) - failed),
            "fail": failed,
            "findings": len(findings_by_category[category]),
            "findings_level_1": sum(
                1 for f in findings_by_category[category]
                if f.get("level") == base.LEVEL_MANDATORY),
            "findings_level_2": sum(
                1 for f in findings_by_category[category]
                if f.get("level") == base.LEVEL_PREFERENCE),
            "success_rate": round(
                max(0, len(wall_ids) - failed) / float(total_walls), 4),
        })

    # ---- criticos, sempre a parte --------------------------------------
    critical = [f for f in findings if f.get("severity") == base.SEVERITY_CRITICAL]
    critical_by_code = {}
    for item in critical:
        critical_by_code[item["code"]] = critical_by_code.get(item["code"], 0) + 1

    # ---- por parede (item 15) ------------------------------------------
    per_wall = []
    for wall_id in wall_ids:
        row = {"wall": wall_id, "status": "PASS"}
        for category in base.ALL_CATEGORIES:
            failed = wall_id in failing_walls.get(category, set())
            row[category] = "FAIL" if failed else "PASS"
            if failed:
                row["status"] = "FAIL"
        row["findings"] = sum(1 for f in findings if f.get("wall") == wall_id)
        per_wall.append(row)

    walls_with_level1 = set()
    for item in findings:
        if item.get("level") == base.LEVEL_MANDATORY and item.get("wall"):
            walls_with_level1.add(item["wall"])

    by_code = {}
    for item in findings:
        by_code[item["code"]] = by_code.get(item["code"], 0) + 1

    return {
        "project_id": project.get("project_id"),
        "source": project.get("source"),
        "walls": len(wall_ids),
        "blocks": sum(len(row.get("blocks") or [])
                      for wall in project.get("walls") or []
                      for row in wall.get("rows") or []),
        "categories": categories,
        "findings_total": len(findings),
        "findings_level_1": sum(1 for f in findings
                                if f.get("level") == base.LEVEL_MANDATORY),
        "findings_level_2": sum(1 for f in findings
                                if f.get("level") == base.LEVEL_PREFERENCE),
        "critical_errors": len(critical),
        "critical_by_code": critical_by_code,
        "findings_by_code": by_code,
        # Taxa de sucesso = paredes sem NENHUM erro de nivel 1.
        "success_rate": round(
            (len(wall_ids) - len(walls_with_level1)) / float(total_walls), 4),
        "walls_failing": sorted(walls_with_level1),
        # O sinal que nao pode ser diluido pela media.
        "blocking": bool(critical),
        "per_wall": per_wall,
        "validator_errors": list(validator_errors or []),
    }


def _category_map(score):
    return dict((entry["category"], entry) for entry in score.get("categories") or [])


def compare_runs(baseline, current):
    """BASELINE x NOVA VERSAO (item 14).

    Uma correcao que melhora uma categoria e piora outra NAO pode ser
    aceita em silencio - por isso o veredito global (`verdict`) so' e'
    MELHORIA quando nenhuma categoria regrediu e nenhum critico novo
    apareceu."""
    base_categories = _category_map(baseline)
    current_categories = _category_map(current)

    rows = []
    for category in sorted(set(base_categories) | set(current_categories)):
        before = base_categories.get(category, {}).get("fail", 0)
        after = current_categories.get(category, {}).get("fail", 0)
        if after < before:
            status = STATUS_IMPROVED
        elif after > before:
            status = STATUS_REGRESSED
        else:
            status = STATUS_UNCHANGED
        rows.append({
            "category": category,
            "before": before,
            "after": after,
            "delta": after - before,
            "status": status,
        })

    # Criticos por codigo - um critico NOVO e' regressao critica mesmo que
    # o total tenha caido.
    before_codes = baseline.get("critical_by_code") or {}
    after_codes = current.get("critical_by_code") or {}
    critical_rows = []
    for code in sorted(set(before_codes) | set(after_codes)):
        before = before_codes.get(code, 0)
        after = after_codes.get(code, 0)
        if after > before:
            status = STATUS_CRITICAL_REGRESSION
        elif after < before:
            status = STATUS_IMPROVED
        else:
            status = STATUS_UNCHANGED
        critical_rows.append({
            "code": code, "before": before, "after": after,
            "delta": after - before, "status": status,
        })

    fixed_codes, new_codes = [], []
    before_all = baseline.get("findings_by_code") or {}
    after_all = current.get("findings_by_code") or {}
    for code in sorted(set(before_all) | set(after_all)):
        before, after = before_all.get(code, 0), after_all.get(code, 0)
        if after < before:
            fixed_codes.append({"code": code, "before": before, "after": after})
        elif after > before:
            new_codes.append({"code": code, "before": before, "after": after})

    has_critical_regression = any(
        row["status"] == STATUS_CRITICAL_REGRESSION for row in critical_rows)
    has_regression = any(row["status"] == STATUS_REGRESSED for row in rows)

    # Paredes que passaram a falhar / deixaram de falhar.
    before_failing = set(baseline.get("walls_failing") or [])
    after_failing = set(current.get("walls_failing") or [])

    if has_critical_regression:
        verdict = STATUS_CRITICAL_REGRESSION
    elif has_regression:
        verdict = STATUS_REGRESSED
    elif any(row["status"] == STATUS_IMPROVED for row in rows) or fixed_codes:
        verdict = STATUS_IMPROVED
    else:
        verdict = STATUS_UNCHANGED

    return {
        "project_id": current.get("project_id"),
        "verdict": verdict,
        "categories": rows,
        "critical": critical_rows,
        "fixed_codes": fixed_codes,
        "new_codes": new_codes,
        "success_rate_before": baseline.get("success_rate"),
        "success_rate_after": current.get("success_rate"),
        "walls_fixed": sorted(before_failing - after_failing),
        "walls_broken": sorted(after_failing - before_failing),
        "walls_still_failing": sorted(before_failing & after_failing),
    }
