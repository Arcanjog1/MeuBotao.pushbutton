# -*- coding: utf-8 -*-
"""Diff por PAREDE / FIADA / BLOCO (itens 19 a 22 do pedido).

Nao reimplementa casamento nem classificacao de diferenca - isso ja
existe, testado, em `comparator/compare_projects.py` e
`comparator/match.py`, e ja usa identidade GEOMETRICA (nunca `wall_idx`,
ver `model.wall_stable_key` - item 20/21: reversao de ponta produz a
MESMA identidade). Este modulo so' REORGANIZA aquele resultado nas tres
perguntas que o pedido faz:

  item 19 - "QUAIS paredes mudaram?"          -> `changed_wall_ids`
  item 21 - ADDED/REMOVED/MOVED/CHANGED_CODE   -> `diff_class_to_action`
  item 22 - parede -> fiada -> blocos          -> `course_diff_for_wall`

`compare_projects.compare_wall` ja produz `differences` com `row` dentro
de cada item - a hierarquia parede->fiada->bloco do item 22 e' so' um
agrupamento por essa chave, nao uma travessia geometrica nova.
"""

from ..comparator import compare_projects as comparator

ACTION_ADDED = "ADDED"
ACTION_REMOVED = "REMOVED"
ACTION_MOVED = "MOVED"
ACTION_CHANGED_CODE = "CHANGED_CODE"

_CLASS_TO_ACTION = {
    # DIFF_EXTRA: o resultado ATUAL tem peca onde o lado de referencia
    # nao tem -> foi ADICIONADA.
    comparator.DIFF_EXTRA: ACTION_ADDED,
    # DIFF_MISSING: o lado de referencia tinha peca ali e o atual nao tem
    # mais -> foi REMOVIDA.
    comparator.DIFF_MISSING: ACTION_REMOVED,
    # DIFF_LAYOUT: o INTERVALO mudou (a peca se moveu no eixo).
    comparator.DIFF_LAYOUT: ACTION_MOVED,
    # DIFF_EQUIVALENT: mesmo intervalo, codigo de peca diferente.
    comparator.DIFF_EQUIVALENT: ACTION_CHANGED_CODE,
}


def diff_class_to_action(diff_class):
    return _CLASS_TO_ACTION.get(diff_class)


def compute_wall_diff(current_project, reference_project):
    """`current_project`/`reference_project` no formato `model.py`. O
    nome 'reference' aqui e' generico (item 9: RESULTADO A x RESULTADO B)
    - nao precisa ser um golden, pode ser a versao anterior do solver."""
    return comparator.compare_projects(current_project, reference_project)


def changed_wall_ids(comparison, min_changes=1):
    """Item 19: 'QUAIS paredes mudaram?' - ordenado por quantidade de
    mudanca (mais mudada primeiro), pra abrir o diagnostico das piores
    primeiro (item 33)."""
    rows = []
    for entry in comparison.get("per_wall") or []:
        changes = sum(count for name, count in entry["counts"].items()
                      if name != comparator.DIFF_IDENTICAL)
        if changes >= min_changes:
            rows.append((entry["wall"], changes))
    rows.sort(key=lambda item: (-item[1], item[0] or ""))
    only_result = comparison.get("walls_only_in_result") or []
    only_reference = comparison.get("walls_only_in_reference") or []
    return {
        "changed": [wall_id for wall_id, _count in rows],
        "changed_with_counts": [{"wall": wid, "changes": count} for wid, count in rows],
        "added_walls": sorted(only_result),
        "removed_walls": sorted(only_reference),
    }


def _wall_entry(comparison, wall_id):
    for entry in comparison.get("per_wall") or []:
        if entry["wall"] == wall_id:
            return entry
    return None


def block_diff_for_wall(comparison, wall_id):
    """Item 21: ADDED/REMOVED/MOVED/CHANGED_CODE, uma lista por parede."""
    entry = _wall_entry(comparison, wall_id)
    if entry is None:
        return None
    out = []
    for difference in entry["differences"]:
        row = dict(difference)
        row["action"] = diff_class_to_action(difference["class"])
        out.append(row)
    return out


def course_diff_for_wall(comparison, wall_id):
    """Item 22: parede -> fiada -> blocos. Agrupa as diferencas ja
    calculadas (cada uma ja carrega `row`) por indice de fiada."""
    diffs = block_diff_for_wall(comparison, wall_id)
    if diffs is None:
        return None
    by_row = {}
    for difference in diffs:
        by_row.setdefault(difference["row"], []).append(difference)
    return dict((row, sorted(items, key=lambda d: (
        (d.get("result_block") or {}).get("t_cm", [0])[0]
        if d.get("result_block") else
        (d.get("reference_block") or {}).get("t_cm", [0])[0]
    ))) for row, items in by_row.items())


def wall_diff_report(comparison, min_changes=1, max_walls=None):
    """Visao completa (itens 19-22 combinados): para cada parede
    alterada, contagem por acao + o diff fiada a fiada."""
    summary = changed_wall_ids(comparison, min_changes=min_changes)
    wall_ids = summary["changed"]
    if max_walls is not None:
        wall_ids = wall_ids[:max_walls]
    walls = []
    for wall_id in wall_ids:
        entry = _wall_entry(comparison, wall_id)
        diffs = block_diff_for_wall(comparison, wall_id)
        by_action = {ACTION_ADDED: 0, ACTION_REMOVED: 0, ACTION_MOVED: 0,
                    ACTION_CHANGED_CODE: 0}
        for difference in diffs:
            action = difference.get("action")
            if action in by_action:
                by_action[action] += 1
        walls.append({
            "wall": wall_id,
            "reference_wall": entry.get("reference_wall") if entry else None,
            "similarity": entry.get("similarity") if entry else None,
            "structural_similarity": entry.get("structural_similarity") if entry else None,
            "by_action": by_action,
            "courses": course_diff_for_wall(comparison, wall_id),
        })
    return {
        "summary": summary,
        "walls": walls,
    }
