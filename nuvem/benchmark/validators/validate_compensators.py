# -*- coding: utf-8 -*-
"""COMPENSADORES (C09/C04) - uso consecutivo, excesso e faixa vertical.

Compensador e' peca de ACERTO: existe para fechar o resto que nenhum
bloco inteiro fecha. Dois deles encostados, ou varios no mesmo trecho,
sao sinal de que o trecho foi resolvido no chute em vez de na aritmetica
- e empilhados entre fiadas viram uma faixa fragil vertical.

`COMPENSATOR_AVOIDABLE` (nivel 2) e' o unico achado aqui que olha o
GABARITO: so' faz sentido dizer "dava para fechar sem compensador" quando
existe uma solucao conhecida para o mesmo trecho. Sem gabarito, ele nao
e' emitido - nunca chuta.
"""

from .. import analysis
from .. import model
from . import base


def _runs_of_solid_blocks(row, wall, block_height_cm):
    """Quebra a fiada em TRECHOS: sequencias de pecas encostadas, cortadas
    por aberturas ativas e por qualquer vazio maior que a junta. E' a
    unidade em que a regra "no maximo N compensadores por trecho" foi
    escrita."""
    extents = analysis.row_extents(row)
    runs = []
    current = []
    previous_end = None
    for t_start, t_end, block in extents:
        if previous_end is not None and t_start - previous_end > analysis.BOND_MAX_ADJACENT_GAP_CM:
            if current:
                runs.append(current)
            current = []
        current.append(block)
        previous_end = t_end
    if current:
        runs.append(current)
    return runs


def validate_wall(wall, block_height_cm):
    findings = []
    for row in model.rows_sorted(wall):
        blocks = model.blocks_sorted(row)

        # ---- 1) compensadores consecutivos -----------------------------
        for i in range(len(blocks) - 1):
            left, right = blocks[i], blocks[i + 1]
            if not (analysis.is_compensator(left) and analysis.is_compensator(right)):
                continue
            gap = right["t_start_cm"] - left["t_end_cm"]
            if gap > analysis.BOND_MAX_ADJACENT_GAP_CM:
                continue
            findings.append(base.finding(
                "COMPENSATOR_CONSECUTIVE",
                wall=wall["id"],
                detail=(
                    "{0} e {1} encostados na fiada {2} (t={3:.1f}cm e "
                    "{4:.1f}cm)".format(left.get("code"), right.get("code"),
                                        row["row"], left["t_start_cm"],
                                        right["t_start_cm"])
                ),
                row=row["row"],
                blocks=[left.get("id"), right.get("id")],
                codes=[left.get("code"), right.get("code")],
                t_cm=round(left["t_end_cm"], 2),
            ))

        # ---- 2) excesso no trecho --------------------------------------
        for run in _runs_of_solid_blocks(row, wall, block_height_cm):
            compensators = [b for b in run if analysis.is_compensator(b)]
            if len(compensators) > analysis.MAX_COMPENSATORS_PER_TRECHO:
                findings.append(base.finding(
                    "COMPENSATOR_EXCESS_IN_RUN",
                    wall=wall["id"],
                    detail=(
                        "{0} compensadores no trecho t={1:.1f}..{2:.1f}cm da "
                        "fiada {3} (teto {4})".format(
                            len(compensators), run[0]["t_start_cm"],
                            run[-1]["t_end_cm"], row["row"],
                            analysis.MAX_COMPENSATORS_PER_TRECHO)
                    ),
                    row=row["row"],
                    blocks=[b.get("id") for b in compensators],
                    run_t_cm=[round(run[0]["t_start_cm"], 2),
                              round(run[-1]["t_end_cm"], 2)],
                    count=len(compensators),
                ))

    # ---- 3) faixa vertical de compensadores ---------------------------
    rows = model.rows_sorted(wall)
    num_courses = len(rows)
    if num_courses >= analysis.BOND_STRIP_MIN_COURSES:
        points = []
        for row in rows:
            for block in row.get("blocks") or []:
                if analysis.is_compensator(block):
                    center = (block["t_start_cm"] + block["t_end_cm"]) / 2.0
                    points.append((center, row["row"]))
        for cluster in analysis.cluster_1d(points, analysis.BOND_STRIP_CLUSTER_TOLERANCE_CM):
            course_indices = sorted(set(cluster["items"]))
            ratio = len(course_indices) / float(num_courses)
            if (len(course_indices) >= analysis.BOND_STRIP_MIN_COURSES
                    and ratio >= analysis.BOND_STRIP_RATIO):
                findings.append(base.finding(
                    "COMPENSATOR_VERTICAL_STRIP",
                    wall=wall["id"],
                    detail=(
                        "compensadores empilhados em t={0:.1f}cm em {1} de {2} "
                        "fiadas".format(cluster["center"], len(course_indices),
                                        num_courses)
                    ),
                    t_cm=round(cluster["center"], 2),
                    rows=course_indices,
                    ratio=round(ratio, 3),
                ))
    return findings


def _compensator_count(wall):
    return sum(1 for row in wall.get("rows") or []
               for block in row.get("blocks") or []
               if analysis.is_compensator(block))


def validate(project, context=None):
    block_height = analysis.block_height_of(project)
    findings = []
    for wall in project.get("walls") or []:
        findings.extend(validate_wall(wall, block_height))

    # ---- 4) evitavel: so' com gabarito na mao (nivel 2) ----------------
    reference = (context or {}).get("reference")
    pairs = (context or {}).get("wall_pairs")
    if reference and pairs:
        for result_wall, reference_wall in pairs:
            if result_wall is None or reference_wall is None:
                continue
            mine = _compensator_count(result_wall)
            theirs = _compensator_count(reference_wall)
            if mine > theirs:
                findings.append(base.finding(
                    "COMPENSATOR_AVOIDABLE",
                    wall=result_wall["id"],
                    detail=(
                        "{0} compensadores contra {1} na mesma parede do "
                        "projeto humano ({2})".format(
                            mine, theirs, reference_wall["id"])
                    ),
                    count=mine,
                    reference_count=theirs,
                    reference_wall=reference_wall["id"],
                ))
    return findings


base.register("compensators", validate)
