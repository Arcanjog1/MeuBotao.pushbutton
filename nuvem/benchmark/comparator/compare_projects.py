# -*- coding: utf-8 -*-
"""Comparacao RESULTADO x GABARITO - e a separacao entre "errado" e
"diferente" (item 10 do pedido).

A regra que organiza este modulo inteiro:

    Uma solucao diferente da do projetista humano **nao e' erro** se
    cumprir todas as regras obrigatorias.

Entao a comparacao nunca produz um veredito sozinha. Ela produz
DIFERENCAS classificadas, e quem decide se algo reprova sao os
validadores de nivel 1 (que rodam sobre o resultado, independentes do
gabarito).

Classes de diferenca (`classify_differences`):

* `IDENTICAL` - mesma peca, mesmo lugar.
* `EQUIVALENT_SUBSTITUTION` - peca diferente ocupando o MESMO intervalo
  (ex.: um B39 onde o humano pos B34+C04). Diferenca legitima enquanto o
  nivel 1 passar.
* `DIFFERENT_LAYOUT` - o intervalo em si mudou.
* `MISSING_IN_RESULT` - o humano pos peca ali e o solver nao pos nada. E'
  a diferenca que mais costuma esconder erro de cobertura.
* `EXTRA_IN_RESULT` - o solver pos peca onde o humano deixou vazio.
"""

from .. import analysis
from .. import model
from . import match

DIFF_IDENTICAL = "IDENTICAL"
DIFF_EQUIVALENT = "EQUIVALENT_SUBSTITUTION"
DIFF_LAYOUT = "DIFFERENT_LAYOUT"
DIFF_MISSING = "MISSING_IN_RESULT"
DIFF_EXTRA = "EXTRA_IN_RESULT"

ALL_DIFF_CLASSES = (DIFF_IDENTICAL, DIFF_EQUIVALENT, DIFF_LAYOUT,
                    DIFF_MISSING, DIFF_EXTRA)

# Dois blocos ocupam "o mesmo intervalo" quando as duas bordas batem
# dentro disto. Uma junta inteira (1cm) de folga.
SAME_EXTENT_TOLERANCE_CM = 1.5


def classify_block_pair(result_block, reference_block):
    if result_block is None:
        return DIFF_MISSING
    if reference_block is None:
        return DIFF_EXTRA
    same_extent = (
        abs(result_block["t_start_cm"] - reference_block["t_start_cm"]) <= SAME_EXTENT_TOLERANCE_CM
        and abs(result_block["t_end_cm"] - reference_block["t_end_cm"]) <= SAME_EXTENT_TOLERANCE_CM
    )
    if not same_extent:
        return DIFF_LAYOUT
    if result_block.get("code") == reference_block.get("code"):
        return DIFF_IDENTICAL
    return DIFF_EQUIVALENT


def compare_wall(result_wall, reference_wall):
    """Diferencas de UMA parede casada, fiada a fiada."""
    counts = dict((name, 0) for name in ALL_DIFF_CLASSES)
    differences = []
    reference_rows = analysis.wall_rows_by_index(reference_wall)
    result_rows = analysis.wall_rows_by_index(result_wall)
    for row_index in sorted(set(reference_rows) | set(result_rows)):
        result_row = result_rows.get(row_index)
        reference_row = reference_rows.get(row_index)
        for result_block, reference_block in match.match_blocks_in_row(result_row, reference_row):
            klass = classify_block_pair(result_block, reference_block)
            counts[klass] += 1
            if klass == DIFF_IDENTICAL:
                continue
            differences.append({
                "class": klass,
                "wall": result_wall.get("id"),
                "reference_wall": reference_wall.get("id"),
                "row": row_index,
                "result_block": None if result_block is None else {
                    "id": result_block.get("id"),
                    "code": result_block.get("code"),
                    "role": result_block.get("role"),
                    "t_cm": [result_block["t_start_cm"], result_block["t_end_cm"]],
                },
                "reference_block": None if reference_block is None else {
                    "id": reference_block.get("id"),
                    "code": reference_block.get("code"),
                    "role": reference_block.get("role"),
                    "t_cm": [reference_block["t_start_cm"], reference_block["t_end_cm"]],
                },
            })
    total = sum(counts.values()) or 1
    return {
        "wall": result_wall.get("id"),
        "reference_wall": reference_wall.get("id"),
        "counts": counts,
        "similarity": round(counts[DIFF_IDENTICAL] / float(total), 4),
        # Similaridade "estrutural": conta como acerto tambem a
        # substituicao equivalente, porque ela cumpre o mesmo papel no
        # mesmo lugar. E' o numero honesto para acompanhar evolucao.
        "structural_similarity": round(
            (counts[DIFF_IDENTICAL] + counts[DIFF_EQUIVALENT]) / float(total), 4),
        "differences": differences,
    }


def compare_projects(result_project, reference_project):
    """Comparacao completa. NAO diz se o resultado esta' certo - diz o que
    ele tem de diferente do gabarito, e onde."""
    matching = match.match_walls(result_project, reference_project)
    per_wall = [compare_wall(result_wall, reference_wall)
                for result_wall, reference_wall in matching["pairs"]]

    totals = dict((name, 0) for name in ALL_DIFF_CLASSES)
    for entry in per_wall:
        for name, value in entry["counts"].items():
            totals[name] += value
    total_blocks = sum(totals.values()) or 1

    return {
        "project_id": result_project.get("project_id"),
        "reference_project_id": reference_project.get("project_id"),
        "walls_matched": len(matching["pairs"]),
        "walls_only_in_result": [w.get("id") for w in matching["only_in_result"]],
        "walls_only_in_reference": [w.get("id") for w in matching["only_in_reference"]],
        "totals": totals,
        "similarity": round(totals[DIFF_IDENTICAL] / float(total_blocks), 4),
        "structural_similarity": round(
            (totals[DIFF_IDENTICAL] + totals[DIFF_EQUIVALENT]) / float(total_blocks), 4),
        "per_wall": per_wall,
        "pairs": matching["pairs"],
    }


def classify_differences(comparison, max_examples=5):
    """Resumo legivel das diferencas por classe, com exemplos concretos -
    e' o que o relatorio mostra e o que a investigacao de causa usa como
    ponto de partida."""
    buckets = dict((name, []) for name in ALL_DIFF_CLASSES)
    for entry in comparison.get("per_wall") or []:
        for difference in entry["differences"]:
            buckets[difference["class"]].append(difference)
    summary = []
    for name in ALL_DIFF_CLASSES:
        if name == DIFF_IDENTICAL:
            continue
        items = buckets[name]
        summary.append({
            "class": name,
            "count": len(items),
            "walls": sorted(set(d["wall"] for d in items))[:20],
            "examples": items[:max_examples],
        })
    return summary
