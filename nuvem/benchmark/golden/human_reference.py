# -*- coding: utf-8 -*-
"""Comparacao HUMANO x SOLVER (itens 40-41 do CR-BLOCK-REFERENCE-CORPUS).

So' faz sentido quando o lado de referencia e' `reference_kind=HUMAN`
(`manifest.KIND_HUMAN`) - comparar contra um baseline do proprio solver
e' outra pergunta (regressao/determinismo), respondida por
`compare.py`/`corpus.py`, nao por este modulo.

Item 41: "nao chamar toda diferenca de erro". Em cima do diff ja'
calculado por `wall_diff.py` (ADDED/REMOVED/MOVED/CHANGED_CODE, item 21),
este modulo classifica cada diferenca num vocabulario mais fino:

    IDENTICAL             - mesma peca, mesmo lugar.
    EQUIVALENT             - peca diferente, MESMO intervalo, nivel 1 ok.
    DIFFERENT_VALID         - layout diferente (peca a mais/a menos/
                              movida), nivel 1 ok - solucao diferente,
                              nao errada (regra fundamental do projeto).
    POTENTIAL_REGRESSION     - a parede TEM achado de nivel 1 (obrigatorio)
                              e a diferenca e' de layout - pode ser a
                              causa, precisa de olhar humano.
    RULE_VIOLATION             - a parede tem achado de nivel 1 numa
                              substituicao de peca no MESMO lugar - a
                              troca em si e' que fere a regra.
    UNKNOWN                     - sem `findings` para checar nivel 1, uma
                              diferenca de layout (ADDED/REMOVED/MOVED)
                              fica UNKNOWN, nunca adivinhada como valida.

NUNCA reimplementa regra (item 43): "tem achado de nivel 1" vem sempre
dos validadores existentes (`validators/base.py`, via a lista de
`findings` de quem chama) - este modulo so' cruza isso com o diff.
"""

from . import wall_diff as wall_diff_module
from ..validators import base as validators_base

CLASS_IDENTICAL = "IDENTICAL"
CLASS_EQUIVALENT = "EQUIVALENT"
CLASS_DIFFERENT_VALID = "DIFFERENT_VALID"
CLASS_POTENTIAL_REGRESSION = "POTENTIAL_REGRESSION"
CLASS_RULE_VIOLATION = "RULE_VIOLATION"
CLASS_UNKNOWN = "UNKNOWN"

ALL_CLASSES = (CLASS_IDENTICAL, CLASS_EQUIVALENT, CLASS_DIFFERENT_VALID,
              CLASS_POTENTIAL_REGRESSION, CLASS_RULE_VIOLATION, CLASS_UNKNOWN)

_LAYOUT_ACTIONS = (wall_diff_module.ACTION_ADDED, wall_diff_module.ACTION_REMOVED,
                   wall_diff_module.ACTION_MOVED)


def _wall_has_mandatory_finding(findings, wall_id):
    for item in findings or []:
        if item.get("wall") == wall_id and item.get("level") == validators_base.LEVEL_MANDATORY:
            return True
    return False


def classify_difference(difference, findings=None):
    """`difference`: um item de `wall_diff.block_diff_for_wall(...)`
    (tem `action` e `wall`). `findings`: lista de achados do RESULTADO
    ATUAL (ja' calculados pelos validadores) - sem ela, uma diferenca de
    LAYOUT fica `UNKNOWN` (nao da' pra dizer se e' valida sem checar
    regra); uma TROCA DE PECA no mesmo lugar continua `EQUIVALENT` (fato
    estrutural, nao depende de achado)."""
    action = difference.get("action")
    if action == wall_diff_module.ACTION_CHANGED_CODE:
        base_class = CLASS_EQUIVALENT
    elif action in _LAYOUT_ACTIONS:
        base_class = CLASS_DIFFERENT_VALID
    else:
        return CLASS_UNKNOWN

    if findings is None:
        return base_class if action == wall_diff_module.ACTION_CHANGED_CODE else CLASS_UNKNOWN

    wall_id = difference.get("wall")
    if _wall_has_mandatory_finding(findings, wall_id):
        return (CLASS_RULE_VIOLATION if base_class == CLASS_EQUIVALENT
               else CLASS_POTENTIAL_REGRESSION)
    return base_class


def classify_wall_differences(differences, findings=None):
    """`differences`: a lista de `wall_diff.block_diff_for_wall(...)`.
    Devolve a MESMA lista, com `human_vs_solver_class` acrescentado em
    cada item - nunca substitui `action`/`class` (item 21 continua
    disponivel do jeito que era)."""
    out = []
    for difference in differences:
        row = dict(difference)
        row["human_vs_solver_class"] = classify_difference(difference, findings=findings)
        out.append(row)
    return out


def human_vs_solver_report(wall_diff_result, findings=None):
    """Em cima de `wall_diff.wall_diff_report(...)` (item 21/40): cada
    parede alterada ganha a lista de diferencas classificada, mais uma
    contagem por classe - a pergunta "isso e' regressao ou so' diferente
    do humano?" respondida por parede, sem chamar toda diferenca de
    erro (item 41)."""
    walls = []
    totals = dict((klass, 0) for klass in ALL_CLASSES)
    for wall in wall_diff_result.get("walls") or []:
        # `wall_diff.wall_diff_report` ja' guarda os diffs por fiada
        # (`courses`); achatar de novo aqui so' pra' classificar.
        flat = []
        for course_diffs in (wall.get("courses") or {}).values():
            flat.extend(course_diffs)
        classified = classify_wall_differences(flat, findings=findings)
        counts = dict((klass, 0) for klass in ALL_CLASSES)
        for item in classified:
            counts[item["human_vs_solver_class"]] += 1
            totals[item["human_vs_solver_class"]] += 1
        walls.append({
            "wall": wall["wall"],
            "reference_wall": wall.get("reference_wall"),
            "counts": counts,
            "differences": classified,
        })
    return {
        "findings_available": findings is not None,
        "totals": totals,
        "walls": walls,
    }
